"""
Empiriske figurar E1-E6 for Formlære-artikkelen.

Ingen figur-suptittel eller footer-forklaring i bileta;
all tekstkontekst blir skriven inn i LaTeX av forfattar.

Datagrunnlag: STOLAR/STOLAR.csv (2048 stolar, 1997 med komplett tabellgeometri
og mesh-avleidde trekk). GLB-meshar i STOLAR/glb/.

Seks morfologiske aksar:
  Høgde, Breidde, Djupn, Sphericity, Fill-ratio, Inertia-ratio

Figurane:
  E1  PCA-morforom farga etter stilperiode
  E2  7x7 mesh-silhuett-grid over PCA-planet
  E3  KDE-tetthet per epoke
  E4  Kanalisering: normalisert varians per akse per epoke
  E5  Rullande sentroide og spreiing over tid
  E6  Giga-grid: alle silhuettar sorterte kronologisk

Silhuettane cachast til _silhouette_cache.npz for rask rerun.

Utgang: 300 DPI PNG i ./png_empirical/.
"""

import os, re, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import gridspec
from matplotlib.patches import Ellipse, Rectangle, FancyArrowPatch
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from scipy.stats import gaussian_kde
from scipy.ndimage import binary_closing, binary_fill_holes
from scipy.spatial import ConvexHull
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import trimesh

warnings.filterwarnings("ignore")

# ─── Paths ────────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CSV  = os.path.join(REPO, "STOLAR", "STOLAR.csv")
GLB  = os.path.join(REPO, "STOLAR", "glb")
OUT  = os.path.join(HERE, "png_empirical")
os.makedirs(OUT, exist_ok=True)

# ─── Style ────────────────────────────────────────────────────────────
SLATE = "#3C4B5F"
AMBER = "#B47332"
LIGHTSLATE = "#E1E6EE"
LIGHTAMBER = "#F3E4CD"
CREAM = "#FAF6EE"

OI = {
    "orange": "#E69F00", "skyblue": "#56B4E9", "green": "#009E73",
    "yellow": "#F0E442", "blue": "#0072B2", "rust": "#D55E00",
    "pink": "#CC79A7", "black": "#000000",  "grey": "#999999",
}

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Segoe UI", "Arial"],
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
})


def save(fig, name):
    path = os.path.join(OUT, f"{name}.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved: png_empirical/{name}.png")


# ─── Data loading and preprocessing ──────────────────────────────────
AXES = ["Høgde (cm)", "Breidde (cm)", "Djupn (cm)",
        "Sphericity (mesh)", "Fill-ratio (mesh)", "Inertia-ratio (mesh)"]

AXIS_LABELS_NN = {
    "Høgde (cm)": "Høgde",
    "Breidde (cm)": "Breidde",
    "Djupn (cm)": "Djupn",
    "Sphericity (mesh)": "Sphericity",
    "Fill-ratio (mesh)": "Fill-ratio",
    "Inertia-ratio (mesh)": "Inertia-ratio",
}

# Ordered periods for time-ordered plots (spans ca. 1400-2024)
PERIOD_ORDER = [
    "Renessanse", "Barokk", "Régence", "Rokokko", "Empire",
    "Nyklassisisme", "Hepplewhite", "Historisme", "Viktorianisme",
    "Jugend/Art Nouveau", "Art Deco / Tidleg modernisme",
    "Bauhaus", "Funksjonalisme", "Nordisk funksjonalisme",
    "Modernisme", "Midtjahrhundre modernisme",
    "Modernisme / Midtjahrhundre", "Skandinavisk modernisme",
    "Postmodernisme", "Samtidsdesign",
]

# Approximate midpoint year per period (for time-axis ordering)
PERIOD_YEAR = {
    "Renessanse": 1550, "Barokk": 1680, "Régence": 1720, "Rokokko": 1755,
    "Nyklassisisme": 1790, "Hepplewhite": 1790, "Empire": 1810,
    "Historisme": 1870, "Viktorianisme": 1875,
    "Jugend/Art Nouveau": 1905, "Art Deco / Tidleg modernisme": 1925,
    "Bauhaus": 1928, "Funksjonalisme": 1935, "Nordisk funksjonalisme": 1945,
    "Modernisme": 1955, "Midtjahrhundre modernisme": 1960,
    "Modernisme / Midtjahrhundre": 1962, "Skandinavisk modernisme": 1965,
    "Postmodernisme": 1985, "Samtidsdesign": 2015,
}

# Color mapping: chronological gradient slate→amber
def make_period_colors():
    ordered = sorted(PERIOD_YEAR.items(), key=lambda kv: kv[1])
    n = len(ordered)
    cmap = LinearSegmentedColormap.from_list(
        "per", [SLATE, "#6B7080", "#A08860", AMBER], N=n)
    return {name: cmap(i / max(n - 1, 1)) for i, (name, _) in enumerate(ordered)}

PERIOD_COLOR = make_period_colors()


def _parse_century(v):
    if not isinstance(v, str):
        return None
    m = re.match(r"(\d{3,4})", v)
    if m:
        return int(m.group(1)) + 50
    return None


def _parse_datering(v):
    if not isinstance(v, str):
        return None
    nums = re.findall(r"\d{4}", v)
    if not nums:
        return None
    if len(nums) == 1:
        return float(nums[0])
    return (float(nums[0]) + float(nums[1])) / 2


def load_data():
    df = pd.read_csv(CSV)
    for c in AXES:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Frå år"] = pd.to_numeric(df["Frå år"], errors="coerce")
    df["Til år"] = pd.to_numeric(df["Til år"], errors="coerce")
    # treat values < 1000 as missing (placeholder zeros)
    df["Frå år"] = df["Frå år"].where(df["Frå år"] >= 1000)
    df["Til år"] = df["Til år"].where(df["Til år"] >= 1000)

    # fall-back parsers
    yr_h = df["Hundreår"].apply(_parse_century)
    yr_d = df["Datering"].apply(_parse_datering)

    def best(r):
        f, t = r["Frå år"], r["Til år"]
        if pd.notna(f) and pd.notna(t):
            return (f + t) / 2
        if pd.notna(f):
            return f
        if pd.notna(t):
            return t
        if pd.notna(r["_yrd"]):
            return r["_yrd"]
        if pd.notna(r["_yrh"]):
            return r["_yrh"]
        return np.nan

    df["_yrh"] = yr_h
    df["_yrd"] = yr_d
    df = df[df[AXES].notna().all(axis=1)].copy()
    df["år"] = df.apply(best, axis=1)
    df = df.drop(columns=["_yrh", "_yrd"])

    total_geom = len(df)
    have_year = df["år"].notna().sum()
    print(f"  loaded: {total_geom} chairs with complete geometry  "
          f"({have_year} have a usable year)")
    return df


def fit_pca(df):
    X = df[AXES].values
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    pca = PCA(n_components=6).fit(Xs)
    scores = pca.transform(Xs)
    df = df.copy()
    for i in range(6):
        df[f"PC{i+1}"] = scores[:, i]
    return df, pca, scaler


