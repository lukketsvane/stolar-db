"""Postdoc-kvalitet research for Art III-V overhaul."""
import csv, math, warnings
from collections import Counter, defaultdict
import statistics
import numpy as np
from scipy.stats import pearsonr, spearmanr, kruskal, mannwhitneyu
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder
from sklearn.decomposition import PCA
from sklearn.feature_selection import mutual_info_classif
warnings.filterwarnings('ignore')

rows = []
with open("../stolar_db.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append(r)

def sf(v):
    try:
        x = float(v.replace(",", "."))
        return x if x > 0 else None
    except:
        return None

mat_counts = Counter()
for r in rows:
    r["_mats"] = [m.strip() for m in r.get("Materialar", "").split(",") if m.strip()]
    r["_h"] = sf(r.get("Høgde (cm)", ""))
    r["_w"] = sf(r.get("Breidde (cm)", ""))
    r["_d"] = sf(r.get("Djupn (cm)", ""))
    r["_sh"] = sf(r.get("Setehøgde (cm)", ""))
    r["_style"] = r.get("Stilperiode", "").strip()
    r["_nat"] = r.get("Nasjonalitet", "").strip()
    try:
        r["_y"] = int(r.get("Frå år", "").strip())
        r["_y"] = r["_y"] if r["_y"] > 100 else None
    except:
        r["_y"] = None
    mat_counts.update(r["_mats"])

top_mats = [m for m, c in mat_counts.most_common(30) if c >= 20]

print("=" * 90)
print("  POSTDOC-KVALITET RESEARCH")
print("=" * 90)

# ================================================================
# ART III: FULL RF + CONFUSION MATRIX + PCA
# ================================================================
print("\n" + "=" * 90)
print("  ART III: FULL RF MED CONFUSION MATRIX OG PCA")
print("=" * 90)

style_data = []
for r in rows:
    if r["_style"] and r["_h"] and r["_w"] and r["_d"]:
        mat_binary = [1 if m in r["_mats"] else 0 for m in top_mats]
        hw = r["_h"] / r["_w"] if r["_w"] > 0 else 0
        vol = r["_h"] * r["_w"] * r["_d"]
        style_data.append({
            "h": r["_h"], "w": r["_w"], "d": r["_d"],
            "sh": r["_sh"] or 0, "hw": hw, "vol": vol,
            "style": r["_style"], "mat_binary": mat_binary,
            "year": r["_y"] or 0, "nat": r["_nat"],
        })

style_counts = Counter(d["style"] for d in style_data)
valid_styles = {s for s, c in style_counts.items() if c >= 10}
style_data = [d for d in style_data if d["style"] in valid_styles]
print(f"N = {len(style_data)}, k = {len(valid_styles)} stilar")

X_dims = np.array([[d["h"], d["w"], d["d"], d["sh"], d["hw"], d["vol"]] for d in style_data])
X_mats = np.array([d["mat_binary"] for d in style_data])
X_both = np.hstack([X_dims, X_mats])
y = np.array([d["style"] for d in style_data])

# 5-fold CV
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
all_preds = np.empty_like(y)
for train_idx, test_idx in skf.split(X_both, y):
    rf = RandomForestClassifier(n_estimators=200, random_state=42)
    rf.fit(X_both[train_idx], y[train_idx])
    all_preds[test_idx] = rf.predict(X_both[test_idx])

print("\nFULL CLASSIFICATION REPORT (dim+mat, 6+30 features):")
print(classification_report(y, all_preds, zero_division=0))

# Confusion matrix - topp forvekslingar
cm = confusion_matrix(y, all_preds, labels=sorted(valid_styles))
labels = sorted(valid_styles)
confusions = []
for i in range(len(labels)):
    for j in range(len(labels)):
        if i != j and cm[i][j] > 0:
            confusions.append((labels[i], labels[j], cm[i][j]))
confusions.sort(key=lambda x: -x[2])
print("TOPP FORVEKSLINGAR:")
for true, pred, n in confusions[:10]:
    print(f"  {true:<22} -> {pred:<22} n={n}")

# PCA
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_dims)
print(f"\nPCA: PC1={pca.explained_variance_ratio_[0]*100:.1f}%, PC2={pca.explained_variance_ratio_[1]*100:.1f}%")
print(f"Total: {sum(pca.explained_variance_ratio_)*100:.1f}%")
print("Stilsentroidar i PCA-rommet:")
for s in sorted(valid_styles, key=lambda x: np.mean(X_pca[y == x, 0])):
    mask_s = y == s
    cx, cy = np.mean(X_pca[mask_s, 0]), np.mean(X_pca[mask_s, 1])
    print(f"  {s:<22} PC1={cx:>+7.1f}  PC2={cy:>+7.1f}  n={mask_s.sum()}")

# MI per feature
print("\nMI PER FEATURE (sklearn):")
mi = mutual_info_classif(X_both, y,
    discrete_features=[False]*6 + [True]*len(top_mats), random_state=42)
feat_names = ["Hogde", "Breidde", "Djupn", "Setehogde", "H/W", "Volum"] + top_mats
mi_ranked = sorted(zip(feat_names, mi), key=lambda x: -x[1])
for name, m in mi_ranked[:15]:
    bar = "#" * int(m * 80)
    print(f"  {name:<20} MI={m:.4f}  {bar}")

# ================================================================
# ART V: MODULOR I PCA-ROMMET
# ================================================================
print("\n" + "=" * 90)
print("  ART V: MODULOR SOM UTELIGGAR I PCA-ROMMET")
print("=" * 90)

all_dims = np.array([[r["_h"], r["_w"], r["_d"]] for r in rows
                      if r["_h"] and r["_w"] and r["_d"]
                      and 20 < r["_h"] < 250 and 2 < r["_w"] < 200])
pca3 = PCA(n_components=2)
X_pca3 = pca3.fit_transform(all_dims)
modulor_point = pca3.transform([[113, 53, 43]])
centroid = np.mean(X_pca3, axis=0)
dist = np.linalg.norm(modulor_point - centroid)
dists_all = np.linalg.norm(X_pca3 - centroid, axis=1)
sd_dist = np.std(dists_all)
z_modulor = dist / sd_dist
pct = 100 * np.mean(dists_all < dist)

print(f"  Empirisk sentroid: ({centroid[0]:.1f}, {centroid[1]:.1f})")
print(f"  Modulor-punkt:     ({modulor_point[0][0]:.1f}, {modulor_point[0][1]:.1f})")
print(f"  Euklidisk avstand: {dist:.1f}")
print(f"  Z-score:           {z_modulor:.2f} sigma")
print(f"  Percentil:         {pct:.1f}% av stolane naerare sentroiden")
print(f"  -> Modulor er ein {z_modulor:.1f}-sigma uteliggar i PCA-rommet")

# Per-style distance to Modulor in PCA
print("\n  Avstand til Modulor i PCA per stil:")
for s in sorted(valid_styles, key=lambda x: style_counts.get(x, 0), reverse=True):
    mask_s = y == s
    if mask_s.sum() < 5:
        continue
    # Get PCA coords for this style
    style_dims = X_dims[mask_s, :3]  # H, W, D
    style_pca = pca3.transform(style_dims)
    style_cent = np.mean(style_pca, axis=0)
    d = np.linalg.norm(style_cent - modulor_point[0])
    print(f"    {s:<22} dist={d:>6.1f}  n={mask_s.sum()}")

print("\n" + "=" * 90)
print("  FERDIG")
print("=" * 90)
