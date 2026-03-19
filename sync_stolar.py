#!/usr/bin/env python3
"""
sync_stolar.py — Keep Notion and git repo in sync for the STOLAR database.

Usage:
  python sync_stolar.py --status              # Show sync status report
  python sync_stolar.py --sync                # Full sync (fix mismatches)
  python sync_stolar.py --sync --loop 120     # Continuous sync every 2 min
  python sync_stolar.py --migrate-urls        # Rewrite old VA_3d Notion URLs to STOLAR paths
"""

import argparse
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

# -- Config --
BASE = Path(__file__).parent
GLB_DIR = BASE / "STOLAR" / "glb"
BGUW_DIR = BASE / "STOLAR" / "bguw"

NOTION_TOKEN = ""
GH_TOKEN = ""
for line in (BASE / ".env").read_text(encoding="utf-8").splitlines():
    k, _, v = line.partition("=")
    k, v = k.strip(), v.strip().strip('"')
    if k == "NOTION_API_KEY":
        NOTION_TOKEN = v
    elif k == "PERSONAL_ACCESS_TOKEN":
        GH_TOKEN = v

DATABASE_ID = "405e0f64-6b77-4aab-88b8-73281e58c4f0"
GH_OWNER = "lukketsvane"
GH_REPO = "stolar-db"
GH_BRANCH = "main"
GITHUB_RAW_GLB = f"https://raw.githubusercontent.com/{GH_OWNER}/{GH_REPO}/{GH_BRANCH}/STOLAR/glb"
GITHUB_RAW_BGUW = f"https://raw.githubusercontent.com/{GH_OWNER}/{GH_REPO}/{GH_BRANCH}/STOLAR/bguw"

NOTION_HDR = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

WORKERS = 5


# -- Notion --
def query_notion():
    """Query all pages, return dict {oid: {pid, has_bguw, has_3d, bguw_url, model_url}}."""
    entries = {}
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
        for p in data["results"]:
            props = p["properties"]
            rt = props.get("Objekt-ID", {}).get("rich_text", [])
            oid = rt[0]["plain_text"] if rt else ""
            if not oid:
                continue

            bguw_files = props.get("Bilete-bguw", {}).get("files", [])
            bguw_url = None
            if bguw_files:
                f = bguw_files[0]
                bguw_url = f.get("external", {}).get("url") or f.get("file", {}).get("url")

            model_files = props.get("3D-modell", {}).get("files", [])
            model_url = None
            if model_files:
                f = model_files[0]
                model_url = f.get("external", {}).get("url") or f.get("file", {}).get("url")

            entries[oid] = {
                "pid": p["id"],
                "has_bguw": bool(bguw_url),
                "has_3d": bool(model_url),
                "bguw_url": bguw_url,
                "model_url": model_url,
            }
        has_more = data.get("has_more", False)
        cursor = data.get("next_cursor")
    return entries


def scan_local():
    """Scan STOLAR/glb/ and STOLAR/bguw/ for local files. Return dict {oid: {bguw, glb, textured}}."""
    local = {}
    # Scan GLBs
    if GLB_DIR.exists():
        for f in GLB_DIR.iterdir():
            if f.suffix != ".glb":
                continue
            name = f.stem
            if name.endswith("_textured"):
                oid = name.removesuffix("_textured")
                local.setdefault(oid, {"bguw": False, "glb": False, "textured": False})
                local[oid]["textured"] = True
            else:
                oid = name
                local.setdefault(oid, {"bguw": False, "glb": False, "textured": False})
                local[oid]["glb"] = True
    # Scan bguw
    if BGUW_DIR.exists():
        for f in BGUW_DIR.iterdir():
            if f.name.endswith("_bguw.png"):
                oid = f.stem.removesuffix("_bguw")
                local.setdefault(oid, {"bguw": False, "glb": False, "textured": False})
                local[oid]["bguw"] = True
    return local


def scan_untracked():
    """Find untracked files in STOLAR/ that need git add."""
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "STOLAR/"],
        cwd=str(BASE), capture_output=True, text=True,
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().split("\n")
            if f.strip() and "_prescale" not in f]


