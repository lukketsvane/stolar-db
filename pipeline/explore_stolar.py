"""
STOLAR -- Utforskande visualiseringar av heile databasen
Iver Raknes Finne, AHO 2026

Genererer ei rekkje tematiske figurar for djupare forståing.
"""

import sys, os, warnings
sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from collections import Counter

os.makedirs("figurar", exist_ok=True)

# ── Stil ──────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 180,
    "font.family": "serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 11,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

GRØN = ["#d8f3dc", "#b7e4c7", "#95d5b2", "#74c69d", "#52b788", "#40916c", "#2d6a4f", "#1b4332"]
cmap_grøn = LinearSegmentedColormap.from_list("stolar", GRØN, N=256)

# ── Last data ─────────────────────────────────────────────────────
df = pd.read_csv("STOLAR/STOLAR_all.csv", encoding="utf-8")
df.columns = [c.strip() for c in df.columns]

# Finn kolonnenamn dynamisk
col = {}
for c in df.columns:
    lc = c.lower()
    if "h" in lc and "gde" in lc and "sete" not in lc: col["H"] = c
    elif "breidd" in lc: col["B"] = c
    elif "djupn" in lc: col["D"] = c
    elif "sete" in lc and "gde" in lc: col["SH"] = c
    elif "vekt" in lc: col["V"] = c
    elif "fr" in lc and "r" in lc and len(c) < 8: col["FRA"] = c
    elif "til" in lc and "r" in lc and len(c) < 8: col["TIL"] = c
    elif "material" in lc and "komm" not in lc: col["MAT"] = c
    elif "stilperiode" in lc: col["STI"] = c
    elif "nasjon" in lc and "museet" not in lc: col["NAS"] = c

H, B, D, SH, V = col["H"], col["B"], col["D"], col["SH"], col["V"]
FRA, TIL, MAT, STI, NAS = col["FRA"], col["TIL"], col["MAT"], col["STI"], col["NAS"]

df["midtaar"] = (df[FRA].fillna(df[TIL]) + df[TIL].fillna(df[FRA])) / 2
df["volum"]   = df[H] * df[B] * df[D]
df["primmat"] = df[MAT].apply(lambda s: s.split(",")[0].strip() if pd.notna(s) else np.nan)
df["ratio_hb"] = df[H] / df[B]   # slankheit
df["ratio_hd"] = df[H] / df[D]
df["ratio_sh_h"] = df[SH] / df[H]  # setehøgde-proporsjon

print(f"n = {len(df)} stolar\n")

# ══════════════════════════════════════════════════════════════════
# FIG 1 -- Det store spreiingsplottet: kvar stol i tid x dimensjon
# ══════════════════════════════════════════════════════════════════
print("Fig 1: Det store spreiingsplottet")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

plots = [
    (H, "Høgde (cm)"),
    (B, "Breidde (cm)"),
    (D, "Djupn (cm)"),
    ("volum", "Volum (cm³)"),
]

for ax, (yc, ylabel) in zip(axes.flatten(), plots):
    sub = df[["midtaar", yc, "primmat"]].dropna()
    top5 = sub["primmat"].value_counts().head(6).index
    for mat in top5:
        m = sub[sub["primmat"] == mat]
        ax.scatter(m["midtaar"], m[yc], alpha=0.25, s=8, label=mat)
    ax.set_xlabel("År")
    ax.set_ylabel(ylabel)
    ax.legend(fontsize=6, loc="upper left", framealpha=0.7)

fig.suptitle("STOLAR -- 2300 stolar i tid og rom\nFargar = primærmaterial", fontsize=13)
plt.tight_layout()
plt.savefig("figurar/exp01_det_store_scatterplot.png", bbox_inches="tight")
plt.close()


# ══════════════════════════════════════════════════════════════════
# FIG 2 -- Morforom: PCA av alle dimensjonar, farga etter periode
# ══════════════════════════════════════════════════════════════════
print("Fig 2: Morforom (PCA)")
feats = [H, B, D, SH, V]
work = df[feats + ["midtaar", STI, "primmat"]].dropna()

scaler = StandardScaler()
X = scaler.fit_transform(work[feats])
pca = PCA(n_components=3)
pc = pca.fit_transform(X)

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Farga etter tid
sc = axes[0].scatter(pc[:, 0], pc[:, 1], c=work["midtaar"], cmap=cmap_grøn,
                     alpha=0.4, s=8)
plt.colorbar(sc, ax=axes[0], label="År")
axes[0].set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
axes[0].set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
axes[0].set_title("Morforom -- farga etter tid")

