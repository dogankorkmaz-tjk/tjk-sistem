"""atyarisi tjkbulten API'sinin ham yanıtlarını gün gün saklar: data/atyarisi/YYYY-MM-DD.json.gz = {liste, program, sonuc}.
Ham arşiv; sonradan özellik (pist durumu, hava, ekipman/jokey değişikliği, son 800, soy, ikramiyeler...) buradan türetilir.
Nazik: istekler arası >=3 sn, hata/429'da durur. Kullanım: python -m tjk.atyarisi_arsiv gun [tarih] | geri BAS BIT [MAX] | derinlik"""
import os, sys, json, gzip, time, datetime, requests
from . import atyapi as A

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KL = os.path.join(KOK, "data", "atyarisi")
BEKLE = 3.0
H = A._H


def _get(url, **kw):
    r = requests.get(url, headers=H, timeout=30, **kw)
    time.sleep(BEKLE)
    if r.status_code in (429, 500, 502, 503, 504):
        raise RuntimeError(f"sunucu {r.status_code}")
    return r.json()


def yol(t):
    return os.path.join(KL, t + ".json.gz")


def tam_mi(d):
    """sonuç tamamen belli mi (her koşuda en az bir at için sıra var)"""
    ko = [k for v in (d.get("sonuc") or {}).values() for k in v]
    return bool(ko) and all(any((a.get("order") or 0) > 0 for a in (k.get("horses") or [])) or k.get("canceledRace") for k in ko)


def arsivle(t, yenile=False):
    os.makedirs(KL, exist_ok=True)
    mevcut = json.load(gzip.open(yol(t), "rt")) if os.path.exists(yol(t)) else None
    if mevcut and tam_mi(mevcut) and not yenile:
        return "var"
    L = _get(A.LISTE, params={"date": t}).get("d") or []
    liste, prog, son = [], {}, {}
    for h in L:
        hi = h.get("hippodrome") or {}
        if hi.get("isForeign"):
            continue
        hid = A._hip(hi.get("place")) or A._hip(hi.get("code")) or (hi.get("code") or "").lower()
        liste.append({k: h.get(k) for k in ("id", "totalDay", "hippodrome", "raceCourse", "weather", "openingHour", "closingHour", "isNightRace", "isCompleted")} | {"hid": hid})
        prog[hid] = (_get(A.DETAY, params={"programId": h["id"]}).get("d") or {}).get("races") or []
        son[hid] = (_get(A.RESULT, params={"programId": h["id"]}).get("d") or {}).get("races") or []
    if not liste:
        return "yok"
    with gzip.open(yol(t), "wt") as f:
        json.dump({"tarih": t, "alindi": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"), "liste": liste, "program": prog, "sonuc": son}, f, ensure_ascii=False, separators=(",", ":"))
    return f"{len(liste)} hipodrom"


def derinlik():
    out = {}
    for t in ("2026-09-01", "2026-06-01", "2026-01-15", "2025-09-01", "2025-06-01", "2025-01-15", "2024-06-01", "2024-01-15", "2023-06-01"):
        try:
            L = [h for h in (_get(A.LISTE, params={"date": t}).get("d") or []) if not (h.get("hippodrome") or {}).get("isForeign")]
            s = None
            if L:
                rr = (_get(A.RESULT, params={"programId": L[0]["id"]}).get("d") or {}).get("races") or []
                s = {"kosu": len(rr), "atli": sum(1 for k in rr for a in k.get("horses", []) if (a.get("order") or 0) > 0),
                     "last800": sum(1 for k in rr if k.get("last800")), "bahis": sum(len(k.get("raceMoneys") or []) for k in rr)}
            out[t] = {"hipodrom": [h["hippodrome"].get("place") for h in L], "sonuc": s}
        except Exception as e:
            out[t] = {"hata": repr(e)}
    os.makedirs(os.path.join(KOK, "data", "futbol"), exist_ok=True)
    json.dump(out, open(os.path.join(KOK, "data", "futbol", "atyarisi_derinlik.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False)[:1500])


def _kaydet():
    """Emek boşa gitmesin: geriye doldururken 10 günde bir repoya yaz (yalnız GitHub Actions'ta)."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    import subprocess
    try:
        for c in (["git", "config", "user.name", "tjk-bot"], ["git", "config", "user.email", "tjk-bot@users.noreply.github.com"], ["git", "add", "-A", "data"]):
            subprocess.run(c, check=False)
        if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
            return
        subprocess.run(["git", "commit", "-qm", "atyarisi arşiv ara kayıt"], check=False)
        for _ in range(3):
            if subprocess.run(["git", "pull", "-q", "--rebase"]).returncode == 0 and subprocess.run(["git", "push", "-q"]).returncode == 0:
                break
            subprocess.run(["git", "rebase", "--abort"], check=False); time.sleep(5)
    except Exception as e:
        print("ara kayıt hatası:", repr(e))


if __name__ == "__main__":
    m = sys.argv[1]
    if m == "derinlik":
        derinlik()
    elif m == "gun":
        t = sys.argv[2] if len(sys.argv) > 2 else (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d")
        print(t, arsivle(t, yenile=True))
    elif m == "geri":
        b, e = datetime.date.fromisoformat(sys.argv[2]), datetime.date.fromisoformat(sys.argv[3]); mx = int(sys.argv[4]) if len(sys.argv) > 4 else 100
        n = 0; d = e
        while d >= b and n < mx:
            try:
                s = arsivle(d.isoformat())
            except Exception as ex:
                print("durduruldu:", d, repr(ex)); break
            if s != "var":
                n += 1
            print(d, s, flush=True); d -= datetime.timedelta(days=1)
            if n and n % 10 == 0 and s != "var":
                _kaydet()
