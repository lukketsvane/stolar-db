#!/usr/bin/env python3
"""
scale_all_glbs.py — Uniformly scale every GLB in NM_stolar/{objectId}/ so that
its bounding-box height matches the real-world height from the Mål metadata.

Scaling is uniform (preserves proportions). The model is also re-centered so that
the bottom sits at Y=0 and XZ center is at origin.

Backs up originals as *_prescale.glb (skips if backup already exists = already scaled).
"""

import json
import os
import re
import shutil
import struct
from pathlib import Path

import numpy as np

BASE = Path(__file__).parent
NM_DIR = BASE / "NM_stolar"
META_JSON = NM_DIR / "NM_stolar.json"


# ── Height parsing ───────────────────────────────────────────────────────────

def parse_height_cm(maal_str):
    """Extract height in cm from Mål string like 'H 95,5 x B 50,5 x D 49 cm'."""
    if not maal_str:
        return None
    s = str(maal_str)
    # Pattern: "H <number>" (labeled height)
    m = re.search(r'\bH\s*([\d]+[,.]?\d*)', s)
    if m:
        return float(m.group(1).replace(',', '.'))
    # Fallback: first number before 'x' (unlabeled, assume H x B x D)
    m = re.search(r'([\d]+[,.]?\d*)\s*x', s)
    if m:
        return float(m.group(1).replace(',', '.'))
    return None


# ── GLB read/write (binary, no trimesh needed) ──────────────────────────────

def read_glb(path):
    """Read GLB → (json_data, bin_data)."""
    with open(path, 'rb') as f:
        magic = f.read(4)
        if magic != b'glTF':
            raise ValueError(f"Not a GLB: {path}")
        version = struct.unpack('<I', f.read(4))[0]
        total_length = struct.unpack('<I', f.read(4))[0]

        chunk0_length = struct.unpack('<I', f.read(4))[0]
        chunk0_type = struct.unpack('<I', f.read(4))[0]
        json_bytes = f.read(chunk0_length)
        json_data = json.loads(json_bytes.decode('utf-8'))

        bin_data = b''
        remaining = total_length - 12 - 8 - chunk0_length
        if remaining > 0:
            chunk1_length = struct.unpack('<I', f.read(4))[0]
            chunk1_type = struct.unpack('<I', f.read(4))[0]
            bin_data = f.read(chunk1_length)

    return json_data, bin_data


def write_glb(path, json_data, bin_data):
    """Write GLB from json_data dict + binary buffer."""
    json_str = json.dumps(json_data, separators=(',', ':'))
    while len(json_str) % 4 != 0:
        json_str += ' '
    json_bytes = json_str.encode('utf-8')

    bin_padded = bin_data
    while len(bin_padded) % 4 != 0:
        bin_padded += b'\x00'

    total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_padded)

    with open(path, 'wb') as f:
        f.write(b'glTF')
        f.write(struct.pack('<I', 2))
        f.write(struct.pack('<I', total_length))
        f.write(struct.pack('<I', len(json_bytes)))
        f.write(struct.pack('<I', 0x4E4F534A))
        f.write(json_bytes)
        f.write(struct.pack('<I', len(bin_padded)))
        f.write(struct.pack('<I', 0x004E4942))
        f.write(bin_padded)


# ── Trimesh-based bounding box ───────────────────────────────────────────────

def get_bounds(glb_path):
    """Return (min_xyz, max_xyz) arrays using trimesh."""
    import trimesh
    scene = trimesh.load(str(glb_path))
    return scene.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]


# ── Scale + recenter via GLB node transforms ─────────────────────────────────

