"""
STOLAR figurar batch 2 (fig 17-22) - publikasjonskvalitet.
Profesjonell akademisk stil, detaljerte annotasjonar, nynorske etiketter.
"""
import csv, math, os
from collections import Counter, defaultdict
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.patches import Ellipse
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
C_ORANGE = '#d35400'
C_PINK = '#c0392b'

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "stolar_db.csv")
FIG_DIR = os.path.join(os.path.dirname(__file__), "..", "texts", "fig")
os.makedirs(FIG_DIR, exist_ok=True)

# ---- Load data ----
rows = []
with open(CSV_PATH, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        rows.append(row)

def sf(v):
    """Safe float conversion."""
    try:
        x = float(v.replace(",", "."))
        return x if x > 0 else None
    except (ValueError, AttributeError):
        return None

def get_museum(row):
    nm = row.get("Nasjonalmuseet", "")
    obj = row.get("Objekt-ID", "")
    if "nasjonalmuseet.no" in nm or obj.startswith("OK-") or obj.startswith("NMK"):
        return "NMK"
    return "V&A"

def century_sort(c):
    try:
        return int(c.split("-")[0])
    except (ValueError, IndexError):
        return 9999

# Enrich rows
for r in rows:
    r["_museum"] = get_museum(r)
    r["_mats"] = [m.strip() for m in r.get("Materialar", "").split(",") if m.strip()]
    r["_century"] = r.get("Hundreår", "").strip()
    r["_style"] = r.get("Stilperiode", "").strip()
    r["_h"] = sf(r.get("Høgde (cm)", ""))
    r["_w"] = sf(r.get("Breidde (cm)", ""))
    r["_d"] = sf(r.get("Djupn (cm)", ""))
    r["_weight"] = sf(r.get("Estimert vekt (kg)", ""))
    r["_produsent"] = r.get("Produsent", "").strip()
    try:
        y = int(r.get("Frå år", "").strip())
        r["_year"] = y if y > 100 else None
    except (ValueError, AttributeError):
        r["_year"] = None


def entropy_bits(materials):
    """Shannon entropy in bits."""
    counts = Counter(materials)
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum((n / total) * math.log2(n / total) for n in counts.values() if n > 0)


# ==================================================================
# FIGUR 17: MATERIAL SUCCESSION (stacked area, NMK)
# ==================================================================
print("Fig 17: Materialsuksesjon (stacked area)...")

# Target materials for the stacked area
target_mats = ["Mahogni", "Eik", "Bjørk", "Furu", "Bøk", "Stål", "Kryssfiner", "Plast"]
mat_colors = {
    "Mahogni": C_MAHOGNI,
    "Eik": '#8B7355',
    "Bjørk": '#D4A76A',
    "Furu": '#9ACD32',
    "Bøk": '#BC8F8F',
    "Stål": '#708090',
    "Kryssfiner": '#DEB887',
    "Plast": C_RED,
}

# Build decade data for NMK
nmk_rows = [r for r in rows if r["_museum"] == "NMK" and r["_year"] is not None]
decade_mat_counts = defaultdict(Counter)
decade_totals = defaultdict(int)

for r in nmk_rows:
    decade = (r["_year"] // 10) * 10
    decade_totals[decade] += 1
    for m in r["_mats"]:
        decade_mat_counts[decade][m] += 1

# Use decades from 1700-2020 (merge sparse early decades into 50-year blocks)
# Actually use 50-year periods to smooth the data
period_size = 50
period_mat_counts = defaultdict(Counter)
period_totals = defaultdict(int)

for r in nmk_rows:
    if r["_year"] < 1600:
        continue
    period = (r["_year"] // period_size) * period_size
    period_totals[period] += 1
    for m in r["_mats"]:
        period_mat_counts[period][m] += 1

periods = sorted(p for p in period_totals if 1600 <= p <= 2020 and period_totals[p] >= 3)

# Compute percentages
mat_pcts = {}
for mat in target_mats:
    mat_pcts[mat] = []
    for p in periods:
        total = period_totals[p]
        count = period_mat_counts[p].get(mat, 0)
        mat_pcts[mat].append(100 * count / total if total > 0 else 0)

fig, ax = plt.subplots(figsize=(9, 5.5))
x = np.arange(len(periods))
labels = [str(p) for p in periods]

# Stack the areas
bottoms = np.zeros(len(periods))
for mat in target_mats:
    vals = np.array(mat_pcts[mat])
    ax.fill_between(x, bottoms, bottoms + vals, label=mat,
                    color=mat_colors[mat], alpha=0.85, linewidth=0.5, edgecolor='white')
    bottoms += vals

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
ax.set_ylabel('Prosentdel av stolar (%)')
ax.set_xlabel('Periode (50-aarsbolkar)')
ax.set_title('Materialsuksesjon i NMK-samlinga, 1600\u20132020')
ax.set_ylim(0, max(bottoms) * 1.05)
ax.legend(loc='upper left', ncol=2, fontsize=7, framealpha=0.9)

# Annotate mahogni peak
mah_vals = mat_pcts["Mahogni"]
peak_idx = mah_vals.index(max(mah_vals))
peak_val = mah_vals[peak_idx]
ax.annotate(f'Mahogni-topp\n{peak_val:.0f} %',
            xy=(peak_idx, bottoms[peak_idx] * 0.3),
            xytext=(peak_idx + 1.5, bottoms[peak_idx] * 0.5 + 20),
            fontsize=8, fontweight='bold', color=C_MAHOGNI,
            arrowprops=dict(arrowstyle='->', color=C_MAHOGNI, lw=1.2),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor=C_MAHOGNI))

fig.savefig(os.path.join(FIG_DIR, "fig17_material_succession.pdf"))
plt.close()
print("  -> fig17_material_succession.pdf")


# ==================================================================
# FIGUR 18: MATERIAL COMPLEXITY (mean materials per chair over time)
# ==================================================================
print("Fig 18: Materialkompleksitet over tid...")

period_size_18 = 25
period_mat_counts_18 = defaultdict(list)

for r in rows:
    if r["_year"] is not None and r["_mats"]:
        p = (r["_year"] // period_size_18) * period_size_18
        period_mat_counts_18[p].append(len(r["_mats"]))

periods_18 = sorted(p for p in period_mat_counts_18 if p >= 1600 and len(period_mat_counts_18[p]) >= 5)
means_18 = [statistics.mean(period_mat_counts_18[p]) for p in periods_18]
sds_18 = [statistics.stdev(period_mat_counts_18[p]) if len(period_mat_counts_18[p]) > 1 else 0 for p in periods_18]
ns_18 = [len(period_mat_counts_18[p]) for p in periods_18]

fig, ax = plt.subplots(figsize=(9, 5))
x18 = np.arange(len(periods_18))

ax.errorbar(x18, means_18, yerr=sds_18, fmt='o-', color=C_BLUE,
            ecolor=C_GREY, elinewidth=1, capsize=3, capthick=1,
            markersize=6, linewidth=1.8, markerfacecolor=C_BLUE,
            markeredgecolor='white', markeredgewidth=0.8, zorder=5)

# Fill a subtle band for SD
means_arr = np.array(means_18)
sds_arr = np.array(sds_18)
ax.fill_between(x18, means_arr - sds_arr, means_arr + sds_arr,
                alpha=0.12, color=C_BLUE)

# Annotate the peak period
peak_idx_18 = means_18.index(max(means_18))
peak_val_18 = means_18[peak_idx_18]
ax.annotate(f'Topp: {peak_val_18:.1f} materialar\n({periods_18[peak_idx_18]}\u2013{periods_18[peak_idx_18]+24})',
            xy=(peak_idx_18, peak_val_18),
            xytext=(peak_idx_18 - 2, peak_val_18 + 1.2),
            fontsize=8, fontweight='bold', color=C_DARK,
            arrowprops=dict(arrowstyle='->', color=C_DARK, lw=1.2),
            bbox=dict(boxstyle='round,pad=0.3', facecolor=C_LIGHT, alpha=0.9, edgecolor=C_BLUE))

# Add n below each point
for i, n in enumerate(ns_18):
    ax.text(i, means_18[i] - sds_18[i] - 0.4, f'n={n}', ha='center',
            fontsize=6, color=C_GREY)

labels_18 = [str(p) for p in periods_18]
ax.set_xticks(x18)
ax.set_xticklabels(labels_18, rotation=45, ha='right', fontsize=7)
ax.set_ylabel('Gjennomsnittleg tal paa materialar per stol')
ax.set_xlabel('25-aarsperiode')
ax.set_title('Materialkompleksitet over tid: talet paa materialar per stol')
ax.set_ylim(0, max(means_18) + max(sds_18) + 2)

fig.savefig(os.path.join(FIG_DIR, "fig18_material_complexity.pdf"))
plt.close()
print("  -> fig18_material_complexity.pdf")


# ==================================================================
# FIGUR 19: WEIGHT TREND (box plots per century)
# ==================================================================
print("Fig 19: Vekttrend per hundreaar...")

century_weights = defaultdict(list)
for r in rows:
    c = r["_century"]
    w = r["_weight"]
    if c and w and w > 0 and c not in ("1200-talet", "1300-talet", "1400-talet"):
        century_weights[c].append(w)

main_centuries_19 = sorted(
    [c for c in century_weights if len(century_weights[c]) >= 5],
    key=century_sort
)

fig, ax = plt.subplots(figsize=(8, 5))

data_19 = [century_weights[c] for c in main_centuries_19]
bp = ax.boxplot(data_19, patch_artist=True, widths=0.6,
                medianprops=dict(color=C_DARK, linewidth=2),
                whiskerprops=dict(color=C_GREY, linewidth=0.8),
                capprops=dict(color=C_GREY, linewidth=0.8),
                flierprops=dict(marker='o', markersize=3, markerfacecolor=C_GREY, alpha=0.4))

# Color boxes by epoch
epoch_colors = []
for c in main_centuries_19:
    yr = century_sort(c)
    if yr < 1700:
        epoch_colors.append(C_MAHOGNI)     # Early
    elif yr < 1800:
        epoch_colors.append(C_GOLD)        # 18th century
    elif yr < 1900:
        epoch_colors.append(C_PURPLE)      # 19th century
    else:
        epoch_colors.append(C_TEAL)        # Modern

for patch, color in zip(bp['boxes'], epoch_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.55)

# Annotate medians and n
for i, c in enumerate(main_centuries_19):
    med = statistics.median(century_weights[c])
    n = len(century_weights[c])
    ax.text(i + 1, med + 1.5, f'{med:.0f} kg', ha='center', fontsize=7,
            fontweight='bold', color=epoch_colors[i])
    ax.text(i + 1, -3.5, f'n={n}', ha='center', fontsize=7, color=C_GREY)

ax.set_xticklabels(main_centuries_19, rotation=45, ha='right')
ax.set_ylabel('Estimert vekt (kg)')
ax.set_title('Vektutvikling: fraa tung barokk til lett modernisme')

# Add a trend line through medians
medians_19 = [statistics.median(century_weights[c]) for c in main_centuries_19]
x19 = np.arange(1, len(main_centuries_19) + 1)
z = np.polyfit(x19, medians_19, 2)
poly = np.poly1d(z)
x_smooth = np.linspace(1, len(main_centuries_19), 50)
ax.plot(x_smooth, poly(x_smooth), '--', color=C_RED, linewidth=1.2, alpha=0.6,
        label='Trendlinje (2. grad)')
ax.legend(fontsize=8)

fig.savefig(os.path.join(FIG_DIR, "fig19_weight_trend.pdf"))
plt.close()
print("  -> fig19_weight_trend.pdf")


# ==================================================================
# FIGUR 20: STYLE HEIGHT GRADIENT (horizontal bars)
# ==================================================================
print("Fig 20: Hogdegradient per stilperiode...")

style_heights = defaultdict(list)
style_century_map = defaultdict(Counter)

for r in rows:
    s = r["_style"]
    h = r["_h"]
    c = r["_century"]
    if s and h:
        style_heights[s].append(h)
    if s and c:
        style_century_map[s][c] += 1

# Only styles with enough data
valid_styles = {s: style_heights[s] for s in style_heights if len(style_heights[s]) >= 5}

# Sort by mean height
sorted_styles = sorted(valid_styles.keys(), key=lambda s: statistics.mean(valid_styles[s]))

means_20 = [statistics.mean(valid_styles[s]) for s in sorted_styles]
sds_20 = [statistics.stdev(valid_styles[s]) if len(valid_styles[s]) > 1 else 0 for s in sorted_styles]
ns_20 = [len(valid_styles[s]) for s in sorted_styles]

# Determine dominant century for color
def dominant_century(style):
    if style_century_map[style]:
        return style_century_map[style].most_common(1)[0][0]
    return ""

century_color_map = {
    "1500-talet": '#2ecc71',
    "1600-talet": C_MAHOGNI,
    "1700-talet": C_GOLD,
    "1800-talet": C_PURPLE,
    "1900-talet": C_BLUE,
    "2000-talet": C_TEAL,
}

bar_colors = []
for s in sorted_styles:
    dc = dominant_century(s)
    bar_colors.append(century_color_map.get(dc, C_GREY))

fig, ax = plt.subplots(figsize=(8, 7))
y_pos = np.arange(len(sorted_styles))

bars = ax.barh(y_pos, means_20, xerr=sds_20, color=bar_colors, alpha=0.75,
               edgecolor='white', linewidth=0.5, height=0.7,
               error_kw=dict(ecolor=C_GREY, elinewidth=0.8, capsize=2))

# Annotate n and SD
for i, (s, m, sd, n) in enumerate(zip(sorted_styles, means_20, sds_20, ns_20)):
    ax.text(m + sd + 1.5, i, f'$\\bar{{x}}$={m:.0f} cm  (SD={sd:.1f}, n={n})',
            va='center', fontsize=6.5, color=C_DARK)

ax.set_yticks(y_pos)
ax.set_yticklabels(sorted_styles, fontsize=8)
ax.set_xlabel('Gjennomsnittleg hogde (cm)')
ax.set_title('Kronologisk hogdegradient: stilperiodar sorterte etter hogde')

# Add century legend
legend_handles = []
for cent, color in sorted(century_color_map.items()):
    legend_handles.append(mpatches.Patch(color=color, alpha=0.75, label=cent))
ax.legend(handles=legend_handles, loc='lower right', fontsize=7,
          title='Dominant hundreaar', title_fontsize=8)

# Add vertical line at overall mean
overall_mean = statistics.mean([h for hs in valid_styles.values() for h in hs])
ax.axvline(x=overall_mean, color=C_RED, linestyle=':', linewidth=1, alpha=0.6)
ax.text(overall_mean + 0.5, len(sorted_styles) - 0.5,
        f'Samla snitt: {overall_mean:.0f} cm', fontsize=7, color=C_RED)

fig.savefig(os.path.join(FIG_DIR, "fig20_style_height_gradient.pdf"))
plt.close()
print("  -> fig20_style_height_gradient.pdf")


# ==================================================================
# FIGUR 21: DESIGNER PROFILES IN H/W SPACE
# ==================================================================
print("Fig 21: Designarprofil i H/W-rommet...")

designer_keys = {
    "Chippendale": ["Chippendale", "Thomas Chippendale"],
    "Aalto": ["Alvar Aalto", "Aalto"],
    "Eames": ["Eames, Charles", "Eames, Ray", "Charles Eames"],
    "Breuer": ["Breuer, Marcel", "Marcel Breuer"],
    "Thonet": ["Thonet", "Thonet, Michael", "Michael Thonet"],
    "Jacobsen": ["Jacobsen, Arne", "Arne Jacobsen"],
    "Wegner": ["Wegner, Hans", "Hans Wegner"],
}

designer_colors = {
    "Chippendale": C_MAHOGNI,
    "Aalto": C_GREEN,
    "Eames": C_BLUE,
    "Breuer": C_RED,
    "Thonet": C_GOLD,
    "Jacobsen": C_TEAL,
    "Wegner": C_PURPLE,
}

designer_markers = {
    "Chippendale": 'o',
    "Aalto": 's',
    "Eames": 'D',
    "Breuer": '^',
    "Thonet": 'v',
    "Jacobsen": 'P',
    "Wegner": '*',
}

designer_data = defaultdict(lambda: {"h": [], "w": []})

for r in rows:
    p = r["_produsent"].lower()
    h, w = r["_h"], r["_w"]
    if not (h and w and h > 0 and w > 0):
        continue
    for dname, aliases in designer_keys.items():
        for alias in aliases:
            if alias.lower() in p:
                designer_data[dname]["h"].append(h)
                designer_data[dname]["w"].append(w)
                break

fig, ax = plt.subplots(figsize=(8, 6))

# Plot each designer
for dname in designer_keys:
    dd = designer_data[dname]
    if len(dd["h"]) < 2:
        continue
    mean_h = statistics.mean(dd["h"])
    mean_w = statistics.mean(dd["w"])
    sd_h = statistics.stdev(dd["h"]) if len(dd["h"]) > 1 else 0
    sd_w = statistics.stdev(dd["w"]) if len(dd["w"]) > 1 else 0

    color = designer_colors[dname]
    marker = designer_markers[dname]

    # Plot individual points faintly
    ax.scatter(dd["w"], dd["h"], color=color, marker=marker,
               alpha=0.25, s=30, zorder=3)

    # Plot mean as large marker
    ax.scatter([mean_w], [mean_h], color=color, marker=marker,
               s=120, edgecolors='white', linewidths=1.2, zorder=6,
               label=f'{dname} (n={len(dd["h"])})')

    # Draw SD ellipse
    if sd_h > 0 and sd_w > 0:
        ellipse = Ellipse((mean_w, mean_h), width=2 * sd_w, height=2 * sd_h,
                          facecolor=color, alpha=0.12, edgecolor=color,
                          linewidth=1.2, linestyle='--', zorder=2)
        ax.add_patch(ellipse)

    # Label
    ax.annotate(dname, (mean_w, mean_h),
                xytext=(8, 8), textcoords='offset points',
                fontsize=8, fontweight='bold', color=color,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          alpha=0.85, edgecolor=color, linewidth=0.5))

ax.set_xlabel('Breidde (cm)')
ax.set_ylabel('Hogde (cm)')
ax.set_title('Designarprofil i dimensjonsrommet (H $\\times$ W)')
ax.legend(loc='lower right', fontsize=7, framealpha=0.9)

# Add golden ratio line
phi = (1 + math.sqrt(5)) / 2
xlims = ax.get_xlim()
x_line = np.linspace(max(xlims[0], 20), min(xlims[1], 100), 50)
ax.plot(x_line, phi * x_line, ':', color=C_GOLD, linewidth=1, alpha=0.5,
        label=f'$\\varphi$ = {phi:.2f}')

fig.savefig(os.path.join(FIG_DIR, "fig21_designer_profiles.pdf"))
plt.close()
print("  -> fig21_designer_profiles.pdf")


# ==================================================================
# FIGUR 22: EXPLORATION VS EXPLOITATION (rolling entropy)
# ==================================================================
print("Fig 22: Utforsking vs. utnytting (rullande entropi)...")

# Collect year-material pairs
year_mats = []
for r in rows:
    if r["_year"] and r["_mats"] and r["_year"] >= 1600:
        for m in r["_mats"]:
            year_mats.append((r["_year"], m))

year_mats.sort(key=lambda x: x[0])

# Rolling 50-year window
window = 50
# Compute at each year from 1650 to 2000 (center of window)
roll_years = list(range(1650, 2001, 5))
roll_entropy = []

for center in roll_years:
    start = center - window // 2
    end = center + window // 2
    mats_in_window = [m for (y, m) in year_mats if start <= y < end]
    if len(mats_in_window) >= 10:
        roll_entropy.append(entropy_bits(mats_in_window))
    else:
        roll_entropy.append(None)

# Filter out None values
valid = [(y, e) for y, e in zip(roll_years, roll_entropy) if e is not None]
vy = [v[0] for v in valid]
ve = [v[1] for v in valid]

fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(vy, ve, '-', color=C_DARK, linewidth=2, zorder=5)
ax.fill_between(vy, ve, alpha=0.08, color=C_BLUE)

# Mark phases with colored bands
# Exploitation: mahogni-monopol (roughly 1750-1830)
ax.axvspan(1750, 1830, alpha=0.12, color=C_MAHOGNI, zorder=1)
ax.text(1790, max(ve) * 0.95, 'UTNYTTING\n(mahogni-monopol)',
        ha='center', fontsize=7, color=C_MAHOGNI, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.85,
                  edgecolor=C_MAHOGNI))

# Exploration: industrial explosion (roughly 1880-1960)
ax.axvspan(1880, 1960, alpha=0.12, color=C_TEAL, zorder=1)
ax.text(1920, max(ve) * 0.88, 'UTFORSKING\n(industriell eksplosjon)',
        ha='center', fontsize=7, color=C_TEAL, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.85,
                  edgecolor=C_TEAL))

