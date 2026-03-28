#!/usr/bin/env python3
"""
Artikkel VII – Faserom: Den skjulte geometrien til forma
=========================================================
JAILBREAK-PIPELINE: Ekstraherer skjult informasjon frå 2200+ 3D-modellar og silhuettar.

METHODS (aldri brukt i designhistoria):
  1. Shape DNA          – Laplace-Beltrami eigenspektrum frå 3D-mesh
  2. Tregheitsmoment    – Principal moments of inertia frå mesh
  3. Mesh-topologi      – Euler-karakteristikk, genus, convex hull ratio
  4. Silhuett-Fourier   – Elliptisk Fourier-deskriptorar frå bguw-bilete
  5. Fraktal dimensjon  – Box-counting fractal dimension av silhuetten
  6. Kruvingsanalyse    – Mean/Gaussian curvature distribution frå mesh
  7. Cross-section DNA  – Tverrsnittsprofil ved 5 høgder

FIGURES:
  fig1  – Mega-grid: 400 silhuettar sortert etter Shape DNA
  fig2  – Shape DNA spektrogram over hundreår
  fig3  – Tregheitsellipsoide-atlas
  fig4  – Silhuett-Fourier rekonstruksjon (4, 8, 16, 32, 64 harmonics)
  fig5  – Fraktal dimensjon vs tid
  fig6  – Morphospace frå Shape DNA (UMAP)
  fig7  – Cross-section DNA: tverrsnittsprofil evolution
  fig8  – Convex hull ratio vs genus: topologisk mangfald
  fig9  – Curvature heatmap montage
  fig10 – Ghost chairs: interpolerte former i tomme regionar
"""

import os, sys, warnings, glob, json, time
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec
from scipy.spatial.distance import pdist, squareform
from scipy.ndimage import gaussian_filter1d
from sklearn.preprocessing import StandardScaler
from PIL import Image
import cv2
import trimesh

# ── paths ──
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV  = os.path.join(ROOT, "STOLAR", "STOLAR.csv")
GLB  = os.path.join(ROOT, "STOLAR", "glb")
BGUW = os.path.join(ROOT, "STOLAR", "bguw")
FIG  = os.path.join(ROOT, "texts", "VII-Faserom", "fig")
os.makedirs(FIG, exist_ok=True)

# ── style ──
DARK = "#0a0a0f"
C1 = "#00f0ff"
C2 = "#ff3366"
C3 = "#ffcc00"
C4 = "#00ff88"
C5 = "#aa66ff"

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.linewidth": 0.6,
    "axes.labelsize": 10, "figure.dpi": 300, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.05,
})


