"""Uyandırma ölçümü: modelin piyasanın gözden kaçırdığı (uzun ganyanlı) atları işaretleme becerisi.
docs/data/gun/*.json içindeki biten koşulardan (kazanan, pp piyasa, pm Bolton, pm2 Jason) hesaplanır -> docs/data/uyandir.json.
Not: pp kapanışa yakın ganyandan gelir; tüyo kaydı (data/tuyo) ilk görülen değerle ayrıca dondurulur.
Ölçüler (ganyan >= 10 olan atlar): işaretlenen (model/piyasa >= eşik) at sayısı, kazanan, piyasanın beklediği kazanan, 1 TL ganyan geri dönüşü;
gerçek sürprizlerde (kazanan, ganyan >= 10) modelin ortalama oranı ve tüm uzun atlardaki ortalama oran."""
import os, glob, json
import numpy as np

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(KOK, "docs", "data")
UZUN = 10.0
ESIKLER = (1.15, 1.30)


def _koşular(meta=False):
    R = []
    for f in sorted(glob.glob(os.path.join(SITE, "gun", "*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for h in d.get("hipodromlar", []):
            for k in h.get("kosular", []):
                s = k.get("sonuc")
                if not s or any(v.get("pm2") is None or v.get("pm") is None or not v.get("pp") for v in s.values()):
                    continue
                w = [n for n, v in s.items() if v.get("sira") == 1]
                if len(w) == 1:
                    R.append((d["tarih"], w[0], s, h.get("id"), k.get("kosu")) if meta else (d["tarih"], w[0], s))
    return R


G_M = [1, 0.80, 0.69, 0.69, 0.69]
G_P = [1, 0.87, 0.74, 0.74, 0.74]


def _ustk(p, G, N=1000, seed=7):
    """Plackett-Luce (konuma göre üstel ağırlık) örneklemesiyle her atın ilk-2/3/5'e girme olasılığı."""
    rng = np.random.default_rng(seed); n = len(p); p = np.maximum(np.asarray(p, float), 1e-9)
    cnt = np.zeros((3, n)); Ks = (2, 3, 5)
    for _ in range(N):
        kal = list(range(n))
        for pos in range(5):
            w = p[kal] ** G[pos]; j = rng.choice(len(kal), p=w / w.sum()); a = kal.pop(j)
            for q, k in enumerate(Ks):
                if pos < k: cnt[q, a] += 1
    return cnt / N


def sirasiz():
    """Sırasız ilk-2/3/5 seçimlerinin isabeti: model (Bolton/Jason) ve piyasa için seçilen K atın gerçekte ilk-K'ya girme sayısı."""
    R = _koşular(); out = {"koşu": len(R), "k": {}}
    acc = {m: {k: {"hit": 0, "n": 0, "bek": 0.0, "tam": 0} for k in (2, 3, 5)} for m in ("Bolton", "Jason", "Piyasa")}
    for _, w, s in R:
        nos = list(s.keys()); n = len(nos)
        if n < 6:
            continue
        sira = {no: s[no]["sira"] for no in nos}
        for m, key, G in (("Bolton", "pm", G_M), ("Jason", "pm2", G_M), ("Piyasa", "pp", G_P)):
            c = _ustk([s[no][key] for no in nos], G)
            for q, k in enumerate((2, 3, 5)):
                sec = np.argsort(-c[q])[:k]
                hit = sum(1 for i in sec if sira[nos[i]] and sira[nos[i]] <= k)
                a = acc[m][k]; a["hit"] += hit; a["n"] += 1; a["bek"] += float(c[q][sec].sum()); a["tam"] += int(hit == k)
    for k in (2, 3, 5):
        out["k"][str(k)] = {m: {"koşu": acc[m][k]["n"], "isabet": acc[m][k]["hit"], "beklenen": round(acc[m][k]["bek"], 1),
                                "tam": acc[m][k]["tam"]} for m in acc}
    json.dump(out, open(os.path.join(SITE, "sirasiz.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return out


AYAR = {2: (0.30, 4), 3: (0.50, 4), 5: (0.35, 7)}     # "sıkı": site ile aynı (ROI taramasına göre)
AYAR_GENIS = {2: (0.20, 5), 3: (0.25, 5), 5: (0.35, 7)}  # "geniş": ilk deneydeki gevşek eşikler
VARYANT = {"siki": AYAR, "genis": AYAR_GENIS}


def _ornekle(p, G, N=1000, seed=7):
    rng = np.random.default_rng(seed); n = len(p); p = np.maximum(np.asarray(p, float), 1e-9)
    S = np.zeros((N, 5), int)
    for t in range(N):
        kal = list(range(n))
        for pos in range(5):
            w = p[kal] ** G[pos]; j = rng.choice(len(kal), p=w / w.sum()); S[t, pos] = kal.pop(j)
    return S


def genis():
    """Ek atlı sırasız kümelerin canlı ölçümü (iki eşik takımı): gerçek ilk-K'nın tamamı kümenin içinde mi (tam kapsama), kümenin kendi beklentisi, ort. at ve kombinasyon."""
    from math import comb
    R = _koşular(meta=True)
    out = {"koşu": 0, "ayar": {v: {str(k): {"esik": x[0], "maks": x[1]} for k, x in A.items()} for v, A in VARYANT.items()}, "k": {v: {} for v in VARYANT}, "son": []}
    acc = {v: {k: {m: {"koşu": 0, "boy": 0, "komb": 0, "tam": 0, "bek": 0.0} for m in ("Bolton", "Jason", "Piyasa")} for k in (2, 3, 5)} for v in VARYANT}
    son = []
    for tarih, w, s, hid, kosu in R:
        nos = list(s.keys()); n = len(nos)
        if n < 6: continue
        out["koşu"] += 1; sira = {no: s[no]["sira"] for no in nos}; kayit = {"gun": tarih, "hip": hid, "kosu": kosu, "k": {v: {} for v in VARYANT}}
        for m, key, G in (("Bolton", "pm", G_M), ("Jason", "pm2", G_M), ("Piyasa", "pp", G_P)):
            S = _ornekle([s[no][key] for no in nos], G)
            for kk in (2, 3, 5):
                say = np.bincount(S[:, :kk].ravel(), minlength=n) / len(S); o = np.argsort(-say)
                gercek = {i for i in range(n) if sira[nos[i]] and sira[nos[i]] <= kk}
                for v, A in VARYANT.items():
                    ku = list(o[:kk]); esik, maks = A[kk]
                    for i in o[kk:]:
                        if len(ku) >= maks or say[i] < esik: break
                        ku.append(i)
                    tam = gercek <= set(ku); bek = float(np.mean([set(r[:kk]) <= set(ku) for r in S]))
                    a = acc[v][kk][m]; a["koşu"] += 1; a["boy"] += len(ku); a["komb"] += comb(len(ku), kk); a["tam"] += int(tam); a["bek"] += bek
                    kayit["k"][v].setdefault(str(kk), {})[m] = {"set": [nos[i] for i in ku], "gercek": sorted(nos[i] for i in gercek), "tam": bool(tam)}
        son.append(kayit)
    for v in VARYANT:
        for kk in (2, 3, 5):
            out["k"][v][str(kk)] = {m: {"koşu": a["koşu"], "ort_at": round(a["boy"] / a["koşu"], 2) if a["koşu"] else None, "ort_komb": round(a["komb"] / a["koşu"], 1) if a["koşu"] else None,
                                        "tam": a["tam"], "beklenen_tam": round(a["bek"], 1)} for m, a in acc[v][kk].items()}
    out["son"] = son[-12:]
    json.dump(out, open(os.path.join(SITE, "sirasiz_genis.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return out


def hesapla():
    sirasiz()
    genis()
    R = _koşular()
    out = {"koşu": len(R), "gun": sorted({r[0] for r in R}), "uzun_esik": UZUN, "model": {}}
    for ad, key in (("Bolton", "pm"), ("Jason", "pm2")):
        uzun = [(n == w, v["g"], v[key] / v["pp"], v["pp"], v["sira"]) for _, w, s in R for n, v in s.items() if v["g"] >= UZUN]
        sur = [u for u in uzun if u[0]]
        m = {"uzun_at": len(uzun), "uzun_oran_ort": round(float(np.mean([u[2] for u in uzun])), 3) if uzun else None,
             "surpriz": len(sur), "surpriz_oran_ort": round(float(np.mean([u[2] for u in sur])), 3) if sur else None,
             "surpriz_oran_med": round(float(np.median([u[2] for u in sur])), 3) if sur else None, "esik": []}
        for e in ESIKLER:
            fl = [u for u in uzun if u[2] >= e]
            m["esik"].append({"esik": e, "at": len(fl), "kazanan": sum(1 for u in fl if u[0]), "ilk3": sum(1 for u in fl if u[4] <= 3),
                              "beklenen": round(float(sum(u[3] for u in fl)), 2),
                              "geri_donus": round(float(sum(u[1] for u in fl if u[0]) / len(fl)), 3) if fl else None})
        out["model"][ad] = m
    json.dump(out, open(os.path.join(SITE, "uyandir.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return out


if __name__ == "__main__":
    print(json.dumps(hesapla(), ensure_ascii=False, indent=1))
