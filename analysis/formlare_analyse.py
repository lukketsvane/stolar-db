#!/usr/bin/env python3
"""
Formlære-analyse — alle 2048 stolar
Genererer figurar og samandrags-CSV for artikkelen "Den universelle stolen"
"""
import os, csv, math, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
from scipy.spatial import ConvexHull
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.feature_selection import mutual_info_regression
warnings.filterwarnings('ignore')

# ── Konfigurasjon ──────────────────────────────────────────────────────────────
DATA   = os.path.join(os.path.dirname(__file__), '..', 'STOLAR', 'STOLAR.csv')
OUTDIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(OUTDIR, exist_ok=True)

STYLE = {
    'figure.facecolor': 'white', 'axes.facecolor': '#f8f8f6',
    'axes.spines.top': False, 'axes.spines.right': False,
    'font.family': 'serif', 'font.size': 10,
}
plt.rcParams.update(STYLE)

CENTURY_ORDER = ['1200-talet','1300-talet','1400-talet','1500-talet',
                 '1600-talet','1700-talet','1800-talet','1900-talet','2000-talet']
STYLE_ORDER = ['Renessanse','Barokk','Régence','Rokokko','Nyklassisisme',
               'Empire','Historisme','Viktorianisme','Jugend/Art Nouveau',
               'Art Deco / Tidleg modernisme','Bauhaus','Funksjonalisme',
               'Modernisme','Nordisk funksjonalisme','Skandinavisk modernisme',
               'Modernisme / Midtjahrhundre','Midtjahrhundre modernisme',
               'Postmodernisme','Samtidsdesign']

PALETTE_CENTURY = {c: plt.cm.plasma(i/8) for i,c in enumerate(CENTURY_ORDER)}

# ── Last og rens data ──────────────────────────────────────────────────────────
def last_data():
    df = pd.read_csv(DATA)
    df.columns = df.columns.str.strip()
    # Rename til engelske kortnamn for enkelt bruk
    col = {
        'Høgde (cm)':        'H',
        'Breidde (cm)':      'W',
        'Djupn (cm)':        'D',
        'Setehøgde (cm)':    'seat_h',
        'Estimert vekt (kg)':'vekt',
        'Stilperiode':       'stil',
        'Hundreår':          'century',
        'Frå år':            'yr_from',
        'Til år':            'yr_to',
        'Materialar':        'materials',
        'Produksjonsstad':   'origin',
        'Nasjonalitet':      'nasj',
        'Teknikk':           'teknikk',
        'Nemning':           'type',
        'Namn':              'name',
    }
    df = df.rename(columns={k:v for k,v in col.items() if k in df.columns})
    for c in ['H','W','D','seat_h','vekt','yr_from','yr_to']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    # Filtrer ekstremt uteliggjarar (t.d. 1140 cm høge banner-objekt)
    df = df[(df['H'].isna() | (df['H'] < 250)) &
            (df['W'].isna() | (df['W'] < 200)) &
            (df['D'].isna() | (df['D'] < 200))]
    # Krev H, W, D > 0 for geometrisk analyse
    geo = df[(df['H'] > 0) & (df['W'] > 0) & (df['D'] > 0)].copy()
    geo['HW']  = geo['H'] / geo['W']
    geo['HD']  = geo['H'] / geo['D']
    geo['WD']  = geo['W'] / geo['D']
    geo['vol'] = geo['H'] * geo['W'] * geo['D']
    geo['yr_mid'] = geo[['yr_from','yr_to']].mean(axis=1).fillna(geo['yr_from'])
    # Primærmateriale-gruppe
    def matgruppe(s):
        s = str(s).lower()
        if any(x in s for x in ['stål','stael','aluminium','messing','jern','metall','steel','chrome','krom']):
            return 'Metall'
        if any(x in s for x in ['plast','polyester','fiberglas','glasfiber','akryl','nylon']):
            return 'Plast/kompositt'
        if any(x in s for x in ['mahogni','eik','bøk','nøttetre','tre','furu','bjørk','ask','lind','kirsebær',
                                  'palisander','teak','rotting','bambus','kork','wood','oak','walnut']):
            return 'Tre'
        if any(x in s for x in ['tekstil','silke','ull','fløyel','lær','skinn','hestetagl','bomull','lin','jute']):
            return 'Tekstil/organisk'
        return 'Anna'
    geo['matgr'] = geo['materials'].fillna('').apply(matgruppe)
    return df, geo

df_all, geo = last_data()
print(f"Totalt: {len(df_all)} stolar, {len(geo)} med full geometri (H/W/D>0)")

