"""Kullanım:  python -m tjk.calistir sabah | canli | gece | hepsi
sabah: bugünün programı + model form puanları + AGF  -> docs/data/bugun.json
canli: AGF'yi yeniler, biten koşuların sonucunu ve kapanış ganyanlarını ekler
gece : dünün (ve eksik günlerin) sonuçlarını geçmişe ekler, canlı test skorunu hesaplar -> docs/data/skor.json"""
import re, os, sys, json, glob, datetime
import numpy as np, pandas as pd
from . import ortak as O
from . import csvprog as C
from . import sonuccsv as SC
from .ozellik import hazirla, model_olasilik
from . import kupon as KP
from . import plase as PL
from . import tuyo as TY
from . import besli as BS
from . import tabela as TB
from . import sirali3 as S3
from . import deger as DG
from . import kombine as KB
from . import uyandir as UY
from . import devir as DV
from . import egzotik as EG
from . import uc_at as UA
from . import golge as GL
from . import esnek as ES
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
    csv_agf = {}
    if not satirlar:
        try:                                          # program sitesi (agftablosu) engelli/erişilemez: günün programı TJK program CSV'lerinden kurulur
            satirlar, programlar, csv_agf = C.program_satirlari(tarih)
            if satirlar:
                print("program agftablosu yerine TJK CSV'den kuruldu:", sorted(programlar))
        except Exception as e:
            print("CSV program hatası:", repr(e)); satirlar, programlar, csv_agf = [], {}, {}
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
    A = GL.yukle(); bz2 = {}; bzj = {}
    if A:
        try:
            bugun_m = {(h, int(kn)): GL.MS.bilgiden(b_) for h in programlar for kn, b_ in programlar[h]["bilgi"].items() if GL.MS.bilgiden(b_)}
            d2 = GL.MS.ekle(d, bugun_m) if "f_dp150_m" in A["feat"] else d
            dy = d2[d2.yeni].copy(); dy["z2"] = GL.z2(dy, A)
            bz2 = dy.set_index(["hipodrom", "kosu", "no"]).z2.to_dict()
            try:
                from . import g1v3 as _V3; G3 = _V3.yukle()
                if G3:
                    dj = d2[d2.yeni].copy(); dj["zj"] = _V3.zj(dj, G3); bzj = dj.set_index(["hipodrom", "kosu", "no"]).zj.to_dict()
            except Exception as e:
                print("v3 zj hatası:", repr(e)); bzj = {}
        except Exception as e:
            print("aday model hatası:", repr(e)); A = None
    AK = GL.yukle_k(); bz3 = {}
    if AK and A:
        try:
            dk = GL.kapi_ekle(d2); dk = dk[dk.yeni].copy(); dk["z3"] = GL.z2(dk, AK)
            bz3 = dk.set_index(["hipodrom", "kosu", "no"]).z3.to_dict()
        except Exception as e:
            print("Jason-K hatası:", repr(e)); AK = None
    else:
        AK = None
    AF = GL.yukle_f(); bz5 = {}
    if AF and A:
        try:
            df_ = GL.fk_ekle(d2); df_ = df_[df_.yeni].copy(); df_["z5"] = GL.z2(df_, AF)
            bz5 = df_.set_index(["hipodrom", "kosu", "no"]).z5.to_dict()
        except Exception as e:
            print("Jason-F hatası:", repr(e)); AF = None
    else:
        AF = None
    AS = GL.yukle_s(); bz4 = {}
    if AS and A:
        try:
            ds = d2[d2.yeni].copy(); ds["z4"] = GL.z2(ds, AS)
            bz4 = ds.set_index(["hipodrom", "kosu", "no"]).z4.to_dict()
        except Exception as e:
            print("Jason-S hatası:", repr(e)); AS = None
    else:
        AS = None
    obj = {"tarih": tarih, "model": M.get("surum", "v1"), "w0": float(M["w"][0]),
           **({"w0_aday": float(A["w"][0]), "lp2_aday": float(A.get("lp2_a", 0.0)), "aday_egitim_son": A["egitim_son_tarih"]} if A else {}),
           **({"w0_k": float(AK["w"][0]), "lp2_k": float(AK.get("lp2_a", 0.0))} if AK else {}),
           **({"w0_f": float(AF["w"][0]), "lp2_f": float(AF.get("lp2_a", 0.0))} if AF else {}),
           **({"w0_s": float(AS["w"][0]), "lp2_s": float(AS.get("lp2_a", 0.0)), "a_s": [round(float(x), 4) for x in AS["a"]]} if AS else {}),
           "guncelleme": O.tr_simdi().strftime("%H:%M"), "hipodromlar": []}
    for h in [x for x in O.TRH if x in programlar]:
        g = pr[pr.hipodrom == h]
        kos = []
        for kn, kg in g.groupby("kosu"):
            atlar = [{"no": int(r.no), "at": r.p_at, "jokey": r.p_jokey, "apr": bool(r.p_apranti),
                      "st": bos_sayi(float(r.st)) if pd.notna(r.st) else None,
                      **({"kg": float(r.p_kilo)} if pd.notna(getattr(r, "p_kilo", None)) else {}),
                      **({"hk": float(r.hk)} if pd.notna(getattr(r, "hk", None)) else {}),
                      "z": round(float(bz.get((h, kn, int(r.no)), 0.0)), 4),
                      **({"zj": round(float(bzj[(h, kn, int(r.no))]), 4)} if (h, kn, int(r.no)) in bzj else {}),
                      **({"z2": round(float(bz2.get((h, kn, int(r.no)), 0.0)), 4)} if A else {}),
                      **({"z3": round(float(bz3.get((h, kn, int(r.no)), 0.0)), 4)} if AK else {}),
                      **({"z4": round(float(bz4.get((h, kn, int(r.no)), 0.0)), 4)} if AS else {}),
                      **({"z5": round(float(bz5.get((h, kn, int(r.no)), 0.0)), 4)} if AF else {})} for r in kg.itertuples()]
            kos.append({"kosu": int(kn), "saat": programlar[h]["saat"].get(int(kn)),
                        "bilgi": programlar[h]["bilgi"].get(int(kn)), "atlar": atlar})
        obj["hipodromlar"].append({"id": h, "ad": O.AD[h], "kosular": kos})
    agf_ekle(obj)
    csv_agf_uygula(obj, csv_agf)
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


