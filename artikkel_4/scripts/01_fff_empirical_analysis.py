#!/usr/bin/env python3
"""
Form Follows Fitness – Empirisk analyse
========================================
Analyserer ALLE objekt i Nasjonalmuseet si stolsamling for å bevise
at form ikkje følgjer funksjon, men fitness: eit fleirdimensjonalt
seleksjonstrykk av material, teknologi, økonomi, geografi og kultur.

Kvar analyse produserer:
  - Kvantitative resultat (CSV)
  - Figurar (PNG)
  - LaTeX-fragment med nøkkeltal

Krev: pandas, numpy, scipy, sklearn, matplotlib, seaborn
"""

import os
import sys
import json
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score, permutation_test_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mutual_info_score, f1_score, classification_report
from sklearn.manifold import TSNE
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Paths
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART3_DATA = os.path.join(os.path.dirname(ROOT), 'artikkel_3', 'data')
OUT_DATA = os.path.join(ROOT, 'data')
OUT_FIG = os.path.join(ROOT, 'figurar')
os.makedirs(OUT_DATA, exist_ok=True)
os.makedirs(OUT_FIG, exist_ok=True)

# --- Styling ---
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})
COLORS = sns.color_palette("Set2", 12)

# =================================================================
# 1. LOAD DATA
# =================================================================
print("=" * 60)
print("FORM FOLLOWS FITNESS – EMPIRISK ANALYSE")
print("=" * 60)

meta = pd.read_csv(os.path.join(ART3_DATA, 'metadata.csv'))
geom = pd.read_csv(os.path.join(ART3_DATA, 'features_geometric.csv'))
mats = pd.read_csv(os.path.join(ART3_DATA, 'features_material.csv'))

# Merge all
df = meta.merge(geom, on='objectId', how='inner').merge(mats, on='objectId', how='inner')

# Parse datering to numeric year
df['year'] = pd.to_numeric(df['datering'], errors='coerce')
df = df.dropna(subset=['year'])
df['year'] = df['year'].astype(int)

