# ESC Validator - Development Rules

## Domain Knowledge

### What is ESC?
- **ESC** = Erosion and Sediment Control
- ESC sheets are specialized civil engineering drawings that show:
  - Erosion control measures (silt fences, inlet protection, etc.)
  - Sediment control practices
  - Construction sequencing for environmental protection
  - Required notes and certifications

### Sheet Specifications
- Standard size: 11x17 inches (ANSI B), landscape orientation
- Typical scan resolution: 150-300 DPI
- May include handwritten notes, redlines, stamps
- Usually page 1-3 of a larger civil engineering drawing set

### The 16-Item Checklist
Critical items that **cannot be false negatives**:
- **SCE** (Stormwater Control Evaluation) notation
- **CONC WASH** (concrete washout area)

Other checklist items include:
- Silt fence locations
- Inlet protection
- Construction entrance/exit
- Stabilized staging areas
- Erosion control notes
- Engineer's seal and signature

**Why This Matters:**
- Missing any item = permit rejection
- Resubmission cycles cost 1-2 weeks + $500-2000
- Christian reviews ~50 ESC sheets per year
- Current manual review: 15-20 min per sheet
- Target with automation: 5-10 min per sheet

---

## Architecture Principles

### Module Organization
```
esc-validator/
├── core/
│   ├── models.py          # Dataclasses: ChecklistItem, ValidationResult, ESCSheet
│   ├── config.py          # Configuration and thresholds
│   └── constants.py       # ESC-specific constants (item names, required text)
├── phases/
│   ├── text_detection.py      # Phase 1: OCR and text extraction
│   ├── template_matching.py   # Phase 2: Visual pattern matching
│   ├── spatial_reasoning.py   # Phase 3: Geometric relationships
│   ├── fuzzy_matching.py      # Phase 4: Fuzzy text matching
│   ├── confidence_scoring.py  # Phase 5: Multi-signal scoring
│   └── ml_detection.py        # Phase 6: Machine learning (future)
├── validators/
│   ├── critical_items.py  # SCE, CONC WASH validators
│   └── standard_items.py  # Other checklist validators
├── utils/
│   ├── pdf_utils.py       # PDF extraction and preprocessing
│   ├── image_utils.py     # Image manipulation and enhancement
│   └── logging_utils.py   # Structured logging with confidence scores
├── cli.py                 # Command-line interface
└── tests/
    ├── test_data/         # Real ESC sheets (not synthetic)
    └── test_*.py          # Unit and integration tests
```

### Data Models
Use **dataclasses** for all core types:

```python
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

@dataclass
class ChecklistItem:
    name: str
    required_text: list[str]  # Text patterns to detect
    is_critical: bool         # True for SCE, CONC WASH
    location_hint: str        # "top-right", "notes section", etc.

@dataclass
class ValidationResult:
    item: ChecklistItem
    found: bool
    confidence: float         # 0.0 to 1.0
    detection_method: str     # "ocr", "template", "ml", etc.
    location: tuple[int, int] | None  # (x, y) if found
    evidence: str            # What was detected
```

### Phase Implementation Rules
1. **One phase per file** - Keep phase logic isolated
2. **Each phase returns confidence scores** - Never return just True/False
3. **Phases compose** - Later phases can use earlier phase results
4. **Phases are optional** - Should work independently for testing

---

## Coding Standards

### Required Practices
- ✅ **Type hints for all functions** - No exceptions
- ✅ **Use pathlib.Path** - Never use string paths
- ✅ **Dataclasses over dicts** - For structured data
- ✅ **Explicit confidence scores** - Every detection returns 0.0-1.0 float
- ✅ **Structured logging** - Include context: item name, confidence, method

