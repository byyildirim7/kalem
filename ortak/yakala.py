#!/usr/bin/env python3
"""Tarayıcı motorları için ortak kare yakalayıcı.
  python3 ortak/yakala.py <sayfa> <cikis_klasoru> [genislik] [yukseklik]
<sayfa> paket köküne göre yol (ör. ornek/ucan-makine/sahneler/01-paperjs/sayfa.html).
Sayfa ortak/surucu.js'i kur()/kare(f) ile çağırır; kareler cikis/0000.png ... olarak yazılır.
Zaman kare numarasından gelir; Math.random yok, iki koşu aynı kareyi verir."""
import http.server, os, sys, subprocess, threading, shutil, tempfile
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # sayfa günlüğü her karakteri taşıyabilir; Windows konsolu cp1252/cp1254
def chrome_bul():   # CHROME değişkeni > işletim sisteminin bilinen yolları > PATH
    if os.environ.get("CHROME"): return os.environ["CHROME"]
    adaylar = {"darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
               "win32": [os.path.join(os.environ.get(v, ""), "Google", "Chrome", "Application", "chrome.exe") for v in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]}
    for a in adaylar.get(sys.platform, []) + [shutil.which(n) or "" for n in ("google-chrome", "chromium", "chrome")]:
        if a and os.path.exists(a): return a
    sys.exit("Chrome bulunamadı; CHROME değişkeniyle yolunu ver")
CHROME = chrome_bul()
sayfa, cikis = sys.argv[1], os.path.abspath(sys.argv[2])
W, H = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1920, 1080)
shutil.rmtree(cikis, ignore_errors=True); os.makedirs(cikis)
import time
bitti = threading.Event(); durum = {"hata": None, "son": time.time(), "kare": 0}
class I(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=KOK, **k)
    def log_message(s, *a): pass
    def end_headers(s): s.send_header("Cache-Control", "no-store"); super().end_headers()
    def do_POST(s):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(s.path); q = parse_qs(u.query); veri = s.rfile.read(int(s.headers.get("Content-Length", 0)))
        durum["son"] = time.time()
        if u.path == "/kare": durum["kare"] += 1; open(os.path.join(cikis, f"{int(q['i'][0]):04d}.png"), "wb").write(veri)
        elif u.path == "/log": print("[sayfa]", veri.decode("utf-8", "replace"), flush=True)
        elif u.path == "/bitti":
            m = veri.decode(); print("[sayfa] bitti:", m, flush=True)
            if m.startswith("hata"): durum["hata"] = m
            bitti.set()
        s.send_response(200); s.send_header("Content-Length", "0"); s.end_headers()
http.server.ThreadingHTTPServer.allow_reuse_address = True
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), I); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
prof = tempfile.mkdtemp(prefix="vm-yakala-")
angle = ["--use-angle=metal"] if sys.platform == "darwin" else []   # Metal yalnız macOS'ta; Windows kendi varsayılanını (D3D11) kullanır
# --expose-gc: surucu.js birkaç karede bir gc() çağırır; büyük PNG blob'ları birikip Chrome'un blob sınırını doldurmasın
p = subprocess.Popen([CHROME, "--headless=new", f"--user-data-dir={prof}", "--no-first-run", *angle, "--enable-gpu", "--js-flags=--expose-gc",
                      "--ignore-gpu-blocklist", f"--window-size={W},{H}", f"http://127.0.0.1:{port}/{sayfa}"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    ok = False
    while not ok:   # 60 sn hiç ses gelmezse sayfa yüklenmemiştir (çoğu zaman JS sözdizimi hatası)
        ok = bitti.wait(timeout=2)
        if not ok and time.time() - durum["son"] > 60:
            print(f"ZAMAN AŞIMI: 60 sn sayfadan ses yok ({durum['kare']} kare geldi). Sözdizimini sına: node --check <js>"); break
finally:
    p.terminate(); p.wait(); shutil.rmtree(prof, ignore_errors=True); srv.shutdown()   # başsız Chrome öksüz kalmasın
if not ok: sys.exit(2)
if durum["hata"]: sys.exit(1)
