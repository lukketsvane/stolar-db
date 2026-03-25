"""
Generer alle figurar for STOLAR-artiklane som PDF.
"""
import csv
import math
import os
from collections import Counter, defaultdict
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'figure.figsize': (7, 4.5),
    'figure.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.15,
})

CSV_PATH = "../stolar_db.csv"
FIG_DIR = "../texts/fig"
os.makedirs(FIG_DIR, exist_ok=True)

rows = []
with open(CSV_PATH, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        rows.append(row)

def safe_float(val):
    try:
        v = float(val.replace(",", "."))
        return v if v > 0 else None
    except (ValueError, AttributeError):
        return None

def get_museum(row):
    nm = row.get("Nasjonalmuseet", "")
    obj = row.get("Objekt-ID", "")
    if "nasjonalmuseet.no" in nm or obj.startswith("OK-") or obj.startswith("NMK"):
        return "NMK"
    return "V&A"

def century_sort(c):
    try: return int(c.split("-")[0])
    except: return 9999

# Enrich
for r in rows:
    r["_museum"] = get_museum(r)
    r["_mats"] = [m.strip() for m in r.get("Materialar","").split(",") if m.strip()]
    r["_century"] = r.get("Hundreår", "").strip()
    try:
        y = int(r.get("Frå år","").strip())
        r["_year"] = y if y > 100 else None
    except:
        r["_year"] = None
    r["_h"] = safe_float(r.get("Høgde (cm)", ""))
    r["_w"] = safe_float(r.get("Breidde (cm)", ""))
    r["_d"] = safe_float(r.get("Djupn (cm)", ""))
    r["_style"] = r.get("Stilperiode", "").strip()

centuries = sorted(set(r["_century"] for r in rows if r["_century"]), key=century_sort)
# Skip centuries with very few chairs
main_centuries = [c for c in centuries if c not in ("1200-talet", "1300-talet")]

# ==========================================================
# FIGUR 1: MAHOGNIENS BOGE (NMK, 25-aarsbolkar)
# ==========================================================
print("Fig 1: Mahogniens boge...")
period_data = defaultdict(lambda: {"total": 0, "mahogni": 0})
for r in rows:
    if r["_museum"] != "NMK" or r["_year"] is None: continue
    p = (r["_year"] // 25) * 25
    period_data[p]["total"] += 1
    if "Mahogni" in r["_mats"]:
        period_data[p]["mahogni"] += 1

periods = sorted(p for p in period_data if p >= 1600 and period_data[p]["total"] >= 3)
pcts = [100 * period_data[p]["mahogni"] / period_data[p]["total"] for p in periods]
labels = [f"{p}" for p in periods]

fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.bar(range(len(periods)), pcts, color=["#8B4513" if p < 100 else "#D2691E" for p in pcts],
              edgecolor="white", linewidth=0.5)
# Highlight 100% bar
for i, p in enumerate(pcts):
    if p >= 99:
        bars[i].set_color("#4A0E0E")
        bars[i].set_edgecolor("#FFD700")
        bars[i].set_linewidth(2)
        ax.annotate("100 %", (i, p), ha="center", va="bottom", fontweight="bold",
                    fontsize=11, color="#4A0E0E")

ax.set_xticks(range(len(periods)))
ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Stolar med mahogni (%)")
ax.set_title("Mahogniens boge: NMK-samlinga, 1600-2024")
ax.set_ylim(0, 115)
ax.axhline(y=50, color="gray", linestyle=":", linewidth=0.7, alpha=0.5)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.savefig(f"{FIG_DIR}/fig1_mahogni_boge.pdf")
plt.close()

# ==========================================================
# FIGUR 2: SHANNON-ENTROPI OVER TID (bits)
# ==========================================================
print("Fig 2: Shannon-entropi...")
century_mats = defaultdict(list)
for r in rows:
    if r["_century"] and r["_mats"]:
        century_mats[r["_century"]].extend(r["_mats"])

def entropy_bits(materials):
    counts = Counter(materials)
    total = sum(counts.values())
    return -sum((n/total) * math.log2(n/total) for n in counts.values() if n > 0)

entropies = []
for c in centuries:
    if century_mats[c]:
        entropies.append((c, entropy_bits(century_mats[c]), len(set(century_mats[c]))))

fig, ax1 = plt.subplots(figsize=(7, 4.5))
cs = [e[0] for e in entropies]
hs = [e[1] for e in entropies]
ss = [e[2] for e in entropies]

color1 = "#2C3E50"
color2 = "#E74C3C"
ax1.plot(range(len(cs)), hs, "o-", color=color1, linewidth=2, markersize=6, label="H' (bits)")
ax1.set_ylabel("Shannon-entropi H' (bits)", color=color1)
ax1.set_ylim(0, 6)
ax1.tick_params(axis="y", labelcolor=color1)

ax2 = ax1.twinx()
ax2.bar(range(len(cs)), ss, alpha=0.3, color=color2, label="Unike materialar (S)")
ax2.set_ylabel("Unike materialar (S)", color=color2)
ax2.tick_params(axis="y", labelcolor=color2)

ax1.set_xticks(range(len(cs)))
ax1.set_xticklabels(cs, rotation=45, ha="right", fontsize=8)
ax1.set_title("Materialentropi og -rikdom per hundreaar")
ax1.spines["top"].set_visible(False)
fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.92), fontsize=9)
fig.savefig(f"{FIG_DIR}/fig2_entropi.pdf")
plt.close()

