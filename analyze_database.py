import os
import csv

def analyze_stolar():
    csv_path = 'STOLAR/STOLAR.csv'
    glb_dir = 'STOLAR/glb'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found")
        return
    
    # Check for GLB files
    glb_files = [f for f in os.listdir(glb_dir) if f.endswith('.glb')]
    glb_ids = {f.replace('.glb', '').replace('_textured', '') for f in glb_files}
    
    missing_glb = []
    has_glb_but_no_url = []
    has_url_but_no_file = []
    missing_height = []
    total_objects = 0
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_objects += 1
            obj_id = str(row['Objekt-ID'])
            url_field = row.get('3D-modell', '')
            has_url = url_field is not None and url_field.strip() != ''
            has_file = obj_id in glb_ids
            height_val = row.get('Høgde (cm)', '')
            
            try:
                height = float(height_val) if height_val else 0
            except ValueError:
                height = 0
            
            if not has_file:
                missing_glb.append(obj_id)
            
            if has_file and not has_url:
                has_glb_but_no_url.append(obj_id)
                
            if has_url and not has_file:
                has_url_but_no_file.append(obj_id)
                
            if height == 0:
                missing_height.append(obj_id)
            
    print(f"Total objects in CSV: {total_objects}")
    print(f"Total GLB files in {glb_dir}: {len(glb_files)}")
    print(f"Objects missing GLB file: {len(missing_glb)}")
    print(f"Objects with GLB URL in CSV but no file: {len(has_url_but_no_file)}")
    print(f"Objects with GLB file but no URL in CSV: {len(has_glb_but_no_url)}")
    print(f"Objects missing height: {len(missing_height)}")
    
    if has_url_but_no_file:
        print("\nFirst 10 objects with URL but no file:")
        print(has_url_but_no_file[:10])

if __name__ == "__main__":
    analyze_stolar()
