"""Tabela bahsi (ilk 4 at) kağıt üstü takip (21 Ekim 2026, ön-kayıtlı kural: yarış başlamadan dondur, sonra değiştirme).
Her koşu için (>=6 at) her modelin: sıralı kombine <=24 ve <=120 geçerli kombinasyon, sırasız kombine (modelin en yüksek 5 atı, 120 komb.).
Değerlendirme: data/odeme'de o koşu için 'TABELA BAHİS' (sıralı) / 'TABELA BAHİS SIRASIZ' satırı varsa; hiçbiri yoksa ama o koşuda başka ödeme satırı varsa
tabela oynanmamış sayılır ve ölçüme girmez. Birim 1,50 TL (kullanıcı doğruladı 21 Ekim 2026), ödeme satırı birim bilet (1,50 TL) başına kabul edilir."""
import os, json, glob, math, itertools
import pandas as pd
from .besli import _olasiliklar, _modeller, GG, G_M, G_P

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data", "tabela"), os.path.join(KOK, "docs", "data")
BUTCELER = (24, 120)
BIRIM = 1.5
L = 4


def _prob(W, T, sets):
    top = 0.0
    for tup in itertools.product(*sets):
        if len(set(tup)) < L:
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
    W = [[max(v, 1e-9) ** g for v in p] for g in G[:L]]
    return W, [sum(w) for w in W]


def gecerli(sets):
    return sum(1 for t in itertools.product(*sets) if len(set(t)) == L)


def kupon(p, B, G):
    n = len(p)
    if n < 6:
        return None
    W, T = _W(p, G)
    t = sorted(range(n), key=lambda i: -p[i]); aday = t[:min(n, 9)]
    sets = [[t[0]], [t[1]], [t[2]], [t[3]]]
    cur = _prob(W, T, sets); nv = gecerli(sets)
    for _ in range(60):
        best = None; bg = 0.0
        for k in range(L):
            for h in aday:
                if h in sets[k]:
                    continue
                sets[k].append(h); v2 = gecerli(sets)
                if v2 > B or v2 <= nv:
                    sets[k].pop(); continue
                pr = _prob(W, T, sets); sets[k].pop()
                g = math.log(pr / cur) / math.log(v2 / nv)
                if g > bg:
                    bg, best = g, (k, h, pr, v2)
        if not best:
            break
        sets[best[0]].append(best[1]); cur, nv = best[2], best[3]
    return sets, cur


def _odeme(tarih):
    try:
        o = pd.read_csv(os.path.join(KOK, "data", "odeme", tarih[:7] + ".csv.gz"))
        return o[o.tarih == tarih]
    except Exception:
        return pd.DataFrame()


