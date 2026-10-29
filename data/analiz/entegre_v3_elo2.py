"""G1-S v3 (Jason özellikleri ortak eğitim) ileri-yürüyüş. Ön kayıt: hipotez_defteri 2026-10-24 12:45."""
import os, sys, random
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_geriye.py")).read().split("aylar = sorted")[0]
exec(compile(src, "entegre_geriye", "exec"))
import pandas as pd
from tjk import golge as GL
from tjk.calistir import yukle_model
from scipy.optimize import minimize, minimize_scalar
Mm = yukle_model(); NOLP = os.environ.get("NOLP", "0") == "1"; FEAT = Mm["feat"] + GL.EK + ([] if NOLP else GL.LPEK); NJ = len(FEAT)
d = pd.read_pickle("/tmp/claude-0/jason_d.pkl"); d["f_lp2"] = np.log(d.p_piyasa.clip(lower=1e-6)) ** 2
import sys as _s, os as _o; _s.path.insert(0, "data/analiz"); import mesafe_pist_ozellik as MP
EXTRA = _o.environ.get("EXTRA", "0") == "1"
d = MP.uygula(d, False)
import elo_ozellik as EL, elo2_ozellik as E2
VAR = _o.environ.get("VAR", "")                       # "", "C", "M": taban = v3 + Elo; VAR ek özellik
d = EL.ekle(d); FEAT = FEAT + EL.EXTRA_FEAT
if VAR:
    d = E2.ekle(d, VAR); FEAT = FEAT + E2.FEAT[VAR]
NJ = len(FEAT)
d = d[d.tarih >= "2023-01-01"]; JD = {}
for key, g in d.groupby(["tarih", "hipodrom", "kosu"], sort=False): JD[key] = (g.no.astype(int).values, np.nan_to_num(g[FEAT].values.astype(float)))
J = pd.read_pickle("/tmp/claude-0/jason_wf.pkl"); JI = {(r.tarih, r.hipodrom, int(r.kosu), int(r.no)): r.z2 for r in J.itertuples()}
keep = []
for r in R:
    q = JD.get((r["key"][0], r["key"][1], int(r["key"][2])))
    if q is None: continue
    ix = {n: i for i, n in enumerate(q[0])}
    if any(n not in ix for n in r["nos"]): continue
    r["XJ"] = q[1][[ix[n] for n in r["nos"]]]; keep.append(r)
R = keep; print("Jason özellikli koşu", len(R), flush=True)
if NOLP:                                                # piyasa olasılığı (LM) ve f_lp2 çıkarılır; geçmiş-piyasa artığı özellikleri (yalnız önceki koşular) kalır
    _pack0 = pack
    def pack(rl, F=False):
        LM, XX, FF = _pack0(rl, F); return np.where(LM > -1e8, 0.0, LM), XX, FF
def packJ(rl):
    LM, XX, FF = pack(rl, True); XJ = np.zeros((len(rl), M, NJ))
    for k, r in enumerate(rl): XJ[k, :len(r["lm"])] = r["XJ"]
    return LM, XX, FF, XJ
def fitJ(rl, l2=30.0, lj=50.0):
    LM, XX, _, XJ = packJ(rl); msk = LM > -1e8; mu = XJ[msk].mean(0); sd = XJ[msk].std(0) + 1e-9; Z = np.where(msk[..., None], (XJ - mu) / sd, 0.0)
    def f(t):
        s = np.where(msk, t[0] * LM + XX @ t[1:10] + Z @ t[10:10 + NJ], -1e9); out, ds, dg = steps(s, np.r_[1.0, t[10 + NJ:14 + NJ]])
        g = np.r_[(ds * LM.clip(-50, 0)).sum(), np.einsum("nm,nmk->k", ds, XX) + 2 * l2 * t[1:10], np.einsum("nm,nmk->k", ds, Z) + 2 * lj * t[10:10 + NJ], dg]
        return sum(o.sum() for o in out) + l2 * (t[1:10] @ t[1:10]) + lj * (t[10:10 + NJ] @ t[10:10 + NJ]), g
    t0 = np.zeros(14 + NJ); t0[0] = 1; t0[10 + NJ:] = 1
    return minimize(f, t0, jac=True, method="L-BFGS-B", options={"maxiter": 400}).x, mu, sd
