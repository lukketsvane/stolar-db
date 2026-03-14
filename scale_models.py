#!/usr/bin/env python3
"""
scale_models.py — Skaler GLB-modellar til faktiske mål frå Nasjonalmuseet.
Brukar YAML-data for å finne rett dimensjon (H x B x D) for kvar stol,
les noverande storleik frå GLB-fila, og skalerer uniform til rett storleik.

Lagar backup (_original.glb) før skalering.
"""

import yaml
import re
import glob
import os
import sys
import shutil
import struct
import json
import numpy as np

# ============================================================
# 1. Parse dimensions from YAML
# ============================================================

def parse_dimensions_cm(mal_str):
    """Parse the 'Mål' field to extract H, B, D in cm.
    Returns (H, B, D) or None if parsing fails.
    """
    if not mal_str:
        return None
    s = str(mal_str)

    # Pattern 1: "H 95,5 x B 50,5 x D 49 cm" (with optional "cm" after each)
    m = re.search(
        r'H\s*([\d]+[,.]?\d*)\s*(?:cm\s*)?x\s*,?\s*B\s*([\d]+[,.]?\d*)\s*(?:cm\s*)?x\s*D\s*([\d]+[,.]?\d*)',
        s
    )
    if m:
        h = float(m.group(1).replace(',', '.'))
        b = float(m.group(2).replace(',', '.'))
        d = float(m.group(3).replace(',', '.'))
        return (h, b, d)

    # Pattern 2: "139 x 70,5 x 70 cm" (no H/B/D labels, assume H x B x D order)
    m = re.search(r'([\d]+[,.]?\d*)\s*x\s*([\d]+[,.]?\d*)\s*x\s*([\d]+[,.]?\d*)\s*cm', s)
    if m:
        h = float(m.group(1).replace(',', '.'))
        b = float(m.group(2).replace(',', '.'))
        d = float(m.group(3).replace(',', '.'))
        return (h, b, d)

    # Pattern 3: Circular "H 107 x ⌀ 62 cm" -> H=107, B=62, D=62
    m = re.search(r'H\s*([\d]+[,.]?\d*)\s*x\s*[⌀Ø]\s*([\d]+[,.]?\d*)\s*cm', s)
    if m:
        h = float(m.group(1).replace(',', '.'))
        diam = float(m.group(2).replace(',', '.'))
        return (h, diam, diam)

    return None


