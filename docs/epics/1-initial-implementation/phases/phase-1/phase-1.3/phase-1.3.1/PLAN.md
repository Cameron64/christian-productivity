# Phase 1.3.1: Visual Detection Accuracy Improvements

**Status:** Planning
**Priority:** P1 (High)
**Expected Duration:** 3-4 days
**Prerequisites:** Phase 1.3 complete
**Focus:** Significantly improve accuracy of north arrow detection and street counting

---

## Overview

Phase 1.3 implemented visual detection but achieved:
- **North arrow:** 12.3% confidence (target: 90%+)
- **Street counting:** 55 streets detected on Notes sheet (expected: 0-3)

**Phase 1.3.1 Goal:** Increase accuracy to production-ready levels:
- North arrow: 90%+ detection accuracy
- Street counting: ±1 street accuracy on plan sheets, 0 streets on notes sheets

---

## Current Problems & Root Causes

### Problem 1: North Arrow Low Confidence (12.3%)

**Root Cause Analysis:**

1. **Template Mismatch:**
   - Template provided by user is a clean, standalone decorative arrow
   - Actual north arrow on ESC sheet may have:
     - Different style (simpler/more complex)
     - Surrounding text ("NORTH", "N")
     - Title block borders/lines nearby
     - Different scale/size

2. **ORB Feature Matching Limitations:**
   - ORB is rotation-invariant ✓
   - BUT: ORB is NOT scale-invariant ✗
   - We're only trying one scale
   - North arrow on sheet may be 50% smaller or 200% larger than template

3. **Insufficient Good Matches:**
   - Current threshold: 10 good matches (arbitrary)
   - Only getting 10-15 matches with low confidence
   - Need more keypoints or different detector

**Evidence:**
```
INFO:esc_validator.symbol_detector:North arrow detected at (6011, 3364) with confidence 0.12
```
- Detected location seems plausible (top-right area)
- But confidence way too low for production use

---

### Problem 2: Street Counting Too High (55 streets)

**Root Cause Analysis:**

1. **Detecting Non-Street Features:**
   - Current algorithm detects ANY long line
   - ESC Notes sheets have:
     - Table borders (many long horizontal/vertical lines)
     - Text underlines
     - Leader lines from notes
     - Drawing borders/title block
     - Legend boxes
   - All of these pass current filters

2. **Thresholds Too Permissive:**
   - `minLineLength=500` pixels (at 150 DPI)
   - Many non-street features are this long
   - `threshold=100` (line strength) still captures weak lines

3. **No Context Awareness:**
   - Algorithm doesn't know if sheet is a plan view or notes sheet
   - Doesn't look for street-specific features:
     - ROW (Right of Way) lines
     - Centerline markings
     - Street name labels nearby
     - Typical street patterns (parallel edges, curves)

**Evidence:**
```
WARNING:esc_validator.text_detector:Visual count very high (55) - likely detecting non-street features
INFO:esc_validator.text_detector:✗ streets: detected=False, count=0, confidence=0.30
```
- System correctly flagged as unreliable
- But should detect 0 streets on notes sheet, not 55

---

## Phase 1.3.1 Solution Strategy

### Solution 1: Multi-Scale Template Matching for North Arrow

**Approach:** Try template matching at multiple scales + rotation angles

**Why This Works:**
- Template matching more robust than ORB for simple symbols
- Multi-scale handles size variations
- Normalized correlation coefficient less sensitive to brightness

**Implementation:**

