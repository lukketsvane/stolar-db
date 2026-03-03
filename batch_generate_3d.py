"""
Batch 3D mesh generation for NM_stolar museum furniture images.

For each image in NM_stolar/:
  - Creates/finds noreg/<ObjectID>/ subfolder
  - Copies image if not present
  - Generates a 3D GLB mesh via Hunyuan3D-2
  - Scales the mesh uniformly so its height = recorded catalog height (cm -> meters)

Usage:
    C:/Users/Shadow/Desktop/stolar-db/Hunyuan3D-2/venv/Scripts/python.exe batch_generate_3d.py

Resumable: already-completed GLBs are skipped.
"""

import csv
import json
import os
import re
import shutil
import sys
import time
import traceback
from pathlib import Path

# ---- Paths ------------------------------------------------------------------
BASE        = Path("C:/Users/Shadow/Desktop/stolar-db")
NM_STOLAR   = BASE / "NM_stolar"
NOREG       = BASE / "noreg"
HY3D_ROOT   = BASE / "Hunyuan3D-2"
LOG_FILE    = BASE / "batch_generate_3d.log"

sys.path.insert(0, str(HY3D_ROOT))

# ---- Height helpers ---------------------------------------------------------

def _try_float(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None


def _h_from_maal(maal_str):
    """Extract H value from strings like 'H 96 x B 45 x D 41,5 cm'."""
    m = re.search(r'\bH[^\d]*(\d+[,.]?\d*)', str(maal_str or ""))
    return _try_float(m.group(1)) if m else None


def build_height_map():
    heights = {}

    # norske_stolar.csv
    csv_path = BASE / "norske_stolar.csv"
    if csv_path.exists():
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f, delimiter=";"):
                oid = row.get("object_id", "").strip()
                h   = _try_float(row.get("hoegde_cm"))
                if oid and h and oid not in heights:
                    heights[oid] = h

    # All JSON files (skip heavy dirs)
    SKIP = {"node_modules", "Hunyuan3D-2", "venv", ".git", ".claude"}
    for dirpath, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for fname in files:
            if not fname.endswith(".json"):
                continue
            try:
                data = json.loads(Path(dirpath, fname).read_text(encoding="utf-8"))
            except Exception:
                continue
            for item in (data if isinstance(data, list) else [data]):
                if not isinstance(item, dict):
                    continue
                props = item.get("properties", item)
                oid = (props.get("Objekt-ID") or props.get("objectId") or
                       props.get("object_id") or item.get("objectId") or
                       item.get("object_id"))
                if not oid:
                    continue
                oid = str(oid).strip()
                h = (_try_float(props.get("Hoegde (cm)") or props.get("Hogde (cm)") or
                                props.get("H\u00f8gde (cm)") or props.get("H\u00f8yde (cm)") or
                                props.get("hoegde_cm") or props.get("height_cm") or
                                item.get("H\u00f8gde (cm)") or item.get("hoegde_cm"))
                    or _h_from_maal(props.get("M\u00e5l") or item.get("M\u00e5l")))
                if h and oid not in heights:
                    heights[oid] = h

    return heights


def fetch_height_api(object_id):
    try:
        import requests
        url = f"https://api.digitaltmuseum.org/search?q={object_id}&museums=NMK&fields=dimensions"
        resp = requests.get(url, timeout=10)
        if resp.ok:
            for item in (resp.json().get("items") or []):
                dims = item.get("dimensions") or {}
                h = _try_float(dims.get("height") or dims.get("height_cm"))
                if h:
                    return h
                h = _h_from_maal(item.get("description", ""))
                if h:
                    return h
    except Exception:
        pass
    return None


# ---- Main -------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Batch 3D Generation - NM_stolar")
    print("=" * 60)

    print("Building height map...")
    heights = build_height_map()
    print(f"  Local heights: {len(heights)} objects")

    images = sorted(f for f in os.listdir(NM_STOLAR) if f.lower().endswith(".jpg"))
    print(f"  Images: {len(images)}")

    # API fallback for missing heights
    missing = [img.rsplit("_", 1)[0] for img in images
               if img.rsplit("_", 1)[0] not in heights]
    if missing:
        print(f"  Fetching {len(missing)} missing heights from API...")
        for oid in missing:
            h = fetch_height_api(oid)
            if h:
                heights[oid] = h
                print(f"    {oid} -> {h} cm (API)")
            else:
                print(f"    {oid} -> not found (will save unscaled)")

    # Load pipeline
    print("\nLoading Hunyuan3D-2 (first run downloads ~5 GB of weights)...")
    from hy3dgen.rembg import BackgroundRemover
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2")
    rembg    = BackgroundRemover()
    print("  Ready.\n")

    log = open(LOG_FILE, "a", encoding="utf-8")
    log.write(f"\n=== Run {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    done = skipped = failed = 0
    total = len(images)

    for i, img_file in enumerate(images):
        object_id = img_file.rsplit("_", 1)[0]
        src_img   = NM_STOLAR / img_file
        out_dir   = NOREG / object_id
        glb_path  = out_dir / f"{object_id}.glb"
        dst_img   = out_dir / img_file
        tag       = f"[{i+1:03d}/{total}] {object_id}"

        if glb_path.exists():
            print(f"{tag} - SKIP")
            skipped += 1
            continue

        print(f"{tag} - generating...", flush=True)
        t0 = time.time()
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            if not dst_img.exists():
                shutil.copy2(src_img, dst_img)

            image = rembg(Image.open(src_img).convert("RGB"))
            mesh  = pipeline(image=image, num_inference_steps=50)[0]

            height_cm = heights.get(object_id)
            if height_cm:
                target_m  = height_cm / 100.0
                current_h = float(mesh.extents.max())
                if current_h > 0:
                    mesh.apply_scale(target_m / current_h)
                note = f"scaled {height_cm}cm"
            else:
                note = "unscaled"

            mesh.export(str(glb_path))
            msg = f"{tag} - OK ({note}, {time.time()-t0:.0f}s)"
            print(msg); log.write(msg + "\n"); log.flush()
            done += 1

        except Exception as e:
            msg = f"{tag} - FAILED: {e} ({time.time()-t0:.0f}s)"
            print(msg); traceback.print_exc()
            log.write(msg + "\n" + traceback.format_exc() + "\n"); log.flush()
            failed += 1

    summary = f"Done: {done} generated, {skipped} skipped, {failed} failed"
    log.write(summary + "\n")
    log.close()
    print("\n" + "=" * 60)
    print(summary)
    print(f"Log: {LOG_FILE}")


if __name__ == "__main__":
    from PIL import Image
    main()
