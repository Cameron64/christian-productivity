# Test Fixtures

This directory contains test data and assets used by the test suite.

## Directory Structure

```
fixtures/
├── README.md              # This file
├── pdfs/                  # Sample PDF files
├── images/                # Sample images and templates
└── expected/              # Expected test outputs (for regression tests)
```

---

## PDF Fixtures

### `pdfs/esc_sheet_valid.pdf`
- **Purpose:** Valid ESC sheet with all required elements
- **Source:** Real project (anonymized)
- **Use Case:** Positive test - should pass all validation
- **Contains:**
  - North arrow
  - Scale bar
  - Legend
  - SCE marker
  - CONC WASH marker
  - Street labels (2+ streets)
  - Contour lines (existing and proposed)

### `pdfs/esc_sheet_missing_sce.pdf`
- **Purpose:** ESC sheet missing SCE marker
- **Source:** Modified from valid sheet
- **Use Case:** Negative test - should fail validation
- **Missing:** SCE (critical element)

### `pdfs/esc_sheet_missing_conc_wash.pdf`
- **Purpose:** ESC sheet missing CONC WASH marker
- **Source:** Modified from valid sheet
- **Use Case:** Negative test - should fail validation
- **Missing:** CONC WASH (critical element)

### `pdfs/drawing_set_sample.pdf`
- **Purpose:** Multi-page drawing set for batch testing
- **Source:** Real project (anonymized)
- **Use Case:** Performance and batch processing tests
- **Pages:** 50-100 pages
- **Size:** <10 MB

---

## Image Fixtures

### `images/north_arrow_template.png`
- **Purpose:** Template for north arrow detection
- **Source:** Extracted from ESC sheet
- **Resolution:** 300 DPI
- **Size:** ~100x100 pixels
- **Format:** PNG with transparency

### `images/plan_sheet_300dpi.png`
- **Purpose:** High-resolution plan sheet for OCR testing
- **Source:** Page extracted from ESC sheet
- **Resolution:** 300 DPI
- **Use Case:** Test OCR accuracy and preprocessing

---

## Expected Outputs

### `expected/esc_validation_results.json`
- **Purpose:** Expected validation output for regression tests
- **Source:** Generated from `esc_sheet_valid.pdf`
- **Format:** JSON with all checklist results
- **Use Case:** Ensure validation output doesn't change unexpectedly

**Example structure:**
```json
{
  "north_bar": {
    "detected": true,
    "confidence": 0.95,
    "count": 1,
    "notes": "North arrow detected"
  },
  "sce": {
    "detected": true,
    "confidence": 0.85,
    "count": 3,
    "notes": "3 SCE instances found"
  },
  ...
}
```

---

## Adding New Fixtures

### Guidelines

1. **Real Data Preferred**
   - Use actual project files when possible
   - Anonymize if needed (remove client names, addresses)

2. **Keep Fixtures Small**
   - PDFs: <5 MB each
   - Images: <2 MB each
   - Use Git LFS for larger files (>5 MB)

3. **Document Each Fixture**
   - Update this README with purpose and use case
   - Add comments in test code explaining why fixture is used

4. **Version Control**
   - Check fixtures into Git
   - Use descriptive file names
   - Don't commit temporary test outputs

### Adding a New PDF Fixture

```bash
# 1. Copy PDF to fixtures/pdfs/
cp ~/projects/my_esc_sheet.pdf tests/fixtures/pdfs/esc_sheet_custom.pdf

# 2. Document in this README

# 3. Create pytest fixture in conftest.py
@pytest.fixture(scope="session")
def esc_sheet_custom() -> Path:
    """Custom ESC sheet for specific test case."""
    return PDFS_DIR / "esc_sheet_custom.pdf"

# 4. Use in tests
def test_custom_scenario(esc_sheet_custom):
    results = validate_esc_sheet(esc_sheet_custom)
    assert results['north_bar']['detected']
```

---

## Fixture Availability

Not all fixtures may be available in the repository due to:
- File size constraints
- Confidentiality (real project data)
- Licensing (templates from external sources)

**Missing fixtures:**
- Tests will be automatically skipped via `pytest.skip()`
- Warning message will indicate which fixture is missing
- See `tests/conftest.py` for fixture definitions

**To add missing fixtures:**
1. Obtain the required file (see fixture documentation above)
2. Place in appropriate directory (`pdfs/` or `images/`)
3. Re-run tests - they will no longer be skipped

---

## Using Fixtures in Tests

### Basic Usage

```python
def test_esc_validation(sample_esc_pdf):
    """Test with sample PDF fixture."""
    results = validate_esc_sheet(sample_esc_pdf)
    assert results is not None
```

### Multiple Fixtures

```python
def test_template_matching(plan_sheet_300dpi, north_arrow_template):
    """Test with multiple fixtures."""
    detected = detect_north_arrow(plan_sheet_300dpi, north_arrow_template)
    assert detected
```

### Parametrized Fixtures

```python
@pytest.mark.parametrize("pdf_fixture", [
    "sample_esc_pdf",
    "esc_missing_sce",
    "esc_missing_conc_wash"
])
def test_multiple_pdfs(pdf_fixture, request):
    """Test with multiple PDF fixtures."""
    pdf = request.getfixturevalue(pdf_fixture)
    results = validate_esc_sheet(pdf)
    # Assertions...
```

---

## Fixture Maintenance

### Regular Tasks

- **Review fixture size:** Ensure fixtures stay <5 MB
- **Update expected outputs:** When validation logic changes
- **Refresh real data:** Periodically update with recent project files
- **Clean obsolete fixtures:** Remove unused fixtures

### Before Committing

```bash
# Check fixture sizes
find tests/fixtures -type f -size +5M

# Verify fixtures are documented
git diff tests/fixtures/README.md
```

---

## Related Files

- **Fixture Definitions:** `tests/conftest.py`
- **Test Architecture:** `docs/testing/TEST_ARCHITECTURE.md`
- **CI/CD Config:** `.github/workflows/test.yml`

---

**Last Updated:** 2025-11-02
**Total Fixtures:** 0 (to be added)
**Status:** Structure created, awaiting fixture files
