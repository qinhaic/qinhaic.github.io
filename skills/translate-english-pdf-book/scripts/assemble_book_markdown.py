#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_translations(paths: list[Path]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            key = item["id"]
            if key in result:
                raise ValueError(f"duplicate translation ID across files: {key}")
            result[key] = item["translation"].strip()
    return result


def numeric_id(value: str) -> int:
    if not value.startswith("P") or not value[1:].isdigit():
        raise ValueError(f"invalid paragraph ID: {value}")
    return int(value[1:])


def main() -> None:
    ap = argparse.ArgumentParser(description="Assemble verified translation JSONL files into a book Markdown file.")
    ap.add_argument("sections", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("translations", nargs="+", type=Path)
    ap.add_argument("--book-title", required=True)
    ap.add_argument("--author", default="")
    args = ap.parse_args()
    sections = json.loads(args.sections.read_text(encoding="utf-8"))
    translated = load_translations(args.translations)
    parts = [f"# 《{args.book_title}》", "", "## 全书中文学习译稿", ""]
    if args.author:
        parts.extend([f"**作者：**{args.author}", ""])
    parts.extend([
        "**说明：**本稿为依据用户提供的英文 PDF 制作的 AI 辅助个人学习译稿，并非正式出版物；学术引用请以英文原版为准。",
        "", "---", "", "# 目录", ""
    ])
    parts.extend(f"{i}. {section['title']}" for i, section in enumerate(sections, 1))
    used: set[str] = set()
    for section in sections:
        start, end = numeric_id(section["start_id"]), numeric_id(section["end_id"])
        if end < start:
            raise ValueError(f"reversed range in section: {section['title']}")
        parts.extend(["", f"# {section['title']}", ""])
        for number in range(start, end + 1):
            key = f"P{number:06d}"
            if key not in translated:
                raise ValueError(f"missing translation for {key}")
            if key in used:
                raise ValueError(f"overlapping section range at {key}")
            used.add(key)
            parts.extend([translated[key], ""])
    unused = sorted(set(translated) - used)
    if unused:
        raise ValueError(f"translations outside section ranges: {unused[:20]}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as fh:
        fh.write("\n".join(parts).rstrip() + "\n")
    print(f"wrote {args.output} with {len(used)} translated paragraphs")


if __name__ == "__main__":
    main()

