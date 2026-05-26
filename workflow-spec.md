# OpenSpec 07：Paper Directory 统一规范

> 定义从原始 PDF 到 paper-reader 可渲染格式的标准处理流程和文件规范。
> 适用范围：`docs/paper/` 下所有论文目录。

## 元数据
- **类型**：操作规范（非系统模块）
- **阶段**：Phase 1 — 开题报告
- **状态**：draft
- **依赖**：无（独立工作流规范）

---

## 1. 目录结构标准

每个论文目录的最终状态必须包含以下文件：

```
论文目录名/
├── paper.md              # 主文件：中英对照阅读笔记（必需）
├── source_map.json       # 元数据 + 锚点索引（推荐，有 PDF 时必需）
├── translation_notes.md  # 翻译说明/附录记录（可选，有 PDF 时推荐）
├── assets/               # 图片资源目录（有 PDF 时必需）
│   ├── fig1.png          # 图表清晰截图
│   ├── table1.png
│   └── page_01.png       # 整页截图（备用）
└── *.pdf                 # 原始 PDF（有则保留）
```

### 目录命名规则

- 用论文核心主题的**中文缩写**作为目录名
- 长度建议 6-20 个汉字，不包含特殊字符
- 同一篇论文如果重新处理，覆盖原目录

### 规范状态对照

| 状态 | 条件 |
|------|------|
| **完整** | 有 paper.md + source_map.json + assets/ + pdf |
| **标准** | 有 paper.md + source_map.json |
| **笔记级** | 仅有 paper.md（中文笔记，无 PDF 处理） |
| **占位** | 仅有 paper.md（`status: "placeholder"`，标记待处理） |

---

## 2. paper.md 格式规范

### 2.1 整体结构

paper.md 分为三个逻辑区域，**按顺序排列**：

```
1. 元数据区       → YAML frontmatter + 可选元数据表格
2. 正文区         → 锚点化中英对照段落
3. 阅读笔记区     → ## 阅读提示
```

### 2.2 元数据区（规范格式）

统一使用 **YAML frontmatter**（其余格式已废弃）：

```yaml
---
title: "论文完整英文标题"
title_cn: "论文中文标题（如有）"
authors: "作者列表"
source: "期刊/arXiv:ID"
year: "2025"
pages: 12
doi: "10.xxxx/xxxxx"
paper_type: "methods"  # methods | review | benchmark | survey
relevance: "与 RiceClaw 论文的关联说明"
reader_created: "2026-05-24"
status: "complete"  # complete | placeholder
---
```

**字段规则：**
- `title` / `title_cn`：至少提供一个
- `source`：期刊名 + 年份，或 `arXiv:ID`
- `status`：`complete` = 已全文处理；`placeholder` = 仅占位
- `paper_type` / `relevance`：可选，辅助论文分类

### 2.3 正文区（规范格式）

正文区由**锚点块**序列组成，每个锚点块结构如下：

```markdown
<a id="S001"></a>
**Source:** p.3 S001

**Original:**
We introduce the first end-to-end framework for fully automated scientific discovery in ML research, enabled by frontier LLMs.

**中文:**
我们首次引入了一个由前沿 LLM 驱动的端到端框架，用于机器学习研究中的全自动科学发现。

---

<a id="S002"></a>
**Source:** p.4 S002

**Original:**
The framework includes idea generation, experiment design, execution, and writing up results.

**中文:**
该框架包括想法生成、实验设计、执行以及结果撰写。

---
```

#### 锚点块规则

| 组件 | 必需 | 格式 |
|------|------|------|
| `<a id="SXXX">` | ✅ | 以 S 开头，三位数字序号：`S001`, `S002`... |
| `**Source:**` | ✅ | 格式：`p.{页码} {锚点ID}` |
| `**Original:**` | ✅ | 英文原文段落 |
| `**中文:**` | ✅ | 中文翻译段落 |
| `---` | ✅ | 分隔线（锚点块之间的分隔）|

#### 锚点 ID 命名空间

