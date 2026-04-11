import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from viz_style import setup_style, finalize_plot

warnings.filterwarnings('ignore')
setup_style()

df = pd.read_csv('STOLAR/STOLAR.csv')
df = df.dropna(subset=['Høgde (cm)', 'Frå år', 'Stilperiode'])
df = df[(df['Høgde (cm)'] > 30) & (df['Høgde (cm)'] < 150)]

valid_styles = df['Stilperiode'].value_counts()
valid_styles = valid_styles[valid_styles > 30].index

dev_current, dev_next = [], []
for style in valid_styles:
    style_data = df[df['Stilperiode'] == style].sort_values('Frå år')
    mean_h = style_data['Høgde (cm)'].mean()
    deviations = style_data['Høgde (cm)'].values - mean_h
    for i in range(len(deviations) - 1):
        dev_current.append(deviations[i])
        dev_next.append(deviations[i+1])

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(dev_current, dev_next, color='black', alpha=0.1, s=10, marker='s', edgecolors='none')

m, b = np.polyfit(dev_current, dev_next, 1)
x_line = np.linspace(min(dev_current), max(dev_current), 100)
ax.plot(x_line, m*x_line + b, color='black', linewidth=1.5, label=f'Autokorrelasjon (r = {m:.2f})')

ax.axhline(0, color='black', linestyle=':', linewidth=0.8)
ax.axvline(0, color='black', linestyle=':', linewidth=0.8)

finalize_plot(ax, xlabel='Avvik ved tid T (cm)', ylabel='Avvik ved tid T+1 (cm)')
ax.legend(frameon=True)
plt.savefig('analysis/figures_new/fig_levin_feedback.png')
plt.close()
print("Regenererte Levin-Feedback")
