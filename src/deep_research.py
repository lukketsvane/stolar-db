"""
Djup research for Art II-IV.
Chi2, Cohen's d, PCA, stilmigrasjon, Mahalanobis drift,
materiale->dimensjon korrelasjon, formvariasjon under konstant funksjon.
"""
import csv, math, os
from collections import Counter, defaultdict
import statistics
import numpy as np
from scipy import stats as sp_stats

CSV_PATH = "../stolar_db.csv"

rows = []
with open(CSV_PATH, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f): rows.append(row)

def sf(val):
    try:
        v = float(val.replace(",","."))
        return v if v > 0 else None
    except: return None

def museum(r):
    if "nasjonalmuseet.no" in r.get("Nasjonalmuseet","") or r.get("Objekt-ID","").startswith(("OK-","NMK")):
        return "NMK"
    return "V&A"

for r in rows:
    r["_m"] = museum(r)
    r["_mats"] = [m.strip() for m in r.get("Materialar","").split(",") if m.strip()]
    r["_c"] = r.get("Hundreår","").strip()
    r["_h"] = sf(r.get("Høgde (cm)",""))
    r["_w"] = sf(r.get("Breidde (cm)",""))
    r["_d"] = sf(r.get("Djupn (cm)",""))
    r["_sh"] = sf(r.get("Setehøgde (cm)",""))
    r["_wt"] = sf(r.get("Estimert vekt (kg)",""))
    r["_style"] = r.get("Stilperiode","").strip()
    r["_nat"] = r.get("Nasjonalitet","").strip()
    try: r["_year"] = int(r.get("Frå år","").strip())
    except: r["_year"] = None

# ==================================================================
# 1. FORMVARIASJON UNDER KONSTANT FUNKSJON
# ==================================================================
print("=" * 80)
print("1. FORMVARIASJON UNDER KONSTANT FUNKSJON")
print("=" * 80)
hs = [r["_h"] for r in rows if r["_h"]]
ws = [r["_w"] for r in rows if r["_w"]]
ds = [r["_d"] for r in rows if r["_d"]]
wts = [r["_wt"] for r in rows if r["_wt"]]

for name, vals in [("Hogde", hs), ("Breidde", ws), ("Djupn", ds), ("Vekt", wts)]:
    mn, mx = min(vals), max(vals)
    ratio = mx/mn if mn > 0 else 0
    cv = statistics.stdev(vals)/statistics.mean(vals)
    print(f"  {name:<10} N={len(vals):>5}  Min={mn:>7.1f}  Max={mx:>7.1f}  "
          f"Ratio={ratio:>7.1f}x  CV={cv:.3f}  Mean={statistics.mean(vals):.1f}  Median={statistics.median(vals):.1f}")

# Volum
vols = [r["_h"]*r["_w"]*r["_d"] for r in rows if r["_h"] and r["_w"] and r["_d"]
        and r["_h"]*r["_w"]*r["_d"] < 5000000]  # Filter outliers
print(f"\n  Volum (filtrert) N={len(vols)}  Min={min(vols):.0f}  Max={max(vols):.0f}  "
      f"Ratio={max(vols)/min(vols):.0f}x  CV={statistics.stdev(vols)/statistics.mean(vols):.3f}")

# ==================================================================
# 2. COHEN'S d: MATERIAL -> DIMENSJON
# ==================================================================
print("\n" + "=" * 80)
print("2. COHEN'S d: MATERIAL -> DIMENSJON (hogde)")
print("=" * 80)

mat_heights = defaultdict(list)
for r in rows:
    if r["_h"]:
        for m in r["_mats"]:
            mat_heights[m].append(r["_h"])

# Top materials by frequency
top_mats = [m for m, _ in Counter(m for r in rows for m in r["_mats"]).most_common(15)]

print(f"\n  {'Mat A':<15} {'Mat B':<15} {'N_A':>5} {'N_B':>5} {'Mean_A':>8} {'Mean_B':>8} {'d':>8}")
print("  " + "-" * 75)
pairs_done = set()
for i, a in enumerate(top_mats):
    for j, b in enumerate(top_mats):
        if i >= j: continue
        if (a,b) in pairs_done: continue
        pairs_done.add((a,b))
        ha = mat_heights[a]
        hb = mat_heights[b]
        if len(ha) < 20 or len(hb) < 20: continue
        ma, mb = statistics.mean(ha), statistics.mean(hb)
        sa, sb = statistics.stdev(ha), statistics.stdev(hb)
        pooled = math.sqrt((sa**2 + sb**2)/2)
        d = abs(ma - mb) / pooled if pooled > 0 else 0
        if d > 0.3:
            print(f"  {a:<15} {b:<15} {len(ha):>5} {len(hb):>5} {ma:>8.1f} {mb:>8.1f} {d:>8.3f}")

