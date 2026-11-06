#!/bin/bash
# Motor paketlerini kurar. Gerekenler: Node 20+, Python 3, ffmpeg, Google Chrome. Manim isteğe bağlı (pip install manim).
set -e
K="$(cd "$(dirname "$0")" && pwd)"
for d in motorlar/paperjs motorlar/pixijs motorlar/threejs motorlar/yardimci motorlar/hyperframes ses; do
  echo "kuruluyor: $d"
  [ -L "$K/$d/node_modules" ] && rm "$K/$d/node_modules"
  (cd "$K/$d" && npm install --no-audit --no-fund --loglevel=error)
done
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) WIN=1 ;; *) WIN= ;; esac   # Windows'ta Git Bash
if [ -n "$WIN" ]; then FF_KUR="winget install Gyan.FFmpeg"; else FF_KUR="brew install ffmpeg"; fi
command -v ffmpeg >/dev/null || echo "UYARI: ffmpeg yok ($FF_KUR)"
CHROME_VAR=
for a in "$CHROME" "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
         "$PROGRAMFILES/Google/Chrome/Application/chrome.exe" "$LOCALAPPDATA/Google/Chrome/Application/chrome.exe"; do
  [ -n "$a" ] && [ -f "$a" ] && CHROME_VAR=1
done
[ -n "$CHROME_VAR" ] || echo "UYARI: Google Chrome bulunamadı; CHROME değişkeniyle yolunu ver"
python3 -c "import manim" 2>/dev/null || [ -x "$K/.venv-manim/bin/python" ] || [ -x "$K/.venv-manim/Scripts/python.exe" ] \
  || echo "Not: Manim kurulu değil; formül sahneleri için: python3 -m venv .venv-manim && .venv-manim/bin/pip install manim (Windows: .venv-manim/Scripts/pip)"
echo tamam
