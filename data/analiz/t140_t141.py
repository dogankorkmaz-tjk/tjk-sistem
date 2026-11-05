"""T140 ablasyon + T141 LightGBM piyasasız. ÜRETİM DOSYALARINA YAZMAZ."""
import sys, numpy as np, pandas as pd, time, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "."); from tjk import golge as GL
from tjk.calistir import yukle_model
import lightgbm as lgb
rng = np.random.default_rng(140)
def log(*a): print(*a, flush=True)
M = yukle_model(); d = pd.read_pickle("/tmp/claude-0/jason_d.pkl")
d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
d = d[d.kazandi.notna() & d.lp.notna()].copy().reset_index(drop=True)
base = M["feat"] + GL.EK
G = {"form": ["f_hwin","f_hpct3","f_hpctson","f_ilk","f_gun","f_s6ort","f_s6top3","f_s6n","f_kgs","f_hippct"],
     "jokey": ["f_jwin","f_jdeg","f_cift","f_jgen100"], "kilo_hnd": ["f_kilo","f_apr","f_kilodeg","f_hnd"], "hiz": ["f_sonrel","f_fig3"],
     "mesafe": ["f_gun_kisa","f_gun_orta","f_gun_uzun","f_dp150_m"], "sahip_baba": ["f_twin","f_swin","f_bwin"],
     "t2_t3": ["f_t2_d","f_t2_a","f_t2_k","f_t3_a","f_t3_e","f_t3_d"], "kapi_yas": ["f_no","f_yas","f_st","f_st1"]}
assert sorted(sum(G.values(), [])) == sorted(base), set(base) ^ set(sum(G.values(), []))
key = [d.tarih, d.hipodrom, d.kosu]
REL = []
for f in base:
    n = f + "_r"; d[n] = d[f] - d.groupby(key)[f].transform("mean"); REL.append(n)
d = d.copy()
def fit(tr, feat, sifir=True):
    t = tr.copy()
    if sifir: t["lp"] = 0.0
    th, mu, sd, nk = GL._fit(t, feat, M.get("lam", 100.0))
    return {"feat": feat, "mu": {k: float(v) for k, v in mu.items()}, "sd": {k: float(v) for k, v in sd.items()}, "w": [float(x) for x in th]}
def zs(te, A): return GL.z2(te, A)
def raceLL(te, s):
    t = te[["tarih", "hipodrom", "kosu", "kazandi"]].copy(); t["s"] = np.asarray(s)
    k = [t.tarih, t.hipodrom, t.kosu]; m = t.groupby(k, sort=False).s.transform("max"); t["e"] = np.exp(t.s - m)
    Z = t.groupby(k, sort=False).e.transform("sum"); t["lp_"] = t.s - m - np.log(Z); w = t[t.kazandi == 1]
    return w.groupby(["tarih", "hipodrom", "kosu"]).lp_.sum()
def nullLL(te):
    n = te.groupby(["tarih", "hipodrom", "kosu"]).size(); return -np.log(n)
