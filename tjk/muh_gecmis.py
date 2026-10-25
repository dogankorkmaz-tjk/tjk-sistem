"""vhs-medya geçmiş koşuların kapanış muhtemelleri (sıralı ikili / ikili top-22 + ganyan + varış sırası) -> data/muh_gecmis/<gün>.json
Kullanım: MUH_BAS=2026-07-01 MUH_BIT=2026-07-31 python -m tjk.muh_gecmis  (günde ~50 küçük istek, 4 iş parçacığı, nazik)"""
import json, os, time, datetime
from concurrent.futures import ThreadPoolExecutor
from tjk import muhtemeller as M

def gun_isle(gun):
    yol = gun.replace("-", "/"); ck = M._json(f"{M.HOST}{yol}/checksum.json")
    gj = M._json(f"{M.CDN}{yol}/day-{ck['day']}.json") if ck else None
    if not gj: return None
    isler = []
    for y in gj["data"]["yarislar"]:
        if y.get("YURTDISI"): continue
        for k in y["kosular"]:
            key = f'{y["KEY"]}-{k["NO"]}'; runs = (ck.get("runs") or {}).get(key)
            if runs: isler.append((key, runs[0], k.get("DURUM"), k.get("SAAT")))
    def al(a):
        key, rs, durum, saat = a; time.sleep(0.15)
        run = M._json(f"{M.CDN}{yol}/{key}-{rs}.json")
        if not run: return key, None
        e = {"durum": durum, "saat": saat}
        for b in ((run.get("data") or {}).get("muhtemeller") or {}).get("bahisler", []):
            t = b.get("B"); mm = b.get("muhtemeller") or []
            if t == "GANYAN": e["gan"] = [[x.get("S1"), x.get("G"), x.get("R")] for x in mm]
            elif t == "SIRALI İKİLİ": e["si"] = [[x.get("S1"), x.get("S2"), x.get("G")] for x in mm]; e["si_daha"] = bool(b.get("hasMore"))
            elif t == "İKİLİ": e["ik"] = [[x.get("S1"), x.get("S2"), x.get("G")] for x in mm]; e["ik_daha"] = bool(b.get("hasMore"))
        return key, e
    with ThreadPoolExecutor(4) as ex: res = dict(ex.map(al, isler))
    return {k: v for k, v in res.items() if v}

if __name__ == "__main__":
    b = datetime.date.fromisoformat(os.environ["MUH_BAS"]); e = datetime.date.fromisoformat(os.environ["MUH_BIT"])
    os.makedirs(os.path.join(M.KOK, "data", "muh_gecmis"), exist_ok=True); d = b
    while d <= e:
        yol = os.path.join(M.KOK, "data", "muh_gecmis", d.isoformat() + ".json")
        if not os.path.exists(yol):
            o = gun_isle(d.isoformat())
            if o: json.dump(o, open(yol, "w"), ensure_ascii=False, separators=(",", ":")); print(d, len(o), flush=True)
        d += datetime.timedelta(days=1)
