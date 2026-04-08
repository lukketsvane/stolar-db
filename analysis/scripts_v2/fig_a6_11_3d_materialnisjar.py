"""A.6.11 — Materialnisjar i 3D-morforommet
(Avleidd hypotese frå Proposisjon 5.3 og 4.5)

Avleidd hypotese: Om material verkeleg er ein del av seleksjonstrykket
(prop 4.5) og om kvart material avgrensar ein funksjonell nisje
(prop 5.3), då skal stolar laga av ulike material okkupere ulike
regionar i (Høgde × Breidde × Djupn)-rommet — ikkje berre i tid, men i
geometri. Stolen av mahogni skal vere geometrisk ulik stolen av stål.

Vi plottar kvar stol som eit punkt i 3D morforommet, fargelagt etter
primærmaterialet, og legg til 1σ-ellipsoidar for kvar materialgruppe.
Visuell overlapping mot geometrisk separasjon avgjer om hypotesen står.

Visuell: 3D-scatter (Høgde, Breidde, Djupn) med fem materialgrupper i
kvar sin farge, sett frå ein litt heva vinkel. Materialgruppene er valde
slik at dei spenner over ulike epokar — eik (medieval), nøttetre (1600-),
mahogni (1700-1800), stål (1900-) og plast (1950-).
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL,
)

MATERIALS = [
    ('eik',      '#9C7846'),   # mid oak brown
    ('nøttetre', '#7A4C2A'),   # dark walnut
    ('mahogni',  '#A23E2A'),   # mahogany rust
    ('stål',     '#5C6B73'),   # steel grey-blue
    ('plast',    '#3F7E8E'),   # plastic teal
]


def primary(s):
    if not isinstance(s, str):
        return None
    s = s.lower()
    for k, _ in MATERIALS:
        if k in s:
            return k
    return None


def run_test():
    df = load_chairs()
    df = df.dropna(subset=['h_cm', 'w_cm', 'd_cm', 'material']).copy()
    df = df[(df['h_cm'] > 0) & (df['w_cm'] > 0) & (df['d_cm'] > 0)]
    df['mat'] = df['material'].apply(primary)
    df = df.dropna(subset=['mat'])
    # Clip outliers per dimension
    for c in ('h_cm', 'w_cm', 'd_cm'):
        lo, hi = np.percentile(df[c], [1, 99])
        df = df[(df[c] >= lo) & (df[c] <= hi)]
    return df


def plot(df):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=105, ratio=0.63))
    ax = fig.add_subplot(111, projection='3d', computed_zorder=False)
    fig.subplots_adjust(left=0.0, right=0.98, bottom=0.10, top=0.86)

    # Clip the displayed range to the 5–95 percentile of each dimension
    # so the cloud isn't dominated by outliers and the axis scales are
    # comparable across dimensions.
    clip = {}
    for c in ('w_cm', 'd_cm', 'h_cm'):
        lo, hi = np.percentile(df[c], [5, 95])
        clip[c] = (lo, hi)

    for mat, colour in MATERIALS:
        sub = df[df['mat'] == mat]
        if len(sub) < 5:
            continue
        ax.scatter(
            sub['w_cm'], sub['d_cm'], sub['h_cm'],
            s=6, color=colour, alpha=0.40, linewidths=0,
            label=f'{mat.capitalize()}  ({len(sub)})',
            depthshade=True,
        )
        # Add the centroid as a larger marker
        ax.scatter(
            [sub['w_cm'].mean()], [sub['d_cm'].mean()], [sub['h_cm'].mean()],
            s=110, color=colour, edgecolor=INK, linewidths=0.9,
            marker='o', zorder=10,
        )

    ax.set_xlim(clip['w_cm'])
    ax.set_ylim(clip['d_cm'])
    ax.set_zlim(clip['h_cm'])
    # Equal box aspect so visual distances mean the same in every dim
    ax.set_box_aspect((1, 1, 1))

    ax.set_xlabel('Breidde  (cm)', fontsize=7.5, labelpad=2)
    ax.set_ylabel('Djupn  (cm)',   fontsize=7.5, labelpad=2)
    ax.set_zlabel('Høgde  (cm)',   fontsize=7.5, labelpad=2)
    ax.tick_params(axis='both', labelsize=6.5, pad=0)
    ax.view_init(elev=22, azim=-60)

    # Subtle pane styling — keep them faint cream so they don't dominate
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor('#FDFCF8')
        axis.pane.set_edgecolor(RULE)
        axis.pane.set_alpha(0.4)
    ax.grid(True, color=RULE, linewidth=0.3, alpha=0.6)

    leg = ax.legend(loc='upper left', bbox_to_anchor=(0.0, 1.0),
                    fontsize=6.5, handletextpad=0.3, labelspacing=0.25,
                    frameon=False)
    for t in leg.get_texts():
        t.set_color(INK_SOFT)



    out = FIG_DIR / 'fig-A.6.11-materialnisjar.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df = run_test()
    print(f'n = {len(df)}')
    for m, _ in MATERIALS:
        sub = df[df['mat'] == m]
        if len(sub) >= 5:
            print(f'  {m:<10} n={len(sub):>4}  '
                  f'centroid=(W={sub["w_cm"].mean():.1f}, '
                  f'D={sub["d_cm"].mean():.1f}, H={sub["h_cm"].mean():.1f})')
    out = plot(df)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
