#!/usr/bin/env python3
"""
fetch_va_images.py — Download chair images from V&A (Victoria and Albert Museum)
collection pages into bilete/VA/.

Reads va_entries.json (list of {objekt_id, vam_url, title}) and fetches
the main image for each at 1600px width.

Resumable: skips existing files.
"""

import json
import os
import re
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

BASE = Path(__file__).parent
VA_DIR = BASE / "bilete" / "VA"
ENTRIES_FILE = BASE / "va_entries.json"


def fetch_vam_image_url(page_url):
    """Scrape V&A collection page to find the IIIF image ID."""
    req = Request(page_url, headers={"User-Agent": "Mozilla/5.0 stolar-db/1.0"})
    html = urlopen(req, timeout=15).read().decode("utf-8")

    # V&A uses framemark.vam.ac.uk/collections/{IMAGE_ID}/full/...
    m = re.search(r'framemark\.vam\.ac\.uk/collections/([^/]+)/full/', html)
    if m:
        img_id = m.group(1)
        return f"https://framemark.vam.ac.uk/collections/{img_id}/full/1600,/0/default.jpg"

    # Fallback: look for any large image URL
    m = re.search(r'(https://framemark\.vam\.ac\.uk/collections/[^"\']+)', html)
    if m:
        base = m.group(1).split("/full/")[0]
        return f"{base}/full/1600,/0/default.jpg"

    return None


def download(url, dest, timeout=30):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 stolar-db/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return len(data)


def main():
    VA_DIR.mkdir(parents=True, exist_ok=True)

    if not ENTRIES_FILE.exists():
        print(f"No {ENTRIES_FILE} found. Create it first with entries from Notion.")
        return

    entries = json.loads(ENTRIES_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(entries)} V&A entries")

    ok = failed = skipped = 0
    for i, entry in enumerate(entries, 1):
        oid = entry.get("objekt_id", "")
        vam_url = entry.get("vam_url", "")
        title = entry.get("title", "")
        dest = VA_DIR / f"{oid}.jpg"

        if dest.exists():
            skipped += 1
            continue

        print(f"  [{i}/{len(entries)}] {oid} ({title})...", end=" ", flush=True)

        try:
            img_url = fetch_vam_image_url(vam_url)
            if not img_url:
                print("NO IMAGE FOUND")
                failed += 1
                continue

            size = download(img_url, dest)
            print(f"OK ({size // 1024} KB)")
            ok += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"FAILED: {e}")
            failed += 1

    print(f"\nDone: {ok} downloaded, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
