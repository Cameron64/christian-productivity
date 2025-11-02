# Entrada East Project Screenshots

**Source Document:** `documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf`
**Project:** 5620-01 Entrada East Subdivision
**Date:** August 7, 2025
**Total Screenshots:** 18

---

## Quick Reference

| Screenshot | Page | DPI | Purpose | Size |
|------------|------|-----|---------|------|
| `page_16_screenshot.png` | 16 | 150 | **ESC Notes (primary test)** | Standard |
| `page_3_full_resolution.png` | 3 | 300 | Plan sheet (high-res) | Large |
| `page3_title_block.png` | 3 | 150 | Title block extraction | Small |
| `page14_full_resolution.png` | 14 | 300 | Plan sheet with north arrow | Large |
| `page14_north_arrow_detection.png` | 14 | 150 | North arrow detection test | Medium |
| `page14_actual_north_arrow_region.png` | 14 | 150 | North arrow closeup | Small |
| `north_arrow_detection_full.png` | 14 | 150 | Full page north arrow test | Standard |
| `north_arrow_detection_zoom.png` | 14 | 150 | Zoomed north arrow | Small |

---

## Page-by-Page Breakdown

### Cover/Title Pages (Pages 0-4)

**preview_page_0.png**
- **Page:** 0 (Cover sheet)
- **Content:** Project title, client info, project number
- **Use Case:** Project identification, metadata extraction

**preview_page_1.png**
- **Page:** 1
- **Content:** Index/table of contents
- **Use Case:** Sheet navigation reference

**preview_page_2.png**
- **Page:** 2
- **Content:** General notes
- **Use Case:** Text extraction testing

**preview_page_3.png**
- **Page:** 3
- **Content:** Plan view
- **Use Case:** Quick preview for sheet type detection

**preview_page_4.png**
- **Page:** 4
- **Content:** Plan view continuation
- **Use Case:** Quick preview

### Page 3 - Plan Sheet (Full Detail)

**page_3_full_resolution.png**
- **DPI:** 300
- **Size:** Large (~2-5 MB)
- **Content:** Complete plan sheet with streets, lots, contours
- **Use Cases:**
  - Street labeling verification
  - Contour line detection
  - High-resolution OCR testing
  - Visual detection debugging

**page3_title_block.png**
- **DPI:** 150
- **Size:** Small (<1 MB)
- **Content:** Title block only (bottom-right corner)
- **Use Cases:**
  - Sheet number extraction
  - Project info extraction
  - Quick reference for sheet identification

### Page 14 - North Arrow Testing

**page14_full_resolution.png**
- **DPI:** 300
- **Size:** Large (~2-5 MB)
- **Content:** Complete plan sheet
- **Use Cases:**
  - Full sheet validation
  - High-resolution feature detection

**page14_north_arrow_detection.png**
- **DPI:** 150
- **Size:** Medium (~1-2 MB)
- **Content:** Full page with north arrow highlighted/annotated
- **Use Cases:**
  - Visual detection validation
  - Debug north arrow detection algorithm
  - Template matching testing

**page14_actual_north_arrow_region.png**
- **DPI:** 150
- **Size:** Small (<500 KB)
- **Content:** Closeup of north arrow symbol only
- **Use Cases:**
  - Template creation/refinement
  - Symbol detection testing
  - Visual comparison

**north_arrow_detection_full.png**
- **DPI:** 150
- **Size:** Standard (~1 MB)
- **Content:** Full page with detection overlay
- **Use Cases:**
  - Algorithm validation
  - Confidence score visualization

**north_arrow_detection_zoom.png**
- **DPI:** 150
- **Size:** Small (<500 KB)
- **Content:** Zoomed view of detected north arrow
- **Use Cases:**
  - Detailed inspection
  - Debug false positives/negatives

### Page 15-19 - Additional Plan Sheets

**preview_page_14.png**
- **Page:** 14
- **Content:** Quick preview
- **Use Case:** Fast reference

**preview_page_15.png**
- **Page:** 15
- **Content:** Plan view
- **Use Case:** Sheet type detection

**preview_page_17.png**
- **Page:** 17
- **Content:** Plan/profile sheet
- **Use Case:** Different sheet type testing

**preview_page_18.png**
- **Page:** 18
- **Content:** Plan/profile continuation
- **Use Case:** Multi-page validation

**preview_page_19.png**
- **Page:** 19
- **Content:** Plan view
- **Use Case:** Additional test cases

### Page 16 - ESC Notes (PRIMARY TEST SHEET)

**page_16_screenshot.png**
- **DPI:** 150
- **Size:** Standard (~1 MB)
- **Content:** **Erosion and Sediment Control Notes sheet**
- **Use Cases:**
  - **Primary validation test sheet**
  - Text detection (12+ checklist items)
  - OCR accuracy testing
  - Critical element detection (SCE, CONC WASH)
  - Legend verification
  - Scale bar detection
  - Street labeling (should be 0 for notes sheet)
  - Phase 1, 2, and 2.1 testing

