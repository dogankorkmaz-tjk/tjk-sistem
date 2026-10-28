"""T44 gün içi kapı eğilimi + T45 piyasa-ağırlığı etkileşimleri.
f_gi: aynı gün, aynı hipodrom ve aynı pist türünde ÖNCEKİ koşu numaralı koşularda kapı konumu x=(start-1)/(n-1)-0.5 ile
(kazandi - p_piyasa) arasındaki regresyon eğimi b=Sxy/(Sxx+3); f_gi = 10 * x * b. Sızıntı yok (yalnız kosu<k, sonuçları bilinen koşular).
T45: lp = log p_piyasa; f_lpk = lp*[n_at<=7], f_lpb = lp*[n_at>=12], f_lpkm = lp*[mesafe<=1300], f_lpum = lp*[mesafe>=2000]."""
import numpy as np, pandas as pd
K2 = 3.0
def gi(d):
    A = pd.read_pickle("/tmp/claude-0/arsiv_kapi.pkl").drop_duplicates(["tarih", "hip", "kosu", "no"]); A["tarih"] = A.tarih.astype(str)
    d = d.drop(columns=[c for c in ["start", "n_k", "D"] if c in d]).merge(A.rename(columns={"hip": "hipodrom"})[["tarih", "hipodrom", "kosu", "no", "start", "n_k", "D"]], on=["tarih", "hipodrom", "kosu", "no"], how="left")
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    x = np.where(np.isfinite(d.start) & np.isfinite(d.n_k) & (d.n_k > 1), (d.start - 1) / np.clip(d.n_k - 1, 1, None) - 0.5, 0.0)
    e = (d.kazandi.values - d.p_piyasa.values); e = np.where(np.isfinite(e), e, 0.0)
    pist = d.pist.astype(str).values if "pist" in d else np.array(["?"] * len(d))
    f = np.zeros(len(d)); gk = d.groupby(["tarih", "hipodrom", "kosu"], sort=False).indices
    st = {}; cur = None
    for (t, h, k), ix in gk.items():
        if cur != t: st = {}; cur = t
        p = pist[ix[0]]; key = (h, p); sxy, sxx = st.get(key, (0.0, 0.0))
        f[ix] = 10 * x[ix] * (sxy / (sxx + K2))
        st[key] = (sxy + float((x[ix] * e[ix]).sum()), sxx + float((x[ix] ** 2).sum()))
    d["f_gi"] = f
    return d
def lpk(d):
    lp = np.log(d.p_piyasa.clip(lower=1e-6).values); n = d.n_at.values.astype(float); m = d.mesafe.values.astype(float) if "mesafe" in d else np.full(len(d), np.nan)
    d["f_lpk"] = lp * (n <= 7); d["f_lpb"] = lp * (n >= 12); d["f_lpkm"] = lp * (m <= 1300); d["f_lpum"] = lp * (m >= 2000)
    return d
