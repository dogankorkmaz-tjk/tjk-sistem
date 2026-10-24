"""Egzotik bahis kâğıt testi (sıralı ikili, ikili, üçlü) - KURALLAR DONDURULMUŞTUR (10 Ekim 2026).

Fikir: model/AGF olasılık oranı >= 1,15 olan VE piyasa (AGF) açısından yeterince olası kombinasyonları sanal olarak "alır".
Olasılıklar Harville + TJK verisinden kestirilmiş düzeltme (gama, delta) ile. Kombinasyon başına birim fiyat TJK'nın.
Başlangıç kuralı Haziran-Ekim 2026 geçmiş verisinden (126 gün) çıkarıldı; bu dosya ilerisi için sınav.
Değerlendirme yalnızca o koşunun sonuç CSV'si (ödeme satırları) yüklendiğinde yapılır.
Çıktılar: data/egzotik/<tarih>.json, docs/data/egzotik.json
"""
import os, json, glob, math, itertools
import pandas as pd

VERI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SITE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "data")

GAMA, DELTA = 0.867, 0.735                      # 20.649 koşudan kestirilen Harville düzeltmesi (2. ve 3. bitiş)
ORAN = 1.15                                     # model olasılığı / AGF olasılığı en az bu kadar
ESIK = {"SIRALI İKİLİ": 0.00306, "İKİLİ": 0.00596, "ÜÇLÜ BAHİS": 0.00141}   # AGF tabanlı kombinasyon olasılığı alt sınırı
BIRIM = {"SIRALI İKİLİ": 1.0, "İKİLİ": 1.0, "ÜÇLÜ BAHİS": 2.0}
VARYANT = {"Jason-1.25": 1.25, "Jason-1.50": 1.50}          # 12 Ekim 2026 ön-kayıt: sonuçlar görülmeden eklendi; ana kural (ORAN) dokunulmadı
IK_KES = (395000, 545000)                       # birinci ikramiye üçte birleri (2025-26 koşularından); yalnızca İZLEME bölünmesi, kural değil
K = {"SIRALI İKİLİ": 2, "İKİLİ": 2, "ÜÇLÜ BAHİS": 3}


def ik_dilim(ik):
    try:
        ik = float(ik)
    except (TypeError, ValueError):
        return None
    return "düşük" if ik < IK_KES[0] else ("orta" if ik <= IK_KES[1] else "yüksek")


def _kombolar(p, k, gama=None, delta=None):
    gama = GAMA if gama is None else gama; delta = DELTA if delta is None else delta
    q2 = {n: v ** gama for n, v in p.items()}; q3 = {n: v ** delta for n, v in p.items()}
    s2, s3 = sum(q2.values()), sum(q3.values()); out = {}
    for c in itertools.permutations(p, k):
        pr = p[c[0]]
        if k >= 2:
            pr *= q2[c[1]] / (s2 - q2[c[0]])
        if k >= 3:
            pr *= q3[c[2]] / (s3 - q3[c[0]] - q3[c[1]])
        out[c] = pr
    return out


def _secim(atlar, w0, zk="z", lp2=0.0, esik_oran=ORAN, gd=None):
    """atlar: koşu atları (agf, z). Her tür için seçilen kombinasyonlar: {tur: ["a-b", ...]}. zk: form puanı alanı (Bolton "z", Jason "z2")."""
    at = [a for a in atlar if a.get("agf") and not a.get("kosmaz")]
    if len(at) < 5 or (zk != "z" and any(a.get(zk) is None for a in at)):
        return None
    tot = sum(a["agf"] for a in at)
    pk = {a["no"]: a["agf"] / tot for a in at}
    ham = {a["no"]: math.exp(w0 * math.log(max(pk[a["no"]], 1e-6)) + lp2 * math.log(max(pk[a["no"]], 1e-6)) ** 2 + (a.get(zk) or 0.0)) for a in at}
    Z = sum(ham.values()); pm = {n: v / Z for n, v in ham.items()}
    out = {}; oran = {}
    for tur, k in K.items():
        A, B = _kombolar(pk, k), (_kombolar(pm, k, *gd) if gd else _kombolar(pm, k))
        if tur == "İKİLİ":
            A2, B2 = {}, {}
            for c, v in A.items():
                A2[tuple(sorted(c))] = A2.get(tuple(sorted(c)), 0) + v
            for c, v in B.items():
                B2[tuple(sorted(c))] = B2.get(tuple(sorted(c)), 0) + v
            A, B = A2, B2
        sec = [c for c in A if A[c] >= ESIK[tur] and B[c] / A[c] >= esik_oran]
        out[tur] = ["-".join(str(int(n)) for n in c) for c in sorted(sec)]
        oran[tur] = {"-".join(str(int(n)) for n in c): [round(B[c] / A[c], 2), round(B[c], 4)] for c in sorted(sec)}   # [model/piyasa oranı, model olasılığı]
    out["_oran"] = oran
    return out


