"""
Artikkel II: Produksjonsgeografi.
Analyse av dimensjonar, omsluttande volum, konvergens over tid.
NMK vs V&A, Jaccard, CV-trendar.
"""
import csv
import math
from collections import defaultdict
import statistics

CSV_PATH = "../stolar_db.csv"

rows = []
with open(CSV_PATH, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

def get_museum(row):
    nm_url = row.get("Nasjonalmuseet", "").strip()
    obj_id = row.get("Objekt-ID", "").strip()
    if "nasjonalmuseet.no" in nm_url or obj_id.startswith("OK-") or obj_id.startswith("NMK"):
        return "NMK"
    return "V&A"

def safe_float(val):
    try:
        v = float(val.replace(",", "."))
        return v if v > 0 else None
    except (ValueError, AttributeError):
        return None

# Parse dimensjonar
parsed = []
for row in rows:
    century = row.get("Hundreaar", row.get("Hundreår", "")).strip()
    if not century:
        continue
    h = safe_float(row.get("Hoegde (cm)", row.get("Høgde (cm)", "")))
    w = safe_float(row.get("Breidde (cm)", ""))
    d = safe_float(row.get("Djupn (cm)", ""))
    sh = safe_float(row.get("Setehogde (cm)", row.get("Setehøgde (cm)", "")))
    weight = safe_float(row.get("Estimert vekt (kg)", ""))
    museum = get_museum(row)
    namn = row.get("Namn", "ukjend")
    year_str = row.get("Fraa aar", row.get("Frå år", "")).strip()
    try:
        year = int(year_str) if year_str and year_str != "0" else None
    except ValueError:
        year = None
    stil = row.get("Stilperiode", "").strip()
    nasjonalitet = row.get("Nasjonalitet", "").strip()

    parsed.append({
        "century": century,
        "h": h, "w": w, "d": d, "sh": sh, "weight": weight,
        "museum": museum, "name": namn, "year": year,
        "style": stil, "nationality": nasjonalitet,
    })

def century_sort(c):
    try: return int(c.split("-")[0])
    except: return 9999

centuries = sorted(set(p["century"] for p in parsed), key=century_sort)

# ---- 1. Dimensjonsstatistikk per hundreaar ----
print("=" * 100)
print("DIMENSJONSSTATISTIKK PER HUNDREAAR")
print("=" * 100)
print(f"{'Hundreaar':<15} {'N_h':>5} {'Mean_H':>8} {'SD_H':>8} {'CV_H':>8} {'Mean_W':>8} {'SD_W':>8} {'CV_W':>8} {'Mean_D':>8}")
print("-" * 90)

for c in centuries:
    items = [p for p in parsed if p["century"] == c]
    hs = [p["h"] for p in items if p["h"]]
    ws = [p["w"] for p in items if p["w"]]
    ds = [p["d"] for p in items if p["d"]]

    if len(hs) > 1:
        mh = statistics.mean(hs)
        sdh = statistics.stdev(hs)
        cvh = sdh / mh if mh > 0 else 0
    else:
        mh = hs[0] if hs else 0
        sdh = cvh = 0

    if len(ws) > 1:
        mw = statistics.mean(ws)
        sdw = statistics.stdev(ws)
        cvw = sdw / mw if mw > 0 else 0
    else:
        mw = ws[0] if ws else 0
        sdw = cvw = 0

    md = statistics.mean(ds) if ds else 0

    print(f"{c:<15} {len(hs):>5} {mh:>8.1f} {sdh:>8.1f} {cvh:>8.3f} {mw:>8.1f} {sdw:>8.1f} {cvw:>8.3f} {md:>8.1f}")

# ---- 2. Omsluttande volum per hundreaar ----
print("\n" + "=" * 100)
print("OMSLUTTANDE VOLUM (H x W x D) PER HUNDREAAR")
print("=" * 100)
print(f"{'Hundreaar':<15} {'N':>5} {'Mean_V':>10} {'Median_V':>10} {'SD_V':>10} {'CV_V':>8} {'Min_V':>10} {'Max_V':>10} {'Ratio':>8}")
print("-" * 85)

for c in centuries:
    items = [p for p in parsed if p["century"] == c]
    vols = []
    for p in items:
        if p["h"] and p["w"] and p["d"]:
            v = p["h"] * p["w"] * p["d"]
            vols.append(v)

    if len(vols) > 1:
        mv = statistics.mean(vols)
        medv = statistics.median(vols)
        sdv = statistics.stdev(vols)
        cvv = sdv / mv if mv > 0 else 0
        minv = min(vols)
        maxv = max(vols)
        ratio = maxv / minv if minv > 0 else 0
        print(f"{c:<15} {len(vols):>5} {mv:>10.0f} {medv:>10.0f} {sdv:>10.0f} {cvv:>8.3f} {minv:>10.0f} {maxv:>10.0f} {ratio:>8.1f}")
    elif vols:
        print(f"{c:<15} {len(vols):>5} {vols[0]:>10.0f}")

# ---- 3. H/W-ratio per hundreaar (proporsjonsdrift) ----
print("\n" + "=" * 100)
print("PROPORSJONSDRIFT: H/W-RATIO PER HUNDREAAR")
print("=" * 100)
print(f"{'Hundreaar':<15} {'N':>5} {'Mean_HW':>10} {'Median_HW':>10} {'SD_HW':>10}")
phi = (1 + math.sqrt(5)) / 2
print(f"  (Gullsnitt phi = {phi:.3f})")
print("-" * 50)

for c in centuries:
    items = [p for p in parsed if p["century"] == c]
    ratios = []
    for p in items:
        if p["h"] and p["w"] and p["w"] > 0:
            ratios.append(p["h"] / p["w"])
    if len(ratios) > 1:
        mr = statistics.mean(ratios)
        medr = statistics.median(ratios)
        sdr = statistics.stdev(ratios)
        print(f"{c:<15} {len(ratios):>5} {mr:>10.3f} {medr:>10.3f} {sdr:>10.3f}")

# ---- 4. NMK vs V&A dimensjonar ----
print("\n" + "=" * 100)
print("NMK vs V&A: GJENNOMSNITTLEG HOGDE")
print("=" * 100)
print(f"{'Hundreaar':<15} {'N_NMK':>6} {'H_NMK':>8} {'N_VA':>6} {'H_VA':>8} {'Delta':>8}")
print("-" * 55)

for c in centuries:
    nmk_h = [p["h"] for p in parsed if p["century"] == c and p["museum"] == "NMK" and p["h"]]
    va_h = [p["h"] for p in parsed if p["century"] == c and p["museum"] == "V&A" and p["h"]]
    if nmk_h and va_h:
        mnh = statistics.mean(nmk_h)
        mvh = statistics.mean(va_h)
        print(f"{c:<15} {len(nmk_h):>6} {mnh:>8.1f} {len(va_h):>6} {mvh:>8.1f} {mnh-mvh:>8.1f}")

# ---- 5. Konvergens-analyse: CV over tid for 50-aarsbolkar ----
print("\n" + "=" * 100)
print("RULLANDE CV FOR HOGDE (50-AARSBOLKAR)")
print("=" * 100)
period_h = defaultdict(list)
for p in parsed:
    if p["year"] and p["h"] and p["year"] > 100:
        period = (p["year"] // 50) * 50
        period_h[period].append(p["h"])

for period in sorted(period_h.keys()):
    hs = period_h[period]
    if len(hs) > 2:
        m = statistics.mean(hs)
        sd = statistics.stdev(hs)
        cv = sd / m if m > 0 else 0
        bar = "#" * int(cv * 100)
        print(f"  {period}-{period+49}  N={len(hs):>4}  Mean={m:>6.1f}  SD={sd:>5.1f}  CV={cv:.3f}  {bar}")

# ---- 6. Vektanalyse per hundreaar ----
print("\n" + "=" * 100)
print("ESTIMERT VEKT PER HUNDREAAR")
print("=" * 100)
for c in centuries:
    ws = [p["weight"] for p in parsed if p["century"] == c and p["weight"]]
    if len(ws) > 1:
        mw = statistics.mean(ws)
        medw = statistics.median(ws)
        sdw = statistics.stdev(ws)
        print(f"  {c:<15} N={len(ws):>4}  Mean={mw:>6.1f} kg  Median={medw:>6.1f} kg  SD={sdw:>5.1f}")

# ---- 7. Stilperiode-fordeling ----
print("\n" + "=" * 100)
print("STILPERIODAR (stolar med stilmerke)")
print("=" * 100)
from collections import Counter
styles = [p["style"] for p in parsed if p["style"]]
print(f"Stolar med stilmerke: {len(styles)} av {len(parsed)} ({100*len(styles)/len(parsed):.1f}%)")
top_styles = Counter(styles).most_common(15)
for s, n in top_styles:
    print(f"  {s:<30} {n:>5}")

# ---- 8. Nasjonalitetsfordeling ----
print("\n" + "=" * 100)
print("NASJONALITETSFORDELING")
print("=" * 100)
nats = [p["nationality"] for p in parsed if p["nationality"]]
print(f"Stolar med nasjonalitet: {len(nats)} av {len(parsed)} ({100*len(nats)/len(parsed):.1f}%)")
top_nats = Counter(nats).most_common(15)
for n, count in top_nats:
    print(f"  {n:<30} {count:>5}  ({100*count/len(nats):.1f}%)")

# ---- 9. Modulor-avvik ----
print("\n" + "=" * 100)
print("MODULOR-AVVIK (Le Corbusier sin prediksjon: H=113 cm)")
print("=" * 100)
MODULOR_H = 113
for c in centuries:
    hs = [p["h"] for p in parsed if p["century"] == c and p["h"]]
    if hs:
        m = statistics.mean(hs)
        med = statistics.median(hs)
        print(f"  {c:<15} Mean={m:>6.1f}  Avvik={m-MODULOR_H:>+7.1f} cm  Median={med:>6.1f}")

# ---- 10. Dimensjonsekstrem ----
print("\n" + "=" * 100)
print("DIMENSJONSEKSTREMA")
print("=" * 100)
with_vol = [(p, p["h"]*p["w"]*p["d"]) for p in parsed if p["h"] and p["w"] and p["d"]]
with_vol.sort(key=lambda x: x[1])
print("Minste volum:")
for p, v in with_vol[:5]:
    print(f"  {v:>10.0f} cm3  {p['name'][:40]:<40}  {p.get('year','?')}  {p['museum']}")
print("Storste volum:")
for p, v in with_vol[-5:]:
    print(f"  {v:>10.0f} cm3  {p['name'][:40]:<40}  {p.get('year','?')}  {p['museum']}")
if with_vol:
    ratio = with_vol[-1][1] / with_vol[0][1] if with_vol[0][1] > 0 else 0
    print(f"\nVolumratio max/min: {ratio:.0f}x")
