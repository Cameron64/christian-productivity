# Streets Labeled Detection - Fix Plan

**Issue:** Phase 1.1 detected 194 "street" mentions, flagged as false positive
**Root Cause:** OCR counting every mention of "street" in notes, text, and actual street labels
**Goal:** Distinguish between actual street name labels on the plan vs. mentions in notes/text

---

## Problem Analysis

### Current Behavior (Phase 1.1):
```
Streets Labeled: ✗ 194 occurrences - likely false positive from notes/text
```

### What's Actually Happening:

1. **Legitimate street labels** on the plan (e.g., "North Loop Blvd", "Koti Way", "William Cannon Dr")
2. **Text mentions** in notes (e.g., "street design standards", "all streets shall...", "street name")
3. **Keywords detected:** "street", "st", "road", "rd", "drive", "dr", "way", "lane", "ln", "avenue", "ave"

**Problem:** Keywords like "way", "st", "dr" appear constantly in regular text, inflating the count

---

## Solution Approach

### Two-Step Detection Strategy

**Key Insight:** We need to answer TWO questions:
1. **How many unique streets** are shown on the plan? (graphic/visual)
2. **Are those streets labeled** with names? (text detection)

### Step 1: Count Unique Streets (Line Detection)

Detect street centerlines/polylines on the plan:

```python
def count_streets_on_plan(image: np.ndarray) -> int:
    """
    Count unique streets by detecting road centerlines/polylines.

    Streets appear as:
    - Parallel lines (road edges)
    - Centerlines (dashed or solid)
    - Connected polylines forming road network
    """

    # Convert to grayscale and detect edges
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    # Detect lines using HoughLinesP
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100,
                            minLineLength=200, maxLineGap=50)

    if lines is None:
        return 0

    # Group parallel lines into street segments
    street_segments = group_parallel_lines(lines)

    # Count unique connected street segments
    unique_streets = count_connected_segments(street_segments)

    return unique_streets
```

### Step 2: Match Labels to Streets (Text Detection)

Find street name labels and match them to detected streets:

```python
def match_labels_to_streets(text: str, street_count: int) -> Tuple[bool, int, List[str]]:
    """
    Find street name labels and verify they match the street count.

    Returns:
        (detected, label_count, street_names)

    Success criteria:
        - label_count should be close to street_count
        - Each street should have a label
    """

    # Find all street name labels using pattern matching
    street_names = find_street_name_labels(text)

    # Compare label count to actual street count
    label_count = len(street_names)

    # Detected = True if most streets are labeled (>70%)
    coverage = label_count / street_count if street_count > 0 else 0
    detected = coverage >= 0.7

    return detected, label_count, street_names
```

### Option 1: Context-Based Filtering (Text-Only, Phase 1.2)

**For now (Phase 1.2):** Use pattern matching to find street labels, but acknowledge limitation:

**Key Insight:** Real street labels are usually:
- Proper nouns (Title Case or ALL CAPS)
- Near the actual plan/drawing (not in notes section)
- Followed by street type suffix (Blvd, Dr, Way, etc.)
- Not in long sentences

**Limitation:** Without visual street detection, we can only count labels, not verify completeness

