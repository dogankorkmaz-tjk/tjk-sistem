"""Kanıt sayacı (14 Ekim 2026) - kâğıt testlerin sonucuna NE KADAR güvenilebileceğini gösterir.

Bu modül hiçbir kuralı, modeli, kuponu ya da eşiği DEĞİŞTİRMEZ; yalnızca mevcut kayıtları okuyup ölçer.

İki şey hesaplar:
1) Kanıt sayacı: her (model, bahis türü) için koşu sayısı, geri dönüş, güven aralığı ve
   "+%5 avantajı ayırt etmek için kaç koşu daha lazım" tahmini.
   Birim = koşu. Koşu başına oranlı tahminci (ratio estimator): R = Σkazanç / Σharcama,
   artıklar e_i = kazanç_i - R*harcama_i, TL başına oynaklık = sd(e) / ort(harcama).
   Gerekli koşu = ((1,96 + 0,84) * oynaklık / hedef)^2  (%5 anlamlılık, %80 güç).
2) Varyant sayacı: sitede kaç farklı kural izleniyor (en az). Ne kadar çok kural denenirse
   biri tesadüfen iyi görünür; güven aralığı bu yüzden Bonferroni ile genişletilir:
   z_düzeltilmiş = Φ^-1(1 - 0,05 / (2*m)).

3) e-değer (15 Ekim 2026): her gün bakılabilen ("anytime-valid") kanıt. Koşu başına getiri X = kazanç/harcama;
   H0: beklenen getiri ≤ 1. Bahis martingali W = ort_λ Π(1 + λ(X-1)), λ ∈ LAMBDA (sabit ızgara, X ≥ 0 olduğundan W > 0).
   H0 altında P(W hiç ≥ 1/α olur) ≤ α (Ville eşitsizliği), yani her gün bakmak sonucu bozmaz. Eşik çoklu kurala göre m/0,05.

Çıktı: docs/data/kanit.json
"""
import os, json, glob, math
from statistics import NormalDist

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI = os.path.join(KOK, "data")
SITE = os.path.join(KOK, "docs", "data")

HEDEF = 0.05          # ayırt etmek istediğimiz avantaj (geri dönüşte +%5)
Z_NOM = 1.96          # %95 güven
Z_GUC = 0.84          # %80 güç
MIN_N = 30            # bunun altında "çok erken"
LAMBDA = (0.01, 0.02, 0.05, 0.1, 0.2)   # e-değer bahis kesirleri (önceden sabit, sonuca göre değişmez)


def e_deger(liste):
    """liste: [(harcama, kazanç, tarih), ...] -> karışım bahis martingalinin son değeri (tarih sırasıyla)."""
    W = [1.0] * len(LAMBDA)
    for b, k, *_ in sorted(liste, key=lambda x: x[2] if len(x) > 2 else ""):
        if b <= 0:
            continue
        x = k / b
        W = [w * (1 + l * (x - 1)) for w, l in zip(W, LAMBDA)]
    return sum(W) / len(W)


def _oku(yol):
    try:
        return json.load(open(yol, encoding="utf-8"))
    except Exception:
        return None


def egzotik_kosular():
    """data/egzotik/*.json -> {(model, tür): [(harcama, kazanç), ...]} (yalnızca gerçekten seçim yapılan, sonuçlanan koşular)."""
    out = {}
    for y in sorted(glob.glob(os.path.join(VERI, "egzotik", "*.json"))):
        d = _oku(y) or {}
        for c in d.values():
            m = c.get("model", "Bolton")
            for tur, r in (c.get("sonuc") or {}).items():
                if r.get("bedel", 0) > 0:
                    out.setdefault((m, tur), []).append((float(r["bedel"]), float(r["kazanc"]), os.path.basename(y)[:10]))
    return out


