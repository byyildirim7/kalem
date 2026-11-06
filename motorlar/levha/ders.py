"""Ders katmanı v6 (8. sınıf Fen FB.8.2 / 11. sınıf Fizik 11.1.8-11.1.10): kaldıraç ve palanga.
Anlatım sırası: öğeler ADIM ADIM gelir (her yazı satırı ~1 sn kalemle, arada 0,5 sn durak); gelen çizgi bir an kalınlaşır.
Renk = taraf: giriş (F, bileşenleri, d1, x) kırmızı · çıkış (G, d2, h) çivit · ek ağırlık (P) okra · yapı (O, makara, ip) sepya.
Kart satırlarında terimler kendi tarafının rengiyle yazılır ([r|..] [c|..] [o|..]); satır yazılırken o taraftaki çizgiler vurgulanır.
Ders kitabı çizimi: dik uzaklık = iki ucu oklu (↔) ölçü çizgisi + kuvvet noktalarından inen kesikli uzatma çizgileri; kuvvet doğrultusu
uzantısı kesikli; bileşenler kesikli; yol ölçüleri bir referans noktasının İLK ve SON konumu arasında, iki uçta kesikli yatay uzatma,
ilk (ya da dönülen) konum kesikli hayalet. Yol denetimi: uçlar referansa ±2 px, boy nesnenin kendi boyundan farklı ya da uzatmalı.
Çarpışma denetimi: öğe x (hareketli parçalar + ipler + gövde mürekkebi + folyo + kenar bandı + önceki öğeler, 7 px pay) = 0 px."""
import math, os, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import mekanizma as MEK
D = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.join(D, "font", "EBGaramond-Italic.ttf")
def _ilk_font(*yollar):
    for y in yollar:
        if os.path.exists(y): return y
    return yollar[-1]
WF = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")   # Windows: Arial Narrow (Office ile gelir) yoksa Arial; ₁ ₂ için Segoe UI (Arial'da yok)
DAR_FONT = _ilk_font("/System/Library/Fonts/Supplemental/Arial Narrow.ttf", "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf", "/Library/Fonts/Arial.ttf", os.path.join(WF, "ARIALN.TTF"), os.path.join(WF, "arial.ttf"), "/System/Library/Fonts/Helvetica.ttc")
DUZ_FONT = _ilk_font("/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", os.path.join(WF, "segoeui.ttf"), DAR_FONT)
YEDEK = _ilk_font("/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf", os.path.join(WF, "timesi.ttf"), DUZ_FONT)
RENK = {"r": np.array([42, 64, 164], np.float32), "c": np.array([122, 74, 47], np.float32), "o": np.array([28, 106, 154], np.float32), "s": np.array([22, 39, 58], np.float32)}
SATIR, DURAK, CIZ = 30, 15, 15                       # kare: yazı satırı 1 sn, durak 0,5 sn, çizgi 0,5 sn
STIL = "defter"; UC = (18, 30, 44)
def tr_buyuk(s): return s.replace("i", "İ").replace("ı", "I").upper()
def stil_ayarla(stil):
    """blueprint: teknik dar yazı (Arial Narrow, eksik alt indis Helvetica'dan), renk = taraf: giriş amber, çıkış camgöbeği, P açık sarı, yapı beyaz"""
    global STIL, FONT, YEDEK, UC
    STIL = stil
    if stil == "blueprint":
        FONT, YEDEK = DAR_FONT, DUZ_FONT; UC = (255, 250, 240)
        RENK.update(r=np.array([71, 179, 255], np.float32), c=np.array([230, 225, 92], np.float32), o=np.array([122, 240, 255], np.float32), s=np.array([255, 244, 234], np.float32))

def sayi(v): return (f"{v:.2f}".rstrip("0").rstrip(".")).replace(".", ",")
_CM = {}
def _kapsar(yol, c):
    if yol not in _CM:
        from fontTools.ttLib import TTFont
        _CM[yol] = set((TTFont(yol, fontNumber=0) if yol.endswith(".ttc") else TTFont(yol)).getBestCmap())
    return ord(c) in _CM[yol]
def kosular(s, taban):
    R, i = [], 0
    for m in re.finditer(r"\[([rcos])\|([^\]]*)\]", s):
        if m.start() > i: R.append((taban, s[i:m.start()]))
        R.append((m.group(1), m.group(2))); i = m.end()
    if i < len(s): R.append((taban, s[i:]))
    return R
def yazi_sprite(metin, boy, taban="s"):
    """renkli koşular: [r|..] kırmızı, [c|..] çivit, [o|..] okra; renkli koşu kalın (kontür). Döner: birleşik alfa, satır kutuları, renk katmanları."""
    f = ImageFont.truetype(FONT, boy); fy = ImageFont.truetype(YEDEK, boy) if os.path.exists(YEDEK) else f
    sat = [kosular(s, taban) for s in metin.split("\n")]; ah = int(boy * 1.22)
    fnt = lambda c: f if _kapsar(FONT, c) or f is fy else fy
    gen = [sum(fnt(c).getlength(c) for _, t in R for c in t) for R in sat]; w = int(max(gen)) + 16; h = ah * len(sat) + 12
    kat = {}; kut = []
    for i, R in enumerate(sat):
        x = 5.
        for k, t in R:
            if k not in kat: kat[k] = Image.new("L", (w, h), 0)
            d = ImageDraw.Draw(kat[k])
            for c in t: d.text((x, 5 + i * ah), c, font=fnt(c), fill=255, stroke_width=0 if k == "s" else 1, stroke_fill=255); x += fnt(c).getlength(c)
        kut.append((5, 5 + i * ah, int(x) + 3, 5 + (i + 1) * ah))
    kat = {k: np.array(v) for k, v in kat.items()}
    return np.max(list(kat.values()), 0), kut, kat

def kesikli(a, b, dash=10, gap=7):
    a, b = np.asarray(a, float), np.asarray(b, float); L = np.hypot(*(b - a)); u = (b - a) / (L + 1e-9); S = []; t = 0.
    while t < L - 1: S.append(np.array([a + u * t, a + u * min(L, t + dash)])); t += dash + gap
    return S
def ok_basi(a, b, boy=15):
    a, b = np.asarray(a, float), np.asarray(b, float); u = (b - a) / (np.hypot(*(b - a)) + 1e-9); R = []
    for s in (-1, 1): c, si = math.cos(s * .45), math.sin(s * .45); w = np.array([c * -u[0] - si * -u[1], si * -u[0] + c * -u[1]]); R.append(np.array([b, b + w * boy]))
    return R
