---
name: voice-clone-video-dub
description: |
  End-to-end pipeline for a foreign-language video: download clip, clean
  auto-captions, translate to Chinese (or any target), optionally voice-clone
  the speakers and dub the new audio, burn subtitles, output a finished MP4.
  Use this skill when the user gives a YouTube (or local video) link and asks
  to "翻译", "加字幕", "配音", "克隆声音", "中文配音" — or any combination of
  those actions on a 1–30 min video. Do NOT use for: video editing (cuts,
  filters), AI-generated video (use seedance-video-creator), audio-only
  transcription, or one-off subtitle file generation.
---

# Voice-Clone Video Dub

## Inputs to collect

- Video source: YouTube URL or local file path
- Time range to clip: e.g. `t=399s` to `t=999s`. Default: full video
  clipped to first 10 min from the given start.
- Target language for translation & dub: default Chinese (zh-cn).
- Whether to clone voices: default YES. If user only wants hardcoded
  subs + translated SRT, skip the Demucs + XTTS stages.
- If the user wants the clones of *specific* people (named), confirm
  those people actually speak in the clip before committing to a 15-min
  Demucs + per-speaker XTTS pass.

## Pipeline (one phase at a time, fail loud at each boundary)

### 1. Acquire video + raw auto-captions

```
yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" \
  --merge-output-format mp4 --download-sections "*START-END" \
  -o src.mp4 "<URL>"
yt-dlp --list-subs "<URL>"        # confirm a manual or auto track exists
yt-dlp --write-auto-subs --sub-langs en-orig --convert-subs srt \
  -o src.en-orig.srt "<URL>"     # grab the original (non-translated) track
```

If the user wants a different source language, change `en-orig` to the
appropriate code. If only auto-translated subs exist (no `*-orig`), they
will be ~10% worse quality — flag this to the user and let them choose.

### 2. Clean the YouTube incremental captions

YouTube auto-subs are emitted as ~10ms "stable" snapshots interleaved
with ~2s "growing" snapshots. The stable text is what a viewer actually
sees. Run `scripts/clean-subs.js` to collapse them to one segment per
spoken line and rebase timestamps to 0.

```
node "$SKILL_DIR/scripts/clean-subs.js" \
  src.en-orig.srt en.srt
```

If the user wants subtitles *only* (no dub), you can skip the
translation-clip-window decision and process the whole video. With dub,
clip the SRT to the same time window you clipped the video.

### 3. Translate to target language in parallel

- Split en.srt into chunks of ~20 segments each
- For each chunk, run `claude -p --model sonnet --tools ""` with a
  translation prompt that returns `[{i, zh}, ...]` JSON only
- Concatenate into zh.srt
- Strip the `>>` speaker-change markers (they were preserved during
  translation as cues but should not appear in the final subs)

If the translation returns fenced JSON, strip the fence. If any segment
is missing, retry just that segment before proceeding.

### 4. Decide speakers (3-way vote, ~30s)

This stage decides which reference voice to use for each dubbed segment.

1. **Text vote** — let Claude label each segment `L` or `C` from the
   Chinese text (question vs statement, introduction patterns). Use the
   `>>` markers and known podcast conventions as primary cues.
2. **Voice vote** — run `scripts/diarize.js` on the Demucs-isolated
   vocals. It clusters `resemblyzer` embeddings into 2 speakers and
   picks the one that dominates the first 30s as "L" (host). The Node
   wrapper shells out to `python3` by default; if resemblyzer is
   only in a venv, set `PYTHON_BIN` to point at the venv's python:
   ```bash
   PYTHON_BIN="$VENV/bin/python" node scripts/diarize.js \
     separated/htdemucs/full/vocals.wav zh.srt spk_map.json
   ```
   Without `PYTHON_BIN`, it uses system python3 and will fail with
   `ModuleNotFoundError: No module named 'resemblyzer'`.
3. **Manual reconciliation** — for any segment where the two votes
   disagree, use the textual cue. If still unclear, default to the
   dominant speaker for that 30s window.

