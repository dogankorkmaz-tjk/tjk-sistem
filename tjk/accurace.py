"""Accurace koşu PDF'ini (tek sayfa, görüntü) okuyup CSV/JSON satırlarına çevirir.
Kullanım:  python3 -m tjk.accurace <dosya.pdf> [...]     -> data/accurace/<ad>.json
Dosya adı:  2026-10-10_izmir_1.pdf  (tarih_hipodrom_kosu). Elle indirilen PDF'ler okunur; siteye bağlanmaz.
Sütunlar: sure, mesafe (bölüm m), bariyer (m), hiz_ort, bitis_sure(sn), hiz_max, hiz_bitis, kosulan_mesafe, delta, fark
"""
import os, re, sys, json, subprocess, tempfile
import numpy as np
from PIL import Image

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = 200 / 100.0                                     # 100 dpi koordinatlarından 200 dpi'ye


def _ocr(im, psm=6, wl=None):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as t:
        yol = t.name
    im.save(yol)
    cmd = ["tesseract", yol, "-", "--psm", str(psm), "-c", "preserve_interword_spaces=1"]
    if wl:
        cmd += ["-c", "tessedit_char_whitelist=" + wl]
    s = subprocess.run(cmd, capture_output=True, text=True).stdout
    os.unlink(yol)
    return s


def _sure(s):
    m = re.match(r"(?:(\d+)['’°])?(\d+)[\"'’°]+(\d{2})$", s.strip().replace("''", '"'))
    return None


def _sn(tok):
    """1'56"00 -> 116.00 ; 7"57 / 7'57 / 7°57 -> 7.57"""
    t = re.sub(r"[^0-9'\"°’]", "", tok)
    p = re.split(r"['\"°’]+", t)
    p = [x for x in p if x != ""]
    try:
        if len(p) == 3:
            return int(p[0]) * 60 + float(p[1] + "." + p[2])
        if len(p) == 2:
            return float(p[0] + "." + p[1])
    except ValueError:
        pass
    return None


def _say(tok):
    t = tok.replace(",", ".").replace("—", "-")
    try:
        return float(t)
    except ValueError:
        return None


def _satirlar(im):
    """Soldaki renkli numara rozetlerinden satır merkezlerini bul."""
    a = np.array(im.convert("RGB")).astype(int)
    W = a.shape[1]; s = W / 906
    kol = a[:, int(15 * s):int(58 * s)]
    mx, mn = kol.max(2), kol.min(2)
    renkli = ((mx - mn) > 60).sum(1) > 8 * s
    out, bas = [], None
    for y, v in enumerate(renkli):
        if v and bas is None:
            bas = y
        if not v and bas is not None:
            if y - bas > 20 * s and bas > 400 * s:
                out.append((bas, y))
            bas = None
    return out


def _numara(im, y0, y1):
    s = im.size[0] / 906
    c = im.crop((int(15 * s), y0, int(58 * s), y1)).convert("RGB")
    a = np.array(c).astype(int)
    beyaz = (a.min(2) > 215)
    g = Image.fromarray(np.where(beyaz, 0, 255).astype("uint8")).resize((c.size[0] * 3, c.size[1] * 3))
    g = Image.fromarray(np.pad(np.array(g), 30, constant_values=255))
    m = re.search(r"\d{1,2}", _ocr(g, 7, "0123456789"))
    return int(m.group()) if m else None


def oku(pdf):
    with tempfile.TemporaryDirectory() as k:
        subprocess.run(["pdftoppm", "-r", "200", "-png", pdf, os.path.join(k, "p")], check=True)
        im = Image.open([os.path.join(k, f) for f in sorted(os.listdir(k))][0])
    s = im.size[0] / 906
    rows = _satirlar(im)
    ust = _ocr(im.crop((0, int(150 * s), im.size[0], int(240 * s))), 6)
    bolum = _ocr(im.crop((0, int(250 * s), int(300 * s), int(290 * s))), 7)
    out = []
    for (y0, y1) in rows:
        no = _numara(im, y0, y1)
        satir = _ocr(im.crop((int(70 * s), y0, im.size[0], y1)), 7).strip()
        ad = re.match(r"([^\d]+?)\s{2,}|([^\d]+?)(?=\d)", satir + "  ")
        ad = (ad.group(1) or ad.group(2)).strip() if ad else None
        kalan = satir[len(ad):] if ad and satir.startswith(ad) else satir
        tok = kalan.split()
        r = {"no": no, "ad": ad, "ham": satir}
        if len(tok) >= 9:
            r.update(sure=_sn(tok[0]), mesafe=_say(tok[1]), bariyer=_say(tok[2]), hiz_ort=_say(tok[3]),
                     bitis_sure=_sn(tok[4]), hiz_max=_say(tok[5]), hiz_bitis=_say(tok[6]),
                     kosulan_mesafe=_say(tok[7]), delta=_say(tok[8]), fark=_say(tok[9]) if len(tok) > 9 else None)
        out.append(r)
    return {"baslik": ust.strip(), "bolum": bolum.strip(), "atlar": out}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    os.makedirs(os.path.join(KOK, "data", "accurace"), exist_ok=True)
    for f in sys.argv[1:]:
        c = oku(f)
        c["dosya"] = os.path.basename(f)
        json.dump(c, open(os.path.join(KOK, "data", "accurace", os.path.splitext(os.path.basename(f))[0] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f, len(c["atlar"]), "at")
        for r in c["atlar"]:
            print({k: v for k, v in r.items() if k != "ham"})