# Find and annotate the dip (minimum in exploitation zone)
exploit_data = [(y, e) for y, e in zip(vy, ve) if 1730 <= y <= 1850]
if exploit_data:
    min_y, min_e = min(exploit_data, key=lambda x: x[1])
    ax.annotate(f'Minimumsverdi\nH\' = {min_e:.2f} bits\n({min_y})',
                xy=(min_y, min_e),
                xytext=(min_y - 60, min_e + 0.8),
                fontsize=7, color=C_MAHOGNI,
                arrowprops=dict(arrowstyle='->', color=C_MAHOGNI, lw=1),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          alpha=0.9, edgecolor=C_MAHOGNI))

# Find and annotate the peak (maximum in exploration zone)
explore_data = [(y, e) for y, e in zip(vy, ve) if 1880 <= y <= 1990]
if explore_data:
    max_y, max_e = max(explore_data, key=lambda x: x[1])
    ax.annotate(f'Maksimumsverdi\nH\' = {max_e:.2f} bits\n({max_y})',
                xy=(max_y, max_e),
                xytext=(max_y + 30, max_e - 0.8),
                fontsize=7, color=C_TEAL,
                arrowprops=dict(arrowstyle='->', color=C_TEAL, lw=1),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          alpha=0.9, edgecolor=C_TEAL))

ax.set_xlabel('Aar (senteraar for 50-aarsvindauge)')
ax.set_ylabel('Shannon-entropi H\' (bits)')
ax.set_title('Utforsking vs. utnytting: rullande materialentropi, 1650\u20132000')
ax.set_xlim(1640, 2010)

# Add legend for phases
legend_patches = [
    mpatches.Patch(color=C_MAHOGNI, alpha=0.3, label='Utnyttingsfase'),
    mpatches.Patch(color=C_TEAL, alpha=0.3, label='Utforskingsfase'),
]
ax.legend(handles=legend_patches, loc='upper left', fontsize=8)

fig.savefig(os.path.join(FIG_DIR, "fig22_exploration_exploitation.pdf"))
plt.close()
print("  -> fig22_exploration_exploitation.pdf")


# ---- Summary ----
print(f"\nAlle figurar lagra i {FIG_DIR}/")
for fname in sorted(os.listdir(FIG_DIR)):
    if fname.startswith("fig1") or fname.startswith("fig2"):
        if "17" in fname or "18" in fname or "19" in fname or "20" in fname or "21" in fname or "22" in fname:
            print(f"  {fname}")
