# PaperReader-agent

A literature paper reading tool with Chinese-English side-by-side reader, PDF parsing via MinerU/Docling, and automated index building.

## Files

- `paper-reader.html` — Main reader interface (Chinese-English side-by-side)
- `build-reader.js` — Index builder: scans paper directories, generates `papers-data.js`
- `docling_parse.py` — PDF parsing script using Docling/MinerU
- `workflow-spec.md` — Workflow specification and operation guide
- `papers-data.js` — Generated paper index (loaded by reader)
- `papers-index.json` — Paper metadata index

## Usage

1. Add paper notes as subdirectories with `paper.md`
2. Run `node build-reader.js` to rebuild index
3. Open `paper-reader.html` in browser
