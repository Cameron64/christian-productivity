# ESC Sheet Validator

Automated validation tool for Erosion and Sediment Control (ESC) sheets in civil engineering drawing sets.

**Version:** 0.1.0 (Phase 1)
**Status:** Ready for testing

---

## Overview

The ESC Sheet Validator automatically checks ESC sheets for required elements per Austin/Travis County subdivision regulations. It uses OCR and computer vision to detect labels, features, and verify minimum quantities, reducing manual review time from 15-20 minutes to 5-10 minutes per sheet.

### What It Checks (Phase 1)

**Text/Label Detection (7 items):**
- ✓ Legend present
- ✓ Scale present
- ✓ North bar present
- ✓ Limits of construction (LOC) labeled
- ✓ Silt fence (SF) labeled
- ✓ Streets labeled
- ✓ Lot and block labels

**Feature Detection (5 items):**
- ✓ Stabilized construction entrance (SCE) - at least 1 required
- ✓ Concrete washout (CONC WASH) - at least 1 required
- ✓ Staging/spoils area labeled

**Quantity Verification:**
- ✓ At least 1 SCE present
- ✓ At least 1 CONC WASH present

**Expected Accuracy:** 75-85% for text-based elements (Phase 1)

---

## Installation

### Prerequisites
- Python 3.8 or higher
- Tesseract OCR (for text detection)
- 8GB RAM minimum (16GB recommended)

### Install Tesseract OCR

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location (C:\Program Files\Tesseract-OCR)
3. Add to PATH or set `TESSERACT_CMD` environment variable

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### Install Python Dependencies

From the `tools/esc-validator` directory:

```bash
pip install -r requirements.txt
```

This installs:
- `pdfplumber` - PDF extraction
- `pytesseract` - OCR text detection
- `opencv-python` - Image processing
- `python-Levenshtein` - Fuzzy text matching
- `Pillow` - Image manipulation
- `pandas` - Data analysis
- `matplotlib` - Visualization

---

## Usage

### Basic Usage

Validate a single PDF drawing set:

```bash
python validate_esc.py "path/to/drawing_set.pdf"
```

The tool will:
1. Search for the ESC sheet in the PDF
2. Extract and preprocess the sheet
3. Detect required elements using OCR
4. Generate a validation report
5. Print results to console

### Save Report to File

```bash
python validate_esc.py "drawing_set.pdf" --output report.md
```

### Batch Processing

Validate multiple PDFs at once:

```bash
python validate_esc.py documents/*.pdf --batch --output-dir reports/
```

Each PDF gets its own validation report in the `reports/` directory.

### Advanced Options

**Specify ESC sheet page number manually:**
```bash
python validate_esc.py "drawing_set.pdf" --page 15
```

**Save extracted images for inspection:**
```bash
python validate_esc.py "drawing_set.pdf" --save-images --output-dir output/
```

**Generate verbose report with detailed findings:**
```bash
python validate_esc.py "drawing_set.pdf" --verbose --output report.md
```

**Adjust extraction resolution:**
```bash
python validate_esc.py "drawing_set.pdf" --dpi 300
```

**Enable debug logging:**
```bash
python validate_esc.py "drawing_set.pdf" --debug
```

---

## Command-Line Options

```
usage: validate_esc.py [-h] [-o OUTPUT] [--output-dir OUTPUT_DIR] [--batch]
                       [-p PAGE] [--save-images] [-v] [--dpi DPI] [--debug]
                       pdf_files [pdf_files ...]

positional arguments:
  pdf_files             PDF file(s) to validate

optional arguments:
  -h, --help            show this help message and exit
  -o, --output OUTPUT   Output file path for validation report (markdown)
  --output-dir DIR      Output directory for reports/images
  --batch               Batch process multiple PDFs
  -p, --page PAGE       Specific page number of ESC sheet (0-indexed)
  --save-images         Save extracted and preprocessed images
  -v, --verbose         Generate verbose report with detailed findings
  --dpi DPI             Resolution for PDF extraction (default: 300)
  --debug               Enable debug logging
```

