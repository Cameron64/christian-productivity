# Phase 1.3.2: North Arrow & Street Detection Accuracy Improvements

**Status:** Planning
**Priority:** P1 (High)
**Expected Duration:** 2-3 days
**Prerequisites:** Phase 1.3.1 complete
**Focus:** Fix template mismatch and improve street label detection on plan sheets

---

## Overview

Phase 1.3.1 achieved **excellent results on ESC Notes sheets** (100% accuracy for sheet type and street detection) but revealed critical issues on **plan sheets**:

1. **North arrow template mismatch** - Decorative template doesn't match simple arrows used in these drawings
2. **Street label extraction failures** - OCR not detecting street names on plan sheets
3. **Street counting fallback issues** - Context-aware detection working but falling back to 0 due to missing labels

**Phase 1.3.2 Goal:** Achieve production-ready accuracy on **both notes AND plan sheets**:
- North arrow: 75%+ detection on plan sheets with actual north arrows
- Street counting: ±1 street accuracy on plan sheets with visible streets

---

## Current State (Phase 1.3.1 Results)

### ✅ Works Perfectly:
- **Sheet type detection:** 100% accurate (correctly identifies notes sheets)
- **Street counting (notes sheets):** 100% accurate (0 false positives)
- **North arrow rejection (notes sheets):** Correctly rejects non-existent arrows

### ❌ Needs Fixing:
- **North arrow (plan sheets):** 0% detection (template mismatch)
- **Street counting (plan sheets):** Returns 0 instead of 2 (missing labels)

---

## Problem Analysis

### Problem 1: North Arrow Template Mismatch

**Root Cause:**
- Current template: Decorative/ornate arrow with scrollwork (`templates/north_arrow.png`)
- Actual arrows in Christian's drawings: Simple black directional arrows
- Multi-scale matching works correctly but can't find a decorative template on simple arrows

**Evidence:**
```
Page 14 (ESC Plan):
  Template: Decorative scrollwork arrow
  Actual: Simple black arrow in upper-center area
  Result: 59.8% confidence (rejected as false positive at border corner)
```

**Impact:** Cannot detect north arrows on any plan sheets in this drawing set

---

### Problem 2: Street Label Extraction Failure

**Root Cause:**
- `extract_street_label_locations()` uses pytesseract to find street names
- OCR is not detecting "ENTRADA DRIVE" or "ROMULUS DRIVE" text on Page 14
- Possible causes:
  1. Street text might be in different font/style not recognized by OCR
  2. Text might be rotated or curved along street centerline
  3. DPI might be too low for small text (currently 150 DPI)
  4. Text might be overlapping with other features (contours, ESC lines)

**Evidence:**
```
Page 14 (ESC Plan with 2 visible streets):
  extract_street_label_locations() returned: 0 locations
  Visual count: 28 street groups (too high, filtered)
  Final count: 0 (fell back to label count)
```

**Impact:** Context-aware detection can't work without labels to validate against

---

## Phase 1.3.2 Solutions

### Solution 1: Multi-Template North Arrow Detection

**Approach:** Support multiple north arrow templates and use the best match

**Implementation:**

```python
def detect_north_arrow_multitemplate(
    image: np.ndarray,
    template_dir: Path,
    threshold: float = 0.6
) -> Tuple[bool, float, Optional[Tuple[int, int]], Optional[str]]:
    """
    Try multiple north arrow templates and return the best match.

    Args:
        image: Input image
        template_dir: Directory containing north arrow templates
        threshold: Minimum confidence for detection

    Returns:
        (detected, confidence, location, template_name)
    """
    # Load all templates in directory
    template_files = list(template_dir.glob("north_arrow*.png"))

    if not template_files:
        logger.warning(f"No north arrow templates found in {template_dir}")
        return False, 0.0, None, None

    best_detection = (False, 0.0, None, None)

    for template_path in template_files:
        detected, confidence, location = detect_north_arrow_multiscale(
            image, template_path, threshold=threshold
        )

        logger.debug(f"Template {template_path.name}: {confidence:.1%} confidence")

        # Keep best match
        if confidence > best_detection[1]:
            best_detection = (detected, confidence, location, template_path.name)

    detected, confidence, location, template_name = best_detection

    if detected:
        logger.info(f"Best match: {template_name} at {location} ({confidence:.1%})")

    return detected, confidence, location, template_name
```

