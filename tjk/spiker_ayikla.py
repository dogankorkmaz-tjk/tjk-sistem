"""Spiker transkriptinden (tjk/spiker.py çıktısı) at düzeyi olay ve konum çıkarımı.
olaylar(seg) → {no: [(tür, sn, boy|None, metin), ...]}; konum(seg, sure) → {no: {"erken": sıra, "orta": sıra, "gec": sıra}} (ilk anılış sırası, pencere içinde).
Kural tabanlı; doğruluk resmî delayedExit ve video şeridiyle ölçülür (data/analiz/spiker_dogrula.py)."""
import re

SAYI = {"bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6, "altın": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10,
        "on bir": 11, "on iki": 12, "on üç": 13, "on dört": 14, "on beş": 15, "on altı": 16, "on yedi": 17, "on sekiz": 18}
_K = "|".join(sorted((re.escape(k) for k in SAYI), key=len, reverse=True))
NO_RE = re.compile(rf"(?<![\w,.])(\d{{1,2}}|{_K})\s*(?:numara\w*|nolu|no\.?|maradı|ma(?=\s))", re.I)
BOY_RE = re.compile(rf"(\d{{1,2}}(?:[.,]5)?|{_K}|yarım|bir buçuk|iki buçuk)\s*(?:[-–,]\s*(?:\d{{1,2}}|{_K})\s*)?boy", re.I)
TUR = [
    ("gec_cikis", r"geç başla|geç çık|oyalan|ancak başla|başlayamad|yarışa başlamad|start\w* kaçır|kötü çık|kötü başla|startta kald|geriden başla|çıkışta kald|geriye düş|geride kald|çıkamad|başlayabild|gecik|ağır al|geç kald|sonra koşuya|sonra başla"),
    ("avantaj_kaybi", r"avantaj kaybet|boy kaybet|zemin kaybet"),
    ("sikisma", r"sıkış|önü kapan|yol bulama|kapalı kald|arada kald|çekilmek zorunda|sert çekil|etkilen|engellen|önünü kes|çarp"),
    ("dis_acilma", r"dışa açıl|dışı açıl|dışarı açıl|dışa doğru açıl|dışarıya açıl|geniş dön|dışa kaç|dışarı kaç"),
    ("dusme_tokezleme", r"tökezle|jokeyini düşür|jokey\w* düş|attan düş|yere düş|binicisini|eyerden|jokeysiz|yere bırak|eyer kay|sendele|yarışı tamamlayamad|yarıştan kopt|başıboş|binicisiz|jokeysiz koş"),
    ("huysuz", r"huysuz|şahlan|dik dur|yüklenmek istemed"),
    ("lehine", r"boşluk bul|yol açıl|yolu açıl|rakipsiz|zorlanmadan|rahat önde|rahat koş|kimse zorlamad|tek başına önde|baskısız"),   # T161 (6 Kasım 23:25): lehine akış
]
SORUN = {"gec_cikis", "avantaj_kaybi", "sikisma", "dis_acilma", "dusme_tokezleme", "huysuz"}   # "lehine" sorun değildir
TUR = [(a, re.compile(b, re.I)) for a, b in TUR]


def kucuk(t):
    """Türkçe küçük harf (Python 'İ'.lower() → 'i̇' bozulmasını önler)."""
    return t.replace("İ", "i").replace("I", "ı").lower()


def _no(s):
    s = kucuk(s).strip()
    return int(s) if s.isdigit() else SAYI.get(s)


def _boy(t):
    m = BOY_RE.search(kucuk(t))
    if not m: return None
    s = m.group(1).lower().replace(",", ".")
    if s == "yarım": return 0.5
    if s == "bir buçuk": return 1.5
    if s == "iki buçuk": return 2.5
    try: return float(s)
    except ValueError: return float(SAYI.get(s, 0)) or None


def anilanlar(t):
    t = kucuk(t)
    return [(m.start(), _no(m.group(1))) for m in NO_RE.finditer(t) if _no(m.group(1))]


START_SN = 25.0          # geç çıkış yalnız koşunun ilk 25 sn'sinde (start anlatımı; sonradan "geriye düştü" yarış içi gerilemedir)
COK_AT = {"gec_cikis", "avantaj_kaybi"}   # bu türlerde cümlede olaydan önce anılan TÜM atlar (spiker birden çok atı tek cümlede sayar)


