import json
import os
import time
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
PRIMARY_MODEL = "gemini-2.0-flash"
IMAGE_DIR = "STOLAR/bguw"

CHAIR_IDS = [
    "O129433", "O129434", "O129435", "O129437", "O1295279", "O129645", "O129647", "O129648", "O129649", "O129650", 
    "O129652", "O129653", "O129654", "O129655", "O129656", "O129657", "O129658", "O129659", "O129660", "O129662", 
    "O129668", "O1298370", "O1298377", "O1298378", "O1298379", "O1298380", "O1298384", "O129869", "O1299501", "O1299646", 
    "O129973", "O129974", "O1300057", "O1300058", "O130048", "O130101", "O130125", "O130130", "O130133", "O130182", 
    "O130191", "O130297", "O130378", "O130479", "O130512", "O130617", "O130645", "O130647", "O130651", "O130718"
]

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

def process_chair(chair_id):
    image_path = os.path.join(IMAGE_DIR, f"{chair_id}_bguw.png")
    if not os.path.exists(image_path):
        return chair_id, {"error": "File not found"}
    
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        while True:
            try:
                response = client.models.generate_content(
                    model=PRIMARY_MODEL,
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
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"Rate limit hit for {chair_id}, sleeping 15s...")
                    time.sleep(15)
                else:
                    raise e
    except Exception as e:
        print(f"Error processing {chair_id}: {e}")
        return chair_id, {"error": str(e)}

def main():
    results = {}
    print(f"Processing {len(CHAIR_IDS)} chairs sequentially...")
    for i, cid in enumerate(CHAIR_IDS):
        chair_id, res = process_chair(cid)
        results[chair_id] = res
        print(f"[{i+1}/{len(CHAIR_IDS)}] Processed {chair_id}")
        time.sleep(4.5) # ensure we don't exceed 15 requests/min
        
        # periodically save
        if (i+1) % 10 == 0:
            with open("batch_results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
    with open("batch_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Saved to batch_results.json")

if __name__ == "__main__":
    main()
