#!/usr/bin/env python3
"""
C3 + C4: museum cross-validation and hold-out stability for FORMLÆRE.

For each retained hypothesis, re-runs the test on:
  - V&A subset only (Object-ID prefix O / OK)
  - Nasjonalmuseet subset only (NMK / NAMF)
  - Leave-one-period-out runs (drop one century at a time)
  - Leave-one-style-out runs (drop the largest single style at a time)

Output: analysis/cross_validation.md, analysis/cross_validation.csv

A finding that holds in both museums and across all hold-outs is robust;
one that depends on a single subset is flagged.
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
from scipy.spatial import cKDTree, ConvexHull
from sklearn.feature_selection import mutual_info_regression
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler, LabelEncoder

ROOT = Path(__file__).resolve().parent.parent
STOLAR_CSV = ROOT / 'STOLAR' / 'STOLAR.csv'
MESH_CSV = ROOT / 'analysis' / 'mesh_features.csv'
OUT_MD = ROOT / 'analysis' / 'cross_validation.md'
OUT_CSV = ROOT / 'analysis' / 'cross_validation.csv'


def load_catalog() -> pd.DataFrame:
    df = pd.read_csv(STOLAR_CSV, encoding='utf-8')
    rename = {df.columns[i]: c for i, c in enumerate([
        'Namn','Bilete','Fra','Mat','MatK','Nasjmus','ID','PStad','Prod','Til',
        'GLB','Vekt','Nasj','URL','Emneord','Erverving','SH','Stil','Tekn',
        'Br','Dat','Dj','Ho','Nemn','Hundre',
    ])}
    df = df.rename(columns=rename)
    for c in ['Fra','Br','Ho','Dj']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    def matgrp(s):
        s = (s or '').lower()
        if 'plast' in s: return 'plast'
        if 'st\xe5l' in s or 'metall' in s or 'jern' in s: return 'metall'
        if any(x in s for x in ['tre','eik','furu','mahogni','teak','bj\xf8rk','b\xf8k']): return 'tre'
        return 'anna'
    df['matgr'] = df.Mat.apply(matgrp)
    # Museum tag
    pid = df.ID.astype(str).str.extract(r'^([A-Z]+)', expand=False)
    df['museum'] = pid.map(lambda p: 'NMK' if p in ('NMK', 'NAMF') else ('VAM' if p in ('O', 'OK') else 'other'))
    return df


def cv_nn(arr2d: np.ndarray) -> float:
    if len(arr2d) < 50: return float('nan')
    Xn = StandardScaler().fit_transform(arr2d)
    tree = cKDTree(Xn)
    d, _ = tree.query(Xn, k=2)
    nn = d[:, 1]
    nn = nn[nn > 0]
    if len(nn) < 10: return float('nan')
    return float(nn.std() / nn.mean())


def proxy_dominance(geo: pd.DataFrame) -> tuple[int, str]:
    """Returns (wins, notes) — how many of 4 catalog dims have stil > mat in MI."""
    sub = geo.dropna(subset=['Ho','Br','Dj','Stil','matgr'])
    if len(sub) < 50: return (0, 'insufficient')
    sub = sub.copy()
    sub['HW'] = sub.Ho / sub.Br
    le_s = LabelEncoder(); sub['s'] = le_s.fit_transform(sub.Stil.fillna('?'))
    le_m = LabelEncoder(); sub['m'] = le_m.fit_transform(sub.matgr.fillna('?'))
    wins = 0
    parts = []
    for tgt in ['Ho','Br','Dj','HW']:
        d = sub[['s','m', tgt]].dropna()
        if len(d) < 30:
            parts.append(f'{tgt}: skip')
            continue
        mi_s = mutual_info_regression(d[['s']], d[tgt], discrete_features=True, random_state=42)[0]
        mi_m = mutual_info_regression(d[['m']], d[tgt], discrete_features=True, random_state=42)[0]
        if mi_s > mi_m: wins += 1
        parts.append(f'{tgt}: stil={mi_s:.2f}/mat={mi_m:.2f}')
    return wins, '; '.join(parts)


def cv_span(mesh: pd.DataFrame) -> float:
    cols = ['sphericity','fill_ratio','inertia_ratio','complexity','vol_hull','area']
    sub = mesh.dropna(subset=cols)
    if len(sub) < 50: return float('nan')
    cvs = [sub[c].std() / max(abs(sub[c].mean()), 1e-9) for c in cols]
    return float(max(cvs) / min(cvs)) if min(cvs) > 0 else float('nan')


def silhouette_of(mesh: pd.DataFrame, cat: pd.DataFrame) -> tuple[float, int, int]:
    j = mesh.merge(cat[['ID','Stil']], left_on='objekt_id', right_on='ID', how='inner')
    j = j.dropna(subset=['sphericity','fill_ratio','inertia_ratio','complexity','Stil'])
    big = j.Stil.value_counts()
    big = big[big >= 10].index
    j = j[j.Stil.isin(big)]
    if len(j) < 50 or j.Stil.nunique() < 3:
        return float('nan'), len(j), j.Stil.nunique()
    X = j[['sphericity','fill_ratio','inertia_ratio','complexity']].values
    Xn = StandardScaler().fit_transform(X)
    return float(silhouette_score(Xn, j.Stil.values)), len(j), j.Stil.nunique()


def hull_growth(geo: pd.DataFrame) -> float:
    sub = geo.dropna(subset=['Ho','Br','Dj','Fra']).copy()
    for c in ['Ho','Br','Dj']:
        lo, hi = sub[c].quantile([0.01, 0.99])
        sub = sub[(sub[c] >= lo) & (sub[c] <= hi)]
    if len(sub) < 50: return float('nan')
    sub['period'] = (sub.Fra // 25) * 25
    cum = []
    vols = []
    for p in sorted(sub.period.unique()):
        cum.extend(sub[sub.period <= p][['Ho','Br','Dj']].values.tolist())
        if len(cum) >= 4:
            try: vols.append(ConvexHull(np.array(cum)).volume)
            except Exception: pass
    if len(vols) < 5 or vols[0] <= 0: return float('nan')
    return float(vols[-1] / vols[0])


# ── Cross-validation runner ───────────────────────────────────────────────────

ROWS = []

def run_subset(label: str, geo: pd.DataFrame, mesh_sub: pd.DataFrame | None, cat: pd.DataFrame) -> None:
    """Run all kept hypotheses on a subset and append rows."""
    n = len(geo)
    # 1.4 catalog
    cv = cv_nn(geo[['Ho','Br','Dj']].dropna().values)
    ROWS.append({'subset': label, 'n_catalog': n, 'test': '1.4 CV(nn) catalog', 'value': f'{cv:.2f}', 'pass': 'YES' if cv > 0.4 else 'NO'})
    # 2.4 proxy dominance
    wins, _ = proxy_dominance(geo)
    ROWS.append({'subset': label, 'n_catalog': n, 'test': '2.4 stil>mat (catalog)', 'value': f'{wins}/4', 'pass': 'YES' if wins >= 3 else 'NO'})
    # 4.4 hull growth
    hg = hull_growth(geo)
    ROWS.append({'subset': label, 'n_catalog': n, 'test': '4.4 hull growth ratio', 'value': f'{hg:.0f}×' if hg == hg else 'NA', 'pass': 'YES' if (hg == hg and hg > 1.1) else 'NO'})

    if mesh_sub is None or len(mesh_sub) < 50:
        return

    # 1.4 mesh
    cv_m = cv_nn(mesh_sub[['sphericity','fill_ratio','inertia_ratio','complexity']].dropna().values)
    ROWS.append({'subset': label, 'n_catalog': n, 'test': '1.4 CV(nn) mesh', 'value': f'{cv_m:.2f}', 'pass': 'YES' if cv_m > 0.4 else 'NO'})
    # 3.3 mesh CV span
    span = cv_span(mesh_sub)
    ROWS.append({'subset': label, 'n_catalog': n, 'test': '3.3 mesh CV span', 'value': f'{span:.0f}×' if span == span else 'NA', 'pass': 'YES' if (span == span and span > 10) else 'NO'})
    # 3.4 mesh silhouette
    sil, n_j, n_st = silhouette_of(mesh_sub, cat)
    ROWS.append({'subset': label, 'n_catalog': n, 'test': '3.4 mesh silhouette', 'value': f'{sil:.2f}', 'pass': 'YES' if sil < 0 else 'NO'})


def main() -> int:
    print('loading...')
    cat = load_catalog()
    geo_full = cat[(cat.Br > 0) & (cat.Ho > 0) & (cat.Dj > 0)]
    mesh = pd.read_csv(MESH_CSV)

    print('\n=== Per-museum ===')
    for label, mask in [
        ('FULL', cat.museum.notna()),
        ('VAM only', cat.museum == 'VAM'),
        ('NMK only', cat.museum == 'NMK'),
    ]:
        c = cat[mask]
        g = geo_full[geo_full.ID.isin(c.ID)]
        m_sub = mesh[mesh.objekt_id.isin(c.ID)]
        print(f'{label}: n_catalog={len(g)}, n_mesh={len(m_sub)}')
        run_subset(label, g, m_sub, cat)

    print('\n=== Hold-one-century-out ===')
    centuries = sorted(cat.Hundre.dropna().unique())
    for cy in centuries:
        c = cat[cat.Hundre != cy]
        g = geo_full[geo_full.ID.isin(c.ID)]
        m_sub = mesh[mesh.objekt_id.isin(c.ID)]
        if len(g) < 100: continue
        label = f'drop {cy}'
        run_subset(label, g, m_sub, cat)

    print('\n=== Hold-largest-style-out ===')
    largest_style = cat.Stil.value_counts().index[0]
    c = cat[cat.Stil != largest_style]
    g = geo_full[geo_full.ID.isin(c.ID)]
    m_sub = mesh[mesh.objekt_id.isin(c.ID)]
    label = f'drop {largest_style}'
    run_subset(label, g, m_sub, cat)

    df = pd.DataFrame(ROWS)
    df.to_csv(OUT_CSV, index=False, encoding='utf-8')
    print(f'\nwrote {OUT_CSV}')

    # Build markdown report
    with OUT_MD.open('w', encoding='utf-8') as f:
        f.write('# C3 + C4 — kryss-validering og hold-out-stabilitet\n\n')
        f.write('| Subset | Test | Verdi | Held |\n|---|---|---|---|\n')
        for r in ROWS:
            f.write(f"| {r['subset']} | {r['test']} | {r['value']} | {r['pass']} |\n")
    print(f'wrote {OUT_MD}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
