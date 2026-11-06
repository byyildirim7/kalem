#!/usr/bin/env python3
"""Render edilmiş ders videosunun SON karesinden sayıları ölçer (çözücüden bağımsız), cikti/<ad>-v4-olcum.txt sonuna yazar.
Renk = taraf: kırmızı (F, d1, x), çivit (G, d2, h), okra (P). Oklar ve ↔ ölçüler renk maskesinin bileşenlerinden; px -> N (ok ölçeği), px -> m (bölme/birim).
  python3 ders_olc.py <levhalar/ad.json> <video adı>"""
import json, sys, math, cv2, numpy as np
T = json.load(open(sys.argv[1], encoding="utf-8")); V = sys.argv[2]; yol = f"cikti/{V}-v4-dur.mp4"; SC = 1080 / 1024; OX = (1920 - 1536 * SC) / 2
c = cv2.VideoCapture(yol); NK = int(c.get(cv2.CAP_PROP_FRAME_COUNT)); c.set(cv2.CAP_PROP_POS_FRAMES, NK - 1); _, f = c.read()
hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); Hh, Ss, Vv = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
if T.get("stil") == "blueprint":                     # amber (giriş), camgöbeği (çıkış), açık sarı (P)
    MAS = {"r": (Hh >= 10) & (Hh <= 22) & (Ss > 120) & (Vv > 170), "c": (Hh > 84) & (Hh < 98) & (Ss > 90) & (Vv > 160), "o": (Hh >= 23) & (Hh <= 33) & (Ss > 80) & (Vv > 200)}
else: MAS = {"r": ((Hh < 10) | (Hh > 170)) & (Ss > 90) & (Vv > 70), "c": (Hh > 95) & (Hh < 125) & (Ss > 60) & (Vv > 50), "o": (Hh > 11) & (Hh < 26) & (Ss > 180) & (Vv > 110)}
def bil(k):
    n, l, st, _ = cv2.connectedComponentsWithStats(MAS[k].astype(np.uint8), 8)
    return [dict(x=((x + w / 2) - OX) / SC, y=(y + hh / 2) / SC, w=w / SC, h=hh / SC, x0=(x - OX) / SC, y0=y / SC, x1=(x + w - OX) / SC, y1=(y + hh) / SC) for x, y, w, hh, a in st[1:] if a > 25]
def dusey(k, x, tol=8, en_az=15, cubuk=False):
    C = [b for b in bil(k) if abs(b["x"] - x) < tol and b["h"] > en_az and b["w"] < 30]
    if not C: return None
    b = dict(max(C, key=lambda b: b["h"]))
    if cubuk: b["h"] -= 2                             # ↔ yol çubuğu: çizgi kalınlığı
    return b
def yatay(k, y, x0, x1, tol=10):
    """aynı satırdaki parçaların birleşimi (başka renkli bir kesikli çizgi ölçüyü bölebilir)"""
    C = [b for b in bil(k) if abs(b["y"] - y) < tol and b["w"] > 30 and x0 - 20 < b["x0"] and b["x1"] < x1 + 20]
    if not C: return None
    a_, b_ = min(c["x0"] for c in C), max(c["x1"] for c in C); return dict(x0=a_, x1=b_, w=b_ - a_ - 2)          # 2 px: çizgi kalınlığı (iki uç)
def capraz(k, x0, x1, y0, y1):
    C = [b for b in bil(k) if x0 < b["x"] < x1 and y0 < b["y"] < y1 and b["w"] > 40 and b["h"] > 30]; return max(C, key=lambda b: b["w"] * b["h"]) if C else None
