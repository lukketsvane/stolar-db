"""
analyse_VII_faserom.py
Article VII: Formens faserom — Phase Space of Form

Applies dynamical systems theory, TDA Mapper, diffusion pseudotime,
recurrence quantification, and information geometry to the STOLAR dataset.

Generates 7 publication-ready figures for the LaTeX article.
"""

import csv
import math
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyArrowPatch
from scipy.spatial.distance import pdist, squareform
from scipy.ndimage import gaussian_filter
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import DBSCAN
import kmapper as km

warnings.filterwarnings("ignore")

# ── Style ────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Palatino", "Palatino Linotype", "Book Antiqua", "Georgia", "serif"],
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
})

FIG_DIR = Path(__file__).parent / "fig"
FIG_DIR.mkdir(exist_ok=True)
DATA_PATH = Path(__file__).parent.parent.parent / "STOLAR" / "STOLAR.csv"

# ── Century palette (consistent across all figures) ──────────────
CENTURY_COLORS = {
    "1200-talet": "#4e342e",
    "1300-talet": "#5d4037",
    "1400-talet": "#6d4c41",
    "1500-talet": "#795548",
    "1600-talet": "#d32f2f",
    "1700-talet": "#e65100",
    "1800-talet": "#1565c0",
    "1900-talet": "#2e7d32",
    "2000-talet": "#6a1b9a",
}

CENTURY_ORDER = [
    "1200-talet", "1300-talet", "1400-talet", "1500-talet",
    "1600-talet", "1700-talet", "1800-talet", "1900-talet", "2000-talet"
]


def safe_float(s):
    try:
        return float(str(s).replace(",", ".").strip())
    except (ValueError, AttributeError, TypeError):
        return None


def parse_materials(cell):
    if not cell or not str(cell).strip():
        return []
    return [x.strip() for x in str(cell).split(",") if x.strip()]


