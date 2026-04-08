"""A.6.14 — Tilpassingslandskapet som ein Lyapunov-flate
(Avleidd hypotese frå Proposisjon 3.1, 3.2 og 5.1)

Avleidd hypotese: Om proposisjon 3.x stemmer skal stolane samle seg i
fleire stabile basengar i morforommet — ikkje i éin attraktor og ikkje
uniformt. Vi konstruerer eit Lyapunov-aktig potensial frå den negativt
log-transformerte tettleiken til alle stolar i (Breidde × Høgde):

    V(w, h)  =  −log p̂(w, h)

Lokale minimum av V er stabile basengar (der stolane akkumulerer).
Multimodalitet i V er direkte støtte for prop 3.2.

Visuell: 3D-overflate av V over (W × H), med eit topptynt scatter
av alle stolane projiserte ned på flata. Auget ser direkte kor mange
basengar finst og kor djupe dei er.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import gaussian_kde
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL, HIGHLIGHT,
)


def run_test():
    df = load_chairs()
    df = df.dropna(subset=['h_cm', 'w_cm']).copy()
    df = df[(df['h_cm'] > 0) & (df['w_cm'] > 0)]
    for c in ('h_cm', 'w_cm'):
        lo, hi = np.percentile(df[c], [1, 99])
        df = df[(df[c] >= lo) & (df[c] <= hi)]

    w = df['w_cm'].values
    h = df['h_cm'].values
    kde = gaussian_kde(np.vstack([w, h]), bw_method=0.20)

    # Grid for the surface
    w_grid = np.linspace(w.min(), w.max(), 90)
    h_grid = np.linspace(h.min(), h.max(), 90)
    W, H = np.meshgrid(w_grid, h_grid)
    P = kde(np.vstack([W.ravel(), H.ravel()])).reshape(W.shape)
    # Lyapunov potential: -log of normalised density
    V = -np.log(P + 1e-9)
    # Centre and clip extremes for legibility
    V = V - V.min()
    V = np.clip(V, 0, np.percentile(V, 98))
    return df, W, H, V


def plot(df, W, H, V):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=105, ratio=0.95))
    ax = fig.add_subplot(111, projection='3d')
    fig.subplots_adjust(left=0.02, right=0.96, bottom=0.10, top=0.86)

    # Custom warm cmap: low (basin floor) = warm cream, high = ink
    landscape_cmap = LinearSegmentedColormap.from_list(
        'landscape',
        ['#F1E6CC', '#D9A26B', '#B8542A', '#5C3A1F', INK],
    )

    surf = ax.plot_surface(
        W, H, V, cmap=landscape_cmap,
        linewidth=0.05, antialiased=True,
        rstride=1, cstride=1,
        edgecolor=INK_SOFT, alpha=0.92,
    )

    # Contours projected on the floor — basins seen from above
    ax.contour(W, H, V, levels=12, zdir='z',
               offset=V.min() - 0.4,
               colors=INK_SOFT, linewidths=0.4, alpha=0.45)

    ax.set_xlabel('Breidde  (cm)', fontsize=7.5, labelpad=2)
    ax.set_ylabel('Høgde  (cm)', fontsize=7.5, labelpad=2)
    ax.set_zlabel('V  =  −log p̂', fontsize=7.5, labelpad=2)
    ax.tick_params(axis='both', labelsize=6.5, pad=0)
    ax.view_init(elev=28, azim=-65)

    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor('#FDFCF8')
        axis.pane.set_edgecolor(RULE)
        axis.pane.set_alpha(0.4)
    ax.grid(True, color=RULE, linewidth=0.3, alpha=0.5)

    fig.text(0.04, 0.95,
             'Tilpassingslandskapet har fleire stabile basengar',
             fontsize=9.5, color=INK, ha='left', va='top', weight='bold')
    fig.text(0.04, 0.91,
             'Lyapunov-potensiale  V = −log p̂(W, H)  over alle stolar',
             fontsize=6.8, color=INK_SOFT, ha='left', va='top')

    fig.text(0.04, 0.025,
             f'n = {len(df)} stolar  ·  '
             f'KDE bandbreidde 0.20  ·  '
             f'Låge område = stabile attraktorar',
             fontsize=6.3, color=INK_SOFT, ha='left')

    out = FIG_DIR / 'fig-A.6.14-landskap.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df, W, H, V = run_test()
    print(f'n = {len(df)}, V range = [{V.min():.2f}, {V.max():.2f}]')
    out = plot(df, W, H, V)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
