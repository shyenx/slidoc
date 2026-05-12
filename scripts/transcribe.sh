#!/usr/bin/env bash
# Transcribe a single video to SRT with built-in quality gate.
# Usage:
#   transcribe.sh <video.mp4> <out_dir> <basename> [lang] [model]
# Examples:
#   transcribe.sh lecture.mp4 ./subtitles 1-speaker-topic zh medium
#   transcribe.sh lecture.mp4 ./subtitles 1-speaker-topic zh large-v3
set -euo pipefail

VIDEO="${1:?video path required}"
OUT="${2:?out dir required}"
BASE="${3:?basename required}"
LANG="${4:-zh}"
MODEL_NAME="${5:-medium}"   # medium | large-v3

MODEL="$HOME/.cache/whisper/ggml-${MODEL_NAME}.bin"
[[ -f "$MODEL" ]] || { echo "Model not found: $MODEL" >&2; exit 2; }
WHISPER_BIN="$(command -v whisper-cli || echo /opt/homebrew/bin/whisper-cli)"

mkdir -p "$OUT"
WAV="/tmp/lvtd_${BASE//\//_}_$$.wav"
SRT="$OUT/${BASE}.srt"

echo "[transcribe] $(basename "$VIDEO") -> $BASE.srt (model=$MODEL_NAME)"
ffmpeg -y -i "$VIDEO" -ar 16000 -ac 1 -c:a pcm_s16le "$WAV" 2>/dev/null

if [[ "$MODEL_NAME" == "large-v3" ]]; then
  # Anti-hallucination flags (lower thresholds → more aggressive fallback)
  "$WHISPER_BIN" -m "$MODEL" -l "$LANG" -osrt -of "$OUT/$BASE" \
    -et 2.0 -lpt -0.8 -mc 2.0 \
    "$WAV"
else
  "$WHISPER_BIN" -m "$MODEL" -l "$LANG" -osrt -of "$OUT/$BASE" "$WAV"
fi
rm -f "$WAV"

# Quality gate
total=$(grep -v -E '^[0-9]+$|^$|-->' "$SRT" | wc -l | tr -d ' ')
uniq=$(grep -v -E '^[0-9]+$|^$|-->' "$SRT" | sort -u | wc -l | tr -d ' ')
[[ $total -eq 0 ]] && { echo "[quality] EMPTY SRT" >&2; exit 3; }
pct=$((uniq * 100 / total))
echo "[quality] $BASE: $uniq/$total unique ($pct%)"

# Top repeated lines for inspection
top_count=$(grep -v -E '^[0-9]+$|^$|-->' "$SRT" | sort | uniq -c | sort -rn | head -1 | awk '{print $1}')
echo "[quality] top repeated line count: $top_count"

if [[ $pct -lt 80 && "$MODEL_NAME" != "large-v3" ]]; then
  echo "[quality] FAIL <80%, suggest re-running with large-v3:"
  echo "  $0 \"$VIDEO\" \"$OUT\" \"$BASE\" $LANG large-v3"
  exit 4
fi

if [[ $top_count -gt 100 ]]; then
  echo "[quality] WARN: one line repeated $top_count times — possible hallucination loop"
fi
