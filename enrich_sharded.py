import json
import os
import time
import base64
import sys
import concurrent.futures
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
PRIMARY_MODEL = "gemini-2.0-flash"
FALLBACK_MODEL = "gemini-flash-latest"
IMAGE_DIR = "STOLAR/bguw"
MAX_WORKERS = 3 # Parallel requests

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
        
        # Try primary model
        model_to_use = PRIMARY_MODEL
        try:
            response = client.models.generate_content(
                model=model_to_use,
                contents=[
                    PROMPT,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                # Quota hit on primary, try fallback
                model_to_use = FALLBACK_MODEL
                print(f"Quota hit for {PRIMARY_MODEL}, trying {FALLBACK_MODEL} for {chair_id}...")
                response = client.models.generate_content(
                    model=model_to_use,
                    contents=[
                        PROMPT,
                        types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    )
                )
            else:
                raise e
        
        result = json.loads(response.text)
        return chair_id, result
    except Exception as e:
        print(f"Error processing {chair_id}: {e}")
        # If we hit a rate limit on both or other error, return error string
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            return chair_id, "RETRY"
        return chair_id, "ERROR"

def main():
    if len(sys.argv) < 3:
        print("Usage: python enrich_sharded.py <shard_index> <total_shards>")
        return

    shard_index = int(sys.argv[1])
    total_shards = int(sys.argv[2])
    shard_json_path = f"STOLAR/enriched_chairs_shard_{shard_index}.json"
    
    API_PATH = "STOLAR/api.json"
    JSON_PATH = "STOLAR/enriched_chairs.json"
    
    api_data = load_data(API_PATH)
    master_enriched = load_data(JSON_PATH)
    shard_enriched = load_data(shard_json_path)
    
    missing = []
    for chair in api_data.get('chairs', []):
        obj_id = chair['id']
        # If not in master AND not in my shard yet, and has image
        if obj_id not in master_enriched and obj_id not in shard_enriched:
            image_path = os.path.join(IMAGE_DIR, f"{obj_id}_bguw.png")
            if os.path.exists(image_path):
                missing.append(obj_id)
    
    # Partition based on total_shards
    my_missing = missing[shard_index::total_shards]
    
    print(f"Shard {shard_index}/{total_shards}: Found {len(my_missing)} missing chairs.")
    
    batch_size = 20
    for i in range(0, len(my_missing), batch_size):
        batch = my_missing[i:i+batch_size]
        print(f"Shard {shard_index}: Processing batch {i//batch_size + 1}/{(len(my_missing)-1)//batch_size + 1}...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_id = {executor.submit(process_chair, cid): cid for cid in batch}
            batch_results = 0
            for future in concurrent.futures.as_completed(future_to_id):
                cid, result = future.result()
                if result and isinstance(result, dict):
                    shard_enriched[cid] = result
                    batch_results += 1
                elif result == "RETRY":
                    print(f"Shard {shard_index}: Hit quota on both models, sleeping for 60s...")
                    time.sleep(60)
        
        if batch_results > 0:
            save_data(shard_json_path, shard_enriched)
            print(f"Shard {shard_index}: Saved progress. Total enriched in shard: {len(shard_enriched)}")
        
        time.sleep(2)

if __name__ == "__main__":
    main()