def load_data():
    """Load STOLAR dataset, filter to chairs with valid dimensions."""
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    print(f"Loaded {len(df)} rows from STOLAR.csv")

    # Clean numeric columns
    for col in ["Høgde (cm)", "Breidde (cm)", "Djupn (cm)", "Setehøgde (cm)",
                 "Estimert vekt (kg)", "Frå år"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce")

    # Filter: need at least height, width, and century
    mask = (
        df["Høgde (cm)"].notna() & (df["Høgde (cm)"] > 0) &
        df["Breidde (cm)"].notna() & (df["Breidde (cm)"] > 0) &
        df["Hundreår"].notna() & (df["Hundreår"].str.strip() != "")
    )
    df = df[mask].copy()
    print(f"After filtering (H>0, W>0, century): {len(df)} chairs")

    # Add decade from year
    df["Decade"] = (df["Frå år"] // 10 * 10).astype("Int64")
    df["Year"] = df["Frå år"]

    # Material count per chair
    df["MatCount"] = df["Materialar"].apply(lambda x: len(parse_materials(x)))

    return df


# ══════════════════════════════════════════════════════════════════
# FIGURE 1: TDA MAPPER GRAPH
# ══════════════════════════════════════════════════════════════════
def fig1_mapper(df):
    """Topological Mapper graph of design space."""
    print("\n[Fig 1] Computing Mapper graph...")

    # Feature matrix: H, W, D, SH, MatCount, Year
    features = ["Høgde (cm)", "Breidde (cm)"]
    if "Djupn (cm)" in df.columns:
        features.append("Djupn (cm)")
    if "Setehøgde (cm)" in df.columns:
        features.append("Setehøgde (cm)")
    features.extend(["MatCount", "Year"])

    sub = df.dropna(subset=features[:3]).copy()  # Need at least H, W, D
    X_raw = sub[features[:3]].values
    # Fill missing SH and year
    if "Setehøgde (cm)" in features:
        sh = sub["Setehøgde (cm)"].fillna(sub["Setehøgde (cm)"].median()).values
        X_raw = np.column_stack([X_raw, sh])
    mc = sub["MatCount"].fillna(2).values
    yr = sub["Year"].fillna(sub["Year"].median()).values
    X_raw = np.column_stack([X_raw, mc, yr])

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    # Mapper
    mapper = km.KeplerMapper(verbose=0)
    lens = mapper.fit_transform(X, projection=[0, 1])  # Project onto first 2 scaled dims

    graph = mapper.map(
        lens, X,
        cover=km.Cover(n_cubes=20, perc_overlap=0.4),
        clusterer=DBSCAN(eps=0.8, min_samples=3),
    )

    # Extract node positions and edges
    node_positions = {}
    node_sizes = []
    node_colors_century = []

    centuries = sub["Hundreår"].values

    for node_id, member_indices in graph["nodes"].items():
        # Position = mean of lens values
        pos = lens[member_indices].mean(axis=0)
        node_positions[node_id] = pos
        node_sizes.append(len(member_indices))

        # Dominant century
        cent_counts = Counter(centuries[member_indices])
        dominant = cent_counts.most_common(1)[0][0]
        node_colors_century.append(CENTURY_COLORS.get(dominant, "#999999"))

    if not node_positions:
        print("  WARNING: No Mapper nodes. Skipping fig1.")
        return

    # Plot
    fig, ax = plt.subplots(figsize=(7, 5.5))

    # Edges
    for edge in graph["links"].keys():
        for target in graph["links"][edge]:
            if edge in node_positions and target in node_positions:
                p1 = node_positions[edge]
                p2 = node_positions[target]
                ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
                        color="#cccccc", linewidth=0.4, alpha=0.6, zorder=1)

    # Nodes
    positions = np.array(list(node_positions.values()))
    sizes = np.array(node_sizes)
    colors = node_colors_century

    ax.scatter(positions[:, 0], positions[:, 1],
               s=sizes * 3, c=colors, alpha=0.85, edgecolors="white",
               linewidths=0.3, zorder=2)

    # Legend
    legend_handles = []
    for cent in CENTURY_ORDER:
        if cent in set(centuries):
            legend_handles.append(
                plt.Line2D([0], [0], marker="o", color="w",
                           markerfacecolor=CENTURY_COLORS.get(cent, "#999"),
                           markersize=6, label=cent)
            )
    ax.legend(handles=legend_handles, loc="upper right", framealpha=0.9,
              title="Hundreår", fontsize=6, title_fontsize=7)

    ax.set_xlabel("Mapper-projeksjon dim. 1")
    ax.set_ylabel("Mapper-projeksjon dim. 2")
    ax.set_title("Fig. 1: Mapper-graf over formrommet (TDA)")
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("white")
    plt.tight_layout()

    fig.savefig(FIG_DIR / "fig1_mapper_graf.pdf")
    fig.savefig(FIG_DIR / "fig1_mapper_graf.png")
    plt.close(fig)
    print(f"  Saved fig1_mapper_graf.pdf ({len(graph['nodes'])} nodes, {sum(len(v) for v in graph['links'].values())} edges)")


# ══════════════════════════════════════════════════════════════════
# FIGURE 2: DIFFUSION PSEUDOTIME
# ══════════════════════════════════════════════════════════════════
def fig2_diffusion_pseudotime(df):
    """Diffusion pseudotime -- borrowed from single-cell genomics."""
    print("\n[Fig 2] Computing diffusion pseudotime...")

    sub = df.dropna(subset=["Høgde (cm)", "Breidde (cm)"]).copy()
    X_raw = sub[["Høgde (cm)", "Breidde (cm)"]].values

    if "Djupn (cm)" in sub.columns:
        d = sub["Djupn (cm)"].fillna(sub["Djupn (cm)"].median()).values
        X_raw = np.column_stack([X_raw, d])

    mc = sub["MatCount"].fillna(2).values
    X_raw = np.column_stack([X_raw, mc])

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    # Build diffusion kernel (Gaussian affinity)
    n = len(X)
    print(f"  Building diffusion kernel for {n} chairs...")

    # Use k-nearest neighbors for efficiency
    k = min(30, n - 1)
    nn = NearestNeighbors(n_neighbors=k, metric="euclidean")
    nn.fit(X)
    dists, indices = nn.kneighbors(X)

    # Adaptive kernel bandwidth (local sigma)
    sigma = np.median(dists[:, -1])

    # Build sparse affinity matrix
    from scipy.sparse import lil_matrix
    W = lil_matrix((n, n))
    for i in range(n):
        for j_idx in range(k):
            j = indices[i, j_idx]
            w = np.exp(-(dists[i, j_idx] ** 2) / (2 * sigma ** 2))
            W[i, j] = w
            W[j, i] = w

    W = W.tocsr()

    # Row-normalize to get transition matrix
    row_sums = np.array(W.sum(axis=1)).flatten()
    row_sums[row_sums == 0] = 1
    D_inv = 1.0 / row_sums

    # Compute diffusion map via eigendecomposition of normalized Laplacian
    from scipy.sparse.linalg import eigsh
    from scipy.sparse import diags

    D_inv_sqrt = diags(np.sqrt(D_inv))
    M_sym = D_inv_sqrt @ W @ D_inv_sqrt

    n_components = 4
    eigenvalues, eigenvectors = eigsh(M_sym, k=n_components + 1, which="LM")

    # Sort by eigenvalue (descending)
    idx_sort = np.argsort(-eigenvalues)
    eigenvalues = eigenvalues[idx_sort]
    eigenvectors = eigenvectors[:, idx_sort]

    # Diffusion coordinates (skip first trivial eigenvector)
    psi = eigenvectors[:, 1:n_components + 1]
    for i in range(psi.shape[1]):
        psi[:, i] *= eigenvalues[i + 1]  # weight by eigenvalue

    # Pseudotime: distance from the "oldest" chair in diffusion space
    # Find the chair with earliest year
    years = sub["Year"].values
    root_idx = np.nanargmin(years)
    pseudotime = np.sqrt(np.sum((psi - psi[root_idx]) ** 2, axis=1))

    # Normalize to [0, 1]
    pseudotime = (pseudotime - pseudotime.min()) / (pseudotime.max() - pseudotime.min() + 1e-12)

    # Plot: diffusion components colored by pseudotime
    fig, axes = plt.subplots(1, 2, figsize=(7, 3.5))

    centuries = sub["Hundreår"].values
    cent_colors = [CENTURY_COLORS.get(c, "#999999") for c in centuries]

    # Left: colored by century
    ax = axes[0]
    ax.scatter(psi[:, 0], psi[:, 1], c=cent_colors, s=3, alpha=0.5, rasterized=True)
    ax.set_xlabel("Diffusjonskomponent 1")
    ax.set_ylabel("Diffusjonskomponent 2")
    ax.set_title("a) Hundreår")
    ax.set_facecolor("#fafafa")

    # Right: colored by pseudotime
    ax = axes[1]
    sc = ax.scatter(psi[:, 0], psi[:, 1], c=pseudotime, cmap="magma_r", s=3, alpha=0.5, rasterized=True)
    ax.set_xlabel("Diffusjonskomponent 1")
    ax.set_ylabel("Diffusjonskomponent 2")
    ax.set_title("b) Pseudotid")
    ax.set_facecolor("#fafafa")
    cbar = plt.colorbar(sc, ax=ax, shrink=0.8)
    cbar.set_label("Pseudotid (0 = eldst)")

    fig.suptitle("Fig. 2: Diffusjonskart og pseudotid", fontsize=9, fontweight="bold")
    fig.patch.set_facecolor("white")
    plt.tight_layout()

    fig.savefig(FIG_DIR / "fig2_diffusjon_pseudotid.pdf")
    fig.savefig(FIG_DIR / "fig2_diffusjon_pseudotid.png")
    plt.close(fig)
    print(f"  Saved fig2_diffusjon_pseudotid.pdf")
    print(f"  Eigenvalues: {eigenvalues[:5]}")

    # Report correlation between pseudotime and actual year
    valid = ~np.isnan(years)
    corr = np.corrcoef(pseudotime[valid], years[valid])[0, 1]
    print(f"  Pseudotime-year correlation: r = {corr:.3f}")

    return pseudotime, psi, sub


# ══════════════════════════════════════════════════════════════════
# FIGURE 3: RECURRENCE PLOT
# ══════════════════════════════════════════════════════════════════
def fig3_recurrence(df):
    """Recurrence plot: when does design history repeat itself?"""
    print("\n[Fig 3] Computing recurrence plot...")

    # Aggregate by decade: mean H, W, D, MatCount, material entropy
    decades = sorted(df["Decade"].dropna().unique())
    decade_profiles = []

    for dec in decades:
        sub = df[df["Decade"] == dec]
        if len(sub) < 3:
            continue

        h_mean = sub["Høgde (cm)"].mean()
        w_mean = sub["Breidde (cm)"].mean()
        d_mean = sub["Djupn (cm)"].mean() if "Djupn (cm)" in sub.columns else 0
        mc_mean = sub["MatCount"].mean()

        # Material entropy
        all_mats = []
        for _, row in sub.iterrows():
            all_mats.extend(parse_materials(row.get("Materialar", "")))
        counts = Counter(all_mats)
        total = sum(counts.values())
        h_ent = 0
        if total > 0:
            for c in counts.values():
                p = c / total
                if p > 0:
                    h_ent -= p * math.log2(p)

        decade_profiles.append({
            "decade": int(dec),
            "h": h_mean, "w": w_mean, "d": d_mean,
            "mc": mc_mean, "h_ent": h_ent,
            "n": len(sub)
        })

    dec_df = pd.DataFrame(decade_profiles)
    dec_labels = dec_df["decade"].values

    # Build feature matrix and compute pairwise distances
    features = dec_df[["h", "w", "d", "mc", "h_ent"]].values
    scaler = StandardScaler()
    features_s = scaler.fit_transform(features)

    dist_matrix = squareform(pdist(features_s, metric="euclidean"))

    # Recurrence matrix (threshold-based)
    threshold = np.percentile(dist_matrix, 15)  # 15th percentile = "close"
    recurrence = (dist_matrix <= threshold).astype(float)

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(7, 3.5))

    # Left: distance matrix
    ax = axes[0]
    im = ax.imshow(dist_matrix, cmap="magma_r", aspect="auto",
                   extent=[dec_labels[0], dec_labels[-1], dec_labels[-1], dec_labels[0]])
    ax.set_xlabel("Tiår")
    ax.set_ylabel("Tiår")
    ax.set_title("a) Avstandsmatrise")
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Euklidsk avstand")

    # Right: recurrence plot
    ax = axes[1]
    ax.imshow(recurrence, cmap="Greys", aspect="auto",
              extent=[dec_labels[0], dec_labels[-1], dec_labels[-1], dec_labels[0]])
    ax.set_xlabel("Tiår")
    ax.set_ylabel("Tiår")
    ax.set_title(f"b) Rekurrensplott (terskel = {threshold:.2f})")

    fig.suptitle("Fig. 3: Rekurrensanalyse -- nar repeterer formhistoria seg?", fontsize=9, fontweight="bold")
    fig.patch.set_facecolor("white")
    plt.tight_layout()

    fig.savefig(FIG_DIR / "fig3_rekurrensplott.pdf")
    fig.savefig(FIG_DIR / "fig3_rekurrensplott.png")
    plt.close(fig)
    print(f"  Saved fig3_rekurrensplott.pdf ({len(dec_df)} decades)")

    # Report notable recurrences
    n = len(dec_labels)
    recurrences = []
    for i in range(n):
        for j in range(i + 2, n):  # Skip diagonal and adjacent
            if recurrence[i, j] == 1:
                recurrences.append((dec_labels[i], dec_labels[j], dist_matrix[i, j]))

    recurrences.sort(key=lambda x: x[2])
    print("  Top 10 non-adjacent recurrences:")
    for d1, d2, dist in recurrences[:10]:
        gap = d2 - d1
        print(f"    {int(d1)}s <-> {int(d2)}s (gap={gap} yr, dist={dist:.2f})")

    return dist_matrix, dec_labels


