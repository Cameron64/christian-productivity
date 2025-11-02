"""
Unit Tests for Quality Checker (Phase 4)

Tests overlapping label detection and spatial validation logic.
"""

import sys
from pathlib import Path
import pytest
import numpy as np

# Add tools/esc-validator to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools" / "esc-validator"))

from esc_validator.quality_checker import (
    BoundingBox,
    TextElement,
    OverlapIssue,
    ProximityIssue,
    calculate_bbox_intersection,
    calculate_overlap_percentage,
    classify_overlap_severity,
    detect_overlapping_labels,
    classify_label_type,
    euclidean_distance,
    find_nearest_feature_distance,
    validate_label_proximity,
    QualityChecker
)


class TestBoundingBox:
    """Test BoundingBox dataclass and properties."""

    def test_center_x(self):
        """Test center_x property calculation."""
        bbox = BoundingBox(x=100, y=200, width=50, height=30)
        assert bbox.center_x == 125.0  # 100 + 50/2

    def test_center_y(self):
        """Test center_y property calculation."""
        bbox = BoundingBox(x=100, y=200, width=50, height=30)
        assert bbox.center_y == 215.0  # 200 + 30/2

    def test_area(self):
        """Test area property calculation."""
        bbox = BoundingBox(x=100, y=200, width=50, height=30)
        assert bbox.area == 1500  # 50 * 30


class TestBboxIntersection:
    """Test bounding box intersection calculations."""

    def test_overlapping_boxes(self):
        """Test intersection calculation for overlapping boxes."""
        bbox1 = BoundingBox(x=100, y=100, width=50, height=20)
        bbox2 = BoundingBox(x=120, y=105, width=50, height=20)

        result = calculate_bbox_intersection(bbox1, bbox2)

        assert result is not None
        assert result.x == 120
        assert result.y == 105
        assert result.width == 30  # 150 - 120
        assert result.height == 15  # 120 - 105

    def test_non_overlapping_boxes(self):
        """Test intersection returns None for non-overlapping boxes."""
        bbox1 = BoundingBox(x=100, y=100, width=50, height=20)
        bbox2 = BoundingBox(x=200, y=200, width=50, height=20)

        result = calculate_bbox_intersection(bbox1, bbox2)

        assert result is None

    def test_touching_boxes_no_overlap(self):
        """Test boxes that touch at edges don't count as overlapping."""
        bbox1 = BoundingBox(x=100, y=100, width=50, height=20)
        bbox2 = BoundingBox(x=150, y=100, width=50, height=20)  # Touching right edge

        result = calculate_bbox_intersection(bbox1, bbox2)

        # Edges touching but no area overlap
        assert result is None

    def test_contained_box(self):
        """Test when one box is completely inside another."""
        bbox1 = BoundingBox(x=100, y=100, width=100, height=100)  # Large
        bbox2 = BoundingBox(x=125, y=125, width=20, height=20)    # Small, inside

        result = calculate_bbox_intersection(bbox1, bbox2)

        assert result is not None
        assert result.x == 125
        assert result.y == 125
        assert result.width == 20
        assert result.height == 20


class TestOverlapPercentage:
    """Test overlap percentage calculations."""

    def test_50_percent_overlap(self):
        """Test 50% overlap calculation."""
        bbox1 = BoundingBox(x=100, y=100, width=40, height=20)  # Area = 800
        bbox2 = BoundingBox(x=120, y=100, width=40, height=20)  # Area = 800
        intersection = BoundingBox(x=120, y=100, width=20, height=20)  # Area = 400

        overlap = calculate_overlap_percentage(bbox1, bbox2, intersection)

        assert overlap == 50.0  # 400 / 800 = 50%

    def test_100_percent_overlap(self):
        """Test complete overlap (one box inside another)."""
        bbox1 = BoundingBox(x=100, y=100, width=100, height=100)  # Large
        bbox2 = BoundingBox(x=125, y=125, width=20, height=20)    # Small, inside
        intersection = BoundingBox(x=125, y=125, width=20, height=20)  # Same as bbox2

        overlap = calculate_overlap_percentage(bbox1, bbox2, intersection)

        assert overlap == 100.0  # Smaller box completely overlapped

    def test_25_percent_overlap(self):
        """Test 25% overlap."""
        bbox1 = BoundingBox(x=100, y=100, width=40, height=40)  # Area = 1600
        bbox2 = BoundingBox(x=120, y=120, width=40, height=40)  # Area = 1600
        intersection = BoundingBox(x=120, y=120, width=20, height=20)  # Area = 400

        overlap = calculate_overlap_percentage(bbox1, bbox2, intersection)

        assert overlap == 25.0  # 400 / 1600 = 25%

    def test_zero_area_box(self):
        """Test handling of zero-area boxes."""
        bbox1 = BoundingBox(x=100, y=100, width=0, height=20)  # Zero area
        bbox2 = BoundingBox(x=100, y=100, width=40, height=20)
        intersection = BoundingBox(x=100, y=100, width=0, height=20)

        overlap = calculate_overlap_percentage(bbox1, bbox2, intersection)

        assert overlap == 0.0


