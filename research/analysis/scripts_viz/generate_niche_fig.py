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

df = pd.read_csv('STOLAR/STOLAR.csv')
df = df.dropna(subset=['Høgde (cm)', 'Breidde (cm)', 'Nemning'])

def clean_nemning(n):
    n = str(n).lower()
    if 'lenestol' in n: return 'Lenestol'
    if 'krakk' in n or 'taburett' in n: return 'Krakk'
    if 'stol' in n: return 'Stol'
    return 'Anna'

df['Klasse'] = df['Nemning'].apply(clean_nemning)
classes = ['Krakk', 'Stol', 'Lenestol']
# Technical shades
styles = [
    {'color': 'black', 'ls': '-', 'fill': True, 'alpha': 0.1},
    {'color': 'black', 'ls': '--', 'fill': False, 'alpha': 1.0},
    {'color': 'black', 'ls': ':', 'fill': True, 'alpha': 0.05}
]

fig, ax = plt.subplots(figsize=(8, 6))

for i, cls in enumerate(classes):
    subset = df[df['Klasse'] == cls]
    if len(subset) < 10: continue
    pts = subset[['Breidde (cm)', 'Høgde (cm)']].values
    
    try:
        hull = ConvexHull(pts)
        s = styles[i]
        poly = Polygon(pts[hull.vertices], closed=True, fill=s['fill'], facecolor=s['color'], alpha=s['alpha'], edgecolor='black', linewidth=1.0, linestyle=s['ls'], label=cls)
        ax.add_patch(poly)
    except:
        pass

finalize_plot(ax, xlabel='Breidde (cm)', ylabel='Høgde (cm)', xlim=(20, 120), ylim=(20, 150))
ax.legend(frameon=True)
plt.savefig('analysis/figures_new/fig_niche_overlap.png')
plt.close()
print("Regenererte Niche-plott")
