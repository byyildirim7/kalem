#!/usr/bin/env python3
"""Levha motoru (genel): durgun Codex levhası + parça tanımı -> kalemle oluşum + melez çalışma + durma sonu.
  python3 levha.py levhalar/<ad>.json [--hizli] [--seviye 8|lise] [--varyant ...] [--stil blueprint]
Levhaya özel olan YALNIZ tanım dosyası (parçalar, merkez, elips, diş sayısı, hareket, ön maskeler, kuvvet yolu).
Çıktı: cikti/<ad>-v4-dur.mp4, -kontrol.png, -olusum-izgara.png, -yakin.png, -olcum.txt. Model yok: OpenCV + NumPy + SciPy + PIL.

Hareket türleri: donme {hiz: tur/sn} · bagli {parca, oran: (-) ters yön} · esapman {periyot: çapa salınım periyodu, her
yarım periyotta bir diş} · salinim {genlik: derece, periyot: sn, atalet: durma süresi çarpanı}.
Parça türleri: disk (elips içi tamamı döner) · disli (jant + diş silueti + göbek + kollar) · parca (maske: kirmizi, pivot etrafında)
· sekil (GENEL: herhangi bir şekil + eklem; hareketi mekanizma.py çözücüsü verir: krank_kayma, biyel, anahtar, ip_sarma, mermi, sabit).
İki görsel yöntemi: tanımda gorsel_b (aynı iskelet, hareketli parçalar YOK) varsa parçaların açtığı yer (b)'den dolar; (b) parça
çevresinde faz korelasyonuyla yerel hizalanır, kâğıt tonu (a)'ya eşitlenir. Dişli, bu modelin özel hâli (dönme eklemi + bağlı oran)."""
import json, os, re, subprocess, sys, time
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"): os.environ.setdefault(_k, "1")   # fork'lu paralel render kilitlenmesin
import cv2, numpy as np
cv2.setNumThreads(0)
import mekanizma as MEK
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

D = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(sys.argv[1], encoding="utf-8")); AD = T["ad"]; HIZLI = "--hizli" in sys.argv
_arg = lambda k, v=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else v
SEVIYE, VARYANT = _arg("--seviye", "8"), _arg("--varyant")
if T.get("ders"): AD = AD + ("-seviye8" if SEVIYE == "8" else "-lise" + (f"-{VARYANT}" if VARYANT else ""))
STIL = _arg("--stil", T.get("stil", "defter")); INV = STIL == "blueprint"        # blueprint: açık çizgi koyu zemin (mürekkep mantığı ters)
if INV: AD = AD + "-blueprint"
DERS_OGE = []
OK_ = float(T.get("olusum_olcek", (T.get("ders") or {}).get("olusum_olcek", 1.0)))   # kalemle oluşum süresi çarpanı (1,0 = 14,3 sn)
if T.get("ders") and SEVIYE != "8":               # lise: hareket ders kitabı şekli gibi YATAY dengede biter (dik uzaklık = kol boyu)
    for _p in T["parcalar"]:
        if _p["ad"] in T["ders"].get("kareler_lise", {}): _p["hareket"]["kareler"] = T["ders"]["kareler_lise"][_p["ad"]]
    T["smax"] = T["ders"].get("smax_lise", T.get("smax"))
REF = cv2.imread(os.path.join(D, T["gorsel"])); H0, W0 = REF.shape[:2]; G = cv2.cvtColor(REF, cv2.COLOR_BGR2GRAY).astype(np.float32)
if INV: G = 255 - G                               # "mürekkep koyu, kâğıt açık" varsayımı korunur
W, H, FPS = 1920, 1080, 30; SC = H / H0; OX = (W - W0 * SC) / 2
YY, XX = np.mgrid[0:H0, 0:W0].astype(np.float32)
GB_IMG = cv2.imread(os.path.join(D, T["gorsel_b"])) if T.get("gorsel_b") else None   # (b): yalnız gövde
ZMN = T.get("zaman", {})
OLC = []; T0 = time.time()
def adim(ad): OLC.append((ad, round(time.time() - T0, 1))); print(f"[{time.time() - T0:6.1f} sn] {ad}", flush=True)
sio = lambda x: .5 - .5 * np.cos(np.pi * np.clip(x, 0, 1)); ara = lambda t, a, b: np.clip((t - a) / (b - a), 0, 1)

# ═════ 1. maskeler ve dokular
def sekil(e, shape=(H0, W0)):
    m = np.zeros(shape, np.uint8)
    if "kutu" in e: x0, y0, x1, y1 = e["kutu"]; m[y0:y1, x0:x1] = 255
    if "cokgen" in e: cv2.fillPoly(m, [np.int32(e["cokgen"])], 255, cv2.LINE_AA)
    if "daire" in e: cv2.circle(m, tuple(e["daire"][:2]), e["daire"][2], 255, -1, cv2.LINE_AA)
    return m
ON = np.zeros((H0, W0), np.uint8)
for e in T["on"]: ON = np.maximum(ON, sekil(e))
if T.get("on_maske") and os.path.exists(T["on_maske"]): ON = np.maximum(ON, cv2.imread(T["on_maske"], 0))
P = {p["ad"]: p for p in T["parcalar"]}
def kutup(p): c = p["c"]; u, v = (XX - c[0]) / p["sx"], (YY - c[1]) / p["sy"]; return np.hypot(u, v), np.degrees(np.arctan2(v, u)) % 360
def alfa_sekil(p):
    """şekil sınırı (+6 px) içindeki mürekkep; sınırdan dışarı taşan kâğıt saydam (diş arası yöntemiyle aynı)."""
    m = MEK.maske(p["sekil"], (H0, W0)) > 127; pay = int(p.get("pay", 6)); ell = lambda k: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1))
    big = cv2.dilate(m.astype(np.uint8), ell(pay)) > 0; core = cv2.erode(m.astype(np.uint8), ell(3)) > 0
    ring = (cv2.dilate(big.astype(np.uint8), ell(2)) > 0) & ~big; kag = ((G > (150 if INV else 195)) & big & ~core) | ring
    n, lab = cv2.connectedComponents(kag.astype(np.uint8), connectivity=4); dis = np.unique(lab[ring]); dis = dis[dis > 0]
    al = big & ~np.isin(lab, dis); al = cv2.morphologyEx(al.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(al.astype(np.float32) / 255, (0, 0), .7)
def alfa(p):
    if p["tur"] == "sekil": return alfa_sekil(p)
    if p["tur"] == "disk":
        m = np.zeros((H0, W0), np.uint8); c = p["c"]; cv2.ellipse(m, (int(c[0] * 8), int(c[1] * 8)), (int(p["r"] * p["sx"] * 8), int(p["r"] * p["sy"] * 8)), 0, 0, 360, 255, -1, cv2.LINE_AA, 3)
        return m.astype(np.float32) / 255
    if p["tur"] == "parca":                       # kırmızı mürekkep (çapa) + pivot göbeği
        hsv = cv2.cvtColor(REF, cv2.COLOR_BGR2HSV); h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        m = (((h < 14) | (h > 165)) & (s > 55) & (v > 50)).astype(np.uint8) * 255
        if p.get("bolge"): x0, y0, x1, y1 = p["bolge"]; b = np.zeros_like(m); b[y0:y1, x0:x1] = 1; m *= b
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)); n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        m = np.isin(lab, [i for i in range(1, n) if st[i, 4] > 400]).astype(np.uint8) * 255
        m = ndimage.binary_fill_holes(m > 0).astype(np.uint8) * 255; m = cv2.dilate(m, np.ones((5, 5), np.uint8))
        if p.get("ek_daire"): m = np.maximum(m, sekil({"daire": p["ek_daire"]}))
        return cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), .7)
    r, a = kutup(p); j0, j1 = p["jant"]; R = p["r"]
    m = ((r >= j0) & (r <= R + 1)) | (r <= p.get("gobek", 0))
    halka = (r >= j1) & (r <= R + 5); kagit = ((G > 178) & halka) | ((r > R + 1) & (r <= R + 5))   # diş arası: dışarıdan taşan kâğıt
    n, lab = cv2.connectedComponents(kagit.astype(np.uint8), connectivity=4); dis = np.unique(lab[(r > R + 1) & (r <= R + 5)]); dis = dis[dis > 0]
    m &= ~np.isin(lab, dis)
    if p.get("kol"):
        k = p["kol"]; d = (a - k["aci0"] + 180 / k["n"]) % (360 / k["n"]) - 180 / k["n"]
        m |= (np.abs(r * np.sin(np.radians(d))) <= k["genislik"] / 2) & (r >= p.get("gobek", 0) * .7) & (r <= j0 + 3)
    m = cv2.morphologyEx(m.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), .7)
