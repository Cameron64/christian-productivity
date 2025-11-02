"""
Quality Checker for ESC Sheets (Phase 4)

Detects overlapping labels and validates spatial relationships between
labels and features.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import numpy as np
import pytesseract

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Bounding box for a text element."""
    x: int  # Left coordinate
    y: int  # Top coordinate
    width: int
    height: int

    @property
    def center_x(self) -> float:
        """Calculate center X coordinate."""
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        """Calculate center Y coordinate."""
        return self.y + self.height / 2

    @property
    def area(self) -> int:
        """Calculate bounding box area."""
        return self.width * self.height


@dataclass
class TextElement:
    """Text element with location and metadata."""
    text: str
    bbox: BoundingBox
    confidence: float  # 0-100 (Tesseract confidence)

    def __str__(self) -> str:
        return f"'{self.text}' at ({self.bbox.x}, {self.bbox.y})"


@dataclass
class OverlapIssue:
    """Detected overlap between two text elements."""
    text1: str
    text2: str
    overlap_area: int  # Square pixels
    overlap_percent: float  # Percentage of smaller box overlapped
    severity: str  # "critical", "warning", "minor"
    location: Tuple[int, int]  # Center of overlap region

    def __str__(self) -> str:
        return f"{self.severity.upper()}: '{self.text1}' overlaps '{self.text2}' ({self.overlap_percent:.1f}%)"


@dataclass
class ProximityIssue:
    """Detected spatial relationship issue."""
    label_text: str
    label_type: str  # "SCE", "CONC WASH", "contour", etc.
    nearest_distance: Optional[float]  # Distance in pixels, None if no features found
    expected_max: float  # Expected maximum distance
    severity: str  # "error", "warning"

    def __str__(self) -> str:
        if self.nearest_distance is None:
            return f"{self.severity.upper()}: {self.label_type} label '{self.label_text}' has no nearby features"
        return f"{self.severity.upper()}: {self.label_type} label '{self.label_text}' is {self.nearest_distance:.0f}px from feature (expected <{self.expected_max:.0f}px)"


@dataclass
class QualityCheckResults:
    """Results from quality checks."""
    overlapping_labels: List[OverlapIssue]
    proximity_issues: List[ProximityIssue]

    @property
    def total_issues(self) -> int:
        """Total number of quality issues found."""
        return len(self.overlapping_labels) + len(self.proximity_issues)

    @property
    def critical_overlaps(self) -> int:
        """Number of critical overlap issues."""
        return sum(1 for issue in self.overlapping_labels if issue.severity == "critical")

    @property
    def warning_overlaps(self) -> int:
        """Number of warning-level overlaps."""
        return sum(1 for issue in self.overlapping_labels if issue.severity == "warning")

    @property
    def proximity_errors(self) -> int:
        """Number of proximity errors."""
        return sum(1 for issue in self.proximity_issues if issue.severity == "error")

    @property
    def proximity_warnings(self) -> int:
        """Number of proximity warnings."""
        return sum(1 for issue in self.proximity_issues if issue.severity == "warning")


# Proximity rules from Phase 2.1 testing (pixels)
PROXIMITY_RULES = {
    "contour": 150,      # Phase 2.1 validated
    "SCE": 200,          # Silt fence markers
    "CONC WASH": 250,    # Concrete washout areas
    "storm_drain": 200,  # Inlet protection
    "street": 300,       # Street names near centerlines
}


