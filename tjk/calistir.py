"""Kullanım:  python -m tjk.calistir sabah | canli | gece | hepsi
sabah: bugünün programı + model form puanları + AGF  -> docs/data/bugun.json
canli: AGF'yi yeniler, biten koşuların sonucunu ve kapanış ganyanlarını ekler
gece : dünün (ve eksik günlerin) sonuçlarını geçmişe ekler, canlı test skorunu hesaplar -> docs/data/skor.json"""
import os, sys, json, glob, datetime
import numpy as np, pandas as pd
from . import ortak as O
from . import csvprog as C
from . import sonuccsv as SC
from .ozellik import hazirla, model_olasilik
from . import kupon as KP
from . import plase as PL
from . import devir as DV
from . import egzotik as EG
from . import golge as GL
from . import bildir as BL

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
        if os.path.exists(gun_yolu(t)):                    # kaynak geçici olarak okunamadıysa eldeki iyi programı SİLME
            eski = json.load(open(gun_yolu(t), encoding="utf-8"))
            if eski.get("hipodromlar"):
                print("eldeki program korundu:", [h["id"] for h in eski["hipodromlar"]])
                yaz_json(os.path.join(SITE, "bugun.json"), eski)
                return eski
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
    A = GL.yukle(); bz2 = {}
    if A:
        try:
            bugun_m = {(h, int(kn)): GL.MS.bilgiden(b_) for h in programlar for kn, b_ in programlar[h]["bilgi"].items() if GL.MS.bilgiden(b_)}
            d2 = GL.MS.ekle(d, bugun_m) if "f_dp150_m" in A["feat"] else d
            dy = d2[d2.yeni].copy(); dy["z2"] = GL.z2(dy, A)
            bz2 = dy.set_index(["hipodrom", "kosu", "no"]).z2.to_dict()
        except Exception as e:
            print("aday model hatası:", repr(e)); A = None
    obj = {"tarih": tarih, "model": M.get("surum", "v1"), "w0": float(M["w"][0]),
           **({"w0_aday": float(A["w"][0]), "lp2_aday": float(A.get("lp2_a", 0.0)), "aday_egitim_son": A["egitim_son_tarih"]} if A else {}),
           "guncelleme": O.tr_simdi().strftime("%H:%M"), "hipodromlar": []}
    for h in [x for x in O.TRH if x in programlar]:
        g = pr[pr.hipodrom == h]
        kos = []
        for kn, kg in g.groupby("kosu"):
            atlar = [{"no": int(r.no), "at": r.p_at, "jokey": r.p_jokey, "apr": bool(r.p_apranti),
                      "st": bos_sayi(float(r.st)) if pd.notna(r.st) else None,
                      "z": round(float(bz.get((h, kn, int(r.no)), 0.0)), 4),
                      **({"z2": round(float(bz2.get((h, kn, int(r.no)), 0.0)), 4)} if A else {})} for r in kg.itertuples()]
            kos.append({"kosu": int(kn), "saat": programlar[h]["saat"].get(int(kn)),
                        "bilgi": programlar[h]["bilgi"].get(int(kn)), "atlar": atlar})
        obj["hipodromlar"].append({"id": h, "ad": O.AD[h], "kosular": kos})
    agf_ekle(obj)
    csv_uygula(obj)
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


