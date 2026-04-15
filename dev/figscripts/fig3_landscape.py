"""Figure 3 — Contour fitness landscape with vacant plateau.

Two-dimensional projection (grammatical elegance x industrial integration).
Contour-filled surface with:
  - Four named local maxima (Modulor, Palladio, VdL, Ken/tatami)
  - A dashed outline marking the vacant plateau in C \\ K (top-right region)
  - A candidate marker (Neufert?) inside the plateau
  - An arrow from Modulor and from Palladio pointing toward the plateau

Visualises CK's K/C partition: filled contours = adaptive peaks;
dashed region = thinkable-but-unrealised; question-marked candidate is
the predictive case.
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter  # type: ignore

OUT = Path(__file__).resolve().parents[2] / "writings" / "figures" / "formgjevarkompetanse"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica"],
    "font.size": 8,
    "axes.linewidth": 0.6,
})

# System coordinates in (elegance, integration) with a proxy "height"
SYSTEMS = [
    # name, x (eleganse 0-10), y (integrasjon 0-10), h (lokalmaks), colour
    ("Modulor",      7.7, 2.8, 7.2, "#2171b5"),
    ("Palladio",     8.2, 3.7, 7.5, "#238b45"),
    ("Van der Laan", 9.0, 1.5, 6.8, "#cb181d"),
    ("Ken/tatami",   4.8, 8.2, 7.0, "#6a51a3"),
]

# Build a smooth landscape as a sum of 2D Gaussians
x = np.linspace(0, 10, 240)
y = np.linspace(0, 10, 240)
X, Y = np.meshgrid(x, y)
Z = np.zeros_like(X)
for _, cx, cy, h, _ in SYSTEMS:
    Z += h * np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / 1.6)

# Add a subtle baseline tilt + noise to break symmetry
Z += 0.35 * (X / 10) + 0.25 * (Y / 10)
rng = np.random.default_rng(7)
Z += 0.15 * gaussian_filter(rng.standard_normal(Z.shape), sigma=4)

# Colormap: viridis-like but softer; emphasise low vs high
cmap = plt.get_cmap("viridis")

fig, ax = plt.subplots(figsize=(7.0, 4.0))

levels = np.linspace(Z.min(), Z.max(), 14)
cf = ax.contourf(X, Y, Z, levels=levels, cmap=cmap, alpha=0.9)
ax.contour(X, Y, Z, levels=levels, colors="white", linewidths=0.3, alpha=0.55)

# Colourbar for height (tilpassing)
cbar = fig.colorbar(cf, ax=ax, shrink=0.85, pad=0.02)
cbar.set_label(r"Tilpassing $\mathcal{L}(c,t)$", fontsize=7.5)
cbar.ax.tick_params(labelsize=6.5)

# --- Vacant plateau outline (C \ K) in the top-right region ---
plateau_pts = np.array([
    [7.6, 7.0], [9.6, 7.2], [9.8, 9.5], [7.8, 9.5], [7.6, 7.0]
])
ax.plot(plateau_pts[:, 0], plateau_pts[:, 1],
        linestyle=(0, (4, 3)), color="white", linewidth=1.8)
ax.plot(plateau_pts[:, 0], plateau_pts[:, 1],
        linestyle=(0, (4, 3)), color="#222222", linewidth=1.0)
ax.text(8.7, 9.75, r"$C \setminus K$: ledig høgplatå",
        ha="center", fontsize=7.2, color="#222222",
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))

# Neufert candidate inside plateau
ax.text(8.3, 8.6, "?", fontsize=22, color="#222222", ha="center", va="center",
        fontweight="bold", alpha=0.55)
ax.text(9.05, 8.5, "Neufert?\nHabraken?", fontsize=6.4, ha="left",
        color="#222222", va="center",
        bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#888888",
                  linewidth=0.5, alpha=0.95))

# --- System markers and labels ---
for name, cx, cy, h, colour in SYSTEMS:
    ax.plot(cx, cy, marker="o", markersize=8.5, markerfacecolor=colour,
            markeredgecolor="white", markeredgewidth=1.2, zorder=5)
    offset_x, offset_y = {
        "Modulor": (-1.4, -0.7),
        "Palladio": (-0.2, 1.0),
        "Van der Laan": (-1.6, 0.4),
        "Ken/tatami": (0.0, -1.1),
    }[name]
    ax.annotate(name, xy=(cx, cy), xytext=(cx + offset_x, cy + offset_y),
                fontsize=7.5, color=colour, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white",
                          ec=colour, linewidth=0.5, alpha=0.9),
                zorder=6)

# --- Arrows: from Modulor and Palladio toward the plateau ---
for src in ["Modulor", "Palladio"]:
    sx, sy = next((cx, cy) for (n, cx, cy, _, _) in SYSTEMS if n == src)
    arrow = FancyArrowPatch((sx, sy), (8.3, 7.8),
                            arrowstyle="->,head_width=3.0,head_length=4.0",
                            color="white", linewidth=1.6, alpha=0.9,
                            linestyle=(0, (3, 2.5)), mutation_scale=10, zorder=4)
    ax.add_patch(arrow)
    arrow2 = FancyArrowPatch((sx, sy), (8.3, 7.8),
                             arrowstyle="->,head_width=3.0,head_length=4.0",
                             color="#333333", linewidth=0.7, alpha=0.85,
                             linestyle=(0, (3, 2.5)), mutation_scale=10, zorder=5)
    ax.add_patch(arrow2)

# Label on arrow
ax.text(6.4, 5.6, "tenkeleg\ntrajektorie",
        fontsize=6.4, color="#222222", alpha=0.95, style="italic", ha="center",
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))

# Axes and cosmetics
ax.set_xlabel("Grammatisk eleganse / minimalisme $\\rightarrow$")
ax.set_ylabel("Industriell integrasjonsdjupn $\\rightarrow$")
ax.set_xlim(0.5, 10)
ax.set_ylim(0.5, 10)
ax.set_xticks([])
ax.set_yticks([])

ax.set_title(r"Tilpassingslandskapet: fire lokale maksima og ledig høgplatå i $C \setminus K$",
             fontsize=9, pad=6)

for ext in ("pdf", "png"):
    path = OUT / f"fig3_landscape.{ext}"
    fig.savefig(path, bbox_inches="tight", dpi=600 if ext == "png" else None)
    print(f"wrote {path}")