# H/W ratio per material
print("\n  H/W-ratio per materiale:")
mat_hw = defaultdict(list)
for r in rows:
    if r["_h"] and r["_w"] and r["_w"] > 0:
        for m in r["_mats"]:
            mat_hw[m].append(r["_h"]/r["_w"])

for m in ["Stål", "Kryssfiner", "Plast", "Mahogni", "Eik", "Furu", "Bøk", "Bjørk"]:
    if mat_hw[m] and len(mat_hw[m]) > 10:
        print(f"    {m:<15} N={len(mat_hw[m]):>4}  Mean H/W = {statistics.mean(mat_hw[m]):.3f}  "
              f"Median = {statistics.median(mat_hw[m]):.3f}")

# ==================================================================
# 3. STILMIGRASJON: nasjonalitet per stilperiode
# ==================================================================
print("\n" + "=" * 80)
print("3. STILMIGRASJON: nasjonalitet per stil")
print("=" * 80)

style_nat = defaultdict(lambda: Counter())
for r in rows:
    if r["_style"] and r["_nat"]:
        style_nat[r["_style"]][r["_nat"]] += 1

styles_enough = {s for s, c in style_nat.items() if sum(c.values()) >= 10}
for s in sorted(styles_enough, key=lambda x: sum(style_nat[x].values()), reverse=True):
    c = style_nat[s]
    total = sum(c.values())
    top2 = c.most_common(2)
    dom = top2[0]
    dom_pct = 100*dom[1]/total
    print(f"  {s:<25} N={total:>4}  Dominant: {dom[0]:<15} ({dom_pct:.0f}%)  "
          f"{'RETINERT' if dom_pct > 70 else 'MIGRERT' if dom_pct < 50 else 'DELT'}")

# ==================================================================
# 4. DIMENSJONELL DRIFT: Mahalanobis mellom hundreaar
# ==================================================================
print("\n" + "=" * 80)
print("4. DIMENSJONELL DRIFT (forenkla Mahalanobis)")
print("=" * 80)

def cs(c):
    try: return int(c.split("-")[0])
    except: return 9999

main_c = sorted([c for c in set(r["_c"] for r in rows if r["_c"])
                  if c not in ("1200-talet","1300-talet","1400-talet")], key=cs)

century_dims = {}
for c in main_c:
    items = [r for r in rows if r["_c"]==c and r["_h"] and r["_w"] and r["_d"]]
    if len(items) > 10:
        century_dims[c] = {
            "h_mean": statistics.mean([r["_h"] for r in items]),
            "w_mean": statistics.mean([r["_w"] for r in items]),
            "d_mean": statistics.mean([r["_d"] for r in items]),
            "h_sd": statistics.stdev([r["_h"] for r in items]),
            "w_sd": statistics.stdev([r["_w"] for r in items]),
            "n": len(items),
        }

prev_c = None
for c in main_c:
    if c not in century_dims: continue
    if prev_c and prev_c in century_dims:
        a, b = century_dims[prev_c], century_dims[c]
        # Simplified: Euclidean distance in SD units
        dh = (b["h_mean"] - a["h_mean"]) / ((a["h_sd"] + b["h_sd"])/2) if a["h_sd"]+b["h_sd"] > 0 else 0
        dw = (b["w_mean"] - a["w_mean"]) / ((a["w_sd"] + b["w_sd"])/2) if a["w_sd"]+b["w_sd"] > 0 else 0
        dd = (b["d_mean"] - a["d_mean"]) / ((a["h_sd"] + b["h_sd"])/2) if a["h_sd"]+b["h_sd"] > 0 else 0
        dist = math.sqrt(dh**2 + dw**2 + dd**2)
        print(f"  {prev_c} -> {c}:  drift = {dist:.3f} SD  "
              f"(dH={dh:+.2f}, dW={dw:+.2f}, dD={dd:+.2f})")
    prev_c = c

# ==================================================================
# 5. CHI2: MATERIAL x NASJONALITET
# ==================================================================
print("\n" + "=" * 80)
print("5. CHI2: MATERIAL x NASJONALITET")
print("=" * 80)

top_nats = ["Storbritannia", "Noreg", "Frankrike", "Italia", "Danmark", "Tyskland"]
top_mats_chi = ["Mahogni", "Eik", "Bøk", "Furu", "Stål", "Kryssfiner", "Nøttetre",
                "Bjørk", "Lær", "Tekstil"]

