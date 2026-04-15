"""Figure 2 — Cognitive lightcone diagram.

Polar plot with 9 axes (primary axes from tab:axes in the article).
Four systems as concentric "cones": axes within their cognitive lightcone
are drawn as thick radial arms; axes outside (blind spots) are drawn as
thin dashed arms with a failure marker (x) at the perimeter.

Operationalises Proposition 7 (Finne 2026):
failure signature clusters on unrepresented axes.
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

OUT = Path(__file__).resolve().parents[2] / "writings" / "figures" / "formgjevarkompetanse"
OUT.mkdir(parents=True, exist_ok=True)

# --- Axes (order around the polar plot; short labels) ---
AXES = [
    "Mat.gr.",
    "Gramm.",
    "Koh.",
    "Komm.",
    "Industr.",
    "Antrop.",
    "3D",
    "Skala",
    "Ergon.",
]

# Competence score per system per axis (H=9, M=5, L=2). Mirrors the
# verbal diagnoses in the tex body. Scores > 6 are "inside lightcone".
SCORES = {
    "Modulor":  [9, 9, 7, 9, 3, 2, 5, 7, 2],
    "Palladio": [9, 8, 8, 6, 3, 3, 9, 8, 3],
    "Van der Laan": [9, 9, 8, 2, 2, 2, 9, 6, 2],
    "Ken/tatami": [5, 5, 9, 9, 9, 9, 7, 7, 5],
}

COLORS = {
    "Modulor": "#2171b5",
    "Palladio": "#238b45",
    "Van der Laan": "#cb181d",
    "Ken/tatami": "#6a51a3",
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica"],
    "font.size": 7,
    "axes.linewidth": 0.5,
})

N = len(AXES)
theta = np.linspace(0, 2 * np.pi, N, endpoint=False)

fig = plt.figure(figsize=(7.1, 3.6))
gs = fig.add_gridspec(1, 4, wspace=0.9)

for i, (name, scores) in enumerate(SCORES.items()):
    ax = fig.add_subplot(gs[0, i], projection="polar")
    colour = COLORS[name]

    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 5, 8])
    ax.set_yticklabels([])
    ax.set_xticks(theta)
    ax.set_xticklabels(AXES, fontsize=6.5)
    ax.tick_params(axis="x", pad=2)
    ax.grid(True, linewidth=0.3, alpha=0.4)
    ax.spines["polar"].set_linewidth(0.4)

    # Draw lightcone wedge: union of strong axes as a translucent sector.
    strong_idx = [j for j, s in enumerate(scores) if s >= 7]
    weak_idx = [j for j, s in enumerate(scores) if s < 4]

    # Radial arms — all axes
    for j, (t, s) in enumerate(zip(theta, scores)):
        if s >= 7:
            ax.plot([t, t], [0, s], color=colour, linewidth=2.2, solid_capstyle="round")
        elif s >= 4:
            ax.plot([t, t], [0, s], color=colour, linewidth=1.0, alpha=0.55)
        else:
            ax.plot([t, t], [0, 9], color=colour, linewidth=0.6, linestyle=(0, (1, 1.5)), alpha=0.5)
            # failure marker at perimeter
            ax.plot(t, 9.2, marker="x", color=colour, markersize=4.5, markeredgewidth=1.0)

    # Filled polygon for realised competence
    closed_t = np.concatenate([theta, theta[:1]])
    closed_r = np.array(scores + scores[:1])
    ax.fill(closed_t, closed_r, color=colour, alpha=0.12, linewidth=0)
    ax.plot(closed_t, closed_r, color=colour, linewidth=0.9, alpha=0.75)

    ax.set_title(name, fontsize=8, pad=8, color=colour, fontweight="bold")

# Legend — explain encoding, placed under the whole figure
legend_y = -0.08
fig.text(0.5, legend_y, (
    "Tjukk arm: innanfor lyskjegla (skår $\\geq$ 7)    "
    "Tynn arm: delvis (4-6)    "
    "Stipla + $\\times$: blindflekk ($\\leq$ 3); svikt forventa her per Proposisjon 7"
), ha="center", fontsize=6.8)

fig.suptitle("Kognitiv lyskjegle per system; urepresenterte aksar er sviktkandidatar",
             fontsize=8.5, y=1.02)

for ext in ("pdf", "png"):
    path = OUT / f"fig2_lightcone.{ext}"
    fig.savefig(path, bbox_inches="tight", dpi=600 if ext == "png" else None)
    print(f"wrote {path}")
