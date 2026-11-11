"""T201: TAM piyasasız model (elenen tüm özellikler geri eklenmiş) AGF'ye karşı. Ön kayıt: hipotez_defteri T201. Actions: t201.yml.
Betik sonuca bakılarak ayarlanmaz. Önce data/analiz/t201_hazirla.py çalışmalı (/tmp/claude-0 tabloları).
Ortam: T201_SADECE_OZ=1 → yalnız özellik üretimi + kapsama raporu (sonuç ölçülmez)."""
import os, sys, json, glob, time, collections, importlib
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [KOK, os.path.join(KOK, "data", "analiz")]
_ns = {"__file__": os.path.join(KOK, "data", "analiz", "t192.py")}
exec(compile(open(os.path.join(KOK, "data", "analiz", "t192.py")).read().split("feat = M[")[0], "t192head", "exec"), _ns)
d, M, O, _fit, skorla, EK, LPEK, np, pd = [_ns[k] for k in ("d", "M", "O", "_fit", "skorla", "EK", "LPEK", "np", "pd")]
from scipy.optimize import minimize
from tjk import elo as EL
T0 = time.time()
def log(*a): print(f"[{round(time.time() - T0)}s]", *a, flush=True)
d = EL.ekle(d)
K4 = ["tarih", "hipodrom", "kosu", "no"]
d = d.sort_values(K4).reset_index(drop=True)
BASE = [c for c in dict.fromkeys(M["feat"] + EK + EL.EXTRA_FEAT) if c not in LPEK and c != "f_lp2"]
GRUP, KAPSAM, DISARIDA = {}, {}, {}

def al(ad, fn, cols, video=False):
    """fn(d kopyası) -> DataFrame; cols sütunları K4 ile ana tabloya eklenir. Hata → grup dışarıda (raporlanır)."""
    global d
    t = time.time()
    try:
        x = fn(d.copy())
        x["tarih"] = x.tarih.astype(str)
        x = x[K4 + cols].drop_duplicates(K4)
        d = d.drop(columns=[c for c in cols if c in d]).merge(x, on=K4, how="left")
        for c in cols: d[c] = pd.to_numeric(d[c], errors="coerce").astype(float)
        for c in cols: d[c] = d[c].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        nz = (d[cols].abs() > 1e-12).any(axis=1)
        KAPSAM[ad] = {"sifir_olmayan": round(float(nz.mean()), 3), "2025+": round(float(nz[d.tarih >= "2025"].mean()), 3)}
        GRUP[ad] = {"cols": cols, "video": video}
        log("OK", ad, cols, "kapsam", KAPSAM[ad], f"{round(time.time() - t)}sn")
    except Exception as e:
        DISARIDA[ad] = f"{type(e).__name__}: {str(e)[:200]}"; log("DIŞARIDA", ad, DISARIDA[ad])
    d = d.sort_values(K4).reset_index(drop=True)

m = lambda name: importlib.import_module(name)
E2 = m("elo2_ozellik")
# --- program/geçmiş tabanlı gruplar (önceki testlerin kodu, değiştirilmeden çağrılır)
al("jokey_at_asinalik_T36", lambda x: m("jokey_asinalik").ekle(x, False), ["f_jn", "f_j1"])
al("dogrudan_karsilasma_T70", lambda x: m("h2h_ozellik").ekle(x), ["f_h2h_s", "f_h2h_m", "f_h2h_n"])
al("soy_baba_pist_T81", lambda x: m("soy_pist").ekle(x), ["f_sp", "f_spd"])
al("soy_baba_mesafe_T38", lambda x: m("soy_mesafe").ekle(x), ["f_sm", "f_sd"])
al("soy_anne_T83", lambda x: m("soy_anne").ekle(x), ["f_an", "f_ab", "f_abp", "f_abm"])
al("soy_yas_yetistirici_T146", lambda x: m("t152_ozellik").ekle(x, "SYG"), m("t152_ozellik").FEAT["SYG"])
al("jokey_antrenor_hucre_T71", lambda x: m("hucre_ozellik").ekle(x), ["f_jp", "f_jh", "f_tp"])
al("kapi_1300_T35", lambda x: m("kapi13").ekle(x, True), ["f_k13", "f_kh"])
al("kapi_mesafe_bandi", lambda x: m("kapi_ozellik").uygula(x), ["f_kk", "f_ko", "f_ku"])
al("mesafe_pist_ek", lambda x: m("mesafe_pist_ozellik").uygula(x, True), ["f_ps", "f_dpp", "f_pchg", "f_dup", "f_ddn"])
al("cins_elo_T79", lambda x: m("cins_elo").ekle(x, E2._elo), ["f_elo_s", "f_ns"])
al("pist_mesafe_hucre_elo", lambda x: E2.ekle(x, "C"), ["f_elo_c", "f_nc"])
al("ekipman_degisim_T29", lambda x: E2.ekle(x, "ME"), ["f_ek_ekle", "f_ek_cikar", "f_ek_ilk"])
al("dil_bagi_T33", lambda x: E2.ekle(x, "MD"), ["f_db_ekle", "f_db_cikar"])
al("sinif_degisim_T30", lambda x: E2.ekle(x, "MS"), ["f_sf", "f_sf3"])

