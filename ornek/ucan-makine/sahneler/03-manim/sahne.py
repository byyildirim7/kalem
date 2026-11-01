# Sahne 3: kaldırma formülü (Manim, LaTeX yok: Text/MarkupText). 240 kare = 8 sn.
import json, numpy as np, manimpango
from pathlib import Path
from manim import *
from PIL import Image, ImageFilter

AD = Path(__file__).parent
FONT = AD.parent.parent.parent.parent / "ortak" / "font"
for f in ["EBGaramond.ttf", "EBGaramond-Italic.ttf", "IMFeENrm28P.ttf", "IMFeENit28P.ttf"]:
    manimpango.register_font(str(FONT / f))   # yalnız bu süreç, sisteme kurulum yok

config.pixel_width, config.pixel_height, config.frame_rate = 1920, 1080, 30
KAGIT, MUR, SOLUK, KIRMIZI = "#E8D9B8", "#2b1d12", "#6b5640", "#b3261e"
config.background_color = KAGIT
FELL, GAR = "IM FELL English", "EB Garamond"
K = 1 / 30  # bir kare

def doku():
    p = AD / "doku.png"
    rng = np.random.default_rng(1485)
    w, h = 1920, 1080
    def blur(a, r): return np.asarray(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), float)
    leke = blur(rng.integers(0, 255, (h, w)), 60); leke = (leke - leke.mean()) / (leke.std() + 1e-6)
    ince = rng.normal(0, 1, (h, w))
    y, x = np.mgrid[0:h, 0:w]
    kenar = np.clip(((x - w/2) / (w/2))**2 + ((y - h/2) / (h/2))**2, 0, 2)
    v = 1 - 0.10 * kenar**1.5 + 0.018 * leke + 0.012 * ince
    base = np.array([0xE8, 0xD9, 0xB8], float)
    img = np.clip(base[None, None, :] * v[..., None] * np.array([1, 0.99, 0.96]), 0, 255).astype(np.uint8)
    Image.fromarray(img).save(p)
    return p

def tit(m, seed, amp=0.015):
    return m

def el_cizgi(a, b, seed, renk=MUR, w=4):
    rng = np.random.default_rng(seed)
    a, b = np.array(a, float), np.array(b, float)
    n = np.array([-(b-a)[1], (b-a)[0], 0]); n = n / (np.linalg.norm(n) + 1e-9)
    f1, f2 = rng.uniform(0, 6.3, 2)
    return ParametricFunction(lambda t: a + (b-a)*t + n*0.025*(np.sin(9*t+f1)+0.6*np.sin(21*t+f2)),
                              t_range=[0, 1, 0.02], color=renk, stroke_width=w)

def tarama(x0, x1, y0, h, renk=SOLUK):
    """x0..x1 aralığında y0'dan h yüksekliğe eğik tarama çizgileri."""
    g = VGroup()
    if h < 0.08: return g
    s = 0.17; xs = np.arange(x0 - h, x1, s)
    for i, xa in enumerate(xs):
        xb = xa + h
        ax, bx, ay, by = xa, xb, y0, y0 + h
        if ax < x0: ay += x0 - ax; ax = x0
        if bx > x1: by -= bx - x1; bx = x1
        if ax >= bx: continue
        g.add(Line([ax, ay, 0], [bx, by, 0], color=renk, stroke_width=1.6))
    return g