def donusum(p, th):                               # kaynak -> hedef afin (elips çerçevesinde dönme; düşmede th = (dy, saydamlık))
    if isinstance(th, tuple): return np.array([[1, 0, 0], [0, 1, th[0]]], np.float64)
    if p["tur"] == "parca": cx, cy = p["pivot"]; sx = sy = 1
    else: (cx, cy), sx, sy = p["c"], p["sx"], p["sy"]
    c, s = np.cos(th), np.sin(th); A = np.array([[c, -s * sx / sy], [s * sy / sx, c]])
    return np.hstack([A, (np.array([cx, cy]) - A @ np.array([cx, cy]))[:, None]])
def kutusu(p, al):
    ys, xs = np.nonzero(al > .01); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    if p["tur"] == "sekil": pass                  # öteleme/dönmede hedef kutu her karede ayrıca hesaplanır
    elif p["tur"] == "parca":
        cx, cy = p["pivot"]; R = np.hypot(np.maximum(abs(x0 - cx), abs(x1 - cx)), np.maximum(abs(y0 - cy), abs(y1 - cy))); x0, y0, x1, y1 = cx - R, cy - R, cx + R, cy + R
    else:
        c = p["c"]; x0, y0, x1, y1 = c[0] - p["r"] * p["sx"] - 6, c[1] - p["r"] * p["sy"] - 6, c[0] + p["r"] * p["sx"] + 6, c[1] + p["r"] * p["sy"] + 6
    return [int(max(0, np.floor(x0))), int(max(0, np.floor(y0))), int(min(W0, np.ceil(x1))), int(min(H0, np.ceil(y1)))]

def kagit_haritasi(img, m, yk):
    gy = img @ np.array([.114, .587, .299], np.float32); w = ((gy > 192) & (m == 0)).astype(np.float32)
    if w.sum() < 1000: return np.broadcast_to(yk, img.shape).astype(np.float32)
    num = cv2.GaussianBlur(img * w[..., None], (0, 0), 22); den = cv2.GaussianBlur(w, (0, 0), 22)[..., None]
    return np.where(den > 1e-3, num / np.maximum(den, 1e-3), yk)
def kagit_doldur(img, m, tohum=1):
    """maske içi: düz kâğıt yaması (doku) + yerel kâğıt rengi haritası; kenar 1,2 px yumuşak."""
    yg = (G < 195).astype(np.float32); en = None
    for y in range(0, H0 - 120, 20):
        for x in range(0, W0 - 320, 20):
            s = yg[y:y + 120, x:x + 320].sum()
            if en is None or s < en[0]: en = (s, x, y)
    _, x, y = en; Y = REF[y:y + 120, x:x + 320].astype(np.float32); yk = Y.reshape(-1, 3).mean(0)
    rng = np.random.default_rng(tohum); big = np.zeros(img.shape, np.float32); h, w = Y.shape[:2]
    for yy in range(0, img.shape[0], h):
        for xx in range(0, img.shape[1], w):
            t = np.flip(Y, 1) if rng.random() < .5 else Y; big[yy:yy + h, xx:xx + w] = t[:min(h, img.shape[0] - yy), :min(w, img.shape[1] - xx)]
    big += kagit_haritasi(img, m, yk) - yk
    a = cv2.GaussianBlur((m > 0).astype(np.float32), (0, 0), 1.2)[..., None]
    return img * (1 - a) + big * a
def kaydir_doldur(img, m, kutu, eksen):
    x0, y0, x1, y1 = kutu; out = img.copy(); kal = np.zeros(m.shape, bool); kal[y0:y1, x0:x1] = m[y0:y1, x0:x1] > 0
    for d in (-70, 70, -120, 120, -180, 180, -260, 260):
        ys, xs = np.nonzero(kal); yk, xk = (ys + d, xs) if eksen == "dikey" else (ys, xs + d)
        ok = (yk >= y0) & (yk < y1) & (xk >= x0) & (xk < x1); ok[ok] &= (m[yk[ok], xk[ok]] == 0)
        out[ys[ok], xs[ok]] = img[yk[ok], xk[ok]]; kal[ys[ok], xs[ok]] = False
    return out, kal

