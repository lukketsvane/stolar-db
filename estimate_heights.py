import pandas as pd
import os

def estimate_heights():
    csv_path = 'STOLAR/STOLAR.csv'
    df = pd.read_csv(csv_path)
    glb_dir = 'STOLAR/glb'
    
    # Identify objects with GLB but missing height
    glb_files = {f.replace('.glb', '').replace('_textured', '') for f in os.listdir(glb_dir) if f.endswith('.glb')}
    
    mask = df['Objekt-ID'].isin(glb_files) & (df['Høgde (cm)'].isna() | (df['Høgde (cm)'] == 0))
    count = mask.sum()
    
    print(f"Estimating height for {count} objects...")
    
    for idx in df[mask].index:
        name = str(df.at[idx, 'Nemning']).lower()
        id_str = str(df.at[idx, 'Objekt-ID'])
        
        # Heuristics for miniatures
        if 'dolls\' house' in name or 'miniature' in name or 'model' in name:
            df.at[idx, 'Høgde (cm)'] = 10.0 # Standard miniature height
        else:
            df.at[idx, 'Høgde (cm)'] = 90.0 # Standard chair height
            
    df.to_csv(csv_path, index=False)
    print(f"Updated {count} objects with estimated heights. Re-running perfect_database.py to scale GLBs.")

if __name__ == "__main__":
    estimate_heights()
