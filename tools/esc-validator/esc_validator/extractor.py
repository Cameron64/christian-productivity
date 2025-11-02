"""
PDF Extraction and Preprocessing

Extract ESC sheets from PDF drawing sets and convert to high-resolution
images optimized for OCR and computer vision processing.
"""

import logging
import re
from pathlib import Path
from typing import Tuple, Optional
import pdfplumber
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_esc_in_page_labels(pdf_path: str) -> Optional[int]:
    """
    Find ESC sheet using PDF PageLabels metadata (Phase 5.1).

    Civil 3D and other CAD software embed sheet names in PageLabels metadata.
    This is the fastest and most reliable detection method when available.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Page number (0-indexed) of ESC sheet if found in metadata, None otherwise

    Example PageLabel:
        b'\\xfe\\xff\\x00[\\x001\\x004\\x00]\\x00 \\x001\\x009\\x00 \\x00E\\x00R\\x00O\\x00S\\x00I\\x00O\\x00N...'
        Decodes to: "[14] 19 EROSION CONTROL (1 OF 2)"
    """
    logger.info("Checking for PageLabels metadata (Civil 3D format)")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Try to access PageLabels from PDF catalog
            if not hasattr(pdf, 'doc') or not hasattr(pdf.doc, 'catalog'):
                logger.debug("No PDF catalog access - PageLabels not available")
                return None

            catalog = pdf.doc.catalog
            if 'PageLabels' not in catalog:
                logger.debug("No PageLabels in PDF catalog")
                return None

            page_labels_dict = catalog['PageLabels']
            if 'Nums' not in page_labels_dict:
                logger.debug("PageLabels exists but has no Nums array")
                return None

            nums = page_labels_dict['Nums']
            logger.info(f"✓ Found PageLabels metadata with {len(nums)//2} entries")

            # Nums is a flat array: [page_idx, label_dict, page_idx, label_dict, ...]
            # Iterate in pairs
            for i in range(0, len(nums), 2):
                page_idx = nums[i]
                label_dict = nums[i + 1]

                if 'P' not in label_dict:
                    continue

                # Decode UTF-16BE label (skip BOM \xfe\xff)
                label_bytes = label_dict['P']
                try:
                    # UTF-16BE encoded with BOM
                    label = label_bytes[2:].decode('utf-16-be')
                except:
                    # Try without BOM skip
                    try:
                        label = label_bytes.decode('utf-16-be')
                    except:
                        logger.debug(f"Could not decode label at page {page_idx}")
                        continue

                label_upper = label.upper()

                # Check for ESC-related keywords (prioritize main ESC sheets, not notes)
                is_esc_sheet = False
                sheet_priority = 0

                # Priority 1: Main ESC/Erosion Control sheets
                if 'EROSION CONTROL' in label_upper and 'NOTES' not in label_upper:
                    is_esc_sheet = True
                    sheet_priority = 10
                    # Prefer "(1 OF" for multi-page sheets
                    if '(1 OF' in label_upper or '(1/' in label_upper:
                        sheet_priority = 11

                # Priority 2: ESC abbreviation (without notes)
                elif 'ESC' in label_upper and 'NOTES' not in label_upper:
                    is_esc_sheet = True
                    sheet_priority = 9

                # Priority 3: Sediment control
                elif 'SEDIMENT CONTROL' in label_upper and 'NOTES' not in label_upper:
                    is_esc_sheet = True
                    sheet_priority = 8

                # Priority 4: E&SC variations
                elif any(kw in label_upper for kw in ['E&SC', 'E & SC', 'E.S.C']) and 'NOTES' not in label_upper:
                    is_esc_sheet = True
                    sheet_priority = 7

                if is_esc_sheet:
                    logger.info(f"✓ Found ESC sheet in PageLabels: '{label}' (page {page_idx + 1}, priority {sheet_priority})")
                    # Return first high-priority match (main ESC sheet, not notes)
                    if sheet_priority >= 9:
                        return page_idx

            logger.warning("✗ PageLabels found but no ESC sheet detected")
            return None

    except Exception as e:
        logger.debug(f"Error reading PageLabels: {e}")
        return None


