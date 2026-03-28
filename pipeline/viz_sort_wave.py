"""
Lag sorterings-bølgje-animasjon av heile stoldatabasen.
Viser alle stolar som små thumbnails i eit rutenett,
og animerer bølgjande overgangar mellom ulike sorteringskriterium.
Output: WebM (VP9) + MP4 (H.264) + GIF (fallback).
"""

import csv
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio

# === CONFIG ===
CSV_PATH = "STOLAR/STOLAR.csv"
BGUW_DIR = "STOLAR/bguw"
OUT_DIR = "results"
CANVAS = 1000             # grid area (px)
N_FRAMES = 250
FPS = 24
HOLD_FRAMES = 20          # frames to pause on each sorted state
TRANSITION_FRAMES = 45    # frames per wave transition
WAVE_SPREAD = 0.5         # wave stagger (0 = all at once, 1 = extreme stagger)
LABEL_H = 40              # label strip height
BG = (240, 240, 240)      # background color


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
                "year": float(row["Frå år"] or 0),
                "height": float(row["Høgde (cm)"] or 0),
                "width": float(row["Breidde (cm)"] or 0),
                "depth": float(row["Djupn (cm)"] or 0),
                "weight": float(row["Estimert vekt (kg)"] or 0),
                "mat": row.get("Materialar", ""),
                "century": row.get("Hundreår", ""),
            })
    return chairs


def sort_orders(chairs):
    n = len(chairs)

    def by(key, zeros_last=True):
        if zeros_last:
            return sorted(range(n), key=lambda i: (
                0 if chairs[i][key] > 0 else 1,
                chairs[i][key] if chairs[i][key] > 0 else 9999, i))
        return sorted(range(n), key=lambda i: (chairs[i][key] or 9999, i))

    # Material count (number of distinct materials)
    mat_counts = []
    for c in chairs:
        mats = [m.strip() for m in c["mat"].split(",") if m.strip()]
        mat_counts.append(len(mats))

    idx_matcount = sorted(range(n), key=lambda i: (mat_counts[i], i))

    # Volume proxy: H * W * D
    volumes = []
    for c in chairs:
        v = c["height"] * c["width"] * c["depth"] if (c["height"] and c["width"] and c["depth"]) else 0
        volumes.append(v)
    idx_volume = sorted(range(n), key=lambda i: (0 if volumes[i] > 0 else 1, volumes[i] or 9e9, i))

    return [
        ("Årstal",           by("year", zeros_last=True)),
        ("Høgde (cm)",       by("height")),
        ("Breidde (cm)",     by("width")),
        ("Volum (H×B×D)",    idx_volume),
        ("Materialtal",      idx_matcount),
        ("Vekt (kg)",        by("weight")),
    ]


def load_thumbs(chairs, sz):
    print(f"  Loading {len(chairs)} thumbnails @ {sz}px ...")
    out = []
    for i, c in enumerate(chairs):
        img = Image.open(c["img"]).convert("RGB").resize((sz, sz), Image.LANCZOS)
        out.append(np.array(img))
        if (i + 1) % 500 == 0:
            print(f"    {i+1}/{len(chairs)}")
    return out


def ease(t):
    """Smooth ease-in-out (Hermite)."""
    return t * t * (3 - 2 * t)


def positions_for(order, cols):
    """Map chair_index -> (row, col) for a given sort order."""
    n = len(order)
    pos = [None] * n
    for grid_i, chair_i in enumerate(order):
        pos[chair_i] = (grid_i // cols, grid_i % cols)
    return pos


def wave_lerp(src, dst, t, spread, cols):
    """Interpolate with left-to-right wave."""
    out = []
    for i in range(len(src)):
        phase = src[i][1] / max(cols - 1, 1)       # 0..1 by source column
        lt = (t - phase * spread) / (1 - spread)
        lt = ease(max(0.0, min(1.0, lt)))
        r = src[i][0] * (1 - lt) + dst[i][0] * lt
        c = src[i][1] * (1 - lt) + dst[i][1] * lt
        out.append((r, c))
    return out


def render(thumbs, positions, cols, rows, sz, canvas_w, label=""):
    h = canvas_w + LABEL_H
    buf = np.full((h, canvas_w, 3), BG, dtype=np.uint8)

    for ci, (r, c) in enumerate(positions):
        y, x = int(round(r * sz)), int(round(c * sz))
        if 0 <= y and y + sz <= canvas_w and 0 <= x and x + sz <= canvas_w:
            buf[y:y+sz, x:x+sz] = thumbs[ci]

    img = Image.fromarray(buf)
    if label:
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 22)
        except OSError:
            font = ImageFont.load_default()
        bb = draw.textbbox((0, 0), label, font=font)
        tx = (canvas_w - (bb[2] - bb[0])) // 2
        ty = canvas_w + (LABEL_H - (bb[3] - bb[1])) // 2
        draw.text((tx, ty), label, fill=(30, 30, 30), font=font)
    return img