def _kfz(x):
    x = x.copy(); x["rid"] = x.groupby(O.K).ngroup()
    hv = x.hnd_rel.notna() & x.groupby("rid").hnd_rel.transform(lambda s: s.notna().all())
    x["kfz"] = (x.f_kilo - 0.5 * x.hnd_rel).where(hv, 0.0).fillna(0.0); x["kfz_pos"] = x.kfz.clip(lower=0); return x
al("fazla_kilo", _kfz, ["kfz", "kfz_pos"])

def _zorluk(x):            # T191 fZ (aynı tanım)
    x = x.sort_values(K4).reset_index(drop=True); x["rid"] = x.groupby(O.K).ngroup(); r = x.rel_sure.astype(float)
    k = x.tarih + "|" + x.hipodrom.astype(str) + "|" + x.pist.astype(str)
    sm = r.groupby(k).transform("sum"); sc = r.groupby(k).transform("count"); g = r - (sm - r.fillna(0)) / (sc - r.notna()).clip(lower=1)
    S = pd.Series(x[x.sira <= 4].groupby("rid").f_fig3.mean().reindex(x.rid).values, index=x.index); S = (S - S.mean()).fillna(0.0)
    v = g + S; t = pd.DataFrame({"at": x["at"].values, "v": v.values})
    s3 = t.groupby("at").v.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean()).fillna(0).clip(-3, 3)
    x["f_fZ"] = s3.values - pd.Series(s3.values).groupby(x.rid.values).transform("mean").values; return x
al("zorluk_figuru_T191", _zorluk, ["f_fZ"])

def _pl(x):                # T195 f_pl (aynı tanım: aylık, genişleyen pencere, PL ilk 4, L2 1,0, yarı ömür 365)
    x = x.sort_values(K4).reset_index(drop=True); x["rid"] = x.groupby(O.K).ngroup()
    hid = pd.factorize(x["at"].astype(str))[0]; H = int(hid.max()) + 1
    sira = pd.to_numeric(x.sira, errors="coerce").fillna(0).values; rk = np.where(sira > 0, sira, 99).astype(int)
    rid = x.rid.values; gun = pd.to_datetime(x.tarih).values.astype("datetime64[D]").astype(int); tarih = x.tarih.astype(str)
    def fit(idx, T, th0):
        r_ = rid[idx]; o = np.argsort(r_, kind="stable"); idx = idx[o]; r_ = r_[o]
        st = np.r_[0, np.nonzero(np.diff(r_))[0] + 1]; n = len(idx); seg = np.repeat(np.arange(len(st)), np.diff(np.r_[st, n]))
        h = hid[idx]; rkk = rk[idx]; w = 0.5 ** ((T - np.maximum.reduceat(gun[idx], st)) / 365.0); stages = []
        for k in range(1, 5):
            win = (rkk == k); ok = (np.add.reduceat(win.astype(int), st) == 1); stages.append((rkk >= k, win & ok[seg], ok))
        def f(th):
            s = th[h]; ll = 0.0; g = np.zeros(n)
            for mem, ws, ok in stages:
                sk = np.where(mem, s, -np.inf); mx = np.maximum.reduceat(sk, st); mx = np.where(np.isfinite(mx), mx, 0.0)
                e = np.exp(sk - mx[seg]); Z = np.add.reduceat(e, st); Zs = np.where(Z > 0, Z, 1.0); va = ok & (Z > 0)
                ll += (w[va] * (np.add.reduceat(np.where(ws, s, 0.0), st)[va] - (np.log(Zs) + mx)[va])).sum(); g += (w * va)[seg] * (ws - e / Zs[seg])
            return -ll + 0.5 * (th @ th), -np.bincount(h, weights=g, minlength=H) + th
        return minimize(f, th0.copy(), jac=True, method="L-BFGS-B", options={"maxiter": 120}).x
    out = np.zeros(len(x)); th = np.zeros(H)
    for a in sorted(tarih.str[:7].unique()):
        tr = np.nonzero((tarih < a + "-01").values)[0]; te = np.nonzero(tarih.str.startswith(a).values)[0]
        if len(tr) < 5000 or len(te) == 0: continue
        th = fit(tr, int(np.datetime64(a + "-01", "D").astype(int)), th); out[te] = th[hid[te]]
    x["f_pl"] = out - pd.Series(out).groupby(x.rid.values).transform("mean").values; return x