### CLI Interface Standards
All CLI tools must support:
```python
import argparse

parser = argparse.ArgumentParser(description="Validate ESC sheet")
parser.add_argument("input", type=Path, help="Path to ESC sheet PDF")
parser.add_argument("--output", "-o", type=Path, help="Output JSON results")
parser.add_argument("--verbose", "-v", action="store_true", help="Detailed logging")
parser.add_argument("--confidence-threshold", type=float, default=0.7,
                   help="Minimum confidence (0.0-1.0)")
parser.add_argument("--phases", nargs="+",
                   choices=["text", "template", "spatial", "fuzzy", "ml"],
                   help="Which detection phases to run")
```

### Logging Standards
Use structured logging with appropriate levels:

```python
import logging

# Set up logger for each module
logger = logging.getLogger(__name__)

# Log levels:
# DEBUG   - Confidence scores, intermediate results
# INFO    - Validation results, processing steps
# WARNING - Low confidence detections (< 0.7), potential false negatives
# ERROR   - Processing failures, unreadable PDFs
# CRITICAL - Never use (reserved for catastrophic failures)

# Example usage:
logger.debug(f"SCE detection confidence: {confidence:.2f} via {method}")
logger.info(f"Found {item.name} at location {location}")
logger.warning(f"Low confidence ({confidence:.2f}) for critical item: {item.name}")
```

### Error Handling
```python
# DO: Explicit error handling with context
try:
    image = extract_sheet_image(pdf_path, page=0)
except PDFProcessingError as e:
    logger.error(f"Failed to extract page 0 from {pdf_path}: {e}")
    raise ValidationError(f"Cannot process ESC sheet: {e}") from e

# DON'T: Suppress exceptions in validation logic
try:
    result = validate_critical_item(item)
except Exception:
    pass  # ❌ Christian needs to see failures!
```

---

## Anti-Patterns to Avoid

### ❌ DON'T:
1. **Load entire 100+ page PDFs into memory**
   - Extract only the ESC sheet page (usually page 1-3)
   - Use streaming for large files

2. **Use absolute paths in code**
   ```python
   # Bad
   config_file = "C:/Users/Cam/christian-productivity/config.json"

   # Good
   from pathlib import Path
   PROJECT_ROOT = Path(__file__).parent.parent
   config_file = PROJECT_ROOT / "config.json"
   ```

3. **Suppress exceptions in validation logic**
   - Christian needs to see when validation fails
   - Better to raise and log than silently skip

4. **Return boolean without confidence**
   ```python
   # Bad
   def detect_sce(image) -> bool:
       return found

   # Good
   def detect_sce(image) -> tuple[bool, float]:
       return found, confidence
   ```

5. **Hardcode thresholds**
   ```python
   # Bad
   if confidence > 0.7:  # Magic number

   # Good
   from core.config import CONFIDENCE_THRESHOLD
   if confidence > CONFIDENCE_THRESHOLD:
   ```

6. **Use synthetic test data**
   - Test with real ESC sheets from Christian's projects
   - Edge cases matter: handwriting, poor scans, stamps

7. **Optimize prematurely**
   - Get accuracy right first
   - Then optimize if processing takes > 30 seconds per sheet

---

## File Size Guidelines & Refactoring Triggers

### When to Refactor

**Automatic triggers for code review:**

| Metric | Threshold | Action Required |
|--------|-----------|-----------------|
| **Lines of code** | > 500 lines | Consider splitting into multiple modules |
| **File size** | > 15 KB | Review for potential extraction of utilities/helpers |
| **Token count** | > 10,000 tokens (~1,000-1,500 LOC) | High priority refactor - Claude's performance degrades |
| **Functions per file** | > 15 functions | Extract related functions into separate module |
| **Class size** | > 300 lines | Split into multiple classes or extract mixins |
| **Cyclomatic complexity** | > 10 per function | Break down into smaller functions |

### Refactoring Checklist

When a file hits the thresholds above:

1. **Analyze responsibilities**
   - Is this file doing multiple jobs?
   - Can I extract utilities, helpers, or validators?

