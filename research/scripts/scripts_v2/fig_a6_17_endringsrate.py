"""A.6.17 — Endringsrate og episodisk diskontinuitet
(Proposisjon 4.3 — brot og stase)

Hypothesis: the rate of formal change between successive 25-year
periods is *episodic*: long stretches near the median punctuated by
clear bursts. We compute the per-period-pair Wasserstein-1 distance
in each of (Høgde, Breidde, Djupn) and aggregate to a single
"rate" R = sqrt(W_h² + W_w² + W_d²) cm per 25-year step. We test
the rate distribution for bimodality via Sarle's coefficient
BC = (γ₁² + 1) / (γ₂ + 3·(n−1)²/((n−2)(n−3))).
BC > 0.555 ⇒ likely bimodal; BC ≤ 0.555 ⇒ likely unimodal-with-tail.

Visual: a dense, three-band display.
  • Top band: stacked area of the per-dimension Wasserstein
    contributions, so you can see which dimension drove each burst.
  • Middle band: the aggregated rate as a lollipop chart with
    the two episode clusters highlighted.
  • Right inset: KDE of the rate distribution + median + BC stamp.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from scipy.stats import wasserstein_distance, skew, kurtosis, gaussian_kde

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL, ACCENT_GOLD, HIGHLIGHT, PAPER,
)

DIMS = [
    ('h_cm', 'Høgde',   ACCENT_RUST),
    ('w_cm', 'Breidde', ACCENT_TEAL),
    ('d_cm', 'Djupn',   ACCENT_GOLD),
]
START = 1500
END   = 2025
BIN_W = 25
MIN_PER_BIN = 10


def bimodality_coefficient(x: np.ndarray) -> float:
    """Sarle's bimodality coefficient.

    BC = (g1² + 1) / (g2 + 3·(n−1)²/((n−2)(n−3)))
    BC > 0.555 ⇒ probable bimodal; BC ≤ 0.555 ⇒ probable unimodal.
    """
    n = len(x)
    if n < 4:
        return float('nan')
    g1 = skew(x, bias=False)
    g2 = kurtosis(x, fisher=True, bias=False)
    correction = 3.0 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    return (g1 ** 2 + 1.0) / (g2 + correction)


def run_test():
    df = load_chairs()
    df = df.dropna(subset=['h_cm', 'w_cm', 'd_cm', 'year_mid']).copy()
    df = df[(df['h_cm'] > 0) & (df['w_cm'] > 0) & (df['d_cm'] > 0)]
    df = df[(df['year_mid'] >= START) & (df['year_mid'] <= END)]

    bins = np.arange(START, END + 1, BIN_W)
    df['bin'] = np.digitize(df['year_mid'], bins) - 1
    used = sorted(int(b) for b in df['bin'].unique())

    pair_starts: list[tuple[int, int]] = []
    per_dim: dict[str, list[float]] = {col: [] for col, _, _ in DIMS}
    n_pair: list[int] = []

    for i in range(len(used) - 1):
        a_idx, b_idx = used[i], used[i + 1]
        a = df[df['bin'] == a_idx]
        b = df[df['bin'] == b_idx]
        if len(a) < MIN_PER_BIN or len(b) < MIN_PER_BIN:
            continue
        if b_idx - a_idx != 1:
            continue
        pair_starts.append((int(bins[a_idx]), int(bins[b_idx])))
        n_pair.append(len(a) + len(b))
        for col, _, _ in DIMS:
            per_dim[col].append(wasserstein_distance(a[col].values, b[col].values))

    rates = np.sqrt(sum(np.array(per_dim[c]) ** 2 for c, _, _ in DIMS))
    bc = bimodality_coefficient(rates)
    median = float(np.median(rates))
    return pair_starts, per_dim, rates, bc, median, len(df), n_pair


def plot(pair_starts, per_dim, rates, bc, median, n_total, n_pair):
    apply_style()

    # Two-column layout: main lollipop on the left, inset KDE on the right.
    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=1.05))
    gs = fig.add_gridspec(
        2, 2,
        left=0.135, right=0.97,
        bottom=0.10, top=0.94,
        height_ratios=[1.0, 2.4],
        width_ratios=[3.4, 1.0],
        hspace=0.10, wspace=0.10,
    )

    starts = np.array([a for a, _ in pair_starts])
    n_pairs = len(rates)

    # ── Top band: per-dimension stacked sparkline ────────────────────────────
    ax_top = fig.add_subplot(gs[0, 0])
    h = np.array(per_dim['h_cm'])
    w = np.array(per_dim['w_cm'])
    d = np.array(per_dim['d_cm'])
    ax_top.fill_between(starts, 0, h,
                        color=ACCENT_RUST, alpha=0.75, linewidth=0,
                        label='Høgde')
    ax_top.fill_between(starts, h, h + w,
                        color=ACCENT_TEAL, alpha=0.75, linewidth=0,
                        label='Breidde')
    ax_top.fill_between(starts, h + w, h + w + d,
                        color=ACCENT_GOLD, alpha=0.75, linewidth=0,
                        label='Djupn')
    ax_top.set_xlim(START - 10, END + 10)
    ax_top.set_ylim(0, (h + w + d).max() * 1.10)
    ax_top.set_xticks([])
    ax_top.set_yticks([])
    for s in ('top', 'right', 'left', 'bottom'):
        ax_top.spines[s].set_visible(False)
    ax_top.text(0.0, 1.05, 'Per-dimensjon Wasserstein  (stabla)',
                transform=ax_top.transAxes,
                fontsize=6.5, color=INK_SOFT, ha='left', va='bottom')
    # Tiny inline legend at the right edge of the top band
    ax_top.text(0.995, 0.86, 'H',
                transform=ax_top.transAxes,
                fontsize=6.5, color=ACCENT_RUST, ha='right', va='top',
                weight='semibold')
    ax_top.text(0.995, 0.55, 'B',
                transform=ax_top.transAxes,
                fontsize=6.5, color=ACCENT_TEAL, ha='right', va='top',
                weight='semibold')
    ax_top.text(0.995, 0.24, 'D',
                transform=ax_top.transAxes,
                fontsize=6.5, color=ACCENT_GOLD, ha='right', va='top',
                weight='semibold')

    # ── Main lollipop: aggregated rate ───────────────────────────────────────
    ax = fig.add_subplot(gs[1, 0], sharex=ax_top)

    def is_modernist(year):
        return 1900 <= year <= 1950
    def is_baroque(year):
        return 1625 <= year <= 1675

    colors = [
        ACCENT_RUST if is_modernist(s) else (
            ACCENT_TEAL if is_baroque(s) else INK_SOFT
        )
        for s in starts
    ]

    # Faint shaded bands behind the two episode clusters
    ax.axvspan(1625, 1700, color=ACCENT_TEAL, alpha=0.06, zorder=0)
    ax.axvspan(1900, 1950, color=ACCENT_RUST, alpha=0.06, zorder=0)

    # Lollipop stems + heads
    for s, r, c in zip(starts, rates, colors):
        ax.plot([s, s], [0, r], color=c, linewidth=1.0,
                alpha=0.85, zorder=2)
        ax.plot([s], [r], 'o', color=c, markersize=4.0,
                markeredgecolor=c, zorder=3)

    # Median reference line
    ax.axhline(median, color=INK, linewidth=0.5, linestyle=':', alpha=0.7,
               zorder=1)
    ax.text(START + 5, median + 0.6,
            f'median {median:.1f}',
            fontsize=6.0, color=INK_SOFT, ha='left', va='bottom')

    # Annotate the modernist break
    rust_idx = [i for i, s in enumerate(starts) if is_modernist(s)]
    if rust_idx:
        peak_rust = rust_idx[int(np.argmax(rates[rust_idx]))]
        ax.annotate(
            'modernismens\nradiasjon',
            xy=(starts[peak_rust], rates[peak_rust]),
            xytext=(starts[peak_rust] + 25, rates[peak_rust] + 5.0),
            fontsize=6.2, color=ACCENT_RUST, ha='left', va='bottom',
            arrowprops=dict(arrowstyle='-', color=ACCENT_RUST,
                            lw=0.5, alpha=0.75,
                            connectionstyle='arc3,rad=-0.15'),
        )

    # Annotate the 17th-century break
    teal_idx = [i for i, s in enumerate(starts) if is_baroque(s)]
    if teal_idx:
        peak_teal = teal_idx[int(np.argmax(rates[teal_idx]))]
        ax.annotate(
            'barokk-stilbrot',
            xy=(starts[peak_teal], rates[peak_teal]),
            xytext=(starts[peak_teal] - 25, rates[peak_teal] + 2.5),
            fontsize=6.2, color=ACCENT_TEAL, ha='right', va='bottom',
            arrowprops=dict(arrowstyle='-', color=ACCENT_TEAL,
                            lw=0.5, alpha=0.75,
                            connectionstyle='arc3,rad=0.15'),
        )

    ax.set_xlim(START - 10, END + 10)
    ax.set_ylim(0, max(rates) * 1.30)
    ax.set_xlabel('Periode-start  (år)', fontsize=8.0)
    ax.set_ylabel('Endringsrate  (cm / 25 år)', fontsize=8.0)
    ax.set_xticks(np.arange(1500, 2026, 100))
    ax.tick_params(axis='both', labelsize=7.0)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)

    # ── Right inset: KDE of the rate distribution + BC stamp ────────────────
    ax_kde = fig.add_subplot(gs[1, 1], sharey=ax)
    kde = gaussian_kde(rates, bw_method=0.4)
    y_grid = np.linspace(0, max(rates) * 1.30, 240)
    dens = kde(y_grid)
    dens /= dens.max()  # normalised
    ax_kde.fill_betweenx(y_grid, 0, dens,
                         color=INK_SOFT, alpha=0.18, linewidth=0)
    ax_kde.plot(dens, y_grid, color=INK, linewidth=0.9)

    # Mark the two episode clusters as horizontal hatch zones at their values
    for i, c in enumerate(colors):
        if c == ACCENT_RUST or c == ACCENT_TEAL:
            ax_kde.plot([0, 1.05], [rates[i], rates[i]],
                        color=c, linewidth=0.7, alpha=0.65,
                        zorder=4)

    # Median tick
    ax_kde.axhline(median, color=INK, linewidth=0.5, linestyle=':', alpha=0.7)

    ax_kde.set_xlim(0, 1.15)
    ax_kde.set_xticks([])
    ax_kde.tick_params(axis='y', labelleft=False, length=0)
    for s in ('top', 'right', 'bottom', 'left'):
        ax_kde.spines[s].set_visible(False)

    # BC stamp directly under the KDE
    ax_kde.text(0.5, -0.04,
                f'BC\n{bc:.2f}',
                transform=ax_kde.transAxes,
                fontsize=6.6, color=INK, ha='center', va='top',
                weight='semibold', linespacing=1.05)
    ax_kde.text(0.5, -0.14,
                'unimodal\nmed hale',
                transform=ax_kde.transAxes,
                fontsize=5.6, color=INK_SOFT, ha='center', va='top',
                style='italic', linespacing=1.1)

    # KDE label at the top
    ax_kde.text(0.5, 1.01, 'tettleik',
                transform=ax_kde.transAxes,
                fontsize=6.0, color=INK_SOFT, ha='center', va='bottom',
                style='italic')

    out = FIG_DIR / 'fig-A.6.17-endringsrate.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    pair_starts, per_dim, rates, bc, median, n, n_pair = run_test()
    print(f'n_chairs = {n}, n_pairs = {len(rates)}')
    print(f'median rate = {median:.2f} cm/25yr')
    print(f'max rate    = {rates.max():.2f} cm/25yr ({pair_starts[int(np.argmax(rates))]})')
    print(f'bimodality coefficient (Sarle) = {bc:.4f}')
    order = np.argsort(rates)[::-1]
    print('top 5 rates:')
    for i in order[:5]:
        print(f'  {pair_starts[i]}  {rates[i]:.2f} cm/25yr')
    print('bottom 5 rates:')
    for i in order[-5:][::-1]:
        print(f'  {pair_starts[i]}  {rates[i]:.2f} cm/25yr')
    out = plot(pair_starts, per_dim, rates, bc, median, n, n_pair)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