al("pl_at_gucu_T195", _pl, ["f_pl"])

def _accurace(x):          # yer kaybı (f_yk, f_maz) ve son bölüm hızı (f_k): atın ≤120 gün önceki son Accurace kaydı
    import re, unicodedata
    A = []
    for f in glob.glob(os.path.join(KOK, "data", "accurace", "*.json")):
        mm = re.match(r"(\d{4}-\d\d-\d\d)_(.+)_(\d+)$", os.path.basename(f)[:-5]); j = json.load(open(f))
        r = [a for a in j.get("atlar", []) if a.get("no") is not None]
        km = [a.get("kosulan_mesafe") for a in r if a.get("kosulan_mesafe")]; hb = [a.get("hiz_bitis") for a in r if isinstance(a.get("hiz_bitis"), (int, float)) and 30 <= a["hiz_bitis"] <= 80]
        if len(r) < 4: continue
        mk = float(np.median(km)) if len(km) >= 4 else None; mb = float(np.median(hb)) if len(hb) >= 4 else None
        for a in r:
            fm = (a["kosulan_mesafe"] - mk) if (mk is not None and a.get("kosulan_mesafe")) else np.nan
            if np.isfinite(fm) and abs(fm) >= 80: fm = np.nan
            k_ = (a["hiz_bitis"] - mb) if (mb is not None and isinstance(a.get("hiz_bitis"), (int, float)) and 30 <= a["hiz_bitis"] <= 80) else np.nan
            A.append((mm.group(1), mm.group(2), int(mm.group(3)), int(a["no"]), fm, k_))
    A = pd.DataFrame(A, columns=["tarih", "hipodrom", "kosu", "no", "fm", "k"])
    asc = lambda s: unicodedata.normalize("NFKD", str(s).replace("İ", "I").replace("ı", "i")).encode("ascii", "ignore").decode().lower().strip()
    A["hipodrom"] = A.hipodrom.map(asc)
    B = x[K4 + ["at", "sira", "p_piyasa"]].copy(); B["prk"] = B.groupby(["tarih", "hipodrom", "kosu"]).p_piyasa.rank(ascending=False, method="first")
    A = A.merge(B, on=K4, how="inner"); A["kotu"] = (A.sira > A.prk).astype(float); A["td"] = pd.to_datetime(A.tarih)
    x = x.copy(); x["td"] = pd.to_datetime(x.tarih); x["_i"] = np.arange(len(x)); xs = x.sort_values("td")
    L = pd.merge_asof(xs[["_i", "td", "at"]], A.sort_values("td")[["at", "td", "fm", "kotu", "k"]].rename(columns={"td": "tdA"}), left_on="td", right_on="tdA", by="at", direction="backward", allow_exact_matches=False)
    L = L.set_index("_i").reindex(x._i); ok = ((L.td - L.tdA).dt.days <= 120).values
    x["f_yk"] = np.where(ok, (L.fm / 10).values, np.nan); x["f_maz"] = np.where(ok, (L.fm * L.kotu / 10).values, np.nan); x["f_k"] = np.where(ok, L.k.values, np.nan); return x
al("accurace_yer_kaybi_son_bolum", _accurace, ["f_yk", "f_maz", "f_k"])

