"""Iter 03 — ta ein stol, vis RAW og etter Y→Z rotasjon. Rask."""
from pathlib import Path
import numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "writings" / "figures" / "formlaere" / "iter03.png"

def render(ax, v, f, title):
    tri = v[f]
    coll = Poly3DCollection(tri, facecolors=(0.7, 0.2, 0.2, 0.9),
                            edgecolors=(0, 0, 0, 0.05), linewidths=0.03)
    ax.add_collection3d(coll)
    lo, hi = v.min(axis=0), v.max(axis=0)
    span = (hi - lo).max()
    mid = 0.5 * (lo + hi)
    ax.set_xlim(mid[0] - span/2, mid[0] + span/2)
    ax.set_ylim(mid[1] - span/2, mid[1] + span/2)
    ax.set_zlim(mid[2] - span/2, mid[2] + span/2)
    ax.set_box_aspect([1, 1, 1])
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
    ax.view_init(elev=15, azim=-55)
    ax.set_title(title, fontsize=9)

# candidate chairs: pick a handful and print extents so we see
ids = ["NMK.2005.0581", "NMK.2005.0640", "NMK.2005.0643", "O131727"]
fig = plt.figure(figsize=(16, 8))
for k, oid in enumerate(ids):
    p = REPO / "STOLAR" / "glb" / f"{oid}.glb"
    m = trimesh.load(p, force="mesh")
    v = np.asarray(m.vertices); f = np.asarray(m.faces)
    ext = (v.max(axis=0) - v.min(axis=0))

    # RAW
    ax1 = fig.add_subplot(2, 4, k + 1, projection="3d")
    render(ax1, v, f, f"{oid} RAW  ext={ext.round(2)}")

    # Rotate so that Y (tallest GLB axis for typical chairs) becomes Z
    R = trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0])
    m2 = m.copy(); m2.apply_transform(R)
    v2 = np.asarray(m2.vertices); f2 = np.asarray(m2.faces)
    ax2 = fig.add_subplot(2, 4, 4 + k + 1, projection="3d")
    render(ax2, v2, f2, f"{oid} etter Y→Z rot")

fig.savefig(OUT, dpi=120, bbox_inches="tight")
print("wrote", OUT)