def load_data():
    df = pd.read_csv(CSV, encoding="utf-8")
    df["Frå år"] = pd.to_numeric(df["Frå år"], errors="coerce")
    df = df.dropna(subset=["Frå år"])
    df = df[(df["Frå år"] >= 1200) & (df["Frå år"] <= 2025)]
    df["Hundreår_num"] = (df["Frå år"] // 100) * 100
    return df


def extract_mesh_features(glb_path, n_eigenvalues=20):
    """Extract Shape DNA, moments of inertia, topology from a GLB mesh."""
    try:
        scene = trimesh.load(glb_path, force="mesh")
        if isinstance(scene, trimesh.Scene):
            meshes = list(scene.geometry.values())
            if not meshes:
                return None
            mesh = meshes[0]
            for m in meshes[1:]:
                mesh = trimesh.util.concatenate([mesh, m])
        else:
            mesh = scene

        if len(mesh.vertices) < 20:
            return None

        # normalize: center + scale to unit bounding box
        mesh.vertices -= mesh.centroid
        scale = mesh.bounding_box.extents.max()
        if scale > 0:
            mesh.vertices /= scale

        features = {}

        # ── Principal moments of inertia ──
        try:
            inertia = mesh.moment_inertia
            eigenvalues_inertia = np.sort(np.linalg.eigvalsh(inertia))[::-1]
            features["I1"] = eigenvalues_inertia[0]
            features["I2"] = eigenvalues_inertia[1]
            features["I3"] = eigenvalues_inertia[2]
            features["anisotropy"] = eigenvalues_inertia[0] / (eigenvalues_inertia[2] + 1e-10)
        except Exception:
            features["I1"] = features["I2"] = features["I3"] = 0
            features["anisotropy"] = 1

        # ── Topological features ──
        features["n_vertices"] = len(mesh.vertices)
        features["n_faces"] = len(mesh.faces)
        try:
            features["euler"] = mesh.euler_number
        except Exception:
            features["euler"] = 2

        try:
            features["volume"] = abs(mesh.volume)
        except Exception:
            features["volume"] = 0

        try:
            features["surface_area"] = mesh.area
        except Exception:
            features["surface_area"] = 0

        # convex hull ratio (compactness)
        try:
            hull = mesh.convex_hull
            features["convex_hull_ratio"] = features["volume"] / (hull.volume + 1e-10)
            features["hull_area_ratio"] = features["surface_area"] / (hull.area + 1e-10)
        except Exception:
            features["convex_hull_ratio"] = 1.0
            features["hull_area_ratio"] = 1.0

        # sphericity
        if features["surface_area"] > 0 and features["volume"] > 0:
            features["sphericity"] = (np.pi**(1/3) * (6 * features["volume"])**(2/3)) / features["surface_area"]
        else:
            features["sphericity"] = 0

        # ── Shape DNA: Laplace-Beltrami eigenvalues ──
        try:
            # subsample mesh for computational tractability
            if len(mesh.vertices) > 3000:
                mesh = mesh.simplify_quadric_decimation(3000)

            # build cotangent Laplacian
            L = trimesh.smoothing.laplacian_calculation(mesh)
            if L is not None and L.shape[0] > n_eigenvalues + 1:
                L_dense = L.toarray() if hasattr(L, 'toarray') else np.array(L)
                evals = np.sort(np.real(np.linalg.eigvalsh(L_dense)))
                # skip first (always 0), take next n
                shape_dna = evals[1:n_eigenvalues + 1]
                for k in range(min(len(shape_dna), n_eigenvalues)):
                    features[f"lambda_{k+1}"] = shape_dna[k]
                # fill missing
                for k in range(len(shape_dna), n_eigenvalues):
                    features[f"lambda_{k+1}"] = 0
            else:
                for k in range(n_eigenvalues):
                    features[f"lambda_{k+1}"] = 0
        except Exception:
            for k in range(n_eigenvalues):
                features[f"lambda_{k+1}"] = 0

        # ── Cross-section profiles at 5 heights ──
        try:
            zmin, zmax = mesh.vertices[:, 2].min(), mesh.vertices[:, 2].max()
            heights = np.linspace(zmin + 0.05, zmax - 0.05, 5)
            for hi, h in enumerate(heights):
                try:
                    section = mesh.section(plane_origin=[0, 0, h],
                                           plane_normal=[0, 0, 1])
                    if section is not None:
                        path = section.to_planar()[0]
                        features[f"xsec_{hi}_area"] = abs(path.area)
                        features[f"xsec_{hi}_perim"] = path.length
                    else:
                        features[f"xsec_{hi}_area"] = 0
                        features[f"xsec_{hi}_perim"] = 0
                except Exception:
                    features[f"xsec_{hi}_area"] = 0
                    features[f"xsec_{hi}_perim"] = 0
        except Exception:
            for hi in range(5):
                features[f"xsec_{hi}_area"] = 0
                features[f"xsec_{hi}_perim"] = 0

        return features

    except Exception as e:
        return None


def extract_silhouette_features(img_path, n_harmonics=64):
    """Extract Fourier descriptors and fractal dimension from silhouette."""
    try:
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            return None, None

        # extract alpha channel or convert to binary
        if img.shape[2] == 4:
            alpha = img[:, :, 3]
            binary = (alpha > 128).astype(np.uint8) * 255
        else:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            return None, None

        # largest contour
        contour = max(contours, key=cv2.contourArea)
        if len(contour) < 30:
            return None, None

        # ── Elliptical Fourier Descriptors ──
        pts = contour.squeeze()
        if pts.ndim != 2:
            return None, None

        n_pts = len(pts)
        t = np.arange(n_pts)
        dx = np.diff(pts[:, 0], append=pts[0, 0])
        dy = np.diff(pts[:, 1], append=pts[0, 1])
        dt = np.sqrt(dx**2 + dy**2)
        dt[dt == 0] = 1e-6
        T = dt.sum()
        t_cum = np.cumsum(dt)

        fourier = np.zeros((n_harmonics, 4))  # a_n, b_n, c_n, d_n
        for n in range(1, n_harmonics + 1):
            an = bn = cn = dn = 0
            for i in range(n_pts):
                ti = t_cum[i]
                ti_prev = t_cum[i - 1] if i > 0 else 0
                cos_diff = np.cos(2 * np.pi * n * ti / T) - np.cos(2 * np.pi * n * ti_prev / T)
                sin_diff = np.sin(2 * np.pi * n * ti / T) - np.sin(2 * np.pi * n * ti_prev / T)
                an += (dx[i] / dt[i]) * cos_diff
                bn += (dx[i] / dt[i]) * sin_diff
                cn += (dy[i] / dt[i]) * cos_diff
                dn += (dy[i] / dt[i]) * sin_diff
            factor = T / (2 * np.pi**2 * n**2)
            fourier[n-1] = [an * factor, bn * factor, cn * factor, dn * factor]

        # normalize: size + rotation invariant
        a1, b1, c1, d1 = fourier[0]
        size = np.sqrt(a1**2 + b1**2)
        if size > 0:
            fourier /= size

        # ── Fractal dimension (box-counting) ──
        def box_count_fractal(binary_img):
            Z = binary_img > 0
            p = min(Z.shape)
            n = int(np.floor(np.log2(p)))
            sizes = 2**np.arange(n, 1, -1)
            counts = []
            for s in sizes:
                count = 0
                for i in range(0, Z.shape[0], s):
                    for j in range(0, Z.shape[1], s):
                        if Z[i:i+s, j:j+s].any():
                            count += 1
                counts.append(count)
            # log-log fit
            coeffs = np.polyfit(np.log(sizes), np.log(counts), 1)
            return -coeffs[0]

        fractal_dim = box_count_fractal(binary)

        features = {f"efd_{i}": fourier[i].tolist() for i in range(min(n_harmonics, 32))}
        features["fractal_dim"] = fractal_dim
        features["contour_len"] = len(contour)
        features["area"] = cv2.contourArea(contour)
        features["perimeter"] = cv2.arcLength(contour, True)
        features["circularity"] = 4 * np.pi * features["area"] / (features["perimeter"]**2 + 1e-10)
        features["solidity"] = features["area"] / (cv2.contourArea(cv2.convexHull(contour)) + 1e-10)

        return features, contour

    except Exception:
        return None, None


def reconstruct_from_fourier(fourier_coeffs, n_harmonics, n_points=500):
    """Reconstruct contour from first n_harmonics Fourier coefficients."""
    t = np.linspace(0, 1, n_points)
    x = np.zeros(n_points)
    y = np.zeros(n_points)
    for n in range(n_harmonics):
        if n >= len(fourier_coeffs):
            break
        a, b, c, d = fourier_coeffs[n]
        x += a * np.cos(2 * np.pi * (n + 1) * t) + b * np.sin(2 * np.pi * (n + 1) * t)
        y += c * np.cos(2 * np.pi * (n + 1) * t) + d * np.sin(2 * np.pi * (n + 1) * t)
    return x, y


# ══════════════════════════════════════════════════════════════
# FIGURE GENERATION
# ══════════════════════════════════════════════════════════════

def fig1_silhouette_grid(df):
    """Fig 1: Mega-grid of silhouettes sorted by year."""
    print("  [fig1] Building silhouette mega-grid...")
    bguw_files = glob.glob(os.path.join(BGUW, "*_bguw.png"))

    # map objekt-id to bguw file
    id_to_file = {}
    for f in bguw_files:
        base = os.path.basename(f).replace("_bguw.png", "")
        id_to_file[base] = f

    # match with metadata
    matched = []
    for _, row in df.iterrows():
        oid = str(row.get("Objekt-ID", ""))
        if oid in id_to_file:
            matched.append((row["Frå år"], id_to_file[oid], oid))

    matched.sort(key=lambda x: x[0])

    # subsample to grid
    n_cols = 25
    n_rows = 16
    n_total = n_cols * n_rows
    step = max(1, len(matched) // n_total)
    selected = matched[::step][:n_total]

    thumb_size = 80
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 13), facecolor=DARK)
    fig.subplots_adjust(wspace=0.02, hspace=0.02)

    for idx in range(n_rows * n_cols):
        r, c = divmod(idx, n_cols)
        ax = axes[r][c]
        ax.set_facecolor(DARK)
        ax.axis("off")

        if idx < len(selected):
            year, fpath, oid = selected[idx]
            try:
                img = Image.open(fpath).convert("RGBA")
                img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                ax.imshow(img, interpolation="bilinear")
                # tiny year label
                ax.text(0.5, -0.02, str(int(year)), transform=ax.transAxes,
                        fontsize=3, color="#666", ha="center", va="top")
            except Exception:
                pass

    fig.suptitle("400 stolar sorterte kronologisk (1280-2024)",
                 color="white", fontsize=14, y=0.98)
    fig.savefig(os.path.join(FIG, "fig1_silhuett_grid.png"), facecolor=DARK)
    fig.savefig(os.path.join(FIG, "fig1_silhuett_grid.pdf"), facecolor=DARK)
    plt.close()
    print("  ✓ fig1_silhuett_grid")


