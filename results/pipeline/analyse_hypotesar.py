"""
STOLAR -- Analyse av 7 kjernehypotesar
Iver Raknes Finne, AHO 2026

Kvar del køyrer sjølvstendig og lagrar figurar til figurar/hyp_*.png
og skriv nøkkeltal til results/hypotesar.json
"""

import json, warnings, os, sys
sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
from scipy.fft import rfft, rfftfreq
from sklearn.preprocessing import LabelEncoder
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.feature_selection import mutual_info_regression, mutual_info_classif
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from collections import Counter

warnings.filterwarnings("ignore")
os.makedirs("figurar", exist_ok=True)
os.makedirs("results", exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 150,
    "font.family": "serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# ── Last inn data ─────────────────────────────────────────────────
df = pd.read_csv("STOLAR/STOLAR_all.csv", encoding="utf-8")

# Normaliser kolonnenamn (enkoding-variasjon)
df.columns = [c.strip() for c in df.columns]

# Finn rett kolonnenamn (kan variere med encoding)
col_map = {}
for c in df.columns:
    lc = c.lower()
    if "h" in lc and "gde" in lc and "sete" not in lc:
        col_map["hogde"] = c
    elif "breidd" in lc:
        col_map["breidde"] = c
    elif "djupn" in lc:
        col_map["djupn"] = c
    elif "sete" in lc and "gde" in lc:
        col_map["setehogde"] = c
    elif "vekt" in lc:
        col_map["vekt"] = c
    elif "fr" in lc and "r" in lc and len(c) < 8:
        col_map["fraaaar"] = c
    elif "til" in lc and "r" in lc and len(c) < 8:
        col_map["tilaaar"] = c
    elif "material" in lc and "komm" not in lc:
        col_map["material"] = c
    elif "stilperiode" in lc:
        col_map["stil"] = c
    elif "nasjon" in lc and "museet" not in lc:
        col_map["nasjon"] = c
    elif "hundre" in lc:
        col_map["hundreaar"] = c

print("Kolonnekartet:", col_map)

# Bygg ein rein arbeidsdf
H   = col_map.get("hogde", "Høgde (cm)")
B   = col_map.get("breidde", "Breidde (cm)")
D   = col_map.get("djupn", "Djupn (cm)")
SH  = col_map.get("setehogde", "Setehøgde (cm)")
V   = col_map.get("vekt", "Estimert vekt (kg)")
FRA = col_map.get("fraaaar", "Frå år")
TIL = col_map.get("tilaaar", "Til år")
MAT = col_map.get("material", "Materialar")
STI = col_map.get("stil", "Stilperiode")
NAS = col_map.get("nasjon", "Nasjonalitet")

df["midtaar"] = (df[FRA].fillna(df[TIL]) + df[TIL].fillna(df[FRA])) / 2
df["volum"]   = df[H] * df[B] * df[D]

# Primærmaterial (første i liste)
def primary_material(s):
    if pd.isna(s): return np.nan
    return s.split(",")[0].strip()

df["primmat"] = df[MAT].apply(primary_material)

results = {}

print(f"\n=== Datasettstorleik: {len(df)} stolar ===\n")

# ═══════════════════════════════════════════════════════════════════
# H1: Material forklarar meir enn stil/funksjon
# MI(material → geometri) vs MI(stil → geometri)
# ═══════════════════════════════════════════════════════════════════
print("── H1: Material vs Stil (Mutual Information) ──")

geom_cols = [H, B, D, SH]
work1 = df[geom_cols + [MAT, STI, "primmat", "midtaar"]].dropna(subset=[H])

# Encode kategoriar
le_mat = LabelEncoder()
le_sti = LabelEncoder()

mat_valid = work1.dropna(subset=["primmat"])
sti_valid  = work1.dropna(subset=[STI])

mi_mat, mi_sti = {}, {}
for col in [H, B, D]:
    sub_m = mat_valid[[col, "primmat"]].dropna()
    sub_s = sti_valid[[col, STI]].dropna()

    X_mat = le_mat.fit_transform(sub_m["primmat"]).reshape(-1, 1)
    X_sti = le_sti.fit_transform(sub_s[STI]).reshape(-1, 1)

    mi_mat[col] = mutual_info_regression(X_mat, sub_m[col], random_state=42)[0]
    mi_sti[col] = mutual_info_regression(X_sti, sub_s[col], random_state=42)[0]

dim_labels = ["Høgde", "Breidde", "Djupn"]
x = np.arange(len(dim_labels))
fig, ax = plt.subplots(figsize=(7, 4))
w = 0.35
b1 = ax.bar(x - w/2, [mi_mat[c] for c in [H, B, D]], w, label="Material", color="#2d6a4f")
b2 = ax.bar(x + w/2, [mi_sti[c]  for c in [H, B, D]], w, label="Stilperiode", color="#b5838d")
ax.set_xticks(x); ax.set_xticklabels(dim_labels)
ax.set_ylabel("Mutual Information (nats)")
ax.set_title("H1 -- MI(prediktor → dimensjon)")
ax.legend()
for bar in b1: ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+.002, f"{bar.get_height():.3f}", ha="center", fontsize=8)
for bar in b2: ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+.002, f"{bar.get_height():.3f}", ha="center", fontsize=8)
plt.tight_layout()
plt.savefig("figurar/hyp1_MI_material_vs_stil.png")
plt.close()