def csv_uygula(obj):
    """data/tjk_csv/ içindeki o güne ait TJK CSV'lerinden saat, cins, mesafe, pist, ikramiyeyi koşulara işler ve eğitim verisi için biriktirir."""
    veri = C.gunun(obj["tarih"])
    n = 0
    for h in obj["hipodromlar"]:
        if h["id"] not in veri:
            continue
        kosular, atlar, ekur = veri[h["id"]]
        for k in h["kosular"]:
            b = kosular.get(k["kosu"])
            if not b:
                continue
            k["saat"] = b["saat"]; k["bilgi"] = C.bilgi_metni(b)
            k["mesafe"] = b["mesafe"]; k["pist"] = b["pist"]; k["cins"] = b["cins"]; k["ikramiye"] = b["ikramiye1"]
            n += 1
        C.kaydet(obj["tarih"], h["id"], kosular, atlar, VERI)
    if n:
        print("TJK CSV'den koşu bilgisi işlendi:", n, "koşu")


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
        h["altili"] = {}
        for alt, ayaklar in agf[h["id"]].items():
            m = O.agf_kosulara({alt: ayaklar}, atlar)
            if m:
                h["altili"][str(alt)] = max(m)       # altılının son koşusu
                for kk in h["kosular"]:              # iki altılıda da olan koşular için her tablonun değeri ayrı saklanır (agf = sonuncusu)
                    dd = m.get(kk["kosu"])
                    if dd:
                        for a in kk["atlar"]:
                            if dd.get(a["no"]) is not None:
                                a["agf_a" + str(alt)] = dd[a["no"]]
        for k in h["kosular"]:
            d = harita.get(k["kosu"])
            if not d:
                continue
            for a in k["atlar"]:
                v = d.get(a["no"])
                a["agf"] = v
                if v is not None and a.get("agf0") is None:
                    a["agf0"] = v                    # ilk görülen AGF (sabah)
            k["agf_saat"] = O.tr_simdi().strftime("%H:%M")
            k.setdefault("agf0_saat", k["agf_saat"])
    print("AGF eklendi:", {h: len(v) for h, v in agf.items()})


# ------------------------------------------------------------------ canlı (sonuçlar)
def agf_arsivle(obj):
    """O günün ilk ve son AGF değerlerini data/agf/YYYY-MM.csv.gz içine yazar (ileride AGF-ganyan sapması testi için)."""
    rows = []
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            for a in k["atlar"]:
                if a.get("agf") is None and a.get("agf0") is None:
                    continue
                rows.append({"tarih": obj["tarih"], "hipodrom": h["id"], "kosu": k["kosu"], "no": a["no"],
                             "agf0": a.get("agf0"), "agf": a.get("agf"),
                             "agf0_saat": k.get("agf0_saat"), "agf_saat": k.get("agf_saat")})
    if not rows:
        return 0
    yeni = pd.DataFrame(rows)
    yol = os.path.join(VERI, "agf", obj["tarih"][:7] + ".csv.gz")
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    if os.path.exists(yol):
        yeni = pd.concat([pd.read_csv(yol), yeni], ignore_index=True)
    yeni = yeni.drop_duplicates(O.K + ["no"], keep="last").sort_values(O.K + ["no"])
    yeni.to_csv(yol, index=False)
    return len(rows)


def agf_zaman_yaz(obj):
    """Her AGF okumasını data/agf_zaman/<gün>.csv.gz içine zaman damgasıyla ekler (yalnızca değeri değişen atlar).
    Amaç: AGF yarışa yaklaştıkça nasıl hareket ediyor ve bu hareket bilgi taşıyor mu testi."""
    saat = O.tr_simdi().strftime("%H:%M")
    yol = os.path.join(VERI, "agf_zaman", obj["tarih"] + ".csv.gz")
    eski = pd.read_csv(yol) if os.path.exists(yol) else pd.DataFrame(columns=["saat", "hipodrom", "kosu", "no", "agf"])
    son = {}
    for r in eski.itertuples():
        son[(r.hipodrom, r.kosu, r.no)] = r.agf
    rows = []
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            if k.get("sonuc"):
                continue
            for a in k["atlar"]:
                v = a.get("agf")
                if v is None or son.get((h["id"], k["kosu"], a["no"])) == v:
                    continue
                rows.append({"saat": saat, "hipodrom": h["id"], "kosu": k["kosu"], "no": a["no"], "agf": v})
    if rows:
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        pd.concat([eski, pd.DataFrame(rows)], ignore_index=True).to_csv(yol, index=False, compression="gzip")
    return len(rows)


def hizli(t):
    """Yarış başlangıcına son 40 dakikada 5 dakikada bir AGF'yi okur, yalnızca data/agf_zaman'a yazar (gün JSON'una dokunmaz)."""
    import copy
    yol = gun_yolu(t)
    if not os.path.exists(yol):
        return
    obj = json.load(open(yol, encoding="utf-8"))
    simdi = O.tr_simdi(); dk = simdi.hour * 60 + simdi.minute
    def mins(x):
        try: return int(x[:2]) * 60 + int(x[3:5])
        except Exception: return None
    yakin = [mins(k.get("saat")) for h in obj["hipodromlar"] for k in h["kosular"] if not k.get("sonuc") and mins(k.get("saat")) is not None]
    if not any(m - 40 <= dk <= m + 2 for m in yakin):
        print("yarışa yakın pencere yok, atlandı"); return
    c = copy.deepcopy(obj)
    agf_ekle(c)
    print("agf_zaman satırı:", agf_zaman_yaz(c))


