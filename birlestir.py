#!/usr/bin/env python3
"""Sahneleri tek videoya birleştirir: sahneler arası gl-transitions geçişi + kareye kilitli Tone.js efekt sesi.
  python3 birlestir.py ornek/ucan-makine [--gecis BookFlip] [--etiket]
--etiket: her sahnenin altına motor kartı basar (zaman.json'da sahne "etiket": [motor, ne yapıyor, (yardımcı)],
ilk geçişte "gecis_etiketi"). Anlatım/tanıtım videosu için; düz kullanımda kapalı.
Girdi: <proje>/zaman.json + her sahnenin <proje>/sahneler/<klasor>/video.mp4 ve olaylar.json.
Çıktı: <proje>/cikti.mp4 (+ <proje>/_is/ ara dosyalar, <proje>/kontrol.png).
Geçiş, A'nın son N karesiyle B'nin ilk N karesini üst üste bindirir; toplam süre = kareler toplamı - N x (sahne-1)."""
import json, os, shutil, subprocess, sys

KOK = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows'ta varsayılan cp1254; Türkçe çıktı UTF-8 terminalde bozuluyordu
proje = sys.argv[1].rstrip("/")
GECIS = sys.argv[sys.argv.index("--gecis") + 1] if "--gecis" in sys.argv else "BookFlip"
P = os.path.join(KOK, proje)
Z = json.load(open(os.path.join(P, "zaman.json"), encoding="utf-8"))
FPS, W, H, N = Z["fps"], Z["genislik"], Z["yukseklik"], Z["gecis_kare"]
IS = os.path.join(P, "_is"); shutil.rmtree(IS, ignore_errors=True); os.makedirs(IS)
KOD = ["-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS)]

def ff(*a): subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)
def kare_say(v):
    return int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                               "stream=nb_read_frames", "-of", "csv=p=0", v], capture_output=True, text=True, check=True).stdout.strip())

S = Z["sahneler"]
for s in S:
    v = os.path.join(P, "sahneler", s["klasor"], "video.mp4")
    if not os.path.exists(v): sys.exit(f"eksik: {v}")
    k = kare_say(v)
    if k != s["kare"]: print(f"uyarı: {s['klasor']} {k} kare, beklenen {s['kare']} (gerçek sayı kullanılır)")
    s["_v"], s["_k"] = v, k

parca, olay, ofs = [], [], 0
for i, s in enumerate(S):
    bas, son = (N if i > 0 else 0), (s["_k"] - N if i < len(S) - 1 else s["_k"])
    g = os.path.join(IS, f"govde{i}.mp4")
    ff("-i", s["_v"], "-vf", f"trim=start_frame={bas}:end_frame={son},setpts=PTS-STARTPTS", "-an", *KOD, g)
    parca.append(g)
    oj = os.path.join(P, "sahneler", s["klasor"], "olaylar.json")
    for o in (json.load(open(oj, encoding="utf-8")) if os.path.exists(oj) else []):
        olay.append({**o, "kare": o["kare"] + ofs, "sahne": s["no"]})
    if i < len(S) - 1:
        d = os.path.join(IS, f"gecis{i}"); os.makedirs(d + "/a"); os.makedirs(d + "/b")
        ff("-i", s["_v"], "-vf", f"select=gte(n\\,{s['_k'] - N})", "-vsync", "0", "-start_number", "0", d + "/a/%04d.png")
        ff("-i", S[i + 1]["_v"], "-vf", f"select=lt(n\\,{N})", "-vsync", "0", "-start_number", "0", d + "/b/%04d.png")
        rel = os.path.relpath(d, KOK)
        subprocess.run([sys.executable, os.path.join(KOK, "ortak/yakala.py"), f"ortak/gecis.html?k={rel}&ad={GECIS}&n={N}&w={W}&h={H}",
                        d + "/cikis", str(W), str(H)], check=True)
        gv = os.path.join(IS, f"gecis{i}.mp4")
        ff("-framerate", str(FPS), "-i", d + "/cikis/%04d.png", *KOD, gv)
        parca.append(gv)
        olay.append({"kare": ofs + s["_k"] - N, "tur": "sayfa", "guc": 0.8})
    ofs += s["_k"] - N

TOPLAM = ofs + N   # son sahnede N düşülmedi

