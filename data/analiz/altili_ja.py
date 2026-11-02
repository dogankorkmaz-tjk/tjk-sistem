"""Jason − AGF altılı kupon karşılaştırması (altili_deger.csv'den; 2 Kasım 2026, Doğan sorusu). python3 -I altili_ja.py <csv>"""
import sys,numpy as np,pandas as pd
D=pd.read_csv(sys.argv[1]);rng=np.random.default_rng(3)
for B in(64,256):
    x=D[D.B==B];m=x[x['mod']=='J'].merge(x[x['mod']=='A'],on=['t','h','k'],suffixes=('_J','_A'));m['g']=m.t+m.h
    print(f'\nB={B}: altılı {len(m)} (DEVİR dahil)')
    for per,f in(('tümü',m.t>='2000'),('2025',m.t<'2026'),('2026',m.t>='2026')):
        y=m[f];s=y.groupby('g')[['pay_J','cost_J','pay_A','cost_A','hit_J','hit_A','ph_J','ph_A']].sum();o=[];oh=[]
        for _ in range(3000):
            t=s.iloc[rng.integers(0,len(s),len(s))].sum();o.append(t.pay_J/t.cost_J-t.pay_A/t.cost_A);oh.append(t.hit_J/t.ph_J-t.hit_A/t.ph_A if t.ph_J and t.ph_A else np.nan)
        t=s.sum();lo,hi=np.percentile(o,[2.5,97.5])
        print(f'{per}: Jason ROI {t.pay_J/t.cost_J:.2f} (tutan {int(t.hit_J)}, model-bekl {t.ph_J:.1f}) | AGF ROI {t.pay_A/t.cost_A:.2f} (tutan {int(t.hit_A)}, bekl {t.ph_A:.1f}) | ROI farkı {t.pay_J/t.cost_J-t.pay_A/t.cost_A:+.2f} GA95 [{lo:+.2f},{hi:+.2f}] | maliyet J {y.cost_J.mean():.0f} A {y.cost_A.mean():.0f} kombinasyon/altılı')
