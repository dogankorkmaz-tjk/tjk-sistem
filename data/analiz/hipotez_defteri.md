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

## Eklenen deney: kesinti neden değişiyor (12 Ekim 2026)
- KEŞİF. Doğrudan ölçüm yapılamadı: elimizde yarış başına havuz büyüklüğü yok (yalnız altılı/üçlü gibi havuzlar). Dolaylı ölçü (ganyan ödemesi × kazananın AGF payı) ay ay 0,59–0,73 arasında oynuyor; bu, kesinti değil AGF'nin ganyan havuzundan farkını da içeriyor, ayrıştırılamaz. Sonuç: "kesinti değişiyor" iddiası kanıtlanamadı, kullanılmayacak.

## Eklenen deney: kapanış çizgisi değeri (CLV), ilk bakış
- KEŞİF, çok küçük örnek: 10–12 Ekim, 57 koşu, 578 at. İlk AGF anlık görüntüsüne göre Jason'un %25+ fazla gördüğü 34 atta AGF kapanışa kadar ortalama +%15,8 yükseldi (bootstrap %95: +%2,8 / +%27,2); tüm atlarda ortalama −%2,2. Koşu içi korelasyon +0,13 (se 0,06). Yön olumlu ama örnek küçük, "ilk" görüntü sabah erken, "son" görüntü gerçek kapanış değil. Veri biriktikçe (≥500 koşu) yeniden bakılacak.

## Eklenen deney: sıralı beşli devir hesaplayıcısı (12 Ekim 2026)
- KEŞİF, YAPILAMADI. 7'li ganyanda devir formülü (0,69 × (1 + D/havuz)) kullanılıyor. Sıralı beşlide aynı varsayımı sınadım: 156 devir sonrası ödeme, devirsiz 1.259 ödemeyle karşılaştırıldı.
- Devir sonrası ödeme ortalaması 117.660 TL, devirsiz 57.539 TL (≈2 kat). Devir tutarıyla ödeme arasındaki korelasyon 0,13; ödemenin devire oranı medyan 0,17. Devir sonraki yarışın havuzuna tam eklenseydi ödeme devirle birlikte artmalıydı.
- Sonuç: devrin nereye, hangi kurala göre aktığı verimizle doğrulanamıyor. Güvenilmeyen bir "fırsat" etiketi koymamak için hesaplayıcı eklenmedi. Gerekli bilgi: makine/TJK ekranında devirli günün beşli havuzunda "devir" satırı.

## Eklenen deney: kapı yanlılığı ("fazla mesafe" vekili), 12 Ekim 2026
- KEŞİF. Accurace verisi yerine eldeki veriyle: (hipodrom, mesafe, pist, kapı grubu iç/orta/dış) için ÖNCEKİ günlerin ortalama bitiş artığı, 30 ağırlıklı önselle, Jason'a tek ek özellik. Parametreler tek seferde, bakmadan seçildi; ayarlama yapılmadı. Walk-forward, 2024Q2–2026Q4, 14.697 koşu.
- Sonuç: Jason +0,0153 → +0,0177 nats/koşu; fark +0,0024 (se 0,0006; gün bazında se 0,0010). Gerçek ama küçük. Daha önce koyduğumuz benimseme eşiği +0,005'in altında.
- Karar: Jason'a eklenmedi. Betik: data/analiz/kapi_yanlilik_testi.py.

## Ön-kayıt: Jason-K gölge modeli (12 Ekim 2026, ~23:40)
- Jason-K = Jason + kapı yanlılığı özelliği; her gece ayrı eğitilir, canlıda Jason ile yan yana skorlanır (docs/data/golge.json: k_eksi_jason). Jason değişmedi.
- Geriye dönük beklenti (walk-forward): +0,0024 nats/koşu. Karar: 1 Ocak 2027'de canlı fark ve %95 aralık; alt sınır > 0 ise Jason-K ana aday olur. Bu tarihten önce karar yok.

## Eklenen deney: ıslak pist özelliği (13 Ekim 2026)
- KEŞİF. Kron sayfalarından kum pist durumu (Normal/Nemli/Sulu/Islak) 379 hipodrom-günde var (Oca 2026'dan). Özellik: atın önceki ıslak-gün koşularındaki piyasaya göre bitiş artığı ortalaması (K=2), yalnız bugün ıslaksa. Jason olasılığına tek parametreli ek terim; 464 ıslak-gün koşusu (Şub–Eki 2026).
- Sonuç: β=0,66, kazanç 0,0014 nats/koşu, LR=1,29, p≈0,26. Anlamlı değil; örnek küçük (ıslak veri yalnız 2026'dan).
- Karar: modele eklenmedi. Kron sayfaları zaten günlük kaydediliyor; kış ayları sonrası (≈1 Mart 2027) aynı betikle yeniden bakılacak. Betik: data/analiz/islak_pist_testi.py.
- Not: kron başlığı gün sonunda kaydedildiği için pist gün içinde değişmiş olabilir; canlı kullanım için yarıştan önceki pist durumu gerekir.

## Makine doğrulaması ve sıralı beşli "-G" varyantı (13 Ekim 2026, ~16:00)
- Makine fişi (Adana 5. koşu): her sıraya birden fazla at yazılabiliyor, aynı at iki sıraya da yazılabiliyor (6,7 / 6,7 / ...). Fiş: 110 bahis, 137,50 TL. Beş ayrı atlı geçerli kombinasyon sayısı = 110; satır çarpımı 336 olurdu (420 TL). Yani makine yalnız geçerli kombinasyonları ücretlendiriyor.
- Düzeltme (ölçüm, kural değil): sıralı beşli kâğıt testinde harcama artık geçerli kombinasyon sayısı × 1,25 TL. Eski kayıtlar çarpımla yazılmıştı (gerçek maliyetin %65–83'ü kadar fazla); toplamlar yeniden hesaplanıyor, çarpım ayrıca harcama_carpim alanında. 9 koşuda 0 isabet, beklenen isabet ~%5–10/koşu.
- Dondurulmuş kuponlara dokunulmadı. Ek ön-kayıtlı varyant: Bolton-G ve Jason-G (48 ve 96 geçerli kombinasyon bütçesi; aynı açgözlü kurucu, bütçe geçerli sayıya göre). Bugünden itibaren dondurulur; karar tarihi 1 Ocak 2027 (≥ 300 koşu, yalnızca betimleyici: isabet oranı ve geri dönüş).

## Kontrol tarihleri
- **1 Kasım 2026**: ilk bakış (≈300 egzotik koşu). Yalnızca "kural çöküyor mu?" sorusu. Karar yok: bu hacimde aralık yaklaşık ±0,15.
- **1 Ocak 2027**: asıl değerlendirme (≈1.000+ koşu). Ana kural ve iki varyant yan yana, yarış günü bazında bootstrap %95 aralık; alt sınır 1,0'ı geçerse "kanıt", geçmezse "kanıt yok".
- **1 Nisan 2027**: 3 atlı kombine ikili ve Jason-1.50 için ilk anlamlı bakış (kupon sayısı az; yalnızca betimleyici). Bu tarihten önce karar verilmez.