class TestOverlapSeverity:
    """Test overlap severity classification."""

    def test_critical_overlap(self):
        """Test critical severity (>50%)."""
        assert classify_overlap_severity(75.0) == "critical"
        assert classify_overlap_severity(51.0) == "critical"
        assert classify_overlap_severity(100.0) == "critical"

    def test_warning_overlap(self):
        """Test warning severity (20-50%)."""
        assert classify_overlap_severity(45.0) == "warning"
        assert classify_overlap_severity(25.0) == "warning"
        assert classify_overlap_severity(50.0) == "warning"
        assert classify_overlap_severity(20.1) == "warning"

    def test_minor_overlap(self):
        """Test minor severity (<20%)."""
        assert classify_overlap_severity(15.0) == "minor"
        assert classify_overlap_severity(5.0) == "minor"
        assert classify_overlap_severity(0.1) == "minor"


class TestDetectOverlappingLabels:
    """Test overlapping label detection algorithm."""

    def test_no_overlaps(self):
        """Test with well-separated text elements."""
        elements = [
            TextElement("SCE #1", BoundingBox(100, 100, 50, 20), 85.0),
            TextElement("SCE #2", BoundingBox(200, 200, 50, 20), 85.0),
            TextElement("SCE #3", BoundingBox(300, 300, 50, 20), 85.0),
        ]

        overlaps = detect_overlapping_labels(elements, min_confidence=40.0)

        assert len(overlaps) == 0

    def test_single_critical_overlap(self):
        """Test detection of critical overlap (>50%)."""
        elements = [
            TextElement("EX. 635.0", BoundingBox(100, 100, 50, 20), 85.0),
            TextElement("PROP. 636.0", BoundingBox(110, 105, 50, 20), 85.0),  # Heavy overlap
        ]

        overlaps = detect_overlapping_labels(elements, min_confidence=40.0)

        assert len(overlaps) == 1
        assert overlaps[0].severity == "critical"
        assert overlaps[0].overlap_percent > 50

    def test_warning_level_overlap(self):
        """Test detection of warning-level overlap (20-50%)."""
        elements = [
            TextElement("LOT 1", BoundingBox(100, 100, 40, 20), 85.0),
            TextElement("BLOCK 2", BoundingBox(120, 105, 40, 20), 85.0),  # Partial overlap
        ]

        overlaps = detect_overlapping_labels(elements, min_confidence=40.0)

        assert len(overlaps) >= 1
        # Should have at least one overlap in warning or critical range
        assert any(o.severity in ["warning", "critical"] for o in overlaps)

    def test_filter_low_confidence(self):
        """Test filtering of low-confidence text."""
        elements = [
            TextElement("High Conf 1", BoundingBox(100, 100, 50, 20), 85.0),
            TextElement("High Conf 2", BoundingBox(110, 105, 50, 20), 85.0),  # Overlaps
            TextElement("Low Conf", BoundingBox(115, 108, 50, 20), 30.0),     # Low confidence, overlaps
        ]

        overlaps = detect_overlapping_labels(elements, min_confidence=40.0)

        # Should only detect overlap between high-confidence elements
        # Low confidence element should be filtered out
        assert all("Low Conf" not in (o.text1, o.text2) for o in overlaps)

    def test_skip_duplicate_text(self):
        """Test skipping overlaps for duplicate text (likely OCR errors)."""
        elements = [
            TextElement("SCE #1", BoundingBox(100, 100, 50, 20), 85.0),
            TextElement("SCE #1", BoundingBox(105, 102, 50, 20), 82.0),  # Duplicate, overlaps
        ]

        overlaps = detect_overlapping_labels(elements, min_confidence=40.0)

        assert len(overlaps) == 0  # Should skip same text overlaps

    def test_min_severity_filter(self):
        """Test filtering by minimum severity."""
        elements = [
            TextElement("Text1", BoundingBox(100, 100, 50, 20), 85.0),
            TextElement("Text2", BoundingBox(145, 105, 50, 20), 85.0),  # Minor overlap
        ]

        # Request only critical overlaps
        overlaps = detect_overlapping_labels(
            elements,
            min_confidence=40.0,
            min_severity="critical"
        )

        # Minor overlaps should be filtered out
        assert all(o.severity == "critical" for o in overlaps)


