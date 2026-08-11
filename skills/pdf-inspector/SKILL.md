---
name: 精神分析文献阅读
description: 用 pdf-inspector（Firecrawl 的 Rust PDF 库）检查与提取 PDF：检测文本型/扫描件/图片型/混合型、找出需 OCR 的页、定位表格页/分栏页、提取文本与 Markdown。适合阅读精神分析文献 PDF 前判断可提取性、定位扫描页，以及翻译质检。
---

# 精神分析文献阅读（基于 pdf-inspector）

基于 [firecrawl/pdf-inspector](https://github.com/firecrawl/pdf-inspector)（Rust 核心，本地解析，不联网、不依赖 OCR）。用于判断 PDF 是否可本地提取、定位扫描页/编码问题、提取文本与 Markdown——适合精神分析文献、论文 PDF 的阅读与质检。

## 环境
- 需要 Python 3.11+。建议用独立 venv 安装 pdf-inspector：
  `uv venv .venv && uv pip install --python .venv/bin/python pdf-inspector`
- 运行脚本（用 venv 的 Python）：
  `.venv/bin/python scripts/inspect_pdf.py …`

## 用法

检查报告（类型/置信度/页数/需OCR页/表格页/分栏页/Markdown 长度）：
```bash
.venv/bin/python scripts/inspect_pdf.py <pdf> --mode inspect
.venv/bin/python scripts/inspect_pdf.py <pdf> --mode inspect --json   # 机器可读
```

提取：
```bash
.venv/bin/python scripts/inspect_pdf.py <pdf> --mode text [--out out.txt]
.venv/bin/python scripts/inspect_pdf.py <pdf> --mode markdown [--out out.md]
.venv/bin/python scripts/inspect_pdf.py <pdf> --mode positions [--pages 1,3,5]
```

## 与整书中译/PDF 工作流配合
- **阅读前检查**：先跑 `--mode inspect`。`pdf_type=scanned/image_based` 或存在 `pages_needing_ocr` 时，该 PDF 文本层不可用，应先走 OCR 或确认是否继续。
- **双栏论文**：`pages_with_columns` 非空说明有多栏，配合 translate-english-pdf-book 技能的双栏坐标提取（extract_columns.py）。
- **质检**：对渲染后 PDF 跑 inspect，确认 `pdf_type` 与页数、是否有残留分栏异常。

## 注意事项
- pdf-inspector 只做本地解析与启发式提取，表格/标题识别非完美；复杂版式仍应抽查。
- `extract_text` 对部分版式（如双栏论文）可能返回空；纯文本优先用 `--mode markdown` 或 `--mode positions` 兜底。
