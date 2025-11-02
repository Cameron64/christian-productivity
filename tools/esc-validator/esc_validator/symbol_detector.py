"""
Symbol Detection Module

Detects symbols (like north arrows) on ESC sheets using computer vision.
Uses ORB (Oriented FAST and Rotated BRIEF) for rotation-invariant feature matching.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


def detect_north_arrow(
    image: np.ndarray,
    template_path: Path,
    min_matches: int = 10,
    max_distance: int = 50
) -> Tuple[bool, float, Optional[Tuple[int, int]]]:
    """
    Detect north arrow symbol using ORB feature matching.

    This method is rotation-invariant, so it works even if the north arrow
    is rotated on the drawing.

    Args:
        image: Input image (grayscale or BGR)
        template_path: Path to north arrow template image
        min_matches: Minimum number of good matches to consider detection (default: 10)
        max_distance: Maximum feature distance for "good" matches (default: 50)

    Returns:
        Tuple of (detected, confidence, location)
        - detected: True if north arrow found
        - confidence: 0.0-1.0 confidence score
        - location: (x, y) coordinates of detected symbol, or None if not found

    Example:
        >>> detected, conf, loc = detect_north_arrow(image, Path("templates/north_arrow.png"))
        >>> if detected:
        ...     print(f"North arrow found at {loc} with {conf:.1%} confidence")
    """
    # Load template
    if not template_path.exists():
        logger.error(f"Template not found: {template_path}")
        return False, 0.0, None

    template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
    if template is None:
        logger.error(f"Failed to load template: {template_path}")
        return False, 0.0, None

    # Convert image to grayscale if needed
    if len(image.shape) == 3:
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray_image = image

    logger.debug(f"Template size: {template.shape}")
    logger.debug(f"Image size: {gray_image.shape}")

    # Create ORB detector (rotation-invariant)
    orb = cv2.ORB_create(nfeatures=500)

    # Find keypoints and descriptors
    try:
        kp1, des1 = orb.detectAndCompute(template, None)
        kp2, des2 = orb.detectAndCompute(gray_image, None)
    except cv2.error as e:
        logger.error(f"ORB detection failed: {e}")
        return False, 0.0, None

    if des1 is None or des2 is None:
        logger.warning("No features detected in template or image")
        return False, 0.0, None

    logger.debug(f"Template keypoints: {len(kp1)}, Image keypoints: {len(kp2)}")

    # Match features using Brute Force matcher with Hamming distance
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    try:
        matches = bf.match(des1, des2)
    except cv2.error as e:
        logger.error(f"Feature matching failed: {e}")
        return False, 0.0, None

    if not matches:
        logger.debug("No matches found")
        return False, 0.0, None

    # Filter for good matches (low distance)
    good_matches = [m for m in matches if m.distance < max_distance]
    num_good = len(good_matches)

    logger.debug(f"Total matches: {len(matches)}, Good matches: {num_good}")

    # Detection threshold
    detected = num_good >= min_matches

    # Calculate confidence score
    # Confidence based on:
    # 1. Number of good matches relative to template keypoints
    # 2. Quality of matches (inverse of average distance)
    if detected:
        match_ratio = num_good / max(len(kp1), 1)
        avg_distance = np.mean([m.distance for m in good_matches])
        distance_score = 1.0 - (avg_distance / max_distance)

        # Weighted average
        confidence = 0.6 * min(match_ratio, 1.0) + 0.4 * distance_score
        confidence = min(1.0, max(0.0, confidence))
    else:
        confidence = num_good / min_matches * 0.5  # Partial credit

    # Find location (centroid of matched keypoints)
    location = None
    if detected and good_matches:
        # Get positions of matched keypoints in the image
        matched_points = [kp2[m.trainIdx].pt for m in good_matches[:20]]  # Top 20 matches

        if matched_points:
            x_coords = [p[0] for p in matched_points]
            y_coords = [p[1] for p in matched_points]
            location = (int(np.mean(x_coords)), int(np.mean(y_coords)))
            logger.info(f"North arrow detected at {location} with confidence {confidence:.2f}")

    return detected, confidence, location


def draw_detection_result(
    image: np.ndarray,
    template_path: Path,
    location: Optional[Tuple[int, int]],
    detected: bool
) -> np.ndarray:
    """
    Draw detection result on image for visualization/debugging.

    Args:
        image: Input image (BGR)
        template_path: Path to template (for size reference)
        location: (x, y) location of detected symbol
        detected: Whether symbol was detected

    Returns:
        Image with detection visualization
    """
    result_img = image.copy()

    if not detected or location is None:
        return result_img

    # Load template to get size
    template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
    if template is None:
        return result_img

    th, tw = template.shape
    x, y = location

    # Draw bounding box around detected location
    color = (0, 255, 0)  # Green for detected
    thickness = 3

    # Draw rectangle (approximate size based on template)
    half_w = tw // 2
    half_h = th // 2
    cv2.rectangle(
        result_img,
        (x - half_w, y - half_h),
        (x + half_w, y + half_h),
        color,
        thickness
    )

    # Draw center point
    cv2.circle(result_img, (x, y), 5, color, -1)

    # Add label
    label = "NORTH ARROW"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    font_thickness = 2

    # Get text size for background rectangle
    (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)

    # Draw background rectangle for text
    cv2.rectangle(
        result_img,
        (x - text_w // 2 - 5, y - half_h - text_h - 15),
        (x + text_w // 2 + 5, y - half_h - 5),
        color,
        -1
    )

    # Draw text
    cv2.putText(
        result_img,
        label,
        (x - text_w // 2, y - half_h - 10),
        font,
        font_scale,
        (255, 255, 255),
        font_thickness
    )

    return result_img


def point_to_line_distance(point: Tuple[float, float], line_p1: Tuple[float, float], line_p2: Tuple[float, float]) -> float:
    """
    Calculate perpendicular distance from point to line.

    Args:
        point: (x, y) coordinates of point
        line_p1: (x, y) coordinates of line start
        line_p2: (x, y) coordinates of line end

    Returns:
        Distance from point to line
    """
    px, py = point
    x1, y1 = line_p1
    x2, y2 = line_p2

    # Line equation: (y2-y1)*x - (x2-x1)*y + x2*y1 - y2*x1 = 0
    # Distance = |ax + by + c| / sqrt(a^2 + b^2)
    a = y2 - y1
    b = -(x2 - x1)
    c = x2*y1 - y2*x1

    numerator = abs(a*px + b*py + c)
    denominator = np.sqrt(a*a + b*b)

    if denominator == 0:
        # Degenerate line (point)
        return np.sqrt((px-x1)**2 + (py-y1)**2)

    return numerator / denominator


def group_parallel_lines(lines: np.ndarray, angle_threshold: float = 15, distance_threshold: float = 100) -> list:
    """
    Group parallel lines that likely form streets.

    Streets on civil engineering plans typically have:
    - Parallel edges (centerline, edge of pavement, curb lines)
    - Similar angles
    - Close proximity

    Args:
        lines: Lines from cv2.HoughLinesP (shape: [N, 1, 4])
        angle_threshold: Maximum angle difference (degrees) to consider lines parallel
        distance_threshold: Maximum distance (pixels) between parallel lines

    Returns:
        List of street groups, where each group is a list of parallel lines
    """
    if lines is None or len(lines) == 0:
        return []

    street_groups = []
    used = set()

    for i, line1 in enumerate(lines):
        if i in used:
            continue

        x1, y1, x2, y2 = line1[0]
        angle1 = np.arctan2(y2-y1, x2-x1) * 180 / np.pi

        # Start new street group
        group = [line1]
        used.add(i)

        # Find parallel lines nearby (road edges)
        for j, line2 in enumerate(lines):
            if j in used or j <= i:
                continue

            x3, y3, x4, y4 = line2[0]
            angle2 = np.arctan2(y4-y3, x4-x3) * 180 / np.pi

            # Check if parallel (accounting for 180° wrapping)
            angle_diff = abs(angle1 - angle2)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            if angle_diff > angle_threshold and angle_diff < (180 - angle_threshold):
                continue

            # Check if nearby (within road width)
            midpoint = ((x3+x4)/2, (y3+y4)/2)
            dist = point_to_line_distance(midpoint, (x1, y1), (x2, y2))

            if dist < distance_threshold:
                group.append(line2)
                used.add(j)

        # Only count as street if has parallel lines OR very long (major road)
        line_len = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        # Streets should have parallel edges OR be very long single lines
        if len(group) >= 2 or line_len > 800:
            street_groups.append(group)

    return street_groups


def classify_line_type(line: np.ndarray, image: np.ndarray, sample_points: int = 20) -> Tuple[str, float]:
    """
    Classify a line as solid or dashed by analyzing pixel intensities along the line.

    Args:
        line: Line coordinates [x1, y1, x2, y2]
        image: Binary edge image
        sample_points: Number of points to sample along the line

    Returns:
        Tuple of (line_type, confidence)
        - line_type: "solid", "dashed", or "unknown"
        - confidence: 0.0-1.0 confidence score
    """
    x1, y1, x2, y2 = line[0] if len(line.shape) == 2 else line

    # Generate sample points along the line
    t = np.linspace(0, 1, sample_points)
    x_points = (x1 + t * (x2 - x1)).astype(int)
    y_points = (y1 + t * (y2 - y1)).astype(int)

    # Clip to image bounds
    h, w = image.shape[:2]
    valid_mask = (x_points >= 0) & (x_points < w) & (y_points >= 0) & (y_points < h)
    x_points = x_points[valid_mask]
    y_points = y_points[valid_mask]

    if len(x_points) < 5:
        return "unknown", 0.0

    # Sample pixel intensities along the line
    intensities = image[y_points, x_points]

    # Normalize to 0-1 range
    if intensities.max() > 1:
        intensities = intensities / 255.0

    # Detect gaps (low intensity = no line)
    threshold = 0.5
    gaps = intensities < threshold

    # Count transitions between line and gap
    transitions = np.diff(gaps.astype(int))
    num_transitions = np.sum(np.abs(transitions))

    # Calculate line coverage (what % of the line has pixels)
    coverage = np.sum(~gaps) / len(gaps)

    # Classification logic:
    # Solid line: high coverage (>80%), few transitions (<4)
    # Dashed line: moderate coverage (30-80%), many transitions (≥4)
    # Unknown: very low coverage (<30%)

    if coverage > 0.8 and num_transitions < 4:
        line_type = "solid"
        confidence = min(1.0, coverage)
    elif coverage >= 0.3 and num_transitions >= 4:
        line_type = "dashed"
        # More transitions = higher confidence it's dashed
        confidence = min(1.0, num_transitions / 10.0)
    else:
        line_type = "unknown"
        confidence = 0.0

    logger.debug(f"Line classification: {line_type} (coverage={coverage:.2f}, transitions={num_transitions})")

    return line_type, confidence


def detect_contour_lines(
    image: np.ndarray,
    min_line_length: int = 300,
    max_line_gap: int = 50,
    classify_types: bool = True
) -> Tuple[list, list]:
    """
    Detect contour lines on ESC sheet and optionally classify as solid/dashed.

    Args:
        image: Input image (grayscale or BGR)
        min_line_length: Minimum line length to detect (default: 300)
        max_line_gap: Maximum gap in line (default: 50)
        classify_types: Whether to classify line types (default: True)

    Returns:
        Tuple of (solid_lines, dashed_lines)
        Each is a list of tuples: [(line_coords, confidence), ...]
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Detect lines using Hough Transform
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=80,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap
    )

    if lines is None:
        logger.debug("No contour lines detected")
        return [], []

    logger.debug(f"Detected {len(lines)} potential contour lines")

    solid_lines = []
    dashed_lines = []

    if classify_types:
        # Classify each line
        for line in lines:
            line_type, confidence = classify_line_type(line, edges)

            if line_type == "solid":
                solid_lines.append((line, confidence))
            elif line_type == "dashed":
                dashed_lines.append((line, confidence))
            # Skip "unknown" lines

    logger.info(f"Classified lines: {len(solid_lines)} solid, {len(dashed_lines)} dashed")

    return solid_lines, dashed_lines


