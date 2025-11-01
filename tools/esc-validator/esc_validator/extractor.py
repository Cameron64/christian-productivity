"""
PDF Extraction and Preprocessing

Extract ESC sheets from PDF drawing sets and convert to high-resolution
images optimized for OCR and computer vision processing.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional
import pdfplumber
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_esc_sheet(pdf_path: str, sheet_keyword: str = "ESC") -> Optional[int]:
    """
    Find the ESC sheet in a PDF drawing set by searching page text.

    Args:
        pdf_path: Path to the PDF file
        sheet_keyword: Keyword to identify ESC sheet (default: "ESC")

    Returns:
        Page number (0-indexed) of ESC sheet, or None if not found
    """
    logger.info(f"Searching for ESC sheet in: {pdf_path}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text from page
                text = page.extract_text() or ""

                # Look for ESC keyword in text (case-insensitive)
                if sheet_keyword.upper() in text.upper():
                    # Additional validation: check if it's likely an ESC plan
                    text_upper = text.upper()
                    if any(keyword in text_upper for keyword in ["EROSION", "SEDIMENT", "CONTROL", "PLAN"]):
                        logger.info(f"Found ESC sheet at page {page_num + 1}")
                        return page_num

            logger.warning(f"No ESC sheet found with keyword '{sheet_keyword}'")
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
