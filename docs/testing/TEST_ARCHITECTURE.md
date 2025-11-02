# Test Architecture - Christian's Productivity Tools

**Version:** 1.0.0
**Created:** 2025-11-02
**Purpose:** Scalable test architecture for multiple automation tools and future UI

---

## Overview

This document defines the testing strategy for all productivity automation tools in this repository. The architecture is designed to support:

- **Multiple tools** (ESC Validator, Code Lookup, Drawing Analysis, etc.)
- **CI/CD integration** (GitHub Actions)
- **Future UI testing** (web or desktop interfaces)
- **Consistent patterns** across all projects
- **Fast feedback loops** during development

---

## Testing Philosophy

### Core Principles

1. **Test Behavior, Not Implementation** - Tests should validate outcomes, not internal details
2. **Fast Feedback** - Unit tests run in <10s, integration tests in <60s
3. **Isolation** - Tests don't depend on external services or network
4. **Repeatability** - Same inputs always produce same outputs
5. **Clear Failures** - Test names and error messages make root cause obvious
6. **Maintainability** - Tests are as clean and documented as production code

### Test Pyramid

```
        /\
       /  \        E2E Tests (5%)
      /----\       - Full workflow validation
     /      \      - UI + API integration
    /--------\
   / Integration \ Integration Tests (20%)
  /--------------\ - Component interaction
 /    Unit Tests  \ - Module boundaries
/------------------\

Unit Tests (75%)
- Pure functions
- Single responsibility
- Fast execution
```

---

## Directory Structure

```
christian-productivity/
├── tests/                              # Root test directory
│   ├── __init__.py
│   ├── conftest.py                     # Shared pytest fixtures
│   ├── fixtures/                       # Test data and assets
│   │   ├── README.md                   # Fixture documentation
│   │   ├── pdfs/                       # Sample PDF files
│   │   │   ├── esc_sheet_valid.pdf
│   │   │   ├── esc_sheet_missing_items.pdf
│   │   │   └── drawing_set_sample.pdf
│   │   ├── images/                     # Sample images
│   │   │   ├── north_arrow_template.png
│   │   │   └── plan_sheet_300dpi.png
│   │   └── expected/                   # Expected test outputs
│   │       ├── esc_validation_results.json
│   │       └── text_extraction_output.txt
│   │
│   ├── unit/                           # Unit tests (fast, isolated)
│   │   ├── __init__.py
│   │   ├── test_text_detection.py
│   │   ├── test_symbol_detection.py
│   │   ├── test_line_detection.py
│   │   └── test_validators.py
│   │
│   ├── integration/                    # Integration tests (cross-module)
│   │   ├── __init__.py
│   │   ├── test_esc_validation_pipeline.py
│   │   ├── test_pdf_processing.py
│   │   └── test_report_generation.py
│   │
│   ├── e2e/                            # End-to-end tests (full workflows)
│   │   ├── __init__.py
│   │   ├── test_cli_commands.py
│   │   ├── test_batch_processing.py
│   │   └── test_ui_workflows.py        # Future: UI tests
│   │
│   ├── performance/                    # Performance benchmarks
│   │   ├── __init__.py
│   │   ├── test_processing_speed.py
│   │   └── benchmarks.json             # Historical performance data
│   │
│   └── utils/                          # Test utilities
│       ├── __init__.py
│       ├── assertions.py               # Custom assertions
│       ├── builders.py                 # Test data builders
│       └── mocks.py                    # Mock objects
│
├── tools/esc-validator/                # Tool-specific structure
│   ├── esc_validator/                  # Source code
│   │   └── ...
│   └── tests/                          # Tool-local tests (optional)
│       ├── conftest.py                 # Tool-specific fixtures
│       └── integration/                # Tool integration tests
│
├── .github/
│   └── workflows/
│       ├── test.yml                    # Main test CI workflow
│       ├── test-pr.yml                 # PR-specific tests
│       └── performance.yml             # Performance regression tests
│
├── pytest.ini                          # Pytest configuration
├── .coveragerc                         # Coverage configuration
└── tox.ini                             # Multi-environment testing
```

---

## Test Categories

### 1. Unit Tests (`tests/unit/`)

**Purpose:** Test individual functions and classes in isolation

**Characteristics:**
- No file I/O (use in-memory data or mocks)
- No external dependencies
- Run in <10 seconds total
- 100% deterministic

