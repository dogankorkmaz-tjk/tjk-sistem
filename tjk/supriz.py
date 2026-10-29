"""SÜPRİZ GÖLGESİ (T57; ön kayıt hipotez_defteri 2026-10-30). Oranı >=15 atlarda donmuş ağaç modeli (T55 N, eğitim 2023-06..2026-03).
Bayrak: model/taban olasılık oranı r >= 1,686. YALNIZ izleme; kupon/EV ile bağlantısı YOK.
Üç adım (hepsi hata verirse sessizce atlanır, ana hattı bozmaz):
  ozellik_yaz(dj, tarih)  sabah: bugünün atları için piyasadan bağımsız özellikleri data/supriz/ozellik/<gün>.json.gz'ye yazar
  bayrak_guncelle(obj)    yarışa yakın: TJK canlı muhtemel ganyanıyla bayrak üretir -> data/supriz/canli/<gün>.json + docs/data/supriz_canli.json
  skor_yaz(temiz)         ertesi sabah: kapanış ganyanıyla (eğitimdeki tanım) puanla -> data/supriz/skor.csv.gz + docs/data/supriz.json
"""
import os, json, gzip, math, datetime
import numpy as np
import pandas as pd

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DS = os.path.join(KOK, "data", "supriz")
SITE = os.path.join(KOK, "docs", "data")
_M = None


def yukle():
    global _M
    if _M is None:
        p = os.path.join(DS, "model_n.json")
        _M = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    return _M or None


def _agac(n, x):
    while "leaf_value" not in n:
        v = x[n["split_feature"]]; mt = n.get("missing_type")
        if v is None or v != v:
            if mt == "NaN": git_sol = n["default_left"]
            else: v = 0.0; git_sol = v <= n["threshold"]
        elif mt == "Zero" and abs(v) <= 1e-35: git_sol = n["default_left"]
        else: git_sol = v <= n["threshold"]
        n = n["left_child"] if git_sol else n["right_child"]
    return n["leaf_value"]


def ham_skor(M, x):
    """Ağaç toplamı (taban logit'e eklenen kısım). x: özellik listesi (M['feat'] sırası, NaN olabilir)."""
    return sum(_agac(t, x) for t in M["agaclar"])


def _nan(v):
    return None if v is None or (isinstance(v, float) and v != v) else v


def _yol_oz(tarih): return os.path.join(DS, "ozellik", tarih + ".json.gz")


