"""Kullanım:  python -m tjk.calistir sabah | canli | gece | hepsi
sabah: bugünün programı + model form puanları + AGF  -> docs/data/bugun.json
canli: AGF'yi yeniler, biten koşuların sonucunu ve kapanış ganyanlarını ekler
gece : dünün (ve eksik günlerin) sonuçlarını geçmişe ekler, canlı test skorunu hesaplar -> docs/data/skor.json"""
import os, sys, json, glob, datetime
import numpy as np, pandas as pd
from . import ortak as O
from .ozellik import hazirla, model_olasilik

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI = os.path.join(KOK, "data")
SITE = os.path.join(KOK, "docs", "data")
os.makedirs(os.path.join(SITE, "gun"), exist_ok=True)
# geçmiş veriler aylık parçalar hâlinde: data/<tür>/YYYY-MM.csv.gz (her gece yalnızca son ay dosyası değişir)
TURLER = ("sonuclar", "temiz", "program")


def yukle_model():
    return json.load(open(os.path.join(VERI, "model_v1.json"), encoding="utf-8"))


def oku(a):
    parcalar = sorted(glob.glob(os.path.join(VERI, a, "*.csv.gz")))
    return pd.concat([pd.read_csv(p, low_memory=False) for p in parcalar], ignore_index=True)


def ekle(a, yeni, sutunlar=None):
    """Yeni satırları ilgili ay dosyalarına ekler (aynı anahtar varsa yenisi kalır)."""
    k = O.K + ["no"]
    os.makedirs(os.path.join(VERI, a), exist_ok=True)
    for ay, g in yeni.groupby(yeni.tarih.str[:7]):
        yol = os.path.join(VERI, a, f"{ay}.csv.gz")
        if os.path.exists(yol):
            eski = pd.read_csv(yol, low_memory=False)
            g = g.reindex(columns=eski.columns)
            g = pd.concat([eski, g], ignore_index=True).drop_duplicates(k, keep="last")
        elif sutunlar is not None:
            g = g.reindex(columns=sutunlar)
        g.sort_values(k).to_csv(yol, index=False)


def yaz_json(yol, obj):
    tmp = yol + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, yol)


def gun_yolu(t):
    return os.path.join(SITE, "gun", f"{t.isoformat()}.json")


