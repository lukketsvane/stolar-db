#!/usr/bin/env python3
"""
FORMLÆRE v2: Reinska analyse med outlier-filtrering og robuste mål.
"""

import pandas as pd
import numpy as np
from collections import Counter
from scipy import stats
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv('/home/user/stolar-db/stolar_db.csv')

for col in ['Høgde (cm)', 'Breidde (cm)', 'Djupn (cm)', 'Setehøgde (cm)', 'Estimert vekt (kg)', 'Frå år']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# REINSKING: Fjern urealistiske verdiar
df = df[(df['Høgde (cm)'] > 30) | df['Høgde (cm)'].isna()]
df = df[(df['Høgde (cm)'] < 300) | df['Høgde (cm)'].isna()]
df = df[(df['Breidde (cm)'] > 15) | df['Breidde (cm)'].isna()]
df = df[(df['Breidde (cm)'] < 300) | df['Breidde (cm)'].isna()]
df = df[(df['Djupn (cm)'] > 15) | df['Djupn (cm)'].isna()]
df = df[(df['Djupn (cm)'] < 300) | df['Djupn (cm)'].isna()]

print(f"Etter reinsking: {len(df)} stolar")

df['material_list'] = df['Materialar'].fillna('').str.split(', ')
df['n_materialar'] = df['material_list'].apply(lambda x: len([m for m in x if m]))
df['museum'] = df['Objekt-ID'].apply(lambda x: 'NM' if str(x).startswith(('OK-', 'NMK')) else 'VA')

dim_cols = ['Høgde (cm)', 'Breidde (cm)', 'Djupn (cm)']
dim_df = df.dropna(subset=dim_cols).copy()
dim_df['h_w_ratio'] = dim_df['Høgde (cm)'] / dim_df['Breidde (cm)']
dim_df['h_d_ratio'] = dim_df['Høgde (cm)'] / dim_df['Djupn (cm)']
dim_df['volume'] = dim_df['Høgde (cm)'] * dim_df['Breidde (cm)'] * dim_df['Djupn (cm)']

print(f"Med dimensjonsdata: {len(dim_df)}")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("1. FORMROMMET - EMPIRISK KARTLEGGING")
print("="*70)

for col in dim_cols:
    vals = dim_df[col]
    print(f"  {col}: median={vals.median():.1f}, IQR=[{vals.quantile(.25):.1f}, {vals.quantile(.75):.1f}], "
          f"CV={vals.std()/vals.mean()*100:.1f}%")

print(f"  H/B-ratio: median={dim_df['h_w_ratio'].median():.2f}, "
      f"IQR=[{dim_df['h_w_ratio'].quantile(.25):.2f}, {dim_df['h_w_ratio'].quantile(.75):.2f}]")

# Formrom-dekking
h_bins = np.arange(30, 200, 10)
w_bins = np.arange(20, 130, 10)
d_bins = np.arange(20, 130, 10)
total_cells = (len(h_bins)-1) * (len(w_bins)-1) * (len(d_bins)-1)
h_idx = np.digitize(dim_df['Høgde (cm)'], h_bins)
w_idx = np.digitize(dim_df['Breidde (cm)'], w_bins)
d_idx = np.digitize(dim_df['Djupn (cm)'], d_bins)
occupied = len(set(zip(h_idx, w_idx, d_idx)))
print(f"\n  Formrom (10cm celler): {occupied}/{total_cells} busette ({occupied/total_cells*100:.1f}%)")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("2. SELEKSJONSTRYKK - FORMVARIASJON UNDER KONSTANT FUNKSJON")
print("="*70)

mat_combos = df['Materialar'].dropna().unique()
print(f"  Unike materialkombinasjonar: {len(mat_combos)}")
print(f"  Stilperiodar: {len(df['Stilperiode'].dropna().unique())}")
print(f"  Nasjonalitetar: {len(df['Nasjonalitet'].dropna().unique())}")

# Intra-stil variasjon
print(f"\n  Variasjon INNANFOR stilperiodar (CV for H/B-ratio):")
style_dim = dim_df.dropna(subset=['Stilperiode'])
style_stats = []
for style in sorted(style_dim['Stilperiode'].unique()):
    sub = style_dim[style_dim['Stilperiode'] == style]
    if len(sub) >= 10:
        cv = sub['h_w_ratio'].std() / sub['h_w_ratio'].mean() * 100
        style_stats.append((style, len(sub), cv, sub['h_w_ratio'].mean()))
        print(f"    {style}: n={len(sub)}, CV={cv:.1f}%, mean H/B={sub['h_w_ratio'].mean():.2f}")

