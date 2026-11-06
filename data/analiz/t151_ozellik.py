"""T151 özellikleri (ön kayıt: hipotez_defteri 2026-11-06 T151). Hepsi yalnız ÖNCEKİ günlerin bilgisiyle.
Startta kalma (TJK resmî sonuç API'si 'delayedExit', data/atyarisi arşivi, 2023-06 →):
  f_de1 : atın SON koşusunda geç çıkış (boy, 6'da kırpılır, /6); son koşu bilgisi yoksa 0
  f_deE : atın son koşusundan ÖNCEKİ en çok 9 koşusunda geç çıkış oranı, büzmeli n/(n+5) (eski geçmiş/eğilim)
Fedai (video şeridi, data/video_seyir; yalnız iki atı da koşan ekürili koşular, ekür = resmî 'stablemate'):
  fedai etiketi (koşu sonrası): koşunun ilk %25'lik karelerinde ortalama sırası ≤ 2,0 VE bitiş sırası ≥ 4 VE ekürisi önünde bitirdi
  f_fd1 : atın SON ekürili-videolu koşusunda fedai mi (0/1)
  f_fdE : atın daha önceki ekürili-videolu koşularında fedai oranı, büzmeli n/(n+3)
  f_fdP : bu koşuda ekürisi varsa, ekürisinin/ekürilerinin en yüksek fedai eğilimi (onun f_fdE'si ve son-koşu bayrağının büyüğü); yoksa 0
"""
import glob, gzip, json, os, re, collections
import numpy as np, pandas as pd

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
K_DE, K_FD = 5.0, 3.0


def _boy(s):
    s = str(s or "").strip().lower().replace(",", ".")
    if not s:
        return 0.0
    if s.startswith("yarım"):
        return 0.5
    m = re.match(r"([\d.]+)\s*(boy|metre|mt|m)?", s)
    if not m:
        return 1.0
    v = float(m.group(1)); u = m.group(2) or "boy"
    return v / 2.4 if u in ("metre", "mt", "m") else v


def _arsiv():
    S = []; EK = {}
    for f in sorted(glob.glob(os.path.join(KOK, "atyarisi", "*.json.gz"))):
        o = json.load(gzip.open(f, "rt")); t = o["tarih"]
        for hid, ks in (o.get("sonuc") or {}).items():
            for k in ks:
                hs = k.get("horses") or []
                for a in hs:
                    S.append((t, hid, int(k["number"]), int(a["number"]), min(_boy(a.get("delayedExit")), 6.0)))
                    if a.get("stablemate"):
                        EK[(t, hid, int(k["number"]), int(a["number"]))] = int(a["stablemate"])
    A = pd.DataFrame(S, columns=["tarih", "hipodrom", "kosu", "no", "de"]).drop_duplicates(["tarih", "hipodrom", "kosu", "no"])
    return A, EK


def _video_erken(kok=os.path.join(KOK, "video_seyir")):
    """(tarih, hip, kosu) -> {no: ilk %25 karelerde ortalama sıra}; görünmeyen at = (kutu+1+n)/2."""
    R = {}
    for f in glob.glob(os.path.join(kok, "20*.json")):
        b = os.path.basename(f)[:-5].split("_")
        if len(b) != 3:
            continue
        try:
            j = json.load(open(f))
        except Exception:
            continue
        nums = [int(x) for x in j.get("numaralar") or []]
        z = [x["sira"] for x in j.get("zaman") or [] if x.get("sira")]
        kapi = list(j.get("numaralar") or [])[:j.get("kutu", 10)]
        while z and z[0] == kapi:
            z.pop(0)
        if len(z) < 8 or len(nums) < 2:
            continue
        k = j.get("kutu", 10); n = len(nums); arka = (k + 1 + n) / 2.0
        ilk = z[:max(2, len(z) // 4)]
        R[(b[0], b[1], int(b[2]))] = {a: float(np.mean([(fr.index(a) + 1) if a in fr else arka for fr in ilk])) for a in nums}
    return R


def ekle(d, grup):
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    A, EK = _arsiv()
    m = d[["tarih", "hipodrom", "kosu", "no"]].merge(A, on=["tarih", "hipodrom", "kosu", "no"], how="left")
    de = m["de"].values
    at = d["at"].astype(str).values; tar = d.tarih.astype(str).values
    sira = pd.to_numeric(d.sira, errors="coerce").fillna(0).values
    if grup == "DE":
        H = collections.defaultdict(list); f1 = np.zeros(len(d)); fE = np.zeros(len(d)); bek = []; cur = None
        for i in range(len(d)):
            if tar[i] != cur:
                for a_, v_ in bek: H[a_].append(v_)
                bek = []; cur = tar[i]
            h = H[at[i]]
            if h:
                f1[i] = h[-1] / 6.0
                es = h[-10:-1]
                if es: fE[i] = np.mean([v > 0 for v in es]) * len(es) / (len(es) + K_DE)
            if np.isfinite(de[i]): bek.append((at[i], de[i]))
        d["f_de1"] = f1; d["f_deE"] = fE
        return d
    if grup == "FD":
        V = _video_erken()
        key = list(zip(tar, d.hipodrom.astype(str).values, d.kosu.astype(int).values))
        ekg = np.array([EK.get((t, h, k, int(n)), 0) for (t, h, k), n in zip(key, d.no.values)])
        lab = np.full(len(d), np.nan)                       # koşu sonrası fedai etiketi (yalnız ekürili+videolu)
        grp = pd.Series(range(len(d))).groupby([d.tarih, d.hipodrom, d.kosu])
        for (t, h, k), ix in grp:
            ix = list(ix); v = V.get((str(t), str(h), int(k)))
            if v is None: continue
            for i in ix:
                if ekg[i] <= 0 or sira[i] <= 0: continue
                es = [j for j in ix if j != i and ekg[j] == ekg[i] and sira[j] > 0]
                if not es: continue
                e = v.get(int(d.no.values[i]))
                if e is None: continue
                lab[i] = float(e <= 2.0 and sira[i] >= 4 and min(sira[j] for j in es) < sira[i])
        H = collections.defaultdict(list); f1 = np.zeros(len(d)); fE = np.zeros(len(d)); bek = []; cur = None
        for i in range(len(d)):
            if tar[i] != cur:
                for a_, v_ in bek: H[a_].append(v_)
                bek = []; cur = tar[i]
            h = H[at[i]]
            if h:
                f1[i] = h[-1]
                es = h[:-1]
                if es: fE[i] = np.mean(es) * len(es) / (len(es) + K_FD)
            if np.isfinite(lab[i]): bek.append((at[i], lab[i]))
        fP = np.zeros(len(d))
        for (t, h, k), ix in grp:
            ix = list(ix)
            for i in ix:
                if ekg[i] <= 0: continue
                es = [j for j in ix if j != i and ekg[j] == ekg[i]]
                if es: fP[i] = max(max(fE[j], f1[j]) for j in es)
        d["f_fd1"] = f1; d["f_fdE"] = fE; d["f_fdP"] = fP; d["_fd_lab"] = lab
        return d
    raise ValueError(grup)


FEAT = {"DE": ["f_de1", "f_deE"], "DE1": ["f_de1"], "DEE": ["f_deE"], "FD": ["f_fd1", "f_fdE", "f_fdP"]}
