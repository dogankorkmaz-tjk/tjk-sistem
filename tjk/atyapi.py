"""atyarisi.com (TJK resmî çevrimiçi portalı) program API'si: günün programı, atlar, jokey, kilo, HP, Son 6, AGF, bahis türleri.
robots.txt izin veriyor, llms.txt otomatik kullanıma açık (23 Ekim 2026). Gün başına hipodrom sayısı kadar küçük istek; süreç içinde önbelleklenir.
Yalnızca Türkiye hipodromları; CSV yüklemeye gerek bırakmaz, CSV yedek olarak kalır."""
import re, requests
from . import ortak as O

LISTE = "https://tjkbulten.atyarisi.com/api/v1/ProgramHippodromes"
DETAY = "https://tjkbulten.atyarisi.com/api/v2/ProgramDetails"
_H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36", "Accept": "application/json",
      "Origin": "https://www.atyarisi.com", "Referer": "https://www.atyarisi.com/"}
_ONBELLEK = {}
_LISTE = {}          # {tarih: {hipodrom: {'raceCourse': [{type,status,weight}], 'weather': {...}}}} (pist durumu ve hava; gun() ile birlikte alınır)


def _sn(s):
    m = re.match(r"^\s*(\d+)[.:](\d{2})[.](\d{1,2})\s*$", str(s or ""))
    return int(m.group(1)) * 60 + int(m.group(2)) + float("0." + m.group(3)) if m else None


def _hip(ad):
    k = str(ad or "").strip().translate(O.TR).lower()
    for h, a in O.AD.items():
        if a.translate(O.TR).lower() == k or h == k:
            return h
    return None


def gun(tarih, yenile=False):
    """-> {hipodrom: {"saat0": ..., "kosular": [API koşu sözlükleri]}}; erişilemezse {} (önbellekte boş kalmaz)."""
    if tarih in _ONBELLEK and not yenile:
        return _ONBELLEK[tarih]
    out = {}
    try:
        r = requests.get(LISTE, params={"date": tarih}, headers=_H, timeout=30)
        for h in (r.json().get("d") or []):
            hi = h.get("hippodrome") or {}
            if hi.get("isForeign"):
                continue
            hid = _hip(hi.get("place")) or _hip(hi.get("code"))
            if not hid or hid not in O.TRH:
                continue
            _LISTE.setdefault(tarih, {})[hid] = {"raceCourse": h.get("raceCourse") or [], "weather": h.get("weather") or {}}
            rr = requests.get(DETAY, params={"programId": h["id"]}, headers=_H, timeout=30)
            ko = (rr.json().get("d") or {}).get("races") or []
            if ko:
                out[hid] = {"kosular": ko}
    except Exception as e:
        print("atyarisi API hatası:", repr(e))
        return {}
    if out:
        _ONBELLEK[tarih] = out
    return out


def _pist_harf(p):
    return {"Kum": "K", "Çim": "Ç", "Sentetik": "S"}.get(p, "K")


def program_satirlari(tarih):
    """csvprog.program_satirlari ile aynı biçim: (satırlar, {hip: {"saat","bilgi"}}, {(hip,kosu,no): AGF %})"""
    from .csvprog import bilgi_metni
    satirlar, programlar, agf = [], {}, {}
    for hip, v in gun(tarih).items():
        saat, bilgi = {}, {}
        for k in v["kosular"]:
            kn = int(k["number"])
            saat[kn] = k.get("hour"); bilgi[kn] = bilgi_metni(_kosu(k))
            for a in k.get("horses") or []:
                no = int(a["number"])
                j = a.get("jockey") or {}
                son6 = "".join(_pist_harf(x.get("raceCourseType")) + str(x.get("result", "")) for x in (a.get("last6") or []))
                p = a.get("parents") or {}
                satirlar.append({"tarih": tarih, "hipodrom": hip, "kosu": kn, "no": no, "p_at": a["name"].strip(),
                                 "p_jokey": (j.get("name") or "").strip(), "p_apranti": bool(j.get("apprentice")),
                                 "p_kilo": a.get("weight"), "yas_ham": re.sub(r"\s+", " ", a.get("age") or "").strip(),
                                 "baba": f"{(p.get('father') or {}).get('name','')} - {(p.get('mother') or {}).get('name','')}",
                                 "sahip": (a.get("owner") or {}).get("name", ""), "antrenor": (a.get("coach") or {}).get("name", ""),
                                 "st": float(a["start"]) if a.get("start") is not None else float("nan"),
                                 "hk": float(a["handicap"]) if str(a.get("handicap") or "").isdigit() else float("nan"),
                                 "son6": son6, "kgs": float(a["kgs"]) if a.get("kgs") is not None else float("nan")})
                ag = _agf(a)
                if ag is not None:
                    agf[(hip, kn, no)] = ag
        programlar[hip] = {"saat": saat, "bilgi": bilgi}
    return satirlar, programlar, agf


