"""Son dakika değişikliklerini atyarisi API'sinden otomatik izler (26 Ekim 2026).
 - pist türü değişti (yağmur vb.): data/pist_degisiklik.csv'ye 'otomatik' satır eklenir -> calistir.pist_uygula bilgi metnini ve model puanlarını yeniler
 - jokey / koşmaz / kilo değişikliği: koşuya 'degisiklik' notu yazılır (jokey ve koşmaz zaten API'den jokey_uygula / kosmaz_isle ile işleniyor; puan yenileme orada)
Başlamış / sonuçlanmış koşulara dokunmaz. Elle girilen pist kaydı (kullanici) varsa API ile üzerine yazılmaz."""
import os, re, datetime
from . import ortak as O
from . import atyapi

VERI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_PIST = {"kum": "Kum", "cim": "Çim", "çim": "Çim", "sentetik": "Sentetik"}


def _norm(p):
    return _PIST.get(str(p or "").strip().lower().replace("İ", "i").replace("I", "ı"))


def _basladi(k, simdi):
    return bool(k.get("sonuc")) or bool(k.get("saat") and simdi >= k["saat"])


def pist_yaz(obj):
    """API'deki pist türü programdakinden (bilgi metni) farklıysa pist_degisiklik.csv'ye yazar. Döner: yazılan satır sayısı."""
    t = obj["tarih"]; simdi = O.tr_simdi().strftime("%H:%M")
    g = atyapi.gun(t)
    if not g:
        return 0
    yol = os.path.join(VERI, "pist_degisiklik.csv")
    var = {}
    if os.path.exists(yol):
        for l in open(yol, encoding="utf-8").read().split("\n")[1:]:
            p = l.split(",")
            if len(p) >= 4 and p[0] == t:
                var[(p[1], p[2])] = (p[3].strip(), l)
    yeni = []
    for h in obj["hipodromlar"]:
        v = g.get(h["id"])
        if not v:
            continue
        ak = {int(k["number"]): k for k in v["kosular"]}
        for k in h["kosular"]:
            if _basladi(k, simdi) or k["kosu"] not in ak:
                continue
            api_p = _norm(ak[k["kosu"]].get("raceCourseType"))
            m = re.search(r"(\d{3,4})\s*m?\s*(Kum|Çim|Sentetik)", k.get("bilgi") or "")
            if not api_p or not m:
                continue
            prog_p = m.group(2)
            kayit = var.get((h["id"], str(k["kosu"])))
            if kayit:
                if "otomatik" not in kayit[1]:
                    continue                                   # elle girilmiş kayıt öncelikli
                if kayit[0] == api_p:
                    continue
            if api_p != prog_p:
                yeni.append(f"{t},{h['id']},{k['kosu']},{api_p},otomatik atyarisi API ({prog_p} -> {api_p}),{simdi}")
    if yeni:
        yeni_dosya = not os.path.exists(yol)
        with open(yol, "a", encoding="utf-8") as fh:
            if yeni_dosya:
                fh.write("tarih,hipodrom,kosu,pist,bildiren,saat_tr\n")
            fh.write("\n".join(yeni) + "\n")
        print("pist değişikliği (otomatik):", len(yeni), yeni)
    return len(yeni)


