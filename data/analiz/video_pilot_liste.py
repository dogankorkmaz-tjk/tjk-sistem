"""Video pilotu örneği (video_pilot_plani.md, adım 1): 40 koşu = 20 'şüpheli' (hipodrom dengeli) + 20 rastgele (tüm koşulardan, taban oranı için).
Şüpheli = koşuda startta geç çıkan at (resmî delayedExit) VEYA şeritte erken ilk 3'te görünüp 7. ya da daha geride bitiren at.
Kaynak: data/atyarisi (resmî API arşivi: video bağlantısı, at listesi) + data/video_seyir (şerit özeti). Dönem 2026-05..2026-10. Tohum 40.
Çıktı: data/video_pilot/liste.json (etiketleme sayfası bunu okur). Ağ isteği YOK."""
import json, gzip, glob, os, random, ast
KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
rnd = random.Random(40); ADAY, SUP = [], []
for f in sorted(glob.glob(os.path.join(KOK, "data", "atyarisi", "2026-0[5-9]-*.json.gz")) + glob.glob(os.path.join(KOK, "data", "atyarisi", "2026-10-*.json.gz"))):
    t = os.path.basename(f)[:10]
    try: d = json.load(gzip.open(f, "rt"))
    except Exception: continue
    for hip, L in (d.get("sonuc") or {}).items():
        for r in L or []:
            v = r.get("video"); H = r.get("horses") or []
            if not v or not isinstance(H, list) or len(H) < 5: continue
            sf = os.path.join(KOK, "data", "video_seyir", f"{t}_{hip}_{r['number']}.json")
            if not os.path.exists(sf): continue
            try: oz = json.load(open(sf)).get("ozet"); oz = ast.literal_eval(oz) if isinstance(oz, str) else (oz or {})
            except Exception: oz = {}
            atlar = [{"no": h.get("number"), "ad": h.get("name"), "sira": h.get("order"), "gec": h.get("delayedExit") or ""} for h in H]
            neden = []
            for a in atlar:
                if a["gec"]: neden.append(f"{a['no']} startta geç çıktı ({a['gec']})")
                o = oz.get(str(a["no"])) or {}
                if o.get("erken") is not None and o["erken"] <= 3 and (a["sira"] or 99) >= 7: neden.append(f"{a['no']} erken önde, {a['sira']}. bitirdi")
            k = {"tarih": t, "hipodrom": hip, "kosu": r["number"], "saat": r.get("hour"), "mesafe": r.get("distance"), "pist": r.get("raceCourseType"),
                 "video": v, "video_hd": v.replace("_m.mp4", ".mp4"), "atlar": sorted(atlar, key=lambda a: a["no"] or 0), "neden": neden}
            (SUP if neden else ADAY).append(k)
rnd.shuffle(SUP); rnd.shuffle(ADAY)
def sec(L, n):                     # hipodromları dengele: her hipodromdan sırayla
    by = {}
    for k in L: by.setdefault(k["hipodrom"], []).append(k)
    out = []
    while len(out) < n and any(by.values()):
        for h in sorted(by):
            if by[h] and len(out) < n: out.append(by[h].pop())
    return out
S = sec(SUP, 20); _s = {id(k) for k in S}; TUM = [k for k in SUP + ADAY if id(k) not in _s]; rnd.shuffle(TUM); R = TUM[:20]   # rastgele = TÜM koşulardan (taban oranı için), şüpheliler hariç tutulmaz
for k in S: k["grup"] = "şüpheli"
for k in R: k["grup"] = "rastgele"
L = S + R; rnd.shuffle(L)
for i, k in enumerate(L, 1): k["id"] = f"P{i:02d}"
json.dump({"aciklama": __doc__.split("\n")[0], "aday_sayisi": {"supheli": len(SUP), "rastgele": len(ADAY)}, "kosular": L},
          open(os.path.join(KOK, "data", "video_pilot", "liste.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
import shutil; shutil.copy(os.path.join(KOK, "data", "video_pilot", "liste.json"), os.path.join(KOK, "docs", "data", "video_pilot.json"))   # etiket sayfası (docs/etiket.html) okur
print("aday şüpheli", len(SUP), "rastgele", len(ADAY), "| seçilen", len(L), "| hipodrom:", sorted({k['hipodrom'] for k in L}))