def verify_contour_conventions(
    image: np.ndarray,
    text: str,
    existing_should_be_dashed: bool = True
) -> Dict[str, any]:
    """
    Verify that contour line type conventions are followed.

    Standard convention (Austin):
    - Existing contours: Dashed lines
    - Proposed contours: Solid lines

    Args:
        image: Input image (grayscale or BGR)
        text: Extracted text from OCR (for label matching)
        existing_should_be_dashed: Whether existing contours should be dashed (default: True)

    Returns:
        Dictionary with verification results:
        {
            'existing_correct': bool,
            'proposed_correct': bool,
            'existing_confidence': float,
            'proposed_confidence': float,
            'notes': str
        }
    """
    # Import here to avoid circular dependency
    from .text_detector import fuzzy_match

    # Detect lines and classify
    solid_lines, dashed_lines = detect_contour_lines(image, classify_types=True)

    # Find contour labels in text
    has_existing = any(fuzzy_match(text, kw) for kw in ["existing", "exist", "ex"])
    has_proposed = any(fuzzy_match(text, kw) for kw in ["proposed", "prop", "future"])

    # Calculate confidence
    total_lines = len(solid_lines) + len(dashed_lines)

    if total_lines == 0:
        return {
            'existing_correct': False,
            'proposed_correct': False,
            'existing_confidence': 0.0,
            'proposed_confidence': 0.0,
            'notes': 'No contour lines detected'
        }

    # Check conventions
    results = {
        'existing_correct': True,
        'proposed_correct': True,
        'existing_confidence': 0.0,
        'proposed_confidence': 0.0,
        'notes': ''
    }

    notes = []

    # Verify existing contours (should be dashed)
    if has_existing:
        if existing_should_be_dashed:
            # Calculate average confidence of dashed lines
            if dashed_lines:
                avg_confidence = np.mean([conf for _, conf in dashed_lines])
                results['existing_confidence'] = avg_confidence
                results['existing_correct'] = len(dashed_lines) > 0
                notes.append(f"Existing: {len(dashed_lines)} dashed lines (correct)")
            else:
                results['existing_correct'] = False
                results['existing_confidence'] = 0.0
                notes.append("WARNING: No dashed lines found for existing contours")
        else:
            # Solid existing contours
            if solid_lines:
                avg_confidence = np.mean([conf for _, conf in solid_lines])
                results['existing_confidence'] = avg_confidence
                results['existing_correct'] = len(solid_lines) > 0
                notes.append(f"Existing: {len(solid_lines)} solid lines (correct)")

    # Verify proposed contours (should be solid)
    if has_proposed:
        if solid_lines:
            avg_confidence = np.mean([conf for _, conf in solid_lines])
            results['proposed_confidence'] = avg_confidence
            results['proposed_correct'] = len(solid_lines) > 0
            notes.append(f"Proposed: {len(solid_lines)} solid lines (correct)")
        else:
            results['proposed_correct'] = False
            results['proposed_confidence'] = 0.0
            notes.append("WARNING: No solid lines found for proposed contours")

    results['notes'] = '; '.join(notes)

    logger.info(f"Contour verification: {results['notes']}")

    return results


