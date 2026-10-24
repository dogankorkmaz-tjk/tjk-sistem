# Veri envanteri ve kaynak keşfi (canlı belge, 24 Ekim 2026)
Amaç: modeli piyasa kalitesine getirmek (Benter yaklaşımı: çok sayıda doğru kurulmuş değişken + halka açık piyasa olasılığıyla birleştirme). Kural: robots.txt/kullanım şartına uyulur; engel aşılmaz; istekler nazik (>=3 sn arayla, düşük hacim).
Test disiplini: her yeni özellik önce buraya/hipotez defterine ön kayıt; walk-forward; çoklu karşılaştırma düzeltmesi (çok özellik denemek sahte kazanç üretir); karar kuralı önceden.

## Elimizde (otomatik)
- Program, AGF, jokey/kilo/HP/Son 6/KGS/ST, bahis türü bayrakları (atyarisi API, 23 Ekim 2026'dan)
- Sonuçlar, kapanış ganyanı, tüm ikramiyeler (atyarisi RaceResult)
- Canlı AGF zaman serisi (data/agf_zaman), muhtemel ganyan (vhs-medya)
- Yabancı yarışlar/ABD canlı oranlar (ayrı hatlar)

## Yarı elle (kullanıcı yükler)
- İdman PDF'leri (eksik: 3 Ağu–6 Eki; 23 Eki sonrası)
- Kron/Son 800 dosyaları, Accurace PDF'leri, video seyir

## Aday kaynaklar ve durum
| Veri | Kaynak | Otomatik mi | Durum |
|---|---|---|---|
| Galoplar/sprintler (bölüm süreleri, çaba, iç-dış, pist durumu) | atyarisi istatistik widget (`/galoplar`) | araştırılıyor | probe6 |
| En iyi derece, son 2 koşu, birlikte koşular, kayıtlar, at-jokey | atyarisi istatistik widget'ları | araştırılıyor | probe7 |
| At detayı (tüm geçmiş koşular) | atyarisi `/at-detay`, Nal Sesleri API | Nal Sesleri çalışıyor | toplama sürüyor |
| Pist ağırlığı/durumu, hava | atyarisi ProgramHippodromes (raceCourse, weather) | evet | arşivlenecek |
| Ekipman ve jokey değişikliği | atyarisi ProgramDetails | evet | arşivlenecek |
| Soy (baba, anne, anne babası, baba babası) | atyarisi ProgramDetails | evet | arşivlenecek |
| Son 800, at bazında fark/derece | atyarisi RaceResult | evet | arşivlenecek |
| Sabit ihtimalli oranlar (ikinci piyasa) | atyarisi `/tjk-sabit-ihtimalli` | araştırılıyor | probe7 |
| Muhtemel ganyan + AGF zaman serisi | atyarisi/vhs-medya | kısmen | genişletilecek |
| Havuz büyüklüğü, devir | atyarisi muhtemel/AGF sayfası | araştırılıyor | probe7 |
| Editör/tahminci tahminleri | atyarisi `/tahminleri`, hazır kuponlar | araştırılıyor | probe7 (karşılaştırma ölçütü; piyasada fiyatlı olma olasılığı yüksek) |
| Tarihsel hava (hipodrom koordinatı) | Open-Meteo arşiv API (ücretsiz, ticari olmayan) | evet | denenecek |
| Hipodrom geometrisi (pist uzunluğu, viraj, düzlük, kapı etkisi) | halka açık TJK pist bilgileri / kendi verimizden öğrenme | kısmen | planlanacak |
| Geçmiş yıllar program/sonuç (eğitim derinliği) | atyarisi `date=` parametresi | denenecek | derinlik denemesi |
| Geçmiş AGF | Nal Sesleri (AGF1/AGF2, 2023'ten) | evet (nazik) | çalışıyor |
| Türkçe at yarışı yorumları (metin) | atyarisi yorumlar | belirsiz | düşük öncelik |

## Çıkarma/kullanmama kararı
Değeri belirsiz her aday için: yeterli veri çekilir, ön kayıtlı testle ölçülür; yalnızca örnek yeterliyken ve sonuç yokken eleriz. Elenen veri ve gerekçe buraya yazılır.

## Accurace otomatik kaynak araştırması (24 Ekim 2026) — SONUÇ: ücretsiz/izinli otomatik kaynak yok
- Accurace (accurace.net): TJK ile 10 yıllık münhasır sözleşme; veri "güvenli API, panel, yayın grafiği" olarak yayıncı/bahis operatörü/profesyonellere; halka açık arşiv yok; iletişim/demo ile.
- tjk.org robots.txt: User-agent * için Disallow: / (yalnız Googlebot ve sosyal önizleme botları izinli) → PDF'leri otomatik çekmek kuralımıza aykırı; elle indirme sürer.
- UAT Racing (uatracing.com): "gerçek 200 m split", TempoRadar (İlk400/Son400/Son800) gösteriyor; robots arşiv/istatistik/API yollarını engelliyor, üyelik gerekli → kazınmaz.
- atyarisi API (kullandığımız): RaceResult'ta yalnız last800 (koşu düzeyi), at başına derece/fark; 200 m dilimi yok.
- Seçenekler: (1) Accurace'a veri lisansı sor; (2) elle PDF yüklemeye devam (1 Aralık'ta f_k/tempo yeniden); (3) kayıt dışı yollar denenmeyecek.
