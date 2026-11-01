"""T65: AGF ekür payı düzeltmesi (EŞİT) vs HAM. python3 data/analiz/ekur_agf_t65.py"""
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
rows=[];desc=[]
for f in sorted(glob.glob('docs/data/gun/2026-1*.json')):
    g=json.load(open(f));t=g['tarih']
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
            grp={e:l for e,l in grp.items() if len(l)>=2}
            if not grp: continue
            agf=np.array([a['agf'] for a in at],float);fix=agf.copy()
            for l in grp.values():
                fix[l]=agf[l].sum()/len(l)
                if len(l)==2: desc.append((agf[l].min()/max(agf[l].max(),1e-9),sr[l][np.argmin(agf[l])]<sr[l][np.argmax(agf[l])]))
            r=dict(t=t,n=len(at))
            for ad,(w0,key,cf) in {'B':(g.get('w0',1.0),'z',0),'G':(g.get('w0_g1'),'z6',0)}.items():
                if w0 is None or any(a.get(key) is None for a in at): continue
                for v,x in (('ham',agf),('esit',fix)):
                    pp=x/x.sum();p=sm([w0*math.log(max(q,1e-6))+(a[key] or 0) for q,a in zip(pp,at)])
                    r[ad+'_'+v]=plll(p,sr);r[ad+'_w_'+v]=math.log(p[int(np.argmin(sr))])
            rows.append(r)
D=pd.DataFrame(rows);print('ekür koşu',len(D),D.t.min(),D.t.max())
print('çift: AGF oranı medyan',np.median([a for a,_ in desc]),'düşük-AGF üyenin önde bitirme oranı',np.mean([b for _,b in desc]),'n',len(desc))
rng=np.random.default_rng(1);days=D.t.unique()
for ad in 'BG':
    if ad+'_ham' not in D: continue
    for nm,suf in (('ilk5',''),('kazanan','_w')):
        d=D[f'{ad}{suf if suf=="" else suf}_esit'.replace('_esit','_esit') if False else ad+suf+'_esit']-D[ad+suf+'_ham']
        d=d.dropna();dd=D.loc[d.index,'t']
        gm=d.groupby(dd).agg(['sum','count']);bs=[]
        for _ in range(5000):
            sel=rng.choice(len(gm),len(gm));bs.append(gm['sum'].values[sel].sum()/gm['count'].values[sel].sum())
        print(ad,nm,'fark(EŞİT−HAM) nats/koşu %.4f'%d.mean(),'GA [%.4f,%.4f]'%tuple(np.percentile(bs,[2.5,97.5])),'n',len(d))
