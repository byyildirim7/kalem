"""palanga: bir sabit (F) + bir hareketli (M) makara. İp tavandaki kancadan iner, M'nin altından dolanır, F'nin üstünden geçer,
ucundaki tutamak (H) aşağı çekilir. Sürücü d = yükün kalkışı (px): H 2d iner, yük ve M d kalkar (ip boyu sabit).
Makaralar ip hızıyla döner: F açısal hız 2v/r (saat yönü), M v/r (ters; sol kol duran ipte yuvarlanır).
İşaretler (kodla): kırmızı F (G/2 boyunda) ve G okları, soluk ölçü çubukları: çekilen ip boyu ve yanında 2 x yük kalkışı."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tasarim_ortak import Iskelet, istek_yaz, geometri_yaz, KIR, W, H
RI, RJ = 56, 64                                    # ip oluğu yarıçapı, jant dış yarıçapı
F = [700, 230]; M = [F[0] - 2 * RI, 600]; AX = M[0] - RI; HX = F[0] + RI; HY = 360; DMAX = 180; ZEMIN = 900
YUK = [{"kol": [M[0], M[1], M[0], 730, 18, 18]}, {"daire": [M[0], M[1], 16]}, {"kutu": [M[0] - 80, 730, M[0] + 80, 880]}]
TUT = [{"kutu": [HX - 34, HY, HX + 34, HY + 22]}, {"daire": [HX, HY - 4, 9]}]
GOVDE = [{"kutu": [130, 70, 1060, 118]}, {"kutu": [140, 118, 180, ZEMIN]}, {"kutu": [1010, 118, 1050, ZEMIN]},
         {"kutu": [60, ZEMIN, 1140, 935]}, {"kutu": [F[0] - 10, 118, F[0] + 10, F[1] - RJ + 2]}, {"daire": [AX, 128, 9]}]
def govde(s):
    for e in GOVDE: s.ilkel(e)
def makara(s, c): s.kollu_cark(c, RJ, RI - 10, 16, 6, 10); s.daire(c, RI, 2)
def hareketli(s):
    makara(s, F); makara(s, M)
    s.cizgi([(AX, 128), (AX, M[1])], 3); s.cizgi([(M[0] + RI, M[1]), (F[0] - RI, F[1])], 3); s.cizgi([(HX, F[1]), (HX, HY)], 3)
    s.d.arc([M[0] - RI, M[1] - RI, M[0] + RI, M[1] + RI], 0, 180, fill=(58, 39, 22), width=3); s.d.arc([F[0] - RI, F[1] - RI, F[0] + RI, F[1] + RI], 180, 360, fill=(58, 39, 22), width=3)
    for e in YUK: s.ilkel(e, dolgu=(232, 217, 184))
    s.cizgi([(M[0] - 80, 780), (M[0] + 80, 780)], 2); s.cizgi([(M[0] - 20, 730), (M[0] - 20, 780)], 2); s.cizgi([(M[0] + 30, 780), (M[0] + 30, 880)], 2)
    for e in TUT: s.ilkel(e, dolgu=KIR if "kutu" in e else None)
a = Iskelet(); govde(a); hareketli(a); a.kaydet("iskelet.png")
b = Iskelet(); govde(b); b.kaydet("iskelet-govde.png")
SUR = {"d": [[0, 0], [45, 0], [225, DMAX], [240, DMAX]]}
PAR = [dict(ad="F", tur="sekil", sekil=[{"daire": [*F, RJ + 2]}], c=F, r=RJ + 2, sx=1.0, sy=1.0, simetri=6, eklem=dict(tur="donme", pivot=F),
            hareket=dict(tur="dogrusal", surucu="d", donme=2 / RI, merkez=F)),
       dict(ad="M", tur="sekil", sekil=[{"daire": [*M, RJ + 2]}], c=M, r=RJ + 2, sx=1.0, sy=1.0, simetri=6, eklem=dict(tur="donme+kayma", pivot=M, eksen=[0, -1]),
            hareket=dict(tur="dogrusal", surucu="d", oteleme=[0, -1], donme=-1 / RI, merkez=M)),
       dict(ad="Y", tur="sekil", sekil=YUK, eklem=dict(tur="kayma", eksen=[0, -1]), hareket=dict(tur="dogrusal", surucu="d", oteleme=[0, -1])),
       dict(ad="H", tur="sekil", sekil=TUT, notr=True, eklem=dict(tur="kayma", eksen=[0, 1]), hareket=dict(tur="dogrusal", surucu="d", oteleme=[0, 2]))]
IP = [dict(ad="ip", tur="makara", sonra="M", kalinlik=3, kanca=False, bant=29,
           yol=[{"sabit": [AX, 128]}, {"makara": "M", "yan": "alt", "r": RI}, {"makara": "F", "yan": "ust", "r": RI}, {"uc": {"parca": "H", "nokta": [HX, HY - 4]}}])]
ISA = [dict(tur="ok", parca="H", nokta=[HX + 50, HY - 70], yon=[0, 1], boy=60),                    # F = G/2
       dict(tur="ok", parca="Y", nokta=[M[0] - 115, 760], yon=[0, 1], boy=120),                   # G
       dict(tur="olcu", parca="H", nokta=[HX, HY - 4], x=HX + 95),                                # çekilen ip boyu
       dict(tur="olcu", parca="Y", nokta=[M[0], 730], x=M[0] - 150),                              # yük kalkışı
       dict(tur="olcu_kat", parca="Y", nokta=[M[0], 730], x=HX + 117, y0=HY - 4, kat=2)]          # 2 x yük kalkışı, çekilen ipin yanında
DERS = dict(tur="palanga", G=20, F=10, ok_olcek=6.0, AX=AX, HX=HX, HY=HY, M=M, Fc=F, RI=RI, RJ=RJ, birim=DMAX, birim_m=.5, dmax=DMAX, olusum_olcek=round(5.6 / 14.33, 3),
            yuk_kutu=[M[0] - 80, 730, M[0] + 80, 880], tut_kutu=[HX - 34, HY, HX + 34, HY + 22])
geometri_yaz(".", dict(W=W, H=H, tur="mekanizma", parcalar=PAR, govde=GOVDE, ipler=IP, suruculer=SUR, isaretler=[], ders=DERS, smax=400,
    zaman=dict(yol=[9999, 10000], yakin=[9999, 10000, 10001, 10002]), kuvvet_yolu=None, harfler=[], yakinlasma=None,
    olusum_sirasi=["F", "govde", "M", "Y", "H"], kontrol_kareleri=[60, 150, 255, 330, 399], yakin_kareler=[0, 120, 255, 399],
    fizik=dict(tur="palanga", ip="ip", cekilen=["H", [HX, HY - 4]], yuk=["Y", [M[0], 730]])))
istek_yaz(".", "palanga", "bir palanga (bir sabit, bir hareketli makara) ile ağır taş kaldırma düzeneği.",
    """- Üstte yatay tavan kirişi, iki yanında dikmeler, altta zemin.
- Tavana asılı SABİT MAKARA (sağ üstte) ve onun altında, sol aşağıda HAREKETLİ MAKARA: ikisi de tam daire, 6 kollu, kenarında ip oluğu.
- TEK DÜZ İP: tavandaki kancadan dikey iner, hareketli makaranın altından dolanır, dikey çıkıp sabit makaranın üstünden geçer, sağda dikey iner; ucunda küçük yatay TUTAMAK. İp çizgileri iskeletteki yerlerde, dümdüz dikey.
- Hareketli makaranın göbeğinden inen demir ÇATAL/askı ve ona asılı köşeli ağır TAŞ BLOK (yük).""",
    "ipin ucundaki küçük tutamak",
    "üstte yatay tavan kirişi, iki yan dikme, altta zemin kirişi, tavandan inen kısa askı kayışı ve tavandaki küçük kanca halkası. Makaralar, ip, taş blok, tutamak YOK; o alanlar boş kâğıt.")
print("palanga tamam")