def _odeme_oku(tarih):
    try:
        od = pd.read_csv(os.path.join(VERI, "odeme", tarih[:7] + ".csv.gz"))
    except Exception:
        return pd.DataFrame()
    od = od[(od.tarih == tarih) & od.tur.isin(list(K))]
    return od


def _uclu_suz(s, k):
    """Üçlü bahis oynanmayan koşuda (program CSV'sinde yok ya da CSV yok) üçlü seçimi boşaltılır (14 Ekim 2026)."""
    if s is not None and k.get("uclu") is not True:
        s["ÜÇLÜ BAHİS"] = []
        if s.get("_oran"):
            s["_oran"]["ÜÇLÜ BAHİS"] = {}
    return s


def guncelle(obj):
    tarih = obj["tarih"]
    yol = os.path.join(VERI, "egzotik", tarih + ".json")
    kay = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    simdi = None
    try:
        from . import ortak as O
        simdi = O.tr_simdi().strftime("%H:%M")
    except Exception:
        pass
    od = None
    modeller = [("", "z", obj.get("w0", 1.0), "Bolton", 0.0, ORAN)]
    if obj.get("w0_aday") is not None:
        modeller.append(("J|", "z2", obj["w0_aday"], "Jason", obj.get("lp2_aday", 0.0), ORAN))      # Jason: aynı kural, ayrı sayaç (gölge kâğıt testi)
        for ad_v, o_v in VARYANT.items():                                                         # ön-kayıtlı varyantlar (12 Ekim 2026): yalnızca eşik farklı, ana kural değişmedi
            modeller.append((ad_v.replace("Jason-", "J") .replace(".", "") + "|", "z2", obj["w0_aday"], ad_v, obj.get("lp2_aday", 0.0), o_v))
    if obj.get("w0_s") is not None:                                                            # Jason-S (14 Ekim 2026): aynı dondurulmuş kural, ayrı gölge sayaç
        modeller.append(("JS|", "z4", obj["w0_s"], "Jason-S", obj.get("lp2_s", 0.0), ORAN))
    GD = {}
    try:                                                                                       # G1-S: önce z6_doldur (obj'ye w0_g1/a_g1 yazar: v3 varsa v3), sonra aynı katsayılarla seçim
        from . import g1 as _G1
        _G1.z6_doldur(obj)
        if obj.get("w0_g1") is not None and obj.get("a_g1"):
            modeller.append(("G1|", "z6", obj["w0_g1"], "G1-S", 0.0, ORAN)); GD["G1|"] = (obj["a_g1"][1], obj["a_g1"][2])
    except Exception as e:
        print("G1-S hatası:", repr(e))
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            basladi = bool(k.get("sonuc")) or (simdi is not None and k.get("saat") and simdi >= k["saat"] and obj.get("gecmis") is not True)
            for onek, zk, w0, ad_m, lp2, or_m in modeller:
                anahtar = f"{onek}{h['id']}|{k['kosu']}"
                c = kay.get(anahtar)
                if c is None and not basladi:
                    s = _uclu_suz(_secim(k.get("atlar", []), w0, zk, lp2, or_m, GD.get(onek)), k)
                    if s is not None:
                        ora = s.pop("_oran", None)
                        kay[anahtar] = c = {"model": ad_m, "hipodrom": h["id"], "kosu": k["kosu"], "saat": k.get("saat"), "uretim": simdi, "dondu": False, "secim": s, "oran": ora,
                                            "ad": {str(a["no"]): a.get("at") for a in k.get("atlar", [])}}
                elif c is not None and not c.get("dondu"):
                    if basladi:
                        c["dondu"] = True
                    else:
                        s = _uclu_suz(_secim(k.get("atlar", []), w0, zk, lp2, or_m, GD.get(onek)), k)
                        if s is not None:
                            c["oran"] = s.pop("_oran", None)
                            c["secim"] = s; c["uretim"] = simdi
                if c is not None and c.get("ik") is None and k.get("ikramiye"):
                    c["ik"] = k.get("ikramiye")                                   # ikramiye bölünmesi için (yalnızca izleme)
                # değerlendirme
                if c and "sonuc" not in c and k.get("sonuc") and c.get("dondu", True):
                    if od is None:
                        od = _odeme_oku(tarih)
                    x = od[(od.hipodrom == h["id"]) & (od.kosu == k["kosu"])] if len(od) else od
                    if len(x):
                        res = {}
                        for tur in K:
                            r = x[x.tur == tur]
                            if not len(r):
                                continue                                  # bu koşuda bu bahis türü oynanmamış
                            sec = set(c["secim"].get(tur, []))
                            kaz = 0.0; isabet = False
                            for q in r.itertuples():
                                kk = [int(z) for z in str(q.kombo).split("/")]
                                key = "-".join(str(n) for n in (sorted(kk) if tur == "İKİLİ" else kk))
                                if key in sec:
                                    kaz += float(q.tutar); isabet = True
                            res[tur] = {"kombo": len(sec), "bedel": round(len(sec) * BIRIM[tur], 2), "kazanc": round(kaz, 2), "isabet": isabet}
                        c["sonuc"] = res
    if kay:
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def h_ad(c):
    return c.get("hipodrom_ad") or c["hipodrom"]


