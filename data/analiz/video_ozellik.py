"""T41 video özellikleri (hipotez_defteri 2026-10-28 12:58). Her at için yalnız ÖNCEKİ günlerin videolu koşularından, büzmeli (n/(n+5)) ortalamalar.
f_v1 stil (erken sıra, 0=önde 1=arkada), f_v2 kapanış kazancı (orta−geç)/(n−1), f_v3 yer kaybı (geç−erken)/(n−1), f_v4 tempo-düzeltmeli kapanış
(f_v2 × (bu koşunun son400/önceki400 oranının koşular arası z'si)), f_v5 = (koşudaki önden gidici sayısı) × (0,5 − f_v1).
NOT: ara süre ('bolum') koşu düzeyidir (yayında önde gidenin süresi), at bazlı değildir; f_v4 bu yüzden koşu temposuyla düzeltilmiş kapanıştır."""
import glob, json, os, numpy as np, pandas as pd, collections
K = 5.0
def _seri(j, n):
    """Zaman serisinden ince pencereli özellikler (T50): v6 çıkış (ilk %10 kare ort. göreli sıra), v7 son hamle (%80 sırası − son sıra)/(n−1), v8 erken kazanç (%10 sırası − %40 sırası)/(n−1)."""
    z = [x["sira"] for x in j["zaman"] if x["sira"]]; kapi = list(j["numaralar"])[:j.get("kutu", 10)]
    while z and z[0] == kapi: z.pop(0)
    L = len(z)
    if L < 10: return {}
    k = j.get("kutu", 10); arka = (k + 1 + n) / 2.0
    def yer(fr, a): return fr.index(a) + 1 if a in fr else arka
    ip = lambda lo, hi: z[int(L * lo):max(int(L * hi), int(L * lo) + 1)]
    out = {}
    for a in j["numaralar"]:
        c = np.mean([yer(fr, a) for fr in ip(0.0, 0.1)]); m10 = np.mean([yer(fr, a) for fr in ip(0.08, 0.12)]); m40 = np.mean([yer(fr, a) for fr in ip(0.38, 0.42)])
        m80 = np.mean([yer(fr, a) for fr in ip(0.78, 0.82)]); son = yer(z[-1], a)
        out[int(a)] = ((c - 1) / (n - 1) - 0.5, (m80 - son) / (n - 1), (m10 - m40) / (n - 1))
    return out
def _yukle():
    S = []
    for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video_seyir", "20*.json")):
        b = os.path.basename(f)[:-5].split("_")
        if len(b) != 3: continue
        try: j = json.load(open(f))
        except Exception: continue
        if j.get("okuyucu") != "rakam1" or not j.get("ozet"): continue
        bl = {int(k): v for k, v in j.get("bolum", {}).items() if k.isdigit() and int(k) % 200 == 0 and int(k) <= 3000}
        fade = bl[400] / (bl[800] - bl[400]) if 400 in bl and 800 in bl and bl[800] > bl[400] else np.nan
        n = max(len(j["numaralar"]), 2); ek = _seri(j, n)
        for no, o in j["ozet"].items():
            e6, e7, e8 = ek.get(int(no), (np.nan, np.nan, np.nan))
            S.append((b[0], b[1], int(b[2]), int(no), (o["erken"] - 1) / (n - 1), o["kazanc_gec"] / (n - 1), o["kayip_gec"] / (n - 1), fade, e6, e7, e8))
    V = pd.DataFrame(S, columns=["tarih", "hipodrom", "kosu", "no", "v1", "v2", "v3", "fade", "v6", "v7", "v8"])
    z = (V.fade - V.fade.mean()) / (V.fade.std() + 1e-9); V["v4"] = np.where(np.isfinite(z), V.v2 * z, 0.0)
    return V
def ekle(d):
    V = _yukle(); d = d.drop(columns=[c for c in ["f_v1", "f_v2", "f_v3", "f_v4", "f_v5", "f_v6", "f_v7", "f_v8"] if c in d])
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    V = V.merge(d[["tarih", "hipodrom", "kosu", "no", "at"]], on=["tarih", "hipodrom", "kosu", "no"], how="inner")
    if os.environ.get("PLACEBO"):                      # plasebo: aynı gün içinde video satırlarının at kimliği karıştırılır (özellikler değişmez)
        rg = np.random.default_rng(12345); V = V.copy()
        for t_, ix_ in V.groupby("tarih").indices.items():
            V.iloc[ix_, V.columns.get_loc("at")] = rg.permutation(V["at"].values[ix_])
    H = collections.defaultdict(lambda: np.zeros(8)); Vk = V.sort_values("tarih"); pend = collections.defaultdict(list)
    bygun = {t: g for t, g in Vk.groupby("tarih")}
    gunler = sorted(set(d.tarih))
    out = np.zeros((len(d), 8)); pos = {}
    for i, (t, h, k, at) in enumerate(zip(d.tarih.values, d.hipodrom.values, d.kosu.values, d["at"].values)): pos.setdefault(t, []).append(i)
    for t in gunler:
        ix = pos[t]
        for i in ix:
            a = d["at"].values[i]
            if a in H and H[a][0] > 0:
                s = H[a]; w = s[0] / (s[0] + K)
                out[i, 0] = w * (s[1] / s[0] - 0.5); out[i, 1] = w * s[2] / s[0]; out[i, 2] = w * s[3] / s[0]; out[i, 3] = w * s[4] / s[0]; out[i, 5:8] = w * s[5:8] / s[0]
        g = d.iloc[ix][["hipodrom", "kosu"]].assign(i=ix).assign(v1=out[ix, 0]); g["nf"] = (g.v1 < -0.2).groupby([g.hipodrom, g.kosu]).transform("sum")
        for i, nf in zip(g.i.values, g.nf.values): out[i, 4] = nf * (0.0 - out[i, 0])
        if t in bygun:
            for r in bygun[t].itertuples():
                s = H[r.at]; s[0] += 1; s[1] += r.v1; s[2] += r.v2; s[3] += r.v3; s[4] += (0.0 if not np.isfinite(r.v4) else r.v4); s[5] += (0.0 if not np.isfinite(r.v6) else r.v6); s[6] += (0.0 if not np.isfinite(r.v7) else r.v7); s[7] += (0.0 if not np.isfinite(r.v8) else r.v8)
    for j, c in enumerate(["f_v1", "f_v2", "f_v3", "f_v4", "f_v5", "f_v6", "f_v7", "f_v8"]): d[c] = out[:, j]
    return d
