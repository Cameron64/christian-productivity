#!/usr/bin/env python3
"""
Test Phase 2: Line Type Detection

Tests the line detection and classification functionality added in Phase 2.
"""

import sys
from pathlib import Path
import cv2
import numpy as np

# Configure console encoding for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add esc_validator to path
sys.path.insert(0, str(Path(__file__).parent))

from esc_validator.symbol_detector import (
    classify_line_type,
    detect_contour_lines,
    verify_contour_conventions
)
from esc_validator.text_detector import extract_text_from_image


def test_line_classification():
    """Test basic line classification."""
    print("=" * 60)
    print("TEST 1: Line Classification")
    print("=" * 60)

    # Create test images with solid and dashed lines
    img_size = (500, 500)

    # Solid line image
    solid_img = np.zeros(img_size, dtype=np.uint8)
    cv2.line(solid_img, (50, 250), (450, 250), 255, 2)

    # Dashed line image (simulate with multiple segments)
    dashed_img = np.zeros(img_size, dtype=np.uint8)
    for x in range(50, 450, 40):
        cv2.line(dashed_img, (x, 250), (x+20, 250), 255, 2)

    # Test solid line
    solid_line = np.array([50, 250, 450, 250])
    line_type, confidence = classify_line_type(solid_line, solid_img)
    print(f"\nSolid line test:")
    print(f"  Detected type: {line_type}")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  ✓ PASS" if line_type == "solid" else f"  ✗ FAIL")

    # Test dashed line
    dashed_line = np.array([50, 250, 450, 250])
    line_type, confidence = classify_line_type(dashed_line, dashed_img)
    print(f"\nDashed line test:")
    print(f"  Detected type: {line_type}")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  ✓ PASS" if line_type == "dashed" else f"  ✗ FAIL")


def test_contour_detection(image_path: str):
    """Test contour line detection on real image."""
    print("\n" + "=" * 60)
    print("TEST 2: Contour Line Detection")
    print("=" * 60)

    # Load image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"ERROR: Could not load image: {image_path}")
        return

    print(f"\nImage: {Path(image_path).name}")
    print(f"Size: {image.shape[1]}x{image.shape[0]}")

    # Detect contour lines
    solid_lines, dashed_lines = detect_contour_lines(image, classify_types=True)

    print(f"\nResults:")
    print(f"  Solid lines detected: {len(solid_lines)}")
    print(f"  Dashed lines detected: {len(dashed_lines)}")

    # Show confidence scores
    if solid_lines:
        avg_solid_conf = np.mean([conf for _, conf in solid_lines])
        print(f"  Solid lines avg confidence: {avg_solid_conf:.2f}")

    if dashed_lines:
        avg_dashed_conf = np.mean([conf for _, conf in dashed_lines])
        print(f"  Dashed lines avg confidence: {avg_dashed_conf:.2f}")


def test_contour_verification(image_path: str):
    """Test full contour convention verification."""
    print("\n" + "=" * 60)
    print("TEST 3: Contour Convention Verification")
    print("=" * 60)

    # Load image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"ERROR: Could not load image: {image_path}")
        return

    print(f"\nImage: {Path(image_path).name}")

    # Extract text
    text = extract_text_from_image(image)
    print(f"Extracted {len(text)} characters of text")

    # Verify contour conventions
    results = verify_contour_conventions(image, text)

    print(f"\nResults:")
    print(f"  Existing contours correct: {results['existing_correct']}")
    print(f"  Existing confidence: {results['existing_confidence']:.2f}")
    print(f"  Proposed contours correct: {results['proposed_correct']}")
    print(f"  Proposed confidence: {results['proposed_confidence']:.2f}")
    print(f"  Notes: {results['notes']}")

    # Overall assessment
    if results['existing_correct'] and results['proposed_correct']:
        print("\n✓ PASS: Contour conventions followed")
    else:
        print("\n⚠ WARNING: Contour convention issues detected")


def test_full_integration(pdf_path: str):
    """Test Phase 2 integration with full validator."""
    print("\n" + "=" * 60)
    print("TEST 4: Full Integration with Validator")
    print("=" * 60)

    from esc_validator import validate_esc_sheet

    print(f"\nPDF: {Path(pdf_path).name}")
    print("Running validation with line detection enabled...")

    # Run validation with Phase 2 enabled
    results = validate_esc_sheet(
        pdf_path=pdf_path,
        enable_line_detection=True
    )

    if not results["success"]:
        print("\n✗ FAIL: Validation failed")
        for error in results.get("errors", []):
            print(f"  ERROR: {error}")
        return

    print(f"\n✓ Validation completed successfully")
    print(f"  Page: {results['page_num'] + 1}")
    print(f"  Checks passed: {results['summary']['passed']}/{results['summary']['total']}")

    # Check if line verification was performed
    if "line_verification" in results:
        line_results = results["line_verification"]
        print(f"\nLine Verification Results:")
        print(f"  {line_results['notes']}")

        if line_results['existing_correct'] and line_results['proposed_correct']:
            print("  ✓ PASS: All contour line types correct")
        else:
            print("  ⚠ WARNING: Line type issues detected")
    else:
        print("\n⚠ Line verification not performed")


def main():
    """Run all Phase 2 tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Phase 2 line detection")
    parser.add_argument("--image", help="Path to ESC sheet image for testing")
    parser.add_argument("--pdf", help="Path to PDF for integration testing")
    parser.add_argument("--all", action="store_true", help="Run all tests")

    args = parser.parse_args()

    print("\nESC Validator - Phase 2 Testing")
    print("=" * 60)

    # Test 1: Basic line classification (always run)
    test_line_classification()

    # Test 2-3: Image-based tests (if image provided)
    if args.image or args.all:
        if args.image:
            image_path = args.image
        else:
            # Try to find a test image
            test_dir = Path(__file__).parent / "test_output"
            images = list(test_dir.glob("*_preprocessed.png"))
            if images:
                image_path = str(images[0])
                print(f"\nUsing test image: {Path(image_path).name}")
            else:
                print("\nNo test image found. Skipping image tests.")
                print("Use --image flag to specify an image.")
                image_path = None

        if image_path:
            test_contour_detection(image_path)
            test_contour_verification(image_path)

    # Test 4: Full integration (if PDF provided)
    if args.pdf:
        test_full_integration(args.pdf)
    elif args.all:
        print("\n" + "=" * 60)
        print("Skipping integration test (no PDF specified)")
        print("Use --pdf flag to test full integration")

    print("\n" + "=" * 60)
    print("Phase 2 testing complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
