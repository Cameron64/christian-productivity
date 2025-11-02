# Entrada East Project Screenshots

**Source Document:** `documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf`
**Project:** 5620-01 Entrada East Subdivision
**Date:** August 7, 2025
**Total Screenshots:** 18
**Organization:** Feature-based (by testing purpose)

---

## Directory Structure

```
entrada-east-08.07.2025/
├── INDEX.md                    # This file
├── esc-notes/                  # ESC Notes sheet (Page 16)
│   └── page_16_screenshot.png  # Primary validation test sheet
├── north-arrow/                # North arrow detection (Page 14)
│   ├── north_arrow_detection_full.png
│   ├── north_arrow_detection_zoom.png
│   ├── page14_actual_north_arrow_region.png
│   └── page14_north_arrow_detection.png
├── contours/                   # Contour line testing (Pages 3, 14)
│   ├── page_3_full_resolution.png
│   └── page14_full_resolution.png
├── title-blocks/               # Title block extraction (Page 3)
│   └── page3_title_block.png
└── previews/                   # Quick reference previews
    ├── preview_page_0.png      # Cover sheet
    ├── preview_page_1.png      # Index
    ├── preview_page_2.png      # General notes
    ├── preview_page_3.png      # Plan view
    ├── preview_page_4.png      # Plan view
    ├── preview_page_14.png     # Plan view
    ├── preview_page_15.png     # Plan view
    ├── preview_page_17.png     # Plan/profile
    ├── preview_page_18.png     # Plan/profile
    └── preview_page_19.png     # Plan view
```

---

## Quick Reference by Feature

| Feature | Directory | Files | Primary Use Case |
|---------|-----------|-------|------------------|
| **ESC Notes Validation** | `esc-notes/` | 1 | Phase 1 text detection, primary test sheet |
| **North Arrow Detection** | `north-arrow/` | 4 | Visual detection, template matching |
| **Contour Line Testing** | `contours/` | 2 | Phase 2/2.1 line detection & filtering |
| **Title Block Extraction** | `title-blocks/` | 1 | Metadata extraction, sheet identification |
| **Quick Previews** | `previews/` | 10 | Fast reference, sheet type detection |

---

## Feature Directories

### 1. ESC Notes (`esc-notes/`)

**Purpose:** Primary validation test sheet for ESC checklist items

**page_16_screenshot.png**
- **Page:** 16
- **DPI:** 150
- **Size:** ~525 KB
- **Content:** Complete ESC Notes sheet
- **Primary Use Cases:**
  - **Phase 1 Testing:** Text detection (12+ checklist elements)
  - **Critical Items:** SCE and CONC WASH detection
  - **Legend Verification:** Scale bar, north arrow, legend
  - **OCR Accuracy:** Clean text extraction
  - **Sheet Type Detection:** Identify as "notes" type
  - **Street Labeling:** Should detect 0 streets (notes sheet)

**Key Elements:**
- North arrow symbol ✓
- Scale bar ✓
- Legend ✓
- "EROSION AND SEDIMENT CONTROL NOTES" title ✓
- SCE (Silt Fence) markers - 3+ instances ✓
- CONC WASH markers - 1+ instances ✓
- Storm drain inlet protection ✓
- Construction sequence notes ✓

**Test Commands:**
```bash
# Use in validation
python validate_esc.py --image esc-notes/page_16_screenshot.png

# Quick view
find esc-notes/ -name "*.png"
```

---

### 2. North Arrow (`north-arrow/`)

**Purpose:** Visual detection and template matching for north arrow symbol

**north_arrow_detection_full.png**
- **Page:** 14
- **DPI:** 150
- **Size:** ~4.5 MB
- **Content:** Full page with north arrow detection overlay
- **Use Cases:**
  - Algorithm validation
  - Confidence score visualization
  - Debug detection failures

**north_arrow_detection_zoom.png**
- **DPI:** 150
- **Size:** ~24 KB
- **Content:** Zoomed view of detected north arrow
- **Use Cases:**
  - Detailed inspection
  - Template refinement
  - Debug false positives

**page14_actual_north_arrow_region.png**
- **DPI:** 150
- **Size:** ~113 KB
- **Content:** Closeup of north arrow symbol only
- **Use Cases:**
  - **Template creation/refinement**
  - Symbol detection testing
  - Visual comparison with template

**page14_north_arrow_detection.png**
- **DPI:** 150
- **Size:** ~6 KB
- **Content:** Detection result visualization
- **Use Cases:**
  - Quick validation check
  - Detection overlay

**Test Commands:**
```bash
# Find north arrow screenshots
ls north-arrow/

# Test detection
python -c "from esc_validator.symbol_detector import detect_north_arrow; \
detect_north_arrow('north-arrow/page14_actual_north_arrow_region.png')"
```

**Phase Reference:** Phase 1.3 (Visual Detection)

---

### 3. Contours (`contours/`)

**Purpose:** Line detection, classification, and spatial filtering

