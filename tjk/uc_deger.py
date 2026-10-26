"""Sıralı üçlü: değer odaklı (λ=0,5) vs kapsama kuponu, ileriye dönük kâğıt üstü takip (26 Ekim 2026, ön-kayıt T25: data/analiz/hipotez_defteri.md).
Yarışa son 15 dk içinde en son canlı muhtemel ganyan görüntüsüyle kuponlar dondurulur (yarış başlayınca değişmez); koşu bitince ilk 3 ve ÜÇLÜ ödemesiyle değerlendirilir.
Çıktılar: data/uc_deger/<gün>.json, docs/data/uc_deger.json. Mevcut hiçbir kural/kupon değişmez."""
import os, json, glob, math, itertools
import numpy as np, pandas as pd
from . import ortak as O
from . import sirali3 as S3

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data", "uc_deger"), os.path.join(KOK, "docs", "data")
BASLA = "2026-10-26"
NS = (24, 48)
GP = [1.0, 0.87, 0.74]            # piyasa sıra üsleri (sayfadaki G5_P)
PENCERE_DK = 15
BIRIM = 2.0
HIPKEY = {"diyarbakir": "DBAKIR"}


def _pl(W, T, sira):
    pr = 1.0
    for k, i in enumerate(sira):
        den = T[k] - sum(W[k][u] for u in sira[:k])
        if den <= 1e-12:
            return 0.0
        pr *= W[k][i] / den
    return pr


def _model_p(obj, k, pp_by_no):
    """G1-S canlı olasılığı: softmax(w0*log pp + c2*log pp^2 + z6b) (tarayıcı modelP ile aynı)."""
    w0 = obj.get("w0_g1"); c2 = obj.get("lp2_g1") or 0.0
    if w0 is None:
        return None
    nos = [a["no"] for a in k["atlar"] if a["no"] in pp_by_no]
    z = []
    for a in k["atlar"]:
        if a["no"] not in pp_by_no:
            continue
        zz = a.get("z6b") if a.get("z6b") is not None else a.get("z6")
        if zz is None:
            return None
        l = math.log(max(pp_by_no[a["no"]], 1e-6))
        z.append(w0 * l + c2 * l * l + zz)
    z = np.array(z); e = np.exp(z - z.max()); return nos, e / e.sum()


def _kuponlar(nos, p, qd, a5):
    p = np.asarray(p, float); qd = np.asarray(qd, float); n = len(nos)
    out = []
    for B in NS:                                              # (a) kapsama
        kp = S3.kupon(list(p), B)
        if kp:
            sets = kp[0]; kom = [tuple(nos[i] for i in t) for t in itertools.product(*sets) if len(set(t)) == 3]
            out.append({"tur": "kapsama", "n": len(kom), "butce": B, "kombolar": kom, "tutma_model": None, "tutma_piyasa": None})
    pW = [p ** g for g in a5[:3]]; pT = [w.sum() for w in pW]
    qW = [qd ** g for g in GP]; qT = [w.sum() for w in qW]
    cand = sorted(range(n), key=lambda i: -(p[i] + qd[i]))[:8]
    rows = []
    for t in itertools.permutations(cand, 3):
        pr = _pl(pW, pT, t); qr = max(_pl(qW, qT, t), 1e-9)
        rows.append((pr / math.sqrt(qr), t, pr, qr))
    rows.sort(key=lambda x: -x[0])
    for B in NS:                                              # (b) değer odaklı
        sel = rows[:B]
        out.append({"tur": "deger", "n": len(sel), "butce": B, "kombolar": [tuple(nos[i] for i in r[1]) for r in sel],
                    "tutma_model": round(sum(r[2] for r in sel), 5), "tutma_piyasa": round(sum(r[3] for r in sel), 5)})
    return out


def _odeme(tarih):
    try:
        o = pd.read_csv(os.path.join(KOK, "data", "odeme", tarih[:7] + ".csv.gz"))
        return o[(o.tarih == tarih) & (o.tur == S3.TUR)]
    except Exception:
        return pd.DataFrame()


