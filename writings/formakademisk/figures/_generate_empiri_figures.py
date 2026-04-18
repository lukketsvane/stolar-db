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


def _silhouette_is_pretty(img):
    """Quality filter: reject silhouettes that are too thin, too sparse,
    too fragmented, or have extreme aspect ratio for a chair."""
    if img is None:
        return False
    H, W = img.shape
    area = int(img.sum())
    if area < 0.08 * H * W:
        return False
    if area > 0.75 * H * W:
        return False
    rows = np.any(img, axis=1)
    cols = np.any(img, axis=0)
    if not rows.any() or not cols.any():
        return False
    r0 = int(np.argmax(rows)); r1 = H - 1 - int(np.argmax(rows[::-1]))
    c0 = int(np.argmax(cols)); c1 = W - 1 - int(np.argmax(cols[::-1]))
    bh = r1 - r0 + 1
    bw = c1 - c0 + 1
    if bh < 0.40 * H:
        return False
    if bw < 0.22 * W:
        return False
    ar = bh / max(bw, 1)
    if ar < 0.60 or ar > 2.6:
        return False
    fill = area / (bh * bw)
    if fill < 0.28 or fill > 0.92:
        return False
    from scipy.ndimage import label as _label
    _, ncomp = _label(img)
    if ncomp > 3:
        return False
    return True


