#!/usr/bin/env python3
"""Push enrichment data from JSON files to Notion, translating to Nynorsk."""

import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE = Path(__file__).parent

NOTION_TOKEN = ""
for line in (BASE / ".env").read_text(encoding="utf-8").splitlines():
    k, _, v = line.partition("=")
    if k.strip() == "NOTION_API_KEY":
        NOTION_TOKEN = v.strip().strip('"')

DATABASE_ID = "405e0f64-6b77-4aab-88b8-73281e58c4f0"
HDR = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# English -> Nynorsk translation maps
ORIGIN_MAP = {
    "Great Britain": "Storbritannia", "England": "Storbritannia", "Britain": "Storbritannia",
    "London": "Storbritannia", "United Kingdom": "Storbritannia", "Scotland": "Storbritannia",
    "France": "Frankrike", "Paris": "Frankrike",
    "Germany": "Tyskland", "Bavaria": "Tyskland", "Berlin": "Tyskland", "Munich": "Tyskland",
    "Italy": "Italia", "Rome": "Italia", "Milan": "Italia", "Venice": "Italia", "Florence": "Italia", "Turin": "Italia",
    "Denmark": "Danmark", "Copenhagen": "Danmark",
    "Sweden": "Sverige", "Stockholm": "Sverige",
    "Norway": "Noreg", "Finland": "Finland",
    "United States": "USA", "USA": "USA", "New York": "USA", "America": "USA",
    "Japan": "Japan", "China": "Kina", "India": "India",
    "Netherlands": "Nederland", "Holland": "Nederland", "Amsterdam": "Nederland",
    "Belgium": "Belgia", "Austria": "Austerrike", "Vienna": "Austerrike",
    "Spain": "Spania", "Switzerland": "Sveits", "Czech Republic": "Tsjekkia",
    "Czechoslovakia": "Tsjekkia", "Poland": "Polen", "Russia": "Russland",
    "Ireland": "Irland", "Portugal": "Portugal", "Greece": "Hellas",
    "Hungary": "Ungarn", "Romania": "Romania", "Turkey": "Tyrkia",
    "Egypt": "Egypt", "Brazil": "Brasil", "Mexico": "Mexico",
    "Canada": "Canada", "Australia": "Australia",
}

MATERIAL_MAP = {
    "Oak": "Eik", "Beech": "Bøk", "Walnut": "Valnøtt", "Mahogany": "Mahogni",
    "Pine": "Furu", "Elm": "Alm", "Ash": "Ask", "Birch": "Bjørk",
    "Cherry": "Kirsebær", "Maple": "Lønn", "Teak": "Teak", "Rosewood": "Rosentre",
    "Ebony": "Ibenholt", "Cedar": "Seder", "Lime": "Lind", "Yew": "Barlind",
    "Wood": "Tre", "Plywood": "Kryssfiner", "Bamboo": "Bambus",
    "Steel": "Stål", "Iron": "Jern", "Brass": "Messing", "Bronze": "Bronse",
    "Copper": "Kopar", "Aluminium": "Aluminium", "Aluminum": "Aluminium",
    "Chrome": "Krom", "Metal": "Metall", "Silver": "Sølv", "Gold": "Gull",
    "Leather": "Lær", "Silk": "Silke", "Velvet": "Fløyel", "Cotton": "Bomull",
    "Wool": "Ull", "Linen": "Lin", "Canvas": "Lerret", "Textile": "Tekstil",
    "Fabric": "Tekstil", "Upholstery": "Polstring",
    "Glass": "Glas", "Ceramic": "Keramikk", "Marble": "Marmor", "Stone": "Stein",
    "Plastic": "Plast", "Fiberglass": "Glasfiber", "Fibreglass": "Glasfiber",
    "Polyester": "Polyester", "Polyurethane": "Polyuretan", "Nylon": "Nylon",
    "Acrylic": "Akryl", "Rubber": "Gummi", "Resin": "Harpiks",
    "Cane": "Rotting", "Rattan": "Rotting", "Rush": "Siv", "Straw": "Strå",
    "Wicker": "Vidje", "Paper": "Papir", "Cardboard": "Papp",
    "Horsehair": "Hestehår", "Linen (material)": "Lin",
    "Silk braid": "Silkeband", "Gilt": "Forgylling", "Ivory": "Elfenbein",
    "Lacquer": "Lakk", "Paint": "Maling", "Varnish": "Ferniss",
}

