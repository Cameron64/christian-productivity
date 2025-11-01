"""
Report Generation

Generate human-readable validation reports in various formats.
"""

import logging
from typing import Dict
from datetime import datetime
from pathlib import Path

from .text_detector import DetectionResult

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Element display names for reports
ELEMENT_DISPLAY_NAMES = {
    "legend": "Legend",
    "scale": "Scale",
    "north_bar": "North Bar",
    "loc": "Limits of Construction (LOC)",
    "silt_fence": "Silt Fence (SF)",
    "sce": "Stabilized Construction Entrance (SCE)",
    "conc_wash": "Concrete Washout",
    "staging": "Staging/Spoils Area",
    "existing_contours": "Existing Contours Labeled",
    "proposed_contours": "Proposed Contours Labeled",
    "streets": "Streets Labeled",
    "lot_block": "Lot and Block Labels",
}


def format_status_icon(detected: bool) -> str:
    """Format pass/fail as icon."""
    return "✓" if detected else "✗"


def format_confidence(confidence: float) -> str:
    """Format confidence as percentage."""
    return f"{confidence * 100:.0f}%"


def generate_markdown_report(
    validation_results: Dict[str, any],
    pdf_path: str,
    verbose: bool = False
) -> str:
    """
    Generate a markdown-formatted validation report.

    Args:
        validation_results: Results from validate_esc_sheet()
        pdf_path: Path to original PDF (for reference)
        verbose: Include detailed information (default: False)

    Returns:
        Markdown-formatted report as string
    """
    logger.info("Generating markdown report")

    # Extract data from results
    success = validation_results["success"]
    page_num = validation_results.get("page_num")
    detection_results = validation_results["detection_results"]
    quantity_results = validation_results["quantity_results"]
    summary = validation_results["summary"]
    errors = validation_results.get("errors", [])

    # Build report
    lines = []

    # Header
    lines.append("# ESC Sheet Validation Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**PDF File:** {Path(pdf_path).name}")
    if page_num is not None:
        lines.append(f"**Page Number:** {page_num + 1}")
    lines.append("")

    # Overall status
    if not success:
        lines.append("## ⚠️ VALIDATION FAILED")
        lines.append("")
        lines.append("The validation process encountered errors and could not complete.")
        lines.append("")
        if errors:
            lines.append("**Errors:**")
            for error in errors:
                lines.append(f"- {error}")
        return "\n".join(lines)

    # Summary
    pass_rate = summary.get("pass_rate", 0.0)
    passed = summary.get("passed", 0)
    total = summary.get("total", 0)
    critical_failures = summary.get("critical_failures", [])

    if critical_failures:
        status_emoji = "⚠️"
        status_text = "NEEDS REVIEW"
    elif pass_rate >= 0.9:
        status_emoji = "✅"
        status_text = "PASS"
    elif pass_rate >= 0.7:
        status_emoji = "⚠️"
        status_text = "ACCEPTABLE"
    else:
        status_emoji = "❌"
        status_text = "FAIL"

    lines.append(f"## {status_emoji} Status: {status_text}")
    lines.append("")
    lines.append(f"**Checks Passed:** {passed}/{total} ({pass_rate:.1%})")
    lines.append(f"**Average Confidence:** {format_confidence(summary.get('avg_confidence', 0.0))}")
    lines.append("")

    # Critical failures section
    if critical_failures:
        lines.append("## 🚨 Critical Issues")
        lines.append("")
        lines.append("The following required elements were not detected:")
        lines.append("")
        for element in critical_failures:
            display_name = ELEMENT_DISPLAY_NAMES.get(element, element)
            lines.append(f"- **{display_name}** - MUST be added before submission")
        lines.append("")

    # Checklist table
    lines.append("## Checklist Results")
    lines.append("")
    lines.append("| Element | Status | Count | Confidence | Notes |")
    lines.append("|---------|--------|-------|------------|-------|")

    for element, result in detection_results.items():
        display_name = ELEMENT_DISPLAY_NAMES.get(element, element)
        status = format_status_icon(result.detected)
        count_str = str(result.count) if result.count > 0 else "-"
        confidence = format_confidence(result.confidence) if result.detected else "-"
        notes = result.notes if result.notes else "-"

        # Highlight critical elements
        if element in quantity_results:
            min_required = 1  # Simplification - all critical elements need >= 1
            if not quantity_results[element]:
                status = "❌"
                notes = f"Required: ≥{min_required}, Found: {result.count}"

        lines.append(f"| {display_name} | {status} | {count_str} | {confidence} | {notes} |")

    lines.append("")

    # Verbose details
    if verbose and detection_results:
        lines.append("## Detailed Findings")
        lines.append("")

        for element, result in detection_results.items():
            if result.detected and result.matches:
                display_name = ELEMENT_DISPLAY_NAMES.get(element, element)
                lines.append(f"### {display_name}")
                lines.append("")
                lines.append(f"- **Detected:** Yes")
                lines.append(f"- **Occurrences:** {result.count}")
                lines.append(f"- **Confidence:** {format_confidence(result.confidence)}")
                if result.matches:
                    lines.append(f"- **Matches:** {', '.join(result.matches[:5])}")  # Show first 5
                lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")

    if not detection_results:
        lines.append("- No elements detected - verify that ESC sheet was correctly identified")
        lines.append("- Try increasing DPI or improving image quality")
    elif critical_failures:
        lines.append("### Required Actions")
        for element in critical_failures:
            display_name = ELEMENT_DISPLAY_NAMES.get(element, element)
            lines.append(f"1. Add **{display_name}** to the ESC sheet")
        lines.append("")

    # Items with low confidence
    low_confidence = [
        (element, result) for element, result in detection_results.items()
        if result.detected and result.confidence < 0.7
    ]

    if low_confidence:
        lines.append("### Manual Verification Recommended")
        lines.append("")
        lines.append("The following items were detected but with low confidence:")
        lines.append("")
        for element, result in low_confidence:
            display_name = ELEMENT_DISPLAY_NAMES.get(element, element)
            lines.append(f"- **{display_name}** (confidence: {format_confidence(result.confidence)})")
        lines.append("")
        lines.append("Please manually verify these elements on the ESC sheet.")
        lines.append("")

    if not critical_failures and pass_rate >= 0.9:
        lines.append("✅ ESC sheet appears to be complete and ready for submission!")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*This report was generated automatically by the ESC Validator tool (Phase 1).*")
    lines.append("*Always perform manual review before submission.*")

    return "\n".join(lines)


