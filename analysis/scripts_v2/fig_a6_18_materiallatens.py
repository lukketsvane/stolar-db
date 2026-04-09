"""A.6.18 — Latente materialsignaturar
(Proposisjon 2.61 — signaturen er latent)

Hypothesis: every new structural material — stål, plast, aluminium,
kryssfiner — first occupies a region of the morphospace that is
geometrically indistinguishable from the wooden chair it replaces, and
only later diverges into its own niche.

Visual: 2×2 small multiples — one panel per material — plus a single
right-margin distance-to-tree timeseries that aggregates all four
trajectories. Every small multiple shows the SAME background scatter
of tree-only chairs (the wooden context that the new material must
either imitate or escape) and overlays the material's own chairs
plus a per-50-year centroid trajectory walking through the wood.

You can read the latency directly: when the coloured trail sits on
top of the grey wood scatter, the material is geometrically a
wooden chair. When the trail breaks free of the grey region, the
material has found its own niche.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL, ACCENT_GOLD, HIGHLIGHT, PAPER,
)

PLANE = ['w_cm', 'h_cm']
ALL_DIMS = ['h_cm', 'w_cm', 'd_cm']

TREE_TOKENS = (
    'tre', 'eik', 'bjørk', 'bjork', 'bøk', 'bok', 'furu',
    'mahogni', 'nøttetre', 'nottetre', 'ask', 'teak', 'valnøtt',
    'valnott', 'palisander', 'lønn', 'lonn', 'rosentre',
)

MODERN_MATERIALS = [
    ('stål',       'Stål',        ACCENT_RUST),
    ('plast',      'Plast',       ACCENT_TEAL),
    ('kryssfiner', 'Kryssfiner',  INK),
    ('aluminium',  'Aluminium',   ACCENT_GOLD),
]

START = 1750
END   = 2025
BIN_W = 50
MIN_PER_BIN = 6

B_LO, B_HI = 35, 90
H_LO, H_HI = 55, 110


def normalise_materials(s: str) -> list[str]:
    if not isinstance(s, str):
        return []
    return [t.strip().lower() for t in s.split(',') if t.strip()]


_TRIM = (
    'lær', 'lor', 'tekstil', 'ull', 'bomull', 'lin', 'silke',
    'skumplast', 'skumgummi', 'gummi', 'maling', 'lakk',
    'polyamid', 'messing', 'tinn', 'forgylling',
)


def is_tree_only(materials: list[str]) -> bool:
    if not materials:
        return False
    structural = [m for m in materials if m not in _TRIM]
    if not structural:
        return False
    return all(any(tok in m for tok in TREE_TOKENS) for m in structural)


def contains(materials: list[str], token: str) -> bool:
    return any(token in m for m in materials)


def run_test():
    df = load_chairs()
    df = df.dropna(subset=ALL_DIMS + ['year_mid', 'material']).copy()
    df = df[(df['h_cm'] > 0) & (df['w_cm'] > 0) & (df['d_cm'] > 0)]
    df = df[(df['year_mid'] >= START) & (df['year_mid'] <= END)]
    df['mat_list'] = df['material'].apply(normalise_materials)
    df['is_tree'] = df['mat_list'].apply(is_tree_only)

    bins = np.arange(START, END + 1, BIN_W)
    df['period'] = (np.digitize(df['year_mid'], bins) - 1) * BIN_W + START
    periods = sorted(df['period'].unique())

    tree_cent = {}
    for p in periods:
        sub = df[(df['period'] == p) & df['is_tree']]
        if len(sub) >= MIN_PER_BIN:
            tree_cent[p] = (
                sub[ALL_DIMS].mean().values,
                sub[PLANE].mean().values,
                len(sub),
            )

    out = {}
    for token, _, _ in MODERN_MATERIALS:
        rows = []
        for p in periods:
            if p not in tree_cent:
                continue
            sub = df[(df['period'] == p)
                     & df['mat_list'].apply(lambda m: contains(m, token))
                     & ~df['is_tree']]
            if len(sub) < MIN_PER_BIN:
                continue
            cent3 = sub[ALL_DIMS].mean().values
            cent2 = sub[PLANE].mean().values
            tree3, tree2, _ = tree_cent[p]
            dist = float(np.linalg.norm(cent3 - tree3))
            rows.append({
                'period': p,
                'n': len(sub),
                'cent3': cent3,
                'cent2': cent2,
                'tree2': tree2,
                'dist':  dist,
                'sub':   sub,
            })
        out[token] = rows
    return df, tree_cent, out, periods


def plot(df, tree_cent, results, periods):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=1.16))
    gs = fig.add_gridspec(
        3, 2,
        left=0.115, right=0.97,
        bottom=0.085, top=0.94,
        height_ratios=[1.0, 1.0, 0.92],
        wspace=0.18, hspace=0.34,
    )

    tree_pts = df[df['is_tree']]

    # ── 2x2 grid of material small multiples ────────────────────────────────
    panel_positions = {
        'stål':       (0, 0),
        'plast':      (0, 1),
        'kryssfiner': (1, 0),
        'aluminium':  (1, 1),
    }

    for token, label, color in MODERN_MATERIALS:
        r, c = panel_positions[token]
        ax = fig.add_subplot(gs[r, c])
        rows = results[token]

        # Background: every panel shows the same wood scatter
        ax.scatter(tree_pts['w_cm'], tree_pts['h_cm'],
                   s=1.6, c=RULE, alpha=0.32, linewidths=0,
                   zorder=1)

        if rows:
            # Per-period chair scatter for this material
            mat_scatter_x = []
            mat_scatter_y = []
            for r_ in rows:
                sub = r_['sub']
                mat_scatter_x.extend(sub['w_cm'].tolist())
                mat_scatter_y.extend(sub['h_cm'].tolist())
            ax.scatter(mat_scatter_x, mat_scatter_y,
                       s=2.4, c=color, alpha=0.28, linewidths=0,
                       zorder=2)

            # Centroid trajectory
            xs = np.array([r_['cent2'][0] for r_ in rows])
            ys = np.array([r_['cent2'][1] for r_ in rows])

            ax.plot(xs, ys, '-', color=color, linewidth=1.3,
                    alpha=0.95, zorder=4)
            ax.plot(xs, ys, 'o', color=color, markersize=3.4,
                    markeredgecolor=PAPER, markeredgewidth=0.7, zorder=5)

            # Direction arrow on the last segment
            if len(xs) >= 2:
                arrow = FancyArrowPatch(
                    (xs[-2], ys[-2]), (xs[-1], ys[-1]),
                    arrowstyle='->',
                    mutation_scale=8,
                    color=color, linewidth=0.0,
                    shrinkA=2.5, shrinkB=2.5,
                    zorder=6,
                )
                ax.add_patch(arrow)

            # Period labels next to dots — only first and last
            for i, r_ in enumerate(rows):
                if i == 0 or i == len(rows) - 1:
                    ax.text(r_['cent2'][0] + 1.0,
                            r_['cent2'][1] + 1.0,
                            str(r_['period']),
                            fontsize=5.0, color=color,
                            ha='left', va='bottom',
                            style='italic', alpha=0.85)

        # Title with material name in its own colour
        ax.set_title(label, fontsize=7.6, color=color, pad=2,
                     loc='left', weight='semibold')

        ax.set_xlim(B_LO, B_HI)
        ax.set_ylim(H_LO, H_HI)
        ax.set_xticks([40, 60, 80])
        ax.set_yticks([60, 80, 100])
        ax.tick_params(axis='both', labelsize=5.8)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)

        # Only the bottom row gets x-labels, only the left column gets y-labels
        if r != 1:
            ax.set_xticklabels([])
        if c != 0:
            ax.set_yticklabels([])

    # Shared axis labels for the 2x2 grid
    fig.text(0.495, 0.395,
             'Breidde  (cm)',
             fontsize=7.0, color=INK_SOFT, ha='center')
    fig.text(0.018, 0.69,
             'Høgde  (cm)',
             fontsize=7.0, color=INK_SOFT, ha='center', va='center',
             rotation=90)

    # ── Bottom row: distance-to-tree timeseries (full width) ────────────────
    ax2 = fig.add_subplot(gs[2, :])

    for token, label, color in MODERN_MATERIALS:
        rows = results[token]
        if not rows:
            continue
        xs = [r_['period'] + BIN_W / 2 for r_ in rows]
        ys = [r_['dist'] for r_ in rows]
        ax2.plot(xs, ys, '-', color=color, linewidth=1.3,
                 alpha=0.95, zorder=3)
        ax2.plot(xs, ys, 'o', color=color, markersize=3.4,
                 markeredgecolor=PAPER, markeredgewidth=0.7, zorder=4)
        # Endpoint label
        ax2.text(xs[-1] + 4, ys[-1], label,
                 fontsize=6.2, color=color, ha='left', va='center',
                 weight='semibold')

    # Latent threshold band
    ax2.axhspan(0, 12.0, color=INK_SOFT, alpha=0.07, zorder=1)
    ax2.text(START + 5, 11.3, 'latent sone (≤ 12 cm)',
             fontsize=5.8, color=INK_SOFT, ha='left', va='top',
             style='italic')

    ax2.set_xlim(START, END + 30)
    ax2.set_ylim(0, 45)
    ax2.set_xlabel('Periode-midt  (år)', fontsize=7.5)
    ax2.set_ylabel('Avstand til tre-sentroid  (cm)', fontsize=7.0)
    ax2.set_xticks([1800, 1850, 1900, 1950, 2000])
    ax2.tick_params(axis='both', labelsize=6.5)
    for s in ('top', 'right'):
        ax2.spines[s].set_visible(False)
    ax2.set_title('Latens-divergens (alle material)',
                  fontsize=7.4, color=INK_SOFT, pad=2,
                  loc='left', style='italic')

    out = FIG_DIR / 'fig-A.6.18-materiallatens.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df, tree_cent, results, periods = run_test()
    print(f'n total = {len(df)}, tree-only = {df["is_tree"].sum()}')
    for token, rows in results.items():
        print(f'\n{token}:')
        for r in rows:
            print(f'  {r["period"]}: n={r["n"]:3d}  '
                  f'dist={r["dist"]:5.2f} cm')
    out = plot(df, tree_cent, results, periods)
    print(f'\nwrote {out}')


if __name__ == '__main__':
    main()
