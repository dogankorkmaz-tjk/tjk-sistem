"""T61: Milliyet/Misli altılı analizleri geriye dönük puanlama. python3 data/analiz/milliyet_misli_t61.py
Veri: WebFetch ile çekilen 13 yazı (13 gün; 25 Ekim temiz sonuçlarda yok, 15.06/13.06/24.07/4.07 yazıları erişilemedi). data/yorumcu_gecmis/milliyet_misli.json"""
import json, glob, numpy as np, pandas as pd
D = json.load(open('data/yorumcu_gecmis/milliyet_misli.json', encoding='utf-8'))
T = pd.concat([pd.read_csv(f, low_memory=False) for f in sorted(glob.glob('data/temiz/2026-0[6-9].csv.gz')) + ['data/temiz/2026-10.csv.gz']])
T0 = T.copy()          # ayak doğrulaması koşmayanları da içerir (kuponda olan at sonradan koşmaz olabilir)
T = T[(T.kosmadi != True)]
def kosu(t, h, k): return T[(T.tarih == t) & (T.hipodrom == h) & (T.kosu == k)]
def kazanan(r): w = r[r.sira == 1].no.tolist(); return w[0] if w else None
def topk(r, k): return set(r.sort_values('p_piyasa', ascending=False).no.head(k).tolist())
rows = []; altili = []; ban = []; sur = []
for g in D:
    t, h = g['tarih'], g['hipodrom']; R = int(T[(T.tarih == t) & (T.hipodrom == h)].kosu.max())
    for c in g['kuponlar']:
        no = c.get('altili')
        cand = [list(range(R - 5, R + 1))] if no is None else [list(range(1, 7)) if no == 1 else list(range(R - 5, R + 1))]
        ok = None
        for ks in cand:       # ayak büyüklüğü doğrulaması: at numaraları o koşuda var mı
            if all(all(int(x) in set(T0[(T0.tarih == t) & (T0.hipodrom == h) & (T0.kosu == k)].no) for x in c['ayak'][i]) for i, k in enumerate(ks)): ok = ks; break
        if ok is None: print('eşlenemedi', t, h, c['ad'], c['tip']); continue
        hits = []
        for i, k in enumerate(ok):
            r = kosu(t, h, k); w = kazanan(r); s = set(int(x) for x in c['ayak'][i]); n = len(r)
            if w is None: hits = None; break
            hits.append((w in s, len(s), w in topk(r, len(s)), len(s) / n))
        if hits is None: continue
        for x in hits: rows.append((c['ad'], c['tip'], t) + x)
        altili.append((c['ad'], c['tip'], t, all(x[0] for x in hits), all(x[2] for x in hits), int(np.prod([x[1] for x in hits]))))
    for b in g.get('banko', []):
        r = kosu(t, h, b['kosu']); w = kazanan(r)
        if w is not None: ban.append((t, w == b['no'], r[r.no == b['no']].ganyan.iloc[0] if (r.no == b['no']).any() else np.nan, w in topk(r, 1)))
    for b in g.get('surpriz', []):
        r = kosu(t, h, b['kosu']); w = kazanan(r)
        if w is None or not (r.no == b['no']).any(): continue
        a = r[r.no == b['no']].iloc[0]; sur.append((t, b['no'], w == b['no'], a.sira <= 3, a.sira <= 5, a.ganyan, w and r[r.no == w].ganyan.iloc[0]))
R_ = pd.DataFrame(rows, columns=['ad', 'tip', 'tarih', 'hit', 'k', 'pazar', 'rast'])
print('AYAK PUANI (liste içinde kazanan | kapanış piyasası aynı sayıda ilk-k | rastgele beklenti | ort. k)')
for key, g in list(R_.groupby('ad')) + [('TÜMÜ', R_)] + list(R_.groupby('tip')):
    print(f"{str(key):22s} ayak {len(g):3d} | yorumcu {g.hit.mean()*100:5.1f}% | piyasa {g.pazar.mean()*100:5.1f}% | rastgele {g.rast.mean()*100:5.1f}% | k={g.k.mean():.1f}")
A = pd.DataFrame(altili, columns=['ad', 'tip', 'tarih', 'tam', 'pazar_tam', 'kombo'])
print('\nALTILI (6/6): kupon', len(A), '| yorumcu tam', int(A.tam.sum()), '| piyasa ilk-k tam', int(A.pazar_tam.sum()))
print(A.groupby('ad').agg(kupon=('tam', 'size'), tam=('tam', 'sum'), piyasa_tam=('pazar_tam', 'sum'), ort_kombo=('kombo', 'mean')).round(0).to_string())
Bn = pd.DataFrame(ban, columns=['tarih', 'kazandi', 'g', 'fav'])
print('\nBANKO:', len(Bn), 'koşu | kazandı', int(Bn.kazandi.sum()), '| ort. ganyan %.2f' % Bn.g.mean(), '| piyasa favorisi', int(Bn.fav.sum()))
S = pd.DataFrame(sur, columns=['tarih', 'no', 'kazandi', 'ilk3', 'ilk5', 'g', 'kazg'])
print('SÜRPRİZ ADAYI:', len(S), 'at | kazandı', int(S.kazandi.sum()), '| ilk3', int(S.ilk3.sum()), '| ilk5', int(S.ilk5.sum()), '| ort. ganyan %.1f' % S.g.mean())
print(S.to_string())