def scoreJ(rl, tm):
    t, mu, sd = tm; LM, XX, FF, XJ = packJ(rl); msk = LM > -1e8; Z = np.where(msk[..., None], (XJ - mu) / sd, 0.0)
    return np.where(msk, t[0] * LM + XX @ t[1:10] + Z @ t[10:10 + NJ], -1e9), np.r_[1.0, t[10 + NJ:14 + NJ]], FF
def fit2S(S0, FF, l2=20.0):
    msk = S0 > -1e8; mu = FF[msk].mean(0); sd = FF[msk].std(0) + 1e-9; Z = (FF - mu) / sd; N = len(S0); idx = np.arange(N)
    def f(b):
        s = S0 + Z @ b; s = np.where(msk, s, -1e9); s -= s.max(1, keepdims=True); e = np.exp(s); p = e / e.sum(1, keepdims=True); dd = p.copy(); dd[idx, 0] -= 1
        return -np.log(p[idx, 0] + 1e-12).sum() + l2 * (b @ b), np.einsum("nm,nmk->k", dd, Z) + 2 * l2 * b
    return minimize(f, np.zeros(7), jac=True, method="L-BFGS-B").x, mu, sd
def ev(S, gam):
    out, _, _ = steps(S, gam); return np.cumsum(np.array(out), axis=0).T                      # (N, 5)
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if os.environ.get("TESTBAS","2026-04") <= a <= os.environ.get("TESTSON","9999")]
RES = {}; OOS = {}                                     # OOS: ay -> (S_v2, zJ-lookup) for stacking c
for a in test:
    _cp = "/tmp/claude-0/cache_%s_%s.pkl" % ((VAR or "0") + ("N" if NOLP else ""), a)      # ortam yeniden başlayınca kaldığı aydan devam
    if os.path.exists(_cp) and os.environ.get("NOCACHE", "0") != "1":
        import pickle as _pk; RES[a] = _pk.load(open(_cp, "rb")); print(a, "önbellekten", flush=True); continue
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    t1 = fit1(tr, 30.0); bg = fit2([r for r in tr if r["F"] is not None], t1)
    LMt, XXt, FFt = pack(te, True); S2 = np.where(LMt > -1e8, t1[0] * LMt + XXt @ t1[1:10] + ((FFt - bg[1]) / bg[2]) @ bg[0], -1e9)
    Z = np.zeros_like(S2)
    for k, r in enumerate(te):
        for i, n in enumerate(r["nos"]): Z[k, i] = JI.get((r["key"][0], r["key"][1], int(r["key"][2]), n), 0.0)
    tm = fitJ(tr); S3, g3, FF3 = scoreJ(te, tm)
    # v3: galop ikinci aşama, ofset = Jason-dahil v3 aşama 1 (galop dönemi koşular, kendi eğitim ofseti)
    trg = [r for r in tr if r["F"] is not None]; S3tr, _, FF3tr = scoreJ(trg, tm); bg3 = fit2S(S3tr, FF3tr); S3g = S3 + ((FF3 - bg3[1]) / bg3[2]) @ bg3[0]
    RES[a] = dict(v2=ev(S2, np.r_[1.0, t1[10:14]]), v3=ev(S3g, g3), v3_galopsuz=ev(S3, g3), S3=S3, keys=[r["key"] for r in te], nos=[r["nos"] for r in te], gun=[r["gun"] for r in te], S2=S2, S3g=S3g, g3=g3, Z=Z, gam=np.r_[1.0, t1[10:14]], te=te)
    if NOLP:                                            # piyasasız model: referanslar (piyasa-only ve eşit olasılık) aynı koşular için
        L0 = _pack0(te)[0]; RES[a]["ref_mkt"] = ev(L0, np.ones(5)); RES[a]["ref_uni"] = ev(np.where(L0 > -1e8, 0.0, -1e9), np.ones(5))
    RES[a]["L0"] = (_pack0 if NOLP else pack)(te)[0]    # T52: ham log-piyasa (koşu başına, maske -1e9)
    import pickle as _pk; _pk.dump({k_: RES[a][k_] for k_ in ("v3_galopsuz", "gun", "ref_mkt", "ref_uni", "S3", "keys", "nos", "L0") if k_ in RES[a]}, open(_cp, "wb"))
    print(a, "tamam", flush=True)