def process_meshes(df, max_meshes=300):
    """Process GLB meshes and extract features."""
    print(f"  [mesh] Processing up to {max_meshes} meshes...")
    glb_files = glob.glob(os.path.join(GLB, "*.glb"))

    # skip textured variants
    glb_files = [f for f in glb_files if "_textured" not in f]

    id_to_glb = {}
    for f in glb_files:
        base = os.path.basename(f).replace(".glb", "")
        id_to_glb[base] = f

    results = []
    count = 0
    for _, row in df.iterrows():
        if count >= max_meshes:
            break
        oid = str(row.get("Objekt-ID", ""))
        if oid not in id_to_glb:
            continue

        feats = extract_mesh_features(id_to_glb[oid], n_eigenvalues=15)
        if feats is None:
            continue

        feats["Objekt-ID"] = oid
        feats["year"] = row["Frå år"]
        feats["century"] = row["Hundreår_num"]
        feats["style"] = row.get("Stilperiode", "Ukjend")
        feats["material"] = str(row.get("Materialar", ""))[:30]
        results.append(feats)
        count += 1
        if count % 50 == 0:
            print(f"    ... {count}/{max_meshes} meshes processed")

    print(f"  ✓ {len(results)} meshes processed")
    return pd.DataFrame(results)


def process_silhouettes(df, max_sil=500):
    """Process bguw images and extract silhouette features."""
    print(f"  [silhouette] Processing up to {max_sil} silhouettes...")
    bguw_files = glob.glob(os.path.join(BGUW, "*_bguw.png"))
    id_to_bguw = {}
    for f in bguw_files:
        base = os.path.basename(f).replace("_bguw.png", "")
        id_to_bguw[base] = f

    results = []
    all_fourier = []
    count = 0
    for _, row in df.iterrows():
        if count >= max_sil:
            break
        oid = str(row.get("Objekt-ID", ""))
        if oid not in id_to_bguw:
            continue

        feats, contour = extract_silhouette_features(id_to_bguw[oid], n_harmonics=32)
        if feats is None:
            continue

        feats["Objekt-ID"] = oid
        feats["year"] = row["Frå år"]
        feats["century"] = row["Hundreår_num"]
        feats["style"] = row.get("Stilperiode", "Ukjend")
        results.append(feats)
        all_fourier.append([feats[f"efd_{i}"] for i in range(32)])
        count += 1
        if count % 100 == 0:
            print(f"    ... {count}/{max_sil} silhouettes processed")

    print(f"  ✓ {len(results)} silhouettes processed")
    return pd.DataFrame(results), all_fourier


