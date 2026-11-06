"""Video şeridinden (data/video_seyir, 0,5 sn'de bir ilk-10 sırası) at düzeyi koşu ölçüleri (6 Kasım 2026, T162).
sorunlar(j) → {no: [(t, kayip), ...]}: koşunun %15–%90'ı arasında ≤3 sn içinde ≥3 sıra kayıp (şerit dışına düşme = kutu+1), sonraki 3 sn'de toparlamadan.
olcu(j) → {no: {"son_kazanc", "orta_sira", "erken_sira", "sorun_n", "sorun_kayip"}}; tempo(j) → koşu düzeyi lider bölüm hızları (ilk yarı / ikinci yarı oranı)."""
import numpy as np

PENCERE = 6      # 6 kare = 3 sn
ESIK = 3


def _matris(j):
    z = [x for x in j.get("zaman") or [] if x.get("sira")]
    kapi = list(j.get("numaralar") or [])[: j.get("kutu", 10)]
    while z and z[0]["sira"] == kapi:
        z.pop(0)                                          # start öncesi kapı sırası kareleri
    nos = [int(n) for n in j.get("numaralar") or []]; k = j.get("kutu", 10)
    if len(z) < 20 or not nos: return None, None, nos
    t = np.array([x["t"] for x in z]); R = np.full((len(z), len(nos)), k + 1.0)
    ix = {n: i for i, n in enumerate(nos)}
    for a, x in enumerate(z):
        for r, n in enumerate(x["sira"], 1):
            if n in ix: R[a, ix[n]] = r
    return t, R, nos


def sorunlar(j):
    t, R, nos = _matris(j); out = {}
    if t is None: return out
    L = len(t); a0, a1 = int(L * 0.15), int(L * 0.90)
    for i, n in enumerate(nos):
        r = R[:, i]; son = -99
        for a in range(a0, a1 - PENCERE):
            kayip = r[a + PENCERE] - r[a]
            if kayip >= ESIK and a - son > PENCERE * 2:
                sonra = r[min(L - 1, a + 2 * PENCERE)]
                if sonra - r[a] >= ESIK - 1:                # 3 sn sonra hâlâ geride: geçici okuma hatası değil
                    out.setdefault(n, []).append((float(t[a]), float(kayip))); son = a
    return out


def olcu(j):
    t, R, nos = _matris(j)
    if t is None: return {}
    L = len(t); S = sorunlar(j); n_ = len(nos); out = {}
    for i, n in enumerate(nos):
        r = R[:, i]
        out[n] = {"erken_sira": float(r[: max(1, L // 3)].mean()) / n_, "orta_sira": float(r[L // 3: 2 * L // 3].mean()) / n_,
                  "son_kazanc": float(r[int(L * 0.7): int(L * 0.75) + 1].mean() - r[-max(1, L // 20):].mean()) / n_,
                  "sorun_n": len(S.get(n, [])), "sorun_kayip": float(sum(k for _, k in S.get(n, [])))}
    return out


def tempo(j):
    """Liderin bölüm süreleri (bolum: mesafe işareti → sn). İlk yarı / ikinci yarı ortalama hız oranı (>1: hızlı başlayan tempo)."""
    b = sorted((int(k), v) for k, v in (j.get("bolum") or {}).items() if int(k) < 3600)
    if len(b) < 4: return None
    m = np.array([x[0] for x in b], float); s = np.array([x[1] for x in b], float)
    h = len(b) // 2; v1 = (m[h] - m[0]) / max(1e-6, s[h] - s[0]); v2 = (m[-1] - m[h]) / max(1e-6, s[-1] - s[h])
    return float(v1 / v2) if v2 > 0 else None
