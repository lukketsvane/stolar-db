import requests
import json
import time
import pandas as pd
import os

def fetch_va_heights():
    # Load the list of objects missing height
    df_missing = pd.read_csv('missing_heights_to_research.csv')
    va_ids = df_missing['Objekt-ID'].tolist()
    
    results = {}
    total = len(va_ids)
    
    print(f"Starting API fetch for {total} V&A objects...")
    
    for i, obj_id in enumerate(va_ids):
        # Only process V&A IDs (starting with O)
        if not str(obj_id).startswith('O'):
            continue
            
        url = f"https://www.vam.ac.uk/api/json/museumobject/{obj_id}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # The height is usually in dimensions[0] or similar
                # Let's try to find it in the data
                # Typically: data[0]['fields']['dimensions']
                if isinstance(data, list) and len(data) > 0:
                    fields = data[0].get('fields', {})
                    dimensions = fields.get('dimensions', '')
                    # Dimensions is a string like "Height: 85.5 cm, Width: 45 cm..."
                    # Extract height
                    import re
                    match = re.search(r'Height:\s*([\d\.,]+)\s*cm', dimensions, re.IGNORECASE)
                    if match:
                        height = float(match.group(1).replace(',', '.'))
                        results[obj_id] = height
                        print(f"[{i+1}/{total}] {obj_id}: {height} cm")
                    else:
                        # Try mm
                        match_mm = re.search(r'Height:\s*([\d\.,]+)\s*mm', dimensions, re.IGNORECASE)
                        if match_mm:
                            height = float(match_mm.group(1).replace(',', '.')) / 10.0
                            results[obj_id] = height
                            print(f"[{i+1}/{total}] {obj_id}: {height} cm (from mm)")
                        else:
                            print(f"[{i+1}/{total}] {obj_id}: No height found in dimensions: {dimensions[:50]}")
                else:
                    print(f"[{i+1}/{total}] {obj_id}: Unexpected API response format")
            else:
                print(f"[{i+1}/{total}] {obj_id}: API error {response.status_code}")
        except Exception as e:
            print(f"[{i+1}/{total}] {obj_id}: Exception: {e}")
        
        # Be nice to the API
        time.sleep(0.1)
        
    # Save results
    with open('va_heights_discovered.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nFinished! Discovered heights for {len(results)} objects.")

if __name__ == "__main__":
    fetch_va_heights()
