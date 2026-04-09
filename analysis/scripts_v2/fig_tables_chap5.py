"""Render the four chapter-5 tables (5.23, 5.44, 5.45, 5.62) as flat
image files, so they survive the docx export pipeline cleanly.

Each table is laid out as a matplotlib figure with manual text + rule
positioning (avoids ax.table()'s rigid cell sizing). Output is saved
both as .pdf (for the LaTeX build) and .png (for the docx export).
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from style import apply_style, FIG_DIR, INK, INK_SOFT, RULE, PAPER


def render_table(rows, col_xs, filename, fig_w=3.5, row_h=0.30,
                 header_pad=0.10, font_size=12.5, header_size=13.0):
    """Draw a simple text table.

    rows[0]    is the header row.
    col_xs     is a list of x-positions (axes coordinates) for each column,
               left-aligned at that x.

    Font sizes are deliberately large + bold so the table stays legible
    after the figure is scaled down to the 89 mm body column. Headers are
    bold; body rows are semibold.
    """
    apply_style()

    n_rows = len(rows)
    fig_h = header_pad + row_h * n_rows + 0.10
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    # Top rule, header rule, bottom rule
    top_y = 1.0 - 0.04
    header_baseline = top_y - 0.11
    header_rule_y = header_baseline - 0.07
    body_top = header_rule_y - 0.05
    bottom_y = 0.04

    # Compute body row spacing
    n_body = n_rows - 1
    body_span = body_top - bottom_y
    if n_body > 0:
        row_step = body_span / n_body
    else:
        row_step = 0.0

    # Top rule
    ax.add_line(Line2D([0.0, 1.0], [top_y, top_y], color=INK, lw=1.2))
    # Header rule
    ax.add_line(Line2D([0.0, 1.0], [header_rule_y, header_rule_y],
                       color=INK, lw=0.7))
    # Bottom rule
    ax.add_line(Line2D([0.0, 1.0], [bottom_y - 0.01, bottom_y - 0.01],
                       color=INK, lw=1.2))

    # Header row
    for x, cell in zip(col_xs, rows[0]):
        ax.text(x, header_baseline, cell,
                fontsize=header_size, color=INK, ha='left', va='center',
                weight='bold')

    # Body rows
    for i, row in enumerate(rows[1:]):
        y = body_top - row_step * (i + 0.5)
        for x, cell in zip(col_xs, row):
            ax.text(x, y, cell,
                    fontsize=font_size, color=INK,
                    ha='left', va='center', weight='semibold')

    fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
    pdf = FIG_DIR / f'{filename}.pdf'
    png = FIG_DIR / f'{filename}.png'
    fig.savefig(pdf)
    fig.savefig(png)
    plt.close(fig)
    print(f'wrote {pdf.name}, {png.name}')


def main():
    FIG_DIR.mkdir(exist_ok=True)

    # NB: long cells are wrapped onto two lines with explicit \n so the
    # bigger bold font still fits inside the body column. Row heights are
    # generous enough that wrapped rows do not collide.

    # ── 5.23  Agentar (4 cols) ────────────────────────────────────────────────
    rows_523 = [
        ['Agent', 'dim(C)', 'Latens \u03c4', 'L\u00e6ringsorden \u03ba'],
        ['Materialet\n(tre, st\u00e5l)', '0\n(passiv)', '\u221e', '0\n(ingen)'],
        ['Termostat', '1', 'minimal', '0'],
        ['CNC-maskin', '3', 'l\u00e5g', '0'],
        ['Handverkar', r'$\gg$ 1', 'variabel', '2\n(regelendring)'],
        ['Designtradisjon', r'$\gg$ 1', '\u00e5r\u2013ti\u00e5r',
         '3\n(rom-restruktur.)'],
        ['Diffusjons-\nmodell', 'n\n(latent rom)', 'l\u00e5g',
         '1\n(param.-\noppdatering)'],
    ]
    render_table(
        rows_523,
        col_xs=[0.00, 0.32, 0.50, 0.68],
        filename='fig-5.23-agentar',
        fig_w=5.6,
        row_h=0.56,
    )

    # ── 5.44  Lyskjegleoperasjonar (3 cols) ───────────────────────────────────
    rows_544 = [
        ['Operasjon', 'Verknad', 'D\u00f8me'],
        ['Utviding', 'Lyskjegla dekkjer\nnye regionar',
         'Handverkaren oppdagar\neit nytt materiale'],
        ['Oppl\u00f8ysings-\nauke', 'Fleire delformer vert\nsynlege i same region',
         'Snikkaren l\u00e6rer \u00e5 sj\u00e5\nnye saman\u00adf\u00f8yingar'],
        ['R\u00f8rsle', 'Lyskjegla flyttar seg\ntil ukjent territorium',
         'Designaren g\u00e5r fr\u00e5\nm\u00f8bel til arkitektur'],
        ['Kollaps', 'Lyskjegla krympar til\n\u00e9in realisert posisjon',
         'Avgjersle: dette vert\nden endelege forma'],
        ['Skjerping', 'Same dekning,\nh\u00f8gare presisjon',
         'Meistaren foredlar\nteknikken sin'],
    ]
    render_table(
        rows_544,
        col_xs=[0.00, 0.22, 0.60],
        filename='fig-5.44-lyskjegle',
        fig_w=5.6,
        row_h=0.62,
    )

    # ── 5.45  C-K-operatorar (3 cols) ─────────────────────────────────────────
    rows_545 = [
        ['C-K-operator', 'Retning', 'Lyskjegle-\noperasjon'],
        ['C \u2192 C\n(konseptekspansjon)', 'Innanfor C', 'Utviding'],
        ['C \u2192 K\n(konjektur \u2192 kunnskap)', 'Fr\u00e5 C til K', 'Kollaps'],
        ['K \u2192 C\n(kunnskap \u2192 konjektur)', 'Fr\u00e5 K til C', 'R\u00f8rsle'],
        ['K \u2192 K\n(kunnskapsutdjuping)', 'Innanfor K',
         'Oppl\u00f8ysings-\nauke'],
    ]
    render_table(
        rows_545,
        col_xs=[0.00, 0.52, 0.74],
        filename='fig-5.45-ck',
        fig_w=4.6,
        row_h=0.56,
    )

    # ── 5.62  Grammatikkoperasjonar (3 cols) ──────────────────────────────────
    rows_562 = [
        ['Operasjon', 'Regel', 'Verknad'],
        ['Addisjon', 'a \u2192 a + b',
         'Legg til ein ny del;\nbehald den opphavlege'],
        ['Subtraksjon', 'a \u2192 a \u2212 b', 'Fjern ein del'],
        ['Deling', r'a $\rightarrow$ $a_1 + a_2$',
         'Del forma;\nbehald omrisset'],
        ['Modifikasjon', 'a \u2192 a\u2032',
         'Endre proporsjon,\norientering, retning'],
        ['Substitusjon', 'a \u2192 b',
         'Erstatt heile forma\nmed ei anna'],
    ]
    render_table(
        rows_562,
        col_xs=[0.00, 0.28, 0.50],
        filename='fig-5.62-grammatikk',
        fig_w=4.6,
        row_h=0.56,
    )


if __name__ == '__main__':
    main()
