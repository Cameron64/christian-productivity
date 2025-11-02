"""
Unit tests for OCR engine abstraction (Phase 4.1).

Tests the OCR engine abstraction layer that supports multiple OCR backends:
- PaddleOCR (primary, deep learning-based)
- Tesseract (fallback, rule-based)

File: tests/unit/test_ocr_engine.py
Created: 2025-11-02
Phase: 4.1 (PaddleOCR Integration)
"""

import sys
from pathlib import Path
import pytest
import numpy as np
import cv2

# Add tools path for imports
TOOLS_PATH = Path(__file__).parent.parent.parent / "tools" / "esc-validator"
sys.path.insert(0, str(TOOLS_PATH))

from esc_validator.ocr_engine import (
    OCRResult,
    OCREngine,
    PaddleOCREngine,
    TesseractOCREngine,
    get_ocr_engine,
    set_ocr_cache,
    get_ocr_cache,
    clear_ocr_cache,
)


# ============================================================================
# Test Suite 1: OCR Engine Abstraction
# ============================================================================

class TestOCREngineAbstraction:
    """Test OCR engine selection and initialization."""

    def test_paddleocr_initialization(self):
        """Test PaddleOCR engine initializes successfully."""
        engine = get_ocr_engine("paddleocr")
        assert engine.get_engine_name() == "PaddleOCR"
        assert isinstance(engine, PaddleOCREngine)

    def test_tesseract_initialization(self):
        """Test Tesseract engine initializes successfully."""
        engine = get_ocr_engine("tesseract")
        assert engine.get_engine_name() == "Tesseract"
        assert isinstance(engine, TesseractOCREngine)

    def test_invalid_engine_name(self):
        """Test invalid engine name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown OCR engine"):
            get_ocr_engine("invalid_engine")

    def test_default_engine_is_paddleocr(self):
        """Test that default engine is PaddleOCR."""
        engine = get_ocr_engine()  # No argument
        assert engine.get_engine_name() == "PaddleOCR"


# ============================================================================
# Test Suite 2: OCRResult Dataclass
# ============================================================================

class TestOCRResult:
    """Test OCRResult dataclass properties and methods."""

    def test_ocr_result_format(self):
        """Test OCRResult has correct properties."""
        result = OCRResult(
            text="TEST",
            confidence=85.5,
            bbox=(10, 20, 100, 50)
        )

        assert result.text == "TEST"
        assert result.confidence == 85.5
        assert result.bbox == (10, 20, 100, 50)

    def test_ocr_result_coordinates(self):
        """Test OCRResult coordinate properties."""
        result = OCRResult(
            text="TEST",
            confidence=90.0,
            bbox=(10, 20, 100, 50)
        )

        assert result.x == 10
        assert result.y == 20
        assert result.width == 90  # 100 - 10
        assert result.height == 30  # 50 - 20

    def test_ocr_result_center(self):
        """Test OCRResult center calculation."""
        result = OCRResult(
            text="TEST",
            confidence=90.0,
            bbox=(10, 20, 100, 50)
        )

        assert result.center_x == 55.0  # (10 + 100) / 2
        assert result.center_y == 35.0  # (20 + 50) / 2

    def test_ocr_result_with_zero_confidence(self):
        """Test OCRResult with zero confidence."""
        result = OCRResult(
            text="UNCERTAIN",
            confidence=0.0,
            bbox=(0, 0, 50, 30)
        )

        assert result.confidence == 0.0
        assert result.text == "UNCERTAIN"

    def test_ocr_result_with_max_confidence(self):
        """Test OCRResult with maximum confidence."""
        result = OCRResult(
            text="CERTAIN",
            confidence=100.0,
            bbox=(0, 0, 50, 30)
        )

        assert result.confidence == 100.0
        assert result.text == "CERTAIN"


# ============================================================================
# Test Suite 3: OCR Text Extraction
# ============================================================================

class TestOCRTextExtraction:
    """Test OCR text extraction from images."""

    @pytest.fixture
    def simple_text_image(self, sample_text_image):
        """Use sample_text_image fixture from conftest."""
        # Convert to grayscale for OCR
        return cv2.cvtColor(sample_text_image, cv2.COLOR_RGB2GRAY)

    def test_paddleocr_text_extraction(self, simple_text_image):
        """Test PaddleOCR extracts text from test image."""
        engine = get_ocr_engine("paddleocr")
        results = engine.extract_text(simple_text_image)

        # Should find at least one text element
        assert len(results) > 0

        # All results should be OCRResult objects
        assert all(isinstance(r, OCRResult) for r in results)

        # Confidence should be in valid range
        assert all(0 <= r.confidence <= 100 for r in results)

        # Text should not be empty
        assert all(len(r.text.strip()) > 0 for r in results)

        # Bounding boxes should be valid
        for r in results:
            assert r.width > 0
            assert r.height > 0

    def test_tesseract_text_extraction(self, simple_text_image):
        """Test Tesseract extracts text from test image."""
        engine = get_ocr_engine("tesseract")
        results = engine.extract_text(simple_text_image)

        # Should find at least one text element
        assert len(results) > 0

        # All results should be OCRResult objects
        assert all(isinstance(r, OCRResult) for r in results)

    def test_confidence_filtering(self, simple_text_image):
        """Test min_confidence parameter filters results."""
        engine = get_ocr_engine("paddleocr")

        # Get all results
        all_results = engine.extract_text(simple_text_image, min_confidence=0.0)

        # Get filtered results
        filtered_results = engine.extract_text(simple_text_image, min_confidence=70.0)

        # Filtered should have <= results
        assert len(filtered_results) <= len(all_results)

        # All filtered results should meet threshold
        assert all(r.confidence >= 70.0 for r in filtered_results)

    def test_language_parameter(self, simple_text_image):
        """Test language parameter is accepted."""
        engine = get_ocr_engine("paddleocr")

        # Should not raise error
        results = engine.extract_text(simple_text_image, lang="eng")
        assert len(results) >= 0

    def test_empty_image(self):
        """Test OCR on empty white image."""
        # Create blank white image
        blank = np.ones((500, 500), dtype=np.uint8) * 255

        engine = get_ocr_engine("paddleocr")
        results = engine.extract_text(blank)

        # Should return empty list (no text found)
        assert len(results) == 0


# ============================================================================
# Test Suite 4: OCR Caching
# ============================================================================

class TestOCRCaching:
    """Test OCR result caching functionality."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_ocr_cache()

    def teardown_method(self):
        """Clear cache after each test."""
        clear_ocr_cache()

    def test_cache_set_and_get(self):
        """Test OCR cache stores and retrieves results."""
        test_results = [
            OCRResult("TEST1", 90.0, (0, 0, 100, 50)),
            OCRResult("TEST2", 85.0, (100, 0, 200, 50))
        ]

        set_ocr_cache(test_results)
        cached = get_ocr_cache()

        assert cached is not None
        assert len(cached) == 2
        assert cached[0].text == "TEST1"
        assert cached[1].text == "TEST2"

    def test_cache_clear(self):
        """Test cache clears successfully."""
        test_results = [OCRResult("TEST", 90.0, (0, 0, 100, 50))]

        set_ocr_cache(test_results)
        assert get_ocr_cache() is not None

        clear_ocr_cache()
        assert get_ocr_cache() is None

    def test_cache_isolation(self):
        """Test cache starts empty in new test."""
        # Should start empty (cleared by setup_method)
        assert get_ocr_cache() is None

    def test_cache_overwrites(self):
        """Test setting cache overwrites previous value."""
        results1 = [OCRResult("FIRST", 90.0, (0, 0, 100, 50))]
        results2 = [OCRResult("SECOND", 85.0, (10, 10, 110, 60))]

        set_ocr_cache(results1)
        assert get_ocr_cache()[0].text == "FIRST"

        set_ocr_cache(results2)
        cached = get_ocr_cache()
        assert len(cached) == 1
        assert cached[0].text == "SECOND"

    def test_cache_empty_list(self):
        """Test caching empty list."""
        set_ocr_cache([])
        cached = get_ocr_cache()

        assert cached is not None
        assert len(cached) == 0

    def test_cache_large_result_set(self):
        """Test caching large number of results."""
        # Simulate many OCR detections
        large_results = [
            OCRResult(f"TEXT_{i}", 80.0 + i % 20, (i * 10, i * 5, (i + 1) * 10, (i + 1) * 5))
            for i in range(200)
        ]

        set_ocr_cache(large_results)
        cached = get_ocr_cache()

        assert cached is not None
        assert len(cached) == 200
        assert cached[0].text == "TEXT_0"
        assert cached[199].text == "TEXT_199"