# Ana testler (15 Ekim 2026, Doğan'ın seçimi): kanıt eşiği yalnız bunlara göre. Diğer kurallar sitede durur, "arşiv" sayılır.
ANA_EGZ_MODEL = "Jason"                      # egzotik ana kural (1,15), 3 bahis türü
ANA_DEGER = ("ikili", 1.25, 0.01)           # değer filtresi 1,25, piyasa olasılığı >= %1
ANA_BESLI = ("Jason-G", 150)                # sıralı 5'li, geçerli kombinasyon bütçesi 150
# Ganyan: canlıda son ganyan bilinmediği için EV>1,1 kuralı izlenemiyor; canlı karşılığı Jason tüyoları (pJ >= %6, pJ/AGF >= 1,30, 1 TL ganyan)


def deger_kosular(tur, esik, pmmin):
    from .deger import _kazanc, BIRIM as DB
    out = []
    for y in sorted(glob.glob(os.path.join(VERI, "deger", "*.json"))):
        for c in (_oku(y) or {}).values():
            if not c.get("sonuc") or not (c.get("odeme") or {}).get(tur):
                continue
            sec = [b for b in c["bilet"][tur] if b[1] >= esik and (b[2] / max(b[1], 1e-9)) >= pmmin]
            if sec:
                out.append((len(sec) * DB[tur], sum(_kazanc(c, tur, b[0]) for b in sec), os.path.basename(y)[:10] + "|" + str(c.get("saat", ""))))
    return out


def tuyo_kosular():
    k = {}
    for y in sorted(glob.glob(os.path.join(VERI, "tuyo", "*.json"))):
        for key, c in (_oku(y) or {}).items():
            if c.get("sira") is None:
                continue
            r = k.setdefault((os.path.basename(y)[:10], c["hipodrom"], c["kosu"]), [0.0, 0.0, os.path.basename(y)[:10] + "|" + str(c.get("saat", ""))])
            r[0] += 1.0; r[1] += (c.get("g") or 0.0) if c["sira"] == 1 else 0.0
    return [tuple(v) for v in k.values()]


def besli_kosular(model, butce):
    from .besli import gecerli_say, BIRIM as BB
    out = []
    for y in sorted(glob.glob(os.path.join(VERI, "besli", "*.json"))):
        for c in (_oku(y) or {}).values():
            for q in c.get("kuponlar", []):
                if q.get("model") == model and q.get("butce") == butce and "isabet" in q:
                    out.append((gecerli_say(q["ayaklar"]) * BB, float(q.get("kazanc") or 0.0), os.path.basename(y)[:10] + "|" + str(c.get("saat", ""))))
    return out


def kural_say():
    """Sitede izlenen kural/varyant sayısı (en az). Her dosyadan, bahis türünden bağımsız ayrı kural kimlikleri sayılır."""
    L = lambda n: _oku(os.path.join(SITE, n + ".json")) or {}
    parca = {}
    eg = L("egzotik")
    parca["egzotik"] = 3 + len(eg.get("toplam_varyant") or {})                    # Bolton, Jason, Jason-S + ön-kayıtlı varyantlar
    dg = L("deger")
    parca["deger"] = len({(t.get("esik"), t.get("pm_min")) for t in dg.get("toplam", [])})
    kb = L("kombine")
    parca["kombine"] = len({(t.get("grup"), t.get("model")) for t in kb.get("toplam", [])})
    bs = L("besli")
    parca["besli"] = len({(t.get("grup"), t.get("model")) for t in bs.get("toplam", [])})
    k7 = L("kupon7")
    parca["kupon7"] = len({(t.get("grup"), t.get("mod"), t.get("butce")) for t in k7.get("toplam", [])})
    pl = L("plase")
    parca["plase"] = len({(t.get("tur"), t.get("k")) for t in pl.get("toplam", [])})
    return max(1, sum(parca.values())), parca


def z_duz(m):
    return NormalDist().inv_cdf(1 - 0.05 / (2 * max(1, m)))


