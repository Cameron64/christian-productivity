# Phase 4: Quality Checks - REVISED IMPLEMENTATION PLAN

**Status:** Ready to Implement
**Expected Duration:** 6-10 hours
**Expected Start:** After Phase 2.1 testing completes
**Accuracy Target:** 85-95% for implemented features
**ROI Target:** Save 3-5 min per sheet × 50 sheets = **2.5-4 hours/year**

---

## Revision History

**Original Phase 4:** Full quality check suite including legend verification
**Revised Phase 4 (Phase 4 Lite):** Focus on high-feasibility, high-ROI components only

**Why Revised:**
- Phase 3 lessons: Template matching struggles with variability, low ROI features not worth pursuing
- Phase 2.1 success: Spatial proximity techniques work extremely well (99% accuracy)
- Focus on proven techniques with clear time savings

---

## Overview

Phase 4 Lite implements **only the high-value QC checks** that have proven feasibility based on Phase 2.1 results. This phase focuses on detecting common QC issues that cause permit resubmissions: overlapping labels (readability) and misplaced annotations (spatial errors).

**What We're Building:**
1. ✅ Overlapping label detection (readability issues)
2. ✅ Enhanced spatial validation (labels near features)
3. ❌ Legend verification (DEFERRED - low ROI, high risk)

---

## Phase 3 Lessons Applied

| Lesson from Phase 3 | How Applied in Phase 4 |
|---------------------|------------------------|
| **Template matching fails with variability** | Skip legend template matching entirely |
| **Know when to stop (3 hours)** | Hard time limit: 10 hours total for Phase 4 |
| **ROI matters** | Target 2.5-4 hours/year savings (vs 6 min/year in Phase 3) |
| **Visual confirmation is fast** | Accept manual legend verification |
| **Spatial proximity works (150px, 99% accuracy)** | Extend Phase 2.1 spatial logic for validation |

---

## Objectives

### Primary Goals
1. **Detect overlapping text labels** - Readability QC failures
2. **Validate label proximity to features** - Misplaced annotations
3. **Report spatial QC issues** - Flag for manual review

### Success Criteria
- Overlapping label detection: ≥90% accuracy
- Spatial validation: ≥85% accuracy
- Processing time overhead: <5 seconds
- False positive rate: <10%
- **Zero false negatives on critical overlaps** (text completely obscured)

### Non-Goals (Deferred)
- ❌ Legend line type verification
- ❌ Legend vs drawing consistency
- ❌ Symbol standardization checks
- ❌ Scale/dimension validation

---

## Technical Approach

### Component 1: Overlapping Label Detection

**Problem:**
- Text labels overlap, making sheets hard to read
- City reviewers reject sheets with overlapping annotations
- Common issue: "SCE", "CONC WASH", contour elevations overlapping

**Solution:**
Phase 2.1 already extracts text with bounding boxes via `extract_text_with_locations()`. We'll check for geometric overlaps.

**Algorithm:**
```python
def detect_overlapping_labels(text_data: List[TextDetection]) -> List[OverlapIssue]:
    """
    Detect overlapping text labels using bounding box intersection.

    Args:
        text_data: List of (text, confidence, bbox) from Phase 2.1

    Returns:
        List of overlap issues with:
        - text1, text2: Overlapping labels
        - overlap_area: Intersection area in pixels
        - overlap_percent: Percentage of smaller box overlapped
        - severity: "critical" (>50%), "warning" (20-50%), "minor" (<20%)
    """
    overlaps = []

    for i, (text1, conf1, bbox1) in enumerate(text_data):
        for j, (text2, conf2, bbox2) in enumerate(text_data[i+1:], start=i+1):
            intersection = calculate_bbox_intersection(bbox1, bbox2)
            if intersection:
                overlap_percent = calculate_overlap_percentage(bbox1, bbox2, intersection)
                severity = classify_overlap_severity(overlap_percent)
                overlaps.append(OverlapIssue(text1, text2, overlap_percent, severity))

    return overlaps
```