# Farga etter material
top6mat = work["primmat"].value_counts().head(6).index
colors_mat = {m: plt.cm.Set2(i) for i, m in enumerate(top6mat)}
for mat in top6mat:
    mask = work["primmat"] == mat
    axes[1].scatter(pc[mask, 0], pc[mask, 1], alpha=0.35, s=8,
                    color=colors_mat[mat], label=mat)
axes[1].set_xlabel(f"PC1"); axes[1].set_ylabel(f"PC2")
axes[1].set_title("Morforom -- farga etter material")
axes[1].legend(fontsize=7, framealpha=0.7)

# PC1 vs PC3
axes[2].scatter(pc[:, 0], pc[:, 2], c=work["midtaar"], cmap=cmap_grøn,
                alpha=0.3, s=8)
axes[2].set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
axes[2].set_ylabel(f"PC3 ({pca.explained_variance_ratio_[2]*100:.1f}%)")
axes[2].set_title("Morforom -- PC1 vs PC3")

fig.suptitle("STOLAR morforom -- 5-dimensjonal PCA-projeksjon", fontsize=13)
plt.tight_layout()
plt.savefig("figurar/exp02_morforom_pca.png", bbox_inches="tight")
plt.close()

print(f"  PCA var: {pca.explained_variance_ratio_}")
print(f"  Loadings PC1: {dict(zip(feats, pca.components_[0].round(3)))}")


# ══════════════════════════════════════════════════════════════════
# FIG 3 -- Proporsjonslandskap: H/B ratio over tid
# ══════════════════════════════════════════════════════════════════
print("Fig 3: Proporsjonslandskap")
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

sub3 = df[["midtaar", "ratio_hb", "ratio_hd", "ratio_sh_h", "primmat"]].dropna()

# H/B over tid med KDE-kontur
axes[0].scatter(sub3["midtaar"], sub3["ratio_hb"], alpha=0.15, s=6, color="#2d6a4f")
# Glidande median
bins = np.arange(1300, 2025, 25)
medians = []
for i in range(len(bins)-1):
    seg = sub3[(sub3["midtaar"]>=bins[i]) & (sub3["midtaar"]<bins[i+1])]
    if len(seg) > 3:
        medians.append((bins[i]+12.5, seg["ratio_hb"].median()))
if medians:
    mx, my = zip(*medians)
    axes[0].plot(mx, my, color="#b5838d", linewidth=2, label="Median (25-års bin)")
axes[0].axhline(y=1.618, color="#e9c46a", linestyle="--", alpha=0.6, label="Gullsnittet (1.618)")
axes[0].set_xlabel("År"); axes[0].set_ylabel("Høgde / Breidde")
axes[0].set_title("Slankheitsratio over tid")
axes[0].legend(fontsize=7)

# SH/H proporsjon over tid
axes[1].scatter(sub3["midtaar"], sub3["ratio_sh_h"], alpha=0.15, s=6, color="#2d6a4f")
medians2 = []
for i in range(len(bins)-1):
    seg = sub3[(sub3["midtaar"]>=bins[i]) & (sub3["midtaar"]<bins[i+1])]
    if len(seg) > 3:
        medians2.append((bins[i]+12.5, seg["ratio_sh_h"].median()))
if medians2:
    mx, my = zip(*medians2)
    axes[1].plot(mx, my, color="#b5838d", linewidth=2, label="Median")
axes[1].axhline(y=0.618/1.618, color="#e9c46a", linestyle="--", alpha=0.6, label="Modulor (0.382)")
axes[1].set_xlabel("År"); axes[1].set_ylabel("Setehøgde / Totalhøgde")
axes[1].set_title("Setehøgde-proporsjon over tid")
axes[1].legend(fontsize=7)

# H/B histogram per material
top5 = sub3["primmat"].value_counts().head(5).index
for mat in top5:
    m = sub3[sub3["primmat"]==mat]["ratio_hb"]
    axes[2].hist(m, bins=30, alpha=0.4, label=f"{mat} (n={len(m)})", density=True)
axes[2].set_xlabel("Høgde / Breidde")
axes[2].set_ylabel("Tettleik")
axes[2].set_title("Slankheit per material")
axes[2].legend(fontsize=7)

fig.suptitle("STOLAR -- Proporsjonar og gullsnittet", fontsize=13)
plt.tight_layout()
plt.savefig("figurar/exp03_proporsjonar.png", bbox_inches="tight")
plt.close()


