#!/bin/bash
# Sahne 5 (Three.js): eskizden 3D'ye. Cikti: video.mp4 (1920x1080, 30 fps, 300 kare), kontrol.png, olaylar.json
set -euo pipefail
BU="$(cd "$(dirname "$0")" && pwd)"
KOK="$(cd "$BU/../../../.." && pwd)"
cd "$KOK"
python3 "$BU/hazirla.py"                      # eskizden murekkep katmani (eskiz-cizgi.png)
node "$BU/olaylar.mjs"                        # ses olaylari, ayni zaman.js'ten
KARE="$BU/.kareler"
BAS=$(date +%s)
python3 ortak/yakala.py ornek/ucan-makine/sahneler/05-threejs/sayfa.html "$KARE"
echo "kare yakalama: $(( $(date +%s) - BAS )) sn"
N=$(ls "$KARE"/*.png | wc -l | tr -d ' ')
[ "$N" = 300 ] || { echo "HATA: $N kare (300 olmali)"; exit 1; }
ffmpeg -loglevel error -y -framerate 30 -i "$KARE/%04d.png" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -r 30 -frames:v 300 -movflags +faststart "$BU/video.mp4"
ffmpeg -loglevel error -y -i "$KARE/0000.png" -i "$KARE/0050.png" -i "$KARE/0130.png" -i "$KARE/0210.png" -i "$KARE/0299.png" \
  -filter_complex "[0]scale=384:216[a];[1]scale=384:216[b];[2]scale=384:216[c];[3]scale=384:216[d];[4]scale=384:216[e];[a][b][c][d][e]hstack=5" "$BU/kontrol.png"
rm -rf "$KARE"
echo "toplam: $(( $(date +%s) - BAS )) sn"
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_read_frames,pix_fmt,codec_name -of csv=p=0 "$BU/video.mp4"
