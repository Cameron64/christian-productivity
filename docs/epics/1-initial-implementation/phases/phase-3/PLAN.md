# Phase 3: Symbol & Pattern Detection - Complete Implementation

**Status:** ⚠️ PARTIALLY COMPLETE (Core infrastructure done in Phase 1.3, remaining items TODO)
**Completion Date:** Phase 1.3 completed 2025-11-01, Phase 3 completion TBD
**Priority:** P2 (Medium - Core features done, enhancements remain)
**Expected Duration:** 1-2 weeks for remaining items
**Prerequisites:** Phase 1.3 complete, Phase 2 complete

---

## Overview

Phase 3 aims to detect **visual symbols and patterns** beyond text to complete ESC sheet validation. The core infrastructure was implemented in **Phase 1.3** (north arrow symbol detection, street counting), but additional symbol types and accuracy improvements remain.

**What's Already Done (Phase 1.3):**
- ✅ North arrow detection using ORB feature matching (rotation-invariant)
- ✅ Street counting using Hough line detection
- ✅ Parallel line grouping for road segments
- ✅ Template library infrastructure (`templates/` directory)
- ✅ Integration with main validator workflow
- ✅ Debug visualization support

**What Remains for Phase 3:**
- ❌ Hough Circle Transform for block label detection
- ❌ Standard ESC symbols (SF, SCE, CONC WASH icons) detection
- ❌ Multi-scale template matching improvements
- ❌ Symbol library expansion (10+ templates)
- ❌ Rotation-invariant matching enhancements

---

## Current State Assessment

### Completed Features (Phase 1.3)

**1. North Arrow Detection** (`symbol_detector.py:17-131`)
- Implementation: ORB (Oriented FAST and Rotated BRIEF) feature matching
- Rotation-invariant: ✅
- Scale-invariant: ❌ (needs multi-scale, planned for Phase 1.3.1)
- Current accuracy: **12.3% confidence** (needs improvement)
- Template: `templates/north_arrow.png` exists
- Location detection: Returns (x, y) coordinates
- Integration: Used in `text_detector.py` via `detect_required_labels()`

**2. Street Counting** (`symbol_detector.py:773-860`)
- Implementation: Hough Line Transform + parallel line grouping
- Current accuracy: **Over-detects** (55 streets on Notes sheet vs 0 expected)
- Grouping: Detects parallel lines within typical road width
- Debug visualization: Color-coded street groups
- Integration: Used in `verify_street_labeling_complete()`

**3. Template Infrastructure**
- Directory: `tools/esc-validator/templates/`
- Templates: 1 (north_arrow.png)
- Documentation: `templates/README.md` exists
- Format: PNG grayscale

**4. Visualization Tools** (`symbol_detector.py:134-212`)
- `draw_detection_result()` - Draws bounding boxes and labels
- Debug image generation with color-coded detections
- Supports both symbol and line detection visualization

### Known Issues from Phase 1.3

**Issue 1: North Arrow Low Confidence (12.3%)**
- Root cause: Template size mismatch (ORB not scale-invariant)
- Impact: Detection unreliable in production
- Solution: Multi-scale template matching (planned Phase 1.3.1)

**Issue 2: Street Counting Over-Detection (55 vs 0)**
- Root cause: Detects table borders, text underlines, leader lines as streets
- Impact: High false positive rate on Notes sheets
- Solution: Context-aware detection with spatial filtering (planned Phase 1.3.1)

**Issue 3: Limited Symbol Library**
- Current: 1 template (north arrow only)
- Target: 10+ templates for common ESC symbols

---

## Phase 3 Objectives (Remaining Work)

### Objective 1: Expand Symbol Detection Capabilities

**Goal:** Detect standard ESC symbols beyond north arrow

**Symbols to Detect:**
1. **Block Labels** (circles with alpha character inside)
   - Method: Hough Circle Transform + OCR verification
   - Use case: Verify each lot has block label
   - Expected accuracy: 80%+

2. **Silt Fence (SF) Icon**
   - Method: Template matching
   - Use case: Verify SF barriers are shown
   - Expected accuracy: 75%+