**Required Templates:**
1. `north_arrow_decorative.png` - Current ornate template (for other projects)
2. `north_arrow_simple.png` - Simple black arrow (extract from Page 14)
3. `north_arrow_standard.png` - Standard CAD north arrow symbol

**Extraction Process:**
```python
# Extract actual north arrow from Page 14 and save as template
# User will manually crop the arrow region and save to templates/
```

---

### Solution 2: Enhanced Street Label Detection

**Approach:** Multi-strategy street name detection with improved OCR

**Strategy 1: Higher DPI OCR**
```python
def extract_street_label_locations_enhanced(
    text: str,
    image: np.ndarray,
    dpi: int = 300  # Increase from 150 to 300 for better text recognition
) -> list:
    """Enhanced street label detection with higher DPI."""
    # Upscale image for better OCR
    scale_factor = dpi / 150
    h, w = image.shape[:2]
    upscaled = cv2.resize(image, (int(w * scale_factor), int(h * scale_factor)))

    # Run OCR on upscaled image
    data = pytesseract.image_to_data(upscaled, output_type=pytesseract.Output.DICT)

    # ... existing pattern matching logic ...
    # But scale coordinates back down
    locations = [(x / scale_factor, y / scale_factor) for x, y in raw_locations]

    return locations
```

**Strategy 2: Fuzzy Text Matching**
```python
def find_street_labels_fuzzy(
    image: np.ndarray,
    expected_streets: list = None
) -> list:
    """
    Find street labels using fuzzy matching against expected street names.

    If we know the project, we can look for expected streets:
    - "ENTRADA" (matches "ENTRADA DRIVE")
    - "ROMULUS" (matches "ROMULUS DRIVE")
    """
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    # Build list of common street keywords
    street_keywords = ["DRIVE", "DR", "STREET", "ST", "WAY", "ROAD", "RD", "LANE", "LN"]

    if expected_streets:
        street_keywords.extend(expected_streets)

    locations = []
    for i, word in enumerate(data['text']):
        word_upper = word.upper()

        # Check for exact match or fuzzy match
        for keyword in street_keywords:
            if keyword in word_upper or fuzz.partial_ratio(keyword, word_upper) > 85:
                x = data['left'][i] + data['width'][i] // 2
                y = data['top'][i] + data['height'][i] // 2
                locations.append((x, y))
                logger.debug(f"Found street keyword '{word}' at ({x}, {y})")
                break

    return locations
```

**Strategy 3: Visual Line + Text Proximity**
```python
def associate_text_with_lines(
    image: np.ndarray,
    lines: np.ndarray,
    max_distance: int = 150
) -> list:
    """
    Find ALL text near detected lines, not just street patterns.

    This catches cases where street name isn't in standard format.
    """
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    line_text_associations = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        line_center = ((x1+x2)//2, (y1+y2)//2)

        # Find all text within max_distance of this line
        nearby_text = []
        for i, word in enumerate(data['text']):
            if not word.strip():
                continue

            x = data['left'][i] + data['width'][i] // 2
            y = data['top'][i] + data['height'][i] // 2

            dist = np.sqrt((line_center[0] - x)**2 + (line_center[1] - y)**2)

            if dist < max_distance:
                nearby_text.append(word)

        if nearby_text:
            line_text_associations.append({
                'line': line,
                'text': ' '.join(nearby_text),
                'center': line_center
            })

    return line_text_associations
```

---

### Solution 3: Hybrid Street Detection

**Approach:** Combine visual + text detection with better fallback logic

