"""T36 jokey–at aşinalığı: f_jn=log1p(önceki biniş sayısı) (atın geçmişi varsa), f_j1=[ilk kez biniyor ∧ atın geçmişi var],
f_jat=(jokey,at) çiftinin ÖNCEKİ günlerdeki ortalama (kazandı−p_piyasa), n/(n+5) büzmeli ×10. Yalnız önceki günler."""
import numpy as np, collections
def ekle(d, jat):
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    at = d["at"].astype(str).values; jk = d.jokey.astype(str).values; gun = d.tarih.astype(str).values; ex = (d.kazandi.values - d.p_piyasa.values)
    N = collections.defaultdict(int); S = collections.defaultdict(float); AN = collections.defaultdict(int)
    jn = np.zeros(len(d)); j1 = np.zeros(len(d)); fj = np.zeros(len(d)); pend = []; cur = None
    for i in range(len(d)):
        if gun[i] != cur:
            for k_, a_, e_ in pend: N[k_] += 1; AN[a_] += 1; S[k_] += e_ if np.isfinite(e_) else 0.0
            pend = []; cur = gun[i]
        k = (at[i], jk[i]); n = N[k]
        if AN[at[i]] > 0: jn[i] = np.log1p(n); j1[i] = float(n == 0); fj[i] = 10 * S[k] / (n + 5.0)
        pend.append((k, at[i], ex[i]))
    d["f_jn"] = jn; d["f_j1"] = j1
    if jat: d["f_jat"] = fj
    return d
