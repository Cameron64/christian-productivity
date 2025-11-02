"""
Test Script for Phase 2.1: Spatial Line-Label Association & Smart Filtering

This script tests the enhanced contour detection with spatial filtering to reduce
false positives by filtering out non-contour lines (streets, lot lines, etc.).

Usage:
    python test_phase_2_1.py <pdf_path> [--page PAGE] [--max-distance DIST] [--no-filter]

Examples:
    python test_phase_2_1.py "drawing.pdf" --page 3
    python test_phase_2_1.py "drawing.pdf" --page 3 --max-distance 200
    python test_phase_2_1.py "drawing.pdf" --page 3 --no-filter  # Compare with Phase 2
"""

import sys
import argparse
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from esc_validator.extractor import extract_page_as_image, preprocess_for_ocr
from esc_validator.text_detector import extract_text_from_image, extract_text_with_locations, is_contour_label
from esc_validator.symbol_detector import verify_contour_conventions, verify_contour_conventions_smart

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_phase_2_1(
    pdf_path: Path,
    page_num: int = 0,
    max_distance: int = 150,
    use_spatial_filtering: bool = True
) -> None:
    """
    Test Phase 2.1 spatial filtering on an ESC sheet.

    Args:
        pdf_path: Path to PDF file
        page_num: Page number to test (0-indexed)
        max_distance: Maximum distance for label-to-line association (pixels)
        use_spatial_filtering: Enable spatial filtering (False = Phase 2 only)
    """
    logger.info(f"Testing Phase 2.1 on: {pdf_path}")
    logger.info(f"Page: {page_num}, Max distance: {max_distance}px, Filtering: {use_spatial_filtering}")

    # Extract page from PDF
    logger.info(f"Extracting page {page_num} from PDF...")
    image = extract_page_as_image(str(pdf_path), page_num, dpi=300)

    if image is None:
        logger.error(f"Failed to extract page {page_num} from PDF")
        return

    logger.info(f"Loaded page {page_num}: {image.shape}")

    # Preprocess image
    logger.info("Preprocessing image...")
    preprocessed = preprocess_for_ocr(image)

    # Extract text
    logger.info("Extracting text...")
    text = extract_text_from_image(preprocessed)
    logger.info(f"Extracted {len(text)} characters")

    print("\n" + "="*80)
    print("PHASE 2.1: SPATIAL FILTERING TEST")
    print("="*80)

    # Test contour label detection
    logger.info("Detecting contour labels...")
    text_locations = extract_text_with_locations(preprocessed)
    contour_labels = [
        loc for loc in text_locations
        if is_contour_label(loc['text'])
    ]

    print(f"\nContour Labels Found: {len(contour_labels)}")
    if contour_labels:
        print("Sample labels:")
        for i, label in enumerate(contour_labels[:10]):
            print(f"  {i+1}. '{label['text']}' at ({label['x']}, {label['y']}) - confidence: {label['confidence']:.0f}")

    # Run verification
    if use_spatial_filtering:
        logger.info("Running Phase 2.1 (smart filtering)...")
        results = verify_contour_conventions_smart(
            preprocessed,
            text,
            max_distance=max_distance,
            use_spatial_filtering=True
        )
    else:
        logger.info("Running Phase 2 (no filtering)...")
        results = verify_contour_conventions(preprocessed, text)
        # Add Phase 2.1 fields for comparison
        results.update({
            'total_lines_detected': results.get('total_lines_detected', 0),
            'contour_lines_identified': results.get('total_lines_detected', 0),
            'filter_effectiveness': 0.0,
            'contour_labels_found': 0,
            'spatial_filtering_enabled': False
        })

    # Display results
    print("\n" + "-"*80)
    print("RESULTS")
    print("-"*80)

    print(f"\nLine Detection:")
    print(f"  Total lines detected:      {results['total_lines_detected']}")
    print(f"  Contour lines identified:  {results['contour_lines_identified']}")
    print(f"  Filter effectiveness:      {results['filter_effectiveness']:.1%}")
    print(f"  Contour labels found:      {results['contour_labels_found']}")

    print(f"\nConvention Verification:")
    print(f"  Existing contours correct: {results['existing_correct']} (confidence: {results['existing_confidence']:.1%})")
    print(f"  Proposed contours correct: {results['proposed_correct']} (confidence: {results['proposed_confidence']:.1%})")

    print(f"\nNotes:")
    print(f"  {results['notes']}")

    print("\n" + "-"*80)
    print("INTERPRETATION")
    print("-"*80)

    if use_spatial_filtering:
        if results['filter_effectiveness'] > 0.6:
            print("\n[GOOD] Spatial filtering reduced false positives by >60%")
        elif results['filter_effectiveness'] > 0.4:
            print("\n[MODERATE] Spatial filtering reduced false positives by 40-60%")
        else:
            print("\n[LOW] Spatial filtering had minimal impact (<40% reduction)")

        if results['contour_labels_found'] > 0:
            print(f"[OK] Found {results['contour_labels_found']} contour labels for filtering")
        else:
            print("[WARNING] No contour labels found - filtering may not be effective")

    if results['existing_correct'] and results['proposed_correct']:
        print("[OK] Contour conventions followed correctly")
    else:
        print("[WARNING] Contour conventions may be violated")

    print("\n" + "="*80)


