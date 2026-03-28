#!/usr/bin/env python3
"""
Artikkel VI – Seleksjonstrykk: Topologisk dataanalyse og optimal transport i formrommet
========================================================================================
Genererer alle figurar for Artikkel VI.

Figurar:
  fig1  – UMAP morforom (farga etter hundreår, material, stil)
  fig2  – Persistent homology: diagram + barcode
  fig3  – Wasserstein-drift mellom hundreår
  fig4  – Seleksjonstrykk som vektorfelt på UMAP
  fig5  – Orthogonale seleksjonskrefter (dekomponering)
  fig6  – Optimal transport-plan mellom to hundreår
  fig7  – Spektral klyngeanalyse (Laplacian eigenmaps)
  fig8  – Persistenslandskap over tid
  fig9  – Varians-tunnel med seleksjonsgradient
  fig10 – Fasediagram: materialovergangar
"""

import os, sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.collections import LineCollection
from matplotlib import cm
import matplotlib.patheffects as pe
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy.spatial.distance import pdist, squareform, cdist
from scipy.sparse.csgraph import laplacian
from scipy.sparse import csr_matrix
from scipy.ndimage import gaussian_filter
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.neighbors import KNeighborsRegressor, NearestNeighbors
from sklearn.decomposition import PCA
import umap
import ripser
import ot

# ── paths ──
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV  = os.path.join(ROOT, "STOLAR", "STOLAR.csv")
FIG  = os.path.join(ROOT, "texts", "VI-Seleksjonstrykk", "fig")
os.makedirs(FIG, exist_ok=True)

# ── global style ──
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.linewidth": 0.6,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
})

# ── color palettes ──
CENTURY_CMAP = plt.cm.magma
MAT_COLORS = {
    "Tre": "#8B4513", "Eik": "#A0522D", "Mahogni": "#4A0E0E",
    "Stål": "#708090", "Jern": "#2F4F4F", "Aluminium": "#B0C4DE",
    "Tekstil": "#DA70D6", "Lêr": "#D2691E", "Plast": "#00CED1",
    "Rotting": "#F0E68C", "Bambus": "#9ACD32",
}
DARK_BG = "#0a0a0f"
ACCENT1 = "#00f0ff"   # cyan
ACCENT2 = "#ff3366"   # magenta
ACCENT3 = "#ffcc00"   # gold