def saat_duzelt(obj):
    """data/saat_duzelt.json: {"tarih": {"hipodrom": {"koşu": "SS:DD"}}} - erteleme gibi elle bildirilen koşu saatleri; TJK programı/CSV'si ne derse desin bu saat geçerli olur."""
    try:
        d = json.load(open(os.path.join(VERI, "saat_duzelt.json"), encoding="utf-8")).get(obj["tarih"], {})
    except Exception:
        return 0
    n = 0
    for h in obj["hipodromlar"]:
        for kn, sa in (d.get(h["id"]) or {}).items():
            for k in h["kosular"]:
                if str(k["kosu"]) == str(kn) and not k.get("sonuc") and k.get("saat") != sa:
                    k["saat"] = sa; n += 1
    if n:
        print("elle saat düzeltmesi uygulandı:", n, "koşu")
    return n


def vhs_saat(obj):
    """Program CSV'si olmayan (saati boş) koşulara saati TJK'nın halka açık canlı muhtemel sayfasından (vhs-medya) işler; CSV'deki saate dokunmaz."""
    try:
        from . import muhtemeller as MH
        if not any(not k.get("saat") for h in obj["hipodromlar"] for k in h["kosular"]):
            return
        sa = MH.program_saatleri(obj["tarih"])
        n = 0
        for h in obj["hipodromlar"]:
            d = sa.get(MH._slug(h["id"])) or {}
            for k in h["kosular"]:
                if not k.get("saat") and d.get(int(k["kosu"])):
                    k["saat"] = d[int(k["kosu"])]; n += 1
        if n:
            print("vhs'den koşu saati işlendi:", n, "koşu")
    except Exception as e:
        print("vhs saat hatası:", repr(e)[:100])


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
            eski = re.search(r"(\d{3,4})\s*m?\s*(Kum|Çim|Sentetik)", k.get("bilgi") or "")
            yeni_b = C.bilgi_metni(b)
            ym = re.search(r"(\d{3,4})\s*m?\s*(Kum|Çim|Sentetik)", yeni_b or "")
            if ym and (not eski or eski.groups() != ym.groups()) and not k.get("sonuc"):
                k["yeniden_puan"] = True
            k["saat"] = b["saat"]; k["bilgi"] = yeni_b
            k["mesafe"] = b["mesafe"]; k["pist"] = b["pist"]; k["cins"] = b["cins"]; k["ikramiye"] = b["ikramiye1"]
            k["besli"] = bool(b.get("besli")); k["tabela"] = bool(b.get("tabela")); k["uclu"] = bool(b.get("uclu")); k["csv"] = True
            n += 1
        C.kaydet(obj["tarih"], h["id"], kosular, atlar, VERI)
    if n:
        print("TJK CSV'den koşu bilgisi işlendi:", n, "koşu")
    vhs_saat(obj)
    saat_duzelt(obj)
    ertele_uygula(obj)


def ertele_uygula(obj):
    """data/ertelenen.json: {"tarih": {"hipodrom": "yeni_tarih"}} - günü ertelenen hipodrom o günün programından çıkarılır (sonuç beklenmez, test sayımına girmez)."""
    try:
        d = json.load(open(os.path.join(VERI, "ertelenen.json"), encoding="utf-8")).get(obj["tarih"], {})
    except Exception:
        return
    if not d:
        return
    kalan = [h for h in obj["hipodromlar"] if h["id"] not in d]
    if len(kalan) != len(obj["hipodromlar"]):
        obj["ertelenen"] = d; obj["hipodromlar"] = kalan
        print("ertelenen hipodrom çıkarıldı:", d)


