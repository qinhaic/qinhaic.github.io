# 多栏 / 复杂版式提取规范

本文件记录单栏书之外的版式适配经验，重点是从两栏（APA 期刊论文、双栏书籍）PDF
稳定提取可分段文本。2026 年在 Baskin-Sommers 等 2014《自恋型人格障碍中的共情》
11 页两栏论文上验证通过。

## 何时需要坐标提取

- `pdftotext -layout` 会把左栏和右栏文本交错放在同一物理行，缩进检测不可行。
- 判断标准：layout 文本行内出现"左栏句子后半 + 右栏句子前半"拼接、或 `>>` 换栏
  异常时，改用 `scripts/extract_columns.py`（基于 PyMuPDF 块坐标）。

## 阈值与选取方法

`extract_columns.py --analyze` 打印每页块的 x 范围，据此取栏分隔线。

- `--mid`：栏间中线（左栏 `x0 < mid ≤ 右栏 x0`）。两栏 APA 页约在页宽的 47% 处。
- `--header-bottom`：页眉下界（刊头、running header），低于此 y 的块丢弃。
- `--footer-top`：页脚上界（页码、脚注底线），起始 y 大于此的块丢弃。正文可能伸到
  `footer_top - 1` 左右，选阈值前先看正文最下块的 y1。
- `--front-end`：第 1 页正文起点（标题、作者、摘要、关键词区域下缘）。
- `--footnote-y`：第 1 页脚注起点（作者单位、通讯、致谢）。用 `y 且 x<mid` 双重条件
  区分，避免把右栏正文块误当脚注。
- `--merge-gap` / `--max-tall`：相邻块间隙 < merge_gap 且前一块高度 < max_tall 时合并
  （用于把被拆成两行的标题还原为一整段）。默认 6.0 / 22.0。

第 1 页阅读顺序固定为：front matter → 脚注 → 左栏 → 右栏 →（其余页）左栏 → 右栏。

## 文本清洗与连字符

- 行断连字符：`(?<=[a-z])-[ ]+(?=[a-z])` 删除。但会把真正的复合词错误折叠
  （`self-enhancement`→`selfenhancement`），需用 `--correction bad=good` 或内置
  `CORRECTIONS` 逐个恢复。见本项目例：`selfenhancement`、`vis-a`-vis`→`vis-à-vis`、
  `overor underestimate`→`over- or underestimate`。
- 软连字符 `\xad` 直接删除。
- PDF 内嵌控制字符（0x01–0x08、0x0b、0x0c、0x0e–0x1f）统一替换为 `-`（常见于
  en-dash 与百分号范围，如 `37%`+控制字符+`39%`）。

## 版权水印

APA 类 PDF 带页缘水印（"This article is intended solely for the personal use of
the individual user…"）。PyMuPDF 文本层通常已排除，但 `pdftotext -raw` 会保留。
确认水印不是正文内容；脚本内置 `WATERMARK_PATTERNS` 过滤。不要把它翻译进正文。

## 验收标准

- 每段一个 `{"id","page","source"}`，ID 从 `P000001` 连续编号。
- 同页内、跨页的段落顺序与版心实际阅读顺序一致（逐页抽查页首和页尾）。
- 页眉、页脚、页码、水印未混入正文。
- 被拆两行的标题合并完整；复合连字符词已还原。
- 输出 `qa/column-profile.json` 记录所用阈值，供复现。
