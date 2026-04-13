import json
import os

with open(r'STOLAR\api.json', 'r', encoding='utf-8') as f:
    api_data = json.load(f)
    chairs = api_data['chairs']

with open(r'STOLAR\enriched_chairs.json', 'r', encoding='utf-8') as f:
    enriched_data = json.load(f)

missing = []
for chair in chairs:
    obj_id = chair['id']
    if obj_id not in enriched_data:
        image_path = os.path.join('STOLAR', 'bguw', f"{obj_id}_bguw.png")
        if os.path.exists(image_path):
            missing.append(obj_id)

print(json.dumps(missing))
