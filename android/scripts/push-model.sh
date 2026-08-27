#!/usr/bin/env bash
#
# Side-loads the on-device LLM onto the phone.
#
# The model is NOT in this repo and NOT in the APK — it is ~0.5-1.3 GB and
# licence-gated. Run this once per device (it survives app reinstalls, so you do
# not repeat it on every build).
#
#   ./scripts/push-model.sh ~/Downloads/gemma3-1b-it-int4.task
#
# Getting the file (do this on the laptop during Green Light, or before the
# event — it is a slow download):
#   1. Accept the Gemma licence at https://huggingface.co/litert-community/Gemma3-1B-IT
#   2. Download a .task build, e.g.
#      Gemma3-1B-IT_multi-prefill-seq_q4_ekv2048.task  (~555 MB)
#   3. Run this script against it.
#
# Any MediaPipe-compatible .task bundle works — Gemma 3 1B is simply the best
# quality-per-megabyte at the time of writing. Phi-3-mini also runs but is ~2 GB
# and noticeably slower to first token on a phone.

set -euo pipefail

MODEL_SRC="${1:-}"
DEST_DIR="/data/local/tmp/propiq"
DEST="$DEST_DIR/model.task"

if [[ -z "$MODEL_SRC" ]]; then
  echo "usage: $0 <path-to-model.task>" >&2
  exit 1
fi

if [[ ! -f "$MODEL_SRC" ]]; then
  echo "error: no such file: $MODEL_SRC" >&2
  exit 1
fi

if ! command -v adb >/dev/null 2>&1; then
  echo "error: adb not on PATH. Install platform-tools." >&2
  exit 1
fi

if [[ -z "$(adb devices | sed -n '2p')" ]]; then
  echo "error: no device connected. Check USB debugging is on." >&2
  exit 1
fi

SIZE_MB=$(( $(wc -c < "$MODEL_SRC") / 1048576 ))
echo "Pushing $(basename "$MODEL_SRC") (${SIZE_MB} MB) → $DEST"
echo "This takes a few minutes over USB 2.0. Do not unplug."

adb shell "mkdir -p $DEST_DIR"
adb push "$MODEL_SRC" "$DEST"

# World-readable: the app runs as its own uid and cannot read another app's
# files, but /data/local/tmp is reachable when the mode bits allow it.
adb shell "chmod 644 $DEST" || true

echo
echo "Verifying…"
adb shell "ls -l $DEST"

echo
echo "Done. Launch PropIQ Field → Start field assessment."
echo "The voice card shows 'LLM ON-DEVICE' once the model has loaded."
echo
echo "If it does not appear, check logcat:"
echo "  adb logcat -s LocalLlm:*"