def guncelle(obj, simdi=None):
    tarih = obj["tarih"]
    if tarih < BASLA:
        return
    os.makedirs(VERI, exist_ok=True)
    yol = os.path.join(VERI, tarih + ".json")
    kay = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    if simdi is None:
        simdi = O.tr_simdi().strftime("%H:%M")
    try:
        muh = json.load(open(os.path.join(KOK, "data", "muh", tarih + ".json"), encoding="utf-8"))
    except Exception:
        muh = {}
    a5 = obj.get("a_g1") or [1.0, 0.8, 0.69]
    od = None
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            anahtar = f"{h['id']}|{k['kosu']}"; saat = k.get("saat") or "99:99"; c = kay.get(anahtar)
            baslamadi = not k.get("sonuc") and simdi < saat
            if baslamadi and k.get("uclu") is True:
                m = muh.get(f"{HIPKEY.get(h['id'], h['id'].upper())}-{k['kosu']}")
                sn = [x for x in (m or {}).get("anlik", []) if x.get("dk") is not None and 0 <= x["dk"] <= PENCERE_DK and x.get("durum") in ("AÇIK", None)]
                if sn:
                    g = {int(n): v for n, v in sn[-1]["g"].items() if v}
                    nos_ok = [a["no"] for a in k["atlar"] if not a.get("kosmaz") and a["no"] in g]
                    if len(nos_ok) >= 6:
                        ham = {n: 1.0 / g[n] for n in nos_ok}; s = sum(ham.values()); pp = {n: v / s for n, v in ham.items()}
                        r = _model_p(obj, k, pp)
                        if r:
                            nos, p = r
                            qd = np.array([pp[n] for n in nos])
                            kup = _kuponlar(nos, p, qd, a5)
                            if kup:
                                kay[anahtar] = c = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": saat, "uretim": simdi, "goruntu": sn[-1]["t"], "dk": sn[-1]["dk"],
                                                    "kuponlar": [{**q, "kombolar": [list(t) for t in q["kombolar"]], "bedel": round(q["n"] * BIRIM, 2)} for q in kup]}
            if c and "sonuc" not in c and k.get("sonuc"):
                sira = {int(no): v["sira"] for no, v in k["sonuc"].items() if v.get("sira") is not None and v["sira"] > 0}
                ilk3 = [no for no, s_ in sorted(sira.items(), key=lambda x: x[1])][:3]
                if len(ilk3) == 3:
                    if od is None:
                        od = _odeme(tarih)
                    o = od[(od.hipodrom == h["id"]) & (od.kosu == k["kosu"])] if len(od) else od
                    if len(o):
                        kaz = []
                        for q in o.itertuples():
                            try:
                                kaz.append(([int(z) for z in str(q.kombo).split("/")], float(q.tutar)))
                            except Exception:
                                pass
                        c["ilk3"] = ilk3; c["sonuc"] = True
                        for q in c["kuponlar"]:
                            S = {tuple(t) for t in q["kombolar"]}
                            kz = sum(tt for kk, tt in kaz if len(kk) == 3 and tuple(kk) in S)
                            q["isabet"] = kz > 0; q["kazanc"] = round(kz, 2)
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz()


def ozet_yaz():
    top = {}
    son = []
    for y in sorted(glob.glob(os.path.join(VERI, "*.json"))):
        for c in json.load(open(y, encoding="utf-8")).values():
            if not c.get("sonuc"):
                continue
            son.append({"hipodrom": c["hipodrom"], "kosu": c["kosu"], "ilk3": c.get("ilk3"), **{f"{q['tur']}{q['butce']}": [q.get("isabet"), q.get("kazanc")] for q in c["kuponlar"]}})
            for q in c["kuponlar"]:
                t = top.setdefault(f"{q['tur']}-{q['butce']}", {"tur": q["tur"], "butce": q["butce"], "kosu": 0, "harcama": 0.0, "isabet": 0, "kazanc": 0.0})
                t["kosu"] += 1; t["harcama"] += q["bedel"]; t["isabet"] += int(q.get("isabet", False)); t["kazanc"] += q.get("kazanc", 0.0)
    for t in top.values():
        t["geri_donus"] = round(t["kazanc"] / t["harcama"], 3) if t["harcama"] else None
        t["harcama"] = round(t["harcama"], 2); t["kazanc"] = round(t["kazanc"], 2)
    os.makedirs(SITE, exist_ok=True)
    json.dump({"toplam": sorted(top.values(), key=lambda x: (x["butce"], x["tur"])), "kosu": len({(s['hipodrom'], s['kosu']) for s in son}), "son": son[-12:]},
              open(os.path.join(SITE, "uc_deger.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