contingency = []
for nat in top_nats:
    row_data = []
    nat_rows = [r for r in rows if r["_nat"] == nat]
    for mat in top_mats_chi:
        count = sum(1 for r in nat_rows if mat in r["_mats"])
        row_data.append(count)
    contingency.append(row_data)

ct = np.array(contingency)
chi2, p, dof, expected = sp_stats.chi2_contingency(ct)
print(f"  Chi2 = {chi2:.1f}, df = {dof}, p = {p:.2e}")
print(f"\n  Observert vs forventa (residualar):")
residuals = (ct - expected) / np.sqrt(expected)
print(f"  {'':>15}", end="")
for m in top_mats_chi: print(f"  {m[:6]:>7}", end="")
print()
for i, nat in enumerate(top_nats):
    print(f"  {nat:>15}", end="")
    for j in range(len(top_mats_chi)):
        r = residuals[i][j]
        marker = "***" if abs(r) > 3 else "**" if abs(r) > 2 else "*" if abs(r) > 1.5 else ""
        print(f"  {r:>+5.1f}{marker:>2}", end="")
    print()

# ==================================================================
# 6. SPESIFIKKE STOLAR FOR NARRATIV
# ==================================================================
print("\n" + "=" * 80)
print("6. NARRATIVT INTERESSANTE STOLAR")
print("=" * 80)

# Lettaste og tyngste
with_wt = [(r, r["_wt"]) for r in rows if r["_wt"]]
with_wt.sort(key=lambda x: x[1])
print("\nLettaste stolar:")
for r, w in with_wt[:5]:
    print(f"  {w:>6.1f} kg  {r.get('Namn','?')[:40]:<40}  {r['_year'] or '?'}  {', '.join(r['_mats'][:4])}")
print("Tyngste stolar:")
for r, w in with_wt[-5:]:
    print(f"  {w:>6.1f} kg  {r.get('Namn','?')[:40]:<40}  {r['_year'] or '?'}  {', '.join(r['_mats'][:4])}")

# Hogaste og lagaste
with_h = [(r, r["_h"]) for r in rows if r["_h"] and r["_h"] > 20 and r["_h"] < 200]
with_h.sort(key=lambda x: x[1])
print("\nLagaste stolar:")
for r, h in with_h[:5]:
    print(f"  {h:>6.1f} cm  {r.get('Namn','?')[:40]:<40}  {r['_year'] or '?'}  {', '.join(r['_mats'][:4])}")
print("Hogaste stolar:")
for r, h in with_h[-5:]:
    print(f"  {h:>6.1f} cm  {r.get('Namn','?')[:40]:<40}  {r['_year'] or '?'}  {', '.join(r['_mats'][:4])}")

# ==================================================================
# 7. TEKNIKK-EVOLUSJON: kva teknikkar forsvinn og dukkar opp
# ==================================================================
print("\n" + "=" * 80)
print("7. TEKNIKK-EVOLUSJON")
print("=" * 80)

century_techs = defaultdict(Counter)
for r in rows:
    if r["_c"]:
        ts = [t.strip() for t in r.get("Teknikk","").split(",") if t.strip()]
        century_techs[r["_c"]].update(ts)

main_techs = ["Polstring", "Tapping", "Skjæring", "Dreiing", "Formbøying",
              "Laminering", "Sveising", "Skruing", "Sprøytestøyping"]

print(f"\n  {'Teknikk':<20}", end="")
for c in main_c: print(f"  {c[:4]:>5}", end="")
print()
for t in main_techs:
    print(f"  {t:<20}", end="")
    for c in main_c:
        n = century_techs[c].get(t, 0)
        total = sum(century_techs[c].values()) or 1
        pct = 100*n/total
        if pct > 0:
            print(f"  {pct:>4.0f}%", end="")
        else:
            print(f"     -", end="")
    print()

# ==================================================================
# 8. VEKT PER MATERIALE
# ==================================================================
print("\n" + "=" * 80)
print("8. VEKT PER HOVUDMATERIALE")
print("=" * 80)

mat_wt = defaultdict(list)
for r in rows:
    if r["_wt"]:
        for m in r["_mats"]:
            mat_wt[m].append(r["_wt"])

for m in ["Stål", "Kryssfiner", "Plast", "Mahogni", "Eik", "Furu", "Bøk", "Bjørk", "Nøttetre"]:
    if mat_wt[m] and len(mat_wt[m]) > 3:
        print(f"  {m:<15} N={len(mat_wt[m]):>3}  Mean={statistics.mean(mat_wt[m]):>6.1f} kg  "
              f"Median={statistics.median(mat_wt[m]):>6.1f} kg")
