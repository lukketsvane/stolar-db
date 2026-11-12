import csv, sys, re, collections, statistics as st
sys.stdout.reconfigure(encoding='utf-8')
R=list(csv.DictReader(open(r"C:/Users/Iver/Documents/github/stolar-db/STOLAR/STOLAR.csv",encoding='utf-8-sig',newline='')))
def f(r,c):
    try: return float(r[c])
    except: return None
C=collections.Counter
def pref(i): 
    m=re.match(r'[A-Za-z]+',i); return m.group(0) if m else ('num' if i[:1].isdigit() else i[:3])
print('ID-prefiks:',C(pref(r['Objekt-ID']) for r in R).most_common(12))
print('lenkje-domene:',C(re.sub(r'https?://([^/]+)/.*',r'\1',r['Nasjonalmuseet']) for r in R).most_common(5))
def mus(r): return 'VA' if 'vam.ac.uk' in r['Nasjonalmuseet'] else 'NM'
print('museum:',C(mus(r) for r in R))
print('Nemning topp 25:',C(r['Nemning'] for r in R).most_common(25))
print('Materialar topp 12:',C(r['Materialar'] for r in R).most_common(12))
S=[r for r in R if f(r,'Setehøgde (cm)') is not None]
print('\n== setehøgd n=',len(S),' museum:',C(mus(r) for r in S),' ID-prefiks:',C(pref(r['Objekt-ID']) for r in S).most_common(6))
eq=[r for r in S if f(r,'Høgde (cm)') is not None and abs(f(r,'Setehøgde (cm)')-f(r,'Høgde (cm)'))<0.01]
print('setehøgd == totalhøgd:',len(eq))
sh=sorted(f(r,'Setehøgde (cm)') for r in S)
q=lambda a,p: a[int(p*(len(a)-1))]
print('setehøgd kvantilar 0/5/25/50/75/95/100:',[q(sh,p) for p in (0,.05,.25,.5,.75,.95,1)])
print('setehøgd <25 eller >60:',sum(1 for x in sh if x<25 or x>60))
print('Nemning i setehøgd-utvalet:',C(r['Nemning'] for r in S).most_common(15))
yr=[f(r,'Frå år') for r in S if f(r,'Frå år')]
print('år i setehøgd-utvalet: min/median/max',min(yr),st.median(yr),max(yr),' per hundreår:',sorted(C(int(y//100*100) for y in yr).items()))
print('stil i setehøgd-utvalet:',C(r['Stilperiode'] for r in S).most_common(16))
for c in ['Høgde (cm)','Breidde (cm)','Djupn (cm)']:
    v=sorted(x for x in (f(r,c) for r in R) if x is not None)
    print(c,'n',len(v),'kvantilar 0/1/5/50/95/99/100:',[q(v,p) for p in (0,.01,.05,.5,.95,.99,1)])
print('Stilperiode alle:',C(r['Stilperiode'] for r in R).most_common(20))
print('døme på rader med setehøgd:')
for r in S[:6]+S[150:153]: print('  ',r['Objekt-ID'],'|',r['Nemning'],'|',r['Materialar'][:25],'| H',r['Høgde (cm)'],'B',r['Breidde (cm)'],'D',r['Djupn (cm)'],'sete',r['Setehøgde (cm)'],'|',r['Datering'])