def hesapla(liste, zd, m=1):
    ev = e_deger(liste)
    n = len(liste)
    gun = len({x[2] for x in liste}) if liste and len(liste[0]) > 2 else None
    liste = [(x[0], x[1]) for x in liste]
    B = sum(b for b, _ in liste)
    K = sum(k for _, k in liste)
    if n == 0 or B <= 0:
        return {"n": n, "harcama": round(B, 2), "kazanc": round(K, 2), "geri_donus": None, "aralik": None, "aralik_duz": None,
                "gerekli_n": None, "kalan_n": None, "etiket": "veri yok"}
    R = K / B
    sonuc = {"n": n, "gun": gun, "harcama": round(B, 2), "kazanc": round(K, 2), "geri_donus": round(R, 3),
             "e": round(ev, 3), "e_esik": round(m / 0.05, 1)}
    if n < 2:
        sonuc.update({"aralik": None, "aralik_duz": None, "gerekli_n": None, "kalan_n": None, "etiket": "çok erken"})
        return sonuc
    bm = B / n
    s = math.sqrt(sum((k - R * b) ** 2 for b, k in liste) / (n - 1))
    sd_r = s / bm
    se = sd_r / math.sqrt(n)
    lo, hi = R - Z_NOM * se, R + Z_NOM * se
    lo_d, hi_d = R - zd * se, R + zd * se
    gerekli = ((Z_NOM + Z_GUC) * sd_r / HEDEF) ** 2 if sd_r > 0 else None
    if n < MIN_N:
        et = "çok erken"
    elif ev >= m / 0.05:
        et = "net olumlu (e-değer)"
    elif lo_d > 1:
        et = "net olumlu"
    elif hi_d < 1:
        et = "net olumsuz"
    else:
        et = "belirsiz"
    sonuc.update({"aralik": [round(lo, 2), round(hi, 2)], "aralik_duz": [round(lo_d, 2), round(hi_d, 2)], "oynaklik": round(sd_r, 2),
                  "gerekli_n": int(math.ceil(gerekli)) if gerekli else None,
                  "kalan_n": max(0, int(math.ceil(gerekli)) - n) if gerekli else None, "etiket": et})
    if gerekli and gun:
        gunluk = n / gun                                   # günde ortalama kaç koşuda seçim yapılıyor
        sonuc["kalan_yil"] = round(max(0, gerekli - n) / gunluk / 365, 1)
    return sonuc


def yaz(tarih=None):
    m_tum, parca = kural_say()
    egz = egzotik_kosular()
    ana = [(("Egzotik (Jason)", t), egz.get((ANA_EGZ_MODEL, t), [])) for t in ("SIRALI İKİLİ", "İKİLİ", "ÜÇLÜ BAHİS")]
    ana += [(("Değer filtresi 1,25", "İKİLİ"), deger_kosular(*ANA_DEGER)),
            (("Jason tüyo (ganyan)", "GANYAN"), tuyo_kosular()),
            (("Sıralı 5'li (Jason-G 150)", "SIRALI 5"), besli_kosular(*ANA_BESLI))]
    m = len(ana)
    zd = z_duz(m)
    satirlar = []
    for (ad, tur), liste in ana:
        r = hesapla(liste, zd, m)
        r.update({"model": ad, "tur": tur, "kaynak": "ana", "ana": True})
        satirlar.append(r)
    for (model, tur), liste in sorted(egz.items()):
        if model == ANA_EGZ_MODEL:
            continue
        r = hesapla(liste, zd, m)
        r.update({"model": model, "tur": tur, "kaynak": "egzotik", "ana": False})
        if r.get("etiket") not in ("çok erken", "veri yok"):
            r["etiket"] = "arşiv (kanıt dışı)"
        satirlar.append(r)
    os.makedirs(SITE, exist_ok=True)
    cikti = {"tarih": tarih, "kural_sayisi": m, "kural_sayisi_tum": m_tum, "parcalar": parca, "z": Z_NOM, "z_duz": round(zd, 2), "hedef": HEDEF, "guc": 0.8,
             "min_n": MIN_N, "satirlar": satirlar}
    json.dump(cikti, open(os.path.join(SITE, "kanit.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return cikti


if __name__ == "__main__":
    c = yaz()
    print("kural sayısı:", c["kural_sayisi"], c["parcalar"], "z_düz:", c["z_duz"])
    for r in c["satirlar"]:
        print(r["model"], r["tur"], "n=%d" % r["n"], "GD", r["geri_donus"], "aralık", r["aralik"], "düz", r["aralik_duz"], "gerekli", r["gerekli_n"], "e", r.get("e"), "/", r.get("e_esik"), r["etiket"])