```python
def detect_north_arrow_multiscale(
    image: np.ndarray,
    template_path: Path,
    scales: tuple = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2.0),
    rotation_angles: tuple = (0, 15, 30, 45, -15, -30, -45),
    threshold: float = 0.6
) -> Tuple[bool, float, Optional[Tuple[int, int]]]:
    """
    Multi-scale, multi-rotation template matching.

    Strategy:
    1. Try template at multiple scales (30% to 200%)
    2. Try multiple rotation angles (±45°)
    3. Use TM_CCOEFF_NORMED method (best for symbols)
    4. Return best match above threshold

    Returns:
        (detected, confidence, location)
    """
    template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)

    # Convert image to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    best_score = 0
    best_location = None
    best_scale = 1.0
    best_angle = 0

    # Try each scale
    for scale in scales:
        # Resize template
        w = int(template.shape[1] * scale)
        h = int(template.shape[0] * scale)

        if w < 10 or h < 10 or w > gray.shape[1] or h > gray.shape[0]:
            continue

        scaled_template = cv2.resize(template, (w, h))

        # Try each rotation
        for angle in rotation_angles:
            # Rotate template
            if angle != 0:
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(scaled_template, M, (w, h),
                                        borderValue=255)  # White background
            else:
                rotated = scaled_template

            # Template matching
            result = cv2.matchTemplate(gray, rotated, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val > best_score:
                best_score = max_val
                best_location = (max_loc[0] + w//2, max_loc[1] + h//2)
                best_scale = scale
                best_angle = angle

    # Determine detection
    detected = best_score >= threshold
    confidence = best_score

    logger.info(f"Best match: score={best_score:.3f}, scale={best_scale:.2f}, "
                f"angle={best_angle}°, location={best_location}")

    return detected, confidence, best_location
```

**Expected Improvement:**
- Current: 12.3% confidence
- Target: 75-95% confidence
- **Rationale:** Template matching with multi-scale is the gold standard for symbol detection

---

### Solution 2: Context-Aware Street Detection

**Approach:** Use multiple signals to distinguish streets from other lines

**Key Insight:** Streets have unique characteristics:
1. **Always have nearby labels** (street names within 100-200 pixels)
2. **Have specific patterns** (parallel edges 40-80 pixels apart for typical roads)
3. **Are curved or straight** (not zigzag like leader lines)
4. **Don't form closed rectangles** (unlike table borders)

**Implementation:**

```python
def count_streets_contextaware(
    image: np.ndarray,
    text: str,
    debug: bool = False
) -> Tuple[int, Optional[np.ndarray]]:
    """
    Context-aware street counting.

    Strategy:
    1. Detect all long lines (candidates)
    2. Filter by street-specific features:
       - Has nearby street name label
       - Has parallel companion lines (ROW edges)
       - Smooth curve or straight (not zigzag)
       - Not part of closed rectangle (table border)
    3. Group remaining lines into streets
    4. Cross-validate with text labels

    Returns:
        (street_count, debug_image)
    """
    # Step 1: Detect candidate lines (same as before)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    edges = cv2.Canny(gray, 50, 150)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=120,  # Higher threshold
        minLineLength=800,  # Longer lines only (streets are long)
        maxLineGap=150
    )

    if lines is None or len(lines) == 0:
        return 0, None

    # Step 2: Get street name locations from text
    street_label_locations = extract_street_label_locations(text, image)

    # Step 3: Filter lines by street characteristics
    street_candidates = []

    for line in lines:
        x1, y1, x2, y2 = line[0]

        # Check 1: Has nearby street label?
        has_label = has_nearby_street_label(
            (x1, y1, x2, y2),
            street_label_locations,
            max_distance=200  # pixels
        )

        # Check 2: Is smooth (not zigzag)?
        angle = np.arctan2(y2-y1, x2-x1)
        is_smooth = True  # For now, all Hough lines are straight

        # Check 3: Not part of table border?
        is_table_border = is_part_of_rectangle(line, lines)

        # Check 4: Has parallel companion (road edges)?
        has_parallel = has_parallel_line_nearby(
            line, lines,
            distance_range=(30, 100),  # Typical road width
            angle_tolerance=10
        )

        # Score this line
        score = 0
        if has_label: score += 3  # Most important
        if has_parallel: score += 2
        if not is_table_border: score += 1

        if score >= 3:  # Need at least label + parallel OR label + not table
            street_candidates.append({
                'line': line,
                'score': score,
                'has_label': has_label
            })

    # Step 4: Group candidates into streets
    street_groups = group_parallel_lines(
        [c['line'] for c in street_candidates],
        angle_threshold=15,
        distance_threshold=100
    )

    # Step 5: Validate against text labels
    num_text_labels = len(street_label_locations)
    visual_count = len(street_groups)

    # Sanity check
    if visual_count > 20:
        # Still detecting too many - fall back to text count
        logger.warning(f"Visual count still high ({visual_count}), using text count")
        return num_text_labels, None

    # Return whichever is more reliable
    if num_text_labels > 0:
        # Text labels found - trust them
        final_count = num_text_labels
    else:
        # No text labels - use visual count
        final_count = visual_count

    return final_count, create_debug_image(image, street_groups)
```

