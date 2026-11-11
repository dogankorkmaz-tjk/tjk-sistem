"""T202: altılıda DEĞER seçimi (Πq/Πa). Ön kayıt: hipotez_defteri T202. Actions: t202.yml. Betik sonuca bakılarak ayarlanmaz."""
import os, sys, json, glob, itertools
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK)
src = open(os.path.join(KOK, "data", "analiz", "t200.py")).read().split("def mix(a, p0, w)")[0]
exec(compile(src, "t200head", "exec"))   # AL (altılılar), np, pd, G ... hazır
def mixq(a, p0, w):
    l = (1 - w) * np.log(a) + w * np.log(np.maximum(p0, 1e-9)); e = np.exp(l - l.max()); return e / e.sum()
NC = 4
def combos(legs_p, legs_a, kriter, B):
    """her ayakta legs_p'ye göre ilk NC at; kombinasyonlar kriter ile sıralanır, ilk B döner (ayak içi indeks listeleri)"""
    cand = [np.argsort(-p)[:NC] for p in legs_p]
    idx = np.array(list(itertools.product(*[range(len(c)) for c in cand])))
    lp = np.zeros(len(idx)); la = np.zeros(len(idx))
    for j, c in enumerate(cand):
        lp += np.log(np.maximum(legs_p[j][c[idx[:, j]]], 1e-12)); la += np.log(np.maximum(legs_a[j][c[idx[:, j]]], 1e-12))
    sk = la if kriter == "a" else lp - la
    o = np.argsort(-sk)[:B]
    return [[int(cand[j][i]) for j, i in enumerate(idx[k])] for k in o]
def kur(q, B):  # T200 açgözlü kurucu (bilgi kolu A)
    n = len(q); S = [[int(np.argmax(q[j]))] for j in range(n)]
    while True:
        C = np.prod([len(s) for s in S]); best = None
        for j in range(n):
            m = len(S[j])
            if C * (m + 1) / m > B: continue
            Pj = q[j][S[j]].sum()
            for i in range(len(q[j])):
                if i in S[j]: continue
                sc = np.log((Pj + q[j][i]) / Pj) / np.log((m + 1) / m)
                if best is None or sc > best[0]: best = (sc, j, i)
        if best is None: return S
        S[best[1]].append(best[2])
def say(legs, kazan, combos_list):
    """kupon: kombinasyon listesi -> (tutan ayak, kazanan kombinasyon sayısı, maliyet)"""
    W = [set(np.where(g.kazandi.values == 1)[0]) for g in legs]
    win = sum(all(c[j] in W[j] for j in range(6)) for c in combos_list)
    return win
rows = []; W15, W50 = 0.15, 0.50
for x in AL:
    L = x["legs"]; a = [g.a.values for g in L]; p0 = [g.p0.values for g in L]
    q15 = [mixq(a[j], p0[j], W15) for j in range(6)]; q50 = [mixq(a[j], p0[j], W50) for j in range(6)]
    r = {"t": x["t"], "h": x["h"], "gun": x["t"] + x["h"], "yil": "2025" if x["t"] < "2026" else "2026", "tutar": x["tutar"], "devir": int(x["devir"])}
    # ödeme–AGF kontrolü için kazanan(lar)ın değerleri (ilk kazanan)
    wi = [int(np.argmax(g.kazandi.values)) for g in L]
    r["sla"] = float(-sum(np.log(max(a[j][wi[j]], 1e-9)) for j in range(6)))
    r["slqa"] = float(sum(np.log(max(q50[j][wi[j]], 1e-9) / max(a[j][wi[j]], 1e-9)) for j in range(6)))
    for B in (64, 256):
        kup = {"AX": combos(a, a, "a", B), "V15": combos(q15, a, "v", B), "V50": combos(q50, a, "v", B)}
        # bilgi: açgözlü A
        S = kur(a, B); cl = [list(c) for c in itertools.product(*S)]; kup["A"] = cl
        for ad, cl in kup.items():
            w = say(L, None, cl); cost = len(cl)
            hits = [int(any(c[j] in set(np.where(L[j].kazandi.values == 1)[0]) for c in cl)) for j in range(6)]
            r[f"cost_{ad}_{B}"] = cost; r[f"hit_{ad}_{B}"] = sum(hits); r[f"all_{ad}_{B}"] = int(w > 0)
            r[f"pay_{ad}_{B}"] = 0.0 if x["devir"] else float(x["tutar"] * w)
    rows.append(r)
