#!/usr/bin/env python3
"""
v3 figures — Töpfer Edition.
Publication-quality monochrome line-art designs for FORMLÆRE.
"""
import sys
import re
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import gridspec
from scipy.stats import gaussian_kde, wasserstein_distance
from scipy.spatial import cKDTree, ConvexHull
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
MESH = ROOT / 'analysis' / 'mesh_features.csv'
CAT = ROOT / 'STOLAR' / 'STOLAR.csv'
OUT = ROOT / 'analysis' / 'figures'
OUT.mkdir(exist_ok=True)

# Palette — Töpfer-Technical with Functional Color
INK = '#1a1a1a'
PAPER = '#fbfbf8'
GRID = '#e8e7df'
CORE_AREA = '#FFF9E6' # Pale yellow for background regions

# Material Palette (from I-3_morphospace_kart.png)
MAT_COLORS = {
    'tre':     '#A88C7B', # Brownish
    'metall':  '#5C6B7F', # Blueish grey
    'plast':   '#C8a268', # Orange/Gold
    'tekstil': '#4F7B52', # Greenish
    'anna':    '#bbbbbb'  # Neutral grey
}

STYLE = {
    'figure.facecolor': 'white',
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'axes.facecolor': PAPER,
    'axes.edgecolor': INK,
    'axes.labelcolor': INK,
    'axes.titlecolor': INK,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.linewidth': 0.6,
    'xtick.color': INK,
    'ytick.color': INK,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'font.family': 'serif',
    'font.serif': ['EB Garamond', 'Garamond', 'Palatino', 'serif'],
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 9,
    'legend.frameon': False,
    'legend.fontsize': 8,
    'lines.linewidth': 0.8,
    'patch.linewidth': 0.5,
}
plt.rcParams.update(STYLE)

def load():
    mesh = pd.read_csv(MESH)
    cat = pd.read_csv(CAT, encoding='utf-8')
    rename = {cat.columns[i]: c for i, c in enumerate([
        'Namn','Bilete','Fra','Mat','MatK','Nasjmus','ID','PStad','Prod','Til',
        'GLB','Vekt','Nasj','URL','Emneord','Erverving','SH','Stil','Tekn',
        'Br','Dat','Dj','Ho','Nemn','Hundre',
    ])}
    cat = cat.rename(columns=rename)
    for c in ['Fra','Br','Ho','Dj']:
        cat[c] = pd.to_numeric(cat[c], errors='coerce')
    def matgrp(s):
        s = (s or '').lower()
        if 'plast' in s: return 'plast'
        if 'stål' in s or 'metall' in s or 'jern' in s: return 'metall'
        if any(x in s for x in ['tre','eik','furu','mahogni','teak','bjørk','bøk','asp']): return 'tre'
        if any(x in s for x in ['tekstil','lær','skinn','stoff','ull','fløyel']): return 'tekstil'
        return 'anna'
    cat['matgr'] = cat.Mat.apply(matgrp)
    return mesh, cat

