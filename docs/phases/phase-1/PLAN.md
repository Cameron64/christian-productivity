# ESC Sheet Validation System - Implementation Plan

## Overview

Automated validation system for Erosion and Sediment Control (ESC) sheets in civil engineering drawing sets. This tool will automatically verify that ESC sheets contain all required elements per Austin/Travis County regulations.

**Primary User:** Christian (Civil Engineer - Subdivision Planning)
**Use Case:** Pre-submission quality control for permit applications
**Target:** 70-80% automation of manual checklist validation

---

## Required Elements Checklist (16 Items)

### Text/Label Detection (7 items)
1. ✓ Existing contours labeled (dashed lines)
2. ✓ Proposed contours labeled (solid lines)
3. ✓ Lot and block labeled (block = alpha in circle, lot = number)
4. ✓ Streets labeled
5. ✓ Legend present
6. ✓ Scale present
7. ✓ North bar present

### Feature Detection (5 items)
8. ✓ Limits of construction (LOC - dashed perimeter line)
9. ✓ Silt fence (SF with dashed line)
10. ✓ Stabilized construction entrance (SCE - at least 1)
11. ✓ Concrete washout (CONC WASH - at least 1)
12. ✓ Staging/spoils area (near entrance)

### Quality Checks (4 items)
13. ✓ Legend matches line types shown
14. ✓ No overlapping labels
15. ✓ Line types match descriptions (dashed vs solid)
16. ✓ Minimum quantities met (at least 1 SCE, 1 CONC WASH)

---

## Technology Stack

### Core Tools (Already Installed)
- **pdfplumber** - PDF extraction
- **Pillow/PIL** - Image processing
- **pytesseract** - OCR for text detection
- **pandas** - Data analysis

### New Dependencies Required
```bash
pip install opencv-python opencv-contrib-python
pip install python-Levenshtein
pip install matplotlib
```

### Optional (Phase 6 - Advanced ML)
```bash
pip install ultralytics      # YOLOv8
pip install paddleocr         # Better OCR for engineering drawings
pip install torch torchvision # PyTorch
```

---

## Implementation Phases

### PHASE 1: Basic Text Detection (Week 1-2)
**Goal:** Detect presence of required text labels
**Expected Accuracy:** 75-85%
**Confidence:** High

#### Deliverables:
1. PDF extraction and preprocessing
   - Extract ESC sheet from drawing set
   - Convert to high-res image (300 DPI)
   - Enhance contrast for better OCR

2. OCR-based text detection
   - Detect: Legend, Scale, North Bar
   - Detect: LOC, SF, SCE, CONC WASH labels
   - Detect: Street names
   - Detect: Staging/spoils area text

3. Count verification
   - Verify at least 1 SCE
   - Verify at least 1 CONC WASH
   - Count all detected instances

**Code Structure:**
```python
def extract_esc_sheet(pdf_path, sheet_name="ESC"):
    """Extract ESC sheet and convert to enhanced image"""
    # Convert PDF page to high-res image
    # Apply preprocessing (grayscale, contrast enhancement)
    return image, page_number

def detect_required_labels(image):
    """Run OCR and check for required text elements"""
    # Run pytesseract OCR
    # Search for required keywords with fuzzy matching
    return checklist_results

def verify_minimum_quantities(all_text):
    """Ensure at least 1 of each required feature"""
    # Count occurrences of SCE, CONC WASH
    return quantity_results
```

**Testing Strategy:**
- Test on 5-10 real ESC sheets from Christian's projects
- Measure precision/recall for each element
- Identify failure modes
- Decide: continue to Phase 2 or jump to Phase 6 (ML)

---

### PHASE 2: Line Type Detection (Week 2-3)
**Goal:** Detect dashed vs solid lines, verify contour labels
**Expected Accuracy:** 70-80%
**Confidence:** Medium

#### Deliverables:
1. Line detection with OpenCV
   - Edge detection (Canny)
   - Line detection (Hough Transform)
   - Classify lines as dashed vs solid

