"""
Shannon-entropi (H') for materialar per hundreår i STOLAR-databasen.
Artikkel I: Materialar som geopolitisk historie.
"""
import csv
import math
from collections import Counter, defaultdict

CSV_PATH = "../stolar_db.csv"

# Les CSV
rows = []
with open(CSV_PATH, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Print column names for debugging
print("Kolonne-namn:", list(rows[0].keys())[:5])

print(f"Totalt rader: {len(rows)}")

# ---- 1. Parse materialar og hundreår ----
century_materials = defaultdict(list)  # hundreår -> liste av individuelle materialar
century_chairs = defaultdict(int)

for row in rows:
    century = row.get("Hundreår", "").strip()
    materials_raw = row.get("Materialar", "").strip()
    if not century or not materials_raw:
        continue
    # Materialar er kommaseparerte
    mats = [m.strip() for m in materials_raw.split(",") if m.strip()]
    century_materials[century].extend(mats)
    century_chairs[century] += 1

# Sorter hundreår kronologisk
def century_sort_key(c):
    # "1200-talet" -> 1200
    try:
        return int(c.split("-")[0])
    except ValueError:
        return 9999

sorted_centuries = sorted(century_materials.keys(), key=century_sort_key)

# ---- 2. Rekn ut Shannon-entropi per hundreår ----
print("\n" + "=" * 80)
print(f"{'Hundreaar':<15} {'Stolar':>7} {'Ulike mat.':>12} {'Tot. forek.':>12} {'H_prime':>8} {'H_max':>8} {'Evenness':>10}")
print("=" * 80)

results = []
for century in sorted_centuries:
    mats = century_materials[century]
    n_chairs = century_chairs[century]
    counts = Counter(mats)
    total = sum(counts.values())
    n_species = len(counts)

    # Shannon entropy: H' = -sum(p_i * ln(p_i))
    H = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            H -= p * math.log(p)

    H_max = math.log(n_species) if n_species > 1 else 0.0
    evenness = H / H_max if H_max > 0 else 0.0

    results.append({
        "century": century,
        "n_chairs": n_chairs,
        "n_unique_materials": n_species,
        "total_occurrences": total,
        "H_prime": H,
        "H_max": H_max,
        "evenness": evenness,
    })

    print(f"{century:<15} {n_chairs:>7} {n_species:>12} {total:>12} {H:>8.4f} {H_max:>8.4f} {evenness:>10.4f}")

# ---- 3. Topp materialar per hundreår ----
print("\n\n" + "=" * 80)
print("TOPP 5 MATERIALAR PER HUNDREÅR")
print("=" * 80)
for century in sorted_centuries:
    mats = century_materials[century]
    counts = Counter(mats)
    total = sum(counts.values())
    top5 = counts.most_common(5)
    print(f"\n{century} ({century_chairs[century]} stolar, {len(counts)} unike materialar):")
    for mat, count in top5:
        pct = 100 * count / total
        print(f"  {mat:<25} {count:>5}  ({pct:5.1f}%)")

# ---- 4. Globale materialar over tid ----
print("\n\n" + "=" * 80)
print("MATERIALKATEGORIAR: lokale vs. globale")
print("=" * 80)

local_woods = {"Bjørk", "Furu", "Eik", "Ask", "Or", "Alm", "Gran", "Bøk", "Osp", "Selje", "Lind"}
global_materials = {"Mahogni", "Teak", "Bambus", "Palisander", "Jakaranda", "Rotting", "Ibenholt",
                    "Palissander", "Rosentre", "Sedertre", "Ebony", "Rosewood", "Palme"}
industrial_materials = {"Stål", "Aluminium", "Plast", "Akryl", "Glasfiber", "Polypropylen",
                        "Polyuretan", "Skumplast", "Nylon", "Polyester", "Fiberplast",
                        "Krom", "Polykarbonat", "ABS", "PVC", "Gummi",
                        "Steel", "Aluminium", "Plastic", "Fiberglass", "Chrome",
                        "Polypropylene", "Polyurethane", "Foam", "Nylon"}
metals = {"Messing", "Bronse", "Jern", "Stål", "Aluminium", "Krom", "Sink",
          "Brass", "Bronze", "Iron", "Steel", "Chrome", "Zinc", "Copper", "Kopar"}

print(f"\n{'Hundreår':<15} {'Lokalt tre':>12} {'Globalt tre':>12} {'Metall':>12} {'Industrielt':>12} {'Anna':>12}")
print("-" * 75)
for century in sorted_centuries:
    mats = century_materials[century]
    total = len(mats)
    n_local = sum(1 for m in mats if m in local_woods)
    n_global = sum(1 for m in mats if m in global_materials)
    n_metal = sum(1 for m in mats if m in metals)
    n_industrial = sum(1 for m in mats if m in industrial_materials)
    n_other = total - n_local - n_global - n_metal - n_industrial
    print(f"{century:<15} {n_local:>5} ({100*n_local/total:4.1f}%) {n_global:>5} ({100*n_global/total:4.1f}%) "
          f"{n_metal:>5} ({100*n_metal/total:4.1f}%) {n_industrial:>5} ({100*n_industrial/total:4.1f}%) "
          f"{n_other:>5} ({100*n_other/total:4.1f}%)")

# ---- 5. Tidlegaste stolar ----
print("\n\n" + "=" * 80)
print("TIDLEGASTE STOLAR I DATABASEN (sortert etter år)")
print("=" * 80)
earliest = sorted([r for r in rows if r.get("Frå år")], key=lambda r: int(r["Frå år"]) if r["Frå år"].strip().lstrip('-').isdigit() else 9999)
for r in earliest[:15]:
    print(f"  {r.get('Frå år','?'):>6}  {r.get('Namn','ukjend'):<40}  Mat: {r.get('Materialar',''):<40}  {r.get('Nasjonalitet','')}")

# ---- 6. Nye materialar per hundreår ----
print("\n\n" + "=" * 80)
print("NYE MATERIALAR SOM DUKKAR OPP PER HUNDREÅR")
print("=" * 80)
seen = set()
for century in sorted_centuries:
    mats = set(Counter(century_materials[century]).keys())
    new = mats - seen
    if new:
        print(f"\n{century}: +{len(new)} nye")
        for m in sorted(new):
            print(f"  + {m}")
    seen.update(mats)
