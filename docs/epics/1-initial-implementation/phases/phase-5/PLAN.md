# Phase 5: Improved TOC Detection & Enhanced Verbosity - Implementation Plan

**Status:** 📝 Planning
**Priority:** HIGH (Performance & UX)
**Timeline:** 3-4 hours
**Created:** 2025-11-02

---

## Overview

Phase 5 addresses two issues with the ESC validator:

1. **TOC detection fails too often** → causing slow full-PDF scans (5-15 seconds wasted)
2. **No user feedback** → users don't know what the tool is doing

**Goal:** Improve existing TOC detection to work >80% of the time, and add progress indicators so users see what's happening.

---

## Problem Analysis

### Current Implementation (extractor.py)

The validator ALREADY has TOC detection (`find_toc_esc_reference()` at extractor.py:22-87), but it fails too often:

```python
def find_toc_esc_reference(pdf_path: str, max_toc_pages: int = 10) -> Optional[int]:
    """Find ESC sheet by searching for Table of Contents."""

    # Problem 1: Limited TOC keyword patterns
    toc_indicators = [
        "SHEET INDEX",
        "DRAWING LIST",
        "SHEET LIST",
        "INDEX OF SHEETS",
        "TABLE OF CONTENTS"
    ]

    # Problem 2: Only looks for ESC in TOC lines
    if any(keyword in line_upper for keyword in ["ESC", "EROSION", "SEDIMENT CONTROL"]):
        # Problem 3: Strict regex for page number extraction
        page_match = re.search(r'\b(\d{1,3})\b\s*$', line)
```

**What happens when TOC detection fails:**
1. Tool falls back to `find_esc_sheet()` (line 90-229)
2. Scans EVERY page in the PDF (could be 100+ pages)
3. Scores each page with weighted keywords
4. Takes 5-15 seconds vs <1 second with TOC

**Current success rate:** Estimated ~30-50% (needs measurement)

---

## Solution Design

### Part 1: Improve TOC Detection (1.5 hours)

**Goal:** Increase TOC detection success rate from ~30-50% to >80%

**Strategy: Expand Pattern Matching**

#### 1.1 More TOC Keywords (15 min)

Add patterns observed in civil engineering drawing sets:

```python
# Current
toc_indicators = ["SHEET INDEX", "DRAWING LIST", "SHEET LIST", "INDEX OF SHEETS", "TABLE OF CONTENTS"]

# After Phase 5
toc_indicators = [
    # Existing
    "SHEET INDEX", "DRAWING LIST", "SHEET LIST", "INDEX OF SHEETS", "TABLE OF CONTENTS",
    # New - civil engineering variations
    "PLAN INDEX", "DRAWING INDEX", "SHEET LISTING", "PLAN LISTING",
    "CONTENTS", "INDEX",  # Standalone (if early in PDF)
    # Abbreviations
    "TBL OF CONTENTS", "T.O.C", "TOC",
    # With sheet numbers
    "SHEET", "DRAWING"  # If followed by C1.0, C2.0 patterns
]
```

#### 1.2 More ESC Keywords (15 min)

Expand ESC detection in TOC lines:

```python
# Current
esc_keywords = ["ESC", "EROSION", "SEDIMENT CONTROL"]

# After Phase 5
esc_keywords = [
    # Existing
    "ESC", "EROSION", "SEDIMENT CONTROL",
    # Variations
    "E&SC", "E & SC", "E.S.C", "EC",  # Abbreviations
    "EROSION CONTROL", "SEDIMENT",
    "SWPPP", "POLLUTION PREVENTION",  # Related
    # Sheet numbers
    "ESC-", "EC-", "ESC ", "EC "  # Followed by numbers
]
```

#### 1.3 Better Page Number Extraction (30 min)

Add multiple extraction strategies:

