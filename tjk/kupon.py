"""Altılı kupon kurucu: değer = model olasılığı / havuz payı (AGF veya kapanış ganyanı).
Beklenen getiri oranı = (1-kesinti) * Π_ayak Σ_{h∈S} r_h / Π|S|,  r_h = pm_h / pa_h."""
import math, json, glob, os
import pandas as pd

KESINTI = 0.31


def kur(ayaklar, butce, mod="deger"):
    """ayaklar: [{no: (pm, pa)}]. butce: en çok kombinasyon. mod: 'deger' (r'ye göre) | 'favori' (pm'ye göre).
    Döner: seçilen no listeleri."""
    sec = []
    for a in ayaklar:
        en = max(a, key=lambda h: a[h][0])
        sec.append([en])
    def skor(h, a):
        pm, pa = a[h]
        return pm if mod == "favori" else pm / max(pa, 1e-6)
    while True:
        n = math.prod(len(s) for s in sec)
        en_iyi, en_k = None, 0
        for i, a in enumerate(ayaklar):
            adaylar = [h for h in a if h not in sec[i]]
            if not adaylar or n // len(sec[i]) * (len(sec[i]) + 1) > butce:
                continue
            h = max(adaylar, key=lambda x: skor(x, a))
            R = sum(skor(x, a) for x in sec[i]); r = skor(h, a)
            kazanc = math.log((R + r) / R) / math.log((len(sec[i]) + 1) / len(sec[i]))
            if kazanc > en_k:
                en_iyi, en_k = (i, h), kazanc
        if not en_iyi:
            return sec
        sec[en_iyi[0]].append(en_iyi[1])


def ozet(ayaklar, sec):
    n = math.prod(len(s) for s in sec)
    tut = math.prod(sum(a[h][0] for h in s) for a, s in zip(ayaklar, sec))
    tut_p = math.prod(sum(a[h][1] for h in s) for a, s in zip(ayaklar, sec))
    roi = (1 - KESINTI) * math.prod(sum(a[h][0] / max(a[h][1], 1e-6) for h in s) for a, s in zip(ayaklar, sec)) / n
    return {"kombinasyon": n, "tutma_model": tut, "tutma_piyasa": tut_p, "beklenen_getiri_orani": roi}


TURLER = {"3'LÜ GANYAN": 3, "4'LÜ GANYAN": 4, "5'Lİ GANYAN": 5, "6'LI GANYAN": 6, "7'Lİ GANYAN": 7}


def gecmis_ayaklar(tur="6'LI GANYAN"):
    """{(tarih,hip,son_kosu): (ayaklar, kazananlar)} — docs/data/gun/*.json sonuçlarından."""
    o = pd.read_csv("data/odeme/2026-10.csv.gz")
    a = o[o.tur == tur]; L = TURLER[tur]
    gun = {}
    for y in glob.glob("docs/data/gun/*.json"):
        d = json.load(open(y)); gun[d["tarih"]] = d
    out = []
    for _, r in a.iterrows():
        d = gun.get(r.tarih)
        if not d:
            continue
        h = next((x for x in d["hipodromlar"] if x["id"] == r.hipodrom), None)
        if not h:
            continue
        k = {x["kosu"]: x for x in h["kosular"]}
        ay, kaz, ok = [], [], True
        for i in range(L):
            x = k.get(r.kosu - L + 1 + i)
            if not x or not x.get("sonuc"):
                ok = False; break
            s = x["sonuc"]
            ay.append({int(no): (v["pm"], v["pp"]) for no, v in s.items()})
            kaz.append([int(no) for no, v in s.items() if v["sira"] == 1])
        if ok:
            out.append((r.tarih, r.hipodrom, r.kosu, ay, kaz, float(r.tutar)))
    return out


# ------------------------------------------------------------------ kağıt üstü (paper trading) kayıt
VERI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SITE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "data")
ESIK_ONERI = 1.20      # modele göre beklenen getiri bu orana ulaşmayan kupon "önerilmez" (kayıtta kalır)
BIRIM_1TL = ("sanliurfa", "elazig", "diyarbakir")      # bu hipodromlarda 6'lı ganyan 1 TL, diğerlerinde 1,25 TL


def birim(hip):
    return 1.0 if hip in BIRIM_1TL else 1.25


STRATEJILER = [("favori", 48), ("deger", 48), ("favori", 192), ("deger", 192)]


def _ayaklar_obj(h, son, w0):
    """Bir hipodromun altılısı (son koşu = son) için [{no: (pm, pa)}] ve at adları; AGF eksikse None."""
    k = {x["kosu"]: x for x in h["kosular"]}
    ay, ad = [], []
    for kn in range(son - 5, son + 1):
        x = k.get(kn)
        at = [a for a in (x or {}).get("atlar", []) if a.get("agf") and not a.get("kosmaz")]
        if not at:
            return None
        tot = sum(a["agf"] for a in at)
        pp = {a["no"]: a["agf"] / tot for a in at}
        ham = {a["no"]: math.exp(w0 * math.log(max(pp[a["no"]], 1e-6)) + (a.get("z") or 0.0)) for a in at}
        Z = sum(ham.values())
        ay.append({no: (ham[no] / Z, pp[no]) for no in pp})
        ad.append({a["no"]: a["at"] for a in at})
    return ay, ad


