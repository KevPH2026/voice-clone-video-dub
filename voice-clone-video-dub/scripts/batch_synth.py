#!/usr/bin/env python3
"""batch_synth.py — bulk XTTS v2 voice-clone synthesis per segment.

Loads XTTS once, loops over a manifest-style SRT, writes one WAV per
segment, and emits a manifest.jsonl that assemble-track.js consumes.

Manifest format (per SRT segment):
  {i, spk, text, s, e}
  - spk: "L" (host) or "C" (guest)
  - s, e: millisecond timestamps in the SRT

This script is the deterministic part of the SKILL.md step 5d.
The LLM that runs the skill decides *which* reference wav each
segment uses (L vs C); this script just applies that decision
consistently and never re-loads the model.

Usage:
  python3 batch_synth.py <srt> <out_dir> <ref_l> <ref_c> [temp]

Example:
  python3 batch_synth.py zh.srt segments/ ref_lenny.wav ref_cat.wav 0.5

Outputs:
  segments/seg_NNN.wav   (one per SRT segment)
  manifest.jsonl          (one record per segment with path + duration)

Requires the TTS package to be installed and the torch.load patch
from references/xtts-setup.md applied. Set HF_ENDPOINT env var to a
mirror if HuggingFace is blocked.
"""

import json
import os
import re
import sys
import time
from pathlib import Path


def parse_srt(path: Path):
    content = path.read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", content.strip())
    items = []
    for b in blocks:
        lines = [l for l in b.strip().split("\n") if l.strip()]
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
        sh, sm, ss, sms, eh, em, es, ems = m.groups()
        s = int(sh) * 3600000 + int(sm) * 60000 + int(ss) * 1000 + int(sms)
        e = int(eh) * 3600000 + int(em) * 60000 + int(es) * 1000 + int(ems)
        text = " ".join(lines[2:]).strip()
        # strip speaker-change markers if any survived cleaning
        text = re.sub(r">>\s*", "", text).strip()
        if text:
            items.append({"i": idx, "s": s, "e": e, "text": text})
    return items


def wav_duration_ms(path: Path) -> int:
    """Estimate duration from WAV size: 24kHz mono 16-bit = 48000 bytes/sec."""
    size = path.stat().st_size
    if size <= 44:
        return 0
    return int((size - 44) / 48000 * 1000)


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        sys.exit(1)

    srt_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    ref_l = sys.argv[3]
    ref_c = sys.argv[4]
    temperature = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.jsonl"

    # Resume support: if manifest exists, skip already-done segments.
    done = set()
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("ok") and rec.get("path"):
                    done.add(rec["i"])
            except json.JSONDecodeError:
                pass

    items = parse_srt(srt_path)
    print(f"parsed {len(items)} segments; {len(done)} already done", flush=True)

    print("loading XTTS v2 (one-time)...", flush=True)
    t0 = time.time()
    from TTS.api import TTS  # imported lazily so the script's --help is fast
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
    print(f"loaded in {time.time() - t0:.1f}s", flush=True)

    with manifest_path.open("a", encoding="utf-8") as f:
        total_t0 = time.time()
        for it in items:
            if it["i"] in done:
                continue
            # Spk: try to read a spk_map.json next to the SRT (the SKILL.md
            # text-attribution stage writes it). If absent, default to "C"
            # which is the dominant speaker in the canonical podcast example.
            spk = "C"
            spk_map = srt_path.with_name("spk_map.json")
            if spk_map.exists():
                try:
                    m = json.loads(spk_map.read_text(encoding="utf-8"))
                    spk = m.get(str(it["i"]), spk)
                except Exception:
                    pass
            ref = ref_l if spk == "L" else ref_c
            out_path = out_dir / f"seg_{it['i']:03d}.wav"
            ts = time.time()
            try:
                tts.tts_to_file(
                    text=it["text"],
                    file_path=str(out_path),
                    speaker_wav=ref,
                    language="zh-cn",
                    temperature=temperature,
                )
                dur = wav_duration_ms(out_path)
                rec = {
                    "i": it["i"],
                    "spk": spk,
                    "text": it["text"],
                    "s": it["s"],
                    "e": it["e"],
                    "path": str(out_path),
                    "duration_ms": dur,
                    "ok": True,
                    "synth_time_s": round(time.time() - ts, 2),
                }
                print(
                    f"  seg {it['i']:3d} [{spk}] {rec['synth_time_s']:5.1f}s "
                    f"-> {dur/1000:5.2f}s audio: {it['text'][:50]}",
                    flush=True,
                )
            except Exception as ex:
                rec = {
                    "i": it["i"],
                    "spk": spk,
                    "text": it["text"],
                    "s": it["s"],
                    "e": it["e"],
                    "path": None,
                    "ok": False,
                    "error": str(ex),
                }
                print(f"  seg {it['i']:3d} [{spk}] FAILED: {ex}", flush=True)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()

    print(
        f"\ndone: {len(items)} segs, total {time.time() - total_t0:.1f}s, "
        f"manifest at {manifest_path}",
        flush=True,
    )


if __name__ == "__main__":
    main()
