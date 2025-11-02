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
    checklist_elements: Optional[List[str]] = None
) -> Dict[str, DetectionResult]:
    """
    Detect all required labels from the ESC checklist.

    This is the main Phase 1 detection function.

    Args:
        image: Preprocessed image as numpy array (grayscale)
        checklist_elements: Optional list of specific elements to check.
                           If None, checks all elements.

    Returns:
        Dictionary mapping element names to DetectionResult objects

    Example:
        >>> results = detect_required_labels(preprocessed_image)
        >>> if results["sce"].detected:
        ...     print(f"Found {results['sce'].count} SCE labels")
    """
    logger.info("Starting required label detection")

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

        # Phase 1.2: Smart street name detection
        if element == "streets":
            detected, count, matches = detect_street_labels_smart(full_text)

            # Set confidence based on count
            if count == 0:
                confidence = 0.0
                notes = "No street labels detected"
            elif count <= 20:  # Reasonable range
                confidence = 0.75  # Good confidence, but can't verify completeness
                notes = f"Found {count} labeled street(s)"
            else:  # Suspiciously high
                confidence = 0.4
                detected = False
                notes = f"Found {count} potential streets - verify manually"

            results[element] = DetectionResult(
                element=element,
                detected=detected,
                confidence=confidence,
                count=count,
                matches=matches[:10],  # Show first 10
                notes=notes
            )

            # Log result
            status = "✓" if detected else "✗"
            logger.info(f"{status} {element}: detected={detected}, count={count}, confidence={confidence:.2f}")
            continue  # Skip normal keyword detection

        # Phase 1.2: North bar detection with limitation notes
        if element == "north_bar":
            # Phase 1.2: Acknowledge limitation - can't detect graphic symbols
            # Mark for manual verification
            north_count = full_text.upper().count('NORTH')

            if north_count > 50:
                # Probably false positive from notes
                detected = False
                confidence = 0.0
                notes = "Text-only detection unreliable for graphic symbols. Manual verification required. Symbol detection in Phase 1.3."
            elif 1 <= north_count <= 10:
                # Might be present
                detected = True
                confidence = 0.3  # Low confidence - could be text or symbol
                notes = "Possible north arrow detected. Verify manually. Full detection in Phase 1.3."
            else:
                detected = False
                confidence = 0.0
                notes = "No north arrow detected via text. Symbol detection available in Phase 1.3."

            results[element] = DetectionResult(
                element=element,
                detected=detected,
                confidence=confidence,
                count=north_count if north_count <= 10 else 0,
                matches=[],
                notes=notes
            )

            # Log result
            status = "✓" if detected else "✗"
            logger.info(f"{status} {element}: detected={detected}, count={north_count}, confidence={confidence:.2f}")
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
