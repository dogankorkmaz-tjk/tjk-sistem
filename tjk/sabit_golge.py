"""Sabit ihtimalli gölge kolu (3 Kasım 2026, T95 ileri ön kaydı + T98 genişleme: data/analiz/hipotez_defteri.md). Kağıt üstü, para yok.
Kural (sonuç görülmeden donduruldu): yarışa 7 dk kala ile yarış saati+3 dk arasındaki İLK çalışmada, o anda yayınlanmış son sabit oran (data/piyasa)
ile Jason olasılığı (piyasa girdisi o anki MUHTEMEL GANYAN (data/muh), yoksa AGF payı) çarpılır; EV >= 1,2 olan ata 1 TL:
  Tür G  (ganyan, tip 1001)        : P = p_Jason; kazanç sıra==1
  Tür FH (Favori Hariç, tip 1103)  : P = p / (1 - favori p'si); favori = 1103 listesinde olmayan tek at; kazanç = kalanlar arasında en önde
  Tür P2 (İlk 2, tip 1002)         : P = Plackett-Luce ilk 2; kazanç sıra<=2   (en az 5 at)
  Tür P3 (İlk 3, tip 1100)         : P = Plackett-Luce ilk 3; kazanç sıra<=3   (en az 6 at)
  Her tür için Kol A: EV>=1,2; Kol B: A şartı VE p_Jason >= pp (havuz payı).
Kombine kolları (K2, K3, KJ): gün içindeki ganyan (G) Kol A seçimlerinden, koşu başına en yüksek p_Jason'lı at alınır; K2 = en yüksek 2, K3 = en yüksek 3,
KJ = p_Jason>=0,25 olanlar (en az 2, en çok 4); tek kombine bahis (1 TL), kazanç = oranların çarpımı, hepsi kazanırsa. NOT: seçim gün sonunda tüm seçimlere bakılarak yapılır (ileri bilgi içerir) -> yalnız ipucu.
Kayıtlar ilk dondurulduğunda değişmez. Kesinti (at çıkması) ve ölü yarış hesaba katılmaz (tablo: 18+ oranda yok).
Tanılama: dondurmadan sonraki son yayınlanan oran ('son') ve yarışa kaç dk kala dondurulduğu ('dk') saklanır."""
import os, json, glob, math
import pandas as pd
from . import ortak as O

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE, PIY = os.path.join(KOK, "data", "sabit_golge"), os.path.join(KOK, "docs", "data"), os.path.join(KOK, "data", "piyasa")
ESIK_EV = 1.2
HIPKEY = {"diyarbakir": "DBAKIR"}
ONCE, SONRA = 7.0, 3.0     # dondurma penceresi: yarış saatinden ÖNCE 7 dk ... SONRA 3 dk
TIP = {"G": 1001, "FH": 1103, "P2": 1002, "P3": 1100}
MINAT = {"G": 4, "FH": 4, "P2": 5, "P3": 6}
TURLER = ("G", "FH", "P2", "P3")


def _dk(s):
    p = [int(x) for x in str(s).split(":")]
    return p[0] * 60 + p[1] + (p[2] / 60 if len(p) > 2 else 0)


def _oranlar(tarih, hip, kosu, simdi_dk=None, tip=1001):
    """Yayınlanmış en son sabit oran (tip); simdi_dk verilirse o ana kadar."""
    yol = os.path.join(PIY, tarih + ".csv.gz")
    if not os.path.exists(yol):
        return {}
    d = pd.read_csv(yol)
    d = d[(d.tip == tip) & (d.hipodrom == hip) & (d.kosu == kosu) & (d.oran > 1.0)]
    if simdi_dk is not None:
        d = d[d.saat.map(_dk) <= simdi_dk]
    if d.empty:
        return {}
    return {int(n): float(g.sort_values("saat").oran.iloc[-1]) for n, g in d.groupby("no")}


