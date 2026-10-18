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
            r = O._CR.get(u, impersonate="chrome", timeout=30) if O._CR else requests.get(u, headers=O.HEADERS, timeout=30)
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


def sl_kosu_probe(*yollar):
    """Sporting Life tek koşu sayfası ham kaydı (keşif)."""
    import requests, time
    yol = os.path.join(KOK, "data", "yabanci_ham"); os.makedirs(yol, exist_ok=True)
    H = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; gunde birkac yavas istek)"}
    for i, y in enumerate(yollar):
        h = requests.get("https://www.sportinglife.com/racing/results/" + y, headers=H, timeout=30)
        open(os.path.join(yol, f"sl_kosu_{i}.html"), "w", encoding="utf-8").write(h.text)
        print(y, h.status_code, len(h.text)); time.sleep(3)


# ---------- Sporting Life: yerel piyasa oranları (robots.txt izin veriyor; az ve yavaş istek) ----------
SL = "https://www.sportinglife.com/racing/results/"
SL_ULKE = {"United States": "abd", "England": "birlesik-krallik", "Scotland": "birlesik-krallik", "Wales": "birlesik-krallik",
           "Eire": "irlanda", "Canada": "kanada", "France": "fransa", "South Africa": "guney-afrika", "Australia": "avustralya"}


def _sl_json(url, bekle=3):
    import requests, time
    H = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; gunde birkac yavas istek)"}
    for den in range(3):
        try:
            r = requests.get(url, headers=H, timeout=30); time.sleep(bekle)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
            return json.loads(m.group(1))["props"]["pageProps"] if m else None
        except Exception as e:
            print("  SL hata:", url, e); time.sleep(10 * (den + 1))
    return None


def _slug(s):
    s = str(s).lower().translate(O.TR)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _eslestir(sl_ad, adaylar):
    """SL pist adı -> agftablosu hipodrom slug'ı (ortak kelime)."""
    a = set(_slug(sl_ad).split("-")) - {"park", "downs", "racecourse", "race", "course", "the", "at", "big"}
    en, puan = None, 0
    for h in adaylar:
        b = set(h.split("-")) - {"park", "downs", "racecourse", "race", "course", "the", "at", "big"}
        p = len(a & b)
        if p > puan:
            en, puan = h, p
    return en


def _kesir(o):
    try:
        if o in (None, "", "-"):
            return None
        if str(o).upper() in ("EVS", "EVENS"):
            return 2.0
        a, b = str(o).split("/"); return float(a) / float(b) + 1
    except Exception:
        return None


def sl_topla(bas, son, ulkeler=("abd", "birlesik-krallik", "irlanda", "kanada")):
    """TJK'da oynanan (data/yabanci'de kaydı olan) yabancı pistlerin yerel son oranlarını ve form bilgisini kaydeder."""
    import glob
    tj = pd.concat([pd.read_csv(f, usecols=["tarih", "hipodrom", "ulke"]) for f in glob.glob(os.path.join(VERI, "*.csv.gz"))]).drop_duplicates()
    cik = os.path.join(KOK, "data", "yabanci_sl"); os.makedirs(cik, exist_ok=True)
    t = bas
    while t <= son:
        gun = t.isoformat(); tjg = tj[(tj.tarih == gun) & tj.ulke.isin(ulkeler)]
        y = os.path.join(cik, t.strftime("%Y-%m") + ".csv.gz")
        eski = pd.read_csv(y) if os.path.exists(y) else pd.DataFrame()
        if len(tjg) == 0 or (len(eski) and (eski.tarih == gun).any()):
            t += datetime.timedelta(days=1); continue
        pp = _sl_json(SL + gun)
        rows = []
        for m in (pp or {}).get("meetings", []):
            ms = m["meeting_summary"]; ulke = SL_ULKE.get(ms["course"]["country"]["long_name"])
            if ulke not in ulkeler:
                continue
            hip = _eslestir(ms["course"]["name"], tjg[tjg.ulke == ulke].hipodrom.tolist() if ulke != "kanada" else tjg.hipodrom.tolist())
            if not hip:
                continue
            races = sorted(m["races"], key=lambda r: r.get("time") or "")
            for sira, rc in enumerate(races, 1):
                rid = rc["race_summary_reference"]["id"]
                rp = _sl_json(f"{SL}{gun}/{_slug(ms['course']['name'])}/{rid}/{_slug(rc.get('name') or 'race')}")
                if not rp or not rp.get("race"):
                    continue
                rs = rp["race"].get("race_summary", {})
                mno = re.match(r"Race\s+(\d+)", rc.get("name") or "")
                for x in rp["race"].get("rides", []):
                    b = x.get("betting") or {}; hz = x.get("horse") or {}
                    rows.append({"tarih": gun, "hipodrom": hip, "ulke": ulke, "sl_pist": ms["course"]["name"], "sl_id": rid,
                                 "kosu_sira": sira, "kosu_no": int(mno.group(1)) if mno else None, "saat": rc.get("time"),
                                 "mesafe": rc.get("distance"), "zemin": (rc.get("course_surface") or {}).get("surface"),
                                 "pist_durum": rc.get("going") or rs.get("going"), "no": x.get("cloth_number"),
                                 "at": (hz.get("name") or "").upper(), "sira": x.get("finish_position"),
                                 "oran_son": _kesir(b.get("current_odds")), "oran_gecmis": "|".join(b.get("historical_odds") or []),
                                 "jokey": (x.get("jockey") or {}).get("name"), "antrenor": (x.get("trainer") or {}).get("name"),
                                 "yas": hz.get("age"), "son_kosu_gun": hz.get("last_ran_days"),
                                 "onceki": json.dumps([[p.get("date"), p.get("course_name"), p.get("distance"), p.get("going"), p.get("position"), p.get("runner_count"), p.get("odds"), p.get("bha")] for p in (hz.get("previous_results") or []) if p.get("race_id") != rid])})
        if rows:
            pd.concat([eski, pd.DataFrame(rows)], ignore_index=True).to_csv(y, index=False)
        print(gun, "SL satır", len(rows), flush=True)
        t += datetime.timedelta(days=1)


