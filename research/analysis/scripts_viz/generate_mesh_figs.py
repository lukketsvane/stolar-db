import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from scipy.spatial import ConvexHull
import os
import warnings
from viz_style import setup_style, finalize_plot, ACCENT_RAUD, ACCENT_GRAA

warnings.filterwarnings('ignore')
setup_style()

os.makedirs('analysis/figures_new', exist_ok=True)

df_mesh = pd.read_csv('analysis/mesh_features.csv')
df_mesh['complexity'] = df_mesh['complexity'].fillna(df_mesh['complexity'].median())
df_mesh = df_mesh.dropna(subset=['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity', 'vol_hull'])

df_katalog = pd.read_csv('STOLAR/STOLAR.csv')
df = df_mesh.merge(df_katalog[['Objekt-ID', 'Stilperiode', 'Materialar', 'Frå år']], left_on='objekt_id', right_on='Objekt-ID', how='inner')

# --- A.6.3 Kanaliseringshierarki ---
features = ['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity', 'vol_hull', 'area']
cvs = df[features].std() / df[features].mean()
cvs = cvs.sort_values()

fig, ax = plt.subplots(figsize=(8, 4))
for i, (feat, cv) in enumerate(cvs.items()):
    ax.hlines(y=i, xmin=cvs.min()*0.5, xmax=cv, color='black', linewidth=1.0)
    ax.plot(cv, i, 'ks', markersize=6)
ax.set_yticks(range(len(cvs)))
ax.set_yticklabels(cvs.index)
ax.set_xscale('log')
finalize_plot(ax, xlabel='Variasjonskoeffisient (CV)')
plt.savefig('analysis/figures_new/mesh_3_3_channeling.png')
plt.close()

# --- A.6.4 Silhouette (PCA) ---
pca = PCA(n_components=2)
X = df[['sphericity', 'fill_ratio', 'inertia_ratio', 'complexity']]
X_norm = (X - X.mean()) / X.std()
X_pca = pca.fit_transform(X_norm)

top_styles = df['Stilperiode'].value_counts().head(6).index
# Monochrome palette: different markers and shades of gray
markers = ['s', '^', 'o', 'D', 'v', 'p']

fig, ax = plt.subplots(figsize=(8, 8))
ax.scatter(X_pca[:, 0], X_pca[:, 1], color='#eeeeee', s=10, marker='.', alpha=0.5, label='Alle andre', edgecolors='none')

for i, style in enumerate(top_styles):
    mask = df['Stilperiode'] == style
    ax.scatter(X_pca[mask, 0], X_pca[mask, 1], s=25, color='black', marker=markers[i], alpha=0.7, label=style, edgecolors='black', linewidths=0.5)

ax.legend(frameon=True, loc='upper right')
finalize_plot(ax, xlabel='Hovudkomponent 1', ylabel='Hovudkomponent 2')
plt.savefig('analysis/figures_new/mesh_3_4_silhouette.png')
plt.close()

# --- A.6.5 Hull Expansion ---
df['period_50'] = (df['Frå år'] // 50) * 50
periods = sorted(df[df['period_50'] >= 1500]['period_50'].unique())
vols = []
for p in periods:
    mask = (df['period_50'] >= 1500) & (df['period_50'] <= p)
    if mask.sum() > 4:
        pts = df.loc[mask, ['sphericity', 'fill_ratio', 'complexity']].values
        try:
            hull = ConvexHull(pts)
            vols.append(hull.volume)
        except:
            vols.append(vols[-1] if vols else 0)
    else:
        vols.append(0)

# Monotonic
for i in range(1, len(vols)):
    if vols[i] < vols[i-1]: vols[i] = vols[i-1]

fig, ax = plt.subplots(figsize=(8, 4))
ax.step(periods, vols, where='post', color='black', linewidth=1.5)
ax.fill_between(periods, vols, step='post', color='black', alpha=0.05)
ax.scatter(periods, vols, color='black', marker='s', s=15)
finalize_plot(ax, xlabel='År (kumulativt)', ylabel='Hylster-volum')
plt.savefig('analysis/figures_new/mesh_4_4_hull.png')
plt.close()

# --- A.6.12 Substrat-uavhengigheit ---
def clean_mat(m):
    if pd.isna(m): return 'Anna'
    m = str(m).lower()
    for kw in ['eik', 'bøk', 'mahogni', 'furu', 'bjørk', 'palisander', 'valnøtt']:
        if kw in m: return kw.capitalize()
    return 'Anna'

df['mat_clean'] = df['Materialar'].apply(clean_mat)
knn = NearestNeighbors(n_neighbors=6).fit(X_norm)
_, indices = knn.kneighbors(X_norm)

same_mat_fraction = []
for i in range(len(df)):
    own_mat = df.iloc[i]['mat_clean']
    if own_mat == 'Anna': continue
    neighbors_mat = df.iloc[indices[i][1:]]['mat_clean'].values
    same_mat_fraction.append(sum(neighbors_mat == own_mat) / 5)

fig, ax = plt.subplots(figsize=(10, 5))
bins = np.linspace(0, 1, 6)
counts, _ = np.histogram(same_mat_fraction, bins=bins)
ax.stairs(counts, bins, color='black', linewidth=1.2, fill=True, alpha=0.1)
base_prob = df[df['mat_clean'] != 'Anna']['mat_clean'].value_counts(normalize=True).apply(lambda x: x**2).sum()
ax.axvline(base_prob, color='black', linestyle='--', linewidth=1.0, label=f'Tilfeldig ({base_prob:.2f})')
ax.legend(frameon=False)
finalize_plot(ax, xlabel='Andel naboar med same materiale', ylabel='Tal på stolar')
plt.savefig('analysis/figures_new/mesh_5_22_substrate.png')
plt.close()

print("Regenererte Mesh-figurar")
