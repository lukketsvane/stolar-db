import pandas as pd
import os

def identify_deficiencies():
    df = pd.read_csv('STOLAR/STOLAR.csv')
    glb_dir = 'STOLAR/glb'
    glb_files = {f.replace('.glb', '').replace('_textured', '') for f in os.listdir(glb_dir) if f.endswith('.glb')}
    
    # 1. Missing GLB
    missing_glb = df[~df['Objekt-ID'].isin(glb_files)]
    
    # 2. Missing height but have GLB
    missing_height = df[df['Objekt-ID'].isin(glb_files) & (df['Høgde (cm)'].isna() | (df['Høgde (cm)'] == 0))]
    
    # 3. Duplicates
    duplicates = df[df.duplicated(subset=['Objekt-ID'], keep=False)]
    
    print(f"--- Deficiencies Report ---")
    print(f"Objects missing GLB: {len(missing_glb)}")
    if len(missing_glb) > 0:
        print(missing_glb[['Objekt-ID', 'Nemning']].head(10))
        
    print(f"\nObjects with GLB but missing height: {len(missing_height)}")
    if len(missing_height) > 10:
        print(missing_height[['Objekt-ID', 'Nemning']].head(10))
        
    print(f"\nDuplicate Objekt-IDs: {len(duplicates)}")
    if len(duplicates) > 0:
        print(duplicates[['Objekt-ID', 'Nemning']].sort_values('Objekt-ID').head(10))

    # Check sync with root stolar_db.csv
    root_csv = 'stolar_db.csv'
    if os.path.exists(root_csv):
        df_root = pd.read_csv(root_csv)
        print(f"\nRoot stolar_db.csv: {len(df_root)} rows")
        if len(df) != len(df_root):
            print(f"WARNING: Row count mismatch! STOLAR/STOLAR.csv ({len(df)}) vs stolar_db.csv ({len(df_root)})")

if __name__ == "__main__":
    identify_deficiencies()