# ═════════════════════════════════════════════════════════════════════
# FIG E1: PCA-morforom farga etter stilperiode
# ═════════════════════════════════════════════════════════════════════
def fig_E1_morforom_pca(df, pca):
    fig = plt.figure(figsize=(12, 6.5))
    gs = gridspec.GridSpec(1, 3, width_ratios=[3.1, 3.1, 1.35],
                           wspace=0.22, figure=fig)

    # clip display to robust quantiles so outliers do not blow out the panel
    def lims(vals, q=0.99):
        lo = np.quantile(vals, 1 - q)
        hi = np.quantile(vals, q)
        pad = (hi - lo) * 0.08
        return lo - pad, hi + pad

    x1lo, x1hi = lims(df["PC1"])
    x2lo, x2hi = lims(df["PC2"])
    x3lo, x3hi = lims(df["PC3"])

    # --- Main scatter: PC1 vs PC2 ---
    ax = fig.add_subplot(gs[0])
    ax.scatter(df["PC1"], df["PC2"], s=6, c=OI["grey"], alpha=0.15,
               linewidths=0, zorder=1)
    top_periods = df["Stilperiode"].value_counts().head(12).index.tolist()
    ordered = [p for p in PERIOD_ORDER if p in top_periods]
    for p in ordered:
        sub = df[df["Stilperiode"] == p]
        c = PERIOD_COLOR.get(p, OI["grey"])
        ax.scatter(sub["PC1"], sub["PC2"], s=14, color=c, alpha=0.8,
                   edgecolors="none", label=f"{p} (n={len(sub)})", zorder=3)

    ax.set_xlim(x1lo, x1hi); ax.set_ylim(x2lo, x2hi)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% varians)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% varians)")
    ax.set_title("(a)", loc="left", fontsize=10.5, weight="bold")
    ax.grid(alpha=0.18, linewidth=0.5)
    ax.axhline(0, color=OI["grey"], linewidth=0.5, alpha=0.5)
    ax.axvline(0, color=OI["grey"], linewidth=0.5, alpha=0.5)

    # --- Secondary: PC1 vs PC3 ---
    ax2 = fig.add_subplot(gs[1])
    ax2.scatter(df["PC1"], df["PC3"], s=6, c=OI["grey"], alpha=0.15,
                linewidths=0, zorder=1)
    for p in ordered:
        sub = df[df["Stilperiode"] == p]
        c = PERIOD_COLOR.get(p, OI["grey"])
        ax2.scatter(sub["PC1"], sub["PC3"], s=14, color=c, alpha=0.8,
                    edgecolors="none", zorder=3)
    ax2.set_xlim(x1lo, x1hi); ax2.set_ylim(x3lo, x3hi)
    ax2.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% varians)")
    ax2.set_ylabel(f"PC3 ({pca.explained_variance_ratio_[2]*100:.1f}% varians)")
    ax2.set_title("(b)", loc="left", fontsize=10.5, weight="bold")
    ax2.grid(alpha=0.18, linewidth=0.5)
    ax2.axhline(0, color=OI["grey"], linewidth=0.5, alpha=0.5)
    ax2.axvline(0, color=OI["grey"], linewidth=0.5, alpha=0.5)

    # --- Loadings (biplot arrows on panel a) ---
    load = pca.components_.T[:, :2]
    # scale arrows so the longest fills ~80% of the shorter half-axis
    halfx = (x1hi - x1lo) / 2 * 0.72
    halfy = (x2hi - x2lo) / 2 * 0.72
    load_mag = np.sqrt(load[:, 0] ** 2 + load[:, 1] ** 2)
    max_mag = load_mag.max()
    for i, name in enumerate(AXES):
        x = load[i, 0] / max_mag * halfx
        y = load[i, 1] / max_mag * halfy
        ax.annotate("", xy=(x, y), xytext=(0, 0),
                    arrowprops=dict(arrowstyle="->", color=OI["black"],
                                    lw=1.1, alpha=0.92))
        ax.text(x * 1.18, y * 1.18, AXIS_LABELS_NN[name],
                fontsize=8.5, color=OI["black"], weight="bold",
                ha="center", va="center",
                bbox=dict(facecolor=CREAM, edgecolor=SLATE, linewidth=0.4,
                          boxstyle="round,pad=0.18", alpha=0.92))

    # --- Legend panel ---
    lax = fig.add_subplot(gs[2])
    lax.axis("off")
    handles = []
    for p in ordered:
        c = PERIOD_COLOR.get(p, OI["grey"])
        n_p = (df["Stilperiode"] == p).sum()
        handles.append(plt.Line2D([0], [0], marker="o", linestyle="",
                                   markersize=7, markerfacecolor=c,
                                   markeredgecolor="none",
                                   label=f"{p}  (n={n_p})"))
    lax.legend(handles=handles, loc="upper left",
               frameon=False, fontsize=8.2, handletextpad=0.5,
               title="Stilperiode (kronologisk)",
               title_fontsize=9.2, alignment="left")

    save(fig, "E1_morforom_pca")


# ═════════════════════════════════════════════════════════════════════
# Silhouette rendering + cache
# ═════════════════════════════════════════════════════════════════════
CACHE_PATH = os.path.join(HERE, "_silhouette_cache_96.npz")
CACHE_N = 96


def _silhouette(glb_path, n):
    """Binary silhouette from GLB, projected to side view (ZY)."""
    try:
        m = trimesh.load(glb_path, force="mesh", process=False)
    except Exception:
        return None
    v = np.asarray(m.vertices, dtype=float)
    if v.size == 0:
        return None
    if len(v) > 120000:
        idx = np.random.default_rng(0).choice(len(v), 120000, replace=False)
        v = v[idx]
    u, w = v[:, 2], v[:, 1]
    u = u - (u.max() + u.min()) / 2
    w = w - (w.max() + w.min()) / 2
    scale = max(np.abs(u).max(), np.abs(w).max(), 1e-9)
    u, w = u / scale, w / scale
    img = np.zeros((n, n), dtype=bool)
    ix = ((u + 1.08) / 2.16 * n).astype(int).clip(0, n - 1)
    iy = ((w + 1.08) / 2.16 * n).astype(int).clip(0, n - 1)
    img[n - 1 - iy, ix] = True
    img = binary_closing(img, iterations=1)
    img = binary_fill_holes(img)
    return img


# module-level worker for multiprocessing (must be picklable)
def _silhouette_worker(args):
    oid, path, n = args
    img = _silhouette(path, n)
    if img is None:
        return oid, None
    # pack to bytes for cross-process transfer
    return oid, np.packbits(img).tobytes()


def build_silhouette_cache(ids, force=False, workers=None):
    """Cache silhouettes for all given Objekt-IDs.
    Parallelised over CPUs. Missing entries are rendered and written back."""
    existing = {}
    if os.path.exists(CACHE_PATH) and not force:
        z = np.load(CACHE_PATH, allow_pickle=False)
        existing = {k: z[k].astype(bool) for k in z.files}
    missing = [i for i in ids if i not in existing
               and os.path.exists(os.path.join(GLB, f"{i}.glb"))]
    if not missing:
        print(f"  silhouette cache ok: {len(existing)} entries (no new)")
        return existing

    if workers is None:
        workers = max(mp.cpu_count() - 2, 2)
    print(f"  silhouette cache: {len(existing)} present, rendering {len(missing)} "
          f"with {workers} workers...")
    args_list = [(oid, os.path.join(GLB, f"{oid}.glb"), CACHE_N) for oid in missing]
    done = 0
    n_pix = CACHE_N * CACHE_N
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for oid, data in ex.map(_silhouette_worker, args_list, chunksize=4):
            done += 1
            if data is not None:
                bits = np.frombuffer(data, dtype=np.uint8)
                img = np.unpackbits(bits)[:n_pix].reshape(CACHE_N, CACHE_N).astype(bool)
                existing[oid] = img
            if done % 100 == 0 or done == len(missing):
                print(f"    {done}/{len(missing)}")
    np.savez_compressed(CACHE_PATH,
                        **{oid: img.astype(bool) for oid, img in existing.items()})
    print(f"  cached to {os.path.basename(CACHE_PATH)} ({len(existing)} entries)")
    return existing


# ═════════════════════════════════════════════════════════════════════
# FIG E2: mesh-grid over morforommet
# ═════════════════════════════════════════════════════════════════════
def fig_E2_mesh_grid(df, pca, sils):
    """7x7 grid. Within each cell, select the 'Holotype': the chair closest 
    to the medoid of its local cluster, filtering for mesh quality."""
    K = 7
    pc1 = df["PC1"].values
    pc2 = df["PC2"].values
    q1a, q1b = np.quantile(pc1, [0.02, 0.98])
    q2a, q2b = np.quantile(pc2, [0.02, 0.98])
    xs = np.linspace(q1a, q1b, K)
    ys = np.linspace(q2a, q2b, K)

    used = set()
    cells = {}
    dx = xs[1] - xs[0]; dy = ys[1] - ys[0]
    
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            # mask for chairs in this cell
            mask = (pc1 >= x - dx/2) & (pc1 < x + dx/2) & \
                   (pc2 >= y - dy/2) & (pc2 < y + dy/2)
            cell_df = df[mask]
            
            if len(cell_df) == 0:
                continue
            
            # Robustness Filter: exclude extreme PC3-PC6 outliers to get 'clean' silhuettes
            pc36_dist = np.sqrt((cell_df[["PC3","PC4","PC5","PC6"]]**2).sum(axis=1))
            robust_df = cell_df[pc36_dist < pc36_dist.quantile(0.85)]
            if len(robust_df) > 0: cell_df = robust_df

            # Medoid Selection: pick chair closest to the cell's own centroid
            c1, c2 = cell_df["PC1"].mean(), cell_df["PC2"].mean()
            dist = (cell_df["PC1"] - c1)**2 + (cell_df["PC2"] - c2)**2
            best_idx = dist.idxmin()
            
            oid = df.loc[best_idx, "Objekt-ID"]
            if oid in sils:
                cells[(i, j)] = (oid, df.loc[best_idx])

    fig = plt.figure(figsize=(13.5, 7.5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1.0, 1.2], wspace=0.10, figure=fig)

    # --- Left: scatter coloured by Stilperiode with grid overlay ---
    axL = fig.add_subplot(gs[0, 0])
    axL.scatter(pc1, pc2, s=6, c=OI["grey"], alpha=0.15, linewidths=0, zorder=1)
    for (i, j), (oid, row) in cells.items():
        axL.scatter([row["PC1"]], [row["PC2"]], s=60, facecolor="white", 
                    edgecolor=OI["rust"], linewidths=1.2, zorder=6)
        axL.scatter([row["PC1"]], [row["PC2"]], s=15, color=OI["rust"], zorder=7)

    for x in np.concatenate([xs - dx / 2, [xs[-1] + dx / 2]]):
        axL.axvline(x, color=SLATE, linewidth=0.35, alpha=0.25)
    for y in np.concatenate([ys - dy / 2, [ys[-1] + dy / 2]]):
        axL.axhline(y, color=SLATE, linewidth=0.35, alpha=0.25)
    axL.set_xlabel(f"PC1")
    axL.set_ylabel(f"PC2")
    axL.set_title("(a) Holotype-utveljing i morforommet", loc="left", weight="bold")

    # --- Right: silhouette grid ---
    axR = fig.add_subplot(gs[0, 1])
    axR.set_xlim(-0.5, K - 0.5); axR.set_ylim(-0.5, K - 0.5)
    axR.set_aspect("equal")
    axR.axis("off")

    for (i, j), (oid, row) in cells.items():
        img = sils[oid]
        p = row.get("Stilperiode", "")
        tint = PERIOD_COLOR.get(p, LIGHTSLATE)
        axR.add_patch(Rectangle((i - 0.48, j - 0.48), 0.96, 0.96,
                                 facecolor=to_rgba(tint, 0.15), edgecolor="none",
                                 zorder=1))
        axR.imshow(img, extent=(i - 0.44, i + 0.45, j - 0.44, j + 0.45),
                   cmap="Greys", interpolation="nearest", zorder=2, aspect="auto")
        lbl = str(p)[:12]
        axR.text(i, j - 0.52, lbl, fontsize=6.5, ha="center", va="top", color=SLATE)

    save(fig, "E2_mesh_grid")


