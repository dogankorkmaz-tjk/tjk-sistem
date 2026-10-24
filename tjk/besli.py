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
BUTCELER_G = (48, 96, 150)   # -G varyantları: geçerli kombinasyon sayısı (150 eklendi 13 Ekim 2026, 16:10)
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


def _acgozlu_g(p, B, sets, G=None):
    """Verilen başlangıç kümelerinden açgözlü genişletme; bütçe geçerli kombinasyon sayısına göre."""
    n = len(p)
    W, T = _W(p, G or G_M)
    ord_ = sorted(range(n), key=lambda i: -p[i]); aday = ord_[:min(n, 9)]
    sets = [list(x) for x in sets]
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


def kupon_g(p, B, G=None):
    """Çok başlangıçlı açgözlü kurucu (sürüm 2, 13 Ekim 2026 16:30): ilk iki sıra için tek yönlü ve iki yönlü başlangıçlardan en iyisi.
    Tek başlangıçlı açgözlü, favori çifti iki yönlü açmayı (6,7/6,7) göremiyordu; aynı maliyette %8 daha düşük tutma veriyordu."""
    n = len(p)
    if n < 5:
        return None
    t = sorted(range(n), key=lambda i: -p[i])
    W, T = _W(p, G or G_M)
    baslangic = [[[t[0]], [t[1]], [t[2]], [t[3]], [t[4]]],
                 [[t[0], t[1]], [t[0], t[1]], [t[2]], [t[3]], [t[4]]],
                 [[t[0], t[1]], [t[0], t[1]], [t[2], t[3]], [t[2], t[3]], [t[4]]]]
    en = None
    for st in baslangic:
        if not (0 < gecerli_say(st) <= B):
            continue
        sets, pr = _acgozlu_g(p, B, st, G)
        if en is None or pr > en[1] + 1e-12:
            en = (sets, pr)
    return en


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


G1V = {"s": None}   # G1-S sürümü (v2/v3): -G kuponlara damga, eski sürümlü kuponlar başlamamış koşuda yenilenir
GG = {}   # model -> sıra üsleri (Jason-S kendi öğrenilmiş ölçeklerini kullanır)


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
    ps = None
    if obj.get("w0_s") is not None and all(a.get("z4") is not None for a in at):
        l2 = obj.get("lp2_s", 0.0)
        ps = sm([obj["w0_s"] * math.log(max(p, 1e-6)) + l2 * math.log(max(p, 1e-6)) ** 2 + a["z4"] for p, a in zip(pp, at)])
    pf = None
    if obj.get("w0_f") is not None and all(a.get("z5") is not None for a in at):
        l2 = obj.get("lp2_f", 0.0)
        pf = sm([obj["w0_f"] * math.log(max(p, 1e-6)) + l2 * math.log(max(p, 1e-6)) ** 2 + a["z5"] for p, a in zip(pp, at)])
    GG["Jason-S"] = obj.get("a_s") or G_M
    pg = None
    try:                                                   # G1-S: katsayılar obj'den (z6_doldur v3/v2'ye göre yazar; z6 ile aynı sürüm olmalı)
        if obj.get("w0_g1") is not None and obj.get("a_g1") and all(a.get("z6") is not None for a in at):
            pg = sm([obj["w0_g1"] * math.log(max(p, 1e-6)) + a["z6"] for p, a in zip(pp, at)]); GG["G1-S"] = obj["a_g1"]
    except Exception as e:
        print("G1-S olasılık hatası:", repr(e))
    return at, pp, {"Bolton": pm, **({"Jason": pj} if pj else {}), **({"Jason-S": ps} if ps else {}), **({"Jason-F": pf} if pf else {}), **({"G1-S": pg} if pg else {})}


def _modeller(obj, k):
    r = _olasiliklar(obj, k)
    return list(r[2].keys()) if r else []


