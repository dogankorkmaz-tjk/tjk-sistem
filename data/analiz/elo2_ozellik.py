"""Elo varyantları (ön kayıt: hipotez_defteri 2026-10-28 02:40).
 hucre: (at, pist, mesafe bandı) hücresine özgü Elo; f_elo_c (hücre puanı − alan ortalaması), f_nc (hücre deneyimi, min(n,5)/5).
 marj: sıra yerine bitiş süresi farkıyla Elo (S_ij = σ((rel_j − rel_i)/TAU), rel = saniye/km geride); f_elo_m, f_rak3_m (rakiplerin ort. marjlı puanı, son 3 koşu).
Yalnız önceki günlerden; gün içi tüm koşular günün başındaki puanlarla."""
import collections, numpy as np, pandas as pd
TAU = 0.4; KELO = 0.6
def _band(m):
    return np.where(np.isnan(m), 1, np.digitize(m, [1300, 1700, 2100]))
def _elo(d, keys, mode):
    rid = d.groupby(["tarih", "hipodrom", "kosu"]).ngroup().values; tar = d.tarih.astype(str).values
    sr0 = pd.to_numeric(d.sira, errors="coerce").fillna(0).values
    mes = d.mesafe.values.astype(float) if "mesafe" in d else np.full(len(d), np.nan)
    rel = (d.rel_sure.values.astype(float) / np.where(np.isnan(mes), 1400.0, mes) * 1000.0) if "rel_sure" in d else np.full(len(d), np.nan)
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
def ekle(d, var):
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    at = d["at"].astype(str).values
    if var == "C":
        pist = d.pist.astype(str).values if "pist" in d else np.array(["?"] * len(d)); mes = d.mesafe.values.astype(float) if "mesafe" in d else np.full(len(d), np.nan)
        keys = np.array([f"{a}|{p}|{b}" for a, p, b in zip(at, pist, _band(mes))])
        e, _, n = _elo(d, keys, "sira"); d["f_elo_c"] = e; d["f_nc"] = n
    elif var == "M":
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
    elif var == "ME":                                    # marjlı Elo + ekipman değişimi (T29)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        T = pd.read_pickle("/tmp/claude-0/ekip.pkl").drop_duplicates(["tarih", "hipodrom", "kosu", "no"])
        d = d.merge(T, on=["tarih", "hipodrom", "kosu", "no"], how="left"); d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
        ek = d.ekip.values; hist = {}; seen = collections.defaultdict(set); a_ = np.zeros(len(d)); c_ = np.zeros(len(d)); i_ = np.zeros(len(d))
        for i, (a, e) in enumerate(zip(d["at"].astype(str).values, ek)):
            if not isinstance(e, str): continue
            S = set(e.split()); P = hist.get(a)
            if P is not None:
                a_[i] = min(len(S - P), 3); c_[i] = min(len(P - S), 3); i_[i] = float(len(S - seen[a]) > 0 and len(seen[a]) > 0)
            hist[a] = S; seen[a] |= S
        d["f_ek_ekle"] = a_; d["f_ek_cikar"] = c_; d["f_ek_ilk"] = i_
    return d
FEAT = {"C": ["f_elo_c", "f_nc"], "M": ["f_elo_m", "f_rak3_m"], "ME": ["f_elo_m", "f_rak3_m", "f_ek_ekle", "f_ek_cikar", "f_ek_ilk"]}