**Example:**
```python
# tests/unit/test_text_detection.py
def test_is_contour_label_detects_elevation():
    """Should identify elevation numbers as contour labels."""
    assert is_contour_label("250.5")
    assert is_contour_label("100")
    assert not is_contour_label("abc")
    assert not is_contour_label("25")  # Too low
```

**Naming Convention:** `test_<module>_<function>_<scenario>`

---

### 2. Integration Tests (`tests/integration/`)

**Purpose:** Test interactions between modules/components

**Characteristics:**
- Uses real file I/O with fixtures
- Tests multiple modules together
- Run in <60 seconds total
- Focuses on module boundaries

**Example:**
```python
# tests/integration/test_esc_validation_pipeline.py
def test_full_esc_validation_with_real_pdf(sample_esc_pdf):
    """Should validate complete ESC sheet through full pipeline."""
    results = validate_esc_sheet(sample_esc_pdf, page=16)

    assert results['north_bar']['detected'] is True
    assert results['sce']['detected'] is True
    assert len(results) == 16  # All checklist items
```

---

### 3. End-to-End Tests (`tests/e2e/`)

**Purpose:** Test complete user workflows

**Characteristics:**
- Tests CLI commands or UI interactions
- Uses realistic scenarios
- May take several minutes
- Validates entire tool from input to output

**Example:**
```python
# tests/e2e/test_cli_commands.py
def test_validate_esc_cli_generates_report(tmp_path, sample_pdf):
    """Should validate ESC sheet and generate markdown report."""
    output = tmp_path / "report.md"

    result = subprocess.run([
        "python", "validate_esc.py",
        str(sample_pdf),
        "--page", "16",
        "--output", str(output)
    ], capture_output=True, text=True)

    assert result.returncode == 0
    assert output.exists()
    assert "PASS" in output.read_text() or "FAIL" in output.read_text()
```

---

### 4. Performance Tests (`tests/performance/`)

**Purpose:** Ensure performance doesn't regress

**Characteristics:**
- Measures execution time
- Tracks historical benchmarks
- Runs on schedule (nightly CI)
- Fails if performance degrades >20%

**Example:**
```python
# tests/performance/test_processing_speed.py
@pytest.mark.performance
def test_esc_validation_completes_under_30_seconds(benchmark, sample_pdf):
    """Phase 2.1 target: <30s processing time."""
    result = benchmark(validate_esc_sheet, sample_pdf, page=16)

    assert benchmark.stats['mean'] < 30.0  # seconds
```

---

## Fixtures and Test Data

### Fixture Organization

**Global Fixtures** (`tests/conftest.py`):
- Shared across all tools
- Examples: PDF loaders, image processors, temp directories

**Tool-Specific Fixtures** (`tools/<tool>/tests/conftest.py`):
- Only used by specific tool
- Examples: ESC-specific templates, checklist configurations

### Test Data Management

**Location:** `tests/fixtures/`

**Guidelines:**
1. **Real Data** - Use actual project files (anonymized if needed)
2. **Minimal Size** - Keep fixtures <5 MB each
3. **Versioned** - Check fixtures into git (use Git LFS for large files)
4. **Documented** - Include README explaining each fixture's purpose

**Example Fixture Structure:**
```python
# tests/conftest.py
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def sample_esc_pdf():
    """Sample ESC sheet with all required elements present."""
    return FIXTURES_DIR / "pdfs" / "esc_sheet_valid.pdf"

@pytest.fixture
def esc_missing_sce():
    """ESC sheet missing SCE marker (should fail validation)."""
    return FIXTURES_DIR / "pdfs" / "esc_sheet_missing_sce.pdf"

@pytest.fixture
def north_arrow_template():
    """Template image for north arrow detection."""
    return FIXTURES_DIR / "images" / "north_arrow_template.png"
```

---

## Test Execution

### Running Tests Locally

