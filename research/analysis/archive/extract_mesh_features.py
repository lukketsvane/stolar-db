#!/usr/bin/env python3
"""
Extract per-chair mesh features from STOLAR/glb/*.glb.

Output: analysis/mesh_features.csv with one row per chair.

Features extracted (substrate-independent shape descriptors):
  bbox H/W/D       physical dimensions (m)
  vol_bbox         bounding-box volume
  vol_hull         convex-hull volume
  vol_mesh         watertight mesh volume (NaN if not watertight)
  area             surface area (m²)
  sphericity       (π^(1/3) (6 V_hull)^(2/3)) / area
  fill_ratio       vol_hull / vol_bbox
  vert_centroid    centroid Z, normalized by H (0 = bottom, 1 = top)
  inertia_ratio    smallest / largest principal moment (0 = rod, 1 = sphere)
  complexity       log10(vertices / area), proxy for local detail
  n_verts, n_faces raw mesh complexity

Loads in batches of 60–80 with gc.collect after each.
"""
from __future__ import annotations
import csv
import gc
import os
import sys
import warnings
from pathlib import Path
from typing import Iterable

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

warnings.filterwarnings('ignore', category=DeprecationWarning)

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
GLB_DIR = ROOT / 'STOLAR' / 'glb'
OUT = ROOT / 'analysis' / 'mesh_features.csv'
BATCH_SIZE = 64

FEATURE_COLS = [
    'objekt_id', 'n_verts', 'n_faces',
    'bbox_x', 'bbox_y', 'bbox_z',
    'vol_bbox', 'vol_hull', 'vol_mesh',
    'area',
    'sphericity', 'fill_ratio',
    'vert_centroid_norm',
    'inertia_smallest', 'inertia_middle', 'inertia_largest',
    'inertia_ratio',
    'complexity',
    'is_watertight',
    'load_error',
]


def extract(path: Path) -> dict:
    """Return a dict of features for one GLB. Returns NaN-filled row on error."""
    rec = {c: float('nan') for c in FEATURE_COLS}
    rec['objekt_id'] = path.stem.replace('_textured', '')
    rec['load_error'] = ''
    try:
        scene = trimesh.load(str(path), force='scene')
        # Concatenate all geometries into one mesh
        if isinstance(scene, trimesh.Scene):
            geoms = list(scene.geometry.values())
            if not geoms:
                rec['load_error'] = 'empty_scene'
                return rec
            mesh = trimesh.util.concatenate(geoms)
        else:
            mesh = scene
        rec['n_verts'] = len(mesh.vertices)
        rec['n_faces'] = len(mesh.faces)

        bbox = mesh.bounds  # 2x3
        ext = bbox[1] - bbox[0]
        rec['bbox_x'] = float(ext[0])
        rec['bbox_y'] = float(ext[1])
        rec['bbox_z'] = float(ext[2])
        rec['vol_bbox'] = float(ext[0] * ext[1] * ext[2])

        # Compute convex hull once and reuse for volume + area + sphericity + inertia
        hull_area = float('nan')
        try:
            hull = mesh.convex_hull
            rec['vol_hull'] = float(hull.volume)
            hull_area = float(hull.area)
        except Exception:
            hull = None
            rec['vol_hull'] = float('nan')

        rec['is_watertight'] = float(mesh.is_watertight)
        if mesh.is_watertight:
            rec['vol_mesh'] = float(mesh.volume)

        rec['area'] = float(mesh.area)

        # Wadell sphericity: ratio of (sphere area for same volume) / (actual area).
        # Use convex-hull volume vs convex-hull area so the ratio is bounded in (0, 1].
        if rec['vol_hull'] > 0 and hull_area > 0:
            rec['sphericity'] = float(
                (np.pi ** (1.0 / 3.0)) * ((6.0 * rec['vol_hull']) ** (2.0 / 3.0)) / hull_area
            )
        if rec['vol_bbox'] > 0:
            rec['fill_ratio'] = rec['vol_hull'] / rec['vol_bbox'] if rec['vol_hull'] > 0 else float('nan')

        # Vertical centroid: assume Y or Z is up — use the axis with the largest extent as "up"
        # In glTF the convention is Y-up; verify by picking the largest extent if ambiguous
        verts = mesh.vertices
        # treat axis 1 (Y) as up by default, since glTF
        z = verts[:, 1]
        h = ext[1]
        if h > 0:
            rec['vert_centroid_norm'] = float((z.mean() - bbox[0, 1]) / h)

        # Principal moments of inertia from convex hull (more stable than from raw mesh)
        try:
            if hull is None:
                hull = mesh.convex_hull
            inertia = hull.moment_inertia  # 3x3
            evals = np.sort(np.linalg.eigvalsh(inertia))
            rec['inertia_smallest'] = float(evals[0])
            rec['inertia_middle'] = float(evals[1])
            rec['inertia_largest'] = float(evals[2])
            if evals[2] > 0:
                rec['inertia_ratio'] = float(evals[0] / evals[2])
        except Exception:
            pass

        if rec['area'] > 0 and rec['n_verts'] > 0:
            rec['complexity'] = float(np.log10(rec['n_verts'] / rec['area']))

    except Exception as e:
        rec['load_error'] = str(e)[:120]
    return rec


def batched(iterable: Iterable, n: int):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= n:
            yield batch
            batch = []
    if batch:
        yield batch


def main() -> int:
    if not GLB_DIR.exists():
        print(f"ERROR: {GLB_DIR} not found", file=sys.stderr)
        return 1
    glbs = sorted(p for p in GLB_DIR.glob('*.glb') if not p.name.endswith('_textured.glb'))
    print(f"glb files: {len(glbs)}")
    print(f"output: {OUT}")
    print(f"batch size: {BATCH_SIZE}\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FEATURE_COLS)
        w.writeheader()

        done = 0
        errors = 0
        for batch_idx, batch in enumerate(batched(glbs, BATCH_SIZE), start=1):
            for path in batch:
                rec = extract(path)
                if rec.get('load_error'):
                    errors += 1
                w.writerow(rec)
                done += 1
            f.flush()
            gc.collect()
            print(f"batch {batch_idx}: {done}/{len(glbs)} processed, {errors} errors")

    print(f"\ndone. {done} chairs, {errors} errors. wrote {OUT}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
