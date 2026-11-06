"""T152 özellik grupları (ön kayıt: hipotez_defteri 2026-11-06 T152). T142/T146/T149'un özellikleri, T150 resmi tabanına (harness, VAR=MJ) taşındı.
Hepsi yalnız ÖNCEKİ koşulardan (at bazında shift(1)); koşu içinde ortalamadan sapma olarak DEĞİL, T142/T149'daki gibi ham (T146 koşu içi merkezli).
OV (T142, video özeti; data/video_seyir 'ozet', okuyucu=rakam1): son 3 koşu ortalaması ov_gain (orta−geç), ov_fin (geç−son), ov_tot (erken−son),
    ov_flop (son−orta ≥3), ov_unl ((orta−geç ≥2) ve son ≥ geç), ov_var (geçmişte videolu koşu var mı).
V2 (T149 DÜZELTİLMİŞ: şeritte görünmeyen at = (kutu+1+n)/2, T41/MJV ile aynı; T149'da 6 veriliyordu): son 3 koşu ortalaması lead_frac, top3_frac,
    mean_rank, early_rank, late_rank (sıralar alan büyüklüğüyle (n−1)'e bölünür), vol, fade (erken ≤2 ve bitiş ≥4), lead_lost; v2_var.
SY (T146, atyarisi arşivi): anne-babası, baba-babası, yetiştirici, sahip, baba×mesafe bandı, baba×pist hedef kodlaması (büzme 50, yalnız önceki günler),
    tam yaş (doğum tarihinden), 3 yaş ve altı için tam yaş ve yaş kesri; koşu içi merkezlenir. Satış bedeli (kapsam %1,8) ALINMADI."""