def _jn(j):
    return re.sub(r"\s*AP$", "", str(j or "")).strip()


def pist_uygula(obj):
    """data/pist_degisiklik.csv (tarih,hipodrom,kosu,pist,...): resmi pist türü değişen başlamamış koşuların bilgi metnini düzeltir ve
    o koşulardaki tüm atların model puanlarını (z, z2, z3, z4) yeni pist türüyle yeniden hesaplar (14 Ekim 2026: İstanbul çim -> sentetik)."""
    yol = os.path.join(VERI, "pist_degisiklik.csv")
    if not os.path.exists(yol):
        return
    t = obj["tarih"]; simdi = O.tr_simdi().strftime("%H:%M")
    degis = {}
    for l in open(yol, encoding="utf-8").read().split("\n")[1:]:
        p = l.split(",")
        if len(p) >= 4 and p[0] == t:
            degis[(p[1], int(p[2]))] = p[3].strip()
    hedef = set()
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            if k.get("yeniden_puan") and not k.get("sonuc") and not (k.get("saat") and simdi >= k["saat"]):
                hedef.add((h["id"], k["kosu"]))
            yp = degis.get((h["id"], k["kosu"]))
            if not yp or k.get("sonuc") or (k.get("saat") and simdi >= k["saat"]):
                continue
            b = k.get("bilgi") or ""
            m = re.search(r"(\d{3,4})\s*m?\s*(Kum|Çim|Sentetik)", b)
            if m and m.group(2) != yp:
                k["bilgi"] = b[:m.start(2)] + yp + b[m.end(2):]; hedef.add((h["id"], k["kosu"]))
    if not hedef:
        return
    try:
        cj = C.jokeyler(t) or {}
        satirlar = []
        for hid in {x[0] for x in hedef}:
            html = O.getir(O.prog_url(datetime.date.fromisoformat(t), hid))
            satirlar += O.parse_prog(html, t, hid) if html else []
        if not satirlar:
            print("pist değişikliği: program okunamadı, puanlar yenilenmedi"); return
        pr = pd.DataFrame(satirlar).dropna(subset=["no"]); pr["no"] = pr.no.astype(int)
        for i, r in pr.iterrows():
            j = cj.get((r.hipodrom, int(r.kosu), int(r.no)))
            if j:
                pr.at[i, "p_jokey"] = _jn(j); pr.at[i, "p_apranti"] = j.strip().endswith("AP")
        yeni = pr.rename(columns={"p_at": "at", "p_jokey": "jokey", "p_apranti": "apranti", "p_kilo": "kilo"})
        yeni["hnd"] = yeni.hk; yeni["kosmadi"] = False; yeni["ganyan"] = 10.0
        M = yukle_model(); A = GL.yukle()
        d = hazirla(oku("temiz")[lambda x: x.tarih < t], oku("program"), M, yeni)
        bz = d[d.yeni].set_index(["hipodrom", "kosu", "no"]).z.to_dict()
        bugun_m = {(h["id"], int(k["kosu"])): GL.MS.bilgiden(k.get("bilgi")) for h in obj["hipodromlar"] for k in h["kosular"] if GL.MS.bilgiden(k.get("bilgi"))}
        d2 = GL.MS.ekle(d, bugun_m) if A and "f_dp150_m" in A["feat"] else d
        bz2 = bz3 = bz4 = bz5 = bzj = {}
        if A:
            dy = d2[d2.yeni].copy(); dy["z2"] = GL.z2(dy, A); bz2 = dy.set_index(["hipodrom", "kosu", "no"]).z2.to_dict()
            bzj = {}
            try:
                from . import g1v3 as _V3; G3 = _V3.yukle()
                if G3:
                    dj = d2[d2.yeni].copy(); dj["zj"] = _V3.zj(dj, G3); bzj = dj.set_index(["hipodrom", "kosu", "no"]).zj.to_dict()
            except Exception as e:
                print("v3 zj hatası:", repr(e))
            AK = GL.yukle_k()
            if AK:
                dk = GL.kapi_ekle(d2); dk = dk[dk.yeni].copy(); dk["z3"] = GL.z2(dk, AK); bz3 = dk.set_index(["hipodrom", "kosu", "no"]).z3.to_dict()
            AS = GL.yukle_s()
            if AS:
                ds = d2[d2.yeni].copy(); ds["z4"] = GL.z2(ds, AS); bz4 = ds.set_index(["hipodrom", "kosu", "no"]).z4.to_dict()
            AF = GL.yukle_f()
            if AF:
                df_ = GL.fk_ekle(d2); df_ = df_[df_.yeni].copy(); df_["z5"] = GL.z2(df_, AF); bz5 = df_.set_index(["hipodrom", "kosu", "no"]).z5.to_dict()
        n = 0
        for h in obj["hipodromlar"]:
            for k in h["kosular"]:
                if (h["id"], k["kosu"]) not in hedef:
                    continue
                for a in k["atlar"]:
                    key = (h["id"], k["kosu"], a["no"])
                    for ad, bzx in (("z", bz), ("z2", bz2), ("z3", bz3), ("z4", bz4), ("z5", bz5), ("zj", bzj)):
                        if key in bzx and ad in a:
                            a[ad] = round(float(bzx[key]), 4)
                    a.pop("z6", None)                   # G1-S puanı (z6) yeni özelliklerle yeniden hesaplanır
                k.pop("yeniden_puan", None)
                n += 1
        print("pist değişikliği işlendi: koşu", n, sorted(hedef))
    except Exception as e:
        print("pist değişikliği hatası:", repr(e))


