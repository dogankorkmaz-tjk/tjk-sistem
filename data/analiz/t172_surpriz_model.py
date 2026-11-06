"""T172 (ön kayıt hipotez_defteri 2026-11-07 02:1x): sürpriz uzmanı model vs Benter+piyasa (favori olmayan atların ilk K'ya girişi)."""
import os, sys, glob, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, "data/analiz")
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from tjk import besli as BS
from tjk.golge import EK, LPEK
from tjk.calistir import yukle_model
import t162_ozellik as T162
rng = np.random.default_rng(172)
M = yukle_model(); JF = M["feat"] + EK
d = pd.read_pickle("/tmp/claude-0/ozellik_tum.pkl"); d["tarih"] = d.tarih.astype(str)
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
d = T162.ekle(d); SV = T162.FEAT
# yer tutma (T171-B)
t = d[(d.kosmadi != True) & d.sira.notna() & (d.sira > 0) & d.ganyan.notna()][["tarih", "hipodrom", "kosu", "no", "sira", "at", "jokey", "ganyan"]].copy()
t["n"] = t.groupby(["tarih", "hipodrom", "kosu"]).no.transform("size"); t["mr"] = t.groupby(["tarih", "hipodrom", "kosu"]).ganyan.rank(method="average")
t["r"] = (t.mr - t.sira) / (t.n - 1).clip(lower=1); J, A, YT = {}, {}, {}
for gun, x in t.sort_values("tarih").groupby("tarih", sort=True):
    for r in x.itertuples():
        sj, nj = J.get(r.jokey, (0.0, 0)); sa, na = A.get(r.at, (0.0, 0)); YT[(r.tarih, r.hipodrom, int(r.kosu), int(r.no))] = (sj / (nj + 10), sa / (na + 5))
    for r in x[x.sira > 1].itertuples():
        sj, nj = J.get(r.jokey, (0.0, 0)); J[r.jokey] = (sj + r.r, nj + 1); sa, na = A.get(r.at, (0.0, 0)); A[r.at] = (sa + r.r, na + 1)
d["jokey_yer"] = [YT.get((a, b, int(c), int(e)), (0, 0))[0] for a, b, c, e in zip(d.tarih, d.hipodrom, d.kosu, d.no)]
d["at_yer"] = [YT.get((a, b, int(c), int(e)), (0, 0))[1] for a, b, c, e in zip(d.tarih, d.hipodrom, d.kosu, d.no)]
YF = ["jokey_yer", "at_yer"]
d["mesafe_n"] = pd.to_numeric(d.get("mesafe"), errors="coerce")
FX = {(a, b, int(c), int(e)): i for i, (a, b, c, e) in enumerate(zip(d.tarih, d.hipodrom, d.kosu, d.no))}
XALL = d[JF + LPEK + SV + YF + ["mesafe_n"]].to_numpy(float)
print("özellik tablosu hazır", XALL.shape, flush=True)
def topk(w, G, K, ns=4000):
    n = len(w); cnt = np.zeros(n); alive = np.ones((ns, n), bool)
    for k in range(K):
        wk = np.power(np.maximum(w, 1e-12), G[k]) * alive; wk = wk / wk.sum(1, keepdims=True)
        u = rng.random((ns, 1)); ch = (wk.cumsum(1) < u).sum(1).clip(max=n - 1)
        alive[np.arange(ns), ch] = False
    return (~alive).mean(0)
AYLAR = ["2025-10", "2025-11", "2025-12"] + [f"2026-{m:02d}" for m in range(1, 11)]
ROWS = {3: [], 5: []}
for ay in AYLAR:
    c = pickle.load(open(f"/tmp/claude-0/cache_MJ_{ay}.pkl", "rb"))
    for i, key in enumerate(c["keys"]):
        nos = list(c["nos"][i]); n = len(nos)
        if n < 7: continue
        s = np.array(c["S3"][i][:n]); lm = np.array(c["L0"][i][:n]); p = np.exp(s - s.max()); p /= p.sum(); pm = np.exp(lm - lm.max()); pm /= pm.sum()
        g = list(c["g3"]); mr = np.argsort(np.argsort(-pm)) + 1
        idx = [FX.get((key[0], key[1], int(key[2]), int(x))) for x in nos]
        for K in (3, 5):
            if n < K + 3: continue
            PB = topk(p, g, K); PM = topk(pm, BS.G_P, K)
            for j in range(n):
                if mr[j] <= K: continue
                xi = XALL[idx[j]] if idx[j] is not None else np.full(XALL.shape[1], np.nan)
                ROWS[K].append((ay, key[0], f"{key[1]}|{key[2]}", int(j < K), PB[j], PM[j], mr[j], n, *xi))
    print(ay, "tamam", flush=True)
