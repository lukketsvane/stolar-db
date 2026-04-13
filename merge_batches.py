import json

with open('STOLAR/enriched_chairs.json', 'r', encoding='utf-8') as f:
    enriched = json.load(f)

with open('batch_results.json', 'r', encoding='utf-8') as f:
    new_data = json.load(f)

enriched.update(new_data)

with open('STOLAR/enriched_chairs.json', 'w', encoding='utf-8') as f:
    json.dump(enriched, f, indent=2, ensure_ascii=False)

print(f"Successfully merged {len(new_data)} chairs.")
