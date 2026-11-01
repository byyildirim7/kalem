// Sayfa tarafı sürücü. kur() bir kez, kare(f) her kare için çağrılır; kare(f) çizilmiş bir canvas döndürür.
// Fontlar: Fell (IM Fell, başlık), Garamond (EB Garamond, metin) /ortak/font altından yüklenir.
export async function surucu(kur, kare, KARE = 240) {
  const log = (m) => fetch("/log", { method: "POST", body: String(m) });
  try {
    for (const [ad, dosya, stil] of [["Fell", "IMFeENrm28P.ttf", "normal"], ["Fell", "IMFeENit28P.ttf", "italic"], ["Garamond", "EBGaramond.ttf", "normal"], ["Garamond", "EBGaramond-Italic.ttf", "italic"]]) {
      const f = new FontFace(ad, `url(/ortak/font/${dosya})`, { style: stil }); await f.load(); document.fonts.add(f);
    }
    await kur();
    for (let f = 0; f < KARE; f++) {
      const cv = await kare(f);
      const b = await new Promise((ok) => cv.toBlob(ok, "image/png"));
      await fetch("/kare?i=" + f, { method: "POST", body: b });
    }
    await fetch("/bitti", { method: "POST", body: "tamam" });
  } catch (e) { await log("HATA " + (e.stack || e)); await fetch("/bitti", { method: "POST", body: "hata " + e }); }
}
