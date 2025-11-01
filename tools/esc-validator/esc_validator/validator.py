"""
ESC Sheet Validator

Integration module that orchestrates extraction, detection, and validation.
"""

import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
import numpy as np

from .extractor import extract_esc_sheet, save_image
from .text_detector import (
    detect_required_labels,
    verify_minimum_quantities,
    get_checklist_summary,
    DetectionResult
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_esc_sheet(
    pdf_path: str,
    sheet_keyword: str = "ESC",
    page_num: Optional[int] = None,
    dpi: int = 300,
    save_images: bool = False,
    output_dir: Optional[str] = None
) -> Dict[str, any]:
    """
    Complete ESC sheet validation workflow (Phase 1).

    Extracts ESC sheet, runs text detection, verifies minimum quantities,
    and returns comprehensive validation results.

    Args:
        pdf_path: Path to the PDF file
        sheet_keyword: Keyword to identify ESC sheet (default: "ESC")
        page_num: Specific page number to extract (0-indexed). If None, auto-detect.
        dpi: Resolution for extraction (default: 300)
        save_images: Whether to save extracted/preprocessed images (default: False)
        output_dir: Directory to save images (if save_images=True)

    Returns:
        Dictionary containing:
        - success: bool - Whether validation completed successfully
        - page_num: int - Page number of ESC sheet
        - detection_results: Dict[str, DetectionResult] - Element detection results
        - quantity_results: Dict[str, bool] - Minimum quantity verification
        - summary: Dict - Summary statistics
        - errors: List[str] - Any errors encountered

    Example:
        >>> results = validate_esc_sheet("project_drawings.pdf")
        >>> if results["success"]:
        ...     print(f"Validation complete: {results['summary']['pass_rate']:.1%} passed")
        ...     if results["summary"]["critical_failures"]:
        ...         print(f"CRITICAL: {results['summary']['critical_failures']}")
    """
    logger.info(f"Starting ESC sheet validation for: {pdf_path}")

    errors = []

    # Validate inputs
    if not Path(pdf_path).exists():
        error = f"PDF file not found: {pdf_path}"
        logger.error(error)
        return {
            "success": False,
            "page_num": None,
            "detection_results": {},
            "quantity_results": {},
            "summary": {},
            "errors": [error]
        }

    # Step 1: Extract ESC sheet
    logger.info("Step 1: Extracting ESC sheet")
    original_image, preprocessed_image, page_num_found = extract_esc_sheet(
        pdf_path=pdf_path,
        sheet_keyword=sheet_keyword,
        page_num=page_num,
        dpi=dpi,
        preprocess=True
    )

    if original_image is None or preprocessed_image is None:
        error = "Failed to extract ESC sheet from PDF"
        logger.error(error)
        return {
            "success": False,
            "page_num": None,
            "detection_results": {},
            "quantity_results": {},
            "summary": {},
            "errors": [error]
        }

    logger.info(f"Successfully extracted ESC sheet from page {page_num_found + 1}")

    # Optional: Save images for inspection
    if save_images:
        if output_dir is None:
            output_dir = Path(pdf_path).parent / "esc_validation_output"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        pdf_name = Path(pdf_path).stem
        original_path = output_path / f"{pdf_name}_page{page_num_found + 1}_original.png"
        preprocessed_path = output_path / f"{pdf_name}_page{page_num_found + 1}_preprocessed.png"

        save_image(original_image, str(original_path))
        save_image(preprocessed_image, str(preprocessed_path))
        logger.info(f"Saved images to: {output_path}")

    # Step 2: Detect required labels
    logger.info("Step 2: Detecting required labels")
    detection_results = detect_required_labels(preprocessed_image)

    # Step 3: Verify minimum quantities
    logger.info("Step 3: Verifying minimum quantities")
    quantity_results = verify_minimum_quantities(detection_results)

    # Step 4: Generate summary
    logger.info("Step 4: Generating summary")
    summary = get_checklist_summary(detection_results)

    # Check for critical failures
    if summary["critical_failures"]:
        errors.append(f"CRITICAL: Missing required elements: {', '.join(summary['critical_failures'])}")

    # Determine overall success
    # Success = extraction worked, even if some checks failed
    # (We report failures but don't mark validation as unsuccessful)
    success = True

    logger.info(f"Validation complete: {summary['passed']}/{summary['total']} checks passed")

    return {
        "success": success,
        "page_num": page_num_found,
        "detection_results": detection_results,
        "quantity_results": quantity_results,
        "summary": summary,
        "errors": errors
    }


def validate_esc_sheet_from_image(image_path: str) -> Dict[str, any]:
    """
    Validate ESC sheet from an already-extracted image file.

    Useful for testing or when ESC sheet is already extracted.

    Args:
        image_path: Path to ESC sheet image file

    Returns:
        Validation results (same format as validate_esc_sheet)
    """
    import cv2

    logger.info(f"Validating ESC sheet from image: {image_path}")

    # Load image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        error = f"Failed to load image: {image_path}"
        logger.error(error)
        return {
            "success": False,
            "page_num": None,
            "detection_results": {},
            "quantity_results": {},
            "summary": {},
            "errors": [error]
        }

    # Run detection
    detection_results = detect_required_labels(image)
    quantity_results = verify_minimum_quantities(detection_results)
    summary = get_checklist_summary(detection_results)

    errors = []
    if summary["critical_failures"]:
        errors.append(f"CRITICAL: Missing required elements: {', '.join(summary['critical_failures'])}")

    return {
        "success": True,
        "page_num": None,  # Unknown when loading from image
        "detection_results": detection_results,
        "quantity_results": quantity_results,
        "summary": summary,
        "errors": errors
    }
