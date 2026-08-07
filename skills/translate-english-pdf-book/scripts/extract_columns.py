#!/usr/bin/env python3
"""Column-aware paragraph extraction for multi-column PDFs (APA two-column papers, etc.).

pdftotext -layout interleaves left and right column text on the same physical
line, so whitespace/indentation detection cannot separate columns.  This script
uses PyMuPDF block coordinates instead: split blocks by the column midline,
order each column by y (reading order), and filter headers/footers by y.

Typical thresholds for an APA page (points, top-left origin, y grows downward):
  --mid 270        x where the gutter sits (left col x0 < mid <= right col x0)
  --header-bottom 70     drop blocks fully above this (masthead, running header)
  --footer-top 724       drop blocks starting below this (page number)
  --front-end 435        page 1: y below this is front matter (title..keywords)
  --footnote-y 640       page 1: y above this + x<mid is the author/correspondence footnote

Use --analyze to print per-page block x-extents and pick the midline empirically.

Dependencies: pip install pymupdf   (poppler not required)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pymupdf

# Restore compound hyphens / characters that the line-break dehyphenation or
# control-char handling collapsed.  Extend via --correction "bad=good".
CORRECTIONS = {
    "selfenhancement": "self-enhancement",
    "selfenhancing": "self-enhancing",
    "selfrespect": "self-respect",
    "selfesteem": "self-esteem",
    "overor underestimate": "over- or underestimate",
    "interand intrapersonal": "inter- and intrapersonal",
    "powermotivated": "power-motivated",
    "vis-a`-vis": "vis-à-vis",
}

# Watermark-ish repeated text that is NOT content (APA copyright notice).
# PyMuPDF's text layer usually excludes it; if present, drop these blocks.
WATERMARK_PATTERNS = (
    re.compile(r"^This article is intended solely", re.I),
    re.compile(r"^In the public domain", re.I),
)


def clean(text: str, corrections: dict[str, str]) -> str:
    text = text.replace("\xad", "")                      # soft hyphen
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "-", text)  # stray control chars
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<=[a-z])-[ ]+(?=[a-z])", "", text)  # line-break hyphenation
    for bad, good in corrections.items():
        text = text.replace(bad, good)
    return text.strip()


def is_watermark(text: str) -> bool:
    return any(p.match(text.strip()) for p in WATERMARK_PATTERNS)


def merged(blocks: list[tuple], merge_gap: float, max_tall: float,
           corrections: dict[str, str]) -> list[str]:
    """Merge same-column blocks in reading order; keep split headings whole."""
    out: list[tuple] = []
    for b in sorted(blocks, key=lambda b: (b[1], b[0])):
        x0, y0, x1, y1, text = b
        piece = clean(text, corrections)
        if not piece or is_watermark(piece):
            continue
        if out:
            prev = out[-1]
            gap = y0 - prev[3]
            if gap < merge_gap and (prev[3] - prev[1]) < max_tall:
                out[-1] = (prev[0], prev[1], max(prev[3], y1), max(prev[3], y1),
                           prev[4] + " " + piece)
                continue
        out.append((x0, y0, x1, y1, piece))
    return [t[4] for t in out]


def norm_blocks(page, header_bottom: float, footer_top: float) -> list[tuple]:
    """Reduce PyMuPDF 7-tuples to (x0,y0,x1,y1,text), dropping headers/footers."""
    blocks = []
    for b in page.get_text("blocks"):
        x0, y0, x1, y1, text, _no, _typ = b
        if b[6] != 0 or y0 < header_bottom or y1 > footer_top:
            continue
        blocks.append((x0, y0, x1, y1, text))
    return blocks


def split_columns(blocks: list[tuple], mid: float) -> tuple[list[tuple], list[tuple]]:
    left = sorted((b for b in blocks if b[0] < mid), key=lambda b: (b[1], b[0]))
    right = sorted((b for b in blocks if b[0] >= mid), key=lambda b: (b[1], b[0]))
    return left, right


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("project", type=Path)
    ap.add_argument("--mid", type=float, default=270.0, help="column gutter x (default 270)")
    ap.add_argument("--header-bottom", type=float, default=70.0)
    ap.add_argument("--footer-top", type=float, default=724.0)
    ap.add_argument("--front-end", type=float, default=435.0, help="page-1 front matter bottom")
    ap.add_argument("--footnote-y", type=float, default=640.0, help="page-1 footnote top")
    ap.add_argument("--merge-gap", type=float, default=6.0)
    ap.add_argument("--max-tall", type=float, default=22.0)
    ap.add_argument("--no-first-page-special", action="store_true",
                    help="treat page 1 like any other page (no front/footnote split)")
    ap.add_argument("--correction", action="append", default=[], metavar="bad=good",
                    help="extra hyphen-collapse correction (repeatable)")
    ap.add_argument("--analyze", action="store_true",
                    help="print per-page block x-extents to choose --mid, then exit")
    args = ap.parse_args()

    pdf = args.pdf.expanduser().resolve()
    project = args.project.expanduser().resolve()
    if not pdf.is_file():
        sys.exit(f"Not a file: {pdf}")

    corrections = dict(CORRECTIONS)
    for item in args.correction:
        bad, _, good = item.partition("=")
        if not bad or not good:
            sys.exit(f"Bad --correction (want bad=good): {item}")
        corrections[bad] = good

    doc = pymupdf.open(pdf)

    if args.analyze:
        for pno in range(doc.page_count):
            page = doc[pno]
            xs = sorted(b[0] for b in page.get_text("blocks"))
            if xs:
                print(f"page {pno+1:3d}: x range {xs[0]:6.1f} .. {xs[-1]:6.1f} "
                      f"({len(xs)} blocks)")
        return

    segments: list[tuple[int, str]] = []
    for pno in range(doc.page_count):
        page = doc[pno]
        blocks = norm_blocks(page, args.header_bottom, args.footer_top)
        if pno == 0 and not args.no_first_page_special:
            front = [b for b in blocks if b[1] < args.front_end]
            foot = [b for b in blocks if b[1] >= args.footnote_y and b[0] < args.mid]
            body = [b for b in blocks if b[1] >= args.front_end and b not in foot]
            left, right = split_columns(body, args.mid)
            for piece in (merged(front, args.merge_gap, args.max_tall, corrections)
                          + merged(foot, args.merge_gap, args.max_tall, corrections)
                          + merged(left, args.merge_gap, args.max_tall, corrections)
                          + merged(right, args.merge_gap, args.max_tall, corrections)):
                segments.append((pno + 1, piece))
        else:
            left, right = split_columns(blocks, args.mid)
            for piece in (merged(left, args.merge_gap, args.max_tall, corrections)
                          + merged(right, args.merge_gap, args.max_tall, corrections)):
                segments.append((pno + 1, piece))

    seg_path = project / "plan" / "segments.jsonl"
    plain_path = project / "source" / "segments.txt"
    profile_path = project / "qa" / "column-profile.json"
    seg_path.parent.mkdir(parents=True, exist_ok=True)
    plain_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.parent.mkdir(parents=True, exist_ok=True)

    with seg_path.open("w", encoding="utf-8") as fh:
        for i, (pg, src) in enumerate(segments, 1):
            fh.write(json.dumps({"id": f"P{i:06d}", "page": pg, "source": src}, ensure_ascii=False) + "\n")
    with plain_path.open("w", encoding="utf-8") as fh:
        for i, (pg, src) in enumerate(segments, 1):
            fh.write(f"\n--- P{i:06d} (p.{pg}) ---\n{src}\n")
    profile_path.write_text(json.dumps({
        "script": "extract_columns.py",
        "params": {k: v for k, v in vars(args).items() if k not in ("pdf", "project")},
        "segments": len(segments),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {len(segments)} segments to {seg_path}")
    print(f"plain view: {plain_path}")
    print(f"profile:   {profile_path}")


if __name__ == "__main__":
    main()
