import gzip,json,glob,re,numpy as np,pandas as pd
R='/home/claude/tjk-sistem/'
P=pd.read_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_p.pkl');P['tarih']=P.tarih.astype(str)
rows=[]
for f in sorted(glob.glob(R+'data/atyarisi/202[456]-*.json.gz')):
    d=f[-18:-8]
    if d<'2024-04-01': continue
    try: j=json.load(gzip.open(f,'rt'))
    except Exception: continue
    for hip,L in (j.get('program') or {}).items():
        if not isinstance(L,list): continue
        for k in L:
            rows.append((d,hip,int(k['number']),k.get('typeDescription',''),k.get('name',''),k.get('groupName','')))
M=pd.DataFrame(rows,columns=['tarih','hipodrom','kosu','tip','ad','grup'])
def sinif(t):
    t=t.upper()
    if t.startswith('G 1'):return 'G1'
    if t.startswith('G 2'):return 'G2'
    if t.startswith('G 3'):return 'G3'
    if t.startswith('KV') or 'KV-' in t:return 'KV'
    if 'HANDİKAP' in t or 'HANDIKAP' in t:return 'Handikap'
    if 'ŞARTLI' in t:return 'Şartlı'
    if 'MAIDEN' in t or 'MAİDEN' in t:return 'Maiden'
    return 'Diğer'
M['sinif']=M.tip.map(sinif)
print(M.tip.value_counts().head(25).to_string()); print(M.sinif.value_counts())
D=P.merge(M.drop_duplicates(['tarih','hipodrom','kosu']),on=['tarih','hipodrom','kosu'],how='left')
print(D.sinif.isna().mean())
D.to_pickle('/tmp/claude-0/-home-claude/040c998b-aac2-52a8-b71c-a3999afbcf3f/scratchpad/oos_sinif.pkl')