# ═════════════════════════════════════════════════════════════════════
# FIG E6: Giga-grid av alle silhuettar (kronologisk)
# ═════════════════════════════════════════════════════════════════════
def fig_E6_giga_grid(df, sils, mode="year"):
    """
    Arrange every cached silhouette into one large grid.
      mode="year" — sort by år, left-to-right, top-to-bottom.
      mode="pc1"  — sort by PC1.
    Background behind each silhouette is coloured by Stilperiode.
    """
    # pick rows that have a silhouette and a year
    rows = df[df["Objekt-ID"].isin(sils)].copy()
    rows = rows[rows["år"].notna()].copy()
    if mode == "pc1":
        rows = rows.sort_values("PC1")
        suffix = "pc1"
    else:
        rows = rows.sort_values("år")
        suffix = "year"
    N = len(rows)
    # near-square grid
    cols = int(np.ceil(np.sqrt(N * 1.18)))
    grid_rows = int(np.ceil(N / cols))
    print(f"  giga-grid ({mode}): {N} stolar in {grid_rows}x{cols} grid")

    cell = 1  # logical unit
    pad = 0.0

    fig_w = min(20, cols * 0.30)
    fig_h = fig_w * (grid_rows / cols) * 1.02
    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = fig.add_axes([0.02, 0.04, 0.96, 0.94])
    ax.set_xlim(-0.5, cols - 0.5)
    ax.set_ylim(grid_rows - 0.5, -0.5)  # top-to-bottom
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ["top", "right", "bottom", "left"]:
        ax.spines[s].set_visible(False)

    # pre-compute per-period color
    oids = rows["Objekt-ID"].values
    pers = rows["Stilperiode"].fillna("").values

    # draw
    for k, oid in enumerate(oids):
        r = k // cols
        c = k % cols
        img = sils[oid]
        tint = PERIOD_COLOR.get(pers[k], LIGHTSLATE)
        ax.add_patch(Rectangle((c - 0.48, r - 0.48), 0.96, 0.96,
                                facecolor=to_rgba(tint, 0.35),
                                edgecolor="none", zorder=1))
        ax.imshow(img, extent=(c - 0.46, c + 0.46, r + 0.46, r - 0.46),
                  cmap="Greys", interpolation="nearest",
                  vmin=0, vmax=1, zorder=2, aspect="auto")

    # legend strip: period colors with year range
    # place below grid
    ax.set_title("")
    save(fig, f"E6_giga_grid_{suffix}")


# ═════════════════════════════════════════════════════════════════════
# Legend helper: one-row period colour strip (separate file)
# ═════════════════════════════════════════════════════════════════════
def fig_E6_legend():
    ordered = sorted(PERIOD_YEAR.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(12, 1.6))
    n = len(ordered)
    for i, (p, y) in enumerate(ordered):
        ax.add_patch(Rectangle((i, 0), 0.95, 1,
                                 facecolor=PERIOD_COLOR.get(p, OI["grey"]),
                                 edgecolor="white", linewidth=0.6))
        ax.text(i + 0.47, -0.10, f"{y}", fontsize=7.5,
                 ha="center", va="top", color=SLATE)
        ax.text(i + 0.47, 0.5, p, fontsize=7, ha="center", va="center",
                 color="white", rotation=0, weight="bold")
    ax.set_xlim(-0.1, n + 0.1)
    ax.set_ylim(-0.6, 1.1)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ["top", "right", "bottom", "left"]:
        ax.spines[s].set_visible(False)
    save(fig, "E6_periode_fargelegende")


# ═════════════════════════════════════════════════════════════════════
# FIG E3: Tilpassingslandskap som tetthet over tid
# ═════════════════════════════════════════════════════════════════════
def fig_E3_landskap_tid(df, pca):
    epochs = [
        ("Barokk",                     (1600, 1720)),
        ("Rokokko",                    (1720, 1790)),
        ("Nyklassisisme og Empire",    (1790, 1850)),
        ("Historisme og Viktoriansk",  (1850, 1905)),
        ("Modernisme 1920–1970",       (1920, 1970)),
        ("Samtidsdesign 1970–2024",    (1970, 2025)),
    ]

    fig = plt.figure(figsize=(13, 8.2))
    gs = gridspec.GridSpec(2, 3, hspace=0.30, wspace=0.22, figure=fig)

    pc1 = df["PC1"].values; pc2 = df["PC2"].values
    # clip display to robust quantiles
    xmin, xmax = np.quantile(pc1, [0.005, 0.995])
    ymin, ymax = np.quantile(pc2, [0.005, 0.995])
    xpad = (xmax - xmin) * 0.04; ypad = (ymax - ymin) * 0.04
    xmin -= xpad; xmax += xpad; ymin -= ypad; ymax += ypad

    xx, yy = np.meshgrid(np.linspace(xmin, xmax, 140),
                          np.linspace(ymin, ymax, 140))
    positions = np.vstack([xx.ravel(), yy.ravel()])

    # compute all KDEs first to find a common density scale for fair comparison
    kdes = {}
    for label, (y0, y1) in epochs:
        sub = df[(df["år"] >= y0) & (df["år"] < y1)]
        if len(sub) >= 5:
            try:
                kde = gaussian_kde(sub[["PC1", "PC2"]].values.T, bw_method=0.30)
                z = kde(positions).reshape(xx.shape)
                kdes[label] = (z, sub)
            except Exception:
                kdes[label] = (None, sub)
        else:
            kdes[label] = (None, sub)
    vmax = max((z.max() for (z, _) in kdes.values() if z is not None), default=1.0)

    dens_cmap = LinearSegmentedColormap.from_list(
        "amberfade", [(1, 1, 1, 0),
                      to_rgba(LIGHTAMBER, 0.70),
                      to_rgba(AMBER, 0.88),
                      to_rgba(SLATE, 0.98)], N=256)

    # overall centroid for reference arrow
    gcx, gcy = pc1.mean(), pc2.mean()

    for idx, (label, (y0, y1)) in enumerate(epochs):
        r, c = divmod(idx, 3)
        ax = fig.add_subplot(gs[r, c])
        ax.scatter(pc1, pc2, s=4, c=OI["grey"], alpha=0.10, linewidths=0)
        z, sub = kdes[label]
        if z is not None:
            levels = np.linspace(vmax * 0.02, vmax, 10)
            ax.contourf(xx, yy, z, levels=levels, cmap=dens_cmap, zorder=2)
            ax.contour(xx, yy, z, levels=levels[::2], colors=[SLATE],
                        linewidths=0.35, alpha=0.55, zorder=3)
        if len(sub) >= 5:
            ax.scatter(sub["PC1"], sub["PC2"], s=11, c=AMBER,
                        edgecolors=SLATE, linewidths=0.3, alpha=0.85, zorder=4)
            cx, cy = sub["PC1"].mean(), sub["PC2"].mean()
            # arrow from overall centroid to epoch centroid (emphasises drift)
            ax.annotate("", xy=(cx, cy), xytext=(gcx, gcy),
                        arrowprops=dict(arrowstyle="->", color=OI["rust"],
                                        lw=1.6, alpha=0.9),
                        zorder=6)
            ax.plot(cx, cy, marker="o", markersize=8,
                    markerfacecolor=OI["rust"], markeredgecolor="white",
                    markeredgewidth=1.0, zorder=7)
            # annotate distance from global centroid
            d = np.sqrt((cx - gcx) ** 2 + (cy - gcy) ** 2)
            ax.text(0.03, 0.96, f"Δ = {d:.2f}  σ₁ = {sub['PC1'].std():.2f}  σ₂ = {sub['PC2'].std():.2f}",
                    transform=ax.transAxes, fontsize=7.8, color=SLATE,
                    va="top", ha="left",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.8,
                               boxstyle="round,pad=0.25"))
        ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
        ax.set_title(f"{label}   n = {len(sub)}", fontsize=10.2, loc="left")
        if r == 1: ax.set_xlabel("PC1")
        if c == 0: ax.set_ylabel("PC2")
        ax.grid(alpha=0.1, linewidth=0.4)
        ax.tick_params(labelsize=8)

    save(fig, "E3_landskap_tid")


