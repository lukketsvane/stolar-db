#!/usr/bin/env python3
"""
generate_textured_and_upload.py — Add PBR textures to existing untextured GLB
meshes using Hunyuan3D-2's paint pipeline, push to GitHub, update Notion.

GPU textures meshes continuously while a background thread handles
git push + Notion updates every BATCH_SIZE models.
"""

import gc
import os
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from queue import Queue

import requests
import trimesh
from PIL import Image

# ── Config ──
BASE = Path(__file__).parent
OUT_DIR = BASE / "VA_3d"
BGUW_DIR = BASE / "VA_bguw"
LOG_FILE = BASE / "generate_textured_and_upload.log"
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


# ── Git + Notion upload (runs in background thread) ──
upload_queue = Queue()
upload_lock = threading.Lock()
notion_cache = {}  # oid -> {pid, has_textured}
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
                pages[oid] = {"pid": p["id"], "has_textured": has_textured}
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
    """Push new textured GLBs to GitHub and update Notion."""
    with upload_lock:
        try:
            # Clear stale lock if exists
            lock = BASE / ".git" / "index.lock"
            if lock.exists():
                try:
                    lock.unlink()
                except Exception:
                    pass

            # Find untracked textured GLBs
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard", "VA_3d/"],
                cwd=str(BASE), capture_output=True, text=True,
            )
            untracked = [
                f for f in result.stdout.strip().split("\n")
                if f.endswith("_textured.glb") and f.strip()
            ]
            if not untracked:
                return

            print(f"  [uploader] Committing {len(untracked)} textured GLBs...")
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
                ["git", "commit", "-m", f"feat: add {len(untracked)} new textured 3D chair models"],
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
                    print(f"  [uploader] Pushed {len(untracked)} textured GLBs!")
                    break
                time.sleep(5)

            # Update Notion for new oids
            time.sleep(2)  # let GitHub CDN catch up
            notion_loaded.wait()
            to_update = []
            for oid in oids:
                info = notion_cache.get(oid)
                if info and not info["has_textured"]:
                    to_update.append((oid, info["pid"]))

            if to_update:
                ok = 0
                with ThreadPoolExecutor(max_workers=10) as ex:
                    futs = {ex.submit(update_notion_page, pid, oid): oid for oid, pid in to_update}
                    for f in as_completed(futs):
                        try:
                            if f.result():
                                ok += 1
                                notion_cache[futs[f]]["has_textured"] = True
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
    print(" Texture Generation + Upload Pipeline")
    print("=" * 60)

    if not NOTION_TOKEN:
        print("WARNING: No NOTION_API_KEY in .env — Notion updates disabled")

    # Collect entries: GLBs that lack a _textured.glb, matched with bguw image
    entries = []
    for obj_dir in sorted(OUT_DIR.iterdir()):
        if not obj_dir.is_dir():
            continue
        oid = obj_dir.name
        glb_path = obj_dir / f"{oid}.glb"
        textured_path = obj_dir / f"{oid}_textured.glb"
        if not glb_path.exists():
            continue
        if textured_path.exists():
            continue
        # Find bguw reference image
        bguw_path = BGUW_DIR / f"{oid}_bguw.png"
        if not bguw_path.exists():
            # Also check inside the object directory
            bguw_path = obj_dir / f"{oid}_bguw.png"
        if not bguw_path.exists():
            continue
        entries.append((oid, glb_path, bguw_path))

    if not entries:
        print("No entries to process (all textured or no matching bguw images).")
        return

    print(f"  Entries: {len(entries)} meshes to texture")

    # Start background threads
    print("Loading Notion pages (background)...")
    notion_thread = threading.Thread(target=load_notion_pages, daemon=True)
    notion_thread.start()

    upload_thread = threading.Thread(target=upload_worker, daemon=True)
    upload_thread.start()

    # Load GPU pipeline
    print("Loading Hunyuan3D-2 paint pipeline...")
    import torch
    from hy3dgen.texgen import Hunyuan3DPaintPipeline

    if not torch.cuda.is_available():
        print("CUDA not available! Run as Administrator.")
        sys.exit(1)

    # GPU optimizations
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    paint_pipeline = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
    print("Paint pipeline ready.\n")

    log = open(LOG_FILE, "a", encoding="utf-8")
    log.write(f"\n=== Texture Run {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    done = failed = 0
    total = len(entries)
    t_start = time.time()

    for i, (oid, glb_path, bguw_path) in enumerate(entries):
        textured_path = glb_path.parent / f"{oid}_textured.glb"
        tag = f"[{i+1:03d}/{total}] {oid}"

        print(f"{tag} — texturing...", flush=True)
        t0 = time.time()

        try:
            # Load mesh and image
            mesh = trimesh.load(str(glb_path), process=False, force="mesh")
            image = Image.open(bguw_path).convert("RGB")

            # Generate textured mesh
            textured_mesh = paint_pipeline(mesh, image)

            # Export
            textured_mesh.export(str(textured_path))

            elapsed = time.time() - t0
            done += 1
            rate = done / (time.time() - t_start) * 3600
            remaining = total - i - 1
            eta_h = remaining / (done / (time.time() - t_start)) / 3600
            msg = f"{tag} — OK ({elapsed:.0f}s) [{rate:.0f}/hr, ETA {eta_h:.1f}h]"
            print(msg)
            log.write(msg + "\n")
            log.flush()

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
    print(f" Done: {done} textured, {failed} failed, {total - done - failed} skipped")
    print(f" Time: {elapsed_total:.1f}h ({done/(elapsed_total or 1):.0f}/hr)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
