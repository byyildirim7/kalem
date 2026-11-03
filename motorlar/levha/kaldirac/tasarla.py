"""kaldirac (ders sürümü): destek noktası O üstünde dönen kiriş, 4 eşit bölme: kuvvet kolu 3 bölme (a = 600 px), yük kolu 1 bölme (b = 200 px).
Uzun kolun ucuna küçük giriş kuvveti F, kısa kolun ucunda asılı yük G. Açı: sin(teta) = 0,2 -> yük h = 0,2 bölme, F'nin yolu x = 0,6 bölme.
Yük nötr (sepya); kırmızı YALNIZ kuvvet oklarında. Etiketler, bölme çentikleri, ölçü çizgileri ve sonuç kartı kodla (levha.py etiket katmanı)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tasarim_ortak import Iskelet, istek_yaz, geometri_yaz, W, H
P = [820, 560]; B = 200; L1, L2 = 3 * B, 1 * B; ZEMIN = 860; YX = P[0] + L2; KAL = 34
KOL = [{"kol": [P[0] - L1, P[1], P[0] + L2, P[1], KAL, KAL]}, {"daire": [*P, 22]}]
YUK = [{"kol": [YX, P[1] + 10, YX, 645, 9, 9]}, {"kutu": [YX - 70, 640, YX + 70, 780]}]
GOVDE = [{"cokgen": [[P[0], P[1] + 19], [P[0] - 100, ZEMIN], [P[0] + 100, ZEMIN]]}, {"kutu": [160, ZEMIN, 1380, 900]}]
def govde(s):
    for e in GOVDE: s.ilkel(e)
def hareketli(s):
    for e in KOL: s.ilkel(e, dolgu=(232, 217, 184))
    s.daire(P, 9, 3)
    for e in YUK: s.ilkel(e, dolgu=(232, 217, 184))
    for y in (687, 734): s.cizgi([(YX - 70, y), (YX + 70, y)], 2)
    s.cizgi([(YX - 10, 640), (YX - 10, 687)], 2); s.cizgi([(YX + 25, 687), (YX + 25, 734)], 2); s.cizgi([(YX - 30, 734), (YX - 30, 780)], 2)
a = Iskelet(); govde(a); hareketli(a); a.kaydet("iskelet.png")
b = Iskelet(); govde(b); b.kaydet("iskelet-govde.png")
A = -math.degrees(math.asin(.2))                       # sol uç aşağı: yük h = b * 0,2
PAR = [dict(ad="L", tur="sekil", sekil=KOL, pivot=P, eklem=dict(tur="donme", pivot=P),
            hareket=dict(tur="anahtar", pivot=P, kareler=[[0, 0], [20, 0], [70, A], [120, 0]])),             # 1 çevrim, yatay dengede biter
       dict(ad="Y", tur="sekil", sekil=YUK, eklem=dict(tur="takip"), hareket=dict(tur="takip", parca="L", nokta=[YX, P[1]]))]
ust = P[1] - KAL / 2                                   # kirişin üst yüzü
DERS = dict(tur="kaldirac", pivot=P, bolme=B, sol=3, sag=1, G=30, F=10, kalinlik=KAL, yuk_nokta=[YX, P[1]], sol_uc=[P[0] - L1, P[1]],
            ok_olcek=5.0,                               # 1 N = 5 px: G 150 px, F 50 px
            kareler_lise={"L": [[0, 0], [20, 0], [70, A], [120, 0]]}, smax_lise=200, olusum_olcek=round(5.6 / 14.33, 3),
            yuk_kutu=[YX - 70, 640, YX + 70, 780])   # lise: iki çevrim, YATAY dengede biter
geometri_yaz(".", dict(W=W, H=H, tur="mekanizma", parcalar=PAR, govde=GOVDE, ipler=[], isaretler=[], ders=DERS, smax=450,
    zaman=dict(yol=[9999, 10000], yakin=[9999, 10000, 10001, 10002]), kuvvet_yolu=None, harfler=[], yakinlasma=None,
    olusum_sirasi=["L", "govde", "Y"], kontrol_kareleri=[60, 140, 200, 280, 420, 449], yakin_kareler=[0, 140, 280, 420],
    fizik=dict(tur="kaldirac", parca="L", pivot=P, uc1=[P[0] - L1, P[1]], uc2=[P[0] + L2, P[1]])))
istek_yaz(".", "kaldirac", "bir kaldıraç: üçgen destek üstünde uzun kiriş, kısa kolunda asılı ağır taş.",
    """- Altta zemin kirişi, ortada üçgen DESTEK (ahşap takoz, taramalı); tepesi kirişin göbeğindeki mile değer.
- Yatay, düz, uzun ahşap KİRİŞ: destek üstündeki milde döner; sol tarafı uzun, sağ tarafı kısa. Tam yatay, iskeletteki boyda ve kalınlıkta.
- Kısa kolun tam ucundan inen kısa demir askı ve ona asılı köşeli ağır TAŞ BLOK (yük), taş örgüsü ve taramayla, sepya.""",
    None, "zemin kirişi ve ortada üçgen destek takozu. Kiriş, askı ve taş YOK; o alanlar boş kâğıt.")
print("kaldirac (ders) tamam, teta =", round(A, 3))