def ok(a, b, boy=15): return [np.array([a, b], float)] + ok_basi(a, b, boy)
def cift_ok(a, b, boy=10): return [np.array([a, b], float)] + ok_basi(a, b, boy) + ok_basi(b, a, boy)
def kesikli_cokgen(P, dash=10, gap=7):
    P = np.asarray(P, float); S = []
    for i in range(len(P)): S += kesikli(P[i], P[(i + 1) % len(P)], dash, gap)
    return S

class Oge:
    def __init__(self, ad, tur, renk="s", al=.95, adim=None, sure=None, kaydir=None, muaf=(), taraf=None, kutu=False, gecikme=0, temas=(), **k):
        self.ad, self.tur, self.renk, self.al, self.adim, self.kaydir, self.muaf, self.taraf, self.kutu, self.gecikme = ad, tur, renk, al, adim, kaydir, set(muaf), taraf, kutu, gecikme
        self.temas = set(temas)                       # değmesi çizim gereği olan öğeler (ölçü oku ucu uzatma çizgisine, hayalete)
        self.of = np.zeros(2); self.n0 = 0; self.vurgu = []; self.__dict__.update(k)
        if tur == "yazi":
            if STIL == "blueprint" and renk == "s" and not ad.startswith("kart") and "=" not in self.metin: self.metin = tr_buyuk(self.metin)   # yapı etiketleri büyük harf (formül değil)
            self.spr, self.kut, self.kat = yazi_sprite(self.metin, self.boy, renk)
            self.sure = sure or SATIR * len(self.kut)
        else: self.sure = sure or CIZ
    def gorunur(self, n): return n >= self.n0 and (self.tur == "yazi" or bool(self.geo(n)))
    def maske(self, n, of=None, yaz=1., kalin=0):
        of = self.of if of is None else of
        if self.tur == "yazi":
            ax, ay = np.asarray(self.capa(n), float) + of; h, w = self.spr.shape
            x0 = ax - (w if self.hiza == "sag" else w / 2 if self.hiza == "orta" else 0); y0 = ay - (h / 2 if self.dikey == "orta" else h if self.dikey == "alt" else 0)
            if self.kutu:                             # sonuç kutusunun çerçevesi de denetime girer
                m = self.spr.copy(); h_, w_ = m.shape; cv2.rectangle(m, (1, 1), (w_ - 2, h_ - 2), 255, 2); return int(round(x0)), int(round(y0)), m
            return int(round(x0)), int(round(y0)), self.spr
        P = [np.asarray(p, float) + of for p in self.geo(n)]
        if not P: return None
        A = np.vstack(P); x0, y0 = np.floor(A.min(0)).astype(int) - 10; x1, y1 = np.ceil(A.max(0)).astype(int) + 10
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        for p in P: cv2.polylines(m, [np.int32((p - [x0, y0]) * 4)], False, 255, self.kal + kalin, cv2.LINE_AA, 2)
        return x0, y0, m

class Balon(Oge):
    daire_kurali = True                               # balon dairesi hiçbir parçaya değmez (kendi parçası dahil); yalnız kılavuz ucu değer
    """parça numarası: daire içinde numara + parçaya giden kılavuz çizgisi (ucu parçaya bağlı noktada, balon serbest yerleşir)"""
    def __init__(self, ad, no, merkez, hedef, adim=None, **k):
        super().__init__(ad, "poly", "s", .9, adim, kaydir="serbest", kal=2, geo=lambda n: [1], **k); self.no, self.merkez, self.hedef = str(no), merkez, hedef
    def maske(self, n, of=None, yaz=1., kalin=0):
        of = self.of if of is None else of; c = np.asarray(self.merkez(n), float) + of; h = np.asarray(self.hedef(n), float); R = 17
        v = h - c; L = np.hypot(*v) + 1e-9; a = c + v / L * R
        x0, y0 = np.floor(np.minimum(c - R, h)).astype(int) - 6; x1, y1 = np.ceil(np.maximum(c + R, h)).astype(int) + 6
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.circle(m, tuple(np.int32((c - [x0, y0]) * 4)), R * 4, 255, self.kal + kalin, cv2.LINE_AA, 2)
        if L > R + 4: cv2.line(m, tuple(np.int32((a - [x0, y0]) * 4)), tuple(np.int32((h - [x0, y0]) * 4)), 255, 1 + kalin, cv2.LINE_AA, 2); cv2.circle(m, tuple(np.int32((h - [x0, y0]) * 4)), 8, 255, -1, cv2.LINE_AA, 2)
        (tw, th_), _ = cv2.getTextSize(self.no, cv2.FONT_HERSHEY_SIMPLEX, .62, 2)
        cv2.putText(m, self.no, (int(c[0] - x0 - tw / 2), int(c[1] - y0 + th_ / 2)), cv2.FONT_HERSHEY_SIMPLEX, .62, 255, 2, cv2.LINE_AA)
        return x0, y0, m
    def daire_maske(self, n, of=None):
        of = self.of if of is None else of; c = np.asarray(self.merkez(n), float) + of; R = 19; x0, y0 = int(c[0]) - R - 3, int(c[1]) - R - 3
        m = np.zeros((2 * R + 7, 2 * R + 7), np.uint8); cv2.circle(m, (int((c[0] - x0) * 4), int((c[1] - y0) * 4)), R * 4, 255, -1, cv2.LINE_AA, 2); return x0, y0, m

def silme(o, yaz, m):
    """yazının yazılmış kısmı: soldan sağa, satır satır"""
    if yaz >= 1: return m
    L = [b[2] - b[0] for b in o.kut]; top = sum(L) * yaz; v = np.zeros(m.shape, np.float32); xs = np.arange(m.shape[1])
    for b, l in zip(o.kut, L):
        u = min(top, l); top -= u
        if u <= 0: break
        v[b[1]:b[3]] = np.clip((b[0] + u + 6 - xs) / 6, 0, 1)[None]
    return (m * v).astype(np.uint8)