def _agf(a):
    L = a.get("agf") or []
    return float(L[-1]["percentage"]) if L and L[-1].get("percentage") is not None else None


def _kosu(k):
    b = k.get("bets") or ""
    pr = k.get("prizes") or []
    bg = k.get("bestGrade")
    return {"saat": k.get("hour"), "cins": k.get("typeDescription"), "yas": k.get("groupName"),
            "mesafe": int(k["distance"]) if str(k.get("distance") or "").isdigit() else None, "pist": k.get("raceCourseType"),
            "rekor_sn": _sn(bg), "ikramiye1": int(pr[0]) if pr else None,
            "besli": "SIRALI 5" in b, "uclu": "ÜÇLÜ BAHİS" in b, "tabela": "TABELA BAHİS" in b}


def gunun(tarih):
    """csvprog.gunun biçimi: {hip: (kosular, atlar, ekur)}"""
    out = {}
    for hip, v in gun(tarih).items():
        kosular, atlar, ekur = {}, {}, set()
        for k in v["kosular"]:
            kn = int(k["number"]); kosular[kn] = _kosu(k); atlar[kn] = {}
            for a in k.get("horses") or []:
                no = int(a["number"]); bg = a.get("bestGrade") or {}
                atlar[kn][no] = {"hnd": int(a["handicap"]) if str(a.get("handicap") or "").isdigit() else None,
                                 "eid_sn": _sn(bg.get("value") if isinstance(bg, dict) else bg),
                                 "kilo": a.get("weight"), "kilo_fark": float(a.get("overweight") or 0.0)}
                if (a.get("stablemate") or 0) > 0:
                    ekur.add((kn, no))
        out[hip] = (kosular, atlar, ekur)
    return out


def jokeyler(tarih):
    out = {}
    for hip, v in gun(tarih).items():
        for k in v["kosular"]:
            for a in k.get("horses") or []:
                j = a.get("jockey") or {}
                if j.get("name"):
                    out[(hip, int(k["number"]), int(a["number"]))] = j["name"].strip() + (" AP" if j.get("apprentice") else "")
    return out


def kosmazlar(tarih):
    return {(hip, int(k["number"]), int(a["number"])) for hip, v in gun(tarih).items() for k in v["kosular"]
            for a in k.get("horses") or [] if a.get("status") is False}


def agf_uygula(obj, saat):
    """agftablosu engelliyse güncel AGF'yi API'den atlara yazar (agf = son değer, agf0 = ilk görülen)."""
    n = 0
    g = gun(obj["tarih"])
    for h in obj["hipodromlar"]:
        v = g.get(h["id"])
        if not v:
            continue
        ko = {int(k["number"]): k for k in v["kosular"]}
        for k in h["kosular"]:
            ak = ko.get(k["kosu"])
            if not ak or k.get("sonuc"):
                continue
            haritalar = {int(a["number"]): _agf(a) for a in ak.get("horses") or []}
            gor = False
            for a in k["atlar"]:
                x = haritalar.get(a["no"])
                if x is None:
                    continue
                a["agf"] = x; gor = True; n += 1
                if a.get("agf0") is None:
                    a["agf0"] = x
                if a.get("agf_a1") is None:
                    a["agf_a1"] = x
            if gor:
                k["agf_saat"] = saat; k.setdefault("agf0_saat", saat)
    if n:
        print("AGF atyarisi API'sinden eklendi:", n, "at")
    return n


RESULT = "https://tjkbulten.atyarisi.com/api/v4/RaceResult"
_SON = {}


