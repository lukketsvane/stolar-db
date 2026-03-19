#!/usr/bin/env python3
"""
Final weight estimation generator.
Handles dimension unit detection (mm vs cm), miniatures, and edge cases.
"""
import json
import math

def load_data():
    with open('_gap_analysis.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# Material classifications (Norwegian names)
HARDWOOD = {'eik', 'b\u00f8k', 'ask', 'bj\u00f8rk', 'alm', 'mahogni',
            'n\u00f8ttetre', 'palisander', 'ibenholt', 'teak', 'buksbom',
            'l\u00f8nn', 'l\u00f8vtre', 'p\u00e6retre'}
SOFTWOOD = {'furu', 'gran', 'lind', 'palme', 'bambus'}
GENERIC_WOOD = {'tre'}
ENGINEERED_WOOD = {'kryssfiner', 'finer', 'sponplate'}
METAL_STRUCTURAL = {'st\u00e5l', 'st\u00e5lr\u00f8r', 'jern', 'aluminium', 'metall'}
METAL_DECORATIVE = {'messing', 'bronse', 's\u00f8lv'}
PLASTICS = {'plast', 'glasfiber', 'polypropylen', 'polyuretan', 'polyetylen',
            'polyamid', 'polyester', 'polykarbonat', 'melamin'}
UPHOLSTERY_HEAVY = {'l\u00e6r', 'skinn', 'skumplast', 'gummi', 'kunstl\u00e6r'}
UPHOLSTERY_LIGHT = {'ull', 'silke', 'tekstil', 'bomull', 'fl\u00f8yel', 'lin',
                     'hestetagl', 'plysj', 'strie', 'stramei', 'lerret',
                     'rotting', 'str\u00e5', 'sadelgjord', 'papir', 'papirsnor',
                     'pappmasj\u00e9', 'syntetisk fiber', 'kunstsilke',
                     'vegetabilsk fiber', 'filt', 'gyllenl\u00e6r'}
HEAVY_MATERIALS = {'betong', 'marmor', 'naturstein'}
DECORATIVE = {'maling', 'voks', 'perlemor', 'emalje', 'linoleum'}

ALL_WOOD = HARDWOOD | SOFTWOOD | GENERIC_WOOD | ENGINEERED_WOOD


def get_primary_structure(materials):
    """Determine the primary structural material type."""
    mats_lower = [m.lower().strip() for m in materials]

    has_heavy = any(m in HEAVY_MATERIALS for m in mats_lower)
    has_metal_struct = any(m in METAL_STRUCTURAL for m in mats_lower)
    has_hardwood = any(m in HARDWOOD for m in mats_lower)
    has_softwood = any(m in SOFTWOOD for m in mats_lower)
    has_generic_wood = any(m in GENERIC_WOOD for m in mats_lower)
    has_engineered = any(m in ENGINEERED_WOOD for m in mats_lower)
    has_plastic = any(m in PLASTICS for m in mats_lower)
    has_heavy_uph = any(m in UPHOLSTERY_HEAVY for m in mats_lower)
    has_light_uph = any(m in UPHOLSTERY_LIGHT for m in mats_lower)
    has_any_wood = has_hardwood or has_softwood or has_generic_wood or has_engineered

    if has_heavy:
        return 'heavy'
    elif has_metal_struct and not has_any_wood:
        return 'metal_only'
    elif has_metal_struct and has_any_wood:
        return 'metal_wood_mix'
    elif has_hardwood and has_engineered:
        return 'hardwood_engineered'
    elif has_hardwood:
        if has_heavy_uph:
            return 'hardwood_upholstered_heavy'
        elif has_light_uph:
            return 'hardwood_upholstered_light'
        else:
            return 'hardwood_plain'
    elif has_softwood:
        if has_heavy_uph or has_light_uph:
            return 'softwood_upholstered'
        else:
            return 'softwood_plain'
    elif has_generic_wood:
        if has_heavy_uph or has_light_uph:
            return 'generic_wood_upholstered'
        else:
            return 'generic_wood_plain'
    elif has_engineered:
        return 'engineered'
    elif has_plastic:
        return 'plastic'
    elif has_heavy_uph or has_light_uph:
        return 'upholstery_only'
    else:
        return 'unknown'


def normalize_dimensions(height, width, depth):
    """
    Detect if dimensions are likely in mm and convert to cm.
    Most chairs are 40-130 cm tall. If height > 200, likely mm.
    Also handle benches which can be wider/longer.
    """
    h = height
    w = width
    d = depth

    # Check if dimensions look like mm
    # A chair > 250 cm is extremely unlikely unless it's a bench
    # But a bench at 250 cm wide is plausible
    # Focus on height: chairs are almost never > 200 cm tall
    if h and h > 250:
        # Likely mm, convert to cm
        h = h / 10
        if w: w = w / 10
        if d: d = d / 10

    return h, w, d


def build_calibration_coefficients(data):
    """Build category-based weight coefficients from known-weight entries."""
    calibration = {k:v for k,v in data.items()
                   if v.get('weight') is not None and v.get('weight') > 0
                   and v.get('height') is not None and v.get('height') > 10
                   and v.get('materials') and len(v['materials']) > 0}

    ref_vol = 90 * 45 * 45
    categories = {}

    for k, v in calibration.items():
        cat = get_primary_structure(v['materials'])
        h, w, d = normalize_dimensions(
            v['height'],
            v.get('width') or v['height'] * 0.52,
            v.get('depth') or v['height'] * 0.52
        )
        if w == 0: w = h * 0.52
        if d == 0: d = h * 0.52

        volume = h * w * d
        if volume <= 0:
            continue

        vol_factor = (volume / ref_vol) ** 0.7
        coeff = v['weight'] / vol_factor

        if cat not in categories:
            categories[cat] = []
        categories[cat].append(coeff)

    # Compute median coefficient per category
    coefficients = {}
    for cat, coeffs in categories.items():
        if len(coeffs) >= 2:
            coeffs.sort()
            coefficients[cat] = coeffs[len(coeffs) // 2]
        elif len(coeffs) == 1:
            # For single-entry categories, only use if reasonable
            # Skip extreme outliers (like a single solid bronze piece)
            if coeffs[0] < 50:
                coefficients[cat] = coeffs[0]

    # Define fallback chain for categories with insufficient data
    fallback_map = {
        'softwood_plain': 'hardwood_plain',
        'softwood_upholstered': 'hardwood_upholstered_light',
        'generic_wood_plain': 'hardwood_plain',
        'generic_wood_upholstered': 'hardwood_upholstered_light',
        'upholstery_only': 'hardwood_upholstered_light',
        'unknown': 'hardwood_upholstered_light',
        'heavy': 'metal_only',  # will be overridden for stone
    }

    # Fill in missing categories with fallbacks
    for cat, fallback in fallback_map.items():
        if cat not in coefficients and fallback in coefficients:
            coefficients[cat] = coefficients[fallback]

    return coefficients


def estimate_weight(entry, coefficients):
    """Estimate weight for a single entry."""
    height = entry.get('height')
    width = entry.get('width')
    depth = entry.get('depth')
    materials = entry.get('materials', [])
    seat_h = entry.get('seat_h')
    entry_type = (entry.get('type', '') or '').lower()
    style = (entry.get('style', '') or '').lower()
    name = (entry.get('name', '') or '').lower()
    mat_desc = (entry.get('mat_desc', '') or '').lower()

    if height is None or height <= 0 or not materials:
        return None

    # Normalize dimensions (mm -> cm if needed)
    h, w, d = normalize_dimensions(height, width, depth)

    # Handle missing width/depth
    if w is None or w == 0:
        w = h * 0.52
    if d is None or d == 0:
        d = h * 0.52

    ref_vol = 90 * 45 * 45
    volume = h * w * d
    if volume <= 0:
        return None
    vol_factor = (volume / ref_vol) ** 0.7

    # Get primary structure category
    cat = get_primary_structure(materials)

    # Special handling for heavy materials (stone, concrete, marble)
    mats_lower = [m.lower().strip() for m in materials]
    if cat == 'heavy':
        # Stone/concrete: much denser, use volume-based estimation
        # Chair shape is not solid - use fill factor
        has_stone = any(m in ('marmor', 'naturstein') for m in mats_lower)
        has_concrete = any(m in ('betong',) for m in mats_lower)
        if has_stone:
            fill_factor = 0.12
            density_gcm3 = 2.7  # marble density
        elif has_concrete:
            fill_factor = 0.14
            density_gcm3 = 2.3  # concrete density
        else:
            fill_factor = 0.12
            density_gcm3 = 2.3
        weight_g = volume * fill_factor * density_gcm3
        weight_kg = weight_g / 1000
        # Clamp heavy items
        weight_kg = min(150, max(5, weight_kg))
        return round(weight_kg, 1)

    # For metal-only items, use the standard coefficient approach
    # (the solid metal path was removed as it over-estimated iron-frame chairs)

    # Look up coefficient
    if cat in coefficients:
        coeff = coefficients[cat]
    else:
        # Global fallback
        all_coeffs = sorted(coefficients.values())
        coeff = all_coeffs[len(all_coeffs) // 2]

    base_weight = coeff * vol_factor

    # Detect special types
    is_stool = ('krakk' in name or 'taburett' in name or 'stol utan rygg' in entry_type
                or 'uten rygg' in entry_type or 'krakk' in entry_type or 'taburett' in entry_type
                or 'krakk' in mat_desc or 'taburett' in mat_desc)
    is_bench = ('benk' in name or 'benk' in entry_type or 'sofa' in name or 'sofa' in entry_type)
    is_armchair = ('armstol' in name or 'lenestol' in name or 'armstol' in entry_type
                   or 'lenestol' in entry_type or 'armchair' in name)

    # Check seat height vs total height for stools
    if seat_h and h and seat_h > 0:
        if (h - seat_h) < 8:
            is_stool = True

    # Miniature detection
    if h < 15:
        # Very small - likely a model/miniature
        base_weight *= 0.03
    elif h < 25 and w < 25:
        base_weight *= 0.08
    elif h < 40 and w and w < 35:
        base_weight *= 0.35

    # Type adjustments
    if is_stool and not is_bench:
        base_weight *= 0.65
    if is_armchair:
        base_weight *= 1.10

    # Style adjustments (mild)
    if style in ('barokk', 'r\u00e9gence'):
        base_weight *= 1.08
    elif style in ('funksjonalisme', 'postmodernisme'):
        base_weight *= 0.95

    # Clamp to reasonable range
    if h >= 30:
        base_weight = max(1.5, base_weight)
    elif h >= 15:
        base_weight = max(0.3, base_weight)
    else:
        base_weight = max(0.1, base_weight)

    # Upper clamp depends on size
    if h < 50:
        base_weight = min(30, base_weight)
    elif h < 100:
        base_weight = min(60, base_weight)
    elif h < 200:
        base_weight = min(100, base_weight)
    else:
        base_weight = min(150, base_weight)

    return round(base_weight, 1)


def main():
    data = load_data()
    coefficients = build_calibration_coefficients(data)

    print("Category coefficients:")
    for cat, coeff in sorted(coefficients.items()):
        print(f"  {cat}: {coeff:.2f}")

    # Validate on calibration data
    calibration = {k:v for k,v in data.items()
                   if v.get('weight') is not None and v.get('weight') > 0
                   and v.get('height') is not None and v.get('height') > 0
                   and v.get('materials') and len(v['materials']) > 0}

    pct_errors = []
    abs_errors = []
    for k, v in calibration.items():
        actual = v['weight']
        est = estimate_weight(v, coefficients)
        if est is None:
            continue
        abs_err = abs(est - actual)
        pct_err = abs_err / actual * 100 if actual > 0 else 0
        pct_errors.append(pct_err)
        abs_errors.append(abs_err)

    pct_errors.sort()
    abs_errors.sort()
    print(f"\nValidation ({len(pct_errors)} entries):")
    print(f"  Median absolute % error: {pct_errors[len(pct_errors)//2]:.1f}%")
    print(f"  Mean absolute % error: {sum(pct_errors)/len(pct_errors):.1f}%")
    print(f"  Median absolute error: {abs_errors[len(abs_errors)//2]:.1f} kg")
    print(f"  Within 20%: {sum(1 for e in pct_errors if e <= 20)}/{len(pct_errors)} ({sum(1 for e in pct_errors if e <= 20)/len(pct_errors)*100:.0f}%)")
    print(f"  Within 30%: {sum(1 for e in pct_errors if e <= 30)}/{len(pct_errors)} ({sum(1 for e in pct_errors if e <= 30)/len(pct_errors)*100:.0f}%)")
    print(f"  Within 50%: {sum(1 for e in pct_errors if e <= 50)}/{len(pct_errors)} ({sum(1 for e in pct_errors if e <= 50)/len(pct_errors)*100:.0f}%)")

    # Generate estimates for all entries without weight
    to_estimate = {k:v for k,v in data.items()
                   if (v.get('weight') is None or v.get('weight') == 0)
                   and v.get('height') is not None and v.get('height') > 0
                   and v.get('materials') and len(v['materials']) > 0}

    estimates = {}
    for k, v in to_estimate.items():
        est = estimate_weight(v, coefficients)
        if est is not None and est > 0:
            estimates[k] = est

    # Distribution
    est_values = sorted(estimates.values())
    print(f"\nGenerated {len(estimates)} estimates")
    print(f"  Min: {min(est_values):.1f}, Max: {max(est_values):.1f}")
    print(f"  Mean: {sum(est_values)/len(est_values):.1f}, Median: {est_values[len(est_values)//2]:.1f}")
    print(f"  < 5 kg: {sum(1 for v in est_values if v < 5)}")
    print(f"  5-10 kg: {sum(1 for v in est_values if 5 <= v < 10)}")
    print(f"  10-20 kg: {sum(1 for v in est_values if 10 <= v < 20)}")
    print(f"  20-30 kg: {sum(1 for v in est_values if 20 <= v < 30)}")
    print(f"  30-50 kg: {sum(1 for v in est_values if 30 <= v < 50)}")
    print(f"  50+ kg: {sum(1 for v in est_values if v >= 50)}")

    # Entries still not estimated
    still_missing = [k for k in data if (data[k].get('weight') is None or data[k].get('weight') == 0)
                     and k not in estimates]
    print(f"\nStill not estimated: {len(still_missing)}")
    print(f"  Of those, height=0 or None: {sum(1 for k in still_missing if not data[k].get('height') or data[k].get('height') <= 0)}")

    # Save
    with open('_weight_estimates.json', 'w', encoding='utf-8') as f:
        json.dump(estimates, f, indent=2, ensure_ascii=False, sort_keys=True)

    print(f"\nSaved {len(estimates)} estimates to _weight_estimates.json")

    # Sample outputs
    print("\n=== SAMPLE: Heaviest estimates ===")
    for k in sorted(estimates, key=lambda x: estimates[x], reverse=True)[:10]:
        v = data[k]
        h, w, d = normalize_dimensions(v.get('height'), v.get('width'), v.get('depth'))
        print(f"  {k}: {estimates[k]}kg, h={h}, w={w}, d={d}, cat={get_primary_structure(v['materials'])}, mats={v.get('materials')}")

    print("\n=== SAMPLE: Lightest estimates ===")
    for k in sorted(estimates, key=lambda x: estimates[x])[:10]:
        v = data[k]
        print(f"  {k}: {estimates[k]}kg, h={v.get('height')}, w={v.get('width')}, d={v.get('depth')}, cat={get_primary_structure(v['materials'])}, mats={v.get('materials')}")

    print("\n=== SAMPLE: Typical chairs (10-15 kg range) ===")
    typical = [(k, estimates[k]) for k in estimates if 10 <= estimates[k] <= 15]
    for k, est in typical[:15]:
        v = data[k]
        mats = ', '.join(v.get('materials', []))
        print(f"  {k}: {est}kg, dims={v.get('height')}x{v.get('width')}x{v.get('depth')}cm, style={v.get('style','')}, mats=[{mats}]")


if __name__ == '__main__':
    main()
