"""Sıralı 5'li kombine kupon: kağıt üstü takip. Her koşu (>=5 at) için Bolton ve Jason kuponları (~48 ve ~96 kombinasyon) yarış başlamadan dondurulur;
koşu bitince ilk beş sıraya göre değerlendirilir, ödeme data/odeme'deki 'SIRALI 5 Lİ BAHİS' satırından alınır (DEVİR satırı = bilen yok).
Öneri kuralı (önceden yazıldı, sonradan değişmez): modelin tutma olasılığı / piyasa (AGF) tutma olasılığı >= ESIK_ORAN.
Birim 1,25 TL. Devir bilgisi kullanılmaz."""
import os, json, glob, math, itertools
import pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data", "besli"), os.path.join(KOK, "docs", "data")
G_M = [1, 0.80, 0.69, 0.69, 0.69]
G_P = [1, 0.87, 0.74, 0.74, 0.74]
BUTCELER = (48, 96)
BUTCELER_G = (48, 96, 150)   # -G varyantları: geçerli kombinasyon sayısı (150 eklendi 13 Ekim 2026, 16:10)
ESIK_ORAN = 1.15
BIRIM = 1.25


def _prob(W, T, sets):
    top = 0.0
    for tup in itertools.product(*sets):
        if len(set(tup)) < 5:
            continue
        pr = 1.0; used = []
        for k, h in enumerate(tup):
            den = T[k] - sum(W[k][u] for u in used)
            if den <= 1e-12:
                pr = 0.0; break
            pr *= W[k][h] / den; used.append(h)
        top += pr
    return top


def _W(p, G):
    W = [[max(v, 1e-9) ** g for v in p] for g in G]
    return W, [sum(w) for w in W]


def gecerli_say(sets):
    """Makine yalnız beş ayrı atlı kombinasyonları sayar/ücretlendirir (13 Ekim 2026 makine fişiyle doğrulandı: 110 geçerli = 137,50 TL, çarpım 336)."""
    return sum(1 for tup in itertools.product(*sets) if len(set(tup)) == 5)


def _acgozlu_g(p, B, sets, G=None):
    """Verilen başlangıç kümelerinden açgözlü genişletme; bütçe geçerli kombinasyon sayısına göre."""
    n = len(p)
    W, T = _W(p, G or G_M)
    ord_ = sorted(range(n), key=lambda i: -p[i]); aday = ord_[:min(n, 9)]
    sets = [list(x) for x in sets]
    cur = _prob(W, T, sets); nv = gecerli_say(sets)
    for _ in range(60):
        best = None; bg = 0.0
        for k in range(5):
            for h in aday:
                if h in sets[k]:
                    continue
                sets[k].append(h); v2 = gecerli_say(sets)
                if v2 > B or v2 <= nv:
                    sets[k].pop(); continue
                pr = _prob(W, T, sets); sets[k].pop()
                g = math.log(pr / cur) / math.log(v2 / nv)
                if g > bg:
                    bg, best = g, (k, h, pr, v2)
        if not best:
            break
        sets[best[0]].append(best[1]); cur = best[2]; nv = best[3]
    return sets, cur


def kupon_g(p, B, G=None):
    """Çok başlangıçlı açgözlü kurucu (sürüm 2, 13 Ekim 2026 16:30): ilk iki sıra için tek yönlü ve iki yönlü başlangıçlardan en iyisi.
    Tek başlangıçlı açgözlü, favori çifti iki yönlü açmayı (6,7/6,7) göremiyordu; aynı maliyette %8 daha düşük tutma veriyordu."""
    n = len(p)
    if n < 5:
        return None
    t = sorted(range(n), key=lambda i: -p[i])
    W, T = _W(p, G or G_M)
    baslangic = [[[t[0]], [t[1]], [t[2]], [t[3]], [t[4]]],
                 [[t[0], t[1]], [t[0], t[1]], [t[2]], [t[3]], [t[4]]],
                 [[t[0], t[1]], [t[0], t[1]], [t[2], t[3]], [t[2], t[3]], [t[4]]]]
    en = None
    for st in baslangic:
        if not (0 < gecerli_say(st) <= B):
            continue
        sets, pr = _acgozlu_g(p, B, st, G)
        if en is None or pr > en[1] + 1e-12:
            en = (sets, pr)
    return en


