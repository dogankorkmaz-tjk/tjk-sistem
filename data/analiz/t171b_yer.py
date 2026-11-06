"""T171-B (ön kayıt hipotez_defteri 2026-11-07 02:0x): 'yer tutma' özelliği (jokey/at, kazanamadığı koşularda piyasaya göre bitiş artığı) 2.–5. sıra tahminine katkı."""
import glob, pickle, numpy as np, pandas as pd
from scipy.optimize import minimize
rng = np.random.default_rng(1712)
T = pd.concat([pd.read_csv(f, usecols=["tarih", "hipodrom", "kosu", "sira", "no", "at", "jokey", "kosmadi", "ganyan"]) for f in sorted(glob.glob("data/temiz/20*.csv.gz"))])
T = T[(T.kosmadi != True) & T.sira.notna() & (T.sira > 0) & T.ganyan.notna()].copy(); T["sira"] = T.sira.astype(int)
T["n"] = T.groupby(["tarih", "hipodrom", "kosu"]).no.transform("size")
T["mr"] = T.groupby(["tarih", "hipodrom", "kosu"]).ganyan.rank(method="average")
T["r"] = (T.mr - T.sira) / (T.n - 1).clip(lower=1)
T = T.sort_values(["tarih", "hipodrom", "kosu", "no"])
J, A, F = {}, {}, {}
for gun, x in T.groupby("tarih", sort=True):
    for r in x.itertuples():                                   # önce bugünkü özellik (yalnız önceki günler)
        sj, nj = J.get(r.jokey, (0.0, 0)); sa, na = A.get(r.at, (0.0, 0))
        F[(r.tarih, r.hipodrom, int(r.kosu), int(r.no))] = (sj / (nj + 10), sa / (na + 5))
    for r in x[x.sira > 1].itertuples():                       # sonra bugünün kazanamayan atlarıyla güncelle
        sj, nj = J.get(r.jokey, (0.0, 0)); J[r.jokey] = (sj + r.r, nj + 1)
        sa, na = A.get(r.at, (0.0, 0)); A[r.at] = (sa + r.r, na + 1)
print("özellik:", len(F), flush=True)
AYLAR = ["2025-10", "2025-11", "2025-12"] + [f"2026-{m:02d}" for m in range(1, 11)]
R = []
for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb"))
    for i, key in enumerate(c["keys"]):
        nos = list(c["nos"][i]); n = len(nos)
        if n < 6: continue
        X = np.array([F.get((key[0], key[1], int(key[2]), int(x)), (0.0, 0.0)) for x in nos])
        R.append(dict(gun=key[0], ay=ay, s=np.array(c["S3"][i][:n], float), g=np.array(c["g3"], float), X=X))
print("koşu:", len(R), flush=True)
def ll(r, b, steps=range(1, 5)):
    s, g, X = r["s"], r["g"], r["X"]; n = len(s); out = []
    for k in steps:
        if k >= n - 1: break
        z = g[min(k, len(g) - 1)] * s[k:] + X[k:] @ b; z = z - z.max()
        out.append(z[0] - np.log(np.exp(z).sum()))            # nos bitiriş sırasında: k. adımda kalanlar k.., kazanan k
    return np.array(out)
egit = [r for r in R if r["ay"] <= "2026-03"]; test = [r for r in R if r["ay"] >= "2026-04"]
def fit(mask):
    f = lambda b: -sum(ll(r, b * mask).sum() for r in egit) + 1.0 * (b @ b)
    return minimize(f, np.zeros(2), method="L-BFGS-B").x * mask
for ad, mask in (("İKİSİ (birincil)", np.array([1.0, 1.0])), ("yalnız jokey", np.array([1.0, 0.0])), ("yalnız at", np.array([0.0, 1.0]))):
    b = fit(mask)
    d = np.array([ll(r, b).sum() - ll(r, np.zeros(2)).sum() for r in test]); gun = np.array([r["gun"] for r in test])
    ds = pd.Series(d).groupby(gun).agg(["sum", "size"]); ug = ds.index.values
    bs = [(lambda s_: ds.loc[s_, "sum"].sum() / ds.loc[s_, "size"].sum())(rng.choice(ug, len(ug))) for _ in range(3000)]
    print(f"{ad}: β = {np.round(b, 3).tolist()} | test 2.–5. sıra log-olabilirlik farkı {d.mean():+.4f} nats/koşu [{np.percentile(bs, 2.5):+.4f}; {np.percentile(bs, 97.5):+.4f}] ({len(test)} koşu)", flush=True)
    if mask.sum() == 2:
        for k in range(1, 5):
            dk = [ (lambda a, z: a[k-1] - z[k-1] if len(a) >= k else 0.0)(ll(r, b), ll(r, np.zeros(2))) for r in test]
            print(f"     {k+1}. sıra: {np.mean(dk):+.4f}")