# ============================================================================
# Test Suite 5: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_ocr_result_negative_bbox(self):
        """Test OCRResult with negative coordinates."""
        # OpenCV can sometimes produce negative coordinates
        result = OCRResult(
            text="EDGE",
            confidence=75.0,
            bbox=(-10, -5, 50, 30)
        )

        assert result.x == -10
        assert result.y == -5
        # Width/height still calculated correctly
        assert result.width == 60  # 50 - (-10)
        assert result.height == 35  # 30 - (-5)

    def test_ocr_result_zero_area(self):
        """Test OCRResult with zero-area bounding box."""
        result = OCRResult(
            text="POINT",
            confidence=50.0,
            bbox=(10, 20, 10, 20)  # Same start and end
        )

        assert result.width == 0
        assert result.height == 0

    def test_engine_with_invalid_image(self):
        """Test OCR engine with invalid image input."""
        engine = get_ocr_engine("paddleocr")

        # None should be handled gracefully
        with pytest.raises((TypeError, AttributeError)):
            engine.extract_text(None)

    def test_engine_with_corrupted_image(self):
        """Test OCR engine with corrupted image data."""
        engine = get_ocr_engine("paddleocr")

        # Random noise (not a real image structure)
        noise = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        # Should not crash (may return empty results)
        results = engine.extract_text(noise)
        assert isinstance(results, list)


