import json

new_data = {
  "O120510": {
    "tal_komponentar": 4,
    "har_armlene": False,
    "har_polstring": False,
    "rygg_type": "heiltre",
    "tal_bein": 2,
    "symmetri": "bilateral",
    "synleg_samansetjing": "ingen_synleg",
    "ornament_nivaa": 3,
    "struktur_type": "bukk"
  },
  "O120512": {
    "tal_komponentar": 16,
    "har_armlene": True,
    "har_polstring": True,
    "rygg_type": "open",
    "tal_bein": 4,
    "symmetri": "bilateral",
    "synleg_samansetjing": "tapp-og-hol",
    "ornament_nivaa": 2,
    "struktur_type": "fire-bein"
  },
  "O120513": {
    "tal_komponentar": 13,
    "har_armlene": True,
    "har_polstring": False,
    "rygg_type": "spiler",
    "tal_bein": 3,
    "symmetri": "bilateral",
    "synleg_samansetjing": "tapp-og-hol",
    "ornament_nivaa": 1,
    "struktur_type": "anna"
  },
  "O120517": {
    "tal_komponentar": 14,
    "har_armlene": True,
    "har_polstring": True,
    "rygg_type": "polstra",
    "tal_bein": 4,
    "symmetri": "bilateral",
    "synleg_samansetjing": "ingen_synleg",
    "ornament_nivaa": 2,
    "struktur_type": "fire-bein"
  },
  "O120518": {
    "tal_komponentar": 14,
    "har_armlene": True,
    "har_polstring": True,
    "rygg_type": "polstra",
    "tal_bein": 4,
    "symmetri": "bilateral",
    "synleg_samansetjing": "ingen_synleg",
    "ornament_nivaa": 3,
    "struktur_type": "fire-bein"
  }
}

try:
    with open('STOLAR/enriched_chairs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error loading JSON: {e}")
    data = {}

data.update(new_data)

with open('STOLAR/enriched_chairs.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Updated STOLAR/enriched_chairs.json with 5 new entries')
