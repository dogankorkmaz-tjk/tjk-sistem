"""T154 (ön kayıt: hipotez_defteri 2026-11-06 12:30): MJP = MJ + sıraya özgü δ (adım j≥1 puanı γ_j·(s + P·δ)).
entegre_v3_elo2.py'yi döngüden önceki kısmına kadar AYNEN çalıştırır (VAR=MJP → MJ özellikleri), sonra yalnız galopsuz v3 aşamasını δ'lı eğitir.
Çıktı biçimi harness ile aynı: /tmp/claude-0/v3_elo2MJP{N}_2025-10.pkl = {ay: (kayıp[N,5] birikimli, gun)}; δ katsayıları t154_delta{N}.json.
Kontrol: PLASE_SIFIR=1 ile δ=0'a kilitlenir → MJ galopsuz çıktısını birebir vermeli (kod doğrulaması)."""
import os, sys, json, pickle
assert os.environ.get("VAR") == "MJP"
_yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_v3_elo2.py")
_src = open(_yol).read().split('aylar = sorted({r["ay"]')[0]
_g = {"__file__": _yol, "__name__": "t154"}; exec(compile(_src, _yol, "exec"), _g)
np = _g["np"]; minimize = _g["minimize"]; R = _g["R"]; packJ = _g["packJ"]; FEAT = _g["FEAT"]; NJ = _g["NJ"]
PF = ["f_t2_d", "f_t2_a", "f_t2_k", "f_t3_a", "f_t3_e", "f_t3_d", "f_s6top3", "f_hpct3", "f_st", "f_kilo", "f_hnd", "f_yas", "f_elo_m"]
IP = [FEAT.index(f) for f in PF]; K = len(IP); SIFIR = os.environ.get("PLASE_SIFIR", "0") == "1"
print("δ özellikleri", PF, "| NJ", NJ, "| sıfır kilidi", SIFIR, flush=True)
def steps2(s, sp, gam, nstep=5):
    N = len(s); idx = np.arange(N); mask = s > -1e8; out = []; ds = np.zeros_like(s); dsp = np.zeros_like(s); dg = np.zeros(nstep - 1)
    for j in range(nstep):
        b = s if j == 0 else sp; g = 1.0 if j == 0 else gam[j]
        z = np.where(mask, g * b, -1e30); z -= z.max(1, keepdims=True); e = np.exp(z); p = e / e.sum(1, keepdims=True)
        out.append(-np.log(p[idx, j] + 1e-12)); d = p.copy(); d[idx, j] -= 1
        if j == 0: ds += d
        else: ds += g * d; dsp += g * d; dg[j - 1] = (d * np.where(mask, b, 0)).sum()
        mask[idx, j] = False
    return out, ds, dsp, dg
def fitP(rl, l2=30.0, lj=50.0):
    LM, XX, _, XJ = packJ(rl); msk = LM > -1e8; mu = XJ[msk].mean(0); sd = XJ[msk].std(0) + 1e-9; Z = np.where(msk[..., None], (XJ - mu) / sd, 0.0); P = Z[..., IP]
    def f(t):
        dl = np.zeros(K) if SIFIR else t[14 + NJ:]
        s = np.where(msk, t[0] * LM + XX @ t[1:10] + Z @ t[10:10 + NJ], -1e9); sp = np.where(msk, s + P @ dl, -1e9)
        out, ds, dsp, dg = steps2(s, sp, np.r_[1.0, t[10 + NJ:14 + NJ]])
        gdl = np.zeros(K) if SIFIR else np.einsum("nm,nmk->k", dsp, P) + 2 * lj * dl
        g = np.r_[(ds * LM.clip(-50, 0)).sum(), np.einsum("nm,nmk->k", ds, XX) + 2 * l2 * t[1:10], np.einsum("nm,nmk->k", ds, Z) + 2 * lj * t[10:10 + NJ], dg, gdl]
        return sum(o.sum() for o in out) + l2 * (t[1:10] @ t[1:10]) + lj * (t[10:10 + NJ] @ t[10:10 + NJ]) + lj * (dl @ dl), g
    t0 = np.zeros(14 + NJ + K); t0[0] = 1; t0[10 + NJ:14 + NJ] = 1
    return minimize(f, t0, jac=True, method="L-BFGS-B", options={"maxiter": 400}).x, mu, sd
def evP(rl, tm):
    t, mu, sd = tm; LM, XX, FF, XJ = packJ(rl); msk = LM > -1e8; Z = np.where(msk[..., None], (XJ - mu) / sd, 0.0)
    dl = np.zeros(K) if SIFIR else t[14 + NJ:]
    s = np.where(msk, t[0] * LM + XX @ t[1:10] + Z @ t[10:10 + NJ], -1e9); sp = np.where(msk, s + Z[..., IP] @ dl, -1e9)
    out, _, _, _ = steps2(s, sp, np.r_[1.0, t[10 + NJ:14 + NJ]]); return np.cumsum(np.array(out), axis=0).T
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if os.environ.get("TESTBAS", "2026-04") <= a <= os.environ.get("TESTSON", "9999")]
N_ = "N" if _g["NOLP"] else ""; ek = "Z" if SIFIR else ""; OUT = {}; DL = {}
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    tm = fitP(tr); OUT[a] = (evP(te, tm), [r["gun"] for r in te]); DL[a] = [float(x) for x in tm[0][14 + NJ:]]
    print(a, "tamam", len(te), "koşu | δ", np.round(tm[0][14 + NJ:], 3).tolist(), flush=True)
pickle.dump(OUT, open(f"/tmp/claude-0/v3_elo2MJP{ek}{N_}_{os.environ.get('TESTBAS', '2026-04')}.pkl", "wb"))
json.dump({"ozellik": PF, "delta": DL}, open(os.path.join(os.path.dirname(_yol), f"t154_delta{ek}{N_}.json"), "w"), indent=1)
print("kaydedildi", flush=True)
