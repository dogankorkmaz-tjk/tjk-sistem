"""Yabancı koşu kaydı (15 Ekim 2026). Amaç: TJK'dan oynanan yabancı koşuların TJK havuzundaki son ganyanını biriktirmek,
sonra aynı koşunun kendi ülkesindeki piyasa oranıyla karşılaştırmak ("iki piyasa" testi). Model kullanılmaz, kural yok; yalnız kayıt.

Kaynak: agftablosu.com sitemap'inden yabancı sonuç sayfaları (robots.txt izin veriyor; az ve yavaş istek, ortak.getir).
Çıktı: data/yabanci/YYYY-MM.csv.gz (her at: tarih, hipodrom, ulke, kosu, sira, no, at, jokey, ganyan, kosmadi, url)
        data/yabanci/islenen.txt (işlenmiş sayfa adresleri) ve data/yabanci/pmu_robots.json (karşı piyasa kaynağının izin kontrolü)
Kullanım: python -m tjk.calistir yabanci   (gece job'unda da çalışır)"""
import os, re, json, datetime
import pandas as pd
from . import ortak as O

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI = os.path.join(KOK, "data", "yabanci")
EN_COK = int(os.environ.get("YABANCI_EN_COK", "60"))   # çalışma başına en çok sayfa (yavaş ve az istek)
AY = {a: i + 1 for i, a in enumerate(O.AYLAR)}
URL_RE = re.compile(r"https?://www\.agftablosu\.com/at-yarisi-sonuclar/at-yarisi-sonuclari-([a-z0-9-]+?)-(\d{1,2})-([a-z]+)-(\d{4})")
ULKELER = ["fransa", "birlesik-krallik", "irlanda", "abd", "avustralya", "guney-afrika", "arjantin", "sili", "kanada",
           "brezilya", "uruguay", "almanya", "italya", "isvec", "bae", "dubai", "japonya", "hong-kong", "yeni-zelanda",
           "singapur", "suudi-arabistan", "katar", "bahreyn", "macaristan", "cekya", "polonya", "belcika", "norvec", "danimarka"]


def _ayir(slug):
    for u in sorted(ULKELER, key=len, reverse=True):
        if slug.endswith("-" + u):
            return slug[: -len(u) - 1], u
    return slug, ""


