"""vhs-medya: bugünkü yurtiçi koşuların bahis türü listesi (22 Ekim 2026) -> data/futbol/muh_probe.json"""
import json, os
from tjk import muhtemeller as M
KOK = M.KOK
simdi = M._tr_simdi(); gun = simdi.date().isoformat(); yol = gun.replace("-", "/")
ck = M._json(f"{M.HOST}{yol}/checksum.json")
gj = M._json(f"{M.CDN}{yol}/day-{ck['day']}.json") if ck else None
out = {"gun": gun, "run": {}, "saat": {}}
if gj:
    for y in gj["data"]["yarislar"]:
        if y.get("YURTDISI"):
            continue
        for k in y["kosular"]:
            key = f'{y["KEY"]}-{k["NO"]}'
            out["saat"][key] = k["SAAT"]
            runs = (ck.get("runs") or {}).get(key)
            if not runs:
                continue
            run = M._json(f"{M.CDN}{yol}/{key}-{runs[0]}.json")
            if run:
                m = (run.get("data") or {}).get("muhtemeller") or {}
                out["run"][key] = [b.get("B") for b in m.get("bahisler", [])]
os.makedirs(os.path.join(KOK, "data", "futbol"), exist_ok=True)
json.dump(out, open(os.path.join(KOK, "data", "futbol", "muh_probe.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(out["run"], ensure_ascii=False)[:2500])