class TestLabelTypeClassification:
    """Test label type classification."""

    def test_sce_classification(self):
        """Test SCE label detection."""
        assert classify_label_type("SCE #1") == "SCE"
        assert classify_label_type("sce #5") == "SCE"
        assert classify_label_type("CONSTRUCTION ENTRANCE") == "SCE"

    def test_conc_wash_classification(self):
        """Test concrete washout classification."""
        assert classify_label_type("CONC WASH") == "CONC WASH"
        assert classify_label_type("CONCRETE WASHOUT") == "CONC WASH"
        assert classify_label_type("WASHOUT") == "CONC WASH"
        assert classify_label_type("WASH OUT") == "CONC WASH"

    def test_contour_classification(self):
        """Test contour label classification."""
        assert classify_label_type("EXIST 635.0") == "contour"
        assert classify_label_type("PROP. 636.5") == "contour"
        assert classify_label_type("635") == "contour"  # Elevation number
        assert classify_label_type("636.5") == "contour"

    def test_street_classification(self):
        """Test street label classification."""
        assert classify_label_type("KOTI WAY") == "street"
        assert classify_label_type("MAIN STREET") == "street"
        assert classify_label_type("OAK ROAD") == "street"
        assert classify_label_type("MAPLE DR") == "street"
        assert classify_label_type("PINE LN") == "street"

    def test_unclassified_label(self):
        """Test unclassified labels."""
        assert classify_label_type("RANDOM TEXT") is None
        assert classify_label_type("NOTES") is None
        assert classify_label_type("12") is None  # Too short for elevation


class TestEuclideanDistance:
    """Test Euclidean distance calculation."""

    def test_horizontal_distance(self):
        """Test horizontal distance."""
        dist = euclidean_distance((100, 100), (150, 100))
        assert dist == 50.0

    def test_vertical_distance(self):
        """Test vertical distance."""
        dist = euclidean_distance((100, 100), (100, 150))
        assert dist == 50.0

    def test_diagonal_distance(self):
        """Test diagonal distance (3-4-5 triangle)."""
        dist = euclidean_distance((0, 0), (3, 4))
        assert dist == 5.0

    def test_same_point(self):
        """Test distance to same point."""
        dist = euclidean_distance((100, 100), (100, 100))
        assert dist == 0.0


class TestFindNearestFeature:
    """Test nearest feature distance finding."""

    def test_single_feature(self):
        """Test with single feature."""
        label_bbox = BoundingBox(x=100, y=100, width=50, height=20)  # Center: (125, 110)
        features = [(150, 110)]  # 25px to the right

        distance = find_nearest_feature_distance(label_bbox, features)

        assert distance == 25.0

    def test_multiple_features(self):
        """Test with multiple features (should find nearest)."""
        label_bbox = BoundingBox(x=100, y=100, width=50, height=20)  # Center: (125, 110)
        features = [
            (200, 200),  # Far
            (130, 115),  # Near (should be ~7.07 distance)
            (300, 300),  # Far
        ]

        distance = find_nearest_feature_distance(label_bbox, features)

        assert distance == pytest.approx(7.07, abs=0.1)

    def test_no_features(self):
        """Test with no features."""
        label_bbox = BoundingBox(x=100, y=100, width=50, height=20)
        features = []

        distance = find_nearest_feature_distance(label_bbox, features)

        assert distance is None


