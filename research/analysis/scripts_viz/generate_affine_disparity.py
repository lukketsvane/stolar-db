import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from viz_style import setup_style, finalize_plot

warnings.filterwarnings('ignore')
setup_style()

df_mesh = pd.read_csv('analysis/mesh_features.csv')
df_mesh['complexity'] = df_mesh['complexity'].fillna(df_mesh['complexity'].median())
df_mesh = df_mesh.dropna(subset=['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity'])

df_katalog = pd.read_csv('STOLAR/STOLAR.csv')
df = df_mesh.merge(df_katalog[['Objekt-ID', 'Frå år']], left_on='objekt_id', right_on='Objekt-ID', how='inner')
df = df[(df['Frå år'] >= 1600) & (df['Frå år'] <= 1950)]
df['period_50'] = (df['Frå år'] // 50) * 50

periods = sorted(df['period_50'].unique())
v_list, p_list = [], []
for p in periods:
    data_p = df[df['period_50'] == p][['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity']]
    if len(data_p) > 10:
        v_list.append(np.linalg.det(np.cov(data_p.values, rowvar=False)))
        p_list.append(p)

fig, ax = plt.subplots(figsize=(8, 4))
ax.step(p_list, v_list, where='post', color='black', linewidth=1.5)
ax.fill_between(p_list, v_list, step='post', color='black', alpha=0.05)
ax.scatter(p_list, v_list, color='black', marker='s', s=20)
ax.set_yscale('log')
finalize_plot(ax, xlabel='År', ylabel='Generalisert varians (log)')
plt.savefig('analysis/figures_new/fig_affine_disparity.png')
plt.close()
print("Regenererte Affine Disparity")