# ==========================================================
# FIGUR 3: MATERIALKATEGORIAR OVER TID (stacked area)
# ==========================================================
print("Fig 3: Materialkategoriar...")
local_woods = {"Bjørk", "Furu", "Eik", "Ask", "Or", "Alm", "Gran", "Bøk", "Osp", "Lind"}
global_woods = {"Mahogni", "Teak", "Palisander", "Ibenholt", "Rotting", "Bambus", "Palme",
                "Jakaranda", "Nøttetre"}
metals = {"Messing", "Bronse", "Jern", "Stål", "Aluminium", "Krom", "Sink", "Metall",
          "Stålrør", "Sølv"}
industrials = {"Plast", "Glasfiber", "Polypropylen", "Polyuretan", "Skumplast", "Nylon",
               "Polyester", "Polykarbonat", "Akryl", "Gummi", "Kunstlær", "Linoleum",
               "Melamin", "Polyamid", "Polyetylen", "Sponplate", "Syntetisk fiber"}
textiles = {"Silke", "Tekstil", "Bomull", "Lin", "Ull", "Fløyel", "Lær", "Skinn",
            "Strie", "Hestetagl", "Plysj", "Kunstsilke", "Stramei", "Filt"}

cat_data = {cat: [] for cat in ["Lokalt tre", "Koloniale materialar", "Tekstil/lær",
                                  "Metall", "Industrielt", "Anna"]}

for c in main_centuries:
    mats = century_mats.get(c, [])
    total = len(mats) if mats else 1
    n_local = sum(1 for m in mats if m in local_woods)
    n_global = sum(1 for m in mats if m in global_woods)
    n_metal = sum(1 for m in mats if m in metals)
    n_indust = sum(1 for m in mats if m in industrials)
    n_textile = sum(1 for m in mats if m in textiles)
    n_other = total - n_local - n_global - n_metal - n_indust - n_textile
    cat_data["Lokalt tre"].append(100 * n_local / total)
    cat_data["Koloniale materialar"].append(100 * n_global / total)
    cat_data["Tekstil/lær"].append(100 * n_textile / total)
    cat_data["Metall"].append(100 * n_metal / total)
    cat_data["Industrielt"].append(100 * n_indust / total)
    cat_data["Anna"].append(100 * n_other / total)

