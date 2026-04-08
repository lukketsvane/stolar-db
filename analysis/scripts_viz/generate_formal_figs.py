import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import os
import warnings
from viz_style import setup_style, finalize_plot

warnings.filterwarnings('ignore')
setup_style()
os.makedirs('analysis/figures_formal', exist_ok=True)

df = pd.read_csv('STOLAR/STOLAR.csv')
df = df.dropna(subset=['Høgde (cm)', 'Breidde (cm)'])
df = df[(df['Høgde (cm)'] > 20) & (df['Høgde (cm)'] < 200)]
df = df[(df['Breidde (cm)'] > 20) & (df['Breidde (cm)'] < 150)]

def draw_d1_morphospace():
    fig, ax = plt.subplots(figsize=(6, 6))
    # All database entries
    ax.scatter(df['Breidde (cm)'], df['Høgde (cm)'], color='black', s=1, alpha=0.1, marker='.')
    # Highlight some density contours
    sns.kdeplot(x=df['Breidde (cm)'], y=df['Høgde (cm)'], color='black', alpha=0.3, linewidths=0.5, levels=5, ax=ax)
    
    finalize_plot(ax, xlabel='Breidde (cm)', ylabel='Høgde (cm)', xlim=(20, 120), ylim=(20, 160))
    plt.savefig('analysis/figures_formal/d1_morphospace.png')
    plt.close()

def draw_d2_pressure():
    # Hypothesis: Selection pressure for "Standard Table Height" (ca 45cm seat height / 85cm total)
    fig, ax = plt.subplots(figsize=(6, 6))
    x = np.linspace(20, 120, 100)
    y = np.linspace(20, 160, 100)
    X, Y = np.meshgrid(x, y)
    # Selection pressure target (85cm height)
    Z = np.exp(-(Y - 85)**2 / 200) 
    
    # Vector field pointing toward the 85cm line
    ax.contour(X, Y, Z, levels=5, colors='black', alpha=0.1)
    for target_y in [85]:
        ax.axhline(target_y, color='black', linestyle='--', linewidth=1.0, alpha=0.5)
        ax.text(105, target_y + 2, 'Seleksjonsmål', fontname='EB Garamond', fontsize=10)
    
    # Quiver
    xq, yq = np.mgrid[30:110:10j, 30:150:10j]
    uq = np.zeros_like(xq)
    vq = (85 - yq) / 10
    ax.quiver(xq, yq, uq, vq, color='black', alpha=0.4, width=0.005)
    
    finalize_plot(ax, xlabel='Breidde (cm)', ylabel='Høgde (cm)', xlim=(20, 120), ylim=(20, 160))
    plt.savefig('analysis/figures_formal/d2_pressure.png')
    plt.close()

def draw_d3_landscape():
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#ffffff')
    
    x = df['Breidde (cm)'].values
    y = df['Høgde (cm)'].values
    X, Y = np.mgrid[20:120:50j, 40:160:50j]
    positions = np.vstack([X.ravel(), Y.ravel()])
    values = np.vstack([x, y])
    kernel = gaussian_kde(values)
    Z = np.reshape(kernel(positions).T, X.shape)
    Z = Z / Z.max()
    
    ax.plot_wireframe(X, Y, Z, color='black', linewidth=0.3, alpha=0.3)
    ax.set_zlabel('Fitness', fontname='EB Garamond', size=12)
    ax.view_init(elev=30, azim=-45)
    ax.set_axis_off()
    plt.savefig('analysis/figures_formal/d3_landscape.png')
    plt.close()

def draw_d4_grammar():
    fig, ax = plt.subplots(figsize=(6, 2))
    # Abstract grammar logic
    ax.text(0.1, 0.5, 's', fontname='EB Garamond', size=14)
    ax.text(0.2, 0.5, '→', fontname='EB Garamond', size=14)
    ax.text(0.3, 0.5, '(s - τ(a)) + τ(b)', fontname='EB Garamond', size=14)
    
    # Schematic box replace
    ax.add_patch(plt.Rectangle((0.6, 0.3), 0.1, 0.4, fill=True, facecolor='black', alpha=0.1))
    ax.text(0.72, 0.5, '⇒', size=12)
    ax.add_patch(plt.Rectangle((0.8, 0.3), 0.1, 0.4, fill=True, facecolor='black', alpha=0.3))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    plt.savefig('analysis/figures_formal/d4_grammar.png')
    plt.close()

def draw_d6_agent():
    # Lyapunov-basert agens-navigasjon
    fig, ax = plt.subplots(figsize=(6, 6))
    x = np.linspace(-1, 1, 100)
    y = np.linspace(-1, 1, 100)
    X, Y = np.meshgrid(x, y)
    Z = X**2 + Y**2 # Lyapunov funnel V
    
    ax.contour(X, Y, Z, levels=8, colors='black', alpha=0.1, linestyles=':')
    
    # Trajectory of chair form
    t = np.linspace(0, 1, 15)
    xt = 0.8 * np.exp(-3*t) * np.cos(10*t)
    yt = 0.8 * np.exp(-3*t) * np.sin(10*t)
    ax.plot(xt, yt, 'k-', linewidth=1.5, alpha=0.8)
    ax.scatter(xt, yt, color='black', s=10, marker='s', alpha=np.linspace(0.1, 1, 15))
    ax.scatter([0], [0], color='black', marker='*', s=100, label='Mål (g)')
    
    finalize_plot(ax, xlabel='π₁', ylabel='π₂')
    ax.legend(frameon=False, prop={'family': 'EB Garamond'})
    plt.savefig('analysis/figures_formal/d6_agent.png')
    plt.close()

def draw_d7_lightcone():
    fig, ax = plt.subplots(figsize=(6, 6))
    t = np.linspace(0, 1, 100)
    # Expanding boundaries
    ax.plot(0.5 - 0.4*t, t, 'k-', linewidth=1.0)
    ax.plot(0.5 + 0.4*t, t, 'k-', linewidth=1.0)
    ax.fill_betweenx(t, 0.5 - 0.4*t, 0.5 + 0.4*t, color='black', alpha=0.05)
    
    # Possible shapes within
    for ti in [0.2, 0.5, 0.8]:
        width = ti * 0.4
        for xi in np.linspace(0.5 - width, 0.5 + width, 3):
            rect = plt.Rectangle((xi-0.02, ti-0.03), 0.04, 0.06, fill=True, facecolor='black', alpha=0.2)
            ax.add_patch(rect)

    finalize_plot(ax, xlabel='Morfologi (Shape)', ylabel='Tid (T)')
    plt.savefig('analysis/figures_formal/d7_lightcone.png')
    plt.close()

import seaborn as sns
if __name__ == '__main__':
    draw_d1_morphospace()
    draw_d2_pressure()
    draw_d3_landscape()
    draw_d4_grammar()
    draw_d6_agent()
    draw_d7_lightcone()
    print("Genererte Formelle Figurar (All Data)")