def build_frames(thumbs, orders, cols, rows, sz):
    n_sorts = len(orders)
    all_pos = [positions_for(o, cols) for _, o in orders]

    # Build segment plan
    segs = []
    for i in range(n_sorts):
        segs.append(("hold", i))
        segs.append(("wave", i, (i + 1) % n_sorts))

    total_units = n_sorts * HOLD_FRAMES + n_sorts * TRANSITION_FRAMES
    scale = N_FRAMES / total_units

    frames = []
    for seg in segs:
        if len(frames) >= N_FRAMES:
            break
        if seg[0] == "hold":
            nf = max(1, round(HOLD_FRAMES * scale))
            si = seg[1]
            lbl = f"sortert etter {orders[si][0]}"
            for _ in range(nf):
                if len(frames) >= N_FRAMES:
                    break
                frames.append(render(thumbs, all_pos[si], cols, rows, sz, CANVAS, lbl))
        else:
            nf = max(1, round(TRANSITION_FRAMES * scale))
            fi, ti = seg[1], seg[2]
            fn, tn = orders[fi][0], orders[ti][0]
            for f in range(nf):
                if len(frames) >= N_FRAMES:
                    break
                t = f / max(nf - 1, 1)
                pos = wave_lerp(all_pos[fi], all_pos[ti], t, WAVE_SPREAD, cols)
                lbl = f"{fn}  -->  {tn}"
                frames.append(render(thumbs, pos, cols, rows, sz, CANVAS, lbl))

        if len(frames) % 25 < 2:
            print(f"    {len(frames)}/{N_FRAMES} frames")

    return frames[:N_FRAMES]


def save_webm(frames, path, fps):
    """Save as VP9 WebM -- best quality/size ratio."""
    writer = imageio.get_writer(
        path, fps=fps, codec="libvpx-vp9",
        pixelformat="yuv420p",
        output_params=["-crf", "30", "-b:v", "0",    # constant quality
                       "-row-mt", "1"])                # faster encode
    for f in frames:
        a = np.array(f)
        h, w = a.shape[:2]
        writer.append_data(a[:h - h % 2, :w - w % 2])
    writer.close()


def save_mp4(frames, path, fps):
    writer = imageio.get_writer(
        path, fps=fps, codec="libx264",
        pixelformat="yuv420p",
        output_params=["-crf", "23"])
    for f in frames:
        a = np.array(f)
        h, w = a.shape[:2]
        writer.append_data(a[:h - h % 2, :w - w % 2])
    writer.close()


def save_gif(frames, path, fps):
    small = [f.resize((500, 500 + LABEL_H // 2), Image.LANCZOS) for f in frames]
    q = [f.quantize(128, method=Image.Quantize.MEDIANCUT,
                     dither=Image.Dither.NONE) for f in small]
    q[0].save(path, save_all=True, append_images=q[1:],
              duration=int(1000/fps), loop=0, optimize=True)


def main():
    print("=== STOLAR Sort Wave ===")
    chairs = load_data()
    print(f"  {len(chairs)} chairs with bguw images")

    # Grid layout
    cols = math.ceil(math.sqrt(len(chairs)))
    sz = CANVAS // cols
    cols = CANVAS // sz
    rows = cols
    mx = cols * rows
    if len(chairs) > mx:
        print(f"  trimming to {mx} (grid {cols}x{rows})")
        chairs = chairs[:mx]

    print(f"  grid {cols}x{rows}, thumb {sz}px, canvas {CANVAS}px")

    orders = sort_orders(chairs)
    print(f"  {len(orders)} sort criteria: {', '.join(n for n,_ in orders)}")

    thumbs = load_thumbs(chairs, sz)

    print(f"  Rendering {N_FRAMES} frames @ {FPS}fps ...")
    frames = build_frames(thumbs, orders, cols, rows, sz)

    os.makedirs(OUT_DIR, exist_ok=True)

    # WebM (primary)
    webm = os.path.join(OUT_DIR, "sort_wave.webm")
    print(f"  Saving WebM -> {webm}")
    save_webm(frames, webm, FPS)
    print(f"    {os.path.getsize(webm)/1e6:.1f} MB")

    # MP4 (compatibility)
    mp4 = os.path.join(OUT_DIR, "sort_wave.mp4")
    print(f"  Saving MP4 -> {mp4}")
    save_mp4(frames, mp4, FPS)
    print(f"    {os.path.getsize(mp4)/1e6:.1f} MB")

    # GIF (fallback, 500px)
    gif = os.path.join(OUT_DIR, "sort_wave.gif")
    print(f"  Saving GIF -> {gif}")
    save_gif(frames, gif, FPS)
    print(f"    {os.path.getsize(gif)/1e6:.1f} MB")

    print(f"\n  Done! {len(frames)} frames, {len(frames)/FPS:.1f}s duration")


if __name__ == "__main__":
    main()