# ═════════════════════════════════════════════════════════════════════
# FIG E4: Kanalisering på tvers av aksar
# ═════════════════════════════════════════════════════════════════════
def fig_E4_kanalisering(df):
    # For each axis, compute per-period standard deviation, z-scored across periods.
    # Also include per-period sample sizes.
    counts = df["Stilperiode"].value_counts()
    periods = [p for p in PERIOD_ORDER if p in counts.index and counts[p] >= 12]

    # Normalise each axis to z-scores to compare
    df2 = df.copy()
    for c in AXES:
        s = df2[c]
        df2[c + "_z"] = (s - s.mean()) / s.std()

    fig = plt.figure(figsize=(12.5, 8.5))
    gs = gridspec.GridSpec(3, 2, hspace=0.55, wspace=0.25, figure=fig)

    for i, c in enumerate(AXES):
        r, cc = divmod(i, 2)
        ax = fig.add_subplot(gs[r, cc])
        zcol = c + "_z"
        # per-period violin/strip
        pos = [PERIOD_YEAR[p] for p in periods]
        data = [df2[df2["Stilperiode"] == p][zcol].values for p in periods]
        # violin
        parts = ax.violinplot(data, positions=pos, widths=14, showmeans=False,
                              showmedians=False, showextrema=False)
        for j, body in enumerate(parts["bodies"]):
            body.set_facecolor(PERIOD_COLOR.get(periods[j], OI["grey"]))
            body.set_edgecolor(SLATE)
            body.set_linewidth(0.5)
            body.set_alpha(0.75)
        # overlay: per-period std dev as line
        stds = [np.std(d) for d in data]
        ax.plot(pos, stds, color=SLATE, linewidth=1.4, alpha=0.7,
                 marker="o", markersize=4, markerfacecolor=AMBER,
                 markeredgecolor=SLATE, markeredgewidth=0.5,
                 label="σ per periode")
        # horizontal ref: std of all
        ax.axhline(0, color=OI["grey"], linewidth=0.4, alpha=0.5)
        ax.axhline(df2[zcol].std(), color=AMBER, linewidth=0.7,
                   linestyle="--", alpha=0.6, label="σ totalt")
        ax.set_title(AXIS_LABELS_NN[c], loc="left", fontsize=10.2)
        ax.set_xlim(1480, 2050)
        ax.set_ylim(-3.2, 3.8)
        ax.set_xlabel("år" if r == 2 else "")
        ax.set_ylabel("z-skår" if cc == 0 else "")
        ax.grid(alpha=0.12, linewidth=0.4)
        if i == 0:
            ax.legend(loc="upper left", fontsize=7.5, frameon=False)

    save(fig, "E4_kanalisering")


# ═════════════════════════════════════════════════════════════════════
# FIG E5: Stase og brot som tids-signatur
# ═════════════════════════════════════════════════════════════════════
def fig_E5_stase_brot(df, pca):
    # Use PC1, PC2 centroid and spread in 20-year windows
    df = df.sort_values("år").copy()
    yrs = df["år"].values
    p1 = df["PC1"].values; p2 = df["PC2"].values

    y_min = max(1400, int(np.quantile(yrs, 0.01) // 20) * 20)
    y_max = 2025
    window = 30
    step = 10
    centers = np.arange(y_min + window // 2, y_max - window // 2 + 1, step)

    c1 = []; c2 = []; s1 = []; s2 = []; n = []
    for c in centers:
        mask = (yrs >= c - window / 2) & (yrs <= c + window / 2)
        if mask.sum() < 5:
            c1.append(np.nan); c2.append(np.nan)
            s1.append(np.nan); s2.append(np.nan)
            n.append(mask.sum())
            continue
        c1.append(p1[mask].mean()); c2.append(p2[mask].mean())
        s1.append(p1[mask].std());  s2.append(p2[mask].std())
        n.append(mask.sum())
    c1, c2 = np.array(c1), np.array(c2)
    s1, s2 = np.array(s1), np.array(s2)
    n = np.array(n)

    # detect "break" points: large first differences in centroid
    diff = np.sqrt(np.diff(c1, prepend=c1[0]) ** 2
                   + np.diff(c2, prepend=c2[0]) ** 2)

    fig = plt.figure(figsize=(12.5, 8.5))
    gs = gridspec.GridSpec(3, 1, height_ratios=[1, 1, 1],
                           hspace=0.35, figure=fig)

    # --- top: centroid PC1 and PC2 over time ---
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(centers, c1, color=SLATE, lw=1.8, label="sentroid PC1")
    ax1.plot(centers, c2, color=AMBER, lw=1.8, label="sentroid PC2")
    ax1.fill_between(centers, c1 - s1, c1 + s1, color=SLATE, alpha=0.15)
    ax1.fill_between(centers, c2 - s2, c2 + s2, color=AMBER, alpha=0.15)
    # mark key breaks
    for ybreak, txt in [(1680, "barokk-konsolidering"),
                         (1830, "industriell revolusjon"),
                         (1920, "modernismens gjennomslag")]:
        ax1.axvline(ybreak, color=OI["rust"], linewidth=0.9,
                     linestyle="--", alpha=0.7)
        ax1.text(ybreak + 5, ax1.get_ylim()[1] * 0.86, txt,
                  fontsize=8, color=OI["rust"], rotation=0)
    ax1.set_ylabel("sentroide-verdi")
    ax1.set_title("(a)", loc="left", fontsize=10.2, weight="bold")
    ax1.legend(loc="lower left", fontsize=8.5, frameon=False)
    ax1.grid(alpha=0.18, linewidth=0.4)
    ax1.set_xlim(y_min, y_max)

    # --- middle: spread over time ---
    ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)
    ax2.plot(centers, s1, color=SLATE, lw=1.6, label="σ(PC1)")
    ax2.plot(centers, s2, color=AMBER, lw=1.6, label="σ(PC2)")
    ax2.set_ylabel("morforom-spreiing")
    ax2.set_title("(b)", loc="left", fontsize=10.2, weight="bold")
    for ybreak in [1680, 1830, 1920]:
        ax2.axvline(ybreak, color=OI["rust"], linewidth=0.9,
                     linestyle="--", alpha=0.5)
    ax2.legend(loc="upper left", fontsize=8.5, frameon=False)
    ax2.grid(alpha=0.18, linewidth=0.4)

    # --- bottom: change magnitude + sample size ---
    ax3 = fig.add_subplot(gs[2, 0], sharex=ax1)
    ax3.plot(centers, diff, color=OI["rust"], lw=1.4,
             label="‖Δ sentroid‖ per steg")
    ax3_r = ax3.twinx()
    ax3_r.fill_between(centers, 0, n, color=SLATE, alpha=0.18,
                        step="mid", label="n stolar i vindauge")
    ax3_r.set_ylabel("n i vindauge", color=SLATE)
    ax3_r.tick_params(axis="y", labelcolor=SLATE)
    ax3_r.spines["right"].set_visible(True)
    ax3.set_ylabel("sentroide-endring", color=OI["rust"])
    ax3.tick_params(axis="y", labelcolor=OI["rust"])
    ax3.set_title("(c)", loc="left", fontsize=10.2, weight="bold")
    ax3.set_xlabel("år")
    for ybreak in [1680, 1830, 1920]:
        ax3.axvline(ybreak, color=OI["rust"], linewidth=0.9,
                     linestyle="--", alpha=0.5)
    ax3.grid(alpha=0.18, linewidth=0.4)
    ax3.set_xlim(y_min, y_max)

    save(fig, "E5_stase_brot")


# ═════════════════════════════════════════════════════════════════════
def fig_E15_lande_prediction(df, pca):
    """
    Formal evolutionary analysis using the Lande equation. 
    Two panels: (a) G-matrix structure and beta pressure; 
    (b) Comparison of predicted vs observed response.
    """
    df_pre = df[(df["mat_class"] == "wood") & (df["år"] < 1920)]
    df_post = df[(df["mat_class"] == "wood") & (df["år"] >= 1920)]
    df_metal = df[df["mat_class"] == "metal"]
    
    if len(df_pre) < 15 or len(df_post) < 15:
        print("  skipping E15: insufficient wood samples")
        return

    pcs = ["PC1", "PC2"]
    G = df_pre[pcs].cov().values
    
    # beta points AWAY from metal
    metal_c = df_metal[pcs].mean().values
    pre_c = df_pre[pcs].mean().values
    beta = (pre_c - metal_c)
    beta /= np.linalg.norm(beta)
    
    # Lande prediction
    delta_z_pred = G @ beta
    delta_z_obs = df_post[pcs].mean().values - pre_c

    fig = plt.figure(figsize=(13.5, 7))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1], wspace=0.2)
    
    # --- (a) G-matrix & Kanalisering ---
    axA = fig.add_subplot(gs[0])
    axA.scatter(df["PC1"], df["PC2"], s=3, c=OI["grey"], alpha=0.08, zorder=1)
    axA.scatter(df_pre["PC1"], df_pre["PC2"], s=15, c=AMBER, alpha=0.25, label="Tre (ancestral, <1920)")
    
    # G-matrix Ellipse
    vals, vecs = np.linalg.eigh(G)
    order = vals.argsort()[::-1]; vals, vecs = vals[order], vecs[:, order]
    theta = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
    width, height = 2 * np.sqrt(vals)
    for sig in [1, 2]:
        ell = Ellipse(xy=pre_c, width=sig*width, height=sig*height, angle=theta,
                      edgecolor=AMBER, facecolor="none", lw=1.2, alpha=0.6/sig, linestyle="--")
        axA.add_patch(ell)
    
    # Beta arrow (Pressure from steel)
    axA.annotate("", xy=pre_c, xytext=pre_c - beta*0.8,
                 arrowprops=dict(arrowstyle="<-", color=OI["blue"], lw=2.5, mutation_scale=20),
                 zorder=10)
    axA.text(*(pre_c - beta*0.9), r"$\beta$ (seleksjonstrykk frå stål)", 
             color=OI["blue"], weight="bold", ha="center", fontsize=10)

    axA.set_title("(a) G-matrise og seleksjonsgradient", loc="left", weight="bold")
    axA.set_xlabel("PC1"); axA.set_ylabel("PC2")
    
    # --- (b) Response comparison ---
    axB = fig.add_subplot(gs[1])
    axB.scatter(df["PC1"], df["PC2"], s=3, c=OI["grey"], alpha=0.08, zorder=1)
    axB.scatter(df_post["PC1"], df_post["PC2"], s=15, c=OI["rust"], alpha=0.25, label="Tre (modern, >1920)")
    
    # Prediction arrow
    scale = 1.5
    axB.arrow(pre_c[0], pre_c[1], delta_z_pred[0]*scale, delta_z_pred[1]*scale, 
              head_width=0.08, head_length=0.1, fc=SLATE, ec=SLATE, lw=2.5, 
              label=r"Predikert respons ($\Delta \bar{z}$)", zorder=11)
    # Observed arrow
    axB.arrow(pre_c[0], pre_c[1], delta_z_obs[0], delta_z_obs[1], 
              head_width=0.08, head_length=0.1, fc=OI["rust"], ec=OI["rust"], lw=2.5, 
              label="Observert respons", zorder=11)
    
    # Mark optima
    axB.scatter(*pre_c, s=120, c=AMBER, edgecolors="white", zorder=12)
    axB.scatter(*(pre_c + delta_z_obs), s=120, c=OI["rust"], edgecolors="white", zorder=12)

    axB.set_title("(b) Prediksjon vs. Observert flukt", loc="left", weight="bold")
    axB.set_xlabel("PC1"); axB.set_ylabel("PC2")
    axB.legend(loc="upper right", fontsize=8)

    save(fig, "E15_lande_prediction")


