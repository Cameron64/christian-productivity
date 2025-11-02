# Test Migration Guide

How to migrate existing ad-hoc test scripts to the new pytest architecture.

---

## Overview

**Old Approach:**
- Ad-hoc test scripts (`test_phase_1_3_1.py`, `test_phase_2.py`, etc.)
- Manual CLI execution
- Hardcoded file paths
- No CI/CD integration
- Difficult to maintain

**New Approach:**
- Pytest-based test suite
- Automatic test discovery
- Fixtures for test data
- CI/CD integration (GitHub Actions)
- Organized by test type (unit/integration/e2e)

---

## Migration Steps

### Step 1: Identify Test Type

For each existing test file, determine its category:

| If the test... | Then it's... | Migrate to... |
|---------------|--------------|---------------|
| Tests a single function with no I/O | Unit test | `tests/unit/` |
| Tests interaction between modules | Integration test | `tests/integration/` |
| Tests full CLI workflow | E2E test | `tests/e2e/` |
| Benchmarks performance | Performance test | `tests/performance/` |

### Step 2: Extract Reusable Components

Before migrating, identify:

1. **Test data:** Move to `tests/fixtures/`
2. **Helper functions:** Move to `tests/utils/`
3. **Common assertions:** Move to `tests/utils/assertions.py`
4. **Mock objects:** Move to `tests/utils/mocks.py`

### Step 3: Convert to Pytest

**Old Pattern:**
```python
# test_phase_2_1.py (ad-hoc script)
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path")
    args = parser.parse_args()

    # Test logic
    image = extract_page_as_image(args.pdf_path, 26)
    result = verify_contour_conventions_smart(image, ...)

    # Manual assertion
    print(f"Detected {len(result['contours'])} contours")
    if len(result['contours']) < 20:
        print("[PASS]")
    else:
        print("[FAIL]")

if __name__ == "__main__":
    main()
```

**New Pattern:**
```python
# tests/integration/test_spatial_filtering.py (pytest)
import pytest

@pytest.mark.integration
@pytest.mark.esc
def test_spatial_filtering_reduces_false_positives(sample_esc_pdf):
    """Phase 2.1: Should filter 857 lines to ~9 contours."""
    # Fixture provides PDF path
    image = extract_page_as_image(str(sample_esc_pdf), page_num=26)
    result = verify_contour_conventions_smart(image, max_distance=150)

    # Pytest assertion with descriptive message
    assert len(result['contours']) < 20, \
        f"Expected <20 contours after filtering, got {len(result['contours'])}"

    # Additional assertions
    assert result['filter_effectiveness'] > 0.8
```

---

## Example Migrations

### Example 1: Unit Test

**Before: `test_phase_1_3_1.py`** (lines 41-90)
```python
def test_phase_1_3_1(pdf_path, page_num=16, verbose=False):
    """Test Phase 1.3.1 improvements."""
    image = extract_page_as_image(str(pdf_path), page_num, dpi=150)
    text = extract_text_from_image(preprocess_for_ocr(image))
    sheet_type = detect_sheet_type(preprocessed, text)
    print(f"Sheet Type: {sheet_type.upper()}")
```

**After: `tests/unit/test_sheet_detection.py`**
```python
import pytest

@pytest.mark.unit
@pytest.mark.esc
def test_detect_sheet_type_esc_notes(sample_text_image):
    """Should detect ESC notes sheet type."""
    text = "EROSION AND SEDIMENT CONTROL NOTES"
    sheet_type = detect_sheet_type(sample_text_image, text)
    assert sheet_type == "notes"

@pytest.mark.unit
@pytest.mark.esc
def test_detect_sheet_type_plan(sample_text_image):
    """Should detect plan sheet type."""
    text = "PLAN VIEW SHEET 5 KOTI WAY"
    sheet_type = detect_sheet_type(sample_text_image, text)
    assert sheet_type == "plan"
```

### Example 2: Integration Test

**Before: `test_phase_2.py`**
```python
def test_phase_2(pdf_path, page_num=26):
    """Test line detection."""
    image = extract_page_as_image(pdf_path, page_num)
    result = verify_contour_conventions(image, text)
    print(f"Detected {result['total_lines']} lines")
```

**After: `tests/integration/test_line_detection.py`**
```python
@pytest.mark.integration
@pytest.mark.esc
@pytest.mark.skip(reason="Requires real PDF fixture")
def test_line_detection_on_esc_sheet(sample_esc_pdf):
    """Phase 2: Should detect all lines on ESC sheet."""
    image = extract_page_as_image(str(sample_esc_pdf), page_num=26)
    preprocessed = preprocess_for_ocr(image)
    text = extract_text_from_image(preprocessed)

    result = verify_contour_conventions(preprocessed, text)

    assert 'total_lines' in result
    assert result['total_lines'] > 100, "Should detect >100 lines"
    assert 'solid_lines' in result
    assert 'dashed_lines' in result
```

### Example 3: E2E Test

**Before: Manual CLI test**
```bash
python validate_esc.py "drawing.pdf" --page 16 --output report.md
# Manually check report.md
```