lg = lambda v: np.log(np.clip(v, 1e-4, 1 - 1e-4) / (1 - np.clip(v, 1e-4, 1 - 1e-4)))
ADLAR = JF + LPEK + SV + YF + ["mesafe_n"]
GRUP = {"şerit": SV, "yer tutma": YF, "Jason özellikleri": JF + LPEK}
out = {}
for K in (3, 5):
    D = pd.DataFrame(ROWS[K], columns=["ay", "gun", "kosu", "y", "PB", "PM", "mr", "n"] + ADLAR)
    D["lPB"] = lg(D.PB); D["lPM"] = lg(D.PM)
    base = ["lPB", "lPM"]; full = base + ["mr", "n"] + ADLAR
    P = {"kontrol": [], "uzman": [], **{f"uzman−{gname}": [] for gname in GRUP}}
    for ay in [a for a in AYLAR if a >= "2026-01"]:
        tr = D[D.ay < ay]; te = D[D.ay == ay]
        if not len(te): continue
        lr = LogisticRegression(C=10.0, max_iter=500).fit(tr[base], tr.y)
        P["kontrol"].append(pd.Series(lr.predict_proba(te[base])[:, 1], index=te.index))
        def hgb(cols):
            m = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=300, max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0, random_state=0)
            m.fit(tr[cols], tr.y); return pd.Series(m.predict_proba(te[cols])[:, 1], index=te.index)
        P["uzman"].append(hgb(full))
        for gname, gc in GRUP.items(): P[f"uzman−{gname}"].append(hgb([c for c in full if c not in gc]))
        print(K, ay, "fit", flush=True)
    T = D[D.ay >= "2026-01"].copy()
    for k_, v in P.items(): T[k_] = pd.concat(v).reindex(T.index).clip(1e-4, 1 - 1e-4)
    ll = lambda q: -(T.y * np.log(T[q]) + (1 - T.y) * np.log(1 - T[q]))
    R = T.assign(**{f"ll_{q}": ll(q) for q in P}).groupby(["gun", "kosu"]).sum(numeric_only=True).reset_index()
    def fark(a, b, q):
        x = (R[f"ll_{a}"] - R[f"ll_{b}"]); g_ = x.groupby(R.gun).agg(["sum", "size"]); ug = g_.index.values
        bs = [(lambda s_: g_.loc[s_, "sum"].sum() / g_.loc[s_, "size"].sum())(rng.choice(ug, len(ug))) for _ in range(3000)]
        return x.mean(), np.percentile(bs, q)
    m, (lo, hi) = fark("uzman", "kontrol", [1.25, 98.75])
    print(f"=== ilk {K} (favori olmayan {len(T)} at, {R.shape[0]} koşu, test 2026-01..10) BİRİNCİL: uzman − kontrol log-kayıp {m:+.4f} nats/koşu [{lo:+.4f}; {hi:+.4f}] (%97,5) → {'UZMAN İYİ (aday)' if hi < 0 else 'fark yok / kötü'}")
    print(f"    AUC: Benter tek {roc_auc_score(T.y, T.PB):.3f} | piyasa tek {roc_auc_score(T.y, T.PM):.3f} | kontrol {roc_auc_score(T.y, T.kontrol):.3f} | uzman {roc_auc_score(T.y, T.uzman):.3f}")
    for gname in GRUP:
        m2, (l2, h2) = fark(f"uzman−{gname}", "uzman", [2.5, 97.5]); print(f"    {gname} çıkarılınca uzman kötüleşme {m2:+.4f} [{l2:+.4f}; {h2:+.4f}]")
    T[["gun", "kosu", "y", "PB", "PM", "kontrol", "uzman"]].to_pickle(f"/tmp/claude-0/t172_tahmin_{K}.pkl")
