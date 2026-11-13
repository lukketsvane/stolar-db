"""38b_ramme3d_ekstra.py - fleire 3D-trekk per stol, rett frå punktskyene: tyngdepunkt, veltemargin, flateretningar,
asymmetri, massefordeling i høgda og fylling.

  python analyse/38b_ramme3d_ekstra.py   -> analyse/data/ramme3d_ekstra.npz
"""
import csv, importlib.util, os, sys
import numpy as np
import ramme

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("r3", os.path.join(HER, "38_ramme3d.py"))
r3 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r3)
NAMN = ["tp_x", "tp_y", "tp_z", "margin_bak", "margin_fram", "margin_side", "velt_bak_grad", "velt_fram_grad", "velt_side_grad",
        "flate_opp", "flate_ned", "flate_loddrett", "flate_fram", "flate_bak", "asymmetri", "hylster_volum", "boks_volum", "fylling"]


def straale(hull_pts, o, d):
    """Avstand frå punktet o langs retninga d til kanten av det konvekse hylsteret (2D)."""
    best = np.inf
    n = len(hull_pts)
    for i in range(n):
        a, b = hull_pts[i], hull_pts[(i + 1) % n]
        e = b - a
        den = d[0] * e[1] - d[1] * e[0]
        if abs(den) < 1e-12:
            continue
        t = ((a[0] - o[0]) * e[1] - (a[1] - o[1]) * e[0]) / den
        u = ((a[0] - o[0]) * d[1] - (a[1] - o[1]) * d[0]) / den
        if t > 0 and -1e-9 <= u <= 1 + 1e-9:
            best = min(best, t)
    return float(best) if np.isfinite(best) else np.nan


if __name__ == "__main__":
    from scipy.spatial import ConvexHull
    R = ramme.last()
    mm = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "mesh_maal.csv"), encoding="utf-8"))}
    n = len(R["id"])
    E = np.full((n, len(NAMN)), np.nan)
    LAG = np.zeros((n, 60), np.float32)
    for k, cid in enumerate(R["id"]):
        zf = np.load(os.path.join(r3.CACHE, cid + ".npz"))
        x, y, z, nx, ny, nz = r3.kanonisk(zf["p"], zf["n"], mm[cid], float(R["H"][k]))
        tp = np.array([x.mean(), y.mean(), z.mean()])
        E[k, 0:3] = tp
        golv = z < 3
        if golv.sum() > 200:
            try:
                g = np.column_stack([x[golv], y[golv]])
                g = g[:: max(1, len(g) // 4000)]
                h = g[ConvexHull(g).vertices]
                E[k, 3] = straale(h, tp[:2], np.array([-1.0, 0.0]))
                E[k, 4] = straale(h, tp[:2], np.array([1.0, 0.0]))
                E[k, 5] = min(straale(h, tp[:2], np.array([0.0, 1.0])), straale(h, tp[:2], np.array([0.0, -1.0])))
                E[k, 6:9] = np.degrees(np.arctan(E[k, 3:6] / max(tp[2], 1e-6)))
            except Exception:
                pass
        E[k, 9], E[k, 10] = float((nz > 0.8).mean()), float((nz < -0.8).mean())
        E[k, 11], E[k, 12], E[k, 13] = float((np.abs(nz) < 0.3).mean()), float((nx > 0.8).mean()), float((nx < -0.8).mean())
        g3 = np.zeros((60, 64, 64), bool)
        ix, iy, iz = np.floor((x + 80) / 2.5).astype(int), np.floor((y + 80) / 2.5).astype(int), np.floor(z / 2.5).astype(int)
        ok = (ix >= 0) & (ix < 64) & (iy >= 0) & (iy < 64) & (iz >= 0) & (iz < 60)
        g3[iz[ok], ix[ok], iy[ok]] = True
        sp = g3[:, :, ::-1]
        E[k, 14] = 1 - (g3 & sp).sum() / max((g3 | sp).sum(), 1)
        try:
            P = np.column_stack([x, y, z])[::30]
            E[k, 15] = float(ConvexHull(P).volume)
        except Exception:
            pass
        E[k, 16] = float(np.ptp(x) * np.ptp(y) * np.ptp(z))
        E[k, 17] = E[k, 15] / E[k, 16] if E[k, 16] > 0 else np.nan
        LAG[k] = np.bincount(iz[ok], minlength=60)[:60] / len(z)
        if k % 200 == 0:
            print(k, "av", n, flush=True)
    np.savez_compressed(os.path.join(HER, "data", "ramme3d_ekstra.npz"), id=R["id"], ekstra=E, namn=np.array(NAMN), lag=LAG)
    print("ferdig", {a: round(float(np.nanmedian(E[:, j])), 2) for j, a in enumerate(NAMN)})
