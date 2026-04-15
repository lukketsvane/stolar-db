import json
import os

API_PATH = "STOLAR/api.json"
JSON_PATH = "STOLAR/enriched_chairs.json"
IMAGE_DIR = "STOLAR/bguw"

def load_data(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

api_data = load_data(API_PATH)
master_enriched = load_data(JSON_PATH)

missing = []
for chair in api_data.get('chairs', []):
    obj_id = chair['id']
    if obj_id not in master_enriched:
        image_path = os.path.join(IMAGE_DIR, f"{obj_id}_bguw.png")
        if os.path.exists(image_path):
            missing.append(obj_id)

print(f"Total chairs in API: {len(api_data.get('chairs', []))}")
print(f"Already enriched: {len(master_enriched)}")
print(f"Missing with images: {len(missing)}")
