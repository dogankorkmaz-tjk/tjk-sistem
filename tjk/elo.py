"""Rakip gücü (Elo) özellikleri (T27/T28, 28 Ekim 2026). Ön kayıt: data/analiz/hipotez_defteri.md.
f_elo, f_rak3: sıra tabanlı ikili Elo (at puanı − alan ortalaması; son 3 koşudaki rakiplerin ortalama puanı).
f_elo_m, f_rak3_m: aynı, ama S_ij = σ((rel_j − rel_i)/TAU), rel = saniye/km geride (süre yoksa sıra). Yalnız önceki günlerden."""
import collections, numpy as np, pandas as pd
TAU = 0.4; KELO = 0.6
EXTRA_FEAT = ["f_elo", "f_rak3", "f_elo_m", "f_rak3_m"]
def _elo(d, keys, mode):
    rid = d.groupby(["tarih", "hipodrom", "kosu"]).ngroup().values; tar = d.tarih.astype(str).values
    sr0 = pd.to_numeric(d.sira, errors="coerce").fillna(0).values
    mes = d.mesafe.values.astype(float) if "mesafe" in d else np.full(len(d), np.nan)
    rs = d.rel_sure.values.astype(float) if "rel_sure" in d else np.full(len(d), np.nan)
    wt = d.groupby(["tarih", "hipodrom", "kosu"]).derece_sn.transform("min").values.astype(float) if "derece_sn" in d else np.full(len(d), np.nan)
    # saniye/km geride; mesafe yoksa kazananın süresine oranlanır (≈ km başına): rel/min_derece*60
    rel = np.where(np.isnan(mes), rs / wt * 60.0, rs / mes * 1000.0)
    R = {}; HIST = collections.defaultdict(list); N = collections.defaultdict(int)
    f_e = np.zeros(len(d)); f_r = np.zeros(len(d)); f_n = np.zeros(len(d))
    gun = pd.Series(np.arange(len(d))).groupby(tar).apply(lambda x: (x.min(), x.max() + 1))
    for t, (i0, i1) in gun.items():
        r_ = rid[i0:i1]; bas = np.r_[0, np.nonzero(np.diff(r_))[0] + 1, len(r_)]; kos = [list(range(i0 + x, i0 + y)) for x, y in zip(bas[:-1], bas[1:])]; upd = []
        for idx in kos:
            rt = np.array([R.get(keys[i], 0.0) for i in idx]); m = rt.mean()
            for q, i in enumerate(idx):
                f_e[i] = rt[q] - m; h = HIST[keys[i]][-3:]; f_r[i] = np.mean(h) if h else 0.0; f_n[i] = min(N[keys[i]], 5) / 5.0
            upd.append((idx, rt))
        for idx, rt in upd:
            ok = [q for q, i in enumerate(idx) if sr0[i] > 0]; n = len(ok)
            if n < 3: continue
            rr = rt[ok]; sr = np.array([sr0[idx[q]] for q in ok]); tm = np.array([rel[idx[q]] for q in ok])
            E = 1 / (1 + np.exp(-(rr[:, None] - rr[None, :]))); np.fill_diagonal(E, 0)
            if mode == "sure" and np.isfinite(tm).all():
                S = 1 / (1 + np.exp(-(tm[None, :] - tm[:, None]) / TAU))
            else:
                S = (sr[None, :] > sr[:, None]).astype(float) + 0.5 * (sr[None, :] == sr[:, None])
            np.fill_diagonal(S, 0); dl = KELO * (S.sum(1) - E.sum(1)) / (n - 1)
            for qq, q in enumerate(ok):
                i = idx[q]; HIST[keys[i]].append((rr.sum() - rr[qq]) / (n - 1)); R[keys[i]] = R.get(keys[i], 0.0) + dl[qq]; N[keys[i]] += 1
    return f_e, f_r, f_n

def ekle(d):
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    at = d["at"].astype(str).values
    e, r, _ = _elo(d, at, "sira"); d["f_elo"] = e; d["f_rak3"] = r
    e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
    return d
