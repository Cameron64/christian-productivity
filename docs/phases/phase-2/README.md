# Phase 2: Line Type Detection

**Status:** Not Started
**Expected Start:** Week 2-3 (after Phase 1 accuracy validation)
**Expected Duration:** 1-2 weeks
**Accuracy Target:** 70-80%

---

## Overview

Phase 2 adds computer vision-based line detection to verify contour types and validate that dashed/solid line conventions are followed on ESC sheets.

---

## Objectives

1. Detect and classify lines as solid or dashed
2. Verify existing contours use dashed lines
3. Verify proposed contours use solid lines
4. Validate contour labels are near contour lines
5. Spatial proximity analysis for label-to-feature matching

---

## Technical Approach

### OpenCV Pipeline

1. **Edge Detection:** Canny edge detector
2. **Line Detection:** Hough Line Transform
3. **Line Classification:** Gap analysis to determine dashed vs solid
4. **Spatial Analysis:** Match labels to nearby lines

---

## Prerequisites

- Phase 1 complete with ≥70% accuracy on actual ESC sheet
- OpenCV already installed (from Phase 1 requirements)

---

## Planned Deliverables

### Code
- `esc_validator/line_detector.py` - Line detection module
- Integration with existing validator
- Updated CLI options

### Documentation
- Implementation plan
- Line detection algorithm explanation
- Accuracy benchmarks

### Tests
- Unit tests for line classification
- Integration tests with full validator
- Test cases with known line types

---

## Expected Challenges

- **Drawing complexity** - Many overlapping lines
- **Line thickness variations** - May affect gap detection
- **Curved lines** - Hough Transform works best on straight lines
- **Faint lines** - May not detect in scanned drawings

---

## Decision Point

**Continue to Phase 2 if:**
- Phase 1 achieves ≥70% accuracy on text detection
- Christian confirms line type validation is valuable
- Test ESC sheets have clear line type conventions

**Skip Phase 2 if:**
- Phase 1 accuracy is sufficient without line detection
- Line types are not consistently used in Christian's projects
- Jump to Phase 6 (ML) for comprehensive approach

---

## Success Criteria

- Detect ≥70% of contour lines correctly
- Classify line types with ≥75% accuracy
- Reduce false positives from Phase 1 by spatial filtering
- Processing time remains <30 seconds per sheet

---

**Status:** AWAITING PHASE 1 VALIDATION
