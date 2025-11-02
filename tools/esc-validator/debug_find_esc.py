"""
Debug script to identify ESC sheet in Entrada East PDF.

Scans all pages and shows detailed scoring breakdown.
"""

import pdfplumber
import re
from pathlib import Path

def score_page(text: str) -> dict:
    """Score a page and return detailed breakdown."""
    text_upper = text.upper()
    scores = {}

    # High-value indicators (5 points each)
    if "ESC" in text_upper and "PLAN" in text_upper:
        scores["ESC + PLAN"] = 5
    if "EROSION AND SEDIMENT CONTROL PLAN" in text_upper:
        scores["Full phrase"] = 5
    if re.search(r'\b(ESC|EC)[-\s]?\d+\b', text_upper):
        scores["Sheet number pattern"] = 5

    # Medium-value indicators (2 points each)
    if "SILT FENCE" in text_upper:
        scores["Silt fence"] = 2
    if "CONSTRUCTION ENTRANCE" in text_upper or "STABILIZED CONSTRUCTION ENTRANCE" in text_upper:
        scores["Construction entrance"] = 2
    if "CONCRETE WASHOUT" in text_upper or "WASHOUT" in text_upper:
        scores["Washout"] = 2

    # Low-value indicators (1 point each)
    if "EROSION" in text_upper:
        scores["Erosion"] = 1
    if "SEDIMENT" in text_upper:
        scores["Sediment"] = 1

    return scores

# Path to PDF
pdf_path = Path(__file__).parent.parent.parent / "documents" / "5620-01 Entrada East 08.07.2025 FULL SET-redlines.pdf"

print(f"Scanning: {pdf_path}")
print("=" * 80)

results = []

with pdfplumber.open(pdf_path) as pdf:
    total_pages = len(pdf.pages)
    print(f"Total pages: {total_pages}\n")

    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        scores = score_page(text)
        total_score = sum(scores.values())

        if total_score >= 5:  # Show pages with at least 5 points
            results.append((page_num, total_score, scores, text[:500]))

# Sort by score (highest first)
results.sort(key=lambda x: x[1], reverse=True)

# Show top candidates
print("TOP CANDIDATES:")
print("=" * 80)

for page_num, total_score, scores, text_preview in results[:10]:
    print(f"\nPage {page_num + 1} - Score: {total_score}")
    print("-" * 40)
    for keyword, points in scores.items():
        print(f"  {keyword}: {points} pts")
    print(f"\nText preview:")
    print(text_preview[:300])
    print("..." if len(text_preview) > 300 else "")
    print()

if results:
    best_page, best_score, best_scores, _ = results[0]
    print("=" * 80)
    print(f"BEST MATCH: Page {best_page + 1} with score {best_score}")
    print(f"Missing threshold by: {10 - best_score} point(s)")
else:
    print("No pages found with score >= 5")
