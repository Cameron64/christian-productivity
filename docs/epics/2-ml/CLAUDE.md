# Epic 2: ML/AI Enhancements - AI Assistant Guide

**For:** AI Assistants (Claude) working on ML enhancements for ESC Validator
**Purpose:** Understand ML architecture, implementation priorities, and integration strategy
**Last Updated:** 2025-11-02
**Status:** Planning/Architecture phase

---

## Quick Start

**New to this epic?** Read in this order:
1. **This file (CLAUDE.md)** - Overview and navigation
2. **[ML_ARCHITECTURE_ANALYSIS.md](ML_ARCHITECTURE_ANALYSIS.md)** - Detailed ML architecture
3. **[Epic 1 phases](../1-initial-implementation/phases/)** - Understand current rule-based implementation

**Key Context:**
- Epic 1 achieved 75-85% accuracy with rule-based CV
- Current bottleneck: 52s processing time (2x OCR passes)
- Main challenges: OCR noise, performance, false positives

---

## Epic Overview

### Mission
Integrate targeted ML/AI components to improve ESC Validator performance, accuracy, and user experience while maintaining the proven rule-based foundation.

### Philosophy
**Hybrid approach** - Use ML where it provides clear value, keep rule-based logic where it works well.

### Success Criteria
- Processing time: 52s → **<20s** (60%+ reduction)
- False positive rate: ~30% → **<10%** (70% reduction)
- OCR accuracy: 75-85% → **80-90%** (improvement)
- Implementation time: **10-14 hours** for Phase 4.1 + 4.2

---

## Epic Structure

```
docs/epics/2-ml/
├── CLAUDE.md                          # This file - AI assistant guide
├── ML_ARCHITECTURE_ANALYSIS.md        # High-level architecture (READ THIS!)
├── IMPLEMENTATION_PLAN.md             # Detailed implementation plan (READ THIS!)
│
└── phases/                            # ML enhancement phases
    ├── phase-4.1/                     # PaddleOCR integration
    │   ├── PLAN.md                    # Implementation plan ✅ CREATED
    │   ├── IMPLEMENTATION.md          # Technical details (after coding)
    │   └── TEST_REPORT.md             # Results (after testing)
    ├── phase-4.2/                     # Random Forest overlap filter
    │   ├── PLAN.md                    # Implementation plan ✅ CREATED
    │   └── ... (future)
    └── phase-4.3/                     # YOLO symbol detection (optional/deferred)
        └── ... (if pursued)
```

---

## Current State (v0.3.0)

### What Works (Epic 1)
- ✅ **Text detection:** 75-85% accuracy (Tesseract OCR)
- ✅ **Line detection:** 70-80% accuracy (Hough Transform)
- ✅ **Spatial filtering:** 99% false positive reduction
- ✅ **Quality checks:** Overlap detection, spatial validation
- ✅ **Processing time:** 14s (without quality checks), 52.7s (with quality checks)

### What Needs Improvement
- ⚠️ **Performance:** 52.7s processing time (running OCR 2x)
- ⚠️ **OCR noise:** Many false overlaps are artifacts (single chars, special chars)
- ⚠️ **OCR accuracy:** Tesseract struggles with complex backgrounds
- ⚠️ **Symbol detection:** Phase 3 deferred (template matching unreliable)

---

## ML Components: Priority & ROI

### Phase 4.1: PaddleOCR Integration ⭐ HIGHEST PRIORITY

**Problem:** Performance bottleneck (dual OCR passes), OCR quality
**Solution:** Replace Tesseract with PaddleOCR (deep learning OCR)

**Expected Impact:**
- Single OCR pass (not 2x)
- Better bounding boxes (fewer artifacts)
- **Processing time: 52s → 15-20s** (3x improvement!)

**Implementation:**
- Effort: 4-6 hours
- Training required: None (pre-trained model)
- Dependencies: PaddleOCR (200MB)
- Risk: Low

**When to Start:** Immediately after user approval

---

### Phase 4.2: Random Forest Overlap Filter ⭐ HIGH PRIORITY

