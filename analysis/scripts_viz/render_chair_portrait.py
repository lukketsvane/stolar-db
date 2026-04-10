import sys
import os
import pandas as pd
from pathlib import Path

# Add scripts_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts_v2'))
from style import apply_style
import fig_tables_chap5

def render_portrait(obj_id, output_dir):
    # Load data
    df_stolar = pd.read_csv('STOLAR/STOLAR.csv')
    df_mesh = pd.read_csv('analysis/mesh_features.csv')
    
    # Filter
    meta = df_stolar[df_stolar['Objekt-ID'] == obj_id].iloc[0]
    try:
        mesh = df_mesh[df_mesh['objekt_id'] == obj_id].iloc[0]
        has_mesh = True
    except:
        has_mesh = False

    rows = [["Eigenskap", "Verdi"]]
    rows.append(["Namn", str(meta['Namn'])[:30]])
    rows.append(["År", str(int(meta['Frå år'])) if not pd.isna(meta['Frå år']) else "Ukjent"])
    rows.append(["Stil", str(meta['Stilperiode'])[:30]])
    rows.append(["Materiale", str(meta['Materialar'])[:30]])
    
    if has_mesh:
        rows.append(["Mesh Vertiser", f"{int(mesh['n_verts'])}"])
        rows.append(["Kompleksitet", f"{mesh['complexity']:.2f}"])
        rows.append(["Sfærisitet", f"{mesh['sphericity']:.2f}"])
        rows.append(["Fyllingsgrad", f"{mesh['fill_ratio']:.2f}"])

    output_path = os.path.join(output_dir, f"table_{obj_id}")
    
    # Hack: override FIG_DIR in the imported module so it doesn't prepend analysis/figures
    fig_tables_chap5.FIG_DIR = Path('')
    
    fig_tables_chap5.render_table(rows, [0.05, 0.50], output_path, fig_w=4.0)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python render_chair_portrait.py <obj_id> <output_dir>")
        sys.exit(1)
    render_portrait(sys.argv[1], sys.argv[2])
