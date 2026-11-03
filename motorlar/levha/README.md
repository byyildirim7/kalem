# Levha motoru

**Türkçe** | [English](README.en.md)

![Levha motoru: kalemle oluşum ve tek tek gelen yazılar](demo.gif)

Kodla tasarlanan bir makineyi (kaldıraç, palanga, krank-piston, dişli zinciri, mancınık) eski bir Leonardo defteri levhası gibi çizer, sonra o makineyi **çalıştırıp** ders anlatan bir videoya çevirir. Makine kalemle oluşur, parçaları kendi eklemlerinde hareket eder, yazılar tek tek gelir, ölçüler kesikli çizgiyle gösterilir.

Mavi teknik çizim (blueprint) tarzı da var ve Codex gerektirmez, tamamen kodla çalışır.

## Nasıl çalışıyor

1. **Tasarla** (`<makine>/tasarla.py`): makine koordinatlarla tarif edilir. Çıktısı sade bir çizgi iskeleti (`iskelet.png`), parçasız gövde iskeleti (`iskelet-govde.png`) ve `geometri.json`.
2. **Codex ile gravür çiz**: iskelet, Codex CLI'nin `image_generation` aracıyla defter gravürüne çevrilir. İki görsel çıkar: `levha.png` (tam makine) ve `govde.png` (hareketli parçalar çıkarılmış gövde).
3. **Oturt** (`incelt_mek.py`): Codex çizimi iskeletle birebir aynı yerde çıkmaz. Her parça çizimde aranır, birkaç piksellik kayma bulunur, tasarım çizime oturtulur.
4. **Render** (`levha.py`): kalemle oluşum, parça ve eklem hareketi, ders katmanı, mp4.
5. **Ölç** (`ders_olc.py`): videonun son karesinden okların ve ölçülerin gerçek değeri ölçülür, yazılanla karşılaştırılır.

Çıktı `cikti/` klasörüne düşer: mp4, kontrol görüntüleri ve ölçüm raporu.

## Kurulum