TECHNIQUE_MAP = {
    "Carving": "Utskjering", "Carved": "Utskjering", "Turning": "Dreiing",
    "Turned": "Dreiing", "Upholstery": "Polstring", "Upholstered": "Polstring",
    "Welding": "Sveising", "Welded": "Sveising",
    "Laminating": "Laminering", "Laminated": "Laminering",
    "Bending": "Bøying", "Bent": "Bøying", "Steam bending": "Dampbøying",
    "Painting": "Måling", "Painted": "Måling", "Lacquering": "Lakkering",
    "Lacquered": "Lakkering", "Gilding": "Forgylling", "Gilt": "Forgylling",
    "Inlay": "Innlegging", "Inlaid": "Innlegging", "Marquetry": "Intarsia",
    "Veneering": "Finering", "Veneered": "Finering",
    "Joinery": "Samanføying", "Mortise and tenon": "Tapping",
    "Dovetail": "Sinkesamband", "Dowelling": "Plugging",
    "Moulding": "Støyping", "Molding": "Støyping", "Casting": "Støyping",
    "Weaving": "Veving", "Woven": "Veving", "Plaiting": "Fletting",
    "Nailing": "Spikring", "Screwing": "Skruing",
    "Polishing": "Polering", "Staining": "Beising",
    "Embossing": "Pressing", "Stamping": "Stempling",
    "Injection moulding": "Sprøytestøyping",
}

STYLE_MAP = {
    "Renaissance": "Renessanse", "Baroque": "Barokk", "Rococo": "Rokoko",
    "Neoclassical": "Nyklassisisme", "Neo-classical": "Nyklassisisme",
    "Empire": "Empire", "Regency": "Regency",
    "Gothic": "Gotikk", "Gothic Revival": "Nygotikk", "Neo-Gothic": "Nygotikk",
    "Victorian": "Viktorianisme", "Edwardian": "Edwardiansk",
    "Art Nouveau": "Jugend", "Arts and Crafts": "Arts and Crafts",
    "Art Deco": "Art Deco", "Modernist": "Modernisme", "Modern": "Modernisme",
    "Functionalism": "Funksjonalisme",
    "Post-modern": "Postmodernisme", "Postmodern": "Postmodernisme",
    "Contemporary": "Samtidsdesign", "Minimalism": "Minimalisme",
    "Biedermeier": "Biedermeier", "Chippendale": "Chippendale",
    "Queen Anne": "Queen Anne", "William and Mary": "William and Mary",
    "George I": "Georg I", "George II": "Georg II", "George III": "Georg III",
    "Louis XV": "Louis XV", "Louis XVI": "Louis XVI",
    "Aesthetic Movement": "Estetisk rørsle",
    "Japonisme": "Japonisme",
}


def translate_list(items, mapping):
    result = []
    for item in items:
        item_clean = item.strip()
        if item_clean in mapping:
            result.append(mapping[item_clean])
        else:
            # Try partial match
            translated = item_clean
            for eng, nyn in mapping.items():
                if eng.lower() in item_clean.lower():
                    translated = nyn
                    break
            result.append(translated)
    return list(dict.fromkeys(result))  # deduplicate preserving order


def translate_origin(origin):
    if not origin:
        return None
    return ORIGIN_MAP.get(origin, ORIGIN_MAP.get(origin.split(",")[0].strip(), origin))


def translate_style(style):
    if not style:
        return None
    return STYLE_MAP.get(style, style)


