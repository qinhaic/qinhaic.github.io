#!/usr/bin/env python3
"""Merge hand-translated segments + verbatim tail (references) into translation.jsonl.

Two supported translation sources:
  * --data FILE.py  a Python file defining `TRANSLATIONS = {id: zh_text, ...}`
  * --json FILE     a JSON file mapping {id: zh_text}

Segments with id >= VERBATIM_FROM are copied from the source verbatim (e.g. the
references section, kept in English per skill rules).  Fails loudly if any body
segment is missing a translation or any translation id is unused.

Usage:
  build_translations.py segments.jsonl [--data translations_data.py | --json tr.json]
      --verbatim-from P000076 --out translations/translation.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("segments", type=Path, help="plan/segments.jsonl")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--data", type=Path, help="python file defining TRANSLATIONS dict")
    src.add_argument("--json", type=Path, help="json file mapping id -> zh")
    ap.add_argument("--verbatim-from", type=str, default="",
                    help="id prefix/pivot: segments >= this are copied verbatim from source")
    ap.add_argument("--out", type=Path, default=Path("translations/translation.jsonl"))
    args = ap.parse_args()

    segments = [json.loads(l) for l in args.segments.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.data:
        ns: dict = {}
        exec(args.data.read_text(encoding="utf-8"), ns)
        if "TRANSLATIONS" not in ns:
            sys.exit("--data file must define TRANSLATIONS = {id: zh}")
        translations: dict[str, str] = ns["TRANSLATIONS"]
    else:
        translations = json.loads(args.json.read_text(encoding="utf-8"))

    out_records: list[dict] = []
    missing: list[str] = []
    for r in segments:
        iid = r["id"]
        if args.verbatim_from and iid >= args.verbatim_from:
            zh = r["source"]
        else:
            zh = translations.get(iid)
            if not zh or not zh.strip():
                missing.append(iid)
                continue
            zh = zh.strip()
        out_records.append({"id": iid, "translation": zh})

    used = {r["id"] for r in segments}
    unused = sorted(set(translations) - used)
    if missing:
        print("MISSING TRANSLATIONS:", missing, file=sys.stderr)
        sys.exit(1)
    if unused:
        print("UNUSED IDs in translation source:", unused, file=sys.stderr)
        sys.exit(1)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for rec in out_records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote {len(out_records)} translations to {args.out}")


if __name__ == "__main__":
    main()