def mesafe_yaz(obj):
    """API'deki mesafe programdakinden (bilgi metni) farklıysa data/mesafe_degisiklik.csv'ye yazar (30 Ekim 2026). Elle (kullanici) kayıt öncelikli.
    calistir.pist_uygula bu dosyayı da okur: bilgi metnindeki mesafeyi düzeltir, model puanlarını yeniler. Döner: yazılan satır sayısı."""
    t = obj["tarih"]; simdi = O.tr_simdi().strftime("%H:%M")
    g = atyapi.gun(t)
    if not g:
        return 0
    yol = os.path.join(VERI, "mesafe_degisiklik.csv")
    var = {}
    if os.path.exists(yol):
        for l in open(yol, encoding="utf-8").read().split("\n")[1:]:
            p = l.split(",")
            if len(p) >= 4 and p[0] == t:
                var[(p[1], p[2])] = (p[3].strip(), l)
    yeni = []
    for h in obj["hipodromlar"]:
        v = g.get(h["id"])
        if not v:
            continue
        ak = {int(k["number"]): k for k in v["kosular"]}
        for k in h["kosular"]:
            if _basladi(k, simdi) or k["kosu"] not in ak:
                continue
            d = str(ak[k["kosu"]].get("distance") or "").strip()
            m = re.search(r"(\d{3,4})\s*m?\s*(Kum|Çim|Sentetik)", k.get("bilgi") or "")
            if not d.isdigit() or not m:
                continue
            kayit = var.get((h["id"], str(k["kosu"])))
            if kayit:
                if "otomatik" not in kayit[1] or kayit[0] == d:
                    continue
            if d != m.group(1):
                yeni.append(f"{t},{h['id']},{k['kosu']},{d},otomatik atyarisi API ({m.group(1)} -> {d}),{simdi}")
    if yeni:
        yeni_dosya = not os.path.exists(yol)
        with open(yol, "a", encoding="utf-8") as fh:
            if yeni_dosya:
                fh.write("tarih,hipodrom,kosu,mesafe,bildiren,saat_tr\n")
            fh.write("\n".join(yeni) + "\n")
        print("mesafe değişikliği (otomatik):", len(yeni), yeni)
    return len(yeni)


def notlar(obj):
    """Her başlamamış koşu için 'degisiklik' listesi (UI'da gösterilir): pist, jokey, koşmaz, kilo."""
    t = obj["tarih"]; simdi = O.tr_simdi().strftime("%H:%M")
    g = atyapi.gun(t)
    if not g:
        return 0
    n = 0
    PD = {}
    yol = os.path.join(VERI, "pist_degisiklik.csv")
    if os.path.exists(yol):
        for l in open(yol, encoding="utf-8").read().split("\n")[1:]:
            p = l.split(",")
            if len(p) >= 4 and p[0] == t:
                PD[(p[1], p[2])] = p[3].strip()
    for h in obj["hipodromlar"]:
        v = g.get(h["id"])
        if not v:
            continue
        ak = {int(k["number"]): k for k in v["kosular"]}
        for k in h["kosular"]:
            k.pop("degisiklik", None)
            ar = ak.get(k["kosu"])
            if not ar or _basladi(k, simdi):
                continue
            L = []
            if str(ar.get("raceCourseChanged") or "").strip():
                L.append("Pist değişti: " + str(ar.get("raceCourseChanged")).strip())
            if str(ar.get("distanceChanged") or "").strip():
                L.append("Mesafe değişti: " + str(ar.get("distanceChanged")).strip())
            pk = PD.get((h["id"], str(k["kosu"])))
            if pk:
                L.append("Pist " + {"Kum": "kuma", "Çim": "çime", "Sentetik": "sentetiğe"}.get(pk, pk) + " alındı (model puanları yenilendi)")
            nm = {a["no"]: a for a in k["atlar"]}
            for a in ar.get("horses") or []:
                no = int(a["number"]); x = nm.get(no)
                if x is None:
                    continue
                if a.get("status") is False:
                    L.append(f"Koşmaz: {no} {x.get('at','')}")
                    continue
                j = a.get("jockey") or {}
                if j.get("isJockeyChanged") and j.get("oldJockeyName"):
                    L.append(f"Jokey: {no} {x.get('at','')} {j['oldJockeyName']} → {j.get('name','')}")
                try:
                    kg = float(a.get("weight"))
                    if x.get("kg") and abs(float(x["kg"]) - kg) >= 0.5:
                        L.append(f"Kilo: {no} {x.get('at','')} {x['kg']:g} → {kg:g}")
                except Exception:
                    pass
            if L:
                k["degisiklik"] = L; n += len(L)
    if n:
        print("son dakika değişiklik notu:", n)
    return n


