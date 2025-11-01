# Christian's Productivity Tools - Project Overview

## Purpose

This repository contains productivity automation tools for **Christian**, a civil engineer specializing in subdivision planning and drainage design in Austin, Texas.

**Primary Goal:** Automate repetitive tasks in civil engineering workflows to reclaim 150-200+ hours per year.

---

## Who is Christian?

**Role:** Civil Engineer - Subdivision Planning & Drainage Design
**Location:** Austin, Texas
**Specialization:**
- Subdivision layout and planning
- Drainage design (storm drains, open channels, culverts)
- Street and road design (cross-sections, profiles, ROW planning)
- Erosion and sediment control planning
- Permit applications and regulatory compliance

**Daily Work Involves:**
- Reviewing and creating civil engineering drawing sets (100+ page PDFs)
- Referencing Austin city codes and technical manuals (DCM, TCM, LDC)
- Processing forms and permit applications
- Quality control checks on plans before submission
- Coordinating with City of Austin Development Services

---

## Current Tools & Workflow

### Software Christian Uses:
- **CAD Software:** AutoCAD Civil 3D (likely) - for design work
- **PDF Tools:** pdfplumber, pypdf - for document processing
- **Code References:** Municode Library, eLaws, City of Austin portals
- **Data Analysis:** Python, pandas, Excel
- **OCR:** pytesseract for scanned documents

### File Types Christian Works With:
- **PDFs:** Civil engineering drawing sets with redlines (e.g., "5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf")
- **Images:** High-res plan sheet extractions (PNG, JPEG at 150-300 DPI)
- **Data:** CSV, Excel, JSON (for tables, forms, code sections)

### Current Pain Points:
1. **Code lookups take too long** - Opening browser, navigating Municode, searching, reading
2. **Drawing analysis is manual** - Scrolling through 100+ page PDFs to find specific sheets or features
3. **Form filling is repetitive** - Copy/paste same information across multiple permit forms
4. **QC checklists are tedious** - Manually verifying 15+ items on ESC sheets, drainage plans, etc.
5. **Table lookups interrupt flow** - Finding pipe sizing, ROW widths, parking calculations in technical manuals

---

## Repository Structure

```
christian-productivity/
├── CLAUDE.md                    # This file - project overview for AI
├── PLAN.md                      # Detailed implementation plan for ESC validator
├── README.md                    # User-facing documentation (to be created)
├── requirements.txt             # Python dependencies
│
├── .claude/                     # Claude Code configuration
│   ├── CLAUDE.md                # Global instructions (in user home directory)
│   └── skills/
│       └── pdf-processing-pro/  # Production PDF processing skill
│
├── docs/                        # Documentation and references
│   ├── austin-code-formats-analysis.md  # Analysis of available code formats
│   └── subdivision-code/        # Austin code references
│       ├── README.md            # Overview of code structure
│       ├── primary-code-sections.md     # Title 25 & 30 details
│       ├── technical-manuals.md         # DCM, TCM references
│       ├── quick-reference.md           # Topic-based lookups
│       └── access-strategy.md           # How to access codes
│
├── tools/                       # Automation tools (to be built)
│   └── esc-validator/           # ESC sheet validation tool (ACTIVE PROJECT)
│
├── scripts/                     # Utility scripts (existing ad-hoc tools)
│   ├── extract_page29.py        # Extract specific page from PDF
│   ├── extract_sheet26_hires.py # Extract sheet as high-res image
│   ├── search_koti_fast.py      # Search for keywords in PDF
│   ├── find_koti_way.py         # Find specific street references
│   ├── find_koti_index.py       # Build index of references
│   ├── check_specific_pages.py  # Verify page contents
│   └── check_toc.py             # Check table of contents
│
└── documents/                   # Drawing sets and reference documents
    └── 5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf
```

---

## Active Project: ESC Sheet Validator

**Status:** Planning complete, ready to start Phase 1 implementation

