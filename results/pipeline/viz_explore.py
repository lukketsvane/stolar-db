"""
STOLAR -- Utforskande visualiseringar
Ridgeline, morphospace-kube, varianstunnel, sentroidbane.

Køyr frå prosjektrota:
  python pipeline/viz_explore.py
"""

import sys, os, warnings
sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from scipy.stats import gaussian_kde

OUT = "results/explore"
os.makedirs(OUT, exist_ok=True)

# ── Fargepalettar ──
TIDS_CMAP = cm.get_cmap("YlGnBu")

# ── Last data ──
print("Lastar STOLAR-data...")
df = pd.read_csv("STOLAR/STOLAR_all.csv", encoding="utf-8-sig")
df.columns = [c.strip() for c in df.columns]

H = "Høgde (cm)"
B = "Breidde (cm)"
D = "Djupn (cm)"
SH = "Setehøgde (cm)"
FRA = "Frå år"
TIL = "Til år"
MAT = "Materialar"
STI = "Stilperiode"

df["midtaar"] = (df[FRA].fillna(df[TIL]) + df[TIL].fillna(df[FRA])) / 2
df["hundreaar"] = (df["midtaar"] // 100 * 100).astype("Int64")
df["primmat"] = df[MAT].apply(lambda s: s.split(",")[0].strip() if pd.notna(s) else "Ukjend")

# Filtrer rimeleg dimensjonsdata
dim = df.dropna(subset=[H, B, D, "midtaar"]).copy()
dim = dim[(dim[H] > 20) & (dim[H] < 250) & (dim[B] > 10) & (dim[B] < 200) & (dim[D] > 10) & (dim[D] < 200)]
print(f"  {len(dim)} stolar med H/B/D + aarstal")

centuries = sorted(dim["hundreaar"].dropna().unique())
century_counts = dim["hundreaar"].value_counts()
centuries = [c for c in centuries if century_counts.get(c, 0) >= 10]
print(f"  Hundreaar med >=10 stolar: {centuries}")


# ══════════════════════════════════════════════════════════════════
# 1. RIDGELINE: dimensjonsfordeling per hundreaar
# ══════════════════════════════════════════════════════════════════
print("\n[1/4] Ridgeline-plott...")

def ridgeline(dim_col, label, filename):
    n_cent = len(centuries)
    fig, axes = plt.subplots(n_cent, 1, figsize=(10, 1.4 * n_cent), sharex=True)
    fig.patch.set_facecolor("white")

    vals_all = dim[dim_col].dropna()
    x_min, x_max = vals_all.quantile(0.01), vals_all.quantile(0.99)
    x_grid = np.linspace(x_min, x_max, 300)
    norm = Normalize(vmin=min(centuries), vmax=max(centuries))

    for i, cent in enumerate(centuries):
        ax = axes[i]
        ax.set_facecolor("white")
        sub = dim[dim["hundreaar"] == cent][dim_col].dropna()

        if len(sub) < 5:
            ax.axis("off")
            continue

        kde = gaussian_kde(sub, bw_method=0.3)
        density = kde(x_grid)
        density = density / density.max()

        color = TIDS_CMAP(norm(cent))
        ax.fill_between(x_grid, 0, density, alpha=0.7, color=color, linewidth=0)
        ax.plot(x_grid, density, color=color, linewidth=1.2, alpha=0.9)

        ax.set_ylim(0, 1.3)
        ax.set_xlim(x_min, x_max)
        ax.axis("off")

        # Label
        cent_label = f"{int(cent)}-talet"
        n = len(sub)
        ax.text(x_min - (x_max - x_min) * 0.01, 0.3, f"{cent_label}  (n={n})",
                ha="right", va="center", fontsize=8, color="#333", fontfamily="serif")

        # Median
        med = sub.median()
        ax.axvline(med, color=color, linewidth=1.5, alpha=0.5, linestyle="--")
        ax.text(med, 1.05, f"{med:.0f}", ha="center", va="bottom",
                fontsize=7, color="#555", fontfamily="serif")

    axes[0].set_title(f"STOLAR -- {label} per hundreaar\n"
                       f"KDE-fordeling med medianmarkør (n={len(dim)})",
                       fontsize=13, fontfamily="serif", color="#1a1a2e", pad=15)
    axes[-1].set_xlim(x_min, x_max)
    axes[-1].tick_params(axis="x", labelbottom=True, labelsize=9)
    axes[-1].set_xlabel(f"{label}", fontsize=10, fontfamily="serif")
    axes[-1].spines["bottom"].set_visible(True)
    axes[-1].spines["bottom"].set_color("#999")
    axes[-1].tick_params(bottom=True, colors="#666")

    plt.subplots_adjust(hspace=-0.3, left=0.22, right=0.95, top=0.92, bottom=0.06)
    path = os.path.join(OUT, filename)
    plt.savefig(path, dpi=180, facecolor="white", bbox_inches="tight")
    plt.close()
    print(f"  -> {path}")

ridgeline(H, "Hogde (cm)", "ridgeline_hogde.png")
ridgeline(B, "Breidde (cm)", "ridgeline_breidde.png")
ridgeline(D, "Djupn (cm)", "ridgeline_djupn.png")


# ══════════════════════════════════════════════════════════════════
# 2. MORPHOSPACE-KUBE: H x B x D, farga etter tid
# ══════════════════════════════════════════════════════════════════
print("\n[2/4] Morphospace-kube...")

fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection="3d")
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