```python
def count_streets_hybrid(
    image: np.ndarray,
    text: str,
    debug: bool = False
) -> Tuple[int, Optional[np.ndarray]]:
    """
    Hybrid street detection combining multiple strategies.

    Strategy priority:
    1. Text labels found + visual confirmation → Most reliable
    2. Visual lines + nearby text (any text) → Moderately reliable
    3. Visual lines with street characteristics → Least reliable
    4. Text labels only → Fallback if visual fails
    """
    # Strategy 1: Try standard label extraction
    street_labels = extract_street_label_locations_enhanced(text, image, dpi=300)

    # Strategy 2: Try fuzzy matching if no labels found
    if not street_labels:
        street_labels = find_street_labels_fuzzy(image)

    # Visual detection
    candidate_lines = detect_long_lines(image)

    # Strategy 3: Associate text with lines
    line_text_assoc = associate_text_with_lines(image, candidate_lines)

    # Combine strategies
    if street_labels and len(street_labels) > 0:
        # Have text labels - validate with visual
        visual_count = count_lines_near_labels(candidate_lines, street_labels)

        # Use whichever is more conservative
        final_count = min(len(street_labels), visual_count)
        confidence = 0.9

    elif line_text_assoc:
        # Have lines with nearby text - medium confidence
        # Filter to lines that have text AND street characteristics
        street_lines = [
            assoc for assoc in line_text_assoc
            if has_parallel_line_nearby(assoc['line'], candidate_lines) or
               len(assoc['text']) > 5  # Non-trivial text
        ]
        final_count = len(street_lines)
        confidence = 0.6

    else:
        # Pure visual - low confidence
        street_groups = group_parallel_lines(candidate_lines)
        final_count = len(street_groups)
        confidence = 0.3

    logger.info(f"Hybrid detection: {final_count} streets (confidence: {confidence:.1%})")

    return final_count, None
```

---

## Phase 1.3.2 Implementation Plan

### Task 1: Create North Arrow Template Library

**Time:** 0.5 days

**Steps:**
1. Manually extract simple north arrow from Page 14
2. Create `templates/north_arrow_simple.png`
3. Rename current template to `templates/north_arrow_decorative.png`
4. Implement `detect_north_arrow_multitemplate()`
5. Update `detect_required_labels()` to use multi-template detection

**Files:**
- `templates/north_arrow_simple.png` - NEW
- `templates/north_arrow_decorative.png` - RENAME
- `esc_validator/symbol_detector.py` - Add new function

---

### Task 2: Enhanced Street Label Detection

**Time:** 1 day

**Steps:**
1. Implement `extract_street_label_locations_enhanced()` with higher DPI
2. Implement `find_street_labels_fuzzy()` with fuzzy matching
3. Implement `associate_text_with_lines()` for visual+text proximity
4. Add `python-Levenshtein` dependency for fuzzy matching
5. Test on Page 14 to verify street name detection

**Files:**
- `esc_validator/symbol_detector.py` - Add new functions
- `requirements.txt` - Add python-Levenshtein

---

### Task 3: Hybrid Street Detection Integration

**Time:** 1 day

**Steps:**
1. Implement `count_streets_hybrid()` combining all strategies
2. Update `count_streets_contextaware()` to use hybrid approach as fallback
3. Add confidence scoring for different detection strategies
4. Test on both Page 3 (notes) and Page 14 (plan)
5. Ensure no regressions on notes sheet detection

**Files:**
- `esc_validator/symbol_detector.py` - Enhance existing function

---

### Task 4: Integration & Testing

**Time:** 0.5 days

**Steps:**
1. Create comprehensive test suite
2. Test on multiple sheet types:
   - Page 3 (ESC Notes) - ensure no regression
   - Page 14 (ESC Plan with 2 streets)
   - Page 16 (Construction Details) - ensure proper classification
3. Update configuration with new feature flags
4. Update documentation
5. Performance testing (<45 seconds)

**Files:**
- `test_phase_1_3_2.py` - NEW
- `docs/phases/phase-3/phase-1.3.2/RESULTS.md` - NEW

---

## Success Criteria

Phase 1.3.2 is **COMPLETE** when:

