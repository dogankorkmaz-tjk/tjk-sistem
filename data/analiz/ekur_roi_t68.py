"""T68: ekür kenarı sıralı ikili havuz ROI. python3 data/analiz/ekur_roi_t68.py"""
import json,math,os
import numpy as np,pandas as pd
TH=3.7
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str)
E=pd.read_pickle('/tmp/claude-0/ekur.pkl');E['tarih']=E.tarih.astype(str)
D=P.merge(E,on=['tarih','hipodrom','kosu','no'],how='left');D['ekur']=D.ekur.fillna(0).astype(int);D=D[D.sira.notna()&D.p_Jason.notna()]
def bol(hv,a,b):
    G={}
    for key in ('si','ik'):
        for x,y,g in (hv.get(key) or []):
            try: G[(key,x,y)]=float(g)
            except: pass
    pt={u for (k,x,y) in G for u in (x,y) if u not in (a,b)};ia=ib=0.0;n=0
    for p in pt:
        for key in ('si','ik'):
            for ka,kb in (((p,a),(p,b)),((a,p),(b,p))):
                ga=G.get((key,)+ka);gb=G.get((key,)+kb)
                if ga and gb: ia+=1/ga;ib+=1/gb;n+=1
    if n==0 or ia<=0 or ib<=0: return None
    r=ia/ib;return r/(1+r)
lg=lambda s:math.log(min(max(s,1e-4),1-1e-4)/(1-min(max(s,1e-4),1-1e-4)));sg=lambda x:1/(1+math.exp(-x))
cache={};rec={v:{t:[0,0.0,0] for t in (1.0,1.15,1.3)} for v in ('taban','teta','ikisi')};per={}
for (t,hp,ks),g in D.groupby(['tarih','hipodrom','kosu']):
    pairs=[tuple(h.no.astype(int)) for e,h in g[g.ekur>0].groupby('ekur') if len(h)==2]
    if not pairs or len(g)<6: continue
    if t not in cache:
        f=f'data/muh_gecmis/{t}.json';cache[t]=json.load(open(f)) if os.path.exists(f) else {}
    hv=None
    for key in (f'{hp.upper()}-{ks}',f'{hp}-{ks}'):
        if key in cache[t]: hv=cache[t][key];break
    if not hv or not hv.get('si'): continue
    g=g.set_index(g.no.astype(int));p0=(g.p_Jason/g.p_Jason.sum()).to_dict();sira=g.sira.to_dict()
    pv={'taban':dict(p0),'teta':dict(p0),'ikisi':dict(p0)};eh=set()
    for a,b in pairs:
        eh|={a,b};Pp=p0[a]+p0[b];s0=p0[a]/Pp;st=sg(TH*lg(s0));sa=bol(hv,str(a),str(b))
        pv['teta'][a]=Pp*st;pv['teta'][b]=Pp*(1-st)
        sb=st if sa is None else sg(0.5*lg(sa)+0.5*lg(st));pv['ikisi'][a]=Pp*sb;pv['ikisi'][b]=Pp*(1-sb)
    grp={a:i for i,pr in enumerate(pairs) for a in pr}
    for x,y,gs in hv['si']:
        try: x=int(x);y=int(y);G=float(gs)
        except: continue
        if x not in p0 or y not in p0: continue
        nx=int(x in eh)+int(y in eh)
        if nx!=1 and not (nx==2 and grp.get(x)!=grp.get(y)): continue
        if nx==0: continue
        hit=1.0 if (sira[x]==1 and sira[y]==2) else 0.0
        for v in pv:
            q=pv[v][x]*pv[v][y]/(1-pv[v][x])
            for th in rec[v]:
                if q*G>th:
                    rec[v][th][0]+=1;rec[v][th][1]+=hit*G;rec[v][th][2]+=hit
                    d=per.setdefault((v,th),{}).setdefault(t,[0,0.0]);d[0]+=1;d[1]+=hit*G
print('veri: günler',len(cache))
for th in (1.0,1.15,1.3):
    for v in rec:
        n,pay,h=rec[v][th];print(f'eşik {th} {v}: bahis {n} isabet {h} ROI {pay/n if n else float("nan"):.3f}')
rng=np.random.default_rng(1)
def roi_ci(v,th,v0=None):
    days=sorted(set(per.get((v,th),{}))|set(per.get((v0,th),{}) if v0 else {}));
    a=np.array([per.get((v,th),{}).get(d,[0,0.0]) for d in days]);b=np.array([per.get((v0,th),{}).get(d,[0,0.0]) for d in days]) if v0 else None
    bs=[]
    for _ in range(5000):
        s=rng.integers(0,len(days),len(days));na,pa=a[s].sum(0)
        if v0 is None: bs.append(pa/na if na else np.nan)
        else:
            nb,pb=b[s].sum(0);bs.append((pa/na if na else np.nan)-(pb/nb if nb else np.nan))
    return np.nanpercentile(bs,[2.5,97.5])
for th in (1.15,1.0,1.3):
    print('eşik',th,'İKİSİ ROI GA',roi_ci('ikisi',th),'İKİSİ−TABAN GA',roi_ci('ikisi',th,'taban'),'TETA−TABAN GA',roi_ci('teta',th,'taban'))
