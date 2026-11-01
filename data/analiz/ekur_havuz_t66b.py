"""T66b: ekür bölüşümü havuzdan, uzun geçmiş. python3 data/analiz/ekur_havuz_t66b.py"""
import json,glob,math,os
import numpy as np,pandas as pd
GAM=np.array([1,0.80,0.67,0.59,0.52]);TH=3.7
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str)
E=pd.read_pickle('/tmp/claude-0/ekur.pkl');E['tarih']=E.tarih.astype(str)
D=P.merge(E,on=['tarih','hipodrom','kosu','no'],how='left');D['ekur']=D.ekur.fillna(0).astype(int);D=D[D.sira.notna()&D.p_Jason.notna()]
def bol(h,a,b):
    G={}
    for key in ('si','ik'):
        for x,y,g in (h.get(key) or []):
            try: G[(key,x,y)]=float(g)
            except: pass
    pt=set(u for (k,x,y) in G for u in (x,y) if u not in (a,b));ia=ib=0.0;n=0
    for p in pt:
        for key in ('si','ik'):
            for ka,kb in (((p,a),(p,b)),((a,p),(b,p))):
                ga=G.get((key,)+ka);gb=G.get((key,)+kb)
                if ga and gb: ia+=1/ga;ib+=1/gb;n+=1
    if n==0 or ia<=0 or ib<=0: return None
    r=ia/ib;return r/(1+r)
def lg(s): s=min(max(s,1e-4),1-1e-4);return math.log(s/(1-s))
def sg(x): return 1/(1+math.exp(-x))
def pl(p,sr):
    o=np.argsort(sr)[:5];m=np.ones(len(p),bool);t=0.0
    for k,i in enumerate(o):
        t+=GAM[k]*math.log(max(p[i]/p[m].sum(),1e-12));m[i]=False
    return t
cache={};rows=[];npair=nv=0
for (t,hp,ks),g in D.groupby(['tarih','hipodrom','kosu']):
    if len(g)<6 or not all((g.sira==j).sum()==1 for j in range(1,6)): continue
    g=g.reset_index(drop=True);pairs=[(h.index[0],h.index[1]) for e,h in g[g.ekur>0].groupby('ekur') if len(h)==2]
    if not pairs: continue
    if t not in cache:
        f=f'data/muh_gecmis/{t}.json';cache[t]=json.load(open(f)) if os.path.exists(f) else {}
    M=cache[t];hv=None
    for key in (f'{hp.upper()}-{ks}',f'{hp}-{ks}'):
        if key in M: hv=M[key];break
    sr=g.sira.values.astype(float);p0=g.p_Jason.values/g.p_Jason.sum()
    pv={'taban':p0.copy(),'havuz':p0.copy(),'teta':p0.copy(),'ikisi':p0.copy()};any_v=False
    for i,j in pairs:
        npair+=1;Pp=p0[i]+p0[j];s0=p0[i]/Pp
        sa=bol(hv,str(int(g.no[i])),str(int(g.no[j]))) if hv else None
        st=sg(TH*lg(s0));pv['teta'][i]=Pp*st;pv['teta'][j]=Pp*(1-st)
        if sa is not None:
            nv+=1;any_v=True
            pv['havuz'][i]=Pp*sa;pv['havuz'][j]=Pp*(1-sa)
            sb=sg(0.5*lg(sa)+0.5*lg(st));pv['ikisi'][i]=Pp*sb;pv['ikisi'][j]=Pp*(1-sb)
        else:
            pv['ikisi'][i]=Pp*st;pv['ikisi'][j]=Pp*(1-st)
    r=dict(t=t,hv=any_v)
    for v,p in pv.items(): r[v]=pl(p,sr);r[v+'_w']=math.log(p[int(np.argmin(sr))])
    rows.append(r)
R=pd.DataFrame(rows);print('ekür koşu',len(R),'çift',npair,'havuz bölüşümü çıkan çift',nv,'havuzlu koşu',int(R.hv.sum()))
rng=np.random.default_rng(1)
def ga(d,days):
    gm=d.groupby(days).agg(['sum','count']);bs=[]
    for _ in range(5000):
        s=rng.choice(len(gm),len(gm));bs.append(gm['sum'].values[s].sum()/gm['count'].values[s].sum())
    return np.percentile(bs,[2.5,97.5])
for nm,S in (('TÜM',R),('HAVUZLU',R[R.hv])):
    for a,b in (('havuz','taban'),('teta','taban'),('ikisi','teta')):
        for ol,suf in (('ilk5',''),('kazanan','_w')):
            d=S[a+suf]-S[b+suf];lo,hi=ga(d,S.t)
            print(nm,f'{a}−{b}',ol,'%.4f'%d.mean(),'GA [%.4f,%.4f]'%(lo,hi),'n',len(d))
