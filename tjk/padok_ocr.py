"""T143-B: padok karelerinin alt yazısını OCR'la (tesseract tur+eng). Kullanım: python3 tjk/padok_ocr.py KARE_KLASÖRÜ ÇIKTI.csv.gz
Her kare için alt %45 kırpılır, 2x büyütülür, gri tonlanır; metin tek satıra indirilir. Çıktı: dosya, kare_no, epoch (başlangıç dosyasından), metin."""
import sys, os, glob, re, subprocess, gzip, csv, io
from multiprocessing import Pool
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


if __name__ == "__main__":
    kok, cikti = sys.argv[1], sys.argv[2]
    F = sorted(glob.glob(os.path.join(kok, "**", "*.jpg"), recursive=True))
    bas = {}
    for b in glob.glob(os.path.join(kok, "**", "*_baslangic.txt"), recursive=True):
        bas[os.path.basename(b).split("_")[0]] = float(open(b).read().strip())
    print("kare", len(F), "| başlangıç", bas, flush=True)
    with Pool(os.cpu_count() or 2) as p:
        R = p.map(ocr, F, chunksize=50)
    os.makedirs(os.path.dirname(cikti) or ".", exist_ok=True)
    with gzip.open(cikti, "wt", encoding="utf-8", newline="") as g:
        w = csv.writer(g); w.writerow(["dosya", "kare_no", "epoch", "metin"])
        for f, t in R:
            ad = os.path.basename(f)[:-4]; on, no = ad.split("_")[0], int(ad.split("_")[1])
            w.writerow([ad, no, round(bas[on] + no - 1, 1) if on in bas else "", t])
    print("yazıldı", cikti, sum(1 for _, t in R if t), "metinli kare")