# ══════════════════════════════════════════════════════════════════
# FIGURE 4: PHASE PORTRAIT
# ══════════════════════════════════════════════════════════════════
def fig4_phase_portrait(df):
    """Phase portrait: H vs W velocity, showing attractors."""
    print("\n[Fig 4] Computing phase portrait...")

    # Aggregate by decade
    decades = sorted(df["Decade"].dropna().unique())
    dec_stats = []
    for dec in decades:
        sub = df[df["Decade"] == dec]
        if len(sub) < 5:
            continue
        dec_stats.append({
            "decade": int(dec),
            "h_mean": sub["Høgde (cm)"].mean(),
            "w_mean": sub["Breidde (cm)"].mean(),
            "h_std": sub["Høgde (cm)"].std(),
            "w_std": sub["Breidde (cm)"].std(),
            "n": len(sub),
        })

    dec_df = pd.DataFrame(dec_stats)
    if len(dec_df) < 3:
        print("  Not enough decades for phase portrait")
        return

    # Compute velocities (finite differences)
    dec_df["dH"] = np.gradient(dec_df["h_mean"].values)
    dec_df["dW"] = np.gradient(dec_df["w_mean"].values)

    # Century assignment
    dec_df["century"] = dec_df["decade"].apply(
        lambda x: f"{(x // 100) * 100}-talet" if x < 2000 else "2000-talet"
    )

    fig, axes = plt.subplots(1, 2, figsize=(7, 3.5))

    # Left: State space (H vs W trajectory)
    ax = axes[0]
    h_vals = dec_df["h_mean"].values
    w_vals = dec_df["w_mean"].values
    decades_arr = dec_df["decade"].values
    colors = [CENTURY_COLORS.get(c, "#999") for c in dec_df["century"]]

    # Draw trajectory
    ax.plot(h_vals, w_vals, color="#cccccc", linewidth=0.8, zorder=1, alpha=0.7)
    ax.scatter(h_vals, w_vals, c=colors, s=dec_df["n"].values * 0.5 + 10,
               alpha=0.85, edgecolors="white", linewidths=0.3, zorder=2)

    # Arrows showing direction
    for i in range(0, len(h_vals) - 1, 3):
        dx = h_vals[i + 1] - h_vals[i]
        dy = w_vals[i + 1] - w_vals[i]
        ax.annotate("", xy=(h_vals[i + 1], w_vals[i + 1]),
                     xytext=(h_vals[i], w_vals[i]),
                     arrowprops=dict(arrowstyle="->", color=colors[i],
                                     lw=1.0, alpha=0.7))

    # Label first and last
    ax.annotate(f"{int(decades_arr[0])}s", (h_vals[0], w_vals[0]),
                fontsize=6, fontweight="bold")
    ax.annotate(f"{int(decades_arr[-1])}s", (h_vals[-1], w_vals[-1]),
                fontsize=6, fontweight="bold")

    ax.set_xlabel("Gjennomsnittleg hogde (cm)")
    ax.set_ylabel("Gjennomsnittleg breidde (cm)")
    ax.set_title("a) Tilstandsrom (H, W)")
    ax.set_facecolor("#fafafa")

    # Right: Phase portrait (dH vs dW)
    ax = axes[1]
    dh = dec_df["dH"].values
    dw = dec_df["dW"].values

    ax.axhline(0, color="#ccc", linewidth=0.5, zorder=0)
    ax.axvline(0, color="#ccc", linewidth=0.5, zorder=0)

    ax.scatter(dh, dw, c=colors, s=dec_df["n"].values * 0.5 + 10,
               alpha=0.85, edgecolors="white", linewidths=0.3, zorder=2)

    # Connect sequentially
    ax.plot(dh, dw, color="#cccccc", linewidth=0.6, zorder=1, alpha=0.5)

    # Mark the origin (equilibrium point)
    ax.scatter([0], [0], marker="+", s=100, color="red", zorder=3, linewidths=1.5)
    ax.annotate("Likevekt", (0.05, 0.05), fontsize=6, color="red")

    ax.set_xlabel("dH/dt (cm/tiår)")
    ax.set_ylabel("dW/dt (cm/tiår)")
    ax.set_title("b) Faseportrett")
    ax.set_facecolor("#fafafa")

    fig.suptitle("Fig. 4: Faseportrett -- stolens dynamikk i tilstandsrommet", fontsize=9, fontweight="bold")
    fig.patch.set_facecolor("white")
    plt.tight_layout()

    fig.savefig(FIG_DIR / "fig4_faseportrett.pdf")
    fig.savefig(FIG_DIR / "fig4_faseportrett.png")
    plt.close(fig)
    print(f"  Saved fig4_faseportrett.pdf ({len(dec_df)} decades)")

    # Report phase dynamics
    print(f"  Mean dH/dt: {dh.mean():.3f} cm/decade")
    print(f"  Mean dW/dt: {dw.mean():.3f} cm/decade")
    print(f"  H range: {h_vals.min():.1f} - {h_vals.max():.1f} cm")
    print(f"  W range: {w_vals.min():.1f} - {w_vals.max():.1f} cm")


