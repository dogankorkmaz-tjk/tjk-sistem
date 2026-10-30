"""Sporx 'hazır kuponlar' (halka açık, robots.txt izinli) -> data/yorumcu/otomatik/<gün>.json. YARIŞTAN ÖNCE ilk görülen hali DONAR (sonradan düzenleme izlenir, skora girmez).
Kaynaklar: üç kupon ('FENOMEN TİLKİ', 'EDİTÖRÜN KUPONU', 'HİPODROM GÜZELİ') ve iki yapay zeka günün atı ('SPRINTMASTER', 'BEYGİRBOOSTER').
Altılı ayakları yarış numarasına çevirmek puanlama anında yapılır (I. altılı = ilk 6 koşu, II. altılı = son 6 koşu; ayak alan büyüklükleri ile doğrulanır)."""
import os, re, json, datetime
import requests
try:
    from curl_cffi import requests as CR
except Exception:
    CR = None
from bs4 import BeautifulSoup
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
URL = "https://www.sporx.com/at-yarisi-hazir-kuponlar"
KLAS = os.path.join(KOK, "data", "yorumcu", "otomatik")
H = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; dusuk sikli istek)"}


def _getir():
    r = CR.get(URL, impersonate="chrome", timeout=25) if CR else requests.get(URL, headers=H, timeout=25)
    if r.status_code != 200: raise RuntimeError(f"HTTP {r.status_code}")
    b = r.content
    try: return b.decode("utf-8")
    except UnicodeDecodeError: return b.decode("cp1254", errors="replace")


def _slug(s):
    t = {"İ": "i", "I": "i", "ı": "i", "Ş": "s", "ş": "s", "Ğ": "g", "ğ": "g", "Ü": "u", "ü": "u", "Ö": "o", "ö": "o", "Ç": "c", "ç": "c"}
    return re.sub(r"[^a-z0-9]+", "-", "".join(t.get(c, c) for c in s).lower()).strip("-")


HIPLER = ["istanbul", "ankara", "izmir", "bursa", "adana", "kocaeli", "elazig", "diyarbakir", "sanliurfa", "antalya"]


def _hipid(x):
    x = _slug(x or "").replace("-", "")
    for h in HIPLER:
        if x == h or (len(x) >= 4 and h.endswith(x)): return h
    return x or None


def ayristir(html):
    """-> {'kuponlar': [{'ad','atad','altili':'İstanbul II. Altılı Ganyan','hip':'istanbul','altili_no':2,'ayaklar':[[no,...]x6]}], 'yz': [{'ad','at','hip','kosu'}]}"""
    s = BeautifulSoup(html, "html.parser"); out = {"kuponlar": [], "yz": []}
    txt = s.get_text("\n", strip=True)
    for m in re.finditer(r"Yapay Zeka tahmincimiz\s*\n\s*([^\n]+?)\s*\n\s*bug.n i.in .neriyor:\s*\n\s*(.+?)\s*\(\s*(\S+)\s+(\d+)\.\s*k.\)", txt):
        out["yz"].append({"ad": m.group(1), "at": m.group(2).strip(), "hip": _hipid(m.group(3)), "kosu": int(m.group(4))})
    # kupon kutuları
    for kutu in re.split(r'font-size: 20px;">', html)[1:]:
        ad = re.match(r"([^<]+)</div>", kutu); ad = ad.group(1).strip() if ad else "?"
        sub = BeautifulSoup(kutu, "html.parser")
        yaz = [d.get_text(" ", strip=True) for d in sub.select('.tahmin_texts div')]
        yaz = [y for y in yaz if y]
        altili = next((y for y in yaz if re.search(r"Alt.l. Ganyan", y)), None); atad = yaz[0] if yaz else ""
        cols = sub.select(".kupon-yazar-column")[:6]
        ay = [[int(x.get_text(strip=True)) for x in c.select(".kupon-yazar-item") if x.get_text(strip=True).isdigit()] for c in cols]
        if len(ay) != 6 or not altili: continue
        mm = re.match(r"(.+?)\s+(I+|IV|V|VI)\.\s*Alt", altili)
        rom = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
        out["kuponlar"].append({"ad": ad, "slug": _slug(ad), "atad": atad, "altili": altili, "hip": _hipid(mm.group(1)) if mm else None,
                                "altili_no": rom.get(mm.group(2)) if mm else None, "ayaklar": ay})
    return out


def kaydet(tarih=None):
    simdi = datetime.datetime.utcnow() + datetime.timedelta(hours=3); tarih = tarih or simdi.date().isoformat()
    os.makedirs(KLAS, exist_ok=True); yol = os.path.join(KLAS, tarih + ".json")
    try: D = json.load(open(yol, encoding="utf-8"))
    except Exception: D = {"tarih": tarih, "kuponlar": {}, "yz": {}, "degisiklik": []}
    onceki = (datetime.date.fromisoformat(tarih) - datetime.timedelta(days=1)).isoformat()
    try: P = json.load(open(os.path.join(KLAS, onceki + ".json"), encoding="utf-8"))
    except Exception: P = {"kuponlar": {}, "yz": {}}
    R = ayristir(_getir()); yeni = 0
    for k in R["kuponlar"]:
        key = f"{k['slug']}|{k['hip']}|{k['altili_no']}"
        eski = P["kuponlar"].get(key)
        if eski and eski["ayaklar"] == k["ayaklar"] and eski["atad"] == k["atad"]: continue          # dünkü içerik: sayfa henüz güncellenmemiş
        if key in D["kuponlar"]:
            if D["kuponlar"][key]["ayaklar"] != k["ayaklar"]: D["degisiklik"].append({"t": simdi.strftime("%H:%M"), "key": key, "ayaklar": k["ayaklar"]})
            continue
        D["kuponlar"][key] = {**k, "ilk_gorulme": simdi.strftime("%H:%M:%S")}; yeni += 1
    for y in R["yz"]:
        key = f"{y['ad']}|{y['hip']}|{y['kosu']}"
        eski = P["yz"].get(key)
        if eski and eski["at"] == y["at"]: continue
        if key not in D["yz"]: D["yz"][key] = {**y, "ilk_gorulme": simdi.strftime("%H:%M:%S")}; yeni += 1
    json.dump(D, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("yorumcu_sporx: yeni", yeni, "| kupon", len(D["kuponlar"]), "yz", len(D["yz"]))
    return yeni


if __name__ == "__main__":
    kaydet()
