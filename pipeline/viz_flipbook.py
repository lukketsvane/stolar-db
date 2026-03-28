"""
Flipbook-animasjon: eitt stolbilete av gangen, sortert etter ulike eigenskapar.
Rask visuell gjennomgang av heile databasen, med infobar som viser verdien.

Bruk:
  python pipeline/viz_flipbook.py              # generer 250 PNG-frames for godkjenning
  python pipeline/viz_flipbook.py --video      # generer WebM-videoar (alle sorteringar)
"""

import csv
import os
import sys
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio

# === CONFIG ===
CSV_PATH = "STOLAR/STOLAR.csv"
BGUW_DIR = "STOLAR/bguw"
FRAME_DIR = "results/flipbook_frames"
VIDEO_DIR = "results/flipbooks"
SIZE = 500                  # square output
BAR_H = 48                 # info bar height
TOTAL_H = SIZE + BAR_H     # canvas height
N_PREVIEW = 250             # frames for preview
FPS = 30                    # frames per second
FRAMES_PER_CHAIR = 1        # how many frames each chair is shown


def load_data():
    chairs = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            obj_id = row["Objekt-ID"].strip()
            img_path = os.path.join(BGUW_DIR, f"{obj_id}_bguw.png")
            if not os.path.exists(img_path):
                continue
            chairs.append({
                "id": obj_id,
                "img": img_path,
                "name": row.get("Namn", "").strip(),
                "year": float(row["Frå år"] or 0),
                "height": float(row["Høgde (cm)"] or 0),
                "width": float(row["Breidde (cm)"] or 0),
                "depth": float(row["Djupn (cm)"] or 0),
                "weight": float(row["Estimert vekt (kg)"] or 0),
                "mat": row.get("Materialar", ""),
                "century": row.get("Hundreår", ""),
                "nation": row.get("Nasjonalitet", ""),
                "style": row.get("Stilperiode", ""),
                "producer": row.get("Produsent", ""),
            })
    return chairs


def get_sort_configs():
    """Each config: (filename, label, sort_key, value_formatter)."""
    return [
        ("aarstal", "Årstal",
         lambda c: (c["year"] or 9999, c["id"]),
         lambda c: f'{int(c["year"])}' if c["year"] else "ukjend"),

        ("hogde", "Høgde (cm)",
         lambda c: (c["height"] or 9999, c["id"]),
         lambda c: f'{c["height"]:.0f} cm' if c["height"] else "ukjend"),

        ("breidde", "Breidde (cm)",
         lambda c: (c["width"] or 9999, c["id"]),
         lambda c: f'{c["width"]:.0f} cm' if c["width"] else "ukjend"),

        ("vekt", "Vekt (kg)",
         lambda c: (0 if c["weight"] > 0 else 1, c["weight"] or 9999, c["id"]),
         lambda c: f'{c["weight"]:.1f} kg' if c["weight"] > 0 else "ukjend"),

        ("volum", "Volum (H×B×D)",
         lambda c: (0 if (c["height"] and c["width"] and c["depth"]) else 1,
                     c["height"] * c["width"] * c["depth"] if (c["height"] and c["width"] and c["depth"]) else 9e9,
                     c["id"]),
         lambda c: f'{c["height"]*c["width"]*c["depth"]/1000:.0f} L'
                   if (c["height"] and c["width"] and c["depth"]) else "ukjend"),

        ("materialtal", "Antal materialar",
         lambda c: (len([m for m in c["mat"].split(",") if m.strip()]), c["id"]),
         lambda c: f'{len([m for m in c["mat"].split(",") if m.strip()])} materialar'),
    ]


def make_frame(img_path, sort_label, value_str, index, total, chair):
    """Create one frame: chair image + info bar at bottom."""
    # Load and resize chair image (keep transparency for white bg)
    img = Image.open(img_path).convert("RGBA")
    img = img.resize((SIZE, SIZE), Image.LANCZOS)

    # Create full canvas with white background
    canvas = Image.new("RGB", (SIZE, TOTAL_H), (255, 255, 255))
    # Composite chair onto white bg (respects alpha)
    white_bg = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 255))
    white_bg.paste(img, mask=img.split()[3])
    canvas.paste(white_bg.convert("RGB"), (0, 0))

    # Draw info bar
    draw = ImageDraw.Draw(canvas)
    # Dark bar background
    draw.rectangle([(0, SIZE), (SIZE, TOTAL_H)], fill=(25, 25, 25))

    try:
        font_main = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        font_main = ImageFont.load_default()
        font_small = font_main

    # Progress bar
    progress = index / max(total - 1, 1)
    bar_y = SIZE + 2
    bar_h = 3
    draw.rectangle([(0, bar_y), (SIZE, bar_y + bar_h)], fill=(60, 60, 60))
    draw.rectangle([(0, bar_y), (int(SIZE * progress), bar_y + bar_h)], fill=(200, 80, 60))

    # Left: sort criterion + value
    y_text = SIZE + 10
    draw.text((12, y_text), f"{sort_label}: {value_str}", fill=(255, 255, 255), font=font_main)

    # Right: counter
    counter = f"{index + 1} / {total}"
    bb = draw.textbbox((0, 0), counter, font=font_main)
    draw.text((SIZE - (bb[2] - bb[0]) - 12, y_text), counter, fill=(160, 160, 160), font=font_main)

    # Second line: chair name + producer
    name = chair.get("name", "")
    producer = chair.get("producer", "")
    subtitle = name
    if producer:
        subtitle += f"  --  {producer}"
    if len(subtitle) > 60:
        subtitle = subtitle[:57] + "..."
    draw.text((12, y_text + 22), subtitle, fill=(120, 120, 120), font=font_small)

    return np.array(canvas)


