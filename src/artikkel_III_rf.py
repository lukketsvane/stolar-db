"""
Artikkel III: Random Forest klassifikasjon.
Prediker stilperiode og nasjonalitet fraa dimensjonar og materialar.
Fellesinformasjon (MI) mellom variablar.
"""
import csv
import math
import numpy as np
from collections import Counter, defaultdict
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, classification_report
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_selection import mutual_info_classif

CSV_PATH = "../stolar_db.csv"

rows = []
with open(CSV_PATH, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

def safe_float(val):
    try:
        v = float(val.replace(",", "."))
        return v if v > 0 else None
    except (ValueError, AttributeError):
        return None

# Samle unike materialar
all_materials_set = set()
for row in rows:
    mats = row.get("Materialar", "").strip()
    if mats:
        for m in mats.split(","):
            m = m.strip()
            if m:
                all_materials_set.add(m)

# Topp materialar (minst 20 forekomstar)
mat_counts = Counter()
for row in rows:
    mats = row.get("Materialar", "").strip()
    if mats:
        for m in mats.split(","):
            m = m.strip()
            if m:
                mat_counts[m] += 1

top_materials = [m for m, c in mat_counts.most_common(30) if c >= 20]
print(f"Top materialar brukt som features ({len(top_materials)}): {top_materials[:10]}...")

# Bygg datasett
data = []
for row in rows:
    h = safe_float(row.get("Hoegde (cm)", row.get("Høgde (cm)", "")))
    w = safe_float(row.get("Breidde (cm)", ""))
    d = safe_float(row.get("Djupn (cm)", ""))
    sh = safe_float(row.get("Setehogde (cm)", row.get("Setehøgde (cm)", "")))
    stil = row.get("Stilperiode", "").strip()
    nasjonalitet = row.get("Nasjonalitet", "").strip()
    century = row.get("Hundreaar", row.get("Hundreår", "")).strip()
    mats = row.get("Materialar", "").strip()
    year_str = row.get("Fraa aar", row.get("Frå år", "")).strip()
    try:
        year = int(year_str) if year_str and year_str != "0" else None
    except ValueError:
        year = None

    mat_list = [m.strip() for m in mats.split(",") if m.strip()] if mats else []
    mat_binary = [1 if m in mat_list else 0 for m in top_materials]

    data.append({
        "h": h, "w": w, "d": d, "sh": sh,
        "year": year, "century": century,
        "style": stil, "nationality": nasjonalitet,
        "mat_binary": mat_binary,
        "mat_list": mat_list,
    })

# ---- 1. Stil-prediksjon (dimensjonar + materialar) ----
print("\n" + "=" * 90)
print("RANDOM FOREST: PREDIKER STILPERIODE")
print("=" * 90)

# Filtrer: berre rader med stil + dimensjonar
style_data = [d for d in data if d["style"] and d["h"] and d["w"] and d["d"]]
# Berre stilar med >= 10 stolar
style_counts = Counter(d["style"] for d in style_data)
valid_styles = {s for s, c in style_counts.items() if c >= 10}
style_data = [d for d in style_data if d["style"] in valid_styles]

print(f"Stolar med stil + dimensjonar: {len(style_data)}")
print(f"Stilar med >= 10 stolar: {len(valid_styles)}")

if style_data:
    # Features: dimensjonar + materialar
    X_dims = np.array([[d["h"], d["w"], d["d"], d["sh"] or 0] for d in style_data])
    X_mats = np.array([d["mat_binary"] for d in style_data])
    X_both = np.hstack([X_dims, X_mats])

    y_style = np.array([d["style"] for d in style_data])

    # Stratified 5-fold CV
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # A: Dimensjonar aleine
    f1s_dims = []
    for train_idx, test_idx in skf.split(X_dims, y_style):
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_dims[train_idx], y_style[train_idx])
        pred = rf.predict(X_dims[test_idx])
        f1s_dims.append(f1_score(y_style[test_idx], pred, average="weighted"))

    # B: Materialar aleine
    f1s_mats = []
    for train_idx, test_idx in skf.split(X_mats, y_style):
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_mats[train_idx], y_style[train_idx])
        pred = rf.predict(X_mats[test_idx])
        f1s_mats.append(f1_score(y_style[test_idx], pred, average="weighted"))

    # C: Begge
    f1s_both = []
    for train_idx, test_idx in skf.split(X_both, y_style):
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_both[train_idx], y_style[train_idx])
        pred = rf.predict(X_both[test_idx])
        f1s_both.append(f1_score(y_style[test_idx], pred, average="weighted"))

    print(f"\nStilperiode-prediksjon (weighted F1, 5-fold CV):")
    print(f"  Dimensjonar aleine:    F1 = {np.mean(f1s_dims):.3f} (+/- {np.std(f1s_dims):.3f})")
    print(f"  Materialar aleine:     F1 = {np.mean(f1s_mats):.3f} (+/- {np.std(f1s_mats):.3f})")
    print(f"  Dimensjonar + mat:     F1 = {np.mean(f1s_both):.3f} (+/- {np.std(f1s_both):.3f})")

    # Feature importance for combined model
    rf_full = RandomForestClassifier(n_estimators=200, random_state=42)
    rf_full.fit(X_both, y_style)
    feat_names = ["Hogde", "Breidde", "Djupn", "Setehogde"] + top_materials
    importances = list(zip(feat_names, rf_full.feature_importances_))
    importances.sort(key=lambda x: x[1], reverse=True)
    print("\n  Topp 15 feature importances:")
    for name, imp in importances[:15]:
        bar = "#" * int(imp * 200)
        print(f"    {name:<25} {imp:.4f}  {bar}")

