"""ganyancanavari.com.tr günlük galop listesi -> data/galop/YYYY-MM.csv.gz (24 Ekim 2026).
Kaynak: POST /functions/galoplar_gunluk.php (sitenin kendi sayfasının çağırdığı JSON; robots.txt: User-agent * Allow /). Herkese açık günlük galoplar; ücretli 'Canavar+' bölümlerine dokunulmaz.
Nazik: istekler arası >=4 sn, hata/429/403'te durur, günde bir kez + sınırlı geri doldurma. Kullanım: python -m tjk.galop gun [tarih] | geri BAS BIT [MAX] | derinlik"""
import os, re, sys, json, time, datetime as dt
import pandas as pd
import requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KL = os.path.join(KOK, "data", "galop")
URL = "https://www.ganyancanavari.com.tr/functions/galoplar_gunluk.php"
H = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; dusuk sikli istek; dogan.korkmaz)", "Accept": "application/json, text/javascript, */*; q=0.01",
     "X-Requested-With": "XMLHttpRequest", "Referer": "https://www.ganyancanavari.com.tr/mobile/gunluk-galoplar.html", "Origin": "https://www.ganyancanavari.com.tr"}
BEKLE = 4.0
SUT = ["it", "hip", "at_id", "at", "jokey", "pdur", "pist", "tur", "durum", "p400", "p600", "p800", "p1000", "p1200", "p1400", "video", "aciklama"]


def sn(x):
    """'27.10' -> 27.1 ; '1.04.00' -> 64.0 ; '-' -> None"""
    x = str(x or "").strip()
    m = re.fullmatch(r"(\d+)\.(\d\d)\.(\d\d)", x)
    if m:
        return int(m[1]) * 60 + int(m[2]) + int(m[3]) / 100
    m = re.fullmatch(r"(\d+)\.(\d\d)", x)
    return int(m[1]) + int(m[2]) / 100 if m else None


def cek(tarih):
    d = dt.date.fromisoformat(tarih)
    veri = {"key": "gunluk-galoplar", "email": "", "tarih": d.strftime("%d.%m.%Y"), "sehir": "HEPSİ", "tip": "HEPSİ", "cins": "HEPSİ", "isOnlyFollowed": "false"}
    time.sleep(BEKLE)
    r = requests.post(URL, data=veri, headers=H, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    j = r.json()
    if not j.get("success"):
        raise RuntimeError("success!=1")
    rows = []
    for g in j.get("Galoplar") or []:
        pist = str(g.get("Pist") or "").split()
        rows.append({"it": dt.datetime.strptime(g["Tarih"], "%d.%m.%Y").date().isoformat(), "hip": g.get("Sehir"), "at_id": g.get("At_id"), "at": g.get("At_Unvan"),
                     "jokey": g.get("Jokey"), "pist": pist[0] if pist else None, "pdur": pist[1] if len(pist) > 1 else None, "tur": g.get("Tip"), "durum": g.get("Durum"),
                     **{f"p{m}": sn(g.get(f"p{m}")) for m in (400, 600, 800, 1000, 1200, 1400)}, "video": g.get("VideoLink") or None, "aciklama": g.get("Aciklama")})
    return rows


def yaz(rows):
    if not rows:
        return 0
    os.makedirs(KL, exist_ok=True); n = 0
    df = pd.DataFrame(rows, columns=SUT)
    for ay, g in df.groupby(df.it.str[:7]):
        yol = os.path.join(KL, ay + ".csv.gz")
        eski = pd.read_csv(yol) if os.path.exists(yol) else pd.DataFrame(columns=SUT)
        yeni = pd.concat([eski, g], ignore_index=True).drop_duplicates(subset=["it", "at_id", "tur", "jokey", "p400", "p600", "p800", "p1000", "p1200", "p1400"])
        n += len(yeni) - len(eski); yeni.sort_values(["it", "hip", "at"]).to_csv(yol, index=False, compression="gzip")
    return n


def _kaydet():
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    import subprocess
    for c in (["git", "config", "user.name", "tjk-bot"], ["git", "config", "user.email", "tjk-bot@users.noreply.github.com"], ["git", "add", "-A", "data"]):
        subprocess.run(c, check=False)
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        return
    subprocess.run(["git", "commit", "-qm", "galop ara kayıt"], check=False)
    for _ in range(3):
        if subprocess.run(["git", "pull", "-q", "--rebase"]).returncode == 0 and subprocess.run(["git", "push", "-q"]).returncode == 0:
            break
        subprocess.run(["git", "rebase", "--abort"], check=False); time.sleep(5)


if __name__ == "__main__":
    m = sys.argv[1]
    bugun = (dt.datetime.utcnow() + dt.timedelta(hours=3)).date()
    if m == "gun":
        t = sys.argv[2] if len(sys.argv) > 2 else bugun.isoformat()
        r = cek(t); print(t, len(r), "satır; yeni:", yaz(r))
    elif m == "derinlik":
        out = {}
        for t in ("2026-10-17", "2026-09-01", "2026-06-01", "2026-01-15", "2025-06-01", "2024-06-01", "2023-06-01"):
            try:
                r = cek(t); out[t] = {"satir": len(r), "hip": sorted({x["hip"] for x in r}), "ornek": r[:1]}
            except Exception as e:
                out[t] = {"hata": repr(e)}
            print(t, out[t].get("satir", out[t].get("hata")), flush=True)
        os.makedirs(os.path.join(KOK, "data", "futbol"), exist_ok=True)
        json.dump(out, open(os.path.join(KOK, "data", "futbol", "galop_derinlik.json"), "w"), ensure_ascii=False, indent=1)
    elif m == "geri":
        b, e = dt.date.fromisoformat(sys.argv[2]), dt.date.fromisoformat(sys.argv[3]); mx = int(sys.argv[4]) if len(sys.argv) > 4 else 100
        d = e; n = 0
        while d >= b and n < mx:
            try:
                r = cek(d.isoformat())
            except Exception as ex:
                print("durduruldu:", d, repr(ex)); break
            print(d, len(r), "satır; yeni:", yaz(r), flush=True); n += 1; d -= dt.timedelta(days=1)
            if n % 15 == 0:
                _kaydet()
