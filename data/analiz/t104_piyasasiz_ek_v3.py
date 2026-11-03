"""T104: T100'ün Benter v3 tabanında tekrarı (ön kayıt: hipotez_defteri T104). python3 data/analiz/t104_piyasasiz_ek_v3.py
Taban A = v3 (piyasa+G1+Jason+galop). B = piyasasız (LM ağırlığı 0, aynı Jason+G1 özellikleri, galopsuz)."""
import os, sys
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_v3.py")).read().split("\naylar = sorted")[0]
exec(compile(src, "entegre_v3", "exec"))
def fitJb(rl, l2=30.0, lj=50.0):
    LM, XX, _, XJ = packJ(rl); msk = LM > -1e8; mu = XJ[msk].mean(0); sd = XJ[msk].std(0) + 1e-9; Z = np.where(msk[..., None], (XJ - mu) / sd, 0.0)
    def f(t):
        s = np.where(msk, XX @ t[1:10] + Z @ t[10:10 + NJ], -1e9); out, ds, dg = steps(s, np.r_[1.0, t[10 + NJ:14 + NJ]])
        g = np.r_[0.0, np.einsum("nm,nmk->k", ds, XX) + 2 * l2 * t[1:10], np.einsum("nm,nmk->k", ds, Z) + 2 * lj * t[10:10 + NJ], dg]
        return sum(o.sum() for o in out) + l2 * (t[1:10] @ t[1:10]) + lj * (t[10:10 + NJ] @ t[10:10 + NJ]), g
    t0 = np.zeros(14 + NJ); t0[10 + NJ:] = 1
    t = minimize(f, t0, jac=True, method="L-BFGS-B", bounds=[(0, 0)] + [(None, None)] * (13 + NJ), options={"maxiter": 400}).x
    return t, mu, sd
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if a >= "2026-04"]
rng = np.random.default_rng(5); rows = []
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    tm = fitJ(tr); S3, g3, FF3 = scoreJ(te, tm)
    trg = [r for r in tr if r["F"] is not None]; S3tr, _, FF3tr = scoreJ(trg, tm); bg3 = fit2S(S3tr, FF3tr); SA = S3 + ((FF3 - bg3[1]) / bg3[2]) @ bg3[0]
    SB, _, _ = scoreJ(te, fitJb(tr))
    for q, r in enumerate(te):
        n = len(r["lm"]); oA = list(np.argsort(-SA[q, :n])); oB = list(np.argsort(-SB[q, :n]))
        for k in (2, 3, 4, 5):
            if n < k + 2: continue
            base = oA[:k]; X = next(i for i in oB if i not in base); Y = oA[k]
            rest = [i for i in range(n) if i not in base]; Z = int(rng.choice(rest))
            rows.append((r["gun"], k, int(0 in base), int(X == 0), int(Y == 0), int(Z == 0), float(np.exp(r["lm"][X])), int(oA[0] != oB[0]), int(oA[0] == 0)))
    print(a, len(te), "ok", flush=True)
import pandas as pd
D = pd.DataFrame(rows, columns=["gun", "k", "taban", "ek", "Y", "Z", "pmX", "ayr", "A1"]); ug = sorted(D.gun.unique()); out = []
def boot(df, f, B=5000):
    ix = df.groupby("gun").indices; ds = list(ix); r = np.random.default_rng(7); v = []
    for _ in range(B):
        s = r.choice(len(ds), len(ds)); idx = np.concatenate([ix[ds[j]] for j in s]); v.append(f(df.iloc[idx]))
    return np.percentile(v, [2.5, 97.5])
out.append(f"T104 (v3 tabanı): test {D[D.k==3].shape[0]} koşu (k=3), {len(ug)} gün; {test[0]}..{test[-1]}")
for k in (3, 2, 4, 5):
    d = D[D.k == k]; f = lambda x: x.ek.mean() - x.Y.mean(); lo, hi = boot(d, f); fz = lambda x: x.ek.mean() - x.Z.mean(); zl, zh = boot(d, fz)
    out.append(f"{'BİRİNCİL' if k==3 else 'keşifsel'} k={k}: taban kazanan {d.taban.mean():.3f} | ek (piyasasız) {d.ek.mean():.4f} | Y {d.Y.mean():.4f} | rastgele {d.Z.mean():.4f} | ek−Y {f(d):+.4f} GA95 [{lo:+.4f},{hi:+.4f}] | ek−rastgele {fz(d):+.4f} [{zl:+.4f},{zh:+.4f}]")
open("data/analiz/t104_sonuc.txt", "w").write("\n".join(out)); print("\n".join(out))