**Problem:** OCR noise in overlap detection (false positives)
**Solution:** ML classifier to distinguish real overlaps from OCR artifacts

**Expected Impact:**
- Filter single-char and special-char overlaps
- **False positives: ~30% → <10%** (70% reduction)

**Implementation:**
- Effort: 6-8 hours
- Training required: Yes (200-300 examples, 1 hour training)
- Dependencies: scikit-learn (already installed)
- Risk: Low

**When to Start:** After Phase 4.1 completes

---

### Phase 4.3: YOLOv8 Symbol Detection 🔵 LOW PRIORITY (OPTIONAL)

**Problem:** North arrow, scale bar detection (Phase 3 deferred)
**Solution:** Object detection model (YOLO) for civil engineering symbols

**Expected Impact:**
- 95%+ detection accuracy (rotation-invariant)
- Solves Phase 3 template matching issues

**Implementation:**
- Effort: 2-3 weeks
- Training required: Yes (100-200 annotated images)
- Dependencies: Ultralytics YOLO (6-50MB model)
- Risk: Medium

**When to Start:** Only if ROI becomes positive (currently 6 min/year savings)

---

## Technology Stack

### OCR Engines

| Technology | Use Case | Pros | Cons | Recommendation |
|------------|----------|------|------|----------------|
| **PaddleOCR** | Primary OCR | Fast (100-200ms GPU), accurate, better bboxes | 200MB dependency | ⭐ **Use for Phase 4.1** |
| **EasyOCR** | Alternative OCR | Easy to use, 80+ languages | Slower, 500MB models | Backup option |
| **Tesseract 5.x** | Fallback OCR | Already integrated, lightweight | Lower accuracy, artifacts | Keep as fallback |

**Decision:** PaddleOCR for Phase 4.1

---

### Machine Learning

| Technology | Use Case | Pros | Cons | Recommendation |
|------------|----------|------|------|----------------|
| **Random Forest** | Overlap filter | Fast (<1ms), interpretable, small model | Requires labeled data | ⭐ **Use for Phase 4.2** |
| **Logistic Regression** | Alternative filter | Very fast, simple | Lower accuracy | Backup option |
| **Small Neural Net** | Advanced filter | Non-linear patterns | Less interpretable | Only if RF insufficient |

**Decision:** Random Forest for Phase 4.2

---

### Object Detection

| Technology | Use Case | Pros | Cons | Recommendation |
|------------|----------|------|------|----------------|
| **YOLOv8** | Symbol detection | 95%+ accuracy, fast (20-50ms GPU) | Requires training data | ⭐ **Use if Phase 4.3 needed** |
| **Faster R-CNN** | Alternative detector | Slightly better accuracy | 3-5x slower than YOLO | Not recommended |
| **U-Net** | Semantic segmentation | Pixel-level classification | Slow, requires extensive annotation | Overkill for current needs |

**Decision:** YOLOv8 for Phase 4.3 (if pursued)

---

## Implementation Roadmap

### Immediate (Next 1-2 Weeks) - RECOMMENDED

**Phase 4.1: PaddleOCR Integration**
- [ ] Install PaddleOCR: `pip install paddleocr`
- [ ] Create `esc_validator/ocr_engine.py` wrapper module
- [ ] Replace Tesseract calls in `text_detector.py`
- [ ] Update bounding box parsing for PaddleOCR format
- [ ] Benchmark performance (target: <20s processing time)
- [ ] Update unit tests
- [ ] Test on 3-5 diverse ESC sheets

**Success Criteria:**
- Processing time <20 seconds
- Text detection accuracy ≥75% (no degradation)
- Bounding box quality improved (visual inspection)
- Zero breaking changes to Phase 1 API

---

**Phase 4.2: Random Forest Overlap Filter**
- [ ] Extract 300 overlap examples from test sheets
- [ ] Manually label as artifact (0) or real overlap (1)
- [ ] Extract features (overlap %, text length, confidence, etc.)
- [ ] Train Random Forest classifier (100 trees)
- [ ] Integrate into `quality_checker.py`
- [ ] Test on diverse sheets

