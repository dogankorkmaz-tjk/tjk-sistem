"""T175 (ön kayıt hipotez_defteri 2026-11-07 02:2x): koşu türü — sürpriz oranı, bahis ROI'si, türe özgü yeniden ağırlık."""
import gzip, json, glob, pickle, numpy as np, pandas as pd
from scipy.optimize import minimize
rng = np.random.default_rng(175)
def tur(s):
    s = str(s); t = s.split("/")[0].strip().split(" ")[0].upper()
    if t.startswith("MAIDEN"): return "Maiden"
    if t.startswith("ŞARTLI"): return "Şartlı"
    if t.startswith("HANDIKAP") or t.startswith("HANDİKAP"): return "Handikap"
    if t.startswith("KV"): return "KV"
    if t.startswith("SATIŞ"): return "Satış"
    return "Grup/diğer"
TY = {}
for f in sorted(glob.glob("data/atyarisi/2025-1*.json.gz")) + sorted(glob.glob("data/atyarisi/2026-*.json.gz")):
    try: x = json.load(gzip.open(f))
    except Exception: continue
    gun = x.get("tarih") or f.split("/")[-1][:10]
    for h, L in (x.get("program") or {}).items():
        for r in L or []:
            try: TY[(gun, h, int(r["number"]))] = (tur(r.get("typeDescription")), "Arap" if "Arap" in str(r.get("groupName")) else "İngiliz")
            except Exception: pass
print("tür kaydı", len(TY))
AYLAR = ["2025-10", "2025-11", "2025-12"] + [f"2026-{m:02d}" for m in range(1, 11)]
TM = pd.concat([pd.read_csv(f, usecols=["tarih", "hipodrom", "kosu", "no", "ganyan", "kosmadi"]) for f in sorted(glob.glob("data/temiz/202[56]-*.csv.gz"))])
TM = TM[TM.kosmadi != True]; GN = {(r.tarih, r.hipodrom, int(r.kosu), int(r.no)): float(r.ganyan) for r in TM.itertuples() if r.ganyan == r.ganyan}
KOS = []; GAN = []
for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb"))
    for i, key in enumerate(c["keys"]):
        k3 = (key[0], key[1], int(key[2])); nos = list(c["nos"][i]); n = len(nos)
        s = np.array(c["S3"][i][:n]); lm = np.array(c["L0"][i][:n]); p = np.exp(s - s.max()); p /= p.sum(); pm = np.exp(lm - lm.max()); pm /= pm.sum()
        t_, irk = TY.get(k3, ("bilinmiyor", "?")); mr = np.argsort(np.argsort(-pm)) + 1
        KOS.append(dict(gun=key[0], key=k3, tur=t_, irk=irk, n=n, s=s, lm=lm, sur3=bool((mr[:3] > 3).any()), sur5=bool((mr[:5] > 5).any()) if n >= 6 else np.nan,
                        favkaz=bool(mr[0] == 1)))
        g = np.array([GN.get(k3 + (x,), np.nan) for x in nos])
        if not np.isnan(g).any():
            ev = p * g; j = int(np.argmax(ev))
            if ev[j] >= 1.2: GAN.append(dict(gun=key[0], key=k3, S=1.0, r=g[j] * (j == 0)))
K = pd.DataFrame(KOS); TYP = dict(zip(K.key, K.tur)); IRK = dict(zip(K.key, K.irk)); NAT = dict(zip(K.key, K.n))
print("koşu", len(K), "| tür bilinmeyen", int((K.tur == "bilinmiyor").sum()))
print("=== A) türe göre sürpriz (favori-dışı at ilk 3'te / ilk 5'te), favori kazanma")
print(K.groupby("tur").agg(kosu=("gun", "size"), ort_at=("n", "mean"), surpriz3=("sur3", "mean"), surpriz5=("sur5", "mean"), favori_kazanir=("favkaz", "mean")).round(3).to_string())
print(K.groupby("irk").agg(kosu=("gun", "size"), surpriz3=("sur3", "mean"), favori_kazanir=("favkaz", "mean")).round(3).to_string())
B = {"ganyan değer (T159)": pd.DataFrame(GAN)}
d = pickle.load(open("/tmp/claude-0/t169b.pkl", "rb")); x = d[(d.tur == "si") & (d.tip == "kombine") & (d.S > 0)]; B["sıralı ikili kombine"] = pd.DataFrame(dict(gun=x.gun, key=x.key, S=x.S, r=x.r))
d = pickle.load(open("/tmp/claude-0/t169.pkl", "rb")); x = d[(d.tur == "ik") & (d.tip == "kombine") & (d.U == 0.75) & (d.S > 0)]; B["ikili kombine"] = pd.DataFrame(dict(gun=x.gun, key=x.key, S=x.S, r=x.r))
d, OWN = pickle.load(open("/tmp/claude-0/t170_kayit.pkl", "rb")); KB = {3: 1.0, 5: 1.0}
for Kk, ad in ((3, "üçlü kombine"), (5, "sıralı 5'li kombine")):
    x = d[(d.K == Kk) & (d.tip == "kombine") & (d.th == 1.2) & (d.B == 1000) & (d.S > 0)].copy()
    N = x.hip.map(OWN).astype(float) * KB[Kk] + x.carry; W = np.maximum(1.0, N / np.where(x.tutar > 0, x.tutar, np.nan))
    g = np.where(x.devir, N + 0.75 * x.S, x.u * (N + 0.75 * x.S) / (W + x.u)); x["r"] = np.where(x.u > 0, np.nan_to_num(g), 0.0)
    B[ad] = pd.DataFrame(dict(gun=x.gun, key=list(zip(x.gun, x.hip, x.kosu)), S=x.S, r=x.r))
