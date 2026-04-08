"""A.6.15 — Stilperiodefylogenese (Ward-klynging)
(Avleidd hypotese frå Proposisjon 3.4)

Avleidd hypotese: Sjølv om individuelle stolar ikkje klynger seg
(A.6.3), kan det finnast ein hierarkisk struktur PÅ STILNIVÅ. Vi
treffer eit dendrogram av sentroidane til kvar stilperiode i
mesh-trekkrommet (sphericity, fill_ratio, inertia_ratio, complexity)
ved Ward-linkage. Ein meiningsfull hierarki vil grupere historisk
nær-relaterte stilar saman.

Visuell: dendrogram med Ward-distanse på X-aksen, stilperiodar på
Y-aksen, fargesett etter epoke (pre-1700, 1700-talet, 1800-talet,
1900-talet, samtid).
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL,
)

MESH_COLS = ['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity']
MIN_PER_STYLE = 10

# Crude epoch assignment for colouring; only used for label colours.
def epoch(style: str) -> str:
    s = style.lower()
    pre1700 = ('renessanse', 'barokk', 'régence')
    e1700 = ('rokokko', 'louis xvi', 'chippendale', 'hepplewhite',
             'régence', 'nyrokokko')
    e1800 = ('nyklassisisme', 'empire', 'historisme', 'viktorianisme',
             'wiener bentwood')
    e1900 = ('jugend', 'art nouveau', 'art deco', 'tidleg modernisme',
             'bauhaus', 'funksjonalisme', 'modernisme', 'midtjahrhundre',
             'skandinavisk', 'nordisk funksjonalisme')
    samtid = ('postmodernisme', 'samtidsdesign')
    if any(k in s for k in samtid):
        return 'samtid'
    if any(k in s for k in e1900):
        return '1900'
    if any(k in s for k in e1800):
        return '1800'
    if any(k in s for k in e1700):
        return '1700'
    if any(k in s for k in pre1700):
        return 'pre1700'
    return 'pre1700'


EPOCH_COLOURS = {
    'pre1700': ACCENT_TEAL,
    '1700':    '#5A6B73',
    '1800':    '#8A6F3B',
    '1900':    ACCENT_RUST,
    'samtid':  '#6F3A5C',
}


def run_test():
    df = load_chairs()
    df = df.dropna(subset=MESH_COLS + ['style']).copy()
    counts = df['style'].value_counts()
    keep = counts[counts >= MIN_PER_STYLE].index
    df = df[df['style'].isin(keep)].copy()

    centroids = df.groupby('style')[MESH_COLS].mean()
    X = StandardScaler().fit_transform(centroids.values)
    Z = linkage(X, method='ward')
    return df, centroids, Z


def plot(df, centroids, Z):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.62))
    ax = fig.add_axes([0.42, 0.1, 0.55, 0.85])

    labels = list(centroids.index)
    counts = df['style'].value_counts().reindex(labels).values

    # Suppress matplotlib's default coloring; we colour leaves manually
    dendro = dendrogram(
        Z, labels=labels, orientation='right',
        color_threshold=0,
        above_threshold_color=INK_SOFT,
        leaf_font_size=6.5,
        ax=ax,
    )

    # Re-colour all branches in soft ink
    for line in ax.collections:
        line.set_color(INK_SOFT)
        line.set_linewidth(0.7)

    # Colour leaf labels by epoch
    for txt in ax.get_ymajorticklabels():
        style = txt.get_text()
        ep = epoch(style)
        txt.set_color(EPOCH_COLOURS[ep])
        txt.set_fontsize(6.4)
        # Append sample count
        n = int(df['style'].value_counts().get(style, 0))
        txt.set_text(f'{style}  ({n})')

    ax.set_xlabel('Ward-distanse  (z-skalert mesh-trekk)', fontsize=7.5)
    ax.tick_params(axis='x', labelsize=6.5)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)

    # Manual legend in upper-left
    legend_x = 0.04
    legend_y = 0.96
    fig.text(legend_x, legend_y, 'Epoke',
             fontsize=6.5, color=INK, weight='bold',
             ha='left', va='top')
    for k, (ep, lbl) in enumerate([
        ('pre1700', 'før 1700'),
        ('1700',    '1700-talet'),
        ('1800',    '1800-talet'),
        ('1900',    '1900-talet'),
        ('samtid',  'samtid'),
    ]):
        fig.text(legend_x + 0.015, legend_y - 0.025 - k * 0.022,
                 '\u2014',
                 fontsize=8.0, color=EPOCH_COLOURS[ep],
                 ha='left', va='top')
        fig.text(legend_x + 0.045, legend_y - 0.025 - k * 0.022,
                 lbl,
                 fontsize=6.0, color=INK_SOFT,
                 ha='left', va='top')

    out = FIG_DIR / 'fig-A.6.15-fylogenese.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df, centroids, Z = run_test()
    print(f'n styles = {len(centroids)}, n chairs = {len(df)}')
    out = plot(df, centroids, Z)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
