"""Kullanım: python3 data/analiz/at_bak.py "AT ADI"   → o adın at dosyası(ları): karne + son 8 koşu."""
import sys, gzip, json
ad = " ".join(sys.argv[1:]).strip().upper()
I = json.load(gzip.open("data/at/indeks.json.gz"))
for k, v in I.items():
    if v[1].upper() == ad:
        a = json.load(gzip.open(f"data/at/s_{v[0]}.json.gz"))[k]
        print(k, "| baba:", a["baba"], "| anne:", a["anne"], "| antrenör:", a["antrenor"], "| sahip:", a["sahip"])
        print("KARNE:", json.dumps(a["karne"], ensure_ascii=False))
        for r in sorted(a["kosular"], key=lambda r: (r["t"], r["k"]))[-8:]:
            sp = r.get("spiker") or {}; vd = r.get("video") or {}
            print(r["t"], r["hip"], r["k"], f'no{r["no"]}', r.get("mesafe"), "sıra", r.get("sira"), "gan", r.get("gan"), "jokey", r.get("jokey"),
                  "| olay", [e["tur"] for e in sp.get("olay", [])], "| video erken/son", vd.get("erken"), vd.get("son"))