**page_3_full_resolution.png**
- **Page:** 3
- **DPI:** 300
- **Size:** ~4.5 MB
- **Content:** High-resolution plan sheet with streets, lots, contours
- **Use Cases:**
  - **Phase 2:** Line detection (solid vs dashed)
  - **Phase 2.1:** Spatial filtering (857 → 9 contours)
  - Street labeling verification
  - Contour convention testing
  - High-resolution OCR

**page14_full_resolution.png**
- **Page:** 14
- **DPI:** 300
- **Size:** ~1.2 MB
- **Content:** High-resolution plan sheet
- **Use Cases:**
  - Alternative contour testing
  - Full sheet validation
  - High-resolution feature detection

**Test Commands:**
```bash
# Phase 2: Line detection
python test_phase_2.py --image contours/page_3_full_resolution.png

# Phase 2.1: Spatial filtering
python test_phase_2_1.py --image contours/page_3_full_resolution.png --max-distance 150

# Quick view all contour sheets
ls contours/
```

**Expected Results (page 3):**
- Total lines: 800-900 (before filtering)
- Filtered contours: 5-15 (after Phase 2.1)
- Solid lines: Proposed contours
- Dashed lines: Existing contours

**Phase Reference:** Phase 2 (Line Detection), Phase 2.1 (Spatial Filtering)

---

### 4. Title Blocks (`title-blocks/`)

**Purpose:** Metadata extraction and sheet identification

**page3_title_block.png**
- **Page:** 3
- **DPI:** 150
- **Size:** ~68 KB
- **Content:** Title block only (bottom-right corner)
- **Use Cases:**
  - Sheet number extraction
  - Project info extraction
  - Engineer seal detection
  - Date verification
  - Quick reference for sheet ID

**Extractable Information:**
- Sheet number
- Sheet title
- Project name
- Project number
- Date
- Engineer name
- Company name

**Test Commands:**
```bash
# Extract metadata
python -c "from esc_validator.text_detector import extract_text_from_image; \
import cv2; img = cv2.imread('title-blocks/page3_title_block.png'); \
print(extract_text_from_image(img))"
```

---

### 5. Previews (`previews/`)

**Purpose:** Fast reference and sheet type detection (no heavy processing)

**Quick Preview Index:**
| File | Page | Content | Sheet Type | Use Case |
|------|------|---------|------------|----------|
| `preview_page_0.png` | 0 | Cover sheet | Cover | Project identification |
| `preview_page_1.png` | 1 | Index/TOC | Index | Navigation reference |
| `preview_page_2.png` | 2 | General notes | Notes | Text extraction |
| `preview_page_3.png` | 3 | Plan view | Plan | Sheet type detection |
| `preview_page_4.png` | 4 | Plan view | Plan | Additional test case |
| `preview_page_14.png` | 14 | Plan view | Plan | Fast reference |
| `preview_page_15.png` | 15 | Plan view | Plan | Sheet variety |
| `preview_page_17.png` | 17 | Plan/profile | Profile | Different type testing |
| `preview_page_18.png` | 18 | Plan/profile | Profile | Continuation |
| `preview_page_19.png` | 19 | Plan view | Plan | Additional test |

**Test Commands:**
```bash
# Quick preview all sheets
ls previews/ | sort -V

# Detect sheet types
for f in previews/*.png; do
  echo "$f -> $(detect_sheet_type $f)"
done
```

**DPI:** 75-100 (low resolution for speed)
**Size:** 150-450 KB each

---

## Common Testing Workflows

### 1. Full ESC Validation (Phase 1)
```bash
# Primary test
python validate_esc.py esc-notes/page_16_screenshot.png

# Expected: All checklist items detected
# Critical: SCE ✓, CONC WASH ✓
# Accuracy: 75-85%
```

### 2. North Arrow Detection (Phase 1.3)
```bash
# Test detection
python test_north_arrow.py north-arrow/page14_actual_north_arrow_region.png

# Compare methods
python test_phase_1_3.py --old-method --new-method

# Expected: Confidence >80%
```

### 3. Contour Line Detection (Phase 2)
```bash
# Detect all lines
python test_phase_2.py contours/page_3_full_resolution.png

# Expected: 800-900 lines detected
# Solid: ~100-200 (proposed)
# Dashed: ~600-700 (existing)
```

### 4. Spatial Filtering (Phase 2.1)
```bash
# Smart filtering
python test_phase_2_1.py contours/page_3_full_resolution.png --max-distance 150

# Expected: 5-15 contours after filtering
# Improvement: 98-99% false positive reduction
```

### 5. Sheet Type Detection
```bash
# Test sheet type detection
for dir in esc-notes north-arrow contours previews; do
  for img in $dir/*.png; do
    python detect_sheet_type.py "$img"
  done
done

# Expected:
# - esc-notes: "notes"
# - Others: "plan" or "profile"
```

---

## Search Quick Reference

