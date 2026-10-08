"""İndirme ve ayrıştırma: agftablosu.com (robots.txt izin veriyor; istekler yavaş ve az)."""
import re, time, datetime
from io import StringIO
import numpy as np, pandas as pd, requests
from bs4 import BeautifulSoup

BASE = "https://www.agftablosu.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; gunde birkac yavas istek)"}
DELAY = 2.0
AYLAR = ["ocak", "subat", "mart", "nisan", "mayis", "haziran",
         "temmuz", "agustos", "eylul", "ekim", "kasim", "aralik"]
GUNLER = ["pazartesi", "sali", "carsamba", "persembe", "cuma", "cumartesi", "pazar"]
TRH = ["istanbul", "ankara", "izmir", "bursa", "adana", "kocaeli",
       "elazig", "sanliurfa", "diyarbakir", "antalya"]
AD = {"istanbul": "İstanbul", "ankara": "Ankara", "izmir": "İzmir", "bursa": "Bursa", "adana": "Adana",
      "kocaeli": "Kocaeli", "elazig": "Elazığ", "sanliurfa": "Şanlıurfa", "diyarbakir": "Diyarbakır",
      "antalya": "Antalya"}
TR = str.maketrans('İIıŞşĞğÜüÖöÇç', 'iiissgguuoocc')
K = ['tarih', 'hipodrom', 'kosu']


def tr_simdi():
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)


def getir(url):
    """Sayfayı indirir. 404 -> ''. Hata -> None (sonra tekrar denenir)."""
    for deneme in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            time.sleep(DELAY)
            if r.status_code == 404:
                return ""
            r.raise_for_status()
            r.encoding = r.apparent_encoding or "utf-8"
            return r.text
        except requests.RequestException as e:
            print("  hata, tekrar:", url, e)
            time.sleep(8 * (deneme + 1))
    return None


def sonuc_urls(t, hip):
    return [f"{BASE}/at-yarisi-sonuclar/at-yarisi-sonuclari-{hip}-{g}-{AYLAR[t.month-1]}-{t.year}"
            for g in (str(t.day), f"{t.day:02d}")]


def prog_url(t, hip):
    return f"{BASE}/at-yarisi/{hip}/{t.day}-{AYLAR[t.month-1]}-{t.year}-{GUNLER[t.weekday()]}"


def gunun_hipodromlari(t, ana_sayfa_html):
    """Ana sayfadaki program bağlantılarından o günün Türkiye hipodromları."""
    gun = f"{t.day}-{AYLAR[t.month-1]}-{t.year}"
    bul = re.findall(r"/at-yarisi/([a-z\-]+)/" + re.escape(gun) + r"-", ana_sayfa_html or "")
    return [h for h in TRH if h in set(bul)]


# ---------- sonuç sayfası ----------
def derece_saniye(s):
    p = str(s).strip().split(".")
    if len(p) == 3 and all(x.isdigit() for x in p):
        return int(p[0]) * 60 + int(p[1]) + int(p[2]) / 100
    return None


def to_float(s):
    try:
        return float(str(s).replace(",", ".").strip())
    except ValueError:
        return None


def parse_sonuc(html, tarih, hip):
    try:
        tablolar = pd.read_html(StringIO(html), thousands=None, converters={c: str for c in
                    ["Sıra", "No", "Atın Adı", "Jokey", "Kilo", "Derece", "Ganyan", "Hnd."]})
    except ValueError:
        return []
    satirlar, kosu_no = [], 0
    for t in tablolar:
        t.columns = [str(c).strip() for c in t.columns]
        if "Atın Adı" not in t.columns:
            continue
        kosu_no += 1
        for _, r in t.iterrows():
            jh = str(r.get("Jokey", ""))
            satirlar.append({"tarih": tarih, "hipodrom": hip, "kosu": kosu_no,
                "sira": pd.to_numeric(r.get("Sıra"), errors="coerce"),
                "no": pd.to_numeric(r.get("No"), errors="coerce"),
                "at": re.sub(r"\(\d+\)\s*$", "", str(r["Atın Adı"])).strip(),
                "jokey": jh.replace("APApranti", "").strip(), "apranti": "APApranti" in jh,
                "kilo": to_float(r.get("Kilo")), "derece_sn": derece_saniye(r.get("Derece")),
                "kosmadi": "Koşmaz" in str(r.get("Derece")), "ganyan": to_float(r.get("Ganyan")),
                "hnd": pd.to_numeric(r.get("Hnd."), errors="coerce")})
    return satirlar


# ---------- program sayfası ----------
PK = ["N", "At İsmi", "Yaş", "Orijin (Baba - Anne)", "Kilo", "Jokey", "Sahip", "Antrenör",
      "St", "HK", "Son 6 Y.", "KGS", "S20"]


def kosu_saatleri(html):
    """'5. Koşu 16.00' biçimindeki başlıklardan {kosu: 'SS:DD'}."""
    metin = BeautifulSoup(html, "lxml").get_text(" ")
    out = {}
    for m in re.finditer(r"(\d{1,2})\.\s*Koşu\s+(\d{1,2})[.:](\d{2})", metin):
        out.setdefault(int(m.group(1)), f"{int(m.group(2)):02d}:{m.group(3)}")
    return out


