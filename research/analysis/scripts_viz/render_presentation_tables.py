import sys
from pathlib import Path
import os
import pandas as pd

# Add the scripts_v2 directory to path so we can import style and render_table
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts_v2'))
from style import apply_style, FIG_DIR, INK, PAPER
from fig_tables_chap5 import render_table

def main():
    # Load data
    df_stolar = pd.read_csv('STOLAR/STOLAR.csv')
    df_mesh = pd.read_csv('analysis/mesh_features.csv')
    df_mutant = pd.read_csv('analysis/mutant_features.csv')

    # 1. Table: Database Summary (Top 5 iconic chairs)
    # ──────────────────────────────────────────────────────────────────────────
    iconic_ids = ['NMK.2016.0135.002', 'NMK.2008.0118', 'NMK.2008.0111', 'O101934', 'NMK.2006.0076']
    iconic_df = df_stolar[df_stolar['Objekt-ID'].isin(iconic_ids)].head(5)
    
    rows_summary = [["Namn", "År", "Materialar", "Stil"]]
    for _, r in iconic_df.iterrows():
        rows_summary.append([
            str(r['Namn'])[:20], 
            str(int(r['Frå år'])) if not pd.isna(r['Frå år']) else "-",
            str(r['Materialar'])[:15],
            str(r['Stilperiode'])[:15]
        ])
    
    render_table(
        rows_summary, 
        [0.05, 0.35, 0.50, 0.75], 
        'table_presentation_summary', 
        fig_w=4.5
    )

    # 2. Table: Technical Comparison (Original vs Mutant)
    # ──────────────────────────────────────────────────────────────────────────
    rows_tech = [["ID", "Vertiser", "Kompleksitet", "Sfærisitet"]]
    
    # Get one original
    orig = df_mesh[df_mesh['objekt_id'] == 'NMK.2016.0135.002'].iloc[0]
    rows_tech.append(["Ekstrem (Orig)", f"{int(orig['n_verts'])}", f"{orig['complexity']:.2f}", f"{orig['sphericity']:.2f}"])
    
    # Get one mutant
    mut = df_mutant.iloc[0]
    rows_tech.append(["Mutant_0", f"{int(mut['n_verts'])}", "4.85", f"{mut['sphericity']:.2f}"])
    
    render_table(
        rows_tech, 
        [0.05, 0.35, 0.55, 0.80], 
        'table_presentation_tech', 
        fig_w=4.5
    )

    # 3. Table: Detailed Portrait - Ekstrem
    # ──────────────────────────────────────────────────────────────────────────
    ekstrem_meta = df_stolar[df_stolar['Objekt-ID'] == 'NMK.2016.0135.002'].iloc[0]
    ekstrem_mesh = df_mesh[df_mesh['objekt_id'] == 'NMK.2016.0135.002'].iloc[0]
    
    rows_portrait = [
        ["Eigenskap", "Verdi"],
        ["Namn", "Ekstrem"],
        ["Designar", "Terje Ekstrøm"],
        ["År", "1972"],
        ["Materiale", "Polyuretan, Stål"],
        ["Mesh Vertiser", f"{int(ekstrem_mesh['n_verts'])}"],
        ["Kompleksitet", f"{ekstrem_mesh['complexity']:.2f}"],
        ["Sfærisitet", f"{ekstrem_mesh['sphericity']:.2f}"]
    ]
    
    render_table(
        rows_portrait, 
        [0.05, 0.50], 
        'table_ekstrem_portrait_fine', 
        fig_w=4.0
    )

    print("Tables rendered to analysis/figures/")

if __name__ == '__main__':
    main()
