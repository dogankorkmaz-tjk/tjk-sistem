# Hipotez defteri

Amaç: kaç şey denediğimizi kaydetmek. Ne kadar çok şey denersek, şans eseri iyi görünen bir şey bulma ihtimali o kadar artar.
Bu yüzden bir sonucu "buldum" saymadan önce buradaki deneme sayısına bakılır. Yeni deneme yapılırken satır eklenir.

Durum: BİRİNCİL = sonuçtan önce yazıldı (ön-kayıt) · KEŞİF = sonuca bakarak seçilebilir, tek başına kanıt değil

## 11–12 Ekim 2026 (Claude + Doğan)
| # | Deneme | Tür | Sonuç (özet) |
|---|---|---|---|
| 1 | Altılı ayaklarında sürpriz sıklığı (ayak 1–6, ≥10 ve ≥20 ganyan) | KEŞİF | Hiçbir ayak piyasanın fiyatladığının üstünde değil |
| 2 | Sürpriz dilimleri: hipodrom, ay, gün, sondan konum, alan, pist, mesafe, cins, ırk, yaş, ikramiye, hipodrom×ayak (≈70+ dilim, BH düzeltmeli) | KEŞİF | Yalnız Diyarbakır oranı >1, yine de kör ROI −%22; çoğu fark gürültü |
| 3 | Egzotik kural, walk-forward, 3 bahis × 2 model (eşik 1,15) | BİRİNCİL (kural dondurulmuştu) | Sıralı ikili 1,01 [0,94–1,07], ikili 0,995, üçlü(2026) 0,955 |
| 4 | Eşik taraması 1,00 / 1,25 / 1,50 / 2,00 (egzotik) | KEŞİF (4 ek eşik) | Oran yükseldikçe getiri arttı (1,25: 1,085; 1,50: 1,23); üçlüde artmadı |
| 5 | Uyandırma: ganyan≥10, eşik 1,0/1,15/1,30/1,50, 2 model | KEŞİF | Jason işaretlileri piyasanın 1,36 katı kazandı; ROI ≈ başa baş |
| 6 | İkili sekmesi kuralının yeniden hesabı (≥1,25 ve piyasa ≥%1) | Doğrulama | 2026: 1,03 (sayfa 1,04 ile uyumlu); 2025 Oca–May: 1,07 (sayfa 1,15 idi, düzeltildi) |
| 7 | Sürpriz + 2 favori ikili (297 kupon) | KEŞİF (fikir sonuç görüldükten sonra) | 1,20 [0,73–1,73]; en büyük 3 ödeme çıkarılınca 0,91 |
| 8 | 3 atlı kombine ikili (A,B,S), birincil + duyarlılık | KEŞİF | 1,20 [0,79–1,67]; kontrol 0,76 |
| 9 | Sıralı 5'li bütçe/geçerli kombinasyon (3 varyant) | KEŞİF | Geçerli sayımla aynı paraya ≈2× tutma olasılığı (makine testi bekleniyor) |
| 10 | Sızıntı denetimi (kod, son6, canlı-benzeri fark, çeyrek tutarlılığı, kalibrasyon payı) | Doğrulama | Sızıntı bulunamadı; kalibrasyon payı +0,0025 / toplam +0,0113 (Bolton), +0,0153 (Jason) |

## Ön-kayıtlı ileri testler (karar ölçütleri)
- Ana egzotik kural (1,15), Jason-1.25 ve Jason-1.50: ön-kayıt 12 Ekim 2026, 22:18 (commit a3c2336)
- 3 atlı kombine ikili: ön-kayıt 12 Ekim 2026, 22:49 (commit 520a5b8)
- Uyandırma eşiği 1,30 (canlı ölçüm, 10 Ekim'den beri)

## Eklenen deney: avantaj bölünmesi (12 Ekim 2026)
- KEŞİF (üç bölünme önceden yazıldı: hipodrom, koşu cinsi, alan büyüklüğü; başka bölünme denenmedi). Jason walk-forward nats kazancı, 10.493 yarış, genel +0,0171.
- Sonuç: 18 dilimin hiçbirinde fark anlamlı değil (Benjamini–Hochberg q ≥ 0,93). Avantaj bir hipodroma/cinse/alan büyüklüğüne yığılmış değil; odaklanılacak yer yok.

## Kontrol tarihleri
- **1 Kasım 2026**: ilk bakış (≈300 egzotik koşu). Yalnızca "kural çöküyor mu?" sorusu. Karar yok: bu hacimde aralık yaklaşık ±0,15.
- **1 Ocak 2027**: asıl değerlendirme (≈1.000+ koşu). Ana kural ve iki varyant yan yana, yarış günü bazında bootstrap %95 aralık; alt sınır 1,0'ı geçerse "kanıt", geçmezse "kanıt yok".
- **1 Nisan 2027**: 3 atlı kombine ikili ve Jason-1.50 için ilk anlamlı bakış (kupon sayısı az; yalnızca betimleyici). Bu tarihten önce karar verilmez.
