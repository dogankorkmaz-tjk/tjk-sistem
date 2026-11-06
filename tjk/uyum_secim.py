"""T131: uyum skoru (dondurulmuş) + AGF sırası → seçim kaydı. Kural: AGF sırası >=3 ∧ uyum sırası <=2. Kullanım: python3 tjk/uyum_secim.py [YYYY-MM-DD]
Yazar: data/t131_kayit/<gun>_secim.csv ve docs/data/uyum_secim.json. Sonuç görülmeden kural değişmez.
6 Kasım 2026 (kayıt yöntemi, kural DEĞİL): (a) yalnız henüz BAŞLAMAMIŞ koşular kaydedilir (saat > şimdi TR); (b) bir koşu bir kez kaydedildi mi DONAR
(sonraki çalıştırmalar o koşunun seçimini/AGF'sini değiştirmez); (c) her satıra kayıt saati yazılır. Günlük otomatik çağrı: calistir canlı modu (gunluk())."""
import sys, json, os, datetime, subprocess
import pandas as pd

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _tr_simdi():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))


def kaydet(gun=None):
    os.chdir(KOK)
    B = json.load(open('docs/data/bugun.json', encoding='utf-8'))
    gun = gun or B['tarih']
    yu = f'data/t131_kayit/{gun}_uyum.csv'
    if not os.path.exists(yu):
        print('T131: uyum puanı yok', yu); return None
    U = pd.read_csv(yu)
    f = f'data/agf_zaman/{gun}.csv.gz'
    if not os.path.exists(f):
        print('T131: AGF yok', f); return None
    A = pd.read_csv(f); A = A.sort_values('saat').groupby(['hipodrom', 'kosu', 'no'], as_index=False).tail(1)       # son anlık görüntü
    simdi = _tr_simdi(); hhmm = simdi.strftime('%H:%M')
    saat = {}
    if B.get('tarih') == gun:
        for h in B['hipodromlar']:
            for k in h['kosular']:
                saat[(h['id'], int(k['kosu']))] = k.get('saat')
    ys = f'data/t131_kayit/{gun}_secim.csv'
    eski = pd.read_csv(ys) if os.path.exists(ys) else pd.DataFrame()
    kayitli = set(zip(eski.hipodrom, eski.kosu)) if len(eski) else set()
    M = U.merge(A[['hipodrom', 'kosu', 'no', 'agf', 'saat']], on=['hipodrom', 'kosu', 'no'], how='left')
    M['rkA'] = M.groupby(['hipodrom', 'kosu']).agf.rank(ascending=False, method='first')
    M['secim'] = (M.rkA >= 3) & (M.rkU <= 2)
    M['kayit_saati'] = simdi.strftime('%Y-%m-%d %H:%M')
    yeni = [(h, k) for (h, k), g in M.groupby(['hipodrom', 'kosu'])
            if (h, k) not in kayitli and g.agf.notna().all() and saat.get((h, int(k))) and saat[(h, int(k))] > hhmm]
    Y = M[[hk in set(yeni) for hk in zip(M.hipodrom, M.kosu)]]
    T = pd.concat([eski, Y], ignore_index=True) if len(eski) else Y
    if len(Y):
        os.makedirs('data/t131_kayit', exist_ok=True); T.to_csv(ys, index=False)
    out = {'gun': gun, 'olusturma': simdi.strftime('%Y-%m-%d %H:%M TR'),
           'kural': 'AGF sırası >=3 ve uyum sırası <=2 (T131, deneysel, bahis önerisi değil)', 'kosular': []}
    for (h, k), g in (T.groupby(['hipodrom', 'kosu']) if len(T) else []):
        s = g[g.secim.astype(bool)].sort_values('rkU')
        out['kosular'].append({'hipodrom': h, 'kosu': int(k), 'saat': saat.get((h, int(k))), 'agf_saat': g.saat.dropna().iloc[0] if g.saat.notna().any() else None,
                               'kayit_saati': g.kayit_saati.iloc[0] if 'kayit_saati' in g and g.kayit_saati.notna().any() else None,
                               'secimler': [{'no': int(r.no), 'at': r.at, 'uyum_sirasi': int(r.rkU), 'agf_sirasi': int(r.rkA), 'agf': float(r.agf), 'U': round(float(r.U), 3)} for r in s.itertuples()]})
    out['kosular'].sort(key=lambda x: (x['saat'] or '', x['hipodrom'], x['kosu']))
    json.dump(out, open('docs/data/uyum_secim.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('T131', gun, '| yeni kaydedilen koşu', len(yeni), '| toplam kayıtlı', len(kayitli) + len(yeni), '| seçim', int(T.secim.astype(bool).sum()) if len(T) else 0)
    return out


def gunluk():
    """Canlı modda her çalıştırmada: bugünün uyum puanı yoksa üret (~50 sn, piyasasız, yalnız önceki günler), sonra başlamamış koşuları kaydet."""
    try:
        os.chdir(KOK)
        gun = json.load(open('docs/data/bugun.json', encoding='utf-8'))['tarih']
        if not os.path.exists(f'data/t131_kayit/{gun}_uyum.csv'):
            r = subprocess.run([sys.executable, 'data/analiz/t131_bugun.py'], capture_output=True, text=True, timeout=600)
            print('T131 uyum puanı üretildi' if r.returncode == 0 else 'T131 uyum hatası: ' + (r.stderr or '')[-300:])
        kaydet(gun)
    except Exception as e:
        print('T131 günlük hata:', repr(e))


if __name__ == '__main__':
    kaydet(sys.argv[1] if len(sys.argv) > 1 else None)