3. **Sediment Control Entrance (SCE) Icon**
   - Method: Template matching
   - Use case: Critical item - must detect accurately
   - Expected accuracy: 85%+

4. **Concrete Washout (CONC WASH) Icon**
   - Method: Template matching + text proximity
   - Use case: Critical item - must detect accurately
   - Expected accuracy: 85%+

5. **North Arrow** (enhancement)
   - Current: 12.3% confidence
   - Target: 85%+ confidence with multi-scale matching

---

### Objective 2: Implement Hough Circle Transform

**Goal:** Detect circular block labels and verify lot labeling

**Approach:**

```python
def detect_block_labels(
    image: np.ndarray,
    min_radius: int = 20,
    max_radius: int = 60,
    verify_with_ocr: bool = True
) -> List[Tuple[int, int, int, str]]:
    """
    Detect circular block labels on subdivision plans.

    Block labels are typically:
    - Circles or rounded rectangles
    - Contain single alpha character (A, B, C, ...)
    - Located near lot numbers
    - Size: 40-120 pixels diameter at 150 DPI

    Args:
        image: Input image (grayscale or BGR)
        min_radius: Minimum circle radius in pixels (default: 20)
        max_radius: Maximum circle radius in pixels (default: 60)
        verify_with_ocr: If True, verify alpha character inside circle

    Returns:
        List of (x, y, radius, letter) tuples
        Example: [(1500, 2000, 45, 'A'), (1600, 2100, 42, 'B')]
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Edge detection
    edges = cv2.Canny(gray, 50, 150)

    # Detect circles using Hough Circle Transform
    circles = cv2.HoughCircles(
        edges,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=100,  # Circles should be well-separated
        param1=50,    # Canny edge threshold
        param2=30,    # Circle detection threshold
        minRadius=min_radius,
        maxRadius=max_radius
    )

    if circles is None:
        logger.debug("No circles detected")
        return []

    circles = np.uint16(np.around(circles))
    block_labels = []

    # Verify each circle
    for circle in circles[0, :]:
        x, y, r = circle

        if verify_with_ocr:
            # Extract circle region
            roi = gray[max(0, y-r):min(gray.shape[0], y+r),
                      max(0, x-r):min(gray.shape[1], x+r)]

            # OCR to find alpha character
            text = pytesseract.image_to_string(
                roi,
                config='--psm 10'  # Single character mode
            ).strip()

            # Verify it's a single alpha character
            if len(text) == 1 and text.isalpha():
                block_labels.append((x, y, r, text.upper()))
                logger.debug(f"Block label '{text}' detected at ({x}, {y})")
            else:
                logger.debug(f"Circle at ({x}, {y}) rejected: text='{text}'")
        else:
            # Accept circle without verification
            block_labels.append((x, y, r, '?'))

    logger.info(f"Detected {len(block_labels)} block labels")
    return block_labels
```

**Integration:**

```python
# In validator.py, add block label detection
block_labels = detect_block_labels(preprocessed_image)

# Verify coverage
detection_results["block_labels"] = DetectionResult(
    element="block_labels",
    detected=len(block_labels) > 0,
    confidence=0.85 if len(block_labels) > 0 else 0.0,
    count=len(block_labels),
    matches=[label[3] for label in block_labels],
    notes=f"Found {len(block_labels)} block label(s): {', '.join([l[3] for l in block_labels])}"
)
```

**Time Estimate:** 1 day

---

### Objective 3: Build Comprehensive Symbol Template Library

**Goal:** Create library of 10+ ESC symbol templates for template matching

**Template Extraction Process:**

1. **Source:** Christian's actual ESC sheets
2. **Method:**
   - Extract symbol from high-res PDF (300 DPI)
   - Crop to ~100x100 pixels (symbol-only, minimal background)
   - Convert to grayscale
   - Clean up artifacts (optional thresholding)
   - Save as PNG

3. **Templates to Create:**

