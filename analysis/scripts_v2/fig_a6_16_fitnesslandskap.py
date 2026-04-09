"""A.6.17 — Tilpassingslandskapet som tettleiksflate
(Avleidd hypotese frå Proposisjon 3.2)

Avleidd hypotese: Tilpassingslandskapet over (Breidde, Høgde) skal
ha fleire stabile attraktorar (basengar) snarare enn éin global
optimum eller uniform fordeling. Vi konstruerer ei 2D KDE-tettleik
p̂(W, H), plottar henne som ein 3D-overflate, og merker dei lokale
maksimumspunkta som raude prikkar.

Visuell: KDE-tettleik som 3D-flate over (Breidde × Høgde), med
varm fargemap. Lokale maksimum (basengar) er markert som raude
prikkar oppe på flata.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import gaussian_kde
from scipy.ndimage import maximum_filter
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL,
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
    kde = gaussian_kde(np.vstack([w, h]), bw_method=0.22)

    w_grid = np.linspace(w.min(), w.max(), 90)
    h_grid = np.linspace(h.min(), h.max(), 90)
    W, H = np.meshgrid(w_grid, h_grid)
    Z = kde(np.vstack([W.ravel(), H.ravel()])).reshape(W.shape)
    # Normalise to [0, 1] for the 3D surface display
    Z = Z / Z.max()

    # Find local maxima (3x3 neighbourhood) above a small floor
    nb_max = maximum_filter(Z, size=8)
    is_peak = (Z == nb_max) & (Z > 0.20)
    peaks = np.argwhere(is_peak)
    peak_coords = [(W[r, c], H[r, c], Z[r, c]) for r, c in peaks]
    return df, W, H, Z, peak_coords


def plot(df, W, H, Z, peaks):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=105, ratio=0.55))
    ax = fig.add_subplot(111, projection='3d')
    fig.subplots_adjust(left=0.0, right=0.96, bottom=0.10, top=0.96)

    # Warm cream-to-rust-to-ink colormap (matches the book palette)
    landscape_cmap = LinearSegmentedColormap.from_list(
        'landscape',
        ['#FBF1DC', '#E8C788', '#D9883C', '#A23E2A', '#5C2A1F'],
    )

    surf = ax.plot_surface(
        W, H, Z, cmap=landscape_cmap,
        linewidth=0.05, antialiased=True,
        rstride=1, cstride=1,
        edgecolor='none', alpha=0.95,
    )

    # Local maxima as red dots, with drop-lines to the floor
    for wp, hp, zp in peaks:
        ax.scatter([wp], [hp], [zp], color='#D32F2F', s=42,
                   edgecolor=INK, linewidths=0.6, depthshade=False, zorder=10)
        ax.plot([wp, wp], [hp, hp], [0, zp],
                color='#D32F2F', linewidth=0.7, alpha=0.7, zorder=9)
        ax.text(wp, hp, zp + 0.06,
                f'({wp:.0f}, {hp:.0f})',
                fontsize=5.8, color='#7A1818',
                ha='center', va='bottom')

    # Contours projected on the floor
    ax.contour(W, H, Z, levels=10, zdir='z',
               offset=-0.02,
               colors=INK_SOFT, linewidths=0.4, alpha=0.5)

    ax.set_xlabel('Breidde  (cm)', fontsize=7.5, labelpad=2)
    ax.set_ylabel('Høgde  (cm)',   fontsize=7.5, labelpad=2)
    ax.set_zlabel('Tettleik (norm.)', fontsize=7.5, labelpad=2)
    ax.tick_params(axis='both', labelsize=6.5, pad=0)
    ax.view_init(elev=32, azim=-60)
    ax.set_zlim(0, 1.05)

    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor('#FDFCF8')
        axis.pane.set_edgecolor(RULE)
        axis.pane.set_alpha(0.4)
    ax.grid(True, color=RULE, linewidth=0.3, alpha=0.5)


    out = FIG_DIR / 'fig-A.6.16-fitnesslandskap.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df, W, H, Z, peaks = run_test()
    print(f'n = {len(df)}, peaks found = {len(peaks)}')
    for w, h, z in peaks:
        print(f'  peak at W={w:.1f}, H={h:.1f}, density={z:.3f}')
    out = plot(df, W, H, Z, peaks)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
