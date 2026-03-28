"""
STOLAR -- 3D-punktsky MORPH-animasjon
Smooth interpolering mellom stolar sortert kronologisk.
Fast kamera -- punktskya morphar frå éin stol til neste.
256x256px, svart bakgrunn, cyan-magenta gradient.

Køyr frå prosjektrota:
  python pipeline/viz_pointcloud_frames.py
"""

import sys, os, warnings
sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm
from PIL import Image, ImageDraw, ImageFont

# ── Config ──
N_POINTS = 2000          # punkt per stol
N_CHAIRS = 100           # antal stolar i serien
INTERP_FRAMES = 8        # interpoleringsframes mellom kvar stol
HOLD_FRAMES = 2          # frames som held på kvar stol
IMG_SIZE = 256
DPI = 128
ELEV = 20
AZIM = 235               # fast kameravinkel
OUT_DIR = "results/pointcloud_frames"
os.makedirs(OUT_DIR, exist_ok=True)

CMAP = cm.get_cmap("cool")

# ── Last metadata ──
print("Lastar STOLAR-data...")
df = pd.read_csv("STOLAR/STOLAR_all.csv", encoding="utf-8-sig")
df.columns = [c.strip() for c in df.columns]
H = "Høgde (cm)"; W = "Breidde (cm)"; D = "Djupn (cm)"
FRA = "Frå år"; TIL = "Til år"; MAT = "Materialar"
STI = "Stilperiode"; OBJ = "Objekt-ID"; GLB = "3D-modell"; NAMN = "Namn"

df["midtaar"] = (df[FRA].fillna(df[TIL]) + df[TIL].fillna(df[FRA])) / 2
df["primmat"] = df[MAT].apply(lambda s: s.split(",")[0].strip() if pd.notna(s) else "Ukjend")

# ── Finn GLB-filer ──
glb_dir = "STOLAR/glb"
available_glbs = set(os.listdir(glb_dir))


def find_glb(row):
    g = row.get(GLB, "")
    if pd.notna(g) and str(g) in available_glbs:
        return str(g)
    oid = row.get(OBJ, "")
    if pd.notna(oid):
        c = f"{oid}.glb"
        if c in available_glbs:
            return c
    return None


df["glb_file"] = df.apply(find_glb, axis=1)
has_glb = df.dropna(subset=["glb_file", "midtaar"]).copy()
has_glb = has_glb[(has_glb[H] > 20) & (has_glb[W] > 10)]
has_glb = has_glb.sort_values("midtaar").reset_index(drop=True)

# Vel N_CHAIRS jamt fordelt
n_avail = len(has_glb)
idxs = np.linspace(0, n_avail - 1, N_CHAIRS, dtype=int)
selection = has_glb.iloc[idxs].reset_index(drop=True)
print(f"  {n_avail} stolar tilgjengeleg, vel {N_CHAIRS} for morph-serie")

total_frames = N_CHAIRS * HOLD_FRAMES + (N_CHAIRS - 1) * INTERP_FRAMES
print(f"  Totalt: {total_frames} frames ({HOLD_FRAMES} hold + {INTERP_FRAMES} interp per stol)")

# ── Fonts ──
try:
    FONT_BIG = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 16)
    FONT_SM = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 9)
except Exception:
    FONT_BIG = ImageFont.load_default()
    FONT_SM = FONT_BIG

FIGSIZE = IMG_SIZE / DPI


def load_pointcloud(glb_path):
    """Sample punkt frå GLB-mesh, normaliser til [-1, 1]."""
    try:
        scene = trimesh.load(glb_path)
        if isinstance(scene, trimesh.Scene):
            meshes = [g for g in scene.geometry.values()
                      if isinstance(g, trimesh.Trimesh) and len(g.faces) > 10]
            if not meshes:
                return None
            mesh = trimesh.util.concatenate(meshes)
        else:
            mesh = scene
        pts = mesh.sample(N_POINTS)
        center = pts.mean(axis=0)
        pts -= center
        scale = np.abs(pts).max()
        if scale > 0:
            pts /= scale
        return pts
    except Exception:
        return None


def sort_points(pts):
    """Sorter punktsky etter sfærisk vinkel for stabil korrespondanse."""
    angles = np.arctan2(pts[:, 2], pts[:, 0])  # vinkel i XZ-planet
    order = np.lexsort((pts[:, 1], angles))     # primær: vinkel, sekundær: høgde
    return pts[order]


def ease_in_out(t):
    """Smooth easing: sakte start og slutt, rask i midten."""
    return t * t * (3 - 2 * t)