def render_preview_frames(chairs, sort_cfg, out_dir, n_frames=N_PREVIEW):
    """Render individuelle PNG-frames for godkjenning."""
    filename, label, sort_key, fmt = sort_cfg
    sorted_chairs = sorted(chairs, key=sort_key)
    total_all = len(sorted_chairs)

    # Subsample jamt fordelt
    if total_all <= n_frames:
        selected = sorted_chairs
    else:
        idxs = np.linspace(0, total_all - 1, n_frames, dtype=int)
        selected = [sorted_chairs[i] for i in idxs]

    total = len(selected)
    sub_dir = os.path.join(out_dir, filename)
    os.makedirs(sub_dir, exist_ok=True)

    print(f"  Rendering {total} frames ({label}) -> {sub_dir}/")

    ok = 0
    for i, chair in enumerate(selected):
        frame = make_frame(chair["img"], label, fmt(chair), i, total, chair)
        out_path = os.path.join(sub_dir, f"frame_{i+1:04d}.png")
        Image.fromarray(frame).save(out_path)
        ok += 1
        if (i + 1) % 50 == 0 or (i + 1) == total:
            print(f"    {i+1}/{total}")

    print(f"    {ok} frames lagra i {sub_dir}/")
    return sub_dir


def render_flipbook_video(chairs, sort_cfg, out_dir):
    """Render full WebM-video."""
    filename, label, sort_key, fmt = sort_cfg
    sorted_chairs = sorted(chairs, key=sort_key)
    total = len(sorted_chairs)

    # Pad to 16-divisible for codec
    canvas_w = SIZE
    canvas_h = math.ceil(TOTAL_H / 16) * 16

    webm_path = os.path.join(out_dir, f"flipbook_{filename}.webm")
    print(f"  Rendering {label} -> {webm_path} ({total} chairs @ {FPS}fps)")

    writer = imageio.get_writer(
        webm_path, fps=FPS, codec="libvpx-vp9",
        pixelformat="yuv420p",
        output_params=["-crf", "35", "-b:v", "0", "-row-mt", "1"])

    for i, chair in enumerate(sorted_chairs):
        frame = make_frame(chair["img"], label, fmt(chair), i, total, chair)
        # Pad height to 16-divisible if needed
        h, w = frame.shape[:2]
        if h % 2 != 0 or w % 2 != 0:
            new_h = math.ceil(h / 2) * 2
            new_w = math.ceil(w / 2) * 2
            padded = np.full((new_h, new_w, 3), 255, dtype=np.uint8)
            padded[:h, :w] = frame
            frame = padded
        for _ in range(FRAMES_PER_CHAIR):
            writer.append_data(frame)
        if (i + 1) % 500 == 0:
            print(f"    {i+1}/{total}")

    writer.close()
    sz = os.path.getsize(webm_path) / 1e6
    dur = total * FRAMES_PER_CHAIR / FPS
    print(f"    done: {sz:.1f} MB, {dur:.0f}s")
    return webm_path


def main():
    video_mode = "--video" in sys.argv

    print("=== STOLAR Flipbook ===")
    chairs = load_data()
    print(f"  {len(chairs)} stolar lasta")

    configs = get_sort_configs()

    if video_mode:
        os.makedirs(VIDEO_DIR, exist_ok=True)
        paths = []
        for cfg in configs:
            p = render_flipbook_video(chairs, cfg, VIDEO_DIR)
            paths.append(p)
        print(f"\n  Ferdig! {len(paths)} videoar:")
        for p in paths:
            print(f"    {p}")
    else:
        # Preview: berre årstal-sortering, 250 frames
        os.makedirs(FRAME_DIR, exist_ok=True)
        cfg = configs[0]  # årstal
        render_preview_frames(chairs, cfg, FRAME_DIR, N_PREVIEW)


if __name__ == "__main__":
    main()
