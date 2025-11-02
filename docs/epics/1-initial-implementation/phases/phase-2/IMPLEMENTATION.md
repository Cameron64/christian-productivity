# Phase 2 Implementation: Line Type Detection

**Status:** ✅ COMPLETE
**Completion Date:** 2025-11-01
**Accuracy Target:** 70-80%

---

## Overview

Phase 2 adds computer vision-based line detection to verify contour types and validate that dashed/solid line conventions are followed on ESC sheets.

**What Phase 2 Does:**
- Detects and classifies lines as solid or dashed
- Verifies existing contours use dashed lines
- Verifies proposed contours use solid lines
- Provides confidence scores for line type classifications

---

## Implementation Summary

### New Modules

#### 1. Line Classification (`symbol_detector.py`)

**Added Functions:**

```python
classify_line_type(line, image, sample_points=20)
```
- Classifies a line as "solid", "dashed", or "unknown"
- Analyzes pixel intensities along the line to detect gaps
- Returns (line_type, confidence)
- **Algorithm:**
  - Samples 20 points along the line
  - Counts transitions between line and gap
  - Solid: >80% coverage, <4 transitions
  - Dashed: 30-80% coverage, ≥4 transitions

```python
detect_contour_lines(image, min_line_length=300, max_line_gap=50, classify_types=True)
```
- Detects all contour lines on ESC sheet
- Uses Canny edge detection + Hough Line Transform
- Classifies each line as solid or dashed
- Returns (solid_lines, dashed_lines) with confidence scores

```python
verify_contour_conventions(image, text, existing_should_be_dashed=True)
```
- Complete contour convention verification
- Checks if existing contours are dashed (standard)
- Checks if proposed contours are solid (standard)
- Returns verification results with confidence scores

```python
find_labels_near_lines(text_with_locations, lines, max_distance=100)
```
- Spatial proximity analysis
- Finds text labels near lines
- Useful for associating labels with features
- Returns list of (label, line_idx, distance) tuples

---

### Integration Points

#### 1. Validator Module (`validator.py`)

**Updated Function:**
```python
validate_esc_sheet(..., enable_line_detection=False)
```
- New parameter: `enable_line_detection` (default: False)
- When enabled, runs Phase 2 contour verification
- Adds `line_verification` to results dictionary
- Reports warnings if line conventions violated

**Results Dictionary:**
```python
{
    "success": bool,
    "page_num": int,
    "detection_results": {...},
    "quantity_results": {...},
    "summary": {...},
    "line_verification": {  # NEW in Phase 2
        "existing_correct": bool,
        "proposed_correct": bool,
        "existing_confidence": float,
        "proposed_confidence": float,
        "notes": str
    },
    "errors": [...]
}
```

#### 2. CLI (`validate_esc.py`)

**New Option:**
```bash
--enable-line-detection
```

**Usage Examples:**
```bash
# Enable line detection for single PDF
python validate_esc.py "drawing.pdf" --enable-line-detection

# Batch processing with line detection
python validate_esc.py documents/*.pdf --batch --enable-line-detection

# Full validation with all features
python validate_esc.py "ESC_plan.pdf" \
    --enable-line-detection \
    --save-images \
    --output report.md \
    --verbose
```

---

## Technical Approach

### Edge Detection Pipeline

1. **Preprocessing:**
   - Convert to grayscale (if needed)
   - Already done by Phase 1 preprocessing

2. **Edge Detection:**
   - Canny edge detector
   - Parameters: `threshold1=50, threshold2=150`

3. **Line Detection:**
   - Hough Line Transform (Probabilistic)
   - Parameters:
     - `rho=1` - Distance resolution (1 pixel)
     - `theta=π/180` - Angular resolution (1 degree)
     - `threshold=80` - Minimum votes
     - `minLineLength=300` - Contour lines are long
     - `maxLineGap=50` - Allow gaps for intersections

4. **Line Classification:**
   - Sample 20 points along each line
   - Analyze pixel intensities
   - Count gaps and transitions
   - Classify based on coverage and gap pattern

### Classification Thresholds

| Line Type | Coverage | Transitions | Confidence |
|-----------|----------|-------------|------------|
| Solid | >80% | <4 | min(1.0, coverage) |
| Dashed | 30-80% | ≥4 | min(1.0, transitions/10) |
| Unknown | <30% | any | 0.0 |