def extract_text_with_bboxes(image: np.ndarray, lang: str = "eng", min_confidence: float = 0.0) -> List[TextElement]:
    """
    Extract text with full bounding boxes from image.

    Args:
        image: Preprocessed image as numpy array (grayscale)
        lang: Tesseract language (default: "eng")
        min_confidence: Minimum confidence threshold (0-100), default 0

    Returns:
        List of TextElement objects with bounding boxes
    """
    logger.info("Running OCR with full bounding boxes for quality checks")

    try:
        # Configure Tesseract for technical drawings
        custom_config = r'--psm 6 --oem 3'

        # Get detailed OCR data with bounding boxes
        data = pytesseract.image_to_data(
            image,
            lang=lang,
            config=custom_config,
            output_type=pytesseract.Output.DICT
        )

        text_elements = []
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = float(data['conf'][i])

            # Filter by confidence and validity
            if text and conf >= min_confidence:
                bbox = BoundingBox(
                    x=data['left'][i],
                    y=data['top'][i],
                    width=data['width'][i],
                    height=data['height'][i]
                )

                # Filter out very thin boxes (likely lines, not text)
                if bbox.width >= 5 and bbox.height >= 5:
                    text_elements.append(TextElement(
                        text=text,
                        bbox=bbox,
                        confidence=conf
                    ))

        logger.info(f"Extracted {len(text_elements)} text elements with bounding boxes")
        return text_elements

    except Exception as e:
        logger.error(f"OCR with bounding boxes error: {e}")
        return []


def calculate_bbox_intersection(bbox1: BoundingBox, bbox2: BoundingBox) -> Optional[BoundingBox]:
    """
    Calculate intersection rectangle of two bounding boxes.

    Args:
        bbox1: First bounding box
        bbox2: Second bounding box

    Returns:
        BoundingBox of intersection, or None if no intersection
    """
    # Calculate intersection bounds
    x_left = max(bbox1.x, bbox2.x)
    y_top = max(bbox1.y, bbox2.y)
    x_right = min(bbox1.x + bbox1.width, bbox2.x + bbox2.width)
    y_bottom = min(bbox1.y + bbox1.height, bbox2.y + bbox2.height)

    # Check if there's actual intersection
    if x_right <= x_left or y_bottom <= y_top:
        return None

    return BoundingBox(
        x=x_left,
        y=y_top,
        width=x_right - x_left,
        height=y_bottom - y_top
    )


def calculate_overlap_percentage(bbox1: BoundingBox, bbox2: BoundingBox, intersection: BoundingBox) -> float:
    """
    Calculate what percentage of the smaller box is overlapped.

    Args:
        bbox1: First bounding box
        bbox2: Second bounding box
        intersection: Intersection bounding box

    Returns:
        Percentage (0-100) of smaller box that is overlapped
    """
    area1 = bbox1.area
    area2 = bbox2.area
    intersection_area = intersection.area

    smaller_area = min(area1, area2)

    if smaller_area == 0:
        return 0.0

    return (intersection_area / smaller_area) * 100.0


def classify_overlap_severity(overlap_percent: float) -> str:
    """
    Classify overlap severity based on percentage.

    Args:
        overlap_percent: Percentage of smaller box overlapped (0-100)

    Returns:
        "critical", "warning", or "minor"
    """
    if overlap_percent > 50:
        return "critical"
    elif overlap_percent > 20:
        return "warning"
    else:
        return "minor"


def detect_overlapping_labels(
    text_elements: List[TextElement],
    min_confidence: float = 40.0,
    min_severity: str = "minor"
) -> List[OverlapIssue]:
    """
    Detect overlapping text labels using bounding box intersection.

    Args:
        text_elements: List of TextElement objects with bounding boxes
        min_confidence: Minimum confidence to consider (default 40)
        min_severity: Minimum severity to report ("critical", "warning", "minor")

    Returns:
        List of OverlapIssue objects
    """
    logger.info(f"Checking for overlapping labels among {len(text_elements)} text elements")

    # Filter by confidence
    valid_elements = [elem for elem in text_elements if elem.confidence >= min_confidence]
    logger.debug(f"Filtered to {len(valid_elements)} elements with confidence >={min_confidence}")

    overlaps = []
    severity_priority = {"critical": 3, "warning": 2, "minor": 1}
    min_priority = severity_priority[min_severity]

    # Check all pairs for overlaps (O(n²) but n is small ~50-100)
    for i, elem1 in enumerate(valid_elements):
        for elem2 in valid_elements[i+1:]:
            # Skip if same text (likely OCR duplicate)
            if elem1.text == elem2.text:
                continue

            # Calculate intersection
            intersection = calculate_bbox_intersection(elem1.bbox, elem2.bbox)

            if intersection:
                overlap_percent = calculate_overlap_percentage(elem1.bbox, elem2.bbox, intersection)
                severity = classify_overlap_severity(overlap_percent)

                # Only report if meets minimum severity
                if severity_priority[severity] >= min_priority:
                    overlaps.append(OverlapIssue(
                        text1=elem1.text,
                        text2=elem2.text,
                        overlap_area=intersection.area,
                        overlap_percent=overlap_percent,
                        severity=severity,
                        location=(int(intersection.center_x), int(intersection.center_y))
                    ))

    logger.info(f"Found {len(overlaps)} overlapping labels")
    logger.debug(f"Critical: {sum(1 for o in overlaps if o.severity == 'critical')}, "
                 f"Warning: {sum(1 for o in overlaps if o.severity == 'warning')}, "
                 f"Minor: {sum(1 for o in overlaps if o.severity == 'minor')}")

    return overlaps