mean_intra_cv = np.mean([s[2] for s in style_stats])
print(f"\n  Gjennomsnittleg intra-stil CV: {mean_intra_cv:.1f}%")
print(f"  -> Vesentleg variasjon INNANFOR stilar stadfestar prop. 2.42")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("3. TILPASSINGSLANDSKAPET - STILAR SOM HAUGAR")
print("="*70)

# Eta² - kor mykje forklarer stilperiode?
valid = style_dim.dropna(subset=dim_cols)
y_h = valid['Høgde (cm)'].values
groups = valid.groupby('Stilperiode')['Høgde (cm)']
ss_b = sum(len(g) * (g.mean() - y_h.mean())**2 for _, g in groups)
ss_t = sum((y_h - y_h.mean())**2)
eta2_style_h = ss_b / ss_t
print(f"  Eta² (stil -> høgde): {eta2_style_h:.3f}")

y_w = valid['Breidde (cm)'].values
groups_w = valid.groupby('Stilperiode')['Breidde (cm)']
ss_b_w = sum(len(g) * (g.mean() - y_w.mean())**2 for _, g in groups_w)
ss_t_w = sum((y_w - y_w.mean())**2)
eta2_style_w = ss_b_w / ss_t_w
print(f"  Eta² (stil -> breidde): {eta2_style_w:.3f}")

y_r = valid['h_w_ratio'].values
groups_r = valid.groupby('Stilperiode')['h_w_ratio']
ss_b_r = sum(len(g) * (g.mean() - y_r.mean())**2 for _, g in groups_r)
ss_t_r = sum((y_r - y_r.mean())**2)
eta2_style_r = ss_b_r / ss_t_r
print(f"  Eta² (stil -> H/B-ratio): {eta2_style_r:.3f}")

print(f"\n  -> Stilperiode forklarer {eta2_style_h*100:.0f}% av høgdevariansen")
print(f"     men {(1-eta2_style_h)*100:.0f}% er UFORKLART av stil åleine.")

# Stilsentra i formrommet
print(f"\n  Stilsentra (median H, B, D, H/B):")
for style, n, cv, mean_r in sorted(style_stats, key=lambda x: x[3]):
    sub = style_dim[style_dim['Stilperiode'] == style]
    print(f"    {style:30s}: H={sub['Høgde (cm)'].median():5.0f}  "
          f"B={sub['Breidde (cm)'].median():5.0f}  "
          f"H/B={mean_r:.2f}")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("4. LANDSKAPET I RØRSLE - TEMPORAL DYNAMIKK")
print("="*70)

centuries = sorted(df['Hundreår'].dropna().unique())
print(f"\n  Material Shannon-entropi per hundreår:")
entropy_data = []
for cent in centuries:
    sub = df[df['Hundreår'] == cent]
    mats = []
    for _, row in sub.iterrows():
        if pd.notna(row['Materialar']):
            mats.extend([m.strip() for m in str(row['Materialar']).split(',') if m.strip()])
    if len(mats) > 10:
        counts = Counter(mats)
        total = sum(counts.values())
        probs = [c/total for c in counts.values()]
        entropy = -sum(p * np.log2(p) for p in probs if p > 0)
        n_types = len(counts)
        h_max = np.log2(n_types)
        evenness = entropy / h_max if h_max > 0 else 0
        entropy_data.append((cent, entropy, n_types, len(sub), evenness))
        print(f"    {cent}: H'={entropy:.2f} bits, {n_types} typar, J'={evenness:.2f} (n={len(sub)})")

