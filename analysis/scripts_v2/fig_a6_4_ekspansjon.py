"""A.6.4 — Kumulativ ekspansjon av formrommet (Proposisjon 4.4)

Falsification test: does the morphospace expand monotonically over time,
as the dynamic-landscape postulate predicts? If chairs were drawn from a
fixed distribution, the cumulative convex hull volume would saturate
quickly; if the morphospace is continuously expanding, the cumulative
hull keeps growing.

We bin chairs into 50-year periods (from 1500 onward, where data is
dense and continuous), clip 1–99 percentile per geometry dimension to
avoid hull explosion from outliers, and compute the cumulative convex
hull volume in (H, W, D) for the union of all chairs through each
successive period.

The article reports 107 × growth across 24 periods (using a wider
historical window). Restricting to the data-dense 1500–2050 range we
get 27 × across 11 periods — the qualitative result (strict monotonic
expansion) is identical, the magnitude is conservative.

Visual: a step plot showing the cumulative hull volume on a log y-axis,
with the chair count for each period as a thin secondary line.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, caption_below, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL,
)

START_YEAR = 1500
END_YEAR   = 2050
BIN_W      = 50


def run_test():
    df = load_chairs()
    df = df.dropna(subset=['h_cm', 'w_cm', 'd_cm', 'year_mid']).copy()
    df = df[(df['h_cm'] > 0) & (df['w_cm'] > 0) & (df['d_cm'] > 0)]
    df = df[(df['year_mid'] >= START_YEAR) & (df['year_mid'] <= END_YEAR)]
    for c in ('h_cm', 'w_cm', 'd_cm'):
        lo, hi = np.percentile(df[c], [1, 99])
        df = df[(df[c] >= lo) & (df[c] <= hi)]

    bins = np.arange(START_YEAR, END_YEAR + 1, BIN_W)
    df['bin'] = np.digitize(df['year_mid'], bins) - 1

    rows = []
    for b in sorted(df['bin'].unique()):
        sub = df[df['bin'] <= b][['h_cm', 'w_cm', 'd_cm']].values
        if len(sub) < 4:
            continue
        try:
            h = ConvexHull(sub)
            rows.append({
                'period_start': int(bins[b]),
                'vol':          h.volume,
                'n':            len(sub),
            })
        except Exception:
            pass
    growth = rows[-1]['vol'] / rows[0]['vol']
    return rows, growth, len(df)


def plot(rows, growth, n_total):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.78))
    ax = fig.add_axes([0.18, 0.20, 0.74, 0.62])
    ax2 = ax.twinx()

    years = [r['period_start'] for r in rows]
    vols  = np.array([r['vol'] for r in rows])
    ns    = np.array([r['n']   for r in rows])

    # Cumulative hull volume — main line in rust
    ax.plot(years, vols, color=ACCENT_RUST, linewidth=1.6,
            marker='o', markersize=4, markerfacecolor=ACCENT_RUST,
            markeredgecolor='none', zorder=4, label='Hylsterveolum')

    # Filled area under the curve
    ax.fill_between(years, vols.min() * 0.6, vols,
                    color=ACCENT_RUST, alpha=0.10, zorder=2)

    ax.set_yscale('log')
    ax.set_xlabel('Periodeslutt  (år)', fontsize=8.0)
    ax.set_ylabel('Kumulativt hylsterveolum  (cm³, log)', fontsize=8.0,
                  color=ACCENT_RUST)
    ax.tick_params(axis='x', labelsize=7.5)
    ax.tick_params(axis='y', labelsize=7.5, colors=ACCENT_RUST)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(ACCENT_RUST)

    # Sample count on right axis (thin teal line, no markers)
    ax2.plot(years, ns, color=ACCENT_TEAL, linewidth=0.9,
             linestyle=(0, (3, 2)), zorder=3, label='Talet stolar')
    ax2.set_ylabel('Talet stolar  (kumulativ)', fontsize=8.0, color=ACCENT_TEAL)
    ax2.tick_params(axis='y', labelsize=7.5, colors=ACCENT_TEAL)
    ax2.spines['top'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['right'].set_color(ACCENT_TEAL)

    fig.text(0.04, 0.95,
             f'Formrommet veks monotont: {growth:.0f}× over {len(rows)} periodar',
             fontsize=9.5, color=INK, ha='left', va='top', weight='bold')
    fig.text(0.04, 0.90,
             f'(H, W, D) konvekst hylster, 50-årsperiodar 1500–2050  ·  '
             f'1.–99. persentil klipping',
             fontsize=6.8, color=INK_SOFT, ha='left', va='top')

    fig.text(0.04, 0.025,
             f'n = {n_total} stolar med komplette dimensjonar  ·  '
             f'Start {vols[0]:.0f} cm³  ·  Slutt {vols[-1]:.0f} cm³',
             fontsize=6.5, color=INK_SOFT, ha='left')

    out = FIG_DIR / 'fig-A.6.4-ekspansjon.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    rows, growth, n = run_test()
    print(f'n = {n}, growth = {growth:.1f}× over {len(rows)} periods')
    for r in rows:
        print(f'  {r["period_start"]}  vol = {r["vol"]:>10.0f}  n = {r["n"]}')
    out = plot(rows, growth, n)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
