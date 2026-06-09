#!/bin/bash
# install-deps.sh — OPTIONAL convenience installer for the
# kev-youtube-video-clone-translate skill.
#
# This is NOT required to use the skill. If you already have a
# Python 3.11 venv with TTS + demucs + resemblyzer installed, skip
# this script and follow the manual steps in
# references/xtts-setup.md instead.
#
# What this script does:
#   1. Verifies the host has Python 3.11 and Homebrew (macOS)
#   2. Creates a venv at ./venv/ next to the skill directory
#   3. Installs torch (CPU), transformers 4.46, TTS, demucs,
#      resemblyzer, torchcodec
#   4. Applies the torch.load weights_only=False patch
#   5. Prints a reminder about HF_ENDPOINT
#
# Usage:
#   ./install-deps.sh
# or:
#   bash install-deps.sh
#
# Tested on: macOS 14 + Apple Silicon + Python 3.11 from Homebrew.
# Not tested on: Linux, Windows, Python 3.12+. If you hit issues,
# follow the manual steps in references/xtts-setup.md.

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  sed -n '2,/^$/p' "$0" | sed 's/^# //; s/^#$//'
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${VENV_PATH:-$SCRIPT_DIR/../venv}"
PY311="${PY311_BIN:-/opt/homebrew/bin/python3.11}"

echo "kev-youtube-video-clone-translate: install-deps"
echo "  venv:     $VENV"
echo "  python:   $PY311"
echo

# Pre-flight
if ! command -v "$PY311" >/dev/null 2>&1; then
  echo "ERROR: $PY311 not found."
  echo "  Install with: brew install python@3.11"
  echo "  Or set PY311_BIN=/path/to/python3.11"
  exit 1
fi

if ! command -v brew >/dev/null 2>&1 && [[ "$(uname -s)" == "Darwin" ]]; then
  echo "WARN: Homebrew not found. You will need to install ffmpeg-full manually."
fi

# 1. Create venv
if [[ ! -d "$VENV" ]]; then
  echo "[1/4] Creating venv..."
  "$PY311" -m venv "$VENV"
else
  echo "[1/4] Venv exists, reusing: $VENV"
fi

# 2. Upgrade pip
echo "[2/4] Upgrading pip..."
"$VENV/bin/pip" install --upgrade pip setuptools wheel >/dev/null

# 3. Install Python deps
echo "[3/4] Installing TTS, demucs, resemblyzer, torch, transformers..."
"$VENV/bin/pip" install \
  torch torchaudio --index-url https://download.pytorch.org/whl/cpu \
  >/dev/null 2>&1 || {
    echo "  WARN: PyTorch CPU install failed. If you're on Linux/Intel Mac,"
    echo "  try without --index-url or see https://pytorch.org/get-started/"
  }
"$VENV/bin/pip" install \
  "transformers==4.46.1" \
  "TTS" \
  "torchcodec" \
  "demucs" \
  "resemblyzer" \
  >/dev/null 2>&1 || {
    echo "ERROR: TTS install failed. See references/xtts-setup.md"
    exit 1
  }

# 4. Patch torch.load for TTS 0.22 + PyTorch 2.6+
echo "[4/4] Patching torch.load (TTS 0.22 + PyTorch 2.6+ compat)..."
TTS_IO="$VENV/lib/python3.11/site-packages/TTS/utils/io.py"
if [[ -f "$TTS_IO" ]]; then
  if grep -q "weights_only=False" "$TTS_IO"; then
    echo "  patch already applied, skipping"
  else
    cp "$TTS_IO" "$TTS_IO.bak"
    sed -i.bak 's|return torch.load(f, map_location=map_location, \*\*kwargs)|return torch.load(f, map_location=map_location, weights_only=False, **kwargs)|' "$TTS_IO"
    rm -f "$TTS_IO.bak"
    echo "  patched $TTS_IO (backup at $TTS_IO.bak)"
  fi
else
  echo "  WARN: $TTS_IO not found. Patch may be unnecessary on this TTS version."
fi

echo
echo "DONE. Reminders:"
echo "  - If HuggingFace is blocked from your network, set:"
echo "      export HF_ENDPOINT=https://hf-mirror.com"
echo "  - You will also need a logged-in claude CLI for the translation stage:"
echo "      claude auth login   # interactive, or sign in via Claude Code"
echo "  - You need ffmpeg with libass for the subtitle-burn step:"
echo "      brew install ffmpeg-full"
echo "  - Activate the venv before running the skill:"
echo "      source $VENV/bin/activate"
