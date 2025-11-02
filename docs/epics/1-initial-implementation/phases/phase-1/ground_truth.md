# Test Case: Entrada East Subdivision (5620-01)

## Test Information

**Test ID:** TC-001
**Date Created:** 2025-11-01
**PDF File:** `5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf`
**File Size:** 69 MB
**Total Pages:** Unknown (large drawing set)
**Page Tested:** Page 1 (auto-detected by tool)

## Sheet Information

**Sheet Type:** Cover/Title Sheet (NOT actual ESC sheet)
**Sheet Title:** "ENTRADA EAST SUBDIVISION - STREET, DRAINAGE, WATER, AND WASTEWATER IMPROVEMENTS"
**Location:** Travis County - City of Austin ETJ
**Project Number:** 5620-01

**Note:** The validator auto-detected page 1 as the "ESC sheet" because it contains the word "EROSION" in the notes section. However, this is actually a cover sheet with a location map, not the dedicated ESC plan sheet.

---

## Ground Truth Annotation

Based on visual inspection of the extracted preprocessed image, here is the manual annotation:

### Required Elements (ESC Checklist)

| # | Element | Present? | Count | Location/Notes | Confidence |
|---|---------|----------|-------|----------------|------------|
| 1 | **Legend** | ✅ YES | 1 | Bottom left corner, appears to be a table/legend | HIGH |
| 2 | **Scale** | ❓ UNCERTAIN | ? | May be present in location map or notes | MEDIUM |
| 3 | **North Bar** | ✅ YES | 1 | Visible north arrow on location map | HIGH |
| 4 | **Limits of Construction (LOC)** | ❌ NO | 0 | This is a cover sheet, not a construction plan | HIGH |
| 5 | **Silt Fence (SF)** | ❌ NO | 0 | This is a cover sheet, no ESC features shown | HIGH |
| 6 | **Stabilized Construction Entrance (SCE)** | ❌ NO | 0 | This is a cover sheet, no ESC features shown | HIGH |
| 7 | **Concrete Washout** | ❌ NO | 0 | This is a cover sheet, no ESC features shown | HIGH |
| 8 | **Staging/Spoils Area** | ❌ NO | 0 | This is a cover sheet, no ESC features shown | HIGH |
| 9 | **Existing Contours Labeled** | ❌ NO | 0 | Location map only, no detailed contours | HIGH |
| 10 | **Proposed Contours Labeled** | ❌ NO | 0 | Location map only, no detailed contours | HIGH |
| 11 | **Streets Labeled** | ✅ YES | Multiple | Location map shows street context | MEDIUM |
| 12 | **Lot and Block Labels** | ❓ UNCERTAIN | ? | May be referenced in notes | LOW |

### Ground Truth Summary

**This is NOT an ESC Plan Sheet - It's a Title/Cover Sheet**

**Expected Results for a proper ESC sheet would be:**
- Legend: YES
- Scale: YES
- North Bar: YES
- LOC: YES (perimeter line around construction)
- SF: YES (silt fence around perimeter)
- SCE: YES (at site entrance)
- CONC WASH: YES (designated washout area)
- Staging: YES (material storage area)
- Contours: YES (both existing and proposed)
- Streets: YES
- Lot/Block: YES

**For THIS cover sheet, expected accurate results:**
- Legend: YES (table at bottom)
- Scale: Maybe (in location map)
- North Bar: YES (on location map)
- LOC: NO (not a construction drawing)
- SF: NO (not shown)
- SCE: NO (not shown)
- CONC WASH: NO (not shown)
- Staging: NO (not shown)
- Contours: NO (location map only)
- Streets: YES (street names visible)
- Lot/Block: Maybe (in notes)

---

## Test Observations

### Issue #1: Wrong Sheet Detected

**Problem:** The validator detected page 1 (cover sheet) as the ESC sheet instead of finding the actual ESC plan sheet in the drawing set.

