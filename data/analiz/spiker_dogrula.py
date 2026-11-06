"""Spiker ayıklamasının doğruluğu: (1) geç çıkış (spiker 'gec_cikis') ↔ resmî delayedExit (at düzeyi kesinlik/duyarlılık);
(2) spiker erken sırası ↔ video şeridi 'erken' sırası (koşu içi Spearman); (3) tür başına olay sıklığı (koşu başına).
Kullanım: python3 data/analiz/spiker_dogrula.py"""
import sys, os, glob, gzip, json, numpy as np, pandas as pd
sys.path.insert(0, "."); from tjk import spiker_ayikla as SA
from scipy.stats import spearmanr

AYAR = set(open("data/analiz/spiker_ayar_kumesi.txt").read().split())   # kuralların ayarlandığı koşular (6 Kasım); doğruluk bunların DIŞINDA raporlanır
KUME = sys.argv[1] if len(sys.argv) > 1 else "disi"                    # "disi" (varsayılan) | "ayar" | "hepsi"
R = []; SP = []; TUR = {}
for f in sorted(glob.glob("data/spiker/*/*.json.gz")):
    ad = os.path.basename(f)[:-8]; t, hip, k = ad.rsplit("_", 2)[0], ad.rsplit("_", 2)[1], int(ad.rsplit("_", 2)[2])
    if (KUME == "disi" and ad in AYAR) or (KUME == "ayar" and ad not in AYAR): continue
    j = json.load(gzip.open(f)); seg = j["seg"]
    try: A = json.load(gzip.open(f"data/atyarisi/{t}.json.gz"))
    except Exception: continue
    r = [x for x in (A.get("sonuc") or {}).get(hip, []) if int(x.get("number", -1)) == k]
    if not r: continue
    H = r[0].get("horses") or []; nos = {int(h["number"]) for h in H if h.get("number") is not None}
    P = [x for x in (A.get("program") or {}).get(hip, []) if int(x.get("number", -1)) == k]
    adlar = {int(h["number"]): h.get("name") for h in (P[0]["horses"] if P else []) if h.get("number") is not None}
    jok = {int(h["number"]): (h.get("jockey") or {}).get("name") for h in (P[0]["horses"] if P else []) if h.get("number") is not None and isinstance(h.get("jockey"), dict)}
    resmi = {int(h["number"]) for h in H if h.get("delayedExit")}
    O = SA.olaylar(seg, nos, jok, adlar); sp = {n for n, L in O.items() if any(o[0] == "gec_cikis" for o in L)}
    for n in nos: R.append(dict(ad=ad, no=n, resmi=n in resmi, spiker=n in sp))
    for L in O.values():
        for o in L: TUR[o[0]] = TUR.get(o[0], 0) + 1
    v = f"data/video_seyir/{ad}.json"
    if os.path.exists(v):
        oz = json.load(open(v)).get("ozet") or {}
        K = SA.konum(seg, j["sure"], nos); x = [(K[n]["erken"], oz[str(n)]["erken"]) for n in K if "erken" in K[n] and str(n) in oz and oz[str(n)].get("erken") is not None]
        if len(x) >= 4: SP.append(spearmanr(*zip(*x)).correlation)
D = pd.DataFrame(R); n = D.ad.nunique()
if not n: print("henüz transkript yok"); sys.exit()
tp = (D.resmi & D.spiker).sum(); fp = (~D.resmi & D.spiker).sum(); fn = (D.resmi & ~D.spiker).sum()
print(f"[{KUME}] koşu {n}, at {len(D)} | geç çıkış: resmî {int(D.resmi.sum())}, spiker {int(D.spiker.sum())}, ikisi {tp} → kesinlik {tp / max(1, tp + fp):.2f}, duyarlılık {tp / max(1, tp + fn):.2f}")
print("koşu başına olay (tür):", {k: round(v / n, 3) for k, v in sorted(TUR.items())}, "| toplam", round(sum(TUR.values()) / n, 3))
if SP: print(f"erken sıra: spiker ↔ video şeridi Spearman medyan {np.median(SP):.2f} (koşu {len(SP)})")