# FIG E7 SPLIT: Morforom-trajektorie separert på materiale (Wood vs Metal)
# ═════════════════════════════════════════════════════════════════════
def fig_E7_trajektorie_split(df, pca):
    """Trajectory split by material, with OU-like attraction peaks."""
    fig = plt.figure(figsize=(14, 7))
    gs = gridspec.GridSpec(1, 2, wspace=0.15)
    
    def get_traj(sub):
        yr_bins = np.arange(1500, 2040, 40)
        res = []
        for i in range(len(yr_bins)-1):
            mask = (sub["år"] >= yr_bins[i]) & (sub["år"] < yr_bins[i+1])
            chunk = sub[mask]
            if len(chunk) >= 5:
                res.append({
                    "year": yr_bins[i] + 20,
                    "cx": chunk["PC1"].mean(),
                    "cy": chunk["PC2"].mean(),
                    "sex": chunk["PC1"].std() / np.sqrt(len(chunk)),
                    "sey": chunk["PC2"].std() / np.sqrt(len(chunk))
                })
        return pd.DataFrame(res)

    for i, (mcls, title, col) in enumerate([("wood", "Tre-trajektorie", AMBER), 
                                            ("metal", "Stål/Metall-trajektorie", OI["skyblue"])]):
        ax = fig.add_subplot(gs[i])
        ax.scatter(df["PC1"], df["PC2"], s=2, c=OI["grey"], alpha=0.08)
        
        sub = df[df["mat_class"] == mcls]
        traj = get_traj(sub)
        
        if len(traj) > 1:
            # Arrows
            for j in range(len(traj)-1):
                ax.annotate("", xy=(traj.iloc[j+1]["cx"], traj.iloc[j+1]["cy"]),
                             xytext=(traj.iloc[j]["cx"], traj.iloc[j]["cy"]),
                             arrowprops=dict(arrowstyle="-|>", color=col, lw=2, alpha=0.8, mutation_scale=15))
            
            # OU-Attraction Peak (Theta)
            # Simplistic OU estimate: weighted mean of later points
            theta_x = traj.iloc[-3:]["cx"].mean()
            theta_y = traj.iloc[-3:]["cy"].mean()
            ax.scatter([theta_x], [theta_y], marker="*", s=300, color=col, edgecolors="white", 
                       label=f"Adaptiv topp (OU θ)", zorder=12)
            
        ax.set_title(title, loc="left", weight="bold")
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.legend()
        
    save(fig, "E7_trajektorie_split")


# ═════════════════════════════════════════════════════════════════════
# FIG E8: Silhuettar som scatter-markers i PCA (direkte morforom-syn)
# ═════════════════════════════════════════════════════════════════════
def _period_rgb_silhouette(img, rgb):
    """Convert binary silhouette to RGBA with a period-tinted fill."""
    H, W = img.shape
    out = np.ones((H, W, 4), dtype=float)
    out[..., 0] = rgb[0]
    out[..., 1] = rgb[1]
    out[..., 2] = rgb[2]
    # alpha: 0 where no chair, ~0.92 where chair
    out[..., 3] = np.where(img, 0.92, 0.0)
    return out


def fig_E8_silhouette_scatter(df, pca, sils, n_show=180):
    """Snap each chair onto a fine grid; within each occupied grid cell,
    draw the silhouette of the chair closest to the local medoid, tinted by
    Stilperiode. Robustness filter applied to pick high-quality 'vinnarar'."""
    pc1 = df["PC1"].values; pc2 = df["PC2"].values
    oids = df["Objekt-ID"].values
    pers = df["Stilperiode"].fillna("").values

    lo1, hi1 = np.quantile(pc1, [0.01, 0.99])
    lo2, hi2 = np.quantile(pc2, [0.01, 0.99])

    K = int(np.ceil(np.sqrt(n_show * 1.5)))
    xe = np.linspace(lo1, hi1, K + 1)
    ye = np.linspace(lo2, hi2, K + 1)

    chosen = {} 
    for k in range(len(df)):
        if oids[k] not in sils: continue
        if pc1[k] < lo1 or pc1[k] > hi1 or pc2[k] < lo2 or pc2[k] > hi2: continue
        i = np.searchsorted(xe, pc1[k]) - 1; i = min(max(i, 0), K - 1)
        j = np.searchsorted(ye, pc2[k]) - 1; j = min(max(j, 0), K - 1)
        if (i, j) not in chosen: chosen[(i, j)] = []
        chosen[(i, j)].append(k)

    final = {}
    for (i, j), idxs in chosen.items():
        cell_df = df.iloc[idxs]
        # Filter for robust mesh (PC3-PC6 distance to origin)
        d36 = np.sqrt((cell_df[["PC3","PC4","PC5","PC6"]]**2).sum(axis=1))
        robust_cell = cell_df[d36 < d36.quantile(0.85)]
        if len(robust_cell) > 0: cell_df = robust_cell
        
        # Pick medoid in PC1-PC2
        c1, c2 = cell_df["PC1"].mean(), cell_df["PC2"].mean()
        dist = (cell_df["PC1"] - c1)**2 + (cell_df["PC2"] - c2)**2
        final[(i, j)] = dist.idxmin()

    fig = plt.figure(figsize=(14, 9))
    gs = gridspec.GridSpec(1, 2, width_ratios=[5.2, 1.0], wspace=0.03, figure=fig)
    ax = fig.add_subplot(gs[0])
    ax.scatter(pc1, pc2, s=5, c=OI["grey"], alpha=0.12, linewidths=0, zorder=1)

    dx = xe[1] - xe[0]; dy = ye[1] - ye[0]
    for (i, j), idx in final.items():
        row = df.loc[idx]
        img = sils[row["Objekt-ID"]]
        col = PERIOD_COLOR.get(row["Stilperiode"], SLATE)
        rgba = _period_rgb_silhouette(img, to_rgba(col)[:3])
        cx = (xe[i] + xe[i + 1]) / 2
        cy = (ye[j] + ye[j + 1]) / 2
        ax.imshow(rgba, extent=(cx-dx*0.48, cx+dx*0.48, cy-dy*0.48, cy+dy*0.48),
                  interpolation="nearest", zorder=3, aspect="auto")

    ax.set_xlim(lo1 - dx * 0.3, hi1 + dx * 0.3)
    ax.set_ylim(lo2 - dy * 0.3, hi2 + dy * 0.3)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% varians)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% varians)")
    ax.set_title("E8: Holotype-grid over morforommet (lokale optima)", loc="left", weight="bold")
    ax.grid(alpha=0.1, lw=0.4)
    ax.axhline(0, color=OI["grey"], linewidth=0.4, alpha=0.4)
    ax.axvline(0, color=OI["grey"], linewidth=0.4, alpha=0.4)

    # color legend on the side
    axL = fig.add_subplot(gs[1])
    axL.axis("off")
    ordered = [p for p in sorted(PERIOD_YEAR.keys(), key=lambda k: PERIOD_YEAR[k])
               if p in set(pers)]
    axL.text(0.0, 1.00, "Stilperiode",
             transform=axL.transAxes, fontsize=10, weight="bold", color=SLATE,
             va="top")
    for i, p in enumerate(ordered):
        y_pos = 0.95 - i * 0.045
        col = PERIOD_COLOR.get(p, OI["grey"])
        axL.scatter([0.02], [y_pos], s=55, c=[col], transform=axL.transAxes,
                    edgecolors="white", linewidths=0.8)
        axL.text(0.095, y_pos, f"{p}  ({PERIOD_YEAR[p]})",
                 transform=axL.transAxes, fontsize=7.8,
                 color=SLATE, va="center", ha="left")

    save(fig, "E8_silhouette_scatter")


