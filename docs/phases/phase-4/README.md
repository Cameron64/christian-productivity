# Phase 4: Quality Checks (REVISED - "Phase 4 Lite")

**Status:** Ready to Implement (Revised Scope)
**Expected Start:** After Phase 2.1 testing completes (2-4 weeks)
**Expected Duration:** 6-10 hours (reduced from 1 week)
**Accuracy Target:** 85-95% (increased confidence)
**ROI Target:** 2.5-4 hours/year time savings

---

## Revision Notice

**Original Phase 4:** Full QC suite including legend verification
**Revised Phase 4 (Phase 4 Lite):** Focus on high-feasibility, high-ROI components only

**Why Revised:**
- **Phase 3 lessons:** Template matching struggles with variability; low ROI features not worth pursuing
- **Phase 2.1 success:** Spatial proximity techniques work extremely well (99% accuracy)
- **Focus shift:** Proven techniques with clear time savings

**Deferred Features:**
- ❌ Legend verification (low ROI, high risk per Phase 3 lessons)
- ❌ Symbol standardization (low ROI)
- ❌ Scale/dimension validation (Phase 3 proved not feasible)

See [PLAN.md](PLAN.md) for detailed implementation plan.

---

## Overview

Phase 4 Lite implements **only the high-value QC checks** that have proven feasibility based on Phase 2.1 results. This phase focuses on detecting common QC issues that cause permit resubmissions: overlapping labels (readability) and misplaced annotations (spatial errors).

---

## Objectives

### What We're Building
1. ✅ **Overlapping label detection** - Readability QC failures
2. ✅ **Enhanced spatial validation** - Labels near features (extends Phase 2.1)
3. ❌ **Legend verification** - DEFERRED (low ROI, high risk)

### Success Criteria
- Overlapping label detection: ≥90% accuracy
- Spatial validation: ≥85% accuracy
- Processing time overhead: <5 seconds
- False positive rate: <10%
- Zero false negatives on critical overlaps (text completely obscured)

---

## Technical Approach

### 1. Overlapping Label Detection

**Problem:** Text labels overlap, making sheets hard to read and causing permit rejections

**Solution:** Use Phase 2.1's `extract_text_with_locations()` bounding boxes for geometric overlap checking

**Algorithm:**
- Extract all text with bounding boxes (already working)
- Calculate intersection of all text box pairs (O(n²))
- Classify overlap severity:
  - **Critical (>50%):** Text likely unreadable
  - **Warning (20-50%):** May impact readability
  - **Minor (<20%):** Edge touching, likely acceptable

**Expected Performance:** 1-2 seconds, <10% false positives

---

### 2. Enhanced Spatial Validation

**Problem:** Labels placed far from features (e.g., "SCE" 500px from fence)

**Solution:** Extend Phase 2.1's successful 150px proximity filtering to validate label placement

**Proximity Rules:**
```python
PROXIMITY_RULES = {
    "contour_label": 150,   # px - Phase 2.1 validated
    "SCE": 200,             # px - Silt fence markers
    "CONC WASH": 250,       # px - Concrete washout areas
    "storm_drain": 200,     # px - Inlet protection
    "street_label": 300,    # px - Street names
}
```

**Algorithm:**
- For each label, find distance to nearest matching feature
- Flag if distance exceeds threshold
- Classify as "error" (1.5x threshold) or "warning"

**Expected Performance:** 2-3 seconds, <15% false positives

---

### 3. Deferred Features (Not Implementing)

**Legend Verification:** Phase 3 showed template matching unreliable; manual verification is fast (5-10 sec)

**Symbol Standardization:** Low ROI, high complexity

**Scale/Dimension Validation:** Phase 3 proved scale detection not feasible with template matching

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

---

## Planned Deliverables

### Code
- `esc_validator/quality_checker.py` - New QC module
- `esc_validator/validator.py` - Updated with QC integration
- Unit tests for overlap detection
- Integration tests for spatial validation

### Documentation
- ✅ [PLAN.md](PLAN.md) - Detailed implementation plan
- ⏳ IMPLEMENTATION.md - Technical details (after coding)
- ⏳ TEST_REPORT.md - Test results (after testing)
- ⏳ SUMMARY.md - Executive summary (after completion)

### Tests
- Unit tests for bbox intersection, overlap calculation
- Integration tests with real ESC sheets
- Synthetic test cases (overlapping labels, misplaced annotations)

---

## Expected Challenges & Mitigations

### Challenge 1: False Positives on Arrows/Leaders
**Mitigation:** Filter thin bounding boxes (<10px), text-only detection

### Challenge 2: Defining "Near" for Different Features
**Mitigation:** Start with Phase 2.1's validated 150px, test and tune per feature type

### Challenge 3: Performance Overhead
**Mitigation:** Early exit on low-confidence text, spatial indexing, target <5 sec

### Challenge 4: OCR Bounding Box Accuracy
**Mitigation:** Add 5-10px padding, use >20% threshold for "significant overlap"

---

## Success Criteria

### Accuracy
- **Overlapping labels:** ≥90% detection accuracy, <10% false positives
- **Spatial validation:** ≥85% accuracy, <15% false positives

### Performance
- Processing overhead: <5 seconds per sheet
- Total time (Phase 1+2+2.1+4): <20 seconds

### ROI
- **Time saved:** 3-5 min per sheet × 50 sheets = **2.5-4 hours/year**
- **Implementation:** 6-10 hours total
- **Break-even:** Year 3-4 (positive ROI)

### Quality Improvement
- Reduce permit resubmissions due to QC issues by ≥50%
- 100% detection on critical overlaps (completely obscured text)

---

## Comparison: Original vs Lite

| Aspect | Original Phase 4 | Phase 4 Lite |
|--------|------------------|--------------|
| **Scope** | Full QC suite | Overlap + spatial only |
| **Legend verification** | Included | DEFERRED |
| **Estimated effort** | 20-30 hours | 8-12 hours (60% reduction) |
| **Expected accuracy** | 80-90% | 85-95% (higher confidence) |
| **ROI** | 5-8 hours/year | 2.5-4 hours/year |
| **Risk level** | Medium-High | Low-Medium |

---

## Timeline

| Task | Duration |
|------|----------|
| Create quality_checker.py | 2-3 hours |
| Integrate with validator | 1-2 hours |
| Write unit tests | 1-2 hours |
| Create synthetic test data | 1 hour |
| Run integration tests | 1 hour |
| Debug & tune thresholds | 1-2 hours |
| Documentation | 1-2 hours |
| **Total** | **8-12 hours** |

---

## Decision Points

**After Testing (10 hours invested):**

- **If accuracy ≥85%:** Mark complete, deploy for testing
- **If accuracy 70-84%:** Deploy as "experimental", gather feedback
- **If accuracy <70%:** Do not deploy; spend 5 hours refining OR defer entirely

---

**Status:** READY TO IMPLEMENT (after Phase 2.1 testing)
**Version Target:** ESC Validator v0.3.0
**For detailed implementation plan, see:** [PLAN.md](PLAN.md)
