import json
from pathlib import Path

BASE = Path(".")
data = json.loads((BASE / "_gap_analysis.json").read_text(encoding="utf-8"))

# Calibration: use existing weights
calibration = {oid: v["weight"] for oid, v in data.items() if v.get("weight") and v["weight"] > 0}
print(f"Calibration entries (with known weight): {len(calibration)}")

# Material density factors (kg per typical chair volume)
MATERIAL_WEIGHT = {
    "Eik": 12, "Oak": 12, "Mahogni": 13, "Mahogany": 13, "Valnott": 11, "Walnut": 11,
    "Bok": 10, "Beech": 10, "Bøk": 10, "Ask": 10, "Ash": 10, "Bjork": 9, "Birch": 9,
    "Furu": 8, "Pine": 8, "Tre": 9, "Wood": 9,
    "Kryssfiner": 7, "Plywood": 7, "Laminert": 7,
    "Stal": 10, "Steel": 10, "Stål": 10, "Jern": 12, "Iron": 12,
    "Aluminium": 5, "Aluminum": 5, "Krom": 8, "Chrome": 8, "Metall": 9, "Metal": 9,
    "Messing": 9, "Brass": 9, "Bronse": 10, "Bronze": 10,
    "Plast": 4, "Plastic": 4, "Polyester": 4, "Polyuretan": 5, "Glasfiber": 5, "Fiberglass": 5,
    "Akryl": 4, "Acrylic": 4,
    "Lar": 1.5, "Leather": 1.5, "Lær": 1.5, "Tekstil": 1, "Textile": 1, "Fabric": 1,
    "Silke": 0.5, "Silk": 0.5, "Flovel": 1, "Velvet": 1, "Bomull": 1, "Cotton": 1,
    "Rotting": 5, "Cane": 5, "Rattan": 5, "Bambus": 6, "Bamboo": 6,
    "Stein": 80, "Stone": 80, "Marmor": 80, "Marble": 80, "Betong": 70,
    "Glas": 8, "Glass": 8,
}

def estimate_weight(entry):
    h = entry.get("height")
    w = entry.get("width")
    d = entry.get("depth")
    mat_desc = entry.get("mat_desc", "") or ""
    materials = entry.get("materials", [])
    name = entry.get("name", "").lower()
    
    if not h or h <= 0:
        return None
    
    # Find primary material weight
    base_weight = 9  # default wood
    all_mats = " ".join(materials) + " " + mat_desc
    for mat_key, weight in MATERIAL_WEIGHT.items():
        if mat_key.lower() in all_mats.lower():
            base_weight = weight
            break
    
    # Size factor based on dimensions
    ref_h, ref_w, ref_d = 85, 50, 50  # reference chair
    h_factor = (h or ref_h) / ref_h
    w_factor = (w or ref_w) / ref_w
    d_factor = (d or ref_d) / ref_d
    size_factor = h_factor * w_factor * d_factor
    
    # Type adjustments
    if "krakk" in name or "stool" in name or "taburett" in name:
        size_factor *= 0.5
    elif "benk" in name or "bench" in name or "sofa" in name:
        size_factor *= 2.0
    elif "lenestol" in name or "armchair" in name:
        size_factor *= 1.2
    
    # Upholstery adds weight
    if any(x in all_mats.lower() for x in ["polstr", "upholster", "stoppet", "skumgummi", "foam"]):
        base_weight += 3
    
    estimated = round(base_weight * size_factor, 1)
    
    # Clamp to reasonable range
    if "stein" in all_mats.lower() or "stone" in all_mats.lower() or "betong" in all_mats.lower():
        estimated = max(estimated, 30)
    else:
        estimated = max(2, min(estimated, 50))
    
    return estimated

# Validate against known weights
errors = []
for oid, known in calibration.items():
    est = estimate_weight(data[oid])
    if est:
        errors.append(abs(est - known) / known)

if errors:
    avg_err = sum(errors) / len(errors)
    print(f"Validation: avg error = {avg_err:.1%} on {len(errors)} known weights")

# Estimate all missing
results = {}
for oid, entry in data.items():
    if entry.get("weight") and entry["weight"] > 0:
        continue  # already has weight
    est = estimate_weight(entry)
    if est:
        results[oid] = est

(BASE / "_weight_estimates.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Estimated weights for {len(results)} entries -> _weight_estimates.json")
