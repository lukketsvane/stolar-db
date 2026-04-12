import json
import os
import time
import base64
from pathlib import Path
from google import genai
from google.genai import types

# Configuration
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.0-flash"

IDS = ["O1153416", "O1153451"]

JSON_PATH = "STOLAR/enriched_chairs.json"
IMAGE_DIR = "STOLAR/bguw"

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

def load_enriched_data():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_enriched_data(data):
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    enriched_data = load_enriched_data()
    
    count = 0
    for chair_id in IDS:
        image_path = os.path.join(IMAGE_DIR, f"{chair_id}_bguw.png")
        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
            continue
            
        print(f"Processing {chair_id}...")
        
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
            enriched_data[chair_id] = result
            print(f"Result for {chair_id}: {result}")
            
        except Exception as e:
            print(f"Error processing {chair_id}: {e}")
            continue

    save_enriched_data(enriched_data)
    print(f"Finished test.")

if __name__ == "__main__":
    main()