def bas(img, o, n):
    if not o.gorunur(n): return
    u = min(1., (n - o.n0) / max(o.sure, 1)); H, W = img.shape[:2]
    vur = any(a <= n < b for a, b in o.vurgu) and o.tur != "yazi"
    r = o.maske(n, kalin=2 if vur else 0)
    if r is None: return
    x0, y0, m = r; h, w = m.shape; X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if X1 <= X0 or Y1 <= Y0: return
    if o.tur == "yazi":
        for k, km in o.kat.items():
            a = (silme(o, u, km)[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(np.float32) / 255 * o.al)[..., None]
            img[Y0:Y1, X0:X1] = img[Y0:Y1, X0:X1] * (1 - a) + RENK[k] * a
        if u < 1:                                    # kalem ucu
            L = [b[2] - b[0] for b in o.kut]; top = sum(L) * u
            for b, l in zip(o.kut, L):
                if top <= l: cv2.circle(img, (int(x0 + b[0] + top), int(y0 + (b[1] + b[3]) / 2)), 2, UC, -1, cv2.LINE_AA); break
                top -= l
        elif o.kutu:                                 # sonuç kutusu
            ana = max(o.kat, key=lambda k: (o.kat[k] > 60).sum() if k != "s" else -1)
            cv2.rectangle(img, (x0 + 1, y0 + 1), (x0 + w - 2, y0 + h - 2), tuple(float(v) for v in RENK[ana]), 2, cv2.LINE_AA)
        return
    al = 1. if vur else o.al * min(1., u * 1.5)
    a = (m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(np.float32) / 255 * al)[..., None]
    img[Y0:Y1, X0:X1] = img[Y0:Y1, X0:X1] * (1 - a) + RENK[o.renk] * a

def sirala(O, bas_n, erken=None):
    """adımları sırayla zamanlar; poly öğe gelince 0,4 sn vurgu; kart satırı yazılırken satırdaki renklerin tarafı vurgulanır.
    erken: {adım: en erken kare}. Döner: son kare, olay listesi [(adım, başlangıç, öğeler)]."""
    erken = erken or {}; t = bas_n; olay = []
    for a in sorted({o.adim for o in O if o.adim is not None}):
        els = [o for o in O if o.adim == a]; t = max(t, erken.get(a, 0))
        for o in els:
            o.n0 = t + o.gecikme
            if o.tur != "yazi": o.vurgu.append((o.n0 + o.sure, o.n0 + o.sure + 12))
        son = max(o.n0 + o.sure for o in els) if els else t; olay.append((a, t, [o.ad for o in els])); t = son + DURAK
    for o in O:
        if o.tur == "yazi" and o.ad.startswith("kart"):
            K = set(o.kat) - {"s"}
            for p in O:
                if p.tur != "yazi" and p.taraf in K: p.vurgu.append((o.n0, o.n0 + o.sure))
    return t, olay

# ───────── makinelere göre öğeler (anlatım sırası adım numarasıyla)
def kaldirac(T, COZ, sv, var=None):
    d = dict(T["ders"]); var = var or ("tork" if sv != "8" else None)
    if sv != "8" and var == "agirlik": d.update(G=50, F=10, P=20, ok_olcek=3.0)
    if sv != "8" and var == "acili": d.update(F=20, aci=30)
    P = np.array(d["pivot"], float); B = d["bolme"]; K = d["kalinlik"]; S = d["ok_olcek"]; G, F = d["G"], d["F"]; m = d.get("bolme_m", .5)
    L1, L2 = d["sol"] * B, d["sag"] * B; YX = P[0] + L2; yk = d.get("yuk_kutu", [YX - 70, 640, YX + 70, 780])
    ML = lambda n: COZ.poz("L", n)[0]; tf = lambda p, n: np.atleast_2d(np.asarray(p, float)) @ ML(n)[:, :2].T + ML(n)[:, 2]
    yuk = lambda p, n: COZ.nokta("Y", p, n)
    K_ = COZ.P["L"]["hareket"]["kareler"]; tepe = min(K_, key=lambda k: k[1])[0]; son = K_[-1][0]       # tepe: en çok dönülen kare (hayalet)
    yol_var = not (sv != "8" and var in ("acili", "agirlik"))
    O = []; a = iter(range(1, 99)); A_ = lambda: next(a)
    O.append(Oge("bölme çentikleri", "poly", "s", .9, None, kal=3, muaf={"L"},
                 geo=lambda n: [tf([[P[0] + k * B, P[1] - K / 2 + 1], [P[0] + k * B, P[1] - K / 2 + 14]], n) for k in range(-d["sol"] + 1, d["sag"]) if k]))
    yo = P[1] - 112
    s1 = A_(); O.append(Oge("O", "yazi", "s", .95, s1, kaydir="serbest", boy=34 if sv == "8" else 40, hiza="sag" if sv == "8" else "sol", dikey="ust",
                            metin="O (destek noktası)" if sv == "8" else "O", capa=lambda n: P + ([-30, 82] if sv == "8" else [26, 28])))
    gx = YX + 70 + 40
    s2 = A_(); O.append(Oge("G oku", "poly", "c", .95, s2, kal=4, taraf="c", geo=lambda n: ok(yuk([gx, 640], n), yuk([gx, 640 + G * S], n))))
    O.append(Oge("G yazısı", "yazi", "c", .95, s2, kaydir="serbest", boy=32, hiza="sol", dikey="orta", gecikme=8,
                 metin="çıkış kuvveti (yük)\n" + f"G = {G} N" if sv == "8" else f"G = {G} N", capa=lambda n: yuk([gx + 14, 640 + G * S / 2], n)))
    def dik(x0, x1, y, n, uc0, uc1):                  # ↔ dik uzaklık + iki noktadan çıkan kesikli uzatmalar
        X0, X1 = tf([x0, P[1]], n)[0][0], tf([x1, P[1]], n)[0][0]
        return cift_ok([X0, y], [X1, y]) + kesikli([X0, uc0], [X0, y - 10]) + kesikli([X1, uc1], [X1, y - 10])
    ust_O = yo - 80 if d.get("P") else yo - 10; alt_O = P[1] - (62 if STIL == "blueprint" else 34)      # blueprint: O uzatması merkez çizgisinin bittiği yerden
    s3 = A_(); O.append(Oge("d₂ ölçüsü", "poly", "c", .9, s3, kal=2, taraf="c", geo=lambda n: cift_ok([P[0], yo], [tf([P[0] + L2, P[1]], n)[0][0], yo]) + kesikli([P[0], alt_O], [P[0], ust_O])
                 + kesikli([tf([P[0] + L2, P[1]], n)[0][0], P[1] - K / 2 - 10], [tf([P[0] + L2, P[1]], n)[0][0], yo - 10])))
    O.append(Oge("d₂ yazısı", "yazi", "c", .95, s3, kaydir="serbest", boy=32, hiza="orta", dikey="alt", gecikme=8,
                 metin=f"yük kolu ({d['sag']} bölme)" if sv == "8" else f"d₂ = {sayi(d['sag'] * m)} m", capa=lambda n: [P[0] + L2 / 2, yo - 10]))
    A = lambda n: tf([P[0] - L1, P[1] - K / 2 - 11], n)[0]
    s4 = A_()
    if d.get("aci"):
        th = math.radians(d["aci"]); Fd, Fp = F * math.sin(th) * S, F * math.cos(th) * S
        Q = lambda p, n: tf([[P[0] - L1 + p[0], P[1] - K / 2 - 11 + p[1]]], n)[0]
        O.append(Oge("F oku + θ yayı", "poly", "r", .95, s4, kal=4, taraf="r", geo=lambda n: ok(Q((-Fp, -Fd), n), A(n))
                     + [np.array([Q((-70 * math.cos(t), -70 * math.sin(t)), n) for t in np.linspace(0, th, 18)])]))
        O.append(Oge("F doğrultusu", "poly", "r", .6, s4, kal=2, gecikme=5, geo=lambda n: kesikli(Q((-Fp * 1.12, -Fd * 1.12), n), Q((-Fp * 1.75, -Fd * 1.75), n), 8, 6)))
        O.append(Oge("kol uzantısı", "poly", "s", .75, s4, kal=2, gecikme=5, geo=lambda n: kesikli(Q((-30, 0), n), Q((-56, 0), n), 8, 6) + kesikli(Q((-86, 0), n), Q((-170, 0), n), 8, 6)))
        O.append(Oge("F yazısı", "yazi", "r", .95, s4, kaydir="serbest", boy=32, hiza="sag", dikey="alt", gecikme=8, metin=f"F = {F} N", capa=lambda n: Q((-Fp * 1.2 + 30, -Fd * 1.2 - 34), n)))
        O.append(Oge("θ yazısı", "yazi", "r", .95, s4, kaydir="serbest", boy=30, hiza="sag", dikey="orta", gecikme=38, metin=f"θ = {d['aci']}°", capa=lambda n: Q((-112, 8), n)))
        s5 = A_(); alt = K + 32
        O.append(Oge("F dik bileşen", "poly", "r", .9, s5, kal=3, taraf="r", geo=lambda n: kesikli(Q((28, -Fd), n), Q((28, 0), n)) + ok_basi(Q((28, -Fd), n), Q((28, 0), n), 12)))
        O.append(Oge("F dik yazısı", "yazi", "r", .95, s5, kaydir="serbest", boy=30, hiza="sol", dikey="orta", gecikme=8, metin=f"F·sinθ = {sayi(F * math.sin(th))} N", capa=lambda n: Q((40, -Fd / 2), n)))
        O.append(Oge("F paralel bileşen", "poly", "r", .9, s5, kal=3, taraf="r", gecikme=40, geo=lambda n: kesikli(Q((-Fp + 20, alt), n), Q((20, alt), n)) + ok_basi(Q((-Fp + 20, alt), n), Q((20, alt), n), 12)))
        O.append(Oge("F paralel yazısı", "yazi", "r", .95, s5, kaydir="serbest", boy=30, hiza="sol", dikey="orta", gecikme=48, metin=f"F·cosθ = {sayi(F * math.cos(th))} N", capa=lambda n: Q((34, alt), n)))
    else:
        O.append(Oge("F oku", "poly", "r", .95, s4, kal=4, taraf="r", geo=lambda n: ok(A(n) - [0, F * S], A(n))))
        O.append(Oge("F yazısı", "yazi", "r", .95, s4, kaydir="serbest", boy=32, hiza="sag", dikey="orta", gecikme=8,
                     metin="giriş kuvveti\n" + f"F = {F} N" if sv == "8" else f"F = {F} N", capa=lambda n: A(n) + [-14, -F * S / 2]))
    f_ust = P[1] - K / 2 - 11 - (24 if d.get("aci") else F * S + 12)   # uzatma F okunun üstünden başlar
    s6 = A_(); O.append(Oge("d₁ ölçüsü", "poly", "r", .9, s6, kal=2, taraf="r", temas={"d₂ ölçüsü"}, geo=lambda n: cift_ok([tf([P[0] - L1, P[1]], n)[0][0], yo], [P[0], yo])
                 + kesikli([tf([P[0] - L1, P[1]], n)[0][0], f_ust], [tf([P[0] - L1, P[1]], n)[0][0], yo - 10])))
    O.append(Oge("d₁ yazısı", "yazi", "r", .95, s6, kaydir="serbest", boy=32, hiza="orta", dikey="alt", gecikme=8,
                 metin=f"kuvvet kolu ({d['sol']} bölme)" if sv == "8" else f"d₁ = {sayi(d['sol'] * m)} m", capa=lambda n: [P[0] - L1 / 2, yo - 10]))
    if d.get("P"):
        cg = (P[0] - L1 + P[0] + L2) / 2; cgu = lambda n: tf([cg, P[1] + K / 2 + 7], n)[0]
        s7 = A_(); O.append(Oge("P oku", "poly", "o", .95, s7, kal=4, taraf="o", geo=lambda n: ok(cgu(n), cgu(n) + [0, d["P"] * S])))
        O.append(Oge("P yazısı", "yazi", "o", .95, s7, kaydir="serbest", boy=30, hiza="sol", dikey="orta", gecikme=8, metin=f"P = {d['P']} N", capa=lambda n: cgu(n) + [14, d["P"] * S / 2]))
        O.append(Oge("d₃ ölçüsü", "poly", "o", .9, s7, kal=2, taraf="o", gecikme=40, temas={"d₂ ölçüsü", "d₁ ölçüsü"}, geo=lambda n: cift_ok([tf([cg, P[1]], n)[0][0], yo - 70], [P[0], yo - 70]) + kesikli([cg, P[1] - K / 2 - 10], [cg, yo - 80])))
        O.append(Oge("d₃ yazısı", "yazi", "o", .95, s7, kaydir="serbest", boy=32, hiza="orta", dikey="alt", gecikme=48, metin=f"d₃ = {sayi((P[0] - cg) / B * m)} m", capa=lambda n: [(cg + P[0]) / 2, yo - 80]))
    YOL = []
    if yol_var:                                      # dönülen konumun kesikli hayaleti + uç yolu x ve yük yolu h (alt kenar referansı)
        s8 = A_(); Mt = ML(tepe); kol_t = MEK.kol_cokgen(P[0] - L1, P[1], P[0] + L2, P[1], K, K) @ Mt[:, :2].T + Mt[:, 2]
        dy_t = yuk([0, 0], tepe)[1]; kut_t = np.array([[yk[0], yk[1]], [yk[2], yk[1]], [yk[2], yk[3]], [yk[0], yk[3]]], float) + [0, dy_t]
        O.append(Oge("dönülen konum (hayalet)", "poly", "s", .55, s8, kal=2, muaf={"L", "Y", "govde"}, temas={"bölme çentikleri", "G oku", "d₁ ölçüsü", "d₂ ölçüsü", "F oku", "F yazısı"}, geo=lambda n: kesikli_cokgen(kol_t, 9, 7) + kesikli_cokgen(kut_t, 9, 7)))
        xb = P[0] - L1 - 46; ux0, ux1 = P[1], (tf([P[0] - L1, P[1]], tepe)[0][1]); xu = tf([P[0] - L1, P[1]], tepe)[0][0]
        O.append(Oge("x yolu", "poly", "r", .9, s8, kal=2, taraf="r", gecikme=20, temas={"dönülen konum (hayalet)"}, geo=lambda n: cift_ok([xb, ux0], [xb, ux1]) + kesikli([P[0] - L1 - 26, ux0], [xb - 8, ux0], 6, 5)
                     + kesikli([xu - 20, ux1], [xb - 8, ux1], 6, 5)))
        O.append(Oge("x yazısı", "yazi", "r", .95, s8, kaydir="serbest", boy=34, hiza="sag", dikey="orta", gecikme=28, metin="x", capa=lambda n: [xb - 10, (ux0 + ux1) / 2]))
        hb = yk[0] - 34; uh0, uh1 = yk[3], yk[3] + dy_t                                    # yükün SOL yanında (sağda G oku var)
        O.append(Oge("h yolu", "poly", "c", .9, s8, kal=2, taraf="c", gecikme=36, temas={"dönülen konum (hayalet)"}, geo=lambda n: cift_ok([hb, uh0], [hb, uh1]) + kesikli([yk[0] - 12, uh0], [hb - 8, uh0], 6, 5) + kesikli([yk[0] - 6, uh1], [hb - 8, uh1], 6, 5)))
        O.append(Oge("h yazısı", "yazi", "c", .95, s8, kaydir="serbest", boy=34, hiza="sag", dikey="orta", gecikme=44, metin="h", capa=lambda n: [hb - 12, (uh0 + uh1) / 2]))
        YOL = [("x", "x yolu", ux0, ux1, None, True), ("h", "h yolu", uh0, uh1, yk[3] - yk[1], True)]
    xm, hm = L1 * .2 / B * m, L2 * .2 / B * m; d1, d2 = d["sol"] * m, d["sag"] * m
    if sv == "8":
        kart = [f"Kuvvet kolu {d['sol']} kat uzun →", f"kuvvetten {d['sol']} kat kazanç: [c|{G} N] yerine [r|{F} N],", f"yoldan {d['sol']} kat kayıp: [r|x] = {d['sol']}·[c|h].", "Kaldıraç ağırlığı ve sürtünme önemsiz."]; kutu = None
    elif var == "acili":
        sn = math.sin(th)
        kart = ["Yalnız dik bileşen tork yapar.", "Στ = 0:  [r|F·sinθ·d₁] = [c|G·d₂]", f"[r|F · sin{d['aci']}° · {sayi(d1)}] = [c|{G} · {sayi(d2)}]", f"[r|F · {sayi(sn * d1)}] = [c|{sayi(G * d2)}]",
                f"[r|F = {sayi(G * d2 / (sn * d1))} N]", "Kaldıraç ağırlığı ve sürtünme önemsiz."]; kutu = 4
    elif var == "agirlik":
        d3 = (P[0] - (P[0] - L1 + P[0] + L2) / 2) / B * m
        kart = ["Kolun ağırlığı ağırlık merkezinde.", "Στ = 0:  [r|F·d₁] + [o|P·d₃] = [c|G·d₂]", f"[r|F · {sayi(d1)}] + [o|{d['P']} · {sayi(d3)}] = [c|{G} · {sayi(d2)}]",
                f"[r|F = {sayi((G * d2 - d['P'] * d3) / d1)} N]", f"(g = 10 m/s²: kolun kütlesi {sayi(d['P'] / 10)} kg; sürtünme önemsiz.)"]; kutu = 3
    else:
        kart = ["Στ = 0 (O'ya göre):  [r|F·d₁] = [c|G·d₂]", f"[r|F · {sayi(d1)}] = [c|{G} · {sayi(d2)}]", f"[r|F = {sayi(G * d2 / d1)} N]", f"İş:  [r|F·x] = [c|G·h]",
                f"[r|{F} · {sayi(xm)}] = [c|{G} · {sayi(hm)}]  →  {sayi(F * xm)} J = {sayi(G * hm)} J", "Kaldıraç ağırlığı ve sürtünme önemsiz."]; kutu = 2
    pay = lambda i: (10 if kutu is not None and i >= kutu else 0) + (10 if kutu is not None and i > kutu else 0)   # kutu komşu satıra değmesin
    for i, s in enumerate(kart):
        O.append(Oge(f"kart {i + 1}", "yazi", "s", .95, 50 + i, boy=37 if i != len(kart) - 1 else 30, hiza="sol", dikey="ust", metin=s, kutu=(i == kutu), capa=(lambda i: lambda n: [90, 46 + i * 50 + pay(i)])(i)))
    return O, {"bas": son + 10, "yol": YOL}

def palanga(T, COZ, sv, var=None):
    d = dict(T["ders"]); var = var or ("temel" if sv != "8" else None)
    if sv != "8" and var == "agirlikli": d.update(P=4, F=12, ok_olcek=8.0)
    if sv != "8" and var == "verim": d.update(F=12.5)
    S = d["ok_olcek"]; G, F = d["G"], d["F"]; AX, HX, HY, M, Fc, RI, RJ = d["AX"], d["HX"], d["HY"], np.array(d["M"], float), np.array(d["Fc"], float), d["RI"], d["RJ"]
    br = d["birim"]; hn = lambda p, n: COZ.nokta("H", p, n); yn = lambda p, n: COZ.nokta("Y", p, n); mn = lambda p, n: np.asarray(p, float) + (COZ.nokta("M", M, n) - M)
    yk = d.get("yuk_kutu", [M[0] - 80, 730, M[0] + 80, 880]); hk = d.get("tut_kutu", [HX - 34, HY, HX + 34, HY + 22])
    O = []; a = iter(range(1, 99)); A_ = lambda: next(a)
    s1 = A_(); O.append(Oge("sabit makara", "yazi", "s", .9, s1, kaydir="serbest", boy=30, hiza="sol", dikey="orta", metin="sabit makara", capa=lambda n: Fc + [RJ + 22, -32]))
    O.append(Oge("hareketli makara", "yazi", "s", .9, s1, kaydir="serbest", boy=30, hiza="sag", dikey="orta", gecikme=SATIR, metin="hareketli makara", capa=lambda n: mn([AX - 12, M[1] + 5], n)))
    s2 = A_(); O.append(Oge("1. ip", "yazi", "s", .95, s2, kaydir="serbest", boy=32, hiza="sag", dikey="orta", metin="1. ip", capa=lambda n: mn([AX - 10, M[1] - 92], n)))
    O.append(Oge("2. ip", "yazi", "s", .95, s2, kaydir="serbest", boy=32, hiza="sol", dikey="orta", gecikme=SATIR, metin="2. ip", capa=lambda n: mn([M[0] + RI + 10, M[1] - 92], n)))
    gx = M[0] - 100; y0 = yk[1]
    s3 = A_(); O.append(Oge("G oku", "poly", "c", .95, s3, kal=4, taraf="c", geo=lambda n: ok(yn([gx, y0], n), yn([gx, y0 + G * S], n))))
    O.append(Oge("G yazısı", "yazi", "c", .95, s3, kaydir="serbest", boy=32, hiza="sag", dikey="orta", gecikme=8,
                 metin="çıkış kuvveti\n(yük) " + f"G = {G} N" if sv == "8" else f"G = {G} N", capa=lambda n: yn([gx - 14, y0 + G * S / 2], n)))
    if d.get("P"):                                     # makara ağırlığı: merkezden kesikli doğrultu, ok makaranın altından dışarı (aynı ölçek)
        px = M[0] + 26; ry = math.sqrt(max(0, (RJ + 2) ** 2 - 26 ** 2)) + 4
        O.append(Oge("P oku", "poly", "o", .95, s3, kal=4, taraf="o", muaf={"M", "Y", "ip"}, gecikme=45, geo=lambda n: kesikli(mn([px, M[1]], n), mn([px, M[1] + ry - 12], n), 6, 5)
                     + ok(mn([px, M[1] + ry], n), mn([px, M[1] + ry + d["P"] * S], n), 12)))
        O.append(Oge("P yazısı", "yazi", "o", .95, s3, kaydir="serbest", boy=30, hiza="sag", dikey="orta", gecikme=53, metin=f"P = {d['P']} N", capa=lambda n: mn([AX - 12, M[1] + 80], n)))
    fx = HX + 128
    s4 = A_(); O.append(Oge("F oku", "poly", "r", .95, s4, kal=4, taraf="r", geo=lambda n: ok(hn([fx, HY - 10 - F * S], n), hn([fx, HY - 10], n))))
    O.append(Oge("F yazısı", "yazi", "r", .95, s4, kaydir="serbest", boy=30, hiza="sol", dikey="orta", gecikme=8,
                 metin="giriş\nkuvveti\n" + f"F = {sayi(F)} N" if sv == "8" else f"F = {sayi(F)} N", capa=lambda n: hn([fx + 12, HY - 10 - F * S / 2], n)))
    s5 = A_(); O.append(Oge("kaldırma", "poly", "s", 0., s5, sure=120, kal=1, geo=lambda n: []))   # görünmez adım: sürücü bu adımda çalışır (120 kare)
    s6 = A_(); dmax = d["dmax"]
    gy = np.array([[yk[0], yk[1]], [yk[2], yk[1]], [yk[2], yk[3]], [yk[0], yk[3]]], float); gh = np.array([[hk[0], hk[1]], [hk[2], hk[1]], [hk[2], hk[3]], [hk[0], hk[3]]], float)
    O.append(Oge("ilk konum (hayalet)", "poly", "s", .55, s6, kal=2, muaf={"ip"}, geo=lambda n: kesikli_cokgen(gy, 9, 7) + kesikli_cokgen(gh, 9, 7)))
    hx = yk[2] + 40; uh0, uh1 = yk[3], yk[3] - dmax
    O.append(Oge("h yolu", "poly", "c", .9, s6, kal=2, taraf="c", gecikme=20, temas={"ilk konum (hayalet)"}, geo=lambda n: cift_ok([hx, uh0], [hx, uh1]) + kesikli([yk[2] + 4, uh0], [hx + 8, uh0], 6, 5) + kesikli([yk[2] + 12, uh1], [hx + 8, uh1], 6, 5)))
    O.append(Oge("h yazısı", "yazi", "c", .95, s6, kaydir="serbest", boy=34, hiza="sol", dikey="orta", gecikme=28, metin="h", capa=lambda n: [hx + 10, (uh0 + uh1) / 2]))
    xx = hk[2] + 44; ux0, ux1 = hk[3], hk[3] + 2 * dmax
    O.append(Oge("x yolu", "poly", "r", .9, s6, kal=2, taraf="r", gecikme=36, temas={"ilk konum (hayalet)"}, geo=lambda n: cift_ok([xx, ux0], [xx, ux1]) + kesikli([hk[2] + 4, ux0], [xx + 30, ux0], 6, 5) + kesikli([hk[2] + 12, ux1], [xx + 30, ux1], 6, 5)))
    O.append(Oge("x yazısı", "yazi", "r", .95, s6, kaydir="serbest", boy=34, hiza="sag", dikey="orta", gecikme=44, metin="x", capa=lambda n: [xx - 10, (ux0 + ux1) / 2]))
    O.append(Oge("2h karşılaştırma", "poly", "c", .9, s6, kal=2, taraf="c", gecikme=52, temas={"x yolu"}, geo=lambda n: cift_ok([xx + 24, ux0], [xx + 24, ux0 + dmax], 8) + cift_ok([xx + 24, ux0 + dmax], [xx + 24, ux1], 8)))
    O.append(Oge("2h yazısı", "yazi", "c", .95, s6, kaydir="serbest", boy=34, hiza="sol", dikey="orta", gecikme=60, metin="2h", capa=lambda n: [xx + 34, ux0 + dmax]))
    YOL = [("h", "h yolu", uh0, uh1, yk[3] - yk[1], True), ("x", "x yolu", ux0, ux1, hk[3] - hk[1], True), ("2h", "2h karşılaştırma", ux0, ux1, None, True)]
    hb = dmax / br * d.get("birim_m", .5); xm = 2 * hb
    if sv == "8":
        kart = ["Yük 2 iple taşınır →", "kuvvet yarıya iner:", f"[c|{G} N] yerine [r|{sayi(F)} N].", "İp 2 kat çekilir:", "[r|x] = 2·[c|h].", "Makara ağırlığı ve", "sürtünme önemsiz."]; kutu = None
    elif var == "agirlikli":
        kart = ["Yük ve makara", "2 iple taşınır:", "2·[r|F] = [c|G] + [o|P]", f"2·[r|F] = [c|{G}] + [o|{d['P']}]", f"[r|F = {sayi((G + d['P']) / 2)} N]", "Sürtünme önemsiz."]; kutu = 4
    elif var == "verim":
        kart = ["Sürtünme var:", f"[r|F = {sayi(F)} N] (ideal {sayi(G / 2)} N)", "η = [c|G·h] / ([r|F·x])", f"η = [c|{G} · {sayi(hb)}] / ([r|{sayi(F)} · {sayi(xm)}])", f"η = {sayi(G * hb / (F * xm))} → %{G * hb / (F * xm) * 100:.0f}", "Makara ağırlığı önemsiz."]; kutu = 4
    else:
        kart = ["Yük 2 iple taşınır:", "2·[r|F] = [c|G]", f"2·[r|F] = [c|{G}]", f"[r|F = {sayi(G / 2)} N]", "İş:  [r|F·x] = [c|G·h]", f"[r|{sayi(F)} · {sayi(xm)}] = [c|{G} · {sayi(hb)}]", f"{sayi(F * xm)} J = {sayi(G * hb)} J", "Makara ağırlığı ve", "sürtünme önemsiz."]; kutu = 3
    pay = lambda i: (10 if kutu is not None and i >= kutu else 0) + (10 if kutu is not None and i > kutu else 0)
    for i, s in enumerate(kart):
        O.append(Oge(f"kart {i + 1}", "yazi", "s", .95, 50 + i, boy=37 if not s.startswith(("Makara", "sürtünme", "Sürtünme ö")) else 30, hiza="sol", dikey="ust", metin=s, kutu=(i == kutu),
                     capa=(lambda i: lambda n: [1080, 96 + i * 50 + pay(i)])(i)))
    return O, {"bas": 0, "kaldirma_adim": s5, "yol_adim": s6, "yol": YOL}

def balonlar(T, COZ):
    """blueprint parça numaraları: tanımdaki 'balon' listesi [no, parça ad ya da None (gövde), hedef nokta, balon merkezi]"""
    B = []
    for b_ in T["ders"].get("balon", []):
        no, pad, hedef, merkez = b_[:4]; muaf = set(b_[4]) if len(b_) > 4 else ({pad} if pad else {"govde"})     # kılavuz ucu çizim gereği parçaya değer
        if pad: f = (lambda pad, hedef: lambda n: COZ.nokta(pad, hedef, n))(pad, hedef); g = (lambda pad, hedef, merkez: lambda n: np.asarray(merkez, float) + (COZ.nokta(pad, hedef, n) - np.asarray(hedef, float)))(pad, hedef, merkez)
        else: f = (lambda h: lambda n: h)(hedef); g = (lambda m_: lambda n: m_)(merkez)
        B.append(Balon(f"parça {no}", no, g, f, muaf=muaf))
    return B

def disli(T, COZ, sv, var=None):
    """dişli zinciri: diş sayıları, dönme yönleri (komşu ters), n₁·z₁ = n₂·z₂, giriş/çıkış devir oranı. Renk: giriş (ilk dişli) r, çıkış (son) c."""
    P = [p for p in T["parcalar"] if p["tur"] == "disli"]; O = []; a = iter(range(1, 99)); A_ = lambda: next(a); alt = ["₁", "₂", "₃", "₄", "₅", "₆"]
    yon = {}
    for p in P:
        h = p["hareket"]; yon[p["ad"]] = 1 if h["tur"] == "donme" else -yon[h["parca"]] if h["oran"] < 0 else yon[h["parca"]]
    aci = T["ders"].get("ok_aci", {})
    for i, p in enumerate(P):
        si = A_(); k = "r" if i == 0 else "c" if i == len(P) - 1 else "s"; c = np.array(p["c"], float); R = p["r"] + T["ders"].get("yay_pay", 22); a0, a1 = aci.get(p["ad"], [230, 290])
        th = np.radians(np.linspace(a0, a1, 30)); yay = np.stack([c[0] + R * np.cos(th), c[1] + R * np.sin(th)], 1)
        if yon[p["ad"]] < 0: yay = yay[::-1]
        O.append(Oge(f"{p['ad']} yönü", "poly", k, .95, si, kal=3, taraf=k if k != "s" else None, geo=(lambda yay: lambda n: [yay] + ok_basi(yay[-4], yay[-1], 14))(yay)))
        lp = c + (R + 34) * np.array([np.cos(np.radians((a0 + a1) / 2)), np.sin(np.radians((a0 + a1) / 2))])
        O.append(Oge(f"{p['ad']} diş sayısı", "yazi", k, .95, si, kaydir="serbest", boy=32, hiza="orta", dikey="orta", gecikme=8,
                     metin=("giriş " if i == 0 else "çıkış " if i == len(P) - 1 else "") + f"z{alt[i]} = {p['Z']}", capa=(lambda lp: lambda n: lp)(lp)))
    z1, zn = P[0]["Z"], P[-1]["Z"]; o = z1 / zn; x, y = T["ders"].get("kart", [60, 40])
    nn = f"n{alt[len(P) - 1]}"; kv = len(P) - 1; isr = "ters" if kv % 2 else "aynı"
    k2 = f"[r|{z1}·n₁] = [c|{zn}·{nn}]  →"; w2 = yazi_sprite(k2, 26)[0].shape[1]
    sg = "−" if kv % 2 else ""
    satir = [("Her kavramada  n₁·z₁ = n₂·z₂ ;  ara dişliler oranı değiştirmez.", 0, False),
             (f"Her kavrama dönme yönünü çevirir; {kv} kavrama: çıkış girişe göre {isr} döner ({'−' if kv % 2 else '+'}).", 0, False),
             (k2, 0, False), (f"[c|{nn} = {sg}{sayi(o)}·n₁]", w2 + 14, True)]
    yy = [y, y + 40, y + 90, y + 86]                  # kutulu satır kendi payıyla; kutu hiçbir satıra değmez
    for i, (s_, dx, kt) in enumerate(satir):
        O.append(Oge(f"kart {i + 1}", "yazi", "s", .95, 50 + i, boy=26, hiza="sol", dikey="ust", metin=s_, kutu=kt, capa=(lambda dx, y_: lambda n: [x + dx, y_])(dx, yy[i])))
    return O, {"bas": 0, "yol": []}

def kur(T, COZ, sv, var=None):
    O, PLAN = {"kaldirac": kaldirac, "palanga": palanga, "disli": disli}[T["ders"]["tur"]](T, COZ, sv, var)
    if STIL == "blueprint": O = balonlar(T, COZ) + O
    return O, PLAN

def yol_denetimi(O, YOL, n_son, rap):
    """her yol ölçüsünün uçları referans noktasının ilk/son y'sine ±2 px; boy nesne boyundan %15+ farklı ya da uzatmalı. Tutmazsa dur."""
    ad = {o.ad: o for o in O}; hata = []
    for ad_, oad, y0, y1, nesne, uzatma in YOL:
        Ls = [L for L in ad[oad].geo(n_son) if len(L) == 2 and abs(L[1][0] - L[0][0]) < 1 and abs(L[1][1] - L[0][1]) > 20]   # düşey ana çizgiler (uzatma ve ok başları hariç)
        ya, yb = min(min(L[0][1], L[1][1]) for L in Ls), max(max(L[0][1], L[1][1]) for L in Ls); r0, r1 = sorted([y0, y1])
        ok_uc = abs(ya - r0) <= 2 and abs(yb - r1) <= 2; boy = yb - ya; fark = None if not nesne else abs(boy - nesne) / nesne
        ok_boy = uzatma or (fark is not None and fark > .15)
        rap.append(f"yol denetimi '{ad_}': uçlar y {ya:.1f}-{yb:.1f}, referans {r0:.1f}-{r1:.1f} (±2 px {'tamam' if ok_uc else 'TUTMADI'}); boy {boy:.1f} px"
                   + (f", nesne boyu {nesne:.0f} px (fark %{fark * 100:.0f})" if nesne else "") + f", kesikli uzatma {'var' if uzatma else 'yok'} -> {'tamam' if ok_uc and ok_boy else 'TUTMADI'}")
        if not (ok_uc and ok_boy): hata.append(ad_)
    if hata: raise SystemExit(f"yol denetimi tutmadı: {hata}")

class _Bos: muaf = set()
_BOS = _Bos()
def yerlestir(O, TEMEL, KARELER, H0, W0, rap):
    """TEMEL(o) -> {n: bool} taban engel (parçalar/ipler öğenin muafına göre + gövde + folyo + kenar). Yerleşen öğeler (7 px payla)
    sayaç maskesine eklenir; öğenin temas izni olan öğeler sayaçtan düşülür. Kesişen yazı serbest, ok kendi ekseninde kaydırılır."""
    ell = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)); C = {n: np.zeros((H0, W0), np.uint8) for n in KARELER}; PL = {}
    for o in sorted(O, key=lambda o: (0 if o.kaydir is None else 1 if o.kaydir != "serbest" else 2) + (o.ad.startswith("kart") and o.kaydir is None) * .5):
        T0 = TEMEL(o); E = {}
        for n in KARELER:
            if not o.gorunur(n): continue
            c = C[n]
            if o.temas:
                c = c.copy()
                for k in o.temas:
                    if n in PL.get(k, {}): X0, Y0, mm = PL[k][n]; c[Y0:Y0 + mm.shape[0], X0:X0 + mm.shape[1]] -= mm
            E[n] = T0[n] | (c > 0)
        TAM = TEMEL(_BOS) if getattr(o, "daire_kurali", False) else None
        def kesisim(of):
            t = 0
            if TAM is not None:                       # balon dairesi x bütün parçalar (muafsız)
                for n in E:
                    x0, y0, m = o.daire_maske(n, of); h, w = m.shape; X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W0, x0 + w), min(H0, y0 + h)
                    if X1 > X0 and Y1 > Y0: t += int(((m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] > 60) & TAM[n][Y0:Y1, X0:X1]).sum())
            for n, En in E.items():
                r = o.maske(n, of)
                if r is None: continue
                x0, y0, m = r; h, w = m.shape; X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W0, x0 + w), min(H0, y0 + h)
                if X1 <= X0 or Y1 <= Y0: t += int((m > 60).sum()); continue
                mk = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] > 60; t += int((m > 60).sum()) - int(mk.sum()) + int((mk & En[Y0:Y1, X0:X1]).sum())
            return t
        k0 = kesisim(o.of); en = (k0, o.of.copy())
        if k0 and o.kaydir:
            if o.kaydir == "serbest": adaylar = [np.array([r * math.cos(a), r * math.sin(a)]) for r in range(4, 200, 4) for a in np.linspace(0, 2 * np.pi, max(8, int(r / 3)), endpoint=False)]
            else: adaylar = [np.asarray(o.kaydir, float) * s for s in range(2, 60, 2)]
            for of in adaylar:
                k = kesisim(of)
                if k < en[0]: en = (k, of)
                if k == 0: break
        o.of = en[1]; PL[o.ad] = {}
        rap.append(f"etiket '{o.ad}': kesişim {k0} px -> {en[0]} px (kaydırma {en[1][0]:+.0f}, {en[1][1]:+.0f} px, {len(E)} örnek kare" + (f", temas izni: {', '.join(sorted(o.temas))}" if o.temas else "") + ")")
        for n in E:
            r = o.maske(n)
            if r is None: continue
            x0, y0, m = r; h, w = m.shape; X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W0, x0 + w), min(H0, y0 + h)
            if X1 <= X0 or Y1 <= Y0: continue
            mm = (cv2.dilate((m > 60).astype(np.uint8), ell)[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] > 0).astype(np.uint8); C[n][Y0:Y1, X0:X1] += mm; PL[o.ad][n] = (X0, Y0, mm)