**Helper Functions:**

```python
def extract_street_label_locations(text: str, image: np.ndarray) -> List[Tuple[int, int]]:
    """
    Use pytesseract with bounding boxes to find where street names are.

    Returns list of (x, y) coordinates where street labels appear.
    """
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    street_patterns = [
        r'\b\w+\s+(Street|St|Drive|Dr|Way|Road|Rd|Lane|Ln|Boulevard|Blvd)\b'
    ]

    locations = []
    for i, word in enumerate(data['text']):
        for pattern in street_patterns:
            if re.search(pattern, word, re.IGNORECASE):
                x = data['left'][i] + data['width'][i] // 2
                y = data['top'][i] + data['height'][i] // 2
                locations.append((x, y))

    return locations


def has_nearby_street_label(
    line: Tuple[int, int, int, int],
    label_locations: List[Tuple[int, int]],
    max_distance: int = 200
) -> bool:
    """Check if line has a street label within max_distance pixels."""
    x1, y1, x2, y2 = line
    line_center = ((x1+x2)//2, (y1+y2)//2)

    for label_loc in label_locations:
        dist = np.sqrt((line_center[0] - label_loc[0])**2 +
                      (line_center[1] - label_loc[1])**2)
        if dist < max_distance:
            return True

    return False


def is_part_of_rectangle(
    line: np.ndarray,
    all_lines: np.ndarray,
    tolerance: int = 20
) -> bool:
    """
    Check if line is part of a closed rectangle (table border).

    Strategy: Check if this line has perpendicular lines at both ends.
    """
    x1, y1, x2, y2 = line[0]
    angle = np.arctan2(y2-y1, x2-x1) * 180 / np.pi

    # Find perpendicular lines near endpoints
    perpendicular_at_start = 0
    perpendicular_at_end = 0

    for other_line in all_lines:
        ox1, oy1, ox2, oy2 = other_line[0]
        other_angle = np.arctan2(oy2-oy1, ox2-ox1) * 180 / np.pi

        # Check if perpendicular (90° difference)
        angle_diff = abs(angle - other_angle)
        if 80 < angle_diff < 100 or 260 < angle_diff < 280:
            # Check if near start point
            if (abs(ox1-x1) < tolerance and abs(oy1-y1) < tolerance) or \
               (abs(ox2-x1) < tolerance and abs(oy2-y1) < tolerance):
                perpendicular_at_start += 1

            # Check if near end point
            if (abs(ox1-x2) < tolerance and abs(oy1-y2) < tolerance) or \
               (abs(ox2-x2) < tolerance and abs(oy2-y2) < tolerance):
                perpendicular_at_end += 1

    # If has perpendicular lines at both ends, likely part of rectangle
    return perpendicular_at_start > 0 and perpendicular_at_end > 0


def has_parallel_line_nearby(
    line: np.ndarray,
    all_lines: np.ndarray,
    distance_range: Tuple[int, int] = (30, 100),
    angle_tolerance: float = 10
) -> bool:
    """Check if line has a parallel companion line (road edge)."""
    x1, y1, x2, y2 = line[0]
    angle = np.arctan2(y2-y1, x2-x1) * 180 / np.pi

    for other_line in all_lines:
        if np.array_equal(line, other_line):
            continue

        ox1, oy1, ox2, oy2 = other_line[0]
        other_angle = np.arctan2(oy2-oy1, ox2-ox1) * 180 / np.pi

        # Check if parallel
        angle_diff = abs(angle - other_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff

        if angle_diff < angle_tolerance or angle_diff > (180 - angle_tolerance):
            # Check distance
            midpoint = ((ox1+ox2)//2, (oy1+oy2)//2)
            dist = point_to_line_distance(midpoint, (x1, y1), (x2, y2))

            if distance_range[0] <= dist <= distance_range[1]:
                return True

    return False
```

**Expected Improvement:**
- Current: 55 streets detected on Notes sheet
- Target: 0-3 streets on Notes sheet, accurate count on Plan sheets
- **Rationale:** Streets MUST have labels - this is the key discriminator