def verify_contour_conventions_smart(
    image: np.ndarray,
    text: str,
    max_distance: int = 150,
    use_spatial_filtering: bool = True,
    existing_should_be_dashed: bool = True
) -> Dict[str, any]:
    """
    Enhanced contour convention verification with spatial filtering (Phase 2.1).

    Uses spatial proximity to filter out non-contour lines (streets, lot lines, etc.)
    and focus only on lines near contour labels.

    Args:
        image: Input image (grayscale or BGR)
        text: Extracted text from OCR (for label matching)
        max_distance: Maximum distance (pixels) for label-to-line association (default: 150)
        use_spatial_filtering: Enable spatial filtering (default: True)
        existing_should_be_dashed: Whether existing contours should be dashed (default: True)

    Returns:
        Dictionary with verification results:
        {
            'existing_correct': bool,
            'proposed_correct': bool,
            'existing_confidence': float,
            'proposed_confidence': float,
            'notes': str,
            'total_lines_detected': int,
            'contour_lines_identified': int,
            'filter_effectiveness': float,
            'contour_labels_found': int,
            'spatial_filtering_enabled': bool
        }
    """
    # Import here to avoid circular dependency
    from .text_detector import (
        extract_text_with_locations,
        is_contour_label,
        is_existing_contour_label,
        is_proposed_contour_label
    )

    # Detect all lines
    solid_lines, dashed_lines = detect_contour_lines(image, classify_types=True)
    all_lines = [(line, conf, 'solid') for line, conf in solid_lines] + \
                [(line, conf, 'dashed') for line, conf in dashed_lines]

    total_lines = len(all_lines)

    if total_lines == 0:
        return {
            'existing_correct': False,
            'proposed_correct': False,
            'existing_confidence': 0.0,
            'proposed_confidence': 0.0,
            'notes': 'No lines detected',
            'total_lines_detected': 0,
            'contour_lines_identified': 0,
            'filter_effectiveness': 0.0,
            'contour_labels_found': 0,
            'spatial_filtering_enabled': use_spatial_filtering
        }

    # If spatial filtering disabled, use original function
    if not use_spatial_filtering:
        basic_results = verify_contour_conventions(image, text, existing_should_be_dashed)
        basic_results.update({
            'total_lines_detected': total_lines,
            'contour_lines_identified': total_lines,
            'filter_effectiveness': 0.0,
            'contour_labels_found': 0,
            'spatial_filtering_enabled': False
        })
        return basic_results

    # Extract text with locations
    text_locations = extract_text_with_locations(image)

    # Filter for contour labels
    contour_labels = [
        (loc['text'], loc['x'], loc['y'])
        for loc in text_locations
        if is_contour_label(loc['text'])
    ]

    contour_labels_count = len(contour_labels)
    logger.info(f"Found {contour_labels_count} contour labels")

    if contour_labels_count == 0:
        logger.warning("No contour labels detected - falling back to unfiltered detection")
        basic_results = verify_contour_conventions(image, text, existing_should_be_dashed)
        basic_results.update({
            'total_lines_detected': total_lines,
            'contour_lines_identified': total_lines,
            'filter_effectiveness': 0.0,
            'contour_labels_found': 0,
            'spatial_filtering_enabled': True,
            'notes': basic_results['notes'] + '; No contour labels found for filtering'
        })
        return basic_results

    # Find lines near contour labels
    nearby_lines = find_labels_near_lines(
        contour_labels,
        [line for line, _, _ in all_lines],
        max_distance
    )

    # Get unique line indices
    contour_line_indices = set(line_idx for _, line_idx, _ in nearby_lines)
    contour_lines_count = len(contour_line_indices)

    logger.info(f"Identified {contour_lines_count} lines near contour labels (filtered from {total_lines} total lines)")

    # Filter to contour lines only
    contour_solid = [
        (line, conf) for i, (line, conf, type_) in enumerate(all_lines)
        if i in contour_line_indices and type_ == 'solid'
    ]
    contour_dashed = [
        (line, conf) for i, (line, conf, type_) in enumerate(all_lines)
        if i in contour_line_indices and type_ == 'dashed'
    ]

    # Check for existing/proposed labels
    has_existing = any(is_existing_contour_label(text) for text, _, _ in contour_labels)
    has_proposed = any(is_proposed_contour_label(text) for text, _, _ in contour_labels)

    # Verify conventions on filtered lines
    results = {
        'existing_correct': True,
        'proposed_correct': True,
        'existing_confidence': 0.0,
        'proposed_confidence': 0.0,
        'notes': '',
        'total_lines_detected': total_lines,
        'contour_lines_identified': contour_lines_count,
        'filter_effectiveness': 1 - (contour_lines_count / total_lines) if total_lines > 0 else 0.0,
        'contour_labels_found': contour_labels_count,
        'spatial_filtering_enabled': True
    }

    notes = []

    # Verify existing contours (should be dashed)
    if has_existing:
        if existing_should_be_dashed:
            if contour_dashed:
                avg_confidence = np.mean([conf for _, conf in contour_dashed])
                results['existing_confidence'] = avg_confidence
                results['existing_correct'] = True
                notes.append(f"Existing: {len(contour_dashed)} dashed contour lines (correct)")
            else:
                results['existing_correct'] = False
                results['existing_confidence'] = 0.0
                notes.append("WARNING: No dashed contour lines found for existing contours")
        else:
            if contour_solid:
                avg_confidence = np.mean([conf for _, conf in contour_solid])
                results['existing_confidence'] = avg_confidence
                results['existing_correct'] = True
                notes.append(f"Existing: {len(contour_solid)} solid contour lines (correct)")

    # Verify proposed contours (should be solid)
    if has_proposed:
        if contour_solid:
            avg_confidence = np.mean([conf for _, conf in contour_solid])
            results['proposed_confidence'] = avg_confidence
            results['proposed_correct'] = True
            notes.append(f"Proposed: {len(contour_solid)} solid contour lines (correct)")
        else:
            results['proposed_correct'] = False
            results['proposed_confidence'] = 0.0
            notes.append("WARNING: No solid contour lines found for proposed contours")

    # Add filter statistics
    filter_pct = results['filter_effectiveness'] * 100
    notes.append(f"Filtered: {total_lines} total lines -> {contour_lines_count} contour lines ({filter_pct:.0f}% reduction)")

    results['notes'] = '; '.join(notes)

    logger.info(f"Smart contour verification: {results['notes']}")

    return results


