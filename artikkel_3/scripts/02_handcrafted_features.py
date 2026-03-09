import os
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull, cKDTree
from scipy.stats import skew
from sklearn.decomposition import PCA
from tqdm import tqdm

def compute_geometric_features(points):
    """Compute 21 geometric features from a 2048x3 point cloud."""
    features = {}
    
    # 1. PCA and eigenvalues
    pca = PCA(n_components=3)
    pca.fit(points)
    eig = pca.explained_variance_
    features['pca_l2_l1'] = eig[1] / (eig[0] + 1e-6)
    features['pca_l3_l1'] = eig[2] / (eig[0] + 1e-6)
    
    # 2. Bounding Box & Aspect Ratios
    # Align points to principal axes for a tighter bounding box
    points_pca = pca.transform(points)
    min_pt = points_pca.min(axis=0)
    max_pt = points_pca.max(axis=0)
    spans = np.sort(max_pt - min_pt)[::-1] # Largest to smallest: H, W, D
    H, W, D = spans[0], spans[1], spans[2]
    features['bbox_H'] = H
    features['bbox_W'] = W
    features['bbox_D'] = D
    features['aspect_H_W'] = H / (W + 1e-6)
    features['aspect_D_W'] = D / (W + 1e-6)
    
    # 3. Compactness and Surface Ratio
    try:
        hull = ConvexHull(points)
        hull_vol = hull.volume
        hull_area = hull.area
    except:
        hull_vol = 0
        hull_area = 0
        
    bbox_vol = H * W * D
    bbox_area = 2 * (H*W + H*D + W*D)
    features['compactness'] = hull_vol / (bbox_vol + 1e-6)
    features['surface_ratio'] = hull_area / (bbox_area + 1e-6)
    
    # 4. Symmetry score
    # Reflect across the plane defined by the two largest PCA components (normal is the 3rd component)
    normal = pca.components_[2]
    points_mirrored = points - 2 * np.outer(np.dot(points, normal), normal)
    tree = cKDTree(points)
    dists, _ = tree.query(points_mirrored, k=1)
    features['symmetry_score'] = np.mean(dists) # Lower is more symmetric
    
    # 5. Height distribution (assuming 1st PCA component or raw Z is height, let's use largest span axis)
    heights = points_pca[:, 0] # 0th is the largest variance direction
    h_min, h_max = heights.min(), heights.max()
    h_range = h_max - h_min
    if h_range == 0: h_range = 1e-6
    h_norm = (heights - h_min) / h_range
    features['h_dist_bottom'] = np.sum(h_norm < 0.333) / len(points)
    features['h_dist_mid'] = np.sum((h_norm >= 0.333) & (h_norm < 0.666)) / len(points)
    features['h_dist_top'] = np.sum(h_norm >= 0.666) / len(points)
    
    # 6. Curvature stats
    _, idxs = tree.query(points, k=15)
    curvatures = []
    for i in range(len(points)):
        nbors = points[idxs[i]]
        nbors_pca = PCA(n_components=3).fit(nbors)
        e = nbors_pca.explained_variance_
        curv = e[2] / (np.sum(e) + 1e-6)
        curvatures.append(curv)
    curvatures = np.array(curvatures)
    features['curv_mean'] = np.mean(curvatures)
    features['curv_std'] = np.std(curvatures)
    features['curv_skew'] = float(skew(curvatures))
    
    # 7. D2 shape distribution (Osada 2002)
    # Random pairwise distances
    np.random.seed(42)
    idx1 = np.random.randint(0, len(points), 10000)
    idx2 = np.random.randint(0, len(points), 10000)
    d2 = np.sqrt(np.sum((points[idx1] - points[idx2])**2, axis=1))
    hist, _ = np.histogram(d2, bins=5, range=(0, 2.0), density=True)
    for i, val in enumerate(hist):
        features[f'd2_bin_{i+1}'] = val
        
    return features

def extract_materials(df):
    all_materials = []
    for mats in df['materialar'].dropna():
        for m in str(mats).split('|'):
            m = m.strip()
            if m:
                all_materials.append(m)
                
    from collections import Counter
    counts = Counter(all_materials)
    top_30 = [x[0] for x in counts.most_common(30)]
    
    mat_features = []
    for idx, row in df.iterrows():
        mats = [m.strip() for m in str(row.get('materialar', '')).split('|')]
        feat = {'objectId': row['objectId']}
        for t in top_30:
            feat[f'mat_{t}'] = 1 if t in mats else 0
        mat_features.append(feat)
        
    return pd.DataFrame(mat_features)

def main():
    data_dir = '../data'
    
    print("Loading point clouds...")
    npz = np.load(os.path.join(data_dir, 'pointclouds.npz'))
    object_ids = npz.files
    
    print(f"Computing geometric features for {len(object_ids)} models...")
    geo_features = []
    for obj_id in tqdm(object_ids):
        pts = npz[obj_id]
        if pts.shape[0] != 2048:
            continue
        feats = compute_geometric_features(pts)
        feats['objectId'] = obj_id
        geo_features.append(feats)
        
    df_geo = pd.DataFrame(geo_features)
    # Reorder columns to put objectId first
    cols = ['objectId'] + [c for c in df_geo.columns if c != 'objectId']
    df_geo = df_geo[cols]
    df_geo.to_csv(os.path.join(data_dir, 'features_geometric.csv'), index=False)
    print(f"Saved geometric features: {df_geo.shape}")
    
    print("Processing material features...")
    df_meta = pd.read_csv(os.path.join(data_dir, 'metadata.csv'))
    df_mat = extract_materials(df_meta)
    df_mat.to_csv(os.path.join(data_dir, 'features_material.csv'), index=False)
    print(f"Saved material features: {df_mat.shape}")

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