**Bounding Box Intersection Math:**
```python
def calculate_bbox_intersection(bbox1, bbox2):
    """
    Calculate intersection rectangle of two bounding boxes.

    bbox format: (x, y, width, height)

    Returns: (x, y, width, height) of intersection, or None
    """
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2

    # Calculate intersection bounds
    x_left = max(x1, x2)
    y_top = max(y1, y2)
    x_right = min(x1 + w1, x2 + w2)
    y_bottom = min(y1 + h1, y2 + h2)

    # Check if there's actual intersection
    if x_right < x_left or y_bottom < y_top:
        return None

    return (x_left, y_top, x_right - x_left, y_bottom - y_top)

def calculate_overlap_percentage(bbox1, bbox2, intersection):
    """Calculate what % of the smaller box is overlapped."""
    area1 = bbox1[2] * bbox1[3]
    area2 = bbox2[2] * bbox2[3]
    intersection_area = intersection[2] * intersection[3]

    smaller_area = min(area1, area2)
    return (intersection_area / smaller_area) * 100
```

**Severity Classification:**
- **Critical (>50% overlap):** Text likely unreadable, blocks other text
- **Warning (20-50% overlap):** May impact readability, review recommended
- **Minor (<20% overlap):** Edge touching, likely acceptable

**Edge Cases:**
- Ignore overlaps between same text (OCR duplicates)
- Ignore overlaps with very low confidence text (<40%)
- Whitelist intentional overlaps (leaders, arrows crossing text)

**Expected Performance:**
- Processing: O(n²) comparisons, but n ~= 50-100 labels per sheet
- Estimated time: 1-2 seconds per sheet
- False positives: <10% (arrows/leaders may be flagged)

**Implementation File:** `esc_validator/quality_checker.py` (new module)

---

### Component 2: Enhanced Spatial Validation

**Problem:**
- Labels placed far from their features (e.g., "SCE" 500px from fence)
- Contour labels disconnected from contour lines
- Notes not anchored to relevant areas

**Solution:**
Extend Phase 2.1's successful spatial proximity filtering to validate label placement.

**Algorithm:**
```python
def validate_label_proximity(
    text_data: List[TextDetection],
    features: Dict[str, List[Feature]],
    proximity_rules: Dict[str, int]
) -> List[ProximityIssue]:
    """
    Validate that labels are near their corresponding features.

    Args:
        text_data: OCR results with bounding boxes
        features: Dict of feature type -> list of features
                  e.g., {"contour_lines": [...], "sce_symbols": [...]}
        proximity_rules: Max distance in pixels per label type
                         e.g., {"contour": 150, "SCE": 200, "CONC WASH": 250}

    Returns:
        List of proximity issues with:
        - label_text: The misplaced label
        - label_type: What kind of label (contour, SCE, etc.)
        - nearest_feature_distance: Distance to closest matching feature
        - expected_max_distance: Threshold from proximity_rules
        - severity: "error" or "warning"
    """
    issues = []

    for text, conf, bbox in text_data:
        label_type = classify_label_type(text)
        if label_type not in proximity_rules:
            continue  # Not a label we validate spatially

        max_distance = proximity_rules[label_type]
        relevant_features = features.get(label_type_to_feature(label_type), [])

        if not relevant_features:
            # No features of this type found - potential issue
            issues.append(ProximityIssue(
                text, label_type, None, max_distance, "warning"
            ))
            continue

        nearest_distance = find_nearest_feature_distance(bbox, relevant_features)

        if nearest_distance > max_distance:
            severity = "error" if nearest_distance > max_distance * 1.5 else "warning"
            issues.append(ProximityIssue(
                text, label_type, nearest_distance, max_distance, severity
            ))

    return issues
```

**Proximity Rules (from Phase 2.1 testing):**
```python
PROXIMITY_RULES = {
    "contour_label": 150,      # px - Phase 2.1 validated
    "SCE": 200,                 # px - Silt fence markers
    "CONC WASH": 250,           # px - Concrete washout areas
    "storm_drain": 200,         # px - Inlet protection
    "street_label": 300,        # px - Street names near centerlines
}
```

**Feature Types to Validate:**
1. **Contour labels → Contour lines** (already working in Phase 2.1)
2. **SCE labels → Detected SCE locations** (from Phase 1)
3. **CONC WASH → Concrete washout symbols** (from Phase 1)
4. **Street names → Street centerlines** (requires Phase 2 line data)