**Root Cause:** The cover sheet contains the word "EROSION" in the general notes section, which triggered the ESC sheet detection logic.

**Impact:** Validation ran on wrong sheet, results are not meaningful for ESC compliance.

**Recommendation:**
- Improve ESC sheet detection logic to look for multiple keywords
- Require "ESC" or "EROSION AND SEDIMENT CONTROL PLAN" in sheet title
- Add page number pattern matching (ESC sheets often numbered like "EC-1" or "ESC-1")

### Issue #2: False Positives on Cover Sheet

**Problem:** The validator detected elements that don't make sense for a cover sheet:
- 346 "north" occurrences (likely from notes/text, not north bars)
- 103 "street" occurrences (excessive for location map)
- 12 "existing contour" labels (no contours on this sheet)

**Root Cause:** Keyword matching without spatial context - counting every occurrence of words in text blocks.

**Impact:** Inflated counts give false confidence in element presence.

**Recommendation:**
- Add spatial filtering (contour labels should be near contour lines)
- Exclude text from notes sections
- Set reasonable maximum thresholds (e.g., >100 occurrences = likely false positive)

### Issue #3: Scale Not Detected

**Problem:** Scale may be present in location map but not detected.

**Possible Reasons:**
- Graphical scale bar (not text)
- Non-standard format
- Small text not OCR'd correctly

**Recommendation:** Add Phase 3 symbol detection for graphical scales

---

## Validator Test Results (Actual)

**Command Run:**
```bash
python validate_esc.py "../../documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf" \
  --output validation_report.md --save-images --output-dir validation_output
```

**Processing Time:** ~15 seconds
**Text Extracted:** 7,106 characters
**Status:** ⚠️ NEEDS REVIEW
**Pass Rate:** 8/12 (67%)
**Average Confidence:** 84%

### Element Detection Results

| Element | Tool Result | Ground Truth | Match? | Notes |
|---------|-------------|--------------|--------|-------|
| Legend | ✅ PASS (90%) | ✅ YES | ✅ **CORRECT** | Table/legend present |
| Scale | ❌ FAIL | ❓ UNCERTAIN | ⚠️ **UNCERTAIN** | May exist, needs manual check |
| North Bar | ✅ PASS (95%, 346 ct) | ✅ YES | ⚠️ **INFLATED** | Correct presence, but 346 count is false positive |
| LOC | ✅ PASS (95%, 5 ct) | ❌ NO | ❌ **FALSE POS** | "LOC" likely in notes, not actual LOC feature |
| Silt Fence | ❌ FAIL | ❌ NO | ✅ **CORRECT** | Not present (cover sheet) |
| SCE | ❌ FAIL | ❌ NO | ✅ **CORRECT** | Not present (cover sheet) |
| CONC WASH | ❌ FAIL | ❌ NO | ✅ **CORRECT** | Not present (cover sheet) |
| Staging | ✅ PASS (90%, 1 ct) | ❌ NO | ❌ **FALSE POS** | Likely "staging" in notes |
| Existing Contours | ✅ PASS (70%, 12 ct) | ❌ NO | ❌ **FALSE POS** | No contours on cover sheet |
| Proposed Contours | ✅ PASS (70%, 4 ct) | ❌ NO | ❌ **FALSE POS** | No contours on cover sheet |
| Streets | ✅ PASS (95%, 103 ct) | ✅ YES | ⚠️ **INFLATED** | Streets present, but 103 count is excessive |
| Lot/Block | ✅ PASS (70%, 7 ct) | ❓ UNCERTAIN | ⚠️ **UNCERTAIN** | May be referenced in notes |

### Accuracy Analysis

**True Positives:** 2-4 (Legend, North Bar, Streets, possibly Lot/Block)
**False Positives:** 4-6 (LOC, Staging, Contours - not actually present as features)
**True Negatives:** 3 (SF, SCE, CONC WASH - correctly not detected)
**False Negatives:** 0-1 (Scale - may be present but not detected)

