"""Faz 2 (ön kayıt 15 Ekim 2026 00:01): altılı değer kurucusu geriye testi. Kullanım: python3 -I altili_deger.py <scratch>"""
import sys,glob,numpy as np,pandas as pd
R='/home/claude/tjk-sistem/';S=sys.argv[1]
d=pd.read_pickle(S+'/agf_d.pkl');K=['tarih','hipodrom','kosu']
O=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')])
O=O[O.tur.str.startswith("6'LI GANYAN")].drop_duplicates(['tarih','hipodrom','kosu'])
G={k:g for k,g in d.groupby(K)}
def kur(p,a,B,mod):
    n=len(p);S=[[int(np.argmax(p[j] if mod!='A' else a[j]))] for j in range(n)]
    q=[p[j] if mod!='A' else a[j] for j in range(n)]
    while True:
        C=np.prod([len(s) for s in S]);best=None
        for j in range(n):
            m=len(S[j])
            if C*(m+1)/m>B: continue
            P=q[j][S[j]].sum()
            for i in range(len(q[j])):
                if i in S[j]: continue
                if mod=='V' and p[j][i]/a[j][i]<1.0: continue
                sc=np.log((P+q[j][i])/P)/np.log((m+1)/m)
                if best is None or sc>best[0]: best=(sc,j,i)
        if best is None: return S
        S[best[1]].append(best[2])
rows=[]
for r in O.itertuples():
    legs=[G.get((r.tarih,r.hipodrom,k)) for k in range(r.kosu-5,r.kosu+1)]
    if any(g is None for g in legs): continue
    nos=[g.no.values for g in legs];p=[g.p_Jason.values/g.p_Jason.sum() for g in legs];a=[g.a.values for g in legs]
    devir='DEVİR' in r.tur
    win=None if devir else [set(int(x) for x in s.split(',')) for s in str(r.kombo).split('/')]
    if not devir and len(win)!=6: continue
    if not devir:
        aw=np.prod([max(a[j][np.isin(nos[j],list(win[j]))].sum(),1e-4) for j in range(6)])
    for B in (64,256):
        for mod in 'VJA':
            Ss=kur(p,a,B,mod);cost=np.prod([len(s) for s in Ss])
            hit=(not devir) and all(any(nos[j][i] in win[j] for i in Ss[j]) for j in range(6))
            ph=np.prod([p[j][Ss[j]].sum() for j in range(6)])
            evr=np.prod([np.mean(p[j][Ss[j]]/a[j][Ss[j]]) for j in range(6)])
            rows.append((r.tarih,r.hipodrom,r.kosu,B,mod,cost,hit,float(r.tutar) if hit else 0.0,ph,evr,np.nan if devir else float(r.tutar)*aw))
D=pd.DataFrame(rows,columns=['t','h','k','B','mod','cost','hit','pay','ph','evr','k_hat']);D.to_csv(S+'/altili_deger.csv',index=False)
u=D.drop_duplicates(['t','h','k']);print('altılı',len(u),'k̂ medyan (ödeme×Πa)',round(u.k_hat.median(),3),'IQR',np.round(u.k_hat.quantile([.25,.75]).values,3))
def boot(m,c1,c2,B=2000):
    m=m.assign(g=m.t+m.h);s=m.groupby('g')[[f'pay_{c1}',f'cost_{c1}',f'pay_{c2}',f'cost_{c2}']].sum();rng=np.random.default_rng(7);o=[]
    for _ in range(B):
        t=s.iloc[rng.integers(0,len(s),len(s))].sum();o.append(t[f'pay_{c1}']/t[f'cost_{c1}']-t[f'pay_{c2}']/t[f'cost_{c2}'])
    return np.percentile(o,[2.5,97.5])
def rboot(x,B=2000):
    x=x.assign(g=x.t+x.h);s=x.groupby('g')[['pay','cost']].sum();rng=np.random.default_rng(9);o=[]
    for _ in range(B):
        t=s.iloc[rng.integers(0,len(s),len(s))].sum();o.append(t.pay/t.cost)
    return np.percentile(o,[2.5,97.5])
for B in (64,256):
    for per,f in (('tümü',lambda x:x),('2025',lambda x:x[x.t<'2026']),('2026',lambda x:x[x.t>='2026'])):
        x=f(D[D.B==B]);line=f'B={B} {per}: '
        for mod in 'VJA':
            y=x[x['mod']==mod];lo,hi=rboot(y);line+=f"{mod}: tutan {int(y.hit.sum())}/{len(y)} model-bekl %{y.ph.mean()*100:.1f} ROI {y.pay.sum()/y.cost.sum():.2f} [{lo:.2f},{hi:.2f}] ort.EVoranı {y.evr.mean():.2f} | "
        m=x[x['mod']=='V'].merge(x[x['mod']=='J'],on=['t','h','k'],suffixes=('_V','_J')).merge(x[x['mod']=='A'].rename(columns={'pay':'pay_A','cost':'cost_A'})[['t','h','k','pay_A','cost_A']],on=['t','h','k'])
        line+=f"V−J {np.round(boot(m,'V','J'),2)} V−A {np.round(boot(m,'V','A'),2)}";print(line)