def load_yaml_dimensions(yaml_path):
    """Load YAML and return dict of objectId -> (H_cm, B_cm, D_cm)."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    dims = {}
    for item in data.get('items', []):
        objid = item.get('objectId', '')
        mal = item.get('Mål', '')
        parsed = parse_dimensions_cm(mal)
        if parsed and objid:
            dims[objid] = parsed
    return dims


# ============================================================
# 2. Read and modify GLB files
# ============================================================

def read_glb(path):
    """Read a GLB file and return (json_data, bin_data)."""
    with open(path, 'rb') as f:
        # GLB header: magic(4) + version(4) + length(4)
        magic = f.read(4)
        if magic != b'glTF':
            raise ValueError(f"Not a valid GLB file: {path}")
        version = struct.unpack('<I', f.read(4))[0]
        total_length = struct.unpack('<I', f.read(4))[0]

        # Chunk 0: JSON
        chunk0_length = struct.unpack('<I', f.read(4))[0]
        chunk0_type = struct.unpack('<I', f.read(4))[0]
        assert chunk0_type == 0x4E4F534A, "First chunk must be JSON"
        json_bytes = f.read(chunk0_length)
        json_data = json.loads(json_bytes.decode('utf-8'))

        # Chunk 1: BIN (optional)
        bin_data = b''
        remaining = total_length - 12 - 8 - chunk0_length
        if remaining > 0:
            chunk1_length = struct.unpack('<I', f.read(4))[0]
            chunk1_type = struct.unpack('<I', f.read(4))[0]
            assert chunk1_type == 0x004E4942, "Second chunk must be BIN"
            bin_data = f.read(chunk1_length)

    return json_data, bin_data


def write_glb(path, json_data, bin_data):
    """Write a GLB file from json_data dict and binary buffer."""
    json_str = json.dumps(json_data, separators=(',', ':'))
    # Pad JSON to 4-byte alignment with spaces
    while len(json_str) % 4 != 0:
        json_str += ' '
    json_bytes = json_str.encode('utf-8')

    # Pad BIN to 4-byte alignment with null bytes
    bin_padded = bin_data
    while len(bin_padded) % 4 != 0:
        bin_padded += b'\x00'

    total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_padded)

    with open(path, 'wb') as f:
        # Header
        f.write(b'glTF')
        f.write(struct.pack('<I', 2))  # version
        f.write(struct.pack('<I', total_length))

        # JSON chunk
        f.write(struct.pack('<I', len(json_bytes)))
        f.write(struct.pack('<I', 0x4E4F534A))
        f.write(json_bytes)

        # BIN chunk
        f.write(struct.pack('<I', len(bin_padded)))
        f.write(struct.pack('<I', 0x004E4942))
        f.write(bin_padded)


def get_glb_bounds_trimesh(path):
    """Get bounding box using trimesh. Returns (size_x, size_y, size_z) in meters."""
    import trimesh
    scene = trimesh.load(path)
    bounds = scene.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
    size = bounds[1] - bounds[0]
    return size  # in scene units (meters for glTF)


def apply_uniform_scale_to_glb(glb_path, scale_factor, output_path):
    """Apply uniform scale to a GLB file by modifying root node transforms."""
    json_data, bin_data = read_glb(glb_path)

    # Find root nodes (nodes referenced by the default scene)
    scenes = json_data.get('scenes', [])
    default_scene_idx = json_data.get('scene', 0)
    scene = scenes[default_scene_idx] if scenes else {}
    root_nodes = scene.get('nodes', [])

    nodes = json_data.get('nodes', [])

    for node_idx in root_nodes:
        node = nodes[node_idx]

        if 'matrix' in node:
            # Existing 4x4 matrix — apply scale
            mat = np.array(node['matrix'], dtype=np.float64).reshape(4, 4, order='F')
            scale_mat = np.eye(4) * scale_factor
            scale_mat[3, 3] = 1.0
            new_mat = mat @ scale_mat
            node['matrix'] = new_mat.flatten(order='F').tolist()
        else:
            # Use TRS (translation/rotation/scale) decomposition
            existing_scale = node.get('scale', [1.0, 1.0, 1.0])
            node['scale'] = [
                existing_scale[0] * scale_factor,
                existing_scale[1] * scale_factor,
                existing_scale[2] * scale_factor
            ]
            # Also scale the translation if present
            if 'translation' in node:
                t = node['translation']
                node['translation'] = [
                    t[0] * scale_factor,
                    t[1] * scale_factor,
                    t[2] * scale_factor
                ]

    write_glb(output_path, json_data, bin_data)


# ============================================================
# 3. Main scaling logic
# ============================================================

def compute_scale_factor(glb_size_m, real_dims_cm):
    """
    Compute uniform scale factor.

    Strategy: match dimensions by sorted order (largest-to-largest),
    then use the geometric mean of the 3 ratios for uniform scale.
    """
    # GLB size in cm
    glb_cm = np.array(glb_size_m) * 100.0
    real = np.array(real_dims_cm)  # (H, B, D) in cm

    # Sort both by size (largest first)
    glb_sorted = np.sort(glb_cm)[::-1]
    real_sorted = np.sort(real)[::-1]

    # Ratios: how much to scale each matched axis
    ratios = real_sorted / glb_sorted

    # Use geometric mean for uniform scale
    # (preserves proportions, minimises distortion)
    geo_mean = np.exp(np.mean(np.log(ratios)))

    return geo_mean


def main():
    yaml_path = 'nasjonalmuseet_stoler_128.yaml'
    noreg_dir = '.'

    print("=" * 65)
    print("  Skalering av GLB-modellar til faktiske dimensjonar")
    print("=" * 65)
    print()

    # Load YAML dimensions
    dims = load_yaml_dimensions(yaml_path)
    print(f"  Lasta dimensjonar for {len(dims)} stolar frå YAML")

    # Find all GLB files
    glb_files = sorted(glob.glob('./*/*.glb'))
    # Also check root (un-organized files)
    glb_files += sorted(glob.glob('./*.glb'))
    print(f"  Fann {len(glb_files)} GLB-filer")
    print()

    scaled = 0
    skipped = 0
    errors = []

    for glb_path in glb_files:
        filename = os.path.basename(glb_path)
        # Extract objectId: everything before the first underscore
        objid = filename.rsplit('_', 1)[0]

        # Skip if already a backup file
        if '_original.glb' in filename:
            continue

        # Find dimensions
        if objid not in dims:
            print(f"  HOPP OVER  {objid} — ingen dimensjonar i YAML")
            skipped += 1
            continue

        real_h, real_b, real_d = dims[objid]

        # Check if already scaled (backup exists)
        backup_path = glb_path.replace('.glb', '_original.glb')
        if os.path.exists(backup_path):
            print(f"  ALLEREIE   {objid} — backup finst, hoppar over")
            skipped += 1
            continue

        try:
            # Get current bounding box
            glb_size = get_glb_bounds_trimesh(glb_path)
            glb_cm = glb_size * 100

            # Compute scale factor
            sf = compute_scale_factor(glb_size, (real_h, real_b, real_d))

            # Report
            new_cm = glb_cm * sf
            print(f"  SKALERER   {objid}")
            print(f"             No:    {glb_cm[0]:.1f} x {glb_cm[1]:.1f} x {glb_cm[2]:.1f} cm")
            print(f"             Mål:   H {real_h} x B {real_b} x D {real_d} cm")
            print(f"             Etter: {new_cm[0]:.1f} x {new_cm[1]:.1f} x {new_cm[2]:.1f} cm")
            print(f"             Faktor: {sf:.4f}")

            # Backup original
            shutil.copy2(glb_path, backup_path)

            # Apply scale
            apply_uniform_scale_to_glb(glb_path, sf, glb_path)
            print()

            scaled += 1

        except Exception as e:
            print(f"  FEIL       {objid} — {e}")
            errors.append((objid, str(e)))
            # Restore backup if it was created
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, glb_path)
                os.remove(backup_path)

    print()
    print("=" * 65)
    print(f"  Ferdig! Skalerte {scaled} modellar, hoppa over {skipped}")
    if errors:
        print(f"  Feil: {len(errors)}")
        for objid, err in errors:
            print(f"    {objid}: {err}")
    print("=" * 65)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