| 前缀 | 类型 | 示例 |
|------|------|------|
| `S###` | 正文段落（Substantive） | `S001`–`S999` |
| `F###` | 图片（Figure） | `F001`–`F099` |
| `T###` | 表格（Table） | `T001`–`T099` |
| `C###` | 图注/表注（Caption） | `C001`–`C099` |

#### 正文区可嵌入的额外元素

**图片**（放在相关锚点块旁）：

```markdown
![Figure 1: Framework overview](assets/fig1.png)
**Original caption:** Figure 1. The overall architecture of our framework.
**中文图注:** 图 1. 本文框架的整体架构。
```

**术语表**（可选，放在正文区末尾、阅读笔记前）：

```markdown
## 术语表 / Terminology

| 英文 | 中文 | 说明 |
|------|------|------|
| Grokking | 顿悟现象 | 模型在过拟合后突然泛化的现象 |
```

### 2.4 正文区禁止的用法

- ❌ 使用 `**原文 (Chinese):**` / `**English:**` 替代标准标记（统一为 `**Original:**` / `**中文:**`）
- ❌ 锚点块之间缺少 `---` 分隔
- ❌ 锚点 ID 跳跃（如从 S001 直接到 S010）
- ❌ 使用 `# 标题`（一级标题）—— 元数据区已包含标题
- ❌ 在 `**Original:**` 或 `**中文:**` 中混入 HTML 标签——除非是锚点 `<a>`

### 2.5 阅读笔记区

放在文件末尾，`## 阅读提示` 标题之后：

```markdown
## 阅读提示

1. **核心贡献：** 一句话总结
2. **与学位论文的关联：** 具体说明哪一章哪一节可引用
3. **关键创新：** bullet list
4. **局限性注意：** 论文的局限，避免误引用
5. **数据来源：** 如果论文有公开数据集/代码，附链接
```

### 2.6 占位符格式（status: placeholder）

```markdown
---
title: "..."
authors: "..."
source: "..."
reader_created: "..."
status: "placeholder"
---

# 标题

> **论文定位**: RiceClaw 第 X 章相关
> **说明**: 本目录待使用 nature-reader 进行全文双语深度处理
```

全文仅此而已，不超过 15 行。

### 2.7 图片放置规范

图片应放在**首次引用的内容段落后、所属章节末尾**，而非章节边界或文档末尾。具体规则：

| 规则 | 说明 | 正确示例 | 错误示例 |
|------|------|----------|----------|
| **内联而非孤立** | 图片应嵌入所属内容章节内，而不是作为独立的 `##` 节放在两个内容节之间 | `## Section 2\n...\n### Fig.X\n![image]` | `## Section 1\n---\n## Fig.X\n![image]\n---\n## Section 2` |
| **章节归属** | 图片 `###` 标题置于父级 `##` 节内 | `## Section 8\n...\n### 图2 / Figure 2\n![Fig.2]` | `## 图2 / Figure 2`（独占一节） |
| **去重** | 同一图片在 paper.md 中只出现一次 | 仅保留 Section 2 内的 Fig.1 | Abstract 后与 Section 2 内各有一份 Fig.1 |
| **位置深度** | 所有图片位置应在文档前 90% 内（≤90% 位置） | Fig.3 at 75% ✅ | Fig.3 at 96% ⚠️（接近文档末尾） |
| **内容分离** | 图片块以 `---` 分隔，确保与前后锚点块之间有明确边界 | `...\n---\n### Fig. X\n![fig]\n---\n<a id="SXXX">` | 图片与锚点块之间无 `---` 分隔 |

**处理流程（用于 nature-reader 或手工创建 paper.md）：**
1. 确定图片在原文中首次引用的段落和页码
2. 找到该段落在 paper.md 中对应的锚点块
3. 在锚点块**之后、所属节的 `---` 分隔符之前**，插入图片块
4. 图片块结构：`---\n\n### Fig. X. ...\n\n![...](assets/...)\n\n---`

