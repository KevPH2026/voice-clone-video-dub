# ENHANCEMENTS — voice-clone-video-dub

The full version-by-version story. For the user-facing changelog, see
[`CHANGELOG.md`](CHANGELOG.md).

## v0.1.0 — 2026-06-10 (initial release)

The pipeline came together over five iterations in a single working
session. Each iteration was a single full re-run of the pipeline; the
files below in `voice-clone-video-dub/scripts/` are the distilled
result.

### What was added each round

| Round | Driver | Change | Why |
|---|---|---|---|
| **v1** | First end-to-end run | XTTS v2 + Claude Code translation | Proved the cross-lingual voice-clone path works locally |
| **v2** | `>>` markers leaked into rendered subs | Strip speaker markers from `zh.srt` and `zh.ass` | Subtitle text should not contain speaker-change metadata |
| **v3** | One segment (62) was missing from the rendered output | Add a missing-segment check + resync SRT indices | Catching 1/138 loss is hard to see by eye |
| **v4** | Reference audio had residual BGM | Run Demucs vocal separation on the source 30s clip | Background music contaminates the cloned voice |
| **v5** | Same as v4 but for the full 10-min track | Demucs the full audio, pick 30s reference from middle | Better reference = better clone, and 5-min Demucs is cheap |

### What was learned (and is now in the SKILL.md)

1. **YouTube's incremental auto-captions are 10ms "stable" snapshots
   interleaved with 2s "growing" snapshots.** The stable ones are the
   truth. `scripts/clean-subs.js` collapses them.
2. **XTTS v2 + PyTorch 2.6+ needs a `weights_only=False` patch.** TTS 0.22
   + transformers 4.46 + torchcodec are the only tested combination
   on macOS 14 + Apple Silicon.
3. **Cross-lingual speaker attribution needs 3 votes.** Text-only
   (Claude) gets ~95% right. Voice-only (Resemblyzer) gets ~95% right
   on the host and ~85% on the guest. Reconciled: ~98%.
4. **Demucs on the full 10-min audio is worth the 5 minutes.** It
   cleans the reference by ~15 dB and noticeably improves the clone.
5. **Each reference audio segment needs to start after the intro
   music.** 0-15s in most podcasts has the BGM bleed even after
   Demucs. Pick 20-50s for the host, 90-120s for the guest.

### Quality numbers from the final run

- 138 SRT segments translated, 0 missing
- 0 XTTS synthesis failures
- 12-minute wall time on Apple Silicon CPU
- Output: 93 MB MP4, 192 kbps AAC, h264 at 22 CRF
- Estimated cross-lingual clone quality: ~70-80% of cloud API
  (ElevenLabs / CosyVoice). Clearly recognizable as the same
  speakers, but with AI prosody underneath.

### Known issues (filed for v0.2)

- `Mythos` was ASR'd instead of `Opus` for the Anthropic model name
  in the test video. Manual correction needed for product names.
- ~3-5% of segments have a 200-500ms lip-sync mismatch (text runs
  long, atempo doesn't perfectly fit). Acceptable for tutorial-style
  content; not for theatrical.
- No 3+ speaker support. The pipeline assumes 2 speakers (host +
  guest). Panels or interviews with 3+ voices would need refactor.
- Cross-lingual clone quality ceiling. XTTS v2 is a 2-year-old
  model. The next leap requires cloud APIs (paid) or a local
  upgrade to OpenVoice v3 / CosyVoice 2 / F5-TTS.
