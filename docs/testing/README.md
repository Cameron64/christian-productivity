# Testing Documentation

Comprehensive testing framework for Christian's Productivity Tools.

---

## Overview

This directory contains the testing architecture, guides, and best practices for all automation tools in this repository.

**Current Status:** ✅ Architecture Complete - Ready for Implementation

**Version:** 1.0.0
**Last Updated:** 2025-11-02

---

## Quick Links

### 🚀 Start Here
- **[QUICK_START.md](QUICK_START.md)** - Get up and running in 5 minutes

### 📖 Documentation
- **[TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md)** - Complete architecture and design
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migrate existing tests to pytest

### 📁 Test Suite
- **[../../tests/](../../tests/)** - Test suite root directory
- **[../../tests/fixtures/README.md](../../tests/fixtures/README.md)** - Test data and fixtures

---

## What's Included

### Test Architecture
- ✅ **Pytest-based framework** - Industry standard testing
- ✅ **Test categorization** - Unit, integration, E2E, performance
- ✅ **Fixture system** - Reusable test data and assets
- ✅ **CI/CD integration** - GitHub Actions workflows
- ✅ **Coverage reporting** - Track test coverage over time
- ✅ **Performance benchmarks** - Monitor performance regressions

### Directory Structure

```
tests/
├── conftest.py              # Shared fixtures
├── fixtures/                # Test data (PDFs, images)
├── unit/                    # Fast, isolated tests
├── integration/             # Cross-module tests
├── e2e/                     # End-to-end workflows
├── performance/             # Performance benchmarks
└── utils/                   # Test utilities

.github/workflows/
├── test.yml                 # Main CI test workflow
├── test-pr.yml              # Fast PR tests
└── performance.yml          # Nightly performance tests
```

### Configuration Files
- `pytest.ini` - Pytest configuration
- `.coveragerc` - Coverage settings
- `requirements-test.txt` - Test dependencies

---

## Test Categories

| Category | Purpose | Speed | Location |
|----------|---------|-------|----------|
| **Unit** | Test individual functions | <10s | `tests/unit/` |
| **Integration** | Test module interactions | <60s | `tests/integration/` |
| **E2E** | Test complete workflows | Minutes | `tests/e2e/` |
| **Performance** | Benchmark speed | Varies | `tests/performance/` |

---

## Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements-test.txt
```

### 2. Run Tests

```bash
# All tests
pytest

# Fast tests only
pytest -m "not slow"

# With coverage
pytest --cov=tools --cov-report=html
```

### 3. Write Your First Test

```python
# tests/unit/test_example.py
import pytest

@pytest.mark.unit
def test_example():
    """Test description."""
    result = my_function()
    assert result == expected
```

See [QUICK_START.md](QUICK_START.md) for full guide.

---

## Key Features

### Automatic Test Discovery
Pytest automatically finds and runs tests:
- Files matching `test_*.py`
- Functions matching `test_*`
- Classes matching `Test*`

### Fixtures for Test Data
Reusable test data via fixtures:
```python
def test_with_fixture(sample_esc_pdf):
    """Fixture injected automatically."""
    assert sample_esc_pdf.exists()
```

### Test Markers
Categorize and filter tests:
```python
@pytest.mark.unit
@pytest.mark.esc
def test_esc_validation():
    pass
```

Run specific categories:
```bash
pytest -m unit              # Only unit tests
pytest -m "esc and not slow"  # ESC tests, skip slow
```

### Parametrized Tests
Test multiple scenarios efficiently:
```python
@pytest.mark.parametrize("input,expected", [
    ("250.5", True),
    ("abc", False),
])
def test_multiple_inputs(input, expected):
    assert is_valid(input) == expected
```

### Coverage Tracking
Monitor test coverage:
```bash
pytest --cov=tools --cov-report=html
# Open: htmlcov/index.html
```

**Targets:**
- Unit: 90%+
- Integration: 80%+
- Overall: 85%+

---

## CI/CD Integration

### GitHub Actions Workflows

**Main Workflow** (`.github/workflows/test.yml`):
- Runs on push to `master`/`main`/`develop`
- Runs on all pull requests
- Tests on Python 3.9, 3.10, 3.11
- Generates coverage reports

**PR Workflow** (`.github/workflows/test-pr.yml`):
- Fast tests only (unit + integration)
- Runs on every PR commit
- Must pass before merge

**Performance Workflow** (`.github/workflows/performance.yml`):
- Runs nightly at 2 AM UTC
- Benchmarks performance over time
- Alerts on >20% regression

### Viewing Results
1. Go to repository → **Actions** tab
2. View workflow runs
3. Check test results and coverage

---

## Test Examples

### Example: Unit Test

```python
# tests/unit/test_text_detection.py
@pytest.mark.unit
@pytest.mark.parametrize("text,expected", [
    ("250.5", True),
    ("abc", False),
])
def test_is_contour_label(text, expected):
    """Should correctly identify contour labels."""
    assert is_contour_label(text) == expected