**Algorithm:**
```python
def detect_street_labels_smart(text: str) -> Tuple[bool, int, List[str]]:
    """
    Detect actual street name labels, not just mentions of "street".

    Strategy:
    1. Look for Title Case or ALL CAPS patterns with street suffixes
    2. Filter out text from notes/legend sections
    3. Require proper noun format: "Name + Suffix"
    """

    # Street suffix patterns (preceded by a name)
    street_patterns = [
        r'\b[A-Z][a-z]+\s+(Street|St|Boulevard|Blvd|Drive|Dr|Way|Lane|Ln|Road|Rd|Avenue|Ave|Court|Ct|Circle|Cir|Place|Pl)\b',
        r'\b[A-Z\s]+\s+(STREET|ST|BOULEVARD|BLVD|DRIVE|DR|WAY|LANE|LN|ROAD|RD|AVENUE|AVE|COURT|CT|CIRCLE|CIR|PLACE|PL)\b'
    ]

    street_names = []

    # Split into lines to avoid notes sections
    lines = text.split('\n')

    for line in lines:
        # Skip lines that look like notes (long sentences, lots of lowercase)
        if is_likely_notes_section(line):
            continue

        # Find street name patterns
        for pattern in street_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                # Extract the full street name
                street_name = extract_street_name(line, match)
                if street_name and street_name not in street_names:
                    street_names.append(street_name)

    detected = len(street_names) > 0
    count = len(street_names)

    return detected, count, street_names


def is_likely_notes_section(line: str) -> bool:
    """Determine if line is from notes/text rather than plan labels."""

    # Notes characteristics:
    # - Long lines (>100 chars)
    # - Mostly lowercase
    # - Contains sentence markers (periods, commas in middle)
    # - Contains common note words

    if len(line) > 100:
        return True

    # Count lowercase vs uppercase
    lowercase_count = sum(1 for c in line if c.islower())
    uppercase_count = sum(1 for c in line if c.isupper())

    if lowercase_count > uppercase_count * 2:  # Mostly lowercase = notes
        return True

    # Common note words
    note_indicators = [
        'shall', 'shall be', 'must', 'contractor', 'the ', 'all ',
        'requirements', 'standards', 'specifications', 'prior to'
    ]

    if any(indicator in line.lower() for indicator in note_indicators):
        return True

    return False


def extract_street_name(line: str, suffix: str) -> Optional[str]:
    """Extract full street name including prefix."""

    # Find the suffix position
    suffix_pos = line.find(suffix)
    if suffix_pos == -1:
        return None

    # Look backwards to find the street name
    before_suffix = line[:suffix_pos].strip()
    words = before_suffix.split()

    if not words:
        return None

    # Get the last 1-3 words before suffix (e.g., "North Loop" + "Blvd")
    name_parts = words[-3:] if len(words) >= 3 else words
    full_name = ' '.join(name_parts) + ' ' + suffix

    return full_name.strip()
```

---

## Implementation Plan

### Task 1: Update Keywords to Reduce False Positives

**File:** `text_detector.py`

**Current keywords:**
```python
"streets": ["street", "st", "road", "rd", "drive", "dr", "way", "lane", "ln", "avenue", "ave"]
```

**Problem:** "st", "dr", "way" are too generic and appear in regular text

**New approach:**
```python
# Don't use generic keywords - use pattern matching instead
"streets": []  # Will use custom detection function
```

---

### Task 2: Implement Smart Street Detection

**File:** `text_detector.py` (update `detect_required_labels()`)

**Add special handling for streets:**

```python
# In detect_required_labels()

if element == "streets":
    # Use smart pattern-based detection instead of keyword matching
    detected, count, matches = detect_street_labels_smart(full_text)
    confidence = 0.8 if detected and count <= 20 else 0.0

    # Flag if suspiciously high
    if count > 20:
        confidence = 0.3
        detected = False
        notes = f"Suspicious count ({count}) - verify manually"
    else:
        notes = f"Found {count} labeled streets" if detected else ""

    results[element] = DetectionResult(
        element=element,
        detected=detected,
        confidence=confidence,
        count=count,
        matches=matches[:10],  # Show first 10 street names
        notes=notes
    )
    continue  # Skip normal keyword detection
```

---

### Task 3: Add Helper Functions

**File:** `text_detector.py` (add new functions)

```python
def detect_street_labels_smart(text: str) -> Tuple[bool, int, List[str]]:
    """Detect actual street name labels using pattern matching."""
    # Implementation as shown above
    pass


def is_likely_notes_section(line: str) -> bool:
    """Check if line is from notes rather than plan labels."""
    # Implementation as shown above
    pass


def extract_street_name(line: str, suffix: str) -> Optional[str]:
    """Extract full street name from line."""
    # Implementation as shown above
    pass
```

---

### Task 4: Test on Page 16

**Expected Results:**

**Before (Phase 1.1):**
```
Streets Labeled: ✗ 194 occurrences - likely false positive from notes/text
```

**After (Phase 1.2 fix):**
```
Streets Labeled: ✓ 3-8 occurrences - Found labeled streets
Matches: ["William Cannon Dr", "North Loop Blvd", "Koti Way", ...]
```

