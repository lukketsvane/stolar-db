"""A.6.2 — Stilperiode som samlevariabel / Kanaliseringshierarki
(Proposisjonar 2.4, 2.62)

Falsification test: are all geometric features equally constrained, or
does there exist a hierarchy where some features are heavily channelised
(small CV) and others run free (large CV)?

If chairs are uniform machines built to the same recipe, every dimension
would have a similar coefficient of variation. The article reports a 128×
spread across six mesh features (sphericity 0.074 → vol_hull 9.52),
spanning two orders of magnitude.

Visual: horizontal dot plot of CV per feature, log x-axis. The most
channelised features sit at the left, the most variable at the right.
Six points on a single line make the spread immediately legible.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, caption_below, FIG_DIR, ROOT,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL,
)

FEATURES = [
    ('sphericity',     'Sphericity'),
    ('complexity',     'Complexity (log v/a)'),
    ('fill_ratio',     'Fill-ratio'),
    ('inertia_ratio',  'Inertia-ratio'),
    ('vol_bbox',       'Boks-volum'),
    ('vol_hull',       'Hylster-volum'),
]
RNG = np.random.default_rng(2026)
N_BOOT = 500


def cv(x):
    x = x[x > 0]
    return x.std() / abs(x.mean())


def run_test():
    df = pd.read_csv(ROOT / 'analysis' / 'mesh_features.csv', low_memory=False)
    rows = []
    for col, label in FEATURES:
        v = df[col].dropna()
        v = v[v > 0].values
        c = cv(v)
        boots = []
        for _ in range(N_BOOT):
            idx = RNG.integers(0, len(v), len(v))
            boots.append(cv(v[idx]))
        boots = np.array(boots)
        rows.append({
            'col':    col,
            'label':  label,
            'cv':     c,
            'ci_lo':  np.percentile(boots, 2.5),
            'ci_hi':  np.percentile(boots, 97.5),
            'n':      len(v),
        })
    rows.sort(key=lambda r: r['cv'])
    spread = rows[-1]['cv'] / rows[0]['cv']
    return rows, spread


def plot(rows, spread):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.56))
    ax = fig.add_axes([0.3, 0.15000000000000002, 0.66, 0.77])

    n = len(rows)
    y = np.arange(n)[::-1]
    cvs    = np.array([r['cv']    for r in rows])
    ci_los = np.array([r['ci_lo'] for r in rows])
    ci_his = np.array([r['ci_hi'] for r in rows])
    labels = [r['label'] for r in rows]

    # Two-tone: lowest two CVs in teal (channelised), highest two in rust
    colours = []
    for i, c in enumerate(cvs):
        if i < 2:
            colours.append(ACCENT_TEAL)
        elif i >= n - 2:
            colours.append(ACCENT_RUST)
        else:
            colours.append(INK_SOFT)

    # CI horizontal bars + dots
    for yi, lo, hi, col in zip(y, ci_los, ci_his, colours):
        ax.hlines(yi, lo, hi, color=INK, linewidth=0.6, zorder=3)
    for yi, c, col in zip(y, cvs, colours):
        ax.scatter([c], [yi], s=42, color=col, zorder=4,
                   edgecolor='none')

    # Vertical reference lines: most-channelised + most-variable
    ax.axvline(cvs[0],  color=ACCENT_TEAL, linewidth=0.7,
               linestyle=(0, (3, 2)), alpha=0.55, zorder=1)
    ax.axvline(cvs[-1], color=ACCENT_RUST, linewidth=0.7,
               linestyle=(0, (3, 2)), alpha=0.55, zorder=1)

    # Y axis: feature labels with CV value to the right of each point
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.0, color=INK)
    ax.tick_params(axis='y', length=0, pad=2)
    ax.set_ylim(-0.6, n - 0.4)

    # CV value annotation next to each point
    for yi, c in zip(y, cvs):
        ax.text(c * 1.08, yi, f'{c:.3f}' if c < 1 else f'{c:.1f}',
                fontsize=6.8, color=INK_SOFT, ha='left', va='center')

    # X axis: log scale (covers two orders of magnitude)
    ax.set_xscale('log')
    ax.set_xlim(cvs.min() * 0.55, cvs.max() * 2.6)
    ax.set_xlabel('Variasjonskoeffisient  CV  (log)', fontsize=8.0)
    ax.tick_params(axis='x', labelsize=7.5)

    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)



    out = FIG_DIR / 'fig-A.6.2-kanalisering.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    rows, spread = run_test()
    print(f'spread = {spread:.1f}×')
    for r in rows:
        print(f'  {r["label"]:<22}  CV = {r["cv"]:.4f}  '
              f'95% CI [{r["ci_lo"]:.4f}, {r["ci_hi"]:.4f}]')
    out = plot(rows, spread)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