def _ekle_g(c, at, pp, P, simdi, istek=None):
    """c['kuponlar']'a eksik -G kuponlarını ekler (mevcut kuponlara dokunmaz)."""
    Wp, Tp = _W(pp, G_P)
    for model, p in P.items():
        for B in BUTCELER_G:
            if any(q["model"] == model + "-G" and q["butce"] == B for q in c["kuponlar"]):
                continue
            kp = kupon_g(p, B, GG.get(model))
            if not kp:
                continue
            sets, pm_ = kp; pq = _prob(Wp, Tp, sets); v = gecerli_say(sets)
            c["kuponlar"].append({"model": model + "-G", "butce": B, "kombinasyon": v, "bedel": round(v * BIRIM, 2), "bedel_gecerli": round(v * BIRIM, 2),
                                  "ayaklar": [[at[i]["no"] for i in s] for s in sets],
                                  "isimler": [{str(at[i]["no"]): at[i]["at"] for i in s} for s in sets],
                                  "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3), "eklendi": simdi, "surum": 2, **({"g1v": G1V["s"]} if model == "G1-S" else {})})


def _odeme(tarih):
    try:
        o = pd.read_csv(os.path.join(KOK, "data", "odeme", tarih[:7] + ".csv.gz"))
        return o[(o.tarih == tarih) & o.tur.str.contains("SIRALI 5")]
    except Exception:
        return pd.DataFrame()


def guncelle(obj, simdi=None):
    tarih = obj["tarih"]; os.makedirs(VERI, exist_ok=True)
    try:
        from . import g1 as _G1; _G1.z6_doldur(obj)
    except Exception as e:
        print("z6 hatası:", repr(e))
    G1V["s"] = obj.get("g1_surum")
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
            if c and "sonuc" not in c and not k.get("sonuc") and k.get("besli") is False:
                del kay[anahtar]; c = None            # program CSV'sine göre sıralı beşli oynanmayan koşu: kupon tutulmaz (14 Ekim 2026)
            if c is None and not k.get("sonuc") and (simdi is None or simdi < saat) and k["kosu"] >= 2 and k.get("besli") is True:
                r = _olasiliklar(obj, k)
                if r:
                    at, pp, P = r
                    c = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": saat, "uretim": simdi, "kuponlar": []}
                    Wp, Tp = _W(pp, G_P)
                    for model, p in P.items():
                        if model in ("Jason-S", "G1-S"):
                            continue                  # Jason-S ve G1-S yalnız -G kuponlarla ölçülür
                        for B in BUTCELER:
                            kp = kupon(p, B)
                            if not kp:
                                continue
                            sets, pm_ = kp; pq = _prob(Wp, Tp, sets); n = math.prod(len(s) for s in sets)
                            c["kuponlar"].append({"model": model, "butce": B, "kombinasyon": n, "bedel": round(n * BIRIM, 2), "bedel_gecerli": round(gecerli_say(sets) * BIRIM, 2),
                                                  "ayaklar": [[at[i]["no"] for i in s] for s in sets],
                                                  "isimler": [{str(at[i]["no"]): at[i]["at"] for i in s} for s in sets],
                                                  "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3)})
                    _ekle_g(c, at, pp, P, simdi)
                    kay[anahtar] = c
            if c and "sonuc" not in c and not k.get("sonuc") and (simdi is None or simdi < saat) and G1V["s"]:
                _g1e = [q for q in c["kuponlar"] if q["model"] == "G1-S-G" and q.get("g1v") != G1V["s"]]
                if _g1e:                                  # G1-S sürümü değişti (v2 -> v3, 24 Ekim 2026): başlamamış koşuda G1-S kuponları yeni sürümle yenilenir (eksik -G ekleme aşaması üretir)
                    c["kuponlar"] = [q for q in c["kuponlar"] if q not in _g1e]
            if c and "sonuc" not in c and not k.get("sonuc") and (simdi is None or simdi < saat):
                eski = [q for q in c["kuponlar"] if q["model"].endswith("-G") and q.get("surum", 1) < 2]
                if eski:                                  # sürüm 1 (tek başlangıçlı) -G kuponlar henüz başlamamış koşuda sürüm 2 ile değiştirilir
                    c["kuponlar"] = [q for q in c["kuponlar"] if q not in eski]
            _mod = _modeller(obj, k) if (c and "sonuc" not in c and not k.get("sonuc")) else []
            if c and "sonuc" not in c and not k.get("sonuc") and (simdi is None or simdi < saat) and any(
                    not any(q["model"] == m + "-G" and q["butce"] == B for q in c["kuponlar"]) for B in BUTCELER_G for m in _mod):
                r = _olasiliklar(obj, k)                 # henüz başlamamış kayda eksik -G kuponlar eklenir (mevcut kuponlar değişmez)
                if r:
                    at, pp, P = r; _ekle_g(c, at, pp, P, simdi)
            if c and "sonuc" not in c and k.get("sonuc"):
                sira = {int(no): v["sira"] for no, v in k["sonuc"].items() if v.get("sira") is not None and v["sira"] > 0}
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
