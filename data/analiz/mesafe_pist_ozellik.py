"""Mesafe/pist özellikleri: arşivden eksik mesafe/pist doldurulur, f_dp150_m yeniden hesaplanır, EXTRA ise 5 yeni özellik eklenir. Ön kayıt: hipotez_defteri 2026-10-24 17:45."""
import numpy as np, pandas as pd
def uygula(d, extra):
    A = pd.read_pickle("/tmp/claude-0/arsiv_mp.pkl").drop_duplicates(["tarih", "hip", "kosu"])
    d = d.merge(A.rename(columns={"hip": "hipodrom", "mesafe": "m_a", "pist": "p_a"}), on=["tarih", "hipodrom", "kosu"], how="left")
    d["mesafe"] = d.mesafe.where(d.mesafe.notna(), d.m_a); d["pist"] = d.pist.where(d.pist.notna(), d.p_a); d = d.drop(columns=["m_a", "p_a"])
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    rk = d.groupby(["tarih", "hipodrom", "kosu"]).p_piyasa.rank(ascending=False, method="first")
    res = ((rk - 1) / (d.n_at - 1).clip(lower=1) - d.pct).clip(-1, 1).values
    mes = d.mesafe.values.astype(float); pst = d.pist.astype(str).values; tr = pd.to_datetime(d.tarih).values
    n = len(d); dp = np.zeros(n); ps = np.zeros(n); dpp = np.zeros(n); pch = np.zeros(n); dup = np.zeros(n); ddn = np.zeros(n)
    for at, ix in d.groupby("at").indices.items():
        if len(ix) < 2: continue
        ix = ix[np.argsort(tr[ix], kind="stable")]; m = mes[ix]; r = res[ix]; p = pst[ix]
        for j in range(1, len(ix)):
            ok = ~np.isnan(r[:j])
            if not np.isnan(m[j]) and ok.any():
                okm = ok & ~np.isnan(m[:j]); 
                if okm.any():
                    w = np.exp(-np.abs(m[:j][okm] - m[j]) / 150.0); dp[ix[j]] = (w * r[:j][okm]).sum() / (w.sum() + 2.0)
                    same = okm & (p[:j] == p[j])
                    if same.any():
                        w2 = np.exp(-np.abs(m[:j][same] - m[j]) / 150.0); dpp[ix[j]] = (w2 * r[:j][same]).sum() / (w2.sum() + 2.0)
            if p[j] != "nan" and ok.any():
                same = ok & (p[:j] == p[j])
                if same.any(): ps[ix[j]] = r[:j][same].sum() / (same.sum() + 2.0)
            if p[j] != "nan" and p[j - 1] != "nan": pch[ix[j]] = float(p[j] != p[j - 1])
            if not np.isnan(m[j]) and not np.isnan(m[j - 1]):
                lr = np.log(m[j] / m[j - 1]); dup[ix[j]] = max(0.0, lr); ddn[ix[j]] = max(0.0, -lr)
    d["f_dp150_m"] = dp
    if extra:
        d["f_ps"], d["f_dpp"], d["f_pchg"], d["f_dup"], d["f_ddn"] = ps, dpp, pch, dup, ddn
    return d
EXTRA_FEAT = ["f_ps", "f_dpp", "f_pchg", "f_dup", "f_ddn"]
