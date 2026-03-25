"""
artikkel_VII_analyse.py
Compute peak profiles, composite indices, and Jaccard distances
for Artikkel VII: Det empiriske fitnesslandskapet.

All numbers feed directly into the LaTeX article.
"""

import csv
import math
from collections import Counter, defaultdict

# ── Load data ────────────────────────────────────────────────────
def load_data(path="stolar_db.csv"):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

# ── Helpers ──────────────────────────────────────────────────────
def parse_list(cell):
    """Split a comma-separated material/technique cell into a list of items."""
    if not cell or not cell.strip():
        return []
    return [x.strip() for x in cell.split(",") if x.strip()]

def shannon_entropy(items):
    """Shannon entropy H' in bits from a flat list of items."""
    if not items:
        return 0.0
    counts = Counter(items)
    total = sum(counts.values())
    h = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    return h

def cv(values):
    """Coefficient of variation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    var = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(var) / mean

def margalef(n_species, n_total):
    """Margalef richness index."""
    if n_total <= 1:
        return 0.0
    return (n_species - 1) / math.log(n_total)

def jaccard_distance(set_a, set_b):
    """Jaccard distance: 1 - |intersection| / |union|."""
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    if not union:
        return 0.0
    return 1.0 - len(set_a & set_b) / len(union)

def safe_float(s):
    """Parse a float, return None on failure."""
    try:
        return float(s.replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None

# ── Main analysis ────────────────────────────────────────────────
def main():
    rows = load_data()
    print(f"Total chairs loaded: {len(rows)}")

    # Group by style period
    style_groups = defaultdict(list)
    for r in rows:
        s = r.get("Stilperiode", "").strip()
        if s:
            style_groups[s].append(r)

    # Filter to styles with N >= 10
    MIN_N = 10
    styles = {k: v for k, v in style_groups.items() if len(v) >= MIN_N}
    print(f"\nStyles with N >= {MIN_N}: {len(styles)}")
    for s in sorted(styles, key=lambda x: -len(styles[x])):
        print(f"  {s}: {len(styles[s])}")

    # ── Compute per-style profiles ───────────────────────────────
    profiles = {}

    for style, chairs in styles.items():
        n = len(chairs)

        # 1. Material entropy H'
        all_materials = []
        material_sets_per_chair = []
        for c in chairs:
            mats = parse_list(c.get("Materialar", ""))
            all_materials.extend(mats)
            material_sets_per_chair.append(set(mats))
        h_mat = shannon_entropy(all_materials)

        # 2. Technique complexity T_c
        all_techniques = []
        technique_sets_per_chair = []
        for c in chairs:
            techs = parse_list(c.get("Teknikk", ""))
            all_techniques.extend(techs)
            technique_sets_per_chair.append(set(techs))
        t_c = shannon_entropy(all_techniques)

        # 3. Dimensional variance sigma_D (mean CV of H, W, D)
        heights = [safe_float(c.get("Høgde (cm)", "")) for c in chairs]
        widths = [safe_float(c.get("Breidde (cm)", "")) for c in chairs]
        depths = [safe_float(c.get("Djupn (cm)", "")) for c in chairs]
        heights = [h for h in heights if h is not None and h > 0]
        widths = [w for w in widths if w is not None and w > 0]
        depths = [d for d in depths if d is not None and d > 0]

        cv_h = cv(heights) if len(heights) >= 2 else 0
        cv_w = cv(widths) if len(widths) >= 2 else 0
        cv_d = cv(depths) if len(depths) >= 2 else 0
        sigma_d = (cv_h + cv_w + cv_d) / 3

        # 4. Geographic spread G_s (Margalef on nationalities)
        nationalities = [c.get("Nasjonalitet", "").strip() for c in chairs]
        nationalities = [x for x in nationalities if x]
        n_nat = len(set(nationalities))
        n_total_nat = len(nationalities)
        g_s = margalef(n_nat, n_total_nat) if n_total_nat > 1 else 0

        # 5. Material intensity I_m components
        weights = [safe_float(c.get("Estimert vekt (kg)", "")) for c in chairs]
        weights = [w for w in weights if w is not None and w > 0]
        mean_weight = sum(weights) / len(weights) if weights else 0

        mat_counts = [len(parse_list(c.get("Materialar", ""))) for c in chairs]
        mean_mat_count = sum(mat_counts) / len(mat_counts) if mat_counts else 0

        volumes = []
        for c in chairs:
            h = safe_float(c.get("Høgde (cm)", ""))
            w = safe_float(c.get("Breidde (cm)", ""))
            d = safe_float(c.get("Djupn (cm)", ""))
            if h and w and d and h > 0 and w > 0 and d > 0:
                volumes.append(h * w * d)
        mean_volume = sum(volumes) / len(volumes) if volumes else 0

        # Store mean height for chronological ordering
        mean_h = sum(heights) / len(heights) if heights else 0
        mean_w = sum(widths) / len(widths) if widths else 0

        profiles[style] = {
            "n": n,
            "h_mat": h_mat,
            "t_c": t_c,
            "sigma_d": sigma_d,
            "cv_h": cv_h,
            "cv_w": cv_w,
            "cv_d": cv_d,
            "g_s": g_s,
            "mean_weight": mean_weight,
            "mean_mat_count": mean_mat_count,
            "mean_volume": mean_volume,
            "mean_h": mean_h,
            "mean_w": mean_w,
            "n_nat": n_nat,
            "material_set": set(all_materials),
            "technique_set": set(all_techniques),
        }

    # ── Compute z-scores for I_m ─────────────────────────────────
    weight_vals = [p["mean_weight"] for p in profiles.values()]
    matc_vals = [p["mean_mat_count"] for p in profiles.values()]
    vol_vals = [p["mean_volume"] for p in profiles.values()]

    def z_score(vals, x):
        if len(vals) < 2:
            return 0
        mu = sum(vals) / len(vals)
        sd = math.sqrt(sum((v - mu) ** 2 for v in vals) / (len(vals) - 1))
        if sd == 0:
            return 0
        return (x - mu) / sd

    for style, p in profiles.items():
        z_w = z_score(weight_vals, p["mean_weight"])
        z_m = z_score(matc_vals, p["mean_mat_count"])
        z_v = z_score(vol_vals, p["mean_volume"])
        p["i_m"] = z_w + z_m + z_v

    # ── Compute Intensitetsindeks and Breiddeindeks ──────────────
    # Min-max normalize each of the 5 dimensions across all styles
    dims = ["h_mat", "t_c", "sigma_d", "g_s", "i_m"]
    mins = {d: min(p[d] for p in profiles.values()) for d in dims}
    maxs = {d: max(p[d] for p in profiles.values()) for d in dims}

    for style, p in profiles.items():
        norm_vals = []
        for d in dims:
            rng = maxs[d] - mins[d]
            if rng > 0:
                norm_vals.append((p[d] - mins[d]) / rng)
            else:
                norm_vals.append(0)
        p["norm_profile"] = norm_vals
        # Intensitetsindeks: Euclidean norm * 100 for readability
        p["intensitet"] = math.sqrt(sum(v ** 2 for v in norm_vals)) * 100
        # Breiddeindeks: sigma_D * G_s * 100
        p["breidde"] = p["sigma_d"] * p["g_s"] * 100

    # ── Print Table 2: Peak profiles ─────────────────────────────
    # Approximate chronological order
    chrono_order = [
        "Renessanse", "Barokk", "Régence", "Queen Anne", "Rokokko",
        "Hepplewhite", "Louis XVI", "Nyklassisisme", "Empire",
        "Historisme", "Jugend", "Funksjonalisme", "Modernisme",
        "Postmodernisme",
    ]
    ordered = [s for s in chrono_order if s in profiles]
    # Add any remaining
    for s in profiles:
        if s not in ordered:
            ordered.append(s)

    print("\n" + "=" * 90)
    print("TABLE 2: PEAK PROFILES (Toppprofiltabellen)")
    print("=" * 90)
    header = f"{'Stil':<20} {'N':>4} {'H_mat':>6} {'T_c':>6} {'sig_D':>6} {'G_s':>6} {'I_m':>7} {'Intens':>7} {'Breidd':>7}"
    print(header)
    print("-" * 90)
    for s in ordered:
        p = profiles[s]
        print(f"{s:<20} {p['n']:>4} {p['h_mat']:>6.2f} {p['t_c']:>6.2f} {p['sigma_d']:>6.3f} {p['g_s']:>6.3f} {p['i_m']:>7.2f} {p['intensitet']:>7.1f} {p['breidde']:>7.2f}")

    # ── Print Table 2b: Supplementary dimensional info ───────────
    print("\n" + "=" * 90)
    print("SUPPLEMENTARY: Mean dimensions per style")
    print("=" * 90)
    header2 = f"{'Stil':<20} {'N':>4} {'H_bar':>7} {'W_bar':>7} {'CV_H':>7} {'CV_W':>7} {'CV_D':>7} {'Wt_bar':>7} {'MatCnt':>7} {'Vol_bar':>9}"
    print(header2)
    print("-" * 90)
    for s in ordered:
        p = profiles[s]
        print(f"{s:<20} {p['n']:>4} {p['mean_h']:>7.1f} {p['mean_w']:>7.1f} {p['cv_h']:>7.3f} {p['cv_w']:>7.3f} {p['cv_d']:>7.3f} {p['mean_weight']:>7.1f} {p['mean_mat_count']:>7.1f} {p['mean_volume']:>9.0f}")

    # ── Compute Jaccard distances between adjacent styles ────────
    print("\n" + "=" * 90)
    print("TABLE 3: JACCARD DISTANCES BETWEEN ADJACENT STYLES")
    print("=" * 90)
    header3 = f"{'Stilpar':<40} {'J_mat':>7} {'J_tekn':>7} {'dH_mat':>7}"
    print(header3)
    print("-" * 90)
    for i in range(len(ordered) - 1):
        s1, s2 = ordered[i], ordered[i + 1]
        p1, p2 = profiles[s1], profiles[s2]
        j_mat = jaccard_distance(p1["material_set"], p2["material_set"])
        j_tekn = jaccard_distance(p1["technique_set"], p2["technique_set"])
        dh = abs(p2["h_mat"] - p1["h_mat"])
        label = f"{s1} -> {s2}"
        print(f"{label:<40} {j_mat:>7.3f} {j_tekn:>7.3f} {dh:>7.2f}")

    # ── Identify top 5 landscape shifts (highest combined Jaccard) ─
    shifts = []
    for i in range(len(ordered) - 1):
        s1, s2 = ordered[i], ordered[i + 1]
        p1, p2 = profiles[s1], profiles[s2]
        j_mat = jaccard_distance(p1["material_set"], p2["material_set"])
        j_tekn = jaccard_distance(p1["technique_set"], p2["technique_set"])
        j_combined = (j_mat + j_tekn) / 2
        shifts.append((s1, s2, j_mat, j_tekn, j_combined))

    shifts.sort(key=lambda x: -x[4])
    print("\n" + "=" * 90)
    print("TOP 5 LANDSCAPE SHIFTS (by combined Jaccard)")
    print("=" * 90)
    for s1, s2, jm, jt, jc in shifts[:5]:
        print(f"  {s1} -> {s2}: J_mat={jm:.3f}, J_tekn={jt:.3f}, combined={jc:.3f}")

    # ── Print LaTeX-ready table fragments ────────────────────────
    print("\n" + "=" * 90)
    print("LATEX TABLE 2 (copy-paste ready)")
    print("=" * 90)
    for s in ordered:
        p = profiles[s]
        name = s.replace("é", "\\'{e}")
        print(f"{name} & {p['n']} & {p['h_mat']:.2f} & {p['t_c']:.2f} & {p['sigma_d']:.3f} & {p['g_s']:.3f} & {p['i_m']:.2f} & {p['intensitet']:.1f} & {p['breidde']:.2f} \\\\")

    print("\n" + "=" * 90)
    print("LATEX TABLE 3 (copy-paste ready)")
    print("=" * 90)
    for i in range(len(ordered) - 1):
        s1, s2 = ordered[i], ordered[i + 1]
        p1, p2 = profiles[s1], profiles[s2]
        j_mat = jaccard_distance(p1["material_set"], p2["material_set"])
        j_tekn = jaccard_distance(p1["technique_set"], p2["technique_set"])
        dh = abs(p2["h_mat"] - p1["h_mat"])
        s1_name = s1.replace("é", "\\'{e}")
        s2_name = s2.replace("é", "\\'{e}")
        print(f"{s1_name} $\\rightarrow$ {s2_name} & {j_mat:.3f} & {j_tekn:.3f} & {dh:.2f} \\\\")

if __name__ == "__main__":
    main()
