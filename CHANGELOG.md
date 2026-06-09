# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/).
Versions follow [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-06-10

### Added
- Initial release of `voice-clone-video-dub` Mavis skill
- `scripts/clean-subs.js` — collapse YouTube incremental auto-captions
- `scripts/assemble-track.js` — stitch per-segment WAVs to timeline
- `scripts/batch_synth.py` — bulk XTTS v2 voice-clone synthesis
- `scripts/diarize.js` (+ `_diarize_helper.py`) — Resemblyzer speaker clustering
- `scripts/install-deps.sh` — optional one-shot dependency installer
- `references/xtts-setup.md` — PyTorch / TTS / transformers compatibility shims
- `references/demucs-pitfalls.md` — vocal separation failure modes
- `references/speaker-attribution.md` — 3-vote speaker reconciliation
- `before_15s.mp4` / `after_15s.mp4` — sample comparison clips
