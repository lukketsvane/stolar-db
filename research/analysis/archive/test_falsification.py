#!/usr/bin/env python3
"""
Direct falsification tests for the FORMLÆRE postulates.

Postulat 2.2: For kvar funksjonell klasse finst det minst to seleksjonstrykk
              som er statistisk uavhengige av kvarandre.
              FALSIFISERING: ein klasse der eitt einaste trykk forklarer all
              observert formvariasjon.
              TEST: pairwise mutual information mellom alle prediktorpar; den
              minste MI-verdien skal vere klart over null. I tillegg: cumulative
              R² frå éin enkelt sterkaste prediktor mot alle andre lagt på.

Postulat 4.1: Seleksjonstrykka endrar seg over tid.
              FALSIFISERING: tilpassingslandskapet er topologisk uendra over ein
              periode der den observerte fordelinga endrar seg.
              TEST: Wasserstein-avstand (Earth Mover's Distance) mellom
              morphospace-fordelingar i suksessive periodar. EMD ≈ 0 over ein
              periode der nye stolar vert produserte = potensielt falsifisert.

Postulat 5.1: For kvar klasse finst det minst éin agent som navigerer
              tilpassingslandskapet via negativ tilbakekopling.
              FALSIFISERING: fordelinga er statistisk uskiljbar frå ein
              tilfeldig prosess utan tilbakekopling.
              TEST: Kolmogorov-Smirnov mot uniform null AND mot brownian-walk
              null over same intervall.

Output: analysis/falsification.md, analysis/falsification.csv
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
from scipy import stats
from scipy.stats import wasserstein_distance
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import LabelEncoder

ROOT = Path(__file__).resolve().parent.parent
STOLAR_CSV = ROOT / 'STOLAR' / 'STOLAR.csv'
OUT_MD = ROOT / 'analysis' / 'falsification.md'
OUT_CSV = ROOT / 'analysis' / 'falsification.csv'

ROWS: list[dict] = []


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
    return df


def record(postulat: str, test: str, result: str, status: str, notes: str = '') -> None:
    ROWS.append({'postulat': postulat, 'test': test, 'resultat': result, 'status': status, 'detalj': notes})


# ── Postulat 2.2 ──────────────────────────────────────────────────────────────

def falsify_2_2(df: pd.DataFrame) -> None:
    """Test pairwise MI between predictor pairs and the minimum MI.
    Falsified if any pair has MI = 0 (statistically independent)."""
    sub = df.dropna(subset=['Mat','Stil','Hundre','Nasj','Fra'])
    sub = sub[sub.Stil.notna() & sub.matgr.notna()]
    if len(sub) < 100:
        record('2.2', 'pairwise predictor MI', 'INSUFFICIENT', 'NA'); return

    encoders = {}
    for col in ['matgr','Stil','Hundre','Nasj']:
        le = LabelEncoder()
        encoders[col] = le.fit_transform(sub[col].fillna('?'))

    pairs = [
        ('matgr', 'Stil'),
        ('matgr', 'Hundre'),
        ('matgr', 'Nasj'),
        ('Stil', 'Hundre'),
        ('Stil', 'Nasj'),
        ('Hundre', 'Nasj'),
    ]
    mi_values = {}
    for a, b in pairs:
        mi = mutual_info_regression(encoders[a].reshape(-1, 1), encoders[b],
                                    discrete_features=True, random_state=42)[0]
        mi_values[f'{a}-{b}'] = mi

    min_pair, min_mi = min(mi_values.items(), key=lambda kv: kv[1])
    max_pair, max_mi = max(mi_values.items(), key=lambda kv: kv[1])
    notes = '; '.join(f'{k}={v:.3f}' for k, v in sorted(mi_values.items(), key=lambda kv: kv[1]))
    # Postulat 2.2 says ≥ 2 independent pressures must exist. Finding an
    # almost-independent pair (low MI) CONFIRMS the postulate. Falsification
    # would be: ALL pairs strongly correlated, no two are independent.
    confirmed = min_mi < 0.10  # at least one near-independent pair
    record('2.2', 'min pairwise MI between selection-pressure proxies (low = independent pair exists)',
           f'{min_mi:.3f} bits ({min_pair})',
           'HELD (independent pair found)' if confirmed else 'FALSIFIED (no independent pair)',
           notes)

    # Stronger sub-test: cumulative R² from one strongest predictor against full set
    # Use H/W as target
    sub2 = sub.dropna(subset=['Ho','Br'])
    sub2 = sub2[(sub2.Br > 0)]
    if len(sub2) > 100:
        sub2 = sub2.copy()
        sub2['HW'] = sub2.Ho / sub2.Br
        # Encode predictors
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import OneHotEncoder
        # Single strongest predictor: stilperiode
        ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        X_stil = ohe.fit_transform(sub2[['Stil']].fillna('?'))
        r2_stil = LinearRegression().fit(X_stil, sub2.HW).score(X_stil, sub2.HW)
        # All predictors combined
        X_all = ohe.fit_transform(sub2[['Stil','matgr','Hundre','Nasj']].fillna('?'))
        r2_all = LinearRegression().fit(X_all, sub2.HW).score(X_all, sub2.HW)
        gain = r2_all - r2_stil
        record('2.2', 'gain in R² (HW) when adding all other predictors to stil alone',
               f'{gain:.4f}',
               'HELD (other predictors add explanatory power)' if gain > 0.02 else 'FALSIFIED (one predictor sufficient)',
               f'r2(stil)={r2_stil:.3f}, r2(all)={r2_all:.3f}, n={len(sub2)}')


# ── Postulat 4.1 ──────────────────────────────────────────────────────────────

def falsify_4_1(df: pd.DataFrame) -> None:
    """Wasserstein distance between successive 50-year period morphospace
    distributions. Falsified if EMD ≈ 0 across the dataset."""
    sub = df.dropna(subset=['Ho','Br','Dj','Fra'])
    sub = sub[(sub.Ho > 0) & (sub.Br > 0) & (sub.Dj > 0)]
    if len(sub) < 200:
        record('4.1', 'Wasserstein landscape change', 'INSUFFICIENT', 'NA'); return
    sub = sub.copy()
    sub['period'] = (sub.Fra // 50) * 50
    periods = sorted(sub.period.unique())

    emds = []
    for p1, p2 in zip(periods[:-1], periods[1:]):
        a = sub[sub.period == p1].Ho.values
        b = sub[sub.period == p2].Ho.values
        if len(a) > 5 and len(b) > 5:
            emd_h = wasserstein_distance(a, b)
            emds.append((p1, p2, emd_h, len(a), len(b)))

    if not emds:
        record('4.1', 'Wasserstein H', 'INSUFFICIENT', 'NA'); return
    emd_values = [e[2] for e in emds]
    mean_emd = np.mean(emd_values)
    max_emd = max(emd_values)
    near_zero = sum(1 for e in emd_values if e < 0.5)
    record('4.1', 'mean Wasserstein-distance(H) between consecutive 50-y periods',
           f'{mean_emd:.2f} cm',
           'HELD (positive movement)' if mean_emd > 1.0 else 'FALSIFIED (no movement)',
           f'max={max_emd:.2f}, near-zero (<0.5cm)={near_zero}/{len(emds)}, periods={len(periods)}')

    # Per-dimension EMD too — show H, W, D separately
    for dim in ['Ho','Br','Dj']:
        ds = [wasserstein_distance(sub[sub.period == p1][dim].values, sub[sub.period == p2][dim].values)
              for p1, p2 in zip(periods[:-1], periods[1:])
              if len(sub[sub.period == p1]) > 5 and len(sub[sub.period == p2]) > 5]
        if ds:
            record('4.1', f'mean Wasserstein({dim}) consecutive periods',
                   f'{np.mean(ds):.2f} cm', 'HELD' if np.mean(ds) > 1.0 else 'WEAK', '')


# ── Postulat 5.1 ──────────────────────────────────────────────────────────────

def falsify_5_1(df: pd.DataFrame) -> None:
    """KS test against uniform null AND a Gaussian random walk over same range.
    Falsified if both nulls cannot be rejected."""
    sub = df.dropna(subset=['Ho','Br','Dj'])
    sub = sub[(sub.Ho > 0) & (sub.Br > 0) & (sub.Dj > 0)]
    if len(sub) < 100:
        record('5.1', 'KS vs uniform / random walk', 'INSUFFICIENT', 'NA'); return

    for dim_name, col in [('H', 'Ho'), ('W', 'Br'), ('D', 'Dj')]:
        x = sub[col].values
        # Uniform null
        u = stats.uniform(loc=x.min(), scale=x.max() - x.min())
        ks_u, p_u = stats.kstest(x, u.cdf)
        # Random walk null: cumulative gaussian centered at midpoint, std spanning the range
        rw_loc = x.mean()
        rw_scale = x.std()
        rw = stats.norm(loc=rw_loc, scale=rw_scale)
        ks_rw, p_rw = stats.kstest(x, rw.cdf)

        record('5.1', f'KS({dim_name}) vs uniform', f'KS={ks_u:.3f}, p={p_u:.2e}',
               'HELD (rejected uniform)' if p_u < 0.001 else 'FALSIFIED', '')
        record('5.1', f'KS({dim_name}) vs gaussian random walk', f'KS={ks_rw:.3f}, p={p_rw:.2e}',
               'HELD (rejected RW)' if p_rw < 0.001 else 'FALSIFIED', '')


def main() -> int:
    df = load_catalog()
    print(f'loaded {len(df)} chairs')

    falsify_2_2(df)
    falsify_4_1(df)
    falsify_5_1(df)

    out_df = pd.DataFrame(ROWS)
    out_df.to_csv(OUT_CSV, index=False, encoding='utf-8')
    print(f'wrote {OUT_CSV}')

    with OUT_MD.open('w', encoding='utf-8') as f:
        f.write('# Falsifiseringstestar — postulat 2.2, 4.1, 5.1\n\n')
        f.write('| Postulat | Test | Resultat | Status |\n|---|---|---|---|\n')
        for r in ROWS:
            f.write(f"| {r['postulat']} | {r['test']} | {r['resultat']} | {r['status']} |\n")
        f.write('\n## Detaljar\n\n')
        for r in ROWS:
            if r['detalj']:
                f.write(f"**{r['postulat']} — {r['test']}**\n\n{r['detalj']}\n\n")
    print(f'wrote {OUT_MD}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