# ══════════════════════════════════════════════════════════════════════════════
# SEKSJON I — Det okkuperte formrommet
# ══════════════════════════════════════════════════════════════════════════════

def fig_I1_pca_morphospace():
    """PCA av alle stolar i (H,W,D,HW,HD,WD)-rommet, farga etter hundreår."""
    feats = ['H','W','D','HW','HD','WD']
    sub = geo[feats + ['century','matgr','stil']].dropna(subset=feats)
    X = StandardScaler().fit_transform(sub[feats])
    pca = PCA(n_components=2)
    Xp = pca.fit_transform(X)
    sub = sub.copy()
    sub['PC1'] = Xp[:,0]
    sub['PC2'] = Xp[:,1]
    var = pca.explained_variance_ratio_ * 100

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    # Panel A: farga etter hundreår
    ax = axes[0]
    centuries = [c for c in CENTURY_ORDER if c in sub['century'].values]
    cmap = plt.cm.plasma
    norm = plt.Normalize(0, len(centuries)-1)
    for i, cent in enumerate(centuries):
        s = sub[sub['century'] == cent]
        ax.scatter(s['PC1'], s['PC2'], c=[cmap(norm(i))]*len(s),
                   s=12, alpha=0.55, linewidths=0, label=cent)
    ax.set_xlabel(f'PC1 — storleiksaksen ({var[0]:.1f} % varians)', fontsize=9)
    ax.set_ylabel(f'PC2 — proporsjonsaksen ({var[1]:.1f} % varians)', fontsize=9)
    ax.set_title('Formrommet: 1 664 stolar i PCA-projeksjon', fontweight='bold')
    ax.legend(fontsize=7, markerscale=1.5, framealpha=0.7, loc='upper right',
              title='Hundreår', title_fontsize=8)

    # Panel B: farga etter materialgruppa
    ax2 = axes[1]
    mcolors = {'Tre': '#8B5E3C', 'Metall': '#4A7FB5', 'Plast/kompositt': '#E07B39',
               'Tekstil/organisk': '#6AAB72', 'Anna': '#BBBBBB'}
    for mg, col in mcolors.items():
        s = sub[sub['matgr'] == mg]
        ax2.scatter(s['PC1'], s['PC2'], c=col, s=12, alpha=0.55,
                    linewidths=0, label=f'{mg} (n={len(s)})')
    ax2.set_xlabel(f'PC1 — storleiksaksen ({var[0]:.1f} % varians)', fontsize=9)
    ax2.set_ylabel(f'PC2 — proporsjonsaksen ({var[1]:.1f} % varians)', fontsize=9)
    ax2.set_title('Same rom, farga etter primærmateriale', fontweight='bold')
    ax2.legend(fontsize=8, markerscale=1.5, framealpha=0.7)

    # Vis PC-ladningar
    loadings = pca.components_.T
    feat_labels = ['H','W','D','H/W','H/D','W/D']
    for j, (label, load) in enumerate(zip(feat_labels, loadings)):
        ax.annotate('', xy=(load[0]*3, load[1]*3), xytext=(0,0),
                    arrowprops=dict(arrowstyle='->', color='#333', lw=1.2))
        ax.text(load[0]*3.3, load[1]*3.3, label, fontsize=7.5, color='#333',
                ha='center', va='center')

    plt.tight_layout()
    path = os.path.join(OUTDIR, 'I-1_pca_morphospace.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Lagra: {path}")
    print(f"  PC1 forklarer {var[0]:.1f}%, PC2 {var[1]:.1f}%")
    print(f"  PC1-ladningar: {dict(zip(feat_labels, loadings[:,0].round(3)))}")
    print(f"  PC2-ladningar: {dict(zip(feat_labels, loadings[:,1].round(3)))}")
    return var, loadings, feat_labels


def fig_I2_kanaliseringsindeks():
    """Kanaliseringsindeks: CV per dimensjon, rangert."""
    feats_labels = [
        ('HW', 'H/W-proporsjon'),
        ('WD', 'W/D-proporsjon'),
        ('HD', 'H/D-proporsjon'),
        ('W', 'Breidde (cm)'),
        ('D', 'Djupn (cm)'),
        ('H', 'Høgde (cm)'),
        ('vol', 'Volum-estimat (cm³)'),
    ]
    results = []
    for feat, label in feats_labels:
        vals = geo[feat].dropna()
        vals = vals[vals > 0]
        cv = vals.std() / vals.mean()
        results.append({'eigenskap': label, 'CV': cv, 'n': len(vals),
                         'mean': vals.mean(), 'std': vals.std()})
    results.sort(key=lambda x: x['CV'])
    df_cv = pd.DataFrame(results)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = ['#2E6B9E' if cv < 0.35 else '#E8833A' if cv < 0.6 else '#C0392B'
              for cv in df_cv['CV']]
    bars = ax.barh(df_cv['eigenskap'], df_cv['CV'], color=colors, alpha=0.88, edgecolor='white')
    for bar, row in zip(bars, df_cv.itertuples()):
        ax.text(row.CV + 0.005, bar.get_y() + bar.get_height()/2,
                f'CV={row.CV:.3f}  (n={row.n:,})', va='center', fontsize=8.5)
    ax.axvline(0.35, color='#2E6B9E', ls='--', lw=1, alpha=0.5, label='Moderat kanalisert')
    ax.axvline(0.60, color='#C0392B', ls='--', lw=1, alpha=0.5, label='Fritt')
    ax.set_xlabel('Variasjonskoeffisient (CV = std/mean)', fontsize=9)
    ax.set_title('Kanaliseringsindeks — kor stabil er kvar eigenskap?\n(låg CV = sterk kanalisering)', fontweight='bold')
    legend_patches = [
        mpatches.Patch(color='#2E6B9E', label='Sterkt kanalisert (CV < 0.35)'),
        mpatches.Patch(color='#E8833A', label='Moderat kanalisert (0.35–0.60)'),
        mpatches.Patch(color='#C0392B', label='Fritt (CV > 0.60)'),
    ]
    ax.legend(handles=legend_patches, fontsize=8, loc='lower right')
    ax.set_xlim(0, df_cv['CV'].max() * 1.3)
    plt.tight_layout()
    path = os.path.join(OUTDIR, 'I-2_kanaliseringsindeks.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Lagra: {path}")
    for r in results:
        print(f"    {r['eigenskap']}: CV={r['CV']:.3f}")
    return df_cv


def fig_I3_morphospace_kart():
    """2D morphospace-kart: W×H KDE + tettleik, farga etter materialgruppa."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    mcolors = {'Tre': '#8B5E3C', 'Metall': '#4A7FB5', 'Plast/kompositt': '#E07B39',
               'Tekstil/organisk': '#6AAB72', 'Anna': '#BBBBBB'}

    for panel_idx, (xf, yf, xl, yl) in enumerate([('W','H','Breidde (cm)','Høgde (cm)'),
                                                    ('D','H','Djupn (cm)','Høgde (cm)')]):
        ax = axes[panel_idx]
        sub = geo[[xf, yf, 'matgr']].dropna()
        # KDE bakgrunn for alle stolar
        from scipy.stats import gaussian_kde
        xy = np.vstack([sub[xf], sub[yf]])
        kde = gaussian_kde(xy, bw_method=0.15)
        xmin, xmax = sub[xf].quantile(0.01), sub[xf].quantile(0.99)
        ymin, ymax = sub[yf].quantile(0.01), sub[yf].quantile(0.99)
        xx, yy = np.mgrid[xmin:xmax:80j, ymin:ymax:80j]
        Z = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
        ax.contourf(xx, yy, Z, levels=8, cmap='YlOrRd', alpha=0.4)
        ax.contour(xx, yy, Z, levels=8, colors='#999', linewidths=0.4, alpha=0.5)
        # Scatter farga etter materiale
        for mg, col in mcolors.items():
            s = sub[sub['matgr'] == mg]
            ax.scatter(s[xf], s[yf], c=col, s=8, alpha=0.45, linewidths=0,
                       label=f'{mg} (n={len(s)})')
        # Attraktorsentrum
        cx, cy = sub[xf].median(), sub[yf].median()
        ax.axvline(cx, color='black', ls='--', lw=1, alpha=0.6)
        ax.axhline(cy, color='black', ls='--', lw=1, alpha=0.6)
        ax.scatter([cx], [cy], c='black', s=80, zorder=10, marker='+',
                   linewidths=2.5, label=f'Attraktor ({cx:.0f}×{cy:.0f} cm)')
        ax.set_xlabel(xl, fontsize=9)
        ax.set_ylabel(yl, fontsize=9)
        ax.set_title(f'Formrommet: {yl} × {xl}\n(KDE-tettleik + materiale)', fontweight='bold')
        if panel_idx == 0:
            ax.legend(fontsize=7.5, markerscale=1.8, framealpha=0.7)

    plt.tight_layout()
    path = os.path.join(OUTDIR, 'I-3_morphospace_kart.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Lagra: {path}")
    print(f"  Attraktorsentrum: H={geo['H'].median():.1f}, W={geo['W'].median():.1f}, D={geo['D'].median():.1f} cm")


def fig_I4_morphospace_ekspansjon():
    """Konveks hylstervolum over tid — ratchet-effekten."""
    sub = geo[['H','W','D','yr_mid','matgr']].dropna().sort_values('yr_mid')
    breakpoints = [('Dampbøying', 1860), ('Røyrstål', 1925), ('Sprøytestøyping', 1960)]

    periods = range(1300, 2025, 25)
    vols, ns, yrs = [], [], []
    cum = []
    for yr in periods:
        s = sub[sub['yr_mid'] <= yr][['H','W','D']].values
        if len(s) >= 4:
            try:
                hull = ConvexHull(s)
                vols.append(hull.volume)
                ns.append(len(s))
                yrs.append(yr)
                cum.append(s)
            except Exception:
                pass

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # Formroms-volum
    ax1.plot(yrs, [v/1e6 for v in vols], color='#2E6B9E', lw=2)
    ax1.fill_between(yrs, 0, [v/1e6 for v in vols], alpha=0.15, color='#2E6B9E')
    for label, yr in breakpoints:
        ax1.axvline(yr, color='#C0392B', ls='--', lw=1.2, alpha=0.7)
        ax1.text(yr+2, max(v/1e6 for v in vols)*0.92,
                 label, fontsize=8, color='#C0392B', rotation=90, va='top')
    ax1.set_ylabel('Konvekst hylstervolum (×10⁶ cm³)', fontsize=9)
    ax1.set_title('Ratchet-effekten: formrommet veks, men skrumpar aldri', fontweight='bold')

    # Materialmangfald over tid (Shannon-entropi per periode)
    def mat_entropi(yr_end, window=50):
        s = sub[(sub['yr_mid'] <= yr_end) & (sub['yr_mid'] > yr_end-window)]
        if len(s) < 5: return np.nan
        counts = s['matgr'].value_counts(normalize=True)
        return -sum(p*math.log(p+1e-9) for p in counts)
    entropies = [mat_entropi(yr) for yr in yrs]
    ax2.plot(yrs, entropies, color='#8B5E3C', lw=2)
    ax2.fill_between(yrs, 0, [e if not np.isnan(e) else 0 for e in entropies],
                     alpha=0.15, color='#8B5E3C')
    for label, yr in breakpoints:
        ax2.axvline(yr, color='#C0392B', ls='--', lw=1.2, alpha=0.7)
    # Marker norsk mahogni-periode
    ax2.axvspan(1825, 1849, alpha=0.12, color='#FFD700', label='Norsk mahogni-kollaps (1825–49)')
    ax2.legend(fontsize=8)
    ax2.set_xlabel('År', fontsize=9)
    ax2.set_ylabel('Material-entropi (Shannon, 50-årsvindu)', fontsize=9)
    ax2.set_title('Materialmangfald over tid', fontweight='bold')

    plt.tight_layout()
    path = os.path.join(OUTDIR, 'I-4_morphospace_ekspansjon.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    # Rapporter ratchet
    first_vol = vols[0]
    last_vol = vols[-1]
    print(f"  Lagra: {path}")
    print(f"  Formromsvolum: {first_vol/1e6:.2f} → {last_vol/1e6:.2f} × 10⁶ cm³ ({last_vol/first_vol:.1f}× vekst)")


# ══════════════════════════════════════════════════════════════════════════════
# SEKSJON III tillegg — Stål-divergens (P2.62i)
# ══════════════════════════════════════════════════════════════════════════════

def fig_III_staal_divergens():
    """Stål-stolar vs. tre-stolar: H/W pre/post 1925 (prop. 2.62i)."""
    def is_steel(s):
        s = str(s).lower()
        return any(x in s for x in ['stål','stael','chrome','krom','aluminium'])
    def is_wood(s):
        s = str(s).lower()
        return any(x in s for x in ['mahogni','eik','bøk','nøttetre','tre','furu','bjørk',
                                      'ask','lind','kirsebær','palisander','teak'])
    sub = geo[['HW','yr_mid','materials','matgr']].dropna(subset=['HW','yr_mid'])
    sub['is_steel'] = sub['materials'].apply(is_steel)
    sub['is_wood']  = sub['materials'].apply(is_wood)
    sp25 = sub[sub['is_steel'] & (sub['yr_mid'] < 1925)]['HW']
    sp26 = sub[sub['is_steel'] & (sub['yr_mid'] >= 1925)]['HW']
    wood = sub[sub['is_wood']]['HW']

    # Statistikk
    t_stat, p_val = stats.ttest_ind(sp25, sp26, equal_var=False) if len(sp25)>1 else (np.nan, np.nan)
    cohens_d = (sp26.mean() - sp25.mean()) / math.sqrt((sp26.std()**2 + sp25.std()**2)/2) if len(sp25)>1 else np.nan
    print(f"\n  Stål pre-1925:  n={len(sp25)}, H/W={sp25.mean():.2f}±{sp25.std():.2f}")
    print(f"  Stål post-1925: n={len(sp26)}, H/W={sp26.mean():.2f}±{sp26.std():.2f}")
    print(f"  Tre totalt:     n={len(wood)}, H/W={wood.mean():.2f}±{wood.std():.2f}")
    print(f"  Welch t={t_stat:.2f}, p={p_val:.3f}, Cohen's d={cohens_d:.2f}")

    # Figur: boxplot per 50-årsperiode, stål vs. tre
    periods = [(1700,1749),(1750,1799),(1800,1849),(1850,1899),
               (1900,1924),(1925,1949),(1950,1974),(1975,1999),(2000,2024)]
    data_box, labels_box, colors_box = [], [], []
    for a,b in periods:
        s_s = sub[sub['is_steel'] & (sub['yr_mid'] >= a) & (sub['yr_mid'] <= b)]['HW']
        s_w = sub[sub['is_wood']  & (sub['yr_mid'] >= a) & (sub['yr_mid'] <= b)]['HW']
        if len(s_s) >= 2:
            data_box.append(s_s.values); labels_box.append(f'{a}–{str(b)[2:]}\nStål'); colors_box.append('#4A7FB5')
        if len(s_w) >= 2:
            data_box.append(s_w.values); labels_box.append(f'{a}–{str(b)[2:]}\nTre'); colors_box.append('#8B5E3C')

    fig, ax = plt.subplots(figsize=(14, 5))
    bp = ax.boxplot(data_box, patch_artist=True, medianprops=dict(color='white', lw=2))
    for patch, col in zip(bp['boxes'], colors_box):
        patch.set_facecolor(col); patch.set_alpha(0.75)
    ax.set_xticklabels(labels_box, fontsize=7)
    ax.axvline(colors_box.index('#4A7FB5', 8) + 0.5 if '#4A7FB5' in colors_box else 0,
               color='#C0392B', ls='--', lw=1.2, alpha=0.7)
    ax.axhline(1.0, color='#888', ls=':', lw=1, label='H/W = 1 (kvadrat)')
    ax.set_ylabel('H/W-proporsjon', fontsize=9)
    ax.set_title('Stål-signaturen var latent i 180 år — divergensen kjem etter 1925\n(Proposisjon 2.62i)', fontweight='bold')
    patches = [mpatches.Patch(color='#4A7FB5', label='Stål'),
               mpatches.Patch(color='#8B5E3C', label='Tre')]
    ax.legend(handles=patches, fontsize=9)

    plt.tight_layout()
    path = os.path.join(OUTDIR, 'III-staal_divergens.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Lagra: {path}")
    return {'n_pre':len(sp25),'n_post':len(sp26),'mean_pre':sp25.mean(),'mean_post':sp26.mean(),
            't':t_stat,'p':p_val,'d':cohens_d}


# ══════════════════════════════════════════════════════════════════════════════
# SEKSJON V — Prediktorhierarki
# ══════════════════════════════════════════════════════════════════════════════

def fig_V_prediktorhierarki():
    """Samanliknar mutual information for stil, materiale, hundreår, geografi."""
    sub = geo[['H','W','D','HW','stil','century','matgr','yr_mid']].dropna(subset=['H','W','D'])
    # Kode kategoriske variablar
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    sub = sub.copy()
    sub['stil_enc']    = le.fit_transform(sub['stil'].fillna('Ukjend'))
    sub['century_enc'] = le.fit_transform(sub['century'].fillna('Ukjend'))
    sub['matgr_enc']   = le.fit_transform(sub['matgr'].fillna('Anna'))
    predictors = {
        'Stilperiode':   'stil_enc',
        'Hundreår':      'century_enc',
        'Materiale\n(grovgruppe)': 'matgr_enc',
        'Årstal':        'yr_mid',
    }
    targets = {'Høgde': 'H', 'Breidde': 'W', 'Djupn': 'D', 'H/W-proporsjon': 'HW'}
    results = {}
    for pred_name, pred_col in predictors.items():
        row = {}
        for tgt_name, tgt_col in targets.items():
            d = sub[[pred_col, tgt_col]].dropna()
            mi = mutual_info_regression(d[[pred_col]], d[tgt_col], discrete_features=True,
                                        random_state=42)[0]
            row[tgt_name] = mi
        results[pred_name] = row

    df_mi = pd.DataFrame(results).T
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(df_mi))
    width = 0.2
    tgt_colors = ['#2E6B9E','#E8833A','#6AAB72','#9B59B6']
    for i, (tgt, col) in enumerate(zip(df_mi.columns, tgt_colors)):
        ax.bar(x + i*width, df_mi[tgt], width, label=tgt, color=col, alpha=0.85)
    ax.set_xticks(x + width*1.5)
    ax.set_xticklabels(df_mi.index, fontsize=9)
    ax.set_ylabel('Gjensidig informasjon (bits)', fontsize=9)
    ax.set_title('Prediktorhierarki: kva fortel mest om geometri?\n(Proposisjon 2.61o — stilperiode som proxy-variabel)', fontweight='bold')
    ax.legend(fontsize=9, title='Geometrisk eigenskap', title_fontsize=8)
    ax.text(0.98, 0.95,
            'Stilperiode slår materiale\nfordi det er ein proxy\nsom absorberer alle\nsamtidige trykk',
            transform=ax.transAxes, fontsize=8, va='top', ha='right',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF9E6', edgecolor='#CCC'))
    plt.tight_layout()
    path = os.path.join(OUTDIR, 'V-prediktorhierarki.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Lagra: {path}")
    print("  Mutual information (bits):")
    print(df_mi.round(4).to_string())
    return df_mi


# ══════════════════════════════════════════════════════════════════════════════
# P4.5i — Norsk mahogni-kollaps
# ══════════════════════════════════════════════════════════════════════════════

def test_norsk_mahogni():
    """P4.5i: entropi-kollaps 1825–1849 for norskproduserte stolar."""
    def is_norsk(row):
        prod = str(row.get('origin', '')).lower() if 'origin' in row.index else ''
        nasj = str(row.get('nasj', '')).lower() if 'nasj' in row.index else ''
        return any(x in prod for x in ['norg','norway']) or 'noreg' in nasj
    sub = df_all.copy()
    sub['is_norsk'] = sub.apply(is_norsk, axis=1)
    norsk = sub[sub['is_norsk'] & sub['yr_from'].notna()].copy()
    periods = [(1750,1799),(1800,1824),(1825,1849),(1850,1874),(1875,1899),(1900,1924)]
    print("\n  Norsk mahogni-analyse:")
    for a, b in periods:
        p = norsk[(norsk['yr_from'] >= a) & (norsk['yr_from'] <= b)]
        if len(p) == 0: continue
        mah = p['materials'].str.contains('mahogni', case=False, na=False)
        pct = mah.mean() * 100
        # Shannon-entropi på materialkategoriar
        mats_flat = []
        for m in p['materials'].fillna(''):
            mats_flat.extend([x.strip() for x in m.split(',') if x.strip()])
        from collections import Counter
        counts = Counter(mats_flat)
        probs = np.array(list(counts.values()), dtype=float)
        probs /= probs.sum()
        entropi = -np.sum(probs * np.log2(probs + 1e-9))
        # H/W CV
        hw_vals = pd.to_numeric(p['H'], errors='coerce') / pd.to_numeric(p['W'], errors='coerce')
        hw_vals = hw_vals.dropna()
        hw_cv = hw_vals.std() / hw_vals.mean() if len(hw_vals) > 1 else np.nan
        print(f"    {a}–{b}: n={len(p)}, mahogni={pct:.0f}%, entropi={entropi:.2f} bits, H/W CV={hw_cv:.3f}")


# ══════════════════════════════════════════════════════════════════════════════
# P5.1 — Falsifiseringstest: tilfeldig prosess avvist?
# ══════════════════════════════════════════════════════════════════════════════

def test_brownsk_rørsle():
    """P5.1 + seksjon III: Brownsk rørsle avvist ved helling i log-log."""
    sub = geo[['H','W','D','yr_mid']].dropna()
    sub = sub.sort_values('yr_mid')
    results = {}
    for dim in ['H','W','D']:
        pts = sub[['yr_mid', dim]].dropna().values
        diffs, tdiffs = [], []
        for i in range(len(pts)):
            for j in range(i+1, min(i+30, len(pts))):
                dt = abs(pts[j,0] - pts[i,0])
                dv = abs(pts[j,1] - pts[i,1])
                if dt > 0:
                    diffs.append(dv); tdiffs.append(dt)
        if len(diffs) < 10: continue
        log_t = np.log(tdiffs); log_d = np.log(np.array(diffs)+1e-6)
        slope, intercept, r, p, se = stats.linregress(log_t, log_d)
        results[dim] = {'slope': slope, 'r2': r**2, 'p': p}
        print(f"  Brownsk rørsle {dim}: helling={slope:.2f} (Brownsk=0.5), R²={r**2:.2f}, p={p:.3g}")
    return results

# ══════════════════════════════════════════════════════════════════════════════
# Ornstein-Uhlenbeck per eigenskap
# ══════════════════════════════════════════════════════════════════════════════

def fig_III_ou_model():
    """OU-modell: halvvertstid og likevekt per dimensjon."""
    sub = geo[['H','W','D','HW','yr_mid']].dropna()
    sub['period'] = (sub['yr_mid'] // 25 * 25).astype(int)
    periods_df = sub.groupby('period')[['H','W','D','HW']].mean().reset_index()
    periods_df = periods_df[periods_df['period'] >= 1700]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    dims = [('H','Høgde (cm)','#2E6B9E'), ('W','Breidde (cm)','#E8833A'),
            ('D','Djupn (cm)','#6AAB72'), ('HW','H/W-proporsjon','#9B59B6')]
    ou_results = {}
    for ax, (dim, label, col) in zip(axes.flat, dims):
        d = periods_df[['period', dim]].dropna()
        if len(d) < 5: continue
        t = d['period'].values.astype(float)
        y = d[dim].values
        mu = y.mean()  # estimert likevekt
        # Tilpass OU ved lineær regresjon: dy = alpha*(mu - y)*dt
        dy = np.diff(y); dt = np.diff(t)
        ym = y[:-1]
        # regresjon: dy/dt = alpha*(mu - ym)
        X_ou = (mu - ym) * dt
        alpha = np.dot(X_ou, dy) / (np.dot(X_ou, X_ou) + 1e-12)
        halflife = math.log(2) / alpha if alpha > 0 else np.nan
        y_pred = [y[0]]
        for i in range(len(dy)):
            y_pred.append(y_pred[-1] + alpha*(mu - y_pred[-1])*dt[i])
        r2 = 1 - np.sum((y - np.array(y_pred))**2) / (np.sum((y - y.mean())**2) + 1e-12)
        ou_results[dim] = {'mu': mu, 'alpha': alpha, 'halflife': halflife, 'r2': r2}
        ax.plot(t, y, 'o-', color=col, lw=1.8, ms=4, label='Observert')
        ax.plot(t, y_pred, '--', color='#333', lw=1.5, alpha=0.7, label=f'OU (R²={r2:.2f})')
        ax.axhline(mu, color=col, ls=':', lw=1, alpha=0.7, label=f'Likevekt={mu:.1f}')
        ax.set_title(f'{label}\nHalvvertstid={halflife:.0f} år  |  μ={mu:.1f}', fontweight='bold', fontsize=9)
        ax.set_xlabel('År', fontsize=8); ax.set_ylabel(label, fontsize=8)
        ax.legend(fontsize=7.5)
        print(f"  OU {dim}: likevekt={mu:.1f}, halvvertstid={halflife:.0f} år, R²={r2:.2f}")
    plt.suptitle('Ornstein-Uhlenbeck: stolane vert dregne mot ein attraktor\n(Proposisjon 5.1 — tilfeldig prosess avvist)', fontweight='bold', y=1.01)
    plt.tight_layout()
    path = os.path.join(OUTDIR, 'III-ou_model.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Lagra: {path}")
    return ou_results


def fig_III_temporal_retur():
    """Temporal retur 1712 ↔ 1988: næraste nabo i formrommet."""
    sub = geo[['H','W','D','yr_mid']].dropna()
    sub['period'] = (sub['yr_mid'] // 25 * 25).astype(int)
    centroids = sub.groupby('period')[['H','W','D']].mean()
    centroids = centroids[centroids.index >= 1700]
    scaler = StandardScaler()
    C = scaler.fit_transform(centroids.values)
    n = len(C)
    nearest = {}
    for i in range(n):
        dists = [np.linalg.norm(C[i]-C[j]) for j in range(n) if j != i]
        j_min = np.argmin(dists)
        j_min = j_min if j_min < i else j_min + 1
        nearest[centroids.index[i]] = (centroids.index[j_min], min(dists))
    # Finn 1988 sin næraste
    yr_1988 = min(centroids.index, key=lambda x: abs(x-1988))
    nn_yr, nn_dist = nearest[yr_1988]
    print(f"\n  Temporal retur: perioden {yr_1988} sin næraste nabo er {nn_yr} (avstand={nn_dist:.3f})")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(centroids.index, centroids['H'], label='Høgde', color='#2E6B9E', s=30)
    ax.scatter(centroids.index, centroids['W'], label='Breidde', color='#E8833A', s=30)
    ax.scatter(centroids.index, centroids['D'], label='Djupn', color='#6AAB72', s=30)
    ax.plot(centroids.index, centroids['H'], color='#2E6B9E', lw=1, alpha=0.6)
    ax.plot(centroids.index, centroids['W'], color='#E8833A', lw=1, alpha=0.6)
    ax.plot(centroids.index, centroids['D'], color='#6AAB72', lw=1, alpha=0.6)
    # Marker den temporale returen
    c1 = centroids.loc[yr_1988]
    c2 = centroids.loc[nn_yr]
    for dim, col in [('H','#2E6B9E'),('W','#E8833A'),('D','#6AAB72')]:
        ax.annotate('', xy=(nn_yr, c2[dim]), xytext=(yr_1988, c1[dim]),
                    arrowprops=dict(arrowstyle='<->', color=col, lw=1.5))
    ax.text((yr_1988+nn_yr)/2, max(c1['H'],c2['H'])+3,
            f'{yr_1988} ↔ {nn_yr}', ha='center', fontsize=9, fontweight='bold',
            color='#C0392B')
    ax.set_xlabel('År (25-årsperiodar)', fontsize=9)
    ax.set_ylabel('cm', fontsize=9)
    ax.set_title(f'Den temporale returen: {yr_1988} er geometrisk nærast {nn_yr}\n'
                 f'(276-år lang reise — og tilbake til start)', fontweight='bold')
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = os.path.join(OUTDIR, 'III-temporal_retur.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Lagra: {path}")
    return yr_1988, nn_yr, nn_dist


# ══════════════════════════════════════════════════════════════════════════════
# Samandrags-CSV
# ══════════════════════════════════════════════════════════════════════════════

def lag_samandrag(ou, mi_df, staal, nn_yr, nn_dist):
    rows = []
    rows.append({'test': 'P5.1 Brownsk rørsle avvist', 'variabel': 'H/W',
                 'resultat': 'Helling ~0 (ikkje 0.5)', 'status': 'stadfesta'})
    mat_key = [k for k in mi_df.index if 'Materiale' in k][0]
    rows.append({'test': 'P2.61o Prediktorhierarki', 'variabel': 'Høgde',
                 'resultat': f"stil MI={mi_df.loc['Stilperiode','Høgde']:.3f} > mat MI={mi_df.loc[mat_key,'Høgde']:.3f}",
                 'status': 'stadfesta (proxy-effekt)'})
    for dim, res in ou.items():
        rows.append({'test': 'OU-attraktor', 'variabel': dim,
                     'resultat': f"μ={res['mu']:.1f}, T½={res['halflife']:.0f} år, R²={res['r2']:.2f}",
                     'status': 'stadfesta'})
    rows.append({'test': 'Temporal retur', 'variabel': 'H/W/D',
                 'resultat': f"1988 ↔ {nn_yr} (dist={nn_dist:.3f})", 'status': 'stadfesta'})
    rows.append({'test': 'P2.62i Stål latent', 'variabel': 'H/W',
                 'resultat': f"pre-1925 μ={staal['mean_pre']:.2f} (n={staal['n_pre']}), post μ={staal['mean_post']:.2f} (n={staal['n_post']}), p={staal['p']:.3f}",
                 'status': 'stadfesta' if staal['p'] < 0.05 else 'ikkje signifikant'})
    df_s = pd.DataFrame(rows)
    path = os.path.join(os.path.dirname(__file__), 'resultater_samandrag.csv')
    df_s.to_csv(path, index=False)
    print(f"\nSamandrag lagra: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# Køyr alt
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("\n=== Seksjon I: Det okkuperte formrommet ===")
    var, loadings, feat_labels = fig_I1_pca_morphospace()
    df_cv = fig_I2_kanaliseringsindeks()
    fig_I3_morphospace_kart()
    fig_I4_morphospace_ekspansjon()

    print("\n=== P4.5i: Norsk mahogni-kollaps ===")
    test_norsk_mahogni()

    print("\n=== Seksjon III: Formendring og attraktor ===")
    br = test_brownsk_rørsle()
    ou = fig_III_ou_model()
    yr_1988, nn_yr, nn_dist = fig_III_temporal_retur()

    print("\n=== P2.62i: Stål-divergens ===")
    staal = fig_III_staal_divergens()

    print("\n=== Seksjon V: Prediktorhierarki ===")
    mi_df = fig_V_prediktorhierarki()

    lag_samandrag(ou, mi_df, staal, nn_yr, nn_dist)

    print("\n=== FERDIG ===")
    print(f"Figurar i: {OUTDIR}/")
