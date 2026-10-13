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
- 13 Ekim 2026, 16:10: -G bütçelerine 150 eklendi (48/96/150). 16:30: -G kurucusu "sürüm 2" oldu (çok başlangıçlı: tek yönlü ve iki yönlü ilk-iki başlangıçlarından en iyisi). Neden: kullanıcının makine fişi (6,7/6,7/...; 110 komb., modele göre %3,04) sürüm 1'in 100 kombinasyonluk kuponundan (%2,57) kombinasyon başına ~%8 verimliydi; sürüm 1 favori çiftini iki yönlü açmayı göremiyordu. Bugünkü 39 kupon için ortalama verim farkı yaklaşık +%15–25. Hiç sonuç görülmeden yapıldı; başlamış koşuların sürüm 1 -G kuponları olduğu gibi kaldı (kayıtta surum alanı yok = sürüm 1), başlamamışlar sürüm 2 ile yenilendi.

## Kontrol tarihleri
- **1 Kasım 2026**: ilk bakış (≈300 egzotik koşu). Yalnızca "kural çöküyor mu?" sorusu. Karar yok: bu hacimde aralık yaklaşık ±0,15.
- **1 Ocak 2027**: asıl değerlendirme (≈1.000+ koşu). Ana kural ve iki varyant yan yana, yarış günü bazında bootstrap %95 aralık; alt sınır 1,0'ı geçerse "kanıt", geçmezse "kanıt yok".
- **1 Nisan 2027**: 3 atlı kombine ikili ve Jason-1.50 için ilk anlamlı bakış (kupon sayısı az; yalnızca betimleyici). Bu tarihten önce karar verilmez.

## 13 Ekim 2026 — canlı pist durumu kaydı
Kocaeli kum pist "Nemli" (kullanıcı bildirimi, 17:37). data/pist_durum.csv'ye işlendi. Modellerde HİÇBİR değişiklik yok (ıslak-pist özelliği örnek azlığından kapalı; 1 Mart 2027'de yeniden sınanacak). Amaç: akşamki kron sayfasındaki resmi durumla karşılaştırıp bildirimin doğruluğunu ve bildirimden sonra öncül gün/koşu başı değişimini kayda geçirmek. Not: yalnız 17:45'ten önceki koşular için "canlı" anlam taşır.

