#!/usr/bin/env python3
"""Resemblyzer-based speaker diarization for the voice-clone skill.

Used by scripts/diarize.js via a small Node wrapper. The Node script
just shells out to this file; we keep the heavy Python deps in one
place so a `pip install` upgrade doesn't require touching Node code.

The skill calls this in the SKILL.md "Speaker attribution" stage.
Run it directly only for debugging; in production the Node wrapper is
the entry point.
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from sklearn.cluster import KMeans


WINDOW = 1.5
HOP = 0.75


def parse_srt(path: str):
    content = Path(path).read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", content.strip())
    items = []
    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) < 3:
            continue
        try:
            idx = int(lines[0].strip())
        except ValueError:
            continue
        m = re.match(
            r"(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})",
            lines[1],
        )
        if not m:
            continue
        sh, sm, ss, sms = m.group(1, 2, 3, 4)
        s = int(sh) * 3600000 + int(sm) * 60000 + int(ss) * 1000 + int(sms)
        items.append({"i": idx, "s": s})
    return items


def run(vocals_path: str, srt_path: str) -> dict:
    wav = preprocess_wav(vocals_path)
    sr = 16000
    total = len(wav)

    enc = VoiceEncoder()
    win = int(WINDOW * sr)
    hop = int(HOP * sr)
    embeddings, times = [], []
    pos = 0
    while pos + win <= total:
        embeddings.append(enc.embed_utterance(wav[pos:pos + win]))
        times.append(pos / sr)
        pos += hop
    embs = np.array(embeddings)
    times = np.array(times)

    km = KMeans(n_clusters=2, random_state=0, n_init=10)
    labels = km.fit_predict(embs)

    # Pick the cluster that dominates the first 30s as "host" (L).
    early = labels[times < 30]
    counts = np.bincount(early)
    lenny_label = int(np.argmax(counts)) if len(counts) >= 2 else 0

    srt = parse_srt(srt_path)
    result = {}
    for it in srt:
        mid_s = (it["s"]) / 1000
        idx = int(mid_s / HOP)
        if idx >= len(labels):
            idx = len(labels) - 1
        label = int(labels[idx])
        result[str(it["i"])] = "L" if label == lenny_label else "C"
    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python3 _diarize_helper.py <vocals.wav> <srt_path>", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(run(sys.argv[1], sys.argv[2])))