2. Contour label verification
   - Find contour-like patterns
   - Check for numeric labels near contours
   - Spatial analysis: label proximity to lines

**Code Structure:**
```python
def detect_line_types(image):
    """Detect and classify line types (solid vs dashed)"""
    # Canny edge detection
    # Hough line detection
    # Gap analysis to determine dashed vs solid
    return line_type_results

def verify_contour_labels(image, ocr_data):
    """Check if contour lines have numeric labels"""
    # Find contour patterns
    # Extract numeric labels from OCR
    # Spatial correlation analysis
    return contour_label_results
```

**Challenges:**
- Drawing complexity may interfere with line detection
- Overlapping elements complicate classification
- May need iterative refinement

---

### PHASE 3: Symbol & Pattern Detection (Week 3-4)
**Goal:** Detect specific symbols (circles, north arrow, etc.)
**Expected Accuracy:** 70-85%
**Confidence:** Medium-High

#### Deliverables:
1. Template matching for symbols
   - Create symbol templates from sample drawings
   - Detect north arrow
   - Detect other standard symbols

2. Block label detection
   - Detect circles using Hough Circle Transform
   - Check for single alpha character inside circle
   - Verify lot numbers (numeric labels outside circles)

**Code Structure:**
```python
def detect_symbols(image):
    """Detect standard symbols using template matching"""
    # Load symbol templates
    # Run template matching
    # Return detected symbol locations
    return symbol_results

def detect_block_labels(image, ocr_data):
    """Detect block labels (alpha character in circle)"""
    # Hough circle detection
    # Check OCR data for alpha chars near circles
    # Verify spatial relationship
    return block_label_results
```

**Requirements:**
- Create symbol template library from Christian's drawings
- May need multiple templates for variations

---

### PHASE 4: Quality Checks (Week 4-5)
**Goal:** Validate legend accuracy, detect overlapping labels
**Expected Accuracy:** 80-90%
**Confidence:** High

#### Deliverables:
1. Legend verification
   - Extract legend region from sheet
   - Analyze line types shown in legend
   - Compare to line types used in main drawing
   - Verify consistency

2. Overlapping label detection
   - Extract all text bounding boxes from OCR
   - Check for geometric overlaps
   - Report any overlapping labels

**Code Structure:**
```python
def verify_legend_matches_drawing(image, ocr_data):
    """Check if legend line types match those used in drawing"""
    # Extract legend area
    # Analyze line types in legend vs drawing
    # Compare and validate
    return legend_verification_results

def detect_overlapping_labels(ocr_data):
    """Check if any text labels overlap"""
    # Extract all bounding boxes
    # Geometric overlap detection
    return overlap_results
```

**Notes:**
- Legend location may vary between drawings
- Need heuristics to identify legend region

---

### PHASE 5: Integration & Reporting (Week 5-6)
**Goal:** Combine all checks into unified validation system
**Expected Accuracy:** 70-80% overall
**Confidence:** High

#### Deliverables:
1. Unified validation function
   - Orchestrates all phase checks
   - Aggregates results
   - Calculates overall pass/fail

2. Report generation
   - Markdown format report
   - Element-by-element checklist
   - Issues list with recommendations
   - Confidence scores for each detection

3. Batch processing
   - Process multiple drawings in one run
   - Summary statistics across projects

**Code Structure:**
```python
def validate_esc_sheet(pdf_path, sheet_name="ESC"):
    """Complete ESC sheet validation"""
    # Extract and preprocess
    # Run all phase checks
    # Aggregate results
    # Calculate pass/fail
    return complete_results

def generate_validation_report(results, output_format="markdown"):
    """Generate human-readable validation report"""
    # Format checklist with pass/fail indicators
    # List all detected issues
    # Include confidence scores
    # Add recommendations
    return formatted_report
```

**CLI Interface:**
```bash
# Single sheet validation
python validate_esc.py "5620-01 Entrada East.pdf" --output report.md

# Batch processing
python validate_esc.py documents/*.pdf --batch --output-dir reports/

# Verbose mode with visual overlay
python validate_esc.py "drawing.pdf" --verbose --annotate --output annotated.pdf
```

