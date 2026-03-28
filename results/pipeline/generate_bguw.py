#!/usr/bin/env python3
"""
generate_bguw.py — Generate Bilete-bguw images and upload to GitHub + Notion.

1. Query Notion for entries missing Bilete-bguw
2. Download source images from Bilete-URL if not local
3. Generate white-background (bguw) images via Gemini
4. Upload bguw to GitHub (STOLAR/bguw/), update Notion

Single script — run it and walk away.
"""

import argparse
import base64
import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import requests
from PIL import Image

# ── Config ──
BASE = Path(__file__).parent
VA_DIR = BASE / "STOLAR" / "images"
BGUW_DIR = BASE / "STOLAR" / "bguw"

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
GITHUB_RAW_BGUW = f"https://raw.githubusercontent.com/{GH_OWNER}/{GH_REPO}/{GH_BRANCH}/STOLAR/bguw"
PROP_NAME = "Bilete-bguw"
UA = "stolar-db/1.0 (PhD research; AHO)"

NOTION_HDR = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}
GH_HDR = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

GEMINI_MODELS = {
    "nano": "gemini-2.5-flash-image",
    "nano-pro": "gemini-2.5-pro-preview-06-05",
    "nano-2": "gemini-3.1-flash-image-preview",
}
GEMINI_MODEL = GEMINI_MODELS["nano-2"]  # default, overridden by CLI args
GEMINI_PROMPT = "place it sharp against solid white background, have the subject cut sharply, and background be #fff 100% white."

DOWNLOAD_WORKERS = 40
BGUW_WORKERS = 15
UPLOAD_WORKERS = 8


# ── Notion ──
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


def parse_pages(pages):
    """Return list of dicts with oid, pid, bilete_url, has_bguw."""
    entries = []
    for p in pages:
        props = p["properties"]
        rt = props.get("Objekt-ID", {}).get("rich_text", [])
        oid = rt[0]["plain_text"] if rt else ""
        if not oid:
            continue
        bilete_url = props.get("Bilete-URL", {}).get("url") or ""
        has_bguw = bool(props.get(PROP_NAME, {}).get("files"))
        entries.append({
            "oid": oid,
            "pid": p["id"],
            "bilete_url": bilete_url,
            "has_bguw": has_bguw,
        })
    return entries


# ── Phase 1: Download source images ──
def download_image(oid, url):
    out = VA_DIR / f"{oid}.jpg"
    if out.exists():
        return oid, "exists"
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=30) as resp:
            out.write_bytes(resp.read())
        return oid, "ok"
    except HTTPError as e:
        return oid, f"HTTP {e.code}"
    except Exception as e:
        return oid, str(e)[:60]


def phase1_download(entries):
    """Download source images for entries that need bguw but have no local image."""
    targets = [
        (e["oid"], e["bilete_url"])
        for e in entries
        if not e["has_bguw"]
        and e["bilete_url"]
        and not (VA_DIR / f"{e['oid']}.jpg").exists()
        and not (VA_DIR / f"{e['oid']}.png").exists()
    ]
    if not targets:
        print("[Phase 1] All source images present locally.")
        return

    print(f"[Phase 1] Downloading {len(targets)} source images ({DOWNLOAD_WORKERS} workers)...")
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as ex:
        futures = {ex.submit(download_image, oid, url): oid for oid, url in targets}
        for i, f in enumerate(as_completed(futures)):
            oid, status = f.result()
            if status in ("ok", "exists"):
                ok += 1
            else:
                fail += 1
                if (i + 1) <= 10 or fail <= 5:
                    print(f"  {oid} FAIL: {status}")
    print(f"  Downloaded: {ok}, Failed: {fail}")


# ── Phase 2: Generate bguw via Gemini ──
def generate_bguw_single(oid, img_path, out_path, client):
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


def phase2_generate(entries, client):
    """Generate bguw for entries missing it."""
    need = []
    for e in entries:
        if e["has_bguw"]:
            continue
        oid = e["oid"]
        bguw_path = BGUW_DIR / f"{oid}_bguw.png"
        if bguw_path.exists():
            continue
        # Find source image
        src = VA_DIR / f"{oid}.jpg"
        if not src.exists():
            src = VA_DIR / f"{oid}.png"
        if not src.exists():
            continue
        need.append((oid, src, bguw_path))

    if not need:
        print("[Phase 2] All bguw images generated.")
        return []

    print(f"[Phase 2] Generating {len(need)} bguw images ({BGUW_WORKERS} workers)...")
    generated = []
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=BGUW_WORKERS) as ex:
        futures = {
            ex.submit(generate_bguw_single, oid, src, out, client): oid
            for oid, src, out in need
        }
        for i, f in enumerate(as_completed(futures)):
            oid, status = f.result()
            if status == "ok":
                ok += 1
                generated.append(oid)
                print(f"  [{ok}/{len(need)}] {oid} bguw generated")
            elif status == "exists":
                ok += 1
                generated.append(oid)
            else:
                fail += 1
                print(f"  [{i+1}/{len(need)}] {oid} FAIL: {status}")
    print(f"  Generated: {ok}, Failed: {fail}")
    return generated


