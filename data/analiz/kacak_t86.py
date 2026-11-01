"""T86. python3 data/analiz/kacak_t86.py"""
import glob,json,re,unicodedata,random,numpy as np,pandas as pd
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
rows=[]
for f in sorted(glob.glob('data/accurace/*.json')):
    m=re.match(r'.*/(\d{4}-\d{2}-\d{2})_([a-z]+)_(\d+)\.json',f);d=json.load(open(f))
    A=[a for a in d.get('atlar',[]) if a.get('sure')]
    if len(A)<5:continue
    ba=d.get('baslik','');pist='Kum' if 'Kum' in ba else 'Çim' if 'Cim' in ba or 'Çim' in ba else 'Sentetik' if 'Sentetik' in ba else '?'
    k=min(A,key=lambda a:a['sure']);rows.append((m.group(1),asc(m.group(2)),int(m.group(3)),k['no'],pist))
K=pd.DataFrame(rows,columns=['tarih','hipodrom','kosu','no','pist']);print('accurace kaçak koşu',len(K),K.pist.value_counts().to_dict(),flush=True)
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str);P['hipodrom']=P.hipodrom.map(asc)
P['pm']=P.p_piyasa/P.groupby(['tarih','hipodrom','kosu']).p_piyasa.transform('sum');P['pj']=P.p_Jason/P.groupby(['tarih','hipodrom','kosu']).p_Jason.transform('sum')
P['kz']=(pd.to_numeric(P.sira,errors='coerce')==1).astype(float)
Q=K.merge(P,on=['tarih','hipodrom','kosu','no'],how='inner').dropna(subset=['pm']);print('eşleşen',len(Q),flush=True)
Q['grup']=np.where(((Q.hipodrom=='izmir')&(Q.pist=='Çim'))|(Q.hipodrom.isin(['bursa','kocaeli','antalya'])&(Q.pist=='Kum')),'iddia','diğer')
random.seed(86)
def rapor(ad,x):
    if len(x)<20:print(ad,'n',len(x),'az');return
    gun=sorted(set(x.tarih));gi={t:x[x.tarih==t] for t in gun};bs=[]
    for _ in range(1000):
        z=pd.concat([gi[random.choice(gun)] for _ in gun]);bs.append((z.kz-z.pm).mean())
    lo,hi=np.percentile(bs,[1.25,98.75]);print(f'{ad:22s} n={len(x):4d} kaçak kazanma {x.kz.mean():.4f} piyasa {x.pm.mean():.4f} fark {(x.kz-x.pm).mean():+.4f} GA97,5 [{lo:+.4f},{hi:+.4f}]',flush=True)
rapor('TÜM',Q)
for g,x in Q.groupby('grup'):rapor('grup '+g,x)
for (h,p),x in Q.groupby(['hipodrom','pist']):
    if len(x)>=20:rapor(f'{h} {p}',x)
for p,x in Q.groupby('pist'):rapor('pist '+p,x)
