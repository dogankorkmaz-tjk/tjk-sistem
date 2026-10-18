"""Otomatik ileriye dönük kâğıt üstü test (ön kayıt: hipotez_defteri.md, 18 Ekim 2026).
Kayıt: data/abd_oto/<gün>.json = koşu başlamadan önceki SON yerel (Sporting Life) oran görüntüsü.
Kural (değişmez): q = normalize(1/oran); q x TJK KAPANIŞ ganyanı > 1,25 -> 1 TL ganyan. Ödeme: TJK resmî ganyanı.
Not: bahis anı TJK ganyanı yok; kapanış ganyanı üst sınırdır (bayide yakalanabilirlik ayrıca ölçülmeli).
Çıktı: docs/data/abd_oto_sonuc.json. Kullanım: python3 -I data/analiz/abd_oto_degerlendir.py"""
import glob, json, os, re
import numpy as np, pandas as pd

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ESIK = 1.25
ULKE_TJK = {"abd": "abd", "birlesik-krallik": "birlesik-krallik", "irlanda": "irlanda", "fransa": "fransa", "guney-afrika": "guney-afrika"}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def ad(s):
    return re.sub(r"\(\d+\)\s*$", "", str(s)).strip().upper()


def ulke_yer(yer):
    y = slug(yer or "")
    for k, u in (("abd", "abd"), ("kanada", "abd"), ("ngiltere", "birlesik-krallik"), ("rlanda", "irlanda"), ("fransa", "fransa"), ("guney-afrika", "guney-afrika")):
        if y.endswith(k) or ("-" + k) in y:
            return u
    return "diger"


def muh_tablo():
    """data/muh/*.json -> satır tablosu. ganyan = RESMÎ kapanış, g_anlik = başlamadan önceki son AÇIK muhtemel ganyan (0 <= dk)."""
    satir = []
    for f in sorted(glob.glob(KOK + "/data/muh/*.json")):
        gun = os.path.basename(f)[:-5]
        for key, k in json.load(open(f, encoding="utf-8")).items():
            so = k.get("sonuc")
            if not so:
                continue
            ank = [a for a in k.get("anlik", []) if a.get("durum") == "AÇIK" and a.get("dk", -1) >= 0]
            son = ank[-1]["g"] if ank else {}
            for no, ad_ in (k.get("atlar") or {}).items():
                g = so["ganyan"].get(str(no))
                if g is None:
                    continue
                satir.append({"tarih": gun, "hipodrom": k["slug"], "ulke": ulke_yer(k.get("yer")), "kosu": k["kosu"], "sira": so["sira"].get(str(no), 99),
                              "no": int(no), "at": ad(ad_), "ganyan": g, "g_anlik": son.get(str(no)), "kosmadi": False})
    return pd.DataFrame(satir)


