"""
STOLAR figurar v2 - publikasjonskvalitet.
Profesjonell akademisk stil, detaljerte annotasjonar, nynorske etiketter.
"""
import csv, math, os
from collections import Counter, defaultdict
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ---- Global styling ----
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Palatino', 'Book Antiqua', 'Georgia', 'Times New Roman'],
    'font.size': 9,
    'axes.titlesize': 11,
    'axes.titleweight': 'bold',
    'axes.labelsize': 10,
    'axes.linewidth': 0.6,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'legend.framealpha': 0.9,
    'legend.edgecolor': '0.8',
    'figure.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.2,
    'lines.linewidth': 1.5,
    'lines.markersize': 5,
})

# Fargekart
C_DARK = '#1a1a2e'
C_MAHOGNI = '#6b2c1a'
C_MAHOGNI_LIGHT = '#a0522d'
C_BLUE = '#2c3e6b'
C_RED = '#b03a2e'
C_GREEN = '#1e6b3a'
C_GOLD = '#c49b2a'
C_PURPLE = '#5b2c6f'
C_TEAL = '#117a65'
C_GREY = '#7f8c8d'
C_LIGHT = '#ecf0f1'

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
    except: return None

def get_museum(row):
    nm = row.get("Nasjonalmuseet", "")
    obj = row.get("Objekt-ID", "")
    if "nasjonalmuseet.no" in nm or obj.startswith("OK-") or obj.startswith("NMK"):
        return "NMK"
    return "V&A"

for r in rows:
    r["_museum"] = get_museum(r)
    r["_mats"] = [m.strip() for m in r.get("Materialar","").split(",") if m.strip()]
    r["_century"] = r.get("Hundreår", "").strip()
    try:
        y = int(r.get("Frå år","").strip())
        r["_year"] = y if y > 100 else None
    except: r["_year"] = None
    r["_h"] = safe_float(r.get("Høgde (cm)", ""))
    r["_w"] = safe_float(r.get("Breidde (cm)", ""))
    r["_d"] = safe_float(r.get("Djupn (cm)", ""))
    r["_style"] = r.get("Stilperiode", "").strip()

def cs(c):
    try: return int(c.split("-")[0])
    except: return 9999

centuries = sorted(set(r["_century"] for r in rows if r["_century"]), key=cs)
main_centuries = [c for c in centuries if c not in ("1200-talet", "1300-talet")]

century_mats = defaultdict(list)
for r in rows:
    if r["_century"] and r["_mats"]:
        century_mats[r["_century"]].extend(r["_mats"])

def entropy_bits(materials):
    counts = Counter(materials)
    total = sum(counts.values())
    return -sum((n/total)*math.log2(n/total) for n in counts.values() if n > 0)


# ==================================================================
# FIGUR 1: MAHOGNIENS BOGE (hovudfigur)
# ==================================================================
print("Fig 1: Mahogniens boge (v2)...")

