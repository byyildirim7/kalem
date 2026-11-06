#!/usr/bin/env python3
"""Blueprint stili: Codex'siz, tamamen kodla. Tasarımın kendi iskeletinden (iskelet.png + geometri) iki görsel üretir:
  (a) levha.png: makinenin tamamı, (b) govde.png: hareketli parçalar yok. Lacivert zemin (hafif ışık gradyanı) + ince ızgara
  (ana + ara), beyaz/açık mavi ince çizgiler, kesitlerde 45° tarama, parçaların içi opak (ızgara görünmez), sağ altta başlık bloğu.
  python3 blueprint.py <tasarım klasörü> [ad]   -> <klasör>/blueprint/{levha,govde}.png, levhalar/<ad>-blueprint.json
Merkez çizgileri ve parça numarası balonları videoda üst katmanda (levha.py / ders.py) çizilir: dönen parça onları döndürmesin."""
import json, os, sys, time, shutil, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); import mekanizma as MEK
W0, H0 = 1536, 1024
ZEMIN_ORTA, ZEMIN_KENAR = np.array([122, 70, 18], np.float32), np.array([84, 46, 10], np.float32)        # BGR #12467a, #0a2e54
IZGARA = np.array([255, 208, 159], np.float32); CIZGI = np.array([255, 244, 234], np.float32)
def _ilk_font(*yollar):
    for y in yollar:
        if os.path.exists(y): return y
    return yollar[-1]
DAR_FONT = _ilk_font("/System/Library/Fonts/Supplemental/Arial Narrow.ttf", "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf", "/Library/Fonts/Arial.ttf")
DUZ_FONT = _ilk_font("/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", DAR_FONT)
FONT = DAR_FONT
def tr_buyuk(s): return s.replace("i", "İ").replace("ı", "I").upper()

