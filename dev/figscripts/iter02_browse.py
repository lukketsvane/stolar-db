"""Iter 02 — bla gjennom 16 tilfeldige GLB-ar for å finne ut korleis
formata er, og kva som faktisk ser ut som stolar i ro-orientering."""
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "writings" / "figures" / "formlaere" / "iter02.png"
GLB_DIR = REPO / "STOLAR" / "glb"

rng = np.random.default_rng(0)
glbs = [p for p in sorted(GLB_DIR.glob("*.glb"))
        if "_textured" not in p.name and
        not (p.stem.split("_")[-1].isdigit() and len(p.stem.split("_")[-1]) >= 5)]
print(f"total glbs: {len(glbs)}")
picked = rng.choice(glbs, size=16, replace=False)

fig = plt.figure(figsize=(14, 14))
for k, path in enumerate(picked):
    ax = fig.add_subplot(4, 4, k + 1, projection="3d")
    try:
        m = trimesh.load(path, force="mesh")
        v = np.asarray(m.vertices); f = np.asarray(m.faces)
        if len(v) == 0:
            ax.set_title(f"{path.stem} empty"); continue
        tri = v[f]
        coll = Poly3DCollection(tri, facecolors=(0.25, 0.35, 0.55, 0.9),
                                edgecolors=(0, 0, 0, 0.06), linewidths=0.04)
        ax.add_collection3d(coll)
        lo, hi = v.min(axis=0), v.max(axis=0)
        ext = hi - lo
        span = ext.max()
        mid = 0.5 * (lo + hi)
        ax.set_xlim(mid[0] - span/2, mid[0] + span/2)
        ax.set_ylim(mid[1] - span/2, mid[1] + span/2)
        ax.set_zlim(mid[2] - span/2, mid[2] + span/2)
        ax.set_box_aspect([1, 1, 1])
        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
        ax.set_xlabel("X", fontsize=6); ax.set_ylabel("Y", fontsize=6); ax.set_zlabel("Z", fontsize=6)
        ax.view_init(elev=18, azim=-55)
        ax.set_title(f"{path.stem}\next {ext[0]:.2f} × {ext[1]:.2f} × {ext[2]:.2f}",
                      fontsize=7)
    except Exception as e:
        ax.set_title(f"{path.stem} err: {e}", fontsize=6)
fig.savefig(OUT, dpi=130, bbox_inches="tight")
print("wrote", OUT)
