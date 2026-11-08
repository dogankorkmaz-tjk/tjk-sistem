"""Hipotez defterinden (hipotez_defteri.md) özet tablo üretir.
Çıktı: data/analiz/hipotez_ozet.md (okunabilir tablo) ve docs/data/hipotez_ozet.json (site için).
Kullanım: python3 data/analiz/hipotez_ozet.py
Her gece/her test sonrası çalıştırılır; defterdeki yeni 'ÖN KAYIT Txx' ve 'SONUÇ Txx' kayıtları otomatik eklenir.
Not: durum, defterdeki 'Karar:' cümlesinden anahtar sözcüklerle çıkarılır; belirsiz olanlar 'Karar belirsiz' görünür
(uydurma karar yazılmaz)."""
import re, json, sys, pathlib, datetime

KOK = pathlib.Path(__file__).resolve().parents[2]
DEFTER = KOK / 'data/analiz/hipotez_defteri.md'
CIKTI_MD = KOK / 'data/analiz/hipotez_ozet.md'
CIKTI_JSON = KOK / 'docs/data/hipotez_ozet.json'


def tl(s):
    return s.replace('İ', 'i').replace('I', 'ı').lower()


ID = r'T\d+(?:[a-z]|-[A-Za-z]+)?'
RE_ID = re.compile(ID)
RE_BASLIK = re.compile(r'^#{2,4}\s+(.*)$')
RE_SONUC_KELIME = re.compile(r'(SONUÇ|DOĞRULAMA)\s+(' + ID + r'(?:\s*[;,/+&]\s*' + ID + r')*)')
RE_ONKAYIT = re.compile(r'ÖN KAYIT\s+(' + ID + r'(?:\s*[;,/+&]\s*' + ID + r')*)')
RE_KARAR = re.compile(r'(?:^|[\s\-•*])(KARAR|Karar)\b')

ELENDI = re.compile(r'sağlanmadı|eklenmez|eklenmedi|açılmaz|kapatıldı|etki yok|elendi|terk|vazgeç|çıkmadı|bilgi taşımıyor|kanıt yok|anlamlı değil|anlamsız|fayda yok|fayda sağlamad|kurala uymad|geçilemedi|başarısız|model değişikliği yok|değiştirmez|ek bilgi vermiyor')
GECTI = re.compile(r'sağlandı|doğrulandı|geçildi|\bgeçti\b|kabul edil|eklenir|üretime (?:alın|ekle)')
TANIM = re.compile(r'karar yok|keşif|tanımlayıcı|karar çıkmaz|örnek çok küçük|sonuç yok')
ADAY = re.compile(r'aday|yeniden test|tekrar test|ocak 2027|mart 2027|nisan 2027|ileri takip')


def tl(s):
    return s.replace('İ', 'i').replace('I', 'ı').lower()


def durum_cikar(karar, acik=True):
    """İlk geçen anahtar sözcük kazanır (cümlenin ilk hükmü); ikinci hüküm genelde ayrı bir konudur."""
    k = tl(karar)
    e, g = ELENDI.search(k), GECTI.search(k)
    if e and g and not acik:
        return 'Karma (hem olumlu hem olumsuz ifade, deftere bak)'
    if e and (not g or e.start() < g.start()):
        d = 'Elendi'
    elif g:
        d = 'Geçti'
    elif ADAY.search(k) and re.search(r'aday', k):
        return 'Aday / ileri takipte'
    elif TANIM.search(k):
        return 'Tanımlayıcı / keşif (karar yok)'
    else:
        return 'Karar belirsiz'
    if ADAY.search(k) and d != 'Geçti':
        d += ' (yeniden test planlı)'
    return d


def kisalt(s, n=230):
    s = re.sub(r'\s+', ' ', s).strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'


