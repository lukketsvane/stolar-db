"""
Shannon-entropi (H') i BITS for materialar per hundreaar i STOLAR-databasen.
Artikkel I v2: Materialar som geopolitisk historie.
Split NMK vs V&A, mahogni-dominans, materiell dobbeltheit.
"""
import csv
import math
from collections import Counter, defaultdict

CSV_PATH = "../stolar_db.csv"

rows = []
with open(CSV_PATH, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print(f"Totalt rader: {len(rows)}")

# Identifiser museum basert paa Objekt-ID og Nasjonalmuseet-felt
def get_museum(row):
    nm_url = row.get("Nasjonalmuseet", "").strip()
    obj_id = row.get("Objekt-ID", "").strip()
    if "nasjonalmuseet.no" in nm_url or obj_id.startswith("OK-") or obj_id.startswith("NMK"):
        return "NMK"
    else:
        return "V&A"

# Parse alle rader
parsed = []
for row in rows:
    century = row.get("Hundreaar", row.get("Hundreår", "")).strip()
    materials_raw = row.get("Materialar", "").strip()
    fra_aar = row.get("Fraa aar", row.get("Frå år", "")).strip()
    museum = get_museum(row)
    namn = row.get("Namn", "ukjend")
    nasjonalitet = row.get("Nasjonalitet", "")

    if not century or not materials_raw:
        continue

    mats = [m.strip() for m in materials_raw.split(",") if m.strip()]
    parsed.append({
        "century": century,
        "materials": mats,
        "museum": museum,
        "year": fra_aar,
        "name": namn,
        "nationality": nasjonalitet,
    })

print(f"Gyldige rader (hundreaar + materialar): {len(parsed)}")

# Sorter hundreaar
def century_sort_key(c):
    try:
        return int(c.split("-")[0])
    except ValueError:
        return 9999

# ---- 1. Shannon-entropi i BITS per hundreaar ----
def compute_entropy_bits(material_list):
    counts = Counter(material_list)
    total = sum(counts.values())
    n_species = len(counts)
    H = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            H -= p * math.log2(p)
    H_max = math.log2(n_species) if n_species > 1 else 0.0
    J = H / H_max if H_max > 0 else 0.0
    return H, H_max, J, n_species, total, counts

# Samla entropi
century_materials_all = defaultdict(list)
century_materials_nmk = defaultdict(list)
century_materials_va = defaultdict(list)
century_chairs_all = defaultdict(int)
century_chairs_nmk = defaultdict(int)
century_chairs_va = defaultdict(int)

for p in parsed:
    century_materials_all[p["century"]].extend(p["materials"])
    century_chairs_all[p["century"]] += 1
    if p["museum"] == "NMK":
        century_materials_nmk[p["century"]].extend(p["materials"])
        century_chairs_nmk[p["century"]] += 1
    else:
        century_materials_va[p["century"]].extend(p["materials"])
        century_chairs_va[p["century"]] += 1

sorted_centuries = sorted(century_materials_all.keys(), key=century_sort_key)

print("\n" + "=" * 90)
print("SHANNON-ENTROPI I BITS - SAMLA")
print("=" * 90)
print(f"{'Hundreaar':<15} {'N':>5} {'Forek.':>8} {'S':>4} {'H (bits)':>10} {'Hmax':>8} {'J':>8}")
print("-" * 60)
for c in sorted_centuries:
    H, Hm, J, S, tot, _ = compute_entropy_bits(century_materials_all[c])
    N = century_chairs_all[c]
    print(f"{c:<15} {N:>5} {tot:>8} {S:>4} {H:>10.3f} {Hm:>8.3f} {J:>8.4f}")

# ---- 2. NMK vs V&A ----
print("\n" + "=" * 90)
print("SHANNON-ENTROPI: NMK vs V&A")
print("=" * 90)
print(f"{'Hundreaar':<15} {'N_NMK':>6} {'H_NMK':>8} {'N_VA':>6} {'H_VA':>8} {'Delta':>8}")
print("-" * 55)
for c in sorted_centuries:
    nmk_mats = century_materials_nmk.get(c, [])
    va_mats = century_materials_va.get(c, [])
    H_nmk = compute_entropy_bits(nmk_mats)[0] if nmk_mats else 0
    H_va = compute_entropy_bits(va_mats)[0] if va_mats else 0
    N_nmk = century_chairs_nmk.get(c, 0)
    N_va = century_chairs_va.get(c, 0)
    delta = H_nmk - H_va if nmk_mats and va_mats else float('nan')
    d_str = f"{delta:>8.3f}" if not math.isnan(delta) else "     N/A"
    print(f"{c:<15} {N_nmk:>6} {H_nmk:>8.3f} {N_va:>6} {H_va:>8.3f} {d_str}")

# ---- 3. Mahogni-dominans over tid ----
print("\n" + "=" * 90)
print("MAHOGNI-DOMINANS (% av alle materialfoerekomstar)")
print("=" * 90)
print(f"{'Hundreaar':<15} {'Samla %':>10} {'NMK %':>10} {'V&A %':>10} {'NMK n':>8} {'V&A n':>8}")
print("-" * 60)
for c in sorted_centuries:
    all_mats = century_materials_all[c]
    nmk_mats = century_materials_nmk.get(c, [])
    va_mats = century_materials_va.get(c, [])

    all_mahogni = sum(1 for m in all_mats if m == "Mahogni")
    nmk_mahogni = sum(1 for m in nmk_mats if m == "Mahogni")
    va_mahogni = sum(1 for m in va_mats if m == "Mahogni")

    all_pct = 100 * all_mahogni / len(all_mats) if all_mats else 0
    nmk_pct = 100 * nmk_mahogni / len(nmk_mats) if nmk_mats else 0
    va_pct = 100 * va_mahogni / len(va_mats) if va_mats else 0

    print(f"{c:<15} {all_pct:>9.1f}% {nmk_pct:>9.1f}% {va_pct:>9.1f}% {nmk_mahogni:>8} {va_mahogni:>8}")

# ---- 4. Materiell dobbeltheit: berande vs. fasade ----
print("\n" + "=" * 90)
print("MATERIELL DOBBELTHEIT: stolar med baade lokalt tre OG importert materiale")
print("=" * 90)
local_woods = {"Bjork", "Bjørk", "Furu", "Eik", "Ask", "Or", "Alm", "Gran", "Bok", "Bøk", "Osp", "Lind"}
imported = {"Mahogni", "Palisander", "Ibenholt", "Rotting", "Teak", "Bambus", "Silke", "Floeyel", "Fløyel"}

for c in sorted_centuries:
    items = [p for p in parsed if p["century"] == c]
    n_double = 0
    for item in items:
        mats_set = set(item["materials"])
        has_local = bool(mats_set & local_woods)
        has_imported = bool(mats_set & imported)
        if has_local and has_imported:
            n_double += 1
    pct = 100 * n_double / len(items) if items else 0
    print(f"{c:<15} {n_double:>5} av {len(items):>5}  ({pct:5.1f}%)")

# ---- 5. Topp 10 materialar samla med rangering per hundreaar ----
print("\n" + "=" * 90)
print("TOPP 10 MATERIALAR OVER HEILE PERIODEN")
print("=" * 90)
all_materials = []
for c in sorted_centuries:
    all_materials.extend(century_materials_all[c])
top10 = Counter(all_materials).most_common(10)
for mat, count in top10:
    pct = 100 * count / len(all_materials)
    print(f"  {mat:<25} {count:>6}  ({pct:5.1f}%)")

# ---- 6. Rullande 50-aars entropi ----
print("\n" + "=" * 90)
print("RULLANDE 50-AARS ENTROPI (for aa identifisere utforsking/utnytting)")
print("=" * 90)

# Grupper etter 50-aarsbolkar
period_materials = defaultdict(list)
for p in parsed:
    try:
        year = int(p["year"])
        if year < 100:
            continue
        period = (year // 50) * 50
        period_materials[period].extend(p["materials"])
    except (ValueError, KeyError):
        continue

for period in sorted(period_materials.keys()):
    mats = period_materials[period]
    if len(mats) < 5:
        continue
    H, Hm, J, S, tot, _ = compute_entropy_bits(mats)
    bar = "#" * int(H * 5)
    print(f"  {period}-{period+49}  N_forek={tot:>5}  S={S:>3}  H'={H:>6.3f} bits  {bar}")

# ---- 7. Spesifikke stoler for narrative ----
print("\n" + "=" * 90)
print("NARRATIVE STOLAR: tidlege + noekkeldoeme")
print("=" * 90)

# Garastolen
for p in parsed:
    if "Garastolen" in p.get("name", "") or "Gårastolen" in p.get("name", ""):
        print(f"  GARASTOLEN: {p}")

# Tidlegaste stolar med rike materialar
rich = [(p, len(p["materials"])) for p in parsed if p.get("year","").isdigit() and int(p["year"]) < 1700 and len(p["materials"]) >= 4]
rich.sort(key=lambda x: int(x[0]["year"]))
print("\nTidlege stolar med >= 4 materialar:")
for p, n in rich[:10]:
    print(f"  {p['year']}  {p['name'][:45]:<45}  ({n} mat.)  {', '.join(p['materials'][:6])}")

# Mest materielt komplekse stolar nokosinne
all_parsed_rich = sorted(parsed, key=lambda p: len(p["materials"]), reverse=True)
print("\nMest komplekse stolar (flest materialar):")
for p in all_parsed_rich[:8]:
    print(f"  {p.get('year','?'):>6}  {p['name'][:45]:<45}  ({len(p['materials'])} mat.)  {', '.join(p['materials'][:6])}")

# ---- 8. Jaccard-avstand NMK vs V&A per hundreaar ----
print("\n" + "=" * 90)
print("JACCARD-AVSTAND MELLOM NMK OG V&A MATERIALPALETTAR")
print("=" * 90)
for c in sorted_centuries:
    nmk_set = set(century_materials_nmk.get(c, []))
    va_set = set(century_materials_va.get(c, []))
    if nmk_set and va_set:
        intersection = nmk_set & va_set
        union = nmk_set | va_set
        jaccard = 1 - len(intersection) / len(union) if union else 0
        print(f"  {c:<15} Jaccard-avstand: {jaccard:.3f}  (NMK: {len(nmk_set)} mat, V&A: {len(va_set)} mat, felles: {len(intersection)})")
