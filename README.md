# Christian's Productivity Applications

A collection of productivity tools for Christian, focusing on intelligent processing of complex surveys, charts, and long-form documents.

## Purpose

This project explores building productivity applications that can:
- Process long, complex PDF surveys and charts (beyond typical context window limits)
- Extract and analyze data from documents
- Provide intelligent summarization and insights
- Handle forms, tables, and OCR from scanned documents

## Technology Stack

### PDF Processing
- **PDF Processing Pro**: Production-ready skill with chunking capabilities
  - 1,024-token chunking with page separators
  - Progressive disclosure for large documents
  - Forms, tables, and OCR support
  - Batch processing capabilities

### Key Features
- Form analysis and field detection
- Table extraction with format preservation
- OCR for scanned documents
- Multi-page form handling
- Validation and error handling
- Batch operations for multiple PDFs

## Project Structure

```
Christian productivity/
├── .claude/                    # Claude Code skills and configuration
│   └── skills/
│       └── pdf-processing-pro/ # PDF processing skill
├── scripts/                    # Custom processing scripts
├── docs/                       # Documentation
├── examples/                   # Example workflows
└── README.md
```

## Getting Started

### Prerequisites

Install required Python packages:
```bash
pip install pdfplumber pypdf pillow pytesseract pandas
```

For OCR support, install Tesseract:
- **macOS**: `brew install tesseract`
- **Ubuntu**: `apt-get install tesseract-ocr`
- **Windows**: Download from GitHub releases

### Using PDF Processing Pro

The skill provides several ready-to-use scripts:

**Extract text from PDF:**
```bash
python .claude/skills/pdf-processing-pro/scripts/extract_text.py document.pdf --output text.txt
```

**Analyze PDF form structure:**
```bash
python .claude/skills/pdf-processing-pro/scripts/analyze_form.py survey.pdf --output schema.json
```

**Extract tables:**
```bash
python .claude/skills/pdf-processing-pro/scripts/extract_tables.py report.pdf --output tables.csv
```

## Handling Large Documents

For surveys and charts that exceed context window limits, the skill uses:

1. **Chunking**: Text is automatically split into 1,024-token segments
2. **Page Separators**: Maintains document structure and navigation
3. **Progressive Loading**: Only loads necessary sections into context
4. **Batch Processing**: Process multiple documents efficiently

### Example Workflow for Long Surveys

```python
# Process page-by-page to avoid memory issues
import pdfplumber

with pdfplumber.open("long_survey.pdf") as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
        text = page.extract_text()
        # Process each page immediately
        # Generate summary or extract key information
        print(f"Page {page_num}: {text[:200]}...")
```

## Documentation

- [SKILL.md](.claude/skills/pdf-processing-pro/SKILL.md) - Main skill documentation
- [FORMS.md](.claude/skills/pdf-processing-pro/FORMS.md) - Complete form processing guide
- [TABLES.md](.claude/skills/pdf-processing-pro/TABLES.md) - Advanced table extraction
- [OCR.md](.claude/skills/pdf-processing-pro/OCR.md) - Scanned PDF processing

## Next Steps

1. Define specific application requirements
2. Create custom processing workflows
3. Build validation and analysis tools
4. Develop user interfaces for common tasks

## License

MIT