def hazirla():
    A = {}; ref = REF.astype(np.float32)
    for p in T["parcalar"]: A[p["ad"]] = alfa(p)
    # iki dönen parçanın kesiştiği pikseller (kavrama bölgesi): merkezine göre normalize yarıçapı küçük olan parçanın (komşunun dişi komşuya)
    dd = [p for p in T["parcalar"] if p["tur"] in ("disk", "disli")]
    if len(dd) > 1:
        RN = np.stack([np.hypot((XX - p["c"][0]) / p["sx"], (YY - p["c"][1]) / p["sy"]) / (p["r"] - (1. if p["tur"] == "disk" else (p["r"] - p["jant"][1]) * .45)) for p in dd])
        sahip = np.argmin(RN, 0)
        for i, p in enumerate(dd): A[p["ad"]] = A[p["ad"]] * cv2.GaussianBlur((sahip == i).astype(np.float32), (0, 0), .6)
    adlar = [p["ad"] for p in T["parcalar"]]; DOK = {}
    for i, p in enumerate(T["parcalar"]):         # doku: kendi pikseli; önündekilerin altında kalan yer dönme simetrisiyle
        al = A[p["ad"]]; tex = ref.copy()
        ortu = (ON > 40) | np.any([A[q] > .3 for q in adlar[i + 1:]] or [np.zeros((H0, W0), bool)], axis=0)
        for ip in T.get("ipler", []):                 # ip bu parçanın önünden geçiyorsa (sonra = bu ya da önceki parça)
            if adlar.index(ip["sonra"]) >= i: ortu = ortu | (IPM[ip["ad"]] > 0)
        n = p.get("simetri") or 0
        if p["tur"] == "sekil" and not (n and "c" in p):   # simetrisiz parça: önü kapalı yer çevresinden onarılır (Telea)
            kal = ortu & (al > .01)
            if kal.any():
                ys_, xs_ = np.nonzero(al > .01); bx0, by0, bx1, by1 = max(0, xs_.min() - 8), max(0, ys_.min() - 8), min(W0, xs_.max() + 9), min(H0, ys_.max() + 9)
                tex[by0:by1, bx0:bx1] = cv2.inpaint(REF[by0:by1, bx0:bx1], kal[by0:by1, bx0:bx1].astype(np.uint8) * 255, 6, cv2.INPAINT_TELEA).astype(np.float32)
            n = 0
        if n and p["tur"] != "parca":
            r, a = kutup(p); kal = ortu & (al > .01)
            for k in list(range(1, n)):
                if not kal.any(): break
                aa = np.radians(a[kal] + 360 * k / n); xs = p["c"][0] + p["sx"] * r[kal] * np.cos(aa); ys = p["c"][1] + p["sy"] * r[kal] * np.sin(aa)
                xi, yi = np.clip(np.round(xs).astype(int), 0, W0 - 1), np.clip(np.round(ys).astype(int), 0, H0 - 1)
                ok = ~ortu[yi, xi]; idx = np.argwhere(kal)[ok]; tex[idx[:, 0], idx[:, 1]] = ref[yi[ok], xi[ok]]; kal[idx[:, 0], idx[:, 1]] = False
            if p["tur"] == "sekil" and kal.any():        # simetriyle dolmayan artık: Telea
                ys_, xs_ = np.nonzero(al > .01); bx0, by0, bx1, by1 = max(0, xs_.min() - 8), max(0, ys_.min() - 8), min(W0, xs_.max() + 9), min(H0, ys_.max() + 9)
                tex[by0:by1, bx0:bx1] = cv2.inpaint(np.clip(tex[by0:by1, bx0:bx1], 0, 255).astype(np.uint8), kal[by0:by1, bx0:bx1].astype(np.uint8) * 255, 6, cv2.INPAINT_TELEA).astype(np.float32)
        if p.get("notr"):                            # kırmızı mürekkebi sepyaya çevir (kırmızı yalnız kuvvet oklarında)
            hsv = cv2.cvtColor(np.clip(tex, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV); kr = (((hsv[..., 0] < 14) | (hsv[..., 0] > 165)) & (hsv[..., 1] > 50)) & (al > .01)
            lum = (tex @ np.array([.114, .587, .299], np.float32))[..., None] / 215.; ink_, kag_ = np.array([22, 39, 58], np.float32), np.array([184, 217, 232], np.float32)
            tex = np.where(kr[..., None], ink_ + (kag_ - ink_) * np.clip(lum, 0, 1), tex)
        x0, y0, x1, y1 = kutusu(p, al)
        if p["hareket"]["tur"] == "dusme":              # inişe kadar: topun altında ilk dolu mürekkep satırı
            ys_, xs_ = np.nonzero(al > .3); alt = ys_.max(); xa, xb = xs_.min(), xs_.max(); D_ = 60
            for yy_ in range(alt + 6, min(H0 - 2, alt + 400)):
                if (G[yy_, xa:xb] < 140).mean() > .3: D_ = yy_ - alt - 2; break
            p["_dus"] = int(max(20, D_))
        DOK[p["ad"]] = dict(t=np.dstack([tex, al[..., None]])[y0:y1, x0:x1].astype(np.float32), k=(x0, y0, x1, y1))
    if GB_IMG is not None:
        arka, BRAP = b_arka(A); globals()["BRAP"] = BRAP
        return A, DOK, arka, np.dstack([ref, cv2.GaussianBlur(ON.astype(np.float32) / 255, (0, 0), .8)[..., None]])
    # arka plan: dönen parçaların durağan izi temizlenir (önde kalanlar korunur)
    iz = np.zeros((H0, W0), np.uint8)
    for p in T["parcalar"]: iz = np.maximum(iz, cv2.dilate((A[p["ad"]] > .05).astype(np.uint8) * 255, np.ones((5, 5), np.uint8)))
    iz[ON > 128] = 0; arka = ref.copy(); kalan = iz.copy()
    for d in T.get("dolgu", []):
        arka, k = kaydir_doldur(arka, iz, d["kutu"], d["tur"]); x0, y0, x1, y1 = d["kutu"]; kk = np.zeros_like(iz); kk[y0:y1, x0:x1] = k[y0:y1, x0:x1] * 255
        kalan[y0:y1, x0:x1] = kk[y0:y1, x0:x1]
    arka = kagit_doldur(arka, kalan, 3)
    on = np.dstack([ref, cv2.GaussianBlur(ON.astype(np.float32) / 255, (0, 0), .8)[..., None]])
    kagit = kagit_doldur(np.zeros((H, W, 3), np.float32), np.full((H, W), 255, np.uint8), 11) if False else None
    return A, DOK, arka, on

def b_arka(A):
    """İKİ GÖRSEL: arka plan = (a), hareketli parçaların durgun yeri (+7 px) ve ip bandı (b)'den. (b) önce bütünüyle, sonra her parçanın
    çevresinde ayrı faz korelasyonuyla (a)'ya hizalanır (parça yeri iki görselde de maskelenir); kâğıt tonu yerel haritayla (a)'ya eşitlenir."""
    ref = REF.astype(np.float32); B = GB_IMG.astype(np.float32)
    if B.shape[:2] != (H0, W0): B = cv2.resize(B, (W0, H0), interpolation=cv2.INTER_AREA)
    ell = lambda k: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)); BOL = []
    for p in T["parcalar"]: BOL.append((p["ad"], cv2.dilate((A[p["ad"]] > .05).astype(np.uint8) * 255, ell(7))))
    for ip in T.get("ipler", []): BOL.append((ip["ad"], cv2.dilate(IPM[ip["ad"]], ell(3))))
    R = np.max([b for _, b in BOL], 0); delik = cv2.dilate(R, ell(12)) > 0
    ga = np.where(delik, 0, 255 - G).astype(np.float32); _gB = cv2.cvtColor(B.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32); gb = np.where(delik, 0, _gB if INV else 255 - _gB).astype(np.float32)
    (gx, gy), gr = cv2.phaseCorrelate(ga, gb, cv2.createHanningWindow((W0, H0), cv2.CV_32F)); rap = [f"(b) genel kayma {gx:+.1f}, {gy:+.1f} px (güven {gr:.2f})"]
    yk = REF[G > 200].reshape(-1, 3).mean(0) if (G > 200).sum() > 1000 else np.array([184, 217, 232], np.float32)
    gbg = cv2.cvtColor(B.astype(np.uint8), cv2.COLOR_BGR2GRAY)
    if INV: gbg = 255 - gbg
    KA = kagit_haritasi(ref, delik.astype(np.uint8), yk); KB = np.where(True, 0, 0)
    w = ((gbg > 192) & ~delik).astype(np.float32); num = cv2.GaussianBlur(B * w[..., None], (0, 0), 22); den = cv2.GaussianBlur(w, (0, 0), 22)[..., None]
    KB = np.where(den > 1e-3, num / np.maximum(den, 1e-3), yk); Bt = B + (KA - KB) if not INV else B      # blueprint: iki görsel aynı koddan, ton eşitlemeye gerek yok
    arka = ref.copy()
    for ad, Ri in BOL:
        ys, xs = np.nonzero(Ri); x0, y0, x1, y1 = max(0, xs.min() - 120), max(0, ys.min() - 120), min(W0, xs.max() + 121), min(H0, ys.max() + 121)
        dx, dy, r = gx, gy, 0.
        if x1 - x0 > 64 and y1 - y0 > 64:
            (lx, ly), r = cv2.phaseCorrelate(ga[y0:y1, x0:x1], gb[y0:y1, x0:x1], cv2.createHanningWindow((x1 - x0, y1 - y0), cv2.CV_32F))
            if r > .05 and np.hypot(lx - gx, ly - gy) < 25: dx, dy = lx, ly
        Bs = cv2.warpAffine(Bt, np.float32([[1, 0, -dx], [0, 1, -dy]]), (W0, H0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        a = cv2.GaussianBlur(Ri.astype(np.float32) / 255, (0, 0), 2.)[..., None]; arka = arka * (1 - a) + Bs * a
        rap.append(f"(b) {ad} yerel kayma {dx:+.1f}, {dy:+.1f} px (güven {r:.2f})")
    return arka, rap

# ═════ 2. hareket (n: kalkıştan sonraki kare; dur sonu)
R_K, NS, DG = 44, 300, 115
def hiz(n, uzat=1.):
    if n <= 0: return 0.
    if n < R_K: return n / R_K
    if n <= NS: return 1.
    u = min(1, (n - NS) / (DG * uzat)); return (1 - u) ** 1.5
SMAX = T.get("smax") or (NS + int(DG * max([p["hareket"].get("atalet", 1) for p in T["parcalar"]] or [1])) + 2)
def birikim(uzat):
    s = np.zeros(SMAX + 400);
    for n in range(1, len(s)): s[n] = s[n - 1] + hiz(n, uzat) / FPS
    return s
S1 = birikim(1.)
def aci(ad, n, kok=None):
    p = P[ad]; h = p["hareket"]; nn = int(np.clip(n, 0, len(S1) - 1)); s = S1[nn]
    if h["tur"] == "donme": return 2 * np.pi * h["hiz"] * s
    if h["tur"] == "bagli": return aci(h["parca"], n) * h["oran"]
    if h["tur"] == "ip_sarma": return COZ.davul_aci(h["ip"], n)
    if h["tur"] == "esapman":
        f = 2 * s / h["periyot"]; k = np.floor(f); return 2 * np.pi / p["Z"] * (k + sio((f - k) / .12))
    if h["tur"] == "dusme":                     # top: periyot başında belirir, yerçekimiyle düşer, küçük sıçrar, oturur, söner
        D_ = p.get("_dus", 80); per = h.get("periyot", 4.0); u = (s % per) / per * per * FPS; T1 = np.sqrt(2 * D_ / (D_ * 2 / (11.5 ** 2)))
        g = 2 * D_ / T1 ** 2; v1 = g * T1 * .27; T2 = 2 * v1 / g; al = float(np.clip(u / 6, 0, 1) * (1 - np.clip((u - per * FPS * .8) / 10, 0, 1)))
        if n <= 0: return (0., 1.)
        if u < T1: dy = .5 * g * u * u
        elif u < T1 + T2: q_ = u - T1; dy = D_ - (v1 * q_ - .5 * g * q_ * q_)
        else: dy = D_
        return (float(dy), al)
    if h["tur"] == "salinim":
        at = h.get("atalet", 1)
        if at == 1: return np.radians(h["genlik"]) * np.sin(np.pi * 2 * s / h["periyot"]) * hiz(nn)
        t = max(n, 0) / FPS; return np.radians(h["genlik"]) * np.sin(2 * np.pi * t / h["periyot"]) * hiz(nn, at)
    return 0.
NSON = SMAX + 60                                 # durduktan sonra folio + 1,5 sn sakin
COZ = MEK.Cozucu(T, aci, SMAX + 400)             # genel kinematik çözücü (şekil parçaları, ipler)
IPS = {}
for _ip in T.get("ipler", []): IPS.setdefault(_ip["sonra"], []).append(_ip)
IPM = {}
for _ip in T.get("ipler", []):                   # ipin durgun bandı (görseldeki ip): arka plan (b)'den, alttaki parça simetriyle
    _Pp, _ = COZ.ip_yolu(_ip["ad"], 0); _m = np.zeros((H0, W0), np.uint8); cv2.polylines(_m, [np.int32(_Pp)], False, 255, int(_ip.get("bant", 11)), cv2.LINE_AA); IPM[_ip["ad"]] = _m

def sekil_bas(img, p, n):
    d = DOK[p["ad"]]; x0, y0, x1, y1 = d["k"]; M, al = COZ.poz(p["ad"], n)
    if al <= 0: return
    Q = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float) @ M[:, :2].T + M[:, 2]
    X0, Y0 = np.maximum(0, np.floor(Q.min(0)).astype(int) - 1); X1, Y1 = np.ceil(Q.max(0)).astype(int) + 1; X1, Y1 = min(W0, X1), min(H0, Y1)
    if X1 <= X0 or Y1 <= Y0: return
    M2 = M.copy(); M2[:, 2] = M[:, 2] + M[:, :2] @ np.array([x0, y0]) - np.array([X0, Y0])
    w = cv2.warpAffine(d["t"], M2, (int(X1 - X0), int(Y1 - Y0)), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    a = w[..., 3:] * al; img[Y0:Y1, X0:X1] = img[Y0:Y1, X0:X1] * (1 - a) + w[..., :3] * a

def ip_ciz(img, ip, n):
    """ip: davuldan kancaya bükülmüş iki ince çizgi + çapraz bükülme izleri (mürekkep); boşalınca parabolik sarkar."""
    Pp, E = COZ.ip_yolu(ip["ad"], n)
    s0 = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Pp, axis=0).T))]); Pp = np.stack([np.interp(np.arange(0, s0[-1], 3), s0, Pp[:, i]) for i in (0, 1)], 1)
    dv = np.gradient(Pp, axis=0); dv /= np.hypot(*dv.T)[:, None] + 1e-9; nr = np.stack([-dv[:, 1], dv[:, 0]], 1); k = ip.get("kalinlik", 3) / 2
    m = np.zeros((H0, W0), np.uint8)
    for s_ in (-k, k): cv2.polylines(m, [np.int32((Pp + nr * s_) * 4)], False, 235, 1, cv2.LINE_AA, 2)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Pp, axis=0).T))]); ph = (n * 0 + 0)
    for t in np.arange(4, s[-1] - 2, 7):
        i = int(np.searchsorted(s, t)); i = min(i, len(Pp) - 1); q = Pp[i]; a_, b_ = q + nr[i] * k - dv[i] * 2, q - nr[i] * k + dv[i] * 2
        cv2.line(m, tuple(np.int32(a_ * 4)), tuple(np.int32(b_ * 4)), 200, 1, cv2.LINE_AA, 2)
    if ip.get("kanca", True): cv2.circle(m, tuple(np.int32(E * 4)), 4 * 5, 220, 1, cv2.LINE_AA, 2)
    a = (m.astype(np.float32) / 255)[..., None]; img[:] = img * (1 - a) + np.array([22, 39, 58], np.float32) * a

