# 项目文件约定

建议结构：

```text
project/
├── project.json
├── source/
│   ├── extracted-layout.txt            # 单栏书（extract_pdf_book.py）
│   ├── extracted-raw.txt
│   ├── extracted-pages-layout.txt
│   ├── extracted-pages-raw.txt
│   └── segments.txt                    # 双栏书明文视图（extract_columns.py）
├── plan/
│   ├── segments.jsonl                  # 分段源（单栏/双栏脚本均产出）
│   ├── sections.json
│   ├── glossary.csv
│   ├── translation-style.md
│   └── translations_data.py            # 可选：单文件译文源（TRANSLATIONS dict）
├── scripts/                            # 项目内定制脚本（不进交付）
├── translations/
│   ├── chapter-01.jsonl                # 方式 A：逐章译文
│   └── ...
│   └── translation.jsonl               # 方式 B：build_translations.py 合并产物
├── qa/
│   ├── validation.json
│   ├── column-profile.json             # 双栏提取所用阈值（复现用）
│   ├── open-questions.md
│   └── renders/
│       ├── full-book.pdf               # LibreOffice 渲染 PDF
│       └── contact-sheet.png
└── deliverables/
    ├── full-book.md
    ├── full-book.docx
    └── full-book.pdf
```

`segments.jsonl` 每行：

```json
{"id":"P000001","page":1,"source":"English paragraph"}
```

译文可用两种来源：

- **逐章 JSONL**：`translations/chapter-NN.jsonl`，每行含 `id` 与 `translation`，由
  `assemble_book_markdown.py` 直接合并。
- **单文件译文源**：`plan/translations_data.py` 定义 `TRANSLATIONS = {id: zh, ...}`，
  由 `build_translations.py` 合并为 `translations/translation.jsonl`；参考文献段可用
  `--verbatim-from` 直接复制英文原文（技能默认保留参考文献原文）。

译文 JSONL 每行：

```json
{"id":"P000001","translation":"中文段落","status":"translated"}
```

`sections.json`：

```json
[
  {"title":"序言","start_id":"P000001","end_id":"P000120"},
  {"title":"第一章　章节名","start_id":"P000121","end_id":"P000560"}
]
```

`project.json` 除来源信息外，持续更新以下恢复字段：

```json
{
  "status": "translating",
  "last_verified_section": "第六章",
  "next_segment_id": "P001421",
  "glossary_version": 3,
  "next_action": "翻译第七章第一批"
}
```

只把已经通过结构检查的章节标记为 `verified`。新会话必须从最后一个已验证检查点恢复，不依赖聊天记录猜进度。

人工调整分段时不要复用同一个 ID 表示不同源文。确需重分段时生成新版本并保留旧清单，以免译文错误对齐。