def extract_page_number_from_toc_line(line: str, next_line: str = "") -> Optional[int]:
    """
    Extract page number from TOC line with multiple strategies.

    Tries extraction strategies in order of reliability:
    1. Number at end of line: "EROSION CONTROL ... 26"
    2. Number range at end: "26-28" → 26
    3. Number in parentheses: "EROSION CONTROL (26)"
    4. Number with "PAGE" keyword: "PAGE 26" or "PG. 26"
    5. Standalone number in next line: "26" (on separate line)

    Args:
        line: The TOC line containing ESC reference
        next_line: The line immediately following (for multi-line TOC entries)

    Returns:
        Page number (1-indexed) if found, None otherwise

    Examples:
        >>> extract_page_number_from_toc_line("EROSION CONTROL PLAN ... 26")
        26
        >>> extract_page_number_from_toc_line("ESC-1 (PAGE 14)")
        14
        >>> extract_page_number_from_toc_line("EROSION CONTROL", "  14")
        14
    """
    # Strategy 1: Number at end of line (most common)
    match = re.search(r'\b(\d{1,3})\b\s*$', line)
    if match:
        logger.debug(f"Page number found at end of line: {match.group(1)}")
        return int(match.group(1))

    # Strategy 2: Number range at end (e.g., "26-28", take first page)
    match = re.search(r'\b(\d{1,3})-\d{1,3}\b\s*$', line)
    if match:
        logger.debug(f"Page range found, using first: {match.group(1)}")
        return int(match.group(1))

    # Strategy 3: Number in parentheses
    match = re.search(r'\((\d{1,3})\)', line)
    if match:
        logger.debug(f"Page number found in parentheses: {match.group(1)}")
        return int(match.group(1))

    # Strategy 4: Number with "PAGE" keyword
    match = re.search(r'(?:PAGE|PG\.?)\s*(\d{1,3})', line, re.IGNORECASE)
    if match:
        logger.debug(f"Page number found with PAGE keyword: {match.group(1)}")
        return int(match.group(1))

    # Strategy 5: Standalone number in next line
    if next_line:
        match = re.search(r'^\s*(\d{1,3})\s*$', next_line)
        if match:
            logger.debug(f"Page number found on next line: {match.group(1)}")
            return int(match.group(1))

    logger.debug("No page number found using any strategy")
    return None


def find_toc_esc_reference(pdf_path: str, max_toc_pages: int = 10) -> Optional[int]:
    """
    Find ESC sheet by searching for Table of Contents.

    Looks for TOC/Sheet Index in first few pages and extracts ESC sheet page number.
    This is much faster and more reliable than scanning the entire PDF.

    Args:
        pdf_path: Path to the PDF file
        max_toc_pages: Maximum number of pages to search for TOC (default: 10)

    Returns:
        Page number (0-indexed) of ESC sheet if found in TOC, None otherwise
    """
    logger.info(f"Searching for TOC in first {max_toc_pages} pages")

    toc_found = False
    toc_page_number = None
    esc_found_in_toc = False

    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_check = min(max_toc_pages, len(pdf.pages))

            for page_num in range(pages_to_check):
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                text_upper = text.upper()

                # Check if this page looks like a TOC
                # Expanded patterns based on civil engineering drawing set conventions
                toc_indicators = [
                    # Standard TOC headers
                    "SHEET INDEX", "DRAWING LIST", "SHEET LIST", "INDEX OF SHEETS", "TABLE OF CONTENTS",
                    # Civil engineering variations
                    "PLAN INDEX", "DRAWING INDEX", "SHEET LISTING", "PLAN LISTING",
                    # Standalone (if early in PDF)
                    "CONTENTS", "INDEX",
                    # Abbreviations
                    "TBL OF CONTENTS", "T.O.C", "TOC",
                    # With sheet numbers (common in civil plans)
                    "SHEET", "DRAWING"  # Will match if followed by sheet number patterns
                ]

                # Track which indicator matched for better diagnostics
                matched_indicator = None
                for indicator in toc_indicators:
                    if indicator in text_upper:
                        matched_indicator = indicator
                        break

                is_toc = matched_indicator is not None

                if is_toc:
                    toc_found = True
                    toc_page_number = page_num + 1
                    logger.info(f"✓ Found TOC on page {page_num + 1} (pattern: '{matched_indicator}')")

                    # Look for ESC sheet references in TOC
                    # Pattern: Sheet title with "ESC" or "EROSION" followed by page number
                    lines = text.split('\n')

                    for i, line in enumerate(lines):
                        line_upper = line.upper()

                        # Check if line mentions ESC/erosion
                        # Expanded patterns to catch more variations
                        esc_keywords = [
                            # Standard terms
                            "ESC", "EROSION", "SEDIMENT CONTROL",
                            # Abbreviations and variations
                            "E&SC", "E & SC", "E.S.C", "EC",
                            "EROSION CONTROL", "SEDIMENT",
                            # Related terms
                            "SWPPP", "POLLUTION PREVENTION",
                            # Sheet number patterns
                            "ESC-", "EC-", "ESC ", "EC "
                        ]
                        if any(keyword in line_upper for keyword in esc_keywords):
                            logger.debug(f"TOC line with ESC keyword: {line}")

                            # Try to extract page number using multi-strategy extraction
                            next_line = lines[i + 1] if i + 1 < len(lines) else ""
                            page_number = extract_page_number_from_toc_line(line, next_line)

                            if page_number:
                                # Convert from 1-indexed to 0-indexed
                                toc_page_num = page_number - 1
                                esc_found_in_toc = True
                                logger.info(f"✓ Found ESC sheet in TOC: page {page_number}")
                                return toc_page_num
                            else:
                                logger.warning(f"✗ ESC keyword found but no page number: {line}")

    except Exception as e:
        logger.error(f"Error searching TOC: {e}")

    # Diagnostic logging for TOC detection failures
    if not toc_found:
        logger.warning(f"✗ No TOC found in first {max_toc_pages} pages - falling back to full PDF scan")
    elif not esc_found_in_toc:
        logger.warning(f"✗ TOC found on page {toc_page_number} but no ESC reference - falling back to full PDF scan")

    return None


