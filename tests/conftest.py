"""
Shared pytest fixtures for all tests.

This module provides fixtures that are available to all test modules:
- Sample PDFs (ESC sheets, drawing sets)
- Sample images (plan sheets, templates)
- Temporary directories
- Common test utilities

Tool-specific fixtures should be defined in:
- tools/<tool>/tests/conftest.py
"""

import sys
import pytest
import logging
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PDFS_DIR = FIXTURES_DIR / "pdfs"
IMAGES_DIR = FIXTURES_DIR / "images"
EXPECTED_DIR = FIXTURES_DIR / "expected"

# Ensure fixture directories exist
FIXTURES_DIR.mkdir(exist_ok=True)
PDFS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)
EXPECTED_DIR.mkdir(exist_ok=True)


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Path to project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def temp_output_dir(tmp_path) -> Path:
    """Temporary directory for test outputs."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


# ============================================================================
# Logging Fixtures
# ============================================================================

@pytest.fixture
def disable_logging():
    """Disable logging during tests for cleaner output."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def enable_debug_logging():
    """Enable debug-level logging for test diagnostics."""
    previous_level = logging.root.level
    logging.basicConfig(level=logging.DEBUG)
    yield
    logging.root.setLevel(previous_level)


# ============================================================================
# PDF Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def sample_esc_pdf() -> Optional[Path]:
    """
    Sample ESC sheet PDF with all required elements present.

    This is a valid ESC sheet that should pass all validation checks.
    Contains: north arrow, scale, legend, SCE, CONC WASH, etc.

    Returns:
        Path to PDF file, or None if not available
    """
    pdf_path = PDFS_DIR / "esc_sheet_valid.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Test fixture not available: {pdf_path}")
    return pdf_path


@pytest.fixture(scope="session")
def esc_missing_sce() -> Optional[Path]:
    """
    Sample ESC sheet missing SCE marker.

    Should fail validation for missing critical element.
    """
    pdf_path = PDFS_DIR / "esc_sheet_missing_sce.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Test fixture not available: {pdf_path}")
    return pdf_path


@pytest.fixture(scope="session")
def esc_missing_conc_wash() -> Optional[Path]:
    """
    Sample ESC sheet missing CONC WASH marker.

    Should fail validation for missing critical element.
    """
    pdf_path = PDFS_DIR / "esc_sheet_missing_conc_wash.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Test fixture not available: {pdf_path}")
    return pdf_path


@pytest.fixture(scope="session")
def drawing_set_sample() -> Optional[Path]:
    """
    Sample multi-page drawing set (50+ pages).

    For testing drawing analysis and batch processing.
    """
    pdf_path = PDFS_DIR / "drawing_set_sample.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Test fixture not available: {pdf_path}")
    return pdf_path


# ============================================================================
# Image Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def north_arrow_template() -> Optional[Path]:
    """
    Template image for north arrow detection.

    Used for template matching in visual detection.
    """
    template_path = IMAGES_DIR / "north_arrow_template.png"
    if not template_path.exists():
        # Try to find it in tools/esc-validator/templates/
        alt_path = PROJECT_ROOT / "tools" / "esc-validator" / "templates" / "north_arrow.png"
        if alt_path.exists():
            return alt_path
        pytest.skip(f"Test fixture not available: {template_path}")
    return template_path


@pytest.fixture(scope="session")
def plan_sheet_300dpi() -> Optional[Path]:
    """
    High-resolution plan sheet image (300 DPI).

    For testing image processing and OCR accuracy.
    """
    image_path = IMAGES_DIR / "plan_sheet_300dpi.png"
    if not image_path.exists():
        pytest.skip(f"Test fixture not available: {image_path}")
    return image_path


@pytest.fixture
def blank_image() -> np.ndarray:
    """
    Create a blank white image for testing.

    Returns:
        numpy array (500x500, RGB)
    """
    img = Image.new('RGB', (500, 500), color='white')
    return np.array(img)


@pytest.fixture
def sample_text_image() -> np.ndarray:
    """
    Create a simple image with text for OCR testing.

    Returns:
        numpy array with rendered text
    """
    from PIL import ImageDraw, ImageFont

    img = Image.new('RGB', (800, 200), color='white')
    draw = ImageDraw.Draw(img)

    # Use default font
    text = "EROSION AND SEDIMENT CONTROL NOTES"
    draw.text((50, 50), text, fill='black')

    return np.array(img)


# ============================================================================
# Expected Output Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def expected_esc_validation_result() -> Optional[Path]:
    """
    Expected JSON output from valid ESC sheet validation.

    Used for regression testing.
    """
    json_path = EXPECTED_DIR / "esc_validation_results.json"
    if not json_path.exists():
        pytest.skip(f"Test fixture not available: {json_path}")
    return json_path


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_tesseract_output():
    """
    Mock Tesseract OCR output for testing without OCR dependency.

    Returns sample extracted text from ESC sheet.
    """
    return """
    EROSION AND SEDIMENT CONTROL NOTES
    SHEET 1 OF 1

    1. SILT FENCE (SCE)
    2. CONCRETE WASHOUT (CONC WASH)
    3. STORM DRAIN INLET PROTECTION

    SCALE: 1" = 30'
    LEGEND:
    - Existing contour (dashed)
    - Proposed contour (solid)

    Streets labeled:
    - KOTI WAY
    - ENTRADA DRIVE
    """


# ============================================================================
# Parametrize Helpers
# ============================================================================

def pytest_configure(config):
    """
    Configure custom pytest options and markers.
    """
    # Add custom markers (also defined in pytest.ini)
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "performance: Performance benchmarks")
    config.addinivalue_line("markers", "ui: UI tests")


def pytest_collection_modifyitems(config, items):
    """
    Modify test items during collection.

    - Add 'unit' marker to tests in tests/unit/
    - Add 'integration' marker to tests in tests/integration/
    - Add 'e2e' marker to tests in tests/e2e/
    """
    for item in items:
        # Get test file path relative to tests/
        rel_path = Path(item.fspath).relative_to(PROJECT_ROOT / "tests")

        # Auto-add markers based on directory
        if rel_path.parts[0] == "unit" and "unit" not in item.keywords:
            item.add_marker(pytest.mark.unit)
        elif rel_path.parts[0] == "integration" and "integration" not in item.keywords:
            item.add_marker(pytest.mark.integration)
        elif rel_path.parts[0] == "e2e" and "e2e" not in item.keywords:
            item.add_marker(pytest.mark.e2e)
        elif rel_path.parts[0] == "performance" and "performance" not in item.keywords:
            item.add_marker(pytest.mark.performance)
