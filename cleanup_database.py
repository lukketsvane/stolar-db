import pandas as pd
import os

def cleanup_non_chairs():
    csv_path = 'STOLAR/STOLAR.csv'
    df = pd.read_csv(csv_path)
    
    # Keywords for deletion
    delete_keywords = [
        'miniature', 'miniatyr', 'dolls\' house', 'dokkehus', 'model ', 'modell ', 
        'fotografi', 'tegning', 'skisse', 'drawing', 'print', 'arkitekturfotografi'
    ]
    
    # Identify rows to delete
    to_delete_mask = df['Nemning'].str.contains('|'.join(delete_keywords), case=False, na=False) | \
                     df['Emneord'].str.contains('|'.join(delete_keywords), case=False, na=False) | \
                     (df['Høgde (cm)'] > 0) & (df['Høgde (cm)'] < 20) # Too small for a chair
    
    # Specific check for "Reserved" or other placeholder names
    to_delete_mask |= df['Namn'].str.contains('Reserved', case=False, na=False)
    
    deleted_objects = df[to_delete_mask]['Objekt-ID'].tolist()
    new_df = df[~to_delete_mask]
    
    print(f"Identifying {len(deleted_objects)} objects for deletion...")
    
    # Delete files
    glb_dir = 'STOLAR/glb'
    bguw_dir = 'STOLAR/bguw'
    img_dir = 'STOLAR/images'
    
    files_deleted = 0
    for obj_id in deleted_objects:
        obj_id_str = str(obj_id)
        # GLB files
        for ext in ['.glb', '_textured.glb']:
            p = os.path.join(glb_dir, obj_id_str + ext)
            if os.path.exists(p):
                os.remove(p)
                files_deleted += 1
        
        # BGUW images
        p_bguw = os.path.join(bguw_dir, obj_id_str + '_bguw.png')
        if os.path.exists(p_bguw):
            os.remove(p_bguw)
            files_deleted += 1
            
        # Standard images
        for ext in ['.png', '.jpg', '.jpeg']:
            p_img = os.path.join(img_dir, obj_id_str + ext)
            if os.path.exists(p_img):
                os.remove(p_img)
                files_deleted += 1

    # Save updated CSV
    new_df.to_csv(csv_path, index=False)
    
    # Also sync root stolar_db.csv if it exists
    if os.path.exists('stolar_db.csv'):
        new_df.to_csv('stolar_db.csv', index=False)
        print("Synced root stolar_db.csv")
    
    print(f"Summary:")
    print(f"- Removed {len(deleted_objects)} objects from database.")
    print(f"- Deleted {files_deleted} associated files (GLB, images).")
    print(f"- New total objects: {len(new_df)}")
    
    if len(deleted_objects) > 0:
        print("\nSample deleted objects:")
        print(deleted_objects[:10])

if __name__ == "__main__":
    cleanup_non_chairs()