def _zemin(x):             # T147 ıslak pist geçmişi (aynı tanım)
    G = pd.read_pickle("/tmp/claude-0/ay_gun.pkl")
    G["yz"] = G.yuzey.astype(str).str.lower().map(lambda s: "c" if "çim" in s or "cim" in s else ("k" if "kum" in s else None)); G["agirlik"] = pd.to_numeric(G.agirlik, errors="coerce")
    G = G.dropna(subset=["yz"]).drop_duplicates(["tarih", "hipodrom", "yz"])
    x = x.copy(); x["yz"] = np.where(x.pist.astype(str).str.lower().str.contains("çim|cim"), "c", "k")
    x = x.merge(G[["tarih", "hipodrom", "yz", "agirlik"]], on=["tarih", "hipodrom", "yz"], how="left")
    x["wet"] = (x.agirlik >= 1.0).astype(float); x.loc[x.agirlik.isna(), "wet"] = np.nan
    x = x.sort_values(["at", "tarih", "kosu"]).reset_index(drop=True)
    w = x.wet.fillna(0.0).values; kn = x.wet.notna().values; pct = x.pct.values; gk = x.groupby("at", sort=False).ngroup().values
    fw = np.zeros(len(x)); nw = np.zeros(len(x)); cw = cd = sw = sd_ = 0.0; last = -1
    for i in range(len(x)):
        if gk[i] != last: cw = cd = sw = sd_ = 0.0; last = gk[i]
        nw[i] = cw; mw = sw / cw if cw > 0 else np.nan; md = sd_ / cd if cd > 0 else np.nan
        fw[i] = (-(mw - md) * (cw / (cw + 3.0))) if (cw > 0 and cd > 0) else 0.0
        if kn[i] and not np.isnan(pct[i]):
            if w[i] >= 1: cw += 1; sw += pct[i]
            else: cd += 1; sd_ += pct[i]
    x["f_gp"] = fw * np.where(x.wet == 1.0, 1.0, 0.0); x["f_gp_n"] = np.where(x.wet == 1.0, np.minimum(nw, 3) / 3.0, 0.0); return x
al("islak_pist_T147", _zemin, ["f_gp", "f_gp_n"])

def _galop(x):             # galop (idman) son 30 gün: sayı, son galoptan gün, sprint, son/min görece 400, yoğun, yok
    def nrm(s): return str(s or "").upper().translate(str.maketrans("İıŞşĞğÜüÖöÇç", "IISSGGUUOOCC")).replace("İ", "I").strip()
    G = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(KOK, "data", "galop", "*.csv.gz"))])
    G["atn"] = G["at"].map(nrm); G["itd"] = pd.to_datetime(G.it); G["p400"] = pd.to_numeric(G.p400, errors="coerce")
    G["rel"] = (G.p400 - G.groupby(["it", "tur"]).p400.transform("median")).clip(-4, 4); G["yog"] = G.durum.isin(["Çalışarak", "Hafif Çalışarak"]).astype(float); G["spr"] = (G.tur == "Sprint").astype(float)
    gr = {a: g.sort_values("itd") for a, g in G.groupby("atn")}; bas = G.itd.min() + pd.Timedelta(days=30)
    x = x.copy(); F = np.zeros((len(x), 7)); td = pd.to_datetime(x.tarih).values; an = x["at"].map(nrm).values
    for i in range(len(x)):
        t = pd.Timestamp(td[i])
        if t < bas: F[i] = [0, 0, 0, 0, 0, 0, 0]; continue
        g = gr.get(an[i]); y = g[(g.itd < t) & (g.itd >= t - pd.Timedelta(days=30))] if g is not None else None
        if y is None or not len(y): F[i] = [0, 30, 0, 0, 0, 0, 1]; continue
        F[i] = [len(y), (t - y.itd.max()).days, y.spr.sum(), y.rel.iloc[-1] if pd.notna(y.rel.iloc[-1]) else 0.0, y.rel.min() if y.rel.notna().any() else 0.0, y.yog.sum(), 0]
    for j, c in enumerate(["g_n", "g_gun", "g_spr", "g_son", "g_min", "g_yog", "g_yok"]): x[c] = F[:, j]
    return x
al("galop_idman", _galop, ["g_n", "g_gun", "g_spr", "g_son", "g_min", "g_yog", "g_yok"])

