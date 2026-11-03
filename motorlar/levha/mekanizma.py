"""Genel mekanizma modeli: PARÇA (herhangi bir şekil) + EKLEM (dönme, kayma, sabit, bağlı) + küçük 2B kinematik çözücü.
Tasarım (tasarla.py), inceltme (incelt_mek.py) ve render (levha.py) aynı modülü kullanır. Model yok: NumPy + OpenCV + PIL.

Parça şekli (durgun poz, görsel koordinatı): ilkel listesi, birleşimi parçanın sınırıdır
  {"daire": [x, y, r]} · {"kutu": [x0, y0, x1, y1]} · {"cokgen": [[x, y], ...]} · {"kol": [x0, y0, x1, y1, w0, w1]} (uçları yuvarlak kiriş)
Hareket (eklem + sürücü) -> her karede DURGUN -> GÜNCEL ileri afin (2x3):
  donme {hiz} · bagli {parca, oran} (dişli: oran = -Z1/Z2)          -> pivot etrafında dönme (levha.py'deki eski yol)
  krank_kayma {krank, merkez, pim0, pim1, eksen}                       -> kayan parça: krank açısından kapalı formülle eksen boyunca öteleme
  biyel {krank, merkez, pim0, pim1, kayan}                             -> biyel: krank pimi ile kayan pim arasındaki katı çubuk
  anahtar {pivot, kareler: [[n, derece], ...], carpma}                  -> kaldıraç/kol: anahtar karelerle açı (yumuşak), isteğe bağlı çarpma sekmesi
  ip_sarma {ip}                                                        -> çark/davul: açısı ipin boyundan (ip = kol ucuna bağlı, davula sarılır)
  mermi {tasiyici, birak, ucus, hedef, zemin}                          -> taşıyıcıyla katı gider, bırakınca balistik uçar, seker, durur
  sabit                                                                -> hiç oynamaz
"""
import math
import numpy as np, cv2

# ───────── şekil
def kol_cokgen(x0, y0, x1, y1, w0, w1=None, n=10):
    w1 = w0 if w1 is None else w1; d = np.array([x1 - x0, y1 - y0], float); L = np.hypot(*d) + 1e-9; u = d / L; v = np.array([-u[1], u[0]])
    a0 = math.atan2(v[1], v[0]); P = []
    for t in np.linspace(0, math.pi, n):       # uç 1 yarım daire
        P.append(np.array([x1, y1]) + w1 / 2 * np.array([math.cos(a0 - t), math.sin(a0 - t)]))
    for t in np.linspace(0, math.pi, n):       # uç 0 yarım daire
        P.append(np.array([x0, y0]) + w0 / 2 * np.array([math.cos(a0 + math.pi - t), math.sin(a0 + math.pi - t)]))
    return np.array(P)

def ilkel_cokgen(e):
    if "kutu" in e: x0, y0, x1, y1 = e["kutu"]; return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float)
    if "cokgen" in e: return np.array(e["cokgen"], float)
    if "daire" in e: x, y, r = e["daire"]; t = np.linspace(0, 2 * np.pi, 96, endpoint=False); return np.stack([x + r * np.cos(t), y + r * np.sin(t)], 1)
    if "kol" in e: return kol_cokgen(*e["kol"])
    raise ValueError(e)

def maske(sekil, shape, pay=0):
    m = np.zeros(shape, np.uint8)
    for e in sekil: cv2.fillPoly(m, [np.int32(np.round(ilkel_cokgen(e) * 4))], 255, cv2.LINE_AA, 2)
    if pay > 0: m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pay + 1, 2 * pay + 1)))
    return m

def kaydir_sekil(sekil, dx, dy):
    o = []
    for e in sekil:
        if "kutu" in e: x0, y0, x1, y1 = e["kutu"]; o.append({"kutu": [x0 + dx, y0 + dy, x1 + dx, y1 + dy]})
        elif "cokgen" in e: o.append({"cokgen": [[x + dx, y + dy] for x, y in e["cokgen"]]})
        elif "daire" in e: x, y, r = e["daire"]; o.append({"daire": [x + dx, y + dy, r]})
        elif "kol" in e: k = list(e["kol"]); k[0] += dx; k[1] += dy; k[2] += dx; k[3] += dy; o.append({"kol": k})
    return o

