import json
import os
import time
import sys
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_TO_USE = "gemini-1.5-flash" 
IMAGE_DIR = "STOLAR/bguw"

ids = ["O120510", "O120512", "O120513", "O120517", "O120518", "O120519", "O120521", "O120525", "O120559", "O120564", "O120670", "O121005", "O121019", "O121083", "O121088", "O121090", "O121092", "O121095", "O121252", "O121254", "O121394", "O121399", "O121404", "O121407", "O121408", "O121411", "O121809", "O121810", "O122238", "O122243", "O122265", "O122269", "O122348", "O122351", "O1223755", "O122406", "O1224753", "O1224758", "O122530", "O122666", "O1226895", "O122700", "O1227035", "O1227036", "O1227389", "O1227489", "O123457", "O123539", "O123763", "O123775"]

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

Return ONLY a JSON object with these keys and the corresponding values for the chair shown in the image."""

def process_chair(chair_id):
    image_path = os.path.join(IMAGE_DIR, f"{chair_id}_bguw.png")
    if not os.path.exists(image_path):
        return chair_id, None
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_TO_USE,
                contents=[
                    PROMPT,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            data = json.loads(response.text)
            return chair_id, data
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                print(f"Rate limit hit for {chair_id}, retrying in 20 seconds...", file=sys.stderr)
                time.sleep(20)
            else:
                print(f"Error processing {chair_id}: {e}", file=sys.stderr)
                return chair_id, {"error": str(e)}

def main():
    results = {}
    print("{")
    first = True
    for chair_id in ids:
        cid, data = process_chair(chair_id)
        if data:
            results[cid] = data
            if not first:
                print(",")
            print(f'  "{cid}": {json.dumps(data)}', end="", flush=True)
            first = False
        time.sleep(5)  # Stay under 15 RPM
    print("\n}")

if __name__ == "__main__":
    main()
