# PaperReader-agent

<p align="center">
  <a href="README.md">🇨🇳 中文</a> | <a href="README.en.md">🇬🇧 English</a>
</p>

**Bilingual paper reading workflow.** Transform academic PDFs into structured Chinese-English reading notes, rendered as a side-by-side reader in your browser.

## Why This Tool?

Graduate students and researchers read dozens of English papers daily. Existing approaches all have pain points:

| Approach | Problem |
|----------|---------|
| Reading raw English directly | Slow, constant dictionary lookups, poor retention |
| Full machine translation | Context fragmentation, inconsistent terminology, lost figures/formulas |
| Annotating PDFs directly | Notes scattered across files, no centralized search |
| Zotero/Paperpile | Great for metadata management, but **no bilingual paragraph-level reading** |

**PaperReader-agent's approach:** Process each paper into a structured bilingual reading note, rendered as a side-by-side interface in the browser. Process once, read forever.

## Workflow at a Glance

```
PDF Paper
  │
  ▼
[MinerU API] ──── VLM + OCR parsing, extracts text, figures, tables, formulas
  │
  ▼
[LLM (Claude/GPT)] ── Bilingual translation + anchor indexing, produces paper.md
  │
  ▼
[Post-processing] ── Clean up redundant images, fix figure index, verify source_map.json
  │
  ▼
[build-reader.js] ── Scan all paper directories, build frontend-loadable index
  │
  ▼
[paper-reader.html] ── Double-click to open, side-by-side bilingual reading in browser
```

## Features

- 📄 **Automatic PDF Parsing** — MinerU API (VLM+OCR) extracts text, figures, tables, and formulas while preserving structure
- 🖼️ **Smart Figure Extraction** — Hybrid mode: prefers embedded images from PDF (high resolution), falls back to VLM-rendered vector graphics
- 📑 **Anchor Index System** — Every paragraph has a unique ID (S001, S002...), enabling section navigation, citation lookup, and cross-referencing
- 🌐 **Bilingual Side-by-Side Reader** — Open directly in browser: English left, Chinese right, with search and image zoom
- 📂 **Multi-Paper Management** — Each paper in its own directory; build-reader.js auto-scans and builds the index
- 🤖 **AI-Assisted Workflow** — MinerU for structured extraction, LLM for translation, human review for quality control

## Quick Start

```bash
# 1. Clone
git clone <repo>
cd paper-reader

# 2. Install Python dependencies (PDF parsing)
pip3 install PyMuPDF

# 3. Parse a PDF
python3 mineru_parse.py path/to/paper.pdf "PaperDirectoryName"

# 4. Generate bilingual reading notes with an LLM (see "Prompt Template" below)
#    Save output as PaperDirectoryName/paper.md

# 5. Post-processing: clean images + fix index
rm -f PaperDirectoryName/assets/page_*.png                    # Delete page renders
#   Rename MinerU hash-named chart images to fig_{n}_p{page}.png

# 6. Build index
node build-reader.js

# 7. Open in browser
open paper-reader.html
```

---

## Full Workflow

### Step 1: Configure MinerU Service

`mineru_parse.py` depends on the MinerU API service (VLM+OCR PDF parsing engine).

**Configuration:** Edit the top of `mineru_parse.py`

```python
SERVER = "http://your-mineru-host:8801"   # MinerU API address
API_KEY = "your-api-key"                   # Authentication key
```

**If you don't have a MinerU service:** Deploy it following the [official docs](https://github.com/opendatalab/MinerU), or ask your team for the internal address.

### Step 2: Parse PDF

```bash
python3 mineru_parse.py path/to/paper.pdf "PaperDirectoryName"
```

**Example:**
```bash
python3 mineru_parse.py ~/Downloads/chronomedkg.pdf "ChronoMedKG"
```

**Auto-generated output:**