def s_doldur(obj):
    """Jason-S (14 Ekim 2026): sabah Jason-S'siz kurulmuş günün başlamamış koşularına z4 ve w0_s/lp2_s/a_s ekler (bir kez)."""
    if obj.get("w0_s") is not None:
        return
    AS = GL.yukle_s(); A = GL.yukle()
    if not AS or not A:
        return
    t = obj["tarih"]; simdi = O.tr_simdi().strftime("%H:%M")
    try:
        cj = C.jokeyler(t) or {}
        satirlar = []
        for h in obj["hipodromlar"]:
            html = O.getir(O.prog_url(datetime.date.fromisoformat(t), h["id"]))
            satirlar += O.parse_prog(html, t, h["id"]) if html else []
        if not satirlar:
            print("Jason-S doldurma: program okunamadı"); return
        pr = pd.DataFrame(satirlar).dropna(subset=["no"]); pr["no"] = pr.no.astype(int)
        for i, r in pr.iterrows():
            j = cj.get((r.hipodrom, int(r.kosu), int(r.no)))
            if j:
                pr.at[i, "p_jokey"] = _jn(j); pr.at[i, "p_apranti"] = j.strip().endswith("AP")
        yeni = pr.rename(columns={"p_at": "at", "p_jokey": "jokey", "p_apranti": "apranti", "p_kilo": "kilo"})
        yeni["hnd"] = yeni.hk; yeni["kosmadi"] = False; yeni["ganyan"] = 10.0
        M = yukle_model()
        d = hazirla(oku("temiz")[lambda x: x.tarih < t], oku("program"), M, yeni)
        bugun_m = {(h["id"], int(k["kosu"])): GL.MS.bilgiden(k.get("bilgi")) for h in obj["hipodromlar"] for k in h["kosular"] if GL.MS.bilgiden(k.get("bilgi"))}
        d2 = GL.MS.ekle(d, bugun_m) if "f_dp150_m" in A["feat"] else d
        ds = d2[d2.yeni].copy(); ds["z4"] = GL.z2(ds, AS)
        bz4 = ds.set_index(["hipodrom", "kosu", "no"]).z4.to_dict()
        n = 0
        for h in obj["hipodromlar"]:
            for k in h["kosular"]:
                if k.get("sonuc") or (k.get("saat") and simdi >= k["saat"]):
                    continue
                for a in k["atlar"]:
                    key = (h["id"], k["kosu"], a["no"])
                    if key in bz4:
                        a["z4"] = round(float(bz4[key]), 4)
                n += 1
        obj["w0_s"] = float(AS["w"][0]); obj["lp2_s"] = float(AS.get("lp2_a", 0.0)); obj["a_s"] = [round(float(x), 4) for x in AS["a"]]
        print("Jason-S doldurma: koşu", n)
    except Exception as e:
        print("Jason-S doldurma hatası:", repr(e))


