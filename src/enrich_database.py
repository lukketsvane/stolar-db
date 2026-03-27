#!/usr/bin/env python3
"""
enrich_database.py - Fyll inn tomme Stilperiode- og Nemning-felt i stolar_db.csv.

Les stolar_db.csv, klassifiser manglande verdiar basert paa eksisterande felt,
og skriv resultatet til stolar_db_enriched.csv.

REGEL: Aldri dikt opp data. Berre klassifiser basert paa bevis i eksisterande felt.
"""

import csv
import re
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_CSV = BASE_DIR / "stolar_db.csv"
OUTPUT_CSV = BASE_DIR / "stolar_db_enriched.csv"

# ---------------------------------------------------------------------------
# Designer -> Stilperiode overrides
# ---------------------------------------------------------------------------
# Keys are lowercased substrings to match against the Produsent field.
DESIGNER_OVERRIDES = {
    # Wiener bentwood / Historisme
    "thonet": "Wiener bentwood / Historisme",
    "gebrüder thonet": "Wiener bentwood / Historisme",
    # Modernisme
    "le corbusier": "Modernisme",
    "perriand": "Modernisme",
    # Midtjahrhundre modernisme
    "eames": "Midtjahrhundre modernisme",
    "saarinen": "Midtjahrhundre modernisme",
    # Skandinavisk modernisme
    "wegner": "Skandinavisk modernisme",
    "jacobsen": "Skandinavisk modernisme",
    "finn juhl": "Skandinavisk modernisme",
    "juhl, finn": "Skandinavisk modernisme",
    "mogensen": "Skandinavisk modernisme",
    # Nordisk funksjonalisme
    "aalto": "Nordisk funksjonalisme",
    "alvar aalto": "Nordisk funksjonalisme",
    # Bauhaus
    "breuer": "Bauhaus",
    "mies van der rohe": "Bauhaus",
    "mart stam": "Bauhaus",
    "stam, mart": "Bauhaus",
    # Pop / Plastisk modernisme
    "panton": "Pop / Plastisk modernisme",
    "colombo": "Pop / Plastisk modernisme",
    # Postmodernisme
    "starck": "Postmodernisme",
    "arad, ron": "Postmodernisme",
    "ron arad": "Postmodernisme",
    # Memphis / Postmodernisme
    "sottsass": "Memphis / Postmodernisme",
    "mendini": "Memphis / Postmodernisme",
    # Arts and Crafts
    "william morris": "Arts and Crafts",
    "morris & co": "Arts and Crafts",
    "morris & company": "Arts and Crafts",
    # Arts and Crafts / American Craftsman
    "gustav stickley": "Arts and Crafts / American Craftsman",
    "stickley": "Arts and Crafts / American Craftsman",
    # Chippendale / Rokokko
    "chippendale": "Chippendale / Rokokko",
    # Nyklassisisme
    "hepplewhite": "Nyklassisisme",
    "sheraton": "Nyklassisisme",
}

# Sort by length descending so more specific matches win first
DESIGNER_KEYS_SORTED = sorted(DESIGNER_OVERRIDES.keys(), key=len, reverse=True)

# British/American nationalities for Viktorianisme classification
BRITISH_AMERICAN = {"storbritannia", "anna"}
# Note: "Anna" (Other) includes US-based designers, so we treat it as potentially
# British/American. For Continental, we check explicitly.
CONTINENTAL = {"frankrike", "italia", "tyskland", "nederland", "austerrike",
               "spania", "sverige", "danmark", "finland", "noreg"}


def classify_stilperiode(row):
    """
    Classify Stilperiode based on Produsent (designer override) and date range.
    Returns a string or None if classification is not possible.
    """
    produsent = row.get("Produsent", "").strip()
    nasjonalitet = row.get("Nasjonalitet", "").strip().lower()
    produksjonsstad = row.get("Produksjonsstad", "").strip().lower()

    # 1. Designer overrides (check longest matches first)
    if produsent:
        produsent_lower = produsent.lower()
        for key in DESIGNER_KEYS_SORTED:
            if key in produsent_lower:
                return DESIGNER_OVERRIDES[key]

    # 2. Date-based classification
    fra_aar_str = row.get("Frå år", "").strip()
    til_aar_str = row.get("Til år", "").strip()

    if not fra_aar_str:
        return None

    try:
        fra_aar = int(fra_aar_str)
    except ValueError:
        return None

    if fra_aar <= 0:
        return None

    # Compute midpoint if both years exist and are valid, otherwise use Frå år
    if til_aar_str:
        try:
            til_aar = int(til_aar_str)
            if til_aar > 0:
                midpoint = (fra_aar + til_aar) / 2
            else:
                midpoint = fra_aar
        except ValueError:
            midpoint = fra_aar
    else:
        midpoint = fra_aar

    # Determine if British/American or Continental for 1860-1900 split
    is_british_american = False
    if nasjonalitet in BRITISH_AMERICAN:
        is_british_american = True
    elif nasjonalitet in CONTINENTAL:
        is_british_american = False
    else:
        # Check Produksjonsstad for hints
        british_us_places = ["england", "london", "britain", "uk", "usa",
                             "united states", "america", "new york",
                             "california", "los angeles", "boston", "chicago"]
        for place in british_us_places:
            if place in produksjonsstad:
                is_british_american = True
                break

    # Period mapping
    if midpoint < 1600:
        return "Renessanse"
    elif midpoint < 1700:
        return "Barokk"
    elif midpoint < 1750:
        return "Rokokko"
    elif midpoint < 1800:
        return "Nyklassisisme"
    elif midpoint < 1830:
        return "Empire"
    elif midpoint < 1860:
        return "Historisme"
    elif midpoint < 1900:
        if is_british_american:
            return "Viktorianisme"
        else:
            return "Historisme"
    elif midpoint < 1920:
        return "Jugend/Art Nouveau"
    elif midpoint < 1945:
        return "Art Deco / Tidleg modernisme"
    elif midpoint < 1970:
        return "Modernisme / Midtjahrhundre"
    elif midpoint < 2000:
        return "Postmodernisme"
    else:
        return "Samtidsdesign"


