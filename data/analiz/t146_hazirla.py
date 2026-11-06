"""atyarisi arşivinden (data/atyarisi/*.json.gz) at düzeyi soy/yetiştirici/yaş/satış + pist-hava tablosu üretir -> /tmp/claude-0/ay_oz.pkl, ay_gun.pkl"""
import gzip, json, glob, pandas as pd, numpy as np
R = []; G = []
def hid(code): return str(code).lower().replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c").replace("i̇", "i")
for f in sorted(glob.glob("data/atyarisi/*.json.gz")):
    try: j = json.load(gzip.open(f))
    except Exception: continue
    t = f.split("/")[-1][:10]
    for L in j.get("liste", []) or []:
        h = L.get("hippodrome") or {}; w = L.get("weather") or {}
        for rc in L.get("raceCourse", []) or []:
            G.append((t, hid(h.get("code", "")), rc.get("type"), rc.get("status"), rc.get("weight"), w.get("temperature"), w.get("humidity")))
    for hip, rs in (j.get("program") or {}).items():
        if hip == "karma": continue
        for r in rs or []:
            for x in r.get("horses", []) or []:
                p = x.get("parents") or {}; g = lambda k: ((p.get(k) or {}).get("name"))
                R.append((t, hip, r.get("number"), x.get("number"), x.get("name"), g("father"), g("mother"), g("fatherOfMother"), g("fatherOfFather"),
                          (x.get("breeder") or {}).get("name"), (x.get("owner") or {}).get("name"), x.get("birthdateEpoch"), x.get("salePrice"), r.get("raceCourseType")))
A = pd.DataFrame(R, columns=["tarih", "hipodrom", "kosu", "no", "ad", "baba", "anne", "annebaba", "babababa", "yetistirici", "sahip", "dogum", "satis", "yuzey"])
A["satis"] = pd.to_numeric(A.satis.astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce")
A.to_pickle("/tmp/claude-0/ay_oz.pkl")
D = pd.DataFrame(G, columns=["tarih", "hipodrom", "yuzey", "durum", "agirlik", "sicaklik", "nem"]); D.to_pickle("/tmp/claude-0/ay_gun.pkl")
print("at satırı", len(A), "gün-pist", len(D)); print(A.tail(2).T.to_string()[:600]); print(D.durum.value_counts().head(8).to_dict()); print(D.agirlik.describe().to_dict())
print("satis dolu", A.satis.notna().mean().round(4), "dogum dolu", A.dogum.notna().mean().round(4), "annebaba dolu", A.annebaba.notna().mean().round(4))