years = dim["midtaar"].values
norm_yr = Normalize(vmin=years.min(), vmax=years.max())
colors = TIDS_CMAP(norm_yr(years))

ax.scatter(dim[H].values, dim[B].values, dim[D].values,
           c=colors, s=8, alpha=0.6, edgecolors="none", depthshade=True)

ax.set_xlabel("Hogde (cm)", fontsize=10, labelpad=8)
ax.set_ylabel("Breidde (cm)", fontsize=10, labelpad=8)
ax.set_zlabel("Djupn (cm)", fontsize=10, labelpad=8)
ax.view_init(elev=25, azim=225)

sm = plt.cm.ScalarMappable(cmap=TIDS_CMAP, norm=norm_yr)
sm.set_array([])
cb = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.08, label="Midtaar")

ax.set_title(f"STOLAR Morphospace -- H x B x D\n"
             f"Farga etter tid ({int(years.min())}--{int(years.max())}), n={len(dim)}",
             fontsize=13, fontfamily="serif", pad=15)

path = os.path.join(OUT, "morphospace_kube.png")
plt.savefig(path, dpi=180, facecolor="white", bbox_inches="tight")
plt.close()
print(f"  -> {path}")

# Animert rotasjon (36 frames)
print("  Rotasjonsframes (36 stk)...")
anim_dir = os.path.join(OUT, "morphospace_anim")
os.makedirs(anim_dir, exist_ok=True)

for fi in range(36):
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.scatter(dim[H].values, dim[B].values, dim[D].values,
               c=colors, s=6, alpha=0.5, edgecolors="none", depthshade=True)
    ax.view_init(elev=20, azim=180 + fi * 10)
    ax.set_xlabel("H", fontsize=8); ax.set_ylabel("B", fontsize=8); ax.set_zlabel("D", fontsize=8)
    ax.set_title(f"Morphospace  ·  {fi+1}/36", fontsize=10, fontfamily="serif")
    plt.savefig(os.path.join(anim_dir, f"rot_{fi:02d}.png"), dpi=100, facecolor="white", bbox_inches="tight")
    plt.close()
print(f"  -> {anim_dir}/ (36 frames)")


# ══════════════════════════════════════════════════════════════════
# 3. VARIANSTUNNEL: sigma(H), sigma(B), sigma(D) over tid
# ══════════════════════════════════════════════════════════════════
print("\n[3/4] Varianstunnel...")

fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
fig.patch.set_facecolor("white")

dims_info = [(H, "Hogde", "#2d6a4f"), (B, "Breidde", "#1b4332"), (D, "Djupn", "#40916c")]

window = 50
step_yr = 25
years_range = np.arange(1500, 2025, step_yr)

for ax, (col, label, color) in zip(axes, dims_info):
    ax.set_facecolor("white")
    means, stds, mids, ns = [], [], [], []

    for yr in years_range:
        sub = dim[(dim["midtaar"] >= yr) & (dim["midtaar"] < yr + window)][col].dropna()
        if len(sub) >= 5:
            means.append(sub.mean())
            stds.append(sub.std())
            mids.append(yr + window / 2)
            ns.append(len(sub))

    means = np.array(means)
    stds = np.array(stds)
    mids = np.array(mids)

    ax.fill_between(mids, means - stds, means + stds, alpha=0.25, color=color, label="+-1 sigma")
    ax.fill_between(mids, means - 2*stds, means + 2*stds, alpha=0.08, color=color, label="+-2 sigma")
    ax.plot(mids, means, color=color, linewidth=2, label=f"Gjennomsnitt {label}")
    ax.set_ylabel(f"{label} (cm)", fontsize=10, fontfamily="serif")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.15)

    # Annoter strengast / friast
    cv = stds / means
    i_min = np.argmin(cv)
    i_max = np.argmax(cv)
    ax.annotate(f"Strengast: {int(mids[i_min])} (CV={cv[i_min]:.2f})",
                xy=(mids[i_min], means[i_min]),
                xytext=(mids[i_min] + 40, means[i_min] + stds.max() * 0.7),
                fontsize=7, color=color, fontfamily="serif",
                arrowprops=dict(arrowstyle="->", color=color, lw=0.8))
    ax.annotate(f"Friast: {int(mids[i_max])} (CV={cv[i_max]:.2f})",
                xy=(mids[i_max], means[i_max]),
                xytext=(mids[i_max] - 60, means[i_max] - stds.max() * 0.7),
                fontsize=7, color=color, fontfamily="serif",
                arrowprops=dict(arrowstyle="->", color=color, lw=0.8))