**After: `tests/e2e/test_cli_validation.py`**
```python
import subprocess

@pytest.mark.e2e
@pytest.mark.esc
def test_validate_esc_cli_generates_report(tmp_path, sample_esc_pdf):
    """Should run CLI validation and generate markdown report."""
    output_file = tmp_path / "report.md"

    result = subprocess.run([
        "python",
        "tools/esc-validator/validate_esc.py",
        str(sample_esc_pdf),
        "--page", "16",
        "--output", str(output_file)
    ], capture_output=True, text=True, timeout=60)

    # Assert command succeeded
    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Assert report was created
    assert output_file.exists(), "Report file not created"

    # Assert report has expected content
    report_content = output_file.read_text()
    assert "PASS" in report_content or "FAIL" in report_content
    assert "north_bar" in report_content
    assert "sce" in report_content
```

---

## Converting Assertions

### Old Style (Print and Manual Check)

```python
# Old
print(f"Detected: {result}")
if result > 5:
    print("[PASS]")
else:
    print("[FAIL]")
```

### New Style (Pytest Assertions)

```python
# New
assert result > 5, f"Expected >5 items, got {result}"
```

### Complex Assertions

```python
# Old
if 'contours' in result and len(result['contours']) < 20:
    print("[PASS] Contours filtered")
else:
    print("[FAIL] Filtering ineffective")

# New
assert 'contours' in result, "Missing 'contours' key in result"
assert len(result['contours']) < 20, \
    f"Expected <20 contours, got {len(result['contours'])}"
```

---

## Converting Fixtures

### Old Style (Hardcoded Paths)

```python
# Old
pdf_path = "C:/Users/Christian/projects/drawing.pdf"
template_path = "templates/north_arrow.png"
```

### New Style (Pytest Fixtures)

```python
# In conftest.py
@pytest.fixture(scope="session")
def sample_esc_pdf():
    return FIXTURES_DIR / "pdfs" / "esc_sheet_valid.pdf"

@pytest.fixture(scope="session")
def north_arrow_template():
    return FIXTURES_DIR / "images" / "north_arrow_template.png"

# In test
def test_with_fixtures(sample_esc_pdf, north_arrow_template):
    # Fixtures injected automatically
    assert sample_esc_pdf.exists()
    assert north_arrow_template.exists()
```

---

## Converting Parametrized Tests

### Old Style (Multiple Similar Tests)

```python
# Old
def test_contour_label_250():
    assert is_contour_label("250.5")

def test_contour_label_100():
    assert is_contour_label("100")

def test_contour_label_abc():
    assert not is_contour_label("abc")
```

### New Style (Parametrize)

```python
# New
@pytest.mark.parametrize("text,expected", [
    ("250.5", True),
    ("100", True),
    ("abc", False),
    ("25", False),
])
def test_is_contour_label(text, expected):
    assert is_contour_label(text) == expected
```

---

## Migration Checklist

For each old test file:

- [ ] Identify test category (unit/integration/e2e)
- [ ] Extract hardcoded paths to fixtures
- [ ] Extract helper functions to `tests/utils/`
- [ ] Convert print statements to assertions
- [ ] Add pytest markers (`@pytest.mark.unit`, etc.)
- [ ] Add descriptive docstrings
- [ ] Parametrize similar tests
- [ ] Run pytest to verify migration
- [ ] Update CI/CD if needed
- [ ] Delete old test file

---

## Testing the Migration

After migrating a test:

```bash
# 1. Run the migrated test
pytest tests/unit/test_migrated.py -v

# 2. Verify it's discovered
pytest --collect-only | grep test_migrated

# 3. Check markers
pytest --markers | grep unit

# 4. Run with coverage
pytest tests/unit/test_migrated.py --cov=tools
```

---

## Common Issues

### Issue: "Fixture not found"

**Problem:** Test references fixture that doesn't exist

**Solution:**
1. Check `tests/conftest.py` for fixture definition
2. Add fixture if missing
3. Ensure fixture file exists in `tests/fixtures/`

### Issue: "Import errors"

**Problem:** Can't import module under test

**Solution:**
1. Verify project root is in path
2. Check imports use absolute paths: `from tools.esc_validator...`
3. Add `sys.path.insert(0, ...)` if needed

### Issue: "Test passes locally but fails in CI"

**Problem:** Test depends on local environment

**Solution:**
1. Check for hardcoded paths
2. Use fixtures and `tmp_path`
3. Verify CI has required dependencies (Tesseract, etc.)

---

## Best Practices

1. **One test file per module** - `test_text_detector.py` tests `text_detector.py`
2. **Descriptive test names** - `test_is_contour_label_with_valid_elevation_returns_true`
3. **Single assertion focus** - Test one thing per test function
4. **Use fixtures** - Don't hardcode paths or create test data inline
5. **Add markers** - Categorize tests with `@pytest.mark.*`
6. **Document edge cases** - Explain why test exists in docstring

---

## Next Steps

1. **Start with unit tests** - Easiest to migrate
2. **Migrate one file at a time** - Don't try to do everything at once
3. **Run tests frequently** - Verify migration as you go
4. **Update CI/CD** - Ensure new tests run automatically
5. **Delete old tests** - Once migration is verified

---

## Resources

- [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md) - Full architecture
- [QUICK_START.md](QUICK_START.md) - Getting started guide
- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Migration Guide](https://docs.pytest.org/en/stable/how-to/existingtestsuite.html)

---

**Last Updated:** 2025-11-02
**Status:** Guide Complete - Ready for Migration