results["H1"] = {
    "MI_material": mi_mat,
    "MI_stil":     mi_sti,
    "material_vinn_hogde": mi_mat[H] > mi_sti[H],
    "material_vinn_breidde": mi_mat[B] > mi_sti[B],
    "material_vinn_djupn": mi_mat[D] > mi_sti[D],
}
print(f"  Høgde:   material={mi_mat[H]:.4f}  stil={mi_sti[H]:.4f}  -> {'MATERIAL' if mi_mat[H]>mi_sti[H] else 'STIL'}")
print(f"  Breidde: material={mi_mat[B]:.4f}  stil={mi_sti[B]:.4f}  -> {'MATERIAL' if mi_mat[B]>mi_sti[B] else 'STIL'}")
print(f"  Djupn:   material={mi_mat[D]:.4f}  stil={mi_sti[D]:.4f}  -> {'MATERIAL' if mi_mat[D]>mi_sti[D] else 'STIL'}")


# ═══════════════════════════════════════════════════════════════════
# H2: Seleksjonstrykk er ortogonale
# Residual-varians etter fjerning av material, nasjon, tid (sekvensielt)
# ═══════════════════════════════════════════════════════════════════
print("\n── H2: Ortogonale seleksjonskrefter (sekvensiell ANOVA) ──")

from sklearn.linear_model import LinearRegression

work2 = df[[H, "primmat", NAS, "midtaar"]].dropna()

def r2_from_dummies(X_df, y):
    le = LabelEncoder()
    dummies = pd.get_dummies(X_df, drop_first=True)
    if dummies.shape[1] == 0: return 0.0
    reg = LinearRegression().fit(dummies, y)
    return reg.score(dummies, y)

y2 = work2[H].values
r2_results = {}
orders = [
    ["primmat", NAS, "midtaar"],
    [NAS, "primmat", "midtaar"],
    ["midtaar", "primmat", NAS],
]

fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)

