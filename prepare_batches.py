import json, re

# Load data
nm_data = json.load(open('C:/Users/Shadow/Documents/GitHub/stolar-db/NM_stolar/NM_stolar.json', encoding='utf-8'))
existing_data = json.load(open('C:/Users/Shadow/.claude/projects/C--Users-Shadow-Documents-GitHub-stolar-db/4c82e4f4-b1d1-499f-b42e-2b3fd619158d/tool-results/mcp-claude_ai_Notion-notion-query-database-view-1773513156424.txt'))
existing_results = json.loads(existing_data[0]['text'])
existing_ids = set(r.get('Objekt-ID', '') for r in existing_results.get('results', []))
print(f"Known existing IDs: {len(existing_ids)}")

def normalize_material(val):
    replacements = {
        "Animalske fibre, filt": "Animalske fibre / filt",
        "Annet, kunstlær": "Annet / kunstlær",
        "Annet, glassfiber": "Annet / glassfiber",
        "Annet, linoleum": "Annet / linoleum",
        "Skinn/lær/pergament, gyllenlær": "Skinn/lær/pergament / gyllenlær",
        "Syntetiske fibre, kunstsilke": "Syntetiske fibre / kunstsilke",
        "Tekstil, fløyel": "Tekstil / fløyel",
        "Tekstil, lerret": "Tekstil / lerret",
        "Tekstil, plysj": "Tekstil / plysj",
        "Vegetabilske fibre, lerret": "Vegetabilske fibre / lerret",
        "Vegetabilske fibre, stramei": "Vegetabilske fibre / stramei",
        "Vegetabilske fibre, strie": "Vegetabilske fibre / strie",
        "Tre, furu (BI)": "Tre / furu (BI)",
    }
    return replacements.get(val, val)

def normalize_teknikk(val):
    replacements = {
        "Innfelling, rammeverk med fylling": "Innfelling / rammeverk med fylling",
        "Innfelling, trenagler": "Innfelling / trenagler",
    }
    return replacements.get(val, val)

def to_list(val):
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [val]

def parse_dims(maal_str):
    if not maal_str:
        return {}
    result = {}
    # "H 93,5 x B 48,5 x D 51 cm" format
    h = re.search(r'H\s+(\d+(?:[,\.]\d+)?)\s*x', maal_str)
    if h:
        result['height'] = float(h.group(1).replace(',', '.'))
    b = re.search(r'B\s+(\d+(?:[,\.]\d+)?)\s*x', maal_str)
    if b:
        result['width'] = float(b.group(1).replace(',', '.'))
    d = re.search(r'D\s+(\d+(?:[,\.]\d+)?)\s*cm', maal_str)
    if d:
        result['depth'] = float(d.group(1).replace(',', '.'))
    # Also try "Bredde: 48,5 cm" etc
    if 'height' not in result:
        h2 = re.search(r'H(?:øyde|oyde)?\s*[:\s]\s*(\d+(?:[,\.]\d+)?)\s*cm', maal_str)
        if h2:
            result['height'] = float(h2.group(1).replace(',', '.'))
    if 'width' not in result:
        b2 = re.search(r'B(?:redde)?\s*[:\s]\s*(\d+(?:[,\.]\d+)?)\s*cm', maal_str)
        if b2:
            result['width'] = float(b2.group(1).replace(',', '.'))
    if 'depth' not in result:
        d2 = re.search(r'D(?:ybde|jupn)?\s*[:\s]\s*(\d+(?:[,\.]\d+)?)\s*cm', maal_str)
        if d2:
            result['depth'] = float(d2.group(1).replace(',', '.'))
    # Seat height from second "Høyde:" or standalone
    seat_matches = re.findall(r'H(?:øyde|oyde)\s*[:\s]\s*(\d+(?:[,\.]\d+)?)\s*cm', maal_str)
    if len(seat_matches) >= 2:
        result['seat_height'] = float(seat_matches[-1].replace(',', '.'))
    elif len(seat_matches) == 1 and 'height' in result:
        result['seat_height'] = float(seat_matches[0].replace(',', '.'))
    return result

def parse_years(datering):
    if not datering:
        return {}
    result = {}
    m2 = re.search(r'(\d{4})\s*[–\-]\s*(\d{4})', datering)
    if m2:
        result['fra'] = int(m2.group(1))
        result['til'] = int(m2.group(2))
        return result
    m = re.search(r'(\d{4})', datering)
    if m:
        year = int(m.group(1))
        result['fra'] = year
        if 'ca' in datering.lower() or 'antagelig' in datering.lower() or 'omkring' in datering.lower():
            result['til'] = year + 10
        else:
            result['til'] = year
        return result
    m_cent = re.search(r'(\d{2})00-tall', datering)
    if m_cent:
        cent = int(m_cent.group(1))
        result['fra'] = cent * 100
        result['til'] = cent * 100 + 99
    return result