def load_data():
    """Les STOLAR.csv, rens og returner feature-matrise + metadata."""
    df = pd.read_csv(CSV, encoding="utf-8")

    # numeriske dimensjonar
    dims = ["Høgde (cm)", "Breidde (cm)", "Djupn (cm)", "Setehøgde (cm)", "Estimert vekt (kg)"]
    for c in dims:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # år
    df["Frå år"] = pd.to_numeric(df["Frå år"], errors="coerce")
    df = df.dropna(subset=["Frå år", "Høgde (cm)", "Breidde (cm)", "Djupn (cm)"])
    df = df[(df["Frå år"] >= 1200) & (df["Frå år"] <= 2025)]
    df["Hundreår_num"] = (df["Frå år"] // 100) * 100

    # material-dummies
    all_mats = set()
    for m in df["Materialar"].dropna():
        for part in str(m).split(","):
            part = part.strip()
            if part:
                all_mats.add(part)
    top_mats = sorted(all_mats)[:30]
    for mat in top_mats:
        df[f"mat_{mat}"] = df["Materialar"].fillna("").str.contains(mat, case=False, regex=False).astype(int)

    # feature-matrise
    feat_cols = ["Høgde (cm)", "Breidde (cm)", "Djupn (cm)"]
    if df["Setehøgde (cm)"].notna().mean() > 0.5:
        feat_cols.append("Setehøgde (cm)")
    feat_cols += [c for c in df.columns if c.startswith("mat_")]

    df_clean = df.dropna(subset=feat_cols[:3]).copy()
    for c in feat_cols:
        df_clean[c] = df_clean[c].fillna(df_clean[c].median())

    X = df_clean[feat_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return df_clean, X_scaled, feat_cols


def compute_umap(X, n_neighbors=30, min_dist=0.3, random_state=42):
    """UMAP embedding."""
    reducer = umap.UMAP(n_neighbors=n_neighbors, min_dist=min_dist,
                        n_components=2, metric="euclidean", random_state=random_state)
    return reducer.fit_transform(X)


def fig1_umap_morphospace(df, emb):
    """Fig 1: Tredobbel UMAP -- hundreår, hovudmaterial, stilperiode."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), facecolor=DARK_BG)

    for ax in axes:
        ax.set_facecolor(DARK_BG)
        ax.tick_params(colors="white", labelsize=6)
        for spine in ax.spines.values():
            spine.set_color("#333")

    # Panel A: hundreår
    ax = axes[0]
    years = df["Frå år"].values
    norm = Normalize(vmin=1300, vmax=2025)
    sc = ax.scatter(emb[:, 0], emb[:, 1], c=years, cmap="magma",
                    s=3, alpha=0.7, norm=norm, edgecolors="none", rasterized=True)
    cbar = plt.colorbar(sc, ax=ax, shrink=0.7, aspect=30, pad=0.02)
    cbar.ax.tick_params(colors="white", labelsize=6)
    cbar.set_label("År", color="white", fontsize=8)
    ax.set_title("a) Kronologisk gradient", color="white", fontsize=10, pad=8)

    # Panel B: hovudmaterial
    ax = axes[1]
    def get_primary_mat(row):
        mats = str(row).split(",")
        return mats[0].strip() if mats else "Ukjend"
    df_copy = df.copy()
    df_copy["primary_mat"] = df_copy["Materialar"].fillna("Ukjend").apply(get_primary_mat)
    top5 = df_copy["primary_mat"].value_counts().head(8).index.tolist()
    colors_mat = plt.cm.Set2(np.linspace(0, 1, len(top5)))

    for i, mat in enumerate(top5):
        mask = df_copy["primary_mat"] == mat
        ax.scatter(emb[mask, 0], emb[mask, 1], c=[colors_mat[i]],
                   s=3, alpha=0.6, label=mat, edgecolors="none", rasterized=True)
    mask_other = ~df_copy["primary_mat"].isin(top5)
    ax.scatter(emb[mask_other, 0], emb[mask_other, 1], c="#333333",
               s=1, alpha=0.2, label="Andre", edgecolors="none", rasterized=True)
    leg = ax.legend(loc="lower right", fontsize=5, framealpha=0.3,
                    facecolor=DARK_BG, edgecolor="#444", labelcolor="white",
                    markerscale=3)
    ax.set_title("b) Materialdomene", color="white", fontsize=10, pad=8)

    # Panel C: stilperiode
    ax = axes[2]
    styles = df["Stilperiode"].fillna("Ukjend")
    top_styles = styles.value_counts().head(10).index.tolist()
    colors_sty = plt.cm.tab10(np.linspace(0, 1, len(top_styles)))

    for i, sty in enumerate(top_styles):
        mask = styles == sty
        ax.scatter(emb[mask, 0], emb[mask, 1], c=[colors_sty[i]],
                   s=3, alpha=0.6, label=sty, edgecolors="none", rasterized=True)
    mask_other = ~styles.isin(top_styles)
    ax.scatter(emb[mask_other, 0], emb[mask_other, 1], c="#333333",
               s=1, alpha=0.2, edgecolors="none", rasterized=True)
    leg = ax.legend(loc="lower right", fontsize=5, framealpha=0.3,
                    facecolor=DARK_BG, edgecolor="#444", labelcolor="white",
                    markerscale=3)
    ax.set_title("c) Stilperiode", color="white", fontsize=10, pad=8)

    for ax in axes:
        ax.set_xlabel("UMAP-1", color="white", fontsize=8)
        ax.set_ylabel("UMAP-2", color="white", fontsize=8)

    fig.suptitle("Formrommet: 2300 stolar projiserte med UMAP",
                 color="white", fontsize=12, y=1.02)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_morforom_umap.pdf"), facecolor=DARK_BG)
    fig.savefig(os.path.join(FIG, "fig1_morforom_umap.png"), facecolor=DARK_BG)
    plt.close()
    print("  ✓ fig1_morforom_umap")


def fig2_persistence(X):
    """Fig 2: Persistent homology -- Vietoris-Rips diagram + barcode."""
    # subsample for computational tractability
    np.random.seed(42)
    idx = np.random.choice(len(X), min(800, len(X)), replace=False)
    X_sub = X[idx]

    result = ripser.ripser(X_sub, maxdim=2, thresh=4.0)
    diagrams = result["dgms"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor=DARK_BG)

    # Persistence diagram
    ax = axes[0]
    ax.set_facecolor(DARK_BG)
    colors = [ACCENT1, ACCENT2, ACCENT3]
    labels = ["$H_0$ (komponentar)", "$H_1$ (løkker)", "$H_2$ (holrom)"]

    max_val = 0
    for dim, dgm in enumerate(diagrams):
        if len(dgm) == 0:
            continue
        finite = dgm[np.isfinite(dgm[:, 1])]
        if len(finite) > 0:
            max_val = max(max_val, finite[:, 1].max(), finite[:, 0].max())
            ax.scatter(finite[:, 0], finite[:, 1], c=colors[dim], s=15,
                       alpha=0.7, label=labels[dim], edgecolors="white",
                       linewidths=0.3, zorder=3)
    ax.plot([0, max_val * 1.1], [0, max_val * 1.1], "--", color="#555", lw=0.8, zorder=1)
    ax.set_xlabel("Fødsel (ε)", color="white", fontsize=10)
    ax.set_ylabel("Død (ε)", color="white", fontsize=10)
    ax.set_title("a) Persistensdiagram", color="white", fontsize=11, pad=8)
    ax.legend(fontsize=8, facecolor=DARK_BG, edgecolor="#444", labelcolor="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    # Barcode
    ax = axes[1]
    ax.set_facecolor(DARK_BG)
    y_offset = 0
    for dim, dgm in enumerate(diagrams):
        finite = dgm[np.isfinite(dgm[:, 1])]
        if len(finite) == 0:
            continue
        # sort by persistence
        pers = finite[:, 1] - finite[:, 0]
        order = np.argsort(-pers)[:50]  # top 50 bars per dimension
        for j, idx_j in enumerate(order):
            b, d = finite[idx_j]
            ax.plot([b, d], [y_offset, y_offset], color=colors[dim],
                    lw=1.5, alpha=0.8, solid_capstyle="round")
            y_offset += 1
        y_offset += 3  # gap between dimensions

    ax.set_xlabel("Skala (ε)", color="white", fontsize=10)
    ax.set_ylabel("Topologiske trekk", color="white", fontsize=10)
    ax.set_title("b) Persistens-strekkode", color="white", fontsize=11, pad=8)
    ax.tick_params(colors="white")
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#333")

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_persistens.pdf"), facecolor=DARK_BG)
    fig.savefig(os.path.join(FIG, "fig2_persistens.png"), facecolor=DARK_BG)
    plt.close()
    print("  ✓ fig2_persistens")

    return diagrams


def fig3_wasserstein_drift(df, X):
    """Fig 3: Wasserstein-distanse mellom hundreår-distribusjonar."""
    centuries = sorted(df["Hundreår_num"].unique())
    centuries = [c for c in centuries if c >= 1400]  # skip sparse early data

    n = len(centuries)
    W_matrix = np.zeros((n, n))

    # compute centroid distributions per century
    centroids = {}
    for c in centuries:
        mask = df["Hundreår_num"] == c
        centroids[c] = X[mask]

    for i, ci in enumerate(centuries):
        for j, cj in enumerate(centuries):
            if i >= j:
                continue
            Xi = centroids[ci][:, :3]  # use first 3 dims (H, W, D)
            Xj = centroids[cj][:, :3]

            # empirical distributions
            a = np.ones(len(Xi)) / len(Xi)
            b = np.ones(len(Xj)) / len(Xj)
            M = cdist(Xi, Xj, metric="euclidean")
            W = ot.emd2(a, b, M)
            W_matrix[i, j] = W
            W_matrix[j, i] = W

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), facecolor=DARK_BG)

    # Heatmap
    ax = axes[0]
    ax.set_facecolor(DARK_BG)
    im = ax.imshow(W_matrix, cmap="inferno", interpolation="nearest")
    ax.set_xticks(range(n))
    ax.set_xticklabels([str(c) for c in centuries], rotation=45, color="white", fontsize=7)
    ax.set_yticks(range(n))
    ax.set_yticklabels([str(c) for c in centuries], color="white", fontsize=7)
    cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.ax.tick_params(colors="white", labelsize=7)
    cbar.set_label("$W_1$ (Wasserstein)", color="white", fontsize=9)
    ax.set_title("a) Wasserstein-distansematrise", color="white", fontsize=11, pad=8)

    # Consecutive drift
    ax = axes[1]
    ax.set_facecolor(DARK_BG)
    consecutive_w = []
    for i in range(n - 1):
        consecutive_w.append(W_matrix[i, i + 1])

    century_labels = [f"{centuries[i]}–{centuries[i+1]}" for i in range(n - 1)]
    bars = ax.bar(range(len(consecutive_w)), consecutive_w, color=ACCENT1, alpha=0.8, width=0.7)

    # highlight max drift
    max_idx = np.argmax(consecutive_w)
    bars[max_idx].set_color(ACCENT2)
    bars[max_idx].set_alpha(1.0)

    ax.set_xticks(range(len(century_labels)))
    ax.set_xticklabels(century_labels, rotation=45, ha="right", color="white", fontsize=7)
    ax.set_ylabel("$W_1$ konsekutiv drift", color="white", fontsize=9)
    ax.set_title("b) Formendring mellom påfølgjande hundreår", color="white", fontsize=11, pad=8)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_wasserstein_drift.pdf"), facecolor=DARK_BG)
    fig.savefig(os.path.join(FIG, "fig3_wasserstein_drift.png"), facecolor=DARK_BG)
    plt.close()
    print("  ✓ fig3_wasserstein_drift")

    return W_matrix, centuries


def fig4_vector_field(df, emb):
    """Fig 4: Seleksjonstrykk som vektorfelt -- temporalt gradient på UMAP."""
    fig, ax = plt.subplots(1, 1, figsize=(8, 8), facecolor=DARK_BG)
    ax.set_facecolor(DARK_BG)

    years = df["Frå år"].values
    norm = Normalize(vmin=1300, vmax=2025)

    # bakgrunn: density
    from scipy.stats import gaussian_kde
    xy = emb.T
    try:
        kde = gaussian_kde(xy, bw_method=0.15)
        xmin, xmax = emb[:, 0].min() - 1, emb[:, 0].max() + 1
        ymin, ymax = emb[:, 1].min() - 1, emb[:, 1].max() + 1
        xx, yy = np.meshgrid(np.linspace(xmin, xmax, 200),
                             np.linspace(ymin, ymax, 200))
        positions = np.vstack([xx.ravel(), yy.ravel()])
        zz = kde(positions).reshape(xx.shape)
        ax.contourf(xx, yy, zz, levels=20, cmap="Greys", alpha=0.3)
    except Exception:
        pass

    # scatter
    ax.scatter(emb[:, 0], emb[:, 1], c=years, cmap="magma", s=2,
               alpha=0.4, norm=norm, edgecolors="none", rasterized=True)

    # vector field: for each grid point, estimate temporal gradient
    grid_n = 20
    xmin, xmax = emb[:, 0].min(), emb[:, 0].max()
    ymin, ymax = emb[:, 1].min(), emb[:, 1].max()
    gx = np.linspace(xmin, xmax, grid_n)
    gy = np.linspace(ymin, ymax, grid_n)
    GX, GY = np.meshgrid(gx, gy)

    # KNN regression: predict year from UMAP position
    knn = KNeighborsRegressor(n_neighbors=30, weights="distance")
    knn.fit(emb, years)

    # compute gradient via finite differences
    eps = (xmax - xmin) / (grid_n * 2)
    U = np.zeros_like(GX)
    V = np.zeros_like(GY)

    for i in range(grid_n):
        for j in range(grid_n):
            cx, cy = GX[i, j], GY[i, j]
            pts = np.array([[cx + eps, cy], [cx - eps, cy],
                            [cx, cy + eps], [cx, cy - eps]])
            preds = knn.predict(pts)
            dydx = (preds[0] - preds[1]) / (2 * eps)
            dydy = (preds[2] - preds[3]) / (2 * eps)
            mag = np.sqrt(dydx**2 + dydy**2) + 1e-8
            U[i, j] = dydx / mag
            V[i, j] = dydy / mag

    # quiver
    ax.quiver(GX, GY, U, V, color=ACCENT1, alpha=0.7, scale=25,
              width=0.004, headwidth=4, headlength=5,
              path_effects=[pe.withStroke(linewidth=1.5, foreground=DARK_BG)])

    ax.set_xlabel("UMAP-1", color="white", fontsize=10)
    ax.set_ylabel("UMAP-2", color="white", fontsize=10)
    ax.set_title("Temporalt seleksjonstrykk: vektorfelt i formrommet",
                 color="white", fontsize=12, pad=10)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_vektorfelt.pdf"), facecolor=DARK_BG)
    fig.savefig(os.path.join(FIG, "fig4_vektorfelt.png"), facecolor=DARK_BG)
    plt.close()
    print("  ✓ fig4_vektorfelt")


def fig5_orthogonal_pressures(df, X, emb):
    """Fig 5: Dekomponering av seleksjonskrefter -- material vs. tid vs. geografi."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), facecolor=DARK_BG)

    grid_n = 18
    xmin, xmax = emb[:, 0].min(), emb[:, 0].max()
    ymin, ymax = emb[:, 1].min(), emb[:, 1].max()
    gx = np.linspace(xmin, xmax, grid_n)
    gy = np.linspace(ymin, ymax, grid_n)
    GX, GY = np.meshgrid(gx, gy)
    eps = (xmax - xmin) / (grid_n * 2)

    targets = {
        "a) Temporalt trykk": df["Frå år"].values,
        "b) Materialkompleksitet": df["Materialar"].fillna("").apply(lambda x: len(x.split(","))).values,
        "c) Dimensjonelt trykk": df["Høgde (cm)"].values,
    }
    colors_fields = [ACCENT1, ACCENT2, ACCENT3]

    for k, (title, target) in enumerate(targets.items()):
        ax = axes[k]
        ax.set_facecolor(DARK_BG)

        knn = KNeighborsRegressor(n_neighbors=30, weights="distance")
        knn.fit(emb, target)

        U = np.zeros_like(GX)
        V = np.zeros_like(GY)

        for i in range(grid_n):
            for j in range(grid_n):
                cx, cy = GX[i, j], GY[i, j]
                pts = np.array([[cx + eps, cy], [cx - eps, cy],
                                [cx, cy + eps], [cx, cy - eps]])
                preds = knn.predict(pts)
                dydx = (preds[0] - preds[1]) / (2 * eps)
                dydy = (preds[2] - preds[3]) / (2 * eps)
                mag = np.sqrt(dydx**2 + dydy**2) + 1e-8
                U[i, j] = dydx / mag
                V[i, j] = dydy / mag

        ax.scatter(emb[:, 0], emb[:, 1], c="#222", s=1, alpha=0.3, rasterized=True)
        ax.quiver(GX, GY, U, V, color=colors_fields[k], alpha=0.8, scale=25,
                  width=0.005, headwidth=4, headlength=5)
        ax.set_title(title, color="white", fontsize=10, pad=8)
        ax.set_xlabel("UMAP-1", color="white", fontsize=8)
        ax.set_ylabel("UMAP-2", color="white", fontsize=8)
        ax.tick_params(colors="white", labelsize=6)
        for spine in ax.spines.values():
            spine.set_color("#333")

    fig.suptitle("Dekomponering av seleksjonskrefter i formrommet",
                 color="white", fontsize=12, y=1.02)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_ortogonale_krefter.pdf"), facecolor=DARK_BG)
    fig.savefig(os.path.join(FIG, "fig5_ortogonale_krefter.png"), facecolor=DARK_BG)
    plt.close()
    print("  ✓ fig5_ortogonale_krefter")


def fig6_transport_plan(df, X):
    """Fig 6: Optimal transport-plan mellom 1700-talet og 1900-talet."""
    mask_early = df["Hundreår_num"] == 1700
    mask_late  = df["Hundreår_num"] == 1900

    Xe = X[mask_early][:, :3]
    Xl = X[mask_late][:, :3]

    # subsample for visibility
    np.random.seed(42)
    if len(Xe) > 150:
        idx_e = np.random.choice(len(Xe), 150, replace=False)
        Xe = Xe[idx_e]
    if len(Xl) > 150:
        idx_l = np.random.choice(len(Xl), 150, replace=False)
        Xl = Xl[idx_l]

    a = np.ones(len(Xe)) / len(Xe)
    b = np.ones(len(Xl)) / len(Xl)
    M = cdist(Xe, Xl, metric="euclidean")
    G = ot.emd(a, b, M)

    # PCA for visualization
    X_all = np.vstack([Xe, Xl])
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_all)
    Xe_pca = X_pca[:len(Xe)]
    Xl_pca = X_pca[len(Xe):]

    fig, ax = plt.subplots(1, 1, figsize=(8, 8), facecolor=DARK_BG)
    ax.set_facecolor(DARK_BG)

    # transport lines (only strongest couplings)
    threshold = np.percentile(G[G > 0], 85)
    for i in range(len(Xe)):
        for j in range(len(Xl)):
            if G[i, j] > threshold:
                alpha_line = min(G[i, j] / G.max() * 3, 0.8)
                ax.plot([Xe_pca[i, 0], Xl_pca[j, 0]],
                        [Xe_pca[i, 1], Xl_pca[j, 1]],
                        color=ACCENT3, alpha=alpha_line, lw=0.5, zorder=1)

    ax.scatter(Xe_pca[:, 0], Xe_pca[:, 1], c=ACCENT1, s=30, alpha=0.9,
               edgecolors="white", linewidths=0.3, label="1700-talet", zorder=3)
    ax.scatter(Xl_pca[:, 0], Xl_pca[:, 1], c=ACCENT2, s=30, alpha=0.9,
               edgecolors="white", linewidths=0.3, label="1900-talet", zorder=3)

    ax.legend(fontsize=10, facecolor=DARK_BG, edgecolor="#444",
              labelcolor="white", loc="upper right")
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)",
                  color="white", fontsize=10)
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)",
                  color="white", fontsize=10)
    ax.set_title("Optimal transport: 1700-talet → 1900-talet",
                 color="white", fontsize=12, pad=10)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_transportplan.pdf"), facecolor=DARK_BG)
    fig.savefig(os.path.join(FIG, "fig6_transportplan.png"), facecolor=DARK_BG)
    plt.close()
    print("  ✓ fig6_transportplan")


