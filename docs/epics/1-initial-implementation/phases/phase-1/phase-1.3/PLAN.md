# Phase 1.3: Visual Detection - Symbols & Line Verification

**Status:** Not Started
**Priority:** P1 (High)
**Expected Duration:** 2-3 days
**Prerequisites:** Phase 1.2 complete
**Focus:** Add computer vision for symbols and visual element verification

---

## Overview

Phase 1.3 adds **visual detection** capabilities to complement Phase 1.2's text detection:

1. **North arrow symbol** detection using template matching
2. **Street count verification** using line detection
3. **Match text labels to visual elements** for complete validation

**Goal:** Close detection gaps from Phase 1.2 by adding computer vision, achieving 90%+ overall accuracy.

---

## Problems Phase 1.3 Solves

### Problem 1: North Arrow (Currently Undetected)

**Phase 1.2 Status:**
```
North Bar: ✗ Not detected
Notes: "Manual verification required. Symbol detection in Phase 1.3."
```

**Solution:** Template matching with rotation invariance
**Expected:** 95%+ detection accuracy

---

### Problem 2: Street Labeling Completeness

**Phase 1.2 Status:**
```
Streets: ✓ 3 labels found ["William Cannon Dr", "Koti Way", ...]
Notes: "Found 3 labeled street(s)"
```

**Question:** Are ALL streets labeled? Or just 3 out of 10?

**Solution:** Visual street counting + label matching
**Expected:** Know if 3/3 (100%) or 3/10 (30%) are labeled

---

## Implementation Plan

### Task 1: North Arrow Template Detection

**Goal:** Detect north arrow symbol at any rotation

**Approach:** ORB feature matching (rotation-invariant)

**Files:**
- `tools/esc-validator/esc_validator/symbol_detector.py` (NEW)
- `tools/esc-validator/templates/north_arrow.png` (NEW)

**Implementation:**

```python
"""Symbol Detection Module"""

import cv2
import numpy as np
from pathlib import Path

def detect_north_arrow(image: np.ndarray, template_path: Path) -> tuple:
    """
    Detect north arrow using ORB feature matching.

    Returns: (detected, confidence, location)
    """
    # Load template
    template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)

    # ORB detector (rotation-invariant)
    orb = cv2.ORB_create(nfeatures=500)

    # Find keypoints
    kp1, des1 = orb.detectAndCompute(template, None)
    kp2, des2 = orb.detectAndCompute(image, None)

    if des1 is None or des2 is None:
        return False, 0.0, None

    # Match features
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    # Count good matches
    good_matches = [m for m in matches if m.distance < 50]
    num_good = len(good_matches)

    # Detection threshold
    detected = num_good >= 10
    confidence = min(1.0, num_good / max(len(kp1), 1))

    # Find location
    location = None
    if detected and good_matches:
        pts = [kp2[m.trainIdx].pt for m in good_matches[:10]]
        location = (int(np.mean([p[0] for p in pts])),
                   int(np.mean([p[1] for p in pts])))

    return detected, confidence, location
```

**Integration:**
```python
# In validator.py

from .symbol_detector import detect_north_arrow

# After text detection:
symbol_results = {}
symbol_results['north_arrow'] = detect_north_arrow(
    preprocessed_image,
    TEMPLATE_DIR / "north_arrow.png"
)

# Override text detection with symbol result
if symbol_results['north_arrow'][0]:  # detected
    detection_results["north_bar"] = DetectionResult(
        element="north_bar",
        detected=True,
        confidence=symbol_results['north_arrow'][1],
        count=1,
        matches=["North arrow symbol"],
        notes=f"Symbol detected at {symbol_results['north_arrow'][2]}"
    )
```

**Time:** 4 hours (template extraction + implementation)

---

### Task 2: Visual Street Counting

**Goal:** Count unique streets on plan using line detection

**Approach:** Hough line detection + parallel line grouping

**Implementation:**

```python
def count_streets_on_plan(image: np.ndarray) -> int:
    """
    Count unique streets by detecting road centerlines.

    Returns: number of unique street segments found
    """
    # Edge detection
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    # Detect lines (streets are long)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=80,
        minLineLength=300,  # Streets are long
        maxLineGap=50
    )

    if lines is None:
        return 0

    # Group parallel lines into streets
    streets = group_parallel_lines(lines)

    return len(streets)


def group_parallel_lines(lines: np.ndarray) -> list:
    """Group parallel lines that form streets."""

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

            # Check if parallel
            angle_diff = abs(angle1 - angle2)
            if angle_diff > 15 and angle_diff < 165:
                continue

            # Check if nearby (within road width)
            midpoint = ((x3+x4)/2, (y3+y4)/2)
            dist = point_to_line_distance(midpoint, (x1,y1), (x2,y2))

            if dist < 100:  # Within typical road width
                group.append(line2)
                used.add(j)

        # Only count as street if has parallel lines or very long
        line_len = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        if len(group) >= 2 or line_len > 500:
            street_groups.append(group)

    return street_groups
```

**Time:** 5 hours

---

### Task 3: Complete Street Labeling Verification

**Goal:** Match text labels to visual street count

**Implementation:**