# ---------------------------------------------------------------- sabah: piyasasız özellikler
def ozellik_yaz(dj, tarih):
    """dj: elo.ekle çıktısı (geçmiş + bugün, 'yeni' bayrağı). Her bugünkü at için piyasadan bağımsız özellikler; lp0 ve gevsek canlı/kapanışta eklenir."""
    try:
        M = yukle()
        if not M:
            return 0
        d = dj.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
        d["_key"] = d["at"].astype(str) + "|" + d["baba"].astype(str)
        g = d.groupby("_key", sort=False)
        d["on_ganyan"] = g.ganyan.shift(1); d["on_kapi"] = g.st.shift(1) / g.n_at.shift(1); d["on_hnd"] = g.hnd.shift(1)
        d["kapi"] = d.st / d.n_at; d["kapi_iy"] = d.on_kapi - d.kapi
        d["jok_deg"] = ((d.jokey != d.son_jokey) & d.son_jokey.notna()).astype(float)
        d["kilo_f"] = d.kilo - d.son_kilo; d["hnd_f"] = d.hnd - d.on_hnd; d["dinlenme"] = np.log1p(d.kgs)
        d["pist_k"] = d.pist.map({p: i for i, p in enumerate(M["pist"])}).fillna(-1)
        d["hip_k"] = d.hipodrom.map({p: i for i, p in enumerate(M["hip"])}).fillna(-1)
        y = d[d.yeni & (d.tarih == tarih)]
        FN = M["feat"]; eksik = [c for c in FN if c not in d.columns and c not in ("lp0", "gevsek")]
        if eksik:
            print("süpriz: eksik özellik", eksik[:6]); return 0
        out = {}
        for r in y.itertuples(index=False):
            row = r._asdict(); x = []
            for c in FN:
                if c in ("lp0", "gevsek"): x.append(None)
                else:
                    v = row.get(c); v = None if v is None or (isinstance(v, float) and v != v) else round(float(v), 5); x.append(v)
            og = row.get("on_ganyan"); og = None if og is None or og != og else float(og)
            out[f"{row['hipodrom']}|{int(row['kosu'])}|{int(row['no'])}"] = {"at": str(row["at"]), "x": x, "og": og}
        os.makedirs(os.path.dirname(_yol_oz(tarih)), exist_ok=True)
        with gzip.open(_yol_oz(tarih), "wt", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        print("süpriz özellik yazıldı:", len(out), "at")
        return len(out)
    except Exception as e:
        print("süpriz özellik hatası:", repr(e)); return 0


def _oz_oku(tarih):
    p = _yol_oz(tarih)
    if not os.path.exists(p): return None
    with gzip.open(p, "rt", encoding="utf-8") as f: return json.load(f)


def _sig(z): return 1 / (1 + math.exp(-z))


def degerlendir(M, rec, p_piyasa, ganyan):
    """Tek at: (p_taban, p_model, r) ya da None (evren dışı: ganyan<15)."""
    if ganyan is None or ganyan < 15 or p_piyasa is None or p_piyasa <= 0: return None
    x = list(rec["x"]); FN = M["feat"]
    x[FN.index("lp0")] = math.log(max(p_piyasa, 1e-6))
    og = rec.get("og"); x[FN.index("gevsek")] = (math.log(ganyan) - math.log(og)) if og and og > 0 else None
    zb = M["b"][0] + M["b"][1] * x[FN.index("lp0")]; zm = zb + ham_skor(M, x)
    pb, pm = _sig(zb), _sig(zm)
    return pb, pm, pm / pb


# ---------------------------------------------------------------- yarış öncesi: canlı muhtemel ganyanla bayrak
def bayrak_guncelle(obj, kapanis_dk=-1.5, pencere_dk=30.0, simdi=None, yaz=True):
    try:
        M = yukle(); tarih = obj["tarih"]
        Z = _oz_oku(tarih); mp = os.path.join(KOK, "data", "muh", tarih + ".json")
        if not (M and Z and os.path.exists(mp)): return 0
        MH = json.load(open(mp, encoding="utf-8")); MI = {}
        for _k, _v in MH.items():
            sl = str(_v.get("slug") or "").split("-")[0]; MI[(sl, _v.get("kosu"))] = _v
            MI[(str(_v.get("hipodrom") or "").lower(), _v.get("kosu"))] = _v
        MI.update({("diyarbakir", kk[1]): vv for kk, vv in list(MI.items()) if kk[0] in ("dbakir", "diyarbakir")})
        cy = os.path.join(DS, "canli", tarih + ".json")
        C = json.load(open(cy, encoding="utf-8")) if os.path.exists(cy) else {}
        simdi = simdi or (datetime.datetime.utcnow() + datetime.timedelta(hours=3)); sdk = simdi.hour * 60 + simdi.minute + simdi.second / 60
        n = 0
        for h in obj["hipodromlar"]:
            for k in h["kosular"]:
                if k.get("sonuc"): continue
                try: dk = int(k["saat"][:2]) * 60 + int(k["saat"][3:5]) - sdk
                except Exception: continue
                if dk < kapanis_dk or dk > pencere_dk: continue
                m = MI.get((h["id"], k["kosu"]))
                an = [a for a in (m or {}).get("anlik", []) if a.get("durum") == "AÇIK" and a.get("g")]
                if not an or an[-1].get("dk") is None or an[-1]["dk"] - dk > 10: continue
                son = an[-1]; at = [a for a in k["atlar"] if not a.get("kosmaz")]
                g = {a["no"]: son["g"].get(str(a["no"])) for a in at}
                if len(at) < 5 or sum(1 for v in g.values() if v and v > 0) < len(at) - 1: continue
                inv = {no: 1 / v for no, v in g.items() if v and v > 0}; z = sum(inv.values())
                bay = []
                for no, v in g.items():
                    rec = Z.get(f"{h['id']}|{k['kosu']}|{no}")
                    if not rec or not v or v <= 0: continue
                    r = degerlendir(M, rec, inv[no] / z, v)
                    if r: bay.append({"no": no, "at": rec["at"], "g": v, "pb": round(r[0], 5), "pm": round(r[1], 5), "r": round(r[2], 3), "bayrak": bool(r[2] >= M["esik"])})
                C[f"{h['id']}|{k['kosu']}"] = {"t": simdi.strftime("%H:%M:%S"), "dk": round(dk, 1), "saat": k["saat"], "uzun": bay}
                n += 1
        if n and yaz:
            os.makedirs(os.path.dirname(cy), exist_ok=True)
            json.dump(C, open(cy, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
            json.dump({"tarih": tarih, "esik": M["esik"], "yarislar": C}, open(os.path.join(SITE, "supriz_canli.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        return n if yaz else C
    except Exception as e:
        print("süpriz bayrak hatası:", repr(e)); return 0


# ---------------------------------------------------------------- ertesi gün: kapanış ganyanıyla puanlama
def skor_yaz(temiz):
    """temiz: oku('temiz') (sonuçlar, p_piyasa, ganyan, kazandi). Özellik dosyası olup henüz puanlanmamış günleri puanlar; özet JSON üretir."""
    try:
        M = yukle()
        if not M: return 0
        yol = os.path.join(DS, "skor.csv.gz")
        S = pd.read_csv(yol) if os.path.exists(yol) else pd.DataFrame(columns=["tarih", "hipodrom", "kosu", "no", "at", "ganyan", "pb", "pm", "r", "kazandi"])
        yapilan = set(S.tarih.astype(str)); yeni = []
        klas = os.path.join(DS, "ozellik")
        for f in sorted(os.listdir(klas)) if os.path.isdir(klas) else []:
            t = f[:10]
            if t in yapilan: continue
            tt = temiz[temiz.tarih == t]
            if len(tt) == 0: continue                           # sonuçlar henüz yok
            Z = _oz_oku(t)
            for r in tt.itertuples(index=False):
                if getattr(r, "kosmadi", False) or r.ganyan is None: continue
                rec = Z.get(f"{r.hipodrom}|{int(r.kosu)}|{int(r.no)}")
                if not rec: continue
                e = degerlendir(M, rec, float(r.p_piyasa), float(r.ganyan))
                if e: yeni.append((t, r.hipodrom, int(r.kosu), int(r.no), rec["at"], float(r.ganyan), e[0], e[1], e[2], int(r.kazandi)))
        if yeni:
            S = pd.concat([S, pd.DataFrame(yeni, columns=S.columns)], ignore_index=True)
            S.to_csv(yol, index=False, compression="gzip")
        _ozet(S, M)
        return len(yeni)
    except Exception as e:
        print("süpriz skor hatası:", repr(e)); return 0


def _ozet(S, M):
    esik = M["esik"]; os.makedirs(SITE, exist_ok=True)
    if len(S) == 0:
        json.dump({"esik": esik, "gun": 0}, open(os.path.join(SITE, "supriz.json"), "w"), ensure_ascii=False); return
    S = S.copy()
    for c in ("ganyan", "pb", "pm", "r", "kazandi"): S[c] = pd.to_numeric(S[c])
    S["bay"] = S.r >= esik; B = S[S.bay]
    zb = np.log(S.pb / (1 - S.pb)); zm = np.log(S.pm / (1 - S.pm)); y = S.kazandi.values.astype(float)
    ll = lambda z: -(y * np.log(1 / (1 + np.exp(-z)) + 1e-12) + (1 - y) * np.log(1 - 1 / (1 + np.exp(-z)) + 1e-12))
    dl = ll(zb.values) - ll(zm.values)                       # + = model taban'dan iyi
    rng = np.random.default_rng(57); ug = S.tarih.unique(); gi = {t: np.where(S.tarih.values == t)[0] for t in ug}
    bs = [dl[np.concatenate([gi[t] for t in rng.choice(ug, len(ug))])].mean() for _ in range(400)] if len(ug) >= 5 else [np.nan]
    ret = B.kazandi.values * B.ganyan.values - 1.0
    gunluk = B.groupby("tarih").size()
    son = B.sort_values(["tarih", "hipodrom", "kosu"]).tail(40)
    out = {"esik": esik, "gun": int(len(ug)), "evren": int(len(S)), "evren_kazanan": int(S.kazandi.sum()),
           "bayrak": int(len(B)), "bayrak_kazanan": int(B.kazandi.sum()),
           "bayrak_kazanma": float(B.kazandi.mean()) if len(B) else None, "bayrak_taban": float(B.pb.mean()) if len(B) else None,
           "bayrak_model": float(B.pm.mean()) if len(B) else None,
           "roi_1tl": float(ret.mean()) if len(B) else None, "ort_oran": float(B.ganyan.mean()) if len(B) else None,
           "ll_iyilesme_milli": float(dl.mean() * 1000), "ll_ga": [float(np.nanpercentile(bs, 2.5) * 1000), float(np.nanpercentile(bs, 97.5) * 1000)],
           "gunluk_ort": float(gunluk.mean()) if len(gunluk) else 0.0, "gunluk_max": int(gunluk.max()) if len(gunluk) else 0,
           "son": [{"t": r.tarih, "h": r.hipodrom, "k": int(r.kosu), "no": int(r.no), "at": r.at, "g": float(r.ganyan), "r": round(float(r.r), 2), "w": int(r.kazandi)} for r in son.itertuples()]}
    json.dump(out, open(os.path.join(SITE, "supriz.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