def fig7_spectral_clusters(X, df, emb):
    """Fig 7: Spektral klyngeanalyse via Laplacian eigenmaps."""
    # k-NN graph
    k = 15
    nn = NearestNeighbors(n_neighbors=k, metric="euclidean")
    nn.fit(X)
    dist_mat, idx_mat = nn.kneighbors(X)

    # adjacency
    n = len(X)
    rows, cols, vals = [], [], []
    for i in range(n):
        for j_pos in range(k):
            j = idx_mat[i, j_pos]
            w = np.exp(-dist_mat[i, j_pos]**2 / (2 * np.median(dist_mat)**2))
            rows.append(i)
            cols.append(j)
            vals.append(w)
    A = csr_matrix((vals, (rows, cols)), shape=(n, n))
    A = (A + A.T) / 2

    # Laplacian
    L = laplacian(A, normed=True)

    # eigendecomposition -- use dense solver on subsample for reliability
    n_eig = 8
    np.random.seed(42)
    sub_n = min(1500, n)
    sub_idx = np.random.choice(n, sub_n, replace=False)
    L_dense = L.toarray() if hasattr(L, 'toarray') else np.array(L)
    L_sub = L_dense[np.ix_(sub_idx, sub_idx)]
    all_evals, all_evecs = np.linalg.eigh(L_sub)
    eigenvalues = all_evals[:n_eig]
    eigenvectors_sub = all_evecs[:, :n_eig]
    # map back to full dataset via NN interpolation
    from sklearn.neighbors import KNeighborsRegressor
    knn_spec = KNeighborsRegressor(n_neighbors=5, weights="distance")
    knn_spec.fit(X[sub_idx], eigenvectors_sub)
    eigenvectors = knn_spec.predict(X)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), facecolor=DARK_BG)

    # Panel A: Spectral embedding colored by century
    ax = axes[0]
    ax.set_facecolor(DARK_BG)
    sc = ax.scatter(eigenvectors[:, 1], eigenvectors[:, 2],
                    c=df["Frå år"].values, cmap="magma", s=3, alpha=0.6,
                    edgecolors="none", rasterized=True)
    cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cbar.ax.tick_params(colors="white", labelsize=7)
    cbar.set_label("År", color="white", fontsize=9)
    ax.set_xlabel("$\\phi_1$ (Fiedler)", color="white", fontsize=10)
    ax.set_ylabel("$\\phi_2$", color="white", fontsize=10)
    ax.set_title("a) Spektral innleiring", color="white", fontsize=11, pad=8)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    # Panel B: Eigenvalue spectrum
    ax = axes[1]
    ax.set_facecolor(DARK_BG)
    ax.bar(range(n_eig), eigenvalues, color=ACCENT1, alpha=0.8, width=0.6)
    ax.set_xlabel("Eigenverdi-indeks", color="white", fontsize=10)
    ax.set_ylabel("$\\lambda_k$", color="white", fontsize=10)
    ax.set_title("b) Laplacian-spektrum", color="white", fontsize=11, pad=8)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    # annotate spectral gap
    gaps = np.diff(eigenvalues)
    max_gap_idx = np.argmax(gaps)
    ax.annotate(f"Spektralt gap\n(k={max_gap_idx + 1})",
                xy=(max_gap_idx + 0.5, (eigenvalues[max_gap_idx] + eigenvalues[max_gap_idx + 1]) / 2),
                color=ACCENT2, fontsize=9, ha="center",
                arrowprops=dict(arrowstyle="->", color=ACCENT2, lw=1.5))

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig7_spektral.pdf"), facecolor=DARK_BG)
    fig.savefig(os.path.join(FIG, "fig7_spektral.png"), facecolor=DARK_BG)
    plt.close()
    print("  ✓ fig7_spektral")

    return eigenvalues, eigenvectors


