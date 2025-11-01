# Access Strategy

## Recommended Workflow for Christian

### Option 1: Web-Based Lookups (Current Best Option)

**For regular reference:**

1. **Bookmark key Municode pages:**
   - [Drainage Criteria Manual](https://library.municode.com/tx/austin/codes/drainage_criteria_manual)
   - [Transportation Criteria Manual](https://library.municode.com/tx/austin/codes/transportation_criteria_manual)
   - [Title 30 - Subdivision Regulations](https://library.municode.com/tx/austin/codes/land_development_code)
   - [Title 25 Chapter 25-6 - Transportation](http://austin-tx.elaws.us/code/ldc_title25_ch25-6)
   - [Title 25 Chapter 25-7 - Drainage](https://services.austintexas.gov/edims/document.cfm?id=192466)

2. **Use built-in search functionality** for specific terms

3. **Navigate hierarchical structure** when browsing

#### Pros
- Always current
- No downloads needed
- Built-in search

#### Cons
- Requires internet
- No offline access
- Slower for repeated lookups

---

### Option 2: Download Critical Sections as PDFs

**For offline reference:**

#### Process

1. **Identify most-used sections** (track what you reference most often)

2. **Download PDFs from Municode:**
   - Navigate to specific section
   - Use browser print → Save as PDF
   - Or use Municode's PDF export if available

3. **Organize locally:**
   ```
   documents/
   ├── drainage/
   │   ├── DCM-Section-1-Drainage-Policy.pdf
   │   ├── DCM-Section-5-Storm-Drains.pdf
   │   └── DCM-Section-6-Open-Channels.pdf
   ├── transportation/
   │   ├── TCM-Street-Standards.pdf
   │   ├── TCM-ROW-Requirements.pdf
   │   └── LDC-25-6-Parking.pdf
   └── subdivision/
       ├── Title-30-Overview.pdf
       └── Title-30-Ch30-5-Environment.pdf
   ```

4. **Use PDF Processing Pro skill** to:
   - Extract text for searching
   - Create searchable index
   - Build custom reference database

#### Pros
- Offline access
- Fast lookups
- Can annotate/highlight
- No internet required

#### Cons
- May become outdated
- Manual download effort
- Need to track updates

---

### Option 3: Hybrid Approach (Recommended)

**Best of both worlds:**

#### 1. Keep critical sections as PDFs
- Download top 10-15 most-used sections
- Store in organized folder structure
- Update quarterly or when notified of changes

#### 2. Use web for everything else
- Bookmarked for quick access
- Always get latest updates
- Good for occasional lookups

#### 3. Build a quick reference guide
- Create searchable index of downloaded PDFs
- Maintain list of bookmarks by topic
- Track which codes apply to which scenarios

---

## Upcoming: Intelligent Code Lookup Tool

### Proposed Tool Features

1. **Local PDF cache** of frequently-used sections
2. **Full-text search** across all cached documents
3. **Smart lookup** - Ask questions in plain language
4. **Cross-reference** - Automatically link related sections
5. **Update notifications** - Track when codes change
6. **Bookmark management** - Quick access to web versions

### Implementation Plan

- Use PDF Processing Pro skill for text extraction
- Build SQLite database for full-text search
- Create simple CLI or web interface
- Integrate web scraping for updates (if needed)

### Next Steps to Build Tool

1. **Start tracking your code lookups** for 2 weeks
2. **Identify top 10-15 most-used sections**
3. **Download those sections as PDFs** to documents folder
4. **Test PDF Processing Pro** on one section to create searchable text
5. **Decide if we should build the intelligent lookup tool**

---

## PDF Organization Best Practices

### File Naming Convention

Use descriptive names with version dates:
- `DCM-Section-5-Storm-Drains-2024-01-15.pdf`
- `TCM-Street-Standards-2024-03-01.pdf`
- `LDC-25-6-Parking-2023-11-15.pdf`

### Folder Structure

```
austin-codes/
├── drainage/
│   ├── current/
│   │   ├── DCM-Section-1-Drainage-Policy-[date].pdf
│   │   ├── DCM-Section-5-Storm-Drains-[date].pdf
│   │   └── DCM-Section-6-Open-Channels-[date].pdf
│   └── archive/
│       └── [older versions]
├── transportation/
│   ├── current/
│   │   ├── TCM-Street-Standards-[date].pdf
│   │   ├── TCM-ROW-Requirements-[date].pdf
│   │   └── LDC-25-6-Parking-[date].pdf
│   └── archive/
│       └── [older versions]
├── subdivision/
│   ├── current/
│   │   ├── Title-30-Overview-[date].pdf
│   │   └── Title-30-Ch30-5-Environment-[date].pdf
│   └── archive/
│       └── [older versions]
└── index/
    ├── searchable-index.db
    └── code-lookup-tool.exe
```

---

## Update Management

### Tracking Updates

1. **Subscribe to notifications:**
   - Check if Austin offers email alerts for code changes
   - Monitor City Council agendas for ordinance amendments

2. **Quarterly review schedule:**
   - Every 3 months, check Municode for updates
   - Re-download any updated PDFs
   - Move outdated versions to archive folder

3. **Version control:**
   - Always include effective date in filename
   - Keep one previous version in archive
   - Document what changed in a changelog file

### Changelog Template

Create a `CHANGELOG.md` in your codes folder:

```markdown
# Code Updates Log

## 2024-03-15
- Updated DCM Section 5 (Storm Drains)
  - Changed: New sizing requirements for 100-year storm
  - Impact: May affect current projects in design phase

## 2024-01-15
- Updated LDC Chapter 25-6 (Parking)
  - Changed: Reduced minimum parking for multi-family
  - Impact: All new residential projects
```

---

## Getting Started Checklist

- [ ] Bookmark key Municode pages in browser
  - [ ] [Drainage Criteria Manual](https://library.municode.com/tx/austin/codes/drainage_criteria_manual)
  - [ ] [Transportation Criteria Manual](https://library.municode.com/tx/austin/codes/transportation_criteria_manual)
  - [ ] [Title 30](https://library.municode.com/tx/austin/codes/land_development_code)
  - [ ] [LDC Chapter 25-6](http://austin-tx.elaws.us/code/ldc_title25_ch25-6)
  - [ ] [LDC Chapter 25-7](https://services.austintexas.gov/edims/document.cfm?id=192466)
- [ ] Create folder structure for PDF storage
- [ ] Start tracking which code sections you use most (see [Quick Reference Guide](quick-reference.md))
- [ ] Download top 3-5 most-used sections as PDFs
- [ ] Test offline access with downloaded PDFs
- [ ] Set calendar reminder for quarterly review
- [ ] Decide if intelligent lookup tool is needed

---

## Related Documents

- [Primary Code Sections](primary-code-sections.md) - Detailed Title 25 & Title 30 information
- [Technical Manuals](technical-manuals.md) - DCM, TCM, and other manuals
- [Quick Reference Guide](quick-reference.md) - Topic-based cross-references and tracking
- [Return to Main Index](README.md)

---

## External Resources

- [Municode Library - Austin](https://library.municode.com/tx/austin)
- [City of Austin Codes & Resources](https://www.austintexas.gov/codes-resources-tools)
- [Development Services Department](https://www.austintexas.gov/department/development-services)
- [Subdivision Applications](https://www.austintexas.gov/subdivision-apps)
