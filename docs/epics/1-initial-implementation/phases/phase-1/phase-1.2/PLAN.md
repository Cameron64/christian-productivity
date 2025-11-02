# Phase 1.2: Text-Only Detection Improvements

**Status:** Not Started
**Priority:** P1 (High)
**Expected Duration:** 1-2 days
**Prerequisites:** Phase 1.1 complete
**Focus:** Text detection improvements without visual/symbol detection

---

## Overview

Phase 1.2 focuses on **text-based detection improvements** to address critical gaps found in Phase 1.1 testing:

1. **Streets labeled** - 194 false positives from keyword matching
2. **North bar** - 998 false positives (but actual graphic symbol present)

**Scope:** Text-only improvements. Visual detection (symbols, lines) deferred to Phase 1.3.

---

## Problems to Address

### Problem 1: Streets Labeled False Positives

**Phase 1.1 Results:**
```
Streets Labeled: ✗ 194 occurrences
Notes: "Excessive occurrences (194), likely false positive from notes/text"
```

**Root Cause:**
- Keywords like "st", "dr", "way", "street" appear constantly in notes
- Example: "street design standards", "all streets shall...", "way to install"
- No distinction between actual street name labels vs. mentions

**Impact:** Cannot reliably detect if streets are labeled

---

### Problem 2: North Bar Detection

**Phase 1.1 Results:**
```
North Bar: ✗ 998 occurrences
Notes: "Excessive occurrences (998), likely false positive from notes/text"
```

**Reality:** North arrow graphic IS present on sheet (confirmed via screenshot)

**Root Cause:**
- OCR detecting "north" in text (street names, directions, notes)
- Cannot detect graphic symbols with text-only OCR

**Impact:** False negative on required element

---

## Solution Approach (Text-Only)

### For Streets: Smart Pattern Matching

**Strategy:** Look for proper street name patterns, not just keywords

**Detection Logic:**
```python
# Bad (current): Generic keywords
keywords = ["street", "st", "way", "dr"]  # Too broad!

# Good (Phase 1.2): Pattern-based
pattern = r'[A-Z][a-z]+\s+(Street|Blvd|Drive|Way|Rd)'
# Finds: "William Cannon Dr", "Koti Way"
# Ignores: "street design", "way to install"
```

**Additional Filtering:**
- Skip notes sections (long sentences, lowercase)
- Require Title Case or ALL CAPS (proper nouns)
- Extract full street names, not just suffixes

**Limitation:** Can only count labels found, not verify ALL streets are labeled (no visual detection)

---

### For North Bar: Acknowledge Limitation

**Reality:** Text-only OCR cannot detect graphic symbols

**Options for Phase 1.2:**

**Option A (Recommended):** Mark as "Manual Verification Required"
```python
# Accept that we can't detect graphics in Phase 1.2
notes = "North arrow detection requires symbol matching (Phase 1.3)"
confidence = 0.0
detected = False
```

**Option B:** Proxy Detection via Text
```python
# Look for single "N" or "NORTH" in expected location
# High false positive risk, not recommended
```

**Decision:** Defer to Phase 1.3 (symbol detection), mark as manual check for now

---

## Implementation Plan

### Task 1: Implement Smart Street Name Detection

**File:** `text_detector.py`

**Add new function:**

