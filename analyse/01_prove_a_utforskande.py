import csv, sys, re, collections, math, random
import numpy as np
sys.stdout.reconfigure(encoding='utf-8'); random.seed(1); rng=np.random.default_rng(1)
R=list(csv.DictReader(open(r"C:/Users/Iver/Documents/github/stolar-db/STOLAR/STOLAR.csv",encoding='utf-8-sig',newline='')))
def f(r,c):
    try: return float(r[c])
    except: return None
mus=lambda r: 'VA' if 'vam.ac.uk' in r['Nasjonalmuseet'] else 'NM'
H,B,D,SE='Høgde (cm)','Breidde (cm)','Djupn (cm)','Setehøgde (cm)'
print('nullverdiar (0.0) per museum  H/B/D:',{m:[sum(1 for r in R if mus(r)==m and f(r,c)==0) for c in (H,B,D)] for m in ('NM','VA')})
print('H>200:',sum(1 for r in R if (f(r,H) or 0)>200),' B>150:',sum(1 for r in R if (f(r,B) or 0)>150),' D>150:',sum(1 for r in R if (f(r,D) or 0)>150))
adult=lambda r: r['Nemning'] not in ('Krakk','Barnestol','Benkestol','Stol utan rygg')
def ok(r): 
    h,b,d=f(r,H),f(r,B),f(r,D)
    return adult(r) and h and b and d and 50<=h<=200 and 25<=b<=150 and 25<=d<=150
A=[r for r in R if ok(r)]
print('\nREINSA (vaksenstol, H 50-200, B/D 25-150): n=',len(A),collections.Counter(mus(r) for r in A))
def spread(x):
    x=np.asarray(x,float); l=np.log(x)
    mad=1.4826*np.median(np.abs(x-np.median(x)))
    return dict(n=len(x),med=round(float(np.median(x)),1),sd=round(float(x.std(ddof=1)),1),cv=round(float(x.std(ddof=1)/x.mean()),3),rcv=round(float(mad/np.median(x)),3),sdlog=round(float(l.std(ddof=1)),3))
def eps2(vals,groups,minn=10):
    g=collections.defaultdict(list)
    for v,k in zip(vals,groups): g[k].append(math.log(v))
    g={k:v for k,v in g.items() if len(v)>=minn and k}
    allv=np.concatenate([np.array(v) for v in g.values()]); N=len(allv); k=len(g)
    ssb=sum(len(v)*(np.mean(v)-allv.mean())**2 for v in g.values()); sst=((allv-allv.mean())**2).sum(); msw=(sst-ssb)/(N-k)
    return round(float((ssb-(k-1)*msw)/sst),3),k,N
for lab,sub in (('begge',A),('NM',[r for r in A if mus(r)=='NM']),('VA',[r for r in A if mus(r)=='VA'])):
    print('--',lab)
    for c in (D,B,H):
        v=[f(r,c) for r in sub]; e=eps2(v,[r['Stilperiode'] for r in sub])
        print(f'   {c:14s}',spread(v),' stil-eps2 (k,N):',e)
# setehøgd
Sx=[r for r in A if f(r,SE) and abs(f(r,SE)-f(r,H))>0.01 and f(r,SE)<f(r,H)]
print('\nSETEHØGD brukande (ikkje lik H, < H, reinsa): n=',len(Sx),collections.Counter(mus(r) for r in Sx))
se=np.array([f(r,SE) for r in Sx]); hh=np.array([f(r,H) for r in Sx]); bb=np.array([f(r,B) for r in Sx]); dd=np.array([f(r,D) for r in Sx]); back=hh-se
sty=[r['Stilperiode'] for r in Sx]
for lab,v in (('sete',se),('rygg=H-sete',back),('djupn',dd),('breidd',bb),('total H',hh)):
    print(f'   {lab:12s}',spread(v),' stil-eps2 (k,N):',eps2(v,sty,8))
print('   sete kvantilar 1/5/25/50/75/95/99:',[round(float(np.quantile(se,p)),1) for p in (.01,.05,.25,.5,.75,.95,.99)])
print('   del i [42,46]:',round(float(((se>=42)&(se<=46)).mean()),3),' del i [40,50]:',round(float(((se>=40)&(se<=50)).mean()),3))
k4=float(((se-se.mean())**4).mean()/se.var()**2-3); print('   eksess-kurtose sete:',round(k4,2),'(Laplace 3, normal 0)')
# tid
yr=np.array([f(r,'Frå år') or np.nan for r in Sx]); m=~np.isnan(yr)
sl=np.polyfit(yr[m],se[m],1); print('   lineær trend sete (cm/100 år):',round(sl[0]*100,2),' etter 1850 n=',int((yr>=1850).sum()),'median',round(float(np.median(se[yr>=1850])),1),' før 1850 median',round(float(np.median(se[(yr<1850)])),1))
for a,b in ((1500,1700),(1700,1800),(1800,1900),(1900,2030)):
    q=(yr>=a)&(yr<b); print(f'   {a}-{b}: n={int(q.sum())} sete med {np.median(se[q]):.1f} sd {se[q].std(ddof=1):.1f} | rygg med {np.median(back[q]):.1f} sd {back[q].std(ddof=1):.1f}')
# forhold varians, bootstrap
L=np.log(np.c_[se,back,dd,bb])
def ratio(Lx): v=Lx.var(axis=0,ddof=1); return v[0]/v[1]
bs=[ratio(L[rng.integers(0,len(L),len(L))]) for _ in range(4000)]
print('   var(log sete)/var(log rygg) =',round(float(ratio(L)),3),' 95% bootstrap:',[round(float(np.quantile(bs,p)),3) for p in (.025,.975)])
Cm=np.corrcoef(L.T); print('   korr log(sete,rygg,djupn,breidd):\n',np.round(Cm,2))
w,v=np.linalg.eigh(np.cov(L.T)); print('   PC1-del av varians:',round(float(w[-1]/w.sum()),3),' ladningar (sete,rygg,djupn,breidd):',np.round(v[:,-1],2))
