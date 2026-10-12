# Yapilacaklar (Dogan + Claude), 10 Ekim 2026 aksami

Siralama:
1. **Bugunun kapanisi:** Izmir K8 resmi odeme (siralı 5'li 8/5/13/10/9: bilen var mi? devir 276.534 TL), Ankara 2. altili sonucu, gunluk P&L ve ders ozeti.
2. **B - Havuz tutarlari:** devirli siralı 5'li ve altili/7'li havuzlarda TOPLAM SATIS + devir tutarini toplamaya basla (ekranda havuz toplami gorunen her fotoyu kaydet). Amac: EV ≈ 0,70 + devir/satis kuralini gercek veriyle dogrulamak, esik belirlemek.
3. **Jason'u gelistir (en umut verici yon):** walk-forward'da her ceyrekte Bolton'dan iyi (+0,0152 vs +0,0111 nat/kosu). Fikirler: idman/kron/plase/zengin verisinden yeni ozellikler, lam ayari, hipodrom/mesafe etkilesimleri; HER yeni ozellik walk-forward + dondurulmus holdout'ta sinanir (cok test = sans oyunu riski).
4. **EV>1,1 bolgesi izleme:** Jason kagit ustu bahisler (n=306'da +%17 ±19); birkac bin bahse kadar para yok.
5. **Walk-forward'u gunluk calistir:** tjk/walkforward.py CI'ya eklensin, sonuc docs'ta gorunsun.
6. **Ucluyu birim duzeltmesiyle yeniden degerlendir** (2025 birim 1 TL, 2026 birim 2 TL); tabela 1,50, besli 1,25.
7. **Chapman:** adi bos. Ancak kalabalik/havuz carpikligi modelinde gercek (birim duzeltmeli) sinyal cikarsa verilir.
8. **SIB gecikme hipotezi:** otomatik snapshot (sib_snap) ile yuzlerce kosuda "T-10 SIB vs final muhtemel" olcumu.
Kural: once olc, sonra para; yuzlerce bahis + dondurulmus holdout olmadan edge iddiasi yok.

## Deney kayitlari (walk-forward, Jason baz = +0,0177 nat/kosu, 2025Q3-2026Q4)
- zengin boy farki ozellikleri: fark -0,00005 ± 0,0005 (katki yok)
- ekipman kodlari + degisimleri: fark -0,0027 ± 0,0008 (ZARAR, asiri uyum)
- lam taramasi (2025Q1+): 10:0,01725 30:0,01723 100:0,01709 300:0,01664 1000:0,01534 -> lam=100 yeterli, ayar kazanci yok (<0,0002)
- (21:30) antrenor/sahip/baba/jokey-antrenor/jokey-hipodrom artik ozellikleri: +0,0001..+0,00015 (SE 0,0001-0,0002) -> anlamsiz. hipodrom/alan buyuklugu/mesafe/apranti x piyasa etkilesimleri: +0,00013 ± 0,00024 -> anlamsiz. Hepsi birlikte +0,00022 ± 0,00032. SONUC: eldeki veriyle Jason tavana yakin; yeni BILGI kaynagi (idman gecmisi) gerek.
- walk-forward artik gece job'unda (tjk/calistir.py gece) calisir, docs/data/walkforward.json uretir.
- tjk/havuz_canli.py: devirli havuz kaydi + EV tablosu (python -m tjk.havuz_canli ev 276534). 276.534 TL devirde medyan satisla EV~1,5, %25-%75 araligi 1,2-1,9, %90 1,08.
- (21:50) jokey-at uyumu: cift artigi +0,0002 ± 0,0002; jokey degisimi 0,0000; jokey yukselisi +0,00001; birlikte kosu sayisi -0,00014 ± 0,00007; hepsi +0,00009 ± 0,0003 -> anlamsiz.
- (22:30) Yapisal havuz: model-secimli siralı ikili/ikili/uclu kombinasyonlar ~basa bas (0,94-1,14, CI 1'i iceriyor), rastgele tabana (~0,75) gore +20-25 puan. Edge kaniti yok; ileriye donuk kagit test tjk/egzotik.py'de. Sonraki: kagit testin gunluk sonucunu izle, birim rejimi (uclu 2025 vs 2026) ayri analiz.
- (23:00) Ikinci/ucuncu sira hedefi (walk-forward, 11.963 kosu): ozellikler 2. sirada +0,0269, 3. sirada +0,0397 nat/kosu katki (kazanma hedefinde +0,011); ogrenilen ussel agirlik 0,69 (2.) ve 0,50 (3.) vs sabit Harville 0,87/0,735. Ilk uc icin ayri hedef gerekli.
- (23:00) Mesafe/pist/gun varyanti duzeltmeli gercek hiz puani (sp1,sp3,spmax5,spsd5,spn): kazanma -0,0002±0,0004, 2. sira +0,0001±0,0006, 3. sira -0,0003±0,0004 -> katki yok.
- (23:00) Esik taramasi (ilk yari sec / ikinci yari sina): ayar secimi tasinmiyor (uclu korelasyon -0,35); kural degismiyor, kagit test devam.
- Kosu seyri/anlatim: tjk.org'da komiser raporu var (cikan at, jokey/antrenor/seyis degisikligi, ek rapor), at bazli seyir yok; haber sitelerinde sadece sonuc ozetleri.
- (23:25) DUZELTME: ilk uc icin 'ozellik katkisi' +0,0269/+0,0397 yanlis hesaplanmisti (ozellikli modelin w0'i ozelliksiz kullanildi). Dogru: piyasa-tek (w0 yeniden ogrenilmis) ustune ozellikler 2. sirada +0,0158 ± 0,0017, 3. sirada +0,0222 ± 0,0020 (kazanma +0,0073 ± 0,0015). Gruplar (2./3.): gecmis_sonuc +0,0115/+0,0129, dinlenme +0,0035/+0,0078 (kazanmada 0), kilo_yas_hnd +0,0012/+0,0024, start +0,0004/+0,0016, jokey ~0, tur_mesafe ~0, t2_t3 ~0.
- (23:25) Video seyir: tjk/video_seyir.py (yayin seridinden at bazinda sira zaman serisi). Ankara 5. kosu ornegi dogrulandi (kazanan/ikinci uyumlu, 5 numara onde gidip coktu, 7 oncu yorulup 4. oldu, 8 kapanisci). Video elle indirilip yuklenir; otomatik indirme yok.

## 11 Ekim 2026 (gece) - ikramiye ve egzotik uzman
- Uzman ilk-3 modeli (2./3. aşama modelleri + dinlenme/istikrar) vs mevcut Harville kuralı: olasılık +0,026 nat/koşu (üçlü), ama seçilen kombinasyon geri dönüşü iyileşmedi (0,79 vs 0,80; sıralı ikili 0,90 vs 0,99). Kâğıt testini bölmedik; kural donuk.
- Birinci ikramiye (tjk_sonuc, 2025-01-01'den, 4.526 koşu): favori güvenilirliği hafif artıyor ama piyasa fiyatlıyor. Kazanan modele ikramiye özelliği (düzey x piyasa payı, at bazlı sınıf değişimi) walk-forward: -0,0002..-0,0005 nat/koşu, katkı yok.
- Egzotik kağıt testi artık ikramiye üçte birlerine göre de izleniyor (düşük <395 bin, orta, yüksek >545 bin). Yalnızca izleme; kural/eşik değişmez. 2026'da yüksek ikramiyede işaret olumlu (üçlü 1,33), 2025'te tutmadı: 300 koşu dolunca bak.
- Accurace: PDF'ler ganyan masasından yükleniyor (tarayıcıda resme çevrilir, data/accurace_ham -> data/accurace). Numara OCR düzeltmesi (bitiş sırasından doldurma) yapılacak. Hedef: İstanbul son ~45 yarış günü (~400 koşu), önce son 10 gün.
- Video: Release ile yükleme (etiket "gelen..."), tjk.gelen işler. Ankara 1-4,6-10 yeniden çalıştırılacak (koşan at numaraları temiz/kosu_at'tan).
- Jokey ve ilk-3 (walk-forward, ~12 bin yarış): jokey özellikleri çıkarılınca 1./2./3. sıra -0,0003/-0,0006/-0,0022 nat/yarış (3. sıra için jokey daha önemli); jokeyin son 150 ata ilk-3 oranı eklenince +0,0022/+0,0014/+0,0019. Küçük ama güvenilir; Chapman adayı uzman modelin parçası olabilir, tek başına değil.
- Özellik budama (ilk-3, seçim 2024Q2-2025Q4, sınav 2026): 2. sıra 34->13 özellik -0,0071±0,0017 (kötü), 3. sıra 34->22 +0,0004±0,0004 (fark yok). Budama yarar sağlamıyor; kazanç yeni bilgiden (Accurace) beklenmeli.

## 2026-10-11 Benter karşılaştırması (Δρ²)
- Walk-forward (14.636 koşu, 2024Q2–2026Q3): Bolton +0,0111 nat/koşu, Jason +0,0152 nat/koşu (piyasaya göre).
- Δρ² = kazanç / ort. ln(N) (N≈9,5 at, ln N≈2,206): Bolton 0,0050, Jason 0,0069. Benter (Hong Kong) 0,0178 → "anlamlı kâr potansiyeli". Bizim kesinti %27, onunki %17–19.
- Kelly: çeyrek Kelly, tavan kasanın %2'si; Oynadıklarım'dan kasa girilir (localStorage gm2_kasa).

## 2026-10-11 Hız figürü deneyi (tjk/deney_hiz.py)
- Jason'da zaten f_fig3 (gün/pist varyantına göre düzeltilmiş göreli süre, son 3) ve f_dp150_m (mesafe uyumu) var.
- Eklenen: mutlak figür (derece / (hip, mesafe, pist) ölçütü), son koşu, son 5 ort., son 5 en iyi. Kapsam %59.
- Sonuç (2025Q3–2026Q4, 8.115 koşu): fark −0,00004 ± 0,0003 nat/koşu → ek bilgi yok. Yapılmaz.

## 2026-10-11 gece - video (Adana + İstanbul, 18 koşu)
- Yayın şeridi yalnızca ilk 10 sırayı gösterir. tjk/video_seyir.py artık kutu=min(at,10) ile çalışır, ama 11+ atlı koşularda palet yalnızca ilk 10 numaranın rengini öğrenir; 11+ atların renkleri bilinmediği için sıralama bozuluyor. Gözlenen: 11 = koyu yeşil, 13 = açık ten rengi; 12, 14-17 bilinmiyor. Çözüm: sabit TJK paleti (1-17) + dikdörtgen eşleştirme (kutu x numara), kutudaki rakam OCR ile doğrulama.
- Son geçerli kare her zaman bitiş değil (video sonunda şerit kayboluyor); doğrulama ρ (data/video_seyir/*.json: dogrulama_rho, guvenilir) ancak ≤10 atlı koşularda anlamlı. 11 Ekim: 18 videodan 8'i güvenilir sayıldı.
- İstanbul 9 (Çelik Abi 13): 1193 m kala şeritte yok (ilk 10 dışı), 721 m kala 10., 355 m kala 7., 2. bitirdi = geriden kapanış.
- (00:45) Video paleti 11-14,16 eklendi: güvenilir koşu 6/18 -> 11/18 (ρ≥0,7, son geçerli kare vs gerçek sıra). Hâlâ sorunlu: 13 atlı Adana 1, 6, 9 ve İstanbul 9 (ρ<0,6); 10 atlı İstanbul 4; ayrıca İstanbul 2 ve 7. 15 ve 17 rengi bilinmiyor. Olası neden: koyu renkler (5 siyah, 8 kahve, 11 koyu yeşil) karışıyor; kutudaki rakamı OCR ile doğrulamak gerekir.

## 2026-10-12 Uzman (aşamalı) model testi - tjk/deney_uzman.py
- Eğitim <= 2025-12-31, sınav 2026 (≈4.800 koşu). Her aşama (1..5. sıra) için ayrı koşullu logit; Jason özellikleriyle. Taban: piyasa lp'sinin Harville üstelleri.
- Aşama başına koşullu log-olasılık kazancı (nat/koşu, piyasa tabanına göre): Jason+üstel 2./3./4./5.: 0,0178/0,0172/0,0123/0,0073; Uzman: 0,0236/0,0346/0,0342/0,0310. Uzman-Jason: +0,0058 (SE 0,0017) / +0,0174 (0,0025) / +0,0219 (0,0034) / +0,0237 (0,0037). 4. ve 5. aşamada w0 negatif: piyasa fiyatı geride bitişler için neredeyse bilgisiz.
- Küme seçimi (1.500 koşu, örnekleme): ilk 2/3/5 ortalama isabet Piyasa 0,922/1,678/3,492; Jason 0,935/1,689/3,511; Uzman 0,933/1,677/3,507 -> fark yok.
- Egzotik geri dönüş (3.807 koşu, kural: model/piyasa kombinasyon olasılığı >= 1,15 ve piyasa olasılığı >= donuk eşik; tutar = ödeme CSV'si): sıralı ikili Jason 0,963 / Uzman 0,983; ikili 0,975 / 0,973; üçlü 0,950 / 0,908. Hepsi 1,00 altında, fark gürültü içinde (ağır kuyruklu ödemeler).
- Sonuç: olasılık tahmini iyileşiyor, bahis getirisi iyileşmiyor. Gölge model olarak canlıya bağlanmadı. Sonraki adım: yeni bilgi (video kapanış gücü, Accurace) aşama modellerine eklenip aynı testle ölçülmeli.

## 2026-10-12 Genişletilmiş sırasız küme testi (tjk/deney_uzman.py: genis_deney)
- Kural (sitedeki gibi): ilk 2 temel 2 at + ek (≥%20, en çok 5); ilk 3 temel 3 + ek (≥%25, en çok 5); ilk 5 temel 5 + ek (≥%35, en çok 7). 2025 sonu eğitim, 2026'dan 2.000 koşu, 300 örnek/koşu. Ölçüler: kapsama (gerçek ilk-K tamamen küme içinde), ortalama kombinasyon, ikili (tüm çiftler) ve üçlü (tüm sıralamalar) geri dönüşü. Sonuç: data/analiz/deney_uzman_genis.json.

## Eşik taraması (12 Eki 2026)
- İkili/üçlü: ilk2 %30/4 at, ilk3 %50/4 at canlıya alındı (`data/analiz/esik_tarama.csv`).
- İlk 5: sırasız ödeme türü yok, sadece kapsama bakıldı; %35/7 kaldı.
- Tabela sırasız (ilk 4), 678 koşu: geri dönüş 0,27–0,49 (her eşikte düşük; maliyet varsayımı kombinasyon başı 1 birim). Jason piyasadan iyi değil. Canlıya eklenmedi (`esik_tarama_tabela.csv`).

## Değer seçimi (kombinasyon bazlı, 12 Eki 2026)
- Kural: Jason'ın kombinasyon olasılığı / piyasa (PL) olasılığı ≥ r olanları oyna; set büyüdükçe otomatik sıkılaşır. `data/analiz/deger_secimi.csv`
- 2026 tüm koşular: tüm kombinasyonlar ROI ~0,60; r≥1,25: ikili 0,94 / üçlü 1,00; r≥1,5: ikili 1,06 / üçlü 1,13 (yaklaşık 70–90 isabet; %90 güven aralığı 1'i kapsıyor).
- Yapılacak: canlıda gölge olarak (para yatırmadan) izle, 500+ isabet birikince karar ver; piyasa PL olasılığı havuz olasılığı değil, gerçek ödeme oranıyla karşılaştırılabilir.
