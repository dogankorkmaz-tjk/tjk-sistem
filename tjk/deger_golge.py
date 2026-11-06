"""Canlı 'değer kuponu (gölge)' kartlarının ileriye dönük kâğıt üstü kaydı (7 Kasım 2026; T163/T167/T168/T169/T169-B).
Koşu başlamadan önceki son 15 dk'da, en son AÇIK canlı muhtemelle (ganyan + kapanış öncesi son ikili/sıralı ikili listesi 'havuz_acik')
Canlı sekmesindeki kurallarla kuponlar kurulur ve koşu başlayınca donar; koşu bitince resmî ödemelerle (data/odeme) değerlendirilir.
Kuponlar: sıralı ikili virgüllü + kombine (liste dışı çift = model × listedeki en yüksek oran, T169-B), ikili kombine (liste dışı 0,75, T169),
üçlü / tabela / sıralı 5'li virgüllü değer kuponu + üçlü/5'li kombine (T167/T170 kurucuları, fiyat modeli docs/data/fiyat_modeli.json, bütçe 500 TL).
Ortak: eşik 1,2; canlı oran × 0,96 (T168); kupon < 20 TL → misli. Çıktılar: data/deger_golge/<gün>.json, docs/data/deger_golge.json.
Tarayıcıdan küçük farklar: piyasa olasılığı ekürisiz 1/oran normalizasyonu (uc_deger ile aynı); eşitlikte seçim sırası farklı olabilir."""
import os, json, glob, math, itertools
import numpy as np, pandas as pd
from . import ortak as O
from . import uc_deger as UD

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data", "deger_golge"), os.path.join(KOK, "docs", "data")
BASLA = "2026-11-07"
PENCERE_DK = 15
TH, KAY, BMX = 1.2, 0.96, 100
GP = [1.0, 0.87, 0.74, 0.74, 0.74]
BIRIM = {"si": 1.0, "ik": 1.0, 3: 2.0, 4: 1.5, 5: 1.25}
TUR = {"si": "SIRALI İKİLİ", "ik": "İKİLİ", 3: "ÜÇLÜ BAHİS", 4: "TABELA BAHİS", 5: "SIRALI 5 Lİ BAHİS"}
HIPKEY = {"diyarbakir": "DBAKIR"}


def _fm():
    try:
        return json.load(open(os.path.join(SITE, "fiyat_modeli.json"), encoding="utf-8"))
    except Exception:
        return None


def _pl_vec(P, w, G, K):
    out = np.ones(len(P))
    for k in range(K):
        wk = np.power(np.maximum(w, 1e-12), G[k]); T = wk.sum()
        den = T - sum(wk[P[:, j]] for j in range(k)) if k else T
        out *= wk[P[:, k]] / np.maximum(den, 1e-12)
    return out


def _misli(n, birim):
    c = n * birim
    return math.ceil(20 / c) if c < 20 else 1


