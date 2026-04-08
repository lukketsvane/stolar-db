"""A.6.1 — Formrommet er ikkje uniformt busett (Proposisjon 1.4 / 2.4)

Falsification test: is style period a stronger predictor of chair geometry
than material? If style period (a temporal/stylistic axis) carries more
information about (H, W, D, H/W) than material composition does, then the
morphospace is structured by style — not by what the chairs are made of.

We compute mutual information (sklearn k-NN estimator) between each
geometry dimension and (a) style period, (b) primary material. Result is
in bits per dimension. The article claims style consistently beats
material across all four dimensions; we reproduce that.

Visual: a grouped horizontal bar chart, four geometry rows, two bars each
(rust = stilperiode, soft ink = materiale). Style is wider on every row.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_selection import mutual_info_regression

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, caption_below, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL,
)

GEOM_COLS = [('h_cm', 'Høgde'), ('w_cm', 'Breidde'),
             ('d_cm', 'Djupn'),  ('hw_ratio', 'H/W')]
RNG = np.random.default_rng(2026)
N_BOOT = 200


def primary_material(s):
    if not isinstance(s, str):
        return None
    s = s.lower()
    keys = ['mahogni', 'eik', 'bøk', 'nøttetre', 'rosentre', 'palisander',
            'furu', 'plast', 'stål', 'aluminium', 'bjørk', 'tekstil', 'lær']
    for k in keys:
        if k in s:
            return k
    return None


def mi_bits(X_disc, y):
    return mutual_info_regression(
        X_disc, y, discrete_features=True, random_state=0
    )[0] / np.log(2)


def run_test(df):
    df = df.copy()
    df['mat_primary'] = df['material'].apply(primary_material)
    df = df[df['w_cm'] > 0]
    df['hw_ratio'] = df['h_cm'] / df['w_cm']
    df = df.dropna(subset=['style', 'mat_primary'] + [c for c, _ in GEOM_COLS])
    n = len(df)

    style_codes = df['style'].astype('category').cat.codes.values.reshape(-1, 1)
    mat_codes = df['mat_primary'].astype('category').cat.codes.values.reshape(-1, 1)

    rows = []
    for col, label in GEOM_COLS:
        y = df[col].values
        mi_s = mi_bits(style_codes, y)
        mi_m = mi_bits(mat_codes,   y)

        # Bootstrap CI
        boots_s, boots_m = [], []
        for _ in range(N_BOOT):
            idx = RNG.integers(0, n, n)
            try:
                boots_s.append(mi_bits(style_codes[idx], y[idx]))
                boots_m.append(mi_bits(mat_codes[idx],   y[idx]))
            except Exception:
                pass
        rows.append({
            'label':    label,
            'mi_style': mi_s,
            'mi_mat':   mi_m,
            'ci_style': (np.percentile(boots_s, 2.5),  np.percentile(boots_s, 97.5)),
            'ci_mat':   (np.percentile(boots_m, 2.5),  np.percentile(boots_m, 97.5)),
            'ratio':    mi_s / max(mi_m, 1e-9),
        })
    return rows, n, df['style'].nunique(), df['mat_primary'].nunique()


def plot(rows, n_total, n_styles, n_mats):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.95))
    ax = fig.add_axes([0.18, 0.20, 0.78, 0.62])

    n_rows = len(rows)
    y = np.arange(n_rows)[::-1]
    bar_h = 0.36

    style_vals = np.array([r['mi_style'] for r in rows])
    mat_vals   = np.array([r['mi_mat']   for r in rows])
    style_ci   = [r['ci_style'] for r in rows]
    mat_ci     = [r['ci_mat']   for r in rows]
    labels     = [r['label']    for r in rows]
    ratios     = [r['ratio']    for r in rows]

    # Bars: style above (rust), material below (soft ink)
    ax.barh(y + bar_h / 2, style_vals, height=bar_h,
            color=ACCENT_RUST, edgecolor='none',
            label='Stilperiode',  zorder=3)
    ax.barh(y - bar_h / 2, mat_vals,   height=bar_h,
            color=INK_SOFT, edgecolor='none',
            label='Materiale',    zorder=3)

    # CI ticks
    for yi, (lo, hi) in zip(y + bar_h / 2, style_ci):
        ax.hlines(yi, lo, hi, color=INK, linewidth=0.55, zorder=4)
    for yi, (lo, hi) in zip(y - bar_h / 2, mat_ci):
        ax.hlines(yi, lo, hi, color=INK, linewidth=0.55, zorder=4)

    # Ratio annotation at the right of each pair
    x_max = max(style_vals.max(), mat_vals.max())
    for yi, r in zip(y, ratios):
        ax.text(x_max * 1.02, yi, f'{r:.1f}×',
                fontsize=7.0, color=ACCENT_RUST,
                ha='left', va='center')

    # Y axis
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.5, color=INK)
    ax.tick_params(axis='y', length=0, pad=2)
    ax.set_ylim(-0.6, n_rows - 0.4)

    # X axis
    ax.set_xlim(0, x_max * 1.18)
    ax.set_xlabel('Gjensidig informasjon  (bits)', fontsize=8.0)
    ax.tick_params(axis='x', labelsize=7.5)

    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)

    # Legend below the bars
    leg = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.20),
                    fontsize=7.5, ncol=2, handletextpad=0.4,
                    columnspacing=1.4, borderaxespad=0)
    for t in leg.get_texts():
        t.set_color(INK_SOFT)

    fig.text(0.04, 0.95,
             'Stilperiode slår materiale på alle fire dimensjonar',
             fontsize=9.5, color=INK, ha='left', va='top', weight='bold')
    fig.text(0.04, 0.90,
             f'n = {n_total} stolar  ·  {n_styles} stilperiodar  ·  {n_mats} materialgrupper',
             fontsize=6.8, color=INK_SOFT, ha='left', va='top')

    fig.text(0.04, 0.025,
             'Multiplikatoren til høgre = stil/materiale-forhold; større enn 1 betyr at stilperiode forklarer meir',
             fontsize=6.5, color=INK_SOFT, ha='left')

    out = FIG_DIR / 'fig-A.6.1-uniformitet.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df = load_chairs()
    rows, n, n_styles, n_mats = run_test(df)
    print(f'n = {n}  styles = {n_styles}  materials = {n_mats}')
    for r in rows:
        print(f'  {r["label"]:<8}  stil {r["mi_style"]:.3f}  mat {r["mi_mat"]:.3f}  '
              f'×{r["ratio"]:.2f}')
    out = plot(rows, n, n_styles, n_mats)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
