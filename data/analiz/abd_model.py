"""ABD modeli (ön kayıt 15 Ekim 2026 01:20). Kullanım: python3 -I abd_model.py [--duman]"""
import sys,glob,numpy as np,pandas as pd
from scipy.optimize import minimize
R='/home/claude/tjk-sistem/';DUMAN='--duman' in sys.argv
d=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/yabanci/*.csv.gz')])
d=d[(d.ulke=='abd')&d.ganyan.notna()&(d.ganyan>0)&~d.kosmadi.fillna(False).astype(bool)&(d.no>0)].copy()
K=['tarih','hipodrom','kosu'];d['p']=1/d.ganyan
g=d.groupby(K).agg(top=('p','sum'),n=('p','size'),kaz=('sira',lambda s:(s==1).sum()))
ok=g[(g.kaz==1)&(g.n>=3)&g.top.between(1.2,1.7)].index
d=d.set_index(K).loc[ok].reset_index().sort_values(K+['no']).reset_index(drop=True)
d['at']=d['at'].astype(str).str.replace(r'\(\d+\)\s*$','',regex=True).str.strip().str.upper()
d['jokey']=d.jokey.astype(str).str.strip().str.upper()
d['pn']=d.p/d.groupby(K).p.transform('sum');d['y']=(d.sira==1).astype(float);d['n']=d.groupby(K).no.transform('size')
d['pct']=(d.sira-1)/(d.n-1);d['res']=d.y-d.pn;d['td']=pd.to_datetime(d.tarih)
pf=glob.glob(R+'data/yabanci_program/*.csv.gz')
if pf:
    P=pd.concat([pd.read_csv(f) for f in pf]).drop_duplicates(K+['no'])[K+['no','antrenor','sahip','yas_ham','st']]
    d=d.merge(P,on=K+['no'],how='left')
else:
    d['antrenor']=np.nan;d['sahip']=np.nan;d['yas_ham']=np.nan;d['st']=np.nan
print('program kapsamı',round(d.antrenor.notna().mean(),3))
d['antrenor']=d.antrenor.fillna('?').astype(str).str.upper().str.strip();d['sahip']=d.sahip.fillna('?').astype(str).str.upper().str.strip()
# --- özellikler: yalnız önceki günler (aynı gün birden çok koşu olsa da gün bazında kaydırılır)
def gecmis(key,cols,pri):
    t=d.groupby([key,'tarih'])[cols].sum().reset_index().sort_values('tarih')
    for c in cols: t['c_'+c]=t.groupby(key)[c].cumsum()-t[c]
    return d[[key,'tarih']].merge(t[[key,'tarih']+['c_'+c for c in cols]],on=[key,'tarih'],how='left')
d['one']=1.0
h=gecmis('at',['y','one','res'],0);d['f_hwin']=(h.c_y.values+24*0.1)/(h.c_one.values+24)-0.1;d['f_ilk']=(h.c_one.values==0)*1.0
d['f_hres']=h.c_res.values/(h.c_one.values+2)
j=gecmis('jokey',['y','one','res'],0);d['f_jwin']=(j.c_y.values+30*0.1)/(j.c_one.values+30)-0.1;d['f_jres']=j.c_res.values/(j.c_one.values+30)
# son 3 bitiş yüzdeliği ve dinlenme: at bazında önceki günler
a=d.groupby(['at','tarih']).agg(pct=('pct','mean'),td=('td','first')).reset_index().sort_values(['at','tarih'])
a['p3']=a.groupby('at').pct.transform(lambda s:s.shift(1).rolling(3,min_periods=1).mean());a['gun']=(a.td-a.groupby('at').td.shift(1)).dt.days
d=d.merge(a[['at','tarih','p3','gun']],on=['at','tarih'],how='left')
d['f_hpct3']=d.p3.fillna(0.5)-0.5;d['f_gun']=np.log1p(d.gun.fillna(60).clip(upper=180))-3.5
t_=gecmis('antrenor',['y','one'],0);d['f_twin']=np.where(d.antrenor=='?',0,(t_.c_y.values+84*0.1)/(t_.c_one.values+84)-0.1)
s_=gecmis('sahip',['y','one'],0);d['f_swin']=np.where(d.sahip=='?',0,(s_.c_y.values+42*0.1)/(s_.c_one.values+42)-0.1)
d['yas']=pd.to_numeric(d.yas_ham.astype(str).str.extract(r'(\d+)')[0],errors='coerce');d['f_yas']=(d.yas-4).fillna(0).clip(-2,4)
d['f_st']=((pd.to_numeric(d.st,errors='coerce')-(d.n+1)/2)/d.n).fillna(0)
d['kilo']=pd.to_numeric(d.kilo,errors='coerce');d['f_kilo']=(d.kilo-d.groupby(K).kilo.transform('mean')).fillna(0)
d['lp']=np.log(d.pn);d['lp2']=d.lp**2
F=['f_hwin','f_ilk','f_hres','f_jwin','f_jres','f_hpct3','f_gun','f_kilo','f_twin','f_swin','f_yas','f_st']
d=d.sort_values(K+['no']).reset_index(drop=True);d['rid']=d.groupby(K).ngroup();d['ay']=d.tarih.str[:7]
def fit(tr,cols,lam):
    X=tr[cols].values;mu=X.mean(0);sd=X.std(0)+1e-9;Z=(X-mu)/sd;Z[:,:2]=X[:,:2] if cols[:2]==['lp','lp2'] else Z[:,:2]
    if cols[:2]==['lp','lp2']: mu[:2]=0;sd[:2]=1
    rid=tr.rid.values;y=tr.y.values;u,inv=np.unique(rid,return_inverse=True)
    def f(w):
        s=Z@w;m=np.full(len(u),-np.inf);np.maximum.at(m,inv,s);e=np.exp(s-m[inv]);S=np.bincount(inv,e);p=e/S[inv]
        pen=lam*np.sum(w[2:]**2)/len(u) if len(w)>2 else 0
        ll=-np.log(p[y==1]).sum()/len(u)+pen
        gr=-(Z[y==1].sum(0)-np.array([np.bincount(inv,p*Z[:,k]).sum() for k in range(Z.shape[1])]))/len(u)
        if len(w)>2: gr[2:]+=2*lam*w[2:]/len(u)
        return ll,gr
    w0=np.zeros(Z.shape[1]);w0[0]=1.0
    w=minimize(f,w0,jac=True,method='L-BFGS-B').x;return w,mu,sd
def skor(te,cols,w,mu,sd):
    Z=(te[cols].values-mu)/sd;s=Z@w;s=pd.Series(s).groupby(te.rid.values).transform(lambda v:v-v.max()).values;e=np.exp(s)
    return e/pd.Series(e).groupby(te.rid.values).transform('sum').values
aylar=sorted(d.ay.unique());out=[]
for i,ay in enumerate(aylar):
    if i<3: continue
    tr=d[d.ay<ay];te=d[d.ay==ay].copy()
    w1,m1,s1=fit(tr,['lp','lp2'],0);te['p1']=skor(te,['lp','lp2'],w1,m1,s1)
    w2,m2,s2=fit(tr,['lp','lp2']+F,100);te['p2']=skor(te,['lp','lp2']+F,w2,m2,s2)
    out.append(te);print(ay,'eğitim',tr.rid.nunique(),'sınama',te.rid.nunique(),flush=True)
if DUMAN: print('duman testi tamam, metrik yazılmadı');sys.exit()
T=pd.concat(out);w=T[T.y==1].copy();w['gun']=w.tarih+w.hipodrom
def boot(x,g,B=3000):
    s=pd.DataFrame({'x':x.values,'g':g.values}).groupby('g').x.agg(['sum','size']);rng=np.random.default_rng(8);o=[]
    for _ in range(B):
        t=s.iloc[rng.integers(0,len(s),len(s))];o.append(t['sum'].sum()/t['size'].sum())
    return np.percentile(o,[2.5,97.5])
for a_,b_,ad in [('p1','pn','M1−M0 (yanlılık)'),('p2','p1','M2−M1 (bilgi)'),('p2','pn','M2−M0')]:
    x=np.log(w[a_])-np.log(w[b_]);lo,hi=boot(x,w.gun);print(f'{ad}: {x.mean():+.4f} nats/koşu GA [{lo:+.4f},{hi:+.4f}]  koşu {len(w)}  aylık pozitif {(x.groupby(w.ay).mean()>0).sum()}/{w.ay.nunique()}')
for c in ('p1','p2'):
    m=T[c]*T.ganyan>1.10;r=T[m].y*T[m].ganyan;print(f'EV>1,10 {c}: bahis {m.sum()} ROI {r.mean():.3f} ± {r.std()/np.sqrt(max(m.sum(),1)):.3f}')
print('M2 ağırlıklar (son fit):',dict(zip(['lp','lp2']+F,np.round(w2,3))))