def kosmaz_isle(obj):
    """SİB program sayfası yapıştırmalarından (data/sib/<gün>-<hip>.csv, gerçek at numarası) koşmaz atları işaretler."""
    n = 0
    elle = set()
    ky = os.path.join(VERI, "kosmaz", obj["tarih"] + ".csv")
    if os.path.exists(ky):
        e = pd.read_csv(ky)
        elle = {(str(r.hipodrom), int(r.kosu), int(r.no)) for r in e.itertuples()}
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            for a in k["atlar"]:
                if (h["id"], k["kosu"], a["no"]) in elle:
                    if not a.get("kosmaz"):
                        n += 1
                    a["kosmaz"] = True
        y = os.path.join(VERI, "sib", f"{obj['tarih']}-{h['id']}.csv")
        if not os.path.exists(y):
            continue
        d = pd.read_csv(y)
        if "kosmaz" not in d.columns:
            continue
        km = {(int(r.kosu), int(r.no)) for r in d[d.kosmaz == 1].itertuples()}
        for k in h["kosular"]:
            for a in k["atlar"]:
                if (k["kosu"], a["no"]) in km:
                    if not a.get("kosmaz"):
                        n += 1
                    a["kosmaz"] = True
    if n:
        print("koşmaz işaretlendi:", n)


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
            z2 = {a["no"]: a.get("z2") for a in k["atlar"]}
            r["z2"] = r.no.map(z2)
            if obj.get("w0_aday") is not None and r.z2.notna().all():
                r["p_aday"] = model_olasilik(r.p_piyasa.values, r.z2.values, obj["w0_aday"], obj.get("lp2_aday", 0.0))
            k["sonuc"] = {str(int(x.no)): {"sira": None if pd.isna(x.sira) else int(x.sira),
                                           "g": float(x.ganyan), "pp": round(float(x.p_piyasa), 5),
                                           "pm": round(float(x.p_model), 5),
                                           **({"pm2": round(float(x.p_aday), 5)} if "p_aday" in r.columns else {})} for x in r.itertuples()}
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
        try:
            agf_zaman_yaz(obj)
        except Exception as e:
            print("agf_zaman hatası:", repr(e))
    csv_uygula(obj)
    kosmaz_isle(obj)
    n = sonuclari_isle(obj, t)
    print("yeni sonuçlanan koşu:", n)
    try:
        KP.guncelle(obj)
    except Exception as e:                       # kupon kaydı isteğe bağlı; ana işi durdurmasın
        print("kupon hatası:", repr(e))
    try:
        KP.guncelle7(obj)
    except Exception as e:
        print("7'li kupon hatası:", repr(e))
    try:
        EG.guncelle(obj)
    except Exception as e:
        print("egzotik hatası:", repr(e))
    try:
        PL.guncelle(obj)
    except Exception as e:
        print("plase hatası:", repr(e))
    try:
        DV.guncelle(obj)
    except Exception as e:
        print("devir hatası:", repr(e))
    try:
        print("bildirim gönderildi:", BL.gonder(obj["tarih"], O.tr_simdi().strftime("%H:%M")))
    except Exception as e:
        print("bildirim hatası:", repr(e))
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
            fk = O.parse_fark(html, g.isoformat(), h)
            if fk: ekle("fark", pd.DataFrame(fk), ["tarih", "hipodrom", "kosu", "sira", "no", "fark_txt", "fark_boy"])
            yeni_p += O.parse_prog(O.getir(O.prog_url(g, h)) or "", g.isoformat(), h)
            print(" ", g, h, len(s), "satır")
        # o günün sitedeki kaydına eksik sonuçları ekle
        yol = gun_yolu(g)
        if os.path.exists(yol):
            obj = json.load(open(yol, encoding="utf-8"))
            if sonuclari_isle(obj, g):
                yaz_json(yol, obj)
            try:
                KP.guncelle(obj)
            except Exception as e:
                print("kupon hatası:", repr(e))
            try:
                KP.guncelle7(obj)
            except Exception as e:
                print("7'li kupon hatası:", repr(e))
            try:
                EG.guncelle(obj)
            except Exception as e:
                print("egzotik hatası:", repr(e))
            try:
                PL.guncelle(obj)
            except Exception as e:
                print("plase hatası:", repr(e))
            print("  AGF arşivlendi:", g, agf_arsivle(obj), "satır")
    if yeni_s:
        ns, npg = pd.DataFrame(yeni_s), pd.DataFrame(yeni_p)
        ekle("sonuclar", ns, sn.columns)
        te = oku("temiz")
        ekle("temiz", O.temiz_yap(ns), te.columns)
        if len(npg):
            ekle("program", npg, oku("program").columns)
        print("EKLENDİ: sonuç", len(ns), "program", len(npg))
    skor()
    try:
        GL.egit()                                   # aday model: dünün sonuna kadar yeniden eğit
        print("gölge skor:", GL.skor())
    except Exception as e:
        print("gölge model hatası:", repr(e))
    try:
        from . import walkforward as WF            # Bolton/Jason ozellikleri vs piyasa: ceyreklik walk-forward (sonuc docs/data/walkforward.json)
        WF.main()
    except Exception as e:
        print("walk-forward hatası:", repr(e))


