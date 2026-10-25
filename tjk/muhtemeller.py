"""vhs.tjk.org/muhtemeller (TJK'nın halka açık canlı muhtemel ganyan sayfası) -> data/muh/<gün>.json

Biçim (18 Ekim 2026'da sayfanın kendi JS'inden çözüldü; robots.txt yok, kullanıcı izni var):
  s/YYYY/MM/DD/checksum.json              (vhs-medya.tjk.org)      -> {day, runs{KEY-no: [koşu_sağlaması, tam_sağlama]}}
  s/YYYY/MM/DD/day-<day>.json             (vhs-medya-cdn.tjk.org)  -> yarislar[]: KEY, YER, YURTDISI, atlar{koşu:{no:ad}}, kosular[{NO,SAAT(TR),DURUM}]
  s/YYYY/MM/DD/<KEY>-<no>-<sağlama>.json (vhs-medya-cdn.tjk.org)  -> muhtemeller.bahisler[GANYAN].muhtemeller[{S1,G,R,A,K}]
DURUM: AÇIK (muhtemel ganyan canlı) / KAPALI (bahis kapandı) / RESMİ (sonuç: R = varış sırası, G = resmî ganyan, G='-' koşmadı).
İstek yükü: günde 2 sabit dosya + yalnız başlamasına ≤ 12 dk kalan açık yurtdışı koşuların kendi dosyası (döngü başına en çok birkaç istek)."""
import datetime, json, os, re, time
import requests

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HOST = "https://vhs-medya.tjk.org/muhtemeller/s/"
CDN = "https://vhs-medya-cdn.tjk.org/muhtemeller/s/"
HEADERS = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; dusuk sikli istek)", "Accept": "application/json"}
try:
    from curl_cffi import requests as _CR
except Exception:
    _CR = None


def _json(url):
    for _ in range(2):
        try:
            r = _CR.get(url, impersonate="chrome", timeout=20) if _CR else requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(1.5)
    return None


def _slug(s):
    t = str(s).lower().translate(str.maketrans("ıİşŞğĞüÜöÖçÇ", "iissgguuoocc"))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def _tr_simdi():
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)


def _ganyan(run):
    """run JSON -> ({no: ganyan}, {no: sıra}, durum, favori)"""
    m = (run.get("data") or {}).get("muhtemeller") or {}
    g, r, fav = {}, {}, None
    for b in m.get("bahisler", []):
        if b.get("isGanyan"):
            for x in b.get("muhtemeller", []):
                try:
                    no = int(x["S1"])
                except Exception:
                    continue
                if x.get("K"):
                    g[no] = None
                    continue
                try:
                    g[no] = float(x["G"])
                except Exception:
                    g[no] = None
                if x.get("R"):
                    r[no] = int(x["R"])
                if x.get("A"):
                    fav = no
    return g, r, m.get("DURUM"), fav


def _havuz(run):
    """run JSON -> {'si': [[S1,S2,G],...], 'ik': [...]} (sıralı ikili / ikili ilk-22 kombinasyon muhtemeli; ilk-5 gölge v3 girdisi)"""
    m = (run.get("data") or {}).get("muhtemeller") or {}; o = {}
    for b in m.get("bahisler", []):
        t = b.get("B")
        if t in ("SIRALI İKİLİ", "İKİLİ"):
            o["si" if t == "SIRALI İKİLİ" else "ik"] = [[x.get("S1"), x.get("S2"), x.get("G")] for x in (b.get("muhtemeller") or [])]
    return o


