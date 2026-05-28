# PaperReader-agent

<p align="center">
  <a href="README.md">🇨🇳 中文</a> | <a href="README.en.md">🇬🇧 English</a>
</p>

**双语论文阅读工作流。** 把学术 PDF 交给 AI，自动解析、翻译、排版，生成可离线打开的双语对照阅读笔记。

## 用法（就三步）

### 1. 配环境

```bash
git clone <repo>
cd paper-reader

# Python 依赖（MinerU PDF 解析需要）
pip3 install PyMuPDF

# 安装 AI 代理技能（让智能体知道怎么处理论文）
git clone https://github.com/Yuan1z0825/nature-skills.git

# 编辑 mineru_parse.py，配好 MinerU API 地址
#   SERVER = "http://your-mineru-host:8801"
#   API_KEY = "your-api-key"
```

**前置依赖：**
- ⬜ **MinerU API** 服务（PDF 解析引擎，必选）— 部署或询问团队内网地址
- ⬜ **nature-skills**（AI 技能插件，必选）— `git clone https://github.com/Yuan1z0825/nature-skills.git`
- ⬜ **Python 3 + PyMuPDF**（可选，仅 mineru_parse.py 需要）

### 2. 交给 AI

在 **Claude Code / Codex / 其他 AI 代理** 中执行一条命令：

```
/nature-skills:nature-reader /path/to/paper.pdf /path/to/workflow-spec.md
```

AI 会自动完成：
- 调 MinerU API 解析 PDF（文本+图片+表格）
- 逐段翻译，生成中英对照 `paper.md`
- 把插图放到正确位置
- 必要时运行 `node build-reader.js` 构建索引

> 如果你用的是没有 nature-reader 技能的 AI，把 `mineru_raw.md` 和 `mineru_raw.json` 喂给它，让它按 `workflow-spec.md` 的格式生成 `paper.md` 即可。

### 3. 打开看

```bash
# 如果 AI 没自动构建索引
node build-reader.js

# 浏览器打开
open paper-reader.html
```

就是这么简单。

---

## 目录结构

```
paper-reader/
├── paper-reader.html     # 阅读器（双击打开，无需服务器）
├── build-reader.js       # 索引构建（新论文后执行）
├── mineru_parse.py       # PDF 解析脚本
├── workflow-spec.md      # 格式规范（给 AI 看的）
│
├── papers-index.json     # 自动生成
├── papers-data.js        # 自动生成
│
├── 论文目录/              # 每篇论文一个目录
│   ├── paper.md          # 中英对照笔记（AI 生成）
│   ├── source_map.json   # 锚点索引
│   ├── assets/fig_*.png  # 插图
│   └── *.pdf             # 原始 PDF
└── ...
```

---

## FAQ

**新增论文后不显示？**
```bash
node build-reader.js
```

**没有 MinerU 服务？**
部署 [MinerU](https://github.com/opendatalab/MinerU)，或找团队要内网地址。配在 `mineru_parse.py` 顶部。

**没有 MinerU 也能用？**
可以。手动写 `paper.md`，然后 `node build-reader.js` 就行。MinerU 只是自动化辅助。

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `paper-reader.html` | 阅读器（双击打开） |
| `build-reader.js` | 索引构建工具 |
| `mineru_parse.py` | PDF 解析脚本（MinerU API） |
| `workflow-spec.md` | 给 AI 的格式规范 |