d = T["ders"]; out = [f"RENDER ÖLÇÜMÜ ({V}, son kare {NK - 1})"]; lise = "lise" in V; yaz = lambda s: out.append("  " + s)
if d["tur"] == "disli":
    P_ = [p for p in T["parcalar"] if p["tur"] == "disli"]; o_ = 1.
    for p in P_[1:]: o_ *= p["hareket"]["oran"]
    yaz(f"devir oranı (çözücü, bağlı oranların çarpımı) n_son/n_giriş = {o_:+.4f} (kartta {P_[0]['Z']}/{P_[-1]['Z']} = {P_[0]['Z'] / P_[-1]['Z']:.4f}; işaret = yön)")
    # render karesinden: diş bandının kutupsal açılımı, ardışık karelerde açı kayması (faz korelasyonu), sürekli dönüş bölümünde toplam
    OK_ = T["ders"].get("olusum_olcek", 1.); OL = int(round(430 * OK_)); AC = np.arange(0, 360, .25)
    def bant(f, p, ic=False):                         # ic: kol bandı (yavaş dişli, uzun periyot), değilse diş bandı
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32); cx, cy = OX + p["c"][0] * SC, p["c"][1] * SC; th = np.radians(AC)
        rs = (np.linspace(p["r"] * .35, p["r"] * .8, 40) if ic else np.linspace(p["r"] - 24, p["r"] - 4, 24)) * SC
        return cv2.remap(g, (cx + np.cos(th)[None] * rs[:, None]).astype(np.float32), (cy + np.sin(th)[None] * rs[:, None]).astype(np.float32), cv2.INTER_LINEAR)
    cap = cv2.VideoCapture(yol); cap.set(cv2.CAP_PROP_POS_FRAMES, OL + 60); top = {P_[0]["ad"]: 0., P_[-1]["ad"]: 0.}; onc = {}
    for i in range(OL + 60, OL + 281):
        ok, f = cap.read()
        if not ok: break
        for ad, p, adim_, ic in ((P_[0]["ad"], P_[0], 10, True), (P_[-1]["ad"], P_[-1], 2, False)):
            if (i - OL - 60) % adim_: continue
            b = bant(f, p, ic)
            if ad in onc: (dx, _), _ = cv2.phaseCorrelate(onc[ad], b); top[ad] += dx * .25
            onc[ad] = b
    w_, c_ = top[P_[0]["ad"]], top[P_[-1]["ad"]]
    yaz(f"render karesinden (kare +60..+280, diş bandı faz korelasyonu): {P_[0]['ad']} {w_:+.2f}°, {P_[-1]['ad']} {c_:+.2f}° -> n_son/n_giriş = {c_ / w_:+.4f} (kartta −{P_[0]['Z'] / P_[-1]['Z']:.2f}; sapma %{abs(abs(c_ / w_) - P_[0]['Z'] / P_[-1]['Z']) / (P_[0]['Z'] / P_[-1]['Z']) * 100:.2f}, işaret ters yön)")
    for k, ad_ in (("r", "giriş yayı"), ("c", "çıkış yayı")):
        C = [b for b in bil(k) if b["w"] > 40 or b["h"] > 40]; yaz(f"{ad_}: {len(C)} bileşen, en büyüğü {max((b['w'] for b in C), default=0):.0f}x{max((b['h'] for b in C), default=0):.0f} px")