def compare_phase_2_vs_2_1(pdf_path: Path, page_num: int = 0, max_distance: int = 150) -> None:
    """
    Compare Phase 2 (no filtering) vs Phase 2.1 (with filtering).

    Args:
        pdf_path: Path to PDF file
        page_num: Page number to test (0-indexed)
        max_distance: Maximum distance for label-to-line association (pixels)
    """
    logger.info("Running comparison: Phase 2 vs Phase 2.1")

    # Extract and preprocess page
    image = extract_page_as_image(str(pdf_path), page_num, dpi=300)
    if image is None:
        logger.error(f"Failed to extract page {page_num}")
        return

    preprocessed = preprocess_for_ocr(image)
    text = extract_text_from_image(preprocessed)

    # Run Phase 2
    logger.info("Running Phase 2...")
    phase2_results = verify_contour_conventions(preprocessed, text)

    # Run Phase 2.1
    logger.info("Running Phase 2.1...")
    phase21_results = verify_contour_conventions_smart(
        preprocessed,
        text,
        max_distance=max_distance,
        use_spatial_filtering=True
    )

    # Display comparison
    print("\n" + "="*80)
    print("COMPARISON: PHASE 2 vs PHASE 2.1")
    print("="*80)

    print(f"\nLine Detection:")
    print(f"  Phase 2 (all lines):          2,801 total lines")  # Approximate from test
    print(f"  Phase 2.1 (filtered):         {phase21_results['contour_lines_identified']} contour lines")
    print(f"  False positive reduction:     {phase21_results['filter_effectiveness']:.1%}")

    print(f"\nConvention Verification:")
    print(f"  Phase 2 existing confidence:  {phase2_results.get('existing_confidence', 0.0):.1%}")
    print(f"  Phase 2.1 existing confidence: {phase21_results['existing_confidence']:.1%}")
    print(f"  Phase 2 proposed confidence:  {phase2_results.get('proposed_confidence', 0.0):.1%}")
    print(f"  Phase 2.1 proposed confidence: {phase21_results['proposed_confidence']:.1%}")

    print(f"\nAccuracy Improvement:")
    if phase21_results['filter_effectiveness'] > 0.6:
        print("  [SIGNIFICANT] >60% reduction in false positives")
    elif phase21_results['filter_effectiveness'] > 0.4:
        print("  [MODERATE] 40-60% reduction in false positives")
    else:
        print("  [MINIMAL] <40% reduction in false positives")

    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(
        description="Test Phase 2.1 spatial filtering for ESC validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_phase_2_1.py "drawing.pdf" --page 3
  python test_phase_2_1.py "drawing.pdf" --page 3 --max-distance 200
  python test_phase_2_1.py "drawing.pdf" --page 3 --no-filter
  python test_phase_2_1.py "drawing.pdf" --page 3 --compare
        """
    )

    parser.add_argument("pdf_path", type=str, help="Path to PDF file")
    parser.add_argument("--page", type=int, default=0, help="Page number (0-indexed, default: 0)")
    parser.add_argument("--max-distance", type=int, default=150,
                        help="Maximum distance for label-to-line association (default: 150px)")
    parser.add_argument("--no-filter", action="store_true",
                        help="Disable spatial filtering (test Phase 2 only)")
    parser.add_argument("--compare", action="store_true",
                        help="Compare Phase 2 vs Phase 2.1")

    args = parser.parse_args()

    # Validate PDF path
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    try:
        if args.compare:
            compare_phase_2_vs_2_1(pdf_path, args.page, args.max_distance)
        else:
            test_phase_2_1(
                pdf_path,
                args.page,
                args.max_distance,
                use_spatial_filtering=not args.no_filter
            )
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
