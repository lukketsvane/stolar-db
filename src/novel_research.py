"""
NOVEL RESEARCH: Sporsmal ingen har stilt for.
Genuint nye analytiske vinklar for STOLAR-artiklane.
"""
import csv, math, os, sys
from collections import Counter, defaultdict
from itertools import combinations
import statistics
import numpy as np

CSV = "../stolar_db.csv"
rows = []
with open(CSV, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f): rows.append(r)

def sf(v):
    try: x=float(v.replace(",",".")); return x if x>0 else None
    except: return None
def museum(r):
    if "nasjonalmuseet.no" in r.get("Nasjonalmuseet","") or r.get("Objekt-ID","").startswith(("OK-","NMK")):
        return "NMK"
    return "V&A"

for r in rows:
    r["_m"]=museum(r); r["_mats"]=[m.strip() for m in r.get("Materialar","").split(",") if m.strip()]
    r["_c"]=r.get("Hundreår","").strip(); r["_h"]=sf(r.get("Høgde (cm)",""))
    r["_w"]=sf(r.get("Breidde (cm)","")); r["_d"]=sf(r.get("Djupn (cm)",""))
    r["_wt"]=sf(r.get("Estimert vekt (kg)","")); r["_sh"]=sf(r.get("Setehøgde (cm)",""))
    r["_style"]=r.get("Stilperiode","").strip(); r["_nat"]=r.get("Nasjonalitet","").strip()
    r["_techs"]=[t.strip() for t in r.get("Teknikk","").split(",") if t.strip()]
    r["_matkom"]=r.get("Materialkommentar","").strip()
    try: r["_y"]=int(r.get("Frå år","").strip()); r["_y"]=r["_y"] if r["_y"]>100 else None
    except: r["_y"]=None

print("=" * 90)
print("  NOVEL RESEARCH: NYE SPORSMAL TIL DATAA")
print("=" * 90)

# ================================================================
# 1. MATERIALRESEPTAR: Kva materialkombinasjonar er mest stabile?
# ================================================================
print("\n\n" + "=" * 90)
print("1. MATERIALRESEPTAR: dei mest stabile kombinasjonane")
print("=" * 90)
print("   (Kva materialpar dukkar opp saman igjen og igjen?)")

pair_counts = Counter()
pair_centuries = defaultdict(set)
for r in rows:
    if len(r["_mats"]) >= 2:
        for a, b in combinations(sorted(set(r["_mats"])), 2):
            pair_counts[(a,b)] += 1
            if r["_c"]: pair_centuries[(a,b)].add(r["_c"])

print(f"\n  {'Materialpar':<40} {'N':>5} {'Hundreaar':>12} {'Levetid'}")
print("  " + "-" * 70)
for (a,b), n in pair_counts.most_common(25):
    cents = len(pair_centuries[(a,b)])
    print(f"  {a} + {b:<25} {n:>5} {cents:>8} h.aa   {'TIDLAUS' if cents >= 5 else 'EPOKEBUNDEN'}")

# ================================================================
# 2. MATERIALRADIUSEN: Kor langt reiser materiala?
# ================================================================
print("\n\n" + "=" * 90)
print("2. MATERIALRADIUSEN: kvantifisering av geografisk rekkjevidd")
print("=" * 90)

