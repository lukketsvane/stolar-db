#!/usr/bin/env python3
"""
fix_broken_images.py — Audit and fix broken GitHub image URLs in Notion.

Phase 1 (--audit): Check all Bilete-bguw and 3D-modell URLs for 404s,
                    cross-reference with local files, print report.
Phase 2 (--fix):   Push missing local files to GitHub, regenerate via
                    Gemini if needed, update Notion URLs.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import requests
from PIL import Image

# ── Config ──
BASE = Path(__file__).parent
VA_DIR = BASE / "VA"
BGUW_DIR = BASE / "VA_bguw"
VA_3D = BASE / "VA_3d"

NOTION_TOKEN = ""
GEMINI_API_KEY = ""
GH_TOKEN = ""
env_file = BASE / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"')
        if k == "NOTION_API_KEY":
            NOTION_TOKEN = v
        elif k == "GEMINI_API_KEY":
            GEMINI_API_KEY = v
        elif k == "PERSONAL_ACCESS_TOKEN":
            GH_TOKEN = v

DATABASE_ID = "405e0f64-6b77-4aab-88b8-73281e58c4f0"
GH_OWNER = "lukketsvane"
GH_REPO = "stolar-db"
GH_BRANCH = "main"
GITHUB_RAW = f"https://raw.githubusercontent.com/{GH_OWNER}/{GH_REPO}/{GH_BRANCH}/VA_3d"
PROP_BGUW = "Bilete-bguw"
PROP_3D = "3D-modell"
UA = "stolar-db/1.0 (PhD research; AHO)"

NOTION_HDR = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

GEMINI_MODEL = "gemini-3.1-flash-image-preview"
GEMINI_PROMPT = "place it sharp against solid white background, have the subject cut sharply, and background be #fff 100% white."

AUDIT_WORKERS = 25
NOTION_WORKERS = 5
BGUW_WORKERS = 10
AUDIT_OUTPUT = BASE / "broken_images_audit.json"


# ── Notion helpers ──
def query_notion():
    pages = []
    cursor, has_more = None, True
    while has_more:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        for attempt in range(3):
            r = requests.post(
                f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
                headers=NOTION_HDR, json=body, timeout=30,
            )
            if r.status_code == 200:
                break
            time.sleep(5 * (attempt + 1))
        r.raise_for_status()
        data = r.json()
        pages.extend(data["results"])
        has_more = data.get("has_more", False)
        cursor = data.get("next_cursor")
    return pages


def extract_file_url(props, prop_name):
    """Extract URL from a Notion files property (handles both external and file types)."""
    files = props.get(prop_name, {}).get("files", [])
    if not files:
        return None, None
    f = files[0]
    url = f.get("external", {}).get("url") or f.get("file", {}).get("url")
    name = f.get("name", "")
    return url, name


def parse_pages(pages):
    entries = []
    for p in pages:
        props = p["properties"]
        rt = props.get("Objekt-ID", {}).get("rich_text", [])
        oid = rt[0]["plain_text"] if rt else ""
        if not oid:
            continue
        bguw_url, bguw_name = extract_file_url(props, PROP_BGUW)
        model_url, model_name = extract_file_url(props, PROP_3D)
        bilete_url = props.get("Bilete-URL", {}).get("url") or ""
        entries.append({
            "oid": oid,
            "pid": p["id"],
            "bguw_url": bguw_url,
            "bguw_name": bguw_name,
            "model_url": model_url,
            "model_name": model_name,
            "bilete_url": bilete_url,
        })
    return entries


# ── Phase 1: Audit ──
def check_url(url, session):
    """HEAD request to check if URL is live. Returns status code."""
    try:
        r = session.head(url, timeout=10, allow_redirects=True)
        return r.status_code
    except requests.exceptions.Timeout:
        return 0
    except Exception:
        return -1


def audit_entries(entries):
    """Check all URLs and categorize results."""
    results = {
        "bguw": {"ok": [], "404_has_local": [], "404_has_bguw_source": [], "404_no_local": [], "other_error": []},
        "model": {"ok": [], "404_has_local": [], "404_no_local": [], "other_error": []},
        "no_bguw_url": [],
        "no_model_url": [],
    }

    # Collect URLs to check
    bguw_checks = [(e, e["bguw_url"]) for e in entries if e["bguw_url"]]
    model_checks = [(e, e["model_url"]) for e in entries if e["model_url"]]

    for e in entries:
        if not e["bguw_url"]:
            results["no_bguw_url"].append({"oid": e["oid"], "pid": e["pid"]})
        if not e["model_url"]:
            results["no_model_url"].append({"oid": e["oid"], "pid": e["pid"]})

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    # Check bguw URLs
    if bguw_checks:
        print(f"  Checking {len(bguw_checks)} Bilete-bguw URLs...")
        with ThreadPoolExecutor(max_workers=AUDIT_WORKERS) as ex:
            futures = {}
            for e, url in bguw_checks:
                futures[ex.submit(check_url, url, session)] = e
                time.sleep(0.02)  # 20ms stagger to avoid CDN throttling

            done = 0
            for f in as_completed(futures):
                e = futures[f]
                status = f.result()
                done += 1
                oid = e["oid"]

                if done % 100 == 0:
                    print(f"    ...checked {done}/{len(bguw_checks)}")

                if status == 200:
                    results["bguw"]["ok"].append({"oid": oid, "url": e["bguw_url"]})
                elif status in (404, 0, -1):
                    local_va3d = VA_3D / oid / f"{oid}_bguw.png"
                    local_bguw = BGUW_DIR / f"{oid}_bguw.png"

                    if local_va3d.exists():
                        results["bguw"]["404_has_local"].append({
                            "oid": oid, "pid": e["pid"], "url": e["bguw_url"],
                            "local_path": str(local_va3d),
                        })
                    elif local_bguw.exists():
                        results["bguw"]["404_has_bguw_source"].append({
                            "oid": oid, "pid": e["pid"], "url": e["bguw_url"],
                            "source_path": str(local_bguw),
                        })
                    else:
                        results["bguw"]["404_no_local"].append({
                            "oid": oid, "pid": e["pid"], "url": e["bguw_url"],
                            "bilete_url": e["bilete_url"],
                        })
                else:
                    results["bguw"]["other_error"].append({
                        "oid": oid, "url": e["bguw_url"], "status": status,
                    })

    # Check 3D model URLs
    if model_checks:
        print(f"  Checking {len(model_checks)} 3D-modell URLs...")
        with ThreadPoolExecutor(max_workers=AUDIT_WORKERS) as ex:
            futures = {}
            for e, url in model_checks:
                futures[ex.submit(check_url, url, session)] = e
                time.sleep(0.02)

            done = 0
            for f in as_completed(futures):
                e = futures[f]
                status = f.result()
                done += 1
                oid = e["oid"]

                if done % 100 == 0:
                    print(f"    ...checked {done}/{len(model_checks)}")

                if status == 200:
                    results["model"]["ok"].append({"oid": oid, "url": e["model_url"]})
                elif status in (404, 0, -1):
                    # Check for local GLB files
                    has_local = False
                    for suffix in [".glb", "_textured.glb"]:
                        if (VA_3D / oid / f"{oid}{suffix}").exists():
                            has_local = True
                            break
                    if has_local:
                        results["model"]["404_has_local"].append({
                            "oid": oid, "pid": e["pid"], "url": e["model_url"],
                            "model_name": e["model_name"],
                        })
                    else:
                        results["model"]["404_no_local"].append({
                            "oid": oid, "pid": e["pid"], "url": e["model_url"],
                        })
                else:
                    results["model"]["other_error"].append({
                        "oid": oid, "url": e["model_url"], "status": status,
                    })

    session.close()
    return results


def print_audit_report(results):
    bg = results["bguw"]
    md = results["model"]
    print(f"\n{'='*60}")
    print(f" Broken Image Audit Report")
    print(f"{'='*60}")
    print(f"\n Bilete-bguw URLs:")
    print(f"   OK:                       {len(bg['ok']):>5}")
    print(f"   404 (has local VA_3d):     {len(bg['404_has_local']):>5}  <- git push + Notion update")
    print(f"   404 (has VA_bguw source):  {len(bg['404_has_bguw_source']):>5}  <- copy + git push + Notion")
    print(f"   404 (no local file):       {len(bg['404_no_local']):>5}  <- needs Gemini regeneration")
    print(f"   Other errors:              {len(bg['other_error']):>5}")
    print(f"   No URL set:                {len(results['no_bguw_url']):>5}")
    print(f"\n 3D-modell URLs:")
    print(f"   OK:                       {len(md['ok']):>5}")
    print(f"   404 (has local file):      {len(md['404_has_local']):>5}  <- git push + Notion update")
    print(f"   404 (no local file):       {len(md['404_no_local']):>5}  <- needs regeneration")
    print(f"   Other errors:              {len(md['other_error']):>5}")
    print(f"   No URL set:                {len(results['no_model_url']):>5}")
    total_broken = (len(bg['404_has_local']) + len(bg['404_has_bguw_source']) +
                    len(bg['404_no_local']) + len(md['404_has_local']) + len(md['404_no_local']))
    print(f"\n Total broken: {total_broken}")
    print(f"{'='*60}")


def save_audit(results, path):
    out = {
        "timestamp": datetime.now().isoformat(),
        "bguw": results["bguw"],
        "model": results["model"],
        "no_bguw_url": results["no_bguw_url"],
        "no_model_url": results["no_model_url"],
    }
    # Convert to serializable (drop Path objects)
    path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\nAudit saved to {path}")


# ── Phase 2: Fix ──
def fix_bguw_copy_source(entries):
    """Copy bguw from VA_bguw/ to VA_3d/{oid}/ for entries missing in VA_3d."""
    fixed = []
    for e in entries:
        oid = e["oid"]
        src = BGUW_DIR / f"{oid}_bguw.png"
        dest_dir = VA_3D / oid
        dest = dest_dir / f"{oid}_bguw.png"
        if dest.exists():
            fixed.append(oid)
            continue
        dest_dir.mkdir(exist_ok=True)
        shutil.copy2(src, dest)
        fixed.append(oid)
    return fixed


def fix_bguw_regenerate(entries):
    """Regenerate bguw via Gemini for entries with no local file."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=GEMINI_API_KEY)

    # First download missing source images
    to_download = []
    for e in entries:
        oid = e["oid"]
        src = VA_DIR / f"{oid}.jpg"
        if not src.exists():
            src = VA_DIR / f"{oid}.png"
        if not src.exists() and e.get("bilete_url"):
            to_download.append((oid, e["bilete_url"]))

    if to_download:
        print(f"    Downloading {len(to_download)} source images...")
        for oid, url in to_download:
            try:
                req = Request(url, headers={"User-Agent": UA})
                with urlopen(req, timeout=30) as resp:
                    (VA_DIR / f"{oid}.jpg").write_bytes(resp.read())
            except Exception as ex:
                print(f"      {oid} download failed: {str(ex)[:60]}")

    # Generate bguw
    need = []
    for e in entries:
        oid = e["oid"]
        src = VA_DIR / f"{oid}.jpg"
        if not src.exists():
            src = VA_DIR / f"{oid}.png"
        if not src.exists():
            continue
        bguw_out = BGUW_DIR / f"{oid}_bguw.png"
        need.append((oid, src, bguw_out))

    if not need:
        print("    No source images available for regeneration.")
        return []

    print(f"    Generating {len(need)} bguw images via Gemini...")
    fixed = []
    with ThreadPoolExecutor(max_workers=BGUW_WORKERS) as ex:
        futures = {ex.submit(_generate_single, oid, src, out, client): oid
                   for oid, src, out in need}
        for i, f in enumerate(as_completed(futures)):
            oid, status = f.result()
            if status in ("ok", "exists"):
                # Copy to VA_3d
                dest_dir = VA_3D / oid
                dest_dir.mkdir(exist_ok=True)
                dest = dest_dir / f"{oid}_bguw.png"
                bguw_src = BGUW_DIR / f"{oid}_bguw.png"
                if not dest.exists() and bguw_src.exists():
                    shutil.copy2(bguw_src, dest)
                fixed.append(oid)
                if len(fixed) <= 10:
                    print(f"      [{i+1}/{len(need)}] {oid} -> OK")
            else:
                print(f"      [{i+1}/{len(need)}] {oid} -> {status}")
    return fixed


