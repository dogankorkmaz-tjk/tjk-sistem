"""T169 (ön kayıt hipotez_defteri 2026-11-07): ikili / sıralı ikili AYRI kuponlar vs KOMBİNE / VİRGÜLLÜ kupon."""
import json, glob, pickle, math, itertools, sys, numpy as np, pandas as pd
rng = np.random.default_rng(169); TH = 1.2; BUT = 100.0
AYLAR = ["2025-10", "2025-11", "2025-12"] + [f"2026-{m:02d}" for m in range(1, 11)]
HMAP = {"DBAKIR": "diyarbakir"}; MUH = {}
for f in glob.glob("data/muh_gecmis/20*.json"):
    t = f[-15:-5]
    for k, v in json.load(open(f)).items():
        h, kn = k.rsplit("-", 1); MUH[(t, HMAP.get(h, h.lower()), int(kn))] = v
OD = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/202[56]-*.csv.gz"))]); ODM = {}
for r in OD[OD.tur.isin(["İKİLİ", "SIRALI İKİLİ"])].itertuples():
    ODM[(r.tarih, r.hipodrom, int(r.kosu), "ik" if r.tur == "İKİLİ" else "si")] = float(r.tutar)
def kombine(cand, val, th, sirali, B):
    """n at kümesi; val(a,b) -> oran. Döner (küme, kombinasyon listesi)."""
    pairs = lambda S: [(a, b) for a in S for b in S if a != b] if sirali else [(a, b) for a, b in itertools.combinations(sorted(S), 2)]
    best = max(((a, b) for a in cand for b in cand if a != b), key=lambda x: val(*x))
    if val(*best) < th: return None
    S = set(best)
    while True:
        cur = set(pairs(S)); sec = None
        for h in cand:
            if h in S: continue
            yeni = [c for c in pairs(S | {h}) if c not in cur]
            if len(cur) + len(yeni) > B: continue
            d = sum(val(*c) - th for c in yeni)
            if d > 0 and (sec is None or d > sec[0]): sec = (d, h)
        if sec is None: break
        S.add(sec[1])
    return S, pairs(S)
def virgullu(cand, val, th, B):
    best = max(((a, b) for a in cand for b in cand if a != b), key=lambda x: val(*x))
    if val(*best) < th: return None
    A, Bs = {best[0]}, {best[1]}
    comb = lambda A, Bs: {(a, b) for a in A for b in Bs if a != b}
    while True:
        cur = comb(A, Bs); sec = None
        for pos in (0, 1):
            for h in cand:
                if h in (A if pos == 0 else Bs): continue
                nw = comb(A | {h}, Bs) if pos == 0 else comb(A, Bs | {h}); yeni = nw - cur
                if len(nw) > B or not yeni: continue
                d = sum(val(*c) - th for c in yeni)
                if d > 0 and (sec is None or d > sec[0]): sec = (d, pos, h)
        if sec is None: break
        (A if sec[1] == 0 else Bs).add(sec[2])
    return (A, Bs), sorted(comb(A, Bs))