def guncelle(obj, simdi=None):
    tarih = obj["tarih"]; os.makedirs(VERI, exist_ok=True)
    try:
        from . import g1 as _G1; _G1.z6_doldur(obj)
    except Exception as e:
        print("z6 hatası:", repr(e))
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
            anahtar = f"{h['id']}|{k['kosu']}"; saat = k.get("saat") or "99:99"
            c = kay.get(anahtar)
            yen = False
            if c and "sonuc" not in c and not k.get("sonuc") and (simdi is None or simdi < saat) and obj.get("g1_surum"):
                if any(q["model"] == "G1-S" and q.get("g1v") != obj["g1_surum"] for q in c["kuponlar"]):
                    c["kuponlar"] = [q for q in c["kuponlar"] if q["model"] != "G1-S"]; yen = True     # G1-S sürümü değişti (v2 -> v3, 24 Ekim 2026): başlamamış koşuda yalnız G1-S kuponları yenilenir
            if (c is None or yen) and not k.get("sonuc") and (simdi is None or simdi < saat):
                r = _olasiliklar(obj, k)
                if r and len(r[0]) >= 6:
                    at, pp, P = r
                    Wp, Tp = _W(pp, G_P)
                    if c is None:
                        c = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": saat, "uretim": simdi, "kuponlar": []}
                    for model, p in P.items():
                        if yen and model != "G1-S":
                            continue
                        G = GG.get(model) or G_M
                        for B in BUTCELER:
                            kp = kupon(p, B, G)
                            if not kp:
                                continue
                            sets, pm_ = kp; pq = _prob(Wp, Tp, sets); v = gecerli(sets)
                            c["kuponlar"].append({"model": model, "tur": "sirali", "butce": B, "kombinasyon": v, "bedel": round(v * BIRIM, 2),
                                                  "ayaklar": [[at[i]["no"] for i in s] for s in sets],
                                                  "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3), **({"g1v": obj.get("g1_surum")} if model == "G1-S" else {})})
                        W, T = _W(p, G)
                        sr = sorted(range(len(p)), key=lambda i: -p[i])
                        for ad, n in (("sirasiz", 5), ("sirasiz+", None)):
                            top = sr[:5]
                            if n is None:     # +1 at kuralı: 6. at kapsamayı >=5 puan artırırsa (aksi halde bu varyant yok)
                                if len(sr) <= 5 or _prob(W, T, [sr[:6]] * L) - _prob(W, T, [sr[:5]] * L) < 0.05:
                                    continue
                                top = sr[:6]
                            sets = [top] * L
                            pm_ = _prob(W, T, sets); pq = _prob(Wp, Tp, sets); v = gecerli(sets)
                            c["kuponlar"].append({"model": model, "tur": ad, "butce": v, "kombinasyon": v, "bedel": round(v * BIRIM, 2),
                                                  "ayaklar": [[at[i]["no"] for i in s] for s in sets],
                                                  "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3), **({"g1v": obj.get("g1_surum")} if model == "G1-S" else {})})
                    kay[anahtar] = c
            if c and "sonuc" not in c and k.get("sonuc"):
                sira = {int(no): v["sira"] for no, v in k["sonuc"].items() if v.get("sira") is not None and v["sira"] > 0}
                ilk4 = [no for no, s in sorted(sira.items(), key=lambda x: x[1])][:4]
                if len(ilk4) == 4:
                    if od is None:
                        od = _odeme(tarih)
                    o = od[(od.hipodrom == h["id"]) & (od.kosu == k["kosu"])] if len(od) else od
                    if len(o):
                        c["ilk4"] = ilk4; c["sonuc"] = True
                        ts = o[o.tur == "TABELA BAHİS"]; tz = o[o.tur == "TABELA BAHİS SIRASIZ"]
                        if not len(ts) and not len(tz):
                            c["oynanmadi"] = True
                            continue
                        c["odeme_sirali"] = float(ts.tutar.max()) if len(ts) else 0.0
                        c["odeme_sirasiz"] = float(tz.tutar.max()) if len(tz) else 0.0
                        for q in c["kuponlar"]:
                            # Ödeme: koşunun ilk 4'ü sıra doğruysa 'TABELA BAHİS', dört at sırasız doğruysa 'TABELA BAHİS SIRASIZ' (24 sıralamadan 23'ü). Kuponun içindeki her sıralama ayrı bilet.
                            ns = q["ayaklar"]
                            npm = sum(1 for t in itertools.product(*ns) if len(set(t)) == L and set(t) == set(ilk4))
                            q["isabet"] = all(ilk4[i] in ns[i] for i in range(L))
                            q["kazanc"] = (c["odeme_sirali"] if q["isabet"] else 0.0) + (npm - (1 if q["isabet"] else 0)) * c["odeme_sirasiz"]
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def ozet_yaz(tarih):
    top = {}
    for y in sorted(glob.glob(os.path.join(VERI, "*.json"))):
        for c in json.load(open(y, encoding="utf-8")).values():
            if not c.get("sonuc") or c.get("oynanmadi"):
                continue
            for q in c["kuponlar"]:
                t = top.setdefault(f"{q['model']}-{q['tur']}-{q['butce']}", {"model": q["model"], "tur": q["tur"], "butce": q["butce"], "kosu": 0, "harcama": 0.0, "isabet": 0, "kazanc": 0.0})
                t["kosu"] += 1; t["harcama"] += q["bedel"]; t["isabet"] += int(q["isabet"]); t["kazanc"] += q["kazanc"]
    for t in top.values():
        t["geri_donus"] = round(t["kazanc"] / t["harcama"], 3) if t["harcama"] else None
        t["harcama"] = round(t["harcama"], 2); t["kazanc"] = round(t["kazanc"], 2)
    yol = os.path.join(VERI, tarih + ".json")
    bugun = list(json.load(open(yol, encoding="utf-8")).values()) if os.path.exists(yol) else []
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "bugun": [{k: v for k, v in c.items() if k != "kuponlar"} | {"n": len(c["kuponlar"])} for c in bugun], "toplam": list(top.values())},
              open(os.path.join(SITE, "tabela.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