# Kategoriser kvart materiale etter opphavleg radius
radius = {
    # Lokalt (< 100 km)
    "Bjørk": 0, "Furu": 0, "Eik": 0, "Ask": 0, "Or": 0, "Alm": 0,
    "Gran": 0, "Bøk": 0, "Osp": 0, "Lind": 0, "Lønn": 0,
    # Europeisk (100-2000 km)
    "Nøttetre": 1, "Buksbom": 1, "Messing": 1, "Bronse": 1, "Jern": 1,
    "Lin": 1, "Ull": 1, "Bomull": 1, "Hestetagl": 1, "Lær": 1, "Skinn": 1,
    "Sølv": 1, "Pæretre": 1,
    # Kolonialt/interkontinentalt (> 5000 km)
    "Mahogni": 2, "Ibenholt": 2, "Palisander": 2, "Rotting": 2, "Teak": 2,
    "Bambus": 2, "Silke": 2, "Palme": 2, "Jakaranda": 2,
    # Industrielt (globalt, men abstrahert)
    "Stål": 3, "Aluminium": 3, "Plast": 3, "Glasfiber": 3, "Kryssfiner": 3,
    "Polypropylen": 3, "Polyuretan": 3, "Skumplast": 3, "Nylon": 3,
    "Polykarbonat": 3, "Gummi": 3,
}
radius_names = {0: "Lokalt (<100 km)", 1: "Europeisk (100-2000 km)",
                2: "Kolonialt (>5000 km)", 3: "Industrielt (globalt)"}