def _muh(tarih, hip, kosu, sn):
    """data/muh: yarışa kadar en son canlı muhtemel ganyan (havuz) -> {no: ganyan}; bayide ekranda görülen şey."""
    yol = os.path.join(KOK, "data", "muh", tarih + ".json")
    if not os.path.exists(yol):
        return {}
    try:
        m = json.load(open(yol, encoding="utf-8")).get(f"{HIPKEY.get(hip, hip.upper())}-{kosu}")
    except Exception:
        return {}
    if not m:
        return {}
    an = [a for a in m.get("anlik", []) if a.get("g") and a.get("t") and _dk(a["t"]) <= sn]
    return {int(n): float(v) for n, v in an[-1]["g"].items() if v is not None and float(v) > 1} if an else {}


def _top2(p, i):
    s = p[i]
    for j in range(len(p)):
        if j != i and p[j] < 1 - 1e-9:
            s += p[j] * p[i] / (1 - p[j])
    return s


def _top3(p, i):
    s = _top2(p, i)
    for j in range(len(p)):
        if j == i or p[j] >= 1 - 1e-9:
            continue
        for k in range(len(p)):
            if k == i or k == j:
                continue
            d = 1 - p[j] - p[k]
            if d > 1e-9:
                s += p[j] * p[k] / (1 - p[j]) * p[i] / d
    return s


def _kazandi(c, sonuc):
    """Seçimin türüne göre kazanıp kazanmadığı (sonuç dict: {no(str): {sira,...}})."""
    tur = c.get("tur", "G"); s = c.get("sira")
    if s is None:
        return None
    if tur == "P2":
        return int(s <= 2)
    if tur == "P3":
        return int(s <= 3)
    if tur == "FH":
        h = {str(x) for x in c.get("haric", [])}
        sr = [v["sira"] for n, v in sonuc.items() if n not in h and v and v.get("sira") is not None]
        return int(bool(sr) and s == min(sr))
    return int(s == 1)


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
                    oranG = _oranlar(tarih, h["id"], k["kosu"], sn)
                    if len(oranG) >= 4:
                        tot = sum(a["agf"] for a in at); pa = {a["no"]: a["agf"] / tot for a in at}   # AGF payı (yedek / tanılama)
                        gm = _muh(tarih, h["id"], k["kosu"], sn)
                        kaynak = "muh" if len(gm) >= max(4, 0.8 * len(at)) else "agf"
                        if kaynak == "muh":
                            tm = sum(1 / gm[a["no"]] for a in at if a["no"] in gm); pp = {a["no"]: (1 / gm[a["no"]]) / tm for a in at if a["no"] in gm}
                            at = [a for a in at if a["no"] in pp]
                        else:
                            pp = pa
                        s = {a["no"]: w0 * math.log(max(pp[a["no"]], 1e-6)) + l2 * math.log(max(pp[a["no"]], 1e-6)) ** 2 + a["z2"] for a in at}
                        m = max(s.values()); e = {n: math.exp(v - m) for n, v in s.items()}; Z = sum(e.values())
                        kay.setdefault("_bakildi", []).append(f"{h['id']}|{k['kosu']}")
                        nolar = [a["no"] for a in at]; P = [e[n] / Z for n in nolar]; pjd = dict(zip(nolar, P))
                        for tur in TURLER:
                            if len(at) < MINAT[tur]:
                                continue
                            oran = oranG if tur == "G" else _oranlar(tarih, h["id"], k["kosu"], sn, TIP[tur])
                            haric = []
                            if tur == "FH":
                                if len(oran) < 4:
                                    continue
                                haric = [n for n in nolar if n not in oran]
                                if len(haric) != 1:
                                    continue
                            elif len(oran) < 4:
                                continue
                            pfh = 1 - sum(pjd[n] for n in haric) if tur == "FH" else 1.0
                            for i, a in enumerate(at):
                                o = oran.get(a["no"])
                                if not o:
                                    continue
                                pr = {"G": P[i], "FH": P[i] / pfh if pfh > 1e-9 else 0.0, "P2": _top2(P, i), "P3": _top3(P, i)}[tur]
                                if pr * o >= ESIK_EV:
                                    key = f"{h['id']}|{k['kosu']}|{a['no']}" + ("" if tur == "G" else "|" + tur)
                                    kay[key] = {"tur": tur, "hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": k.get("saat"), "no": a["no"], "at": a["at"],
                                                "pj": round(P[i], 4), "pt": round(pr, 4), "pp": round(pp[a["no"]], 4), "oran": o, "ev": round(pr * o, 3),
                                                "B": bool(P[i] >= pp[a["no"]]), "dk": round(kalan, 1), "pkaynak": kaynak, **({"haric": haric} if haric else {})}
            for key, c in kay.items():
                if key.startswith("_") or c["hipodrom"] != h["id"] or c["kosu"] != k["kosu"] or "sira" in c:
                    continue
                v = sonuc.get(str(c["no"]))
                if v and v.get("sira") is not None:
                    c["sira"] = v["sira"]; c["g"] = v.get("g"); c["k"] = _kazandi(c, sonuc)
                    son = _oranlar(tarih, h["id"], k["kosu"], None, TIP[c.get("tur", "G")]).get(c["no"])
                    if son:
                        c["son"] = son
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def _k(c):
    return c["k"] if "k" in c else int(c.get("sira") == 1)