```python
def detect_street_labels_smart(text: str) -> Tuple[bool, int, List[str]]:
    """
    Detect actual street name labels using pattern matching.

    Filters out mentions in notes/text and focuses on proper street names.

    Returns:
        (detected, count, street_names)
    """

    # Street name patterns
    # Format: "Name + Suffix" in Title Case or ALL CAPS
    patterns = [
        # Title Case: "North Loop Blvd"
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(Street|St|Boulevard|Blvd|Drive|Dr|Way|Lane|Ln|Road|Rd|Avenue|Ave|Court|Ct|Circle|Cir|Place|Pl)\b',
        # ALL CAPS: "WILLIAM CANNON DR"
        r'\b([A-Z\s]+)\s+(STREET|ST|BOULEVARD|BLVD|DRIVE|DR|WAY|LANE|LN|ROAD|RD|AVENUE|AVE|COURT|CT|CIRCLE|CIR|PLACE|PL)\b'
    ]

    street_names = set()
    lines = text.split('\n')

    for line in lines:
        # Skip notes sections
        if is_likely_notes_section(line):
            continue

        # Find street name patterns
        for pattern in patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                # match is tuple: (name, suffix)
                full_name = f"{match[0].strip()} {match[1]}"
                street_names.add(full_name)

    detected = len(street_names) > 0
    count = len(street_names)

    return detected, count, list(street_names)


def is_likely_notes_section(line: str) -> bool:
    """
    Determine if line is from notes/text rather than plan labels.

    Notes characteristics:
    - Long lines (>100 chars)
    - Mostly lowercase
    - Contains common note words
    """

    # Too long = notes
    if len(line) > 100:
        return True

    # Count lowercase vs uppercase
    lowercase_count = sum(1 for c in line if c.islower())
    uppercase_count = sum(1 for c in line if c.isupper())

    # Mostly lowercase = notes
    if lowercase_count > uppercase_count * 2:
        return True

    # Common note indicators
    note_words = [
        'shall', 'shall be', 'must', 'contractor', 'the ', 'all ',
        'requirements', 'standards', 'prior to', 'in accordance'
    ]

    line_lower = line.lower()
    if any(word in line_lower for word in note_words):
        return True

    return False
```

**Integrate into `detect_required_labels()`:**

```python
# In detect_required_labels()

if element == "streets":
    # Use smart detection instead of generic keywords
    detected, count, matches = detect_street_labels_smart(full_text)

    # Set confidence
    if count == 0:
        confidence = 0.0
    elif count <= 20:  # Reasonable range
        confidence = 0.75  # Good confidence, but can't verify completeness
        notes = f"Found {count} labeled street(s)"
    else:  # Suspiciously high
        confidence = 0.4
        detected = False
        notes = f"Found {count} potential streets - verify manually"

    results[element] = DetectionResult(
        element=element,
        detected=detected,
        confidence=confidence,
        count=count,
        matches=matches[:10],  # Show first 10
        notes=notes
    )
    continue  # Skip normal keyword detection
```

**Deliverable:** Updated `text_detector.py` with smart street detection

**Time:** 3 hours

---

### Task 2: Update North Bar Detection Logic

**File:** `text_detector.py`

**Update detection for north_bar:**

```python
# In detect_required_labels()

if element == "north_bar":
    # Phase 1.2: Acknowledge limitation - can't detect graphic symbols
    # Mark for manual verification

    # Check if "north" appears, but with low confidence
    north_count = full_text.upper().count('NORTH')

    if north_count > 50:
        # Probably false positive from notes
        detected = False
        confidence = 0.0
        notes = "Text-only detection unreliable for graphic symbols. Manual verification required. Symbol detection in Phase 1.3."
    elif 1 <= north_count <= 10:
        # Might be present
        detected = True
        confidence = 0.3  # Low confidence - could be text or symbol
        notes = "Possible north arrow detected. Verify manually. Full detection in Phase 1.3."
    else:
        detected = False
        confidence = 0.0
        notes = "No north arrow detected via text. Symbol detection available in Phase 1.3."

    results[element] = DetectionResult(
        element=element,
        detected=detected,
        confidence=confidence,
        count=north_count if north_count <= 10 else 0,
        matches=[],
        notes=notes
    )
    continue
```

**Deliverable:** Updated north bar detection with manual verification guidance

**Time:** 1 hour

---

### Task 3: Update Reporter for Phase 1.2 Limitations

**File:** `reporter.py`

**Add note about Phase 1.2 limitations:**

```python
# In generate_markdown_report(), after checklist table

lines.append("## Phase 1.2 Limitations")
lines.append("")
lines.append("**Text-Only Detection:**")
lines.append("")
lines.append("This report uses Phase 1.2 text-based detection. The following limitations apply:")
lines.append("")
lines.append("- **North Bar:** Graphic symbols cannot be detected with OCR alone. Manual verification required.")
lines.append("- **Streets Labeled:** Can detect labeled street names, but cannot verify if ALL streets are labeled.")
lines.append("")
lines.append("For complete detection including symbols and visual verification, see Phase 1.3.")
lines.append("")
```

**Deliverable:** Updated reporter with limitation notices

**Time:** 30 minutes

---

### Task 4: Test on Page 16

**Expected Results:**

