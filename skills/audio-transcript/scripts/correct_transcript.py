#!/usr/bin/env python3
"""LLM 转录纠错校验脚本：应用 LLM 判断的修正，校验合理性，写出修正后文件。

用法：
  1. LLM 读 turns_final.json，逐轮扫描声调/同音字/近音词误识。
  2. LLM 生成 corrections.json，格式：[{"turn": 0, "old": "贪气", "new": "叹气"}, ...]
  3. 运行本脚本校验并应用修正：
     venv/bin/python correct_transcript.py turns_final.json corrections.json turns_corrected.json

校验规则：
  - old 必须在指定轮次中存在（精确匹配）
  - new 与 old 长度接近（单字替换为主，最多差 2 字）
  - 不允许大段删改
"""

import json, sys

def validate_and_apply(turns, corrections):
    """Validate each correction and apply. Returns (corrected_turns, report_lines)."""
    report = []
    corrected = [dict(t) for t in turns]  # deep copy

    for c in corrections:
        idx = c["turn"]
        old_s = c["old"]
        new_s = c["new"]

        if idx < 0 or idx >= len(corrected):
            report.append(f"ERROR turn {idx}: index out of range (0-{len(corrected)-1})")
            continue

        text = corrected[idx]["text"]
        count = text.count(old_s)
        if count == 0:
            report.append(f"WARNING turn {idx}: '{old_s}' not found — skipped")
            continue

        # Length sanity check: new should not differ from old by more than 3 chars
        if abs(len(new_s) - len(old_s)) > 3:
            report.append(f"WARNING turn {idx}: length diff {len(old_s)}→{len(new_s)} — skipped (suspicious)")
            continue

        # Apply
        corrected[idx]["text"] = text.replace(old_s, new_s)
        tag = f"({count} occurrences)" if count > 1 else ""
        report.append(f"OK turn {idx}: '{old_s}' → '{new_s}' {tag}")

    return corrected, report


def main():
    if len(sys.argv) < 4:
        print("用法: venv/bin/python correct_transcript.py <turns_final.json> <corrections.json> <turns_corrected.json>")
        sys.exit(1)

    turns = json.load(open(sys.argv[1], encoding="utf-8"))
    corrections = json.load(open(sys.argv[2], encoding="utf-8"))

    corrected, report = validate_and_apply(turns, corrections)

    with open(sys.argv[3], "w", encoding="utf-8") as f:
        json.dump(corrected, f, ensure_ascii=False, indent=1)

    print(f"Applied {len([r for r in report if r.startswith('OK')])} / {len(corrections)} corrections")
    for line in report:
        print(f"  {line}")
    print(f"WROTE {sys.argv[3]}")


if __name__ == "__main__":
    main()