def roi(y): return y.r.sum() / y.S.sum() - 1 if len(y) and y.S.sum() > 0 else np.nan
def ci(y, q=(2.5, 97.5)):
    g_ = y.groupby("gun").agg(m=("S", "sum"), r=("r", "sum")); ug = g_.index.values
    if len(ug) < 5: return (np.nan, np.nan)
    bs = [(lambda s_: g_.r[s_].sum() / g_.m[s_].sum() - 1)(rng.choice(ug, len(ug))) for _ in range(2000)]; return tuple(np.percentile(bs, q))
def fark(a, b, q):
    A_ = a.groupby("gun").agg(m=("S", "sum"), r=("r", "sum")); B_ = b.groupby("gun").agg(m=("S", "sum"), r=("r", "sum"))
    J = A_.join(B_, lsuffix="a", rsuffix="b", how="outer").fillna(0); ug = J.index.values; bs = []
    for _ in range(4000):
        j = J.loc[rng.choice(ug, len(ug))]; bs.append(j.ra.sum() / max(j.ma.sum(), 1e-9) - j.rb.sum() / max(j.mb.sum(), 1e-9))
    return np.percentile(bs, q)
print("=== B) bahis ROI'si türe göre (büyük ödemeler dahil)")
for ad, D in B.items():
    D = D.copy(); D["tur"] = [TYP.get(tuple(k), "bilinmiyor") for k in D.key]; D["irk"] = [IRK.get(tuple(k), "?") for k in D.key]; D["n"] = [NAT.get(tuple(k), np.nan) for k in D.key]
    m = D[D.tur == "Maiden"]; o = D[(D.tur != "Maiden") & (D.tur != "bilinmiyor")]
    lo, hi = fark(m, o, [0.5, 99.5])
    print(f"--- {ad}: tümü {roi(D):+.3f} ({len(D)} koşu) | BİRİNCİL Maiden {roi(m):+.3f} ({len(m)} koşu, {int((m.r>0).sum())} isabet) − diğer {roi(o):+.3f} ({len(o)}) = {roi(m)-roi(o):+.3f} [{lo:+.3f}; {hi:+.3f}] (%99) → {'MAIDEN DAHA İYİ' if lo > 0 else 'kanıt yok'}")
    for t_, y in D.groupby("tur"):
        a, b = ci(y); print(f"      {t_:11s} {roi(y):+.3f} [{a:+.3f}; {b:+.3f}] ({len(y)} koşu, {int((y.r>0).sum())} isabet)")
    for t_, y in D.groupby("irk"): print(f"      ırk {t_:7s} {roi(y):+.3f} ({len(y)} koşu)")
    for lab, msk in (("≤10 at", D.n <= 10), ("≥11 at", D.n >= 11)):
        y = D[msk]; print(f"      {lab}: Maiden {roi(y[y.tur=='Maiden']):+.3f} ({int((y.tur=='Maiden').sum())}) | diğer {roi(y[(y.tur!='Maiden')&(y.tur!='bilinmiyor')]):+.3f}")
print("=== C) türe özgü yeniden ağırlık (kazanan): p ∝ exp(a_t·s + b_t·log p_piyasa)")
K["ll0"] = [ (s - s.max())[0] - np.log(np.exp(s - s.max()).sum()) for s in K.s]
tr = K[K.gun <= "2026-04-30"]; te = K[K.gun >= "2026-05-01"]; PAR = {}
def ll(r, a, b):
    z = a * r.s + b * r.lm; z = z - z.max(); return z[0] - np.log(np.exp(z).sum())
for t_, y in tr.groupby("tur"):
    f = lambda v: -sum(ll(r, 1 + v[0], v[1]) for r in y.itertuples()) + 20 * (v @ v)
    PAR[t_] = minimize(f, np.zeros(2), method="L-BFGS-B").x
    print(f"   {t_:11s} eğitim {len(y)} koşu: a = {1+PAR[t_][0]:.3f}, b = {PAR[t_][1]:+.3f}")
dd = np.array([ll(r, 1 + PAR.get(r.tur, np.zeros(2))[0], PAR.get(r.tur, np.zeros(2))[1]) - r.ll0 for r in te.itertuples()]); gg = te.gun.values
S_ = pd.Series(dd).groupby(gg).agg(["sum", "size"]); ug = S_.index.values
bs = [(lambda s_: S_.loc[s_, "sum"].sum() / S_.loc[s_, "size"].sum())(rng.choice(ug, len(ug))) for _ in range(3000)]
lo, hi = np.percentile(bs, [2.5, 97.5])
print(f"BİRİNCİL test ({len(te)} koşu) kazanan log-olabilirlik farkı {dd.mean():+.4f} nats/koşu [{lo:+.4f}; {hi:+.4f}] → {'ADAY' if lo > 0 else 'kanıt yok'}")
for t_, y in te.assign(dd=dd).groupby("tur"): print(f"      {t_:11s} {y.dd.mean():+.4f} ({len(y)} koşu)")