# ══════════════════════════════════════════════════════════════════
# FIGURE 5: INFORMATION-GEOMETRIC SURFACE
# ══════════════════════════════════════════════════════════════════
def fig5_information_geometry(df):
    """Fisher information surface -- curvature of style distributions."""
    print("\n[Fig 5] Computing information-geometric surface...")

    # For each century: compute the distribution of (H, W) and its Fisher information
    centuries = [c for c in CENTURY_ORDER if c in df["Hundreår"].unique()]

    fisher_data = []
    for cent in centuries:
        sub = df[df["Hundreår"] == cent]
        if len(sub) < 10:
            continue

        h = sub["Høgde (cm)"].dropna().values
        w = sub["Breidde (cm)"].dropna().values

        # Fisher information for normal distribution: I(mu) = 1/sigma^2
        # Higher Fisher info = more concentrated distribution = stronger "attractor"
        h_var = np.var(h, ddof=1) if len(h) > 1 else 1
        w_var = np.var(w, ddof=1) if len(w) > 1 else 1

        fisher_h = 1.0 / h_var if h_var > 0 else 0
        fisher_w = 1.0 / w_var if w_var > 0 else 0
        fisher_total = np.sqrt(fisher_h * fisher_w)  # Geometric mean

        # Material entropy as complexity measure
        all_mats = []
        for _, row in sub.iterrows():
            all_mats.extend(parse_materials(row.get("Materialar", "")))
        counts = Counter(all_mats)
        total = sum(counts.values())
        h_ent = 0
        if total > 0:
            for c in counts.values():
                p = c / total
                if p > 0:
                    h_ent -= p * math.log2(p)

        fisher_data.append({
            "century": cent,
            "h_mean": np.mean(h),
            "w_mean": np.mean(w),
            "h_std": np.std(h, ddof=1),
            "w_std": np.std(w, ddof=1),
            "fisher_h": fisher_h,
            "fisher_w": fisher_w,
            "fisher_total": fisher_total,
            "h_entropy": h_ent,
            "n": len(sub),
        })

    fdf = pd.DataFrame(fisher_data)

    fig, axes = plt.subplots(1, 2, figsize=(7, 3.5))

    # Left: Fisher information trajectory
    ax = axes[0]
    for i, row in fdf.iterrows():
        color = CENTURY_COLORS.get(row["century"], "#999")
        # Ellipse showing 1-sigma spread
        from matplotlib.patches import Ellipse
        ell = Ellipse((row["h_mean"], row["w_mean"]),
                       width=row["h_std"] * 2, height=row["w_std"] * 2,
                       alpha=0.15, facecolor=color, edgecolor=color, linewidth=1)
        ax.add_patch(ell)
        ax.scatter(row["h_mean"], row["w_mean"], c=color,
                   s=row["fisher_total"] * 8000 + 20,
                   edgecolors="white", linewidths=0.5, zorder=3)
        ax.annotate(row["century"][:4], (row["h_mean"], row["w_mean"]),
                    fontsize=5, ha="center", va="bottom",
                    xytext=(0, 5), textcoords="offset points")

    # Connect trajectory
    ax.plot(fdf["h_mean"], fdf["w_mean"], color="#aaa", linewidth=0.8,
            linestyle="--", zorder=1)

    ax.set_xlabel("Gjennomsnittleg hogde (cm)")
    ax.set_ylabel("Gjennomsnittleg breidde (cm)")
    ax.set_title("a) Fisher-informasjon som attraktorstyrke")
    ax.set_facecolor("#fafafa")

    # Right: Fisher info vs material entropy
    ax = axes[1]
    colors = [CENTURY_COLORS.get(c, "#999") for c in fdf["century"]]
    ax.scatter(fdf["h_entropy"], fdf["fisher_total"], c=colors,
               s=fdf["n"] * 0.3 + 30, edgecolors="white", linewidths=0.3,
               alpha=0.9, zorder=2)

    for i, row in fdf.iterrows():
        ax.annotate(row["century"][:4],
                    (row["h_entropy"], row["fisher_total"]),
                    fontsize=5, ha="center", va="bottom",
                    xytext=(0, 4), textcoords="offset points")

    ax.set_xlabel("Materialentropi H' (bits)")
    ax.set_ylabel("Fisher-informasjon (geometrisk snitt)")
    ax.set_title("b) Kompleksitet vs. konsentrasjon")
    ax.set_facecolor("#fafafa")

    fig.suptitle("Fig. 5: Informasjonsgeometrisk overflate", fontsize=9, fontweight="bold")
    fig.patch.set_facecolor("white")
    plt.tight_layout()

    fig.savefig(FIG_DIR / "fig5_informasjonsgeometri.pdf")
    fig.savefig(FIG_DIR / "fig5_informasjonsgeometri.png")
    plt.close(fig)
    print(f"  Saved fig5_informasjonsgeometri.pdf")

    # Print table
    print("\n  Century | N | Fisher_H | Fisher_W | Fisher_tot | H'_mat")
    for _, row in fdf.iterrows():
        print(f"  {row['century']:>12} | {row['n']:>4} | {row['fisher_h']:.4f} | {row['fisher_w']:.4f} | {row['fisher_total']:.4f} | {row['h_entropy']:.2f}")

    return fdf


