"""
FORMLÆRE: MATHEMATICA — Figurgenererering
Genererer 10 diagram som illustrerer dei sentrale konsepta.
Iver Raknes Finne, AHO 2026
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib import patheffects
from scipy.ndimage import gaussian_filter
from mpl_toolkits.mplot3d import Axes3D
import os

OUT = os.path.join(os.path.dirname(__file__), "fig")
os.makedirs(OUT, exist_ok=True)

# --- Felles stil ---
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
    "text.usetex": False,
    "mathtext.fontset": "cm",
})

COLORS = {
    "busett": "#2D6A4F",
    "open": "#D4A373",
    "forboden": "#E5E5E5",
    "accent1": "#264653",
    "accent2": "#E76F51",
    "accent3": "#2A9D8F",
    "accent4": "#E9C46A",
    "accent5": "#F4A261",
    "dark": "#1D3557",
    "mid": "#457B9D",
    "light": "#A8DADC",
    "bg": "#FAFAFA",
}


# ============================================================
# FIG 1: FORMROM MED REGIONAR (B, O, F)
# ============================================================
def fig1_formrom():
    fig, ax = plt.subplots(1, 1, figsize=(7, 6))
    ax.set_facecolor(COLORS["forboden"])

    # M_C boundary (formrom) — irregular blob
    t = np.linspace(0, 2 * np.pi, 300)
    r = 2.2 + 0.4 * np.sin(3*t) + 0.3 * np.cos(5*t) + 0.2 * np.sin(7*t)
    cx, cy = 0.0, 0.0
    bx = cx + r * np.cos(t)
    by = cy + r * np.sin(t)

    # Fill M_C as open region
    ax.fill(bx, by, color=COLORS["open"], alpha=0.6, zorder=1)
    ax.plot(bx, by, color=COLORS["accent1"], lw=2, zorder=3)

    # Busett region — clustered points with density shading
    np.random.seed(42)
    # Cluster 1
    c1x, c1y = -0.8, 0.5
    pts1 = np.random.randn(60, 2) * 0.4 + [c1x, c1y]
    # Cluster 2
    c2x, c2y = 0.9, -0.3
    pts2 = np.random.randn(45, 2) * 0.35 + [c2x, c2y]
    # Cluster 3
    c3x, c3y = -0.2, -1.0
    pts3 = np.random.randn(30, 2) * 0.3 + [c3x, c3y]
    # Cluster 4 (sparse)
    c4x, c4y = 1.2, 1.0
    pts4 = np.random.randn(15, 2) * 0.25 + [c4x, c4y]

    all_pts = np.vstack([pts1, pts2, pts3, pts4])

    # Draw occupied region as green shading
    from scipy.ndimage import gaussian_filter
    xg = np.linspace(-3, 3, 200)
    yg = np.linspace(-3, 3, 200)
    Xg, Yg = np.meshgrid(xg, yg)
    density = np.zeros_like(Xg)
    for p in all_pts:
        density += np.exp(-((Xg - p[0])**2 + (Yg - p[1])**2) / 0.15)
    density = gaussian_filter(density, sigma=3)

    # Clip to M_C
    from matplotlib.path import Path
    mc_path = Path(np.column_stack([bx, by]))
    points_flat = np.column_stack([Xg.ravel(), Yg.ravel()])
    mask = mc_path.contains_points(points_flat).reshape(Xg.shape)
    density_masked = np.where(mask, density, np.nan)

    ax.contourf(Xg, Yg, density_masked, levels=8, cmap="Greens", alpha=0.5, zorder=2)

    # Individual chairs as points
    ax.scatter(all_pts[:, 0], all_pts[:, 1], s=8, c=COLORS["busett"],
               alpha=0.7, zorder=4, edgecolors="none")

    # Labels
    ax.annotate(r"$B$ (busett)", xy=(c1x, c1y + 0.7), fontsize=11,
                color=COLORS["busett"], fontweight="bold", ha="center", zorder=5)
    ax.annotate(r"$O$ (open)", xy=(1.8, 1.5), fontsize=11,
                color=COLORS["accent5"], fontweight="bold", ha="center", zorder=5)
    ax.annotate(r"$F$ (forboden)", xy=(-2.5, 2.5), fontsize=11,
                color="#888", fontweight="bold", ha="center", zorder=5)
    ax.annotate(r"$\mathbf{M}_C$", xy=(2.0, -1.8), fontsize=14,
                color=COLORS["accent1"], fontweight="bold", ha="center", zorder=5)
    ax.annotate(r"$\partial \mathbf{M}_C(\tau)$", xy=(2.3, 0.3), fontsize=10,
                color=COLORS["accent1"], ha="center", zorder=5,
                fontstyle="italic")

    # Technology arrow expanding boundary
    ax.annotate("", xy=(2.6, -0.5), xytext=(2.1, -0.2),
                arrowprops=dict(arrowstyle="->", color=COLORS["accent2"], lw=1.5),
                zorder=5)
    ax.text(2.85, -0.5, r"$\tau \uparrow$", fontsize=10, color=COLORS["accent2"],
            ha="center", va="center")

    ax.set_xlim(-3.2, 3.5)
    ax.set_ylim(-3, 3.2)
    ax.set_xlabel(r"$x_1$ (t.d. høgd)")
    ax.set_ylabel(r"$x_2$ (t.d. breidd)")
    ax.set_title("I. Formrommet $\\mathbf{M}_C$ med regionar $B$, $O$, $F$")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.2)

    fig.savefig(os.path.join(OUT, "fig1_formrom.pdf"))
    fig.savefig(os.path.join(OUT, "fig1_formrom.png"))
    plt.close(fig)
    print("  fig1_formrom OK")


# ============================================================
# FIG 2: MOTSTRIDANDE SELEKSJONSTRYKK (VEKTORFELT)
# ============================================================
def fig2_seleksjonstrykk():
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    x = np.linspace(-2, 2, 20)
    y = np.linspace(-2, 2, 20)
    X, Y = np.meshgrid(x, y)

    # s1: material affordance — pulls toward origin
    U1 = -X * 0.5
    V1 = -Y * 0.3 + 0.2

    # s2: cultural pressure — pulls toward upper-right
    U2 = 0.3 * np.ones_like(X)
    V2 = 0.4 * np.ones_like(Y) - 0.1 * Y

    # Combined
    U3 = U1 + U2
    V3 = V1 + V2

    for ax in axes:
        ax.set_xlim(-2.2, 2.2)
        ax.set_ylim(-2.2, 2.2)
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.15)

    # Panel 1: s_1
    M1 = np.sqrt(U1**2 + V1**2)
    axes[0].quiver(X, Y, U1, V1, M1, cmap="YlGn", alpha=0.8, scale=12)
    axes[0].set_title(r"$s_1$: materiell affordanse", fontsize=10)
    axes[0].set_xlabel(r"$x_1$")
    axes[0].set_ylabel(r"$x_2$")

    # Panel 2: s_2
    M2 = np.sqrt(U2**2 + V2**2)
    axes[1].quiver(X, Y, U2, V2, M2, cmap="OrRd", alpha=0.8, scale=12)
    axes[1].set_title(r"$s_2$: kulturell aksept", fontsize=10)
    axes[1].set_xlabel(r"$x_1$")

    # Panel 3: combined — show conflict region
    M3 = np.sqrt(U3**2 + V3**2)
    axes[2].quiver(X, Y, U3, V3, M3, cmap="PuBu", alpha=0.8, scale=12)
    # Mark conflict zone where gradients oppose
    dot = U1*U2 + V1*V2
    conflict = dot < 0
    axes[2].contourf(X, Y, dot, levels=[-10, 0], colors=[COLORS["accent2"]],
                     alpha=0.15, zorder=0)
    axes[2].contour(X, Y, dot, levels=[0], colors=[COLORS["accent2"]],
                    linewidths=1.5, linestyles="--", zorder=1)
    axes[2].set_title(r"$\nabla s_1 \cdot \nabla s_2 < 0$ (skravert)", fontsize=10)
    axes[2].set_xlabel(r"$x_1$")

    # Compromise point
    # Find where U3, V3 are smallest
    mag = np.sqrt(U3**2 + V3**2)
    idx = np.unravel_index(np.argmin(mag), mag.shape)
    cx, cy = X[idx], Y[idx]
    axes[2].plot(cx, cy, "o", color=COLORS["accent2"], ms=10, zorder=5)
    axes[2].annotate("kompromiss", xy=(cx, cy), xytext=(cx+0.5, cy-0.6),
                     fontsize=9, color=COLORS["accent2"], fontweight="bold",
                     arrowprops=dict(arrowstyle="->", color=COLORS["accent2"]))

    fig.suptitle("II. Motstridande seleksjonstrykk og kompromiss", fontsize=12,
                 fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2_seleksjonstrykk.pdf"))
    fig.savefig(os.path.join(OUT, "fig2_seleksjonstrykk.png"))
    plt.close(fig)
    print("  fig2_seleksjonstrykk OK")


# ============================================================
# FIG 3: TILPASSINGSLANDSKAP (3D OVERFLATE)
# ============================================================
def fig3_landskap():
    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(111, projection="3d")

    x = np.linspace(-3, 3, 200)
    y = np.linspace(-3, 3, 200)
    X, Y = np.meshgrid(x, y)

    # Multi-peaked fitness landscape
    Z = (1.5 * np.exp(-((X - 1)**2 + (Y - 0.5)**2) / 0.8)
         + 1.2 * np.exp(-((X + 1.2)**2 + (Y + 0.8)**2) / 0.6)
         + 0.8 * np.exp(-((X + 0.3)**2 + (Y - 1.5)**2) / 0.5)
         + 0.6 * np.exp(-((X - 1.8)**2 + (Y + 1.5)**2) / 0.7)
         - 0.3 * np.exp(-((X)**2 + (Y)**2) / 2))

    Z = gaussian_filter(Z, sigma=3)

    # Custom colormap
    cmap = LinearSegmentedColormap.from_list("landscape",
        ["#1D3557", "#457B9D", "#A8DADC", "#F1FAEE", "#E9C46A", "#F4A261", "#E76F51"])

    surf = ax.plot_surface(X, Y, Z, cmap=cmap, alpha=0.85, edgecolor="none",
                           antialiased=True, rcount=100, ccount=100)

    # Mark peaks
    peaks = [(1.0, 0.5), (-1.2, -0.8), (-0.3, 1.5), (1.8, -1.5)]
    labels = [r"$S_1$", r"$S_2$", r"$S_3$", r"$S_4$"]
    for (px, py), lbl in zip(peaks, labels):
        ix = np.argmin(np.abs(x - px))
        iy = np.argmin(np.abs(y - py))
        pz = Z[iy, ix]
        ax.scatter([px], [py], [pz + 0.03], s=40, c="white", edgecolors="black",
                   zorder=5, linewidths=1)
        ax.text(px, py, pz + 0.08, lbl, fontsize=10, ha="center",
                fontweight="bold", color=COLORS["dark"])

    ax.set_xlabel(r"$x_1$", labelpad=8)
    ax.set_ylabel(r"$x_2$", labelpad=8)
    ax.set_zlabel(r"$f(\mathbf{x})$", labelpad=8)
    ax.set_title("III. Tilpassingslandskapet med fleire haugar (stilar $S_i$)",
                 pad=15)
    ax.view_init(elev=35, azim=-50)
    ax.set_box_aspect(None, zoom=0.85)

    fig.savefig(os.path.join(OUT, "fig3_landskap.pdf"))
    fig.savefig(os.path.join(OUT, "fig3_landskap.png"))
    plt.close(fig)
    print("  fig3_landskap OK")


# ============================================================
# FIG 4: KOMPROMISS OG PARETO-FRONT
# ============================================================
def fig4_kompromiss():
    fig, ax = plt.subplots(figsize=(7, 5.5))

    np.random.seed(123)
    # Generate Pareto-like front
    t = np.linspace(0.1, 2.5, 200)
    s1 = t
    s2 = 1.8 / t + 0.1 * np.random.randn(200)

    # Scatter of realized forms
    pts_s1 = np.random.uniform(0.3, 2.3, 80)
    pts_s2 = 1.8 / pts_s1 + 0.3 * np.random.randn(80)
    pts_s2 += 0.3  # shift down from front

    ax.scatter(pts_s1, pts_s2, s=20, c=COLORS["mid"], alpha=0.4,
              edgecolors="none", label=r"Realiserte former $\mathbf{x} \in B$")

    # Pareto front
    t_smooth = np.linspace(0.2, 2.4, 500)
    s2_front = 1.8 / t_smooth
    ax.plot(t_smooth, s2_front, color=COLORS["accent2"], lw=2.5,
            label="Pareto-front (optimale kompromiss)", zorder=3)

    # Mark specific compromises on the front
    marks = [(0.5, 1.8/0.5), (1.0, 1.8/1.0), (1.8, 1.8/1.8)]
    names = ["tradisjonell\n(materialdominert)", "balansert\nkompromiss",
             "modernistisk\n(kulturdominert)"]
    for (mx, my), name in zip(marks, names):
        ax.plot(mx, my, "o", ms=10, color=COLORS["accent2"], zorder=5)
        offset = (15, 15) if mx < 1.5 else (-15, 15)
        ax.annotate(name, xy=(mx, my), xytext=offset, fontsize=8,
                    textcoords="offset points", ha="center",
                    arrowprops=dict(arrowstyle="->", color=COLORS["dark"],
                                    connectionstyle="arc3,rad=0.2"),
                    color=COLORS["dark"])

    # Arrows showing trade-off directions
    ax.annotate("", xy=(2.5, 0.5), xytext=(0.3, 0.5),
                arrowprops=dict(arrowstyle="->", color=COLORS["accent3"],
                                lw=1.5, linestyle="--"))
    ax.text(1.4, 0.25, r"$\nabla s_1$", fontsize=11, color=COLORS["accent3"],
            ha="center")
    ax.annotate("", xy=(0.1, 4.0), xytext=(0.1, 0.8),
                arrowprops=dict(arrowstyle="->", color=COLORS["accent5"],
                                lw=1.5, linestyle="--"))
    ax.text(-0.15, 2.4, r"$\nabla s_2$", fontsize=11, color=COLORS["accent5"],
            ha="center", rotation=90)

    ax.set_xlabel(r"$s_1(\mathbf{x})$ — materiell affordanse", fontsize=11)
    ax.set_ylabel(r"$s_2(\mathbf{x})$ — kulturell aksept", fontsize=11)
    ax.set_title("II/III. Kompromiss: kvar form balanserer motstridande trykk")
    ax.legend(loc="upper right", fontsize=9)
    ax.set_xlim(-0.1, 2.8)
    ax.set_ylim(0, 4.5)
    ax.grid(True, alpha=0.15)

    fig.savefig(os.path.join(OUT, "fig4_kompromiss.pdf"))
    fig.savefig(os.path.join(OUT, "fig4_kompromiss.png"))
    plt.close(fig)
    print("  fig4_kompromiss OK")


# ============================================================
# FIG 5: PUNKTERT LIKEVEKT (ENTROPITIDSSERIE)
# ============================================================
def fig5_punktert():
    fig, ax = plt.subplots(figsize=(9, 4.5))

    # Simulated entropy curve with punctuated jumps
    years = np.arange(1280, 2025, 1)
    H = np.zeros_like(years, dtype=float)

    # Base plateau levels
    base = 1.0
    transitions = [
        (1280, 1550, 1.0, 1.2),    # Medieval stability
        (1550, 1620, 1.2, 2.67),    # Colonial import shock
        (1620, 1750, 2.67, 2.8),    # Baroque plateau
        (1750, 1800, 2.8, 2.9),     # Early industrial
        (1800, 1880, 2.9, 3.1),     # Industrial revolution
        (1880, 1920, 3.1, 3.51),    # Modernism shock
        (1920, 1960, 3.51, 3.6),    # Mid-century plateau
        (1960, 1980, 3.6, 4.2),     # Postmodern explosion
        (1980, 2024, 4.2, 5.07),    # Digital/global
    ]

    for start, end, h_start, h_end in transitions:
        mask = (years >= start) & (years < end)
        n = mask.sum()
        # Sigmoid transition
        t_norm = np.linspace(-3, 3, n)
        sigmoid = 1 / (1 + np.exp(-t_norm))
        H[mask] = h_start + (h_end - h_start) * sigmoid

    # Add noise
    H += 0.05 * np.random.randn(len(H))
    H = gaussian_filter(H, sigma=5)

    ax.plot(years, H, color=COLORS["dark"], lw=2)
    ax.fill_between(years, H - 0.15, H + 0.15, color=COLORS["light"], alpha=0.3)

    # Mark key transitions
    events = [
        (1580, r"Kolonial import", COLORS["accent2"]),
        (1875, r"Industrialisering", COLORS["accent5"]),
        (1920, r"Modernisme", COLORS["accent3"]),
        (1970, r"Postmodernisme", COLORS["mid"]),
    ]
    for yr, label, col in events:
        idx = yr - 1280
        ax.axvline(yr, color=col, alpha=0.4, lw=1.5, ls="--")
        ax.annotate(label, xy=(yr, H[idx] + 0.3), fontsize=8, color=col,
                    rotation=45, ha="left", fontweight="bold")

    # Data points from the thesis
    ax.plot(1600, 2.67, "o", ms=8, color=COLORS["accent2"], zorder=5)
    ax.annotate(r"$H' = 2{,}67$", xy=(1600, 2.67), xytext=(1620, 2.2),
                fontsize=9, color=COLORS["accent2"],
                arrowprops=dict(arrowstyle="->", color=COLORS["accent2"]))

    ax.plot(1900, 3.51, "o", ms=8, color=COLORS["accent3"], zorder=5)
    ax.annotate(r"$H' = 3{,}51$", xy=(1900, 3.51), xytext=(1920, 3.0),
                fontsize=9, color=COLORS["accent3"],
                arrowprops=dict(arrowstyle="->", color=COLORS["accent3"]))

    ax.set_xlabel("År")
    ax.set_ylabel(r"Shannon-entropi $H'(t)$")
    ax.set_title("IV. Punktert likevekt: materialentropi 1280--2024")
    ax.set_xlim(1280, 2024)
    ax.set_ylim(0.5, 5.5)
    ax.grid(True, alpha=0.15)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig5_punktert.pdf"))
    fig.savefig(os.path.join(OUT, "fig5_punktert.png"))
    plt.close(fig)
    print("  fig5_punktert OK")


# ============================================================
# FIG 6: NAVIGATOR-TRIPPEL (G, μ, α)
# ============================================================
def fig6_navigator():
    fig, ax = plt.subplots(figsize=(8, 6))

    # Morphospace background
    theta = np.linspace(0, 2*np.pi, 100)
    r_mc = 3.5 + 0.3*np.sin(3*theta)
    ax.fill(r_mc*np.cos(theta), r_mc*np.sin(theta),
            color=COLORS["open"], alpha=0.2, zorder=0)
    ax.plot(r_mc*np.cos(theta), r_mc*np.sin(theta),
            color=COLORS["accent1"], lw=1.5, ls="--", alpha=0.5)

    # Goal region G
    gx, gy = 2.0, 1.5
    g_theta = np.linspace(0, 2*np.pi, 100)
    g_r = 0.6
    ax.fill(gx + g_r*np.cos(g_theta), gy + g_r*np.sin(g_theta),
            color=COLORS["accent3"], alpha=0.3, zorder=2)
    ax.plot(gx + g_r*np.cos(g_theta), gy + g_r*np.sin(g_theta),
            color=COLORS["accent3"], lw=2, zorder=3)
    ax.text(gx, gy, r"$G$", fontsize=16, ha="center", va="center",
            fontweight="bold", color=COLORS["accent3"])

    # Current position
    cx, cy = -1.5, -1.0
    ax.plot(cx, cy, "o", ms=12, color=COLORS["accent2"], zorder=5)
    ax.text(cx - 0.3, cy - 0.4, r"$\mathbf{x}$", fontsize=14,
            fontweight="bold", color=COLORS["accent2"])

    # Distance function μ — dashed line
    ax.annotate("", xy=(gx - 0.5, gy - 0.3), xytext=(cx + 0.15, cy + 0.1),
                arrowprops=dict(arrowstyle="-", color=COLORS["dark"],
                                lw=1.5, ls="--"))
    mid_x, mid_y = (cx + gx) / 2 - 0.3, (cy + gy) / 2 - 0.3
    ax.text(mid_x, mid_y, r"$\mu(\mathbf{x}) = d(\mathbf{x}, G)$",
            fontsize=10, color=COLORS["dark"], fontstyle="italic",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    # Adjustment field α — curved arrow showing path
    path_t = np.linspace(0, 1, 50)
    path_x = cx + (gx - cx) * path_t + 0.8 * np.sin(2*np.pi*path_t)
    path_y = cy + (gy - cy) * path_t - 0.5 * np.sin(np.pi*path_t)
    ax.plot(path_x, path_y, color=COLORS["accent1"], lw=2, ls="-", alpha=0.6, zorder=4)

    # Alpha arrows along path
    for i in range(5, 45, 8):
        dx = path_x[i+1] - path_x[i]
        dy = path_y[i+1] - path_y[i]
        ax.annotate("", xy=(path_x[i] + dx*3, path_y[i] + dy*3),
                    xytext=(path_x[i], path_y[i]),
                    arrowprops=dict(arrowstyle="->", color=COLORS["accent1"],
                                    lw=1.8), zorder=4)

    ax.text(-0.5, -2.5, r"$\alpha(\mathbf{x})$: justeringsfelt",
            fontsize=11, color=COLORS["accent1"], fontweight="bold")

    # Condition label
    ax.text(0, 3.0, r"$\langle \alpha(\mathbf{x}), -\nabla\mu(\mathbf{x}) \rangle > 0$",
            fontsize=12, ha="center", color=COLORS["dark"],
            bbox=dict(boxstyle="round,pad=0.4", facecolor=COLORS["light"],
                      alpha=0.5))

    ax.text(-3.2, 3.2, r"$\mathbf{M}_C$", fontsize=14, color=COLORS["accent1"],
            fontweight="bold")

    ax.set_xlim(-4.2, 4.2)
    ax.set_ylim(-3.8, 4)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$x_1$")
    ax.set_ylabel(r"$x_2$")
    ax.set_title("VI. Navigator-trippelet $N = (G, \\mu, \\alpha)$")
    ax.grid(True, alpha=0.1)

    fig.savefig(os.path.join(OUT, "fig6_navigator.pdf"))
    fig.savefig(os.path.join(OUT, "fig6_navigator.png"))
    plt.close(fig)
    print("  fig6_navigator OK")


# ============================================================
# FIG 7: GRENSEFLATE-HIERARKI (NESTEDE SKALAER)
# ============================================================
def fig7_grenseflate():
    fig, ax = plt.subplots(figsize=(10, 5))

    scales = [
        (r"$\mu$m, ms", "Ionkanal", COLORS["dark"], 0.4),
        ("mm, min", "Celle", COLORS["mid"], 0.7),
        ("cm, timar", "Vev", COLORS["accent3"], 1.0),
        ("m, år", "Organisme", COLORS["accent4"], 1.4),
        ("km, tiår", "Samfunn", COLORS["accent5"], 1.9),
        ("Kontinent, 100 år", "Sivilisasjon", COLORS["accent2"], 2.5),
        ("Globalt, 1000 år", "Biosystem", "#8B5CF6", 3.2),
    ]

    for i, (scale, name, color, radius) in enumerate(scales):
        # Nested ellipses
        ellipse = mpatches.Ellipse((5, 2.5), radius*5.5, radius*2.8,
                                    facecolor=color, alpha=0.12,
                                    edgecolor=color, lw=1.5)
        ax.add_patch(ellipse)

        # Labels on right side
        x_label = 5 + radius * 2.75 + 0.3
        ax.text(x_label, 2.5, f"{name}", fontsize=9, color=color,
                fontweight="bold", va="center")
        ax.text(x_label, 2.15, scale, fontsize=7, color=color,
                va="center", fontstyle="italic")

    # Central navigator
    ax.plot(5, 2.5, "o", ms=6, color=COLORS["dark"], zorder=5)
    ax.text(5, 2.5 - 0.3, r"$N_1$", fontsize=9, ha="center", color=COLORS["dark"])

    # Arrow showing expansion
    ax.annotate("", xy=(13.5, 2.5), xytext=(5.5, 2.5),
                arrowprops=dict(arrowstyle="->", color="#666", lw=1,
                                connectionstyle="arc3,rad=0"))
    ax.text(13.8, 2.5, r"$|\partial N| \uparrow$", fontsize=11,
            color="#666", va="center")

    ax.text(5, 4.8, r"$\partial N_i$: grenseflata veks med skalaen",
            fontsize=11, ha="center", fontweight="bold", color=COLORS["dark"])

    ax.set_xlim(-1, 15)
    ax.set_ylim(0.2, 5.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("VI/VIII. Grenseflate-hierarki: nestede navigatorskalaer", pad=10)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig7_grenseflate.pdf"))
    fig.savefig(os.path.join(OUT, "fig7_grenseflate.png"))
    plt.close(fig)
    print("  fig7_grenseflate OK")


# ============================================================
# FIG 8: STASJONÆR VEG GJENNOM LANDSKAPET
# ============================================================
def fig8_stasjonaer_veg():
    fig, ax = plt.subplots(figsize=(8, 6))

    # Contour landscape
    x = np.linspace(-3, 3, 300)
    y = np.linspace(-3, 3, 300)
    X, Y = np.meshgrid(x, y)

    Z = (1.5 * np.exp(-((X - 1.5)**2 + (Y - 1.5)**2) / 1.2)
         + 1.2 * np.exp(-((X + 1.5)**2 + (Y + 1)**2) / 0.8)
         + 0.7 * np.exp(-((X + 0.5)**2 + (Y - 2)**2) / 0.6)
         - 0.4 * np.exp(-((X - 0)**2 + (Y - 0)**2) / 1.5))
    Z = gaussian_filter(Z, sigma=4)

    cmap = LinearSegmentedColormap.from_list("topo",
        [COLORS["dark"], COLORS["mid"], COLORS["light"], "#F1FAEE",
         COLORS["accent4"], COLORS["accent5"]])

    ax.contourf(X, Y, Z, levels=20, cmap=cmap, alpha=0.6)
    ax.contour(X, Y, Z, levels=15, colors="white", alpha=0.3, linewidths=0.5)

    # Stationary path (the realized one)
    t = np.linspace(0, 1, 100)
    # Path from start to end, following ridges
    px = -2.0 + 3.5 * t + 0.3 * np.sin(4 * np.pi * t)
    py = -1.5 + 3.0 * t - 0.5 * np.sin(2 * np.pi * t) + 0.3 * np.cos(3 * np.pi * t)

    ax.plot(px, py, color="white", lw=3, zorder=3)
    ax.plot(px, py, color=COLORS["accent2"], lw=2, zorder=4,
            label=r"$\gamma^*$: stasjonær veg ($\delta S = 0$)")

    # Alternative (non-stationary) paths
    for offset, alpha_val in [(0.6, 0.3), (-0.5, 0.3), (0.3, 0.2)]:
        alt_y = py + offset * np.sin(3 * np.pi * t) + 0.2 * offset
        ax.plot(px, alt_y, color="#999", lw=1, ls=":", alpha=alpha_val, zorder=2)

    # Start and end markers
    ax.plot(px[0], py[0], "s", ms=12, color=COLORS["dark"], zorder=5)
    ax.text(px[0] - 0.3, py[0] - 0.4, r"$\mathbf{x}_0$", fontsize=12,
            fontweight="bold", color="white",
            path_effects=[patheffects.withStroke(linewidth=3, foreground=COLORS["dark"])])

    ax.plot(px[-1], py[-1], "*", ms=15, color=COLORS["accent4"], zorder=5,
            markeredgecolor="white", markeredgewidth=1)
    ax.text(px[-1] + 0.2, py[-1] - 0.3, r"$\mathbf{x}_T$", fontsize=12,
            fontweight="bold", color="white",
            path_effects=[patheffects.withStroke(linewidth=3, foreground=COLORS["dark"])])

    # S[γ] annotation
    ax.text(0.3, -2.5,
            r"$S[\gamma] = \int_0^T \mathcal{L}(\gamma, \gamma\prime, t)\,dt$",
            fontsize=12, color="white",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=COLORS["dark"], alpha=0.8))

    ax.set_xlabel(r"$x_1$")
    ax.set_ylabel(r"$x_2$")
    ax.set_title("IX. Stasjonær veg: den realiserte vandringa gjennom formrommet")
    ax.legend(loc="upper left", fontsize=9, facecolor="white", framealpha=0.8)
    ax.set_aspect("equal")

    fig.savefig(os.path.join(OUT, "fig8_stasjonaer_veg.pdf"))
    fig.savefig(os.path.join(OUT, "fig8_stasjonaer_veg.png"))
    plt.close(fig)
    print("  fig8_stasjonaer_veg OK")


# ============================================================
# FIG 9: SPREIINGSRELASJON σ² vs ||s||
# ============================================================
def fig9_spreiing():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left panel: σ² ∝ 1/||s||
    s_vals = np.linspace(0.3, 5, 100)
    sigma2 = 1.0 / s_vals

    axes[0].plot(s_vals, sigma2, color=COLORS["accent2"], lw=2.5)
    axes[0].fill_between(s_vals, sigma2, alpha=0.1, color=COLORS["accent2"])

    # Example points
    examples = [
        (0.8, "Dekorative\nmøblar", COLORS["accent4"]),
        (1.5, "Kvardagsstolar", COLORS["mid"]),
        (3.5, "Militær-/\nindustriutstyr", COLORS["dark"]),
    ]
    for s, label, col in examples:
        sig = 1.0 / s
        axes[0].plot(s, sig, "o", ms=10, color=col, zorder=5)
        axes[0].annotate(label, xy=(s, sig), xytext=(10, 15),
                         textcoords="offset points", fontsize=8,
                         color=col, fontweight="bold",
                         arrowprops=dict(arrowstyle="->", color=col))

    axes[0].set_xlabel(r"$\|\mathbf{s}\|$ (seleksjonsstyrke)")
    axes[0].set_ylabel(r"$\sigma^2[\gamma]$ (formvarians)")
    axes[0].set_title("Spreiingsrelasjonen")
    axes[0].grid(True, alpha=0.15)

    # Right panel: illustration — two distributions
    x = np.linspace(-3, 3, 300)
    narrow = np.exp(-x**2 / 0.3) / np.sqrt(0.3 * np.pi)
    wide = np.exp(-x**2 / 2.0) / np.sqrt(2.0 * np.pi)

    axes[1].fill_between(x, wide, alpha=0.3, color=COLORS["accent4"])
    axes[1].plot(x, wide, color=COLORS["accent4"], lw=2,
                 label=r"Svakt trykk: $\sigma^2$ stor")
    axes[1].fill_between(x, narrow, alpha=0.3, color=COLORS["dark"])
    axes[1].plot(x, narrow, color=COLORS["dark"], lw=2,
                 label=r"Sterkt trykk: $\sigma^2$ lita")

    axes[1].set_xlabel("Formrommet (1D-projeksjon)")
    axes[1].set_ylabel("Tettleik")
    axes[1].set_title("Formfordeling under ulik seleksjonsstyrke")
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.15)

    fig.suptitle("IX. Spreiingsrelasjonen: $\\sigma^2[\\gamma] \\propto 1/\\|\\mathbf{s}\\|$",
                 fontsize=12, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig9_spreiing.pdf"))
    fig.savefig(os.path.join(OUT, "fig9_spreiing.png"))
    plt.close(fig)
    print("  fig9_spreiing OK")


# ============================================================
# FIG 10: OVERTALBARHEITSKONTINUUM A → D
# ============================================================
def fig10_overtalbarheit():
    fig, ax = plt.subplots(figsize=(12, 4))

    classes = [
        ("A", "Maskinvare-\nmodifikasjon", "Termostat\nIonkanal",
         COLORS["dark"], "Ingen settpunkt;\nalt hardkoda"),
        ("B", "Settpunkt-\nomskriving", "Morfogenese\nDiffusjonsmodell",
         COLORS["mid"], "Mål redigerbart,\nikkje lærbart"),
        ("C", "Trening med\nbelønning/straff", "Evolusjon\nRL-agent",
         COLORS["accent3"], "Lærer av\nerfaring"),
        ("D", "Kommunikasjon\nav grunnar", "Handverkar\nLLM",
         COLORS["accent2"], "Responderer\npå argument"),
    ]

    x_positions = [1.5, 4.5, 7.5, 10.5]
    box_width = 2.2
    box_height = 2.2

    # Gradient arrow at bottom
    for i in range(300):
        t = i / 300
        x = 0.5 + t * 11
        color_val = plt.cm.RdYlBu(1 - t)
        ax.plot([x, x + 0.04], [-0.8, -0.8], color=color_val, lw=4)

    ax.text(0.2, -0.8, "meir kunnskap\nom indre system", fontsize=7,
            va="center", ha="right", color=COLORS["dark"], fontstyle="italic")
    ax.text(11.8, -0.8, "meir kommunikasjon\nmed systemet", fontsize=7,
            va="center", ha="left", color=COLORS["accent2"], fontstyle="italic")

    for (cls, method, example, color, desc), xp in zip(classes, x_positions):
        # Main box
        rect = mpatches.FancyBboxPatch(
            (xp - box_width/2, 0), box_width, box_height,
            boxstyle="round,pad=0.15", facecolor=color, alpha=0.15,
            edgecolor=color, lw=2)
        ax.add_patch(rect)

        # Class label
        ax.text(xp, box_height - 0.2, f"Klasse {cls}", fontsize=12,
                fontweight="bold", ha="center", va="top", color=color)
        # Method
        ax.text(xp, box_height / 2 + 0.15, method, fontsize=9,
                ha="center", va="center", color=COLORS["dark"])
        # Example
        ax.text(xp, 0.4, example, fontsize=7, ha="center", va="center",
                color="#666", fontstyle="italic")

    # Connecting arrows
    for i in range(3):
        ax.annotate("", xy=(x_positions[i+1] - box_width/2 - 0.1, box_height/2),
                    xytext=(x_positions[i] + box_width/2 + 0.1, box_height/2),
                    arrowprops=dict(arrowstyle="->", color="#999", lw=1.5))

    ax.set_xlim(-0.5, 12.5)
    ax.set_ylim(-1.5, 3)
    ax.axis("off")
    ax.set_title("VII. Overtalbarheitskontinuumet: frå mekanisme til dialog", pad=15)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig10_overtalbarheit.pdf"))
    fig.savefig(os.path.join(OUT, "fig10_overtalbarheit.png"))
    plt.close(fig)
    print("  fig10_overtalbarheit OK")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("Genererer figurar for FORMLÆRE: MATHEMATICA ...")
    fig1_formrom()
    fig2_seleksjonstrykk()
    fig3_landskap()
    fig4_kompromiss()
    fig5_punktert()
    fig6_navigator()
    fig7_grenseflate()
    fig8_stasjonaer_veg()
    fig9_spreiing()
    fig10_overtalbarheit()
    print(f"\nAlle figurar lagra i {OUT}/")
