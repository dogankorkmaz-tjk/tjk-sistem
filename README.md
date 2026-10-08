# TJK model – Ganyan Masası

Benter tarzı kazanma olasılığı modelinin canlı testi. Amaç para kazanmak değil, modeli test etmek.

## Ne otomatik çalışır (GitHub Actions)
| Saat (TR) | İş |
|---|---|
| 03:30 | Dünün (ve eksik günlerin) sonuçları geçmişe eklenir, canlı test skoru hesaplanır |
| 09:15, 12:40 | Bugünün programı (tüm Türkiye hipodromları), modelin form puanları, AGF |
| 13:00–01:00, 20 dk'da bir | AGF yenilenir, biten koşuların sonucu ve kapanış ganyanları eklenir |

Veri kaynağı: agftablosu.com (robots.txt izin veriyor; çalışma başına az sayıda, yavaş istek).

## Site
`docs/` klasörü GitHub Pages ile yayınlanır. Telefonda Chrome → "Ana ekrana ekle".

## Model
`data/model_v1.json` 8 Ekim 2026'da donduruldu ve değişmez. Canlı test sekmesi yalnızca bu tarihten sonraki, modelin hiç görmediği koşuları sayar.

## Elle çalıştırma
Actions → tjk → Run workflow → mod: `sabah`, `canli`, `gece`, `skor` veya `hepsi`.