def pretty_silhouette_mask(sils):
    """Return the set of oids whose silhouette passes the beauty filter."""
    return {oid for oid, img in sils.items() if _silhouette_is_pretty(img)}


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

    pretty = pretty_silhouette_mask(sils)
    print(f"  E2 pretty silhouettes: {len(pretty)}/{len(sils)}")

    cells = {}
    dx = xs[1] - xs[0]; dy = ys[1] - ys[0]

    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            mask = (pc1 >= x - dx / 2) & (pc1 < x + dx / 2) & \
                   (pc2 >= y - dy / 2) & (pc2 < y + dy / 2)
            cell_df = df[mask]
            if len(cell_df) == 0:
                continue
            # keep only chairs with a pretty silhouette
            cell_df = cell_df[cell_df["Objekt-ID"].isin(pretty)]
            if len(cell_df) == 0:
                continue
            # Trim extreme PC3-PC6 outliers (weird poses)
            pc36_dist = np.sqrt((cell_df[["PC3", "PC4", "PC5", "PC6"]] ** 2).sum(axis=1))
            robust_df = cell_df[pc36_dist < pc36_dist.quantile(0.85)]
            if len(robust_df) > 0:
                cell_df = robust_df
            # Medoid: chair closest to the cell's own centroid
            c1, c2 = cell_df["PC1"].mean(), cell_df["PC2"].mean()
            dist = (cell_df["PC1"] - c1) ** 2 + (cell_df["PC2"] - c2) ** 2
            best_idx = dist.idxmin()
            oid = df.loc[best_idx, "Objekt-ID"]
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
    Landé (1979) breeder's equation applied to chair evolution.
    G-matrix of the wood ancestral population, beta (selection gradient)
    pointing away from the steel/plastic centroid. Predicted vs observed
    response of the 1920-onwards population.
    """
    df_pre = df[(df["mat_class"] == "wood") & (df["år"] < 1920)]
    df_post = df[(df["mat_class"] == "wood") & (df["år"] >= 1920)]
    df_metal = df[df["mat_class"].isin(["metal", "plastic"])]

    if len(df_pre) < 15 or len(df_post) < 15 or len(df_metal) < 15:
        print("  skipping E15: insufficient samples")
        return

    pcs = ["PC1", "PC2"]
    G = df_pre[pcs].cov().values
    metal_c = df_metal[pcs].mean().values
    pre_c = df_pre[pcs].mean().values
    beta = pre_c - metal_c
    beta_norm = np.linalg.norm(beta)
    if beta_norm < 1e-6:
        print("  skipping E15: degenerate beta")
        return
    beta /= beta_norm
    delta_z_pred = G @ beta
    delta_z_obs = df_post[pcs].mean().values - pre_c

    # robust axis limits based on all data
    all_pc1 = df["PC1"].values
    all_pc2 = df["PC2"].values
    x_lo, x_hi = np.quantile(all_pc1, [0.01, 0.99])
    y_lo, y_hi = np.quantile(all_pc2, [0.01, 0.99])
    x_pad = (x_hi - x_lo) * 0.05
    y_pad = (y_hi - y_lo) * 0.05
    x_lo -= x_pad; x_hi += x_pad; y_lo -= y_pad; y_hi += y_pad

    fig = plt.figure(figsize=(13.5, 6.8))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1], wspace=0.24, figure=fig)

    axA = fig.add_subplot(gs[0])
    axA.scatter(all_pc1, all_pc2, s=3, c=OI["grey"], alpha=0.12, zorder=1,
                linewidths=0)
    axA.scatter(df_pre["PC1"], df_pre["PC2"], s=14, c=AMBER, alpha=0.45,
                edgecolors="none", label=f"tre, pre-1920 (n={len(df_pre)})",
                zorder=2)
    axA.scatter(df_metal["PC1"], df_metal["PC2"], s=14, c=OI["blue"],
                alpha=0.35, edgecolors="none",
                label=f"stål/plast (n={len(df_metal)})", zorder=2)

    vals, vecs = np.linalg.eigh(G)
    order = vals.argsort()[::-1]; vals = vals[order]; vecs = vecs[:, order]
    theta = np.degrees(np.arctan2(vecs[1, 0], vecs[0, 0]))
    width, height = 2 * np.sqrt(np.maximum(vals, 1e-12))
    for sig in [1, 2]:
        ell = Ellipse(xy=pre_c, width=sig * width, height=sig * height,
                      angle=theta, edgecolor=AMBER, facecolor="none",
                      lw=1.2, alpha=0.85 / sig, linestyle="--", zorder=4)
        axA.add_patch(ell)

    beta_arrow_len = min((x_hi - x_lo), (y_hi - y_lo)) * 0.18
    axA.annotate("", xy=pre_c + beta * beta_arrow_len,
                 xytext=tuple(pre_c),
                 arrowprops=dict(arrowstyle="-|>", color=OI["blue"],
                                 lw=2.2, mutation_scale=20), zorder=10)
    axA.text(*(pre_c + beta * beta_arrow_len * 1.10),
             r"$\beta$", color=OI["blue"], weight="bold",
             ha="center", va="center", fontsize=11,
             bbox=dict(facecolor="white", edgecolor="none", alpha=0.8,
                       boxstyle="round,pad=0.15"))
    axA.scatter(*pre_c, s=140, c=AMBER, edgecolors="white",
                linewidths=1.4, zorder=11)
    axA.set_xlim(x_lo, x_hi); axA.set_ylim(y_lo, y_hi)
    axA.set_title("(a) G-matrise (1σ, 2σ ellipsar) og seleksjonsgradient β",
                  loc="left", weight="bold", fontsize=10.5)
    axA.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
    axA.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
    axA.legend(loc="upper right", fontsize=8, frameon=False)
    axA.grid(alpha=0.12, linewidth=0.4)

    axB = fig.add_subplot(gs[1])
    axB.scatter(all_pc1, all_pc2, s=3, c=OI["grey"], alpha=0.12, zorder=1,
                linewidths=0)
    axB.scatter(df_pre["PC1"], df_pre["PC2"], s=12, c=AMBER, alpha=0.30,
                edgecolors="none", label="tre, pre-1920")
    axB.scatter(df_post["PC1"], df_post["PC2"], s=18, c=OI["rust"], alpha=0.55,
                edgecolors="none", label=f"tre, post-1920 (n={len(df_post)})")
    # Scale the predicted arrow so it is comparable in visual length
    obs_norm = np.linalg.norm(delta_z_obs)
    pred_norm = np.linalg.norm(delta_z_pred)
    scale = obs_norm / max(pred_norm, 1e-9)
    axB.annotate("", xy=pre_c + delta_z_pred * scale,
                 xytext=tuple(pre_c),
                 arrowprops=dict(arrowstyle="-|>", color=SLATE,
                                 lw=2.2, mutation_scale=20), zorder=10)
    axB.annotate("", xy=pre_c + delta_z_obs,
                 xytext=tuple(pre_c),
                 arrowprops=dict(arrowstyle="-|>", color=OI["rust"],
                                 lw=2.2, mutation_scale=20), zorder=10)
    axB.scatter(*pre_c, s=140, c=AMBER, edgecolors="white",
                linewidths=1.4, zorder=11)
    axB.scatter(*(pre_c + delta_z_obs), s=140, c=OI["rust"],
                edgecolors="white", linewidths=1.4, zorder=11)
    # angular agreement
    cosang = float(np.dot(delta_z_pred / (pred_norm + 1e-9),
                          delta_z_obs / (obs_norm + 1e-9)))
    ang_deg = float(np.degrees(np.arccos(np.clip(cosang, -1, 1))))
    txt = (f"‖Δz_pred‖ = {pred_norm:.3f}\n"
           f"‖Δz_obs‖  = {obs_norm:.3f}\n"
           f"vinkel(pred, obs) = {ang_deg:.1f}°\n"
           f"cos(pred, obs) = {cosang:.2f}")
    axB.text(0.02, 0.98, txt, transform=axB.transAxes,
             fontsize=8.5, color=SLATE, va="top", ha="left",
             family="monospace",
             bbox=dict(facecolor="white", edgecolor="none",
                       alpha=0.85, boxstyle="round,pad=0.28"))
    # dummy legend entries
    axB.plot([], [], color=SLATE, lw=2, label="predikert $\\Delta\\bar z = Gβ$")
    axB.plot([], [], color=OI["rust"], lw=2, label="observert $\\Delta\\bar z$")
    axB.set_xlim(x_lo, x_hi); axB.set_ylim(y_lo, y_hi)
    axB.set_title("(b) predikert vs. observert respons",
                  loc="left", weight="bold", fontsize=10.5)
    axB.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
    axB.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
    axB.legend(loc="upper right", fontsize=8, frameon=False)
    axB.grid(alpha=0.12, linewidth=0.4)

    save(fig, "E15_lande_prediction")


# FIG E7 SPLIT: Morforom-trajektorie separert på materiale (wood / metal / plastic)
# ═════════════════════════════════════════════════════════════════════
def fig_E7_trajektorie_split(df, pca):
    """Three-panel trajectory: wood, metal, plastic. Arrows connect
    40-year bins; a star marks the Ornstein-Uhlenbeck adaptive optimum θ
    (estimated as the mean of the last three bins)."""
    fig = plt.figure(figsize=(14.5, 6.2))
    gs = gridspec.GridSpec(1, 3, wspace=0.22, figure=fig)

    all_pc1 = df["PC1"].values; all_pc2 = df["PC2"].values
    x_lo, x_hi = np.quantile(all_pc1, [0.01, 0.99])
    y_lo, y_hi = np.quantile(all_pc2, [0.01, 0.99])
    x_pad = (x_hi - x_lo) * 0.05; y_pad = (y_hi - y_lo) * 0.05
    x_lo -= x_pad; x_hi += x_pad; y_lo -= y_pad; y_hi += y_pad

    def get_traj(sub):
        yr_bins = np.arange(1500, 2040, 40)
        res = []
        for i in range(len(yr_bins) - 1):
            mask = (sub["år"] >= yr_bins[i]) & (sub["år"] < yr_bins[i + 1])
            chunk = sub[mask]
            if len(chunk) >= 5:
                res.append({
                    "year": yr_bins[i] + 20,
                    "cx": chunk["PC1"].mean(),
                    "cy": chunk["PC2"].mean(),
                    "sex": chunk["PC1"].std() / np.sqrt(len(chunk)),
                    "sey": chunk["PC2"].std() / np.sqrt(len(chunk)),
                    "n": len(chunk),
                })
        return pd.DataFrame(res)

    groups = [
        ("wood",    "tre (bøk/ask/mahogni)", AMBER),
        ("metal",   "stål / jern / krom",    OI["blue"]),
        ("plastic", "plast / akryl / poly",  OI["rust"]),
    ]

    for i, (mcls, title, col) in enumerate(groups):
        ax = fig.add_subplot(gs[i])
        ax.scatter(all_pc1, all_pc2, s=3, c=OI["grey"], alpha=0.10,
                   linewidths=0, zorder=1)

        sub = df[df["mat_class"] == mcls]
        traj = get_traj(sub)
        n_mat = len(sub)

        if len(traj) >= 2:
            # arrows coloured along the trajectory (dark → light)
            cmap = LinearSegmentedColormap.from_list(
                f"traj_{mcls}",
                [SLATE, col, "white"],
                N=max(len(traj) - 1, 2))
            for j in range(len(traj) - 1):
                arrow_col = cmap(j / max(len(traj) - 2, 1))
                ax.annotate("",
                            xy=(traj.iloc[j + 1]["cx"], traj.iloc[j + 1]["cy"]),
                            xytext=(traj.iloc[j]["cx"], traj.iloc[j]["cy"]),
                            arrowprops=dict(arrowstyle="-|>", color=arrow_col,
                                            lw=1.9, alpha=0.92,
                                            mutation_scale=15),
                            zorder=4)
            # numbered nodes
            for j, row_ in traj.iterrows():
                ax.errorbar(row_["cx"], row_["cy"],
                            xerr=row_["sex"], yerr=row_["sey"],
                            ecolor=to_rgba(col, 0.4),
                            elinewidth=0.9, capsize=2, zorder=3)
                ax.scatter([row_["cx"]], [row_["cy"]],
                           s=90, c=[col], edgecolors="white",
                           linewidths=1.1, zorder=5)
                ax.text(row_["cx"], row_["cy"], str(j + 1),
                        ha="center", va="center",
                        fontsize=7.4, color="white", weight="bold", zorder=6)
            # OU attractor θ
            theta_x = traj.iloc[-3:]["cx"].mean()
            theta_y = traj.iloc[-3:]["cy"].mean()
            ax.scatter([theta_x], [theta_y], marker="*", s=340,
                       color=col, edgecolors=SLATE, linewidths=0.9,
                       label="OU θ (adaptiv topp)", zorder=8)

        ax.set_xlim(x_lo, x_hi); ax.set_ylim(y_lo, y_hi)
        ax.set_title(f"{title}    n = {n_mat}",
                     loc="left", weight="bold", fontsize=10.2)
        ax.set_xlabel(f"PC1")
        if i == 0:
            ax.set_ylabel(f"PC2")
        ax.grid(alpha=0.12, linewidth=0.4)
        ax.axhline(0, color=OI["grey"], linewidth=0.5, alpha=0.4)
        ax.axvline(0, color=OI["grey"], linewidth=0.5, alpha=0.4)
        if len(traj) >= 2:
            ax.legend(loc="upper right", fontsize=8, frameon=False)

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

    # Only consider chairs whose silhouette passes the beauty filter
    pretty = pretty_silhouette_mask(sils)
    print(f"  E8 pretty silhouettes: {len(pretty)}/{len(sils)}")

    chosen = {}
    for k in range(len(df)):
        if oids[k] not in pretty:
            continue
        if pc1[k] < lo1 or pc1[k] > hi1 or pc2[k] < lo2 or pc2[k] > hi2:
            continue
        i = np.searchsorted(xe, pc1[k]) - 1; i = min(max(i, 0), K - 1)
        j = np.searchsorted(ye, pc2[k]) - 1; j = min(max(j, 0), K - 1)
        chosen.setdefault((i, j), []).append(k)

    final = {}
    for (i, j), idxs in chosen.items():
        cell_df = df.iloc[idxs]
        # prefer chairs closest to PC3-PC6 origin (typical shapes)
        d36 = np.sqrt((cell_df[["PC3", "PC4", "PC5", "PC6"]] ** 2).sum(axis=1))
        robust_cell = cell_df[d36 < d36.quantile(0.85)]
        if len(robust_cell) > 0:
            cell_df = robust_cell
        c1, c2 = cell_df["PC1"].mean(), cell_df["PC2"].mean()
        dist = (cell_df["PC1"] - c1) ** 2 + (cell_df["PC2"] - c2) ** 2
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
# FIG E16: Morfologisk nyskaping over tid (novelty distance)
# ═════════════════════════════════════════════════════════════════════
def fig_E16_morfologisk_nyskaping(df, pca, sils=None):
    """For each chair, compute the minimum 6D distance in PC-space to
    ANY chair that existed before its year. This is the 'morphological
    novelty' at birth. Directly analogous to stratigraphic novelty indices
    in paleobiology (Foote 1997, Ciampaglio 2002).

    Peaks in the per-year max reveal innovation bursts that the observed
    record would not produce under a Brownian-motion null."""
    df = df[df["år"].notna()].copy()
    df = df.sort_values("år").reset_index(drop=True)
    pc_cols = ["PC1", "PC2", "PC3", "PC4", "PC5", "PC6"]
    X = df[pc_cols].values
    yrs = df["år"].values

    N = len(df)
    novelty = np.full(N, np.nan)
    for i in range(N):
        prior = yrs < yrs[i]
        if not prior.any():
            continue
        d = np.linalg.norm(X[prior] - X[i], axis=1)
        novelty[i] = d.min()

    df["novelty"] = novelty

    # Rolling max and mean per 10-year window
    years_grid = np.arange(int(np.nanmin(yrs)), int(np.nanmax(yrs)) + 1, 5)
    med = []; p90 = []; n_in = []
    for yr in years_grid:
        m = (yrs >= yr - 15) & (yrs <= yr + 15)
        if m.sum() < 3:
            med.append(np.nan); p90.append(np.nan); n_in.append(m.sum())
        else:
            v = novelty[m]
            v = v[~np.isnan(v)]
            if len(v) == 0:
                med.append(np.nan); p90.append(np.nan); n_in.append(0)
            else:
                med.append(np.median(v))
                p90.append(np.quantile(v, 0.90))
                n_in.append(len(v))
    med = np.array(med); p90 = np.array(p90); n_in = np.array(n_in)

    # Brownian null: shuffle years, recompute novelty statistic
    rng = np.random.default_rng(0)
    n_perm = 80
    null_p90 = np.full((n_perm, len(years_grid)), np.nan)
    for p in range(n_perm):
        shuf_yr = rng.permutation(yrs)
        nov_s = np.full(N, np.nan)
        ord_ = np.argsort(shuf_yr)
        Xs = X[ord_]
        ys = shuf_yr[ord_]
        for i in range(1, N):
            d = np.linalg.norm(Xs[:i] - Xs[i], axis=1)
            nov_s[ord_[i]] = d.min()
        for gi, yr in enumerate(years_grid):
            m = (shuf_yr >= yr - 15) & (shuf_yr <= yr + 15)
            v = nov_s[m]
            v = v[~np.isnan(v)]
            if len(v) >= 3:
                null_p90[p, gi] = np.quantile(v, 0.90)
    null_hi = np.nanpercentile(null_p90, 95, axis=0)
    null_med = np.nanmedian(null_p90, axis=0)

    # Identify chairs with the highest novelty for labeling
    top_idx = np.argsort(novelty)[-12:][::-1]
    top_chairs = df.iloc[top_idx][["år", "Stilperiode", "Namn", "PC1", "PC2",
                                   "novelty", "Objekt-ID"]].copy()

    fig = plt.figure(figsize=(13.5, 8.5))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.1, 1], hspace=0.32,
                           figure=fig)

    # --- (a) novelty trajectory with null band ---
    ax = fig.add_subplot(gs[0])
    ax.fill_between(years_grid, 0, null_hi, color=OI["grey"], alpha=0.22,
                     label="nullmodell 95% (år permuterte)")
    ax.plot(years_grid, null_med, color=OI["grey"], lw=0.9, alpha=0.7,
             label="nullmodell median")
    ax.plot(years_grid, p90, color=OI["rust"], lw=1.9,
             label="observert 90%-perc nyskapingsavstand")
    ax.plot(years_grid, med, color=SLATE, lw=1.4, alpha=0.85,
             label="observert median")
    # mark top-12 individual chairs
    ax.scatter(df.iloc[top_idx]["år"], df.iloc[top_idx]["novelty"],
                s=60, c=OI["rust"], edgecolors="white", linewidths=0.9,
                zorder=5, label="top-12 individuelle innovatørar")
    ax.set_xlabel("år")
    ax.set_ylabel("morfologisk nyskapingsavstand (PC1–PC6)")
    ax.set_title("(a) minimum-avstand til prior stol gjennom tid",
                  loc="left", weight="bold", fontsize=10.5)
    ax.grid(alpha=0.12, linewidth=0.4)
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.set_xlim(years_grid.min(), years_grid.max())

    # --- (b) top-12 individual innovator labels ---
    axB = fig.add_subplot(gs[1])
    axB.axis("off")
    axB.text(0.0, 1.00,
             "Dei mest morfologisk isolerte stolane i datasettet  "
             "(største avstand til alle tidlegare)",
             transform=axB.transAxes, fontsize=10.5, weight="bold",
             color=SLATE, va="top")
    # build a small table with 3 columns
    top_chairs = top_chairs.reset_index(drop=True)
    n_rows = (len(top_chairs) + 2) // 3
    for k, row_ in top_chairs.iterrows():
        col_idx = k // n_rows
        row_idx = k % n_rows
        xp = 0.01 + col_idx * 0.34
        yp = 0.88 - row_idx * (0.88 / max(n_rows, 1))
        nm = str(row_.get("Namn", ""))[:35]
        per = str(row_.get("Stilperiode", ""))[:20]
        txt = (f"{int(row_['år'])}  ·  {per}\n"
               f"{nm}\n"
               f"nyskaping = {row_['novelty']:.2f}")
        axB.text(xp, yp, txt, transform=axB.transAxes, fontsize=8.4,
                 color=SLATE, va="top", ha="left",
                 bbox=dict(facecolor=to_rgba(AMBER, 0.18),
                           edgecolor=to_rgba(AMBER, 0.5),
                           linewidth=0.4, boxstyle="round,pad=0.28"))

    save(fig, "E16_morfologisk_nyskaping")


# ═════════════════════════════════════════════════════════════════════
# FIG E17: Disparity Through Time (Foote 1993)
# ═════════════════════════════════════════════════════════════════════
def fig_E17_disparity_through_time(df, pca, n_perm=120):
    """Foote (1993): at each time slice, compute mean pairwise distance
    between contemporary forms. Compare to a Brownian-motion null where
    the same chairs have their years permuted. Peaks above the null band =
    adaptive radiation (many divergent forms at once); troughs = consolidation."""
    df = df[df["år"].notna()].copy()
    yrs = df["år"].values
    pc_cols = ["PC1", "PC2", "PC3", "PC4", "PC5", "PC6"]
    X = df[pc_cols].values

    years_grid = np.arange(1550, 2025, 10)
    window = 40

    def disparity(yr_vec):
        out = np.full(len(years_grid), np.nan)
        for gi, yr in enumerate(years_grid):
            m = (yr_vec >= yr - window / 2) & (yr_vec <= yr + window / 2)
            idx = np.where(m)[0]
            if len(idx) < 6:
                continue
            sub = X[idx]
            # mean pairwise distance (no self pairs)
            dmat = np.linalg.norm(sub[:, None, :] - sub[None, :, :], axis=-1)
            n = len(idx)
            out[gi] = dmat.sum() / (n * (n - 1))
        return out

    real = disparity(yrs)
    rng = np.random.default_rng(0)
    null = np.full((n_perm, len(years_grid)), np.nan)
    for i in range(n_perm):
        null[i] = disparity(rng.permutation(yrs))
    lo = np.nanpercentile(null, 2.5, axis=0)
    hi = np.nanpercentile(null, 97.5, axis=0)
    med = np.nanmedian(null, axis=0)

    # sample size per window
    nwin = np.array([
        ((yrs >= yr - window / 2) & (yrs <= yr + window / 2)).sum()
        for yr in years_grid
    ])

    fig = plt.figure(figsize=(13.5, 7))
    gs = gridspec.GridSpec(2, 1, height_ratios=[2.1, 1.0], hspace=0.22,
                           figure=fig)

    ax = fig.add_subplot(gs[0])
    ax.fill_between(years_grid, lo, hi, color=OI["grey"], alpha=0.22,
                     label="Brownian null 95%")
    ax.plot(years_grid, med, color=OI["grey"], lw=0.9, alpha=0.7,
             label="Brownian null median")
    ax.plot(years_grid, real, color=OI["rust"], lw=2.1,
             label="observert disparitet")
    # shade regions where observed > null hi (radiation) and < null lo (constraint)
    ax.fill_between(years_grid, real, hi,
                     where=(real > hi), alpha=0.3, color=AMBER, zorder=2,
                     label="over nullbandet (radiasjon)")
    ax.fill_between(years_grid, real, lo,
                     where=(real < lo), alpha=0.35, color=OI["blue"], zorder=2,
                     label="under nullbandet (stase/konsolidering)")
    # material revolutions
    for y_rev, lbl in [(1680, "barokk-konsolidering"),
                        (1830, "industriell revolusjon"),
                        (1925, "stålrør"),
                        (1970, "plast-støyping")]:
        ax.axvline(y_rev, color=SLATE, linewidth=0.7, linestyle=":", alpha=0.7)
        ax.text(y_rev + 2, ax.get_ylim()[1] * 0.02 if False else 0,
                 "", fontsize=7)
    ax.set_xlabel("år")
    ax.set_ylabel("gjennomsnittleg parvis avstand i 40-års vindauge")
    ax.set_xlim(years_grid.min(), years_grid.max())
    ax.grid(alpha=0.14, linewidth=0.4)
    ax.legend(loc="upper left", fontsize=8.5, frameon=False, ncol=2)

    axB = fig.add_subplot(gs[1], sharex=ax)
    axB.fill_between(years_grid, 0, nwin, color=SLATE, alpha=0.22, step="mid")
    axB.set_ylabel("n i vindauge")
    axB.set_xlabel("år")
    axB.grid(alpha=0.12, linewidth=0.4)
    for y_rev, lbl in [(1680, "barokk-konsolidering"),
                        (1830, "industriell revolusjon"),
                        (1925, "stålrør"),
                        (1970, "plast-støyping")]:
        axB.axvline(y_rev, color=SLATE, linewidth=0.7, linestyle=":",
                     alpha=0.7)
        axB.text(y_rev, axB.get_ylim()[1] * 0.90, lbl, rotation=90,
                  fontsize=7, color=SLATE, ha="right", va="top", alpha=0.85)

    save(fig, "E17_disparity_through_time")


# ═════════════════════════════════════════════════════════════════════
# FIG E18: Prediktiv landskaps-drift (train pre-1900, test post-1900)
# ═════════════════════════════════════════════════════════════════════
def fig_E18_prediktiv_landskapsdrift(df, pca):
    """Fit a KDE-landscape on chairs before 1900; predict where post-1900
    chairs should sit if the landscape were stationary. Highlight regions
    where post-1900 density exceeds the pre-1900 prediction (emergent zones)
    and where post-1900 density falls below (abandoned zones)."""
    df = df[df["år"].notna()].copy()
    pre = df[df["år"] < 1900]
    post = df[df["år"] >= 1900]
    if len(pre) < 30 or len(post) < 30:
        print("  skipping E18: insufficient samples")
        return

    pc1 = df["PC1"].values; pc2 = df["PC2"].values
    xlo, xhi = np.quantile(pc1, [0.005, 0.995])
    ylo, yhi = np.quantile(pc2, [0.005, 0.995])
    xpad = (xhi - xlo) * 0.04; ypad = (yhi - ylo) * 0.04
    xlo -= xpad; xhi += xpad; ylo -= ypad; yhi += ypad

    xx, yy = np.meshgrid(np.linspace(xlo, xhi, 140),
                          np.linspace(ylo, yhi, 140))
    pts = np.vstack([xx.ravel(), yy.ravel()])

    kde_pre = gaussian_kde(pre[["PC1", "PC2"]].values.T, bw_method=0.28)
    kde_post = gaussian_kde(post[["PC1", "PC2"]].values.T, bw_method=0.28)
    z_pre = kde_pre(pts).reshape(xx.shape)
    z_post = kde_post(pts).reshape(xx.shape)
    # diverging: log2 ratio; smoothed floor to avoid division issues
    ratio = np.log2((z_post + z_pre.max() * 1e-3) /
                    (z_pre + z_pre.max() * 1e-3))

    fig = plt.figure(figsize=(14, 6.5))
    gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 1.05], wspace=0.22,
                           figure=fig)

    dens_cmap = LinearSegmentedColormap.from_list(
        "amberfade", [(1, 1, 1, 0),
                      to_rgba(LIGHTAMBER, 0.60),
                      to_rgba(AMBER, 0.85),
                      to_rgba(SLATE, 0.98)], N=256)
    # quota levels for shared visual comparison
    vmax = max(z_pre.max(), z_post.max())
    lvs = np.linspace(vmax * 0.02, vmax, 10)

    axA = fig.add_subplot(gs[0])
    axA.scatter(pc1, pc2, s=3, c=OI["grey"], alpha=0.10, linewidths=0, zorder=1)
    axA.contourf(xx, yy, z_pre, levels=lvs, cmap=dens_cmap, zorder=2)
    axA.contour(xx, yy, z_pre, levels=lvs[::2], colors=[SLATE],
                 linewidths=0.35, alpha=0.55, zorder=3)
    axA.set_xlim(xlo, xhi); axA.set_ylim(ylo, yhi)
    axA.set_title(f"(a) pre-1900 landskap   n={len(pre)}",
                   loc="left", weight="bold", fontsize=10.5)
    axA.set_xlabel("PC1"); axA.set_ylabel("PC2")
    axA.grid(alpha=0.10, linewidth=0.4)

    axB = fig.add_subplot(gs[1])
    axB.scatter(pc1, pc2, s=3, c=OI["grey"], alpha=0.10, linewidths=0, zorder=1)
    axB.contourf(xx, yy, z_post, levels=lvs, cmap=dens_cmap, zorder=2)
    axB.contour(xx, yy, z_post, levels=lvs[::2], colors=[SLATE],
                 linewidths=0.35, alpha=0.55, zorder=3)
    axB.set_xlim(xlo, xhi); axB.set_ylim(ylo, yhi)
    axB.set_title(f"(b) post-1900 landskap   n={len(post)}",
                   loc="left", weight="bold", fontsize=10.5)
    axB.set_xlabel("PC1"); axB.set_ylabel("PC2")
    axB.grid(alpha=0.10, linewidth=0.4)

    axC = fig.add_subplot(gs[2])
    vmax_r = np.nanpercentile(np.abs(ratio), 95)
    cs = axC.pcolormesh(xx, yy, ratio, cmap="RdBu_r",
                         vmin=-vmax_r, vmax=vmax_r, shading="auto",
                         zorder=2)
    axC.scatter(pc1, pc2, s=3, c=OI["grey"], alpha=0.12, linewidths=0, zorder=1)
    axC.set_xlim(xlo, xhi); axC.set_ylim(ylo, yhi)
    axC.set_title("(c) log₂(post / pre) — raudt = ny region, blå = forlaten",
                   loc="left", weight="bold", fontsize=10.5)
    axC.set_xlabel("PC1")
    cb = fig.colorbar(cs, ax=axC, shrink=0.85, pad=0.02)
    cb.set_label("log₂ forholdstal")

    save(fig, "E18_prediktiv_landskapsdrift")


# ═════════════════════════════════════════════════════════════════════
# FIG E19: Morfologisk karakterforskyving (character displacement)
# ═════════════════════════════════════════════════════════════════════
def fig_E19_karakterforskyving(df, pca):
    """Empirical demonstration of *morphological character displacement*:
    when a new substrate (steel/plastic) enters the niche, the established
    substrate (wood) does not simply co-exist; its morphospace collapses.

    Layout:
      Row 1: wood distribution in four time bands (1600-1800, 1800-1900, 1900-1950, 1950-2024)
             + convex hull + n, with steel/plastic overlaid from 1900 onward.
      Row 2: (a) wood hull area over time
             (b) wood total variance over time
             (c) log2 ratio of wood variance, baseline = 1600-1800.
    The same quantity for steel/plastic is included for reference."""
    df = df[df["år"].notna()].copy()

    windows = [(1600, 1800), (1800, 1900), (1900, 1950), (1950, 2025)]
    pc_cols = ["PC1", "PC2"]
    pc1 = df["PC1"].values; pc2 = df["PC2"].values
    xlo, xhi = np.quantile(pc1, [0.005, 0.995])
    ylo, yhi = np.quantile(pc2, [0.005, 0.995])

    def hull_area(points):
        if len(points) < 3:
            return np.nan
        try:
            h = ConvexHull(points)
            return float(h.volume)
        except Exception:
            return np.nan

    def tot_var(points):
        if len(points) < 2:
            return np.nan
        return float(np.trace(np.cov(points.T)))

    # --- per-window stats ---
    wood_area = []; steel_area = []; plastic_area = []
    wood_var  = []; steel_var  = []; plastic_var  = []
    for (a, b) in windows:
        w = df[(df["mat_class"] == "wood") & (df["år"] >= a) & (df["år"] < b)][pc_cols].values
        s = df[(df["mat_class"] == "metal") & (df["år"] >= a) & (df["år"] < b)][pc_cols].values
        p = df[(df["mat_class"] == "plastic") & (df["år"] >= a) & (df["år"] < b)][pc_cols].values
        wood_area.append(hull_area(w)); steel_area.append(hull_area(s)); plastic_area.append(hull_area(p))
        wood_var.append(tot_var(w));   steel_var.append(tot_var(s));   plastic_var.append(tot_var(p))

    # --- figure layout ---
    fig = plt.figure(figsize=(15, 10.5))
    gs = gridspec.GridSpec(3, 4, height_ratios=[1.3, 1.0, 1.0],
                           hspace=0.42, wspace=0.16, figure=fig)

    # Row 1: wood distribution per window, with steel+plastic overlaid
    for i, (a, b) in enumerate(windows):
        ax = fig.add_subplot(gs[0, i])
        ax.scatter(pc1, pc2, s=3, c=OI["grey"], alpha=0.08,
                   linewidths=0, zorder=1)
        wsub = df[(df["mat_class"] == "wood") & (df["år"] >= a) & (df["år"] < b)]
        ssub = df[(df["mat_class"] == "metal") & (df["år"] >= a) & (df["år"] < b)]
        psub = df[(df["mat_class"] == "plastic") & (df["år"] >= a) & (df["år"] < b)]
        # wood
        if len(wsub) >= 3:
            ax.scatter(wsub["PC1"], wsub["PC2"], s=14, c=AMBER, alpha=0.55,
                       edgecolors="none", zorder=2, label=f"tre n={len(wsub)}")
            try:
                h = ConvexHull(wsub[pc_cols].values)
                pts = wsub[pc_cols].values[h.vertices]
                pts = np.r_[pts, pts[:1]]
                ax.plot(pts[:, 0], pts[:, 1],
                        color=AMBER, lw=1.6, alpha=0.9, zorder=3)
                ax.fill(pts[:, 0], pts[:, 1],
                        color=to_rgba(AMBER, 0.10), zorder=2)
            except Exception:
                pass
        # steel
        if len(ssub) >= 3:
            ax.scatter(ssub["PC1"], ssub["PC2"], s=18, c=OI["blue"],
                       alpha=0.65, edgecolors="white", linewidths=0.3,
                       zorder=4, label=f"stål n={len(ssub)}")
        # plastic
        if len(psub) >= 3:
            ax.scatter(psub["PC1"], psub["PC2"], s=18, c=OI["rust"],
                       alpha=0.65, edgecolors="white", linewidths=0.3,
                       zorder=4, label=f"plast n={len(psub)}")
        ax.set_xlim(xlo, xhi); ax.set_ylim(ylo, yhi)
        ax.set_title(f"{a}–{b}", loc="left", fontsize=10.5, weight="bold")
        ax.grid(alpha=0.12, linewidth=0.4)
        ax.set_xlabel("PC1")
        if i == 0: ax.set_ylabel("PC2")
        if len(wsub) >= 3:
            ax.legend(loc="lower right", fontsize=7.5, frameon=False)

    # Row 2: hull area over time, variance over time, compression ratio
    band_centers = [(a + b) / 2 for (a, b) in windows]
    x_labels = [f"{a}–{b}" for (a, b) in windows]

    ax2 = fig.add_subplot(gs[1, :2])
    ax2.plot(band_centers, wood_area, marker="o", color=AMBER, lw=2.2,
             label="tre")
    ax2.plot(band_centers, steel_area, marker="s", color=OI["blue"], lw=1.8,
             label="stål")
    ax2.plot(band_centers, plastic_area, marker="^", color=OI["rust"], lw=1.8,
             label="plast")
    ax2.set_xticks(band_centers); ax2.set_xticklabels(x_labels, fontsize=9)
    ax2.set_ylabel("konveks hylster-areal (PC1–PC2)")
    ax2.set_title("(e) morforom-areal per materiale over tid",
                   loc="left", fontsize=10.5, weight="bold")
    ax2.grid(alpha=0.14, linewidth=0.4)
    ax2.legend(loc="upper right", frameon=False, fontsize=9)
    # annotate wood collapse
    if not np.isnan(wood_area[0]) and not np.isnan(wood_area[-1]) and wood_area[0] > 0:
        pct = 100 * (wood_area[-1] / wood_area[0] - 1)
        ax2.annotate(f"tre-hylster {pct:+.0f}%",
                     xy=(band_centers[-1], wood_area[-1]),
                     xytext=(band_centers[-1] - 60, wood_area[-1] + 0.4),
                     fontsize=9, color=AMBER, weight="bold",
                     arrowprops=dict(arrowstyle="->", color=AMBER, lw=1))

    ax3 = fig.add_subplot(gs[1, 2:])
    ax3.plot(band_centers, wood_var, marker="o", color=AMBER, lw=2.2,
             label="tre")
    ax3.plot(band_centers, steel_var, marker="s", color=OI["blue"], lw=1.8,
             label="stål")
    ax3.plot(band_centers, plastic_var, marker="^", color=OI["rust"], lw=1.8,
             label="plast")
    ax3.set_xticks(band_centers); ax3.set_xticklabels(x_labels, fontsize=9)
    ax3.set_ylabel("total varians tr(Σ) i PC1–PC2")
    ax3.set_title("(f) morfologisk spreiing per materiale",
                   loc="left", fontsize=10.5, weight="bold")
    ax3.grid(alpha=0.14, linewidth=0.4)
    ax3.legend(loc="upper right", frameon=False, fontsize=9)

    ax4 = fig.add_subplot(gs[2, :])
    # steel/plastic hull area ratio over time vs wood's response
    # Compute wood's compression coefficient: wood_var[t] / wood_var[0]
    w0 = wood_var[0] if (wood_var[0] and not np.isnan(wood_var[0])) else np.nan
    comp = np.array(wood_var) / w0 if not np.isnan(w0) else np.array([np.nan] * 4)
    # intruder presence: (steel + plastic) variance per band
    intruder = np.array([
        (0 if np.isnan(s) else s) + (0 if np.isnan(p) else p)
        for s, p in zip(steel_var, plastic_var)
    ])

    ax4b = ax4.twinx()
    ax4.bar(np.arange(4) - 0.15, comp, width=0.3, color=AMBER, alpha=0.8,
             edgecolor=SLATE, linewidth=0.5,
             label="tre-spreiing relativ til 1600-1800")
    ax4b.bar(np.arange(4) + 0.15, intruder, width=0.3, color=OI["blue"],
              alpha=0.85, edgecolor=SLATE, linewidth=0.5,
              label="stål+plast total varians")
    ax4.axhline(1.0, color=SLATE, lw=0.7, linestyle="--", alpha=0.8)
    ax4.set_xticks(range(4)); ax4.set_xticklabels(x_labels, fontsize=9)
    ax4.set_ylabel("tre-spreiing / baseline", color=AMBER)
    ax4b.set_ylabel("total varians stål + plast", color=OI["blue"])
    ax4.tick_params(axis="y", labelcolor=AMBER)
    ax4b.tick_params(axis="y", labelcolor=OI["blue"])
    ax4.set_title(
        "(g) karakterforskyving: tre kollapsar i same tidsbandet som stål og plast ekspanderer",
        loc="left", fontsize=10.5, weight="bold")
    ax4.grid(axis="y", alpha=0.14, linewidth=0.4)

    # combined legend
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4b.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
               fontsize=9, frameon=False)

    save(fig, "E19_karakterforskyving")


# ═════════════════════════════════════════════════════════════════════
# FIG E20: Phylomorphospace (Sidlauskas 2008)
# ═════════════════════════════════════════════════════════════════════
def fig_E20_phylomorphospace(df, pca):
    """Phylomorphospace after Sidlauskas (2008). Stolen from ichthyology:
    place period-centroid nodes in PC1-PC2; connect them along the
    chronological 'tree' (here a linear chain by year) with internal
    branches coloured by the per-branch evolutionary rate (haldane-like).

    A real phylo has branching; artefact history is largely a chain with
    occasional 'reticulation' (revival). We show the chain plus a second
    panel with per-branch rate as a function of year."""
    counts = df["Stilperiode"].value_counts()
    periods = [p for p in sorted(PERIOD_YEAR.keys(), key=lambda k: PERIOD_YEAR[k])
               if p in counts.index and counts[p] >= 10]
    pc_cols = ["PC1", "PC2", "PC3", "PC4", "PC5", "PC6"]

    nodes = []
    for p in periods:
        sub = df[df["Stilperiode"] == p][pc_cols]
        nodes.append(dict(period=p, year=PERIOD_YEAR[p],
                           centroid=sub.mean().values,
                           sigma=sub.std().values,
                           n=len(sub)))
    nodes.sort(key=lambda r: r["year"])

    # per-branch rate: ||Δcentroid|| / Δyear (in darwins-like units)
    edges = []
    for i in range(len(nodes) - 1):
        a, b = nodes[i], nodes[i + 1]
        dt = max(b["year"] - a["year"], 1)
        dv = b["centroid"] - a["centroid"]
        rate6 = np.linalg.norm(dv) / dt
        edges.append(dict(a=i, b=i + 1, year=(a["year"] + b["year"]) / 2,
                          dt=dt, rate=rate6))

    # --- figure ---
    fig = plt.figure(figsize=(15.5, 7.2))
    gs = gridspec.GridSpec(1, 3, width_ratios=[2.1, 0.85, 1.45], wspace=0.18,
                           figure=fig)

    # Panel A: phylomorphospace
    ax = fig.add_subplot(gs[0])
    pc1 = df["PC1"].values; pc2 = df["PC2"].values
    ax.scatter(pc1, pc2, s=4, c=OI["grey"], alpha=0.10,
               linewidths=0, zorder=1)

    # color branches by rate (log scale)
    rates = np.array([e["rate"] for e in edges]) + 1e-9
    lrates = np.log10(rates)
    vmin, vmax = lrates.min(), lrates.max()
    branch_cmap = LinearSegmentedColormap.from_list(
        "rate", [SLATE, "#6B7080", AMBER, OI["rust"]], N=256)

    for e in edges:
        a, b = nodes[e["a"]], nodes[e["b"]]
        norm = (np.log10(e["rate"] + 1e-9) - vmin) / max(vmax - vmin, 1e-9)
        col = branch_cmap(norm)
        ax.annotate("", xy=(b["centroid"][0], b["centroid"][1]),
                    xytext=(a["centroid"][0], a["centroid"][1]),
                    arrowprops=dict(arrowstyle="-", color=col,
                                    lw=max(0.6, 3 * norm + 0.8),
                                    alpha=0.95),
                    zorder=3)

    for i, r in enumerate(nodes):
        c = PERIOD_COLOR.get(r["period"], OI["grey"])
        ax.scatter([r["centroid"][0]], [r["centroid"][1]],
                   s=140, c=[c], edgecolors="white",
                   linewidths=1.4, zorder=5)
        ax.text(r["centroid"][0], r["centroid"][1], str(i + 1),
                ha="center", va="center", fontsize=8.5, color="white",
                weight="bold", zorder=6)

    xlo, xhi = np.quantile(pc1, [0.02, 0.98])
    ylo, yhi = np.quantile(pc2, [0.02, 0.98])
    ax.set_xlim(xlo, xhi); ax.set_ylim(ylo, yhi)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% varians)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% varians)")
    ax.set_title("(a) phylomorphospace — kjede av periode-sentroidar "
                 "med greiner farga etter rate",
                 loc="left", fontsize=10.2, weight="bold")
    ax.grid(alpha=0.12, linewidth=0.4)

    # Panel B: numbered legend list
    axL = fig.add_subplot(gs[1]); axL.axis("off")
    axL.text(0.0, 1.00, "Node-liste", transform=axL.transAxes,
             fontsize=10, weight="bold", color=SLATE, va="top")
    for i, n in enumerate(nodes):
        yp = 0.94 - i * (0.94 / max(len(nodes), 1))
        c = PERIOD_COLOR.get(n["period"], OI["grey"])
        axL.scatter([0.02], [yp], s=55, c=[c], transform=axL.transAxes,
                    edgecolors="white", linewidths=0.8, zorder=3)
        axL.text(0.02, yp, str(i + 1), transform=axL.transAxes,
                 fontsize=7, weight="bold", color="white",
                 ha="center", va="center", zorder=4)
        axL.text(0.10, yp, f"{n['period']}  ({n['year']})",
                 transform=axL.transAxes, fontsize=7.6,
                 color=SLATE, va="center", ha="left")

    # Panel C: per-branch rate over time
    axB = fig.add_subplot(gs[2])
    years_mid = [e["year"] for e in edges]
    axB.bar(years_mid, rates, width=12, color=AMBER,
            edgecolor=SLATE, linewidth=0.5, alpha=0.85)
    axB.set_yscale("log")
    axB.set_xlabel("midt-år for grein")
    axB.set_ylabel("‖Δsentroide‖₆ / Δår   (log skala)")
    axB.set_title("(c) evolusjonsrate per grein (alle seks PC)",
                  loc="left", fontsize=10.2, weight="bold")
    axB.grid(alpha=0.14, linewidth=0.4, axis="y")
    # annotate the fastest branch
    if len(edges):
        k_max = int(np.argmax(rates))
        fastest = edges[k_max]
        a = nodes[fastest["a"]]; b = nodes[fastest["b"]]
        axB.annotate(f"raskast: {a['period']} → {b['period']}\n"
                     f"Δt = {int(fastest['dt'])} år",
                     xy=(fastest["year"], fastest["rate"]),
                     xytext=(fastest["year"] - 110,
                              fastest["rate"] * 1.4),
                     fontsize=8, color=SLATE,
                     arrowprops=dict(arrowstyle="->", color=SLATE,
                                     lw=0.8, alpha=0.7))

    save(fig, "E20_phylomorphospace")


# ═════════════════════════════════════════════════════════════════════
# FIG E21: Morfologisk tempo (Gingerich 1983, haldanes/darwins)
# ═════════════════════════════════════════════════════════════════════
def fig_E21_tempo_gingerich(df, pca):
    """Gingerich (1983) haldane rates applied to chair design.
    Haldane = (z2 - z1) / Δt in standard deviations per generation.
    We use 'generation' ≈ 25 years (one typical designer career).

    Compare observed rates to:
      - typical biological macroevolutionary rates (10⁻³ haldanes/gen)
      - typical evolutionary lineage rates (10⁻² haldanes/gen)
      - anthropogenic rates under domestication (10⁻¹–10¹ haldanes/gen)

    The scale is log-haldane; the comparison shows chairs evolving in the
    same rate regime as domesticated animals, not as wild lineages."""
    df = df[df["år"].notna()].copy()
    df = df.sort_values("år")
    pc_cols = ["PC1", "PC2", "PC3", "PC4", "PC5", "PC6"]

    # use 40-year bins for robust centroid estimation
    bins = np.arange(1500, 2040, 40)
    centroids = []
    for i in range(len(bins) - 1):
        a, b = bins[i], bins[i + 1]
        sub = df[(df["år"] >= a) & (df["år"] < b)]
        if len(sub) < 8:
            continue
        for c in pc_cols:
            pass
        centroids.append(dict(year=(a + b) / 2, bin=(a, b),
                              mean=sub[pc_cols].mean().values,
                              std=sub[pc_cols].std().values,
                              n=len(sub)))

    # haldanes between consecutive bins on each axis
    gen = 25  # years per generation
    rows = []
    for i in range(len(centroids) - 1):
        a, b = centroids[i], centroids[i + 1]
        dt_gen = (b["year"] - a["year"]) / gen
        pooled_sd = (a["std"] + b["std"]) / 2 + 1e-9
        haldane = (b["mean"] - a["mean"]) / (pooled_sd * dt_gen)
        rows.append(dict(year=(a["year"] + b["year"]) / 2,
                         haldane=haldane,
                         span=(a["year"], b["year"])))

    year_arr = np.array([r["year"] for r in rows])
    h_arr = np.array([r["haldane"] for r in rows])  # shape (n, 6)
    h_abs = np.abs(h_arr)

    fig = plt.figure(figsize=(14, 8.5))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1], hspace=0.35,
                           figure=fig)

    axA = fig.add_subplot(gs[0])
    # per-axis lines
    axis_colors = [AMBER, SLATE, OI["blue"], OI["rust"],
                   OI["green"], OI["skyblue"]]
    for i, (c, col) in enumerate(zip(pc_cols, axis_colors)):
        axA.plot(year_arr, h_abs[:, i], marker="o", markersize=4, linewidth=1.2,
                 label=f"|h({c})|", color=col, alpha=0.85)
    # biological benchmarks
    benchmarks = [
        (1e-4, "bradytelisk (makroevolusjon i naturen)", OI["grey"]),
        (1e-2, "mikroevolusjonære linjer", SLATE),
        (1e-1, "domestiserte arter (sprang)", AMBER),
        (1e0, "Bergmann-skift under klimaskift", OI["rust"]),
    ]
    for val, lbl, col in benchmarks:
        axA.axhline(val, color=col, linestyle="--", linewidth=0.7, alpha=0.7)
        axA.text(2020, val * 1.15, lbl, fontsize=7.5, color=col,
                 ha="right", va="bottom")
    axA.set_yscale("log")
    axA.set_ylim(1e-4, 10)
    axA.set_xlim(year_arr.min() - 10, year_arr.max() + 10)
    axA.set_xlabel("år")
    axA.set_ylabel("|haldane| = |Δz| / (σ̄ · Δgen)")
    axA.set_title("(a) Gingerich haldane-ratar per 40-års intervall "
                  "(gen = 25 år)", loc="left", fontsize=10.2, weight="bold")
    axA.grid(alpha=0.14, which="both", linewidth=0.4)
    axA.legend(loc="upper left", fontsize=7.5, ncol=3, frameon=False)

    axB = fig.add_subplot(gs[1])
    pooled = h_abs.mean(axis=1)
    axB.bar(year_arr, pooled, width=30, color=AMBER,
            edgecolor=SLATE, linewidth=0.4, alpha=0.85)
    axB.set_yscale("log")
    axB.set_ylim(1e-3, 10)
    axB.axhline(1e-2, color=SLATE, linestyle="--", linewidth=0.7,
                alpha=0.8, label="mikroevolusjon")
    axB.axhline(1e-1, color=AMBER, linestyle="--", linewidth=0.7,
                alpha=0.8, label="domestisering")
    axB.set_xlabel("år")
    axB.set_ylabel("gjennomsnittleg |haldane| (6 aksar)")
    axB.set_title("(b) samla haldane-rate per intervall",
                  loc="left", fontsize=10.2, weight="bold")
    axB.grid(alpha=0.14, which="both", linewidth=0.4, axis="y")
    axB.legend(loc="upper left", fontsize=8, frameon=False)
    axB.set_xlim(year_arr.min() - 10, year_arr.max() + 10)

    save(fig, "E21_tempo_gingerich")


# ═════════════════════════════════════════════════════════════════════
# FIG E22: Makroevolusjonsmodellar (BM vs OU vs EB, Harmon 2010 style)
# ═════════════════════════════════════════════════════════════════════
def fig_E22_makroevo_modellar(df, pca):
    """For each PC axis, fit three classical macroevolutionary models to
    the observed 'disparity-through-time' curve:
      BM   — Var(Δ) = σ² Δt                (pure random walk)
      OU   — Var(Δ) = (σ²/α)(1-e^{-2α Δt}) (stabilising selection)
      EB   — σ²(t) = σ²₀ exp(r t), r<0      (early-burst niche filling)
    Compare via AIC; colour-code the winning model per axis.

    This is Harmon et al. (2010)'s exact approach, transposed to chairs."""
    df_yr = df[df["år"].notna()].copy()
    pc_cols = ["PC1", "PC2", "PC3", "PC4", "PC5", "PC6"]

    from scipy.optimize import minimize

    # pairs: for each pair of chairs, (Δt, Δx for each axis)
    # we subsample to keep computation reasonable
    rng = np.random.default_rng(0)
    idx = rng.choice(len(df_yr), min(800, len(df_yr)), replace=False)
    sub = df_yr.iloc[idx].sort_values("år").reset_index(drop=True)
    yrs = sub["år"].values
    n = len(sub)

    # build pair arrays
    pair_dt = []
    pair_dx = []  # list of 6-vectors
    # cap at 50k pairs
    for i in range(n - 1):
        js = np.arange(i + 1, n)
        dts = yrs[js] - yrs[i]
        mask = dts > 0
        js = js[mask]; dts = dts[mask]
        if len(js) > 50:
            keep = rng.choice(len(js), 50, replace=False)
            js = js[keep]; dts = dts[keep]
        pair_dt.append(dts)
        pair_dx.append(sub.iloc[js][pc_cols].values - sub.iloc[i][pc_cols].values)
    pair_dt = np.concatenate(pair_dt) if pair_dt else np.array([])
    pair_dx = np.concatenate(pair_dx, axis=0) if pair_dx else np.zeros((0, 6))
    print(f"  E22: {len(pair_dt)} pair observations")

    def neg_ll_bm(params, dt, dx):
        sigma2 = np.exp(params[0])
        var_t = sigma2 * dt
        return 0.5 * np.sum(np.log(2 * np.pi * var_t) + dx ** 2 / var_t)

    def neg_ll_ou(params, dt, dx):
        sigma2 = np.exp(params[0])
        alpha = np.exp(params[1])
        var_t = (sigma2 / (2 * alpha)) * (1 - np.exp(-2 * alpha * dt))
        var_t = np.maximum(var_t, 1e-12)
        return 0.5 * np.sum(np.log(2 * np.pi * var_t) + dx ** 2 / var_t)

    def neg_ll_eb(params, dt, dx):
        sigma2_0 = np.exp(params[0])
        r = params[1]  # typically negative for early burst
        # integrated variance under EB: integral_0^dt sigma^2_0 e^{rs} ds
        if abs(r) < 1e-8:
            var_t = sigma2_0 * dt
        else:
            var_t = (sigma2_0 / r) * (np.exp(r * dt) - 1)
            var_t = np.maximum(var_t, 1e-12)
        return 0.5 * np.sum(np.log(2 * np.pi * var_t) + dx ** 2 / var_t)

    results = []
    for k, c in enumerate(pc_cols):
        dx = pair_dx[:, k]
        # fit BM
        r_bm = minimize(neg_ll_bm, [0.0], args=(pair_dt, dx),
                        method="Nelder-Mead")
        # fit OU
        r_ou = minimize(neg_ll_ou, [0.0, -2.0], args=(pair_dt, dx),
                        method="Nelder-Mead")
        # fit EB
        r_eb = minimize(neg_ll_eb, [0.0, -0.001], args=(pair_dt, dx),
                        method="Nelder-Mead")
        aic_bm = 2 * 1 + 2 * r_bm.fun
        aic_ou = 2 * 2 + 2 * r_ou.fun
        aic_eb = 2 * 2 + 2 * r_eb.fun
        aics = {"BM": aic_bm, "OU": aic_ou, "EB": aic_eb}
        best = min(aics, key=aics.get)
        delta_aic = {k: v - min(aics.values()) for k, v in aics.items()}
        params = {
            "BM": dict(sigma2=np.exp(r_bm.x[0])),
            "OU": dict(sigma2=np.exp(r_ou.x[0]), alpha=np.exp(r_ou.x[1])),
            "EB": dict(sigma2_0=np.exp(r_eb.x[0]), r=r_eb.x[1]),
        }
        results.append(dict(axis=c, aics=aics, delta=delta_aic,
                            best=best, params=params))

    fig = plt.figure(figsize=(14, 9))
    gs = gridspec.GridSpec(2, 3, hspace=0.40, wspace=0.28, figure=fig)

    model_color = {"BM": SLATE, "OU": AMBER, "EB": OI["rust"]}

    for k, res in enumerate(results):
        r, c = divmod(k, 3)
        ax = fig.add_subplot(gs[r, c])
        dts = np.linspace(1, pair_dt.max(), 80)
        # BM
        v_bm = res["params"]["BM"]["sigma2"] * dts
        # OU
        s2o = res["params"]["OU"]["sigma2"]; alpha = res["params"]["OU"]["alpha"]
        v_ou = (s2o / (2 * alpha)) * (1 - np.exp(-2 * alpha * dts))
        # EB
        s2e = res["params"]["EB"]["sigma2_0"]; rr = res["params"]["EB"]["r"]
        if abs(rr) < 1e-8:
            v_eb = s2e * dts
        else:
            v_eb = (s2e / rr) * (np.exp(rr * dts) - 1)
        # empirical variance per dt bin
        bins = np.quantile(pair_dt, np.linspace(0, 1, 20))
        emp_x = []; emp_y = []
        for i in range(len(bins) - 1):
            m = (pair_dt >= bins[i]) & (pair_dt < bins[i + 1])
            if m.sum() < 10: continue
            emp_x.append((bins[i] + bins[i + 1]) / 2)
            emp_y.append(pair_dx[m, k].var())
        ax.scatter(emp_x, emp_y, s=20, c=OI["grey"],
                   edgecolors="white", linewidths=0.3, zorder=2,
                   label="empirisk Var(Δ)")
        ax.plot(dts, v_bm, color=model_color["BM"], lw=1.6, alpha=0.9,
                 label=f"BM ΔAIC={res['delta']['BM']:.1f}")
        ax.plot(dts, v_ou, color=model_color["OU"], lw=1.6, alpha=0.9,
                 label=f"OU ΔAIC={res['delta']['OU']:.1f}")
        ax.plot(dts, v_eb, color=model_color["EB"], lw=1.6, alpha=0.9,
                 label=f"EB ΔAIC={res['delta']['EB']:.1f}")
        win_col = model_color[res["best"]]
        ax.set_title(f"{AXIS_LABELS_NN.get(res['axis'], res['axis'])}   "
                     f"beste: {res['best']}",
                     loc="left", fontsize=9.8, weight="bold", color=win_col)
        ax.set_xlabel("Δår")
        ax.set_ylabel("Var(Δtrekk)")
        ax.grid(alpha=0.12, linewidth=0.4)
        ax.legend(loc="upper left", fontsize=7.2, frameon=False)

    save(fig, "E22_makroevo_modellar")


