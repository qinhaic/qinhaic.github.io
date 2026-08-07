# 音频转写流水线详情（最终版，含改进原因与踩坑）

## 依赖（venv）
PEP 668：macOS Homebrew Python 禁止裸 pip install，必须先建虚拟环境。
```
python3 -m venv venv
venv/bin/pip install faster-whisper resemblyzer scikit-learn numpy av python-docx librosa torch
```
已验证版本（2026-08，Apple M1 / macOS 15 / Python 3.14）：
faster-whisper 1.2.1、ctranslate2 4.8.1、torch 2.13.0、resemblyzer 0.1.4、scikit-learn 1.9.0、av 18.0.0、python-docx 1.2.0、numpy 2.4.6、librosa 0.11.0。
首次运行会下载 medium 模型（约 1.5GB）；网络失败需重试，或用 huggingface_hub.snapshot_download 断点续传。

## 步骤 1：转写 — 改进原因
- **不要用 small 模型**：中文口语识别质量差（实测「你咋样」→「你打压」，「de Shazer」→「Dick Sake」）。medium 后明显改善。
- **word_timestamps=True**：为句读提供字级时间参考；但字级时间戳噪声大，不能直接用于自动断句。
- **vad_filter=True、min_silence_duration_ms=500**：过滤静音段，避免输出无意义文本。
- 其余参数：language="zh"、beam_size=5、initial_prompt="以下是普通话口语对话。"

## 步骤 2：说话人分离
- resemblyzer VoiceEncoder(device="cpu") 提取 256 维声纹；2s 窗口 / 0.5s 步长滑窗；RMS<0.01 跳过静音窗口。
- 归一化后 KMeans(n_clusters=2, n_init=10) 聚类。
- 每转写段按「窗口中心落在段内」的标签多数投票；无窗口落入时取最近中心。
- 按首次出现顺序映射「说话人1/说话人2」（中性编号，不推断身份）。
- 相邻同说话人段合并为轮次（turn），只保留首段的 start 与末段的 end。
- 实测：154 轮中误标约 1-2 处，需人工按语法连续性修正。

## 步骤 3：人工修正说话人误标
思路（脚本 template）：用文本片段匹配定位误标轮次 → 改 speaker → 重新合并相邻同说话人轮次。判断依据是语法/语义是否连贯（如一句话中途被切开、答句归错人）。

## 步骤 4：句读 — 关键改进（自动方案已放弃）
- **基于段间停顿的自动加标点失败**：合并成轮次后轮内停顿≈0s，无法用停顿切句。
- **基于字级时间戳重建再断句失败**：~100/154 轮与原文错位；即使正常样例也过度标点（如把「你还好吗」标成「你还好吗?。」）。
- **最终方案：人工逐句加标点**，按语气与停顿判断，标点一律全角（，。？！；：……——）。

## 步骤 5：逐字保真校验（不编造原则的兜底）
STRIP 正则去除标点后比对原文（见 scripts/punctuate.py）。不一致则打印首个差异，修正后重跑，全部通过才写 turns_punct.json。
**教训**：人工句读曾产生 16 处逐字错误（多加/漏加/改写字符，如「远远要比…」漏了「这些」、「劇透」被简化成「剧透」、多加了「吗」/「就」/「的」）。必须用该校验兜底，任何「顺手改字」都不允许。

## 步骤 6：全角标点检查
扫描半角 , . ; : ? ! ( ) " ' 等，任何命中即不合格。用户明确要求全角，半角会被打回重做（实测反馈过）。

## 步骤 7：Word 生成（python-docx）
- 宋体需同时设置 w:ascii / w:hAnsi / w:eastAsia 三个 rFonts 属性，否则中文显示为默认字体。
- 标题居中 16pt 加粗；副标题灰色 10.5pt 居中。
- 每轮：加粗「说话人N」+ 灰色 `[HH:MM:SS]` 开始时间戳（10.5pt）一行；正文另起一行、左缩进 24pt。
- 行距 1.5 倍，段后 6pt，段前 8pt。
- 文末一行灰色小字注明「语音识别自动生成，个别词句/人名可能有误」。
- 时间戳格式 HH:MM:SS，四舍五入取整。

## 故障排查
- pip 装不上 → PEP 668，用 venv。
- 模型下载失败 → 重试或 snapshot_download 续传。
- 音频无内容 → 先检查文件大小/时长，避免对空文件跑全流程。
- 录音结尾长静音 → 转写会以静音段收尾，交付前可提示用户，不必强删。