def bolunmus_basliklar(baslik, ids):
    """'T44 gün içi kapı...; T45 piyasa-ağırlığı...' başlığını id başına parçalar."""
    parca = {}
    pos = [(m.start(), m.group(0)) for m in RE_ID.finditer(baslik)]
    for n, (b, tid) in enumerate(pos):
        if tid not in ids:
            continue
        son = pos[n + 1][0] if n + 1 < len(pos) else len(baslik)
        parca[tid] = baslik[b + len(tid):son].strip(' :;,/+&—-')
    return parca


def ayristir():
    satirlar = DEFTER.read_text(encoding='utf-8').split('\n')
    kayit = {}
    i = 0
    n = len(satirlar)
    while i < n:
        s = satirlar[i]
        mb = RE_BASLIK.match(s)
        govde_baslangic = s
        if mb:
            govde_baslangic = mb.group(1).strip()
            mo = RE_ONKAYIT.search(govde_baslangic)
            if mo:
                ids = RE_ID.findall(govde_baslangic[mo.start(1):])
                tarih = re.match(r'(\d{4}-\d{2}-\d{2}|\d{1,2} \w+ \d{4})', govde_baslangic)
                kalan = govde_baslangic[mo.end(1):]
                parcalar = bolunmus_basliklar(govde_baslangic[mo.start(1):], ids)
                for tid in ids:
                    r = kayit.setdefault(tid, {'id': tid, 'sonuclar': []})
                    r.setdefault('konu', parcalar.get(tid) or kalan.strip(' :—-'))
                    r.setdefault('tarih', tarih.group(1) if tarih else '')
        ms = RE_SONUC_KELIME.search(govde_baslangic[:90]) if (mb or re.match(r'^(SONUÇ|DOĞRULAMA)\s+T', s)) else None
        if ms and not RE_ONKAYIT.search(govde_baslangic[:90]):
            ids = RE_ID.findall(ms.group(2))
            blok = [s]
            j = i + 1
            while j < n and not RE_BASLIK.match(satirlar[j]) and not re.match(r'^(SONUÇ|DOĞRULAMA|ÖN KAYIT)\s+T\d', satirlar[j]) \
                    and j - i < 60:
                blok.append(satirlar[j])
                j += 1
            karar = ''
            for ln in blok[1:] + blok[:1]:      # önce gövde (son karar), sonra başlık satırı
                pass
            adaylar = [ln for ln in blok if RE_KARAR.search(ln)]
            if adaylar:
                ln = adaylar[-1]
                mk = RE_KARAR.search(ln)
                karar = ln[mk.start(1):]
                # kararın devam satırı varsa ekle
                idx = blok.index(ln)
                if idx + 1 < len(blok) and not RE_KARAR.search(blok[idx + 1]):
                    karar += ' ' + blok[idx + 1].strip()
            metin = ' '.join(blok)
            for tid in ids:
                r = kayit.setdefault(tid, {'id': tid, 'sonuclar': []})
                r['sonuclar'].append({'satir': i + 1, 'metin': metin, 'karar': karar})
            i = j
            continue
        i += 1
    return kayit


def tablo_satiri(r):
    konu = kisalt(r.get('konu', '') or '(başlık yok)', 110)
    if not r['sonuclar']:
        return {'id': r['id'], 'konu': konu, 'tarih': r.get('tarih', ''),
                'durum': 'Sonuç bekleniyor', 'ozet': '', 'neden': '', 'satir': 0}
    son = r['sonuclar'][-1]
    karar = son['karar']
    if karar:
        durum = durum_cikar(karar)
    else:
        durum = durum_cikar(son['metin'][-300:], acik=False)
        if durum != 'Karar belirsiz':
            durum += ' ~'
            karar = '(açık karar satırı yok, son cümlelerden çıkarıldı) ' + son['metin'][-200:]
    govde = re.sub(r'^#*\s*(?:[\d\- :]+)?(?:—\s*)?(SONUÇ|DOĞRULAMA)\s+' + ID + r'\s*', '', son['metin'])
    for kes in ('KARAR', 'Karar'):
        govde = govde.split(kes)[0]
    return {'id': r['id'], 'konu': konu, 'tarih': r.get('tarih', ''), 'durum': durum,
            'ozet': kisalt(govde, 230), 'neden': kisalt(karar, 260), 'satir': son['satir']}