Gerekenler: Python 3.10+, ffmpeg. Codex adımı için ayrıca [Codex CLI](https://github.com/openai/codex) (giriş yapılmış).

```bash
cd motorlar/levha
python3 -m pip install -r requirements.txt
```

Hazır örnek makinelerin Codex çizimleri klasörlerinde durur, yani Codex olmadan hemen deneyebilirsin.

## Tek komut

```bash
python3 yeni_levha.py <makine> [--codex-yok] [--stil blueprint] [--seviye 8|lise] [--varyant ...]
```

Örnekler:

```bash
python3 yeni_levha.py kaldirac --codex-yok --seviye lise --varyant acili      # defter tarzı, hazır çizimle
python3 yeni_levha.py palanga --stil blueprint --seviye lise --varyant agirlikli   # mavi teknik çizim, Codex yok
python3 yeni_levha.py iskelet-yolu --codex-yok                                  # dişli zinciri
python3 yeni_levha.py mancinik                                                  # Codex çalıştırır (para ve süre harcar)
```

Her render 15-25 saniye sürer. Bitişte mp4'ün yolu yazılır (`cikti/<ad>-v4-dur.mp4`).

| Seçenek | Ne yapar |
|---|---|
| `--codex-yok` | Codex'i atlar, klasördeki hazır `levha.png` ve `govde.png` kullanılır. |
| `--stil blueprint` | Görselleri koddan üretir, Codex gerekmez. Lacivert zemin, açık çizgi, renk = taraf (giriş, çıkış, yük). |
| `--seviye 8` | Ders katmanı MEB 8. sınıf düzeyinde: oran ve orantı. Varsayılan. |
| `--seviye lise` | 11. sınıf düzeyi: tork, denge, verim. Hareket yatay dengede biter. |
| `--varyant` | Aynı makinenin farklı sorusu. Kaldıraç: `tork`, `acili`, `agirlik`. Palanga: `temel`, `agirlikli`, `verim`. |

## Codex adımı

`yeni_levha.py` bunu kendisi yapar, `--codex-yok` demezsen. İki Codex işi aynı anda çalışır (a: tam makine, b: gövde). Elle çalıştırırsan iki kural var:

- İstem (prompt) `-i` ile verilen görselden **önce** yazılmalı. Sonra yazılırsa `-i` istemi yutar ve Codex boşa çalışır.
- İstemde "görseli MUTLAKA image_generation ile üret, Python ya da PIL ile çizme" denmelidir. Denmezse Codex işi kolay yoldan, kodla çizer ve gravür dokusu çıkmaz.

```bash
codex exec --skip-git-repo-check --sandbox workspace-write -C kaldirac "<istem>" -i kaldirac/iskelet.png
```

Hazır istem `tasarla.py`'nin yazdığı `ISTEK.md` ve `ISTEK-govde.md` dosyalarındadır. Codex bittiğinde `bitti.txt` yazar. Codex tek seferde tutmayabilir: sonucu `levha.png` olarak göz ile kontrol et, tutmadıysa yeniden çalıştır.

## Ders katmanı ve denetimler

Render sırasında sayılar bir çözücüden gelir ve ayrıca kendi içinde sınanır:

- **Yazılar tek tek gelir**, her satır hesapta bir adımdır. Renk taraf belirtir: kırmızı giriş kuvveti, mavi yük.
- **Kesikli ölçü çizgileri**: kol uzunluğu, yükselme, ip yolu gibi ölçüler çizilir.
- **Fizik denetimi**: kaldıraçta kol oranı ile yay uzunlukları oranı, palangada ip boyu ve "çekilen ip / yük kalkışı" oranı her karede kontrol edilir.
- **Çarpışma denetimi**: dişliler ve parçalar birbirine binmemeli, ekran yazıları parçaların üstüne gelmemeli (folyo çakışması 0 px olmalı).
- **Yol denetimi**: çizilen yol uçları tasarlanan yolla ±2 px örtüşmeli.
- **Render ölçümü** (`ders_olc.py`): videonun son karesinden ok boyları ve ölçüler pikselden okunur ("G oku 149,6 px = 29,92 N, yazan 30 N"). Sonuç `cikti/<ad>-v4-olcum.txt` dosyasında.

Bir denetim tutmazsa komut hata verir ve konsolda hangisi olduğu yazar.

## Yeni makine nasıl eklenir

1. `motorlar/levha/<ad>/` klasörü aç, içine `tasarla.py` yaz. En kolayı `kaldirac/tasarla.py`'yi kopyalayıp değiştirmek.
2. `tasarla.py` şunları yapar: parça şekillerini koordinatla tarif eder, `Iskelet` ile iki iskelet çizer (a: hepsi, b: hareketli parçalar yok), `geometri_yaz` ile `geometri.json`'u, `istek_yaz` ile Codex istemlerini yazar. Ortak yardımcılar `tasarim_ortak.py`'de.
3. Parça şekilleri: `daire`, `kutu`, `cokgen`, `kol` (uçları yuvarlak kiriş).
4. Her parçaya bir **eklem** ve bir **hareket** verilir (`mekanizma.py`):

| Hareket | Ne işe yarar |
|---|---|
| `donme` | Bir pivot etrafında sabit hızla döner (çark, dişli). |
| `bagli` | Başka bir parçaya bağlı döner. Dişlide oran = -Z1/Z2 (ters yön). |
| `krank_kayma` | Krank dönünce kayan parça (piston) ekseni boyunca gider gelir. |
| `biyel` | Krank pimi ile kayan pim arasındaki katı çubuk. |
| `anahtar` | Kol/kaldıraç: verilen kare-açı listesine göre yumuşak sallanır, istenirse çarpma sekmesi. |
| `ip_sarma` | Davul: açısı ipin boyundan çıkar, ip sarıldıkça döner. |
| `dogrusal` | Bir sürücüye (mesafe) göre hem ötelenir hem döner: palanganın hareketli makarası. |
| `takip` | Başka bir parçanın bir noktasını izler, kendisi dönmez: asılı yük. |
| `mermi` | Taşıyıcıyla gider, bırakılınca uçar, seker, durur: mancınık. |
| `sabit` | Hiç oynamaz. |

5. `python3 yeni_levha.py <ad>` ile dene. İlk seferde Codex çalışır ve `levha.png` ile `govde.png` klasöre düşer. Sonraki denemelerde `--codex-yok` yeter.

Ders katmanı (`geometri.json` içindeki `ders` bölümü) makine türüne göre değişir: kaldıraç, palanga ve dişli zinciri için hazır (krank-piston ve mancınık ders katmanı olmadan, yalnız hareketli levha olarak çalışır); yeni tür için `ders.py`'ye bir blok eklemek gerekir. Sadece hareketli bir levha istiyorsan `ders` bölümünü boş bırak, motor yine çalışır.

## Dosyalar

| Dosya | Görev |
|---|---|
| `yeni_levha.py` | Tek komut, bütün adımları sırayla çalıştırır. |
| `<makine>/tasarla.py` | Makinenin geometrisi. |
| `tasarim_ortak.py` | İskelet çizimi, Codex istemi, geometri yazımı. |
| `incelt_mek.py` | Tasarımı Codex çizimine oturtur. |
| `levha.py` | Render: oluşum, hareket, ders katmanı, mp4. |
| `mekanizma.py` | Eklem türleri ve küçük kinematik çözücü. |
| `ders.py`, `ders_olc.py` | Ders katmanı ve render sonrası ölçüm. |
| `blueprint.py` | Codex'siz mavi teknik çizim görselleri. |
| `levhalar/` | Her makinenin render tanımı (otomatik yazılır). |
| `font/` | Gömülü yazı tipleri (EB Garamond, IM Fell, açık lisans). |

Mavi teknik çizim yazıları macOS'ta Arial Narrow, Linux'ta Liberation Sans Narrow ya da DejaVu ile çizilir; hangisi varsa.

## Geçmiş

Motor önce sayaç çarkı levhasıyla bir prototip olarak başladı (piksel kesme yok, her parça kodla yeniden çizilir). Sonra genel mekanizma modeline, ders katmanına ve blueprint stiline geçti. Bu klasör o sürecin temiz, tek başına çalışan halidir.
