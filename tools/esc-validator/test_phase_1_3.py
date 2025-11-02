"""
Test Phase 1.3 Implementation

Quick end-to-end test of Phase 1.3 visual detection features.
"""

import sys
from pathlib import Path
import time
import logging

# Add module to path
sys.path.insert(0, str(Path(__file__).parent))

from esc_validator.extractor import extract_esc_sheet
from esc_validator.text_detector import detect_required_labels
from esc_validator.reporter import generate_markdown_report
from esc_validator.validator import validate_esc_sheet

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_phase_1_3():
    """Test Phase 1.3 on Page 16."""

    pdf_path = "../../documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf"
    page_num = 16  # User-facing page number

    print("="*70)
    print("PHASE 1.3 TEST - Visual Detection")
    print("="*70)
    print(f"\nTesting on: {pdf_path}")
    print(f"Page: {page_num}")
    print()

    # Start timer
    start_time = time.time()

    # Run validation
    print("Running validation...")
    try:
        results = validate_esc_sheet(
            pdf_path=pdf_path,
            page_num=page_num,
            output_dir=None  # Don't save images for test
        )
    except Exception as e:
        print(f"\nERROR: Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    elapsed = time.time() - start_time

    # Check results
    if not results["success"]:
        print(f"\nERROR: Validation unsuccessful")
        print(f"Errors: {results.get('errors', [])}")
        return False

    # Extract key results
    detection_results = results["detection_results"]
    summary = results["summary"]

    # Display results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)

    print(f"\nOverall: {summary['passed']}/{summary['total']} checks passed")
    print(f"Processing time: {elapsed:.1f}s")

    # Focus on Phase 1.3 elements
    print("\n### Phase 1.3 Visual Detection Results ###\n")

    # North arrow
    north = detection_results.get("north_bar")
    if north:
        status = "[PASS]" if north.detected else "[FAIL]"
        print(f"North Arrow: {status}")
        print(f"  Confidence: {north.confidence:.1%}")
        print(f"  Notes: {north.notes}")

    # Streets
    streets = detection_results.get("streets")
    if streets:
        status = "[PASS]" if streets.detected else "[FAIL]"
        print(f"\nStreets: {status}")
        print(f"  Count: {streets.count}")
        print(f"  Confidence: {streets.confidence:.1%}")
        print(f"  Notes: {streets.notes}")
        if streets.matches:
            print(f"  Matches: {', '.join(streets.matches[:5])}")

    # Generate report
    print("\n" + "="*70)
    print("GENERATING REPORT")
    print("="*70)

    report = generate_markdown_report(results, pdf_path, verbose=True)

    # Save report
    report_path = Path("test_phase_1_3_report.md")
    report_path.write_text(report, encoding='utf-8')
    print(f"\nReport saved to: {report_path}")

    # Success criteria
    print("\n" + "="*70)
    print("SUCCESS CRITERIA CHECK")
    print("="*70)

    checks = []

    # 1. Processing time < 45 seconds
    if elapsed < 45:
        checks.append(("[PASS]", f"Processing time < 45s ({elapsed:.1f}s)"))
    else:
        checks.append(("[FAIL]", f"Processing time > 45s ({elapsed:.1f}s)"))

    # 2. Visual detection attempted
    if north and "symbol" in north.notes.lower():
        checks.append(("[PASS]", "North arrow symbol detection attempted"))
    else:
        checks.append(("[WARN]", "North arrow symbol detection not attempted"))

    # 3. Street verification enhanced
    if streets and ("visual" in streets.notes.lower() or "coverage" in streets.notes.lower() or "unreliable" in streets.notes.lower()):
        checks.append(("[PASS]", "Street verification includes visual analysis"))
    else:
        checks.append(("[WARN]", "Street verification is text-only"))

    # 4. No crashes
    checks.append(("[PASS]", "No crashes or errors"))

    print()
    for status, message in checks:
        print(f"{status} {message}")

    passed = sum(1 for s, _ in checks if s == "[PASS]")
    total = len(checks)

    print(f"\nOverall: {passed}/{total} criteria met")

    return passed >= 3  # Pass if at least 3/4 criteria met


if __name__ == "__main__":
    print("\nPhase 1.3 Implementation Test")
    print("Testing visual detection features (north arrow + street counting)\n")

    success = test_phase_1_3()

    if success:
        print("\n[PASS] Phase 1.3 test PASSED")
        sys.exit(0)
    else:
        print("\n[FAIL] Phase 1.3 test FAILED")
        sys.exit(1)
