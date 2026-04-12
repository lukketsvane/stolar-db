"""Generate horizontal chair-info stacks for ALL chairs in the corpus.

Each stack: chair image (bguw) | info table
Table fields: Namn, År, Stil, Materiale, Kompleksitet, Fyllingsgrad, Tregleiksratio, Volum (hylster)
Drops: Sfærisitet, Mesh Vertiser (per user request)
Adds: Volum (konveks hylster)

Output: research/figures/stolar-nn/stack_{obj_id}.jpg
Also writes vol_hull back into STOLAR.csv if missing.
"""
from __future__ import annotations

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ── Paths ────────────────────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parents[3]
STOLAR_CSV = REPO / 'STOLAR' / 'STOLAR.csv'
MESH_CSV = REPO / 'research' / 'analysis' / 'mesh_features.csv'
BGUW_DIR = REPO / 'STOLAR' / 'bguw'
OUT_DIR = REPO / 'research' / 'figures' / 'stolar-nn'

# ── Style constants (match FORMLÆRE book) ────────────────────────────────────
INK = '#1A1A1A'
INK_SOFT = '#4A4A4A'
RULE = '#B8B4AC'
PAPER = '#FAFAF7'
PAPER_RGB = (250, 250, 247)


def render_table_image(header_label, header_value, body_rows):
    """Render info table as PIL Image. Fixed 9 rows, clean rules.

    header_label / header_value: bold top row (e.g. "Namn" / "Balans Gravity")
    body_rows: list of [label, value] pairs for the body
    """
    # Match the original create_stack style: tight rows, large text
    # Figure sized to content, not to a pixel grid
    n_body = len(body_rows)
    row_h_in = 0.32          # inches per body row
    header_block = 0.38      # inches for header (rule + text + rule) — tight
    pad = 0.15               # top/bottom padding
    fig_w_in = 4.2
    fig_h_in = pad + header_block + n_body * row_h_in + pad

    DPI = 200
    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in), dpi=DPI)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    lx0, lx1 = 0.04, 0.96
    col1 = 0.06
    col2 = 0.48

    # Vertical positions in axes coords (0=bottom, 1=top)
    top_rule = 1.0 - pad / fig_h_in
    header_text = top_rule - 0.5 * header_block / fig_h_in
    header_rule = top_rule - header_block / fig_h_in
    bot_rule = pad / fig_h_in

    body_zone = header_rule - bot_rule
    step = body_zone / max(n_body, 1)
    body_y0 = header_rule - 0.5 * step   # center first row in its slot

    # Rules
    for ry in [top_rule, header_rule, bot_rule]:
        ax.axhline(ry, xmin=lx0, xmax=lx1, color=RULE, linewidth=0.7)

    # Header
    ax.text(col1, header_text, header_label,
            fontsize=13, fontweight='bold', color=INK, va='center',
            transform=ax.transAxes)
    ax.text(col2, header_text, header_value,
            fontsize=13, fontweight='bold', color=INK, va='center',
            transform=ax.transAxes)

    # Body
    for i, (label, value) in enumerate(body_rows):
        y = body_y0 - i * step
        ax.text(col1, y, label, fontsize=11.5, color=INK_SOFT, va='center',
                transform=ax.transAxes)
        ax.text(col2, y, value, fontsize=11.5, color=INK_SOFT, va='center',
                transform=ax.transAxes)

    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(h, w, 4)
    img = Image.fromarray(buf[:, :, :3])
    plt.close(fig)
    return img


# Fixed output dimensions for all stacks
STACK_W = 1600   # total width in px
STACK_H = 700    # total height in px
CHAIR_W = 700    # left panel for chair image
TABLE_W = STACK_W - CHAIR_W  # right panel for table