**Distance Calculation:**
```python
def find_nearest_feature_distance(label_bbox, features):
    """
    Find distance from label center to nearest feature.

    Args:
        label_bbox: (x, y, width, height)
        features: List of feature objects with location data

    Returns:
        Distance in pixels (float)
    """
    label_center = (label_bbox[0] + label_bbox[2]/2,
                    label_bbox[1] + label_bbox[3]/2)

    min_distance = float('inf')
    for feature in features:
        feature_point = get_feature_location(feature)
        distance = euclidean_distance(label_center, feature_point)
        min_distance = min(min_distance, distance)

    return min_distance
```

**Edge Cases:**
- Multiple labels for same feature (choose closest)
- Features with no labels (warning, not error)
- Labels outside drawing boundary (separate check)

**Expected Performance:**
- Processing: O(n × m) where n=labels, m=features
- Estimated time: 2-3 seconds per sheet
- False positives: <15% (some labels are intentionally offset)

**Implementation File:** `esc_validator/quality_checker.py` (new module)

---

### Component 3: QC Report Generation

**Output Format:**
```json
{
  "quality_checks": {
    "overlapping_labels": {
      "total_overlaps": 3,
      "critical_overlaps": 1,
      "warning_overlaps": 2,
      "issues": [
        {
          "text1": "EX. 635.0",
          "text2": "PROP. 636.0",
          "overlap_percent": 65.3,
          "severity": "critical",
          "location": [1250, 890]
        }
      ]
    },
    "spatial_validation": {
      "total_issues": 2,
      "errors": 1,
      "warnings": 1,
      "issues": [
        {
          "label_text": "SCE #5",
          "label_type": "SCE",
          "nearest_distance": 320,
          "expected_max": 200,
          "severity": "error"
        }
      ]
    },
    "summary": {
      "total_qc_issues": 5,
      "critical_issues": 1,
      "sheet_quality": "needs_review"
    }
  }
}
```

**Markdown Report Section:**
```markdown
## Quality Check Results

### Overlapping Labels
- **Critical overlaps:** 1 (requires immediate attention)
- **Warning overlaps:** 2 (review recommended)

**Critical Issues:**
1. **"EX. 635.0" overlaps "PROP. 636.0"** (65% overlap) at location (1250, 890)
   - Text likely unreadable
   - Recommendation: Offset labels or use leader lines

### Spatial Validation
- **Errors:** 1 (label too far from feature)
- **Warnings:** 1 (label may be misplaced)

**Errors:**
1. **"SCE #5" is 320px from nearest silt fence** (expected <200px)
   - May indicate misplaced label or missing feature
   - Recommendation: Verify SCE #5 location matches plan

### Overall Quality: NEEDS REVIEW
```

**Implementation File:** `esc_validator/validator.py` (update existing report generation)

---

## Implementation Plan

### Step 1: Create Quality Checker Module (2-3 hours)
```
File: esc_validator/quality_checker.py

Classes:
- OverlapIssue (dataclass)
- ProximityIssue (dataclass)
- QualityChecker (main class)

Functions:
- detect_overlapping_labels()
- calculate_bbox_intersection()
- calculate_overlap_percentage()
- classify_overlap_severity()
- validate_label_proximity()
- find_nearest_feature_distance()
```

### Step 2: Integrate with Existing Validator (1-2 hours)
```
File: esc_validator/validator.py

Updates:
- Import QualityChecker
- Call quality checks after Phase 1 & 2 complete
- Integrate QC results into JSON output
- Add QC section to markdown report
```

### Step 3: Test with Real Data (2-3 hours)
```
Test Cases:
1. Entrada East page 26 (baseline - known good sheet)
2. Create synthetic test with overlapping labels
3. Create synthetic test with misplaced labels
4. Test edge cases (arrows, leaders, low confidence text)

Files:
- tests/unit/test_quality_checker.py (unit tests)
- tests/integration/test_phase4_integration.py (full workflow)
```