def kilo_isaretle(obj):
    """API'deki kilo programdakinden >=0,5 kg farklıysa atın kilosunu günceller ve koşuyu 'yeniden_puan' ile işaretler:
    calistir.pist_uygula bu koşunun z/z2/z3/z4/z5/zj puanlarını (API kilosuyla) yeniden hesaplar, z6 sonra doldurulur. Başlamış koşulara dokunmaz."""
    t = obj["tarih"]; simdi = O.tr_simdi().strftime("%H:%M")
    g = atyapi.gun(t)
    if not g:
        return 0
    obj["_kilo"] = {}
    n = 0
    for h in obj["hipodromlar"]:
        v = g.get(h["id"])
        if not v:
            continue
        ak = {int(k["number"]): k for k in v["kosular"]}
        for k in h["kosular"]:
            ar = ak.get(k["kosu"])
            if not ar or _basladi(k, simdi):
                continue
            nm = {a["no"]: a for a in k["atlar"]}
            ch = False
            for a in ar.get("horses") or []:
                x = nm.get(int(a["number"]))
                if x is None or a.get("status") is False:
                    continue
                try:
                    kg = float(a.get("weight"))
                except Exception:
                    continue
                if x.get("kg") and abs(float(x["kg"]) - kg) >= 0.5:
                    obj["_kilo"][(h["id"], k["kosu"], x["no"])] = kg
                    x["kg"] = kg; ch = True; n += 1
            if ch:
                k["yeniden_puan"] = True
    if n:
        print("kilo değişikliği (otomatik):", n)
    return n


def ekur_isaretle(obj):
    """Ekür (aynı sahibin ortak oranlı atları) grup numarasını atlara 'ek' olarak yazar (atyarisi 'stablemate'); T34 ileri gölge için kayıt amaçlı, model kullanmaz."""
    g = atyapi.gun(obj["tarih"])
    if not g:
        return 0
    n = 0
    for h in obj["hipodromlar"]:
        v = g.get(h["id"])
        if not v:
            continue
        ak = {int(k["number"]): k for k in v["kosular"]}
        for k in h["kosular"]:
            ar = ak.get(k["kosu"])
            if not ar:
                continue
            nm = {a["no"]: a for a in k["atlar"]}
            for a in ar.get("horses") or []:
                try:
                    sm = int(a.get("stablemate") or 0); x = nm.get(int(a["number"]))
                except Exception:
                    continue
                if x is not None and sm > 0 and x.get("ek") != sm:
                    x["ek"] = sm; n += 1
    return n


def pist_durum_yaz(obj):
    """Pist durumu (ağır/yumuşak/nemli... + ağırlık, örn. Çim Yumuşak 3,4): API'den okur, obj['pist_durumu']'na yazar (UI) ve data/pist_durum.csv'ye yeni değerleri ekler.
    Model şimdilik kullanmıyor (kayıt/analiz amaçlı)."""
    t = obj["tarih"]; simdi = O.tr_simdi().strftime("%H:%M")
    try:
        pdur = atyapi.pist_durumlari(t)
    except Exception as e:
        print("pist durumu hatası:", repr(e)); return 0
    obj["pist_durumu"] = pdur
    if not pdur:
        return 0
    yol = os.path.join(VERI, "pist_durum.csv")
    var = set()
    if os.path.exists(yol):
        for l in open(yol, encoding="utf-8").read().split("\n")[1:]:
            p = l.split(",")
            if len(p) >= 4 and p[0] == t:
                var.add((p[1].lower(), p[2].lower().replace("ç", "c"), p[3].strip().lower()))
    TR = str.maketrans("ÇçİıŞşĞğÜüÖö", "CcIiSsGgUuOo")
    yeni = []
    for hid, L in pdur.items():
        for c in L:
            durum = f"{c['durum']} {c['agirlik']}".strip() if c.get("agirlik") else c["durum"]
            key = (hid.translate(TR).lower(), str(c["pist"]).translate(TR).lower(), durum.translate(TR).lower())
            if any(key[0] == v[0] and key[1] == v[1] and key[2] == v[2] for v in var):
                continue
            var.add(key)
            yeni.append(f"{t},{hid.capitalize()},{str(c['pist']).translate(TR)},{durum.translate(TR)},otomatik atyarisi API,{simdi}")
    if yeni:
        yeni_dosya = not os.path.exists(yol)
        with open(yol, "a", encoding="utf-8") as fh:
            if yeni_dosya:
                fh.write("tarih,hipodrom,pist,durum,bildiren,saat_tr\n")
            fh.write("\n".join(yeni) + "\n")
        print("pist durumu (otomatik):", yeni)
    return len(yeni)