def kart(satirlar, yol):
    """Defter kağıdı rengi küçük kart: motor adı (Fell) + ne yaptığı (Garamond italik) + isteğe bağlı yardımcı satırı."""
    from PIL import Image, ImageDraw, ImageFont
    F = lambda d, n: ImageFont.truetype(os.path.join(KOK, "ortak/font", d), n)
    yazi = [(satirlar[0], F("IMFeENrm28P.ttf", 58), (43, 29, 18)), (satirlar[1], F("EBGaramond-Italic.ttf", 37), (90, 70, 50))]
    if len(satirlar) > 2: yazi.append((satirlar[2], F("EBGaramond.ttf", 30), (120, 98, 72)))
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    gen = max(d0.textlength(t, font=f) for t, f, _ in yazi) + 2 * 30 + 26
    yuk = 24 + 68 + 46 + (40 if len(yazi) > 2 else 0) + 20
    im = Image.new("RGBA", (int(gen) + 12, yuk + 12), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 9, gen + 8, yuk + 9), 8, fill=(60, 40, 20, 40))                     # yumuşak gölge
    d.rounded_rectangle((3, 3, gen + 3, yuk + 3), 8, fill=(244, 235, 214, 238), outline=(43, 29, 18, 200), width=2)
    d.ellipse((30, 26 + 24, 46, 26 + 40), fill=(179, 38, 30, 255))                                 # tek kırmızı nokta
    y = 22
    for i, (t, f, c) in enumerate(yazi):
        d.text((30 + (26 if i == 0 else 0), y), t, font=f, fill=c + (255,)); y += [70, 46, 40][i]
    im.save(yol); return im.size

if "--etiket" in sys.argv:
    kartlar, ofs2 = [], 0
    for i, s in enumerate(S):
        bas = ofs2 + (N if i > 0 else 0); son = ofs2 + s["_k"] - (N if i < len(S) - 1 else 0)
        if s.get("etiket"): kartlar.append((s["etiket"], bas + 12, son - 6, "sol"))
        if i == 0 and Z.get("gecis_etiketi"): kartlar.append((Z["gecis_etiketi"], son - 20, son + N + 30, "sag"))
        ofs2 += s["_k"] - N
    girdi, zincir, onceki = [], [], "[0:v]"
    for k, (st, a, b, yer) in enumerate(kartlar):
        yol = os.path.join(IS, f"kart{k}.png"); w, h = kart(st, yol)
        x = 48 if yer == "sol" else W - w - 48; y = H - h - 40
        girdi += ["-loop", "1", "-framerate", str(FPS), "-t", f"{TOPLAM / FPS:.3f}", "-i", yol]
        ta, tb = a / FPS, b / FPS
        zincir.append(f"[{k + 1}:v]format=rgba,fade=in:st={ta:.3f}:d=0.4:alpha=1,fade=out:st={tb - 0.4:.3f}:d=0.4:alpha=1[e{k}]")
        zincir.append(f"{onceki}[e{k}]overlay={x}:{y}:enable='between(t,{ta:.3f},{tb:.3f})'[v{k}]"); onceki = f"[v{k}]"
    _etiket = (girdi, zincir, onceki, os.path.join(IS, "etiketli.mp4"))
liste = os.path.join(IS, "liste.txt")
open(liste, "w", encoding="utf-8").write("".join(f"file '{p}'\n" for p in parca))
sessiz = os.path.join(IS, "sessiz.mp4")
ff("-f", "concat", "-safe", "0", "-i", liste, "-c", "copy", sessiz)
if "--etiket" in sys.argv:
    girdi, zincir, onceki, etiketli = _etiket
    ff("-i", sessiz, *girdi, "-filter_complex", ";".join(zincir), "-map", onceki, "-frames:v", str(TOPLAM), *KOD, etiketli); sessiz = etiketli
olay.sort(key=lambda o: o["kare"])
json.dump({"fps": FPS, "kare": TOPLAM, "olaylar": olay}, open(os.path.join(IS, "olaylar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
wav = os.path.join(IS, "ses.wav")
subprocess.run(["node", os.path.join(KOK, "ses/render.mjs"), os.path.relpath(os.path.join(IS, "olaylar.json"), KOK), wav], check=True)
cikti = os.path.join(P, "cikti.mp4")
ff("-i", sessiz, "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", cikti)
ff("-i", cikti, "-vf", f"select='not(mod(n\\,{max(1, TOPLAM // 12)}))',scale=320:-1,tile=6x2", "-frames:v", "1", "-vsync", "0", os.path.join(P, "kontrol.png"))
print(f"tamam: {cikti}  {kare_say(cikti)} kare ({kare_say(cikti) / FPS:.1f} sn), {len(olay)} ses olayı")