```python
def extract_page_number_from_toc_line(line: str, next_line: str = "") -> Optional[int]:
    """
    Extract page number from TOC line with multiple strategies.

    Tries in order:
    1. Number at end of line: "EROSION CONTROL ... 26"
    2. Number in next line: "26" (standalone)
    3. Number in parentheses: "EROSION CONTROL (26)"
    4. Number with "PAGE": "PAGE 26" or "PG. 26"
    5. Number range (take first): "26-28" → 26
    """

    # Strategy 1: Number at end of line (current implementation)
    match = re.search(r'\b(\d{1,3})\b\s*$', line)
    if match:
        return int(match.group(1))

    # Strategy 2: Number range at end (e.g., "26-28")
    match = re.search(r'\b(\d{1,3})-\d{1,3}\b\s*$', line)
    if match:
        return int(match.group(1))

    # Strategy 3: Number in parentheses
    match = re.search(r'\((\d{1,3})\)', line)
    if match:
        return int(match.group(1))

    # Strategy 4: Number with "PAGE" keyword
    match = re.search(r'(?:PAGE|PG\.?)\s*(\d{1,3})', line, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Strategy 5: Standalone number in next line
    if next_line:
        match = re.search(r'^\s*(\d{1,3})\s*$', next_line)
        if match:
            return int(match.group(1))

    return None
```

#### 1.4 Logging for TOC Detection (30 min)

Add detailed logging to understand why TOC detection fails:

```python
def find_toc_esc_reference(pdf_path: str, max_toc_pages: int = 10) -> Optional[int]:
    """Find ESC sheet by searching for Table of Contents."""
    logger.info(f"Searching for TOC in first {max_toc_pages} pages")

    toc_found = False
    esc_found_in_toc = False

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(min(max_toc_pages, len(pdf.pages))):
            text = pdf.pages[page_num].extract_text() or ""

            # Check for TOC indicators
            is_toc, matched_pattern = is_toc_page(text)

            if is_toc:
                toc_found = True
                logger.info(f"✓ Found TOC on page {page_num + 1} (pattern: '{matched_pattern}')")

                # Look for ESC reference
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if is_esc_line(line):
                        logger.debug(f"  TOC line with ESC: {line}")

                        next_line = lines[i + 1] if i + 1 < len(lines) else ""
                        page_number = extract_page_number_from_toc_line(line, next_line)

                        if page_number:
                            esc_found_in_toc = True
                            logger.info(f"✓ Found ESC sheet in TOC: page {page_number + 1}")
                            return page_number - 1  # Convert to 0-indexed
                        else:
                            logger.warning(f"✗ ESC line found but no page number: {line}")

    # Diagnostic logging
    if not toc_found:
        logger.warning("✗ No TOC found in first {max_toc_pages} pages - falling back to full scan")
    elif not esc_found_in_toc:
        logger.warning("✗ TOC found but no ESC reference - falling back to full scan")

    return None
```

---

### Part 2: Add Progress Indicators (1 hour)

**Goal:** Show users what the tool is doing during validation

**Strategy: Wrap Each Phase with Progress Messages**

#### 2.1 Update validator.py (45 min)

Add step counters and timing to main validation workflow:

