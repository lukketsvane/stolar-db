"""
batch_generate_nm_stolar.py
============================
For each image in NM_stolar/:
  1. If a GLB already exists in noreg/{objectId}/ → COPY it (no generation needed)
  2. Otherwise → generate with Hunyuan3D-2 (batched, GPU-optimised)
  3. Scale to real-world height from NM_stolar.json / norske_stolar.csv
  4. Write NM_stolar/{objectId}/ folder structure (mirroring noreg)

GPU settings (tuned for RTX A4500 19 GB VRAM):
  batch_size = 2       → 2 images generated per pipeline call (~12 GB VRAM)
  num_inference_steps  = 30  → flow-matching CFM needs fewer steps, good quality
  octree_resolution    = 256 → 3-4x faster volume decoding vs 384

Resumable: skips entries whose output .glb already exists.

Run:
  "Hunyuan3D-2/venv/Scripts/python.exe" batch_generate_nm_stolar.py
"""

import csv
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

# ── Paths ────────────────────────────────────────────────────────────────────
BASE     = Path(__file__).parent
NM_DIR   = BASE / "NM_stolar"
NOREG    = BASE / "noreg"
META_JSON = NM_DIR / "NM_stolar.json"
CSV_PATH  = BASE / "norske_stolar.csv"

# ── GPU / generation settings ─────────────────────────────────────────────
BATCH_SIZE        = 2    # images per pipeline call
INFERENCE_STEPS   = 30   # diffusion steps (30 ≈ 95% quality of 50)
OCTREE_RESOLUTION = 256  # voxel resolution (256 = 3-4x faster than 384)

# ── Texture settings ──────────────────────────────────────────────────────
ENABLE_TEXTURE      = False  # Run Hunyuan3DPaintPipeline after shape gen
TEXTURE_CPU_OFFLOAD = False  # True = slower but uses less VRAM

# ── Height helpers ────────────────────────────────────────────────────────────

def _f(v):
    try:
        return float(str(v).replace(",", ".").strip()) if v else None
    except Exception:
        return None


def _h_from_maal(s):
    m = re.search(r'\bH\s*([\d]+[,.]?\d*)', str(s or ""))
    return _f(m.group(1)) if m else None


def build_height_map():
    heights = {}
    # CSV
    if CSV_PATH.exists():
        with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f, delimiter=";"):
                oid = row.get("object_id", "").strip()
                h = _f(row.get("hoegde_cm"))
                if oid and h and oid not in heights:
                    heights[oid] = h
    # All JSON files in project (skip heavy dirs)
    SKIP = {"node_modules", "Hunyuan3D-2", "venv", ".git", ".claude"}
    for dp, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for fn in files:
            if not fn.endswith(".json"):
                continue
            try:
                data = json.loads(Path(dp, fn).read_text(encoding="utf-8"))
            except Exception:
                continue
            for item in (data if isinstance(data, list) else [data]):
                if not isinstance(item, dict):
                    continue
                p = item.get("properties", item)
                oid = (p.get("Objekt-ID") or p.get("objectId") or
                       p.get("object_id") or item.get("objectId") or
                       item.get("object_id"))
                if not oid:
                    continue
                oid = str(oid).strip()
                h = (_f(p.get("Høgde (cm)") or p.get("Høyde (cm)") or
                        p.get("hoegde_cm") or item.get("Høgde (cm)") or
                        item.get("hoegde_cm"))
                    or _h_from_maal(p.get("Mål") or item.get("Mål")))
                if h and oid not in heights:
                    heights[oid] = h
    return heights


# ── Scaling ───────────────────────────────────────────────────────────────────

def scale_to_height(scene, target_h_m):
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
    T = np.eye(4); T[0,3] = -cx; T[1,3] = -bounds[0][1]; T[2,3] = -cz
    S = np.eye(4); S[0,0] = S[1,1] = S[2,2] = sf
    scene.apply_transform(S @ T)
    return scene


def export_and_scale(scene, glb_path, height_cm):
    import trimesh
    if height_cm:
        scene = scale_to_height(scene, height_cm / 100.0)
    scene.export(str(glb_path))


# ── Per-item finalise ─────────────────────────────────────────────────────────

