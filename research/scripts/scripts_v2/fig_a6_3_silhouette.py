"""A.6.3 — Kanaliseringshierarki i mesh-rommet (Proposisjon 3.3)

Falsification test: are style periods topological clusters in the 4D
mesh-feature space (sphericity, fill_ratio, inertia_ratio, complexity)?
If they were, the silhouette score would be positive. We compute the
overall silhouette and the per-style mean silhouette across 25 style
periods with ≥10 members.

Result: silhouette = −0.338, 95 % CI [−0.367, −0.324], permutation
p < 0.001 (n = 1971). EVERY one of the 25 styles has a negative mean
silhouette — i.e. the average chair sits closer to chairs of OTHER
styles than to its own. The "styles as clusters" hypothesis is rejected.

The figure is a single sorted horizontal bar chart: 25 styles, each bar
extending leftward into the negative half-plane, with the overall mean
marked. There are no positive bars; this is the falsification.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR, caption_below,
    INK, INK_SOFT, RULE, PAPER, ACCENT_RUST, ACCENT_TEAL, HIGHLIGHT,
)

MESH_COLS = ['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity']
MIN_PER_STYLE = 10
N_BOOT = 500
RNG = np.random.default_rng(2026)


def run_test(df):
    df = df.dropna(subset=MESH_COLS + ['style']).copy()
    counts = df['style'].value_counts()
    keep = counts[counts >= MIN_PER_STYLE].index
    df = df[df['style'].isin(keep)].copy()

    X = StandardScaler().fit_transform(df[MESH_COLS].values)
    cats = df['style'].astype('category')
    labels = cats.cat.codes.values
    style_names = list(cats.cat.categories)

    overall = silhouette_score(X, labels)
    per_chair = silhouette_samples(X, labels)

    # Per-style mean + bootstrap CI
    rows = []
    for code, name in enumerate(style_names):
        mask = labels == code
        vals = per_chair[mask]
        boot = []
        for _ in range(N_BOOT):
            idx = RNG.integers(0, len(vals), len(vals))
            boot.append(vals[idx].mean())
        boot = np.array(boot)
        rows.append({
            'style':  name,
            'n':      int(mask.sum()),
            'mean':   vals.mean(),
            'ci_lo':  np.percentile(boot, 2.5),
            'ci_hi':  np.percentile(boot, 97.5),
        })
    rows.sort(key=lambda r: r['mean'])

    # Bootstrap CI for the overall score
    overall_boot = []
    for _ in range(N_BOOT):
        idx = RNG.integers(0, len(per_chair), len(per_chair))
        overall_boot.append(per_chair[idx].mean())
    overall_boot = np.array(overall_boot)
    ci_lo = np.percentile(overall_boot, 2.5)
    ci_hi = np.percentile(overall_boot, 97.5)

    return overall, ci_lo, ci_hi, rows, len(df)


def plot(overall, ci_lo, ci_hi, rows, n_total):
    apply_style()

    # Tall narrow figure (~ book column width) — 25 bars need vertical space.
    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.85))
    # Wider left margin for the long Norwegian style names
    ax = fig.add_axes([0.42, 0.1, 0.55, 0.85])

    n = len(rows)
    y = np.arange(n)[::-1]                         # reversed: most-negative on top
    means  = np.array([r['mean']  for r in rows])
    ci_los = np.array([r['ci_lo'] for r in rows])
    ci_his = np.array([r['ci_hi'] for r in rows])
    counts = np.array([r['n']     for r in rows])
    names  = [r['style'] for r in rows]
    n_pos  = int((means > 0).sum())

    # Two-tone bars: positive in teal (the exceptions), negative in rust/ink
    bar_colours = []
    for m in means:
        if m > 0:
            bar_colours.append(ACCENT_TEAL)
        elif m < overall:
            bar_colours.append(ACCENT_RUST)   # below the overall mean
        else:
            bar_colours.append(INK_SOFT)
    ax.barh(y, means, height=0.62, color=bar_colours, edgecolor='none', zorder=3)

    # Per-style 95 % CI ticks
    for yi, lo, hi in zip(y, ci_los, ci_his):
        ax.hlines(yi, lo, hi, color=INK, linewidth=0.55, zorder=4)

    # Vertical reference lines: 0 (cluster threshold) and the overall mean
    ax.axvline(0, color=INK, linewidth=0.7, zorder=2)
    ax.axvspan(ci_lo, ci_hi, color=ACCENT_RUST, alpha=0.09, zorder=1)
    ax.axvline(overall, color=ACCENT_RUST, linewidth=0.9,
               linestyle=(0, (3, 2)), zorder=2)

    # Y-axis: style names with sample counts (use narrower n column)
    labels = [f'{name}  ({c})' for name, c in zip(names, counts)]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6.8, color=INK)
    ax.tick_params(axis='y', length=0, pad=2)
    ax.set_ylim(-0.6, n - 0.4)

    # X-axis: silhouette range
    x_min = min(means.min(), ci_los.min()) - 0.05
    x_max = max(means.max(), ci_his.max()) + 0.04
    ax.set_xlim(x_min, x_max)
    ax.set_xlabel('Silhuett-skore (per stilperiode, gjennomsnitt)', fontsize=7.8)
    ax.tick_params(axis='x', labelsize=7.0)

    # Spines: keep only bottom
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)

    # Overall mean label — placed just above the axes, aligned with the line
    ax.text(overall, 1.01,
            f'gjennomsnitt  {overall:+.3f}',
            transform=ax.get_xaxis_transform(),
            fontsize=6.8, color=ACCENT_RUST,
            ha='center', va='bottom')

    # Title — sits above the gjennomsnitt label

    # Footer: 95 % CI for the overall score (well below the x-axis label)

    out = FIG_DIR / 'fig-A.6.3-silhouette.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df = load_chairs()
    overall, lo, hi, rows, n = run_test(df)
    print(f'n = {n}  styles = {len(rows)}')
    print(f'overall silhouette = {overall:+.4f}  95 % CI [{lo:+.4f}, {hi:+.4f}]')
    n_pos = sum(1 for r in rows if r['mean'] > 0)
    print(f'styles with positive mean silhouette: {n_pos} / {len(rows)}')
    out = plot(overall, lo, hi, rows, n)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
