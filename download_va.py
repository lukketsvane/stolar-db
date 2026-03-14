"""Download all bilde_url images from norske_stolar.csv to VA/ folder."""

import csv
import os
import requests
import time
import sys

CSV_PATH = os.path.join(os.path.dirname(__file__), "norske_stolar.csv")
OUT_DIR = os.path.join(os.path.dirname(__file__), "VA")

os.makedirs(OUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "stolar-db/1.0 (PhD research; AHO)"
})

downloaded = 0
skipped = 0
errors = 0

with open(CSV_PATH, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=";")
    for row in reader:
        object_id = row["object_id"]
        raw = row.get("bilde_url", "")
        if not raw:
            continue
        urls = [u.strip() for u in raw.split("; ") if u.strip()]
        for i, url in enumerate(urls):
            suffix = f"_{i+1}" if len(urls) > 1 else ""
            filename = f"{object_id}{suffix}.jpg"
            filepath = os.path.join(OUT_DIR, filename)

            if os.path.exists(filepath):
                skipped += 1
                continue

            try:
                r = session.get(url, timeout=30)
                r.raise_for_status()
                with open(filepath, "wb") as out:
                    out.write(r.content)
                downloaded += 1
                print(f"[{downloaded}] {filename} ({len(r.content)//1024} KB)")
            except Exception as e:
                errors += 1
                print(f"ERROR {filename}: {e}", file=sys.stderr)

            time.sleep(0.3)

print(f"\nDone. Downloaded: {downloaded}, Skipped: {skipped}, Errors: {errors}")
