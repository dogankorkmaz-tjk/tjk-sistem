"""Sabit ihtimalli ganyan gölge kolu (3 Kasım 2026, T95 ileri ön kaydı: data/analiz/hipotez_defteri.md). Kağıt üstü, para yok.
Kural (sonuç görülmeden donduruldu): yarışa 7 dk kala ile yarış saati+3 dk arasındaki İLK çalışmada, o anda yayınlanmış son sabit ganyan oranı (data/piyasa, tip 1001, oran>1)
ile Jason olasılığı (tüyo ile aynı formül, AGF payı pp üzerinden) çarpılır:
  Kol A: p_Jason × sabit oran >= 1,2           -> o ata 1 TL
  Kol B: Kol A şartı VE p_Jason >= pp (AGF payı) -> o ata 1 TL   (sabit oranın havuz karşısında 'bayat yüksek' kalma riskini eler)
Her kayıt ilk dondurulduğunda değişmez. Sonuçta: sıra 1 ise kazanç = dondurulan oran (kesinti: 18+ oranda yok; uzun atlarda ihmal edilir, kesinti tablosu doğrulanmadı).
Tanılama: dondurmadan sonraki son yayınlanan oran ('son') ve yarışa kaç dk kala dondurulduğu ('dk') saklanır."""
import os, json, glob, math
import pandas as pd
from . import ortak as O

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE, PIY = os.path.join(KOK, "data", "sabit_golge"), os.path.join(KOK, "docs", "data"), os.path.join(KOK, "data", "piyasa")
ESIK_EV = 1.2
ONCE, SONRA = 7.0, 3.0     # dondurma penceresi: yarış saatinden ÖNCE 7 dk ... SONRA 3 dk


def _dk(s):
    p = [int(x) for x in str(s).split(":")]
    return p[0] * 60 + p[1] + (p[2] / 60 if len(p) > 2 else 0)


def _oranlar(tarih, hip, kosu, simdi_dk=None):
    """Yayınlanmış en son sabit ganyan oranı (simdi_dk verilirse o ana kadar)."""
    yol = os.path.join(PIY, tarih + ".csv.gz")
    if not os.path.exists(yol):
        return {}
    d = pd.read_csv(yol)
    d = d[(d.tip == 1001) & (d.hipodrom == hip) & (d.kosu == kosu) & (d.oran > 1.0)]
    if simdi_dk is not None:
        d = d[d.saat.map(_dk) <= simdi_dk]
    if d.empty:
        return {}
    return {int(n): float(g.sort_values("saat").oran.iloc[-1]) for n, g in d.groupby("no")}


def guncelle(obj, simdi=None):
    if obj.get("w0_aday") is None:
        return
    tarih = obj["tarih"]; simdi = simdi or O.tr_simdi()
    os.makedirs(VERI, exist_ok=True)
    yol = os.path.join(VERI, tarih + ".json")
    kay = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    bugun = simdi.strftime("%Y-%m-%d") == tarih; sn = simdi.hour * 60 + simdi.minute + simdi.second / 60
    w0, l2 = obj["w0_aday"], obj.get("lp2_aday", 0.0)
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            sonuc = k.get("sonuc") or {}
            if bugun and not sonuc and k.get("saat") and f"{h['id']}|{k['kosu']}" not in kay.get("_bakildi", []):
                kalan = _dk(k["saat"]) - sn
                at = [a for a in k.get("atlar", []) if a.get("agf") and not a.get("kosmaz")]
                if -SONRA <= kalan <= ONCE and at and all(a.get("z2") is not None for a in at):
                    oran = _oranlar(tarih, h["id"], k["kosu"], sn)
                    if len(oran) >= 4:
                        tot = sum(a["agf"] for a in at); pp = {a["no"]: a["agf"] / tot for a in at}
                        s = {a["no"]: w0 * math.log(max(pp[a["no"]], 1e-6)) + l2 * math.log(max(pp[a["no"]], 1e-6)) ** 2 + a["z2"] for a in at}
                        m = max(s.values()); e = {n: math.exp(v - m) for n, v in s.items()}; Z = sum(e.values())
                        kay.setdefault("_bakildi", []).append(f"{h['id']}|{k['kosu']}")
                        for a in at:
                            o = oran.get(a["no"]); pj = e[a["no"]] / Z
                            if o and pj * o >= ESIK_EV:
                                kay[f"{h['id']}|{k['kosu']}|{a['no']}"] = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": k.get("saat"), "no": a["no"], "at": a["at"],
                                    "pj": round(pj, 4), "pp": round(pp[a["no"]], 4), "oran": o, "ev": round(pj * o, 3), "B": bool(pj >= pp[a["no"]]), "dk": round(kalan, 1)}
            for key, c in kay.items():
                if key.startswith("_") or c["hipodrom"] != h["id"] or c["kosu"] != k["kosu"] or "sira" in c:
                    continue
                v = sonuc.get(str(c["no"]))
                if v and v.get("sira") is not None:
                    c["sira"] = v["sira"]; c["g"] = v.get("g")
                    son = _oranlar(tarih, h["id"], k["kosu"]).get(c["no"])
                    if son:
                        c["son"] = son
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def ozet_yaz(tarih):
    T = {"A": [0, 0, 0.0], "B": [0, 0, 0.0]}   # [bahis, kazanan, kazanç]
    for y in sorted(glob.glob(os.path.join(VERI, "*.json"))):
        for key, c in json.load(open(y, encoding="utf-8")).items():
            if key.startswith("_") or "sira" not in c:
                continue
            for kol in ("A", "B"):
                if kol == "B" and not c.get("B"):
                    continue
                T[kol][0] += 1; T[kol][1] += c["sira"] == 1; T[kol][2] += c["oran"] if c["sira"] == 1 else 0
    yol = os.path.join(VERI, tarih + ".json")
    bugun = [c for k, c in json.load(open(yol, encoding="utf-8")).items() if not k.startswith("_")] if os.path.exists(yol) else []
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "esik": ESIK_EV, "bugun": bugun,
               "toplam": {k: {"bahis": v[0], "kazanan": v[1], "kazanc": round(v[2], 2), "geri_donus": round(v[2] / v[0], 3) if v[0] else None} for k, v in T.items()}},
              open(os.path.join(SITE, "sabit_golge.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
