"""T199: AGF'den hesaplanan 'ilk3 sürpriz' etiketi. Ön kayıt: hipotez_defteri T199."""
import os, json, glob
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open(os.path.join(KOK, "data", "analiz", "t197.py")).read().split("R = []")[0]
exec(compile(src, "t197head", "exec"))
import pandas as pd
def agf_pp(v): h = np.maximum(np.array(v, float), 0.3); return h / h.sum()
R = []
for f in sorted(glob.glob(os.path.join(KOK, "docs", "data", "gun", "*.json"))):
    d = json.load(open(f)); gun = d["tarih"]
    if d.get("w0_g1") is None: continue
    G = d.get("a_g1") or [1, .8, .69]
    for h in d["hipodromlar"]:
        for k in h["kosular"]:
            s = k.get("sonuc")
            if not s: continue
            at = [a for a in k["atlar"] if str(a["no"]) in s and (s[str(a["no"])].get("g") or 0) > 0]
            if len(at) < 5 or len(at) > 16 or any(a.get("z6") is None or a.get("agf") is None for a in at): continue
            g = [s[str(a["no"])]["g"] for a in at]; pk = piyasa(g); z = np.array([a["z6"] for a in at])
            row = {}
            for ad, key in (("A", "agf"), ("A0", "agf0")):
                if any(a.get(key) is None for a in at): row[ad] = None; continue
                pp = agf_pp([a[key] for a in at]); pg = modelp(pp, z, d["w0_g1"], d.get("lp2_g1") or 0.0)
                row[ad] = (pp, pg, harville(pp, G_PIY), harville(pg, G[:3]))
            pg_k = modelp(pk, z, d["w0_g1"], d.get("lp2_g1") or 0.0); i3p_k = harville(pk, G_PIY); i3b_k = harville(pg_k, G[:3])
            for j, a in enumerate(at):
                sr = s[str(a["no"])].get("sira"); r = [gun, h["id"], k["kosu"], a["no"], pk[j], i3b_k[j] / i3p_k[j] >= 1.15, 1.0 if sr == 1 else 0.0, 1.0 if (sr is not None and sr <= 3) else 0.0, s[str(a["no"])]["g"]]
                for ad in ("A", "A0"):
                    x = row[ad]; r += ([x[0][j], x[3][j] / x[2][j] >= 1.15, x[2][j]] if x else [np.nan, False, np.nan])
                R.append(r)
D = pd.DataFrame(R, columns=["gun", "hip", "kosu", "no", "pk", "et_k", "kaz", "ilk3", "g", "pA", "et_A", "i3pA", "pA0", "et_A0", "i3pA0"]); D["ode"] = D.kaz * D.g
print("gün", D.gun.nunique(), "koşu", D.groupby(["gun", "hip", "kosu"]).ngroups, "at", len(D), "etiketli(AGF)", int(D.et_A.sum()), "etiketli(kapanış)", int(D.et_k.sum()), "ikisi", int((D.et_A & D.et_k).sum()), flush=True)
rng = np.random.default_rng(1990)
def ga(S, x, lo=1.25, hi=98.75, B=20000):
    g = x.groupby(S.gun).agg(["sum", "count"]); s, c = g["sum"].values, g["count"].values; n = len(s); i = rng.integers(0, n, (B, n)); m = s[i].sum(1) / c[i].sum(1)
    return [float(s.sum() / c.sum()), *map(float, np.percentile(m, [lo, hi]))]
out = {}
for ad, et, pp, i3 in (("A_son_AGF", "et_A", "pA", "i3pA"), ("A0_ilk_AGF", "et_A0", "pA0", "i3pA0"), ("kapanis_T197", "et_k", "pk", None)):
    S = D[D[et]]
    if len(S) == 0: continue
    r = {"n": len(S), "kazanma": float(S.kaz.mean()), "ort_p_agf": float(S[pp].mean()), "kaz-p": ga(S, S.kaz - S[pp]), "kaz-p_kapanis": ga(S, S.kaz - S.pk), "ilk3": float(S.ilk3.mean())}
    if i3: r["ilk3-i3p"] = ga(S, S.ilk3 - S[i3]); r["ort_i3p"] = float(S[i3].mean())
    gr = S.groupby("gun").agg(o=("ode", "sum"), b=("ode", "size")); o, b = gr.o.values, gr.b.values; n = len(o); i = rng.integers(0, n, (20000, n)); m = o[i].sum(1) / b[i].sum(1) - 1
    r["ROI_bilgi"] = [float(o.sum() / b.sum() - 1), *map(float, np.percentile(m, [2.5, 97.5]))]; out[ad] = r
    print(ad, json.dumps({a: (np.round(v, 4).tolist() if isinstance(v, list) else (round(v, 4) if isinstance(v, float) else v)) for a, v in r.items()}, ensure_ascii=False), flush=True)
K = D.groupby(["gun", "hip", "kosu"]); sayi = K.et_A.sum(); var = sayi > 0
kz = K.apply(lambda g: float((g.et_A & (g.kaz == 1)).any())); bk = K.apply(lambda g: float(1 - np.prod(1 - g.pA[g.et_A]))); bkc = K.apply(lambda g: float(1 - np.prod(1 - g.pk[g.et_A])))
print(f"AGF-etiketli koşu {int(var.sum())}/{len(var)} ({var.mean():.1%}), koşu başına {sayi.mean():.2f}; kazanan etiketli: {kz[var].mean():.1%} (AGF beklentisi {bk[var].mean():.1%}, kapanış beklentisi {bkc[var].mean():.1%})")
e = out["A_son_AGF"]; a1 = e["kaz-p"]; a2 = e["ilk3-i3p"]
print("KARAR:", "AGF etiketi de çalışıyor" if (a1[1] > 0 and a2[1] > 0) else ("kısmen" if a1[1] > 0 else ("işaret" if a1[0] > 0 else "yok")))
json.dump(out, open(os.path.join(KOK, "data", "analiz", "t199.json"), "w"), indent=1, ensure_ascii=False)
