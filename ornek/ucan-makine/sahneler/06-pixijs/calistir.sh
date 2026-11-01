#!/bin/bash
# Sahne 6: PixiJS. Paket kökünden bağımsız çalışır.
set -e
D="$(cd "$(dirname "$0")" && pwd)"; KOK="$(cd "$D/../../../.." && pwd)"; K="$(mktemp -d)/kare"
cd "$KOK"
python3 ortak/yakala.py ornek/ucan-makine/sahneler/06-pixijs/sayfa.html "$K" | tee "$D/.log" | grep -v OLAYJSON || true
grep -h OLAYJSON "$D/.log" | sed 's/.*OLAYJSON //' > "$D/olaylar.json"
ffmpeg -y -v error -framerate 30 -i "$K/%04d.png" -c:v libx264 -pix_fmt yuv420p -crf 16 -preset medium -r 30 "$D/video.mp4"
ffmpeg -y -v error -i "$D/video.mp4" -vf "select='eq(n,0)+eq(n,50)+eq(n,98)+eq(n,160)+eq(n,239)',scale=384:-1,tile=5x1" -frames:v 1 "$D/kontrol.png"
rm -rf "$(dirname "$K")" "$D/.log"
python3 "$D/parlaklik.py" "$D/video.mp4"
