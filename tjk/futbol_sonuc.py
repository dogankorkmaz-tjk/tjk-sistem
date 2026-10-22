"""football-data.co.uk lig CSV'lerini indirir (maç sonuçları, şut, faul, korner, kart, hakem, kurum oranları). data/futbol/fd/<sezon>_<lig>.csv"""
import os, time
import requests
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HD = os.path.join(KOK, "data", "futbol", "fd")
LIGLER = ["T1", "E0", "E1", "SP1", "D1", "I1", "F1", "N1", "P1", "B1", "G1", "SC0"]
SEZON_GECMIS = ["2122", "2223", "2324", "2425", "2526"]
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}


def indir(sezon, lig, yaz=True):
    yol = os.path.join(HD, "%s_%s.csv" % (sezon, lig))
    r = requests.get("https://www.football-data.co.uk/mmz4281/%s/%s.csv" % (sezon, lig), headers=H, timeout=40)
    if r.status_code != 200 or len(r.content) < 500:
        return False
    if os.path.exists(yol) and open(yol, "rb").read() == r.content:
        return False
    open(yol, "wb").write(r.content); return True


def main():
    os.makedirs(HD, exist_ok=True)
    guncel = "2627"
    n = 0
    for lig in LIGLER:
        n += indir(guncel, lig)
        for s in SEZON_GECMIS:
            if not os.path.exists(os.path.join(HD, "%s_%s.csv" % (s, lig))):
                n += indir(s, lig); time.sleep(0.5)
    print("güncellenen dosya", n)


if __name__ == "__main__":
    main()
