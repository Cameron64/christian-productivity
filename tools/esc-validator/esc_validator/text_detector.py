"""
OCR-Based Text Detection

Detect required text labels and features on ESC sheets using OCR (Tesseract).
Includes fuzzy matching for robust keyword detection.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import pytesseract
import numpy as np
from Levenshtein import ratio as levenshtein_ratio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Tesseract path for Windows
if sys.platform == "win32":
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for path in tesseract_paths:
        if Path(path).exists():
            pytesseract.pytesseract.tesseract_cmd = path
            logger.debug(f"Tesseract found at: {path}")
            break


@dataclass
class DetectionResult:
    """Result of text detection for a single element."""
    element: str
    detected: bool
    confidence: float  # 0.0 to 1.0
    count: int  # Number of occurrences found
    matches: List[str]  # Actual text matches found
    notes: str = ""


# Required keywords for each checklist element
REQUIRED_KEYWORDS = {
    # Basic sheet elements
    "legend": ["legend", "key", "symbol"],
    "scale": ["scale", "1\"=", "1'=", "scale:", "not to scale"],
    "north_bar": ["north", "n"],

    # Feature labels
    "loc": ["loc", "limit of construction", "limits of construction"],
    "silt_fence": ["sf", "silt fence", "silt fencing", "erosion control"],
    "sce": ["sce", "stabilized construction entrance", "construction entrance", "rock entrance"],
    "conc_wash": ["conc wash", "concrete wash", "concrete washout", "washout", "wash out"],
    "staging": ["staging", "spoils", "spoil area", "material storage"],

    # Contour and lot/block labels (will look for numeric patterns)
    "existing_contours": ["existing", "exist", "ex"],
    "proposed_contours": ["proposed", "prop", "future"],
    "streets": ["street", "st", "road", "rd", "drive", "dr", "way", "lane", "ln", "avenue", "ave"],
    "lot_block": ["lot", "block"],
}

# Minimum required quantities for critical elements
MIN_QUANTITIES = {
    "sce": 1,  # At least 1 stabilized construction entrance
    "conc_wash": 1,  # At least 1 concrete washout
}


def extract_text_from_image(image: np.ndarray, lang: str = "eng") -> str:
    """
    Extract all text from image using Tesseract OCR.

    Args:
        image: Preprocessed image as numpy array (grayscale)
        lang: Tesseract language (default: "eng")

    Returns:
        Extracted text as string
    """
    logger.info("Running OCR on image")

    try:
        # Configure Tesseract for technical drawings
        # --psm 6: Assume uniform block of text
        # --oem 3: Default OCR Engine Mode (LSTM)
        custom_config = r'--psm 6 --oem 3'

        text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
        logger.info(f"Extracted {len(text)} characters of text")

        return text

    except Exception as e:
        logger.error(f"OCR error: {e}")
        return ""


def extract_text_with_locations(image: np.ndarray, lang: str = "eng") -> List[Dict]:
    """
    Extract text with bounding box locations (Phase 2.1).

    Uses Tesseract's image_to_data() to get text with spatial coordinates.

    Args:
        image: Preprocessed image as numpy array (grayscale)
        lang: Tesseract language (default: "eng")

    Returns:
        List of dicts with:
        - text: str (extracted text)
        - x: int (center X coordinate in pixels)
        - y: int (center Y coordinate in pixels)
        - confidence: float (Tesseract confidence 0-100)
    """
    logger.info("Running OCR with bounding boxes")

    try:
        # Configure Tesseract for technical drawings
        custom_config = r'--psm 6 --oem 3'

        # Get detailed OCR data
        data = pytesseract.image_to_data(image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)

        text_locations = []
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if text and int(data['conf'][i]) > 0:  # Only include valid text with confidence
                text_locations.append({
                    'text': text,
                    'x': data['left'][i] + data['width'][i] // 2,  # Center X
                    'y': data['top'][i] + data['height'][i] // 2,   # Center Y
                    'confidence': float(data['conf'][i])
                })

        logger.info(f"Extracted {len(text_locations)} text elements with locations")
        return text_locations

    except Exception as e:
        logger.error(f"OCR with bounding boxes error: {e}")
        return []


def is_contour_label(text: str) -> bool:
    """
    Check if text is likely a contour label (Phase 2.1).

    Looks for contour keywords or elevation numbers.

    Args:
        text: Text to check

    Returns:
        True if text appears to be a contour label, False otherwise
    """
    text_lower = text.lower()

    # Keywords that indicate contour labels
    keywords = ['contour', 'existing', 'proposed', 'elev', 'elevation', 'ex', 'prop']
    if any(kw in text_lower for kw in keywords):
        return True

    # Numeric elevation pattern (e.g., "100", "105.5")
    # Contours typically in range 50-500 for Austin area
    if re.match(r'^\d{2,3}\.?\d*$', text):
        try:
            value = float(text)
            if 50 <= value <= 500:
                return True
        except ValueError:
            pass

    return False


def is_existing_contour_label(text: str) -> bool:
    """
    Check if text indicates an existing contour (Phase 2.1).

    Args:
        text: Text to check

    Returns:
        True if text indicates existing contour, False otherwise
    """
    text_lower = text.lower()
    existing_keywords = ['existing', 'exist', 'ex contour', 'ex.', 'ex ']

    return any(kw in text_lower for kw in existing_keywords)


def is_proposed_contour_label(text: str) -> bool:
    """
    Check if text indicates a proposed contour (Phase 2.1).

    Args:
        text: Text to check

    Returns:
        True if text indicates proposed contour, False otherwise
    """
    text_lower = text.lower()
    proposed_keywords = ['proposed', 'prop', 'future', 'new']

    return any(kw in text_lower for kw in proposed_keywords)


def fuzzy_match(text: str, keyword: str, threshold: float = 0.8) -> bool:
    """
    Check if keyword appears in text using fuzzy matching.

    Args:
        text: Text to search in (will be lowercased)
        keyword: Keyword to search for (will be lowercased)
        threshold: Minimum similarity ratio (0.0 to 1.0)

    Returns:
        True if fuzzy match found, False otherwise
    """
    text_lower = text.lower()
    keyword_lower = keyword.lower()

    # First try exact match (faster)
    if keyword_lower in text_lower:
        return True

    # Try fuzzy matching on words
    words = text_lower.split()
    for word in words:
        if levenshtein_ratio(word, keyword_lower) >= threshold:
            return True

    return False


def detect_keyword(text: str, keywords: List[str], fuzzy: bool = True, threshold: float = 0.8) -> Tuple[bool, List[str]]:
    """
    Detect if any keyword from list appears in text.

    Args:
        text: Text to search in
        keywords: List of keywords to search for
        fuzzy: Whether to use fuzzy matching (default: True)
        threshold: Fuzzy match threshold (default: 0.8)

    Returns:
        Tuple of (found, matched_keywords)
    """
    matches = []

    for keyword in keywords:
        if fuzzy:
            if fuzzy_match(text, keyword, threshold):
                matches.append(keyword)
        else:
            if keyword.lower() in text.lower():
                matches.append(keyword)

    return len(matches) > 0, matches


def count_keyword_occurrences(text: str, keywords: List[str], fuzzy: bool = True, threshold: float = 0.85) -> int:
    """
    Count how many times any keyword appears in text.

    Uses a sliding window approach to find all occurrences.

    Args:
        text: Text to search in
        keywords: List of keywords to search for
        fuzzy: Whether to use fuzzy matching
        threshold: Fuzzy match threshold (higher for counting)

    Returns:
        Total count of keyword occurrences
    """
    count = 0
    text_lower = text.lower()

    # For each keyword, count occurrences
    for keyword in keywords:
        keyword_lower = keyword.lower()

        # Count exact matches first
        count += text_lower.count(keyword_lower)

        # If fuzzy matching enabled, count fuzzy matches
        if fuzzy:
            words = text_lower.split()
            for word in words:
                # Avoid double-counting exact matches
                if word != keyword_lower and levenshtein_ratio(word, keyword_lower) >= threshold:
                    count += 1

    return count


def is_likely_notes_section(line: str) -> bool:
    """
    Determine if line is from notes/text rather than plan labels.

    Notes characteristics:
    - Long lines (>100 chars)
    - Mostly lowercase
    - Contains common note words

    Args:
        line: Single line of text

    Returns:
        True if line appears to be from notes section, False otherwise
    """
    # Too long = notes
    if len(line) > 100:
        return True

    # Count lowercase vs uppercase
    lowercase_count = sum(1 for c in line if c.islower())
    uppercase_count = sum(1 for c in line if c.isupper())

    # Mostly lowercase = notes
    if lowercase_count > uppercase_count * 2:
        return True

    # Common note indicators
    note_words = [
        'shall', 'shall be', 'must', 'contractor', 'the ', 'all ',
        'requirements', 'standards', 'prior to', 'in accordance'
    ]

    line_lower = line.lower()
    if any(word in line_lower for word in note_words):
        return True

    return False


def detect_street_labels_smart(text: str) -> Tuple[bool, int, List[str]]:
    """
    Detect actual street name labels using pattern matching.

    Filters out mentions in notes/text and focuses on proper street names.

    Args:
        text: Full text from OCR

    Returns:
        Tuple of (detected, count, street_names)
    """
    # Street name patterns
    # Format: "Name + Suffix" in Title Case or ALL CAPS
    patterns = [
        # Title Case: "North Loop Blvd"
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(Street|St|Boulevard|Blvd|Drive|Dr|Way|Lane|Ln|Road|Rd|Avenue|Ave|Court|Ct|Circle|Cir|Place|Pl)\b',
        # ALL CAPS: "WILLIAM CANNON DR"
        r'\b([A-Z\s]+)\s+(STREET|ST|BOULEVARD|BLVD|DRIVE|DR|WAY|LANE|LN|ROAD|RD|AVENUE|AVE|COURT|CT|CIRCLE|CIR|PLACE|PL)\b'
    ]

    street_names = set()
    lines = text.split('\n')

    for line in lines:
        # Skip notes sections
        if is_likely_notes_section(line):
            continue

        # Find street name patterns
        for pattern in patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                # match is tuple: (name, suffix)
                full_name = f"{match[0].strip()} {match[1]}"
                street_names.add(full_name)

    detected = len(street_names) > 0
    count = len(street_names)

    return detected, count, list(street_names)


def verify_street_labeling_complete(
    image: np.ndarray,
    text: str,
    visual_count_func=None,
    use_contextaware_streets: bool = True,
    use_multiscale_north_arrow: bool = True,
    detect_sheet_type_enabled: bool = True
) -> DetectionResult:
    """
    Complete street labeling verification (Phase 1.3.1 Enhanced).

    Combines text-based label detection with visual street counting
    to determine if ALL streets are labeled. Now includes sheet type
    detection and context-aware street counting.

    Args:
        image: Preprocessed image for visual analysis
        text: Extracted text for label detection
        visual_count_func: Optional function to count streets visually
                          If None, uses count_streets_contextaware (Phase 1.3.1)
        use_contextaware_streets: Use context-aware street detection (default: True)
        use_multiscale_north_arrow: Use multi-scale north arrow detection (default: True)
        detect_sheet_type_enabled: Enable sheet type detection (default: True)

    Returns:
        DetectionResult with comprehensive street labeling assessment
    """
    from .symbol_detector import detect_sheet_type, count_streets_contextaware

    # NEW: Detect sheet type first (Phase 1.3.1)
    sheet_type = "unknown"
    if detect_sheet_type_enabled:
        sheet_type = detect_sheet_type(image, text)

        if sheet_type == "notes":
            # Notes sheet - no streets expected
            return DetectionResult(
                element="streets",
                detected=False,
                confidence=0.95,  # High confidence this is correct
                count=0,
                matches=[],
                notes="Notes sheet detected - no streets expected"
            )

    # Step 1: Detect text labels
    detected, label_count, street_names = detect_street_labels_smart(text)

    # Step 2: Count streets visually
    visual_count = None
    if use_contextaware_streets and visual_count_func is None:
        # Use new context-aware counting (Phase 1.3.1)
        try:
            visual_count, _ = count_streets_contextaware(image, text, debug=False)
        except Exception as e:
            logger.warning(f"Context-aware street counting failed: {e}")
            visual_count = None
    elif visual_count_func is not None:
        # Use provided function (legacy/testing)
        try:
            visual_count, _ = visual_count_func(image, debug=False)
        except Exception as e:
            logger.warning(f"Visual street counting failed: {e}")
            visual_count = None

    # Step 3: Assess completeness
    if visual_count is None or visual_count == 0:
        # No visual counting available or no streets on plan
        # Fall back to text-only detection
        if detected:
            return DetectionResult(
                element="streets",
                detected=True,
                confidence=0.8,  # Lower confidence without visual verification
                count=label_count,
                matches=street_names,
                notes=f"Found {label_count} labeled street(s). Visual verification not available."
            )
        else:
            sheet_note = f" (detected as {sheet_type} sheet)" if sheet_type != "unknown" else ""
            return DetectionResult(
                element="streets",
                detected=False,
                confidence=0.5,
                count=0,
                matches=[],
                notes=f"No street labels found{sheet_note}."
            )

    # Step 4: Calculate coverage
    # Context-aware detection should eliminate the need for this check,
    # but keep as safety net
    if visual_count > 20:
        logger.warning(f"Visual count very high ({visual_count}) - likely detecting non-street features")
        # Fall back to text-only
        return DetectionResult(
            element="streets",
            detected=detected,
            confidence=0.7 if detected else 0.3,
            count=label_count,
            matches=street_names,
            notes=f"Found {label_count} labeled street(s). Visual count unreliable ({visual_count} features detected)."
        )

    # Calculate label coverage
    coverage = label_count / visual_count if visual_count > 0 else 0.0

    # Determine detection and confidence
    if coverage >= 0.9:
        # Excellent coverage
        return DetectionResult(
            element="streets",
            detected=True,
            confidence=0.95,
            count=label_count,
            matches=street_names,
            notes=f"Excellent: All {visual_count} streets labeled ({label_count} labels)"
        )
    elif coverage >= 0.7:
        # Good coverage
        return DetectionResult(
            element="streets",
            detected=True,
            confidence=0.85,
            count=label_count,
            matches=street_names,
            notes=f"Good: {label_count}/{visual_count} streets labeled ({coverage:.0%} coverage)"
        )
    elif coverage >= 0.5:
        # Partial coverage
        return DetectionResult(
            element="streets",
            detected=True,
            confidence=0.6,
            count=label_count,
            matches=street_names,
            notes=f"Partial: Only {label_count}/{visual_count} streets labeled ({coverage:.0%} coverage)"
        )
    else:
        # Poor coverage
        return DetectionResult(
            element="streets",
            detected=False,
            confidence=0.4,
            count=label_count,
            matches=street_names,
            notes=f"Incomplete: Only {label_count}/{visual_count} streets labeled ({coverage:.0%} coverage)"
        )


def detect_numeric_labels(text: str, context_keywords: List[str]) -> Tuple[bool, int]:
    """
    Detect numeric labels near context keywords (for contours, lots, blocks).

    Args:
        text: Text to search in
        context_keywords: Keywords to establish context (e.g., ["existing", "contour"])

    Returns:
        Tuple of (found, count) where count is number of numeric labels found
    """
    # Find lines containing context keywords
    lines = text.split('\n')
    relevant_lines = []

    for line in lines:
        for keyword in context_keywords:
            if keyword.lower() in line.lower():
                relevant_lines.append(line)
                break

    # Extract numeric patterns from relevant lines
    # Look for numbers that could be elevations or lot/block numbers
    numeric_pattern = r'\b\d+\.?\d*\b'
    count = 0

    for line in relevant_lines:
        numbers = re.findall(numeric_pattern, line)
        count += len(numbers)

    return count > 0, count


def detect_required_labels(
    image: np.ndarray,
    checklist_elements: Optional[List[str]] = None,
    enable_visual_detection: bool = True,
    template_dir: Optional[Path] = None
) -> Dict[str, DetectionResult]:
    """
    Detect all required labels from the ESC checklist.

    Phase 1.2 + 1.3: Text detection + visual symbol detection.

    Args:
        image: Preprocessed image as numpy array (grayscale)
        checklist_elements: Optional list of specific elements to check.
                           If None, checks all elements.
        enable_visual_detection: Enable Phase 1.3 visual detection (default: True)
        template_dir: Directory containing symbol templates (default: None, auto-detect)

    Returns:
        Dictionary mapping element names to DetectionResult objects

    Example:
        >>> results = detect_required_labels(preprocessed_image)
        >>> if results["sce"].detected:
        ...     print(f"Found {results['sce'].count} SCE labels")
    """
    logger.info("Starting required label detection (Phase 1.2 + 1.3)")

    # Extract all text from image
    full_text = extract_text_from_image(image)

    if not full_text.strip():
        logger.warning("No text extracted from image - OCR may have failed")

    # Determine which elements to check
    if checklist_elements is None:
        checklist_elements = list(REQUIRED_KEYWORDS.keys())

    results = {}

    # Check each element
    for element in checklist_elements:
        if element not in REQUIRED_KEYWORDS:
            logger.warning(f"Unknown element: {element}")
            continue

        keywords = REQUIRED_KEYWORDS[element]

        # Phase 1.3: Complete street labeling verification (text + visual)
        if element == "streets":
            if enable_visual_detection:
                # Import here to avoid circular dependency
                try:
                    from .symbol_detector import count_streets_on_plan
                    result = verify_street_labeling_complete(image, full_text, count_streets_on_plan)
                except ImportError as e:
                    logger.warning(f"Visual detection unavailable: {e}. Falling back to text-only.")
                    detected, count, matches = detect_street_labels_smart(full_text)
                    result = DetectionResult(
                        element="streets",
                        detected=detected,
                        confidence=0.75 if detected else 0.0,
                        count=count,
                        matches=matches[:10],
                        notes=f"Found {count} labeled street(s). Visual verification unavailable."
                    )
            else:
                # Phase 1.2: Text-only detection
                detected, count, matches = detect_street_labels_smart(full_text)
                result = DetectionResult(
                    element="streets",
                    detected=detected,
                    confidence=0.75 if detected else 0.0,
                    count=count,
                    matches=matches[:10],
                    notes=f"Found {count} labeled street(s)"
                )

            results[element] = result

            # Log result
            status = "✓" if result.detected else "✗"
            logger.info(f"{status} {element}: detected={result.detected}, count={result.count}, confidence={result.confidence:.2f}")
            continue  # Skip normal keyword detection

        # Phase 1.3.1: North arrow symbol detection (multi-scale)
        if element == "north_bar":
            if enable_visual_detection:
                # Try visual symbol detection
                try:
                    from .symbol_detector import detect_north_arrow_multiscale

                    # Auto-detect template path if not provided
                    if template_dir is None:
                        # Assume templates are in same directory as this module
                        module_dir = Path(__file__).parent
                        template_path = module_dir.parent / "templates" / "north_arrow.png"
                    else:
                        template_path = template_dir / "north_arrow.png"

                    if template_path.exists():
                        # Phase 1.3.1: Use multi-scale detection for better accuracy
                        detected, confidence, location = detect_north_arrow_multiscale(image, template_path)

                        if detected and confidence > 0.75:
                            # High confidence detection
                            notes = f"North arrow symbol detected at {location} (high confidence)" if location else "North arrow symbol detected (high confidence)"
                        elif detected:
                            # Moderate confidence
                            notes = f"North arrow detected at {location} (confidence: {confidence:.1%})" if location else f"North arrow detected (confidence: {confidence:.1%})"
                        else:
                            # Not detected
                            notes = "North arrow not detected via multi-scale template matching"

                        results[element] = DetectionResult(
                            element=element,
                            detected=detected,
                            confidence=confidence,
                            count=1 if detected else 0,
                            matches=["North arrow symbol"] if detected else [],
                            notes=notes
                        )
                    else:
                        # Template not found, fall back
                        logger.warning(f"North arrow template not found: {template_path}")
                        raise FileNotFoundError("Template not found")

                except (ImportError, FileNotFoundError) as e:
                    logger.warning(f"Visual north arrow detection unavailable: {e}. Falling back to text-based.")
                    # Fall through to text-based detection
                    detected = False
                    confidence = 0.0
                    notes = "Symbol detection unavailable. Manual verification required."

                    results[element] = DetectionResult(
                        element=element,
                        detected=detected,
                        confidence=confidence,
                        count=0,
                        matches=[],
                        notes=notes
                    )
            else:
                # Phase 1.2: Text-based detection (limited)
                north_count = full_text.upper().count('NORTH')

                if north_count > 50:
                    detected = False
                    confidence = 0.0
                    notes = "Text-only detection unreliable for graphic symbols."
                elif 1 <= north_count <= 10:
                    detected = True
                    confidence = 0.3
                    notes = "Possible north arrow detected via text. Enable visual detection for better accuracy."
                else:
                    detected = False
                    confidence = 0.0
                    notes = "No north arrow detected via text. Enable visual detection."

                results[element] = DetectionResult(
                    element=element,
                    detected=detected,
                    confidence=confidence,
                    count=north_count if north_count <= 10 else 0,
                    matches=[],
                    notes=notes
                )

            # Log result
            status = "✓" if results[element].detected else "✗"
            logger.info(f"{status} {element}: detected={results[element].detected}, confidence={results[element].confidence:.2f}")
            continue  # Skip normal keyword detection

        # Special handling for numeric labels (contours, lot/block)
        if element in ["existing_contours", "proposed_contours", "lot_block"]:
            detected, count = detect_numeric_labels(full_text, keywords)
            confidence = 0.7 if detected else 0.0  # Lower confidence for numeric detection
            matches = [f"Found {count} numeric labels"] if detected else []
            notes = "Numeric label detection requires manual verification"

        else:
            # Standard keyword detection
            detected, matches = detect_keyword(full_text, keywords, fuzzy=True, threshold=0.8)
            count = count_keyword_occurrences(full_text, keywords, fuzzy=True, threshold=0.85)
            confidence = 0.9 if detected else 0.0

            # Adjust confidence based on number of matches
            if detected and count > 1:
                confidence = min(0.95, 0.9 + (count * 0.01))

            notes = ""

            # False positive filtering: excessive occurrences likely from notes/text
            if count > 50:
                # Suspiciously high - likely counting text mentions
                confidence *= 0.3  # Reduce confidence drastically
                detected = False   # Mark as not detected
                notes = f"Excessive occurrences ({count}), likely false positive from notes/text"
                logger.warning(f"{element}: {count} occurrences - likely false positive")

        results[element] = DetectionResult(
            element=element,
            detected=detected,
            confidence=confidence,
            count=count,
            matches=matches,
            notes=notes
        )

        # Log result
        status = "✓" if detected else "✗"
        logger.info(f"{status} {element}: detected={detected}, count={count}, confidence={confidence:.2f}")

    logger.info("Label detection complete")
    return results


def verify_minimum_quantities(results: Dict[str, DetectionResult]) -> Dict[str, bool]:
    """
    Verify that minimum required quantities are met for critical elements.

    Args:
        results: Detection results from detect_required_labels()

    Returns:
        Dictionary mapping element names to pass/fail status

    Example:
        >>> detection_results = detect_required_labels(image)
        >>> quantity_check = verify_minimum_quantities(detection_results)
        >>> if not quantity_check["sce"]:
        ...     print("ERROR: Missing stabilized construction entrance!")
    """
    logger.info("Verifying minimum quantities")

    quantity_results = {}

    for element, min_count in MIN_QUANTITIES.items():
        if element not in results:
            logger.warning(f"Element '{element}' not in detection results")
            quantity_results[element] = False
            continue

        actual_count = results[element].count
        passed = actual_count >= min_count

        quantity_results[element] = passed

        status = "✓" if passed else "✗"
        logger.info(f"{status} {element}: required={min_count}, found={actual_count}")

    return quantity_results


def get_checklist_summary(results: Dict[str, DetectionResult]) -> Dict[str, any]:
    """
    Generate a summary of checklist validation results.

    Args:
        results: Detection results from detect_required_labels()

    Returns:
        Dictionary with summary statistics

    Example:
        >>> summary = get_checklist_summary(results)
        >>> print(f"Passed: {summary['passed']}/{summary['total']}")
    """
    total = len(results)
    passed = sum(1 for r in results.values() if r.detected)
    failed = total - passed

    # Calculate average confidence
    confidences = [r.confidence for r in results.values() if r.detected]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    # Identify critical failures
    critical_failures = []
    quantity_results = verify_minimum_quantities(results)
    for element, passed in quantity_results.items():
        if not passed:
            critical_failures.append(element)

    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / total if total > 0 else 0.0,
        "avg_confidence": avg_confidence,
        "critical_failures": critical_failures,
    }

    logger.info(f"Summary: {passed}/{total} checks passed ({summary['pass_rate']:.1%})")

    return summary
