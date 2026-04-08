"""A.6.7 — Direkte falsifisering av postulat 4.1
Postulat 4.1: «Seleksjonstrykka er ikkje konstante over tid.»

Falsification test: if the selection pressures over chair geometry were
constant, the morphospace centroid for each period would sit at the same
point. Any movement of the centroid is direct evidence that the pressures
have changed and the dynamic-landscape postulate holds.

We compute the centroid (mean H, W, D) of each 50-year period from 1500
to 2050 and trace the trajectory through (Høgde × Breidde) space. The
total path length is 84.4 cm, the net displacement is 24.5 cm, and the
tortuosity is 3.45 — i.e. the centroid wanders, then doubles back, then
moves again.

If the postulate were false, every period centroid would sit on top of
every other one. The figure shows a clear walk, falsifying the static-
landscape null.

Visual: a single 2D scatter (mean Høgde × mean Breidde), period
centroids connected by arrows, each centroid labelled with its period
start year and bubble-sized by sample count.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, caption_below, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL, HIGHLIGHT,
)

START = 1500
END   = 2050
BIN_W = 50
MIN_PER_BIN = 5


def run_test():
    df = load_chairs()
    df = df.dropna(subset=['h_cm', 'w_cm', 'd_cm', 'year_mid']).copy()
    df = df[(df['h_cm'] > 0) & (df['w_cm'] > 0) & (df['d_cm'] > 0)]
    df = df[(df['year_mid'] >= START) & (df['year_mid'] <= END)]
    for c in ('h_cm', 'w_cm', 'd_cm'):
        lo, hi = np.percentile(df[c], [1, 99])
        df = df[(df[c] >= lo) & (df[c] <= hi)]

    bins = np.arange(START, END + 1, BIN_W)
    df['bin'] = np.digitize(df['year_mid'], bins) - 1
    g = df.groupby('bin').agg(
        n=('h_cm', 'count'),
        h_mean=('h_cm', 'mean'), h_sem=('h_cm', lambda x: x.std() / np.sqrt(len(x))),
        w_mean=('w_cm', 'mean'), w_sem=('w_cm', lambda x: x.std() / np.sqrt(len(x))),
        d_mean=('d_cm', 'mean'),
    )
    g = g[g['n'] >= MIN_PER_BIN].copy()
    g['period_start'] = bins[g.index.values]
    g.reset_index(drop=True, inplace=True)

    trajectory = g[['h_mean', 'w_mean', 'd_mean']].values
    diffs = np.diff(trajectory, axis=0)
    path_length  = float(np.sqrt((diffs ** 2).sum(axis=1)).sum())
    displacement = float(np.sqrt(((trajectory[-1] - trajectory[0]) ** 2).sum()))
    tortuosity   = path_length / displacement
    return g, len(df), path_length, displacement, tortuosity


def plot(g, n_total, path_length, displacement, tortuosity):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.95))
    ax = fig.add_axes([0.16, 0.15, 0.8, 0.76])

    h = g['h_mean'].values
    w = g['w_mean'].values
    n = g['n'].values
    periods = g['period_start'].values

    # Light "track" line behind the points
    ax.plot(w, h, color=INK_SOFT, linewidth=0.7,
            linestyle='-', alpha=0.55, zorder=2)

    # Arrows between successive periods
    for i in range(len(g) - 1):
        arrow = FancyArrowPatch(
            (w[i], h[i]), (w[i + 1], h[i + 1]),
            arrowstyle='->', mutation_scale=8,
            color=ACCENT_RUST, linewidth=0.0, alpha=0.7, zorder=3,
        )
        ax.add_patch(arrow)

    # Period centroids — bubble size by sample count
    bubble = 12 + 1.5 * np.sqrt(n)
    ax.scatter(w, h, s=bubble, color=ACCENT_RUST, edgecolor=INK,
               linewidth=0.6, zorder=4)

    # Period labels — alternate up/down to avoid overlap
    for i, (xi, yi, p) in enumerate(zip(w, h, periods)):
        dy = 1.2 if i % 2 == 0 else -1.6
        ax.annotate(f'{p}', xy=(xi, yi),
                    xytext=(0, dy * 4), textcoords='offset points',
                    fontsize=6.2, color=INK_SOFT,
                    ha='center', va='center')

    # Highlight start and end with bigger labels
    ax.annotate(f'Start  {periods[0]}', xy=(w[0], h[0]),
                xytext=(8, 8), textcoords='offset points',
                fontsize=7, color=ACCENT_RUST, weight='bold')
    ax.annotate(f'Slutt  {periods[-1]}', xy=(w[-1], h[-1]),
                xytext=(8, -10), textcoords='offset points',
                fontsize=7, color=ACCENT_RUST, weight='bold')

    ax.set_xlabel('Gjennomsnittleg  breidde  (cm)', fontsize=8.0)
    ax.set_ylabel('Gjennomsnittleg  høgde  (cm)', fontsize=8.0)
    ax.tick_params(axis='both', labelsize=7.5)

    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)


    fig.text(0.04, 0.025,
             f'n = {n_total} stolar  ·  '
             f'Total bane {path_length:.0f} cm  ·  '
             f'Netto skift {displacement:.0f} cm  ·  '
             f'Tortuositet {tortuosity:.2f}',
             fontsize=6.5, color=INK_SOFT, ha='left')

    out = FIG_DIR / 'fig-A.6.7-trajektorie.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    g, n, pl, disp, tort = run_test()
    print(f'n = {n}, periods = {len(g)}')
    print(f'path length = {pl:.1f}, displacement = {disp:.1f}, tortuosity = {tort:.2f}')
    print(g[['period_start', 'n', 'h_mean', 'w_mean', 'd_mean']].to_string(index=False))
    out = plot(g, n, pl, disp, tort)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
