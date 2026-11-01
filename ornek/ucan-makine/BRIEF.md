# İç video: Leonardo'nun uçan makinesi (prova, 01.11)

Bu, YouTube bölümünde "her sahneyi başka bir motor çizer" fikrinin örnek videosu. Altı sahne, her biri kendi motoruyla.
Sahneler sonra sayfa çevirme geçişleriyle birleşir, üstüne kareye kilitli efekt sesleri eklenir. Seslendirme yok.

## Ortak görsel dil (hepsi aynı defterden çıkmış gibi durmalı)
- 1920×1080, 30 fps. Kare sayısı `zaman.json`'da (çoğu 240 = 8 sn, Three.js 300 = 10 sn). TAM bu kadar kare.
- Zemin: Leonardo defteri kağıdı `#E8D9B8`, çok hafif lekeli/dokulu (tohumlu, kare numarasından bağımsız sabit doku). Kenarlarda hafif kararma.
- Mürekkep `#2b1d12`, soluk mürekkep `#6b5640`, TEK vurgu kırmızısı `#b3261e` (sahnede en fazla bir iki yerde).
- Çizgi el çizimi gibi: hafif titrek, uçları incelen, tarama (hatching) ile gölge. Düz vektör "flat design" görünümü YOK.
- Yazı tipleri: başlık `Fell` (IM Fell), metin `Garamond` (EB Garamond, italik de var). Dosyalar `/ortak/font/`. Tarayıcı motorlarında `ortak/surucu.js` bunları yükler.
- Yazı Türkçe, kısa, büyük, okunur. Şapkalı harf YOK. Büyük harfe `toLocaleUpperCase('tr')`.
- Ani parlama / flaş YOK (epilepsi riski): ışık yumuşak gelir gider, kare arası ortalama parlaklık sıçraması küçük kalır.
- İlk kare DOLU: siyahtan ya da boş kağıttan fade-in açılış yok; 0. karede sahnenin ana öğesi görünür (sahne 1 hariç: o boş sayfada ilk çizginin başlamasıyla açılır, 0. karede ilk çizgi zaten başlamış olsun).
- Son ~15 kare sakin: büyük hareket bitmiş, sahne bir sonrakine sayfa çevirmeyle geçecek.
- Determinizm: zaman yalnız kare numarasından gelir, `Math.random` yok (tohumlu sözde rastgele). İki koşu aynı kareyi vermeli.

## Gerçekler (sapma yok)
- Leonardo da Vinci'nin uçan makine (ornitopter) çizimleri 1485-1490 civarı (Paris El Yazması B). Ekranda "1485 civarı" denir.
- İlk motorlu, kontrollü uçuş: Wright kardeşler, 17 Aralık 1903. 1903 − 1485 = 418 yıl.
- Kaldırma kuvveti: L = ½ · ρ · v² · S · C_L (ρ hava yoğunluğu, v hız, S kanat alanı, C_L kaldırma katsayısı). Hız 2 katına çıkınca kaldırma 4 katına çıkar.
- Leonardo'nun makinesi hiç uçmadı; insan kası kanat çırpmaya yetmez. (Ekranda iddia olarak bu kadar, sayı uydurma.)

