#!/usr/bin/env python3
"""手动句读模板：为每轮对话按语气/停顿添加全角标点，并做逐字保真校验。

用法：
1. 以步骤 4 纠错后的 turns_corrected.json 为底本，逐条人工加全角标点，填入 PUNCT 字典。
2. 运行本脚本：校验通过与 turns_corrected.json 比对（去标点后），通过则写出 turns_punct.json。

只允许加标点，不允许增删改字（不编造原则）。标点一律全角（，。？！；：……——）。
"""
import json, re

# ===== 在此逐条填写加好全角标点的文本（键为 turns_final.json 的索引）=====
PUNCT = {
    0: "（第 0 轮加好全角标点的正文。）",
    1: "（第 1 轮……）",
    # ... 全部轮次 ...
}

STRIP = re.compile(r"[\s，。？；：、！……——\-–（）()“”‘’\"'\.,\?;:!]")

turns = json.load(open("turns_corrected.json", encoding="utf-8"))
errors, out = [], []
for i, t in enumerate(turns):
    if i not in PUNCT:
        errors.append((i, "MISSING"))
        continue
    mine, orig = PUNCT[i], t["text"]
    if STRIP.sub("", mine) != STRIP.sub("", orig):
        errors.append((i, "MISMATCH", STRIP.sub("", mine), STRIP.sub("", orig)))
    out.append({"speaker": t["speaker"], "start": t["start"], "end": t["end"], "text": mine})

if errors:
    print("FIDELITY ERRORS:", len(errors))
    for e in errors:
        print(e)
else:
    with open("turns_punct.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("ALL", len(out), "TURNS FIDELITY OK -> turns_punct.json")
