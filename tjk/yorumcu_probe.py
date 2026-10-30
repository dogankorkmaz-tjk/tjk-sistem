"""Yorumcu kaynak sondası: sporx hazır kuponlar sayfası + robots.txt ham halleri data/yorumcu_ham/probe/ altına."""
import os, datetime
import requests
try:
    from curl_cffi import requests as CR
except Exception:
    CR = None
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
H = {"User-Agent": "Mozilla/5.0 (kisisel arastirma; dusuk sikli istek)"}
def al(u):
    try:
        r = CR.get(u, impersonate="chrome", timeout=25) if CR else requests.get(u, headers=H, timeout=25)
        return r.status_code, r.text
    except Exception as e:
        return -1, repr(e)
os.makedirs(os.path.join(KOK, "data", "yorumcu_ham", "probe"), exist_ok=True)
for ad, u in (("sporx_kupon", "https://www.sporx.com/at-yarisi-hazir-kuponlar"), ("sporx_robots", "https://www.sporx.com/robots.txt")):
    kod, t = al(u)
    open(os.path.join(KOK, "data", "yorumcu_ham", "probe", ad + ".html"), "w", encoding="utf-8").write(f"<!-- {kod} {datetime.datetime.utcnow().isoformat()} {u} -->\n" + t)
    print(ad, kod, len(t))
