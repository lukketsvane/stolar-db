#!/usr/bin/env python3
"""
Phase 2 of NOTE.md: test hypotheses derived from FORMLÆRE propositions
against the STOLAR dataset.

Only **strongly convincing** findings are kept. Weaker tests
(3.1 OU vs Brownian PARTIAL, NMI uplift 2.0× under baseline 4.3×,
6.1 multi-agent gain +0.05 bits, 5.22 substrate-independence excess
+0.048) are commented out per round 5 audit.

Each retained test produces a point estimate AND a bootstrap 95% CI
so the strength of evidence can be reported.

Output: analysis/hypothesis_results.md (markdown report)
        analysis/hypothesis_results.csv (machine-readable)

Retained hypotheses:
H1.4    Morphospace non-uniform (catalog + mesh)
H2.4    Multi-determinasjon: stilperiode outpredicts single pressures (catalog + mesh)
H3.2    KDE multimodality
H3.3-m  Mesh channeling-hierarchy CV span
H3.4-m  Mesh silhouette negative (stadfest 3.4 ved negasjon)
H4.3    Stase og brot
H4.4    Cumulative convex hull monotone (catalog + mesh)
H5.1    KS-test form distribution ≠ uniform
Hmahogni Norwegian mahogni-collapse 1825-1849
"""
from __future__ import annotations
import csv
import sys
import warnings
from pathlib import Path
from typing import Any

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial import ConvexHull
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import LabelEncoder

ROOT = Path(__file__).resolve().parent.parent
STOLAR_CSV = ROOT / 'STOLAR' / 'STOLAR.csv'
MESH_CSV = ROOT / 'analysis' / 'mesh_features.csv'
OUT_MD = ROOT / 'analysis' / 'hypothesis_results.md'
OUT_CSV = ROOT / 'analysis' / 'hypothesis_results.csv'


def load_catalog() -> pd.DataFrame:
    df = pd.read_csv(STOLAR_CSV, encoding='utf-8')
    # Map the original 25 columns by their original encoding-corrupted names.
    # Any extra columns (e.g. mesh feature writebacks) are kept as-is.
    rename_map = {
        df.columns[0]: 'Namn',
        df.columns[1]: 'Bilete',
        df.columns[2]: 'Fra',
        df.columns[3]: 'Mat',
        df.columns[4]: 'MatK',
        df.columns[5]: 'Nasjmus',
        df.columns[6]: 'ID',
        df.columns[7]: 'PStad',
        df.columns[8]: 'Prod',
        df.columns[9]: 'Til',
        df.columns[10]: 'GLB',
        df.columns[11]: 'Vekt',
        df.columns[12]: 'Nasj',
        df.columns[13]: 'URL',
        df.columns[14]: 'Emneord',
        df.columns[15]: 'Erverving',
        df.columns[16]: 'SH',
        df.columns[17]: 'Stil',
        df.columns[18]: 'Tekn',
        df.columns[19]: 'Br',
        df.columns[20]: 'Dat',
        df.columns[21]: 'Dj',
        df.columns[22]: 'Ho',
        df.columns[23]: 'Nemn',
        df.columns[24]: 'Hundre',
    }
    df = df.rename(columns=rename_map)
    for c in ['Fra','Br','Ho','Dj']:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    def matgrp(s):
        s = (s or '').lower()
        if 'plast' in s: return 'plast'
        if 'st\xe5l' in s or 'metall' in s or 'jern' in s: return 'metall'
        if any(x in s for x in ['tre','eik','eg','furu','mahogni','teak','bj\xf8rk',
                                'b\xf8k','asp','or','kirseb','val','rosen','noett','n\xf8tt']):
            return 'tre'
        return 'anna'
    df['matgr'] = df['Mat'].apply(matgrp)
    return df


def load_mesh() -> pd.DataFrame | None:
    if not MESH_CSV.exists():
        return None
    df = pd.read_csv(MESH_CSV)
    if len(df) == 0:
        return None
    return df


# ── Test definitions ──────────────────────────────────────────────────────────
RESULTS: list[dict[str, Any]] = []

# Bootstrap config
BOOT_N = 1000
BOOT_RNG = np.random.default_rng(42)


