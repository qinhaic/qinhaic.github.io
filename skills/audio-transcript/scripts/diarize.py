#!/usr/bin/env python3
"""Speaker diarization: cluster whisper segments into 2 speakers via resemblyzer embeddings."""
import json, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
import av

def load_audio(path, sr=16000):
    container = av.open(path)
    stream = container.streams.audio[0]
    samples = []
    resampler = av.AudioResampler(format="s16", layout="mono", rate=sr)
    for frame in container.decode(stream):
        frame.pts = None
        for out in resampler.resample(frame):
            arr = out.to_ndarray().reshape(-1)
            samples.append(arr.astype(np.float32) / 32768.0)
    for out in resampler.resample(None):
        arr = out.to_ndarray().reshape(-1)
        samples.append(arr.astype(np.float32) / 32768.0)
    return np.concatenate(samples)

def main():
    audio_path = sys.argv[1]
    seg_json = sys.argv[2]
    out_json = sys.argv[3]

    wav = load_audio(audio_path)
    print(f"loaded audio: {wav.shape[0]/16000:.1f}s", flush=True)

    from resemblyzer import VoiceEncoder, preprocess_wav
    encoder = VoiceEncoder(device="cpu")
    print("voice encoder ready", flush=True)

    # Slide windows, embed non-silent windows
    win = int(2.0 * 16000)
    hop = int(0.5 * 16000)
    embeds, centers = [], []
    for start in range(0, len(wav) - win, hop):
        chunk = wav[start:start + win]
        rms = np.sqrt(np.mean(chunk ** 2))
        if rms < 0.01:  # skip silence
            continue
        emb = encoder.embed_utterance(chunk, return_partials=False)
        embeds.append(emb)
        centers.append((start + win / 2) / 16000.0)
    embeds = np.array(embeds)
    centers = np.array(centers)
    print(f"embedded {len(embeds)} windows", flush=True)

    # Normalize embeddings
    embeds = embeds / np.linalg.norm(embeds, axis=1, keepdims=True)

    # KMeans k=2
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=2, n_init=10, random_state=0).fit(embeds)
    labels = km.labels_
    n0, n1 = (labels == 0).sum(), (labels == 1).sum()
    print(f"cluster sizes: {n0} / {n1}", flush=True)

    # Map cluster label -> speaker A/B by total speech time (larger cluster irrelevant); label by first-appearance order later.
    # Assign each segment by majority vote of overlapping windows
    segs = json.load(open(seg_json, encoding="utf-8"))["segments"]
    for s in segs:
        st, en = s["start"], s["end"]
        mask = (centers >= st) & (centers <= en)
        if mask.sum() == 0:
            # nearest center
            idx = int(np.argmin(np.abs(centers - (st + en) / 2)))
            lab = labels[idx]
        else:
            vals = labels[mask]
            lab = int(np.bincount(vals, minlength=2).argmax())
        s["cluster"] = lab

    # Label clusters by first appearance -> speaker 1 / speaker 2
    seen = {}
    next_id = 1
    for s in segs:
        c = s["cluster"]
        if c not in seen:
            seen[c] = next_id
            next_id += 1
        s["speaker"] = seen[c]

    # Merge consecutive same-speaker segments into turns
    turns = []
    for s in segs:
        if turns and turns[-1]["speaker"] == s["speaker"]:
            turns[-1]["end"] = s["end"]
            turns[-1]["text"] += s["text"]
        else:
            turns.append({"speaker": s["speaker"], "start": s["start"], "end": s["end"], "text": s["text"]})

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(turns, f, ensure_ascii=False, indent=1)
    print(f"WROTE {out_json}: {len(turns)} turns", flush=True)
    for t in turns[:60]:
        print(f"S{t['speaker']} {t['start']:.1f}-{t['end']:.1f}: {t['text'][:60]}", flush=True)

if __name__ == "__main__":
    main()