def zemin(w, h, ox=0., oy=0., sc=1.):
    """lacivert zemin + ışık gradyanı; ızgara ayrı katman (alfa). ox, oy, sc: seviye koordinatından bu görüntüye dönüşüm (video kâğıdı için)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); u, v = (xx - ox) / sc, (yy - oy) / sc
    r = np.clip(np.hypot((u - W0 * .45) / (W0 * .8), (v - H0 * .4) / (H0 * .9)), 0, 1)[..., None]
    z = ZEMIN_ORTA * (1 - r) + ZEMIN_KENAR * r
    g = np.zeros((h, w), np.float32)
    for adim, al in ((16, .07), (80, .17)):
        mx = np.abs(((u + adim / 2) % adim) - adim / 2) * sc; my = np.abs(((v + adim / 2) % adim) - adim / 2) * sc
        g = np.maximum(g, al * np.clip(1.2 - np.minimum(mx, my), 0, 1))
    return z, g

def tarama(m, aralik=11, aci=45):
    """45° kesit taraması (maske içinde)"""
    h, w = m.shape; t = np.zeros((h, w), np.uint8); L = int(np.hypot(h, w))
    for k in range(-L, L, aralik + 2): cv2.line(t, (k, 0), (k + h, h), 255, 2, cv2.LINE_AA)       # 2 px: oluşumda kalem vuruşu sayılır
    return (t.astype(np.float32) / 255) * (m > 0)

def ciz(K, ad):
    t0 = time.time(); G = json.load(open(os.path.join(K, "geometri.json"), encoding="utf-8")); isk = cv2.imread(os.path.join(K, "iskelet.png"))
    mek = G.get("tur") == "mekanizma"
    if mek: parca = [p for p in G["parcalar"]]; govde = G.get("govde", [])
    else:                                            # eski dişli tasarımı (iskelet-yolu): parçalar dişli, gövde tasarla.py'deki kutular
        parca = [dict(ad=k, tur="disk", c=v["c"], r=v["r"] + G["modul"]) for k, v in G["parcalar"].items()]
        govde = [{"kutu": [90, 900, 1450, 950]}, {"kutu": [675, 720, 725, 900]}, {"kutu": [1275, 600, 1325, 900]}]
    def pmaske(p):
        if p.get("sekil"): return MEK.maske(p["sekil"], (H0, W0)) > 127
        m = np.zeros((H0, W0), np.uint8); cv2.circle(m, (int(p["c"][0]), int(p["c"][1])), int(p["r"]), 255, -1); return m > 0
    PM = {p["ad"]: pmaske(p) for p in parca}; GM = MEK.maske(govde, (H0, W0)) > 127 if govde else np.zeros((H0, W0), bool)
    hatchli = lambda p: bool(p.get("sekil")) and not any("daire" in e for e in p["sekil"][:1])     # dolu kesitler: kiriş, blok, tutamak (makara/dişli değil)
    gy = cv2.cvtColor(isk, cv2.COLOR_BGR2GRAY); hsv = cv2.cvtColor(isk, cv2.COLOR_BGR2HSV)
    kir = (((hsv[..., 0] < 12) | (hsv[..., 0] > 168)) & (hsv[..., 1] > 90)); cizgi = (gy < 128) & ~kir
    if os.path.exists(os.path.join(K, "iskelet-govde.png")): cg = cv2.cvtColor(cv2.imread(os.path.join(K, "iskelet-govde.png")), cv2.COLOR_BGR2GRAY) < 128
    else: cg = cizgi & ~cv2.dilate(np.any(list(PM.values()), 0).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    z, g = zemin(W0, H0)
    def gorsel(cizgi_m, parcalar, kir_m):
        opak = GM.copy()
        for p in parcalar: opak |= PM[p["ad"]]
        img = z * (1 - (g * ~opak)[..., None]) + IZGARA * (g * ~opak)[..., None]
        th = tarama(GM.astype(np.uint8)) * .62
        for p in parcalar:
            if hatchli(p): th = np.maximum(th, tarama(PM[p["ad"]].astype(np.uint8)) * .6)
        img = img * (1 - th[..., None]) + IZGARA * th[..., None]
        if kir_m is not None: a = (kir_m.astype(np.float32) * .35)[..., None]; img = img * (1 - a) + IZGARA * a
        a = cv2.GaussianBlur(cizgi_m.astype(np.float32), (0, 0), .6)[..., None] * .95; img = img * (1 - a) + CIZGI * a
        baslik(img, ad, ALT); return img.clip(0, 255).astype(np.uint8)
    ys = np.nonzero((GM | np.any(list(PM.values()), 0))[:, 1150:1490].any(1))[0]; ALT = int(ys.max()) + 8 if len(ys) else 920   # başlık bloğu şekillerin altına
    A = gorsel(cizgi, parca, kir); B = gorsel(cg, [], None)
    o = os.path.join(K, "blueprint"); os.makedirs(o, exist_ok=True)
    cv2.imwrite(os.path.join(o, "levha.png"), A); cv2.imwrite(os.path.join(o, "govde.png"), B)
    for f in ("geometri.json", "iskelet.png", "iskelet-govde.png"):
        if os.path.exists(os.path.join(K, f)): shutil.copy(os.path.join(K, f), o)
    return time.time() - t0, o

def baslik(img, ad, alt=920):
    """sağ altta başlık bloğu: makine adı + ölçek (tarih ve isim yok); şekillerin altındaki boşluğa sığar"""
    x0, x1 = 1150, 1488; y0, y1 = 930, 996
    if alt > 930: y0, y1 = 28, 94                      # altta yer yoksa (dişli zinciri) sağ üstte, aynı boyda
    m = np.zeros(img.shape[:2], np.uint8)
    cv2.rectangle(m, (x0, y0), (x1, y1), 255, 2, cv2.LINE_AA); cv2.line(m, (x0, (y0 + y1) // 2), (x1, (y0 + y1) // 2), 255, 1, cv2.LINE_AA); cv2.line(m, (x0 + 210, (y0 + y1) // 2), (x0 + 210, y1), 255, 1, cv2.LINE_AA)
    im = Image.fromarray(m); d = ImageDraw.Draw(im); hh = (y1 - y0) / 2; f = ImageFont.truetype(FONT, int(min(22, hh * .75))); f2 = ImageFont.truetype(FONT, int(min(18, hh * .62)))
    ADLAR = {"kaldirac": "KALDIRAÇ", "palanga": "PALANGA", "iskelet-yolu": "DİŞLİ ZİNCİRİ"}
    d.text((x0 + 10, y0 + 3), "MAKİNE: " + ADLAR.get(ad, tr_buyuk(ad)), font=f, fill=255)
    d.text((x0 + 10, (y0 + y1) // 2 + 3), "ÖLÇEK 1:10", font=f2, fill=255); d.text((x0 + 220, (y0 + y1) // 2 + 3), "LEVHA 1/1", font=f2, fill=255)
    a = (np.array(im).astype(np.float32) / 255 * .9)[..., None]; img[:] = img * (1 - a) + CIZGI * a

if __name__ == "__main__":
    K = os.path.abspath(sys.argv[1]); ad = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(K)
    sure, o = ciz(K, ad); print(f"blueprint görselleri: {sure:.2f} sn -> {o}")