**Before (Phase 1.1):**
```
Streets: ✗ 194 occurrences (false positive)
North Bar: ✗ 998 occurrences (false positive)
```

**After (Phase 1.2):**
```
Streets: ✓ 0-3 street names found
  Matches: [] or ["William Cannon Dr", ...]
  Notes: "Found 0 labeled street(s)" (ESC Notes sheet may have no streets)

North Bar: ✗ Not detected
  Notes: "Text-only detection unreliable for graphic symbols.
         Manual verification required. Symbol detection in Phase 1.3."
```

**Success Criteria:**
- ✅ No more 194/998 false positive warnings
- ✅ Street detection shows realistic counts
- ✅ Clear notes about limitations
- ✅ User knows to verify manually or wait for Phase 1.3

**Deliverable:** Test report comparing Phase 1.1 vs 1.2

**Time:** 1 hour

---

## Success Criteria

### Overall Phase 1.2 Success

**Must Have (Required):**
- ✅ Smart street name detection implemented
- ✅ False positive rate on streets <10%
- ✅ North bar detection updated with limitation notes
- ✅ Reporter shows Phase 1.2 limitations clearly
- ✅ Test on Page 16 passes

**Should Have (Important):**
- ✅ Street detection: realistic counts (0-15 per sheet)
- ✅ Street names extracted correctly (proper nouns)
- ✅ No regressions on other text elements
- ✅ Processing time still <30 seconds

**Nice to Have (Optional):**
- ⏳ Visualization of detected street names
- ⏳ Confidence adjustments based on sheet type
- ⏳ Additional pattern variations

---

## What's NOT in Phase 1.2

**Deferred to Phase 1.3:**
- ❌ North arrow symbol detection (requires template matching)
- ❌ Visual street counting (requires line detection)
- ❌ Symbol detection for silt fence, SCE, etc.
- ❌ Spatial filtering (OCR bounding boxes)
- ❌ Graphic element verification

Phase 1.2 is **text-only**. Visual detection comes in Phase 1.3.

---

## Testing Plan

### Test Case 1: Street Detection on Notes Sheet

**Input:** Page 16 (Erosion Control Notes)
**Expected:** Low count (0-3), no false positives
**Verify:**
- No "194 occurrences" warning
- Realistic count
- Clear notes

### Test Case 2: North Bar on Notes Sheet

**Input:** Page 16 (has north arrow graphic)
**Expected:** Not detected, manual verification note
**Verify:**
- No "998 occurrences" warning
- Clear limitation message
- Directs user to Phase 1.3 or manual check

---

## Timeline

**Day 1:**
- Morning: Implement smart street detection (3 hours)
- Afternoon: Update north bar logic + reporter (1.5 hours)
- Evening: Test on Page 16 (1 hour)

**Total:** 5.5 hours (~1 day)

---

## Deliverables

### Code Changes
1. Updated `text_detector.py`:
   - `detect_street_labels_smart()` function
   - `is_likely_notes_section()` helper
   - Updated `detect_required_labels()` for streets and north_bar
2. Updated `reporter.py`:
   - Phase 1.2 limitations section

### Documentation
1. Test report: Phase 1.1 vs 1.2 comparison
2. Limitation notes in validation report

---

## Acceptance Criteria

Phase 1.2 is **COMPLETE** when:

1. ✅ Smart street detection implemented
2. ✅ False positives eliminated (<10%)
3. ✅ North bar shows clear limitation message
4. ✅ Reporter explains what Phase 1.2 can/can't do
5. ✅ Test on Page 16 passes
6. ✅ No regressions on other elements

Phase 1.2 is **SUCCESSFUL** when:

1. ✅ All acceptance criteria met
2. ✅ Users understand limitations clearly
3. ✅ Street detection: 0-15 realistic range
4. ✅ No false negative warnings
5. ✅ Sets stage for Phase 1.3

---

## Next Steps After Phase 1.2

**Phase 1.3:** Add visual detection for:
- North arrow symbol (template matching)
- Street count verification (line detection)
- Complete street labeling verification

---

**Status:** Ready to implement
**Estimated LOC:** ~150 lines of changes
**Estimated Time:** 1 day
**Priority:** P1 (High - eliminates false positives)

---

**Created:** 2025-11-01
**Owner:** Claude (via Claude Code)
**For:** Christian's Productivity Tools - ESC Validator
