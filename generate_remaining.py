#!/usr/bin/env python3
"""
generate_remaining.py — Generate 3D GLB models for all NM_stolar entries
that have a source image but no GLB yet. Uses Hunyuan3D-2 (hy3dgen).

After generation, scales each model to match the real-world height from metadata.
"""

import gc
import json
import os
import re
import shutil
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image

BASE = Path(__file__).parent
NM_DIR = BASE / "NM_stolar"
META_JSON = NM_DIR / "NM_stolar.json"

INFERENCE_STEPS = 30
OCTREE_RESOLUTION = 256


def parse_height_cm(maal_str):
    if not maal_str:
        return None
    s = str(maal_str)
    m = re.search(r'\bH\s*([\d]+[,.]?\d*)', s)
    if m:
        return float(m.group(1).replace(',', '.'))
    m = re.search(r'([\d]+[,.]?\d*)\s*x', s)
    if m:
        return float(m.group(1).replace(',', '.'))
    return None


def scale_to_height(scene, target_h_m):
    """Uniform scale so bounding box height = target_h_m, centered at origin."""
    import trimesh
    bounds = scene.bounds
    if bounds is None:
        return scene
    current_h = bounds[1][1] - bounds[0][1]
    if current_h <= 0:
        return scene
    sf = target_h_m / current_h
    cx = (bounds[0][0] + bounds[1][0]) / 2.0
    cz = (bounds[0][2] + bounds[1][2]) / 2.0
    T = np.eye(4)
    T[0, 3] = -cx
    T[1, 3] = -bounds[0][1]
    T[2, 3] = -cz
    S = np.eye(4)
    S[0, 0] = S[1, 1] = S[2, 2] = sf
    scene.apply_transform(S @ T)
    return scene


def find_missing():
    """Return list of (objectId, image_path, height_cm) for entries needing generation."""
    data = json.loads(META_JSON.read_text(encoding="utf-8"))

    img_files = {}
    for f in NM_DIR.iterdir():
        if f.suffix.lower() in (".png", ".jpg", ".jpeg"):
            img_files[f.stem] = f

    missing = []
    for entry in data:
        oid = entry.get("objectId", "")
        obj_dir = NM_DIR / oid

        # Skip if GLB already exists
        if obj_dir.is_dir():
            if any(f.endswith(".glb") and "_prescale" not in f
                   for f in os.listdir(obj_dir)):
                continue

        # Find source image
        img_path = None
        for img in entry.get("images", []):
            fn = img.get("filename", "")
            if fn:
                stem = os.path.splitext(fn)[0]
                if stem in img_files:
                    img_path = img_files[stem]
                    break

        if not img_path:
            continue

        height_cm = parse_height_cm(entry.get("Maal") or entry.get("M\u00e5l", ""))
        missing.append((oid, img_path, height_cm))

    return missing, data


def main():
    missing, nm_data = find_missing()
    print(f"Need to generate: {len(missing)} models")
    if not missing:
        print("Nothing to do.")
        return

    for i, (oid, img, h) in enumerate(missing):
        h_str = f"H={h:.1f}cm" if h else "no height"
        print(f"  {i+1}. {oid} ({h_str}) <- {img.name}")

    print(f"\nLoading Hunyuan3D-2 pipeline...")
    t0 = time.time()

    from hy3dgen.rembg import BackgroundRemover
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

    rembg = BackgroundRemover()
    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2")
    print(f"Pipeline ready ({time.time()-t0:.0f}s)\n")

    import trimesh

    done = failed = 0
    total = len(missing)

    for i, (oid, img_path, height_cm) in enumerate(missing, 1):
        stem = img_path.stem
        obj_dir = NM_DIR / oid
        glb_path = obj_dir / f"{stem}.glb"

        print(f"[{i}/{total}] {oid}", flush=True)
        t_item = time.time()

        try:
            obj_dir.mkdir(parents=True, exist_ok=True)

            # Copy source image into object dir
            dst_img = obj_dir / img_path.name
            if not dst_img.exists():
                shutil.copy2(img_path, dst_img)

            # Background removal
            print(f"  removing background...", flush=True)
            rgba = rembg(Image.open(str(img_path)).convert("RGB"))

            # Generate mesh
            print(f"  generating 3D mesh (steps={INFERENCE_STEPS}, octree={OCTREE_RESOLUTION})...", flush=True)
            mesh = pipeline(
                image=rgba,
                num_inference_steps=INFERENCE_STEPS,
                octree_resolution=OCTREE_RESOLUTION,
            )
            if isinstance(mesh, (list, tuple)):
                mesh = mesh[0]

            # Convert to trimesh scene for scaling
            if isinstance(mesh, trimesh.Trimesh):
                scene = trimesh.Scene()
                scene.add_geometry(mesh)
            elif isinstance(mesh, trimesh.Scene):
                scene = mesh
            else:
                # mesh might be a custom type — try export/reimport
                raw_path = obj_dir / f"{stem}_raw.glb"
                mesh.export(str(raw_path))
                scene = trimesh.load(str(raw_path))
                raw_path.unlink()

            # Scale to real height
            if height_cm:
                scene = scale_to_height(scene, height_cm / 100.0)
                note = f"scaled H={height_cm:.1f}cm"
            else:
                note = "unscaled (no height data)"

            scene.export(str(glb_path))

            # Update metadata
            for entry in nm_data:
                if entry.get("objectId") == oid:
                    entry["model3d"] = glb_path.name
                    for img in entry.get("images", []):
                        if img.get("filename", "").startswith(oid) or \
                           os.path.splitext(img.get("filename", ""))[0] == stem:
                            img["glb"] = glb_path.name
                    break

            # Write per-object JSON
            obj_json = obj_dir / f"{oid}.json"
            if not obj_json.exists():
                for entry in nm_data:
                    if entry.get("objectId") == oid:
                        obj_json.write_text(
                            json.dumps(entry, ensure_ascii=False, indent=2),
                            encoding="utf-8"
                        )
                        break

            elapsed = time.time() - t_item
            print(f"  OK: {glb_path.name} [{note}] ({elapsed:.0f}s)", flush=True)
            done += 1

        except Exception as e:
            elapsed = time.time() - t_item
            print(f"  FAILED: {e} ({elapsed:.0f}s)", flush=True)
            import traceback
            traceback.print_exc()
            failed += 1
            # Clean up partial output
            if glb_path.exists():
                glb_path.unlink()

        # Free GPU memory
        torch.cuda.empty_cache()
        gc.collect()
        print()

    # Save updated master JSON
    META_JSON.write_text(
        json.dumps(nm_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    total_time = time.time() - t0
    print(f"{'='*60}")
    print(f"Done: {done} generated, {failed} failed")
    print(f"Total time: {total_time/60:.1f} min")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