for oi, order in enumerate(orders):
    variances = []
    cumulative = None
    prev_r2 = 0.0
    for feat in order:
        sub = work2[[H] + [f for f in order[:order.index(feat)+1]]].dropna()
        y_sub = sub[H].values
        feats_so_far = [f for f in order[:order.index(feat)+1]]
        r2 = r2_from_dummies(sub[feats_so_far], y_sub)
        increment = max(0, r2 - prev_r2)
        variances.append(increment)
        prev_r2 = r2
    labels = [f.replace("primmat","Material").replace(NAS,"Nasjon").replace("midtaar","Tid") for f in order]
    r2_results[str(oi)] = dict(zip(labels, variances))

    ax = axes[oi]
    bars = ax.barh(labels, variances, color=["#2d6a4f","#52b788","#b7e4c7"])
    ax.set_xlabel("Inkrementell R²")
    ax.set_title(f"Rekkjefølgje {oi+1}")
    for b, v in zip(bars, variances):
        ax.text(v + 0.002, b.get_y()+b.get_height()/2, f"{v:.3f}", va="center", fontsize=9)

plt.suptitle("H2 -- Sekvensiell varians-dekomposisjon (høgde)", y=1.02)
plt.tight_layout()
plt.savefig("figurar/hyp2_ortogonale_krefter.png", bbox_inches="tight")
plt.close()

results["H2"] = r2_results
print(f"  R²-verdiar per kraft: {r2_results}")


# ═══════════════════════════════════════════════════════════════════
# H3: Stilar er klyngor, ikkje årsaker
# K-means vs kunsthistoriske etikettar
# ═══════════════════════════════════════════════════════════════════
print("\n── H3: Stilar = klyngor (K-means vs Stilperiode) ──")

work3 = df[[H, B, D, "primmat", "midtaar", STI]].dropna()
le3   = LabelEncoder()
work3 = work3.copy()
work3["mat_enc"] = le3.fit_transform(work3["primmat"])

# Skalér
scaler3 = StandardScaler()
X3 = scaler3.fit_transform(work3[["mat_enc", H, "midtaar"]].values)

n_stils = work3[STI].nunique()
k = min(n_stils, 12)
km = KMeans(n_clusters=k, random_state=42, n_init=10)
km.fit(X3)
work3["cluster"] = km.labels_

le_sti3 = LabelEncoder()
stil_enc = le_sti3.fit_transform(work3[STI])

ari  = adjusted_rand_score(stil_enc, work3["cluster"])
nmi  = normalized_mutual_info_score(stil_enc, work3["cluster"])

print(f"  k={k}  ARI={ari:.4f}  NMI={nmi:.4f}")
print(f"  {'Klyngor samsvarar med stilar' if ari > 0.15 else 'Klyngor divergerer frå stilar'}")

# Visualiser med PCA-projeksjon
pca3 = PCA(n_components=2)
X3_pca = pca3.fit_transform(X3)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
sc1 = axes[0].scatter(X3_pca[:,0], X3_pca[:,1], c=stil_enc, cmap="tab20", alpha=0.4, s=10)
axes[0].set_title(f"Kunsthistoriske stilar (n={n_stils})")
axes[0].set_xlabel("PC1"); axes[0].set_ylabel("PC2")

sc2 = axes[1].scatter(X3_pca[:,0], X3_pca[:,1], c=work3["cluster"], cmap="tab10", alpha=0.4, s=10)
axes[1].set_title(f"K-means klyngor (k={k})\nARI={ari:.3f}  NMI={nmi:.3f}")
axes[1].set_xlabel("PC1"); axes[1].set_ylabel("PC2")

plt.suptitle("H3 -- Stilgrenser vs. datadrivne klyngor")
plt.tight_layout()
plt.savefig("figurar/hyp3_stilar_vs_klyngor.png")
plt.close()

results["H3"] = {"k": k, "ARI": ari, "NMI": nmi, "n_stils": n_stils}


# ═══════════════════════════════════════════════════════════════════
# H4: Vegen (sti) skaper forma
# Material-spesifikke tidsseriar i same stil -- divergens
# ═══════════════════════════════════════════════════════════════════
print("\n── H4: Materialspesifikke vegar gjennom stilrom ──")

top_stils = df[STI].value_counts().head(4).index.tolist()
top_mats  = df["primmat"].value_counts().head(5).index.tolist()

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
divergences = {}