```python
def verify_street_labeling(
    image: np.ndarray,
    text: str
) -> DetectionResult:
    """
    Complete street labeling verification.

    Step 1: Count streets visually
    Step 2: Find text labels
    Step 3: Verify coverage
    """
    # Visual count
    street_count = count_streets_on_plan(image)

    # Text labels (from Phase 1.2)
    _, label_count, street_names = detect_street_labels_smart(text)

    # Verify coverage
    if street_count == 0:
        return DetectionResult(
            element="streets",
            detected=False,
            confidence=0.0,
            count=0,
            matches=[],
            notes="No streets found on this sheet"
        )

    # Calculate coverage
    coverage = label_count / street_count
    detected = coverage >= 0.7  # At least 70% labeled

    # Confidence based on coverage
    if coverage >= 0.9:
        confidence = 0.95
        notes = f"Excellent: All {street_count} streets labeled"
    elif coverage >= 0.7:
        confidence = 0.8
        notes = f"Good: {label_count}/{street_count} streets labeled"
    else:
        confidence = 0.4
        notes = f"Incomplete: Only {label_count}/{street_count} labeled"

    return DetectionResult(
        element="streets",
        detected=detected,
        confidence=confidence,
        count=label_count,
        matches=street_names,
        notes=notes
    )
```

**Time:** 3 hours

---

### Task 4: Create Template Library

**Structure:**
```
tools/esc-validator/
├── templates/
│   ├── README.md
│   ├── north_arrow.png      # Extract from Page 16
│   └── (future templates)
```

**Template Extraction:**
1. Extract north arrow from your screenshot
2. Crop to ~100x100 pixels
3. Convert to grayscale
4. Save as PNG

**Time:** 1 hour

---

### Task 5: Integration & Testing

**Updates:**
1. `validator.py` - Add symbol detection step
2. `reporter.py` - Show symbol detection results
3. Remove Phase 1.2 limitation warnings

**Test Cases:**
1. **North arrow on Page 16** - Should detect (expected: 95% confidence)
2. **Streets on ESC Plan** - Should verify labeling completeness
3. **Performance** - Processing time should stay <45 seconds

**Time:** 3 hours

---

## Expected Results

### Before (Phase 1.2):
```
North Bar: ✗ Not detected
  Notes: "Manual verification required. Symbol detection in Phase 1.3."

Streets: ✓ 3 labels found
  Notes: "Found 3 labeled street(s)"
  Limitation: Can't verify if ALL streets labeled
```

### After (Phase 1.3):
```
North Bar: ✓ Symbol detected
  Confidence: 92%
  Location: (9500, 800)
  Notes: "North arrow symbol detected"

Streets: ✓ All streets labeled
  Confidence: 95%
  Count: 3 labels (visual: 3 streets)
  Coverage: 100%
  Notes: "Excellent: All 3 streets labeled"
  Matches: ["William Cannon Dr", "Koti Way", "North Loop Blvd"]
```

---

## Success Criteria

**Must Have:**
- ✅ North arrow template matching working
- ✅ North arrow detected on Page 16 (>90% confidence)
- ✅ Street counting implemented
- ✅ Street labeling verification complete
- ✅ Integration with validator working

**Should Have:**
- ✅ North arrow: 95%+ accuracy
- ✅ Street counting: ±1 street accuracy
- ✅ Processing time <45 seconds
- ✅ No regressions on text elements

---

## Timeline

**Day 1:**
- Morning: Extract template, implement north arrow detection (4 hours)
- Afternoon: Test north arrow on Page 16 (1 hour)

**Day 2:**
- Morning: Implement street counting (5 hours)
- Afternoon: Initial testing (1 hour)

**Day 3:**
- Morning: Street labeling verification (3 hours)
- Afternoon: Integration, testing, documentation (3 hours)

**Total:** ~17 hours (2-3 days)

---

## Deliverables

### Code
1. `symbol_detector.py` - New module (ORB matching)
2. `text_detector.py` - Updated (street count verification)
3. `validator.py` - Updated (symbol detection step)
4. `reporter.py` - Updated (symbol results display)

### Templates
1. `templates/north_arrow.png`
2. `templates/README.md`

### Documentation
1. Phase 1.3 test report
2. Before/after accuracy comparison

---

## Testing Plan

### Test Case 1: North Arrow Detection
**Input:** Page 16 (has north arrow)
**Expected:** Detected = True, Confidence >90%

### Test Case 2: Street Verification (Notes Sheet)
**Input:** Page 16 (ESC Notes - may have 0 streets)
**Expected:** 0 streets found, no labels required

### Test Case 3: Street Verification (Plan Sheet)
**Input:** ESC Plan sheet
**Expected:** X streets found, X labels, 100% coverage

---

## Acceptance Criteria

Phase 1.3 is **COMPLETE** when:
1. ✅ North arrow detection: 95%+ accuracy
2. ✅ Street counting implemented and tested
3. ✅ Complete street verification working
4. ✅ Overall checklist accuracy: 10-11/12 (83-92%)
5. ✅ All Phase 1.2 limitations resolved

---

## Next Steps After Phase 1.3

**Phase 2:** Line type detection (existing contours, proposed contours, drainage features)

---

**Status:** Ready to implement
**Estimated LOC:** ~400 lines new code
**Estimated Time:** 2-3 days
**Priority:** P1 (Closes critical visual detection gaps)

---

**Created:** 2025-11-01
**Owner:** Claude (via Claude Code)
**For:** Christian's Productivity Tools - ESC Validator
