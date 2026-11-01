"""T70 doğrudan karşılaşma (head-to-head): aynı koşuda yarışan atların ÖNCEKİ günlerde birbirine karşı geçmişi.
f_h2h_s = Σ_j Σ_(ortak geçmiş koşu) sign(sıra_j − sıra_i) / (Σ N_ij + 3)  (+ = i rakiplerin önünde bitirdi)
f_h2h_m = Σ_j Σ clip((rel_j − rel_i)/derece_min·100, −5, 5) / (Σ N_ij + 3)   (rel = saniye geride; boy farkı vekili, mesafeden bağımsız yüzde)
f_h2h_n = log1p(Σ_j N_ij)/3 (kaç ortak geçmiş karşılaşma). Yalnız önceki günlerden; gün içi güncelleme günün sonunda."""
import collections, numpy as np
def ekle(d):
    d = d.sort_values(["tarih", "hipodrom", "kosu", "no"]).reset_index(drop=True)
    rid = d.groupby(["tarih", "hipodrom", "kosu"]).ngroup().values; tar = d.tarih.astype(str).values; at = d["at"].astype(str).values
    sr = np.asarray(d.sira, dtype=float); sr = np.nan_to_num(sr, nan=0.0)
    rel = np.asarray(d.rel_sure, dtype=float)
    wt = d.groupby(["tarih", "hipodrom", "kosu"]).derece_sn.transform("min").values.astype(float)
    pct = rel / np.where(wt > 0, wt, np.nan) * 100.0
    SS = collections.defaultdict(float); SM = collections.defaultdict(float); NN = collections.defaultdict(int)
    fs = np.zeros(len(d)); fm = np.zeros(len(d)); fn = np.zeros(len(d))
    bas = np.r_[0, np.nonzero(np.diff(tar != np.r_[tar[:1], tar[:-1]]) )[0] + 1] if False else None
    gun_idx = {}
    for i, t in enumerate(tar): gun_idx.setdefault(t, []).append(i)
    for t in sorted(gun_idx):
        ix = np.array(gun_idx[t]); races = collections.defaultdict(list)
        for i in ix: races[rid[i]].append(i)
        pend = []
        for r_, idx in races.items():
            for i in idx:
                s = m = 0.0; n = 0
                for j in idx:
                    if j == i: continue
                    k = (at[i], at[j]); n_ = NN.get(k, 0)
                    if n_: s += SS[k]; m += SM[k]; n += n_
                fs[i] = s / (n + 3); fm[i] = m / (n + 3); fn[i] = np.log1p(n) / 3.0
            ok = [i for i in idx if sr[i] > 0]
            if len(ok) >= 2: pend.append(ok)
        for ok in pend:                                  # gün sonunda güncelle (gün içi sızıntı yok)
            for a in ok:
                for b in ok:
                    if a == b: continue
                    k = (at[a], at[b]); NN[k] += 1; SS[k] += np.sign(sr[b] - sr[a])
                    if np.isfinite(pct[a]) and np.isfinite(pct[b]): SM[k] += float(np.clip(pct[b] - pct[a], -5, 5))
    d["f_h2h_s"] = fs; d["f_h2h_m"] = fm; d["f_h2h_n"] = fn
    return d
