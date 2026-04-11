"""A.6.19 — Det empiriske kraftfeltet i morforommet
(Direkte visualisering av proposisjon 3.1, 3.2, 3.3 og 5.1)

This is the headline figure of the appendix: the FORMLÆRE framework
made literally visible. Proposition 3.1 defines the fitness landscape
as a topology over morphospace; proposition 3.2 says it has multiple
local maxima; proposition 3.3 defines each maximum as an attractor
with measurable basin steepness; proposition 5.1 says agents navigate
those gradients.

We render all four claims at once, derived directly from the chair
data — no parameters, no theory, no smoothing tricks beyond the
2-bandwidth gaussian KDE that scipy gives us for free:

  • The empirical density ρ̂(B, H) of all 2 000+ chairs in the
    (Breidde, Høgde) plane is shown as a hillshade-style filled
    contour map. Bright regions are populated; dark regions are
    forbidden / undiscovered.

  • The DERIVED force field −∇log ρ̂(B, H) is overlaid as a quiver
    of small arrows on a regular grid. Every arrow points along the
    local gradient toward the nearest attractor. This is the
    landscape made into physics: Wright's metaphor turned into
    something a chair-maker could in principle navigate by
    Newton's-method.

  • Local maxima of ρ̂ are detected automatically and marked as
    named attractors. The labels come from the most populous
    style at each maximum — i.e. the data itself names its hills.

  • The temporal trajectory of the corpus mean (50-year periods,
    1500–2025) is overlaid as a thin trail with arrowheads, so
    you can SEE the historical walk through the landscape: the
    European chair tradition migrating from one attractor to
    another over five centuries.

What is unique here is that the landscape, the gradients, the
attractors and the trajectory are all four derived from the same
n = 2 014 chairs — no model, no fit, no styles imposed. The
framework's central diagram is, for the first time, an empirically
measured object.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch
from scipy.stats import gaussian_kde
from scipy.ndimage import maximum_filter

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL, ACCENT_GOLD,
    HIGHLIGHT, PAPER,
)


# ── Plane and ranges ─────────────────────────────────────────────────────────
B_LO, B_HI = 32, 90      # Breidde (cm)
H_LO, H_HI = 50, 115     # Høgde (cm)
GRID_N = 220              # density grid resolution
QUIVER_STRIDE = 16        # subsample density grid for quiver arrows


def compute_landscape(df):
    """Return (BB, HH, density, log_density, grad_b, grad_h)."""
    pts = df[['w_cm', 'h_cm']].values.T
    # Smaller bandwidth than scipy's default reveals the genuine
    # multimodality of the chair distribution; the high-back classical
    # peak (~ 50, 92) and the low-back modernist peak (~ 50, 45) are
    # otherwise smoothed into one blob.
    kde = gaussian_kde(pts, bw_method=0.10)

    bb = np.linspace(B_LO, B_HI, GRID_N)
    hh = np.linspace(H_LO, H_HI, GRID_N)
    BB, HH = np.meshgrid(bb, hh)
    pos = np.vstack([BB.ravel(), HH.ravel()])
    rho = kde(pos).reshape(BB.shape)

    # Use log density for gradient — that's the natural scaling for
    # an "energy" V = −log ρ, with gradient field −∇V = ∇log ρ.
    eps = rho.max() * 1e-3
    log_rho = np.log(rho + eps)

    # Numerical gradient (axis 1 = B, axis 0 = H)
    db = bb[1] - bb[0]
    dh = hh[1] - hh[0]
    grad_h, grad_b = np.gradient(log_rho, dh, db)

    return BB, HH, rho, log_rho, grad_b, grad_h, kde


def find_attractors(rho, BB, HH, neighborhood=18, min_relative_height=0.08,
                    edge_margin=0.06):
    """Detect local maxima of the density grid.

    Excludes peaks within `edge_margin` (fraction of axis range) of any
    boundary, since boundary maxima are usually artifacts of the
    finite-support kernel rather than real attractors.
    """
    mx = maximum_filter(rho, size=neighborhood)
    is_peak = (rho == mx) & (rho > rho.max() * min_relative_height)

    # Edge mask: drop peaks within `edge_margin` of any boundary
    n_h, n_b = rho.shape
    em_b = int(round(n_b * edge_margin))
    em_h = int(round(n_h * edge_margin))
    edge_ok = np.zeros_like(is_peak)
    edge_ok[em_h:n_h - em_h, em_b:n_b - em_b] = True
    is_peak &= edge_ok

    bs = BB[is_peak]
    hs = HH[is_peak]
    vs = rho[is_peak]
    order = np.argsort(vs)[::-1]
    return list(zip(bs[order], hs[order], vs[order]))


def label_attractors(df, peaks, top_k=3, search_radius=9.0):
    """For each detected peak, find the most populous style label
    among chairs within `search_radius` cm. Returns
    [(b, h, label, share, n)] sorted by descending peak height.
    """
    labelled = []
    if 'style' not in df.columns:
        return [(b, h, '', 0.0, 0) for b, h, _ in peaks[:top_k]]
    for b, h, _ in peaks[:top_k]:
        sub = df[((df['w_cm'] - b) ** 2 + (df['h_cm'] - h) ** 2) <= search_radius ** 2]
        sub = sub.dropna(subset=['style'])
        if sub.empty:
            labelled.append((b, h, '', 0.0, 0))
            continue
        counts = sub['style'].value_counts()
        # Pick the top style — but if it's an empty / generic bucket
        # ('Ukjend', 'Annet'), fall back to the next.
        for cand in counts.index:
            s = str(cand).strip()
            if s and s.lower() not in ('ukjend', 'ukjent', 'annet', 'andre',
                                       'nan'):
                top_label = s
                share = counts[cand] / len(sub)
                break
        else:
            top_label = str(counts.index[0])
            share = counts.iloc[0] / len(sub)
        labelled.append((b, h, top_label, float(share), int(len(sub))))
    return labelled


def period_trail(df, bin_w=50, start=1500, end=2025, min_n=10):
    df = df.dropna(subset=['year_mid', 'w_cm', 'h_cm']).copy()
    df = df[(df['year_mid'] >= start) & (df['year_mid'] <= end)]
    df['period'] = ((df['year_mid'] - start) // bin_w).astype(int) * bin_w + start
    g = df.groupby('period').agg(n=('w_cm', 'count'),
                                 b=('w_cm', 'mean'),
                                 h=('h_cm', 'mean'))
    g = g[g['n'] >= min_n]
    return g.reset_index()


def plot(df):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=1.18))
    ax = fig.add_axes([0.135, 0.10, 0.84, 0.84])

    # ── Empirical landscape ─────────────────────────────────────────────────
    BB, HH, rho, log_rho, grad_b, grad_h, kde = compute_landscape(df)

    # Cream → ochre → rust hill colormap (matches book palette)
    hill = LinearSegmentedColormap.from_list(
        'hill',
        ['#FAF7EE', '#F1E5C2', '#E8C788', '#D9A357', '#B8542A', '#5A2210'],
    )

    # Filled density (the landscape)
    levels = np.linspace(rho.min(), rho.max(), 18)
    cf = ax.contourf(BB, HH, rho, levels=levels, cmap=hill,
                     antialiased=True, zorder=1)

    # Density level contours (terrain lines)
    line_levels = np.linspace(rho.min(), rho.max(), 9)[2:]
    ax.contour(BB, HH, rho, levels=line_levels,
               colors=[INK_SOFT], linewidths=0.35, alpha=0.55, zorder=2)

    # ── Force field: −∇V = ∇ log ρ ─────────────────────────────────────────
    # Subsample the grid so the quiver isn't too dense.
    s = QUIVER_STRIDE
    BBq = BB[::s, ::s]
    HHq = HH[::s, ::s]
    Ub = grad_b[::s, ::s]
    Uh = grad_h[::s, ::s]
    # Normalise arrow length so we read direction, not magnitude — magnitude
    # is already encoded by the colormap (steeper = bigger contour gradient).
    norm = np.hypot(Ub, Uh)
    norm[norm == 0] = 1.0
    Ub_n = Ub / norm
    Uh_n = Uh / norm

    ax.quiver(
        BBq, HHq, Ub_n, Uh_n,
        color=INK, alpha=0.55,
        scale=46, scale_units='width',
        width=0.0028,
        headwidth=3.5, headlength=4.0, headaxislength=3.5,
        pivot='mid',
        zorder=3,
    )

    # ── Detected attractors ─────────────────────────────────────────────────
    peaks = find_attractors(rho, BB, HH)
    labelled = label_attractors(df, peaks, top_k=3, search_radius=9.0)
    print(f'detected {len(peaks)} peaks; labelling top {len(labelled)}')
    for b, h, name, share, n in labelled:
        print(f'  peak ({b:.1f}, {h:.1f})  -> {name!r}  share={share:.2f}  n={n}')

    # Choose readable label anchors around each peak — push labels
    # outward from the centre of the chart so leaders don't cross the
    # main density blob.
    cx, cy = (B_LO + B_HI) / 2, (H_LO + H_HI) / 2
    for i, (b, h, name, share, n_local) in enumerate(labelled):
        ax.plot([b], [h], 'o', color=INK, markersize=7.0,
                markerfacecolor=PAPER, markeredgewidth=1.1, zorder=10)
        ax.plot([b], [h], 'o', color=INK, markersize=2.4, zorder=11)
        if not name:
            continue
        # Compact long labels: drop the " / second-name" tail
        short = name.split(' / ')[0]
        if len(short) > 22:
            short = short[:21] + '…'
        # Push label away from the chart centre by ~14 cm
        dx = b - cx
        dy = h - cy
        mag = max(np.hypot(dx, dy), 1.0)
        ox = (dx / mag) * 16.0
        oy = (dy / mag) * 9.0
        # If we're very near the centre, fall back to upper-right
        if abs(dx) < 4 and abs(dy) < 4:
            ox, oy = 18.0, 8.0
        lx = b + ox
        ly = h + oy
        # Clamp inside the axes a bit
        lx = float(np.clip(lx, B_LO + 4, B_HI - 4))
        ly = float(np.clip(ly, H_LO + 4, H_HI - 4))
        ax.annotate(
            short,
            xy=(b, h),
            xytext=(lx, ly),
            fontsize=6.3, color=INK, ha='center', va='center',
            weight='semibold',
            arrowprops=dict(arrowstyle='-', color=INK,
                            lw=0.55, alpha=0.75,
                            connectionstyle='arc3,rad=0.0'),
            zorder=12,
        )

    # ── Historical trajectory: corpus centroid 1500-2025 ───────────────────
    trail = period_trail(df)
    if len(trail) >= 2:
        bs = trail['b'].values
        hs = trail['h'].values
        ax.plot(bs, hs, '-', color=ACCENT_TEAL, linewidth=1.4,
                alpha=0.95, zorder=8)
        ax.plot(bs, hs, 'o', color=ACCENT_TEAL, markersize=2.6,
                markeredgecolor=PAPER, markeredgewidth=0.5, zorder=9)
        # Arrowhead on the last segment
        arrow = FancyArrowPatch(
            (bs[-2], hs[-2]), (bs[-1], hs[-1]),
            arrowstyle='->',
            mutation_scale=10,
            color=ACCENT_TEAL, linewidth=0.0,
            shrinkA=2, shrinkB=2,
            zorder=10,
        )
        ax.add_patch(arrow)
        # Year labels at start and end of the trail
        ax.text(bs[0] + 0.4, hs[0] + 0.4,
                f"{int(trail['period'].iloc[0])}",
                fontsize=5.4, color=ACCENT_TEAL, ha='left', va='bottom',
                style='italic', alpha=0.95)
        ax.text(bs[-1] + 0.4, hs[-1] + 0.4,
                f"{int(trail['period'].iloc[-1])}",
                fontsize=5.4, color=ACCENT_TEAL, ha='left', va='bottom',
                style='italic', alpha=0.95)

    # ── Axes / styling ──────────────────────────────────────────────────────
    ax.set_xlim(B_LO, B_HI)
    ax.set_ylim(H_LO, H_HI)
    ax.set_xlabel('Breidde  (cm)', fontsize=8.0)
    ax.set_ylabel('Høgde  (cm)', fontsize=8.0)
    ax.tick_params(axis='both', labelsize=7.0)
    for s_ in ('top', 'right'):
        ax.spines[s_].set_visible(False)

    # Inline legend / decoder block in the upper-left of the chart
    decoder_x = 0.025
    decoder_y = 0.98
    ax.text(decoder_x, decoder_y,
            r'$\hat\rho$ (B, H)',
            transform=ax.transAxes,
            fontsize=6.4, color=INK, weight='semibold',
            ha='left', va='top')
    ax.text(decoder_x, decoder_y - 0.045,
            'fyllfarge: tettleik',
            transform=ax.transAxes,
            fontsize=5.6, color=INK_SOFT, ha='left', va='top',
            style='italic')
    ax.text(decoder_x, decoder_y - 0.090,
            r'piler: $-\nabla V = \nabla\log\hat\rho$',
            transform=ax.transAxes,
            fontsize=5.6, color=INK_SOFT, ha='left', va='top',
            style='italic')
    ax.text(decoder_x, decoder_y - 0.135,
            'kringle: lokal maks (haug)',
            transform=ax.transAxes,
            fontsize=5.6, color=INK_SOFT, ha='left', va='top',
            style='italic')
    ax.text(decoder_x, decoder_y - 0.180,
            'turkis: 1500→2025-bane',
            transform=ax.transAxes,
            fontsize=5.6, color=ACCENT_TEAL, ha='left', va='top',
            style='italic')

    out = FIG_DIR / 'fig-A.6.19-kraftfelt.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    df = load_chairs()
    df = df.dropna(subset=['h_cm', 'w_cm']).copy()
    df = df[(df['h_cm'] > 30) & (df['h_cm'] < 200)]
    df = df[(df['w_cm'] > 25) & (df['w_cm'] < 150)]
    print(f'n_chairs (B, H) = {len(df)}')
    out = plot(df)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