# ── Phase 3: Upload to GitHub + Notion ──
def gh_upload(local_path, oid):
    gh_path = f"STOLAR/bguw/{oid}_bguw.png"
    content_b64 = base64.b64encode(local_path.read_bytes()).decode()

    sha = None
    r_check = requests.get(
        f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/contents/{gh_path}",
        headers=GH_HDR, params={"ref": GH_BRANCH}, timeout=10,
    )
    if r_check.status_code == 200:
        sha = r_check.json().get("sha")

    body = {
        "message": f"feat: add bguw for {oid}",
        "content": content_b64,
        "branch": GH_BRANCH,
    }
    if sha:
        body["sha"] = sha

    for attempt in range(3):
        r = requests.put(
            f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/contents/{gh_path}",
            headers=GH_HDR, json=body, timeout=30,
        )
        if r.status_code in (200, 201):
            return True
        if r.status_code == 429:
            time.sleep(20)
            continue
        return False
    return False


def notion_set_bguw(pid, oid):
    url = f"{GITHUB_RAW_BGUW}/{oid}_bguw.png"
    for attempt in range(3):
        try:
            r = requests.patch(
                f"https://api.notion.com/v1/pages/{pid}",
                headers=NOTION_HDR,
                json={"properties": {
                    PROP_NAME: {"files": [{
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


def phase3_upload(entries):
    """Upload bguw to GitHub + set in Notion for all entries that have a local bguw but not in Notion."""
    pid_map = {e["oid"]: e["pid"] for e in entries}
    targets = []
    for e in entries:
        if e["has_bguw"]:
            continue
        oid = e["oid"]
        bguw = BGUW_DIR / f"{oid}_bguw.png"
        if not bguw.exists():
            continue
        targets.append((oid, bguw, pid_map[oid]))

    if not targets:
        print("[Phase 3] All bguw uploaded to Notion.")
        return

    print(f"[Phase 3] Uploading {len(targets)} bguw to GitHub + Notion ({UPLOAD_WORKERS} workers)...")

    def handle(oid, local_path, pid):
        ok_gh = gh_upload(local_path, oid)
        if not ok_gh:
            return oid, False, "github_fail"

        ok_n = notion_set_bguw(pid, oid)
        return oid, ok_n, "ok" if ok_n else "notion_fail"

    ok = fail = 0
    with ThreadPoolExecutor(max_workers=UPLOAD_WORKERS) as ex:
        futures = {ex.submit(handle, oid, path, pid): oid for oid, path, pid in targets}
        for i, f in enumerate(as_completed(futures)):
            oid, success, status = f.result()
            if success:
                ok += 1
                if ok <= 20 or (i + 1) % 50 == 0:
                    print(f"  [{i+1}/{len(targets)}] {oid} -> OK")
            else:
                fail += 1
                print(f"  [{i+1}/{len(targets)}] {oid} -> {status}")
    print(f"  Uploaded: {ok}, Failed: {fail}")


# ── Main ──
def main():
    global GEMINI_MODEL

    parser = argparse.ArgumentParser(description="Generate Bilete-bguw images via Gemini")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--nano", action="store_const", dest="model", const="nano",
                       help="Use gemini-2.5-flash-image")
    group.add_argument("--nano-pro", action="store_const", dest="model", const="nano-pro",
                       help="Use gemini-2.5-pro-preview-06-05")
    group.add_argument("--nano-2", action="store_const", dest="model", const="nano-2",
                       help="Use gemini-3.1-flash-image-preview (default)")
    parser.set_defaults(model="nano-2")
    args = parser.parse_args()

    GEMINI_MODEL = GEMINI_MODELS[args.model]
    print(f"Using model: {GEMINI_MODEL}")

    if not NOTION_TOKEN:
        print("ERROR: NOTION_API_KEY not in .env")
        sys.exit(1)
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not in .env")
        sys.exit(1)
    if not GH_TOKEN:
        print("ERROR: PERSONAL_ACCESS_TOKEN not in .env")
        sys.exit(1)

    VA_DIR.mkdir(parents=True, exist_ok=True)
    BGUW_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(" Bilete-bguw Pipeline")
    print(" Download -> Gemini bguw -> GitHub + Notion")
    print("=" * 60)

    # Query Notion
    print("\nQuerying Notion...")
    pages = query_notion()
    entries = parse_pages(pages)
    missing = sum(1 for e in entries if not e["has_bguw"])
    print(f"  Total entries: {len(entries)}")
    print(f"  Missing Bilete-bguw: {missing}")

    if missing == 0:
        print("\nAll entries have Bilete-bguw. Nothing to do.")
        return

    # Phase 1: Download source images
    phase1_download(entries)

    # Phase 2: Generate bguw via Gemini
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)
    phase2_generate(entries, client)

    # Phase 3: Upload to GitHub + Notion
    phase3_upload(entries)

    # Summary
    print(f"\n{'='*60}")
    print(f" Done!")
    total_bguw = len(list(BGUW_DIR.glob("*_bguw.png")))
    print(f" Total bguw images: {total_bguw}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
