#!/usr/bin/env python3
"""Mekanizma tasarımını (tasarla.py -> geometri.json, tur=mekanizma) Codex levhasına oturtur, levha.py tanımını yazar.
  python3 incelt_mek.py <klasör: geometri.json + iskelet.png + levha.png (+ govde.png)> [ad]
Her hareketli parça için şablon = iskeletteki o parçanın çizgileri (parça sınırı içinde); levha mürekkebinde ±15 px aranır
(normalize çapraz ilinti). Bulunan kayma parçanın şekline, pivotuna ve eklem noktalarına uygulanır (krank merkezi krankın,
biyel uçları biyelin, kayan pim kayanın kendi kaymasıyla). Ayrıca %50 bindirme (tasarım/çizim) yazılır. Model yok: OpenCV + NumPy."""
import json, os, sys, zlib, copy
import cv2, numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); import mekanizma as MEK
K = os.path.abspath(sys.argv[1]); AD = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(os.path.normpath(K))
GEO = json.load(open(os.path.join(K, "geometri.json"), encoding="utf-8")); REF = cv2.imread(os.path.join(os.environ.get("LEVHA_REF_KLASOR", K), "levha.png")) ; ISK = cv2.imread(os.path.join(K, "iskelet.png"))   # LEVHA_REF_KLASOR: blueprint modunda Codex levhası yoksa referans yerine blueprint/ görseli
H0, W0 = REF.shape[:2]; ink = lambda im, s: cv2.GaussianBlur(255 - cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), s)
Ia, Is = ink(REF, 3), ink(ISK, 3); ARA = 15; KAY = {}
for p in GEO["parcalar"]:
    m = np.zeros((H0, W0), np.uint8)
    if p["tur"] == "disk": cv2.circle(m, tuple(int(v) for v in p["c"]), int(p["r"]) + 4, 255, -1)
    else: m = MEK.maske(p["sekil"], (H0, W0), pay=8)
    ys, xs = np.nonzero(m); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    sab = (Is * (m > 0))[y0:y1, x0:x1]
    X0, Y0, X1, Y1 = x0 - ARA, y0 - ARA, x1 + ARA, y1 + ARA; pad = [max(0, -Y0), max(0, Y1 - H0), max(0, -X0), max(0, X1 - W0)]
    ara = np.pad(Ia[max(0, Y0):min(H0, Y1), max(0, X0):min(W0, X1)], ((pad[0], pad[1]), (pad[2], pad[3])), mode="edge")
    r = cv2.matchTemplate(ara, sab, cv2.TM_CCOEFF_NORMED); _, v, _, (lx, ly) = cv2.minMaxLoc(r)
    r0 = float(r[ARA, ARA]); KAY[p["ad"]] = (lx - ARA, ly - ARA)
    print(f"{p['ad']}: kayma {lx - ARA:+d}, {ly - ARA:+d} px, ilinti {v:.3f} (tasarım yerinde {r0:.3f})")
def kay(ad): return np.array(KAY.get(ad, (0, 0)), float)
T = copy.deepcopy(GEO); T.pop("W"); T.pop("H"); T.pop("tur"); T.pop("govde", None)
for p in T["parcalar"]:
    d = kay(p["ad"]); dx, dy = float(d[0]), float(d[1])
    if "c" in p: p["c"] = [p["c"][0] + dx, p["c"][1] + dy]
    if "sekil" in p: p["sekil"] = MEK.kaydir_sekil(p["sekil"], dx, dy)
    for k in ("pivot", "merkez"):
        if k in p: p[k] = [p[k][0] + dx, p[k][1] + dy]
    if "eklem" in p and "pivot" in p["eklem"]: p["eklem"]["pivot"] = [p["eklem"]["pivot"][0] + dx, p["eklem"]["pivot"][1] + dy]
P = {p["ad"]: p for p in T["parcalar"]}
for p in T["parcalar"]:
    h = p["hareket"]; ad = p["ad"]
    if h["tur"] in ("krank_kayma", "biyel"):
        h["merkez"] = P[h["krank"]]["c"]; kk = kay(h["krank"]) if h["tur"] == "krank_kayma" else kay(ad)
        h["pim0"] = list(np.array(h["pim0"]) + kk); h["pim1"] = list(np.array(h["pim1"]) + kay(ad))
    if h["tur"] == "anahtar": h["pivot"] = list(np.array(h["pivot"]) + kay(ad))
    if h["tur"] == "dogrusal" and "merkez" in h: h["merkez"] = list(np.array(h["merkez"]) + kay(ad))
FZ = T.get("fizik") or {}
if FZ.get("tur") == "kaldirac":
    for k in ("pivot", "uc1", "uc2"): FZ[k] = list(np.array(FZ[k]) + kay(FZ["parca"]))
for e in T.get("isaretler", []):
    if e["tur"] == "yay": e["pivot"] = list(np.array(e["pivot"]) + kay(e["parca"]))
for ip in T.get("ipler", []):
    for u_ in ([ip["uc"]] if "uc" in ip else [d["uc"] for d in ip.get("yol", []) if "uc" in d]): u_["nokta"] = list(np.array(u_["nokta"]) + kay(u_["parca"]))
rnd = np.random.default_rng(zlib.crc32(AD.encode()))
T.update(ad=AD, gorsel=os.path.relpath(os.path.join(K, "levha.png"), D), folio=f"fol. {int(rnd.integers(3, 60))} {'rv'[int(rnd.integers(0, 2))]}.", on=[], dolgu=[], incelt={k: list(v) for k, v in KAY.items()})
if os.path.exists(os.path.join(K, "govde.png")): T["gorsel_b"] = os.path.relpath(os.path.join(K, "govde.png"), D)
T = json.loads(json.dumps(T, default=float))
yol = os.path.join(D, "levhalar", AD + ".json"); json.dump(T, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("->", yol)
# %50 bindirme: tasarım / çizim (a) ve (b)
os.makedirs(os.path.join(D, "cikti"), exist_ok=True); pan = []
for gor, isk in (("levha.png", "iskelet.png"), ("govde.png", "iskelet-govde.png")):
    RK = os.environ.get("LEVHA_REF_KLASOR", K)
    if not os.path.exists(os.path.join(RK, gor)): continue
    a = cv2.imread(os.path.join(RK, gor)).astype(np.float32); b = cv2.imread(os.path.join(K, isk)).astype(np.float32)
    o = (a * .5 + b * .5).astype(np.uint8); cv2.putText(o, f"{gor} %50 + {isk}", (20, 40), 0, 1.1, (30, 30, 160), 2); pan.append(o)
cv2.imwrite(os.path.join(D, "cikti", AD + "-bindirme.png"), np.hstack(pan) if len(pan) > 1 else pan[0])
