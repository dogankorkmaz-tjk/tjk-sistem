"""Jason'ın tüyoları: Jason olasılığı >= %6 ve piyasa (AGF) payının >= 1,30 katı olan atlar.
Her tüyo ilk görüldüğünde dondurulur (silinmez/değişmez); sonuç gelince değerlendirilir. Kağıt üstü: her ata 1 TL ganyan."""
import os, json, glob, math

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data", "tuyo"), os.path.join(KOK, "docs", "data")
ESIK_P, ESIK_R = 0.06, 1.30


def guncelle(obj):
    if obj.get("w0_aday") is None:
        return
    tarih = obj["tarih"]; os.makedirs(VERI, exist_ok=True)
    yol = os.path.join(VERI, tarih + ".json")
    kay = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
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
                    for a in at:
                        pj = e[a["no"]] / Z; r = pj / pp[a["no"]]
                        key = f"{h['id']}|{k['kosu']}|{a['no']}"
                        if key not in kay and pj >= ESIK_P and r >= ESIK_R:
                            kay[key] = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": k.get("saat"), "no": a["no"], "at": a["at"],
                                        "pj": round(pj, 4), "pp": round(pp[a["no"]], 4), "oran": round(r, 3)}
            for c in kay.values():
                if c["hipodrom"] == h["id"] and c["kosu"] == k["kosu"] and "sira" not in c:
                    v = sonuc.get(str(c["no"]))
                    if v and v.get("sira") is not None:
                        c["sira"] = v["sira"]; c["g"] = v.get("g")
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
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
    json.dump({"tarih": tarih, "bugun": bugun, "toplam": {"n": n, "kazanan": kaz, "ilk3": ilk3, "geri_donus": round(geri / n, 3) if n else None,
                         "grup": {k: {"n": v[0], "kazanan": v[1], "geri_donus": round(v[2] / v[0], 3) if v[0] else None} for k, v in grup.items()}}},
              open(os.path.join(SITE, "tuyo.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
