#!/usr/bin/env python3
"""
generate_pbr.py — Generate 3D meshes with PBR textures on GPU,
scale them, push to GitHub, and update Notion — all simultaneously.

Optimized for Quadro RTX 6000 (24GB VRAM) + Xeon W-3235 (12 threads).

Strategy: load shape pipeline on GPU, generate mesh, offload shape to CPU,
load paint pipeline on GPU, texture mesh, offload paint to CPU. This keeps
max VRAM for whichever pipeline is active.
"""

import gc
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from queue import Queue

import numpy as np
import requests
from PIL import Image

# ── DLL paths for custom_rasterizer (must be before torch imports) ──
os.add_dll_directory(os.path.join(sys.prefix, "Lib", "site-packages", "torch", "lib"))
cuda_bin = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin"
if os.path.isdir(cuda_bin):
    os.add_dll_directory(cuda_bin)

# ── Config ──
BASE = Path(__file__).parent
SRC_DIR = BASE / "VA_bguw"
OUT_DIR = BASE / "VA_3d"
LOG_FILE = BASE / "generate_pbr.log"
BATCH_SIZE = 10  # push + update Notion every N new meshes

# ── Notion ──
NOTION_TOKEN = ""
env_file = BASE / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("NOTION_API_KEY="):
            NOTION_TOKEN = line.split("=", 1)[1].strip().strip('"')

DATABASE_ID = "405e0f64-6b77-4aab-88b8-73281e58c4f0"
GITHUB_RAW = "https://raw.githubusercontent.com/lukketsvane/stolar-db/main/VA_3d"
NOTION_HDR = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