The user can override the host/guest mapping if they say "Cat Wu" is
the host or similar. Always ask before assuming.

### 5. (Optional) Demucs + XTTS voice clone

**Why both?** Demucs removes the background music that contaminates the
reference voice; XTTS v2 is the only open model that does cross-lingual
voice cloning (e.g. English speaker → Chinese speech) well enough on CPU.

```
# 5a. Extract clean 10-min audio
ffmpeg -i src.mp4 -vn -ac 2 -ar 44100 -acodec pcm_s16le full.wav

# 5b. Separate vocals
demucs -n htdemucs --two-stems vocals -d cpu --segment 7 \
  -o separated full.wav

# 5c. Pick 30s of clean reference for each speaker from the
#     separated vocals (avoid 0-15s where BGM bleeds in even
#     after Demucs)
ffmpeg -ss 20 -i separated/htdemucs/full/vocals.wav -t 30 \
  -ac 1 -ar 16000 ref_lenny.wav    # host
ffmpeg -ss 90 -i separated/htdemucs/full/vocals.wav -t 30 \
  -ac 1 -ar 16000 ref_cat.wav      # guest

# 5d. Bulk synthesize per-segment (loads XTTS once, loops fast)
"$VENV/bin/python" "$SKILL_DIR/scripts/batch_synth.py" \
  zh.srt segments/ ref_lenny.wav ref_cat.wav 0.5
# Reads spk_map.json from next to zh.srt for per-segment speaker
# selection. Produces segments/seg_NNN.wav and segments/manifest.jsonl.

# 5e. Assemble final dub track to 10 min timeline
node "$SKILL_DIR/scripts/assemble-track.js" \
  segments/manifest.jsonl dub.wav 600
```

If the user explicitly said "use ElevenLabs / Fish Audio" instead, do
not run this stage. Wait for the API key and use the appropriate SDK.

### 6. Burn subtitles + render

```
# 6a. Build styled ASS from zh.srt (PingFang SC + dark backdrop)
#     See scripts/srt2ass.py pattern — output zh.ass

# 6b. Final mux
ffmpeg-full -i src.mp4 -i dub.wav \
  -map 0:v -map 1:a -vf "ass=zh.ass" \
  -c:v libx264 -crf 22 -preset medium \
  -c:a aac -b:a 192k -movflags +faststart \
  output_zh_dub.mp4
```

`ffmpeg-full` (not the homebrew default) is required for `ass=` and
`libass`. If only the default ffmpeg is available, skip the hardcoded
subtitle and emit a soft-subtitle MP4 + separate SRT.

## Output contract

For every run, deliver:

- `output_zh_dub.mp4` — finished video (default 10 min, ~90 MB)
- `zh.srt` — translated subtitle file
- `zh.ass` — styled ASS (if hardcoded subs were used)
- `dub_track.wav` — standalone dubbed audio
- A short note: speaker attribution accuracy estimate, total synth
  time, and any known-quality caveats (e.g. one model's name was
  misheard as "Mythos" by ASR)

If the user only asked for subtitles, drop the `dub_track.wav` and the
voice-clone caveat. If they asked only for dub, drop the SRT/ASS.

## Failure handling

- **No manual / orig track in the user's language** → fall back to
  `en` (English auto) and warn. Translation quality drops slightly
  but pipeline still completes.
- **ASR error in names / terms** (e.g. "Mythos" instead of "Opus") →
  keep the ASR spelling in zh.srt; add a caveat in the final note.
  The user can `sed` it.
- **XTTS hallucinates extra syllables at temp 0.65** → drop to 0.5.
  Tradeoff: ~2x slower synthesis, more stable prosody.
- **Cross-lingual clone still sounds "foreign-accent"** → that's the
  ceiling of XTTS v2. Options to improve: a paid cloud API
  (ElevenLabs Professional Voice Clone, Fish Audio, Aliyun CosyVoice).
  Don't promise better than that.