fig, ax = plt.subplots(figsize=(8, 5))
colors = ["#228B22", "#8B4513", "#DAA520", "#708090", "#FF4500", "#D3D3D3"]
cats = ["Lokalt tre", "Koloniale materialar", "Tekstil/lær", "Metall", "Industrielt", "Anna"]
bottom = np.zeros(len(main_centuries))
for cat, color in zip(cats, colors):
    vals = cat_data[cat]
    ax.bar(range(len(main_centuries)), vals, bottom=bottom, color=color, label=cat,
           edgecolor="white", linewidth=0.3)
    bottom += np.array(vals)

ax.set_xticks(range(len(main_centuries)))
ax.set_xticklabels(main_centuries, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Prosentdel av materialfoerekomstar")
ax.set_title("Tre materialepokar: lokalt, kolonialt, industrielt")
ax.legend(loc="upper left", fontsize=8, ncol=2)
ax.set_ylim(0, 105)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.savefig(f"{FIG_DIR}/fig3_materialkategoriar.pdf")
plt.close()

# ==========================================================
# FIGUR 4: JACCARD-AVSTAND NMK vs V&A
# ==========================================================
print("Fig 4: Jaccard...")
nmk_mats = defaultdict(set)
va_mats = defaultdict(set)
for r in rows:
    if r["_century"] and r["_mats"]:
        if r["_museum"] == "NMK":
            nmk_mats[r["_century"]].update(r["_mats"])
        else:
            va_mats[r["_century"]].update(r["_mats"])

jaccard_cs = []
jaccard_ds = []
for c in main_centuries:
    if nmk_mats[c] and va_mats[c]:
        inter = nmk_mats[c] & va_mats[c]
        union = nmk_mats[c] | va_mats[c]
        d = 1 - len(inter) / len(union) if union else 1
        jaccard_cs.append(c)
        jaccard_ds.append(d)

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(range(len(jaccard_cs)), jaccard_ds, "s-", color="#2C3E50", linewidth=2, markersize=8)
for i, (c, d) in enumerate(zip(jaccard_cs, jaccard_ds)):
    ax.annotate(f"{d:.2f}", (i, d), textcoords="offset points", xytext=(0, 10),
                ha="center", fontsize=9)
ax.set_xticks(range(len(jaccard_cs)))
ax.set_xticklabels(jaccard_cs, rotation=45, ha="right")
ax.set_ylabel("Jaccard-avstand")
ax.set_title("Materialkonvergens: NMK vs. V&A")
ax.set_ylim(0, 1.1)
ax.axhline(y=0.5, color="gray", linestyle=":", linewidth=0.7, alpha=0.5)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.savefig(f"{FIG_DIR}/fig4_jaccard.pdf")
plt.close()

# ==========================================================
# FIGUR 5: HOEGDE OVER TID + MODULOR
# ==========================================================
print("Fig 5: Hoegde og Modulor...")
century_heights = defaultdict(list)
for r in rows:
    if r["_century"] and r["_h"]:
        century_heights[r["_century"]].append(r["_h"])

fig, ax = plt.subplots(figsize=(7, 4.5))
plot_cs = [c for c in main_centuries if century_heights[c]]
means = [statistics.mean(century_heights[c]) for c in plot_cs]
medians = [statistics.median(century_heights[c]) for c in plot_cs]
sds = [statistics.stdev(century_heights[c]) if len(century_heights[c]) > 1 else 0 for c in plot_cs]

ax.errorbar(range(len(plot_cs)), means, yerr=sds, fmt="o-", color="#2C3E50",
            linewidth=2, markersize=6, capsize=4, label="Gj.snitt +/- SD")
ax.plot(range(len(plot_cs)), medians, "s--", color="#27AE60", markersize=5, label="Median")
ax.axhline(y=113, color="#E74C3C", linestyle="-.", linewidth=2, label="Modulor (113 cm)")
ax.fill_between(range(len(plot_cs)), [113]*len(plot_cs), means,
                alpha=0.1, color="#E74C3C")

ax.set_xticks(range(len(plot_cs)))
ax.set_xticklabels(plot_cs, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Hogde (cm)")
ax.set_title("Hogdekurva og Modulor-avvik")
ax.legend(fontsize=9)
ax.set_ylim(40, 140)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.savefig(f"{FIG_DIR}/fig5_hogde_modulor.pdf")
plt.close()

# ==========================================================
# FIGUR 6: H/W-RATIO DRIFT
# ==========================================================
print("Fig 6: H/W-ratio...")
century_hw = defaultdict(list)
for r in rows:
    if r["_century"] and r["_h"] and r["_w"] and r["_w"] > 0:
        century_hw[r["_century"]].append(r["_h"] / r["_w"])

fig, ax = plt.subplots(figsize=(7, 4))
plot_cs = [c for c in main_centuries if len(century_hw[c]) > 5]
hw_means = [statistics.mean(century_hw[c]) for c in plot_cs]
hw_medians = [statistics.median(century_hw[c]) for c in plot_cs]

ax.plot(range(len(plot_cs)), hw_means, "o-", color="#2C3E50", linewidth=2, label="Gj.snitt H/W")
ax.plot(range(len(plot_cs)), hw_medians, "s--", color="#27AE60", label="Median H/W")
phi = (1 + math.sqrt(5)) / 2
ax.axhline(y=phi, color="#E67E22", linestyle="-.", linewidth=2,
           label=f"Gullsnitt (phi = {phi:.3f})")
ax.set_xticks(range(len(plot_cs)))
ax.set_xticklabels(plot_cs, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("H/W-ratio")
ax.set_title("Proporsjonsdrift: H/W-ratio per hundreaar")
ax.legend(fontsize=9)
ax.set_ylim(0.8, 2.2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.savefig(f"{FIG_DIR}/fig6_hw_ratio.pdf")
plt.close()

# ==========================================================
# FIGUR 7: FEATURE IMPORTANCE (RF stilprediksjon)
# ==========================================================
print("Fig 7: Feature importance...")
# Hardkoda fraa analysen (fraa artikkel_III_rf.py)
features = ["Hogde", "Breidde", "Djupn", "Setehogde", "Bok", "Buksbom",
            "Mahogni", "Silke", "Hestetagl", "Messing", "Eik", "Furu"]
importances = [0.197, 0.140, 0.120, 0.110, 0.038, 0.037, 0.036, 0.035, 0.035, 0.023, 0.022, 0.022]

fig, ax = plt.subplots(figsize=(6, 5))
colors = ["#2C3E50"]*4 + ["#8B4513"]*8
y_pos = range(len(features)-1, -1, -1)
ax.barh(y_pos, importances, color=colors, edgecolor="white", height=0.7)
ax.set_yticks(y_pos)
ax.set_yticklabels(features)
ax.set_xlabel("Feature importance")
ax.set_title("Variabelviktigheit for stilklassifisering (RF)")
# Add dimension vs material annotation
ax.axvline(x=0.05, color="gray", linestyle=":", linewidth=0.5)
ax.text(0.15, 10.5, "DIMENSJONAR\n(56.7 % samla)", fontsize=8, color="#2C3E50", fontweight="bold")
ax.text(0.03, 3, "MATERIALAR", fontsize=8, color="#8B4513", fontweight="bold")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.savefig(f"{FIG_DIR}/fig7_feature_importance.pdf")
plt.close()

# ==========================================================
# FIGUR 8: TEKNIKK-ENTROPI
# ==========================================================
print("Fig 8: Teknikk-entropi...")
century_techs = defaultdict(list)
for r in rows:
    if r["_century"]:
        techs = r.get("Teknikk", "").strip()
        if techs:
            century_techs[r["_century"]].extend([t.strip() for t in techs.split(",") if t.strip()])

tech_cs = []
tech_hs = []
for c in main_centuries:
    ts = century_techs.get(c, [])
    if len(ts) < 5: continue
    counts = Counter(ts)
    total = sum(counts.values())
    H = -sum((n/total) * math.log2(n/total) for n in counts.values() if n > 0)
    tech_cs.append(c)
    tech_hs.append(H)

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(range(len(tech_cs)), tech_hs, "D-", color="#8E44AD", linewidth=2, markersize=7,
        label="Teknikk H' (bits)")
# Also plot material entropy for comparison
mat_hs_comp = []
for c in tech_cs:
    if century_mats[c]:
        mat_hs_comp.append(entropy_bits(century_mats[c]))
    else:
        mat_hs_comp.append(0)
ax.plot(range(len(tech_cs)), mat_hs_comp, "o--", color="#2C3E50", linewidth=1.5,
        markersize=5, alpha=0.6, label="Material H' (bits)")

ax.set_xticks(range(len(tech_cs)))
ax.set_xticklabels(tech_cs, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Shannon-entropi H' (bits)")
ax.set_title("Parallell stigning: material- og teknikk-entropi")
ax.legend(fontsize=9)
ax.set_ylim(0, 6)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.savefig(f"{FIG_DIR}/fig8_teknikk_entropi.pdf")
plt.close()

# ==========================================================
# FIGUR 9: NMK vs V&A hoegde
# ==========================================================
print("Fig 9: NMK vs V&A hoegde...")
nmk_heights = defaultdict(list)
va_heights = defaultdict(list)
for r in rows:
    if r["_century"] and r["_h"]:
        if r["_museum"] == "NMK":
            nmk_heights[r["_century"]].append(r["_h"])
        else:
            va_heights[r["_century"]].append(r["_h"])

plot_cs = [c for c in main_centuries if nmk_heights[c] and va_heights[c]]
nmk_m = [statistics.mean(nmk_heights[c]) for c in plot_cs]
va_m = [statistics.mean(va_heights[c]) for c in plot_cs]

fig, ax = plt.subplots(figsize=(7, 4.5))
x = np.arange(len(plot_cs))
w = 0.35
ax.bar(x - w/2, nmk_m, w, color="#1B4F72", label="NMK (Noreg)")
ax.bar(x + w/2, va_m, w, color="#CB4335", label="V&A (Storbritannia)")
ax.set_xticks(x)
ax.set_xticklabels(plot_cs, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Gj.snittleg hogde (cm)")
ax.set_title("Norske vs. britiske stolar: hogde per hundreaar")
ax.legend(fontsize=9)
ax.set_ylim(0, 130)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.savefig(f"{FIG_DIR}/fig9_nmk_va_hogde.pdf")
plt.close()

# ==========================================================
# FIGUR 10: Materiell dobbeltheit
# ==========================================================
print("Fig 10: Materiell dobbeltheit...")
local_set = {"Bjørk", "Furu", "Eik", "Ask", "Or", "Alm", "Gran", "Bøk", "Osp", "Lind"}
import_set = {"Mahogni", "Palisander", "Ibenholt", "Rotting", "Teak", "Bambus", "Silke", "Fløyel"}
dobbelt_cs = []
dobbelt_pcts = []
for c in main_centuries:
    items = [r for r in rows if r["_century"] == c]
    n_double = sum(1 for r in items if (set(r["_mats"]) & local_set) and (set(r["_mats"]) & import_set))
    if items:
        dobbelt_cs.append(c)
        dobbelt_pcts.append(100 * n_double / len(items))

fig, ax = plt.subplots(figsize=(6, 4))
ax.fill_between(range(len(dobbelt_cs)), dobbelt_pcts, alpha=0.3, color="#8B4513")
ax.plot(range(len(dobbelt_cs)), dobbelt_pcts, "o-", color="#8B4513", linewidth=2, markersize=6)
ax.set_xticks(range(len(dobbelt_cs)))
ax.set_xticklabels(dobbelt_cs, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Andel stolar (%)")
ax.set_title("Materiell dobbeltheit: lokalt berande + importert fasade")
ax.set_ylim(0, 30)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.savefig(f"{FIG_DIR}/fig10_dobbeltheit.pdf")
plt.close()

print(f"\nAlle figurar lagra i {FIG_DIR}/")
for f in sorted(os.listdir(FIG_DIR)):
    print(f"  {f}")
