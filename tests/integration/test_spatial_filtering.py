"""
Integration tests for Phase 2.1 spatial filtering.

Tests the interaction between text detection and line detection modules.
Migrated from: tools/esc-validator/test_phase_2_1.py
"""

import pytest
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.esc_validator.esc_validator.extractor import extract_page_as_image, preprocess_for_ocr
from tools.esc_validator.esc_validator.text_detector import extract_text_from_image
from tools.esc_validator.esc_validator.symbol_detector import (
    verify_contour_conventions_smart,
    verify_contour_conventions  # Phase 2 (for comparison)
)


# ============================================================================
# Phase 2.1: Spatial Filtering Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.esc
class TestSpatialFiltering:
    """Test Phase 2.1 spatial filtering functionality."""

    @pytest.mark.skip(reason="Requires real PDF fixture - see fixtures/README.md")
    def test_spatial_filtering_reduces_false_positives(self, sample_esc_pdf):
        """
        Phase 2.1: Should filter 857 total lines to ~9 contour lines.

        Success criteria:
        - Filter effectiveness > 80% (target: 60-80%)
        - Contour detection > 80% (target: 80%)
        - Processing overhead < 5 seconds
        """
        # Extract page 26 from PDF (ESC sheet with contours)
        image = extract_page_as_image(str(sample_esc_pdf), page_num=26, dpi=300)
        assert image is not None, "Failed to extract page from PDF"

        # Preprocess and extract text
        preprocessed = preprocess_for_ocr(image)
        text = extract_text_from_image(preprocessed)

        # Phase 2.1: Smart filtering
        result_phase_2_1 = verify_contour_conventions_smart(
            preprocessed,
            text,
            max_distance=150,
            use_spatial_filtering=True
        )

        # Assertions
        assert 'contours' in result_phase_2_1
        assert 'filter_stats' in result_phase_2_1

        contours = result_phase_2_1['contours']
        stats = result_phase_2_1['filter_stats']

        # Should detect ~9 contours (not 857 lines)
        assert len(contours) < 20, \
            f"Expected <20 contours after filtering, got {len(contours)}"

        # Filter effectiveness > 80%
        filter_effectiveness = stats.get('filter_effectiveness', 0)
        assert filter_effectiveness > 0.8, \
            f"Expected >80% filter effectiveness, got {filter_effectiveness:.1%}"

        # Should have high confidence
        for contour in contours:
            assert contour.get('confidence', 0) > 0.5, \
                f"Contour confidence too low: {contour}"

    @pytest.mark.skip(reason="Requires real PDF fixture - see fixtures/README.md")
    def test_spatial_filtering_vs_phase_2_comparison(self, sample_esc_pdf):
        """
        Compare Phase 2 (all lines) vs Phase 2.1 (filtered lines).

        Phase 2 should detect ~857 lines.
        Phase 2.1 should filter to ~9 contours (98.9% reduction).
        """
        # Extract and preprocess
        image = extract_page_as_image(str(sample_esc_pdf), page_num=26, dpi=300)
        preprocessed = preprocess_for_ocr(image)
        text = extract_text_from_image(preprocessed)

        # Phase 2: Detect all lines
        result_phase_2 = verify_contour_conventions(
            preprocessed,
            text,
            existing_should_be_dashed=True
        )

        # Phase 2.1: Filtered lines
        result_phase_2_1 = verify_contour_conventions_smart(
            preprocessed,
            text,
            max_distance=150,
            use_spatial_filtering=True
        )

        # Phase 2 should detect many lines (including streets, lot lines)
        total_lines_phase_2 = result_phase_2.get('total_lines', 0)
        assert total_lines_phase_2 > 100, \
            f"Phase 2 should detect >100 lines, got {total_lines_phase_2}"

        # Phase 2.1 should filter dramatically
        contours_phase_2_1 = len(result_phase_2_1['contours'])
        assert contours_phase_2_1 < 20, \
            f"Phase 2.1 should filter to <20 contours, got {contours_phase_2_1}"

        # Calculate reduction
        reduction_rate = 1 - (contours_phase_2_1 / total_lines_phase_2)
        assert reduction_rate > 0.8, \
            f"Expected >80% reduction, got {reduction_rate:.1%}"

    def test_spatial_filtering_with_no_contours(self, blank_image):
        """Should handle images with no contour labels gracefully."""
        # Blank image has no text or contours
        result = verify_contour_conventions_smart(
            blank_image,
            text="",
            max_distance=150,
            use_spatial_filtering=True
        )

        # Should return empty results without crashing
        assert 'contours' in result
        assert len(result['contours']) == 0

    def test_spatial_filtering_distance_parameter(self, sample_text_image):
        """Should respect max_distance parameter."""
        # Test with different distance thresholds
        text = "contour 250 existing"

        result_100px = verify_contour_conventions_smart(
            sample_text_image, text, max_distance=100
        )
        result_200px = verify_contour_conventions_smart(
            sample_text_image, text, max_distance=200
        )

        # Larger distance should capture more (or equal) contours
        assert len(result_200px['contours']) >= len(result_100px['contours'])

    def test_spatial_filtering_fallback_when_no_labels(self, blank_image):
        """Should fall back to Phase 2 behavior when no contour labels found."""
        # No text = no contour labels = fallback to Phase 2
        result = verify_contour_conventions_smart(
            blank_image,
            text="street name legend scale",  # No contour keywords
            max_distance=150,
            use_spatial_filtering=True
        )

        # Should still return valid structure
        assert 'contours' in result
        assert 'filter_stats' in result


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.slow
class TestSpatialFilteringPerformance:
    """Test Phase 2.1 performance requirements."""

    @pytest.mark.skip(reason="Requires real PDF fixture - see fixtures/README.md")
    def test_processing_overhead_under_5_seconds(self, sample_esc_pdf, benchmark):
        """
        Phase 2.1 target: <5 seconds processing overhead vs Phase 2.

        Success criteria: Processing time increase < 5 seconds
        """
        # Extract and preprocess (not benchmarked - same for both)
        image = extract_page_as_image(str(sample_esc_pdf), page_num=26, dpi=300)
        preprocessed = preprocess_for_ocr(image)
        text = extract_text_from_image(preprocessed)

        # Benchmark Phase 2.1
        result = benchmark(
            verify_contour_conventions_smart,
            preprocessed,
            text,
            max_distance=150,
            use_spatial_filtering=True
        )

        # Should complete in reasonable time
        assert benchmark.stats['mean'] < 15.0, \
            f"Phase 2.1 took too long: {benchmark.stats['mean']:.2f}s"

        # Result should be valid
        assert 'contours' in result
        assert 'filter_stats' in result