D = pd.DataFrame(rows); D.to_csv(os.path.join(KOK, "data", "analiz", "t202_altili.csv"), index=False)
rng = np.random.default_rng(2020)
def boot(df, f, B=5000, lo=1.25, hi=98.75):
    idx = {k: v.index.values for k, v in df.groupby("gun")}; keys = list(idx); n = len(keys); out = []
    for _ in range(B):
        sel = np.concatenate([idx[keys[i]] for i in rng.integers(0, n, n)]); out.append(f(df.loc[sel]))
    return [float(f(df)), *map(float, np.percentile(out, [lo, hi]))]
roi = lambda df, ad, B: float(df[f"pay_{ad}_{B}"].sum() / df[f"cost_{ad}_{B}"].sum())
res = {}
for B in (64, 256):
    for ad in ("AX", "A", "V15", "V50"):
        for nm, X in (("tum", D), ("2025", D[D.yil == "2025"]), ("2026", D[D.yil == "2026"])):
            X = X.reset_index(drop=True)
            res[f"{nm}_{ad}_B{B}"] = {"altili": len(X), "tutan_ayak": float(X[f"hit_{ad}_{B}"].mean()), "6/6": int(X[f"all_{ad}_{B}"].sum()), "ROI": roi(X, ad, B), "maliyet": float(X[f"cost_{ad}_{B}"].mean()), "ROI_GA95": boot(X, lambda df, ad=ad, B=B: roi(df, ad, B), B=2000, lo=2.5, hi=97.5)[1:]}
    for ad in ("V15", "V50"):
        f = lambda df, ad=ad, B=B: roi(df, ad, B) - roi(df, "AX", B)
        res[f"fark_tum_{ad}-AX_B{B}"] = boot(D, f)
        for y in ("2025", "2026"): res[f"fark_{y}_{ad}-AX_B{B}"] = float(f(D[D.yil == y]))
        res[f"tutan_fark_tum_{ad}-AX_B{B}"] = float((D[f"hit_{ad}_{B}"] - D[f"hit_AX_{B}"]).mean())
# ödeme–AGF tutarlılık (devir olmayan, tutar>0)
Z = D[(D.devir == 0) & (D.tutar > 0)]
ly = np.log(Z.tutar.values); X1 = Z.sla.values
cor = float(np.corrcoef(ly, X1)[0, 1]); sl = float(np.polyfit(X1, ly, 1)[0])
A2 = np.c_[np.ones(len(Z)), Z.sla.values, Z.slqa.values]; beta = np.linalg.lstsq(A2, ly, rcond=None)[0]
res["odeme_kontrol"] = {"n": len(Z), "corr_log_tutar_vs_-sum_log_a": cor, "egim": sl, "coef_[sabit,sla,slqa50]": [float(b) for b in beta]}
def karar(ad, B):
    g = res[f"fark_tum_{ad}-AX_B{B}"]; y1, y2 = res[f"fark_2025_{ad}-AX_B{B}"], res[f"fark_2026_{ad}-AX_B{B}"]
    if g[1] > 0 and y1 > 0 and y2 > 0: return "ADAY"
    if g[0] > 0 and y1 > 0 and y2 > 0: return "isaret"
    return "yok"
res["karar"] = {f"{ad}_B{B}": karar(ad, B) for ad in ("V15", "V50") for B in (64, 256)}
for k, v in res.items(): print(k, json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else np.round(v, 4).tolist())
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t202.json"), "w"), indent=1, ensure_ascii=False)