**Goal:** Automatically validate Erosion and Sediment Control (ESC) sheets against a 16-item checklist.

**See:** [PLAN.md](PLAN.md) for detailed implementation plan

**Why This Project?**
- High frequency task (every project requires ESC plan)
- Fixed checklist (objective validation)
- High cost of errors (permit rejections, resubmissions)
- Clear success criteria (pass/fail on each element)
- Good starting point before tackling more complex automation

**Expected ROI:**
- Current time: 15-20 min per ESC sheet review
- With tool: 5-10 min per ESC sheet review
- Savings: ~10 min per sheet × ~50 sheets/year = ~8 hours/year
- Plus: reduces errors and resubmission cycles

---

## Planned Automation Projects (Prioritized)

### Tier 1: Highest Impact
1. **Intelligent Code Lookup Tool** (Not started)
   - Offline-first searchable database of Austin codes
   - Natural language queries
   - Cross-reference suggestions
   - **Estimated savings:** 65 hours/year

2. **Drawing Set Analysis Pipeline** (Not started)
   - Auto-index large PDF drawing sets
   - Keyword search across all sheets
   - Batch image extraction
   - **Estimated savings:** 87 hours/year

### Tier 2: High Impact, Lower Effort
3. **Form Auto-Fill System** (Not started)
   - Uses existing PDF Processing Pro skill
   - Auto-populate permit applications
   - **Estimated savings:** 20 hours/year

4. **Table Extraction from Technical Manuals** (Not started)
   - Extract DCM/TCM tables to queryable database
   - Quick lookups for pipe sizing, ROW widths, parking calcs
   - **Estimated savings:** 35 hours/year

### Tier 3: Medium Impact
5. **PDF Sheet-to-Image Batch Converter** (Partially done)
   - Generalize existing manual scripts
   - **Estimated savings:** 10 hours/year

6. **Code Section Quick Reference Cards** (Not started)
   - Searchable cheat sheets
   - **Estimated savings:** 5 hours/year

### Tier 4: Future/Advanced
7. **Grade & Slope Extraction** (Not started)
   - Computer vision to extract grades from plan sheets
   - High complexity, consider Phase 2

8. **Cross-Reference Validator** (Not started)
   - Check design compliance across multiple code sections
   - Requires deep code understanding

**Total Potential Savings:** 200+ hours/year across all projects

---

## Key Reference Documents

### Austin Code & Regulations
Christian regularly references these:

