"""T62: süpriz oranı koşu tipine göre. python3 data/analiz/supriz_tip_t62.py"""
import os, numpy as np, pandas as pd
ESIK = float(os.environ.get('ESIK', 15))
np.random.seed(62)
d = pd.read_pickle('/tmp/claude-0/jason_d.pkl'); d = d[(d.kosmadi == False) | d.kosmadi.isna()]
g = d.groupby(['tarih', 'hipodrom', 'kosu'])
R = g.agg(n=('no', 'size'), kz=('kazandi', 'sum'), mesafe=('mesafe', 'first'), pist=('pist', 'first'), yas=('yas', 'median'), hk=('hk', lambda s: s.notna().mean()),
          gk=('ganyan', lambda s: np.nan)).reset_index()
W = d[d.kazandi == 1].groupby(['tarih', 'hipodrom', 'kosu']).ganyan.first().rename('gw').reset_index()
R = R.merge(W, on=['tarih', 'hipodrom', 'kosu'], how='left'); R = R[(R.kz == 1) & (R.n >= 5) & R.gw.notna() & R.mesafe.notna() & R.pist.notna()].copy()
R['sur'] = (R.gw >= ESIK).astype(float)
print('EŞİK', ESIK); print('kazanan ganyan dağılımı:', R.gw.pipe(lambda x: {'<3': round((x<3).mean(),3), '3-5': round(((x>=3)&(x<5)).mean(),3), '5-7': round(((x>=5)&(x<7)).mean(),3), '7-10': round(((x>=7)&(x<10)).mean(),3), '10-15': round(((x>=10)&(x<15)).mean(),3), '>=15': round((x>=15).mean(),3)}))
R['mes'] = pd.cut(R.mesafe, [0, 1200, 1500, 1900, 9999], labels=['<=1200', '1300-1500', '1600-1900', '>=2000'])
R['alan'] = pd.cut(R.n, [0, 8, 10, 12, 99], labels=['<=8', '9-10', '11-12', '>=13'])
R['yg'] = pd.cut(R.yas, [0, 2.5, 3.5, 99], labels=['2', '3', '4+'])
R['hnd'] = np.where(R.hk > 0.5, 'handikap', 'diger'); R['ay'] = pd.to_datetime(R.tarih).dt.month.map(lambda m: 'kis(12-2)' if m in (12, 1, 2) else 'bahar(3-5)' if m in (3, 4, 5) else 'yaz(6-8)' if m in (6, 7, 8) else 'sonbahar(9-11)')
R['yari'] = np.where(R.tarih < R.tarih.quantile(0.5, interpolation='nearest'), 'A', 'B')
print(f"koşu {len(R)} | süpriz oranı {R.sur.mean()*100:.1f}% | dönem {R.tarih.min()}..{R.tarih.max()} | yarı sınırı {R[R.yari=='B'].tarih.min()}")
days = R.tarih.unique(); gi = {t: np.where(R.tarih.values == t)[0] for t in days}
B = [np.concatenate([gi[t] for t in np.random.choice(days, len(days))]) for _ in range(1000)]
def fark(mask, idx=None, sub=None):
    m = mask if idx is None else mask[idx]; s = R.sur.values if idx is None else R.sur.values[idx]
    if m.sum() == 0 or (~m).sum() == 0: return np.nan
    return s[m].mean() - s[~m].mean()
sat = []
for col in ['hipodrom', 'mes', 'pist', 'alan', 'yg', 'hnd', 'ay']:
    for lv in R[col].dropna().unique():
        m = (R[col] == lv).values
        if m.sum() < 60: continue
        f = fark(m); bs = [fark(m, b) for b in B]; lo, hi = np.nanpercentile(bs, [0.05, 99.95])
        fa = fark(m & (R.yari == 'A').values) if False else None
        mA = (m & (R.yari.values == 'A')); mB = (m & (R.yari.values == 'B'))
        def yfark(y):
            sel = (R.yari.values == y); mm = m[sel]; s = R.sur.values[sel]
            return s[mm].mean() - s[~mm].mean() if mm.sum() > 20 and (~mm).sum() > 20 else np.nan
        sat.append((col, str(lv), int(m.sum()), R.sur.values[m].mean() * 100, f * 100, lo * 100, hi * 100, yfark('A') * 100, yfark('B') * 100))
S = pd.DataFrame(sat, columns=['boyut', 'duzey', 'n_kosu', 'surpriz%', 'fark_pp', 'GA_lo(Bonf)', 'GA_hi(Bonf)', 'farkA', 'farkB'])
S['ornuntu'] = (S['GA_lo(Bonf)'] > 0) | (S['GA_hi(Bonf)'] < 0)
S['yinelendi'] = S.ornuntu & (np.sign(S.farkA) == np.sign(S.farkB)) & (np.sign(S.farkA) == np.sign(S.fark_pp))
pd.set_option('display.width', 200); print(S.round(1).sort_values('fark_pp').to_string(index=False))
print('\nÖRÜNTÜ (Bonferroni GA 0 dışında, iki yarıda aynı yön):'); print(S[S.yinelendi].round(1).to_string(index=False) if S.yinelendi.any() else 'YOK')
# alan büyüklüğü kontrolü: beklenen = at sayısına (n=5..16+) göre süpriz oranı (dolaylı standardizasyon); düzeyin gözlenen - beklenen farkı
R['nn'] = R.n.clip(upper=16); beklenen = R.groupby('nn').sur.transform('mean'); R['art'] = R.sur - beklenen
sat2 = []
for col in ['hipodrom', 'mes', 'pist', 'yg', 'ay']:
    for lv in R[col].dropna().unique():
        m = (R[col] == lv).values
        if m.sum() < 60: continue
        f = R.art.values[m].mean()
        bs = []
        for b in B:
            mm = m[b]; bs.append(R.art.values[b][mm].mean() if mm.sum() else np.nan)
        lo, hi = np.nanpercentile(bs, [0.05, 99.95])
        def y(yy):
            sel = (R.yari.values == yy) & m; return R.art.values[sel].mean() if sel.sum() > 20 else np.nan
        sat2.append((col, str(lv), int(m.sum()), R.sur.values[m].mean() * 100, f * 100, lo * 100, hi * 100, y('A') * 100, y('B') * 100))
S2 = pd.DataFrame(sat2, columns=['boyut', 'duzey', 'n_kosu', 'surpriz%', 'art_pp', 'GA_lo', 'GA_hi', 'artA', 'artB'])
S2['yinelendi'] = ((S2.GA_lo > 0) | (S2.GA_hi < 0)) & (np.sign(S2.artA) == np.sign(S2.artB)) & (np.sign(S2.artA) == np.sign(S2.art_pp))
print('\nALAN BÜYÜKLÜĞÜ KONTROLLÜ (gözlenen - at sayısına göre beklenen süpriz oranı, puan):'); print(S2.round(1).sort_values('art_pp').to_string(index=False))
print('\nALAN KONTROLLÜ ÖRÜNTÜ:'); print(S2[S2.yinelendi].round(1).to_string(index=False) if S2.yinelendi.any() else 'YOK')
print('\nAlan büyüklüğü x süpriz oranı:'); print(R.groupby('alan', observed=True).sur.agg(['size', 'mean']).round(3).to_string())
