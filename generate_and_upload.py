#!/usr/bin/env python3
"""
generate_and_upload.py — Single script: generate 3D meshes on GPU,
scale them, push to GitHub, and update Notion — all simultaneously.

GPU generates meshes continuously while a background thread handles
git push + Notion updates every BATCH_SIZE models.
"""

import gc
import json
import os
import re
import struct
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

# ── Config ──
BASE = Path(__file__).parent
SRC_DIR = BASE / "STOLAR" / "bguw"
OUT_DIR = BASE / "STOLAR" / "glb"
LOG_FILE = BASE / "generate_and_upload.log"
BATCH_SIZE = 10  # push + update Notion every N new meshes

# ── Notion ──
NOTION_TOKEN = ""
env_file = BASE / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("NOTION_API_KEY="):
            NOTION_TOKEN = line.split("=", 1)[1].strip().strip('"')

DATABASE_ID = "405e0f64-6b77-4aab-88b8-73281e58c4f0"
GITHUB_RAW_GLB = "https://raw.githubusercontent.com/lukketsvane/stolar-db/main/STOLAR/glb"
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
        if r.status_code != 200:
            break
        d = r.json()
        for p in d["results"]:
            props = p["properties"]
            rt = props.get("Objekt-ID", {}).get("rich_text", [])
            oid = rt[0]["plain_text"] if rt else ""
            has_3d = len(props.get("3D-modell", {}).get("files", [])) > 0
            if oid:
                pages[oid] = {"pid": p["id"], "has_3d": has_3d}
        has_more = d.get("has_more", False)
        cursor = d.get("next_cursor")
    notion_cache = pages
    notion_loaded.set()
    print(f"  [uploader] Notion: {len(pages)} pages loaded")


def update_notion_page(page_id, oid):
    url = f"{GITHUB_RAW_GLB}/{oid}.glb"
    payload = {
        "properties": {
            "3D-modell": {"files": [{"type": "external", "name": f"{oid}.glb", "external": {"url": url}}]},
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
            # Clear stale lock if exists
            lock = BASE / ".git" / "index.lock"
            if lock.exists():
                try:
                    lock.unlink()
                except Exception:
                    pass

            # Find untracked GLBs
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard", "STOLAR/"],
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
                ["git", "commit", "-m", f"feat: add {len(untracked)} new scaled 3D chair models"],
                cwd=str(BASE), capture_output=True,
            )

            # Fetch + merge + push with retry
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

            # Update Notion for new oids
            time.sleep(2)  # let GitHub CDN catch up
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
    """Background thread: batches upload requests."""
    pending = []
    while True:
        oid = upload_queue.get()
        if oid is None:  # shutdown signal
            if pending:
                git_push_and_notify(pending)
            break
        pending.append(oid)
        if len(pending) >= BATCH_SIZE:
            git_push_and_notify(pending)
            pending = []


# ── Main ──
def main():
    print("=" * 60)
    print(" Generate + Upload Pipeline (single script)")
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

    entries = []
    for img_path in images:
        oid = img_path.stem.replace("_bguw", "")
        entries.append((oid, img_path))

    with_h = sum(1 for oid, _ in entries if oid in heights)
    print(f"  Images: {len(entries)} ({with_h} with height, {len(entries)-with_h} unscaled)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Start background threads
    print("Loading Notion pages (background)...")
    notion_thread = threading.Thread(target=load_notion_pages, daemon=True)
    notion_thread.start()

    upload_thread = threading.Thread(target=upload_worker, daemon=True)
    upload_thread.start()

    # Load GPU pipeline
    print("Loading Hunyuan3D-2 pipeline...")
    import torch
    from hy3dgen.rembg import BackgroundRemover
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

    if not torch.cuda.is_available():
        print("CUDA not available! Run as Administrator.")
        sys.exit(1)

    # GPU optimizations
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    device = "cuda"
    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        "tencent/Hunyuan3D-2", device=device
    )
    pipeline.to(device)
    rembg = BackgroundRemover()
    print("Pipeline ready.\n")

    log = open(LOG_FILE, "a", encoding="utf-8")
    log.write(f"\n=== Run {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    done = skipped = failed = 0
    total = len(entries)
    t_start = time.time()

    for i, (oid, img_path) in enumerate(entries):
        glb_path = OUT_DIR / f"{oid}.glb"
        tag = f"[{i+1:03d}/{total}] {oid}"

        if glb_path.exists():
            skipped += 1
            continue

        print(f"{tag} — generating...", flush=True)
        t0 = time.time()

        try:
            OUT_DIR.mkdir(parents=True, exist_ok=True)

            # Generate mesh
            image = rembg(Image.open(img_path).convert("RGB"))
            mesh = pipeline(image=image, num_inference_steps=50)[0]

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
            rate = done / (time.time() - t_start) * 3600 if done else 0
            remaining = total - i - 1
            eta_h = remaining / (done / (time.time() - t_start)) / 3600 if done else 0
            msg = f"{tag} — OK ({note}, {elapsed:.0f}s) [{rate:.0f}/hr, ETA {eta_h:.1f}h]"
            print(msg)
            log.write(msg + "\n")
            log.flush()
            done += 1

            # Queue for upload
            upload_queue.put(oid)

        except Exception as e:
            elapsed = time.time() - t0
            msg = f"{tag} — FAILED: {e} ({elapsed:.0f}s)"
            print(msg)
            traceback.print_exc()
            log.write(msg + "\n")
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
    print(f" Done: {done} generated, {skipped} skipped, {failed} failed")
    print(f" Time: {elapsed_total:.1f}h ({done/(elapsed_total or 1):.0f}/hr)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
