"""Sıralı ikili ve üçlü için kombine kupon (her sıraya birden fazla at), kağıt üstü takip.
Kupon yarış başlamadan dondurulur (Bolton ve Jason, iki bütçe); koşu bitince data/odeme'deki ödemeyle değerlendirilir.
Öneri kuralı (önceden yazıldı): modelin tutma olasılığı / piyasa (AGF) tutma olasılığı >= ESIK_ORAN. Birim: sıralı ikili 1 TL, üçlü 2 TL."""
import os, json, glob, math, itertools
import pandas as pd
from . import besli as BS

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data", "kombine"), os.path.join(KOK, "docs", "data")
TURLER = {"SIRALI İKİLİ": (2, (6, 12), 1.0), "ÜÇLÜ BAHİS": (3, (12, 30), 2.0)}
ESIK_ORAN = 1.15


def _prob(W, T, sets):
    top = 0.0
    for tup in itertools.product(*sets):
        if len(set(tup)) < len(sets): continue
        pr = 1.0; used = []
        for k, h in enumerate(tup):
            den = T[k] - sum(W[k][u] for u in used)
            if den <= 1e-12: pr = 0.0; break
            pr *= W[k][h] / den; used.append(h)
        top += pr
    return top


def _sayi(sets):
    return sum(1 for tup in itertools.product(*sets) if len(set(tup)) == len(sets))


def kupon(p, B, L):
    n = len(p)
    if n < max(5, L + 2): return None
    W, T = BS._W(p, BS.G_M[:L])
    ord_ = sorted(range(n), key=lambda i: -p[i]); aday = ord_[:min(n, 9)]
    sets = [[ord_[k]] for k in range(L)]; cur = _prob(W, T, sets)
    for _ in range(60):
        nn = math.prod(len(s) for s in sets); best = None; bg = 0.0
        for k in range(L):
            if nn // len(sets[k]) * (len(sets[k]) + 1) > B: continue
            for h in aday:
                if h in sets[k]: continue
                sets[k].append(h); pr = _prob(W, T, sets); sets[k].pop()
                g = math.log(pr / cur) / math.log((len(sets[k]) + 1) / len(sets[k]))
                if g > bg: bg, best = g, (k, h, pr)
        if not best: break
        sets[best[0]].append(best[1]); cur = best[2]
    return sets, cur


def _odeme(tarih):
    try:
        o = pd.read_csv(os.path.join(KOK, "data", "odeme", tarih[:7] + ".csv.gz"))
        return o[(o.tarih == tarih) & o.tur.isin(list(TURLER))]
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
            if c is None and not k.get("sonuc") and (simdi is None or simdi < saat):
                r = BS._olasiliklar(obj, k)
                if r:
                    at, pp, P = r
                    c = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": saat, "uretim": simdi, "kuponlar": []}
                    for tur, (L, BT, birim) in TURLER.items():
                        Wp, Tp = BS._W(pp, BS.G_P[:L])
                        for model, p in P.items():
                            for B in BT:
                                kp = kupon(p, B, L)
                                if not kp: continue
                                sets, pm_ = kp; pq = _prob(Wp, Tp, sets); n = _sayi(sets)
                                c["kuponlar"].append({"tur": tur, "model": model, "butce": B, "kombinasyon": n, "bedel": round(n * birim, 2),
                                                      "ayaklar": [[at[i]["no"] for i in s] for s in sets],
                                                      "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3)})
                    kay[anahtar] = c
            if c and "sonuc" not in c and k.get("sonuc"):
                if od is None: od = _odeme(tarih)
                o = od[(od.hipodrom == h["id"]) & (od.kosu == k["kosu"])] if len(od) else od
                if len(o):
                    c["sonuc"] = True; c["odeme"] = {}
                    for tur in TURLER:
                        x = o[o.tur == tur]
                        c["odeme"][tur] = [[[int(v) for v in r.kombo.split("/")], float(r.tutar)] for r in x.itertuples() if all(v.strip().isdigit() for v in r.kombo.split("/"))]
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def _kazanc(c, q):
    z = 0.0
    for kb, t in c["odeme"].get(q["tur"], []):
        if len(kb) == len(q["ayaklar"]) and all(kb[i] in q["ayaklar"][i] for i in range(len(kb))): z += t
    return z


def ozet_yaz(tarih):
    top = {}
    for y in sorted(glob.glob(os.path.join(VERI, "*.json"))):
        for c in json.load(open(y, encoding="utf-8")).values():
            if not c.get("sonuc"): continue
            for q in c["kuponlar"]:
                if not c["odeme"].get(q["tur"]): continue      # o bahis açık değildi / ödeme yok
                z = _kazanc(c, q)
                for grup in ("hepsi", "onerilen"):
                    if grup == "onerilen" and q["oran"] < ESIK_ORAN: continue
                    t = top.setdefault(f"{grup}-{q['tur']}-{q['model']}-{q['butce']}", {"grup": grup, "tur": q["tur"], "model": q["model"], "butce": q["butce"], "kosu": 0, "harcama": 0.0, "isabet": 0, "kazanc": 0.0})
                    t["kosu"] += 1; t["harcama"] += q["bedel"]; t["isabet"] += int(z > 0); t["kazanc"] += z
    for t in top.values():
        t["geri_donus"] = round(t["kazanc"] / t["harcama"], 3) if t["harcama"] else None
        t["harcama"] = round(t["harcama"], 2); t["kazanc"] = round(t["kazanc"], 2)
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "esik": ESIK_ORAN, "toplam": list(top.values())}, open(os.path.join(SITE, "kombine.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
