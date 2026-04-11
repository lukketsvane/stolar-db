import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from scipy.stats import gaussian_kde
from sklearn.neighbors import NearestNeighbors
from viz_style import setup_style, finalize_plot

warnings.filterwarnings('ignore')
setup_style()

df = pd.read_csv('STOLAR/STOLAR.csv')
df = df.dropna(subset=['Høgde (cm)', 'Breidde (cm)'])
df = df[(df['Høgde (cm)'] > 20) & (df['Høgde (cm)'] < 150)]
df = df[(df['Breidde (cm)'] > 20) & (df['Breidde (cm)'] < 100)]

x = df['Breidde (cm)'].values
y = df['Høgde (cm)'].values
X = np.column_stack([x, y])

# Calculate local density
kde = gaussian_kde(X.T)
density = kde(X.T)

# Calculate local morphological variance (dispersion)
nn = NearestNeighbors(n_neighbors=10).fit(X)
dist, _ = nn.kneighbors(X)
# Mean distance to 10 nearest neighbors as a proxy for local variance
variance = dist.mean(axis=1)

fig, ax = plt.subplots(figsize=(8, 8))

# Map variance to color/size
# High variance = Large, light markers (Frontier)
# Low variance = Small, dark markers (Attractors)
# We invert density for coloring to show the "Variance trap"
sc = ax.scatter(x, y, c=variance, s=5, cmap='Greys', alpha=0.6, marker='s', edgecolors='none')

# Add specific annotations for some chairs to make it "not generic"
# Sample a few "successful" (high density) and "divergent" (high variance)
attractor_chairs = df[density > np.percentile(density, 95)].sample(3, random_state=1)
divergent_chairs = df[variance > np.percentile(variance, 95)].sample(3, random_state=1)

for _, row in attractor_chairs.iterrows():
    ax.annotate('Attraktor', xy=(row['Breidde (cm)'], row['Høgde (cm)']), xytext=(5, 5), textcoords='offset points', fontsize=8, fontname='EB Garamond', color='black')

for _, row in divergent_chairs.iterrows():
    ax.annotate('Divergens', xy=(row['Breidde (cm)'], row['Høgde (cm)']), xytext=(5, 5), textcoords='offset points', fontsize=8, fontname='EB Garamond', color='gray')

finalize_plot(ax, xlabel='Breidde (cm)', ylabel='Høgde (cm)', xlim=(20, 100), ylim=(20, 150))
plt.savefig('analysis/figures_new/fig_density_variance.png')
plt.close()

print("Regenererte A.6.20 (Varians-kart)")