KIRMIZI, SEPYA = np.array([42, 64, 164], np.float32), np.array([22, 39, 58], np.float32)
def _boya(img, m, renk, al):
    a = (m.astype(np.float32) / 255 * al)[..., None]; img[:] = img * (1 - a) + renk * a
def isaret_ciz(img, n):
    """ders işaretleri (yazısız): kırmızı kuvvet okları, soluk ölçü çubukları (çentikli), uç yayları. Kalkıştan sonra 0,8 sn'de belirir."""
    al = float(sio(ara(n, 0, 25)))
    if al <= 0 or not T.get("isaretler"): return
    for e in T["isaretler"]:
        m = np.zeros((H0, W0), np.uint8); S4 = lambda p: tuple(np.int32(np.round(np.asarray(p) * 4)))
        if e["tur"] == "ok":
            p = COZ.nokta(e["parca"], e["nokta"], n); u = np.asarray(e["yon"], float); q = p + u * e["boy"]
            cv2.line(m, S4(p), S4(q), 255, 4, cv2.LINE_AA, 2)
            for sg in (-1, 1):
                c_, s_ = np.cos(sg * .45), np.sin(sg * .45); v = -u; w_ = np.array([c_ * v[0] - s_ * v[1], s_ * v[0] + c_ * v[1]]); cv2.line(m, S4(q), S4(q + w_ * 15), 255, 4, cv2.LINE_AA, 2)
            _boya(img, m, KIRMIZI, .92 * al)
        elif e["tur"] in ("olcu", "olcu_kat"):
            p0 = COZ.nokta(e["parca"], e["nokta"], 0); p = COZ.nokta(e["parca"], e["nokta"], n); x = e["x"]
            if e["tur"] == "olcu": Y = [p0[1], p[1]]
            else: d = p0[1] - p[1]; Y = [e["y0"] + k * d for k in range(e["kat"] + 1)]
            if abs(Y[-1] - Y[0]) < 1: continue
            cv2.line(m, S4((x, Y[0])), S4((x, Y[-1])), 255, 2, cv2.LINE_AA, 2)
            for y in Y: cv2.line(m, S4((x - 7, y)), S4((x + 7, y)), 255, 2, cv2.LINE_AA, 2)
            _boya(img, m, SEPYA, .6 * al)
        elif e["tur"] == "yay":
            c = np.asarray(e["pivot"], float); q0 = np.asarray(e["nokta"], float); q = COZ.nokta(e["parca"], e["nokta"], n); r = np.hypot(*(q0 - c))
            a0, a1 = np.arctan2(*(q0 - c)[::-1]), np.arctan2(*(q - c)[::-1]); a1 = a0 + (a1 - a0 + np.pi) % (2 * np.pi) - np.pi
            if abs(a1 - a0) * r < 1: continue
            aa = np.linspace(a0, a1, 60); Pp = np.stack([c[0] + r * np.cos(aa), c[1] + r * np.sin(aa)], 1)
            cv2.polylines(m, [np.int32(Pp * 4)], False, 255, 3, cv2.LINE_AA, 2)
            for a_ in (a0, a1): u = np.array([np.cos(a_), np.sin(a_)]); cv2.line(m, S4(c + u * (r - 11)), S4(c + u * (r + 11)), 255, 3, cv2.LINE_AA, 2)
            _boya(img, m, KIRMIZI, .85 * al)

def merkez_maskesi():
    """blueprint merkez çizgileri: yeri sabit dönme eksenleri (dişli, sabit makara, kaldıraç pivotu), kesik-noktalı yatay + düşey"""
    m = np.zeros((H0, W0), np.uint8)
    for p in T["parcalar"]:
        h = p["hareket"]; c = None
        if h["tur"] in ("donme", "bagli", "esapman", "ip_sarma") and "c" in p: c, R = p["c"], p["r"] * 1.12 + 18
        elif h["tur"] == "anahtar": c, R = h["pivot"], 58
        elif h["tur"] == "dogrusal" and not any(h.get("oteleme", [0, 0])) and "c" in p: c, R = p["c"], p.get("r", 70) * 1.12 + 18
        if c is None: continue
        for u in ((1, 0), (0, 1)):
            t = -R
            while t < R:
                for a_, b_ in ((t, min(R, t + 20)), (t + 24, min(R, t + 26))):
                    if a_ < R: cv2.line(m, (int((c[0] + u[0] * a_) * 4), int((c[1] + u[1] * a_) * 4)), (int((c[0] + u[0] * b_) * 4), int((c[1] + u[1] * b_) * 4)), 255, 1, cv2.LINE_AA, 2)
                t += 30
    return m
MCM = merkez_maskesi() if INV else None

