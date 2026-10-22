"""Esnek kupon (14 Ekim 2026, ön kayıt: data/analiz/hipotez_defteri.md): sabit bütçe yerine marjinal model/piyasa oranına göre genişlik.
Sıralı ikili, sıralı üçlü ve sıralı beşli için aynı kural. Jason olasılıkları + G_M; kupon yarış başlamadan dondurulur; ayrı kayıt data/esnek/.
Ana kupon/model/kural DEĞİŞMEZ."""
import os, json, math, itertools
import pandas as pd
from . import besli as BS

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data", "esnek"), os.path.join(KOK, "docs", "data")
ESIK = 1.15
TURLER = {"SIRALI İKİLİ": (2, 40, 1.0), "ÜÇLÜ BAHİS": (3, 25, 2.0), "SIRALI 5 Lİ BAHİS": (5, 150, 1.25)}


def _prob(W, T, sets, L):
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


def _say(sets, L):
    return sum(1 for tup in itertools.product(*sets) if len(set(tup)) == L)


def esnek_kupon(p, pp, L, tavan):
    """Döner: (sets, P_model, Q_piyasa) ya da None (oynanmaz). p/pp: aynı sıradaki at listeleri için olasılıklar."""
    n = len(p)
    if n < max(5, L + 2):
        return None
    G = BS.G_M[:L]
    W, T = BS._W(p, G); Wq, Tq = BS._W(pp, BS.G_P[:L])
    t = sorted(range(n), key=lambda i: -p[i]); aday = t[:min(n, 9)]
    sets = [[t[k]] for k in range(L)]
    P = _prob(W, T, sets, L); Q = _prob(Wq, Tq, sets, L)
    if P / max(Q, 1e-12) < ESIK:
        return None
    nv = _say(sets, L)
    for _ in range(80):
        best = None; bg = 0.0
        for k in range(L):
            for h in aday:
                if h in sets[k]:
                    continue
                sets[k].append(h); v2 = _say(sets, L)
                if v2 > tavan or v2 <= nv:
                    sets[k].pop(); continue
                P2 = _prob(W, T, sets, L); Q2 = _prob(Wq, Tq, sets, L); sets[k].pop()
                dP, dQ = P2 - P, Q2 - Q
                if dP <= 0 or (dQ > 0 and dP / dQ < ESIK):
                    continue
                g = math.log(P2 / P) / math.log(v2 / nv)
                if g > bg:
                    bg, best = g, (k, h, P2, Q2, v2)
        if not best:
            break
        sets[best[0]].append(best[1]); P, Q, nv = best[2], best[3], best[4]
    return sets, P, Q


def _odeme(tarih):
    try:
        o = pd.read_csv(os.path.join(KOK, "data", "odeme", tarih[:7] + ".csv.gz"))
        return o[(o.tarih == tarih) & o.tur.isin(list(TURLER) + ["SIRALI BEŞLİ BAHİS"])]
    except Exception:
        return pd.DataFrame()


def _simdi():
    try:
        from . import ortak as O
        return O.tr_simdi().strftime("%H:%M")
    except Exception:
        return None


