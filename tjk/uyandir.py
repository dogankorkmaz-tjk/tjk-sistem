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


def _koşular():
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
                    R.append((d["tarih"], w[0], s))
    return R


def hesapla():
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
