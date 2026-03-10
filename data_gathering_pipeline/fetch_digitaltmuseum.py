import requests
import pandas as pd
import os
import time

# DigitaltMuseum / KulturNav Open API endpoint (example/stub configuration)
# Documentation: https://api.dimu.org/
DIMU_API_URL = "https://api.dimu.org/api/solr/select"
API_KEY = os.getenv("DIMU_API_KEY", "demo") # Use a real key if required

def fetch_metadata(query_term, max_rows=100):
    """
    Fetches metadata for a given object type (e.g., 'keramikk', 'bord', 'glass')
    to generalize the Form Follows Fitness framework beyond chairs.
    """
    print(f"Fetching metadata for '{query_term}' from DigitaltMuseum...")
    
    # This is a representative query structure for DiMu's Solr backend
    params = {
        'q': query_term,
        'wt': 'json',
        'rows': max_rows,
        'fq': 'has_image:true', # We need images/3D models to extract geometry
        'api.key': API_KEY
    }
    
    try:
        response = requests.get(DIMU_API_URL, params=params, timeout=10)
        response.raise_function_for_status()
        data = response.json()
        
        docs = data.get('response', {}).get('docs', [])
        print(f"Found {len(docs)} items for '{query_term}'.")
        return docs
    except Exception as e:
        print(f"Failed to fetch from API: {e}")
        # Return mock data for pipeline demonstration if API is offline
        return [
            {"id": f"mock_{query_term}_1", "title": f"Test {query_term} 1", "material": "tre", "production_place": "Norge", "era": "1850"},
            {"id": f"mock_{query_term}_2", "title": f"Test {query_term} 2", "material": "keramikk", "production_place": "Sverige", "era": "1920"},
        ]

def extract_simulated_geometry(items):
    """
    In a real pipeline, this would download the images/3D models for each item
    and run the point cloud extraction (like in artikkel_3/scripts/01_extract_pointclouds.py)
    to generate bbox, compactness, symmetry, etc.
    """
    print("Simulating 3D geometry extraction...")
    features = []
    for item in items:
        # Simulate geometric features
        features.append({
            "objectId": item.get('id', 'unknown'),
            "bbox_volume": 0.5 + (hash(item.get('id', '')) % 100) / 100.0,
            "compactness": 0.3 + (hash(item.get('title', '')) % 100) / 100.0,
            "symmetry_x": 0.8 + (hash(item.get('material', '')) % 20) / 100.0,
            "curv_mean": 0.1 + (hash(item.get('era', '')) % 50) / 100.0
        })
    return pd.DataFrame(features)

def create_material_features(items):
    """
    Parses unstructured material strings into binary classification columns
    (mat_tre, mat_metall, mat_keramikk) for the machine learning model.
    """
    materials = []
    for item in items:
        mat_str = str(item.get('material', '')).lower()
        materials.append({
            "objectId": item.get('id', 'unknown'),
            "mat_tre": 1 if 'tre' in mat_str else 0,
            "mat_metall": 1 if 'metall' in mat_str or 'stål' in mat_str else 0,
            "mat_keramikk": 1 if 'keramikk' in mat_str or 'porselen' in mat_str else 0,
            "mat_glass": 1 if 'glass' in mat_str else 0,
            "mat_tekstil": 1 if 'tekstil' in mat_str or 'ull' in mat_str else 0
        })
    return pd.DataFrame(materials)

def build_dataset_for_object(object_type):
    """
    End-to-end pipeline for a single object type.
    """
    raw_items = fetch_metadata(object_type, max_rows=50)
    if not raw_items:
        return
    
    # 1. Build Metadata DB
    df_meta = pd.DataFrame([{
        "objectId": i.get('id'),
        "tittel": i.get('title'),
        "produksjonsstad": i.get('production_place', 'Unknown'),
        "stilperiode": i.get('era', 'Unknown')
    } for i in raw_items])
    
    # 2. Build Geometric Features
    df_geo = extract_simulated_geometry(raw_items)
    
    # 3. Build Material Features
    df_mat = create_material_features(raw_items)
    
    # Ensure directories exist
    out_dir = f"../data_{object_type}"
    os.makedirs(out_dir, exist_ok=True)
    
    # Save offline CSVs so the autoresearch agent can instantly optimize them
    df_meta.to_csv(os.path.join(out_dir, "metadata.csv"), index=False)
    df_geo.to_csv(os.path.join(out_dir, "features_geometric.csv"), index=False)
    df_mat.to_csv(os.path.join(out_dir, "features_material.csv"), index=False)
    
    print(f"Data pipeline complete for '{object_type}'. Saved to {out_dir}/")

if __name__ == "__main__":
    # Generalizing the thesis: Testing if FFF holds true for other object categories
    object_categories = ["keramikk", "bord", "lampe"]
    
    for category in object_categories:
        build_dataset_for_object(category)
        time.sleep(2) # Polite API spacing
        
    print("\nNext step: Update chair_autoresearch/train_eval.py to point to one of these new data directories to run FFF optimizations on other functional goods!")