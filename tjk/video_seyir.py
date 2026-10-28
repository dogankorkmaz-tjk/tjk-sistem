"""TJK yayın videosunun alt şeridinden at bazında koşu seyri (sıra zaman serisi) çıkarır.

Kullanım:  python3 -m tjk.video_seyir <video.mp4> <at_sayisi veya 1,2,4,5,...> [tarih hipodrom kosu]
Çıktı: data/video_seyir/<tarih>_<hipodrom>_<kosu>.json (verilmezse video adıyla)

Yöntem: şerit (1920x1080 karede x140..1480, y840..920) her saniye kırpılır; her kutunun renginden at numarası bulunur.
Renk paleti videonun kendisinden öğrenilir: koşu başında şerit 1..N sırasıyla gösterilir.
Kutu soldan sağa ilerlerken ön sıradan geriye doğru dizilir. Kalan mesafe halkadan okunur (tesseract, kısmen güvenilir).
Video herhangi bir çözünürlükte olabilir (480p mobil sürüm dahil): kareler 1920x1080'e ölçeklenir.
Yarış videosu elle indirilip yüklenir ya da tjk.video_gunluk ile (GitHub Actions) indirilir; bu modül hiçbir siteye bağlanmaz.
"""
import os, sys, re, json, glob, subprocess, tempfile
import numpy as np
from PIL import Image

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOL0, ARALIK = 348, 124.5            # ilk kutunun sol kenarı ve kutular arası mesafe (şerit kırpımında)


def _genislik(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width", "-of", "csv=p=0", video], capture_output=True, text=True)
    try:
        return int(r.stdout.strip().split()[0])
    except Exception:
        return 1920


def _kareler(video, klasor, fps=2):
    """Şerit kırpımı (1640x80, 1920x1080 koordinatlarında x140,y840). 854 piksel genişlikli mobil videoda önce şerit kırpılır, sonra büyütülür (hızlı)."""
    w = _genislik(video)
    if w >= 1900:
        vf = f"fps={fps},crop=1640:80:140:840"
    else:
        f = w / 1920.0
        vf = f"fps={fps},crop={int(round(1640 * f))}:{int(round(80 * f))}:{int(round(140 * f))}:{int(round(840 * f))},scale=1640:80:flags=lanczos"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", vf, os.path.join(klasor, "k_%04d.png")], check=True)
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


def _global_palet():
    """11+ numaralı atların sabit yayın renkleri (tjk/video_palet.json; 15 ve 17 henüz bilinmiyor)."""
    y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "video_palet.json")
    return {int(k): np.array(v) for k, v in json.load(open(y)).items()} if os.path.exists(y) else {}


def _sira(im, palet, n, esik=0.9):
    """Kutu-at atamasını Macar yöntemiyle çöz (her numara bir kez). palet: (M,3), M>=n olabilir (şeritte görünmeyen atlar).
    Dönen: palet satır indeksleri (0..M-1), kutu sırasıyla."""
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