def _ikili(nos, p, a5, lst, sirali):
    """Canlı'daki degerIk ile aynı kural. lst: [[S1,S2,G],...]. Döner kupon listesi (virgüllü/kombine)."""
    j = {n: i for i, n in enumerate(nos)}
    key = (lambda a, b: (a, b)) if sirali else (lambda a, b: (min(a, b), max(a, b)))
    Q = {}
    for x in lst or []:
        try:
            a, b, G = int(x[0]), int(x[1]), float(str(x[2]).replace(",", "."))
        except Exception:
            continue
        if a in j and b in j and G > 1:
            Q[key(j[a], j[b])] = G
    if not Q:
        return []
    MX = max(Q.values()); w1 = np.power(p, a5[0]); w2 = np.power(p, a5[1])
    sp = lambda a, b: w1[a] / w1.sum() * w2[b] / (w2.sum() - w2[a])
    def val(a, b):
        G = Q.get(key(a, b))
        if G is None:
            return sp(a, b) * MX * KAY if sirali else 0.75
        mp = sp(a, b) if sirali else sp(a, b) + sp(b, a)
        return mp * G * KAY
    cand = list(np.argsort(-p)[:9])
    best = max(((a, b) for a in cand for b in cand if a != b), key=lambda c: val(*c))
    if val(*best) < TH:
        return []
    cV = lambda A, B: [(a, b) for a in A for b in B if a != b]
    cK = lambda S: [(a, b) for a in S for b in S if a != b and (sirali or a < b)]
    def art(cur, nw):
        cs = {key(*c) for c in cur}
        return sum(val(*c) - TH for c in nw if key(*c) not in cs)
    out = []
    S = {best[0], best[1]}
    for _ in range(20):
        cur = cK(S); sec = None
        for h in cand:
            if h in S: continue
            nw = cK(S | {h})
            if len(nw) > BMX: continue
            d = art(cur, nw)
            if d > 0 and (sec is None or d > sec[0]): sec = (d, h)
        if sec is None: break
        S.add(sec[1])
    srt = lambda X: sorted(X, key=lambda i: -p[i])
    n = len(cK(S)); out.append({"tur": "si_kombine" if sirali else "ik_kombine", "atlar": [int(nos[i]) for i in srt(S)], "n": n, "misli": _misli(n, 1.0)})
    if sirali:
        A, B = {best[0]}, {best[1]}
        for _ in range(20):
            cur = cV(A, B); sec = None
            for pos in (0, 1):
                for h in cand:
                    if h in (B if pos else A): continue
                    nw = cV(A, B | {h}) if pos else cV(A | {h}, B)
                    if len(nw) > BMX: continue
                    d = art(cur, nw)
                    if d > 0 and (sec is None or d > sec[0]): sec = (d, pos, h)
            if sec is None: break
            (B if sec[1] else A).add(sec[2])
        n = len(cV(A, B)); out.append({"tur": "si_virgul", "sets": [[int(nos[i]) for i in srt(A)], [int(nos[i]) for i in srt(B)]], "n": n, "misli": _misli(n, 1.0)})
    return out


def _deger(nos, p, qd, a5, K, fm, B=500.0):
    """Canlı degerKupon (virgüllü değer kuponu) — T167 kurucusu."""
    f = (fm or {}).get(str(K))
    if not f or len(nos) < K + 2:
        return None
    bi = f["birim"]; cand = list(np.argsort(-p)[:9])
    P = np.array(list(itertools.permutations(cand, K)))
    pm = np.maximum(_pl_vec(P, p, a5, K), 1e-15); pq = np.maximum(_pl_vec(P, qd, GP, K), 1e-15)
    oh = np.exp(f["b"][0] + f["b"][1] * np.log(1 / pq) + f["b"][2] * np.log(pm / pq) + f["s2"] / 2) * (fm.get("kayma") or 1.0)
    oran = pm * oh / bi; b = int(np.argmax(oran))
    if oran[b] < TH:
        return None
    S = [{int(P[b, k])} for k in range(K)]; M = [P[:, k] == P[b, k] for k in range(K)]
    while True:
        cur = np.logical_and.reduce(M); sec = None
        for k in range(K):
            for h in set(cand) - S[k]:
                Mk = M[k] | (P[:, k] == h); m = np.logical_and.reduce([Mk if jj == k else M[jj] for jj in range(K)])
                yeni = m & ~cur
                if m.sum() * bi > B or not yeni.any(): continue
                d = (oran[yeni] - TH).sum()
                if d > 0 and (sec is None or d > sec[0]): sec = (d, k, h, Mk)
        if sec is None: break
        _, k, h, Mk = sec; S[k].add(h); M[k] = Mk
    m = np.logical_and.reduce(M); n = int(m.sum())
    return {"tur": f"deger{K}", "sets": [[int(nos[i]) for i in sorted(s, key=lambda i: -p[i])] for s in S], "n": n, "misli": _misli(n, bi),
            "tahmini_ev": round(float((pm[m] * oh[m]).sum() / (n * bi)), 3)}


