import os
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sklearn.ensemble import RandomForestClassifier

STYLE_MAPPING = {
    'Renessanse': 'Renessanse', 'Middelalder': 'Renessanse',
    'Barokk': 'Barokk', 'Régence': 'Barokk', 'Queen Anne': 'Barokk',
    'Rokokko': 'Rokokko', 'Chippendale': 'Rokokko',
    'Empire': 'Nyklassisisme', 'Louis XVI': 'Nyklassisisme', 'Hepplewhite': 'Nyklassisisme',
    'Regency': 'Nyklassisisme', 'Sheraton': 'Nyklassisisme', 'Nyklassisisme': 'Nyklassisisme',
    'Klassisisme': 'Nyklassisisme', 'Biedermeier': 'Nyklassisisme',
    'Historisme': 'Historisme', 'Nyrokokko': 'Historisme', 'Nybarokk': 'Historisme', 'Dragestil': 'Historisme',
    'Art Nouveau': 'Jugend', 'Jugend': 'Jugend', 'Art Nouveau (Jugend)': 'Jugend',
    'Modernisme': 'Modernisme', 'Scandinavian Design': 'Modernisme', 'Etterkrigsmodernisme': 'Modernisme', 'Funksjonalisme': 'Modernisme',
    'Postmodernisme': 'Postmodernisme'
}

def main():
    data_dir = '../data'
    df_meta = pd.read_csv(os.path.join(data_dir, 'metadata.csv'))
    df_geo = pd.read_csv(os.path.join(data_dir, 'features_geometric.csv'))
    df_mat = pd.read_csv(os.path.join(data_dir, 'features_material.csv'))
    
    df = df_geo.merge(df_mat, on='objectId', how='inner')
    df = df.merge(df_meta[['objectId', 'stilperiode', 'produksjonsstad']], on='objectId', how='inner')
    
    geo_cols = [c for c in df.columns if c.startswith(('pca_', 'bbox_', 'aspect_', 'compactness', 'surface_', 'symmetry_', 'h_dist_', 'curv_', 'd2_'))]
    mat_cols = [c for c in df.columns if c.startswith('mat_')]
    
    # 1. Nation Feature Importance
    df_nation = df.dropna(subset=['produksjonsstad']).copy()
    df_nation = df_nation[df_nation['produksjonsstad'] != '']
    df_nation['is_norway'] = df_nation['produksjonsstad'].apply(lambda x: 1 if 'Norge' in str(x) else 0)
    
    X_nation = df_nation[geo_cols + mat_cols]
    y_nation = df_nation['is_norway']
    
    clf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
    clf.fit(X_nation, y_nation)
    
    importances = clf.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print("--- Top 15 Features for Nation Prediction ---")
    top_features = []
    for i in range(15):
        feat = X_nation.columns[indices[i]]
        imp = importances[indices[i]]
        top_features.append((feat, imp))
        print(f"{i+1}. {feat}: {imp:.4f}")
        
    pd.DataFrame(top_features, columns=['Feature', 'Importance']).to_csv(os.path.join(data_dir, 'feature_importance_nation.csv'), index=False)
    
    # 2. Mutual Information
    mi = mutual_info_classif(X_nation, y_nation, random_state=42)
    mi_geo = np.mean([mi[i] for i, c in enumerate(X_nation.columns) if c in geo_cols])
    mi_mat = np.mean([mi[i] for i, c in enumerate(X_nation.columns) if c in mat_cols])
    
    print("\n--- Mutual Information (Mean per feature set) ---")
    print(f"Geometry: {mi_geo:.4f}")
    print(f"Material: {mi_mat:.4f}")
    
    # Confusion Matrix Data for Style
    df_style = df.copy()
    df_style['style_group'] = df_style['stilperiode'].map(STYLE_MAPPING)
    df_style = df_style.dropna(subset=['style_group'])
    
    X_style = df_style[geo_cols + mat_cols]
    y_style = df_style['style_group']
    
    from sklearn.model_selection import cross_val_predict
    y_pred = cross_val_predict(clf, X_style, y_style, cv=5)
    
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_style, y_pred, labels=np.unique(y_style))
    np.save(os.path.join(data_dir, 'style_confusion_matrix.npy'), cm)
    np.save(os.path.join(data_dir, 'style_classes.npy'), np.unique(y_style))
    
    # Save a clean dataset for UMAP
    df_style[['objectId', 'style_group'] + geo_cols].to_csv(os.path.join(data_dir, 'umap_data.csv'), index=False)

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