elif d["tur"] == "kaldirac":
    agir, acili = "agirlik" in V, "acili" in V; S = 3.0 if agir else d["ok_olcek"]; G = 50 if agir else d["G"]; F = 20 if acili else d["F"]
    P = d["pivot"]; B = d["bolme"]; L1, L2 = d["sol"] * B, d["sag"] * B; m = d.get("bolme_m", .5); yk = d.get("yuk_kutu"); yo = P[1] - 112; gx = P[0] + L2 + 110
    g = dusey("c", gx); fo = capraz("r", P[0] - L1 - 140, P[0] - L1 + 10, P[1] - 120, P[1] - 10) if acili else dusey("r", P[0] - L1)
    if g: yaz(f"G oku {g['h'] - 4:.1f} px = {(g['h'] - 4) / S:.2f} N (yazan {G} N); kolun açısı (G okunun üstü tasarım 640'a göre): {math.degrees(math.asin(np.clip((640 - g['y0'] - .5) / L2, -1, 1))):+.2f}°")
    if fo and acili:                                  # açılı F: bileşen piksellerinin F doğrultusundaki (30°) izdüşüm uzunluğu - uç payı
        ys_, xs_ = np.nonzero(MAS["r"][int(fo["y0"] * SC):int(fo["y1"] * SC) + 1, int(fo["x0"] * SC + OX):int(fo["x1"] * SC + OX) + 1]); u = np.array([math.cos(math.radians(30)), math.sin(math.radians(30))])
        pr = (xs_ * u[0] + ys_ * u[1]) / SC; L = pr.max() - pr.min() - 4; yaz(f"F oku (30° doğrultusunda izdüşüm) {L:.1f} px = {L / S:.2f} N (yazan {F} N)")
    elif fo: L = fo["h"] - 4; yaz(f"F oku {L:.1f} px = {L / S:.2f} N (yazan {F} N)")
    d1, d2 = yatay("r", yo, P[0] - L1, P[0]), yatay("c", yo, P[0], P[0] + L2)
    if d1: yaz(f"d₁ ↔ {d1['w']:.1f} px = {d1['w'] / B * m:.3f} m (yazan {sayi_ if (sayi_ := str(d['sol'] * m).replace('.', ',')) else ''} m; dik uzaklık, yatay)")
    if d2: yaz(f"d₂ ↔ {d2['w']:.1f} px = {d2['w'] / B * m:.3f} m (yazan {str(d['sag'] * m).replace('.', ',')} m)")
    if agir:
        p = dusey("o", (P[0] - L1 + P[0] + L2) / 2); d3 = yatay("o", yo - 70, (P[0] - L1 + P[0] + L2) / 2, P[0])
        if p: yaz(f"P oku {p['h'] - 4:.1f} px = {(p['h'] - 4) / S:.2f} N (yazan 20 N)")
        if d3: yaz(f"d₃ ↔ {d3['w']:.1f} px = {d3['w'] / B * m:.3f} m (yazan 0,5 m)")
    if not (agir or acili):
        xb = dusey("r", P[0] - L1 - 46, en_az=40, cubuk=True); hb = dusey("c", yk[0] - 34, en_az=20, cubuk=True)
        if xb and hb: yaz(f"yol: x ↔ {xb['h']:.1f} px = {xb['h'] / B * m:.3f} m, h ↔ {hb['h']:.1f} px = {hb['h'] / B * m:.3f} m, x/h = {xb['h'] / hb['h']:.3f} (kol oranı {d['sol'] / d['sag']:.0f}; kartta {L1 * .2 / B * m:g} / {L2 * .2 / B * m:g} m)")
else:
    agir = "agirlikli" in V; S = 8.0 if agir else d["ok_olcek"]; F = 12 if agir else 12.5 if "verim" in V else d["F"]; G = d["G"]; HX = d["HX"]; M = d["M"]; yk, hk = d["yuk_kutu"], d["tut_kutu"]
    fo, g = dusey("r", HX + 128), dusey("c", M[0] - 100)
    if fo: yaz(f"F oku {fo['h'] - 4:.1f} px = {(fo['h'] - 4) / S:.2f} N (yazan {str(F).replace('.', ',')} N)")
    if g: yaz(f"G oku {g['h'] - 4:.1f} px = {(g['h'] - 4) / S:.2f} N (yazan {G} N)")
    if agir:
        p = dusey("o", M[0] + 26, en_az=12)
        if p: yaz(f"P oku (makaranın altından dışarı, katı kısım) {p['h'] - 4:.1f} px = {(p['h'] - 4) / S:.2f} N (yazan 4 N)")
    hb, xb, h2 = dusey("c", yk[2] + 40, en_az=40, cubuk=True), dusey("r", hk[2] + 44, en_az=40, cubuk=True), dusey("c", hk[2] + 68, en_az=40, cubuk=True)
    if hb and xb: yaz(f"yol: h ↔ {hb['h']:.1f} px = {hb['h'] / d['birim'] * .5:.3f} m (yükün alt kenarı {hb['y0']:.0f} -> {hb['y1']:.0f}), x ↔ {xb['h']:.1f} px = {xb['h'] / d['birim'] * .5:.3f} m (tutamağın alt kenarı), x/h = {xb['h'] / hb['h']:.3f} (beklenen 2,000)"
                      + (f"; 2h karşılaştırma {h2['h']:.1f} px = x'in {h2['h'] / xb['h']:.3f} katı" if h2 else ""))
open(f"cikti/{V}-v4-olcum.txt", "a", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out))