def fig8_persistence_landscape(X, df):
    """Fig 8: Persistenslandskap over tid -- TDA per hundreår."""
    centuries = sorted(df["Hundreår_num"].unique())
    centuries = [c for c in centuries if c >= 1500 and df[df["Hundreår_num"] == c].shape[0] >= 30]

    fig, ax = plt.subplots(1, 1, figsize=(10, 6), facecolor=DARK_BG)
    ax.set_facecolor(DARK_BG)

    betti_1_counts = []
    betti_0_counts = []
    mean_persistence = []

    for c in centuries:
        mask = df["Hundreår_num"] == c
        Xc = X[mask][:, :3]  # H, W, D only

        # subsample if too large
        if len(Xc) > 300:
            np.random.seed(42)
            idx = np.random.choice(len(Xc), 300, replace=False)
            Xc = Xc[idx]

        result = ripser.ripser(Xc, maxdim=1, thresh=3.0)
        dgms = result["dgms"]

        # H1 features
        h1 = dgms[1]
        finite_h1 = h1[np.isfinite(h1[:, 1])]
        betti_1_counts.append(len(finite_h1))

        # H0 features
        h0 = dgms[0]
        finite_h0 = h0[np.isfinite(h0[:, 1])]
        betti_0_counts.append(len(finite_h0))

        if len(finite_h1) > 0:
            mean_persistence.append(np.mean(finite_h1[:, 1] - finite_h1[:, 0]))
        else:
            mean_persistence.append(0)

    x_pos = range(len(centuries))

    # dual axis
    ax.bar(x_pos, betti_1_counts, color=ACCENT2, alpha=0.7, width=0.7,
           label="$\\beta_1$ (løkker)")
    ax.set_xticks(x_pos)
    ax.set_xticklabels([str(c) for c in centuries], rotation=45, color="white", fontsize=8)
    ax.set_ylabel("Antal $H_1$-trekk", color=ACCENT2, fontsize=10)
    ax.tick_params(axis="y", colors=ACCENT2)

    ax2 = ax.twinx()
    ax2.plot(x_pos, mean_persistence, "o-", color=ACCENT3, lw=2, markersize=6,
             label="Snitt-persistens", zorder=5)
    ax2.set_ylabel("Snitt $H_1$-persistens", color=ACCENT3, fontsize=10)
    ax2.tick_params(axis="y", colors=ACCENT3)

    ax.set_title("Topologisk kompleksitet over tid",
                 color="white", fontsize=12, pad=10)
    ax.tick_params(axis="x", colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")
    for spine in ax2.spines.values():
        spine.set_color("#333")

    # combined legend
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
              fontsize=8, facecolor=DARK_BG, edgecolor="#444", labelcolor="white")

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig8_persistenslandskap.pdf"), facecolor=DARK_BG)
    fig.savefig(os.path.join(FIG, "fig8_persistenslandskap.png"), facecolor=DARK_BG)
    plt.close()
    print("  ✓ fig8_persistenslandskap")


