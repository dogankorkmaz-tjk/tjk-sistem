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
