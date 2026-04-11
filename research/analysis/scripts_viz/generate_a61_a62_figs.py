import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import mutual_info_score
from sklearn.preprocessing import LabelEncoder
from viz_style import setup_style, finalize_plot, ACCENT_RAUD, ACCENT_GRAA

warnings.filterwarnings('ignore')
setup_style()

os.makedirs('analysis/figures_new', exist_ok=True)

df = pd.read_csv('STOLAR/STOLAR.csv')
df = df.dropna(subset=['Høgde (cm)', 'Breidde (cm)', 'Djupn (cm)'])
df = df[(df['Høgde (cm)'] > 20) & (df['Høgde (cm)'] < 200)]
df = df[(df['Breidde (cm)'] > 20) & (df['Breidde (cm)'] < 150)]
df = df[(df['Djupn (cm)'] > 20) & (df['Djupn (cm)'] < 150)]

# --- 1. Prop 1.4: Formrommet er ikkje uniformt busett (A.6.1) ---
X = df[['Høgde (cm)', 'Breidde (cm)', 'Djupn (cm)']].values
X_z = (X - X.mean(axis=0)) / X.std(axis=0)

nn = NearestNeighbors(n_neighbors=2)
nn.fit(X_z)
distances, _ = nn.kneighbors(X_z)
nn_dist_obs = distances[:, 1]

n_samples = len(X_z)
X_null = np.random.uniform(low=X_z.min(axis=0), high=X_z.max(axis=0), size=(n_samples, 3))
nn_null = NearestNeighbors(n_neighbors=2)
nn_null.fit(X_null)
distances_null, _ = nn_null.kneighbors(X_null)
nn_dist_null = distances_null[:, 1]

fig, ax = plt.subplots(figsize=(8, 5))
sns.kdeplot(nn_dist_obs, color='black', fill=True, alpha=0.2, linewidth=1.5, label='Observert', ax=ax)
sns.kdeplot(nn_dist_null, color='black', fill=False, alpha=1.0, linewidth=1.0, linestyle='--', label='Poisson Null', ax=ax)

ax.legend(frameon=False)
finalize_plot(ax, xlabel='Z-skalert Nærmaste Nabo-distanse', ylabel='Tettleik')
plt.savefig('analysis/figures_new/fig_1_4_uniformitet.png')
plt.close()

# --- 2. Prop 2.4: Stilperiode som samlevariabel (A.6.2) ---
df_mi = df.dropna(subset=['Stilperiode', 'Materialar'])
le = LabelEncoder()
style_enc = le.fit_transform(df_mi['Stilperiode'].astype(str))
mat_enc = le.fit_transform(df_mi['Materialar'].astype(str))

dims = ['Høgde', 'Breidde', 'Djupn']
df_mi['H/W'] = df_mi['Høgde (cm)'] / df_mi['Breidde (cm)']
dims_cols = ['Høgde (cm)', 'Breidde (cm)', 'Djupn (cm)', 'H/W']

mi_style = []
mi_mat = []

for d in dims_cols:
    dim_enc = pd.qcut(df_mi[d], q=10, labels=False, duplicates='drop')
    mi_style.append(mutual_info_score(dim_enc, style_enc))
    mi_mat.append(mutual_info_score(dim_enc, mat_enc))

fig, ax = plt.subplots(figsize=(8, 4))
y_pos = np.arange(len(dims_cols))

for i in range(len(dims_cols)):
    ax.hlines(y=i, xmin=0, xmax=max(mi_style[i], mi_mat[i]) * 1.1, color='#e0e0e0', linewidth=0.8, zorder=1)
    ax.plot([mi_mat[i], mi_style[i]], [i, i], color='black', linewidth=1.5, zorder=2)
    ax.plot(mi_mat[i], i, 'o', color='white', markeredgecolor='black', markersize=7, zorder=3, label='Materiale' if i==0 else "")
    ax.plot(mi_style[i], i, 's', color='black', markersize=7, zorder=3, label='Stilperiode' if i==0 else "")

ax.set_yticks(y_pos)
ax.set_yticklabels(['Høgde', 'Breidde', 'Djupn', 'H/W-ratio'])
ax.legend(frameon=True, loc='lower right')
finalize_plot(ax, xlabel='Gjensidig informasjon (bits)')
plt.savefig('analysis/figures_new/fig_2_4_mi_style_mat.png')
plt.close()

print("Regenererte A.6.1 og A.6.2")