**Success Criteria:**
- Count should be realistic (3-15 streets typically)
- Matches list shows actual street names (not generic "street" mentions)
- No false positive warning
- Confidence >75%

---

## Alternative: OCR Bounding Box Filtering (Phase 2 Enhancement)

If pattern matching isn't accurate enough, use OCR bounding boxes:

```python
def detect_street_labels_with_boxes(image: np.ndarray) -> List[str]:
    """
    Use OCR bounding boxes to filter labels by position.

    Strategy:
    1. Get OCR results with bounding boxes
    2. Identify "notes" region (bottom or side, text-heavy)
    3. Only count street labels OUTSIDE notes region
    4. Typically in center of plan
    """

    # Get detailed OCR with boxes
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    # Define notes region (e.g., bottom 20% of page)
    height = image.shape[0]
    notes_region_top = int(height * 0.8)

    street_names = []

    for i, word in enumerate(ocr_data['text']):
        # Get bounding box
        x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]

        # Skip if in notes region
        if y > notes_region_top:
            continue

        # Check if word is part of a street name
        if is_street_suffix(word):
            # Get nearby words to form full street name
            street_name = get_nearby_words(ocr_data, i)
            street_names.append(street_name)

    return list(set(street_names))  # Remove duplicates
```

---

## Timeline

**Part of Phase 1.2** (can be done alongside north arrow detection)

**Estimated Time:** 3-4 hours
- 1 hour: Implement pattern matching logic
- 1 hour: Integrate into text_detector.py
- 1 hour: Test on Page 16 and refine
- 30 min: Documentation

---

## Success Metrics

**Target Accuracy:**
- Precision: >80% (detected streets are actually labeled)
- Recall: >70% (most labeled streets are detected)
- False positive rate: <10% (minimal noise from text)

**Expected Count Range:**
- Typical ESC sheet: 3-15 labeled streets
- Page 16 (Erosion Control Notes): Possibly 0-5 (mostly notes, not plan)

---

## Decision: Is Page 16 the Right Test Sheet?

**Important Question:** Page 16 is "Erosion Control Notes" (text-heavy), not the ESC Plan (graphic-heavy).

**For streets labeled check:**
- Notes sheet: Might not have street labels at all
- Plan sheet: Should show site layout with street names

**Recommendation:**
1. Fix the detection algorithm first
2. Test on Page 16 to reduce false positives
3. Find the actual ESC Plan sheet to test positive detection
4. ESC Plan sheet likely has a title like "EROSION CONTROL PLAN" (not "NOTES")

---

---

## Complete Implementation: Visual + Text Detection

### Recommended Approach for Phase 2

Combine both visual and text detection for accurate street labeling verification:

```python
def detect_streets_labeled_complete(
    image: np.ndarray,
    text: str
) -> DetectionResult:
    """
    Complete street labeling detection.

    Step 1: Count streets visually (line detection)
    Step 2: Find street name labels (text detection)
    Step 3: Compare counts and verify labeling completeness
    """

    # Step 1: Visual detection - count streets on plan
    street_count_visual = count_streets_on_plan(image)

    # Step 2: Text detection - find street name labels
    street_labels = find_street_name_labels(text)
    label_count = len(street_labels)

    # Step 3: Verify completeness
    if street_count_visual == 0:
        # No streets on this sheet
        return DetectionResult(
            element="streets",
            detected=False,
            confidence=0.0,
            count=0,
            matches=[],
            notes="No streets found on this sheet"
        )

    # Calculate coverage
    coverage = label_count / street_count_visual
    detected = coverage >= 0.7  # At least 70% labeled

    # Confidence based on coverage
    if coverage >= 0.9:
        confidence = 0.95
        notes = f"All {street_count_visual} streets labeled"
    elif coverage >= 0.7:
        confidence = 0.8
        notes = f"{label_count}/{street_count_visual} streets labeled"
    else:
        confidence = 0.4
        notes = f"Only {label_count}/{street_count_visual} streets labeled - missing labels"

    return DetectionResult(
        element="streets",
        detected=detected,
        confidence=confidence,
        count=label_count,
        matches=street_labels,
        notes=notes
    )
```

### Helper: Count Streets Visually

