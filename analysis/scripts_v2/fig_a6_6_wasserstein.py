"""A.6.6 — Wasserstein-distansen mellom suksessive periodar
(Proposisjon 4.5 — falsifisering av stase-nullhypotesen)

Falsification test: are successive 50-year cohorts statistically the
same? If the morphospace were static, the Wasserstein-1 distance between
successive period distributions would hover around zero. The article's
threshold for "no movement" is 0.5 cm.

We compute the Wasserstein-1 distance between successive 50-year
periods for each of (Høgde, Breidde, Djupn). The article reports
mean distances of 14.4, 8.2, 5.9 cm respectively across 10 period pairs,
with no pair under 0.5 cm. We replicate that.

Visual: three thin vertically-stacked sparkline-style panels (one per
dimension), each showing the distances between successive period pairs
as bars, with the 0.5 cm "no movement" threshold drawn as a faint
horizontal line.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import wasserstein_distance

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, caption_below, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL, HIGHLIGHT,
)

DIMS = [('h_cm', 'Høgde'), ('w_cm', 'Breidde'), ('d_cm', 'Djupn')]
START = 1500
END   = 2050
BIN_W = 50
THRESHOLD = 0.5    # cm: "no movement"
MIN_PER_BIN = 5


def run_test():
    df = load_chairs()
    df = df.dropna(subset=['h_cm', 'w_cm', 'd_cm', 'year_mid'])
    df = df[(df['h_cm'] > 0) & (df['w_cm'] > 0) & (df['d_cm'] > 0)]
    df = df[(df['year_mid'] >= START) & (df['year_mid'] <= END)]
    bins = np.arange(START, END + 1, BIN_W)
    df = df.copy()
    df['bin'] = np.digitize(df['year_mid'], bins) - 1

    used = sorted(df['bin'].unique())
    pair_starts = []
    out = {label: [] for _, label in DIMS}

    for i in range(len(used) - 1):
        a_idx, b_idx = used[i], used[i + 1]
        a = df[df['bin'] == a_idx]
        b = df[df['bin'] == b_idx]
        if len(a) < MIN_PER_BIN or len(b) < MIN_PER_BIN:
            continue
        pair_starts.append((int(bins[a_idx]), int(bins[b_idx])))
        for col, label in DIMS:
            out[label].append(wasserstein_distance(a[col].values, b[col].values))

    summary = {label: {
        'mean': float(np.mean(out[label])),
        'min':  float(np.min(out[label])),
        'max':  float(np.max(out[label])),
        'all':  out[label],
    } for _, label in DIMS}
    return pair_starts, summary, len(df)


def plot(pair_starts, summary, n_total):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.89))
    gs = fig.add_gridspec(3, 1, left=0.16, right=0.96,
                          bottom=0.13, top=0.82, hspace=0.45)

    pair_labels = [f'{a}\n–\n{b}' for a, b in pair_starts]
    x = np.arange(len(pair_labels))
    y_max = max(summary[label]['max'] for _, label in DIMS) * 1.10

    for i, (col, label) in enumerate(DIMS):
        ax = fig.add_subplot(gs[i, 0])
        vals = np.array(summary[label]['all'])
        bars = ax.bar(x, vals, width=0.78,
                      color=ACCENT_RUST if i == 0 else (ACCENT_TEAL if i == 1 else INK_SOFT),
                      edgecolor='none', zorder=3)

        # Threshold line
        ax.axhline(THRESHOLD, color=INK_SOFT, linewidth=0.5,
                   linestyle=(0, (3, 2)), alpha=0.6, zorder=2)
        ax.text(len(x) - 0.4, THRESHOLD + 0.4, '0,5 cm',
                fontsize=6.0, color=INK_SOFT, ha='right', va='bottom')

        # Mean line
        m = summary[label]['mean']
        ax.axhline(m, color=INK, linewidth=0.5, linestyle=':', alpha=0.7, zorder=2)

        ax.set_ylim(0, y_max)
        ax.set_yticks([0, 10, 20, 30])
        ax.set_yticklabels(['0', '10', '20', '30'], fontsize=6.5)
        ax.set_ylabel(f'{label}\n(cm)', fontsize=7.5, color=INK, rotation=0,
                      ha='right', va='center', labelpad=14)

        # Mean number annotation at the right edge
        ax.text(1.005, m / y_max, f'snitt {m:.1f}',
                transform=ax.transAxes, ha='left', va='center',
                fontsize=6.3, color=INK_SOFT)

        # X axis only on the bottom panel
        if i == len(DIMS) - 1:
            ax.set_xticks(x)
            ax.set_xticklabels([str(a) for a, _ in pair_starts],
                               fontsize=6.5, rotation=0)
            ax.set_xlabel('Periode-start  (år)', fontsize=7.5)
        else:
            ax.set_xticks([])

        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)



    out = FIG_DIR / 'fig-A.6.6-wasserstein.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    pair_starts, summary, n = run_test()
    print(f'n = {n}, pairs = {len(pair_starts)}')
    for _, label in DIMS:
        s = summary[label]
        print(f'  {label}:  mean = {s["mean"]:.2f}  min = {s["min"]:.2f}  max = {s["max"]:.2f}')
    out = plot(pair_starts, summary, n)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