def fig_1_4(cat):
    geo = cat[(cat.Br > 0) & (cat.Ho > 0) & (cat.Dj > 0)].dropna(subset=['Ho','Br','Dj'])
    Xn = StandardScaler().fit_transform(geo[['Ho','Br','Dj']].values)
    tree = cKDTree(Xn)
    d, _ = tree.query(Xn, k=2)
    nn = d[:, 1]; nn = nn[nn > 0]
    cv = nn.std() / nn.mean()
    
    # Scatter mapping
    for c in ['Ho','Br','Dj']:
        lo, hi = geo[c].quantile([0.005, 0.995])
        geo = geo[(geo[c] >= lo) & (geo[c] <= hi)]
    cx, cy = geo.Br.median(), geo.Ho.median()

    fig = plt.figure(figsize=(12, 5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1.2, 1], wspace=0.25)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    # Core area rectangle (the "yellow box" from I-3)
    rect = plt.Rectangle((geo.Br.quantile(0.1), geo.Ho.quantile(0.1)), 
                         geo.Br.quantile(0.9)-geo.Br.quantile(0.1), 
                         geo.Ho.quantile(0.9)-geo.Ho.quantile(0.1),
                         facecolor=CORE_AREA, alpha=0.4, zorder=0)
    ax1.add_patch(rect)

    # Scatter colored by material
    for m, color in MAT_COLORS.items():
        sub = geo[geo.matgr == m]
        ax1.scatter(sub.Br, sub.Ho, s=6, c=color, alpha=0.5, edgecolor='none', label=m, zorder=2)
    
    # KDE Contours with brownish gradient
    x, y = geo.Br.values, geo.Ho.values
    kde = gaussian_kde(np.vstack([x, y]))
    xi, yi = np.linspace(x.min(), x.max(), 100), np.linspace(y.min(), y.max(), 100)
    Xi, Yi = np.meshgrid(xi, yi)
    Zi = kde(np.vstack([Xi.ravel(), Yi.ravel()])).reshape(Xi.shape)
    ax1.contour(Xi, Yi, Zi, levels=8, cmap='YlOrBr', linewidths=0.5, alpha=0.7, zorder=3)
    
    # Attractor Cross
    ax1.axvline(cx, color=INK, linestyle='--', linewidth=0.5, alpha=0.6)
    ax1.axhline(cy, color=INK, linestyle='--', linewidth=0.5, alpha=0.6)
    ax1.scatter([cx], [cy], marker='+', s=200, color=INK, linewidths=1.5, zorder=10)
    
    ax1.set_xlabel('breidde (cm)')
    ax1.set_ylabel('høgde (cm)')
    ax1.set_title('i. formrommet (h, b) — tettleik og materiale', loc='left')
    ax1.legend(loc='upper right', markerscale=1.5)

    ax2.hist(nn[nn < np.percentile(nn, 99)], bins=40, color='#5C6B7F', edgecolor=INK, linewidth=0.5, alpha=0.7)
    ax2.axvline(nn.mean(), color='#C8553D', linewidth=1.5)
    ax2.set_xlabel('standardisert nn-avstand')
    ax2.set_title(f'ii. nn-distanse (cv = {cv:.2f})', loc='left')
    ax2.text(0.95, 0.85, f'ratio = {cv/0.36:.1f}×', transform=ax2.transAxes, ha='right',
             bbox=dict(boxstyle='square,pad=0.5', facecolor='white', edgecolor=INK, linewidth=0.5))
    
    fig.savefig(OUT / 'fig-1.4-morphospace.png', bbox_inches='tight')
    plt.close()

def fig_2_4(cat):
    geo = cat[(cat.Br > 0) & (cat.Ho > 0) & (cat.Dj > 0)].dropna(subset=['Ho','Br','Dj','Stil','matgr'])
    geo['HW'] = geo.Ho / geo.Br
    le_s = LabelEncoder(); geo['s_e'] = le_s.fit_transform(geo.Stil)
    le_m = LabelEncoder(); geo['m_e'] = le_m.fit_transform(geo.matgr)
    targets = [('h', 'Ho'), ('b', 'Br'), ('d', 'Dj'), ('h/b', 'HW')]
    s_v, m_v, rats = [], [], []
    for _, col in targets:
        s = mutual_info_regression(geo[['s_e']], geo[col], discrete_features=True)[0]
        m = mutual_info_regression(geo[['m_e']], geo[col], discrete_features=True)[0]
        s_v.append(s); m_v.append(m); rats.append(s/m if m>0 else 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={'wspace': 0.3})
    x = np.arange(len(targets))
    ax1.bar(x - 0.15, s_v, 0.3, color='#5C6B7F', edgecolor=INK, alpha=0.8, label='stilperiode')
    ax1.bar(x + 0.15, m_v, 0.3, color='#A88C7B', edgecolor=INK, alpha=0.8, label='materialgruppe')
    ax1.set_xticks(x); ax1.set_xticklabels([t[0] for t in targets])
    ax1.set_ylabel('nmi (bits)')
    ax1.set_title('i. prediktor-styrke', loc='left')
    ax1.legend()

    ax2.hlines(range(len(targets)), 1, rats, colors=INK, linewidth=0.8)
    ax2.scatter(rats, range(len(targets)), color='#C8a268', s=40, edgecolor=INK, zorder=3)
    ax2.set_yticks(range(len(targets))); ax2.set_yticklabels([t[0] for t in targets])
    ax2.set_xlabel('forholdstal (stil/mat)')
    ax2.set_title('ii. relativ dominans', loc='left')
    fig.savefig(OUT / 'fig-2.4-prediktor.png', bbox_inches='tight')
    plt.close()

