/**
 * build-reader.js — 生成 papers-data.js（索引 + 全部 paper.md 内容）
 *
 * 用法: node build-reader.js
 * 功能: 扫描 docs/paper/ 下所有论文，生成 papers-index.json
 *       和 papers-data.js（可被 paper-reader.html 的 <script> 标签加载）
 *
 * 构建后 paper-reader.html 双击即可使用，无需 HTTP 服务器。
 */

const fs = require('fs');
const path = require('path');

const baseDir = __dirname;
const indexPath = path.join(baseDir, 'papers-index.json');
const dataJsPath = path.join(baseDir, 'papers-data.js');

function extractYear(str) {
  if (!str) return '';
  const matches = str.match(/20\d{2}/g);
  if (!matches) return '';
  const valid = matches.filter(y => y >= '2020' && y <= '2029');
  return valid.length ? valid.sort()[0] : '';
}

function escapeJsString(str) {
  return str.replace(/\\/g, '\\\\')
            .replace(/`/g, '\\`')
            .replace(/\$/g, '\\$');
}

function scanPapers() {
  const dirs = fs.readdirSync(baseDir, { withFileTypes: true });
  const papers = [];
  const papersContent = {};

  for (const d of dirs) {
    if (!d.isDirectory()) continue;
    const dirName = d.name;
    const smPath = path.join(baseDir, dirName, 'source_map.json');
    const pmPath = path.join(baseDir, dirName, 'paper.md');
    const assetsDir = path.join(baseDir, dirName, 'assets');

    if (!fs.existsSync(pmPath)) continue;

    const content = fs.readFileSync(pmPath, 'utf-8');
    papersContent[dirName] = content;

    const hasAssets = fs.existsSync(assetsDir) && fs.statSync(assetsDir).isDirectory();
    let assetFiles = [];
    if (hasAssets) {
      assetFiles = fs.readdirSync(assetsDir).filter(f => /\.(png|jpg|jpeg|gif|svg|webp)$/i.test(f));
    }

    const lineCount = content.split('\n').length;
    let fm = {
      title_en: dirName, title_cn: dirName, authors: '',
      source: '', year: '', pages: '', paper_type: '',
      extraction_confidence: '', has_source_map: false,
      figure_count: 0, table_count: 0, block_count: 0
    };

    if (fs.existsSync(smPath)) {
      try {
        const sm = JSON.parse(fs.readFileSync(smPath, 'utf-8'));
        fm.has_source_map = true;
        fm.pages = sm.metadata?.pages || sm.metadata?.total_pages || '';
        fm.paper_type = sm.metadata?.paper_type || '';
        fm.extraction_confidence = sm.metadata?.confidence || '';
        fm.figure_count = Object.values(sm.blocks || {}).filter(b => b.type === 'figure').length;
        fm.table_count = Object.values(sm.blocks || {}).filter(b => b.type === 'table').length;
        fm.block_count = Object.keys(sm.blocks || {}).length;
        if (sm.metadata?.title) fm.title_en = sm.metadata.title;
        if (sm.metadata?.source) fm.source = sm.metadata.source;
        if (sm.metadata?.source) fm.year = extractYear(sm.metadata.source);
      } catch (e) {}
    }

    if (content.startsWith('---')) {
      const end = content.indexOf('---', 3);
      if (end > 0) {
        const yaml = content.substring(3, end).trim();
        for (const line of yaml.split('\n')) {
          const m = line.match(/^(\w+):\s*(?:"(.*)"|(.*))$/);
          if (m) {
            const key = m[1], val = (m[2] || m[3] || '').trim();
            if (key === 'title' && !fm.title_en) fm.title_en = val;
            else if (key === 'authors') fm.authors = val;
            else if (key === 'source' && !fm.source) { fm.source = val; if (!fm.year) fm.year = extractYear(val); }
          }
        }
      }
    }
    else if (content.includes('## Metadata')) {
      const metaParts = content.split('## Metadata');
      if (metaParts.length > 1) {
        const metaSection = metaParts[1].split('---')[0].split('\n## ')[0];
        for (const line of metaSection.split('\n').filter(l => l.includes('|'))) {
          const cells = line.split('|').map(c => c.trim()).filter(Boolean);
          if (cells.length >= 2) {
            const key = cells[0].replace(/^\*{1,2}/, '').replace(/\*{1,2}$/, '').toLowerCase();
            const val = cells[1];
            if (key === 'title' && !fm.title_en) fm.title_en = val;
            else if (key === 'authors' && !fm.authors) fm.authors = val;
            else if (key === 'journal' && !fm.source) { fm.source = val; if (!fm.year) fm.year = extractYear(val); }
            else if (key === 'arxiv' || key === 'arxiv id') { if (!fm.source) fm.source = 'arXiv:' + val; if (!fm.year) fm.year = extractYear(val); }
          }
        }
      }
    }

    if (!fm.year) fm.year = extractYear(content.substring(0, 2000));
    if (!fm.authors && !content.startsWith('---')) {
      const aMatch = content.match(/\*\*Authors\*\*\s*\|\s*(.+?)(?:\||$)/);
      if (aMatch) fm.authors = aMatch[1].trim();
    }

    let notes = [];
    const notesPath = path.join(baseDir, dirName, 'notes.json');
    if (fs.existsSync(notesPath)) {
      try {
        const parsed = JSON.parse(fs.readFileSync(notesPath, 'utf-8'));
        notes = Array.isArray(parsed.notes) ? parsed.notes : [];
      } catch (e) { console.warn('⚠️ Failed to parse notes.json in ' + dirName + ': ' + e.message); }
    }

    papers.push({
      id: dirName, title_cn: dirName, title_en: fm.title_en || dirName,
      authors: fm.authors || '', source: fm.source || '', year: fm.year || '',
      pages: fm.pages, paper_type: fm.paper_type, lineCount,
      hasAssets, assetCount: assetFiles.length,
      figureCount: fm.figure_count, tableCount: fm.table_count,
      blockCount: fm.block_count, sm: fm.has_source_map,
      notes
    });
  }

  papers.sort((a, b) => {
    if (a.year !== b.year) return (b.year || '').localeCompare(a.year || '');
    return a.id.localeCompare(b.id);
  });

  return { papers, papersContent };
}

function build() {
  console.log('📡 Scanning papers...');
  const { papers, papersContent } = scanPapers();
  const index = { papers, total: papers.length, generated: new Date().toISOString() };

  fs.writeFileSync(indexPath, JSON.stringify(index, null, 2));
  console.log('✅ Wrote papers-index.json (' + papers.length + ' papers)');

  let js = '// papers-data.js — 由 build-reader.js 自动生成\n';
  js += '// 重新生成: node build-reader.js\n\n';
  js += 'var __EMBEDDED_INDEX__ = ' + JSON.stringify(index, null, 2) + ';\n\n';
  js += 'var __EMBEDDED_PAPERS__ = {\n';
  const entries = Object.entries(papersContent);
  for (let i = 0; i < entries.length; i++) {
    const [id, content] = entries[i];
    js += '  ' + JSON.stringify(id) + ': `' + escapeJsString(content) + '`';
    if (i < entries.length - 1) js += ',';
    js += '\n';
  }
  js += '};\n';

  fs.writeFileSync(dataJsPath, js, 'utf-8');
  const jsSize = (Buffer.byteLength(js, 'utf-8') / 1024).toFixed(0);
  console.log('✅ Wrote papers-data.js (' + jsSize + ' KB)');
  console.log('🎉 Done! Double-click paper-reader.html to use.');
}

build();
