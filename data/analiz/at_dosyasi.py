"""AT DOSYASI: her at için tek kayıt (kimlik, soy, tüm koşular, sonuç, video özeti, spiker olayları, galop, tahmin izi, karne).
Çalıştır: python3 data/analiz/at_dosyasi.py  (arka planda; çıktı data/at/s_XX.json.gz + data/at/indeks.json.gz + data/at/ozet.txt)
Anahtar: ad | doğum (epoch) | baba   (TJK 'id' alanı boş; galop at_id yalnız 2026'dan).
Hiçbir model/üretim dosyasına yazmaz. Bilgi amaçlıdır; test ayrı ön kayıtla yapılır."""
import os, sys, glob, gzip, json, re, hashlib, time, collections
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from tjk import spiker_ayikla as SA

KOK = "."
CIKTI = "data/at"; os.makedirs(CIKTI, exist_ok=True)
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.0f}s]", *a, flush=True)

def nm(x, k="name"):
    if isinstance(x, dict): return (x.get(k) or "").strip()
    return ""

# ---------------------------------------------------------------- 1) atyarisi: koşu-at satırları
SATIR = {}      # (tarih,hip,kosu,no) -> dict
KOSU = {}       # (tarih,hip,kosu) -> {mesafe, grup, tur}
for f in sorted(glob.glob("data/atyarisi/20*.json.gz")):
    try: x = json.load(gzip.open(f))
    except Exception: continue
    gun = x.get("tarih") or os.path.basename(f)[:10]
    for hip, L in (x.get("program") or {}).items():
        for r in L or []:
            k = int(r.get("number") or 0)
            KOSU[(gun, hip, k)] = dict(mesafe=r.get("distance"), grup=r.get("groupName") or r.get("groupNameAbbreviation"), tur=r.get("typeDescription"), cins=r.get("gender"))
            for h in r.get("horses") or []:
                try: no = int(h.get("number"))
                except Exception: continue
                p = h.get("parents") or {}
                SATIR[(gun, hip, k, no)] = dict(
                    ad=(h.get("name") or "").strip(), dogum=h.get("birthdateEpoch"), baba=nm(p.get("father")), anne=nm(p.get("mother")),
                    anne_baba=nm(p.get("fatherOfMother")), baba_baba=nm(p.get("fatherOfFather")),
                    yetistirici=nm(h.get("breeder")), sahip=nm(h.get("owner")), antrenor=nm(h.get("coach")),
                    jokey=nm(h.get("jockey")), kg=h.get("weight"), hnd=h.get("handicap"), ekipman=h.get("equipment"), yas=h.get("age"),
                    gan_prog=h.get("ganyan"), start=h.get("start"), son20=h.get("last20"))
log("atyarisi satır:", len(SATIR), "koşu:", len(KOSU))

# ---------------------------------------------------------------- 2) sonuçlar (temiz) ve farklar (zengin)
T = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/temiz/20*.csv.gz"))])
SON = {}
for r in T.itertuples():
    SON[(r.tarih, r.hipodrom, int(r.kosu), int(r.no))] = dict(sira=None if pd.isna(r.sira) else int(r.sira), derece=None if pd.isna(r.derece_sn) else float(r.derece_sn),
                                                            gan=None if pd.isna(r.ganyan) else float(r.ganyan), kosmadi=bool(r.kosmadi) if not pd.isna(r.kosmadi) else False)
Z = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/zengin/20*.csv.gz"))])
FARK = {(r.tarih, r.hipodrom, int(r.kosu), int(r.no)): (None if pd.isna(r.fark_boy) else float(r.fark_boy)) for r in Z.itertuples()}
log("sonuç:", len(SON), "fark:", len(FARK))

# ---------------------------------------------------------------- 3) video özeti
VID = {}
for f in glob.glob("data/video_seyir/20*_*.json"):
    b = os.path.basename(f)[:-5]; m = re.match(r"(\d{4}-\d\d-\d\d)_(.+)_(\d+)$", b)
    if not m: continue
    try: d = json.load(open(f))
    except Exception: continue
    oz = d.get("ozet") or {}; n = d.get("at_sayisi") or len(oz) or None
    for no, v in oz.items():
        try: v2 = {kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in v.items()}
        except Exception: continue
        v2["n"] = n; VID[(m.group(1), m.group(2), int(m.group(3)), int(no))] = v2
log("video at-koşu:", len(VID))

