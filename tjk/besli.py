"""Sıralı 5'li kombine kupon: kağıt üstü takip. Her koşu (>=5 at) için Bolton ve Jason kuponları (~48 ve ~96 kombinasyon) yarış başlamadan dondurulur;
koşu bitince ilk beş sıraya göre değerlendirilir, ödeme data/odeme'deki 'SIRALI 5 Lİ BAHİS' satırından alınır (DEVİR satırı = bilen yok).
Öneri kuralı (önceden yazıldı, sonradan değişmez): modelin tutma olasılığı / piyasa (AGF) tutma olasılığı >= ESIK_ORAN.
Birim 1,25 TL. Devir bilgisi kullanılmaz."""
import os, json, glob, math, itertools
import pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data", "besli"), os.path.join(KOK, "docs", "data")
G_M = [1, 0.80, 0.69, 0.69, 0.69]
G_P = [1, 0.87, 0.74, 0.74, 0.74]
BUTCELER = (48, 96)
ESIK_ORAN = 1.15
BIRIM = 1.25


def _prob(W, T, sets):
    top = 0.0
    for tup in itertools.product(*sets):
        if len(set(tup)) < 5:
            continue
        pr = 1.0; used = []
        for k, h in enumerate(tup):
            den = T[k] - sum(W[k][u] for u in used)
            if den <= 1e-12:
                pr = 0.0; break
            pr *= W[k][h] / den; used.append(h)
        top += pr
    return top


def _W(p, G):
    W = [[max(v, 1e-9) ** g for v in p] for g in G]
    return W, [sum(w) for w in W]


def gecerli_say(sets):
    """Makine yalnız beş ayrı atlı kombinasyonları sayar/ücretlendirir (13 Ekim 2026 makine fişiyle doğrulandı: 110 geçerli = 137,50 TL, çarpım 336)."""
    return sum(1 for tup in itertools.product(*sets) if len(set(tup)) == 5)


def kupon_g(p, B):
    """kupon() ile aynı açgözlü kurucu; bütçe, geçerli kombinasyon sayısına göre (çarpıma değil)."""
    n = len(p)
    if n < 5:
        return None
    W, T = _W(p, G_M)
    ord_ = sorted(range(n), key=lambda i: -p[i]); aday = ord_[:min(n, 9)]
    sets = [[ord_[k]] for k in range(5)]
    cur = _prob(W, T, sets); nv = gecerli_say(sets)
    for _ in range(60):
        best = None; bg = 0.0
        for k in range(5):
            for h in aday:
                if h in sets[k]:
                    continue
                sets[k].append(h); v2 = gecerli_say(sets)
                if v2 > B or v2 <= nv:
                    sets[k].pop(); continue
                pr = _prob(W, T, sets); sets[k].pop()
                g = math.log(pr / cur) / math.log(v2 / nv)
                if g > bg:
                    bg, best = g, (k, h, pr, v2)
        if not best:
            break
        sets[best[0]].append(best[1]); cur = best[2]; nv = best[3]
    return sets, cur


def kupon(p, B):
    n = len(p)
    if n < 5:
        return None
    W, T = _W(p, G_M)
    ord_ = sorted(range(n), key=lambda i: -p[i]); aday = ord_[:min(n, 9)]
    sets = [[ord_[k]] for k in range(5)]
    cur = _prob(W, T, sets)
    for _ in range(60):
        nn = math.prod(len(s) for s in sets); best = None; bg = 0.0
        for k in range(5):
            if nn // len(sets[k]) * (len(sets[k]) + 1) > B:
                continue
            for h in aday:
                if h in sets[k]:
                    continue
                sets[k].append(h); pr = _prob(W, T, sets); sets[k].pop()
                g = math.log(pr / cur) / math.log((len(sets[k]) + 1) / len(sets[k]))
                if g > bg:
                    bg, best = g, (k, h, pr)
        if not best:
            break
        sets[best[0]].append(best[1]); cur = best[2]
    return sets, cur


def _olasiliklar(obj, k):
    at = [a for a in k["atlar"] if a.get("agf") and not a.get("kosmaz")]
    if len(at) < 5:
        return None
    tot = sum(a["agf"] for a in at)
    pp = [a["agf"] / tot for a in at]
    w0 = obj.get("w0", 1.0)
    def sm(s):
        m = max(s); e = [math.exp(x - m) for x in s]; z = sum(e); return [x / z for x in e]
    pm = sm([w0 * math.log(max(p, 1e-6)) + (a.get("z") or 0.0) for p, a in zip(pp, at)])
    pj = None
    if obj.get("w0_aday") is not None and all(a.get("z2") is not None for a in at):
        l2 = obj.get("lp2_aday", 0.0)
        pj = sm([obj["w0_aday"] * math.log(max(p, 1e-6)) + l2 * math.log(max(p, 1e-6)) ** 2 + a["z2"] for p, a in zip(pp, at)])
    return at, pp, {"Bolton": pm, **({"Jason": pj} if pj else {})}