---

## Testing

### Test Script: `test_phase_2.py`

**Run all tests:**
```bash
python test_phase_2.py --all
```

**Test with specific image:**
```bash
python test_phase_2.py --image "test_output/esc_sheet_preprocessed.png"
```

**Test full integration:**
```bash
python test_phase_2.py --pdf "documents/project.pdf"
```

### Test Coverage

1. **Test 1: Line Classification**
   - Synthetic solid line
   - Synthetic dashed line
   - Validates classification algorithm

2. **Test 2: Contour Detection**
   - Real ESC sheet image
   - Counts solid vs dashed lines
   - Reports average confidence

3. **Test 3: Convention Verification**
   - Full contour verification
   - Checks existing/proposed conventions
   - Integrates text detection

4. **Test 4: Full Integration**
   - End-to-end validation with Phase 2 enabled
   - Tests CLI integration
   - Validates results structure

---

## Known Limitations

### Current Challenges

1. **Drawing Complexity**
   - Many overlapping lines on ESC sheets
   - May detect non-contour lines (property lines, streets, etc.)
   - **Mitigation:** Use `min_line_length` to filter short features

2. **Line Thickness Variations**
   - Thick lines may affect gap detection
   - Hand-drawn vs CAD lines behave differently
   - **Mitigation:** Sample points with tolerance threshold

3. **Curved Lines**
   - Hough Transform works best on straight lines
   - Contours are often curved (elevation lines)
   - **Mitigation:** Use `maxLineGap` to connect segments

4. **Faint Lines**
   - Scanned drawings may have faint contours
   - May not pass Canny edge threshold
   - **Mitigation:** Adjust Canny thresholds or enhance preprocessing

5. **False Positives**
   - Streets, lot lines, etc. may be classified as contours
   - No way to distinguish contours from other features yet
   - **Future:** Use spatial proximity to contour labels (Phase 3)

---

## Accuracy Assessment

### Expected Performance

**Line Detection:**
- ≥70% of contour lines detected
- <20% false positives (non-contour lines)

**Line Classification:**
- ≥75% accuracy for solid/dashed classification
- Higher accuracy on CAD drawings vs hand-drawn
- Lower accuracy on scanned/copied drawings

**Convention Verification:**
- Reliable when contours clearly labeled
- Dependent on Phase 1 text detection accuracy
- Best results with clean, high-DPI images

### Benchmark Results

*To be added after testing on real ESC sheets*

---

## Future Enhancements

### Phase 3 Considerations

1. **Spatial Filtering:**
   - Use `find_labels_near_lines()` to associate labels with lines
   - Only classify lines near "contour" labels
   - Filter out streets, lot lines, etc.

2. **Improved Classification:**
   - Detect dash pattern (regular spacing = dashed)
   - Distinguish between different line styles
   - Handle dotted, dash-dot, etc.

3. **Contour Elevation Verification:**
   - Extract elevation labels near contour lines
   - Verify monotonic elevation changes
   - Detect impossible elevations

### Advanced Features (Phase 6)

1. **ML-Based Line Detection:**
   - Train model to distinguish contour vs non-contour lines
   - Learn line style conventions from examples
   - Handle curved contours better

2. **Semantic Segmentation:**
   - Classify entire regions (contours, streets, lots, etc.)
   - More robust than line-by-line analysis
   - Requires labeled training data

---

## API Reference

### Main Functions

#### `classify_line_type(line, image, sample_points=20)`

**Parameters:**
- `line`: np.ndarray - Line coordinates [x1, y1, x2, y2]
- `image`: np.ndarray - Binary edge image
- `sample_points`: int - Number of points to sample along line

**Returns:**
- `tuple` - (line_type, confidence)
  - `line_type`: str - "solid", "dashed", or "unknown"
  - `confidence`: float - 0.0 to 1.0

**Example:**
```python
from esc_validator.symbol_detector import classify_line_type
import cv2

image = cv2.imread("esc_sheet.png", cv2.IMREAD_GRAYSCALE)
edges = cv2.Canny(image, 50, 150)

line = np.array([100, 200, 500, 200])  # Horizontal line
line_type, conf = classify_line_type(line, edges)

print(f"Line type: {line_type} (confidence: {conf:.2f})")
```

---

