"""A.6.5 — Mahogni-kollaps 1825–1849 (Proposisjon 4.5)

Falsification test: are local cohorts ever locked into a single material
by selection pressure? If yes, the dynamic-landscape postulate predicts
visible "kollaps" events where one material dominates a narrow window.

The article reports a clean Norwegian cohort: in 1825–1849, 16 of 16
chairs are mahogni; in 1750–1799 (the previous 25-year period that's
data-rich) the same fraction is 0 / 16. We reproduce that exactly.

Visual: 25-year Norwegian cohorts on the x-axis, mahogni fraction on
the y-axis, with the 1825–1849 cohort highlighted in rust. Sample
sizes printed above each bar.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, caption_below, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL,
)

MIN_N = 3
HIGHLIGHT_PERIOD = 1825


def run_test():
    df = load_chairs()
    nor = df[df['country'] == 'Noreg'].copy()
    nor['has_mahogni'] = nor['material'].str.lower().str.contains('mahogni', na=False)
    nor = nor.dropna(subset=['year_mid'])
    nor['period25'] = (nor['year_mid'] // 25 * 25).astype(int)
    g = nor.groupby('period25').agg(
        n=('material', 'count'),
        n_mahogni=('has_mahogni', 'sum'),
    )
    g['frac'] = g['n_mahogni'] / g['n']
    g = g[g['n'] >= MIN_N].copy()
    g.reset_index(inplace=True)
    return g, len(nor)


def plot(g, n_total):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.78))
    ax = fig.add_axes([0.13, 0.20, 0.83, 0.62])

    periods = g['period25'].values
    fracs   = g['frac'].values
    ns      = g['n'].values

    # Bar colours: highlight period in rust, others in soft ink
    colours = [ACCENT_RUST if p == HIGHLIGHT_PERIOD else INK_SOFT
               for p in periods]
    ax.bar(periods, fracs, width=22, color=colours, edgecolor='none', zorder=3)

    # Sample size annotation above each bar
    for p, f, n in zip(periods, fracs, ns):
        ax.text(p, f + 0.03, f'{n}', fontsize=6.0,
                color=INK_SOFT, ha='center', va='bottom')

    # Highlight band for the lock-in cohort
    ax.axvspan(HIGHLIGHT_PERIOD - 12, HIGHLIGHT_PERIOD + 13,
               color=ACCENT_RUST, alpha=0.07, zorder=1)

    # Annotation for the 1825-1849 spike
    spike = g[g['period25'] == HIGHLIGHT_PERIOD]
    if len(spike):
        ax.annotate(
            '1825–1849:  16 av 16',
            xy=(HIGHLIGHT_PERIOD, 1.0),
            xytext=(HIGHLIGHT_PERIOD - 60, 0.78),
            fontsize=7.5, color=ACCENT_RUST,
            ha='right',
            arrowprops=dict(arrowstyle='-', color=ACCENT_RUST,
                            linewidth=0.6, shrinkB=2),
        )

    # Y axis: percentage 0-100%
    ax.set_ylim(0, 1.18)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['0 %', '25 %', '50 %', '75 %', '100 %'])
    ax.set_ylabel('Del med mahogni', fontsize=8.0)
    ax.tick_params(axis='y', labelsize=7.5)

    # X axis
    ax.set_xlim(periods.min() - 25, periods.max() + 25)
    ax.set_xlabel('25-årsperiode  (start)', fontsize=8.0)
    ax.tick_params(axis='x', labelsize=7.5)

    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)

    fig.text(0.04, 0.95,
             'Mahogni-låsing i norske stolar, 1825–1849',
             fontsize=9.5, color=INK, ha='left', va='top', weight='bold')
    fig.text(0.04, 0.90,
             'Frå null mahogni i førre periode (1750–1799) til 100 % i éin generasjon',
             fontsize=6.8, color=INK_SOFT, ha='left', va='top')

    fig.text(0.04, 0.025,
             f'n = {n_total} norske stolar  ·  '
             f'kohorter med ≥ {MIN_N} stolar  ·  Talet over kvar bar = stolar i kohorten',
             fontsize=6.5, color=INK_SOFT, ha='left')

    out = FIG_DIR / 'fig-A.6.5-mahogni.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    g, n_total = run_test()
    print(f'Norwegian total: {n_total}')
    print(g.to_string())
    out = plot(g, n_total)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