period_data = defaultdict(lambda: {"total": 0, "mahogni": 0, "chairs_with": 0})
for r in rows:
    if r["_museum"] != "NMK" or r["_year"] is None: continue
    p = (r["_year"] // 25) * 25
    period_data[p]["total"] += 1
    if "Mahogni" in r["_mats"]:
        period_data[p]["chairs_with"] += 1

periods = sorted(p for p in period_data if p >= 1600 and period_data[p]["total"] >= 3)
pcts = [100*period_data[p]["chairs_with"]/period_data[p]["total"] for p in periods]
totals = [period_data[p]["total"] for p in periods]

fig, ax = plt.subplots(figsize=(9, 5))

# Gradient bar colors based on pct
colors = []
for p in pcts:
    if p >= 99:
        colors.append('#3d0c02')
    elif p >= 50:
        colors.append(C_MAHOGNI)
    elif p >= 20:
        colors.append(C_MAHOGNI_LIGHT)
    elif p > 0:
        colors.append('#c4956a')
    else:
        colors.append('#d5c4a1')

bars = ax.bar(range(len(periods)), pcts, color=colors, edgecolor='white', linewidth=0.8, width=0.8)

# Highlight the 100% bar
for i, (p, pct) in enumerate(zip(periods, pcts)):
    if pct >= 99:
        bars[i].set_edgecolor(C_GOLD)
        bars[i].set_linewidth(2.5)

# Annotate key points
ax.annotate('100 %\n(26/26 stolar)', xy=(periods.index(1825), 100),
            xytext=(periods.index(1825)+1.5, 108),
            fontsize=10, fontweight='bold', color='#3d0c02',
            arrowprops=dict(arrowstyle='->', color='#3d0c02', lw=1.5),
            ha='center')

ax.annotate('61,7 %\nakselerasjon', xy=(periods.index(1800), 61.7),
            xytext=(periods.index(1800)-2, 78),
            fontsize=8, color=C_MAHOGNI,
            arrowprops=dict(arrowstyle='->', color=C_MAHOGNI, lw=1),
            ha='center')

# N-labels on bars
for i, (pct, n) in enumerate(zip(pcts, totals)):
    if pct > 0:
        ax.text(i, pct + 1.5, f'n={n}', ha='center', va='bottom', fontsize=6.5, color=C_GREY)

# Period shading
ax.axvspan(periods.index(1775)-0.5, periods.index(1850)+0.5, alpha=0.06, color=C_MAHOGNI,
           label='Kolonial kulminasjon')

ax.set_xticks(range(len(periods)))
ax.set_xticklabels([f'{p}' for p in periods], rotation=55, ha='right')
ax.set_ylabel('Andel stolar med mahogni (%)')
ax.set_xlabel('25-arsperiode (NMK-samlinga)')
ax.set_title('Mahogniens boge: Nasjonalmuseet, 1600-2024')
ax.set_ylim(0, 120)
ax.axhline(y=50, color=C_GREY, linestyle=':', linewidth=0.5, alpha=0.4)
ax.legend(loc='upper left', fontsize=8)

fig.savefig(f"{FIG_DIR}/fig1_mahogni_boge.pdf")
plt.close()


# ==================================================================
# FIGUR 2: MATERIALENTROPI (dual-axis, meir detaljert)
# ==================================================================
print("Fig 2: Materialentropi (v2)...")

entropies = []
for c in centuries:
    if century_mats[c]:
        H = entropy_bits(century_mats[c])
        S = len(set(century_mats[c]))
        N = len([r for r in rows if r["_century"]==c and r["_mats"]])
        entropies.append((c, H, S, N))

fig, ax1 = plt.subplots(figsize=(8, 5))
cs_list = [e[0] for e in entropies]
hs = [e[1] for e in entropies]
ss = [e[2] for e in entropies]
ns = [e[3] for e in entropies]

# Bar for S (material richness)
ax2 = ax1.twinx()
bar_w = 0.6
ax2.bar(range(len(cs_list)), ss, alpha=0.2, color=C_RED, width=bar_w, label='Materialrikdom $S$')
ax2.set_ylabel('Unike materialar ($S$)', color=C_RED)
ax2.tick_params(axis='y', labelcolor=C_RED)
ax2.set_ylim(0, 80)

# Line for H'
ax1.plot(range(len(cs_list)), hs, 'o-', color=C_BLUE, linewidth=2.5, markersize=7,
         zorder=5, label="$H'$ (bits)")
# Annotate values
for i, (c, h, s, n) in enumerate(entropies):
    ax1.annotate(f'{h:.2f}', (i, h), textcoords='offset points', xytext=(0, 10),
                 ha='center', fontsize=7.5, color=C_BLUE, fontweight='bold')

# Mark the three regimes
ax1.axvspan(-0.5, 3.5, alpha=0.04, color=C_GREEN, label='Lokalt regime')
ax1.axvspan(3.5, 6.5, alpha=0.04, color=C_MAHOGNI, label='Kolonialt regime')
ax1.axvspan(6.5, 8.5, alpha=0.04, color=C_RED, label='Industrielt regime')

ax1.set_ylabel("Shannon-entropi $H'$ (bits)", color=C_BLUE)
ax1.set_ylim(0, 6.5)
ax1.tick_params(axis='y', labelcolor=C_BLUE)
ax1.set_xticks(range(len(cs_list)))
ax1.set_xticklabels(cs_list, rotation=45, ha='right')
ax1.set_title("Materialentropi og materialrikdom per hundreaar")

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=7.5)

