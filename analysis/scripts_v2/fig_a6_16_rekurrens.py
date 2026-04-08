"""A.6.16 — Rekurrensanalyse: gjentar formhistoria seg?
(Avleidd hypotese frå Proposisjon 4.1 og 4.4)

Avleidd hypotese: Om proposisjon 4.1 (dynamisk landskap) og 4.4
(monoton ekspansjon) begge er sanne, skal formhistoria IKKJE gjenta
seg. Vi reknar ut sentroidane (H, W, D) for kvar 25-årsperiode
1500–2025 og kalkulerer den parvise euklidiske avstanden mellom alle
periodar.

Visuell: ein einleg, stor symmetrisk avstandsmatrise. Mørke celler
= nære periodar (rekurrens). Det modernistiske brotet etter 1900
viser seg som ein lys L-form i nedre høgre hjørne. Ingen periodar
før 1900 liknar nokon periode etter 1900.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial.distance import pdist, squareform

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL, PAPER,
)

START = 1500
END   = 2025
BIN_W = 25
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
    pts = g[['h', 'w', 'd']].values
    periods = g.index.values
    dist = squareform(pdist(pts))
    return df, periods, dist


def plot(df, periods, dist):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.55))
    ax = fig.add_axes([0.16, 0.1, 0.74, 0.8300000000000001])

    # Cream → rust → ink colormap. Light = similar, dark = far.
    warm_cmap = LinearSegmentedColormap.from_list(
        'warm', ['#FBF1DC', '#E8C788', '#D9883C', '#A23E2A', '#3A1A12']
    )

    extent = [periods[0], periods[-1], periods[-1], periods[0]]
    im = ax.imshow(dist, cmap=warm_cmap, extent=extent, aspect='equal',
                   interpolation='nearest')

    # Era guide lines — major centuries
    for year in (1700, 1800, 1900):
        ax.axhline(year, color=INK, linewidth=0.4, alpha=0.4)
        ax.axvline(year, color=INK, linewidth=0.4, alpha=0.4)

    # Annotate the modernist break in the lower-right corner
    ax.annotate(
        'modernismen\nbryt med fortida',
        xy=(1980, 1980), xytext=(1830, 1620),
        fontsize=6.5, color=ACCENT_RUST, ha='center', va='center',
        arrowprops=dict(arrowstyle='->', color=ACCENT_RUST,
                        lw=0.7, alpha=0.85),
    )

    ax.set_xlabel('Periode-start  (år)', fontsize=8.0)
    ax.set_ylabel('Periode-start  (år)', fontsize=8.0)
    ax.tick_params(axis='both', labelsize=7.0)
    ax.set_xticks(np.arange(1500, 2026, 100))
    ax.set_yticks(np.arange(1500, 2026, 100))
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)

    # Colorbar — slim, on the right
    cbar = fig.colorbar(im, ax=ax, pad=0.02, fraction=0.045, shrink=0.8)
    cbar.ax.tick_params(labelsize=6.0, length=0)
    cbar.outline.set_visible(False)
    cbar.set_label('Eukl. avstand (cm)', fontsize=6.5, color=INK_SOFT)


    out = FIG_DIR / 'fig-A.6.16-rekurrens.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df, periods, dist = run_test()
    print(f'n periods = {len(periods)}, mean dist = {dist[np.triu_indices_from(dist, k=1)].mean():.2f}')
    out = plot(df, periods, dist)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
