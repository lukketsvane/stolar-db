"""Generate FORMLÆRE model architecture diagrams — multiple proposals.

Three variants:
  A) Pipeline (TransIP-inspired vertical flow)
  B) Care-centric (Levin's care=intelligence at centre)
  C) Trinity convergence (three pillars → form)
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from style import (apply_style, fig_size, FIG_DIR,
                    INK, INK_SOFT, RULE, PAPER,
                    ACCENT_RUST, ACCENT_TEAL, ACCENT_GOLD, HIGHLIGHT)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

apply_style()

# ── Colours for the three pillars ────────────────────────────────────────────
SG_COL   = ACCENT_TEAL    # Shape Grammar / syntax
CK_COL   = ACCENT_RUST    # CK Theory / logic
TAME_COL = ACCENT_GOLD    # TAME / dynamics
FORM_COL = INK             # output

def _box(ax, xy, w, h, text, fc='white', ec=INK, lw=0.8, fontsize=8,
         fontweight='normal', alpha=0.15, text_color=None):
    """Draw a rounded box with centred text."""
    x, y = xy
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.02",
                          facecolor=fc, edgecolor=ec,
                          linewidth=lw, alpha=1.0, zorder=2)
    ax.add_patch(box)
    # fill
    fill = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle="round,pad=0.02",
                           facecolor=fc, edgecolor='none',
                           linewidth=0, alpha=alpha, zorder=1)
    ax.add_patch(fill)
    tc = text_color or INK
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight=fontweight, color=tc, zorder=3)

def _arrow(ax, xy1, xy2, color=INK, lw=0.8, style='->', shrink=4):
    """Simple arrow between two points."""
    ax.annotate('', xy=xy2, xytext=xy1,
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=lw, shrinkA=shrink, shrinkB=shrink),
                zorder=4)

# ═══════════════════════════════════════════════════════════════════════════════
# VARIANT A — Pipeline (TransIP-style vertical flow)
# ═══════════════════════════════════════════════════════════════════════════════
def variant_a():
    fig, ax = plt.subplots(figsize=fig_size(105, 1.4))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis('off')

    # Title
    ax.text(0.30, 0.97, r'$f_\theta : \mathcal{M} \to \mathbb{R}^d$',
            fontsize=9, color=INK_SOFT, style='italic')

    # ── Left column: the pipeline ──
    # Morphospace
    _box(ax, (0.30, 0.88), 0.42, 0.08,
         'Morforom  M(c)\nFormer  x,  Klasse  c,  Objekt', fc=ACCENT_TEAL,
         alpha=0.12, fontsize=7.5)
    ax.text(0.30, 0.83, 'Shape Algebra  S = (∪, −, Trans(Eⁿ))',
            ha='center', fontsize=6.5, color=ACCENT_TEAL, style='italic')

    # Selection pressures
    _arrow(ax, (0.30, 0.80), (0.30, 0.74), color=INK_SOFT)
    _box(ax, (0.30, 0.70), 0.42, 0.06,
         'Seleksjonstrykk  p₁ … pₙ', fc=ACCENT_RUST,
         alpha=0.12, fontsize=7.5)

    # Fitness landscape
    _arrow(ax, (0.30, 0.66), (0.30, 0.60), color=INK_SOFT)
    _box(ax, (0.30, 0.56), 0.42, 0.06,
         'Tilpassingslandskap  L(c,t) = Σ wᵢ(t)·pᵢ', fc=ACCENT_RUST,
         alpha=0.08, fontsize=7)

    # Agent
    _arrow(ax, (0.30, 0.52), (0.30, 0.45), color=INK_SOFT)
    _box(ax, (0.30, 0.40), 0.42, 0.10,
         'Agent  A = (g, d, δ)\nLyskjegle  C(A) ⊆ M\nGrammatikk  SG = (S, R, ω)',
         fc=ACCENT_GOLD, alpha=0.12, fontsize=7.5)

    # CK operators
    _arrow(ax, (0.30, 0.34), (0.30, 0.27), color=INK_SOFT)
    _box(ax, (0.30, 0.22), 0.42, 0.08,
         'C→C  partisjon  |  C→K  realisering\nK→C  konseptualisering',
         fc=ACCENT_RUST, alpha=0.10, fontsize=7)
    ax.text(0.30, 0.16, 'CK-ekspansjon (Hatchuel & Weil)',
            ha='center', fontsize=6.5, color=ACCENT_RUST, style='italic')

    # Output: Form
    _arrow(ax, (0.30, 0.14), (0.30, 0.08), color=INK)
    _box(ax, (0.30, 0.04), 0.30, 0.06,
         'Form  x  ∈  M(c)', fc=INK, alpha=0.08,
         fontsize=8, fontweight='bold', text_color=INK)

    # ── Right column: Multi-scale competency ──
    ax.text(0.75, 0.93, 'Multiskala-kompetanse', ha='center',
            fontsize=8, fontweight='bold', color=ACCENT_GOLD)
    ax.text(0.75, 0.90, '(TAME — Levin 2022)', ha='center',
            fontsize=6.5, color=ACCENT_GOLD, style='italic')

    scales = [
        (0.85, 'Marknad / kultur'),
        (0.78, 'Handverkar / designar'),
        (0.71, 'Verktøy / reiskapskode'),
        (0.64, 'Materiale / substrat'),
        (0.57, 'Celle / molekyl'),
    ]
    for i, (y, label) in enumerate(scales):
        w = 0.30 - i * 0.03
        _box(ax, (0.75, y), w, 0.05, label,
             fc=ACCENT_GOLD, alpha=0.06 + i*0.03, fontsize=6.5)
        if i < len(scales) - 1:
            _arrow(ax, (0.75, y - 0.03), (0.75, y - 0.05),
                   color=ACCENT_GOLD, lw=0.6)

    # Cone shape suggestion
    ax.plot([0.60, 0.75, 0.90], [0.52, 0.50, 0.52], color=ACCENT_GOLD,
            lw=0.5, ls='--')
    ax.text(0.75, 0.48, 'Lyskjegle → Omsorg → Intelligens',
            ha='center', fontsize=6.5, color=ACCENT_GOLD, style='italic')

    # Care = intelligence box
    _box(ax, (0.75, 0.22), 0.30, 0.08,
         'Omsorg = dim C(A)\nIntelligens = Omsorg si form',
         fc=ACCENT_GOLD, alpha=0.15, fontsize=7.5, fontweight='bold')

    # Connecting arrow from agent to multiscale
    _arrow(ax, (0.52, 0.40), (0.58, 0.71), color=INK_SOFT, lw=0.5,
           style='->', shrink=8)

    fig.savefig(FIG_DIR / 'model-A-pipeline.pdf', bbox_inches='tight', dpi=320)
    fig.savefig(FIG_DIR / 'model-A-pipeline.png', bbox_inches='tight', dpi=320)
    plt.close(fig)
    print('  A  pipeline saved')


# ═══════════════════════════════════════════════════════════════════════════════
# VARIANT B — Care-centric (intelligence = care at centre)
# ═══════════════════════════════════════════════════════════════════════════════
def variant_b():
    fig, ax = plt.subplots(figsize=fig_size(105, 1.0))
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.0, 1.0)
    ax.set_aspect('equal')
    ax.axis('off')

    # Concentric rings
    rings = [
        (0.22, ACCENT_GOLD, 0.20, 'OMSORG\n= dim C(A)', 8, 'bold'),
        (0.45, ACCENT_TEAL, 0.08, '', 7, 'normal'),
        (0.68, ACCENT_RUST, 0.06, '', 7, 'normal'),
        (0.90, INK_SOFT,    0.04, '', 7, 'normal'),
    ]
    for r, col, alpha, label, fs, fw in rings:
        circle = plt.Circle((0, 0), r, facecolor=col, edgecolor=col,
                             alpha=alpha, lw=0.8, zorder=1)
        ax.add_patch(circle)
        if label:
            ax.text(0, 0, label, ha='center', va='center',
                    fontsize=fs, fontweight=fw, color=ACCENT_GOLD, zorder=5)

    # Ring labels (curved would be ideal but straight is clear)
    ax.text(0, 0.35, 'Agent  A = (g, d, δ)', ha='center',
            fontsize=7, color=ACCENT_TEAL, fontweight='bold')
    ax.text(0, 0.57, 'Lyskjegle  C(A)  ·  Grammatikk  SG', ha='center',
            fontsize=6.5, color=ACCENT_TEAL)
    ax.text(0, 0.77, 'Landskap  L(c,t) = Σ wᵢ·pᵢ', ha='center',
            fontsize=6.5, color=ACCENT_RUST)
    ax.text(0, 0.95, 'Morforom  M(c)  =  Shape Algebra', ha='center',
            fontsize=6.5, color=INK_SOFT)

    # Three pillars as external labels
    pillar_data = [
        (-1.05, 0.3, 'SYNTAKS\nShape Grammar\n(Stiny)', SG_COL),
        ( 1.05, 0.3, 'LOGIKK\nCK-teori\n(Hatchuel & Weil)', CK_COL),
        ( 0.0, -0.85, 'DYNAMIKK\nMultiskala-kompetanse\n(Levin)', TAME_COL),
    ]
    for x, y, txt, col in pillar_data:
        ax.text(x, y, txt, ha='center', va='center',
                fontsize=7, color=col, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=col,
                          edgecolor=col, alpha=0.10))
        # arrow toward centre
        dx, dy = -x * 0.4, -y * 0.4
        _arrow(ax, (x + dx*0.3, y + dy*0.3), (x + dx, y + dy),
               color=col, lw=0.7, shrink=6)

    # CK operators on the right ring
    ops = [
        (0.75, -0.3, 'C→C', CK_COL),
        (0.85, -0.1, 'C→K', CK_COL),
        (0.75,  0.1, 'K→C', CK_COL),
    ]
    for x, y, label, col in ops:
        ax.text(x, y, label, ha='center', fontsize=6, color=col,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor=col, alpha=0.8, lw=0.5))

    # Five light-cone operations on the left ring
    lc_ops = [
        (-0.80, -0.35, 'ekspansjon'),
        (-0.90, -0.15, 'refraksjon'),
        (-0.85,  0.05, 'translasjon'),
        (-0.72, -0.50, 'kollaps'),
        (-0.60, -0.15, 'spissing'),
    ]
    for x, y, label in lc_ops:
        ax.text(x, y, label, ha='center', fontsize=5.5, color=SG_COL,
                style='italic')

    # Bottom: the identity
    ax.text(0, -0.68, 'Intelligens  =  Omsorg si form',
            ha='center', fontsize=8.5, fontweight='bold', color=INK,
            style='italic')
    ax.text(0, -0.75, '(prop. 5.61)', ha='center', fontsize=6, color=INK_SOFT)

    fig.savefig(FIG_DIR / 'model-B-care.pdf', bbox_inches='tight', dpi=320)
    fig.savefig(FIG_DIR / 'model-B-care.png', bbox_inches='tight', dpi=320)
    plt.close(fig)
    print('  B  care-centric saved')


# ═══════════════════════════════════════════════════════════════════════════════
# VARIANT C — Trinity convergence with process cycle
# ═══════════════════════════════════════════════════════════════════════════════
def variant_c():
    fig, ax = plt.subplots(figsize=fig_size(105, 1.1))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis('off')

    # Title
    ax.text(0.50, 0.97, 'FORMLÆRE',
            ha='center', fontsize=11, fontweight='bold', color=INK,
            fontfamily='serif')
    ax.text(0.50, 0.93, 'Substrat-uavhengig rammeverk for korleis form oppstår',
            ha='center', fontsize=7, color=INK_SOFT, style='italic')

    # ── Three pillars at top ──
    pillars = [
        (0.17, 0.82, 'SYNTAKS', 'Formalgebra\nFormgrammatikk\n(Stiny 1972, 2006)', SG_COL),
        (0.50, 0.82, 'LOGIKK', 'Konsept–Kunnskap\nC↔K-ekspansjon\n(Hatchuel & Weil 2003)', CK_COL),
        (0.83, 0.82, 'DYNAMIKK', 'Multiskala-\nkompetanse\n(Levin 2022)', TAME_COL),
    ]
    for x, y, title, body, col in pillars:
        _box(ax, (x, y), 0.28, 0.12, f'{title}\n{body}',
             fc=col, alpha=0.12, fontsize=6.5, ec=col)

    # ── Central process cycle ──
    cycle_y = 0.50
    cycle_nodes = [
        (0.15, cycle_y, 'Morforom\nM(c) ⊆ Eⁿ', SG_COL),
        (0.38, cycle_y, 'Landskap\nL(c,t) = Σwᵢpᵢ', CK_COL),
        (0.62, cycle_y, 'Agent\nA = (g, d, δ)', TAME_COL),
        (0.85, cycle_y, 'Grammatikk\nSG = (S, R, ω)', SG_COL),
    ]
    for x, y, label, col in cycle_nodes:
        _box(ax, (x, y), 0.22, 0.10, label,
             fc=col, alpha=0.10, fontsize=7, ec=col)

    # Arrows between cycle nodes
    for i in range(len(cycle_nodes) - 1):
        x1 = cycle_nodes[i][0] + 0.12
        x2 = cycle_nodes[i+1][0] - 0.12
        _arrow(ax, (x1, cycle_y), (x2, cycle_y), color=INK_SOFT, lw=0.7)

    # Return arrow (grammar → morphospace, bottom arc)
    ax.annotate('', xy=(0.15, cycle_y - 0.08), xytext=(0.85, cycle_y - 0.08),
                arrowprops=dict(arrowstyle='->', color=INK_SOFT, lw=0.7,
                                connectionstyle='arc3,rad=0.3',
                                shrinkA=8, shrinkB=8))
    ax.text(0.50, 0.36, 'C→K realisering  →  ny form  →  nytt K',
            ha='center', fontsize=6, color=CK_COL, style='italic')

    # ── Pillar arrows down to cycle ──
    _arrow(ax, (0.17, 0.75), (0.15, 0.56), color=SG_COL, lw=0.5, shrink=6)
    _arrow(ax, (0.50, 0.75), (0.38, 0.56), color=CK_COL, lw=0.5, shrink=6)
    _arrow(ax, (0.83, 0.75), (0.62, 0.56), color=TAME_COL, lw=0.5, shrink=6)
    # grammar also from syntax
    _arrow(ax, (0.17, 0.75), (0.85, 0.56), color=SG_COL, lw=0.4, shrink=8,
           style='->')

    # ── Bottom: Care identity ──
    # Light cone expanding
    _box(ax, (0.35, 0.18), 0.50, 0.10,
         'Lyskjegle  C(A)  →  Omsorg  =  dim C(A)',
         fc=TAME_COL, alpha=0.10, fontsize=7.5, ec=TAME_COL)

    _box(ax, (0.35, 0.06), 0.50, 0.06,
         'Intelligens  =  Omsorg si form   (5.61)',
         fc=INK, alpha=0.08, fontsize=8, fontweight='bold', ec=INK)

    _arrow(ax, (0.62, 0.44), (0.35, 0.24), color=TAME_COL, lw=0.5, shrink=6)
    _arrow(ax, (0.35, 0.12), (0.35, 0.10), color=INK, lw=0.6, shrink=2)

    # ── Right side: empirical grounding ──
    _box(ax, (0.85, 0.18), 0.22, 0.18,
         'Empirisk test\nn ≈ 2 300 stolar\n1280–2024\n\n21 appendiks-\nfigurar\n84/84 subset\nheld',
         fc=PAPER, alpha=1.0, fontsize=5.5, ec=RULE)

    fig.savefig(FIG_DIR / 'model-C-trinity.pdf', bbox_inches='tight', dpi=320)
    fig.savefig(FIG_DIR / 'model-C-trinity.png', bbox_inches='tight', dpi=320)
    plt.close(fig)
    print('  C  trinity saved')


if __name__ == '__main__':
    print('Generating model diagrams...')
    variant_a()
    variant_b()
    variant_c()
    print('Done. Check analysis/figures/')