import glob, gzip, json, os
import numpy as np, pandas as pd

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def _video():
    S = []
    for f in glob.glob(os.path.join(KOK, "video_seyir", "20*.json")):
        b = os.path.basename(f)[:-5].split("_")
        if len(b) != 3: continue
        try: j = json.load(open(f))
        except Exception: continue
        if j.get("okuyucu") != "rakam1": continue
        nums = [int(x) for x in j.get("numaralar") or []]; n = len(nums)
        oz = j.get("ozet") or {}
        z = [x["sira"] for x in j.get("zaman") or [] if x.get("sira")]
        kapi = list(j.get("numaralar") or [])[:j.get("kutu", 10)]
        while z and z[0] == kapi: z.pop(0)
        L = len(z); k = j.get("kutu", 10); arka = (k + 1 + n) / 2.0
        for no in nums:
            o = oz.get(str(no)) or {}
            row = [b[0], b[1], int(b[2]), no, o.get("erken"), o.get("orta"), o.get("gec"), o.get("son")]
            if L >= 15 and n >= 2:
                r = np.array([(fr.index(no) + 1) if no in fr else arka for fr in z], float); a_, c_ = L // 3, 2 * L // 3
                row += [(r == 1).mean(), (r <= 3).mean(), (r.mean() - 1) / (n - 1), (r[:a_].mean() - 1) / (n - 1), (r[c_:].mean() - 1) / (n - 1),
                        np.abs(np.diff(r)).mean() / (n - 1), float((r[c_ - L // 3:] == 1).any()), r[:a_].mean()]
            else:
                row += [np.nan] * 8
            S.append(row)
    return pd.DataFrame(S, columns=["tarih", "hipodrom", "kosu", "no", "erken", "orta", "gec", "son", "lead_frac", "top3_frac", "mean_rank", "early_rank",
                                    "late_rank", "vol", "led_late", "early_abs"]).drop_duplicates(["tarih", "hipodrom", "kosu", "no"])


def _onceki3(d, cols, out):
    d = d.sort_values(["at", "tarih", "kosu"]); g = d.groupby("at", sort=False)
    for c, n in zip(cols, out):
        d[n] = g[c].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    return d


def ekle(d, grup):
    d = d.copy(); d["_i"] = np.arange(len(d))
    if grup in ("OV", "V2"):
        V = _video(); d = d.merge(V, on=["tarih", "hipodrom", "kosu", "no"], how="left")
        sira = pd.to_numeric(d.sira, errors="coerce")
        if grup == "OV":
            d["_g"] = d.orta - d.gec; d["_f"] = d.gec - d.son; d["_t"] = d.erken - d.son
            d["_flop"] = np.where(d.orta.notna(), ((d.son - d.orta) >= 3).astype(float), np.nan)
            d["_unl"] = np.where(d.orta.notna(), (((d.orta - d.gec) >= 2) & (d.son >= d.gec)).astype(float), np.nan)
            out = ["ov_gain", "ov_fin", "ov_tot", "ov_flop", "ov_unl"]; d = _onceki3(d, ["_g", "_f", "_t", "_flop", "_unl"], out)
            d["ov_var"] = d.ov_gain.notna().astype(float)
        else:
            d["fade"] = np.where(d.early_abs.notna(), ((d.early_abs <= 2) & (sira >= 4)).astype(float), np.nan)
            d["lead_lost"] = np.where(d.early_abs.notna(), ((d.led_late == 1) & (sira >= 3)).astype(float), np.nan)
            src = ["lead_frac", "top3_frac", "mean_rank", "early_rank", "late_rank", "vol", "fade", "lead_lost"]
            out = ["v2_" + c for c in src]; d = _onceki3(d, src, out); d["v2_var"] = d.v2_lead_frac.notna().astype(float)
        for n in out: d[n] = d[n].fillna(0.0)
    elif grup in ("SY", "SYG"):          # SYG (T152 sızıntı kontrolü): sahip = YARIŞ GÜNÜ programındaki sahip (d.sahip); SY arşivin (geriye dönük çekilmişse güncel) sahibini kullanır
        A = pd.read_pickle("/tmp/claude-0/ay_oz.pkl").drop_duplicates(["tarih", "hipodrom", "kosu", "no"])
        A["kosu"] = A.kosu.astype(int); A["no"] = A.no.astype(int)
        d = d.merge(A[["tarih", "hipodrom", "kosu", "no", "baba", "annebaba", "babababa", "yetistirici", "sahip", "dogum"]].rename(columns={"baba": "baba_a", "sahip": "sahip_a"}),
                    on=["tarih", "hipodrom", "kosu", "no"], how="left")
        d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
        n_at = d.groupby(["tarih", "hipodrom", "kosu"]).no.transform("count")
        d["res"] = pd.to_numeric(d.kazandi, errors="coerce").fillna(0) - 1.0 / n_at
        mes = pd.to_numeric(d.mesafe, errors="coerce"); d["mb"] = pd.cut(mes, [0, 1399, 1799, 2199, 9999], labels=False).astype("float")
        d["yz"] = np.where(d.pist.astype(str).str.lower().str.contains("çim|cim"), "c", "k")
        d["k_baba_mb"] = np.where(d.baba_a.notna(), d.baba_a.astype(str) + "|" + d.mb.astype(str), None)
        d["k_baba_pist"] = np.where(d.baba_a.notna(), d.baba_a.astype(str) + "|" + d.yz, None)
        def enc(col, shrink=50.0):
            k = d[col].where(d[col].notna(), None)
            g = d.assign(_k=k).dropna(subset=["_k"]).groupby(["_k", "tarih"]).res.agg(["sum", "count"]).reset_index().sort_values(["_k", "tarih"])
            g["cs"] = g.groupby("_k")["sum"].cumsum() - g["sum"]; g["cn"] = g.groupby("_k")["count"].cumsum() - g["count"]; g["v"] = g.cs / (g.cn + shrink)
            return d[["tarih"]].assign(_k=k).merge(g[["_k", "tarih", "v"]], on=["_k", "tarih"], how="left")["v"].fillna(0.0).values
        S = []
        for col, name in (("annebaba", "e_fm"), ("babababa", "e_ff"), ("yetistirici", "e_br"), ("sahip_a", "e_ow"), ("k_baba_mb", "e_bmb"), ("k_baba_pist", "e_bpist")):
            d[name] = enc("sahip" if (grup == "SYG" and col == "sahip_a") else col); S.append(name)
        yr = (pd.to_datetime(d.tarih) - pd.to_datetime(d.dogum, unit="s")).dt.days / 365.25; yas = pd.to_numeric(d.yas, errors="coerce")
        d["age_g"] = yr.fillna(yr.median()); d["age_g3"] = d.age_g * (yas <= 3).astype(float); d["age_gf"] = (d.age_g - d.age_g.round()) * (yas <= 3).astype(float)
        S += ["age_g", "age_g3", "age_gf"]
        key = [d.tarih, d.hipodrom, d.kosu]
        for c in S: d[c] = d[c] - d.groupby(key)[c].transform("mean")
    else:
        raise ValueError(grup)
    return d.sort_values("_i").drop(columns=["_i"]).reset_index(drop=True)


FEAT = {"OV": ["ov_gain", "ov_fin", "ov_tot", "ov_flop", "ov_unl", "ov_var"],
        "V2": ["v2_lead_frac", "v2_top3_frac", "v2_mean_rank", "v2_early_rank", "v2_late_rank", "v2_vol", "v2_fade", "v2_lead_lost", "v2_var"],
        "SYG": ["e_fm", "e_ff", "e_br", "e_ow", "e_bmb", "e_bpist", "age_g", "age_g3", "age_gf"],
        "SY": ["e_fm", "e_ff", "e_br", "e_ow", "e_bmb", "e_bpist", "age_g", "age_g3", "age_gf"]}