def finalise(jpg_path, object_id, stem, out_dir, glb_path, mesh, height_cm,
             obj_meta, nm_data):
    import trimesh

    out_dir.mkdir(parents=True, exist_ok=True)

    # Copy source JPG
    dst_jpg = out_dir / jpg_path.name
    if not dst_jpg.exists():
        shutil.copy2(jpg_path, dst_jpg)

    # Export (possibly scaled) GLB
    if isinstance(mesh, trimesh.Trimesh):
        scene = trimesh.Scene()
        scene.add_geometry(mesh)
    else:
        scene = mesh
    export_and_scale(scene, glb_path, height_cm)

    # Write per-object JSON
    obj_json = out_dir / f"{object_id}.json"
    if obj_meta:
        entry = dict(obj_meta)
        for img in entry.get("images") or []:
            if img.get("filename") == jpg_path.name:
                img["glb"] = glb_path.name
        entry["model3d"] = glb_path.name
        with open(obj_json, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)

    # Update master NM_stolar.json
    if obj_meta is not None:
        for img in obj_meta.get("images") or []:
            if img.get("filename") == jpg_path.name:
                img["glb"] = glb_path.name
        obj_meta["model3d"] = glb_path.name
    if nm_data is not None:
        with open(META_JSON, "w", encoding="utf-8") as f:
            json.dump(nm_data, f, ensure_ascii=False, indent=2)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 64)
    print("  NM_stolar batch -> noreg structure")
    print(f"  batch_size={BATCH_SIZE}  steps={INFERENCE_STEPS}  "
          f"octree={OCTREE_RESOLUTION}")
    print("=" * 64)

    # Load metadata & height map
    print("Loading metadata & height map...")
    nm_data = json.loads(META_JSON.read_text(encoding="utf-8")) if META_JSON.exists() else []
    fname_to_obj = {}
    for obj in nm_data:
        for img in obj.get("images") or []:
            fn = img.get("filename", "")
            if fn:
                fname_to_obj[fn] = obj

    heights = build_height_map()
    print(f"  Heights loaded: {len(heights)} objects")

    # Inventory all images
    all_jpgs = sorted(list(NM_DIR.glob("*.png")) + list(NM_DIR.glob("*.jpg")))
    print(f"  Images in NM_stolar/: {len(all_jpgs)}")

    # ── Phase 1: Copy from noreg where GLBs already exist ────────────────────
    print("\n[Phase 1] Copying existing GLBs from noreg/ ...")
    copied = skipped = 0
    to_generate = []

    for jpg in all_jpgs:
        stem     = jpg.stem
        objid    = stem.rsplit("_", 1)[0]
        out_dir  = NM_DIR / objid
        out_glb  = out_dir / f"{stem}.glb"

        # Already done in NM_stolar
        if out_glb.exists():
            skipped += 1
            continue

        # Source GLB in noreg?
        noreg_glb = NOREG / objid / f"{stem}.glb"
        if noreg_glb.exists():
            out_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(noreg_glb, out_glb)
            # Copy image too if missing
            dst_jpg = out_dir / jpg.name
            if not dst_jpg.exists():
                shutil.copy2(jpg, dst_jpg)
            # Write per-object JSON
            obj_json = out_dir / f"{objid}.json"
            noreg_json = NOREG / objid / f"{objid}.json"
            if not obj_json.exists() and noreg_json.exists():
                shutil.copy2(noreg_json, obj_json)
            copied += 1
            continue

        to_generate.append(jpg)

    print(f"  Copied:   {copied}")
    print(f"  Skipped (already done): {skipped}")
    print(f"  Need generation: {len(to_generate)}")

    if not to_generate:
        print("\nAll done — nothing to generate.")
        return

    # ── Phase 2: Generate remaining with batched Hunyuan3D-2 ─────────────────
    print(f"\n[Phase 2] Generating {len(to_generate)} new models "
          f"(batch={BATCH_SIZE}, steps={INFERENCE_STEPS}, "
          f"octree={OCTREE_RESOLUTION}) ...")

    sys.path.insert(0, str(BASE / "Hunyuan3D-2"))
    from hy3dgen.rembg import BackgroundRemover
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

    print("  Loading shape pipeline (weights cached)...")
    rembg    = BackgroundRemover()
    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2")

    paint_pipe = None
    if ENABLE_TEXTURE:
        from hy3dgen.texgen import Hunyuan3DPaintPipeline
        print("  Loading paint pipeline...")
        paint_pipe = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
        if TEXTURE_CPU_OFFLOAD:
            paint_pipe.enable_model_cpu_offload()
    print("  Pipelines ready.\n")

    done = failed = 0
    total = len(to_generate)
    t_start = time.time()
    batch_times = []

    def eta_str(batches_done, batches_left):
        if not batch_times:
            return "?"
        avg = sum(batch_times) / len(batch_times)
        secs = avg * batches_left
        if secs < 60:
            return f"{secs:.0f}s"
        h, m = divmod(int(secs) // 60, 60)
        return f"{h}h{m:02d}m" if h else f"{m}m"

    num_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

    # Process in batches of BATCH_SIZE
    for b_start in range(0, total, BATCH_SIZE):
        batch = to_generate[b_start : b_start + BATCH_SIZE]
        b_num = b_start // BATCH_SIZE + 1
        items_done = b_start
        pct = 100 * items_done / total

        # Pre-process all images in batch (CPU, overlaps with prev GPU work)
        batch_info = []
        images_rgba = []
        for jpg in batch:
            stem  = jpg.stem
            objid = stem.rsplit("_", 1)[0]
            out_dir = NM_DIR / objid
            out_glb = out_dir / f"{stem}.glb"
            height_cm = heights.get(objid)
            obj_meta  = fname_to_obj.get(jpg.name)
            out_dir.mkdir(parents=True, exist_ok=True)
            rgba = rembg(Image.open(jpg).convert("RGB"))
            images_rgba.append(rgba)
            batch_info.append((jpg, objid, stem, out_dir, out_glb,
                               height_cm, obj_meta))

        ids = " + ".join(info[1] for info in batch_info)
        elapsed_total = time.time() - t_start
        print(f"\n{'─'*64}", flush=True)
        print(f"  Batch {b_num}/{num_batches}  │  items {b_start+1}–{b_start+len(batch)}/{total}"
              f"  │  {pct:.0f}% done  │  ETA {eta_str(b_num-1, num_batches-b_num+1)}"
              f"  │  running {elapsed_total/60:.1f}min", flush=True)
        print(f"  ▶ {ids}", flush=True)

        t0 = time.time()
        try:
            # Single pipeline call for entire batch
            input_img = images_rgba[0] if len(images_rgba) == 1 else images_rgba
            meshes = pipeline(
                image=input_img,
                num_inference_steps=INFERENCE_STEPS,
                octree_resolution=OCTREE_RESOLUTION,
            )

            # Unpack results (pipeline returns list of meshes)
            if not isinstance(meshes, (list, tuple)):
                meshes = [meshes]

            elapsed = time.time() - t0
            batch_times.append(elapsed)
            rate = elapsed / len(batch)

            for mesh, info in zip(meshes, batch_info):
                jpg, objid, stem, out_dir, out_glb, height_cm, obj_meta = info
                try:
                    if paint_pipe is not None:
                        print(f"  ⬡ texturing {objid}...", flush=True)
                        mesh = paint_pipe(mesh, Image.open(jpg))
                    note = f"H={height_cm:.1f}cm" if height_cm else "unscaled"
                    tex_note = "  [textured]" if paint_pipe else ""
                    finalise(jpg, objid, stem, out_dir, out_glb, mesh,
                             height_cm, obj_meta, nm_data)
                    print(f"  ✓ {out_glb.name}  [{note}]{tex_note}", flush=True)
                    done += 1
                except Exception as e:
                    print(f"  ✗ {objid}: {e}", flush=True)
                    failed += 1

            print(f"  ↳ {elapsed:.0f}s this batch  ({rate:.0f}s/item)  "
                  f"│  {done} done  {failed} failed", flush=True)

        except Exception as e:
            elapsed = time.time() - t0
            print(f"  ✗ BATCH FAILED ({elapsed:.0f}s): {e}", flush=True)
            import traceback; traceback.print_exc()
            # Fall back to single-item generation
            for info in batch_info:
                jpg, objid, stem, out_dir, out_glb, height_cm, obj_meta = info
                if out_glb.exists():
                    continue
                try:
                    rgba = rembg(Image.open(jpg).convert("RGB"))
                    [mesh] = pipeline(
                        image=rgba,
                        num_inference_steps=INFERENCE_STEPS,
                        octree_resolution=OCTREE_RESOLUTION,
                    )
                    if paint_pipe is not None:
                        print(f"  ⬡ texturing {objid}...", flush=True)
                        mesh = paint_pipe(mesh, Image.open(jpg))
                    note = f"H={height_cm:.1f}cm" if height_cm else "unscaled"
                    tex_note = "  [textured]" if paint_pipe else ""
                    finalise(jpg, objid, stem, out_dir, out_glb, mesh,
                             height_cm, obj_meta, nm_data)
                    print(f"  ✓ {objid} (fallback)  [{note}]{tex_note}", flush=True)
                    done += 1
                except Exception as e2:
                    print(f"  ✗ {objid} (fallback): {e2}", flush=True)
                    failed += 1

    total_time = time.time() - t_start
    print(f"\n{'='*64}")
    print(f"  DONE")
    print(f"  Copied:    {copied}")
    print(f"  Generated: {done}")
    print(f"  Failed:    {failed}")
    print(f"  Total time: {total_time/60:.1f} min")
    print(f"{'='*64}", flush=True)


if __name__ == "__main__":
    main()
