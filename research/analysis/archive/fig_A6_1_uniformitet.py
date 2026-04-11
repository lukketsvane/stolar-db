#!/usr/bin/env python3
"""A.6.1 Formrommet er ikkje uniformt busett (1.4)"""
from utils import apply_style, load_stolar, INK, CORE_AREA, MAT_COLORS, FIG_OUT
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde
from scipy.spatial import cKDTree
from sklearn.preprocessing import StandardScaler
from matplotlib import gridspec

def main():
    apply_style()
    _, cat = load_stolar()
    geo = cat[(cat.Br > 0) & (cat.Ho > 0) & (cat.Dj > 0)].dropna(subset=['Ho','Br','Dj'])
    Xn = StandardScaler().fit_transform(geo[['Ho','Br','Dj']].values)
    tree = cKDTree(Xn); d, _ = tree.query(Xn, k=2)
    nn = d[:, 1]; nn = nn[nn > 0]; cv = nn.std() / nn.mean()
    
    for c in ['Ho','Br','Dj']:
        lo, hi = geo[c].quantile([0.005, 0.995])
        geo = geo[(geo[c] >= lo) & (geo[c] <= hi)]
    cx, cy = geo.Br.median(), geo.Ho.median()

    fig = plt.figure(figsize=(12, 5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1.2, 1], wspace=0.25)
    ax1 = fig.add_subplot(gs[0]); ax2 = fig.add_subplot(gs[1])

    rect = plt.Rectangle((geo.Br.quantile(0.1), geo.Ho.quantile(0.1)), 
                         geo.Br.quantile(0.9)-geo.Br.quantile(0.1), 
                         geo.Ho.quantile(0.9)-geo.Ho.quantile(0.1),
                         facecolor=CORE_AREA, alpha=0.4, zorder=0)
    ax1.add_patch(rect)

    for m, color in MAT_COLORS.items():
        sub = geo[geo.matgr == m]
        ax1.scatter(sub.Br, sub.Ho, s=6, c=color, alpha=0.5, edgecolor='none', label=m, zorder=2)
    
    x, y = geo.Br.values, geo.Ho.values
    kde = gaussian_kde(np.vstack([x, y]))
    xi, yi = np.linspace(x.min(), x.max(), 100), np.linspace(y.min(), y.max(), 100)
    Xi, Yi = np.meshgrid(xi, yi); Zi = kde(np.vstack([Xi.ravel(), Yi.ravel()])).reshape(Xi.shape)
    ax1.contour(Xi, Yi, Zi, levels=8, cmap='YlOrBr', linewidths=0.5, alpha=0.7, zorder=3)
    ax1.scatter([cx], [cy], marker='+', s=200, color=INK, linewidths=1.5, zorder=10)
    ax1.set_xlabel('breidde (cm)'); ax1.set_ylabel('høgde (cm)')
    ax1.set_title('i. formrommet (h, b) — tettleik og materiale', loc='left')
    ax1.legend(loc='upper right', markerscale=1.5)

    ax2.hist(nn[nn < np.percentile(nn, 99)], bins=40, color='#5C6B7F', edgecolor=INK, linewidth=0.5, alpha=0.7)
    ax2.axvline(nn.mean(), color='#C8553D', linewidth=1.5)
    ax2.set_xlabel('standardisert nn-avstand')
    ax2.set_title(f'ii. nn-distanse (cv = {cv:.2f})', loc='left')
    ax2.text(0.95, 0.85, f'ratio = {cv/0.36:.1f}×', transform=ax2.transAxes, ha='right',
             bbox=dict(boxstyle='square,pad=0.5', facecolor='white', edgecolor=INK, linewidth=0.5))
    
    fig.savefig(FIG_OUT / 'fig-A6-1-morphospace.png', bbox_inches='tight')
    plt.close()
    print(f'wrote fig-A6-1-morphospace.png')

if __name__ == '__main__':
    main()
