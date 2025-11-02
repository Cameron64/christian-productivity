# Test Screenshots - ESC Validator

This directory contains cached screenshots from test PDFs for validation, debugging, and reference.

**Purpose:** Screenshot cache to avoid repeatedly extracting pages from PDFs during development and testing.

---

## ⚠️ IMPORTANT: Check Cache First

**For AI Assistants (Claude):**

Before creating a new screenshot from a PDF:
1. **Check this cache first** - Look for existing screenshots in project subdirectories
2. **Reuse existing screenshots** - If the page/section already exists, use it
3. **Only create new screenshots** - If the specific page/view doesn't exist in cache
4. **Update index** - When adding new screenshots, update the project's INDEX.md

This saves processing time and keeps the cache organized.

---

## Directory Structure

```
test-screenshots/
├── README.md                          # This file
├── entrada-east-08.07.2025/           # Project-specific screenshots
│   ├── INDEX.md                       # Quick reference index
│   └── *.png                          # Screenshots
└── <future-project-name>/             # Additional projects as needed
    ├── INDEX.md
    └── *.png
```

---

## Naming Conventions

### Project Directories
Format: `<project-name>-<date>`

Examples:
- `entrada-east-08.07.2025/`
- `koti-way-subdivision-09.15.2025/`
- `drainage-plan-10.01.2025/`

### Screenshot Files
Format: `<page|section>_<number>_<description>.png`

Examples:
- `page_16_screenshot.png` - Full page 16 (ESC Notes)
- `preview_page_0.png` - Preview of page 0 (cover sheet)
- `page14_north_arrow_detection.png` - North arrow detection on page 14
- `page3_title_block.png` - Title block from page 3

### Best Practices
- Use lowercase with underscores
- Include page number
- Add descriptive suffix
- DPI in filename if non-standard (e.g., `page_16_300dpi.png`)

---

## Quick Search Guide

### Finding Screenshots

**By Page Number:**
```bash
# Find all screenshots of page 16
find . -name "*page_16*"

# Find all screenshots of page 14
find . -name "*page_14*" -o -name "*page14*"
```

**By Feature:**
```bash
# Find north arrow screenshots
find . -name "*north_arrow*"

# Find title block screenshots
find . -name "*title_block*"

# Find ESC notes
find . -name "*esc_notes*" -o -name "*page_16*"
```

**By Project:**
```bash
# List all Entrada East screenshots
ls entrada-east-08.07.2025/

# Search within specific project
find entrada-east-08.07.2025/ -name "*.png"
```

### Using the Index

Each project has an `INDEX.md` with:
- Document source reference
- Page-by-page breakdown
- Feature-specific screenshots
- Common use cases

---

## Current Projects

### 1. Entrada East (08.07.2025)
- **Source:** `documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf`
- **Screenshots:** 18 files
- **Index:** [entrada-east-08.07.2025/INDEX.md](entrada-east-08.07.2025/INDEX.md)
- **Key Pages:**
  - Page 16: ESC Notes sheet (primary test sheet)
  - Page 14: Plan sheet with north arrow
  - Page 3: Title block and sheet info
  - Pages 0-4, 14-19: Preview screenshots

---

## Adding New Screenshots

### When to Add
- Testing new PDF documents
- Need specific page views for debugging
- Reference images for visual detection (templates)
- Documentation examples

### How to Add

1. **Create project directory** (if new project):
```bash
mkdir test-screenshots/<project-name>-<date>/
```

2. **Extract screenshots** from PDF:
```python
from esc_validator.extractor import extract_page_as_image
image = extract_page_as_image("path/to/pdf.pdf", page_num=16, dpi=150)
# Save to test-screenshots/<project>/page_16_screenshot.png
```

3. **Name consistently**:
- `page_<num>_<description>.png` for full pages
- `preview_page_<num>.png` for quick previews
- `<feature>_<page>_<description>.png` for specific features

4. **Update INDEX.md** in project directory

5. **Update this README** (add to "Current Projects" section)

---

## Git Tracking

**Status:** Screenshots are **NOT tracked** in git (see `.gitignore`)

**Rationale:**
- Large binary files
- Generated/derivative content
- Can be regenerated from source PDFs
- Keeps repository size manageable

**To track specific screenshots:**
- Add exception to `.gitignore` for specific files
- Or use Git LFS for large binary files

---

## Cleanup and Maintenance

### Regular Tasks
- **Remove obsolete projects** - When project PDFs are no longer needed
- **Verify screenshot quality** - Ensure screenshots are readable and at appropriate DPI
- **Update indices** - Keep INDEX.md files current
- **Check disk usage** - Monitor screenshot storage (target: <50 MB per project)

### Cleanup Commands
```bash
# Remove all screenshots from old project
rm -rf test-screenshots/<old-project>/

# Find large screenshots (>5 MB)
find test-screenshots/ -name "*.png" -size +5M

# Count total screenshots
find test-screenshots/ -name "*.png" | wc -l
```

---

## Usage in Tests

Screenshots from this cache can be used in:
- **Unit tests** - For OCR and visual detection
- **Integration tests** - For full validation pipelines
- **Debugging** - Quick visual reference without PDF extraction
- **Documentation** - Examples in guides and READMEs

**Example:**
```python
# tests/conftest.py
@pytest.fixture(scope="session")
def entrada_east_page_16():
    """ESC Notes sheet (page 16) from Entrada East project."""
    screenshot_path = (
        PROJECT_ROOT / "tools" / "esc-validator" / "test-screenshots" /
        "entrada-east-08.07.2025" / "page_16_screenshot.png"
    )
    if not screenshot_path.exists():
        pytest.skip("Screenshot not available in cache")
    return screenshot_path
```

---

## Related Documentation

- **ESC Validator README:** [../README.md](../README.md)
- **Test Architecture:** [../../../docs/testing/TEST_ARCHITECTURE.md](../../../docs/testing/TEST_ARCHITECTURE.md)
- **Test Fixtures:** [../../../tests/fixtures/README.md](../../../tests/fixtures/README.md)

---

**Created:** 2025-11-02
**Last Updated:** 2025-11-02
**Total Projects:** 1 (Entrada East)
**Total Screenshots:** 18