# Create century bins
df['century'] = (df['year'] // 100) * 100
df['period_50'] = (df['year'] // 50) * 50

# Classify production as Norwegian vs foreign
def classify_origin(ps):
    if pd.isna(ps):
        return 'Ukjent'
    ps = str(ps).lower()
    norske = ['norge', 'oslo', 'kristiania', 'bergen', 'trondheim', 'stavanger',
              'fredrikstad', 'drammen', 'hamar', 'kongsberg', 'norsk']
    if any(n in ps for n in norske):
        return 'Noreg'
    elif ps in ['', 'ukjent']:
        return 'Ukjent'
    else:
        return 'Utanlands'

df['origin'] = df['produksjonsstad'].apply(classify_origin)

# Material columns
mat_cols = [c for c in df.columns if c.startswith('mat_')]
geom_cols = [c for c in geom.columns if c != 'objectId']

# Clean stilperiode
df['stil'] = df['stilperiode'].fillna('Ukjent')

N = len(df)
print(f"\nTotalt datasett: {N} stolar med komplett metadata + geometri")
print(f"Tidsrom: {df['year'].min()}–{df['year'].max()}")
print(f"Stilperiodar: {df['stil'].nunique()}")
print(f"Geometriske features: {len(geom_cols)}")
print(f"Materialfeatures: {len(mat_cols)}")

results = {}

# =================================================================
# 2. BEVIS 1: FUNKSJON ER KONSTANT – FORM ER IKKJE
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 1: Funksjon er konstant, form varierer radikalt")
print("=" * 60)

# All objects are chairs (same function). Measure total form variance.
geom_data = df[geom_cols].values
scaler = StandardScaler()
geom_scaled = scaler.fit_transform(geom_data)

# Total variance in geometric space
total_var = np.var(geom_scaled, axis=0).sum()
# Coefficient of variation for each raw feature
cv_per_feature = df[geom_cols].std() / df[geom_cols].mean().abs()
cv_per_feature = cv_per_feature.replace([np.inf, -np.inf], np.nan).dropna()

print(f"Total varians i geometrisk rom (standardisert): {total_var:.2f}")
print(f"Gjennomsnittleg CV over alle features: {cv_per_feature.mean():.2f}")
print(f"Max CV: {cv_per_feature.max():.2f} ({cv_per_feature.idxmax()})")

# Range of key dimensions
for feat in ['bbox_H', 'bbox_W', 'bbox_D', 'compactness', 'symmetry_score']:
    fmin, fmax = df[feat].min(), df[feat].max()
    ratio = fmax / fmin if fmin > 0 else np.nan
    print(f"  {feat}: {fmin:.3f} – {fmax:.3f} (ratio {ratio:.1f}x)")

results['bevis1'] = {
    'n_stolar': N,
    'total_varians': float(total_var),
    'mean_cv': float(cv_per_feature.mean()),
    'max_cv_feature': cv_per_feature.idxmax(),
    'max_cv': float(cv_per_feature.max()),
}

# Figure: Distribution of key geometric features showing massive variation
fig, axes = plt.subplots(2, 3, figsize=(12, 7))
key_feats = ['bbox_H', 'bbox_W', 'compactness', 'symmetry_score', 'curv_mean', 'aspect_H_W']
feat_labels = ['Høgde', 'Breidde', 'Kompaktheit', 'Symmetri', 'Kurvatur (snitt)', 'Aspektforhold H/B']
for ax, feat, label in zip(axes.flatten(), key_feats, feat_labels):
    ax.hist(df[feat], bins=30, color=COLORS[0], edgecolor='white', alpha=0.8)
    ax.set_xlabel(label)
    ax.set_ylabel('Tal stolar')
    ax.axvline(df[feat].mean(), color='red', linestyle='--', alpha=0.7, label=f'Snitt: {df[feat].mean():.2f}')
    ax.legend(fontsize=7)
fig.suptitle(f'Formvariasjon blant {N} stolar med identisk funksjon', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, 'fig1_form_variasjon.png'))
plt.close()
print("→ Figur 1: fig1_form_variasjon.png")

# =================================================================
# 3. BEVIS 2: MATERIAL PREDIKERER FORM BETRE ENN FUNKSJON
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 2: Material predikerer form (material → form kopling)")
print("=" * 60)

# For each geometric feature, compute how much variance is explained by material
# Using ANOVA: for each material, compare form distributions with vs without that material
anova_results = []
for mat in mat_cols:
    has_mat = df[mat] == 1
    if has_mat.sum() < 5:
        continue
    for gfeat in geom_cols:
        group_with = df.loc[has_mat, gfeat]
        group_without = df.loc[~has_mat, gfeat]
        if group_with.std() == 0 or group_without.std() == 0:
            continue
        stat, pval = stats.mannwhitneyu(group_with, group_without, alternative='two-sided')
        eff_size = abs(group_with.mean() - group_without.mean()) / df[gfeat].std()
        anova_results.append({
            'material': mat.replace('mat_', ''),
            'geometri_feature': gfeat,
            'p_value': pval,
            'effect_size_d': eff_size,
            'n_with': int(has_mat.sum()),
            'n_without': int((~has_mat).sum()),
            'mean_with': float(group_with.mean()),
            'mean_without': float(group_without.mean()),
        })

anova_df = pd.DataFrame(anova_results)
# Bonferroni correction
anova_df['p_corrected'] = anova_df['p_value'] * len(anova_df)
anova_df['significant'] = anova_df['p_corrected'] < 0.05

n_sig = anova_df['significant'].sum()
n_total = len(anova_df)
pct_sig = 100 * n_sig / n_total

print(f"Totalt testar: {n_total}")
print(f"Signifikante material→form koplingar (Bonferroni p<0.05): {n_sig} ({pct_sig:.1f}%)")

# Top effects
top_effects = anova_df.sort_values('effect_size_d', ascending=False).head(20)
print("\nTopp 10 sterkaste material→form koplingar:")
for _, row in top_effects.head(10).iterrows():
    sig = "*" if row['significant'] else ""
    print(f"  {row['material']:15s} → {row['geometri_feature']:20s}  d={row['effect_size_d']:.3f} {sig}")

anova_df.to_csv(os.path.join(OUT_DATA, 'material_form_coupling.csv'), index=False)
results['bevis2'] = {
    'n_testar': n_total,
    'n_signifikante': n_sig,
    'pct_signifikante': float(pct_sig),
}

# Figure: Heatmap of material→form effect sizes
pivot_mat = anova_df.pivot_table(index='material', columns='geometri_feature',
                                  values='effect_size_d', aggfunc='first')
# Keep materials with at least one strong effect
strong_mats = anova_df.groupby('material')['effect_size_d'].max()
strong_mats = strong_mats[strong_mats > 0.3].index
if len(strong_mats) > 0:
    pivot_sub = pivot_mat.loc[pivot_mat.index.isin(strong_mats)]
    fig, ax = plt.subplots(figsize=(14, max(6, len(pivot_sub) * 0.45)))
    sns.heatmap(pivot_sub, cmap='YlOrRd', ax=ax, linewidths=0.5,
                cbar_kws={'label': 'Effektstorleik (Cohens d)'})
    ax.set_title(f'Material → Form: Effektstorleik (n={N} stolar)', fontweight='bold')
    ax.set_xlabel('Geometrisk eigenskap')
    ax.set_ylabel('Material')
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_FIG, 'fig2_material_form_heatmap.png'))
    plt.close()
    print("→ Figur 2: fig2_material_form_heatmap.png")