# ---------------------------------------------------------------- 4) spiker olayları
SP = {}
for f in glob.glob("data/spiker/*/*.json.gz"):
    b = os.path.basename(f)[:-8]; m = re.match(r"(\d{4}-\d\d-\d\d)_(.+)_(\d+)$", b)
    if not m: continue
    try:
        j = json.load(gzip.open(f)); ol = SA.olaylar(j["seg"]); ko = SA.konum(j["seg"], float(j["sure"]))
    except Exception: continue
    nk = len(ko)
    for no in set(ol) | set(ko):
        e = [dict(tur=t, boy=b_) for (t, s, b_, *_) in ol.get(no, [])]
        v = dict(olay=e)
        kk = ko.get(no) or {}
        if "erken" in kk: v["erken"] = kk["erken"]; v["n"] = nk
        for q in ("orta", "son"):
            if q in kk: v[q] = kk[q]
        SP[(m.group(1), m.group(2), int(m.group(3)), int(no))] = v
log("spiker at-koşu:", len(SP))

# ---------------------------------------------------------------- 5) modelin tahmin izi (docs/data/gun)
TAH = {}
for f in glob.glob("docs/data/gun/20*.json"):
    try: d = json.load(open(f, encoding="utf-8"))
    except Exception: continue
    for h in d.get("hipodromlar", []):
        for k in h.get("kosular", []):
            for a in k.get("atlar", []):
                try: no = int(a["no"])
                except Exception: continue
                TAH[(d["tarih"], h["id"], int(k["kosu"]), no)] = {q: a.get(q) for q in ("z6", "z6b", "agf", "agf0") if a.get(q) is not None}
log("tahmin izi:", len(TAH))

# ---------------------------------------------------------------- 6) kimlik anahtarı ve at kayıtları
import datetime as _dt
def _yil(e):
    try: y = _dt.datetime.utcfromtimestamp(int(e)).year
    except Exception: return None
    return y if 1995 <= y <= 2025 else None        # 2026+ doğum = kaynak hatası (örn. 1792798140); aynı atın geçmişini böler
_YIL = collections.defaultdict(set)
for _s in SATIR.values():
    if _s["ad"] and _yil(_s["dogum"]): _YIL[(_s["ad"], _s["baba"])].add(_yil(_s["dogum"]))
def anahtar(s):
    y = _yil(s["dogum"])
    if y is None:
        c = _YIL.get((s["ad"], s["baba"]), set()); y = next(iter(c)) if len(c) == 1 else "?"
    return f'{s["ad"]}|{y}|{s["baba"]}'
AT = {}
for kk in sorted(SATIR):
    s = SATIR[kk]
    if not s["ad"]: continue
    a = AT.setdefault(anahtar(s), dict(ad=s["ad"], dogum=(s["dogum"] if _yil(s["dogum"]) else None), baba=s["baba"], anne=s["anne"], anne_baba=s["anne_baba"], baba_baba=s["baba_baba"],
                                       yetistirici=s["yetistirici"], sahip=s["sahip"], antrenor=s["antrenor"], kosular=[], galop=[]))
    a["sahip"] = s["sahip"] or a["sahip"]; a["antrenor"] = s["antrenor"] or a["antrenor"]; a["yetistirici"] = s["yetistirici"] or a["yetistirici"]
    gun, hip, k, no = kk; ko = KOSU.get((gun, hip, k), {})
    r = dict(t=gun, hip=hip, k=k, no=no, mesafe=ko.get("mesafe"), grup=ko.get("grup"), jokey=s["jokey"], kg=s["kg"], hnd=s["hnd"], ekipman=s["ekipman"], gan_prog=s["gan_prog"])
    so = SON.get(kk)
    if so: r.update(sira=so["sira"], derece=so["derece"], gan=so["gan"], kosmadi=so["kosmadi"])
    if kk in FARK and FARK[kk] is not None: r["fark_boy"] = FARK[kk]
    if kk in VID: r["video"] = VID[kk]
    if kk in SP: r["spiker"] = SP[kk]
    if kk in TAH: r["tahmin"] = TAH[kk]
    a["kosular"].append(r)
log("at sayısı:", len(AT), "koşu-at:", sum(len(a["kosular"]) for a in AT.values()))

# ---------------------------------------------------------------- 7) galop (ad ile; belirsiz adlar atlanır)
ADK = collections.defaultdict(set)
for k_, a in AT.items(): ADK[a["ad"]].add(k_)
G = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/galop/20*.csv.gz"))]); bel = 0; esl = 0
for r in G.to_dict("records"):
    ks = ADK.get(str(r["at"]).strip())
    if not ks: continue
    if len(ks) > 1: bel += 1; continue
    k_ = next(iter(ks)); esl += 1
    AT[k_]["galop"].append({q: (None if pd.isna(v) else v) for q, v in r.items() if q in ("it", "hip", "pist", "tur", "durum", "p400", "p600", "p800", "p1000", "p1200", "p1400", "pdur")})
    AT[k_].setdefault("at_id", r["at_id"])
