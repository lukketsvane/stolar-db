import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from scipy.spatial import ConvexHull
from matplotlib.patches import Polygon
from viz_style import setup_style, finalize_plot

warnings.filterwarnings('ignore')
setup_style()

df_hist = pd.read_csv('analysis/mesh_features.csv').dropna(subset=['sphericity', 'fill_ratio'])
df_mut = pd.read_csv('analysis/mutant_features.csv').dropna(subset=['sphericity', 'fill_ratio'])

p_h = df_hist[['sphericity', 'fill_ratio']].values
p_m = df_mut[['sphericity', 'fill_ratio']].values
h_h = ConvexHull(p_h)
h_m = ConvexHull(p_m)

# Space Plot
fig, ax = plt.subplots(figsize=(8, 6))
ax.add_patch(Polygon(p_h[h_h.vertices], closed=True, fill=True, facecolor='black', alpha=0.05, edgecolor='black', linestyle=':', label='Historisk (C-rom)'))
ax.add_patch(Polygon(p_m[h_m.vertices], closed=True, fill=False, edgecolor='black', linewidth=1.5, label='Teoretisk (K-rom)'))

ax.scatter(p_h[:,0], p_h[:,1], s=10, c='black', alpha=0.2, marker='s', edgecolors='none')
ax.scatter(p_m[:,0], p_m[:,1], s=25, c='black', alpha=0.8, marker='^', edgecolors='black', linewidths=0.5)

finalize_plot(ax, xlabel='Sphericity', ylabel='Fill Ratio')
ax.legend(frameon=True)
plt.savefig('analysis/figures_new/fig_shape_grammar_space.png')
plt.close()

# KDE Plot
import seaborn as sns
fig, ax = plt.subplots(figsize=(8, 6))
sns.kdeplot(x=df_mut['sphericity'], y=df_mut['fill_ratio'], cmap='Greys', fill=True, alpha=0.2, ax=ax)
sns.kdeplot(x=df_hist['sphericity'], y=df_hist['fill_ratio'], cmap='Greys', fill=False, linewidths=1.0, ax=ax)
finalize_plot(ax, xlabel='Sphericity', ylabel='Fill Ratio')
plt.savefig('analysis/figures_new/fig_shape_grammar_kde.png')
plt.close()

print("Regenererte Shape Grammar")
