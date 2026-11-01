"""T77/T78. python3 data/analiz/sirali_t77_t78.py"""
import sys,glob,re,gzip,json,unicodedata,random,numpy as np,pandas as pd
from multiprocessing import Pool
sys.path.insert(0,'.')
from tjk import besli
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
OP='/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl'
def cins(td):
    b=re.sub(r'\s+',' ',(td or '').strip().split('/')[0].strip().upper());m=re.match(r'ŞARTLI (\d)',b)
    if b.startswith('MAIDEN'):return 'Maiden'
    if m:return 'Şartlı1-2' if int(m.group(1))<=2 else 'Şartlı3+'
    if b.startswith('HANDIKAP') or b.startswith('KISA VADE HANDIKAP'):return 'Handikap'
    return 'Diğer'
C={}
for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
    t=f.split('/')[-1][:10]
    if t<'2025-01-01':continue
    try:d=json.load(gzip.open(f))
    except Exception:continue
    for hip,rs in (d.get('program') or {}).items():
        for r in rs:C[(t,asc(hip),int(r['number']))]=cins(r.get('typeDescription'))
P=pd.read_pickle(OP);P['tarih']=P.tarih.astype(str);P['hipodrom']=P.hipodrom.map(asc);P=P[(P.tarih>='2025-01-01')&P.p_Jason.notna()]
PP={k:g.sort_values('no') for k,g in P.groupby(['tarih','hipodrom','kosu'])}
O=pd.concat([pd.read_csv(f) for f in glob.glob('data/odeme/*.csv.gz')]);O=O[O.tur.str.startswith('SIRALI 5')].drop_duplicates(['tarih','hipodrom','kosu']);O['tarih']=O.tarih.astype(str);O['hipodrom']=O.hipodrom.map(asc);O=O[O.tarih>='2025-01-01']
parse=lambda k:[set(int(x) for x in s.split(',')) for s in str(k).split('/')]
def isle(r):
    t,h,k=r['tarih'],r['hipodrom'],int(r['kosu']);out=[]
    # ilk ayak koşusu: kosu numarası kombo 5 ayağın ilkidir; odeme.kosu = ilk ayak
    ayak=[PP.get((t,h,k+j)) for j in range(5)]
    if any(a is None or len(a)<5 for a in ayak):return out
    devir=str(r['tur']).endswith('DEVİR')
    if devir:return out
    win=parse(r['kombo'])
    # sıralı 5'li: tek koşu, 5 sıra. odeme.kosu = koşu; kombo = 5 sıra kümesi
    g=PP.get((t,h,k))
    if g is None or len(g)<5:return out
    nos=g.no.tolist();p=g.p_Jason.values.astype(float);p=list(p/p.sum());pm=g.p_piyasa.values/g.p_piyasa.sum()
    for B in (48,96,150):
        o=besli.kupon_g(p,B,list(besli.G_M))
        if not o:continue
        sets,pr=o;cost=besli.gecerli_say(sets)*besli.BIRIM
        hit=all(any(nos[i] in win[j] for i in sets[j]) for j in range(5))
        out.append((t,h,k,B,cost,hit,float(r['tutar']) if hit else 0.0,pr,C.get((t,h,k),'Diğer'),len(g),float(pm.max())))
    return out
if __name__=='__main__':
    # not: sıralı 5'li tek koşunun ilk 5'i; yukarıdaki ayak kontrolü gereksiz -> yalnız g gerekli
    import types
    rows=[]
    with Pool(4) as pl:
        for x in pl.imap(isle,O.to_dict('records'),chunksize=8):rows+=x
    d=pd.DataFrame(rows,columns=['t','h','k','B','cost','hit','pay','pr','cins','n','fav']);d.to_csv('/tmp/claude-0/t77.csv',index=False)
    d['alan']=pd.cut(d.n,[0,8,11,99],labels=['≤8','9–11','≥12']).astype(str);d['favg']=pd.cut(d.fav,[0,.25,.40,1],labels=['<.25','.25–.40','>.40']).astype(str)
    d['yari']=np.where(d.t<'2026-04','H1','H2');random.seed(77)
    def roi(s):return (s.pay.sum()-s.cost.sum())/s.cost.sum()
    def kiyas(s,m):
        gun=sorted(set(s.t));gi={g:s[s.t==g] for g in gun};bs=[]
        for _ in range(500):
            z=pd.concat([gi[random.choice(gun)] for _ in gun]);a=z[m.reindex(z.index,fill_value=False)] if False else None
        return None
    for B in (48,96,150):
        x=d[d.B==B].reset_index(drop=True);print(f'\n=== B={B}: koşu {len(x)} tutan {int(x.hit.sum())} ROI {roi(x):+.1%} beklenen tutan {x.pr.sum():.1f}')
        for kol in ('cins','alan','favg'):
            hucre=sorted(set(x[kol]));nh=len(hucre)
            for h_ in hucre:
                m=(x[kol]==h_);s=x[m];r_=x[~m]
                if len(s)<30:print(f'{kol:5s} {h_:10s} n={len(s)} (az)');continue
                gun=sorted(set(x.t));gs={g:(s[s.t==g],r_[r_.t==g]) for g in gun};bs=[]
                for _ in range(400):
                    ch=[random.choice(gun) for _ in gun];a=pd.concat([gs[g][0] for g in ch]);b=pd.concat([gs[g][1] for g in ch])
                    if a.cost.sum()>0 and b.cost.sum()>0:bs.append(roi(a)-roi(b))
                lo,hi=np.percentile(bs,[100*0.025/nh,100*(1-0.025/nh)])
                yarı=' '.join(f"{y}:{roi(s[s.yari==y]):+.0%}/{roi(r_[r_.yari==y]):+.0%}" for y in ('H1','H2') if len(s[s.yari==y]) and len(r_[r_.yari==y]))
                ex=s.pr.sum();ob=int(s.hit.sum());from scipy.stats import poisson
                plo=poisson.ppf(.025,ex) if ex>0 else 0;phi=poisson.ppf(.975,ex)
                print(f'{kol:5s} {h_:10s} n={len(s):4d} tutan {ob:2d} beklenen {ex:5.1f} oran {ob/ex if ex else 0:.2f} (Poisson aralık {plo:.0f}-{phi:.0f}) ROI {roi(s):+.0%} fark {roi(s)-roi(r_):+.0%} GA[{lo:+.0%},{hi:+.0%}] {yarı}',flush=True)
