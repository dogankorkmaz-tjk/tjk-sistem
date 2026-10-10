# 10 Ekim 2026 analiz notlari (Dogan + Claude)

## 1. Ganyan piyasa kalibrasyonu (2023-2026, 18.031 kosu, final muhtemel)
- Favori ve orta oranlarda piyasa kalibre; ROI ~ -%25..-%29 (kesinti). Hicbir oran araligi pozitif degil.
- 25+ oranli atlar fazla oynaniyor: ROI -%53..-%61.
- Basa bas: model olasiligi / piyasa olasiligi >= ~1,37.

## 2. Sirali 5'li devir
- 1.572 kosu, %11 devir. Ilk devir medyani 242 bin TL (~net havuz). Devir sonrasi odeme medyani 41 bin vs 21 bin.
- Rastgele alici EV ~ 0,70 + devir/satis. Satis verisi yok; 5'li havuz tutari ekrandan toplanmali.

## 3. Havuz turu bazinda "tum kombinasyonlari al" ROI (odeme/kombinasyon sayisi - 1)
Ganyan -40%, ikili -40%, sirali ikili -38%, tabela -54%, tabela sirasiz -68%, sirali 5'li -67% (devirsiz).
Uclu -7% (SE 4,4) AMA: 2025 -45%, 2026 +21%; ust %1 odeme cikarilinca -22%; 110 bin ve 59 bin TL'lik iki odeme surukluyor. Edge degil, varyans.

## Acik
- Bolton/Jason walk-forward testi (yil yil egit/test) yapilmadi. Canli skor yalniz 18 kosu.

## 4. Kalabalik (havuz carpikligi) testi: odeme x Harville olasiligi (q*D, 1 = kesintisiz adil)
- Siralı ikili: 2025-2026 boyunca sabit, ortalama ~0,75 (= 1-kesinti), medyan ~0,70. Uzun sans kombinasyonlari kotu (-%73), orta/yuksek -%21..-%26. Edge yok.
- Ucuncu: 2025 (Oca-May) medyan 0,70-0,75; 2026 (Oca-Eki) medyan 1,13-1,49, ortalama 1,3-1,7. Resmi TJK CSV'lerinde (Agu-Eki 2026, 367 kosu, bagimsiz kaynak) medyan 1,40, ortalama 1,52 -> scraping hatasi degil.
- 2026'da orta olasilikli ucluleri (q 3e-3..1e-1) "hepsini al" ROI +%31, bootstrap CI95 [+23, +39], ilk 3 odeme cikarilinca ayni. Hit ratio ~1 (q kalibre).
- Fark ~x1,9-2: SUPHE = 2026'da ucluye birim bahis 0,50 TL'ye indi ama odeme 1 TL icin yaziliyor olabilir (siralı ikilide yok). DOGRULANMADI. Dogrulama: makinede 1 uclu kombinasyon kac TL, odeme tablosundaki tutar kac TL'lik bahis icin?
- Dogrulanirsa edge degil, birim artefakti. Dogrulanmazsa (birim 1 TL) -> "Chapman" adayi: uclu havuzunda kalabalik modeli.