# =================================================================
# 4. BEVIS 3: FITNESSLANDSKAPET – PCA AV ALLE SELEKSJONSTRYKK
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 3: Fitnesslandskapet – PCA av alle dimensjonar")
print("=" * 60)

# Combine geometric + material features
all_features = df[geom_cols + mat_cols].values
all_scaled = StandardScaler().fit_transform(all_features)

pca = PCA(n_components=5)
pca_coords = pca.fit_transform(all_scaled)
var_explained = pca.explained_variance_ratio_

print(f"PCA varians forklart:")
for i, v in enumerate(var_explained):
    print(f"  PC{i+1}: {v*100:.1f}%")
print(f"  Kumulativ PC1–3: {sum(var_explained[:3])*100:.1f}%")

df['PC1'] = pca_coords[:, 0]
df['PC2'] = pca_coords[:, 1]
df['PC3'] = pca_coords[:, 2]

results['bevis3'] = {
    'pca_var': [float(v) for v in var_explained],
    'cumulative_3': float(sum(var_explained[:3])),
}

# Figure: PCA colored by century (showing temporal drift in fitness landscape)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel A: By century
centuries = sorted(df['century'].unique())
cmap_cent = plt.cm.viridis(np.linspace(0, 1, len(centuries)))
cent_colors = {c: cmap_cent[i] for i, c in enumerate(centuries)}
for cent in centuries:
    mask = df['century'] == cent
    axes[0].scatter(df.loc[mask, 'PC1'], df.loc[mask, 'PC2'],
                    c=[cent_colors[cent]], label=f'{cent}-talet',
                    alpha=0.6, s=30, edgecolors='white', linewidths=0.3)
axes[0].set_xlabel(f'PC1 ({var_explained[0]*100:.1f}%)')
axes[0].set_ylabel(f'PC2 ({var_explained[1]*100:.1f}%)')
axes[0].set_title('Fitnesslandskapet: Stolar i PCA-rom, farga etter hundreår')
axes[0].legend(fontsize=7, loc='best')

# Panel B: By origin
for orig, color in zip(['Noreg', 'Utanlands', 'Ukjent'], [COLORS[0], COLORS[1], COLORS[7]]):
    mask = df['origin'] == orig
    axes[1].scatter(df.loc[mask, 'PC1'], df.loc[mask, 'PC2'],
                    c=[color], label=orig, alpha=0.6, s=30,
                    edgecolors='white', linewidths=0.3)
axes[1].set_xlabel(f'PC1 ({var_explained[0]*100:.1f}%)')
axes[1].set_ylabel(f'PC2 ({var_explained[1]*100:.1f}%)')
axes[1].set_title('Fitnesslandskapet: Farga etter opphav')
axes[1].legend(fontsize=8)

plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, 'fig3_fitness_landscape_pca.png'))
plt.close()
print("→ Figur 3: fig3_fitness_landscape_pca.png")

# =================================================================
# 5. BEVIS 4: EXPLORATION vs EXPLOITATION-SYKLUSAR
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 4: Exploration vs Exploitation syklusar")
print("=" * 60)

# Measure form diversity (spread in geometric PCA) per 50-year period
diversity_by_period = []
for period in sorted(df['period_50'].unique()):
    mask = df['period_50'] == period
    n_period = mask.sum()
    if n_period < 3:
        continue
    subset = geom_scaled[mask.values]
    # Intra-period spread: mean pairwise distance
    if n_period > 1:
        dists = pdist(subset, metric='euclidean')
        mean_dist = np.mean(dists)
        std_dist = np.std(dists)
    else:
        mean_dist = 0
        std_dist = 0
    # Convex hull volume as diversity proxy (in PC space)
    pc_sub = pca_coords[mask.values, :3]
    spread = np.prod(np.ptp(pc_sub, axis=0)) if n_period >= 4 else 0

    diversity_by_period.append({
        'period': period,
        'n': n_period,
        'mean_pairwise_dist': float(mean_dist),
        'std_pairwise_dist': float(std_dist),
        'pc_spread': float(spread),
    })