**Report Format:**
```markdown
# ESC Validation Report

**Sheet:** ESC Plan
**Page:** 15
**Status:** ⚠️ NEEDS REVIEW (11/16 checks passed)

## Required Elements

| Element | Status | Notes |
|---------|--------|-------|
| Legend | ✅ | Found at bottom of sheet |
| Scale | ✅ | 1"=50' |
| North Bar | ✅ | Detected in upper right |
| SCE | ✅ | 2 locations found (need ≥1) |
| Concrete Washout | ❌ | NOT DETECTED - manual review needed |
| ... | ... | ... |

## Issues Found

1. ⚠️ **Concrete washout label not detected**
   - Expected: "CONC WASH" or similar
   - Recommendation: Verify presence manually or add clear label

2. ⚠️ **Low confidence on contour labels**
   - Found 8 numeric labels near contour lines
   - Manual verification recommended

## Confidence Scores

- Text Detection: 85%
- Line Type Detection: 72%
- Symbol Detection: 78%
- Overall: 75%
```

---

### PHASE 6: Advanced ML (Optional - Week 7+)
**Goal:** Improve accuracy to 90%+ using machine learning
**Expected Accuracy:** 85-95%
**Confidence:** High (if properly trained)

**Only pursue if Phase 1-5 accuracy is insufficient (<70%)**

#### Option A: Custom Object Detector (YOLOv8)
**Use Case:** Detect specific symbols and features

**Requirements:**
- Annotate 50-100 ESC sheets with bounding boxes
- Label all symbols: SF, SCE, CONC WASH, blocks, north arrows
- Train YOLOv8 model
- 2-4 hours GPU training time

**Expected Improvement:**
- Symbol detection: 70-85% → 90-95%
- Feature detection: 80-90% → 92-97%

**Tools:**
- LabelImg or Roboflow for annotation
- YOLOv8 (ultralytics library)
- GPU recommended (can use Colab free tier)

#### Option B: Specialized OCR (PaddleOCR)
**Use Case:** Better text extraction from engineering drawings

**Benefits:**
- Handles rotated text better than Tesseract
- Better performance on technical drawings
- Multi-language support (if needed)

**Expected Improvement:**
- Text detection: 75-85% → 85-95%
- Label detection: 80-90% → 90-95%

#### Option C: Semantic Segmentation (U-Net)
**Use Case:** Pixel-level line type classification

**Requirements:**
- Annotate line types at pixel level
- Train U-Net model for segmentation
- Classify each pixel as: background, solid line, dashed line, text, symbol

**Expected Improvement:**
- Line type detection: 70-80% → 90-95%
- Contour separation: 60-70% → 85-90%

**Decision Point:**
Evaluate Phase 1-5 results before investing in ML approach.

---

## Expected Accuracy Summary

| Phase | Elements Covered | Expected Accuracy | Confidence |
|-------|-----------------|-------------------|------------|
| **Phase 1** | Text labels (legend, scale, north, streets) | 75-85% | High |
| **Phase 1** | Feature mentions (LOC, SF, SCE, CONC WASH) | 80-90% | High |
| **Phase 1** | Minimum quantities | 85-95% | High |
| **Phase 2** | Line type detection | 70-80% | Medium |
| **Phase 2** | Contour label verification | 60-70% | Medium-Low |
| **Phase 3** | Block labels (circle + alpha) | 70-85% | Medium-High |
| **Phase 3** | Symbol detection (north arrow) | 75-90% | High |
| **Phase 4** | Legend matching | 65-75% | Medium |
| **Phase 4** | Overlapping labels | 85-95% | High |
| **Phase 6** | All elements (with ML) | 85-95% | High |

**Overall System Accuracy:**
- Phase 1-5: 70-80%
- Phase 6: 85-95%

---

## Implementation Strategy

### Week 1: Rapid Prototype
**Goal:** Build Phase 1 (text detection) and validate approach