# ---------------------------------------------------------------------------
# Nemning (type) classification
# ---------------------------------------------------------------------------
# Each tuple: (category, list of keywords to match)
# Order matters: more specific categories first, "Stol" is fallback.
NEMNING_RULES = [
    ("Gyngestol", ["rocking", "gynge", "rocker", "schaukelstuhl"]),
    ("Krakk", ["stool", "krakk", "taburett", "skammel", "hocker"]),
    ("Barnestol", ["child", "children", "barn", "baby", "highchair", "høg stol",
                    "high chair", "barnestuhl"]),
    ("Benkestol", ["bench", "benk", "settle", "benkestol"]),
    ("Kontorstol", ["office", "kontor", "swivel", "dreiestol"]),
    ("Klappstol", ["folding", "klapp", "sammenleggbar", "foldable"]),
    ("Loungestol", ["lounge", "easy chair", "club chair", "lænestol"]),
    ("Spisestol", ["dining", "spise", "side chair"]),
    ("Armstol", ["armchair", "arm chair", "fauteuil", "lenestol",
                  "armstol", "bergère", "bergere"]),
]


def classify_nemning(row):
    """
    Classify Nemning based on Namn, Materialar, Emneord, Materialkommentar.
    Returns a category string.
    """
    namn = row.get("Namn", "").strip().lower()
    materialar = row.get("Materialar", "").strip().lower()
    emneord = row.get("Emneord", "").strip().lower()
    matkom = row.get("Materialkommentar", "").strip().lower()

    # Combine all searchable text
    combined = f"{namn} | {emneord} | {matkom}"

    for category, keywords in NEMNING_RULES:
        for kw in keywords:
            if kw in combined:
                return category

    # Default fallback
    return "Stol"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Read input CSV
    with open(INPUT_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    total = len(rows)
    print(f"Les {total} rader fraa {INPUT_CSV.name}")
    print()

    # Counters
    stil_before = sum(1 for r in rows if r.get("Stilperiode", "").strip())
    nemning_before = sum(1 for r in rows if r.get("Nemning", "").strip())

    stil_filled = 0
    stil_unfilled = 0
    nemning_filled = 0
    nemning_unfilled = 0

    stil_assigned = Counter()
    nemning_assigned = Counter()

    for row in rows:
        # --- Stilperiode ---
        if not row.get("Stilperiode", "").strip():
            result = classify_stilperiode(row)
            if result:
                row["Stilperiode"] = result
                stil_filled += 1
                stil_assigned[result] += 1
            else:
                stil_unfilled += 1

        # --- Nemning ---
        if not row.get("Nemning", "").strip():
            result = classify_nemning(row)
            row["Nemning"] = result
            nemning_filled += 1
            nemning_assigned[result] += 1

    # Write output CSV
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # --- Statistics ---
    stil_after = sum(1 for r in rows if r.get("Stilperiode", "").strip())
    nemning_after = sum(1 for r in rows if r.get("Nemning", "").strip())

    print("=" * 60)
    print("STILPERIODE")
    print("=" * 60)
    print(f"  Foer:       {stil_before}/{total} ({100*stil_before/total:.1f}%)")
    print(f"  Nye fylte:  {stil_filled}")
    print(f"  Etter:      {stil_after}/{total} ({100*stil_after/total:.1f}%)")
    print(f"  Framleis tomme: {stil_unfilled}")
    print()
    print("  Fordeling av tildelte stilperiodar:")
    for stil, cnt in sorted(stil_assigned.items(), key=lambda x: -x[1]):
        print(f"    {stil:42s} {cnt:5d}")

    print()
    print("=" * 60)
    print("NEMNING (type)")
    print("=" * 60)
    print(f"  Foer:       {nemning_before}/{total} ({100*nemning_before/total:.1f}%)")
    print(f"  Nye fylte:  {nemning_filled}")
    print(f"  Etter:      {nemning_after}/{total} ({100*nemning_after/total:.1f}%)")
    print()
    print("  Fordeling av tildelte nemningar:")
    for nem, cnt in sorted(nemning_assigned.items(), key=lambda x: -x[1]):
        print(f"    {nem:42s} {cnt:5d}")

    print()
    print(f"Skreiv resultat til {OUTPUT_CSV.name}")


if __name__ == "__main__":
    main()
