import re,numpy as np,pandas as pd
src=open('data/analiz/clv_ilk_bakis.py').read().split("print(len(D)")[0]
exec(src)
D['bin']=pd.cut(D.p0,[0,.03,.06,.1,.2,1],labels=['<3%','3-6%','6-10%','10-20%','>20%'])
print('ort kayma (log p1/p0) p0 dilimine göre'); print(D.groupby('bin',observed=True).drift.agg(['mean','count']).round(4))
D['e']=pd.cut(D.edge,[-9,-np.log(1.25),0,np.log(1.25),9],labels=['sevilmeyen','hafif-','hafif+','sevilen'])
print(D.pivot_table(index='bin',columns='e',values='drift',aggfunc='mean',observed=True).round(3))
print(D.pivot_table(index='bin',columns='e',values='drift',aggfunc='count',observed=True))