axes[0].set_title("STOLAR Varianstunnel -- Dimensjonell fridom over tid\n"
                   f"Glidande {window}-aarsvindauge, n={len(dim)}",
                   fontsize=13, fontfamily="serif", pad=10)
axes[-1].set_xlabel("Midtaar", fontsize=10, fontfamily="serif")

plt.tight_layout()
path = os.path.join(OUT, "varianstunnel.png")
plt.savefig(path, dpi=180, facecolor="white", bbox_inches="tight")
plt.close()
print(f"  -> {path}")


# ══════════════════════════════════════════════════════════════════
# 4. EVOLUSJONAER BANE: sentroid gjennom H x B x D over tid
# ══════════════════════════════════════════════════════════════════
print("\n[4/4] Evolusjonaer bane (sentroidvandring)...")

fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection="3d")
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# Bakgrunnssky
ax.scatter(dim[H].values, dim[B].values, dim[D].values,
           c="#ccc", s=3, alpha=0.15, edgecolors="none", depthshade=True)

# Sentroidar per 50-aarsperiode
ch, cb_, cd, cy, cn = [], [], [], [], []
for yr in np.arange(1500, 2025, 50):
    sub = dim[(dim["midtaar"] >= yr) & (dim["midtaar"] < yr + 50)]
    if len(sub) >= 5:
        ch.append(sub[H].mean())
        cb_.append(sub[B].mean())
        cd.append(sub[D].mean())
        cy.append(yr + 25)
        cn.append(len(sub))

ch = np.array(ch); cb_ = np.array(cb_); cd = np.array(cd)
cy = np.array(cy); cn = np.array(cn)

norm_cy = Normalize(vmin=cy.min(), vmax=cy.max())

# Teikn bane
for i in range(len(cy) - 1):
    color = TIDS_CMAP(norm_cy(cy[i]))
    ax.plot([ch[i], ch[i+1]], [cb_[i], cb_[i+1]], [cd[i], cd[i+1]],
            color=color, linewidth=3, alpha=0.8)

# Sentroidpunkt
for i in range(len(cy)):
    color = TIDS_CMAP(norm_cy(cy[i]))
    size = max(30, cn[i] * 0.5)
    ax.scatter([ch[i]], [cb_[i]], [cd[i]],
               c=[color], s=size, edgecolors="white", linewidths=0.8, zorder=5)
    if int(cy[i]) % 100 <= 25:
        ax.text(ch[i], cb_[i], cd[i] + 2,
                f"{int(cy[i])}", fontsize=8, color="#333",
                ha="center", fontfamily="serif")

ax.set_xlabel("Hogde (cm)", fontsize=10, labelpad=8)
ax.set_ylabel("Breidde (cm)", fontsize=10, labelpad=8)
ax.set_zlabel("Djupn (cm)", fontsize=10, labelpad=8)
ax.view_init(elev=25, azim=225)

sm2 = plt.cm.ScalarMappable(cmap=TIDS_CMAP, norm=norm_cy)
sm2.set_array([])
fig.colorbar(sm2, ax=ax, shrink=0.5, pad=0.08, label="Midtaar")

ax.set_title("Stolen si reise gjennom formrommet\n"
             f"Sentroid (H, B, D) per 50-aarsperiode, {int(cy.min())}--{int(cy.max())}",
             fontsize=13, fontfamily="serif", pad=15)

path = os.path.join(OUT, "sentroid_bane.png")
plt.savefig(path, dpi=180, facecolor="white", bbox_inches="tight")
plt.close()
print(f"  -> {path}")

print("\n=== FERDIG ===")
print(f"Alle figurar i {OUT}/")