## Sahneler
1. **Paper.js — eskiz kendini çiziyor.** Defter sayfasında ornitopterin yan görünüş eskizi kalemle çiziliyor: önce gövde ve pilot iskeleti, sonra kanat direği, kaburgalar yelpaze gibi, kanat zarı tarama ile. Kenarda Leonardo'nun ayna yazısını andıran soyut satırlar (okunur metin değil). Sonda kanat menteşesine kırmızı bir halka çizilir. Son karede eskiz tamam.
2. **HyperFrames — bilgi ve sayaç.** Bilgi kartı: "Leonardo da Vinci" / "Uçan makine" / "1485 civarı". Ardından büyük sayaç 1485'ten 1903'e sayar, altında "ilk motorlu uçuş · Wright kardeşler" ve sonda kırmızıyla "418 yıl". Haber kurgusu gibi temiz yazı animasyonu, ama defter kağıdı üstünde.
3. **Manim — formül.** Kaldırma formülü mürekkeple yazılır: L = ½ ρ v² S C_L. v² kırmızıyla vurgulanır, altında "hız 2 katı → kaldırma 4 katı" ve iki basit çubuk (1 ve 4 birim) büyür. LaTeX YOK (makinede kurulu değil): Text/MarkupText ile yaz, üst simge için Unicode ² kullan.
4. **Matter.js — parçalar masaya dökülüyor.** Makinenin ahşap parçaları (çubuklar, kaburgalar, krank, pedal, kanat bezi parçaları) yukarıdan masaya düşer, çarpışır, yığılır. Matter fiziği hesaplar, çizim mürekkep tarzında (dolgu yerine kontur + tarama). Sabit adımlı motor, tohumlu başlangıç.
5. **Three.js — eskizden 3D'ye ("vay" anı).** Açılışta kağıt üstünde yan görünüş eskizi; aynı açıda 3D makine eskizin üstüne oturup yavaşça belirir ve eskiz çekilir (kağıttan gerçeğe). Sonra kamera makinenin etrafında ~120° döner, kanatlar krankla çırpar. Model sahnenin kendi klasöründe (`ana.js`). Mürekkep/kağıt görünümü korunur.
6. **PixiJS — kanat çırpınca toz ve ışık.** 2D makine silueti (mürekkep) kanat çırpar; her aşağı vuruşta yerden toz bulutu kalkar, kanat kenarlarında yumuşak ışık parçacıkları dağılır (additive ama yumuşak, flaş yok). Binlerce parçacık. Sonda toz yavaşça çöker.

## Teslim sözleşmesi (her sahne kendi klasöründe)
- Klasör: `ornek/ucan-makine/sahneler/<NN-motor>/`. Yalnız oraya yaz. Paketin başka yerine, başka sahneye, kaynak klasörlere dokunma. Global kurulum yok.
- Giriş: `calistir.sh` → `video.mp4` (H.264, yuv420p, 1920×1080, 30 fps, tam kare sayısı) + `kontrol.png` (5 kare yan yana, küçük) + `olaylar.json`.
- `olaylar.json`: ses için olay listesi: `[{"kare": 12, "tur": "cizgi|tik|vurus|dusme|hisirti|parilti|kanat|sayac", "guc": 0.0-1.0}]`. Kalem çizgisi başlangıcı, çarpma, sayaç adımı, kanat vuruşu gibi anlar. Gerçekte görüntüdeki anla aynı kare.
- Tarayıcı motorları: `python3 ortak/yakala.py ornek/ucan-makine/sahneler/<NN>/sayfa.html <kare_klasoru>` (paket kökünden; sayfa `/ortak/surucu.js`'i import eder, `surucu(kur, kare, KARE)`). Kütüphaneler `/motorlar/<motor>/node_modules/...` altında (paperjs, pixijs, threejs, yardimci = matter/rapier/gl-transitions/tsparticles/anime). ffmpeg'de drawtext YOK, yazı motorun içinde çizilir.
- HyperFrames CLI: `motorlar/hyperframes/node_modules/.bin/hyperframes` (örnek kullanım `sahneler/02-hyperframes/calistir.sh`). GSAP `motorlar/hyperframes/node_modules/gsap/dist/gsap.min.js`.
- Manim: repo kökünde `.venv-manim/bin/python` varsa onu kullan (`MANIM_PY`), yoksa sistemdeki `python3 -m manim`.
- Bitince `kontrol.png`'ye ve birkaç tam kareye kendin bak (Read ile): yazı taşıyor mu, boş/kırık kare var mı, renkler defter dilinde mi. En fazla 3 düzeltme turu.

## Rapor (Türkçe, kısa, en fazla 12 satır)
Ne yaptın, motorun hangi özelliğini kullandın, render süresi, takıldığın yer ve nasıl aştın (bu YouTube'da anlatılacak, dürüst yaz), kalan kusur.
