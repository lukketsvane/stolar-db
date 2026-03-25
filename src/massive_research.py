#!/usr/bin/env python3
"""
STOLAR Comprehensive Research Analysis
=======================================
Analyser for the STOLAR chair database: material complexity, mahogni deep dive,
style migration, specific chair narratives, weight analysis, technique deep dive,
proportion deep dive, and the post-mahogni era at NMK.

Author: STOLAR research team
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
from collections import Counter
from itertools import combinations

# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
CSV_PATH = "C:/Users/Shadow/Documents/GitHub/stolar-db/stolar_db.csv"
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

print("=" * 80)
print("  STOLAR MASSIVE RESEARCH ANALYSIS")
print(f"  Dataset: {len(df)} chairs, {len(df.columns)} columns")
print("=" * 80)

# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def parse_list_field(series):
    """Split comma-separated field into list of stripped strings."""
    return series.dropna().apply(lambda x: [s.strip() for s in str(x).split(",") if s.strip()])


def assign_25yr_period(year):
    """Assign a year to a 25-year period label."""
    if pd.isna(year):
        return None
    y = int(year)
    start = (y // 25) * 25
    return f"{start}-{start + 24}"


def assign_decade(year):
    """Assign a year to a decade label."""
    if pd.isna(year):
        return None
    y = int(year)
    start = (y // 10) * 10
    return f"{start}-{start + 9}"


def assign_50yr_period(year):
    """Assign a year to a 50-year period label."""
    if pd.isna(year):
        return None
    y = int(year)
    start = (y // 50) * 50
    return f"{start}-{start + 49}"


def section_header(title, level=1):
    """Print formatted section header."""
    if level == 1:
        print("\n" + "█" * 80)
        print(f"  {title}")
        print("█" * 80)
    elif level == 2:
        print(f"\n{'─' * 60}")
        print(f"  {title}")
        print("─" * 60)
    else:
        print(f"\n  ▸ {title}")


# Precompute material and technique lists
df["mat_list"] = parse_list_field(df["Materialar"])
df["mat_count"] = df["mat_list"].apply(lambda x: len(x) if isinstance(x, list) else 0)
df["tech_list"] = parse_list_field(df["Teknikk"])
df["tech_count"] = df["tech_list"].apply(lambda x: len(x) if isinstance(x, list) else 0)
df["period_25yr"] = df["Frå år"].apply(assign_25yr_period)
df["decade"] = df["Frå år"].apply(assign_decade)
df["period_50yr"] = df["Frå år"].apply(assign_50yr_period)

# Century as integer for sorting
century_map = {
    "1200-talet": 1200, "1300-talet": 1300, "1400-talet": 1400,
    "1500-talet": 1500, "1600-talet": 1600, "1700-talet": 1700,
    "1800-talet": 1800, "1900-talet": 1900, "2000-talet": 2000,
}
df["century_int"] = df["Hundreår"].map(century_map)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  1. MATERIAL COMPLEXITY PER CHAIR OVER TIME                              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

section_header("1. MATERIAL COMPLEXITY PER CHAIR OVER TIME")

section_header("1a. Mean, Median, Max materials per chair by 25-year period", 2)
period_stats = (
    df[df["period_25yr"].notna()]
    .groupby("period_25yr")["mat_count"]
    .agg(["mean", "median", "max", "count"])
    .sort_index()
)
print(f"\n{'Period':<18} {'Mean':>6} {'Median':>7} {'Max':>5} {'N chairs':>9}")
print("-" * 50)
for period, row in period_stats.iterrows():
    print(f"{period:<18} {row['mean']:>6.2f} {row['median']:>7.1f} {row['max']:>5.0f} {row['count']:>9.0f}")

section_header("1b. Top 20 most materially complex chairs", 2)
top_complex = df.nlargest(20, "mat_count")[
    ["Namn", "Frå år", "Stilperiode", "mat_count", "Materialar"]
]
for _, row in top_complex.iterrows():
    print(f"\n  {row['Namn']} ({row['Frå år']:.0f}, {row['Stilperiode']})")
    print(f"    Materials ({row['mat_count']:.0f}): {row['Materialar']}")

section_header("1c. Material complexity trend by century", 2)
century_stats = (
    df[df["Hundreår"].notna()]
    .groupby("Hundreår")["mat_count"]
    .agg(["mean", "median", "max", "std", "count"])
)
# Sort by century order
century_order = [f"{c}-talet" for c in range(1200, 2100, 100)]
century_stats = century_stats.reindex([c for c in century_order if c in century_stats.index])
print(f"\n{'Century':<14} {'Mean':>6} {'Med':>5} {'Max':>5} {'Std':>6} {'N':>6}")
print("-" * 48)
for cent, row in century_stats.iterrows():
    print(f"{cent:<14} {row['mean']:>6.2f} {row['median']:>5.1f} {row['max']:>5.0f} {row['std']:>6.2f} {row['count']:>6.0f}")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  2. MAHOGNI DEEP DIVE                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

section_header("2. MAHOGNI DEEP DIVE")

# All chairs with mahogni in Materialar
mahogni_mask = df["Materialar"].fillna("").str.contains("Mahogni", case=False)
df_mahogni = df[mahogni_mask].copy()
print(f"\nTotal chairs with mahogni: {len(df_mahogni)} / {len(df)}")

# NMK chairs: those with a Nasjonalmuseet link
nmk_mask = df["Nasjonalmuseet"].notna()
df_nmk = df[nmk_mask].copy()
df_nmk_mahogni = df_nmk[df_nmk["Materialar"].fillna("").str.contains("Mahogni", case=False)]
print(f"NMK chairs total: {len(df_nmk)}")
print(f"NMK chairs with mahogni: {len(df_nmk_mahogni)}")

section_header("2a. NMK mahogni timeline by DECADE", 2)
nmk_decade_all = df_nmk[df_nmk["decade"].notna()].groupby("decade").size()
nmk_decade_mahogni = df_nmk_mahogni[df_nmk_mahogni["decade"].notna()].groupby("decade").size()
decade_pct = (nmk_decade_mahogni / nmk_decade_all * 100).fillna(0)

print(f"\n{'Decade':<14} {'Mahogni':>8} {'Total':>7} {'%':>7}")
print("-" * 40)
all_decades = sorted(set(nmk_decade_all.index) | set(nmk_decade_mahogni.index))
for dec in all_decades:
    m = nmk_decade_mahogni.get(dec, 0)
    t = nmk_decade_all.get(dec, 0)
    p = decade_pct.get(dec, 0)
    if t > 0:
        print(f"{dec:<14} {m:>8} {t:>7} {p:>6.1f}%")

section_header("2b. Materialkommentar field analysis for mahogni subtypes", 2)
mahogni_subtypes = [
    "cubamahogni", "cuba-mahogni", "mahognifiner", "mahogni finer",
    "mahognyfinér", "mahognifanér", "beiset mahogni", "massiv mahogni",
    "imitert mahogni", "falsk mahogni", "mahogni med"
]
kommentar_field = df["Materialkommentar"].fillna("")
for subtype in mahogni_subtypes:
    matches = kommentar_field.str.contains(subtype, case=False)
    n = matches.sum()
    if n > 0:
        print(f"\n  '{subtype}' appears in {n} chairs:")
        for _, row in df[matches].head(5).iterrows():
            print(f"    - {row['Namn']} ({row.get('Frå år', '?')}): {row['Materialkommentar'][:120]}")

# Also search for any mention of mahogni in Materialkommentar
mahogni_kommentar = df[kommentar_field.str.contains("mahogni", case=False)]
print(f"\n  Total chairs mentioning 'mahogni' in Materialkommentar: {len(mahogni_kommentar)}")
# Show unique phrases
print("\n  Sample Materialkommentar entries mentioning mahogni:")
for _, row in mahogni_kommentar.head(20).iterrows():
    print(f"    [{row['Frå år']:.0f}] {row['Materialkommentar'][:140]}")

section_header("2c. Co-occurrence: materials appearing WITH mahogni", 2)
co_materials = Counter()
for _, row in df_mahogni.iterrows():
    if isinstance(row["mat_list"], list):
        for m in row["mat_list"]:
            if m.lower() != "mahogni":
                co_materials[m] += 1

print(f"\n{'Material':<25} {'Count':>6} {'% of mahogni chairs':>20}")
print("-" * 55)
for mat, cnt in co_materials.most_common(25):
    print(f"{mat:<25} {cnt:>6} {cnt/len(df_mahogni)*100:>19.1f}%")

section_header("2d. Techniques used with mahogni", 2)
tech_with_mahogni = Counter()
for _, row in df_mahogni.iterrows():
    if isinstance(row["tech_list"], list):
        for t in row["tech_list"]:
            tech_with_mahogni[t] += 1

print(f"\n{'Technique':<25} {'Count':>6} {'% of mahogni chairs':>20}")
print("-" * 55)
for tech, cnt in tech_with_mahogni.most_common(20):
    print(f"{tech:<25} {cnt:>6} {cnt/len(df_mahogni)*100:>19.1f}%")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  3. STILMIGRASJON DETAILED                                               ║
# ╚════════════════════════════════════════════════════════════════════════════╝

section_header("3. STILMIGRASJON (STYLE MIGRATION) DETAILED")

section_header("3a. Per style: countries, centuries, dominant materials", 2)
styles = df["Stilperiode"].dropna().unique()
for style in sorted(styles):
    sub = df[df["Stilperiode"] == style]
    print(f"\n  ┌─ {style} ({len(sub)} chairs)")
    # Year range
    yr_min = sub["Frå år"].min()
    yr_max = sub["Frå år"].max()
    print(f"  │  Year range: {yr_min:.0f} – {yr_max:.0f}")
    # Centuries
    centuries = sub["Hundreår"].value_counts()
    print(f"  │  Centuries: {', '.join(f'{c} ({n})' for c, n in centuries.items())}")
    # Countries
    countries = sub["Nasjonalitet"].value_counts()
    print(f"  │  Countries: {', '.join(f'{c} ({n})' for c, n in countries.head(6).items())}")
    # Top materials
    all_mats = Counter()
    for mats in sub["mat_list"].dropna():
        for m in mats:
            all_mats[m] += 1
    top5 = all_mats.most_common(5)
    print(f"  │  Top materials: {', '.join(f'{m} ({c})' for m, c in top5)}")
    # Dimensions
    for dim in ["Høgde (cm)", "Breidde (cm)", "Djupn (cm)"]:
        vals = sub[dim].dropna()
        if len(vals) > 0:
            pass  # included in style purity below
    print(f"  └─")

section_header("3b. Style 'purity' - dimensional consistency (CV = std/mean)", 2)
print(f"\n{'Style':<25} {'N':>5} {'H_mean':>7} {'H_cv':>6} {'W_mean':>7} {'W_cv':>6} {'D_mean':>7} {'D_cv':>6}")
print("-" * 80)
style_dim_stats = {}
for style in sorted(styles):
    sub = df[df["Stilperiode"] == style]
    if len(sub) < 3:
        continue
    row_data = {"N": len(sub)}
    for dim_col, dim_key in [("Høgde (cm)", "H"), ("Breidde (cm)", "W"), ("Djupn (cm)", "D")]:
        vals = sub[dim_col].dropna()
        if len(vals) > 2:
            row_data[f"{dim_key}_mean"] = vals.mean()
            row_data[f"{dim_key}_cv"] = vals.std() / vals.mean() if vals.mean() > 0 else 0
        else:
            row_data[f"{dim_key}_mean"] = np.nan
            row_data[f"{dim_key}_cv"] = np.nan
    style_dim_stats[style] = row_data
    rd = row_data
    print(f"{style:<25} {rd['N']:>5} {rd.get('H_mean', 0):>7.1f} {rd.get('H_cv', 0):>6.3f} "
          f"{rd.get('W_mean', 0):>7.1f} {rd.get('W_cv', 0):>6.3f} "
          f"{rd.get('D_mean', 0):>7.1f} {rd.get('D_cv', 0):>6.3f}")

section_header("3c. Confusion matrix: dimension overlap between styles", 2)
print("  (Styles with most similar mean dimensions - potential confusion pairs)")
style_names = sorted(style_dim_stats.keys())
confusion_pairs = []
for i, s1 in enumerate(style_names):
    for s2 in style_names[i+1:]:
        d1 = style_dim_stats[s1]
        d2 = style_dim_stats[s2]
        # Euclidean distance in H, W, D space
        dist = 0
        valid = 0
        for dim_key in ["H", "W", "D"]:
            m1 = d1.get(f"{dim_key}_mean")
            m2 = d2.get(f"{dim_key}_mean")
            if m1 is not None and m2 is not None and not np.isnan(m1) and not np.isnan(m2):
                dist += (m1 - m2) ** 2
                valid += 1
        if valid == 3:
            confusion_pairs.append((s1, s2, np.sqrt(dist)))

confusion_pairs.sort(key=lambda x: x[2])
print(f"\n  Top 15 most dimensionally similar style pairs (likely confusion):")
print(f"  {'Style 1':<22} {'Style 2':<22} {'Eucl. dist (cm)':>16}")
print("  " + "-" * 62)
for s1, s2, d in confusion_pairs[:15]:
    print(f"  {s1:<22} {s2:<22} {d:>16.1f}")

print(f"\n  Top 10 most dimensionally DISTINCT style pairs:")
for s1, s2, d in confusion_pairs[-10:]:
    print(f"  {s1:<22} {s2:<22} {d:>16.1f}")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  4. SPECIFIC CHAIR NARRATIVES                                            ║
# ╚════════════════════════════════════════════════════════════════════════════╝

section_header("4. SPECIFIC CHAIR NARRATIVES")

section_header("4a. The 10 oldest chairs in the database (excluding year=0 placeholder)", 2)
oldest = df[df["Frå år"] > 100].nsmallest(10, "Frå år")
for _, row in oldest.iterrows():
    print(f"\n  {row['Namn']}")
    print(f"    Year: {row['Frå år']:.0f} | Style: {row['Stilperiode']} | Country: {row['Nasjonalitet']}")
    print(f"    Materials: {row['Materialar']}")
    print(f"    Dimensions: H={row['Høgde (cm)']}cm W={row['Breidde (cm)']}cm D={row['Djupn (cm)']}cm")
    print(f"    Seat height: {row['Setehøgde (cm)']}cm | Weight: {row['Estimert vekt (kg)']}kg")
    print(f"    Technique: {row['Teknikk']}")
    if pd.notna(row['Materialkommentar']):
        print(f"    Materialkommentar: {row['Materialkommentar'][:150]}")

section_header("4b. The 10 most materially complex chairs", 2)
most_complex = df.nlargest(10, "mat_count")
for _, row in most_complex.iterrows():
    print(f"\n  {row['Namn']} ({row['Frå år']:.0f}, {row['Stilperiode']})")
    print(f"    {row['mat_count']:.0f} materials: {row['Materialar']}")
    if pd.notna(row['Materialkommentar']):
        print(f"    Kommentar: {row['Materialkommentar'][:150]}")

section_header("4c. All chairs from Eventyrværelset or with 'Jugend' style", 2)
jugend_mask = df["Stilperiode"].fillna("").str.contains("Jugend", case=False)
eventyr_mask = (
    df["Namn"].fillna("").str.contains("eventyr", case=False)
    | df["Materialkommentar"].fillna("").str.contains("eventyr", case=False)
    | df["Nemning"].fillna("").str.contains("eventyr", case=False)
    | df["Emneord"].fillna("").str.contains("eventyr", case=False)
)
jugend_or_eventyr = df[jugend_mask | eventyr_mask]
print(f"\n  Found {jugend_mask.sum()} Jugend chairs and {eventyr_mask.sum()} Eventyrværelset chairs")
print(f"  Combined unique: {len(jugend_or_eventyr)}")
for _, row in jugend_or_eventyr.iterrows():
    label = ""
    if jugend_mask.loc[row.name]:
        label += "[Jugend] "
    if eventyr_mask.loc[row.name]:
        label += "[Eventyr] "
    print(f"\n  {label}{row['Namn']} ({row['Frå år']:.0f})")
    print(f"    Materials: {row['Materialar']}")
    print(f"    Country: {row['Nasjonalitet']} | Technique: {row['Teknikk']}")
    if pd.notna(row['Materialkommentar']):
        print(f"    Kommentar: {row['Materialkommentar'][:150]}")

section_header("4d. All chairs with 'ibenholt' (ebony)", 2)
ibenholt_mask = (
    df["Materialar"].fillna("").str.contains("ibenholt", case=False)
    | df["Materialkommentar"].fillna("").str.contains("ibenholt", case=False)
)
df_ibenholt = df[ibenholt_mask]
print(f"\n  Found {len(df_ibenholt)} chairs with ibenholt/ebony")
for _, row in df_ibenholt.iterrows():
    print(f"\n  {row['Namn']} ({row['Frå år']:.0f}, {row['Stilperiode']})")
    print(f"    Materials: {row['Materialar']}")
    print(f"    Country: {row['Nasjonalitet']}")
    if pd.notna(row['Materialkommentar']):
        print(f"    Kommentar: {row['Materialkommentar'][:150]}")

section_header("4e. Chairs with notable designers", 2)
designers = {
    "Aalto": ["aalto"],
    "Jacobsen": ["jacobsen", "arne jacobsen"],
    "Wegner": ["wegner", "hans wegner"],
    "Breuer": ["breuer", "marcel breuer"],
    "Eames": ["eames", "charles eames"],
    "Thonet": ["thonet"],
    "Chippendale": ["chippendale"],
}
for designer_name, search_terms in designers.items():
    mask = pd.Series(False, index=df.index)
    for term in search_terms:
        mask |= df["Namn"].fillna("").str.contains(term, case=False)
        mask |= df["Produsent"].fillna("").str.contains(term, case=False)
        mask |= df["Materialkommentar"].fillna("").str.contains(term, case=False)
        mask |= df["Stilperiode"].fillna("").str.contains(term, case=False)
        mask |= df["Nemning"].fillna("").str.contains(term, case=False)
    matches = df[mask]
    if len(matches) > 0:
        print(f"\n  ── {designer_name}: {len(matches)} chairs found ──")
        for _, row in matches.iterrows():
            print(f"    {row['Namn']} ({row['Frå år']:.0f}) | Producer: {row['Produsent']} | Style: {row['Stilperiode']}")
            print(f"      Materials: {row['Materialar']}")
    else:
        print(f"\n  ── {designer_name}: No matches found ──")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  5. WEIGHT vs MATERIAL ANALYSIS                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

section_header("5. WEIGHT vs MATERIAL ANALYSIS")

# Filter out 0.0 kg as likely missing data
df_w = df[(df["Estimert vekt (kg)"].notna()) & (df["Estimert vekt (kg)"] > 0)].copy()
print(f"\nChairs with weight data (>0 kg): {len(df_w)}")

section_header("5a. Weight distributions per material group", 2)
# Explode materials
all_materials = Counter()
for mats in df["mat_list"].dropna():
    for m in mats:
        all_materials[m] += 1

# For top 20 materials, compute weight stats
print(f"\n{'Material':<22} {'N':>5} {'Mean wt':>8} {'Med wt':>8} {'Min':>6} {'Max':>6} {'Std':>6}")
print("-" * 68)
top_mats = [m for m, _ in all_materials.most_common(25)]
for mat in top_mats:
    mask = df_w["Materialar"].fillna("").str.contains(mat, case=False, regex=False)
    weights = df_w.loc[mask, "Estimert vekt (kg)"]
    if len(weights) >= 3:
        print(f"{mat:<22} {len(weights):>5} {weights.mean():>8.1f} {weights.median():>8.1f} "
              f"{weights.min():>6.1f} {weights.max():>6.1f} {weights.std():>6.1f}")

section_header("5b. Weight trend by 50-year period", 2)
df_w["period_50yr"] = df_w["Frå år"].apply(assign_50yr_period)
wt_trend = (
    df_w[df_w["period_50yr"].notna()]
    .groupby("period_50yr")["Estimert vekt (kg)"]
    .agg(["mean", "median", "std", "count"])
    .sort_index()
)
print(f"\n{'Period':<16} {'Mean':>7} {'Median':>7} {'Std':>6} {'N':>5}")
print("-" * 45)
for period, row in wt_trend.iterrows():
    print(f"{period:<16} {row['mean']:>7.1f} {row['median']:>7.1f} {row['std']:>6.1f} {row['count']:>5.0f}")

section_header("5c. Lightest vs heaviest per century", 2)
for cent in sorted(df_w["Hundreår"].dropna().unique(), key=lambda x: century_map.get(x, 0)):
    sub = df_w[df_w["Hundreår"] == cent]
    if len(sub) == 0:
        continue
    lightest = sub.loc[sub["Estimert vekt (kg)"].idxmin()]
    heaviest = sub.loc[sub["Estimert vekt (kg)"].idxmax()]
    print(f"\n  {cent}:")
    print(f"    Lightest: {lightest['Namn']} ({lightest['Frå år']:.0f}) — {lightest['Estimert vekt (kg)']:.1f} kg")
    print(f"      Materials: {lightest['Materialar']}")
    print(f"    Heaviest: {heaviest['Namn']} ({heaviest['Frå år']:.0f}) — {heaviest['Estimert vekt (kg)']:.1f} kg")
    print(f"      Materials: {heaviest['Materialar']}")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  6. TECHNIQUE DEEP DIVE                                                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

section_header("6. TECHNIQUE DEEP DIVE")

# Build technique list
all_techniques = Counter()
for techs in df["tech_list"].dropna():
    for t in techs:
        all_techniques[t] += 1

print(f"\nAll techniques found ({len(all_techniques)}):")
for t, c in all_techniques.most_common():
    print(f"  {t:<30} {c:>5}")

section_header("6a. Technique co-occurrence matrix", 2)
tech_names = [t for t, _ in all_techniques.most_common(15)]
cooccur = pd.DataFrame(0, index=tech_names, columns=tech_names)
for techs in df["tech_list"].dropna():
    present = [t for t in techs if t in tech_names]
    for t1, t2 in combinations(present, 2):
        cooccur.loc[t1, t2] += 1
        cooccur.loc[t2, t1] += 1
    for t in present:
        cooccur.loc[t, t] += 1  # diagonal = total count

# Print as table
header = "".ljust(18) + "".join(t[:6].rjust(7) for t in tech_names)
print(f"\n{header}")
print("-" * len(header))
for t1 in tech_names:
    row_str = t1.ljust(18) + "".join(f"{cooccur.loc[t1, t2]:>7}" for t2 in tech_names)
    print(row_str)

section_header("6b. Technique 'signatures' per century", 2)
century_order = [f"{c}-talet" for c in range(1200, 2100, 100)]
print(f"\n{'Technique':<22}", end="")
valid_centuries = [c for c in century_order if c in df["Hundreår"].values]
for c in valid_centuries:
    print(f"{c[:4]:>8}", end="")
print()
print("-" * (22 + 8 * len(valid_centuries)))

for tech, _ in all_techniques.most_common(20):
    print(f"{tech:<22}", end="")
    for cent in valid_centuries:
        cent_total = len(df[df["Hundreår"] == cent])
        tech_in_cent = df[(df["Hundreår"] == cent)].apply(
            lambda r: tech in r["tech_list"] if isinstance(r["tech_list"], list) else False, axis=1
        ).sum()
        pct = tech_in_cent / cent_total * 100 if cent_total > 0 else 0
        print(f"{pct:>7.1f}%", end="")
    print()

section_header("6c. First and last appearance of each technique", 2)
print(f"\n{'Technique':<25} {'First':>8} {'Last':>8} {'Span':>6} {'Count':>6}")
print("-" * 58)
for tech, cnt in all_techniques.most_common():
    tech_years = df[df.apply(
        lambda r: tech in r["tech_list"] if isinstance(r["tech_list"], list) else False, axis=1
    )]["Frå år"].dropna()
    if len(tech_years) > 0:
        first = tech_years.min()
        last = tech_years.max()
        print(f"{tech:<25} {first:>8.0f} {last:>8.0f} {last-first:>6.0f} {cnt:>6}")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  7. PROPORTIONS DEEP DIVE                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

section_header("7. PROPORTIONS DEEP DIVE")

# Filter out zero-dimension chairs (likely missing data)
df_dim = df[
    (df["Høgde (cm)"].notna()) & (df["Breidde (cm)"].notna()) & (df["Djupn (cm)"].notna())
    & (df["Høgde (cm)"] > 0) & (df["Breidde (cm)"] > 0) & (df["Djupn (cm)"] > 0)
].copy()
df_dim["H_W_ratio"] = df_dim["Høgde (cm)"] / df_dim["Breidde (cm)"]
df_dim["W_D_ratio"] = df_dim["Breidde (cm)"] / df_dim["Djupn (cm)"]

# Seat height ratio — also filter zero heights
df_dim_seat = df_dim[(df_dim["Setehøgde (cm)"].notna()) & (df_dim["Setehøgde (cm)"] > 0)].copy()
df_dim_seat["seat_pct"] = df_dim_seat["Setehøgde (cm)"] / df_dim_seat["Høgde (cm)"] * 100

section_header("7a. H/W ratio distribution per century", 2)
print(f"\n{'Century':<14} {'N':>5} {'Mean':>7} {'Med':>7} {'Std':>6} {'Min':>6} {'Max':>6}  {'Skew':>6}")
print("-" * 62)
for cent in [c for c in century_order if c in df_dim["Hundreår"].values]:
    vals = df_dim[df_dim["Hundreår"] == cent]["H_W_ratio"]
    if len(vals) > 2:
        from scipy.stats import skew as calc_skew
        sk = calc_skew(vals.dropna())
        print(f"{cent:<14} {len(vals):>5} {vals.mean():>7.3f} {vals.median():>7.3f} "
              f"{vals.std():>6.3f} {vals.min():>6.3f} {vals.max():>6.3f}  {sk:>6.3f}")

section_header("7b. Seat height as % of total height over time (25-yr periods)", 2)
seat_trend = (
    df_dim_seat[df_dim_seat["period_25yr"].notna()]
    .groupby("period_25yr")["seat_pct"]
    .agg(["mean", "median", "std", "count"])
    .sort_index()
)
print(f"\n{'Period':<18} {'Mean%':>7} {'Med%':>7} {'Std':>6} {'N':>5}")
print("-" * 46)
for period, row in seat_trend.iterrows():
    if row["count"] >= 2:
        print(f"{period:<18} {row['mean']:>7.1f} {row['median']:>7.1f} {row['std']:>6.1f} {row['count']:>5.0f}")

section_header("7c. Width/Depth ratio over time (square vs rectangular?)", 2)
wd_trend = (
    df_dim[df_dim["period_25yr"].notna()]
    .groupby("period_25yr")["W_D_ratio"]
    .agg(["mean", "median", "count"])
    .sort_index()
)
print(f"\n{'Period':<18} {'Mean W/D':>9} {'Med W/D':>9} {'N':>5}  Interpretation")
print("-" * 70)
for period, row in wd_trend.iterrows():
    if row["count"] >= 2:
        interp = "SQUARE" if abs(row["mean"] - 1.0) < 0.05 else ("WIDER" if row["mean"] > 1.0 else "DEEPER")
        print(f"{period:<18} {row['mean']:>9.3f} {row['median']:>9.3f} {row['count']:>5.0f}  {interp}")

section_header("7d. H/W ratio per style (sorted by mean)", 2)
hw_by_style = []
for style in sorted(styles):
    vals = df_dim[df_dim["Stilperiode"] == style]["H_W_ratio"].dropna()
    if len(vals) >= 3:
        hw_by_style.append((style, len(vals), vals.mean(), vals.median(), vals.std()))
hw_by_style.sort(key=lambda x: x[2])
print(f"\n{'Style':<25} {'N':>5} {'Mean H/W':>9} {'Med':>7} {'Std':>6}")
print("-" * 56)
for style, n, mean, med, std in hw_by_style:
    print(f"{style:<25} {n:>5} {mean:>9.3f} {med:>7.3f} {std:>6.3f}")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  8. THE POST-MAHOGNI ERA IN NMK                                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

section_header("8. THE POST-MAHOGNI ERA IN NMK")

section_header("8a. Material succession 1850-1950 at NMK (by decade)", 2)
df_nmk_1850_1950 = df_nmk[(df_nmk["Frå år"] >= 1850) & (df_nmk["Frå år"] <= 1950)].copy()
df_nmk_1850_1950["decade"] = df_nmk_1850_1950["Frå år"].apply(assign_decade)

print(f"\n  NMK chairs 1850-1950: {len(df_nmk_1850_1950)}")

# Per decade, count top materials
decades_1850_1950 = sorted(df_nmk_1850_1950["decade"].dropna().unique())
for dec in decades_1850_1950:
    sub = df_nmk_1850_1950[df_nmk_1850_1950["decade"] == dec]
    mat_counts = Counter()
    for mats in sub["mat_list"].dropna():
        for m in mats:
            mat_counts[m] += 1
    total = len(sub)
    top = mat_counts.most_common(8)
    print(f"\n  {dec} (N={total}):")
    for m, c in top:
        bar = "█" * int(c / total * 30)
        print(f"    {m:<20} {c:>3} ({c/total*100:>5.1f}%) {bar}")

section_header("8b. What specifically replaces mahogni? Tracking key woods", 2)
key_woods = ["Mahogni", "Bjørk", "Eik", "Furu", "Bøk", "Valnøtt", "Ask", "Teak", "Palisander"]
print(f"\n{'Decade':<14}", end="")
for wood in key_woods:
    print(f"{wood[:8]:>9}", end="")
print(f"  {'Total':>6}")
print("-" * (14 + 9 * len(key_woods) + 8))

all_decades_nmk = sorted(df_nmk[df_nmk["decade"].notna()]["decade"].unique())
for dec in all_decades_nmk:
    sub = df_nmk[df_nmk["decade"] == dec]
    total = len(sub)
    if total == 0:
        continue
    print(f"{dec:<14}", end="")
    for wood in key_woods:
        # Case-insensitive match but handle Norwegian characters
        count = sub["Materialar"].fillna("").str.contains(wood, case=False, regex=False).sum()
        pct = count / total * 100
        print(f"{pct:>8.1f}%", end="")
    print(f"  {total:>6}")

section_header("8c. Is there a 'national romantic' material return?", 2)
# Look for Norwegian woods (furu, bjørk, eik) in Dragestil and late 1800s
print("\n  National romantic styles and Norwegian woods:")
nat_romantic_styles = ["Dragestil", "Jugend"]
for style in nat_romantic_styles:
    sub = df[df["Stilperiode"] == style]
    if len(sub) == 0:
        continue
    norw_woods = ["Furu", "Bjørk", "Eik", "Gran"]
    mat_counts = Counter()
    total_mats = 0
    for mats in sub["mat_list"].dropna():
        for m in mats:
            mat_counts[m] += 1
            total_mats += 1
    print(f"\n  {style} ({len(sub)} chairs):")
    for wood in norw_woods:
        c = mat_counts.get(wood, 0)
        pct = c / len(sub) * 100 if len(sub) > 0 else 0
        print(f"    {wood:<15} {c:>4} chairs ({pct:>5.1f}%)")
    # Compare with mahogni
    m_count = mat_counts.get("Mahogni", 0)
    print(f"    {'Mahogni':<15} {m_count:>4} chairs ({m_count/len(sub)*100:>5.1f}%)")
    # All materials for context
    print(f"    Full material profile: {', '.join(f'{m}({c})' for m, c in mat_counts.most_common(10))}")

section_header("8d. The Eventyrværelset chair (furu, 1897) as symbolic counter-example", 2)
# Search for the specific chair
eventyr_candidates = df[
    (df["Materialar"].fillna("").str.contains("Furu", case=False))
    & (df["Frå år"] >= 1890) & (df["Frå år"] <= 1900)
]
print(f"\n  Furu chairs from 1890-1900: {len(eventyr_candidates)}")
for _, row in eventyr_candidates.iterrows():
    print(f"\n  {row['Namn']} ({row['Frå år']:.0f})")
    print(f"    Style: {row['Stilperiode']} | Country: {row['Nasjonalitet']}")
    print(f"    Materials: {row['Materialar']}")
    print(f"    Dimensions: H={row['Høgde (cm)']}cm W={row['Breidde (cm)']}cm D={row['Djupn (cm)']}cm")
    print(f"    Weight: {row['Estimert vekt (kg)']}kg | Seat height: {row['Setehøgde (cm)']}cm")
    print(f"    Technique: {row['Teknikk']}")
    if pd.notna(row['Materialkommentar']):
        print(f"    Materialkommentar: {row['Materialkommentar']}")
    if pd.notna(row['Produsent']):
        print(f"    Producer: {row['Produsent']}")

# Context: what were OTHER chairs made of in 1897?
print(f"\n  CONTEXT: All NMK chairs from 1890-1900 and their primary materials:")
nmk_1890s = df_nmk[(df_nmk["Frå år"] >= 1890) & (df_nmk["Frå år"] <= 1900)]
mat_1890s = Counter()
for mats in nmk_1890s["mat_list"].dropna():
    for m in mats:
        mat_1890s[m] += 1
for m, c in mat_1890s.most_common(15):
    print(f"    {m:<20} {c:>4} ({c/len(nmk_1890s)*100:.1f}%)")

# Mahogni dominance in the decade vs furu as counter-example
mahogni_1890s = nmk_1890s["Materialar"].fillna("").str.contains("Mahogni", case=False).sum()
furu_1890s = nmk_1890s["Materialar"].fillna("").str.contains("Furu", case=False).sum()
print(f"\n  In 1890-1900 at NMK:")
print(f"    Mahogni chairs: {mahogni_1890s} / {len(nmk_1890s)} ({mahogni_1890s/len(nmk_1890s)*100:.1f}%)")
print(f"    Furu chairs:    {furu_1890s} / {len(nmk_1890s)} ({furu_1890s/len(nmk_1890s)*100:.1f}%)")
print(f"    → Furu is the deliberate counter-choice: local, humble, anti-imperial")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  SUMMARY STATISTICS                                                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝

section_header("SUMMARY STATISTICS")

print(f"""
  Total chairs in database:    {len(df)}
  With weight data:            {df['Estimert vekt (kg)'].notna().sum()}
  With materials data:         {df['Materialar'].notna().sum()}
  With technique data:         {df['Teknikk'].notna().sum()}
  With style period:           {df['Stilperiode'].notna().sum()}
  Unique materials:            {len(all_materials)}
  Unique techniques:           {len(all_techniques)}
  Unique style periods:        {df['Stilperiode'].nunique()}
  Unique countries:            {df['Nasjonalitet'].nunique()}
  Year range:                  {df['Frå år'].min():.0f} – {df['Frå år'].max():.0f}
  NMK chairs (with link):      {nmk_mask.sum()}
  Mahogni chairs (total):      {mahogni_mask.sum()}
  Mean materials per chair:    {df['mat_count'].mean():.2f}
  Mean techniques per chair:   {df['tech_count'].mean():.2f}
  Mean weight:                 {df['Estimert vekt (kg)'].mean():.1f} kg
  Mean height:                 {df['Høgde (cm)'].mean():.1f} cm
  Mean width:                  {df['Breidde (cm)'].mean():.1f} cm
  Mean depth:                  {df['Djupn (cm)'].mean():.1f} cm
  Mean seat height:            {df['Setehøgde (cm)'].mean():.1f} cm
""")

print("=" * 80)
print("  ANALYSIS COMPLETE")
print("=" * 80)
