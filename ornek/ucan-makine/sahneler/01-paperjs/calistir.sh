#!/bin/bash
# Sahne 1 (Paper.js): eskiz kendini çiziyor -> video.mp4 + kontrol.png + olaylar.json
set -eo pipefail
D="$(cd "$(dirname "$0")" && pwd)"; K="$(cd "$D/../../../.." && pwd)"; KARE="$D/kareler"
cd "$K"
BAS=$(date +%s)
python3 ortak/yakala.py ornek/ucan-makine/sahneler/01-paperjs/sayfa.html "$KARE" | tee "$D/yakala.log"
grep '^\[sayfa\] OLAYLAR ' "$D/yakala.log" | sed 's/^\[sayfa\] OLAYLAR //' > "$D/olaylar.json"
[ -s "$D/olaylar.json" ] || { echo "olaylar.json boş"; exit 1; }
N=$(ls "$KARE" | grep -c '\.png$'); [ "$N" -eq 240 ] || { echo "kare sayısı $N (240 olmalı)"; exit 1; }
ffmpeg -y -loglevel error -framerate 30 -i "$KARE/%04d.png" -frames:v 240 -c:v libx264 -pix_fmt yuv420p -crf 16 -r 30 "$D/video.mp4"
ffmpeg -y -loglevel error -i "$D/video.mp4" -vf "select='eq(n\,0)+eq(n\,60)+eq(n\,120)+eq(n\,180)+eq(n\,239)',scale=384:-1,tile=5x1" -frames:v 1 "$D/kontrol.png"
[ "${KAREYI_TUT:-0}" = "1" ] || rm -rf "$KARE"
echo "tamam: $(( $(date +%s) - BAS )) sn"