def _komiser(x):           # T194 bayrakları: atın ÖNCEKİ koşusunda raporda adı geçti mi
    from tjk import komiser_olay as KO, komiser as KM
    rows = []
    for r in KO.oku_tum(): rows += KO.cikar(r)
    ol = pd.DataFrame(rows); rv = {v: k for k, v in KM.ASCII.items()}; ol["hipodrom"] = ol.hipodrom.map(lambda s: rv.get(s, s))
    ol = ol.drop_duplicates(["tarih", "hipodrom", "kosu", "no", "tur"]); ol["v"] = 1.0
    P = ol.pivot_table(index=["tarih", "hipodrom", "kosu", "no"], columns="tur", values="v", aggfunc="max").reset_index()
    x = x.merge(P, on=K4, how="left"); x = x.sort_values(["at", "tarih", "kosu"]).reset_index(drop=True); bas = ol.tarih.min()
    for c in ("gec_start", "sakat", "kamci_ceza"):
        v = (x[c] if c in x else pd.Series(np.nan, index=x.index)).fillna(0.0)
        x["k_" + c] = v.groupby(x["at"]).shift(1).fillna(0.0).where(x.tarih > bas, 0.0)
    return x
al("komiser_bayraklari_T194", _komiser, ["k_gec_start", "k_sakat", "k_kamci_ceza"])
# --- video/seyir tabanlı gruplar (T41/T149/T151/T152/T162)
al("video_T41", lambda x: m("video_ozellik").ekle(x), ["f_v1", "f_v2", "f_v3", "f_v4", "f_v5", "f_v6", "f_v7", "f_v8"], video=True)
al("video_olay_OV", lambda x: m("t152_ozellik").ekle(x, "OV"), m("t152_ozellik").FEAT["OV"], video=True)
al("video_serit_V2", lambda x: m("t152_ozellik").ekle(x, "V2"), m("t152_ozellik").FEAT["V2"], video=True)
al("video_sessiz_sorun_T162", lambda x: m("t162_ozellik").ekle(x), m("t162_ozellik").FEAT, video=True)
al("start_kalma_T151", lambda x: m("t151_ozellik").ekle(x, "DE"), m("t151_ozellik").FEAT["DE"], video=True)
al("fedai_T151", lambda x: m("t151_ozellik").ekle(x, "FD"), m("t151_ozellik").FEAT["FD"], video=True)
DISARIDA["gun_ici_kapi_T44"] = "BİLEREK: aynı günün önceki koşu sonuçlarını kullanır; altılı kuponu ilk ayaktan önce kurulduğu için sızıntı olur"
DISARIDA["piyasa_etkilesimleri_T45"] = "BİLEREK: bugünün piyasa olasılığını kullanır (piyasasız modele girmez)"
DISARIDA["padok_T143"] = "veri yok (pilot, birkaç gün)"; DISARIDA["kamci_T190"] = "veri yok (elle gözlem, n<30)"
EKLER = [c for g in GRUP.values() for c in g["cols"]]; VID = [c for g in GRUP.values() if g["video"] for c in g["cols"]]
FULL = BASE + [c for c in EKLER if c not in BASE]; NOVID = [c for c in FULL if c not in VID]
log("taban", len(BASE), "tam", len(FULL), "videosuz", len(NOVID), "grup", len(GRUP), "dışarıda", list(DISARIDA))
json.dump({"gruplar": {k: v["cols"] for k, v in GRUP.items()}, "kapsam": KAPSAM, "disarida": DISARIDA, "taban": BASE},
          open(os.path.join(KOK, "data", "analiz", "t201_ozellik.json"), "w"), indent=1, ensure_ascii=False)
# sızıntı denetimi: kazananın özelliği koşu ortalamasından kaç sd uzak (gelecek bilgisi taşıyan özellik çok büyük çıkar)
_r = d.groupby(O.K).ngroup(); _w = d.kazandi == 1; SIZ = {}
for c in FULL:
    v = d[c].astype(float); sd_ = v.std(ddof=0)
    if sd_ > 0: SIZ[c] = round(float(((v - v.groupby(_r).transform("mean"))[_w]).mean() / sd_), 3)
SUPHE = {k: v for k, v in SIZ.items() if abs(v) > 1.0 and k not in BASE}   # eşik 1,0: meşru güçlü özellikler (Elo, hnd) ~0,5; sonuç bilgisi taşıyan özellik çok daha büyük olur
log("sızıntı denetimi |z|>0,5:", SUPHE or "yok", "| en büyük 8:", sorted(SIZ.items(), key=lambda kv: -abs(kv[1]))[:8])
json.dump({"gruplar": {k: v["cols"] for k, v in GRUP.items()}, "kapsam": KAPSAM, "disarida": DISARIDA, "taban": BASE, "sizinti_z": SIZ},
          open(os.path.join(KOK, "data", "analiz", "t201_ozellik.json"), "w"), indent=1, ensure_ascii=False)
