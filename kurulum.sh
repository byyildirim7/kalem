#!/bin/bash
# Motor paketlerini kurar. Gerekenler: Node 20+, Python 3, ffmpeg, Google Chrome. Manim isteğe bağlı (pip install manim).
set -e
K="$(cd "$(dirname "$0")" && pwd)"
for d in motorlar/paperjs motorlar/pixijs motorlar/threejs motorlar/yardimci motorlar/hyperframes ses; do
  echo "kuruluyor: $d"
  [ -L "$K/$d/node_modules" ] && rm "$K/$d/node_modules"
  (cd "$K/$d" && npm install --no-audit --no-fund --loglevel=error)
done
command -v ffmpeg >/dev/null || echo "UYARI: ffmpeg yok (brew install ffmpeg)"
[ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ] || [ -n "$CHROME" ] || echo "UYARI: Google Chrome bulunamadı; CHROME değişkeniyle yolunu ver"
python3 -c "import manim" 2>/dev/null || echo "Not: Manim kurulu değil; formül sahneleri için: python3 -m pip install manim (ya da MANIM_PY ile başka bir python göster)"
echo tamam