**验证方法（`build-reader.js` 之外的手工检查）：**
```bash
# 检查每个图片的前面和后面的 ## 节是否一致（不一致 = 越界）
python3 << 'EOF'
import re
content = open('paper.md').read()
lines = content.split('\n')
img_lines = [i for i, l in enumerate(lines) if l.strip().startswith('![')]
for i in img_lines:
    sec_before = [l for l in lines[:i] if re.match(r'^##\s', l)][-1] if any(re.match(r'^##\s', l) for l in lines[:i]) else ''
    sec_after  = [l for l in lines[i+1:] if re.match(r'^##\s', l)][0]  if any(re.match(r'^##\s', l) for l in lines[i+1:]) else ''
    if sec_before and sec_after and sec_before != sec_after:
        print(f"⚠️ L{i+1}: 图片跨节边界（{sec_before} → {sec_after}）")
EOF
```

---

## 3. source_map.json 规范

### 3.1 目的

source_map.json 是从 PDF 中提取的结构化索引，用于：
1. 记录每页包含哪些内容锚点
2. 追踪图片/表格的提取路径
3. 提供元数据的程序化访问

### 3.2 标准 Schema

```json
{
  "metadata": {
    "title": "string",
    "authors": "string",
    "source": "string",
    "pages": 12,
    "paper_type": "string",
    "extraction_date": "2026-05-24",
    "confidence": "high"
  },
  "page_index": {
    "1": ["S001", "S002"],
    "2": ["S003", "S004"]
  },
  "blocks": {
    "S001": { "page": 1, "type": "text", "section": "introduction", "description": "short description" }
  },
  "figures": {
    "F001": { "page": 3, "type": "figure", "description": "fig caption", "asset": "assets/fig1.png" }
  },
  "tables": {
    "T001": { "page": 6, "type": "table", "description": "table caption", "asset": "assets/table1.png" }
  }
}
```

### 3.3 字段说明

| 顶层键 | 必需 | 类型 | 说明 |
|--------|------|------|------|
| `metadata` | ✅ | object | 论文元数据 |
| `page_index` | ✅ | object | 页码 → 锚点ID数组的映射 |
| `blocks` | ✅ | object | 所有正文锚点，key=S### |
| `figures` | 推荐 | object | 图片锚点，key=F### |
| `tables` | 推荐 | object | 表格锚点，key=T### |

### 3.4 metadata 子字段

```json
{
  "title": "论文完整标题",
  "authors": "作者（逗号分隔）",
  "source": "期刊/arXiv:ID",
  "pages": 12,
  "paper_type": "methods | review | benchmark | survey",
  "extraction_date": "ISO 日期",
  "confidence": "high | medium | low"
}
```

### 3.5 blocks 中每个条目的格式

```json
{
  "S001": {
    "page": 1,
    "type": "text",
    "section": "introduction",
    "description": "本段介绍了XXX"
  }
}
```

| 字段 | 必需 | 说明 |
|------|------|------|
| `page` | ✅ | 起始页码（整数） |
| `type` | ❌ | 详见下方 type 取值表 |
| `section` | ❌ | 所属章节名 |
| `description` | ❌ | 一段简短中文描述 |

**type 取值（推荐，非强制）：**
`text`, `abstract`, `section_header`, `body_paragraph`, `figure`, `table`, `caption`, `reference`, `footnote`, `bullets`, `code_block`, `subsection_header`

### 3.6 assets 路径约定

```json
{
  "F001": {
    "page": 3,
    "type": "figure",
    "asset": "assets/fig1.png"
  }
}
```

assets/ 路径**始终相对于论文目录**。图片文件放在 `assets/` 子目录中。

### 3.7 已废弃的格式（不再使用）

以下格式在新处理中**不得使用**：