fig.savefig(f"{FIG_DIR}/fig2_entropi.pdf")
plt.close()


# ==================================================================
# FIGUR 3: TRE MATERIALEPOKAR (stacked, forbedra)
# ==================================================================
print("Fig 3: Materialepokar (v2)...")

local_woods = {"Bjørk","Furu","Eik","Ask","Or","Alm","Gran","Bøk","Osp","Lind"}
colonial = {"Mahogni","Teak","Palisander","Ibenholt","Rotting","Bambus","Palme","Jakaranda","Nøttetre"}
metals = {"Messing","Bronse","Jern","Stål","Aluminium","Krom","Sink","Metall","Stålrør","Sølv"}
industrials = {"Plast","Glasfiber","Polypropylen","Polyuretan","Skumplast","Nylon","Polyester",
               "Polykarbonat","Akryl","Gummi","Kunstlær","Linoleum","Melamin","Polyamid",
               "Polyetylen","Sponplate","Syntetisk fiber","Kryssfiner"}
textiles = {"Silke","Tekstil","Bomull","Lin","Ull","Fløyel","Lær","Skinn","Strie",
            "Hestetagl","Plysj","Kunstsilke","Stramei","Filt"}

cats = ["Lokalt tre", "Kolonialt tre", "Tekstil og laar", "Metall", "Industrielt", "Anna"]
cat_colors = [C_GREEN, C_MAHOGNI, C_GOLD, C_GREY, C_RED, C_LIGHT]

cat_data = {c: [] for c in cats}
for century in main_centuries:
    mats = century_mats.get(century, [])
    total = max(len(mats), 1)
    vals = {
        "Lokalt tre": sum(1 for m in mats if m in local_woods),
        "Kolonialt tre": sum(1 for m in mats if m in colonial),
        "Tekstil og laar": sum(1 for m in mats if m in textiles),
        "Metall": sum(1 for m in mats if m in metals),
        "Industrielt": sum(1 for m in mats if m in industrials),
    }
    vals["Anna"] = total - sum(vals.values())
    for c in cats:
        cat_data[c].append(100 * vals.get(c, 0) / total)

fig, ax = plt.subplots(figsize=(8, 5.5))
bottom = np.zeros(len(main_centuries))
for cat, color in zip(cats, cat_colors):
    vals = np.array(cat_data[cat])
    ax.bar(range(len(main_centuries)), vals, bottom=bottom, color=color,
           label=cat, edgecolor='white', linewidth=0.4, width=0.75)
    # Label dominant category
    for i, (v, b) in enumerate(zip(vals, bottom)):
        if v > 15:
            ax.text(i, b + v/2, f'{v:.0f}%', ha='center', va='center',
                    fontsize=6.5, color='white' if color in [C_MAHOGNI, C_GREEN, C_RED, C_BLUE] else C_DARK)
    bottom += vals

ax.set_xticks(range(len(main_centuries)))
ax.set_xticklabels(main_centuries, rotation=45, ha='right')
ax.set_ylabel('Prosentdel av materialfoerekomstar')
ax.set_title('Tre materialepokar: lokalt, kolonialt, industrielt')
ax.legend(loc='upper right', fontsize=7.5, ncol=2)
ax.set_ylim(0, 108)

# Epoch labels
ax.text(0.5, 102, 'LOKALT', ha='center', fontsize=7, color=C_GREEN, fontweight='bold')
ax.text(3, 102, 'KOLONIALT', ha='center', fontsize=7, color=C_MAHOGNI, fontweight='bold')
ax.text(5.5, 102, 'INDUSTRIELT', ha='center', fontsize=7, color=C_RED, fontweight='bold')

fig.savefig(f"{FIG_DIR}/fig3_materialkategoriar.pdf")
plt.close()