def bootstrap(gun, v, B=4000, tohum=7):
    rng = np.random.default_rng(tohum)
    g = pd.Series(v).groupby(np.array(gun)).agg(["sum", "count"])
    s, c = g["sum"].values, g["count"].values
    out = []
    for _ in range(B):
        i = rng.integers(0, len(s), len(s))
        out.append(s[i].sum() / c[i].sum())
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def main():
    T = pd.concat([pd.read_csv(f) for f in glob.glob(KOK + "/data/yabanci/*.csv.gz")], ignore_index=True)
    T = T[T.ulke.isin(ULKE_TJK.values()) & (T.no > 0) & ~T.kosmadi.fillna(False).astype(bool)].copy()
    T["at"] = T["at"].map(ad)
    T["g_anlik"] = np.nan
    M = muh_tablo()
    if len(M):
        # aynı koşu iki kaynaktaysa muh (resmî sonuç + bahis anı ganyanı) önceliklidir
        anahtar = set(zip(M.tarih, M.hipodrom, M.kosu))
        T = pd.concat([T[[(t, h, k) not in anahtar for t, h, k in zip(T.tarih, T.hipodrom, T.kosu)]], M], ignore_index=True)
    T["gun_dt"] = pd.to_datetime(T.tarih)
    kayit = []
    for f in sorted(glob.glob(KOK + "/data/abd_oto/*.json")):
        gun = os.path.basename(f)[:-5]
        for _, k in json.load(open(f, encoding="utf-8")).items():
            if k["ulke"] in ULKE_TJK:
                kayit.append((gun, k))
    satir, eslesmeyen = [], 0
    for gun, k in kayit:
        d0 = pd.to_datetime(gun)
        adaylar = T[(T.gun_dt >= d0 - pd.Timedelta(days=1)) & (T.gun_dt <= d0 + pd.Timedelta(days=1)) & (T.ulke == ULKE_TJK[k["ulke"]])]
        mine = {ad(a["ad"]): a for a in k["atlar"]}
        en = None
        for (t, hp, ko), g in adaylar.groupby(["tarih", "hipodrom", "kosu"]):
            ort = len(set(g["at"]) & set(mine)) / max(1, len(set(g["at"])))
            if ort >= 0.6 and (en is None or ort > en[0]):
                en = (ort, g)
        if en is None:
            eslesmeyen += 1
            continue
        g = en[1]
        if not (g.sira == 1).sum() == 1 or g.ganyan.isna().any():
            eslesmeyen += 1
            continue
        g = g[g["at"].isin(mine)].copy()
        if len(g) < 3:
            eslesmeyen += 1
            continue
        inv = np.array([1 / mine[a]["oran"] for a in g["at"]])
        g["q"] = inv / inv.sum()
        g["ev"] = g.q * g.ganyan
        g["ev_anlik"] = g.q * g.g_anlik
        for _, r in g.iterrows():
            satir.append({"gun": gun, "ulke": k["ulke"], "pist": k["pist"], "kosu": k["kosu"], "at": r["at"], "q": r.q, "g": r.ganyan,
                          "ev": r.ev, "ev_anlik": r.ev_anlik, "g_anlik": r.g_anlik, "kazandi": int(r.sira == 1)})
    D = pd.DataFrame(satir)
    sonuc = {"uretim": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "kayitli_kosu": len(kayit), "eslesmeyen_kosu": eslesmeyen,
             "kural": f"q x TJK kapanış ganyanı > {ESIK}, 1 TL ganyan", "durdurma": "300 bahiste ROI GA alt sınırı < 1 ise ABD/İng/İrl testi kapanır (hipotez_defteri 18 Ekim)",
             "bahis": 0, "kosu": 0}
    if len(D):
        B = D[D.ev > ESIK].copy()
        B["net"] = np.where(B.kazandi == 1, B.g, 0.0)
        sonuc["kosu"] = int(D.groupby(["gun", "ulke", "pist", "kosu"]).ngroups)
        sonuc["bahis"] = int(len(B))
        if len(B):
            sonuc["isabet"] = int(B.kazandi.sum())
            sonuc["roi"] = round(float(B.net.sum() / len(B)), 3)
            if B.gun.nunique() >= 3:
                lo, hi = bootstrap(B.gun.values, B.net.values)
                sonuc["ga95"] = [round(lo, 3), round(hi, 3)]
            sonuc["ulke"] = {u: {"bahis": int(len(x)), "roi": round(float(x.net.sum() / len(x)), 3)} for u, x in B.groupby("ulke")}
        # BAHİS ANI varyantı: karar q x (başlamadan önceki son AÇIK muhtemel ganyan) > eşik; ödeme yine resmî kapanış ganyanı (pari-mutuel).
        if D.ev_anlik.notna().any():
            A = D[D.ev_anlik > ESIK].copy()
            A["net"] = np.where(A.kazandi == 1, A.g, 0.0)
            sonuc["bahis_ani"] = {"bahis": int(len(A)), "kosu": int(D[D.ev_anlik.notna()].groupby(["gun", "ulke", "pist", "kosu"]).ngroups)}
            if len(A):
                sonuc["bahis_ani"].update({"isabet": int(A.kazandi.sum()), "roi": round(float(A.net.sum() / len(A)), 3)})
                if A.gun.nunique() >= 3:
                    lo, hi = bootstrap(A.gun.values, A.net.values); sonuc["bahis_ani"]["ga95"] = [round(lo, 3), round(hi, 3)]
        sonuc["bahisler"] = [{"gun": r.gun, "pist": r.pist, "kosu": int(r.kosu), "at": r.at, "q": round(r.q, 3), "g": r.g, "kazandi": bool(r.kazandi)}
                             for r in B.sort_values(["gun", "pist", "kosu"]).tail(40).itertuples()]
    os.makedirs(KOK + "/docs/data", exist_ok=True)
    json.dump(sonuc, open(KOK + "/docs/data/abd_oto_sonuc.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print({k: v for k, v in sonuc.items() if k != "bahisler"})


if __name__ == "__main__":
    main()