def _generate_single(oid, img_path, out_path, client):
    """Generate a single bguw image via Gemini."""
    if out_path.exists():
        return oid, "exists"

    for attempt in range(3):
        try:
            from google.genai import types
            img = Image.open(img_path)
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
                image_config=types.ImageConfig(aspect_ratio="1:1", image_size="1K"),
                response_modalities=["IMAGE", "TEXT"],
            )
            saved = False
            for chunk in client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=[GEMINI_PROMPT, img],
                config=config,
            ):
                if chunk.parts is None:
                    continue
                for part in chunk.parts:
                    if part.inline_data and part.inline_data.data:
                        out_path.write_bytes(part.inline_data.data)
                        saved = True
            if saved:
                return oid, "ok"
            return oid, "no_output"
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                time.sleep(15 * (attempt + 1))
                continue
            return oid, f"error: {err[:60]}"
    return oid, "rate_limit"


def git_push_files(file_paths):
    """Git add, commit, pull, push a list of file paths."""
    if not file_paths:
        return True

    # Clear stale lock
    lock = BASE / ".git" / "index.lock"
    if lock.exists():
        try:
            lock.unlink()
        except Exception:
            pass

    # git add (batch in groups to avoid arg length limits on Windows)
    BATCH = 100
    for i in range(0, len(file_paths), BATCH):
        batch = file_paths[i:i+BATCH]
        subprocess.run(["git", "add"] + batch, cwd=str(BASE), capture_output=True)

    # Commit
    n = len(file_paths)
    result = subprocess.run(
        ["git", "commit", "-m", f"fix: push {n} missing bguw/glb files to fix broken Notion URLs"],
        cwd=str(BASE), capture_output=True, text=True,
    )
    if result.returncode != 0:
        if "nothing to commit" in (result.stdout + result.stderr):
            print("    Nothing new to commit (files already tracked).")
            return True
        print(f"    Commit failed: {result.stderr[:200]}")
        return False

    # Fetch + merge + push with retry
    for attempt in range(3):
        subprocess.run(["git", "fetch", "origin", "main"], cwd=str(BASE), capture_output=True)
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

        push = subprocess.run(["git", "push"], cwd=str(BASE), capture_output=True, text=True)
        if push.returncode == 0:
            return True
        print(f"    Push attempt {attempt+1} failed: {push.stderr[:100]}")
        time.sleep(5)
    return False


