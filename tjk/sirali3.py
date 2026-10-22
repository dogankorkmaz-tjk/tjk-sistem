"""Sıralı 3'lü kolon kuponu (ÜÇLÜ BAHİS) - kâğıt üstü takip, 14 Ekim 2026.
Model 1. at, 2. at ve 3. at için ayrı seçenek kümelerini KENDİ kurar (sıralı 5'lideki gibi): kolon kuponu = A x B x C, atlar tekrarlanamaz.
Her koşu (üçlü bahis oynanan, >=5 at) için Bolton ve Jason kuponları, bütçe başına (BUTCELER = en çok geçerli kombinasyon) yarış başlamadan dondurulur.
Koşu bitince ilk üç sıraya göre değerlendirilir; ödeme data/odeme'deki 'ÜÇLÜ BAHİS' satırından alınır (egzotik testiyle aynı yöntem). Birim fiyat egzotik.BIRIM.
Öneri kuralı (önceden yazıldı, sonradan değişmez): modelin tutma olasılığı / piyasa (AGF) tutma olasılığı >= ESIK_ORAN.
Mevcut hiçbir kural, model ya da kupon değişmez; bu yalnızca ek bir ölçümdür. Çıktılar: data/sirali3/<tarih>.json, docs/data/sirali3.json"""
import os, json, glob, math, itertools
import pandas as pd
from . import egzotik as EG
from . import besli as BS

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data", "sirali3"), os.path.join(KOK, "docs", "data")
BUTCELER = (12, 24, 48)       # en çok geçerli (üç ayrı atlı) kombinasyon
ESIK_ORAN = 1.15
TUR = "ÜÇLÜ BAHİS"
BIRIM = EG.BIRIM[TUR]


def _gecerli(sets):
    return sum(1 for t in itertools.product(*sets) if len(set(t)) == 3)


def _prob(P, sets):
    return sum(P.get(t, 0.0) for t in itertools.product(*sets) if len(set(t)) == 3)


def kupon(p, B):
    """p: atların kazanma olasılıkları (liste). Çok başlangıçlı açgözlü kurucu; her adımda log(kazanılan olasılık)/log(artan kombinasyon) en büyük olan eklenir."""
    n = len(p)
    if n < 5:
        return None
    P = EG._kombolar({i: v for i, v in enumerate(p)}, 3)
    t = sorted(range(n), key=lambda i: -p[i]); aday = t[:min(n, 8)]
    en = None
    for st in ([[t[0]], [t[1]], [t[2]]], [[t[0], t[1]], [t[0], t[1]], [t[2]]], [[t[0], t[1]], [t[0], t[1]], [t[2], t[3]]]):
        sets = [list(x) for x in st]; nv = _gecerli(sets)
        if not (0 < nv <= B):
            continue
        cur = _prob(P, sets)
        while True:
            best = None; bg = 0.0
            for k in range(3):
                for h in aday:
                    if h in sets[k]:
                        continue
                    sets[k].append(h); v2 = _gecerli(sets)
                    if v2 > B or v2 <= nv:
                        sets[k].pop(); continue
                    pr = _prob(P, sets); sets[k].pop()
                    g = math.log(pr / cur) / math.log(v2 / nv)
                    if g > bg:
                        bg, best = g, (k, h, pr, v2)
            if not best:
                break
            sets[best[0]].append(best[1]); cur = best[2]; nv = best[3]
        if en is None or cur > en[1] + 1e-12:
            en = ([list(s) for s in sets], cur)
    return en


def _odeme(tarih):
    try:
        o = pd.read_csv(os.path.join(KOK, "data", "odeme", tarih[:7] + ".csv.gz"))
        return o[(o.tarih == tarih) & (o.tur == TUR)]
    except Exception:
        return pd.DataFrame()