```python
import time
from typing import Dict, Optional

def validate_esc_sheet(
    pdf_path: str,
    sheet_keyword: str = "ESC",
    page_num: Optional[int] = None,
    dpi: int = 300,
    save_images: bool = False,
    output_dir: Optional[str] = None,
    enable_line_detection: bool = False,
    enable_quality_checks: bool = False,
    ocr_engine: str = "paddleocr",
    verbose: bool = False  # NEW
) -> Dict[str, any]:
    """
    Complete ESC sheet validation workflow with progress indicators.
    """

    total_steps = 5  # Count of major steps
    start_time = time.time()

    # Step 1: Find ESC sheet
    if verbose:
        print(f"[1/{total_steps}] Searching for ESC sheet...")
    step_start = time.time()

    if page_num is None:
        page_num = find_esc_sheet(pdf_path, sheet_keyword)
        if page_num is None:
            return {"success": False, "errors": ["ESC sheet not found"]}

    if verbose:
        print(f"      ✓ Found ESC sheet: page {page_num + 1} ({time.time() - step_start:.1f}s)")

    # Step 2: Extract page
    if verbose:
        print(f"[2/{total_steps}] Extracting page {page_num + 1}...")
    step_start = time.time()

    image = extract_esc_sheet(pdf_path, page_num, dpi)

    if verbose:
        print(f"      ✓ Image extracted ({time.time() - step_start:.1f}s)")

    # Step 3: Text detection
    if verbose:
        print(f"[3/{total_steps}] Running text detection...")
    step_start = time.time()

    detection_results = detect_required_labels(image, ocr_engine=ocr_engine)

    if verbose:
        detected_count = sum(1 for r in detection_results.values() if r.detected)
        total_count = len(detection_results)
        print(f"      ✓ {detected_count}/{total_count} elements detected ({time.time() - step_start:.1f}s)")

    # Step 4: Line analysis (if enabled)
    if enable_line_detection:
        if verbose:
            print(f"[4/{total_steps}] Running contour analysis...")
        step_start = time.time()

        contour_results = verify_contour_conventions(image, detection_results)

        if verbose:
            contour_count = len(contour_results.get("contour_lines", []))
            print(f"      ✓ {contour_count} contours validated ({time.time() - step_start:.1f}s)")

    # Step 5: Generate report
    if verbose:
        print(f"[5/{total_steps}] Generating report...")
    step_start = time.time()

    # ... report generation ...

    if verbose:
        print(f"      ✓ Report saved ({time.time() - step_start:.1f}s)")
        print(f"\n✓ Validation complete in {time.time() - start_time:.1f} seconds")

    return results
```

#### 2.2 Update validate_esc.py CLI (15 min)

Add `-v`/`--verbose` and `--quiet` flags:

```python
def main():
    parser = argparse.ArgumentParser(...)

    # Existing --debug flag (line 297)
    # Add new verbosity flags

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed progress and timing information'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress all output except errors'
    )

    args = parser.parse_args()

    # Configure logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)  # Normal mode

    # Pass verbose flag to validator
    results = validate_esc_sheet(
        pdf_path=args.pdf_files[0],
        ...,
        verbose=args.verbose  # NEW
    )
```

---

### Part 3: Testing (0.5 hours)

#### 3.1 Test TOC Detection Improvements

**Test on 5-10 diverse drawing sets:**

| Drawing Set | TOC Format | Before (success?) | After (success?) |
|-------------|------------|-------------------|------------------|
| Entrada East | "SHEET INDEX" | ✓ Yes | ✓ Yes |
| Project 2 | "DRAWING LIST" | ✗ No (fallback) | ? |
| Project 3 | "CONTENTS" only | ✗ No (fallback) | ? |
| Project 4 | No TOC | ✗ No (fallback) | ✗ No (expected) |
| ... | ... | ... | ... |

**Success criteria:**
- TOC detection rate: >80% (up from ~30-50%)
- No regressions (previously working PDFs still work)
- Fallback still works when TOC truly doesn't exist

#### 3.2 Test Verbosity Output

**Verify all verbosity levels work:**

```bash
# Quiet mode (errors only)
python validate_esc.py drawing.pdf --quiet

# Normal mode (default - minimal output)
python validate_esc.py drawing.pdf

# Verbose mode (progress indicators)
python validate_esc.py drawing.pdf --verbose

# Debug mode (existing - everything)
python validate_esc.py drawing.pdf --debug
```

---

## Implementation Checklist

### TOC Detection Improvements (1.5 hours)

- [ ] Add expanded TOC keyword patterns (15 min)
- [ ] Add expanded ESC keyword patterns (15 min)
- [ ] Implement multi-strategy page number extraction (30 min)
- [ ] Add detailed logging for TOC detection path (30 min)
- [ ] Test on 5+ diverse drawing sets (20 min)

### Progress Indicators (1 hour)

- [ ] Add step counters to `validator.py` (30 min)
- [ ] Add timing per phase (15 min)
- [ ] Update CLI flags in `validate_esc.py` (15 min)
- [ ] Test all verbosity levels (10 min)

### Documentation (0.5 hours)