**Key Elements on Page 16:**
- North arrow (should be detected)
- Scale bar (should be detected)
- Legend (should be detected)
- "EROSION AND SEDIMENT CONTROL NOTES" title
- SCE (Silt Fence) markers (critical - 3+ instances)
- CONC WASH markers (critical - 1+ instances)
- Storm drain inlet protection
- Erosion control notes
- Construction sequence
- Maintenance requirements

---

## Common Use Cases

### 1. ESC Validator Testing
**Primary:** `page_16_screenshot.png`
```python
# Phase 1: Text detection
image = extract_page_as_image("page_16_screenshot.png")
results = detect_required_labels(image)
assert results['sce']['detected']
assert results['conc_wash']['detected']
```

### 2. North Arrow Detection
**Primary:** `page14_north_arrow_detection.png`, `north_arrow_detection_full.png`
```python
# Visual detection testing
image = extract_page_as_image("page14_full_resolution.png")
detected = detect_north_arrow(image, template)
assert detected
```

### 3. Contour Line Detection (Phase 2)
**Primary:** `page_3_full_resolution.png`, `page14_full_resolution.png`
```python
# Line detection and classification
image = extract_page_as_image("page_3_full_resolution.png")
result = verify_contour_conventions(image, text)
assert result['total_lines'] > 100
```

### 4. Spatial Filtering (Phase 2.1)
**Primary:** `page_3_full_resolution.png` (or page 26 if available)
```python
# Smart spatial filtering
image = extract_page_as_image("page_3_full_resolution.png")
result = verify_contour_conventions_smart(image, text)
assert len(result['contours']) < 20  # Filtered from hundreds
```

### 5. Title Block Extraction
**Primary:** `page3_title_block.png`
```python
# Metadata extraction
image = extract_page_as_image("page3_title_block.png")
sheet_num = extract_sheet_number(image)
assert sheet_num == "3"
```

### 6. Sheet Type Detection
**Primary:** `preview_page_*.png` files
```python
# Detect if sheet is ESC notes vs plan view
for page in [3, 14, 15, 16, 17]:
    image = extract_page_as_image(f"preview_page_{page}.png")
    sheet_type = detect_sheet_type(image, text)
    # page 16 should be "notes", others should be "plan"
```

---

## Screenshot Specifications

### Standard Screenshots
- **DPI:** 150
- **Format:** PNG (lossless)
- **Color Space:** RGB
- **Typical Size:** 1-2 MB
- **Use:** General testing, OCR, quick reference

### High-Resolution Screenshots
- **DPI:** 300
- **Format:** PNG (lossless)
- **Color Space:** RGB
- **Typical Size:** 2-5 MB
- **Use:** Detailed analysis, template creation, debugging

### Preview Screenshots
- **DPI:** 75-100
- **Format:** PNG
- **Color Space:** RGB
- **Typical Size:** <500 KB
- **Use:** Fast preview, sheet type detection, navigation

---

## Regenerating Screenshots

If screenshots need to be recreated:

```python
from esc_validator.extractor import extract_page_as_image
from PIL import Image

# Source PDF
pdf_path = "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf"

# Primary test sheet (page 16)
image = extract_page_as_image(pdf_path, page_num=16, dpi=150)
Image.fromarray(image).save("page_16_screenshot.png")

# High-resolution for detailed analysis (page 3)
image = extract_page_as_image(pdf_path, page_num=3, dpi=300)
Image.fromarray(image).save("page_3_full_resolution.png")

# Preview for quick reference
for page in range(20):
    image = extract_page_as_image(pdf_path, page_num=page, dpi=75)
    Image.fromarray(image).save(f"preview_page_{page}.png")
```

---

## Testing History

### Phase 1 Testing (Text/Label Detection)
- **Primary Sheet:** Page 16 (ESC Notes)
- **Tests:** 12+ checklist elements
- **Results:** 75-85% accuracy
- **Critical Elements:** 0% false negatives (SCE, CONC WASH)

### Phase 1.3 Testing (Visual Detection)
- **Primary Sheet:** Page 14 (north arrow)
- **Tests:** North arrow detection, street counting
- **Results:** Improved confidence scores, context-aware counting

### Phase 2 Testing (Line Detection)
- **Primary Sheet:** Page 3 or page 26 (contours)
- **Tests:** Solid/dashed line classification
- **Results:** 70-80% accuracy, detected 857 lines

### Phase 2.1 Testing (Spatial Filtering)
- **Primary Sheet:** Page 26 (or page 3)
- **Tests:** Contour-specific filtering
- **Results:** 99% false positive reduction (857 → 9 lines)

---

## Related Documentation

- **Main Screenshot README:** [../README.md](../README.md)
- **ESC Validator:** [../../README.md](../../README.md)
- **Test Architecture:** [../../../../docs/testing/TEST_ARCHITECTURE.md](../../../../docs/testing/TEST_ARCHITECTURE.md)

---

**Created:** 2025-11-02
**Last Updated:** 2025-11-02
**Project Status:** Active (primary test document)
