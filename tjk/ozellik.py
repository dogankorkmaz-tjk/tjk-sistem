"""Model özellikleri. Colab'daki (8 Ekim'de canlı çalışan) hücrenin fonksiyon hâli; formüller aynı."""
import numpy as np, pandas as pd
from .ortak import K


def onceki_gunler(d, anahtar, M, taban=0.10):
    g = d.groupby([anahtar, 'tarih']).agg(n=('kazandi', 'size'), w=('kazandi', 'sum')).reset_index()
    g = g.sort_values('tarih')
    g['cn'] = g.groupby(anahtar).n.cumsum() - g.n
    g['cw'] = g.groupby(anahtar).w.cumsum() - g.w
    g['oran'] = (g.cw + M * taban) / (g.cn + M) - taban
    return d[[anahtar, 'tarih']].merge(g[[anahtar, 'tarih', 'oran']], on=[anahtar, 'tarih'], how='left').oran.values


def hazirla(temiz, prog, model, yeni=None):
    """temiz: geçmiş sonuçlar (tjk_temiz), prog: geçmiş program, yeni: sonucu bilinmeyen satırlar
    (program sayfasından; sira/kazandi yok). Dönen tabloda her satırın 'z' (form puanı) değeri var."""
    prog = prog.drop_duplicates(K + ['no'])
    keep = ['tarih', 'hipodrom', 'kosu', 'no', 'yas_ham', 'baba', 'sahip', 'antrenor', 'st', 'hk', 'son6', 'kgs']
    d = temiz.merge(prog[[c for c in keep if c in prog.columns]], on=K + ['no'], how='left')
    d['yeni'] = False
    if yeni is not None and len(yeni):
        y = yeni.copy()
        y['yeni'] = True
        y['sira'] = np.nan; y['kazandi'] = 0; y['derece_sn'] = np.nan
        y['ganyan'] = y.get('ganyan', pd.Series(10.0, index=y.index)).fillna(10.0)
        y['p_ham'] = 1 / y.ganyan
        y['p_piyasa'] = y.p_ham / y.groupby(K).p_ham.transform('sum')
        d = pd.concat([d, y], ignore_index=True)
    d = d.sort_values(['tarih', 'hipodrom', 'kosu', 'no']).reset_index(drop=True)
    d['rid'] = d.groupby(K).ngroup()
    ps = d.groupby('rid').p_ham.transform('sum')
    nw = d.groupby('rid').kazandi.transform('sum')
    d['temiz'] = ((ps.between(1.3, 1.6)) & (nw == 1)) | d.yeni
    d['n_at'] = d.groupby('rid')['at'].transform('size')
    d['pct'] = (d.sira - 1) / (d.n_at - 1).clip(lower=1)
    d.loc[d.yeni, 'pct'] = 0.0
    d['tarih_dt'] = pd.to_datetime(d.tarih)
    d['lp'] = np.log(d.p_piyasa)

    gh = d.groupby('at')
    d['h_n'] = gh.cumcount()
    d['h_win'] = gh.kazandi.cumsum() - d.kazandi
    d['h_pct_son'] = gh.pct.shift(1)
    d['h_pct_3'] = gh.pct.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    d['h_gun'] = (d.tarih_dt - gh.tarih_dt.shift(1)).dt.days
    gj = d.groupby('jokey')
    d['j_n'] = gj.cumcount()
    d['j_win'] = gj.kazandi.cumsum() - d.kazandi
    M = 5.0
    d['f_hwin'] = (d.h_win + M * 0.10) / (d.h_n + M) - 0.10
    d['f_hpct3'] = d.h_pct_3.fillna(0.5) - 0.5
    d['f_hpctson'] = d.h_pct_son.fillna(0.5) - 0.5
    d['f_ilk'] = (d.h_n == 0).astype(float)
    d['f_gun'] = np.log1p(d.h_gun.fillna(60).clip(upper=180)) - 3.5
    d['f_jwin'] = (d.j_win + 30 * 0.10) / (d.j_n + 30) - 0.10
    d['f_kilo'] = d.kilo - d.groupby('rid').kilo.transform('mean')
    d['f_apr'] = d.apranti.astype(float)

    d['rel_sure'] = d.derece_sn - d.groupby('rid').derece_sn.transform('min')
    d['hnd_ok'] = d.hnd.where(d.hnd > 0).fillna(d.hk.where(d.hk > 0))
    d['hnd_rel'] = d.hnd_ok - d.groupby('rid').hnd_ok.transform('mean')
    gh = d.groupby('at')
    d['son_jokey'] = gh.jokey.shift(1)
    d['son_kilo'] = gh.kilo.shift(1)
    d['son_rel'] = gh.rel_sure.shift(1)
    gp = d.groupby(['at', 'jokey'])
    d['p_n'] = gp.cumcount(); d['p_win'] = gp.kazandi.cumsum() - d.kazandi
    gx = d.groupby(['at', 'hipodrom'])
    d['x_n'] = gx.cumcount(); d['x_pct'] = gx.pct.cumsum() - d.pct
    d['f_jdeg'] = ((d.h_n > 0) & (d.son_jokey != d.jokey)).astype(float)
    d['f_kilodeg'] = (d.kilo - d.son_kilo).fillna(0).clip(-6, 6)
    d['f_sonrel'] = d.son_rel.fillna(d.rel_sure.median()).clip(upper=6)
    d['f_hnd'] = d.hnd_rel.fillna(0)
    d['f_cift'] = (d.p_win / (d.p_n + 2))
    d['f_hippct'] = (d.x_pct + 3 * 0.5) / (d.x_n + 3) - 0.5
    d['f_no'] = d.no / d.n_at - 0.5
    d['f_gun_kisa'] = (d.h_gun <= 14).astype(float)
    d['f_gun_orta'] = ((d.h_gun > 14) & (d.h_gun <= 42)).astype(float)
    d['f_gun_uzun'] = (d.h_gun > 90).astype(float)

    d['f_twin'] = np.nan_to_num(onceki_gunler(d, 'antrenor', 30))
    d['f_swin'] = np.nan_to_num(onceki_gunler(d, 'sahip', 30))
    d['f_bwin'] = np.nan_to_num(onceki_gunler(d, 'baba', 60))
    tok = d.yas_ham.fillna('').astype(str).str.split()
    d['yas'] = pd.to_numeric(d.yas_ham.fillna('').astype(str).str.extract(r'(\d+)')[0], errors='coerce')
    d['f_yas'] = (d.yas.fillna(4).clip(2, 9) - 4)
    d['t2'] = tok.str[1].fillna('?'); d['t3'] = tok.str[2].fillna('?')
    for ad_ in model["cins"]:
        kol, v = ad_.split('_')[1], ad_[len('f_t2_'):]
        d[ad_] = (d[kol] == v).astype(float)
    d['f_st'] = ((d.st - (d.n_at + 1) / 2) / d.n_at).fillna(0)
    d['f_st1'] = (d.st == 1).astype(float)
    cift = d.son6.fillna('').astype(str).str.replace(r'\D', '', regex=True)
    pos = cift.apply(lambda s: [10 if c == '0' else int(c) for c in s])
    d['s6_n'] = pos.str.len()
    d['f_s6ort'] = pos.apply(lambda l: np.mean(l) if l else np.nan)
    d['f_s6top3'] = pos.apply(lambda l: np.mean([x <= 3 for x in l]) if l else np.nan)
    d['f_s6ort'] = (d.f_s6ort.fillna(d.f_s6ort.mean()) - d.f_s6ort.mean())
    d['f_s6top3'] = (d.f_s6top3.fillna(d.f_s6top3.mean()) - d.f_s6top3.mean())
    d['f_s6n'] = d.s6_n - 6
    d['f_kgs'] = np.log1p(d.kgs.fillna(d.h_gun).fillna(60).clip(upper=180)) - 3.5

    d = d[d.temiz].copy()
    mu, sd, w, feat = pd.Series(model["mu"]), pd.Series(model["sd"]), np.array(model["w"]), model["feat"]
    d['z'] = ((d[feat] - mu[feat]) / sd[feat]).values @ w[1:]
    return d


def model_olasilik(p_piyasa, z, w0):
    s = w0 * np.log(np.asarray(p_piyasa, float)) + np.asarray(z, float)
    e = np.exp(s - s.max())
    return e / e.sum()
