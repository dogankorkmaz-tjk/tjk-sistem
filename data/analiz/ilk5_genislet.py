"""İlk-5 genişletme testleri T1-T4,T6 (ön-kayıt: hipotez_defteri.md 25 Ekim 2026 02:40). python3 -I ilk5_genislet.py <oos_p.pkl>"""
import sys,glob,os,numpy as np,pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))+'/'
P=pd.read_pickle(sys.argv[1]);P['tarih']=P.tarih.astype(str)
P=P.dropna(subset=['sira','p_Jason','p_piyasa']);P=P[(P.p_Jason>0)&(P.p_piyasa>0)]
T=pd.concat([pd.read_csv(f,usecols=['tarih','hipodrom','kosu','no','at','jokey','apranti','kilo']) for f in glob.glob(R+'data/temiz/*.csv.gz')]);T['tarih']=T.tarih.astype(str)
P=P.merge(T.drop_duplicates(['tarih','hipodrom','kosu','no']),on=['tarih','hipodrom','kosu','no'],how='left')
# dinlenme
H=T[['at','tarih']].drop_duplicates().sort_values(['at','tarih']);H['onc']=H.groupby('at').tarih.shift()
H['gun']=(pd.to_datetime(H.tarih)-pd.to_datetime(H.onc)).dt.days;P=P.merge(H[['at','tarih','gun']],on=['at','tarih'],how='left')
P['ilk']=P.gun.isna().astype(float);P['lrest']=np.log1p(P.gun.clip(7,150).fillna(30))
# idman (galop)
G=pd.concat([pd.read_csv(f,usecols=['it','at','p400']) for f in glob.glob(R+'data/galop/*.csv.gz')]);G['it']=pd.to_datetime(G.it)
Gd=G.dropna(subset=['at']).sort_values('it');P['td']=pd.to_datetime(P.tarih)
idm=[];p4=[]
gg={a:x for a,x in Gd.groupby('at')}
for a,t in zip(P['at'].values,P.td.values):
    x=gg.get(a);
    if x is None: idm.append(0);p4.append(np.nan);continue
    m=x[(x.it<t)&(x.it>=t-np.timedelta64(21,'D'))];idm.append(len(m));p4.append(m.p400.dropna().iloc[-1] if m.p400.notna().any() else np.nan)
P['idm']=np.log1p(idm);P['p400']=p4
hips=P.hipodrom.value_counts().index[:10].tolist()
def build(P_,cols):
    R_=[]
    for (t,h,k),g in P_.groupby(['tarih','hipodrom','kosu']):
        g=g.sort_values('sira')
        if len(g)<6 or g.sira.iloc[:6].nunique()<6 or g.sira.iloc[0]!=1: continue
        lj=np.log(g.p_Jason/g.p_Jason.sum()).values;lm=np.log(g.p_piyasa/g.p_piyasa.sum()).values;n=len(g)
        F={'lj':lj,'lm':lm,'n':lj*(n-10)/3.0,'rest':g.lrest.values,'ilk':g.ilk.values,'idm':g.idm.values}
        p4=g.p400.values.astype(float);F['p4']=np.where(np.isnan(p4),0.0,-(p4-np.nanmean(p4)) if np.isfinite(np.nanmean(p4)) else 0.0)
        F['p4n']=np.isnan(p4).astype(float)
        for hh in hips:F['h_'+hh]=lm*(g.hipodrom.values==hh)
        R_.append((t,h,np.vstack([F[c] for c in cols]),g))
    return R_
def pack(R_):
    N=max(r[2].shape[1] for r in R_);nf=R_[0][2].shape[0];X=np.zeros((len(R_),N,nf));M=np.zeros((len(R_),N),bool)
    for i,r in enumerate(R_):n=r[2].shape[1];X[i,:n]=r[2].T;M[i,:n]=True
    return X,M
def nll_grad(th,X,M):   # th (5,nf); sıra s: kalan = konum>=s
    R_,N,nf=X.shape;tot=np.zeros((R_,5));gr=np.zeros_like(th);pos=np.arange(N)[None,:]
    for s in range(5):
        S=X@th[s];alive=(pos>=s)&M;Sm=np.where(alive,S,-1e30);mx=Sm.max(1,keepdims=True);E=np.where(alive,np.exp(Sm-mx),0);Z=E.sum(1,keepdims=True)
        tot[:,s]=-(S[:,s]-(mx[:,0]+np.log(Z[:,0])));pr=E/Z
        gr[s]=(pr[:,:,None]*X).sum((0,1))-X[:,s,:].sum(0)
    return tot,gr
def fit(X,M,nf,lam=1.0,base_idx=(0,1)):
    v0=np.zeros((5,nf));v0[:,0]=1.0
    f=lambda v:(lambda t,g:(t.sum()+0.5*lam*np.sum((v-v0.ravel())**2),g.ravel()+lam*(v-v0.ravel())))(*nll_grad(v.reshape(5,nf),X,M))
    return minimize(f,v0.ravel(),jac=True,method='L-BFGS-B').x.reshape(5,nf)