if SUPHE: log("UYARI: sızıntı şüphesi olan özellik var; ön kayıt kuralı: bu özellikler modelden ÇIKARILIR ve raporlanır"); FULL = [c for c in FULL if c not in SUPHE]; NOVID = [c for c in NOVID if c not in SUPHE]
if os.environ.get("T201_SADECE_OZ"): sys.exit(0)

# ======================= modeller (hepsi piyasasız: lp=0; çeyreklik ileri-yürüyüş) =======================
A3 = [1.0, 0.80, 0.69]
def fit3(tr, feat, lam=100.0):
    """İlk-3 Plackett-Luce, paylaşımlı ağırlık, sabit sıra üsleri A3, ridge lam. Döner th, mu, sd."""
    tr = tr.sort_values(O.K + ["no"]).reset_index(drop=True); rid = tr.groupby(O.K).ngroup().values
    mu, sd = tr[feat].mean(), tr[feat].std(ddof=0).replace(0, 1.0); X = ((tr[feat] - mu) / sd).values
    st = np.r_[0, np.nonzero(np.diff(rid))[0] + 1]; n = len(tr); seg = np.repeat(np.arange(len(st)), np.diff(np.r_[st, n]))
    sr = pd.to_numeric(tr.sira, errors="coerce").fillna(0).values; rk = np.where(sr > 0, sr, 99)
    stg = []
    for k in range(1, 4):
        win = rk == k; ok = np.add.reduceat(win.astype(int), st) == 1; stg.append((rk >= k, win & ok[seg], ok))
    def f(w):
        s = X @ w; ll = 0.0; g = np.zeros(n)
        for (mem, ws, ok), a in zip(stg, A3):
            z = np.where(mem, a * s, -np.inf); mx = np.maximum.reduceat(z, st); mx = np.where(np.isfinite(mx), mx, 0.0)
            e = np.exp(z - mx[seg]); Z = np.add.reduceat(e, st); Zs = np.where(Z > 0, Z, 1.0); va = (ok & (Z > 0))
            ll += (np.add.reduceat(np.where(ws, a * s, 0.0), st)[va] - (np.log(Zs) + mx)[va]).sum(); g += a * va[seg] * (ws - e / Zs[seg])
        return -ll + 0.5 * lam * (w @ w), -(X.T @ g) + lam * w
    w = minimize(f, np.zeros(X.shape[1]), jac=True, method="L-BFGS-B", options={"maxiter": 300}).x
    return np.r_[0.0, w], mu, sd

KOLLAR = {"P0": BASE, "PF": FULL, "PFV": NOVID}
d["q"] = pd.PeriodIndex(pd.to_datetime(d.tarih), freq="Q").astype(str); parts = []
DUMAN = bool(os.environ.get("T201_DUMAN"))     # yalnız kod denetimi (2 çeyrek, kısaltılmış eğitim); sonuç kullanılmaz
for kq in [q for q in sorted(d.q.unique()) if q >= "2025Q1" and (not DUMAN or q in ("2025Q4", "2026Q3"))]:
    te0 = d[d.q == kq]; tr = d[d.tarih < te0.tarih.min()].assign(lp=0.0)
    if DUMAN: tr = tr[tr.tarih >= str(pd.Timestamp(te0.tarih.min()) - pd.Timedelta(days=200))[:10]]
    te = te0.sort_values(O.K + ["no"]).reset_index(drop=True); te["rid"] = te.groupby(O.K).ngroup(); te["lp"] = 0.0
    for ad, feat in list(KOLLAR.items()) + [("PF3", FULL)]:
        fk = [c for c in feat if tr[c].std(ddof=0) > 0]
        if ad == "PF3": th, mu, sd = fit3(tr, fk, M.get("lam", 100.0))
        else: th, mu, sd, nk = _fit(tr, fk, M.get("lam", 100.0))
        te["p_" + ad] = skorla(te, fk, th, mu, sd)
    parts.append(te[["tarih", "hipodrom", "kosu", "no", "kazandi", "sira", "p_piyasa"] + ["p_" + a for a in ("P0", "PF", "PFV", "PF3")]]); log(kq, len(te))
