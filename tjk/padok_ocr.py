"""T143-B: padok karelerinin alt yazısını OCR'la (tesseract tur+eng). Kullanım: python3 tjk/padok_ocr.py KARE_KLASÖRÜ ÇIKTI.csv.gz
Her kare için alt %45 kırpılır, 2x büyütülür, gri tonlanır; metin tek satıra indirilir. Çıktı: dosya, kare_no, epoch (başlangıç dosyasından), metin.
Hız (6 Kasım): tesseract tek iş parçacığı (OMP_THREAD_LIMIT=1; paralel süreçlerle çakışmasın); alt yazı bölgesi önceki OCR'lanan kareden
belirgin farklı değilse (64x24 gri küçük resim ortalama mutlak fark < ESIK) OCR yapılmaz, önceki metin kullanılır (kopya=1)."""
import sys, os, glob, re, subprocess, gzip, csv, io
from multiprocessing import Pool
import numpy as np
os.environ["OMP_THREAD_LIMIT"] = "1"
ESIK = 6.0
from PIL import Image, ImageOps


def ocr(f):
    try:
        im = Image.open(f); w, h = im.size
        c = ImageOps.grayscale(im.crop((0, int(h * 0.55), w, h))).resize((w * 2, int(h * 0.45) * 2), Image.LANCZOS)
        b = io.BytesIO(); c.save(b, "PNG")
        r = subprocess.run(["tesseract", "stdin", "stdout", "-l", "tur+eng", "--psm", "6"], input=b.getvalue(), capture_output=True, timeout=60)
        return f, re.sub(r"\s+", " ", r.stdout.decode("utf-8", "ignore")).strip()
    except Exception as e:
        return f, "HATA " + repr(e)


def imza(f):
    try:
        im = Image.open(f); w, h = im.size
        return f, np.asarray(ImageOps.grayscale(im.crop((0, int(h * 0.55), w, h))).resize((64, 24)), dtype=float)
    except Exception:
        return f, None


if __name__ == "__main__":
    kok, cikti = sys.argv[1], sys.argv[2]
    F = sorted(glob.glob(os.path.join(kok, "**", "*.jpg"), recursive=True))
    bas = {}
    for b in glob.glob(os.path.join(kok, "**", "*_baslangic.txt"), recursive=True):
        bas[os.path.basename(b).split("_")[0]] = float(open(b).read().strip())
    print("kare", len(F), "| başlangıç", bas, flush=True)
    with Pool(os.cpu_count() or 2) as p:
        I = dict(p.map(imza, F, chunksize=200))
        sec, son = [], None
        for f in F:                                  # alt yazı değişen kareler (ilk kare dahil)
            a = I[f]
            if a is None or son is None or np.abs(a - son).mean() >= ESIK:
                sec.append(f); son = a
        print("OCR'lanacak", len(sec), "/", len(F), flush=True)
        O = dict(p.map(ocr, sec, chunksize=20))
    R, kop, t = [], [], ""
    for f in F:
        if f in O:
            t = O[f]; kop.append(0)
        else:
            kop.append(1)
        R.append((f, t))
    os.makedirs(os.path.dirname(cikti) or ".", exist_ok=True)
    with gzip.open(cikti, "wt", encoding="utf-8", newline="") as g:
        w = csv.writer(g); w.writerow(["dosya", "kare_no", "epoch", "kopya", "metin"])
        for (f, t), k in zip(R, kop):
            ad = os.path.basename(f)[:-4]; on, no = ad.split("_")[0], int(ad.split("_")[1])
            w.writerow([ad, no, round(bas[on] + no - 1, 1) if on in bas else "", k, t])
    print("yazıldı", cikti, sum(1 for _, t in R if t), "metinli kare")
