"""T35 kapı ≤1300: f_k13 = (kapı konumu−0.5)×[D≤1300]; f_kh = (hipodrom,mesafe,pist,kapı grubu) hücresinin ÖNCEKİ günlerdeki
ortalama (kazandi − p_piyasa) değeri, n/(n+K) büzmeli (yalnız D≤1300). Sızıntı yok: bir günün satırları o günden ÖNCEKİ verilerle."""
import numpy as np, pandas as pd, collections
K = 300.0
def ekle(d, hucre):
    A = pd.read_pickle("/tmp/claude-0/arsiv_kapi.pkl").drop_duplicates(["tarih", "hip", "kosu", "no"]); A["tarih"] = A.tarih.astype(str)
    d = d.drop(columns=[c for c in ["start", "n_k", "D"] if c in d]).merge(A.rename(columns={"hip": "hipodrom"})[["tarih", "hipodrom", "kosu", "no", "start", "n_k", "D"]], on=["tarih", "hipodrom", "kosu", "no"], how="left")
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    st = d.start.values; n = d.n_k.values; D = d.D.values; ok = np.isfinite(st) & np.isfinite(D)
    out = np.where(ok, (st - 1) / np.clip(n - 1, 1, None) - 0.5, 0.0); kisa = ok & (D <= 1300)
    d["f_k13"] = np.where(kisa, out, 0.0)
    if hucre:
        grp = np.where(st <= 2, 0, np.where(st >= n - 1, 2, 1)); pist = d.pist.astype(str).values if "pist" in d else np.array(["?"] * len(d))
        key = [f"{h}|{int(x) if np.isfinite(x) else 0}|{p}|{g}" for h, x, p, g in zip(d.hipodrom.values, D, pist, grp)]
        ex = (d.kazandi.values - d.p_piyasa.values); gun = d.tarih.values; S = collections.defaultdict(float); C = collections.defaultdict(int); f = np.zeros(len(d)); pend = []; cur = None
        for i in range(len(d)):
            if gun[i] != cur:
                for k_, e_ in pend: S[k_] += e_; C[k_] += 1
                pend = []; cur = gun[i]
            if kisa[i]:
                c = C[key[i]]; f[i] = (S[key[i]] / c) * c / (c + K) if c else 0.0
                if np.isfinite(ex[i]): pend.append((key[i], ex[i]))
        d["f_kh"] = f * 10
    return d
