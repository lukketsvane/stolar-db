"""Van der Laan standalone diagram.

Shows the plastic number's 3D signature: three nested boxes with
sides 1 : rho : rho^2 in an axonometric projection, labelled with the
defining equation rho^3 = rho + 1.
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

OUT = Path(__file__).resolve().parents[2] / "writings" / "figures" / "formgjevarkompetanse"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica"],
    "font.size": 8,
})

rho = 1.3247

fig, ax = plt.subplots(figsize=(3.5, 2.6))
ax.set_aspect("equal")

# Axonometric offset per depth step
dx, dy = 0.22, 0.14

def draw_box(x, y, w, h, colour, alpha, linewidth=1.2, depth=0.25):
    # Front face
    ax.add_patch(Rectangle((x, y), w, h, facecolor="none",
                           edgecolor=colour, linewidth=linewidth, alpha=alpha))
    # Depth edges (axonometric)
    d = depth
    ax.plot([x, x + d], [y, y + d], color=colour, linewidth=linewidth, alpha=alpha)
    ax.plot([x + w, x + w + d], [y, y + d], color=colour, linewidth=linewidth, alpha=alpha)
    ax.plot([x + w, x + w + d], [y + h, y + h + d], color=colour, linewidth=linewidth, alpha=alpha)
    ax.plot([x, x + d], [y + h, y + h + d], color=colour, linewidth=linewidth, alpha=alpha)
    # Back face (dashed)
    ax.add_patch(Rectangle((x + d, y + d), w, h, facecolor="none",
                           edgecolor=colour, linewidth=linewidth * 0.7, alpha=alpha * 0.8,
                           linestyle=(0, (3, 2))))

colour = "#cb181d"
# Three nested boxes: 1, rho, rho^2
draw_box(0, 0, 1, 1, colour, 0.35, depth=0.15)
draw_box(0, 0, rho, rho, colour, 0.6, linewidth=1.4, depth=0.22)
draw_box(0, 0, rho ** 2, rho ** 2, colour, 0.95, linewidth=1.7, depth=0.32)

# Annotations
ax.annotate("", xy=(rho ** 2, -0.08), xytext=(0, -0.08),
            arrowprops=dict(arrowstyle="<->", color="#333", linewidth=0.8))
ax.text(rho ** 2 / 2, -0.25, r"$\rho^2$", ha="center", fontsize=9, color="#222")

ax.annotate("", xy=(-0.08, rho), xytext=(-0.08, 0),
            arrowprops=dict(arrowstyle="<->", color="#333", linewidth=0.8))
ax.text(-0.28, rho / 2, r"$\rho$", ha="center", fontsize=9, color="#222",
        rotation=90)

ax.text(rho ** 2 + 0.4, rho ** 2 / 2, r"$1 : \rho : \rho^2$",
        fontsize=10, color=colour, fontweight="bold")
ax.text(rho ** 2 + 0.4, rho ** 2 / 2 - 0.28, r"$\rho^3 = \rho + 1$",
        fontsize=8.5, color="#222")
ax.text(rho ** 2 + 0.4, rho ** 2 / 2 - 0.55, r"$\rho \approx 1{,}3247$",
        fontsize=7.5, color="#555")

ax.set_xlim(-0.5, rho ** 2 + 1.8)
ax.set_ylim(-0.45, rho ** 2 + 0.5)
ax.axis("off")

for ext in ("pdf", "png"):
    path = OUT / f"fig_vanderlaan.{ext}"
    fig.savefig(path, bbox_inches="tight", dpi=600 if ext == "png" else None)
    print(f"wrote {path}")