def classify_label_type(text: str) -> Optional[str]:
    """
    Classify label type based on text content.

    Args:
        text: Label text

    Returns:
        Label type ("SCE", "CONC WASH", "contour", "street") or None
    """
    text_upper = text.upper()

    # SCE markers
    if "SCE" in text_upper or "CONSTRUCTION ENTRANCE" in text_upper:
        return "SCE"

    # Concrete washout
    if "CONC" in text_upper and "WASH" in text_upper:
        return "CONC WASH"
    if "WASHOUT" in text_upper or "WASH OUT" in text_upper:
        return "CONC WASH"

    # Contour labels (keywords or elevation numbers)
    if any(kw in text_upper for kw in ["EXIST", "PROP", "CONTOUR"]):
        return "contour"

    # Check for elevation numbers (3-4 digits with optional decimal)
    if text_upper.replace(".", "").replace("-", "").isdigit() and len(text_upper) >= 3:
        return "contour"

    # Street names
    street_suffixes = ["ST", "STREET", "RD", "ROAD", "DR", "DRIVE", "WAY", "LN", "LANE", "AVE", "AVENUE"]
    if any(suffix in text_upper for suffix in street_suffixes):
        return "street"

    return None


def euclidean_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate Euclidean distance between two points.

    Args:
        point1: (x, y) coordinates
        point2: (x, y) coordinates

    Returns:
        Distance in pixels
    """
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def find_nearest_feature_distance(
    label_bbox: BoundingBox,
    feature_locations: List[Tuple[float, float]]
) -> Optional[float]:
    """
    Find distance from label center to nearest feature.

    Args:
        label_bbox: Label bounding box
        feature_locations: List of (x, y) feature coordinates

    Returns:
        Distance in pixels, or None if no features
    """
    if not feature_locations:
        return None

    label_center = (label_bbox.center_x, label_bbox.center_y)

    min_distance = float('inf')
    for feature_point in feature_locations:
        distance = euclidean_distance(label_center, feature_point)
        min_distance = min(min_distance, distance)

    return min_distance


def validate_label_proximity(
    text_elements: List[TextElement],
    features: Dict[str, List[Tuple[float, float]]],
    proximity_rules: Dict[str, float] = PROXIMITY_RULES,
    min_confidence: float = 40.0
) -> List[ProximityIssue]:
    """
    Validate that labels are near their corresponding features.

    Args:
        text_elements: List of TextElement objects
        features: Dict of feature type -> list of (x, y) coordinates
                  e.g., {"SCE": [(100, 200), (300, 400)], "contour": [...]}
        proximity_rules: Max distance in pixels per label type
        min_confidence: Minimum text confidence to validate

    Returns:
        List of ProximityIssue objects
    """
    logger.info(f"Validating spatial proximity for {len(text_elements)} labels")

    issues = []

    # Filter by confidence
    valid_elements = [elem for elem in text_elements if elem.confidence >= min_confidence]

    for elem in valid_elements:
        label_type = classify_label_type(elem.text)

        # Skip if not a label type we validate spatially
        if label_type not in proximity_rules:
            continue

        max_distance = proximity_rules[label_type]

        # Get relevant features
        relevant_features = features.get(label_type, [])

        # If no features found, warn (might be missing feature or mislabeled)
        if not relevant_features:
            issues.append(ProximityIssue(
                label_text=elem.text,
                label_type=label_type,
                nearest_distance=None,
                expected_max=max_distance,
                severity="warning"
            ))
            continue

        # Find nearest feature
        nearest_distance = find_nearest_feature_distance(elem.bbox, relevant_features)

        # Check if exceeds threshold
        if nearest_distance and nearest_distance > max_distance:
            # Classify severity (error if >1.5x threshold, warning otherwise)
            severity = "error" if nearest_distance > max_distance * 1.5 else "warning"

            issues.append(ProximityIssue(
                label_text=elem.text,
                label_type=label_type,
                nearest_distance=nearest_distance,
                expected_max=max_distance,
                severity=severity
            ))

    logger.info(f"Found {len(issues)} proximity issues")
    logger.debug(f"Errors: {sum(1 for i in issues if i.severity == 'error')}, "
                 f"Warnings: {sum(1 for i in issues if i.severity == 'warning')}")

    return issues


class QualityChecker:
    """
    Main quality checker for ESC sheets.

    Performs overlap detection and spatial validation.
    """

    def __init__(
        self,
        min_text_confidence: float = 40.0,
        min_overlap_severity: str = "minor",
        proximity_rules: Dict[str, float] = None
    ):
        """
        Initialize quality checker.

        Args:
            min_text_confidence: Minimum OCR confidence to consider (0-100)
            min_overlap_severity: Minimum overlap severity to report
            proximity_rules: Custom proximity rules (uses defaults if None)
        """
        self.min_text_confidence = min_text_confidence
        self.min_overlap_severity = min_overlap_severity
        self.proximity_rules = proximity_rules or PROXIMITY_RULES

        logger.info(f"QualityChecker initialized (min_conf={min_text_confidence}, "
                   f"min_severity={min_overlap_severity})")

    def check_quality(
        self,
        image: np.ndarray,
        features: Dict[str, List[Tuple[float, float]]] = None
    ) -> QualityCheckResults:
        """
        Run all quality checks on an image.

        Args:
            image: Preprocessed image as numpy array
            features: Optional dict of feature locations for proximity validation

        Returns:
            QualityCheckResults with all detected issues
        """
        logger.info("Running quality checks on image")

        # Extract text with bounding boxes
        text_elements = extract_text_with_bboxes(
            image,
            min_confidence=self.min_text_confidence
        )

        if not text_elements:
            logger.warning("No text elements extracted, skipping quality checks")
            return QualityCheckResults(
                overlapping_labels=[],
                proximity_issues=[]
            )

        # Detect overlapping labels
        overlaps = detect_overlapping_labels(
            text_elements,
            min_confidence=self.min_text_confidence,
            min_severity=self.min_overlap_severity
        )

        # Validate spatial proximity (if features provided)
        proximity_issues = []
        if features:
            proximity_issues = validate_label_proximity(
                text_elements,
                features,
                proximity_rules=self.proximity_rules,
                min_confidence=self.min_text_confidence
            )
        else:
            logger.debug("No features provided, skipping proximity validation")

        results = QualityCheckResults(
            overlapping_labels=overlaps,
            proximity_issues=proximity_issues
        )

        logger.info(f"Quality checks complete: {results.total_issues} total issues found")
        logger.info(f"  Overlaps: {len(overlaps)} "
                   f"(critical: {results.critical_overlaps}, warning: {results.warning_overlaps})")
        logger.info(f"  Proximity: {len(proximity_issues)} "
                   f"(errors: {results.proximity_errors}, warnings: {results.proximity_warnings})")

        return results