| Symbol | Priority | Source Sheet | Expected Size | Notes |
|--------|----------|--------------|---------------|-------|
| North Arrow | P0 | ✅ EXISTS | 100x100 | Needs improvement |
| Block Label Circle | P1 | Various | 60x60 | Use Hough instead |
| Silt Fence (SF) | P1 | ESC sheets | 80x80 | Zigzag line pattern |
| SCE Icon | P0 | ESC sheets | 100x100 | Critical item |
| CONC WASH Icon | P0 | ESC sheets | 120x120 | Critical item |
| Inlet Symbol | P2 | Drainage sheets | 60x60 | Future enhancement |
| Catch Basin | P2 | Drainage sheets | 60x60 | Future enhancement |
| Manhole | P2 | Drainage sheets | 50x50 | Future enhancement |
| Tree Symbol | P3 | Landscape sheets | 40x40 | Low priority |
| Fire Hydrant | P3 | Utility sheets | 50x50 | Low priority |

**Template Library Structure:**

```
tools/esc-validator/templates/
├── README.md                    # Template documentation
├── north_arrow.png              # ✅ EXISTS
├── block_label_circle.png       # TODO (or use Hough)
├── silt_fence_icon.png          # TODO - P1
├── sce_icon.png                 # TODO - P0 (critical)
├── conc_wash_icon.png           # TODO - P0 (critical)
├── inlet_symbol.png             # TODO - P2
├── catch_basin.png              # TODO - P2
├── manhole_symbol.png           # TODO - P2
└── variations/                  # Different styles of same symbol
    ├── north_arrow_v2.png
    ├── north_arrow_v3.png
    └── ...
```

**Template README Documentation:**

```markdown
# ESC Validator Template Library

## Template Specifications

### North Arrow
- **File:** `north_arrow.png`
- **Size:** 100x100 pixels
- **Source:** Page 16, Entrada East ESC sheet
- **Rotation:** Template matching is rotation-invariant
- **Scale:** Requires multi-scale matching (0.3x to 2.0x)
- **Accuracy:** 12.3% (needs improvement - see Phase 1.3.1)

### SCE Icon (Sediment Control Entrance)
- **File:** `sce_icon.png`
- **Size:** 100x100 pixels
- **Source:** [To be extracted from Christian's ESC sheets]
- **Critical:** Yes - must detect with >85% accuracy
- **Typical location:** Entry points to construction site

### CONC WASH Icon (Concrete Washout)
- **File:** `conc_wash_icon.png`
- **Size:** 120x120 pixels
- **Source:** [To be extracted]
- **Critical:** Yes - must detect with >85% accuracy
- **Typical location:** Designated washout areas

## Creating New Templates

1. Open ESC sheet PDF in image editor at 300 DPI
2. Locate clear instance of symbol (no overlapping elements)
3. Crop to symbol bounds + 10 pixel margin
4. Resize to target size (maintain aspect ratio)
5. Convert to grayscale
6. Apply threshold if needed: `cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)`
7. Save as PNG with descriptive name
8. Update this README with template metadata

## Template Matching Parameters

Default parameters for `detect_symbol_multiscale()`:
- **Scales:** 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2.0
- **Rotations:** 0°, ±15°, ±30°, ±45°
- **Method:** `cv2.TM_CCOEFF_NORMED`
- **Threshold:** 0.6 (60% match confidence)

Adjust per symbol in `config/symbol_config.json`.
```

**Time Estimate:** 2 days (extraction + documentation)

---

### Objective 4: Implement Multi-Scale Template Matching

**Goal:** Improve north arrow and enable robust symbol detection

**Note:** Detailed implementation plan exists in Phase 1.3.1 PLAN.md (lines 96-180). Summary:

**Key Features:**
- Try template at 11 different scales (0.3x to 2.0x)
- Try 7 rotation angles (0°, ±15°, ±30°, ±45°)
- Use `cv2.TM_CCOEFF_NORMED` (normalized correlation)
- Return best match above threshold (default: 0.6)

**Implementation:**

