import json
import os
import time
import base64
import concurrent.futures
from pathlib import Path
from google import genai
from google.genai import types

# Configuration
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.0-flash"
JSON_PATH = "STOLAR/enriched_chairs.json"
API_PATH = "STOLAR/api.json"
IMAGE_DIR = "STOLAR/bguw"
MAX_WORKERS = 5 # Parallel requests

PROMPT = """Analyze this chair image and provide information according to the following schema in JSON format:
- tal_komponentar (int): Number of main structural components.
- har_armlene (bool): Does it have armrests?
- har_polstring (bool): Does it have upholstery?
- rygg_type (str): one of "heiltre", "polstra", "open", "ingen".
- tal_bein (int): Number of legs (0 for continuous base/pidestall).
- symmetri (str): one of "bilateral", "radial", "asymmetrisk".
- synleg_samansetjing (str): e.g., "ingen_synleg", "sveisa", "skruar", "tapp-og-hol", "bøygd", etc.
- ornament_nivaa (int): 0 (none/minimal) to 3 (highly ornate).
- struktur_type (str): one of "fire-bein", "frittberande", "gyngande", "pidestall", "samanleggbar", "anna".

Return ONLY the JSON object."""

def load_data(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def process_chair(chair_id):
    image_path = os.path.join(IMAGE_DIR, f"{chair_id}_bguw.png")
    if not os.path.exists(image_path):
        return chair_id, None
    
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                PROMPT,
                types.Part.from_bytes(data=image_bytes, mime_type="image/png")
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        result = json.loads(response.text)
        return chair_id, result
    except Exception as e:
        print(f"Error processing {chair_id}: {e}")
        return chair_id, "ERROR"

def main():
    api_data = load_data(API_PATH)
    enriched_data = load_data(JSON_PATH)
    
    missing = []
    for chair in api_data.get('chairs', []):
        obj_id = chair['id']
        if obj_id not in enriched_data:
            image_path = os.path.join(IMAGE_DIR, f"{obj_id}_bguw.png")
            if os.path.exists(image_path):
                missing.append(obj_id)
    
    print(f"Found {len(missing)} missing chairs with images.")
    
    # Process in batches of 50 to save progress frequently
    batch_size = 50
    for i in range(0, len(missing), batch_size):
        batch = missing[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(missing)-1)//batch_size + 1}...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_id = {executor.submit(process_chair, cid): cid for cid in batch}
            for future in concurrent.futures.as_completed(future_to_id):
                cid, result = future.result()
                if result and result != "ERROR":
                    enriched_data[cid] = result
        
        save_data(JSON_PATH, enriched_data)
        # Periodic sync with DB
        os.system("python STOLAR/enrich_db.py")
        print(f"Saved progress and synced DB. Total enriched: {len(enriched_data)}")
        
        # Rate limit safety between batches
        time.sleep(2)

if __name__ == "__main__":
    main()
