"""T198: koşu başına tek 'ilk3 sürpriz' etiketli at (S1 en yüksek f3, S2 en yüksek i3b). Ön kayıt: hipotez_defteri T198."""
import os, json, glob
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open(os.path.join(KOK, "data", "analiz", "t197.py")).read().split("rng = np.random")[0]
exec(compile(src, "t197head", "exec"))
G = {}
for f in glob.glob(os.path.join(KOK, "docs", "data", "gun", "*.json")):
    d = json.load(open(f))
    for h in d["hipodromlar"]:
        for k in h["kosular"]:
            for no, v in (k.get("sonuc") or {}).items(): G[(d["tarih"], h["id"], k["kosu"], int(no))] = v.get("g")
D["g"] = [G.get((a, b, c, int(n))) for a, b, c, n in zip(D.gun, D.hip, D.kosu, D.no)]; D["ode"] = D.kaz * D.g
E = D[D.etiket]; rng = np.random.default_rng(1980)
def sec(col): return E.loc[E.groupby(["gun", "hip", "kosu"])[col].idxmax()]
def ga(S, x, B=20000):
    g = x.groupby(S.gun).agg(["sum", "count"]); s, c = g["sum"].values, g["count"].values; n = len(s); i = rng.integers(0, n, (B, n)); m = s[i].sum(1) / c[i].sum(1)
    return float(s.sum() / c.sum()), np.percentile(m, [1.25, 98.75])
sonuc = {}
for ad, col in (("S1_en_yuksek_f3", "f3"), ("S2_en_yuksek_i3b", "i3b")):
    S = sec(col); k, kc = ga(S, S.kaz - S.pp); t, tc = ga(S, S.ilk3 - S.i3p)
    gr = S.groupby("gun").agg(o=("ode", "sum"), b=("ode", "size")); o, b = gr.o.values, gr.b.values; n = len(o); i = rng.integers(0, n, (20000, n)); m = o[i].sum(1) / b[i].sum(1) - 1
    r = {"n": len(S), "kazanma": float(S.kaz.mean()), "ort_pp": float(S.pp.mean()), "kaz-pp": [k, *map(float, kc)], "ilk3": float(S.ilk3.mean()), "ort_i3p": float(S.i3p.mean()), "ilk3-i3p": [t, *map(float, tc)],
         "ROI_bilgi": [float(o.sum() / b.sum() - 1), *map(float, np.percentile(m, [2.5, 97.5]))]}
    r["karar"] = "ADAY" if (kc[0] > 0 and tc[0] > 0) else ("işaret" if k > 0 else "yok"); sonuc[ad] = r
    print(ad, json.dumps({a: (np.round(v, 4).tolist() if isinstance(v, list) else (round(v, 4) if isinstance(v, float) else v)) for a, v in r.items()}, ensure_ascii=False), flush=True)
json.dump(sonuc, open(os.path.join(KOK, "data", "analiz", "t198.json"), "w"), indent=1, ensure_ascii=False)
