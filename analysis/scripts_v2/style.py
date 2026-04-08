"""Shared matplotlib style for FORMLÆRE figures.

A single warm-ink palette inspired by Töpfer/digibok scientific plates and
the EB Garamond body type used in the typeset book. Every figure imports
this module and calls `apply_style()` before plotting; this guarantees the
palette, fonts, sizes, and grid behaviour are identical across the appendix.

Physical target: figures embed at 89 mm = the body column width of the
125 × 200 mm book page. We render at 320 ppi to keep text crisp when the
PDF is printed.
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from pathlib import Path

# ── Palette ───────────────────────────────────────────────────────────────────
# Warm ink on cream paper. The two accents (rust + teal) are reserved for
# emphasis lines (e.g. observed vs null, treatment vs control). Everything
# else is a tone of ink/paper.
INK         = '#1A1A1A'   # body ink — near black
INK_SOFT    = '#4A4A4A'   # secondary ink — for axis labels, light grids
RULE        = '#B8B4AC'   # warm grey — gridlines and rules
PAPER       = '#FAFAF7'   # cream — figure background, matches book paper
ACCENT_RUST = '#B8542A'   # rust / sienna — observed series
ACCENT_TEAL = '#2B5F75'   # muted teal — null / comparison series
ACCENT_GOLD = '#B4892A'   # ochre — third series, used sparingly
HIGHLIGHT   = '#E8DDC4'   # light fill — confidence bands

# ── Physical sizing ───────────────────────────────────────────────────────────
MM_PER_INCH = 25.4
COL_WIDTH_MM = 89.0          # body column inside the 125 mm page
FULL_WIDTH_MM = 105.0        # column + marginal number column
PT_PER_INCH = 72.0


def fig_size(width_mm: float = COL_WIDTH_MM, ratio: float = 0.62) -> tuple[float, float]:
    """Return a (width_in, height_in) tuple for a figure of `width_mm` wide
    and `width_mm * ratio` tall. Default ratio ≈ 1/golden, which feels right
    for the narrow book column."""
    w = width_mm / MM_PER_INCH
    return (w, w * ratio)


# ── Fonts ─────────────────────────────────────────────────────────────────────
# Try EB Garamond first (matches the book body), then DejaVu Serif as a
# bundled fallback so the figures still build on systems without EB Garamond.
def _pick_font() -> str:
    for candidate in ('EB Garamond', 'EBGaramond', 'Sabon', 'Garamond',
                      'TeX Gyre Pagella', 'DejaVu Serif'):
        try:
            font_manager.findfont(candidate, fallback_to_default=False)
            return candidate
        except Exception:
            continue
    return 'DejaVu Serif'


SERIF_FAMILY = _pick_font()


# ── rcParams ──────────────────────────────────────────────────────────────────
def apply_style() -> None:
    """Mutate matplotlib rcParams to the FORMLÆRE house style. Idempotent."""
    mpl.rcParams.update({
        # Fonts — same family as the book body. Optical sizes lean larger
        # because the printed figure is small.
        'font.family':         'serif',
        'font.serif':          [SERIF_FAMILY, 'DejaVu Serif'],
        'font.size':           9.5,
        'axes.titlesize':      10.0,
        'axes.labelsize':      9.0,
        'xtick.labelsize':     8.5,
        'ytick.labelsize':     8.5,
        'legend.fontsize':     8.5,
        'figure.titlesize':    10.5,

        # Colours — everything inks to INK / RULE on PAPER
        'text.color':          INK,
        'axes.labelcolor':     INK,
        'axes.edgecolor':      INK,
        'axes.titlecolor':     INK,
        'xtick.color':         INK,
        'ytick.color':         INK,
        'figure.facecolor':    PAPER,
        'axes.facecolor':      PAPER,
        'savefig.facecolor':   PAPER,
        'savefig.edgecolor':   PAPER,
        'patch.edgecolor':     INK,

        # Lines and ticks — thin, dense, ink-on-cream
        'lines.linewidth':     1.1,
        'lines.markersize':    3.5,
        'axes.linewidth':      0.6,
        'xtick.major.width':   0.6,
        'ytick.major.width':   0.6,
        'xtick.major.size':    3.0,
        'ytick.major.size':    3.0,
        'xtick.minor.size':    1.5,
        'ytick.minor.size':    1.5,

        # Grids — off by default; figures opt-in via `ax.grid(...)`
        'axes.grid':           False,
        'grid.color':          RULE,
        'grid.linewidth':      0.4,
        'grid.alpha':          0.6,

        # Layout
        'figure.dpi':          120,
        'savefig.dpi':         320,
        'savefig.bbox':        'tight',
        'savefig.pad_inches':  0.04,

        # No top/right spines — cleaner look in the small column
        'axes.spines.top':     False,
        'axes.spines.right':   False,

        # Legend — borderless, sits inside the axes by default
        'legend.frameon':      False,
        'legend.handlelength': 1.6,
        'legend.handletextpad': 0.5,
        'legend.borderpad':    0.2,
        'legend.labelspacing': 0.3,
    })


# ── Caption helper (below the chart, not above) ──────────────────────────────
def caption_below(fig, title, sub=None, footer=None,
                  x=0.05, y_title=0.13, line_gap=0.035):
    """Place a styled caption block BELOW the chart area.

    The title is rendered in semibold (a touch heavier than normal but not
    full bold), the optional sub line in soft ink, and the footer in
    smaller soft ink. All left-aligned at `x`.
    """
    fig.text(x, y_title, title,
             fontsize=10.0, color=INK, ha='left', va='top',
             weight='semibold', linespacing=1.15)
    if sub:
        fig.text(x, y_title - line_gap, sub,
                 fontsize=7.2, color=INK_SOFT, ha='left', va='top',
                 weight='normal', style='italic', linespacing=1.15)
    if footer:
        fig.text(x, y_title - line_gap * 2 - 0.005, footer,
                 fontsize=6.5, color=INK_SOFT, ha='left', va='top',
                 weight='normal', linespacing=1.15)


# ── Data loading helper ───────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
DATA_CSV = ROOT / 'STOLAR' / 'STOLAR.csv'
MESH_CSV = ROOT / 'analysis' / 'mesh_features.csv'
FIG_DIR  = ROOT / 'analysis' / 'figures'


def load_chairs():
    """Read STOLAR.csv with the right encoding and return a dataframe with
    canonical column names so the analysis code is independent of the
    nynorsk header text in the source CSV."""
    import pandas as pd
    df = pd.read_csv(DATA_CSV, encoding='utf-8', low_memory=False)
    rename = {
        'Frå år':                          'year_from',
        'Til år':                          'year_to',
        'Materialar':                      'material',
        'Stilperiode':                     'style',
        'Nasjonalitet':                    'country',
        'Høgde (cm)':                      'h_cm',
        'Breidde (cm)':                    'w_cm',
        'Djupn (cm)':                      'd_cm',
        'Sphericity (mesh)':               'sphericity',
        'Fill-ratio (mesh)':               'fill_ratio',
        'Inertia-ratio (mesh)':            'inertia_ratio',
        'Kompleksitet (mesh, log10 v/a)':  'complexity',
        'Konveks hylster-volum (m³)':      'hull_vol',
        'Objekt-ID':                       'objekt_id',
        'Namn':                            'name',
        'Datering':                        'datering',
        'Hundreår':                        'century',
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    # Numeric coercion
    for c in ('year_from', 'year_to', 'h_cm', 'w_cm', 'd_cm',
              'sphericity', 'fill_ratio', 'inertia_ratio', 'complexity', 'hull_vol'):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    # Mid-year of each chair (for time-series analyses)
    if 'year_from' in df.columns and 'year_to' in df.columns:
        df['year_mid'] = (df['year_from'] + df['year_to']) / 2
        df.loc[df['year_to'].isna(), 'year_mid'] = df['year_from']
    return df
