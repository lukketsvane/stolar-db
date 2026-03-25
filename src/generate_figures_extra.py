"""
Ekstra figurar for Art II-IV basert paa djup research.
"""
import csv, math, os
from collections import Counter, defaultdict
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Palatino','Book Antiqua','Georgia','Times New Roman'],
    'font.size': 9, 'axes.titlesize': 11, 'axes.titleweight': 'bold',
    'axes.labelsize': 10, 'axes.linewidth': 0.6,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.dpi': 300, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.2,
})

C_BLUE='#2c3e6b'; C_RED='#b03a2e'; C_GREEN='#1e6b3a'; C_GOLD='#c49b2a'
C_PURPLE='#5b2c6f'; C_TEAL='#117a65'; C_GREY='#7f8c8d'; C_MAHOGNI='#6b2c1a'
C_DARK='#1a1a2e'

CSV_PATH = "../stolar_db.csv"
FIG_DIR = "../texts/fig"

rows = []
with open(CSV_PATH, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f): rows.append(row)

def sf(v):
    try:
        x = float(v.replace(",","."))
        return x if x > 0 else None
    except: return None

for r in rows:
    r["_mats"] = [m.strip() for m in r.get("Materialar","").split(",") if m.strip()]
    r["_h"] = sf(r.get("Høgde (cm)",""))
    r["_w"] = sf(r.get("Breidde (cm)",""))
    r["_nat"] = r.get("Nasjonalitet","").strip()

# ==================================================================
# FIGUR 11: H/W-RATIO PER MATERIALE (boxplot)
# ==================================================================
print("Fig 11: H/W per materiale...")

mat_hw = defaultdict(list)
for r in rows:
    if r["_h"] and r["_w"] and r["_w"] > 0:
        for m in r["_mats"]:
            mat_hw[m].append(r["_h"]/r["_w"])

mats_plot = ["Bjørk","Furu","Eik","Bøk","Mahogni","Kryssfiner","Stål","Plast"]
mats_data = [mat_hw[m] for m in mats_plot if len(mat_hw[m]) > 10]
mats_labels = [m for m in mats_plot if len(mat_hw[m]) > 10]

fig, ax = plt.subplots(figsize=(8, 5))
bp = ax.boxplot(mats_data, patch_artist=True, widths=0.6,
                medianprops=dict(color=C_DARK, linewidth=2))

colors = [C_GREEN]*4 + [C_MAHOGNI] + [C_GREY, C_RED, C_RED]
for patch, color in zip(bp['boxes'], colors[:len(mats_data)]):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)

phi = (1+math.sqrt(5))/2
ax.axhline(y=phi, color=C_GOLD, linestyle='-.', linewidth=1.5, label=f'Gullsnitt ($\\varphi$={phi:.2f})')
ax.axhline(y=1.0, color=C_GREY, linestyle=':', linewidth=0.7, alpha=0.5)

ax.set_xticklabels(mats_labels, rotation=45, ha='right')
ax.set_ylabel('$H/W$-ratio')
ax.set_title('Kvart materiale dikterer sine proporsjonar')
ax.legend(fontsize=8)
ax.set_ylim(0, 4)

# Annotate means
for i, (m, data) in enumerate(zip(mats_labels, mats_data)):
    mean_val = statistics.mean(data)
    ax.text(i+1, max(data)*0.95 if max(data) < 3.5 else 3.5, f'$\\bar{{x}}$={mean_val:.2f}',
            ha='center', fontsize=7, color=colors[i], fontweight='bold')

fig.savefig(f"{FIG_DIR}/fig11_hw_per_material.pdf")
plt.close()


# ==================================================================
# FIGUR 12: CHI2 RESIDUALAR HEATMAP
# ==================================================================
print("Fig 12: Chi2 residualar...")
from scipy import stats as sp_stats

top_nats = ["Storbritannia","Noreg","Frankrike","Italia","Danmark","Tyskland"]
top_mats_c = ["Mahogni","Eik","Bøk","Furu","Stål","Kryssfiner","Nøttetre","Bjørk"]

ct = []
for nat in top_nats:
    row_data = []
    nat_rows = [r for r in rows if r["_nat"]==nat]
    for mat in top_mats_c:
        row_data.append(sum(1 for r in nat_rows if mat in r["_mats"]))
    ct.append(row_data)
ct = np.array(ct)
chi2, p, dof, expected = sp_stats.chi2_contingency(ct)
residuals = (ct - expected) / np.sqrt(expected)

fig, ax = plt.subplots(figsize=(9, 5))
im = ax.imshow(residuals, cmap='RdBu_r', aspect='auto', vmin=-8, vmax=8)

for i in range(len(top_nats)):
    for j in range(len(top_mats_c)):
        val = residuals[i][j]
        color = 'white' if abs(val) > 4 else C_DARK
        stars = '***' if abs(val)>3 else '**' if abs(val)>2 else '*' if abs(val)>1.5 else ''
        ax.text(j, i, f'{val:+.1f}{stars}', ha='center', va='center',
                fontsize=8, color=color, fontweight='bold' if stars else 'normal')

ax.set_xticks(range(len(top_mats_c)))
ax.set_xticklabels(top_mats_c, rotation=45, ha='right')
ax.set_yticks(range(len(top_nats)))
ax.set_yticklabels(top_nats)
ax.set_title(f'Nasjonale materialfingeravtrykk ($\\chi^2$ = {chi2:.0f}, p < 10$^{{-100}}$)')
cb = plt.colorbar(im, ax=ax, shrink=0.8)
cb.set_label('Standardisert residual')