# ── Height helpers ──
def _try_float(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None


def _h_from_maal(maal_str):
    m = re.search(r'\bH[^\d]*(\d+[,.]?\d*)', str(maal_str or ""))
    return _try_float(m.group(1)) if m else None


def build_height_map():
    heights = {}
    hf = BASE / "va_heights.json"
    if hf.exists():
        data = json.loads(hf.read_text(encoding="utf-8"))
        for oid, h in data.items():
            h_val = _try_float(h)
            if h_val and h_val > 0:
                heights[oid] = h_val
    hp = BASE / "va_heights_partial.json"
    if hp.exists():
        data = json.loads(hp.read_text(encoding="utf-8"))
        for oid, val in data.items():
            h = val[0] if isinstance(val, list) else val
            h_val = _try_float(h)
            if h_val and h_val > 0:
                heights.setdefault(oid, h_val)
    for jf in (BASE / "noreg").rglob("*.json") if (BASE / "noreg").exists() else []:
        try:
            jdata = json.loads(jf.read_text(encoding="utf-8"))
            oid = jdata.get("objectId", "")
            h = _h_from_maal(jdata.get("Mål", ""))
            if oid and h:
                heights.setdefault(oid, h)
        except Exception:
            pass
    return heights


# ── Git + Notion upload (runs in background thread) ──
upload_queue = Queue()
upload_lock = threading.Lock()
notion_cache = {}  # oid -> {pid, has_3d}
notion_loaded = threading.Event()


def load_notion_pages():
    global notion_cache
    pages = {}
    has_more, cursor = True, None
    while has_more:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = None
        for attempt in range(3):
            try:
                r = requests.post(
                    f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
                    headers=NOTION_HDR, json=body, timeout=30,
                )
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(5 * (attempt + 1))
        if r is None or r.status_code != 200:
            break
        d = r.json()
        for p in d["results"]:
            props = p["properties"]
            rt = props.get("Objekt-ID", {}).get("rich_text", [])
            oid = rt[0]["plain_text"] if rt else ""
            files = props.get("3D-modell", {}).get("files", [])
            has_textured = any("_textured" in f.get("name", "") for f in files)
            if oid:
                pages[oid] = {"pid": p["id"], "has_3d": has_textured}
        has_more = d.get("has_more", False)
        cursor = d.get("next_cursor")
    notion_cache = pages
    notion_loaded.set()
    print(f"  [uploader] Notion: {len(pages)} pages loaded")


def update_notion_page(page_id, oid):
    url = f"{GITHUB_RAW}/{oid}/{oid}_textured.glb"
    payload = {
        "properties": {
            "3D-modell": {"files": [{"type": "external", "name": f"{oid}_textured.glb", "external": {"url": url}}]},
        }
    }
    for attempt in range(3):
        try:
            r = requests.patch(
                f"https://api.notion.com/v1/pages/{page_id}",
                headers=NOTION_HDR, json=payload, timeout=30,
            )
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            return r.status_code == 200
        except Exception:
            time.sleep(3)
    return False


def git_push_and_notify(oids):
    """Push new GLBs to GitHub and update Notion."""
    with upload_lock:
        try:
            lock = BASE / ".git" / "index.lock"
            if lock.exists():
                try:
                    lock.unlink()
                except Exception:
                    pass

            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard", "VA_3d/"],
                cwd=str(BASE), capture_output=True, text=True,
            )
            untracked = [
                f for f in result.stdout.strip().split("\n")
                if f.endswith(".glb") and "_prescale" not in f and f.strip()
            ]
            if not untracked:
                return

            print(f"  [uploader] Committing {len(untracked)} GLBs...")
            for git_attempt in range(3):
                lock = BASE / ".git" / "index.lock"
                if lock.exists():
                    try:
                        lock.unlink()
                    except Exception:
                        time.sleep(2)
                        continue
                add = subprocess.run(["git", "add"] + untracked, cwd=str(BASE),
                                     capture_output=True)
                if add.returncode == 0:
                    break
                time.sleep(3)

            subprocess.run(
                ["git", "commit", "-m", f"feat: add {len(untracked)} new PBR textured 3D chair models"],
                cwd=str(BASE), capture_output=True,
            )

            for attempt in range(3):
                subprocess.run(["git", "fetch", "origin", "main"], cwd=str(BASE),
                               capture_output=True)
                merge = subprocess.run(
                    ["git", "merge", "origin/main", "--no-edit"],
                    cwd=str(BASE), capture_output=True, text=True,
                )
                if merge.returncode != 0 and "untracked working tree files" in (merge.stderr or ""):
                    for line in merge.stderr.splitlines():
                        line = line.strip()
                        if line.endswith("_bguw.png"):
                            fp = BASE / line
                            if fp.exists():
                                fp.unlink()
                    subprocess.run(["git", "merge", "origin/main", "--no-edit"],
                                   cwd=str(BASE), capture_output=True)
                push = subprocess.run(["git", "push"], cwd=str(BASE), capture_output=True)
                if push.returncode == 0:
                    print(f"  [uploader] Pushed {len(untracked)} GLBs!")
                    break
                time.sleep(5)

            time.sleep(2)
            notion_loaded.wait()
            to_update = []
            for oid in oids:
                info = notion_cache.get(oid)
                if info and not info["has_3d"]:
                    to_update.append((oid, info["pid"]))

            if to_update:
                ok = 0
                with ThreadPoolExecutor(max_workers=10) as ex:
                    futs = {ex.submit(update_notion_page, pid, oid): oid for oid, pid in to_update}
                    for f in as_completed(futs):
                        try:
                            if f.result():
                                ok += 1
                                notion_cache[futs[f]]["has_3d"] = True
                        except Exception:
                            pass
                print(f"  [uploader] Notion: {ok}/{len(to_update)} updated")

        except Exception as e:
            print(f"  [uploader] Error: {e}")


def upload_worker():
    pending = []
    while True:
        oid = upload_queue.get()
        if oid is None:
            if pending:
                git_push_and_notify(pending)
            break
        pending.append(oid)
        if len(pending) >= BATCH_SIZE:
            git_push_and_notify(pending)
            pending = []


# ── GPU memory helpers ──
def move_to_cpu(model):
    """Move all parameters/buffers to CPU to free VRAM."""
    if hasattr(model, 'to'):
        model.to('cpu')
    if hasattr(model, 'models'):
        for m in model.models.values():
            if hasattr(m, 'pipeline'):
                m.pipeline.to('cpu')
            elif hasattr(m, 'to'):
                m.to('cpu')