**Success Criteria:**
- False positive rate <10%
- Precision ≥90% (correctly identify real overlaps)
- Recall ≥95% (don't miss real overlaps)
- Inference time <5ms per overlap

---

### Short-term (Next 1-3 Months)

**Production Deployment (v0.4.0 or v0.5.0)**
- [ ] Deploy PaddleOCR + Random Forest to Christian
- [ ] Monitor accuracy and performance metrics
- [ ] Collect user feedback
- [ ] Iterate based on real-world usage

**Collect Symbol Annotation Data (Background)**
- [ ] If Phase 4.3 becomes priority, start collecting drawings
- [ ] Annotate incrementally (10 sheets/week)
- [ ] Build dataset for future YOLO training

---

### Long-term (Only If Justified)

**Phase 4.3: YOLOv8 Symbol Detection**
- Only pursue if:
  - Regulatory requirement emerges
  - User feedback indicates high value
  - ROI becomes positive (>10 hours/year savings)

**Estimated effort:** 2-3 weeks
**Current ROI:** Negative (6 min/year savings)

---

## Lessons from Epic 1

### What Worked (Keep These Patterns)

1. **Geometric rules for spatial relationships** (Phase 2.1)
   - 99% accuracy with 150px proximity threshold
   - Fast, deterministic, explainable
   - **Lesson:** Keep rule-based for geometric logic

2. **Incremental development with clear success criteria** (All phases)
   - Small phases (4-6 hours each)
   - Test after each phase
   - **Lesson:** Continue phased approach for ML

3. **Know when to stop** (Phase 3)
   - 3 hours investigation → deferred
   - ROI analysis guided decision
   - **Lesson:** Apply same rigor to ML phases

4. **Comprehensive testing** (Phase 4)
   - 40 unit tests, 100% pass rate
   - Real-world validation on Entrada East
   - **Lesson:** Test ML components thoroughly

---

### What Didn't Work (Avoid These)

1. **Template matching for variable symbols** (Phase 3)
   - <60% confidence on north arrows
   - Many false positives
   - **Lesson:** Use ML (YOLO) for symbols, not templates

2. **Running same process twice** (Phase 4 performance)
   - Tesseract called 2x (Phase 1 + Phase 4)
   - 52s processing time
   - **Lesson:** Consolidate OCR into single pass

3. **Ignoring performance early** (Phase 4)
   - Focused on accuracy first
   - Performance became blocker
   - **Lesson:** Balance accuracy and speed from start

---

## Integration Strategy

### Architectural Principles

1. **Backward Compatibility**
   - Keep existing Phase 1-4 APIs unchanged
   - Add new ML components as enhancements, not replacements
   - Provide fallback to Tesseract if PaddleOCR fails

2. **Modular Design**
   - Create `esc_validator/ocr_engine.py` (OCR abstraction layer)
   - Create `esc_validator/ml_models.py` (ML model management)
   - Keep ML logic separate from rule-based logic

3. **Configuration-Driven**
   - Allow users to choose OCR engine (PaddleOCR vs Tesseract)
   - Make ML models optional (disable if performance concerns)
   - Expose thresholds and parameters in config file

---

### Code Organization

```
tools/esc-validator/
├── esc_validator/
│   ├── text_detector.py         # Phase 1 (uses ocr_engine.py)
│   ├── symbol_detector.py       # Phase 2
│   ├── quality_checker.py       # Phase 4 (uses ml_models.py)
│   ├── validator.py             # Main orchestration
│   │
│   ├── ocr_engine.py            # NEW - OCR abstraction layer
│   │   ├── PaddleOCREngine      # PaddleOCR wrapper
│   │   ├── TesseractEngine      # Tesseract wrapper (fallback)
│   │   └── choose_engine()      # Auto-select based on config
│   │
│   └── ml_models.py             # NEW - ML model management
│       ├── OverlapClassifier    # Random Forest for overlaps
│       ├── SymbolDetector       # YOLO for symbols (Phase 4.3)
│       └── load_models()        # Model loading/caching
│
├── models/                      # NEW - Trained ML models
│   ├── overlap_filter.pkl       # Random Forest model
│   ├── symbols_yolo.pt          # YOLO model (if Phase 4.3)
│   └── README.md                # Model versioning
│
└── config/
    └── ml_config.yaml           # NEW - ML configuration
        ├── ocr_engine: "paddleocr"
        ├── overlap_filter_enabled: true
        └── symbol_detector_enabled: false
```

---

## Testing Strategy

### Phase 4.1 (PaddleOCR) Testing

**Unit Tests:**
- [ ] Test OCR engine abstraction layer
- [ ] Test PaddleOCR text extraction
- [ ] Test bounding box parsing
- [ ] Test fallback to Tesseract

**Integration Tests:**
- [ ] Test Phase 1 with PaddleOCR
- [ ] Test Phase 4 with PaddleOCR
- [ ] Compare results: Tesseract vs PaddleOCR

**Performance Tests:**
- [ ] Benchmark processing time (target: <20s)
- [ ] Test at 150 DPI, 200 DPI, 300 DPI
- [ ] Memory usage profiling

**Real-world Validation:**
- [ ] Test on Entrada East page 26 (baseline)
- [ ] Test on 5-10 diverse ESC sheets
- [ ] Measure accuracy vs Tesseract

---

### Phase 4.2 (Random Forest) Testing

**Unit Tests:**
- [ ] Test feature extraction
- [ ] Test classifier prediction
- [ ] Test model loading/caching
- [ ] Test edge cases (empty text, special chars)

**Integration Tests:**
- [ ] Test integration with quality_checker.py
- [ ] Test end-to-end with real overlaps
- [ ] Compare filtered vs unfiltered overlaps

**Model Validation:**
- [ ] Cross-validation (5-fold)
- [ ] Precision, recall, F1 score
- [ ] Confusion matrix analysis
- [ ] Feature importance analysis

**Real-world Validation:**
- [ ] Test on annotated overlaps (test set)
- [ ] Visual inspection of filtered results
- [ ] User feedback on false positives/negatives

---

## Performance Targets

### Phase 4.1 (PaddleOCR)

| Metric | Current (Tesseract) | Target (PaddleOCR) | Priority |
|--------|---------------------|-------------------|----------|
| Processing time | 52.7s | **<20s** | Critical |
| Text accuracy | 75-85% | **≥75%** | High |
| Bounding box quality | Medium | **High** | High |
| OCR artifacts | Many | **Fewer** | Medium |

---

### Phase 4.2 (Random Forest)

| Metric | Current (Rule-based) | Target (ML) | Priority |
|--------|---------------------|-------------|----------|
| False positive rate | ~30% | **<10%** | Critical |
| Precision | ~70% | **≥90%** | High |
| Recall | ~95% | **≥95%** | Critical |
| Inference time | 0ms | **<5ms** | Low |

---

### Phase 4.3 (YOLO) - If Pursued

| Metric | Current (Template) | Target (YOLO) | Priority |
|--------|-------------------|---------------|----------|
| Detection accuracy | <60% | **≥95%** | Critical |
| False positive rate | ~40% | **<5%** | High |
| Inference time | ~2s | **<3s** | Medium |
| Rotation invariance | No | **Yes** | High |

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PaddleOCR dependency issues | Low | Medium | Test on Windows, provide Tesseract fallback |
| PaddleOCR accuracy worse than Tesseract | Low | High | A/B test before full deployment |
| Random Forest overfitting | Low | Medium | Cross-validation, test on diverse sheets |
| YOLO training data insufficient | Medium | High | Collect 200+ drawings (not 100) |
| GPU requirement | Low | Medium | Optimize for CPU, document GPU benefits |
| Model size bloat | Low | Low | PaddleOCR: 200MB, RF: <1MB (acceptable) |

---

### Process Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Implementation time exceeds estimate | Medium | Medium | Phased approach, stop if >10% over |
| User doesn't see value | Low | Medium | Demo performance gains early |
| Breaking changes to Epic 1 | Low | High | Comprehensive integration tests |
| ML complexity increases maintenance | Medium | Medium | Good documentation, simple models |

---

## Success Metrics

### Phase 4.1 (PaddleOCR) Success

- ✅ Processing time <20 seconds @ 150 DPI
- ✅ Text detection accuracy ≥75% (no regression)
- ✅ Bounding box quality improved (visual inspection)
- ✅ Zero breaking changes to Phase 1 API
- ✅ Tests pass on 5+ diverse sheets

---

### Phase 4.2 (Random Forest) Success

- ✅ False positive rate <10% on overlaps
- ✅ Precision ≥90% (correctly identify real overlaps)
- ✅ Recall ≥95% (don't miss real overlaps)
- ✅ Inference time <5ms per overlap
- ✅ Works across 5+ diverse sheets

---

### Overall Epic 2 Success

- ✅ Processing time: **52s → <20s** (60%+ reduction)
- ✅ False positives: **~30% → <10%** (70% reduction)
- ✅ OCR accuracy: **75-85% → 80-90%** (improvement)
- ✅ User satisfaction: Positive feedback from Christian
- ✅ ROI positive: Time savings > implementation time

---

## Decision Points

### After Phase 4.1 (PaddleOCR)

**If processing time <20s AND accuracy ≥75%:**
→ Proceed to Phase 4.2 (Random Forest)

**If processing time >20s OR accuracy <70%:**
→ Debug performance issues OR revert to Tesseract

**If PaddleOCR installation fails:**
→ Use Tesseract fallback, document GPU benefits

---

### After Phase 4.2 (Random Forest)

**If false positive rate <10% AND precision ≥90%:**
→ Deploy to production (v0.5.0)

**If false positive rate >15% OR precision <80%:**
→ Collect more training data OR tune hyperparameters

**If user feedback negative:**
→ Make ML components optional (config flag)

---

### Phase 4.3 (YOLO) Decision

**Only pursue if ALL of the following are true:**
- ✅ Phase 4.1 and 4.2 complete and successful
- ✅ User requests north arrow/scale detection
- ✅ ROI becomes positive (>10 hours/year savings) OR regulatory requirement
- ✅ 100-200 diverse drawings available for annotation

**Otherwise:** Defer indefinitely

---

## Quick Reference

### Most Important Files

1. **ML Architecture:** [ML_ARCHITECTURE_ANALYSIS.md](ML_ARCHITECTURE_ANALYSIS.md)
2. **Implementation Plan:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Detailed task breakdown
3. **Phase 4.1 Plan:** [phases/phase-4.1/PLAN.md](phases/phase-4.1/PLAN.md)
4. **Phase 4.2 Plan:** [phases/phase-4.2/PLAN.md](phases/phase-4.2/PLAN.md)
5. **Epic 1 Status:** [../1-initial-implementation/phases/README.md](../1-initial-implementation/phases/README.md)
6. **Main CLAUDE.md:** [../../CLAUDE.md](../../CLAUDE.md)

### Key Implementation Files (Future)

- Phase 4.1 code: `tools/esc-validator/esc_validator/ocr_engine.py`
- Phase 4.2 code: `tools/esc-validator/esc_validator/ml_models/overlap_classifier.py`
- ML configuration: `tools/esc-validator/config/ml_config.yaml`
- Trained models: `tools/esc-validator/esc_validator/ml_models/overlap_classifier.pkl`

---

## Next Steps

**For AI Assistant (Claude):**
1. Review this guide with user (Christian)
2. Get approval to proceed with Phase 4.1 + 4.2
3. Create detailed implementation plan for PaddleOCR integration
4. Set up annotation workflow for Random Forest training

**For User (Christian):**
1. Review Epic 2 architecture and priorities
2. Approve Phase 4.1 + 4.2 implementation
3. Provide feedback on ML roadmap
4. Test Phase 4.1 prototype on real drawings

---

**Document Status:** Active - Ready for Implementation
**Next Update:** After Phase 4.1 completion
**Implementation Target:** Phase 4.1 + 4.2 within 2 weeks
**Version:** Epic 2 v1.0 (Planning complete)

---

**Last Updated:** 2025-11-02
**Epic Status:** Planning/Architecture phase
**Ready to Start:** Phase 4.1 (PaddleOCR integration)