def fig_3_3(mesh):
    cols = ['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity', 'area', 'vol_hull']
    sub = mesh.dropna(subset=cols)
    cvs = [sub[c].std() / sub[c].mean() for c in cols]
    order = np.argsort(cvs)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(range(len(cols)), [cvs[i] for i in order], color='white', edgecolor=INK, height=0.5)
    ax.set_yticks(range(len(cols))); ax.set_yticklabels([cols[i] for i in order])
    ax.set_xscale('log'); ax.set_xlabel('cv (log)')
    ax.set_title('kanalisering: hierarki av mesh-trekk', loc='left')
    fig.savefig(OUT / 'fig-3.3-channeling-v2.png', bbox_inches='tight')
    plt.close()

def fig_3_4(mesh, cat):
    j = mesh.merge(cat[['ID','Stil']], left_on='objekt_id', right_on='ID')
    j = j.dropna(subset=['sphericity','fill_ratio','inertia_ratio','complexity','Stil'])
    big = j.Stil.value_counts(); big = big[big >= 30].index
    j = j[j.Stil.isin(big)]
    Xn = StandardScaler().fit_transform(j[['sphericity','fill_ratio','inertia_ratio','complexity']].values)
    pca = PCA(n_components=2); Xp = pca.fit_transform(Xn)
    sil = silhouette_score(Xn, j.Stil.values)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(Xp[:, 0], Xp[:, 1], s=3, c=INK, alpha=0.1)
    for s in j.Stil.unique():
        pts = Xp[j.Stil == s]
        if len(pts) > 6:
            hull = ConvexHull(pts)
            for simplex in hull.simplices:
                ax.plot(pts[simplex, 0], pts[simplex, 1], color=INK, linewidth=0.3, alpha=0.4)
    ax.set_title(f'stilar som gradientar (silhouette = {sil:.2f})', loc='left')
    fig.savefig(OUT / 'fig-3.4-silhouette.png', bbox_inches='tight')
    plt.close()