# -- Notion updates --
def set_bguw(pid, oid):
    url = f"{GITHUB_RAW_BGUW}/{oid}_bguw.png"
    for attempt in range(3):
        try:
            r = requests.patch(
                f"https://api.notion.com/v1/pages/{pid}",
                headers=NOTION_HDR,
                json={"properties": {
                    "Bilete-bguw": {"files": [{
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


def set_3d(pid, oid):
    # Prefer textured, fall back to untextured
    if (GLB_DIR / f"{oid}_textured.glb").exists():
        fname = f"{oid}_textured.glb"
    else:
        fname = f"{oid}.glb"
    url = f"{GITHUB_RAW_GLB}/{fname}"
    for attempt in range(3):
        try:
            r = requests.patch(
                f"https://api.notion.com/v1/pages/{pid}",
                headers=NOTION_HDR,
                json={"properties": {
                    "3D-modell": {"files": [{
                        "type": "external",
                        "name": fname,
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


# -- Git --
def git_push(files):
    if not files:
        return True

    lock = BASE / ".git" / "index.lock"
    if lock.exists():
        try:
            lock.unlink()
        except Exception:
            pass

    BATCH = 100
    for i in range(0, len(files), BATCH):
        subprocess.run(["git", "add"] + files[i:i+BATCH], cwd=str(BASE), capture_output=True)

    result = subprocess.run(
        ["git", "commit", "-m", f"sync: add {len(files)} files from sync_stolar"],
        cwd=str(BASE), capture_output=True, text=True,
    )
    if result.returncode != 0:
        if "nothing to commit" in (result.stdout + result.stderr):
            return True
        return False

    for attempt in range(3):
        subprocess.run(["git", "fetch", "origin", "main"], cwd=str(BASE), capture_output=True)
        subprocess.run(["git", "merge", "origin/main", "--no-edit"],
                       cwd=str(BASE), capture_output=True)
        push = subprocess.run(["git", "push"], cwd=str(BASE), capture_output=True)
        if push.returncode == 0:
            return True
        time.sleep(5)
    return False


# -- Core --
def run_sync(do_fix=False):
    ts = time.strftime("%H:%M:%S")
    print(f"\n[{ts}] Querying Notion...")
    notion = query_notion()

    print(f"[{ts}] Scanning local files...")
    local = scan_local()

    # Stats
    n_total = len(notion)
    n_bguw = sum(1 for v in notion.values() if v["has_bguw"])
    n_3d = sum(1 for v in notion.values() if v["has_3d"])
    l_bguw = sum(1 for v in local.values() if v["bguw"])
    l_glb = sum(1 for v in local.values() if v["glb"])

    # Find mismatches
    fix_bguw = []  # local bguw exists, Notion missing
    fix_3d = []    # local glb exists, Notion missing

    for oid, loc in local.items():
        n = notion.get(oid)
        if not n:
            continue
        if loc["bguw"] and not n["has_bguw"]:
            fix_bguw.append((oid, n["pid"]))
        if loc["glb"] and not n["has_3d"]:
            fix_3d.append((oid, n["pid"]))

    # Untracked files
    untracked = scan_untracked()

    # Report
    print(f"\n{'='*50}")
    print(f" STOLAR Sync Status")
    print(f"{'='*50}")
    print(f" Notion entries:          {n_total:>5}")
    print(f" Notion Bilete-bguw set:  {n_bguw:>5}")
    print(f" Notion 3D-modell set:    {n_3d:>5}")
    print(f" Local bguw files:        {l_bguw:>5}")
    print(f" Local GLB files:         {l_glb:>5}")
    print(f"{'-'*50}")
    print(f" Bguw: local but not in Notion:  {len(fix_bguw):>5}")
    print(f" GLB:  local but not in Notion:  {len(fix_3d):>5}")
    print(f" Files not in git:               {len(untracked):>5}")
    print(f"{'='*50}")

    if not do_fix:
        if fix_bguw or fix_3d or untracked:
            print("\nRun with --sync to fix these.")
        else:
            print("\nAll synced!")
        return

    if not fix_bguw and not fix_3d and not untracked:
        print("\nAll synced!")
        return

    # Fix: push untracked files first
    if untracked:
        print(f"\n  Pushing {len(untracked)} untracked files to git...")
        ok = git_push(untracked)
        print(f"  {'OK' if ok else 'FAILED'}")
        if ok:
            time.sleep(2)

    # Fix: update Notion bguw
    if fix_bguw:
        print(f"\n  Updating {len(fix_bguw)} Bilete-bguw in Notion...")
        ok = fail = 0
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {ex.submit(set_bguw, pid, oid): oid for oid, pid in fix_bguw}
            for f in as_completed(futures):
                if f.result():
                    ok += 1
                else:
                    fail += 1
        print(f"  Updated: {ok}, Failed: {fail}")

    # Fix: update Notion 3D
    if fix_3d:
        print(f"\n  Updating {len(fix_3d)} 3D-modell in Notion...")
        ok = fail = 0
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {ex.submit(set_3d, pid, oid): oid for oid, pid in fix_3d}
            for f in as_completed(futures):
                if f.result():
                    ok += 1
                else:
                    fail += 1
        print(f"  Updated: {ok}, Failed: {fail}")

    print("\nDone!")


OLD_VA3D_BASE = f"https://raw.githubusercontent.com/{GH_OWNER}/{GH_REPO}/{GH_BRANCH}/VA_3d"


def migrate_urls():
    """Rewrite all old VA_3d URLs in Notion to new STOLAR paths."""
    print("Querying Notion for URL migration...")
    notion = query_notion()

    migrate_bguw = []
    migrate_3d = []

    for oid, info in notion.items():
        if info["bguw_url"] and "/VA_3d/" in info["bguw_url"]:
            migrate_bguw.append((oid, info["pid"]))
        if info["model_url"] and "/VA_3d/" in info["model_url"]:
            migrate_3d.append((oid, info["pid"]))

    print(f"\n{'='*50}")
    print(f" URL Migration")
    print(f"{'='*50}")
    print(f" Bguw URLs to migrate (VA_3d -> STOLAR/bguw):  {len(migrate_bguw)}")
    print(f" 3D URLs to migrate (VA_3d -> STOLAR/glb):     {len(migrate_3d)}")
    print(f"{'='*50}")

    if not migrate_bguw and not migrate_3d:
        print("\nAll URLs already on new paths!")
        return

    if migrate_bguw:
        print(f"\n  Migrating {len(migrate_bguw)} Bilete-bguw URLs...")
        ok = fail = 0
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {ex.submit(set_bguw, pid, oid): oid for oid, pid in migrate_bguw}
            for f in as_completed(futures):
                if f.result():
                    ok += 1
                else:
                    fail += 1
        print(f"  Updated: {ok}, Failed: {fail}")

    if migrate_3d:
        print(f"\n  Migrating {len(migrate_3d)} 3D-modell URLs...")
        ok = fail = 0
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {ex.submit(set_3d, pid, oid): oid for oid, pid in migrate_3d}
            for f in as_completed(futures):
                if f.result():
                    ok += 1
                else:
                    fail += 1
        print(f"  Updated: {ok}, Failed: {fail}")

    print("\nMigration done!")


def main():
    parser = argparse.ArgumentParser(description="Sync STOLAR Notion database with git repo")
    parser.add_argument("--status", action="store_true", help="Show sync status (no changes)")
    parser.add_argument("--sync", action="store_true", help="Fix all mismatches")
    parser.add_argument("--migrate-urls", action="store_true", help="Rewrite old VA_3d URLs to STOLAR paths")
    parser.add_argument("--build-api", action="store_true", help="Rebuild STOLAR/api.json from CSV")
    parser.add_argument("--loop", type=int, default=0, help="Poll interval in seconds (0 = once)")
    args = parser.parse_args()

    if not args.status and not args.sync and not args.migrate_urls and not args.build_api:
        parser.print_help()
        sys.exit(1)

    if not NOTION_TOKEN:
        print("ERROR: NOTION_API_KEY not in .env")
        sys.exit(1)

    if args.migrate_urls:
        migrate_urls()
        return

    if args.build_api:
        print("Rebuilding STOLAR/api.json...")
        subprocess.run([sys.executable, str(BASE / "build_api.py"), "--from-csv"],
                       cwd=str(BASE))
        return

    if args.loop > 0 and args.sync:
        print(f"Syncing every {args.loop}s (Ctrl+C to stop)")
        while True:
            try:
                run_sync(do_fix=True)
                print(f"\n  Sleeping {args.loop}s...")
                time.sleep(args.loop)
            except KeyboardInterrupt:
                print("\nStopped.")
                break
    else:
        run_sync(do_fix=args.sync)


if __name__ == "__main__":
    main()