# Rekn ut gjennomsnittleg materialradius per stol over tid
period_radius = defaultdict(list)
for r in rows:
    if r["_y"] and r["_mats"]:
        p = (r["_y"]//50)*50
        rads = [radius.get(m, 1) for m in r["_mats"]]
        max_rad = max(rads) if rads else 0
        mean_rad = sum(rads)/len(rads) if rads else 0
        period_radius[p].append(max_rad)

print(f"\n  {'Periode':<15} {'N':>5} {'Gj.snitt maks-radius':>22} {'Tolking'}")
print("  " + "-" * 60)
for p in sorted(period_radius):
    if p < 1400 or len(period_radius[p]) < 5: continue
    mr = statistics.mean(period_radius[p])
    label = radius_names.get(round(mr), "?")
    bar = "#" * int(mr * 15)
    print(f"  {p}-{p+49:<10} {len(period_radius[p]):>5} {mr:>22.2f}   {bar}")

# ================================================================
# 3. SETEHOGDE SOM % AV TOTALHOGDE: ergonomisk ratio
# ================================================================
print("\n\n" + "=" * 90)
print("3. ERGONOMISK RATIO: setehogde / totalhogde over tid")
print("=" * 90)

def cs(c):
    try: return int(c.split("-")[0])
    except: return 9999

main_c = sorted([c for c in set(r["_c"] for r in rows if r["_c"])
                  if c not in ("1200-talet","1300-talet","1400-talet")], key=cs)

for c in main_c:
    items = [r for r in rows if r["_c"]==c and r["_h"] and r["_sh"] and r["_h"]>30]
    if len(items) < 5: continue
    ratios = [r["_sh"]/r["_h"] for r in items]
    mr = statistics.mean(ratios)
    print(f"  {c:<15} N={len(items):>4}  SH/H = {mr:.3f}  ({mr*100:.1f}%)"
          f"  [setet er {mr*100:.0f}% av total hogde]")

# ================================================================
# 4. MATERIELL ENTROPI PER EINSKILD STOL: individuell kompleksitet
# ================================================================
print("\n\n" + "=" * 90)
print("4. INDIVIDUELL MATERIALENTROPI: kor kompleks er KVAR stol?")
print("=" * 90)

# Entropi per stol = log2(antal materialar) som proxy
period_individual = defaultdict(list)
for r in rows:
    if r["_y"] and r["_mats"]:
        n_mats = len(set(r["_mats"]))
        h_individual = math.log2(n_mats) if n_mats > 1 else 0
        p = (r["_y"]//50)*50
        period_individual[p].append(h_individual)

print(f"\n  {'Periode':<15} {'N':>5} {'Gj.snitt H_ind':>16} {'Tolking'}")
for p in sorted(period_individual):
    if p < 1400 or len(period_individual[p]) < 5: continue
    mh = statistics.mean(period_individual[p])
    print(f"  {p}-{p+49:<10} {len(period_individual[p]):>5} {mh:>16.3f} bits"
          f"  ({'enkel' if mh < 0.5 else 'moderat' if mh < 1.0 else 'kompleks'})")

# ================================================================
# 5. MAHOGNI-HESTETAGL-KOPLINGA: kvifor?
# ================================================================
print("\n\n" + "=" * 90)
print("5. MAHOGNI-HESTETAGL-KOPLINGA")
print("=" * 90)

mahogni_chairs = [r for r in rows if "Mahogni" in r["_mats"]]
with_hestetagl = [r for r in mahogni_chairs if "Hestetagl" in r["_mats"]]
print(f"  Stolar med mahogni: {len(mahogni_chairs)}")
print(f"  Av desse med hestetagl: {len(with_hestetagl)} ({100*len(with_hestetagl)/len(mahogni_chairs):.1f}%)")

# Kva materialar opptrer ALLTID med mahogni?
mahogni_co = Counter()
for r in mahogni_chairs:
    for m in r["_mats"]:
        if m != "Mahogni": mahogni_co[m] += 1

print(f"\n  Materialar som opptrer saman med mahogni:")
for m, n in mahogni_co.most_common(15):
    pct = 100*n/len(mahogni_chairs)
    print(f"    {m:<20} {n:>4} ({pct:.1f}%)")

# Materialkommentar for mahogni+hestetagl
print(f"\n  Materialkommentar for mahogni+hestetagl-stolar:")
for r in with_hestetagl[:8]:
    if r["_matkom"]:
        print(f"    {r.get('Objekt-ID','?'):<15} {r['_matkom'][:80]}")

# ================================================================
# 6. TEKNIKK x MATERIALE: affordanse-matrisa
# ================================================================
print("\n\n" + "=" * 90)
print("6. AFFORDANSE-MATRISA: kva teknikkar 'tillater' kvart materiale?")
print("=" * 90)

mat_tech = defaultdict(Counter)
for r in rows:
    for m in r["_mats"]:
        for t in r["_techs"]:
            mat_tech[m][t] += 1

key_mats = ["Mahogni", "Eik", "Bjørk", "Bøk", "Furu", "Stål", "Kryssfiner", "Plast"]
key_techs = ["Polstring", "Tapping", "Skjæring", "Dreiing", "Formbøying",
             "Laminering", "Sveising", "Skruing", "Fletting"]

print(f"\n  {'':>15}", end="")
for t in key_techs: print(f" {t[:7]:>8}", end="")
print()
for m in key_mats:
    total = sum(mat_tech[m].values()) or 1
    print(f"  {m:<15}", end="")
    for t in key_techs:
        pct = 100*mat_tech[m].get(t, 0)/total
        if pct > 0:
            print(f" {pct:>7.0f}%", end="")
        else:
            print(f"       -", end="")
    print()

# ================================================================
# 7. FORMVARIASJON INNANFOR SAME FUNKSJON: det ultimate beviset
# ================================================================
print("\n\n" + "=" * 90)
print("7. FORMVARIASJON: det ultimate beviset mot FFF")
print("=" * 90)

all_h = [r["_h"] for r in rows if r["_h"] and 20 < r["_h"] < 250]
all_w = [r["_w"] for r in rows if r["_w"] and 2 < r["_w"] < 200]
all_d = [r["_d"] for r in rows if r["_d"] and 1 < r["_d"] < 200]
all_wt = [r["_wt"] for r in rows if r["_wt"] and r["_wt"] < 120]

for name, vals in [("Hogde (cm)", all_h), ("Breidde (cm)", all_w),
                   ("Djupn (cm)", all_d), ("Vekt (kg)", all_wt)]:
    mn, mx = min(vals), max(vals)
    q1, q3 = np.percentile(vals, [25, 75])
    iqr = q3 - q1
    cv = statistics.stdev(vals) / statistics.mean(vals)
    print(f"  {name:<15} N={len(vals):>5}  Range=[{mn:.1f}, {mx:.1f}]  "
          f"Ratio={mx/mn:.0f}x  IQR=[{q1:.1f}, {q3:.1f}]  CV={cv:.3f}")

# Volum
vols = [r["_h"]*r["_w"]*r["_d"] for r in rows
        if r["_h"] and r["_w"] and r["_d"]
        and 20<r["_h"]<250 and 2<r["_w"]<200 and 1<r["_d"]<200]
print(f"\n  Volum (cm3)    N={len(vols):>5}  Range=[{min(vols):.0f}, {max(vols):.0f}]  "
      f"Ratio={max(vols)/min(vols):.0f}x  CV={statistics.stdev(vols)/statistics.mean(vols):.3f}")

# ================================================================
# 8. HISTORISKE KNUTEPUNKT: kva skjer ved kritiske aar?
# ================================================================
print("\n\n" + "=" * 90)
print("8. HISTORISKE KNUTEPUNKT: materialmangfald rundt kritiske aar")
print("=" * 90)

events = [
    (1700, "Unionstida / Queen Anne-tronstigning"),
    (1750, "Sjuaarskrigen startar (britisk karibisk ekspansjon)"),
    (1800, "Napoleonskrigane / handelsblokade"),
    (1850, "Great Exhibition / industrialisering"),
    (1900, "Jugend / nasjonalromantikk"),
    (1925, "Bauhaus / Art Deco"),
    (1950, "Etterkrigstid / Scandinavian Design"),
    (1970, "Oljekrisa / postmodernisme"),
]

def entropy_bits(mats):
    c = Counter(mats); t = sum(c.values())
    if t == 0: return 0
    return -sum((n/t)*math.log2(n/t) for n in c.values() if n > 0)

for year, event in events:
    # 20-aars vindu
    window = [m for r in rows if r["_y"] and abs(r["_y"]-year)<=10
              for m in r["_mats"]]
    n_chairs = len([r for r in rows if r["_y"] and abs(r["_y"]-year)<=10])
    if window:
        H = entropy_bits(window)
        S = len(set(window))
        top3 = Counter(window).most_common(3)
        top_str = ", ".join(f"{m}({n})" for m,n in top3)
        print(f"  {year} {event[:45]:<45}  N={n_chairs:>4} S={S:>3} H'={H:.2f}  {top_str}")

# ================================================================
# 9. CUBAMAHOGNI vs GENERISK MAHOGNI
# ================================================================
print("\n\n" + "=" * 90)
print("9. CUBAMAHOGNI: presisjonsnivaa i materialregistrering")
print("=" * 90)

for keyword in ["cubamahogni", "mahognifiner", "massiv mahogni", "beiset mahogni",
                "mahogni finert", "imitert mahogni", "mahogni med"]:
    matches = [r for r in rows if keyword.lower() in r["_matkom"].lower()]
    if matches:
        years = [r["_y"] for r in matches if r["_y"]]
        yr = f"{min(years)}-{max(years)}" if years else "?"
        print(f"  '{keyword}': {len(matches)} stolar  ({yr})")
        for r in matches[:3]:
            print(f"    {r.get('Objekt-ID','?'):<15} {r['_matkom'][:70]}")

# ================================================================
# 10. MATERIELL DEMOKRATISERING: naar vert luksus tilgjengeleg?
# ================================================================
print("\n\n" + "=" * 90)
print("10. MATERIELL DEMOKRATISERING")
print("=" * 90)

luxury = ["Mahogni", "Silke", "Ibenholt", "Palisander", "Bronse", "Sølv"]
industrial = ["Stål", "Kryssfiner", "Plast", "Aluminium", "Glasfiber"]

for mat_list, label in [(luxury, "LUKSUS"), (industrial, "INDUSTRIELT")]:
    print(f"\n  {label}:")
    for m in mat_list:
        decades = defaultdict(int)
        for r in rows:
            if m in r["_mats"] and r["_y"]:
                decades[(r["_y"]//10)*10] += 1
        if decades:
            first = min(decades.keys())
            peak_dec = max(decades, key=decades.get)
            last = max(d for d in decades if decades[d] > 0)
            total = sum(decades.values())
            print(f"    {m:<15} Forste: {first}  Topp: {peak_dec} (n={decades[peak_dec]})  "
                  f"Siste: {last}  Totalt: {total}")

print("\n\n" + "=" * 90)
print("  FERDIG: novel research complete")
print("=" * 90)