def guncelle(obj):
    """Günün altılıları için kuponları üretir (ilk ayak başlayana dek günceller, sonra dondurur),
    biten altılıları değerlendirir. data/kupon/<tarih>.json ve docs/data/kupon.json yazar."""
    from datetime import datetime
    import datetime as _dt
    tarih = obj["tarih"]
    yol = os.path.join(VERI, "kupon", tarih + ".json")
    kay = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    simdi = None
    try:
        from . import ortak as O
        simdi = O.tr_simdi().strftime("%H:%M")
    except Exception:
        pass
    od = None
    for h in obj["hipodromlar"]:
        k = {x["kosu"]: x for x in h["kosular"]}
        for alt, son in (h.get("altili") or {}).items():
            anahtar = f"{h['id']}|{son}"
            ilk_saat = (k.get(son - 5) or {}).get("saat") or "99:99"
            c = kay.get(anahtar)
            if c is None or (not c.get("dondu") and simdi and simdi < ilk_saat):
                r = _ayaklar_obj(h, son, obj.get("w0", 1.0))
                if r:
                    ay, ad = r
                    c = {"hipodrom": h["id"], "ad": h.get("ad"), "altili": int(alt), "son": son, "ilk_saat": ilk_saat,
                         "uretim": simdi, "dondu": False, "esik": ESIK_ONERI, "kuponlar": []}
                    for mod, B in STRATEJILER:
                        s = kur(ay, B, mod); o = ozet(ay, s)
                        c["kuponlar"].append({"mod": mod, "butce": B, "birim": birim(h["id"]), "bedel": round(o["kombinasyon"] * birim(h["id"]), 2), "ayaklar": [sorted(x) for x in s],
                                              "isimler": [{str(no): ad[i][no] for no in sorted(x)} for i, x in enumerate(s)],
                                              **{kk: round(v, 4) if isinstance(v, float) else v for kk, v in o.items()}})
                    kay[anahtar] = c
            if c and not c.get("dondu") and simdi and simdi >= ilk_saat:
                c["dondu"] = True
            # değerlendirme
            if c and "sonuc" not in c:
                kaz = []
                for kn in range(son - 5, son + 1):
                    s = (k.get(kn) or {}).get("sonuc")
                    if not s:
                        break
                    kaz.append([int(no) for no, v in s.items() if v["sira"] == 1])
                if len(kaz) == 6:
                    if od is None:
                        try:
                            import pandas as pd
                            od = pd.read_csv(os.path.join(VERI, "odeme", tarih[:7] + ".csv.gz"))
                            od = od[(od.tarih == tarih) & (od.tur == "6'LI GANYAN")]
                        except Exception:
                            od = pd.DataFrame()
                    odeme = od[(od.hipodrom == h["id"]) & (od.kosu == son)].tutar.max() if len(od) else float("nan")
                    c["kazananlar"] = kaz
                    c["odeme"] = None if odeme != odeme else float(odeme)
                    # ödeme dosyası henüz yoksa sonuc yazma (gece koşusu tamamlar)
                    if c["odeme"] is not None:
                        c["sonuc"] = True
                        for q in c["kuponlar"]:
                            isabet_ayak = sum(1 for i in range(6) if set(kaz[i]) & set(q["ayaklar"][i]))
                            q["ayak_isabet"] = isabet_ayak
                            q["isabet"] = isabet_ayak == 6
                            q["kazanc"] = c["odeme"] if q["isabet"] else 0.0
    if kay:
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def ozet_yaz(tarih):
    """Tüm günlerin toplamı + bugünün kuponları -> docs/data/kupon.json"""
    gunler = sorted(glob.glob(os.path.join(VERI, "kupon", "*.json")))
    top = {}
    for y in gunler:
        for c in json.load(open(y, encoding="utf-8")).values():
            if not c.get("sonuc"):
                continue
            for q in c["kuponlar"]:
                for grup in ("hepsi", "onerilen"):
                    if grup == "onerilen" and q["beklenen_getiri_orani"] < ESIK_ONERI:
                        continue
                    t = top.setdefault(f"{grup}-{q['mod']}-{q['butce']}", {"grup": grup, "mod": q["mod"], "butce": q["butce"], "altili": 0,
                                                                          "harcama": 0, "isabet": 0, "kazanc": 0.0, "beklenen": 0.0})
                    bed = q.get("bedel", q["kombinasyon"] * 1.25)
                    t["altili"] += 1; t["harcama"] += bed
                    t["isabet"] += int(q["isabet"]); t["kazanc"] += q["kazanc"]
                    t["beklenen"] += q["beklenen_getiri_orani"] * bed
    for t in top.values():
        t["geri_donus"] = round(t["kazanc"] / t["harcama"], 3) if t["harcama"] else None
        t["model_beklenen"] = round(t["beklenen"] / t["harcama"], 3) if t["harcama"] else None
        t["kazanc"] = round(t["kazanc"], 2); t["harcama"] = round(t["harcama"], 2); t.pop("beklenen")
    yol = os.path.join(VERI, "kupon", tarih + ".json")
    bugun = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "bugun": list(bugun.values()), "toplam": list(top.values())},
              open(os.path.join(SITE, "kupon.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    for tur, L in TURLER.items():
        veri = gecmis_ayaklar(tur)
        print(f"== {tur}: {len(veri)} oyun")
        for B in (12, 48, 192):
            for mod in ("favori", "deger"):
                harc = kaz = isabet = 0
                for t, hp, k, ay, kz, tutar in veri:
                    s = kur(ay, B, mod)
                    harc += math.prod(len(x) for x in s)
                    if all(set(kz[i]) & set(s[i]) for i in range(L)):
                        isabet += 1; kaz += tutar
                if harc:
                    print(f"  B={B:4d} {mod:7s} harcama={harc:6d} isabet={isabet:2d}/{len(veri)} geri dönüş={kaz/harc:.2f}")