def get_century(year):
    if year is None:
        return None
    if year < 1300:
        return "1200-talet"
    elif year < 1600:
        return None
    elif year < 1700:
        return "1600-talet"
    elif year < 1800:
        return "1700-talet"
    elif year < 1900:
        return "1800-talet"
    elif year < 2000:
        return "1900-talet"
    else:
        return "2000-talet"

# Build pages
missing_entries = [item for item in nm_data if item['objectId'] not in existing_ids]
print(f"Entries to create: {len(missing_entries)}")

all_pages = []
for item in missing_entries:
    title = item.get('title', '')
    obj_id = item['objectId']
    betegnelse = item.get('Betegnelse', '')

    # Format name like existing entries
    if title and title != betegnelse and title != 'Stol':
        name = title
    elif betegnelse:
        name = f"{betegnelse} ({obj_id})"
    else:
        name = f"{title} ({obj_id})"

    props = {"Name": name, "Objekt-ID": obj_id}

    if betegnelse:
        props["Betegnelse"] = betegnelse
    if item.get('Datering'):
        props["Datering"] = item['Datering']
    if item.get('Mål'):
        props["Mål"] = item['Mål']
    mot = item.get('Materiale og teknikk')
    if mot:
        if isinstance(mot, list):
            mot = '; '.join(mot)
        props["Materialkommentar"] = mot
    if item.get('Produksjonssted'):
        ps = item['Produksjonssted']
        if isinstance(ps, list):
            ps = ', '.join(ps)
        props["Produksjonsstad"] = ps
    if item.get('Ervervelse'):
        props["Erverving"] = item['Ervervelse']
    if item.get('url'):
        props["Nasjonalmuseet"] = item['url']
    if item.get('model3d'):
        props["3D-fil"] = item['model3d']

    # Multi-select: Materialar
    materials = [normalize_material(m) for m in to_list(item.get('Materiale'))]
    if materials:
        props["Materialar"] = json.dumps(materials, ensure_ascii=False)

    # Multi-select: Teknikk
    teknikker = [normalize_teknikk(t) for t in to_list(item.get('Teknikk'))]
    all_tek = list(dict.fromkeys(teknikker))
    if all_tek:
        props["Teknikk"] = json.dumps(all_tek, ensure_ascii=False)

    # Multi-select: Emneord
    emneord = to_list(item.get('Emneord'))
    if emneord:
        props["Emneord"] = json.dumps(emneord, ensure_ascii=False)

    # Select: Stilperiode (single-select, pick first if list)
    sp = item.get('Stilperiode')
    if sp:
        if isinstance(sp, list):
            props["Stilperiode"] = sp[0]
        else:
            props["Stilperiode"] = sp

    # Parse dimensions
    dims = parse_dims(item.get('Mål', ''))
    if 'height' in dims:
        props["Høgde (cm)"] = dims['height']
    if 'width' in dims:
        props["Breidde (cm)"] = dims['width']
    if 'depth' in dims:
        props["Djupn (cm)"] = dims['depth']
    if 'seat_height' in dims:
        props["Setehøgde (cm)"] = dims['seat_height']

    # Parse years
    years = parse_years(item.get('Datering', ''))
    if 'fra' in years:
        props["Frå år"] = years['fra']
    if 'til' in years:
        props["Til år"] = years['til']

    # Century
    century = get_century(years.get('fra'))
    if century:
        props["Hundreår"] = century

    all_pages.append({"properties": props})

# Save chunks of 25 for Notion create-pages
chunk_size = 25
for i in range(0, len(all_pages), chunk_size):
    chunk = all_pages[i:i+chunk_size]
    chunk_num = i // chunk_size
    with open(f'C:/Users/Shadow/Documents/GitHub/stolar-db/chunk_{chunk_num:02d}.json', 'w', encoding='utf-8') as f:
        json.dump(chunk, f, ensure_ascii=False, indent=2)
    print(f"Chunk {chunk_num:02d}: {len(chunk)} pages")

print(f"\nTotal chunks: {(len(all_pages) + chunk_size - 1) // chunk_size}")
print(f"\nSample entry:")
print(json.dumps(all_pages[0], indent=2, ensure_ascii=False))
