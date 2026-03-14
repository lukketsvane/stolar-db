#!/usr/bin/env python3
"""
copy_noreg_glbs.py — Copy existing GLB models from noreg/ into NM_stolar/{objectId}/ subfolders
for entries that don't yet have a GLB there.

Also copies the per-object JSON if available, and updates model3d in NM_stolar.json.
"""

import json
import os
import shutil
from pathlib import Path

BASE = Path(__file__).parent
NM_DIR = BASE / "NM_stolar"
NOREG = BASE / "noreg"
META_JSON = NM_DIR / "NM_stolar.json"


def main():
    data = json.loads(META_JSON.read_text(encoding="utf-8"))
    print(f"Loaded {len(data)} entries from NM_stolar.json")

    copied = skipped = already = no_source = 0

    for entry in data:
        oid = entry.get("objectId", "")
        if not oid:
            continue

        out_dir = NM_DIR / oid

        # Check if GLB already exists in NM_stolar/{oid}/
        if out_dir.is_dir():
            existing_glbs = [f for f in os.listdir(out_dir) if f.endswith(".glb")]
            if existing_glbs:
                already += 1
                continue

        # Check noreg/{oid}/ for a GLB
        noreg_dir = NOREG / oid
        if not noreg_dir.is_dir():
            no_source += 1
            continue

        noreg_glbs = [f for f in os.listdir(noreg_dir) if f.endswith(".glb")]
        if not noreg_glbs:
            no_source += 1
            continue

        # Copy GLB(s)
        out_dir.mkdir(parents=True, exist_ok=True)
        glb_name = noreg_glbs[0]
        shutil.copy2(noreg_dir / glb_name, out_dir / glb_name)

        # Copy per-object JSON if available
        noreg_json = noreg_dir / f"{oid}.json"
        out_json = out_dir / f"{oid}.json"
        if noreg_json.exists() and not out_json.exists():
            shutil.copy2(noreg_json, out_json)

        # Copy source image if available (PNG at NM_stolar root)
        for img in entry.get("images", []):
            fn = img.get("filename", "")
            if fn:
                stem = os.path.splitext(fn)[0]
                for ext in (".png", ".jpg"):
                    src_img = NM_DIR / f"{stem}{ext}"
                    if src_img.exists():
                        dst_img = out_dir / src_img.name
                        if not dst_img.exists():
                            shutil.copy2(src_img, dst_img)
                        break

        # Update entry
        entry["model3d"] = glb_name
        for img in entry.get("images", []):
            if img.get("filename", "").startswith(oid):
                img["glb"] = glb_name

        copied += 1
        print(f"  Copied {oid}/{glb_name}")

    # Write updated master JSON
    META_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nDone:")
    print(f"  Already had GLB: {already}")
    print(f"  Copied from noreg: {copied}")
    print(f"  No source GLB: {no_source}")
    print(f"  Total: {already + copied + no_source}")


if __name__ == "__main__":
    main()
