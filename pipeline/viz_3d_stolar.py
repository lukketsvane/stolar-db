"""
STOLAR -- 3D-visualiseringar frå GLB-meshdata
Samplar punktskyer frå faktiske stol-mesh og lagar:
  1. Stor punktsky-tidslinje (100+ stolar side om side)
  2. Material-morforom (PCA av 3D-silhuettar)
  3. Grid-atlas av stol-silhuettar (sidevisning)
  4. Animert GIF av stol-evolusjon over tid
"""

import sys, os, warnings, glob, json
sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import trimesh
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
import io

os.makedirs("figurar", exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 180,
    "font.family": "serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

GRØN = ["#d8f3dc", "#b7e4c7", "#95d5b2", "#74c69d", "#52b788", "#40916c", "#2d6a4f", "#1b4332"]
cmap_grøn = LinearSegmentedColormap.from_list("stolar", GRØN, N=256)

# ── Last metadata ──
df = pd.read_csv("STOLAR/STOLAR_all.csv", encoding="utf-8")
df.columns = [c.strip() for c in df.columns]

col = {}
for c in df.columns:
    lc = c.lower()
    if "h" in lc and "gde" in lc and "sete" not in lc: col["H"] = c
    elif "breidd" in lc: col["B"] = c
    elif "djupn" in lc: col["D"] = c
    elif "vekt" in lc: col["V"] = c
    elif "fr" in lc and "r" in lc and len(c) < 8: col["FRA"] = c
    elif "til" in lc and "r" in lc and len(c) < 8: col["TIL"] = c
    elif "material" in lc and "komm" not in lc: col["MAT"] = c
    elif "stilperiode" in lc: col["STI"] = c
    elif "nasjon" in lc and "museet" not in lc: col["NAS"] = c
    elif "objekt" in lc: col["ID"] = c
    elif "3d" in lc: col["GLB"] = c

df["midtaar"] = (df[col["FRA"]].fillna(df[col["TIL"]]) + df[col["TIL"]].fillna(df[col["FRA"]])) / 2
df["primmat"] = df[col["MAT"]].apply(lambda s: s.split(",")[0].strip() if pd.notna(s) else np.nan)

# Map GLB filenames to rows
glb_dir = "STOLAR/glb"
available_glbs = set(os.listdir(glb_dir))


def find_glb(row):
    """Finn GLB-fil for ein rad."""
    glb_name = row.get(col["GLB"], "")
    if pd.notna(glb_name) and glb_name in available_glbs:
        return glb_name
    obj_id = row.get(col["ID"], "")
    if pd.notna(obj_id):
        candidate = f"{obj_id}.glb"
        if candidate in available_glbs:
            return candidate
    return None


df["glb_file"] = df.apply(find_glb, axis=1)
has_glb = df.dropna(subset=["glb_file", "midtaar"])
print(f"Stolar med GLB + metadata: {len(has_glb)}")


def load_pointcloud(glb_path, n_points=200):
    """Sample n_points frå ein GLB-mesh."""
    try:
        mesh = trimesh.load(glb_path, force="mesh")
        pts = mesh.sample(n_points)
        # Normaliser til einingskube [-1, 1]
        center = pts.mean(axis=0)
        pts -= center
        scale = np.abs(pts).max()
        if scale > 0:
            pts /= scale
        return pts
    except Exception as e:
        return None


# ══════════════════════════════════════════════════════════════════
# FIG A: Stor tidslinje -- stol-silhuettar langs tidsakse
# Sample 120 stolar jamt fordelt i tid, vis sidevisning (Y vs X)
# ══════════════════════════════════════════════════════════════════
print("Fig A: Tidslinje med 3D-punktskyer...")

sorted_chairs = has_glb.sort_values("midtaar")
n_show = min(120, len(sorted_chairs))
step = max(1, len(sorted_chairs) // n_show)
selection = sorted_chairs.iloc[::step].head(n_show).copy()

# Grid layout: chairs spread along x by year, shown as point cloud silhouettes
fig, ax = plt.subplots(figsize=(40, 8))
ax.set_facecolor("#0a0a0a")
fig.patch.set_facecolor("#0a0a0a")

x_positions = np.linspace(0, 100, len(selection))
loaded = 0

mat_colors = {
    "Eik": "#d4a373", "Bjørk": "#e9c46a", "Mahogni": "#9c6644",
    "Bøk": "#c8a882", "Furu": "#a3b18a", "Valnøtt": "#6b4226",
    "Stål": "#adb5bd", "Aluminium": "#dee2e6", "Plast": "#ff6b6b",
    "Rotting": "#ddb892", "Lær": "#774936", "Nøttetre": "#8b6914",
    "Bambus": "#7c9a3e",
}
default_color = "#52b788"

for i, (idx, row) in enumerate(selection.iterrows()):
    glb_path = os.path.join(glb_dir, row["glb_file"])
    pts = load_pointcloud(glb_path, n_points=150)
    if pts is None:
        continue

    mat = row.get("primmat", "")
    color = mat_colors.get(mat, default_color)
    year = row["midtaar"]

    # Sidevisning: Z (breidde) vs Y (høgde), offset langs tidsakse
    x_off = x_positions[i]
    ax.scatter(pts[:, 2] * 0.35 + x_off, pts[:, 1] * 0.35,
               s=0.3, alpha=0.6, color=color, rasterized=True)

    # Årstal under kvar 10. stol
    if i % 10 == 0:
        ax.text(x_off, -0.55, f"{int(year)}", color="#666666",
                fontsize=5, ha="center", va="top")
    loaded += 1

ax.set_xlim(-1, 101)
ax.set_ylim(-0.7, 0.6)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title(f"STOLAR -- {loaded} stolar i tid (punktskyer frå 3D-mesh)\nFargar = primærmaterial",
             color="white", fontsize=12, pad=10)

plt.tight_layout()
plt.savefig("figurar/exp_3d_tidslinje.png", bbox_inches="tight", facecolor="#0a0a0a")
plt.close()
print(f"  Lasta {loaded}/{n_show} stolar")


# ══════════════════════════════════════════════════════════════════
# FIG B: Stol-atlas -- 10x10 grid av stol-silhuettar
# ══════════════════════════════════════════════════════════════════
print("Fig B: Stol-atlas (10x10 grid)...")

n_grid = 100
step_g = max(1, len(sorted_chairs) // n_grid)
grid_sel = sorted_chairs.iloc[::step_g].head(n_grid)

fig, axes = plt.subplots(10, 10, figsize=(20, 20))
fig.patch.set_facecolor("#0a0a0a")

for i, (idx, row) in enumerate(grid_sel.iterrows()):
    r, c = i // 10, i % 10
    ax = axes[r][c]
    ax.set_facecolor("#0a0a0a")

    glb_path = os.path.join(glb_dir, row["glb_file"])
    pts = load_pointcloud(glb_path, n_points=300)

    mat = row.get("primmat", "")
    color = mat_colors.get(mat, default_color)
    year = int(row["midtaar"]) if pd.notna(row["midtaar"]) else 0

    if pts is not None:
        # Frontvisning: X vs Y
        ax.scatter(pts[:, 0], pts[:, 1], s=0.5, alpha=0.7, color=color, rasterized=True)

    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"{year}", color="#555555", fontsize=5, pad=1)

fig.suptitle("STOLAR -- Atlas av 100 stolar (frontvisning, punktskyer)\nKronologisk venstre-til-høgre, topp-til-botn",
             color="white", fontsize=14, y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("figurar/exp_3d_atlas.png", bbox_inches="tight", facecolor="#0a0a0a")
plt.close()
print("  Atlas ferdig")


# ══════════════════════════════════════════════════════════════════
# FIG C: Superpunksky -- ALLE stolar i eitt morforom
# PCA av form-deskriptorar henta frå mesh
# ══════════════════════════════════════════════════════════════════
print("Fig C: Superpunktsky (form-deskriptorar)...")

# Sampla form-deskriptorar: for kvar stol, ta bbox-ratio, flatness, elongation
descriptors = []
meta_rows = []

sample_n = min(500, len(has_glb))
sample_step = max(1, len(has_glb) // sample_n)
sample_sel = has_glb.iloc[::sample_step].head(sample_n)

for idx, row in sample_sel.iterrows():
    glb_path = os.path.join(glb_dir, row["glb_file"])
    try:
        mesh = trimesh.load(glb_path, force="mesh")
        ext = mesh.extents  # [x, y, z] size
        if ext.min() <= 0:
            continue
        # Form-deskriptorar
        ratio_xy = ext[0] / ext[1]  # breidde/høgde
        ratio_xz = ext[0] / ext[2]  # breidde/djupn
        ratio_yz = ext[1] / ext[2]  # høgde/djupn
        vol_norm = mesh.volume / (ext[0] * ext[1] * ext[2]) if mesh.is_watertight else 0.3
        descriptors.append([ratio_xy, ratio_xz, ratio_yz, vol_norm])
        meta_rows.append(row)
    except Exception:
        continue

print(f"  Lasta {len(descriptors)} form-deskriptorar")

if len(descriptors) > 20:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    X_desc = StandardScaler().fit_transform(np.array(descriptors))
    pca = PCA(n_components=2)
    pc = pca.fit_transform(X_desc)

    meta_df = pd.DataFrame(meta_rows)
    years = meta_df["midtaar"].values
    mats = meta_df["primmat"].values

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor("#0a0a0a")

    for ax in axes:
        ax.set_facecolor("#0a0a0a")

    # Farga etter tid
    sc = axes[0].scatter(pc[:, 0], pc[:, 1], c=years, cmap=cmap_grøn,
                          s=12, alpha=0.7, edgecolors="none")
    cb = plt.colorbar(sc, ax=axes[0])
    cb.ax.yaxis.set_tick_params(color="white")
    cb.ax.yaxis.label.set_color("white")
    plt.setp(plt.getp(cb.ax, "yticklabels"), color="white")
    axes[0].set_title("Form-rom (PCA av mesh-geometri)\nFarga etter tid", color="white", fontsize=11)
    axes[0].set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.0f}%)", color="white")
    axes[0].set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.0f}%)", color="white")
    axes[0].tick_params(colors="white")

    # Farga etter material
    top_mats = pd.Series(mats).value_counts().head(8).index
    for mat in top_mats:
        mask = mats == mat
        color = mat_colors.get(mat, default_color)
        axes[1].scatter(pc[mask, 0], pc[mask, 1], s=12, alpha=0.6,
                        color=color, label=mat, edgecolors="none")
    axes[1].set_title("Form-rom (PCA av mesh-geometri)\nFarga etter material", color="white", fontsize=11)
    axes[1].set_xlabel(f"PC1", color="white")
    axes[1].set_ylabel(f"PC2", color="white")
    axes[1].tick_params(colors="white")
    axes[1].legend(fontsize=8, facecolor="#1a1a1a", edgecolor="#333",
                   labelcolor="white", loc="upper right")

    plt.tight_layout()
    plt.savefig("figurar/exp_3d_morforom.png", bbox_inches="tight", facecolor="#0a0a0a")
    plt.close()