```python
def detect_symbol_multiscale(
    image: np.ndarray,
    template_path: Path,
    scales: tuple = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2.0),
    rotation_angles: tuple = (0, 15, 30, 45, -15, -30, -45),
    threshold: float = 0.6
) -> Tuple[bool, float, Optional[Tuple[int, int]]]:
    """
    Multi-scale, multi-rotation template matching.

    Generic implementation for any symbol template.
    See Phase 1.3.1 PLAN.md for full implementation.
    """
    # [Implementation as detailed in Phase 1.3.1]
    pass
```

**Wrapper for Specific Symbols:**

```python
def detect_sce_icon(image: np.ndarray) -> Tuple[bool, float, Optional[Tuple[int, int]]]:
    """Detect Sediment Control Entrance icon."""
    template_path = TEMPLATE_DIR / "sce_icon.png"
    return detect_symbol_multiscale(
        image,
        template_path,
        threshold=0.7  # Higher threshold for critical item
    )

def detect_conc_wash_icon(image: np.ndarray) -> Tuple[bool, float, Optional[Tuple[int, int]]]:
    """Detect Concrete Washout icon."""
    template_path = TEMPLATE_DIR / "conc_wash_icon.png"
    return detect_symbol_multiscale(
        image,
        template_path,
        threshold=0.7  # Higher threshold for critical item
    )
```

**Expected Improvement:**
- North arrow: 12.3% → **75-95%** confidence
- New symbols: **75-85%** accuracy on first implementation

**Time Estimate:** Included in Phase 1.3.1 (already planned), ~1 day

---

## Implementation Plan

### Task 1: Extract Critical Symbol Templates

**Priority:** P0 (Blocking for validation accuracy)

**Steps:**
1. Identify best source sheets for SCE and CONC WASH icons
2. Extract templates at 300 DPI
3. Clean and format as grayscale PNG
4. Test with existing `detect_north_arrow()` to verify quality
5. Document in `templates/README.md`

**Deliverables:**
- `templates/sce_icon.png`
- `templates/conc_wash_icon.png`
- `templates/silt_fence_icon.png`
- Updated `templates/README.md`

**Time:** 4 hours

---

### Task 2: Implement Hough Circle Detection for Block Labels

**Priority:** P1 (High value, common requirement)

**Steps:**
1. Implement `detect_block_labels()` in `symbol_detector.py`
2. Add OCR verification for alpha character
3. Create helper function `verify_block_label_coverage()`:
   - Calculate expected blocks from subdivision layout
   - Verify each lot has block label
   - Report missing labels
4. Integrate with validator
5. Add CLI flag `--detect-block-labels`
6. Create test cases with known block labels

**Deliverables:**
- `detect_block_labels()` function
- `verify_block_label_coverage()` function
- Integration in `validator.py`
- Test suite in `test_phase_3.py`

**Time:** 1 day

---

### Task 3: Implement Generic Symbol Detection

**Priority:** P1 (Enables template library)

**Steps:**
1. Refactor Phase 1.3.1's `detect_north_arrow_multiscale()` to generic `detect_symbol_multiscale()`
2. Create symbol-specific wrappers:
   - `detect_north_arrow()`
   - `detect_sce_icon()`
   - `detect_conc_wash_icon()`
   - `detect_silt_fence_icon()`
3. Add symbol configuration support (per-symbol thresholds)
4. Update validator to use new functions
5. Performance optimization (search only relevant regions)

**Deliverables:**
- `detect_symbol_multiscale()` generic function
- Symbol-specific wrapper functions
- Configuration file `config/symbol_config.json`
- Performance benchmarks

**Time:** 1.5 days

---

### Task 4: Expand Template Library

**Priority:** P2 (Nice-to-have for completeness)

**Steps:**
1. Extract remaining symbols from Christian's sheets:
   - Inlet symbols
   - Catch basins
   - Manholes
   - Tree symbols (if needed)
2. Create variation templates for common symbols:
   - Multiple north arrow styles
   - Different SCE icon designs
3. Document each template in README
4. Create template validation script (ensure templates are usable)

**Deliverables:**
- 10+ symbol templates
- Template variation library
- `validate_template.py` script
- Comprehensive `templates/README.md`

**Time:** 1 day

---

### Task 5: Integration & Testing

**Priority:** P0 (Must validate before production)