---

## Output Format

### Console Output

```
✅ 5620-01 Entrada East.pdf - PASS
   Checks passed: 10/12 (83%)
   Report saved: report.md
```

Or if issues are found:

```
⚠️  5620-01 Entrada East.pdf - NEEDS REVIEW
   Checks passed: 9/12 (75%)
   CRITICAL ISSUES: CONC_WASH
   Report saved: report.md
```

### Markdown Report

The tool generates a detailed markdown report with:

- **Overall Status:** Pass/Needs Review/Fail
- **Summary Statistics:** Pass rate, confidence scores
- **Critical Issues:** Missing required elements (SCE, CONC WASH)
- **Checklist Results:** Element-by-element table
- **Detailed Findings:** (if --verbose) All detected matches
- **Recommendations:** Actions to address issues

Example report excerpt:

```markdown
# ESC Sheet Validation Report

**Status:** ⚠️ NEEDS REVIEW
**Checks Passed:** 10/12 (83%)
**Average Confidence:** 87%

## 🚨 Critical Issues

- **Concrete Washout** - MUST be added before submission

## Checklist Results

| Element | Status | Count | Confidence | Notes |
|---------|--------|-------|------------|-------|
| Legend | ✓ | 1 | 90% | Found at bottom of sheet |
| Scale | ✓ | 1 | 95% | 1"=50' |
| Concrete Washout | ❌ | 0 | - | Required: ≥1, Found: 0 |
...
```

---

## Project Structure

```
tools/esc-validator/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── validate_esc.py              # Main CLI tool
│
├── esc_validator/               # Python package
│   ├── __init__.py              # Package initialization
│   ├── extractor.py             # PDF extraction & preprocessing
│   ├── text_detector.py         # OCR-based text detection
│   ├── validator.py             # Main validation logic
│   └── reporter.py              # Report generation
│
├── templates/                   # Symbol templates (Phase 3)
├── models/                      # ML models (Phase 6)
└── tests/                       # Test suite
    └── sample_sheets/           # Test ESC sheets
```

---

## How It Works

### Step 1: Extract ESC Sheet

The tool searches the PDF for pages containing "ESC" and related keywords to identify the ESC sheet. If found, it extracts the page as a high-resolution image (300 DPI by default).

### Step 2: Preprocess for OCR

The extracted image is preprocessed to improve OCR accuracy:
- Convert to grayscale
- Apply denoising
- Enhance contrast using CLAHE
- Optional adaptive thresholding

### Step 3: Text Detection

Tesseract OCR extracts all text from the preprocessed image. The tool then searches for required keywords using:
- **Exact matching:** Fast detection of clear labels
- **Fuzzy matching:** Handles OCR errors and variations (e.g., "CONC WASH" vs "CONCRETE WASHOUT")
- **Count verification:** Ensures minimum quantities (≥1 SCE, ≥1 CONC WASH)

### Step 4: Generate Report

Results are compiled into a markdown report with:
- Pass/fail status for each element
- Confidence scores
- Critical failures highlighted
- Recommendations for corrections

---

## Accuracy & Limitations

### Expected Accuracy (Phase 1)

- **Text labels:** 75-85% detection rate
- **Feature mentions:** 80-90% detection rate
- **Minimum quantities:** 85-95% accuracy

### Known Limitations

1. **OCR Quality Dependent**
   - Poor image quality reduces accuracy
   - Handwritten labels may not be detected
   - Small text (<10pt) may be missed

