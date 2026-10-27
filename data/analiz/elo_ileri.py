"""T27 ileri gölge: Elo'lu G1-S (z6) vs Elo'suz (z6 - ze). Gün dosyaları docs/data/gun/*.json. Çalıştır: python3 data/analiz/elo_ileri.py [başlangıç=2026-10-29]"""
import glob,json,sys,numpy as np
BAS=sys.argv[1] if len(sys.argv)>1 else "2026-10-29"
def pl(s,sira,K=5):
    """ilk K sıra Plackett-Luce log-olabilirliği (sıra: 1..K atların indeksi)."""
    s=np.array(s,float);ll=[];m=np.ones(len(s),bool)
    for k in range(K):
        j=sira[k]; z=np.where(m,s,-1e9);z-=z.max();ll.append(z[j]-np.log(np.exp(z[m]).sum()));m[j]=False
    return np.array(ll)
G=[0,0.7978,0.6745,0.5899,0.5246]
rows=[]
for f in sorted(glob.glob('docs/data/gun/*.json')):
    o=json.load(open(f));t=o['tarih']
    if t<BAS or 'w0_g1' not in o: continue
    for h in o['hipodromlar']:
        for k in h['kosular']:
            at=[a for a in k['atlar'] if not a.get('kosmaz') and a.get('z6') is not None and a.get('ze') is not None and a.get('agf')]
            sn=k.get('sonuc')
            if not sn or len(at)<6: continue
            sr=[(sn.get(str(a['no']),{}) or {}).get('sira') for a in at]
            if any(x is None for x in sr): continue
            order=list(np.argsort(sr));
            if [sr[i] for i in order[:5]]!=[1,2,3,4,5]: continue
            tot=sum(a['agf'] for a in at);lp=np.log(np.array([a['agf']/tot for a in at]))
            sn_=o['w0_g1']*lp+np.array([a['z6'] for a in at]);so=sn_-np.array([a['ze'] for a in at])
            ga=[1.0]+list(o['a_g1'][1:5]) if len(o['a_g1'])>=5 else [1,.8,.67,.59,.52]
            def tl(s): 
                s=np.array(s,float);m=np.ones(len(s),bool);ll=[]
                for kk in range(5):
                    j=order[kk];z=np.where(m,ga[kk]*s,-1e9);z-=z.max();ll.append(z[j]-np.log(np.exp(z[m]).sum()));m[j]=False
                return np.array(ll)
            rows.append((t,tl(sn_)-tl(so)))
print("koşu",len(rows))
if rows:
    D=np.array([r[1] for r in rows]);gun=np.array([r[0] for r in rows]);ug=sorted(set(gun));gi={g:np.where(gun==g)[0] for g in ug};rng=np.random.default_rng(1)
    for name,idx in [("kazanan",[0]),("ikili",[0,1]),("üçlü",[0,1,2]),("ilk4",[0,1,2,3]),("ilk5",[0,1,2,3,4])]:
        x=D[:,idx].sum(1);bs=[x[np.concatenate([gi[ug[i]] for i in rng.integers(0,len(ug),len(ug))])].mean() for _ in range(1000)]
        print(f"{name:8s} {x.mean():+.4f} nats/koşu (Elo − Elo'suz; pozitif = Elo iyi) GA [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]")