def move_to_gpu(model, device='cuda'):
    """Move all parameters/buffers back to GPU."""
    if hasattr(model, 'to'):
        model.to(device)
    if hasattr(model, 'models'):
        for m in model.models.values():
            if hasattr(m, 'pipeline'):
                m.pipeline.to(device)
            elif hasattr(m, 'to'):
                m.to(device)


# ── Main ──
def main():
    import torch
    import trimesh

    print("=" * 60)
    print(" PBR Generate + Upload Pipeline (optimized)")
    print("=" * 60)

    if not NOTION_TOKEN:
        print("WARNING: No NOTION_API_KEY in .env — Notion updates disabled")

    # Collect source images
    images = sorted(SRC_DIR.glob("*_bguw.png"))
    if not images:
        print(f"No images found in {SRC_DIR}")
        return

    # Build height map
    print("Building height map...")
    heights = build_height_map()
    print(f"  Heights: {len(heights)} objects")

    # Split entries: need_geometry (no .glb) vs need_texture_only (have .glb, no _textured.glb)
    need_geometry = []
    need_texture = []
    skipped = 0
    for img_path in images:
        oid = img_path.stem.replace("_bguw", "")
        obj_dir = OUT_DIR / oid
        textured_path = obj_dir / f"{oid}_textured.glb"
        glb_path = obj_dir / f"{oid}.glb"
        if textured_path.exists():
            skipped += 1
            continue
        if glb_path.exists():
            need_texture.append((oid, img_path))
        else:
            need_geometry.append((oid, img_path))

    total = len(need_geometry) + len(need_texture)
    print(f"  {len(need_geometry)} need geometry+texture, {len(need_texture)} need texture only, {skipped} already done")

    if total == 0:
        print("Nothing to do.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Start background threads
    print("Loading Notion pages (background)...")
    notion_thread = threading.Thread(target=load_notion_pages, daemon=True)
    notion_thread.start()
    upload_thread = threading.Thread(target=upload_worker, daemon=True)
    upload_thread.start()

    if not torch.cuda.is_available():
        print("CUDA not available!")
        sys.exit(1)

    # GPU optimizations — max performance
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.set_float32_matmul_precision('high')

    device = "cuda"
    log = open(LOG_FILE, "a", encoding="utf-8")
    log.write(f"\n=== PBR Run {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    done = failed = 0
    global_idx = 0
    t_start = time.time()

    # ═══════════════════════════════════════════════════════════
    # PHASE 1: Generate geometry for models that need it
    # ═══════════════════════════════════════════════════════════
    if need_geometry:
        print(f"\n{'─'*60}")
        print(f" PHASE 1: Shape generation ({len(need_geometry)} models)")
        print(f"{'─'*60}")
        print("Loading shape pipeline...")

        from hy3dgen.rembg import BackgroundRemover
        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

        shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            "tencent/Hunyuan3D-2", device=device
        )
        shape_pipeline.to(device)
        shape_pipeline.enable_flashvdm()
        rembg = BackgroundRemover()
        print("  Shape pipeline ready (FlashVDM turbo enabled).\n")

        for i, (oid, img_path) in enumerate(need_geometry):
            obj_dir = OUT_DIR / oid
            glb_path = obj_dir / f"{oid}.glb"
            tag = f"[{i+1:03d}/{len(need_geometry)}] {oid}"

            print(f"{tag} — shape...", end=" ", flush=True)
            t0 = time.time()

            try:
                obj_dir.mkdir(parents=True, exist_ok=True)
                dst_img = obj_dir / img_path.name
                if not dst_img.exists():
                    shutil.copy2(img_path, dst_img)

                src_image = Image.open(img_path).convert("RGB")
                rembg_image = rembg(src_image)
                mesh = shape_pipeline(image=rembg_image, num_inference_steps=30)[0]

                # Scale
                height_cm = heights.get(oid)
                if height_cm:
                    target_m = height_cm / 100.0
                    bbox = mesh.bounds
                    current_h = float(bbox[1][1] - bbox[0][1])
                    if current_h <= 0:
                        current_h = float(mesh.extents.max())
                    if current_h > 0:
                        mesh.apply_scale(target_m / current_h)
                    note = f"scaled {height_cm}cm"
                else:
                    note = "unscaled"

                mesh.export(str(glb_path))
                elapsed = time.time() - t0
                msg = f"OK ({note}, {elapsed:.0f}s)"
                print(msg)
                log.write(f"{tag} — shape {msg}\n")
                log.flush()

            except Exception as e:
                elapsed = time.time() - t0
                msg = f"SHAPE FAILED: {e} ({elapsed:.0f}s)"
                print(msg)
                traceback.print_exc()
                log.write(f"{tag} — {msg}\n")
                log.flush()

            finally:
                torch.cuda.empty_cache()
                gc.collect()

        # Free shape pipeline entirely
        print("\nFreeing shape pipeline from GPU...")
        del shape_pipeline
        del rembg
        torch.cuda.empty_cache()
        gc.collect()

    # ═══════════════════════════════════════════════════════════
    # PHASE 2: Texture all models that have a .glb but no _textured.glb
    # ═══════════════════════════════════════════════════════════
    # Re-scan to pick up freshly generated meshes too
    texture_entries = []
    for img_path in images:
        oid = img_path.stem.replace("_bguw", "")
        obj_dir = OUT_DIR / oid
        glb_path = obj_dir / f"{oid}.glb"
        textured_path = obj_dir / f"{oid}_textured.glb"
        if glb_path.exists() and not textured_path.exists():
            texture_entries.append((oid, img_path, glb_path))

    if texture_entries:
        print(f"\n{'─'*60}")
        print(f" PHASE 2: PBR texturing ({len(texture_entries)} models)")
        print(f"{'─'*60}")
        print("Loading paint pipeline (full GPU)...")

        from hy3dgen.texgen import Hunyuan3DPaintPipeline
        paint_pipeline = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
        print("  Paint pipeline ready.\n")

        for i, (oid, img_path, glb_path) in enumerate(texture_entries):
            textured_path = glb_path.parent / f"{oid}_textured.glb"
            tag = f"[{i+1:03d}/{len(texture_entries)}] {oid}"

            print(f"{tag} — texturing...", end=" ", flush=True)
            t0 = time.time()

            try:
                mesh = trimesh.load(str(glb_path), process=False, force="mesh")

                # Decimate heavy meshes — xatlas UV unwrap is CPU-bound
                # and crawls on 500k+ face meshes. 100k is plenty for textures.
                if len(mesh.faces) > 100_000:
                    import fast_simplification
                    ratio = 1.0 - (100_000 / len(mesh.faces))
                    verts, faces = fast_simplification.simplify(
                        mesh.vertices, mesh.faces, target_reduction=ratio)
                    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)

                src_image = Image.open(img_path).convert("RGB")

                textured_mesh = paint_pipeline(mesh, src_image)
                textured_mesh.export(str(textured_path))

                elapsed = time.time() - t0
                done += 1
                rate = done / (time.time() - t_start) * 3600
                remaining = len(texture_entries) - i - 1
                eta_h = remaining / (done / (time.time() - t_start)) / 3600 if done else 0
                msg = f"OK ({elapsed:.0f}s) [{rate:.0f}/hr, ETA {eta_h:.1f}h]"
                print(msg)
                log.write(f"{tag} — texture {msg}\n")
                log.flush()

                upload_queue.put(oid)

            except Exception as e:
                elapsed = time.time() - t0
                msg = f"TEXTURE FAILED: {e} ({elapsed:.0f}s)"
                print(msg)
                traceback.print_exc()
                log.write(f"{tag} — {msg}\n")
                log.flush()
                failed += 1

            finally:
                torch.cuda.empty_cache()
                gc.collect()

    # Flush remaining uploads
    upload_queue.put(None)
    upload_thread.join(timeout=300)

    log.close()
    elapsed_total = (time.time() - t_start) / 3600
    print(f"\n{'='*60}")
    print(f" Done: {done} textured, {skipped} skipped, {failed} failed")
    print(f" Time: {elapsed_total:.1f}h ({done/(elapsed_total or 1):.0f}/hr)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
