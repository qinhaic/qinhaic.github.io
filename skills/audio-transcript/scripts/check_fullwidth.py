#!/usr/bin/env python3
"""全角标点检查：扫描 turns JSON 中每轮的半角标点，任何命中即不合格。

用法：venv/bin/python check_fullwidth.py <turns_punct.json>
"""
import json, re, sys

path = sys.argv[1] if len(sys.argv) > 1 else "turns_punct.json"
turns = json.load(open(path, encoding="utf-8"))
half = re.compile(r'[,.;:?!()"\']')
hits = []
for i, t in enumerate(turns):
    m = half.findall(t["text"])
    if m:
        hits.append((i, m, t["text"][:50]))
print("turns with half-width punct:", len(hits))
for h in hits[:15]:
    print(h)
