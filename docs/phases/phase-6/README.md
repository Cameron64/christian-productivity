# Phase 6: Advanced ML Enhancement (Optional)

**Status:** Not Started
**Trigger:** Only if Phase 1-5 accuracy <80%
**Expected Duration:** 2-4 weeks
**Accuracy Target:** 85-95%

---

## Overview

Phase 6 is an **optional enhancement** using machine learning to achieve 90%+ accuracy if traditional computer vision approaches (Phase 1-5) fall short of the 80% target.

**Decision:** Pursue Phase 6 only if:
- Phase 1-5 combined accuracy <80%
- Traditional CV approaches exhausted
- Time investment justified by accuracy gain
- Training data available (50-100 annotated sheets)

---

## Three ML Approaches

### Option A: Custom Object Detector (YOLOv8)

**Use Case:** Detect ESC symbols and features directly

**Approach:**
- Annotate 50-100 ESC sheets with bounding boxes
- Label all symbols: SF, SCE, CONC WASH, north arrows, block labels
- Train YOLOv8 model
- 2-4 hours GPU training time

**Expected Improvement:**
- Symbol detection: 70-85% → 90-95%
- Feature detection: 80-90% → 92-97%

**Tools:**
- LabelImg or Roboflow for annotation
- Ultralytics YOLOv8 library
- GPU recommended (can use Google Colab free tier)

**Pros:**
- Handles symbol variations
- Rotation invariant
- Scale invariant
- Fast inference (<1 sec)

**Cons:**
- Requires significant annotation effort
- GPU needed for training
- Model size ~50MB

---

### Option B: Specialized OCR (PaddleOCR)

**Use Case:** Better text extraction from engineering drawings

**Approach:**
- Replace Tesseract with PaddleOCR
- Pre-trained on technical documents
- Handles rotated text better

**Expected Improvement:**
- Text detection: 75-85% → 85-95%
- Label detection: 80-90% → 90-95%

**Tools:**
- PaddleOCR library
- No training required (pre-trained model)

**Pros:**
- Drop-in Tesseract replacement
- Better for technical drawings
- Handles rotation
- No annotation needed

**Cons:**
- Larger model size (~100MB)
- Slower than Tesseract
- Chinese origin (if that matters)

---

### Option C: Semantic Segmentation (U-Net)

**Use Case:** Pixel-level line type classification

**Approach:**
- Annotate line types at pixel level
- Train U-Net model for segmentation
- Classify each pixel: background, solid line, dashed line, text, symbol

**Expected Improvement:**
- Line type detection: 70-80% → 90-95%
- Contour separation: 60-70% → 85-90%

**Tools:**
- U-Net architecture (PyTorch/TensorFlow)
- Pixel-level annotation tool

**Pros:**
- Very accurate line classification
- Handles complex overlapping lines
- Separates line types clearly

**Cons:**
- Most annotation effort
- Longest training time
- Largest model size
- Slowest inference

---

## Recommended Approach

**If pursuing Phase 6, start with Option B (PaddleOCR):**

1. **Easiest to implement** - Drop-in replacement
2. **No annotation needed** - Use pre-trained model
3. **Quick to test** - See improvement immediately
4. **Low risk** - Can fall back to Tesseract

**Then consider Option A (YOLOv8) if:**
- PaddleOCR improves OCR but symbols still problematic
- Can annotate 50+ ESC sheets
- Have GPU access

**Avoid Option C unless:**
- Line detection critical
- Other approaches insufficient
- Have pixel annotation resources

---

## Prerequisites

### For Option A (YOLOv8)
- 50-100 ESC sheets for annotation
- Annotation tool (LabelImg, Roboflow)
- GPU for training (or Colab access)
- 20-40 hours annotation time

### For Option B (PaddleOCR)
- PaddleOCR library (`pip install paddleocr`)
- Replace OCR calls in `text_detector.py`
- Test on existing sheets

### For Option C (U-Net)
- Pixel-level annotation tool
- 10-20 sheets with pixel annotations
- GPU for training
- 40-80 hours annotation time

---

## Planned Deliverables

### Code
- `esc_validator/ml_detector.py` - ML integration module
- Model loading and inference
- Training scripts (if custom training)

### Models
- `models/yolov8_esc.pt` - Trained YOLOv8 (if Option A)
- `models/unet_lines.pt` - Trained U-Net (if Option C)

### Documentation
- Annotation guide
- Training procedure
- Model performance benchmarks
- Inference optimization tips

### Training Data
- Annotated dataset (if custom training)
- Data augmentation pipeline
- Train/val/test splits

---

## Training Pipeline (Option A - YOLOv8)

```python
# 1. Annotate images (LabelImg, Roboflow)
# 2. Create dataset YAML
# 3. Train model
from ultralytics import YOLO

model = YOLO('yolov8n.pt')  # Start with nano model
results = model.train(
    data='esc_dataset.yaml',
    epochs=100,
    imgsz=1280,  # ESC sheets are high-res
    batch=8,
    device=0  # GPU
)

# 4. Validate
metrics = model.val()
print(f"mAP50: {metrics.box.map50}")

# 5. Export
model.export(format='onnx')  # For production
```

---

## Expected Results

### Option A (YOLOv8)
- Training time: 2-4 hours (GPU)
- Annotation time: 20-40 hours
- Inference time: 0.5-1 sec per sheet
- Accuracy: 90-95% mAP50
- Model size: 50MB

### Option B (PaddleOCR)
- Setup time: 1 hour
- No annotation needed
- Inference time: 5-10 sec per sheet
- Accuracy: 85-95% (OCR)
- Model size: 100MB

### Option C (U-Net)
- Training time: 4-8 hours (GPU)
- Annotation time: 40-80 hours
- Inference time: 2-3 sec per sheet
- Accuracy: 90-95% (segmentation)
- Model size: 150MB

---

## Success Criteria

- Overall accuracy ≥85% (stretch: ≥90%)
- False negative rate <5% on critical elements
- Processing time <60 seconds per sheet
- Model deployable on standard hardware
- Annotation effort justified by accuracy gain

---

## Decision Point

**Pursue Phase 6 if:**
- Phase 1-5 accuracy <80% after all optimizations
- Christian confirms additional accuracy worth effort
- Training data can be collected
- Time/resources available for ML work

**Skip Phase 6 if:**
- Phase 1-5 achieves ≥80% accuracy
- Current accuracy sufficient for use case
- Annotation effort not justified
- ML expertise not available

---

## Cost-Benefit Analysis

**Benefits:**
- 10-20% accuracy improvement
- Handles edge cases better
- More robust to variations

**Costs:**
- 20-80 hours annotation time
- GPU resources for training
- Larger model deployment
- Maintenance of ML pipeline

**ROI:**
- If saves 2+ hours/week: Worth it
- If <1 hour/week savings: Maybe not

---

**Status:** CONDITIONAL - Only if Phase 1-5 insufficient
**Recommendation:** Start with Option B (PaddleOCR) if needed
