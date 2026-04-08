import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
from scipy.interpolate import griddata
from sklearn.neighbors import NearestNeighbors
from viz_style import setup_style, finalize_plot

warnings.filterwarnings('ignore')
setup_style()

df = pd.read_csv('STOLAR/STOLAR.csv')
df = df.dropna(subset=['Breidde (cm)', 'Djupn (cm)', 'Frå år'])
df = df[(df['Breidde (cm)'] > 20) & (df['Breidde (cm)'] < 100)]
df = df[(df['Djupn (cm)'] > 20) & (df['Djupn (cm)'] < 100)]
df = df[(df['Frå år'] >= 1600) & (df['Frå år'] <= 1950)]

df['period'] = (df['Frå år'] // 50) * 50
periods = sorted(df['period'].unique())

vectors = []
for i in range(len(periods) - 1):
    p_curr, p_next = periods[i], periods[i+1]
    curr_data = df[df['period'] == p_curr]
    next_data = df[df['period'] == p_next]
    
    if len(next_data) < 5: continue
    nbrs = NearestNeighbors(n_neighbors=5).fit(next_data[['Breidde (cm)', 'Djupn (cm)']].values)
    
    for _, row in curr_data.iterrows():
        start_w, start_d = row['Breidde (cm)'], row['Djupn (cm)']
        dist, indices = nbrs.kneighbors([[start_w, start_d]])
        end_w = next_data.iloc[indices[0]]['Breidde (cm)'].mean()
        end_d = next_data.iloc[indices[0]]['Djupn (cm)'].mean()
        vectors.append({'w': start_w, 'd': start_d, 'u': end_w - start_w, 'v': end_d - start_d})

v_df = pd.DataFrame(vectors)
v_agg = v_df.groupby([v_df['w'].round(0), v_df['d'].round(0)]).mean()
# The index will be ('w', 'd'), and columns will be 'w', 'd', 'u', 'v'
# Let's just use the columns directly
grid_w, grid_d = np.mgrid[35:75:100j, 35:75:100j]
U = griddata(v_agg[['w', 'd']].values, v_agg['u'].values, (grid_w, grid_d), method='linear', fill_value=0)
V = griddata(v_agg[['w', 'd']].values, v_agg['v'].values, (grid_w, grid_d), method='linear', fill_value=0)

fig, ax = plt.subplots(figsize=(8, 8))
ax.streamplot(grid_w.T, grid_d.T, U.T, V.T, color='black', linewidth=0.8, density=1.5, arrowsize=1.0)
ax.scatter(df['Breidde (cm)'], df['Djupn (cm)'], color='black', alpha=0.05, s=2, marker='s')

finalize_plot(ax, xlabel='Breidde (cm)', ylabel='Djupn (cm)', xlim=(35, 75), ylim=(35, 75))
plt.savefig('analysis/figures_new/fig_path_dependence_flow.png')
plt.close()
print("Regenererte Vektorfelt")
