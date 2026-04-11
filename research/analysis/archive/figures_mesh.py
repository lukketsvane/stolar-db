#!/usr/bin/env python3
"""
Generate publication figures for the mesh-based hypothesis tests.

Outputs to analysis/figures/:
  mesh-3.3-channeling.png    CV bar chart of mesh features (kanaliseringshierarki)
  mesh-3.4-silhouette.png    PCA scatter, points coloured by stilperiode
  mesh-5.22-substrate.png    k-NN material homogeneity (substrate-independence)
  mesh-NMI-uplift.png        NMI(stil; feat) catalog vs mesh
  mesh-4.4-hull.png          Cumulative mesh-feature hull volume by 25-year period
"""
from __future__ import annotations
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import warnings; warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import normalized_mutual_info_score
from scipy.spatial import cKDTree, ConvexHull

ROOT = Path(__file__).resolve().parent.parent
MESH = ROOT / 'analysis' / 'mesh_features.csv'
CAT = ROOT / 'STOLAR' / 'STOLAR.csv'
OUT = ROOT / 'analysis' / 'figures'
OUT.mkdir(exist_ok=True)

STYLE = {
    'figure.facecolor': 'white', 'axes.facecolor': '#f8f8f6',
    'axes.spines.top': False, 'axes.spines.right': False,
    'font.family': 'serif', 'font.size': 10,
}
plt.rcParams.update(STYLE)


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    mesh = pd.read_csv(MESH)
    cat = pd.read_csv(CAT, encoding='utf-8')
    cat.columns = ['Namn','Bilete','Fra','Mat','MatK','Nasjmus','ID','PStad','Prod','Til',
                   'GLB','Vekt','Nasj','URL','Emneord','Erverving','SH','Stil','Tekn',
                   'Br','Dat','Dj','Ho','Nemn','Hundre']
    for c in ['Fra','Br','Ho','Dj']:
        cat[c] = pd.to_numeric(cat[c], errors='coerce')
    def matgrp(s):
        s = (s or '').lower()
        if 'plast' in s: return 'plast'
        if 'st\xe5l' in s or 'metall' in s or 'jern' in s: return 'metall'
        if any(x in s for x in ['tre','eik','eg','furu','mahogni','teak','bj\xf8rk','b\xf8k','asp']): return 'tre'
        return 'anna'
    cat['matgr'] = cat.Mat.apply(matgrp)
    return mesh, cat


