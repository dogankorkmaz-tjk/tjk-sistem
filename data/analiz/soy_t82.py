"""T82. python3 data/analiz/soy_t82.py"""
import sys,unicodedata,random,numpy as np,pandas as pd
from scipy.optimize import minimize_scalar
sys.path.insert(0,'data/analiz');import soy_pist,soy_mesafe
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
d=pd.read_pickle('/tmp/claude-0/jason_d.pkl');d['tarih']=d.tarih.astype(str)
import mesafe_pist_ozellik as MP
d=MP.uygula(d,False);d['tarih']=d.tarih.astype(str)
d=soy_pist.ekle(d);d=soy_mesafe.ekle(d)
d['mesafe']=pd.to_numeric(d.mesafe,errors='coerce');d=d.sort_values(['at','tarih','kosu']).reset_index(drop=True)
g=d.groupby('at');d['n_once']=g.cumcount();d['m_onc']=g.mesafe.shift(1);d['p_onc']=g.pist.shift(1)
d['A']=d.n_once<3;d['B']=(d.mesafe-d.m_onc)>=200;d['Cc']=d.p_onc.notna()&(d.pist.astype(str)!=d.p_onc.astype(str))
d['hipodrom']=d.hipodrom.map(asc)
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str);P['hipodrom']=P.hipodrom.map(asc)
P=P[P.p_Jason.notna()].merge(d[['tarih','hipodrom','kosu','no','f_spd','f_sd','A','B','Cc']],on=['tarih','hipodrom','kosu','no'],how='left')
P['kz']=(pd.to_numeric(P.sira,errors='coerce')==1)
P['fA']=np.where(P.A.fillna(False),P.f_spd.fillna(0)+P.f_sd.fillna(0),0);P['fB']=np.where(P.B.fillna(False),P.f_sd.fillna(0),0);P['fC']=np.where(P.Cc.fillna(False),P.f_spd.fillna(0),0)
random.seed(82);gun=sorted(set(P.tarih));cut=gun[int(len(gun)*.6)]
R=[]
for (t,h,k),x in P.groupby(['tarih','hipodrom','kosu']):
    if x.kz.sum()!=1:continue
    R.append((t,np.log(x.p_Jason.values/x.p_Jason.sum()),int(np.argmax(x.kz.values)),{c:x[c].values for c in('fA','fB','fC')}))
print('koşu',len(R),'kesim',cut,flush=True)
for ad,c in(('a ilk3 koşu','fA'),('b mesafe artışı','fB'),('c pist değişimi','fC')):
    S=[r for r in R if np.any(r[3][c]!=0)];tr=[r for r in S if r[0]<cut];te=[r for r in S if r[0]>=cut]
    def nll(b,rs):
        o=[]
        for t,lp,w,F in rs:
            s=lp+b*F[c];s=s-s.max();o.append(-(s[w]-np.log(np.exp(s).sum())))
        return np.array(o)
    b=minimize_scalar(lambda b:nll(b,tr).sum()+1.0*b*b,bounds=(-20,20),method='bounded').x
    dd=nll(0.0,te)-nll(b,te);gt=np.array([r[0] for r in te]);ug=sorted(set(gt));gi={t:np.where(gt==t)[0] for t in ug}
    bs=[dd[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(800)]
    lo=np.percentile(bs,1.67)
    print(f'{ad:16s} β={b:+.2f} eğitim {len(tr)} test {len(te)} koşu kazanç {dd.mean():+.4f} [{lo:+.4f},{np.percentile(bs,98.33):+.4f}] ({"SAĞLANDI" if lo>0 else "sağlanmadı"})',flush=True)