# ------------------------------------------------------------------ geçmiş günleri siteye aktar
def farkgecmis(bas, bit):
    """Geçmiş sonuç sayfalarından yalnızca bitiş farkını (data/fark) doldurur; zaten kayıtlı gün-hipodromları atlar."""
    sn = oku("sonuclar")[["tarih", "hipodrom"]].drop_duplicates()
    sn = sn[(sn.tarih >= bas.isoformat()) & (sn.tarih <= bit.isoformat())].sort_values(["tarih", "hipodrom"])
    try:
        f0 = oku("fark")[["tarih", "hipodrom"]].drop_duplicates(); var = set(zip(f0.tarih, f0.hipodrom))
    except Exception:
        var = set()
    import time
    t0 = time.time(); n, toplu = 0, []
    for t, h in zip(sn.tarih, sn.hipodrom):
        if (t, h) in var: continue
        if time.time() - t0 > 150 * 60: print("süre sınırı, kaldığı yerden yeniden çalıştırın"); break
        html = ""
        for u in O.sonuc_urls(datetime.date.fromisoformat(t), h):
            html = O.getir(u)
            if html: break
        if html: toplu += O.parse_fark(html, t, h)
        if len(toplu) >= 600:
            ekle("fark", pd.DataFrame(toplu), ["tarih", "hipodrom", "kosu", "sira", "no", "fark_txt", "fark_boy"]); n += len(toplu); toplu = []; print(t, "kaydedildi", n, flush=True)
    if toplu:
        ekle("fark", pd.DataFrame(toplu), ["tarih", "hipodrom", "kosu", "sira", "no", "fark_txt", "fark_boy"]); n += len(toplu)
    print("farkgecmis bitti, satır:", n)


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