# ═════════════════════════════════════════════════════════════════════
# FIG E23: Konvergent evolusjon på tvers av materiale
# ═════════════════════════════════════════════════════════════════════
def fig_E23_konvergens(df, pca, sils, n_pairs=8):
    """Convergent evolution: find chair pairs from different material
    classes that sit very close in 6D PC-space. These are cases where a
    new substrate arrived at a pre-existing morphological 'solution'.
    Compare to a null of same-material pair distances (should be smaller).

    The cross-material pairs identify instances where function dominates
    over substrate — direct test of the substrate-independence claim."""
    df = df.copy()
    df = df[df["mat_class"].isin(["wood", "metal", "plastic"])].reset_index(drop=True)
    pc_cols = ["PC1", "PC2", "PC3", "PC4", "PC5", "PC6"]
    X = df[pc_cols].values
    mat = df["mat_class"].values
    yrs = df["år"].values

    # compute pairs with constraint: different materials and year diff >= 50
    n = len(df)
    # sample to avoid O(n^2) blowup
    rng = np.random.default_rng(0)
    idx = rng.choice(n, min(600, n), replace=False)
    sub_X = X[idx]; sub_mat = mat[idx]; sub_yr = yrs[idx]; sub_oid = df.iloc[idx]["Objekt-ID"].values

    # only keep pairs across different materials and with year separation >= 40
    # but rank by 6D distance; keep smallest
    candidates = []
    for i in range(len(sub_X)):
        for j in range(i + 1, len(sub_X)):
            if sub_mat[i] == sub_mat[j]:
                continue
            if abs(sub_yr[i] - sub_yr[j]) < 40:
                continue
            d = np.linalg.norm(sub_X[i] - sub_X[j])
            candidates.append((d, i, j))
    candidates.sort()

    chosen_pairs = []
    used_oids = set()
    for d, i, j in candidates:
        if sub_oid[i] in used_oids or sub_oid[j] in used_oids:
            continue
        chosen_pairs.append((i, j, d))
        used_oids.add(sub_oid[i]); used_oids.add(sub_oid[j])
        if len(chosen_pairs) >= n_pairs:
            break

    # null: within-material distance distribution
    within_dists = []
    for _ in range(2000):
        i, j = rng.choice(len(sub_X), 2, replace=False)
        if sub_mat[i] != sub_mat[j]:
            continue
        within_dists.append(np.linalg.norm(sub_X[i] - sub_X[j]))
    within_dists = np.array(within_dists)

    between_dists = np.array([c[0] for c in candidates])

    # figure: grid of pair silhouettes + null distribution
    fig = plt.figure(figsize=(14, 9))
    gs = gridspec.GridSpec(3, len(chosen_pairs) if chosen_pairs else 1,
                           height_ratios=[1, 1, 1.0],
                           hspace=0.35, wspace=0.12, figure=fig)

    # top two rows: silhouette pairs, labelled
    mat_tint = {"wood": AMBER, "metal": OI["blue"], "plastic": OI["rust"]}
    for col_i, (i, j, d) in enumerate(chosen_pairs):
        for row_i, who in enumerate([i, j]):
            ax = fig.add_subplot(gs[row_i, col_i])
            oid = sub_oid[who]
            img = sils.get(oid)
            if img is not None:
                col = mat_tint.get(sub_mat[who], SLATE)
                rgba = _period_rgb_silhouette(img, to_rgba(col)[:3])
                ax.imshow(rgba, interpolation="nearest", aspect="auto")
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_title(f"{sub_mat[who]}  {int(sub_yr[who])}",
                         fontsize=8.2, color=mat_tint.get(sub_mat[who], SLATE),
                         weight="bold")
            for s in ["top", "right", "bottom", "left"]:
                ax.spines[s].set_color(mat_tint.get(sub_mat[who], SLATE))
                ax.spines[s].set_linewidth(1.2)

    # bottom row: distance distribution
    axD = fig.add_subplot(gs[2, :])
    bins = np.linspace(0, max(between_dists.max() if len(between_dists) else 1,
                              within_dists.max() if len(within_dists) else 1),
                       40)
    axD.hist(within_dists, bins=bins, color=SLATE, alpha=0.55,
             edgecolor="white", linewidth=0.3, density=True,
             label=f"innan-materiale (n={len(within_dists)})")
    axD.hist(between_dists, bins=bins, color=AMBER, alpha=0.55,
             edgecolor="white", linewidth=0.3, density=True,
             label=f"på tvers av materiale (n={len(between_dists)})")
    for d in [c[2] for c in chosen_pairs]:
        axD.axvline(d, color=OI["rust"], linewidth=0.9, alpha=0.85)
    axD.set_xlabel("6D avstand i PC-rom")
    axD.set_ylabel("tettleik")
    axD.set_title("(c) fordeling av parvise avstandar; raude linjer markerer "
                  "dei valde konvergens-para",
                  loc="left", fontsize=10, weight="bold")
    axD.legend(loc="upper right", fontsize=8.5, frameon=False)
    axD.grid(alpha=0.12, linewidth=0.4)

    save(fig, "E23_konvergens")


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

    print("[17/22] E13 punktuert likevekt (H13)...")
    fig_E13_punktuert_likevekt(df_yr, pca)

    print("[18/22] E14 agent-hierarki (H14)...")
    fig_E14_agent_hierarki(df_yr)

    print("[19/22] E16 morfologisk nyskaping over tid...")
    fig_E16_morfologisk_nyskaping(df_yr, pca, sils)

    print("[20/22] E17 disparity through time (Foote 1993)...")
    fig_E17_disparity_through_time(df_yr, pca)

    print("[21/22] E18 prediktiv landskaps-drift...")
    fig_E18_prediktiv_landskapsdrift(df_yr, pca)

    print("[22/26] E19 morfologisk karakterforskyving...")
    fig_E19_karakterforskyving(df_yr, pca)

    print("[23/26] E20 phylomorphospace (Sidlauskas 2008)...")
    fig_E20_phylomorphospace(df_yr, pca)

    print("[24/26] E21 Gingerich haldane-tempo...")
    fig_E21_tempo_gingerich(df_yr, pca)

    print("[25/26] E22 makroevolusjonsmodellar (BM/OU/EB)...")
    fig_E22_makroevo_modellar(df, pca)

    print("[26/26] E23 konvergent evolusjon...")
    fig_E23_konvergens(df_yr, pca, sils)

    for t in ("_sil_test.png", "_sil_test2.png", "_fonttest.png"):
        p = os.path.join(OUT, t)
        if os.path.exists(p):
            os.remove(p)

    print("\nDone.")


if __name__ == "__main__":
    main()