def topla(tarih=None, pencere_dk=12, yalniz_yurtdisi=True):
    """Bir döngü: günün gününü okur, kaydı data/muh/<gün>.json'a ekler. Döner: yazılan snapshot sayısı."""
    simdi = _tr_simdi()
    gun = tarih or simdi.date().isoformat()
    yol = gun.replace("-", "/")
    ck = _json(f"{HOST}{yol}/checksum.json")
    if not ck or not ck.get("day"):
        print("muh: checksum yok", gun); return 0
    gj = _json(f"{CDN}{yol}/day-{ck['day']}.json")
    if not gj or not gj.get("success"):
        print("muh: gün dosyası yok"); return 0
    dosya = os.path.join(KOK, "data", "muh", gun + ".json")
    os.makedirs(os.path.dirname(dosya), exist_ok=True)
    try:
        D = json.load(open(dosya, encoding="utf-8"))
    except Exception:
        D = {}
    yazilan = 0
    for y in gj["data"]["yarislar"]:
        if yalniz_yurtdisi and not y.get("YURTDISI"):
            continue
        for k in y.get("kosular", []):
            key = f'{y["KEY"]}-{k["NO"]}'
            runs = (ck.get("runs") or {}).get(key)
            if not runs:
                continue
            kay = D.setdefault(key, {"hipodrom": y["KEY"], "yer": y.get("YER"), "slug": _slug(y.get("HIPODROM") or y["KEY"]), "kosu": int(k["NO"]),
                                     "saat_tr": k["SAAT"], "pist": k.get("PIST"), "atlar": (y.get("atlar") or {}).get(str(k["NO"]), {}), "anlik": []})
            kay["saat_tr"] = k["SAAT"]
            try:
                bas = datetime.datetime.combine(simdi.date(), datetime.time.fromisoformat(k["SAAT"]))
                # gece yarısını aşan koşular (ABD): saat < 6 ve şimdi akşam ise ertesi güne ait
                if bas.hour < 6 and simdi.hour >= 12:
                    bas += datetime.timedelta(days=1)
                elif bas.hour >= 12 and simdi.hour < 6:
                    bas -= datetime.timedelta(days=1)
                dk = (bas - simdi.replace(tzinfo=None)).total_seconds() / 60
            except Exception:
                dk = None
            durum = k.get("DURUM")
            if durum == "RESMİ":
                if kay.get("sonuc"):
                    continue
                run = _json(f"{CDN}{yol}/{key}-{runs[0]}.json")
                if run and run.get("success"):
                    g, r, dr, fav = _ganyan(run)
                    if r:
                        kay["sonuc"] = {"sira": {str(n): s for n, s in r.items()}, "ganyan": {str(n): v for n, v in g.items()}}
                        yazilan += 1
                continue
            if dk is None or not (-60 <= dk <= pencere_dk):
                continue
            if dk < 0 and kay["anlik"] and kay["anlik"][-1].get("durum") not in ("AÇIK", None):
                continue                                     # bahis kapandı: izlemeyi bırak (ertelemelerde 15 dk'yı bulabilir; açık kaldığı sürece sürer)
            run = _json(f"{CDN}{yol}/{key}-{runs[0]}.json")
            if run and run.get("success"):
                g, r, dr, fav = _ganyan(run)
                if g:
                    kay["anlik"].append({"t": simdi.strftime("%H:%M:%S"), "dk": round(dk, 1), "durum": dr, "g": {str(n): v for n, v in g.items()}, "fav": fav})
                    kay["anlik"] = kay["anlik"][-40:]
                    try:
                        hv = _havuz(run)
                        if hv.get("si") and hv.get("ik"):
                            kay["havuz"] = {"t": simdi.strftime("%H:%M:%S"), "dk": round(dk, 1), "durum": dr, **hv}   # yalnız son durum (ilk5 gölge v3)
                    except Exception:
                        pass
                    yazilan += 1
    json.dump(D, open(dosya, "w", encoding="utf-8"), ensure_ascii=False)
    print("muh:", gun, "yazılan", yazilan, "koşu", len(D))
    try:
        _canli_yaz(D)
    except Exception as e:
        print("muh canlı yazım hatası:", repr(e))
    return yazilan