# ───────── afin yardımcıları
def don(c, th):                                  # c etrafında th radyan (görüntü koordinatı: + saat yönü)
    co, si = math.cos(th), math.sin(th); A = np.array([[co, -si], [si, co]]); c = np.asarray(c, float)
    return np.hstack([A, (c - A @ c)[:, None]])
def otele(dx, dy): return np.array([[1, 0, dx], [0, 1, dy]], float)
def uygula(M, p): p = np.asarray(p, float); return M[:, :2] @ p + M[:, 2]
def bilesik(M2, M1):                              # önce M1 sonra M2
    return np.hstack([M2[:, :2] @ M1[:, :2], (M2[:, :2] @ M1[:, 2] + M2[:, 2])[:, None]])

def sio(x): return .5 - .5 * np.cos(np.pi * np.clip(x, 0, 1))

# ───────── kapalı formüller
def krank_kayma_s(c, pim0, pim1, u, th):
    """krank pimi c etrafında th döner; kayan pim pim1 + s*u doğrusunda, biyel boyu |pim1 - pim0| sabit -> s (durgunda 0)."""
    c, pim0, pim1, u = (np.asarray(v, float) for v in (c, pim0, pim1, u)); u = u / np.hypot(*u); L = np.hypot(*(pim1 - pim0))
    A = uygula(don(c, th), pim0); d = pim1 - A; du = d @ u; disk = du * du - d @ d + L * L
    return -du + math.sqrt(max(disk, 0.)), A

def teget(c, r, E, isaret):
    """davul (c, r) üzerinden E'ye giden ipin değme noktası; isaret ±1 hangi yandan çıktığı."""
    c, E = np.asarray(c, float), np.asarray(E, float); d = E - c; D = np.hypot(*d); a = math.atan2(d[1], d[0]); b = math.acos(min(1, r / max(D, r + 1e-6)))
    t = a + isaret * b; return c + r * np.array([math.cos(t), math.sin(t)])

def ip_boyu(c, r, E, isaret): T = teget(c, r, E, isaret); return float(np.hypot(*(np.asarray(E) - T))), T

def anahtar_deger(K, n):
    """[[n, değer], ...] arası yumuşak (cos) geçiş; 'ivme' işaretli karede t^2."""
    if n <= K[0][0]: return float(K[0][1])
    for i in range(len(K) - 1):
        a, b = K[i], K[i + 1]
        if a[0] <= n <= b[0]:
            u = (n - a[0]) / max(b[0] - a[0], 1e-9); f = u * u if (len(b) > 2 and b[2] == "ivme") else float(sio(u))
            return a[1] + (b[1] - a[1]) * f
    return float(K[-1][1])

def anahtar_aci(kareler, n):
    """[[n, derece], ...] arası yumuşak (cos) geçiş; 'ivme' işaretli karede t^2 (serbest bırakma)."""
    K = kareler
    if n <= K[0][0]: return math.radians(K[0][1])
    for i in range(len(K) - 1):
        a, b = K[i], K[i + 1]
        if a[0] <= n <= b[0]:
            u = (n - a[0]) / max(b[0] - a[0], 1e-9); f = u * u if (len(b) > 2 and b[2] == "ivme") else float(sio(u))
            return math.radians(a[1] + (b[1] - a[1]) * f)
    return math.radians(K[-1][1])