# ═════════════════════════════════════════════════════════════════════
# FIG E9: Substrat-skift (materiale-signatur over tid)
# ═════════════════════════════════════════════════════════════════════
def _has_material(s, needles):
    if not isinstance(s, str):
        return False
    sl = s.lower()
    return any(k in sl for k in needles)


def fig_E9_substrat_skift(df, pca):
    """For each key material group, show how chairs with that material
    occupy PCA space across time bands."""
    groups = [
        ("Bøk/Ask (tradisjonelt treverk)",  ["bøk", "ask"]),
        ("Mahogni/Valnøtt (eksotisk trevirke)", ["mahogni", "valnøtt", "valn\u00f8tt"]),
        ("Stål/Jern/Kromstål", ["stål", "jern", "krom", "st\u00e5l"]),
        ("Plast/Akryl/Polymer", ["plast", "akryl", "poly", "pvc"]),
        ("Aluminium", ["aluminium", "alu"]),
    ]
    tbands = [(1600, 1800), (1800, 1900), (1900, 1960), (1960, 2025)]
    band_lbl = ["1600–1800", "1800–1900", "1900–1960", "1960–2025"]

    fig = plt.figure(figsize=(14, 9))
    gs = gridspec.GridSpec(len(groups), len(tbands), hspace=0.25, wspace=0.12,
                           figure=fig)

    pc1 = df["PC1"].values; pc2 = df["PC2"].values
    xlo, xhi = np.quantile(pc1, [0.005, 0.995])
    ylo, yhi = np.quantile(pc2, [0.005, 0.995])

    for gi, (gname, needles) in enumerate(groups):
        mask_mat = df["Materialar"].apply(lambda s: _has_material(s, needles))
        for bi, (y0, y1) in enumerate(tbands):
            ax = fig.add_subplot(gs[gi, bi])
            ax.scatter(pc1, pc2, s=3, c=OI["grey"], alpha=0.08, linewidths=0, zorder=1)
            mask = mask_mat & df["år"].between(y0, y1)
            sub = df[mask]
            if len(sub) > 0:
                ax.scatter(sub["PC1"], sub["PC2"], s=12, c=AMBER,
                           edgecolors=SLATE, linewidths=0.3,
                           alpha=0.9, zorder=3)
            ax.set_xlim(xlo, xhi); ax.set_ylim(ylo, yhi)
            ax.tick_params(labelsize=7)
            if gi == 0:
                ax.set_title(band_lbl[bi], fontsize=9.5, loc="center")
            if bi == 0:
                ax.set_ylabel(gname, fontsize=8.5, rotation=90, labelpad=4)
            if gi == len(groups) - 1:
                ax.set_xlabel("PC1", fontsize=8)
            else:
                ax.set_xticklabels([])
            if bi != 0:
                ax.set_yticklabels([])
            ax.text(0.97, 0.03, f"n={len(sub)}", transform=ax.transAxes,
                    fontsize=7.2, ha="right", va="bottom", color=SLATE,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.75,
                              boxstyle="round,pad=0.15"))
            ax.grid(alpha=0.08, linewidth=0.3)

    save(fig, "E9_substrat_skift")


# ═════════════════════════════════════════════════════════════════════
# FIG E10: Realiserte og uaktualiserte regionar
# ═════════════════════════════════════════════════════════════════════
def fig_E10_realiseringsgrad(df, pca):
    """Quantify how much of the morphospace is actually occupied.
    Layout:
      (a) 2D binning of PC1-PC2 + convex hull + empty interior cells
      (b) Bar: occupancy % by PC1 decile
      (c) Distribution of chair densities per cell (log scale)."""
    pc1 = df["PC1"].values; pc2 = df["PC2"].values
    xlo, xhi = np.quantile(pc1, [0.01, 0.99])
    ylo, yhi = np.quantile(pc2, [0.01, 0.99])
    xpad = (xhi - xlo) * 0.05; ypad = (yhi - ylo) * 0.05
    xlo -= xpad; xhi += xpad; ylo -= ypad; yhi += ypad

    K = 28
    xe = np.linspace(xlo, xhi, K + 1)
    ye = np.linspace(ylo, yhi, K + 1)
    H, _, _ = np.histogram2d(pc1, pc2, bins=[xe, ye])
    H = H.T  # y, x

    # convex hull of realised points
    pts = np.column_stack([pc1, pc2])
    # restrict hull to points inside display box
    inside = (pc1 >= xlo) & (pc1 <= xhi) & (pc2 >= ylo) & (pc2 <= yhi)
    hull_pts = pts[inside]
    hull = ConvexHull(hull_pts)
    hull_xy = hull_pts[hull.vertices]

    # cell centres
    xc = (xe[:-1] + xe[1:]) / 2
    yc = (ye[:-1] + ye[1:]) / 2

    # point-in-polygon test for cell centres
    from matplotlib.path import Path as mPath
    poly = mPath(np.vstack([hull_xy, hull_xy[:1]]))
    CX, CY = np.meshgrid(xc, yc)
    inside_hull = poly.contains_points(np.column_stack([CX.ravel(), CY.ravel()]))
    inside_hull = inside_hull.reshape(CY.shape)

    empty_in_hull = (H == 0) & inside_hull
    occupied = H > 0
    occ_pct_in_hull = 100 * occupied[inside_hull].mean()
    empty_pct_in_hull = 100 * empty_in_hull.sum() / max(inside_hull.sum(), 1)

    fig = plt.figure(figsize=(13, 7))
    gs = gridspec.GridSpec(2, 3, width_ratios=[2.2, 1, 1],
                           height_ratios=[1, 1], hspace=0.35, wspace=0.30,
                           figure=fig)

    # panel A: binning + hull
    axA = fig.add_subplot(gs[:, 0])
    # background: show H (log)
    Hlog = np.log1p(H)
    axA.pcolormesh(xe, ye, Hlog, cmap="Greys", shading="auto", alpha=0.85,
                   zorder=1)
    # hull boundary
    hx = np.r_[hull_xy[:, 0], hull_xy[0, 0]]
    hy = np.r_[hull_xy[:, 1], hull_xy[0, 1]]
    axA.plot(hx, hy, color=AMBER, linewidth=1.6, alpha=0.95, zorder=3,
             label="konveks innhylling")
    # empty cells inside hull
    for j in range(K):
        for i in range(K):
            if empty_in_hull[j, i]:
                axA.add_patch(Rectangle((xe[i], ye[j]),
                                        xe[i+1]-xe[i], ye[j+1]-ye[j],
                                        facecolor="none", edgecolor=OI["rust"],
                                        linewidth=0.6, linestyle="-",
                                        alpha=0.85, zorder=4))
    axA.set_xlim(xlo, xhi); axA.set_ylim(ylo, yhi)
    axA.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% varians)")
    axA.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% varians)")
    axA.set_title("(a)   raudt rutenett = uaktualisert men mogeleg", loc="left",
                  fontsize=10, weight="bold")
    axA.legend(loc="lower right", fontsize=8, frameon=False)

    # panel B: occupancy by PC1 decile
    axB = fig.add_subplot(gs[0, 1])
    deciles = np.quantile(pc1, np.linspace(0, 1, 11))
    pc1_bin = np.digitize(pc1, deciles[1:-1])
    # for each decile, compute % of PC2 cells with >=1 chair (binned in y direction)
    pct = []
    for d in range(10):
        idx = np.where(pc1_bin == d)[0]
        if len(idx) == 0:
            pct.append(0); continue
        sub_pc2 = pc2[idx]
        # bin into K cells in y
        h, _ = np.histogram(sub_pc2, bins=ye)
        pct.append(100 * (h > 0).mean())
    xs = np.arange(10)
    axB.bar(xs, pct, color=AMBER, edgecolor=SLATE, linewidth=0.5, alpha=0.85)
    axB.set_xlabel("PC1-desil")
    axB.set_ylabel("% PC2-celler okkuperte")
    axB.set_title("(b)", loc="left", fontsize=10, weight="bold")
    axB.set_xticks(xs)
    axB.set_ylim(0, 100)
    axB.grid(axis="y", alpha=0.15, linewidth=0.4)

    # panel C: log-distribution of cell counts
    axC = fig.add_subplot(gs[1, 1])
    counts = H[inside_hull]
    axC.hist(np.log10(counts + 1), bins=22, color=SLATE, alpha=0.85,
             edgecolor="white", linewidth=0.4)
    axC.axvline(0, color=OI["rust"], linewidth=1, linestyle="--", alpha=0.8,
                 label="tom celle")
    axC.set_xlabel("log10(n + 1) per celle")
    axC.set_ylabel("tal celler")
    axC.set_title("(c)", loc="left", fontsize=10, weight="bold")
    axC.legend(fontsize=7.5, frameon=False, loc="upper right")

    # panel D: summary stats
    axD = fig.add_subplot(gs[:, 2])
    axD.axis("off")
    total_cells = inside_hull.sum()
    occ_cells = occupied[inside_hull].sum()
    total_area = (xhi - xlo) * (yhi - ylo)
    hull_area = hull.volume  # ConvexHull in 2D → .volume is the area
    filled_ratio = hull_area / total_area
    lines = [
        f"N stolar         {len(df)}",
        f"Konveks areal   {hull_area:.2f}",
        f"Boks-areal       {total_area:.2f}",
        f"Hull-fyll         {filled_ratio * 100:.1f}%",
        "",
        f"Celler i hylster {int(total_cells)}",
        f"Av desse okkuperte  {int(occ_cells)}",
        f"Okkuperte %     {occ_pct_in_hull:.1f}%",
        f"Tomme %           {empty_pct_in_hull:.1f}%",
        "",
        f"Celler overalt    {K*K}",
        f"Rutenett          {K}×{K}",
    ]
    for i, line in enumerate(lines):
        axD.text(0.0, 0.96 - i * 0.07, line, transform=axD.transAxes,
                 fontsize=9.2, color=SLATE, family="monospace",
                 va="top", ha="left")
    axD.set_title("(d) nøkkeltal", loc="left", fontsize=10, weight="bold")

    save(fig, "E10_realiseringsgrad")


