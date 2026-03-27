"""Endaa djupare research: designar-profil, materialkoplingenettverk, formrom-trajektorie."""
import csv, math, os
from collections import Counter, defaultdict
import statistics
import numpy as np

rows=[]
with open("../stolar_db.csv",encoding="utf-8-sig") as f:
    for r in csv.DictReader(f): rows.append(r)
def sf(v):
    try: x=float(v.replace(",",".")); return x if x>0 else None
    except: return None
for r in rows:
    r["_mats"]=[m.strip() for m in r.get("Materialar","").split(",") if m.strip()]
    r["_h"]=sf(r.get("Høgde (cm)","")); r["_w"]=sf(r.get("Breidde (cm)",""))
    r["_d"]=sf(r.get("Djupn (cm)","")); r["_wt"]=sf(r.get("Estimert vekt (kg)",""))
    r["_style"]=r.get("Stilperiode","").strip(); r["_nat"]=r.get("Nasjonalitet","").strip()
    r["_prod"]=r.get("Produsent","").strip()
    try: r["_y"]=int(r.get("Frå år","").strip()); r["_y"]=r["_y"] if r["_y"]>100 else None
    except: r["_y"]=None

# 1. DESIGNAR-PROFIL: dimensjonar per namngitt designar
print("=" * 80)
print("1. DESIGNAR-PROFIL")
print("=" * 80)

designers = {
    "Chippendale": ["Chippendale"],
    "Aalto": ["Aalto"],
    "Eames": ["Eames"],
    "Breuer": ["Breuer"],
    "Thonet": ["Thonet"],
    "Jacobsen": ["Jacobsen"],
    "Wegner": ["Wegner"],
    "Korsmo": ["Korsmo"],
    "Kinsarvik": ["Kinsarvik"],
    "Hepplewhite": ["Hepplewhite"],
}

for name, keywords in designers.items():
    chairs = [r for r in rows if any(k.lower() in r["_prod"].lower() for k in keywords)]
    if not chairs:
        chairs = [r for r in rows if any(k.lower() in r.get("Namn","").lower() for k in keywords)]
    if chairs:
        hs = [r["_h"] for r in chairs if r["_h"]]
        ws = [r["_w"] for r in chairs if r["_w"]]
        mats_all = [m for r in chairs for m in r["_mats"]]
        top_mats = Counter(mats_all).most_common(3)
        hw = [r["_h"]/r["_w"] for r in chairs if r["_h"] and r["_w"] and r["_w"]>0]
        years = [r["_y"] for r in chairs if r["_y"]]

        print(f"\n  {name} ({len(chairs)} stolar, {min(years) if years else '?'}-{max(years) if years else '?'}):")
        if hs:
            print(f"    Hogde: {statistics.mean(hs):.1f} +/- {statistics.stdev(hs):.1f} cm" if len(hs)>1 else f"    Hogde: {hs[0]:.1f} cm")
        if ws:
            print(f"    Breidde: {statistics.mean(ws):.1f} cm")
        if hw:
            print(f"    H/W: {statistics.mean(hw):.3f}")
        print(f"    Materialar: {', '.join(f'{m}({n})' for m,n in top_mats)}")

# 2. FORMROM-TRAJEKTORIE: senterposisjon per hundreaar i H/W-rommet
print("\n" + "=" * 80)
print("2. FORMROM-TRAJEKTORIE: sentroidar per hundreaar")
print("=" * 80)

def cs(c):
    try: return int(c.split("-")[0])
    except: return 9999

main_c = sorted([c for c in set(r.get("Hundreår","").strip() for r in rows)
                  if c and c not in ("1200-talet","1300-talet","1400-talet")], key=cs)

for c in main_c:
    items = [r for r in rows if r.get("Hundreår","").strip()==c and r["_h"] and r["_w"] and r["_d"]]
    if len(items) < 10: continue
    mh = statistics.mean([r["_h"] for r in items])
    mw = statistics.mean([r["_w"] for r in items])
    md = statistics.mean([r["_d"] for r in items])
    hw = mh/mw if mw > 0 else 0
    vol = mh * mw * md
    n = len(items)
    print(f"  {c:<15} N={n:>4}  H={mh:.1f}  W={mw:.1f}  D={md:.1f}  H/W={hw:.2f}  Vol={vol:.0f}")