fig.savefig(f"{FIG_DIR}/fig12_chi2_residualar.pdf")
plt.close()


# ==================================================================
# FIGUR 13: TEKNIKK-EVOLUSJON (heatmap)
# ==================================================================
print("Fig 13: Teknikk-evolusjon...")

def cs(c):
    try: return int(c.split("-")[0])
    except: return 9999

century_techs = defaultdict(Counter)
for r in rows:
    c = r.get("Hundreår","").strip()
    if c:
        ts = [t.strip() for t in r.get("Teknikk","").split(",") if t.strip()]
        century_techs[c].update(ts)

main_c = ["1500-talet","1600-talet","1700-talet","1800-talet","1900-talet","2000-talet"]
main_t = ["Skjæring","Dreiing","Polstring","Tapping","Plugging",
          "Fletting","Innfelling","Formbøying","Laminering","Skruing","Sveising"]

tech_pcts = []
for t in main_t:
    row_data = []
    for c in main_c:
        total = sum(century_techs[c].values()) or 1
        row_data.append(100*century_techs[c].get(t, 0)/total)
    tech_pcts.append(row_data)

tech_arr = np.array(tech_pcts)

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(tech_arr, cmap='YlOrRd', aspect='auto', vmin=0, vmax=45)

for i in range(len(main_t)):
    for j in range(len(main_c)):
        val = tech_arr[i][j]
        if val > 0:
            color = 'white' if val > 25 else C_DARK
            ax.text(j, i, f'{val:.0f}%', ha='center', va='center',
                    fontsize=8, color=color)

ax.set_xticks(range(len(main_c)))
ax.set_xticklabels(main_c, rotation=45, ha='right')
ax.set_yticks(range(len(main_t)))
ax.set_yticklabels(main_t)
ax.set_title('Teknikk-evolusjon: fraa skjering til sproyting')

# Draw boxes around disappearing and appearing
# Skjering/Dreiing disappear
ax.add_patch(plt.Rectangle((-0.5, -0.5), 3.5, 2, fill=False, edgecolor=C_RED, linewidth=2, linestyle='--'))
ax.text(1, -0.8, 'FORSVINN', fontsize=8, color=C_RED, ha='center', fontweight='bold')

# Formbøying/Laminering/Sveising appear
ax.add_patch(plt.Rectangle((3.5, 7.5), 2.5, 3, fill=False, edgecolor=C_GREEN, linewidth=2, linestyle='--'))
ax.text(5, 10.8, 'OPPSTAAR', fontsize=8, color=C_GREEN, ha='center', fontweight='bold')

cb = plt.colorbar(im, ax=ax, shrink=0.8)
cb.set_label('Prosentdel av teknikk-foerekomstar')

fig.savefig(f"{FIG_DIR}/fig13_teknikk_evolusjon.pdf")
plt.close()


# ==================================================================
# FIGUR 14: DIMENSJONELL DRIFT
# ==================================================================
print("Fig 14: Dimensjonell drift...")

century_h = defaultdict(list)
century_w = defaultdict(list)
century_d = defaultdict(list)
for r in rows:
    c = r.get("Hundreår","").strip()
    if c and c not in ("1200-talet","1300-talet","1400-talet"):
        if r["_h"]: century_h[c].append(r["_h"])
        if r["_w"]: century_w[c].append(r["_w"])

main_c2 = ["1500-talet","1600-talet","1700-talet","1800-talet","1900-talet","2000-talet"]

fig, ax = plt.subplots(figsize=(7, 4.5))

h_means = [statistics.mean(century_h[c]) for c in main_c2 if century_h[c]]
w_means = [statistics.mean(century_w[c]) for c in main_c2 if century_w[c]]
plot_cs = [c for c in main_c2 if century_h[c]]

ax.plot(range(len(plot_cs)), h_means, 'o-', color=C_BLUE, linewidth=2.5, markersize=7, label='Hogde')
ax.plot(range(len(plot_cs)), w_means, 's-', color=C_RED, linewidth=2.5, markersize=7, label='Breidde')

# Annotate the drift
for i in range(1, len(h_means)):
    dh = h_means[i] - h_means[i-1]
    if abs(dh) > 3:
        ax.annotate(f'{dh:+.1f}', ((i+i-1)/2, (h_means[i]+h_means[i-1])/2),
                    fontsize=7, color=C_BLUE, ha='center',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

ax.set_xticks(range(len(plot_cs)))
ax.set_xticklabels(plot_cs, rotation=45, ha='right')
ax.set_ylabel('Centimeter')
ax.set_title('Dimensjonsdrift: hogde fell, breidde oscillerer')
ax.legend(fontsize=9)
ax.set_ylim(40, 110)

# Mark industrialization
ax.axvspan(3.5, 4.5, alpha=0.1, color=C_RED, label='Industrialisering')

fig.savefig(f"{FIG_DIR}/fig14_dimensjonsdrift.pdf")
plt.close()


print(f"\nAlle ekstra figurar lagra i {FIG_DIR}/")
for f in sorted(os.listdir(FIG_DIR)):
    if f.startswith("fig1") and len(f) > 15:  # Only new ones
        print(f"  {f}")
