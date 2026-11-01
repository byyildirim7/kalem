#!/bin/bash
# Sahne 3 (Manim): video.mp4 + kontrol.png + olaylar.json
set -e
cd "$(dirname "$0")"
PY="${MANIM_PY:-python3}"   # Manim kurulu python; başka bir ortamsa MANIM_PY ile ver
T=$(mktemp -d)
$PY -m manim render -r 1920,1080 --fps 30 --media_dir "$T" -v WARNING sahne.py Kaldirma
SRC=$(find "$T" -name Kaldirma.mp4 | head -1)
# tam 240 kare: fazlayı kes, eksiği son kareyi tutarak uzat
ffmpeg -y -v error -i "$SRC" -vf "tpad=stop_mode=clone:stop=30,trim=end_frame=240,setpts=PTS-STARTPTS,fps=30,format=yuv420p" -c:v libx264 -crf 14 -pix_fmt yuv420p -r 30 video.mp4
N=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 video.mp4)
echo "kare: $N"
ffmpeg -y -v error -i video.mp4 -vf "select='eq(n,0)+eq(n,50)+eq(n,95)+eq(n,150)+eq(n,239)',scale=384:-1,tile=5x1" -frames:v 1 kontrol.png
rm -rf "$T"
