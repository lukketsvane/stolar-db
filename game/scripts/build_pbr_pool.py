"""Build pbr_pool.json from STOLAR/pbr_textured/ + manual metadata.

Each entry has:
  id, namn, year, mat, stil, nat, glbPath
where `glbPath` is the URL-path the client uses to fetch the GLB.
"""
from __future__ import annotations
from pathlib import Path
import json

REPO = Path(__file__).resolve().parents[2]
PBR_DIR = REPO / "STOLAR" / "pbr_textured"
OUT = REPO / "game" / "public" / "pbr_pool.json"

# Manual metadata for the curated PBR chairs. Year/mat/stil/nat decide what
# targets they match against.
META = {
    "Red_and_blue": {
        "namn": "Red and Blue", "year": 1918, "mat": "tre",
        "stil": "Modernisme", "nat": "Nederland",
    },
    "heltre": {
        "namn": "Heltre", "year": 1960, "mat": "tre",
        "stil": "Modernisme", "nat": "Noreg",
    },
    "lekker": {
        "namn": "Lekker", "year": 1955, "mat": "tre",
        "stil": "Modernisme", "nat": "Sverige",
    },
    "opsvik": {
        "namn": "Variable Balans", "year": 1979, "mat": "tre",
        "stil": "Modernisme", "nat": "Noreg",
    },
    "terje_ekstrom_1977": {
        "namn": "Ekstrem 1977", "year": 1977, "mat": "tekstil",
        "stil": "Modernisme", "nat": "Noreg",
    },
    "terje_ekstrom_1989": {
        "namn": "Ekstrem 1989", "year": 1989, "mat": "tekstil",
        "stil": "Postmodernisme", "nat": "Noreg",
    },
    # basic_NN are generic chair scans — spread them across eras/nats so
    # targets work. Order matters: 01→11 = 1700→2020 in even steps.
    "basic_01": {"namn": "Stol 01", "year": 1720, "mat": "tre",     "stil": "Barokk",         "nat": "Frankrike"},
    "basic_02": {"namn": "Stol 02", "year": 1780, "mat": "tre",     "stil": "Nyklassisisme",  "nat": "England"},
    "basic_03": {"namn": "Stol 03", "year": 1830, "mat": "tre",     "stil": "Empire",         "nat": "Frankrike"},
    "basic_04": {"namn": "Stol 04", "year": 1870, "mat": "tre",     "stil": "Historisme",     "nat": "Tyskland"},
    "basic_05": {"namn": "Stol 05", "year": 1905, "mat": "tre",     "stil": "Historisme",     "nat": "Sverige"},
    "basic_06": {"namn": "Stol 06", "year": 1935, "mat": "metall",  "stil": "Modernisme",     "nat": "Tyskland"},
    "basic_07": {"namn": "Stol 07", "year": 1955, "mat": "tre",     "stil": "Modernisme",     "nat": "Danmark"},
    "basic_08": {"namn": "Stol 08", "year": 1965, "mat": "tre",     "stil": "Modernisme",     "nat": "Italia"},
    "basic_09": {"namn": "Stol 09", "year": 1985, "mat": "metall",  "stil": "Postmodernisme", "nat": "Italia"},
    "basic_10": {"namn": "Stol 10", "year": 2000, "mat": "plast",   "stil": "Postmodernisme", "nat": "Sverige"},
    "basic_11": {"namn": "Stol 11", "year": 2018, "mat": "plast",   "stil": "Samtidsdesign",  "nat": "Noreg"},
}


def main() -> None:
    rows = []
    for f in sorted(PBR_DIR.glob("*.glb")):
        stem = f.stem
        meta = META.get(stem)
        if not meta:
            print(f"  {stem}: no metadata defined; skipping (add to META in build_pbr_pool.py)")
            continue
        rows.append({
            "id": stem,
            "namn": meta["namn"],
            "year": meta["year"],
            "mat": meta["mat"],
            "stil": meta["stil"],
            "nat": meta["nat"],
            "glbPath": f"/pbr/{f.name}",
            "glbBytes": f.stat().st_size,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    total_mb = sum(r["glbBytes"] for r in rows) / (1024 * 1024)
    print(f"wrote {OUT} ({len(rows)} chairs, {total_mb:.1f} MB total payload)")
    for r in rows:
        print(f"  {r['id']}: {r['namn']} ({r['year']}, {r['stil']}, {r['nat']})")


if __name__ == "__main__":
    main()
