#!/usr/bin/env python3
"""Tek komut: tasarla -> Codex (a: tam makine + b: hareketli parçasız gövde, aynı anda) -> incelt_mek -> levha.py render.
  python3 yeni_levha.py <tasarım adı> [--codex-yok] [--stil blueprint] [--seviye 8|lise] [--varyant tork|acili|agirlik (kaldıraç) · temel|agirlikli|verim (palanga)]
<tasarım adı>/tasarla.py makineyi tasarlar (geometri.json, iskelet.png, iskelet-govde.png, ISTEK.md, ISTEK-govde.md).
--codex-yok: Codex atlanır, klasördeki levha.png + govde.png kullanılır. Çıktı: cikti/<ad>-v4-dur.mp4 + kontrol görüntüleri."""
import json, os, subprocess, sys, time
D = os.path.dirname(os.path.abspath(__file__)); AD = sys.argv[1]; K = os.path.join(D, AD); SURE = {}
def adim(ad, t0): SURE[ad] = round(time.time() - t0, 1); print(f"[{ad}] {SURE[ad]} sn", flush=True)
def codex(tur):
    ist, isk, cik, bit, log = (("ISTEK.md", "iskelet.png", "levha.png", "bitti.txt", "codex-a.log") if tur == "a" else
                              ("ISTEK-govde.md", "iskelet-govde.png", "govde.png", "bitti-govde.txt", "codex-b.log"))
    istem = (f"{ist} dosyasını oku ve harfiyen uygula. Görseli MUTLAKA image_generation (görsel üretme) aracınla, ekteki {isk} dosyasını "
             f"referans görsel olarak vererek üret. Python, PIL, SVG ya da kodla çizim YAPMA: kodla çizilen görsel gravür dokusu taşımaz, kabul edilmez. "
             f"Görsel 1536x1024 olsun, iskeletle birebir örtüşsün. Çıktıyı {cik} adıyla bu klasöre kaydet, sonra {bit} yaz.")
    # İSTEM -i'den ÖNCE (yoksa -i istemi yutar); stdin kapalı
    return subprocess.Popen(["codex", "exec", "--skip-git-repo-check", "--sandbox", "workspace-write", "-C", K, istem, "-i", os.path.join(K, isk)],
                            stdin=subprocess.DEVNULL, stdout=open(os.path.join(K, log), "w"), stderr=subprocess.STDOUT), os.path.join(K, cik)
t = time.time(); subprocess.run([sys.executable, "tasarla.py"], cwd=K, check=True); adim("tasarım", t)
if "--stil" in sys.argv and sys.argv[sys.argv.index("--stil") + 1] == "blueprint":   # Codex'siz: görseller koddan, belirlenimci
    import json
    t = time.time(); subprocess.run([sys.executable, os.path.join(D, "blueprint.py"), K, AD], check=True); adim("blueprint görselleri (Codex yok)", t)
    if not os.path.exists(os.path.join(D, "levhalar", AD + ".json")):     # defter tanımı yoksa (Codex hiç çalışmadı) tasarımdan türet
        ev = dict(os.environ, LEVHA_REF_KLASOR=os.path.join(K, "blueprint")); subprocess.run([sys.executable, os.path.join(D, "incelt_mek.py"), K, AD], check=True, env=ev)
    yb = os.path.join(D, "levhalar", AD + "-blueprint.json")
    if not os.path.exists(yb):                        # ilk kez: defter tanımından türet (balon listesi yok)
        T = json.load(open(os.path.join(D, "levhalar", AD + ".json"))); T.update(gorsel=os.path.relpath(os.path.join(K, "blueprint", "levha.png"), D), gorsel_b=os.path.relpath(os.path.join(K, "blueprint", "govde.png"), D), stil="blueprint")
        json.dump(T, open(yb, "w"), ensure_ascii=False, indent=1)
    EK = [a for i, a in enumerate(sys.argv) if a in ("--seviye", "--varyant") or (i > 0 and sys.argv[i - 1] in ("--seviye", "--varyant"))]
    t = time.time(); subprocess.run([sys.executable, os.path.join(D, "levha.py"), yb] + EK, check=True); adim("render", t)
    print("süreler:", SURE); sys.exit(0)
if "--codex-yok" not in sys.argv:
    t = time.time(); isler = [codex("a"), codex("b")]
    for p, _ in isler: p.wait()
    for _, cik in isler:
        if not os.path.exists(cik) or os.path.getmtime(cik) < t: sys.exit(f"Codex {os.path.basename(cik)} üretmedi; {K}/codex-*.log'a bak")
    adim("Codex (a + b paralel)", t)
for f in ("levha.png", "govde.png"):             # govde.png yalnız tasarım iskelet-govde.png ürettiyse gerekir (dişli zinciri üretmez)
    if f == "govde.png" and not os.path.exists(os.path.join(K, "iskelet-govde.png")): continue
    if not os.path.exists(os.path.join(K, f)): sys.exit(f"{f} yok: Codex adımını çalıştır")
if json.load(open(os.path.join(K, "geometri.json"))).get("tur") == "mekanizma":
    t = time.time(); subprocess.run([sys.executable, os.path.join(D, "incelt_mek.py"), K, AD], check=True); adim("incelt", t)
elif not os.path.exists(os.path.join(D, "levhalar", AD + ".json")): sys.exit(f"levhalar/{AD}.json yok: dişli zinciri tanımı elle yazılır (iskelet-yolu örneğine bak)")
EK = [a for i, a in enumerate(sys.argv) if a in ("--seviye", "--varyant") or (i > 0 and sys.argv[i - 1] in ("--seviye", "--varyant"))]
t = time.time(); subprocess.run([sys.executable, os.path.join(D, "levha.py"), os.path.join(D, "levhalar", AD + ".json")] + EK, check=True); adim("render", t)
import json
if json.load(open(os.path.join(D, "levhalar", AD + ".json"))).get("ders"):      # ders levhası: sayıları render karesinden ölç
    sv = EK[EK.index("--seviye") + 1] if "--seviye" in EK else "8"; vr = EK[EK.index("--varyant") + 1] if "--varyant" in EK else None
    ad = AD + ("-seviye8" if sv == "8" else "-lise" + (f"-{vr}" if vr else "")); subprocess.run([sys.executable, os.path.join(D, "ders_olc.py"), os.path.join(D, "levhalar", AD + ".json"), ad], cwd=D, check=True)
print("süreler:", SURE, "->", os.path.join(D, "cikti", AD + "-v4-dur.mp4"))
