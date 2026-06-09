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

## [0.2.0] - 2026-06-10

### Changed
- **Renamed project** from `voice-clone-video-dub` to
  `kev-youtube-video-clone-translate`. The skill directory under
  the repo was renamed; the Mavis skill `name:` frontmatter was
  updated; the GitHub repository was renamed; all README files
  (en + 8 translations) were updated.
- The v0.1.0 release history above is preserved verbatim — the
  project was released as `voice-clone-video-dub` and renamed in
  v0.2.0. No breaking changes; this is purely a name change.

### Migration
- If you cloned the repo before this rename:
  ```bash
  git remote set-url origin https://github.com/KevPH2026/kev-youtube-video-clone-translate.git
  ```
- If you loaded the skill in Mavis before this rename, reload it
  (the new directory has `name: kev-youtube-video-clone-translate`
  in SKILL.md frontmatter, which is what Mavis matches on).
