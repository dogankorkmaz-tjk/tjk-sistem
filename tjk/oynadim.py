"""docs/data/oynadim/*.json (elle girilen gerçek bahisler) -> docs/data/oynadim_ozet.json
Kaynağa göre net getiri + sabit oran / TJK ganyan karşılaştırması."""
import os, json, glob

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def yaz():
    kay, cift, gun = {}, [], {}
    for f in sorted(glob.glob(os.path.join(KOK, "docs", "data", "oynadim", "*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        t = os.path.basename(f)[:-5]
        for b in d.get("liste", []):
            tut = float(b.get("tutar") or 0)
            k = kay.setdefault(b.get("kaynak") or "?", {"bahis": 0, "tutar": 0.0, "sonuclanan_tutar": 0.0, "odeme": 0.0})
            k["bahis"] += 1; k["tutar"] += tut
            g = gun.setdefault(t, {"tutar": 0.0, "sonuclanan_tutar": 0.0, "odeme": 0.0})
            g["tutar"] += tut
            if b.get("odeme") not in (None, ""):
                k["sonuclanan_tutar"] += tut; k["odeme"] += float(b["odeme"])
                g["sonuclanan_tutar"] += tut; g["odeme"] += float(b["odeme"])
            if b.get("sabit") and b.get("tjk"):
                cift.append({"tarih": t, "hipodrom": b.get("hipodrom"), "kosu": b.get("kosu"), "sabit": b["sabit"], "tjk": b["tjk"]})
    oran = [c["sabit"] / c["tjk"] for c in cift]
    cikis = {"kaynak": {a: {**v, "net": round(v["odeme"] - v["sonuclanan_tutar"], 2)} for a, v in kay.items()},
             "gun": {t: {**v, "net": round(v["odeme"] - v["sonuclanan_tutar"], 2)} for t, v in gun.items()},
             "sabit_tjk": {"n": len(cift), "ort_oran": round(sum(oran) / len(oran), 3) if oran else None,
                           "sabit_yuksek": sum(1 for x in oran if x > 1.0), "son": cift[-10:]}}
    os.makedirs(os.path.join(KOK, "docs", "data"), exist_ok=True)
    json.dump(cikis, open(os.path.join(KOK, "docs", "data", "oynadim_ozet.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return cikis


if __name__ == "__main__":
    print(yaz())