def fig_4_4(cat, mesh):
    # Catalog
    sub = cat.dropna(subset=['Ho','Br','Dj','Fra'])
    sub = sub[(sub.Ho > 0) & (sub.Br > 0) & (sub.Dj > 0) & (sub.Fra >= 1200)]
    sub['period'] = (sub.Fra // 25) * 25
    pts_cum = []
    c_r = []
    for p in sorted(sub.period.unique()):
        pts_cum.extend(sub[sub.period <= p][['Ho','Br','Dj']].values.tolist())
        if len(pts_cum) >= 10:
            try: c_r.append((p, ConvexHull(np.array(pts_cum), qhull_options='QJ').volume))
            except: pass
    c_arr = np.array(c_r)

    # Mesh
    j = mesh.merge(cat[['ID','Fra']], left_on='objekt_id', right_on='ID')
    j = j.dropna(subset=['sphericity','fill_ratio','inertia_ratio','complexity','Fra'])
    j['period'] = (j.Fra // 25) * 25
    pts_cum = []
    m_r = []
    for p in sorted(j.period.unique()):
        pts_cum.extend(j[j.period <= p][['sphericity','fill_ratio','inertia_ratio','complexity']].values.tolist())
        if len(pts_cum) >= 10:
            try: m_r.append((p, ConvexHull(np.array(pts_cum), qhull_options='QJ').volume))
            except: pass
    m_arr = np.array(m_r)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True, gridspec_kw={'hspace': 0.25})
    ax1.step(c_arr[:, 0], c_arr[:, 1], where='post', color=INK)
    ax1.set_yscale('log'); ax1.set_ylabel('katalog-hylster (log)')
    ax1.set_title('i. monoton ekspansjon (katalog)', loc='left')
    ax2.step(m_arr[:, 0], m_arr[:, 1], where='post', color=INK)
    ax2.set_yscale('log'); ax2.set_ylabel('mesh-hylster (log)'); ax2.set_xlabel('årstal')
    ax2.set_title('ii. monoton ekspansjon (mesh)', loc='left')
    fig.savefig(OUT / 'fig-4.4-hull.png', bbox_inches='tight')
    plt.close()

def fig_4_5(cat):
    sub = cat[cat.Nasj.fillna('').str.contains('Noreg|norsk', case=False)].copy()
    sub['HW'] = sub.Ho / sub.Br
    sub['mahogni'] = sub.Mat.apply(lambda s: 'mahogni' in str(s).lower())
    sub['period'] = (sub.Fra // 25) * 25
    periods = sorted([p for p in sub.period.dropna().unique() if 1700 <= p <= 1900])
    rows = []
    for p in periods:
        s = sub[sub.period == p]
        if len(s) >= 3: rows.append((p, s.mahogni.mean(), s.HW.std()/s.HW.mean()))
    arr = np.array(rows)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True, gridspec_kw={'hspace': 0.1})
    bars = ax1.bar(arr[:, 0], arr[:, 1]*100, width=20, color='white', edgecolor=INK)
    for i, p in enumerate(arr[:, 0]):
        if 1825 <= p <= 1849: bars[i].set_hatch('////')
    ax1.set_ylabel('% mahogni'); ax1.set_title('mahogni-kollapsen (noreg)', loc='left')
    ax2.plot(arr[:, 0], arr[:, 2], color=INK, marker='.', markersize=4)
    ax2.set_ylabel('cv(h/b)'); ax2.set_xlabel('årstal')
    fig.savefig(OUT / 'fig-4.5-mahogni.png', bbox_inches='tight')
    plt.close()

def fig_4_1(cat):
    sub = cat[(cat.Ho > 0) & (cat.Br > 0) & (cat.Dj > 0)].dropna(subset=['Fra'])
    sub['period'] = (sub.Fra // 50) * 50
    ps = sorted(sub.period.unique())
    M = np.zeros((len(ps), len(ps)))
    for i, pi in enumerate(ps):
        a = sub[sub.period == pi].Ho.values
        if len(a) < 5: continue
        for j, pj in enumerate(ps):
            b = sub[sub.period == pj].Ho.values
            if len(b) < 5: continue
            M[i, j] = wasserstein_distance(a, b)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(M, cmap='Greys', origin='lower')
    ax.set_xticks(range(len(ps))); ax.set_xticklabels([str(int(p)) for p in ps], rotation=45, ha='right')
    ax.set_yticks(range(len(ps))); ax.set_yticklabels([str(int(p)) for p in ps])
    ax.set_title('wasserstein-distanse over tid', loc='left')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.savefig(OUT / 'fig-falsification-4.1.png', bbox_inches='tight')
    plt.close()

def main():
    mesh, cat = load()
    fig_1_4(cat)
    fig_2_4(cat)
    fig_3_3(mesh)
    fig_3_4(mesh, cat)
    fig_4_4(cat, mesh)
    fig_4_5(cat)
    fig_4_1(cat)
    print('done.')

if __name__ == '__main__':
    main()
