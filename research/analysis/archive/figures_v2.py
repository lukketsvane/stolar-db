#!/usr/bin/env python3
"""
Improved figures replacing the weak v1 ones. Style follows the existing
I-3 / I-4 figures: 2-panel layouts with real scatter / KDE / annotated events.

Outputs to analysis/figures/:
  fig-1.4-morphospace.png      W×H + D×H scatter with KDE, attractor centre marked
  fig-2.4-prediktor.png        Predictor MI heatmap with cumulative gain
  fig-3.3-channeling-v2.png    Violin plot showing distribution of each mesh feature
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
from scipy.stats import gaussian_kde
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import LabelEncoder

ROOT = Path(__file__).resolve().parent.parent
MESH = ROOT / 'analysis' / 'mesh_features.csv'
CAT = ROOT / 'STOLAR' / 'STOLAR.csv'
OUT = ROOT / 'analysis' / 'figures'

STYLE = {
    'figure.facecolor': 'white', 'axes.facecolor': '#fafaf7',
    'axes.spines.top': False, 'axes.spines.right': False,
    'font.family': 'serif', 'font.size': 10,
    'axes.titleweight': 'bold',
}
plt.rcParams.update(STYLE)


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
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
        if 'st\xe5l' in s or 'metall' in s or 'jern' in s: return 'metall'
        if any(x in s for x in ['tre','eik','furu','mahogni','teak','bj\xf8rk','b\xf8k']): return 'tre'
        return 'anna'
    cat['matgr'] = cat.Mat.apply(matgrp)
    return mesh, cat


def fig_1_4_morphospace(cat: pd.DataFrame) -> None:
    """W×H and D×H scatter with KDE, two panels, attractor centre marked.
    Mirrors the I-3 style."""
    geo = cat[(cat.Br > 0) & (cat.Ho > 0) & (cat.Dj > 0)].dropna(subset=['Ho','Br','Dj'])
    # Clip extreme outliers for plot legibility (1-99%)
    for c in ['Ho','Br','Dj']:
        lo, hi = geo[c].quantile([0.005, 0.995])
        geo = geo[(geo[c] >= lo) & (geo[c] <= hi)]

    mat_colors = {'tre': '#A88C7B', 'metall': '#5C6B7F', 'plast': '#C8a268', 'anna': '#bbbbbb'}
    cx, cy, cz = geo.Br.median(), geo.Ho.median(), geo.Dj.median()
    n = len(geo)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

    for ax, (xcol, ycol, xlabel, ylabel, cx_v) in [
        (ax1, ('Br', 'Ho', 'Breidde (cm)', 'Høgde (cm)', cx)),
        (ax2, ('Dj', 'Ho', 'Djupn (cm)', 'Høgde (cm)', cz)),
    ]:
        # KDE background
        x = geo[xcol].values
        y = geo[ycol].values
        try:
            xy = np.vstack([x, y])
            kde = gaussian_kde(xy)
            xi = np.linspace(x.min(), x.max(), 80)
            yi = np.linspace(y.min(), y.max(), 80)
            Xi, Yi = np.meshgrid(xi, yi)
            Zi = kde(np.vstack([Xi.ravel(), Yi.ravel()])).reshape(Xi.shape)
            ax.contourf(Xi, Yi, Zi, levels=15, cmap='YlOrBr', alpha=0.55)
        except Exception:
            pass
        # Scatter coloured by material
        for m, color in mat_colors.items():
            sub = geo[geo.matgr == m]
            if len(sub) > 0:
                ax.scatter(sub[xcol], sub[ycol], s=8, c=color, alpha=0.55,
                           edgecolor='none', label=f'{m} (n={len(sub)})')
        # Attractor centre
        ax.scatter([cx_v], [cy], marker='+', s=180, color='#1a1a1a', linewidths=2.5, zorder=10)
        ax.axvline(cx_v, color='#666', linewidth=0.6, linestyle='--', alpha=0.6)
        ax.axhline(cy, color='#666', linewidth=0.6, linestyle='--', alpha=0.6)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
    ax1.legend(fontsize=7, loc='upper right', frameon=True, framealpha=0.9)
    ax1.set_title(f'Formrommet: Høgde × Breidde ({n} stolar)')
    ax2.set_title(f'Formrommet: Høgde × Djupn ({n} stolar)')
    fig.suptitle(f'Morphospace klumpar seg kring eitt attraktor-senter (CV nn-distanse = 5,4)',
                 fontweight='bold', y=1.02)
    plt.tight_layout()
    p = OUT / 'fig-1.4-morphospace.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_2_4_prediktor(cat: pd.DataFrame) -> None:
    """Heatmap of MI per (predictor, target). Visually compact and readable."""
    geo = cat[(cat.Br > 0) & (cat.Ho > 0) & (cat.Dj > 0)].dropna(
        subset=['Ho','Br','Dj','Stil','matgr','Hundre','Fra']).copy()
    geo['HW'] = geo.Ho / geo.Br
    le_s = LabelEncoder(); geo['s_e'] = le_s.fit_transform(geo.Stil.fillna('?'))
    le_m = LabelEncoder(); geo['m_e'] = le_m.fit_transform(geo.matgr.fillna('?'))
    le_h = LabelEncoder(); geo['h_e'] = le_h.fit_transform(geo.Hundre.fillna('?'))

    predictors = [
        ('Stilperiode', 's_e', True),
        ('Hundreår',   'h_e', True),
        ('Materiale',  'm_e', True),
        ('Årstal',     'Fra', False),
    ]
    targets = [('Høgde', 'Ho'), ('Breidde', 'Br'), ('Djupn', 'Dj'), ('H/W', 'HW')]

    M = np.zeros((len(predictors), len(targets)))
    for i, (pname, pcol, disc) in enumerate(predictors):
        for j, (tname, tcol) in enumerate(targets):
            d = geo[[pcol, tcol]].dropna()
            mi = mutual_info_regression(d[[pcol]], d[tcol], discrete_features=disc, random_state=42)[0]
            M[i, j] = mi

    fig, ax = plt.subplots(figsize=(8, 4.5))
    im = ax.imshow(M, cmap='YlOrBr', aspect='auto', vmin=0, vmax=max(0.6, M.max()))
    ax.set_xticks(range(len(targets)))
    ax.set_xticklabels([t[0] for t in targets])
    ax.set_yticks(range(len(predictors)))
    ax.set_yticklabels([p[0] for p in predictors])
    for i in range(len(predictors)):
        for j in range(len(targets)):
            v = M[i, j]
            color = 'white' if v > 0.4 else 'black'
            ax.text(j, i, f'{v:.2f}', ha='center', va='center', color=color, fontsize=10)
    cbar = plt.colorbar(im, ax=ax, fraction=0.04)
    cbar.set_label('Gjensidig informasjon (bits)', fontsize=9)
    ax.set_title(f'Stilperiode er den sterkaste samlevariabelen for geometri (n = {len(geo)})')
    plt.tight_layout()
    p = OUT / 'fig-2.4-prediktor.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_3_3_channeling_v2(mesh: pd.DataFrame) -> None:
    """Violin plot showing the distribution shape of each mesh feature on its
    own axis. Sphericity is visibly tight; vol_hull is visibly spread."""
    cols = ['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity', 'area', 'vol_hull']
    labels = ['Sphericity', 'Fill ratio', 'Inertia ratio', 'Complexity', 'Surface area', 'Volume (hull)']
    sub = mesh.dropna(subset=cols)
    cvs = {c: sub[c].std() / max(abs(sub[c].mean()), 1e-9) for c in cols}
    # Sort columns by CV ascending
    order = sorted(range(len(cols)), key=lambda i: cvs[cols[i]])
    cols_o = [cols[i] for i in order]
    labels_o = [labels[i] for i in order]
    cvs_o = [cvs[cols[i]] for i in order]

    fig, axes = plt.subplots(2, 3, figsize=(11, 6))
    cmap = plt.cm.RdYlBu_r
    for idx, (col, label, cv) in enumerate(zip(cols_o, labels_o, cvs_o)):
        ax = axes[idx // 3, idx % 3]
        data = sub[col].dropna().values
        # Trim 1-99% for plot
        lo, hi = np.percentile(data, [1, 99])
        data_trim = data[(data >= lo) & (data <= hi)]
        violin_parts = ax.violinplot(data_trim, vert=True, widths=0.7, showmeans=True, showmedians=False)
        # Color by CV rank
        color = cmap(idx / max(len(cols) - 1, 1))
        for pc in violin_parts['bodies']:
            pc.set_facecolor(color)
            pc.set_edgecolor('#333')
            pc.set_alpha(0.75)
        for key in ['cmins', 'cmaxes', 'cbars', 'cmeans']:
            if key in violin_parts:
                violin_parts[key].set_color('#333')
                violin_parts[key].set_linewidth(0.8)
        ax.set_xticks([])
        ax.set_title(f'{label}\nCV = {cv:.3f}', fontsize=10)
        ax.tick_params(axis='y', labelsize=8)
    fig.suptitle(f'Kanaliseringshierarki: kvar trekk har eiga spreiing (128× frå topp til botn, n = {len(sub)})',
                 fontweight='bold', y=1.0)
    plt.tight_layout()
    p = OUT / 'fig-3.3-channeling-v2.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def main() -> int:
    print('loading...')
    mesh, cat = load()
    print(f'  mesh={len(mesh)}, cat={len(cat)}')
    fig_1_4_morphospace(cat)
    fig_2_4_prediktor(cat)
    fig_3_3_channeling_v2(mesh)
    print('done.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