# Dimensional CV per halvhundreår
print(f"\n  Formvariasjon (CV i H/B-ratio) per halvhundreår:")
df_d = dim_df.dropna(subset=['Frå år']).copy()
df_d['halvhundre'] = (df_d['Frå år'] // 50) * 50
hc_stats = df_d.groupby('halvhundre').agg(
    n=('h_w_ratio', 'count'),
    mean=('h_w_ratio', 'mean'),
    std=('h_w_ratio', 'std')
)
hc_stats = hc_stats[hc_stats['n'] >= 10]
hc_stats['cv'] = hc_stats['std'] / hc_stats['mean'] * 100
for idx, row in hc_stats.iterrows():
    bar = '#' * int(row['cv'])
    print(f"    {int(idx):4d}s: CV={row['cv']:5.1f}% {bar} (n={int(row['n'])})")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("5. MATERIALETS GEOMETRISKE SIGNATUR")
print("="*70)

mat_dim = []
for _, row in dim_df.iterrows():
    if pd.notna(row['Materialar']):
        for m in str(row['Materialar']).split(', '):
            m = m.strip()
            if m:
                mat_dim.append({
                    'material': m, 'hogde': row['Høgde (cm)'],
                    'breidde': row['Breidde (cm)'], 'djupn': row['Djupn (cm)'],
                    'h_w': row['h_w_ratio'], 'volume': row['volume']
                })
mat_dim_df = pd.DataFrame(mat_dim)
top_mats = mat_dim_df['material'].value_counts().head(12).index

print(f"\n  Geometrisk signatur for topp-12 materialar:")
for m in top_mats:
    sub = mat_dim_df[mat_dim_df['material'] == m]
    print(f"    {m:15s} (n={len(sub):4d}): H/B={sub['h_w'].median():.2f}, "
          f"Vol={sub['volume'].median()/1000:.0f}L")

# Kruskal-Wallis
groups_kw = [mat_dim_df[mat_dim_df['material'] == m]['h_w'].values for m in top_mats]
h_stat, p_val = stats.kruskal(*groups_kw)
print(f"\n  Kruskal-Wallis H (materialar -> H/B-ratio): H={h_stat:.1f}, p={p_val:.2e}")

# Materialkategoriar
categories = {
    'Metall (stivt)': ['Stål', 'Jern', 'Aluminium'],
    'Hardtre (fibrøst)': ['Eik', 'Bøk', 'Mahogni', 'Nøttetre'],
    'Plastisk': ['Plast', 'Polypropylen', 'Glasfiber'],
    'Polstermaterial': ['Tekstil', 'Lær', 'Silke', 'Fløyel']
}
print(f"\n  Materialkategoriar og H/B-signatur (prop. 5.21):")
for cat, mats in categories.items():
    sub = mat_dim_df[mat_dim_df['material'].isin(mats)]
    if len(sub) >= 10:
        print(f"    {cat:25s} (n={len(sub):4d}): median H/B={sub['h_w'].median():.2f}, "
              f"IQR=[{sub['h_w'].quantile(.25):.2f}, {sub['h_w'].quantile(.75):.2f}]")

# Eta² for alt material -> dimensjonar
all_mats_flat = []
for _, row in df.iterrows():
    if pd.notna(row['Materialar']) and pd.notna(row['Høgde (cm)']) and row['Høgde (cm)'] > 30:
        mats = [m.strip() for m in str(row['Materialar']).split(',') if m.strip()]
        for m in mats:
            all_mats_flat.append({'mat': m, 'h': row['Høgde (cm)']})
adf = pd.DataFrame(all_mats_flat)
top30 = adf['mat'].value_counts().head(30).index
adf = adf[adf['mat'].isin(top30)]
y = adf['h'].values
grps = adf.groupby('mat')['h']
ss_b = sum(len(g)*(g.mean()-y.mean())**2 for _,g in grps)
ss_t = sum((y-y.mean())**2)
eta2_mat_h = ss_b/ss_t
print(f"\n  Eta² (topp-30 materialar -> høgde): {eta2_mat_h:.3f}")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("6-7. NAVIGASJON OG SUBSTRAT-UAVHENGIGHEIT")
print("="*70)

for mus in ['NM', 'VA']:
    sub = dim_df[dim_df['museum'] == mus]
    print(f"\n  {mus} (n={len(sub)}):")
    print(f"    Høgde: median={sub['Høgde (cm)'].median():.0f}, IQR=[{sub['Høgde (cm)'].quantile(.25):.0f}, {sub['Høgde (cm)'].quantile(.75):.0f}]")
    print(f"    H/B:   median={sub['h_w_ratio'].median():.2f}, IQR=[{sub['h_w_ratio'].quantile(.25):.2f}, {sub['h_w_ratio'].quantile(.75):.2f}]")

nm = dim_df[dim_df['museum']=='NM']['h_w_ratio']
va = dim_df[dim_df['museum']=='VA']['h_w_ratio']
u, p = stats.mannwhitneyu(nm, va)
d = (nm.mean()-va.mean()) / np.sqrt((nm.var()+va.var())/2)
print(f"\n  Mann-Whitney U: U={u:.0f}, p={p:.4f}")
print(f"  Cohen's d: {d:.3f}")
print(f"  -> {'Vesentleg' if abs(d) > 0.5 else 'Moderat' if abs(d) > 0.2 else 'Liten'} effekt")

# Overlapp i materialar mellom museum
nm_mats = set()
va_mats = set()
for _, row in df.iterrows():
    if pd.notna(row['Materialar']):
        mats = set(m.strip() for m in str(row['Materialar']).split(','))
        if row['museum'] == 'NM':
            nm_mats |= mats
        else:
            va_mats |= mats
jaccard = len(nm_mats & va_mats) / len(nm_mats | va_mats)
print(f"\n  Materialoverlapp: Jaccard={jaccard:.2f} ({len(nm_mats & va_mats)} felles av {len(nm_mats | va_mats)} totalt)")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("8. DISTRIBUERT NAVIGASJON - MATERIALKOMPLEKSITET")
print("="*70)

df_d2 = df.dropna(subset=['Frå år']).copy()
df_d2['halvhundre'] = (df_d2['Frå år'] // 50) * 50
mc = df_d2.groupby('halvhundre')['n_materialar'].agg(['mean','median','count'])
mc = mc[mc['count'] >= 10]
print(f"\n  Materialar per stol over tid:")
for idx, row in mc.iterrows():
    bar = '█' * int(row['mean'] * 3)
    print(f"    {int(idx)}s: {row['mean']:.1f} mat/stol {bar} (n={int(row['count'])})")

# Material co-occurrence nettverk
print(f"\n  Topp material-par (co-occurrence):")
pair_counts = Counter()
for _, row in df.iterrows():
    if pd.notna(row['Materialar']):
        mats = sorted(set(m.strip() for m in str(row['Materialar']).split(',') if m.strip()))
        for pair in combinations(mats, 2):
            pair_counts[pair] += 1
for (m1, m2), count in pair_counts.most_common(10):
    print(f"    {m1} + {m2}: {count}")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("9. STIAVHENGIGHEIT")
print("="*70)

sorted_df = dim_df.dropna(subset=['Frå år']).sort_values('Frå år')
h_vals = sorted_df['h_w_ratio'].values

print(f"\n  Temporal autokorrelasjon (H/B-ratio):")
for lag in [1, 5, 10, 25, 50]:
    if lag < len(h_vals):
        r = np.corrcoef(h_vals[:-lag], h_vals[lag:])[0,1]
        print(f"    Lag-{lag:2d}: r = {r:.3f}")

# Geografi -> form korrelasjon
print(f"\n  Geografisk stiavhengigheit (H/B per nasjonalitet):")
nat_dim = dim_df.dropna(subset=['Nasjonalitet'])
for nat in nat_dim['Nasjonalitet'].value_counts().head(10).index:
    sub = nat_dim[nat_dim['Nasjonalitet'] == nat]
    print(f"    {nat:20s} (n={len(sub):4d}): H/B={sub['h_w_ratio'].median():.2f}")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("KVANTITATIVT SAMANDRAG")
print("="*70)

print(f"""
  Formrom-dekking:              {occupied/total_cells*100:.1f}% busett
  Intra-stil CV (gjennomsnitt): {mean_intra_cv:.1f}%
  Eta² (stil -> høgde):         {eta2_style_h:.3f}
  Eta² (material -> høgde):     {eta2_mat_h:.3f}
  Shannon H' (1600-talet):      {[e for e in entropy_data if e[0]=='1600-talet'][0][1]:.2f} bits
  Shannon H' (1900-talet):      {[e for e in entropy_data if e[0]=='1900-talet'][0][1]:.2f} bits
  NM vs VA Cohen's d:           {d:.3f}
  Materialoverlapp (Jaccard):   {jaccard:.2f}
  Kruskal-Wallis (mat->H/B):    H={h_stat:.1f}, p={p_val:.2e}
""")
