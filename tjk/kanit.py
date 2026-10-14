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


def hesapla(liste, zd):
    n = len(liste)
    gun = len({x[2] for x in liste}) if liste and len(liste[0]) > 2 else None
    liste = [(x[0], x[1]) for x in liste]
    B = sum(b for b, _ in liste)
    K = sum(k for _, k in liste)
    if n == 0 or B <= 0:
        return {"n": n, "harcama": round(B, 2), "kazanc": round(K, 2), "geri_donus": None, "aralik": None, "aralik_duz": None,
                "gerekli_n": None, "kalan_n": None, "etiket": "veri yok"}
    R = K / B
    sonuc = {"n": n, "gun": gun, "harcama": round(B, 2), "kazanc": round(K, 2), "geri_donus": round(R, 3)}
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
    m, parca = kural_say()
    zd = z_duz(m)
    satirlar = []
    for (model, tur), liste in sorted(egzotik_kosular().items()):
        r = hesapla(liste, zd)
        r.update({"model": model, "tur": tur, "kaynak": "egzotik"})
        satirlar.append(r)
    os.makedirs(SITE, exist_ok=True)
    cikti = {"tarih": tarih, "kural_sayisi": m, "parcalar": parca, "z": Z_NOM, "z_duz": round(zd, 2), "hedef": HEDEF, "guc": 0.8,
             "min_n": MIN_N, "satirlar": satirlar}
    json.dump(cikti, open(os.path.join(SITE, "kanit.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return cikti


if __name__ == "__main__":
    c = yaz()
    print("kural sayısı:", c["kural_sayisi"], c["parcalar"], "z_düz:", c["z_duz"])
    for r in c["satirlar"]:
        print(r["model"], r["tur"], "n=%d" % r["n"], "GD", r["geri_donus"], "aralık", r["aralik"], "düz", r["aralik_duz"], "gerekli", r["gerekli_n"], r["etiket"])
