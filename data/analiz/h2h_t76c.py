"""T76c. python3 data/analiz/h2h_t76c.py"""
import sys,json,unicodedata,random,numpy as np,pandas as pd
from scipy.optimize import minimize
sys.path.insert(0,'data/analiz');import h2h_ozellik
asc=lambda s:unicodedata.normalize('NFKD',str(s).replace('İ','I').replace('ı','i')).encode('ascii','ignore').decode().lower().strip()
d=pd.read_pickle('/tmp/claude-0/jason_d.pkl');d['tarih']=d.tarih.astype(str)
d=h2h_ozellik.ekle(d[['tarih','hipodrom','kosu','no','at','sira','rel_sure','derece_sn']].copy())
d['hipodrom']=d.hipodrom.map(asc)
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str);P['hipodrom']=P.hipodrom.map(asc)
P=P[(P.tarih>='2025-01-01')&P.p_Jason.notna()].merge(d[['tarih','hipodrom','kosu','no','f_h2h_s','f_h2h_m']],on=['tarih','hipodrom','kosu','no'],how='left')
P['sr']=pd.to_numeric(P.sira,errors='coerce').fillna(0)
G=np.array([1,.8,.69,.69,.69]);R=[]
for (t,h,k),g in P.groupby(['tarih','hipodrom','kosu']):
    if len(g)<6 or not all((g.sr==j).sum()==1 for j in range(1,6)):continue
    p=g.p_Jason.values/g.p_Jason.sum();o=[int(np.where(g.sr.values==j)[0][0]) for j in range(1,6)]
    R.append((t,np.log(np.maximum(p,1e-9)),g.f_h2h_s.fillna(0).values,g.f_h2h_m.fillna(0).values,o))
gun=sorted({r[0] for r in R});cut=gun[int(len(gun)*.6)];tr=[r for r in R if r[0]<cut];te=[r for r in R if r[0]>=cut]
print('koşu',len(R),'eğitim',len(tr),'test',len(te),'kesim',cut,flush=True)
def nllk(b,rs,pos):  # b: (4,2) pozisyon 2..5
    out=[]
    for t,lp,s,m,o in rs:
        used=[];row=[]
        for k in range(5):
            sc=G[k]*lp+(0 if k==0 else b[k-1,0]*s+b[k-1,1]*m)
            mx=sc.max();e=np.exp(sc-mx);den=e.sum()-sum(e[u] for u in used);row.append(-np.log(e[o[k]]/den));used.append(o[k])
        out.append(row)
    return np.array(out)
def f(x):return nllk(x.reshape(4,2),tr,0)[:,1:].sum()+1.0*np.sum(x**2)
res=minimize(f,np.zeros(8),method='L-BFGS-B');b=res.x.reshape(4,2);print('β (poz2..5; s,m):',np.round(b,3).tolist(),flush=True)
json.dump(b.tolist(),open('data/analiz/h2h_t76c_beta.json','w'))
A=nllk(b,te,0);B0=nllk(np.zeros((4,2)),te,0);dd=(A-B0)[:,1:].sum(1);gt=np.array([r[0] for r in te]);ug=sorted(set(gt));gi={g:np.where(gt==g)[0] for g in ug};random.seed(76)
bs=[dd[np.concatenate([gi[random.choice(ug)] for _ in ug])].mean() for _ in range(1000)]
print(f'test 2–5. sıra NLL farkı/koşu {dd.mean():+.4f} GA95 [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]')
for j in range(1,5):
    x=(A-B0)[:,j];print(' poz',j+1,f'{x.mean():+.4f}')
