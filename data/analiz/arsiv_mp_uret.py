"""/tmp/claude-0/arsiv_mp.pkl yeniden üretimi (mesafe_pist_ozellik.uygula girdisi): data/atyarisi arşivinden (tarih, hip, kosu, mesafe, pist).
Orijinal üreten betik repoda yoktu (6 Kasım 2026); kaynak ve biçim, mesafe/pistin zaten bilindiği satırlarla doğrulanır. Repo kökünden: python3 data/analiz/arsiv_mp_uret.py"""
import sys, os, glob, json, gzip
import pandas as pd
sys.path.insert(0, "."); from tjk import ortak as O
S = []
for f in sorted(glob.glob("data/atyarisi/*.json.gz")):
    o = json.load(gzip.open(f, "rt")); t = o["tarih"]
    for kaynak in ("program", "sonuc"):
        for hid, kos in (o.get(kaynak) or {}).items():
            if hid not in O.TRH: continue
            for k in kos:
                m = str(k.get("distance") or "")
                S.append({"tarih": t, "hip": hid, "kosu": int(k["number"]), "mesafe": float(m) if m.isdigit() else float("nan"),
                          "pist": k.get("raceCourseType") or None})
A = pd.DataFrame(S).dropna(subset=["mesafe"]).drop_duplicates(["tarih", "hip", "kosu"])
os.makedirs("/tmp/claude-0", exist_ok=True); A.to_pickle("/tmp/claude-0/arsiv_mp.pkl")
print("arsiv_mp", len(A), "koşu", A.tarih.min(), "→", A.tarih.max(), "pist", A.pist.value_counts(dropna=False).to_dict())
d = pd.read_pickle("/tmp/claude-0/jason_d.pkl")[["tarih", "hipodrom", "kosu", "mesafe", "pist"]].drop_duplicates(["tarih", "hipodrom", "kosu"])
m = d.merge(A.rename(columns={"hip": "hipodrom"}), on=["tarih", "hipodrom", "kosu"], suffixes=("", "_a"))
b = m[m.mesafe.notna()]
print("doğrulama (jason_d'de mesafe dolu, arşivde var):", len(b), "koşu | mesafe aynı", int((b.mesafe == b.mesafe_a).sum()), "| pist aynı", int((b.pist == b.pist_a).sum()))
print("dolduracağı koşu (jason_d'de mesafe boş):", int(m.mesafe.isna().sum()), "/ jason_d'de boş toplam", int(d.mesafe.isna().sum()))
