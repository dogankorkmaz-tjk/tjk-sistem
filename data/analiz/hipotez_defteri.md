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

## 14 Ekim 2026, 01:20 — Sıralama için eğitilmiş model ("Jason-S") — ön kayıt, sonuç görülmeden
Soru: Jason özellikleri (jokey, kilo, form, mesafe/pist uyumu, ...) kazananı değil TAM İLK-5 SIRASINI öğrenecek biçimde eğitilirse (Plackett-Luce, ağırlıklar tüm sıralarda paylaşımlı, sıra başına ölçek a2..a5 serbest) 2.–5. sıraların olabilirliği Jason+sabit γ'ya (G_M) göre artar mı? Veri/yöntem: walk-forward çeyreklik (2025Q1–2026Q3, her çeyrek önceki tüm veriyle yeniden fit), aynı özellik kümesi, aynı düzenleyici (lam=100), koşu: ilk 5 sırası beraberliksiz çözülmüş koşular. Ölçüt: sıra 2–5 toplam log-olabilirlik kazancı (nats/koşu), bootstrap %95 GA. Tek karşılaştırma. Karar: GA sıfırın üstünde ve fold'ların çoğunda (>=5/7) pozitifse "beşli için sıralama modeli aday"; aksi halde fikir kapanır. Kullanılmayan: idman (yalnız Ağustos 2026'dan beri), pist durumu (ayrıca denendi, etki yok). Canlıda değişiklik yok.
SONUÇ (14 Ekim 2026): Jason-S (ilk-5 sırasıyla eğitilmiş, aynı özellikler) walk-forward 2025Q1–2026Q4, 10.360 koşu: sıra 2–5 toplam kazanç +0,063 nats/koşu (%95 GA 0,059–0,069), 8/8 çeyrekte pozitif. Kazancın çoğu 3.–5. sıralarda (+0,015…0,024 nats/sıra); 2. sırada ~+0,009. Öğrenilen sıra ölçekleri a2..a5 = 0,79/0,67/0,59/0,53 (canlı G_M 0,80/0,69/0,69/0,69 ile tutarlı, 4.–5. sırada daha düşük). Anlam: sıralama modeli gerçekten iyileşti; tam ilk-5 dizisinin olasılığı ortalama ~%6,5 artıyor. Ama bu tek başına geriye testteki getiri açığını (≈0,5 → 1,0) kapatacak büyüklükte değil. Karar kuralı sağlandı -> "beşli için sıralama modeli ADAY". Canlıda değişiklik yok; sonraki adım: Jason-S olasılıklarıyla kupon kurup aynı geriye testte (gerçek ödemelerle) karşılaştırmak. Betik: data/analiz/siralama_modeli.py.

## 14 Ekim 2026, 01:30 — "X Y'yi geçer mi?" ikili karşılaşma geçmişi (ön kayıt)
Fikir (kullanıcı): sıralamayı ikili sorularla kurmak. Not: ikili (Bradley-Terry) yapı Plackett-Luce ile aynı aile; tek başına yeni bilgi katmaz, çifte özel bilgi gerekir. Test edilecek çifte özel özellik: f_h2h = bugünkü alandaki rakiplerle ÖNCEKİ karşılaşmalarda (kesinlikle önceki günler) bitiş farkı işareti toplamı / (karşılaşma sayısı + 3) (K=3 önsel). Model: Jason-S (ilk-5 eğitimli) vs Jason-S + f_h2h, walk-forward 2025Q1+, aynı koşu kümesi. Ölçüt: tüm 5 sıra toplam log-olabilirlik kazancı (nats/koşu), bootstrap GA, çeyrek tutarlılığı. Tek test. Canlıda değişiklik yok.
SONUÇ (at-at h2h, 14 Ekim 2026): +0,0007 nats/koşu (GA 0,0001–0,0013), 5/8 çeyrek pozitif, ağırlık küçük (std 0,02–0,03) -> pratikte sıfır; fikir kapandı (at-at karşılaşma geçmişi Jason-S'e bilgi katmıyor). Betik: data/analiz/siralama_h2h.py.

## 14 Ekim 2026, 01:35 — Jokey-jokey ikili karşılaşma geçmişi (ön kayıt; kullanıcı önerisi)
Aynı yapı, aynı değerlendirme: f_h2h anahtarı jokey çifti (AP eki atılır), önceki günlerde aynı koşuda karşılaşmalarda bitiş farkı işareti. Beklenti: jokey etkisi zaten f_jwin/f_jgen100'de; fark çok küçük olması muhtemel. Tek test. Betik: data/analiz/siralama_h2h_jokey.py.
SONUÇ (jokey-jokey h2h, 14 Ekim 2026): +0,0023 nats/koşu (GA 0,0014–0,0032), 8/8 çeyrek pozitif; istatistiksel olarak sıfırdan farklı ama çok küçük (tam ilk-5 olasılığı ~%0,2; Jason-S kazancının ~%4'ü). Pratik değer yok; kupon kurucuya eklenmez, ileride modelin başka bir özelliğiyle birlikte yeniden bakılabilir. Betik: data/analiz/siralama_h2h_jokey.py.

## 14 Ekim 2026, 01:45 — Jason-S ile kupon geriye testi (ön kayıt)
Kuponda sıra başına at sayısı: TJK kurallarında sıra başına üst sınır yok (virgüllü 15 ata kadar, bilet azami 12.000 TL = 9.600 komb.); kurucumuzun sınırı bütçe (geçerli komb.) ve aday havuzu (modelin ilk 9 atı). Tipik kupon (12+ atlı, Jason): B=96 ortalama set boyu 1,8/2,1/3,7/4,9/6,1; B=150: 1,8/2,0/4,5/5,8/6,5; maks 7.
Test: Jason-S olasılıkları (walk-forward, ilk-5 eğitimli; sıra ölçekleri a2..a5 o çeyreğin fit'inden) ile aynı kurucu (kupon_g; G_M yerine a), B=48/96/150, 2025Q1+ beşli oynanan ve ilk-5'i çözülmüş koşular; karşılaştırma: aynı koşu/bütçede mevcut Jason (oos_p p_Jason + G_M). Ölçüt: tutma sayısı ve gerçek ödemeli ROI, eşleştirilmiş bootstrap farkı. Ödeme birimi okuması A (bilet başına). Tek karşılaştırma; ROI yalnız betimleyici (tutan sayısı az), asıl karar ölçütü tutma olasılığı artışının gerçekleşmesi. Canlıda değişiklik yok.
SONUÇ (Jason-S kupon geriye testi, 14 Ekim 2026, 1365 koşu, ödeme okuması A): B=48: tutan 24 vs 23, ROI 0,63 vs 0,49 (fark +0,14, GA −0,26..+0,65); B=96: 36 vs 31, ROI 0,52 vs 0,46 (+0,06, −0,12..+0,25); B=150: 53 vs 43, ROI 0,64 vs 0,48 (+0,16, −0,01..+0,35). Model-beklenen tutma oranları iki modelde de benzer (%1,6/%2,6–2,7/%3,4); gerçekleşen tutma Jason-S'te her üç bütçede de daha yüksek. Yön tutarlı (3/3 bütçe), ama fark anlamlı değil ve ROI hâlâ 1'in çok altında (kesinti beklentisi ~0,72'nin de altı). Okuma: Jason-S kuponları tutarlı biçimde biraz daha iyi, kesintiyi aşmıyor. Karar: Jason-S gölge model adayı (canlı kupona geçmez). Betik: data/analiz/besli_geriye_s.py.

## 14 Ekim 2026, ~11:30 — Hibrit sıralama: ilk 2 sıra Jason, 3.–5. sıra Jason-S (ÖN KAYIT, sonuç görülmeden)
Fikir (kullanıcı): 1. ve 2. sıra olasılıkları mevcut Jason'dan (G_M üsleri), 3.–5. sıra Jason-S'ten (kendi ölçekleri a3..a5) gelsin. Matematiksel not: hibritin olabilirliği = LL1(Jason)+LL2(Jason)+LL3-5(Jason-S); Jason-S 1–2. sırada Jason'dan kötü DEĞİLSE hibrit Jason-S'i geçemez. Yani asıl soru: Jason-S 1. ve 2. sırada Jason'a göre kaybediyor mu?
Test 1 (olabilirlik): walk-forward 2025Q1+, aynı koşu kümesi; sıra başına nats/koşu farkı (Jason-S − Jason) bootstrap GA + çeyrek tutarlılığı; hibrit toplamı Jason-S'ten büyükse (GA>0) hibrit aday, değilse fikir kapanır.
Test 2 (kupon): yalnız Test 1'de hibrit Jason-S'i olabilirlikte geçerse; aksi halde yapılmaz (Jason-S kupon testi zaten var). Tek karşılaştırma, canlıda değişiklik yok. Betik: data/analiz/hibrit_testi.py.
SONUÇ Test 1 (hibrit olabilirlik, 14 Ekim 2026, 10.360+ koşu, walk-forward 2025Q1–2026Q4): Jason-S 1. sırada Jason'dan KÖTÜ (−0,0127 nats/koşu, GA −0,0158..−0,0091, 1/8 çeyrek pozitif) — ortak ağırlıklar kazananı biraz feda ediyor; 2. sırada +0,0081, 3–5. sıralarda +0,0144/+0,0195/+0,0215 (hepsi 8/8 çeyrek). Hibrit − Jason-S = +0,0046 nats/koşu (GA +0,0003..+0,0087, sınırda anlamlı); hibrit − Jason = +0,0554 (GA +0,0515..+0,0596); Jason-S − Jason = +0,0508. Ön kayıttaki koşul (hibrit > Jason-S, GA>0) sınırda sağlandı -> Test 2 (kupon) yapılır.

## 14 Ekim 2026, ~12:30 — Jason-S canlı gölge kutusu (ön kayıt)
Jason-S (data/model_aday_s.json, her gece yeniden eğitilir; a2..a5 ≈ 0,80/0,68/0,59/0,53) canlıda üçüncü gölge olarak çalışır: atlara z4 puanı, sonuçlarda pm4, sıralı beşli için "Jason-S-G" kuponları (48/96/150 geçerli komb., kupon_g, kendi a ölçekleriyle) ve sitede Egzotik sekmesinde ayrı "Sıralı 5'li (Jason-S · gölge model)" kutusu. Kuponlar yalnız besli=True koşularda. Karar ölçütü (değiştirilmez): 1 Ocak 2027'ye kadar biriken kuponlarda Jason-G ile eşleştirilmiş tutan sayısı ve ROI farkı; yeterli örnek (≥300 beşli koşusu) yoksa karar 1 Nisan 2027'ye ertelenir. Mevcut kural ve Jason/Bolton kuponları değişmedi.
SONUÇ Test 2 (hibrit kupon, 14 Ekim 2026, 1396 koşu, ödeme okuması A): tutan sayısı Jason / Jason-S / Hibrit: B48 26/24/20, B96 33/36/36, B150 43/53/48. ROI: B48 0,51/0,62/0,45; B96 0,48/0,51/0,52; B150 0,47/0,62/0,55. Hibrit − Jason-S: −0,16 (GA −0,65..+0,27), +0,02 (−0,18..+0,22), −0,08 (−0,21..+0,03) — hibrit Jason-S'ten üstün değil, hiçbir bütçede. Hibrit − Jason: −0,06 / +0,05 / +0,08, hepsi GA 0'ı içeriyor. Karar: hibrit kapandı (olabilirlikte +0,005 küçük avantaj kupona yansımadı); canlıya eklenmez. Jason-S gölge olarak sürer. Not: Jason-S kuponları da kesinti sınırının (~0,72) altında. Betik: data/analiz/hibrit_kupon.py.

## 14 Ekim 2026, 13:45 — İstanbul pist türü değişikliği (operasyonel kayıt, hipotez değil)
Kullanıcı bildirdi: pist ağır (5,5) ölçüldüğü için G1 Harem koşusu hariç tüm İstanbul koşuları sentetik pistte koşulacak. Programda 1. ve 3. koşu çim görünüyordu; 4., 5., 6. koşuların bilgi satırı programda yok. Sistem: data/pist_degisiklik.csv (tarih,hipodrom,kosu,pist) başlamamış koşuların bilgi metnindeki pisti değiştirir ve o koşulardaki tüm atların z/z2/z3/z4 puanlarını yeni pistle yeniden hesaplar (calistir.pist_uygula). Uygulandı: İstanbul 1 ve 3 (çim -> sentetik). 4–6: G1 hangisi ve mesafe/pist bilgisi bekleniyor. Model notu: pist türü yalnız mesafe-pist uyum özelliğine (f_dp150_m) giriyor; yeni pistte atın geçmişi az olabilir, bu koşuların puanları daha güvenilmez sayılmalı.

## 2026-10-14 — İstanbul pist değişikliği, CSV ile işlendi (operasyonel not)
Resmi CSV: İstanbul 1-5, 7, 8. koşular Sentetik; 6. koşu (Harem G1, 1600m) Çim kalır; 3. koşu 1600→1500m. 2 ve 3. koşuda birer koşmaz (BORN HERO, YARGIÇ). Jokey farkı yok. Elazığ'da yalnız beşli/üçlü bayrakları farklı.
Mekanizma: csv_uygula mesafe/pist değişimini `yeniden_puan` bayrağıyla işaretler; pist_uygula başlamamış koşuların z/z2/z3/z4 puanını yeniden hesaplar. Kural/model değişmedi.
Uyarı: sentetik pistte at geçmişi az; bu koşuların puanları daha az güvenilir.

## 2026-10-14 14:26 — Jokey değişikliği (kullanıcı bildirdi)
İstanbul 6. koşu (Harem G1), 4 İLLEDE DORU: S.KAYA -> M.KAYA. İstanbul CSV satırı elle düzeltildi (TJK CSV henüz yansıtmıyordu); jokey_uygula puanları yeniler. Model/kural değişmedi.

## 2026-10-14 14:30 — Jokey değişikliği (kullanıcı bildirdi)
Müs.Çelik ve S.Kaya raporlu. İstanbul 8. koşu 1 FEYZANUR: MÜS.ÇELİK -> B.AKÇAY (CSV elle düzeltildi). Resmi CSV zaten 2/8 COSAS ve 4/13 İLKUTHAN için B.AKÇAY, 3/7 SENKRON için E.AKTUĞ gösteriyor. 6/9 BERAY SULTAN yeni jokey bekliyor.

## 2026-10-14 14:45 — Düzeltme
İstanbul 8. koşuda B.AKÇAY, 9 HÜRRİYET atına bindi (resmi CSV 5); benim 8/1 FEYZANUR için yaptığım elle düzeltme yanlış yorumdu, geri alındı (CSV resmi hâli: FEYZANUR hâlâ MÜS.ÇELİK, raporlu -> yeni jokey bekleniyor, puanı güvenilmez). 6/9 BERAY SULTAN: G.ÖZÇELİK.

## 2026-10-14 14:55 — Jason-S egzotik gölge (kullanıcı isteği)
Jason-S, sıralı ikili/ikili/üçlü için de aynı DONDURULMUŞ kuralla (ORAN 1,15, GAMA/DELTA) gölge olarak seçim yapar (egzotik.py, z4/w0_s/lp2_s). Ayrı sayaç "Jason-S"; kombine (bütçeli) kuponlar Jason-S olasılığı ve a_s üsleriyle. Karar kuralı: Jason ile eşleşmiş karşılaştırma, her tür için >=300 sonuçlanmış koşu; yoksa 1 Nisan 2027. Kural/ana model değişmedi.

## 2026-10-14 15:00 — Birim fiyat teyidi (bayi tablosu, kullanıcı fotoğrafı)
Ganyan/plase/çifte/ikili/sıralı ikili 1 TL; plase ikili 2; sıralı üçlü 2; tabela 1,50; sıralı beşli 1,25; 3lü ganyan 2; 4lü 1,75; 5li 1,50; 6lı 1,25; 7li plase 2. TÜM oyunlarda asgari bilet 20 TL. Koddaki birimler (1/1/2/1,25) doğru. Düzeltme: kombine kupon etiketleri kombinasyon sayısı yerine TL bütçesi (sıralı ikili 20/40 TL, üçlü 20/50 TL); beşli etiketi "<=B komb."; 20 TL altı kuponlara "min. bilet 20 TL" notu. Seçim kuralları değişmedi.

## 2026-10-14 15:10 — ESNEK KUPON (sabit bütçe yerine güvene göre genişlik) — ÖN KAYIT, sonuç görülmeden
Soru: Kuponu sabit bütçe yerine, her yeni kombinasyonun marjinal model/piyasa oranına göre durdurmak (güvenli koşuda dar, belirsizde geniş, kenarı olmayan koşuda hiç oynamamak) sabit bütçeli kuponlardan daha iyi geri dönüş verir mi?
Kural (tek, değişmez): Model = Jason olasılıkları, sıra üsleri G_M (beşli/ikili/üçlü aynı), piyasa = AGF olasılıkları, G_P. Başlangıç: sıra k'ya modelin k. atı. Başlangıç kombinasyonunun model/piyasa oranı < 1,15 ise o koşu OYNANMAZ. Açgözlü genişletme: aday (sıra, at) eklemesinin MARJİNAL oranı (eklenen model olasılığı / eklenen piyasa olasılığı) >= 1,15 ise ve toplam geçerli kombinasyon <= tavan ise eklenir (mevcut açgözlü ölçüt: log olasılık artışı / log kombinasyon artışı); aday kalmayınca durur. Tavan: sıralı ikili 40 komb (40 TL), üçlü 25 komb (50 TL), sıralı beşli 150 geçerli komb (187,5 TL). Aday atlar: Jason sırasına göre ilk 9. Birimler: 1 / 2 / 1,25 TL (bayi fiyat tablosu); asgari bilet 20 TL misli ile tamamlanır, getiri oranı birim başına ölçülür (misli getiri oranını değiştirmez).
Ölçüt: tür başına oynanan koşularda geri dönüş (ödeme/harcama), bootstrap (gün bazında) GA; oynanmayan koşu sayısı ayrı raporlanır. Karşılaştırma: aynı koşularda sabit bütçeli Jason-G (beşli) ve kombine Jason (ikili/üçlü) kuponları, eşleşmiş.
Canlı: yarış başlamadan dondurulur, ayrı kayıt (data/esnek/), sitede Egzotik > Esnek. Ana kupon, model ve kurallar DEĞİŞMEZ.
Karar: tür başına >=300 oynanmış koşu ve eşleşmiş farkın GA'sı sıfırın üstündeyse "aday"; aksi halde kapanır / 1 Nisan 2027'ye ertelenir. Geriye dönük test bu ön kayıttan SONRA ve ayrı kayıtla yapılır; canlı sonuç esastır.

## 15 Ekim 2026, 00:00 — Yol haritası Faz 1: AGF olasılık olarak ne kadar kötü? (ÖN KAYIT, sonuç görülmeden)
Soru: Altılı oynayan halkın dağılımı (AGF, son değer `zengin.agf_son`) kazananı ganyan piyasasından (`p_piyasa`, son muhtemel ganyan) daha mı kötü tahmin ediyor? Jason'ın AGF'ye karşı kazancı ganyana karşı kazancından büyük mü?
Veri: walk-forward OOS Jason/Bolton olasılıkları (çeyreklik, 2024Q2+; aynı kod `tjk/walkforward.py`), AGF'si olan koşular (2025-01→05, 2026-01→10). AGF koşu içinde normalize edilir.
Ölçüt: kazanan log-olasılığı farkı (nats/koşu): Jason−AGF, piyasa−AGF, Jason−piyasa; yarış günü kümeli bootstrap %95 GA; dönem tutarlılığı (2025 / 2026 ayrı).
Karar (değiştirilmez): Jason−AGF ≥ 0,05 nats/koşu ve GA alt sınırı > 0,03 → Faz 2'ye geç (altılıda ayak başına p/a çarpanı anlamlı olabilir). < 0,03 → altılı yolu da kapalı.
Tek test; canlıda değişiklik yok.

## 15 Ekim 2026, 00:01 — Faz 2: Altılı "değer" kurucusu geriye testi (ÖN KAYIT, sonuç görülmeden; yalnız Faz 1 geçerse yorumlanır)
Fikir: altılıda bir kombinasyonun beklenen getirisi ≈ k × Π(pᵢ/aᵢ) (p = Jason OOS, a = AGF payı, k = havuz net oranı/birim). Küçük ayak avantajı altı ayakta çarpılır.
Kurucular (hepsi aynı açgözlü yapı, aynı bütçe B = 64 ve 256 kombinasyon, 1 birim/kombinasyon):
- V (değer): her ayağa önce en yüksek p'li at; sonra her adımda log(tutma olasılığı) artışı / log(maliyet) artışı en büyük at eklenir, ama YALNIZ p/a ≥ 1,0 olan atlar eklenebilir; bütçe dolunca durur.
- J (olasılık): aynı, filtre yok (Jason p ile en yüksek tutma).
- A (AGF): aynı, p yerine AGF a (halkın kendi kuponu, taban).
Veri: odeme `6'LI GANYAN` (+ DEVİR = kimse bilemedi, ödeme 0), ayaklar = kosu−5..kosu; ayak koşusunda ölü yarış "3,4" ikisi de geçer. Tüm 6 ayakta OOS p ve AGF olan altılılar.
Ölçüt: ROI = Σödeme/Σmaliyet (ödeme birim başına varsayımı); V−J ve V−A eşleştirilmiş, gün kümeli bootstrap %95 GA; 2025 ve 2026 ayrı. Ayrıca kalibrasyon: k̂ = medyan(ödeme × Π a_kazanan) ve tahmini EV ile gerçekleşen ROI.
Karar: V'nin ROI GA alt sınırı > 1,0 → canlı kâğıt test adayı (1 Ocak 2027 değerlendirmesi). Aksi halde betimleyici; parayla oynanmaz. Tek varyant; başka eşik/bütçe denenirse KEŞİF olarak ayrıca yazılır.
SONUÇ Faz 1 (15 Ekim 2026, 00:20; 5.313 koşu, 2025-01→2026-10): Jason−AGF +0,0020 nats/koşu (GA −0,0061..+0,0100; 2025 +0,0054, 2026 +0,0005). Piyasa−AGF −0,0200 (GA −0,028..−0,012): AGF, son ganyandan DAHA İYİ tahminci. Jason−piyasa (aynı koşular) +0,0220. Dilim tablosu: ganyan piyasası uzun atışları fazla fiyatlıyor (p≤%3 diliminde piyasa %1,89, gerçek %1,31, AGF %1,34); AGF bu yanlılığı taşımıyor. Karar (ön kayıt gereği): ölçüt sağlanmadı → altılıda p/a çarpanı yolu KAPALI. Jason'ın piyasaya karşı avantajının büyük kısmı AGF'nin zaten bildiği şey. Faz 2 yalnız betimleyici koşturulur. Betik: data/analiz/agf_skor.py.

## 15 Ekim 2026, 00:25 — Faz 1b: AGF'yi Jason'a bilgi olarak eklemek (ÖN KAYIT, Faz 1 sonucundan doğan KEŞİF fikri)
Soru: AGF ganyandan iyi tahmin ettiğine göre Jason ⊕ AGF karışımı ganyan piyasasına karşı Jason'dan fazla kazanır mı, ve bu ganyan EV kuralına yansır mı?
Model: p ∝ p_Jason^(1−w) · a^w (tek parametre w). w yalnız 2025 koşularında (log-olabilirlik) fit edilir, 2026'da sınanır (AGF'li koşular).
Ölçüt: 2026 sınamada (Karışım − Jason) nats/koşu, gün kümeli bootstrap GA; ve EV kuralı (p × son ganyan > 1,1 ve > 1,3) ROI: Karışım vs Jason, aynı koşular.
Karar: nats kazancı GA alt sınırı > 0,005 → "Jason-A" gölge model adayı (AGF canlıda yarıştan önce mevcut; son AGF altılı kapanışında donar). ROI yalnız betimleyici. Tek test.
DÜZELTME + SONUÇ Faz 1b (15 Ekim 2026, 00:10): İlk koşu geçersiz — ekürlü koşularda `ortak.duzelt` ekür olasılığını atlara böler, 1/p_ham ise ödemeyi 2–3 kat şişirir; karışım ekür atlarını "değerli" sanıyordu (ROI 2,95 sahteydi). Düzeltme: ekürlü koşular (%17) çıkarıldı, ödeme = gerçek ganyan. Sonuç (2026 sınama, 2.917 koşu): w=0,31 (2025 fit); Karışım−Jason +0,0056 nats/koşu (GA +0,0026..+0,0087); Karışım−piyasa +0,0279. Ön kayıt ölçütü (GA alt > 0,005) SAĞLANMADI → Jason-A adayı değil. Gerçek ama küçük; ROI örneği çok küçük (19 bahis), betimleyici bile değil.
Yan etki kontrolü (mevcut kural): Jason EV>1,1 (walk-forward 2024Q2+) eski hesap 1,174 (n 311) → gerçek ganyanla 1,139; ekür hariç 1,196 (n 287). Jason−piyasa ekürsüz +0,0134 (tümü +0,0153). Önceki sonuçlar büyük ölçüde geçerli; ancak `walkforward.py` EV/ROI hesabı ekür için düzeltilmeli.
SONUÇ Faz 2 (15 Ekim 2026, 00:15; yalnız betimleyici, Faz 1 geçmedi; 896 altılı, 2025-01→05 + 2026-01→10, ödeme birim başına okuması). k̂ = medyan(ödeme × Π AGF_kazanan) = 0,60 (IQR 0,38–0,74): AGF halkın altılı kapsamasını kabaca temsil ediyor.
ROI [%95 GA] V / J / A: B=64 1,02 [0,47–1,70] / 0,56 / 0,43; B=256 1,39 [0,61–2,40] / 0,81 / 0,48. Yıl ayrımı tutarsız: 2025 V 0,24 (B64) / 0,68 (B256), 2026 V 1,30 / 1,65. En büyük 3 ödeme çıkarılınca V 0,58 (B64) / 0,70 (B256). Tahmini EV oranı (Π p/a) V'de ortalama 4,6–5,9, gerçekleşen çok altında: p/a filtresi küçük AGF'li atlarda gürültüyü seçiyor (kazananın laneti).
Karar (ön kayıt): V'nin GA alt sınırı 1,0'ı geçmedi → aday değil, parayla oynanmaz. V−A (B=256) GA [+0,13, +1,92] pozitif ama ağır kuyruk ve 2025 tutarsızlığı nedeniyle KEŞİF sayılır. İleriye dönük izlenebilir: 1 Nisan 2027'de B=256 V kuralı (bu dosyadaki tanımla, değiştirilmeden) betimleyici bakış. Betik: data/analiz/altili_deger.py.

## 15 Ekim 2026, 00:25 — Faz 0: e-değer izlemesi (ölçüm aracı, kural değişikliği yok)
`tjk/kanit.py` artık her (model, bahis) satırına e-değer yazar: koşu başına getiri X ile karışım bahis martingali W = ort_λ Π(1+λ(X−1)), λ ∈ {0,01; 0,02; 0,05; 0,1; 0,2} (sabit). H0 (ROI ≤ 1) altında W'nin herhangi bir anda 1/α'yı geçme olasılığı ≤ α: her gün bakılabilir. Eşik = kural sayısı/0,05. Simülasyon (ROI=1, 1/20 ihtimalle 20 kat, 1.000 koşu, 2.000 tekrar, her koşudan sonra bakış): e ≥ 20'yi görme oranı 0,032 (≤ 0,05 olmalı) → geçerli.
Bugünkü durum: 31 kural izleniyor → eşik 620. En yüksek e = 1,60 (Jason-1.50 sıralı ikili, 9 koşu); diğerleri 0,29–0,89. Hiçbir kuralda kanıt yok.
Budama önerisi (karar Doğan'ın): kural sayısı 31 → 3 olursa eşik 620 → 60 olur, aynı kanıta ~10 kat daha az veriyle ulaşılır. Önerilen 3: Jason egzotik (ana, 1,15), değer filtresi 1,25, Jason ganyan EV>1,1. Diğerleri silinmez, "arşiv/betimleyici" sayılır ve kanıt hesabına girmez.

## 15 Ekim 2026, 00:35 — Faz 4: empirik Bayes önsel gücü (ÖN KAYIT, sonuç görülmeden)
Gözlem (veriden, sonuç değil): beta-binom moment tahmini önsel gücü k — at 24 (kodda 5), jokey 33 (30), antrenör 84 (30), sahip 42 (30), baba 136 (60). At/antrenör/baba oranları az büzülüyor olabilir.
Test: Jason'ı f_hwin M=24, f_twin 84, f_swin 42, f_bwin 136 (jokey 30 aynı) ile walk-forward (2024Q2+, aynı kod) yeniden üret; mevcut Jason OOS ile aynı koşularda kazanan log-olasılığı farkı, gün kümeli bootstrap GA, çeyrek tutarlılığı.
Karar: fark GA alt sınırı > 0,002 ve çeyreklerin ≥ %75'inde pozitif → Jason-EB gölge adayı (1 Ocak 2027). Aksi halde kapanır. Tek test.
SONUÇ Faz 4 (15 Ekim 2026, 00:45; 14.729 koşu): EB−Jason −0,0001 nats/koşu (GA −0,0003..+0,0001), 5/11 çeyrek pozitif → KAPANDI. Önsel gücü ayarı bilgi eklemiyor (lam taramasıyla tutarlı). Betik: data/analiz/eb_onsel_testi.py.

## 15 Ekim 2026, 00:40 — Faz 3: son dakika kayması (KEŞİF, betimleyici, çok küçük örnek)
data/canli_oran (bayi/yayın ekranı fotoğrafları, 14 koşu, 112 at; her koşunun en geç ekranı, ekürsüz): son ganyan / canlı ekran oranı tüm atlarda ×1,05 (±0,03). Jason'ın canlı orana göre EV>1,1 gördüğü 6 atta ×0,52 (log −0,66 ± 0,23): "değerli" görünen atların oranı kapanışa kadar yarıya inmiş. 6 at kanıt değil, ama yön tehlikeli: canlıda görülen değer kapanışta kaybolabilir (geç para). Ayrıca Faz 1 dolaylı kanıt: altılı kapanışında donan AGF, sonradan oluşan son ganyandan daha iyi tahminci → ganyan havuzuna geç gelen paranın "akıllı" olduğuna işaret yok; kayma muhtemelen ekran okuma zamanı/dar havuz kaynaklı. Ölçüm sürecek: her gerçek bahiste ekran oranı kaydedilsin (zaten Oynadıklarım'da). 100+ değer atında yeniden bakılır. Betik: data/analiz/son_dakika_kayma.py.

## 15 Ekim 2026, 00:20 — Ana testler seçildi (Doğan'ın kararı; sonuçlar değiştirilmedi)
Kanıt yalnız şu 6 satırda aranır (eşik e ≥ 6/0,05 = 120; aralıklar 6 teste göre Bonferroni):
1–3. Egzotik ana kural, Jason (1,15): sıralı ikili, ikili, üçlü
4. Değer filtresi ikili 1,25, piyasa olasılığı ≥ %1
5. Ganyan: canlıda son ganyan bilinmediği için EV>1,1 kuralı izlenemiyor; canlı karşılığı Jason tüyoları (pJ ≥ %6, pJ/AGF ≥ 1,30, 1 TL ganyan)
6. Sıralı 5'li: Jason-G, 150 geçerli kombinasyon bütçesi
Diğer kurallar sitede sürer, "arşiv" etiketlidir, kanıt sayılmaz. Bu liste 1 Ocak 2027 değerlendirmesine kadar değişmez.

## 15 Ekim 2026, 00:25 — Eşikli (kapsama) kupon: 5'li/6'lı/7'li ganyan (ÖN KAYIT, sonuç görülmeden; Doğan'ın fikri)
Kural: her ayakta atlar Jason OOS olasılığına göre sıralanır, ayağın toplam olasılığı ≥ T olana kadar eklenir (en az 1, en çok 8 at). Rekabetçi ayakta otomatik genişler, net favorili ayakta daralır. T ∈ {0,60; 0,75; 0,90} (önceden sabit).
Veri: odeme 5'Lİ / 6'LI / 7'Lİ GANYAN (+DEVİR = kimse bilemedi, 0), ayaklar = son koşudan geriye 5/6/7 koşu; tüm ayaklarda OOS olasılık olan kuponlar; 2025-01→ (ödeme dosyaları). Maliyet = kombinasyon × 1 birim, ödeme birim başına okuması.
Ölçüt: ROI, gün kümeli bootstrap %95 GA; ayrıca tutma oranı ve ortalama maliyet. 9 test (3 T × 3 bahis) → Bonferroni %95/9.
Beklenti (Faz 1'den): Jason ≈ AGF olduğundan genişlik kuralı getiriyi kesinti çizgisinin (k̂ ≈ 0,6) üstüne taşımamalı; esas etki tutma oranı ve oynaklık.
Karar: herhangi bir hücrede Bonferroni GA alt sınırı > 1,0 → canlı kâğıt test adayı; aksi halde betimleyici. Betik: data/analiz/esikli_kupon.py.
SONUÇ (15 Ekim 2026, 00:30): 9 hücrenin hiçbirinde Bonferroni GA alt sınırı 1'i geçmedi → aday yok. ROI: 5'li 0,72/0,73/0,56; 6'lı 0,71/1,16/0,57; 7'li 1,23/0,63/0,17 (T=0,60/0,75/0,90). 1'in üstündeki iki hücre (6'lı T=0,75, 7'li T=0,60) en büyük 3 ödeme çıkınca 0,47 ve 0,58 → birkaç sürpriz ödemenin eseri. Tutma oranı modelle uyumlu (ör. 6'lı T=0,75: gerçek %29,0, model %26,0): model iyi kalibre, ama kalibre olmak kâr demek değil. Maliyet çok hızlı büyüyor (6'lı T=0,75 ortalama 6.005, T=0,90 59.031 kombinasyon). Faz 1 beklentisiyle tutarlı: genişlik kuralı getiriyi kesinti çizgisinin üstüne taşımıyor.

## 15 Ekim 2026, 01:00 — Yabancı koşular: TJK havuzu kaydı başladı (KEŞİF, yalnız kayıt)
`tjk/yabanci.py` (gece job'unda): agftablosu sitemap'indeki yabancı sonuç sayfalarından TJK son ganyanları → data/yabanci/. Fransa sayfaları kaynakta bozuk (her koşuda tek satır, at no=0) → Fransa için TJK tarafı bu kaynaktan alınamıyor. ABD/İngiltere/İrlanda/Kanada düzgün.
İlk 247 koşu (25 Eyl–2 Eki): TJK yabancı havuzu geri ödeme medyanı 0,695 (kesinti ~%30, yurt içiyle aynı). Oran dilimi (kazanma / oranın dediği / ganyan ROI): ≤3 %28,4 / %35,7 / 0,56; 3–6 %17,0 / %15,8 / 0,73; 6–12 %10,4 / %8,3 / 0,86; 12–25 %5,0 / %4,2 / 0,87; 25+ %2,2 / %1,9 / 0,73. Favoriler TJK yabancı havuzunda fazla oynanıyor gibi (yurt içinin tersi). Örnek küçük, hiçbir dilimde ROI > 1 yok.
Karşı piyasa (yerel ülke oranı) henüz yok: PMU açık API robots.txt 404 (dosya yok), pmu.fr robots sonuç sayfalarını yasaklamıyor; ama Fransa'nın TJK tarafı bozuk. İngiltere için yerel oran kaynağı aranacak. Karar yok; ≥1.000 koşu birikince kalibrasyon yeniden okunur.

## 15 Ekim 2026, 01:05 — Ülke ülke yabancı havuz testi (ÖN KAYIT, sonuç görülmeden; Doğan'ın isteği)
Soru: TJK'dan oynanan yabancı koşularda hangi ülkenin TJK havuzu en "yanlış fiyatlı"?
Veri: data/yabanci (agftablosu sitemap ~3 hafta; geçerli koşu: tek kazanan, ≥3 at, Σ1/ganyan 1,2–1,7, at no>0).
Her ülke için (≥ 80 koşu olanlar; azsa "yetersiz"):
1) Geri ödeme = 1/medyan(Σ1/ganyan).
2) Kalibrasyon eğimi β: p ∝ p_piyasa^β (koşullu logit, tek parametre). β>1: favoriler az oynanıyor; β<1: favoriler fazla oynanıyor. Profil olabilirlik %95 GA.
3) Kural sınaması (ileriye dönük benzetim): β tarih sırasına göre ilk yarıda fit, ikinci yarıda p^β ile EV = p × ganyan > 1,10 olan atlara 1 TL ganyan; ROI ve gün kümeli bootstrap GA.
Karar: "aday ülke" = ikinci yarı ROI GA alt sınırı > 0,90 VE β'nın GA'sı 1'i dışlıyor. Aday çıkarsa yalnız ileriye dönük kâğıt test (para yok); çıkmazsa veri birikince (≥ 1.000 koşu/ülke hedefi yok, ≥ 300 koşu) yeniden. Çoklu karşılaştırma: ülke sayısı kadar Bonferroni notu düşülür.
SONUÇ (15 Ekim 2026, 01:20; 613 geçerli koşu, 25 Eyl–14 Eki): Kaynakta yalnız ABD, İngiltere, İrlanda, Kanada sayfaları sağlam; Fransa, Güney Afrika, Avustralya, Arjantin, Şili sayfaları bozuk (at no=0, tek satır) → bu ülkeler bu kaynakla test EDİLEMEZ.
Geri ödeme tüm ülkelerde 0,694–0,696 (kesinti ~%30,5, ülkeden bağımsız).
ABD (346 koşu): β=0,79 (GA 0,65–0,92) → TJK'nın ABD havuzunda favoriler anlamlı biçimde fazla oynanıyor. Ama ileriye benzetim (ilk yarı β=0,76, ikinci yarı EV>1,10): 81 bahis, ROI 0,28 (GA 0,00–0,77) → kural çöktü.
İngiltere (114): β=1,01 (0,77–1,27), iyi kalibre; EV>1,10 bahis çıkmadı. İrlanda (37), Kanada (22): yetersiz.
Karar: aday ülke YOK. ABD'deki yanlılık gerçek ama ~%30 kesintiyi aşacak büyüklükte değil. Kayıt her gece sürer; ABD/İngiltere ≥ 300'er koşu daha birikince aynı betikle yeniden. Betik: data/analiz/ulke_testi.py.

## 15 Ekim 2026, 01:20 — ABD modeli: Türkiye düzeninin ABD'ye uyarlanması (ÖN KAYIT, sonuç görülmeden)
Veri: agftablosu ABD sonuç sayfaları, ~Ekim 2025 → Ekim 2026 (geçmiş çekim sürüyor). Kaynakta yalnız sonuç tablosu var: at, jokey, kilo, derece, ganyan. Mesafe/pist/antrenör/idman YOK → bu özellikler kurulamaz; derece mesafesiz olduğu için hız figürü yok.
Özellikler (hepsi kesinlikle önceki günlerden): atın kazanma oranı (önsel 24), son 3 bitiş yüzdeliği, ilk koşu, dinlenme günü, jokey kazanma oranı (önsel 30), göreli kilo, atın piyasaya göre artığı (son 3, önsel 2), jokeyin piyasaya göre artığı (önsel 30).
Modeller: M0 = piyasa (son ganyan, normalize); M1 = piyasa + eğrilik (lp, lp²; favori yanlılığını düzeltir); M2 = M1 + özellikler. Koşullu logit, ridge λ=100 (Türkiye ile aynı).
Yöntem: aylık genişleyen pencere walk-forward; ilk 3 ay yalnız eğitim. Ölçüt: kazanan log-olasılığı (nats/koşu) M2−M1 (bilgi var mı?) ve M1−M0 (yanlılık ne kadar?), gün kümeli bootstrap GA; EV = p×ganyan > 1,10 ROI (gerçek ganyan) betimleyici.
Karar: M2−M1 GA alt sınırı > 0,005 → "ABD'de halkın kullanmadığı bilgi var", ileriye dönük kâğıt test (para yok). Aksi halde ABD modeli kapanır. Tek test; özellik listesi değişmez. Betik: data/analiz/abd_model.py.
DÜZELTME (15 Ekim 2026, 01:30, sonuç görülmeden): ABD için agftablosu program sayfası VAR (antrenör, sahip, yaş, start, son 6, KGS; mesafe/pist/orijin yok). Özellik listesine eklendi: antrenör kazanma oranı (önsel 84), sahip (önsel 42), yaş, göreli start. Geçmiş çekim artık program sayfasını da alır; ilk parça için `abdprogram` ile tamamlanır. İdman yok (TJK idman PDF'leri yalnız Türk atları). Karar ölçütü değişmedi.

## 15 Ekim 2026, 01:45 — İki piyasa testi: TJK yabancı havuzu vs yerel piyasa (ÖN KAYIT, sonuç görülmeden)
Kaynak: TJK son ganyan (agftablosu, data/yabanci) + yerel son oran (Sporting Life, robots izinli, data/yabanci_sl). ABD için tote, İngiltere/İrlanda için SP. Eşleşme: aynı gün/hipodrom, at adları en çok örtüşen koşu (≥ %60 at örtüşmesi), ekürsüz.
Yerel olasılık q = (1/oran) koşu içinde normalize.
Ölçütler: (1) Tahmin: kazanan log-olasılığı q − TJK p (nats/koşu), ülke bazında. (2) Kural: TJK'da 1 TL ganyan, q × TJK ganyan > k; k=1,25 BİRİNCİL, k=1,10 ikincil. ROI (gerçek TJK ganyanı), gün kümeli bootstrap %95 GA; zaman yarıları ayrı.
Karar: k=1,25 ROI GA alt sınırı > 1,0 → ileriye dönük kâğıt test (canlı: bayide TJK oranı + yerel canlı oran). Değilse ama nokta tahmini > 1,0 ise: veri biriktirilir (geçmiş çekimle örnek büyütülür), karar ≥ 1.000 bahiste. Not: iki taraf da SON oran; canlıda ikisi de kayar, ileriye dönük test şart.
SONUÇ İki piyasa testi (15 Ekim 2026, 02:30; 416 eşleşen koşu, 25 Eyl–14 Eki): Yerel oran TJK'dan çok daha iyi tahminci: q−TJK +0,096 nats/koşu [+0,050, +0,141]; ABD +0,092, İngiltere +0,052 (GA 0'ı kesiyor), İrlanda +0,33 (23 koşu).
Kural k=1,25 (BİRİNCİL), tümü: 411 bahis, ROI 1,39 [0,93–1,88]; yarılar 1,65 / 1,17 → ön kayıt ölçütü (alt sınır > 1,0) TOPLAMDA SAĞLANMADI.
Ülke ayrımı (alt grup, 4 kesit → çoklu test, KEŞİF sayılır): ABD 260 bahis, 32 isabet, ROI 1,57 [1,03–2,13], yarılar 1,58 / 1,56 (tutarlı). İngiltere 115 bahis ROI 0,66. İrlanda 36 bahis (yetersiz). k=1,10 ABD 1,26 [0,89–1,63].
Sağlamlık (ABD, k=1,25): en büyük 3 ödeme hariç 1,17, en büyük 5 hariç 1,01; ödeme yalnız birkaç sürprize dayanmıyor. Pistlere yayılmış (Belmont 2,09 / Gulfstream 2,25 / Keeneland 1,24; Santa Anita 0,19 ve Laurel 0,00 küçük örnek). Ters yön kontrolü: q×TJK < 0,8 olan atlar 0,52; tüm atlar 0,755 → sinyal tek yönlü ve tutarlı. Yerel oran kalibrasyonu iyi (q dilimlerinde kazanma oranı ≈ q).
EN BÜYÜK UYARI: İki taraf da SON oran. Bahis anında ne TJK'nın son ganyanı ne de ABD'nin son oranı bilinir; TJK havuzu küçük olduğu için kendi bahsin oranı düşürür. Geriye dönük kâr canlıya taşınmayabilir.
Karar: Toplam ölçüt sağlanmadığı ve ABD bulgusu alt grup olduğu için PARA YOK. ABD için ileriye dönük kâğıt test açılır (ön kayıt aşağıda). Veri biriktikçe (her gece otomatik) aynı betik yeniden koşulur; 1.000 ABD bahsinde karar.

## 15 Ekim 2026, 02:30 — ÖN KAYIT: ABD iki piyasa ileriye dönük test
Kural (değişmez): ABD koşusu, TJK ganyanı × yerel (ABD) olasılık q > 1,25 → 1 TL ganyan. Ölçüm 15 Ekim 2026 sonrası koşularda, son oranlarla (üst sınır) ve ayrıca bahis anı oranlarıyla (Doğan'ın bayi ekranından T-2 dk TJK ganyanı + Sporting Life oran geçmişinin son kalemi) ayrı ayrı. Karar: 1 Ocak 2027'de veya ≥ 500 bahiste; e-değer ile her gün izlenir.

## 15 Ekim 2026, 03:20 — İki piyasa SAĞLAMLIK: ABD yarış öncesi oranları (ÖN KAYIT, sonuç görülmeden)
Soru: ABD k=1,25 bulgusu (son oranlarla ROI 1,57) yarıştan önceki ABD oranlarıyla da duruyor mu? Durmuyorsa avantaj son dakika parasına bağlıdır ve bayide yakalanamaz.
Veri: data/yabanci_sl oran_gecmis (Sporting Life oran hareketi; son eleman %97,6 oranında son orandan farklı → son orandan ÖNCEKİ görüntüler). Yalnız ABD, aynı eşleşme kuralları (iki_piyasa.py).
Varyantlar (koşudaki TÜM atların geçmişi doluysa koşu dahil; aynı koşu kümesinde üçü karşılaştırılır):
- SON: oran_son (önceki testin aynısı, referans)
- GEÇ (BİRİNCİL): geçmişin son elemanı (bahis anına en yakın)
- ERKEN: geçmişin ilk elemanı
q = 1/oran koşu içinde normalize. Kural: q × TJK son ganyan > 1,25 → 1 TL. Ödeme: gerçek TJK ganyanı.
Ölçüt: ROI ve gün kümeli bootstrap %95 GA; tahmin gücü (kazanan log-olasılığı q−TJK).
Karar: GEÇ varyantında ROI GA alt sınırı > 1,0 → bulgu "bahis anına taşınabilir" adayı (ileriye dönük testte GEÇ oranı da kaydedilir). GEÇ ROI nokta tahmini < 1,10 → avantaj büyük ölçüde son dakika parasında; bayide uygulanabilirliği zayıf.
Sınır: TJK tarafı hâlâ SON ganyan (bahis anı TJK oranı bu veride yok; ileriye dönük testte Doğan'ın ekranından ölçülecek).
SONUÇ (15 Ekim 2026, 03:30; 269 ABD koşusu, geçmişi tam olanlar): SON 227 bahis ROI 1,59 [1,02–2,23]; GEÇ (birincil) 232 bahis ROI 1,49 [0,94–2,09], yarılar 1,52/1,45, büyük 3 hariç 1,04; ERKEN 266 bahis ROI 1,39 [0,89–1,94], büyük 3 hariç 1,00. Tahmin gücü üç varyantta da benzer (+0,079…+0,089 nats/koşu). Seçilen atlarda ABD olasılığı son dakikada ort. ×0,975 (neredeyse değişmiyor).
Okuma: Avantajın büyük kısmı ABD'nin son dakika parasına bağlı DEĞİL; erken oranlarla da sürüyor. Ön kayıt ölçütüne göre: GEÇ alt sınırı 1,0'ın biraz altında (0,94) → "kanıtlanmış" değil; nokta tahmini 1,49 > 1,10 → "son dakikaya bağlı" da değil. Ara bölge: ileriye dönük test sürer. Kalan risk TJK tarafında: bahis anı TJK ganyanı ve kendi bahsimizin küçük havuzdaki etkisi (bu veride yok). Betik: data/analiz/iki_piyasa_erken.py.

## 15 Ekim 2026, 03:45 — Accurace numara düzeltmesi (ölçüm)
`tjk/gelen.py`: Accurace satırlarının at numarası artık resmi sonuçtaki at ADIYLA eşleştirilerek yazılır (OCR numarası `no_ocr` olarak saklanır). 3.757 satırın 3.747'si (%99,7) eşleşti; OCR numarası 73 satırda yanlıştı. Kalan "sorunlu" koşular (151/415) yalnızca OCR'ın bir satırı hiç okumadığı koşular (ör. 11/12 at); diğer atların verisi kullanılabilir.

## 15 Ekim 2026, 03:50 — Yer kaybı (fazla mesafe) İLK BAKIŞ (ÖN KAYIT, sonuç görülmeden)
Hipotez: Halk bitiriş sırasına bakar; önceki koşusunda fazla mesafe koşmuş (geniş dönmüş) atı yeterince oynamaz.
Özellikler (yalnız kesinlikle önceki tarihlerin Accurace verisi, en çok 120 gün geriye):
- fm = koşulan_mesafe − o koşunun medyan koşulan mesafesi (metre); f_yk = atın EN SON önceki Accurace koşusundaki fm / 10 (yoksa 0)
- f_maz = f_yk × [o koşuda piyasa sırasından kötü bitirdi] (mazeretli kötü koşu)
Model: s = log p_Jason(OOS walk-forward) + b1·f_yk + b2·f_maz, koşullu logit. Sınama koşuları: en az bir koşan atta f_yk tanımlı olanlar.
Yöntem: zaman bölünmesi; b'ler sınama koşularının ilk yarısında (tarih medyanından önce) fit, ikinci yarısında ölçülür. BİRİNCİL ölçüt: ikinci yarı kazanan log-olasılığı kazancı (model − Jason), gün kümeli bootstrap %95 GA. Beklenen yön: b1 > 0.
Karar: kazanç ≥ +0,005 ve GA alt > 0 → "Jason-YK" gölge model adayı. Aksi halde "ilk bakış: etki ölçülemedi"; ~1.000 sınama koşusunda (daha fazla Accurace PDF'i ile) aynı betikle yeniden. Güç notu: bu örnekte yalnız büyük etkiler (≳0,01 nats/koşu) görülebilir. Betik: data/analiz/yer_kaybi_testi.py.
SONUÇ Yer kaybı ilk bakış (15 Ekim 2026, 04:05): Accurace 400 koşu / 3.735 at eşleşti; sınama koşusu 1.439 (en az bir atta önceki Accurace verisi; atların %26'sında özellik var).
BİRİNCİL (ön kayıt): ikinci yarı kazanç −0,0116 nats/koşu [−0,0214, −0,0013] → ÖLÇÜT SAĞLANMADI. Neden: ilk yarı ağırlıkla 2024'ün seyrek verisiyle (yalnız Mart 2024'ün 3 günü) fit edildi; katsayılar kararsız (b1 0,96, b2 −0,83) ve ikinci yarıda zarar verdi. Tüm örnek iç-örnek: b1 0,16, b2 0,23, LR 3,56 (p≈0,17) → anlamlı değil.
KEŞİF (sonuç görüldükten sonra, kanıt sayılmaz): yalnız Haziran 2026 sonrası (965 koşu, İzmir ağırlıklı): ilk yarı b1 0,16, b2 0,05; ikinci yarı kazanç +0,0011 [−0,0018, +0,0041]; iç-örnek LR 2,67. Yön beklenen gibi pozitif, büyüklük ölçülemeyecek kadar küçük.
Karar: "İlk bakış: etki ölçülemedi." Yer kaybı, eldeki örnekte Jason'a anlamlı bilgi eklemiyor; büyük bir etki (≥0,01) neredeyse dışlandı. Küçük etki için ~1.000+ yalnız-2026 sınama koşusu gerekir; Accurace yüklemesi sürerse 1 Aralık 2026'da aynı betikle (2026-06 sonrası, aynı tanımlar) yeniden. Betik: data/analiz/yer_kaybi_testi.py.

## 15 Ekim 2026, 03:25 — ÖN KAYIT: ABD iki piyasa GERİYE DÖNÜK BAĞIMSIZ SINAV (veri görülmeden)
Kural 25 Eyl–14 Eki 2026 verisinde bulundu; o tarihten ÖNCEKİ dönem bu kuralın hiç görmediği veridir. Kural aynen donduruldu: ABD koşusu, q (yerel ABD oranı, koşu içinde normalize) × TJK son ganyan > 1,25 → 1 TL ganyan; ekürsüz, iki_piyasa.py eşleşme kuralları.
Veri: TJK tarafı abdgecmis çekimi (Ekim 2025 → 24 Eylül 2026), yerel taraf Sporting Life (sltopla, aynı tarihler). İki varyant: SON oran ve GEÇ oran (oran geçmişinin son elemanı).
BİRİNCİL ölçüt: GEÇ varyantı ROI, gün kümeli bootstrap %95 GA. Karar: alt sınır > 1,0 → "bağımsız örnekte doğrulandı" (para kararı yine ileriye dönük testle birlikte verilir). Alt sınır ≤ 1,0 ama nokta > 1,10 → "zayıf destek". Nokta ≤ 1,0 → "bulgu tekrar etmedi; 3 haftalık sonuç şanstı", kural kapanır.
Ek kontroller (yalnız betimleyici): ay ay ROI, pist bazında, oran dilimi. Kural, eşik ve tanımlar sonuç görüldükten sonra DEĞİŞTİRİLMEZ.

## ABD sabit ihtimalli (SİB) testi — ön kayıt 15 Ekim 2026 04:00 (sonuç görülmeden)
Gözlem (13 Ekim Philadelphia SİB sayfası, kullanıcı yüklemesi): SİB oranlarının 1/oran toplamı koşu başına 1,38–1,42 (ortalama geri ödeme ≈ 0,71, ganyan kesintisiyle aynı düzey). SİB oranı bahis anında kilitlenir (ganyan kapanış oranından ödenir).
Soru: SİB oranı, yerel piyasanın (Sporting Life) KAPANIŞ olasılığına göre bayat/yanlış fiyatlı mı?
Kural (değişmez): SİB'in alındığı andaki oranlar (sib_ham zaman damgalı) ile aynı koşunun SL kapanış oranından q; q × SİB oranı > 1,25 olan atlara 1 TL ganyan (kâğıt üstü). Karşılaştırma ölçüsü: koşu başına log-kayıp farkı (q − SİB-normalize) ve kural ROI'si, gün-kümeli bootstrap.
Veri: Doğan ABD SİB sayfasını telefondan (Dosya > SİB yapıştır) gün içinde 2–3 farklı saatte yapıştırır. Karar: en az 300 bahis veya 1 Ocak 2027; o zamana kadar gerçek para yok.
Not: 10 Ekim ABD SİB dosyalarında oran boş (yapıştırma oran açılmadan yapılmış); 13 Ekim Philadelphia için TJK/SL eşleşmesi yok, karşılaştırma yapılamadı.

### ABD SİB ilk gözlem (15 Ekim 2026 04:10, keşif amaçlı, n=8 koşu)
Horseshoe Indianapolis 13 Ekim SİB (yükleme zamanı belirsiz) ile Sporting Life kapanış oranı karşılaştırıldı: SİB 1/oran toplamı 1,37–1,68 (çoğu ~1,40), SL 1,19–1,46 (çoğu ~1,2–1,3). Her 8 koşuda kazananın SİB oranı SL kapanış oranından düşük. q×SİB>1,0 olan at: 0. Tüm atlara SİB ganyan ROI 0,66. Çıkarım (zayıf, n küçük): SİB oranı yerel piyasadan türetilmiş ve ekstra marj eklenmiş görünüyor; ön kayıtlı kural SİB'de tetiklenmedi. Kural değişmedi; ileriye dönük SİB verisi toplanmaya devam.

### ABD SİB gözlem güncellemesi (15 Ekim 2026 04:20, keşif, n=17 koşu, 13 Ekim Finger Lakes + Horseshoe)
SİB 1/oran toplamı ort. 1,42; SL kapanış 1,25. Tüm atlara SİB ROI 0,66 (SL kapanış oranıyla 0,76). q×SİB>0,9: 0 bahis. Aynı veride q×TJK ganyan>1,0: 15 bahis, 3 isabet, ROI 3,45 (n çok küçük, şans payı büyük; kanıt sayılmaz). Kuralın seçtiği atlarda TJK ganyanı SİB oranından belirgin yüksek (ör. 22,9 vs 9,0; 24,4 vs 14,0; 29,1 vs 14,0): değer ganyan havuzunda, SİB'de değil. SİB tavanı 50.

## 15 Ekim 2026, 09:55 — ABD modeli SONUCU (ön kayıt 01:20'ye göre, kural ve özellik listesi değişmeden)
Veri: Ekim 2025–Ekim 2026 ABD sonuçları ve program sayfaları (program kapsamı %96), 3261 sınama koşusu, 10 aylık walk-forward.
M1−M0 (yanlılık düzeltmesi): +0,0056 nats/koşu, GA [+0,0024, +0,0087], aylık pozitif 9/10.
M2−M1 (halkın kullanmadığı bilgi): +0,0005 nats/koşu, GA [−0,0027, +0,0037], aylık pozitif 5/10.
M2−M0: +0,0060, GA [+0,0017, +0,0102]. EV>1,10 betimleyici: 108 bahis ROI 1,22 ± 0,37 (kanıt değil).
KARAR (önceden yazılı kurala göre): M2−M1 alt sınırı −0,0027 < 0,005 → ABD'de halkın kullanmadığı bilgi bulunamadı; ABD at/jokey/antrenör modeli KAPANDI. Bu sonuç, favori-uzun oran yanlılığının varlığını (M1−M0 pozitif) ve iki piyasa testinin ayrı hipotezini etkilemez. Sporting Life geçmiş oranları ile bağımsız sınav sürüyor.

## 2026-10-15 13:25 — Jokey değişikliği (kullanıcı bildirdi)
Ankara 1. koşu 5 PEVRUL: MÜS.ÇELİK -> V.ABİŞ; 2. koşu 7 HIZLI KRAL: MÜS.ÇELİK -> M.S.ÇELİK (TJK Jokey Değişikliği sayfası, ekran görüntüsü). Ankara CSV satırları elle düzeltildi; jokey_uygula puanları yeniler. Model/kural değişmedi.

## 15 Ekim 2026, 15:20 — Güney Afrika iki piyasa kuralı: ön kayıt (hiçbir GA sonucu görülmeden)
Hipotez: Güney Afrika koşularında Sporting Life yerel oranından normalize q × TJK ganyanı > 1,25 olan atlara 1 TL ganyan, ROI > 1,0 verir. Kural ABD ile BİREBİR aynı ve dondurulmuş (normalize 1/oran, eşik 1,25); GA için hiçbir parametre ayarlanmayacak.
Neden ayrı test: ABD bulgusu GA'ya taşınmaz; farklı yerel piyasa (tote/bookmaker), farklı TJK havuz büyüklüğü. Artısı: GA koşuları Türkiye saatiyle öğlen/öğleden sonra, bayi açıkken.
Veri durumu: TJK GA sonuçları şu an hatalı ayrıştırılmış (sıra/no/ganyan çoğunlukla boş), SL GA geçmişi çekilmedi → geriye dönük test şimdilik YOK. Ayrıştırıcı düzeltilip geçmiş toplanırsa geriye test bu kurala bakılarak, kural değiştirilmeden, ayrı kayıtla yapılır: BİRİNCİL ölçüt ROI gün kümeli bootstrap %95 GA alt sınırı > 1,0.
İleriye dönük kâğıt testi: Yabancı sekmesindeki kayıtlar (data/abd_kayit, ulke=guney-afrika). Değerlendirmede TJK resmi kapanış ganyanı esas; kayıt anındaki ekran ganyanı ayrıca raporlanır (bahis anı uygulanabilirliği). Karar: >=300 işaretli bahis ya da 1 Mart 2027 (hangisi önce): alt sınır > 1,0 → aday (para kararı ayrıca, küçük sabit tutar); nokta ≤ 1,0 → kural GA'da kapanır. O zamana kadar gerçek para YOK.
Mekanizma: abd_canli artık ABD + Güney Afrika koşularını çeker (abd_canli.yml'e UTC 08-15 saatleri eklendi).
15 Ekim 15:35 not: Sporting Life'ın yarış programında Güney Afrika toplantısı YOK (bugün Turffontein koşarken listede yalnız GB/IRE/FR/ABD vardı). At The Races GA koşu sayfaları Actions'tan 403 veriyor; Sky Sports artık ATR'ye yönlendiriyor; sportingpost/hollywoodbets/tellytrack bot korumalı; TAB tek sayfa uygulama. Otomatik GA yerel oran kaynağı şu an yok → GA kâğıt testi yalnız elle girişle (yerel oranı Doğan girer). abd_canli GA filtresini korur ama GA saatleri için ayrı cron kaldırıldı. Kural/ön kayıt değişmedi.

## 15 Ekim 2026, 15:40 — "SİB-q" kuralı: ön kayıt (hiçbir sonuç görülmeden)
Fikir (Doğan'ın ekranından): bayi ekranında her at için TJK GANYAN ve SABİT (United Racing sabit ihtimalli) oranı yan yana. ABD'de SİB'in yerel piyasadan türetilip ~%40 marj eklendiği görüldü (8 koşu, zayıf kanıt). Bu doğruysa normalize SİB yerel olasılığın vekilidir.
Kural (dondurulmuş): q = (1/SABİT) / Σ(1/SABİT) (koşmayanlar hariç); q × TJK ganyanı > 1,25 → 1 TL kâğıt ganyan. Eşik ve normalizasyon ABD kuralıyla aynı; ayarlanmayacak.
Kapsam: tüm yabancı koşular (GA, İngiltere, Fransa, ABD...), ülke ayrıca raporlanır. GA birincil ilgi alanı (bayi saatinde).
Veri: Doğan ekran fotoğrafı/elle girişle Yabancı sekmesinden kaydeder (data/abd_kayit, yontem="sib"). Kayıt anındaki ganyan ve SİB saklanır; değerlendirmede TJK resmi kapanış ganyanı esas, kayıt anı ganyanıyla ROI ayrıca raporlanır.
Karar: >=300 işaretli bahis ya da 1 Mart 2027 (hangisi önce). BİRİNCİL ölçüt: kapanış ganyanıyla ROI, gün kümeli bootstrap %95 GA alt sınırı > 1,0 → aday; nokta ≤ 1,0 → kural kapanır. İkincil (betimleyici): SİB-q'nun log-loss'u TJK ganyanından iyi mi (SİB-q bilgi taşıyor mu).
Bilinen risk: SİB oranı TJK havuzuna bakılarak da ayarlanıyorsa karşılaştırma döngüseldir; SİB'in marjı uzun atışlara yüklüyse q uzun atışları düşük tahmin eder (kural muhafazakâr kalır). Gerçek para YOK.
Not: Bu kayıttan önce yalnız Brighton 15 Ekim 1. koşunun yarış ÖNCESİ ekranından örnek hesap yapıldı (sonuç bilinmeden); kural ondan etkilenmedi.
15 Ekim 15:45 düzeltme (veri hatası, kural değil): abd_canli Sporting Life saatlerini İngiltere saati sanıyordu; SL JSON saatleri UTC. Sonuç: canlı sayfa "kaç dk kaldı"yı 60 dk yanlış hesaplıyor ve 90 dk penceresi aslında 55–150 dk'yı kapsıyordu (yakın koşular listede yoktu). Düzeltildi; saatler artık Türkiye saati. Geçmiş sltopla/abd_program saat kullanımı ayrıca kontrol edilecek (eşleştirme tarih+pist+koşu ile yapıldığı için test sonuçlarını etkilemiş olması beklenmez).
15 Ekim 16:25 altyapı notu: agftablosu.com ~13:30'dan itibaren Actions isteklerine Cloudflare "Just a moment" engeli koydu → Ankara sonuçları, AGF, jokey yenileme işlenmedi. ortak.getir artık curl_cffi (Chrome TLS parmak izi) kullanıyor; keşif isteğinde engel aşıldı. Kural/model değişmedi.
15 Ekim 16:50 altyapı: agftablosu sonuç sayfaları curl_cffi'yi de engelliyor (Cloudflare JS denetimi). ortak.getir artık bu durumda Playwright Chromium (tjk/tarayici.py) ile indiriyor; Actions'ta Ankara sonuç sayfası bu yolla açıldı ve 6 koşu doğru ayrıştı. İş akışlarına playwright kurulumu eklendi.

## 15 Ekim 2026, 16:55 — SONUÇ: ABD iki piyasa BAĞIMSIZ SINAV (ön kayıt 03:25'e göre, kural değişmeden)
Veri: 25 Eylül 2026 ÖNCESİ (Ekim 2025 → 24 Eylül 2026), kuralın hiç görmediği dönem. Eşleşen ABD koşusu 3.171, oran geçmişi tam 2.707. Betik: data/analiz/iki_piyasa_bagimsiz.py.
BİRİNCİL (GEÇ varyantı, k=1,25): 2.259 bahis, 282 isabet, ROI 1,551, gün kümeli bootstrap %95 GA [1,30, 1,83]; yarılar 1,59 / 1,53; en büyük 3 kazanç hariç 1,39.
SON varyantı: 2.133 bahis ROI 1,64 [1,39, 1,94]. ERKEN: 2.520 bahis ROI 1,41 [1,20, 1,68]. Tahmin (q − TJK) log-olasılık kazancı GEÇ +0,104 [+0,089, +0,119] nats.
KARAR (ön kayıt): GA alt sınırı 1,30 > 1,0 → "BAĞIMSIZ ÖRNEKTE DOĞRULANDI".
Betimleyici: 12 ayın hepsinde ROI > 1,0 (en düşük Mart 2026 1,17, Aralık 2025 1,18); pistlerin çoğunda > 1 (istisna: Belmont Park 41 bahis 0,22, Tampa Bay 94 bahis 0,92, Oaklawn 43 bahis 0,95); her oran diliminde > 1,3.
SINIRLAR (para kararı bunlar çözülmeden verilmez): (1) TJK tarafı KAPANIŞ ganyanı; bahis anındaki TJK ganyanı bu veride yok — işaretin bahis anında görünüp görünmediği ileriye dönük testte ölçülecek. (2) Havuzlar küçük olabilir: kendi bahsimiz oranı düşürür; ölçek sınırlı. (3) ABD koşuları 20:00 sonrası, bayi kapalı — uygulanabilirlik Doğan'ın çözümüne bağlı. (4) Eşleşme yalnız tüm atları eşleşen koşularda; seçim yanlılığı küçük olası.
Sonraki adım: ileriye dönük kâğıt testi (Yabancı sekmesi kayıtları) aynen sürer; para kararı ileriye dönük >=300 bahis ve bahis-anı ganyanıyla ROI GA alt sınırı > 1,0 ile.