def ozet_yaz(tarih):
    def bos():
        return {t: {"tur": t, "koşu": 0, "harcama": 0.0, "kazanc": 0.0, "isabetli_kosu": 0, "kosuda_secim": 0} for t in K}
    tops = {"Bolton": bos(), "Jason": bos(), "Jason-S": bos(), "G1-S": bos(), **{v: bos() for v in VARYANT}}
    ikd = {d: bos() for d in ("düşük", "orta", "yüksek")}
    gun = []
    for y in sorted(glob.glob(os.path.join(VERI, "egzotik", "*.json"))):
        for c in json.load(open(y, encoding="utf-8")).values():
            m = c.get("model", "Bolton")
            if os.path.basename(y)[:10] == tarih:
                gun.append({"model": m, "hipodrom": c["hipodrom"], "kosu": c["kosu"], "atlar": c.get("ad", {}), "saat": c.get("saat"), "dondu": c.get("dondu"),
                            "ad": h_ad(c), "secim": c["secim"], "oran": c.get("oran"), "kombo": {t: len(v) for t, v in c["secim"].items()}, "sonuc": c.get("sonuc")})
            for t, r in (c.get("sonuc") or {}).items():
                a = tops[m][t]; a["koşu"] += 1
                if r["kombo"]:
                    a["kosuda_secim"] += 1
                a["harcama"] += r["bedel"]; a["kazanc"] += r["kazanc"]; a["isabetli_kosu"] += int(r["isabet"])
                d_ = ik_dilim(c.get("ik")) if m == "Bolton" else None
                if d_:
                    b_ = ikd[d_][t]; b_["koşu"] += 1; b_["harcama"] += r["bedel"]; b_["kazanc"] += r["kazanc"]; b_["isabetli_kosu"] += int(r["isabet"])
                    b_["kosuda_secim"] += int(bool(r["kombo"]))
    for top in list(tops.values()) + list(ikd.values()):
        for a in top.values():
            a["geri_donus"] = round(a["kazanc"] / a["harcama"], 3) if a["harcama"] else None
            a["harcama"] = round(a["harcama"], 2); a["kazanc"] = round(a["kazanc"], 2)
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "kural": {"gama": GAMA, "delta": DELTA, "oran": ORAN, "esik": ESIK, "birim": BIRIM},
               "bugun": gun, "toplam": list(tops["Bolton"].values()), "toplam_jason": list(tops["Jason"].values()), "toplam_jason_s": list(tops["Jason-S"].values()), "toplam_g1s": list(tops["G1-S"].values()), "toplam_varyant": {v: list(tops[v].values()) for v in VARYANT},
               "toplam_ikramiye": {d: list(v.values()) for d, v in ikd.items()}, "ikramiye_kesim": list(IK_KES)},
              open(os.path.join(SITE, "egzotik.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    try:
        from . import kanit as KT                 # kanıt sayacı: yalnızca ölçer, hiçbir kuralı değiştirmez
        KT.yaz(tarih)
    except Exception as e:
        print("kanıt sayacı hatası:", repr(e))