def bilestir(arka, on, DOK, n, isaret=True):
    img = arka.copy()
    for p in T["parcalar"]:
        if p["tur"] == "sekil":
            sekil_bas(img, p, n)
            for ip in IPS.get(p["ad"], []): ip_ciz(img, ip, n)
            continue
        d = DOK[p["ad"]]; x0, y0, x1, y1 = d["k"]; M = donusum(p, aci(p["ad"], n)).copy()
        if M.shape == (2, 3) and d["t"].shape[0] < y1 - y0: pass
        M[:, 2] += M[:, :2] @ np.array([x0, y0]) - np.array([x0, y0])
        th = aci(p["ad"], n); al = th[1] if isinstance(th, tuple) else 1.
        if isinstance(th, tuple): y1 = min(H0, y1 + int(p.get("_dus", 80)) + 4)
        w = cv2.warpAffine(d["t"], M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        a = w[..., 3:] * al; img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + w[..., :3] * a
        for ip in IPS.get(p["ad"], []): ip_ciz(img, ip, n)
    if INV: a_ = (MCM.astype(np.float32) / 255 * .7)[..., None]; img[:] = img * (1 - a_) + np.array([255, 208, 159], np.float32) * a_
    if isaret:
        isaret_ciz(img, n)
        if DERS_OGE:
            import ders as _ders
            for o in DERS_OGE: _ders.bas(img, o, n)
    return img * (1 - on[..., 3:]) + on[..., :3] * on[..., 3:]

def genis(img, kagit):
    sc = cv2.resize(img, (int(round(W0 * SC)), H), interpolation=cv2.INTER_AREA); out = kagit.copy(); x0 = int(round(OX)); r = 40
    a = np.ones(sc.shape[1], np.float32); a[:r] = np.linspace(0, 1, r); a[-r:] = np.linspace(1, 0, r)
    out[:, x0:x0 + sc.shape[1]] = out[:, x0:x0 + sc.shape[1]] * (1 - a[None, :, None]) + sc * a[None, :, None]; return out

# ═════ 3. oluşum: iskelet -> kalem yolları -> zaman haritası (iskelet_v4 yöntemi)
def zhang_suen(I):
    I = I.astype(np.uint8).copy()
    while True:
        deg = False
        for st in (0, 1):
            Pd = np.pad(I, 1); p2, p3, p4, p5 = Pd[:-2, 1:-1], Pd[:-2, 2:], Pd[1:-1, 2:], Pd[2:, 2:]; p6, p7, p8, p9 = Pd[2:, 1:-1], Pd[2:, :-2], Pd[1:-1, :-2], Pd[:-2, :-2]
            B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9; s = [p2, p3, p4, p5, p6, p7, p8, p9, p2]; A = sum(((s[i] == 0) & (s[i + 1] == 1)).astype(np.uint8) for i in range(8))
            c = ((p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)) if st == 0 else ((p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0))
            m = (I == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if m.any(): I[m] = 0; deg = True
        if not deg: return I
def olusum_hazirla(M0, etiket):
    g = cv2.cvtColor(M0.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY); h, w = g.shape
    ink = (g < 128).astype(np.uint8); ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(ink, 8); ink[np.isin(lab, np.where(st[:, 4] < 12)[0])] = 0
    S = zhang_suen(ink); K8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    kom = cv2.filter2D(S, -1, np.ones((3, 3), np.float32), borderType=cv2.BORDER_CONSTANT) - S; dug = (S == 1) & (kom != 2); gez = np.zeros_like(S, bool); Y = []
    def izle(y, x):
        Q = [(x, y)]; gez[y, x] = True
        while True:
            il = None
            for dy, dx in K8:
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and S[yy, xx] and not gez[yy, xx]: il = (yy, xx); break
            if il is None: return Q
            y, x = il; Q.append((x, y))
            if dug[y, x]: return Q
            gez[y, x] = True
    for y, x in zip(*np.nonzero(dug)):
        gez[y, x] = True
        for dy, dx in K8:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and S[yy, xx] and not gez[yy, xx]: Y.append([(x, y)] + izle(yy, xx))
    for y, x in zip(*np.nonzero((S == 1) & ~gez)): Y.append(izle(y, x))
    # kavşakta düz devam eden yolları birleştir (uçları değen)
    dl = cv2.connectedComponents(cv2.dilate(dug.astype(np.uint8), np.ones((3, 3), np.uint8)), 8)[1]
    ud = lambda Q, son: int(dl[(Q[-1] if son else Q[0])[1], (Q[-1] if son else Q[0])[0]])
    def yon(Q, son): Z = np.array(Q[-7:] if son else Q[:7][::-1], float); v = Z[-1] - Z[0]; return v / (np.hypot(*v) + 1e-9)
    kmap = {}
    for i, Q in enumerate(Y):
        for son in (0, 1):
            d = ud(Q, son)
            if d: kmap.setdefault(d, []).append((i, son))
    kul = np.zeros(len(Y), bool); Z = []
    for i in np.argsort([-len(Q) for Q in Y]):
        if kul[i]: continue
        kul[i] = True; C = list(Y[i])
        for yn in (1, 0):
            while True:
                Q = C if yn else C[::-1]; d = ud(Q, 1)
                if not d: break
                v = yon(Q, 1); en, ad_ = None, -1
                for j, sj in kmap.get(d, []):
                    if kul[j]: continue
                    q = Y[j][-1] if sj else Y[j][0]
                    if abs(q[0] - Q[-1][0]) > 3 or abs(q[1] - Q[-1][1]) > 3: continue
                    c = float(v @ -yon(Y[j], sj))
                    if c > .6 and c > ad_: en, ad_ = (j, sj), c
                if en is None: break
                j, sj = en; kul[j] = True; Q = Q + (Y[j][::-1] if sj else Y[j])[1:]; C = Q if yn else Q[::-1]
        Z.append(C)
    yol = []
    for Q in Z:
        A_ = np.array(Q, float); L = float(np.hypot(*np.diff(A_, axis=0).T).sum()) if len(Q) > 1 else 0
        if L < 5: continue
        B = ndimage.uniform_filter1d(A_, 5, axis=0) if len(A_) > 6 else A_; dv = np.diff(B[::3], axis=0); an = np.arctan2(dv[:, 1], dv[:, 0]) if len(dv) > 1 else np.zeros(1)
        don = float(np.abs((np.diff(an) + np.pi) % (2 * np.pi) - np.pi).sum()) / max(L, 1) if len(an) > 1 else 0
        tur = "kontur" if (L >= 60 and don < .06) or (L >= 140 and don < .09) else "tara"
        mx, my = A_.mean(0); rx, ry = int(np.clip((mx - OX) / SC, 0, W0 - 1)), int(np.clip(my / SC, 0, H0 - 1))
        yol.append(dict(P=A_[::2] if len(A_) > 3 else A_, L=L, tur=tur, parca=etiket[ry, rx]))
    sira = T.get("olusum_sirasi") or sorted({y["parca"] for y in yol})
    sira += [s for s in {y["parca"] for y in yol} if s not in sira]
    def zincir(L, bas):
        kal = list(range(len(L))); out = []; p = np.array(bas, float); U = np.array([[*L[i]["P"][0], *L[i]["P"][-1]] for i in range(len(L))], float) if L else np.zeros((0, 4))
        while kal:
            k = np.array(kal); d0 = np.hypot(*(U[k, :2] - p).T); d1 = np.hypot(*(U[k, 2:] - p).T); j = int(np.argmin(np.minimum(d0, d1))); i = kal.pop(j); y = L[i]
            if d1[j] < d0[j]: y["P"] = y["P"][::-1]
            y["atla"] = float(min(d0[j], d1[j])); out.append(y); p = np.array(y["P"][-1], float)
        return out, p
    kon, tar, kb = [], [], (W / 2, H / 2)
    def _tarali(y):                                   # blueprint kesit taraması: düz, 45° (ya da 225°) eğimli vuruş
        d_ = y["P"][-1] - y["P"][0]; a_ = np.degrees(np.arctan2(d_[1], d_[0])) % 180; return abs(a_ - 45) < 9 and np.hypot(*d_) > .9 * y["L"]
    for pc in sira:
        K_ = [y for y in yol if y["tur"] == "kontur" and y["parca"] == pc]
        if INV:                                       # plotter: parçanın konturu, hemen ardından kendi taraması
            z, kb = zincir([y for y in K_ if not _tarali(y)], kb); kon += z; z, kb = zincir([y for y in K_ if _tarali(y)], kb); kon += z
        else: z, kb = zincir(K_, kb); kon += z
    sure = []
    for y in kon:
        Pp = y["P"]; duz = np.hypot(*(Pp[-1] - Pp[0])) / max(y["L"], 1); v = 400 * (.45 + .9 * duz ** 2) * (1 + min(y["L"], 300) / 300); sure.append((y["L"] / v, y["atla"] / 2400))
    k = 9.1 * OK_ / sum(a + b for a, b in sure); t = .9 * OK_
    for y, (a, b) in zip(kon, sure): t += b * k; y["t0"] = t; t += a * k; y["t1"] = t
    pboy = {pc: sum(y["L"] for y in yol if y["tur"] == "tara" and y["parca"] == pc) for pc in sira}; TB = sum(pboy.values()) or 1; t = 9.8 * OK_
    for pc in sira:
        L = [y for y in yol if y["tur"] == "tara" and y["parca"] == pc]
        if not L: continue
        z, _ = zincir(L, (W / 2, H / 2)); dur = 3.8 * OK_ * pboy[pc] / TB; hz = sum(y["L"] for y in z) / (dur * 6); ser = [t] * 6
        for y in z: kk = int(np.argmin(ser)); y["t0"] = ser[kk]; y["t1"] = ser[kk] + y["L"] / hz; ser[kk] = y["t1"]
        tar += z; t += dur
    def harita(L):
        Zm = np.full((h, w), np.nan, np.float32)
        for y in L:
            Pp = np.round(y["P"]).astype(int); nn = len(Pp); Zm[Pp[:, 1], Pp[:, 0]] = y["t0"] + (y["t1"] - y["t0"]) * np.arange(nn) / max(nn - 1, 1)
        if np.isnan(Zm).all(): return np.full((h, w), 13.6 * OK_, np.float32), np.full((h, w), 99.)
        uz, (iy, ix) = ndimage.distance_transform_edt(np.isnan(Zm), return_indices=True); return Zm[iy, ix], uz
    Zk, dk = harita(kon); Zt, dt = harita(tar)
    Zmap = np.where(dk <= 2.5, Zk + .1, Zt + .1 + .2 * np.clip(dt / 14, 0, 1)).astype(np.float32)
    for y in kon + tar:
        Pp = y["P"]; nn = len(Pp) - 1; Wd = 2.1 if y["tur"] == "kontur" else 1.3
        a = np.roll(Pp, 1, 0); b = np.roll(Pp, -1, 0); a[0] = Pp[0]; b[-1] = Pp[-1]; dv = b - a; dv /= (np.hypot(*dv.T)[:, None] + 1e-9)
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Pp, axis=0).T))]); u = s / max(s[-1], 1e-6)
        wd = Wd * (.28 + .72 * np.sin(np.pi * np.minimum(1, u * 1.15)) ** .55) * (1 + .16 * np.sin(s / 26 + len(Pp))) / 2
        nrm = np.stack([-dv[:, 1], dv[:, 0]], 1); y["sol"] = Pp + nrm * wd[:, None]; y["sag"] = Pp - nrm * wd[:, None]
    return kon + tar, Zmap, dict(kontur=len(kon), tarama=len(tar), iskelet=int(S.sum()))

