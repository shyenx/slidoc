#!/usr/bin/env bash
# Extract keyframes from a single video.
# Usage:
#   extract_keyframes.sh <video.mp4> <out_dir> [scene|fps] [threshold|interval_sec]
# Examples:
#   extract_keyframes.sh lecture.mp4 ./vdir scene 0.30
#   extract_keyframes.sh zoom_rec.mp4 ./vdir fps 90
set -euo pipefail

VIDEO="${1:?video path required}"
VDIR="${2:?out dir required}"
MODE="${3:-scene}"     # scene | fps
PARAM="${4:-}"          # scene threshold OR fps interval seconds

mkdir -p "$VDIR/frames"
rm -f "$VDIR/frames"/*.jpg "$VDIR/frame_log.txt"

case "$MODE" in
  scene)
    THR="${PARAM:-0.30}"
    echo "[extract] scene-detect threshold=$THR"
    ffmpeg -y -i "$VIDEO" \
      -vf "select='gt(scene,$THR)',showinfo,scale=1280:-1" \
      -vsync vfr -q:v 3 "$VDIR/frames/f_%04d.jpg" \
      2> "$VDIR/frame_log.txt"
    ;;
  fps)
    INTERVAL="${PARAM:-90}"
    echo "[extract] fixed-interval=${INTERVAL}s"
    ffmpeg -y -i "$VIDEO" \
      -vf "fps=1/${INTERVAL},showinfo,scale=1280:-1" \
      -q:v 3 "$VDIR/frames/f_%04d.jpg" \
      2> "$VDIR/frame_log.txt"
    ;;
  *)
    echo "Unknown mode: $MODE (use scene or fps)" >&2; exit 2
    ;;
esac

count=$(ls "$VDIR/frames"/*.jpg 2>/dev/null | wc -l | tr -d ' ')
echo "[extract] $count frames -> $VDIR/frames"

# Suggest tuning
if [[ "$MODE" == "scene" ]]; then
  if [[ $count -gt 200 ]]; then
    echo "[hint] too many frames; raise threshold (try 0.40 or 0.50)"
  elif [[ $count -lt 10 ]]; then
    echo "[hint] too few frames; lower threshold (try 0.20 or 0.15) OR switch to fps mode"
  fi
fi
