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
