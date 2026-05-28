# PaperReader-agent

<p align="center">
  <a href="README.md">🇨🇳 中文</a> | <a href="README.en.md">🇬🇧 English</a>
</p>

**双语论文阅读工作流。** 将学术 PDF 转化为结构化的中英对照阅读笔记，通过浏览器实现高效阅读。

## 为什么要有这个工具？

研究生和科研人员每天需要阅读大量英文论文。现有方案各有痛点：

| 方案 | 问题 |
|------|------|
| 纯人工阅读 | 英文阅读速度慢，术语反复查，读完就忘 |
| 机器翻译全文 | 上下文割裂，术语翻译不统一，图片/公式丢失 |
| 直接在 PDF 上标注 | 笔记散落在各 PDF 中，无法集中检索和管理 |
| Zotero/Paperpile | 管理文献元数据很好，但**不支持双语逐段对照** |

**PaperReader-agent 的思路：** 将每篇论文处理成结构化的双语阅读笔记，用浏览器渲染为左右对照界面。一次处理，永久使用。

## 工作流程一览

```
PDF 论文
  │
  ▼
[MinerU API] ──── VLM + OCR 解析，提取文本、图片、表格、公式
  │
  ▼
[LLM (Claude/GPT)] ── 双语翻译 + 锚点化，生成 paper.md
  │
  ▼
[后处理] ── 清理冗余图片、修正图索引、确认 source_map.json
  │
  ▼
[build-reader.js] ── 扫描所有论文目录，构建前端可加载的索引
  │
  ▼
[paper-reader.html] ── 双击打开，浏览器中左右对照阅读
```

## Features

- 📄 **PDF 自动解析** — MinerU API (VLM+OCR) 提取文本、图表、表格、公式，保留原始结构
- 🖼️ **插图智能提取** — 混合模式：优先从 PDF 提取嵌入图片（高分辨率），其次用 VLM 渲染矢量图表
- 📑 **锚点索引体系** — 每段原文有唯一 ID（S001, S002...），支撑章节跳转、引用定位、交叉检索
- 🌐 **中英对照阅读器** — 浏览器直接打开，左栏英文原文、右栏中文翻译，支持搜索和图片放大
- 📂 **多论文管理** — 所有论文独立目录，build-reader.js 自动扫描构建索引
- 🤖 **AI 辅助工作流** — MinerU 做结构化提取，LLM 做翻译，人工做质检验收

## Quick Start

```bash
# 1. 克隆
git clone <repo>
cd paper-reader

# 2. 安装 Python 依赖（PDF 解析需要）
pip3 install PyMuPDF

# 3. 解析一篇 PDF
python3 mineru_parse.py path/to/paper.pdf "论文中文目录名"

# 4. 用大模型生成双语阅读笔记（见下文"提示词模板"）
#    输出保存为 论文中文目录名/paper.md

# 5. 后处理：清理图片 + 修正索引
rm -f 论文中文目录名/assets/page_*.png                    # 删除整页截图
#   将 MinerU 哈希命名的图表重命名为 fig_{序号}_p{页码}.png

# 6. 构建索引
node build-reader.js

# 7. 浏览器打开
open paper-reader.html
```

---

## 完整工作流

### Step 1: MinerU 服务配置

`mineru_parse.py` 依赖 MinerU 的 API 服务（VLM+OCR PDF 解析引擎）。

**配置方法：** 编辑 `mineru_parse.py` 顶部

```python
SERVER = "http://your-mineru-host:8801"   # MinerU API 地址
API_KEY = "your-api-key"                   # 鉴权密钥
```