def abd_canli(gunler=None, pencere_dk=90, ulkeler=("abd", "guney-afrika", "birlesik-krallik", "irlanda", "fransa")):
    """ABD + Güney Afrika koşuları: yalnız başlamasına en çok pencere_dk kala olanların anlık yerel oranları -> docs/data/abd.json (hızlı, paralel)."""
    from concurrent.futures import ThreadPoolExecutor
    from zoneinfo import ZoneInfo
    simdi = datetime.datetime.now(ZoneInfo("UTC"))           # Sporting Life JSON saatleri UTC (15 Ekim: Brighton 12:32 = TJK 15:32 TR)
    gunler = gunler or [simdi.date(), simdi.date() + datetime.timedelta(days=1)]
    RC = "https://www.sportinglife.com/racing/racecards/"
    ham = os.path.join(KOK, "data", "yabanci_ham"); os.makedirs(ham, exist_ok=True)
    isler = []; toplanti = []
    for t in gunler:
        gun = t.isoformat(); pp = _sl_json(RC + gun, 0.5)
        for m in (pp or {}).get("meetings", []):
            ms = m["meeting_summary"]
            try:
                zz = sorted(r.get("time") or "" for r in m.get("races", []))
                toplanti.append({"tarih": gun, "pist": ms["course"]["name"], "ulke": ms["course"]["country"]["long_name"], "kosu": len(zz), "ilk": zz[0] if zz else None, "son": zz[-1] if zz else None})
            except Exception:
                pass
            if SL_ULKE.get(ms["course"]["country"]["long_name"]) not in ulkeler:
                continue
            for sira, rc in enumerate(sorted(m["races"], key=lambda r: r.get("time") or ""), 1):
                try:
                    bas = datetime.datetime.combine(t, datetime.time.fromisoformat(rc["time"]), ZoneInfo("UTC"))
                except Exception:
                    continue
                dk = (bas - simdi).total_seconds() / 60
                if -5 <= dk <= pencere_dk:
                    isler.append((gun, ms, rc, sira, dk, bas.astimezone(ZoneInfo("Europe/Istanbul")).strftime("%H:%M")))

    def al(x):
        gun, ms, rc, sira, dk, saat_tr = x; rid = rc["race_summary_reference"]["id"]
        rp = _sl_json(f"{RC}{gun}/{_slug(ms['course']['name'])}/racecard/{rid}/{_slug(rc.get('name') or 'race')}", 0.7)
        if not rp or not rp.get("race"):
            return None
        mno = re.match(r"Race\s+(\d+)", rc.get("name") or "")
        atlar = []
        for r in rp["race"].get("rides", []):
            b = r.get("betting") or {}; hz = r.get("horse") or {}
            atlar.append({"no": r.get("cloth_number"), "ad": (hz.get("name") or "").upper(), "oran": _kesir(b.get("current_odds")), "gecmis": b.get("historical_odds") or []})
        return {"tarih": gun, "ulke": SL_ULKE.get(ms["course"]["country"]["long_name"]), "pist": ms["course"]["name"], "kosu": int(mno.group(1)) if mno else sira, "saat": saat_tr, "saat_utc": rc.get("time"), "dk": round(dk),
                "mesafe": rc.get("distance"), "zemin": (rc.get("course_surface") or {}).get("surface"), "atlar": atlar}
    with ThreadPoolExecutor(4) as ex:
        kos = [k for k in ex.map(al, isler) if k]
    kos.sort(key=lambda k: k["dk"])
    try:
        oto_kayit(kos, simdi)
    except Exception as e:
        print("oto kayıt hatası:", repr(e))
    cik = {"guncel": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + " UTC", "saat_notu": "saat: Türkiye saati", "kosular": kos, "toplantilar": toplanti}
    json.dump(cik, open(os.path.join(KOK, "docs", "data", "abd.json"), "w"), ensure_ascii=False)
    try:
        ga_program()
    except Exception as e:
        print("GA program hatası:", repr(e))
    try:
        from . import muhtemeller as MUH
        MUH.calistir()
    except Exception as e:
        print("muhtemeller hatası:", repr(e))
    print("ABD+GA canlı koşu", len(kos), "pencere", pencere_dk)


