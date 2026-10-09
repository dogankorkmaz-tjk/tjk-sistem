"""Altılı kupon kurucu: değer = model olasılığı / havuz payı (AGF veya kapanış ganyanı).
Beklenen getiri oranı = (1-kesinti) * Π_ayak Σ_{h∈S} r_h / Π|S|,  r_h = pm_h / pa_h."""
import math, json, glob, os
import pandas as pd

KESINTI = 0.31


def kur(ayaklar, butce, mod="deger"):
    """ayaklar: [{no: (pm, pa)}]. butce: en çok kombinasyon. mod: 'deger' (r'ye göre) | 'favori' (pm'ye göre).
    Döner: seçilen no listeleri."""
    sec = []
    for a in ayaklar:
        en = max(a, key=lambda h: a[h][0])
        sec.append([en])
    def skor(h, a):
        pm, pa = a[h]
        return pm if mod == "favori" else pm / max(pa, 1e-6)
    while True:
        n = math.prod(len(s) for s in sec)
        en_iyi, en_k = None, 0
        for i, a in enumerate(ayaklar):
            adaylar = [h for h in a if h not in sec[i]]
            if not adaylar or n // len(sec[i]) * (len(sec[i]) + 1) > butce:
                continue
            h = max(adaylar, key=lambda x: skor(x, a))
            R = sum(skor(x, a) for x in sec[i]); r = skor(h, a)
            kazanc = math.log((R + r) / R) / math.log((len(sec[i]) + 1) / len(sec[i]))
            if kazanc > en_k:
                en_iyi, en_k = (i, h), kazanc
        if not en_iyi:
            return sec
        sec[en_iyi[0]].append(en_iyi[1])


def ozet(ayaklar, sec):
    n = math.prod(len(s) for s in sec)
    tut = math.prod(sum(a[h][0] for h in s) for a, s in zip(ayaklar, sec))
    tut_p = math.prod(sum(a[h][1] for h in s) for a, s in zip(ayaklar, sec))
    roi = (1 - KESINTI) * math.prod(sum(a[h][0] / max(a[h][1], 1e-6) for h in s) for a, s in zip(ayaklar, sec)) / n
    return {"kombinasyon": n, "tutma_model": tut, "tutma_piyasa": tut_p, "beklenen_getiri_orani": roi}


TURLER = {"3'LÜ GANYAN": 3, "4'LÜ GANYAN": 4, "5'Lİ GANYAN": 5, "6'LI GANYAN": 6, "7'Lİ GANYAN": 7}


def gecmis_ayaklar(tur="6'LI GANYAN"):
    """{(tarih,hip,son_kosu): (ayaklar, kazananlar)} — docs/data/gun/*.json sonuçlarından."""
    o = pd.read_csv("data/odeme/2026-10.csv.gz")
    a = o[o.tur == tur]; L = TURLER[tur]
    gun = {}
    for y in glob.glob("docs/data/gun/*.json"):
        d = json.load(open(y)); gun[d["tarih"]] = d
    out = []
    for _, r in a.iterrows():
        d = gun.get(r.tarih)
        if not d:
            continue
        h = next((x for x in d["hipodromlar"] if x["id"] == r.hipodrom), None)
        if not h:
            continue
        k = {x["kosu"]: x for x in h["kosular"]}
        ay, kaz, ok = [], [], True
        for i in range(L):
            x = k.get(r.kosu - L + 1 + i)
            if not x or not x.get("sonuc"):
                ok = False; break
            s = x["sonuc"]
            ay.append({int(no): (v["pm"], v["pp"]) for no, v in s.items()})
            kaz.append([int(no) for no, v in s.items() if v["sira"] == 1])
        if ok:
            out.append((r.tarih, r.hipodrom, r.kosu, ay, kaz, float(r.tutar)))
    return out


if __name__ == "__main__":
    for tur, L in TURLER.items():
        veri = gecmis_ayaklar(tur)
        print(f"== {tur}: {len(veri)} oyun")
        for B in (12, 48, 192):
            for mod in ("favori", "deger"):
                harc = kaz = isabet = 0
                for t, hp, k, ay, kz, tutar in veri:
                    s = kur(ay, B, mod)
                    harc += math.prod(len(x) for x in s)
                    if all(set(kz[i]) & set(s[i]) for i in range(L)):
                        isabet += 1; kaz += tutar
                if harc:
                    print(f"  B={B:4d} {mod:7s} harcama={harc:6d} isabet={isabet:2d}/{len(veri)} geri dönüş={kaz/harc:.2f}")
