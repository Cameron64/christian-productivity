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
    DetectionResult,
    extract_text_from_image
)
from .symbol_detector import verify_contour_conventions
from .quality_checker import QualityChecker, QualityCheckResults

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_sheet_type(detection_results: Dict[str, DetectionResult]) -> Dict[str, any]:
    """
    Validate that analyzed sheet is likely an ESC plan (not cover sheet, etc.)

    Checks for ESC-specific features and suspicious patterns that indicate
    the sheet may not be an actual ESC plan sheet.

    Args:
        detection_results: Detection results from detect_required_labels()

    Returns:
        Dictionary with:
            - is_esc_sheet: bool - Likely ESC sheet?
            - confidence: float - Confidence in sheet type (0.0 to 1.0)
            - warnings: List[str] - Validation warnings
    """
    warnings = []
    score = 0

    # Check for ESC-specific features
    if detection_results.get("silt_fence", DetectionResult("", False, 0.0, 0, [])).detected:
        score += 3
    if detection_results.get("sce", DetectionResult("", False, 0.0, 0, [])).detected:
        score += 3
    if detection_results.get("conc_wash", DetectionResult("", False, 0.0, 0, [])).detected:
        score += 3
    if detection_results.get("loc", DetectionResult("", False, 0.0, 0, [])).detected:
        score += 2

    # Check for suspicious patterns (cover sheet indicators)
    for element, result in detection_results.items():
        if result.count > 50:
            warnings.append(f"Excessive {element} occurrences ({result.count}) - may not be ESC plan")
            score -= 2

    # Missing critical ESC features
    has_esc_features = (
        detection_results.get("silt_fence", DetectionResult("", False, 0.0, 0, [])).detected or
        detection_results.get("sce", DetectionResult("", False, 0.0, 0, [])).detected or
        detection_results.get("conc_wash", DetectionResult("", False, 0.0, 0, [])).detected
    )

    if not has_esc_features:
        warnings.append("No ESC-specific features detected - may be wrong sheet type")
        score -= 5

    is_esc_sheet = score > 0
    confidence = min(1.0, max(0.0, score / 10.0))

    return {
        "is_esc_sheet": is_esc_sheet,
        "confidence": confidence,
        "warnings": warnings
    }


