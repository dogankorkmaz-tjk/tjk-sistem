"""Kağıt üstü plase / ilk2-ilk3-ilk4 takibi.
 - pm-ilk2 : pari-mutuel PLASE (ilk 2). Model ilk-2 olasılığı, AGF'den türeyen piyasa ilk-2 olasılığından >= %15 yüksek atlar.
 - sib-ilk2/3/4 : SİB sabit oran (yapıştırılan Oyunlar sayfası). Model P(ilk k) x oran >= 1,10 olan atlar.
Her seçim ilk kez görüldüğünde kaydedilir ve değişmez (donuk); sonuç gelince değerlendirilir."""
import os, json, glob, math, difflib
import numpy as np
import pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data"), os.path.join(KOK, "docs", "data")
ESIK_PM, ESIK_SIB = 1.15, 1.10


def ilk_k(p, K=(2, 3, 4), n=20000):
    """Plackett-Luce (Harville) ile P(ilk k) — sabit tohum, deterministik."""
    p = np.asarray(p, float); p = p / p.sum()
    rng = np.random.default_rng(0)
    t = rng.exponential(size=(n, len(p))) / p
    sira = t.argsort(1).argsort(1) + 1
    return {k: (sira <= k).mean(0) for k in K}


def _ad(x):
    x = str(x).upper().replace("İ", "I").replace("Ş", "S").replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O").replace("Ç", "C")
    return " ".join(w for w in x.split() if w not in ("KG", "DB", "SK", "GKR", "SKG", "KGR", "DS"))


def _piyasa_model(k, w0):
    """Koşunun atlarından (AGF'li) {no: (pp, pm, ad)}; yoksa None."""
    at = [a for a in k.get("atlar", []) if a.get("agf") and not a.get("kosmaz")]
    if len(at) < 3:
        return None
    tot = sum(a["agf"] for a in at)
    pp = np.array([a["agf"] / tot for a in at])
    ham = np.exp(w0 * np.log(np.maximum(pp, 1e-6)) + np.array([a.get("z") or 0.0 for a in at]))
    pm = ham / ham.sum()
    return [a["no"] for a in at], pp, pm, [a["at"] for a in at]


def _yukle(tarih):
    y = os.path.join(VERI, "plase", tarih + ".json")
    return y, (json.load(open(y, encoding="utf-8")) if os.path.exists(y) else {})