def guncelle(obj, simdi=None):
    tarih = obj["tarih"]; os.makedirs(VERI, exist_ok=True)
    yol = os.path.join(VERI, tarih + ".json")
    kay = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    simdi = simdi or _simdi(); od = None
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            saat = k.get("saat") or "99:99"; basladi = bool(k.get("sonuc")) or (simdi is not None and simdi >= saat and obj.get("gecmis") is not True)
            r = None
            for tur, (L, tavan, birim) in TURLER.items():
                if (tur == "SIRALI 5 Lİ BAHİS" and k.get("besli") is not True) or (tur == "ÜÇLÜ BAHİS" and k.get("uclu") is not True):
                    if f"{h['id']}|{k['kosu']}|{L}" in kay and not basladi:
                        del kay[f"{h['id']}|{k['kosu']}|{L}"]          # oynanmayan koşu: kayıt tutulmaz
                    continue
                an = f"{h['id']}|{k['kosu']}|{L}"; c = kay.get(an)
                if not basladi and (c is None or not c.get("dondu")):
                    if r is None:
                        r = BS._olasiliklar(obj, k)
                    if r and r[2].get("Jason"):
                        at, pp, P = r
                        kp = esnek_kupon(P["Jason"], pp, L, tavan)
                        base = {"tur": tur, "hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": saat, "uretim": simdi, "birim": birim,
                                "isimler": {str(a["no"]): a["at"] for a in k["atlar"]}}
                        if kp:
                            sets, Pm, Pq = kp; v = _say(sets, L)
                            base.update({"oyna": True, "ayaklar": [[at[i]["no"] for i in s] for s in sets], "kombinasyon": v, "bedel": round(v * birim, 2),
                                         "tutma_model": round(Pm, 5), "tutma_piyasa": round(Pq, 5), "oran": round(Pm / max(Pq, 1e-12), 3)})
                        else:
                            base.update({"oyna": False})
                        kay[an] = c = base
                if c is not None and basladi:
                    c["dondu"] = True
                if c and "sonuc" not in c and k.get("sonuc") and c.get("dondu", True):
                    if od is None:
                        od = _odeme(tarih)
                    x = od[(od.hipodrom == h["id"]) & (od.kosu == k["kosu"])] if len(od) else od
                    if len(x):
                        sira = {int(no): v["sira"] for no, v in k["sonuc"].items() if v.get("sira") is not None and v["sira"] > 0}
                        ilk = [no for no, s in sorted(sira.items(), key=lambda z: z[1])][:L]
                        if len(ilk) == L:
                            xs = x[x.tur.isin(["SIRALI BEŞLİ BAHİS", "SIRALI 5 Lİ BAHİS"])] if L == 5 else x[x.tur == c["tur"]]
                            if L == 5:
                                xs = xs[~xs.tur.str.contains("DEVİR")]; kaz = float(xs.tutar.max()) if len(xs) else 0.0
                                tut = bool(c.get("oyna")) and all(ilk[i] in c["ayaklar"][i] for i in range(5))
                                odeme = kaz if tut else 0.0
                            else:
                                tut = bool(c.get("oyna")) and all(ilk[i] in c["ayaklar"][i] for i in range(L))
                                odeme = 0.0
                                if tut:
                                    for q in xs.itertuples():
                                        kb = [int(v) for v in str(q.kombo).split("/") if v.strip().isdigit()]
                                        if kb == ilk:
                                            odeme += float(q.tutar)
                            c["ilk"] = ilk; c["isabet"] = tut; c["kazanc"] = round(odeme, 2); c["sonuc"] = True
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def ozet_yaz(tarih):
    import glob
    top = {t: {"tur": t, "oynanan": 0, "oynanmayan": 0, "harcama": 0.0, "kazanc": 0.0, "isabet": 0} for t in TURLER}
    gun = []
    for y in sorted(glob.glob(os.path.join(VERI, "*.json"))):
        d = os.path.basename(y)[:10]
        for c in json.load(open(y, encoding="utf-8")).values():
            if d == tarih:
                gun.append(c)
            if "sonuc" in c:
                a = top[c["tur"]]
                if c.get("oyna"):
                    a["oynanan"] += 1; a["harcama"] += c["bedel"]; a["kazanc"] += c.get("kazanc", 0.0); a["isabet"] += int(bool(c.get("isabet")))
                else:
                    a["oynanmayan"] += 1
    for a in top.values():
        a["geri_donus"] = round(a["kazanc"] / a["harcama"], 3) if a["harcama"] else None
        a["harcama"] = round(a["harcama"], 2); a["kazanc"] = round(a["kazanc"], 2)
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "kural": {"esik": ESIK, "tavan": {t: v[1] for t, v in TURLER.items()}, "birim": {t: v[2] for t, v in TURLER.items()}},
               "bugun": gun, "toplam": list(top.values())}, open(os.path.join(SITE, "esnek.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