def validate_esc_sheet(
    pdf_path: str,
    sheet_keyword: str = "ESC",
    page_num: Optional[int] = None,
    dpi: int = 300,
    save_images: bool = False,
    output_dir: Optional[str] = None,
    enable_line_detection: bool = False,
    enable_quality_checks: bool = False
) -> Dict[str, any]:
    """
    Complete ESC sheet validation workflow (Phase 1 + Phase 2 + Phase 4).

    Extracts ESC sheet, runs text detection, verifies minimum quantities,
    optionally validates line types (contours), and optionally runs quality checks.

    Args:
        pdf_path: Path to the PDF file
        sheet_keyword: Keyword to identify ESC sheet (default: "ESC")
        page_num: Specific page number to extract (0-indexed). If None, auto-detect.
        dpi: Resolution for extraction (default: 300)
        save_images: Whether to save extracted/preprocessed images (default: False)
        output_dir: Directory to save images (if save_images=True)
        enable_line_detection: Enable Phase 2 line type detection (default: False)
        enable_quality_checks: Enable Phase 4 quality checks (default: False)

    Returns:
        Dictionary containing:
        - success: bool - Whether validation completed successfully
        - page_num: int - Page number of ESC sheet
        - detection_results: Dict[str, DetectionResult] - Element detection results
        - quantity_results: Dict[str, bool] - Minimum quantity verification
        - summary: Dict - Summary statistics
        - line_verification: Dict - Contour line verification (if enable_line_detection=True)
        - quality_checks: Dict - Quality check results (if enable_quality_checks=True)
        - errors: List[str] - Any errors encountered

    Example:
        >>> results = validate_esc_sheet("project_drawings.pdf", enable_quality_checks=True)
        >>> if results["success"]:
        ...     print(f"Validation complete: {results['summary']['pass_rate']:.1%} passed")
        ...     if results["summary"]["critical_failures"]:
        ...         print(f"CRITICAL: {results['summary']['critical_failures']}")
        ...     if results.get("quality_checks"):
        ...         print(f"Quality issues: {results['quality_checks']['total_issues']}")
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

    # Step 4: Validate sheet type
    logger.info("Step 4: Validating sheet type")
    sheet_validation = validate_sheet_type(detection_results)

    # Add sheet validation warnings to errors list
    if not sheet_validation["is_esc_sheet"]:
        errors.append("WARNING: This may not be an ESC plan sheet - see validation warnings")

    # Step 5: Line type detection (Phase 2 + 2.1 - optional)
    line_verification = None
    if enable_line_detection:
        logger.info("Step 5: Verifying contour line types (Phase 2.1 with spatial filtering)")
        try:
            # Extract text for line verification
            text = extract_text_from_image(preprocessed_image)

            # Use Phase 2.1 smart filtering by default
            from .symbol_detector import verify_contour_conventions_smart
            line_verification = verify_contour_conventions_smart(
                preprocessed_image,
                text,
                max_distance=150,  # Default proximity threshold
                use_spatial_filtering=True
            )

            # Add warnings if line conventions are violated
            if not line_verification.get('existing_correct', True):
                errors.append("WARNING: Existing contour line type may be incorrect")
            if not line_verification.get('proposed_correct', True):
                errors.append("WARNING: Proposed contour line type may be incorrect")

        except Exception as e:
            logger.warning(f"Line verification failed: {e}")
            errors.append(f"Line verification error: {e}")

    # Step 6: Quality checks (Phase 4 - optional)
    quality_check_results = None
    if enable_quality_checks:
        step_num = 6 if enable_line_detection else 5
        logger.info(f"Step {step_num}: Running quality checks (Phase 4)")
        try:
            quality_checker = QualityChecker(
                min_text_confidence=40.0,
                min_overlap_severity="minor"
            )

            # Run quality checks (no features yet - proximity validation skipped for now)
            qc_results = quality_checker.check_quality(
                image=preprocessed_image,
                features=None  # TODO: Extract features for proximity validation
            )

            # Convert to dict for JSON serialization
            quality_check_results = {
                "total_issues": qc_results.total_issues,
                "overlapping_labels": {
                    "total": len(qc_results.overlapping_labels),
                    "critical": qc_results.critical_overlaps,
                    "warning": qc_results.warning_overlaps,
                    "issues": [
                        {
                            "text1": issue.text1,
                            "text2": issue.text2,
                            "overlap_percent": round(issue.overlap_percent, 1),
                            "severity": issue.severity,
                            "location": issue.location
                        }
                        for issue in qc_results.overlapping_labels
                    ]
                },
                "proximity_validation": {
                    "total": len(qc_results.proximity_issues),
                    "errors": qc_results.proximity_errors,
                    "warnings": qc_results.proximity_warnings,
                    "issues": [
                        {
                            "label_text": issue.label_text,
                            "label_type": issue.label_type,
                            "nearest_distance": issue.nearest_distance,
                            "expected_max": issue.expected_max,
                            "severity": issue.severity
                        }
                        for issue in qc_results.proximity_issues
                    ]
                }
            }

            # Add warnings for critical quality issues
            if qc_results.critical_overlaps > 0:
                errors.append(f"WARNING: {qc_results.critical_overlaps} critical overlapping labels found")
            if qc_results.proximity_errors > 0:
                errors.append(f"WARNING: {qc_results.proximity_errors} spatial placement errors found")

        except Exception as e:
            logger.warning(f"Quality checks failed: {e}")
            errors.append(f"Quality checks error: {e}")

    # Step 7: Generate summary
    step_num = 7 if enable_quality_checks else (6 if enable_line_detection else 5)
    logger.info(f"Step {step_num}: Generating summary")
    summary = get_checklist_summary(detection_results)

    # Check for critical failures
    if summary["critical_failures"]:
        errors.append(f"CRITICAL: Missing required elements: {', '.join(summary['critical_failures'])}")

    # Determine overall success
    # Success = extraction worked, even if some checks failed
    # (We report failures but don't mark validation as unsuccessful)
    success = True

    logger.info(f"Validation complete: {summary['passed']}/{summary['total']} checks passed")
    if quality_check_results:
        logger.info(f"Quality checks: {quality_check_results['total_issues']} issues found")

    result = {
        "success": success,
        "page_num": page_num_found,
        "detection_results": detection_results,
        "quantity_results": quantity_results,
        "summary": summary,
        "sheet_validation": sheet_validation,
        "errors": errors
    }

    # Add line verification if enabled
    if line_verification is not None:
        result["line_verification"] = line_verification

    # Add quality checks if enabled
    if quality_check_results is not None:
        result["quality_checks"] = quality_check_results

    return result


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