# 3. KVAR HUNDREAAR SI SIGNATURSTOL
print("\n" + "=" * 80)
print("3. SIGNATURSTOL: den mest 'typiske' stolen per hundreaar")
print("=" * 80)
print("  (Stolen naermast sentroiden)")

for c in main_c:
    items = [r for r in rows if r.get("Hundreår","").strip()==c and r["_h"] and r["_w"] and r["_d"]]
    if len(items) < 10: continue
    mh = statistics.mean([r["_h"] for r in items])
    mw = statistics.mean([r["_w"] for r in items])
    md = statistics.mean([r["_d"] for r in items])
    # Find chair closest to centroid
    best = None
    best_dist = float('inf')
    for r in items:
        dist = math.sqrt((r["_h"]-mh)**2 + (r["_w"]-mw)**2 + (r["_d"]-md)**2)
        if dist < best_dist:
            best_dist = dist
            best = r
    if best:
        print(f"  {c}: {best.get('Namn','?')[:40]:<40}  "
              f"H={best['_h']:.0f} W={best['_w']:.0f} D={best['_d']:.0f}  "
              f"Mat: {', '.join(best['_mats'][:3])}  "
              f"Dist={best_dist:.1f}")

# 4. STORSTE FORMSPRANG: kva stol er mest avvikande per hundreaar?
print("\n" + "=" * 80)
print("4. MEST AVVIKANDE STOL per hundreaar")
print("=" * 80)

for c in main_c:
    items = [r for r in rows if r.get("Hundreår","").strip()==c and r["_h"] and r["_w"]]
    if len(items) < 10: continue
    mh = statistics.mean([r["_h"] for r in items])
    mw = statistics.mean([r["_w"] for r in items])
    outlier = max(items, key=lambda r: math.sqrt((r["_h"]-mh)**2 + (r["_w"]-mw)**2))
    dist = math.sqrt((outlier["_h"]-mh)**2 + (outlier["_w"]-mw)**2)
    print(f"  {c}: {outlier.get('Namn','?')[:40]:<40}  "
          f"H={outlier['_h']:.0f} W={outlier['_w']:.0f}  Dist={dist:.0f}  "
          f"{outlier.get('Stilperiode','')}")

# 5. MATERIELL ENTROPI PER NASJON
print("\n" + "=" * 80)
print("5. MATERIELL ENTROPI PER NASJON")
print("=" * 80)

def entropy_bits(mats):
    c=Counter(mats); t=sum(c.values())
    if t==0: return 0
    return -sum((n/t)*math.log2(n/t) for n in c.values() if n>0)

nat_mats = defaultdict(list)
for r in rows:
    if r["_nat"] and r["_mats"]:
        nat_mats[r["_nat"]].extend(r["_mats"])

for nat in sorted(nat_mats, key=lambda n: len(nat_mats[n]), reverse=True)[:10]:
    mats = nat_mats[nat]
    H = entropy_bits(mats)
    S = len(set(mats))
    n_chairs = len([r for r in rows if r["_nat"]==nat])
    print(f"  {nat:<20} N={n_chairs:>4}  S={S:>3}  H'={H:.2f} bits  "
          f"Topp: {Counter(mats).most_common(1)[0][0]}")

# 6. STILPERIODE-TIDSKART: kvar stil si tidsspreiing
print("\n" + "=" * 80)
print("6. STIL-TIDSKART: kvar hundreaar er kvar stil representert?")
print("=" * 80)

style_years = defaultdict(list)
for r in rows:
    if r["_style"] and r["_y"]:
        style_years[r["_style"]].append(r["_y"])

for s in sorted(style_years, key=lambda x: statistics.mean(style_years[x])):
    years = style_years[s]
    if len(years) < 5: continue
    mn, mx = min(years), max(years)
    mean = statistics.mean(years)
    span = mx - mn
    print(f"  {s:<25} {mn}-{mx}  span={span:>4} aar  mean={mean:.0f}  N={len(years)}")
