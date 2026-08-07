#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def load_jsonl(path: Path, field: str) -> tuple[dict[str, dict], list[str]]:
    records: dict[str, dict] = {}
    duplicates: list[str] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        key = item.get("id")
        if not key or field not in item:
            raise ValueError(f"{path}:{n} must contain id and {field}")
        if key in records:
            duplicates.append(key)
        records[key] = item
    return records, duplicates


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate one-to-one source/translation coverage.")
    ap.add_argument("source", type=Path)
    ap.add_argument("translation", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    source, source_dupes = load_jsonl(args.source, "source")
    target, target_dupes = load_jsonl(args.translation, "translation")
    source_ids, target_ids = set(source), set(target)
    missing = sorted(source_ids - target_ids)
    extra = sorted(target_ids - source_ids)
    empty, english_heavy, marker_leaks, number_warnings = [], [], [], []
    for key in sorted(source_ids & target_ids):
        src = source[key]["source"]
        zh = target[key]["translation"].strip()
        if not zh:
            empty.append(key)
            continue
        letters = re.findall(r"[A-Za-z]", zh)
        cjk = re.findall(r"[\u3400-\u9fff]", zh)
        if len(letters) > 80 and len(letters) > len(cjk) * 1.5:
            english_heavy.append(key)
        if re.search(r"<<<|>>>|\b(?:TODO|TRANSLATE|SYSTEM|USER)\b", zh, re.I):
            marker_leaks.append(key)
        src_nums = set(re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?", src))
        zh_nums = set(re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)?%?", zh))
        lost = sorted(src_nums - zh_nums)
        if lost:
            number_warnings.append({"id": key, "missing_numbers": lost[:12]})
    errors = {
        "duplicate_source_ids": source_dupes,
        "duplicate_translation_ids": target_dupes,
        "missing_ids": missing,
        "extra_ids": extra,
        "empty_translations": empty,
        "marker_leaks": marker_leaks,
    }
    warnings = {"english_heavy": english_heavy, "number_mismatches": number_warnings}
    passed = not any(errors.values())
    report = {
        "passed": passed,
        "source_segments": len(source),
        "translation_segments": len(target),
        "errors": errors,
        "warnings": warnings,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()

