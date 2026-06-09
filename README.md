# voice-clone-video-dub

A Mavis skill that turns a foreign-language video into a Chinese
voice-cloned dub with burned-in subtitles. End-to-end pipeline:

```
YouTube URL
   ↓
[1] yt-dlp → 1080p clip + en-orig SRT
   ↓
[2] clean-subs.js → clean per-line SRT
   ↓
[3] claude -p (parallel chunks) → zh.srt
   ↓
[4] 3-vote speaker attribution (text + resemblyzer)
   ↓
[5] Demucs + XTTS v2 voice clone (optional)
   ↓
[6] srt2ass + ffmpeg ass= → final MP4
```

## What's in the box

- `voice-clone-video-dub/` — the Mavis skill (SKILL.md + 5 scripts + 3 references)
- `before_15s.mp4` — original English audio at 30-45s of the source clip
- `after_15s.mp4` — same 15s, with Lenny & Cat Wu's voices cloned to Chinese
- `requirements.txt` — pinned Python deps (informational; see install script)
- `CHANGELOG.md` — release notes
- `LICENSE` — MIT

## Before / after

| | Original (English) | After (cloned Chinese dub) |
|---|---|---|
| Voice | Lenny / Cat Wu's actual English | XTTS-cloned, same timbre, speaking Chinese |
| Subtitles | — | Burned-in Chinese (zh.srt → zh.ass) |
| Background | Original podcast audio | Cleaned via Demucs vocals separation |
| Frame timing | Matches original | Matches (atempo per-segment) |

The two 15s clips in the repo root demonstrate this side by side.

## Try it

Inside Mavis (any LLM with the skill loaded), give it a YouTube link:

> "https://www.youtube.com/watch?v=... — translate this 10 min clip to
> Chinese, hardcode subs, and clone the speakers' voices"

The skill will:
1. Download and clip the video
2. Translate subtitles in parallel
3. Decide who's speaking per segment
4. (Optional) Clone the voices via XTTS v2
5. Burn subtitles and render the final MP4

## Install (one-time per machine)

```bash
bash voice-clone-video-dub/scripts/install-deps.sh
brew install ffmpeg-full yt-dlp
claude auth login
export HF_ENDPOINT=https://hf-mirror.com  # only if HuggingFace is blocked
```

Or follow the manual steps in `voice-clone-video-dub/references/xtts-setup.md`.

## Repository layout

```
.
├── .gitignore
├── .gitattributes                # normalize line endings (CRLF-safe)
├── LICENSE                       # MIT
├── CHANGELOG.md                  # release notes
├── README.md                     # this file
├── requirements.txt              # pinned Python deps
├── before_15s.mp4                # original English (15s)
├── after_15s.mp4                 # cloned Chinese (15s)
└── voice-clone-video-dub/        # the Mavis skill
    ├── SKILL.md                  # 263-line procedure + setup
    ├── scripts/                  # 5 deterministic scripts
    │   ├── clean-subs.js
    │   ├── assemble-track.js
    │   ├── batch_synth.py
    │   ├── diarize.js
    │   ├── _diarize_helper.py
    │   └── install-deps.sh
    └── references/               # deep dives
        ├── xtts-setup.md
        ├── demucs-pitfalls.md
        └── speaker-attribution.md
```

## How it was built

The v1-v5 iterations that produced this skill are documented in
`voice-clone-video-dub/SKILL.md` — that file is the condensed,
installable version of the workflow we used end-to-end on
Lenny's Podcast with Cat Wu (Anthropic) as the guest.

## License

MIT — see `LICENSE`.

Sample videos (`before_15s.mp4`, `after_15s.mp4`) are 15s clips from
Lenny's Podcast used for pipeline demonstration; the full episode
is not redistributed.
