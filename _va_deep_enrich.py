import json, requests, time, sys
from pathlib import Path

BASE = Path(".")
data = json.loads((BASE / "_gap_analysis.json").read_text(encoding="utf-8"))

va_entries = {oid: v for oid, v in data.items() if "vam.ac.uk" in v.get("url", "")}
print(f"V&A entries to process: {len(va_entries)}")

results = {}
ok = fail = 0

for i, (oid, entry) in enumerate(va_entries.items()):
    # Extract object ID from URL
    url = entry["url"]
    obj_id = url.rstrip("/").split("/item/")[-1].split("/")[0] if "/item/" in url else oid
    
    try:
        r = requests.get(f"https://api.vam.ac.uk/v2/museumobject/{obj_id}", timeout=15)
        if r.status_code != 200:
            fail += 1
            continue
        rec = r.json().get("record", {})
        
        enriched = {}
        
        # Production dates
        dates = rec.get("productionDates", [])
        if dates:
            d = dates[0].get("date", {})
            if d.get("earliest"): enriched["year_from"] = int(d["earliest"][:4])
            if d.get("latest"): enriched["year_to"] = int(d["latest"][:4])
        
        # Credit line
        cl = rec.get("creditLine", "")
        if cl: enriched["credit_line"] = cl
        
        # Description
        bd = rec.get("briefDescription", "")
        if bd: enriched["brief_description"] = bd
        
        # Accession number
        an = rec.get("accessionNumber", "")
        if an: enriched["accession_number"] = an
        
        # IIIF
        iiif = rec.get("images", {}).get("_iiif_image", "")
        if iiif: enriched["iiif_url"] = iiif
        
        # Bibliography
        bib = rec.get("bibliographicReferences", [])
        if bib:
            enriched["bibliography"] = [b.get("text", b.get("title", "")) for b in bib if b.get("text") or b.get("title")]
        
        # Categories
        cats = rec.get("categories", [])
        if cats:
            enriched["categories"] = [c.get("text", "") for c in cats if c.get("text")]
        
        if enriched:
            results[oid] = enriched
            ok += 1
        
    except Exception as e:
        fail += 1
    
    if (i+1) % 100 == 0:
        print(f"  [{i+1}/{len(va_entries)}] ok={ok} fail={fail}")
        time.sleep(0.5)

(BASE / "_va_deep_enrichment.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nDone! {ok} enriched, {fail} failed. Wrote _va_deep_enrichment.json")
