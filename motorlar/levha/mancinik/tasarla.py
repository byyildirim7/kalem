"""mancinik: Leonardo tarzı mancınık. Soldaki tutamaklı çark (vinç) dönünce davula ip sarılır, ip atış kolunun ucunu aşağı çeker
(kol kurulur). Mandal bırakılır: ip kancası düşer, kol yukarı fırlar ve dayanağa çarpar, kepçedeki kırmızı taş uçar, sağda yere düşer.
Hareketli parçalar: C (çark, açısı ipten), Q (atış kolu, anahtar kareler + çarpma), S (taş, mermi). İp kodla çizilir.
Binme sırası: C < ip < Q < S. python3 tasarla.py -> iskelet.png, iskelet-govde.png, geometri.json, ISTEK.md, ISTEK-govde.md"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tasarim_ortak import Iskelet, istek_yaz, geometri_yaz, KIR, W, H
from mekanizma import teget
P = [880, 640]; A0 = -145; LK = 470; LB = 70                       # kol pivotu, durgun açı (derece, görüntü), kepçe uzaklığı, arka uç
u = (math.cos(math.radians(A0)), math.sin(math.radians(A0)))
pt = lambda d: [P[0] + d * u[0], P[1] + d * u[1]]
KEP = pt(LK); BAG = pt(445); RT = 24                                # kepçe merkezi = taş merkezi, ipin bağlandığı nokta, taş yarıçapı
KOL = [{"kol": [*pt(-LB), *pt(LK - 30), 40, 26]}, {"daire": [*P, 34]}, {"daire": [*KEP, 40]}]
CC = [200, 760]; RD = 44                                           # çark merkezi, davul yarıçapı
ZEMIN = 935
GOVDE = [{"kutu": [60, ZEMIN, 1480, 970]},                                          # zemin kirişi
         {"kol": [880, 640, 772, ZEMIN, 34, 40]}, {"kol": [880, 640, 988, ZEMIN, 34, 40]},   # A ayaklar (kol pivotu)
         {"kutu": [930, 430, 962, 700]}, {"kutu": [904, 440, 930, 488]},                 # dayanak dikmesi + yastık
         {"kutu": [186, 922, 214, ZEMIN]}]                                               # çark ayağı
def govde(s):
    for e in GOVDE: s.ilkel(e)
    for xx in range(90, 1460, 110): s.cizgi([(xx, ZEMIN + 4), (xx + 30, 966)], 2)
def hareketli(s):
    s.kollu_cark(CC, 112, 94, 30, 8, 18, 0, tutamak=(112, 150, 14)); s.daire(CC, RD, 3)          # tutamaklı çark + davul
    E = BAG; T = teget(CC, RD, E, -1); s.cizgi([T, E], 3)                                         # ip
    for e in KOL: s.ilkel(e, dolgu=(232, 217, 184))
    s.daire(P, 12, 3); s.daire(KEP, 30, 2)
    s.daire(KEP, RT, 3, dolgu=KIR)                                                                # kırmızı taş
a = Iskelet(); govde(a); hareketli(a); a.kaydet("iskelet.png")
b = Iskelet(); govde(b); b.kaydet("iskelet-govde.png")
# ip hangi yandan çıkar (üstten), sarma yönü: davul değme noktası ipten uzaklaşacak yönde döner
T0 = teget(CC, RD, BAG, -1); r_ = (T0[0] - CC[0], T0[1] - CC[1]); v = (-r_[1], r_[0]); d = (BAG[0] - T0[0], BAG[1] - T0[1]); yon = -1 if v[0] * d[0] + v[1] * d[1] > 0 else 1
BIRAK = 236; FIR = 256
PAR = [dict(ad="C", tur="disk", c=CC, r=164, sx=1.0, sy=1.0, simetri=8, eklem=dict(tur="donme", pivot=CC), hareket=dict(tur="ip_sarma", ip="ip")),
       dict(ad="Q", tur="sekil", sekil=KOL, pivot=P, eklem=dict(tur="donme", pivot=P),
            hareket=dict(tur="anahtar", pivot=P, kareler=[[0, 0], [40, 0], [220, -40], [BIRAK, -40], [FIR, 55, "ivme"]], carpma=[FIR, 6, 5, 8])),
       dict(ad="S", tur="sekil", sekil=[{"daire": [*KEP, RT + 2]}], merkez=KEP, yaricap=RT,
            eklem=dict(tur="bagli"), hareket=dict(tur="mermi", tasiyici="Q", birak=FIR, ucus=30, hedef=1270, zemin=ZEMIN, aci=35))]
IP = [dict(ad="ip", davul="C", r=RD, isaret=-1, yon=yon, uc=dict(parca="Q", nokta=BAG), birak=BIRAK, g=2.2, zemin=ZEMIN - 4, sonra="C", kalinlik=3)]
geometri_yaz(".", dict(W=W, H=H, tur="mekanizma", parcalar=PAR, govde=GOVDE, ipler=IP, kuvvet_yolu="S", smax=345,
    zaman=dict(yol=[FIR, FIR + 34], yakin=[50, 95, 185, 228]),
    harfler=[["a", CC[0] + 60, CC[1] - 210], ["b", P[0] + 60, P[1] + 40], ["c", P[0] - 70, P[1] - 520], ["d", 1290, ZEMIN - 90]],
    yakinlasma=[360, 640, 1.35], olusum_sirasi=["C", "govde", "Q", "S"],
    kontrol_kareleri=[120, 228, 250, 262, 272, 300], yakin_kareler=[0, 228, 262, 300]))
istek_yaz(".", "mancinik", "Leonardo tarzı bir mancınık (vinçle kurulan atış kolu).",
    """- Solda TUTAMAKLI ÇARK: tam daire jant, 8 kol, jantın dışına taşan 8 tutamak (gemi dümeni gibi), ortada ipin sarıldığı DAVUL.
- Davuldan çıkan tek düz İP, atış kolunun ucuna bağlı (iskeletteki düz çizgi, aynı yerde).
- Ortada uzun ahşap ATIŞ KOLU: sağdaki A biçimli ayakların tepesindeki mile takılı, sol yukarı doğru uzanır; ucunda yuvarlak KEPÇE.
- Kepçenin içinde yuvarlak TAŞ.
- Kolun sağında dikey dayanak dikmesi ve yastığı (kol kalkınca buna çarpar).""",
    "kepçedeki yuvarlak taş (tamamı kırmızı tebeşir)",
    "uzun zemin kirişi, ortada A biçimli iki ayak (tepede mil yatağı), sağında dayanak dikmesi ve yastığı, solda çarkın altındaki kısa ayak. Çark, ip, atış kolu, kepçe ve taş YOK; o alanlar boş kâğıt.")
print("mancinik:", dict(KEP=[round(v, 1) for v in KEP], BAG=[round(v, 1) for v in BAG], yon=yon))