# ═════════════════════════════════════════════════════════════════════
# FIG E11: Stiavhengigheit — arvsavstand (H11, prop. 4.3)
# ═════════════════════════════════════════════════════════════════════
def fig_E11_stiavhengigheit(df, pca):
    """H11: for each period, compare mean distance of chairs to (a) the
    centroid of the PRECEDING period and (b) their own centroid. If
    preceding-distance > own-distance → form inherits position."""
    counts = df["Stilperiode"].value_counts()
    periods = [p for p in sorted(PERIOD_YEAR.keys(), key=lambda k: PERIOD_YEAR[k])
               if p in counts.index and counts[p] >= 12]
    pc_cols = ["PC1", "PC2", "PC3", "PC4", "PC5", "PC6"]

    centroids = {p: df[df["Stilperiode"] == p][pc_cols].mean().values for p in periods}
    overall_centroid = df[pc_cols].mean().values

    years, d_own, d_prev, d_overall = [], [], [], []
    for i, p in enumerate(periods):
        sub = df[df["Stilperiode"] == p][pc_cols].values
        own = np.linalg.norm(sub - centroids[p], axis=1).mean()
        d_own.append(own)
        d_overall.append(np.linalg.norm(sub - overall_centroid, axis=1).mean())
        if i == 0:
            d_prev.append(np.nan)
        else:
            prev_c = centroids[periods[i - 1]]
            d_prev.append(np.linalg.norm(sub - prev_c, axis=1).mean())
        years.append(PERIOD_YEAR[p])

    years = np.array(years)
    d_own = np.array(d_own)
    d_prev = np.array(d_prev)
    d_overall = np.array(d_overall)
    ratio = d_prev / d_own  # > 1 means path dependent

    fig = plt.figure(figsize=(12, 7.2))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.1, 1], hspace=0.38,
                           figure=fig)

    axA = fig.add_subplot(gs[0])
    axA.plot(years, d_own, color=SLATE, linewidth=1.8, marker="o",
             markersize=5, label="avstand til eigen sentroide")
    axA.plot(years, d_prev, color=AMBER, linewidth=1.8, marker="s",
             markersize=5, label="avstand til føregåande sentroide")
    axA.plot(years, d_overall, color=OI["grey"], linewidth=1.2,
             marker="^", markersize=4, linestyle="--",
             label="avstand til globalsentroide")
    axA.set_ylabel("snittavstand (PC1–PC6)")
    axA.set_title("(a) stol-avstand til ulike sentroidar", loc="left",
                  fontsize=10.5, weight="bold")
    axA.legend(loc="upper right", frameon=False, fontsize=8.5)
    axA.grid(alpha=0.14, linewidth=0.4)
    axA.set_xlim(min(years) - 15, max(years) + 15)

    axB = fig.add_subplot(gs[1])
    axB.bar(years, ratio, width=22, color=SLATE, alpha=0.85,
             edgecolor="white", linewidth=0.6)
    axB.axhline(1.0, color=OI["rust"], linewidth=1, linestyle="--", alpha=0.85,
                 label="terskel: 1,0")
    axB.set_xlabel("år")
    axB.set_ylabel("ratio: føregåande / eigen")
    axB.set_title("(b) verdi > 1  ⇒  stiavhengigheit (forma bur nærare si eiga periode enn den førre)",
                   loc="left", fontsize=10.5, weight="bold")
    axB.legend(loc="upper right", frameon=False, fontsize=8.5)
    axB.grid(axis="y", alpha=0.14, linewidth=0.4)
    axB.set_xlim(min(years) - 15, max(years) + 15)

    save(fig, "E11_stiavhengigheit")


# ═════════════════════════════════════════════════════════════════════
# FIG E12: Kanaliseringssignatur (H12, prop. 3.21)
# ═════════════════════════════════════════════════════════════════════
def fig_E12_kanalisering_radar(df):
    """H12: radar of z-standardised variance per axis. Canalised axes
    have systematically lower variance than non-canalised ones."""
    vals = {}
    for c in AXES:
        s = df[c]
        # z-standardise so axes are comparable
        z = (s - s.mean()) / s.std()
        vals[c] = z.std()  # = 1 for all, by construction — so use raw CV instead
    # better: coefficient of variation (σ/|μ|)
    cvs = {}
    for c in AXES:
        s = df[c]
        cvs[c] = abs(s.std() / (s.mean() + 1e-9))
    # also: within-period mean variance (pooled)
    within = {}
    for c in AXES:
        s = df[c]
        group_vars = df.groupby("Stilperiode")[c].var().dropna()
        within[c] = group_vars.mean()
    # normalise within by total variance for comparability
    between = {c: df[c].var() for c in AXES}
    within_ratio = {c: within[c] / between[c] for c in AXES}

    labels = [AXIS_LABELS_NN[c] for c in AXES]
    n = len(AXES)
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    theta += theta[:1]

    fig = plt.figure(figsize=(13.5, 6.5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1.15], wspace=0.25, figure=fig)

    # radar: coefficient of variation per axis
    ax1 = fig.add_subplot(gs[0], projection="polar")
    vals1 = [cvs[c] for c in AXES] + [cvs[AXES[0]]]
    ax1.plot(theta, vals1, color=SLATE, linewidth=1.8)
    ax1.fill(theta, vals1, color=SLATE, alpha=0.22)
    ax1.set_xticks(theta[:-1])
    ax1.set_xticklabels(labels, fontsize=8.5)
    ax1.set_title("(a) variasjonskoeffisient CV = σ/|μ|  per akse",
                   fontsize=10.2, loc="left", weight="bold", pad=18)
    ax1.grid(alpha=0.3)

    # bar: within / total variance ratio
    ax2 = fig.add_subplot(gs[1])
    order = sorted(AXES, key=lambda c: within_ratio[c])
    xs = np.arange(len(order))
    vals2 = [within_ratio[c] for c in order]
    cols = [AMBER if within_ratio[c] < 0.4 else SLATE for c in order]
    ax2.barh(xs, vals2, color=cols, edgecolor="white", linewidth=0.5,
             alpha=0.88)
    ax2.set_yticks(xs)
    ax2.set_yticklabels([AXIS_LABELS_NN[c] for c in order], fontsize=9)
    ax2.axvline(0.4, color=OI["rust"], linestyle="--", linewidth=0.9,
                 alpha=0.8, label="kanaliseringsterskel 0,4")
    ax2.set_xlabel("innan-stilperiode-varians / total-varians")
    ax2.set_title("(b) små verdiar = kanaliserte (fanga av kompromisset)",
                   loc="left", fontsize=10.2, weight="bold")
    ax2.legend(loc="lower right", frameon=False, fontsize=8)
    ax2.set_xlim(0, max(vals2) * 1.15)
    ax2.grid(axis="x", alpha=0.14, linewidth=0.4)

    save(fig, "E12_kanalisering_radar")


