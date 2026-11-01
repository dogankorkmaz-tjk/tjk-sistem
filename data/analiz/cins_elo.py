"""T79: koşu cinsi grubuna özgü at Elo'su. f_elo_s = (at, cins grubu) marjlı Elo − alan ortalaması; f_ns = o gruptaki deneyim."""
import gzip, json, glob, re, unicodedata, numpy as np
asc = lambda s: unicodedata.normalize('NFKD', str(s).replace('İ', 'I').replace('ı', 'i')).encode('ascii', 'ignore').decode().lower().strip()
def grup(td):
    b = re.sub(r'\s+', ' ', (td or '').strip().split('/')[0].strip().upper()); m = re.match(r'ŞARTLI (\d)', b)
    if b.startswith('MAIDEN'): return 'M'
    if m: return 'S12' if int(m.group(1)) <= 2 else 'S35'
    if b.startswith('HANDIKAP') or b.startswith('KISA VADE HANDIKAP'): return 'H'
    return 'D'
_C = {}
def _yukle():
    for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
        t = f.split('/')[-1][:10]
        try: d = json.load(gzip.open(f))
        except Exception: continue
        for hip, rs in (d.get('program') or {}).items():
            for r in rs: _C[(t, asc(hip), int(r['number']))] = grup(r.get('typeDescription'))
def ekle(d, elo_fn):
    if not _C: _yukle()
    g = np.array([_C.get((str(t), asc(h), int(k)), 'D') for t, h, k in zip(d.tarih, d.hipodrom, d.kosu)])
    keys = np.array([f"{a}|{c}" for a, c in zip(d['at'].astype(str).values, g)])
    e, _, n = elo_fn(d, keys, "sure"); d["f_elo_s"] = e; d["f_ns"] = n
    return d