def kupon(p, B):
    n = len(p)
    if n < 5:
        return None
    W, T = _W(p, G_M)
    ord_ = sorted(range(n), key=lambda i: -p[i]); aday = ord_[:min(n, 9)]
    sets = [[ord_[k]] for k in range(5)]
    cur = _prob(W, T, sets)
    for _ in range(60):
        nn = math.prod(len(s) for s in sets); best = None; bg = 0.0
        for k in range(5):
            if nn // len(sets[k]) * (len(sets[k]) + 1) > B:
                continue
            for h in aday:
                if h in sets[k]:
                    continue
                sets[k].append(h); pr = _prob(W, T, sets); sets[k].pop()
                g = math.log(pr / cur) / math.log((len(sets[k]) + 1) / len(sets[k]))
                if g > bg:
                    bg, best = g, (k, h, pr)
        if not best:
            break
        sets[best[0]].append(best[1]); cur = best[2]
    return sets, cur


G1V = {"s": None}   # G1-S sürümü (v2/v3): -G kuponlara damga, eski sürümlü kuponlar başlamamış koşuda yenilenir
GG = {}   # model -> sıra üsleri (Jason-S kendi öğrenilmiş ölçeklerini kullanır)


def _olasiliklar(obj, k):
    at = [a for a in k["atlar"] if a.get("agf") and not a.get("kosmaz")]
    if len(at) < 5:
        return None
    tot = sum(a["agf"] for a in at)
    pp = [a["agf"] / tot for a in at]
    w0 = obj.get("w0", 1.0)
    def sm(s):
        m = max(s); e = [math.exp(x - m) for x in s]; z = sum(e); return [x / z for x in e]
    pm = sm([w0 * math.log(max(p, 1e-6)) + (a.get("z") or 0.0) for p, a in zip(pp, at)])
    pj = None
    if obj.get("w0_aday") is not None and all(a.get("z2") is not None for a in at):
        l2 = obj.get("lp2_aday", 0.0)
        pj = sm([obj["w0_aday"] * math.log(max(p, 1e-6)) + l2 * math.log(max(p, 1e-6)) ** 2 + a["z2"] for p, a in zip(pp, at)])
    ps = None
    if obj.get("w0_s") is not None and all(a.get("z4") is not None for a in at):
        l2 = obj.get("lp2_s", 0.0)
        ps = sm([obj["w0_s"] * math.log(max(p, 1e-6)) + l2 * math.log(max(p, 1e-6)) ** 2 + a["z4"] for p, a in zip(pp, at)])
    pf = None
    if obj.get("w0_f") is not None and all(a.get("z5") is not None for a in at):
        l2 = obj.get("lp2_f", 0.0)
        pf = sm([obj["w0_f"] * math.log(max(p, 1e-6)) + l2 * math.log(max(p, 1e-6)) ** 2 + a["z5"] for p, a in zip(pp, at)])
    GG["Jason-S"] = obj.get("a_s") or G_M
    pg = None
    try:                                                   # G1-S: katsayılar obj'den (z6_doldur v3/v2'ye göre yazar; z6 ile aynı sürüm olmalı)
        if obj.get("w0_g1") is not None and obj.get("a_g1") and all(a.get("z6") is not None for a in at):
            pg = sm([obj["w0_g1"] * math.log(max(p, 1e-6)) + a["z6"] for p, a in zip(pp, at)]); GG["G1-S"] = obj["a_g1"]
    except Exception as e:
        print("G1-S olasılık hatası:", repr(e))
    return at, pp, {"Bolton": pm, **({"Jason": pj} if pj else {}), **({"Jason-S": ps} if ps else {}), **({"Jason-F": pf} if pf else {}), **({"G1-S": pg} if pg else {})}


def _modeller(obj, k):
    r = _olasiliklar(obj, k)
    return list(r[2].keys()) if r else []