---

### Solution 3: Sheet Type Detection (Plan vs Notes)

**Approach:** Detect sheet type BEFORE attempting street counting

**Why This Works:**
- Notes sheets have NO streets - can skip visual counting entirely
- Plan sheets have visual streets - visual counting is valuable
- Prevents false positives on Notes sheets

**Implementation:**

```python
def detect_sheet_type(image: np.ndarray, text: str) -> str:
    """
    Detect if sheet is a Plan View or Notes Sheet.

    Returns: "plan", "notes", or "unknown"
    """
    # Check 1: Title/header text
    if "NOTES" in text.upper() or "NOTE:" in text.upper():
        # Check density - notes sheets have MANY note lines
        note_count = text.upper().count("NOTE")
        if note_count > 10:
            return "notes"

    # Check 2: Look for plan-specific features
    plan_indicators = [
        "MATCH LINE",
        "STA ",  # Station markers
        "PROPOSED",
        "EXISTING",
        "CONTOUR",
        "SCALE",
    ]

    plan_score = sum(1 for indicator in plan_indicators if indicator in text.upper())

    # Check 3: Visual density
    # Notes sheets are dense with text
    # Plan sheets have more white space
    text_density = calculate_text_density(image)

    # Decision logic
    if plan_score >= 3 and text_density < 0.4:
        return "plan"
    elif text_density > 0.6:
        return "notes"
    else:
        return "unknown"


def calculate_text_density(image: np.ndarray) -> float:
    """
    Calculate what % of image is covered by text/dark pixels.

    Returns: 0.0 to 1.0
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    dark_pixels = np.sum(binary == 0)
    total_pixels = binary.size

    return dark_pixels / total_pixels
```

**Integration:**

```python
def verify_street_labeling_complete(
    image: np.ndarray,
    text: str,
    visual_count_func=None
) -> DetectionResult:
    """Enhanced with sheet type detection."""

    # NEW: Detect sheet type first
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

    # Continue with normal detection for plan sheets
    # ... (existing logic)
```

**Expected Improvement:**
- Eliminates false positives on Notes sheets entirely
- Faster processing (skips visual detection when not needed)

---

## Phase 1.3.1 Implementation Plan

### Task 1: Improve North Arrow Detection

**Time:** 1 day

**Steps:**
1. Implement `detect_north_arrow_multiscale()` function
2. Test with multiple templates (if needed)
3. Benchmark against Page 16
4. Target: 75%+ confidence

**Files:**
- `esc_validator/symbol_detector.py` - Add new function
- Keep old `detect_north_arrow()` as fallback

---

### Task 2: Implement Context-Aware Street Detection

**Time:** 1.5 days

**Steps:**
1. Implement helper functions:
   - `extract_street_label_locations()`
   - `has_nearby_street_label()`
   - `is_part_of_rectangle()`
   - `has_parallel_line_nearby()`
2. Implement `count_streets_contextaware()`
3. Test on both Plan and Notes sheets
4. Target: ±1 street accuracy on Plans, 0 on Notes

**Files:**
- `esc_validator/symbol_detector.py` - Add new functions
- Replace `count_streets_on_plan()` implementation

---

### Task 3: Implement Sheet Type Detection

**Time:** 0.5 days

**Steps:**
1. Implement `detect_sheet_type()` function
2. Implement `calculate_text_density()` helper
3. Integrate into `verify_street_labeling_complete()`
4. Test on multiple sheet types

**Files:**
- `esc_validator/text_detector.py` - Add sheet type detection

---

### Task 4: Integration & Testing

**Time:** 1 day

**Steps:**
1. Update `detect_required_labels()` to use new functions
2. Add feature flags:
   - `use_multiscale_north_arrow` (default: True)
   - `use_contextaware_streets` (default: True)
   - `detect_sheet_type` (default: True)
3. Run comprehensive tests:
   - Page 16 (ESC Notes)
   - Sample plan sheet with 3 streets
   - Sample plan sheet with 1 street
4. Performance testing (<45 seconds)
5. Update documentation

**Files:**
- `esc_validator/text_detector.py` - Integration
- `test_phase_1_3_1.py` - New test suite

---

## Success Criteria

Phase 1.3.1 is **COMPLETE** when:

