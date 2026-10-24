"""İlk-5 ön-kayıtlı test, tüm hipodromlar. Kullanım: python3 -I ilk5_ltr_tum.py <oos_p.pkl>"""
import sys,numpy as np,pandas as pd
from scipy.optimize import minimize
P=pd.read_pickle(sys.argv[1]);P['tarih']=P.tarih.astype(str)
P=P.dropna(subset=['sira','p_Jason','p_piyasa']);P=P[(P.p_Jason>0)&(P.p_piyasa>0)]
races=[]
for (t,h,k),g in P.groupby(['tarih','hipodrom','kosu']):
    g=g.sort_values('sira')
    if len(g)<6 or g.sira.iloc[:6].nunique()<6 or g.sira.iloc[0]!=1: continue
    races.append((t,h,np.vstack([np.log(g.p_Jason/g.p_Jason.sum()).values,np.log(g.p_piyasa/g.p_piyasa.sum()).values])))
races.sort(key=lambda r:r[0]);days=sorted({r[0] for r in races});cut=days[int(len(days)*0.6)]
fit=[r for r in races if r[0]<cut];test=[r for r in races if r[0]>=cut]
print('koşu',len(races),'fit',len(fit),'test',len(test),'kesim',cut)
def nll(R_,th):
    o=np.zeros((len(R_),5))
    for i,(t,h,X) in enumerate(R_):
        for s in range(5):
            sc=(th[s][:,None]*X).sum(0)[s:];sc=sc-sc.max();o[i,s]=-(sc[0]-np.log(np.exp(sc).sum()))
    return o
def fm(free):
    nf=sum(free);v0=np.tile([1.0 if j==0 else 0.0 for j in range(2) if free[j]],5)
    def th(v):
        T=np.zeros((5,2))
        for s in range(5):T[s,[j for j in range(2) if free[j]]]=v[s*nf:(s+1)*nf]
        return T
    v=minimize(lambda v:nll(fit,th(v)).sum()+0.5*np.sum((v-v0)**2),v0,method='L-BFGS-B').x;return th(v)
C=fm([1,0]);D=fm([1,1]);print('C\n',np.round(C,3),'\nD\n',np.round(D,3))
d=(nll(test,C)-nll(test,D))[:,1:].sum(1);gun=np.array([r[0] for r in test]);hip=np.array([r[1] for r in test])
rng=np.random.default_rng(11)
def ci(x,g):
    s=pd.DataFrame({'g':g,'x':x}).groupby('g').x.agg(['sum','size']);o=[]
    for _ in range(3000):
        t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(o,[2.5,97.5])
lo,hi=ci(d,gun);print(f'\nTOPLAM D−C (2.–5.): {d.mean():+.4f} [{lo:+.4f},{hi:+.4f}] koşu {len(d)}')
print('\nHipodrom bazı (betimleyici):')
for h in pd.Series(hip).value_counts().index:
    m=hip==h
    if m.sum()<40:continue
    a,b=ci(d[m],gun[m]);print(f'{h:12s} n={m.sum():4d} {d[m].mean():+.4f} [{a:+.4f},{b:+.4f}]')
# isabet ölçüsü: modelin 2.-5. sıra için en olası atı gerçek mi (stage-wise top1 isabet)
def hit(R_,th):
    h=np.zeros((len(R_),4))
    for i,(t,hh,X) in enumerate(R_):
        for s in range(1,5):
            sc=(th[s][:,None]*X).sum(0)[s:];h[i,s-1]=float(np.argmax(sc)==0)
    return h
hc,hd=hit(test,C),hit(test,D);print('\nSıra bazlı en-olası-at isabeti 2,3,4,5  C:',np.round(hc.mean(0),3),' D:',np.round(hd.mean(0),3))
np.save('/tmp/ilk5_D.npy',D)
