"""T177 (ön kayıt hipotez_defteri 2026-11-07 02:4x): AGF (altılı havuzu, ilk ayakta donar) → kapanış ganyanı tahmini."""
import glob, gzip, json, re, numpy as np, pandas as pd
from scipy.optimize import minimize
rng = np.random.default_rng(177)
def dk(s): h, m = str(s).split(":")[:2]; return int(h) * 60 + int(m)
TM = pd.concat([pd.read_csv(f, usecols=["tarih", "hipodrom", "kosu", "no", "ganyan", "sira", "kosmadi"]) for f in sorted(glob.glob("data/temiz/2026-1*.csv.gz"))])
TM = TM[(TM.kosmadi != True) & TM.ganyan.notna()]
R = []
for f in sorted(glob.glob("data/agf_zaman/2026-*.csv.gz")):
    gun = f[-17:-7]
    if gun > "2026-11-06": continue
    A = pd.read_csv(f); A["t"] = A.saat.map(dk)
    try: x = json.load(gzip.open(f"data/atyarisi/{gun}.json.gz"))
    except Exception: continue
    for hh, L in (x.get("program") or {}).items():
        saat = {int(r["number"]): r.get("hour") for r in L or []}
        for r in L or []:
            for m in re.findall(r"(\d)\. 6'LI GANYAN bu koşudan başlar", str(r.get("bets"))):
                ilk = int(r["number"]); kes = dk(saat.get(ilk) or "99:99")
                for kn in range(ilk, ilk + 6):
                    a = A[(A.hipodrom == hh) & (A.kosu == kn)]; t_ = TM[(TM.tarih == gun) & (TM.hipodrom == hh) & (TM.kosu == kn)]
                    if a.empty or len(t_) < 4 or not (t_.sira == 1).any(): continue
                    once = a[a.t < kes]
                    if once.empty: continue
                    c = once.sort_values("t").groupby("no").agf.last(); f0 = a.sort_values("t").groupby("no").agf.first()
                    t_ = t_[t_.no.isin(c.index)]
                    if len(t_) < 4 or not (t_.sira == 1).any(): continue
                    ac = np.array([c[n] for n in t_.no], float); a0 = np.array([f0[n] for n in t_.no], float)
                    if (ac <= 0).any() or (a0 <= 0).any(): continue
                    pk = (1 / t_.ganyan.values); pk = pk / pk.sum()
                    R.append(dict(gun=gun, alt=m, ayak=kn - ilk + 1, P0=ac / ac.sum(), mom=ac / a0, pk=pk, w=int(np.argmax(t_.sira.values == 1)), ilk_dk=kes - once.t.min()))
print("ayak-koşu:", len(R), "gün:", len({r['gun'] for r in R}), "| momentum ≠ 1 olan koşu oranı:", round(np.mean([np.any(np.abs(r['mom'] - 1) > 1e-6) for r in R]), 3), "| ilk görüntü kesimden ort.", round(np.mean([r['ilk_dk'] for r in R])), "dk önce")
def pred(r, lam, mu):
    q = r["P0"] * np.power(r["mom"], lam) * np.exp(mu * np.log(r["P0"])); return q / q.sum()
def ll(rs, lam, mu): return np.array([np.log(max(pred(r, lam, mu)[r["w"]], 1e-9)) for r in rs])
def kl(rs, lam, mu): return np.array([(r["pk"] * np.log(r["pk"] / pred(r, lam, mu))).sum() for r in rs])
tr = [r for r in R if r["gun"] <= "2026-10-24"]; te = [r for r in R if r["gun"] > "2026-10-24"]
def fit(mask):
    v = minimize(lambda v: -ll(tr, v[0] * mask[0], v[1] * mask[1]).sum() + 2 * (v @ v), np.zeros(2), method="L-BFGS-B").x; return v * mask
def boot(d, g):
    s = pd.Series(d).groupby(np.asarray(g)).agg(["sum", "size"]); ug = s.index.values
    return np.percentile([(lambda q: s.loc[q, "sum"].sum() / s.loc[q, "size"].sum())(rng.choice(ug, len(ug))) for _ in range(3000)], [2.5, 97.5])
g_ = [r["gun"] for r in te]; base = ll(te, 0, 0); kb = kl(te, 0, 0)
print(f"eğitim {len(tr)} / test {len(te)} ayak-koşu")
for ad, mask in (("P3 momentum + eğim (BİRİNCİL)", np.array([1.0, 1.0])), ("P1 yalnız momentum", np.array([1.0, 0.0])), ("P2 yalnız eğim", np.array([0.0, 1.0]))):
    lam, mu = fit(mask); d = ll(te, lam, mu) - base; lo, hi = boot(d, g_)
    print(f"{ad}: λ={lam:+.3f} μ={mu:+.3f} | test kazanan LL farkı {d.mean():+.4f} [{lo:+.4f}; {hi:+.4f}] | kapanışa uzaklık KL {kl(te, lam, mu).mean():.4f} (P0 {kb.mean():.4f})")
print("ayak sırasına göre kapanışa uzaklık (P0, KL):", {j: round(float(np.mean([kl([r], 0, 0)[0] for r in te + tr if r['ayak'] == j])), 4) for j in range(1, 7)})
