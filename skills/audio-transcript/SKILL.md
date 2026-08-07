---
name: audio-transcript
description: 此技能用于把音频/录音转写成带说话人标注与开始时间戳的对话稿 Word 文档。当用户要求「把录音转成对话稿」「音频转 word」「整理录音文字」「转写音频成对话稿」「转录录音」等时使用。
version: 1.0.0
---

# 音频转写为对话稿 Word

把录音/音频（m4a、mp3、wav 等）转写成按说话轮次组织的对话稿，输出桌面 Word 文档。要求：说话人标注、开始时间戳、全角标点、宋体排版、逐字保真。

## 前置条件
- 使用 Python 虚拟环境（macOS Homebrew Python 受 PEP 668 限制，禁止直接 pip install）。
- 依赖清单见 references/pipeline-details.md「依赖」一节。

## 完整流程（最终改进版）

对每个音频按以下 8 步执行：

**1. 转写** — 用 faster-whisper（medium 模型、int8、CPU）
```
venv/bin/python scripts/transcribe.py <音频> <full_transcript.json> medium
```
要点：language=zh、beam_size=5、vad_filter=True、word_timestamps=True。不要用 small 模型（中文口语误识严重）。

**2. 说话人分离** — resemblyzer 声纹 + KMeans(k=2) 聚类
```
venv/bin/python scripts/diarize.py <音频> <full_transcript.json> <turns.json>
```
要点：2s 滑窗/0.5s 步长、RMS 过滤静音；按首次出现顺序标「说话人1/说话人2」，不推断身份；相邻同说话人段合并为轮次。

**3. 人工核查说话人误标** — 听对话语境，按语法/语义连续性修正错标，再合并相邻同说话人轮次。

**4. 手动加句读（全角标点）** — 逐句按语气与停顿加标点。不要用自动加标点（基于停顿/时间戳的自动方案会过度标点，如「你还好吗?。」）。

**5. 逐字保真校验** — 用 STRIP 正则去掉标点后与原文比对，只允许加标点，不允许增删改字（不编造原则）。见 scripts/punctuate.py。

**6. 全角标点检查** — 扫描半角标点（,.;:?!()" 等），必须全部为全角。见 scripts/check_fullwidth.py。

**7. 生成 Word** — python-docx，宋体排版
```
venv/bin/python scripts/generate_doc.py <turns_punct.json> <输出.docx> <标题> <副标题> <文末说明>
```

**8. 交付** — 输出到桌面；保留旧版本不覆盖；告知用户文件路径。

## 交付格式（用户硬性偏好）
- 字体宋体：正文小四 12pt、标题 16pt、时间戳灰色 10.5pt。
- 时间戳只记开始时间 `[HH:MM:SS]`、灰色小字；不记结束时间。
- 每轮：加粗「说话人N」+ 灰色时间戳一行，正文另起一行（左缩进）。
- 1.5 倍行距，段后间距适中。
- 标点一律全角（用户明确要求，半角会被打回）。
- 文末一行注：语音识别自动生成，个别词句/人名可能有误。
- 说话人用中性编号，不推断身份。

## 关键原则
- 不编造：句读只改标点，不改字；不确定就明说不确定。
- 保留中间产物（full_transcript.json、turns_final.json、turns_punct.json）便于复查。

## 附加资源
- references/pipeline-details.md — 每步参数、改进原因、踩坑记录、完整依赖清单。
- scripts/transcribe.py、diarize.py、punctuate.py、check_fullwidth.py、generate_doc.py — 可复用脚本（均为已验证的最终版）。