def _kombine(nos, p, qd, a5, K, fm, B=500.0):
    """Canlı degerKupon(kip='kombine') — T170: n at, tüm sıralar."""
    f = (fm or {}).get(str(K))
    if not f or len(nos) < K + 2:
        return None
    bi = f["birim"]; cand = list(np.argsort(-p)[:9])
    P = np.array(list(itertools.permutations(cand, K)))
    pm = np.maximum(_pl_vec(P, p, a5, K), 1e-15); pq = np.maximum(_pl_vec(P, qd, GP, K), 1e-15)
    oh = np.exp(f["b"][0] + f["b"][1] * np.log(1 / pq) + f["b"][2] * np.log(pm / pq) + f["s2"] / 2) * (fm.get("kayma") or 1.0)
    oran = pm * oh / bi; b = int(np.argmax(oran))
    if oran[b] < TH:
        return None
    mem = np.zeros(len(p), bool); mem[P[b]] = True; cur = mem[P].all(1)
    while True:
        sec = None
        for h in cand:
            if mem[h]: continue
            m2 = mem.copy(); m2[h] = True; nw = m2[P].all(1); yeni = nw & ~cur
            if nw.sum() * bi > B or not yeni.any(): continue
            d = (oran[yeni] - TH).sum()
            if d > 0 and (sec is None or d > sec[0]): sec = (d, h, nw)
        if sec is None: break
        mem[sec[1]] = True; cur = sec[2]
    n = int(cur.sum()); at = sorted(np.where(mem)[0], key=lambda i: -p[i])
    return {"tur": f"kombine{K}", "atlar": [int(nos[i]) for i in at], "n": n, "misli": _misli(n, bi), "tahmini_ev": round(float((pm[cur] * oh[cur]).sum() / (n * bi)), 3)}


def _kombolar(q):
    t = q["tur"]
    if t == "si_kombine":
        return {c for c in itertools.permutations(q["atlar"], 2)}
    if t.startswith("kombine"):
        return {c for c in itertools.permutations(q["atlar"], int(t[-1]))}
    if t == "ik_kombine":
        return {tuple(sorted(c)) for c in itertools.combinations(q["atlar"], 2)}
    return {c for c in itertools.product(*q["sets"]) if len(set(c)) == len(c)}


def _birim(q):
    t = q["tur"]
    return 1.0 if t.startswith(("si", "ik")) else BIRIM[int(t[-1])]


def _resmi(q):
    t = q["tur"]
    return TUR["si"] if t.startswith("si") else TUR["ik"] if t.startswith("ik") else TUR[int(t[-1])]


