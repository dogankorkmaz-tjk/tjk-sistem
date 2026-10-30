"""T59: bayraklı süpriz atların ilk5 oranı. python3 data/analiz/supriz_ilk5_t59.py"""
import re,sys
src=open('data/analiz/supriz_say_t56.py').read()
cut=src.index('rF1=None')
exec(src[:cut])
m,zb1,zm1=kos(A,T1,FN);pb1=1/(1+np.exp(-zb1));pm1=1/(1+np.exp(-zm1));esik=np.quantile(pm1/pb1,0.95)
m,zb,zm=kos(A2,T2,FN);pb=1/(1+np.exp(-zb));pm=1/(1+np.exp(-zm))
T=T2.copy();T['r']=pm/pb;T['bay']=T.r>=esik
T['i5']=(T.sira<=5).astype(float);T['i3']=(T.sira<=3).astype(float)
T['dil']=pd.qcut(T.ganyan,5,labels=False,duplicates='drop')
print(f"esik {esik:.3f}, T2 {len(T)} at, bayrakli {int(T.bay.sum())}")
b=T[T.bay];nb=T[~T.bay]
print(f"bayrakli: kazanma {b.kazandi.mean()*100:.2f}% ilk3 {b.i3.mean()*100:.1f}% ilk5 {b.i5.mean()*100:.1f}%")
w=nb.groupby('dil').i5.mean();bek=b.dil.map(w)
ex=(b.i5-bek).values
ug=b.tarih.unique();gi={t:np.where(b.tarih.values==t)[0] for t in ug}
bs=[ex[np.concatenate([gi[t] for t in np.random.choice(ug,len(ug))])].mean()*100 for _ in range(1000)]
print(f"ilk5 beklenen (bayraksiz esles.) {bek.mean()*100:.1f}% fark {ex.mean()*100:+.2f}pp [{np.percentile(bs,2.5):+.2f},{np.percentile(bs,97.5):+.2f}] n={len(b)}")
