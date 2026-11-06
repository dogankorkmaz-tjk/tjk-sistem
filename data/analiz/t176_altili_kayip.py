"""T176 (ön kayıt hipotez_defteri 2026-11-07 02:4x): altılı kuponda canlı bilgi kaybı, AGF momentumu, ayak belirsizliği."""
import json, glob, numpy as np, pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import spearmanr
rng = np.random.default_rng(176)
def modelP(pp, z, w0, c2):
    l = np.log(np.maximum(pp, 1e-6)); s = w0 * l + c2 * l * l + z; e = np.exp(s - s.max()); return e / e.sum()
R = []
for f in sorted(glob.glob("docs/data/gun/2026-*.json")):
    d = json.load(open(f, encoding="utf-8")); gun = d.get("tarih")
    if not gun or gun > "2026-11-06" or d.get("w0_g1") is None: continue
    for h in d["hipodromlar"]:
        K = {k["kosu"]: k for k in h["kosular"]}
        for alt, son in (h.get("altili") or {}).items():
            for j, kn in enumerate(range(int(son) - 5, int(son) + 1), start=1):
                k = K.get(kn)
                if not k or not k.get("sonuc"): continue
                so = k["sonuc"]; at = [a for a in k["atlar"] if not a.get("kosmaz") and str(a["no"]) in so and (so[str(a["no"])].get("g") or 0) > 1]
                if len(at) < 4: continue
                fa = "agf_a1" if str(alt) == "1" else "agf"
                agf = np.array([a.get(fa) or np.nan for a in at], float); agf0 = np.array([a.get("agf0") or np.nan for a in at], float)
                g = np.array([so[str(a["no"])]["g"] for a in at], float); sira = np.array([so[str(a["no"])].get("sira") or 99 for a in at])
                zb = [a.get("z6b") if a.get("z6b") is not None else a.get("z6") for a in at]
                if np.isnan(agf).any() or (agf <= 0).any() or not (sira == 1).any() or any(z is None for z in zb): continue
                z = np.array(zb, float); c2 = d.get("lp2_g1") or 0.0 if all(a.get("z6b") is not None for a in at) else 0.0
                w = int(np.argmax(sira == 1)); pA = agf / agf.sum(); pK = (1 / g) / (1 / g).sum()
                R.append(dict(gun=gun, ayak=j, n=len(at), w=w, pA=pA, pK=pK, z=z, w0=d["w0_g1"], c2=c2,
                              mom=np.where(np.isnan(agf0) | (agf0 <= 0), 1.0, agf / np.where(agf0 > 0, agf0, 1))))
print("ayak-koşu:", len(R), "gün:", len({r['gun'] for r in R}))
def ll(r, p): return np.log(max(p[r["w"]], 1e-9))
for r in R:
    r["bA"] = modelP(r["pA"], r["z"], r["w0"], r["c2"]); r["bK"] = modelP(r["pK"], r["z"], r["w0"], r["c2"])
    r["kayip_B"] = ll(r, r["bK"]) - ll(r, r["bA"]); r["kayip_P"] = ll(r, r["pK"]) - ll(r, r["pA"])
    r["kl"] = float((r["bA"] * np.log(r["bA"] / r["pA"])).sum()); r["oyn"] = float(np.abs(np.log(r["mom"])).mean())
D = pd.DataFrame([{k: v for k, v in r.items() if not isinstance(v, np.ndarray)} for r in R])
def boot(x, g):
    s = pd.Series(x).groupby(np.asarray(g)).agg(["sum", "size"]); ug = s.index.values
    bs = [(lambda q: s.loc[q, "sum"].sum() / s.loc[q, "size"].sum())(rng.choice(ug, len(ug))) for _ in range(3000)]; return np.percentile(bs, [2.5, 97.5])
print("=== 1) Canlı bilgi kaybı: kazanan log-olabilirliği, kapanış − ilk ayak öncesi AGF (nats/koşu; büyük = kapanış daha iyi)")
for j in range(1, 7):
    x = D[D.ayak == j]
    if not len(x): continue
    lo, hi = boot(x.kayip_B.values, x.gun.values); lp, hp = boot(x.kayip_P.values, x.gun.values)
    print(f"  {j}. ayak ({len(x)} koşu): Benter {x.kayip_B.mean():+.4f} [{lo:+.4f}; {hi:+.4f}] | piyasa tek {x.kayip_P.mean():+.4f} [{lp:+.4f}; {hp:+.4f}]")
lo, hi = boot(D.kayip_B.values, D.gun.values); print(f"  TÜMÜ ({len(D)}): Benter {D.kayip_B.mean():+.4f} [{lo:+.4f}; {hi:+.4f}] | eğilim (ayak ~ kayıp) Spearman {spearmanr(D.ayak, D.kayip_B)[0]:+.3f}")
print("=== 2) AGF momentumu p' ∝ p_AGF × (agf/agf0)^λ")
tr = [r for r in R if r["gun"] <= "2026-10-07"]; te = [r for r in R if r["gun"] > "2026-10-07"]
def ll_lam(rs, lam):
    out = []
    for r in rs:
        q = r["pA"] * np.power(r["mom"], lam); q /= q.sum(); out.append(ll(r, modelP(q, r["z"], r["w0"], r["c2"])))
    return np.array(out)
lam = minimize_scalar(lambda L: -ll_lam(tr, L).sum(), bounds=(-2, 3), method="bounded").x
dd = ll_lam(te, lam) - ll_lam(te, 0.0); lo, hi = boot(dd, [r["gun"] for r in te])
print(f"  λ (eğitim {len(tr)} koşu) = {lam:+.3f} | test ({len(te)} koşu): {dd.mean():+.4f} nats/koşu [{lo:+.4f}; {hi:+.4f}] → {'ADAY' if lo > 0 else 'kanıt yok'} | kapanış bilgisinin ne kadarını geri alır: %{100*dd.mean()/max(np.mean([r['kayip_B'] for r in te]),1e-9):.0f}")
print("=== 3) Ayak belirsizliği göstergeleri ile kayıp ilişkisi (Spearman)")
for c in ("kl", "oyn", "n"):
    rho, pv = spearmanr(D[c], D.kayip_B); print(f"  {c}: rho {rho:+.3f} (p {pv:.3f})")