def query_all_pages():
    """Get all page IDs mapped by OID."""
    pages = {}
    cursor, has_more = None, True
    while has_more:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = requests.post(
            f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
            headers=HDR, json=body, timeout=30,
        )
        data = r.json()
        for p in data["results"]:
            props = p["properties"]
            rt = props.get("Objekt-ID", {}).get("rich_text", [])
            oid = rt[0]["plain_text"] if rt else ""
            if oid:
                # Also get current values to avoid overwriting
                pages[oid] = {
                    "pid": p["id"],
                    "has_height": props.get("Høgde (cm)", {}).get("number") is not None,
                    "has_width": props.get("Breidde (cm)", {}).get("number") is not None,
                    "has_depth": props.get("Djupn (cm)", {}).get("number") is not None,
                    "has_style": bool(props.get("Stilperiode", {}).get("select")),
                    "has_nationality": bool(props.get("Nasjonalitet", {}).get("select")),
                    "has_designer": bool(
                        (props.get("Produsent", {}).get("rich_text") or [{}])[0].get("plain_text", "")
                    ),
                    "has_origin": bool(
                        (props.get("Produksjonsstad", {}).get("rich_text") or [{}])[0].get("plain_text", "")
                    ),
                }
        has_more = data.get("has_more", False)
        cursor = data.get("next_cursor")
    return pages


def update_page(pid, props):
    for attempt in range(3):
        try:
            r = requests.patch(
                f"https://api.notion.com/v1/pages/{pid}",
                headers=HDR, json={"properties": props}, timeout=30,
            )
            if r.status_code == 200:
                return True
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
        except Exception:
            time.sleep(3)
    return False


def main():
    print("Loading enrichment data...")
    enrichments = {}

    for fname in ["_va_enrichment.json", "_nm_enrichment.json"]:
        f = BASE / fname
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            print(f"  {fname}: {len(data)} entries")
            enrichments.update(data)

    styles = {}
    sf = BASE / "_style_enrichment.json"
    if sf.exists():
        styles = json.loads(sf.read_text(encoding="utf-8"))
        print(f"  _style_enrichment.json: {len(styles)} entries")

    if not enrichments and not styles:
        print("No enrichment data found!")
        return

    print(f"\nTotal enrichments: {len(enrichments)} data + {len(styles)} styles")
    print("Querying Notion for page IDs...")
    pages = query_all_pages()
    print(f"  {len(pages)} pages found")

    ok = skip = fail = 0
    total = len(set(list(enrichments.keys()) + list(styles.keys())))

    for i, oid in enumerate(set(list(enrichments.keys()) + list(styles.keys()))):
        if oid not in pages:
            skip += 1
            continue

        page = pages[oid]
        props = {}
        enr = enrichments.get(oid, {})

        # Dimensions (only fill if missing)
        if not page["has_height"] and enr.get("height_cm"):
            props["Høgde (cm)"] = {"number": enr["height_cm"]}
        if not page["has_width"] and enr.get("width_cm"):
            props["Breidde (cm)"] = {"number": enr["width_cm"]}
        if not page["has_depth"] and enr.get("depth_cm"):
            props["Djupn (cm)"] = {"number": enr["depth_cm"]}

        # Designer (only fill if missing)
        if not page["has_designer"] and enr.get("designer"):
            props["Produsent"] = {"rich_text": [{"text": {"content": enr["designer"]}}]}

        # Origin (only fill if missing)
        if not page["has_origin"] and enr.get("origin"):
            translated = translate_origin(enr["origin"])
            if translated:
                props["Produksjonsstad"] = {"rich_text": [{"text": {"content": translated}}]}

        # Nationality (only fill if missing)
        if not page["has_nationality"] and enr.get("nationality"):
            nat = translate_origin(enr["nationality"])
            if nat:
                props["Nasjonalitet"] = {"select": {"name": nat}}

        # Style (only fill if missing)
        style_val = styles.get(oid) or enr.get("style")
        if not page["has_style"] and style_val:
            translated = translate_style(style_val) if style_val else None
            if translated:
                props["Stilperiode"] = {"select": {"name": translated}}

        # Techniques (always add if available, these are multi-select)
        if enr.get("techniques"):
            translated = translate_list(enr["techniques"], TECHNIQUE_MAP)
            if translated:
                props["Teknikk"] = {"multi_select": [{"name": t} for t in translated]}

        if not props:
            skip += 1
            continue

        if update_page(page["pid"], props):
            ok += 1
        else:
            fail += 1

        if (i + 1) % 100 == 0:
            print(f"  [{i+1}/{total}] Updated: {ok}, Skipped: {skip}, Failed: {fail}")

    print(f"\nDone! Updated: {ok}, Skipped: {skip}, Failed: {fail}")


if __name__ == "__main__":
    main()