# ══════════════════════════════════════════════════════════════════
# FIG 4 -- Material-galakse: kva materiale samelast over tid?
# ══════════════════════════════════════════════════════════════════
print("Fig 4: Material-galakse")

# Splitt multi-material og tell ko-førekomstar
from itertools import combinations

def parse_materials(s):
    if pd.isna(s): return []
    return [m.strip() for m in s.split(",") if m.strip()]

all_mats = []
for idx, row in df.iterrows():
    mats = parse_materials(row[MAT])
    all_mats.extend(mats)

mat_counts = Counter(all_mats)
top_mats = [m for m, c in mat_counts.most_common(20)]

# Ko-førekomst-matrise
comat = pd.DataFrame(0, index=top_mats, columns=top_mats)
for idx, row in df.iterrows():
    mats = [m for m in parse_materials(row[MAT]) if m in top_mats]
    for a, b in combinations(mats, 2):
        comat.loc[a, b] += 1
        comat.loc[b, a] += 1

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(comat.values, cmap=cmap_grøn, aspect="auto")
ax.set_xticks(range(len(top_mats))); ax.set_xticklabels(top_mats, rotation=45, ha="right", fontsize=7)
ax.set_yticks(range(len(top_mats))); ax.set_yticklabels(top_mats, fontsize=7)
plt.colorbar(im, ax=ax, label="Ko-førekomstar")
ax.set_title("Material-galakse -- kor ofte materiale opptrer saman i same stol", fontsize=11)
plt.tight_layout()
plt.savefig("figurar/exp04_material_galakse.png", bbox_inches="tight")
plt.close()


# ══════════════════════════════════════════════════════════════════
# FIG 5 -- Nasjonal signatur: dimensjonsprofil per nasjon
# ══════════════════════════════════════════════════════════════════
print("Fig 5: Nasjonale signaturar")

top_nas = df[NAS].value_counts().head(8).index
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

for i, nasjon in enumerate(top_nas):
    ax = axes[i]
    sub = df[df[NAS] == nasjon][[H, B, D, SH]].dropna()
    means = sub.mean()
    stds  = sub.std()
    dims = ["Høgde", "Breidde", "Djupn", "Setehøgde"]
    colors = ["#2d6a4f", "#52b788", "#74c69d", "#95d5b2"]
    ax.bar(dims, means, yerr=stds, color=colors, alpha=0.8, capsize=4)
    ax.set_title(f"{nasjon} (n={len(sub)})", fontsize=9)
    ax.set_ylim(0, 130)
    ax.tick_params(axis="x", rotation=45)

fig.suptitle("STOLAR -- Nasjonal dimensjonsprofil (gjennomsnitt + std)", fontsize=13)
plt.tight_layout()
plt.savefig("figurar/exp05_nasjonale_signaturar.png", bbox_inches="tight")
plt.close()


# ══════════════════════════════════════════════════════════════════
# FIG 6 -- Evolusjonsbaner: glidande gjennomsnitt per stil
# ══════════════════════════════════════════════════════════════════
print("Fig 6: Evolusjonsbaner per stil")

