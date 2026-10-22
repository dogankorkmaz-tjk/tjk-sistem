"""İddaa oran toplayıcı (22 Ekim 2026). Kamuya açık oran servisinden futbol maçlarının oranlarını kaydeder.
Her maç için: ilk görülen oran ('ac'), kapanışa en yakın görülen oran ('kap', maça <=90 dk kala güncellenir). Aylık dosya data/futbol/oran/YYYY-MM.json.gz.
Piyasa kodları (st): 1=MS(1-0-2), 100=Handikaplı MS, 101=Alt/Üst, 603/604=Alt/Üst 0.5/1.5, 48/49=Alt/Üst yan piyasa (korner/kart olduğu sonuçlarla doğrulanacak), 89=KG Var/Yok, vb."""
import os, json, gzip, time, datetime
import requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLS = os.path.join(KOK, "data", "futbol", "oran")
URL = "https://sportsbookv2.iddaa.com/sportsbook/events?st=1&type=0&version=0"
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept": "application/json"}


def _ay(ts):
    return datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m")


def main():
    r = requests.get(URL, headers=H, timeout=40); r.raise_for_status()
    ev = r.json()["data"]["events"]
    simdi = int(time.time()); os.makedirs(KLS, exist_ok=True)
    dosya = {}
    n_yeni = n_kap = 0
    for e in ev:
        if e.get("sid") != 1 or not e.get("d"):        # yalnız futbol
            continue
        ay = _ay(e["d"])
        if ay not in dosya:
            yol = os.path.join(KLS, ay + ".json.gz")
            dosya[ay] = json.load(gzip.open(yol, "rt", encoding="utf-8")) if os.path.exists(yol) else {}
        d = dosya[ay]; k = str(e["i"])
        mk = {}
        for m in e.get("m", []):
            mk["%s|%s" % (m["st"], m.get("sov", ""))] = [[o["n"], o["odd"]] for o in m["o"]]
        if k not in d:
            d[k] = {"d": e["d"], "ev": e["hn"], "dep": e["an"], "lig": e.get("ci"), "ac": mk, "ac_t": simdi}; n_yeni += 1
        kal = e["d"] - simdi
        if 0 <= kal <= 5400 and not e.get("il"):
            d[k]["kap"] = mk; d[k]["kap_t"] = simdi; n_kap += 1
    for ay, d in dosya.items():
        with gzip.open(os.path.join(KLS, ay + ".json.gz"), "wt", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    print("maç", len(ev), "yeni", n_yeni, "kapanış güncelleme", n_kap)


if __name__ == "__main__":
    main()