# ---- 2. Nasjonalitet-prediksjon ----
print("\n" + "=" * 90)
print("RANDOM FOREST: PREDIKER NASJONALITET")
print("=" * 90)

nat_data = [d for d in data if d["nationality"] and d["h"] and d["w"] and d["d"]]
nat_counts = Counter(d["nationality"] for d in nat_data)
valid_nats = {n for n, c in nat_counts.items() if c >= 15}
nat_data = [d for d in nat_data if d["nationality"] in valid_nats]

print(f"Stolar med nasjonalitet + dimensjonar: {len(nat_data)}")
print(f"Nasjonalitetar med >= 15 stolar: {len(valid_nats)}")

if nat_data:
    X_dims_n = np.array([[d["h"], d["w"], d["d"], d["sh"] or 0] for d in nat_data])
    X_mats_n = np.array([d["mat_binary"] for d in nat_data])
    X_both_n = np.hstack([X_dims_n, X_mats_n])
    y_nat = np.array([d["nationality"] for d in nat_data])

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    f1s_dims_n = []
    for train_idx, test_idx in skf.split(X_dims_n, y_nat):
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_dims_n[train_idx], y_nat[train_idx])
        pred = rf.predict(X_dims_n[test_idx])
        f1s_dims_n.append(f1_score(y_nat[test_idx], pred, average="weighted"))

    f1s_mats_n = []
    for train_idx, test_idx in skf.split(X_mats_n, y_nat):
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_mats_n[train_idx], y_nat[train_idx])
        pred = rf.predict(X_mats_n[test_idx])
        f1s_mats_n.append(f1_score(y_nat[test_idx], pred, average="weighted"))

    f1s_both_n = []
    for train_idx, test_idx in skf.split(X_both_n, y_nat):
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_both_n[train_idx], y_nat[train_idx])
        pred = rf.predict(X_both_n[test_idx])
        f1s_both_n.append(f1_score(y_nat[test_idx], pred, average="weighted"))

    print(f"\nNasjonalitet-prediksjon (weighted F1, 5-fold CV):")
    print(f"  Dimensjonar aleine:    F1 = {np.mean(f1s_dims_n):.3f} (+/- {np.std(f1s_dims_n):.3f})")
    print(f"  Materialar aleine:     F1 = {np.mean(f1s_mats_n):.3f} (+/- {np.std(f1s_mats_n):.3f})")
    print(f"  Dimensjonar + mat:     F1 = {np.mean(f1s_both_n):.3f} (+/- {np.std(f1s_both_n):.3f})")

