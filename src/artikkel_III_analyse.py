"""
Artikkel III: Form og tid.
Random Forest-klassifikasjon av stilperiode og nasjonalitet.
Fellesinformasjon (MI) mellom variablar.
"""
import csv
import math
from collections import Counter, defaultdict
import statistics

CSV_PATH = "../stolar_db.csv"

rows = []
with open(CSV_PATH, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

def safe_float(val):
    try:
        v = float(val.replace(",", "."))
        return v if v > 0 else None
    except (ValueError, AttributeError):
        return None

def get_museum(row):
    nm_url = row.get("Nasjonalmuseet", "").strip()
    obj_id = row.get("Objekt-ID", "").strip()
    if "nasjonalmuseet.no" in nm_url or obj_id.startswith("OK-") or obj_id.startswith("NMK"):
        return "NMK"
    return "V&A"

# Parse
parsed = []
for row in rows:
    century = row.get("Hundreår", "").strip()
    h = safe_float(row.get("Høgde (cm)", ""))
    w = safe_float(row.get("Breidde (cm)", ""))
    d = safe_float(row.get("Djupn (cm)", ""))
    sh = safe_float(row.get("Setehøgde (cm)", ""))
    materials_raw = row.get("Materialar", "").strip()
    stil = row.get("Stilperiode", "").strip()
    nasjonalitet = row.get("Nasjonalitet", "").strip()
    teknikk_raw = row.get("Teknikk", "").strip()
    museum = get_museum(row)
    year_str = row.get("Frå år", "").strip()
    try:
        year = int(year_str) if year_str and year_str != "0" else None
    except ValueError:
        year = None

    mats = [m.strip() for m in materials_raw.split(",") if m.strip()] if materials_raw else []
    teknikkar = [t.strip() for t in teknikk_raw.split(",") if t.strip()] if teknikk_raw else []

    parsed.append({
        "century": century, "h": h, "w": w, "d": d, "sh": sh,
        "materials": mats, "style": stil, "nationality": nasjonalitet,
        "techniques": teknikkar, "museum": museum, "year": year,
    })

# ---- 1. Teknikk-analyse per hundreaar ----
print("=" * 90)
print("TEKNIKKAR PER HUNDREAAR")
print("=" * 90)

def century_sort(c):
    try: return int(c.split("-")[0])
    except: return 9999

centuries = sorted(set(p["century"] for p in parsed if p["century"]), key=century_sort)

all_techs = Counter()
century_techs = defaultdict(list)
for p in parsed:
    if p["century"] and p["techniques"]:
        century_techs[p["century"]].extend(p["techniques"])
        all_techs.update(p["techniques"])

print("\nTopp 15 teknikkar samla:")
for t, n in all_techs.most_common(15):
    print(f"  {t:<30} {n:>5}")

print(f"\n{'Hundreaar':<15} {'N':>5}  Topp 3 teknikkar")
print("-" * 70)
for c in centuries:
    ts = century_techs.get(c, [])
    if ts:
        top3 = Counter(ts).most_common(3)
        top_str = ", ".join(f"{t} ({n})" for t, n in top3)
        print(f"{c:<15} {len(ts):>5}  {top_str}")

# ---- 2. Shannon-entropi for TEKNIKKAR per hundreaar ----
print("\n" + "=" * 90)
print("SHANNON-ENTROPI FOR TEKNIKKAR (bits)")
print("=" * 90)
print(f"{'Hundreaar':<15} {'N':>5} {'S':>4} {'H (bits)':>10} {'J':>8}")
print("-" * 45)
for c in centuries:
    ts = century_techs.get(c, [])
    if len(ts) < 2:
        continue
    counts = Counter(ts)
    total = sum(counts.values())
    S = len(counts)
    H = -sum((n/total) * math.log2(n/total) for n in counts.values() if n > 0)
    Hmax = math.log2(S) if S > 1 else 0
    J = H / Hmax if Hmax > 0 else 0
    print(f"{c:<15} {total:>5} {S:>4} {H:>10.3f} {J:>8.4f}")

# ---- 3. Nye teknikkar per hundreaar ----
print("\n" + "=" * 90)
print("NYE TEKNIKKAR PER HUNDREAAR")
print("=" * 90)
seen_tech = set()
for c in centuries:
    ts = set(century_techs.get(c, []))
    new = ts - seen_tech
    if new:
        print(f"{c}: +{len(new)} nye: {', '.join(sorted(new))}")
    seen_tech.update(ts)

# ---- 4. Material-teknikk korrelasjon ----
print("\n" + "=" * 90)
print("MATERIAL-TEKNIKK KORRELASJON (topp 15 par)")
print("=" * 90)
mat_tech_pairs = Counter()
for p in parsed:
    for m in p["materials"]:
        for t in p["techniques"]:
            mat_tech_pairs[(m, t)] += 1

for (m, t), n in mat_tech_pairs.most_common(15):
    print(f"  {m:<20} + {t:<20} = {n:>5}")

# ---- 5. Teknikk-mangfald per stol over tid ----
print("\n" + "=" * 90)
print("GJENNOMSNITTLEG ANTAL TEKNIKKAR PER STOL")
print("=" * 90)
for c in centuries:
    items = [p for p in parsed if p["century"] == c and p["techniques"]]
    if items:
        mean_n = statistics.mean(len(p["techniques"]) for p in items)
        print(f"  {c:<15} N={len(items):>4}  Mean teknikkar/stol: {mean_n:.2f}")

# ---- 6. Dimensjonar per stilperiode ----
print("\n" + "=" * 90)
print("DIMENSJONAR PER STILPERIODE (sortert etter gj.sn. hogde)")
print("=" * 90)
style_dims = defaultdict(list)
for p in parsed:
    if p["style"] and p["h"]:
        style_dims[p["style"]].append(p)

style_stats = []
for style, items in style_dims.items():
    hs = [p["h"] for p in items]
    ws = [p["w"] for p in items if p["w"]]
    if len(hs) >= 5:
        style_stats.append((style, len(hs), statistics.mean(hs), statistics.stdev(hs),
                           statistics.mean(ws) if ws else 0))

style_stats.sort(key=lambda x: x[2], reverse=True)
print(f"{'Stil':<25} {'N':>5} {'Mean H':>8} {'SD H':>8} {'Mean W':>8}")
print("-" * 60)
for s, n, mh, sdh, mw in style_stats:
    print(f"{s:<25} {n:>5} {mh:>8.1f} {sdh:>8.1f} {mw:>8.1f}")

# ---- 7. Dimensjonar per nasjonalitet ----
print("\n" + "=" * 90)
print("DIMENSJONAR PER NASJONALITET (sortert etter gj.sn. hogde)")
print("=" * 90)
nat_dims = defaultdict(list)
for p in parsed:
    if p["nationality"] and p["h"]:
        nat_dims[p["nationality"]].append(p)

nat_stats = []
for nat, items in nat_dims.items():
    hs = [p["h"] for p in items]
    ws = [p["w"] for p in items if p["w"]]
    if len(hs) >= 10:
        nat_stats.append((nat, len(hs), statistics.mean(hs), statistics.stdev(hs),
                         statistics.mean(ws) if ws else 0))

nat_stats.sort(key=lambda x: x[2], reverse=True)
print(f"{'Nasjonalitet':<25} {'N':>5} {'Mean H':>8} {'SD H':>8} {'Mean W':>8}")
print("-" * 60)
for s, n, mh, sdh, mw in nat_stats:
    print(f"{s:<25} {n:>5} {mh:>8.1f} {sdh:>8.1f} {mw:>8.1f}")

# ---- 8. Fellesinformasjon (simplified) ----
print("\n" + "=" * 90)
print("FORENKLING: Dimensjonsskilnader mellom stilgrupper (Cohen's d)")
print("=" * 90)
# Ta dei to mest frekvente stilperiodane og rekn Cohen's d for hogde
if len(style_stats) >= 2:
    for i in range(min(5, len(style_stats))):
        for j in range(i+1, min(5, len(style_stats))):
            s1, n1, m1, sd1, _ = style_stats[i]
            s2, n2, m2, sd2, _ = style_stats[j]
            pooled_sd = math.sqrt((sd1**2 + sd2**2) / 2) if sd1 > 0 and sd2 > 0 else 1
            d = abs(m1 - m2) / pooled_sd
            print(f"  {s1:<20} vs {s2:<20}  d = {d:.3f}  (dH = {abs(m1-m2):.1f} cm)")