div_df = pd.DataFrame(diversity_by_period)
div_df.to_csv(os.path.join(OUT_DATA, 'exploration_exploitation_cycles.csv'), index=False)

print("Formdiversitet per 50-årsperiode:")
for _, row in div_df.iterrows():
    bar = "█" * int(row['mean_pairwise_dist'] * 2)
    print(f"  {int(row['period']):4d}–{int(row['period'])+49:4d}  n={int(row['n']):3d}  "
          f"diversitet={row['mean_pairwise_dist']:.2f}  {bar}")

results['bevis4'] = {
    'periods': div_df.to_dict('records'),
}

# Figure: Exploration/Exploitation cycles
fig, ax1 = plt.subplots(figsize=(12, 5))
ax1.bar(div_df['period'], div_df['mean_pairwise_dist'],
        width=40, color=COLORS[2], alpha=0.7, label='Formdiversitet (snitt parvis avstand)')
ax1.set_xlabel('Tidsperiode (50 år)')
ax1.set_ylabel('Formdiversitet', color=COLORS[2])
ax1.tick_params(axis='y', labelcolor=COLORS[2])

ax2 = ax1.twinx()
ax2.plot(div_df['period'], div_df['n'], 'o-', color=COLORS[3], linewidth=2,
         markersize=5, label='Tal stolar i perioden')
ax2.set_ylabel('Tal stolar', color=COLORS[3])
ax2.tick_params(axis='y', labelcolor=COLORS[3])

fig.suptitle('Exploration → Exploitation-syklusar i stoldesign (1250–2020)', fontweight='bold')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, 'fig4_exploration_exploitation.png'))
plt.close()
print("→ Figur 4: fig4_exploration_exploitation.png")

# =================================================================
# 6. BEVIS 5: MATERIAL AFFORDANCE DIKTERER GEOMETRISK ROM
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 5: Materialaffordance dikterer geometrisk rom")
print("=" * 60)

# Compare geometric profiles of key material groups
key_materials = {
    'Mahogni': 'mat_Mahogni',
    'Eik': 'mat_Eik',
    'Furu': 'mat_Furu',
    'Bøk': 'mat_Bøk',
    'Kryssfiner': 'mat_Kryssfiner',
    'Stål': 'mat_Stål',
    'Bjørk': 'mat_Bjørk',
}

affordance_results = []
for mat_name, mat_col in key_materials.items():
    if mat_col not in df.columns:
        continue
    mask = df[mat_col] == 1
    if mask.sum() < 5:
        continue
    profile = {}
    profile['material'] = mat_name
    profile['n'] = int(mask.sum())
    for feat in ['compactness', 'symmetry_score', 'curv_mean', 'bbox_H', 'aspect_H_W']:
        profile[f'{feat}_mean'] = float(df.loc[mask, feat].mean())
        profile[f'{feat}_std'] = float(df.loc[mask, feat].std())
    affordance_results.append(profile)

aff_df = pd.DataFrame(affordance_results)
aff_df.to_csv(os.path.join(OUT_DATA, 'material_affordance_profiles.csv'), index=False)

print("\nGeometrisk profil per material:")
print(f"{'Material':12s} {'n':>4s} {'Kompaktheit':>12s} {'Symmetri':>10s} {'Kurvatur':>10s} {'Aspekt H/B':>12s}")
for _, row in aff_df.iterrows():
    print(f"{row['material']:12s} {row['n']:4.0f} "
          f"{row['compactness_mean']:12.3f} {row['symmetry_score_mean']:10.3f} "
          f"{row['curv_mean_mean']:10.3f} {row['aspect_H_W_mean']:12.3f}")

results['bevis5'] = aff_df.to_dict('records')

# Figure: Material affordance radar/bar chart
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
feats_to_plot = ['compactness_mean', 'symmetry_score_mean', 'curv_mean_mean']
feat_labels_aff = ['Kompaktheit', 'Symmetri', 'Kurvatur (snitt)']
for ax, feat, label in zip(axes, feats_to_plot, feat_labels_aff):
    bars = ax.barh(aff_df['material'], aff_df[feat], color=COLORS[:len(aff_df)])
    ax.set_xlabel(label)
    ax.set_title(label)
