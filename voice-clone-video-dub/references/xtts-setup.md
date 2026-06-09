# XTTS v2 Setup on Apple Silicon

Install notes that came out of the v1→v5 iterations. Skip them only
if the user's machine already has a working `TTS` library that
imports `xtts_v2` and loads a checkpoint.

## Python

Use Python 3.11. TTS 0.22 has not been published for 3.14; 3.12 and
3.13 also report dependency conflicts.

```bash
brew install python@3.11
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
```

## Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install "transformers==4.46.1"   # TTS 0.22 needs the old BeamSearchScorer
pip install TTS
pip install torchcodec                # torchaudio 2.11+ lazy-loads wavs
```

## TTS torch.load patch

PyTorch 2.6+ defaults `weights_only=True`. TTS 0.22's old XTTS
checkpoint contains a `XttsConfig` class that's not on the allow-list.
Patch the load function to force `weights_only=False`:

```bash
F=venv/lib/python3.11/site-packages/TTS/utils/io.py
sed -i.bak 's|return torch.load(f, map_location=map_location, \*\*kwargs)|return torch.load(f, map_location=map_location, weights_only=False, **kwargs)|' "$F"
```

The `.bak` keeps the original in case you ever need to revert.

## Loading the model

```python
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # if main HF is blocked
from TTS.api import TTS
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)
```

First load downloads ~1.9 GB. Subsequent loads use the cache.

## Synthesizing a single segment

```python
tts.tts_to_file(
    text="大家好，欢迎来到本期播客。",
    file_path="out.wav",
    speaker_wav="ref.wav",        # 5-30s clean reference
    language="zh-cn",
    temperature=0.5,              # 0.5 = stable, 0.65 = varied, 0.75 = wild
)
```

## Bulk synthesis (the right shape)

The single-call API loads the model every time. For 138 segments, that
would be 138 × 20s = 46 minutes wasted. Load once, loop:

```python
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)
for seg in segments:
    tts.tts_to_file(text=seg.text, file_path=f"segments/seg_{seg.i:03d}.wav",
                    speaker_wav=seg.ref, language="zh-cn", temperature=0.5)
```

Real-time factor on Apple Silicon CPU is ~0.9-1.0: synthesis time ≈
audio duration. A 600s video's worth of segments takes ~10-12 min.

## Cross-lingual quality ceiling

XTTS v2 is a 2-year-old model. The cloned voice will sound like the
reference speaker but with a noticeable "AI" prosody, especially on
Chinese. If the user needs higher quality, route to a paid API:

- ElevenLabs Professional Voice Clone (best)
- Fish Audio (Chinese-friendly)
- Aliyun CosyVoice cloud API (best Chinese specifically)

Do not promise the user that local XTTS will match their original
speakers' exact prosody. Promise "same tone, same general timbre, AI
prosody underneath."

## Common errors

| Error | Fix |
| --- | --- |
| `ImportError: cannot import name 'BeamSearchScorer'` | `pip install "transformers==4.46.1"` |
| `Weights only load failed ... XttsConfig` | Apply the torch.load patch above |
| `TorchCodec is required for load_with_torchcodec` | `pip install torchcodec` |
| Model never finishes loading (hangs at "Using model: xtts") | Set `HF_ENDPOINT=https://hf-mirror.com`; main HF is often blocked from CN |
| Garbled audio / random syllables | Lower `temperature` to 0.5; if still bad, the reference audio is contaminated — re-pick a cleaner slice of vocals |