def jokey_uygula(obj):
    """Yarış başlamadan önce yüklenen güncel TJK CSV'sinde jokey değişmişse: atın jokeyini ve model puanlarını (z, z2, z3) yeniler,
    değişikliği data/jokey_degisiklik/<gün>.csv'ye yazar. Başlamış/sonuçlanmış koşulara dokunmaz."""
    t = obj["tarih"]
    cj = C.jokeyler(t)
    if not cj:
        return
    simdi = O.tr_simdi().strftime("%H:%M")
    deg = {}
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            if k.get("sonuc") or (k.get("saat") and simdi >= k["saat"]):
                continue
            for a in k["atlar"]:
                j = cj.get((h["id"], k["kosu"], a["no"]))
                if j and _jn(j) != _jn(a["jokey"]):
                    deg.setdefault(h["id"], []).append((k["kosu"], a, j))
    if not deg:
        return
    # 1) kayıt
    yol = os.path.join(VERI, "jokey_degisiklik", t + ".csv")
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    var = set()
    if os.path.exists(yol):
        for l in open(yol, encoding="utf-8").read().split("\n")[1:]:
            p = l.split(",")
            if len(p) > 6:
                var.add((p[1], p[2], p[3], p[5], p[6]))
    yeni_sat = []
    for hid, L in deg.items():
        for kn, a, j in L:
            if (hid, str(kn), str(a["no"]), a["jokey"], _jn(j)) not in var:
                yeni_sat.append(f"{t},{hid},{kn},{a['no']},{a['at']},{a['jokey']},{_jn(j)},otomatik {simdi},model puani yenilendi")
    if yeni_sat:
        yeni_dosya = not os.path.exists(yol)
        with open(yol, "a", encoding="utf-8") as fh:
            if yeni_dosya:
                fh.write("tarih,hipodrom,kosu,no,at,eski_jokey,yeni_jokey,kaynak,not\n")
            fh.write("\n".join(yeni_sat) + "\n")
    # 2) programı yeniden çek, tüm jokeyleri CSV'ye göre yaz, z'leri yeniden hesapla
    try:
        satirlar = []
        for hid in deg:
            html = O.getir(O.prog_url(datetime.date.fromisoformat(t), hid))
            satirlar += O.parse_prog(html, t, hid) if html else []
        if not satirlar:
            print("jokey değişikliği: program yeniden okunamadı, puanlar yenilenmedi (jokey adı yazıldı, puan_eski işaretlendi)")
            for h in obj["hipodromlar"]:
                if h["id"] not in deg:
                    continue
                for k in h["kosular"]:
                    if k.get("sonuc") or (k.get("saat") and simdi >= k["saat"]):
                        continue
                    for a in k["atlar"]:
                        j = cj.get((h["id"], k["kosu"], a["no"]))
                        if j and _jn(j) != _jn(a["jokey"]):
                            a["jokey"] = _jn(j); a["apr"] = j.strip().endswith("AP"); a["puan_eski"] = True
            return
        pr = pd.DataFrame(satirlar).dropna(subset=["no"]); pr["no"] = pr.no.astype(int)
        for i, r in pr.iterrows():
            j = cj.get((r.hipodrom, int(r.kosu), int(r.no)))
            if j:
                pr.at[i, "p_jokey"] = _jn(j); pr.at[i, "p_apranti"] = j.strip().endswith("AP")
        yeni = pr.rename(columns={"p_at": "at", "p_jokey": "jokey", "p_apranti": "apranti", "p_kilo": "kilo"})
        yeni["hnd"] = yeni.hk; yeni["kosmadi"] = False; yeni["ganyan"] = 10.0
        M = yukle_model()
        temiz, prog = oku("temiz"), oku("program")
        d = hazirla(temiz[temiz.tarih < t], prog, M, yeni)
        bz = d[d.yeni].set_index(["hipodrom", "kosu", "no"]).z.to_dict()
        bz2, bz3, bz4, bz5 = {}, {}, {}, {}
        A = GL.yukle()
        if A:
            bugun_m = {(h["id"], int(k["kosu"])): GL.MS.bilgiden(k.get("bilgi")) for h in obj["hipodromlar"] for k in h["kosular"] if GL.MS.bilgiden(k.get("bilgi"))}
            d2 = GL.MS.ekle(d, bugun_m) if "f_dp150_m" in A["feat"] else d
            dy = d2[d2.yeni].copy(); dy["z2"] = GL.z2(dy, A)
            bz2 = dy.set_index(["hipodrom", "kosu", "no"]).z2.to_dict()
            AK = GL.yukle_k()
            if AK:
                dk = GL.kapi_ekle(d2); dk = dk[dk.yeni].copy(); dk["z3"] = GL.z2(dk, AK)
                bz3 = dk.set_index(["hipodrom", "kosu", "no"]).z3.to_dict()
            AS = GL.yukle_s()
            if AS:
                ds = d2[d2.yeni].copy(); ds["z4"] = GL.z2(ds, AS)
                bz4 = ds.set_index(["hipodrom", "kosu", "no"]).z4.to_dict()
            AF = GL.yukle_f()
            if AF:
                df_ = GL.fk_ekle(d2); df_ = df_[df_.yeni].copy(); df_["z5"] = GL.z2(df_, AF)
                bz5 = df_.set_index(["hipodrom", "kosu", "no"]).z5.to_dict()
        n = 0
        for h in obj["hipodromlar"]:
            if h["id"] not in deg:
                continue
            for k in h["kosular"]:
                if k.get("sonuc") or (k.get("saat") and simdi >= k["saat"]):
                    continue
                for a in k["atlar"]:
                    key = (h["id"], k["kosu"], a["no"])
                    j = cj.get(key)
                    if not j or _jn(j) == _jn(a["jokey"]):
                        continue                     # yalnız jokeyi değişen atların puanı yenilenir; diğerleri dondurulmuş sabah değerinde kalır
                    a["jokey"] = _jn(j); a["apr"] = j.strip().endswith("AP")
                    if key in bz:
                        a["z"] = round(float(bz[key]), 4)
                    if key in bz2 and "z2" in a:
                        a["z2"] = round(float(bz2[key]), 4)
                    if key in bz3 and "z3" in a:
                        a["z3"] = round(float(bz3[key]), 4)
                    if key in bz4 and "z4" in a:
                        a["z4"] = round(float(bz4[key]), 4)
                    if key in bz5 and "z5" in a:
                        a["z5"] = round(float(bz5[key]), 4)
                n += 1
        print("jokey değişikliği işlendi:", {h: len(L) for h, L in deg.items()}, "| koşu yenilendi:", n)
    except Exception as e:
        print("jokey değişikliği işlenemedi:", repr(e))


