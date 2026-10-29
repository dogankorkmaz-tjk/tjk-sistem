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
def _ortak(d, KH=0.6, KJ=0.1, KT=0.1):
    """Güç = r_at + r_jokey + r_antrenör (marjlı skor); hepsi aynı artıkla güncellenir. Döner: jokey ve antrenör puanı − alan ortalaması (günün başındaki puanlar)."""
    rid = d.groupby(["tarih", "hipodrom", "kosu"]).ngroup().values; tar = d.tarih.astype(str).values
    sr0 = pd.to_numeric(d.sira, errors="coerce").fillna(0).values
    mes = d.mesafe.values.astype(float) if "mesafe" in d else np.full(len(d), np.nan)
    rs = d.rel_sure.values.astype(float) if "rel_sure" in d else np.full(len(d), np.nan)
    wt = d.groupby(["tarih", "hipodrom", "kosu"]).derece_sn.transform("min").values.astype(float) if "derece_sn" in d else np.full(len(d), np.nan)
    rel = np.where(np.isnan(mes), rs / wt * 60.0, rs / mes * 1000.0)
    at = d["at"].astype(str).values; jk = d["jokey"].astype(str).values; an = d["antrenor"].astype(str).values
    RH, RJ, RT = {}, {}, {}; fj = np.zeros(len(d)); ft = np.zeros(len(d))
    gun = pd.Series(np.arange(len(d))).groupby(tar).apply(lambda x: (x.min(), x.max() + 1))
    for t, (i0, i1) in gun.items():
        r_ = rid[i0:i1]; bas = np.r_[0, np.nonzero(np.diff(r_))[0] + 1, len(r_)]; kos = [list(range(i0 + x, i0 + y)) for x, y in zip(bas[:-1], bas[1:])]; upd = []
        for idx in kos:
            h = np.array([RH.get(at[i], 0.0) for i in idx]); j = np.array([RJ.get(jk[i], 0.0) for i in idx]); tt = np.array([RT.get(an[i], 0.0) for i in idx])
            fj[idx] = j - j.mean(); ft[idx] = tt - tt.mean(); upd.append((idx, h, j, tt))
        for idx, h, j, tt in upd:
            ok = [q for q, i in enumerate(idx) if sr0[i] > 0]; n = len(ok)
            if n < 3: continue
            st = (h + j + tt)[ok]; sr = np.array([sr0[idx[q]] for q in ok]); tm = np.array([rel[idx[q]] for q in ok])
            E = 1 / (1 + np.exp(-(st[:, None] - st[None, :]))); np.fill_diagonal(E, 0)
            if np.isfinite(tm).all(): S = 1 / (1 + np.exp(-(tm[None, :] - tm[:, None]) / TAU))
            else: S = (sr[None, :] > sr[:, None]).astype(float) + 0.5 * (sr[None, :] == sr[:, None])
            np.fill_diagonal(S, 0); dl = (S.sum(1) - E.sum(1)) / (n - 1)
            for qq, q in enumerate(ok):
                i = idx[q]; RH[at[i]] = RH.get(at[i], 0.0) + KH * dl[qq]; RJ[jk[i]] = RJ.get(jk[i], 0.0) + KJ * dl[qq]; RT[an[i]] = RT.get(an[i], 0.0) + KT * dl[qq]
    return fj, ft
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
    elif var == "MD":                                    # marjlı Elo + dil bağı (DB) eklendi/çıkarıldı (T33)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        T = pd.read_pickle("/tmp/claude-0/ekip.pkl").drop_duplicates(["tarih", "hipodrom", "kosu", "no"])
        d = d.merge(T, on=["tarih", "hipodrom", "kosu", "no"], how="left"); d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
        hist = {}; a_ = np.zeros(len(d)); c_ = np.zeros(len(d))
        for i, (a, e) in enumerate(zip(d["at"].astype(str).values, d.ekip.values)):
            if not isinstance(e, str): continue
            db = "DB" in e.split()
            if a in hist: a_[i] = float(db and not hist[a]); c_[i] = float(hist[a] and not db)
            hist[a] = db
        d["f_db_ekle"] = a_; d["f_db_cikar"] = c_
    elif var == "MJ":                                    # marjlı Elo + ortak (at+jokey+antrenör) Elo; f_jel, f_tel (T32)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
    elif var in ("MJK", "MJK2"):                         # MJ + kapı ≤1300 (T35)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import kapi13; d = kapi13.ekle(d, var == "MJK2")
    elif var == "MJV":                                   # MJ + video özellikleri (T41)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import video_ozellik; d = video_ozellik.ekle(d)
    elif var in ("MJG", "MJW"):                          # MJ + gün içi kapı eğilimi (T44) / piyasa-ağırlığı etkileşimleri (T45)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import gun_ici; d = gun_ici.gi(d) if var == "MJG" else gun_ici.lpk(d)
    elif var in ("MJB", "MJB2"):                         # MJ + jokey–at aşinalığı (T36)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import jokey_asinalik; d = jokey_asinalik.ekle(d, var == "MJB2")
    elif var == "MJM":                                   # MJ + soy–mesafe (T38)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import soy_mesafe; d = soy_mesafe.ekle(d)
    elif var == "MS":                                    # marjlı Elo + sınıf değişimi (T30)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        T = pd.read_pickle("/tmp/claude-0/sinifp.pkl"); T["dt"] = pd.to_datetime(T.tarih)
        gm = T.groupby("dt").prize1.median().sort_index(); med = {}
        for t_ in gm.index:
            w = T[(T.dt < t_) & (T.dt >= t_ - pd.Timedelta(days=60))].prize1
            med[t_] = w.median() if len(w) >= 50 else T[T.dt.dt.to_period("M") == t_.to_period("M")].prize1.median()
        T["sn"] = np.log(T.prize1 / T.dt.map(med)).clip(-2, 2)
        d = d.merge(T[["tarih", "hipodrom", "kosu", "sn"]], on=["tarih", "hipodrom", "kosu"], how="left"); d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
        hist = collections.defaultdict(list); f1 = np.zeros(len(d)); f3 = np.zeros(len(d)); gun = d.tarih.astype(str).values; atn = d["at"].astype(str).values; sn = d.sn.values
        pend = []; cur = None
        for i in range(len(d)):
            if gun[i] != cur:
                for a_, v_ in pend: hist[a_].append(v_)
                pend = []; cur = gun[i]
            if np.isfinite(sn[i]):
                h = hist[atn[i]]
                if h: f1[i] = np.clip(sn[i] - h[-1], -2, 2); f3[i] = np.clip(sn[i] - np.mean(h[-3:]), -2, 2)
                pend.append((atn[i], sn[i]))
        d["f_sf"] = f1; d["f_sf3"] = f3
    return d
FEAT = {"MJV": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_v1", "f_v2", "f_v3", "f_v4", "f_v5"], "MJG": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_gi"], "MJW": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_lpk", "f_lpb", "f_lpkm", "f_lpum"], "C": ["f_elo_c", "f_nc"], "M": ["f_elo_m", "f_rak3_m"], "MD": ["f_elo_m", "f_rak3_m", "f_db_ekle", "f_db_cikar"], "MJ": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel"], "MJM": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_sm", "f_sd"], "MJB": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_jn", "f_j1"], "MJB2": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_jn", "f_j1", "f_jat"], "MJK": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_k13"], "MJK2": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_k13", "f_kh"], "MS": ["f_elo_m", "f_rak3_m", "f_sf", "f_sf3"], "ME": ["f_elo_m", "f_rak3_m", "f_ek_ekle", "f_ek_cikar", "f_ek_ilk"]}
