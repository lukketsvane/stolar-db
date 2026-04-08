"""A.6.12 — Nyhetsrate i morforommet (Kauffmans tilstøytande moglege)
(Avleidd hypotese frå Proposisjon 6.5)

Avleidd hypotese: Etter Kauffman (1993) er evolusjonen ikkje styrt mot
ein fast attraktor, men driven av eit «det tilstøytande moglege» som
sjølv ekspanderer kvar gong nokon entrar ein ny region. To rivaliserande
prediksjonar:

  H_metning   — Eit avgrensa landskap. Talet på nye morforomregioner per
                tidsperiode skal flate ut når korpuset veks (mindre og
                mindre nytt blir mogleg).
  H_kauffman  — Eit ekspanderande moglegheitsrom. Talet på nye regionar
                blir verande høgt eller veks; det tilstøytande moglege
                ekspanderer i takt med korpuset.

Vi diskretiserer 3D-morforommet i 5 cm-kuber, går gjennom kvar 25-års-
periode i kronologisk rekkefølgje, og tel kor mange voksler er nyokku-
perte (dvs. ikkje var registrerte i nokon tidlegare periode). Resultatet
er nyhetsraten per periode.

Visuell: stem-plot av tal nye voksler per periode (raud), med kumulativ
totale voksler i ein bakgrunnsline (grå), og talet stolar per periode i
ein tynn teal-line på sekundæraksen.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, fig_size, load_chairs, FIG_DIR,
    INK, INK_SOFT, RULE, ACCENT_RUST, ACCENT_TEAL,
)

VOX_SIZE = 5.0     # cm — voxel side
START = 1500
END   = 2025
BIN_W = 25


def voxelise(values, vox=VOX_SIZE):
    return tuple((values // vox).astype(int))


def run_test():
    df = load_chairs()
    df = df.dropna(subset=['h_cm', 'w_cm', 'd_cm', 'year_mid']).copy()
    df = df[(df['h_cm'] > 0) & (df['w_cm'] > 0) & (df['d_cm'] > 0)]
    df = df[(df['year_mid'] >= START) & (df['year_mid'] <= END)]
    for c in ('h_cm', 'w_cm', 'd_cm'):
        lo, hi = np.percentile(df[c], [1, 99])
        df = df[(df[c] >= lo) & (df[c] <= hi)]

    df['period'] = (df['year_mid'] // BIN_W * BIN_W).astype(int)
    df['vox'] = list(zip(
        (df['h_cm'] // VOX_SIZE).astype(int),
        (df['w_cm'] // VOX_SIZE).astype(int),
        (df['d_cm'] // VOX_SIZE).astype(int),
    ))

    seen = set()
    rows = []
    for p in sorted(df['period'].unique()):
        sub = df[df['period'] == p]
        new_voxels = set(sub['vox']) - seen
        rows.append({
            'period':       int(p),
            'n_chairs':     int(len(sub)),
            'n_new':        int(len(new_voxels)),
            'cum_voxels':   int(len(seen) + len(new_voxels)),
            'novelty_rate': float(len(new_voxels)) / max(len(sub), 1),
        })
        seen |= new_voxels
    return rows, len(df), len(seen)


def plot(rows, n_total, n_voxels_total):
    apply_style()

    fig = plt.figure(figsize=fig_size(width_mm=89, ratio=0.85))
    ax = fig.add_axes([0.16, 0.20, 0.74, 0.62])
    ax2 = ax.twinx()

    p   = np.array([r['period']   for r in rows])
    new = np.array([r['n_new']    for r in rows])
    cum = np.array([r['cum_voxels'] for r in rows])
    chairs = np.array([r['n_chairs'] for r in rows])

    # Stems for new voxels per period
    ax.vlines(p, 0, new, color=ACCENT_RUST, linewidth=1.5, zorder=4)
    ax.scatter(p, new, color=ACCENT_RUST, s=14, zorder=5,
               edgecolor='none', label='Nye voksler')

    # Cumulative voxels (background line, soft ink)
    ax.plot(p, cum, color=INK_SOFT, linewidth=0.8,
            linestyle=(0, (3, 2)), alpha=0.9, zorder=2,
            label='Kumulativt')

    ax.set_xlim(START - 10, END + 10)
    ax.set_ylim(0, max(cum.max(), new.max()) * 1.05)
    ax.set_xlabel('Periode-start  (år)', fontsize=8.0)
    ax.set_ylabel('Talet voksler  (5 cm-kuber)', fontsize=8.0)
    ax.tick_params(axis='both', labelsize=7.5)

    # Sample-count line on the right axis
    ax2.plot(p, chairs, color=ACCENT_TEAL, linewidth=0.7,
             linestyle=':', alpha=0.85, zorder=3)
    ax2.set_ylabel('Talet stolar i perioden', fontsize=7.5, color=ACCENT_TEAL)
    ax2.tick_params(axis='y', labelsize=6.5, colors=ACCENT_TEAL)
    ax2.spines['top'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['right'].set_color(ACCENT_TEAL)

    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)

    leg = ax.legend(loc='upper left', fontsize=7,
                    handletextpad=0.4, labelspacing=0.25)
    for t in leg.get_texts():
        t.set_color(INK_SOFT)

    fig.text(0.04, 0.95,
             'Nyhetsraten metnar ikkje: det tilstøytande moglege ekspanderer',
             fontsize=9.5, color=INK, ha='left', va='top', weight='bold')
    fig.text(0.04, 0.90,
             f'Nye 5 cm-voksler per periode (raud) mot kumulativ summa (grå stipla)',
             fontsize=6.8, color=INK_SOFT, ha='left', va='top')

    fig.text(0.04, 0.025,
             f'n = {n_total} stolar  ·  totalt {n_voxels_total} unike voksler  ·  '
             f'25-årsperiodar',
             fontsize=6.3, color=INK_SOFT, ha='left')

    out = FIG_DIR / 'fig-A.6.12-nyhetsrate.pdf'
    fig.savefig(out)
    fig.savefig(out.with_suffix('.png'))
    return out


def main():
    rows, n, n_voxels = run_test()
    print(f'n = {n}, total unique voxels = {n_voxels}')
    for r in rows:
        print(f'  {r["period"]}  chairs={r["n_chairs"]:>3}  '
              f'new={r["n_new"]:>3}  cum={r["cum_voxels"]:>3}  '
              f'rate={r["novelty_rate"]:.2f}')
    out = plot(rows, n, n_voxels)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