2. **Look for natural boundaries**
   - Groups of related functions → new module
   - Large class → split by concern
   - Repeated patterns → extract to utils

3. **Common extractions for this project:**
   ```
   # If text_detection.py > 500 lines, extract:
   text_detection.py         # Core detection logic
   └── ocr_engines.py        # Different OCR implementations
   └── text_preprocessing.py # Text cleaning, normalization
   └── text_patterns.py      # Regex patterns, search terms

   # If validators grow too large, split by type:
   validators/
   ├── critical_items.py     # SCE, CONC WASH
   ├── erosion_control.py    # Silt fence, inlet protection
   ├── staging_areas.py      # Construction entrance, stockpiles
   └── documentation.py      # Notes, seals, signatures
   ```

4. **After refactoring:**
   - Run all tests (must pass)
   - Update imports in dependent files
   - Update this CLAUDE.md if architecture changed
   - Document the refactoring decision in commit message

### Proactive Monitoring

Add to your development workflow:
```bash
# Check file sizes before committing
find . -name "*.py" -size +15k -exec ls -lh {} \;

# Count lines in modules (Unix/Git Bash)
find . -name "*.py" -exec wc -l {} \; | sort -rn | head -10

# PowerShell alternative
Get-ChildItem -Recurse -Filter "*.py" |
  Select-Object FullName, @{N="Lines";E={(Get-Content $_.FullName).Count}} |
  Sort-Object Lines -Descending |
  Select-Object -First 10
```

**Golden Rule:** If you're scrolling more than 2-3 screen heights to navigate a file, it's time to refactor.

---

## Testing Requirements

### Test Data Standards
- ✅ Use **real ESC sheets** from Christian's projects
- ✅ Include edge cases:
  - Handwritten notes and redlines
  - Poor quality scans (low DPI)
  - Rotated or skewed sheets
  - Stamps and signatures overlapping text
  - Multi-page ESC sheets
- ✅ Anonymize client/project info before committing

### Test Coverage
- **Critical items (SCE, CONC WASH):** 100% test coverage, multiple scenarios
- **Standard items:** 80%+ coverage
- **Utilities and helpers:** 70%+ coverage

### Test Structure
```python
# tests/test_critical_items.py
import pytest
from pathlib import Path

TEST_DATA = Path(__file__).parent / "test_data"

def test_sce_detection_clear_text():
    """SCE in standard location with clear OCR text"""
    sheet = load_test_sheet(TEST_DATA / "esc_clear_sce.pdf")
    found, confidence = detect_sce(sheet)
    assert found is True
    assert confidence > 0.9

def test_sce_detection_handwritten():
    """SCE added by hand - harder to detect"""
    sheet = load_test_sheet(TEST_DATA / "esc_handwritten_sce.pdf")
    found, confidence = detect_sce(sheet)
    # Lower confidence OK, but must not miss it
    assert found is True
    assert confidence > 0.5

def test_sce_missing_raises_warning():
    """Missing SCE must be flagged - no false negatives"""
    sheet = load_test_sheet(TEST_DATA / "esc_no_sce.pdf")
    found, confidence = detect_sce(sheet)
    assert found is False
    # Should log WARNING since SCE is critical
```

---

## Success Criteria

### Phase 1-5 (Rule-Based)
- ✅ **Accuracy:** 70-80% items automatically validated
- ✅ **False Negatives:** 0% on critical items (SCE, CONC WASH)
- ✅ **Processing Time:** < 30 seconds per sheet
- ✅ **Confidence Calibration:** Low-confidence flags correlate with actual ambiguity