def csv_agf_uygula(obj, csv_agf):
    """AGF tablosu siteden alınamadıysa TJK program CSV'sindeki AGF yüzdesi (ilk görülen = sabah değeri) atlara yazılır; siteden gelen değere dokunmaz."""
    if not csv_agf:
        return
    n = 0
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            for a in k["atlar"]:
                v = csv_agf.get((h["id"], k["kosu"], a["no"]))
                if v is not None and a.get("agf") is None:
                    a["agf"] = v; a["agf_a1"] = v; a["agf0"] = v; n += 1
    if n:
        print("AGF TJK CSV'sinden eklendi:", n, "at")


def agf_ekle(obj):
    html = O.getir(O.BASE + "/agf-tablosu")
    if not html:
        try:
            from . import atyapi
            atyapi.agf_uygula(obj, O.tr_simdi().strftime("%H:%M"))     # agftablosu engelli: AGF atyarisi API'sinden
        except Exception as e:
            print("AGF API hatası:", repr(e))
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
    try:
        from . import muhtemeller as MUH
        MUH.topla(t.isoformat(), pencere_dk=30, yalniz_yurtdisi=False)      # canlı muhtemel ganyan (yurtiçi dahil) -> geç kupon girdisi
        print("geç kupon:", BS.gec_guncelle(c))
    except Exception as e:
        print("geç kupon hatası:", repr(e))
    try:
        from . import piyasa_zaman as PZ
        print("piyasa_zaman satırı:", PZ.topla(t.isoformat()))
    except Exception as e:
        print("piyasa_zaman hatası:", repr(e))


def kosmaz_isle(obj):
    """SİB program sayfası yapıştırmalarından (data/sib/<gün>-<hip>.csv, gerçek at numarası) koşmaz atları işaretler."""
    n = 0
    elle = set()
    ky = os.path.join(VERI, "kosmaz", obj["tarih"] + ".csv")
    if os.path.exists(ky):
        e = pd.read_csv(ky)
        elle = {(str(r.hipodrom), int(r.kosu), int(r.no)) for r in e.itertuples()}
    try:
        elle |= C.kosmazlar(obj["tarih"])          # TJK CSV'sindeki "(Koşmaz)" işaretleri
    except Exception as ex:
        print("CSV koşmaz hatası:", repr(ex))
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