rng=np.random.default_rng(21)
def ci(x,g):
    s=pd.DataFrame({'g':g,'x':x}).groupby('g').x.agg(['sum','size']);o=[]
    for _ in range(3000):
        t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(o,[2.5,97.5])
def teste(ad,cols_extra,P_,etiket):
    cols=['lj','lm']+cols_extra;R_=build(P_,cols);R_.sort(key=lambda r:r[0]);days=sorted({r[0] for r in R_});cut=days[int(len(days)*0.6)]
    fi=[r for r in R_ if r[0]<cut];te=[r for r in R_ if r[0]>=cut];Xf,Mf=pack(fi);Xt,Mt=pack(te)
    thB=fit(Xf[:,:,:2],Mf,2);thN=fit(Xf,Mf,len(cols))
    nb=nll_grad(thB,Xt[:,:,:2],Mt)[0][:,1:].sum(1);nn=nll_grad(thN,Xt,Mt)[0][:,1:].sum(1);d=nb-nn;g=np.array([r[0] for r in te]);lo,hi=ci(d,g)
    print(f'{etiket:34s} koşu fit {len(fi)} test {len(te)} | ek kazanç {d.mean():+.4f} [{lo:+.4f},{hi:+.4f}]')
    return thN,te,Xt,Mt
print('--- T1-T4 (taban D\'ye ek kazanç, 2.–5. sıra, nats/koşu) ---')
teste('t1',['n'],P,'T1 alan büyüklüğü')
teste('t2',['h_'+h for h in hips],P,'T2 hipodrom×piyasa')
teste('t3',['rest','ilk'],P,'T3 dinlenme süresi')
P26=P[P.tarih>='2026-01-01']
teste('t4',['idm','p4','p4n'],P26,'T4 idman (2026-01+)')
print('--- T4 kontrol: aynı 2026 koşularında T3 (karşılaştırma için) ---')
teste('t3b',['rest','ilk'],P26,'T3 (yalnız 2026)')
# T6 artık analizi: D (tüm veriyle fit değil; ilk %60 fit) ile test dönemi artığı
R_=build(P,['lj','lm']);R_.sort(key=lambda r:r[0]);days=sorted({r[0] for r in R_});cut=days[int(len(days)*0.6)]
fi=[r for r in R_ if r[0]<cut];te=[r for r in R_ if r[0]>=cut];Xf,Mf=pack(fi);th=fit(Xf,Mf,2)
rows=[]
for t,h,X,g in te:
    s2=th[1]@X;n=X.shape[1];pw=expit(s2[None,:]-s2[:,None]);np.fill_diagonal(pw,0)   # pw[i,j]=P(j önde | i,j)
    er=1+pw.sum(1);gr=g.copy();gr['art']=np.arange(1,n+1)-er;gr['n']=n;rows.append(gr)
Q=pd.concat(rows);Q['gan_d']=pd.cut(Q.ganyan,[0,2.5,5,10,20,1e9]).astype(str);Q['no_d']=pd.cut(Q.no,[0,3,6,9,12,99]).astype(str)
Q['kilo_z']=Q.kilo-Q.groupby(['tarih','hipodrom','kosu']).kilo.transform('mean');Q['kilo_d']=pd.cut(Q.kilo_z,[-99,-2,-0.5,0.5,2,99]).astype(str)
Q['n_d']=pd.cut(Q.n,[0,8,10,12,99]).astype(str);Q['rest_d']=pd.cut(Q.gun.fillna(999),[0,14,28,60,150,999,1e9]).astype(str)
top=Q.jokey.value_counts().index[:15];Q['jok']=np.where(Q.jokey.isin(top),Q.jokey,'diğer')
res=[]
for c in ['hipodrom','n_d','gan_d','no_d','kilo_d','jok','apranti','rest_d']:
    for v,x in Q.groupby(c).art:
        if len(x)<150:continue
        t=x.mean()/(x.std()/np.sqrt(len(x)));res.append((c,str(v),len(x),x.mean(),t))
r=pd.DataFrame(res,columns=['boyut','dilim','n','art_ort','t']);r['p']=2*(1-__import__('scipy.stats',fromlist=['norm']).norm.cdf(np.abs(r.t)));o=np.argsort(r.p.values);m=len(r);q=np.empty(m);q[o]=np.minimum.accumulate((r.p.values[o]*m/np.arange(1,m+1))[::-1])[::-1];r['q']=np.minimum(q,1)
print('\n--- T6 sıra artığı (+ = beklenenden geride bitti), BH q ---\n',len(r),'dilim; q<0,10 olanlar:');print(r[r.q<0.10].sort_values('q').round(4).to_string(index=False) if (r.q<0.10).any() else 'yok')
print('en uç 6 (|t|):');print(r.reindex(r.t.abs().sort_values(ascending=False).index).head(6).round(4).to_string(index=False))