def _ekle_g(c, at, pp, P, simdi, istek=None):
    """c['kuponlar']'a eksik -G kuponlarını ekler (mevcut kuponlara dokunmaz)."""
    Wp, Tp = _W(pp, G_P)
    for model, p in P.items():
        for B in BUTCELER_G:
            if any(q["model"] == model + "-G" and q["butce"] == B for q in c["kuponlar"]):
                continue
            kp = kupon_g(p, B, GG.get(model))
            if not kp:
                continue
            sets, pm_ = kp; pq = _prob(Wp, Tp, sets); v = gecerli_say(sets)
            c["kuponlar"].append({"model": model + "-G", "butce": B, "kombinasyon": v, "bedel": round(v * BIRIM, 2), "bedel_gecerli": round(v * BIRIM, 2),
                                  "ayaklar": [[at[i]["no"] for i in s] for s in sets],
                                  "isimler": [{str(at[i]["no"]): at[i]["at"] for i in s} for s in sets],
                                  "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3), "eklendi": simdi, "surum": 2, **({"g1v": G1V["s"]} if model == "G1-S" else {})})


def _odeme(tarih):
    try:
        o = pd.read_csv(os.path.join(KOK, "data", "odeme", tarih[:7] + ".csv.gz"))
        return o[(o.tarih == tarih) & o.tur.str.contains("SIRALI 5")]
    except Exception:
        return pd.DataFrame()


_OD_ONBELLEK = {}


def _od_ay(ay):
    if ay not in _OD_ONBELLEK:
        try:
            o = pd.read_csv(os.path.join(KOK, "data", "odeme", ay + ".csv.gz")); _OD_ONBELLEK[ay] = o[o.tur.str.contains("SIRALI 5")]
        except Exception:
            _OD_ONBELLEK[ay] = pd.DataFrame()
    return _OD_ONBELLEK[ay]


def devir_durum(tarih, hip, kosu, havuz_oncesi):
    """Bu sıralı 5'li havuzuna devir geliyor mu? (yönetmelik md.11: bilen yoksa tutar aynı hipodromun bir sonraki sıralı 5'li havuzuna eklenir).
    Önceki havuz = aynı gün bu koşudan önceki son sıralı 5'li koşusu; yoksa önceki 3 günün son sıralı 5'li koşusu. Sonucu henüz yoksa None (bilinmiyor).
    Dönüş: {'var': True, 'tutar': devir TL, 'kaynak': 'yyyy-aa-gg|kosu'} ya da None."""
    import datetime as _dt
    _OD_ONBELLEK.clear()
    bu = _od_ay(tarih[:7])
    onc = [x for x in havuz_oncesi if x < kosu]
    if onc:
        pk = max(onc); o = bu[(bu.tarih == tarih) & (bu.hipodrom == hip) & (bu.kosu == pk)] if len(bu) else bu
        if len(o) and o.tur.str.contains("DEVİR").any():
            return {"var": True, "tutar": round(float(o[o.tur.str.contains("DEVİR")].tutar.max()), 2), "kaynak": f"{tarih}|{pk}"}
        return None
    d0 = _dt.date.fromisoformat(tarih)
    for g in range(1, 4):
        gun = (d0 - _dt.timedelta(days=g)).isoformat(); od = _od_ay(gun[:7])
        o = od[(od.tarih == gun) & (od.hipodrom == hip)] if len(od) else od
        if len(o):
            sk = int(o.kosu.max()); son = o[o.kosu == sk]
            if son.tur.str.contains("DEVİR").any():
                return {"var": True, "tutar": round(float(son[son.tur.str.contains("DEVİR")].tutar.max()), 2), "kaynak": f"{gun}|{sk}"}
            return None
    return None


def _ekle_devir(c, at, pp, P, simdi):
    """Devirli havuz: G1-S ile donmuş 'Devir-G1S' kuponları (bütçe 96, 150 ve 600; ön kayıt hipotez_defteri 2026-10-24 19:30 ve 20:30)."""
    if "G1-S" not in P:
        return
    Wp, Tp = _W(pp, G_P)
    for B in (96, 150, 600):
        if any(q["model"] == "Devir-G1S" and q["butce"] == B for q in c["kuponlar"]):
            continue
        kp = kupon_g(P["G1-S"], B, GG.get("G1-S"))
        if not kp:
            continue
        sets, pm_ = kp; pq = _prob(Wp, Tp, sets); v = gecerli_say(sets)
        c["kuponlar"].append({"model": "Devir-G1S", "butce": B, "kombinasyon": v, "bedel": round(v * BIRIM, 2), "bedel_gecerli": round(v * BIRIM, 2),
                              "ayaklar": [[at[i]["no"] for i in s] for s in sets], "isimler": [{str(at[i]["no"]): at[i]["at"] for i in s} for s in sets],
                              "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3), "eklendi": simdi, "surum": 2,
                              **({"g1v": G1V["s"]} if G1V["s"] else {})})


def _kup_gec(model, B, p, at, Wp, Tp, GGm, g1v, sn):
    kp = kupon_g(p, B, GGm)
    if not kp:
        return None
    sets, pm_ = kp; pq = _prob(Wp, Tp, sets); v = gecerli_say(sets)
    return {"model": model, "butce": B, "kombinasyon": v, "bedel": round(v * BIRIM, 2), "bedel_gecerli": round(v * BIRIM, 2),
            "ayaklar": [[at[i]["no"] for i in s_] for s_ in sets], "isimler": [{str(at[i]["no"]): at[i]["at"] for i in s_} for s_ in sets],
            "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3), "eklendi": sn, "surum": 2, **({"g1v": g1v} if g1v else {})}


def _gec_ortak(obj):
    """Geç kupon ortak hazırlık: (kay, M-index, c3, t, simdi_dk, sn) ya da None."""
    import datetime as _dt
    from . import ortak as _O, g1 as _G1, g1v3 as _V3
    tarih = obj["tarih"]; yol = os.path.join(VERI, tarih + ".json"); my = os.path.join(KOK, "data", "muh", tarih + ".json")
    if not (os.path.exists(yol) and os.path.exists(my)):
        return None
    M = json.load(open(my, encoding="utf-8")); sn = _O.tr_simdi(); simdi_dk = sn.hour * 60 + sn.minute + sn.second / 60
    c3 = _V3.yukle()
    if not c3:
        return None
    try:
        _G1.z6_doldur(obj)
    except Exception as e:
        print("z6 hatası (geç):", repr(e))
    MI = {}
    for _k, _v in M.items():
        _sl = str(_v.get("slug") or "").split("-")[0]; MI[(_sl, _v.get("kosu"))] = _v
        MI[(str(_v.get("hipodrom") or "").lower(), _v.get("kosu"))] = _v
    MI.update({("diyarbakir", kk[1]): vv for kk, vv in list(MI.items()) if kk[0] in ("dbakir", "diyarbakir")})
    return MI, c3, _dt.date.fromisoformat(tarih), simdi_dk, sn


def gec_p(obj, h, k, ort, kapanis_dk=-10.0, pencere_dk=30.0):
    """Tek koşu için geç olasılıklar: (at, atc, pm, p, son, dk) ya da None. p = G1-S v3 (girdi: canlı muhtemel ganyan)."""
    from . import g1v3 as _V3
    MI, c3, t, simdi_dk, sn = ort
    try:
        dk = int(k["saat"][:2]) * 60 + int(k["saat"][3:5]) - simdi_dk
    except Exception:
        return None
    if dk < kapanis_dk or dk > pencere_dk:
        return None
    m = MI.get((h["id"], k["kosu"]))
    an = [x for x in (m or {}).get("anlik", []) if x.get("durum") == "AÇIK" and x.get("g")]
    if not an or an[-1].get("dk") is None or an[-1]["dk"] - dk > 10:
        return None                                          # anlık yok ya da 10 dk'dan eski
    son = an[-1]; at = [a for a in k["atlar"] if a.get("agf") and not a.get("kosmaz")]
    g = [son["g"].get(str(a["no"])) for a in at]
    if len(at) < 5 or any(x is None or x <= 0 for x in g):
        return None
    inv = [1 / x for x in g]; z = sum(inv); pm = [x / z for x in inv]
    atc = [{**a, "agf": 100 * q} for a, q in zip(at, pm)]
    zz = _V3.z6(atc, t, c3)
    if not zz:
        return None
    for a in atc:
        a["z6"] = zz[a["no"]]
    sc = [obj["w0_g1"] * math.log(max(q, 1e-6)) + zz[a["no"]] for q, a in zip(pm, atc)]
    mx = max(sc); e = [math.exp(x - mx) for x in sc]; zs = sum(e); p = [x / zs for x in e]
    return at, atc, pm, p, son, dk


def gec_guncelle(obj, kapanis_dk=-10.0, pencere_dk=30.0):
    """GEÇ KUPON (24 Ekim 2026, Doğan: bayide start'a 5 dk kala oynuyor): yarışa kalan süre [kapanis_dk, pencere_dk] ise, TJK canlı muhtemel ganyanıyla
    (data/muh, vhs.tjk.org) G1-S v3'ü backtest'teki girdiyle (kapanış ganyanı ~ muhtemel ganyan) yeniden çalıştırır ve c['gec']'e yazar.
    kapanis_dk altında DONAR (artık güncellenmez). Sabah/AGF kuponu ayrı kalır. Ön kayıt: hipotez_defteri 2026-10-24 21:30."""
    ort = _gec_ortak(obj)
    if not ort:
        return 0
    tarih = obj["tarih"]; yol = os.path.join(VERI, tarih + ".json"); kay = json.load(open(yol, encoding="utf-8")); g1v = obj.get("g1_surum"); n = 0
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            c = kay.get(f"{h['id']}|{k['kosu']}")
            if not c or "sonuc" in c or k.get("sonuc"):
                continue
            r = gec_p(obj, h, k, ort, kapanis_dk, pencere_dk)
            if not r:
                continue
            at, atc, pm, p, son, dk = r
            GGm = obj.get("a_g1"); Wp, Tp = _W(pm, G_P); kup = []
            for B in BUTCELER_G:
                q = _kup_gec("G1-S-G (geç)", B, p, at, Wp, Tp, GGm, g1v, son["t"])
                if q: kup.append(q)
            if c.get("devir"):
                for B in (96, 150, 600):
                    q = _kup_gec("Devir-G1S (geç)", B, p, at, Wp, Tp, GGm, g1v, son["t"])
                    if q: kup.append(q)
            if kup:
                c["gec"] = {"t": son["t"], "dk": round(dk, 1), "kaynak": "muhtemel ganyan", "kuponlar": kup, "hesap": ort[4].strftime("%H:%M:%S")}; n += 1
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    if n:
        ozet_yaz(tarih)
    return n


def guncelle(obj, simdi=None):
    tarih = obj["tarih"]; os.makedirs(VERI, exist_ok=True)
    try:
        from . import g1 as _G1; _G1.z6_doldur(obj)
    except Exception as e:
        print("z6 hatası:", repr(e))
    G1V["s"] = obj.get("g1_surum")
    yol = os.path.join(VERI, tarih + ".json")
    kay = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    if simdi is None:
        try:
            from . import ortak as O
            simdi = O.tr_simdi().strftime("%H:%M")
        except Exception:
            simdi = None
    od = None
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            anahtar = f"{h['id']}|{k['kosu']}"
            saat = k.get("saat") or "99:99"
            c = kay.get(anahtar)
            if c and "sonuc" not in c and not k.get("sonuc") and k.get("besli") is False:
                del kay[anahtar]; c = None            # program CSV'sine göre sıralı beşli oynanmayan koşu: kupon tutulmaz (14 Ekim 2026)
            if c is None and not k.get("sonuc") and (simdi is None or simdi < saat) and k["kosu"] >= 2 and k.get("besli") is True:
                r = _olasiliklar(obj, k)
                if r:
                    at, pp, P = r
                    c = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": saat, "uretim": simdi, "kuponlar": []}
                    Wp, Tp = _W(pp, G_P)
                    for model, p in P.items():
                        if model in ("Jason-S", "G1-S"):
                            continue                  # Jason-S ve G1-S yalnız -G kuponlarla ölçülür
                        for B in BUTCELER:
                            kp = kupon(p, B)
                            if not kp:
                                continue
                            sets, pm_ = kp; pq = _prob(Wp, Tp, sets); n = math.prod(len(s) for s in sets)
                            c["kuponlar"].append({"model": model, "butce": B, "kombinasyon": n, "bedel": round(n * BIRIM, 2), "bedel_gecerli": round(gecerli_say(sets) * BIRIM, 2),
                                                  "ayaklar": [[at[i]["no"] for i in s] for s in sets],
                                                  "isimler": [{str(at[i]["no"]): at[i]["at"] for i in s} for s in sets],
                                                  "tutma_model": round(pm_, 5), "tutma_piyasa": round(pq, 5), "oran": round(pm_ / max(pq, 1e-9), 3)})
                    _ekle_g(c, at, pp, P, simdi)
                    kay[anahtar] = c
            if c and "sonuc" not in c and not k.get("sonuc") and (simdi is None or simdi < saat) and G1V["s"]:
                _g1e = [q for q in c["kuponlar"] if q["model"] in ("G1-S-G", "Devir-G1S") and q.get("g1v") != G1V["s"]]
                if _g1e:                                  # G1-S sürümü değişti (v2 -> v3, 24 Ekim 2026): başlamamış koşuda G1-S kuponları yeni sürümle yenilenir (eksik -G ekleme aşaması üretir)
                    c["kuponlar"] = [q for q in c["kuponlar"] if q not in _g1e]
            if c and "sonuc" not in c and not k.get("sonuc") and (simdi is None or simdi < saat):
                eski = [q for q in c["kuponlar"] if q["model"].endswith("-G") and q.get("surum", 1) < 2]
                if eski:                                  # sürüm 1 (tek başlangıçlı) -G kuponlar henüz başlamamış koşuda sürüm 2 ile değiştirilir
                    c["kuponlar"] = [q for q in c["kuponlar"] if q not in eski]
            _mod = _modeller(obj, k) if (c and "sonuc" not in c and not k.get("sonuc")) else []
            if c and "sonuc" not in c and not k.get("sonuc") and (simdi is None or simdi < saat) and any(
                    not any(q["model"] == m + "-G" and q["butce"] == B for q in c["kuponlar"]) for B in BUTCELER_G for m in _mod):
                r = _olasiliklar(obj, k)                 # henüz başlamamış kayda eksik -G kuponlar eklenir (mevcut kuponlar değişmez)
                if r:
                    at, pp, P = r; _ekle_g(c, at, pp, P, simdi)
            if c and "sonuc" not in c and not k.get("sonuc") and (simdi is None or simdi < saat):
                try:
                    if c.get("devir") is None:
                        havuz = [x["kosu"] for x in h["kosular"] if x.get("besli") is True]
                        dv = devir_durum(tarih, h["id"], k["kosu"], havuz)
                        if dv:
                            c["devir"] = dv
                    if c.get("devir"):
                        r = _olasiliklar(obj, k)
                        if r:
                            at, pp, P = r; _ekle_devir(c, at, pp, P, simdi)
                except Exception as e:
                    print("devir hatası:", repr(e))
            if c and "sonuc" not in c and k.get("sonuc"):
                sira = {int(no): v["sira"] for no, v in k["sonuc"].items() if v.get("sira") is not None and v["sira"] > 0}
                ilk5 = [no for no, s in sorted(sira.items(), key=lambda x: x[1])][:5]
                if len(ilk5) == 5:
                    if od is None:
                        od = _odeme(tarih)
                    o = od[(od.hipodrom == h["id"]) & (od.kosu == k["kosu"])] if len(od) else od
                    if len(o):
                        kazanan = o[~o.tur.str.contains("DEVİR")]
                        odeme = float(kazanan.tutar.max()) if len(kazanan) else 0.0
                        c["ilk5"] = ilk5; c["odeme"] = odeme; c["sonuc"] = True
                        for q in c["kuponlar"] + (c.get("gec") or {}).get("kuponlar", []):
                            q["isabet"] = all(ilk5[i] in q["ayaklar"][i] for i in range(5))
                            q["kazanc"] = odeme if q["isabet"] else 0.0
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz(tarih)


def ozet_yaz(tarih):
    top = {}
    for y in sorted(glob.glob(os.path.join(VERI, "*.json"))):
        for c in json.load(open(y, encoding="utf-8")).values():
            if not c.get("sonuc"):
                continue
            for q in c["kuponlar"] + (c.get("gec") or {}).get("kuponlar", []):
                if "isabet" not in q:
                    continue
                for grup in ("hepsi", "onerilen"):
                    if grup == "onerilen" and q["oran"] < ESIK_ORAN:
                        continue
                    t = top.setdefault(f"{grup}-{q['model']}-{q['butce']}", {"grup": grup, "model": q["model"], "butce": q["butce"], "kosu": 0, "harcama": 0.0, "isabet": 0, "kazanc": 0.0, "beklenen": 0.0})
                    t["kosu"] += 1; t["harcama"] += gecerli_say(q["ayaklar"]) * BIRIM; t["harcama_carpim"] = t.get("harcama_carpim", 0.0) + q["bedel"]; t["isabet"] += int(q["isabet"]); t["kazanc"] += q["kazanc"]
    for t in top.values():
        t["geri_donus"] = round(t["kazanc"] / t["harcama"], 3) if t["harcama"] else None
        t["harcama"] = round(t["harcama"], 2); t["harcama_carpim"] = round(t.get("harcama_carpim", 0.0), 2); t["kazanc"] = round(t["kazanc"], 2); t.pop("beklenen")
    yol = os.path.join(VERI, tarih + ".json")
    bugun = list(json.load(open(yol, encoding="utf-8")).values()) if os.path.exists(yol) else []
    os.makedirs(SITE, exist_ok=True)
    json.dump({"tarih": tarih, "esik": ESIK_ORAN, "bugun": bugun, "toplam": list(top.values())},
              open(os.path.join(SITE, "besli.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