# ============================================================================
# Test Suite 6: Engine Comparison
# ============================================================================

class TestEngineComparison:
    """Compare PaddleOCR and Tesseract results."""

    def test_engines_produce_similar_results(self, sample_text_image):
        """Test both engines produce similar text counts."""
        grayscale = cv2.cvtColor(sample_text_image, cv2.COLOR_RGB2GRAY)

        paddle_engine = get_ocr_engine("paddleocr")
        tesseract_engine = get_ocr_engine("tesseract")

        paddle_results = paddle_engine.extract_text(grayscale)
        tesseract_results = tesseract_engine.extract_text(grayscale)

        # Both should find at least some text
        assert len(paddle_results) > 0
        assert len(tesseract_results) > 0

        # Result counts should be in same ballpark (within 50%)
        ratio = len(paddle_results) / len(tesseract_results)
        assert 0.5 <= ratio <= 2.0

    def test_both_engines_have_same_interface(self):
        """Test both engines implement the same interface."""
        paddle = get_ocr_engine("paddleocr")
        tesseract = get_ocr_engine("tesseract")

        # Both should have extract_text method
        assert hasattr(paddle, "extract_text")
        assert hasattr(tesseract, "extract_text")

        # Both should have get_engine_name method
        assert hasattr(paddle, "get_engine_name")
        assert hasattr(tesseract, "get_engine_name")

        # Names should be different
        assert paddle.get_engine_name() != tesseract.get_engine_name()


# ============================================================================
# Performance Markers
# ============================================================================

@pytest.mark.slow
class TestOCRPerformance:
    """Performance tests for OCR engines (marked as slow)."""

    def test_paddleocr_reasonable_speed(self, sample_text_image):
        """Test PaddleOCR completes in reasonable time."""
        import time

        grayscale = cv2.cvtColor(sample_text_image, cv2.COLOR_RGB2GRAY)
        engine = get_ocr_engine("paddleocr")

        start = time.time()
        results = engine.extract_text(grayscale)
        elapsed = time.time() - start

        # Should complete in < 5 seconds on simple image
        assert elapsed < 5.0
        assert len(results) > 0

    def test_cache_hit_is_fast(self, sample_text_image):
        """Test cache hit is significantly faster than OCR."""
        import time

        grayscale = cv2.cvtColor(sample_text_image, cv2.COLOR_RGB2GRAY)
        engine = get_ocr_engine("paddleocr")

        # First call - no cache
        clear_ocr_cache()
        start1 = time.time()
        results1 = engine.extract_text(grayscale)
        time1 = time.time() - start1

        # Cache the results
        set_ocr_cache(results1)

        # Second call - use cache (simulate)
        start2 = time.time()
        cached_results = get_ocr_cache()
        time2 = time.time() - start2

        # Cache retrieval should be nearly instant (< 0.01s)
        assert time2 < 0.01
        assert len(cached_results) == len(results1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