def kosu_bilgileri(html):
    """'ŞARTLI 4 , 2 Yaşlı İngilizler, 57 kg, 1400 Kum' satırlarından {kosu: kısa açıklama}."""
    metin = BeautifulSoup(html, "lxml").get_text("\n")
    out, son = {}, None
    for satir in metin.split("\n"):
        s = satir.strip()
        m = re.match(r"^(\d{1,2})\.\s*Koşu\b", s)
        if m:
            son = int(m.group(1))
            continue
        if son and son not in out and re.search(r"\d{3,4}\s*(Kum|Çim|Sentetik)", s):
            out[son] = re.sub(r"\s+", " ", s)[:120]
    return out


def parse_prog(html, tarih, hip):
    if not html:
        return []
    try:
        tablolar = pd.read_html(StringIO(html), converters={c: str for c in PK})
    except ValueError:
        return []
    out, kosu = [], 0
    for t in tablolar:
        t.columns = [str(c).strip() for c in t.columns]
        if "At İsmi" not in t.columns:
            continue
        kosu += 1
        for _, r in t.iterrows():
            jh = str(r.get("Jokey", ""))
            out.append({"tarih": tarih, "hipodrom": hip, "kosu": kosu,
                "no": pd.to_numeric(r.get("N"), errors="coerce"),
                "p_at": re.sub(r"\(\d+\)\s*$", "", str(r.get("At İsmi", ""))).strip(),
                "p_jokey": jh.replace("APApranti", "").strip(), "p_apranti": "APApranti" in jh,
                "p_kilo": to_float(r.get("Kilo")),
                "yas_ham": str(r.get("Yaş", "")).strip(),
                "baba": str(r.get("Orijin (Baba - Anne)", "")).strip(), "sahip": str(r.get("Sahip", "")).strip(),
                "antrenor": str(r.get("Antrenör", "")).strip(), "st": pd.to_numeric(r.get("St"), errors="coerce"),
                "hk": pd.to_numeric(r.get("HK"), errors="coerce"), "son6": str(r.get("Son 6 Y.", "")).strip(),
                "kgs": pd.to_numeric(r.get("KGS"), errors="coerce")})
    return out


# ---------- AGF (altılı havuzundaki oynanma yüzdesi) ----------
def parse_agf(html):
    """{hip: {altili_no: {ayak: {no: yuzde}}}} — yalnızca Türkiye hipodromları."""
    metin = BeautifulSoup(html, "lxml").get_text("\n")
    satirlar = [s.strip() for s in metin.split("\n") if s.strip()]
    out, hip, alt, ayak = {}, None, None, None
    for s in satirlar:
        sn = s.translate(TR).lower()
        m = re.search(r"(\d)\.\s*alt[iı]l[iı]", sn)
        if m:
            h = next((x for x in TRH if re.search(r"\b" + x + r"\b", sn)), None)
            if h:
                hip, alt, ayak = h, int(m.group(1)), None
                continue
            if not any(x in sn for x in TRH):
                # yabancı hipodrom başlığı
                if re.search(r"\d{1,2}:\d{2}", sn):
                    hip = None
                continue
        if re.fullmatch(r"(\d{1,2})\s*[./]?\s*(?:ayak)\b.*", sn):
            ayak = int(re.match(r"(\d{1,2})", sn).group(1))
            continue
        if hip and alt and ayak:
            for no, yuz in re.findall(r"(?<!\d)(\d{1,2})\s*\(\s*%\s*([\d.,]+)\s*\)", s):
                out.setdefault(hip, {}).setdefault(alt, {}).setdefault(ayak, {})[int(no)] = float(yuz.replace(",", "."))
    return out


def agf_kosulara(agf_hip, kosu_atlari):
    """Ayakları koşu numaralarına eşler. kosu_atlari: {kosu: set(no)}.
    Her altılı için başlangıç koşusunu, at numaralarının en iyi uyduğu kaydırmayla bulur."""
    out = {}
    n_kosu = max(kosu_atlari) if kosu_atlari else 0
    for alt, ayaklar in sorted(agf_hip.items()):
        en_iyi, en_puan = None, -1
        for bas in range(1, max(2, n_kosu - len(ayaklar) + 2)):
            puan = 0
            for ayak, d in ayaklar.items():
                kn = bas + ayak - 1
                if kn in kosu_atlari:
                    puan += len(set(d) & kosu_atlari[kn]) - 2 * len(set(d) - kosu_atlari[kn])
            if puan > en_puan:
                en_iyi, en_puan = bas, puan
        for ayak, d in ayaklar.items():
            out[en_iyi + ayak - 1] = d          # aynı koşu iki altılıda varsa sonuncusu (daha güncel) kalır
    return out


# ---------- piyasa olasılığı (ekürü düzeltmesi) ----------
def duzelt(g):
    g = g.copy()
    g['p_ham'] = 1 / g.ganyan
    toplam = g.p_ham.sum()
    if toplam > 1.5:
        for oran, grp in sorted(g.groupby('ganyan'), key=lambda x: x[0]):
            n = len(grp); r = 0
            while n - r > 1 and toplam > 1.5:
                toplam -= 1 / oran; r += 1
            if r:
                g.loc[grp.index, 'p_ham'] = (n - r) / n / oran
            if toplam <= 1.5:
                break
    g['p_piyasa'] = g.p_ham / g.p_ham.sum()
    return g


def temiz_yap(df):
    x = df[df.ganyan.notna() & (df.ganyan > 0)].copy().reset_index(drop=True)
    if x.empty:
        return x
    x = pd.concat([duzelt(g) for _, g in x.groupby(K)], ignore_index=True)
    x['kazandi'] = (x.sira == 1).astype(int)
    x['getiri'] = x.kazandi * x.ganyan - 1
    return x
