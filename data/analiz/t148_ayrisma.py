"""T148 piyasa–piyasasız ayrışma (betimsel). t145_oos.pkl okur."""
import numpy as np, pandas as pd
rng = np.random.default_rng(148)
O = pd.read_pickle("/tmp/claude-0/t145_oos.pkl"); O["R"] = np.log(O.pZ.clip(lower=1e-9) / O.pPk.clip(lower=1e-9))
K = ["tarih", "hipodrom", "kosu"]
bins = [-9, -0.5, -0.2, 0.2, 0.5, 9]; lab = ["Z≪piyasa (≤−0,5)", "Z<piyasa (−0,5..−0,2)", "benzer (±0,2)", "Z>piyasa (0,2..0,5)", "Z≫piyasa (≥0,5)"]
O["kov"] = pd.cut(O.R, bins, labels=lab)
print("=== T148 at düzeyi ayrışma: R = log(p_Z / p_Pk). O/E = gözlenen kazanma / beklenen")
def oe(x, col, days):
    ug = np.unique(x.tarih.values); idx = {g: np.where(x.tarih.values == g)[0] for g in ug}
    def stat(ii): a = x.iloc[ii]; return a.kazandi.sum() / a[col].sum()
    b0 = stat(np.arange(len(x))); bs = [stat(np.concatenate([idx[p] for p in rng.choice(ug, len(ug))])) for _ in range(300)]
    return b0, np.percentile(bs, 2.5), np.percentile(bs, 97.5)
for k, x in O.groupby("kov", observed=True):
    a = oe(x, "pPk", 0); b = oe(x, "pJ", 0); z = oe(x, "pZ", 0)
    print("  %-24s n=%5d kazanan=%4d  O/E_piyasa(kalibre) %.2f [%.2f,%.2f] | O/E_Jason %.2f [%.2f,%.2f] | O/E_Z %.2f" % (k, len(x), int(x.kazandi.sum()), *a, *b, z[0]))
print("bitti")
