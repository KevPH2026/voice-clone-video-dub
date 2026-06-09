# Demucs Pitfalls

Demucs v4 (`htdemucs`) is the standard open source for vocal / music
separation. On a 10-min clip with `--segment 7` it takes ~5 min on
Apple Silicon CPU. Most of the time it just works. When it doesn't:

## Residual background music

Even after Demucs, the first 10-15 seconds of a podcast often have
music bleeding through (intro theme, sponsor jingle). Symptoms: the
cloned voice has a slight musical ring; the "AI music" sound is
mistaken for part of the speaker's tone.

Fix: pick a reference slice starting at `>= 15s` in the video. The
introduction music is usually over by then. For longer podcast
chapters that *have* a recurring background track, look for a moment
where the speaker is mid-thought but the music has dipped — usually
right after a long pause.

## Reference voice sounds muffled or tinny

The vocals track is missing some high-frequency content that Demucs
attributed to the "music" stem. Symptoms: the cloned voice lacks
breath sounds and sibilance.

Fix: switch from `htdemucs` to `htdemucs_ft` (fine-tuned variant, ~3x
slower but more conservative on what it routes to music). The first
release of the skill can stay on `htdemucs`; only switch if the user
flags the muffled output.

## Multiple speakers mixed in one segment

Demucs separates *all* vocals from *all* music. It does NOT separate
two speakers. If host and guest are talking at the same time, both
end up in `vocals.wav`. The reference will sound like a conversation,
and the clone will have ghost voice underneath.

Fix: pick a 30s slice where only one person is talking. Most
podcast/chat formats have a few seconds of single-speaker time within
the first 60s. If not, use a tool like `pyannote-audio` to
speaker-separate the vocals *before* picking a reference.

## Segment length and `--segment`

Default segment length is `7.85s` with `0.25s` shifts. For
podcast-style 10-min audio this is fine. For very long videos, longer
segments are faster but use more RAM. For very short audio (<30s),
Demucs may produce artifacts at the segment boundaries; use
`--segment 30` to force one segment for the whole clip.

## When NOT to run Demucs

- The video is mostly speech with no music (e.g. an indoor
  monologue). Just use the original audio as reference; the clone
  will be slightly cleaner because no separation artifacts.
- The video has multiple languages or very heavy reverb. Demucs
  sometimes confuses reverb with music and removes both.

In these cases, skip Demucs entirely and use `ffmpeg` to slice the
cleanest 30s of speech from the original audio.
