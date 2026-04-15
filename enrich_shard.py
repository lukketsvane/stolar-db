import json
import os
import time
import concurrent.futures
import sys
import random
from google import genai
from google.genai import types

# Configuration
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# Rotate models to maximize total quota
MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite-preview-02-05",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b"
]

IMAGE_DIR = "STOLAR/bguw"
MAX_WORKERS = 2 # Per shard

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

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def process_chair(chair_id):
    image_path = os.path.join(IMAGE_DIR, f"{chair_id}_bguw.png")
    if not os.path.exists(image_path):
        return chair_id, None
    
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Randomly pick a model or try them in sequence
        models_to_try = list(MODELS)
        random.shuffle(models_to_try)
        
        last_err = ""
        for model_to_use in models_to_try:
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
                result = json.loads(response.text)
                return chair_id, result
            except Exception as e:
                last_err = str(e)
                if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
                    continue # Try next model
                else:
                    raise e
        
        print(f"All models exhausted for {chair_id}: {last_err}")
        return chair_id, "RETRY"
        
    except Exception as e:
        print(f"Error processing {chair_id}: {e}")
        return chair_id, "ERROR"

def main():
    if len(sys.argv) < 2:
        return
    
    shard_index = sys.argv[1]
    shard_file = f"shard_{shard_index}.json"
    output_file = f"STOLAR/enriched_chairs_shard_{shard_index}.json"
    
    if not os.path.exists(shard_file):
        return
    
    shard_ids = load_json(shard_file)
    enriched_data = load_json(output_file)
    
    to_process = [cid for cid in shard_ids if cid not in enriched_data]
    print(f"Shard {shard_index}: {len(to_process)} remaining.")
    
    # Process in small batches
    batch_size = 5
    for i in range(0, len(to_process), batch_size):
        batch = to_process[i:i+batch_size]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_id = {executor.submit(process_chair, cid): cid for cid in batch}
            batch_results = 0
            has_retry = False
            for future in concurrent.futures.as_completed(future_to_id):
                cid, result = future.result()
                if isinstance(result, dict):
                    enriched_data[cid] = result
                    batch_results += 1
                elif result == "RETRY":
                    has_retry = True
        
        if batch_results > 0:
            save_json(output_file, enriched_data)
        
        if has_retry:
            print(f"Shard {shard_index}: Hit quota on all models, sleeping for 30s...")
            time.sleep(30)
        else:
            time.sleep(2)

if __name__ == "__main__":
    main()