def muh_sonuc_df(t, hid):
    """data/muh/<gün>.json'dan (vhs.tjk.org) bir hipodromun biten koşuları: kosu, no, sira, ganyan (resmî kapanış)."""
    yol = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "muh", t.isoformat() + ".json")
    if not os.path.exists(yol):
        return pd.DataFrame()
    D = json.load(open(yol, encoding="utf-8"))
    satir = []
    for key, v in D.items():
        ad = re.sub(r"[^a-z0-9]", "", str(v.get("hipodrom", "")).lower().translate(str.maketrans("ıİşŞğĞüÜöÖçÇ", "iissgguuoocc")))
        if not (ad == hid or str(v.get("slug", "")).startswith(hid)) or not v.get("sonuc"):
            continue
        so = v["sonuc"]
        for no, sira in so["sira"].items():
            g = so["ganyan"].get(no)
            if g:
                satir.append({"tarih": t.isoformat(), "hipodrom": hid, "kosu": int(v["kosu"]), "sira": sira, "no": int(no), "ganyan": float(g), "kosmadi": False})
    return pd.DataFrame(satir)


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
        s = pd.DataFrame(O.parse_sonuc(html, t.isoformat(), h["id"])) if html else pd.DataFrame()
        # 18 Ekim 2026: vhs.tjk.org/muhtemeller yedeği (resmî sıra + kapanış ganyanı); agftablosu eksik/gecikmeliyse kullanılır
        try:
            m = muh_sonuc_df(t, h["id"])
            if not m.empty:
                if s.empty:
                    s = m
                else:
                    tam = set(s[s.ganyan.notna() & (s.ganyan > 0) & s.sira.notna()].kosu)
                    s = pd.concat([s, m[~m.kosu.isin(tam)]], ignore_index=True)
        except Exception as e:
            print("muh yedek hatası:", repr(e))
        # 23 Ekim 2026: atyarisi.com resmî sonuç API'si (agftablosu engelli; CSV yüklemeye gerek kalmasın) - eksik koşuları tamamlar
        try:
            from . import atyapi
            m = atyapi.sonuc_df(t, h["id"])
            if not m.empty:
                if s.empty:
                    s = m
                else:
                    tam = set(s[s.ganyan.notna() & (s.ganyan > 0) & s.sira.notna()].kosu)
                    s = pd.concat([s, m[~m.kosu.isin(tam)]], ignore_index=True)
        except Exception as e:
            print("atyarisi sonuç hatası:", repr(e))
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
            if obj.get("w0_k") is not None and r.z2.notna().all():
                z3 = {a["no"]: a.get("z3") for a in k["atlar"]}; r["z3"] = r.no.map(z3)
                if r.z3.notna().all():
                    r["p_k"] = model_olasilik(r.p_piyasa.values, r.z3.values, obj["w0_k"], obj.get("lp2_k", 0.0))
            if obj.get("w0_s") is not None and r.z2.notna().all():
                z4 = {a["no"]: a.get("z4") for a in k["atlar"]}; r["z4"] = r.no.map(z4)
                if r.z4.notna().all():
                    r["p_s"] = model_olasilik(r.p_piyasa.values, r.z4.values, obj["w0_s"], obj.get("lp2_s", 0.0))
            try:                                                  # Benter-G1 gölge modeli (24 Ekim 2026)
                from . import g1 as _G1
                pg = _G1.tahmin(r, t)
                if pg is not None:
                    r["p_g1"] = pg
            except Exception as e:
                print("g1 hatası:", repr(e))
            k["sonuc"] = {str(int(x.no)): {"sira": None if pd.isna(x.sira) else int(x.sira),
                                           "g": float(x.ganyan), "pp": round(float(x.p_piyasa), 5),
                                           "pm": round(float(x.p_model), 5),
                                           **({"pm2": round(float(x.p_aday), 5)} if "p_aday" in r.columns else {}),
                                           **({"pm3": round(float(x.p_k), 5)} if "p_k" in r.columns else {}),
                                           **({"pm4": round(float(x.p_s), 5)} if "p_s" in r.columns else {}),
                                           **({"pm5": round(float(x.p_g1), 5)} if "p_g1" in r.columns else {})} for x in r.itertuples()}
            yeni_sonuc += 1
    obj["guncelleme"] = simdi.strftime("%H:%M")
    return yeni_sonuc


