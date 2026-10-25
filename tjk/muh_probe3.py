"""vhs-medya geçmiş gün erişilebilirliği (25 Ekim 2026): her gün için checksum/day dosyası ve sıralı ikili muhtemelin varlığı -> data/futbol/muh_probe3.json"""
import json, os
from tjk import muhtemeller as M
out = {}
for gun in (os.environ.get("MUH_GUNLER") or "2026-09-01,2026-07-01,2026-04-01,2026-01-15,2025-10-15,2025-06-15,2025-01-15,2024-06-15").split(","):
    yol = gun.replace("-", "/"); ck = M._json(f"{M.HOST}{yol}/checksum.json"); gj = M._json(f"{M.CDN}{yol}/day-{ck['day']}.json") if ck else None
    e = {"ck": bool(ck), "gj": bool(gj), "kosu": len((ck or {}).get("runs") or {}), "run_ornek": None}
    if gj:
        for y in gj["data"]["yarislar"]:
            if y.get("YURTDISI"): continue
            for k in y["kosular"]:
                key = f'{y["KEY"]}-{k["NO"]}'; runs = (ck.get("runs") or {}).get(key)
                if runs and e["run_ornek"] is None:
                    run = M._json(f"{M.CDN}{yol}/{key}-{runs[0]}.json")
                    e["run_ornek"] = {"key": key, "var": bool(run), "turler": [b.get("B") for b in ((run or {}).get("data") or {}).get("muhtemeller", {}).get("bahisler", [])]}
    out[gun] = e; print(gun, e, flush=True)
os.makedirs(os.path.join(M.KOK, "data", "futbol"), exist_ok=True)
json.dump(out, open(os.path.join(M.KOK, "data", "futbol", "muh_probe3.json"), "w"), ensure_ascii=False, indent=1)