def apply_scale_and_center(glb_path, output_path, scale_factor, bounds):
    """Apply uniform scale and recenter (bottom at Y=0, XZ centered)."""
    json_data, bin_data = read_glb(glb_path)

    scenes = json_data.get('scenes', [])
    default_scene_idx = json_data.get('scene', 0)
    scene = scenes[default_scene_idx] if scenes else {}
    root_nodes = scene.get('nodes', [])
    nodes = json_data.get('nodes', [])

    # Compute translation to center + ground the model after scaling
    min_xyz, max_xyz = bounds
    cx = (min_xyz[0] + max_xyz[0]) / 2.0
    cy_bottom = min_xyz[1]
    cz = (min_xyz[2] + max_xyz[2]) / 2.0

    for node_idx in root_nodes:
        node = nodes[node_idx]

        if 'matrix' in node:
            mat = np.array(node['matrix'], dtype=np.float64).reshape(4, 4, order='F')
            # Build: translate to origin → scale → result
            T = np.eye(4)
            T[0, 3] = -cx
            T[1, 3] = -cy_bottom
            T[2, 3] = -cz
            S = np.eye(4)
            S[0, 0] = S[1, 1] = S[2, 2] = scale_factor
            new_mat = mat @ (S @ T)
            node['matrix'] = new_mat.flatten(order='F').tolist()
        else:
            existing_scale = node.get('scale', [1.0, 1.0, 1.0])
            node['scale'] = [
                existing_scale[0] * scale_factor,
                existing_scale[1] * scale_factor,
                existing_scale[2] * scale_factor,
            ]
            # Adjust translation: first center, then scale
            t = node.get('translation', [0.0, 0.0, 0.0])
            node['translation'] = [
                (t[0] - cx) * scale_factor,
                (t[1] - cy_bottom) * scale_factor,
                (t[2] - cz) * scale_factor,
            ]

    write_glb(output_path, json_data, bin_data)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    data = json.loads(META_JSON.read_text(encoding="utf-8"))
    print(f"Loaded {len(data)} entries from NM_stolar.json")

    # Build objectId → height_cm map
    height_map = {}
    for entry in data:
        oid = entry.get("objectId", "")
        h = parse_height_cm(entry.get("Mål", ""))
        if oid and h:
            height_map[oid] = h

    print(f"Heights parsed: {len(height_map)}")

    # Find all GLB files
    scaled = skipped_backup = skipped_no_height = errors = 0
    results = []

    dirs = sorted(
        d for d in NM_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )

    for obj_dir in dirs:
        oid = obj_dir.name
        glbs = [f for f in obj_dir.iterdir() if f.suffix == ".glb" and "_prescale" not in f.name]
        if not glbs:
            continue

        glb = glbs[0]

        # Skip if already scaled
        backup = glb.with_name(glb.stem + "_prescale.glb")
        if backup.exists():
            skipped_backup += 1
            continue

        # Get target height
        target_h = height_map.get(oid)
        if not target_h:
            skipped_no_height += 1
            continue

        target_h_m = target_h / 100.0

        try:
            bounds = get_bounds(glb)
            current_h = bounds[1][1] - bounds[0][1]  # max_y - min_y

            if current_h <= 0:
                print(f"  SKIP {oid}: zero height bounding box")
                errors += 1
                continue

            sf = target_h_m / current_h

            # Backup original
            shutil.copy2(glb, backup)

            # Apply scale + recenter
            apply_scale_and_center(str(backup), str(glb), sf, bounds)

            actual_h_after = current_h * sf * 100  # in cm
            results.append((oid, target_h, actual_h_after, sf))
            scaled += 1

            if scaled % 50 == 0:
                print(f"  ... scaled {scaled} so far")

        except Exception as e:
            print(f"  ERROR {oid}: {e}")
            # Restore backup if created
            if backup.exists() and not glb.exists():
                backup.rename(glb)
            elif backup.exists():
                backup.unlink()
            errors += 1

    # Summary
    print(f"\n{'='*70}")
    print(f"  Scaled: {scaled}")
    print(f"  Already scaled (backup exists): {skipped_backup}")
    print(f"  No height data: {skipped_no_height}")
    print(f"  Errors: {errors}")
    print(f"{'='*70}")

    if results:
        print(f"\n{'Object ID':<30} {'Target H':>10} {'Actual H':>10} {'Factor':>10}")
        print("-" * 62)
        for oid, target, actual, sf in results:
            print(f"  {oid:<28} {target:>8.1f}cm {actual:>8.1f}cm {sf:>10.4f}")

        # Verify tolerance
        max_err = max(abs(actual - target) / target * 100 for _, target, actual, _ in results)
        print(f"\n  Max height error: {max_err:.2f}%")


if __name__ == "__main__":
    main()