**如果你没有 MinerU 服务：** 查看 [MinerU 官方文档](https://github.com/opendatalab/MinerU) 部署，或联系团队获取内网地址。

### Step 2: PDF 解析

```bash
python3 mineru_parse.py path/to/paper.pdf "论文中文目录名"
```

**示例：**
```bash
python3 mineru_parse.py ~/Downloads/chronomedkg.pdf "ChronoMedKG：一个基于时间框架的生物医学知识图谱及临床推理基准"
```

**执行后自动生成：**

```
论文目录名/
├── source_map.json       # 结构化索引（需后续精修）
├── mineru_raw.md         # MinerU 提取的 Markdown 原文
├── mineru_raw.json       # MinerU 结构化 JSON（含 content_list）
├── assets/               # 图片资源
│   ├── <hash1>.jpg       # MinerU 返回的图片（哈希命名）
│   ├── <hash2>.jpg
│   └── ...
└── 论文名.pdf            # 原 PDF 副本
```

**API 参数说明**（修改 `mineru_parse.py` 中的 `_build_multipart` 调用）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `backend` | `hybrid-auto-engine` | 解析引擎。可选 `hybrid-auto-engine`（自动混合）或 `pure-vlm`（纯视觉） |
| `formula_enable` | `true` | 是否启用公式识别 |
| `table_enable` | `true` | 是否启用表格提取 |
| `return_md` | `true` | 返回 Markdown 格式结果 |
| `return_content_list` | `true` | 返回结构化内容列表（含图片位置） |
| `return_images` | `true` | 返回图片数据（base64） |

### Step 3: 用大模型生成双语阅读笔记

使用 `mineru_raw.md` 和 `mineru_raw.json` 作为上下文，向大模型（Claude/GPT-4o/DeepSeek）发送提示词，生成标准格式的 `paper.md`。

#### 提示词模板

```markdown
你是一个学术论文阅读助手。根据以下 MinerU 解析结果，生成标准格式的双语阅读笔记。

## 输入材料

### MinerU 原始 Markdown
```
[粘贴 mineru_raw.md 的内容]
```

### MinerU 结构化 JSON（图片位置信息）
```
[粘贴 mineru_raw.json 中的 content_list 数组]
```

### 图片目录（assets/ 下的文件）
```
[列出 assets/ 目录中的文件名，例如：]
fig_p2_0.jpeg    ← 嵌入图片（高分辨率），用于 Figure 1
fig_p8_0.png     ← 嵌入图片，用于 Figure 2
fig_p31_0.png    ← 嵌入图片，用于 Figure 6
fig_p32_0.png    ← 嵌入图片，用于 Figure 7
```

## 输出格式要求

生成一个 `paper.md`，格式如下：

### 整体结构（三部分顺序固定）
1. **YAML frontmatter** — 元数据
2. **正文区** — 锚点化的中英对照段落
3. **阅读笔记区** — `## 阅读提示`

### 正文区规则
- 每段原文用一个锚点块 `<a id="S001">` 标记，连续编号 S001, S002, S003...
- 每个锚点块包含：
  ```markdown
  <a id="S001"></a>
  **Source:** p.1 S001

  **Original:**
  <英文原文>

  **中文:**
  <中文翻译>

  ---
  ```
- 在首次引用图片的段落后插入：
  ```markdown
  ---

  ### 图 1 / Figure 1. <标题>

  ![Figure 1: <标题>](assets/<正确的图片文件名>)
  **Original caption:** <原文图注>
  **中文图注:** <中文图注>

  ---
  ```
- **永远不要使用 page_ 开头的图片路径**（如 page_02.png），只使用 fig_ 开头的
- 锚点块之间必须有 `---` 分隔

### 图片引用规则（重要）
- 优先使用 `fig_p*.*` 命名的文件（嵌入图片，高分辨率）
- 对于缺失嵌入图片的图表，使用 MinerU content_list 定位：
  - content_list 中 `type:"image"` 且 `img_path` 以 `"images/"` 开头的条目是真实图表
  - 这些图片在 assets/ 中以哈希名存在，paper.md 中先使用占位名 `fig_X_pY.png`
- 图片放在首次引用的段落后，不跨章节边界

### 术语表
- 正文区末尾、阅读笔记前，可添加 `## 术语表 / Terminology`
- 格式：`| 英文 | 中文 | 说明 |`

### 阅读笔记区
```markdown
## 阅读提示

1. **核心贡献：** ...
2. **关键创新：** ...
3. **局限性注意：** ...
4. **数据来源：** ...
```

### 质量要求
- 翻译准确，术语一致
- 锚点 ID 连续不跳跃
- 保留原文关键术语（括号标注英文）
- 长段落分段翻译，不丢失信息
```

#### LLM 推荐配置

| 模型 | 适用场景 | 质量 | 成本 |
|------|----------|------|------|
| Claude Sonnet 4 | 正式论文 | ⭐⭐⭐⭐⭐ | 中等 |
| GPT-4o | 快速处理 | ⭐⭐⭐⭐ | 中等 |
| DeepSeek V3 | 大量处理 | ⭐⭐⭐⭐ | 低 |
| Claude Haiku | 快速预览 | ⭐⭐⭐ | 低 |

### Step 4: 后处理（图片资产清理）

MinerU 可能输出大量图片，需筛选出真正的论文插图。

**通过 content_list 定位真实图表：**

```bash
python3 << 'EOF'
import json

with open("论文目录名/mineru_raw.json") as f:
    data = json.load(f)

for item in data["content_list"]:
    if item.get("type") == "image" and "images/" in (item.get("img_path") or ""):
        page = item["page_idx"] + 1  # 转为 1-indexed
        print(f"  p{page} → {item['img_path']}  ({item.get('text','')[:50]})")
EOF
```

**清理步骤：**
```bash
cd 论文目录名

# 1. 删除整页截图
rm -f assets/page_*.png

# 2. 将 MinerU 哈希图重命名为友好名称
#    例如：Figure 3 出现在第 19 页
cp assets/<hash_figure3>.jpg assets/fig_03_p19.png

# 3. 删除已重命名的哈希文件（可选）
# rm assets/<hash_figure3>.jpg
```

**最终 assets/ 应只包含：**
```
assets/
├── fig_p2_0.jpeg     # PDF 嵌入图（高分辨率优先使用）
├── fig_p8_0.png
├── fig_03_p19.png    # MinerU 渲染图（无嵌入时使用）
├── fig_04_p24.png
├── fig_05_p29.png
├── fig_p31_0.png
├── fig_p32_0.png
└── fig_08_p33.png
```

### Step 5: 修正 source_map.json

MinerU 自动生成的 `source_map.json` 的 `figures` 段需要手动精修：

```bash
# 对照论文中的图号，修正 source_map.json 的 figures 段
```

需要修正的内容：
- 图号：`F01` → `F001`（三位数对齐）
- 补齐缺失的图（MinerU 可能遗漏）
- `asset` 路径：指向 `assets/fig_*.*` 而非哈希文件名
- `description`：写中文描述

### Step 6: 构建索引

```bash
node build-reader.js
```

**作用：** 扫描所有论文目录，读取 `paper.md` 和 `source_map.json`，生成：

| 文件 | 作用 |
|------|------|
| `papers-index.json` | 论文元数据索引（标题、作者、来源、图/表数量等） |
| `papers-data.js` | 所有论文的完整 paper.md 内容（嵌入 JS，供前端加载） |

**必须每次修改后都运行。** 否则改动不会反映到界面上。

**输出示例：**
```
📡 Scanning papers...
✅ Wrote papers-index.json (46 papers)
✅ Wrote papers-data.js (2144 KB)
🎉 Done! Double-click paper-reader.html to use.
```

### Step 7: 查看结果

```bash
# macOS
open paper-reader.html

# Linux
xdg-open paper-reader.html

# Windows
start paper-reader.html
```

无需 HTTP 服务器。`paper-reader.html` 直接从内嵌的 `papers-data.js` 加载数据。

**阅读器特性：**
- 左右对照：左栏英文原文，右栏中文翻译
- 锚点跳转：点击导航栏章节，滚动到对应锚点
- 图片点击放大
- 搜索论文

---

## 目录结构约定

```
paper-reader/                    # 项目根目录
├── paper-reader.html            # 阅读器界面（双击打开）
├── build-reader.js              # 索引构建工具
├── mineru_parse.py              # PDF 解析脚本
├── workflow-spec.md             # 完整操作规范（详细版）
├── MinerU-api/api.md            # MinerU API 文档
│
├── papers-index.json            # 自动构建 → 论文索引
├── papers-data.js               # 自动构建 → 嵌入数据
│
├── 论文目录1/                   # 每篇论文一个目录
│   ├── paper.md                 # 中英对照阅读笔记（必需）
│   ├── source_map.json          # 锚点索引（推荐）
│   ├── mineru_raw.md            # MinerU 原始输出
│   ├── mineru_raw.json
│   ├── assets/                  # 图片资源
│   │   ├── fig_p2_0.jpeg
│   │   ├── fig_03_p19.png
│   │   └── ...
│   └── *.pdf                    # 原始 PDF
│
├── 论文目录2/
│   └── ...
└── ...
```

**目录命名规则：**
- 用论文核心主题的**中文缩写**（6–20 汉字）
- 不包含特殊字符
- 同一篇论文重新处理时覆盖原目录

---

## 文件格式规范

详见 `workflow-spec.md`（操作规范完整版），核心要点：

### paper.md

三段式结构：

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
中文翻译。

---

<!-- 图片：放在首次引用的段落后 -->
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
    "title": "论文标题",
    "authors": "作者",
    "source": "期刊",
    "pages": 12,
    "extraction_date": "2026-05-24",
    "confidence": "high"
  },
  "page_index": {
    "1": ["S001", "S002"],
    "2": ["S003", "S004", "F001"]
  },
  "blocks": {
    "S001": { "page": 1, "type": "text", "description": "介绍..." },
    "S002": { "page": 1, "type": "text", "description": "相关工作..." }
  },
  "figures": {
    "F001": { "page": 2, "type": "figure", "description": "图1 | 整体框架", "asset": "assets/fig_p2_0.jpeg" }
  },
  "tables": {
    "T001": { "page": 3, "type": "table", "description": "数据集统计", "asset": "" }
  }
}
```

---

## 图片资产总览

| 命名模式 | 来源 | 分辨率 | 优先级 | 说明 |
|----------|------|--------|--------|------|
| `fig_p{page}_{idx}.ext` | PyMuPDF 从 PDF 提取 | 高 | 🥇 优先使用 | PDF 中有嵌入图片对象时存在 |
| `fig_{n:02d}_p{page}.png` | 从 MinerU 哈希重命名 | 中 | 🥈 备选 | VLM 渲染的矢量图表 |
| `<hash>.jpg` | MinerU API 原始输出 | 中 | ❌ 需重命名 | 重命名后才使用 |
| `page_*.png` | 整页渲染 | 低 | ❌ 不用 | 含界面 chrome，非插图 |

---

## 常见问题

**Q: books 或参考论文目录在哪？**
项目根目录下的子目录就是论文目录。`build-reader.js` 会自动扫描所有含 `paper.md` 的子目录。

**Q: 新增论文后不显示？**
```bash
node build-reader.js
```
没运行这个就不会更新。

**Q: 图片显示破裂？**
检查两处：
1. `paper.md` 中的 `](assets/...)` 路径是否和实际文件一致
2. 文件是否真的在 `assets/` 目录下

**Q: 如何配置 MinerU 服务？**
编辑 `mineru_parse.py` 顶部的 `SERVER` 和 `API_KEY`。如果你没有服务，需要先部署 MinerU。

**Q: 没有 MinerU 也能用吗？**
可以。手动创建 `paper.md` 和 `assets/`，然后 `node build-reader.js` 即可。MinerU 只是 PDF 自动解析的辅助工具。

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `paper-reader.html` | 阅读器界面（双击打开） |
| `build-reader.js` | 索引构建工具（Node.js） |
| `mineru_parse.py` | MinerU API PDF 解析脚本 |
| `workflow-spec.md` | 完整操作规范和格式标准 |
| `MinerU-api/api.md` | MinerU API 接口文档 |