def sirala(satir):
    m = re.match(r'T(\d+)', satir['id'])
    return (int(m.group(1)) if m else 9999, satir['id'])


def duzeltmeler():
    f = KOK / 'data/analiz/hipotez_duzeltme.json'
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}


def main():
    kayit = ayristir()
    satirlar = sorted((tablo_satiri(r) for r in kayit.values()), key=sirala)
    dz = duzeltmeler()
    for s_ in satirlar:        # elle düzeltme: {"T45": {"durum": "Elendi", "neden": "..."}}
        if s_['id'] in dz:
            s_.update(dz[s_['id']])
            s_['durum'] = s_['durum'].rstrip(' ~')
    sayim = {}
    for s in satirlar:
        anahtar = s['durum'].split(' (')[0].rstrip(' ~')
        sayim[anahtar] = sayim.get(anahtar, 0) + 1

    md = ['# Hipotez özeti (otomatik üretilir, elle düzenlemeyin)',
          f'Güncelleme: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")} · kaynak: data/analiz/hipotez_defteri.md', '',
          'Durumdaki "~" işareti: defterde açık "Karar:" satırı yok, son cümlelerden çıkarıldı (doğrulanmamış). Düzeltmek için data/analiz/hipotez_duzeltme.json.', '', 'Toplam: ' + ' · '.join(f'{k}: {v}' for k, v in sorted(sayim.items(), key=lambda x: -x[1])), '']
    for grup, baslik in (('Geçti', 'Geçenler (kural sağlandı)'),
                         ('Elendi', 'Elenenler (modele eklenmedi / kural sağlanmadı)'),
                         ('Aday / ileri takipte', 'Aday: ileri takipte (henüz kanıt değil)'),
                         ('Karma', 'Karma sonuç (bir kısmı geçti, bir kısmı olmadı)'),
                         ('Tanımlayıcı / keşif', 'Tanımlayıcı / keşif (karar kuralı yok)'),
                         ('Karar belirsiz', 'Sonuç var ama karar cümlesi ayrıştırılamadı (deftere bak)'),
                         ('Sonuç bekleniyor', 'Ön kayıtlı, sonucu henüz yok')):
        grp = [s for s in satirlar if s['durum'].split(' (')[0].rstrip(' ~') == grup]
        if not grp:
            continue
        md += [f'## {baslik} — {len(grp)}', '', '| # | Konu | Durum | Sonuç ölçüsü | Karar / neden |', '|---|---|---|---|---|']
        for s in grp:
            esc = lambda t: t.replace('|', '\\|')
            md.append(f"| {s['id']} | {esc(s['konu'])} | {s['durum']} | {esc(s['ozet'])} | {esc(s['neden'])} |")
        md.append('')
    yeni_md = '\n'.join(md)
    eski = CIKTI_MD.read_text(encoding='utf-8') if CIKTI_MD.exists() else ''
    if re.sub(r'Güncelleme:[^\n]*', '', eski) == re.sub(r'Güncelleme:[^\n]*', '', yeni_md):
        print('içerik değişmedi'); return
    CIKTI_MD.write_text(yeni_md, encoding='utf-8')
    CIKTI_JSON.parent.mkdir(parents=True, exist_ok=True)
    CIKTI_JSON.write_text(json.dumps({'guncelleme': datetime.datetime.now().isoformat(timespec='minutes'),
                                      'sayim': sayim, 'testler': satirlar}, ensure_ascii=False, indent=1), encoding='utf-8')
    print('test sayısı', len(satirlar), sayim)


if __name__ == '__main__':
    main()