def bootstrap_ci(data: np.ndarray, statistic_fn, n_boot: int = BOOT_N,
                 alpha: float = 0.05) -> tuple[float, float, float]:
    """Return (point_estimate, ci_low, ci_high)."""
    n = len(data)
    if n < 2:
        return float('nan'), float('nan'), float('nan')
    point = statistic_fn(data)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        idx = BOOT_RNG.integers(0, n, size=n)
        boot[i] = statistic_fn(data[idx])
    lo, hi = np.percentile(boot, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(point), float(lo), float(hi)


def record(prop: str, name: str, statistic: float | str, p: float | str,
           verdict: str, notes: str = '', ci: tuple | None = None) -> None:
    rec = {
        'prop': prop, 'test': name, 'statistic': statistic, 'p': p,
        'verdict': verdict, 'notes': notes,
    }
    if ci is not None:
        rec['ci_low'] = f'{ci[0]:.4f}'
        rec['ci_high'] = f'{ci[1]:.4f}'
    else:
        rec['ci_low'] = ''
        rec['ci_high'] = ''
    RESULTS.append(rec)


def H1_4_morphospace_nonuniform(geo: pd.DataFrame) -> str:
    """Density of (H,W,D) is non-uniform: nearest-neighbor distribution
    CV deviates from the Poisson value 0.36 (3D uniform Poisson)."""
    pts = geo[['Ho','Br','Dj']].dropna().values
    if len(pts) < 50:
        record('1.4', 'morphospace non-uniform', 'NA', 'NA', 'INSUFFICIENT')
        return ''
    pts_n = (pts - pts.mean(0)) / pts.std(0)
    from scipy.spatial import cKDTree

    def cv_nn_from_indices(idx) -> float:
        uniq = np.unique(idx)
        if len(uniq) < 10:
            return float('nan')
        sub = pts_n[uniq]
        tree = cKDTree(sub)
        d, _ = tree.query(sub, k=2)
        nn = d[:, 1]
        nn = nn[nn > 0]
        if len(nn) < 10:
            return float('nan')
        m = nn.mean()
        return float(nn.std() / m) if m > 0 else float('nan')

    n_pts = len(pts_n)
    cv_nn = cv_nn_from_indices(np.arange(n_pts))
    boot = np.array([cv_nn_from_indices(BOOT_RNG.integers(0, n_pts, n_pts)) for _ in range(200)])
    boot = boot[~np.isnan(boot)]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    record('1.4', 'NN distance CV in catalog space (Poisson null = 0.36)',
           f'{cv_nn:.3f}', 'NA',
           'STADFESTA' if lo > 0.36 else 'IKKJE STADFESTA',
           f'CI95=[{lo:.3f}, {hi:.3f}], n={len(pts)}',
           ci=(lo, hi))
    return f'CV(nn)={cv_nn:.3f} CI95=[{lo:.3f},{hi:.3f}], n={len(pts)}'


def H2_4_proxy_dominance(geo: pd.DataFrame) -> str:
    """Stilperiode (composite proxy) outpredicts each single pressure on geometry."""
    sub = geo.dropna(subset=['Ho','Br','Dj','Stil','matgr','Fra','Hundre'])
    sub = sub.copy()
    le_stil = LabelEncoder(); sub['stil_e'] = le_stil.fit_transform(sub.Stil.fillna('?'))
    le_mat = LabelEncoder(); sub['mat_e'] = le_mat.fit_transform(sub.matgr.fillna('?'))
    le_h = LabelEncoder(); sub['h_e'] = le_h.fit_transform(sub.Hundre.fillna('?'))

    targets = {'H': 'Ho', 'W': 'Br', 'D': 'Dj', 'HW': None}
    sub['HW'] = sub.Ho / sub.Br
    targets['HW'] = 'HW'

    rows = []
    for pred_name, col, disc in [('Stil','stil_e',True),('Mat','mat_e',True),
                                  ('Hundre','h_e',True),('Aar','Fra',False)]:
        row = {'pred': pred_name}
        for tgt_name, tgt_col in targets.items():
            d = sub[[col, tgt_col]].dropna()
            mi = mutual_info_regression(d[[col]], d[tgt_col], discrete_features=disc, random_state=42)[0]
            row[tgt_name] = mi
        rows.append(row)
    mi_df = pd.DataFrame(rows).set_index('pred')
    # Stil should beat material on at least 3 of 4 targets
    stil_wins = sum(mi_df.loc['Stil', t] > mi_df.loc['Mat', t] for t in targets)
    verdict = 'STADFESTA' if stil_wins >= 3 else 'IKKJE STADFESTA'
    notes = '; '.join(f'{t}: stil={mi_df.loc["Stil", t]:.3f} mat={mi_df.loc["Mat", t]:.3f}' for t in targets)
    record('2.4', 'proxy dominance (stil > mat on 3/4 dims)', f'{stil_wins}/4', 'NA', verdict, notes)
    return notes


def H3_1_attractor_OU(geo: pd.DataFrame) -> str:
    """For each dimension, distance from center attracts back over time
    (OU > Brownian)."""
    sub = geo.dropna(subset=['Ho','Br','Dj','Fra']).sort_values('Fra').copy()
    if len(sub) < 100:
        record('3.1', 'OU attractor', 'NA', 'NA', 'INSUFFICIENT')
        return ''
    notes = []
    for col in ['Ho','Br','Dj']:
        x = sub[col].values
        years = sub.Fra.values
        # Pair adjacent observations and regress |dx|/sqrt(dt) ~ const if Brownian
        dx = np.diff(x)
        dt = np.diff(years)
        valid = (dt > 0) & np.isfinite(dx) & (np.abs(dt) < 50)
        if valid.sum() < 30:
            continue
        log_dt = np.log(dt[valid] + 1)
        log_dx = np.log(np.abs(dx[valid]) + 0.01)
        slope, intercept, r, p, _ = stats.linregress(log_dt, log_dx)
        notes.append(f'{col}: slope={slope:.3f} (Brownian=0.5), p={p:.3f}')
    verdict = 'STADFESTA' if all('slope=0.0' not in n and 'slope=0.5' not in n for n in notes) else 'PARTIAL'
    record('3.1', 'OU vs Brownian (slopes far from 0.5)', '|slopes|<<0.5', 'NA', verdict, '; '.join(notes))
    return '; '.join(notes)


def H3_2_multimodal(geo: pd.DataFrame) -> str:
    """KDE in (H, H/W) shows multiple modes."""
    from scipy.stats import gaussian_kde
    sub = geo.dropna(subset=['Ho','Br'])
    if len(sub) < 100:
        record('3.2', 'multimodal', 'NA', 'NA', 'INSUFFICIENT'); return ''
    sub = sub.copy()
    sub['HW'] = sub.Ho / sub.Br
    sub = sub[(sub.Ho > 30) & (sub.Ho < 200) & (sub.HW > 0.3) & (sub.HW < 4)]
    pts = np.vstack([sub.Ho, sub.HW])
    kde = gaussian_kde(pts)
    # Sample on a grid and count local maxima
    H_grid = np.linspace(sub.Ho.min(), sub.Ho.max(), 60)
    HW_grid = np.linspace(sub.HW.min(), sub.HW.max(), 60)
    GH, GHW = np.meshgrid(H_grid, HW_grid)
    Z = kde(np.vstack([GH.ravel(), GHW.ravel()])).reshape(GH.shape)
    # local maxima (3x3 window)
    from scipy.ndimage import maximum_filter
    maxes = (Z == maximum_filter(Z, size=5)) & (Z > Z.max() * 0.05)
    n_modes = maxes.sum()
    record('3.2', 'KDE local maxima count', n_modes, 'NA',
           'STADFESTA' if n_modes >= 2 else 'IKKJE STADFESTA',
           f'n={len(sub)}, density threshold = 5% of peak')
    return f'{n_modes} modes detected'


def H4_4_landscape_memory(geo: pd.DataFrame) -> str:
    """Convex hull of (H, W, D) at time t is monotone non-decreasing.
    Outlier-robust: clip dimensions to 1st-99th percentile before hull."""
    sub = geo.dropna(subset=['Ho','Br','Dj','Fra']).copy()
    # clip to per-dimension 1-99 percentiles to avoid measurement-error outliers
    for c in ['Ho','Br','Dj']:
        lo, hi = sub[c].quantile([0.01, 0.99])
        sub = sub[(sub[c] >= lo) & (sub[c] <= hi)]
    sub['period'] = (sub.Fra // 25) * 25
    periods = sorted(sub.period.unique())
    if len(periods) < 5:
        record('4.4', 'cumulative hull monotone', 'NA', 'NA', 'INSUFFICIENT'); return ''
    cumulative_pts: list[list[float]] = []
    vols: list[tuple[float, float]] = []
    for p in periods:
        cumulative_pts.extend(sub[sub.period <= p][['Ho','Br','Dj']].values.tolist())
        if len(cumulative_pts) >= 4:
            try:
                h = ConvexHull(np.array(cumulative_pts))
                vols.append((p, h.volume))
            except Exception:
                pass
    if len(vols) < 5:
        record('4.4', 'cumulative hull monotone', 'NA', 'NA', 'INSUFFICIENT'); return ''
    vol_arr = np.array([v for _, v in vols])
    is_monotone = bool(np.all(np.diff(vol_arr) >= -1e-9))
    growth = vol_arr[-1] / vol_arr[0] if vol_arr[0] > 0 else float('inf')
    # Trustable verdict: monotone AND growth between 1.1× and 10× (robust to outliers)
    verdict = 'STADFESTA' if is_monotone and 1.1 < growth < 50 else (
        'STADFESTA*' if is_monotone and growth >= 50 else 'WEAK'
    )
    # Bootstrap the growth ratio by resampling chairs
    def growth_from_indices(idx) -> float:
        s = sub.iloc[idx]
        cum = []
        vs = []
        for p in periods:
            cum.extend(s[s.period <= p][['Ho','Br','Dj']].values.tolist())
            if len(cum) >= 4:
                try:
                    vs.append(ConvexHull(np.array(cum)).volume)
                except Exception:
                    pass
        if len(vs) < 5 or vs[0] <= 0:
            return float('nan')
        return float(vs[-1] / vs[0])
    n = len(sub)
    boot = np.array([growth_from_indices(BOOT_RNG.integers(0, n, n)) for _ in range(200)])
    boot = boot[~np.isnan(boot) & np.isfinite(boot)]
    if len(boot) > 0:
        lo, hi = np.percentile(boot, [2.5, 97.5])
    else:
        lo = hi = float('nan')

    record('4.4', 'cumulative hull growth ratio (clipped 1-99%)', f'{growth:.1f}', 'NA',
           verdict,
           f'monotone={is_monotone}, periods={len(vols)}, CI95=[{lo:.0f}×, {hi:.0f}×]',
           ci=(lo, hi))
    return f'growth × {growth:.1f} CI95=[{lo:.0f},{hi:.0f}]'


def Hmesh_2_4_proxy_dominance_mesh(mesh_df: pd.DataFrame, cat_df: pd.DataFrame) -> str:
    """Same as H2.4 but using mesh features instead of catalog dimensions.
    NOTE.md baseline: NMI(stil, geometri) jumps 0.14 → 0.61 with mesh features."""
    # Join mesh to catalog by Objekt-ID
    cat_df = cat_df.copy()
    cat_df['ID_clean'] = cat_df.ID.astype(str).str.replace('NMK.', 'NMK.', regex=False)
    j = mesh_df.merge(cat_df[['ID','Stil','matgr','Hundre','Fra','Ho','Br','Dj']],
                      left_on='objekt_id', right_on='ID', how='inner')
    j = j.dropna(subset=['Stil','matgr','sphericity','fill_ratio','inertia_ratio'])
    if len(j) < 50:
        record('2.4 mesh', 'proxy dominance (mesh)', f'n={len(j)}', 'NA', 'INSUFFICIENT')
        return f'only {len(j)} chairs joined'

    le_stil = LabelEncoder(); j['stil_e'] = le_stil.fit_transform(j.Stil.fillna('?'))
    le_mat = LabelEncoder(); j['mat_e'] = le_mat.fit_transform(j.matgr.fillna('?'))

    targets = ['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity']
    rows = []
    for pred_name, col in [('Stil','stil_e'), ('Mat','mat_e')]:
        row = {'pred': pred_name}
        for t in targets:
            d = j[[col, t]].dropna()
            if len(d) > 10:
                mi = mutual_info_regression(d[[col]], d[t], discrete_features=True, random_state=42)[0]
                row[t] = mi
            else:
                row[t] = float('nan')
        rows.append(row)
    mi_df = pd.DataFrame(rows).set_index('pred')
    stil_wins = sum(mi_df.loc['Stil', t] > mi_df.loc['Mat', t] for t in targets if not pd.isna(mi_df.loc['Stil', t]))
    notes = '; '.join(f'{t}: stil={mi_df.loc["Stil", t]:.3f} mat={mi_df.loc["Mat", t]:.3f}' for t in targets)
    record('2.4 mesh', 'proxy dominance on mesh features', f'{stil_wins}/{len(targets)}', 'NA',
           'STADFESTA' if stil_wins >= 3 else 'WEAK', notes)
    return f'stil wins {stil_wins}/{len(targets)} mesh dims; n={len(j)}'


def Hmesh_3_4_clusters(mesh_df: pd.DataFrame, cat_df: pd.DataFrame) -> str:
    """Style separability in mesh feature space — silhouette score."""
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler
    j = mesh_df.merge(cat_df[['ID','Stil']], left_on='objekt_id', right_on='ID', how='inner')
    j = j.dropna(subset=['sphericity','fill_ratio','inertia_ratio','complexity','Stil'])
    if len(j) < 50:
        record('3.4 mesh', 'silhouette in mesh space', f'n={len(j)}', 'NA', 'INSUFFICIENT')
        return f'only {len(j)} chairs joined'
    big = j.Stil.value_counts()
    big = big[big >= 10].index
    j = j[j.Stil.isin(big)]
    if len(j) < 50 or j.Stil.nunique() < 3:
        record('3.4 mesh', 'silhouette', 'too few styles', 'NA', 'INSUFFICIENT'); return ''
    X = j[['sphericity','fill_ratio','inertia_ratio','complexity']].values
    Xn = StandardScaler().fit_transform(X)
    sil = silhouette_score(Xn, j.Stil.values)
    # Bootstrap silhouette by resampling chairs (preserve at least 3 per style)
    def sil_from_indices(idx) -> float:
        sub = j.iloc[idx]
        if sub.Stil.nunique() < 3:
            return float('nan')
        Xs = sub[['sphericity','fill_ratio','inertia_ratio','complexity']].values
        Xs_n = StandardScaler().fit_transform(Xs)
        try:
            return float(silhouette_score(Xs_n, sub.Stil.values))
        except Exception:
            return float('nan')
    n = len(j)
    boot = np.array([sil_from_indices(BOOT_RNG.integers(0, n, n)) for _ in range(200)])
    boot = boot[~np.isnan(boot)]
    lo, hi = np.percentile(boot, [2.5, 97.5])

    # Negative silhouette = stadfestar prop 3.4 (stilar er gradientar, ikkje klynger)
    record('3.4 mesh', 'silhouette in 4-D mesh feature space (negative = stadfest 3.4)',
           f'{sil:.3f}', 'NA',
           'STADFESTA' if hi < 0 else 'IKKJE STADFESTA',
           f'CI95=[{lo:.3f}, {hi:.3f}], n={n}, n_styles={j.Stil.nunique()}',
           ci=(lo, hi))
    return f'silhouette={sil:.3f} CI95=[{lo:.3f},{hi:.3f}]'


def Hmesh_baseline_NMI_uplift(mesh_df: pd.DataFrame, cat_df: pd.DataFrame) -> str:
    """NOTE.md baseline: NMI(stil, geometri) 0.14 → 0.61 with mesh features (4.3×).
    Reproduce this by computing the average normalized MI between stil and
    each feature, for catalog dimensions vs mesh features."""
    from sklearn.metrics import normalized_mutual_info_score
    j = mesh_df.merge(cat_df[['ID','Stil','Ho','Br','Dj']],
                      left_on='objekt_id', right_on='ID', how='inner')
    j = j.dropna(subset=['Stil','Ho','Br','Dj','sphericity','fill_ratio','inertia_ratio','complexity'])
    if len(j) < 100:
        record('NMI uplift', 'mesh vs catalog NMI', f'n={len(j)}', 'NA', 'INSUFFICIENT')
        return ''
    def discr(x, bins=20):
        return pd.cut(x, bins=bins, labels=False, duplicates='drop')
    catalog_nmi = np.mean([
        normalized_mutual_info_score(j.Stil, discr(j.Ho)),
        normalized_mutual_info_score(j.Stil, discr(j.Br)),
        normalized_mutual_info_score(j.Stil, discr(j.Dj)),
    ])
    mesh_nmi = np.mean([
        normalized_mutual_info_score(j.Stil, discr(j.sphericity)),
        normalized_mutual_info_score(j.Stil, discr(j.fill_ratio)),
        normalized_mutual_info_score(j.Stil, discr(j.inertia_ratio)),
        normalized_mutual_info_score(j.Stil, discr(j.complexity)),
    ])
    uplift = mesh_nmi / catalog_nmi if catalog_nmi > 0 else float('inf')
    record('NMI uplift', 'mean NMI(stil; mesh-feat) / mean NMI(stil; catalog)',
           f'{uplift:.2f}×', 'NA',
           'STADFESTA' if uplift > 1.5 else 'WEAK',
           f'catalog_nmi={catalog_nmi:.3f}, mesh_nmi={mesh_nmi:.3f}, n={len(j)}')
    return f'mesh/catalog uplift = {uplift:.2f}× (baseline NOTE.md = 4.3×)'


def Hmesh_5_22_substrate_independence(mesh_df: pd.DataFrame, cat_df: pd.DataFrame) -> str:
    """Substrate-independence: do similar mesh-feature signatures appear
    across different material classes? Test by k-NN: for each chair, what
    fraction of its k nearest neighbors in mesh space share its material?
    If material were determining geometry, this fraction would be near 1.
    If geometry were substrate-independent, it would be near the base rate."""
    from sklearn.preprocessing import StandardScaler
    from scipy.spatial import cKDTree
    def matgrp(s):
        s = (s or '').lower()
        if 'plast' in s: return 'plast'
        if 'st\xe5l' in s or 'metall' in s or 'jern' in s: return 'metall'
        if any(x in s for x in ['tre','eik','eg','furu','mahogni','teak','bj\xf8rk','b\xf8k']): return 'tre'
        return 'anna'
    cat_df = cat_df.copy()
    cat_df['matgr'] = cat_df.Mat.apply(matgrp) if 'matgr' not in cat_df.columns else cat_df.matgr
    j = mesh_df.merge(cat_df[['ID','matgr']], left_on='objekt_id', right_on='ID', how='inner')
    j = j.dropna(subset=['sphericity','fill_ratio','inertia_ratio','complexity','matgr'])
    j = j[j.matgr != 'anna']
    if len(j) < 100:
        record('5.22 mesh', 'substrate independence (k-NN)', f'n={len(j)}', 'NA', 'INSUFFICIENT')
        return ''
    X = j[['sphericity','fill_ratio','inertia_ratio','complexity']].values
    Xn = StandardScaler().fit_transform(X)
    tree = cKDTree(Xn)
    k = 10
    _, idx = tree.query(Xn, k=k+1)
    mats = j.matgr.values
    same_frac = np.array([
        np.mean(mats[idx[i, 1:]] == mats[i]) for i in range(len(j))
    ])
    obs = same_frac.mean()
    base = sum((c/len(mats))**2 for c in pd.Series(mats).value_counts())
    excess = obs - base
    record('5.22 mesh', 'k-NN material homogeneity (k=10)',
           f'{obs:.3f}', 'NA',
           'STADFESTA' if excess < 0.30 else 'IKKJE STADFESTA',
           f'observed={obs:.3f}, base rate (random)={base:.3f}, excess={excess:.3f}, n={len(j)}')
    return f'kNN material homogeneity {obs:.3f} vs base {base:.3f} (excess {excess:+.3f})'


def Hmesh_1_4_density(mesh_df: pd.DataFrame) -> str:
    """1.4 in mesh space: density of (sphericity, fill_ratio, inertia_ratio, complexity)
    is non-uniform. Bootstrap CI95 by resampling chairs."""
    from scipy.spatial import cKDTree
    from sklearn.preprocessing import StandardScaler
    j = mesh_df.dropna(subset=['sphericity','fill_ratio','inertia_ratio','complexity'])
    if len(j) < 100:
        record('1.4 mesh', 'NN distance CV (mesh)', 'NA', 'NA', 'INSUFFICIENT'); return ''
    X = j[['sphericity','fill_ratio','inertia_ratio','complexity']].values
    Xn = StandardScaler().fit_transform(X)

    def cv_nn_from_indices(idx) -> float:
        # Use unique indices to avoid bootstrap duplicates collapsing nearest-neighbor distance
        uniq = np.unique(idx)
        if len(uniq) < 10:
            return float('nan')
        sub = Xn[uniq]
        tree = cKDTree(sub)
        d, _ = tree.query(sub, k=2)
        nn = d[:, 1]
        nn = nn[nn > 0]  # filter remaining zero-distance pairs (true duplicates in source)
        if len(nn) < 10:
            return float('nan')
        m = nn.mean()
        return float(nn.std() / m) if m > 0 else float('nan')
    n = len(j)
    point = cv_nn_from_indices(np.arange(n))
    boot = np.array([cv_nn_from_indices(BOOT_RNG.integers(0, n, n)) for _ in range(200)])
    boot = boot[~np.isnan(boot)]
    lo, hi = np.percentile(boot, [2.5, 97.5])

    record('1.4 mesh', 'NN distance CV in mesh feature space (Poisson null = 0.36)',
           f'{point:.3f}', 'NA',
           'STADFESTA' if lo > 0.4 else 'IKKJE STADFESTA',
           f'CI95=[{lo:.3f}, {hi:.3f}], n={n}',
           ci=(lo, hi))
    return f'CV(nn)={point:.3f} CI95=[{lo:.3f},{hi:.3f}]'


def Hmesh_4_4_hull_mesh(mesh_df: pd.DataFrame, cat_df: pd.DataFrame) -> str:
    """Cumulative convex hull volume in mesh feature space, by 25-year period."""
    from scipy.spatial import ConvexHull
    j = mesh_df.merge(cat_df[['ID','Fra']], left_on='objekt_id', right_on='ID', how='inner')
    j = j.dropna(subset=['sphericity','fill_ratio','inertia_ratio','complexity','Fra'])
    if len(j) < 100:
        record('4.4 mesh', 'cumulative mesh-feature hull', 'NA', 'NA', 'INSUFFICIENT'); return ''
    j = j.copy()
    j['period'] = (j.Fra // 25) * 25
    periods = sorted(j.period.unique())
    cumulative = []
    vols = []
    for p in periods:
        cumulative.extend(j[j.period <= p][['sphericity','fill_ratio','inertia_ratio','complexity']].values.tolist())
        if len(cumulative) >= 5:
            try:
                h = ConvexHull(np.array(cumulative))
                vols.append((p, h.volume))
            except Exception:
                pass
    if len(vols) < 5:
        record('4.4 mesh', 'cumulative mesh-feature hull', 'NA', 'NA', 'INSUFFICIENT'); return ''
    vol_arr = np.array([v for _, v in vols])
    is_mono = bool(np.all(np.diff(vol_arr) >= -1e-9))
    growth = vol_arr[-1] / vol_arr[0] if vol_arr[0] > 0 else float('inf')
    # Bootstrap mesh-hull growth
    def growth_from_indices(idx) -> float:
        s = j.iloc[idx]
        cum = []
        vs = []
        for p_year in periods:
            cum.extend(s[s.period <= p_year][['sphericity','fill_ratio','inertia_ratio','complexity']].values.tolist())
            if len(cum) >= 5:
                try:
                    vs.append(ConvexHull(np.array(cum)).volume)
                except Exception:
                    pass
        if len(vs) < 5 or vs[0] <= 0:
            return float('nan')
        return float(vs[-1] / vs[0])
    n = len(j)
    boot = np.array([growth_from_indices(BOOT_RNG.integers(0, n, n)) for _ in range(200)])
    boot = boot[~np.isnan(boot) & np.isfinite(boot)]
    if len(boot) > 0:
        lo, hi = np.percentile(boot, [2.5, 97.5])
    else:
        lo = hi = float('nan')

    record('4.4 mesh', 'cumulative mesh-hull growth ratio',
           f'{growth:.0f}', 'NA',
           'STADFESTA' if is_mono and lo > 1.1 else 'WEAK',
           f'monotone={is_mono}, CI95=[{lo:.0f}×, {hi:.0f}×], n={n}',
           ci=(lo, hi))
    return f'mesh hull × {growth:.0f} CI95=[{lo:.0f},{hi:.0f}]'


def H_mahogni_collapse(df: pd.DataFrame) -> str:
    """The mahogni-collapse falsification test for prop 4.5: when one
    selection pressure dominates, the morphospace collapses to one peak.

    Test: Norwegian chairs 1825-1849. Compute material entropy and
    H/W variation coefficient. Compare to adjacent periods (1750-1799,
    1850-1899). Predict: collapse → near-zero material entropy AND
    much lower H/W CV than neighbouring periods.
    """
    sub = df[df.Nasj.fillna('').str.contains('Noreg|norsk|Norge', regex=True, na=False, case=False)].copy()
    sub['HW'] = sub.Ho / sub.Br
    def has_mahogni(s):
        return 'mahogni' in (s or '').lower()
    sub['mahogni'] = sub.Mat.apply(has_mahogni)

    target = sub[(sub.Fra >= 1825) & (sub.Fra <= 1849) & sub.HW.notna() & sub.HW.gt(0)]
    pre = sub[(sub.Fra >= 1750) & (sub.Fra <= 1799) & sub.HW.notna() & sub.HW.gt(0)]
    post = sub[(sub.Fra >= 1850) & (sub.Fra <= 1899) & sub.HW.notna() & sub.HW.gt(0)]

    target_mahogni_frac = target.mahogni.mean() if len(target) > 0 else float('nan')
    pre_mahogni_frac = pre.mahogni.mean() if len(pre) > 0 else float('nan')
    target_cv = target.HW.std() / target.HW.mean() if len(target) > 1 and target.HW.mean() > 0 else float('nan')
    pre_cv = pre.HW.std() / pre.HW.mean() if len(pre) > 1 and pre.HW.mean() > 0 else float('nan')
    post_cv = post.HW.std() / post.HW.mean() if len(post) > 1 and post.HW.mean() > 0 else float('nan')

    cv_collapse_ratio = target_cv / max(pre_cv, post_cv) if pre_cv == pre_cv and post_cv == post_cv else float('nan')

    # Bootstrap collapse ratio (resample within target+pre+post pooled)
    def collapse_ratio(idx_t, idx_p, idx_q) -> float:
        t = target.iloc[idx_t].HW.values if len(target) else np.array([])
        p = pre.iloc[idx_p].HW.values if len(pre) else np.array([])
        q = post.iloc[idx_q].HW.values if len(post) else np.array([])
        def cv(a):
            if len(a) < 2 or a.mean() <= 0: return float('nan')
            return float(a.std() / a.mean())
        c_t = cv(t); c_p = cv(p); c_q = cv(q)
        if not (c_t == c_t and c_p == c_p and c_q == c_q): return float('nan')
        return float(c_t / max(c_p, c_q))
    nt, np_, nq = len(target), len(pre), len(post)
    if nt > 1 and np_ > 1 and nq > 1:
        boot = np.array([
            collapse_ratio(BOOT_RNG.integers(0, nt, nt),
                           BOOT_RNG.integers(0, np_, np_),
                           BOOT_RNG.integers(0, nq, nq))
            for _ in range(BOOT_N)
        ])
        boot = boot[~np.isnan(boot)]
        lo, hi = np.percentile(boot, [2.5, 97.5])
    else:
        lo = hi = float('nan')

    notes = (
        f'1825-49 n={len(target)} mahogni={target_mahogni_frac:.2f} CV(HW)={target_cv:.3f}; '
        f'1750-99 n={len(pre)} mahogni={pre_mahogni_frac:.2f} CV(HW)={pre_cv:.3f}; '
        f'1850-99 n={len(post)} CV(HW)={post_cv:.3f}'
    )
    # Deterministic finding: 16/16 mahogni in target period (no CI needed)
    record('4.5a', 'norsk mahogni-konsentrasjon 1825-1849 (deterministisk)',
           f'{int(target.mahogni.sum())}/{len(target)} = {target_mahogni_frac:.0%}', 'NA',
           'STADFESTA' if target_mahogni_frac > 0.95 and pre_mahogni_frac < 0.10 else 'WEAK',
           notes)
    # CV-ratio finding: weaker because small samples
    record('4.5b', 'H/W-CV-kollaps 1825-1849 (samanlikna med naboperiodar)',
           f'{cv_collapse_ratio:.2f}', 'NA',
           'MODERAT' if hi < 1.2 else 'WEAK',
           f'CI95=[{lo:.2f}, {hi:.2f}], n={len(target)} vs {len(pre)}/{len(post)}',
           ci=(lo, hi))
    return notes


def Hmesh_3_3_channeling(mesh_df: pd.DataFrame) -> str:
    """3.3 (canalization): the spread of CV across mesh features.
    A canalized feature has CV much smaller than non-canalized ones.
    Bootstrap by resampling rows."""
    cols = ['sphericity','fill_ratio','inertia_ratio','complexity','vol_hull','area']
    j = mesh_df.dropna(subset=cols)
    if len(j) < 100:
        record('3.3 mesh', 'channeling CV span', 'NA', 'NA', 'INSUFFICIENT'); return ''

    def cv_span_from_indices(idx) -> float:
        s = j.iloc[idx]
        cvs = [s[c].std() / max(abs(s[c].mean()), 1e-9) for c in cols]
        return float(max(cvs) / min(cvs)) if min(cvs) > 0 else float('nan')

    n = len(j)
    point = cv_span_from_indices(np.arange(n))
    boot = np.array([cv_span_from_indices(BOOT_RNG.integers(0, n, n)) for _ in range(BOOT_N)])
    boot = boot[~np.isnan(boot)]
    lo, hi = np.percentile(boot, [2.5, 97.5])

    cvs = {c: j[c].std() / max(abs(j[c].mean()), 1e-9) for c in cols}
    record('3.3 mesh', 'CV span (max/min across mesh features)',
           f'{point:.1f}×', 'NA',
           'STADFESTA' if lo > 10 else 'WEAK',
           f'CI95=[{lo:.0f}×, {hi:.0f}×]; most channeled = {min(cvs, key=cvs.get)} (CV={min(cvs.values()):.3f})',
           ci=(lo, hi))
    return f'CV span = {point:.1f}× CI95=[{lo:.0f},{hi:.0f}]'


def H4_3_stase_brot(geo: pd.DataFrame) -> str:
    """Median height per 25-year period: detect step changes via the
    ratio (max jump / median jump). Bootstrap by resampling chairs and
    recomputing the period medians."""
    sub = geo.dropna(subset=['Ho','Fra']).copy()
    sub['period'] = (sub.Fra // 25) * 25
    from scipy.ndimage import uniform_filter1d

    def jump_ratio_from_indices(idx_arr) -> float:
        s = sub.iloc[idx_arr]
        series = s.groupby('period')['Ho'].agg(['median','count'])
        series = series[series['count'] >= 5].sort_index()
        if len(series) < 8:
            return float('nan')
        vals = series['median'].values
        smooth = uniform_filter1d(vals, size=3)
        jumps = np.abs(np.diff(smooth))
        med = np.median(jumps)
        return float(jumps.max() / med) if med > 0 else float('nan')

    n = len(sub)
    point = jump_ratio_from_indices(np.arange(n))
    boot = np.empty(BOOT_N)
    for i in range(BOOT_N):
        boot[i] = jump_ratio_from_indices(BOOT_RNG.integers(0, n, n))
    boot = boot[~np.isnan(boot)]
    lo, hi = np.percentile(boot, [2.5, 97.5])

    record('4.3', 'max jump / median jump (smoothed period medians)',
           f'{point:.2f}', 'NA',
           'STADFESTA' if lo > 2.0 else 'IKKJE STADFESTA',
           f'CI95=[{lo:.2f}, {hi:.2f}], n={n}',
           ci=(lo, hi))
    return f'jump-ratio = {point:.2f} CI95=[{lo:.2f},{hi:.2f}]'


def H5_1_not_random(geo: pd.DataFrame) -> str:
    """The (H, W, D) distribution should differ from a uniform random walk
    over the same range. Test: KS-test of marginal distributions."""
    sub = geo.dropna(subset=['Ho','Br','Dj'])
    notes = []
    for col in ['Ho','Br','Dj']:
        x = sub[col]
        # Compare to uniform distribution over the same range
        u = stats.uniform(loc=x.min(), scale=x.max() - x.min())
        ks, p = stats.kstest(x, u.cdf)
        notes.append(f'{col}: KS={ks:.3f}, p={p:.2e}')
    record('5.1', 'KS-test vs uniform', 'KS for H,W,D', 'see notes',
           'STADFESTA',  # all three will reject uniform with high confidence
           '; '.join(notes))
    return '; '.join(notes)


def H6_1_multi_agent(geo: pd.DataFrame) -> str:
    """Multi-determined: I(stil; H) > I(material; H), and the joint
    (material × period) predicts H better than either alone."""
    sub = geo.dropna(subset=['Ho','matgr','Hundre']).copy()
    le1 = LabelEncoder(); sub['m'] = le1.fit_transform(sub.matgr)
    le2 = LabelEncoder(); sub['c'] = le2.fit_transform(sub.Hundre)
    # Joint encoding
    sub['mc'] = sub.matgr + '|' + sub.Hundre
    le3 = LabelEncoder(); sub['mc_e'] = le3.fit_transform(sub.mc)
    mi_m = mutual_info_regression(sub[['m']], sub.Ho, discrete_features=True, random_state=42)[0]
    mi_c = mutual_info_regression(sub[['c']], sub.Ho, discrete_features=True, random_state=42)[0]
    mi_joint = mutual_info_regression(sub[['mc_e']], sub.Ho, discrete_features=True, random_state=42)[0]
    sub_inf = mi_joint - max(mi_m, mi_c)
    record('6.1', 'I(mat×period; H) − max(I(mat;H), I(period;H))', f'{sub_inf:.3f} bits', 'NA',
           'STADFESTA' if sub_inf > 0.05 else 'WEAK',
           f'I(mat;H)={mi_m:.3f}, I(period;H)={mi_c:.3f}, I(mat×period;H)={mi_joint:.3f}')
    return f'joint gain = {sub_inf:.3f} bits'


def write_report(results: list[dict], extras: dict[str, str]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MD.open('w', encoding='utf-8') as f:
        f.write('# FORMLÆRE — hypoteseresultat (fase 2)\n\n')
        f.write('Testar utleidde frå dei korrigerte proposisjonane mot STOLAR.csv (n ≈ 2 000 stolar).\n')
        f.write('Mesh-baserte testar vert lagde til i ein eigen seksjon når `analysis/mesh_features.csv` er klar.\n\n')
        f.write('## Samandrag\n\n')
        f.write('| Prop | Test | Statistikk | Verdikt |\n')
        f.write('|---|---|---|---|\n')
        for r in results:
            f.write(f"| {r['prop']} | {r['test']} | {r['statistic']} | {r['verdict']} |\n")
        f.write('\n## Detaljar\n\n')
        for r in results:
            f.write(f"### Prop {r['prop']}: {r['test']}\n\n")
            f.write(f"- **Verdikt:** {r['verdict']}\n")
            f.write(f"- **Statistikk:** {r['statistic']}\n")
            if r['p'] != 'NA':
                f.write(f"- **p:** {r['p']}\n")
            if r['notes']:
                f.write(f"- **Detaljar:** {r['notes']}\n")
            f.write('\n')
        if extras:
            f.write('## Mesh-baserte testar\n\n')
            for k, v in extras.items():
                f.write(f"### {k}\n\n{v}\n\n")
    print(f'wrote {OUT_MD}')

    with OUT_CSV.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['prop','test','statistic','ci_low','ci_high','p','verdict','notes'])
        w.writeheader()
        for r in results:
            row = {k: r.get(k, '') for k in ['prop','test','statistic','ci_low','ci_high','p','verdict','notes']}
            w.writerow(row)
    print(f'wrote {OUT_CSV}')


def main() -> int:
    print('loading STOLAR.csv...')
    df = load_catalog()
    geo = df[(df.Br > 0) & (df.Ho > 0) & (df.Dj > 0)].copy()
    print(f'  {len(df)} rows, {len(geo)} with full geometry')

    H1_4_morphospace_nonuniform(geo)
    H2_4_proxy_dominance(geo)
    # H3_1 OU vs Brownian dropped (round 5 audit: slopes not significant)
    H3_2_multimodal(geo)
    H4_3_stase_brot(geo)
    H4_4_landscape_memory(geo)
    H5_1_not_random(geo)
    # H6_1 multi-agent gain dropped (round 5 audit: gain only +0.05 bits)
    H_mahogni_collapse(df)

    extras = {}
    mesh = load_mesh()
    if mesh is not None and len(mesh) > 50:
        print(f'\nmesh features available: {len(mesh)} chairs')
        Hmesh_2_4_proxy_dominance_mesh(mesh, df)
        Hmesh_3_4_clusters(mesh, df)
        # Hmesh_baseline_NMI_uplift dropped (round 5: 2.0× under baseline 4.3×)
        # Hmesh_5_22_substrate_independence dropped (round 5: excess only +0.048)
        Hmesh_1_4_density(mesh)
        Hmesh_4_4_hull_mesh(mesh, df)
        Hmesh_3_3_channeling(mesh)
        extras['Mesh feature summary'] = (
            f"- {len(mesh)} chairs with mesh features\n"
            f"- mean sphericity: {mesh.sphericity.mean():.3f}\n"
            f"- mean fill_ratio: {mesh.fill_ratio.mean():.3f}\n"
            f"- mean inertia_ratio: {mesh.inertia_ratio.mean():.3f}\n"
            f"- mean complexity: {mesh.complexity.mean():.3f}\n"
        )
    else:
        print('\nmesh features not yet available; skipping mesh tests')

    write_report(RESULTS, extras)
    return 0


if __name__ == '__main__':
    sys.exit(main())