P = pd.concat(parts, ignore_index=True)
Z = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(KOK, "data", "zengin", "*.csv.gz")))])[["tarih", "hipodrom", "kosu", "no", "agf_son"]]
Z["hipodrom"] = Z.hipodrom.map(lambda s: str(s).translate(O.TR).lower())
P = P.merge(Z, on=K4, how="left"); K3 = ["tarih", "hipodrom", "kosu"]
P = P[P.groupby(K3).agf_son.transform(lambda s: s.notna().all() and s.sum() > 50)].copy()
P["a"] = P.agf_son.clip(lower=0.01); P["a"] = P.a / P.groupby(K3).a.transform("sum")
for c in ("p_P0", "p_PF", "p_PFV", "p_PF3"): P[c] = P[c] / P.groupby(K3)[c].transform("sum")
W = P[(P.kazandi == 1) & (P.groupby(K3).kazandi.transform("sum") == 1)].copy(); W["gun"] = W.tarih; W["yil"] = W.tarih.str[:4]
for c, n in (("a", "AGF"), ("p_piyasa", "kapanis"), ("p_P0", "P0"), ("p_PF", "PF"), ("p_PFV", "PFV"), ("p_PF3", "PF3")): W["l_" + n] = np.log(W[c].clip(lower=1e-9))
log("AGF'li koşu", len(W), "gün", W.gun.nunique(), W.tarih.min(), W.tarih.max())
rng = np.random.default_rng(2010)
def ga(v, g, lo, hi, B=20000):
    s = pd.Series(np.asarray(v)).groupby(np.asarray(g)).agg(["sum", "count"]); a, c = s["sum"].values, s["count"].values; n = len(a)
    i = rng.integers(0, n, (B, n)); mm = a[i].sum(1) / c[i].sum(1); return [float(a.sum() / c.sum()), *map(float, np.percentile(mm, [lo, hi]))]
R = {}
CMP = [("PF", "AGF", True), ("PF", "P0", True), ("P0", "AGF", False), ("PFV", "AGF", False), ("PF3", "AGF", False), ("PF", "PFV", False), ("PF3", "PF", False), ("AGF", "kapanis", False)]
for yil in ("2025", "2026", "tum"):
    X = W if yil == "tum" else W[W.yil == yil]
    for a, b, ana in CMP:
        lo, hi = (0.833, 99.167) if ana else (2.5, 97.5)
        R[f"{yil}_{a}-{b}"] = ga(X["l_" + a] - X["l_" + b], X.gun, lo, hi)
    R[f"{yil}_kayip"] = {n: float(-X["l_" + n].mean()) for n in ("AGF", "kapanis", "P0", "PF", "PFV", "PF3")}; R[f"{yil}_kosu"] = int(len(X))
for k, v in R.items(): log(k, v if not isinstance(v, list) else [round(x, 4) for x in v])

# ======================= altılı kuponu (T200 ile aynı kurucu) =======================
G = {k: g.reset_index(drop=True) for k, g in P.groupby(K3)}
Od = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(KOK, "data", "odeme", "*.csv.gz")))])
Od = Od[Od.tur.str.startswith("6'LI GANYAN")].drop_duplicates(K3)
AL = []
for r in Od.itertuples():
    legs = [G.get((r.tarih, r.hipodrom, k)) for k in range(r.kosu - 5, r.kosu + 1)]
    if any(g is None for g in legs) or any(g.kazandi.sum() < 1 for g in legs): continue
    AL.append({"t": r.tarih, "h": r.hipodrom, "legs": legs, "devir": "DEVİR" in r.tur, "tutar": float(r.tutar)})
def mix(a, p, w):
    l = (1 - w) * np.log(a) + w * np.log(np.maximum(p, 1e-9)); e = np.exp(l - l.max()); return e / e.sum()
