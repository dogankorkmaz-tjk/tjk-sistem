"""T39 sürpriz bulma (keşif). python3 data/analiz/surpriz_analiz.py <scratchpad>"""
import sys,numpy as np,pandas as pd
P=pd.read_pickle(sys.argv[1]+'/oos_p.pkl');P['tarih']=P.tarih.astype(str)
P=P[P.p_Jason.notna()&P.p_piyasa.notna()&P.kazandi.notna()].copy()
P['g']=P.groupby(['tarih','hipodrom','kosu']).ngroup();n=P.groupby('g').no.transform('size');P=P[n>=6]
P['pm']=P.p_piyasa/P.groupby('g').p_piyasa.transform('sum');P['pj']=P.p_Jason/P.groupby('g').p_Jason.transform('sum');P['r']=P.pj/P.pm
print('at',len(P),'koşu',P.g.nunique(),P.tarih.min())
rng=np.random.default_rng(1);gun=P.tarih.values;ug=np.unique(gun);ix={u:np.where(gun==u)[0] for u in ug}
L=P[P.pm<0.08].copy();print('uzun oranlı (piyasa p<0.08) at:',len(L),'kazanma %.2f%% piyasa %.2f%% Jason %.2f%%'%(L.kazandi.mean()*100,L.pm.mean()*100,L.pj.mean()*100))
L['q']=pd.qcut(L.r,5,labels=False)
print('  Jason/piyasa oranı beşlikleri (düşük→yüksek): kazanma | piyasa | Jason | n')
for q,g in L.groupby('q'):print('  %d  %.2f%% | %.2f%% | %.2f%% | %d'%(q,g.kazandi.mean()*100,g.pm.mean()*100,g.pj.mean()*100,len(g)))
for nm,g in [('üst beşlik',L[L.q==4]),('alt beşlik',L[L.q==0])]:
    g=g.reset_index(drop=True);x=g.pm.values;y=g.kazandi.values.astype(float);gg=g.tarih.values
    ugg=np.unique(gg);ii={u:np.where(gg==u)[0] for u in ugg};d=y-x;bs=[d[np.concatenate([ii[ugg[i]] for i in rng.integers(0,len(ugg),len(ugg))])].mean() for _ in range(1000)]
    print('  %s: kazanma−piyasa %+.2f puan [%+.2f,%+.2f]'%(nm,d.mean()*100,np.percentile(bs,2.5)*100,np.percentile(bs,97.5)*100))
W=P[(P.kazandi==1)];S=W[W.p_piyasa>0]
big=W[W.pm<0.067];print('sürpriz kazananlar (piyasa p<%6.1f, ~ganyan≥15): %d koşu (%.1f%% tüm koşular)'%(0.067*100,len(big),len(big)/W.g.nunique()*100))
print('  Jason p / piyasa p ortalaması %.2f ; medyan %.2f ; Jason bunlarda daha yüksek p verdi oranı %.1f%%'%(big.r.mean(),big.r.median(),(big.r>1).mean()*100))
P['rj']=P.groupby('g').pj.rank(ascending=False);P['rm']=P.groupby('g').pm.rank(ascending=False);b=P.loc[big.index]
print('  sürpriz kazananın Jason sırası ort. %.2f, piyasa sırası %.2f (alan ort. ~%.1f at)'%(b.rj.mean(),b.rm.mean(),P.groupby('g').no.transform('size').loc[big.index].mean()))