def oto_kayit(kos, simdi):
    """Otomatik kâğıt üstü kayıt: her koşunun başlamasından önceki SON yerel-oran görüntüsünü saklar (0 <= dk <= 6).
    Bahis anı TJK ganyanı sistemde yok; değerlendirme TJK resmî kapanış ganyanı ile yapılır (data/analiz/abd_oto_degerlendir.py)."""
    yol = os.path.join(KOK, "data", "abd_oto"); os.makedirs(yol, exist_ok=True)
    for k in kos:
        if not (0 <= k["dk"] <= 6):
            continue
        f = os.path.join(yol, k["tarih"] + ".json")
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            d = {}
        atlar = [{"no": a["no"], "ad": a["ad"], "oran": a["oran"]} for a in k["atlar"] if a.get("oran")]
        if len(atlar) < 3:
            continue
        d[f'{k["ulke"]}|{k["pist"]}|{k["kosu"]}'] = {"ulke": k["ulke"], "pist": k["pist"], "kosu": k["kosu"], "saat_utc": k["saat_utc"],
            "dk": round(k["dk"], 1), "gorulen_utc": simdi.strftime("%H:%M:%S"), "atlar": atlar}
        json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False)


def sayfa_probe(dosya="data/probe_istek.txt"):
    """Keşif: dosyadaki her URL'yi (robots.txt izinli sayfalar) yavaşça indirip data/yabanci_ham/probe_<i>.html olarak kaydeder."""
    import requests, time
    H = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; gunde birkac yavas istek)"}
    yol = os.path.join(KOK, "data", "yabanci_ham"); os.makedirs(yol, exist_ok=True)
    urller = [u.strip() for u in open(os.path.join(KOK, dosya), encoding="utf-8") if u.strip().startswith(("http", "tarayici:"))]
    try:
        from curl_cffi import requests as CR          # tarayıcı TLS parmak izi (Cloudflare denemesi)
    except Exception:
        CR = None
    for i, u in enumerate(urller[:10]):
        try:
            if u.startswith("tarayici:"):
                from . import tarayici as TR
                h = TR.getir(u[9:]) or "YOK"
                open(os.path.join(yol, f"probe_{i}.html"), "w", encoding="utf-8").write(h); print(u, len(h)); continue
            r = CR.get(u, impersonate="chrome", timeout=30) if CR else requests.get(u, headers=H, timeout=30)
            open(os.path.join(yol, f"probe_{i}.html"), "w", encoding="utf-8").write(r.text)
            print(u, r.status_code, len(r.text))
        except Exception as e:
            print(u, "hata", repr(e))
        time.sleep(3)


def ga_program(t=None):
    """Günün Güney Afrika toplantıları (agftablosu program sayfası; saat yok) -> docs/data/ga.json. Günde bir kez çekilir."""
    from zoneinfo import ZoneInfo
    t = t or datetime.datetime.now(ZoneInfo("Europe/Istanbul")).date()
    cik = os.path.join(KOK, "docs", "data", "ga.json")
    try:
        eski = json.load(open(cik, encoding="utf-8"))
        if eski.get("tarih") == t.isoformat() and eski.get("kosular"):
            return
    except Exception:
        pass
    ana = O.getir(O.BASE) or ""
    gun = f"{t.day}-{O.AYLAR[t.month-1]}-{t.year}"
    sluglar = sorted(set(s for s in re.findall(r"/at-yarisi/([a-z\-]+)/" + re.escape(gun) + r"-", ana) if s.endswith("-guney-afrika")))
    kos = []
    for sl in sluglar:
        rows = O.parse_prog(O.getir(O.prog_url(t, sl)) or "", t.isoformat(), sl)
        pist = sl.replace("-guney-afrika", "").replace("-", " ").title()
        for kn in sorted({int(r["kosu"]) for r in rows}):
            atlar = [{"no": int(r["no"]), "ad": str(r["p_at"]), "oran": None} for r in rows if int(r["kosu"]) == kn]
            kos.append({"tarih": t.isoformat(), "ulke": "guney-afrika", "kaynak": "program", "pist": pist, "kosu": kn, "saat": "", "atlar": sorted(atlar, key=lambda a: a["no"])})
    json.dump({"tarih": t.isoformat(), "kosular": kos}, open(cik, "w", encoding="utf-8"), ensure_ascii=False)
    print("GA program:", sluglar, len(kos), "koşu")
