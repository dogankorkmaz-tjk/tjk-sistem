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
