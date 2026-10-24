# İlk 5 için veri/fikir havuzu (2026-10-24)
Amaç: sıralı 5'li / tabela / üçlü için 2.–5. sıra tahminini iyileştirmek. Tüm testler önceden kayıtlı, güç sınırlı (≈0.074 nat SD/koşu).

## Literatür özeti
- Harville 2.–3. sırayı favori lehine abartır (Ali 1998; Lo & Bacon-Shone: Henery/Stern daha iyi). Bizde gam üsleri bunu zaten kısmen çözüyor.
- Egzotik havuzlar kazanan havuzundan daha verimsiz (Benter, Ali) → asıl fırsat tabela/üçlü/5'li tarafında.
- Benter: model + piyasa ikinci aşama birleşimi (bizde var).

## Öncelik sırası
1. Piyasa-ima edilen 2./3. olasılıklar: TJK ikili/sıralı ikili/üçlü muhtemel havuzları (run JSON `bahisler` alanı probe edilmeli). Piyasanın kendi sıralama bilgisi; Harville varsayımını ölçüp düzeltir. Maliyet düşük, potansiyel yüksek.
2. Bitiş hızı f_k (Accurace): 1 Aralık 2026 bağımsız yeniden test; özellikle 2.–5. sıra için (kazananı değil, kapanışı iyi olanı yakalar).
3. Yer kaybı / engellenme (fazla mesafe): sonraki koşuda düzeltme; dar örnek.
4. Tempo/koşu stili x saha tempo senaryosu (önde giden sayısı) → kapanışçıların 2–5. sıra payı.
5. Henery/Stern tipi sıra-bağımlı kalibrasyon: 2.–5. sıra için ayrı üs, isotonic; sıralı ölçüt (top-5 log-lik) ile.
6. Öğrenerek sıralama (LambdaMART/XGBoost rank, NDCG@5) — mevcut z6b üstüne artık olarak; aşırı uyum riski yüksek, ancak ≥300 koşuda.
7. Geç para hareketi (anlık muhtemel/AGF değişimi) — canlı mod verisi birikince CLV ile.
8. Sınıf/kilo/handikap değişimi, ekipman, jokey-antrenör kombinasyonları (çoğu zaten deneyde; ilk5 metriğiyle yeniden bakılabilir).

## Test disiplini
Önceden kaydet, tek hipotez, ilk-5 log-lik + tabela ROI, piyasa referansı; ≥300 koşu birikmeden karar yok.