def notion_set_bguw(pid, oid):
    url = f"{GITHUB_RAW}/{oid}/{oid}_bguw.png"
    for attempt in range(3):
        try:
            r = requests.patch(
                f"https://api.notion.com/v1/pages/{pid}",
                headers=NOTION_HDR,
                json={"properties": {
                    PROP_BGUW: {"files": [{
                        "type": "external",
                        "name": f"{oid}_bguw.png",
                        "external": {"url": url},
                    }]}
                }},
                timeout=30,
            )
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            return r.status_code == 200
        except Exception:
            time.sleep(3)
    return False


def notion_set_model(pid, oid, model_name):
    """Re-set the 3D-modell URL to point to the correct file."""
    # Determine the GLB filename
    if not model_name:
        if (VA_3D / oid / f"{oid}_textured.glb").exists():
            model_name = f"{oid}_textured.glb"
        elif (VA_3D / oid / f"{oid}.glb").exists():
            model_name = f"{oid}.glb"
        else:
            return False
    url = f"{GITHUB_RAW}/{oid}/{model_name}"
    for attempt in range(3):
        try:
            r = requests.patch(
                f"https://api.notion.com/v1/pages/{pid}",
                headers=NOTION_HDR,
                json={"properties": {
                    PROP_3D: {"files": [{
                        "type": "external",
                        "name": model_name,
                        "external": {"url": url},
                    }]},
                }},
                timeout=30,
            )
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            return r.status_code == 200
        except Exception:
            time.sleep(3)
    return False