def fig9_variance_tunnel(df):
    """Fig 9: Varians-tunnel med seleksjonsgradient over tid."""
    df_v = df.dropna(subset=["Høgde (cm)", "Breidde (cm)", "Djupn (cm)"])
    decades = sorted(df_v["Frå år"].apply(lambda x: int(x // 50) * 50).unique())
    decades = [d for d in decades if d >= 1500 and df_v[df_v["Frå år"].apply(lambda x: int(x // 50) * 50) == d].shape[0] >= 5]

    fig, ax = plt.subplots(1, 1, figsize=(12, 5), facecolor=DARK_BG)
    ax.set_facecolor(DARK_BG)

    dims_labels = [("Høgde (cm)", ACCENT1, "Høgde"),
                   ("Breidde (cm)", ACCENT2, "Breidde"),
                   ("Djupn (cm)", ACCENT3, "Djupn")]

    for col, color, label in dims_labels:
        medians = []
        q25 = []
        q75 = []
        q10 = []
        q90 = []

        for d in decades:
            mask = df_v["Frå år"].apply(lambda x: int(x // 50) * 50) == d
            vals = df_v.loc[mask, col].dropna()
            medians.append(vals.median())
            q25.append(vals.quantile(0.25))
            q75.append(vals.quantile(0.75))
            q10.append(vals.quantile(0.10))
            q90.append(vals.quantile(0.90))

        ax.fill_between(decades, q10, q90, alpha=0.1, color=color)
        ax.fill_between(decades, q25, q75, alpha=0.25, color=color)
        ax.plot(decades, medians, "-", color=color, lw=2, label=label)

    ax.set_xlabel("Halvhundreår", color="white", fontsize=10)
    ax.set_ylabel("Dimensjon (cm)", color="white", fontsize=10)
    ax.set_title("Dimensjonell varians-tunnel: seleksjonstrykk over tid",
                 color="white", fontsize=12, pad=10)
    ax.legend(fontsize=9, facecolor=DARK_BG, edgecolor="#444", labelcolor="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig9_varianstunnel.pdf"), facecolor=DARK_BG)
    fig.savefig(os.path.join(FIG, "fig9_varianstunnel.png"), facecolor=DARK_BG)
    plt.close()
    print("  ✓ fig9_varianstunnel")


def fig10_phase_diagram(df):
    """Fig 10: Fasediagram for materialovergangar over tid."""
    df_m = df.dropna(subset=["Materialar", "Frå år"])

    # top materials
    all_mats_flat = []
    for mats in df_m["Materialar"]:
        for m in str(mats).split(","):
            m = m.strip()
            if m:
                all_mats_flat.append(m)
    from collections import Counter
    mat_counts = Counter(all_mats_flat)
    top_mats = [m for m, c in mat_counts.most_common(12)]

    # material fractions per half-century
    half_centuries = sorted(df_m["Frå år"].apply(lambda x: int(x // 50) * 50).unique())
    half_centuries = [h for h in half_centuries if h >= 1500]

    fractions = {m: [] for m in top_mats}
    for hc in half_centuries:
        mask = df_m["Frå år"].apply(lambda x: int(x // 50) * 50) == hc
        subset = df_m.loc[mask, "Materialar"]
        n_total = len(subset)
        for m in top_mats:
            n_has = subset.str.contains(m, case=False, regex=False).sum()
            fractions[m].append(n_has / max(n_total, 1))

    fig, ax = plt.subplots(1, 1, figsize=(12, 6), facecolor=DARK_BG)
    ax.set_facecolor(DARK_BG)

    # stacked area
    bottom = np.zeros(len(half_centuries))
    cmap = plt.cm.Set3(np.linspace(0, 1, len(top_mats)))

    for i, m in enumerate(top_mats):
        vals = np.array(fractions[m])
        ax.fill_between(half_centuries, bottom, bottom + vals,
                        alpha=0.8, color=cmap[i], label=m)
        bottom += vals

    ax.set_xlabel("Halvhundreår", color="white", fontsize=10)
    ax.set_ylabel("Materialfraksjon", color="white", fontsize=10)
    ax.set_title("Fasediagram: materialovergangar i formrommet",
                 color="white", fontsize=12, pad=10)
    ax.set_ylim(0, min(bottom.max() * 1.05, 3.0))
    ax.legend(loc="upper left", fontsize=7, facecolor=DARK_BG, edgecolor="#444",
              labelcolor="white", ncol=3)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig10_fasediagram.pdf"), facecolor=DARK_BG)
    fig.savefig(os.path.join(FIG, "fig10_fasediagram.png"), facecolor=DARK_BG)
    plt.close()
    print("  ✓ fig10_fasediagram")


def compute_stats(df, X, W_matrix, centuries, eigenvalues):
    """Compute and print key statistics for the article."""
    stats = {}

    # Wasserstein stats
    consecutive_w = []
    for i in range(len(centuries) - 1):
        consecutive_w.append(W_matrix[i, i + 1])
    max_drift_idx = np.argmax(consecutive_w)
    stats["max_drift_century"] = f"{centuries[max_drift_idx]}–{centuries[max_drift_idx + 1]}"
    stats["max_drift_value"] = consecutive_w[max_drift_idx]
    stats["mean_drift"] = np.mean(consecutive_w)

    # Spectral gap
    gaps = np.diff(eigenvalues)
    stats["spectral_gap_k"] = int(np.argmax(gaps) + 1)
    stats["spectral_gap_value"] = float(gaps[np.argmax(gaps)])

    # Variance statistics
    for dim in ["Høgde (cm)", "Breidde (cm)", "Djupn (cm)"]:
        cv = df[dim].std() / df[dim].mean()
        stats[f"CV_{dim}"] = cv

    # n
    stats["n_total"] = len(df)
    stats["n_centuries"] = len(centuries)

    print("\n" + "=" * 60)
    print("NØKKELTAL FOR ARTIKKEL VI")
    print("=" * 60)
    for k, v in stats.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")
    print("=" * 60)

    return stats


# ── MAIN ──
if __name__ == "__main__":
    print("=" * 60)
    print("ARTIKKEL VI: SELEKSJONSTRYKK")
    print("Topologisk dataanalyse og optimal transport i formrommet")
    print("=" * 60)

    print("\n1. Lastar data...")
    df, X, feat_cols = load_data()
    print(f"   n = {len(df)} stolar, {len(feat_cols)} variablar")

    print("\n2. Reknar UMAP-innleiring...")
    emb = compute_umap(X)

    print("\n3. Genererer figurar...")
    fig1_umap_morphospace(df, emb)
    fig2_persistence(X)
    W_matrix, centuries = fig3_wasserstein_drift(df, X)
    fig4_vector_field(df, emb)
    fig5_orthogonal_pressures(df, X, emb)
    fig6_transport_plan(df, X)
    eigenvalues, eigenvectors = fig7_spectral_clusters(X, df, emb)
    fig8_persistence_landscape(X, df)
    fig9_variance_tunnel(df)
    fig10_phase_diagram(df)

    print("\n4. Statistikk...")
    stats = compute_stats(df, X, W_matrix, centuries, eigenvalues)

    print("\n✓ Alle 10 figurar lagra i", FIG)
    print("✓ Ferdig!")