def kursun_listesi():
    L = []
    for i, p in enumerate([q for q in T["parcalar"] if "c" in q and "r" in q]):
        c = p["c"]; R = p["r"] * 1.12; th = np.linspace(0, 2 * np.pi, 160)
        L.append((np.stack([OX + (c[0] + R * p["sx"] * np.cos(th)) * SC, (c[1] + R * p["sy"] * np.sin(th)) * SC], 1), (.05 + .07 * i) * OK_))
        L.append((np.array([[OX + (c[0] - R * 1.2) * SC, c[1] * SC], [OX + (c[0] + R * 1.2) * SC, c[1] * SC]]), (.1 + .07 * i) * OK_))
        L.append((np.array([[OX + c[0] * SC, (c[1] - R * 1.2) * SC], [OX + c[0] * SC, (c[1] + R * 1.2) * SC]]), (.12 + .07 * i) * OK_))
    return L
def kes(Pp, f):
    if f >= 1: return Pp
    n = max(2, int(round(f * (len(Pp) - 1))) + 1); return Pp[:n]

# ═════ 4. kırmızı kuvvet yolu + harfler + folio
def catmull(N, k=10):
    N = np.array(N, float); o = [N[0]]
    for i in range(len(N) - 1):
        p0, p1, p2, p3 = N[max(0, i - 1)], N[i], N[i + 1], N[min(len(N) - 1, i + 2)]
        for j in range(1, k + 1):
            u = j / k; o.append(.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return np.array(o)
def yazi(metin, boy, renk, al):
    f = ImageFont.truetype(os.path.join(D, "font", "IMFeENit28P.ttf"), boy); b = f.getbbox(metin); im = Image.new("RGBA", (b[2] - b[0] + 8, b[3] - b[1] + 12), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - b[0], 4 - b[1]), metin, font=f, fill=(*renk, int(255 * al))); a = np.array(im).astype(np.float32); return a[..., [2, 1, 0, 3]]
def bas(img, spr, x, y, al=1.):
    h, w = spr.shape[:2]; x0, y0 = int(x - w / 2), int(y - h / 2); a = spr[..., 3:] / 255 * al
    img[y0:y0 + h, x0:x0 + w] = img[y0:y0 + h, x0:x0 + w] * (1 - a) + spr[..., :3] * a