plt.suptitle('Materialaffordance: Kvart material dikterer eige geometrisk rom', fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, 'fig5_material_affordance.png'))
plt.close()
print("→ Figur 5: fig5_material_affordance.png")

# =================================================================
# 7. BEVIS 6: SELEKSJONSTRYKK ER KVANTIFISERBARE (MUTUAL INFORMATION)
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 6: Seleksjonstrykk er kvantifiserbare (informasjonsteori)")
print("=" * 60)

# Mutual information between categorical variables and form (discretized)
# Discretize geometric features into quintiles
geom_discrete = pd.DataFrame()
for feat in geom_cols:
    geom_discrete[feat] = pd.qcut(df[feat], q=5, labels=False, duplicates='drop')

# MI between origin and each geometric feature
mi_origin = {}
origin_encoded = LabelEncoder().fit_transform(df['origin'])
for feat in geom_cols:
    mi_origin[feat] = mutual_info_score(origin_encoded, geom_discrete[feat])

# MI between century and each geometric feature
mi_century = {}
century_encoded = LabelEncoder().fit_transform(df['century'])
for feat in geom_cols:
    mi_century[feat] = mutual_info_score(century_encoded, geom_discrete[feat])

# MI between dominant material and each geometric feature
# Get dominant material per chair
dom_mat = df[mat_cols].idxmax(axis=1)
dom_mat_encoded = LabelEncoder().fit_transform(dom_mat)
mi_material = {}
for feat in geom_cols:
    mi_material[feat] = mutual_info_score(dom_mat_encoded, geom_discrete[feat])

mi_df = pd.DataFrame({
    'feature': geom_cols,
    'MI_origin': [mi_origin[f] for f in geom_cols],
    'MI_century': [mi_century[f] for f in geom_cols],
    'MI_material': [mi_material[f] for f in geom_cols],
})
mi_df['MI_total'] = mi_df[['MI_origin', 'MI_century', 'MI_material']].sum(axis=1)
mi_df = mi_df.sort_values('MI_total', ascending=False)
mi_df.to_csv(os.path.join(OUT_DATA, 'mutual_information_seleksjonstrykk.csv'), index=False)

print("\nMutual Information: Seleksjonstrykk → Form")
print(f"{'Feature':20s} {'Opphav':>8s} {'Hundreår':>9s} {'Material':>9s} {'Totalt':>8s}")
for _, row in mi_df.iterrows():
    print(f"{row['feature']:20s} {row['MI_origin']:8.3f} {row['MI_century']:9.3f} "
          f"{row['MI_material']:9.3f} {row['MI_total']:8.3f}")

# Average MI per selection pressure
avg_mi = {
    'Geografi (opphav)': mi_df['MI_origin'].mean(),
    'Tid (hundreår)': mi_df['MI_century'].mean(),
    'Material': mi_df['MI_material'].mean(),
}
print(f"\nGjennomsnittleg MI per seleksjonstrykk:")
for name, val in sorted(avg_mi.items(), key=lambda x: -x[1]):
    print(f"  {name:20s}: {val:.4f}")

results['bevis6'] = {
    'avg_mi': avg_mi,
    'mi_table': mi_df.to_dict('records'),
}

# Figure: MI comparison
fig, ax = plt.subplots(figsize=(10, 6))
x = range(len(mi_df))
width = 0.25
ax.bar([i - width for i in x], mi_df['MI_material'], width, label='Material', color=COLORS[0])
ax.bar(x, mi_df['MI_century'], width, label='Hundreår', color=COLORS[1])
ax.bar([i + width for i in x], mi_df['MI_origin'], width, label='Opphav', color=COLORS[2])
ax.set_xticks(x)
ax.set_xticklabels(mi_df['feature'], rotation=45, ha='right', fontsize=7)
ax.set_ylabel('Mutual Information (bits)')
ax.set_title('Kva driv form? Mutual Information mellom seleksjonstrykk og geometri', fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, 'fig6_mutual_information.png'))
plt.close()
print("→ Figur 6: fig6_mutual_information.png")

# =================================================================
# 8. BEVIS 7: MULTIVARIATE PREDICTION – KVA FORKLARER FORM?
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 7: Random Forest – Kva predikerer form best?")
print("=" * 60)

# Task: Predict geometric cluster from different feature sets
# First, cluster the chairs geometrically
from sklearn.cluster import KMeans

# Find optimal k
inertias = []
K_range = range(2, 12)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(geom_scaled)
    inertias.append(km.inertia_)

