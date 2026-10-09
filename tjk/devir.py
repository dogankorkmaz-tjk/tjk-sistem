"""Devir (carryover) fırsat uyarısı: devirli 7'li ganyan havuzları için beklenen getiriyi hesaplar.
Devir kesintiye tabi değildir: tüm kombinasyonları oynayanın beklenen geri dönüşü ≈ 0,69 × (1 + D / net_havuz).
Beceri varsayımı yok (r=1); modelli sürüm ayrıca gösterilir ama iyimser kabul edilir."""
import os, glob, json, math
import numpy as np
import pandas as pd
from .kupon import kur, ozet

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data"), os.path.join(KOK, "docs", "data")
NET_ORAN = 0.69
ESIK = 1.10          # kötümser havuz senaryosunda sıfır beceriyle geri dönüş bu orandan yüksekse "fırsat"


def _oku(a):
    p = sorted(glob.glob(os.path.join(VERI, a, "*.csv.gz")))
    return pd.concat([pd.read_csv(x) for x in p], ignore_index=True) if p else pd.DataFrame()


def devirler(tarih):
    """{hipodrom: {'tarih':..,'tutar':..}} — 7'li ganyanda bugüne taşınan devir (sonraki bir ödeme tüketmediyse)."""
    o = _oku("odeme")
    if o.empty:
        return {}
    o = o[o.tarih < tarih]
    o7 = o[o.tur.str.contains("7'Lİ GANYAN")]
    out = {}
    for hip, g in o7.groupby("hipodrom"):
        g = g.sort_values("tarih")
        son = g.iloc[-1]
        if "DEVİR" in son.tur:
            out[hip] = {"tarih": son.tarih, "tutar": float(son.tutar)}
    return out


def havuz_medyan():
    h = _oku("havuz")
    if h.empty:
        return 370000.0
    x = h[h.tur == "7'LI GANYAN"].tutar
    return float(x.median()) if len(x) else 370000.0


def guncelle(obj):
    tarih = obj["tarih"]
    dv = devirler(tarih)
    med = havuz_medyan()
    rows = []
    for h in obj["hipodromlar"]:
        if h["id"] not in dv:
            continue
        d = dv[h["id"]]["tutar"]
        kos = sorted(x["kosu"] for x in h["kosular"])
        if len(kos) < 7:
            continue
        legs = kos[-7:]
        k = {x["kosu"]: x for x in h["kosular"]}
        sen = {}
        for ad, carp in (("iyimser", 0.7), ("orta", 1.0), ("kotumser", 1.5)):
            net = med * carp
            sen[ad] = {"net_havuz": round(net), "roi_sifir_beceri": round(NET_ORAN * (1 + d / net), 3)}
        r = {"hipodrom": h["id"], "ad": h.get("ad"), "devir": d, "devir_tarihi": dv[h["id"]]["tarih"], "ayaklar": legs,
             "ilk_saat": k[legs[0]].get("saat"), "senaryolar": sen, "firsat": sen["kotumser"]["roi_sifir_beceri"] >= ESIK,
             "firsat_orta": sen["orta"]["roi_sifir_beceri"] >= ESIK, "kuponlar": []}
        ay = []
        ok = True
        for kn in legs:
            at = [a for a in k[kn]["atlar"] if a.get("agf") and not a.get("kosmaz")]
            if len(at) < 3:
                ok = False; break
            tot = sum(a["agf"] for a in at)
            pp = {a["no"]: a["agf"] / tot for a in at}
            ham = {a["no"]: math.exp(obj.get("w0", 1.0) * math.log(max(pp[a["no"]], 1e-6)) + (a.get("z") or 0.0)) for a in at}
            Z = sum(ham.values())
            ay.append({no: (ham[no] / Z, pp[no]) for no in pp})
        if ok:
            for B in (48, 192, 768):
                s = kur(ay, B, "favori"); o = ozet(ay, s)
                r["kuponlar"].append({"butce": B, "kombinasyon": o["kombinasyon"], "ayaklar": [sorted(x) for x in s],
                                      "tutma_model": round(o["tutma_model"], 4), "tutma_agf": round(o["tutma_piyasa"], 4)})
        rows.append(r)
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "guncelleme": obj.get("guncelleme"), "medyan_net_havuz": round(med), "devirler": rows,
               "tum_devirler": dv}, open(os.path.join(SITE, "devir.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return rows