### Step 4: Documentation & CLI Updates (1-2 hours)
```
Documentation:
- Update tools/esc-validator/README.md
- Create docs/phases/phase-4/IMPLEMENTATION.md
- Update docs/phases/README.md (phase tracker)

CLI:
- Add --skip-qc flag (for performance testing)
- Update output verbosity for QC warnings
```

---

## Prerequisites

**Code Dependencies:**
- ✅ Phase 1 complete (text extraction with bounding boxes)
- ✅ Phase 2.1 complete (spatial proximity logic)
- ✅ `extract_text_with_locations()` function working

**Test Data:**
- ✅ Entrada East page 26 (baseline)
- ⏳ Create synthetic test PDFs with overlap issues
- ⏳ Create synthetic test PDFs with spatial issues

**External Libraries:**
- ✅ All dependencies already installed (opencv, pytesseract, pdfplumber)
- ❌ No new dependencies required

---

## Expected Challenges & Mitigations

### Challenge 1: False Positives on Arrows/Leaders
**Problem:** Arrow lines crossing text may be detected as overlapping labels

**Mitigation:**
- Filter out very thin bounding boxes (width or height <10px)
- Only check text-to-text overlaps, not text-to-graphic
- Tesseract's bounding boxes are text-only (should naturally avoid this)

**Fallback:** Accept 10-15% false positive rate, mark as "minor" severity

---

### Challenge 2: Defining "Near" for Different Features
**Problem:** 150px works for contours, but what about streets, storm drains?

**Mitigation:**
- Start with Phase 2.1's validated 150px for contours
- Test with Entrada East to calibrate other feature types
- Use conservative thresholds (200-300px) initially
- Tune based on false positive rate in testing

**Fallback:** Make proximity rules configurable via config file

---

### Challenge 3: Performance Overhead
**Problem:** O(n²) overlap detection might be slow for sheets with 200+ labels

**Mitigation:**
- Early exit on low-confidence text (<40%)
- Spatial indexing (grid-based) to reduce comparisons
- Target: <5 seconds overhead on worst case

**Fallback:** Add `--skip-qc` flag for fast validation mode

---

### Challenge 4: OCR Bounding Box Accuracy
**Problem:** Tesseract bounding boxes may not perfectly match visual text bounds

**Mitigation:**
- Add 5-10px padding to bounding boxes for overlap detection
- Use "significant overlap" threshold (>20%) to filter edge cases
- Visual inspection of flagged overlaps during testing

**Fallback:** Tune overlap percentage thresholds based on real-world testing

---

## Success Metrics

### Accuracy Targets
- **Overlapping labels:** ≥90% detection accuracy
  - True positive: Correctly identifies unreadable overlaps
  - False positive: <10% (flags acceptable overlaps)
  - False negative: <5% (misses actual readability issues)

- **Spatial validation:** ≥85% accuracy
  - True positive: Correctly identifies misplaced labels
  - False positive: <15% (flags acceptable placements)
  - False negative: <10% (misses actual spatial errors)

### Performance Targets
- Processing time overhead: <5 seconds per sheet
- Total processing time: <20 seconds (Phase 1 + 2 + 2.1 + 4)
- Memory usage: No significant increase (<50MB additional)

### ROI Targets
- **Time saved per sheet:** 3-5 minutes
  - Eliminate manual QC for overlap checking
  - Automated spatial validation vs manual inspection

- **Annual savings:** 3-5 min × 50 sheets = **2.5-4 hours/year**

- **ROI vs Phase 3:**
  - Phase 3: 3 hours invested for 6 min/year = **negative ROI**
  - Phase 4: 10 hours invested for 2.5-4 hours/year = **positive ROI** by year 3-4

### Quality Improvement Targets
- Reduce permit resubmissions due to QC issues by ≥50%
- Catch critical readability issues before submission (100% on critical overlaps)

---

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_quality_checker.py

def test_bbox_intersection_overlapping():
    """Test intersection calculation for overlapping boxes."""
    bbox1 = (100, 100, 50, 20)
    bbox2 = (120, 105, 50, 20)
    result = calculate_bbox_intersection(bbox1, bbox2)
    assert result == (120, 105, 30, 15)