# Use k=6 (reasonable for style periods)
km = KMeans(n_clusters=6, random_state=42, n_init=10)
df['form_cluster'] = km.fit_predict(geom_scaled)

# Now predict form_cluster from different feature sets
feature_sets = {
    'Berre material': mat_cols,
    'Berre hundreår': ['year'],
    'Material + hundreår': mat_cols + ['year'],
    'Material + hundreår + opphav': mat_cols + ['year'] + [f'origin_{o}' for o in ['Noreg', 'Utanlands']],
}

# Create origin dummies
for o in ['Noreg', 'Utanlands']:
    df[f'origin_{o}'] = (df['origin'] == o).astype(int)

prediction_results = []
for name, cols in feature_sets.items():
    valid_cols = [c for c in cols if c in df.columns]
    X = df[valid_cols].values
    y = df['form_cluster'].values
    clf = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=10)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(clf, X, y, cv=cv, scoring='f1_macro')
    prediction_results.append({
        'feature_set': name,
        'f1_mean': float(scores.mean()),
        'f1_std': float(scores.std()),
        'n_features': len(valid_cols),
    })
    print(f"  {name:40s}  F1={scores.mean():.3f} ± {scores.std():.3f}")

pred_df = pd.DataFrame(prediction_results)
pred_df.to_csv(os.path.join(OUT_DATA, 'form_prediction_results.csv'), index=False)
results['bevis7'] = pred_df.to_dict('records')

# =================================================================
# 9. BEVIS 8: TEMPORAL DRIFT – FITNESSLANDSKAPET ENDRAR SEG
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 8: Temporal drift – fitnesslandskapet endrar seg")
print("=" * 60)

# Track centroid of geometric features per 50-year period
centroids = []
for period in sorted(df['period_50'].unique()):
    mask = df['period_50'] == period
    n = mask.sum()
    if n < 3:
        continue
    centroid = df.loc[mask, geom_cols].mean()
    centroids.append({'period': period, 'n': n, **centroid.to_dict()})

cent_df = pd.DataFrame(centroids)

# Measure drift: distance between consecutive centroids
if len(cent_df) > 1:
    cent_vals = cent_df[geom_cols].values
    cent_scaled = StandardScaler().fit_transform(cent_vals)
    drifts = []
    for i in range(1, len(cent_scaled)):
        dist = np.linalg.norm(cent_scaled[i] - cent_scaled[i-1])
        drifts.append({
            'from': int(cent_df.iloc[i-1]['period']),
            'to': int(cent_df.iloc[i]['period']),
            'drift': float(dist),
        })
    drift_df = pd.DataFrame(drifts)
    drift_df.to_csv(os.path.join(OUT_DATA, 'temporal_drift.csv'), index=False)

    print("Drift mellom 50-årsperiodar (euklidisk avstand i standardisert rom):")
    for _, row in drift_df.iterrows():
        bar = "█" * int(row['drift'] * 3)
        print(f"  {int(row['from']):4d}→{int(row['to']):4d}  drift={row['drift']:.3f}  {bar}")

    # Figure: Temporal drift
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(drift_df['to'], drift_df['drift'], 'o-', color=COLORS[4], linewidth=2, markersize=8)
    ax.fill_between(drift_df['to'], drift_df['drift'], alpha=0.2, color=COLORS[4])
    ax.set_xlabel('Tidsperiode')
    ax.set_ylabel('Drift (euklidisk avstand mellom sentriodar)')
    ax.set_title('Temporal drift: Kor fort endrar fitnesslandskapet seg?', fontweight='bold')
    # Mark key events
    events = {1800: 'Mahogni-\ntoppen', 1850: 'Industrialisering', 1950: 'Etterkrigstid'}
    for yr, label in events.items():
        if yr >= drift_df['to'].min() and yr <= drift_df['to'].max():
            ax.axvline(yr, color='gray', linestyle=':', alpha=0.5)
            ax.text(yr, ax.get_ylim()[1]*0.9, label, ha='center', fontsize=7, color='gray')
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_FIG, 'fig7_temporal_drift.png'))
    plt.close()
    print("→ Figur 7: fig7_temporal_drift.png")
    results['bevis8'] = drift_df.to_dict('records')

# =================================================================
# 10. BEVIS 9: KONVERGENS – ULIKE MATERIALAR → SAME FORM
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 9: Konvergens – ulike materialar konvergerer mot same form")
print("=" * 60)

# In industrial era (post-1900), do different materials converge in form space?
pre_1900 = df[df['year'] < 1900]
post_1900 = df[df['year'] >= 1900]

