import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import umap
from sklearn.preprocessing import StandardScaler

# Set aesthetic parameters for publication
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 12,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.bbox': 'tight'
})

def main():
    data_dir = '../data'
    out_dir = '../figurar'
    os.makedirs(out_dir, exist_ok=True)
    
    # ---------------------------------------------------------
    # Figure 1: UMAP of Form Space (Geometric Features)
    # ---------------------------------------------------------
    df_umap = pd.read_csv(os.path.join(data_dir, 'umap_data.csv'))
    geo_cols = [c for c in df_umap.columns if c not in ['objectId', 'style_group']]
    
    X = df_umap[geo_cols].values
    X_scaled = StandardScaler().fit_transform(X)
    
    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42)
    embedding = reducer.fit_transform(X_scaled)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    styles = df_umap['style_group'].unique()
    colors = sns.color_palette("husl", len(styles))
    
    for i, style in enumerate(styles):
        idx = df_umap['style_group'] == style
        ax.scatter(embedding[idx, 0], embedding[idx, 1], label=style, color=colors[i], alpha=0.7, s=40, edgecolors='w', linewidth=0.5)
        
    ax.set_title("Figur 1: UMAP-projeksjon av stolane sitt formrom (21 geometriske trekk)", pad=15)
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    ax.legend(title="Stilperiode", bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig1_formrom.pdf'))
    plt.savefig(os.path.join(out_dir, 'fig1_formrom.png'))
    plt.close()
    
    # ---------------------------------------------------------
    # Figure 2: Classification Results F1
    # ---------------------------------------------------------
    df_res = pd.read_csv(os.path.join(data_dir, 'classification_results.csv'))
    
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=df_res, x='Task', y='F1', hue='Feature', palette='viridis', ax=ax)
    
    ax.set_title("Figur 2: Klassifikasjonsnøyaktigheit (Makro F1-score)", pad=15)
    ax.set_xlabel("Prediksjonsoppgåve")
    ax.set_ylabel("Makro F1-score")
    ax.set_ylim(0, 1.0)
    
    # Add chance baselines as horizontal lines or text
    ax.axhline(0.12, color='gray', linestyle='--', alpha=0.7)
    ax.text(0, 0.14, 'Tilfeldig gjett (Stil) ≈ 0.12', color='gray', ha='center')
    ax.axhline(0.50, color='gray', linestyle='--', alpha=0.7)
    ax.text(1, 0.52, 'Tilfeldig gjett (Nasjon) ≈ 0.50', color='gray', ha='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig2_klassifikasjon.pdf'))
    plt.savefig(os.path.join(out_dir, 'fig2_klassifikasjon.png'))
    plt.close()
    
    # ---------------------------------------------------------
    # Figure 3: Confusion Matrix
    # ---------------------------------------------------------
    cm = np.load(os.path.join(data_dir, 'style_confusion_matrix.npy'))
    classes = np.load(os.path.join(data_dir, 'style_classes.npy'), allow_pickle=True)
    
    # Normalize by row
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(cm_norm, annot=True, fmt=".2f", cmap="Blues", xticklabels=classes, yticklabels=classes, ax=ax)
    
    ax.set_title("Figur 3: Forvirringsmatrise for stilprediksjon (Kombinert modell)", pad=15)
    ax.set_xlabel("Predikert stil")
    ax.set_ylabel("Faktisk stil")
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig3_forvirring.pdf'))
    plt.savefig(os.path.join(out_dir, 'fig3_forvirring.png'))
    plt.close()
    
    # ---------------------------------------------------------
    # Figure 4: Feature Importances
    # ---------------------------------------------------------
    df_imp = pd.read_csv(os.path.join(data_dir, 'feature_importance_nation.csv'))
    
    # Map feature names to readable Norwegian
    name_map = {
        'h_dist_top': 'Høgdefordeling (Topp)',
        'h_dist_mid': 'Høgdefordeling (Midt)',
        'd2_bin_3': 'D2 Formfordeling (Bin 3)',
        'd2_bin_4': 'D2 Formfordeling (Bin 4)',
        'd2_bin_1': 'D2 Formfordeling (Bin 1)',
        'd2_bin_2': 'D2 Formfordeling (Bin 2)',
        'd2_bin_5': 'D2 Formfordeling (Bin 5)',
        'curv_std': 'Krumming (Std.avvik)',
        'bbox_D': 'Djupn (Bounding Box)',
        'bbox_H': 'Høgde (Bounding Box)',
        'pca_l2_l1': 'PCA Eigenverdi-ratio (λ2/λ1)',
        'symmetry_score': 'Symmetriscore',
        'aspect_D_W': 'Aspektratio (D/B)',
        'surface_ratio': 'Overflateratio (Hull/Bbox)',
        'mat_Nøttetre': 'Material: Nøttetre'
    }
    df_imp['Lesevennleg'] = df_imp['Feature'].map(lambda x: name_map.get(x, x))
    
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(data=df_imp.head(15), x='Importance', y='Lesevennleg', palette='magma', ax=ax)
    
    ax.set_title("Figur 4: Topp 15 viktigaste trekk for prediksjon av produksjonsland", pad=15)
    ax.set_xlabel("Gjennomsnittleg reduksjon i Gini-ureinheit")
    ax.set_ylabel("Trekk (Geometri / Material)")
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'fig4_kopling.pdf'))
    plt.savefig(os.path.join(out_dir, 'fig4_kopling.png'))
    plt.close()
    
    print("Saved all 4 figures to ../figurar")

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