def generate_text_report(
    validation_results: Dict[str, any],
    pdf_path: str
) -> str:
    """
    Generate a simple text-formatted validation report.

    Args:
        validation_results: Results from validate_esc_sheet()
        pdf_path: Path to original PDF

    Returns:
        Plain text report as string
    """
    logger.info("Generating text report")

    detection_results = validation_results["detection_results"]
    summary = validation_results["summary"]
    critical_failures = summary.get("critical_failures", [])

    lines = []
    lines.append("=" * 60)
    lines.append("ESC SHEET VALIDATION REPORT")
    lines.append("=" * 60)
    lines.append(f"PDF: {Path(pdf_path).name}")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Summary
    passed = summary.get("passed", 0)
    total = summary.get("total", 0)
    pass_rate = summary.get("pass_rate", 0.0)

    lines.append(f"SUMMARY: {passed}/{total} checks passed ({pass_rate:.1%})")
    lines.append("")

    # Critical failures
    if critical_failures:
        lines.append("CRITICAL FAILURES:")
        for element in critical_failures:
            display_name = ELEMENT_DISPLAY_NAMES.get(element, element)
            lines.append(f"  [!] {display_name}")
        lines.append("")

    # Checklist
    lines.append("CHECKLIST:")
    for element, result in detection_results.items():
        display_name = ELEMENT_DISPLAY_NAMES.get(element, element)
        status = "[✓]" if result.detected else "[✗]"
        lines.append(f"  {status} {display_name} (count: {result.count})")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def save_report(report: str, output_path: str) -> bool:
    """
    Save report to file.

    Args:
        report: Report content as string
        output_path: Path to save report

    Returns:
        True if successful, False otherwise
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"Report saved to: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving report: {e}")
        return False
