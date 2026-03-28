#!/usr/bin/env python3
"""
build_api.py — Build STOLAR/api.json from Notion database.

This generates the public JSON API that websites can consume directly:
  https://raw.githubusercontent.com/lukketsvane/stolar-db/main/STOLAR/api.json

Usage:
  python build_api.py              # Build from Notion (live query)
  python build_api.py --from-csv   # Build from stolar_db.csv (offline/fast)
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import requests

BASE = Path(__file__).parent
OUT_FILE = BASE / "STOLAR" / "api.json"

# -- Config --
NOTION_TOKEN = ""
env_file = BASE / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"')
        if k == "NOTION_API_KEY":
            NOTION_TOKEN = v

DATABASE_ID = "405e0f64-6b77-4aab-88b8-73281e58c4f0"
GH_OWNER = "lukketsvane"
GH_REPO = "stolar-db"
GH_BRANCH = "main"
GH_RAW = f"https://raw.githubusercontent.com/{GH_OWNER}/{GH_REPO}/{GH_BRANCH}"

NOTION_HDR = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# Notion property name -> JSON key mapping
PROP_MAP = {
    "Namn": ("name", "title"),
    "Objekt-ID": ("id", "rich_text"),
    "Nemning": ("type", "rich_text"),
    "Datering": ("dating", "rich_text"),
    "Frå år": ("year_from", "number"),
    "Til år": ("year_to", "number"),
    "Hundreår": ("century", "rich_text"),
    "Stilperiode": ("style", "rich_text"),
    "Produsent": ("designer", "rich_text"),
    "Produksjonsstad": ("origin", "rich_text"),
    "Nasjonalitet": ("nationality", "rich_text"),
    "Materialar": ("materials", "rich_text"),
    "Materialkommentar": ("materials_desc", "rich_text"),
    "Teknikk": ("technique", "rich_text"),
    "Emneord": ("keywords", "rich_text"),
    "Høgde (cm)": ("height_cm", "number"),
    "Breidde (cm)": ("width_cm", "number"),
    "Djupn (cm)": ("depth_cm", "number"),
    "Setehøgde (cm)": ("seat_height_cm", "number"),
    "Estimert vekt (kg)": ("weight_kg", "number"),
    "Erverving": ("acquisition", "rich_text"),
    "Nasjonalmuseet": ("museum_url", "url"),
    "Bilete-URL": ("source_image_url", "url"),
}


def extract_prop(props, notion_key, json_key, prop_type):
    prop = props.get(notion_key, {})
    if prop_type == "title":
        titles = prop.get("title", [])
        return titles[0]["plain_text"] if titles else ""
    elif prop_type == "rich_text":
        rt = prop.get("rich_text", [])
        return rt[0]["plain_text"] if rt else ""
    elif prop_type == "number":
        return prop.get("number")
    elif prop_type == "url":
        return prop.get("url") or ""
    return ""


def query_notion_full():
    """Query all pages with full properties."""
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


def build_from_notion():
    """Build API JSON from live Notion query."""
    print("Querying Notion...")
    pages = query_notion_full()
    print(f"  {len(pages)} pages fetched")

    # Scan local files
    glb_dir = BASE / "STOLAR" / "glb"
    bguw_dir = BASE / "STOLAR" / "bguw"
    local_glbs = {f.stem for f in glb_dir.glob("*.glb")} if glb_dir.exists() else set()
    local_bguw = {f.stem.removesuffix("_bguw") for f in bguw_dir.glob("*_bguw.png")} if bguw_dir.exists() else set()

    chairs = []
    for p in pages:
        props = p["properties"]
        chair = {}

        # Extract all mapped properties
        for notion_key, (json_key, prop_type) in PROP_MAP.items():
            val = extract_prop(props, notion_key, json_key, prop_type)
            if val is not None and val != "":
                chair[json_key] = val

        oid = chair.get("id", "")
        if not oid:
            continue

        # Asset URLs
        if oid in local_glbs:
            chair["glb_url"] = f"{GH_RAW}/STOLAR/glb/{oid}.glb"
        elif f"{oid}_textured" in local_glbs:
            chair["glb_url"] = f"{GH_RAW}/STOLAR/glb/{oid}_textured.glb"

        if oid in local_bguw:
            chair["bguw_url"] = f"{GH_RAW}/STOLAR/bguw/{oid}_bguw.png"

        chairs.append(chair)

    return chairs


def build_from_csv():
    """Build API JSON from stolar_db.csv (fast, offline)."""
    csv_path = BASE / "stolar_db.csv"
    if not csv_path.exists():
        print("ERROR: stolar_db.csv not found")
        sys.exit(1)

    # Scan local files
    glb_dir = BASE / "STOLAR" / "glb"
    bguw_dir = BASE / "STOLAR" / "bguw"
    local_glbs = {f.stem for f in glb_dir.glob("*.glb")} if glb_dir.exists() else set()
    local_bguw = {f.stem.removesuffix("_bguw") for f in bguw_dir.glob("*_bguw.png")} if bguw_dir.exists() else set()

    CSV_MAP = {
        "Namn": "name",
        "Objekt-ID": "id",
        "Nemning": "type",
        "Datering": "dating",
        "Frå år": "year_from",
        "Til år": "year_to",
        "Hundreår": "century",
        "Stilperiode": "style",
        "Produsent": "designer",
        "Produksjonsstad": "origin",
        "Nasjonalitet": "nationality",
        "Materialar": "materials",
        "Materialkommentar": "materials_desc",
        "Teknikk": "technique",
        "Emneord": "keywords",
        "Høgde (cm)": "height_cm",
        "Breidde (cm)": "width_cm",
        "Djupn (cm)": "depth_cm",
        "Setehøgde (cm)": "seat_height_cm",
        "Estimert vekt (kg)": "weight_kg",
        "Erverving": "acquisition",
        "Nasjonalmuseet": "museum_url",
        "Bilete-URL": "source_image_url",
    }
    NUMERIC = {"year_from", "year_to", "height_cm", "width_cm", "depth_cm", "seat_height_cm", "weight_kg"}

    chairs = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chair = {}
            for csv_key, json_key in CSV_MAP.items():
                val = row.get(csv_key, "").strip()
                if not val:
                    continue
                if json_key in NUMERIC:
                    try:
                        chair[json_key] = float(val.replace(",", "."))
                    except ValueError:
                        chair[json_key] = val
                else:
                    chair[json_key] = val

            oid = chair.get("id", "")
            if not oid:
                continue

            if oid in local_glbs:
                chair["glb_url"] = f"{GH_RAW}/STOLAR/glb/{oid}.glb"
            elif f"{oid}_textured" in local_glbs:
                chair["glb_url"] = f"{GH_RAW}/STOLAR/glb/{oid}_textured.glb"

            if oid in local_bguw:
                chair["bguw_url"] = f"{GH_RAW}/STOLAR/bguw/{oid}_bguw.png"

            chairs.append(chair)

    return chairs


def main():
    parser = argparse.ArgumentParser(description="Build STOLAR/api.json")
    parser.add_argument("--from-csv", action="store_true", help="Build from CSV instead of Notion")
    args = parser.parse_args()

    if args.from_csv:
        print("Building from stolar_db.csv...")
        chairs = build_from_csv()
    else:
        if not NOTION_TOKEN:
            print("No NOTION_API_KEY — falling back to CSV")
            chairs = build_from_csv()
        else:
            chairs = build_from_notion()

    # Sort by ID
    chairs.sort(key=lambda c: c.get("id", ""))

    # Stats
    with_glb = sum(1 for c in chairs if "glb_url" in c)
    with_bguw = sum(1 for c in chairs if "bguw_url" in c)

    api = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total": len(chairs),
        "with_3d": with_glb,
        "with_bguw": with_bguw,
        "base_url": GH_RAW,
        "chairs": chairs,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(api, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nWrote {OUT_FILE}")
    print(f"  Total chairs: {len(chairs)}")
    print(f"  With 3D model: {with_glb}")
    print(f"  With bguw image: {with_bguw}")


if __name__ == "__main__":
    main()
