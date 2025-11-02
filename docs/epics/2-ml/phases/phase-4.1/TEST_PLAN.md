# Phase 4.1: PaddleOCR Integration - Testing Plan

**Epic:** 2-ml (Machine Learning Enhancements)
**Phase:** 4.1 (PaddleOCR Integration)
**Status:** Ready for Testing
**Test Date:** TBD
**Tester:** Christian (Primary User)
**Version:** ESC Validator v0.4.0

---

## Table of Contents

1. [Test Overview](#test-overview)
2. [Test Environment Setup](#test-environment-setup)
3. [Unit Tests](#unit-tests)
4. [Integration Tests](#integration-tests)
5. [Performance Tests](#performance-tests)
6. [User Acceptance Tests](#user-acceptance-tests)
7. [Regression Tests](#regression-tests)
8. [Test Data](#test-data)
9. [Success Criteria](#success-criteria)
10. [Test Execution Schedule](#test-execution-schedule)
11. [Issue Tracking](#issue-tracking)

---

## Test Overview

### Objectives

Phase 4.1 introduces PaddleOCR integration with OCR caching to improve performance and accuracy. Testing must validate:

1. **Functional Correctness** - All features work as expected
2. **Performance Improvement** - 52.7s → 15-20s target met
3. **Accuracy** - Text detection ≥75% (no regression)
4. **Backward Compatibility** - Existing workflows unaffected
5. **Reliability** - No memory leaks, no crashes
6. **Fallback Behavior** - Tesseract fallback works correctly

### Test Scope

**In Scope:**
- OCR engine abstraction layer
- PaddleOCR text extraction
- Tesseract fallback
- OCR result caching
- Cache lifecycle management
- Performance benchmarking
- End-to-end validation workflow

**Out of Scope:**
- Phase 1-4 functionality (already tested)
- PDF extraction (no changes)
- Report generation (no changes)
- Symbol detection (no changes)

### Test Types

| Type | Purpose | Duration | Priority |
|------|---------|----------|----------|
| Unit Tests | Test individual components | 1-2 hours | HIGH |
| Integration Tests | Test component interactions | 2-3 hours | HIGH |
| Performance Tests | Validate speed improvements | 1-2 hours | CRITICAL |
| Regression Tests | Ensure no breaking changes | 1 hour | HIGH |
| User Acceptance | Real-world validation | 2-4 hours | CRITICAL |

**Total Estimated Time:** 7-12 hours

---

## Test Environment Setup

### Prerequisites

1. **Python Environment**
   ```bash
   python --version  # Should be 3.8+
   ```

2. **Install Dependencies**
   ```bash
   cd "C:\Users\Cam Dowdle\source\repos\personal\Christian productivity\tools\esc-validator"
   pip install -r requirements.txt
   ```

3. **Verify PaddleOCR Installation**
   ```bash
   python -c "from paddleocr import PaddleOCR; print('PaddleOCR installed successfully')"
   ```

4. **Download Models (First Run)**
   ```bash
   # This will download ~200MB of models (one-time)
   python -c "from esc_validator.ocr_engine import get_ocr_engine; get_ocr_engine('paddleocr')"
   ```

### Test Data Location

```
documents/
└── 5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf

Additional test sheets (if available):
documents/test-sheets/
├── sheet1.pdf  # Diverse project 1
├── sheet2.pdf  # Diverse project 2
└── sheet3.pdf  # Diverse project 3
```

### Environment Variables

```bash
# Optional: Set log level for debugging
export LOG_LEVEL=DEBUG

# Optional: Disable GPU (if available)
export CUDA_VISIBLE_DEVICES=""
```

---

## Unit Tests

### Test Suite 1: OCR Engine Abstraction

**File:** `tests/unit/test_ocr_engine.py` (To Be Created)

#### Test 1.1: PaddleOCR Initialization
```python
def test_paddleocr_initialization():
    """Test PaddleOCR engine initializes successfully."""
    engine = get_ocr_engine("paddleocr")
    assert engine.get_engine_name() == "PaddleOCR"
```

**Expected Result:** ✅ Engine initializes without errors

#### Test 1.2: Tesseract Initialization
```python
def test_tesseract_initialization():
    """Test Tesseract engine initializes successfully."""
    engine = get_ocr_engine("tesseract")
    assert engine.get_engine_name() == "Tesseract"
```

**Expected Result:** ✅ Engine initializes without errors

#### Test 1.3: Invalid Engine Name
```python
def test_invalid_engine_name():
    """Test invalid engine name raises ValueError."""
    with pytest.raises(ValueError):
        get_ocr_engine("invalid_engine")
```

**Expected Result:** ✅ Raises ValueError

#### Test 1.4: OCRResult Format
```python
def test_ocr_result_format():
    """Test OCRResult has correct properties."""
    result = OCRResult(
        text="TEST",
        confidence=85.5,
        bbox=(10, 20, 100, 50)
    )

    assert result.text == "TEST"
    assert result.confidence == 85.5
    assert result.x == 10
    assert result.y == 20
    assert result.width == 90
    assert result.height == 30
    assert result.center_x == 55.0
    assert result.center_y == 35.0
```

**Expected Result:** ✅ All properties calculate correctly

#### Test 1.5: PaddleOCR Text Extraction
```python
def test_paddleocr_text_extraction():
    """Test PaddleOCR extracts text from test image."""
    # Load test image
    image = cv2.imread("tests/fixtures/test_text.png", cv2.IMREAD_GRAYSCALE)

    engine = get_ocr_engine("paddleocr")
    results = engine.extract_text(image)

    assert len(results) > 0
    assert all(isinstance(r, OCRResult) for r in results)
    assert all(r.confidence >= 0 and r.confidence <= 100 for r in results)
```

**Expected Result:** ✅ Extracts text with valid OCRResult objects

#### Test 1.6: Tesseract Text Extraction
```python
def test_tesseract_text_extraction():
    """Test Tesseract extracts text from test image."""
    # Load test image
    image = cv2.imread("tests/fixtures/test_text.png", cv2.IMREAD_GRAYSCALE)

    engine = get_ocr_engine("tesseract")
    results = engine.extract_text(image)

    assert len(results) > 0
    assert all(isinstance(r, OCRResult) for r in results)
```

**Expected Result:** ✅ Extracts text with valid OCRResult objects

#### Test 1.7: Confidence Filtering
```python
def test_confidence_filtering():
    """Test min_confidence parameter filters results."""
    image = cv2.imread("tests/fixtures/test_text.png", cv2.IMREAD_GRAYSCALE)

    engine = get_ocr_engine("paddleocr")
    all_results = engine.extract_text(image, min_confidence=0.0)
    filtered_results = engine.extract_text(image, min_confidence=70.0)

    assert len(filtered_results) <= len(all_results)
    assert all(r.confidence >= 70.0 for r in filtered_results)
```

**Expected Result:** ✅ Low confidence results filtered out

---

### Test Suite 2: OCR Caching

**File:** `tests/unit/test_ocr_caching.py` (To Be Created)

#### Test 2.1: Cache Set and Get
```python
def test_cache_set_and_get():
    """Test OCR cache stores and retrieves results."""
    test_results = [
        OCRResult("TEST1", 90.0, (0, 0, 100, 50)),
        OCRResult("TEST2", 85.0, (100, 0, 200, 50))
    ]

    set_ocr_cache(test_results)
    cached = get_ocr_cache()

    assert cached is not None
    assert len(cached) == 2
    assert cached[0].text == "TEST1"
```

**Expected Result:** ✅ Cache stores and retrieves correctly

#### Test 2.2: Cache Clear
```python
def test_cache_clear():
    """Test cache clears successfully."""
    test_results = [OCRResult("TEST", 90.0, (0, 0, 100, 50))]

    set_ocr_cache(test_results)
    assert get_ocr_cache() is not None

    clear_ocr_cache()
    assert get_ocr_cache() is None
```

**Expected Result:** ✅ Cache clears and returns None

#### Test 2.3: Cache Isolation
```python
def test_cache_isolation():
    """Test cache doesn't leak between tests."""
    clear_ocr_cache()
    assert get_ocr_cache() is None
```

**Expected Result:** ✅ Cache starts empty

#### Test 2.4: Extract Text with Caching
```python
def test_extract_text_with_caching():
    """Test extract_text_from_image populates cache."""
    clear_ocr_cache()

    image = cv2.imread("tests/fixtures/test_text.png", cv2.IMREAD_GRAYSCALE)
    text = extract_text_from_image(image, use_cache=True)

    cached = get_ocr_cache()
    assert cached is not None
    assert len(cached) > 0
```

**Expected Result:** ✅ Cache populated after OCR

#### Test 2.5: Cache Hit
```python
def test_cache_hit():
    """Test subsequent calls use cached results."""
    image = cv2.imread("tests/fixtures/test_text.png", cv2.IMREAD_GRAYSCALE)

    # First call - populates cache
    clear_ocr_cache()
    extract_text_from_image(image, use_cache=True)

    # Second call - should use cache (faster)
    start = time.time()
    extract_text_with_locations(image, use_cached=True)
    elapsed = time.time() - start

    # Should be very fast (< 0.1s) since using cache
    assert elapsed < 0.1
```

**Expected Result:** ✅ Cache hit significantly faster

---

## Integration Tests

### Test Suite 3: End-to-End Pipeline

**File:** `tests/integration/test_paddleocr_pipeline.py` (To Be Created)

#### Test 3.1: Phase 1 → Phase 4 Cache Flow
```python
def test_phase1_to_phase4_cache_flow():
    """Test OCR cache flows from Phase 1 to Phase 4."""
    from esc_validator.validator import validate_esc_sheet
    from esc_validator.ocr_engine import clear_ocr_cache

    clear_ocr_cache()

    result = validate_esc_sheet(
        pdf_path="documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf",
        enable_quality_checks=True,
        ocr_engine="paddleocr"
    )

    assert result["success"] == True
    # Cache should be cleared by validator
    assert get_ocr_cache() is None
```

**Expected Result:** ✅ Full pipeline works with cache

#### Test 3.2: PaddleOCR vs Tesseract Detection Counts
```python
def test_paddleocr_vs_tesseract_detection_counts():
    """Compare detection counts between engines."""
    pdf_path = "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf"

    # Test with PaddleOCR
    result_paddle = validate_esc_sheet(pdf_path, ocr_engine="paddleocr")

    # Test with Tesseract
    result_tess = validate_esc_sheet(pdf_path, ocr_engine="tesseract")

    # Detection counts should be similar (±20%)
    paddle_count = result_paddle["summary"]["passed"]
    tess_count = result_tess["summary"]["passed"]

    diff_pct = abs(paddle_count - tess_count) / max(paddle_count, tess_count)
    assert diff_pct < 0.20  # Within 20%
```

**Expected Result:** ✅ Detection counts similar

#### Test 3.3: Quality Checks Use Cached OCR
```python
def test_quality_checks_use_cached_ocr():
    """Verify Phase 4 uses cached OCR from Phase 1."""
    import logging
    from esc_validator.quality_checker import logger as qc_logger

    # Enable logging to capture cache hit message
    qc_logger.setLevel(logging.INFO)

    with patch.object(qc_logger, 'info') as mock_log:
        result = validate_esc_sheet(
            pdf_path="documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf",
            enable_quality_checks=True
        )

        # Check if cache hit message was logged
        cache_hit_logged = any(
            "Using cached OCR results" in str(call)
            for call in mock_log.call_args_list
        )

        assert cache_hit_logged == True
```

**Expected Result:** ✅ Logs confirm cache usage

#### Test 3.4: Fallback to Tesseract
```python
def test_fallback_to_tesseract():
    """Test fallback to Tesseract if PaddleOCR fails."""
    # Mock PaddleOCR to fail
    with patch('esc_validator.ocr_engine.PaddleOCR', side_effect=ImportError):
        engine = get_ocr_engine("paddleocr")

        # Should fall back to Tesseract
        assert engine.get_engine_name() == "Tesseract"
```

**Expected Result:** ✅ Falls back gracefully

---

## Performance Tests

### Test Suite 4: Performance Benchmarking

**File:** `benchmark_ocr.py` (Already Created)

#### Test 4.1: Tesseract Baseline Performance
```bash
python benchmark_ocr.py \
    "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf" \
    --engine tesseract \
    --runs 3
```

**Expected Result:**
- Average time: ~50-55 seconds
- Consistent across runs (±5 seconds)

**Success Criteria:** ✅ Baseline established

#### Test 4.2: PaddleOCR Performance
```bash
python benchmark_ocr.py \
    "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf" \
    --engine paddleocr \
    --runs 3
```

**Expected Result:**
- Average time: **15-20 seconds**
- Consistent across runs (±3 seconds)

**Success Criteria:** ✅ **<20 seconds target met**

#### Test 4.3: Engine Comparison
```bash
python benchmark_ocr.py \
    "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf" \
    --engine both \
    --runs 3
```

**Expected Result:**
- PaddleOCR **3x faster** than Tesseract
- Speedup: 2.5x - 3.5x
- Improvement: 60-70%

**Success Criteria:** ✅ **3x speedup achieved**

#### Test 4.4: Memory Usage
```python
def test_memory_usage():
    """Test memory usage stays reasonable."""
    import psutil
    import os

    process = psutil.Process(os.getpid())

    # Baseline memory
    clear_ocr_cache()
    baseline_mb = process.memory_info().rss / 1024 / 1024

    # Run validation
    result = validate_esc_sheet(
        "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf",
        enable_quality_checks=True
    )

    # Memory after validation (cache should be cleared)
    after_mb = process.memory_info().rss / 1024 / 1024

    # Memory increase should be < 50 MB
    memory_increase = after_mb - baseline_mb
    assert memory_increase < 50
```

**Expected Result:** ✅ Memory increase < 50 MB

#### Test 4.5: No Memory Leaks
```python
def test_no_memory_leaks():
    """Test repeated validations don't leak memory."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    baseline_mb = process.memory_info().rss / 1024 / 1024

    # Run 5 validations
    for i in range(5):
        result = validate_esc_sheet(
            "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf",
            enable_quality_checks=True
        )

        # Memory should stabilize (not grow linearly)
        current_mb = process.memory_info().rss / 1024 / 1024

    # Total increase should be < 100 MB (not 5x the single run)
    total_increase = current_mb - baseline_mb
    assert total_increase < 100
```

**Expected Result:** ✅ No linear memory growth

---

## User Acceptance Tests

### Test Suite 5: Real-World Validation

#### Test 5.1: Entrada East ESC Sheet (Baseline)
```bash
python validate_esc.py \
    "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf" \
    --enable-quality-checks \
    --output-format json \
    --output uat-test-1.json
```

**Manual Verification:**
1. Open JSON report
2. Verify all expected elements detected:
   - ✅ Legend
   - ✅ Scale
   - ✅ North arrow
   - ✅ SCE (Stabilized Construction Entrance)
   - ✅ CONC WASH (Concrete Washout)
   - ✅ LOC (Limit of Construction)
   - ✅ Silt Fence
   - ✅ Streets labeled
3. Check quality issues flagged
4. Compare with manual review

**Success Criteria:**
- ✅ All critical elements detected (SCE, CONC WASH)
- ✅ Processing time < 20 seconds
- ✅ Quality issues reasonable (not excessive false positives)

#### Test 5.2: Diverse Project Sheets
```bash
# Test on 3-5 different ESC sheets from different projects
for sheet in sheet1.pdf sheet2.pdf sheet3.pdf; do
    python validate_esc.py "documents/test-sheets/$sheet" \
        --enable-quality-checks \
        --output "uat-$sheet.json"
done
```

**Manual Verification for Each:**
1. Review detection results
2. Check for false positives/negatives
3. Verify performance < 20s
4. Compare quality to Tesseract baseline (if needed)

**Success Criteria:**
- ✅ Consistent performance across sheets
- ✅ Accuracy ≥75% on all sheets
- ✅ No crashes or errors

#### Test 5.3: Edge Cases

**Test 5.3a: Low Quality Scan**
- Test with poor quality PDF (if available)
- **Expected:** Lower confidence scores, but no crash

**Test 5.3b: Rotated Sheet**
- Test with rotated ESC sheet (if available)
- **Expected:** PaddleOCR handles rotation better than Tesseract

**Test 5.3c: Hand-Drawn Notes**
- Test with sheet containing hand-drawn annotations
- **Expected:** Handles gracefully, flags low confidence

**Test 5.3d: Large Sheet (200+ DPI)**
- Test with high-resolution sheet
- **Expected:** Slower but accurate, no memory issues

---

## Regression Tests

### Test Suite 6: Backward Compatibility

#### Test 6.1: Existing Unit Tests Pass
```bash
cd tests
pytest unit/ -v
```

**Expected Result:** ✅ All existing unit tests pass

#### Test 6.2: Existing Integration Tests Pass
```bash
pytest integration/ -v
```

**Expected Result:** ✅ All existing integration tests pass

#### Test 6.3: Phase 1 Text Detection Accuracy
```python
def test_phase1_accuracy_maintained():
    """Verify Phase 1 accuracy ≥75% with PaddleOCR."""
    # Run validation
    result = validate_esc_sheet(
        "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf",
        ocr_engine="paddleocr"
    )

    # Check pass rate
    pass_rate = result["summary"]["pass_rate"]
    assert pass_rate >= 0.75  # 75% minimum
```

**Expected Result:** ✅ Accuracy ≥75%

#### Test 6.4: Phase 2 Line Detection
```python
def test_phase2_line_detection_works():
    """Verify Phase 2 line detection still works."""
    result = validate_esc_sheet(
        "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf",
        enable_line_detection=True
    )

    assert "line_verification" in result
    assert result["line_verification"] is not None
```

**Expected Result:** ✅ Line detection unaffected

#### Test 6.5: Default Engine is PaddleOCR
```python
def test_default_engine_is_paddleocr():
    """Verify PaddleOCR is default engine."""
    # Call without specifying engine
    result = validate_esc_sheet(
        "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf"
    )

    # Should succeed (using PaddleOCR by default)
    assert result["success"] == True
```

**Expected Result:** ✅ PaddleOCR used by default

---

## Test Data

### Primary Test Sheet
- **File:** `documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf`
- **Page:** 26 (ESC sheet)
- **Known Ground Truth:**
  - Has SCE markers
  - Has CONC WASH markers
  - Has silt fence labels
  - Has street labels
  - Has contour lines (existing and proposed)

### Additional Test Sheets (If Available)
- **Sheet 1:** Different project, similar format
- **Sheet 2:** Different drafter, different style
- **Sheet 3:** Older project, possibly lower quality scan

### Test Fixtures
Create simple test images for unit tests:
```
tests/fixtures/
├── test_text.png          # Simple text labels
├── test_overlapping.png   # Overlapping labels
├── test_rotated.png       # Rotated text
└── test_low_quality.png   # Poor quality scan
```

---

## Success Criteria

### Phase 4.1 Must Pass ALL of These:

#### Performance Criteria
- [  ] **Processing time < 20 seconds** @ 150 DPI with quality checks enabled
- [  ] PaddleOCR **2.5-3.5x faster** than Tesseract
- [  ] Memory usage < 600 MB during validation
- [  ] No memory leaks over multiple runs

#### Accuracy Criteria
- [  ] Text detection accuracy **≥75%** (Phase 1 baseline maintained)
- [  ] **0% false negatives** on critical items (SCE, CONC WASH)
- [  ] Detection counts within **20%** of Tesseract baseline
- [  ] Quality checks produce reasonable results (not excessive false positives)

#### Reliability Criteria
- [  ] **Zero crashes** during testing
- [  ] Graceful fallback to Tesseract if PaddleOCR unavailable
- [  ] Cache properly cleared (no lingering references)
- [  ] Works on 5+ diverse ESC sheets

#### Compatibility Criteria
- [  ] **All existing unit tests pass**
- [  ] **All existing integration tests pass**
- [  ] No breaking changes to API
- [  ] Default behavior works (PaddleOCR as primary)

#### Documentation Criteria
- [  ] Test results documented
- [  ] Performance benchmarks recorded
- [  ] Known issues identified and documented
- [  ] User acceptance sign-off obtained

---

## Test Execution Schedule

### Phase 1: Automated Testing (2-3 hours)
**Timeframe:** Day 1, Morning

1. **Setup** (30 min)
   - Install dependencies
   - Download PaddleOCR models
   - Prepare test data

2. **Unit Tests** (1 hour)
   - Create and run unit test suites
   - Fix any failures
   - Document results

3. **Integration Tests** (1-1.5 hours)
   - Create and run integration tests
   - Verify cache flow
   - Check fallback behavior

### Phase 2: Performance Testing (1-2 hours)
**Timeframe:** Day 1, Afternoon

1. **Baseline Benchmark** (30 min)
   - Run Tesseract baseline (3 runs)
   - Record average time

2. **PaddleOCR Benchmark** (30 min)
   - Run PaddleOCR (3 runs)
   - Record average time
   - Calculate speedup

3. **Memory Testing** (30 min)
   - Profile memory usage
   - Test for leaks
   - Document findings

### Phase 3: User Acceptance Testing (2-4 hours)
**Timeframe:** Day 2

1. **Entrada East Validation** (30 min)
   - Run validation
   - Manual review of results
   - Compare to expected

2. **Diverse Sheets** (1-2 hours)
   - Test on 5+ different sheets
   - Document accuracy per sheet
   - Note any issues

3. **Edge Cases** (30 min)
   - Test problematic sheets
   - Verify graceful handling

4. **User Sign-Off** (30 min)
   - Review results with Christian
   - Get feedback
   - Document acceptance

### Phase 4: Regression Testing (1 hour)
**Timeframe:** Day 2, Final

1. **Run Existing Tests** (30 min)
   - Unit tests
   - Integration tests

2. **Verify No Breaking Changes** (30 min)
   - Check Phase 1-4 functionality
   - Validate reports unchanged
   - Confirm CLI works

---

## Issue Tracking

### Issue Template

```markdown
## Issue #X: [Brief Description]

**Severity:** Critical / High / Medium / Low
**Test:** [Test ID where found]
**Component:** [OCR Engine / Caching / Validator / etc.]

**Description:**
[Detailed description of the issue]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Workaround:**
[If any]

**Status:** Open / In Progress / Resolved / Deferred
```

### Issue Log

Track all issues found during testing:

| ID | Severity | Description | Status | Resolution |
|----|----------|-------------|--------|------------|
| 1  |          |             |        |            |
| 2  |          |             |        |            |

---

## Test Report Template

After testing, create `TEST_REPORT.md`:

```markdown
# Phase 4.1 Test Report

**Test Date:** [Date]
**Tester:** [Name]
**Version Tested:** ESC Validator v0.4.0

## Summary
- Tests Run: X
- Tests Passed: X
- Tests Failed: X
- Pass Rate: X%

## Performance Results
- Tesseract Baseline: X seconds
- PaddleOCR: X seconds
- Speedup: Xx
- Target Met: ✅ / ❌

## Accuracy Results
- Text Detection: X%
- Critical Items: X%
- Baseline Maintained: ✅ / ❌

## Issues Found
[List of issues with IDs]

## Recommendation
☐ PASS - Ready for production
☐ CONDITIONAL PASS - Minor issues, deploy with caveats
☐ FAIL - Major issues, requires fixes

## Sign-Off
Tester: _________________ Date: _______
User (Christian): ________ Date: _______
```

---

## Next Steps After Testing

### If Tests Pass
1. Update version to v0.4.0 (Release)
2. Deploy to production
3. Monitor performance in real use
4. Collect user feedback
5. Plan Phase 4.2 (ML overlap filter)

### If Tests Fail
1. Document all failures in Issue Log
2. Prioritize critical issues
3. Fix high-priority issues
4. Re-run affected tests
5. Repeat until success criteria met

### If Performance Target Not Met
1. Profile to find bottlenecks
2. Consider optimizations:
   - Adjust OCR parameters
   - Optimize image preprocessing
   - Reduce model complexity
3. Re-evaluate target (<20s may need adjustment)
4. Consider hybrid approach (PaddleOCR for some, Tesseract for others)

---

## Appendix A: Quick Test Commands

```bash
# Setup
cd "C:\Users\Cam Dowdle\source\repos\personal\Christian productivity\tools\esc-validator"
pip install -r requirements.txt

# Unit Tests
pytest tests/unit/test_ocr_engine.py -v
pytest tests/unit/test_ocr_caching.py -v

# Integration Tests
pytest tests/integration/test_paddleocr_pipeline.py -v

# Performance Benchmark
python benchmark_ocr.py "../../documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf" --runs 3

# Quick Validation
python validate_esc.py "../../documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf" --enable-quality-checks

# Memory Profiling
python -m memory_profiler validate_esc.py "../../documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf"
```

---

## Appendix B: Troubleshooting

### Issue: PaddleOCR Models Not Downloading
**Solution:** Manually download from PaddleOCR repo or check internet connection

### Issue: Import Error for PaddleOCR
**Solution:** Reinstall with `pip install --force-reinstall paddleocr`

### Issue: Performance Worse Than Expected
**Solution:** Check DPI setting, ensure CPU not throttled, close other applications

### Issue: Memory Usage Too High
**Solution:** Check cache is being cleared, reduce DPI, test on smaller image

### Issue: Tests Failing on Windows Paths
**Solution:** Use raw strings (r"path") or Path objects, not regular strings

---

**Test Plan Version:** 1.0
**Created:** 2025-11-02
**Last Updated:** 2025-11-02
**Status:** Ready for Execution
**Owner:** Christian (with Claude assistance)