```bash
# Run all tests
pytest

# Run specific category
pytest tests/unit/                  # Fast unit tests only
pytest tests/integration/           # Integration tests
pytest tests/e2e/                   # End-to-end tests

# Run tests for specific tool
pytest tests/ -k "esc"              # All ESC validator tests

# Run with coverage
pytest --cov=tools --cov-report=html

# Run performance benchmarks
pytest tests/performance/ --benchmark-only

# Verbose output
pytest -v -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_pure_function():
    pass

@pytest.mark.integration
def test_module_interaction():
    pass

@pytest.mark.e2e
def test_full_workflow():
    pass

@pytest.mark.slow
def test_large_pdf_processing():
    pass

@pytest.mark.performance
def test_speed_benchmark():
    pass

@pytest.mark.ui
def test_web_interface():
    pass
```

**Running by marker:**
```bash
pytest -m unit                  # Only unit tests
pytest -m "not slow"            # Skip slow tests
pytest -m "integration or e2e"  # Multiple markers
```

---

## CI/CD Integration

### GitHub Actions Workflow

**Main Test Workflow** (`.github/workflows/test.yml`):

```yaml
name: Tests

on:
  push:
    branches: [master, main, develop]
  pull_request:
    branches: [master, main]

jobs:
  test:
    runs-on: windows-latest  # Christian's environment

    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install Tesseract OCR
        run: choco install tesseract

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-benchmark

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=tools --cov-report=xml

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Run E2E tests
        run: pytest tests/e2e/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

**PR-Specific Workflow** (`.github/workflows/test-pr.yml`):
- Fast tests only (unit + integration)
- Runs on every PR commit
- Must pass before merge

**Performance Workflow** (`.github/workflows/performance.yml`):
- Runs nightly
- Tracks performance over time
- Alerts if >20% regression

---

## Configuration Files

### pytest.ini

```ini
[pytest]
# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Output
addopts =
    --strict-markers
    --tb=short
    --disable-warnings
    -ra

# Markers
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (cross-module)
    e2e: End-to-end tests (full workflows)
    slow: Slow tests (>10 seconds)
    performance: Performance benchmarks
    ui: UI tests (requires UI framework)

# Coverage
[coverage:run]
source = tools
omit =
    */tests/*
    */test_*.py
    */__pycache__/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
```

### .coveragerc

```ini
[run]
branch = True
source = tools/

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

[html]
directory = htmlcov
```

---

## Testing Best Practices

### Naming Conventions

**Test Functions:**
```python
# Format: test_<function>_<scenario>_<expected_outcome>
def test_is_contour_label_with_valid_elevation_returns_true():
    pass

def test_validate_esc_sheet_when_sce_missing_fails():
    pass

def test_extract_text_with_poor_quality_image_returns_low_confidence():
    pass
```

**Test Classes:**
```python
# Group related tests by feature
class TestContourLabelDetection:
    def test_detects_elevation_numbers(self):
        pass

    def test_detects_contour_keywords(self):
        pass

    def test_rejects_invalid_formats(self):
        pass
```

### Assertion Patterns

**Use descriptive messages:**
```python
# Bad
assert result == 5

# Good
assert result == 5, f"Expected 5 streets, got {result}"
```

**Use custom assertions:**
```python
# tests/utils/assertions.py
def assert_validation_passed(results, element):
    """Assert that validation passed for specific element."""
    assert element in results, f"Element '{element}' not in results"
    assert results[element]['detected'], f"Element '{element}' was not detected"
    assert results[element]['confidence'] > 0.5, \
        f"Confidence too low for '{element}': {results[element]['confidence']}"
```

### Mocking Guidelines

**Mock external dependencies, not internal logic:**

```python
# Good - mock file I/O
@patch('esc_validator.extractor.extract_page_as_image')
def test_validation_handles_pdf_error(mock_extract):
    mock_extract.return_value = None  # Simulate error
    result = validate_esc_sheet("fake.pdf")
    assert result['status'] == 'error'

# Bad - mocking internal logic defeats the test
@patch('esc_validator.text_detector.is_contour_label')
def test_contour_detection(mock_is_contour):
    mock_is_contour.return_value = True
    # This doesn't test anything meaningful!
```

### Parametrized Tests

**Use `pytest.mark.parametrize` for multiple scenarios:**

```python
@pytest.mark.parametrize("text,expected", [
    ("250.5", True),
    ("100", True),
    ("50", True),
    ("25", False),  # Too low
    ("600", False),  # Too high
    ("abc", False),  # Not a number
    ("contour", True),  # Keyword
    ("existing", True),  # Keyword
])
def test_is_contour_label(text, expected):
    assert is_contour_label(text) == expected