**Precision:** 2-4 out of 8 = **25-50%** (of detected elements, how many are correct?)
**Recall:** 2-4 out of 3-5 = **40-80%** (of present elements, how many were detected?)

---

## Recommendations for Improvement

### Priority 1: Fix ESC Sheet Detection

**Problem:** Tool detected wrong sheet (cover sheet instead of ESC plan)

**Solutions:**
1. Require "ESC" or "EROSION AND SEDIMENT CONTROL PLAN" in page text
2. Look for sheet number patterns: "EC-", "ESC-", "SWPPP-"
3. Check for presence of multiple ESC keywords (not just one mention)
4. Add visual detection of typical ESC plan features (silt fence symbols)

**Implementation:**
```python
def find_esc_sheet(pdf_path):
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        text_upper = text.upper()

        # Score each page
        score = 0
        if "ESC" in text_upper and "PLAN" in text_upper: score += 5
        if "EROSION AND SEDIMENT CONTROL" in text_upper: score += 5
        if "SILT FENCE" in text_upper: score += 2
        if "CONSTRUCTION ENTRANCE" in text_upper: score += 2
        if "WASHOUT" in text_upper: score += 1

        # Requires minimum score
        if score >= 7:
            return page_num
```

### Priority 2: Reduce False Positives

**Problem:** Counting keyword mentions in notes/text as actual features

**Solutions:**
1. Filter out text from legend/notes regions
2. Set maximum occurrence thresholds
3. Add spatial context checking (Phase 2+)
4. Require proximity to visual features (lines, symbols)

**Implementation:**
```python
# Flag suspicious high counts
if count > 50:
    confidence *= 0.5  # Reduce confidence
    notes = f"Suspiciously high count ({count}), may include false positives"
```

### Priority 3: Better Reporting

**Problem:** Report doesn't indicate when wrong sheet is analyzed

**Solution:** Add sheet validation warning
```markdown
## ⚠️ Sheet Verification Warning

This sheet may not be an ESC plan sheet:
- No silt fence symbols detected
- No construction entrance symbols detected
- Excessive keyword occurrences suggest notes/text rather than plan features

Recommendation: Manually verify this is the correct ESC sheet.
```

---

## Test Case Conclusions

### Test Outcome: ⚠️ PARTIALLY SUCCESSFUL

**What Worked:**
- ✅ Tool ran without errors
- ✅ Extracted text successfully (7,106 characters)
- ✅ Generated report
- ✅ Correctly did NOT detect critical ESC features (SF, SCE, CONC_WASH) on cover sheet

**What Needs Improvement:**
- ❌ Detected wrong sheet (cover sheet, not ESC plan)
- ❌ Multiple false positives (LOC, Staging, Contours)
- ❌ Inflated occurrence counts (346 "north", 103 "streets")
- ❌ No warning that sheet may not be ESC plan

**Overall Assessment:**
The tool's core functionality works (extraction, OCR, detection, reporting), but the **ESC sheet identification** logic needs significant improvement. The false positive rate is high when run on non-ESC sheets.

**Recommendation:**
Before running more test cases, we should:
1. Find the actual ESC sheet in this drawing set
2. Re-run test on correct sheet
3. Implement improved sheet detection logic

---

## Next Steps

1. **Manually locate ESC sheet:** Search PDF for sheet labeled "ESC", "EC-1", or "EROSION CONTROL PLAN"
2. **Re-run test:** Use `--page` flag to specify correct ESC sheet
3. **Document real results:** Record accuracy on actual ESC plan sheet
4. **Implement improvements:** Fix sheet detection and false positive issues
5. **Add test suite:** Automated tests with multiple ESC sheets

---

**Test Case Prepared By:** Claude (via Claude Code)
**Date:** 2025-11-01
**Status:** DRAFT - Needs re-test on actual ESC sheet
