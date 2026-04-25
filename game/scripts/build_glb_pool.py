"""Pick the smallest viable GLB files for game pickups.

Output: game/public/glb_pool.json with [{id, namn, year, mat, stil, nat, glbBytes}, ...]
Selection: GLBs ≤ MAX_BYTES, valid chair metadata, distributed across years.
"""
from __future__ import annotations
from pathlib import Path
import json
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
GLB_DIR = REPO / "STOLAR" / "glb"
CSV = REPO / "STOLAR" / "STOLAR.csv"
OUT = REPO / "game" / "public" / "glb_pool.json"
MAX_BYTES = 7_500_000   # ~7.5 MB cap per file (still loadable)
TARGET_COUNT = 40


def main() -> None:
    df = pd.read_csv(CSV)
    rows = []
    for _, r in df.iterrows():
        oid = str(r["Objekt-ID"]).strip()
        if not oid or oid == "nan":
            continue
        glb = GLB_DIR / f"{oid}.glb"
        if not glb.exists():
            continue
        size = glb.stat().st_size
        if size <= 0 or size > MAX_BYTES:
            continue
        fra, til = r.get("Frå år"), r.get("Til år")
        if pd.isna(fra) and pd.isna(til):
            continue
        year = int(round(((float(fra) if pd.notna(fra) else float(til)) +
                          (float(til) if pd.notna(til) else float(fra))) / 2))
        if year < 1500 or year > 2025:
            continue
        rows.append({
            "id": oid,
            "namn": r.get("Namn") if isinstance(r.get("Namn"), str) else "Stol",
            "year": year,
            "mat": material_bucket(r.get("Materialar")),
            "stil": str(r.get("Stilperiode") or "ukjent").split(" / ")[0].split(",")[0].strip() or "ukjent",
            "nat": r.get("Nasjonalitet") if isinstance(r.get("Nasjonalitet"), str) else None,
            "glbBytes": size,
        })

    print(f"candidate count under {MAX_BYTES/1024:.0f}KB: {len(rows)}")
    rows.sort(key=lambda x: x["glbBytes"])
    rows = rows[:TARGET_COUNT]

    # Print stats
    by_year = pd.Series([r["year"] for r in rows])
    print(f"selected {len(rows)} chairs, year range {by_year.min()} – {by_year.max()}")
    print("years:", sorted({r["year"] // 50 * 50 for r in rows}))
    print("mats:", dict(pd.Series([r["mat"] for r in rows]).value_counts()))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
    total_mb = sum(r["glbBytes"] for r in rows) / (1024 * 1024)
    print(f"wrote {OUT} ({total_mb:.1f} MB total payload if all loaded)")


def material_bucket(s) -> str:
    if not isinstance(s, str): return "ukjent"
    s = s.lower()
    if any(t in s for t in ("stål", "jern", "metall", "messing", "krom")): return "metall"
    if any(t in s for t in ("plast", "polyester", "polyuretan", "polypropen")): return "plast"
    if any(t in s for t in ("bøk", "eik", "tre", "furu", "lønn", "ask", "kryssfiner", "valnøtt", "mahogni", "teak")): return "tre"
    if any(t in s for t in ("lær", "skinn")): return "lær"
    if any(t in s for t in ("ull", "bomull", "silke", "lin", "tekstil", "ty", "filt")): return "tekstil"
    return "anna"


if __name__ == "__main__":
    main()
