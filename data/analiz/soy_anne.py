"""T83 anne hattı: f_an = annenin ÖNCEKİ günlerdeki yavrularının (kardeşler) ort. bitiş artığı, n/(n+10) büzmeli; f_ab = anne babasının (fatherOfMother) yavru-torunlarının ort. artığı, n/(n+40);
f_abp = anne babası × pist tipi (kum/çim/sentetik) özgü kısım; f_abm = anne babası × mesafe bandı özgü kısım. res = piyasa sırası yüzdeliği − gerçek yüzdelik. Yalnız önceki günler."""
import numpy as np, collections, pickle
def band(m): return np.where(~np.isfinite(m), -1, np.where(m <= 1200, 0, np.where(m <= 1500, 1, np.where(m <= 1900, 2, 3))))
def ekle(d):
    M = pickle.load(open("/tmp/claude-0/soy_map.pkl", "rb"))
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    rk = d.groupby(["tarih", "hipodrom", "kosu"]).p_piyasa.rank(ascending=False, method="first")
    res = ((rk - 1) / (d.n_at - 1).clip(lower=1) - d.pct).clip(-1, 1).values
    an = np.array([M.get(a, ("", "", ""))[1] for a in d["at"].astype(str)]); ab = np.array([M.get(a, ("", "", ""))[2] for a in d["at"].astype(str)])
    import pandas as pd
    mb = band(pd.to_numeric(d.mesafe, errors="coerce").values.astype(float)); ps = d.pist.astype(str).values; gun = d.tarih.astype(str).values
    SN = collections.defaultdict(float); CN = collections.defaultdict(int); SB = collections.defaultdict(float); CB = collections.defaultdict(int)
    SP = collections.defaultdict(float); CP = collections.defaultdict(int); SM = collections.defaultdict(float); CM = collections.defaultdict(int)
    n = len(d); f_an = np.zeros(n); f_ab = np.zeros(n); f_abp = np.zeros(n); f_abm = np.zeros(n); pend = []; cur = None
    for i in range(n):
        if gun[i] != cur:
            for a_, b_, p_, m_, r_ in pend:
                if a_: SN[a_] += r_; CN[a_] += 1
                if b_:
                    SB[b_] += r_; CB[b_] += 1
                    if p_: SP[(b_, p_)] += r_; CP[(b_, p_)] += 1
                    if m_ >= 0: SM[(b_, m_)] += r_; CM[(b_, m_)] += 1
            pend = []; cur = gun[i]
        a_, b_ = an[i], ab[i]
        if a_: f_an[i] = SN[a_] / (CN[a_] + 10.0)
        if b_:
            f_ab[i] = SB[b_] / (CB[b_] + 40.0)
            if ps[i] in ("Kum", "Çim", "Sentetik"): f_abp[i] = SP[(b_, ps[i])] / (CP[(b_, ps[i])] + 40.0) - f_ab[i]
            if mb[i] >= 0: f_abm[i] = SM[(b_, mb[i])] / (CM[(b_, mb[i])] + 40.0) - f_ab[i]
        if np.isfinite(res[i]): pend.append((a_, b_, ps[i] if ps[i] in ("Kum", "Çim", "Sentetik") else None, mb[i], res[i]))
    d["f_an"] = f_an; d["f_ab"] = f_ab; d["f_abp"] = f_abp; d["f_abm"] = f_abm
    return d
