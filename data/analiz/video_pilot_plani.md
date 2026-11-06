# Video pilotu planı (3. adım) — 6 Kasım 2026

Amaç: yarış videosundan, şeridin (ilk 10 sıra) veremediği olayları çıkarmak: **starta girerken huysuzlanma / geç yükleme, kapanma–sıkışma, geniş dönüp fazladan koşma, jokey düşmesi / dengesizlik**. Benter'in "kötü şans düzeltmesi" fikri: bu olayları yaşayan atın derecesi gerçek gücünü küçük gösterir.

## Zaten elimizde olan (video gerektirmeyen ya da hazır)
| Bilgi | Kaynak | Durum |
|---|---|---|
| Startta geç çıkış (boy) | TJK resmî API `delayedExit` | T151'de test ediliyor |
| Bitirememe / derecesiz | sonuç (Drcsz, sıra 0) | veride var |
| Yarış içi sıra, ilk 10 at | video şeridi (9.178 video, 2024-10 →) | MJV (T41) kullanıyor |
| Ekür, fedai | resmî `stablemate` + şerit | T151 betimsel (154 olay; az) |

## Pilot (karar vermeden önce ölçülecek)
1. **Örnek**: 40 koşu; 20'si rastgele, 20'si "şüpheli" (şeritte ani sıra kaybı ≥3 olan ya da startta geç çıkışlı at bulunan koşular). İstanbul/İzmir/Ankara/Bursa karışık, çim ve kum.
2. **Elle etiket (Doğan)**: her koşu için olay listesi — at no, olay türü (huysuzlanma/geç yükleme, kapanma/sıkışma, geniş dönüş, jokey sorunu, diğer), yaklaşık saniye. Telefon için basit bir form sayfası hazırlanır (Ganyan Masası → Diğer → Video etiketle), kayıt GitHub'a yazılır. Tahmini süre: koşu başı 2–3 dk (tekrar izleme) → ~1,5 saat.
3. **Otomatik tespit denemesi** (GitHub Actions, CPU):
   - `_m.mp4` (480p) yerine yüksek çözünürlüklü sürüm (~80 MB) indirilir; saniyede 5 kare.
   - Hazır nesne algılayıcı (YOLO "horse/person") ile kare başına at kutuları; koşu başına ~1–2 dk CPU.
   - Ölçülebilecekler: (a) start bölümünde kutudan çıkan at sayısı ve geç çıkan kutu (kamera sabitken), (b) dönemeçte at kutularının iç raydan yanal uzaklığı (geniş dönüş; ray çizgisi kare içinde tespit edilmeli), (c) grup içinde kutu üst üste binmesi + şeritte sıra kaybı (sıkışma işareti).
   - Kimlik eşleştirme (hangi kutu hangi at): forma rengi + şerit sırası ile; en zor kısım bu.
4. **Başarı ölçütü (go/no-go)**: elle etiketlere karşı otomatik tespit, olay türü başına duyarlılık ≥ %60 ve yanlış alarm ≤ koşu başına 0,5. Kimlik eşleştirme doğruluğu ≥ %80. Bunlar tutmazsa geniş ölçekli işe girilmez; yalnız tutan olay türleri devam eder.
5. **Sonra**: tutan olaylar 2024-10 → tüm videolara uygulanır, özellik olarak "son koşu / eski geçmiş" ayrımıyla (T151 ile aynı yapı) PM0 ve piyasalı tabanda ön kayıtla sınanır.

## Riskler (dürüst)
- Yayın kamerası sürekli hareket ediyor ve zaman zaman yakın plana geçiyor; yanal konum ölçümü bu yüzden gürültülü olabilir.
- Olaylar seyrek (fedai örneğindeki gibi) → etki büyük olsa bile istatistiksel güç düşük kalabilir.
- Yarış tekrarlarını izleyen bahisçiler son koşudaki olayları kısmen fiyatlıyor olabilir; bu yüzden hem piyasasız hem piyasalı test ve "eski geçmiş" özelliği şart.
- Video indirme yükü: koşu başı ~80 MB; tüm arşiv için kademeli (günde birkaç yüz koşu), mevcut `video_gunluk` hattının nezaketiyle.

## Senden gereken
- Pilot için onay ve ~1,5 saatlik etiketleme zamanı (istediğin zaman, parça parça olabilir).

## Durum — 6 Kasım 2026 12:25
- **Örnek hazır**: `data/analiz/video_pilot_liste.py` (tohum 40, ağ isteği yok) → `data/video_pilot/liste.json` (+ site kopyası `docs/data/video_pilot.json`). 20 şüpheli (hipodrom dengeli; ölçüt: resmî `delayedExit` VEYA şeritte erken ilk 3'te olup 7.+ bitiren at) + 20 rastgele (TÜM koşulardan; 12'si şüpheli ölçütünü de karşılıyor → taban oranı ölçülebilir). Dönem 2026-05..10; adana, ankara, bursa, istanbul, izmir, kocaeli. Ölçüt gevşek: 2.162 adayın 1.578'i "şüpheli" — yani ölçüt olay ayırt etmekte zayıf; pilot tam bunu da ölçecek.
- **Etiket sayfası**: `docs/etiket.html` (Ganyan Masası → Diğer → Video etiketle). Video tarayıcıda TJK'nin herkese açık CDN'inden oynar (izleyen sensin; otomatik çekim yok). Kör etiketleme: grup ve neden GÖSTERİLMEZ. Olay türleri: huysuzlanma/geç yükleme, kötü çıkış/tökezleme, kapanma/sıkışma, geniş dönüş, jokey sorunu, diğer; o anki video saniyesiyle. Kayıt: `data/video_pilot/etiket/Pxx.json` (GitHub anahtarıyla, diğer kayıt sayfaları gibi).
- **Otomatik tespit (CV) fizibilitesi — dürüst değerlendirme, henüz koşulmadı**:
  - Kolay/umutlu: (a) start bölümü (sabit kamera, kutu hizası) → geç çıkış; ama resmî `delayedExit` bunu zaten veriyor, CV'nin ek değeri düşük. (b) jokey düşmesi/bitirememe → resmî sonuçta zaten var.
  - Orta: kapanma/sıkışma — şeritte ani sıra kaybı + kutuların üst üste binmesi; yalnız öndeki ~10 atta görülür.
  - Zor: geniş dönüş (yayın kamerası pan/zoom yapıyor, ray çizgisi her karede yok) ve kimlik eşleştirme (hangi kutu hangi at: forma rengi/numara; 480p'de numara okunmuyor, HD gerekir).
  - Maliyet: HD koşu başı ~80 MB, CPU'da YOLO ~1–2 dk/koşu → 40 koşu ≈ 1 saat GitHub Actions, 3,2 GB indirme (mevcut video_gunluk hattının nezaket kurallarıyla).
  - Öneri: önce elle etiket (taban oranı + olayların gerçekten ne sıklıkta olduğu); CV denemesi yalnız elle etiketlerde olay sıklığı koşu başına ≥0,3 çıkarsa — aksi halde istatistiksel güç zaten yetmez (fedai örneğinde 154 olay bile anlamsızdı). CV koşusu ayrı onay ister.
