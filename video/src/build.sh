#!/usr/bin/env bash
# Baut video/staubern-2026-challenge.mp4. Braucht node+playwright, python3+numpy, ffmpeg
# und die Schriften Barlow Condensed (600/700), IBM Plex Sans (500/600), IBM Plex Mono (500)
# als TTF in $FONTS (Dateinamen siehe scene.html).
set -euo pipefail
cd "$(dirname "$0")"
FONTS=${FONTS:?FONTS=Pfad zum Schriften-Ordner setzen}
WORK=${WORK:-$(mktemp -d)}
node render.js "$FONTS" "$WORK/frames" 30
python3 audio.py "$WORK/audio.wav"
ffmpeg -y -loglevel error -framerate 30 -i "$WORK/frames/f%04d.png" -i "$WORK/audio.wav" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -profile:v high -movflags +faststart \
  -c:a aac -b:a 192k -shortest ../staubern-2026-challenge.mp4
echo "fertig: video/staubern-2026-challenge.mp4"
