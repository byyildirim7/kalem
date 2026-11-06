#!/bin/bash
# Sahne 4: Matter.js. Paket kökünden bağımsız çalışır.
set -eo pipefail
D="$(cd "$(dirname "$0")" && pwd)"; KOK="$(cd "$D/../../../.." && pwd)"; T="$(mktemp -d)"
cd "$KOK"
python3 ortak/yakala.py ornek/ucan-makine/sahneler/04-matter/sayfa.html "$T/k" | tee "$T/log.txt"
python3 - "$T/log.txt" "$D/olaylar.json" <<'P'
import sys,json
for s in open(sys.argv[1]):
    if "OLAYLAR " in s: open(sys.argv[2],"w").write(json.dumps(json.loads(s.split("OLAYLAR ",1)[1]),ensure_ascii=False))
P
ffmpeg -y -loglevel error -framerate 30 -i "$T/k/%04d.png" -c:v libx264 -pix_fmt yuv420p -crf 16 -r 30 "$D/video.mp4"
ffmpeg -y -loglevel error -i "$D/video.mp4" -vf "select='eq(n,0)+eq(n,50)+eq(n,100)+eq(n,160)+eq(n,239)',scale=384:216,tile=5x1" -frames:v 1 "$D/kontrol.png"
rm -rf "$T"
