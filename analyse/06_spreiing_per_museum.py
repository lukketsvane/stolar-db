"""Prøve A per museum: robust spreiing og stildel for kvar akse, pluss setehøgd over tid.
Køyr etter 04_reinsa_tabell.py:  python analyse/06_spreiing_per_museum.py
Robust spreiing = 1.4826 * MAD / median.  Stildel = epsilon-kvadrat for stilperiode på log-mål (stilar med minst 10 stolar)."""
import csv, sys, collections, math, os
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = [r for r in csv.DictReader(open(os.path.join(ROT, 'analyse', 'data', 'stolar_reinsa.csv'), encoding='utf-8-sig'))
     if r['vaksenstol'] == '1' and r['maal_ok'] == '1']
def rcv(x):
    x = np.asarray(x, float); return 1.4826 * np.median(np.abs(x - np.median(x))) / np.median(x)
def eps2(v, g, minn=10):
    d = collections.defaultdict(list)
    for a, k in zip(v, g):
        if k: d[k].append(math.log(a))
    d = {k: x for k, x in d.items() if len(x) >= minn}
    if len(d) < 2: return float('nan'), len(d)
    al = np.concatenate([np.array(x) for x in d.values()]); N = len(al); k = len(d)
    ssb = sum(len(x) * (np.mean(x) - al.mean()) ** 2 for x in d.values()); sst = ((al - al.mean()) ** 2).sum()
    return (ssb - (k - 1) * (sst - ssb) / (N - k)) / sst, k
for m in ('NM', 'VA'):
    A = [r for r in R if r['museum'] == m]; S = [r for r in A if r['sete_ok'] == '1']
    print(f'-- {m}: n mål ok {len(A)}, med setehøgd ok {len(S)}')
    for lab, sub, f in (('sete', S, lambda r: float(r['sete'])), ('rygg', S, lambda r: float(r['H']) - float(r['sete'])),
                        ('djupn', A, lambda r: float(r['D'])), ('breidd', A, lambda r: float(r['B'])), ('totalhøgd', A, lambda r: float(r['H']))):
        v = [f(r) for r in sub]; e, k = eps2(v, [r['stil'] for r in sub])
        print(f'   {lab:10s} n={len(v):4d} median {np.median(v):5.1f}  robust spreiing {rcv(v):.3f}  SD {np.std(v, ddof=1):5.1f}  stildel {e:.2f} ({k} stilar)')
    se = np.array([float(r['sete']) for r in S]); yr = np.array([float(r['aar_fraa']) if r['aar_fraa'] else np.nan for r in S])
    for a, b in ((1500, 1700), (1700, 1800), (1800, 1900), (1900, 2030)):
        q = (yr >= a) & (yr < b)
        if q.sum() >= 5: print(f'      {a}-{b}: n={int(q.sum()):3d} median sete {np.median(se[q]):.1f}')
    print('      del i 42-46 cm:', round(float(((se >= 42) & (se <= 46)).mean()), 2))
