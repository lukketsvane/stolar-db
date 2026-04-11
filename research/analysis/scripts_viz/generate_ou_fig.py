import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from viz_style import setup_style, finalize_plot

warnings.filterwarnings('ignore')
setup_style()

df = pd.read_csv('STOLAR/STOLAR.csv')
df = df.dropna(subset=['Høgde (cm)', 'Frå år'])
df = df[(df['Høgde (cm)'] > 20) & (df['Høgde (cm)'] < 200)]

df['period_25'] = (df['Frå år'] // 25) * 25
medians_25 = df.groupby('period_25')['Høgde (cm)'].median()

x, y = [], []
for i in range(len(medians_25)-1):
    p_curr, p_next = medians_25.index[i], medians_25.index[i+1]
    curr_chairs = df[df['period_25'] == p_curr]['Høgde (cm)'].values
    m_curr, m_next = medians_25.loc[p_curr], medians_25.loc[p_next]
    for h in curr_chairs:
        x.append(h - m_curr)
        y.append(m_next - h)

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(x, y, color='black', alpha=0.1, s=10, marker='s', edgecolors='none')
m, b = np.polyfit(x, y, 1)
x_line = np.linspace(min(x), max(x), 100)
ax.plot(x_line, m*x_line + b, color='black', linewidth=1.5, label=f'Mean Reversion (m = {m:.2f})')
ax.axhline(0, color='black', linestyle=':', linewidth=0.8)
ax.axvline(0, color='black', linestyle=':', linewidth=0.8)

finalize_plot(ax, xlabel='Avvik frå periode-median (cm)', ylabel='Retur mot neste median (cm)')
ax.legend(frameon=True)
plt.savefig('analysis/figures_new/fig_3_1_ou_reversion.png')
plt.close()
print("Regenererte OU-plott")