2. **Keyword-Based Detection**
   - Relies on standard terminology
   - Non-standard abbreviations may not match
   - Context-free (doesn't understand drawing semantics)

3. **No Line/Symbol Detection (Phase 1)**
   - Cannot verify dashed vs solid contour lines
   - Cannot detect symbols like north arrows visually
   - Cannot validate legend line types

4. **False Negatives Possible**
   - Better to flag for manual review than miss critical elements
   - Always perform manual verification before submission

### Future Enhancements

- **Phase 2:** Line type detection (solid vs dashed)
- **Phase 3:** Symbol detection (north arrow, circles)
- **Phase 4:** Quality checks (legend matching, overlapping labels)
- **Phase 5:** Integration and batch processing improvements
- **Phase 6:** Machine learning for 90%+ accuracy

---

## Troubleshooting

### "No ESC sheet found"

**Problem:** Tool cannot locate ESC sheet in PDF.

**Solutions:**
- Manually specify page number: `--page 15`
- Check that ESC sheet contains keywords: "ESC", "EROSION", "SEDIMENT", "CONTROL"
- Verify PDF is not password-protected or corrupted

### "OCR accuracy is poor"

**Problem:** Text detection misses many labels.

**Solutions:**
- Increase extraction resolution: `--dpi 450`
- Save images and inspect quality: `--save-images`
- Check Tesseract installation: `tesseract --version`
- Try improving PDF quality (rescan at higher DPI)

### "False negatives on critical elements"

**Problem:** Tool reports missing SCE or CONC WASH that are actually present.

**Solutions:**
- Check for non-standard abbreviations (add to keyword list)
- Verify labels are text, not graphics
- Inspect preprocessed image to see if text is readable
- Consider adding custom keywords in `text_detector.py`

### "Import errors or missing dependencies"

**Problem:** Python packages not found.

**Solutions:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep pdfplumber
pip list | grep pytesseract
pip list | grep opencv
```

---

## Testing

### Test on Sample ESC Sheet

```bash
# Validate test sheet
python validate_esc.py "tests/sample_sheets/test_esc.pdf" --verbose

# Save output for inspection
python validate_esc.py "tests/sample_sheets/test_esc.pdf" \
  --save-images --output-dir test_output/
```

### Run Unit Tests (Coming Soon)

```bash
python -m pytest tests/
```

---

## Performance

**Typical Performance (300 DPI):**
- Extraction: 2-5 seconds per page
- OCR: 5-10 seconds per sheet
- Detection: <1 second
- **Total: 8-16 seconds per sheet**

**Time Savings:**
- Manual review: 15-20 minutes
- With tool: 5-10 minutes (including manual verification)
- **Net savings: ~10 minutes per sheet**

---

## Development

### Adding New Keywords

To add new keyword variations, edit `esc_validator/text_detector.py`:

```python
REQUIRED_KEYWORDS = {
    "sce": ["sce", "stabilized construction entrance", "construction entrance",
            "rock entrance", "YOUR_NEW_KEYWORD"],
    # ...
}
```

### Adjusting Detection Thresholds

Fuzzy matching threshold (0.0 to 1.0, higher = stricter):

```python
def detect_keyword(text, keywords, threshold=0.8):  # Default: 0.8
    # ...
```

### Changing Minimum Quantities

To require different quantities, edit `text_detector.py`:

```python
MIN_QUANTITIES = {
    "sce": 2,  # Require 2 SCEs instead of 1
    "conc_wash": 1,
}
```

---

## Contributing

This tool is part of Christian's Productivity Tools repository. To contribute:

1. Test on diverse ESC sheets from different projects
2. Document failure modes and edge cases
3. Suggest keyword additions for detection
4. Report accuracy metrics on your drawings

---

## License

Part of Christian's Productivity Tools - Internal use for civil engineering workflows.

---

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review logs with `--debug` flag
3. Inspect extracted images with `--save-images`
4. Refer to PLAN.md for implementation details

---

## Version History

**0.1.0 (Phase 1) - 2025-11-01**
- Initial release
- PDF extraction and preprocessing
- OCR-based text detection
- Fuzzy keyword matching
- Minimum quantity verification
- Markdown report generation
- CLI with batch processing

**Planned:**
- 0.2.0: Phase 2 (line detection)
- 0.3.0: Phase 3 (symbol detection)
- 0.4.0: Phase 4 (quality checks)
- 0.5.0: Phase 5 (integration)
- 1.0.0: Production release with ML (Phase 6)

---

**Last Updated:** 2025-11-01
**Author:** Christian's Productivity Tools
**For:** Christian (Civil Engineer - Subdivision Planning)