def kamera(img, n):
    if not T.get("yakinlasma"): return img
    x, y, s = T["yakinlasma"]; z0, z1, z2, z3 = ZMN.get("yakin", [R_K + 30, R_K + 80, R_K + 150, R_K + 205]); z = float(sio(ara(n, z0, z1)) * (1 - sio(ara(n, z2, z3))))
    if z <= 0: return img
    k = 1 + (s - 1) * z; mx = W / 2 + (OX + x * SC - W / 2) * z; my = H / 2 + (y * SC - H / 2) * z
    return cv2.warpAffine(img, np.float32([[k, 0, W / 2 - k * mx], [0, k, H / 2 - k * my]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def kare_ciz(i):
    g = globals(); OL, MUR, ZM, P0, M0, KUR, YOL, ESK, arka, on, DOK, kag, YOLK, HARF, FOL = (g[k] for k in ('OL', 'MUR', 'ZM', 'P0', 'M0', 'KUR', 'YOL', 'ESK', 'arka', 'on', 'DOK', 'kag', 'YOLK', 'HARF', 'FOL'))
    if i < OL:
        t = i / FPS; GK = float(sio(ara(t, .5 * OK_, 13.6 * OK_))); a = MUR * np.clip((t - ZM) / .25, 0, 1)[..., None] + (1 - MUR) * GK
        P0x = P0 if not INV else P0N + (P0 - P0N) * float(sio(ara(t, 0, .6)))          # blueprint: önce ızgara (plotter)
        img = P0x + (M0 - P0x) * a
        mk = np.zeros((H, W), np.uint8); al_k = 1 - float(sio(ara(t, 11.8 * OK_, 13.8 * OK_)))
        if al_k > 0:
            for Pp, s in KUR:
                u = float(ara(t, s, s + .55 * OK_))
                if u > 0: cv2.polylines(mk, [np.int32(kes(Pp, float(sio(u))) * 4)], False, int(120 * al_k), 1, cv2.LINE_AA, 2)
            img = img * (1 - mk[..., None] / 255) + np.array([235, 190, 140] if INV else [62, 78, 92], np.float32) * (mk[..., None] / 255)
        mk = np.zeros((H, W), np.uint8); uc = None
        for y in YOL:
            if t < y["t0"] or t > y["t1"] + .6: continue
            f = min(1, (t - y["t0"]) / max(y["t1"] - y["t0"], 1e-3)); op = 1 - min(1, max(0, (t - y["t1"] - .15) / .45))
            k = max(1, int(round(f * (len(y["P"]) - 1)))); pts = np.vstack([y["sol"][:k + 1], y["sag"][:k + 1][::-1]])
            cv2.fillPoly(mk, [np.int32(pts * 4)], int(230 * op), cv2.LINE_AA, 2)
            if f < 1: uc = y["P"][k]
        img = img * (1 - mk[..., None] / 255) + np.array([255, 246, 236] if INV else [14, 26, 40], np.float32) * (mk[..., None] / 255)
        if uc is not None:
            cv2.line(img, (int(uc[0] + 2), int(uc[1] - 2)), (int(uc[0] + 28), int(uc[1] - 42)), (22, 40, 60), 1, cv2.LINE_AA); cv2.circle(img, (int(uc[0]), int(uc[1])), 2, (10, 20, 30), -1, cv2.LINE_AA)
        img = img * ESK
    else:
        n = i - OL; img = genis(bilestir(arka, on, DOK, n), kag)
        if YOLK is not None:
            y0_, y1_ = ZMN.get("yol", [R_K + 40, R_K + 128]); ciz = float(ara(n, y0_, y1_)) if isinstance(T.get("kuvvet_yolu"), str) else float(sio(ara(n, y0_, y1_)))
            if ciz > 0:
                Pp = np.stack([OX + YOLK[:, 0] * SC, YOLK[:, 1] * SC], 1); k = max(2, int(ciz * (len(Pp) - 1)) + 1); mk = np.zeros((H, W), np.uint8)
                cv2.polylines(mk, [np.int32(Pp[:k] * 4)], False, 215, 3, cv2.LINE_AA, 2)
                a_, b_ = Pp[k - 1], Pp[max(0, k - 4)]; an = np.arctan2(a_[1] - b_[1], a_[0] - b_[0])
                for sg in (-1, 1): cv2.line(mk, tuple(np.int32(a_ * 4)), tuple(np.int32((a_ - 13 * np.array([np.cos(an + sg * .45), np.sin(an + sg * .45)])) * 4)), 215, 3, cv2.LINE_AA, 2)
                img = img * (1 - mk[..., None] / 255) + np.array([28, 40, 148], np.float32) * (mk[..., None] / 255)
                for spr, x, y, j in HARF:
                    al = float(ara(ciz * (len(YOLK) - 1), j, j + 6))
                    if al > 0: bas(img, spr, x, y, al)
        img = kamera(img * ESK, n)
        fa = float(sio(ara(n, SMAX - 10, SMAX + 12)))
        if fa > 0 and not INV: bas(img, FOL, 1730, 1015, fa)                    # blueprint: folyo yerine başlık bloğu (görselde)
    return img.clip(0, 255).astype(np.uint8)

def parca_ciz(ara_):                             # bir çekirdeğin işi: [a, b) kareleri -> kendi mp4 parçası (+ kontrol kareleri, fark, özet)
    import hashlib
    a, b, yol = ara_; KONT = globals()["KONT"]
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "medium", "-threads", "2", yol], stdin=subprocess.PIPE)
    kare, fark, ozet, onceki = {}, [], [], None
    for i in range(a, b):
        o = kare_ciz(i); ff.stdin.write(o.tobytes()); ozet.append(hashlib.md5(o.tobytes()).hexdigest())
        if onceki is not None and i % 3 == 0: fark.append((float(np.abs(o.astype(np.int16) - onceki).mean()), i))
        onceki = o.astype(np.int16)
        if i in KONT: kare[i] = o
    ff.stdin.close(); ff.wait(); return kare, fark, ozet

if __name__ == "__main__":
    os.makedirs(os.path.join(D, "cikti"), exist_ok=True); C = os.path.join(D, "cikti", AD + "-v4")
    adim("başla")
    A, DOK, arka, on = hazirla(); adim("melez katmanlar (dokular, arka plan temizliği, ön maske)")
    if T.get("ders"):                                # anlatım planı: adımlar sırayla; palangada kaldırma anı plandan
        import ders
        ders.stil_ayarla(STIL); _O, PLAN = ders.kur(T, COZ, SEVIYE, VARYANT); DERS_OGE[:] = _O
        t_son, OLAY = ders.sirala(DERS_OGE, PLAN["bas"])
        if "kaldirma_adim" in PLAN:
            t5 = next(t for a_, t, _ in OLAY if a_ == PLAN["kaldirma_adim"]); KS = 120
            T["suruculer"]["d"] = [[0, 0], [t5, 0], [t5 + KS, T["ders"]["dmax"]]]; COZ._m.clear()
            for _o in DERS_OGE: _o.vurgu = []
            t_son, OLAY = ders.sirala(DERS_OGE, PLAN["bas"], {PLAN["yol_adim"]: t5 + KS + 6})
        SMAX = max(SMAX, t_son + 45); NSON = SMAX + 60
    if INV:
        import blueprint as BP
        _z, _g = BP.zemin(W, H, OX, 0., SC); P0N = _z.astype(np.float32); kag = (_z * (1 - _g[..., None]) + BP.IZGARA * _g[..., None]).astype(np.float32)
    else: kag = kagit_doldur(np.zeros((H, W, 3), np.float32), np.full((H, W), 255, np.uint8), 11); P0N = kag
    rng = np.random.default_rng(4); e = np.ones((H, W, 3), np.float32); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    kd = np.minimum.reduce([xx, W - xx, yy, H - yy]); e *= 1 - (np.clip(1 - kd / 160, 0, 1) ** 2)[..., None] * np.array([.10, .06, .02])
    for _ in range(7):
        cx_, cy_, r_ = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(60, 220); b = np.exp(-(((xx - cx_) / r_) ** 2 + ((yy - cy_) / (r_ * rng.uniform(.5, 1.2))) ** 2))
        e *= 1 - (b * rng.uniform(.025, .05))[..., None] * np.array([.8, .55, .25])
    ESK = cv2.GaussianBlur(e, (0, 0), 1.0)
    if INV: ESK = (1 - (np.clip(1 - kd / 260, 0, 1) ** 2)[..., None] * .18 * np.ones(3)).astype(np.float32)   # blueprint: yalnız hafif kenar kararması
    adim("kâğıt + eskime")
    # kavrama denetimi: tanımda Z'si olan ve birbirine değen dişli çiftleri, 120 karede binen piksel
    rap = []
    dis = [p for p in T["parcalar"] if p["tur"] == "disli"]
    for i in range(len(dis)):
        for j in range(i + 1, len(dis)):
            p, q = dis[i], dis[j]
            if np.hypot(p["c"][0] - q["c"][0], p["c"][1] - q["c"][1]) > p["r"] + q["r"]: continue
            en = 0
            for n in range(0, 240, 4):
                m = []
                for z in (p, q):
                    d = DOK[z["ad"]]; x0, y0, x1, y1 = d["k"]; M = donusum(z, aci(z["ad"], n + R_K)).copy(); M[:, 2] += M[:, :2] @ np.array([x0, y0]) - np.array([x0, y0])
                    w_ = np.zeros((H0, W0), np.float32); w_[y0:y1, x0:x1] = cv2.warpAffine(d["t"][..., 3], M, (x1 - x0, y1 - y0)); m.append(w_ > .5)
                en = max(en, int((m[0] & m[1]).sum()))
            rap.append(f"kavrama {p['ad']}-{q['ad']}: 60 karede en çok {en} px binme")
    for i in range(len(T["parcalar"])):             # genel çakışma denetimi (şekil parçaları dahil): binme sırası tanımda, burada yalnız ölçülür
        for j in range(i + 1, len(T["parcalar"])):
            p, q = T["parcalar"][i], T["parcalar"][j]
            if p["tur"] == "disli" and q["tur"] == "disli": continue
            if "sekil" not in (p["tur"], q["tur"]): continue
            en = (0, 0)
            for n in range(0, SMAX, 6):
                m = []
                for z in (p, q):
                    if z["tur"] != "sekil":
                        d = DOK[z["ad"]]; x0, y0, x1, y1 = d["k"]; M = donusum(z, aci(z["ad"], n)).copy(); M[:, 2] += M[:, :2] @ np.array([x0, y0]) - np.array([x0, y0])
                        a_ = np.zeros((H0, W0), np.float32); a_[y0:y1, x0:x1] = cv2.warpAffine(d["t"][..., 3], M, (x1 - x0, y1 - y0)); m.append(a_ > .5)
                    else:
                        d = DOK[z["ad"]]; t4 = d["t"].copy(); t4[..., :3] = 255; dd_ = dict(t=t4, k=d["k"]); DOK[z["ad"]], sak = dd_, d
                        w_ = np.zeros((H0, W0, 3), np.float32); sekil_bas(w_, z, n); DOK[z["ad"]] = sak; m.append(w_[..., 0] > 127)
                k_ = int((m[0] & m[1]).sum())
                if k_ > en[0]: en = (k_, n)
            rap.append(f"çakışma {p['ad']}-{q['ad']} (önde {q['ad']}): en çok {en[0]} px (kare +{en[1]})")
    rap += globals().get("BRAP", [])
    def tam_alfa(p, n):                             # parçanın n. karedeki tam kare alfa maskesi
        d = DOK[p["ad"]]; x0, y0, x1, y1 = d["k"]; a_ = np.zeros((H0, W0), np.float32)
        if p["tur"] == "sekil":
            t4 = d["t"].copy(); t4[..., :3] = 255; sak = DOK[p["ad"]]; DOK[p["ad"]] = dict(t=t4, k=d["k"]); w_ = np.zeros((H0, W0, 3), np.float32); sekil_bas(w_, p, n); DOK[p["ad"]] = sak; return w_[..., 0] > 76
        M = donusum(p, aci(p["ad"], n)).copy(); M[:, 2] += M[:, :2] @ np.array([x0, y0]) - np.array([x0, y0]); a_[y0:y1, x0:x1] = cv2.warpAffine(d["t"][..., 3], M, (x1 - x0, y1 - y0)); return a_ > .3
    _fh, _fw = 34 * 1.4 / SC, 120 / SC; FOLK = (int((1730 - OX) / SC - _fw / 2 - 30), int(1015 / SC - _fh / 2 - 10), int((1730 - OX) / SC + _fw / 2 + 10), int(1015 / SC + _fh / 2 + 10))
    for p in T["parcalar"]:                          # folyo ile parça (mancınıkta taş) çakışması
        en = 0
        for n in range(0, SMAX + 60, 3):
            if n < SMAX - 10: continue
            a_ = tam_alfa(p, n); en = max(en, int(a_[max(0, FOLK[1]):FOLK[3], max(0, FOLK[0]):min(W0, FOLK[2])].sum()))
        rap.append(f"folyo çakışması {p['ad']}: {en} px")
    if T.get("ders"):
        KAR = list(range(0, SMAX + 60, 6))
        _ag = arka @ np.array([.114, .587, .299], np.float32)
        govde_m = cv2.dilate(((_ag > 160) if INV else (_ag < 140)).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        if INV: govde_m |= MCM > 60
        temel = {}
        for n in KAR:
            m_ = np.zeros((H0, W0), bool); ipm = np.zeros((H0, W0), bool)
            for ip in T.get("ipler", []): _m = np.zeros((H0, W0), np.uint8); cv2.polylines(_m, [np.int32(COZ.ip_yolu(ip["ad"], n)[0])], False, 1, 7); ipm |= _m > 0
            if n >= SMAX - 10: m_[max(0, FOLK[1]):FOLK[3], max(0, FOLK[0]):min(W0, FOLK[2])] = True
            m_[:, :45] = True; m_[:, -45:] = True; m_[:24] = True; m_[-24:] = True     # görsel kenarı kâğıda karışır: yazı kenardan 45 px içeride
            temel[n] = (m_, ipm, {p["ad"]: tam_alfa(p, n) for p in T["parcalar"]})
        _tc = {}
        def TEMEL(o):
            k_ = frozenset(o.muaf)
            if k_ not in _tc:
                _tc[k_] = {n: temel[n][0] | (govde_m if "govde" not in k_ else False) | (temel[n][1] if "ip" not in k_ else False) | np.any([v for k, v in temel[n][2].items() if k not in k_] or [np.zeros((H0, W0), bool)], 0) for n in KAR}
            return _tc[k_]
        ders.yerlestir(DERS_OGE, TEMEL, KAR, H0, W0, rap); del temel, _tc
        ders.yol_denetimi(DERS_OGE, PLAN["yol"], SMAX, rap)
        for a_, t_, ads in OLAY: rap.append(f"anlatım adımı {a_}: {(round(430 * OK_) + t_) / FPS:.2f} sn ({t_ / FPS:.2f} sn kalkıştan sonra) -> {', '.join(ads)}")
        for o in sorted(DERS_OGE, key=lambda o: o.n0):
            if o.tur == "yazi": rap.append(f"satır '{o.ad}': {(round(430 * OK_) + o.n0) / FPS:.2f} sn'de başlar, {o.sure / FPS:.1f} sn'de yazılır: {re.sub(r'\[[rcos]\|([^\]]*)\]', r'\1', o.metin).replace(chr(10), ' / ')}")
    adim("kavrama denetimi")
    Mref = bilestir(arka, on, DOK, 0, isaret=False); M0 = genis(Mref, kag)
    FZ = T.get("fizik") or {}
    if FZ.get("tur") == "palanga":                 # ip boyu korunuyor mu, çekilen ip / yük kalkışı = 2,00 mi (çözücünün çizdiği konumlardan)
        Ls, R_ = [], []
        y_c0 = COZ.nokta(FZ["cekilen"][0], FZ["cekilen"][1], 0)[1]; y_y0 = COZ.nokta(FZ["yuk"][0], FZ["yuk"][1], 0)[1]
        for n in range(0, SMAX):
            Pp, _ = COZ.ip_yolu(FZ["ip"], n); Ls.append(float(np.hypot(*np.diff(Pp, axis=0).T).sum()))
            dc = COZ.nokta(FZ["cekilen"][0], FZ["cekilen"][1], n)[1] - y_c0; dy = y_y0 - COZ.nokta(FZ["yuk"][0], FZ["yuk"][1], n)[1]
            if dy > 5: R_.append(dc / dy)
        rap.append(f"FİZİK palanga: ip boyu {min(Ls):.2f}-{max(Ls):.2f} px (oynama {max(Ls) - min(Ls):.2f} px, {SMAX} kare); çekilen ip / yük kalkışı = {np.mean(R_):.4f} (en kötü sapma {np.max(np.abs(np.array(R_) - 2)):.4f}, {len(R_)} kare); makara açısal hızı: sabit 2v/r, hareketli v/r")
    if FZ.get("tur") == "kaldirac":
        c = np.asarray(FZ["pivot"], float); R_, V_ = [], []
        for n in range(0, SMAX):
            s_ = []
            for k in ("uc1", "uc2"):
                q0 = np.asarray(FZ[k], float); q = COZ.nokta(FZ["parca"], q0, n); a = np.arctan2(*(q - c)[::-1]) - np.arctan2(*(q0 - c)[::-1]); a = (a + np.pi) % (2 * np.pi) - np.pi
                s_.append((abs(a) * np.hypot(*(q0 - c)), abs(q[1] - q0[1])))
            if s_[1][0] > 2: R_.append(s_[0][0] / s_[1][0]); V_.append(s_[0][1] / max(s_[1][1], 1e-9))
        L1 = np.hypot(*(np.asarray(FZ["uc1"]) - c)); L2 = np.hypot(*(np.asarray(FZ["uc2"]) - c))
        rap.append(f"FİZİK kaldıraç: kol boyları {L1:.0f}/{L2:.0f} = {L1 / L2:.3f}; yay uzunlukları oranı {np.mean(R_):.4f} (en kötü sapma {np.max(np.abs(np.array(R_) - L1 / L2)):.4f}, {len(R_)} kare); düşey yol oranı {np.mean(V_):.4f}; kuvvet okları F:G = 1:{L1 / L2:.0f}")
    etiket = np.full((H0, W0), "govde", dtype=object)
    for p in T["parcalar"]: etiket[A[p["ad"]] > .3] = p["ad"]
    YOL, ZM, oz = olusum_hazirla(255 - M0 if INV else M0, etiket); KUR = kursun_listesi(); adim(f"iskelet + oluşum planı ({oz})")
    P0 = kag; lm = M0 @ np.array([.114, .587, .299]); lp = P0 @ np.array([.114, .587, .299]); MUR = (np.clip((lm - lp - 12) / 40, 0, 1) if INV else np.clip((lp - lm - 12) / 40, 0, 1))[..., None]
    OL = int(round(430 * OK_))
    if isinstance(T.get("kuvvet_yolu"), str):        # mermi yolu: kuvvet yolu taşın gerçek uçuşu (Leonardo'nun atış eğrisi gibi)
        _q = P[T["kuvvet_yolu"]]; COZ.poz(_q["ad"], _q["hareket"]["birak"] + 1); YOLK = _q["_iz"][:_q["hareket"]["ucus"] + 1, :2].copy()
    else: YOLK = catmull(T["kuvvet_yolu"]) if T.get("kuvvet_yolu") else None
    HARF = [(yazi(h, 40, (148, 40, 28), .9), OX + x * SC, y * SC, int(np.argmin(np.hypot(YOLK[:, 0] - x, YOLK[:, 1] - y)))) for h, x, y in T.get("harfler", [])] if YOLK is not None else []
    FOL = yazi(T.get("folio", "fol."), 34, (92, 58, 32), .62)
    N = OL + NSON if not HIZLI else OL + 60
    globals().update(dict(OL=OL, MUR=MUR, ZM=ZM, P0=P0, M0=M0, KUR=KUR, YOL=YOL, ESK=ESK, arka=arka, on=on, DOK=DOK, kag=kag, YOLK=YOLK, HARF=HARF, FOL=FOL,
                          KONT={15, 60, 150, 240, 300, 360, 429, OL + 120, OL + 280, OL + 400, N - 1} | {OL + k for k in T.get("kontrol_kareleri", []) + T.get("yakin_kareler", []) if OL + k < N}))
    import multiprocessing as mp, tempfile, shutil
    CEK = 1 if "--seri" in sys.argv else max(1, (os.cpu_count() or 2) - 1); ISK = tempfile.mkdtemp(prefix="levha-"); sinir = np.linspace(0, N, CEK + 1).astype(int)
    isler = [(int(sinir[k]), int(sinir[k + 1]), os.path.join(ISK, f"p{k:03d}.mp4")) for k in range(CEK) if sinir[k + 1] > sinir[k]]
    if CEK == 1: sonuc = [parca_ciz(isler[0])]
    else:
        with mp.get_context("fork").Pool(CEK) as havuz: sonuc = havuz.map(parca_ciz, isler, chunksize=1)
    KARE, fark, ozet = {}, [], []
    for k_, f_, o_ in sonuc: KARE.update(k_); fark += f_; ozet += o_
    open(os.path.join(ISK, "liste.txt"), "w", encoding="utf-8").write("".join(f"file '{y}'\n" for _, _, y in isler))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(ISK, "liste.txt"), "-c", "copy", C + "-dur.mp4"], check=True)
    open(C + "-ozet.txt", "w", encoding="utf-8").write("\n".join(ozet) + "\n"); shutil.rmtree(ISK, ignore_errors=True)
    adim(f"kareler yazıldı ({CEK} çekirdek, {N} kare, mp4 birleştirildi)")
    def izg(ks, ad, cols, sz):
        Tl = []
        for k in ks:
            t_ = cv2.resize(KARE[k], sz, interpolation=cv2.INTER_AREA); cv2.putText(t_, f"kare {k} ({k / 30:.1f} sn)", (8, 22), 0, .55, (30, 30, 160), 2); Tl.append(t_)
        while len(Tl) % cols: Tl.append(np.zeros_like(Tl[0]))
        cv2.imwrite(ad, np.vstack([np.hstack(Tl[r:r + cols]) for r in range(0, len(Tl), cols)]))
    ks = sorted(KARE); izg([k for k in ks if k < OL], C + "-olusum-izgara.png", 4, (480, 270)); izg([k for k in ks if k >= OL - 1], C + "-kontrol.png", 3, (640, 360))
    yak = []
    YK = [OL + k for k in T["yakin_kareler"]] if T.get("yakin_kareler") else [k for k in ks if k >= OL][:4]
    for p in T["parcalar"]:
        if p["tur"] == "sekil": ys_, xs_ = np.nonzero(A[p["ad"]] > .3); c = [(xs_.min() + xs_.max()) / 2, (ys_.min() + ys_.max()) / 2]; rr = max(np.ptp(xs_), np.ptp(ys_)) / 2
        else: c = p.get("c") or p["pivot"]; rr = p.get("r", 90)
        X, Y = int(OX + c[0] * SC), int(c[1] * SC); h = int(min(150 if p["tur"] != "sekil" else 260, (rr + 20) * SC)); sat = []
        for k in YK:
            cr = KARE[k][max(0, Y - h):Y + h, max(0, X - h):X + h]; cr = cv2.resize(cr, (300, 300), interpolation=cv2.INTER_CUBIC); cv2.putText(cr, f"{p['ad']} k{k}", (6, 18), 0, .5, (30, 30, 160), 1); sat.append(cr)
        yak.append(np.hstack(sat))
    cv2.imwrite(C + "-yakin.png", np.vstack(yak)); adim("kontrol görüntüleri")
    en = max(fark); s = "\n".join([f"{a}: {b} sn" for a, b in OLC] + rap + [f"oluşumda en büyük kare farkı {max(f for f, i in fark if i < OL):.3f}", f"tüm videoda en büyük kare farkı {en[0]:.3f} (kare {en[1]})", f"kare {N} ({N / 30:.1f} sn)"])
    open(C + "-olcum.txt", "w", encoding="utf-8").write(s + "\n"); print(s)