def isle(video, n, ad=None, fps=2, esik=0.80):
    """Şerit okuma: her karede ilk 10 kutunun at numarası RAKAM şekliyle okunur (tjk.video_okuma). Renk paleti kullanılmaz
    (11+ numaralı atlarda ve renk kayması olan karelerde yanlış at yazıyordu)."""
    from . import video_okuma as VO
    numaralar = list(n) if isinstance(n, (list, tuple)) else list(range(1, n + 1))   # koşmayan at varsa numaralar 1..N olmaz
    n = len(numaralar)
    tum = numaralar
    kutu = min(n, 10)          # yayın şeridi yalnızca ilk 10 sırayı gösterir
    numaralar = tum[:kutu]
    kume = set(tum)
    with tempfile.TemporaryDirectory() as k:
        fr = _kareler(video, k, fps)
        zaman = []
        for i, f in enumerate(fr):
            im = Image.open(f)
            s = []
            for j in range(kutu):
                num, c = VO.numara(im, j)
                if num is None and c == 0.0:
                    break                                  # şerit soldan dolar: ilk boş kutudan sonrası yok
                if num is None or not (1 <= num <= 30) or c < esik:
                    s = None; break
                s.append(num)
            ok = bool(s) and len(s) >= min(kutu, 4) and len(set(s)) == len(s)
            zaman.append({"t": round(i / fps, 1), "sira": s if ok else None, "mesafe": _mesafe(im) if (ok and i % 6 == 0) else None})
    gecerli = [z for z in zaman if z["sira"]]
    ayrim = 1.0
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
    ozet = _ozet(gecerli, tum, numaralar)
    try:
        bol = bolum_oku(video)
    except Exception as e:
        bol = {}
    cikti = {"okuyucu": "rakam1", "bolum": bol, "video": os.path.basename(video), "at_sayisi": n, "kutu": kutu, "numaralar": tum, "palet_ayrimi": ayrim,
             "kare": len(zaman), "gecerli_kare": len(gecerli), "ozet": ozet, "zaman": zaman}
    yol = os.path.join(KOK, "data", "video_seyir", (ad or os.path.splitext(os.path.basename(video))[0]) + ".json")
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    json.dump(cikti, open(yol, "w", encoding="utf-8"), ensure_ascii=False)
    return cikti


def bolum_oku(video, fps=1):
    """Yayında sağ üstte görünen 'NNN M 00'SS"CC' ara sürelerini (kalan mesafeden bitişe süre) okur.
    Dönen: {"800": 51.27, "600": 39.76, ...} (en sık okunan değer). Koordinatlar 854x480 kare içindir; kare önce 854 genişliğe ölçeklenir."""
    import collections
    ok = collections.defaultdict(collections.Counter)
    with tempfile.TemporaryDirectory() as k:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps={fps},scale=854:480,crop=190:62:650:22,scale=760:248:flags=lanczos,format=gray",
                        os.path.join(k, "b_%04d.png")], check=True)
        for f in sorted(glob.glob(os.path.join(k, "b_*.png"))):
            im = Image.open(f)
            a = np.array(im)
            if (a > 200).mean() < 0.02:         # yazı yoksa (beyaz piksel yok) atla
                continue
            im2 = im.point(lambda p: 255 if p > 170 else 0)
            im2.save(f)
            s = subprocess.run(["tesseract", f, "-", "--psm", "6", "-c", "tessedit_char_whitelist=0123456789M'\\\" "],
                               capture_output=True, text=True).stdout
            for ln in s.splitlines():
                m = re.search(r"(\d{3,4})\s*M\s*(\d{1,2})\D{1,3}(\d{2})\D{1,3}(\d{2})", ln)
                if m:
                    ok[m.group(1)][round(int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 100.0, 2)] += 1
    return {m: c.most_common(1)[0][0] for m, c in ok.items() if c.most_common(1)[0][1] >= 2}


def _ozet(gecerli, numaralar, gorunen=None):
    """Her at için: erken/orta/geç sıra (geçerli kare zaman dilimlerinin ortalaması), son sıra, yer kazancı."""
    if len(gecerli) < 6:
        return {}
    L = len(gecerli)
    dilim = {"erken": gecerli[:L // 3], "orta": gecerli[L // 3: 2 * L // 3], "gec": gecerli[2 * L // 3:]}
    o = {}
    gorunen = gorunen or numaralar
    k = len(gorunen); n = len(numaralar)
    arka = (k + 1 + n) / 2.0          # ilk 10'da olmayan atın sırası bilinmez; arka grubun ortası

    def yer(z, at):
        return z["sira"].index(at) + 1 if at in z["sira"] else arka
    for at in numaralar:
        d = {}
        for ad, kareler in dilim.items():
            d[ad] = round(float(np.mean([yer(z, at) for z in kareler])), 2)
        d["son"] = round(yer(gecerli[-1], at), 1)
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