# Intra-material variance before and after industrialization
convergence_results = []
for mat_name, mat_col in key_materials.items():
    if mat_col not in df.columns:
        continue
    for label, subset in [('Før 1900', pre_1900), ('Etter 1900', post_1900)]:
        mask = subset[mat_col] == 1
        if mask.sum() < 3:
            continue
        geom_sub = subset.loc[mask, geom_cols].values
        geom_sub_s = StandardScaler().fit_transform(geom_sub) if len(geom_sub) > 1 else geom_sub
        intra_var = np.mean(np.var(geom_sub_s, axis=0)) if len(geom_sub) > 1 else 0
        convergence_results.append({
            'material': mat_name,
            'period': label,
            'n': int(mask.sum()),
            'intra_variance': float(intra_var),
        })

conv_df = pd.DataFrame(convergence_results)
conv_df.to_csv(os.path.join(OUT_DATA, 'convergence_analysis.csv'), index=False)

if len(conv_df) > 0:
    print(f"{'Material':12s} {'Periode':>12s} {'n':>4s} {'Intra-varians':>14s}")
    for _, row in conv_df.iterrows():
        print(f"{row['material']:12s} {row['period']:>12s} {row['n']:4.0f} {row['intra_variance']:14.3f}")
results['bevis9'] = conv_df.to_dict('records')

# =================================================================
# 11. BEVIS 10: STILPERIODE ER EMERGENT, IKKJE KAUSAL
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 10: Stil er emergent – spring i fitnesslandskapet")
print("=" * 60)

# Compare: Can we predict style from form+material?
# vs: Can we predict form from style alone?
# If style is emergent from fitness, then material+time should predict form
# better than style label alone.

# Filter to chairs with known style
df_styled = df[df['stil'] != 'Ukjent'].copy()
if len(df_styled) > 20:
    # Encode style
    le_style = LabelEncoder()
    style_encoded = le_style.fit_transform(df_styled['stil'])

    # A) Predict form cluster from style label alone
    X_style = style_encoded.reshape(-1, 1)
    y_cluster = df_styled['form_cluster'].values

    clf_a = RandomForestClassifier(n_estimators=200, random_state=42)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    try:
        score_a = cross_val_score(clf_a, X_style, y_cluster, cv=cv, scoring='f1_macro')
        print(f"  Stil → Form-kluster:      F1 = {score_a.mean():.3f} ± {score_a.std():.3f}")
    except:
        score_a = np.array([0])
        print("  Stil → Form-kluster:      Kunne ikkje evaluerast")

    # B) Predict form cluster from material + time
    X_mat_time = df_styled[mat_cols + ['year']].values
    clf_b = RandomForestClassifier(n_estimators=200, random_state=42)
    try:
        score_b = cross_val_score(clf_b, X_mat_time, y_cluster, cv=cv, scoring='f1_macro')
        print(f"  Material+Tid → Form-kluster: F1 = {score_b.mean():.3f} ± {score_b.std():.3f}")
    except:
        score_b = np.array([0])
        print("  Material+Tid → Form-kluster: Kunne ikkje evaluerast")

    results['bevis10'] = {
        'style_to_form_f1': float(score_a.mean()),
        'mattime_to_form_f1': float(score_b.mean()),
        'n_styled': len(df_styled),
    }

# =================================================================
# 12. BEVIS 11: NOREG SOM MIKROKOSOM – SAME MØNSTER, ANNA SKALA
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 11: Noreg som mikrokomos av det globale fitnesskartet")
print("=" * 60)

nor = df[df['origin'] == 'Noreg']
uta = df[df['origin'] == 'Utanlands']

print(f"  Norske stolar: {len(nor)}")
print(f"  Utanlandske stolar: {len(uta)}")

if len(nor) > 5 and len(uta) > 5:
    # Compare geometric centroids
    nor_centroid = nor[geom_cols].mean()
    uta_centroid = uta[geom_cols].mean()
    diff = (nor_centroid - uta_centroid).abs()

    print("\n  Geometrisk samanlikning (norsk vs utanlandsk):")
    for feat in ['compactness', 'symmetry_score', 'curv_mean', 'aspect_H_W', 'bbox_H']:
        n_val = nor[feat].mean()
        u_val = uta[feat].mean()
        t_stat, p_val = stats.ttest_ind(nor[feat], uta[feat])
        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
        print(f"    {feat:20s}  Noreg={n_val:.3f}  Utland={u_val:.3f}  p={p_val:.4f} {sig}")

    results['bevis11'] = {
        'n_noreg': len(nor),
        'n_utanlands': len(uta),
    }