# ══════════════════════════════════════════════════════════════════
# FIGURE 6: FITNESS LANDSCAPE (3D surface)
# ══════════════════════════════════════════════════════════════════
def fig6_fitness_landscape(df):
    """3D fitness landscape: density in H-W space as 'fitness'."""
    print("\n[Fig 6] Computing fitness landscape...")

    h = df["Høgde (cm)"].dropna().values
    w = df["Breidde (cm)"].dropna().values

    # 2D histogram as density proxy
    h_range = (40, 160)
    w_range = (20, 120)

    hist, xedges, yedges = np.histogram2d(h, w, bins=60,
                                           range=[h_range, w_range])
    # Smooth
    hist_smooth = gaussian_filter(hist.T, sigma=2.5)

    # Normalize
    hist_smooth = hist_smooth / hist_smooth.max()

    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111, projection="3d")

    # Create meshgrid
    xc = (xedges[:-1] + xedges[1:]) / 2
    yc = (yedges[:-1] + yedges[1:]) / 2
    X, Y = np.meshgrid(xc, yc)

    # Custom colormap
    cmap = plt.cm.magma_r

    surf = ax.plot_surface(X, Y, hist_smooth, cmap=cmap, alpha=0.85,
                           rstride=1, cstride=1, antialiased=True,
                           edgecolor="none")

    # Find peaks
    from scipy.ndimage import maximum_filter, label
    local_max = maximum_filter(hist_smooth, size=7)
    peaks = (hist_smooth == local_max) & (hist_smooth > 0.2)
    peak_coords = np.argwhere(peaks)

    for py, px in peak_coords:
        ax.scatter([xc[px]], [yc[py]], [hist_smooth[py, px] + 0.02],
                   color="red", s=30, zorder=5, depthshade=False)

    ax.set_xlabel("Hogde (cm)", labelpad=8)
    ax.set_ylabel("Breidde (cm)", labelpad=8)
    ax.set_zlabel("Tettleik (normalisert)", labelpad=5)
    ax.set_title("Fig. 6: Fitnesslandskap -- tettleiken i formrommet", fontsize=9, fontweight="bold")
    ax.view_init(elev=35, azim=225)
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("white")

    fig.colorbar(surf, ax=ax, shrink=0.5, label="Tettleik")
    plt.tight_layout()

    fig.savefig(FIG_DIR / "fig6_fitnesslandskap.pdf")
    fig.savefig(FIG_DIR / "fig6_fitnesslandskap.png")
    plt.close(fig)
    print(f"  Saved fig6_fitnesslandskap.pdf ({len(peak_coords)} peaks found)")


