"""T212: numara kalabalığı. Ön kayıt: hipotez_defteri T212."""
import os, sys, json, glob
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, KOK)
_ns = {"__file__": os.path.join(KOK, "data", "analiz", "t192.py")}
exec(compile(open(os.path.join(KOK, "data", "analiz", "t192.py")).read().split("feat = M[")[0], "h", "exec"), _ns)
d, np, pd = _ns["d"], _ns["np"], _ns["pd"]
d = d[~d.kosmadi.fillna(False).astype(bool)]; d = d[d.p_piyasa > 0]
GP = [1, 0.87, 0.74, 0.74, 0.74]
P = {}
for k, g in d.groupby(["tarih", "hipodrom", "kosu"]):
    if len(g) >= 5: P[k] = dict(zip(g.no.astype(int), g.p_piyasa.values))
o = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(KOK, "data", "odeme", "*.csv.gz")))])
BIRIM = {"SIRALI İKİLİ": 1.0, "TABELA BAHİS": 1.5, "SIRALI 5 Lİ BAHİS": 1.25}
dev = o[o.tur.str.contains("SIRALI 5 Lİ BAHİS DEVİR")]; devset = set(zip(dev.tarih, dev.hipodrom))
# devirli havuz: aynı gün/hipodromda önceki sıralı 5'li koşusu DEVİR olduysa (basit: aynı hipodrom-günde kosu sırası) → o koşudan sonraki ilk 5'li koşu hariç
o5 = o[o.tur == "SIRALI 5 Lİ BAHİS"].sort_values(["tarih", "hipodrom", "kosu"]); dkos = dev.groupby(["tarih", "hipodrom"]).kosu.apply(list).to_dict()
def devirli(t, h, k):
    return any(x < k and not any(y for y in [] ) for x in dkos.get((t, h), []))
rows = []
for tur, b in BIRIM.items():
    x = o[o.tur == tur]
    for t, h, k, kombo, tut in zip(x.tarih, x.hipodrom, x.kosu, x.kombo, x.tutar):
        if tur == "SIRALI 5 Lİ BAHİS" and devirli(t, h, k): continue
        pk = P.get((t, h, k))
        if pk is None or not tut or tut <= 0: continue
        try: nos = [int(v) for v in str(kombo).split("/")]
        except Exception: continue
        if any(n not in pk for n in nos): continue
        W = [{n: pk[n] ** GP[i] for n in pk} for i in range(len(nos))]; A = 1.0; used = 0.0
        for i, n in enumerate(nos):
            T = sum(W[i].values()) - sum(W[i][m] for m in nos[:i]); A *= W[i][n] / T
        pop = sum(1 for n in nos if n == 7 or n <= 3); ctrl = sum(1 for n in nos if n >= 10)
        rows.append(dict(tur=tur, tarih=t, lq=np.log(tut / b * A), la=np.log(A), x=pop, xk=ctrl))
R = pd.DataFrame(rows); print(R.groupby("tur").size().to_dict(), flush=True)
rng = np.random.default_rng(2120)
def ols(df, col):
    X = np.column_stack([np.ones(len(df)), df[col].values, df.la.values]); y = df.lq.values; return np.linalg.lstsq(X, y, rcond=None)[0][1]
def boot(df, col):
    b = ols(df, col); u, inv = np.unique(df.tarih.values, return_inverse=True); nd = len(u); gi = [np.where(inv == i)[0] for i in range(nd)]; out = []
    for _ in range(2000):
        idx = np.concatenate([gi[i] for i in rng.integers(0, nd, nd)]); out.append(ols(df.iloc[idx], col))
    return {"beta": float(b), "GA95": [float(v) for v in np.percentile(out, [2.5, 97.5])], "n": int(len(df))}
res = {}
for tur in BIRIM:
    df = R[R.tur == tur]
    if len(df) < 300: continue
    yil = pd.to_datetime(df.tarih).dt.year.values
    res[tur] = {"tum": boot(df, "x"), "2023-24": boot(df[yil <= 2024], "x"), "2025+": boot(df[yil >= 2025], "x"), "kontrol_x>=10_tum": boot(df, "xk"), "ort_x": float(df.x.mean())}
    print(tur, json.dumps(res[tur]), flush=True)
json.dump(res, open(os.path.join(KOK, "data", "analiz", "t212.json"), "w"), indent=1, ensure_ascii=False)
