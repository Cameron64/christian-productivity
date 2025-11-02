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

    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_check = min(max_toc_pages, len(pdf.pages))

            for page_num in range(pages_to_check):
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                text_upper = text.upper()

                # Check if this page looks like a TOC
                toc_indicators = ["SHEET INDEX", "DRAWING LIST", "SHEET LIST", "INDEX OF SHEETS", "TABLE OF CONTENTS"]
                is_toc = any(indicator in text_upper for indicator in toc_indicators)

                if is_toc:
                    logger.info(f"Found TOC at page {page_num + 1}")

                    # Look for ESC sheet references in TOC
                    # Pattern: Sheet title with "ESC" or "EROSION" followed by page number
                    lines = text.split('\n')

                    for i, line in enumerate(lines):
                        line_upper = line.upper()

                        # Check if line mentions ESC/erosion
                        if any(keyword in line_upper for keyword in ["ESC", "EROSION", "SEDIMENT CONTROL"]):
                            logger.debug(f"TOC line: {line}")

                            # Try to extract page number from this line or nearby lines
                            # Common patterns: "ESC-1 ... 15", "EROSION CONTROL PLAN ... PAGE 15"
                            # Look for numbers at end of line or in next few lines
                            page_match = re.search(r'\b(\d{1,3})\b\s*$', line)
                            if page_match:
                                toc_page_num = int(page_match.group(1)) - 1  # Convert to 0-indexed
                                logger.info(f"Found ESC sheet in TOC: page {toc_page_num + 1}")
                                return toc_page_num

                            # Try next line (sometimes page number is on separate line)
                            if i + 1 < len(lines):
                                next_line = lines[i + 1]
                                page_match = re.search(r'^\s*(\d{1,3})\s*$', next_line)
                                if page_match:
                                    toc_page_num = int(page_match.group(1)) - 1
                                    logger.info(f"Found ESC sheet in TOC: page {toc_page_num + 1}")
                                    return toc_page_num

    except Exception as e:
        logger.error(f"Error searching TOC: {e}")

    logger.info("No ESC sheet found in TOC")
    return None


def find_esc_sheet(pdf_path: str, sheet_keyword: str = "ESC") -> Optional[int]:
    """
    Find ESC sheet using multi-factor scoring algorithm.

    First tries to find ESC sheet via Table of Contents (fast, reliable).
    If TOC not found or doesn't contain ESC reference, falls back to
    scanning all pages with weighted scoring.

    Scoring criteria:
    - High-value (5 pts): ESC + PLAN together, full phrase, sheet number pattern
    - Medium-value (2 pts): ESC-specific features (silt fence, SCE, washout)
    - Low-value (1 pt): General keywords (erosion, sediment)

    Minimum score threshold: 10 points

    Args:
        pdf_path: Path to the PDF file
        sheet_keyword: Keyword to identify ESC sheet (default: "ESC")

    Returns:
        Page number (0-indexed) of best match, or None if no suitable sheet found
    """
    logger.info(f"Searching for ESC sheet in: {pdf_path}")

    # PHASE 1: Try TOC-based detection (fast)
    toc_page = find_toc_esc_reference(pdf_path)
    if toc_page is not None:
        logger.info("Using TOC-based sheet detection (fast path)")
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

                # Medium-value indicators (2 points each)
                if "SILT FENCE" in text_upper:
                    score += 2
                if "CONSTRUCTION ENTRANCE" in text_upper or "STABILIZED CONSTRUCTION ENTRANCE" in text_upper:
                    score += 2
                if "CONCRETE WASHOUT" in text_upper or "WASHOUT" in text_upper:
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
            if best_score >= 10:
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