# ══════════════════════════════════════════════════════════════════
# FIG D: Animert GIF -- stol-evolusjon (30 frames, 50-års vindauge)
# ══════════════════════════════════════════════════════════════════
print("Fig D: Animert GIF av stol-evolusjon...")

frames = []
year_min = int(has_glb["midtaar"].min())
year_max = int(has_glb["midtaar"].max())
window = 50  # år per frame
step_yr = 25  # overlapp

for yr_start in range(max(year_min, 1400), year_max - window, step_yr):
    yr_end = yr_start + window
    sub = has_glb[(has_glb["midtaar"] >= yr_start) & (has_glb["midtaar"] < yr_end)]
    if len(sub) < 3:
        continue

    # Vis maks 9 stolar per frame
    show = sub.head(9)

    fig, axes_grid = plt.subplots(3, 3, figsize=(6, 6))
    fig.patch.set_facecolor("#0a0a0a")

    for ai in range(9):
        r, c = ai // 3, ai % 3
        ax = axes_grid[r][c]
        ax.set_facecolor("#0a0a0a")
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_aspect("equal")
        ax.axis("off")

        if ai < len(show):
            row = show.iloc[ai]
            glb_path = os.path.join(glb_dir, row["glb_file"])
            pts = load_pointcloud(glb_path, n_points=200)
            mat = row.get("primmat", "")
            color = mat_colors.get(mat, default_color)
            if pts is not None:
                ax.scatter(pts[:, 0], pts[:, 1], s=0.8, alpha=0.7,
                           color=color, rasterized=True)

    fig.suptitle(f"{yr_start}--{yr_end}", color="white", fontsize=16,
                 fontweight="bold", y=0.98)

    # Rendre til PIL
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", facecolor="#0a0a0a", dpi=100)
    plt.close()
    buf.seek(0)
    frames.append(Image.open(buf).copy())
    buf.close()

