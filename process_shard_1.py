import json
import os
import time
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
import concurrent.futures

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

IMAGE_DIR = "STOLAR/bguw"
OUTPUT_FILE = "STOLAR/enriched_chairs_shard_1.json"

PROMPT = """Analyze this chair image and provide information according to the following schema in JSON format:
- tal_komponentar (int)
- har_armlene (bool)
- har_polstring (bool)
- rygg_type (str): "heiltre", "polstra", "open", "ingen"
- tal_bein (int)
- symmetri (str): "bilateral", "radial", "asymmetrisk"
- synleg_samansetjing (str)
- ornament_nivaa (int): 0-3
- struktur_type (str): "fire-bein", "frittberande", "gyngande", "pidestall", "samanleggbar", "anna"

Return ONLY the JSON object without markdown formatting."""

def process_chair(chair_id):
    image_path = os.path.join(IMAGE_DIR, f"{chair_id}_bguw.png")
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return chair_id, None
    
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                PROMPT,
                types.Part.from_bytes(data=image_bytes, mime_type="image/png")
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        return chair_id, json.loads(response.text)
    except Exception as e:
        print(f"Error processing {chair_id}: {e}")
        return chair_id, None

def main():
    with open("missing_chairs.txt", "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    # 0-indexed: lines 296-590 means indices 295 to 589. So slice 295:590
    target_ids = lines[295:590]
    print(f"Target IDs: {len(target_ids)} (first: {target_ids[0]}, last: {target_ids[-1]})")

    results = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                results = json.load(f)
            except json.JSONDecodeError:
                results = {}

    to_process = [cid for cid in target_ids if cid not in results]
    print(f"Remaining to process: {len(to_process)}")

    batch_size = 5
    for i in range(0, len(to_process), batch_size):
        batch = to_process[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(to_process)-1)//batch_size + 1}...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_id = {executor.submit(process_chair, cid): cid for cid in batch}
            for future in concurrent.futures.as_completed(future_to_id):
                cid, result = future.result()
                if result:
                    results[cid] = result
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        time.sleep(1) # rate limit mitigation

if __name__ == "__main__":
    main()
