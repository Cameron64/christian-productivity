#!/usr/bin/env python3
"""
ESC Sheet Validator - Command Line Interface

Validate Erosion and Sediment Control (ESC) sheets from civil engineering
drawing sets. Checks for required elements per Austin/Travis County regulations.

Usage:
    # Validate single PDF
    python validate_esc.py "path/to/drawing_set.pdf"

    # Specify output file
    python validate_esc.py "drawing.pdf" --output report.md

    # Batch process multiple PDFs
    python validate_esc.py documents/*.pdf --batch --output-dir reports/

    # Save extracted images
    python validate_esc.py "drawing.pdf" --save-images --output-dir output/

    # Verbose report with detailed findings
    python validate_esc.py "drawing.pdf" --verbose

    # Specify page number manually
    python validate_esc.py "drawing.pdf" --page 15
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import List
import os

# Configure console encoding for Windows
if sys.platform == "win32":
    # Try to set UTF-8 encoding for console output
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        # If reconfigure fails, fall back to ASCII-safe output
        pass

# Add the esc_validator package to path
sys.path.insert(0, str(Path(__file__).parent))

from esc_validator import validate_esc_sheet
from esc_validator.validator import validate_esc_sheet_from_image
from esc_validator.reporter import generate_markdown_report, generate_text_report, save_report

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_single_pdf(
    pdf_path: str,
    output_path: str = None,
    page_num: int = None,
    save_images: bool = False,
    output_dir: str = None,
    verbose: bool = False,
    verbose_progress: bool = False,
    dpi: int = 300,
    enable_line_detection: bool = False,
    ocr_engine: str = "tesseract"
) -> bool:
    """
    Validate a single PDF file.

    Args:
        pdf_path: Path to PDF file
        output_path: Path to save report (optional)
        page_num: Specific page number (optional)
        save_images: Whether to save extracted images
        output_dir: Directory for outputs
        verbose: Include detailed findings in report
        verbose_progress: Show progress indicators during validation
        dpi: Resolution for extraction
        enable_line_detection: Enable Phase 2 line type detection

    Returns:
        True if validation passed, False otherwise
    """
    logger.info(f"Validating: {pdf_path}")

    # Run validation
    results = validate_esc_sheet(
        pdf_path=pdf_path,
        page_num=page_num,
        dpi=dpi,
        save_images=save_images,
        output_dir=output_dir,
        enable_line_detection=enable_line_detection,
        verbose=verbose_progress,
        ocr_engine=ocr_engine
    )

    # Check if validation succeeded
    if not results["success"]:
        print(f"\n❌ Validation FAILED for {Path(pdf_path).name}")
        for error in results.get("errors", []):
            print(f"   ERROR: {error}")
        return False

    # Generate report
    report = generate_markdown_report(results, pdf_path, verbose=verbose)

    # Print summary to console
    summary = results["summary"]
    critical_failures = summary.get("critical_failures", [])

    if critical_failures:
        print(f"\n⚠️  {Path(pdf_path).name} - NEEDS REVIEW")
        print(f"   Checks passed: {summary['passed']}/{summary['total']} ({summary['pass_rate']:.1%})")
        print(f"   CRITICAL ISSUES: {', '.join(critical_failures).upper()}")
    elif summary["pass_rate"] >= 0.9:
        print(f"\n✅ {Path(pdf_path).name} - PASS")
        print(f"   Checks passed: {summary['passed']}/{summary['total']} ({summary['pass_rate']:.1%})")
    else:
        print(f"\n⚠️  {Path(pdf_path).name} - ACCEPTABLE")
        print(f"   Checks passed: {summary['passed']}/{summary['total']} ({summary['pass_rate']:.1%})")

    # Save report if output path specified
    if output_path:
        if save_report(report, output_path):
            print(f"   Report saved: {output_path}")
        else:
            print(f"   ERROR: Failed to save report")
            return False
    else:
        # Print report to console if no output file
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)

    return not bool(critical_failures)


def validate_batch(
    pdf_paths: List[str],
    output_dir: str = None,
    save_images: bool = False,
    verbose: bool = False,
    verbose_progress: bool = False,
    dpi: int = 300,
    enable_line_detection: bool = False
) -> dict:
    """
    Validate multiple PDF files.

    Args:
        pdf_paths: List of PDF file paths
        output_dir: Directory to save reports
        save_images: Whether to save extracted images
        verbose: Include detailed findings in reports
        verbose_progress: Show progress indicators during validation
        dpi: Resolution for extraction
        enable_line_detection: Enable Phase 2 line type detection

    Returns:
        Dictionary with batch statistics
    """
    logger.info(f"Batch processing {len(pdf_paths)} files")

    # Create output directory
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

    results_summary = {
        "total": len(pdf_paths),
        "passed": 0,
        "needs_review": 0,
        "failed": 0,
    }

    # Process each file
    for pdf_path in pdf_paths:
        try:
            # Generate output path
            if output_dir:
                pdf_name = Path(pdf_path).stem
                report_path = output_path / f"{pdf_name}_validation.md"
            else:
                report_path = None

            # Validate
            passed = validate_single_pdf(
                pdf_path=pdf_path,
                output_path=str(report_path) if report_path else None,
                save_images=save_images,
                output_dir=output_dir,
                verbose=verbose,
                verbose_progress=verbose_progress,
                dpi=dpi,
                enable_line_detection=enable_line_detection
            )

            if passed:
                results_summary["passed"] += 1
            else:
                results_summary["needs_review"] += 1

        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            results_summary["failed"] += 1
            print(f"\n❌ FAILED: {Path(pdf_path).name} - {e}")

    # Print batch summary
    print("\n" + "=" * 60)
    print("BATCH VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {results_summary['total']}")
    print(f"✅ Passed:            {results_summary['passed']}")
    print(f"⚠️  Needs review:      {results_summary['needs_review']}")
    print(f"❌ Failed:            {results_summary['failed']}")
    print("=" * 60)

    if output_dir:
        print(f"\nReports saved to: {output_dir}")

    return results_summary


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate ESC sheets in civil engineering drawing sets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate single PDF
  python validate_esc.py "5620-01 Entrada East.pdf"

  # Save report to file
  python validate_esc.py "drawing.pdf" --output report.md

  # Batch process multiple PDFs
  python validate_esc.py documents/*.pdf --batch --output-dir reports/

  # Save extracted images for inspection
  python validate_esc.py "drawing.pdf" --save-images --output-dir output/

  # Verbose report with detailed findings
  python validate_esc.py "drawing.pdf" --output report.md --verbose

  # Manually specify ESC sheet page number
  python validate_esc.py "drawing.pdf" --page 15
        """
    )

    parser.add_argument(
        "pdf_files",
        nargs="+",
        help="PDF file(s) to validate"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output file path for validation report (markdown)"
    )

    parser.add_argument(
        "--output-dir",
        help="Output directory for reports and images (used with --batch or --save-images)"
    )

    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch process multiple PDFs"
    )

    parser.add_argument(
        "-p", "--page",
        type=int,
        help="Specific page number of ESC sheet (0-indexed)"
    )

    parser.add_argument(
        "--save-images",
        action="store_true",
        help="Save extracted and preprocessed images"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed progress and timing information"
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )

    parser.add_argument(
        "--verbose-report",
        action="store_true",
        help="Generate verbose report with detailed findings"
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution for PDF extraction (default: 300)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    parser.add_argument(
        "--enable-line-detection",
        action="store_true",
        help="Enable Phase 2 line type detection (contour verification)"
    )

    parser.add_argument(
        "--ocr-engine",
        choices=["paddleocr", "tesseract"],
        default="tesseract",
        help="OCR engine to use (default: tesseract, paddleocr has API issues)"
    )

    args = parser.parse_args()

    # Set log level based on verbosity flags
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # Validate arguments
    if len(args.pdf_files) > 1 and not args.batch:
        print("Error: Multiple files specified without --batch flag")
        print("Use --batch to process multiple files")
        sys.exit(1)

    if args.output and args.batch:
        print("Error: Cannot use --output with --batch (use --output-dir instead)")
        sys.exit(1)

    # Process files
    try:
        if args.batch:
            results = validate_batch(
                pdf_paths=args.pdf_files,
                output_dir=args.output_dir,
                save_images=args.save_images,
                verbose=args.verbose_report,
                verbose_progress=args.verbose,
                dpi=args.dpi,
                enable_line_detection=args.enable_line_detection
            )
            # Exit with error code if any files failed or need review
            if results["failed"] > 0 or results["needs_review"] > 0:
                sys.exit(1)

        else:
            # Single file validation
            success = validate_single_pdf(
                pdf_path=args.pdf_files[0],
                output_path=args.output,
                page_num=args.page,
                save_images=args.save_images,
                output_dir=args.output_dir,
                verbose=args.verbose_report,
                verbose_progress=args.verbose,
                dpi=args.dpi,
                enable_line_detection=args.enable_line_detection,
                ocr_engine=args.ocr_engine
            )

            # Exit with error code if validation failed
            if not success:
                sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
