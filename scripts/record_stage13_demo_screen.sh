#!/usr/bin/env bash
set -euo pipefail

OUT="demo_videos/stage13_screen_demo_$(date +%Y%m%d_%H%M%S).mp4"
SIZE="$(xdpyinfo | awk '/dimensions:/ {print $2; exit}')"

echo "Recording display: ${DISPLAY:-:0}"
echo "Screen size: $SIZE"
echo "Output: $OUT"
echo "Press Ctrl+C to stop."

ffmpeg -y \
  -video_size "$SIZE" \
  -framerate 30 \
  -f x11grab \
  -i "${DISPLAY:-:0}" \
  -c:v libx264 -preset veryfast -crf 23 \
  -pix_fmt yuv420p \
  "$OUT"