def canli(t):
    yol = gun_yolu(t)
    obj = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else None
    if obj is not None:
        var = {h["id"] for h in obj.get("hipodromlar", [])}
        try:
            eksik = [h for h in C.gunun(t.isoformat()) if h not in var]
        except Exception:
            eksik = []
        if not var or eksik:                               # program boş ya da yeni yüklenen CSV'nin hipodromu programda yok -> programı yeniden kur
            print("program yeniden kuruluyor; eksik hipodrom:", eksik or "(hepsi)")
            obj = sabah(t)
    else:
        obj = sabah(t)
    if not obj["hipodromlar"]:
        return
    son = max((k.get("saat") or "23:59") for h in obj["hipodromlar"] for k in h["kosular"])
    if O.tr_simdi().strftime("%H:%M") < son:
        agf_ekle(obj)
        try:
            agf_zaman_yaz(obj)
        except Exception as e:
            print("agf_zaman hatası:", repr(e))
    try:
        from . import piyasa_zaman as PZ              # sabit ihtimalli + muhtemel oran zaman serisi (24 Ekim 2026)
        PZ.topla(t.isoformat())
    except Exception as e:
        print("piyasa_zaman hatası:", repr(e))
    csv_uygula(obj)
    jokey_uygula(obj)
    s_doldur(obj)
    pist_uygula(obj)
    kosmaz_isle(obj)
    try:
        from . import muhtemeller as MUH
        MUH.topla(t.isoformat(), yalniz_yurtdisi=False)       # vhs.tjk.org: resmî sıra + ganyan (agftablosu gecikirse yedek)
    except Exception as e:
        print("muhtemeller hatası:", repr(e))
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
        UA.guncelle(obj)
    except Exception as e:
        print("3 atlı ikili hatası:", repr(e))
    try:
        PL.guncelle(obj)
    except Exception as e:
        print("plase hatası:", repr(e))
    try:
        from . import atyapi as _AY, tuyo_egz as _TE
        _AY.odeme_yaz(obj['tarih'])          # atyarisi ikramiyeleri (CSV yüklenmese de)
    except Exception as e:
        print('atyarisi ikramiye hatası:', repr(e))
    try:
        TY.guncelle(obj)
        _TE.guncelle()
    except Exception as e:
        print("tuyo hatası:", repr(e))
    try:
        BS.guncelle(obj)
    except Exception as e:
        print("besli hatası:", repr(e))
    try:
        TB.guncelle(obj)
    except Exception as e:
        print("tabela hatası:", repr(e))
    try:
        S3.guncelle(obj)
    except Exception as e:
        print("sıralı 3'lü kolon kuponu hatası:", repr(e))
    try:
        ES.guncelle(obj)
    except Exception as e:
        print("esnek hatası:", repr(e))
    try:
        DG.guncelle(obj)
    except Exception as e:
        print("değer hatası:", repr(e))
    try:
        KB.guncelle(obj)
    except Exception as e:
        print("kombine hatası:", repr(e))
    try:
        UY.hesapla()
    except Exception as e:
        print("uyandır hatası:", repr(e))
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
                UA.guncelle(obj)
            except Exception as e:
                print("3 atlı ikili hatası:", repr(e))
            try:
                PL.guncelle(obj)
            except Exception as e:
                print("plase hatası:", repr(e))
            try:
                from . import atyapi as _AY, tuyo_egz as _TE
                _AY.odeme_yaz(obj['tarih'])          # atyarisi ikramiyeleri (CSV yüklenmese de)
            except Exception as e:
                print('atyarisi ikramiye hatası:', repr(e))
            try:
                TY.guncelle(obj)
                _TE.guncelle()
            except Exception as e:
                print("tuyo hatası:", repr(e))
            try:
                BS.guncelle(obj)
            except Exception as e:
                print("besli hatası:", repr(e))
            try:
                TB.guncelle(obj)
            except Exception as e:
                print("tabela hatası:", repr(e))
            try:
                ES.guncelle(obj)
            except Exception as e:
                print("esnek hatası:", repr(e))
            try:
                DG.guncelle(obj)
            except Exception as e:
                print("değer hatası:", repr(e))
            try:
                KB.guncelle(obj)
            except Exception as e:
                print("kombine hatası:", repr(e))
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
        try:
            GL.egit_k()                             # ikinci gölge: Jason-K (Jason + kapı yanlılığı)
        except Exception as e:
            print("Jason-K eğitim hatası:", repr(e))
        try:
            GL.egit_s()                             # üçüncü gölge: Jason-S (ilk-5 sırasıyla eğitilmiş)
        except Exception as e:
            print("Jason-S eğitim hatası:", repr(e))
        try:
            GL.egit_f()                             # dördüncü gölge: Jason-F (Jason + handikap fazla kilo)
        except Exception as e:
            print("Jason-F eğitim hatası:", repr(e))
        print("gölge skor:", GL.skor())
    except Exception as e:
        print("gölge model hatası:", repr(e))
    try:
        from . import g1 as _G1                    # Benter-G1: katsayıları her gece tüm geçmişle yenile (8 sn)
        _G1.egit()
        _G1.egit3()
        _G1.egit_galop()
        from . import g1v3 as _V3                  # G1-S v3: Jason özellikleri ortak eğitim (~100 sn); başarısız olursa eski v2 dosyaları ve önceki v3 kalır
        _V3.egit()
    except Exception as e:
        print("g1 eğitim hatası:", repr(e))
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
        try:                                   # yabancı koşu kaydı (yalnız kayıt; hata gece işini durdurmaz)
            from . import yabanci as YB
            YB.calistir()
        except Exception as ex:
            print("yabancı kayıt atlandı:", ex)
    elif mod == "yabanci":
        if arg: os.environ["YABANCI_EN_COK"] = arg[0]
        from . import yabanci as YB
        YB.calistir()
    elif mod == "abdgecmis":
        from . import yabanci as YB
        YB.abd_gecmis(datetime.date.fromisoformat(arg[0]), datetime.date.fromisoformat(arg[1]))
    elif mod == "abdprogram":
        from . import yabanci as YB
        YB.abd_program(datetime.date.fromisoformat(arg[0]), datetime.date.fromisoformat(arg[1]))
    elif mod == "slprobe":
        from . import yabanci as YB
        YB.sl_probe(*arg)
    elif mod == "slkosu":
        from . import yabanci as YB
        YB.sl_kosu_probe(*[a.replace("|", "/") for a in arg])
    elif mod == "sltopla":
        from . import yabanci as YB
        YB.sl_topla(datetime.date.fromisoformat(arg[0]), datetime.date.fromisoformat(arg[1]))
    elif mod == "abdcanli":
        from . import yabanci as YB
        YB.abd_canli()
    elif mod == "sayfaprobe":
        from . import yabanci as YB
        YB.sayfa_probe()
    elif mod == "yabanciham":
        from . import yabanci as YB
        YB.ham_ornek()
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
        try:
            from . import oynadim as OD
            OD.yaz()
        except Exception as ex:
            print("oynadim özeti atlandı:", ex)


if __name__ == "__main__":
    main()