import pickle; (pickle.dump({a: (RES[a]["ref_mkt"], RES[a]["ref_uni"]) for a in test}, open("/tmp/claude-0/v3_nolp_ref_%s.pkl" % os.environ.get("TESTBAS","2026-04"), "wb")) if NOLP else None); pickle.dump({a: (RES[a]["v3_galopsuz"], RES[a]["gun"]) for a in test}, open("/tmp/claude-0/v3_elo2%s_%s.pkl" % ((VAR or "0") + ("N" if NOLP else ""), os.environ.get("TESTBAS","2026-04")), "wb")); print("kaydedildi", EXTRA, flush=True); sys.exit(0) if os.environ.get("TESTSON") else None
def cat(ays, k): return np.concatenate([RES[a][k] for a in ays]) if k != "gun" else sum([RES[a]["gun"] for a in ays], [])
# yığma (c) 07..10
st = {}
for a in [x for x in test if x >= "2026-07"]:
    ntr = [(x, RES[x]) for x in test if x < a]
    def nll(c): return sum(sum(o.sum() for o in steps(np.where(RES[x]["S2"] > -1e8, RES[x]["S2"] + c * RES[x]["Z"], -1e9), RES[x]["gam"])[0]) for x, _ in ntr) + 20 * c * c
    c = minimize_scalar(nll, bounds=(-3, 3), method="bounded").x
    st[a] = ev(np.where(RES[a]["S2"] > -1e8, RES[a]["S2"] + c * RES[a]["Z"], -1e9), RES[a]["gam"])
random.seed(3)
def rapor(ays, A, B, ad, Bk):
    gun = np.array(sum([RES[a]["gun"] for a in ays], [])); ug = sorted(set(gun)); gi = {g: np.where(gun == g)[0] for g in ug}
    a_ = np.concatenate([A[x] if isinstance(A, dict) else RES[x][A] for x in ays]); b_ = np.concatenate([B[x] if isinstance(B, dict) else RES[x][B] for x in ays])
    print(f"{ad} [{ays[0]}..{ays[-1]}] {len(gun)} koşu")
    for j, n in enumerate(["kazanan", "ikili", "üçlü", "ilk4", "ilk5"]):
        dd = a_[:, j] - b_[:, j]; bs = [dd[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(700)]
        print(f"   {n:8s} {dd.mean():+.4f} [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]")
rapor(test, "v3", "v2", "v3 − v2", None)
rapor(test, "v3_galopsuz", "v2", "v3(galopsuz) − v2", None)
a7 = [x for x in test if x >= "2026-07"]
rapor(a7, "v3", "v2", "v3 − v2", None); rapor(a7, "v3", st, "v3 − yığma", None); rapor(a7, st, "v2", "yığma − v2", None)

import pickle; (pickle.dump({a: (RES[a]["ref_mkt"], RES[a]["ref_uni"]) for a in test}, open("/tmp/claude-0/v3_nolp_ref_%s.pkl" % os.environ.get("TESTBAS","2026-04"), "wb")) if NOLP else None); pickle.dump({a: (RES[a]["v3_galopsuz"], RES[a]["gun"]) for a in test}, open("/tmp/claude-0/v3_elo2%s_%s.pkl" % ((VAR or "0") + ("N" if NOLP else ""), os.environ.get("TESTBAS","2026-04")), "wb")); print("kaydedildi", EXTRA)