def guncelle(obj, simdi=None):
    tarih = obj["tarih"]
    if tarih < BASLA:
        return
    os.makedirs(VERI, exist_ok=True)
    yol = os.path.join(VERI, tarih + ".json")
    kay = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    if simdi is None:
        simdi = O.tr_simdi().strftime("%H:%M")
    try:
        muh = json.load(open(os.path.join(KOK, "data", "muh", tarih + ".json"), encoding="utf-8"))
    except Exception:
        muh = {}
    a5 = obj.get("a_g1") or [1.0, 0.8, 0.69, 0.69, 0.69]; fm = _fm(); od = None
    for h in obj["hipodromlar"]:
        for k in h["kosular"]:
            anahtar = f"{h['id']}|{k['kosu']}"; saat = k.get("saat") or "99:99"; c = kay.get(anahtar)
            if not k.get("sonuc") and simdi < saat:
                m = muh.get(f"{HIPKEY.get(h['id'], h['id'].upper())}-{k['kosu']}") or {}
                sn = [x for x in m.get("anlik", []) if x.get("dk") is not None and 0 <= x["dk"] <= PENCERE_DK and x.get("durum") in ("AÇIK", None)]
                if sn:
                    g = {int(n): v for n, v in sn[-1]["g"].items() if v}
                    nos_ok = [a["no"] for a in k["atlar"] if not a.get("kosmaz") and a["no"] in g]
                    if len(nos_ok) >= 5:
                        ham = {n: 1.0 / g[n] for n in nos_ok}; s = sum(ham.values()); pp = {n: v / s for n, v in ham.items()}
                        r = UD._model_p(obj, k, pp)
                        if r:
                            nos, p = r; p = np.asarray(p, float); qd = np.array([pp[n] for n in nos])
                            kup = []; hv = m.get("havuz_acik") or {}
                            if hv.get("dk") is not None and hv["dk"] >= 0:
                                kup += _ikili(nos, p, a5, hv.get("si"), True) + _ikili(nos, p, a5, hv.get("ik"), False)
                            for K in (3, 4, 5):
                                if K == 3 and k.get("uclu") is False: continue
                                if K == 4 and k.get("tabela") is False: continue
                                if K == 5 and k.get("besli") is False: continue
                                try:
                                    q = _deger(nos, p, qd, a5, K, fm)
                                except Exception as e:
                                    print("deger_golge", anahtar, K, repr(e)); q = None
                                if q: kup.append(q)
                                if K in (3, 5):          # T170: üçlü ve 5'li kombine
                                    try:
                                        q2 = _kombine(nos, p, qd, a5, K, fm)
                                    except Exception as e:
                                        print("deger_golge kombine", anahtar, K, repr(e)); q2 = None
                                    if q2: kup.append(q2)
                            for q in kup:
                                q["bedel"] = round(q["n"] * _birim(q) * q["misli"], 2)
                            kay[anahtar] = c = {"hipodrom": h["id"], "ad": h.get("ad"), "kosu": k["kosu"], "saat": saat, "uretim": simdi, "goruntu": sn[-1]["t"],
                                                "dk": sn[-1]["dk"], "ikili_liste_dk": hv.get("dk"), "at_sayisi": len(nos), "cins": k.get("cins"), "kuponlar": kup}   # at_sayisi: T174 ileri pencere (≥11 alt kümesi)
            if c and "sonuc" not in c and k.get("sonuc"):
                if od is None:
                    try:
                        od = pd.read_csv(os.path.join(KOK, "data", "odeme", tarih[:7] + ".csv.gz")); od = od[od.tarih == tarih]
                    except Exception:
                        od = pd.DataFrame()
                o = od[(od.hipodrom == h["id"]) & (od.kosu == k["kosu"])] if len(od) else od
                if not len(o):
                    continue
                c["sonuc"] = True
                for q in c["kuponlar"]:
                    S = _kombolar(q); res = _resmi(q); kz = 0.0; dv = False; var = False
                    for x in o.itertuples():
                        if not str(x.tur).startswith(res) or (res == TUR["ik"] and str(x.tur) != res):
                            continue
                        try:
                            kk = tuple(int(z) for z in str(x.kombo).split("/"))
                        except Exception:
                            continue
                        var = True
                        if q["tur"] == "ik_kombine": kk = tuple(sorted(kk))
                        if kk in S:
                            if "DEVİR" in str(x.tur): dv = True
                            else: kz += float(x.tutar) * q["misli"]
                    q["isabet"] = kz > 0 or dv; q["kazanc"] = round(kz, 2); q["devir_isabet"] = dv; q["odeme_var"] = var
    json.dump(kay, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ozet_yaz()


ADLAR = {"si_virgul": "Sıralı ikili · virgüllü", "si_kombine": "Sıralı ikili · kombine", "ik_kombine": "İkili · kombine",
         "deger3": "Sıralı üçlü · virgüllü", "kombine3": "Sıralı üçlü · kombine", "deger4": "Tabela · virgüllü", "deger5": "Sıralı 5'li · virgüllü", "kombine5": "Sıralı 5'li · kombine"}


def ozet_yaz():
    top = {}; gun = set()
    for y in sorted(glob.glob(os.path.join(VERI, "20*.json"))):
        for c in json.load(open(y, encoding="utf-8")).values():
            if not c.get("sonuc"):
                continue
            gun.add(os.path.basename(y)[:10])
            for q in c["kuponlar"]:
                if not q.get("odeme_var", True):
                    continue
                t = top.setdefault(q["tur"], {"tur": q["tur"], "ad": ADLAR.get(q["tur"], q["tur"]), "kosu": 0, "harcama": 0.0, "isabet": 0, "devir": 0, "kazanc": 0.0})
                t["kosu"] += 1; t["harcama"] += q["bedel"]; t["isabet"] += int(bool(q.get("isabet"))); t["devir"] += int(bool(q.get("devir_isabet"))); t["kazanc"] += q.get("kazanc", 0.0)
    for t in top.values():
        t["geri_donus"] = round(t["kazanc"] / t["harcama"], 3) if t["harcama"] else None
        t["harcama"] = round(t["harcama"], 2); t["kazanc"] = round(t["kazanc"], 2)
    sira = list(ADLAR)
    os.makedirs(SITE, exist_ok=True)
    json.dump({"baslangic": BASLA, "gun": len(gun), "toplam": sorted(top.values(), key=lambda x: sira.index(x["tur"]) if x["tur"] in sira else 99),
               "not": "Ödeme resmî ilan × misli; havuz paylaşımı (bizim bahsimizin ikramiyeyi bölmesi) dahil değil; DEVİR isabeti kazanç 0 sayılır, ayrıca gösterilir."},
              open(os.path.join(SITE, "deger_golge.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