## 13 Ekim 2026 — Adana 7'li ganyan devir sonucu (gözlem)
Adana 7'li ganyan (3–9. koşu, birim 2 TL) 11 Ekim'den 464.387 TL devirliydi; bugün tutturuldu, TV ödemesi 146.556,80. Kazanan: 6-7-11(9)-7-9-4-16(18). Model kuponları tutmadı. Ödeme/1 kupon varsayımı: ekran rakamı kupon başına (bursa 6'lı fişiyle tutarlı; teyit edilmedi). Kazanan sayısı ve gerçek net havuz bilinmiyor -> devir senaryo (iyimser/orta/kötümser) kalibrasyonu bekliyor; kazanan kupon sayısı gelince net havuz = ödeme x N - devir.

## 13 Ekim 2026 — Islak pist vekili (yağış) ön kayıt
Soru: 2023–2025 için resmi pist etiketi yok (kron yalnız 2026'dan). Open-Meteo günlük yağış (hipodrom koordinatı) ıslak pist vekili olarak kullanılabilir mi? Adım 1: 2026 etiketli günlerde vekilin doğruluğu (yağış 0/1/2 gün önce -> Nemli/Sulu/Islak): AUC. AUC<0,75 ise vekil kullanılmaz, deney biter. Adım 2 (yalnız adım 1 geçerse): Jason olasılığına, atın ÖNCEKİ vekil-ıslak koşularındaki artığı ile tek parametreli terim, LR testi, walk-forward OOS, 2023–2026 (çok daha fazla örnek). Tek test; sonuç ne olursa olsun modele eklenmez, 1 Ocak 2027 değerlendirmesine girer. Veri: data/hava/gunluk.csv (Actions ile çekilir).
SONUÇ (13 Ekim 2026): Adım 1 geçti — 3 günlük yağış toplamı resmi ıslak etiketi AUC 0,89 ile ayırıyor (eşik 12,5 mm, Youden 0,64, 368 etiketli gün). Adım 2: vekil-ıslak kum koşusu 1045 (2025-01 sonrası OOS), β=0,35, kazanç 0,0004 nats/koşu, LR=0,91, p≈0,34 → fark yok. Çıkarım: örnek 1045 koşuya çıktı ama etki yine ölçülemeyecek kadar küçük/yok; ıslak-pist özelliği modele EKLENMEZ. Betik: data/analiz/islak_vekil_testi.py. Yeniden test gerekmez (1 Mart planı iptal; yalnız etiketli veri 3x artarsa).

## 14 Ekim 2026 — Sıralı beşli: sıralama modeli (Harville düzeltmesi) ön kayıt
Soru: 2.–5. sıralar için Harville (p'ye orantılı sıradaki seçim) yerine pozisyona özgü üs γk (sıradaki seçim ∝ p^γk, k=2..5; Henery/Stern tipi) tam ilk-5 sırasının log-olabilirliğini artırır mı? Veri: 2025-01 → 2026-10 walk-forward OOS olasılıklar (Jason ve piyasa), ilk 5'i çözümlü koşular (beraberlik/ekür dışı). Eğitim: 2025 (γ ayrı ayrı, koşullu LL), sınama: 2026. Ölçüt: sınama LL/koşu kazancı (Harville'e göre), 5 sıra için ve her sıra için; p<0,05 bootstrap. Karar: kazanç anlamlıysa ve γ tutarlıysa (2025/2026 ikisinde de) kupon kurucuya aday; model/kupon canlıda DEĞİŞMEZ, 1 Ocak 2027 değerlendirmesinde karar. Betik: data/analiz/siralama_gama.py.
SONUÇ (14 Ekim 2026): Canlı kupon kurucu zaten pozisyona özgü üs kullanıyordu (G_M=[1,.80,.69,.69,.69], G_P=[1,.87,.74,.74,.74]; önceki oturumda kalibre edilmişti) — "yalnız Harville" demem hataydı. Yeni uyum (2025 eğitim, 2026 sınama, 4419 koşu): Jason γ = 0,79/0,66/0,58/0,52; canlı değerlere göre kazanç yalnız 5. sırada anlamlı (+0,009 nats/koşu, ~%1 tutma artışı), 2–4. sıralarda sıfır/eksi. Piyasa için aynı (+0,0055 yalnız 5. sıra). Sonuç: sıralama modeli zaten iyi kalibre, buradan büyük kazanç YOK. Canlıda değişiklik yapılmaz; isterse 5. sıra γ'sı 0,69→~0,55 küçük iyileştirme (aday, kontrol tarihi). Betik: data/analiz/siralama_gama.py.

## 14 Ekim 2026, 00:50 — Sıralı beşli "2 favori + 1 süpriz" yapısı (ÖN KAYIT, sonuç görülmeden)
Kupon: sıra 1,2,3'e hepsine {F1,F2,S} (F1,F2 = Jason olasılığı en yüksek iki at; S = piyasa (AGF) sıralaması >=4 olanlar arasında Jason olasılığı en yüksek at); sıra 4,5 mevcut açgözlü kurucuyla bütçeye (96 ve 150 geçerli komb.) kadar genişletilir. Karşılaştırma: aynı koşu ve bütçede mevcut kupon_g (Jason). Ölçüt: tutma oranı ve gerçek ödemeli getiri (ROI, bootstrap), 2025-01 sonrası ~1578 beşli koşusu. Tek varyant; başka varyant denenmez, denenirse ayrı kaydedilir. Önceki ikili "sürpriz+2 favori" sonucu KEŞİF'ti (CI 0,73–1,73, en büyük 3 ödeme çıkınca 0,91); bu test onun ileriye dönük sınavı değil, farklı bahis. Canlıda değişiklik yok.

## 14 Ekim 2026 — Sıralı beşli geriye test (gerçek ödemeler, 2025-01 sonrası, 1379 koşu, kupon_g, OOS olasılıklar)
ROI(A: ödeme kombinasyon başına) / ROI(B: x1,25 = 1 TL başına ödeme varsayımı). Tutan: Jason B48 23 (%1,7) 0,49/0,61; B96 31 (%2,2) 0,45/0,56; B150 43 (%3,1) 0,48/0,59. Bolton: 0,42/0,52; 0,51/0,64; 0,47/0,59. Piyasa (AGF olasılığıyla kurulan): B48 0,60/0,75; B96 0,50/0,62; B150 0,59/0,74. Tüm güven aralıkları üst sınırı ~1,07'yi geçmiyor; hiçbir hücre 1'i aşmıyor. Okuma: model/kupon hiçbir şey kesintinin üstüne taşımadı; piyasa olasılığıyla kurulan kupon Jason'dan kötü değil (hatta ROI nokta tahmini yüksek, fark anlamsız). B okuması (≈0,6–0,75) ~%28 kesinti beklentisiyle (~0,72) tutarlı, A okuması (~0,5) değil -> ödeme muhtemelen 1 TL başına (teyit gerekli).

## 14 Ekim 2026, 01:05 — Sıralı beşli kuponları yalnız oynanan koşulara
Hata: sistem 2. koşudan itibaren tüm koşulara beşli kuponu üretiyordu; sıralı beşli bazı koşularda oynanmıyor (Adana 7'de yok; Adana'da 2,5,6,8,9, Kocaeli'de 4,5,6,8 oynanmış). 13 Ekim özetimdeki "Adana 7'de -G kuponları tuttu" ifadesi GEÇERSİZ (o koşuda beşli yoktu). Skorlama zaten yalnız ödeme satırı olan koşulara işliyordu (istatistik etkilenmedi); görüntüde fazladan kupon vardı. Düzeltme: program CSV'sinde koşu bloğundaki bahis listesinde "SIRALI 5" varsa koşuya besli=True işaretlenir; yalnız besli=True koşulara kupon üretilir, besli=False olan başlamamış kayıtlar silinir, site de besli=False koşuları göstermez. Program CSV'si yoksa kupon üretilmez. Doğrulama: işaretlenen koşular gerçek ödeme satırlarıyla birebir aynı (Adana 2,5,6,8,9; Kocaeli 4,5,6,8).

## 14 Ekim 2026, 01:10 — Üçlü bahis biletleri yalnız oynanan koşulara
Beşlideki düzeltmenin aynısı üçlü (ÜÇLÜ BAHİS) için: program CSV'sinde koşu bloğunun bahis listesinde "ÜÇLÜ BAHİS" varsa koşuya uclu=True; yalnız o koşularda üçlü bileti/seçimi üretilir (deger.py, egzotik.py, site). Önceden üretilmiş başlamamış koşu kayıtlarındaki üçlü listeleri boşaltılır. CSV yoksa üçlü üretilmez. Doğrulama 13 Ekim: işaretlenenler gerçek ödeme satırlarıyla aynı (Adana 7; Kocaeli 2 ve 6). İstatistik daha önce de yalnız ödeme satırı olan koşuları sayıyordu, etkilenmedi; değişen yalnız gösterilen/üretilen bilet. İkili ve sıralı ikili her koşuda oynandığından değişmedi.
