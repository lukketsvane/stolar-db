#!/usr/bin/env python3
"""
Extra tests for FORMLÆRE propositions.
Focus: 3.2 (Multimodality), 5.22 (Substrate independence), 6.3 (Complexity/Time).
All output in Töpfer style.
"""
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import gridspec
from scipy.stats import gaussian_kde
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.decomposition import PCA

warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
MESH = ROOT / 'analysis' / 'mesh_features.csv'
CAT = ROOT / 'STOLAR' / 'STOLAR.csv'
OUT = ROOT / 'analysis' / 'figures'
OUT.mkdir(exist_ok=True)

# Töpfer Palette
INK = '#1a1a1a'
PAPER = '#fbfbf8'
GRID = '#e8e7df'

plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': PAPER,
    'font.family': 'serif',
    'font.serif': ['EB Garamond', 'Garamond', 'serif'],
    'axes.linewidth': 0.6,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'axes.titlesize': 11,
    'font.size': 10,
    'lines.linewidth': 0.8,
})

def load():
    mesh = pd.read_csv(MESH)
    cat = pd.read_csv(CAT, encoding='utf-8')
    rename = {cat.columns[i]: c for i, c in enumerate([
        'Namn','Bilete','Fra','Mat','MatK','Nasjmus','ID','PStad','Prod','Til',
        'GLB','Vekt','Nasj','URL','Emneord','Erverving','SH','Stil','Tekn',
        'Br','Dat','Dj','Ho','Nemn','Hundre',
    ])}
    cat = cat.rename(columns=rename)
    cat['Fra'] = pd.to_numeric(cat['Fra'], errors='coerce')
    cat['Ho'] = pd.to_numeric(cat['Ho'], errors='coerce')
    cat['Br'] = pd.to_numeric(cat['Br'], errors='coerce')
    def matgrp(s):
        s = (s or '').lower()
        if any(x in s for x in ['stål','metall','jern']): return 'metall'
        if any(x in s for x in ['tre','eik','furu']): return 'tre'
        return 'anna'
    cat['matgr'] = cat.Mat.apply(matgrp)
    return mesh, cat

def test_3_2_multimodality(mesh):
    """Prop 3.2: Multimodality in mesh space."""
    cols = ['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity']
    X = mesh[cols].dropna().values
    Xn = StandardScaler().fit_transform(X)
    pca = PCA(n_components=1); Xp = pca.fit_transform(Xn).ravel()
    
    fig, ax = plt.subplots(figsize=(8, 4))
    kde = gaussian_kde(Xp)
    x = np.linspace(Xp.min(), Xp.max(), 200)
    ax.plot(x, kde(x), color=INK, linewidth=1.0)
    ax.fill_between(x, kde(x), color=INK, alpha=0.05)
    
    # Find local maxima (simple version)
    y = kde(x)
    peaks = x[(y > np.roll(y,1)) & (y > np.roll(y,-1))]
    for p in peaks:
        ax.axvline(p, color=INK, linestyle=':', linewidth=0.5, alpha=0.6)
        ax.text(p, ax.get_ylim()[1]*0.9, f'attraktor', rotation=90, fontsize=7, ha='right')

    ax.set_xlabel('første hovudkomponent (mesh-rom)')
    ax.set_ylabel('tettleik (kde)')
    ax.set_title('3.2 multimodalitet i landskapet (attraktorar)', loc='left')
    fig.savefig(OUT / 'fig-3.2-multimodal.png', bbox_inches='tight', dpi=300)
    plt.close()

def test_5_22_substrate(mesh, cat):
    """Prop 5.22: Substrate independence (Metal vs Wood in same region)."""
    j = mesh.merge(cat[['ID','matgr']], left_on='objekt_id', right_on='ID')
    cols = ['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity']
    sub = j[j.matgr.isin(['tre', 'metall'])].dropna(subset=cols)
    X = sub[cols].values
    Xn = StandardScaler().fit_transform(X)
    
    # 1-NN check: Does metal have wood as neighbor?
    nbrs = NearestNeighbors(n_neighbors=5).fit(Xn)
    distances, indices = nbrs.kneighbors(Xn)
    
    # Cross-substrate neighbors
    cross_count = 0
    for i in range(len(indices)):
        my_mat = sub.iloc[i].matgr
        neighbor_mats = sub.iloc[indices[i][1:]].matgr.values
        if any(neighbor_mats != my_mat):
            cross_count += 1
    
    ratio = cross_count / len(indices)
    
    fig, ax = plt.subplots(figsize=(6, 5))
    pca = PCA(n_components=2); Xp = pca.fit_transform(Xn)
    ax.scatter(Xp[sub.matgr=='tre', 0], Xp[sub.matgr=='tre', 1], s=5, c='white', edgecolor=INK, alpha=0.3, label='tre')
    ax.scatter(Xp[sub.matgr=='metall', 0], Xp[sub.matgr=='metall', 1], s=10, c=INK, alpha=0.6, label='metall')
    ax.set_title(f'5.22 substrat-uavhengigheit\n({ratio*100:.1f}% har naboar i anna materiale)', loc='left')
    ax.legend()
    fig.savefig(OUT / 'fig-5.22-substrate.png', bbox_inches='tight', dpi=300)
    plt.close()

def test_6_3_complexity(mesh, cat):
    """Prop 6.3: Complexity/Resolution over time."""
    j = mesh.merge(cat[['ID','Fra']], left_on='objekt_id', right_on='ID')
    j = j[j.Fra > 1500].dropna(subset=['complexity', 'Fra'])
    j['period'] = (j.Fra // 25) * 25
    stats = j.groupby('period')['complexity'].agg(['mean', 'std']).dropna()
    
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(stats.index, stats['mean'], color=INK, marker='.', markersize=4)
    ax.fill_between(stats.index, stats['mean'] - stats['std']*0.5, stats['mean'] + stats['std']*0.5, color=INK, alpha=0.05)
    ax.set_xlabel('årstal')
    ax.set_ylabel('geometrisk kompleksitet')
    ax.set_title('6.3 artikulering og bandbreidde over tid', loc='left')
    fig.savefig(OUT / 'fig-6.3-complexity.png', bbox_inches='tight', dpi=300)
    plt.close()

if __name__ == '__main__':
    mesh, cat = load()
    test_3_2_multimodality(mesh)
    test_5_22_substrate(mesh, cat)
    test_6_3_complexity(mesh, cat)
    print('Extra propositions tested.')
