"""T71 jokey/antrenör hücre etkileri: (jokey,pist), (jokey,hipodrom), (antrenör,pist). Özellik = hücrenin ÖNCEKİ günlerdeki büzmeli ort. bitiş artığı
MİNUS kişinin tüm hücrelerdeki büzmeli ort. artığı (yani pist/hipodroma ÖZGÜ etki; genel jokey/antrenör gücü zaten f_jel/f_tel'de). res = (piyasa sırası yüzdeliği − gerçek yüzdelik), T38 ile aynı.
Büzme n/(n+K), K=20 (hücre) ve K=20 (kişi). Yalnız önceki günlerden; gün içi güncelleme günün sonunda."""
import numpy as np, collections
K = 20.0
def _feat(d, kisi, hucre, gun, res):
    S = collections.defaultdict(float); C = collections.defaultdict(int); SA = collections.defaultdict(float); CA = collections.defaultdict(int)
    f = np.zeros(len(d)); pend = []; cur = None
    for i in range(len(d)):
        if gun[i] != cur:
            for k_, h_, r_ in pend: S[(k_, h_)] += r_; C[(k_, h_)] += 1; SA[k_] += r_; CA[k_] += 1
            pend = []; cur = gun[i]
        k_, h_ = kisi[i], hucre[i]
        if k_ in ("nan", "None", "") or h_ in ("nan", "None", ""): continue
        c = C[(k_, h_)]; f[i] = S[(k_, h_)] / (c + K) - SA[k_] / (CA[k_] + K) if CA[k_] else 0.0
        if np.isfinite(res[i]): pend.append((k_, h_, res[i]))
    return f
def ekle(d):
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    rk = d.groupby(["tarih", "hipodrom", "kosu"]).p_piyasa.rank(ascending=False, method="first")
    res = ((rk - 1) / (d.n_at - 1).clip(lower=1) - d.pct).clip(-1, 1).values
    gun = d.tarih.astype(str).values; jk = d.jokey.astype(str).values; an = d.antrenor.astype(str).values
    pist = d.pist.astype(str).values; hip = d.hipodrom.astype(str).values
    d["f_jp"] = _feat(d, jk, pist, gun, res); d["f_jh"] = _feat(d, jk, hip, gun, res); d["f_tp"] = _feat(d, an, pist, gun, res)
    return d
