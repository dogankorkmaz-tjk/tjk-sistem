"""T86b. python3 data/analiz/kacak_t86b.py"""
import glob,json,re,unicodedata,random,numpy as np,pandas as pd,collections
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
rows=[]
for f in glob.glob('data/video_seyir/20*.json'):
    m=re.match(r'.*/(\d{4}-\d{2}-\d{2})_([a-z]+)_(\d+)\.json',f)
    if not m:continue
    try:d=json.load(open(f))
    except Exception:continue
    oz=d.get('ozet') or {};n=len(oz)
    if n<5 or d.get('gecerli_kare',0)<50:continue
    for no,v in oz.items():
        if v.get('erken') is not None:rows.append((m.group(1),asc(m.group(2)),int(m.group(3)),int(no),(v['erken']-1)/(n-1)))
V=pd.DataFrame(rows,columns=['tarih','hipodrom','kosu','no','er']);print('video at-koşu',len(V),flush=True)
J=pd.read_pickle('/tmp/claude-0/jason_d.pkl');J['tarih']=J.tarih.astype(str);J['hipodrom']=J.hipodrom.map(asc)
import sys;sys.path.insert(0,'data/analiz');import mesafe_pist_ozellik as MP
J=MP.uygula(J,False);J['tarih']=J.tarih.astype(str);J['hipodrom']=J.hipodrom.map(asc) if J.hipodrom.dtype==object else J.hipodrom
J=J[['tarih','hipodrom','kosu','no','at','pist']].drop_duplicates(['tarih','hipodrom','kosu','no'])
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str);P['hipodrom']=P.hipodrom.map(asc)
g=P.groupby(['tarih','hipodrom','kosu']);P['pm']=P.p_piyasa/g.p_piyasa.transform('sum');P['pj']=P.p_Jason/g.p_Jason.transform('sum');P['kz']=(pd.to_numeric(P.sira,errors='coerce')==1).astype(float)
A=P.merge(J,on=['tarih','hipodrom','kosu','no'],how='left').merge(V,on=['tarih','hipodrom','kosu','no'],how='left')
A=A.dropna(subset=['at']).sort_values(['tarih','hipodrom','kosu','no']).reset_index(drop=True)
# büzmeli önceki stil
hist=collections.defaultdict(list);bz=np.full(len(A),np.nan);nk=np.zeros(len(A));cur=None;pend=[]
for i,(t,at,er) in enumerate(zip(A.tarih.values,A['at'].values,A.er.values)):
    if t!=cur:
        for a_,e_ in pend:hist[a_].append(e_)
        pend=[];cur=t
    h=hist.get(at,[]);nk[i]=len(h)
    if len(h)>=2:bz[i]=(sum(h[-5:])+0.5*2)/(len(h[-5:])+2)
    if er==er:pend.append((at,er))
A['bz']=bz;A['nk']=nk
R=[]
for k,x in A.groupby(['tarih','hipodrom','kosu']):
    y=x.dropna(subset=['bz'])
    if len(y)<3 or len(y)<0.6*len(x):continue
    a=y.loc[y.bz.idxmin()];b=y.loc[y.bz.idxmax()]
    R.append((k[0],k[1],a.pist,'kacak',a.kz,a.pm,a.pj,a.bz));R.append((k[0],k[1],a.pist,'bekleyen',b.kz,b.pm,b.pj,b.bz))
R=pd.DataFrame(R,columns=['tarih','hipodrom','pist','tip','kz','pm','pj','bz']);print('koşu',len(R)//2,flush=True)
R['grup']=np.where(((R.hipodrom=='izmir')&(R.pist=='Çim'))|(R.hipodrom.isin(['bursa','kocaeli'])&(R.pist=='Kum')),'C1',np.where(R.pist=='Sentetik','C2','diger'))
random.seed(861)
def rapor(ad,x):
    if len(x)<25:print(f'{ad:34s} n={len(x)} az');return
    gun=sorted(set(x.tarih));gi={t:x[x.tarih==t] for t in gun};out=[]
    for col in('pm','pj'):
        bs=[]
        for _ in range(800):
            z=pd.concat([gi[random.choice(gun)] for _ in gun]);bs.append((z.kz-z[col]).mean())
        lo,hi=np.percentile(bs,[1.25,98.75]);out.append(f'{col}: {(x.kz-x[col]).mean():+.4f} [{lo:+.4f},{hi:+.4f}]')
    print(f'{ad:34s} n={len(x):4d} kazanma {x.kz.mean():.4f} | '+' | '.join(out),flush=True)
for tip in('kacak','bekleyen'):
    x=R[R.tip==tip];rapor(tip+' TÜM',x)
    for gr in('C1','C2','diger'):rapor(f'{tip} {gr}',x[x.grup==gr])
    for (h,p),y in x.groupby(['hipodrom','pist']):
        if len(y)>=25:rapor(f'{tip} {h} {p}',y)