def find_esc_sheet(pdf_path: str, sheet_keyword: str = "ESC") -> Optional[int]:
    """
    Find ESC sheet using multi-layered detection (Phase 5.1 enhanced).

    Detection hierarchy (fastest to slowest):
    1. PageLabels metadata (Civil 3D PDFs) - INSTANT
    2. Table of Contents parsing - FAST (~1 second)
    3. Multi-factor scoring across all pages - SLOW (5-15 seconds)

    Scoring criteria (Phase 3):
    - High-value (5 pts): ESC + PLAN together, full phrase, sheet number pattern,
                          ESC NOTES, control notes phrases
    - Medium-high (3 pts): Standalone EROSION CONTROL or SEDIMENT CONTROL
    - Medium-value (2 pts): ESC-specific features (silt fence, SCE, washout, SWPPP, BMP)
    - Low-value (1 pt): General keywords (erosion, sediment)

    Minimum score threshold: 8 points (lowered from 10 to reduce false negatives)

    Args:
        pdf_path: Path to the PDF file
        sheet_keyword: Keyword to identify ESC sheet (default: "ESC")

    Returns:
        Page number (0-indexed) of best match, or None if no suitable sheet found
    """
    logger.info(f"Searching for ESC sheet in: {pdf_path}")

    # PHASE 0: Try PageLabels metadata (Phase 5.1 - instant, most reliable)
    metadata_page = find_esc_in_page_labels(pdf_path)
    if metadata_page is not None:
        logger.info("✓ Using PageLabels metadata detection (instant path)")
        return metadata_page

    # PHASE 1: Try TOC-based detection (Phase 5 - fast)
    toc_page = find_toc_esc_reference(pdf_path)
    if toc_page is not None:
        logger.info("✓ Using TOC-based sheet detection (fast path)")
        return toc_page

    # PHASE 2: Fall back to multi-factor scoring (slower but thorough)
    logger.info("TOC not found or incomplete - using multi-factor scoring")

    try:
        best_page = None
        best_score = 0

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text from page
                text = page.extract_text() or ""
                text_upper = text.upper()

                score = 0

                # High-value indicators (5 points each)
                if "ESC" in text_upper and "PLAN" in text_upper:
                    score += 5
                if "EROSION AND SEDIMENT CONTROL PLAN" in text_upper:
                    score += 5
                # Sheet number patterns: ESC-1, EC-1, ESC 1, etc.
                if re.search(r'\b(ESC|EC)[-\s]?\d+\b', text_upper):
                    score += 5
                # ESC NOTES is a strong indicator
                if "ESC" in text_upper and "NOTES" in text_upper:
                    score += 5
                if re.search(r'\b(ESC|EROSION|SEDIMENT)\s+CONTROL\s+NOTES\b', text_upper):
                    score += 5

                # Medium-high value indicators (3 points each)
                # These are standalone erosion/sediment control phrases
                if "EROSION CONTROL" in text_upper and "EROSION AND SEDIMENT CONTROL" not in text_upper:
                    score += 3
                if "SEDIMENT CONTROL" in text_upper and "EROSION AND SEDIMENT CONTROL" not in text_upper:
                    score += 3

                # Medium-value indicators (2 points each)
                if "SILT FENCE" in text_upper:
                    score += 2
                if "CONSTRUCTION ENTRANCE" in text_upper or "STABILIZED CONSTRUCTION ENTRANCE" in text_upper:
                    score += 2
                if "CONCRETE WASHOUT" in text_upper or "WASHOUT" in text_upper:
                    score += 2
                # SWPPP is a strong ESC indicator
                if "SWPPP" in text_upper:
                    score += 2
                # BMP with context
                if "BMP" in text_upper and ("EROSION" in text_upper or "SEDIMENT" in text_upper):
                    score += 2

                # Low-value indicators (1 point each)
                if "EROSION" in text_upper:
                    score += 1
                if "SEDIMENT" in text_upper:
                    score += 1

                # Track best match
                logger.debug(f"Page {page_num + 1}: score = {score}")
                if score > best_score:
                    best_score = score
                    best_page = page_num

            # Require minimum score threshold
            if best_score >= 8:
                logger.info(f"Found ESC sheet at page {best_page + 1} (score: {best_score})")
                return best_page
            else:
                logger.warning(f"No ESC sheet found (best score: {best_score})")
                return None

    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        return None