#### `detect_contour_lines(image, min_line_length=300, max_line_gap=50, classify_types=True)`

**Parameters:**
- `image`: np.ndarray - Input image (grayscale or BGR)
- `min_line_length`: int - Minimum line length to detect (default: 300)
- `max_line_gap`: int - Maximum gap in line (default: 50)
- `classify_types`: bool - Whether to classify line types (default: True)

**Returns:**
- `tuple` - (solid_lines, dashed_lines)
  - Each is a list of tuples: [(line_coords, confidence), ...]

**Example:**
```python
from esc_validator.symbol_detector import detect_contour_lines
import cv2

image = cv2.imread("esc_sheet.png")
solid_lines, dashed_lines = detect_contour_lines(image)

print(f"Found {len(solid_lines)} solid lines")
print(f"Found {len(dashed_lines)} dashed lines")
```

---

#### `verify_contour_conventions(image, text, existing_should_be_dashed=True)`

**Parameters:**
- `image`: np.ndarray - Input image (grayscale or BGR)
- `text`: str - Extracted text from OCR
- `existing_should_be_dashed`: bool - Whether existing contours should be dashed (default: True)

**Returns:**
- `dict` - Verification results:
  ```python
  {
      'existing_correct': bool,
      'proposed_correct': bool,
      'existing_confidence': float,
      'proposed_confidence': float,
      'notes': str
  }
  ```

**Example:**
```python
from esc_validator.symbol_detector import verify_contour_conventions
from esc_validator.text_detector import extract_text_from_image
import cv2

image = cv2.imread("esc_sheet.png", cv2.IMREAD_GRAYSCALE)
text = extract_text_from_image(image)

results = verify_contour_conventions(image, text)

if results['existing_correct'] and results['proposed_correct']:
    print("✓ Contour conventions followed")
else:
    print(f"⚠ Warning: {results['notes']}")
```

---

#### `find_labels_near_lines(text_with_locations, lines, max_distance=100)`

**Parameters:**
- `text_with_locations`: list - List of (text, x, y) tuples from OCR
- `lines`: list - List of line coordinates [x1, y1, x2, y2]
- `max_distance`: float - Maximum distance (pixels) to consider "near" (default: 100)

**Returns:**
- `list` - List of (label, line_idx, distance) tuples for labels near lines

**Example:**
```python
from esc_validator.symbol_detector import find_labels_near_lines
import pytesseract
import cv2

image = cv2.imread("esc_sheet.png")

# Get text with bounding boxes
data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
text_locations = [
    (data['text'][i], data['left'][i], data['top'][i])
    for i in range(len(data['text']))
    if data['text'][i].strip()
]

# Detect lines
lines = [...]  # From detect_contour_lines()

# Find nearby labels
nearby = find_labels_near_lines(text_locations, lines, max_distance=100)

for label, line_idx, dist in nearby:
    print(f"Label '{label}' near line {line_idx} (distance: {dist:.1f}px)")
```

---

## Changelog

### Version 1.0 (2025-11-01)

**Added:**
- Line classification algorithm (`classify_line_type`)
- Contour line detection (`detect_contour_lines`)
- Contour convention verification (`verify_contour_conventions`)
- Spatial proximity analysis (`find_labels_near_lines`)
- Integration with validator module
- CLI flag `--enable-line-detection`
- Test script `test_phase_2.py`

**Modified:**
- `validator.py` - Added `enable_line_detection` parameter
- `validate_esc.py` - Added CLI argument for line detection
- `symbol_detector.py` - Added Phase 2 functions

---

## Credits

**Implementation:** Claude (via Claude Code)
**Design:** Based on PLAN.md Phase 2 specification
**Testing:** Pending validation on real ESC sheets

---

## See Also

- [PLAN.md](../../PLAN.md) - Overall ESC validator implementation plan
- [docs/phases/phase-2/README.md](../../docs/phases/phase-2/README.md) - Phase 2 planning document
- [README.md](README.md) - ESC validator overview
- [test_phase_2.py](test_phase_2.py) - Phase 2 test suite

---

**Next Steps:**
1. Run `test_phase_2.py` on sample ESC sheets
2. Benchmark accuracy on 5-10 diverse drawings
3. Adjust thresholds based on results
4. Document actual performance metrics
5. Decide: Continue to Phase 3 or jump to Phase 6 (ML)?