```python
def count_streets_on_plan(image: np.ndarray) -> int:
    """
    Count unique streets by detecting road centerlines.

    Approach:
    1. Detect all long lines (potential streets)
    2. Group parallel line pairs (road edges)
    3. Find centerlines or parallel pairs
    4. Count unique street segments
    """

    # Detect edges
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Detect lines
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=80,
        minLineLength=300,  # Streets are long
        maxLineGap=50
    )

    if lines is None or len(lines) == 0:
        return 0

    # Convert to more usable format
    line_segments = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        # Calculate angle and length
        length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        angle = np.arctan2(y2-y1, x2-x1) * 180 / np.pi

        line_segments.append({
            'p1': (x1, y1),
            'p2': (x2, y2),
            'length': length,
            'angle': angle,
            'midpoint': ((x1+x2)/2, (y1+y2)/2)
        })

    # Group lines into streets (parallel lines close together)
    streets = []
    used = set()

    for i, line1 in enumerate(line_segments):
        if i in used:
            continue

        # Start a new street
        street_lines = [line1]
        used.add(i)

        # Find parallel lines nearby
        for j, line2 in enumerate(line_segments):
            if j in used or j <= i:
                continue

            # Check if parallel (similar angle)
            angle_diff = abs(line1['angle'] - line2['angle'])
            if angle_diff > 15 and angle_diff < 165:  # Not parallel
                continue

            # Check if nearby (road edges)
            dist = point_to_line_distance(
                line2['midpoint'],
                line1['p1'],
                line1['p2']
            )

            if dist < 100:  # Within road width
                street_lines.append(line2)
                used.add(j)

        # Only count if it looks like a street (multiple parallel lines or very long)
        if len(street_lines) >= 2 or any(l['length'] > 500 for l in street_lines):
            streets.append(street_lines)

    return len(streets)


def point_to_line_distance(point, line_p1, line_p2):
    """Calculate perpendicular distance from point to line."""
    px, py = point
    x1, y1 = line_p1
    x2, y2 = line_p2

    # Line length
    line_len = np.sqrt((x2-x1)**2 + (y2-y1)**2)
    if line_len == 0:
        return np.sqrt((px-x1)**2 + (py-y1)**2)

    # Perpendicular distance
    dist = abs((y2-y1)*px - (x2-x1)*py + x2*y1 - y2*x1) / line_len

    return dist
```

### Testing Strategy

```python
# Test on Page 16 (ESC Notes - may have 0 streets)
result = detect_streets_labeled_complete(page16_image, page16_text)

# Expected:
# street_count_visual = 0 (no streets on notes sheet)
# label_count = 0
# detected = False (no streets to label)
# notes = "No streets found on this sheet"


# Test on ESC Plan sheet (actual site layout)
result = detect_streets_labeled_complete(esc_plan_image, esc_plan_text)

# Expected:
# street_count_visual = 5 (5 streets visible on plan)
# label_count = 5 (all labeled: "Koti Way", "William Cannon Dr", etc.)
# detected = True
# coverage = 100%
# notes = "All 5 streets labeled"
```

---

## Phase-Based Implementation

### Phase 1.2 (Quick Fix - Text Only)
- ✅ Implement smart pattern matching for street labels
- ✅ Reduce false positives from notes/text
- ⚠️ **Limitation:** Can't verify if ALL streets are labeled (no visual count)
- **Accuracy:** ~60-70% (assumes text detection finds most labels)

### Phase 2 (Line Detection)
- ✅ Add visual street counting (line detection)
- ✅ Match label count to visual street count
- ✅ Verify labeling completeness
- **Accuracy:** ~85-95% (full verification)

---

**Next Steps:**
1. **Phase 1.2:** Implement pattern-based street label detection (text-only)
2. Test on Page 16 (expect 0-3 labels, no false positive)
3. Find actual ESC Plan sheet
4. **Phase 2:** Add visual street counting for complete verification
5. Test on ESC Plan sheet (validate label coverage)

---

**Created:** 2025-11-01
**Updated:** 2025-11-01 (added visual detection strategy)
**Part of:** Phase 1.2 Enhancements (text), Phase 2 (visual)
**Priority:** P1 (High - closes another detection gap)
