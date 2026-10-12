"""Değer filtresi (kağıt üstü takip): ikili (sırasız, 1 birim) ve üçlü (sıralı, 2 birim) için kombinasyon bazlı seçim.
Kural (önceden yazıldı, sonradan değişmez): Jason'ın kombinasyon olasılığı / piyasa (AGF) olasılığı >= ESIK ise bilet işaretlenir.
Biletler yarış başlamadan dondurulur; koşu bitince data/odeme'deki ÖDEME ile değerlendirilir. Para yatırılmaz."""
import os, json, glob, math, itertools
import pandas as pd
from . import besli as BS

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data", "deger"), os.path.join(KOK, "docs", "data")
ESIKLER = (1.25, 1.5)
BIRIM = {"ikili": 1.0, "uclu": 2.0}


def _w(p, G):
    W, T = BS._W(p, G); return W, T


def _ikili(W, T):
    n = len(W[0]); P = {}
    for i in range(n):
        for j in range(i + 1, n):
            a = W[0][i] / T[0] * W[1][j] / (T[1] - W[1][i]); b = W[0][j] / T[0] * W[1][i] / (T[1] - W[1][j])
            P[(i, j)] = a + b
    return P


def _uclu(W, T):
    n = len(W[0]); P = {}
    for i, j, k in itertools.permutations(range(n), 3):
        d = T[2] - W[2][i] - W[2][j]
        if d <= 1e-12: continue
        P[(i, j, k)] = W[0][i] / T[0] * W[1][j] / (T[1] - W[1][i]) * W[2][k] / d
    return P


def _odeme(tarih):
    try:
        o = pd.read_csv(os.path.join(KOK, "data", "odeme", tarih[:7] + ".csv.gz"))
        return o[(o.tarih == tarih) & o.tur.isin(["İKİLİ", "ÜÇLÜ BAHİS"])]
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
                if r and "Jason" in r[2]:
                    at, pp, P = r; n = len(at)
                    if n >= 6:
                        no = [a["no"] for a in at]
                        Wj, Tj = _w(P["Jason"], BS.G_M); Wp, Tp = _w(pp, BS.G_P)
                        c = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": saat, "uretim": simdi, "n": n, "bilet": {"ikili": [], "uclu": []}}
                        pj, pq = _ikili(Wj, Tj), _ikili(Wp, Tp)
                        for key, q in pj.items():
                            o_ = q / max(pq[key], 1e-12)
                            if o_ >= ESIKLER[0]: c["bilet"]["ikili"].append([[no[i] for i in key], round(o_, 3), round(q, 5)])
                        if n <= 14:
                            pj, pq = _uclu(Wj, Tj), _uclu(Wp, Tp)
                            for key, q in pj.items():
                                o_ = q / max(pq[key], 1e-12)
                                if o_ >= ESIKLER[0]: c["bilet"]["uclu"].append([[no[i] for i in key], round(o_, 3), round(q, 6)])
                        kay[anahtar] = c
            if c and "sonuc" not in c and k.get("sonuc"):
                if od is None: od = _odeme(tarih)
                o = od[(od.hipodrom == h["id"]) & (od.kosu == k["kosu"])] if len(od) else od
                if len(o):
                    c["sonuc"] = True; c["odeme"] = {}
                    for tur, ad in (("İKİLİ", "ikili"), ("ÜÇLÜ BAHİS", "uclu")):
                        x = o[o.tur == tur]
                        c["odeme"][ad] = [[[int(v) for v in r.kombo.split("/")], float(r.tutar)] for r in x.itertuples() if all(v.strip().isdigit() for v in r.kombo.split("/"))]
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def _kazanc(c, tur, b):
    o = c.get("odeme", {}).get(tur, [])
    if tur == "ikili":
        return sum(t for kb, t in o if sorted(kb) == sorted(b))
    return sum(t for kb, t in o if kb == b)


def ozet_yaz(tarih):
    top = {}
    for y in sorted(glob.glob(os.path.join(VERI, "*.json"))):
        for c in json.load(open(y, encoding="utf-8")).values():
            if not c.get("sonuc"): continue
            for tur in ("ikili", "uclu"):
                if tur not in c.get("odeme", {}) or not c["odeme"][tur]: continue   # ödeme satırı yoksa ölçme dışı
                for e in ESIKLER:
                    t = top.setdefault(f"{tur}-{e}", {"tur": tur, "esik": e, "kosu": 0, "bilet": 0, "harcama": 0.0, "isabet": 0, "kazanc": 0.0})
                    sec = [b for b in c["bilet"][tur] if b[1] >= e]
                    t["kosu"] += 1; t["bilet"] += len(sec); t["harcama"] += len(sec) * BIRIM[tur]
                    for b, _, _ in sec:
                        z = _kazanc(c, tur, b)
                        if z > 0: t["isabet"] += 1; t["kazanc"] += z
    for t in top.values():
        t["geri_donus"] = round(t["kazanc"] / t["harcama"], 3) if t["harcama"] else None
        t["harcama"] = round(t["harcama"], 1); t["kazanc"] = round(t["kazanc"], 1)
    yol = os.path.join(VERI, tarih + ".json"); bugun = []
    if os.path.exists(yol):
        for c in json.load(open(yol, encoding="utf-8")).values():
            d = {k: c[k] for k in ("hipodrom", "ad", "kosu", "saat", "n") if k in c}; d["sonuc"] = bool(c.get("sonuc"))
            for tur in ("ikili", "uclu"):
                bl = sorted(c["bilet"][tur], key=lambda b: -b[1])
                d[tur] = {"say125": len(bl), "say15": sum(1 for b in bl if b[1] >= 1.5), "ilk": [[b[0], b[1]] for b in bl[:5]]}
            bugun.append(d)
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "esikler": list(ESIKLER), "bugun": bugun, "toplam": list(top.values())},
              open(os.path.join(SITE, "deger.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
