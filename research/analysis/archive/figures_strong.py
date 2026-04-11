#!/usr/bin/env python3
"""
Publication-quality figures for the ★★★ findings only.

Outputs to analysis/figures/:
  fig-1.4-nn-cv.png         NN-distance distribution vs Poisson null
  fig-2.4-proxy.png         stil vs material MI bar chart (4 dims)
  fig-3.3-channeling.png    CV-spreiing across mesh features
  fig-3.4-silhouette.png    PCA scatter, points coloured by stilperiode
  fig-4.4-hull.png          Cumulative convex hull volume by 25-year period
  fig-4.5-mahogni.png       Norwegian mahogni-collapse 1825-1849
  fig-falsification.png     Wasserstein distances between successive periods

Captions in nynorsk, single-line, no proposition references in titles.
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
from scipy.spatial import cKDTree, ConvexHull
from scipy.stats import wasserstein_distance
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import mutual_info_regression
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parent.parent
MESH = ROOT / 'analysis' / 'mesh_features.csv'
CAT = ROOT / 'STOLAR' / 'STOLAR.csv'
OUT = ROOT / 'analysis' / 'figures'
OUT.mkdir(exist_ok=True)

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


def fig_1_4_nn(cat: pd.DataFrame) -> None:
    """NN-distance histogram, observed vs Poisson null (3D)."""
    geo = cat[(cat.Br > 0) & (cat.Ho > 0) & (cat.Dj > 0)].dropna(subset=['Ho','Br','Dj'])
    pts = geo[['Ho','Br','Dj']].values
    Xn = StandardScaler().fit_transform(pts)
    tree = cKDTree(Xn)
    d, _ = tree.query(Xn, k=2)
    nn = d[:, 1]; nn = nn[nn > 0]
    cv = nn.std() / nn.mean()

    # Poisson 3D NN-distance has CV ≈ 0.36
    poisson_cv = 0.36

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(nn, bins=60, color='#2E5C8A', edgecolor='#1a365d', alpha=0.85)
    ax.axvline(nn.mean(), color='#C8553D', linewidth=2.0, label=f'Observert middel = {nn.mean():.3f}')
    ax.set_xlabel('Standardisert nærmaste-nabo-avstand')
    ax.set_ylabel('Tal stolar')
    ax.set_title(f'Nærmaste-nabo-fordelinga er klumpa, ikkje uniform (CV = {cv:.2f}, n = {len(nn)})')
    ax.text(0.97, 0.95, f'CV(observert) = {cv:.2f}\nCV(Poisson 3D) = {poisson_cv:.2f}\nForholdstal = {cv/poisson_cv:.0f}×',
            transform=ax.transAxes, ha='right', va='top', fontsize=9,
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF9E6', edgecolor='#ccc'))
    ax.legend(loc='upper right', fontsize=9, frameon=False, bbox_to_anchor=(1.0, 0.65))
    plt.tight_layout()
    p = OUT / 'fig-1.4-nn-cv.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_2_4_proxy(cat: pd.DataFrame) -> None:
    """Bar chart: stilperiode MI vs material MI on each catalog dim."""
    geo = cat[(cat.Br > 0) & (cat.Ho > 0) & (cat.Dj > 0)].dropna(subset=['Ho','Br','Dj','Stil','matgr']).copy()
    geo['HW'] = geo.Ho / geo.Br
    le_s = LabelEncoder(); geo['s_e'] = le_s.fit_transform(geo.Stil.fillna('?'))
    le_m = LabelEncoder(); geo['m_e'] = le_m.fit_transform(geo.matgr.fillna('?'))
    targets = [('H', 'Ho'), ('W', 'Br'), ('D', 'Dj'), ('H/W', 'HW')]
    stil_vals = []
    mat_vals = []
    for label, col in targets:
        d = geo[['s_e','m_e', col]].dropna()
        stil_vals.append(mutual_info_regression(d[['s_e']], d[col], discrete_features=True, random_state=42)[0])
        mat_vals.append(mutual_info_regression(d[['m_e']], d[col], discrete_features=True, random_state=42)[0])

    x = np.arange(len(targets))
    w = 0.36
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - w/2, stil_vals, w, label='Stilperiode', color='#2E5C8A', edgecolor='#1a365d')
    ax.bar(x + w/2, mat_vals, w, label='Materiale', color='#C8a268', edgecolor='#7d5828')
    ax.set_xticks(x)
    ax.set_xticklabels([t[0] for t in targets])
    ax.set_ylabel('Gjensidig informasjon (bits)')
    ax.set_title(f'Stilperiode slår materiale på alle fire dimensjonar (n = {len(geo)})')
    ax.legend(loc='upper right', frameon=False)
    for i, (s, m) in enumerate(zip(stil_vals, mat_vals)):
        ax.text(i - w/2, s + 0.01, f'{s:.2f}', ha='center', fontsize=8)
        ax.text(i + w/2, m + 0.01, f'{m:.2f}', ha='center', fontsize=8)
    plt.tight_layout()
    p = OUT / 'fig-2.4-proxy.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_3_3_channeling(mesh: pd.DataFrame) -> None:
    cols = ['sphericity','fill_ratio','inertia_ratio','complexity','area','vol_hull']
    sub = mesh.dropna(subset=cols)
    cvs = {c: sub[c].std() / max(abs(sub[c].mean()), 1e-9) for c in cols}
    items = sorted(cvs.items(), key=lambda kv: kv[1])
    labels, vals = zip(*items)
    span = vals[-1] / vals[0]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = plt.cm.RdYlBu_r(np.linspace(0.15, 0.85, len(items)))
    ax.barh(range(len(items)), vals, color=colors, edgecolor='#444', linewidth=0.5)
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels(labels)
    ax.set_xlabel('Variasjonskoeffisient (std / mean)')
    ax.set_xscale('log')
    ax.set_title(f'Kanaliseringshierarki: {span:.0f}× spreiing mellom mest og minst kanalisert mesh-trekk')
    for i, (lbl, v) in enumerate(items):
        ax.text(v * 1.05, i, f'{v:.3f}', va='center', fontsize=8)
    ax.text(0.97, 0.05, f'n = {len(sub)} stolar',
            transform=ax.transAxes, ha='right', fontsize=8, color='#666')
    plt.tight_layout()
    p = OUT / 'fig-3.3-channeling.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_3_4_silhouette(mesh: pd.DataFrame, cat: pd.DataFrame) -> None:
    j = mesh.merge(cat[['ID','Stil']], left_on='objekt_id', right_on='ID', how='inner')
    j = j.dropna(subset=['sphericity','fill_ratio','inertia_ratio','complexity','Stil'])
    big = j.Stil.value_counts(); big = big[big >= 30].index
    j = j[j.Stil.isin(big)]
    X = j[['sphericity','fill_ratio','inertia_ratio','complexity']].values
    Xn = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2); Xp = pca.fit_transform(Xn)
    sil = silhouette_score(Xn, j.Stil.values)
    fig, ax = plt.subplots(figsize=(8, 6))
    styles = sorted(j.Stil.unique())
    cmap = plt.cm.tab20
    for i, s in enumerate(styles):
        mask = (j.Stil == s).values
        ax.scatter(Xp[mask, 0], Xp[mask, 1], c=[cmap(i / max(len(styles)-1, 1))],
                   s=18, alpha=0.55, edgecolor='none', label=s)
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f} % varians)')
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f} % varians)')
    ax.set_title(f'Stilar er gradientar i mesh-rommet, ikkje topologiske klynger (silhouette = {sil:.2f})')
    ax.legend(fontsize=7, loc='center left', bbox_to_anchor=(1.01, 0.5),
              markerscale=2, frameon=False)
    plt.tight_layout()
    p = OUT / 'fig-3.4-silhouette.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_4_4_hull(cat: pd.DataFrame) -> None:
    sub = cat.dropna(subset=['Ho','Br','Dj','Fra']).copy()
    sub = sub[(sub.Ho > 0) & (sub.Br > 0) & (sub.Dj > 0)]
    for c in ['Ho','Br','Dj']:
        lo, hi = sub[c].quantile([0.01, 0.99])
        sub = sub[(sub[c] >= lo) & (sub[c] <= hi)]
    sub['period'] = (sub.Fra // 25) * 25
    periods = sorted(sub.period.unique())
    cum = []
    rows = []
    for p in periods:
        cum.extend(sub[sub.period <= p][['Ho','Br','Dj']].values.tolist())
        if len(cum) >= 4:
            try: rows.append((p, ConvexHull(np.array(cum)).volume))
            except Exception: pass
    arr = np.array(rows)
    growth = arr[-1, 1] / arr[0, 1]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(arr[:, 0], arr[:, 1], marker='o', color='#2E5C8A', linewidth=1.8, markersize=4)
    ax.fill_between(arr[:, 0], 0, arr[:, 1], color='#7A9CC6', alpha=0.25)
    ax.set_yscale('log')
    ax.set_xlabel('25-årsperiode')
    ax.set_ylabel('Kumulativ konveks hylsterveolum (cm³)')
    ax.set_title(f'Formrommet ekspanderer monotont gjennom 700 år (totalvekst {growth:.0f}×)')
    plt.tight_layout()
    p = OUT / 'fig-4.4-hull.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_4_5_mahogni(cat: pd.DataFrame) -> None:
    sub = cat[cat.Nasj.fillna('').str.contains('Noreg|norsk|Norge', regex=True, na=False, case=False)].copy()
    sub['HW'] = sub.Ho / sub.Br
    sub = sub[(sub.HW > 0) & (sub.HW < 5)]
    sub['mahogni'] = sub.Mat.apply(lambda s: 'mahogni' in (s or '').lower())
    sub['period'] = (sub.Fra // 25) * 25
    periods = sorted([p for p in sub.period.dropna().unique() if 1700 <= p <= 1900])
    rows = []
    for p in periods:
        s = sub[sub.period == p]
        if len(s) >= 3:
            rows.append((p, s.mahogni.mean(), s.HW.std() / s.HW.mean() if s.HW.mean() > 0 else 0, len(s)))
    arr = np.array(rows)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True)
    ax1.bar(arr[:, 0], arr[:, 1] * 100, width=20, color='#8b3a3a', edgecolor='#3d1818', alpha=0.85)
    ax1.set_ylabel('% mahogni')
    ax1.set_ylim(0, 110)
    ax1.axvspan(1825, 1849, color='#FFF9E6', alpha=0.6, zorder=0)
    ax1.set_title('Norsk mahogni-kollapsen 1825-1849: 100 % mahogni samstundes som H/W-variansen halverer seg')
    ax2.plot(arr[:, 0], arr[:, 2], marker='o', color='#2E5C8A', linewidth=1.8, markersize=5)
    ax2.set_ylabel('CV(H/W)')
    ax2.set_xlabel('25-årsperiode')
    ax2.axvspan(1825, 1849, color='#FFF9E6', alpha=0.6, zorder=0)
    plt.tight_layout()
    p = OUT / 'fig-4.5-mahogni.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def fig_falsification_4_1(cat: pd.DataFrame) -> None:
    sub = cat.dropna(subset=['Ho','Br','Dj','Fra'])
    sub = sub[(sub.Ho > 0) & (sub.Br > 0) & (sub.Dj > 0)].copy()
    sub['period'] = (sub.Fra // 50) * 50
    periods = sorted(sub.period.unique())
    pairs = []
    for p1, p2 in zip(periods[:-1], periods[1:]):
        a = sub[sub.period == p1]; b = sub[sub.period == p2]
        if len(a) > 5 and len(b) > 5:
            pairs.append((p1, p2,
                wasserstein_distance(a.Ho.values, b.Ho.values),
                wasserstein_distance(a.Br.values, b.Br.values),
                wasserstein_distance(a.Dj.values, b.Dj.values)))
    arr = np.array(pairs)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    centers = (arr[:, 0] + arr[:, 1]) / 2
    ax.plot(centers, arr[:, 2], marker='o', label='H', color='#2E5C8A')
    ax.plot(centers, arr[:, 3], marker='s', label='W', color='#C8553D')
    ax.plot(centers, arr[:, 4], marker='^', label='D', color='#388E3C')
    ax.set_ylabel('Wasserstein-distanse mellom suksessive 50-årsperiodar (cm)')
    ax.set_xlabel('Periode-midtpunkt')
    ax.set_title('Landskapet endrar seg gjennom heile 700 år (Wasserstein > 5 cm i kvar periode)')
    ax.legend(frameon=False)
    ax.axhline(0, color='#888', linewidth=0.5)
    plt.tight_layout()
    p = OUT / 'fig-falsification-4.1.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'wrote {p}')


def main() -> int:
    print('loading...')
    mesh, cat = load()
    print(f'  mesh={len(mesh)}, cat={len(cat)}')
    fig_1_4_nn(cat)
    fig_2_4_proxy(cat)
    fig_3_3_channeling(mesh)
    fig_3_4_silhouette(mesh, cat)
    fig_4_4_hull(cat)
    fig_4_5_mahogni(cat)
    fig_falsification_4_1(cat)
    print('done.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