- [ ] Update user README with verbosity examples (15 min)
- [ ] Document TOC detection improvements (10 min)
- [ ] Add troubleshooting guide for TOC failures (10 min)

---

## Expected Outcomes

### Performance

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| TOC detection rate | ~30-50% | >80% | +30-50% |
| Time when TOC works | <1 second | <1 second | No change |
| Time when TOC fails | 5-15 seconds | 5-15 seconds | No change |
| **Average time** | **3-8 seconds** | **<2 seconds** | **60-75% faster** |

### User Experience

**Before:**
```
[No output - black box]
[15 seconds pass...]
✅ Validation passed
```

**After (verbose):**
```
[1/5] Searching for ESC sheet...
      ✓ Found via TOC: page 26 (0.8s)
[2/5] Extracting page 26...
      ✓ Image extracted (1.2s)
[3/5] Running text detection...
      ✓ 12/12 elements detected (6.8s)
[4/5] Running contour analysis...
      ✓ 9 contours validated (4.2s)
[5/5] Generating report...
      ✓ Report saved (0.5s)

✓ Validation complete in 13.5 seconds
```

---

## Risks & Mitigations

### Risk 1: TOC patterns still don't match some drawing sets
**Impact:** Medium
**Likelihood:** Medium

Even with expanded patterns, some drawing sets may use unique TOC formats.

**Mitigation:**
- Keep full-scan fallback (no worse than current behavior)
- Log TOC failures to identify missing patterns
- Can add more patterns in future updates

---

### Risk 2: Progress output clutters batch processing
**Impact:** Low
**Likelihood:** Low

Verbose output may be unwanted when processing multiple files.

**Mitigation:**
- Default to quiet mode for batch processing
- Users can opt-in to verbose with `-v` flag
- `--quiet` flag suppresses all non-error output

---

### Risk 3: Performance regression
**Impact:** Low
**Likelihood:** Very Low

Additional pattern matching could slow down TOC detection.

**Mitigation:**
- TOC search only checks first 10 pages (same as current)
- Regex patterns are compiled once
- Measure performance before/after

---

## Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| TOC detection rate | >80% | Test on 10 diverse drawing sets |
| TOC lookup time | <1 second | Time `find_toc_esc_reference()` |
| Full-scan fallback rate | <20% | Count TOC failures / total runs |
| User sees progress | Always | Visual inspection of `-v` output |
| No performance regression | <5% slower | Compare before/after timing |

---

## Timeline

| Task | Duration | Dependencies |
|------|----------|--------------|
| Expand TOC/ESC keywords | 0.5 hours | None |
| Multi-strategy page extraction | 0.5 hours | None |
| Add logging to TOC detection | 0.5 hours | Keywords done |
| Add progress indicators | 1 hour | None |
| Testing & validation | 0.5 hours | All code complete |
| Documentation | 0.5 hours | Testing complete |
| **Total** | **3-4 hours** | - |

---

## Future Enhancements (Phase 5.1+)

### Phase 5.1: Full Sheet Indexing
- Build complete index of ALL sheets from TOC
- Cache index as `.esc_index.json`
- Allow sheet selection by number: `--sheet C2.0`
- **Effort:** 2-3 hours
- **Priority:** LOW (nice-to-have)

### Phase 5.2: Progress Bars
- Visual progress bars for long operations
- ETA estimation
- Better for batch processing
- **Effort:** 1-2 hours
- **Priority:** LOW (cosmetic)

---

## References

- **Current Implementation:** [tools/esc-validator/esc_validator/extractor.py](../../../../../tools/esc-validator/esc_validator/extractor.py) (lines 22-229)
- **Validator Workflow:** [tools/esc-validator/esc_validator/validator.py](../../../../../tools/esc-validator/esc_validator/validator.py)
- **CLI Interface:** [tools/esc-validator/validate_esc.py](../../../../../tools/esc-validator/validate_esc.py)

---

**Created:** 2025-11-02
**Author:** Claude (AI Assistant)
**Status:** Ready to implement
**Estimated Effort:** 3-4 hours
