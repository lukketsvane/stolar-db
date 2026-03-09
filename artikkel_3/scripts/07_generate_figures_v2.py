"""
07_generate_figures_v2.py
Generate all 7 figures for the improved Article 3.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import umap
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import silhouette_score

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.15
})

STYLE_ORDER = ['Renessanse', 'Barokk', 'Rokokko', 'Nyklassisisme', 'Historisme', 'Jugend', 'Modernisme', 'Postmodernisme']
STYLE_COLORS = sns.color_palette("husl", 8)
STYLE_CMAP = dict(zip(STYLE_ORDER, STYLE_COLORS))


def main():
    data_dir = '../data'
    out_dir = '../figurar'
    os.makedirs(out_dir, exist_ok=True)

    # Load data
    df_umap = pd.read_csv(os.path.join(data_dir, 'umap_data.csv'))
    df_cv = pd.read_csv(os.path.join(data_dir, 'cv_detailed_results.csv'))
    df_class_dist = pd.read_csv(os.path.join(data_dir, 'class_distribution.csv'))
    df_per_class = pd.read_csv(os.path.join(data_dir, 'per_class_f1.csv'))
    df_corr = pd.read_csv(os.path.join(data_dir, 'feature_correlation.csv'))
    df_sil = pd.read_csv(os.path.join(data_dir, 'silhouette_scores.csv'))
    cm = np.load(os.path.join(data_dir, 'style_confusion_matrix.npy'))
    classes = np.load(os.path.join(data_dir, 'style_classes.npy'), allow_pickle=True)

    # ---- Fig 1: UMAP with contours + silhouette annotation ----
    geo_cols = [c for c in df_umap.columns if c not in ['objectId', 'style_group']]
    X = df_umap[geo_cols].values
    X_scaled = StandardScaler().fit_transform(X)

    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42)
    embedding = reducer.fit_transform(X_scaled)

    labels_enc = LabelEncoder().fit_transform(df_umap['style_group'].values)
    sil_21d = df_sil.loc[df_sil['Dimensjon'] == '21D (originalt)', 'Silhouette'].values[0]

    fig, ax = plt.subplots(figsize=(8, 6))
    for style in STYLE_ORDER:
        idx = df_umap['style_group'] == style
        if idx.sum() == 0:
            continue
        ax.scatter(embedding[idx, 0], embedding[idx, 1],
                   label=style, color=STYLE_CMAP[style], alpha=0.7, s=40,
                   edgecolors='w', linewidth=0.5)
        # Add KDE contour per style if enough points
        if idx.sum() >= 5:
            try:
                from scipy.stats import gaussian_kde
                pts = embedding[idx]
                kde = gaussian_kde(pts.T, bw_method=0.5)
                xmin, xmax = embedding[:, 0].min() - 1, embedding[:, 0].max() + 1
                ymin, ymax = embedding[:, 1].min() - 1, embedding[:, 1].max() + 1
                xx, yy = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
                zz = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
                ax.contour(xx, yy, zz, levels=1, colors=[STYLE_CMAP[style]], alpha=0.4, linewidths=1)
            except Exception:
                pass

    ax.text(0.02, 0.98, f'Silhouette (21D) = {sil_21d:.3f}',
            transform=ax.transAxes, va='top', fontsize=9,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    ax.legend(title="Stilperiode", bbox_to_anchor=(1.05, 1), loc='upper left', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig1_formrom.pdf'))
    plt.savefig(os.path.join(out_dir, 'fig1_formrom.png'))
    plt.close()
    print("Fig 1 saved.")

    # ---- Fig 2: Class distribution bar chart ----
    df_cd = df_class_dist.copy()
    # Reorder by STYLE_ORDER
    df_cd['sort'] = df_cd['Stilgruppe'].map({s: i for i, s in enumerate(STYLE_ORDER)})
    df_cd = df_cd.sort_values('sort')

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(df_cd['Stilgruppe'], df_cd['Antal'],
                  color=[STYLE_CMAP.get(s, 'gray') for s in df_cd['Stilgruppe']],
                  edgecolor='white', linewidth=0.5)
    for bar, val in zip(bars, df_cd['Antal']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                str(val), ha='center', va='bottom', fontsize=9)
    ax.set_ylabel("Antal stolar")
    ax.set_xlabel("Stilgruppe")
    ax.tick_params(axis='x', rotation=30)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig2_klassefordeling.pdf'))
    plt.savefig(os.path.join(out_dir, 'fig2_klassefordeling.png'))
    plt.close()
    print("Fig 2 saved.")

    # ---- Fig 3: Classification results with error bars ----
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), sharey=True)

    for i, task in enumerate(['Stil', 'Nasjon']):
        ax = axes[i]
        subset = df_cv[df_cv['Eksperiment'].str.startswith(task)]
        labels = [e.split('/')[1] for e in subset['Eksperiment']]
        x = np.arange(len(labels))
        colors = ['#2196F3', '#4CAF50', '#FF9800']

        bars = ax.bar(x, subset['F1_mean'].values, yerr=subset['F1_std'].values,
                      capsize=4, color=colors, edgecolor='white', linewidth=0.5)
        for bar, val, std in zip(bars, subset['F1_mean'], subset['F1_std']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + std + 0.02,
                    f'{val:.1%}', ha='center', va='bottom', fontsize=9)

        chance = subset['Chance_F1'].values[0]
        ax.axhline(chance, color='gray', linestyle='--', alpha=0.7)
        ax.text(len(labels)-0.5, chance + 0.02, f'Sjanse: {chance:.1%}', color='gray', fontsize=8, ha='right')

        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, 1.0)
        ax.set_title(f'{task}prediksjon')
        if i == 0:
            ax.set_ylabel("Makro F1-score")

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig3_klassifikasjon.pdf'))
    plt.savefig(os.path.join(out_dir, 'fig3_klassifikasjon.png'))
    plt.close()
    print("Fig 3 saved.")

    # ---- Fig 4: Confusion matrix (kept, improved) ----
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    # Reorder to STYLE_ORDER
    class_list = list(classes)
    order_idx = [class_list.index(s) for s in STYLE_ORDER if s in class_list]
    cm_ordered = cm_norm[np.ix_(order_idx, order_idx)]
    classes_ordered = [STYLE_ORDER[i] for i, s in enumerate(STYLE_ORDER) if s in class_list]

    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(cm_ordered, annot=True, fmt=".2f", cmap="Blues",
                xticklabels=classes_ordered, yticklabels=classes_ordered, ax=ax,
                cbar_kws={'label': 'Andel'})
    ax.set_xlabel("Predikert stil")
    ax.set_ylabel("Faktisk stil")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig4_forvirring.pdf'))
    plt.savefig(os.path.join(out_dir, 'fig4_forvirring.png'))
    plt.close()
    print("Fig 4 saved.")

    # ---- Fig 5: Per-class F1 grouped bars ----
    fig, ax = plt.subplots(figsize=(10, 5))
    df_pc = df_per_class.copy()
    # Reorder styles
    df_pc['sort'] = df_pc['Stilgruppe'].map({s: i for i, s in enumerate(STYLE_ORDER)})
    df_pc = df_pc.sort_values(['sort', 'Trekksett'])

    trekksett = ['Geometri', 'Material', 'Kombinert']
    x = np.arange(len(STYLE_ORDER))
    width = 0.25
    colors = ['#2196F3', '#4CAF50', '#FF9800']

    for i, ts in enumerate(trekksett):
        vals = []
        for s in STYLE_ORDER:
            row = df_pc[(df_pc['Stilgruppe'] == s) & (df_pc['Trekksett'] == ts)]
            vals.append(row['F1'].values[0] if len(row) > 0 else 0)
        ax.bar(x + i*width, vals, width, label=ts, color=colors[i], edgecolor='white', linewidth=0.5)

    ax.set_xticks(x + width)
    ax.set_xticklabels(STYLE_ORDER, rotation=30, ha='right')
    ax.set_ylabel("F1-score")
    ax.set_ylim(0, 1.0)
    ax.legend(title="Trekksett")
    ax.axhline(0.125, color='gray', linestyle=':', alpha=0.5, label='Tilfeldig')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig5_perklasse_f1.pdf'))
    plt.savefig(os.path.join(out_dir, 'fig5_perklasse_f1.png'))
    plt.close()
    print("Fig 5 saved.")

    # ---- Fig 6: Feature correlation heatmap (geo x mat top features) ----
    # Load full data for correlation matrix
    df_geo_raw = pd.read_csv(os.path.join(data_dir, 'features_geometric.csv'))
    df_mat_raw = pd.read_csv(os.path.join(data_dir, 'features_material.csv'))
    df_merged = df_geo_raw.merge(df_mat_raw, on='objectId', how='inner')

    geo_feats = [c for c in df_geo_raw.columns if c != 'objectId']
    # Top 10 mat features by variance
    mat_feats_all = [c for c in df_mat_raw.columns if c != 'objectId']
    mat_var = df_merged[mat_feats_all].var().sort_values(ascending=False)
    mat_top = mat_var.head(12).index.tolist()

    cross = df_merged[geo_feats + mat_top].corr().loc[geo_feats, mat_top]

    fig, ax = plt.subplots(figsize=(10, 7))
    sns.heatmap(cross, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                ax=ax, cbar_kws={'label': 'Pearson r'},
                xticklabels=[c.replace('mat_', '') for c in mat_top],
                yticklabels=geo_feats)
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig6_korrelasjon.pdf'))
    plt.savefig(os.path.join(out_dir, 'fig6_korrelasjon.png'))
    plt.close()
    print("Fig 6 saved.")

    # ---- Fig 7: Feature importance dual panel (style + nation) ----
    df_imp_nation = pd.read_csv(os.path.join(data_dir, 'feature_importance_nation.csv'))
    df_imp_style = pd.read_csv(os.path.join(data_dir, 'feature_importance_style.csv'))

    name_map = {
        'h_dist_top': 'Topp-fordeling', 'h_dist_mid': 'Midtfordeling',
        'h_dist_bottom': 'Botnfordeling',
        'd2_bin_1': 'D2 Bin 1', 'd2_bin_2': 'D2 Bin 2', 'd2_bin_3': 'D2 Bin 3',
        'd2_bin_4': 'D2 Bin 4', 'd2_bin_5': 'D2 Bin 5',
        'curv_std': 'Krumming (std)', 'curv_mean': 'Krumming (snitt)',
        'curv_skew': 'Krumming (skeiv.)',
        'bbox_D': 'Djupn', 'bbox_H': 'Høgde', 'bbox_W': 'Breidde',
        'pca_l2_l1': 'PCA λ2/λ1', 'pca_l3_l1': 'PCA λ3/λ1',
        'symmetry_score': 'Symmetri', 'surface_ratio': 'Overflateratio',
        'compactness': 'Kompaktheit',
        'aspect_H_W': 'Aspekt H/B', 'aspect_D_W': 'Aspekt D/B',
    }
    for c in mat_feats_all:
        name_map[c] = c.replace('mat_', 'Mat: ')

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    for ax, df_imp, title in [(axes[0], df_imp_style, 'Stilprediksjon'),
                               (axes[1], df_imp_nation, 'Nasjonsprediksjon')]:
        top15 = df_imp.head(15).copy()
        top15['Label'] = top15['Feature'].map(lambda x: name_map.get(x, x))
        # Color by type
        colors = ['#2196F3' if not f.startswith('mat_') else '#4CAF50' for f in top15['Feature']]
        ax.barh(range(len(top15)-1, -1, -1), top15['Importance'].values, color=colors)
        ax.set_yticks(range(len(top15)-1, -1, -1))
        ax.set_yticklabels(top15['Label'].values)
        ax.set_xlabel("Gini-importance")
        ax.set_title(title)

    # Legend
    from matplotlib.patches import Patch
    axes[1].legend(handles=[Patch(color='#2196F3', label='Geometri'),
                            Patch(color='#4CAF50', label='Material')],
                   loc='lower right')

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig7_kopling.pdf'))
    plt.savefig(os.path.join(out_dir, 'fig7_kopling.png'))
    plt.close()
    print("Fig 7 saved.")

    print("\nAll 7 figures saved to ../figurar/")


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