def render_pts(pts, frame_nr, total, year_str, info_str, progress):
    """Render punktsky med fast kamera, returnerer PIL Image."""
    fig = plt.figure(figsize=(FIGSIZE, FIGSIZE), dpi=DPI)
    ax = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("#0a0a0f")
    ax.set_facecolor("#0a0a0f")

    y_vals = pts[:, 1]
    norm = Normalize(vmin=-1, vmax=1)
    colors = CMAP(norm(y_vals))
    colors[:, :3] = colors[:, :3] * 0.6 + 0.4
    colors[:, 3] = 0.85

    ax.scatter(pts[:, 0], pts[:, 2], pts[:, 1],
               c=colors, s=1.5, edgecolors="none",
               depthshade=True, rasterized=True)

    ax.view_init(elev=ELEV, azim=AZIM)
    ax.set_axis_off()
    for a in [ax.xaxis, ax.yaxis, ax.zaxis]:
        a.pane.fill = False
        a.pane.set_edgecolor("none")
    ax.grid(False)
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)
    plt.subplots_adjust(left=0, right=1, top=0.92, bottom=0.04)

    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(h, w, 4)
    img = Image.fromarray(buf[:, :, :3])
    plt.close(fig)

    # Tekstoverlay
    draw = ImageDraw.Draw(img)
    draw.text((8, 4), year_str, fill="#ffffff", font=FONT_BIG)

    prog_txt = f"{frame_nr + 1}/{total}"
    bbox = draw.textbbox((0, 0), prog_txt, font=FONT_SM)
    draw.text((IMG_SIZE - bbox[2] - 8, 6), prog_txt, fill="#666", font=FONT_SM)

    draw.text((8, IMG_SIZE - 16), info_str, fill="#888", font=FONT_SM)

    draw.rectangle([0, IMG_SIZE - 2, int(IMG_SIZE * progress), IMG_SIZE], fill="#52b788")

    return img


# ── Pre-last alle punktskyer ──
print("\nLastar punktskyer...")
clouds = []
meta = []
for i, (_, row) in enumerate(selection.iterrows()):
    glb_path = os.path.join(glb_dir, row["glb_file"])
    pts = load_pointcloud(glb_path)
    if pts is not None:
        pts = sort_points(pts)
        clouds.append(pts)
        meta.append(row)
    if (i + 1) % 20 == 0:
        print(f"  {i+1}/{N_CHAIRS} lasta ({len(clouds)} OK)")

print(f"  {len(clouds)} punktskyer klare")

# Oppdater totalt antal frames
N = len(clouds)
total_frames = N * HOLD_FRAMES + (N - 1) * INTERP_FRAMES

# ── Render morph-serie ──
print(f"\nRendrar {total_frames} frames til {OUT_DIR}/...")
frame_nr = 0

for ci in range(N):
    row = meta[ci]
    year = int(row["midtaar"])
    mat = row["primmat"]
    stil = row.get(STI, "")
    info = mat
    if pd.notna(stil) and str(stil).strip():
        info += f"  ·  {stil}"

    # Hold-frames: vis stolen som han er
    for _ in range(HOLD_FRAMES):
        img = render_pts(clouds[ci], frame_nr, total_frames,
                         str(year), info, (frame_nr + 1) / total_frames)
        img.save(os.path.join(OUT_DIR, f"frame_{frame_nr:04d}.png"), "PNG")
        frame_nr += 1

    # Interpolering til neste stol
    if ci < N - 1:
        next_row = meta[ci + 1]
        next_year = int(next_row["midtaar"])
        next_mat = next_row["primmat"]
        next_stil = next_row.get(STI, "")
        next_info = next_mat
        if pd.notna(next_stil) and str(next_stil).strip():
            next_info += f"  ·  {next_stil}"

        for fi in range(INTERP_FRAMES):
            t = ease_in_out((fi + 1) / (INTERP_FRAMES + 1))
            pts_interp = (1 - t) * clouds[ci] + t * clouds[ci + 1]

            # Interpoler årstal og tekst
            yr_interp = int((1 - t) * year + t * next_year)
            info_interp = info if t < 0.5 else next_info

            img = render_pts(pts_interp, frame_nr, total_frames,
                             str(yr_interp), info_interp,
                             (frame_nr + 1) / total_frames)
            img.save(os.path.join(OUT_DIR, f"frame_{frame_nr:04d}.png"), "PNG")
            frame_nr += 1

    if (ci + 1) % 10 == 0:
        print(f"  stol {ci+1}/{N} ({year}) -- frame {frame_nr}/{total_frames}")

print(f"\nFERDIG: {frame_nr} frames i {OUT_DIR}/")
print(f"  @ 30fps = {frame_nr/30:.0f}s video")
