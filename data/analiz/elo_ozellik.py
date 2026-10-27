"""Rakip gücü (Elo) özellikleri. Ön kayıt: hipotez_defteri 2026-10-28 00:55. d: tarih/hipodrom/kosu/no/at/sira sütunlu."""
import collections, numpy as np, pandas as pd
EXTRA_FEAT = ["f_elo", "f_rak3"]
def ekle(d, KELO=0.6):
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    rid = d.groupby(["tarih", "hipodrom", "kosu"]).ngroup().values
    sr0 = pd.to_numeric(d.sira, errors="coerce").fillna(0).values; tar = d.tarih.astype(str).values; at = d["at"].astype(str).values
    R = {}; HIST = collections.defaultdict(list); f_e = np.zeros(len(d)); f_r = np.zeros(len(d))
    gun = pd.Series(np.arange(len(d))).groupby(tar).apply(lambda x: (x.min(), x.max() + 1))
    for t, (i0, i1) in gun.items():
        r_ = rid[i0:i1]; bas = np.r_[0, np.nonzero(np.diff(r_))[0] + 1, len(r_)]; kos = [list(range(i0 + x, i0 + y)) for x, y in zip(bas[:-1], bas[1:])]; upd = []
        for idx in kos:
            rt = np.array([R.get(at[i], 0.0) for i in idx]); m = rt.mean()
            for q, i in enumerate(idx):
                f_e[i] = rt[q] - m; h = HIST[at[i]][-3:]; f_r[i] = np.mean(h) if h else 0.0
            upd.append((idx, rt))
        for idx, rt in upd:
            ok = [q for q, i in enumerate(idx) if sr0[i] > 0]; n = len(ok)
            if n < 3: continue
            rr = rt[ok]; sr = np.array([sr0[idx[q]] for q in ok])
            E = 1 / (1 + np.exp(-(rr[:, None] - rr[None, :]))); np.fill_diagonal(E, 0)
            S = (sr[None, :] > sr[:, None]).astype(float) + 0.5 * (sr[None, :] == sr[:, None]); np.fill_diagonal(S, 0)
            dl = KELO * (S.sum(1) - E.sum(1)) / (n - 1)
            for qq, q in enumerate(ok):
                i = idx[q]; HIST[at[i]].append((rr.sum() - rr[qq]) / (n - 1)); R[at[i]] = R.get(at[i], 0.0) + dl[qq]
    d["f_elo"] = f_e; d["f_rak3"] = f_r
    return d