# ==================================================================
# FIGUR 4: JACCARD-AVSTAND (forbedra)
# ==================================================================
print("Fig 4: Jaccard (v2)...")

nmk_mats_set = defaultdict(set)
va_mats_set = defaultdict(set)
for r in rows:
    if r["_century"] and r["_mats"]:
        if r["_museum"] == "NMK": nmk_mats_set[r["_century"]].update(r["_mats"])
        else: va_mats_set[r["_century"]].update(r["_mats"])

jc, jd, j_nmk, j_va, j_felles = [], [], [], [], []
for c in main_centuries:
    if nmk_mats_set[c] and va_mats_set[c]:
        inter = nmk_mats_set[c] & va_mats_set[c]
        union = nmk_mats_set[c] | va_mats_set[c]
        d = 1 - len(inter)/len(union)
        jc.append(c); jd.append(d)
        j_nmk.append(len(nmk_mats_set[c])); j_va.append(len(va_mats_set[c]))
        j_felles.append(len(inter))

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.fill_between(range(len(jc)), jd, alpha=0.15, color=C_BLUE)
ax.plot(range(len(jc)), jd, 's-', color=C_BLUE, linewidth=2.5, markersize=8)

for i, (c, d, nk, va, fl) in enumerate(zip(jc, jd, j_nmk, j_va, j_felles)):
    ax.annotate(f'{d:.2f}\n({fl} felles)', (i, d), textcoords='offset points',
                xytext=(0, 12), ha='center', fontsize=7.5, color=C_BLUE)

ax.set_xticks(range(len(jc)))
ax.set_xticklabels(jc, rotation=45, ha='right')
ax.set_ylabel('Jaccard-avstand ($d_J$)')
ax.set_xlabel('Hundreaar')
ax.set_title('Materialkonvergens: Nasjonalmuseet vs. Victoria and Albert Museum')
ax.set_ylim(0, 1.15)
ax.axhline(y=0.5, color=C_GREY, linestyle=':', linewidth=0.6, alpha=0.5)
ax.text(len(jc)-1.5, 0.08, 'Konvergens\n(globaliseringseffekt)', fontsize=8,
        ha='center', color=C_TEAL, style='italic')
ax.text(0.5, 0.92, 'Divergens\n(ulike materialverder)', fontsize=8,
        ha='center', color=C_RED, style='italic')

fig.savefig(f"{FIG_DIR}/fig4_jaccard.pdf")
plt.close()


# ==================================================================
# FIGUR 5: HOGDE + MODULOR (forbedra)
# ==================================================================
print("Fig 5: Hogde + Modulor (v2)...")

century_h = defaultdict(list)
nmk_h = defaultdict(list)
va_h = defaultdict(list)
for r in rows:
    if r["_century"] and r["_h"]:
        century_h[r["_century"]].append(r["_h"])
        if r["_museum"] == "NMK": nmk_h[r["_century"]].append(r["_h"])
        else: va_h[r["_century"]].append(r["_h"])

plot_cs = [c for c in main_centuries if len(century_h[c]) > 3]
means = [statistics.mean(century_h[c]) for c in plot_cs]
meds = [statistics.median(century_h[c]) for c in plot_cs]
q25 = [np.percentile(century_h[c], 25) for c in plot_cs]
q75 = [np.percentile(century_h[c], 75) for c in plot_cs]

fig, ax = plt.subplots(figsize=(8, 5))

# IQR band
ax.fill_between(range(len(plot_cs)), q25, q75, alpha=0.15, color=C_BLUE, label='IQR (25.-75. persentil)')
ax.plot(range(len(plot_cs)), means, 'o-', color=C_BLUE, linewidth=2, markersize=6, label='Gjennomsnitt')
ax.plot(range(len(plot_cs)), meds, 's--', color=C_TEAL, linewidth=1.5, markersize=5, label='Median')

# Modulor
ax.axhline(y=113, color=C_RED, linestyle='-.', linewidth=2, label='Le Modulor (113 cm)')
ax.fill_between(range(len(plot_cs)), [113]*len(plot_cs), means, alpha=0.08, color=C_RED)