1. ✅ **North Arrow Detection:** 75%+ confidence on test sheets
2. ✅ **Street Counting on Plan Sheets:** ±1 street accuracy
3. ✅ **Street Counting on Notes Sheets:** 0 streets (not 55)
4. ✅ **Sheet Type Detection:** 90%+ accuracy distinguishing Plan vs Notes
5. ✅ **Performance:** Processing time still <45 seconds
6. ✅ **No Regressions:** All Phase 1.2 text detection still works

---

## Expected Accuracy After Phase 1.3.1

### Before (Phase 1.3):
```
North Arrow: 12.3% confidence
Streets (Notes sheet): 55 detected → flagged as unreliable
Overall: Functional but requires manual verification
```

### After (Phase 1.3.1):
```
North Arrow: 75-90% confidence (multi-scale matching)
Streets (Notes sheet): 0 detected (correct!)
Streets (Plan sheet with 3 streets): 3 detected, 3 labeled = 100% coverage
Overall: Production-ready accuracy
```

---

## Alternative Approaches Considered

### Alternative 1: SIFT/SURF Instead of ORB
**Pros:** Better scale invariance
**Cons:** Not free (SURF), slower (SIFT)
**Decision:** Try multi-scale template matching first (simpler, faster)

### Alternative 2: Deep Learning for Symbol Detection
**Pros:** Best possible accuracy (95%+)
**Cons:** Requires training data, much slower, overkill for this problem
**Decision:** Save for Phase 6 if needed

### Alternative 3: Hough Circle Detection for North Arrow
**Pros:** North arrows often have circles
**Cons:** Doesn't work for non-circular north arrows, less robust
**Decision:** Multi-scale template matching is better

---

## Risk Mitigation

### Risk 1: Multi-Scale Matching Too Slow
**Mitigation:**
- Limit scales to 10-12 values
- Limit rotations to ±45° (7 angles)
- Total: ~80 template matches per sheet (fast enough)
- If still slow, search only top-right quadrant (north arrow location)

### Risk 2: Template Still Doesn't Match
**Mitigation:**
- Extract actual north arrow from Page 16 as backup template
- Support multiple templates (try all, use best match)
- Fall back to text-based detection if visual fails

### Risk 3: Context-Aware Street Detection Misses Streets
**Mitigation:**
- If no labels found but visual lines detected, flag for manual review
- Provide confidence score: low if visual/text mismatch
- Keep old simple algorithm as option (`use_contextaware_streets=False`)

---

## Timeline

**Day 1:**
- Morning: Implement multi-scale north arrow detection
- Afternoon: Test and tune thresholds

**Day 2:**
- Morning: Implement street label location extraction
- Afternoon: Implement context-aware filtering functions

**Day 3:**
- Morning: Integrate context-aware street detection
- Afternoon: Implement sheet type detection

**Day 4:**
- Morning: Integration and testing
- Afternoon: Documentation and final validation

**Total:** 3-4 days

---

## Deliverables

1. **Code:**
   - Enhanced `symbol_detector.py` with multi-scale matching
   - Context-aware street detection functions
   - Sheet type detection in `text_detector.py`

2. **Tests:**
   - `test_phase_1_3_1.py` - Comprehensive accuracy tests
   - Test cases for Plan sheets, Notes sheets, edge cases

3. **Documentation:**
   - Updated accuracy metrics
   - Before/after comparison
   - Configuration options

4. **Benchmarks:**
   - Accuracy report on 5-10 sample sheets
   - Performance benchmarks

---

## Success Metrics

### Target Accuracy:
- **North Arrow:** 75-90% confidence (up from 12.3%)
- **Streets on Plan Sheet:** ±1 street (currently N/A)
- **Streets on Notes Sheet:** 0 streets (currently 55)
- **Sheet Type Detection:** 90%+ accuracy

### Target Performance:
- **Processing Time:** <45 seconds (maintain current performance)
- **False Positive Rate:** <5% (down from ~100% on notes sheets)

---

**Status:** Ready to implement
**Priority:** P1 - Blocks production use
**Owner:** Claude (via Claude Code)
**For:** Christian's Productivity Tools - ESC Validator

---

**Created:** 2025-11-01
**Last Updated:** 2025-11-01