class Kaldirma(Scene):
    def construct(self):
        self.camera.background_color = KAGIT
        zem = ImageMobject(str(doku())); zem.height = config.frame_height; zem.move_to(ORIGIN)
        self.add(zem)
        ol = []
        def ev(kare, tur, guc): ol.append({"kare": int(kare), "tur": tur, "guc": guc})
        def t(f): return f * K

        baslik = Text("KALDIRMA KUVVETİ", font=FELL, color=MUR, font_size=44).move_to([0, 3.4, 0])
        alt = Text("neden hiz her seydir", font=GAR, slant=ITALIC, color=SOLUK, font_size=1) # yer tutucu, kullanilmaz
        alt = Text("yukarı iten kuvvet", font=GAR, slant=ITALIC, color=SOLUK, font_size=30).next_to(baslik, DOWN, buff=0.12)
        cizgi_b = el_cizgi([-2.6, 2.45, 0], [2.6, 2.45, 0], 3, SOLUK, 2.5)
        self.add(baslik, alt, cizgi_b)  # 0. karede dolu

        # formül parçaları
        def T(s, f=GAR, c=MUR, sz=112, **k): return Text(s, font=f, color=c, font_size=sz, **k)
        L = T("L", FELL); eq = T("="); yarim = T("½"); rho = T("ρ", slant=ITALIC)
        v2 = T("v²", slant=ITALIC); S = T("S", slant=ITALIC)
        CL = MarkupText('C<sub>L</sub>', font=GAR, color=MUR, font_size=112)
        parca = VGroup(L, eq, yarim, rho, v2, S, CL).arrange(RIGHT, buff=0.5, aligned_edge=DOWN).move_to([0, 1.35, 0])
        self.add(L, eq)   # 0. karede formül başlamış
        ev(0, "cizgi", 0.5)

        # 1) formül yazılır: 0 -> 66 kare
        kareler = [0]
        def oyna(*a, f, **k):
            self.play(*a, run_time=t(f), **k); kareler[0] += f
        sira = [(yarim, 12), (rho, 12), (v2, 12), (S, 12), (CL, 14)]
        for m, f in sira:
            ev(kareler[0], "tik", 0.45)
            oyna(Write(m, stroke_color=MUR), f=f, rate_func=linear)
        oyna(Wait(), f=6) if False else self.wait(t(6)); kareler[0] += 6   # 68
        # 2) v² kırmızı + el altı çizgisi: 68 -> 98
        ev(kareler[0], "vurus", 0.8)
        alt_c = el_cizgi(v2.get_corner(DL) + [-0.1, -0.16, 0], v2.get_corner(DR) + [0.1, -0.16, 0], 9, KIRMIZI, 5)
        oyna(v2.animate.set_color(KIRMIZI), Create(alt_c), f=14, rate_func=smooth)  # 82
        # açıklama
        ac = VGroup(Text("hız 2 katı  →  kaldırma 4 katı", font=GAR, slant=ITALIC, color=MUR, font_size=46)).move_to([0, 0.05, 0])
        ev(kareler[0], "cizgi", 0.4)
        oyna(FadeIn(ac, shift=UP*0.1), f=14)   # 96
        self.wait(t(4)); kareler[0] += 4  # 100

        # 3) iki çubuk
        taban_y = -3.2; birim = 0.5; xa, xb, gen = -1.9, 1.9, 1.5
        zemin = el_cizgi([-3.6, taban_y, 0], [3.6, taban_y, 0], 5, MUR, 3.5)
        h = ValueTracker(0)  # 0..1 büyüme
        def cubuk(x, deger):
            g = VGroup()
            def olustur():
                yuk = deger * birim * h.get_value()
                grup = VGroup()
                if yuk > 0.02:
                    r = Rectangle(width=gen, height=yuk, stroke_color=MUR, stroke_width=4, fill_color=KAGIT, fill_opacity=0).move_to([x, taban_y + yuk/2, 0])
                    grup.add(tarama(x - gen/2, x + gen/2, taban_y, yuk), r)
                return grup
            return always_redraw(olustur)
        c1, c4 = cubuk(xa, 1), cubuk(xb, 4)
        e1 = T("hız × 1", GAR, MUR, 32, slant=ITALIC).move_to([xa, taban_y - 0.32, 0])
        e2 = T("hız × 2", GAR, MUR, 32, slant=ITALIC).move_to([xb, taban_y - 0.32, 0])
        n1 = T("1", GAR, MUR, 56).move_to([xa, taban_y + 1*birim + 0.4, 0])
        n4 = T("4", GAR, KIRMIZI, 64).move_to([xb, taban_y + 4*birim + 0.4, 0])
        ev(kareler[0], "cizgi", 0.5)
        oyna(Create(zemin), FadeIn(e1), FadeIn(e2), f=12)  # 112
        self.add(c1, c4)
        ev(kareler[0], "hisirti", 0.4)
        oyna(h.animate.set_value(1), f=60, rate_func=rate_functions.ease_in_out_sine)  # 172
        ev(kareler[0] - 30, "tik", 0.4); ev(kareler[0], "vurus", 0.9)
        oyna(FadeIn(n1, scale=0.8), FadeIn(n4, scale=0.8), f=10)  # 182
        # sakin kapanış
        self.wait(t(240 - kareler[0]))
        (AD / "olaylar.json").write_text(json.dumps(sorted(ol, key=lambda e: e["kare"]), ensure_ascii=False, indent=1))
