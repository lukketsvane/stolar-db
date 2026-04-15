"""Figure 1 — System montage (2x2).

Compresses the four historical examples into a single single-column figure:
  A. Modulor (real image)
  B. Palladio villa plan (real image)
  C. Van der Laan plastic-number diagram (generated)
  D. Ken/tatami perspective (real image)
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.image import imread
from matplotlib.patches import Rectangle

REPO = Path(__file__).resolve().parents[2]
FIG_DIR = REPO / "writings" / "figures" / "formgjevarkompetanse"
OUT = FIG_DIR

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica"],
    "font.size": 7,
})

img_modulor = imread(FIG_DIR / "figur_1-le-corbusier.png")
img_palladio = imread(FIG_DIR / "figur_2a-palladio-villa-plan.png")
img_ken = imread(FIG_DIR / "figur_4a-ken-modul-perspektiv.png")

fig = plt.figure(figsize=(3.5, 3.2))
gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.15,
                      left=0.02, right=0.98, top=0.93, bottom=0.04)

# --- Panel A: Modulor ---
axA = fig.add_subplot(gs[0, 0])
axA.imshow(img_modulor)
axA.set_xticks([]); axA.set_yticks([])
for s in axA.spines.values():
    s.set_linewidth(0.5)
axA.set_title("A  Modulor (Le Corbusier, 1948)",
              fontsize=6.8, loc="left", pad=2, fontweight="bold")

# --- Panel B: Palladio villa plan ---
axB = fig.add_subplot(gs[0, 1])
axB.imshow(img_palladio)
axB.set_xticks([]); axB.set_yticks([])
for s in axB.spines.values():
    s.set_linewidth(0.5)
axB.set_title("B  Palladio-villa (~1570)",
              fontsize=6.8, loc="left", pad=2, fontweight="bold")

# --- Panel C: Van der Laan (generated diagram) ---
axC = fig.add_subplot(gs[1, 0])
axC.set_aspect("equal")
rho = 1.3247  # plastic number
# Three nested rectangles with sides 1 : rho : rho^2
widths = [1.0, rho, rho ** 2]
heights = [1.0, rho, rho ** 2]
colours = ["#cb181d", "#cb181d", "#cb181d"]
alphas = [0.25, 0.45, 0.70]
for w, h, c, a in zip(widths, heights, colours, alphas):
    rect = Rectangle((0, 0), w, h, facecolor="none",
                     edgecolor=c, linewidth=1.3, alpha=a)
    axC.add_patch(rect)
# Label the plastic number
axC.text(rho ** 2 / 2, -0.28, r"$1 : \rho : \rho^2$",
         ha="center", fontsize=7.5, color="#cb181d")
axC.text(0.05, rho ** 2 - 0.15, r"$\rho^3 = \rho + 1$",
         fontsize=6.8, color="#222222")
axC.set_xlim(-0.15, rho ** 2 + 0.15)
axC.set_ylim(-0.45, rho ** 2 + 0.15)
axC.set_xticks([]); axC.set_yticks([])
for s in axC.spines.values():
    s.set_linewidth(0.5)
axC.set_title("C  Van der Laan, plastisk tal (~1960)",
              fontsize=6.8, loc="left", pad=2, fontweight="bold")

# --- Panel D: Ken/tatami ---
axD = fig.add_subplot(gs[1, 1])
axD.imshow(img_ken)
axD.set_xticks([]); axD.set_yticks([])
for s in axD.spines.values():
    s.set_linewidth(0.5)
axD.set_title("D  Ken/tatami (Japan, ~10. hundreåret)",
              fontsize=6.8, loc="left", pad=2, fontweight="bold")

for ext in ("pdf", "png"):
    path = OUT / f"fig1_montage.{ext}"
    fig.savefig(path, bbox_inches="tight", dpi=600 if ext == "png" else None)
    print(f"wrote {path}")
