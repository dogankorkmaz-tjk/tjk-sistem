# DEVİR NOTU — 6 Kasım 2026 (yeni oturum için)

Bu not, T131–T149 oturumunun sonunda yazıldı. Tek doğruluk kaynağı hâlâ `data/analiz/hipotez_defteri.md`; bu not onun özeti ve kullanım kılavuzudur. **Önce defteri grep'le, sonra konuş/öner.**

## 1. Proje
"Ganyan Masası" (docs/index.html, GitHub Pages; repo dogankorkmaz-tjk/tjk-sistem). Dürüst, ön kayıtlı, kâğıt üstü TJK model testi. Kullanıcı Doğan Korkmaz; bayiden yarışa dakikalar kala oynuyor.
- **Benter** = ana model (iç adı G1-S v3, z6/pg, g1s_katsayi; 24 Ekim'den beri canlı). Konuşmada "Benter" de, "G1-S" deme.
- **Jason** = ganyan/sürpriz modeli (Koşu sekmesi ana satır). **Bolton** = 8 Ekim'de dondurulmuş referans.

## 2. Ana hedef (kullanıcı tanımı, 6 Kasım 03:04)
İki aşama: (1) Benter'in **piyasasız** modelinden daha iyi bir piyasasız model; (2) sonra piyasa bilgisiyle birleşik ana model. Hedef "piyasasız modelle piyasayı geçmek" DEĞİL (bunu yanlış yorumlamıştım).
- Aşama 1 ölçüsü Ρ = (eşit − model)/(eşit − piyasa), aynı yürüyen testte. T49 tam PM0: 0,82–0,83; T138 Jason-yalnız Z: 0,80. Benter 1994 referansı belirsiz: 0,82 (9 faktörlü örnek-dışı model, ULAŞILDI) / 1,02 (tam model, örnek türü belirtilmemiş, AÇIK).
- Aşama 2 ölçüsü: birleşik kazanç (Jason−kalibre piyasa pseudo-R² 0,0072; Benter 0,0178 [örnek belirsiz], 0,0090 [9 faktör OOS]).

## 3. Kalıcı kurallar
- Kısa Türkçe cevap. Dürüst itiraz. Öncelik sıralı bahisler. Opus yalnız gerçekten gerekirse öner.
- Her şeyi commit+push (mesaj sonu: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` ve `Claude-Session: https://claude.ai/code/session_012KA2VqUhYCRKxUNauMWuYE`; `git pull --rebase` serbest; push'u jitter'lı döngüyle tekrarla). Stop hook işlenmemiş değişiklik/itilmemiş commit isterse yap.
- Her fikir deftere karar kuralıyla ÖNCEDEN yazılır, sonra test edilir. Önerme/iddiadan önce defteri grep'le.
- Uzun testler arka planda (nohup setsid), ön planda bloklama.
- ROI başlığı büyük ödemeleri DAHİL eder + GA (en büyük ödemesiz ROI yalnız bilgi).
- Üretim Jason/Benter deneylerle DEĞİŞMEZ; testler üretime yazmaz.
- Padok/canlı yayın eski videosu (16 Ağustos) kaydedilmez.
- Konuyla ilgili işe yarayabilecek HER veri için uyanık ol; kullanıcıdan iste ya da kendin bul ve söyle.
- Yorumcu notlarında "/" = isteğe bağlı, sondaki "-" yok sayılır. Bankomat 6 Kasım'dan itibaren SIRALI veriyor (geçmiş 2/4/5 Kasım notları sirali=false kalır; ilk yeni notta geçiş gününü doğrula).

## 4. Test sonuçları (T131–T149; tümü yürüyen aylık, test 2025-10..2026-10 = 6.587 koşu / 386 gün; kazanan log-olasılığı; gün-küme bootstrap %95 GA)
Yorum kuralı: piyasasızda (Z) kazanç var, piyasalıda (J) yok → "özellik gerçek ama piyasa biliyor" (piyasa verisi yokken değerli); ikisinde de var → bilgi adayı (ileri doğrulama şart); ikisinde de yok → kapalı.
| Test | Konu | Sonuç |
|---|---|---|
| T131 | T126 koşu uyumu ileri doğrulama | bekliyor (değerlendirme 31 Ocak 2027 veya ≥1500 koşu) |
| T132–T134 | katsayıların mesafe/pistle değişmesi; Jason etkileşimleri | ayırt edilemedi/aday değil |
| T135/T136 | egzotik havuz verimlilik atlası (sıralı ikili, ikili, üçlü) | takeout üstü sınıf yok; sıralı 5'li birim belirsiz→karar yok; altılı/3-4-5'li atlası YAPILMADI (ayrı ön kayıt) |
| T137 | yorumcu bilgi taşıyor mu | veri büyüyor, n(A)=36; karar yalnız n(A)≥300'de |
| T138 | Z vs piyasa | Z−P −0,0855; J−Pk +0,0161 [+0,0126;+0,0194]; J−Z +0,1051 |
| T139 | mesafe/pist etkileşim, göreli kilo×uzun | ZB−Z −0,0015; ZK−Z +0,0002 → kapalı |
| T140 | ablasyon | form 0,030, kilo 0,029, jokey 0,023, renk/cinsiyet 0,018 benzersiz; hız 0,006 (örtüşüyor) |
| T141 | LightGBM piyasasız | G−Z +0,0055 [+0,0008;+0,0104] küçük; G−P −0,080; GBM'li birleşik Jason'dan KÖTÜ → kapalı |
| T142 | video özet olayları | JV−J +0,00095, ZV−Z +0,00157 → ADAY (zayıf) |
| T144 | hız puanı derinleştirme | ZH−Z +0,00054 ayırt edilemedi → kapalı |
| T145 | segment haritası (betimsel) | Ρ Ankara 0,68, Bursa 0,92; ilk-koşucu yoğun ve genç at koşularında açık büyük |
| T146 | soy/yetiştirici/sahip/yaş | ZS−Z +0,0021 [+0,0002;+0,0041] ADAY; JS−J yok → "piyasa biliyor" sınıfı |
| T147 | at bazında zemin tercihi | 0,0000 → kapalı |
| T148 | ayrışma O/E (betimsel) | Z≫piyasa O/E 1,17, ROI 0,658 [0,606;0,719]; hiçbir grup 1,00 üstü değil |
| T149 | videonun tam sıra zaman serisi | ZV2−Z +0,00442 [+0,00243;+0,00661] 12/13; ZV2−ZV +0,00285 [+0,00101;+0,00460]; JV2−J +0,00190 [+0,00040;+0,00332] 9/13 → ADAY, ilk hem piyasasız hem piyasalıda anlamlı |

**Genel okuma:** piyasa ≫ özelliklerimiz. Piyasasız Ρ tüm yöntemlerde ≈0,80–0,82; tek bir özellik grubu 0,07–0,085 nat boşluğu kapatmıyor; darboğaz yöntem değil BİLGİ. Küçük gerçek kazançlar: soy/yaş (yalnız piyasasız), video olayları (T142/T149). Bizim engelimiz: kesinti — 1 TL ganyan tüm atlara ~0,61–0,64 döner, ~%55–60 kenar gerekir.

## 5. Benter 1994 hakkında doğrulanmış gerçekler
19 faktör grubu (güncel kondisyon, geçmiş performans, ayarlamalar: rakip gücü/kilo/jokey/şanssızlık/kapı, mevcut koşu, tercihler: mesafe/pist/zemin/hipodrom); antrenör/tempo/sınıf adıyla geçmiyor. Birleşik logit (α,β). Pseudo-R² kamu 0,1218 / temel 0,1245 / birleşik 0,1396 (örnek türü belirtilmemiş); 2.313 koşuluk OOS: kamu 0,1237, 9 faktörlü temel 0,1016, birleşik 0,1327, tipster 0,1014. ~5+5 adam-yıl. HK kesinti ~%17–19. Kesirli Kelly. Egzotik havuzlarda avantaj daha yüksek (Harville γ=0,81, δ=0,65). İçeriden bilgi modellenemez.

## 6. Veri
`data/atyarisi/*.json.gz` (1231 gün, 2023-06→; program.horses: parents.{father,mother,fatherOfMother,fatherOfFather}, breeder, owner, birthdateEpoch, salePrice [%1,8–2,3 dolu], last6, equipment, kgs, weight; liste: hipodrom pist durumu/ağırlığı + hava), `data/video_seyir` (9.130 json, 2024-10→; 'zaman' her 0,5 sn ÖNDEKİ 5 atın sırası; 'ozet' erken/orta/geç/son; ham video SAKLANMIYOR), `data/galop` (139.283 satır, 2026-01-01→11-05, galop.yml/idman.yml günlük, %94,8 kapsam), `data/accurace` (kullanıcı yüklü PDF'ler, OCR; çoğu İstanbul/İzmir; otomatik ÇEKİLEMEZ), `data/program, zengin, kron, odeme, yorumcu, temiz`.
Elo/rakip gücü VAR ve Benter içinde: `tjk/elo.py` (f_elo, f_rak3, f_elo_m, f_rak3_m, f_jel, f_tel), T27/T28 geçti.

## 7. ÖNEMLİ: /tmp önbellekleri yeni oturumda KAYBOLUR
`/tmp/claude-0/jason_d.pkl` (200.105 satır × 94 sütun, 2023-01..2026-10) T134–T149'un tek kaynağı. **Üreten betik bulunamadı** (betikler yalnız okuyor; en yakın: `t132_katsayi_degisim.py` data/temiz/2024-10+ ve atyarisi'nden kendi tablosunu kuruyor). Yeni oturumda ilk iş: jason_d'yi yeniden üretmek ve üreten betiği repoya eklemek; üretimdeki Jason'ın özellik hattından (M["feat"] 34 özellik + GL.EK f_dp150_m, f_jgen100, f_fig3 = 37; GL.LPEK=["f_lp2"] listede SON olmalı) üretip eski sonuçlarla (örn. T138 J −1,8058, P −1,8254) doğrula. Diğerleri yeniden üretilebilir: `ay_oz.pkl`/`ay_gun.pkl` ← `t146_hazirla.py`; `t145_oos.pkl` ← `t145_segment.py`; `video_ozet.pkl` ← data/video_seyir 'ozet'.
Test iskeleti: `GL._fit(d, feat, lam=100)` → (theta, mu, sd, nk); skorlama `GL.z2(te, A)` LPEK'i hariç tutar; piyasasız = eğitim kopyasında lp=0 ve yalnız z skoru. LightGBM sabit: num_leaves 15, lr 0,03, min_data_in_leaf 200, ff 0,7, bagging 0,8, λ2 10, son 60 günde erken durdurma.

## 8. Bu oturumdaki HATALARIM (dürüst liste) ve çalışma kuralları
1. "At için Elo yok" dedim; YANLIŞ — Elo var, Benter'de. (Deftere düzeltme yazıldı.) Defteri grep'lemeden "yok" deme.
2. "Tempo/pist/galop yok" dedim; var (T49 PM0 bunları içeriyor). T138–T141 "Z" yalnız Jason'ın 37 özelliği: Benter'in TAM piyasasız karşılığı değil; ikisini karıştırmayacaksın.
3. Benter makalesindeki rakamları belirsiz örnek türüyle verdim; sonra düzelttim. Makale rakamını "OOS" diye sunmadan önce örnek türünü belirt.
4. Ana hedefi "piyasasız modelle piyasayı geçmek" diye yorumladım; kullanıcı iki aşamalı hedefi tanımladı.
5. "Bugünkü yorumcu raporu" = biten günün (dünün) raporu; yanlış anladım. Sadece ilk seçimleri değil TÜM seçimleri kullan.
6. T144'te sabit sütun (`fg_var_yok`, sd=0) NaN ağırlık → log-olasılık 0,0000 gibi göründü, sessiz kaldı. Her testte sütun varyansı ve NaN kontrolü yap, sonuçları sağlama (ham değerler makul mü) ile doğrula.
7. Diğer betik hataları: T144 `d.at` (pandas .at erişimcisi) → `d["at"]`; T146'da yinelenen `sahip` sütunu; önceki T134'te eksik mesafe/pist'in kısa/kum sayılması ve f_lp2 konumu (düzeltildi).
8. Padok örneklemesini yanlış zamanladım (12:40/15 dk), sonra değiştirdim.
9. Galop/idman kapsamı ve yarış içi olay verisi hakkında kesinlik taslayıp sonra düzelttim. "Video verisi her şeyi içerir" değil: yalnız ön-5 atı izliyor.
10. Çok sayıda ardışık, birbirine bağlı iddiada kendi önceki ifademi kontrol etmedim. Kural: sayı/iddia vermeden önce dosyadan doğrula; emin değilsen "doğrulamadım" de.
Genel uyarı: T142, T146, T149 "ADAY"ları çoklu karşılaştırma altında; hiçbiri üretime eklenmedi, eklenmesin — ileri doğrulama ve Benter-tabanı testi önce.

## 9. Bekleyen işler
- 6 Kasım sabahı kullanıcı eksik Accurace günlerini gönderecek (gelen.py OCR hattı). padok_kare ilk koşusu 13:25 TR (artifact `padok_kare_<run_id>`; 5,25 sa, 60 sn). TJK planlı bakım (5→6 Kasım gecesi) sonrası gece işi/AGF/program çekimini kontrol et; ortak.py devre kesicisi (3 ardışık 403→dur) var. `agf_zaman_yaz` sabah modunda AGF zaman serisi yazmıyor (düzeltilecek). Galop/idman geçmişi geriye doldurma dene; TJK yarış sonrası rapor/yorum (yarış içi olay) ara; ödeme verisi Haz–Ağu 2026 doldurma.
- 6 Kasım Bursa yorumcu notları (Elmas Dedem, Start Verilmeden) sonuçtan sonra aynı büyüklükte Jason kıyasıyla puanla; Naim 8 Kasım Pazar İstanbul notu doğrulanmadı; T137'yi veri büyüdükçe güncelle (`python3 data/analiz/t137_yorumcu_bilgi.py`).
- Sıradaki aday testler (her biri önce ön kayıt): T142/T149 ileri doğrulama + Benter tabanı; cinsiyet/yaş×mesafe; altılı/3-4-5'li ganyan atlası (ayak koşullu); ham video yeniden indirme (ön-5 dışı olaylar, Actions işi); padok pilotu T143 (3 günlük fizibilite).
- Eski liste: Kuponlar/Sabit/Canlı sekmelerinde ekür tipi JS hatası kontrolü; video_gunluk geri doldurma; "~5 dk" başlık metni → 7 dk; T129/T128 artığı; T124b bölüm temizliği; T127 örnekleri; T131 değerlendirme (31 Ocak 2027); T41 yeniden test Kas–Oca; Benter ROI çizgisi; yer kaybı testi 1 Aralık 2026; kilo/mesafe/pist 1 Mart 2027; T45 1 Mart 2027; Benter pm5 loglama doğrulama.
