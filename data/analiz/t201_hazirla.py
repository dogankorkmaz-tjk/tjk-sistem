"""T201 ön hazırlık: eski özellik kodlarının beklediği /tmp/claude-0 tablolarını data/atyarisi arşivinden yeniden üretir
(ekip.pkl, sinifp.pkl, arsiv_mp.pkl, arsiv_kapi.pkl, soy_map.pkl; ay_oz.pkl/ay_gun.pkl için t146_hazirla.py çağrılır).
Yalnız program bilgisi (yarıştan ÖNCE bilinen: ekipman, ikramiye, mesafe, pist, start, soy). Repo kökünden çalışır."""
import os, sys, glob, json, gzip, subprocess
import pandas as pd
sys.path.insert(0, "."); from tjk import ortak as O
T = "/tmp/claude-0"; os.makedirs(T, exist_ok=True)
EK, SN, MP, KP, SOY = [], [], [], [], {}
for f in sorted(glob.glob("data/atyarisi/20*.json.gz")):
    try: j = json.load(gzip.open(f, "rt"))
    except Exception: continue
    t = os.path.basename(f)[:10]
    for kaynak in ("program", "sonuc"):
        for hip, L in (j.get(kaynak) or {}).items():
            if not isinstance(L, list): continue
            for k in L:
                try: kn = int(k["number"])
                except Exception: continue
                m = str(k.get("distance") or ""); D = float(m) if m.isdigit() else float("nan")
                if hip in O.TRH: MP.append((t, hip, kn, D, k.get("raceCourseType") or None))
                if kaynak != "program": continue
                pr = k.get("prizes"); 
                try: p1 = float(pr[0]) if pr else None
                except Exception: p1 = None
                SN.append((t, hip, kn, p1, k.get("typeDescription", ""), m))
                hs = [h for h in (k.get("horses") or []) if h.get("status") is not False]
                for h in k.get("horses") or []:
                    try: no = int(h.get("number"))
                    except Exception: continue
                    EK.append((t, hip, kn, no, str(h.get("equipment") or "").strip()))
                    try: st = float(h.get("start"))
                    except Exception: st = float("nan")
                    KP.append((t, hip, kn, no, st, float(len(hs)), D))
                    p = h.get("parents") or {}; g = lambda x: ((p.get(x) or {}).get("name") or "")
                    if h.get("name"): SOY[str(h["name"])] = (g("father"), g("mother"), g("fatherOfMother"))
pd.DataFrame(EK, columns=["tarih", "hipodrom", "kosu", "no", "ekip"]).drop_duplicates(["tarih", "hipodrom", "kosu", "no"]).to_pickle(T + "/ekip.pkl")
pd.DataFrame(SN, columns=["tarih", "hipodrom", "kosu", "prize1", "tip", "mes"]).drop_duplicates(["tarih", "hipodrom", "kosu"]).to_pickle(T + "/sinifp.pkl")
pd.DataFrame(MP, columns=["tarih", "hip", "kosu", "mesafe", "pist"]).dropna(subset=["mesafe"]).drop_duplicates(["tarih", "hip", "kosu"]).to_pickle(T + "/arsiv_mp.pkl")
pd.DataFrame(KP, columns=["tarih", "hip", "kosu", "no", "start", "n_k", "D"]).drop_duplicates(["tarih", "hip", "kosu", "no"]).to_pickle(T + "/arsiv_kapi.pkl")
import pickle; pickle.dump(SOY, open(T + "/soy_map.pkl", "wb"))
print("ekip", len(EK), "sinif", len(SN), "mp", len(MP), "kapi", len(KP), "soy", len(SOY), flush=True)
if not (os.path.exists(T + "/ay_oz.pkl") and os.path.exists(T + "/ay_gun.pkl")):
    subprocess.run([sys.executable, "data/analiz/t146_hazirla.py"], check=False)
print("ay_oz", os.path.exists(T + "/ay_oz.pkl"), "ay_gun", os.path.exists(T + "/ay_gun.pkl"))
