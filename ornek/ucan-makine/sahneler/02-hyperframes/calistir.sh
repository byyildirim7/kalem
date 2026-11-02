#!/bin/bash
# Sahne 2 HyperFrames: bilgi karti + 1485->1903 sayaci
set -e
AD="$(cd "$(dirname "$0")" && pwd)"
M="$AD/../../../../motorlar/hyperframes"   # paket kökündeki motor (kurulum.sh kurar)
BIN="$M/node_modules/.bin"
mkdir -p "$AD/proje/lib"
cp "$M/node_modules/gsap/dist/gsap.min.js" "$AD/proje/lib/" 2>/dev/null || cp "$M/lib/gsap.min.js" "$AD/proje/lib/"
python3 "$AD/olay.py"
cd "$AD/proje"; mkdir -p renders; rm -f renders/*.mp4
"$BIN/hyperframes" render . -o renders/cikti.mp4 --fps 30 --quiet --workers 1 --no-best-effort >&2 || "$BIN/hyperframes" render . -o renders/cikti.mp4 --fps 30 --workers 1 >&2
ffmpeg -loglevel error -y -i renders/cikti.mp4 -c:v libx264 -pix_fmt yuv420p -r 30 -frames:v 240 -an "$AD/video.mp4"
ffmpeg -loglevel error -y -i "$AD/video.mp4" -vf "select='eq(n,0)+eq(n,50)+eq(n,110)+eq(n,170)+eq(n,225)',scale=384:-1,tile=5x1" -frames:v 1 "$AD/kontrol.png"
mkdir -p "$AD/k"; for n in 0 110 225; do ffmpeg -loglevel error -y -i "$AD/video.mp4" -vf "select=eq(n\,$n)" -frames:v 1 "$AD/k/$n.png"; done
ffprobe -v error -show_entries stream=codec_name,pix_fmt,width,height,nb_frames,r_frame_rate -of csv=p=0 "$AD/video.mp4"