def _odeme(tarih):
    try:
        o = pd.read_csv(os.path.join(KOK, "data", "odeme", tarih[:7] + ".csv.gz"))
        return o[(o.tarih == tarih) & o.tur.str.contains("SIRALI 5")]
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
            anahtar = f"{h['id']}|{k['kosu']}"
            saat = k.get("saat") or "99:99"
            c = kay.get(anahtar)
            if c is None and not k.get("sonuc") and (simdi is None or simdi < saat) and k["kosu"] >= 2:
                r = _olasiliklar(obj, k)
                if r:
                    at, pp, P = r
                    c = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": saat, "uretim": simdi, "kuponlar": []}
                    Wp, Tp = _W(pp, G_P)
                    for model, p in P.items():
                        for B in BUTCELER:
                            kp = kupon(p, B)
                            if not kp:
                                continue
                            sets, pm_ = kp; pq = _prob(Wp, Tp, sets); n = math.prod(len(s) for s in sets)
                            c["kuponlar"].append({"model": model, "butce": B, "kombinasyon": n, "bedel": round(n * BIRIM, 2), "bedel_gecerli": round(gecerli_say(sets) * BIRIM, 2),
                                                  "ayaklar": [[at[i]["no"] for i in s] for s in sets],
                                                  "isimler": [{str(at[i]["no"]): at[i]["at"] for i in s} for s in sets],
                                                  "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3)})
                    for model, p in P.items():                 # ek varyant "-G": bütçe geçerli kombinasyon sayısına göre (makine fişi 13 Ekim 2026)
                        for B in BUTCELER:
                            kp = kupon_g(p, B)
                            if not kp:
                                continue
                            sets, pm_ = kp; pq = _prob(Wp, Tp, sets); v = gecerli_say(sets)
                            c["kuponlar"].append({"model": model + "-G", "butce": B, "kombinasyon": v, "bedel": round(v * BIRIM, 2), "bedel_gecerli": round(v * BIRIM, 2),
                                                  "ayaklar": [[at[i]["no"] for i in s] for s in sets],
                                                  "isimler": [{str(at[i]["no"]): at[i]["at"] for i in s} for s in sets],
                                                  "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3)})
                    kay[anahtar] = c
            if c and "sonuc" not in c and not k.get("sonuc") and (simdi is None or simdi < saat) and not any(q["model"].endswith("-G") for q in c["kuponlar"]):
                r = _olasiliklar(obj, k)                 # henüz başlamamış, -G içermeyen kayda -G varyantı eklenir (mevcut kuponlar değişmez)
                if r:
                    at, pp, P = r; Wp, Tp = _W(pp, G_P)
                    for model, p in P.items():
                        for B in BUTCELER:
                            kp = kupon_g(p, B)
                            if not kp:
                                continue
                            sets, pm_ = kp; pq = _prob(Wp, Tp, sets); v = gecerli_say(sets)
                            c["kuponlar"].append({"model": model + "-G", "butce": B, "kombinasyon": v, "bedel": round(v * BIRIM, 2), "bedel_gecerli": round(v * BIRIM, 2),
                                                  "ayaklar": [[at[i]["no"] for i in s] for s in sets],
                                                  "isimler": [{str(at[i]["no"]): at[i]["at"] for i in s} for s in sets],
                                                  "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3), "eklendi": simdi})
            if c and "sonuc" not in c and k.get("sonuc"):
                sira = {int(no): v["sira"] for no, v in k["sonuc"].items() if v.get("sira") is not None}
                ilk5 = [no for no, s in sorted(sira.items(), key=lambda x: x[1])][:5]
                if len(ilk5) == 5:
                    if od is None:
                        od = _odeme(tarih)
                    o = od[(od.hipodrom == h["id"]) & (od.kosu == k["kosu"])] if len(od) else od
                    if len(o):
                        kazanan = o[~o.tur.str.contains("DEVİR")]
                        odeme = float(kazanan.tutar.max()) if len(kazanan) else 0.0
                        c["ilk5"] = ilk5; c["odeme"] = odeme; c["sonuc"] = True
                        for q in c["kuponlar"]:
                            q["isabet"] = all(ilk5[i] in q["ayaklar"][i] for i in range(5))
                            q["kazanc"] = odeme if q["isabet"] else 0.0
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
                    t = top.setdefault(f"{grup}-{q['model']}-{q['butce']}", {"grup": grup, "model": q["model"], "butce": q["butce"], "kosu": 0, "harcama": 0.0, "isabet": 0, "kazanc": 0.0, "beklenen": 0.0})
                    t["kosu"] += 1; t["harcama"] += gecerli_say(q["ayaklar"]) * BIRIM; t["harcama_carpim"] = t.get("harcama_carpim", 0.0) + q["bedel"]; t["isabet"] += int(q["isabet"]); t["kazanc"] += q["kazanc"]
    for t in top.values():
        t["geri_donus"] = round(t["kazanc"] / t["harcama"], 3) if t["harcama"] else None
        t["harcama"] = round(t["harcama"], 2); t["harcama_carpim"] = round(t.get("harcama_carpim", 0.0), 2); t["kazanc"] = round(t["kazanc"], 2); t.pop("beklenen")
    yol = os.path.join(VERI, tarih + ".json")
    bugun = list(json.load(open(yol, encoding="utf-8")).values()) if os.path.exists(yol) else []
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "esik": ESIK_ORAN, "bugun": bugun, "toplam": list(top.values())},
              open(os.path.join(SITE, "besli.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
