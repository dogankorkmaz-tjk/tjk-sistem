"""3 atlı kombine ikili kâğıt testi - ÖN-KAYIT 12 Ekim 2026 (kurallar donduruldu, sonuçlar görülmeden yazıldı).

Kupon: {A, B, S}. A,B = Jason olasılığına göre en yüksek 2 at. S = sürpriz atı: piyasa (AGF) olasılığı <= SURPRIZ_PK (≈ ganyan >= 10),
Jason/piyasa oranı >= ORAN, A/B dışında; birden fazlaysa piyasa olasılığı en yüksek olan. S yoksa kupon yok.
Oynanış: kombine ikili, üç çift (A-B, A-S, B-S), çift başına 1 birim = kupon 3 birim. Sıra önemsiz.
Dondurma/değerlendirme: egzotik.py ile aynı mantık (yarış başlayana kadar güncellenir, ödeme CSV'si gelince değerlendirilir).
Not: yarış saati bilinmeyen koşularda dondurma sonuç gelene kadar uzayabilir (saat_var alanı ile ayrılır).
Çıktılar: data/uc_at/<tarih>.json, docs/data/uc_at.json
Geçmişe dönük (walk-forward, 2025-01..2026-10): işaretli 297 kupon, geri dönüş 1,20 [0,79-1,67]; en büyük 3 ödeme çıkarılınca 0,94 - KANITLANMIŞ DEĞİL.
"""
import os, json, glob, math, itertools
import pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI = os.path.join(KOK, "data")
SITE = os.path.join(KOK, "docs", "data")
ORAN = 1.30
SURPRIZ_PK = 0.07
BIRIM = 1.0          # çift başına
ODEME_TUR = "İKİLİ"


def _kupon(atlar, w0, lp2):
    at = [a for a in atlar if a.get("agf") and not a.get("kosmaz") and a.get("z2") is not None]
    if len(at) < 6:
        return None
    tot = sum(a["agf"] for a in at)
    pk = {a["no"]: a["agf"] / tot for a in at}
    ham = {n: math.exp(w0 * math.log(max(p, 1e-6)) + lp2 * math.log(max(p, 1e-6)) ** 2 + next(a["z2"] for a in at if a["no"] == n)) for n, p in pk.items()}
    Z = sum(ham.values()); pm = {n: v / Z for n, v in ham.items()}
    ab = sorted(pm, key=lambda n: -pm[n])[:2]
    adaylar = [n for n in pk if n not in ab and pk[n] <= SURPRIZ_PK and pm[n] / pk[n] >= ORAN]
    if not adaylar:
        return None
    s = max(adaylar, key=lambda n: pk[n])
    nolar = [int(ab[0]), int(ab[1]), int(s)]
    ciftler = ["-".join(str(x) for x in sorted(c)) for c in itertools.combinations(nolar, 2)]
    return {"at": nolar, "ciftler": ciftler, "oran_s": round(pm[s] / pk[s], 2), "pk_s": round(pk[s], 4), "pm_s": round(pm[s], 4)}


def guncelle(obj):
    if obj.get("w0_aday") is None:
        return
    tarih = obj["tarih"]
    yol = os.path.join(VERI, "uc_at", tarih + ".json")
    kay = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    simdi = None
    try:
        from . import ortak as O
        simdi = O.tr_simdi().strftime("%H:%M")
    except Exception:
        pass
    od = None
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            basladi = bool(k.get("sonuc")) or (simdi is not None and k.get("saat") and simdi >= k["saat"] and obj.get("gecmis") is not True)
            anahtar = f"{h['id']}|{k['kosu']}"
            c = kay.get(anahtar)
            if not basladi and (c is None or not c.get("dondu")):
                s = _kupon(k.get("atlar", []), obj["w0_aday"], obj.get("lp2_aday", 0.0))
                if s is not None:
                    kay[anahtar] = c = {"hipodrom": h["id"], "kosu": k["kosu"], "saat": k.get("saat"), "saat_var": bool(k.get("saat")), "uretim": simdi, "dondu": False,
                                        "secim": s, "ad": {str(a["no"]): a.get("at") for a in k.get("atlar", [])}}
            elif c is not None and not c.get("dondu") and basladi:
                c["dondu"] = True
            if c and "sonuc" not in c and k.get("sonuc") and c.get("dondu", True):
                if od is None:
                    try:
                        od = pd.read_csv(os.path.join(VERI, "odeme", tarih[:7] + ".csv.gz"))
                        od = od[(od.tarih == tarih) & (od.tur == ODEME_TUR)]
                    except Exception:
                        od = pd.DataFrame()
                x = od[(od.hipodrom == h["id"]) & (od.kosu == k["kosu"])] if len(od) else od
                if len(x):
                    sec = set(c["secim"]["ciftler"]); kaz = 0.0; isabet = False
                    for q in x.itertuples():
                        kk = "-".join(str(n) for n in sorted(int(z) for z in str(q.kombo).split("/")))
                        if kk in sec:
                            kaz += float(q.tutar); isabet = True
                    c["sonuc"] = {"bedel": round(len(sec) * BIRIM, 2), "kazanc": round(kaz, 2), "isabet": isabet}
    if kay:
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def ozet_yaz(tarih):
    top = {"kupon": 0, "harcama": 0.0, "kazanc": 0.0, "isabet": 0}
    gun = []
    for y in sorted(glob.glob(os.path.join(VERI, "uc_at", "*.json"))):
        for c in json.load(open(y, encoding="utf-8")).values():
            if os.path.basename(y)[:10] == tarih:
                gun.append({"hipodrom": c["hipodrom"], "kosu": c["kosu"], "saat": c.get("saat"), "saat_var": c.get("saat_var"), "dondu": c.get("dondu"), "secim": c["secim"], "ad": c.get("ad", {}), "sonuc": c.get("sonuc")})
            r = c.get("sonuc")
            if r:
                top["kupon"] += 1; top["harcama"] += r["bedel"]; top["kazanc"] += r["kazanc"]; top["isabet"] += int(r["isabet"])
    top["geri_donus"] = round(top["kazanc"] / top["harcama"], 3) if top["harcama"] else None
    top["harcama"] = round(top["harcama"], 2); top["kazanc"] = round(top["kazanc"], 2)
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "kural": {"oran": ORAN, "surpriz_pk": SURPRIZ_PK, "birim": BIRIM}, "bugun": gun, "toplam": top},
              open(os.path.join(SITE, "uc_at.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
