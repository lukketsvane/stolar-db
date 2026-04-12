import json
import csv
import os

def enrich_db():
    # Load enriched data
    with open('STOLAR/enriched_chairs.json', 'r', encoding='utf-8') as f:
        enriched_data = json.load(f)

    # Fields to add
    new_fields = [
        "tal_komponentar", "har_armlene", "har_polstring", "rygg_type",
        "tal_bein", "symmetri", "synleg_samansetjing", "ornament_nivaa",
        "struktur_type"
    ]

    # Update STOLAR.csv
    csv_rows = []
    header = []
    with open('STOLAR/STOLAR.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        # Add new fields to header if they don't exist
        for field in new_fields:
            if field not in header:
                header.append(field)
        
        for row in reader:
            obj_id = row['Objekt-ID']
            if obj_id in enriched_data:
                for field in new_fields:
                    row[field] = enriched_data[obj_id].get(field, "")
            csv_rows.append(row)

    with open('STOLAR/STOLAR.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(csv_rows)

    # Update api.json
    with open('STOLAR/api.json', 'r', encoding='utf-8') as f:
        api_data = json.load(f)

    for chair in api_data['chairs']:
        obj_id = chair['id']
        if obj_id in enriched_data:
            for field in new_fields:
                chair[field] = enriched_data[obj_id].get(field, "")

    with open('STOLAR/api.json', 'w', encoding='utf-8') as f:
        json.dump(api_data, f, indent=2, ensure_ascii=False)

    print("Successfully updated STOLAR.csv and api.json")

if __name__ == "__main__":
    enrich_db()
