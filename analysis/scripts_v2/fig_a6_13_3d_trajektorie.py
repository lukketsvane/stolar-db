"""A.6.13 — Periodesentroidens 3D-vandring 1500–2025
(Avleidd hypotese, falsifiserer postulat 4.1 i tre dimensjonar)

Avleidd hypotese: A.6.7 viste at sentroiden vandrar i 2D-projeksjon
(H × B). Men ein konstant tilpassingslandskap kan i prinsippet vere
konstant i to dimensjonar og endre seg i den tredje. Vi testar derfor
om sentroiden òg vandrar i FULL 3D — dvs. (Høgde × Breidde × Djupn).

Vi reknar ut sentroiden av kvar 50-årsperiode i 3D og koplar dei
saman som ein bane. Banelengda i 3D og tortuositeten skal vere
samanliknbare med eller større enn dei 2D-tala.

Visuell: 3D-bane gjennom morforommet, med kvar periodesentroide som ein
fargepunkt frå tidleg (mørk teal) til seint (rust). Linjer mellom
suksessive periodar med pillar-thin alpha. Ingen lågsynt-perspektiv —
banen skal vere lett å lese.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL,
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
        h_mean=('h_cm', 'mean'),
        w_mean=('w_cm', 'mean'),
        d_mean=('d_cm', 'mean'),
    )
    g = g[g['n'] >= MIN_PER_BIN].copy()
    g.reset_index(inplace=True)

    pts = g[['h_mean', 'w_mean', 'd_mean']].values
    diffs = np.diff(pts, axis=0)
    path_length  = float(np.sqrt((diffs ** 2).sum(axis=1)).sum())
    displacement = float(np.sqrt(((pts[-1] - pts[0]) ** 2).sum()))
    tortuosity   = path_length / displacement
    return df, g, path_length, displacement, tortuosity


def plot(df, g, path_length, displacement, tortuosity):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=105, ratio=0.95))
    ax = fig.add_subplot(111, projection='3d')
    fig.subplots_adjust(left=0.0, right=0.96, bottom=0.10, top=0.86)

    h = g['h_mean'].values
    w = g['w_mean'].values
    d = g['d_mean'].values
    n = g['n'].values
    p = g['period'].values

    # Trajectory line (segments coloured along time)
    cmap = LinearSegmentedColormap.from_list(
        'time', [ACCENT_TEAL, '#5A6B73', ACCENT_RUST]
    )
    for i in range(len(g) - 1):
        frac = i / max(len(g) - 2, 1)
        col = cmap(frac)
        ax.plot([w[i], w[i + 1]],
                [d[i], d[i + 1]],
                [h[i], h[i + 1]],
                color=col, linewidth=1.8, alpha=0.9, zorder=4)

    # Centroids — sized by sample count, coloured by time
    sizes = 60 + 4.0 * np.sqrt(n)
    colours = [cmap(i / max(len(g) - 1, 1)) for i in range(len(g))]
    ax.scatter(w, d, h, s=sizes, c=colours,
               edgecolor=INK, linewidths=0.8, depthshade=True, zorder=6)

    # Drop-lines from each centroid to the (W, D) floor — anchors the eye
    z_floor = h.min() - 5
    for xi, yi, zi in zip(w, d, h):
        ax.plot([xi, xi], [yi, yi], [z_floor, zi],
                color=INK_SOFT, linewidth=0.4, alpha=0.4, zorder=2)
    # Faint floor track
    ax.plot(w, d, [z_floor] * len(w),
            color=INK_SOFT, linewidth=0.6, alpha=0.5, zorder=3)

    # Period labels at every centroid — alternating offset
    for i, (xi, yi, zi, pp) in enumerate(zip(w, d, h, p)):
        dz = 1.5 if i % 2 == 0 else -3.0
        ax.text(xi, yi, zi + dz, str(int(pp)),
                fontsize=6.0, color=INK,
                ha='center', va='bottom')

    # Zoom axes around the centroid region with a small pad
    pad = 6
    ax.set_xlim(w.min() - pad, w.max() + pad)
    ax.set_ylim(d.min() - pad, d.max() + pad)
    ax.set_zlim(z_floor, h.max() + pad)

    ax.set_xlabel('Breidde  (cm)', fontsize=7.5, labelpad=2)
    ax.set_ylabel('Djupn  (cm)',   fontsize=7.5, labelpad=2)
    ax.set_zlabel('Høgde  (cm)',   fontsize=7.5, labelpad=2)
    ax.tick_params(axis='both', labelsize=6.5, pad=0)
    ax.view_init(elev=18, azim=-65)

    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor('#FDFCF8')
        axis.pane.set_edgecolor(RULE)
        axis.pane.set_alpha(0.4)
    ax.grid(True, color=RULE, linewidth=0.3, alpha=0.6)


    fig.text(0.04, 0.025,
             f'n = {len(df)} stolar  ·  '
             f'Total bane {path_length:.0f} cm  ·  '
             f'Netto {displacement:.0f} cm  ·  '
             f'Tortuositet {tortuosity:.2f}',
             fontsize=6.3, color=INK_SOFT, ha='left')

    out = FIG_DIR / 'fig-A.6.13-3d-trajektorie.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df, g, pl, disp, tort = run_test()
    print(f'n = {len(df)}, periods = {len(g)}')
    print(f'3D path length = {pl:.1f}, displacement = {disp:.1f}, '
          f'tortuosity = {tort:.2f}')
    print(g[['period', 'n', 'h_mean', 'w_mean', 'd_mean']].to_string(index=False))
    out = plot(df, g, pl, disp, tort)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
