"""T53: MJV vs MJ gerçek ödemeli egzotik ROI (donmuş kural). python3 data/analiz/video_roi_t53.py"""
import sys,glob,pickle,itertools,random,numpy as np,pandas as pd
sys.path.insert(0,'.')
from tjk import egzotik as E
random.seed(53)
AYLAR=[f"2026-{m:02d}" for m in range(1,11)]
O=pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/odeme/2026-*.csv.gz"))]);PAY={}
for q in O.itertuples():
    if q.tur in E.K:
        kk=tuple(int(z) for z in str(q.kombo).split("/")); kk=tuple(sorted(kk)) if q.tur=="İKİLİ" else kk
        PAY.setdefault((q.tarih,q.hipodrom,int(q.kosu)),{}).setdefault(q.tur,[]).append((kk,float(q.tutar)))
def combos(s,gam,k):
    out={};n=len(s)
    for c in itertools.permutations(range(n),k):
        pr=1.0;used=[]
        for j,i in enumerate(c):
            z=np.exp(gam[j]*(s-s.max()));m=np.ones(n,bool);m[used]=False;pr*=z[i]/z[m].sum();used.append(i)
        out[c]=pr
    return out
def sym(A):
    A2={}
    for c,v in A.items(): A2[tuple(sorted(c))]=A2.get(tuple(sorted(c)),0)+v
    return A2
def yukle(v):
    o={}
    for a in AYLAR:
        c=pickle.load(open(f"/tmp/claude-0/cache_{v}_{a}.pkl","rb"))
        for k,key in enumerate(c["keys"]): o[key]=(c["S3"][k],c["g3"],c["nos"][k],c["gun"][k],a)
    return o
Mj=yukle("MJ");Mv=yukle("MJV");L0={}
for a in AYLAR:
    c=pickle.load(open(f"/tmp/claude-0/cache_MJ_{a}.pkl","rb"))
    for k,key in enumerate(c["keys"]): L0[key]=c["L0"][k]
ST={}   # (model,tur) -> list (gun, ay, harcama, getiri, ortak anahtar)
for key in sorted(set(Mj)&set(Mv)):
    pr=PAY.get(key)
    if not pr: continue
    nos=Mj[key][2];n=len(nos);pk=np.exp(L0[key][:n])
    for tur in ("SIRALI İKİLİ","ÜÇLÜ BAHİS","İKİLİ"):
        if tur not in pr: continue
        kk=E.K[tur];pay={}
        for c,t in pr[tur]: pay[c]=pay.get(c,0)+t
        A=E._kombolar(dict(enumerate(pk)),kk)
        if tur=="İKİLİ": A=sym(A)
        for m,M in (("MJ",Mj),("MJV",Mv)):
            S,g,_,gun,ay=M[key];B=combos(S[:n],g,kk)
            if tur=="İKİLİ": B=sym(B)
            sec=[c for c in A if A[c]>=E.ESIK[tur] and B[c]/A[c]>=1.15]
            if not sec: continue
            ST.setdefault((m,tur),[]).append((gun,ay,len(sec)*E.BIRIM[tur],sum(pay.get(tuple(nos[i] for i in c),0.0) for c in sec)))
def roi(L,gun,gg):
    b=sum(x[2] for g in gun for x in gg.get(g,[]));return (sum(x[3] for g in gun for x in gg.get(g,[]))-b)/b if b else 0.0
def grp(L):
    gg={}
    for x in L: gg.setdefault(x[0],[]).append(x)
    return gg
def rapor(ad,sel):
    LA=[x for t in sel for x in ST.get(("MJ",t),[])];LB=[x for t in sel for x in ST.get(("MJV",t),[])]
    for per,fil in (("tümü",lambda a:True),("H",lambda a:a<="2026-03"),("B",lambda a:a>="2026-04")):
        la=[x for x in LA if fil(x[1])];lb=[x for x in LB if fil(x[1])]
        gun=sorted({x[0] for x in la+lb});ga,gb=grp(la),grp(lb)
        ra,rb=roi(la,gun,ga),roi(lb,gun,gb);bs=[]
        for _ in range(1000):
            G=[random.choice(gun) for _ in gun];bs.append(roi(lb,G,gb)-roi(la,G,ga))
        t3=lambda L:sorted([x[3] for x in L],reverse=True)[:3]
        def roi3(L):
            tt=sum(x[2] for x in L);top=t3(L);return (sum(x[3] for x in L)-sum(top)-tt)/tt if tt else 0
        tut=lambda L:sum(1 for x in L if x[3]>0)
        print(f"{ad:14s}[{per:4s}] MJ n={len(la)} tutan={tut(la)} ROI {ra:+.1%} (ilk3 çıkar {roi3(la):+.1%}) | MJV n={len(lb)} tutan={tut(lb)} ROI {rb:+.1%} ({roi3(lb):+.1%}) | MJV−MJ {rb-ra:+.1%} [{np.percentile(bs,2.5):+.1%},{np.percentile(bs,97.5):+.1%}]",flush=True)
for t in ("SIRALI İKİLİ","İKİLİ","ÜÇLÜ BAHİS"): rapor(t,[t])
rapor("TOPLAM",["SIRALI İKİLİ","İKİLİ","ÜÇLÜ BAHİS"])