**Steps:**
1. Update `detect_required_labels()` to include new symbols
2. Update reporter to display symbol detection results
3. Create comprehensive test suite:
   - Test each symbol type individually
   - Test on sheets with multiple symbols
   - Test on sheets with no symbols (false positive check)
   - Performance benchmarks (<45 seconds)
4. Accuracy validation on 5-10 real ESC sheets
5. Documentation updates

**Deliverables:**
- `test_phase_3.py` - Comprehensive test suite
- `PHASE_3_IMPLEMENTATION.md` - Technical documentation
- `PHASE_3_TEST_REPORT.md` - Accuracy metrics
- Updated `README.md` and user documentation

**Time:** 2 days

---

## Success Criteria

Phase 3 is **COMPLETE** when:

### Must Have (P0):
- ✅ North arrow detection: **75%+** accuracy (multi-scale)
- ✅ SCE icon detection: **85%+** accuracy
- ✅ CONC WASH icon detection: **85%+** accuracy
- ✅ Template library: **5+ symbols**
- ✅ Generic symbol detection framework working
- ✅ Integration with validator complete
- ✅ Processing time: **<45 seconds** per sheet

### Should Have (P1):
- ✅ Block label detection: **80%+** accuracy
- ✅ Silt fence icon detection: **75%+** accuracy
- ✅ Template library: **8+ symbols**
- ✅ Symbol variation support (multiple templates per symbol type)
- ✅ Per-symbol configuration (thresholds, scales)

### Nice to Have (P2):
- ✅ Template library: **10+ symbols**
- ✅ Drainage symbols (inlets, catch basins, manholes)
- ✅ Template validation tooling
- ✅ Debug visualization for all symbol types

---

## Expected Results

### Before Phase 3:
```
North Arrow: ✓ Detected
  Confidence: 12.3%
  Method: ORB feature matching
  Notes: "Low confidence - needs improvement"

Block Labels: ✗ Not detected
  Notes: "Symbol detection not implemented"

SCE Icon: ✗ Not detected
  Notes: "Manual verification required"

CONC WASH: ✗ Not detected
  Notes: "Manual verification required"
```

### After Phase 3:
```
North Arrow: ✓ Detected
  Confidence: 87%
  Location: (9500, 800)
  Method: Multi-scale template matching
  Scale: 1.2x, Rotation: 0°
  Notes: "Symbol detected successfully"

Block Labels: ✓ 3 detected
  Confidence: 82%
  Labels: A, B, C
  Coverage: 100% (3/3 lots labeled)
  Notes: "All lots have block labels"

SCE Icon: ✓ 2 detected
  Confidence: 89%, 85%
  Locations: (2500, 3200), (4100, 1800)
  Notes: "SCE at north and south entrances"

CONC WASH: ✓ 1 detected
  Confidence: 91%
  Location: (1200, 4500)
  Notes: "Concrete washout area designated"

Silt Fence: ✓ Detected
  Confidence: 78%
  Length: ~450 ft perimeter
  Notes: "SF barriers along south boundary"
```

---

## Timeline

**Week 1:**
- **Mon:** Extract critical templates (SCE, CONC WASH, SF)
- **Tue:** Implement Hough circle detection for block labels
- **Wed:** Test block label detection, iterate
- **Thu:** Refactor to generic symbol detection framework
- **Fri:** Implement symbol-specific wrappers

**Week 2:**
- **Mon:** Extract remaining templates (drainage, etc.)
- **Tue:** Create template variations library
- **Wed:** Integration with validator
- **Thu:** Comprehensive testing and accuracy validation
- **Fri:** Documentation and final review

**Total:** 10 days (~2 weeks)

---

## Deliverables

### Code Files

**New Files:**
- `test_phase_3.py` - Phase 3 test suite
- `config/symbol_config.json` - Per-symbol configuration
- `validate_template.py` - Template quality validation script
- `PHASE_3_IMPLEMENTATION.md` - Technical documentation
- `PHASE_3_TEST_REPORT.md` - Accuracy benchmarks