**Tasks:**
1. Set up development environment
2. Install dependencies (opencv, tesseract)
3. Build PDF extraction function
4. Implement basic OCR text detection
5. Test on 5-10 real ESC sheets from Christian's projects

**Success Criteria:**
- Can extract ESC sheet from drawing set
- Can detect at least 8/16 checklist items
- Accuracy >60% on text-based elements

**Decision Point:**
- If accuracy >70%: Continue to Phase 2
- If accuracy 50-70%: Refine Phase 1, consider better preprocessing
- If accuracy <50%: Jump to Phase 6 (ML approach)

### Week 2-3: Iterate Based on Results
**Goal:** Expand capabilities based on Phase 1 performance

**If Phase 1 successful (>70%):**
- Implement Phase 2 (line detection)
- Implement Phase 3 (symbol detection)
- Test integrated system

**If Phase 1 marginal (50-70%):**
- Improve preprocessing techniques
- Try PaddleOCR instead of Tesseract
- Optimize OCR parameters
- Re-test before proceeding

**If Phase 1 poor (<50%):**
- Pivot to Phase 6 (ML approach)
- Begin annotating training data
- Set up YOLOv8 training pipeline

### Week 4-5: Production Hardening
**Goal:** Make tool production-ready

**Tasks:**
1. Error handling and edge cases
2. Batch processing capability
3. Report generation
4. CLI interface
5. Documentation
6. Integration with existing PDF tools

**Deliverables:**
- Command-line tool
- User documentation
- Sample reports
- Test suite

### Week 6+: Optional Advanced Features
**Goal:** Enhance accuracy if needed

**Potential Enhancements:**
- ML-based detection (YOLOv8)
- Visual annotation overlay
- CAD plugin integration
- Web interface
- Real-time validation during design

---

## File Structure

```
christian-productivity/
├── PLAN.md                          # This file
├── CLAUDE.md                        # Project overview for Claude
├── README.md                        # User-facing documentation
├── requirements.txt                 # Python dependencies
│
├── docs/
│   └── subdivision-code/            # Existing code references
│
├── tools/
│   └── esc-validator/               # ESC validation tool (NEW)
│       ├── README.md                # Tool documentation
│       ├── requirements.txt         # Tool-specific dependencies
│       ├── validate_esc.py          # Main CLI tool
│       ├── esc_validator/           # Python package
│       │   ├── __init__.py
│       │   ├── extractor.py         # PDF extraction (Phase 1)
│       │   ├── text_detector.py     # OCR-based detection (Phase 1)
│       │   ├── line_detector.py     # Line type detection (Phase 2)
│       │   ├── symbol_detector.py   # Symbol detection (Phase 3)
│       │   ├── quality_checker.py   # Quality checks (Phase 4)
│       │   ├── validator.py         # Integration (Phase 5)
│       │   ├── reporter.py          # Report generation (Phase 5)
│       │   └── ml_detector.py       # ML models (Phase 6, optional)
│       │
│       ├── templates/               # Symbol templates for matching
│       │   ├── north_arrow.png
│       │   ├── silt_fence.png
│       │   └── ...
│       │
│       ├── models/                  # Trained ML models (Phase 6)
│       │   └── yolov8_esc.pt
│       │
│       └── tests/                   # Test suite
│           ├── test_extractor.py
│           ├── test_detector.py
│           └── sample_sheets/       # Test ESC sheets
│
├── scripts/                         # Existing utility scripts
│   ├── extract_page29.py
│   ├── search_koti_fast.py
│   └── ...
│
└── documents/                       # Drawing sets and PDFs
    └── 5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf
```

---

## Testing Strategy

### Unit Tests
Test each component independently:
- PDF extraction accuracy
- OCR text detection precision/recall
- Line type classification accuracy
- Symbol detection accuracy
- Report generation correctness

### Integration Tests
Test complete workflow:
- End-to-end validation on sample sheets
- Batch processing on multiple sheets
- Error handling for malformed PDFs
- Performance benchmarks

