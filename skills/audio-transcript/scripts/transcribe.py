#!/usr/bin/env python3
"""Transcribe audio with faster-whisper, output JSON segments."""
import sys, json, time
from faster_whisper import WhisperModel

def fmt(sec):
    ms = int(round(sec * 1000))
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    return f"{h:02d}:{m:02d}:{s:02d}"

def main():
    audio = sys.argv[1]
    out_json = sys.argv[2]
    model_size = sys.argv[3] if len(sys.argv) > 3 else "medium"
    device = "cpu"
    compute_type = "int8"

    t0 = time.time()
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    print(f"Model {model_size} loaded in {time.time()-t0:.1f}s", flush=True)

    t1 = time.time()
    segments, info = model.transcribe(
        audio,
        language="zh",
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        initial_prompt="以下是普通话口语对话。",
        word_timestamps=True,
    )
    segs = []
    for s in segments:
        words = [{"w": w.word, "s": w.start, "e": w.end} for w in (s.words or [])]
        segs.append({"start": s.start, "end": s.end, "text": s.text.strip(), "words": words})
        print(f"{fmt(s.start)} -> {fmt(s.end)} | {s.text.strip()}", flush=True)
    print(f"transcribed {len(segs)} segments in {time.time()-t1:.1f}s", flush=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"duration": info.duration, "segments": segs}, f, ensure_ascii=False, indent=1)
    print("WROTE", out_json, flush=True)

if __name__ == "__main__":
    main()
