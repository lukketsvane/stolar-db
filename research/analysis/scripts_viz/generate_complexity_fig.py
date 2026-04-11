import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from viz_style import setup_style, finalize_plot

warnings.filterwarnings('ignore')
setup_style()

df_mesh = pd.read_csv('analysis/mesh_features.csv')
df_katalog = pd.read_csv('STOLAR/STOLAR.csv')
df = df_mesh.merge(df_katalog[['Objekt-ID', 'Frå år']], left_on='objekt_id', right_on='Objekt-ID', how='inner')
df = df.dropna(subset=['complexity', 'Frå år'])
df = df[(df['Frå år'] >= 1600) & (df['Frå år'] <= 1950)]
df['period_50'] = (df['Frå år'] // 50) * 50

periods = sorted(df['period_50'].unique())
stats = []
for p in periods:
    c = df[df['period_50'] == p]['complexity'].values
    if len(c) >= 5:
        stats.append((p, np.percentile(c, 10), np.percentile(c, 50), np.percentile(c, 90)))

p, p10, p50, p90 = zip(*stats)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(p, p90, color='black', linewidth=1.2, label='90. persentil', marker='.', markersize=4)
ax.plot(p, p50, color='black', linewidth=2.0, label='Median', marker='s', markersize=5)
ax.plot(p, p10, color='black', linewidth=1.2, label='10. persentil', marker='.', markersize=4)
ax.fill_between(p, p10, p90, color='black', alpha=0.05)

finalize_plot(ax, xlabel='År', ylabel='Kompleksitet (log10 v/a)')
ax.legend(frameon=False, loc='upper left')
plt.savefig('analysis/figures_new/fig_complexity_funnel.png')
plt.close()
print("Regenererte Kompleksitets-funnel")