def _kombineler(secimler):
    """Bir günün G Kol A seçimlerinden K2, K3, KJ: {kol: [bacaklar]}; koşu başına en yüksek p_Jason'lı at."""
    en = {}
    for c in secimler:
        kk = (c["hipodrom"], c["kosu"])
        if kk not in en or c["pj"] > en[kk]["pj"]:
            en[kk] = c
    L = sorted(en.values(), key=lambda c: -c["pj"]); out = {}
    if len(L) >= 2:
        out["K2"] = L[:2]
    if len(L) >= 3:
        out["K3"] = L[:3]
    kj = [c for c in L if c["pj"] >= 0.25][:4]
    if len(kj) >= 2:
        out["KJ"] = kj
    return out


def _durum(bacak):
    if any("sira" in c and not _k(c) for c in bacak):
        return "kaybetti"
    if all("sira" in c and _k(c) for c in bacak):
        return "kazandı"
    return "bekliyor"


def ozet_yaz(tarih):
    T = {t: {"A": [0, 0, 0.0], "B": [0, 0, 0.0]} for t in TURLER}   # [bahis, kazanan, kazanç]
    K = {"K2": [0, 0, 0.0], "K3": [0, 0, 0.0], "KJ": [0, 0, 0.0]}
    for y in sorted(glob.glob(os.path.join(VERI, "*.json"))):
        gun = json.load(open(y, encoding="utf-8"))
        for key, c in gun.items():
            if key.startswith("_") or "sira" not in c:
                continue
            tur = c.get("tur", "G")
            for kol in ("A", "B"):
                if kol == "B" and not c.get("B"):
                    continue
                T[tur][kol][0] += 1; T[tur][kol][1] += _k(c); T[tur][kol][2] += c["oran"] if _k(c) else 0
        gs = [c for k_, c in gun.items() if not k_.startswith("_") and c.get("tur", "G") == "G"]
        for kol, b in _kombineler(gs).items():
            d = _durum(b)
            if d == "bekliyor":
                continue
            K[kol][0] += 1; K[kol][1] += d == "kazandı"; K[kol][2] += math.prod(c["oran"] for c in b) if d == "kazandı" else 0
    yol = os.path.join(VERI, tarih + ".json")
    gun = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    bugun = [c for k, c in gun.items() if not k.startswith("_")]
    kb = {kol: {"oran": round(math.prod(c["oran"] for c in b), 2), "durum": _durum(b), "bacaklar": [{"ad": c.get("ad") or c["hipodrom"], "kosu": c["kosu"], "no": c["no"], "at": c["at"], "oran": c["oran"], "pj": c["pj"]} for c in b]}
          for kol, b in _kombineler([c for c in bugun if c.get("tur", "G") == "G"]).items()}
    f = lambda v: {"bahis": v[0], "kazanan": v[1], "kazanc": round(v[2], 2), "geri_donus": round(v[2] / v[0], 3) if v[0] else None}
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "esik": ESIK_EV, "bugun": bugun, "kombine_bugun": kb,
               "toplam": {k: f(v) for k, v in T["G"].items()},
               "toplam_tur": {t: {k: f(v) for k, v in T[t].items()} for t in TURLER if t != "G"},
               "toplam_kombine": {k: f(v) for k, v in K.items()}},
              open(os.path.join(SITE, "sabit_golge.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
