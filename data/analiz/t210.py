"""T210: Adana Çelik jokeyleri. Ön kayıt: hipotez_defteri T210."""
import os, sys, json
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, KOK)
_ns = {"__file__": os.path.join(KOK, "data", "analiz", "t192.py")}
exec(compile(open(os.path.join(KOK, "data", "analiz", "t192.py")).read().split("feat = M[")[0], "h", "exec"), _ns)
d, np, pd = _ns["d"], _ns["np"], _ns["pd"]
d = d[~d.kosmadi.fillna(False).astype(bool)].copy()
j = d.jokey.astype(str).str.upper()
d["celik"] = j.str.contains("ÇELİK") & ~j.str.contains("ÇELİKBAŞ")
d["adana"] = d.hipodrom.astype(str).str.lower().str.contains("adana")
d["yil"] = pd.to_datetime(d.tarih).dt.year
rng = np.random.default_rng(2100); BB = 10000
def boot(x, gun, f):
    u, inv = np.unique(gun, return_inverse=True); n = len(u); idx = rng.integers(0, n, (BB, n)); out = []
    S = [np.bincount(inv, weights=v) for v in x]; return [float(a) for a in np.percentile(f(*[s[idx].sum(1) for s in S]), [2.5, 97.5])]
res = {}
def blok(df, ad):
    w = df.kazandi.astype(float).values; e = df.p_piyasa.values; g = df.getiri.astype(float).values; gun = df.tarih.values
    r = {"n": int(len(df)), "kazanan": float(w.sum()), "beklenen": float(e.sum()), "oran": float(w.sum() / e.sum()),
         "oran_GA": boot([w, e], gun, lambda a, b: a / b), "roi": float(g.mean()), "roi_GA": boot([g, np.ones(len(g))], gun, lambda a, b: a / b)}
    res[ad] = r; print(ad, json.dumps(r), flush=True)
for per, f in (("tum", lambda x: x.yil >= 2023), ("2023-24", lambda x: x.yil <= 2024), ("2025-26", lambda x: x.yil >= 2025)):
    blok(d[d.adana & d.celik & f(d)], f"adana_celik_{per}"); blok(d[d.adana & ~d.celik & f(d)], f"adana_diger_{per}"); blok(d[~d.adana & d.celik & f(d)], f"digerhip_celik_{per}")
# B altılı
o = pd.concat([pd.read_csv(os.path.join(KOK, "data", "odeme", a)) for a in sorted(os.listdir(os.path.join(KOK, "data", "odeme"))) if a.endswith(".csv.gz")])
o = o[o.tur.astype(str).str.contains("6'LI GANYAN") & o.hipodrom.astype(str).str.lower().str.contains("adana")]
o = o.drop_duplicates(["tarih", "kosu"]); A = d[d.adana]; k_all = set(zip(A.tarih, A.kosu)); rows = []
for mod in ("ilk", "son"):
    ok = [(t, k) for t, k in zip(o.tarih, o.kosu) if all(((t, k + i) if mod == "ilk" else (t, k - i)) in k_all for i in range(6))]
    res[f"altili_{mod}_tam"] = len(ok)
mod = "ilk" if res["altili_ilk_tam"] >= res["altili_son_tam"] else "son"; res["altili_yorum"] = mod; print("yorum", mod, res["altili_ilk_tam"], res["altili_son_tam"], len(o), flush=True)
G = A.groupby(["tarih", "kosu"])
for t, k in zip(o.tarih, o.kosu):
    legs = [k + i if mod == "ilk" else k - i for i in range(6)]
    if not all((t, l) in k_all for l in legs): continue
    P = []; W = []
    for l in legs:
        g = G.get_group((t, l)); P.append(float(g[g.celik].p_piyasa.sum())); W.append(int(g[g.celik].kazandi.astype(float).sum() > 0))
    P = np.array(P); rows.append(dict(tarih=t, p0=float(np.prod(1 - P)), cel_hic=int(sum(W) == 0), nleg=sum(W), enleg=float(P.sum())))
R = pd.DataFrame(rows); res["altili_n"] = int(len(R))
if len(R):
    gun = R.tarih.values
    res["B"] = {"n": int(len(R)), "celiksiz_gozlenen": float(R.cel_hic.mean()), "celiksiz_beklenen": float(R.p0.mean()), "fark_GA": boot([R.cel_hic.values - R.p0.values, np.ones(len(R))], gun, lambda a, b: a / b),
                "ort_celik_ayak_gozlenen": float(R.nleg.mean()), "ort_celik_ayak_beklenen": float(R.enleg.mean()), "ayak_fark_GA": boot([R.nleg.values - R.enleg.values, np.ones(len(R))], gun, lambda a, b: a / b)}
    print("B", json.dumps(res["B"]), flush=True)
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t210.json"), "w"), indent=1, ensure_ascii=False)