# ══════════════════════════════════════════════════════════════════
# FIGURE 7: EVOLUTION MAP (Wasserstein barycenters path)
# ══════════════════════════════════════════════════════════════════
def fig7_evolution_map(df):
    """Wasserstein-inspired barycenter trajectory through morphospace."""
    print("\n[Fig 7] Computing evolution map...")

    # PCA on full feature set to get 2D morphospace
    sub = df.dropna(subset=["Høgde (cm)", "Breidde (cm)"]).copy()

    feat_cols = ["Høgde (cm)", "Breidde (cm)"]
    if "Djupn (cm)" in sub.columns:
        sub["Djupn_fill"] = sub["Djupn (cm)"].fillna(sub["Djupn (cm)"].median())
        feat_cols.append("Djupn_fill")

    sub["MC_fill"] = sub["MatCount"].fillna(2)
    feat_cols.append("MC_fill")

    X = StandardScaler().fit_transform(sub[feat_cols].values)
    pca = PCA(n_components=2)
    coords = pca.fit_transform(X)
    sub["PC1"] = coords[:, 0]
    sub["PC2"] = coords[:, 1]

    print(f"  PCA explained variance: {pca.explained_variance_ratio_}")

    # Compute century centroids (barycenters)
    centuries = [c for c in CENTURY_ORDER if c in sub["Hundreår"].unique()]
    centroids = []
    for cent in centuries:
        mask = sub["Hundreår"] == cent
        centroids.append({
            "century": cent,
            "pc1": sub.loc[mask, "PC1"].mean(),
            "pc2": sub.loc[mask, "PC2"].mean(),
            "pc1_std": sub.loc[mask, "PC1"].std(),
            "pc2_std": sub.loc[mask, "PC2"].std(),
            "n": mask.sum(),
        })
    cdf = pd.DataFrame(centroids)

    # Plot
    fig, ax = plt.subplots(figsize=(7, 5.5))

    # Background: all chairs
    cent_colors_all = [CENTURY_COLORS.get(c, "#999") for c in sub["Hundreår"]]
    ax.scatter(sub["PC1"], sub["PC2"], c=cent_colors_all, s=2, alpha=0.15, rasterized=True)

    # Centroid trajectory with error ellipses
    from matplotlib.patches import Ellipse
    for i, row in cdf.iterrows():
        color = CENTURY_COLORS.get(row["century"], "#999")

        # 1-sigma ellipse
        ell = Ellipse((row["pc1"], row["pc2"]),
                       width=row["pc1_std"] * 2, height=row["pc2_std"] * 2,
                       alpha=0.12, facecolor=color, edgecolor=color, linewidth=0.8)
        ax.add_patch(ell)

    # Draw trajectory with arrows
    for i in range(len(cdf) - 1):
        r1, r2 = cdf.iloc[i], cdf.iloc[i + 1]
        color = CENTURY_COLORS.get(r1["century"], "#999")

        # Compute Wasserstein-like distance (L2 between centroids)
        w_dist = np.sqrt((r2["pc1"] - r1["pc1"])**2 + (r2["pc2"] - r1["pc2"])**2)

        ax.annotate("",
                     xy=(r2["pc1"], r2["pc2"]),
                     xytext=(r1["pc1"], r1["pc2"]),
                     arrowprops=dict(arrowstyle="-|>",
                                     color=color, lw=1.5 + w_dist * 0.8,
                                     alpha=0.8))

    # Centroid dots with labels
    for _, row in cdf.iterrows():
        color = CENTURY_COLORS.get(row["century"], "#999")
        ax.scatter(row["pc1"], row["pc2"], c=color, s=row["n"] * 0.2 + 40,
                   edgecolors="white", linewidths=1, zorder=4)
        ax.annotate(row["century"],
                    (row["pc1"], row["pc2"]),
                    fontsize=6, fontweight="bold", ha="center",
                    xytext=(0, 8), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                              alpha=0.8, edgecolor=color, linewidth=0.5))

    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% varians)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% varians)")
    ax.set_title("Fig. 7: Evolusjonskart -- barysentrumsti gjennom morforommet",
                 fontsize=9, fontweight="bold")
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("white")

    # Legend
    legend_handles = []
    for cent in centuries:
        legend_handles.append(
            plt.Line2D([0], [0], marker="o", color="w",
                       markerfacecolor=CENTURY_COLORS.get(cent, "#999"),
                       markersize=6, label=cent)
        )
    ax.legend(handles=legend_handles, loc="upper left", framealpha=0.9,
              fontsize=6, title="Hundreår", title_fontsize=7)

    plt.tight_layout()

    fig.savefig(FIG_DIR / "fig7_evolusjonskart.pdf")
    fig.savefig(FIG_DIR / "fig7_evolusjonskart.png")
    plt.close(fig)
    print(f"  Saved fig7_evolusjonskart.pdf")

    # Report centroid distances
    print("\n  Centroid trajectory distances:")
    for i in range(len(cdf) - 1):
        r1, r2 = cdf.iloc[i], cdf.iloc[i + 1]
        d = np.sqrt((r2["pc1"] - r1["pc1"])**2 + (r2["pc2"] - r1["pc2"])**2)
        print(f"    {r1['century']} -> {r2['century']}: d = {d:.3f}")

    return cdf


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("ARTIKKEL VII: FORMENS FASEROM")
    print("Phase Space of Form -- Analysis Pipeline")
    print("=" * 70)

    df = load_data()

    # Generate all 7 figures
    fig1_mapper(df)
    pseudotime, psi, sub_diff = fig2_diffusion_pseudotime(df)
    dist_matrix, dec_labels = fig3_recurrence(df)
    fig4_phase_portrait(df)
    fisher_df = fig5_information_geometry(df)
    fig6_fitness_landscape(df)
    centroid_df = fig7_evolution_map(df)

    print("\n" + "=" * 70)
    print("ALL FIGURES GENERATED SUCCESSFULLY")
    print(f"Output directory: {FIG_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
