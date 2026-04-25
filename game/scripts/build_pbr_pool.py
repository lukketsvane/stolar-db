"""Build pbr_pool.json from game/public/pbr_textured/ + auto-metadata."""
from __future__ import annotations
from pathlib import Path
import json
import re

REPO = Path(__file__).resolve().parents[2]
PBR_DIR = REPO / "game" / "public" / "pbr_textured"
OUT = REPO / "game" / "public" / "pbr_pool.json"

STIL_OPTIONS = ['Barokk', 'Rokokko', 'Nyklassisisme', 'Empire', 'Modernisme', 'Postmodernisme', 'Historisme', 'Samtidsdesign']
NAT_OPTIONS = ['Noreg', 'Sverige', 'Danmark', 'Tyskland', 'England', 'Frankrike', 'Italia', 'Nederland']

NN_WORDS = {
    "antique": "Antikk",
    "baroque": "Barokk",
    "blue": "Blå",
    "chair": "stol",
    "chest": "Kiste",
    "curved": "Bogen",
    "ergonomic": "Ergonomisk",
    "fabric": "Tekstil",
    "geometric": "Geometrisk",
    "green": "Grøn",
    "high": "Høg",
    "lounge": "Lenestol",
    "metal": "Metall",
    "model": "",
    "modern": "Moderne",
    "office": "Kontor",
    "orange": "Oransje",
    "ornate": "Utskoren",
    "painted": "Måla",
    "pink": "Rosa",
    "plastic": "Plast",
    "red": "Raud",
    "rocking": "Gyngestol",
    "rope": "Tau",
    "simple": "Enkel",
    "slatted": "Spilekledd",
    "spiral": "Spiral",
    "stool": "Krakk",
    "throne": "Trone",
    "v1": "I", "v2": "II", "v3": "III", "v4": "IV", "v5": "V",
    "woven": "Fletta",
    "wooden": "Tre",
    "chain": "Kjeda",
    "3d": "",
}

def nn_name(stem: str) -> str:
    cleaned = stem.replace("+chair+3d+model", "").replace("+3d+model", "")
    parts = re.split(r"[+_\s]+", cleaned)
    out = []
    for p in parts:
        key = p.lower()
        if not key:
            continue
        if key in NN_WORDS:
            w = NN_WORDS[key]
            if w:
                out.append(w)
        else:
            out.append(p.capitalize())
    if not out:
        return stem
    name = " ".join(out)
    # Numeric-only or single-token cryptic IDs become "Stol N"
    if re.fullmatch(r"\d+", name) or re.fullmatch(r"[Cc]\d+", name):
        return f"Stol {name.upper()}"
    return name

MAX_CHAIRS = 17  # cap to avoid WebGL context loss on heavy scenes
MAX_BYTES_PER_CHAIR = 8 * 1024 * 1024  # skip files larger than 8 MB to keep load light

def main() -> None:
    rows = []
    all_files = sorted(list(PBR_DIR.glob("*.glb")))
    eligible = [f for f in all_files if f.stat().st_size <= MAX_BYTES_PER_CHAIR]
    files = sorted(eligible, key=lambda p: p.stat().st_size)[:MAX_CHAIRS]
    files.sort()
    for i, f in enumerate(files):
        stem = f.stem

        year = 1700 + (i * 10)
        mat = "tre"
        stil = STIL_OPTIONS[i % len(STIL_OPTIONS)]
        nat = NAT_OPTIONS[i % len(NAT_OPTIONS)]
        namn = nn_name(stem)

        if "metal" in stem or "steel" in stem or "krom" in stem:
            mat = "metall"
        elif "plastic" in stem or "pink" in stem or "orange" in stem:
            mat = "plast"
        elif "textile" in stem or "leather" in stem or "painted" in stem or "fabric" in stem:
            mat = "tekstil"

        if "modern" in stem or "ergonomic" in stem or "office" in stem:
            stil = "Modernisme"
            year = max(year, 1950)
        elif "chest" in stem:
            stil = "Historisme"
            year = 1880
        elif "baroque" in stem or "antique" in stem or "ornate" in stem or "throne" in stem:
            stil = "Barokk"
            year = min(year, 1750)
        elif "rocking" in stem or "rope" in stem or "woven" in stem:
            stil = "Historisme"
        elif "geometric" in stem or "spiral" in stem:
            stil = "Postmodernisme"
            year = max(year, 1980)

        rows.append({
            "id": stem,
            "namn": namn,
            "year": year,
            "mat": mat,
            "stil": stil,
            "nat": nat,
            "glbPath": f"/pbr_textured/{f.name}",
            "glbBytes": f.stat().st_size,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    total_mb = sum(r["glbBytes"] for r in rows) / (1024 * 1024)
    print(f"wrote {OUT} ({len(rows)} chairs, {total_mb:.1f} MB total payload)")


if __name__ == "__main__":
    main()
