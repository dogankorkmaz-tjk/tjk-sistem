"""Telefona bildirim (ntfy.sh). NTFY_TOPIC ortam değişkeni (GitHub secret) yoksa hiçbir şey göndermez.
Aynı öneri bir kez gönderilir (data/bildirim/<gün>.json). Başlamış koşu/ayak için gönderilmez."""
import os, json
import requests

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI, SITE = os.path.join(KOK, "data"), os.path.join(KOK, "docs", "data")


def _j(a):
    y = os.path.join(SITE, a + ".json")
    return json.load(open(y, encoding="utf-8")) if os.path.exists(y) else {}


def oneriler(simdi):
    """[(anahtar, baslik, mesaj)] — henüz başlamamış, sistemin önerdiği bahisler."""
    out = []
    for r in _j("devir").get("devirler", []):
        if r.get("firsat") and (r.get("ilk_saat") or "00:00") > simdi:
            q = next((x for x in r.get("kuponlar", []) if x["butce"] == 192), (r.get("kuponlar") or [None])[0])
            m = f"Devir {round(r['devir']):,} TL · ilk ayak {r['ilk_saat']}".replace(",", ".")
            if q:
                m += "\n" + " | ".join(",".join(map(str, x)) for x in q["ayaklar"]) + f"\n{q['kombinasyon']} kombinasyon"
            out.append((f"devir|{r['hipodrom']}", f"★ {r['ad']} 7'li ganyan devir fırsatı", m))
    for c in _j("kupon").get("bugun", []):
        if c.get("sonuc") or (c.get("ilk_saat") or "00:00") <= simdi:
            continue
        qs = [q for q in c.get("kuponlar", []) if q["beklenen_getiri_orani"] >= c.get("esik", 1.2) and q["mod"] == "deger"]
        if not qs:
            continue
        m = f"{c.get('ad')} {c['altili']}. altılı ({c['son']-5}–{c['son']}. koşu) · ilk ayak {c['ilk_saat']}"
        for q in sorted(qs, key=lambda x: x["butce"]):
            bed = q.get("bedel", q["kombinasyon"] * 1.25)
            m += f"\n~{q['butce']} ({q['kombinasyon']} komb., {bed:.0f} TL): " + " | ".join(",".join(map(str, x)) for x in q["ayaklar"])
        out.append((f"altili|{c['hipodrom']}|{c['son']}", f"★ Altılı önerisi: {c.get('ad')} {c['altili']}. altılı", m))
    for c in _j("plase").get("bugun", []):          # yalnızca SİB ilk2/3/4 (pari-mutuel plase kanıtlanana dek bildirim yok)
        if c.get("sonuc") or c["tur"] != "sib" or (c.get("saat") or "00:00") <= simdi:
            continue
        for q in c.get("secimler", []):
            out.append((f"sib|{c['hipodrom']}|{c['kosu']}|{q['k']}|{q['no']}", f"★ SİB ilk {q['k']}: {c['hipodrom']} {c['kosu']}. koşu",
                        f"{q['no']} {q['ad']} @{q['oran']} · EV {q['ev']} · koşu {c.get('saat')}"))
    return out


def gonder(tarih, simdi, kuru=False):
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic and not kuru:
        return 0
    y = os.path.join(VERI, "bildirim", tarih + ".json")
    gon = json.load(open(y, encoding="utf-8")) if os.path.exists(y) else {}
    n = 0
    for k, baslik, mesaj in oneriler(simdi):
        if k in gon:
            continue
        if kuru:
            print("[kuru]", baslik, "|", mesaj.replace("\n", " / ")); n += 1; continue
        try:
            r = requests.post("https://ntfy.sh/", json={"topic": topic, "title": baslik, "message": mesaj, "priority": 4, "tags": ["horse"]}, timeout=20)
            if r.ok:
                gon[k] = simdi; n += 1
        except Exception as e:
            print("bildirim hatası:", repr(e))
    if n and not kuru:
        os.makedirs(os.path.dirname(y), exist_ok=True)
        json.dump(gon, open(y, "w", encoding="utf-8"), ensure_ascii=False)
    return n