def _canli_yaz(D):
    """Sayfa (Yabancı sekmesi) için: son 90 dk içinde alınmış en güncel AÇIK muhtemel ganyan -> docs/data/muh_canli.json (at adıyla eşleşir)."""
    yol = os.path.join(KOK, "docs", "data", "muh_canli.json")
    simdi = datetime.datetime.now(datetime.timezone.utc)
    try:
        C = json.load(open(yol, encoding="utf-8"))
    except Exception:
        C = {}
    for key, k in D.items():
        a = [x for x in k.get("anlik", []) if x.get("durum") == "AÇIK" and x.get("g")]
        if not a or k.get("sonuc"):
            continue
        C[key] = {"yer": k.get("yer"), "kosu": k["kosu"], "saat_tr": k["saat_tr"], "atlar": k.get("atlar"),
                  "g": a[-1]["g"], "dk": a[-1]["dk"], "utc": simdi.strftime("%Y-%m-%dT%H:%M:%SZ")}
    sinir = (simdi - datetime.timedelta(minutes=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
    C = {a: b for a, b in C.items() if b.get("utc", "") >= sinir and not (D.get(a) or {}).get("sonuc")}
    json.dump(C, open(yol, "w", encoding="utf-8"), ensure_ascii=False)


def program_saatleri(tarih):
    """vhs-medya gün dosyasından {HİPODROM_SLUG: {koşu_no: 'SS:DD'}} (yurtiçi dahil). Program CSV'si gelmediği günlerde saat bilgisi buradan alınır (22 Ekim 2026)."""
    yol = tarih.replace("-", "/")
    ck = _json(f"{HOST}{yol}/checksum.json")
    if not ck or not ck.get("day"):
        return {}
    gj = _json(f"{CDN}{yol}/day-{ck['day']}.json")
    if not gj or not gj.get("success"):
        return {}
    out = {}
    for y in gj["data"]["yarislar"]:
        if y.get("YURTDISI"):
            continue
        out[_slug(y["KEY"])] = {int(k["NO"]): k["SAAT"] for k in y.get("kosular", []) if k.get("SAAT")}
    return out


def _dk(saat, simdi):
    bas = datetime.datetime.combine(simdi.date(), datetime.time.fromisoformat(saat))
    if bas.hour < 6 and simdi.hour >= 12:
        bas += datetime.timedelta(days=1)
    elif bas.hour >= 12 and simdi.hour < 6:
        bas -= datetime.timedelta(days=1)
    return (bas - simdi.replace(tzinfo=None)).total_seconds() / 60


def yakin(sure_s, aralik=40, ust=5.0, alt=-1.5):
    """Döngü arasındaki bekleme süresinde: başlamasına [alt, ust] dk kalan açık koşuların muhtemel ganyanını sık aralıkla (varsayılan 40 sn) kaydeder.
    Amaç: bahis anı ganyanı ile resmî kapanış ganyanı arasındaki farkı (T-4..T0) ince çözünürlükle ölçmek. Her turda 1 checksum + yalnız pencere içindeki koşular."""
    bitis = time.time() + sure_s
    gj = None; gun_day = None; n = 0
    while time.time() < bitis - 5:
        t0 = time.time(); simdi = _tr_simdi(); gun = simdi.date().isoformat()
        if simdi.hour < 6:   # gece yarısını aşan koşular dünün TJK gününde
            gun = (simdi.date() - datetime.timedelta(days=1)).isoformat()
        yol = gun.replace("-", "/")
        ck = _json(f"{HOST}{yol}/checksum.json")
        if ck and ck.get("day"):
            if gun_day != (gun, ck["day"]):
                gj = _json(f"{CDN}{yol}/day-{ck['day']}.json"); gun_day = (gun, ck["day"])
            dosya = os.path.join(KOK, "data", "muh", gun + ".json")
            try:
                D = json.load(open(dosya, encoding="utf-8"))
            except Exception:
                D = {}
            yaz = 0
            for y in ((gj or {}).get("data") or {}).get("yarislar", []):
                for k in y.get("kosular", []):
                    key = f'{y["KEY"]}-{k["NO"]}'; runs = (ck.get("runs") or {}).get(key)
                    kay = D.get(key)
                    if not runs or not kay or kay.get("sonuc") or k.get("DURUM") == "RESMİ":
                        continue
                    try:
                        dk = _dk(k["SAAT"], simdi)
                    except Exception:
                        continue
                    if not (alt <= dk <= ust):
                        continue
                    run = _json(f"{CDN}{yol}/{key}-{runs[0]}.json")
                    if run and run.get("success"):
                        g, r, dr, fav = _ganyan(run)
                        if g:
                            kay["anlik"].append({"t": simdi.strftime("%H:%M:%S"), "dk": round(dk, 2), "durum": dr, "g": {str(a): v for a, v in g.items()}, "fav": fav})
                            kay["anlik"] = kay["anlik"][-40:]; yaz += 1
            if yaz:
                json.dump(D, open(dosya, "w", encoding="utf-8"), ensure_ascii=False); n += yaz
        kal = aralik - (time.time() - t0)
        if kal > 0 and time.time() + kal < bitis - 5:
            time.sleep(kal)
        elif kal > 0:
            break
    print("muh yakin: yazılan", n)
    return n


def geri(tarihler):
    """Geçmiş günler (bir kez): resmî sonuçlar + TJK'nın arşivlenmiş ganyan geçmişi (s/h/<gün>/<KEY>-<no>-GANYAN-0.json, varsa) -> data/muh."""
    for g in tarihler:
        try:
            topla(g)
        except Exception as e:
            print("muh geri hatası:", repr(e))
        yol = g.replace("-", "/")
        dosya = os.path.join(KOK, "data", "muh", g + ".json")
        try:
            D = json.load(open(dosya, encoding="utf-8"))
        except Exception:
            continue
        hk = os.path.join(KOK, "data", "muh", "h", g); os.makedirs(hk, exist_ok=True)
        n = 0
        for key in D:
            h = _json(f"{CDN}h/{yol}/{key}-GANYAN-0.json")
            if h:
                json.dump(h, open(os.path.join(hk, key + ".json"), "w", encoding="utf-8"), ensure_ascii=False); n += 1
        print("muh geçmiş ganyan dosyası:", g, n, "/", len(D))


def calistir():
    """Döngü girişi: bugün (+ gece yarısından sonra dünün TJK günü, çünkü ABD koşuları ertesi güne taşar)."""
    simdi = _tr_simdi(); n = 0
    gf = os.path.join(KOK, "data", "muh_geri.txt")
    if os.path.exists(gf):
        tl = [x.strip() for x in open(gf) if re.match(r"\d{4}-\d\d-\d\d", x.strip())]
        os.remove(gf)
        geri(tl)
    gunler = [simdi.date().isoformat()]
    if simdi.hour < 6:
        gunler.append((simdi.date() - datetime.timedelta(days=1)).isoformat())
    for g in gunler:
        try:
            n += topla(g, yalniz_yurtdisi=False)
        except Exception as e:
            print("muh hatası:", repr(e))
    return n


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "yakin":
        yakin(int(sys.argv[2]))
    else:
        calistir()