# Figure: Norway vs Foreign in fitness landscape
if len(nor) > 5:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(uta['PC1'], uta['PC2'], c=[COLORS[1]], alpha=0.4, s=25, label=f'Utanlands (n={len(uta)})')
    ax.scatter(nor['PC1'], nor['PC2'], c=[COLORS[0]], alpha=0.6, s=35, label=f'Noreg (n={len(nor)})')
    ax.set_xlabel(f'PC1 ({var_explained[0]*100:.1f}%)')
    ax.set_ylabel(f'PC2 ({var_explained[1]*100:.1f}%)')
    ax.set_title('Noreg som mikrokomos i fitnesslandskapet', fontweight='bold')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_FIG, 'fig8_noreg_vs_utland.png'))
    plt.close()
    print("→ Figur 8: fig8_noreg_vs_utland.png")

# =================================================================
# 13. BEVIS 12: MATERIALENTROPIEN FØLGJER POLITISKE SJOKK
# =================================================================
print("\n" + "=" * 60)
print("BEVIS 12: Materialentropi → politiske og økonomiske sjokk")
print("=" * 60)

# Shannon entropy of material distribution per period
entropy_by_period = []
for period in sorted(df['period_50'].unique()):
    mask = df['period_50'] == period
    n = mask.sum()
    if n < 3:
        continue
    mat_sums = df.loc[mask, mat_cols].sum()
    mat_probs = mat_sums / mat_sums.sum()
    mat_probs = mat_probs[mat_probs > 0]
    entropy = -np.sum(mat_probs * np.log2(mat_probs))
    n_materials_used = (mat_sums > 0).sum()
    entropy_by_period.append({
        'period': period,
        'n': n,
        'entropy': float(entropy),
        'n_materials': int(n_materials_used),
    })

ent_df = pd.DataFrame(entropy_by_period)
ent_df.to_csv(os.path.join(OUT_DATA, 'material_entropy.csv'), index=False)

print(f"{'Periode':>8s} {'n':>4s} {'Entropi':>8s} {'Materialar':>10s}")
for _, row in ent_df.iterrows():
    bar = "█" * int(row['entropy'] * 2)
    print(f"  {int(row['period']):4d}    {int(row['n']):4d} {row['entropy']:8.2f} {int(row['n_materials']):10d}  {bar}")

results['bevis12'] = ent_df.to_dict('records')

# Figure: Material entropy over time
fig, ax1 = plt.subplots(figsize=(12, 5))
ax1.plot(ent_df['period'], ent_df['entropy'], 'o-', color=COLORS[5], linewidth=2, markersize=8)
ax1.fill_between(ent_df['period'], ent_df['entropy'], alpha=0.2, color=COLORS[5])
ax1.set_xlabel('Tidsperiode')
ax1.set_ylabel('Shannon-entropi (materialdistribusjon)', color=COLORS[5])
ax1.set_title('Materialentropi over tid: Kompleksiteten i fitnesslandskapet', fontweight='bold')

# Mark historical events
events = {
    1650: 'Merkantilismen',
    1800: 'Napoleonskrigane',
    1850: 'Industriell\nrevolusjon',
    1900: 'Jugend',
    1950: 'Etterkrigstid',
}
for yr, label in events.items():
    if yr >= ent_df['period'].min() and yr <= ent_df['period'].max():
        ax1.axvline(yr, color='gray', linestyle=':', alpha=0.5)
        ax1.text(yr, ax1.get_ylim()[1]*0.95, label, ha='center', fontsize=7,
                 color='gray', rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUT_FIG, 'fig9_material_entropy.png'))
plt.close()
print("→ Figur 9: fig9_material_entropy.png")

# =================================================================
# 14. SAVE ALL RESULTS
# =================================================================
with open(os.path.join(OUT_DATA, 'fff_results_summary.json'), 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)

print("\n" + "=" * 60)
print("ALLE ANALYSAR FULLFØRTE")
print("=" * 60)
print(f"\nResultat lagra i: {OUT_DATA}")
print(f"Figurar lagra i: {OUT_FIG}")
print(f"\nTotalt {N} stolar analyserte over {len(results)} empiriske bevis.")
print("\nFigurar genererte:")
for f_name in sorted(os.listdir(OUT_FIG)):
    if f_name.endswith('.png'):
        print(f"  {f_name}")
