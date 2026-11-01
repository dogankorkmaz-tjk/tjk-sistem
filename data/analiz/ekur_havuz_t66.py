"""T66: ekür çift içi bölüşüm sıralı ikili/ikili havuzundan. python3 data/analiz/ekur_havuz_t66.py"""
import json,glob,math,collections
import numpy as np,pandas as pd
GAM=np.array([1,0.80,0.67,0.59,0.52])
E=pd.read_pickle('/tmp/claude-0/ekur.pkl');E['tarih']=E.tarih.astype(str)
EK={(r.tarih,r.hipodrom,int(r.kosu),int(r.no)):int(r.ekur) for r in E.itertuples() if r.ekur>0}
def sm(s):
    s=np.array(s,float);e=np.exp(s-s.max());return e/e.sum()
def plll(p,sr):
    o=np.argsort(sr)[:5];m=np.ones(len(p),bool);t=0.0
    for k,i in enumerate(o):
        t+=GAM[k]*math.log(max(p[i]/p[m].sum(),1e-12));m[i]=False
    return t
def bol(h,a,b):
    """a,b ekür çifti (str no); havuz kombinasyonlarından s_a ya da None"""
    ia=ib=0.0;n=0
    G={}
    for key in ('si','ik'):
        for x,y,g in (h.get(key) or []):
            try: G[(key,x,y)]=float(g)
            except: pass
    partners=set()
    for (key,x,y) in G:
        for u in (x,y):
            if u not in (a,b): partners.add(u)
    for p in partners:
        for key,pairs in (('si',[((p,a),(p,b)),((a,p),(b,p))]),('ik',[((p,a),(p,b)),((a,p),(b,p))])):
            for ka,kb in pairs:
                ga=G.get((key,)+ka); gb=G.get((key,)+kb)
                if ga and gb: ia+=1/ga; ib+=1/gb; n+=1
    if n==0 or ia<=0 or ib<=0: return None
    r=ia/ib;return r/(1+r)
muh={}
for f in glob.glob('data/muh/2026-1*.json'): muh[f[-15:-5]]=json.load(open(f))
rows=[];nv=0;nt=0;desc=[]
for f in sorted(glob.glob('docs/data/gun/2026-1*.json')):
    g=json.load(open(f));t=g['tarih'];M=muh.get(t,{})
    for h in g['hipodromlar']:
        for k in h['kosular']:
            s=k.get('sonuc')
            if not s: continue
            at=[a for a in k['atlar'] if a.get('agf') and not a.get('kosmaz') and str(a['no']) in s and s[str(a['no'])].get('sira')]
            if len(at)<6: continue
            sr=np.array([s[str(a['no'])]['sira'] for a in at],float)
            if not all((sr==j).sum()==1 for j in range(1,6)): continue
            ek=[a.get('ek') or EK.get((t,h['id'],k['kosu'],a['no'])) or 0 for a in at]
            grp=collections.defaultdict(list)
            for i,e in enumerate(ek):
                if e: grp[e].append(i)
            grp={e:l for e,l in grp.items() if len(l)==2}
            if not grp: continue
            hv=(M.get(h['id'].upper()+'-'+str(k['kosu'])) or {}).get('havuz') or {}
            agf=np.array([a['agf'] for a in at],float);ham=agf.copy();hav=agf.copy();esit=agf.copy()
            for l in grp.values():
                S=agf[l].sum();esit[l]=S/2;nt+=1
                sa=bol(hv,str(at[l[0]]['no']),str(at[l[1]]['no'])) if hv else None
                if sa is not None:
                    nv+=1;hav[l[0]]=S*sa;hav[l[1]]=S*(1-sa)
                    desc.append((sa,agf[l[0]]/S,float(sr[l[0]]<sr[l[1]])))
            r=dict(t=t)
            for ad,(w0,key) in {'B':(g.get('w0',1.0),'z'),'G':(g.get('w0_g1'),'z6')}.items():
                if w0 is None or any(a.get(key) is None for a in at): continue
                for v,x in (('ham',ham),('esit',esit),('hav',hav)):
                    pp=x/x.sum();p=sm([w0*math.log(max(q,1e-6))+(a[key] or 0) for q,a in zip(pp,at)])
                    r[ad+'_'+v]=plll(p,sr);r[ad+'_w_'+v]=math.log(p[int(np.argmin(sr))])
            rows.append(r)
D=pd.DataFrame(rows);print('ekür koşu',len(D),D.t.min(),D.t.max(),'çift',nt,'havuzdan bölüşüm çıkan çift',nv)
if desc:
    a=np.array(desc);print('betimleyici: havuz payı s_a vs sonuç: s_a>0.5 olan üyenin önde bitirme oranı %.3f (n=%d); AGF payı>0.5 olan üye %.3f'%(np.mean(np.where(a[:,0]>0.5,a[:,2],1-a[:,2])),len(a),np.mean(np.where(a[:,1]>0.5,a[:,2],1-a[:,2]))))
rng=np.random.default_rng(1)
for ad in 'BG':
    if ad+'_ham' not in D: continue
    for var in ('hav','esit'):
        for nm,suf in (('ilk5',''),('kazanan','_w')):
            d=(D[ad+suf+'_'+var]-D[ad+suf+'_ham']).dropna();dd=D.loc[d.index,'t']
            gm=d.groupby(dd).agg(['sum','count']);bs=[]
            for _ in range(5000):
                sel=rng.choice(len(gm),len(gm));bs.append(gm['sum'].values[sel].sum()/gm['count'].values[sel].sum())
            print(ad,var.upper(),nm,'fark(−HAM) %.4f'%d.mean(),'GA [%.4f,%.4f]'%tuple(np.percentile(bs,[2.5,97.5])),'n',len(d))