def skor_ek(c, kz):
    """Kalibrasyon, günlük log-loss ve sapma grupları (c: model olasılıklı satırlar, kz: kazananlar)."""
    ek = {}
    kal = []
    for lo, hi in ((0, .03), (.03, .06), (.06, .10), (.10, .15), (.15, .22), (.22, .35), (.35, 1.01)):
        x = c[(c.p_model >= lo) & (c.p_model < hi)]
        if len(x):
            kal.append({"aralik": f"{int(lo*100)}–{min(100,int(round(hi*100)))}", "n": int(len(x)),
                        "model": float(x.p_model.mean()), "piyasa": float(x.p_piyasa.mean()), "gercek": float(x.kazandi.mean())})
    ek["kalibrasyon"] = kal
    gun = []
    for t, x in kz.groupby("tarih"):
        gun.append({"t": t, "n": int(len(x)), "ll_model": float(-np.log(x.p_model).mean()), "ll_piyasa": float(-np.log(x.p_piyasa).mean())})
    ek["gunluk"] = gun[-30:]
    r = c.p_model / c.p_piyasa
    grp = []
    for ad, m in (("Model piyasadan çok yüksek (≥1,5×)", (r >= 1.5) & (c.p_model >= .05)),
                  ("Model piyasadan çok düşük (≤0,67×)", (r <= 0.67) & (c.p_piyasa >= .05))):
        x = c[m]
        grp.append({"ad": ad, "n": int(len(x)), "gercek": int(x.kazandi.sum()) if len(x) else 0,
                    "model": float(x.p_model.sum()) if len(x) else 0.0, "piyasa": float(x.p_piyasa.sum()) if len(x) else 0.0})
    ek["sapma"] = grp
    return ek


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
    out.update(skor_ek(c, kz))
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
    arg = []
    if ":" in mod: mod, *arg = mod.split(":")
    simdi = O.tr_simdi(); bugun = simdi.date()
    if mod == "sabah":
        sabah(bugun)
    elif mod == "hizli":
        hizli(bugun)
    elif mod == "canli":
        SC.isle()
        canli(bugun)
    elif mod == "gece":
        SC.isle()
        gece(bugun)
    elif mod == "gecmis":
        bas = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else bugun - datetime.timedelta(days=45)
        gecmis(bas, bugun - datetime.timedelta(days=1))
    elif mod == "robots":
        import requests
        r = requests.get("https://www.tjk.org/robots.txt", timeout=30, headers={"User-Agent": "tjk-sistem/1.0 (kisisel arastirma)"})
        yaz_json(os.path.join(SITE, "robots_tjk.json"), {"durum": r.status_code, "metin": r.text[:6000]})
        print(r.status_code); print(r.text[:3000])
    elif mod == "sonucbak":
        # keşif: sonuç sayfasında ikramiye/havuz/devir bilgisi var mı? (yalnızca agftablosu)
        from bs4 import BeautifulSoup
        rapor = {"zaman": O.tr_simdi().strftime("%Y-%m-%d %H:%M"), "sayfalar": []}
        for geri in (1, 2, 3):
            t = bugun - datetime.timedelta(days=geri)
            for h in O.TRH:
                html = ""
                for u in O.sonuc_urls(t, h):
                    html = O.getir(u) or ""
                    if html: break
                if not html: continue
                metin = BeautifulSoup(html, "html.parser").get_text("\n")
                satirlar = [x.strip() for x in metin.splitlines() if x.strip()]
                anahtar = ("altılı", "altili", "ikili", "üçlü", "ucul", "dörtlü", "sıralı", "devir", "ikramiye", "havuz", "ödül", "toplam")
                ilgili = [x for x in satirlar if any(a in x.lower() for a in anahtar)]
                rapor["sayfalar"].append({"tarih": t.isoformat(), "hip": h, "uzunluk": len(html), "ilgili": ilgili[:80], "bas": satirlar[:60]})
                break
            if len(rapor["sayfalar"]) >= 3: break
        yaz_json(os.path.join(SITE, "probe_sonuc.json"), rapor)
        print(json.dumps(rapor, ensure_ascii=False)[:3000])
    elif mod == "farkgecmis":
        farkgecmis(datetime.date.fromisoformat(arg[0]), datetime.date.fromisoformat(arg[1]))
    elif mod == "muhtemelbak":
        import re as _re
        from bs4 import BeautifulSoup
        ana = O.getir(O.BASE) or ""
        linkler = sorted(set(_re.findall(r'href="([^"]*muhtemel[^"]*)"', ana, flags=_re.I)))
        rapor = {"zaman": O.tr_simdi().strftime("%Y-%m-%d %H:%M"), "linkler": linkler, "sayfalar": []}
        for l in linkler[:3]:
            u = l if l.startswith("http") else O.BASE + (l if l.startswith("/") else "/" + l)
            h = O.getir(u) or ""
            satir = [x.strip() for x in BeautifulSoup(h, "html.parser").get_text("\n").splitlines() if x.strip()]
            rapor["sayfalar"].append({"url": u, "uzunluk": len(h), "satir": satir[:120]})
        yaz_json(os.path.join(SITE, "probe_muhtemel.json"), rapor)
        print(json.dumps(rapor, ensure_ascii=False)[:2500])
    elif mod == "skor":
        skor()
    elif mod == "dene":
        dene(bugun)
    elif mod == "hepsi":
        gece(bugun); sabah(bugun); canli(bugun)
    else:
        raise SystemExit("bilinmeyen mod: " + mod)
    if mod in ("canli", "gece", "hepsi"):
        try:
            from . import canli as CN
            CN.ozet()
        except Exception as ex:
            print("canli oran özeti atlandı:", ex)


if __name__ == "__main__":
    main()
