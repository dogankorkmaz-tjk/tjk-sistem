"""Start gecikmesi kaydı (24 Ekim 2026): her koşu için program saati ile bahsin açık kaldığı son an / kapandığı ilk an (data/muh anlıklarından).
Çıktı: data/analiz/gecikme.json (koşu başına) ve özet. Alt sınır: bahis en az o kadar dk açık kaldı. Çözünürlük anlık sıklığına bağlı (GitHub ~5 dk)."""
import json, glob, os, statistics
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _dk(t):
    return int(t[:2]) * 60 + int(t[3:5]) + (int(t[6:8]) / 60 if len(t) >= 8 else 0)


def hesapla():
    out = {}
    for f in sorted(glob.glob(os.path.join(KOK, "data", "muh", "*.json"))):
        gun = os.path.basename(f)[:10]
        try:
            M = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for key, v in M.items():
            if not str(v.get("yer") or "").strip() or "Birleşik" in str(v.get("yer")) or any(x in str(v.get("yer")) for x in ("ABD", "Malezya", "Fransa", "Şili", "Arjantin", "Avustralya", "Afrika")):
                continue                                     # yalnız Türkiye
            an = v.get("anlik") or []
            if not an or not v.get("saat_tr"):
                continue
            s0 = _dk(v["saat_tr"]); acik = [x for x in an if x.get("durum") == "AÇIK"]; kap = [x for x in an if x.get("durum") not in ("AÇIK", None)]
            if not acik:
                continue
            son = max(_dk(x["t"]) for x in acik) - s0
            ilk_kap = min((_dk(x["t"]) for x in kap if _dk(x["t"]) >= _dk(acik[-1]["t"])), default=None)
            out[f"{gun}|{key}"] = {"saat": v["saat_tr"], "acik_son_dk": round(son, 1), "kapali_ilk_dk": None if ilk_kap is None else round(ilk_kap - s0, 1), "n": len(an)}
    return out


def main():
    return _yaz()


def _yaz():
    o = hesapla()
    json.dump(o, open(os.path.join(KOK, "data", "analiz", "gecikme.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    xs = [r["acik_son_dk"] for r in o.values()]
    print("koşu:", len(xs))
    if xs:
        print("bahis açıkken görülen son an (program saatine göre dk): medyan %.1f, ort %.1f, >0 olan %d (%.0f%%), >3 dk %d, >5 dk %d, maks %.1f" % (statistics.median(xs), statistics.mean(xs), sum(x > 0 for x in xs), 100 * sum(x > 0 for x in xs) / len(xs), sum(x > 3 for x in xs), sum(x > 5 for x in xs), max(xs)))


if __name__ == "__main__":
    main()