### By Feature
```bash
# ESC validation
ls esc-notes/

# North arrow testing
ls north-arrow/

# Contour line testing
ls contours/

# Title block extraction
ls title-blocks/

# Quick previews
ls previews/
```

### By Page Number
```bash
# Find all screenshots from page 16
find . -name "*page_16*"
# Result: esc-notes/page_16_screenshot.png

# Find all screenshots from page 14
find . -name "*page14*" -o -name "*page_14*"
# Result: north-arrow/* and contours/page14_full_resolution.png

# Find all screenshots from page 3
find . -name "*page_3*" -o -name "*page3*"
# Result: contours/page_3_full_resolution.png, title-blocks/page3_title_block.png, previews/preview_page_3.png
```

### By Use Case
```bash
# High-resolution images (>1 MB)
find . -name "*.png" -size +1M

# Preview images only
ls previews/

# Detection debugging
ls north-arrow/*detection*

# Template material
ls north-arrow/*region*
```

---

## Adding New Screenshots

### When to Add to Each Directory

**esc-notes/**
- Primary ESC Notes sheets (page 16 or equivalent)
- Different projects' ESC sheets
- Different scan qualities for testing
- Example: `page_16_high_res.png`, `page_16_poor_scan.png`

**north-arrow/**
- North arrow detection results
- Template material
- Different symbol styles
- Example: `page_5_north_arrow.png`, `north_arrow_style_2.png`

**contours/**
- High-resolution plan sheets with contours
- Different contour density examples
- Challenging cases (tight spacing, curved, etc.)
- Example: `page_26_dense_contours.png`, `page_8_curved_contours.png`

**title-blocks/**
- Various title block styles
- Different companies/engineers
- Edge cases (missing info, stamps, etc.)
- Example: `page_5_title_block.png`, `title_block_with_seal.png`

**previews/**
- Quick reference for any page
- Sheet type examples
- Navigation aids
- Example: `preview_page_25.png`

---

## Naming Conventions

### General Pattern
`<page_number>_<description>.png` or `<description>_page_<number>.png`

### Examples
```
# ESC Notes
page_16_screenshot.png              # Standard
page_16_high_res_300dpi.png        # Variant with DPI
esc_notes_page_16.png              # Alternative format

# North Arrow
page14_north_arrow_region.png      # Feature specific
north_arrow_detection_full.png     # Result visualization
north_arrow_template.png           # Template material

# Contours
page_3_full_resolution.png         # High-res for processing
page_3_contours_only.png           # Isolated feature
page_26_dense_contours.png         # Descriptive case

# Previews
preview_page_0.png                 # Standard format
```

---

## Regenerating Screenshots

If screenshots need to be recreated:

```python
from esc_validator.extractor import extract_page_as_image
from PIL import Image

pdf_path = "documents/5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf"

# ESC Notes (primary test)
img = extract_page_as_image(pdf_path, page_num=16, dpi=150)
Image.fromarray(img).save("esc-notes/page_16_screenshot.png")

# High-res contours
img = extract_page_as_image(pdf_path, page_num=3, dpi=300)
Image.fromarray(img).save("contours/page_3_full_resolution.png")

# North arrow region (crop from page 14)
img = extract_page_as_image(pdf_path, page_num=14, dpi=150)
# ... crop to north arrow region ...
Image.fromarray(img).save("north-arrow/page14_north_arrow_region.png")

# Previews (low-res for speed)
for page in range(20):
    img = extract_page_as_image(pdf_path, page_num=page, dpi=75)
    Image.fromarray(img).save(f"previews/preview_page_{page}.png")
```

---

## Testing History by Feature

### ESC Notes (Phase 1)
- **Primary Test Sheet:** page_16_screenshot.png
- **Accuracy:** 75-85%
- **Critical Elements:** 0% false negatives
- **Status:** ✅ Production ready

### North Arrow (Phase 1.3)
- **Test Images:** 4 variations from page 14
- **Method:** ORB → Multi-scale template matching
- **Improvement:** Significant confidence increase
- **Status:** ✅ Complete

### Contours (Phase 2 + 2.1)
- **Test Images:** page_3_full_resolution.png (primary)
- **Phase 2 Results:** 857 lines detected (all types)
- **Phase 2.1 Results:** 9 contours (filtered)
- **Improvement:** 98.9% false positive reduction
- **Status:** ✅ Production ready

---

## Related Documentation

- **Main Screenshot Cache:** [../README.md](../README.md)
- **ESC Validator Guide:** [../../README.md](../../README.md)
- **Test Architecture:** [../../../../docs/testing/TEST_ARCHITECTURE.md](../../../../docs/testing/TEST_ARCHITECTURE.md)
- **Development Rules:** [../../.claude/CLAUDE.md](../../.claude/CLAUDE.md)

---

**Created:** 2025-11-02
**Last Updated:** 2025-11-02
**Organization:** Feature-based (by testing purpose)
**Project Status:** Active (primary test document)