def create_stack(obj_id, meta, mesh_row, bguw_dir, output_path):
    """Create one horizontal stack image with fixed dimensions."""
    bguw_path = bguw_dir / f"{obj_id}_bguw.png"
    if not bguw_path.exists():
        return False

    # Header: "Namn" + the chair's actual name
    namn = str(meta.get('Namn', ''))[:35]
    header_value = namn if namn and namn != 'nan' else obj_id

    # Body rows (always 8 for consistent layout)
    body = []
    year = meta.get('Frå år')
    body.append(["År", str(int(year)) if pd.notna(year) else "—"])

    stil = str(meta.get('Stilperiode', ''))
    body.append(["Stil", stil[:30] if stil and stil != 'nan' else "—"])

    mat = str(meta.get('Materialar', ''))
    body.append(["Materiale", mat[:35] if mat and mat != 'nan' else "—"])

    if mesh_row is not None:
        compl = mesh_row.get('complexity')
        body.append(["Kompleksitet", f"{compl:.2f}" if pd.notna(compl) else "—"])

        fr = mesh_row.get('fill_ratio')
        body.append(["Fyllingsgrad", f"{fr:.2f}" if pd.notna(fr) else "—"])

        ir = mesh_row.get('inertia_ratio')
        body.append(["Tregleiksratio", f"{ir:.2f}" if pd.notna(ir) else "—"])

        vh = mesh_row.get('vol_hull')
        if pd.notna(vh) and vh > 0:
            vstr = f"{vh:.4f} m\u00b3" if vh < 0.01 else f"{vh:.3f} m\u00b3"
            body.append(["Volum (hylster)", vstr])
        else:
            body.append(["Volum (hylster)", "—"])
    else:
        for label in ["Kompleksitet", "Fyllingsgrad", "Tregleiksratio", "Volum (hylster)"]:
            body.append([label, "—"])

    # Render table at fixed 900x700 px
    table_img = render_table_image("Namn", header_value, body)
    table_img = table_img.resize((TABLE_W, STACK_H), Image.Resampling.LANCZOS)

    # Load and fit chair image into fixed left panel
    chair_img = Image.open(bguw_path).convert('RGB')
    # Scale to fit within CHAIR_W x STACK_H, centered, with PAPER background
    scale = min(CHAIR_W / chair_img.width, STACK_H / chair_img.height) * 0.88
    new_w = int(chair_img.width * scale)
    new_h = int(chair_img.height * scale)
    chair_img = chair_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    chair_panel = Image.new('RGB', (CHAIR_W, STACK_H), PAPER_RGB)
    x_off = (CHAIR_W - new_w) // 2
    y_off = (STACK_H - new_h) // 2
    chair_panel.paste(chair_img, (x_off, y_off))

    # Combine
    combined = Image.new('RGB', (STACK_W, STACK_H), PAPER_RGB)
    combined.paste(chair_panel, (0, 0))
    combined.paste(table_img, (CHAIR_W, 0))

    combined.save(str(output_path))
    return True


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    df = pd.read_csv(STOLAR_CSV, encoding='utf-8', low_memory=False)
    df_mesh = pd.read_csv(MESH_CSV, encoding='utf-8')

    # Index mesh by objekt_id
    mesh_dict = {}
    for _, row in df_mesh.iterrows():
        mesh_dict[row['objekt_id']] = row

    # Also update STOLAR.csv with vol_hull if not present
    if 'Konveks hylster-volum (m\u00b3)' not in df.columns:
        df['Konveks hylster-volum (m\u00b3)'] = np.nan

    vol_updated = 0
    for idx, row in df.iterrows():
        oid = row['Objekt-ID']
        if oid in mesh_dict:
            mrow = mesh_dict[oid]
            vh = mrow.get('vol_hull')
            if pd.notna(vh) and pd.isna(row.get('Konveks hylster-volum (m\u00b3)')):
                df.at[idx, 'Konveks hylster-volum (m\u00b3)'] = vh
                vol_updated += 1

    if vol_updated > 0:
        print(f"Writing {vol_updated} new vol_hull values to STOLAR.csv...")
        df.to_csv(STOLAR_CSV, index=False, encoding='utf-8')

    # Generate stacks
    total = len(df)
    done = 0
    skipped = 0

    for idx, row in df.iterrows():
        oid = row['Objekt-ID']
        out_path = OUT_DIR / f"objekt_{oid}_nn.png"

        if out_path.exists():
            done += 1
            continue

        mesh_row = mesh_dict.get(oid)
        meta = row.to_dict()

        ok = create_stack(oid, meta, mesh_row, BGUW_DIR, out_path)
        if ok:
            done += 1
        else:
            skipped += 1

        if (done + skipped) % 200 == 0:
            print(f"  {done + skipped}/{total} processed ({done} ok, {skipped} skipped)")

    print(f"\nDone: {done} stacks created, {skipped} skipped (no bguw image)")
    print(f"Output: {OUT_DIR}")


if __name__ == '__main__':
    main()