1. ✅ **North Arrow (Plan Sheets):** 75%+ detection with simple arrow template
2. ✅ **Street Label Detection:** Find street names on plan sheets
3. ✅ **Street Counting (Plan Sheets):** ±1 street accuracy
4. ✅ **No Regressions:** All Phase 1.3.1 notes sheet accuracy maintained
5. ✅ **Performance:** Processing time still <45 seconds

---

## Expected Accuracy After Phase 1.3.2

### Before (Phase 1.3.1):
```
Page 3 (Notes):
  Sheet Type: NOTES ✓
  Streets: 0 detected ✓
  North Arrow: Correctly rejected ✓

Page 14 (Plan):
  Sheet Type: NOTES ✗ (should be PLAN or UNKNOWN)
  Streets: 0 detected ✗ (should be ~2)
  North Arrow: Not detected ✗ (template mismatch)
```

### After (Phase 1.3.2):
```
Page 3 (Notes):
  Sheet Type: NOTES ✓
  Streets: 0 detected ✓
  North Arrow: Correctly rejected ✓
  (No regression)

Page 14 (Plan):
  Sheet Type: PLAN or UNKNOWN ✓
  Streets: 2 detected ✓ (ENTRADA DRIVE, ROMULUS DRIVE)
  North Arrow: DETECTED ✓ (with simple arrow template)
```

---

## Risk Mitigation

### Risk 1: Manual Template Extraction Required

**Mitigation:**
- Provide clear instructions for extracting north arrow from Page 14
- Create template extraction utility script
- Validate template quality before integration

### Risk 2: OCR Still Fails to Detect Street Names

**Mitigation:**
- Hybrid approach with 3 fallback strategies
- Use visual+text proximity as backup
- Provide confidence scores so user knows reliability

### Risk 3: Higher DPI Slows Performance

**Mitigation:**
- Only upscale small regions of interest (not entire image)
- Use upscaling only when initial detection fails
- Monitor performance and adjust if > 45 seconds

---

## Alternative Approaches Considered

### Alternative 1: Deep Learning for North Arrow Detection

**Pros:** Best accuracy (95%+), handles any arrow style
**Cons:** Requires training data, much slower, overkill for 2-3 templates
**Decision:** Multi-template matching simpler and sufficient

### Alternative 2: Ask User for Expected Street Names

**Pros:** 100% reliable label detection if user provides names
**Cons:** Adds user interaction, defeats automation purpose
**Decision:** Use as optional configuration, not required

### Alternative 3: OCR Pre-training on Engineering Fonts

**Pros:** Better OCR accuracy on CAD text
**Cons:** Complex, requires training data, might not help
**Decision:** Try higher DPI and fuzzy matching first

---

## Timeline

**Day 1:**
- Morning: Extract north arrow templates, implement multi-template detection
- Afternoon: Test north arrow detection on plan sheets

**Day 2:**
- Morning: Implement enhanced street label extraction (higher DPI + fuzzy)
- Afternoon: Implement text-line association strategy

**Day 3:**
- Morning: Integrate hybrid street detection
- Afternoon: Testing and validation

**Total:** 2-3 days

---

## Deliverables

1. **Templates:**
   - `north_arrow_simple.png` - Extracted from actual drawings
   - `north_arrow_decorative.png` - Original template (renamed)

2. **Code:**
   - Multi-template north arrow detection
   - Enhanced street label extraction (3 strategies)
   - Hybrid street counting with confidence scores

3. **Tests:**
   - `test_phase_1_3_2.py` - Comprehensive test suite
   - Test cases for both notes and plan sheets

4. **Documentation:**
   - Template extraction guide
   - Updated accuracy metrics
   - Configuration guide

---

## Dependencies

**New Python Packages:**
```bash
pip install python-Levenshtein  # For fuzzy string matching
```

**Existing (already installed):**
- opencv-python
- pytesseract
- numpy

---

**Status:** Ready to implement
**Priority:** P1 - Required for production use on plan sheets
**Owner:** Claude (via Claude Code)
**For:** Christian's Productivity Tools - ESC Validator

---

**Created:** 2025-11-02
**Last Updated:** 2025-11-02