def test_bbox_intersection_non_overlapping():
    """Test intersection returns None for non-overlapping boxes."""
    bbox1 = (100, 100, 50, 20)
    bbox2 = (200, 200, 50, 20)
    result = calculate_bbox_intersection(bbox1, bbox2)
    assert result is None

def test_overlap_severity_classification():
    """Test severity levels for different overlap percentages."""
    assert classify_overlap_severity(60) == "critical"
    assert classify_overlap_severity(35) == "warning"
    assert classify_overlap_severity(15) == "minor"

def test_proximity_validation_within_threshold():
    """Test spatial validation passes when label is near feature."""
    # ... test implementation

def test_proximity_validation_beyond_threshold():
    """Test spatial validation fails when label is too far."""
    # ... test implementation
```

### Integration Tests
```python
# tests/integration/test_phase4_integration.py

def test_phase4_with_entrada_east():
    """Test Phase 4 on known good sheet (Entrada East page 26)."""
    # Should have minimal QC issues
    result = run_validator_with_phase4("entrada_east_page26.pdf")
    assert result["quality_checks"]["total_qc_issues"] < 3

def test_phase4_with_synthetic_overlaps():
    """Test detection of intentionally created overlapping labels."""
    result = run_validator_with_phase4("synthetic_overlaps.pdf")
    assert result["quality_checks"]["overlapping_labels"]["critical_overlaps"] > 0

def test_phase4_performance_overhead():
    """Test that Phase 4 adds <5 seconds to processing time."""
    # ... test implementation
