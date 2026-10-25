"""vhs-medya: SIRALI İKİLİ / İKİLİ muhtemel yapısı (25 Ekim 2026) -> data/futbol/muh_probe2_<gün>.json. Biten günlerin koşu dosyasında da var mı bakar."""
import json, os
from tjk import muhtemeller as M
simdi = M._tr_simdi(); gun = os.environ.get("MUH_GUN") or (simdi.date() - __import__("datetime").timedelta(days=1)).isoformat(); yol = gun.replace("-", "/")
ck = M._json(f"{M.HOST}{yol}/checksum.json"); gj = M._json(f"{M.CDN}{yol}/day-{ck['day']}.json") if ck else None
out = {"gun": gun, "ornek": {}, "ck_var": bool(ck), "gj_var": bool(gj)}
n = 0
if gj:
    for y in gj["data"]["yarislar"]:
        if y.get("YURTDISI"): continue
        for k in y["kosular"]:
            key = f'{y["KEY"]}-{k["NO"]}'; runs = (ck.get("runs") or {}).get(key)
            if not runs or n >= 3: continue
            run = M._json(f"{M.CDN}{yol}/{key}-{runs[0]}.json")
            if not run: continue
            d = run.get("data") or {}; m = d.get("muhtemeller") or {}
            e = {"data_anahtarlar": list(d.keys()), "durum": k.get("DURUM"), "bahis_turleri": [b.get("B") for b in m.get("bahisler", [])]}
            for b in m.get("bahisler", []):
                if b.get("B") in ("SIRALI İKİLİ", "İKİLİ", "GANYAN"):
                    mm = b.get("muhtemeller") or []
                    e[b["B"]] = {"anahtarlar": [x for x in b if x != "muhtemeller"], "adet": len(mm), "ilk": mm[:6]}
            out["ornek"][key] = e; n += 1
os.makedirs(os.path.join(M.KOK, "data", "futbol"), exist_ok=True)
json.dump(out, open(os.path.join(M.KOK, "data", "futbol", "muh_probe2_%s.json" % gun), "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:3000])