R = []
for U in (0.75, 0.5, 1.0):
  for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb"))
    for i, key in enumerate(c["keys"]):
        k3 = (key[0], key[1], int(key[2])); m = MUH.get(k3)
        if not m: continue
        nos = list(c["nos"][i]); n = len(nos); s = c["S3"][i][:n]; g = c["g3"]
        p1 = np.exp(s - s.max()); p1 /= p1.sum(); w2 = np.power(p1, g[1]); kaz = (nos[0], nos[1])
        sp = lambda a, b: p1[nos.index(a)] * w2[nos.index(b)] / (w2.sum() - w2[nos.index(a)])
        cand = [nos[j] for j in np.argsort(-p1)[:9]]
        for tur in ("si", "ik"):
            od = ODM.get(k3 + (tur,))
            if od is None: continue
            Q = {}
            for x in m.get(tur) or []:
                try: a, b, o = int(x[0]), int(x[1]), float(str(x[2]).replace(",", "."))
                except Exception: continue
                if a in nos and b in nos and o > 1: Q[(a, b) if tur == "si" else tuple(sorted((a, b)))] = o
            if not Q: continue
            sir = tur == "si"
            def val(a, b):
                kk = (a, b) if sir else tuple(sorted((a, b))); o = Q.get(kk)
                if o is None: return U
                return (sp(a, b) if sir else sp(a, b) + sp(b, a)) * o
            hitc = (lambda cmb: kaz in cmb) if sir else (lambda cmb: tuple(sorted(kaz)) in cmb)
            base = dict(gun=key[0], key=k3, tur=tur, U=U)
            if U == 0.75:
                ay_sec = [kk for kk in Q if val(*kk) >= TH]
                R.append(dict(base, tip="ayri", S=20.0 * len(ay_sec), r=20.0 * od * (kaz in ay_sec if sir else tuple(sorted(kaz)) in ay_sec), n=len(ay_sec)))
            for tip, fn in (("kombine", lambda: kombine(cand, val, TH, sir, BUT)),) + ((("virgul", lambda: virgullu(cand, val, TH, BUT)),) if sir else ()):
                o_ = fn()
                if o_ is None: R.append(dict(base, tip=tip, S=0.0, r=0.0, n=0)); continue
                _, cmb = o_; cmb = list(cmb); cost = len(cmb); ms = math.ceil(20 / cost) if cost < 20 else 1
                R.append(dict(base, tip=tip, S=cost * ms, r=od * ms * hitc(cmb), n=len(cmb)))
  print("U", U, "tamam", flush=True)
D = pd.DataFrame(R); pickle.dump(D, open("/tmp/claude-0/t169.pkl", "wb"))
def eslesik(a, b, q):
    A = a.groupby("gun").agg(ma=("S", "sum"), ra=("r", "sum")); Bb = b.groupby("gun").agg(mb=("S", "sum"), rb=("r", "sum"))
    J = A.join(Bb, how="outer").fillna(0); J = J[(J.ma > 0) | (J.mb > 0)]; ug = J.index.values
    f = lambda j: (j.ra.sum() / max(j.ma.sum(), 1e-9) - 1, j.rb.sum() / max(j.mb.sum(), 1e-9) - 1)
    ra, rb = f(J); bs = []
    for _ in range(4000):
        j = J.loc[rng.choice(ug, len(ug))]; x, y = f(j); bs.append((x, y, y - x))
    lo, hi = np.percentile(np.array(bs), q, axis=0); return (ra, lo[0], hi[0]), (rb, lo[1], hi[1]), (rb - ra, lo[2], hi[2])
def ozet(x): o = x[x.S > 0]; return f"{len(o)} koşu, ort {o.S.mean():.0f} TL, ort {o.n.mean():.1f} komb, {int((o.r > 0).sum())} isabet"
for tur, ad in (("si", "sıralı ikili"), ("ik", "ikili")):
    a = D[(D.tur == tur) & (D.tip == "ayri")]; b = D[(D.tur == tur) & (D.tip == "kombine") & (D.U == 0.75)]
    A_, B_, F_ = eslesik(a, b, (1.25, 98.75))
    print(f"=== {ad} BİRİNCİL (%97,5) | AYRI {A_[0]:+.3f} [{A_[1]:+.3f}; {A_[2]:+.3f}] ({ozet(a)}) | KOMBİNE {B_[0]:+.3f} [{B_[1]:+.3f}; {B_[2]:+.3f}] ({ozet(b)}) | FARK {F_[0]:+.3f} [{F_[1]:+.3f}; {F_[2]:+.3f}]")
    for U in (0.5, 1.0):
        b2 = D[(D.tur == tur) & (D.tip == "kombine") & (D.U == U)]; _, B2, F2 = eslesik(a, b2, (2.5, 97.5))
        print(f"    duyarlılık listede olmayan oran={U}: KOMBİNE {B2[0]:+.3f} [{B2[1]:+.3f}; {B2[2]:+.3f}] ({ozet(b2)}) fark {F2[0]:+.3f}")
    if tur == "si":
        v = D[(D.tur == tur) & (D.tip == "virgul") & (D.U == 0.75)]; _, V, FV = eslesik(a, v, (2.5, 97.5))
        print(f"    VİRGÜLLÜ: {V[0]:+.3f} [{V[1]:+.3f}; {V[2]:+.3f}] ({ozet(v)}) fark ayrıya göre {FV[0]:+.3f} [{FV[1]:+.3f}; {FV[2]:+.3f}]")