class TestProximityValidation:
    """Test spatial proximity validation."""

    def test_label_within_threshold(self):
        """Test label within acceptable distance."""
        elements = [
            TextElement("SCE #1", BoundingBox(100, 100, 50, 20), 85.0),
        ]
        features = {
            "SCE": [(140, 110)]  # ~15px away, well within 200px threshold
        }

        issues = validate_label_proximity(
            elements,
            features,
            min_confidence=40.0
        )

        assert len(issues) == 0

    def test_label_beyond_threshold_warning(self):
        """Test label beyond threshold but <1.5x (warning)."""
        elements = [
            TextElement("SCE #1", BoundingBox(100, 100, 50, 20), 85.0),
        ]
        features = {
            "SCE": [(400, 110)]  # ~275px away, >200px but <300px (1.5x)
        }

        issues = validate_label_proximity(
            elements,
            features,
            min_confidence=40.0
        )

        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert issues[0].nearest_distance > 200

    def test_label_beyond_threshold_error(self):
        """Test label well beyond threshold (error)."""
        elements = [
            TextElement("SCE #1", BoundingBox(100, 100, 50, 20), 85.0),
        ]
        features = {
            "SCE": [(500, 110)]  # ~375px away, >300px (1.5x threshold)
        }

        issues = validate_label_proximity(
            elements,
            features,
            min_confidence=40.0
        )

        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert issues[0].nearest_distance > 300

    def test_no_matching_features(self):
        """Test label with no matching features found."""
        elements = [
            TextElement("SCE #1", BoundingBox(100, 100, 50, 20), 85.0),
        ]
        features = {
            "CONC WASH": [(200, 200)]  # Wrong type
        }

        issues = validate_label_proximity(
            elements,
            features,
            min_confidence=40.0
        )

        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert issues[0].nearest_distance is None

    def test_unclassified_labels_skipped(self):
        """Test that unclassified labels are skipped."""
        elements = [
            TextElement("RANDOM TEXT", BoundingBox(100, 100, 50, 20), 85.0),
        ]
        features = {
            "SCE": [(200, 200)]
        }

        issues = validate_label_proximity(
            elements,
            features,
            min_confidence=40.0
        )

        assert len(issues) == 0  # Unclassified label should be skipped


class TestQualityChecker:
    """Test QualityChecker class integration."""

    def test_initialization(self):
        """Test QualityChecker initialization."""
        checker = QualityChecker(
            min_text_confidence=50.0,
            min_overlap_severity="warning"
        )

        assert checker.min_text_confidence == 50.0
        assert checker.min_overlap_severity == "warning"

    def test_check_quality_no_text(self):
        """Test quality check with no text elements extracted."""
        checker = QualityChecker()

        # Create a blank image
        blank_image = np.ones((1000, 1000), dtype=np.uint8) * 255

        # This should not crash, just return empty results
        # Note: May fail if Tesseract not installed, so we'll skip this
        # in actual testing without mocking
        pass  # TODO: Add mock tests for full integration

    def test_quality_check_results_properties(self):
        """Test QualityCheckResults property calculations."""
        from esc_validator.quality_checker import QualityCheckResults

        overlaps = [
            OverlapIssue("Text1", "Text2", 500, 60.0, "critical", (100, 100)),
            OverlapIssue("Text3", "Text4", 300, 25.0, "warning", (200, 200)),
            OverlapIssue("Text5", "Text6", 100, 15.0, "minor", (300, 300)),
        ]

        proximity = [
            ProximityIssue("SCE #1", "SCE", 250.0, 200.0, "error"),
            ProximityIssue("SCE #2", "SCE", 220.0, 200.0, "warning"),
        ]

        results = QualityCheckResults(
            overlapping_labels=overlaps,
            proximity_issues=proximity
        )

        assert results.total_issues == 5
        assert results.critical_overlaps == 1
        assert results.warning_overlaps == 1
        assert results.proximity_errors == 1
        assert results.proximity_warnings == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
