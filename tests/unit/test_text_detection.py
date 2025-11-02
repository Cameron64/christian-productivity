"""
Unit tests for text detection module.

Tests the text_detector.py module functions in isolation.
"""

import pytest
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.esc_validator.esc_validator.text_detector import (
    is_contour_label,
    is_existing_contour_label,
    is_proposed_contour_label,
)


# ============================================================================
# Test is_contour_label() - Basic contour detection
# ============================================================================

class TestIsContourLabel:
    """Test contour label detection logic."""

    @pytest.mark.parametrize("text,expected", [
        # Valid elevation numbers
        ("250.5", True),
        ("100", True),
        ("50", True),
        ("500", True),
        ("100.0", True),
        ("250.25", True),

        # Invalid - out of range
        ("25", False),    # Too low
        ("600", False),   # Too high
        ("49", False),    # Below minimum
        ("501", False),   # Above maximum

        # Valid keywords
        ("contour", True),
        ("CONTOUR", True),
        ("Contour", True),
        ("existing", True),
        ("EXISTING", True),
        ("proposed", True),
        ("PROPOSED", True),
        ("elev", True),
        ("ELEV", True),
        ("elevation", True),
        ("ex", True),
        ("prop", True),

        # Invalid - not contour related
        ("abc", False),
        ("street", False),
        ("legend", False),
        ("scale", False),
        ("12345", False),  # Too large
        ("", False),       # Empty string
    ])
    def test_is_contour_label_with_various_inputs(self, text, expected):
        """Should correctly identify contour labels."""
        assert is_contour_label(text) == expected, \
            f"Expected is_contour_label('{text}') to be {expected}"

    def test_is_contour_label_with_mixed_text(self):
        """Should detect contour keywords in mixed text."""
        assert is_contour_label("existing contour")
        assert is_contour_label("proposed grade")
        assert is_contour_label("elev 250")

    def test_is_contour_label_case_insensitive(self):
        """Should be case insensitive for keywords."""
        assert is_contour_label("CONTOUR")
        assert is_contour_label("contour")
        assert is_contour_label("CoNtOuR")


# ============================================================================
# Test is_existing_contour_label() - Existing contour detection
# ============================================================================

class TestIsExistingContourLabel:
    """Test existing contour label detection."""

    @pytest.mark.parametrize("text,expected", [
        # Valid existing contour labels
        ("existing", True),
        ("EXISTING", True),
        ("Existing Contour", True),
        ("ex", True),
        ("EX", True),
        ("existing grade", True),

        # Invalid - proposed or other
        ("proposed", False),
        ("PROPOSED", False),
        ("prop", False),
        ("new", False),
        ("future", False),

        # Numeric labels should not be existing-specific
        ("250", False),
        ("100.5", False),
    ])
    def test_is_existing_contour_label(self, text, expected):
        """Should correctly identify existing contour labels."""
        assert is_existing_contour_label(text) == expected, \
            f"Expected is_existing_contour_label('{text}') to be {expected}"

    def test_is_existing_contour_label_case_insensitive(self):
        """Should be case insensitive."""
        assert is_existing_contour_label("EXISTING")
        assert is_existing_contour_label("existing")
        assert is_existing_contour_label("ExIsTiNg")


# ============================================================================
# Test is_proposed_contour_label() - Proposed contour detection
# ============================================================================

class TestIsProposedContourLabel:
    """Test proposed contour label detection."""

    @pytest.mark.parametrize("text,expected", [
        # Valid proposed contour labels
        ("proposed", True),
        ("PROPOSED", True),
        ("Proposed Contour", True),
        ("prop", True),
        ("PROP", True),
        ("proposed grade", True),

        # Invalid - existing or other
        ("existing", False),
        ("EXISTING", False),
        ("ex", False),
        ("old", False),
        ("current", False),

        # Numeric labels should not be proposed-specific
        ("250", False),
        ("100.5", False),
    ])
    def test_is_proposed_contour_label(self, text, expected):
        """Should correctly identify proposed contour labels."""
        assert is_proposed_contour_label(text) == expected, \
            f"Expected is_proposed_contour_label('{text}') to be {expected}"

    def test_is_proposed_contour_label_case_insensitive(self):
        """Should be case insensitive."""
        assert is_proposed_contour_label("PROPOSED")
        assert is_proposed_contour_label("proposed")
        assert is_proposed_contour_label("PrOpOsEd")


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string(self):
        """Should handle empty strings gracefully."""
        assert not is_contour_label("")
        assert not is_existing_contour_label("")
        assert not is_proposed_contour_label("")

    def test_whitespace_only(self):
        """Should handle whitespace-only strings."""
        assert not is_contour_label("   ")
        assert not is_contour_label("\t")
        assert not is_contour_label("\n")

    def test_special_characters(self):
        """Should handle special characters."""
        assert not is_contour_label("@#$%")
        assert not is_contour_label("!?&*")

    def test_very_long_string(self):
        """Should handle very long strings."""
        long_text = "a" * 10000
        assert not is_contour_label(long_text)

    def test_unicode_characters(self):
        """Should handle unicode characters."""
        assert not is_contour_label("日本語")
        assert not is_contour_label("émoji")


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.performance
class TestPerformance:
    """Test performance of text detection functions."""

    def test_is_contour_label_is_fast(self, benchmark):
        """Should execute in <1ms."""
        result = benchmark(is_contour_label, "250.5")
        assert result is True
        # Benchmark automatically records timing

    def test_batch_detection_is_fast(self, benchmark):
        """Should process 1000 labels in <100ms."""
        labels = ["250.5", "existing", "proposed", "street", "legend"] * 200

        def batch_detect():
            return [is_contour_label(label) for label in labels]

        results = benchmark(batch_detect)
        assert len(results) == 1000