log("galop satırı eşleşti:", esl, "belirsiz ad (atlandı):", bel)

# ---------------------------------------------------------------- 8) karne
def karne(a):
    K = sorted(a["kosular"], key=lambda r: (r["t"], r["k"])); ck = [r for r in K if r.get("sira") and not r.get("kosmadi")]
    q = dict(n_kosu=len(K), n_sonuc=len(ck), ilk=K[0]["t"], son=K[-1]["t"])
    if ck:
        s = np.array([r["sira"] for r in ck], float); q["galibiyet"] = int((s == 1).sum()); q["ilk3"] = int((s <= 3).sum()); q["ort_sira"] = round(float(s.mean()), 2)
        if len(s) >= 6: q["son5_ort_sira"] = round(float(s[-5:].mean()), 2); q["onceki_ort_sira"] = round(float(s[:-5].mean()), 2)
        gun = pd.to_datetime([r["t"] for r in ck]);
        if len(gun) > 1: q["ort_dinlenme_gun"] = round(float(np.diff(gun.values).astype("timedelta64[D]").astype(float).mean()), 1)
    q["jokey_sayisi"] = len({r["jokey"] for r in K if r["jokey"]})
    ev = collections.Counter(e["tur"] for r in K[-5:] for e in (r.get("spiker") or {}).get("olay", []))
    if ev: q["son5_olaylar"] = dict(ev)
    er = [r["spiker"]["erken"] / r["spiker"]["n"] for r in K if (r.get("spiker") or {}).get("erken") and (r["spiker"].get("n") or 0) > 3]
    if er: q["spiker_erken_norm"] = round(float(np.mean(er)), 3); q["spiker_erken_n"] = len(er)
    ve = [r["video"]["erken"] / r["video"]["n"] for r in K if (r.get("video") or {}).get("erken") and (r["video"].get("n") or 0) > 3]
    if ve: q["video_erken_norm"] = round(float(np.mean(ve)), 3); q["video_erken_n"] = len(ve)
    return q
for a in AT.values(): a["karne"] = karne(a)
log("karne bitti")

# ---------------------------------------------------------------- 9) yaz (256 parça + indeks)
PARCA = collections.defaultdict(dict); IDX = {}
for k_, a in AT.items():
    sh = hashlib.md5(k_.encode()).hexdigest()[:2]; PARCA[sh][k_] = a
    IDX[k_] = [sh, a["ad"], a["karne"]["n_kosu"], a["karne"]["son"]]
for sh, d in PARCA.items():
    with gzip.open(f"{CIKTI}/s_{sh}.json.gz", "wt", encoding="utf-8") as fh: json.dump(d, fh, ensure_ascii=False, separators=(",", ":"))
with gzip.open(f"{CIKTI}/indeks.json.gz", "wt", encoding="utf-8") as fh: json.dump(IDX, fh, ensure_ascii=False, separators=(",", ":"))
# özet
n = len(AT); L = [a["karne"] for a in AT.values()]
oz = [f"at: {n}", f"koşu-at kaydı: {sum(l['n_kosu'] for l in L)}", f"≥5 koşusu olan at: {sum(l['n_kosu']>=5 for l in L)}",
      f"sonuçlu koşu-at: {sum(l['n_sonuc'] for l in L)}",
      f"videosu olan koşu-at: {sum(1 for a in AT.values() for r in a['kosular'] if 'video' in r)}",
      f"spiker kaydı olan koşu-at: {sum(1 for a in AT.values() for r in a['kosular'] if 'spiker' in r)}",
      f"tahmin izi olan koşu-at: {sum(1 for a in AT.values() for r in a['kosular'] if 'tahmin' in r)}",
      f"galop kaydı olan at: {sum(1 for a in AT.values() if a['galop'])}  (galop satırı {sum(len(a['galop']) for a in AT.values())})",
      f"anahtar çakışması (aynı ad, birden çok anahtar): {sum(1 for v in ADK.values() if len(v)>1)} ad",
      f"belirsiz doğum yılı (?) anahtarı: {sum(1 for k_ in AT if k_.split('|')[1] in ('?','None'))}"]
open(f"{CIKTI}/ozet.txt", "w", encoding="utf-8").write("\n".join(oz) + "\n"); log("\n" + "\n".join(oz))
