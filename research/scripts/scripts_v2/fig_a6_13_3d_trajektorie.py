"""A.6.13 — Periodesentroidens vandring i (Breidde × Høgde × Djupn)
(Avleidd hypotese, falsifiserer postulat 4.1 i tre dimensjonar)

Kvar 50-årsperiode (1500–2050) får ein sentroide i fullt 3D
morforom. Her er trajektorien projisert ned på (Breidde × Høgde),
med Djupn koda som punktstorleik. Dette gir all tre dimensjonane
samtidig utan 3D-perspektivforvirring.

Empirisk funn:
  • banelengde 84 cm i fullt 3D
  • netto skift 25 cm
  • tortuositet 3.45 (banen vandrar fram og attende)

Den vandrande banen falsifiserer hypotesen om eit konstant
tilpassingslandskap. Funksjonell ergonomi har endra seg svært lite
over 500 år; sentroidvandringa er over éin standard avvik.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL, PAPER,
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

    df['period'] = ((df['year_mid'] - START) // BIN_W).astype(int) * BIN_W + START
    g = df.groupby('period').agg(
        n=('h_cm', 'count'),
        h=('h_cm', 'mean'),
        w=('w_cm', 'mean'),
        d=('d_cm', 'mean'),
    )
    g = g[g['n'] >= MIN_PER_BIN].copy()
    g.reset_index(inplace=True)

    pts = g[['h', 'w', 'd']].values
    diffs = np.diff(pts, axis=0)
    path_length  = float(np.sqrt((diffs ** 2).sum(axis=1)).sum())
    displacement = float(np.sqrt(((pts[-1] - pts[0]) ** 2).sum()))
    tortuosity   = path_length / displacement
    return df, g, path_length, displacement, tortuosity


def plot(df, g, path_length, displacement, tortuosity):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.85))
    ax = fig.add_axes([0.16, 0.15, 0.80, 0.78])

    w = g['w'].values
    h = g['h'].values
    d = g['d'].values
    n = g['n'].values
    p = g['period'].values

    cmap = LinearSegmentedColormap.from_list(
        'time', [ACCENT_TEAL, '#5A6B73', '#8A6F3B', ACCENT_RUST]
    )

    # Faint background scatter of all chairs (W, H)
    ax.scatter(df['w_cm'], df['h_cm'], s=1.5, color=INK_SOFT,
               alpha=0.10, linewidths=0, zorder=1)

    # Track line connecting all centroids
    ax.plot(w, h, color=INK_SOFT, linewidth=0.7, alpha=0.55, zorder=3)

    # Coloured arrows between successive periods
    for i in range(len(g) - 1):
        frac = i / max(len(g) - 2, 1)
        col = cmap(frac)
        arrow = FancyArrowPatch(
            (w[i], h[i]), (w[i + 1], h[i + 1]),
            arrowstyle='->', mutation_scale=12,
            color=col, lw=1.6, alpha=0.92, zorder=4,
        )
        ax.add_patch(arrow)

    # Centroid points — size encodes Djupn (depth), colour encodes time
    # Linearly map Djupn to bubble area
    d_norm = (d - d.min()) / (d.max() - d.min() + 1e-9)
    sizes = 60 + 240 * d_norm
    colours = [cmap(i / max(len(g) - 1, 1)) for i in range(len(g))]
    ax.scatter(w, h, s=sizes, c=colours, edgecolor=INK,
               linewidths=0.7, zorder=5)

    # Period labels — alternate above/below with enough offset
    for i, (xi, yi, pp) in enumerate(zip(w, h, p)):
        # Offset labels well clear of the bubbles (~14 pt)
        dy = 12 if i % 2 == 0 else -12
        ax.annotate(f'{int(pp)}',
                    xy=(xi, yi),
                    xytext=(0, dy), textcoords='offset points',
                    fontsize=6.5, color=INK,
                    weight='bold' if (i == 0 or i == len(g) - 1) else 'normal',
                    ha='center',
                    va='bottom' if dy > 0 else 'top')

    ax.set_xlabel('Breidde (cm)', fontsize=8.0)
    ax.set_ylabel('Høgde (cm)', fontsize=8.0)
    ax.tick_params(axis='both', labelsize=7.0)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)

    # Pad to give labels room
    pad_x = (w.max() - w.min()) * 0.18
    pad_y = (h.max() - h.min()) * 0.15
    ax.set_xlim(w.min() - pad_x, w.max() + pad_x)
    ax.set_ylim(h.min() - pad_y, h.max() + pad_y)

    # Compact size legend in upper-right corner
    leg_x = ax.get_xlim()[1] - 1
    leg_y_top = ax.get_ylim()[1] - 1
    ax.text(leg_x, leg_y_top, 'Punktstorleik = djupn',
            fontsize=5.8, color=INK_SOFT, ha='right', va='top',
            style='italic')

    out = FIG_DIR / 'fig-A.6.13-3d-trajektorie.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df, g, pl, disp, tort = run_test()
    print(f'n = {len(df)}, periods = {len(g)}')
    print(f'3D path length = {pl:.1f}, displacement = {disp:.1f}, '
          f'tortuosity = {tort:.2f}')
    out = plot(df, g, pl, disp, tort)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
