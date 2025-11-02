# Testing Quick Start Guide

Get up and running with the test suite in 5 minutes.

---

## Installation

### 1. Install Test Dependencies

```bash
# Core testing tools
pip install pytest pytest-cov pytest-benchmark pytest-xdist

# Linting and formatting (optional)
pip install flake8 black isort mypy
```

### 2. Verify Installation

```bash
pytest --version
# Should show: pytest 7.x.x
```

---

## Running Tests

### Quick Commands

```bash
# Run all tests
pytest

# Run only fast tests (unit + integration, skip slow)
pytest -m "not slow"

# Run only unit tests
pytest tests/unit/ -v

# Run with coverage
pytest --cov=tools --cov-report=html

# Run in parallel (faster)
pytest -n auto

# Run last failed tests
pytest --lf

# Stop on first failure
pytest -x
```

### By Test Type

```bash
# Unit tests (fast, isolated)
pytest -m unit

# Integration tests (cross-module)
pytest -m integration

# E2E tests (full workflows)
pytest -m e2e

# Performance benchmarks
pytest -m performance --benchmark-only
```

### By Tool

```bash
# ESC Validator tests only
pytest -m esc

# Future: Code Lookup tests
pytest -m code_lookup
```

---

## Writing Your First Test

### 1. Choose Test Category

- **Unit Test?** → `tests/unit/test_<module>.py`
- **Integration Test?** → `tests/integration/test_<feature>.py`
- **E2E Test?** → `tests/e2e/test_<workflow>.py`

### 2. Create Test File

```python
# tests/unit/test_my_module.py
import pytest

def test_my_function():
    """Test description goes here."""
    result = my_function(input_data)
    assert result == expected_output
```

### 3. Run Your Test

```bash
pytest tests/unit/test_my_module.py -v
```

---

## Using Fixtures

### Available Fixtures

```python
def test_with_sample_pdf(sample_esc_pdf):
    """Use sample PDF fixture."""
    # sample_esc_pdf is a Path object
    assert sample_esc_pdf.exists()

def test_with_temp_dir(temp_output_dir):
    """Use temporary directory for outputs."""
    output_file = temp_output_dir / "result.json"
    output_file.write_text("{}")
    assert output_file.exists()

def test_with_blank_image(blank_image):
    """Use generated blank image."""
    # blank_image is numpy array
    assert blank_image.shape == (500, 500, 3)
```

See: `tests/conftest.py` for all available fixtures

### Creating Your Own Fixture

```python
# tests/conftest.py or tool-specific conftest.py
@pytest.fixture
def my_custom_fixture():
    """Description of fixture."""
    # Setup
    data = setup_test_data()

    yield data

    # Teardown (optional)
    cleanup_test_data(data)
```

---

## Test Markers

### Using Markers

```python
@pytest.mark.unit
def test_pure_function():
    """Fast unit test."""
    pass

@pytest.mark.integration
def test_module_interaction():
    """Integration test."""
    pass

@pytest.mark.slow
def test_large_file_processing():
    """Slow test (>10 seconds)."""
    pass

@pytest.mark.skip(reason="Fixture not available")
def test_needs_real_data():
    """Skipped test."""
    pass
```

### Available Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.performance` - Performance benchmarks
- `@pytest.mark.esc` - ESC Validator specific
- `@pytest.mark.skip()` - Skip test
- `@pytest.mark.skipif()` - Conditional skip
- `@pytest.mark.parametrize()` - Multiple scenarios

---

## Common Patterns

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("250.5", True),
    ("abc", False),
    ("100", True),
])
def test_with_multiple_inputs(input, expected):
    assert is_contour_label(input) == expected
```

### Testing Exceptions

```python
def test_raises_error_on_invalid_input():
    with pytest.raises(ValueError):
        my_function(invalid_input)
```

### Approximate Comparisons

```python
def test_confidence_score():
    score = calculate_confidence()
    assert score == pytest.approx(0.85, abs=0.01)
```

### Custom Assertions

```python
def test_validation_result():
    result = validate_esc_sheet(pdf)

    # Custom assertion from tests/utils/assertions.py
    assert_validation_passed(result, 'north_bar')
    assert_element_confidence_high(result, 'sce', min_confidence=0.7)
```

---

## Coverage Reports

### Generate HTML Report

```bash
pytest --cov=tools --cov-report=html
# Open: htmlcov/index.html
```

### View Terminal Report

```bash
pytest --cov=tools --cov-report=term-missing
```

### Coverage Targets

- **Unit Tests:** 90%+
- **Integration Tests:** 80%+
- **Overall:** 85%+

---

## Debugging Tests

### Verbose Output

```bash
pytest -v -s  # -v = verbose, -s = show print statements
```

### Debug Specific Test

```bash
pytest tests/unit/test_my_module.py::test_my_function -v -s
```

### Drop into Debugger on Failure

```bash
pytest --pdb  # Drop into pdb on failure
```

### Print Test Info

```python
def test_debug_info(capsys):
    """Capture and check printed output."""
    print("Debug info here")
    captured = capsys.readouterr()
    assert "Debug info" in captured.out
```

---

## CI/CD Integration

### Local Pre-commit Check

Run this before committing:

```bash
# Fast tests + lint
pytest tests/unit/ tests/integration/ -m "not slow" && flake8 tools/ tests/ && black --check tools/ tests/
```

### GitHub Actions

Tests automatically run on:
- Every push to `master`/`main`/`develop`
- Every pull request
- Nightly (performance tests)

Check status:
- Go to repository → Actions tab
- View workflow runs and results

---

## Troubleshooting

### "Fixture not found"

**Problem:** `pytest.fixture 'sample_esc_pdf' not found`

**Solution:** Check if fixture file exists in `tests/fixtures/pdfs/`. See `tests/fixtures/README.md` for instructions.

### "Import errors"

**Problem:** `ModuleNotFoundError: No module named 'esc_validator'`

**Solution:**
```bash
# Ensure project is in path
cd "C:\Users\Cam Dowdle\source\repos\personal\Christian productivity"
pytest
```

### "Tests are slow"

**Problem:** Tests take too long to run

**Solution:**
```bash
# Run in parallel
pytest -n auto

# Skip slow tests
pytest -m "not slow"

# Run only unit tests
pytest tests/unit/
```

### "Coverage is low"

**Problem:** Coverage below target

**Solution:**
1. Identify uncovered code: `pytest --cov=tools --cov-report=term-missing`
2. Write tests for missing coverage
3. Focus on critical code paths first

---

## Next Steps

1. **Read Full Architecture:** [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md)
2. **Add Test Fixtures:** See [fixtures/README.md](../tests/fixtures/README.md)
3. **Migrate Existing Tests:** Move ad-hoc tests to pytest structure
4. **Enable CI/CD:** Push to GitHub to trigger workflows

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures Guide](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers Guide](https://docs.pytest.org/en/stable/how-to/mark.html)
- [Test Architecture](TEST_ARCHITECTURE.md)

---

**Last Updated:** 2025-11-02
**Questions?** See [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md) or ask in GitHub issues
