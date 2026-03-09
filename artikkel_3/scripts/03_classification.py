import os
import numpy as np
import pandas as pd
<<<<<<< HEAD
from sklearn.ensemble import HistGradientBoostingClassifier
=======
from sklearn.ensemble import RandomForestClassifier
>>>>>>> badf2ed9ee146fa19fcd77b9e01215819a390a08
from sklearn.model_selection import StratifiedKFold, permutation_test_score, cross_validate
from sklearn.metrics import make_scorer, f1_score, accuracy_score
import warnings

warnings.filterwarnings('ignore')

STYLE_MAPPING = {
    'Renessanse': 'Renessanse',
    'Middelalder': 'Renessanse',
    
    'Barokk': 'Barokk',
    'Régence': 'Barokk',
    'Queen Anne': 'Barokk',
    
    'Rokokko': 'Rokokko',
    'Chippendale': 'Rokokko',
    
    'Empire': 'Nyklassisisme',
    'Louis XVI': 'Nyklassisisme',
    'Hepplewhite': 'Nyklassisisme',
    'Regency': 'Nyklassisisme',
    'Sheraton': 'Nyklassisisme',
    'Nyklassisisme': 'Nyklassisisme',
    'Klassisisme': 'Nyklassisisme',
    'Biedermeier': 'Nyklassisisme',
    
    'Historisme': 'Historisme',
    'Nyrokokko': 'Historisme',
    'Nybarokk': 'Historisme',
    'Dragestil': 'Historisme',
    
    'Art Nouveau': 'Jugend',
    'Jugend': 'Jugend',
    'Art Nouveau (Jugend)': 'Jugend',
    
    'Modernisme': 'Modernisme',
    'Scandinavian Design': 'Modernisme',
    'Etterkrigsmodernisme': 'Modernisme',
    'Funksjonalisme': 'Modernisme',
    
    'Postmodernisme': 'Postmodernisme'
}

def load_data():
    data_dir = '../data'
    df_meta = pd.read_csv(os.path.join(data_dir, 'metadata.csv'))
    df_geo = pd.read_csv(os.path.join(data_dir, 'features_geometric.csv'))
    df_mat = pd.read_csv(os.path.join(data_dir, 'features_material.csv'))
    
    # Merge datasets
    df = df_geo.merge(df_mat, on='objectId', how='inner')
    df = df.merge(df_meta[['objectId', 'stilperiode', 'produksjonsstad']], on='objectId', how='inner')
    
    return df

def run_experiment(X, y, name="Experiment", n_permutations=100):
    print(f"\n--- {name} ---")
    print(f"Dataset shape: X={X.shape}, y={y.shape}")
    
<<<<<<< HEAD
    clf = HistGradientBoostingClassifier(random_state=42, class_weight='balanced')
=======
    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
>>>>>>> badf2ed9ee146fa19fcd77b9e01215819a390a08
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    scoring = {'f1_macro': 'f1_macro',
               'accuracy': 'accuracy'}
               
    results = cross_validate(clf, X, y, cv=cv, scoring=scoring, return_train_score=False)
    
    f1_mean = np.mean(results['test_f1_macro'])
    acc_mean = np.mean(results['test_accuracy'])
    
    print(f"CV Macro F1: {f1_mean:.3f} (+/- {np.std(results['test_f1_macro']):.3f})")
    print(f"CV Accuracy: {acc_mean:.3f} (+/- {np.std(results['test_accuracy']):.3f})")
    
    # Permutation test for F1 macro
    score, perm_scores, pvalue = permutation_test_score(
        clf, X, y, scoring='f1_macro', cv=cv, n_permutations=n_permutations, n_jobs=-1, random_state=42
    )
    print(f"Permutation p-value: {pvalue:.4f} (Chance baseline F1: {np.mean(perm_scores):.3f})")
    
    return f1_mean, pvalue

