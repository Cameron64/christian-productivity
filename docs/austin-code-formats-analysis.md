# City of Austin Code - Available Formats Analysis

## Executive Summary

City of Austin building codes, ordinances, and regulations are available in multiple formats. However, **there is no official API** for programmatic access. This analysis covers all available formats and access methods.

---

## 1. Primary Format: Municode Web Platform (HTML)

**Access:** https://library.municode.com/tx/austin

### What's Available:
- **Code of Ordinances** - Complete city ordinances
- **Land Development Code (LDC)** - Title 25 (development regulations) + Title 30 (subdivision)
- **Administrative Rules**
- **Technical Criteria Manuals** (8 different manuals)

### Format Details:
- **Type:** HTML-based web interface
- **Backend:** Azure Blob Storage for content
- **Navigation:** Hierarchical structure with sections/subsections
- **Search:** Built-in search functionality
- **Export:** PDF rendering available (via Adobe PDF Embed API)

### Pros:
✅ Official source
✅ Always up-to-date
✅ Free access
✅ Searchable
✅ Can generate PDFs of sections

### Cons:
❌ No official API
❌ No bulk download option
❌ Requires web scraping for programmatic access
❌ Content in HTML format requires parsing

---

## 2. PDF Downloads (Limited)

**Access:** Various city resources and Municode ordinance downloads

### What's Available:
- Individual ordinances (via Municode download)
- Technical manuals (Building Criteria Manual, etc.)
- Specific guides and amendments
- Code interpretation documents

### Format Details:
- **Type:** PDF documents
- **Source:** Azure Functions endpoint: `https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/`
- **Availability:** Individual sections, not complete code

### Pros:
✅ Readable format
✅ Can be processed with PDF tools
✅ Offline access

### Cons:
❌ Not comprehensive (only specific sections)
❌ Manual download required
❌ May not be latest version
❌ Large file sizes

---

## 3. Excel/Structured Data (Very Limited)

**Access:** Specific regulatory tables on austintexas.gov

### What's Available:
- Site Development Regulation Tables
- Specific zoning tables
- Limited data exports

### Format Details:
- **Type:** Excel spreadsheets (.xlsx)
- **Availability:** Only for specific regulatory tables
- **Coverage:** Very limited subset of code

### Pros:
✅ Structured data
✅ Easy to work with programmatically

### Cons:
❌ Extremely limited coverage
❌ Only specific tables available
❌ Not comprehensive

---

## 4. Open Data Portal API (Permits/Data, NOT Code Text)

**Access:** https://data.austintexas.gov

### What's Available:
- **Issued Construction Permits** - Building, electrical, mechanical, plumbing permits
- **Site Plan Cases** - Development case information
- **GIS Data** - Mapping and geographic data
- **NOT AVAILABLE:** Actual ordinance/code text

### Format Details:
- **Type:** Socrata Open Data API (SODA)
- **Format:** JSON, CSV, XML
- **Features:** Filter, query, aggregate data

### Pros:
✅ True API access
✅ Multiple data formats
✅ Good for permit/case data

### Cons:
❌ Does NOT contain code text or ordinances
❌ Only for operational data (permits, cases, etc.)
❌ Not useful for code lookups

---

## 5. Web Scraping (Unofficial)

**Access:** Custom scraping solutions

### Available Tools:
1. **noclocks/municode-scraper** (GitHub)
   - Python + Selenium WebDriver
   - Scrapes ordinances and resolutions
   - Downloads documents locally

2. **dkylewillis/municode-scraper-lib** (GitHub - 404'd)
   - Library for scraping Municode
   - Exports to HTML and JSON
   - May no longer be maintained

### Format Details:
- **Type:** Custom extraction from HTML
- **Output:** JSON, HTML, structured data
- **Reliability:** Unofficial, subject to website changes

### Pros:
✅ Can create structured database
✅ Programmatic access
✅ Custom output formats

### Cons:
❌ Unofficial/unsupported
❌ May break if website changes
❌ Legal/ethical considerations
❌ Maintenance burden
❌ May violate terms of service

---

## 6. Third-Party Aggregators

### UpCodes
**Access:** https://up.codes/codes/austin

- Aggregates building codes
- Web interface similar to Municode
- May have API (commercial)

### eLaws
**Access:** http://austin-tx.elaws.us/code/coor

- Alternative code viewer
- HTML format
- Free access

---

## Recommendations for Christian's Use Case

### Option A: Hybrid Approach (Recommended)
1. **For regular lookups:** Use Municode web interface
2. **For specific sections:** Download PDFs from Municode
3. **For processing:** Build a lightweight web scraper (Python + BeautifulSoup)
4. **For storage:** Cache frequently accessed sections locally as structured JSON

### Option B: Cache-First Strategy
1. Build a scraper to download entire code sections once
2. Store as structured data (JSON/SQLite)
3. Update cache monthly/quarterly
4. Use local cache for lookups
5. Fall back to web for latest info

### Option C: PDF-Based Workflow
1. Download relevant PDF sections from Municode
2. Use PDF Processing Pro skill for extraction
3. Build searchable index from extracted text
4. Update PDFs periodically

---

## Implementation Considerations

### Legal/Ethical:
- ⚠️ Municode terms of service should be reviewed before scraping
- ✅ Austin codes are public information
- ✅ Caching for personal use likely acceptable
- ❌ Republishing or commercial use may have restrictions

### Technical:
- **Web Scraping Complexity:** Medium (hierarchical navigation)
- **Update Frequency:** Codes change periodically (monthly/quarterly updates needed)
- **Storage Requirements:** ~500MB-2GB for complete code (estimated)
- **Processing Time:** Several hours for full scrape

### Maintenance:
- Website structure may change
- Scraper would need updates
- Manual verification of accuracy recommended

---

## Next Steps for Christian's Productivity App

1. **Define specific use cases:** What code sections does she need most often?
2. **Choose access strategy:** Based on frequency and coverage needs
3. **Build proof of concept:** Test with one code section
4. **Evaluate performance:** Speed, accuracy, maintenance
5. **Scale as needed:** Expand to more sections

### Recommended Stack:
```python
# Web scraping
- requests / httpx
- BeautifulSoup4 or lxml
- selenium (if JavaScript required)

# Storage
- SQLite for local cache
- JSON for structured data

# Search
- Whoosh or SQLite FTS for full-text search
- Elasticsearch for advanced search (if needed)

# PDF Processing (for downloaded PDFs)
- Use installed PDF Processing Pro skill
```

---

## Summary Table

| Format | Availability | Coverage | Update Freq | Programmatic Access | Cost |
|--------|-------------|----------|-------------|---------------------|------|
| Municode HTML | ✅ Excellent | Complete | Real-time | ❌ No API (scraping only) | Free |
| PDF Downloads | ⚠️ Limited | Sections only | Manual | ✅ Yes (after download) | Free |
| Excel Data | ❌ Very Limited | Tables only | Manual | ✅ Yes | Free |
| Open Data API | ✅ Excellent | Permits/Cases ONLY | Real-time | ✅ Yes | Free |
| Web Scraping | ⚠️ Custom | Custom | Custom | ✅ Yes | Dev time |
| UpCodes | ✅ Good | Building codes | Unknown | ⚠️ Maybe (commercial) | Free/Paid |

**Bottom Line:** For comprehensive code text access, web scraping Municode is the only programmatic option since no official API exists for code content.