- **Demucs leaks residual music** → pick a later, quieter slice of
  vocals for the reference (e.g. 90-120s instead of 20-50s).
- **Speaker label flipped for one segment** → acceptable. The user
  is listening to voice tone, not labeling data. Fix only if >10% of
  segments are wrong.

## Setup (one-time per machine)

This skill has two non-trivial dependencies: a Python 3.11 venv
for TTS/Demucs/Resemblyzer, and a logged-in `claude` CLI for the
translation stage. The user can either run the convenience
installer (recommended) or follow the manual steps.

### Quick path (recommended)

```bash
bash scripts/install-deps.sh
```

This creates a venv at `../venv/` (next to the skill), installs
TTS + demucs + resemblyzer, applies the torch.load patch, and
prints what to do next. The script is idempotent — running it
twice is harmless.

After the installer finishes, you still need:

```bash
brew install ffmpeg-full yt-dlp         # ffmpeg with libass for subtitle burn
claude auth login                       # for the translation step
export HF_ENDPOINT=https://hf-mirror.com  # only if HuggingFace is blocked
```

### Manual path (if the installer doesn't fit your environment)

Read `references/xtts-setup.md` and follow the steps there. Same
end state, but you copy each command yourself.

### Hard requirements

| Requirement | Why |
| --- | --- |
| Python 3.11 | TTS 0.22 not on 3.12-3.14 yet |
| macOS / Linux | Windows would need every ffmpeg path in scripts rewritten |
| ~5 GB free disk | XTTS 1.9 GB + Demucs 80 MB + Resemblyzer 100 MB + scratch WAVs |
| 8 GB RAM minimum | Demucs + XTTS concurrently can OOM at 4 GB |
| Logged-in `claude` CLI | Translation stage calls `claude -p` with the user's OAuth |
| `ffmpeg-full` | Default `ffmpeg` on Homebrew has no `ass=` filter — sub burn fails silently |
| Network access to HuggingFace (or mirror) | First XTTS load downloads 1.9 GB checkpoint |

### Soft requirements (the pipeline degrades without them)

- **Demucs** — if you don't install it, the voice clone will
  have residual background music. The dub is still usable, just
  less clean. Skip stage 5b and use the original audio as
  reference instead.
- **Resemblyzer** — if you don't install it, fall back to text-only
  speaker attribution (single vote instead of 3-way reconciliation).
  Expect ~5% of segments to have the wrong speaker.

### Translation API alternative

The SKILL.md pipeline uses `claude -p` (Claude Code CLI) for
translation. If the user doesn't have Claude Code, two fallbacks:

- **OpenAI** — replace `claude -p --model sonnet --tools ""` with
  an `openai` CLI call. The prompts in step 3 still work.
- **Local model** — `ollama run qwen2.5:7b` is good enough for
  zh subtitle translation. Slower and lower quality but no API
  cost.

## Examples

**Input**: "https://www.youtube.com/watch?v=ABC — translate this 10 min
clip to Chinese, hardcode subtitles"

**Pipeline**: stages 1, 2, 3, 6 (skip 4, 5). Output: `clip_zh.mp4` +
`zh.srt` + `zh.ass`. No voice clone, faster (~5 min wall time).

**Input**: "Same link, but I want Lenny and Cat Wu's actual voices
saying the Chinese"

**Pipeline**: all stages. Wall time ~30-40 min (Demucs alone is 5 min,
XTTS 138 segments is ~12 min, render is ~2 min). Output includes
`dub_track.wav` so the user can re-mux against a different cut.

## References

- `references/xtts-setup.md` — full PyTorch / TTS / transformers
  compatibility shims, demoted in from the conversation's debugging
  history
- `references/demucs-pitfalls.md` — what to do when Demucs leaks BGM
  or produces a hollow-sounding vocal
- `references/speaker-attribution.md` — the 3-vote reconciliation rule
  and when to fall back to text-only labelling