# ---- 3. Hundreaar-prediksjon ----
print("\n" + "=" * 90)
print("RANDOM FOREST: PREDIKER HUNDREAAR")
print("=" * 90)

cent_data = [d for d in data if d["century"] and d["h"] and d["w"] and d["d"]]
cent_counts = Counter(d["century"] for d in cent_data)
valid_cents = {c for c, n in cent_counts.items() if n >= 20}
cent_data = [d for d in cent_data if d["century"] in valid_cents]

if cent_data:
    X_both_c = np.hstack([
        np.array([[d["h"], d["w"], d["d"], d["sh"] or 0] for d in cent_data]),
        np.array([d["mat_binary"] for d in cent_data])
    ])
    y_cent = np.array([d["century"] for d in cent_data])

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    f1s_cent = []
    for train_idx, test_idx in skf.split(X_both_c, y_cent):
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_both_c[train_idx], y_cent[train_idx])
        pred = rf.predict(X_both_c[test_idx])
        f1s_cent.append(f1_score(y_cent[test_idx], pred, average="weighted"))
    print(f"  Hundreaar-prediksjon (dim+mat): F1 = {np.mean(f1s_cent):.3f} (+/- {np.std(f1s_cent):.3f})")

# ---- 4. Stilmerke som prediktor for dimensjonar (omvendt) ----
print("\n" + "=" * 90)
print("OMVENDT: KAN STILMERKE PREDIKERE DIMENSJONAR?")
print("=" * 90)

# Koder stilmerke som one-hot, prediker hogde-klasse
if style_data:
    le = LabelEncoder()
    y_style_enc = le.fit_transform([d["style"] for d in style_data])
    n_styles = len(le.classes_)

    # One-hot for stil
    X_style_onehot = np.zeros((len(style_data), n_styles))
    for i, idx in enumerate(y_style_enc):
        X_style_onehot[i, idx] = 1

    # Prediker hundreaar fraa stil
    y_century_for_style = np.array([d.get("century", "ukjend") for d in style_data])

    # Sjekk: kan stil predikere hundreaar?
    valid_mask = np.array([c in valid_cents for c in y_century_for_style])
    if valid_mask.sum() > 50:
        X_s = X_style_onehot[valid_mask]
        y_c = y_century_for_style[valid_mask]

        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        f1s_style_to_cent = []
        for train_idx, test_idx in skf.split(X_s, y_c):
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X_s[train_idx], y_c[train_idx])
            pred = rf.predict(X_s[test_idx])
            f1s_style_to_cent.append(f1_score(y_c[test_idx], pred, average="weighted"))
        print(f"  Stilmerke -> Hundreaar:   F1 = {np.mean(f1s_style_to_cent):.3f} (+/- {np.std(f1s_style_to_cent):.3f})")

print("\n" + "=" * 90)
print("SAMANDRAG: Prediksjonskraft")
print("=" * 90)
print("  Dimensjonar + material -> Stilperiode:   F1 = {:.3f}".format(np.mean(f1s_both)))
print("  Dimensjonar + material -> Nasjonalitet:  F1 = {:.3f}".format(np.mean(f1s_both_n)))
print("  Dimensjonar + material -> Hundreaar:     F1 = {:.3f}".format(np.mean(f1s_cent)))
print("  Stilmerke aleine -> Hundreaar:            F1 = {:.3f}".format(np.mean(f1s_style_to_cent)))