def fig2_shape_dna_spectrogram(mesh_df):
    """Fig 2: Shape DNA eigenvalue spectrogram over centuries."""
    print("  [fig2] Shape DNA spectrogram...")
    lambda_cols = [c for c in mesh_df.columns if c.startswith("lambda_")]
    if not lambda_cols:
        print("  ⚠ No Shape DNA data")
        return

    centuries = sorted(mesh_df["century"].unique())
    centuries = [c for c in centuries if mesh_df[mesh_df["century"] == c].shape[0] >= 5]

    fig, ax = plt.subplots(1, 1, figsize=(12, 6), facecolor=DARK)
    ax.set_facecolor(DARK)

    n_lambda = len(lambda_cols)
    matrix = np.zeros((len(centuries), n_lambda))

    for i, c in enumerate(centuries):
        subset = mesh_df[mesh_df["century"] == c][lambda_cols].values
        matrix[i] = np.median(subset, axis=0)

    # normalize per eigenvalue
    for j in range(n_lambda):
        col_max = matrix[:, j].max()
        if col_max > 0:
            matrix[:, j] /= col_max

    im = ax.imshow(matrix.T, aspect="auto", cmap="inferno",
                   interpolation="bicubic", origin="lower")
    ax.set_xticks(range(len(centuries)))
    ax.set_xticklabels([str(int(c)) for c in centuries], color="white", fontsize=8)
    ax.set_ylabel("Eigenverdi-indeks $\\lambda_k$", color="white", fontsize=10)
    ax.set_xlabel("Hundreår", color="white", fontsize=10)
    ax.set_title("Shape DNA: Laplace-Beltrami eigenspektrum over tid",
                 color="white", fontsize=12, pad=10)
    cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.ax.tick_params(colors="white", labelsize=7)
    cbar.set_label("Normalisert eigenverdi", color="white", fontsize=9)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    fig.savefig(os.path.join(FIG, "fig2_shape_dna.png"), facecolor=DARK)
    fig.savefig(os.path.join(FIG, "fig2_shape_dna.pdf"), facecolor=DARK)
    plt.close()
    print("  ✓ fig2_shape_dna")


def fig3_inertia_atlas(mesh_df):
    """Fig 3: Inertia ellipsoid ratios over time."""
    print("  [fig3] Inertia ellipsoid atlas...")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), facecolor=DARK)

    for ax in axes:
        ax.set_facecolor(DARK)

    years = mesh_df["year"].values
    norm = Normalize(vmin=1300, vmax=2025)

    # Panel A: I1/I3 (anisotropy) vs year
    ax = axes[0]
    ax.scatter(years, mesh_df["anisotropy"].clip(0, 20), c=years, cmap="magma",
               s=8, alpha=0.6, norm=norm, edgecolors="none")
    ax.set_xlabel("År", color="white", fontsize=9)
    ax.set_ylabel("Anisotropi ($I_1/I_3$)", color="white", fontsize=9)
    ax.set_title("a) Tregleiksanisotropi", color="white", fontsize=10, pad=8)

    # Panel B: I2/I1 vs I3/I1
    ax = axes[1]
    i2i1 = (mesh_df["I2"] / (mesh_df["I1"] + 1e-10)).clip(0, 1.5)
    i3i1 = (mesh_df["I3"] / (mesh_df["I1"] + 1e-10)).clip(0, 1.5)
    sc = ax.scatter(i2i1, i3i1, c=years, cmap="magma", s=8, alpha=0.6, norm=norm, edgecolors="none")
    ax.set_xlabel("$I_2/I_1$", color="white", fontsize=9)
    ax.set_ylabel("$I_3/I_1$", color="white", fontsize=9)
    ax.set_title("b) Tregleiksrom", color="white", fontsize=10, pad=8)
    # add reference shapes
    ax.annotate("Sfære", xy=(1, 1), color=C1, fontsize=7, ha="center")
    ax.annotate("Stong", xy=(0.1, 0.1), color=C2, fontsize=7, ha="center")

    # Panel C: sphericity over time
    ax = axes[2]
    ax.scatter(years, mesh_df["sphericity"].clip(0, 1), c=years, cmap="magma",
               s=8, alpha=0.6, norm=norm, edgecolors="none")
    ax.set_xlabel("År", color="white", fontsize=9)
    ax.set_ylabel("Sfærisitet", color="white", fontsize=9)
    ax.set_title("c) Sfærisitet over tid", color="white", fontsize=10, pad=8)

    for ax in axes:
        ax.tick_params(colors="white", labelsize=7)
        for spine in ax.spines.values():
            spine.set_color("#333")

    cbar = plt.colorbar(sc, ax=axes, shrink=0.7, pad=0.02)
    cbar.ax.tick_params(colors="white", labelsize=7)

    fig.suptitle("Tregheitsellipsoid-atlas: korleis 3D-forma fordeler seg",
                 color="white", fontsize=12, y=1.02)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_tregheit.png"), facecolor=DARK)
    fig.savefig(os.path.join(FIG, "fig3_tregheit.pdf"), facecolor=DARK)
    plt.close()
    print("  ✓ fig3_tregheit")


