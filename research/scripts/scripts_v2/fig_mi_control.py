"""Random-aggregate MI control test.

Tests whether the MI(style, form) > MI(material, form) asymmetry
is due to style carrying genuine morphological information or merely
to style having higher cardinality (25 categories vs ~13 for material).

Method: construct 1000 random groupings of chairs into 25 categories
(same cardinality as style), compute MI(random_group, dimension) for
each, and compare the distribution against observed MI(style, dimension).

If MI(style) >> MI(random), style carries real information.
If MI(style) ~ MI(random), the asymmetry is an artifact of cardinality.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression
from style import apply_style, load_chairs, FIG_DIR
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

apply_style()

# ── Load data ────────────────────────────────────────────────────────────────
df = load_chairs()
df = df.dropna(subset=['h_cm', 'w_cm', 'd_cm', 'style'])
df = df[df['w_cm'] > 0].copy()
df['hw_ratio'] = df['h_cm'] / df['w_cm']

dims = ['h_cm', 'w_cm', 'd_cm', 'hw_ratio']
dim_labels = ['H', 'W', 'D', 'H/W']

# ── Observed MI(style, dim) ──────────────────────────────────────────────────
style_codes = df['style'].astype('category').cat.codes.values.reshape(-1, 1)
n_styles = len(df['style'].astype('category').cat.categories)

mi_style = {}
for d in dims:
    y = df[d].values
    mi = mutual_info_regression(style_codes, y, discrete_features=True,
                                random_state=0)[0]
    mi_style[d] = mi / np.log(2)  # nats -> bits

print(f"Number of style categories: {n_styles}")
print(f"Number of chairs: {len(df)}")
print()
for d, lab in zip(dims, dim_labels):
    print(f"  MI(style, {lab}) = {mi_style[d]:.4f} bits")

# ── Random-aggregate null distribution ───────────────────────────────────────
N_PERM = 1000
rng = np.random.default_rng(2026)

mi_random = {d: [] for d in dims}

for i in range(N_PERM):
    # Assign each chair to one of n_styles random groups
    random_labels = rng.integers(0, n_styles, size=len(df)).reshape(-1, 1)
    for d in dims:
        y = df[d].values
        mi = mutual_info_regression(random_labels, y, discrete_features=True,
                                    random_state=0)[0]
        mi_random[d].append(mi / np.log(2))

# ── Results ──────────────────────────────────────────────────────────────────
print()
print("Random-aggregate null (1000 permutations):")
for d, lab in zip(dims, dim_labels):
    null_arr = np.array(mi_random[d])
    p_val = np.mean(null_arr >= mi_style[d])
    print(f"  {lab}: observed={mi_style[d]:.4f}, "
          f"null mean={null_arr.mean():.4f}, "
          f"null 95th={np.percentile(null_arr, 95):.4f}, "
          f"p={p_val:.4f}")

# ── Figure ───────────────────────────────────────────────────────────────────
from style import INK, INK_SOFT, ACCENT_RUST, ACCENT_TEAL, PAPER, RULE

fig, axes = plt.subplots(1, 4, figsize=(10, 2.8), sharey=False)
fig.patch.set_facecolor(PAPER)

for ax, d, lab in zip(axes, dims, dim_labels):
    null_arr = np.array(mi_random[d])
    ax.hist(null_arr, bins=30, color=ACCENT_TEAL, alpha=0.5, edgecolor='none',
            label='Random aggregate')
    ax.axvline(mi_style[d], color=ACCENT_RUST, linewidth=2, linestyle='-',
               label=f'Style ({mi_style[d]:.3f})')
    ax.set_xlabel('MI (bits)', fontsize=8)
    ax.set_title(lab, fontsize=9, fontweight='bold')
    ax.set_facecolor(PAPER)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(labelsize=7)

axes[0].set_ylabel('Count', fontsize=8)
axes[-1].legend(fontsize=7, frameon=False)
fig.suptitle('MI control: observed style vs. random aggregate (same cardinality)',
             fontsize=10, fontweight='bold', y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.93])

out = FIG_DIR / 'fig-mi-control.pdf'
fig.savefig(out, dpi=320, bbox_inches='tight')
fig.savefig(out.with_suffix('.png'), dpi=320, bbox_inches='tight')
plt.close(fig)
print(f"\nwrote {out}")
