import json
import os
import time
import base64
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
MAX_WORKERS = 5 # Parallel requests
OUTPUT_FILE = "STOLAR/enriched_chairs_shard_4.json"

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
    # Read missing_chairs.txt lines 1181-1475 (1-based index)
    with open("missing_chairs.txt", "r", encoding='utf-16') as f:
        all_lines = f.readlines()
    
    # 1181 to 1475 inclusive
    shard_ids = [line.strip() for line in all_lines[1180:1475]]
    print(f"Loaded {len(shard_ids)} IDs from missing_chairs.txt")
    
    enriched_data = load_data(OUTPUT_FILE)
    
    missing = []
    for cid in shard_ids:
        if cid not in enriched_data:
            image_path = os.path.join(IMAGE_DIR, f"{cid}_bguw.png")
            if os.path.exists(image_path):
                missing.append(cid)
            else:
                print(f"Image for {cid} not found.")
    
    print(f"Found {len(missing)} missing chairs with images in this shard.")
    
    batch_size = 20
    for i in range(0, len(missing), batch_size):
        batch = missing[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(missing)-1)//batch_size + 1}...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_id = {executor.submit(process_chair, cid): cid for cid in batch}
            batch_results = 0
            for future in concurrent.futures.as_completed(future_to_id):
                cid, result = future.result()
                if result and isinstance(result, dict):
                    enriched_data[cid] = result
                    batch_results += 1
                elif result == "RETRY":
                    print("Hit quota on both models, sleeping for 60s...")
                    time.sleep(60)
        
        if batch_results > 0:
            save_data(OUTPUT_FILE, enriched_data)
            print(f"Saved progress. Total enriched in shard 4: {len(enriched_data)}")
        
        time.sleep(2)

if __name__ == "__main__":
    main()