def _cumleler(seg):
    """Segmentleri birleştirip cümlelere böler (segment sınırı cümleyi bölebiliyor); her cümle (başlangıç sn, metin)."""
    out, buf, t0 = [], "", None
    for s, e, t in seg:
        for parca in re.split(r"(?<=[.!?])\s+", t.strip()):
            if not parca: continue
            if t0 is None: t0 = s
            buf = (buf + " " + parca).strip()
            if re.search(r"[.!?]$", parca):
                out.append((t0, buf)); buf, t0 = "", None
    if buf: out.append((t0, buf))
    return out


def _jokey_anilan(t, jokeyler):
    """Cümlede jokey soyadı geçen (≥4 harf) atlar: [(konum, no)]. jokeyler: {no: 'V.ABİŞ' / 'VEDAT ABİŞ'}."""
    out = []
    for no, ad in (jokeyler or {}).items():
        soy = kucuk(str(ad)).replace(".", " ").split()
        if not soy or len(soy[-1]) < 4: continue
        for m in re.finditer(rf"\b{re.escape(soy[-1])}", t):
            out.append((m.start(), no))
    return out


START_RAKIP = re.compile(r"rakipler\w*.{0,40}?boy.{0,30}?(geri|sonra|gecik|gel)", re.I)   # start anlatımında "rakiplerinin N boy gerisinde/sonra"


def _ad_anilan(t, adlar):
    """At adı (ilk ≥4 harfli sözcüğü) geçen konumlar: [(konum, no)]; numarasız anılan atlar için. adlar: {no: 'RENES PAŞA'}."""
    out = []
    for no, ad in (adlar or {}).items():
        w = [x for x in kucuk(str(ad)).split() if len(x) >= 4]
        if not w: continue
        for m in re.finditer(rf"\b{re.escape(w[0])}", t):
            out.append((m.start(), no))
    return out


def olaylar(seg, gecerli=None, jokeyler=None, adlar=None):
    """gecerli: koşan at numaraları kümesi. Olay ifadesi cümle içinde kendinden ÖNCE anılan ata bağlanır (COK_AT türlerinde hepsine, her birinin
    kendinden sonraki ilk 'N boy' miktarıyla); cümlede at yoksa bir önceki cümlenin son anılan atına."""
    out = {}; onceki = None
    for s, t in _cumleler(seg):
        t = kucuk(t)
        A = sorted([(p, n) for p, n in anilanlar(t) if not gecerli or n in gecerli] + _jokey_anilan(t, jokeyler) + _ad_anilan(t, adlar))
        for tur, rx in TUR:
            if tur == "gec_cikis" and s > START_SN: continue
            M = list(rx.finditer(t))
            if tur == "gec_cikis" and not M: M = list(START_RAKIP.finditer(t))
            for m in M:
                aday = [(p, n) for p, n in A if p < m.start()]
                if not aday:
                    if onceki is None: continue
                    aday = [(0, onceki)]
                if tur not in COK_AT: aday = aday[-1:]
                for i, (p, n) in enumerate(aday):
                    son = aday[i + 1][0] if i + 1 < len(aday) else len(t)
                    out.setdefault(n, []).append((tur, s, _boy(t[p:son + 1]), t))
        if A: onceki = A[-1][1]
    for n in out:                                   # start bölümündeki avantaj kaybı / dışa açılma → start sorunu olarak da işaretlenir
        if any(o[0] in ("avantaj_kaybi", "dis_acilma") and o[1] <= START_SN for o in out[n]) and not any(o[0] == "gec_cikis" for o in out[n]):
            o = [o for o in out[n] if o[0] in ("avantaj_kaybi", "dis_acilma") and o[1] <= START_SN][0]; out[n].append(("gec_cikis", o[1], o[2], o[3]))
    for n in out:                                   # aynı at, aynı tür tekrarı (ör. bölünmüş cümle) → bir kez
        g = {}; [g.setdefault(o[0], o) for o in out[n]]; out[n] = list(g.values())
    return out


def konum(seg, sure, gecerli=None):
    """Pencere içinde ilk anılış sırası → sıra (1 = ilk anılan). Pencereler sürenin %0–35 / 35–65 / 65–90'ı (son %10 bitiş özeti; atlanır)."""
    P = {"erken": (0.0, 0.35), "orta": (0.35, 0.65), "gec": (0.65, 0.90)}; out = {}
    for ad, (a, b) in P.items():
        sira = []
        for s, t in _cumleler(seg):
            if not (a * sure <= s < b * sure): continue
            t = kucuk(t)
            if any(rx.search(t) for a_, rx in TUR if a_ in SORUN): continue   # sorun cümleleri (geç çıkış vb.) sıra anlatımı değildir
            for p, n in anilanlar(t):
                if (not gecerli or n in gecerli) and n not in sira: sira.append(n)
        for i, n in enumerate(sira, 1):
            out.setdefault(n, {})[ad] = i
    return out
