"""A.6.8 — Materiell kompleksitet per nasjon

Test: do different national chair-making traditions blend more or fewer
materials per chair? The number of distinct material entries per chair
serves as a proxy for material complexity. If chairs were drawn from a
single global recipe we'd expect the per-country distributions to be
identical; if national traditions matter, they'll differ.

We compute, for every chair with both a country and a material list, the
number of comma-separated material tokens. Then we summarise per country
(mean, median, IQR, n).

Visual: horizontal "rain plot": per-country jittered dots overlaid with
mean ± IQR markers. No filled violins (they fight the warm-ink palette);
the dots speak for themselves and the markers carry the summary stats.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL,
)

MIN_PER_COUNTRY = 30
RNG = np.random.default_rng(2026)


def run_test():
    df = load_chairs()
    df = df.dropna(subset=['material', 'country']).copy()
    df['n_mat'] = df['material'].apply(
        lambda s: len([x for x in s.split(',') if x.strip()])
    )
    g = df.groupby('country')['n_mat'].agg(
        n='count', mean='mean', median='median',
        q25=lambda x: np.percentile(x, 25),
        q75=lambda x: np.percentile(x, 75),
        max='max',
    )
    g = g[g['n'] >= MIN_PER_COUNTRY]
    # Sort by median, then by mean as a tiebreaker
    g = g.sort_values(['median', 'mean'], ascending=[False, False])
    rows = []
    for country, row in g.iterrows():
        vals = df[df['country'] == country]['n_mat'].values
        rows.append({
            'country': country,
            'n': int(row['n']),
            'mean': float(row['mean']),
            'median': float(row['median']),
            'q25': float(row['q25']),
            'q75': float(row['q75']),
            'vals': vals,
        })
    return rows, len(df)


def plot(rows, n_total):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.73))
    ax = fig.add_axes([0.32, 0.15000000000000002, 0.62, 0.77])

    n = len(rows)
    y = np.arange(n)[::-1]

    for yi, r in zip(y, rows):
        v = r['vals']
        # Jittered dots
        jitter = RNG.uniform(-0.18, 0.18, size=len(v))
        ax.scatter(v, yi + jitter, s=2.5, color=INK_SOFT,
                   alpha=0.30, linewidths=0, zorder=2)
        # IQR bar
        ax.hlines(yi, r['q25'], r['q75'], color=ACCENT_RUST,
                  linewidth=2.2, alpha=0.85, zorder=4)
        # Median dot
        ax.scatter([r['median']], [yi], s=22, color=ACCENT_RUST,
                   edgecolor=INK, linewidth=0.5, zorder=5)
        # Mean small tick
        ax.scatter([r['mean']], [yi], s=14, marker='|',
                   color=INK, linewidth=1.0, zorder=6)

    # Y axis: country names with sample counts
    ax.set_yticks(y)
    ax.set_yticklabels([f'{r["country"]}  ({r["n"]})' for r in rows],
                       fontsize=7.2, color=INK)
    ax.tick_params(axis='y', length=0, pad=2)
    ax.set_ylim(-0.6, n - 0.4)

    # X axis
    max_v = max(r['vals'].max() for r in rows)
    ax.set_xlim(0.5, max_v + 0.5)
    ax.set_xticks(np.arange(1, max_v + 1))
    ax.set_xlabel('Talet på distinkte material per stol', fontsize=8.0)
    ax.tick_params(axis='x', labelsize=7.5)

    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)



    out = FIG_DIR / 'fig-A.6.8-materialblanding.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    rows, n = run_test()
    print(f'n = {n}, countries = {len(rows)}')
    for r in rows:
        print(f'  {r["country"]:<14}  n={r["n"]:>4}  '
              f'median={r["median"]:.1f}  mean={r["mean"]:.2f}  '
              f'IQR=[{r["q25"]:.1f},{r["q75"]:.1f}]')
    out = plot(rows, n)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
