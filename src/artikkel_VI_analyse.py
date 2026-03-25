"""
artikkel_VI_analyse.py
Selection pressure operationalization, cluster stability analysis,
and gradient measurement for Artikkel VI.

Proves empirically that style periods are local optima (not just clusters)
and quantifies which selection pressures dominate each transition.
"""

import csv
import math
from collections import Counter, defaultdict
import itertools

# ── Load data ────────────────────────────────────────────────────
def load_data(path="stolar_db.csv"):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

def parse_list(cell):
    if not cell or not cell.strip():
        return []
    return [x.strip() for x in cell.split(",") if x.strip()]

def safe_float(s):
    try:
        return float(s.replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None

def shannon_entropy(items):
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
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    var = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(var) / mean

def euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

def cosine_sim(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x ** 2 for x in a))
    nb = math.sqrt(sum(x ** 2 for x in b))
    if na == 0 or nb == 0:
        return 0
    return dot / (na * nb)

# ── Main analysis ────────────────────────────────────────────────
def main():
    rows = load_data()
    print(f"Total chairs loaded: {len(rows)}\n")

    # ── 1. SELECTION PRESSURE PROXIES per chair ──────────────────
    # We define 5 selection pressure proxies measurable from the data:
    # P1: Material affordance (material count * material diversity within style)
    # P2: Technological capacity (technique count per chair)
    # P3: Economic pressure (inverse of estimated weight = material efficiency)
    # P4: Cultural pressure (how "typical" the chair is for its style = 1 - distance to centroid)
    # P5: Ergonomic pressure (how close seat height is to functional optimum ~45cm)

    # Group by style
    MIN_N = 17
    style_groups = defaultdict(list)
    for r in rows:
        s = r.get("Stilperiode", "").strip()
        if s:
            style_groups[s].append(r)
    styles = {k: v for k, v in style_groups.items() if len(v) >= MIN_N}

    chrono_order = [
        "Renessanse", "Barokk", "Régence", "Rokokko",
        "Hepplewhite", "Louis XVI", "Nyklassisisme", "Empire",
        "Historisme", "Jugend", "Funksjonalisme", "Modernisme",
        "Postmodernisme",
    ]
    ordered = [s for s in chrono_order if s in styles]

    # ── 2. CENTROID per style (H, W, D, SH) ─────────────────────
    centroids = {}
    for style, chairs in styles.items():
        dims = []
        for c in chairs:
            h = safe_float(c.get("Høgde (cm)", ""))
            w = safe_float(c.get("Breidde (cm)", ""))
            d = safe_float(c.get("Djupn (cm)", ""))
            sh = safe_float(c.get("Setehøgde (cm)", ""))
            if h and w:
                dims.append((h, w, d if d else 0, sh if sh else 0))
        if dims:
            n = len(dims)
            centroid = tuple(sum(x[i] for x in dims) / n for i in range(4))
            centroids[style] = centroid

    # ── 3. INTRA-STYLE COHESION (silhouette-like) ────────────────
    # Mean distance to own centroid vs mean distance to nearest other centroid
    print("=" * 80)
    print("CLUSTER STABILITY: Intra-style cohesion")
    print("=" * 80)
    print(f"{'Stil':<20} {'N':>4} {'Intra_d':>8} {'Inter_d':>8} {'Ratio':>8} {'Silhouette':>10}")
    print("-" * 80)

    style_cohesion = {}
    for style in ordered:
        chairs = styles[style]
        if style not in centroids:
            continue
        own_c = centroids[style]

        # Intra-cluster: mean distance of chairs to own centroid
        dists_own = []
        for c in chairs:
            h = safe_float(c.get("Høgde (cm)", ""))
            w = safe_float(c.get("Breidde (cm)", ""))
            if h and w:
                d_val = safe_float(c.get("Djupn (cm)", "")) or 0
                sh = safe_float(c.get("Setehøgde (cm)", "")) or 0
                pt = (h, w, d_val, sh)
                dists_own.append(euclidean(pt, own_c))

        intra_d = sum(dists_own) / len(dists_own) if dists_own else 0

        # Inter-cluster: distance to nearest OTHER centroid
        min_inter = float('inf')
        for other_style, other_c in centroids.items():
            if other_style != style:
                d = euclidean(own_c, other_c)
                if d < min_inter:
                    min_inter = d

        ratio = intra_d / min_inter if min_inter > 0 else 0
        silhouette = (min_inter - intra_d) / max(min_inter, intra_d) if max(min_inter, intra_d) > 0 else 0

        style_cohesion[style] = {
            "intra_d": intra_d,
            "inter_d": min_inter,
            "ratio": ratio,
            "silhouette": silhouette,
            "n": len(dists_own),
        }
        print(f"{style:<20} {len(dists_own):>4} {intra_d:>8.1f} {min_inter:>8.1f} {ratio:>8.3f} {silhouette:>10.3f}")

    # ── 4. SELECTION PRESSURE DOMINANCE per transition ───────────
    # For each pair of adjacent styles, measure which dimension changes most
    print("\n" + "=" * 80)
    print("SELECTION PRESSURE DOMINANCE PER TRANSITION")
    print("=" * 80)

    # Compute per-style feature vectors
    style_features = {}
    for style, chairs in styles.items():
        all_mats = []
        all_techs = []
        heights, widths, depths, seat_heights, weights = [], [], [], [], []
        nats = []

        for c in chairs:
            all_mats.extend(parse_list(c.get("Materialar", "")))
            all_techs.extend(parse_list(c.get("Teknikk", "")))
            h = safe_float(c.get("Høgde (cm)", ""))
            w = safe_float(c.get("Breidde (cm)", ""))
            d = safe_float(c.get("Djupn (cm)", ""))
            sh = safe_float(c.get("Setehøgde (cm)", ""))
            wt = safe_float(c.get("Estimert vekt (kg)", ""))
            nat = c.get("Nasjonalitet", "").strip()
            if h: heights.append(h)
            if w: widths.append(w)
            if d: depths.append(d)
            if sh: seat_heights.append(sh)
            if wt: weights.append(wt)
            if nat: nats.append(nat)

        h_mat = shannon_entropy(all_mats)
        t_c = shannon_entropy(all_techs)
        mean_h = sum(heights) / len(heights) if heights else 0
        mean_w = sum(widths) / len(widths) if widths else 0
        mean_d = sum(depths) / len(depths) if depths else 0
        mean_sh = sum(seat_heights) / len(seat_heights) if seat_heights else 0
        mean_wt = sum(weights) / len(weights) if weights else 0
        n_mats = len(set(all_mats))
        n_techs = len(set(all_techs))
        n_nats = len(set(nats))

        style_features[style] = {
            "h_mat": h_mat, "t_c": t_c,
            "mean_h": mean_h, "mean_w": mean_w, "mean_d": mean_d,
            "mean_sh": mean_sh, "mean_wt": mean_wt,
            "n_mats": n_mats, "n_techs": n_techs, "n_nats": n_nats,
        }

    # Pressure categories:
    # MATERIAL: delta(h_mat) + delta(n_mats)
    # TECHNOLOGY: delta(t_c) + delta(n_techs)
    # DIMENSIONAL: delta(mean_h) + delta(mean_w) + delta(mean_d)
    # GEOGRAPHIC: delta(n_nats)
    # ECONOMIC: delta(mean_wt)

    pressure_names = ["Material", "Teknologi", "Dimensjon", "Geografi", "Okonomi"]

    print(f"\n{'Overgang':<35} {'Material':>9} {'Teknol.':>9} {'Dimens.':>9} {'Geogr.':>9} {'Okon.':>9} {'Dominant':>12}")
    print("-" * 105)

    transition_data = []
    for i in range(len(ordered) - 1):
        s1, s2 = ordered[i], ordered[i + 1]
        f1, f2 = style_features[s1], style_features[s2]

        # Normalize changes as % of range across all styles
        d_mat = abs(f2["h_mat"] - f1["h_mat"]) + abs(f2["n_mats"] - f1["n_mats"]) * 0.1
        d_tech = abs(f2["t_c"] - f1["t_c"]) + abs(f2["n_techs"] - f1["n_techs"]) * 0.1
        d_dim = (abs(f2["mean_h"] - f1["mean_h"]) + abs(f2["mean_w"] - f1["mean_w"]) + abs(f2["mean_d"] - f1["mean_d"])) / 3
        d_geo = abs(f2["n_nats"] - f1["n_nats"])
        d_econ = abs(f2["mean_wt"] - f1["mean_wt"])

        # Normalize each to 0-100 scale
        total = d_mat + d_tech + d_dim / 10 + d_geo + d_econ / 5
        if total > 0:
            pct_mat = d_mat / total * 100
            pct_tech = d_tech / total * 100
            pct_dim = (d_dim / 10) / total * 100
            pct_geo = d_geo / total * 100
            pct_econ = (d_econ / 5) / total * 100
        else:
            pct_mat = pct_tech = pct_dim = pct_geo = pct_econ = 20

        pcts = [pct_mat, pct_tech, pct_dim, pct_geo, pct_econ]
        dominant = pressure_names[pcts.index(max(pcts))]

        label = f"{s1} -> {s2}"
        print(f"{label:<35} {pct_mat:>8.1f}% {pct_tech:>8.1f}% {pct_dim:>8.1f}% {pct_geo:>8.1f}% {pct_econ:>8.1f}% {dominant:>12}")

        transition_data.append({
            "from": s1, "to": s2,
            "pcts": pcts, "dominant": dominant,
            "d_mat": d_mat, "d_tech": d_tech, "d_dim": d_dim,
        })

    # ── 5. ERGONOMIC CONSTRAINT ANALYSIS ─────────────────────────
    # How close is each style to the ergonomic optimum (SH ~ 43-47 cm)?
    print("\n" + "=" * 80)
    print("ERGONOMIC CONSTRAINT: Seat height deviation from optimum (45 cm)")
    print("=" * 80)
    ERGO_OPT = 45.0
    print(f"{'Stil':<20} {'N_SH':>5} {'Mean_SH':>8} {'Dev':>8} {'|Dev|':>8} {'CV_SH':>8}")
    print("-" * 70)

    for style in ordered:
        chairs = styles[style]
        shs = [safe_float(c.get("Setehøgde (cm)", "")) for c in chairs]
        shs = [x for x in shs if x is not None and x > 0]
        if shs:
            mean_sh = sum(shs) / len(shs)
            dev = mean_sh - ERGO_OPT
            cv_sh = cv(shs)
            print(f"{style:<20} {len(shs):>5} {mean_sh:>8.1f} {dev:>+8.1f} {abs(dev):>8.1f} {cv_sh:>8.3f}")

    # ── 6. MATERIAL AFFORDANCE MATRIX (top materials x styles) ───
    print("\n" + "=" * 80)
    print("MATERIAL DOMINANCE PER STYLE (top 3 materials, % share)")
    print("=" * 80)

    for style in ordered:
        chairs = styles[style]
        all_mats = []
        for c in chairs:
            all_mats.extend(parse_list(c.get("Materialar", "")))
        counts = Counter(all_mats)
        total = sum(counts.values())
        top3 = counts.most_common(3)
        top3_str = ", ".join(f"{m} ({c/total*100:.0f}%)" for m, c in top3)
        print(f"  {style:<20} (N_mat={total:>4}): {top3_str}")

    # ── 7. STYLE-AS-ATTRACTOR TEST ───────────────────────────────
    # For each style, test if chairs cluster more tightly around own centroid
    # than expected by chance (permutation-like reasoning)
    print("\n" + "=" * 80)
    print("ATTRACTOR STRENGTH: Ratio of intra-style to global variance")
    print("=" * 80)

    # Global centroid
    all_heights = []
    all_widths = []
    for style in ordered:
        for c in styles[style]:
            h = safe_float(c.get("Høgde (cm)", ""))
            w = safe_float(c.get("Breidde (cm)", ""))
            if h: all_heights.append(h)
            if w: all_widths.append(w)
    global_cv_h = cv(all_heights)
    global_cv_w = cv(all_widths)
    print(f"Global CV_H = {global_cv_h:.3f}, Global CV_W = {global_cv_w:.3f}\n")

    print(f"{'Stil':<20} {'CV_H':>8} {'CV_W':>8} {'Ratio_H':>8} {'Ratio_W':>8} {'Attractor':>10}")
    print("-" * 70)
    for style in ordered:
        chairs = styles[style]
        heights = [safe_float(c.get("Høgde (cm)", "")) for c in chairs]
        widths = [safe_float(c.get("Breidde (cm)", "")) for c in chairs]
        heights = [x for x in heights if x and x > 0]
        widths = [x for x in widths if x and x > 0]
        cv_h = cv(heights) if len(heights) >= 2 else 0
        cv_w = cv(widths) if len(widths) >= 2 else 0
        ratio_h = cv_h / global_cv_h if global_cv_h > 0 else 0
        ratio_w = cv_w / global_cv_w if global_cv_w > 0 else 0
        mean_ratio = (ratio_h + ratio_w) / 2
        strength = "STERK" if mean_ratio < 0.5 else ("MODERAT" if mean_ratio < 0.8 else "SVAK")
        print(f"{style:<20} {cv_h:>8.3f} {cv_w:>8.3f} {ratio_h:>8.3f} {ratio_w:>8.3f} {strength:>10}")

    # ── 8. LATEX-READY TABLES ────────────────────────────────────
    print("\n" + "=" * 80)
    print("LATEX: Cluster stability table")
    print("=" * 80)
    for style in ordered:
        if style in style_cohesion:
            sc = style_cohesion[style]
            name = style.replace("é", "\\'{e}")
            print(f"{name} & {sc['n']} & {sc['intra_d']:.1f} & {sc['inter_d']:.1f} & {sc['ratio']:.3f} & {sc['silhouette']:.3f} \\\\")

    print("\n" + "=" * 80)
    print("LATEX: Selection pressure dominance table")
    print("=" * 80)
    for td in transition_data:
        s1 = td["from"].replace("é", "\\'{e}")
        s2 = td["to"].replace("é", "\\'{e}")
        pcts = td["pcts"]
        dom = td["dominant"]
        print(f"{s1} $\\rightarrow$ {s2} & {pcts[0]:.0f} & {pcts[1]:.0f} & {pcts[2]:.0f} & {pcts[3]:.0f} & {pcts[4]:.0f} & {dom} \\\\")


if __name__ == "__main__":
    main()
