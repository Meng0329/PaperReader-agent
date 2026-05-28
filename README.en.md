# PaperReader-agent

<p align="center">
  <a href="README.md">🇨🇳 中文</a> | <a href="README.en.md">🇬🇧 English</a>
</p>

**Bilingual paper reading workflow.** Hand a PDF to AI — it parses, translates, formats, and produces an offline bilingual reader page.

## Usage (3 Steps)

### 1. Setup

```bash
git clone https://github.com/Meng0329/PaperReader-agent.git
cd PaperReader-agent

# Python dependencies (for MinerU PDF parsing)
pip3 install PyMuPDF

# Install AI agent skill (teaches the agent how to process papers)
git clone https://github.com/Yuan1z0825/nature-skills.git

# Edit mineru_parse.py — configure your MinerU API
#   SERVER = "http://your-mineru-host:8801"
#   API_KEY = "your-api-key"
```

**Prerequisites:**
- ⬜ **MinerU API** service (PDF parsing engine, required) — deploy or ask for internal address
- ⬜ **nature-skills** (AI skill plugin, required) — `git clone https://github.com/Yuan1z0825/nature-skills.git`
- ⬜ **Python 3 + PyMuPDF** (optional, only needed for mineru_parse.py)

### 2. Let AI Handle It

Run this in **Claude Code / Codex / any AI agent**:

```
/nature-skills:nature-reader /path/to/paper.pdf /path/to/workflow-spec.md
```

The AI will automatically:
- Call MinerU API to parse the PDF (text + figures + tables)
- Translate paragraph by paragraph into bilingual `paper.md`
- Place figures at the correct positions
- Run `node build-reader.js` to rebuild index (if needed)

> If your AI agent doesn't have the nature-reader skill, just feed it `mineru_raw.md` and `mineru_raw.json` and ask it to produce a `paper.md` following `workflow-spec.md`.

### 3. Open & Read

```bash
# Rebuild index if the AI didn't auto-run it
node build-reader.js

# Open in browser
open paper-reader.html
```

That's it.

---

## Directory Structure

```
PaperReader-agent/
├── paper-reader.html     # Reader (double-click, no server needed)
├── build-reader.js       # Index builder (run after adding a paper)
├── mineru_parse.py       # PDF parsing script
├── workflow-spec.md      # Format spec (for AI to follow)
│
├── papers-index.json     # Auto-generated
├── papers-data.js        # Auto-generated
│
├── PaperDir/             # One directory per paper
│   ├── paper.md          # Bilingual notes (AI-generated)
│   ├── source_map.json   # Anchor index
│   ├── assets/fig_*.png  # Figures
│   └── *.pdf             # Original PDF
└── ...
```

---

## FAQ

**New paper doesn't show up?**
```bash
node build-reader.js
```

**No MinerU service?**
Deploy [MinerU](https://github.com/opendatalab/MinerU) or ask your team for the internal address. Configure it at the top of `mineru_parse.py`.

**Can I use this without MinerU?**
Yes. Write `paper.md` manually, then run `node build-reader.js`. MinerU is just a helper for automation.

---

## Files

| File | Description |
|------|-------------|
| `paper-reader.html` | Reader (double-click to open) |
| `build-reader.js` | Index builder |
| `mineru_parse.py` | PDF parser (MinerU API) |
| `workflow-spec.md` | Format spec (for AI) |
