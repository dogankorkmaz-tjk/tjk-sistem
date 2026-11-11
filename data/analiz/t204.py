"""T204: bahis anı denetimi (yerli). Ön kayıt: hipotez_defteri T204. Actions: t204.yml. Betik sonuca bakılarak ayarlanmaz."""
import os, sys, json, glob
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK)
_ns = {"__file__": os.path.join(KOK, "data", "analiz", "t192.py")}
exec(compile(open(os.path.join(KOK, "data", "analiz", "t192.py")).read().split("feat = M[")[0], "t192head", "exec"), _ns)
d, M, O, _fit, skorla, EK, LPEK, np, pd = [_ns[k] for k in ("d", "M", "O", "_fit", "skorla", "EK", "LPEK", "np", "pd")]
from tjk import elo as EL
from tjk import komiser as KM
d = EL.ekle(d); d["rid"] = d.groupby(O.K).ngroup()
E = M["feat"] + EK + LPEK + EL.EXTRA_FEAT
BAS = "2026-10-15"
tr = d[d.tarih < BAS]; th, mu, sd, nk = _fit(tr, E, M.get("lam", 100.0))
te = d[d.tarih >= BAS].sort_values(O.K + ["no"]).reset_index(drop=True)
print("eğitim", len(tr), "pencere", len(te), flush=True)
def bahis_ani(min_dk):
    out = {}
    for f in sorted(glob.glob(os.path.join(KOK, "data", "muh", "*.json"))):
        gun = os.path.basename(f)[:-5]; D = json.load(open(f))
        for k, v in D.items():
            if v.get("yurtdisi") or "kosu" not in v: continue
            hip = str(v.get("hipodrom", "")).translate(O.TR).lower()
            if hip not in O.TRH: continue
            a = [s for s in v.get("anlik", []) if s.get("durum") == "AÇIK" and s.get("g") and s.get("dk", -9) >= min_dk]
            if not a: continue
            s = max(a, key=lambda s: -s["dk"]) if False else min(a, key=lambda s: s["dk"])   # başlamaya en yakın (≥ min_dk)
            out[(gun, hip, int(v["kosu"]))] = {int(n): float(g) for n, g in s["g"].items() if g not in (None, "-", 0)}
    return out
G = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(KOK, "data", "odeme", "*.csv.gz")))]); G = G[G.tur == "GANYAN"]
ODE = {(r.tarih, r.hipodrom, int(r.kosu), str(r.kombo)): float(r.tutar) for r in G.itertuples()}
TR2A = {v: k for k, v in KM.ASCII.items()}
rng = np.random.default_rng(2040); BB = 5000
def kos(min_dk):
    BA = bahis_ani(min_dk); rows = []
    for (t, h, k), g in te.groupby(["tarih", "hipodrom", "kosu"]):
        key = (t, h, int(k)); b = BA.get(key)
        if not b or not set(g.no.astype(int)).issubset(b.keys()) or not (g.kazandi == 1).any(): continue
        x = g.copy(); gb = x.no.astype(int).map(b).values.astype(float); pb = (1 / gb) / (1 / gb).sum()
        x["p_bet"] = pb; x["g_bet"] = gb; x["lp"] = np.log(pb); x["f_lp2"] = np.log(pb) ** 2; x["p_piyasa_c"] = x.p_piyasa.values
        x["p_piyasa"] = pb; x["p_E"] = skorla(x.reset_index(drop=True), E, th, mu, sd); rows.append(x.assign(p_piyasa=pb))
    R = pd.concat(rows, ignore_index=True)
    R["p_E"] = R.p_E / R.groupby(["tarih", "hipodrom", "kosu"]).p_E.transform("sum")
    R["pc"] = R.p_piyasa_c; R["g_kap"] = [ODE.get((t, TR2A.get(h, h), int(k), str(n)), np.nan) if kz == 1 else np.nan for t, h, k, n, kz in zip(R.tarih, R.hipodrom, R.kosu, R.no, R.kazandi)]
    R["ode"] = R.g_kap.fillna(0.0)
    # kapanış ganyanı (tüm atlar için) kayma: çözümleme ancak p_piyasa_c (kapanış olasılığı) üzerinden → g_kapanis ≈ 1/pc (kesinti dahil ölçek farkı sabit)
    R["kayma"] = np.log((1 / R.pc) / R.g_bet) ; return R
def roi(S):
    g = S.groupby("tarih").agg(n=("ode", "size"), o=("ode", "sum")).values
    if len(g) == 0 or g[:, 0].sum() == 0: return None
    m = len(g); idx = rng.integers(0, m, (BB, m)); T = g[idx].sum(1)
    return {"bahis": int(g[:, 0].sum()), "isabet": int((S.ode > 0).sum()), "ROI": float(g[:, 1].sum() / g[:, 0].sum()), "GA95": [float(x) for x in np.percentile(T[:, 1] / T[:, 0], [2.5, 97.5])]}
sonuc = {}
for ad, mind in (("ANA_1dk", 1.0), ("DUY_3dk", 3.0)):
    R = kos(mind); nk_ = R.groupby(["tarih", "hipodrom", "kosu"]).ngroups
    rb = R[((R.p_E / R.p_bet) >= 1.15) & (R.p_E >= 0.10)]; rc = R[((R.p_E / R.pc) >= 1.15) & (R.p_E >= 0.10)]
    rb_ekran = rb.assign(ode=np.where(rb.kazandi == 1, rb.g_bet, 0.0))
    gunk = rb.groupby("tarih").kayma.agg(["sum", "count"]).values; gall = R.groupby("tarih").kayma.agg(["sum", "count"]).values
    def kayma_ga():
        days = sorted(R.tarih.unique()); a = R[R.index.isin(rb.index)].groupby("tarih").kayma.agg(["sum", "count"]).reindex(days, fill_value=0).values; b = R.groupby("tarih").kayma.agg(["sum", "count"]).reindex(days, fill_value=0).values
        n = len(days); idx = rng.integers(0, n, (BB, n)); A = a[idx].sum(1); B_ = b[idx].sum(1); fark = A[:, 0] / np.maximum(A[:, 1], 1) - B_[:, 0] / B_[:, 1]
        return float(a[:, 0].sum() / max(a[:, 1].sum(), 1) - b[:, 0].sum() / b[:, 1].sum()), [float(x) for x in np.percentile(fark, [2.5, 97.5])], float(a[:, 0].sum() / max(a[:, 1].sum(), 1)), float(b[:, 0].sum() / b[:, 1].sum())
    kf = kayma_ga()
    sonuc[ad] = {"kosu": nk_, "gun": int(R.tarih.nunique()), "RB": roi(rb), "RC": roi(rc), "RB_ekran_orani": roi(rb_ekran), "kayma_secilen": kf[2], "kayma_tum": kf[3], "kayma_fark": kf[0], "kayma_fark_GA95": kf[1]}
    print(ad, json.dumps(sonuc[ad], ensure_ascii=False), flush=True)
json.dump(sonuc, open(os.path.join(KOK, "data", "analiz", "t204.json"), "w"), indent=1, ensure_ascii=False)
n_b = (sonuc["ANA_1dk"]["RB"] or {}).get("bahis", 0)
print("YORUM: n_bahis", n_b, "->", "BİLGİ (n<500)" if n_b < 500 else ("kanıt yok" if sonuc["ANA_1dk"]["RB"]["GA95"][0] < 1 else "aday"))
