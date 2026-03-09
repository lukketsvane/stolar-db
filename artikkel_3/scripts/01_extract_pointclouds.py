import os
import glob
import json
import numpy as np
import pandas as pd
import trimesh
from tqdm import tqdm

def process_glb(path, num_points=2048):
    try:
        # Load GLB. force='mesh' tries to load everything as a single mesh
        scene = trimesh.load(path, force='mesh')
        
        if isinstance(scene, trimesh.Scene):
            meshes = [geom for geom in scene.geometry.values() if hasattr(geom, 'vertices') and len(geom.vertices) > 0]
            if not meshes:
                return None
            mesh = trimesh.util.concatenate(meshes)
        else:
            mesh = scene
            
        if not hasattr(mesh, 'vertices') or len(mesh.vertices) == 0:
            return None

        # Sample points
        points, _ = trimesh.sample.sample_surface(mesh, num_points)
        
        # Normalize: center at origin, scale to unit sphere
        centroid = np.mean(points, axis=0)
        points -= centroid
        max_dist = np.max(np.sqrt(np.sum(points**2, axis=1)))
        if max_dist > 0:
            points /= max_dist
            
        return points
    except Exception as e:
        print(f"Error processing {path}: {e}")
        return None

def extract_metadata(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Extract fields
    obj_id = data.get('objectId', os.path.basename(json_path).replace('.json', ''))
    
    # Stilperiode might be a list or a string
    stil = data.get('Stilperiode', '')
    if isinstance(stil, list):
        stil = stil[0] if stil else ''
        
    # Same for produksjonssted
    prod = data.get('Produksjonssted', '')
    if isinstance(prod, list):
        prod = prod[0] if prod else ''
        
    # Materiale
    mat = data.get('Materiale', [])
    if isinstance(mat, str):
        mat = [mat]
        
    datering = data.get('Datering', '')
    if isinstance(datering, list):
        datering = datering[0] if datering else ''

    return {
        'objectId': obj_id,
        'stilperiode': stil,
        'produksjonsstad': prod,
        'materialar': '|'.join(mat),
        'datering': datering
    }

def main():
    base_dir = '../../NM_stolar'
    out_dir = '../data'
    os.makedirs(out_dir, exist_ok=True)
    
    glb_files = sorted(glob.glob(os.path.join(base_dir, '**/*.glb'), recursive=True))
    json_files = sorted(glob.glob(os.path.join(base_dir, '**/*.json'), recursive=True))
    
    print(f"Found {len(glb_files)} GLB files and {len(json_files)} JSON files.")
    
    # Mapping JSONs by objectId
    metadata = []
    for jf in json_files:
        try:
            m = extract_metadata(jf)
            metadata.append(m)
        except Exception as e:
            pass
            
    df_meta = pd.DataFrame(metadata)
    df_meta.to_csv(os.path.join(out_dir, 'metadata.csv'), index=False, encoding='utf-8')
    print(f"Saved metadata for {len(df_meta)} objects.")
    
    # Extract point clouds
    pointclouds = {}
    for gf in tqdm(glb_files, desc="Extracting point clouds"):
        # Attempt to get objectId from filename (usually everything before _)
        filename = os.path.basename(gf)
        obj_id = filename.rsplit('_', 1)[0]
        if '_original' in filename:
            continue
            
        points = process_glb(gf)
        if points is not None:
            pointclouds[obj_id] = points
            
    np.savez_compressed(os.path.join(out_dir, 'pointclouds.npz'), **pointclouds)
    print(f"Saved {len(pointclouds)} point clouds.")

if __name__ == '__main__':
    # Ensure working dir is script dir
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