def fig_3_3_channeling(mesh: pd.DataFrame) -> None:
    """Bar chart of CV per mesh feature, sorted ascending (most → least channeled)."""
    cols = ['sphericity','fill_ratio','inertia_ratio','complexity','vol_hull','area','bbox_y','bbox_x','bbox_z']
    sub = mesh.dropna(subset=cols)
    cvs = {c: sub[c].std() / max(abs(sub[c].mean()), 1e-9) for c in cols}
    items = sorted(cvs.items(), key=lambda kv: kv[1])
    labels, vals = zip(*items)
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    colors = plt.cm.RdYlBu_r(np.linspace(0.15, 0.85, len(items)))
    bars = ax.barh(range(len(items)), vals, color=colors, edgecolor='#444', linewidth=0.5)
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels(labels)
    ax.set_xlabel('Variasjonskoeffisient (std / mean)')
    ax.set_title(f'Kanaliseringshierarki i mesh-trekk-rommet ({vals[-1]/vals[0]:.0f}× spreiing)',
                 fontweight='bold')
    ax.set_xscale('log')
    ax.axvline(0.5, color='#888', linewidth=0.5, linestyle='--', alpha=0.5)
    ax.text(0.5, len(items)-0.3, '  CV ≈ 0.5', fontsize=8, color='#666', va='top')
    for i, (lbl, v) in enumerate(items):
        ax.text(v * 1.05, i, f'{v:.3f}', va='center', fontsize=8)
    ax.text(0.98, 0.05, f'n = {len(sub)} stolar',
            transform=ax.transAxes, ha='right', fontsize=8, color='#666')
    plt.tight_layout()
    p = OUT / 'mesh-3.3-channeling.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_3_4_silhouette(mesh: pd.DataFrame, cat: pd.DataFrame) -> None:
    """PCA scatter in 4D mesh feature space, points colored by stilperiode.
    Negative silhouette → no visual cluster boundaries."""
    j = mesh.merge(cat[['ID','Stil']], left_on='objekt_id', right_on='ID', how='inner')
    j = j.dropna(subset=['sphericity','fill_ratio','inertia_ratio','complexity','Stil'])
    big = j.Stil.value_counts()
    big = big[big >= 30].index
    j = j[j.Stil.isin(big)]
    X = j[['sphericity','fill_ratio','inertia_ratio','complexity']].values
    Xn = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2)
    Xp = pca.fit_transform(Xn)
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    styles = sorted(j.Stil.unique())
    cmap = plt.cm.tab20
    for i, s in enumerate(styles):
        mask = (j.Stil == s).values
        ax.scatter(Xp[mask, 0], Xp[mask, 1],
                   c=[cmap(i / max(len(styles)-1, 1))],
                   s=18, alpha=0.55, edgecolor='none', label=s)
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f} % varians)')
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f} % varians)')
    from sklearn.metrics import silhouette_score as _sil
    sil = _sil(Xn, j.Stil.values)
    ax.set_title(f'Stilperiodar i 4D mesh-trekk-rommet (silhouette = {sil:.2f})',
                 fontweight='bold')
    ax.legend(fontsize=7, loc='center left', bbox_to_anchor=(1.01, 0.5),
              markerscale=2, frameon=False)
    ax.text(0.02, 0.02, f'n = {len(j)}, {len(styles)} stilar (≥ 30 per stil)',
            transform=ax.transAxes, fontsize=8, color='#666')
    plt.tight_layout()
    p = OUT / 'mesh-3.4-silhouette.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_5_22_substrate(mesh: pd.DataFrame, cat: pd.DataFrame) -> None:
    """k-NN material homogeneity histogram: how often does a chair share material
    with its mesh-space nearest neighbours? If substrate-independent, the
    distribution is centred near the random base rate."""
    j = mesh.merge(cat[['ID','matgr']], left_on='objekt_id', right_on='ID', how='inner')
    j = j.dropna(subset=['sphericity','fill_ratio','inertia_ratio','complexity','matgr'])
    j = j[j.matgr != 'anna']
    X = j[['sphericity','fill_ratio','inertia_ratio','complexity']].values
    Xn = StandardScaler().fit_transform(X)
    tree = cKDTree(Xn)
    k = 10
    _, idx = tree.query(Xn, k=k+1)
    mats = j.matgr.values
    same_frac = np.array([
        np.mean(mats[idx[i, 1:]] == mats[i]) for i in range(len(j))
    ])
    base = sum((c/len(mats))**2 for c in pd.Series(mats).value_counts())

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.hist(same_frac, bins=np.linspace(0, 1, 22), color='#7A9CC6',
            edgecolor='#2E5C8A', alpha=0.85)
    ax.axvline(base, color='#C8553D', linewidth=2.0, linestyle='--',
               label=f'Tilfeldig basis = {base:.2f}')
    ax.axvline(same_frac.mean(), color='#388E3C', linewidth=2.0,
               label=f'Observert middel = {same_frac.mean():.2f}')
    ax.axvline(1.0, color='#666', linewidth=1.0, linestyle=':',
               label='Perfekt determinasjon = 1.0')
    ax.set_xlabel('Andel av 10 nærmaste mesh-naboar med same material')
    ax.set_ylabel('Tal stolar')
    ax.set_title(f'Substrat-uavhengigheit i mesh-rommet (excess +{same_frac.mean()-base:.2f} over tilfeldig)',
                 fontweight='bold')
    ax.legend(loc='upper left', fontsize=9, frameon=False)
    ax.text(0.98, 0.95, f'n = {len(j)}\nk = {k}',
            transform=ax.transAxes, ha='right', va='top', fontsize=8, color='#666')
    plt.tight_layout()
    p = OUT / 'mesh-5.22-substrate.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_NMI_uplift(mesh: pd.DataFrame, cat: pd.DataFrame) -> None:
    """Bar comparison: NMI(stil; X) for catalog dimensions vs mesh features."""
    j = mesh.merge(cat[['ID','Stil','Ho','Br','Dj']], left_on='objekt_id', right_on='ID', how='inner')
    j = j.dropna(subset=['Stil','Ho','Br','Dj','sphericity','fill_ratio','inertia_ratio','complexity'])

    def discr(x, bins=20):
        return pd.cut(x, bins=bins, labels=False, duplicates='drop')

    catalog_pairs = [
        ('H', j.Ho), ('W', j.Br), ('D', j.Dj),
    ]
    mesh_pairs = [
        ('sphericity', j.sphericity),
        ('fill_ratio', j.fill_ratio),
        ('inertia_ratio', j.inertia_ratio),
        ('complexity', j.complexity),
    ]
    catalog_nmis = [normalized_mutual_info_score(j.Stil, discr(v)) for _, v in catalog_pairs]
    mesh_nmis = [normalized_mutual_info_score(j.Stil, discr(v)) for _, v in mesh_pairs]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    cat_x = np.arange(len(catalog_pairs))
    mesh_x = np.arange(len(mesh_pairs)) + len(catalog_pairs) + 0.7
    ax.bar(cat_x, catalog_nmis, color='#A88C7B', edgecolor='#5C4534', label='Katalogdimensjonar')
    ax.bar(mesh_x, mesh_nmis, color='#7A9CC6', edgecolor='#2E5C8A', label='Mesh-trekk')
    all_x = list(cat_x) + list(mesh_x)
    all_lbl = [n for n, _ in catalog_pairs] + [n for n, _ in mesh_pairs]
    ax.set_xticks(all_x)
    ax.set_xticklabels(all_lbl, rotation=0, fontsize=9)
    ax.set_ylabel('NMI(stilperiode; trekk)')
    cat_mean = np.mean(catalog_nmis)
    mesh_mean = np.mean(mesh_nmis)
    ax.axhline(cat_mean, color='#A88C7B', linestyle='--', alpha=0.6,
               label=f'Katalog-middel = {cat_mean:.3f}')
    ax.axhline(mesh_mean, color='#2E5C8A', linestyle='--', alpha=0.6,
               label=f'Mesh-middel = {mesh_mean:.3f}')
    uplift = mesh_mean / cat_mean if cat_mean > 0 else float('inf')
    ax.set_title(f'NMI-løft frå katalog til mesh-trekk: {uplift:.2f}×',
                 fontweight='bold')
    ax.legend(loc='upper left', fontsize=8, frameon=False)
    ax.text(0.98, 0.05, f'n = {len(j)}', transform=ax.transAxes,
            ha='right', fontsize=8, color='#666')
    plt.tight_layout()
    p = OUT / 'mesh-NMI-uplift.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_4_4_hull(mesh: pd.DataFrame, cat: pd.DataFrame) -> None:
    """Cumulative mesh-feature 4D convex hull volume vs 25-year period."""
    j = mesh.merge(cat[['ID','Fra']], left_on='objekt_id', right_on='ID', how='inner')
    j = j.dropna(subset=['sphericity','fill_ratio','inertia_ratio','complexity','Fra'])
    j = j.copy()
    j['period'] = (j.Fra // 25) * 25
    periods = sorted(j.period.unique())
    cumulative = []
    rows = []
    for p_year in periods:
        cumulative.extend(j[j.period <= p_year][['sphericity','fill_ratio','inertia_ratio','complexity']].values.tolist())
        if len(cumulative) >= 5:
            try:
                h = ConvexHull(np.array(cumulative))
                rows.append((p_year, h.volume, len(cumulative)))
            except Exception:
                pass
    if not rows:
        print('insufficient data for hull figure'); return
    arr = np.array(rows)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(arr[:, 0], arr[:, 1], marker='o', color='#2E5C8A', linewidth=1.8, markersize=5)
    ax.fill_between(arr[:, 0], 0, arr[:, 1], color='#7A9CC6', alpha=0.25)
    ax.set_xlabel('25-årsperiode')
    ax.set_ylabel('Kumulativt konveks hylsterveolum (4D mesh-trekk)')
    growth = arr[-1, 1] / arr[0, 1] if arr[0, 1] > 0 else float('inf')
    ax.set_title(f'Kumulativ ekspansjon av mesh-formrommet (vekst {growth:.0f}×, monotont)',
                 fontweight='bold')
    ax.set_yscale('log')
    # Annotate with technological breakthroughs
    bp = [(1860, 'dampbøying'), (1925, 'rør-stål'), (1960, 'sprøytestøyping')]
    for yr, lbl in bp:
        if arr[0, 0] <= yr <= arr[-1, 0]:
            ax.axvline(yr, color='#C8553D', linestyle=':', alpha=0.5, linewidth=1.0)
            ax.text(yr, arr[:, 1].max() * 1.1, lbl, rotation=90,
                    fontsize=7, color='#C8553D', va='top', ha='right')
    ax.text(0.02, 0.95, f'V_first = {arr[0,1]:.3g}\nV_last  = {arr[-1,1]:.3g}',
            transform=ax.transAxes, va='top', fontsize=8, color='#666',
            family='monospace')
    plt.tight_layout()
    pf = OUT / 'mesh-4.4-hull.png'
    fig.savefig(pf, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {pf}')


def main() -> int:
    print('loading data...')
    mesh, cat = load()
    print(f'  mesh: {len(mesh)} rows, cat: {len(cat)} rows')
    fig_3_3_channeling(mesh)
    fig_3_4_silhouette(mesh, cat)
    fig_5_22_substrate(mesh, cat)
    fig_NMI_uplift(mesh, cat)
    fig_4_4_hull(mesh, cat)
    print('\ndone.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
