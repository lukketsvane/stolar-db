"""A.6.20 — Stolatlaset
(Specimen plate: every chair as one solid tile, full bleed)

Pure colour mosaic, no chrome:
  • The whole figure IS the atlas. No title, no legend, no year ticks,
    no axis lines, no padding, no inset. Every pixel is data.
  • Each cell is ONE solid colour — no inner block, no glyph, no
    seat line. The cell is full-bleed.
  • Cell colour is the material's hue, modulated by the chair's
    own (Breidde, Høgde): height pulls the value down (taller =
    deeper), width pulls saturation up (wider = more saturated).
    Every chair gets a unique shade that still reads as its
    material category.
  • Tiles touch edge-to-edge with antialias OFF, so adjacent cells
    of similar colour merge into solid blocks. The only visible
    boundaries are where dimensions or material change.
  • Sorted column-major by year — read down columns for chronology.
    Six centuries of warm wood collapse in a hard vertical line at
    1900 into the cool teal/rust/gold field of the modern era.

Title, legend and year markers belong in the LaTeX caption beneath
this figure, not in the figure itself.
"""
from __future__ import annotations

import sys
import colorsys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from style import (
    apply_style, load_chairs, FIG_DIR, MM_PER_INCH,
)


# ── Material categorisation ─────────────────────────────────────────────────
WOOD_TOKENS = (
    'tre', 'eik', 'bjørk', 'bjork', 'bøk', 'bok', 'furu',
    'mahogni', 'nøttetre', 'nottetre', 'ask', 'teak', 'valnøtt',
    'valnott', 'palisander', 'lønn', 'lonn', 'rosentre', 'sitka',
)


# (hue 0-1, base saturation, base value) — every chair will be a
# perturbation of this seed point in HSV space.
MATERIAL_HSV = {
    # Hue, Sat, Val
    'tre':        (0.085, 0.78, 0.55),  # warm wood brown
    'stål':       (0.045, 0.85, 0.78),  # bright rust
    'kryssfiner': (0.555, 0.70, 0.55),  # mid teal
    'plast':      (0.115, 0.85, 0.75),  # bright gold
    'aluminium':  (0.520, 0.10, 0.62),  # cool slate
    'annet':      (0.090, 0.20, 0.78),  # warm cream
}


def categorise(material: object) -> str:
    if not isinstance(material, str):
        return 'annet'
    s = material.lower()
    if 'stål' in s:        return 'stål'
    if 'kryssfiner' in s:  return 'kryssfiner'
    if 'plast' in s:       return 'plast'
    if 'aluminium' in s:   return 'aluminium'
    if any(tok in s for tok in WOOD_TOKENS):
        return 'tre'
    return 'annet'


def chair_color(mat: str, h_cm: float, w_cm: float,
                d_cm: float) -> tuple[float, float, float]:
    """One unique colour per chair, anchored to its material's HSV seed."""
    h, s, v = MATERIAL_HSV[mat]

    # Height modulates brightness: tall chairs are deeper / darker.
    # Range covered: ~60-130 cm.
    h_norm = float(np.clip((h_cm - 60) / 70.0, 0.0, 1.0))
    v_mod = v - 0.30 * h_norm

    # Width modulates saturation: wider chairs are punchier.
    # Range covered: ~38-80 cm.
    w_norm = float(np.clip((w_cm - 38) / 42.0, 0.0, 1.0))
    s_mod = s * (0.55 + 0.50 * w_norm)

    # Depth gives a tiny hue tilt — barely perceptible, just enough
    # to break up uniformity within a column.
    d_norm = float(np.clip((d_cm - 38) / 42.0, 0.0, 1.0))
    h_mod = h + (d_norm - 0.5) * 0.012

    h_mod = h_mod % 1.0
    s_mod = float(np.clip(s_mod, 0.0, 1.0))
    v_mod = float(np.clip(v_mod, 0.05, 0.95))
    return colorsys.hsv_to_rgb(h_mod, s_mod, v_mod)


# ── Atlas geometry ──────────────────────────────────────────────────────────
N_COLS = 40
N_ROWS = 40


def main():
    apply_style()

    df = load_chairs()
    bad_to = df['year_to'].fillna(0) == 0
    df.loc[bad_to, 'year_mid'] = df.loc[bad_to, 'year_from']

    df = df.dropna(subset=['h_cm', 'w_cm', 'd_cm', 'year_mid']).copy()
    df = df[(df['h_cm'] > 30) & (df['h_cm'] < 200)]
    df = df[(df['w_cm'] > 25) & (df['w_cm'] < 150)]
    df = df[(df['d_cm'] > 20) & (df['d_cm'] < 150)]
    df = df[df['year_mid'] > 1100]
    df = df.sort_values('year_mid', kind='mergesort').reset_index(drop=True)
    df['mat'] = df['material'].apply(categorise)

    n_cells = N_COLS * N_ROWS
    if len(df) > n_cells:
        idx = np.linspace(0, len(df) - 1, n_cells).round().astype(int)
        df = df.iloc[idx].reset_index(drop=True)

    # ── Build the colour grid ──────────────────────────────────────────────
    # Image is rendered as an RGB ndarray and shown via imshow with
    # interpolation='nearest' so the cell boundaries are pixel-sharp.
    grid = np.zeros((N_ROWS, N_COLS, 3), dtype=np.float32)
    # Fill background with the first material colour so any unused cell
    # at the corpus tail blends in instead of leaving a white hole.
    fill_color = chair_color(df.iloc[-1]['mat'],
                             float(df.iloc[-1]['h_cm']),
                             float(df.iloc[-1]['w_cm']),
                             float(df.iloc[-1]['d_cm']))
    grid[:, :] = fill_color

    for i, row in df.iterrows():
        col = i // N_ROWS
        rownum = i % N_ROWS
        grid[rownum, col] = chair_color(
            row['mat'],
            float(row['h_cm']),
            float(row['w_cm']),
            float(row['d_cm']),
        )

    # ── Figure: pure mosaic, full bleed ────────────────────────────────────
    # Aspect: cells are SQUARE in the saved image — let imshow handle it.
    fig_w_mm = 105.0
    fig_h_mm = 168.0
    fig = plt.figure(figsize=(fig_w_mm / MM_PER_INCH,
                              fig_h_mm / MM_PER_INCH))

    # Single axes filling the entire figure — no margin anywhere.
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_facecolor((0, 0, 0, 0))
    ax.imshow(
        grid,
        interpolation='nearest',
        aspect='auto',           # stretch to fill the axes
        origin='upper',
    )
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ('top', 'right', 'bottom', 'left'):
        ax.spines[sp].set_visible(False)

    out = FIG_DIR / 'fig-A.6.20-stolatlaset.pdf'
    fig.savefig(out, pad_inches=0)
    fig.savefig(out.with_suffix('.png'), dpi=400, pad_inches=0)
    print(f'wrote {out}  ({len(df)} chairs)')

    # Print the chronological year markers as plain text — these go in
    # the LaTeX caption now, not in the figure.
    print('\nChronological column-start years:')
    for c in range(0, N_COLS, 4):
        first_in_col = c * N_ROWS
        if first_in_col >= len(df):
            continue
        yr = int(df.iloc[first_in_col]['year_mid'])
        print(f'  col {c:2d} → {yr}')

    return out


if __name__ == '__main__':
    main()
