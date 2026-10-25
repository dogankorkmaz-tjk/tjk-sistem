"""T23 kupon bütçe eğrisi. python3 -I butce_t23.py <oos_p.pkl> <cikti.csv> [maks_koşu]"""
import sys,glob,numpy as np,pandas as pd,math
from multiprocessing import Pool
R='/home/claude/tjk-sistem/'
CEXP=[0.977,0.767,0.666,0.575,0.513];ESIK=[12,24,48,96,150,250,400]
TUR={'ÜÇLÜ BAHİS':3,'TABELA BAHİS':4,'SIRALI 5 Lİ BAHİS':5}
P=pd.read_pickle(sys.argv[1]);P['tarih']=P.tarih.astype(str)
G={k:g for k,g in P.groupby(['tarih','hipodrom','kosu'])}
def prob_say(W,T,sets):
    L=len(sets);top=0.0;cnt=0;kul=[]
    def rec(k,pr):
        nonlocal top,cnt
        if k==L: top+=pr;cnt+=1;return
        for h in sets[k]:
            if h in kul: continue
            den=T[k]-sum(W[k][u] for u in kul)
            if den<=1e-12: continue
            kul.append(h);rec(k+1,pr*W[k][h]/den);kul.pop()
    rec(0,1.0);return top,cnt
def yol(p,L):
    """tek açgözlü yol; her eşikte anlık görüntü (sets,pr,n)"""
    p=np.maximum(np.asarray(p,float),1e-9);p=p/p.sum();n=len(p)
    W=[list(p**CEXP[k]) for k in range(L)];T=[sum(w) for w in W]
    ord_=list(np.argsort(-p));aday=ord_[:min(n,9)]
    sets=[[ord_[k]] for k in range(L)];cur,nv=prob_say(W,T,sets);snap={}
    ei=0
    while True:
        while ei<len(ESIK) and nv>ESIK[ei]: ei+=1
        # anlık görüntü: eşiği aşmayan son hal
        best=None;bg=0
        for k in range(L):
            for h in aday:
                if h in sets[k]: continue
                sets[k].append(h);pr,v2=prob_say(W,T,sets);sets[k].pop()
                if v2>ESIK[-1] or v2<=nv: continue
                g=math.log(pr/cur)/math.log(v2/nv)
                if g>bg: bg=g;best=(k,h,pr,v2)
        for e in ESIK:
            if nv<=e and e not in snap: pass
        if best is None: break
        # eşik geçilecekse önceki hali kaydet
        for e in ESIK:
            if nv<=e<best[3] and e not in snap: snap[e]=([s[:] for s in sets],cur,nv)
        sets[best[0]].append(best[1]);cur=best[2];nv=best[3]
    for e in ESIK:
        if e not in snap and nv<=e: snap[e]=([s[:] for s in sets],cur,nv)
    return snap
def is_(args):
    t,h,k,tur,kombo,tutar=args;L=TUR[tur]
    g=G.get((str(t),h,k))
    if g is None or len(g)<L+1: return []
    g=g.sort_values('no');nos=g.no.tolist()
    win=[set(int(x) for x in s.split(',')) for s in str(kombo).split('/')]
    if len(win)<L: return []
    out=[]
    for kaynak,col in (('model','p_Jason'),('piyasa','p_piyasa')):
        sn=yol(g[col].values,L)
        for e,(sets,pr,nv) in sn.items():
            hit=all(any(nos[i] in win[j] for i in sets[j]) for j in range(L))
            out.append((str(t),h,k,tur,kaynak,e,nv,pr,hit,float(tutar) if hit else 0.0))
    return out
if __name__=='__main__':
    O=pd.concat([pd.read_csv(f) for f in glob.glob(R+'data/odeme/*.csv.gz')])
    O=O[O.tur.isin(TUR)&(O.tarih.astype(str)>='2025-10-19')].drop_duplicates(['tarih','hipodrom','kosu','tur'])
    if len(sys.argv)>3: O=O.sample(int(sys.argv[3]),random_state=1)
    jobs=[(r.tarih,r.hipodrom,r.kosu,r.tur,r.kombo,r.tutar) for r in O.itertuples()]
    print('iş',len(jobs),flush=True)
    with Pool(2) as pl: res=[x for sub in pl.imap_unordered(is_,jobs,chunksize=8) for x in sub]
    d=pd.DataFrame(res,columns=['t','h','k','tur','kaynak','esik','n','pr','hit','pay']);d.to_csv(sys.argv[2],index=False);print('satır',len(d))
