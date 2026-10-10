"""TJK yayın videosunun alt şeridinden at bazında koşu seyri (sıra zaman serisi) çıkarır.

Kullanım:  python3 -m tjk.video_seyir <video.mp4> <at_sayisi veya 1,2,4,5,...> [tarih hipodrom kosu]
Çıktı: data/video_seyir/<tarih>_<hipodrom>_<kosu>.json (verilmezse video adıyla)

Yöntem: şerit (1920x1080 karede x140..1480, y840..920) her saniye kırpılır; her kutunun renginden at numarası bulunur.
Renk paleti videonun kendisinden öğrenilir: koşu başında şerit 1..N sırasıyla gösterilir.
Kutu soldan sağa ilerlerken ön sıradan geriye doğru dizilir. Kalan mesafe halkadan okunur (tesseract, kısmen güvenilir).
Yarış videosu elle indirilip yüklenir; bu araç hiçbir siteye bağlanmaz.
"""
import os, sys, re, json, glob, subprocess, tempfile
import numpy as np
from PIL import Image

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOL0, ARALIK = 348, 124.5            # ilk kutunun sol kenarı ve kutular arası mesafe (şerit kırpımında)


def _kareler(video, klasor, fps=2):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps={fps},crop=1640:80:140:840",
                    os.path.join(klasor, "k_%04d.png")], check=True)
    return sorted(glob.glob(os.path.join(klasor, "k_*.png")))


def _vek(rgb):
    """RGB -> (doygunluk*cos(ton), doygunluk*sin(ton), 0.7*parlaklık): yayındaki saydamlık/parlama farklarına dayanıklı."""
    import colorsys
    h, sa, v = colorsys.rgb_to_hsv(*(np.array(rgb) / 255.0))
    return np.array([sa * np.cos(2 * np.pi * h), sa * np.sin(2 * np.pi * h), 0.7 * v])


def _renkler(im, n):
    a = np.array(im.convert("RGB"))
    out = []
    for i in range(n):
        sol = int(SOL0 + ARALIK * i)
        out.append(_vek(a[14:24, sol + 8:sol + 20].reshape(-1, 3).mean(0)))
    return np.array(out)


def _palet(kareler, n):
    """Başlangıçtaki (1..N sıralı) şeritten renk paletini öğren: ilk karelerden en 'tutarlı' olanı seç."""
    best = None
    for f in kareler[:12]:
        r = _renkler(Image.open(f), n)
        d = min(np.linalg.norm(r[i] - r[j]) for i in range(n) for j in range(i + 1, n))
        if best is None or d > best[0]:
            best = (d, r)
    return best[1], best[0]


def _sira(im, palet, n, esik=0.9):
    """Kutu-at atamasını Macar yöntemiyle çöz (her numara bir kez): bulanık kareleri de kurtarır."""
    from scipy.optimize import linear_sum_assignment
    r = _renkler(im, n)
    dist = np.linalg.norm(r[:, None, :] - palet[None, :, :], axis=2)
    ks, ats = linear_sum_assignment(dist)
    if dist[ks, ats].max() > esik:
        return None
    sira = [0] * n
    for k, a in zip(ks, ats):
        sira[k] = int(a) + 1
    return sira


def _mesafe(im):
    c = im.crop((100, 15, 290, 65)).convert("L").resize((570, 150)).point(lambda p: 255 if p > 200 else 0)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as t:
        yol = t.name
    c.save(yol)
    s = subprocess.run(["tesseract", yol, "-", "--psm", "7", "-c", "tessedit_char_whitelist=0123456789m"],
                       capture_output=True, text=True).stdout
    os.unlink(yol)
    m = re.search(r"(\d{2,4})", s)
    return int(m.group(1)) if m else None


def isle(video, n, ad=None, fps=2):
    numaralar = list(n) if isinstance(n, (list, tuple)) else list(range(1, n + 1))   # koşmayan at varsa numaralar 1..N olmaz
    n = len(numaralar)
    with tempfile.TemporaryDirectory() as k:
        fr = _kareler(video, k, fps)
        palet, ayrim = _palet(fr, n)
        zaman = []
        for i, f in enumerate(fr):
            im = Image.open(f)
            s = _sira(im, palet, n)
            s = [numaralar[x - 1] for x in s] if s else None
            zaman.append({"t": round(i / fps, 1), "sira": s, "mesafe": _mesafe(im) if s else None})
    gecerli = [z for z in zaman if z["sira"]]
    kapi = numaralar                                  # koşu öncesi şerit 1..N sırasıyla durur: o kareleri at
    while gecerli and gecerli[0]["sira"] == kapi:
        gecerli.pop(0)
    # mesafe: azalan ve makul değerleri tut
    son = 9999
    for z in zaman:
        m = z["mesafe"]
        if m is not None and (m > son or m > 3000):
            z["mesafe"] = None
        elif m is not None:
            son = m
    ozet = _ozet(gecerli, numaralar)
    cikti = {"video": os.path.basename(video), "at_sayisi": n, "numaralar": numaralar, "palet_ayrimi": round(float(ayrim), 1),
             "kare": len(zaman), "gecerli_kare": len(gecerli), "ozet": ozet, "zaman": zaman}
    yol = os.path.join(KOK, "data", "video_seyir", (ad or os.path.splitext(os.path.basename(video))[0]) + ".json")
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    json.dump(cikti, open(yol, "w", encoding="utf-8"), ensure_ascii=False)
    return cikti


def _ozet(gecerli, numaralar):
    """Her at için: erken/orta/geç sıra (geçerli kare zaman dilimlerinin ortalaması), son sıra, yer kazancı."""
    if len(gecerli) < 6:
        return {}
    L = len(gecerli)
    dilim = {"erken": gecerli[:L // 3], "orta": gecerli[L // 3: 2 * L // 3], "gec": gecerli[2 * L // 3:]}
    o = {}
    for at in numaralar:
        d = {}
        for ad, kareler in dilim.items():
            d[ad] = round(float(np.mean([z["sira"].index(at) + 1 for z in kareler])), 2)
        d["son"] = gecerli[-1]["sira"].index(at) + 1
        d["kazanc_gec"] = round(d["orta"] - d["gec"], 2)           # + = geride gelip öne çıkıyor (kapanışçı)
        d["kayip_gec"] = round(d["gec"] - d["erken"], 2)            # + = öndeyken geriye düşmüş
        o[str(at)] = d
    return o


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    ad = "_".join(sys.argv[3:6]) if len(sys.argv) >= 6 else None
    a2 = sys.argv[2]
    c = isle(sys.argv[1], [int(x) for x in a2.split(',')] if ',' in a2 else int(a2), ad)
    print("geçerli kare", c["gecerli_kare"], "/", c["kare"])
    for at, d in c["ozet"].items():
        print(at, d)