class Cozucu:
    """Tanımdaki her parçanın her karedeki DURGUN->GÜNCEL afini. aci_fn(ad, n): eski yol (dönen parçalar) açısı."""
    def __init__(self, T, aci_fn, nmax):
        self.T = T; self.P = {p["ad"]: p for p in T["parcalar"]}; self.aci = aci_fn; self.nmax = nmax; self._m = {}
        self.ipler = {i["ad"]: i for i in T.get("ipler", [])}

    def kol_ucu(self, ip, n):                       # ipin bağlı olduğu noktanın güncel yeri (bırakıldıysa kanca ip boyuyla sınırlı düşer)
        ad, p0 = ip["uc"]["parca"], ip["uc"]["nokta"]; nb = ip.get("birak")
        if nb is None or n <= nb: return uygula(self.poz(ad, n)[0], p0)
        if "_kanca" not in ip:                      # küçük Verlet: yerçekimi, davuldan uzaklık <= ip boyu, zemin
            E0 = uygula(self.poz(ad, nb)[0], p0); Lb, Tb = ip_boyu(self.P[ip["davul"]]["c"], ip["r"], E0, ip["isaret"])
            x = E0.copy(); xo = E0.copy(); g = ip.get("g", 2.2); Z = [x.copy()]
            for _ in range(400):
                v = (x - xo) * .97; xo = x.copy(); x = x + v + np.array([0, g])
                d = x - Tb; L = np.hypot(*d)
                if L > Lb: x = Tb + d / L * Lb
                if x[1] > ip.get("zemin", 1e9): x[1] = ip["zemin"]; xo[0] = x[0] - (x[0] - xo[0]) * .6; xo[1] = x[1]
                Z.append(x.copy())
            ip["_kanca"] = (np.array(Z), Tb, Lb)
        Z = ip["_kanca"][0]; return Z[min(int(n - nb), len(Z) - 1)]

    def ip_durumu(self, ad, n):
        """davul değme noktası, kanca, ip boyu, bolluk (sarkma için). Bırakınca davul mandalla durur, ip boşalır."""
        ip = self.ipler[ad]; c = self.P[ip["davul"]]["c"]; r = ip["r"]; nb = ip.get("birak"); E = self.kol_ucu(ip, n)
        if nb is not None and n > nb:
            _, Tb, Lb = ip["_kanca"]; return Tb, E, Lb, max(0., Lb - float(np.hypot(*(E - Tb))))
        L, Tn = ip_boyu(c, r, E, ip["isaret"]); return Tn, E, L, 0.

    def davul_aci(self, ad, n):
        ip = self.ipler[ad]; nb = ip.get("birak")
        if nb is not None and n > nb: n = nb
        L0, _ = ip_boyu(self.P[ip["davul"]]["c"], ip["r"], self.kol_ucu(ip, 0), ip["isaret"]); L, _ = ip_boyu(self.P[ip["davul"]]["c"], ip["r"], self.kol_ucu(ip, n), ip["isaret"])
        return ip["yon"] * (L0 - L) / ip["r"]

    def poz(self, ad, n):
        k = (ad, int(n) if float(n).is_integer() else n)
        if k in self._m: return self._m[k]
        p = self.P[ad]; h = p["hareket"]; tur = h["tur"]; al = 1.
        if tur == "sabit": M = otele(0, 0)
        elif tur == "krank_kayma":
            s, _ = krank_kayma_s(h["merkez"], h["pim0"], h["pim1"], h["eksen"], self.aci(h["krank"], n)); u = np.asarray(h["eksen"], float); u /= np.hypot(*u); M = otele(*(s * u))
        elif tur == "biyel":
            q = self.P[h["kayan"]]["hareket"]; th = self.aci(h["krank"], n)
            s, A = krank_kayma_s(q["merkez"], q["pim0"], q["pim1"], q["eksen"], th); u = np.asarray(q["eksen"], float); u /= np.hypot(*u)
            A0, B0 = np.asarray(h["pim0"], float), np.asarray(h["pim1"], float)
            A = uygula(don(h["merkez"], th), A0); B = B0 + s * u
            dth = math.atan2(*(B - A)[::-1]) - math.atan2(*(B0 - A0)[::-1]); M = bilesik(otele(*(A - A0)), don(A0, dth))
        elif tur == "anahtar":
            th = anahtar_aci(h["kareler"], n)
            c = h.get("carpma")                       # [n0, derece genlik, sönüm kare, periyot kare]: dayanağa çarpıp geri seker
            if c and n > c[0]: t = n - c[0]; th -= math.radians(c[1]) * math.exp(-t / c[2]) * abs(math.sin(math.pi * t / c[3]))
            M = don(h["pivot"], th)
        elif tur == "ip_sarma": M = don(p["c"], self.davul_aci(h["ip"], n))
        elif tur == "dogrusal":                       # sürücü d (px): öteleme = oteleme*d, dönme = donme*d (rad/px, durgun merkez etrafında)
            d = self.surucu(h["surucu"], n); ot = np.asarray(h.get("oteleme", [0, 0]), float) * d
            M = bilesik(otele(*ot), don(h.get("merkez", p.get("c", [0, 0])), h.get("donme", 0.) * d))
        elif tur == "takip":                          # başka parçanın bir noktasını izler, kendisi dönmez (asılı yük)
            q0 = np.asarray(h["nokta"], float); q = uygula(self.poz(h["parca"], n)[0], q0); M = otele(*(q - q0))
        elif tur == "mermi": M, al = self.mermi(ad, n)
        else: raise ValueError(f"{ad}: bilinmeyen hareket {tur}")
        self._m[k] = (M, al); return M, al

    def surucu(self, ad, n): return anahtar_deger(self.T["suruculer"][ad], n)

    def nokta(self, parca, p0, n): return uygula(self.poz(parca, n)[0], p0)

    def ip_yolu(self, ad, n):
        """ipin çokgen yolu. tur=makara: sabit uç -> makaralar (alt/üst sarım, dikey kollar) -> çekilen uç."""
        ip = self.ipler[ad]
        if ip.get("tur") != "makara":
            Tn, E, L, bol = self.ip_durumu(ad, n); c = np.hypot(*(E - Tn)); sag = math.sqrt(max(0., 3 * c * bol / 8)); u = np.linspace(0, 1, 60)[:, None]
            Pp = Tn * (1 - u) + E * u; Pp[:, 1] += sag * 4 * u[:, 0] * (1 - u[:, 0]); Pp[:, 1] = np.minimum(Pp[:, 1], ip.get("zemin", 1e9)); return Pp, E
        Q = []
        for d in ip["yol"]:
            if "sabit" in d: Q.append(np.asarray(d["sabit"], float))
            elif "uc" in d: E = self.nokta(d["uc"]["parca"], d["uc"]["nokta"], n); Q.append(E)
            else:
                pr = self.P[d["makara"]]; c = uygula(self.poz(d["makara"], n)[0], pr["c"]); r = d["r"]
                a = np.radians(np.linspace(180, 0, 40) if d["yan"] == "alt" else np.linspace(180, 360, 40))
                Q += list(np.stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)], 1))
        return np.array(Q), Q[-1]

    def mermi(self, ad, n):

        p = self.P[ad]; h = p["hareket"]; nb = h["birak"]
        if n <= nb: return self.poz(h["tasiyici"], n)[0], 1.
        if "_iz" not in p: p["_iz"] = self.mermi_yolu(ad)
        Y = p["_iz"]; i = min(int(n - nb), len(Y) - 1); f = (n - nb) - int(n - nb); q = Y[i] if i + 1 >= len(Y) else Y[i] * (1 - f) + Y[i + 1] * f
        M0 = self.poz(h["tasiyici"], nb)[0]; c0 = uygula(M0, p["merkez"])
        return bilesik(otele(q[0] - c0[0], q[1] - c0[1]), bilesik(don(c0, q[2]), M0)), 1.

    def mermi_yolu(self, ad):
        """bırakma noktasından hedefe (zemin) 'ucus' karede parabol; zeminde iki küçük sekme, yuvarlanma, durma. [x, y, açı]"""
        p = self.P[ad]; h = p["hareket"]; nb = h["birak"]; M0 = self.poz(h["tasiyici"], nb)[0]; c0 = uygula(M0, p["merkez"]); r = p["yaricap"]
        Tf = h["ucus"]; xl = h["hedef"]; yl = h["zemin"] - r; vx = (xl - c0[0]) / Tf; vy = -abs(vx) * math.tan(math.radians(h.get("aci", 45)))
        g = 2 * (yl - c0[1] - vy * Tf) / Tf ** 2; Y = []; x, y, a = c0[0], c0[1], 0.
        for t in range(Tf + 1): Y.append([c0[0] + vx * t, c0[1] + vy * t + .5 * g * t * t, vx * t / r * .5])
        x, y, a = Y[-1]; vy = (vy + g * Tf) * -.28; vx *= .4
        for _ in range(240):
            vy += g; y += vy; x += vx; a += vx / r
            if y >= yl: y = yl; vy = -vy * .3 if abs(vy) > 2 * g else 0.; vx *= .7
            if abs(vx) < .05 and vy == 0: vx = 0.
            Y.append([x, y, a])
        return np.array(Y)