**Modified Files:**
- `esc_validator/symbol_detector.py` - Add new detection functions
- `esc_validator/validator.py` - Integrate new symbol detection
- `esc_validator/reporter.py` - Display symbol results
- `tools/esc-validator/README.md` - Usage documentation
- `templates/README.md` - Template library documentation

### Templates

**Critical (P0):**
- `templates/sce_icon.png`
- `templates/conc_wash_icon.png`
- `templates/north_arrow.png` (✅ exists, needs multi-scale support)

**High Priority (P1):**
- `templates/silt_fence_icon.png`
- `templates/block_label_circle.png` (optional - Hough better)

**Medium Priority (P2):**
- `templates/inlet_symbol.png`
- `templates/catch_basin.png`
- `templates/manhole_symbol.png`

**Variations:**
- `templates/variations/north_arrow_v2.png`
- `templates/variations/north_arrow_v3.png`
- `templates/variations/sce_icon_v2.png`

---

## Testing Plan

### Test Case 1: North Arrow Multi-Scale Detection
**Input:** Page 16 (Entrada East ESC sheet)
**Method:** Multi-scale template matching
**Expected:** Detected=True, Confidence >75%, Location in title block area
**Validation:** Visual inspection of bounding box

### Test Case 2: Block Label Detection
**Input:** Subdivision plan sheet with 3 blocks (A, B, C)
**Method:** Hough Circle Transform + OCR
**Expected:** 3 circles detected, labels [A, B, C], 100% coverage
**Validation:** Compare to ground truth labels

### Test Case 3: SCE Icon Detection
**Input:** ESC sheet with 2 SCE icons at site entrances
**Method:** Multi-scale template matching
**Expected:** 2 detections, confidence >85% each
**Validation:** Manual verification of locations

### Test Case 4: CONC WASH Icon Detection
**Input:** ESC sheet with 1 concrete washout area
**Method:** Multi-scale template matching
**Expected:** 1 detection, confidence >85%
**Validation:** Manual verification

### Test Case 5: False Positive Test
**Input:** Notes sheet (no symbols present)
**Expected:** 0 symbols detected (no false positives)
**Validation:** Ensure high precision

### Test Case 6: Performance Benchmark
**Input:** Full ESC sheet (all symbols present)
**Method:** Full validator with Phase 3 enabled
**Expected:** Processing time <45 seconds
**Validation:** Time measurement

---

## Risk Mitigation

### Risk 1: Template Extraction Quality
**Risk:** Extracted templates may not match actual symbols on sheets
**Mitigation:**
- Extract from multiple source sheets
- Create template variations library
- Support fallback to alternate templates
- Manual template review before testing

### Risk 2: Multi-Scale Matching Performance
**Risk:** Testing 11 scales × 7 rotations = 77 matches per symbol may be slow
**Mitigation:**
- Limit search region (e.g., title block for north arrow)
- Use pyramid downsampling for coarse-to-fine search
- Parallelize template matching across symbols
- Set aggressive threshold to early-exit (0.9+ = stop searching)

### Risk 3: Symbol Variations Across Projects
**Risk:** Different drafters may use different symbol styles
**Mitigation:**
- Build template variations library
- Try all templates, use best match
- Document which templates work best for which projects
- Allow users to add custom templates

### Risk 4: OCR Accuracy for Block Labels
**Risk:** OCR may misread alpha characters in circles
**Mitigation:**
- Preprocess circle ROI (threshold, denoise)
- Use pytesseract single-character mode (`--psm 10`)
- Verify character is A-Z only
- Fall back to accepting circle without character verification

### Risk 5: False Positives on Decorative Elements
**Risk:** Title block decorations may match symbol templates
**Mitigation:**
- Use higher thresholds for critical symbols (0.7 instead of 0.6)
- Implement spatial filtering (e.g., SCE must be near site boundary)
- Cross-reference with text labels ("SCE" text near SCE icon)
- Provide confidence scores and allow user to review low-confidence detections

---

## Decision Points

### Decision 1: Hough Circle vs Template Matching for Block Labels
**Options:**
- A) Hough Circle Transform + OCR (robust to style variations)
- B) Template matching (faster, requires templates for each style)

