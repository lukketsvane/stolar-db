#!/usr/bin/env python3
"""
download_missing_images.py — Download source images for NM_stolar entries
that don't yet have a local image file.

Reads URLs from NM_stolar.json (images[].highRes) and from image_urls_resten.txt.
Saves as PNG in NM_stolar/ root (matching existing convention).
"""

import json
import os
import re
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

BASE = Path(__file__).parent
NM_DIR = BASE / "NM_stolar"
META_JSON = NM_DIR / "NM_stolar.json"
URLS_FILE = NM_DIR / "image_urls_resten.txt"


def existing_images():
    """Set of stems already present as PNG or JPG in NM_stolar/."""
    stems = set()
    for f in NM_DIR.iterdir():
        if f.suffix.lower() in (".png", ".jpg", ".jpeg"):
            stems.add(f.stem)
    return stems


def parse_url_file():
    """Parse image_urls_resten.txt → dict of stem → url."""
    urls = {}
    if not URLS_FILE.exists():
        return urls
    for line in URLS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Format: "FILENAME: URL"
        m = re.match(r'^(.+?):\s*(https?://.+)$', line)
        if m:
            fn = m.group(1).strip()
            url = m.group(2).strip()
            stem = os.path.splitext(fn)[0]
            urls[stem] = url
    return urls


def download(url, dest, timeout=30):
    """Download url to dest path."""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 stolar-db/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return len(data)


def main():
    data = json.loads(META_JSON.read_text(encoding="utf-8"))
    have = existing_images()
    print(f"Existing images: {len(have)}")

    # Build download list from JSON metadata
    to_download = []  # (stem, url, objectId)
    for entry in data:
        oid = entry.get("objectId", "")
        for img in entry.get("images", []):
            fn = img.get("filename", "")
            if not fn:
                continue
            stem = os.path.splitext(fn)[0]
            if stem in have:
                continue
            url = img.get("highRes") or img.get("fullRes") or img.get("thumbnail")
            if url:
                to_download.append((stem, url, oid))

    # Also check URL file for any extras
    url_map = parse_url_file()
    for stem, url in url_map.items():
        if stem not in have and not any(s == stem for s, _, _ in to_download):
            oid = stem.rsplit("_", 1)[0]
            to_download.append((stem, url, oid))

    # Deduplicate by stem
    seen = set()
    unique = []
    for stem, url, oid in to_download:
        if stem not in seen:
            seen.add(stem)
            unique.append((stem, url, oid))
    to_download = unique

    print(f"Need to download: {len(to_download)} images")
    if not to_download:
        print("Nothing to download.")
        return

    ok = failed = 0
    for i, (stem, url, oid) in enumerate(to_download, 1):
        dest = NM_DIR / f"{stem}.jpg"
        print(f"  [{i}/{len(to_download)}] {oid} -> {stem}...", end=" ", flush=True)
        try:
            size = download(url, dest)
            print(f"OK ({size // 1024} KB)")
            ok += 1
            # Be polite to the server
            if i < len(to_download):
                time.sleep(0.5)
        except Exception as e:
            print(f"FAILED: {e}")
            failed += 1

    print(f"\nDone: {ok} downloaded, {failed} failed")


if __name__ == "__main__":
    main()