**Primary Sources:**
- [Municode Library - Austin](https://library.municode.com/tx/austin) - Official code repository
  - Drainage Criteria Manual (DCM) - Storm drain design, open channels, culverts
  - Transportation Criteria Manual (TCM) - Street standards, ROW requirements
  - Title 30 - Austin/Travis County Subdivision Regulations
- [eLaws - LDC Chapter 25-6](http://austin-tx.elaws.us/code/ldc_title25_ch25-6) - Transportation/Parking
- [City of Austin Development Services](https://www.austintexas.gov/department/development-services)

**Most-Referenced Sections:**
- DCM Section 5 - Storm Drains
- DCM Section 6 - Open Channels
- DCM Section 7 - Culverts
- TCM - Street Design Standards
- LDC 25-6 - Parking Requirements
- Title 30 Chapter 30-5 - Environmental Requirements

**Access Strategy:** Currently web-based lookups, planning hybrid approach with local PDF cache (see docs/subdivision-code/access-strategy.md)

### Current Project
**Entrada East Subdivision** (Project 5620-01)
- Full civil engineering drawing set
- Active project with redlines
- Date: August 7, 2025
- Specific analysis: KOTI Way segment (stations 0+00 to 4+00)

---

## Technical Setup

### Python Environment
```bash
# Core dependencies (installed)
pip install pdfplumber pypdf pillow pytesseract pandas

# Required for ESC validator (to be installed)
pip install opencv-python opencv-contrib-python
pip install python-Levenshtein
pip install matplotlib

# Optional ML dependencies (Phase 6)
pip install ultralytics paddleocr torch torchvision
```

### System Requirements
- Python 3.8+
- Tesseract OCR (installed)
- 8GB RAM minimum (16GB recommended for ML)
- Windows 10/11 (current environment)
- Git for version control

---

## Development Guidelines

### When Working with Christian's Code:

1. **Focus on time savings** - Every tool should measurably reduce time spent on repetitive tasks

2. **Build incrementally** - Start with simple prototypes, validate with real data, then enhance

3. **Prioritize reliability** - False negatives on critical items (permit requirements) are unacceptable

4. **Use existing infrastructure** - Leverage PDF Processing Pro skill and existing scripts

5. **Document everything** - Christian needs to understand and maintain these tools

6. **Test with real drawings** - Use actual project PDFs, not synthetic test data

7. **Handle edge cases** - Drawing formats vary by drafter, project, and date

8. **Provide confidence scores** - Let Christian know when manual review is needed

### Code Quality Standards:
- Type hints for all functions
- Comprehensive error handling
- Logging for debugging
- CLI interfaces for all tools
- Unit tests for core functionality
- Clear documentation in docstrings

---

## Next Steps

### Immediate (This Week):
1. ✅ Complete ESC validator planning (DONE - see PLAN.md)
2. Gather 5-10 sample ESC sheets from Christian's projects for testing
3. Start Phase 1 implementation (text detection)
4. Test prototype on real ESC sheets

### Short-term (Next 2-4 Weeks):
1. Complete ESC validator Phases 1-3
2. Validate accuracy on diverse ESC sheets
3. Decision point: Continue to Phase 5 or pivot to ML (Phase 6)

### Medium-term (Next 1-3 Months):
1. Production-ready ESC validator
2. Start Intelligent Code Lookup Tool
3. Build Drawing Set Analysis Pipeline

### Long-term (3-6 Months):
1. Complete Tier 1 & Tier 2 automation projects
2. Measure actual time savings
3. Identify next high-value automation opportunities

---

## Success Metrics

### For ESC Validator:
- **Accuracy:** 70-80% automation of checklist (Phase 1-5) or 85-95% (Phase 6)
- **Time Savings:** Reduce review time from 15-20 min to 5-10 min per sheet
- **Error Reduction:** Zero false negatives on critical items (SCE, CONC WASH)
- **User Adoption:** Christian uses tool on every project

### For Overall Repository:
- **Time Reclaimed:** 150-200+ hours per year across all tools
- **ROI:** $25k-40k equivalent in engineer time saved annually
- **Quality Improvement:** Fewer permit resubmissions due to missing elements
- **Workflow Integration:** Tools become part of Christian's standard process

---

## Communication Preferences

When working on Christian's projects:

- **Be concise** - Engineers value clarity over verbosity
- **Show the math** - Include time savings estimates, accuracy metrics
- **Provide examples** - Use real project data when explaining concepts
- **Explain tradeoffs** - Be honest about accuracy limitations
- **Ask when uncertain** - Better to clarify requirements than build wrong thing
- **Test early** - Validate assumptions with real data quickly

---

## Project History

**2025-11-01:** Repository initialized with ESC validator planning
- Analyzed Christian's workflows and pain points
- Prioritized automation opportunities by ROI
- Created detailed implementation plan for ESC validator
- Set up project structure and documentation

**Next milestone:** Phase 1 prototype of ESC validator (Week 1)

---

## Related Files

- [PLAN.md](PLAN.md) - ESC validator implementation plan
- [docs/subdivision-code/README.md](docs/subdivision-code/README.md) - Austin code references
- [.claude/skills/pdf-processing-pro/skill.md](.claude/skills/pdf-processing-pro/skill.md) - PDF processing toolkit

---

**Last Updated:** 2025-11-01
**Project Owner:** Christian (Civil Engineer)
**AI Assistant:** Claude (via Claude Code)
