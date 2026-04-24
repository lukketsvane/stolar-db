"""Iter 01 — render ein ekte GLB-stol. Ser eg ein stol som står?"""
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "writings" / "figures" / "formlaere" / "iter01.png"

# Pick a chair I know should be a canonical chair (an early NMK id).
GLB = REPO / "STOLAR" / "glb" / "NMK.2005.0591.glb"
mesh = trimesh.load(GLB, force="mesh")
print("loaded", GLB.name, "verts", len(mesh.vertices))
print("bounds:", mesh.bounds)
print("extent:", (mesh.bounds[1] - mesh.bounds[0]).round(3))

# Render without changing orientation — just show as the GLB stores it.
fig = plt.figure(figsize=(6, 6))
ax = fig.add_subplot(projection="3d")
v = np.asarray(mesh.vertices); f = np.asarray(mesh.faces)
tri = v[f]
coll = Poly3DCollection(tri, facecolors=(0.7, 0.2, 0.2, 0.92),
                        edgecolors=(0.1, 0.1, 0.1, 0.1), linewidths=0.05)
ax.add_collection3d(coll)
lo, hi = v.min(axis=0), v.max(axis=0)
span = (hi - lo).max()
mid = 0.5 * (lo + hi)
ax.set_xlim(mid[0] - span/2, mid[0] + span/2)
ax.set_ylim(mid[1] - span/2, mid[1] + span/2)
ax.set_zlim(mid[2] - span/2, mid[2] + span/2)
ax.set_box_aspect([1, 1, 1])
ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
ax.view_init(elev=18, azim=-55)
ax.set_title(f"{GLB.name}  —  raw orientering frå GLB-fil")
fig.savefig(OUT, dpi=140, bbox_inches="tight")
print("wrote", OUT)
