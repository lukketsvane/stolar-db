import os
import pandas as pd
import trimesh
import numpy as np

def perfect_database():
    csv_path = 'STOLAR/STOLAR.csv'
    glb_dir = 'STOLAR/glb'
    gh_raw_base = "https://raw.githubusercontent.com/lukketsvane/stolar-db/main/STOLAR/glb"
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found")
        return
    
    df = pd.read_csv(csv_path)
    
    # Identify GLB files
    glb_files = [f for f in os.listdir(glb_dir) if f.endswith('.glb')]
    # Use a dict for fast lookup: {obj_id: filename}
    # Some might have _textured.glb, prefer the main one if it exists
    glb_map = {}
    for f in glb_files:
        obj_id = f.replace('.glb', '').replace('_textured', '')
        if obj_id not in glb_map or '_textured' not in f:
            glb_map[obj_id] = f

    print(f"Found {len(glb_map)} unique objects with GLB files.")
    
    updated_rows = 0
    scaled_files = 0
    missing_height_count = 0
    
    for idx, row in df.iterrows():
        obj_id = str(row['Objekt-ID'])
        
        # 1. Update 3D-modell URL if missing but file exists
        if obj_id in glb_map:
            current_url = str(row.get('3D-modell', ''))
            if pd.isna(row['3D-modell']) or current_url.strip() == '' or current_url == 'nan':
                filename = glb_map[obj_id]
                df.at[idx, '3D-modell'] = f"{gh_raw_base}/{filename}"
                updated_rows += 1
        
        # 2. Scale GLB if height is available
        height_cm = row['Høgde (cm)']
        if obj_id in glb_map and pd.notna(height_cm) and height_cm > 0:
            filename = glb_map[obj_id]
            filepath = os.path.join(glb_dir, filename)
            
            try:
                # Load with trimesh (returns Scene for GLB)
                scene = trimesh.load(filepath)
                
                # current height (Y axis is standard for GLB up)
                # bounds is [min, max], where min/max are [x, y, z]
                current_height = scene.bounds[1][1] - scene.bounds[0][1]
                
                if current_height <= 0:
                    current_height = float(scene.extents.max())
                
                target_height = height_cm / 100.0  # Scale to meters
                
                # Check if scaling is needed (tolerance 0.1cm = 0.001m)
                if abs(current_height - target_height) > 0.001:
                    scale_factor = target_height / current_height
                    scene.apply_scale(scale_factor)
                    scene.export(filepath)
                    scaled_files += 1
                    # print(f"Scaled {obj_id}: {current_height:.4f} -> {target_height:.4f}")
            except Exception as e:
                print(f"Error scaling {obj_id}: {e}")
        elif obj_id in glb_map:
            missing_height_count += 1

    # Save updated CSV
    df.to_csv(csv_path, index=False)
    
    print(f"\nSummary:")
    print(f"- Updated {updated_rows} rows in CSV with GLB URLs.")
    print(f"- Scaled {scaled_files} GLB files to match database height.")
    print(f"- {missing_height_count} objects have GLB but no height in database.")
    print(f"- Database saved to {csv_path}")

if __name__ == "__main__":
    perfect_database()