top8_sti = df[STI].value_counts().head(8).index
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for ai, dim_col, dim_label in [(0, H, "Høgde"), (1, B, "Breidde"), (2, D, "Djupn"), (3, SH, "Setehøgde")]:
    ax = axes[ai//2][ai%2]
    for si, stil in enumerate(top8_sti):
        sub = df[df[STI]==stil][["midtaar", dim_col]].dropna().sort_values("midtaar")
        if len(sub) < 5: continue
        # Glidande gjennomsnitt (vindauge=7)
        sub = sub.copy()
        sub["smooth"] = sub[dim_col].rolling(7, center=True, min_periods=3).mean()
        ax.plot(sub["midtaar"], sub["smooth"], linewidth=1.5, alpha=0.7, label=stil[:18])
    ax.set_xlabel("År"); ax.set_ylabel(f"{dim_label} (cm)")
    ax.set_title(f"{dim_label} -- glidande gjennomsnitt per stilperiode")
    ax.legend(fontsize=6, ncol=2)

fig.suptitle("STOLAR -- Evolusjonsbaner i dimensjonane", fontsize=13)
plt.tight_layout()
plt.savefig("figurar/exp06_evolusjonsbaner.png", bbox_inches="tight")
plt.close()


# ══════════════════════════════════════════════════════════════════
# FIG 7 -- Entropi-tidsserie: Shannon-entropi av material per 25 år
# ══════════════════════════════════════════════════════════════════
print("Fig 7: Material-entropi over tid")

df["bin25"] = (df["midtaar"] // 25 * 25)

def shannon_entropy(values):
    counts = Counter(values)
    total = sum(counts.values())
    return -sum((c/total)*np.log2(c/total) for c in counts.values() if c > 0)

entropy_ts = {}
for yr, grp in df.dropna(subset=["primmat"]).groupby("bin25"):
    if len(grp) < 3: continue
    entropy_ts[int(yr)] = shannon_entropy(grp["primmat"])

ent_s = pd.Series(entropy_ts).sort_index()

# Også: tal unike materiale per bin
unique_ts = {}
for yr, grp in df.dropna(subset=["primmat"]).groupby("bin25"):
    if len(grp) < 3: continue
    unique_ts[int(yr)] = grp["primmat"].nunique()

uni_s = pd.Series(unique_ts).sort_index()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

axes[0].fill_between(ent_s.index, ent_s.values, alpha=0.2, color="#2d6a4f")
axes[0].plot(ent_s.index, ent_s.values, color="#2d6a4f", linewidth=2)
axes[0].axvline(1760, color="#b5838d", linestyle="--", alpha=0.5, label="Industriell revolusjon")
axes[0].axvline(1850, color="#e9c46a", linestyle="--", alpha=0.5, label="1850")
axes[0].axvline(1950, color="#264653", linestyle="--", alpha=0.5, label="CNC-æra")
axes[0].set_xlabel("År"); axes[0].set_ylabel("Shannon-entropi (bits)")
axes[0].set_title("Material-entropi over tid\n(høgare = meir mangfald)")
axes[0].legend(fontsize=7)

axes[1].bar(uni_s.index, uni_s.values, width=20, color="#52b788", alpha=0.7)
axes[1].plot(uni_s.index, uni_s.values, color="#2d6a4f", linewidth=1)
axes[1].set_xlabel("År"); axes[1].set_ylabel("Unike primærmaterial")
axes[1].set_title("Tal på unike primærmaterial per 25-årsbin")

fig.suptitle("STOLAR -- Material-diversitet gjennom 750 år", fontsize=13)
plt.tight_layout()
plt.savefig("figurar/exp07_material_entropi.png", bbox_inches="tight")
plt.close()


# ══════════════════════════════════════════════════════════════════
# FIG 8 -- Dimensjonell korrelasjon: parvise scatter + heatmap
# ══════════════════════════════════════════════════════════════════
print("Fig 8: Dimensjonelle korrelasjonar")

dim_cols = [H, B, D, SH, V]
dim_labels = ["Høgde", "Breidde", "Djupn", "Setehøgde", "Vekt"]
corr = df[dim_cols].corr()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Heatmap
im = axes[0].imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
axes[0].set_xticks(range(len(dim_labels))); axes[0].set_xticklabels(dim_labels, rotation=45, ha="right")
axes[0].set_yticks(range(len(dim_labels))); axes[0].set_yticklabels(dim_labels)
for i in range(len(dim_labels)):
    for j in range(len(dim_labels)):
        axes[0].text(j, i, f"{corr.values[i,j]:.2f}", ha="center", va="center", fontsize=9)
plt.colorbar(im, ax=axes[0])
axes[0].set_title("Dimensjonell korrelasjonsmatrise")

# Høgde vs Breidde scatter med material
sub8 = df[[H, B, "primmat"]].dropna()
top4 = sub8["primmat"].value_counts().head(4).index
for mat in top4:
    m = sub8[sub8["primmat"]==mat]
    axes[1].scatter(m[B], m[H], alpha=0.3, s=12, label=mat)
axes[1].set_xlabel("Breidde (cm)"); axes[1].set_ylabel("Høgde (cm)")
axes[1].set_title("Høgde vs Breidde -- topp 4 materiale")
axes[1].legend(fontsize=8)

fig.suptitle("STOLAR -- Dimensjonelle samanspenningar", fontsize=13)
plt.tight_layout()
plt.savefig("figurar/exp08_korrelasjonar.png", bbox_inches="tight")
plt.close()


# ══════════════════════════════════════════════════════════════════
# FIG 9 -- Stolens anatomi: boksplott per stilperiode
# ══════════════════════════════════════════════════════════════════
print("Fig 9: Anatomisk variasjon per stil")

top_sti = df[STI].value_counts().head(8).index
sub9 = df[df[STI].isin(top_sti)]

fig, axes = plt.subplots(1, 4, figsize=(16, 6))

for ax, (yc, lbl) in zip(axes, [(H, "Høgde"), (B, "Breidde"), (D, "Djupn"), (SH, "Setehøgde")]):
    data = [sub9[sub9[STI]==s][yc].dropna().values for s in top_sti]
    bp = ax.boxplot(data, labels=[s[:12] for s in top_sti], patch_artist=True, vert=True)
    for patch, color in zip(bp["boxes"], GRØN[:len(top_sti)]):
        patch.set_facecolor(color)
    ax.set_ylabel(f"{lbl} (cm)")
    ax.tick_params(axis="x", rotation=45)
    ax.set_title(lbl)

fig.suptitle("STOLAR -- Anatomisk variasjon per stilperiode", fontsize=13)
plt.tight_layout()
plt.savefig("figurar/exp09_anatomisk_variasjon.png", bbox_inches="tight")
plt.close()


# ══════════════════════════════════════════════════════════════════
# FIG 10 -- Tidslinje: når er stolane produserte? Histogram
# ══════════════════════════════════════════════════════════════════
print("Fig 10: Tidslinje -- når er stolane produserte")

fig, axes = plt.subplots(2, 1, figsize=(14, 7), gridspec_kw={"height_ratios": [2, 1]})

# Histogram over tid
axes[0].hist(df["midtaar"].dropna(), bins=80, color="#2d6a4f", alpha=0.8, edgecolor="#1b4332")
axes[0].set_xlabel("År"); axes[0].set_ylabel("Tal stolar")
axes[0].set_title("Produksjons-tidslinje (n=2300)")

# Per nasjon (stacked)
top4nas = df[NAS].value_counts().head(4).index
for nas in top4nas:
    sub = df[df[NAS]==nas]["midtaar"].dropna()
    axes[1].hist(sub, bins=80, alpha=0.4, label=nas)
axes[1].set_xlabel("År"); axes[1].set_ylabel("Tal stolar")
axes[1].set_title("Per nasjonalitet")
axes[1].legend(fontsize=8)

fig.suptitle("STOLAR -- Tidslinje", fontsize=13)
plt.tight_layout()
plt.savefig("figurar/exp10_tidslinje.png", bbox_inches="tight")
plt.close()


# ══════════════════════════════════════════════════════════════════
# FIG 11 -- Vektkart: estimert vekt per material og tid
# ══════════════════════════════════════════════════════════════════
print("Fig 11: Vektkart")

sub11 = df[["midtaar", V, "primmat"]].dropna()
top6 = sub11["primmat"].value_counts().head(6).index

fig, ax = plt.subplots(figsize=(12, 6))
for mat in top6:
    m = sub11[sub11["primmat"]==mat].sort_values("midtaar")
    if len(m) < 5: continue
    smooth = m[V].rolling(10, center=True, min_periods=3).mean()
    ax.plot(m["midtaar"], smooth, linewidth=2, alpha=0.7, label=mat)
    ax.scatter(m["midtaar"], m[V], alpha=0.1, s=5)

ax.set_xlabel("År"); ax.set_ylabel("Estimert vekt (kg)")
ax.set_title("STOLAR -- Vektutvikling per material\n(glidande gjennomsnitt, vindauge=10)")
ax.legend()
plt.tight_layout()
plt.savefig("figurar/exp11_vekt_per_material.png", bbox_inches="tight")
plt.close()


# ══════════════════════════════════════════════════════════════════
# FIG 12 -- Materialskifte: primærmaterial-andel over hundreår
# ══════════════════════════════════════════════════════════════════
print("Fig 12: Materialskifte over hundreår")

sub12 = df[["bin25", "primmat"]].dropna()
top8mat = sub12["primmat"].value_counts().head(8).index.tolist()

pivot = sub12.groupby(["bin25", "primmat"]).size().unstack(fill_value=0)
# Berre topp 8 + resten
pivot_top = pivot[pivot.columns.intersection(top8mat)]
pivot_top["Andre"] = pivot.drop(columns=pivot.columns.intersection(top8mat), errors="ignore").sum(axis=1)
pivot_pct = pivot_top.div(pivot_top.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(14, 6))
pivot_pct.plot.area(ax=ax, stacked=True, alpha=0.8,
                     color=GRØN[:len(pivot_pct.columns)])
ax.set_xlabel("År"); ax.set_ylabel("Andel (%)")
ax.set_title("STOLAR -- Materialskifte over tid (topp 8 materiale)")
ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1, 0.5))
plt.tight_layout()
plt.savefig("figurar/exp12_materialskifte.png", bbox_inches="tight")
plt.close()


print("\n=== FERDIG: 12 utforskande figurar i figurar/exp01--exp12 ===")