def main():
    df = load_data()
    
    # Feature lists
    geo_cols = [c for c in df.columns if c.startswith(('pca_', 'bbox_', 'aspect_', 'compactness', 'surface_', 'symmetry_', 'h_dist_', 'curv_', 'd2_'))]
    mat_cols = [c for c in df.columns if c.startswith('mat_')]
    
    # --- Experiment A: Style Prediction ---
    df_style = df.copy()
    # Map styles
    df_style['style_group'] = df_style['stilperiode'].map(STYLE_MAPPING)
    df_style = df_style.dropna(subset=['style_group'])
    
    print(f"Total instances for Style Prediction: {len(df_style)}")
    print("Class distribution:")
    print(df_style['style_group'].value_counts())
    
    X_style_geo = df_style[geo_cols].values
    X_style_mat = df_style[mat_cols].values
    X_style_comb = df_style[geo_cols + mat_cols].values
    y_style = df_style['style_group'].values
    
<<<<<<< HEAD
    f1_a1, _ = run_experiment(X_style_geo, y_style, "A1: Style Prediction (Geometry Only)", n_permutations=1)
    f1_a2, _ = run_experiment(X_style_mat, y_style, "A2: Style Prediction (Material Only)", n_permutations=1)
    f1_a3, _ = run_experiment(X_style_comb, y_style, "A3: Style Prediction (Combined)", n_permutations=1)
=======
    f1_a1, _ = run_experiment(X_style_geo, y_style, "A1: Style Prediction (Geometry Only)", n_permutations=50)
    f1_a2, _ = run_experiment(X_style_mat, y_style, "A2: Style Prediction (Material Only)", n_permutations=50)
    f1_a3, _ = run_experiment(X_style_comb, y_style, "A3: Style Prediction (Combined)", n_permutations=50)
>>>>>>> badf2ed9ee146fa19fcd77b9e01215819a390a08
    
    # --- Experiment B: Nation Prediction (Norway vs Others) ---
    df_nation = df.copy()
    df_nation = df_nation.dropna(subset=['produksjonsstad'])
    df_nation = df_nation[df_nation['produksjonsstad'] != '']
    
    df_nation['is_norway'] = df_nation['produksjonsstad'].apply(lambda x: 1 if 'Norge' in str(x) else 0)
    
    print(f"\nTotal instances for Nation Prediction: {len(df_nation)}")
    print("Class distribution (1=Norge, 0=Andre):")
    print(df_nation['is_norway'].value_counts())
    
    X_nation_geo = df_nation[geo_cols].values
    X_nation_mat = df_nation[mat_cols].values
    X_nation_comb = df_nation[geo_cols + mat_cols].values
    y_nation = df_nation['is_norway'].values
    
<<<<<<< HEAD
    f1_b1, _ = run_experiment(X_nation_geo, y_nation, "B1: Nation Prediction (Geometry Only)", n_permutations=1)
    f1_b2, _ = run_experiment(X_nation_mat, y_nation, "B2: Nation Prediction (Material Only)", n_permutations=1)
    f1_b3, _ = run_experiment(X_nation_comb, y_nation, "B3: Nation Prediction (Combined)", n_permutations=1)
=======
    f1_b1, _ = run_experiment(X_nation_geo, y_nation, "B1: Nation Prediction (Geometry Only)", n_permutations=50)
    f1_b2, _ = run_experiment(X_nation_mat, y_nation, "B2: Nation Prediction (Material Only)", n_permutations=50)
    f1_b3, _ = run_experiment(X_nation_comb, y_nation, "B3: Nation Prediction (Combined)", n_permutations=50)
>>>>>>> badf2ed9ee146fa19fcd77b9e01215819a390a08
    
    # Save results summary for plotting
    results_summary = pd.DataFrame([
        {'Task': 'Style', 'Feature': 'Geometry', 'F1': f1_a1},
        {'Task': 'Style', 'Feature': 'Material', 'F1': f1_a2},
        {'Task': 'Style', 'Feature': 'Combined', 'F1': f1_a3},
        {'Task': 'Nation', 'Feature': 'Geometry', 'F1': f1_b1},
        {'Task': 'Nation', 'Feature': 'Material', 'F1': f1_b2},
        {'Task': 'Nation', 'Feature': 'Combined', 'F1': f1_b3}
    ])
    results_summary.to_csv('../data/classification_results.csv', index=False)

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
