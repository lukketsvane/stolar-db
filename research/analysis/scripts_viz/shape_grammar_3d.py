#!/usr/bin/env python3
"""
Shape Grammar 3D Avleiingsmotor for FORMLÆRE.
Implementerer metodikken frå Xue & Chen (2024) direkte over 3D-meshar.
"""

import os
import sys
import pandas as pd
import numpy as np
import trimesh
from pathlib import Path
from sklearn.cluster import KMeans
import random
import csv
import warnings

warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parents[1]
GLB_DIR = ROOT / 'STOLAR' / 'glb'
OUT = ROOT / 'analysis' / 'mutant_features.csv'

def extract_features(mesh, objekt_id, rule_applied):
    """Trekk ut trekk frå ein mesh (same logikk som extract_mesh_features.py)"""
    rec = {'objekt_id': objekt_id, 'rule': rule_applied}
    
    rec['n_verts'] = len(mesh.vertices)
    rec['n_faces'] = len(mesh.faces)
    
    bbox = mesh.bounds
    ext = bbox[1] - bbox[0]
    rec['bbox_x'] = float(ext[0])
    rec['bbox_y'] = float(ext[1])
    rec['bbox_z'] = float(ext[2])
    rec['vol_bbox'] = float(ext[0] * ext[1] * ext[2])
    
    try:
        hull = mesh.convex_hull
        rec['vol_hull'] = float(hull.volume)
        hull_area = float(hull.area)
    except Exception:
        hull = None
        rec['vol_hull'] = float('nan')
        hull_area = float('nan')

    rec['area'] = float(mesh.area)
    
    if rec['vol_hull'] > 0 and hull_area > 0:
        rec['sphericity'] = float((np.pi ** (1.0 / 3.0)) * ((6.0 * rec['vol_hull']) ** (2.0 / 3.0)) / hull_area)
    else:
        rec['sphericity'] = float('nan')
        
    if rec['vol_bbox'] > 0:
        rec['fill_ratio'] = rec['vol_hull'] / rec['vol_bbox'] if rec['vol_hull'] > 0 else float('nan')
    else:
        rec['fill_ratio'] = float('nan')
        
    return rec

def load_mesh(obj_id):
    path = GLB_DIR / f"{obj_id}.glb"
    if not path.exists():
        return None
    try:
        scene = trimesh.load(str(path), force='scene')
        if isinstance(scene, trimesh.Scene):
            geoms = list(scene.geometry.values())
            if not geoms:
                return None
            mesh = trimesh.util.concatenate(geoms)
        else:
            mesh = scene
        # Normalize: center at origin, base at y=0
        mesh.vertices -= mesh.bounds[0]
        mesh.vertices[:, 0] -= (mesh.bounds[1][0] - mesh.bounds[0][0])/2
        mesh.vertices[:, 2] -= (mesh.bounds[1][2] - mesh.bounds[0][2])/2
        return mesh
    except:
        return None

def slice_and_combine(mesh_base, mesh_top):
    """R1: Erstatning (Byter ut toppen av stolen)"""
    h_base = mesh_base.bounds[1][1]
    cut_height = h_base * 0.5
    
    # Skjer base-stolen
    try:
        bottom = trimesh.intersections.slice_mesh_plane(mesh_base, plane_normal=[0, -1, 0], plane_origin=[0, cut_height, 0])
    except:
        bottom = mesh_base
        
    # Skjer top-stolen
    h_top = mesh_top.bounds[1][1]
    top_cut = h_top * 0.5
    try:
        top = trimesh.intersections.slice_mesh_plane(mesh_top, plane_normal=[0, 1, 0], plane_origin=[0, top_cut, 0])
        # Flytt toppen ned til cut_height
        top.vertices[:, 1] += (cut_height - top_cut)
        
        # Skaler toppen til å passe breidda på basen
        w_base = mesh_base.bounds[1][0] - mesh_base.bounds[0][0]
        w_top = top.bounds[1][0] - top.bounds[0][0]
        if w_top > 0:
            scale_x = w_base / w_top
            mat = trimesh.transformations.scale_matrix(scale_x, [0,0,0], [1,0,0])
            top.apply_transform(mat)
    except:
        top = mesh_top
        
    return trimesh.util.concatenate([bottom, top])

def apply_scale(mesh):
    """R3: Skalering (anisotropisk)"""
    m = mesh.copy()
    sx = random.uniform(0.8, 1.2)
    sy = random.uniform(0.8, 1.2)
    sz = random.uniform(0.8, 1.2)
    mat = trimesh.transformations.scale_matrix(1.0, [0,0,0])
    mat[0,0] = sx
    mat[1,1] = sy
    mat[2,2] = sz
    m.apply_transform(mat)
    return m

def apply_shear(mesh):
    """R7/R8: Forskyving/Kurve-deformasjon (Shear i X-retning basert på Y)"""
    m = mesh.copy()
    shear_factor = random.uniform(-0.3, 0.3)
    # y-koordinaten påverkar x-koordinaten
    m.vertices[:, 0] += m.vertices[:, 1] * shear_factor
    return m

def main():
    print("1. Etablerer DNA Gene Pool frå mesh_features.csv...")
    df = pd.read_csv(ROOT / 'analysis' / 'mesh_features.csv')
    df = df.dropna(subset=['sphericity', 'fill_ratio', 'vol_hull'])
    
    # Vel 8 prototypar via K-means for å maksimere spreiing
    features = df[['sphericity', 'fill_ratio', 'vol_hull']].values
    kmeans = KMeans(n_clusters=8, random_state=42).fit(features)
    
    medoid_ids = []
    for i in range(8):
        center = kmeans.cluster_centers_[i]
        dist = np.linalg.norm(features - center, axis=1)
        medoid_idx = np.argmin(dist)
        medoid_ids.append(df.iloc[medoid_idx]['objekt_id'])
        
    print(f"DNA Pool (S): {medoid_ids}")
    
    meshes = {}
    for obj_id in medoid_ids:
        m = load_mesh(obj_id)
        if m is not None:
            meshes[obj_id] = m
            
    valid_ids = list(meshes.keys())
    if len(valid_ids) < 2:
        print("For få gyldige meshar lasta.")
        return
        
    print("2-5. Genererer mutasjonar via 3D Formgrammatikk-reglar (R1-R8)...")
    mutants = []
    
    # Produser N mutasjonar
    N_MUTANTS = 300
    for i in range(N_MUTANTS):
        base_id = random.choice(valid_ids)
        base_mesh = meshes[base_id].copy()
        
        rule_choice = random.choice(['R1_Erstatning', 'R3_Skalering', 'R7_Forskyving'])
        
        if rule_choice == 'R1_Erstatning':
            top_id = random.choice(valid_ids)
            mutant_mesh = slice_and_combine(base_mesh, meshes[top_id])
        elif rule_choice == 'R3_Skalering':
            mutant_mesh = apply_scale(base_mesh)
        elif rule_choice == 'R7_Forskyving':
            mutant_mesh = apply_shear(base_mesh)
            
        feat = extract_features(mutant_mesh, f"mutant_{i}", rule_choice)
        mutants.append(feat)
        if (i+1) % 50 == 0:
            print(f"Generert {i+1} mutasjonar...")
            
    print("6. Lagrar teoretisk formrom...")
    mutant_df = pd.DataFrame(mutants)
    mutant_df.to_csv(OUT, index=False)
    print(f"Lagra {len(mutants)} mutasjonar til {OUT}")

if __name__ == '__main__':
    main()
