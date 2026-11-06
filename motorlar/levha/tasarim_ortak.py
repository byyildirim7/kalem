"""tasarla.py'lerin ortak çizim + yazım yardımcıları: iskelet (a: tam makine) ve iskelet-govde (b: hareketli parçalar yok),
geometri.json, ISTEK.md / ISTEK-govde.md. Çizgi iskeleti PIL ile, 1536x1024, sepya mürekkep, düz zemin."""
import json, math
from PIL import Image, ImageDraw
import numpy as np
from mekanizma import ilkel_cokgen
W, H = 1536, 1024; INK = (58, 39, 22); ZEMIN = (232, 217, 184); KIR = (164, 64, 42)

class Iskelet:
    def __init__(self): self.im = Image.new("RGB", (W, H), ZEMIN); self.d = ImageDraw.Draw(self.im)
    def ilkel(self, e, w=4, dolgu=None):
        P = [tuple(map(float, p)) for p in ilkel_cokgen(e)]
        if dolgu: self.d.polygon(P, fill=dolgu)
        self.d.line(P + [P[0]], fill=INK, width=w, joint="curve")
    def daire(self, c, r, w=4, dolgu=None):
        self.d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=INK, width=w, fill=dolgu)
    def cizgi(self, P, w=4, renk=INK): self.d.line([tuple(map(float, p)) for p in P], fill=renk, width=w, joint="curve")
    def kollu_cark(self, c, r_dis, r_ic, gobek, n, kol_w, aci0=0, tutamak=None):
        self.daire(c, r_dis); self.daire(c, r_ic); self.daire(c, gobek); self.daire(c, 9, 3)
        for k in range(n):
            a = aci0 + 2 * math.pi * k / n; u = (math.cos(a), math.sin(a)); v = (-u[1], u[0])
            for s in (-1, 1):
                self.cizgi([(c[0] + gobek * u[0] + s * kol_w / 2 * v[0], c[1] + gobek * u[1] + s * kol_w / 2 * v[1]),
                            (c[0] + r_ic * u[0] + s * kol_w / 2 * v[0], c[1] + r_ic * u[1] + s * kol_w / 2 * v[1])], 3)
            if tutamak:                                   # dışarı taşan tutamak (gemi dümeni gibi)
                r1, r2, tw = tutamak; self.ilkel({"kol": [c[0] + r1 * u[0], c[1] + r1 * u[1], c[0] + r2 * u[0], c[1] + r2 * u[1], tw, tw]}, 3)
                self.daire((c[0] + r2 * u[0], c[1] + r2 * u[1]), tw * .8, 3)
    def kaydet(self, yol): self.im.save(yol)

ORTAK_STIL = """## Stil
- Sepya mürekkep #3A2716, düz lekesiz parşömen zemin #E8D9B8 (zemine doku, leke, vinyet YOK).
- Ahşap ve demir: kalın el çizimi kontur, yoğun tarama (hatching) ile gölge, ahşap damarı, cıvata ve kama ayrıntısı; Leonardo'nun makine etütleri gibi zengin ama okunur.
- Soluk pergel daireleri ve merkez artıları (inşa çizgisi) eklenebilir, ama yalnız boş kâğıtta; hiçbir parçanın içine değil.
- YAZI YOK: harf, rakam, sahte Latince, imza yok. İnsan, el, yüz yok. Fotoğraf gerçekçiliği, 3D render, renk YOK."""

def istek_yaz(klasor, baslik, makine, parcalar_md, kirmizi, govde_md):
    a = f"""# Codex görsel isteği · LEVHA {baslik} (a: tam makine)

Ekteki `iskelet.png` bir mekanizmanın sade teknik çizimidir: {makine}
Bunu **Leonardo da Vinci defteri tarzında el çizimi bir gravüre çevir: `levha.png`**.

## EN ÖNEMLİ KURAL: geometri birebir korunur
- Her parçanın YERİ, BOYU, AÇISI ve BİÇİMİ iskeletle aynı kalacak. Çizimi kaydırma, büyütme, kırpma, döndürme YOK. Görsel boyutu 1536x1024, iskeletle üst üste konunca parçalar örtüşmeli.
- Görünüş TAM KARŞIDAN (yan elevasyon): çarklar tam daire, perspektif yok, eğik değil.
{parcalar_md}
- Hareketli parçaların önüne başka hiçbir şey (dikme, kiriş, mil, gölge) ÇİZME. Gövde parçaları yalnız iskeletteki yerlerde.
- Kollar eşit aralıklı, düzgün.

{ORTAK_STIL}
{"- KIRMIZI YOK: bu görselde kırmızı hiç kullanılmaz; her şey sepya." if kirmizi is None else "- Tek kırmızı tebeşir vurgusu (#A4402A): " + kirmizi + ", iskelettekiyle aynı yerde ve boyda. Başka hiçbir yerde kırmızı yok."}

Bitince `levha.png` olarak bu klasöre kaydet ve `bitti.txt` yaz.
"""
    b = f"""# Codex görsel isteği · LEVHA {baslik} (b: YALNIZ GÖVDE)

Ekteki `iskelet-govde.png`, bir makinenin hareketli parçaları ÇIKARILMIŞ gövdesidir: {govde_md}
Bunu **Leonardo da Vinci defteri tarzında el çizimi bir gravüre çevir: `govde.png`**.

## EN ÖNEMLİ KURAL: geometri birebir korunur, eklenen bir şey yok
- Her gövde parçasının YERİ, BOYU ve BİÇİMİ iskeletle aynı kalacak. Kaydırma, büyütme, kırpma, döndürme YOK. 1536x1024.
- İskelette OLMAYAN hiçbir parça ekleme: çark, kol, çubuk, ip, taş, dişli YOK. İskeletteki boş kâğıt alanlar boş ve düz kâğıt kalsın (oraya sonra başka parçalar konacak).
- Görünüş TAM KARŞIDAN (yan elevasyon), perspektif yok.

{ORTAK_STIL}
- KIRMIZI YOK: bu görselde kırmızı hiç kullanılmaz.

Bitince `govde.png` olarak bu klasöre kaydet ve `bitti-govde.txt` yaz.
"""
    open(f"{klasor}/ISTEK.md", "w", encoding="utf-8").write(a); open(f"{klasor}/ISTEK-govde.md", "w", encoding="utf-8").write(b)

def geometri_yaz(klasor, G): json.dump(G, open(f"{klasor}/geometri.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