GR = np.round(np.arange(0, 1.0001, 0.05), 2)
tr25 = [g for x in AL if x["t"] < "2026" for g in x["legs"]]
wF = float(GR[int(np.argmax([np.mean([np.log(mix(g.a.values, g.p_PF.values, w)[g.kazandi.values == 1].sum() / g.kazandi.sum()) for g in tr25]) for w in GR]))])
log("altılı", len(AL), "| karışım w (2025 fit, PF):", wF)
def kur(q, B):
    n = len(q); S = [[int(np.argmax(q[j]))] for j in range(n)]
    while True:
        C = np.prod([len(s) for s in S]); best = None
        for j in range(n):
            mm = len(S[j])
            if C * (mm + 1) / mm > B: continue
            Pj = q[j][S[j]].sum()
            for i in range(len(q[j])):
                if i in S[j]: continue
                sc = np.log((Pj + q[j][i]) / Pj) / np.log((mm + 1) / mm)
                if best is None or sc > best[0]: best = (sc, j, i)
        if best is None: return S
        S[best[1]].append(best[2])
ARMS = {"AGF": lambda g: g.a.values, "PF": lambda g: g.p_PF.values, "P0": lambda g: g.p_P0.values, "KARISIM": lambda g: mix(g.a.values, g.p_PF.values, wF)}
rows = []
for x in AL:
    r = {"t": x["t"], "gun": x["t"] + x["h"], "yil": x["t"][:4]}
    for ad, f in ARMS.items():
        q = [f(g) for g in x["legs"]]
        for B in (64, 256):
            S = kur(q, B); hits = [bool(g.kazandi.values[S[j]].any()) for j, g in enumerate(x["legs"])]
            r[f"hit_{ad}_{B}"] = sum(hits); r[f"cost_{ad}_{B}"] = int(np.prod([len(s) for s in S])); r[f"pay_{ad}_{B}"] = x["tutar"] if (all(hits) and not x["devir"]) else 0.0
    rows.append(r)
D = pd.DataFrame(rows)
for yil in ("2025", "2026"):
    X = D[D.yil == yil]
    for ad in ("PF", "P0", "KARISIM"):
        for B in (64, 256):
            ana = (ad == "PF")
            R[f"altili_{yil}_tutan_{ad}-AGF_B{B}"] = ga(X[f"hit_{ad}_{B}"] - X[f"hit_AGF_{B}"], X.gun, *((0.833, 99.167) if ana else (2.5, 97.5)), B=5000)
    for ad in ARMS:
        for B in (64, 256):
            R[f"altili_{yil}_betim_{ad}_B{B}"] = {"altili": int(len(X)), "ort_ayak": float(X[f"hit_{ad}_{B}"].mean()), "6/6": int((X[f"hit_{ad}_{B}"] == 6).sum()), "ROI": float(X[f"pay_{ad}_{B}"].sum() / max(X[f"cost_{ad}_{B}"].sum(), 1))}
for k, v in R.items():
    if k.startswith("altili"): log(k, v if not isinstance(v, list) else [round(x, 4) for x in v])
# ======================= KARAR (ön kayıt) =======================
def iki_yil(k): return all(R[f"{y}_{k}"][1] > 0 for y in ("2025", "2026"))
K1 = "PİYASASIZ MODEL AGF'DEN İSABETLİ" if iki_yil("PF-AGF") else ("AGF DAHA İSABETLİ" if all(R[f"{y}_PF-AGF"][0] < 0 for y in ("2025", "2026")) else "AYIRT EDİLEMEZ / KARIŞIK")
K2 = "ELENEN ÖZELLİKLER PİYASASIZDA FAYDALI" if iki_yil("PF-P0") else ("ZARARLI" if all(R[f"{y}_PF-P0"][2] < 0 for y in ("2025", "2026")) else "FAYDA KANITLANMADI")
K3_ = "KUPONDA AGF'Yİ GEÇİYOR" if all(R[f"altili_{y}_tutan_PF-AGF_B{B}"][1] > 0 for y in ("2025", "2026") for B in (64, 256)) else ("KUPONDA AGF'NİN GERİSİNDE" if all(R[f"altili_{y}_tutan_PF-AGF_B{B}"][0] < 0 for y in ("2025", "2026") for B in (64, 256)) else "KUPONDA AYIRT EDİLEMEZ")
log("KARAR 1 (kazanan, PF vs AGF):", K1); log("KARAR 2 (PF vs P0):", K2); log("KARAR 3 (altılı tutan ayak, PF vs AGF):", K3_)
R["karar"] = [K1, K2, K3_]; R["w_karisim"] = wF
json.dump(R, open(os.path.join(KOK, "data", "analiz", "t201.json"), "w"), indent=1, ensure_ascii=False)