**Recommendation:** **Option A** - Hough Circle
**Rationale:** Block labels vary too much in style (filled vs outline, different fonts). Hough Circle is more generic.

---

### Decision 2: Phase 1.3.1 vs Phase 3 Priority
**Context:** Phase 1.3.1 improves accuracy of existing features. Phase 3 adds new features.

**Recommendation:** **Complete Phase 1.3.1 first**
**Rationale:**
- Phase 1.3.1 fixes critical accuracy issues (12.3% → 75%+ for north arrow)
- Phase 1.3.1's multi-scale matching is foundational for Phase 3 templates
- Better to have 2 symbols working well than 6 symbols working poorly

---

### Decision 3: Template Library Size
**Options:**
- A) Minimum viable (5 templates: north arrow, SCE, CONC WASH, SF, block)
- B) Comprehensive (10+ templates including drainage, landscape symbols)

**Recommendation:** **Option A for Phase 3, Option B for Phase 3.1**
**Rationale:**
- Focus on ESC-specific symbols first (80/20 rule)
- Validate approach before expanding
- Drainage/landscape symbols can be Phase 3.1 enhancement

---

## Acceptance Criteria

Phase 3 is **COMPLETE** and ready for production when:

1. ✅ **Symbol Detection Accuracy:**
   - North arrow: ≥75% confidence (up from 12.3%)
   - SCE icon: ≥85% confidence
   - CONC WASH icon: ≥85% confidence
   - Block labels: ≥80% accuracy
   - Silt fence: ≥75% accuracy

2. ✅ **Template Library:**
   - Minimum 5 symbol templates
   - Templates validated on actual ESC sheets
   - Documentation complete

3. ✅ **Performance:**
   - Processing time <45 seconds per sheet
   - No regressions on Phase 1/2 features

4. ✅ **Integration:**
   - All symbols integrated in validator
   - Reporter displays symbol results
   - CLI flags for enabling/disabling symbol types

5. ✅ **Testing:**
   - Test suite with 10+ test cases
   - Accuracy validated on 5-10 real ESC sheets
   - False positive rate <5%

6. ✅ **Documentation:**
   - Implementation documentation complete
   - User guide updated
   - Template creation guide

---

## Next Steps After Phase 3

**Phase 4:** Drainage feature detection (inlets, pipes, flow arrows)
**Phase 5:** Lot boundary and area calculation
**Phase 6:** Machine learning for comprehensive symbol recognition

---

## Related Documentation

- **Phase 1.3 PLAN.md** - Original visual detection implementation
- **Phase 1.3.1 PLAN.md** - Multi-scale matching details (lines 96-180)
- **Phase 2 README.md** - Line detection (completed)
- **templates/README.md** - Template library documentation
- **symbol_detector.py** - Current implementation (863 lines)

---

## Lessons Learned from Phase 1.3

**What Worked:**
- ✅ ORB feature matching is rotation-invariant (as advertised)
- ✅ Template infrastructure is clean and extensible
- ✅ Debug visualization very helpful for tuning
- ✅ Integration with validator was straightforward

**What Needs Improvement:**
- ❌ ORB not scale-invariant (need multi-scale matching)
- ❌ Simple line detection too sensitive (need context-aware filtering)
- ❌ Need more robust template matching method
- ❌ Should extract templates from actual drawings, not generic images

**Key Insights:**
- Template quality matters more than algorithm sophistication
- Context-aware filtering is critical (streets must have labels)
- Multi-scale matching essential for production use
- Start with one high-quality template per symbol, not multiple low-quality templates

---

**Status:** ⚠️ PARTIALLY COMPLETE (60% done in Phase 1.3, 40% remains)
**Priority:** P2 (Medium - foundational work done, enhancements remain)
**Blocking Issues:** Phase 1.3.1 accuracy improvements should complete first
**Owner:** Claude (via Claude Code)
**For:** Christian's Productivity Tools - ESC Validator

---

**Created:** 2025-11-02
**Last Updated:** 2025-11-02
**Related Phases:** 1.3 (visual detection), 1.3.1 (accuracy improvements), 2 (line detection)
