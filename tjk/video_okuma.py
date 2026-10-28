"""Yayın şeridindeki kutulardan at numarası okuma (renk yerine RAKAM şekli): beyaz rakam maskesi -> glif ayrıştırma -> şablon eşleme.
Şerit görüntüsü: 1640x80 (1920x1080 koordinatlarında x140,y840 kırpımı). Kutu j'nin sol kenarı ≈ SOL0 + ARALIK*j."""
import os, json
import numpy as np
from PIL import Image

SOL0, ARALIK = 348, 124.5
GW, GH = 20, 28                                     # glif şablon boyutu
YOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "video_glif.npz")
_LIB = None


def _kutu_bbox(a):
    """Kutu dolgu bölgesi: gri şerit zemininden (düşük doygunluk, yüksek parlaklık) ayrışan pikseller."""
    mx = a.max(2); mn = a.min(2)
    sat = (mx - mn) / (mx + 1e-6)
    dolgu = (sat > 0.22) | (mx < 115)
    return dolgu


def glifler(kare, j):
    """Kutu j için beyaz rakam maskesinden glif listesi (soldan sağa), her biri GHxGW normalize maske. Kutu yoksa None."""
    s = int(SOL0 + ARALIK * j)
    c = np.asarray(kare.crop((max(0, s - 4), 4, s + 104, 76)).convert("RGB")).astype(int)
    dolgu = _kutu_bbox(c)
    ys, xs = np.where(dolgu)
    if len(xs) < 600:                                # kutu yok / çok küçük
        return None
    # en büyük yatay yoğunluklu bölge: kolon toplamı > 10 olan kolonların uç noktaları
    kolon = dolgu.sum(0); k = np.where(kolon > 14)[0]
    sat = np.where(dolgu.sum(1) > 20)[0]
    if len(k) < 40 or len(sat) < 25:
        return None
    x0, x1, y0, y1 = k[0], k[-1], sat[0], sat[-1]
    if x1 - x0 < 55 or y1 - y0 < 35:
        return None
    pad_x, pad_y = int((x1 - x0) * 0.08), int((y1 - y0) * 0.12)
    ic = c[y0 + pad_y:y1 - pad_y, x0 + pad_x:x1 - pad_x]
    beyaz = (ic.min(2) > 185)
    from scipy import ndimage
    lb, nl = ndimage.label(beyaz)
    yuk = beyaz.shape[0]; seg = []
    for q in range(1, nl + 1):
        yy, xx = np.where(lb == q)
        if len(yy) < 30 or (yy.max() - yy.min() + 1) < 0.5 * yuk:
            continue                                  # kıvrık çizgi / gürültü
        seg.append((xx.min(), xx.max() + 1, q))
    seg.sort()
    beyaz = np.isin(lb, [q for _, _, q in seg]) if seg else beyaz
    seg = [(a_, b_) for a_, b_, _ in seg]
    # çok geniş segment (iki rakam birleşmiş): en az beyaz kolonunda böl
    seg2 = []
    for a, b in seg:
        if b - a > 0.8 * yuk:
            kt = beyaz[:, a:b].sum(0); orta = range(int((b - a) * 0.3), int((b - a) * 0.7) + 1)
            m = min(orta, key=lambda q: kt[q]) + a
            seg2 += [(a, m), (m + 1, b)]
        else:
            seg2.append((a, b))
    out = []
    for a, b in seg2:
        g = beyaz[:, a:b]
        rr = np.where(g.any(1))[0]
        cc = np.where(g.any(0))[0]
        if len(rr) < 8 or len(cc) < 2:
            continue
        g = g[rr[0]:rr[-1] + 1, cc[0]:cc[-1] + 1]
        h, w = g.shape
        nw = max(2, min(GW, int(round(w * GH / float(h)))))
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((nw, GH), Image.BILINEAR)
        can = np.zeros((GH, GW)); x0 = (GW - nw) // 2
        can[:, x0:x0 + nw] = np.asarray(im).astype(float) / 255.0
        out.append(can)
    return out if out else None


def _norm(g):
    g = g - g.mean(); n = np.linalg.norm(g)
    return g / n if n > 0 else g


def kutuphane():
    global _LIB
    if _LIB is None:
        z = np.load(YOL); L = {}
        for k in z.files:
            L.setdefault(k.split("_")[0], []).append(_norm(z[k]))
        _LIB = L
    return _LIB


def rakam(g):
    """Tek glif -> (rakam, benzerlik, ikinciyle fark)."""
    L = kutuphane(); gn = _norm(g)
    sk = {d: max(float((gn * t).sum()) for t in ts) for d, ts in L.items()}
    d = max(sk, key=sk.get)
    ikinci = sorted(sk.values())[-2] if len(sk) > 1 else 0
    return int(d), sk[d], sk[d] - ikinci


def numara(kare, j):
    """Kutu j'deki at numarası (int) ve güven (min glif benzerliği); okunamazsa (None, 0)."""
    gl = glifler(kare, j)
    if not gl or len(gl) > 2:
        return None, 0.0
    ds = [rakam(g) for g in gl]
    n = int("".join(str(d[0]) for d in ds))
    return n, min(d[1] for d in ds)