```

### Test Data Requirements
1. **Entrada East page 26** - Baseline (minimal issues)
2. **Synthetic overlap test PDF** - Overlapping contour labels, SCE markers
3. **Synthetic spatial test PDF** - Misplaced labels, disconnected annotations
4. **Edge case test PDF** - Arrows, leaders, low contrast text

---

## Deliverables

### Code
- ✅ `esc_validator/quality_checker.py` - New module
- ✅ `esc_validator/validator.py` - Updated with QC integration
- ✅ `tests/unit/test_quality_checker.py` - Unit tests
- ✅ `tests/integration/test_phase4_integration.py` - Integration tests

### Documentation
- ✅ `docs/phases/phase-4/PLAN.md` - This file (implementation plan)
- ⏳ `docs/phases/phase-4/IMPLEMENTATION.md` - Technical details (after coding)
- ⏳ `docs/phases/phase-4/TEST_REPORT.md` - Test results (after testing)
- ⏳ `docs/phases/phase-4/SUMMARY.md` - Executive summary (after completion)
- ⏳ `tools/esc-validator/README.md` - Updated with Phase 4 capabilities

### Test Artifacts
- ⏳ Test screenshots (overlap examples, spatial examples)
- ⏳ Test PDFs (synthetic cases)
- ⏳ Test results JSON (from integration tests)

---

## Timeline Estimate

| Task | Duration | Dependencies |
|------|----------|--------------|
| Create quality_checker.py | 2-3 hours | Phase 2.1 complete |
| Integrate with validator | 1-2 hours | quality_checker.py |
| Write unit tests | 1-2 hours | quality_checker.py |
| Create synthetic test data | 1 hour | - |
| Run integration tests | 1 hour | All code complete |
| Debug & tune thresholds | 1-2 hours | Test results |
| Documentation | 1-2 hours | All code complete |

**Total Estimated Time:** 8-12 hours (target: 10 hours)

---

## Decision Points

### After Testing (10 hours invested)

**If accuracy ≥85% on both overlap and spatial validation:**
- ✅ Mark Phase 4 complete
- ✅ Deploy for Christian's testing (2-4 weeks)
- ✅ Monitor false positive rates in real use

**If accuracy 70-84%:**
- ⚠️ Acceptable for MVP
- Deploy with "experimental" flag
- Gather user feedback before refinement

**If accuracy <70%:**
- ❌ Do not deploy
- Analyze failure modes
- **Decision point:** Spend another 5 hours refining OR defer Phase 4 entirely

---

## Deferred Features (Not in Phase 4 Lite)

**Legend Verification:**
- Why deferred: Phase 3 lessons show template matching unreliable
- Alternative: Manual visual verification (5-10 seconds)
- Potential future work: ML-based legend extraction (Phase 6)

**Symbol Standardization:**
- Why deferred: Low ROI, high complexity
- Alternative: Accept symbol variability

**Scale/Dimension Validation:**
- Why deferred: Phase 3 showed scale detection not feasible
- Alternative: Manual verification

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| False positives >15% | Medium | Medium | Tune thresholds, add whitelist |
| Performance >5 sec overhead | Low | Low | Spatial indexing, early exit |
| OCR bounding box inaccuracy | Medium | Low | Add padding, tune thresholds |
| Feature not worth ROI | Low | High | Hard 10-hour time limit |
| Integration breaks existing phases | Low | High | Comprehensive integration tests |

**Overall Risk Level:** LOW-MEDIUM (most risks have straightforward mitigations)

---

## Post-Implementation Review Criteria

**Consider Phase 4 successful if:**
1. ✅ Overlap detection ≥90% accuracy
2. ✅ Spatial validation ≥85% accuracy
3. ✅ Processing overhead <5 seconds
4. ✅ False positive rate <15%
5. ✅ Total implementation time ≤12 hours
6. ✅ No regression in Phase 1/2/2.1 accuracy

**Consider Phase 4 acceptable if:**
1. ⚠️ Overlap detection ≥80% accuracy
2. ⚠️ Spatial validation ≥75% accuracy
3. ⚠️ Processing overhead <8 seconds
4. ⚠️ Implementation time ≤15 hours

**Abort Phase 4 if:**
1. ❌ Any metric below "acceptable" threshold after 12 hours
2. ❌ False positive rate >25% (unusable)
3. ❌ Integration breaks existing phases

---

## Comparison: Original Phase 4 vs Phase 4 Lite

| Aspect | Original Phase 4 | Phase 4 Lite | Reasoning |
|--------|------------------|--------------|-----------|
| **Scope** | Full QC suite | Overlap + spatial only | Phase 3 lesson: focus on high ROI |
| **Legend verification** | Included | DEFERRED | Phase 3 lesson: template matching unreliable |
| **Estimated effort** | 20-30 hours | 8-12 hours | 60% time reduction |
| **Expected accuracy** | 80-90% | 85-95% | Higher confidence with proven techniques |
| **ROI** | 5-8 hours/year | 2.5-4 hours/year | Still positive ROI by year 3-4 |
| **Risk level** | Medium-High | Low-Medium | Builds on Phase 2.1 success |

---

## Next Steps After Phase 4

**Option 1: Test on Diverse Sheets (RECOMMENDED)**
- Test Phase 4 on 5-10 ESC sheets
- Validate accuracy across different projects
- Collect feedback from Christian
- Timeline: 2-4 weeks

**Option 2: Implement Phase 5 (Confidence Scoring)**
- Only if Phase 4 accuracy <85%
- Aggregate confidence from Phases 1-4
- Timeline: 1-2 weeks

**Option 3: Deploy to Production**
- If Phase 4 accuracy >90%
- Monitor real-world usage
- Iterate based on feedback
- Timeline: Immediate

---

## References

**Related Documentation:**
- [Phase 3 Results (North Arrow Investigation)](../phase-3/phase-1.3.2/RESULTS.md) - Lessons learned
- [Phase 2.1 Implementation (Spatial Filtering)](../phase-2/phase-2.1/IMPLEMENTATION.md) - Spatial proximity techniques
- [Phase 2.1 Test Report](../phase-2/phase-2.1/TEST_REPORT.md) - 99% accuracy with spatial filtering
- [Phase 1 Test Report](../phase-1/TEST_REPORT.md) - Text detection results

**Related Code:**
- `esc_validator/text_detector.py:extract_text_with_locations()` - Bounding box extraction
- `esc_validator/symbol_detector.py:verify_contour_conventions_smart()` - Spatial proximity example

---

**Plan Created:** 2025-11-02
**Status:** Ready to implement
**Expected Start:** After Phase 2.1 testing (2-4 weeks)
**Target Version:** ESC Validator v0.3.0