def bos_sayi(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else x


# ------------------------------------------------------------------ sabah
def sabah(t):
    tarih = t.isoformat()
    ana = O.getir(O.BASE) or ""
    hips = O.gunun_hipodromlari(t, ana)
    print("ana sayfadan bugünün hipodromları:", hips)
    programlar, satirlar = {}, []
    adaylar = hips or O.TRH
    for h in adaylar:
        html = O.getir(O.prog_url(t, h))
        if not html:
            continue
        p = O.parse_prog(html, tarih, h)
        if not p:
            continue
        programlar[h] = {"saat": O.kosu_saatleri(html), "bilgi": O.kosu_bilgileri(html)}
        satirlar += p
    if not satirlar:
        print("bugün Türkiye'de yarış yok ya da program okunamadı")
        obj = {"tarih": tarih, "guncelleme": O.tr_simdi().strftime("%H:%M"), "hipodromlar": []}
        yaz_json(gun_yolu(t), obj); yaz_json(os.path.join(SITE, "bugun.json"), obj)
        return obj
    pr = pd.DataFrame(satirlar).dropna(subset=["no"])
    pr["no"] = pr.no.astype(int)
    yeni = pr.rename(columns={"p_at": "at", "p_jokey": "jokey", "p_apranti": "apranti", "p_kilo": "kilo"})
    yeni["hnd"] = yeni.hk; yeni["kosmadi"] = False; yeni["ganyan"] = 10.0
    M = yukle_model()
    temiz, prog = oku("temiz"), oku("program")
    temiz = temiz[temiz.tarih < tarih]
    d = hazirla(temiz, prog, M, yeni)
    bz = d[d.yeni].set_index(["hipodrom", "kosu", "no"]).z.to_dict()
    obj = {"tarih": tarih, "model": M.get("surum", "v1"), "w0": float(M["w"][0]),
           "guncelleme": O.tr_simdi().strftime("%H:%M"), "hipodromlar": []}
    for h in [x for x in O.TRH if x in programlar]:
        g = pr[pr.hipodrom == h]
        kos = []
        for kn, kg in g.groupby("kosu"):
            atlar = [{"no": int(r.no), "at": r.p_at, "jokey": r.p_jokey, "apr": bool(r.p_apranti),
                      "st": bos_sayi(float(r.st)) if pd.notna(r.st) else None,
                      "z": round(float(bz.get((h, kn, int(r.no)), 0.0)), 4)} for r in kg.itertuples()]
            kos.append({"kosu": int(kn), "saat": programlar[h]["saat"].get(int(kn)),
                        "bilgi": programlar[h]["bilgi"].get(int(kn)), "atlar": atlar})
        obj["hipodromlar"].append({"id": h, "ad": O.AD[h], "kosular": kos})
    agf_ekle(obj)
    if os.path.exists(gun_yolu(t)):                       # gün içinde yeniden çalışırsa eldeki sonuçlar kalsın
        eski = json.load(open(gun_yolu(t), encoding="utf-8"))
        es = {(h["id"], k["kosu"]): k.get("sonuc") for h in eski["hipodromlar"] for k in h["kosular"]}
        for h in obj["hipodromlar"]:
            for k in h["kosular"]:
                if es.get((h["id"], k["kosu"])):
                    k["sonuc"] = es[(h["id"], k["kosu"])]
    yaz_json(gun_yolu(t), obj)
    yaz_json(os.path.join(SITE, "bugun.json"), obj)
    print("yazıldı:", {h["id"]: len(h["kosular"]) for h in obj["hipodromlar"]})
    return obj


def agf_ekle(obj):
    html = O.getir(O.BASE + "/agf-tablosu")
    if not html:
        return
    try:
        agf = O.parse_agf(html)
    except Exception as e:                       # AGF isteğe bağlı; hata tüm işi durdurmasın
        print("AGF okunamadı:", e); return
    for h in obj["hipodromlar"]:
        if h["id"] not in agf:
            continue
        atlar = {k["kosu"]: {a["no"] for a in k["atlar"]} for k in h["kosular"]}
        harita = O.agf_kosulara(agf[h["id"]], atlar)
        for k in h["kosular"]:
            d = harita.get(k["kosu"])
            if not d:
                continue
            for a in k["atlar"]:
                a["agf"] = d.get(a["no"])
            k["agf_saat"] = O.tr_simdi().strftime("%H:%M")
    print("AGF eklendi:", {h: len(v) for h, v in agf.items()})


# ------------------------------------------------------------------ canlı (sonuçlar)
def sonuclari_isle(obj, t, w0=None):
    """Biten koşulara sonuç sırası, kapanış ganyanı, piyasa ve model olasılığı ekler."""
    w0 = w0 if w0 is not None else obj.get("w0", 1.0)
    simdi = O.tr_simdi()
    yeni_sonuc = 0
    for h in obj["hipodromlar"]:
        bekleyen = [k for k in h["kosular"] if not k.get("sonuc")]
        if not bekleyen:
            continue
        if t == simdi.date():
            ilk = min((k.get("saat") or "00:00") for k in bekleyen)
            if ilk > simdi.strftime("%H:%M"):
                continue                         # henüz hiçbir koşu başlamadı
        html = None
        for u in O.sonuc_urls(t, h["id"]):
            html = O.getir(u)
            if html:
                break
        if not html:
            continue
        s = pd.DataFrame(O.parse_sonuc(html, t.isoformat(), h["id"]))
        if s.empty:
            continue
        for k in bekleyen:
            r = s[(s.kosu == k["kosu"]) & s.ganyan.notna() & (s.ganyan > 0)].copy()
            if r.empty or r.sira.notna().sum() == 0:
                continue
            r = O.duzelt(r)
            z = {a["no"]: a["z"] for a in k["atlar"]}
            r["z"] = r.no.map(z).fillna(0.0)
            r["p_model"] = model_olasilik(r.p_piyasa.values, r.z.values, w0)
            k["sonuc"] = {str(int(x.no)): {"sira": None if pd.isna(x.sira) else int(x.sira),
                                           "g": float(x.ganyan), "pp": round(float(x.p_piyasa), 5),
                                           "pm": round(float(x.p_model), 5)} for x in r.itertuples()}
            yeni_sonuc += 1
    obj["guncelleme"] = simdi.strftime("%H:%M")
    return yeni_sonuc


def canli(t):
    yol = gun_yolu(t)
    obj = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else sabah(t)
    if not obj["hipodromlar"]:
        return
    son = max((k.get("saat") or "23:59") for h in obj["hipodromlar"] for k in h["kosular"])
    if O.tr_simdi().strftime("%H:%M") < son:
        agf_ekle(obj)
    n = sonuclari_isle(obj, t)
    print("yeni sonuçlanan koşu:", n)
    yaz_json(yol, obj); yaz_json(os.path.join(SITE, "bugun.json"), obj)


# ------------------------------------------------------------------ gece (geçmişe ekle + skor)
def gece(bugun):
    sn = oku("sonuclar")
    son = datetime.date.fromisoformat(sn.tarih.max())
    gunler = [son + datetime.timedelta(days=i) for i in range(1, (bugun - son).days)]
    print("son kayıtlı gün:", son, "| işlenecek:", [g.isoformat() for g in gunler])
    yeni_s, yeni_p = [], []
    for g in gunler:
        for h in O.TRH:
            html = None
            for u in O.sonuc_urls(g, h):
                html = O.getir(u)
                if html:
                    break
            s = O.parse_sonuc(html, g.isoformat(), h) if html else []
            if not s:
                continue
            yeni_s += s
            yeni_p += O.parse_prog(O.getir(O.prog_url(g, h)) or "", g.isoformat(), h)
            print(" ", g, h, len(s), "satır")
        # o günün sitedeki kaydına eksik sonuçları ekle
        yol = gun_yolu(g)
        if os.path.exists(yol):
            obj = json.load(open(yol, encoding="utf-8"))
            if sonuclari_isle(obj, g):
                yaz_json(yol, obj)
    if yeni_s:
        ns, npg = pd.DataFrame(yeni_s), pd.DataFrame(yeni_p)
        ekle("sonuclar", ns, sn.columns)
        te = oku("temiz")
        ekle("temiz", O.temiz_yap(ns), te.columns)
        if len(npg):
            ekle("program", npg, oku("program").columns)
        print("EKLENDİ: sonuç", len(ns), "program", len(npg))
    skor()


# ------------------------------------------------------------------ geçmiş günleri siteye aktar
def gecmis(bas, bit):
    """data/ CSV'lerinden, bas..bit arası (dahil) her gün için docs/data/gun/<gün>.json üretir."""
    M = yukle_model()
    d = hazirla(oku("temiz"), oku("program"), M)
    d = d[d.temiz & (d.tarih >= bas.isoformat()) & (d.tarih <= bit.isoformat())]
    w0 = float(M["w"][0])
    n = 0
    for tarih, gd in d.groupby("tarih"):
        obj = {"tarih": tarih, "model": M.get("surum", "v1"), "w0": w0, "gecmis": True,
               "guncelleme": "arşiv", "hipodromlar": []}
        for h in [x for x in O.TRH if x in set(gd.hipodrom)]:
            kos = []
            for kn, kg in gd[gd.hipodrom == h].groupby("kosu"):
                kg = kg[~kg.kosmadi.astype(bool)]
                if kg.empty:
                    continue
                atlar = [{"no": int(r["no"]), "at": r["at"], "jokey": r["jokey"],
                          "apr": bool(r["apranti"]), "st": bos_sayi(float(r["st"])) if pd.notna(r["st"]) else None,
                          "z": round(float(r["z"]), 4)} for _, r in kg.iterrows()]
                sonuc = None
                k2 = kg[kg.ganyan.notna() & (kg.ganyan > 0)].copy()
                if len(k2) and k2.sira.notna().sum():
                    k2["p_model"] = model_olasilik(k2.p_piyasa.values, k2.z.values, w0)
                    sonuc = {str(int(r["no"])): {"sira": None if pd.isna(r["sira"]) else int(r["sira"]),
                             "g": float(r["ganyan"]), "pp": round(float(r["p_piyasa"]), 5),
                             "pm": round(float(r["p_model"]), 5)} for _, r in k2.iterrows()}
                kos.append({"kosu": int(kn), "saat": None, "bilgi": None, "atlar": atlar, "sonuc": sonuc})
            obj["hipodromlar"].append({"id": h, "ad": O.AD[h], "kosular": kos})
        yaz_json(gun_yolu(datetime.date.fromisoformat(tarih)), obj); n += 1
    print("geçmiş gün yazıldı:", n)


def skor():
    M = yukle_model()
    freeze = M.get("freeze", "2026-10-08")
    d = hazirla(oku("temiz"), oku("program"), M)
    c = d[d.tarih >= freeze].copy()
    out = {"freeze": freeze, "guncelleme": O.tr_simdi().strftime("%Y-%m-%d %H:%M")}
    if c.empty:
        out["kosu"] = 0
        yaz_json(os.path.join(SITE, "skor.json"), out); print("canlı dönemde koşu yok"); return
    c["rid"] = c.groupby(O.K).ngroup()
    s = M["w"][0] * c.lp + c.z
    c["e"] = np.exp(s - s.groupby(c.rid).transform("max"))
    c["p_model"] = c.e / c.groupby("rid").e.transform("sum")
    c["ev"] = c.p_model * c.ganyan
    c["getiri"] = c.kazandi * c.ganyan - 1
    kz = c[c.kazandi == 1]
    fark = np.log(kz.p_model.values) - np.log(kz.p_piyasa.values)
    fav = c.loc[c.groupby("rid").p_piyasa.idxmax()]; top = c.loc[c.groupby("rid").p_model.idxmax()]
    out.update({"kosu": int(c.rid.nunique()), "gun": int(c.tarih.nunique()),
                "ll_piyasa": float(-np.log(kz.p_piyasa).mean()), "ll_model": float(-np.log(kz.p_model).mean()),
                "fark": float(fark.mean()), "fark_se": float(fark.std(ddof=1) / np.sqrt(len(fark))) if len(fark) > 1 else None,
                "fav_isabet": float(fav.kazandi.mean()), "model_isabet": float(top.kazandi.mean())})
    ev = []
    for e in (0.9, 1.0, 1.1):
        b = c[c.ev > e]
        if len(b):
            ev.append({"esik": e, "n": int(len(b)), "roi": float(b.getiri.mean()),
                       "se": float(b.getiri.std(ddof=1) / np.sqrt(len(b))) if len(b) > 1 else None})
    out["ev"] = ev

    def kural(ad, x, beklenti):
        if not len(x):
            return {"ad": ad, "n": 0, "beklenti": beklenti}
        v = (x.p_piyasa * (1 - x.p_piyasa)).sum()
        return {"ad": ad, "n": int(len(x)), "gercek": int(x.kazandi.sum()), "beklenen": float(x.p_piyasa.sum()),
                "z": float((x.kazandi.sum() - x.p_piyasa.sum()) / np.sqrt(v)) if v > 0 else None,
                "roi": float(x.getiri.mean()), "beklenti": beklenti}
    out["kurallar"] = [kural("K1: iç start (1-2) favori, ganyan ≤ 3,5", c[(c.ganyan <= 3.5) & (c.st <= 2)], "oran > 1"),
                       kural("K2: apranti jokeyli at", c[c.apranti.astype(bool)], "oran < 1")]
    g = pd.DataFrame({"tarih": kz.tarih.values, "fark": fark}).groupby("tarih").fark.agg(["sum", "size"])
    g["kum"] = g["sum"].cumsum() / g["size"].cumsum()
    out["seri"] = [{"t": t, "n": int(r["size"]), "kum": float(r.kum)} for t, r in g.iterrows()]
    hp = []
    for h, x in kz.assign(f=fark).groupby("hipodrom"):
        hp.append({"h": h, "ad": O.AD.get(h, h), "n": int(len(x)), "fark": float(x.f.mean())})
    out["hipodrom"] = sorted(hp, key=lambda r: -r["n"])
    yaz_json(os.path.join(SITE, "skor.json"), out)
    print("skor:", {k: out[k] for k in ("kosu", "fark", "fark_se")})


def dene(t):
    """Veri gerektirmeyen bağlantı denemesi: siteye erişim ve ayrıştırıcılar."""
    ana = O.getir(O.BASE)
    print("ana sayfa:", "YOK" if ana is None else f"{len(ana)} karakter")
    hips = O.gunun_hipodromlari(t, ana or "")
    print("bugünün hipodromları:", hips)
    rapor = {"zaman": O.tr_simdi().strftime("%Y-%m-%d %H:%M"), "ana_sayfa": None if ana is None else len(ana),
             "hipodromlar": hips, "detay": {}}
    for h in hips[:2]:
        html = O.getir(O.prog_url(t, h)) or ""
        p = O.parse_prog(html, t.isoformat(), h)
        print(f"  {h} program: {len(p)} at | saatler: {O.kosu_saatleri(html)} | bilgi örnek: {list(O.kosu_bilgileri(html).items())[:1]}")
        rapor["detay"][h] = {"program_html": len(html), "program_at": len(p), "saatler": O.kosu_saatleri(html),
                             "bilgi": list(O.kosu_bilgileri(html).items())[:2]}
        dun = t - datetime.timedelta(days=1)
        for u in O.sonuc_urls(t, h):
            s = O.getir(u)
            if s:
                n = len(O.parse_sonuc(s, t.isoformat(), h))
                print(f"  {h} bugünkü sonuç satırı: {n}"); rapor["detay"][h]["sonuc_satir"] = n; break
    agf = O.parse_agf(O.getir(O.BASE + "/agf-tablosu") or "")
    print("AGF:", {h: {a: len(v) for a, v in d.items()} for h, d in agf.items()})
    rapor["agf"] = {h: {a: {ay: len(x) for ay, x in v.items()} for a, v in d.items()} for h, d in agf.items()}
    yaz_json(os.path.join(SITE, "dene.json"), rapor)


def main():
    mod = sys.argv[1] if len(sys.argv) > 1 else "canli"
    simdi = O.tr_simdi(); bugun = simdi.date()
    if mod == "sabah":
        sabah(bugun)
    elif mod == "canli":
        canli(bugun)
    elif mod == "gece":
        gece(bugun)
    elif mod == "gecmis":
        bas = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else bugun - datetime.timedelta(days=45)
        gecmis(bas, bugun - datetime.timedelta(days=1))
    elif mod == "robots":
        import requests
        r = requests.get("https://www.tjk.org/robots.txt", timeout=30, headers={"User-Agent": "tjk-sistem/1.0 (kisisel arastirma)"})
        yaz_json(os.path.join(SITE, "robots_tjk.json"), {"durum": r.status_code, "metin": r.text[:6000]})
        print(r.status_code); print(r.text[:3000])
    elif mod == "skor":
        skor()
    elif mod == "dene":
        dene(bugun)
    elif mod == "hepsi":
        gece(bugun); sabah(bugun); canli(bugun)
    else:
        raise SystemExit("bilinmeyen mod: " + mod)


if __name__ == "__main__":
    main()