for si, stil in enumerate(top_stils):
    ax = axes[si//2][si%2]
    sub = df[(df[STI] == stil) & (df["primmat"].isin(top_mats))].dropna(subset=[H, "midtaar"])
    div_per_mat = {}
    for mat, grp in sub.groupby("primmat"):
        if len(grp) < 3: continue
        grp_s = grp.sort_values("midtaar")
        ax.plot(grp_s["midtaar"], grp_s[H].rolling(3, min_periods=1).mean(),
                label=mat, alpha=0.7, linewidth=1.5, marker="o", markersize=3)
        div_per_mat[mat] = float(grp_s[H].std())
    ax.set_title(f"{stil} (n={len(sub)})")
    ax.set_xlabel("År"); ax.set_ylabel("Høgde (cm)")
    ax.legend(fontsize=7)
    divergences[stil] = div_per_mat

plt.suptitle("H4 -- Ulike materiale-stiar gjennom same stil")
plt.tight_layout()
plt.savefig("figurar/hyp4_material_stiar.png")
plt.close()

results["H4"] = {"stil_divergens": divergences}
print(f"  Analysert {len(top_stils)} stilar x {len(top_mats)} materiale")


# ═══════════════════════════════════════════════════════════════════
# H5: Distribusjon-forflytting = eldring/døying
# Spektralanalyse på tidsserie av gjennomsnittleg høgde per stil
# ═══════════════════════════════════════════════════════════════════
print("\n── H5: Distribusjon-forflytting (spektral analyse) ──")

bin_size = 25  # år per bin
df["tidsbin"] = (df["midtaar"] // bin_size * bin_size)

top5_stils = df[STI].value_counts().head(5).index.tolist()
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
axes = axes.flatten()

tuning_tider = {}

for si, stil in enumerate(top5_stils):
    ax = axes[si]
    sub = df[df[STI] == stil].dropna(subset=[H, "midtaar"])
    if len(sub) < 10: continue

    ts = sub.groupby("tidsbin")[H].mean().sort_index()
    if len(ts) < 4: continue

    # Spektral analyse
    signal = ts.values - ts.values.mean()
    freqs  = rfftfreq(len(signal), d=bin_size)
    power  = np.abs(rfft(signal))**2

    dom_idx   = np.argmax(power[1:]) + 1  # skip DC
    dom_freq  = freqs[dom_idx]
    tuning_tid = 1.0/dom_freq if dom_freq > 0 else np.nan
    tuning_tider[stil] = float(tuning_tid) if not np.isnan(tuning_tid) else None

    ax.plot(ts.index, ts.values, color="#2d6a4f", linewidth=1.5)
    ax.fill_between(ts.index, ts.values, alpha=0.15, color="#2d6a4f")
    ax.set_title(f"{stil[:20]}\nTuning-tid ≈ {tuning_tid:.0f} år" if not np.isnan(tuning_tid) else stil[:20])
    ax.set_xlabel("År"); ax.set_ylabel("Gj.sn. høgde (cm)")

# Siste subplot: samanlikning tuning-tider
ax = axes[5]
valid = {k: v for k, v in tuning_tider.items() if v is not None}
if valid:
    ks = list(valid.keys())
    vs = list(valid.values())
    colors = ["#2d6a4f" if v < 100 else "#b5838d" for v in vs]
    ax.barh([k[:15] for k in ks], vs, color=colors)
    ax.set_xlabel("Tuning-tid (år)")
    ax.set_title("Tuning-tid per stil\n(kort = rask respons)")

plt.suptitle("H5 -- Distribusjon-dynamikk og tuning-tider per stil")
plt.tight_layout()
plt.savefig("figurar/hyp5_distribusjon_dynamikk.png")
plt.close()

results["H5"] = {"tuning_tider": tuning_tider}
print(f"  Tuning-tider: {tuning_tider}")


# ═══════════════════════════════════════════════════════════════════
# H6: Volum-varians = kraft-styrke
# CV(volum) per material og nasjon; korrelér med MI-styrke
# ═══════════════════════════════════════════════════════════════════
print("\n── H6: Volum-varians = seleksjonskraft-styrke ──")

work6 = df[["volum", "primmat", NAS]].dropna()

cv_mat = work6.groupby("primmat")["volum"].agg(
    lambda x: x.std()/x.mean() if x.mean() > 0 else np.nan
).dropna().sort_values()

cv_nas = work6.groupby(NAS)["volum"].agg(
    lambda x: x.std()/x.mean() if x.mean() > 0 else np.nan
).dropna().sort_values()

# MI per material (mot høgde -- som proxy for "kraft-styrke")
mi_per_mat = {}
for mat in cv_mat.index:
    sub = df[df["primmat"] == mat][[H]].dropna()
    if len(sub) < 5: continue
    mi_per_mat[mat] = float(sub[H].std())  # std som enkel proxy

# Korrelas: CV vs. MI-proxy
shared_mats = [m for m in cv_mat.index if m in mi_per_mat]
cv_vals  = [cv_mat[m]     for m in shared_mats]
mi_vals  = [mi_per_mat[m] for m in shared_mats]
r, p = stats.pearsonr(cv_vals, mi_vals) if len(cv_vals) > 2 else (np.nan, np.nan)

fig, axes = plt.subplots(1, 3, figsize=(14, 5))

# CV per material (topp 20)
top20_mat = cv_mat.tail(20)
axes[0].barh(top20_mat.index, top20_mat.values, color="#2d6a4f")
axes[0].set_xlabel("CV(volum)")
axes[0].set_title("Volum-variasjon per material\n(høg CV = laus seleksjon)")

# CV per nasjon
axes[1].barh(cv_nas.index, cv_nas.values, color="#52b788")
axes[1].set_xlabel("CV(volum)")
axes[1].set_title("Volum-variasjon per nasjon")

# Scatter: CV vs. form-spreiing (std av høgde)
axes[2].scatter(cv_vals, mi_vals, alpha=0.7, color="#2d6a4f", s=40)
for m, x, y in zip(shared_mats, cv_vals, mi_vals):
    axes[2].annotate(m[:8], (x, y), fontsize=7, alpha=0.7)
axes[2].set_xlabel("CV(volum)")
axes[2].set_ylabel("Std(høgde) -- proxy MI-styrke")
axes[2].set_title(f"H6 -- CV vs. form-spreiing\nPearson r={r:.3f} (p={p:.3f})")

plt.suptitle("H6 -- Volum-varians som proxy for seleksjonskraft")
plt.tight_layout()
plt.savefig("figurar/hyp6_volum_varians.png")
plt.close()

results["H6"] = {
    "pearson_r": float(r) if not np.isnan(r) else None,
    "pearson_p": float(p) if not np.isnan(p) else None,
    "cv_material_topp5": cv_mat.tail(5).to_dict(),
    "cv_nasjon": cv_nas.to_dict(),
}
print(f"  Pearson r={r:.4f}  p={p:.4f}")


# ═══════════════════════════════════════════════════════════════════
# H7: Substrat-skift åpnar nye former
# PCA entropy + convex hull FØR/ETTER industrialisering (~1850)
# ═══════════════════════════════════════════════════════════════════
print("\n── H7: Substrat-skift og form-rom (pre/post 1850) ──")

from scipy.spatial import ConvexHull

work7 = df[[H, B, D, "midtaar"]].dropna()
work7 = work7[(work7[H] > 20) & (work7[B] > 20) & (work7[D] > 20)]

pre  = work7[work7["midtaar"] < 1850]
post = work7[work7["midtaar"] >= 1850]

def pca_entropy(X, n_components=3):
    """Shannon-entropi av PCA eigenvalue-fordeling"""
    pca = PCA(n_components=min(n_components, X.shape[1], X.shape[0]-1))
    pca.fit(X)
    ev = pca.explained_variance_ratio_
    ev = ev[ev > 0]
    return float(-np.sum(ev * np.log(ev)))

def hull_volume(X):
    """Convex hull volume i skalert rom"""
    if len(X) < 4: return np.nan
    try:
        sc = StandardScaler().fit_transform(X)
        return float(ConvexHull(sc[:, :3]).volume)
    except Exception:
        return np.nan

sc7 = StandardScaler().fit_transform(work7[[H, B, D]])
pre_idx  = work7["midtaar"] < 1850
post_idx = ~pre_idx

X_pre  = StandardScaler().fit_transform(pre[[H, B, D]])
X_post = StandardScaler().fit_transform(post[[H, B, D]])

entropy_pre  = pca_entropy(X_pre)
entropy_post = pca_entropy(X_post)
hull_pre     = hull_volume(pre[[H, B, D]].values)
hull_post    = hull_volume(post[[H, B, D]].values)

print(f"  Pre-1850:  n={len(pre)}  PCA-entropi={entropy_pre:.4f}  Hull={hull_pre:.1f}")
print(f"  Post-1850: n={len(post)} PCA-entropi={entropy_post:.4f}  Hull={hull_post:.1f}")

# Visualiser form-rom over tid (20-år-bins)
work7["bin20"] = (work7["midtaar"] // 20 * 20)
entropy_series = {}
for yr, grp in work7.groupby("bin20"):
    if len(grp) < 5: continue
    X_g = StandardScaler().fit_transform(grp[[H, B, D]])
    entropy_series[int(yr)] = pca_entropy(X_g)

ents = pd.Series(entropy_series).sort_index()

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].plot(ents.index, ents.values, color="#2d6a4f", linewidth=1.5)
axes[0].axvline(1850, color="#b5838d", linestyle="--", label="Industrialisering ~1850")
axes[0].axvline(1950, color="#e9c46a", linestyle="--", label="CNC ~1950")
axes[0].fill_between(ents.index, ents.values, alpha=0.15, color="#2d6a4f")
axes[0].set_xlabel("År"); axes[0].set_ylabel("PCA-entropi (form-rom)")
axes[0].set_title("H7 -- Form-rom-dimensjonalitet over tid")
axes[0].legend()

bars_data = {
    "Pre-1850": entropy_pre,
    "Post-1850": entropy_post,
}
axes[1].bar(list(bars_data.keys()), list(bars_data.values()),
            color=["#52b788", "#2d6a4f"])
axes[1].set_ylabel("PCA-entropi")
axes[1].set_title(f"Form-rom FØR/ETTER industrialisering\nHull: {hull_pre:.1f} → {hull_post:.1f}")
for i, (k, v) in enumerate(bars_data.items()):
    axes[1].text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=10)

plt.suptitle("H7 -- Substrat-skift og form-rom-størrelse")
plt.tight_layout()
plt.savefig("figurar/hyp7_substrat_skift.png")
plt.close()

results["H7"] = {
    "entropy_pre1850":  entropy_pre,
    "entropy_post1850": entropy_post,
    "hull_pre1850":     hull_pre,
    "hull_post1850":    hull_post,
    "n_pre":  int(len(pre)),
    "n_post": int(len(post)),
    "entropi_auka": entropy_post > entropy_pre,
}

# ═══════════════════════════════════════════════════════════════════
# Skriv alle resultat til JSON
# ═══════════════════════════════════════════════════════════════════
def convert(o):
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, bool): return bool(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, dict): return {k: convert(v) for k, v in o.items()}
    if isinstance(o, list): return [convert(i) for i in o]
    return o

with open("results/hypotesar.json", "w", encoding="utf-8") as f:
    json.dump(convert(results), f, ensure_ascii=False, indent=2)

print("\n=== FERDIG. Figurar i figurar/hyp*.png -- resultat i results/hypotesar.json ===")
