# 3. madde — Benter seviyesine yapı: durum ve önerilen test (taslak, onay bekliyor)

## Zaten yapılmış olanlar (tekrar edilmeyecek)
- **Sıraya özgü üsler (Henery/Stern tipi):** 14 Ekim'de yapıldı. Üretimdeki Benter, `a_g1`/`gam` üslerini kazanan ve ilk-5 sırası üzerinden ortak eğitiyor (`g1v3._steps`).
- **Ortak eğitim (sıralı olasılıklar özelliklerle birlikte):** v3 tüm 5 adımda birlikte eğitiliyor.
- **Benter'in iki aşamalı birleşimi (α·log p_piyasa + Xb):** 2. aşama; birleşik kazanç +0,0098 nat (galoplu +0,0118).
- **Daha önce denenmiş API alanları:**
  - Ekipman (T29)
  - Hız figürü (T144)
  - Soy/yaş (T146 → T152-S)
  - Kapı, tempo/stil (T114–T125)
  - delayedExit (T151)
  - Handikap puanı: modelde `f_hnd`.
- **Hiç kullanılmamış alanlar:** `last20` (son 20 koşu puanı), `weightLoss` (apranti indirimi; `f_apr` ile kısmen var), `foal` (doğduğu ülke), `fotoFinish`, `prizes` (ikramiye ve sınıf; `sinif_tablo.py` betimsel).
  - Bunlardan beklenti düşük: çoğu, var olan özelliklerin (form, sınıf, apranti) türevi.

## Asıl yapısal boşluk: sıraya özgü katsayılar
Şu an 2.–5. sıranın seçimi kazananla **aynı** puanı kullanıyor (yalnız üs farklı). Benter 1994 ve Lo–Bacon-Shone'un gözlemine göre bazı atlar "plase atı": kazanmaktan çok 2–3. olurlar. Örnek: kapanışçılar, istikrarlı ama hızı sınırlı atlar. Bu durumda:
- Kazanan puanı ile "ilk-5'e girme" puanı farklı özellik ağırlıkları ister.
- Sıralı ikili, üçlü, tabela ve 5'li doğrudan bu olasılıklara dayanır.
- MJT9'un piyasalıda kazananı değil ilk4/ilk5'i iyileştirmesi (−0,0070) bu boşluğa işaret ediyor.

## Önerilen ön kayıt T154 (onaylanırsa deftere aynen yazılır)
- **Model:** taban MJ (üretim Benter). MJP = MJ + adım 2–5 için ayrı katsayı vektörü δ. Adım j≥2'de puan s_j = γ_j·(s + X·δ). δ yalnız şu küçük kümede, ridge ile 0'a çekilir:
  - stil/öncülük
  - istikrar (son 6'da ilk-3 oranı)
  - f_st
  - kilo farkı
  - handikap farkı
  - yaş
- **Ölçü:** piyasalı ve piyasasız, yürüyen aylık 2025-10..2026-10 (T152 çerçevesi; sızıntı kontrolü: sahip/antrenör kullanılmaz).
- **Birincil (2 karşılaştırma → %97,5 güven aralığı, gün-küme bootstrap):** MJP − MJ, **ilk5 Plackett-Luce kaybı** (sıralı bahislerin ölçüsü).
- **Koruma:** kazanan kaybı kötüleşmemeli (GA alt sınırı < +0,0005).
- **Karar:**
  - Piyasalıda ilk5 GA üst sınırı < 0 ve koruma sağlanırsa → ana model adayı. Üretime ancak 2026-11 → 2027-01 ileri pencere doğrulamasıyla girer.
  - Piyasasızda aynı kural → aşama-1 adayı.
- **Betimsel:** ikili, üçlü, ilk4; aylara göre işaret; δ katsayıları.
- **Süre:** harness iki koşum (NOLP 0/1), arka planda yaklaşık 10 dk.

## Neden bu, neden şimdi
Yeni özellik avı doygunluğa yaklaştı: son 10 testin çoğu "etkisiz" ya da "küçük". Sıralı bahisler ana modelin işi ve ROI'nin geleceği yer. Bu test yeni veri değil, mevcut bilginin sıralara doğru dağıtılmasını sınıyor.