```

### Example: Integration Test

```python
# tests/integration/test_spatial_filtering.py
@pytest.mark.integration
@pytest.mark.esc
def test_spatial_filtering_reduces_false_positives(sample_esc_pdf):
    """Phase 2.1: Should filter 857 lines to ~9 contours."""
    image = extract_page_as_image(str(sample_esc_pdf), page_num=26)
    result = verify_contour_conventions_smart(image, max_distance=150)

    assert len(result['contours']) < 20
    assert result['filter_effectiveness'] > 0.8
```

### Example: E2E Test

```python
# tests/e2e/test_cli_validation.py
@pytest.mark.e2e
def test_validate_esc_cli(tmp_path, sample_esc_pdf):
    """Should run full CLI validation workflow."""
    result = subprocess.run([
        "python", "validate_esc.py",
        str(sample_esc_pdf), "--output", str(tmp_path / "report.md")
    ], capture_output=True)

    assert result.returncode == 0
```

---

## Migrating Existing Tests

We've migrated from ad-hoc test scripts to pytest:

**Before:**
- `test_phase_1_3_1.py` (CLI script)
- `test_phase_2.py` (CLI script)
- `test_phase_2_1.py` (CLI script)

**After:**
- `tests/unit/test_text_detection.py`
- `tests/integration/test_spatial_filtering.py`
- `tests/e2e/test_cli_validation.py`

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for step-by-step migration.

---

## Success Metrics

### Coverage Targets
- **Unit Tests:** 90%+ coverage
- **Integration Tests:** 80%+ coverage
- **Overall:** 85%+ coverage

### Performance Targets
- **ESC Validator:** <30 seconds per sheet
- **Test Suite Runtime:** <5 minutes (unit + integration)
- **PR Feedback:** <10 minutes

### Quality Targets
- **Zero false negatives** on critical elements (SCE, CONC WASH)
- **Pass rate:** >95% on main branch
- **Flaky tests:** <1% failure rate

---

## Best Practices

1. **Write tests first** - TDD when possible
2. **One assertion per test** - Keep tests focused
3. **Descriptive names** - Test name explains what's tested
4. **Use fixtures** - Don't repeat test data setup
5. **Fast tests** - Keep unit tests under 1 second
6. **Independent tests** - Tests don't depend on each other
7. **Clean up** - Tests leave no artifacts
8. **Document edge cases** - Explain why test exists

---

## Future Enhancements

### Planned (Short-term)
- [ ] Migrate all existing ad-hoc tests
- [ ] Add more unit tests (target: 90% coverage)
- [ ] Create test data fixtures
- [ ] Performance benchmark baselines

### Planned (Long-term)
- [ ] UI testing framework (Playwright)
- [ ] Visual regression testing
- [ ] Load testing for batch processing
- [ ] Mutation testing
- [ ] Property-based testing (Hypothesis)

---

## Troubleshooting

### Common Issues

**"Tests not found"**
- Ensure test files match `test_*.py`
- Run from project root directory

**"Fixture not found"**
- Check `tests/conftest.py` for fixture definition
- Ensure fixture file exists in `tests/fixtures/`

**"Import errors"**
- Verify project root in path
- Check absolute imports: `from tools.esc_validator...`

**"Tests slow"**
- Run in parallel: `pytest -n auto`
- Skip slow tests: `pytest -m "not slow"`

See [QUICK_START.md](QUICK_START.md) for more troubleshooting.

---

## Resources

### Documentation
- [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md) - Architecture deep dive
- [QUICK_START.md](QUICK_START.md) - Getting started guide
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Migration instructions

### External Resources
- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [GitHub Actions for Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)

---

## Contributing

When adding new tools or features:

1. **Write tests first** - TDD approach
2. **Follow naming conventions** - See TEST_ARCHITECTURE.md
3. **Use appropriate category** - Unit/integration/e2e
4. **Add markers** - Categorize tests properly
5. **Update fixtures** - Document new test data
6. **Run full suite** - Ensure no regressions

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-02 | Initial test architecture and framework |

---

## Support

**Questions?**
- See documentation above
- Check [issues](https://github.com/yourusername/repo/issues)
- Review example tests in `tests/`

**Found a bug?**
- Open an issue with test that reproduces bug
- Include pytest output and environment details

---

**Last Updated:** 2025-11-02
**Status:** ✅ Architecture Complete - Ready for Implementation
**Next Milestone:** Migrate existing tests and achieve 85% coverage