def guncelle(obj):
    tarih, w0 = obj["tarih"], obj.get("w0", 1.0)
    y, kay = _yukle(tarih)
    try:
        from . import ortak as O
        simdi = O.tr_simdi().strftime("%H:%M")
    except Exception:
        simdi = "00:00"
    # --- A) pari-mutuel ilk2 (otomatik)
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            sa = k.get("saat") or "99:99"
            r = _piyasa_model(k, w0)
            if not r:
                continue
            nos, pp, pm, ad = r
            anahtar = f"pm2|{h['id']}|{k['kosu']}"
            if anahtar in kay or simdi >= sa:       # başlamış koşuya yeni seçim eklenmez
                continue
            tm, tp = ilk_k(pm, (2,))[2], ilk_k(pp, (2,))[2]
            sec = [{"no": int(n), "ad": a, "tm": round(float(m), 4), "tp": round(float(q), 4), "oran": round(float(m / q), 3)}
                   for n, a, m, q in zip(nos, ad, tm, tp) if q > 0 and m / q >= ESIK_PM and m >= 0.08]
            kay[anahtar] = {"tur": "pm-ilk2", "hipodrom": h["id"], "kosu": k["kosu"], "saat": sa, "secimler": sec}
    # --- B) SİB ilk2/3/4 (yapıştırılan Oyunlar dosyaları)
    son = {}
    for f in sorted(glob.glob(os.path.join(VERI, "sib_oyun", f"{tarih}_*_atlar.csv"))):
        d = pd.read_csv(f)
        if len(d):
            son[(d.hipodrom.iloc[0], int(d.kosu.iloc[0]))] = d              # aynı koşunun en son yapıştırması
    for (hip, kosu), d in son.items():
        h = next((x for x in obj["hipodromlar"] if x["id"] == hip), None)
        k = next((x for x in (h or {}).get("kosular", []) if x["kosu"] == kosu), None)
        if not k:
            continue
        r = _piyasa_model(k, w0)
        if not r or f"sib|{hip}|{kosu}" in kay:
            continue
        if (k.get("saat") or "99:99") <= simdi:
            continue
        nos, pp, pm, ad = r
        pk = ilk_k(pm)
        adlar = [_ad(a) for a in ad]
        sec = []
        for row in d.itertuples():
            m = difflib.get_close_matches(_ad(row.ad), adlar, 1, 0.8)
            if not m:
                continue
            i = adlar.index(m[0])
            for kk, oran in ((2, row.ilk2), (3, row.ilk3), (4, row.ilk4)):
                if pd.notna(oran) and pk[kk][i] * oran >= ESIK_SIB:
                    sec.append({"k": kk, "no": int(nos[i]), "ad": ad[i], "oran": float(oran), "p": round(float(pk[kk][i]), 4),
                                "ev": round(float(pk[kk][i] * oran), 3)})
        kay[f"sib|{hip}|{kosu}"] = {"tur": "sib", "hipodrom": hip, "kosu": kosu, "saat": k.get("saat"), "secimler": sec}
    # --- değerlendirme
    od = None
    for a, c in kay.items():
        if c.get("sonuc"):
            continue
        h = next((x for x in obj["hipodromlar"] if x["id"] == c["hipodrom"]), None)
        k = next((x for x in (h or {}).get("kosular", []) if x["kosu"] == c["kosu"]), None)
        s = (k or {}).get("sonuc")
        if not s:
            continue
        if c["tur"] == "pm-ilk2":
            if od is None:
                try:
                    od = pd.read_csv(os.path.join(VERI, "odeme", tarih[:7] + ".csv.gz"))
                    od = od[(od.tarih == tarih) & (od.tur == "PLASE")]
                except Exception:
                    od = pd.DataFrame()
            if not len(od) or not len(od[(od.hipodrom == c["hipodrom"]) & (od.kosu == c["kosu"])]):
                continue                           # ödeme dosyası gelince (gece)
            pay = {int(r.kombo): r.tutar for r in od[(od.hipodrom == c["hipodrom"]) & (od.kosu == c["kosu"])].itertuples() if str(r.kombo).isdigit()}
            for q in c["secimler"]:
                q["girdi"] = (s.get(str(q["no"])) or {}).get("sira") in (1, 2)
                q["kazanc"] = float(pay.get(q["no"], 0.0)) if q["girdi"] else 0.0
        else:
            for q in c["secimler"]:
                sira = (s.get(str(q["no"])) or {}).get("sira")
                q["girdi"] = sira is not None and sira <= q["k"]
                q["kazanc"] = q["oran"] if q["girdi"] else 0.0
        c["sonuc"] = True
    if kay:
        os.makedirs(os.path.dirname(y), exist_ok=True)
        json.dump(kay, open(y, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def ozet_yaz(tarih):
    top, bugun = {}, []
    for y in sorted(glob.glob(os.path.join(VERI, "plase", "*.json"))):
        kay = json.load(open(y, encoding="utf-8"))
        for c in kay.values():
            if os.path.basename(y)[:10] == tarih:
                bugun.append(c)
            if not c.get("sonuc"):
                continue
            for q in c["secimler"]:
                t = top.setdefault(f"{c['tur']}-{q.get('k', 2)}", {"tur": c["tur"], "k": q.get("k", 2), "bahis": 0, "isabet": 0, "kazanc": 0.0, "bek": 0.0})
                t["bahis"] += 1; t["isabet"] += int(q["girdi"]); t["kazanc"] += q["kazanc"]
                t["bek"] += q["ev"] if "ev" in q else q["oran"] * 0 + (q["tm"] / q["tp"]) * 0
    for t in top.values():
        t["geri_donus"] = round(t["kazanc"] / t["bahis"], 3) if t["bahis"] else None
        t["kazanc"] = round(t["kazanc"], 2)
        t["model_beklenen"] = round(t["bek"] / t["bahis"], 3) if t["bahis"] and t["tur"] == "sib" else None
        t.pop("bek")
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "bugun": bugun, "toplam": list(top.values())},
              open(os.path.join(SITE, "plase.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
