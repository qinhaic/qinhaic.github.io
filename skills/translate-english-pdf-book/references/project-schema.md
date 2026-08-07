# 项目文件约定

建议结构：

```text
project/
├── project.json
├── source/
│   ├── extracted-layout.txt
│   ├── extracted-raw.txt
│   ├── extracted-pages-layout.txt
│   ├── extracted-pages-raw.txt
│   └── segments.jsonl
├── plan/
│   ├── sections.json
│   ├── glossary.csv
│   └── translation-style.md
├── translations/
│   ├── chapter-01.jsonl
│   └── ...
├── qa/
│   ├── validation.json
│   ├── open-questions.md
│   └── renders/
└── deliverables/
    ├── full-book.md
    ├── full-book.docx
    └── full-book.pdf
```

`segments.jsonl` 每行：

```json
{"id":"P000001","page":1,"source":"English paragraph"}
```

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
