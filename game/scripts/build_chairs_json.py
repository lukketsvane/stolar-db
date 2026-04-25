"""Build chairs.json for the game from STOLAR.csv + iter27 embedding.

Output: game/public/chairs.json (one row per chair with valid bguw + year + dims).
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CSV = REPO / "STOLAR" / "STOLAR.csv"
EMB = REPO / "writings" / "figures" / "formlaere" / "iter27_embedding.npz"
BGUW_DIR = REPO / "STOLAR" / "bguw"
OUT = REPO / "game" / "public" / "chairs.json"


def parse_year(row) -> int | None:
    fra, til = row.get("Frå år"), row.get("Til år")
    if pd.notna(fra) and pd.notna(til):
        return int(round((float(fra) + float(til)) / 2))
    if pd.notna(fra):
        return int(round(float(fra)))
    if pd.notna(til):
        return int(round(float(til)))
    return None


def material_bucket(s: str | float) -> str:
    if not isinstance(s, str):
        return "ukjent"
    s = s.lower()
    has_metall = any(t in s for t in ("stål", "jern", "metall", "messing", "krom", "aluminium"))
    has_tre = any(t in s for t in ("bøk", "eik", "tre", "furu", "lønn", "ask", "kryssfiner", "valnøtt", "mahogni", "teak", "rosenved", "lerk", "platan", "bambus", "rottin"))
    has_plast = any(t in s for t in ("plast", "polyester", "polyuretan", "polypropen", "akryl", "plexi", "fiberg"))
    has_lær = any(t in s for t in ("lær", "skinn"))
    has_tekstil = any(t in s for t in ("ull", "bomull", "silke", "lin", "tekstil", "ty", "filt", "fløyel"))
    if has_metall and not has_tre:
        return "metall"
    if has_plast and not has_tre:
        return "plast"
    if has_tre:
        return "tre"
    if has_lær:
        return "lær"
    if has_tekstil:
        return "tekstil"
    return "anna"


def style_bucket(s: str | float) -> str:
    if not isinstance(s, str):
        return "ukjent"
    s = s.strip()
    return s.split(" / ")[0].split(",")[0].strip() or "ukjent"


def main():
    df = pd.read_csv(CSV)
    print(f"loaded {len(df)} rows")

    # embedding lookup
    emb = np.load(EMB, allow_pickle=True)
    emb_coords = emb["coords"]  # (N, 3)
    emb_ids = emb["ids"].astype(str)
    emb_map = {oid: emb_coords[i].tolist() for i, oid in enumerate(emb_ids)}
    print(f"embedding for {len(emb_map)} chairs")

    rows = []
    skipped = 0
    for _, r in df.iterrows():
        oid = str(r["Objekt-ID"]).strip()
        if not oid or oid == "nan":
            skipped += 1; continue
        bguw = BGUW_DIR / f"{oid}_bguw.png"
        if not bguw.exists():
            skipped += 1; continue
        year = parse_year(r)
        if year is None or year < 1500 or year > 2025:
            skipped += 1; continue
        h = r.get("Høgde (cm)"); w = r.get("Breidde (cm)"); d = r.get("Djupn (cm)")
        sh = r.get("Setehøgde (cm)")
        if pd.isna(h) or pd.isna(w) or pd.isna(d):
            skipped += 1; continue
        rows.append({
            "id": oid,
            "namn": r.get("Namn") if isinstance(r.get("Namn"), str) else "Stol",
            "year": year,
            "h": float(h),
            "w": float(w),
            "d": float(d),
            "sh": float(sh) if pd.notna(sh) else None,
            "mat": material_bucket(r.get("Materialar")),
            "stil": style_bucket(r.get("Stilperiode")),
            "nat": r.get("Nasjonalitet") if isinstance(r.get("Nasjonalitet"), str) else None,
            "arm": bool(r["har_armlene"]) if pd.notna(r.get("har_armlene")) else None,
            "pad": bool(r["har_polstring"]) if pd.notna(r.get("har_polstring")) else None,
            "rygg": r.get("rygg_type") if isinstance(r.get("rygg_type"), str) else None,
            "bein": int(r["tal_bein"]) if pd.notna(r.get("tal_bein")) else None,
            "emb": emb_map.get(oid),
        })

    print(f"kept {len(rows)} chairs, skipped {skipped}")

    # quality breakdowns
    by_year = pd.Series([r["year"] for r in rows])
    print(f"year range: {by_year.min()} – {by_year.max()}, median {int(by_year.median())}")
    n_emb = sum(1 for r in rows if r["emb"] is not None)
    print(f"with embedding: {n_emb} ({n_emb/len(rows)*100:.0f}%)")
    mats = pd.Series([r["mat"] for r in rows]).value_counts()
    print("materials:", dict(mats))
    stils = pd.Series([r["stil"] for r in rows]).value_counts().head(10)
    print("top styles:", dict(stils))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