```
PaperDirectoryName/
├── source_map.json       # Structured index (needs refinement)
├── mineru_raw.md         # MinerU Markdown output
├── mineru_raw.json       # MinerU structured JSON (with content_list)
├── assets/               # Image assets
│   ├── <hash1>.jpg       # MinerU images (hash-named)
│   ├── <hash2>.jpg
│   └── ...
└── paper.pdf             # Original PDF copy
```

**API Parameters** (configurable in `mineru_parse.py`'s `_build_multipart` call):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `backend` | `hybrid-auto-engine` | Engine: `hybrid-auto-engine` (auto) or `pure-vlm` (vision-only) |
| `formula_enable` | `true` | Enable formula recognition |
| `table_enable` | `true` | Enable table extraction |
| `return_md` | `true` | Return Markdown result |
| `return_content_list` | `true` | Return structured content list (includes image positions) |
| `return_images` | `true` | Return image data (base64) |

### Step 3: Generate Bilingual Reading Notes with an LLM

Use `mineru_raw.md` and `mineru_raw.json` as context. Send the following prompt to an LLM (Claude/GPT-4o/DeepSeek) to generate a standard-format `paper.md`.

#### Prompt Template

```markdown
You are an academic paper reading assistant. Generate a standard-format bilingual reading note from the MinerU parsing results below.

## Input Materials

### MinerU Raw Markdown
```
[paste content of mineru_raw.md]
```

### MinerU Structured JSON (image position info)
```
[paste content_list array from mineru_raw.json]
```

### Image Directory (assets/ files)
```
[list files in assets/ directory, e.g.:]
fig_p2_0.jpeg    ← embedded image (high resolution), for Figure 1
fig_p8_0.png     ← embedded image, for Figure 2
fig_p31_0.png    ← embedded image, for Figure 6
fig_p32_0.png    ← embedded image, for Figure 7
```

## Output Format Requirements

Generate a `paper.md` with the following structure:

### Overall Structure (three sections, in order)
1. **YAML frontmatter** — Metadata
2. **Content body** — Anchored bilingual paragraphs
3. **Reading notes** — `## 阅读提示` section

### Content Body Rules
- Each paragraph is an anchor block `<a id="S001">`, consecutively numbered S001, S002, S003...
- Each anchor block contains:
  ```markdown
  <a id="S001"></a>
  **Source:** p.1 S001

  **Original:**
  <English original text>

  **中文:**
  <Chinese translation>

  ---
  ```
- Insert images after the paragraph where they are first referenced:
  ```markdown
  ---

  ### 图 1 / Figure 1. <Title>

  ![Figure 1: <Title>](assets/<correct_image_filename>)
  **Original caption:** <original caption>
  **中文图注:** <Chinese caption>

  ---
  ```
- **Never use page_-prefixed image paths** (e.g., `page_02.png`); only use `fig_`-prefixed ones.
- Anchor blocks must be separated by `---`.

### Image Referencing Rules (Important)
- Prefer `fig_p*.*` named files (embedded images, high resolution).
- For figures without embedded images, use MinerU's content_list to locate them:
  - In content_list, items with `type:"image"` and `img_path` starting with `"images/"` are real figures
  - These exist in assets/ with hash names; use a placeholder name `fig_X_pY.png` in paper.md initially
- Place images after their first referenced paragraph, not across section boundaries.

### Glossary
- Optionally add `## 术语表 / Terminology` before the reading notes section.
- Format: `| English | 中文 | Description |`

### Reading Notes Section
```markdown
## 阅读提示

1. **核心贡献：** ...
2. **关键创新：** ...
3. **局限性注意：** ...
4. **数据来源：** ...
```

### Quality Requirements
- Accurate translation, consistent terminology
- Consecutive anchor IDs, no gaps
- Preserve key terms with English in parentheses
- Split long paragraphs without losing information
```

#### Recommended LLMs

| Model | Use Case | Quality | Cost |
|-------|----------|---------|------|
| Claude Sonnet 4 | Formal papers | ⭐⭐⭐⭐⭐ | Medium |
| GPT-4o | Fast processing | ⭐⭐⭐⭐ | Medium |
| DeepSeek V3 | Bulk processing | ⭐⭐⭐⭐ | Low |
| Claude Haiku | Quick preview | ⭐⭐⭐ | Low |

### Step 4: Post-Processing (Image Cleanup)

MinerU may output many images. You need to filter out the actual paper figures.

**Locate real figures via content_list:**

```bash
python3 << 'EOF'
import json

with open("PaperDirectoryName/mineru_raw.json") as f:
    data = json.load(f)

for item in data["content_list"]:
    if item.get("type") == "image" and "images/" in (item.get("img_path") or ""):
        page = item["page_idx"] + 1  # convert to 1-indexed
        print(f"  p{page} → {item['img_path']}  ({item.get('text','')[:50]})")
EOF
```

**Cleanup steps:**
```bash
cd PaperDirectoryName

# 1. Delete full-page screenshots
rm -f assets/page_*.png

# 2. Rename MinerU hash images to friendly names
#    e.g., Figure 3 appears on page 19
cp assets/<hash_figure3>.jpg assets/fig_03_p19.png

# 3. Optionally delete the original hash file
# rm assets/<hash_figure3>.jpg
```

**Final assets/ should look like:**
```
assets/
├── fig_p2_0.jpeg     # PDF embedded image (prefer high resolution)
├── fig_p8_0.png
├── fig_03_p19.png    # MinerU rendered image (fallback)
├── fig_04_p24.png
├── fig_05_p29.png
├── fig_p31_0.png
├── fig_p32_0.png
└── fig_08_p33.png
```

### Step 5: Refine source_map.json

The `figures` section of the auto-generated `source_map.json` needs manual refinement:

Required fixes:
- Figure IDs: `F01` → `F001` (three digits to match S###/T###)
- Fill in missing figures (MinerU may miss some)
- `asset` path: point to `assets/fig_*.*` instead of hash filenames
- `description`: write a meaningful Chinese description

### Step 6: Build Index

```bash
node build-reader.js
```

**What it does:** Scans all paper directories, reads `paper.md` and `source_map.json`, generates:

| File | Purpose |
|------|---------|
| `papers-index.json` | Paper metadata index (title, authors, source, figure/table counts, etc.) |
| `papers-data.js` | Full paper.md content for all papers (embedded JS for frontend loading) |

**Must run after every modification.** Otherwise changes won't appear in the reader.

**Expected output:**
```
📡 Scanning papers...
✅ Wrote papers-index.json (46 papers)
✅ Wrote papers-data.js (2144 KB)
🎉 Done! Double-click paper-reader.html to use.
```

### Step 7: View Results

```bash
# macOS
open paper-reader.html

# Linux
xdg-open paper-reader.html

# Windows
start paper-reader.html
```

No HTTP server needed. `paper-reader.html` loads data directly from the embedded `papers-data.js`.

**Reader features:**
- Side-by-side: English original (left), Chinese translation (right)
- Anchor navigation: click chapter headings in the nav bar to jump to corresponding content
- Click to enlarge images
- Search papers

---

## Directory Structure

```
paper-reader/                    # Project root
├── paper-reader.html            # Reader interface (double-click to open)
├── build-reader.js              # Index builder
├── mineru_parse.py              # PDF parsing script
├── workflow-spec.md             # Full workflow specification
├── MinerU-api/api.md            # MinerU API docs
│
├── papers-index.json            # Auto-built → paper index
├── papers-data.js               # Auto-built → embedded data
│
├── PaperDir1/                   # Each paper is a subdirectory
│   ├── paper.md                 # Bilingual reading notes (required)
│   ├── source_map.json          # Anchor index (recommended)
│   ├── mineru_raw.md            # MinerU raw Markdown
│   ├── mineru_raw.json
│   ├── assets/                  # Image assets
│   │   ├── fig_p2_0.jpeg
│   │   ├── fig_03_p19.png
│   │   └── ...
│   └── *.pdf                    # Original PDF
│
├── PaperDir2/
│   └── ...
└── ...
```

**Directory naming:**
- Use a short descriptive name (Chinese abbreviation recommended, 6–20 characters)
- No special characters
- Re-process the same paper by overwriting its directory

---

## File Format Specification

See `workflow-spec.md` for the full specification. Key points:

### paper.md

Three-section structure:

```markdown
---
title: "Full English Title"
title_cn: "中文标题"
authors: "..."
source: "Journal/arXiv:ID"
year: "2025"
pages: 12
doi: "10.xxxx/xxxxx"
paper_type: "methods"
reader_created: "2026-05-24"
status: "complete"
---

## Section 1. Introduction

<a id="S001"></a>
**Source:** p.1 S001

**Original:**
English text here.

**中文:**
Chinese translation.

---

<!-- Image: placed after its first referenced paragraph -->
### 图 1 / Figure 1. Framework overview

![Figure 1: Framework overview](assets/fig_p2_0.jpeg)
**Original caption:** Figure 1. The overall architecture.
**中文图注:** 图 1. 整体架构。

---

## 阅读提示

1. **核心贡献：** ...
```

### source_map.json

```json
{
  "metadata": {
    "title": "Paper Title",
    "authors": "Authors",
    "source": "Journal",
    "pages": 12,
    "extraction_date": "2026-05-24",
    "confidence": "high"
  },
  "page_index": {
    "1": ["S001", "S002"],
    "2": ["S003", "S004", "F001"]
  },
  "blocks": {
    "S001": { "page": 1, "type": "text", "description": "Introduction..." },
    "S002": { "page": 1, "type": "text", "description": "Related work..." }
  },
  "figures": {
    "F001": { "page": 2, "type": "figure", "description": "图1 | Framework overview", "asset": "assets/fig_p2_0.jpeg" }
  },
  "tables": {
    "T001": { "page": 3, "type": "table", "description": "Dataset statistics", "asset": "" }
  }
}
```

---

## Image Asset Summary

| Naming Pattern | Source | Resolution | Priority | Notes |
|---------------|--------|------------|----------|-------|
| `fig_p{page}_{idx}.ext` | Extracted from PDF via PyMuPDF | High | 🥇 Prefer | Exists only when PDF has embedded image objects |
| `fig_{n:02d}_p{page}.png` | Renamed from MinerU hash | Medium | 🥈 Fallback | VLM-rendered vector charts |
| `<hash>.jpg` | MinerU API raw output | Medium | ❌ Needs rename | Must be renamed before use |
| `page_*.png` | Full page render | Low | ❌ Don't use | Includes browser chrome, not paper figures |

---

## FAQ

**Q: Where are the paper directories?**
Any subdirectory in the project root that contains `paper.md`. `build-reader.js` scans automatically.

**Q: New paper doesn't show up?**
```bash
node build-reader.js
```
It won't update without this step.

**Q: Broken images?**
Check two things:
1. Does the `](assets/...)` path in `paper.md` match the actual file?
2. Does the file actually exist in `assets/`?

**Q: How to configure MinerU service?**
Edit `SERVER` and `API_KEY` at the top of `mineru_parse.py`. If you don't have a service, you need to deploy MinerU first.

**Q: Can I use this without MinerU?**
Yes. Just create `paper.md` and `assets/` manually, then `node build-reader.js`. MinerU is only a helper for automatic PDF parsing.

---

## Related Files

| File | Description |
|------|-------------|
| `paper-reader.html` | Reader interface (double-click to open) |
| `build-reader.js` | Index builder (Node.js) |
| `mineru_parse.py` | MinerU API PDF parsing script |
| `workflow-spec.md` | Full workflow and format specification |
| `MinerU-api/api.md` | MinerU API interface documentation |
