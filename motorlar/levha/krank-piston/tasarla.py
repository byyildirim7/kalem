"""krank-piston: 8 kollu volan döner, krank pimi biyeli sürer, biyel koçu (kızak + mil + çekiç başı) yatay raylarda ileri-geri iter.
Dişli yok. Hareketli parçalar: V (volan, dönme), B (biyel), K (koç, kayma). Binme sırası: V < B < K (koç en önde).
python3 tasarla.py -> iskelet.png (a), iskelet-govde.png (b), geometri.json, ISTEK.md, ISTEK-govde.md"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tasarim_ortak import Iskelet, istek_yaz, geometri_yaz, KIR, W, H
C = [400, 520]; RJ, RI, GB = 230, 196, 46; RK = 150; FI0 = -40          # volan: jant dış/iç, göbek, krank yarıçapı, krank pimi açısı (derece)
PIM0 = [C[0] + RK * math.cos(math.radians(FI0)), C[1] + RK * math.sin(math.radians(FI0))]; L = 430
PIM1 = [PIM0[0] + math.sqrt(L * L - (C[1] - PIM0[1]) ** 2), C[1]]          # kayan pim: volan ekseni yüksekliğinde yatay doğru
x = PIM1[0]
KOC = [{"kutu": [x - 26, 478, x + 146, 562]}, {"kutu": [x + 146, 503, x + 334, 537]}, {"kutu": [x + 334, 466, x + 396, 574]}]
BIY = [{"kol": [*PIM0, *PIM1, 30, 26]}, {"daire": [*PIM0, 30]}, {"daire": [*PIM1, 26]}]
GOVDE = [{"kutu": [110, 880, 1470, 932]}, {"kutu": [378, 756, 422, 880]},                      # taban, volan ayağı
         {"kutu": [645, 452, 1150, 468]}, {"kutu": [645, 572, 1150, 588]},                     # raylar
         {"kutu": [672, 588, 708, 880]}, {"kutu": [1092, 588, 1128, 880]},                    # ray dikmeleri
         {"kutu": [1392, 440, 1452, 600]}, {"kutu": [1404, 600, 1440, 880]}]                  # örs + ayağı
def govde(s):
    for e in GOVDE: s.ilkel(e)
    for xx in range(150, 1450, 130): s.cizgi([(xx, 884), (xx + 40, 928)], 2)                  # taban damarı
def hareketli(s):
    s.kollu_cark(C, RJ, RI, GB, 8, 26, math.radians(FI0)); s.daire(PIM0, 20, 3)                # volan (bir kolunda krank pimi)
    for e in BIY: s.ilkel(e, dolgu=(232, 217, 184))
    s.daire(PIM0, 12, 1, dolgu=KIR); s.daire(PIM1, 10, 3)                                     # kırmızı: krank pimi başı
    for e in KOC: s.ilkel(e, dolgu=(232, 217, 184))
    s.daire(PIM1, 14, 3); s.cizgi([(x + 334 + 31, 466), (x + 334 + 31, 574)], 2)
a = Iskelet(); govde(a); hareketli(a); a.kaydet("iskelet.png")
b = Iskelet(); govde(b); b.kaydet("iskelet-govde.png")
u = [1, 0]
P = [dict(ad="V", tur="disk", c=C, r=RJ + 4, sx=1.0, sy=1.0, simetri=8, eklem=dict(tur="donme", pivot=C), hareket=dict(tur="donme", hiz=.3)),
     dict(ad="B", tur="sekil", sekil=BIY, pay=3, eklem=dict(tur="biyel"), hareket=dict(tur="biyel", krank="V", merkez=C, pim0=PIM0, pim1=PIM1, kayan="K")),
     dict(ad="K", tur="sekil", sekil=KOC, eklem=dict(tur="kayma", eksen=u), hareket=dict(tur="krank_kayma", krank="V", merkez=C, pim0=PIM0, pim1=PIM1, eksen=u))]
geometri_yaz(".", dict(W=W, H=H, tur="mekanizma", parcalar=P, govde=GOVDE, ipler=[],
    kuvvet_yolu=[[C[0] + 262 * math.cos(math.radians(t)), C[1] + 262 * math.sin(math.radians(t))] for t in range(-170, -40, 15)] + [[700, 420], [1000, 420], [1372, 420]],
    harfler=[["a", C[0] - 200, C[1] - 210], ["b", C[0] + 210, C[1] - 205], ["c", 1000, 395], ["d", 1372, 392]],
    yakinlasma=[round((PIM0[0] + PIM1[0]) / 2), 480, 1.45], olusum_sirasi=["V", "govde", "B", "K"]))
istek_yaz(".", "krank-piston", "bir volan-krank-biyel-koç düzeneği.",
    """- Solda 8 kollu büyük ahşap VOLAN: tam daire, kalın jant, demir çember; kollarından birinin üstünde (sağ üstte) KRANK PİMİ.
- Krank piminden sağa uzanan BİYEL KOLU: iki ucu yuvarlak göz, sağ ucu yatay iki RAY arasındaki kızağa bağlı.
- KOÇ: rayların arasında kayan kızak bloğu + uzun demir mil + sağ uçta ağır ÇEKİÇ BAŞI; en sağdaki örsün hemen önünde durur, ona değmez.
- Biyel volanın önünden geçer, koçun kızağı biyelin sağ ucunun önündedir (iskeletteki gibi).""",
    "biyelin sol gözündeki küçük krank pimi başı",
    "taban kirişi, volan ayağı (volanın altında kısa dikme), iki yatay ray ve iki ray dikmesi, en sağda örs ve ayağı. Volan, biyel ve koç YOK; raylar boş.")
print("krank-piston:", dict(PIM0=[round(v, 1) for v in PIM0], PIM1=[round(v, 1) for v in PIM1]))
