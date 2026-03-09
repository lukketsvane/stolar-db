"""
04_extended_analysis.py
Extended analyses for Article 3:
A) Class distribution
B) Per-class F1 (precision/recall/F1 per style, all 3 feature sets)
C) Correlation analysis (Pearson between geo and mat features)
D) Feature ablation (leave-one-out F1-drop for geometry->style)
E) Nation-style confound (chi-square)
F) UMAP silhouette scores (21D and 2D)
G) CV standard deviations (5-fold for all 6 experiments)
H) Combined underperformance analysis (top-K MI feature selection)
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate, cross_val_predict, permutation_test_score
from sklearn.metrics import f1_score, classification_report, silhouette_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import mutual_info_classif
from scipy.stats import chi2_contingency, pearsonr
import umap
import warnings

warnings.filterwarnings('ignore')

STYLE_MAPPING = {
    'Renessanse': 'Renessanse', 'Middelalder': 'Renessanse',
    'Barokk': 'Barokk', 'Régence': 'Barokk', 'Queen Anne': 'Barokk',
    'Rokokko': 'Rokokko', 'Chippendale': 'Rokokko',
    'Empire': 'Nyklassisisme', 'Louis XVI': 'Nyklassisisme', 'Hepplewhite': 'Nyklassisisme',
    'Regency': 'Nyklassisisme', 'Sheraton': 'Nyklassisisme', 'Nyklassisisme': 'Nyklassisisme',
    'Klassisisme': 'Nyklassisisme', 'Biedermeier': 'Nyklassisisme',
    'Historisme': 'Historisme', 'Nyrokokko': 'Historisme', 'Nybarokk': 'Historisme', 'Dragestil': 'Historisme',
    'Art Nouveau': 'Jugend', 'Jugend': 'Jugend', 'Art Nouveau (Jugend)': 'Jugend',
    'Modernisme': 'Modernisme', 'Scandinavian Design': 'Modernisme',
    'Etterkrigsmodernisme': 'Modernisme', 'Funksjonalisme': 'Modernisme',
    'Postmodernisme': 'Postmodernisme'
}


def load_data():
    data_dir = '../data'
    df_meta = pd.read_csv(os.path.join(data_dir, 'metadata.csv'))
    df_geo = pd.read_csv(os.path.join(data_dir, 'features_geometric.csv'))
    df_mat = pd.read_csv(os.path.join(data_dir, 'features_material.csv'))

    df = df_geo.merge(df_mat, on='objectId', how='inner')
    df = df.merge(df_meta[['objectId', 'stilperiode', 'produksjonsstad']], on='objectId', how='inner')

    geo_cols = [c for c in df.columns if c.startswith(('pca_', 'bbox_', 'aspect_', 'compactness', 'surface_', 'symmetry_', 'h_dist_', 'curv_', 'd2_'))]
    mat_cols = [c for c in df.columns if c.startswith('mat_')]

    return df, geo_cols, mat_cols


def prepare_style(df):
    df_style = df.copy()
    df_style['style_group'] = df_style['stilperiode'].map(STYLE_MAPPING)
    df_style = df_style.dropna(subset=['style_group'])
    return df_style


def prepare_nation(df):
    df_nation = df.dropna(subset=['produksjonsstad']).copy()
    df_nation = df_nation[df_nation['produksjonsstad'] != '']
    df_nation['is_norway'] = df_nation['produksjonsstad'].apply(lambda x: 1 if 'Norge' in str(x) else 0)
    return df_nation


def analysis_A_class_distribution(df_style):
    """A: Class distribution — number of chairs per style group."""
    dist = df_style['style_group'].value_counts().reset_index()
    dist.columns = ['Stilgruppe', 'Antal']
    dist = dist.sort_values('Antal', ascending=False)
    dist.to_csv('../data/class_distribution.csv', index=False)
    print("A) Class distribution:")
    print(dist.to_string(index=False))
    return dist


def analysis_B_per_class_f1(df_style, geo_cols, mat_cols):
    """B: Per-class F1 for all 3 feature sets (geometry, material, combined)."""
    y = df_style['style_group'].values
    classes = sorted(df_style['style_group'].unique())

    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    results = []
    for name, X in [('Geometri', df_style[geo_cols].values),
                     ('Material', df_style[mat_cols].values),
                     ('Kombinert', df_style[geo_cols + mat_cols].values)]:
        y_pred = cross_val_predict(clf, X, y, cv=cv)
        report = classification_report(y, y_pred, output_dict=True, zero_division=0)
        for cls in classes:
            if cls in report:
                results.append({
                    'Trekksett': name,
                    'Stilgruppe': cls,
                    'Precision': round(report[cls]['precision'], 3),
                    'Recall': round(report[cls]['recall'], 3),
                    'F1': round(report[cls]['f1-score'], 3),
                    'Support': report[cls]['support']
                })

    df_result = pd.DataFrame(results)
    df_result.to_csv('../data/per_class_f1.csv', index=False)
    print("\nB) Per-class F1:")
    print(df_result.to_string(index=False))
    return df_result


def analysis_C_correlation(df, geo_cols, mat_cols):
    """C: Pearson correlation between geo and mat features, plus inter-set max |r|."""
    df_clean = df[geo_cols + mat_cols].dropna()

    # Full correlation matrix
    corr_matrix = df_clean.corr(method='pearson')

    # Extract cross-set correlations (geo x mat)
    cross_corr = corr_matrix.loc[geo_cols, mat_cols]

    # For each geo feature, find the max |r| with any mat feature
    rows = []
    for g in geo_cols:
        max_r = cross_corr.loc[g].abs().max()
        best_mat = cross_corr.loc[g].abs().idxmax()
        actual_r = cross_corr.loc[g, best_mat]
        rows.append({
            'Geo_feature': g,
            'Best_mat_feature': best_mat,
            'Pearson_r': round(actual_r, 3),
            'Abs_r': round(max_r, 3)
        })

    df_corr = pd.DataFrame(rows).sort_values('Abs_r', ascending=False)
    df_corr.to_csv('../data/feature_correlation.csv', index=False)

    mean_abs_r = df_corr['Abs_r'].mean()
    max_abs_r = df_corr['Abs_r'].max()
    print(f"\nC) Cross-set correlation: mean max|r| = {mean_abs_r:.3f}, global max|r| = {max_abs_r:.3f}")
    print(df_corr.head(10).to_string(index=False))
    return df_corr


def analysis_D_ablation(df_style, geo_cols):
    """D: Leave-one-out feature ablation for geometry->style."""
    y = df_style['style_group'].values
    X_full = df_style[geo_cols].values
    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Baseline
    baseline_scores = cross_validate(clf, X_full, y, cv=cv, scoring='f1_macro')
    baseline_f1 = np.mean(baseline_scores['test_score'])

    rows = []
    for i, col in enumerate(geo_cols):
        X_reduced = np.delete(X_full, i, axis=1)
        scores = cross_validate(clf, X_reduced, y, cv=cv, scoring='f1_macro')
        reduced_f1 = np.mean(scores['test_score'])
        drop = baseline_f1 - reduced_f1
        rows.append({
            'Feature': col,
            'Baseline_F1': round(baseline_f1, 4),
            'Reduced_F1': round(reduced_f1, 4),
            'F1_drop': round(drop, 4)
        })

    df_abl = pd.DataFrame(rows).sort_values('F1_drop', ascending=False)
    df_abl.to_csv('../data/ablation_style.csv', index=False)
    print(f"\nD) Feature ablation (baseline F1 = {baseline_f1:.4f}):")
    print(df_abl.head(10).to_string(index=False))
    return df_abl


def analysis_E_nation_style_confound(df):
    """E: Nation-style confound — crosstab + chi-square test."""
    df_both = df.dropna(subset=['stilperiode', 'produksjonsstad']).copy()
    df_both['style_group'] = df_both['stilperiode'].map(STYLE_MAPPING)
    df_both = df_both.dropna(subset=['style_group'])
    df_both['is_norway'] = df_both['produksjonsstad'].apply(lambda x: 'Noreg' if 'Norge' in str(x) else 'Utland')

    ct = pd.crosstab(df_both['style_group'], df_both['is_norway'])
    chi2, p, dof, expected = chi2_contingency(ct)

    ct_out = ct.copy()
    ct_out['Total'] = ct_out.sum(axis=1)
    ct_out.loc['Total'] = ct_out.sum()
    ct_out.to_csv('../data/nation_style_confound.csv')

    print(f"\nE) Nation-style confound: chi² = {chi2:.2f}, dof = {dof}, p = {p:.4f}")
    print(ct)
    return chi2, p, dof


def analysis_F_silhouette(df_style, geo_cols):
    """F: Silhouette scores in 21D and UMAP-2D."""
    X = df_style[geo_cols].values
    X_scaled = StandardScaler().fit_transform(X)
    labels = LabelEncoder().fit_transform(df_style['style_group'].values)

    # 21D silhouette
    sil_21d = silhouette_score(X_scaled, labels)

    # UMAP 2D
    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42)
    X_2d = reducer.fit_transform(X_scaled)
    sil_2d = silhouette_score(X_2d, labels)

    result = pd.DataFrame([
        {'Dimensjon': '21D (originalt)', 'Silhouette': round(sil_21d, 4)},
        {'Dimensjon': '2D (UMAP)', 'Silhouette': round(sil_2d, 4)}
    ])
    result.to_csv('../data/silhouette_scores.csv', index=False)
    print(f"\nF) Silhouette scores: 21D = {sil_21d:.4f}, UMAP-2D = {sil_2d:.4f}")
    return sil_21d, sil_2d


def analysis_G_cv_detailed(df_style, df_nation, geo_cols, mat_cols):
    """G: Detailed CV results with std for all 6 experiments."""
    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    experiments = []
    # Style experiments
    y_style = df_style['style_group'].values
    for name, X in [('Stil/Geometri', df_style[geo_cols].values),
                     ('Stil/Material', df_style[mat_cols].values),
                     ('Stil/Kombinert', df_style[geo_cols + mat_cols].values)]:
        results = cross_validate(clf, X, y_style, cv=cv,
                                 scoring={'f1_macro': 'f1_macro', 'accuracy': 'accuracy'},
                                 return_train_score=False)
        # Permutation test
        score, perm_scores, pvalue = permutation_test_score(
            clf, X, y_style, scoring='f1_macro', cv=cv, n_permutations=50, n_jobs=-1, random_state=42
        )
        experiments.append({
            'Eksperiment': name,
            'F1_mean': round(np.mean(results['test_f1_macro']), 4),
            'F1_std': round(np.std(results['test_f1_macro']), 4),
            'Acc_mean': round(np.mean(results['test_accuracy']), 4),
            'Acc_std': round(np.std(results['test_accuracy']), 4),
            'Chance_F1': round(np.mean(perm_scores), 4),
            'P_value': round(pvalue, 4)
        })

    # Nation experiments
    y_nation = df_nation['is_norway'].values
    for name, X in [('Nasjon/Geometri', df_nation[geo_cols].values),
                     ('Nasjon/Material', df_nation[mat_cols].values),
                     ('Nasjon/Kombinert', df_nation[geo_cols + mat_cols].values)]:
        results = cross_validate(clf, X, y_nation, cv=cv,
                                 scoring={'f1_macro': 'f1_macro', 'accuracy': 'accuracy'},
                                 return_train_score=False)
        score, perm_scores, pvalue = permutation_test_score(
            clf, X, y_nation, scoring='f1_macro', cv=cv, n_permutations=50, n_jobs=-1, random_state=42
        )
        experiments.append({
            'Eksperiment': name,
            'F1_mean': round(np.mean(results['test_f1_macro']), 4),
            'F1_std': round(np.std(results['test_f1_macro']), 4),
            'Acc_mean': round(np.mean(results['test_accuracy']), 4),
            'Acc_std': round(np.std(results['test_accuracy']), 4),
            'Chance_F1': round(np.mean(perm_scores), 4),
            'P_value': round(pvalue, 4)
        })

    df_cv = pd.DataFrame(experiments)
    df_cv.to_csv('../data/cv_detailed_results.csv', index=False)
    print("\nG) Detailed CV results:")
    print(df_cv.to_string(index=False))
    return df_cv


def analysis_H_combined_underperformance(df_style, geo_cols, mat_cols):
    """H: Feature-selected combined (top-K MI) to explain paradox."""
    y = df_style['style_group'].values
    X_all = df_style[geo_cols + mat_cols].values
    all_cols = geo_cols + mat_cols

    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Mutual information for feature selection
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    mi = mutual_info_classif(X_all, y_encoded, random_state=42)

    mi_df = pd.DataFrame({'Feature': all_cols, 'MI': mi}).sort_values('MI', ascending=False)

    rows = []
    for K in [10, 15, 20, 25, 30, 35, 40, 51]:
        top_k = mi_df.head(K)['Feature'].tolist()
        col_idx = [all_cols.index(c) for c in top_k]
        X_sel = X_all[:, col_idx]
        scores = cross_validate(clf, X_sel, y, cv=cv, scoring='f1_macro')
        f1 = np.mean(scores['test_score'])

        n_geo = sum(1 for c in top_k if c in geo_cols)
        n_mat = sum(1 for c in top_k if c in mat_cols)
        rows.append({
            'Top_K': K,
            'N_geo': n_geo,
            'N_mat': n_mat,
            'F1_macro': round(f1, 4)
        })

    df_comb = pd.DataFrame(rows)
    df_comb.to_csv('../data/combined_analysis.csv', index=False)
    print("\nH) Combined underperformance analysis:")
    print(df_comb.to_string(index=False))

    # Also save feature importance for style prediction
    clf_style = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
    clf_style.fit(df_style[geo_cols + mat_cols], y)
    imp = clf_style.feature_importances_
    imp_df = pd.DataFrame({'Feature': all_cols, 'Importance': imp}).sort_values('Importance', ascending=False)
    imp_df.to_csv('../data/feature_importance_style.csv', index=False)

    return df_comb


def main():
    df, geo_cols, mat_cols = load_data()
    df_style = prepare_style(df)
    df_nation = prepare_nation(df)

    print(f"Total objects: {len(df)}")
    print(f"With style label: {len(df_style)}")
    print(f"With nation label: {len(df_nation)}")
    print(f"Geo features: {len(geo_cols)}, Mat features: {len(mat_cols)}")
    print("=" * 60)

    analysis_A_class_distribution(df_style)
    analysis_B_per_class_f1(df_style, geo_cols, mat_cols)
    analysis_C_correlation(df, geo_cols, mat_cols)
    analysis_D_ablation(df_style, geo_cols)
    analysis_E_nation_style_confound(df)
    analysis_F_silhouette(df_style, geo_cols)
    analysis_G_cv_detailed(df_style, df_nation, geo_cols, mat_cols)
    analysis_H_combined_underperformance(df_style, geo_cols, mat_cols)

    print("\n" + "=" * 60)
    print("All extended analyses complete. CSVs saved to ../data/")


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