### Phase 6 (ML-Based) - Optional
- ✅ **Accuracy:** 85-95% items automatically validated
- ✅ **False Negatives:** < 1% on critical items
- ✅ **Processing Time:** < 45 seconds per sheet (including model inference)
- ✅ **Model Size:** < 100 MB (must run on Christian's laptop)

### User Experience
- ✅ Christian uses tool on every project (adoption)
- ✅ Review time reduced from 15-20 min to 5-10 min per sheet
- ✅ Zero permit rejections due to missed checklist items (in 6 months)
- ✅ Tool provides actionable output (JSON + highlighted PDF)

---

## Development Workflow

### Starting a New Phase
1. Read this file and PLAN.md
2. Create new module in `phases/` directory
3. Define function signatures with type hints
4. Write tests FIRST for critical paths
5. Implement detection logic
6. Test on 5+ real ESC sheets
7. Tune confidence thresholds
8. Document any new patterns discovered

### Before Committing
- [ ] All tests pass
- [ ] Type hints on all new functions
- [ ] Logging statements include confidence scores
- [ ] No hardcoded paths or magic numbers
- [ ] Check file sizes (refactor if > 500 lines)
- [ ] Update PLAN.md if approach changed

### Code Review Checklist
When reviewing your own code before asking Christian to test:
- [ ] Would this catch the issue if I was tired and missed it manually?
- [ ] If it fails, will Christian know why?
- [ ] Are confidence scores trustworthy?
- [ ] Did I test with real sheets, not toy examples?
- [ ] Is this code readable by Christian (who may maintain it)?

---

## Communication with Christian

### When Asking for Feedback
- Show confidence scores, not just pass/fail
- Explain which detection method found each item
- If uncertain, show Christian the evidence (cropped image, extracted text)
- Estimate time savings in minutes, not just percentages

### When Reporting Results
```json
{
  "sheet": "entrada-east-esc-sheet-1.pdf",
  "timestamp": "2025-11-01T14:32:00",
  "processing_time_seconds": 12.3,
  "results": [
    {
      "item": "SCE",
      "found": true,
      "confidence": 0.92,
      "method": "template_matching",
      "location": [1240, 180],
      "needs_review": false
    },
    {
      "item": "CONC WASH",
      "found": true,
      "confidence": 0.68,
      "method": "fuzzy_text",
      "evidence": "CONC. WASHOUT AREA",
      "needs_review": true,
      "reason": "Confidence below 0.7 threshold"
    }
  ],
  "summary": {
    "total_items": 16,
    "found": 14,
    "needs_review": 2,
    "estimated_time_saved_minutes": 8
  }
}
```

---

## Performance Considerations

### Optimization Order (don't optimize prematurely!)
1. **Correctness** - Get accuracy right first
2. **User experience** - Clear output and confidence scores
3. **Speed** - Only if > 30 seconds per sheet

### If Performance Becomes an Issue:
- Cache OCR results (text extraction is expensive)
- Use lower DPI for initial pass (150 DPI), high DPI only for ambiguous items
- Parallelize independent checklist items
- Consider GPU acceleration only for Phase 6 (ML)

### Memory Management
- Don't keep full-resolution images in memory
- Release resources after each phase
- Use generators for batch processing

---

## Future Considerations

### When to Move to Phase 6 (ML)
Decision point after Phase 5 is complete:
- If accuracy < 70%, consider ML
- If false negative rate on critical items > 0%, consider ML
- If Christian is happy with 70-80%, Phase 6 is optional

### Potential ML Approaches
- Object detection (YOLO/Faster R-CNN) for visual elements
- OCR with layout analysis (PaddleOCR, LayoutLM)
- Custom trained model on ESC sheets (if we get 50+ labeled examples)

### Integration with Other Tools
Future synergies with other repo tools:
- Drawing Set Analysis Pipeline: Auto-extract ESC sheet from full set
- Form Auto-Fill: Use validated ESC data to populate permit forms
- Code Lookup: Cross-reference detected items with DCM/TCM requirements

---

**Last Updated:** 2025-11-01
**Phase Status:** Planning complete, ready for Phase 1 implementation
**Primary Developer:** Claude (with Christian as domain expert)