if frames:
    # Siste frame held lenger
    frames_extended = frames + [frames[-1]] * 3
    frames_extended[0].save(
        "figurar/exp_3d_evolusjon.gif",
        save_all=True,
        append_images=frames_extended[1:],
        duration=600,
        loop=0,
    )
    print(f"  GIF: {len(frames)} frames")


# ══════════════════════════════════════════════════════════════════
# FIG E: Stol-silhuett-stripe (kompakt, alle stolar i éi rekkje)
# ══════════════════════════════════════════════════════════════════
print("Fig E: Silhuett-stripe (kompakt)...")

n_stripe = min(200, len(sorted_chairs))
step_s = max(1, len(sorted_chairs) // n_stripe)
stripe_sel = sorted_chairs.iloc[::step_s].head(n_stripe)

fig, ax = plt.subplots(figsize=(50, 4))
ax.set_facecolor("#0a0a0a")
fig.patch.set_facecolor("#0a0a0a")

for i, (idx, row) in enumerate(stripe_sel.iterrows()):
    glb_path = os.path.join(glb_dir, row["glb_file"])
    pts = load_pointcloud(glb_path, n_points=100)
    if pts is None:
        continue

    mat = row.get("primmat", "")
    color = mat_colors.get(mat, default_color)
    year = row["midtaar"]

    # Alle stolar på rekkje, normalisert Y
    x_off = i * 0.8
    ax.scatter(pts[:, 0] * 0.3 + x_off, pts[:, 1] * 0.3,
               s=0.15, alpha=0.6, color=color, rasterized=True)

ax.set_xlim(-0.5, n_stripe * 0.8 + 0.5)
ax.set_ylim(-0.5, 0.5)
ax.set_aspect("equal")
ax.axis("off")

# Årstal-markørar
for i, (idx, row) in enumerate(stripe_sel.iterrows()):
    if i % 20 == 0:
        year = int(row["midtaar"])
        ax.text(i * 0.8, -0.45, str(year), color="#555", fontsize=4, ha="center")

fig.suptitle(f"STOLAR -- {n_stripe} stolar i kronologisk rekkje (punktskyer frå 3D-mesh)",
             color="white", fontsize=10, y=0.95)
plt.savefig("figurar/exp_3d_stripe.png", bbox_inches="tight", facecolor="#0a0a0a", dpi=200)
plt.close()


print("\n=== FERDIG: 5 figurar med 3D-data ===")
print("  exp_3d_tidslinje.png  -- 120 stolar langs tidsakse")
print("  exp_3d_atlas.png      -- 10x10 grid")
print("  exp_3d_morforom.png   -- PCA av mesh-geometri")
print("  exp_3d_evolusjon.gif  -- animert tidslinje")
print("  exp_3d_stripe.png     -- kompakt stripe av 200 stolar")
