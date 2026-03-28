"""
STOLAR -- 3D-punktsky-frames (ALLE stolar)
Rendrar kvar stol som 3D-punktsky, sortert etter midtår.
256x256px, svart bakgrunn, cyan→magenta gradient.

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
N_POINTS = 2000
IMG_SIZE = 256
DPI = 128
OUT_DIR = "results/pointcloud_frames"
os.makedirs(OUT_DIR, exist_ok=True)

CMAP = cm.get_cmap("cool")

# ── Last metadata ──
print("Lastar STOLAR-data...")
df = pd.read_csv("STOLAR/STOLAR_all.csv", encoding="utf-8-sig")
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

N_TOTAL = len(has_glb)
print(f"  {N_TOTAL} stolar med GLB + metadata -- rendrar ALLE")

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


def render_frame(pts, frame_idx, total, year, material, stil):
    """Render ein stol som 3D-punktsky → PIL Image."""
    fig = plt.figure(figsize=(FIGSIZE, FIGSIZE), dpi=DPI)
    ax = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("#0a0a0f")
    ax.set_facecolor("#0a0a0f")

    y_vals = pts[:, 1]
    norm = Normalize(vmin=y_vals.min(), vmax=y_vals.max())
    colors = CMAP(norm(y_vals))
    colors[:, :3] = colors[:, :3] * 0.6 + 0.4
    colors[:, 3] = 0.85

    azim = 225 + (frame_idx / total) * 60
    ax.scatter(pts[:, 0], pts[:, 2], pts[:, 1],
               c=colors, s=1.5, edgecolors="none",
               depthshade=True, rasterized=True)

    ax.view_init(elev=20, azim=azim)
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
    draw.text((8, 4), str(int(year)), fill="#ffffff", font=FONT_BIG)

    prog = f"{frame_idx + 1}/{total}"
    bbox = draw.textbbox((0, 0), prog, font=FONT_SM)
    draw.text((IMG_SIZE - bbox[2] - 8, 6), prog, fill="#666", font=FONT_SM)

    bottom = material
    if pd.notna(stil) and str(stil).strip():
        bottom += f"  ·  {stil}"
    draw.text((8, IMG_SIZE - 16), bottom, fill="#888", font=FONT_SM)

    frac = (frame_idx + 1) / total
    draw.rectangle([0, IMG_SIZE - 2, int(IMG_SIZE * frac), IMG_SIZE], fill="#52b788")

    return img


# ── Render ALLE ──
print(f"\nRendrar {N_TOTAL} frames til {OUT_DIR}/...")
rendered = 0
skipped = 0

for i, (_, row) in enumerate(has_glb.iterrows()):
    glb_path = os.path.join(glb_dir, row["glb_file"])
    pts = load_pointcloud(glb_path)

    if pts is None:
        skipped += 1
        continue

    img = render_frame(
        pts, i, N_TOTAL,
        year=row["midtaar"],
        material=row["primmat"],
        stil=row.get(STI, ""),
    )

    out_path = os.path.join(OUT_DIR, f"frame_{i:04d}.png")
    img.save(out_path, "PNG")
    rendered += 1

    if (i + 1) % 100 == 0:
        print(f"  [{i+1:4d}/{N_TOTAL}] {row.get(OBJ, '?')} ({int(row['midtaar'])}) -- {rendered} ok, {skipped} skip")

print(f"\nFERDIG: {rendered} frames lagra, {skipped} hoppa over")
print(f"Output: {OUT_DIR}/frame_0000.png ... frame_{N_TOTAL-1:04d}.png")