def pmu_robots():
    """Karşı piyasa kaynağı (PMU açık API) robots.txt durumu - yalnız kayıt; hiçbir veri çekilmez."""
    import requests
    out = {"zaman": O.tr_simdi().strftime("%Y-%m-%d %H:%M"), "kaynaklar": {}}
    for u in ("https://online.turfinfo.api.pmu.fr/robots.txt", "https://www.pmu.fr/robots.txt"):
        try:
            r = requests.get(u, headers=O.HEADERS, timeout=30)
            out["kaynaklar"][u] = {"durum": r.status_code, "metin": r.text[:4000]}
        except Exception as e:
            out["kaynaklar"][u] = {"hata": str(e)[:300]}
    os.makedirs(VERI, exist_ok=True)
    json.dump(out, open(os.path.join(VERI, "pmu_robots.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("PMU robots:", {k: v.get("durum", v.get("hata")) for k, v in out["kaynaklar"].items()})


def topla():
    os.makedirs(VERI, exist_ok=True)
    yol_isl = os.path.join(VERI, "islenen.txt")
    islenen = set(open(yol_isl, encoding="utf-8").read().split()) if os.path.exists(yol_isl) else set()
    sm = O.getir(O.BASE + "/sitemap.xml") or ""
    adayl = []
    for m in URL_RE.finditer(sm):
        slug, g, ay, yil = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
        if ay not in AY or any(slug == h for h in O.TRH):
            continue
        try:
            t = datetime.date(yil, AY[ay], g)
        except ValueError:
            continue
        if t >= O.tr_simdi().date():           # bugünün sayfası henüz eksik olabilir
            continue
        adayl.append((t, slug, m.group(0)))
    adayl = sorted(set(adayl))
    yeni = [a for a in adayl if a[2] not in islenen]
    print(f"yabancı sonuç sayfası: sitemap {len(adayl)}, yeni {len(yeni)} (bu çalışmada en çok {EN_COK})")
    satirlar = []
    for t, slug, url in yeni[:EN_COK]:
        html = O.getir(url)
        if html is None:
            continue                          # ağ hatası: sonraki çalışmada yeniden denenir
        hip, ulke = _ayir(slug)
        rows = O.parse_sonuc(html, t.isoformat(), hip) if html else []
        for r in rows:
            r.update({"ulke": ulke, "url": url})
        satirlar += rows
        islenen.add(url)
        print(f"  {t} {slug}: {len(rows)} satır")
    if satirlar:
        d = pd.DataFrame(satirlar)[["tarih", "hipodrom", "ulke", "kosu", "sira", "no", "at", "jokey", "kilo", "ganyan", "kosmadi", "url"]]
        for ay, g in d.groupby(d.tarih.str[:7]):
            y = os.path.join(VERI, ay + ".csv.gz")
            eski = pd.read_csv(y) if os.path.exists(y) else pd.DataFrame()
            pd.concat([eski, g], ignore_index=True).drop_duplicates(["tarih", "hipodrom", "kosu", "no", "at"], keep="last").to_csv(y, index=False)
    open(yol_isl, "w", encoding="utf-8").write("\n".join(sorted(islenen)) + "\n")
    return len(satirlar)


def ozet():
    """Kalibrasyon özeti: TJK yabancı havuzunda 1/ganyan toplamı (kesinti göstergesi) ve oran dilimine göre kazanma sıklığı."""
    import glob
    fs = sorted(glob.glob(os.path.join(VERI, "*.csv.gz")))
    if not fs:
        return None
    d = pd.concat([pd.read_csv(f) for f in fs])
    d = d[d.ganyan.notna() & (d.ganyan > 0) & ~d.kosmadi.fillna(False).astype(bool) & (d.no > 0)]   # no=0: kaynağı bozuk sayfa (ör. Fransa)
    k = ["tarih", "hipodrom", "kosu"]
    d["p"] = 1 / d.ganyan
    g = d.groupby(k).agg(top=("p", "sum"), n=("p", "size"), kaz=("sira", lambda s: (s == 1).sum()))
    tam = g[(g.kaz == 1) & (g.n >= 3) & g.top.between(1.2, 1.7)].index      # eksik/ekürlü görünen koşular dışarıda
    d = d.set_index(k).loc[tam].reset_index()
    d["pn"] = d.p / d.groupby(k).p.transform("sum")
    out = {"zaman": O.tr_simdi().strftime("%Y-%m-%d %H:%M"), "kosu": int(len(tam)), "ulke": d.groupby("ulke").apply(lambda x: x[k].drop_duplicates().shape[0]).to_dict(),
           "geri_odeme_medyan": round(float(1 / g.loc[tam].top.median()), 3) if len(tam) else None}
    d["dilim"] = pd.cut(d.ganyan, [1, 3, 6, 12, 25, 1000])
    out["dilim"] = [{"dilim": str(i), "at": int(len(x)), "kazanma": round(float((x.sira == 1).mean()), 4),
                     "oranin_dedigi": round(float(x.pn.mean()), 4),
                     "ganyan_roi": round(float(((x.sira == 1) * x.ganyan).mean()), 3)} for i, x in d.groupby("dilim", observed=True)]
    json.dump(out, open(os.path.join(VERI, "ozet.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False)[:1500])
    return out


def calistir():
    pmu_robots()
    topla()
    ozet()


def ham_ornek():
    """Ayrıştırıcı geliştirmek için birkaç ham sayfayı kaydeder (data/yabanci_ham/)."""
    yol = os.path.join(KOK, "data", "yabanci_ham"); os.makedirs(yol, exist_ok=True)
    sm = O.getir(O.BASE + "/sitemap.xml") or ""
    secim = {}
    for m in URL_RE.finditer(sm):
        hip, ulke = _ayir(m.group(1))
        if ulke in ("fransa", "birlesik-krallik", "abd") and ulke not in secim:
            secim[ulke] = m.group(0)
    for ulke, url in secim.items():
        h = O.getir(url) or ""
        open(os.path.join(yol, ulke + ".html"), "w", encoding="utf-8").write(h)
        print(ulke, url, len(h))


ABD_PIST = ["belmont-park", "horseshoe-indianapolis", "santa-anita-park", "keeneland", "gulfstream-park", "finger-lakes",
            "philadelphia", "laurel-park", "delaware-park", "aqueduct", "saratoga", "churchill-downs", "del-mar",
            "woodbine", "monmouth-park", "oaklawn-park", "fair-grounds", "tampa-bay-downs", "parx-racing", "golden-gate-fields"]


def abd_gecmis(bas, son):
    """ABD (ve Kanada'da Woodbine) geçmiş sonuç sayfaları: pist x gün adresi denenir; 404 hızlı geçilir. Az ve yavaş istek (ortak.getir 2 sn)."""
    os.makedirs(VERI, exist_ok=True)
    yol_isl = os.path.join(VERI, "islenen.txt")
    islenen = set(open(yol_isl, encoding="utf-8").read().split()) if os.path.exists(yol_isl) else set()
    t, satir, bulunan = bas, [], 0
    while t <= son:
        for pist in ABD_PIST:
            ulke = "kanada" if pist == "woodbine" else "abd"
            url = f"{O.BASE}/at-yarisi-sonuclar/at-yarisi-sonuclari-{pist}-{ulke}-{t.day}-{O.AYLAR[t.month-1]}-{t.year}"
            if url in islenen:
                continue
            html = O.getir(url)
            if html is None:
                continue
            islenen.add(url)
            if not html:
                continue
            rows = O.parse_sonuc(html, t.isoformat(), pist)
            for r in rows:
                r.update({"ulke": ulke, "url": url})
            satir += rows; bulunan += 1
            if rows:
                _program(t, pist, ulke)
        if t.day == 1 or t == son:
            print(t, "sayfa", bulunan, "satır", len(satir), flush=True)
            _yaz(satir); satir = []
            open(yol_isl, "w", encoding="utf-8").write("\n".join(sorted(islenen)) + "\n")
        t += datetime.timedelta(days=1)
    _yaz(satir)
    open(yol_isl, "w", encoding="utf-8").write("\n".join(sorted(islenen)) + "\n")


def _yaz(satirlar):
    if not satirlar:
        return
    d = pd.DataFrame(satirlar)[["tarih", "hipodrom", "ulke", "kosu", "sira", "no", "at", "jokey", "kilo", "ganyan", "kosmadi", "url"]]
    for ay, g in d.groupby(d.tarih.str[:7]):
        y = os.path.join(VERI, ay + ".csv.gz")
        eski = pd.read_csv(y) if os.path.exists(y) else pd.DataFrame()
        pd.concat([eski, g], ignore_index=True).drop_duplicates(["tarih", "hipodrom", "kosu", "no", "at"], keep="last").to_csv(y, index=False)


def _program(t, pist, ulke):
    """Program sayfası (antrenör, sahip, yaş, start, son 6, KGS) -> data/yabanci_program/YYYY-MM.csv.gz. Mesafe/pist sayfada yok."""
    yol = os.path.join(KOK, "data", "yabanci_program"); os.makedirs(yol, exist_ok=True)
    y = os.path.join(yol, t.strftime("%Y-%m") + ".csv.gz")
    eski = pd.read_csv(y) if os.path.exists(y) else pd.DataFrame()
    if len(eski) and ((eski.tarih == t.isoformat()) & (eski.hipodrom == pist)).any():
        return
    html = O.getir(O.prog_url(t, f"{pist}-{ulke}"))
    rows = O.parse_prog(html or "", t.isoformat(), pist)
    if rows:
        pd.concat([eski, pd.DataFrame(rows)], ignore_index=True).to_csv(y, index=False)


def abd_program(bas, son):
    """Sonucu olan ABD/Kanada günleri için eksik program sayfalarını çeker (geçmiş çekimin ilk parçası programsız yapıldı)."""
    import glob
    d = pd.concat([pd.read_csv(f, usecols=["tarih", "hipodrom", "ulke"]) for f in glob.glob(os.path.join(VERI, "*.csv.gz"))]).drop_duplicates()
    d = d[d.ulke.isin(["abd", "kanada"]) & (d.tarih >= bas.isoformat()) & (d.tarih <= son.isoformat())]
    for i, r in enumerate(d.sort_values("tarih").itertuples()):
        _program(datetime.date.fromisoformat(r.tarih), r.hipodrom, r.ulke)
        if i % 25 == 0:
            print(r.tarih, i, "/", len(d), flush=True)


def sl_probe(tarih="2026-10-12"):
    """Sporting Life (robots.txt izin veriyor) sonuç sayfası yapısını keşif: günün sayfası + bir ABD koşusu ham kaydı."""
    import requests, time
    yol = os.path.join(KOK, "data", "yabanci_ham"); os.makedirs(yol, exist_ok=True)
    H = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; gunde birkac yavas istek)"}
    gun = requests.get(f"https://www.sportinglife.com/racing/results/{tarih}", headers=H, timeout=30).text
    open(os.path.join(yol, "sl_gun.html"), "w", encoding="utf-8").write(gun)
    linkler = sorted(set(re.findall(r"/racing/results/" + tarih + r"/[a-z0-9-]+/\d+/[a-z0-9-]+", gun)))
    print("koşu linki", len(linkler)); print("\n".join(linkler[:80]))
    abd = [l for l in linkler if any(p in l for p in ("santa-anita", "finger-lakes", "horseshoe", "presque", "mountaineer"))]
    if abd:
        time.sleep(3)
        open(os.path.join(yol, "sl_abd.html"), "w", encoding="utf-8").write(requests.get("https://www.sportinglife.com" + abd[0], headers=H, timeout=30).text)
        print("ABD örnek:", abd[0])
