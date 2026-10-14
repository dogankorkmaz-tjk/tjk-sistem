"""Yabancı koşu ekran görüntüleri (15 Ekim 2026). Kaynak sitede bozuk olan ülkeler (Fransa, Güney Afrika, Avustralya,
Arjantin, Şili) için TJK sonuç ekranının görüntüsü -> OCR -> sıra, at no, ganyan.

Akış: site -> data/yabanci_foto/<tarih>_<saat>_<ulke>_<n>.<png|jpg> -> .github/workflows/yabanci_foto.yml -> bu modül.
Çıktı: data/yabanci_foto/metin/<ad>.txt (ham OCR, sonradan yeniden ayrıştırılabilir), data/yabanci_elle/kayit.csv,
       docs/data/yabanci_foto.json (sitede durum). Görüntü işlendikten sonra da saklanır (yeniden okunabilsin diye).
Ayrıştırıcı ilk sürüm: satırda baştaki tam sayılar (sıra, numara) + ondalıklı oran. Gerçek ekran örnekleriyle ayarlanacak."""
import os, re, sys, json, glob, subprocess, tempfile, datetime
import pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOTO = os.path.join(KOK, "data", "yabanci_foto")
METIN = os.path.join(FOTO, "metin")
CIKTI = os.path.join(KOK, "data", "yabanci_elle")
SITE = os.path.join(KOK, "docs", "data")
AD_RE = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{6})_([a-z-]+)_(\d+)\.(png|jpe?g|webp)$", re.I)
SATIR_RE = re.compile(r"^\D{0,3}(\d{1,2})\D{1,4}(\d{1,2})\b(.*)$")
ORAN_RE = re.compile(r"(?<![\d.,])(\d{1,4}),(\d{2})(?![\d.,])")     # ganyan virgüllü (4,35); kilo/derece (56.00, 1.12.45) karışmasın


def ocr(yol):
    """tesseract (tur+eng, iki sayfa düzeni denenir, daha çok satır çıkanı alınır). PIL ile 2x büyütme küçük yazıyı iyileştirir."""
    from PIL import Image, ImageOps
    im = Image.open(yol).convert("L")
    if im.size[0] < 1400:
        im = im.resize((im.size[0] * 2, im.size[1] * 2))
    im = ImageOps.autocontrast(im)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        im.save(f.name); g = f.name
    en = ""
    for psm in ("6", "4"):
        r = subprocess.run(["tesseract", g, "-", "-l", "tur+eng", "--psm", psm], capture_output=True, text=True)
        if not r.stdout.strip():                                       # tur dili kurulu değilse
            r = subprocess.run(["tesseract", g, "-", "--psm", psm], capture_output=True, text=True)
        if len(parse(r.stdout)) > len(parse(en)):
            en = r.stdout
        elif not en:
            en = r.stdout
    os.unlink(g)
    return en


def parse(metin):
    out = []
    for s in metin.splitlines():
        m = SATIR_RE.search(s.strip())
        if not m:
            continue
        o = ORAN_RE.findall(m.group(3))
        if not o:
            continue
        oran = float(o[-1][0] + "." + o[-1][1])                       # satırdaki son virgüllü sayı = ganyan
        sira, no, ad = int(m.group(1)), int(m.group(2)), re.split(r"\d", m.group(3).strip(" |-.:"))[0].strip()
        if 1 <= sira <= 24 and 1 <= no <= 24 and 1.0 <= oran <= 999:
            out.append({"sira": sira, "no": no, "at": ad[:40], "ganyan": oran, "ham": s.strip()[:120]})
    # tutarlılık: sıra 1..n, numaralar tekrarsız
    if out:
        siralar = [x["sira"] for x in out]
        out_ok = sorted(siralar) == list(range(1, len(siralar) + 1)) and len({x["no"] for x in out}) == len(out)
        for x in out:
            x["tutarli"] = out_ok
    return out


def isle():
    os.makedirs(METIN, exist_ok=True); os.makedirs(CIKTI, exist_ok=True); os.makedirs(SITE, exist_ok=True)
    kayit_yol = os.path.join(CIKTI, "kayit.csv")
    kayit = pd.read_csv(kayit_yol) if os.path.exists(kayit_yol) else pd.DataFrame()
    durum = []
    for yol in sorted(glob.glob(os.path.join(FOTO, "*"))):
        ad = os.path.basename(yol); m = AD_RE.search(ad)
        if not m:
            continue
        txt = os.path.join(METIN, ad + ".txt")
        if not os.path.exists(txt):
            open(txt, "w", encoding="utf-8").write(ocr(yol))
            print("OCR:", ad)
        rows = parse(open(txt, encoding="utf-8").read())
        tarih, _, ulke, n = m.group(1), m.group(2), m.group(3), int(m.group(4))
        tutarli = bool(rows) and rows[0]["tutarli"]
        durum.append({"dosya": ad, "tarih": tarih, "ulke": ulke, "satir": len(rows), "tutarli": tutarli,
                      "kazanan": next((f"{x['no']} ({x['ganyan']})" for x in rows if x["sira"] == 1), None)})
        if rows:
            d = pd.DataFrame(rows).assign(dosya=ad, tarih=tarih, ulke=ulke)
            kayit = pd.concat([kayit[kayit.dosya != ad] if len(kayit) else kayit, d], ignore_index=True)
    if len(kayit):
        kayit.to_csv(kayit_yol, index=False)
    json.dump({"zaman": (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
               "toplam": len(durum), "tutarli": sum(x["tutarli"] for x in durum), "dosyalar": durum[-60:][::-1]},
              open(os.path.join(SITE, "yabanci_foto.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(durum)} görüntü, {sum(x['tutarli'] for x in durum)} tutarlı")


if __name__ == "__main__":
    isle()
