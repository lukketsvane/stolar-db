#!/usr/bin/env python3
"""A.6.2 Stilperiode som samlevariabel (2.4, 2.62)"""
from utils import apply_style, load_stolar, INK, FIG_OUT
import matplotlib.pyplot as plt
import numpy as np
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import LabelEncoder

def main():
    apply_style()
    _, cat = load_stolar()
    geo = cat[(cat.Br > 0) & (cat.Ho > 0) & (cat.Dj > 0)].dropna(subset=['Ho','Br','Dj','Stil','matgr'])
    geo['HW'] = geo.Ho / geo.Br
    le_s = LabelEncoder(); geo['s_e'] = le_s.fit_transform(geo.Stil)
    le_m = LabelEncoder(); geo['m_e'] = le_m.fit_transform(geo.matgr)
    
    targets = [('h', 'Ho'), ('b', 'Br'), ('d', 'Dj'), ('h/b', 'HW')]
    s_v, m_v, rats = [], [], []
    for _, col in targets:
        s = mutual_info_regression(geo[['s_e']], geo[col], discrete_features=True, random_state=42)[0]
        m = mutual_info_regression(geo[['m_e']], geo[col], discrete_features=True, random_state=42)[0]
        s_v.append(s); m_v.append(m); rats.append(s/m if m>0 else 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={'wspace': 0.3})
    x = np.arange(len(targets))
    ax1.bar(x - 0.15, s_v, 0.3, color='#5C6B7F', edgecolor=INK, alpha=0.8, label='stilperiode')
    ax1.bar(x + 0.15, m_v, 0.3, color='#A88C7B', edgecolor=INK, alpha=0.8, label='materialgruppe')
    ax1.set_xticks(x); ax1.set_xticklabels([t[0] for t in targets])
    ax1.set_ylabel('nmi (bits)'); ax1.set_title('i. prediktor-styrke', loc='left'); ax1.legend()

    ax2.hlines(range(len(targets)), 1, rats, colors=INK, linewidth=0.8)
    ax2.scatter(rats, range(len(targets)), color='#C8a268', s=40, edgecolor=INK, zorder=3)
    ax2.set_yticks(range(len(targets))); ax2.set_yticklabels([t[0] for t in targets])
    ax2.set_xlabel('forholdstal (stil/mat)'); ax2.set_title('ii. relativ dominans', loc='left')
    
    fig.savefig(FIG_OUT / 'fig-A6-2-prediktor.png', bbox_inches='tight')
    plt.close()
    print(f'wrote fig-A6-2-prediktor.png')

if __name__ == '__main__':
    main()
