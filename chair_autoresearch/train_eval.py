import os
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import StratifiedKFold, permutation_test_score, cross_validate
from sklearn.metrics import f1_score, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
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
    try:
        data_dir = '../artikkel_3/data'
        df_meta = pd.read_csv(os.path.join(data_dir, 'metadata.csv'))
        df_geo = pd.read_csv(os.path.join(data_dir, 'features_geometric.csv'))
        df_mat = pd.read_csv(os.path.join(data_dir, 'features_material.csv'))
    except FileNotFoundError:
        print("Data files not found. Using dummy data for demonstration.")
        n_samples = 500
        n_geo_features = 50
        n_mat_features = 20
        object_ids = range(n_samples)
        
        df_meta = pd.DataFrame({
            'objectId': object_ids,
            'stilperiode': np.random.choice(list(STYLE_MAPPING.keys()), n_samples),
            'produksjonsstad': np.random.choice(['Norge', 'Sverige', 'Danmark', 'Tyskland'], n_samples)
        })
        df_geo = pd.DataFrame(np.random.rand(n_samples, n_geo_features), columns=[f'pca_{i}' for i in range(n_geo_features)])
        df_geo['objectId'] = object_ids
        df_mat = pd.DataFrame(np.random.rand(n_samples, n_mat_features), columns=[f'mat_{i}' for i in range(n_mat_features)])
        df_mat['objectId'] = object_ids
    
    df = df_geo.merge(df_mat, on='objectId', how='inner')
    df = df.merge(df_meta[['objectId', 'stilperiode', 'produksjonsstad']], on='objectId', how='inner')
    
    return df

def run_experiment(clf_pipeline, X, y, name="Experiment", n_permutations=100):
    print(f"\n--- {name} ---")
    print(f"Dataset shape: X={X.shape}, y={y.shape}")
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    scoring = {'f1_macro': 'f1_macro',
               'accuracy': 'accuracy'}
               
    results = cross_validate(clf_pipeline, X, y, cv=cv, scoring=scoring, return_train_score=False, n_jobs=-1)
    
    f1_mean = np.mean(results['test_f1_macro'])
    acc_mean = np.mean(results['test_accuracy'])
    
    print(f"CV Macro F1: {f1_mean:.3f} (+/- {np.std(results['test_f1_macro']):.3f})")
    print(f"CV Accuracy: {acc_mean:.3f} (+/- {np.std(results['test_accuracy']):.3f})")
    
    score, perm_scores, pvalue = permutation_test_score(
        clf_pipeline, X, y, scoring='f1_macro', cv=cv, n_permutations=n_permutations, n_jobs=-1, random_state=42
    )
    print(f"Permutation p-value: {pvalue:.4f} (Chance baseline F1: {np.mean(perm_scores):.3f})")
    
    return f1_mean, pvalue

def main():
    df = load_data()
    
    geo_cols = [c for c in df.columns if c.startswith(('pca_', 'bbox_', 'aspect_', 'compactness', 'surface_', 'symmetry_', 'h_dist_', 'curv_', 'd2_'))]
    mat_cols = [c for c in df.columns if c.startswith('mat_')]
    feature_cols = geo_cols + mat_cols
    
    # --- Data preparation for Style prediction ---
    df_style = df.copy()
    df_style['style_group'] = df_style['stilperiode'].map(STYLE_MAPPING)
    df_style = df_style.dropna(subset=['style_group'])
    X_style_comb = df_style[feature_cols]
    y_style = df_style['style_group'].values
    
    # --- Data preparation for Nation prediction ---
    df_nation = df.copy()
    df_nation = df_nation.dropna(subset=['produksjonsstad'])
    df_nation = df_nation[df_nation['produksjonsstad'] != '']
    df_nation['is_norway'] = df_nation['produksjonsstad'].apply(lambda x: 1 if 'Norge' in str(x) else 0)
    X_nation_comb = df_nation[feature_cols]
    y_nation = df_nation['is_norway'].values
    
    # --- Model Definition ---
    # We employ a high-performance soft-voting ensemble of two powerful and diverse models:
    # 1. HistGradientBoostingClassifier: Fast, handles NaNs natively, and is highly accurate.
    # 2. ExtraTreesClassifier: A robust random forest variant that explores diverse feature splits.
    # This combination often yields state-of-the-art performance on heterogeneous tabular data.
    
    # Define base estimators for the Style prediction ensemble
    hgbc_style = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=500,
        max_leaf_nodes=41,
        l2_regularization=0.5,
        class_weight='balanced',
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=15,
        random_state=42
    )

    etc_style = ExtraTreesClassifier(
        n_estimators=500,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=1,
        min_samples_split=2,
        max_features='sqrt'
    )

    style_voter = VotingClassifier(
        estimators=[('hgbc', hgbc_style), ('etc', etc_style)],
        voting='soft',
        weights=[0.6, 0.4], # Give a slight edge to the gradient boosting model
        n_jobs=-1
    )

    style_clf_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('classifier', style_voter)
    ])

    # Define base estimators for the Nation prediction ensemble
    hgbc_nation = HistGradientBoostingClassifier(
        learning_rate=0.04,
        max_iter=400,
        max_leaf_nodes=31,
        l2_regularization=0.2,
        class_weight='balanced',
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=15,
        random_state=42
    )

    etc_nation = ExtraTreesClassifier(
        n_estimators=450,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=1,
        min_samples_split=2,
        max_features=0.7
    )

    nation_voter = VotingClassifier(
        estimators=[('hgbc', hgbc_nation), ('etc', etc_nation)],
        voting='soft',
        weights=[0.6, 0.4],
        n_jobs=-1
    )

    nation_clf_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('classifier', nation_voter)
    ])
    
    # Run experiments with the new pipelines
    f1_a3, _ = run_experiment(style_clf_pipeline, X_style_comb, y_style, "A3: Style Prediction (Combined)", n_permutations=1)
    f1_b3, _ = run_experiment(nation_clf_pipeline, X_nation_comb, y_nation, "B3: Nation Prediction (Combined)", n_permutations=1)
    
    final_score = f1_a3 + f1_b3
    print(f"\nFINAL_SCORE: {final_score:.6f}")
    return final_score

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
    if 'artikkel_3' in os.listdir(script_dir):
        pass
    elif os.path.basename(script_dir) == 'artikkel_3':
        os.chdir(os.path.join(script_dir, '..'))
    else:
        try:
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
        except NameError:
            pass
    main()