def update_notion_batch(entries, update_fn):
    """Update Notion for a batch of entries using the given function."""
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=NOTION_WORKERS) as ex:
        futures = {ex.submit(update_fn, e): e for e in entries}
        for i, f in enumerate(as_completed(futures)):
            success = f.result()
            if success:
                ok += 1
            else:
                fail += 1
                e = futures[f]
                if fail <= 10:
                    print(f"      {e.get('oid', '?')} -> FAIL")
            if (i + 1) % 50 == 0:
                print(f"      ...updated {i+1}/{len(entries)}")
    return ok, fail


# ── Main ──
def main():
    parser = argparse.ArgumentParser(description="Audit and fix broken GitHub image URLs in Notion")
    parser.add_argument("--audit", action="store_true", help="Phase 1 only: audit and report")
    parser.add_argument("--fix", action="store_true", help="Phase 1 + Phase 2: audit and fix")
    parser.add_argument("--skip-regen", action="store_true",
                        help="Skip Gemini regeneration for entries with no local file")
    args = parser.parse_args()

    if not args.audit and not args.fix:
        parser.print_help()
        sys.exit(1)

    if not NOTION_TOKEN:
        print("ERROR: NOTION_API_KEY not in .env")
        sys.exit(1)
    if args.fix and not args.skip_regen and not GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY not set, will skip regeneration")
        args.skip_regen = True

    VA_DIR.mkdir(exist_ok=True)
    BGUW_DIR.mkdir(exist_ok=True)
    VA_3D.mkdir(exist_ok=True)

    print("=" * 60)
    print(" Broken Image URL Audit & Fix")
    print("=" * 60)

    # Query Notion
    print("\nQuerying Notion...")
    pages = query_notion()
    entries = parse_pages(pages)
    print(f"  Total entries: {len(entries)}")
    print(f"  With Bilete-bguw URL: {sum(1 for e in entries if e['bguw_url'])}")
    print(f"  With 3D-modell URL: {sum(1 for e in entries if e['model_url'])}")

    # Phase 1: Audit
    print("\n[Phase 1] Checking URLs...")
    results = audit_entries(entries)
    print_audit_report(results)
    save_audit(results, AUDIT_OUTPUT)

    if not args.fix:
        return

    # Phase 2: Fix
    bg = results["bguw"]
    md = results["model"]
    all_git_paths = []
    bguw_fixed_entries = []  # entries to update in Notion
    model_fixed_entries = []

    # 2a: bguw files already in VA_3d — just need git push
    if bg["404_has_local"]:
        print(f"\n[Phase 2a] {len(bg['404_has_local'])} bguw files already in VA_3d")
        for e in bg["404_has_local"]:
            p = f"VA_3d/{e['oid']}/{e['oid']}_bguw.png"
            if (BASE / p).exists():
                all_git_paths.append(p)
                bguw_fixed_entries.append(e)

    # 2b: bguw files in VA_bguw — copy to VA_3d
    if bg["404_has_bguw_source"]:
        print(f"\n[Phase 2b] Copying {len(bg['404_has_bguw_source'])} from VA_bguw/ to VA_3d/")
        copied = fix_bguw_copy_source(bg["404_has_bguw_source"])
        for e in bg["404_has_bguw_source"]:
            if e["oid"] in copied:
                p = f"VA_3d/{e['oid']}/{e['oid']}_bguw.png"
                all_git_paths.append(p)
                bguw_fixed_entries.append(e)
        print(f"    Copied: {len(copied)}")

    # 2c: regenerate via Gemini
    if not args.skip_regen and bg["404_no_local"]:
        print(f"\n[Phase 2c] Regenerating {len(bg['404_no_local'])} bguw via Gemini")
        regenerated = fix_bguw_regenerate(bg["404_no_local"])
        for e in bg["404_no_local"]:
            if e["oid"] in regenerated:
                p = f"VA_3d/{e['oid']}/{e['oid']}_bguw.png"
                all_git_paths.append(p)
                bguw_fixed_entries.append(e)
        print(f"    Regenerated: {len(regenerated)}")
    elif bg["404_no_local"]:
        print(f"\n[Phase 2c] Skipping {len(bg['404_no_local'])} entries (--skip-regen)")

    # 2d: 3D models already in VA_3d
    if md["404_has_local"]:
        print(f"\n[Phase 2d] {len(md['404_has_local'])} 3D models already in VA_3d")
        for e in md["404_has_local"]:
            oid = e["oid"]
            for suffix in [".glb", "_textured.glb"]:
                p = f"VA_3d/{oid}/{oid}{suffix}"
                if (BASE / p).exists():
                    all_git_paths.append(p)
            model_fixed_entries.append(e)

    if not all_git_paths:
        print("\nNo files to push!")
        return

    # Git push
    print(f"\n[Phase 2] Git pushing {len(all_git_paths)} files...")
    push_ok = git_push_files(all_git_paths)
    if push_ok:
        print(f"    Pushed successfully!")
        time.sleep(3)  # let CDN propagate
    else:
        print("    WARNING: git push failed — Notion URLs may still be broken")
        print("    You can re-run this script to retry")

    # Update Notion URLs
    if bguw_fixed_entries:
        print(f"\n[Phase 2] Updating {len(bguw_fixed_entries)} Bilete-bguw URLs in Notion...")
        ok, fail = update_notion_batch(
            bguw_fixed_entries,
            lambda e: notion_set_bguw(e["pid"], e["oid"]),
        )
        print(f"    Updated: {ok}, Failed: {fail}")

    if model_fixed_entries:
        print(f"\n[Phase 2] Updating {len(model_fixed_entries)} 3D-modell URLs in Notion...")
        ok, fail = update_notion_batch(
            model_fixed_entries,
            lambda e: notion_set_model(e["pid"], e["oid"], e.get("model_name", "")),
        )
        print(f"    Updated: {ok}, Failed: {fail}")

    # Summary
    print(f"\n{'='*60}")
    print(f" Done!")
    print(f" Bguw fixed: {len(bguw_fixed_entries)}")
    print(f" Models fixed: {len(model_fixed_entries)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
