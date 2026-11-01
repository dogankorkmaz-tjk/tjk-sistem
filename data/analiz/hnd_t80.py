"""T80. python3 data/analiz/hnd_t80.py"""
import gzip,json,glob,re,unicodedata,random,numpy as np,pandas as pd
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
C={}
for f in sorted(glob.glob('data/atyarisi/20*.json.gz')):
    t=f.split('/')[-1][:10]
    if t<'2024-04-01':continue
    try:d=json.load(gzip.open(f))
    except Exception:continue
    for hip,rs in (d.get('program') or {}).items():
        for r in rs:
            b=re.sub(r'\s+',' ',(r.get('typeDescription') or '').strip().split('/')[0].strip().upper());m=re.match(r'(?:KISA VADE )?HAND[İI]KAP[ -]?(\d+)',b)
            if m:C[(t,asc(hip),int(r['number']))]=int(m.group(1))
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str);P['hipodrom']=P.hipodrom.map(asc)
J=pd.read_pickle('/tmp/claude-0/jason_d.pkl')[['tarih','hipodrom','kosu','no','hnd','kilo','yas_ham']];J['tarih']=J.tarih.astype(str);J['hipodrom']=J.hipodrom.map(asc)
P=P.merge(J.drop_duplicates(['tarih','hipodrom','kosu','no']),on=['tarih','hipodrom','kosu','no'],how='left')
P['hn']=[C.get((t,h,k)) for t,h,k in zip(P.tarih,P.hipodrom,P.kosu)];P=P[P.hn.notna()&P.p_piyasa.notna()&P.sira.notna()].copy()
P['yas_ham']=P.yas_ham.astype(str).str.extract(r'(\d+)')[0]
for c in('hnd','kilo','yas_ham'):P[c]=pd.to_numeric(P[c],errors='coerce')
P['kz']=(pd.to_numeric(P.sira,errors='coerce')==1).astype(float)
g=P.groupby(['tarih','hipodrom','kosu']);P['pm']=P.p_piyasa/g.p_piyasa.transform('sum')
P['hmax']=(P.hnd==g.hnd.transform('max'));P['kmed']=g.kilo.transform('median');P['yq']=g.yas_ham.rank(pct=True)
print('Handikap at',len(P),'koşu',g.ngroups,{n:int((P.hn==n).sum()) for n in sorted(P.hn.unique())},flush=True)
I={'I1 H13 en yüksek hnd':(P.hn==13)&P.hmax,'I2 H14 hnd 40-50':(P.hn==14)&P.hnd.between(40,50),
 'I3 H15 hnd45-60 hafif':(P.hn==15)&P.hnd.between(45,60)&(P.kilo<P.kmed),'I4 H16 hnd60-75 ağır':(P.hn==16)&P.hnd.between(60,75)&(P.kilo>P.kmed),
 'I5 H17 hnd75-85|kilo50-56':(P.hn==17)&(P.hnd.between(75,85)|P.kilo.between(50,56)),'I6 Handikap en genç 1/3':(P.yq<=1/3)}
random.seed(80);gun=sorted(set(P.tarih));ix={t:np.where(P.tarih.values==t)[0] for t in gun}
for ad,m in I.items():
    mm=m.values;a=P.kz.values-P.pm.values;n=int(mm.sum())
    if n<30:print(ad,'n',n,'az');continue
    bs=[]
    for _ in range(600):
        s=np.concatenate([ix[random.choice(gun)] for _ in gun]);q=mm[s]
        if q.sum():bs.append(a[s][q].mean())
    lo,hi=np.percentile(bs,[0.4,99.6])
    print(f'{ad:28s} n={n:5d} kazanma {P.kz.values[mm].mean():.4f} piyasa {P.pm.values[mm].mean():.4f} fark {a[mm].mean():+.4f} GA99,2 [{lo:+.4f},{hi:+.4f}] ({"SAĞLANDI" if lo>0 else "sağlanmadı"})',flush=True)
print('\nModel − piyasa kazanan NLL (negatif=model iyi), Handikap n bazında:')
for n,gg in P.groupby('hn'):
    L=[]
    for _,r in gg.groupby(['tarih','hipodrom','kosu']):
        if r.kz.sum()!=1 or r.p_Jason.isna().any():continue
        pj=r.p_Jason/r.p_Jason.sum();L.append((r.tarih.iloc[0],-np.log(pj[r.kz==1].iloc[0])+np.log(r.pm[r.kz==1].iloc[0])))
    if len(L)<50:continue
    d=np.array([x[1] for x in L]);gt=np.array([x[0] for x in L]);ug=sorted(set(gt));gi={t:np.where(gt==t)[0] for t in ug}
    bs=[d[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(500)]
    print(f'Handikap {int(n)} koşu {len(d)} fark {d.mean():+.4f} [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]')
