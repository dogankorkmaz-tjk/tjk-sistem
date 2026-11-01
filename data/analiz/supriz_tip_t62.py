"""T62: süpriz oranı koşu tipine göre. python3 data/analiz/supriz_tip_t62.py"""
import numpy as np, pandas as pd
np.random.seed(62)
d = pd.read_pickle('/tmp/claude-0/jason_d.pkl'); d = d[(d.kosmadi == False) | d.kosmadi.isna()]
g = d.groupby(['tarih', 'hipodrom', 'kosu'])
R = g.agg(n=('no', 'size'), kz=('kazandi', 'sum'), mesafe=('mesafe', 'first'), pist=('pist', 'first'), yas=('yas', 'median'), hk=('hk', lambda s: s.notna().mean()),
          gk=('ganyan', lambda s: np.nan)).reset_index()
W = d[d.kazandi == 1].groupby(['tarih', 'hipodrom', 'kosu']).ganyan.first().rename('gw').reset_index()
R = R.merge(W, on=['tarih', 'hipodrom', 'kosu'], how='left'); R = R[(R.kz == 1) & (R.n >= 5) & R.gw.notna() & R.mesafe.notna() & R.pist.notna()].copy()
R['sur'] = (R.gw >= 15).astype(float)
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
# lojistik regresyon: alan büyüklüğü sabit tutulur
try:
    import statsmodels.formula.api as smf
    m0 = smf.logit('sur ~ n', R).fit(disp=0); m1 = smf.logit('sur ~ n + C(mes) + C(pist) + C(yg) + C(hnd) + C(ay)', R).fit(disp=0)
    from scipy.stats import chi2
    lr = 2 * (m1.llf - m0.llf); df = m1.df_model - m0.df_model; print(f"\nLojistik: n'ye ek (mesafe+pist+yaş+handikap+mevsim) LR={lr:.1f} df={df:.0f} p={chi2.sf(lr, df):.4g}; n katsayısı {m0.params['n']:.3f}/at (süpriz olasılığı alan büyüdükçe)")
    for c in ['hipodrom']:
        m2 = smf.logit('sur ~ n + C(mes) + C(pist) + C(yg) + C(hnd) + C(ay) + C(hipodrom)', R).fit(disp=0); lr2 = 2 * (m2.llf - m1.llf); df2 = m2.df_model - m1.df_model; print(f"hipodrom ek LR={lr2:.1f} df={df2:.0f} p={chi2.sf(lr2, df2):.4g}")
except Exception as e:
    print('regresyon yok:', repr(e))
print('\nAlan büyüklüğü x süpriz oranı:'); print(R.groupby('alan', observed=True).sur.agg(['size', 'mean']).round(3).to_string())