PRM = dict(objective="binary", num_leaves=15, learning_rate=0.03, min_data_in_leaf=200, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, seed=141, verbose=-1, num_threads=2)
FG = base + REL
aylar = [f"2025-{m:02d}" for m in (10, 11, 12)] + [f"2026-{m:02d}" for m in range(1, 11)]
R = []; OOS = []; names = ["P", "Pk", "J", "Z", "G"] + ["Zc_" + g for g in G] + ["Zo_" + g for g in G]
for ay in aylar:
    t0 = time.time(); son = (pd.Timestamp(ay + "-01") - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    tr = d[d.tarih <= son]; te = d[d.tarih.str[:7] == ay].copy()
    if te.empty: continue
    Pk = fit(tr, ["f_lp2"], False); J = fit(tr, base + GL.LPEK, False); Zm = fit(tr, base, True)
    lp2 = lambda A: A["w"][0] * te.lp.values + float(A["w"][1 + A["feat"].index("f_lp2")] / A["sd"]["f_lp2"]) * te.lp.values ** 2
    S = {"P": te.lp.values, "Pk": lp2(Pk), "J": lp2(J) + GL.z2(te, J), "Z": zs(te, Zm)}
    # LightGBM
    val0 = (pd.Timestamp(son) - pd.Timedelta(days=60)).strftime("%Y-%m-%d"); a = tr[tr.tarih <= val0]; b = tr[tr.tarih > val0]
    m1 = lgb.train(PRM, lgb.Dataset(a[FG], a.kazandi), 600, valid_sets=[lgb.Dataset(b[FG], b.kazandi)], callbacks=[lgb.early_stopping(50, verbose=False)])
    nb = max(m1.best_iteration, 50); m2 = lgb.train(PRM, lgb.Dataset(tr[FG], tr.kazandi), nb)
    p = np.clip(m2.predict(te[FG]), 1e-6, 1 - 1e-6); te["pg"] = p
    te["pgn"] = te.pg / te.groupby([te.tarih, te.hipodrom, te.kosu]).pg.transform("sum"); S["G"] = np.log(te.pgn.values)
    # ablasyon
    for g, cols in G.items():
        S["Zc_" + g] = zs(te, fit(tr, [f for f in base if f not in cols], True))
        S["Zo_" + g] = zs(te, fit(tr, cols, True))
    df = pd.concat({k: raceLL(te, v) for k, v in S.items()}, axis=1); df["null"] = nullLL(te).reindex(df.index); df = df.dropna()
    for (t, h, k), r in df.iterrows(): R.append((ay, t, *[r[c] for c in names], r["null"]))
    te["sg"] = np.log(te.pgn.values); OOS.append((ay, te[["tarih", "hipodrom", "kosu", "no", "kazandi", "lp", "f_lp2", "sg"]].copy()))
    log(ay, "n", len(df), " ".join("%s %.4f" % (c, df[c].mean()) for c in ["P", "Pk", "J", "Z", "G"]), "ağaç", nb, "%d sn" % (time.time() - t0))
D = pd.DataFrame(R, columns=["ay", "gun"] + names + ["null"]); ud, inv = np.unique(D.gun, return_inverse=True); N = np.bincount(inv)
def ci(x):
    x = np.asarray(x); S_ = np.bincount(inv, weights=x); bs = []
    for _ in range(1000):
        k = np.bincount(rng.integers(0, len(ud), len(ud)), minlength=len(ud)); bs.append((k * S_).sum() / (k * N).sum())
    lo, hi = np.percentile(bs, [2.5, 97.5]); return x.mean(), lo, hi
log("=== T141 koşu", len(D), "gün", len(ud), " ort. kazanan log-olasılığı:", " ".join("%s %.4f" % (c, D[c].mean()) for c in ["P", "Pk", "J", "Z", "G"]), "null %.4f" % D["null"].mean())
for a, b, ad in (("G", "P", "G−P (ANA HEDEF)"), ("G", "Pk", "G−Pk"), ("G", "Z", "G−Z"), ("Z", "P", "Z−P")):
    m, lo, hi = ci(D[a] - D[b]); log("  %-18s %+.5f [%+.5f, %+.5f]" % (ad, m, lo, hi), "-> HEDEF SAĞLANDI" if (a, b) == ("G", "P") and lo > 0 else "")
log("pseudo-R2 (1−LL/null): " + " ".join("%s %.4f" % (c, 1 + D[c].mean() / (-D["null"].mean())) for c in ["P", "J", "Z", "G"]))
log("=== T140 ablasyon (nat/koşu; 'çıkarınca kayıp' = Z(tümü)−Z(grupsuz) ; 'yalnız' = Z(yalnız grup)−null)")
for g in G:
    m1, l1, h1 = ci(D["Z"] - D["Zc_" + g]); m2, l2, h2 = ci(D["Zo_" + g] - D["null"])
    log("  %-11s çıkarınca kayıp %+.5f [%+.5f, %+.5f] | yalnız %+.5f [%+.5f, %+.5f]" % (g, m1, l1, h1, m2, l2, h2))
# birleşik (piyasa + G): önceki OOS aylarında uydur
log("=== T141 birleşik (piyasa + log p_G), önceki aylarda uydurulan 3 parametre")
rows = []
for i in range(3, len(OOS)):
    tr = pd.concat([x[1] for x in OOS[:i]]); te = OOS[i][1]
    th, mu, sd, _ = GL._fit(tr.assign(lp=tr.lp), ["sg", "f_lp2"], 1.0)
    X = ((te[["sg", "f_lp2"]] - pd.Series(mu)) / pd.Series(sd)).values; s = th[0] * te.lp.values + X @ th[1:]
    ll = raceLL(te, s); rows.append((OOS[i][0], ll, th))
    log("  ", OOS[i][0], "w0 %.3f b(sg,std) %.3f a(lp2,std) %.3f" % (th[0], th[1], th[2]))
JG = pd.concat([r[1] for r in rows]); idx = JG.index
DD = D.copy(); DD["key"] = list(zip(DD.gun, [None] * len(DD)))
# koşu anahtarıyla hizala
Dk = pd.DataFrame(R, columns=["ay", "gun"] + names + ["null"])
keyidx = []
for ay, t in [(x[0], x[1]) for x in OOS]: pass
tmp = {}
for ay, te in OOS:
    pass
log("birleşik değerlendirme: koşu", len(JG))
J_all = pd.concat([raceLL(te, te.lp.values * 0) for _, te in OOS[3:]])  # yer tutucu (hizalama için)
Jref = {}
for ay, te in OOS[3:]:
    pass
sel = D[D.ay.isin([r[0] for r in rows])].copy(); sel["JG"] = JG.values[:len(sel)] if len(JG) == len(sel) else np.nan
if sel.JG.notna().all():
    ud2, inv2 = np.unique(sel.gun, return_inverse=True); N2 = np.bincount(inv2)
    def ci2(x):
        x = np.asarray(x); S_ = np.bincount(inv2, weights=x); bs = []
        for _ in range(1000):
            k = np.bincount(rng.integers(0, len(ud2), len(ud2)), minlength=len(ud2)); bs.append((k * S_).sum() / (k * N2).sum())
        lo, hi = np.percentile(bs, [2.5, 97.5]); return x.mean(), lo, hi
    for a, b, ad in (("JG", "Pk", "J_G−Pk"), ("JG", "J", "J_G−J (Jason'a göre)")):
        m, lo, hi = ci2(sel[a] - sel[b]); log("  %-22s %+.5f [%+.5f, %+.5f]  koşu %d" % (ad, m, lo, hi, len(sel)))
else: log("birleşik hizalama tutmadı (koşu sayıları farklı): JG", len(JG), "sel", len(sel))
log("bitti")
