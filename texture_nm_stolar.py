"""
texture_nm_stolar.py — Apply Hunyuan3D-2 paint pipeline to existing NM_stolar GLBs

For each NM_stolar/{objectId}/*.glb:
  1. Load the untextured GLB (trimesh)
  2. Find the corresponding source JPG
  3. Run Hunyuan3DPaintPipeline(mesh, image) → textured mesh
  4. Export textured GLB (overwrite original, backup saved as *_notex.glb)

Resumable: skips GLBs that already have texture data.
GPU: ~15-18 GB VRAM (turbo mode by default).

Run:
  "Hunyuan3D-2/venv/Scripts/python.exe" texture_nm_stolar.py
"""

import os
import shutil
import sys
import time
from pathlib import Path

import trimesh
from PIL import Image

# ── Paths ────────────────────────────────────────────────────────────────────
BASE   = Path(__file__).parent
NM_DIR = BASE / "NM_stolar"

# ── Settings ─────────────────────────────────────────────────────────────────
CPU_OFFLOAD = False   # True = slower but uses less VRAM (~10 GB vs ~18 GB)
SUBFOLDER   = "hunyuan3d-paint-v2-0-turbo"  # turbo = faster (LCM-based)


def has_texture(glb_path):
    """Check if a GLB already has texture data."""
    try:
        scene = trimesh.load(str(glb_path), process=False)
        geoms = scene.geometry.values() if hasattr(scene, 'geometry') else [scene]
        for m in geoms:
            vis = getattr(m, 'visual', None)
            if vis is None:
                continue
            mat = getattr(vis, 'material', None)
            if mat is None:
                continue
            # PBR or SimpleMaterial with an image → has texture
            img = getattr(mat, 'image', None)
            if img is not None:
                return True
            # Also check baseColorTexture for PBR
            bct = getattr(mat, 'baseColorTexture', None)
            if bct is not None:
                return True
        return False
    except Exception:
        return False


def find_source_jpg(obj_dir, stem):
    """Find the source JPG for a GLB. Checks subdir first, then NM_stolar root."""
    # The JPG should be in the same subdir with the same stem
    jpg_in_dir = obj_dir / f"{stem}.jpg"
    if jpg_in_dir.exists():
        return jpg_in_dir
    # Try NM_stolar root (images are also stored there)
    jpg_root = NM_DIR / f"{stem}.jpg"
    if jpg_root.exists():
        return jpg_root
    # Fallback: any JPG in the subdir
    jpgs = list(obj_dir.glob("*.jpg"))
    if jpgs:
        return jpgs[0]
    return None


def main():
    print("=" * 64)
    print("  NM_stolar texture generation (Hunyuan3D-2 Paint Pipeline)")
    print(f"  subfolder: {SUBFOLDER}  cpu_offload: {CPU_OFFLOAD}")
    print("=" * 64)

    # ── Collect work items ────────────────────────────────────────────────────
    items = []
    already_textured = 0
    no_jpg = 0

    for obj_dir in sorted(NM_DIR.iterdir()):
        if not obj_dir.is_dir():
            continue
        for glb in sorted(obj_dir.glob("*.glb")):
            if "_notex" in glb.stem:
                continue  # skip backups
            stem = glb.stem
            if has_texture(glb):
                already_textured += 1
                continue
            jpg = find_source_jpg(obj_dir, stem)
            if jpg is None:
                no_jpg += 1
                print(f"  [SKIP] {glb.name}: no source JPG found")
                continue
            items.append((glb, jpg, obj_dir))

    print(f"\n  To texture:       {len(items)}")
    print(f"  Already textured: {already_textured}")
    print(f"  No source JPG:    {no_jpg}")

    if not items:
        print("\n  Nothing to do.")
        return

    # ── Load pipeline ─────────────────────────────────────────────────────────
    print("\n  Loading Hunyuan3D-2 paint pipeline...")
    t0 = time.time()

    sys.path.insert(0, str(BASE / "Hunyuan3D-2"))
    from hy3dgen.texgen import Hunyuan3DPaintPipeline

    paint_pipe = Hunyuan3DPaintPipeline.from_pretrained(
        "tencent/Hunyuan3D-2", subfolder=SUBFOLDER
    )
    if CPU_OFFLOAD:
        paint_pipe.enable_model_cpu_offload()

    print(f"  Pipeline ready ({time.time() - t0:.0f}s)\n")

    # ── Process ───────────────────────────────────────────────────────────────
    done = 0
    failed = 0
    t_start = time.time()

    for i, (glb_path, jpg_path, obj_dir) in enumerate(items, 1):
        objid = obj_dir.name
        pct = 100 * (i - 1) / len(items)
        elapsed = time.time() - t_start
        eta = ""
        if done > 0:
            avg = elapsed / done
            remaining = avg * (len(items) - i + 1)
            mins = remaining / 60
            eta = f"  ETA {mins:.0f}min"

        print(f"  [{i}/{len(items)}] {pct:.0f}%{eta}  {objid} / {glb_path.name}")

        t_item = time.time()
        try:
            # Load untextured mesh
            mesh = trimesh.load(str(glb_path), process=False)

            # Backup original
            backup = glb_path.with_name(glb_path.stem + "_notex.glb")
            if not backup.exists():
                shutil.copy2(glb_path, backup)

            # Load source image
            image = Image.open(jpg_path)

            # Run texture pipeline
            textured_mesh = paint_pipe(mesh, image)

            # Export (overwrite original)
            textured_mesh.export(str(glb_path))

            item_time = time.time() - t_item
            done += 1
            print(f"    done ({item_time:.0f}s)")

        except Exception as e:
            item_time = time.time() - t_item
            failed += 1
            print(f"    FAILED ({item_time:.0f}s): {e}")

    # ── Summary ───────────────────────────────────────────────────────────────
    total_time = time.time() - t_start
    print(f"\n{'=' * 64}")
    print(f"  DONE")
    print(f"  Textured: {done}")
    print(f"  Failed:   {failed}")
    print(f"  Skipped:  {already_textured} (already textured) + {no_jpg} (no JPG)")
    print(f"  Total time: {total_time / 60:.1f} min")
    print(f"{'=' * 64}")


if __name__ == "__main__":
    os.chdir(BASE)
    main()
