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
    elif var in ("MJ", "MJP"):                           # MJP (T154): MJ ile aynı özellikler; sıraya özgü δ harness içinde (PLASE)                                    # marjlı Elo + ortak (at+jokey+antrenör) Elo; f_jel, f_tel (T32)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
    elif var in ("MJK", "MJK2"):                         # MJ + kapı ≤1300 (T35)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import kapi13; d = kapi13.ekle(d, var == "MJK2")
    elif var in ("MJV", "MJVP", "MJV2"):                                   # MJ + video özellikleri (T41)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import os as _os
        if var == "MJVP": _os.environ["PLACEBO"] = "1"
        import video_ozellik; d = video_ozellik.ekle(d)
    elif var in ("MJG", "MJW"):                          # MJ + gün içi kapı eğilimi (T44) / piyasa-ağırlığı etkileşimleri (T45)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import gun_ici; d = gun_ici.gi(d) if var == "MJG" else gun_ici.lpk(d)
    elif var in ("MJB", "MJB2"):                         # MJ + jokey–at aşinalığı (T36)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import jokey_asinalik; d = jokey_asinalik.ekle(d, var == "MJB2")
    elif var == "MJH":                                   # MJ + doğrudan karşılaşma (T70)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import h2h_ozellik; d = h2h_ozellik.ekle(d)
    elif var == "MJS":                                   # MJ + koşu cinsi grubuna özgü at Elo'su (T79)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import cins_elo; d = cins_elo.ekle(d, _elo)
    elif var == "MJY":                                   # MJ + soy–pist (T81)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import soy_pist; d = soy_pist.ekle(d)
    elif var == "MJZ":                                   # MJ + anne hattı (T83)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import soy_anne, soy_pist, soy_mesafe; d = soy_pist.ekle(soy_mesafe.ekle(soy_anne.ekle(d)))
    elif var == "MJC":                                   # MJ + jokey/antrenör hücre etkileri (T71)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import hucre_ozellik; d = hucre_ozellik.ekle(d)
    elif var == "MJM":                                   # MJ + soy–mesafe (T38)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import soy_mesafe; d = soy_mesafe.ekle(d)
    elif var in ("MJOV", "MJT9", "MJSY", "MJSYG"):                  # MJ + T142 olay / T149 düzeltilmiş şerit / T146 soy-yaş (T152)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import t152_ozellik; d = t152_ozellik.ekle(d, {"MJOV": "OV", "MJT9": "V2", "MJSY": "SY", "MJSYG": "SYG"}[var])
    elif var == "MJPK":                                  # T155: MJ + OV + V2 + SYG (T152 kodu; her grup ayrı hesaplanır, sütunlar aktarılır) + δ yapısı (harness)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import t152_ozellik
        for g in ("OV", "V2", "SYG"):
            x = t152_ozellik.ekle(d, g); assert len(x) == len(d) and (x.no.values == d.no.values).all() and (x.tarih.values == d.tarih.values).all(), g
            for c in t152_ozellik.FEAT[g]: d[c] = x[c].values
    elif var in ("MJDE", "MJDE1", "MJDEE", "MJFD"):        # MJ + startta kalma / fedai (T151)
        e, r, _ = _elo(d, at, "sure"); d["f_elo_m"] = e; d["f_rak3_m"] = r
        d["f_jel"], d["f_tel"] = _ortak(d)
        import t151_ozellik; d = t151_ozellik.ekle(d, "FD" if var == "MJFD" else "DE")
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
FEAT = {"MJPK": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "ov_gain", "ov_fin", "ov_tot", "ov_flop", "ov_unl", "ov_var", "v2_lead_frac", "v2_top3_frac", "v2_mean_rank", "v2_early_rank", "v2_late_rank", "v2_vol", "v2_fade", "v2_lead_lost", "v2_var", "e_fm", "e_ff", "e_br", "e_ow", "e_bmb", "e_bpist", "age_g", "age_g3", "age_gf"], "MJP": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel"], "MJOV": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "ov_gain", "ov_fin", "ov_tot", "ov_flop", "ov_unl", "ov_var"], "MJT9": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "v2_lead_frac", "v2_top3_frac", "v2_mean_rank", "v2_early_rank", "v2_late_rank", "v2_vol", "v2_fade", "v2_lead_lost", "v2_var"], "MJSYG": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "e_fm", "e_ff", "e_br", "e_ow", "e_bmb", "e_bpist", "age_g", "age_g3", "age_gf"], "MJSY": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "e_fm", "e_ff", "e_br", "e_ow", "e_bmb", "e_bpist", "age_g", "age_g3", "age_gf"], "MJDE": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_de1", "f_deE"], "MJDE1": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_de1"], "MJDEE": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_deE"], "MJFD": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_fd1", "f_fdE", "f_fdP"], "MJZ": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_an", "f_ab", "f_abp", "f_abm", "f_sp", "f_spd", "f_sm", "f_sd"], "MJY": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_sp", "f_spd"], "MJS": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_elo_s", "f_ns"], "MJC": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_jp", "f_jh", "f_tp"], "MJH": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_h2h_s", "f_h2h_m", "f_h2h_n"], "MJV2": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_v1", "f_v2", "f_v3", "f_v4", "f_v5", "f_v6", "f_v7", "f_v8"], "MJVP": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_v1", "f_v2", "f_v3", "f_v4", "f_v5"], "MJV": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_v1", "f_v2", "f_v3", "f_v4", "f_v5"], "MJG": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_gi"], "MJW": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_lpk", "f_lpb", "f_lpkm", "f_lpum"], "C": ["f_elo_c", "f_nc"], "M": ["f_elo_m", "f_rak3_m"], "MD": ["f_elo_m", "f_rak3_m", "f_db_ekle", "f_db_cikar"], "MJ": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel"], "MJM": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_sm", "f_sd"], "MJB": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_jn", "f_j1"], "MJB2": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_jn", "f_j1", "f_jat"], "MJK": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_k13"], "MJK2": ["f_elo_m", "f_rak3_m", "f_jel", "f_tel", "f_k13", "f_kh"], "MS": ["f_elo_m", "f_rak3_m", "f_sf", "f_sf3"], "ME": ["f_elo_m", "f_rak3_m", "f_ek_ekle", "f_ek_cikar", "f_ek_ilk"]}
