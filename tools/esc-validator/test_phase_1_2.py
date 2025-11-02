"""
Test Phase 1.2 improvements on Page 16.

This script tests the smart street detection and improved north bar logic.
"""

import sys
import io
from pathlib import Path

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add esc_validator to path
sys.path.insert(0, str(Path(__file__).parent))

from esc_validator.extractor import extract_page_as_image
from esc_validator.text_detector import detect_required_labels, extract_text_from_image
from esc_validator.reporter import generate_markdown_report

# Paths
PDF_PATH = "../../documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf"
PAGE_NUM = 15  # 0-indexed (Page 16 in PDF)

def main():
    print("=" * 60)
    print("Phase 1.2 Test - Page 16")
    print("=" * 60)
    print()

    # Extract page
    print(f"Extracting page {PAGE_NUM + 1} from PDF...")
    image = extract_page_as_image(PDF_PATH, PAGE_NUM, dpi=200)

    if image is None:
        print("ERROR: Failed to extract page")
        return

    print(f"✓ Page extracted: {image.shape}")
    print()

    # Run detection
    print("Running Phase 1.2 detection...")
    results = detect_required_labels(image)

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print()

    # Show results for streets and north_bar specifically
    if "streets" in results:
        r = results["streets"]
        print(f"Streets Labeled:")
        print(f"  Detected: {r.detected}")
        print(f"  Count: {r.count}")
        print(f"  Confidence: {r.confidence:.2f}")
        print(f"  Matches: {r.matches[:5]}")  # First 5
        print(f"  Notes: {r.notes}")
        print()

    if "north_bar" in results:
        r = results["north_bar"]
        print(f"North Bar:")
        print(f"  Detected: {r.detected}")
        print(f"  Count: {r.count}")
        print(f"  Confidence: {r.confidence:.2f}")
        print(f"  Notes: {r.notes}")
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total = len(results)
    detected = sum(1 for r in results.values() if r.detected)

    print(f"Total elements checked: {total}")
    print(f"Elements detected: {detected}")
    print(f"Pass rate: {detected/total:.1%}")
    print()

    # Check for false positives
    print("=" * 60)
    print("FALSE POSITIVE CHECK")
    print("=" * 60)

    has_false_positives = False

    for element, result in results.items():
        if result.count > 50:
            print(f"⚠️  {element}: {result.count} occurrences (likely false positive)")
            has_false_positives = True

    if not has_false_positives:
        print("✓ No false positives detected (no elements with >50 occurrences)")

    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
