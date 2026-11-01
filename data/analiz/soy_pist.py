"""T81 soy–pist: f_sp = (baba, pist tipi Kum/Çim/Sentetik) için babanın ÖNCEKİ günlerdeki yavrularının ort. bitiş artığı, n/(n+20) büzmeli; f_spd = f_sp − babanın tüm pistlerdeki büzmeli ort. (pist tipine ÖZGÜ etki)."""
import numpy as np, collections
def ekle(d, K=20.0):
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    rk = d.groupby(["tarih", "hipodrom", "kosu"]).p_piyasa.rank(ascending=False, method="first")
    res = ((rk - 1) / (d.n_at - 1).clip(lower=1) - d.pct).clip(-1, 1).values
    pst = d.pist.astype(str).values; ba = d.baba.astype(str).values; gun = d.tarih.astype(str).values
    S = collections.defaultdict(float); C = collections.defaultdict(int); SA = collections.defaultdict(float); CA = collections.defaultdict(int)
    fm = np.zeros(len(d)); fd = np.zeros(len(d)); pend = []; cur = None
    for i in range(len(d)):
        if gun[i] != cur:
            for k_, bb, r_ in pend: S[(k_, bb)] += r_; C[(k_, bb)] += 1; SA[k_] += r_; CA[k_] += 1
            pend = []; cur = gun[i]
        if pst[i] in ("Kum", "Çim", "Sentetik") and ba[i] not in ("nan", "None", ""):
            c = C[(ba[i], pst[i])]; fm[i] = S[(ba[i], pst[i])] / (c + K); ca = CA[ba[i]]; fd[i] = fm[i] - SA[ba[i]] / (ca + K)
            if np.isfinite(res[i]): pend.append((ba[i], pst[i], res[i]))
    d["f_sp"] = fm; d["f_spd"] = fd
    return d