# Annotate avvik
for i, (c, m) in enumerate(zip(plot_cs, means)):
    avvik = m - 113
    ax.annotate(f'{avvik:+.0f}', (i, m), textcoords='offset points', xytext=(0, -15),
                ha='center', fontsize=7, color=C_RED)

ax.set_xticks(range(len(plot_cs)))
ax.set_xticklabels(plot_cs, rotation=45, ha='right')
ax.set_ylabel('Hogde (cm)')
ax.set_title('Stolhogde og Modulor-avvik per hundreaar')
ax.legend(loc='upper right', fontsize=8)
ax.set_ylim(40, 135)

fig.savefig(f"{FIG_DIR}/fig5_hogde_modulor.pdf")
plt.close()


# ==================================================================
# FIGUR 6: H/W-RATIO (forbedra)
# ==================================================================
print("Fig 6: H/W-ratio (v2)...")

century_hw = defaultdict(list)
for r in rows:
    if r["_century"] and r["_h"] and r["_w"] and r["_w"] > 0:
        century_hw[r["_century"]].append(r["_h"]/r["_w"])

plot_cs = [c for c in main_centuries if len(century_hw[c]) > 5]
hw_means = [statistics.mean(century_hw[c]) for c in plot_cs]
hw_meds = [statistics.median(century_hw[c]) for c in plot_cs]
hw_q25 = [np.percentile(century_hw[c], 25) for c in plot_cs]
hw_q75 = [np.percentile(century_hw[c], 75) for c in plot_cs]

fig, ax = plt.subplots(figsize=(8, 4.5))
phi = (1+math.sqrt(5))/2

ax.fill_between(range(len(plot_cs)), hw_q25, hw_q75, alpha=0.12, color=C_PURPLE)
ax.plot(range(len(plot_cs)), hw_means, 'o-', color=C_PURPLE, linewidth=2, markersize=6, label='Gj.snitt $H/W$')
ax.plot(range(len(plot_cs)), hw_meds, 's--', color=C_TEAL, linewidth=1.5, markersize=4, label='Median $H/W$')
ax.axhline(y=phi, color=C_GOLD, linestyle='-.', linewidth=2, label=f'Gullsnitt $\\varphi$ = {phi:.3f}')
ax.axhline(y=1.0, color=C_GREY, linestyle=':', linewidth=0.7, alpha=0.5)

ax.set_xticks(range(len(plot_cs)))
ax.set_xticklabels(plot_cs, rotation=45, ha='right')
ax.set_ylabel('$H/W$-ratio')
ax.set_title('Proporsjonsdrift: stolen vert breiare relativt til hogda')
ax.legend(loc='upper right', fontsize=8)
ax.set_ylim(0.6, 2.5)

# Annotate the crossing
for i, (m, c) in enumerate(zip(hw_means, plot_cs)):
    if i > 0 and hw_means[i-1] > phi and m < phi:
        ax.annotate('Gullsnittet\npassert', (i-0.5, phi), textcoords='offset points',
                    xytext=(25, 15), fontsize=8, color=C_GOLD, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color=C_GOLD))

fig.savefig(f"{FIG_DIR}/fig6_hw_ratio.pdf")
plt.close()


# ==================================================================
# FIGUR 7: FEATURE IMPORTANCE (forbedra)
# ==================================================================
print("Fig 7: Feature importance (v2)...")

features = ["Hogde", "Breidde", "Djupn", "Setehogde", "Bok (Bøk)", "Buksbom",
            "Mahogni", "Silke", "Hestetagl", "Messing", "Eik", "Furu"]
importances = [0.197, 0.140, 0.120, 0.110, 0.038, 0.037, 0.036, 0.035, 0.035, 0.023, 0.022, 0.022]

fig, ax = plt.subplots(figsize=(7, 5.5))

# Color by type
colors = [C_BLUE]*4 + [C_MAHOGNI]*8
y_pos = np.arange(len(features)-1, -1, -1)
bars = ax.barh(y_pos, importances, color=colors, edgecolor='white', height=0.65)

