"""T38 soy–mesafe: f_sm = (baba, mesafe bandı) için babanın ÖNCEKİ günlerdeki yavrularının ort. bitiş artığı (res=piyasa sırası yüzdeliği−gerçek yüzdelik),
n/(n+20) büzmeli ×1; f_sd = f_sm − babanın tüm mesafelerdeki büzmeli ort. artığı (mesafeye ÖZGÜ etki). Bantlar: ≤1200, 1300–1500, 1600–1900, ≥2000."""
import numpy as np, collections
def band(m):
    return np.where(~np.isfinite(m), -1, np.where(m <= 1200, 0, np.where(m <= 1500, 1, np.where(m <= 1900, 2, 3))))
def ekle(d, K=20.0):
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    rk = d.groupby(["tarih", "hipodrom", "kosu"]).p_piyasa.rank(ascending=False, method="first")
    res = ((rk - 1) / (d.n_at - 1).clip(lower=1) - d.pct).clip(-1, 1).values
    b = band(d.mesafe.values.astype(float)); ba = d.baba.astype(str).values; gun = d.tarih.astype(str).values
    S = collections.defaultdict(float); C = collections.defaultdict(int); SA = collections.defaultdict(float); CA = collections.defaultdict(int)
    fm = np.zeros(len(d)); fd = np.zeros(len(d)); pend = []; cur = None
    for i in range(len(d)):
        if gun[i] != cur:
            for k_, bb, r_ in pend: S[(k_, bb)] += r_; C[(k_, bb)] += 1; SA[k_] += r_; CA[k_] += 1
            pend = []; cur = gun[i]
        if b[i] >= 0 and ba[i] not in ("nan", "None", ""):
            c = C[(ba[i], b[i])]; fm[i] = S[(ba[i], b[i])] / (c + K); ca = CA[ba[i]]; fd[i] = fm[i] - SA[ba[i]] / (ca + K)
            if np.isfinite(res[i]): pend.append((ba[i], b[i], res[i]))
    d["f_sm"] = fm; d["f_sd"] = fd
    return d