def find_labels_near_lines(
    text_with_locations: list,
    lines: list,
    max_distance: float = 100
) -> list:
    """
    Find text labels that are spatially near lines (contours, streets, etc).

    Args:
        text_with_locations: List of (text, x, y) tuples from OCR with bounding boxes
        lines: List of line coordinates [x1, y1, x2, y2]
        max_distance: Maximum distance (pixels) to consider "near" (default: 100)

    Returns:
        List of (label, line_idx, distance) tuples for labels near lines
    """
    nearby_labels = []

    for text, x, y in text_with_locations:
        min_distance = float('inf')
        closest_line_idx = -1

        for idx, line in enumerate(lines):
            line_coords = line[0] if len(line.shape) == 2 else line
            x1, y1, x2, y2 = line_coords

            # Calculate distance from label to line
            dist = point_to_line_distance((x, y), (x1, y1), (x2, y2))

            if dist < min_distance:
                min_distance = dist
                closest_line_idx = idx

        if min_distance <= max_distance and closest_line_idx >= 0:
            nearby_labels.append((text, closest_line_idx, min_distance))

    logger.debug(f"Found {len(nearby_labels)} labels near lines")

    return nearby_labels


def count_streets_on_plan(image: np.ndarray, debug: bool = False) -> Tuple[int, Optional[np.ndarray]]:
    """
    Count unique streets by detecting road centerlines.

    Uses Hough line detection to find long, prominent lines that represent
    streets, then groups parallel lines into street segments.

    Args:
        image: Input image (grayscale or BGR)
        debug: If True, return visualization image

    Returns:
        Tuple of (street_count, debug_image)
        - street_count: Number of unique street segments found
        - debug_image: Visualization image (if debug=True), otherwise None
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Detect lines (streets are long and straight)
    # At 150 DPI, typical street on plan: 500-2000+ pixels
    # Increase threshold to filter out minor features
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=100,       # Higher threshold = only strong lines
        minLineLength=500,   # Streets are long (500 pixels minimum at 150 DPI)
        maxLineGap=100       # Allow larger gaps for intersections, stamps
    )

    if lines is None:
        logger.debug("No lines detected")
        return 0, None

    logger.debug(f"Detected {len(lines)} total lines")

    # Group parallel lines into streets
    street_groups = group_parallel_lines(lines)
    street_count = len(street_groups)

    logger.debug(f"Grouped into {street_count} street(s)")

    # Create debug visualization if requested
    debug_image = None
    if debug:
        # Create color image for visualization
        if len(image.shape) == 2:
            debug_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            debug_image = image.copy()

        # Draw each street group in a different color
        colors = [
            (0, 255, 0),    # Green
            (255, 0, 0),    # Blue
            (0, 0, 255),    # Red
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
        ]

        for i, group in enumerate(street_groups):
            color = colors[i % len(colors)]
            for line in group:
                x1, y1, x2, y2 = line[0]
                cv2.line(debug_image, (x1, y1), (x2, y2), color, 3)

            # Label each street group
            if group:
                x1, y1, x2, y2 = group[0][0]
                cv2.putText(
                    debug_image,
                    f"Street {i+1}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    color,
                    2
                )

    return street_count, debug_image


if __name__ == "__main__":
    """Test north arrow detection and street counting on a sample image."""
    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Test symbol detection")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--north-arrow", action="store_true", help="Test north arrow detection")
    parser.add_argument("--street-count", action="store_true", help="Test street counting")
    parser.add_argument("--template", default="templates/north_arrow.png", help="North arrow template")
    parser.add_argument("--output", help="Save visualization to file")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Load image
    img = cv2.imread(args.image)
    if img is None:
        print(f"Error: Could not load image: {args.image}")
        sys.exit(1)

    # Test north arrow detection
    if args.north_arrow:
        template_path = Path(args.template)
        detected, confidence, location = detect_north_arrow(img, template_path)

        print(f"\nNorth Arrow Detection Results:")
        print(f"  Detected: {detected}")
        print(f"  Confidence: {confidence:.1%}")
        if location:
            print(f"  Location: {location}")

        if args.output and detected:
            result_img = draw_detection_result(img, template_path, location, detected)
            cv2.imwrite(args.output, result_img)
            print(f"\nSaved visualization to: {args.output}")

    # Test street counting
    if args.street_count:
        street_count, debug_img = count_streets_on_plan(img, debug=True)

        print(f"\nStreet Counting Results:")
        print(f"  Streets found: {street_count}")

        if args.output and debug_img is not None:
            cv2.imwrite(args.output, debug_img)
            print(f"\nSaved visualization to: {args.output}")
