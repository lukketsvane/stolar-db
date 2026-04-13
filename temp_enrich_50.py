import json
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash"

IMAGE_DIR = "STOLAR/bguw"
IDS = ["O1240871", "O1240872", "O1240918", "O1241466", "O1242902", "O1243278", "O1243279", "O1243361", "O124593", "O1247425", "O1248498", "O1249163", "O125191", "O125408", "O1254532", "O1254906", "O125676", "O1257436", "O125998", "O126103", "O1263993", "O1264771", "O1265378", "O126577", "O1266680", "O126915", "O127300", "O127328", "O1273289", "O1273291", "O1273341", "O1273517", "O1273522", "O127517", "O127523", "O127526", "O127527", "O127576", "O1282899", "O128483", "O128816", "O129250", "O129264", "O129265", "O129267", "O129268", "O129269", "O129305", "O129353", "O129431"]

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
        return None
    
    while True:
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            response = client.models.generate_content(
                model=MODEL,
                contents=[
                    PROMPT,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            try:
                result = json.loads(response.text)
                return result
            except Exception as e:
                print(f"JSON Parse error for {chair_id}")
                return None
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"Rate limited on {chair_id}, sleeping 30s...")
                time.sleep(30)
            else:
                print(f"Error on {chair_id}: {e}")
                return None

def main():
    results = {}
    
    if os.path.exists("temp_output.json"):
        with open("temp_output.json", "r", encoding="utf-8") as f:
            try:
                results = json.load(f)
            except:
                pass
            
    for cid in IDS:
        if cid in results and results[cid]:
            continue
        print(f"Processing {cid}...")
        res = process_chair(cid)
        if res:
            results[cid] = res
            with open("temp_output.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        time.sleep(4.1) # 15 requests per minute -> ~4 sec per request
    print("Finished processing.")

if __name__ == "__main__":
    main()