| 已废弃特征 | 替代方案 |
|-----------|---------|
| blocks 为 JSON 数组 | blocks 为 JSON 对象（以 S### 为 key）|
| `meta` 代替 `metadata` | 统一使用 `metadata` |
| `source_blocks` / `table_blocks` / `figure_blocks` 拆分 | 统一合并到 `blocks` + `figures` + `tables` |
| `mapping` 数组 | 使用 `page_index` + `blocks` |
| 无 page_index | 必须包含 page_index |
| `{"format": "anchor-based"}` 等元字段 | 不额外声明格式，结构即声明 |
| captions 作为独立顶层键 | captions 内容并入 figures/tables 的 description 字段 |

### 3.8 图/表映射规则（source_map ↔ paper.md）

source_map.json 的 `figures` 和 `tables` 段必须与 paper.md 的图片引用保持**双向映射一致**。

**规则：**

| # | 规则 | 说明 | 违反后果 |
|---|------|------|----------|
| 1 | **每图必有条目** | paper.md 中每个 `![...](...)` 图片必须在 source_map 中有唯一对应的 `figures[k]` 或 `tables[k]` 条目 | 渲染时无法建立索引关联 |
| 2 | **asset 路径一致** | source_map 条目中的 `asset` 路径必须与 paper.md 中 `![...](path)` 的 path 一致 | 图片无法被索引定位 |
| 3 | **description 有含义** | 描述不可仅写 `"Figure 1"`，必须包含内容描述（如 `"图1 | 原理进化示意图"` 或 `"TripleCheck pipeline overview"`）| 降低索引可用性 |
| 4 | **去重** | 同一物理图片在 source_map 中只出现一次（如 Fig.1 多次引用但 asset 相同，只保留一个条目） | 索引膨胀、混淆 |
| 5 | **markdown 表格** | paper.md 中的 markdown 表格（行首以 `|` 开头）也应在 `tables` 中有条目，`asset` 可为空字符串 | 表格无法被索引 |

**验证脚本：**

```bash
cd docs/paper
python3 << 'EOF'
import json, re
from pathlib import Path

for d in sorted(Path('.').iterdir()):
    if not d.is_dir() or not (d / 'source_map.json').exists():
        continue
    sm = json.load(open(d / 'source_map.json'))
    content = (d / 'paper.md').read_text()
    
    img_refs = re.findall(r'!\[(.*?)\]\(([^)]+)\)', content)
    for alt, path in img_refs:
        is_table = bool(re.search(r'Table|表', alt))
        entries = sm.get('tables', {}) if is_table else sm.get('figures', {})
        
        found = False
        for k, v in entries.items():
            if path in v.get('asset', '') or alt[:20] == v.get('description', '')[:20]:
                found = True
                break
        
        if not found:
            print(f"⚠️  {d.name}: 图片 '{alt[:30]}' 在 source_map 中无对应条目")
EOF
```

---

## 4. 处理流程（PDF → 最终文件）

### 4.1 标准流水线

```
Step 1: PDF 获取
  ├── 下载原始 PDF
  └── 放入论文目录，重命名为清晰文件名（可选）

Step 2: 文档解析（双通道）
  ├── 用法: python3 docs/paper/docling_parse.py <PDF> <输出目录>
  │
  ├── 通道 A — Docling API
  │   ├── 上传 PDF → POST /v1/convert/file
  │   ├── 输出: docling_raw.md + docling_raw.json + assets/page_*.png
  │   └── do_formula_enrichment=true 尝试公式 LaTeX 识别
  │
  ├── 通道 B — PyMuPDF
  │   ├── 直接从 PDF 文件提取嵌入的独立图片
  │   ├── 输出: assets/fig_p{page}_{idx}.ext
  │   └── 按 Docling 检测顺序生成 alias: assets/fig_{n:02d}_p{page}.png
  │
  ├── 自动生成: source_map.json（章节锚点 + 图片/表格索引）
  └── 验证：检查 docling_raw.md 正文完整性 + assets/ 图是否齐全

Step 3: 中英对照翻译（nature-reader / 人工精校）
  ├── 依据 source_map.json 的锚点结构，逐段翻译
  ├── 生成 paper.md（标准格式）
  └── 输出：paper.md（初稿）

Step 4: 人工质检
  ├── 检查术语一致性（水稻品种名、基因名等）
  ├── 检查图片位置和完整性
  ├── 补充阅读笔记（## 阅读提示）
  └── 输出：paper.md（终稿）

Step 5: source_map.json 精修
  ├── 补全 figures/tables 的 asset 路径
  ├── 补全 page_index
  ├── 补全 metadata
  ├── 逐项核对 paper.md 中所有 `![...](...)` 图片均在 source_map 中有对应条目
  ├── 运行 §3.8 的验证脚本确保双向映射一致
  └── 输出：source_map.json（终版）

Step 6: 索引重建
  └── node build-reader.js（更新 papers-index.json + papers-data.js）
```

