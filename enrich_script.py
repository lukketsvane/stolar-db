import json
import re

ids_to_process = ["NMK.2018.0110", "NMK.2018.0221", "NMK.2018.0382", "NMK.2018.0383", "NMK.2018.0423", "NMK.2018.0430", "NMK.2018.0468", "NMK.2018.0486", "NMK.2020.0270", "NMK.2020.0271", "NMK.2020.0272", "NMK.2020.0273", "NMK.2021.0137", "NMK.2021.0149", "NMK.2021.0204", "NMK.2023.0091", "NMK.DEP.2010.0009", "NMK.DEP.2019.0014", "NMK.INVENTAR.2017.0213", "O100671", "O100678", "O101934", "O101947", "O10273", "O10416", "O107395", "O107438", "O107439", "O107444", "O107557", "O108602", "O108604", "O108606", "O108869", "O109262", "O109491", "O109522", "O109823", "O109825", "O109862", "O110055", "O110056", "O110757", "O111434", "O111829", "O111968", "O112016", "O112068", "O112073", "O112074", "O112075", "O112076", "O112077", "O112078", "O112079", "O112081", "O112088", "O1121874", "O112269", "O112351", "O1123933", "O112468", "O112501", "O112502", "O112503", "O11281", "O11300", "O1131394", "O1131697", "O11334", "O113385", "O113387", "O113388", "O113389", "O113420", "O11345", "O1135253", "O1135719", "O1135720", "O1135721", "O1135723", "O113578", "O113729", "O1140195", "O1140196", "O114110", "O114123", "O1141612", "O114191", "O114197", "O114267", "O114457", "O114459", "O114460", "O114462", "O114827", "O114853", "O115054", "O115280", "O115282"]

with open('STOLAR/api.json', 'r', encoding='utf-8') as f:
    api_data = json.load(f)

chairs_dict = {chair['id']: chair for chair in api_data.get('chairs', [])}

with open('STOLAR/enriched_chairs.json', 'r', encoding='utf-8') as f:
    enriched_data = json.load(f)

for chair_id in ids_to_process:
    if chair_id not in chairs_dict:
        continue
    
    chair = chairs_dict[chair_id]
    
    # 1. Armrest
    name = chair.get('name', '').lower()
    c_type = chair.get('type', '').lower()
    har_armlene = 'arm' in name or 'arm' in c_type
    
    # 2. Upholstery
    mat = chair.get('materials', '').lower()
    desc = chair.get('materials_desc', '').lower()
    tech = chair.get('technique', '').lower()
    polst_keywords = ['polstr', 'tekstil', 'lær', 'skinn', 'fløyel', 'ull', 'hud', 'stoff', 'canvas', 'lerret']
    har_polstring = any(k in mat or k in desc or k in tech for k in polst_keywords)
    
    # 3. Back type
    if 'krakk' in c_type or 'stool' in name or 'uten rygg' in name:
        rygg_type = 'ingen'
    elif har_polstring:
        rygg_type = 'polstra'
    else:
        rygg_type = 'open' if ('gjennombrutt' in desc or 'open' in name) else 'heiltre'
        if 'plast' in mat or 'poly' in mat or 'betong' in mat:
            rygg_type = 'heiltre'
            
    # 4. Legs
    tal_bein = 4
    if 'strata' in name or 'pedestal' in desc or 'balans' in name or 'krakk' in name and 'betong' in mat:
        tal_bein = 0 if ('betong' in mat or 'strata' in name) else 2
    if 'chaise' in name.lower() or 'sedan' in name.lower():
        tal_bein = 0
        
    # 5. Symmetry
    symmetri = 'bilateral'
    if 'strata' in name:
        symmetri = 'radial'
        
    # 6. Joinery
    if 'plast' in mat or 'poly' in mat or 'betong' in mat or 'marmor' in mat:
        synleg_samansetjing = 'ingen_synleg'
    elif 'stål' in mat and ('rør' in mat or 'tubular' in desc):
        synleg_samansetjing = 'skruar'
    elif 'sveis' in tech or 'sveis' in desc:
        synleg_samansetjing = 'sveisa'
    else:
        synleg_samansetjing = 'tapp-og-hol'
        
    # 7. Ornament level
    style = chair.get('style', '').lower()
    if any(s in style for s in ['samtids', 'modern', 'bauhaus', 'funksjonal', 'art deco']):
        ornament_nivaa = 0
    elif 'jugend' in style or 'art nouveau' in style:
        ornament_nivaa = 1
    elif 'nyklassis' in style or 'empire' in style:
        ornament_nivaa = 2
    elif 'barokk' in style or 'rokokko' in style or 'historis' in style or 'viktorian' in style or 'renessanse' in style:
        ornament_nivaa = 3
    else:
        ornament_nivaa = 1
        
    # 8. Structure type
    struktur_type = 'fire-bein'
    if 'rør' in mat and 'bauhaus' in style:
        struktur_type = 'frittberande'
    elif 'gyng' in desc or 'tip ton' in name:
        struktur_type = 'gyngande'
    elif 'strata' in name or 'sedan' in name:
        struktur_type = 'anna'
    elif 'balans' in name:
        struktur_type = 'anna'
        
    # 9. Components
    tal_komponentar = 5 if struktur_type == 'fire-bein' else 3
    if ornament_nivaa >= 2:
        tal_komponentar += 2
    if har_polstring:
        tal_komponentar += 1
    if synleg_samansetjing == 'ingen_synleg':
        tal_komponentar = 1
        
    enriched_data[chair_id] = {
        "tal_komponentar": tal_komponentar,
        "har_armlene": har_armlene,
        "har_polstring": har_polstring,
        "rygg_type": rygg_type,
        "tal_bein": tal_bein,
        "symmetri": symmetri,
        "synleg_samansetjing": synleg_samansetjing,
        "ornament_nivaa": ornament_nivaa,
        "struktur_type": struktur_type
    }

with open('STOLAR/enriched_chairs.json', 'w', encoding='utf-8') as f:
    json.dump(enriched_data, f, indent=2, ensure_ascii=False)

print(f"Enriched {len(ids_to_process)} chairs.")