def fig4_fourier_reconstruction(df):
    """Fig 4: Progressive Fourier reconstruction of a single chair."""
    print("  [fig4] Fourier reconstruction...")
    bguw_files = glob.glob(os.path.join(BGUW, "*_bguw.png"))

    # find a good chair with clear silhouette
    best = None
    for f in bguw_files[:200]:
        feats, contour = extract_silhouette_features(f, n_harmonics=64)
        if feats and contour is not None and len(contour) > 200:
            best = (f, feats, contour)
            break

    if best is None:
        print("  ⚠ No suitable silhouette found")
        return

    fpath, feats, contour = best
    fourier_raw = [feats[f"efd_{i}"] for i in range(32)]

    fig, axes = plt.subplots(2, 4, figsize=(16, 8), facecolor=DARK)

    harmonics_levels = [2, 4, 8, 16, 24, 32, 48, 64]

    for idx, n_harm in enumerate(harmonics_levels):
        r, c = divmod(idx, 4)
        ax = axes[r][c]
        ax.set_facecolor(DARK)
        ax.set_aspect("equal")

        # reconstruct
        n_use = min(n_harm, len(fourier_raw))
        x, y = reconstruct_from_fourier(fourier_raw[:n_use], n_use)

        ax.fill(x, y, color=C1, alpha=0.15)
        ax.plot(x, y, color=C1, lw=1.5, alpha=0.9)
        ax.set_title(f"$N = {n_harm}$ harmoniske", color="white", fontsize=9, pad=5)
        ax.tick_params(colors="white", labelsize=5)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color("#333")

    fig.suptitle("Fourier-rekonstruksjon: frå grov til fin form",
                 color="white", fontsize=13, y=1.01)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_fourier_rekon.png"), facecolor=DARK)
    fig.savefig(os.path.join(FIG, "fig4_fourier_rekon.pdf"), facecolor=DARK)
    plt.close()
    print("  ✓ fig4_fourier_rekon")


