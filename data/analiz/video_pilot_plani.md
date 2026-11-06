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