# Value labels
for i, (imp, y) in enumerate(zip(importances, y_pos)):
    ax.text(imp + 0.003, y, f'{imp:.1%}', va='center', fontsize=8,
            color=colors[i], fontweight='bold')

ax.set_yticks(y_pos)
ax.set_yticklabels(features, fontsize=9)
ax.set_xlabel('Feature importance (Random Forest)')
ax.set_title('Kva predikerer stilperiode? Variabelviktigheit')

# Separator line
ax.axhline(y=7.5, color=C_GREY, linestyle='-', linewidth=0.8, alpha=0.4)

# Category annotations
ax.text(0.17, 10, 'DIMENSJONAR', fontsize=9, color=C_BLUE, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=C_BLUE, alpha=0.8))
ax.text(0.17, 5, 'MATERIALAR', fontsize=9, color=C_MAHOGNI, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=C_MAHOGNI, alpha=0.8))

# Summary
ax.text(0.12, -1.2, 'Dimensjonar: 56,7 % samla    |    Materialar: 43,3 % samla',
        fontsize=8, color=C_GREY, style='italic', transform=ax.transData)

ax.set_xlim(0, 0.25)
fig.savefig(f"{FIG_DIR}/fig7_feature_importance.pdf")
plt.close()


# ==================================================================
# FIGUR 8: TEKNIKK vs MATERIAL ENTROPI (forbedra)
# ==================================================================
print("Fig 8: Teknikk+material entropi (v2)...")

century_techs = defaultdict(list)
for r in rows:
    if r["_century"]:
        ts = r.get("Teknikk", "").strip()
        if ts: century_techs[r["_century"]].extend([t.strip() for t in ts.split(",") if t.strip()])

tech_cs, tech_hs, mat_hs_c = [], [], []
for c in main_centuries:
    ts = century_techs.get(c, [])
    if len(ts) < 5: continue
    tech_cs.append(c)
    tech_hs.append(entropy_bits(ts))
    mat_hs_c.append(entropy_bits(century_mats[c]) if century_mats[c] else 0)

fig, ax = plt.subplots(figsize=(7, 4.5))
x = range(len(tech_cs))
ax.plot(x, mat_hs_c, 'o-', color=C_BLUE, linewidth=2.5, markersize=7, label="Material $H'$")
ax.plot(x, tech_hs, 'D-', color=C_PURPLE, linewidth=2.5, markersize=7, label="Teknikk $H'$")

ax.fill_between(x, tech_hs, mat_hs_c, alpha=0.08, color=C_GREY)

for i, (mh, th) in enumerate(zip(mat_hs_c, tech_hs)):
    ax.annotate(f'{mh:.1f}', (i, mh), textcoords='offset points', xytext=(-12, 8),
                fontsize=7, color=C_BLUE)
    ax.annotate(f'{th:.1f}', (i, th), textcoords='offset points', xytext=(5, -12),
                fontsize=7, color=C_PURPLE)

ax.set_xticks(x)
ax.set_xticklabels(tech_cs, rotation=45, ha='right')
ax.set_ylabel("Shannon-entropi $H'$ (bits)")
ax.set_title('Parallell stigning: material- og teknikkdiversitet')
ax.legend(loc='upper left', fontsize=9)
ax.set_ylim(0, 6)

fig.savefig(f"{FIG_DIR}/fig8_teknikk_entropi.pdf")
plt.close()


# ==================================================================
# FIGUR 9: NMK vs V&A HOGDE (forbedra)
# ==================================================================
print("Fig 9: NMK vs V&A (v2)...")

plot_cs9 = [c for c in main_centuries if nmk_h[c] and va_h[c]]
nmk_m = [statistics.mean(nmk_h[c]) for c in plot_cs9]
va_m = [statistics.mean(va_h[c]) for c in plot_cs9]
deltas = [n-v for n,v in zip(nmk_m, va_m)]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), height_ratios=[3, 1.3], sharex=True)
fig.subplots_adjust(hspace=0.08)