### 4.2 最小可行版本（快速处理）

当时间有限时，至少完成以下文件即可让 paper-reader 渲染：

```
论文目录/
├── paper.md          # 必需：标准格式，至少有一部分锚点块
└── assets/           # 推荐：至少包含文章中引用的图
```

此时不生成 source_map.json，paper-reader 会自动回退到纯文本 fetch 模式。

### 4.3 一键解析脚本

使用 `docs/paper/docling_parse.py` 自动完成整个解析流程：

```bash
# 安装依赖（只需一次）
pip3 install PyMuPDF

# 解析 PDF（双通道：Docling API 文本 + PyMuPDF 图片）
python3 docs/paper/docling_parse.py path/to/paper.pdf docs/paper/论文目录
```

执行后自动生成：

```
论文目录/
├── paper.md              # 中英对照阅读笔记（需人工/LLM 翻译后填充）
├── source_map.json       # 自动生成的结构化索引
├── docling_raw.md        # Docling API 返回的 Markdown 原文
├── docling_raw.json      # Docling API 返回的结构化 JSON
├── assets/
│   ├── page_01.png       # 全页渲染图（Docling API）
│   ├── fig_01_p34.png    # 独立图片（PyMuPDF），按检测顺序命名
│   ├── fig_02_p34.png    #   fig_NN_p{page}.png 格式
│   └── ...               #   paper.md 中直接引用此命名
└── *.pdf                 # 原始 PDF
```

脚本双通道说明：

| 通道 | 工具 | 产出 | 作用 |
|------|------|------|------|
| A | Docling API `/v1/convert/file` | `docling_raw.md/.json`, `page_*.png` | 文本提取、结构分析、全页渲染 |
| B | PyMuPDF (`fitz`) | `fig_p{page}_{idx}.ext` + `fig_{n:02d}_p{page}.png` | 从 PDF 直接抠出独立图片 |

详细 API 文档见 `docs/docling/api.md`。

### 4.4 中文笔记版（Type B → Type A 升级路径）

当前 Type B（仅中文笔记）的 3 篇论文升级路径：

```
1. 找到原始 PDF（或 arXiv 链接）
2. 执行 Step 2-4（Docling API + nature-reader 翻译）
3. 将 paper.md 替换为标准格式
4. 添加 source_map.json
5. 验证 paper-reader 渲染一切正常
```

---

## 5. 验证清单

新添加/修改一篇论文后，运行以下清单验证完整性：

```
□ paper.md 存在
□ paper.md 包含至少一个锚点块（<a id="SXXX">）
□ paper.md 的锚点块包含 **Original:** 和 **中文:**
□ paper.md 以 ## 阅读提示 结尾（或至少有一个总结段落）
□ paper.md 没有使用废弃格式（**原文 (Chinese):** 等）
□ paper.md 图片放在所属章节末尾，不跨节边界（见 §2.7）
□ source_map.json 存在且格式为标准 schema（如适用）
□ source_map.json 的 blocks 键名与 paper.md 的锚点 ID 一致
□ source_map.json 的 figures/tables 覆盖 paper.md 全部图片（见 §3.8）
□ source_map.json 每个 figure/table 条目有含义明确的 description
□ assets/ 存在且包含所有引用的图片
□ 运行 node build-reader.js 无报错
□ 双击 paper-reader.html 验证渲染
```

---
