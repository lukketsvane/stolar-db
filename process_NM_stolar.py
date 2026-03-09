"""
process_NM_stolar.py — Batch generate 3D GLB models for all images in NM_stolar/
that don't yet have a corresponding GLB in noreg/{objectId}/.

Usage:
    "Hunyuan3D-2/venv/Scripts/python.exe" process_NM_stolar.py

Run from:  C:\\Users\\Shadow\\Desktop\\stolar-db\\
"""

import os
import sys
import json
import shutil
import time
from pathlib import Path

import numpy as np

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
NM_STOLAR   = BASE_DIR / 'NM_stolar'
NOREG       = BASE_DIR / 'noreg'
MASTER_JSON     = NOREG / 'nasjonalmuseet_stoler_128.json'
NM_STOLAR_JSON  = NM_STOLAR / 'NM_stolar.json'

# ── Import scaling helpers from existing scale_models.py ────────────────────
sys.path.insert(0, str(NOREG))
from scale_models import (
    parse_dimensions_cm,
    get_glb_bounds_trimesh,
    compute_scale_factor,
    apply_uniform_scale_to_glb,
)

# ── Metadata helpers ──────────────────────────────────────────────────────────

def load_metadata():
    """Return dict: objectId -> item dict, merging both JSON sources."""
    result = {}
    for path in (MASTER_JSON, NM_STOLAR_JSON):
        if path.exists():
            with open(path, encoding='utf-8') as f:
                for item in json.load(f):
                    objid = item.get('objectId', '')
                    if objid and objid not in result:
                        result[objid] = item
    return result


def extract_object_id(filename: str) -> str:
    """
    OK-02256_35727.jpg          → OK-02256
    OK-06659_OK-06659.jpg       → OK-06659
    OK-1984-0149_OK-1984-0149+20250325.jpg → OK-1984-0149
    """
    stem = Path(filename).stem
    return stem.rsplit('_', 1)[0]


def update_entry_json(json_path: Path, stem: str, glb_name: str):
    """Write / update the per-entry JSON file with model3d reference."""
    if json_path.exists():
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}

    data['model3d'] = glb_name

    # Update matching image entry if present
    for img in data.get('images', []):
        if Path(img.get('filename', '')).stem == stem:
            img['glb'] = glb_name

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 3D generation helpers ─────────────────────────────────────────────────────

def remove_background(jpg_path: Path):
    """Return RGBA PIL Image with background removed."""
    from PIL import Image as PILImage
    from hy3dgen.rembg import BackgroundRemover
    rembg = BackgroundRemover()
    img = PILImage.open(jpg_path).convert('RGB')
    return rembg(img)


def generate_mesh(pipeline, image_rgba):
    """Run Hunyuan3D-2 shape generation. Returns a trimesh object."""
    return pipeline(image=image_rgba)[0]


def scale_glb(raw_glb: Path, out_glb: Path, dims_cm):
    """Scale raw GLB to real-world dimensions and write to out_glb."""
    size = get_glb_bounds_trimesh(str(raw_glb))
    sf   = compute_scale_factor(size, dims_cm)
    apply_uniform_scale_to_glb(str(raw_glb), sf, str(out_glb))
    return sf


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print('=' * 68)
    print('  Hunyuan3D-2 batch generation  ·  NM_stolar → noreg')
    print('=' * 68)

    metadata = load_metadata()
    print(f'  Loaded metadata for {len(metadata)} entries')

    images = sorted(NM_STOLAR.glob('*.jpg'))
    print(f'  Found {len(images)} images in NM_stolar/')
    print()

    # ── Check which images need processing ──────────────────────────────────
    to_process = []
    for jpg in images:
        objid   = extract_object_id(jpg.name)
        stem    = jpg.stem
        out_dir = NOREG / objid
        out_glb = out_dir / f'{stem}.glb'
        if out_glb.exists():
            continue
        to_process.append((jpg, objid, stem, out_dir, out_glb))

    if not to_process:
        print('  Nothing to process — all entries already have GLBs.')
        print('  (To regenerate, delete the existing .glb files first.)')
        return

    print(f'  {len(to_process)} images to process'
          f' ({len(images) - len(to_process)} already done, skipped)')
    print()

    # ── Load pipeline once ───────────────────────────────────────────────────
    print('  Loading Hunyuan3D-2 pipeline (first run downloads ~5 GB)...')
    t0 = time.time()
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained('tencent/Hunyuan3D-2')
    print(f'  Pipeline ready  ({time.time()-t0:.0f}s)')
    print()

    # ── Process loop ─────────────────────────────────────────────────────────
    n_done = 0
    n_err  = 0
    errors = []

    for i, (jpg, objid, stem, out_dir, out_glb) in enumerate(to_process, 1):
        tag = f'[{i}/{len(to_process)}]'
        print(f'{tag}  {objid}')
        t_item = time.time()

        raw_glb = out_dir / f'{stem}_raw.glb'

        try:
            out_dir.mkdir(parents=True, exist_ok=True)

            # Copy source JPG
            dest_jpg = out_dir / jpg.name
            if not dest_jpg.exists():
                shutil.copy2(jpg, dest_jpg)

            # Background removal
            print(f'        removing background...')
            image_rgba = remove_background(jpg)

            # Shape generation
            print(f'        generating 3D mesh...')
            mesh = generate_mesh(pipeline, image_rgba)
            mesh.export(str(raw_glb))

            # Scaling
            dims = None
            if objid in metadata:
                mal = metadata[objid].get('Mål', '')
                dims = parse_dimensions_cm(mal)

            if dims:
                h, b, d = dims
                sf = scale_glb(raw_glb, out_glb, dims)
                raw_glb.unlink()
                print(f'        scaled  H={h} B={b} D={d} cm  (factor {sf:.4f})')
            else:
                raw_glb.rename(out_glb)
                print(f'        WARN: no dimensions found, saved unscaled')

            # Update entry JSON
            json_path = out_dir / f'{objid}.json'
            if not json_path.exists() and objid in metadata:
                # Bootstrap from master JSON
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata[objid], f, ensure_ascii=False, indent=2)
            update_entry_json(json_path, stem, out_glb.name)

            elapsed = time.time() - t_item
            print(f'        ✓  {out_glb.name}  ({elapsed:.0f}s)')
            n_done += 1

        except Exception as e:
            print(f'        ✗  ERROR: {e}')
            errors.append((objid, str(e)))
            n_err += 1
            # Clean up partial outputs
            for p in (raw_glb, out_glb):
                if p.exists():
                    try: p.unlink()
                    except: pass

        print()

    # ── Summary ──────────────────────────────────────────────────────────────
    print('=' * 68)
    print(f'  Done.  Processed: {n_done}   Errors: {n_err}   Skipped: {len(images)-len(to_process)}')
    if errors:
        print()
        print('  Failed entries:')
        for objid, err in errors:
            print(f'    {objid}: {err}')
    print('=' * 68)


if __name__ == '__main__':
    # Ensure cwd is the project root so scale_models.py relative paths work
    os.chdir(BASE_DIR)
    main()
