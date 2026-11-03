"""Jason'ın tüyoları: Jason olasılığı >= %6 ve piyasa (AGF) payının >= 1,30 katı olan atlar.
Her tüyo ilk görüldüğünde dondurulur (silinmez/değişmez); sonuç gelince değerlendirilir. Kağıt üstü: her ata 1 TL ganyan."""
import os, json, glob, math

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data", "tuyo"), os.path.join(KOK, "docs", "data")
ESIK_P, ESIK_R = 0.06, 1.30


SON = os.path.join(KOK, "data", "tuyo_son")    # 3 Kasım 2026 (T110 ön kaydı): "son durum" kolu — yarış başlayana kadar her çalışmada yeniden hesaplanır, başlayınca donar


def _simdi():
    from . import ortak as O
    return O.tr_simdi().strftime("%H:%M")


def guncelle(obj, simdi=None):
    if obj.get("w0_aday") is None:
        return
    simdi = simdi or _simdi()
    tarih = obj["tarih"]; os.makedirs(VERI, exist_ok=True); os.makedirs(SON, exist_ok=True)
    yol = os.path.join(VERI, tarih + ".json"); yol_son = os.path.join(SON, tarih + ".json")
    kay = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    son = json.load(open(yol_son, encoding="utf-8")) if os.path.exists(yol_son) else {}
    w0, l2 = obj["w0_aday"], obj.get("lp2_aday", 0.0)
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            sonuc = k.get("sonuc") or {}
            at = [a for a in k.get("atlar", []) if a.get("agf") and not a.get("kosmaz")]
            if at and all(a.get("z2") is not None for a in at):
                tot = sum(a["agf"] for a in at)
                pp = {a["no"]: a["agf"] / tot for a in at}
                s = {a["no"]: w0 * math.log(max(pp[a["no"]], 1e-6)) + l2 * math.log(max(pp[a["no"]], 1e-6)) ** 2 + a["z2"] for a in at}
                m = max(s.values()); e = {n: math.exp(v - m) for n, v in s.items()}; Z = sum(e.values())
                if not sonuc:
                    yeni_son = {}
                    for a in at:
                        pj = e[a["no"]] / Z; r = pj / pp[a["no"]]
                        key = f"{h['id']}|{k['kosu']}|{a['no']}"
                        if pj >= ESIK_P and r >= ESIK_R:
                            rec = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": k.get("saat"), "no": a["no"], "at": a["at"],
                                   "pj": round(pj, 4), "pp": round(pp[a["no"]], 4), "oran": round(r, 3)}
                            if key not in kay:
                                kay[key] = dict(rec, gor=simdi)
                            yeni_son[key] = rec
                    basladi = bool(k.get("saat")) and simdi >= k["saat"]
                    if not basladi:      # son durum: yarış başlayana kadar güncel eşik durumu (AGF/oran değiştikçe tüyo gelir-gider); başlayınca donar
                        pre = f"{h['id']}|{k['kosu']}|"
                        for kk in [x for x in son if x.startswith(pre)]:
                            if kk not in yeni_son: del son[kk]
                        for kk, rec in yeni_son.items():
                            gor = son[kk]["gor"] if kk in son and "gor" in son[kk] else simdi
                            son[kk] = dict(rec, gor=gor, guncel=simdi)
            for C_ in (kay, son):
                for c in C_.values():
                    if c["hipodrom"] == h["id"] and c["kosu"] == k["kosu"] and "sira" not in c:
                        v = sonuc.get(str(c["no"]))
                        if v and v.get("sira") is not None:
                            c["sira"] = v["sira"]; c["g"] = v.get("g")
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    json.dump(son, open(yol_son, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def ozet_yaz(tarih):
    n = kaz = ilk3 = 0; geri = 0.0; gun = {}; grup = {"ust": [0, 0, 0.0], "alt": [0, 0, 0.0]}   # [n, kazanan, geri]
    for y in sorted(glob.glob(os.path.join(VERI, "*.json"))):
        t = os.path.basename(y)[:-5]
        for c in json.load(open(y, encoding="utf-8")).values():
            if "sira" not in c:
                continue
            n += 1; kaz += c["sira"] == 1; ilk3 += c["sira"] <= 3
            geri += (c.get("g") or 0) if c["sira"] == 1 else 0
            if c.get("g") and c.get("pj"):                    # 23 Ekim 2026 ön kaydı: kapanış ganyanı Jason'un adil ganyanından (1/pj) yüksek mi
                G = grup["ust" if c["g"] >= 1 / c["pj"] else "alt"]
                G[0] += 1; G[1] += c["sira"] == 1; G[2] += c["g"] if c["sira"] == 1 else 0
    yol = os.path.join(VERI, tarih + ".json")
    bugun = list(json.load(open(yol, encoding="utf-8")).values()) if os.path.exists(yol) else []
    os.makedirs(SITE, exist_ok=True)
    ns = ks = i3 = 0; gs = 0.0
    for y in sorted(glob.glob(os.path.join(SON, "*.json"))):
        for c in json.load(open(y, encoding="utf-8")).values():
            if "sira" not in c:
                continue
            ns += 1; ks += c["sira"] == 1; i3 += c["sira"] <= 3; gs += (c.get("g") or 0) if c["sira"] == 1 else 0
    ys = os.path.join(SON, tarih + ".json"); bugun_son = list(json.load(open(ys, encoding="utf-8")).values()) if os.path.exists(ys) else []
    json.dump({"tarih": tarih, "bugun": bugun, "bugun_son": bugun_son, "toplam_son": {"n": ns, "kazanan": ks, "ilk3": i3, "geri_donus": round(gs / ns, 3) if ns else None},
               "toplam": {"n": n, "kazanan": kaz, "ilk3": ilk3, "geri_donus": round(geri / n, 3) if n else None,
                         "grup": {k: {"n": v[0], "kazanan": v[1], "geri_donus": round(v[2] / v[0], 3) if v[0] else None} for k, v in grup.items()}}},
              open(os.path.join(SITE, "tuyo.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
