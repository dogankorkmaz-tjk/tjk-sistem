"""vhs-medya gün/koşu dosyalarında bahis türü listesi var mı? (22 Ekim 2026) -> data/futbol/../muh_probe.json"""
import json, os, datetime
from tjk import muhtemeller as M
KOK = M.KOK
simdi = M._tr_simdi(); gun = simdi.date().isoformat(); yol = gun.replace("-", "/")
ck = M._json(f"{M.HOST}{yol}/checksum.json")
out = {"gun": gun, "ck_keys": list((ck or {}).keys()), "ck_ornek": {k: v for k, v in list((ck or {}).get("runs", {}).items())[:3]}}
gj = M._json(f"{M.CDN}{yol}/day-{ck['day']}.json") if ck else None
if gj:
    ys = gj["data"]["yarislar"]
    out["yarislar"] = [{k: (v if k not in ("atlar",) else "...") for k, v in y.items() if k != "kosular"} for y in ys if not y.get("YURTDISI")]
    for y in ys:
        if not y.get("YURTDISI"):
            out.setdefault("kosular", {})[y["KEY"]] = y["kosular"][:3]
            key = f'{y["KEY"]}-{y["kosular"][0]["NO"]}'
            runs = ck["runs"].get(key)
            if runs:
                run = M._json(f"{M.CDN}{yol}/{key}-{runs[0]}.json")
                if run:
                    d = run.get("data") or {}
                    m = d.get("muhtemeller") or {}
                    out.setdefault("run", {})[key] = {"data_keys": list(d.keys()), "muh_keys": list(m.keys()),
                        "bahisler": [{k: v for k, v in b.items() if k != "muhtemeller"} for b in m.get("bahisler", [])]}
os.makedirs(os.path.join(KOK, "data", "futbol"), exist_ok=True)
json.dump(out, open(os.path.join(KOK, "data", "futbol", "muh_probe.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:3000])
