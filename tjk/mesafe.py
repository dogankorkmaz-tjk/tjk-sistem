"""Mesafe uyumu özelliği (Benter'in DPGA'sına benzer) - yalnızca aday model Jason'da kullanılır, Bolton'a dokunmaz.

Her at için: geçmiş koşularının "piyasanın beklediğine göre bitiş artığı" (pozitif = beklenenden iyi), bugünkü koşunun mesafesine
yakınlığa göre üstel ağırlıkla (bant 150 m) ortalanır ve küçük bir önsel ile (2 ağırlık birimi) sıfıra çekilir.
Artık = piyasa-örtük sıra yüzdeliği - gerçek bitiş yüzdeliği, [-1, 1].
Mesafe/pist kaynakları: data/yillik/eslesme_*.csv.gz (yıllık program PDF'lerinden), data/kosu, sonuç ve program CSV başlıkları.
Mesafesi bilinmeyen koşu ya da at için özellik 0'dır."""
import os, re, glob
import numpy as np, pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI = os.path.join(KOK, "data")
BANT = 150.0
ONSEL = 2.0
_RX = re.compile(r";\s*(\d{3,4})m;\s*(Kum|Çim|Sentetik)")


def _slug(s):
    s = s.strip().lower().replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
    return re.sub("[^a-z]", "", s)


def _basliklar(klasor):
    rows = []
    for f in sorted(glob.glob(os.path.join(VERI, klasor, "*.csv"))):
        try:
            L = open(f, encoding="utf-8", errors="replace").read().replace("﻿", "").split("\n")
        except Exception:
            continue
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", L[0]) if L else None
        if not m:
            continue
        tarih = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"; hip = _slug(L[0].split(";")[0])
        for l in L:
            h = re.match(r"\s*(\d+)\.\s*Kosu", l)
            if h:
                md = _RX.search(l)
                if md:
                    rows.append((tarih, hip, int(h.group(1)), int(md.group(1)), md.group(2)))
    return rows


def tablo():
    """(tarih, hipodrom, kosu) -> mesafe, pist; tüm kaynaklar birleşik."""
    parcalar = []
    for f in glob.glob(os.path.join(VERI, "yillik", "eslesme_*.csv.gz")):
        parcalar.append(pd.read_csv(f)[["tarih", "hipodrom", "kosu", "mesafe", "pist"]])
    for f in glob.glob(os.path.join(VERI, "kosu", "*.csv.gz")):
        try:
            parcalar.append(pd.read_csv(f)[["tarih", "hipodrom", "kosu", "mesafe", "pist"]])
        except Exception:
            pass
    rows = _basliklar("tjk_sonuc") + _basliklar("tjk_csv")
    if rows:
        parcalar.append(pd.DataFrame(rows, columns=["tarih", "hipodrom", "kosu", "mesafe", "pist"]))
    if not parcalar:
        return pd.DataFrame(columns=["tarih", "hipodrom", "kosu", "mesafe", "pist"])
    t = pd.concat(parcalar, ignore_index=True)           # sıra: yıllık eşleştirme, data/kosu, gerçek başlıklar (sonuncu kazanır)
    return t.drop_duplicates(["tarih", "hipodrom", "kosu"], keep="last")


def bilgiden(bilgi):
    """'Handikap 17/DHÖ /H1 · 4 Yaşlı Araplar · 1900m Çim' ya da 'ŞARTLI 4 , 2 Yaşlı İngilizler, 57 kg, 1400 Kum' -> (mesafe, pist)."""
    m = re.search(r"(\d{3,4})\s*m?\s*(Kum|Çim|Sentetik)", bilgi or "")
    return (int(m.group(1)), m.group(2)) if m else None


def ekle(d, bugun=None):
    """d: ozellik.hazirla çıktısı. 'f_dp150_m' sütunu eklenir. bugun: {(hipodrom, kosu): (mesafe, pist)} - sonucu bilinmeyen bugünkü koşular."""
    d = d.copy()
    t = tablo()
    d = d.merge(t, on=["tarih", "hipodrom", "kosu"], how="left", suffixes=("", "_m"))
    if bugun:
        for (h, k), (m, p) in bugun.items():
            ix = d.index[(d.hipodrom == h) & (d.kosu == k) & d.yeni]
            d.loc[ix, "mesafe"] = m; d.loc[ix, "pist"] = p
    rk = d.groupby(["tarih", "hipodrom", "kosu"]).p_piyasa.rank(ascending=False, method="first")
    pct_impl = (rk - 1) / (d.n_at - 1).clip(lower=1)
    res = (pct_impl - d.pct).clip(-1, 1)
    res[d.yeni.values] = np.nan
    d["_res"] = res.values
    f = np.zeros(len(d))
    mes = d.mesafe.values.astype(float); r = d["_res"].values
    for at, ix in d.groupby("at").indices.items():
        if len(ix) < 2:
            continue
        ix = ix[np.argsort(d.tarih_dt.values[ix], kind="stable")]
        m = mes[ix]; rr = r[ix]
        for j in range(1, len(ix)):
            if np.isnan(m[j]):
                continue
            ok = ~np.isnan(m[:j]) & ~np.isnan(rr[:j])
            if not ok.any():
                continue
            w = np.exp(-np.abs(m[:j][ok] - m[j]) / BANT)
            f[ix[j]] = (w * rr[:j][ok]).sum() / (w.sum() + ONSEL)
    d["f_dp150_m"] = f
    return d.drop(columns=["_res"])
