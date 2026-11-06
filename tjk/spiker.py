"""Spiker anlatımı → yazı (6 Kasım 2026, kullanıcı fikri; yoklama: hipotez_defteri 22:13).
Video listesi resmî atyarisi arşivinden (data/atyarisi/<gün>.json.gz → sonuc[].video). Video indirilir, ses çıkarılır, faster-whisper 'small'
(CPU int8, Türkçe) ile yazıya dökülür, video silinir. Çıktı: data/spiker/<YYYY-MM>/<tarih>_<hip>_<koşu>.json.gz = {"model", "url", "sure", "seg": [[bas, son, metin], ...]}.
Nezaket: indirmeler sırayla ve aralarında ≥2 sn; çalıştırma başına üst sınır (N).
Kullanım: python3 -m tjk.spiker calis N [PAY TOPLAM]   (önce dünün eksikleri, sonra arşivden en yeniden geriye; en çok N video;
          PAY/TOPLAM: paralel işler listeyi paylaşır — iş PAY, sırası PAY mod TOPLAM olan videoları alır)
          python3 -m tjk.spiker gun YYYY-MM-DD"""
import os, sys, json, gzip, glob, time, subprocess, tempfile, datetime as dt
from multiprocessing import Pool

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
MODEL = "small"
_M = None


def yol(tarih, hip, kosu):
    return os.path.join(KOK, "data", "spiker", tarih[:7], f"{tarih}_{hip}_{kosu}.json.gz")


def liste(gunler=None):
    """(tarih, hip, koşu, url) — arşivde videosu olan ve henüz yazıya dökülmemiş koşular."""
    F = sorted(glob.glob(os.path.join(KOK, "data", "atyarisi", "20*.json.gz")), reverse=True)
    out = []
    for f in F:
        t = os.path.basename(f)[:10]
        if gunler and t not in gunler:
            continue
        try:
            j = json.load(gzip.open(f))
        except Exception:
            continue
        for hip, L in (j.get("sonuc") or {}).items():
            for r in L or []:
                u = r.get("video"); k = r.get("number")
                if u and k is not None and not os.path.exists(yol(t, hip, int(k))):
                    out.append((t, hip, int(k), u))
    return out


def _model():
    global _M
    if _M is None:
        from faster_whisper import WhisperModel
        _M = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=1, num_workers=1)
    return _M


def _yaz(is_):
    t, hip, k, u, mp4 = is_
    import numpy as np, wave
    try:
        with tempfile.TemporaryDirectory() as d:
            w = os.path.join(d, "a.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vn", "-ac", "1", "-ar", "16000", w], check=True)
            ww = wave.open(w); a = np.frombuffer(ww.readframes(ww.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        seg, info = _model().transcribe(a, language="tr", vad_filter=False, beam_size=5)
        S = [[round(s.start, 1), round(s.end, 1), s.text.strip()] for s in seg]
        os.makedirs(os.path.dirname(yol(t, hip, k)), exist_ok=True)
        json.dump({"model": MODEL, "url": u, "sure": round(len(a) / 16000, 1), "seg": S}, gzip.open(yol(t, hip, k), "wt", encoding="utf-8"), ensure_ascii=False)
        return t, hip, k, "tamam", len(S)
    except Exception as e:
        return t, hip, k, "hata:" + repr(e)[:80], 0
    finally:
        try: os.remove(mp4)
        except Exception: pass


def calis(isler):
    tmp = tempfile.mkdtemp(); n = 0
    def indir():
        for t, hip, k, u in isler:
            mp4 = os.path.join(tmp, f"{t}_{hip}_{k}.mp4")
            r = subprocess.run(["curl", "-s", "-m", "180", "-A", UA, "-e", "https://www.tjk.org/", "-o", mp4, "-w", "%{http_code}", u], capture_output=True, text=True)
            time.sleep(2)
            if r.stdout.strip() == "200" and os.path.exists(mp4) and os.path.getsize(mp4) > 100000:
                yield (t, hip, k, u, mp4)
            else:
                print("indirilemedi", t, hip, k, r.stdout.strip(), flush=True)
    with Pool(max(1, os.cpu_count() or 1)) as p:
        for r in p.imap_unordered(_yaz, indir()):
            n += r[3] == "tamam"; print(*r, flush=True)
    return n


if __name__ == "__main__":
    if sys.argv[1] == "gun":
        I = liste({sys.argv[2]})
    elif sys.argv[1] == "tek":                     # tek TARIH_HİP_KOŞU ... (belirli koşular)
        H = {tuple(x.rsplit("_", 2)) for x in sys.argv[2:]}
        I = [x for x in liste({h[0] for h in H}) if (x[0], x[1], str(x[2])) in H]
    else:
        N = int(sys.argv[2]); dun = (dt.date.today() - dt.timedelta(days=1)).isoformat()
        I = liste({dun}) + [x for x in liste() if x[0] != dun]
        pay, top = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
        I = I[pay::top][:N]
    t0 = time.time(); print("iş", len(I), flush=True)
    n = calis(I); print(f"tamam {n}/{len(I)} | {time.time() - t0:.0f} sn", flush=True)
