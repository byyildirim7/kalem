"""Önce geometri: makineyi kod tasarlar, sade çizgi iskeleti çizer (Codex'e referans), geometri.json yazar.
Görünüş: tam karşıdan (elevasyon) -> dönen parçalar tam daire, perspektif yok. Dönen parçaların önünde hiçbir şey yok.
python3 tasarla.py -> iskelet.png (1536x1024) + geometri.json"""
import json, math
from PIL import Image, ImageDraw
W, H = 1536, 1024; INK = (58, 39, 22); ZEMIN = (232, 217, 184); KIR = (164, 64, 42)
M = 10  # modül: diş adımı = pi*M ; yarıçap = z*M/2
def disli(z): return z * M / 2
# zincir (yan yana dış kavrama, hiçbir dönen parça başkasının önüne binmez): büyük dişli kollu çark W z60 -> A z24 -> B z36 -> C z16
P = {}
P["W"] = dict(tur="kollu-disli", c=(360, 560), z=60, r=disli(60), kol=8, rim=40, gobek=60)
def yan(ana, z, aci, ad, kol, gobek):
    a = P[ana]; r = disli(z); dd = a["r"] + r; t = math.radians(aci)
    P[ad] = dict(tur="disli", c=(round(a["c"][0] + dd * math.cos(t)), round(a["c"][1] + dd * math.sin(t))), z=z, r=r, kol=kol, gobek=gobek)
yan("W", 24, 0, "A", 4, 26); yan("A", 36, -40, "B", 6, 36); yan("B", 16, 25, "C", 0, 20)
im = Image.new("RGB", (W, H), ZEMIN); d = ImageDraw.Draw(im)
# gövde: yalnız arkada ve dönen dairelerin DIŞINDA (taban kirişi + iki ayak + millerin uç destekleri)
d.rectangle([90, 900, 1450, 950], outline=INK, width=4)
for x, ust in ((700, 720), (1300, 600)): d.rectangle([x - 25, ust, x + 25, 900], outline=INK, width=4)
def dis_ciz(c, z, r, w=4):
    ha, hd = M, 1.25 * M; pts = []
    for i in range(z):
        a0 = 2 * math.pi * i / z; s = 2 * math.pi / z
        for f, rr in ((0.0, r - hd), (0.18, r - hd), (0.30, r + ha), (0.55, r + ha), (0.67, r - hd), (1.0, r - hd)):
            a = a0 + f * s; pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    d.polygon(pts, outline=INK, width=w)
def daire(c, r, w=4): d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=INK, width=w)
for k, g in P.items():
    dis_ciz(g["c"], g["z"], g["r"]); ic = g["r"] - (g.get("rim") or 2.6 * M); daire(g["c"], ic); daire(g["c"], g["gobek"]); daire(g["c"], 9, 3)
    for n in range(g["kol"]):
        a = 2 * math.pi * n / g["kol"]
        d.line([(g["c"][0] + g["gobek"] * math.cos(a), g["c"][1] + g["gobek"] * math.sin(a)),
                (g["c"][0] + ic * math.cos(a), g["c"][1] + ic * math.sin(a))], fill=INK, width=14 if k == "W" else 10)
# tek kırmızı vurgu: en sondaki dişlinin göbeği
g = P["C"]; d.ellipse([g["c"][0] - 12, g["c"][1] - 12, g["c"][0] + 12, g["c"][1] + 12], fill=KIR)
im.save("iskelet.png")
json.dump(dict(W=W, H=H, modul=M, parcalar=P, surucu="W", zincir=[["W", "A"], ["A", "B"], ["B", "C"]]),
          open("geometri.json", "w", encoding="utf-8"), indent=1)
print({k: (v["c"], round(v["r"])) for k, v in P.items()})
