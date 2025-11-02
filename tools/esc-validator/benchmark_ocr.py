"""
OCR Performance Benchmark Script (Phase 4.1)

Compares performance of Tesseract vs PaddleOCR and demonstrates
the performance impact of OCR caching.
"""

import time
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from esc_validator.validator import validate_esc_sheet
from esc_validator.ocr_engine import clear_ocr_cache

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def benchmark_validation(
    pdf_path: str,
    ocr_engine: str = "paddleocr",
    enable_quality_checks: bool = True,
    runs: int = 1
) -> dict:
    """
    Benchmark validation performance.

    Args:
        pdf_path: Path to PDF file
        ocr_engine: OCR engine to use
        enable_quality_checks: Whether to enable Phase 4 quality checks
        runs: Number of runs to average

    Returns:
        dict with timing results
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Benchmarking: {ocr_engine.upper()} engine")
    logger.info(f"Quality checks: {'ENABLED' if enable_quality_checks else 'DISABLED'}")
    logger.info(f"Runs: {runs}")
    logger.info(f"{'='*60}\n")

    times = []

    for run in range(runs):
        # Clear cache before each run
        clear_ocr_cache()

        logger.info(f"Run {run + 1}/{runs}...")
        start_time = time.time()

        result = validate_esc_sheet(
            pdf_path=pdf_path,
            enable_quality_checks=enable_quality_checks,
            ocr_engine=ocr_engine
        )

        elapsed = time.time() - start_time
        times.append(elapsed)

        logger.info(f"  Time: {elapsed:.2f} seconds")

        if result["success"]:
            summary = result["summary"]
            logger.info(f"  Detection: {summary['passed']}/{summary['total']} passed")

            if enable_quality_checks and result.get("quality_checks"):
                qc = result["quality_checks"]
                logger.info(f"  Quality issues: {qc['total_issues']}")
        else:
            logger.error(f"  Validation FAILED: {result.get('errors', [])}")

    avg_time = sum(times) / len(times) if times else 0
    min_time = min(times) if times else 0
    max_time = max(times) if times else 0

    logger.info(f"\nResults for {ocr_engine.upper()}:")
    logger.info(f"  Average: {avg_time:.2f}s")
    logger.info(f"  Min: {min_time:.2f}s")
    logger.info(f"  Max: {max_time:.2f}s")

    return {
        "engine": ocr_engine,
        "quality_checks": enable_quality_checks,
        "runs": runs,
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "times": times
    }


def compare_engines(pdf_path: str, runs: int = 3):
    """
    Compare Tesseract vs PaddleOCR performance.

    Args:
        pdf_path: Path to PDF file
        runs: Number of runs per engine
    """
    logger.info("\n" + "="*80)
    logger.info("OCR ENGINE COMPARISON (Phase 4.1)")
    logger.info("="*80)

    # Benchmark Tesseract (baseline)
    tesseract_results = benchmark_validation(
        pdf_path=pdf_path,
        ocr_engine="tesseract",
        enable_quality_checks=True,
        runs=runs
    )

    # Benchmark PaddleOCR (Phase 4.1)
    paddleocr_results = benchmark_validation(
        pdf_path=pdf_path,
        ocr_engine="paddleocr",
        enable_quality_checks=True,
        runs=runs
    )

    # Calculate improvement
    tesseract_avg = tesseract_results["avg_time"]
    paddleocr_avg = paddleocr_results["avg_time"]

    improvement = ((tesseract_avg - paddleocr_avg) / tesseract_avg) * 100
    speedup = tesseract_avg / paddleocr_avg if paddleocr_avg > 0 else 0

    logger.info("\n" + "="*80)
    logger.info("FINAL COMPARISON")
    logger.info("="*80)
    logger.info(f"Tesseract (baseline):  {tesseract_avg:.2f}s")
    logger.info(f"PaddleOCR (Phase 4.1): {paddleocr_avg:.2f}s")
    logger.info(f"\nPerformance Improvement: {improvement:.1f}%")
    logger.info(f"Speedup: {speedup:.2f}x faster")

    if paddleocr_avg < tesseract_avg:
        logger.info(f"\n✓ SUCCESS: PaddleOCR is faster by {tesseract_avg - paddleocr_avg:.2f} seconds")
    else:
        logger.warning(f"\n✗ WARNING: PaddleOCR is slower by {paddleocr_avg - tesseract_avg:.2f} seconds")

    logger.info("="*80 + "\n")

    return {
        "tesseract": tesseract_results,
        "paddleocr": paddleocr_results,
        "improvement_pct": improvement,
        "speedup": speedup
    }


def main():
    """Main benchmark entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark OCR engine performance")
    parser.add_argument("pdf_path", help="Path to PDF file to test")
    parser.add_argument("--engine", choices=["tesseract", "paddleocr", "both"],
                        default="both", help="OCR engine to benchmark")
    parser.add_argument("--runs", type=int, default=3,
                        help="Number of runs per engine (default: 3)")
    parser.add_argument("--no-quality-checks", action="store_true",
                        help="Disable quality checks (Phase 4)")

    args = parser.parse_args()

    # Validate PDF exists
    if not Path(args.pdf_path).exists():
        logger.error(f"PDF not found: {args.pdf_path}")
        sys.exit(1)

    enable_qc = not args.no_quality_checks

    if args.engine == "both":
        # Compare both engines
        compare_engines(args.pdf_path, runs=args.runs)
    else:
        # Benchmark single engine
        benchmark_validation(
            pdf_path=args.pdf_path,
            ocr_engine=args.engine,
            enable_quality_checks=enable_qc,
            runs=args.runs
        )


if __name__ == "__main__":
    main()