def guncelle(obj, simdi=None):
    tarih = obj["tarih"]; os.makedirs(VERI, exist_ok=True)
    yol = os.path.join(VERI, tarih + ".json")
    kay = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    if simdi is None:
        try:
            from . import ortak as O
            simdi = O.tr_simdi().strftime("%H:%M")
        except Exception:
            simdi = None
    od = None
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            anahtar = f"{h['id']}|{k['kosu']}"; saat = k.get("saat") or "99:99"; c = kay.get(anahtar)
            if c is None and not k.get("sonuc") and (simdi is None or simdi < saat) and k.get("uclu") is True:
                r = BS._olasiliklar(obj, k)
                if r:
                    at, pp, P = r
                    PM = EG._kombolar({i: v for i, v in enumerate(pp)}, 3)
                    c = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": saat, "uretim": simdi, "kuponlar": []}
                    for model, p in P.items():
                        if model == "Jason-S":
                            continue
                        for B in BUTCELER:
                            kp = kupon(p, B)
                            if not kp:
                                continue
                            sets, pm_ = kp; pq = _prob(PM, sets); v = _gecerli(sets)
                            c["kuponlar"].append({"model": model, "butce": B, "kombinasyon": v, "bedel": round(v * BIRIM, 2),
                                                  "ayaklar": [[at[i]["no"] for i in s] for s in sets],
                                                  "isimler": [{str(at[i]["no"]): at[i]["at"] for i in s} for s in sets],
                                                  "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3)})
                    if c["kuponlar"]:
                        kay[anahtar] = c
                    else:
                        c = None
            if c and "sonuc" not in c and k.get("sonuc"):
                sira = {int(no): v["sira"] for no, v in k["sonuc"].items() if v.get("sira") is not None and v["sira"] > 0}
                ilk3 = [no for no, s in sorted(sira.items(), key=lambda x: x[1])][:3]
                if len(ilk3) == 3:
                    if od is None:
                        od = _odeme(tarih)
                    o = od[(od.hipodrom == h["id"]) & (od.kosu == k["kosu"])] if len(od) else od
                    if len(o):
                        kazanan = []
                        for q in o.itertuples():
                            try:
                                kazanan.append(([int(z) for z in str(q.kombo).split("/")], float(q.tutar)))
                            except Exception:
                                pass
                        c["ilk3"] = ilk3; c["sonuc"] = True
                        for q in c["kuponlar"]:
                            kaz = sum(tt for kk, tt in kazanan if len(kk) == 3 and all(kk[i] in q["ayaklar"][i] for i in range(3)))
                            q["isabet"] = kaz > 0; q["kazanc"] = round(kaz, 2)
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def ozet_yaz(tarih):
    top = {}
    for y in sorted(glob.glob(os.path.join(VERI, "*.json"))):
        for c in json.load(open(y, encoding="utf-8")).values():
            if not c.get("sonuc"):
                continue
            for q in c["kuponlar"]:
                for grup in ("hepsi", "onerilen"):
                    if grup == "onerilen" and q["oran"] < ESIK_ORAN:
                        continue
                    t = top.setdefault(f"{grup}-{q['model']}-{q['butce']}", {"grup": grup, "model": q["model"], "butce": q["butce"], "kosu": 0, "harcama": 0.0, "isabet": 0, "kazanc": 0.0})
                    t["kosu"] += 1; t["harcama"] += q["bedel"]; t["isabet"] += int(q.get("isabet", False)); t["kazanc"] += q.get("kazanc", 0.0)
    for t in top.values():
        t["geri_donus"] = round(t["kazanc"] / t["harcama"], 3) if t["harcama"] else None
        t["harcama"] = round(t["harcama"], 2); t["kazanc"] = round(t["kazanc"], 2)
    yol = os.path.join(VERI, tarih + ".json")
    bugun = list(json.load(open(yol, encoding="utf-8")).values()) if os.path.exists(yol) else []
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "esik": ESIK_ORAN, "birim": BIRIM, "bugun": bugun, "toplam": list(top.values())},
              open(os.path.join(SITE, "sirali3.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
