#!/usr/bin/env bash
# Install local Kokoro-82M TTS for DevAscent narration (CPU-only friendly).
# ~327MB model, Apache-2.0. Runs fine on 16GB RAM / modern i7 without a GPU.
#
# After this, restart the server; POST /api/tts returns natural WAV audio and
# the UI's "premium voice" toggle works. Without it, narration uses the
# browser's built-in voice automatically.
set -euo pipefail

VENV="${1:-.venv}"
PY="$VENV/bin/python"

if [ ! -x "$PY" ]; then
  echo "No venv python at $PY — pass your venv path: scripts/setup_tts.sh /path/to/.venv"
  exit 1
fi

echo "Installing Kokoro TTS + deps into $VENV (CPU build of torch)…"
"$PY" -m pip install --upgrade pip
# CPU-only torch keeps the footprint small and avoids CUDA on a laptop.
"$PY" -m pip install torch --index-url https://download.pytorch.org/whl/cpu
"$PY" -m pip install kokoro soundfile numpy
# espeak-ng is Kokoro's phonemizer backend.
if command -v apt-get >/dev/null 2>&1; then
  echo "Installing espeak-ng (needs sudo)…"
  sudo apt-get update -qq && sudo apt-get install -y espeak-ng
else
  echo "Install 'espeak-ng' with your package manager if phonemization fails."
fi

echo "Verifying…"
"$PY" - <<'PYEOF'
try:
    from kokoro import KPipeline
    p = KPipeline(lang_code="a")
    n = sum(1 for _ in p("DevAscent local voice is ready.", voice="af_heart"))
    print(f"OK — Kokoro produced {n} audio chunk(s).")
except Exception as e:
    print("Kokoro not ready:", e)
    raise SystemExit(1)
PYEOF

echo "Done. Restart the server — /api/tts is now live."
