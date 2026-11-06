"""4. adım (aşama 2 ölçüsü): T150/T151 ile AYNI koşu kümesinde kalibre piyasa (alfa·log p + sıra üstelleri, özellik yok) kaybı; yürüyen aylık 2025-10..2026-10.
Çıktı /tmp/claude-0/kalpiyasa_2025-10.pkl : {ay: (kayıp[N,5], gun listesi, koşu anahtarları)}. Repo kökünden: python3 data/analiz/asama2_kalpiyasa.py"""
import os, pickle
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "entegre_geriye.py")).read().split("aylar = sorted")[0]
exec(compile(src, "entegre_geriye", "exec"))
aylar = sorted({r["ay"] for r in R}); test = [a for a in aylar if "2025-10" <= a <= "2026-10"]; OUT = {}
for a in test:
    tr = [r for r in R if r["ay"] < a]; te = [r for r in R if r["ay"] == a]
    tp = piyasa_gamma(tr); OUT[a] = (evalm(te, tp).T, [r["gun"] for r in te], [r["key"] for r in te]); print(a, len(te), "alfa %.3f" % tp[0], "gamma", [round(x, 3) for x in tp[10:14]], "kazanan %.4f" % OUT[a][0][:, 0].mean(), flush=True)
pickle.dump(OUT, open("/tmp/claude-0/kalpiyasa_2025-10.pkl", "wb")); print("kaydedildi")
