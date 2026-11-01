---
name: kalem
description: Kodla video yaparken her sahnenin hangi motorla çizileceğine karar verir, sahneleri o motorlarla üretir, sayfa çevirme gibi geçişlerle birleştirir ve kareye kilitli efekt sesi ekler. "kodla video yap", "animasyon yap", "bu videoyu sahnelere böl", "hangi motorla yapayım", "Reels/YouTube için animasyon" dendiğinde kullan.
---

# Kalem: her sahnenin kendi kalemi var

Bu skill reponun kökünden çalışır (`claude` repo klasöründe açılır). Bütün yollar repo köküne göredir. Yeni video `projeler/<ad>/` altında kurulur.

Tek bir motorla yapılan videolar birbirine benzer. Bu skill videoyu sahnelere böler, her sahnenin İÇİNDE NE OLDUĞUNA bakar ve onu en iyi çizen motoru seçer. Motor bir kalemdir: aynı resmi kurşun kalem ve suluboya farklı çizer.

## Sahnenin içinde ne var → hangi motor

| Sahnenin içinde... | Motor | Neden |
|---|---|---|
| Elle çizilen, kendini çizen çizgi, eskiz, kalem hareketi | **Paper.js** | Çizgiyi en yumuşak ve doğal çizen motor. Yalnız kalem işi için. |
| Karakter, yürüme, el kaldırma, şeklin başka şekle dönüşmesi | **Düz canvas (kendi çizim kodun)** | Hareket ve şekil üzerinde tam kontrol. |
| Patlama, ışık, parlama, toz, binlerce küçük parça | **PixiJS** | Binlerce parçayı kasmadan oynatır. |
| Ekrana yazı, sayı, sayaç, bilgi kartı, haber kurgusu | **HyperFrames** (HTML + GSAP) | Yazı ve bilgi animasyonunda en temizi. |
| Gerçek 3D: kamera dönüyor, ışık, gölge, makine | **Three.js** | Tarayıcıda gerçek 3D. |
| Formül, grafik, şema, matematik | **Manim** (Python) | 3Blue1Brown'un aracı. LaTeX yoksa Text ile yaz. |

Yardımcılar sahne çizmez, bir motorun içinde ona yardım eder:

| İş | Yardımcı |
|---|---|
| Hafif şeyler düşüyor, devriliyor, zıplıyor | Matter.js |
| Ağır şeyler kayıyor, üst üste yığılıyor | Rapier |
| Sahneden sahneye geçiş (125 hazır geçiş, sayfa çevirme = BookFlip) | gl-transitions (`ortak/gecis.html`) |
| Bir şey ekrana yay gibi zıplayarak geliyor | Anime.js |
| Konfeti, yıldız, emoji yağmuru | tsParticles |
| 3D modeli küçültmek | glTF-Transform |
| Kareye kilitli efekt sesi (tık, hışırtı, vuruş) | Tone.js (`ses/ses.html`) |

Bu tablo bir kişinin zevkiyle kuruldu: 20 araç aynı sahneyle yarıştırıldı, izlenip puanlandı. **Kendi denemelerini yap ve tabloyu kendi gözüne göre değiştir.**

## Akış

1. **Sahnelere böl.** Kullanıcının anlattığı videoyu 4-8 sahneye ayır. Her sahne için gündelik dille tek cümle yaz ve motoru seç, kullanıcıya tablo olarak göster:
   "1. sahnenin içinde kendi kendine çizilen bir eskiz var → Paper.js ile çizmek lazım."
   Teknik sıkıştırma yok ("sayı koşuyor" değil "sahnenin içinde artan bir sayı var").
   **Bir sahne = bir motor.** Sahnede birden çok iş varsa ekranı kaplayan ana iş motoru belirler, yan işler yardımcı olarak girer.
2. **Ortak dosyaları yaz.** `<proje>/zaman.json` (fps, boyut, geçiş kare sayısı, sahne listesi ve kare sayıları) ve `<proje>/BRIEF.md` (ortak görsel dil, gerçekler, her sahnenin tarifi, teslim sözleşmesi). Örnek: `ornek/ucan-makine/` (varsa).
3. **Sahneleri üret.** Kağıt dokusu, renkler ve yazı tipleri BRIEF'te bir kez tanımlanır, her sahne aynısını kullanır; videonun tek elden çıkmış gibi durması buna bağlı.
    Her sahne kendi klasöründe: `<proje>/sahneler/<NN-motor>/` → `calistir.sh`, `video.mp4`, `kontrol.png`, `olaylar.json`. Sahneler birbirinden bağımsızdır, paralel üretilebilir (her sahneye ayrı ajan).
4. **Kontrol.** Her sahnenin `kontrol.png`'sine ve birkaç tam karesine bak: yazı taşıyor mu, boş kare var mı, renkler ortak dilde mi, ilk kare dolu mu.
5. **Birleştir.** `python3 birlestir.py <proje> [--gecis BookFlip]` → geçişler + ses → `<proje>/cikti.mp4`.
   İzleyiciye hangi sahnenin hangi motorla çizildiğini göstermek istersen `--etiket` ekle: zaman.json'da her sahneye `"etiket": ["Paper.js", "kendi kendine çizilen kalem çizgisi"]` (isteğe bağlı üçüncü satır yardımcı için), ilk geçiş için `"gecis_etiketi"`. Her sahnenin sol altına defter kağıdı rengi küçük bir kart basılır.
6. **Denetim.** Taze bir ajana yalnız kontrol karelerini ve BRIEF'i ver, sor: "İzleyen kişi burada 'olmaz öyle şey' der mi?" Bulunanları düzelt, sonra kullanıcıya aç.

## Teknik sözleşme

- **Zaman kare numarasından gelir.** `Math.random` yok, tohumlu rastgele. İki koşu aynı kareyi vermeli.
- Tarayıcı motorları: sayfa `/ortak/surucu.js`'teki `surucu(kur, kare, KARE)`'yi çağırır, `kare(f)` çizilmiş bir canvas döndürür. Yakalama: `python3 ortak/yakala.py <sayfa yolu> <kare klasörü> [genişlik yükseklik]`, sonra ffmpeg ile mp4.
- `olaylar.json`: `[{"kare": 12, "tur": "cizgi|tik|vurus|dusme|hisirti|parilti|kanat|sayac", "guc": 0-1}]`. Görüntüdeki anla aynı kare. Ses buradan üretilir, o yüzden ses ile görüntü hiç kaymaz.
- Tarayıcı sayfasını yakalamadan önce JS'i `node --check` ile sına; sözdizimi hatasında sayfa hiç yüklenmez ve yakalayıcı 60 sn sonra durur.
- Manim: repo kökünde `.venv-manim/bin/python` varsa onu kullan (`MANIM_PY`), LaTeX yoksa MathTex değil Text.
- ffmpeg'de yazı çizme (drawtext) yok; yazı motorun içinde çizilir.
- Türkçe harfler (Ç Ğ Ş İ Ö Ü) eksiksiz; büyük harfe `toLocaleUpperCase('tr')`.
- İlk kare dolu: siyahtan açılış yok. Son ~15 kare sakin (geçiş oraya biner).
- Ani parlama / flaş yok: kare arası parlaklık sıçraması küçük kalır.
- Dikey video (Reels/Shorts) için üst ~250 px, alt ~420 px, sağ ~150 px'e anlam taşıyan öğe koyma.

## Kurulum

`./kurulum.sh` motorların paketlerini kurar (Node 20+, Python 3, ffmpeg, Google Chrome gerekir; Manim isteğe bağlı: `pip install manim`).