### Validation Dataset
**Minimum:** 10 ESC sheets from Christian's projects
**Ideal:** 30-50 ESC sheets covering:
- Different projects
- Different drafters (varying styles)
- Different scales
- Different complexity levels

**Ground Truth:**
- Manually annotate all 16 checklist items
- Mark each element as present/absent
- Note any ambiguous cases
- Use for accuracy measurement

### Metrics
- **Precision:** Of detected elements, how many are correct?
- **Recall:** Of required elements, how many did we detect?
- **F1 Score:** Harmonic mean of precision and recall
- **False Positive Rate:** How often do we incorrectly flag issues?
- **False Negative Rate:** How often do we miss actual issues?

**Acceptable Thresholds:**
- Phase 1-5: 70% F1 score minimum
- Phase 6: 85% F1 score target

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OCR accuracy too low on drawings | Medium | High | Use PaddleOCR, improve preprocessing, or jump to ML |
| Line detection fails due to complexity | Medium | Medium | Focus on text-based checks first, defer line detection |
| Drawing format variations break tool | High | Medium | Test on diverse samples, build robust parsing |
| Symbol templates don't match all drawings | Medium | Low | Collect templates from multiple sources |
| Training data insufficient for ML | Low | High | Only pursue ML if we can get 50+ annotated samples |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| False negatives (missing actual issues) | Medium | High | Set conservative thresholds, require manual review |
| False positives (flagging non-issues) | Medium | Medium | Include confidence scores, allow overrides |
| Tool becomes maintenance burden | Low | Medium | Keep codebase simple, avoid over-engineering |
| Christian's workflow changes | Low | Low | Build modular system, easy to adapt |

### Success Criteria

**Minimum Success:**
- Automates 60% of checklist validation
- Reduces review time by 30%
- Zero false negatives on critical items (SCE, CONC WASH)

**Target Success:**
- Automates 80% of checklist validation
- Reduces review time by 50%
- <10% false positive rate

**Stretch Success:**
- Automates 90%+ of checklist validation
- Reduces review time by 70%
- Integrates into CAD workflow for real-time validation

---

## Timeline Summary

| Week | Phase | Milestone |
|------|-------|-----------|
| 1 | Phase 1 | Working text detection prototype |
| 2 | Phase 2 | Line type detection implemented |
| 3 | Phase 3 | Symbol detection working |
| 4 | Phase 4 | Quality checks complete |
| 5 | Phase 5 | Production-ready tool with CLI |
| 6 | Testing | Validation on real projects |
| 7+ | Phase 6 | ML enhancements (if needed) |

**Total Estimated Time:**
- Basic system (Phase 1-5): 5-6 weeks
- With ML (Phase 6): 7-10 weeks

---

## Future Enhancements

### Phase 7: Web Interface (Optional)
- Upload PDF via browser
- Real-time validation
- Interactive report with clickable elements
- Share reports via URL

### Phase 8: CAD Integration (Optional)
- Plugin for AutoCAD Civil 3D
- Real-time validation during design
- Auto-flag missing elements
- Suggest corrections

### Phase 9: Multi-Sheet Validation (Optional)
- Validate entire drawing set consistency
- Check cross-references between sheets
- Verify plan/profile alignment
- Validate calculations

### Phase 10: Intelligent Assistance (Optional)
- AI suggests where to place missing elements
- Auto-generate checklists for specific project types
- Learn from corrections over time
- Predict common issues by project phase

---

## Related Documents

- [Austin Code References](docs/subdivision-code/README.md) - Regulatory requirements
- [PDF Processing Pro Skill](.claude/skills/pdf-processing-pro/skill.md) - PDF extraction toolkit
- [Quick Reference Guide](docs/subdivision-code/quick-reference.md) - Common code lookups

---

## Project Status

**Current Phase:** Planning Complete
**Next Action:** Create CLAUDE.md project overview
**Decision Needed:** Start with Phase 1 prototype or gather sample sheets first?

**Stakeholder:** Christian (Civil Engineer)
**Created:** 2025-11-01
**Last Updated:** 2025-11-01
