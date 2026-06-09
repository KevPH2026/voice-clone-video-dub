#!/bin/bash
# start.sh — kick off the voice-clone-video-dub pipeline.
#
# This is a thin wrapper. The actual orchestration lives in
# voice-clone-video-dub/SKILL.md and is intended to be driven by
# an LLM in Mavis. This script exists for two cases:
#
#   1. Quick smoke test: ./start.sh https://youtu.be/...
#      (runs the pipeline with all defaults)
#   2. CI: ./start.sh --dry-run <url>
#      (prints the steps without running them)
#
# Requirements (after install-deps.sh):
#   - venv at ../venv (or set VENV_BIN)
#   - ffmpeg-full in PATH
#   - claude CLI logged in
#   - HF_ENDPOINT set (if behind GFW)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/voice-clone-video-dub"
VENV_BIN="${VENV_BIN:-$SCRIPT_DIR/venv/bin/python}"
DRY_RUN=0

usage() {
  sed -n '2,/^$/p' "$0" | sed 's/^# //; s/^#$//'
  echo "Usage: $0 [--dry-run] <youtube-url> [start_sec] [end_sec]"
  echo "Example: $0 https://www.youtube.com/watch?v=PplmzlgE0kg 399 999"
  exit 0
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
fi

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

URL="${1:-}"
START="${2:-399}"
END="${3:-999}"

if [[ -z "$URL" ]]; then
  usage
fi

# Pre-flight
if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "ERROR: yt-dlp not installed. Run: brew install yt-dlp"
  exit 1
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERROR: ffmpeg not installed. Run: brew install ffmpeg-full"
  exit 1
fi
if [[ ! -x "$VENV_BIN" && ! -f "$VENV_BIN" ]]; then
  echo "WARN: venv python not found at $VENV_BIN."
  echo "      Run bash voice-clone-video-dub/scripts/install-deps.sh to create it."
  echo "      Or set VENV_BIN=/path/to/python to point at an existing venv."
  if [[ $DRY_RUN -eq 0 ]]; then
    exit 1
  fi
fi
if ! command -v claude >/dev/null 2>&1; then
  echo "ERROR: claude CLI not installed. Run: npm install -g @anthropic-ai/claude-code"
  exit 1
fi

OUT_DIR="${OUT_DIR:-$SCRIPT_DIR/runs/$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$OUT_DIR"

step() {
  echo
  echo "=== $1 ==="
}

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    "$@"
  fi
}

step "1. Acquire video + raw captions"
run yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" \
  --merge-output-format mp4 --download-sections "*${START}-${END}" \
  -o "$OUT_DIR/src.mp4" "$URL"
run yt-dlp --write-auto-subs --sub-langs en-orig --convert-subs srt \
  -o "$OUT_DIR/src.en-orig.srt" "$URL"

step "2. Clean captions"
run node "$SKILL_DIR/scripts/clean-subs.js" \
  "$OUT_DIR/src.en-orig.srt" "$OUT_DIR/en.srt" "$START" "$END"

step "3. Translate (do this in Mavis; this step requires the LLM)"
echo "  Open Mavis and ask: 'translate $OUT_DIR/en.srt to Chinese, save to $OUT_DIR/zh.srt'"
echo "  Or use the in-pipeline Claude Code call: claude -p --model sonnet --tools \"\" < prompt"

step "4-5. Decide speakers + voice clone (do this in Mavis)"
echo "  After step 3, in Mavis say: 'voice-clone the speakers in $OUT_DIR/zh.srt using the Demucs-isolated vocals'"
echo "  This produces $OUT_DIR/segments/ and $OUT_DIR/segments/manifest.jsonl"

step "6. Render"
echo "  After steps 3-5, in Mavis say: 'assemble the dub and burn subtitles to $OUT_DIR/output.mp4'"

step "Done. Output in $OUT_DIR/"
ls -la "$OUT_DIR" || true
