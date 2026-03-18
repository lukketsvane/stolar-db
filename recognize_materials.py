import os
import json
import requests
import time
import base64
import concurrent.futures
import threading

# Load env vars
NOTION_TOKEN = ""
GEMINI_API_KEY = ""
with open(".env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("NOTION_API_KEY="):
            NOTION_TOKEN = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("GEMINI_API_KEY="):
            GEMINI_API_KEY = line.split("=", 1)[1].strip().strip('"')

DATABASE_ID = "405e0f646b774aab88b873281e58c4f0"
NOTION_HDR = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

# 1. Fetch vocabulary
def get_vocabulary():
    r_db = requests.get(f"https://api.notion.com/v1/databases/{DATABASE_ID}", headers=NOTION_HDR)
    db_data = r_db.json()
    mat_prop = db_data.get("properties", {}).get("Materialar", {})
    if "multi_select" in mat_prop:
        return [opt["name"] for opt in mat_prop["multi_select"].get("options", [])]
    return []

# 2. Query empty Materialar AND empty Materialkommentar
def get_candidates():
    candidates = []
    has_more = True
    cursor = None
    while has_more:
        body = {
            "filter": {
                "and": [
                    {
                        "property": "Materialar",
                        "multi_select": {
                            "is_empty": True
                        }
                    },
                    {
                        "property": "Materialkommentar",
                        "rich_text": {
                            "is_empty": True
                        }
                    }
                ]
            },
            "page_size": 100
        }
        if cursor:
            body["start_cursor"] = cursor
            
        r = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=NOTION_HDR, json=body)
        data = r.json()
        
        for page in data.get("results", []):
            props = page["properties"]
            
            img_url = None
            if "Bilete-URL" in props and props["Bilete-URL"].get("url"):
                img_url = props["Bilete-URL"]["url"]
            elif "Bilete-bguw" in props and props["Bilete-bguw"]["files"]:
                f = props["Bilete-bguw"]["files"][0]
                img_url = f.get("file", {}).get("url") or f.get("external", {}).get("url")
            elif "Files & media" in props and props["Files & media"]["files"]:
                f = props["Files & media"]["files"][0]
                img_url = f.get("file", {}).get("url") or f.get("external", {}).get("url")
                
            if img_url:
                candidates.append({
                    "id": page["id"],
                    "oid": "".join(t["plain_text"] for t in props.get("Objekt-ID", {}).get("rich_text", [])),
                    "img_url": img_url,
                })
                
        has_more = data.get("has_more", False)
        cursor = data.get("next_cursor")
        
    return candidates

# 3. Analyze image with Gemini REST API
def analyze_image(img_url, vocab):
    try:
        resp = requests.get(img_url, timeout=15)
        resp.raise_for_status()
        img_bytes = resp.content
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    except Exception as e:
        safe_print(f"Failed to download image: {e}")
        return None
        
    prompt = f"""
Du er en ekspert på møbelhistorie og materialer (katalogisering på museum). Analyser dette bildet av en stol/møbel.
Din oppgave:
1. Identifiser materialene. Velg KUN fra denne listen av tillatte materialer: {', '.join(vocab)}.
2. Skriv en kort, museumsaktig 'Materialkommentar' på norsk (bokmål) som beskriver materialene, overflatebehandling (f.eks. malt, beiset, fernissert, lakkert) og konstruksjonen (f.eks. dreid, skåret, polstret sete, flettet).
Eksempler på gode kommentarer:
- "Fernissert alm med skåret dekor og hestehårstrekk."
- "Bøk med skåret dekor og lærtrekk."
- "Svartlakkert tre, profilert, skåret og dreid dekor, polstret, silketrekk, bronselister."
- "Dreid og skåret bøk, polstret sete trukket med ullstoff."

Returner et JSON-objekt med følgende struktur:
{{
  "materials": [
    {{
      "name": "Materialnavn fra listen",
      "confidence": 0.95,
      "reasoning": "Hvorfor du tror dette materialet er brukt"
    }}
  ],
  "kommentar": "Din kortfattede beskrivelse her."
}}
Returner KUN gyldig JSON. Ikke bruk markdown som ```json.
"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": img_b64
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        if r.status_code == 429:
             time.sleep(2) # Backoff for Gemini rate limit
             r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        r.raise_for_status()
        data = r.json()
        
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        return json.loads(text.strip())
    except Exception as e:
        safe_print(f"Gemini error: {e}")
        if 'r' in locals() and r.status_code != 200:
            safe_print(f"Response: {r.text}")
        return None

# 4. Update Notion
def update_notion(page_id, materials_to_add, generated_comment):
    payload = {
        "properties": {}
    }
    
    if materials_to_add:
        payload["properties"]["Materialar"] = {
            "multi_select": [{"name": m} for m in materials_to_add]
        }
        
    if generated_comment:
        payload["properties"]["Materialkommentar"] = {
            "rich_text": [{"text": {"content": f"[AI] {generated_comment}"}}]
        }
        
    for attempt in range(4):
        r = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=NOTION_HDR, json=payload)
        if r.status_code == 200:
            return True
        elif r.status_code == 429:
            time.sleep(2 * (attempt + 1)) # Backoff for Notion rate limit
        else:
            safe_print(f"Notion update failed: {r.text}")
            return False
    return False


def process_candidate(cand, vocab, index, total):
    safe_print(f"\n[{index}/{total}] Behandler {cand['oid']}...")
    result = analyze_image(cand["img_url"], vocab)
    
    if not result or "materials" not in result or "kommentar" not in result:
        safe_print(f"[{cand['oid']}] ❌ Kunne ikke analysere bilde eller uventet JSON-format.")
        return
        
    materials_to_add = []
    for m in result.get("materials", []):
        name = m.get("name")
        conf = m.get("confidence", 0)
        
        if name in vocab and conf >= 0.85:
            materials_to_add.append(name)
            
    kommentar = result.get("kommentar", "").strip()
    
    safe_print(f"[{cand['oid']}] AI Foreslåtte materialer: {materials_to_add}")
    safe_print(f"[{cand['oid']}] AI Foreslått kommentar: {kommentar}")
    
    ok = update_notion(cand["id"], materials_to_add, kommentar)
    if ok:
        safe_print(f"[{cand['oid']}] ✅ Oppdatert i Notion!")
    else:
        safe_print(f"[{cand['oid']}] ❌ Feil ved oppdatering.")


def main():
    safe_print("Henter vokabular for Materialar...")
    vocab = get_vocabulary()
    safe_print(f"Fant {len(vocab)} materialer i vokabularet.")
    
    safe_print("Finner kandidater der BÅDE 'Materialar' og 'Materialkommentar' er tomme...")
    candidates = get_candidates()
    safe_print(f"Fant {len(candidates)} kandidater.")
    
    if not candidates:
        safe_print("Ingen kandidater å behandle. Avslutter.")
        return

    safe_print(f"\nStarter parallell prosessering av {len(candidates)} kandidater...")
    
    # Using 5 workers to speed up but not hit Notion 3 req/sec limit too hard
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i, cand in enumerate(candidates):
            futures.append(executor.submit(process_candidate, cand, vocab, i+1, len(candidates)))
            
        # Wait for all to complete
        concurrent.futures.wait(futures)

    safe_print("\nFerdig med alle kandidater!")

if __name__ == "__main__":
    main()