# ═════════════════════════════════════════════════════════════════════
# FIG E13: Punktert likevekt mot nullmodell (H13, prop. 4.2, 4.11)
# ═════════════════════════════════════════════════════════════════════
def fig_E13_punktuert_likevekt(df, pca, n_perm=200):
    """H13: rolling centroid derivative with material-revolution markers,
    compared to permutation null (shuffle years, keep geometry)."""
    df = df.sort_values("år").copy()
    yrs = df["år"].values
    pc = df[["PC1", "PC2"]].values

    y0, y1 = 1500, 2025
    window = 30; step = 5
    centers = np.arange(y0 + window // 2, y1 - window // 2 + 1, step)

    def rolling_deriv(yr_vec, pc_vec):
        cxs = []
        for c in centers:
            m = (yr_vec >= c - window / 2) & (yr_vec <= c + window / 2)
            if m.sum() < 5:
                cxs.append(np.full(2, np.nan))
            else:
                cxs.append(pc_vec[m].mean(axis=0))
        cxs = np.array(cxs)
        d = np.linalg.norm(np.diff(cxs, axis=0), axis=1)
        return np.concatenate([[np.nan], d])

    real = rolling_deriv(yrs, pc)
    rng = np.random.default_rng(0)
    null = np.full((n_perm, len(centers)), np.nan)
    for i in range(n_perm):
        shuffled_yr = rng.permutation(yrs)
        null[i] = rolling_deriv(shuffled_yr, pc)
    # null band: 2.5–97.5 percentiles across perms (ignore NaNs)
    lo = np.nanpercentile(null, 2.5, axis=0)
    hi = np.nanpercentile(null, 97.5, axis=0)
    med = np.nanmedian(null, axis=0)

    fig = plt.figure(figsize=(13.5, 6.3))
    ax = fig.add_subplot(111)
    ax.fill_between(centers, lo, hi,
                     color=OI["grey"], alpha=0.22,
                     label="nullmodell 95% (år permutert)")
    ax.plot(centers, med, color=OI["grey"], linewidth=0.9,
             alpha=0.7, label="nullmodell median")
    ax.plot(centers, real, color=OI["rust"], linewidth=1.8,
             label="observert ‖Δsentroide‖")

    # annotate material revolutions
    revs = [
        (1680, "barokk-konsolidering"),
        (1760, "industrielt maskineri"),
        (1830, "dampbøying (Thonet)"),
        (1925, "stålrør (Breuer, Mies)"),
        (1955, "skumgummi + polyuretan"),
        (1970, "plast-støyping"),
    ]
    ymax = np.nanmax(real) * 1.15
    for y_rev, lbl in revs:
        ax.axvline(y_rev, color=SLATE, linewidth=0.7, linestyle=":",
                    alpha=0.7)
        ax.text(y_rev, ymax * 0.96, lbl, rotation=90, fontsize=7.5,
                 color=SLATE, ha="right", va="top", alpha=0.8)

    ax.set_xlabel("år")
    ax.set_ylabel("‖Δsentroide‖ per 5-års-steg")
    ax.set_ylim(0, ymax)
    ax.set_xlim(y0, y1)
    ax.grid(alpha=0.12, linewidth=0.4)
    ax.legend(loc="upper left", frameon=False, fontsize=8.8)
    save(fig, "E13_punktuert_likevekt")


# ═════════════════════════════════════════════════════════════════════
# FIG E14: Agent-hierarki (H14, prop. 6.12)
# ═════════════════════════════════════════════════════════════════════
def fig_E14_agent_hierarki(df):
    """H14: intra-period Mahalanobis spread for handverk vs. industri era.
    Higher agent (organisation/market) absorbs variance → smaller spread."""
    pre = df[(df["år"] < 1850) & df["år"].notna()].copy()
    post = df[(df["år"] >= 1950) & df["år"].notna()].copy()
    mid = df[(df["år"] >= 1850) & (df["år"] < 1950) & df["år"].notna()].copy()

    pc_cols = ["PC1", "PC2", "PC3", "PC4", "PC5", "PC6"]

    def mahalanobis_spread(sub):
        if len(sub) < 6:
            return np.nan
        X = sub[pc_cols].values
        cov = np.cov(X.T)
        try:
            inv = np.linalg.inv(cov + np.eye(len(pc_cols)) * 1e-6)
        except np.linalg.LinAlgError:
            return np.nan
        mu = X.mean(axis=0)
        d = np.sqrt(np.einsum("ij,jk,ik->i", X - mu, inv, X - mu))
        return d.mean()

    # per-period spreads
    def periods_of(sub):
        return sub["Stilperiode"].value_counts().loc[lambda s: s >= 10].index

    rows = []
    for label, sub, col in [("handverk (før 1850)", pre, SLATE),
                             ("overgang (1850–1950)", mid, OI["grey"]),
                             ("industri (etter 1950)", post, AMBER)]:
        for p in periods_of(sub):
            g = sub[sub["Stilperiode"] == p]
            s = mahalanobis_spread(g)
            if np.isnan(s):
                continue
            rows.append(dict(grp=label, period=p, spread=s, n=len(g), col=col,
                             year=PERIOD_YEAR.get(p, 1900)))
    rows_df = pd.DataFrame(rows)

    fig = plt.figure(figsize=(12.5, 7.5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1.4, 1.0], wspace=0.28,
                           figure=fig)

    ax1 = fig.add_subplot(gs[0])
    for g, sub_rows in rows_df.groupby("grp"):
        col = sub_rows["col"].iloc[0]
        ax1.scatter(sub_rows["year"], sub_rows["spread"],
                    s=40 + sub_rows["n"] * 0.6, c=[col], alpha=0.85,
                    edgecolors="white", linewidths=0.8, label=g)
    ax1.set_xlabel("år (stilperiode-midtpunkt)")
    ax1.set_ylabel("gjennomsnittleg intra-periode Mahalanobis-spreiing")
    ax1.set_title("(a) spreiing per stilperiode, etter agent-skala",
                   loc="left", fontsize=10.2, weight="bold")
    ax1.grid(alpha=0.14, linewidth=0.4)
    ax1.legend(loc="upper right", frameon=False, fontsize=8.5)

    ax2 = fig.add_subplot(gs[1])
    groups = ["handverk (før 1850)", "overgang (1850–1950)", "industri (etter 1950)"]
    data = [rows_df[rows_df["grp"] == g]["spread"].values for g in groups]
    cols = [SLATE, OI["grey"], AMBER]
    parts = ax2.boxplot(data, tick_labels=groups, patch_artist=True, widths=0.55)
    for patch, col in zip(parts["boxes"], cols):
        patch.set_facecolor(to_rgba(col, 0.6))
        patch.set_edgecolor(SLATE)
    for m in parts["medians"]:
        m.set_color(OI["rust"])
        m.set_linewidth(1.5)
    ax2.set_ylabel("Mahalanobis-spreiing")
    ax2.set_title("(b) aggregert over grupper",
                   loc="left", fontsize=10.2, weight="bold")
    ax2.grid(axis="y", alpha=0.14, linewidth=0.4)
    for lbl in ax2.get_xticklabels():
        lbl.set_rotation(0); lbl.set_fontsize(9)
    save(fig, "E14_agent_hierarki")


# ═════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════
def main():
    print("[1/15] loading data...")
    df = load_data()

    # Material classification for evolutionary analysis
    def classify(m):
        m = str(m).lower()
        if any(x in m for x in ["stål", "st\u00e5l", "jern", "krom", "metall"]): return "metal"
        if any(x in m for x in ["plast", "akryl", "poly", "pvc", "fiberglas"]): return "plastic"
        if any(x in m for x in ["bøk", "b\u00f8k", "ask", "mahogni", "valnøtt", "valn\u00f8tt", "eik", "furu", "bjørk", "bj\u00f8rk", "tre"]): return "wood"
        return "other"
    df["mat_class"] = df["Materialar"].apply(classify)

    print("[2/15] fitting PCA on 6 standardised axes (alle med geometri)...")
    df, pca, scaler = fit_pca(df)
    print(f"  explained var: {pca.explained_variance_ratio_.round(3)}")
    print(f"  cumulative:    {np.cumsum(pca.explained_variance_ratio_).round(3)}")

    print("[3/15] building silhouette cache (lazy, parallel)...")
    sils = build_silhouette_cache(df["Objekt-ID"].tolist())

    print("[4/15] E1 morforom...")
    fig_E1_morforom_pca(df, pca)

    print("[5/15] E2 mesh-grid (Holotype Grid refinement)...")
    # Updated E2 will use the improved selection logic
    fig_E2_mesh_grid(df, pca, sils)

    df_yr = df[df["år"].notna()].copy()
    print(f"  (time-aware figures use {len(df_yr)} chairs with year)")

    print("[6/15] E3 landskap over tid...")
    fig_E3_landskap_tid(df_yr, pca)

    print("[7/15] E4 kanalisering...")
    fig_E4_kanalisering(df_yr)

    print("[8/15] E5 stase og brot...")
    fig_E5_stase_brot(df_yr, pca)

    print("[9/15] E6 giga-grid (alle silhuettar)...")
    fig_E6_giga_grid(df_yr, sils, mode="year")
    fig_E6_giga_grid(df, sils, mode="pc1")
    fig_E6_legend()

    print("[10/15] E7 morforom-trajektorie (split wood/metal + OU)...")
    fig_E7_trajektorie_split(df_yr, pca)

    print("[11/15] E8 silhuett-scatter i PCA (Holotype refinement)...")
    fig_E8_silhouette_scatter(df, pca, sils, n_show=260)

    print("[12/15] E9 substrat-skift over tid...")
    fig_E9_substrat_skift(df_yr, pca)

    print("[13/18] E10 realiseringsgrad...")
    fig_E10_realiseringsgrad(df, pca)

    print("[14/18] E11 stiavhengigheit (H11)...")
    fig_E11_stiavhengigheit(df_yr, pca)

    print("[15/18] E15 Lande-likning og evolusjonær respons...")
    fig_E15_lande_prediction(df_yr, pca)

    print("[16/18] E12 kanalisering radar (H12)...")
    fig_E12_kanalisering_radar(df)

    print("[17/18] E13 punktuert likevekt (H13)...")
    fig_E13_punktuert_likevekt(df_yr, pca)

    print("[18/18] E14 agent-hierarki (H14)...")
    fig_E14_agent_hierarki(df_yr)

    for t in ("_sil_test.png", "_sil_test2.png", "_fonttest.png"):
        p = os.path.join(OUT, t)
        if os.path.exists(p):
            os.remove(p)

    print("\nDone.")


if __name__ == "__main__":
    main()