def fig5_fractal_dimension(sil_df):
    """Fig 5: Fractal dimension over time."""
    print("  [fig5] Fractal dimension timeline...")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), facecolor=DARK)

    # Panel A: scatter
    ax = axes[0]
    ax.set_facecolor(DARK)
    valid = sil_df.dropna(subset=["fractal_dim"])
    valid = valid[(valid["fractal_dim"] > 1.0) & (valid["fractal_dim"] < 2.0)]

    sc = ax.scatter(valid["year"], valid["fractal_dim"], c=valid["year"],
                    cmap="magma", s=8, alpha=0.5, edgecolors="none",
                    norm=Normalize(1300, 2025))

    # rolling median
    sorted_v = valid.sort_values("year")
    window = max(20, len(sorted_v) // 20)
    rolling_med = sorted_v["fractal_dim"].rolling(window, center=True).median()
    ax.plot(sorted_v["year"], rolling_med, color=C1, lw=2.5,
            path_effects=[pe.withStroke(linewidth=4, foreground=DARK)])

    ax.set_xlabel("År", color="white", fontsize=10)
    ax.set_ylabel("Fraktal dimensjon $D_f$", color="white", fontsize=10)
    ax.set_title("a) Silhuett-kompleksitet over tid", color="white", fontsize=11, pad=8)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    # Panel B: distribution per century
    ax = axes[1]
    ax.set_facecolor(DARK)
    centuries = sorted(valid["century"].unique())
    centuries = [c for c in centuries if valid[valid["century"] == c].shape[0] >= 10]

    positions = range(len(centuries))
    data = [valid[valid["century"] == c]["fractal_dim"].values for c in centuries]

    bp = ax.boxplot(data, positions=positions, patch_artist=True,
                    widths=0.6, showfliers=False)
    for patch in bp["boxes"]:
        patch.set_facecolor(C2)
        patch.set_alpha(0.6)
    for element in ["whiskers", "caps", "medians"]:
        for line in bp[element]:
            line.set_color("white")

    ax.set_xticks(positions)
    ax.set_xticklabels([str(int(c)) for c in centuries], color="white", fontsize=8, rotation=45)
    ax.set_ylabel("Fraktal dimensjon $D_f$", color="white", fontsize=10)
    ax.set_title("b) Distribusjon per hundreår", color="white", fontsize=11, pad=8)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_fraktal.png"), facecolor=DARK)
    fig.savefig(os.path.join(FIG, "fig5_fraktal.pdf"), facecolor=DARK)
    plt.close()
    print("  ✓ fig5_fraktal")


def fig6_shape_dna_umap(mesh_df):
    """Fig 6: UMAP of Shape DNA + inertia features."""
    print("  [fig6] Shape DNA morphospace UMAP...")
    import umap

    feat_cols = [c for c in mesh_df.columns if c.startswith("lambda_") or c in
                 ["I1", "I2", "I3", "sphericity", "convex_hull_ratio", "hull_area_ratio"]]

    X = mesh_df[feat_cols].values
    X = np.nan_to_num(X, 0)
    X = StandardScaler().fit_transform(X)

    reducer = umap.UMAP(n_neighbors=20, min_dist=0.2, random_state=42)
    emb = reducer.fit_transform(X)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor=DARK)

    # Panel A: year
    ax = axes[0]
    ax.set_facecolor(DARK)
    sc = ax.scatter(emb[:, 0], emb[:, 1], c=mesh_df["year"].values, cmap="magma",
                    s=15, alpha=0.7, edgecolors="white", linewidths=0.2,
                    norm=Normalize(1300, 2025))
    cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cbar.ax.tick_params(colors="white", labelsize=7)
    cbar.set_label("År", color="white", fontsize=9)
    ax.set_title("a) Shape DNA morforom (år)", color="white", fontsize=11, pad=8)
    ax.set_xlabel("UMAP-1", color="white")
    ax.set_ylabel("UMAP-2", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    # Panel B: convex hull ratio
    ax = axes[1]
    ax.set_facecolor(DARK)
    sc = ax.scatter(emb[:, 0], emb[:, 1], c=mesh_df["convex_hull_ratio"].clip(0, 1),
                    cmap="viridis", s=15, alpha=0.7, edgecolors="white", linewidths=0.2)
    cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cbar.ax.tick_params(colors="white", labelsize=7)
    cbar.set_label("Konveks-hull-ratio", color="white", fontsize=9)
    ax.set_title("b) Shape DNA morforom (kompaktheit)", color="white", fontsize=11, pad=8)
    ax.set_xlabel("UMAP-1", color="white")
    ax.set_ylabel("UMAP-2", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_shape_dna_umap.png"), facecolor=DARK)
    fig.savefig(os.path.join(FIG, "fig6_shape_dna_umap.pdf"), facecolor=DARK)
    plt.close()
    print("  ✓ fig6_shape_dna_umap")


def fig7_crosssection_evolution(mesh_df):
    """Fig 7: Cross-section DNA evolution over time."""
    print("  [fig7] Cross-section evolution...")
    xsec_cols = [c for c in mesh_df.columns if c.startswith("xsec_") and c.endswith("_area")]

    if not xsec_cols:
        print("  ⚠ No cross-section data")
        return

    centuries = sorted(mesh_df["century"].unique())
    centuries = [c for c in centuries if mesh_df[mesh_df["century"] == c].shape[0] >= 5]

    fig, ax = plt.subplots(1, 1, figsize=(12, 6), facecolor=DARK)
    ax.set_facecolor(DARK)

    n_heights = len(xsec_cols)
    height_labels = ["Botn", "Lågmidt", "Midt", "Høgmidt", "Topp"][:n_heights]

    for hi, col in enumerate(xsec_cols):
        medians = []
        q25 = []
        q75 = []
        for c in centuries:
            vals = mesh_df[mesh_df["century"] == c][col].dropna()
            vals = vals[vals > 0]
            if len(vals) > 0:
                medians.append(vals.median())
                q25.append(vals.quantile(0.25))
                q75.append(vals.quantile(0.75))
            else:
                medians.append(0)
                q25.append(0)
                q75.append(0)

        color = [C1, C2, C3, C4, C5][hi % 5]
        ax.fill_between(centuries, q25, q75, alpha=0.15, color=color)
        ax.plot(centuries, medians, "o-", color=color, lw=2, markersize=5,
                label=height_labels[hi] if hi < len(height_labels) else f"H{hi}")

    ax.set_xlabel("Hundreår", color="white", fontsize=10)
    ax.set_ylabel("Tverrsnitt-areal (normalisert)", color="white", fontsize=10)
    ax.set_title("Cross-section DNA: tverrsnittsprofil over tid",
                 color="white", fontsize=12, pad=10)
    ax.legend(fontsize=8, facecolor=DARK, edgecolor="#444", labelcolor="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    fig.savefig(os.path.join(FIG, "fig7_crosssection.png"), facecolor=DARK)
    fig.savefig(os.path.join(FIG, "fig7_crosssection.pdf"), facecolor=DARK)
    plt.close()
    print("  ✓ fig7_crosssection")


def fig8_topology_scatter(mesh_df):
    """Fig 8: Convex hull ratio vs euler number -- topological diversity."""
    print("  [fig8] Topological diversity scatter...")
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), facecolor=DARK)

    # Panel A: CHR vs sphericity colored by year
    ax = axes[0]
    ax.set_facecolor(DARK)
    chr_vals = mesh_df["convex_hull_ratio"].clip(0, 1)
    sph_vals = mesh_df["sphericity"].clip(0, 1)
    sc = ax.scatter(chr_vals, sph_vals, c=mesh_df["year"], cmap="magma",
                    s=15, alpha=0.6, edgecolors="white", linewidths=0.2,
                    norm=Normalize(1300, 2025))
    ax.set_xlabel("Konveks-hull-ratio (kompaktheit)", color="white", fontsize=10)
    ax.set_ylabel("Sfærisitet", color="white", fontsize=10)
    ax.set_title("a) Kompaktheit vs sfærisitet", color="white", fontsize=11, pad=8)
    cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cbar.ax.tick_params(colors="white", labelsize=7)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    # Panel B: Hull area ratio vs volume colored by year
    ax = axes[1]
    ax.set_facecolor(DARK)
    har = mesh_df["hull_area_ratio"].clip(0, 3)
    vol = mesh_df["volume"].clip(0, mesh_df["volume"].quantile(0.95))
    sc = ax.scatter(har, vol, c=mesh_df["year"], cmap="magma",
                    s=15, alpha=0.6, edgecolors="white", linewidths=0.2,
                    norm=Normalize(1300, 2025))
    ax.set_xlabel("Overflate/hull-ratio (porøsitet)", color="white", fontsize=10)
    ax.set_ylabel("Volum (normalisert)", color="white", fontsize=10)
    ax.set_title("b) Porøsitet vs volum", color="white", fontsize=11, pad=8)
    cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cbar.ax.tick_params(colors="white", labelsize=7)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig8_topologi.png"), facecolor=DARK)
    fig.savefig(os.path.join(FIG, "fig8_topologi.pdf"), facecolor=DARK)
    plt.close()
    print("  ✓ fig8_topologi")


def fig9_circularity_solidity(sil_df):
    """Fig 9: Circularity vs solidity -- form complexity landscape."""
    print("  [fig9] Form complexity landscape...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor=DARK)

    valid = sil_df.dropna(subset=["circularity", "solidity"])
    valid = valid[(valid["circularity"] > 0) & (valid["circularity"] < 1.1)]

    # Panel A: circularity vs solidity
    ax = axes[0]
    ax.set_facecolor(DARK)
    sc = ax.scatter(valid["circularity"], valid["solidity"],
                    c=valid["year"], cmap="magma", s=12, alpha=0.6,
                    edgecolors="white", linewidths=0.2,
                    norm=Normalize(1300, 2025))
    ax.set_xlabel("Sirkularitet", color="white", fontsize=10)
    ax.set_ylabel("Soliditet", color="white", fontsize=10)
    ax.set_title("a) Formkompleksitet: sirkularitet vs soliditet",
                 color="white", fontsize=11, pad=8)
    cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cbar.ax.tick_params(colors="white", labelsize=7)
    cbar.set_label("År", color="white", fontsize=9)

    # annotate extremes
    if len(valid) > 0:
        most_circular = valid.loc[valid["circularity"].idxmax()]
        least_circular = valid.loc[valid["circularity"].idxmin()]
        ax.annotate(f"Mest sirkulær\n({int(most_circular['year'])})",
                    xy=(most_circular["circularity"], most_circular["solidity"]),
                    color=C1, fontsize=7, ha="left")

    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    # Panel B: fractal dim vs circularity
    ax = axes[1]
    ax.set_facecolor(DARK)
    valid2 = valid.dropna(subset=["fractal_dim"])
    valid2 = valid2[(valid2["fractal_dim"] > 1.0) & (valid2["fractal_dim"] < 2.0)]
    if len(valid2) > 0:
        sc = ax.scatter(valid2["fractal_dim"], valid2["circularity"],
                        c=valid2["year"], cmap="magma", s=12, alpha=0.6,
                        edgecolors="white", linewidths=0.2,
                        norm=Normalize(1300, 2025))
        ax.set_xlabel("Fraktal dimensjon $D_f$", color="white", fontsize=10)
        ax.set_ylabel("Sirkularitet", color="white", fontsize=10)
        ax.set_title("b) Fraktal kompleksitet vs sirkularitet",
                     color="white", fontsize=11, pad=8)
        cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
        cbar.ax.tick_params(colors="white", labelsize=7)

    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    plt.tight_layout()
    fig.savefig(os.path.join(FIG, "fig9_formkompleksitet.png"), facecolor=DARK)
    fig.savefig(os.path.join(FIG, "fig9_formkompleksitet.pdf"), facecolor=DARK)
    plt.close()
    print("  ✓ fig9_formkompleksitet")


def fig10_ghost_chairs(mesh_df):
    """Fig 10: Ghost chairs -- interpolated forms in empty morphospace regions."""
    print("  [fig10] Ghost chairs in morphospace...")
    import umap

    feat_cols = [c for c in mesh_df.columns if c.startswith("lambda_") or c in
                 ["I1", "I2", "I3", "sphericity", "convex_hull_ratio"]]

    X = mesh_df[feat_cols].values
    X = np.nan_to_num(X, 0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    reducer = umap.UMAP(n_neighbors=20, min_dist=0.3, random_state=42)
    emb = reducer.fit_transform(X_scaled)

    fig, ax = plt.subplots(1, 1, figsize=(10, 10), facecolor=DARK)
    ax.set_facecolor(DARK)

    # density map
    from scipy.stats import gaussian_kde
    try:
        xy = emb.T
        kde = gaussian_kde(xy, bw_method=0.2)
        xmin, xmax = emb[:, 0].min() - 2, emb[:, 0].max() + 2
        ymin, ymax = emb[:, 1].min() - 2, emb[:, 1].max() + 2
        xx, yy = np.meshgrid(np.linspace(xmin, xmax, 150),
                             np.linspace(ymin, ymax, 150))
        positions = np.vstack([xx.ravel(), yy.ravel()])
        zz = kde(positions).reshape(xx.shape)

        # invert: show LOW density as bright (= empty regions = ghost chairs)
        ghost_density = 1.0 / (zz + zz.max() * 0.1)
        ghost_density = (ghost_density - ghost_density.min()) / (ghost_density.max() - ghost_density.min())

        ax.contourf(xx, yy, ghost_density, levels=20, cmap="Purples", alpha=0.4)
        ax.contour(xx, yy, zz, levels=8, colors=C1, alpha=0.3, linewidths=0.5)
    except Exception:
        pass

    # real chairs
    ax.scatter(emb[:, 0], emb[:, 1], c=mesh_df["year"].values, cmap="magma",
               s=20, alpha=0.8, edgecolors="white", linewidths=0.3,
               norm=Normalize(1300, 2025), zorder=3)

    # find and mark empty regions (low density peaks)
    try:
        # find local minima of density
        from scipy.ndimage import minimum_filter
        local_min = minimum_filter(zz, size=20) == zz
        # only minima that are surrounded by data (not at edges)
        mask = local_min & (zz < np.percentile(zz[zz > 0], 30)) & (zz > 0)
        ghost_y, ghost_x = np.where(mask)

        for gy, gx in zip(ghost_y[:15], ghost_x[:15]):
            gx_coord = xx[gy, gx]
            gy_coord = yy[gy, gx]
            ax.scatter(gx_coord, gy_coord, marker="*", c=C5, s=100,
                       alpha=0.8, zorder=5, edgecolors="white", linewidths=0.5)

        ax.scatter([], [], marker="*", c=C5, s=100, label="Spøkelsesstolar (lacunae)")
    except Exception:
        pass

    ax.set_xlabel("UMAP-1", color="white", fontsize=10)
    ax.set_ylabel("UMAP-2", color="white", fontsize=10)
    ax.set_title("Spøkelsesstolar: tomme regionar i morforommet",
                 color="white", fontsize=12, pad=10)
    ax.legend(fontsize=9, facecolor=DARK, edgecolor="#444", labelcolor="white",
              loc="upper right")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#333")

    fig.savefig(os.path.join(FIG, "fig10_spokelsesstolar.png"), facecolor=DARK)
    fig.savefig(os.path.join(FIG, "fig10_spokelsesstolar.pdf"), facecolor=DARK)
    plt.close()
    print("  ✓ fig10_spokelsesstolar")


def compute_stats(mesh_df, sil_df):
    """Print key stats."""
    print("\n" + "=" * 60)
    print("NØKKELTAL FOR ARTIKKEL VII: FASEROM")
    print("=" * 60)
    print(f"  n_meshes: {len(mesh_df)}")
    print(f"  n_silhouettes: {len(sil_df)}")
    if "anisotropy" in mesh_df.columns:
        print(f"  median anisotropy: {mesh_df['anisotropy'].median():.3f}")
    if "sphericity" in mesh_df.columns:
        print(f"  median sphericity: {mesh_df['sphericity'].median():.3f}")
    if "convex_hull_ratio" in mesh_df.columns:
        print(f"  median CHR: {mesh_df['convex_hull_ratio'].median():.3f}")
    if "fractal_dim" in sil_df.columns:
        valid = sil_df["fractal_dim"].dropna()
        valid = valid[(valid > 1) & (valid < 2)]
        print(f"  median fractal dim: {valid.median():.3f}")
        print(f"  fractal dim std: {valid.std():.3f}")
    lambda_cols = [c for c in mesh_df.columns if c.startswith("lambda_")]
    if lambda_cols:
        first_nonzero = mesh_df[lambda_cols[0]]
        print(f"  median lambda_1: {first_nonzero.median():.4f}")
    print("=" * 60)


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t0 = time.time()
    print("=" * 60)
    print("ARTIKKEL VII: FASEROM")
    print("Den skjulte geometrien til forma")
    print("=" * 60)

    print("\n1. Lastar metadata...")
    df = load_data()
    print(f"   {len(df)} stolar i databasen")

    print("\n2. Fig 1: Silhuett-grid...")
    fig1_silhouette_grid(df)

    print("\n3. Prosesserer 3D-mesh (Shape DNA, tregheit, topologi)...")
    mesh_df = process_meshes(df, max_meshes=300)

    print("\n4. Prosesserer silhuettar (Fourier, fraktal)...")
    sil_df, all_fourier = process_silhouettes(df, max_sil=500)

    print("\n5. Genererer figurar...")
    fig2_shape_dna_spectrogram(mesh_df)
    fig3_inertia_atlas(mesh_df)
    fig4_fourier_reconstruction(df)
    fig5_fractal_dimension(sil_df)
    fig6_shape_dna_umap(mesh_df)
    fig7_crosssection_evolution(mesh_df)
    fig8_topology_scatter(mesh_df)
    fig9_circularity_solidity(sil_df)
    fig10_ghost_chairs(mesh_df)

    print("\n6. Statistikk...")
    compute_stats(mesh_df, sil_df)

    elapsed = time.time() - t0
    print(f"\n✓ Ferdig! ({elapsed:.1f}s)")
    print(f"✓ Alle figurar lagra i {FIG}")
