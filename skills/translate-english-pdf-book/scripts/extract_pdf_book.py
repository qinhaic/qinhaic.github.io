#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


def run(*args: str) -> str:
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout


def main() -> None:
    ap = argparse.ArgumentParser(description="Create a non-destructive English PDF book translation project.")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("project", type=Path)
    args = ap.parse_args()
    pdf = args.pdf.expanduser().resolve()
    project = args.project.expanduser().resolve()
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        raise SystemExit(f"Not a PDF file: {pdf}")
    if project.exists() and any(project.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty project: {project}")
    for command in ("pdfinfo", "pdftotext"):
        if not shutil.which(command):
            raise SystemExit(f"Missing required command: {command}")

    source = project / "source"
    for rel in (source, project / "plan", project / "translations", project / "qa" / "renders", project / "deliverables"):
        rel.mkdir(parents=True, exist_ok=True)

    info = run("pdfinfo", str(pdf))
    if re.search(r"^Encrypted:\s+yes", info, re.M | re.I):
        raise SystemExit("Encrypted PDF: obtain an authorized readable copy before translation.")
    layout_path = source / "extracted-layout.txt"
    raw_path = source / "extracted-raw.txt"
    subprocess.run(("pdftotext", "-layout", str(pdf), str(layout_path)), check=True)
    subprocess.run(("pdftotext", "-raw", str(pdf), str(raw_path)), check=True)
    raw = raw_path.read_text(encoding="utf-8", errors="replace")
    layout = layout_path.read_text(encoding="utf-8", errors="replace")
    raw_pages = raw.split("\f")
    layout_pages = layout.split("\f")
    if raw_pages and not raw_pages[-1].strip():
        raw_pages.pop()
    if layout_pages and not layout_pages[-1].strip():
        layout_pages.pop()
    # Keep exactly one newline before each page marker. Extra blank lines at
    # page boundaries would falsely terminate paragraphs that continue over a page.
    raw_marked = "".join(f"<<<PAGE_{i:04d}>>>\n{page.strip()}\n" for i, page in enumerate(raw_pages, 1))
    layout_marked = "".join(f"<<<PAGE_{i:04d}>>>\n{page.rstrip()}\n" for i, page in enumerate(layout_pages, 1))
    (source / "extracted-pages-raw.txt").write_text(raw_marked, encoding="utf-8")
    (source / "extracted-pages-layout.txt").write_text(layout_marked, encoding="utf-8")

    compact = re.sub(r"\s+", "", raw)
    alpha = sum(ch.isalpha() for ch in compact)
    quality = alpha / max(1, len(compact))
    page_match = re.search(r"^Pages:\s+(\d+)", info, re.M)
    metadata = {
        "source_pdf": str(pdf),
        "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "pdf_pages": int(page_match.group(1)) if page_match else None,
        "extracted_pages": len(raw_pages),
        "extracted_characters": len(raw),
        "alphabetic_ratio": round(quality, 4),
        "needs_ocr_review": len(raw.strip()) < max(1000, len(raw_pages) * 120) or quality < 0.45,
        "status": "extracted"
    }
    (project / "project.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
