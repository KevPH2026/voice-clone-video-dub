# Speaker Attribution

The hardest part of voice-clone dubbing isn't the synthesis — it's
knowing **who is supposed to be talking in each translated segment**.
If you get this wrong, the clone sounds like the wrong person at the
wrong moment, and the listener's "this is fake" alarm goes off.

This skill uses a 3-vote reconciliation rule. Two of the votes are
automated; the third is a small text-based check.

## Vote 1: text-based labeling (Claude)

Pass the translated SRT to Claude with a prompt that names the two
speakers and asks for `L` / `C` per segment. Useful cues:

- "今天我的嘉宾是..." = host, "欢迎" = host
- Sentences ending in `?` or starting with "怎么 / 什么 / 为什么 /
  能不能" = host question, ~80% accuracy
- Sentences starting with "我觉得 / 我们 / 我之前" = guest answer,
  ~80% accuracy
- A `>>` marker at the start of a segment = a speaker change; the
  text after the `>>` is the new speaker

Claude will get ~95% right. The remaining 5% are short interjections
("嗯", "对", "是这样") that get attributed to the wrong person
because there's not enough context.

## Vote 2: voice-based clustering (resemblyzer)

Run `scripts/diarize.js` on the Demucs-isolated vocals. It slides a
1.5s window with 0.75s hop, computes a 256-dim speaker embedding per
window, and clusters the embeddings into 2 groups. The cluster that
dominates the first 30s is mapped to the host.

This catches mistakes Claude made on long monologues. It also gets
~5% wrong, mostly short utterances from the softer voice (usually
the female guest) that get classified as the louder host.

## Vote 3: text-only reconciliation (manual or LLM)

For segments where votes 1 and 2 disagree, fall back to text cues:
- If segment ends in `?` and is short → host
- If segment contains first-person plural "我们" → guest
- If neither, take the vote that matches the surrounding context

In practice, segments 31, 43, 44, 51-53, 57, 66, 68, 69, 79, 93, 100
are common disagreement points because they're either very short
interjections or sentence continuations.

## When the text-based vote is clearly better

Resemblyzer (and most voice-based diarizers) misclassifies soft
female speech. If your text-based vote says "C, C, C" for 30 seconds
in a row, and the voice vote says "L" for all of them, the voice
vote is wrong — the male host is just being silent.

Trust text over voice when the votes disagree on 5+ consecutive
segments in the same direction.

## When there are 3+ speakers

The pipeline as written assumes 2 speakers (host + guest). For
panels or interviews with 3+ distinct voices, you would need:

1. Increase the KMeans `n_clusters` to 3+
2. Re-pick reference audio for each new cluster (after the first
   two are correctly labelled)
3. Re-run synthesis with one of three reference voices per segment

This is not currently automated by the skill. If the user has a
3+ speaker video, mention the limitation and ask if they want to
proceed manually.

## Why not just trust the timestamps?

The translated SRT has timestamps from the original. You might think
"the same person is talking for the whole continuous run" — but
podcast-style conversations interleave Q&A tightly enough that a
30-second "Cat Wu" run often contains a 0.5s "right" from Lenny.
You cannot just bucket by run.