x = np.arange(len(plot_cs9))
w = 0.35
ax1.bar(x-w/2, nmk_m, w, color=C_BLUE, label='NMK (Noreg)', edgecolor='white')
ax1.bar(x+w/2, va_m, w, color=C_RED, label='V&A (Storbritannia)', edgecolor='white')

for i, (n, v) in enumerate(zip(nmk_m, va_m)):
    ax1.text(i-w/2, n+1.5, f'{n:.0f}', ha='center', fontsize=7, color=C_BLUE)
    ax1.text(i+w/2, v+1.5, f'{v:.0f}', ha='center', fontsize=7, color=C_RED)

ax1.set_ylabel('Gj.snittleg hogde (cm)')
ax1.set_title('Norske vs. britiske stolar: hogde per hundreaar')
ax1.legend(fontsize=9)
ax1.set_ylim(0, 130)

# Delta subplot
colors_d = [C_BLUE if d > 0 else C_RED for d in deltas]
ax2.bar(x, deltas, color=colors_d, edgecolor='white', width=0.6)
ax2.axhline(y=0, color=C_DARK, linewidth=0.8)
for i, d in enumerate(deltas):
    ax2.text(i, d + (1.5 if d > 0 else -3), f'{d:+.1f}', ha='center', fontsize=7.5,
             color=colors_d[i], fontweight='bold')
ax2.set_ylabel('$\\Delta$ (NMK $-$ V&A)')
ax2.set_xticks(x)
ax2.set_xticklabels(plot_cs9, rotation=45, ha='right')
ax2.set_ylim(min(deltas)-8, max(deltas)+8)

fig.savefig(f"{FIG_DIR}/fig9_nmk_va_hogde.pdf")
plt.close()


# ==================================================================
# FIGUR 10: MATERIELL DOBBELTHEIT (forbedra)
# ==================================================================
print("Fig 10: Dobbeltheit (v2)...")

local_set = {"Bjørk","Furu","Eik","Ask","Or","Alm","Gran","Bøk","Osp","Lind"}
import_set = {"Mahogni","Palisander","Ibenholt","Rotting","Teak","Bambus","Silke","Fløyel"}

dbl_cs, dbl_pcts, dbl_ns = [], [], []
for c in main_centuries:
    items = [r for r in rows if r["_century"] == c]
    n_dbl = sum(1 for r in items if (set(r["_mats"]) & local_set) and (set(r["_mats"]) & import_set))
    if items:
        dbl_cs.append(c)
        dbl_pcts.append(100*n_dbl/len(items))
        dbl_ns.append(n_dbl)

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.fill_between(range(len(dbl_cs)), dbl_pcts, alpha=0.2, color=C_MAHOGNI)
ax.plot(range(len(dbl_cs)), dbl_pcts, 'o-', color=C_MAHOGNI, linewidth=2.5, markersize=7)

for i, (pct, n) in enumerate(zip(dbl_pcts, dbl_ns)):
    if pct > 1:
        ax.annotate(f'{pct:.1f}%\n(n={n})', (i, pct), textcoords='offset points',
                    xytext=(0, 10), ha='center', fontsize=7.5, color=C_MAHOGNI)

ax.set_xticks(range(len(dbl_cs)))
ax.set_xticklabels(dbl_cs, rotation=45, ha='right')
ax.set_ylabel('Andel stolar (%)')
ax.set_title('Materiell dobbeltheit: berande lokalt + importert fasade')
ax.set_ylim(0, 32)

# Annotation
peak_i = dbl_pcts.index(max(dbl_pcts))
ax.annotate('Kolonial\nkulminasjon', (peak_i, max(dbl_pcts)),
            textcoords='offset points', xytext=(30, 5), fontsize=8,
            color=C_MAHOGNI, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=C_MAHOGNI))

fig.savefig(f"{FIG_DIR}/fig10_dobbeltheit.pdf")
plt.close()


print(f"\n{'='*50}")
print(f"Alle figurar (v2) lagra i {FIG_DIR}/")
for f in sorted(os.listdir(FIG_DIR)):
    size = os.path.getsize(f"{FIG_DIR}/{f}")
    print(f"  {f:40s} {size//1024:>4d} KB")
