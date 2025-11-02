"""
Test the fixed ESC extraction on Entrada East PDF.
"""

from pathlib import Path
from esc_validator.extractor import find_esc_sheet
import logging

# Enable debug logging to see scores
logging.basicConfig(level=logging.DEBUG)

# Path to PDF
pdf_path = Path(__file__).parent.parent.parent / "documents" / "5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf"

print(f"Testing ESC extraction on: {pdf_path.name}")
print("=" * 80)

# Test with new thresholds and keywords
page_num = find_esc_sheet(str(pdf_path))

if page_num is not None:
    print(f"\n✅ SUCCESS: Found ESC sheet at page {page_num + 1}")
else:
    print(f"\n❌ FAILED: Could not find ESC sheet")

print("=" * 80)