def sonuc_gun(tarih):
    """{hipodrom: [API koşu sözlükleri (atlar sıra/derece/kapanış ganyanı + raceMoneys: tüm bahislerin ikramiyesi)]}"""
    if tarih in _SON:
        return _SON[tarih]
    out = {}
    try:
        for h in (requests.get(LISTE, params={"date": tarih}, headers=_H, timeout=30).json().get("d") or []):
            hi = h.get("hippodrome") or {}
            hid = None if hi.get("isForeign") else (_hip(hi.get("place")) or _hip(hi.get("code")))
            if not hid or hid not in O.TRH:
                continue
            out[hid] = (requests.get(RESULT, params={"programId": h["id"]}, headers=_H, timeout=30).json().get("d") or {}).get("races") or []
    except Exception as e:
        print("atyarisi sonuç hatası:", repr(e))
        return {}
    if out:
        _SON[tarih] = out
    return out


def sonuc_df(t, hid):
    """calistir.muh_sonuc_df ile aynı sütunlar: tarih, hipodrom, kosu, sira, no, ganyan, kosmadi (yalnızca sonucu belli koşular)."""
    import pandas as pd
    satir = []
    for k in sonuc_gun(t.isoformat()).get(hid, []):
        hs = k.get("horses") or []
        if not any((a.get("order") or 0) > 0 for a in hs):
            continue
        for a in hs:
            g = a.get("ganyan")
            if g and (a.get("order") or 0) > 0:
                satir.append({"tarih": t.isoformat(), "hipodrom": hid, "kosu": int(k["number"]), "sira": int(a["order"]),
                              "no": int(a["number"]), "ganyan": float(g), "kosmadi": False})
    return pd.DataFrame(satir)


_TUR = {"GANYAN", "İKİLİ", "SIRALI İKİLİ", "ÜÇLÜ BAHİS", "TABELA BAHİS", "TABELA BAHİS SIRASIZ", "SIRALI 5 Lİ BAHİS", "PLASE", "PLASE İKİLİ"}


def odeme_yaz(tarih):
    """Sonucu belli koşuların bahis ikramiyelerini data/odeme/YYYY-MM.csv.gz içine (TJK CSV'siyle aynı biçimde) ekler; CSV'den gelen satırlara dokunmaz.
    Böylece egzotik/tabela/sıralı-5 değerlendirmeleri CSV yüklenmeden de çalışır."""
    import os, pandas as pd
    from .sonuccsv import _yaz, KOK
    rows = []
    for hip, ko in sonuc_gun(tarih).items():
        for k in ko:
            if not any((a.get("order") or 0) > 0 for a in (k.get("horses") or [])):
                continue
            for m in k.get("raceMoneys") or []:
                tur = str(m.get("betTypeName") or "").strip().upper().replace("İ", "İ")
                try:
                    tutar = float(str(m.get("prizeText") or "0").replace(".", "").replace(",", "."))
                except ValueError:
                    continue
                if tur in _TUR and m.get("result") and tutar > 0:
                    rows.append({"tarih": tarih, "hipodrom": hip, "kosu": int(k["number"]), "tur": tur, "seq": 0, "kombo": str(m["result"]).strip(), "tutar": tutar})
    if not rows:
        return 0
    yol = os.path.join(KOK, "odeme", tarih[:7] + ".csv.gz")
    if os.path.exists(yol):
        var = pd.read_csv(yol); var = var[var.tarih == tarih]
        anahtar = set(zip(var.hipodrom, var.kosu, var.tur))
        rows = [r for r in rows if (r["hipodrom"], r["kosu"], r["tur"]) not in anahtar]
    if not rows:
        return 0
    # aynı tür birden fazla satırsa (PLASE) seq numaralanır
    sayac = {}
    for r in rows:
        a = (r["hipodrom"], r["kosu"], r["tur"]); r["seq"] = sayac.get(a, 0); sayac[a] = r["seq"] + 1
    n = _yaz("odeme", pd.DataFrame(rows), ["tarih", "hipodrom", "kosu", "tur", "seq", "kombo"])
    print("atyarisi ikramiyeleri eklendi:", tarih, n, "satır")
    return n


def pist_durumlari(tarih):
    """-> {hipodrom: [{"pist": "Çim", "durum": "Yumuşak", "agirlik": 3.4}]} (yalnız durumu yazılmış pistler); gun() çağrılmış olmalı."""
    gun(tarih)
    out = {}
    for hid, v in (_LISTE.get(tarih) or {}).items():
        L = [{"pist": c.get("type"), "durum": str(c.get("status") or "").strip(), "agirlik": c.get("weight")} for c in v["raceCourse"] if str(c.get("status") or "").strip()]
        if L:
            out[hid] = L
    return out
