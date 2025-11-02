# Phase 4.2: Overlap Artifact Filter - Implementation Plan

**Epic:** 2-ml (Machine Learning Enhancements)
**Status:** Ready to Implement
**Expected Duration:** 6-8 hours
**Target Completion:** Week 2 of ML implementation
**Priority:** MEDIUM
**ROI:** High (70% false positive reduction)

---

## Quick Links

- **Parent Epic:** [Epic 2 ML Architecture](../../ML_ARCHITECTURE_ANALYSIS.md)
- **Full Implementation Plan:** [Epic 2 Implementation Plan](../../IMPLEMENTATION_PLAN.md#phase-42-overlap-artifact-filter)
- **Epic 1 Phase Tracker:** [Epic 1 Phases README](../../../1-initial-implementation/phases/README.md)
- **Prerequisites:** [Phase 4.1 (PaddleOCR)](../phase-4.1/PLAN.md)

---

## Objectives

Train and deploy a Random Forest classifier to filter OCR artifacts from real overlaps:

### Primary Goals
1. **Reduce false positive rate** - ~30% → <10%
2. **Distinguish OCR noise from real overlaps** - Single chars, special chars vs multi-word labels
3. **Improve user trust** - Only report actionable overlap issues
4. **Fast inference** - <5ms per overlap classification

### Success Criteria
- ✅ False positive rate <10% on overlaps
- ✅ Precision ≥90% (correctly identify real overlaps)
- ✅ Recall ≥95% (don't miss real overlaps)
- ✅ Inference time <5ms per overlap
- ✅ Works on diverse sheets (5-10 test cases)

---

## Problem Statement

### Current State (v0.3.0 + Phase 4.1)

**Phase 4 Overlap Detection Results:**
```
Entrada East page 26:
- Total overlaps detected: 34
- Critical: 10 (>50% overlap)
- Warning: 9 (20-50% overlap)
- Minor: 15 (<20% overlap)

Examples:
✅ Real: "SCE-1" overlaps "INLET" (35% overlap)
❌ Artifact: "\" overlaps "│" (53% overlap)
❌ Artifact: "~" overlaps "_" (45% overlap)
❌ Artifact: "5" overlaps "3" (28% overlap)
```

**Problem:**
- Rule-based overlap detection treats all overlaps equally
- Cannot distinguish OCR noise from legitimate overlaps
- ~30% false positive rate (estimated)
- User must manually review 10+ false positives per sheet

### Proposed Solution

**ML-Based Artifact Filtering:**
```
1. Detect all potential overlaps (existing logic)
2. Extract features from each overlap
3. Classify overlap as artifact (0) or real (1) using Random Forest
4. Filter out artifacts, keep only real overlaps
5. Report filtered results

Expected outcome:
- 34 overlaps → ~10-12 real overlaps
- False positive rate: <10%
- User reviews only actionable issues
```

---

## Technical Approach

### ML Model: Random Forest Classifier

**Why Random Forest?**
- Fast inference (<1ms per classification)
- Interpretable (feature importance)
- Small model size (<1MB)
- Easy to train (100-500 examples)
- Robust to imbalanced data
- No GPU required

**Alternative Considered:**
- Small neural network (MLP) - More complex, less interpretable
- **Decision:** Start with Random Forest, upgrade to NN if needed

---

### Feature Engineering

**Features for Classification:**
```python
@dataclass
class OverlapFeatures:
    """Feature vector for overlap classification."""
    # Geometric features
    overlap_percent: float          # 0-100%
    bbox_area1: float               # pixels²
    bbox_area2: float               # pixels²
    aspect_ratio1: float            # width/height
    aspect_ratio2: float            # width/height

    # Text features
    len1: int                       # character count
    len2: int                       # character count
    is_single_char1: bool           # len == 1
    is_single_char2: bool           # len == 1
    has_special_chars1: bool        # non-alphanumeric
    has_special_chars2: bool        # non-alphanumeric
    is_duplicate: bool              # text1 == text2
    text_similarity: float          # Levenshtein similarity (0-1)

    # OCR quality features
    confidence1: float              # 0-100%
    confidence2: float              # 0-100%
    avg_confidence: float           # mean of both
```

**Feature Rationale:**

| Feature | Why It Matters | Example |
|---------|----------------|---------|
| **overlap_percent** | Higher overlap = more likely real issue | 65% = critical, 15% = artifact |
| **len1, len2** | Single chars often artifacts | "\\" (len=1) vs "SCE-1" (len=5) |
| **is_single_char** | Strong signal for artifacts | True = 90% artifact |
| **has_special_chars** | OCR noise contains \│~_ etc | True + True = artifact |
| **is_duplicate** | Same text detected twice = OCR error | "635.0" overlaps "635.0" |
| **text_similarity** | Similar text = likely duplicate | 0.95 similarity = artifact |
| **confidence** | Low confidence = OCR uncertainty | Both <40% = likely artifact |
| **aspect_ratio** | Unusual ratios = artifacts | 10:1 ratio = vertical line artifact |

---

### Training Data Collection

**Process:**
1. Run current validator on 5-10 diverse ESC sheets
2. Extract all detected overlaps (200-300 examples expected)
3. Manually label each as **artifact (0)** or **real overlap (1)**
4. Save to CSV for training

**Annotation Guidelines:**

```
Label as ARTIFACT (0) if:
✅ Single character overlaps (e.g., "\" overlaps "│")
✅ Special character overlaps (e.g., "~" overlaps "_")
✅ Duplicate text (same text detected twice)
✅ Low confidence (<40%) on BOTH elements
✅ Very small bounding boxes (<20px width/height)
✅ OCR noise patterns (isolated symbols, fragmented text)

Label as REAL OVERLAP (1) if:
✅ Multi-word labels overlapping (e.g., "SCE-1" overlaps "INLET")
✅ High confidence (>60%) on BOTH elements
✅ Readable text that would cause confusion
✅ Overlapping street names, lot numbers, elevations
✅ Professional annotations that overlap
```

**Expected Distribution:**
- Artifacts: ~70% (210/300 examples)
- Real overlaps: ~30% (90/300 examples)
- **Imbalanced dataset** → Use class_weight='balanced' in Random Forest

---

## Implementation Tasks

### Task 1: Data Collection & Annotation (2-3 hours)

**Script:** `tools/esc-validator/scripts/collect_overlap_examples.py` (NEW)

**Functionality:**
```python
def collect_overlap_examples(pdf_paths: List[Path], output_csv: Path):
    """
    Collect overlap examples from multiple sheets.

    Process:
    1. Run validator on each PDF
    2. Extract all overlap issues
    3. Create CSV with features pre-filled
    4. Manual labeling: fill 'is_real_overlap' column (0 or 1)
    """
    all_overlaps = []

    for pdf_path in pdf_paths:
        result = validate_esc_sheet(pdf_path)

        for overlap in result.quality_issues:
            all_overlaps.append({
                'pdf_file': pdf_path.name,
                'element1': overlap.element1,
                'element2': overlap.element2,
                'overlap_percent': overlap.overlap_percent,
                # ... all features ...
                'is_real_overlap': None  # TO BE FILLED MANUALLY
            })

    df = pd.DataFrame(all_overlaps)
    df.to_csv(output_csv, index=False)
```

**Target Sheets:**
- Entrada East (baseline)
- 4-9 additional diverse ESC sheets
- Different CAD styles, different projects

**Deliverable:**
- ✅ `collect_overlap_examples.py` script
- ✅ 200-300 labeled examples in `data/overlap_training_data.csv`
- ✅ Annotation guidelines documented

**Time:** 2-3 hours (1 hour scripting + 1-2 hours annotation)

---

### Task 2: Feature Engineering (1 hour)

**File:** `tools/esc-validator/esc_validator/ml_models/overlap_classifier.py` (NEW)

**Components:**
1. `OverlapFeatures` dataclass - Feature vector definition
2. `extract_overlap_features()` - Extract features from overlap + OCR results
3. Helper functions - `has_special_chars()`, `aspect_ratio()`, `text_similarity()`

**Key Implementation:**
```python
def extract_overlap_features(
    overlap: OverlapIssue,
    elem1: OCRResult,
    elem2: OCRResult
) -> OverlapFeatures:
    """
    Extract features from overlap for classification.

    Args:
        overlap: Detected overlap issue
        elem1: First OCR element
        elem2: Second OCR element

    Returns:
        OverlapFeatures object ready for model input
    """
    from Levenshtein import distance as levenshtein_distance

    # Calculate all features
    return OverlapFeatures(
        overlap_percent=overlap.overlap_percent,
        len1=len(elem1.text),
        len2=len(elem2.text),
        is_single_char1=(len(elem1.text.strip()) == 1),
        is_single_char2=(len(elem2.text.strip()) == 1),
        has_special_chars1=has_special_chars(elem1.text),
        has_special_chars2=has_special_chars(elem2.text),
        is_duplicate=(elem1.text == elem2.text),
        text_similarity=calculate_text_similarity(elem1.text, elem2.text),
        confidence1=elem1.confidence,
        confidence2=elem2.confidence,
        aspect_ratio1=calculate_aspect_ratio(elem1.bbox),
        aspect_ratio2=calculate_aspect_ratio(elem2.bbox),
    )
```

**Deliverable:**
- ✅ `overlap_classifier.py` with feature extraction
- ✅ Unit tests for feature calculation

**Time:** 1 hour

---

### Task 3: Model Training (1 hour)

**Script:** `tools/esc-validator/scripts/train_overlap_classifier.py` (NEW)

**Training Pipeline:**
```python
def train_overlap_classifier(training_csv: Path, model_output: Path):
    """
    Train Random Forest classifier for overlap artifact detection.

    Process:
    1. Load labeled training data
    2. Extract features (X) and labels (y)
    3. Train/test split (80/20, stratified)
    4. Train Random Forest with balanced class weights
    5. Evaluate on test set
    6. Cross-validation (5-fold)
    7. Feature importance analysis
    8. Save trained model (.pkl)
    """
    # Load data
    df = pd.read_csv(training_csv)
    df = df[df['is_real_overlap'].notna()]  # Remove unlabeled

    # Extract features and labels
    X = df[FEATURE_COLUMNS].values
    y = df['is_real_overlap'].values

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train Random Forest
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        class_weight='balanced'  # Handle imbalanced data
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))
    print(confusion_matrix(y_test, y_pred))

    # Cross-validation
    cv_scores = cross_val_score(clf, X, y, cv=5, scoring='f1')
    print(f"CV F1 Scores: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # Save model
    joblib.dump(clf, model_output)
```

**Success Criteria:**
- Precision ≥90% on "Real Overlap" class
- Recall ≥95% on "Real Overlap" class
- F1 score ≥0.85 overall
- Cross-validation stable (std <0.05)

**Deliverable:**
- ✅ `train_overlap_classifier.py` script
- ✅ Trained model (`overlap_classifier.pkl`)
- ✅ Training report with metrics
- ✅ Feature importance analysis

**Time:** 1 hour

---

### Task 4: Model Integration (1-2 hours)

**File:** `tools/esc-validator/esc_validator/ml_models/overlap_classifier.py` (CONTINUED)

**Add Inference:**
```python
class OverlapArtifactFilter:
    """Classifier to filter OCR artifacts from real overlaps."""

    def __init__(self, model_path: Optional[Path] = None):
        """Load trained model or use fallback."""
        if model_path is None:
            model_path = Path(__file__).parent / "overlap_classifier.pkl"

        try:
            self.model = joblib.load(model_path)
            self.enabled = True
        except Exception as e:
            logger.warning(f"Could not load overlap classifier: {e}")
            self.enabled = False

    def is_real_overlap(
        self,
        overlap: OverlapIssue,
        elem1: OCRResult,
        elem2: OCRResult
    ) -> bool:
        """
        Classify overlap as real (True) or artifact (False).

        Returns:
            True if real overlap, False if artifact
        """
        if not self.enabled:
            return self._rule_based_filter(overlap, elem1, elem2)

        # Extract features
        features = extract_overlap_features(overlap, elem1, elem2)
        X = features.to_array().reshape(1, -1)

        # Predict
        prediction = self.model.predict(X)[0]
        return bool(prediction)  # 1 = real, 0 = artifact

    def _rule_based_filter(self, overlap, elem1, elem2) -> bool:
        """Fallback rule-based filter if ML model unavailable."""
        # Simple rules: reject single chars, special chars, low confidence
        if len(elem1.text.strip()) == 1 and len(elem2.text.strip()) == 1:
            return False
        if elem1.confidence < 40 and elem2.confidence < 40:
            return False
        return True

    def filter_overlaps(
        self,
        overlaps: List[OverlapIssue],
        ocr_results: List[OCRResult]
    ) -> List[OverlapIssue]:
        """Filter list of overlaps, keeping only real overlaps."""
        # Build OCR lookup dict
        ocr_dict = {result.text: result for result in ocr_results}

        filtered = []
        for overlap in overlaps:
            elem1 = ocr_dict.get(overlap.element1)
            elem2 = ocr_dict.get(overlap.element2)

            if elem1 is None or elem2 is None:
                filtered.append(overlap)  # Can't classify, keep
                continue

            if self.is_real_overlap(overlap, elem1, elem2):
                filtered.append(overlap)

        return filtered
```

**Integration into quality_checker.py:**
```python
# esc_validator/quality_checker.py (UPDATED)

_overlap_filter = None

def detect_overlapping_labels(
    image: np.ndarray,
    ocr_results: Optional[List[OCRResult]] = None,
    use_ml_filter: bool = True
) -> List[OverlapIssue]:
    """Detect overlapping labels with optional ML filtering."""
    global _overlap_filter

    # ... existing overlap detection logic ...

    # Apply ML filter
    if use_ml_filter:
        if _overlap_filter is None:
            _overlap_filter = OverlapArtifactFilter()
        overlaps = _overlap_filter.filter_overlaps(overlaps, ocr_results)

    return overlaps
```

**Deliverable:**
- ✅ `OverlapArtifactFilter` class with inference
- ✅ Integration into quality_checker.py
- ✅ Fallback rule-based filter
- ✅ Unit tests for classifier

**Time:** 1-2 hours

---

### Task 5: Validation & Testing (1-2 hours)

**Validation Script:** `tools/esc-validator/scripts/validate_overlap_filter.py` (NEW)

**Validation Process:**
```python
def validate_overlap_filter(pdf_paths: List[Path]):
    """
    Validate overlap filter on diverse sheets.

    Compare:
    - Unfiltered overlaps (all detections)
    - Filtered overlaps (ML-filtered)
    - Manual review results
    """
    results = []

    for pdf_path in pdf_paths:
        # Run without filter
        result_unfiltered = validate_esc_sheet(pdf_path, use_ml_filter=False)

        # Run with filter
        result_filtered = validate_esc_sheet(pdf_path, use_ml_filter=True)

        results.append({
            'pdf': pdf_path.name,
            'unfiltered_count': len(result_unfiltered.quality_issues),
            'filtered_count': len(result_filtered.quality_issues),
            'reduction': len(result_unfiltered.quality_issues) - len(result_filtered.quality_issues)
        })

    # Print summary
    df = pd.DataFrame(results)
    print(df)
    print(f"\nAvg reduction: {df['reduction'].mean():.1f} overlaps/sheet")
    print(f"Pct reduction: {(df['reduction']/df['unfiltered_count']).mean()*100:.1f}%")
```

**Unit Tests:**
```python
# tests/unit/test_overlap_classifier.py

def test_overlap_artifact_filter_artifacts():
    """Test ML filter correctly rejects artifacts."""
    filter = OverlapArtifactFilter()

    # Test artifact (single chars)
    artifact = OverlapIssue(element1="\\", element2="|", overlap_percent=53)
    elem1 = OCRResult(text="\\", confidence=45, bbox=(10, 10, 15, 20))
    elem2 = OCRResult(text="|", confidence=50, bbox=(12, 12, 17, 22))
    assert not filter.is_real_overlap(artifact, elem1, elem2)

def test_overlap_artifact_filter_real():
    """Test ML filter correctly identifies real overlaps."""
    filter = OverlapArtifactFilter()

    # Test real overlap
    real = OverlapIssue(element1="SCE-1", element2="INLET", overlap_percent=35)
    elem1 = OCRResult(text="SCE-1", confidence=85, bbox=(100, 100, 150, 120))
    elem2 = OCRResult(text="INLET", confidence=90, bbox=(130, 105, 180, 125))
    assert filter.is_real_overlap(real, elem1, elem2)

def test_overlap_filter_fallback():
    """Test rule-based fallback when ML model unavailable."""
    filter = OverlapArtifactFilter(model_path=Path("nonexistent.pkl"))
    assert not filter.enabled  # Should fall back

    # Should still work with rule-based logic
    artifact = OverlapIssue(element1="~", element2="_", overlap_percent=45)
    elem1 = OCRResult(text="~", confidence=30, bbox=(10, 10, 15, 20))
    elem2 = OCRResult(text="_", confidence=35, bbox=(12, 12, 17, 22))
    assert not filter.is_real_overlap(artifact, elem1, elem2)
```

**Integration Tests:**
```python
# tests/integration/test_overlap_filter_integration.py

def test_overlap_filter_reduces_false_positives():
    """Test that ML filter significantly reduces false positives."""
    # Run on Entrada East page 26
    result_unfiltered = validate_esc_sheet(ENTRADA_EAST_PDF, use_ml_filter=False)
    result_filtered = validate_esc_sheet(ENTRADA_EAST_PDF, use_ml_filter=True)

    unfiltered_count = len(result_unfiltered.quality_issues)
    filtered_count = len(result_filtered.quality_issues)

    # Should reduce overlaps by at least 50%
    reduction_pct = (unfiltered_count - filtered_count) / unfiltered_count
    assert reduction_pct >= 0.5, f"Expected ≥50% reduction, got {reduction_pct*100:.1f}%"
```

**Deliverable:**
- ✅ Validation script
- ✅ Validation results on 5-10 sheets
- ✅ Unit tests for classifier
- ✅ Integration tests for filtering

**Time:** 1-2 hours

---

## Expected Outcomes

### Accuracy Improvements

| Metric | Current (v0.3.0) | Target (v0.5.0) | Expected Gain |
|--------|------------------|-----------------|---------------|
| False positive rate | ~30% | <10% | **70% reduction** |
| Precision (real overlaps) | N/A | ≥90% | New metric |
| Recall (real overlaps) | 100% | ≥95% | Maintain high recall |
| F1 score | N/A | ≥0.85 | New metric |

### User Experience Improvements

| Metric | Before | After | Impact |
|--------|--------|-------|--------|
| Overlaps to review | ~34 per sheet | ~10-12 per sheet | **70% reduction** |
| False positives | ~10 per sheet | <3 per sheet | Higher trust |
| Time per review | 3-5 min | 1-2 min | Faster QC |

---

## Dependencies

### Prerequisites
- ✅ Phase 4 complete (overlap detection)
- ✅ Phase 4.1 complete (PaddleOCR integration)
- ⏳ 200-300 labeled training examples

### External Libraries
```bash
# Add to requirements.txt
scikit-learn==1.3.2
joblib==1.3.2
python-Levenshtein==0.21.1
```

### Test Data
- ✅ Entrada East page 26
- ⏳ 4-9 additional diverse ESC sheets
- ⏳ Labeled training dataset CSV

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Random Forest overfitting | Medium | Medium | Cross-validation, test on unseen sheets |
| Insufficient training data | Low | Medium | Collect 300 examples (not 200) |
| Annotation time exceeds estimate | Medium | Low | Start with 100 examples, iterate |
| Model accuracy below target | Low | Medium | Tune hyperparameters, try neural network |
| Model file too large | Low | Low | RF models <1MB, acceptable |

**Overall Risk Level:** LOW (most risks have straightforward mitigations)

---

## Deliverables

### Code
1. ✅ `scripts/collect_overlap_examples.py` - Data collection
2. ✅ `ml_models/overlap_classifier.py` - Feature extraction + classifier
3. ✅ `scripts/train_overlap_classifier.py` - Training script
4. ✅ `ml_models/overlap_classifier.pkl` - Trained model
5. ✅ Updated `quality_checker.py` - Integration
6. ✅ `scripts/validate_overlap_filter.py` - Validation script

### Tests
1. ✅ `tests/unit/test_overlap_classifier.py` - Classifier tests
2. ✅ `tests/integration/test_overlap_filter_integration.py` - Pipeline tests

### Documentation
1. ✅ This file (PLAN.md) - Implementation plan
2. ⏳ `IMPLEMENTATION.md` - Technical details (after coding)
3. ⏳ `TEST_REPORT.md` - Test results (after testing)
4. ⏳ `SUMMARY.md` - Executive summary (after completion)

### Data
1. ✅ `data/overlap_training_data.csv` - Labeled training dataset (200-300 examples)
2. ✅ Trained model file (<1MB)

---

## Timeline

**Total Estimated Time:** 6-8 hours

| Day | Tasks | Hours |
|-----|-------|-------|
| **Day 1** | Data collection + annotation | 2-3 hours |
| **Day 2** | Feature engineering + training | 2 hours |
| **Day 3** | Integration + testing | 2-3 hours |

**Target Completion:** End of Week 2 (ML implementation)

---

## Success Metrics

### Phase 4.2 Success Criteria
- ✅ False positive rate <10% on overlaps
- ✅ Precision ≥90% (correctly identify real overlaps)
- ✅ Recall ≥95% (don't miss real overlaps)
- ✅ F1 score ≥0.85
- ✅ Inference time <5ms per overlap
- ✅ Model size <1MB
- ✅ Works on diverse sheets (5-10 test cases)
- ✅ Graceful fallback if model unavailable

### Deployment Criteria
- All success criteria met
- User (Christian) approval
- Tested on 5-10 diverse ESC sheets
- Documentation complete

---

## Next Steps After Phase 4.2

**Immediate:**
1. Deploy v0.5.0 (PaddleOCR + ML Filter)
2. Test on diverse sheets
3. Collect user feedback

**Short-term:**
1. Monitor accuracy over time
2. Retrain model with more examples if needed
3. Document edge cases

**Long-term (Optional):**
1. Consider Phase 4.3 (YOLO for symbols) - only if ROI justifies
2. Explore neural network if Random Forest insufficient
3. Expand to other quality checks

---

## References

### Related Documentation
- **Epic 2 ML Architecture:** [ML_ARCHITECTURE_ANALYSIS.md](../../ML_ARCHITECTURE_ANALYSIS.md)
- **Epic 2 Implementation Plan:** [IMPLEMENTATION_PLAN.md](../../IMPLEMENTATION_PLAN.md#phase-42-overlap-artifact-filter)
- **Phase 4 Implementation:** [phase-4/IMPLEMENTATION.md](../../../1-initial-implementation/phases/phase-4/IMPLEMENTATION.md)
- **Phase 4.1 Plan:** [phase-4.1/PLAN.md](../phase-4.1/PLAN.md)

### Related Code
- `esc_validator/quality_checker.py` - Current overlap detection
- `esc_validator/ocr_engine.py` - OCR abstraction (Phase 4.1)
- `esc_validator/text_detector.py` - Text detection with bboxes

---

**Plan Created:** 2025-11-02
**Status:** Ready to implement (after Phase 4.1)
**Expected Start:** Week 2 of ML implementation (pending Phase 4.1 completion)
**Target Version:** ESC Validator v0.5.0