```

---

## Migrating Existing Tests

### Current State

**Existing test files** (to be migrated):
- `test_phase_1_3_1.py` - Visual detection tests
- `test_phase_2.py` - Line detection tests
- `test_phase_2_1.py` - Spatial filtering tests

**Problems:**
- Ad-hoc structure (not discoverable by pytest)
- Manual CLI execution required
- No fixtures (hardcoded paths)
- Not integrated with CI/CD
- Mix of unit/integration/e2e concerns

### Migration Strategy

**Phase 1: Extract Reusable Components**
1. Identify reusable test logic
2. Extract to `tests/utils/` and `tests/conftest.py`
3. Create fixtures for sample data

**Phase 2: Reorganize by Test Type**
1. Split into unit/integration/e2e
2. Convert CLI scripts to pytest functions
3. Add pytest markers

**Phase 3: Enable CI/CD**
1. Configure GitHub Actions
2. Add coverage reporting
3. Set up performance tracking

**Example Migration:**

```python
# OLD: test_phase_2_1.py (CLI script)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path")
    args = parser.parse_args()

    # Hardcoded test logic
    image = extract_page_as_image(args.pdf_path, 26)
    result = verify_contour_conventions_smart(image, ...)
    print(f"Detected {len(result['contours'])} contours")

# NEW: tests/integration/test_spatial_filtering.py
def test_spatial_filtering_reduces_false_positives(sample_esc_page_26):
    """Phase 2.1: Should filter 857 lines to ~9 contours."""
    image = sample_esc_page_26  # Fixture
    result = verify_contour_conventions_smart(image, max_distance=150)

    assert len(result['contours']) < 20, \
        f"Expected <20 contours after filtering, got {len(result['contours'])}"
    assert result['filter_effectiveness'] > 0.8, \
        f"Expected >80% filter effectiveness, got {result['filter_effectiveness']:.1%}"
```

---

## Future: UI Testing

### When UI is Built

**Framework Options:**
- **Playwright** (recommended) - Web UI testing
- **Selenium** - Web UI (older alternative)
- **PyAutoGUI** - Desktop UI testing

**Test Location:** `tests/e2e/test_ui_workflows.py`

**Example UI Test:**
```python
@pytest.mark.ui
def test_upload_esc_sheet_and_validate(page, sample_esc_pdf):
    """Should upload ESC sheet, run validation, and display results."""
    page.goto("http://localhost:8000")

    # Upload file
    page.locator("#file-upload").set_input_files(sample_esc_pdf)
    page.locator("#validate-button").click()

    # Wait for results
    page.wait_for_selector("#validation-results")

    # Assert results displayed
    results = page.locator(".checklist-item")
    assert results.count() == 16  # All checklist items
    assert page.locator(".item-pass").count() >= 10  # Most items pass
```

---

## Success Metrics

### Coverage Targets

| Test Type | Coverage Target |
|-----------|----------------|
| Unit Tests | 90%+ |
| Integration Tests | 80%+ |
| E2E Tests | 70%+ |
| Overall | 85%+ |

### Performance Targets

| Tool | Target Time |
|------|-------------|
| ESC Validator | <30 seconds per sheet |
| Drawing Analysis | <60 seconds per 100-page set |
| Code Lookup | <2 seconds per query |

### CI/CD Targets

- **Test Suite Runtime:** <5 minutes (unit + integration)
- **PR Feedback:** <10 minutes (fast tests only)
- **Nightly Full Suite:** <30 minutes (all tests + performance)

---

## Next Steps

### Immediate (This Session)
1. ✅ Create test architecture documentation
2. Create pytest configuration files
3. Set up directory structure
4. Create conftest.py with initial fixtures
5. Migrate one existing test as example
6. Create GitHub Actions workflow

### Short-term (Next Week)
1. Migrate all existing tests to new structure
2. Add coverage reporting
3. Create test data fixtures
4. Document each fixture's purpose

### Medium-term (Next Month)
1. Achieve 85% test coverage
2. Implement performance benchmarking
3. Add UI tests when UI is built
4. Create developer testing guide

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [GitHub Actions for Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Test-Driven Development Guide](https://testdriven.io/)

---

**Last Updated:** 2025-11-02
**Author:** Claude (via Claude Code)
**Status:** Architecture Defined - Ready for Implementation