def extract_page_as_image(pdf_path: str, page_num: int, dpi: int = 300) -> Optional[np.ndarray]:
    """
    Extract a single page from PDF as high-resolution image.

    Args:
        pdf_path: Path to the PDF file
        page_num: Page number (0-indexed)
        dpi: Resolution for extraction (default: 300)

    Returns:
        Image as numpy array (RGB), or None if extraction fails
    """
    logger.info(f"Extracting page {page_num + 1} at {dpi} DPI")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num >= len(pdf.pages):
                logger.error(f"Page {page_num} does not exist (PDF has {len(pdf.pages)} pages)")
                return None

            page = pdf.pages[page_num]

            # Convert page to image at specified DPI
            img = page.to_image(resolution=dpi)

            # Convert to PIL Image, then to numpy array
            pil_img = img.original
            np_img = np.array(pil_img)

            # Convert RGBA to RGB if needed
            if np_img.shape[2] == 4:
                np_img = cv2.cvtColor(np_img, cv2.COLOR_RGBA2RGB)

            logger.info(f"Extracted image with shape: {np_img.shape}")
            return np_img

    except Exception as e:
        logger.error(f"Error extracting page as image: {e}")
        return None


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image to improve OCR accuracy.

    Applies:
    - Grayscale conversion
    - Contrast enhancement
    - Denoising
    - Adaptive thresholding

    Args:
        image: Input image as numpy array (RGB)

    Returns:
        Preprocessed image as numpy array (grayscale)
    """
    logger.info("Preprocessing image for OCR")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Apply denoising
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)

    # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # Optional: Apply adaptive thresholding for better text detection
    # This can help separate text from background
    # Uncomment if OCR accuracy is poor
    # thresholded = cv2.adaptiveThreshold(
    #     enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    # )
    # return thresholded

    logger.info("Preprocessing complete")
    return enhanced


def preprocess_for_line_detection(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for line detection (Phase 2).

    Applies:
    - Grayscale conversion
    - Gaussian blur
    - Edge detection preparation

    Args:
        image: Input image as numpy array (RGB)

    Returns:
        Preprocessed image as numpy array (grayscale)
    """
    logger.info("Preprocessing image for line detection")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    logger.info("Line detection preprocessing complete")
    return blurred


def extract_esc_sheet(
    pdf_path: str,
    sheet_keyword: str = "ESC",
    page_num: Optional[int] = None,
    dpi: int = 300,
    preprocess: bool = True
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[int]]:
    """
    Extract ESC sheet from PDF and return both original and preprocessed images.

    This is the main entry point for Phase 1 extraction.

    Args:
        pdf_path: Path to the PDF file
        sheet_keyword: Keyword to identify ESC sheet (default: "ESC")
        page_num: Specific page number to extract (0-indexed). If None, auto-detect.
        dpi: Resolution for extraction (default: 300)
        preprocess: Whether to preprocess image for OCR (default: True)

    Returns:
        Tuple of (original_image, preprocessed_image, page_number)
        Returns (None, None, None) if extraction fails

    Example:
        >>> original, processed, page_num = extract_esc_sheet("drawing_set.pdf")
        >>> if original is not None:
        ...     print(f"Extracted ESC sheet from page {page_num + 1}")
    """
    logger.info(f"Starting ESC sheet extraction from: {pdf_path}")

    # Validate PDF path
    if not Path(pdf_path).exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return None, None, None

    # Find ESC sheet if page number not provided
    if page_num is None:
        page_num = find_esc_sheet(pdf_path, sheet_keyword)
        if page_num is None:
            logger.error("Could not find ESC sheet in PDF")
            return None, None, None

    # Extract page as image
    original_image = extract_page_as_image(pdf_path, page_num, dpi)
    if original_image is None:
        return None, None, None

    # Preprocess for OCR if requested
    preprocessed_image = None
    if preprocess:
        preprocessed_image = preprocess_for_ocr(original_image)

    logger.info("ESC sheet extraction complete")
    return original_image, preprocessed_image, page_num


def save_image(image: np.ndarray, output_path: str) -> bool:
    """
    Save image to disk.

    Args:
        image: Image as numpy array
        output_path: Path to save image

    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert RGB to BGR for OpenCV
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        cv2.imwrite(output_path, image)
        logger.info(f"Saved image to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return False
