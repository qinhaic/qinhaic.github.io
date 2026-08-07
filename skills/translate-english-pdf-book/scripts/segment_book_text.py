#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PAGE = re.compile(r"^<<<PAGE_(\d{4})>>>$")


def main() -> None:
    ap = argparse.ArgumentParser(description="Create stable paragraph IDs from page-marked PDF text.")
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    lines = args.input.read_text(encoding="utf-8").splitlines()
    page = 0
    paragraph_page = 0
    paragraphs: list[tuple[int, str]] = []
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, paragraph_page
        text = " ".join(buffer).strip()
        text = re.sub(r"(?<=[a-z])-[ ]+(?=[a-z])", "", text)
        text = re.sub(r"\s+", " ", text)
        if text:
            paragraphs.append((paragraph_page or page, text))
        buffer = []
        paragraph_page = 0

    for raw in lines:
        match = PAGE.match(raw.strip())
        if match:
            page = int(match.group(1))
        elif not raw.strip():
            flush()
        else:
            starts_indented_paragraph = bool(re.match(r"^\s{3,}\S", raw))
            if starts_indented_paragraph and buffer:
                flush()
            if not buffer:
                paragraph_page = page
            buffer.append(raw.strip())
    flush()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as fh:
        for index, (page_no, source) in enumerate(paragraphs, 1):
            fh.write(json.dumps({"id": f"P{index:06d}", "page": page_no, "source": source}, ensure_ascii=False) + "\n")
    print(f"wrote {len(paragraphs)} segments to {args.output}")
    print("Review headers, footers, cross-page sentences, headings, notes, and tables before translation.")


if __name__ == "__main__":
    main()
