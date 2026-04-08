"""A.6.10 — Vert stolen flatare? H/B-proporsjonen 1500–2024
(Tilleggstest til Proposisjon 4.1)

Test: does the height-to-width aspect ratio of chairs change systematically
over time? If the dynamic-landscape postulate holds, the centroid of
this ratio should drift; if selection pressures over proportion were
constant, the rolling median would be flat.

We compute H/W per chair, then the rolling 50-year median + IQR over the
full corpus, and the per-century KDE distribution.

Visual: a two-panel figure.
  Left  — scatter (faint dots) + rolling median line + IQR band, with a
          horizontal reference at the modal H/W and at H/W = 1 (square).
  Right — five horizontal KDE strips, one per century from 1600 to 2000,
          ordered top-down by century, sharing the same x-axis as the
          left panel's y-axis.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL, HIGHLIGHT,
)

START = 1500
END   = 2024
WIN   = 50    # rolling median half-window in years


def run_test():
    df = load_chairs()
    df = df.dropna(subset=['h_cm', 'w_cm', 'year_mid']).copy()
    df = df[(df['h_cm'] > 0) & (df['w_cm'] > 0)]
    df['hw'] = df['h_cm'] / df['w_cm']
    df = df[(df['year_mid'] >= START) & (df['year_mid'] <= END)]
    # Drop H/W outliers (1-99 percentile)
    lo, hi = np.percentile(df['hw'], [1, 99])
    df = df[(df['hw'] >= lo) & (df['hw'] <= hi)]

    # Rolling median + IQR over a 50-year window
    df = df.sort_values('year_mid').reset_index(drop=True)
    years_sorted = df['year_mid'].values
    hw_sorted = df['hw'].values
    grid = np.arange(START, END + 1, 5)
    med, q25, q75 = [], [], []
    for y in grid:
        m = (years_sorted >= y - WIN / 2) & (years_sorted <= y + WIN / 2)
        if m.sum() >= 8:
            v = hw_sorted[m]
            med.append(np.median(v))
            q25.append(np.percentile(v, 25))
            q75.append(np.percentile(v, 75))
        else:
            med.append(np.nan)
            q25.append(np.nan)
            q75.append(np.nan)

    # Per-century KDEs (1600, 1700, 1800, 1900, 2000)
    century_kdes = []
    for c in (1600, 1700, 1800, 1900, 2000):
        sub = df[(df['year_mid'] >= c - 50) & (df['year_mid'] < c + 50)]
        if len(sub) < 8:
            century_kdes.append((c, None, None, len(sub)))
            continue
        kde = gaussian_kde(sub['hw'].values)
        century_kdes.append((c, kde, sub['hw'].values, len(sub)))

    return df, grid, np.array(med), np.array(q25), np.array(q75), century_kdes


def plot(df, grid, med, q25, q75, century_kdes):
    apply_style()

    # Single-panel version: just the XY scatter + rolling median + IQR
    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.66))
    ax = fig.add_axes([0.16, 0.15000000000000002, 0.8, 0.77])

    # Scatter (faint dots) + rolling median + IQR
    ax.scatter(df['year_mid'], df['hw'], s=2.0, color=INK_SOFT,
               alpha=0.20, linewidths=0, zorder=2)
    ax.fill_between(grid, q25, q75, color=ACCENT_RUST,
                    alpha=0.18, linewidth=0, zorder=3,
                    label='Interkvartilbreidde')
    ax.plot(grid, med, color=ACCENT_RUST, linewidth=1.6,
            zorder=4, label='Rullande median')

    # Reference lines: H/W = 1 (square) + modal H/W
    ax.axhline(1.0, color=INK_SOFT, linewidth=0.5,
               linestyle=(0, (3, 2)), alpha=0.6, zorder=2)
    modal = float(np.nanmedian(df['hw']))
    ax.axhline(modal, color=ACCENT_TEAL, linewidth=0.6,
               linestyle=(0, (3, 2)), alpha=0.65, zorder=2)
    ax.text(START + 8, modal + 0.04, f'median {modal:.2f}',
            fontsize=6.3, color=ACCENT_TEAL)
    ax.text(START + 8, 1.0 - 0.10, 'kvadratisk stol  (H = W)',
            fontsize=6.3, color=INK_SOFT)

    ax.set_xlim(START, END)
    ax.set_ylim(0.4, 3.0)
    ax.set_xlabel('År', fontsize=8.0)
    ax.set_ylabel('Høgde / Breidde', fontsize=8.0)
    ax.tick_params(axis='both', labelsize=7.5)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)

    leg = ax.legend(loc='upper right', fontsize=7,
                    handletextpad=0.4, labelspacing=0.25)
    for t in leg.get_texts():
        t.set_color(INK_SOFT)



    out = FIG_DIR / 'fig-A.6.10-proporsjon.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df, grid, med, q25, q75, ck = run_test()
    print(f'n = {len(df)}, median H/W = {np.nanmedian(df["hw"]):.3f}')
    for c, kde, vals, n in ck:
        if vals is not None:
            print(f'  {c}: n={n}, median {np.median(vals):.3f}')
    out = plot(df, grid, med, q25, q75, ck)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
