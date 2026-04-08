"""A.6.9 — Materialstraumen over fem hundreår

Test: do material choices show selection waves consistent with the dynamic-
landscape postulate? If selection pressures over materials were constant,
the share of each material would be roughly flat in time. We expect to
see distinct waves: oak in the medieval-baroque era, walnut in the late
17th c., mahogni dominating the 18th c., and a steel/plastic/plywood
modernist wave in the 20th c.

We tokenise the comma-separated material list of every chair, normalise
to one of ten primary categories, and count for each 25-year period the
number of chairs that contain each material. The result is a stacked
area chart showing the changing material composition.

Visual: stacked filled-area plot, ten muted bands, x-axis 1500–2025,
y-axis chair count. Bands ordered chronologically by first dominance
so the visual flow reads left-to-right.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL,
)

START = 1500
END   = 2025
BIN_W = 25

# Ten primary materials, ordered by era of first dominance.
MATERIALS = [
    'eik', 'nøttetre', 'bøk', 'mahogni', 'furu', 'bjørk',
    'kryssfiner', 'stål', 'plast', 'aluminium',
]

# Warm/earthy palette — wood tones in browns/ochres, modern materials
# cooler. Each colour stays inside the warm-ink universe.
COLOURS = {
    'eik':        '#9C7846',  # mid oak brown
    'nøttetre':   '#7A4C2A',  # dark walnut
    'bøk':        '#C9A476',  # pale beech
    'mahogni':    '#A23E2A',  # mahogany rust
    'furu':       '#D9B97A',  # pine straw
    'bjørk':      '#E5D3A0',  # birch cream
    'kryssfiner': '#8A6A3D',  # plywood mid
    'stål':       '#5C6B73',  # steel grey-blue
    'plast':      '#3F7E8E',  # plastic teal
    'aluminium':  '#A8B0B6',  # aluminium grey
}


def primary_material(s):
    s = s.lower()
    for k in MATERIALS:
        if k in s:
            return k
    return None


def run_test():
    df = load_chairs()
    df = df.dropna(subset=['material', 'year_mid']).copy()
    df = df[(df['year_mid'] >= START) & (df['year_mid'] <= END)]

    df['mats_norm'] = df['material'].str.split(',').apply(
        lambda lst: list({primary_material(m.strip()) for m in lst
                          if primary_material(m.strip())})
    )
    df['period'] = (df['year_mid'] // BIN_W * BIN_W).astype(int)

    rows = []
    for p in sorted(df['period'].unique()):
        sub = df[df['period'] == p]
        row = {'period': p, 'total': len(sub)}
        for m in MATERIALS:
            row[m] = int(sub['mats_norm'].apply(lambda lst: m in lst).sum())
        rows.append(row)
    return pd.DataFrame(rows), len(df)


def plot(g, n_total):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.85))
    ax = fig.add_axes([0.13, 0.2, 0.73, 0.72])

    x = g['period'].values
    ys = [g[m].values for m in MATERIALS]

    # Stacked area
    ax.stackplot(
        x, *ys,
        labels=[m.capitalize() for m in MATERIALS],
        colors=[COLOURS[m] for m in MATERIALS],
        alpha=0.95, edgecolor='none',
    )

    # Total chair count line on top — thin black for context
    total = g['total'].values
    ax.plot(x, total, color=INK, linewidth=0.7, alpha=0.75, zorder=5)

    ax.set_xlim(START, END)
    ax.set_xlabel('Periode-start  (år)', fontsize=8.0)
    ax.set_ylabel('Talet stolar med materialet', fontsize=8.0)
    ax.tick_params(axis='both', labelsize=7.5)

    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)

    # Legend on the right side, two columns of small swatches
    leg = ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5),
                    fontsize=6.5, ncol=1, handlelength=1.0,
                    handletextpad=0.4, labelspacing=0.30,
                    borderaxespad=0)
    for t in leg.get_texts():
        t.set_color(INK_SOFT)

    # Title + sub

    fig.text(0.04, 0.025,
             f'n = {n_total} stolar med materialliste  ·  '
             f'25-årsperiodar  ·  Stolar med fleire material er talt for kvart',
             fontsize=6.3, color=INK_SOFT, ha='left')

    out = FIG_DIR / 'fig-A.6.9-materialstraum.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    g, n = run_test()
    print(f'n = {n}, periods = {len(g)}')
    print(g.to_string(index=False))
    out = plot(g, n)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
