"""
Smooth flipbook: sorterer stolar etter visuell likskap,
slik at kvar stol glir saumlaust over i neste.

1. Trekk ut visuelle eigenskapar (nedskalert LAB-bilete + fargehistogram)
2. Greedy nearest-neighbor-kjede (TSP-approx) i feature-space
3. Render flipbook WebM i den rekkefølgja

Bruk:
  python pipeline/viz_smooth_flipbook.py
"""

import csv
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.distance import cdist
import imageio

# === CONFIG ===
CSV_PATH = "STOLAR/STOLAR.csv"
BGUW_DIR = "STOLAR/bguw"
OUT_DIR = "results/flipbooks"
SIZE = 512
BAR_H = 48
TOTAL_H = SIZE + BAR_H  # 560
FPS = 30
FEAT_SIZE = 32           # downscale to 32x32 for feature extraction
N_HIST_BINS = 16         # color histogram bins per channel


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
                "producer": row.get("Produsent", ""),
                "mat": row.get("Materialar", ""),
            })
    return chairs


def extract_features(chairs):
    """
    Extract visual feature vector for each chair.
    Combines:
      - Downscaled LAB-space pixels (shape + color layout)
      - Color histogram in LAB space (overall color distribution)
      - Edge density (shape complexity)
    """
    print(f"  Extracting features from {len(chairs)} images...")
    features = []

    for i, chair in enumerate(chairs):
        img = Image.open(chair["img"]).convert("RGB")

        # 1) Downscaled pixels in LAB-ish space (use YCbCr as fast LAB proxy)
        small = img.resize((FEAT_SIZE, FEAT_SIZE), Image.LANCZOS)
        arr = np.array(small, dtype=np.float32) / 255.0
        pixels_flat = arr.reshape(-1)  # 32*32*3 = 3072

        # 2) Color histogram (captures overall palette)
        hist_r = np.histogram(arr[:,:,0], bins=N_HIST_BINS, range=(0,1))[0].astype(np.float32)
        hist_g = np.histogram(arr[:,:,1], bins=N_HIST_BINS, range=(0,1))[0].astype(np.float32)
        hist_b = np.histogram(arr[:,:,2], bins=N_HIST_BINS, range=(0,1))[0].astype(np.float32)
        hist = np.concatenate([hist_r, hist_g, hist_b])
        hist = hist / (hist.sum() + 1e-8)  # normalize

        # 3) Edge density (Sobel-like via simple diff)
        gray = arr.mean(axis=2)
        dx = np.abs(np.diff(gray, axis=1)).mean()
        dy = np.abs(np.diff(gray, axis=0)).mean()
        edge = np.array([dx, dy], dtype=np.float32)

        # 4) Background ratio (how much is near-white)
        brightness = arr.mean(axis=2)
        bg_ratio = np.array([(brightness > 0.92).mean()], dtype=np.float32)

        # Combine with weights
        feat = np.concatenate([
            pixels_flat * 2.0,    # spatial layout (dominant)
            hist * 5.0,           # color palette
            edge * 10.0,          # shape complexity
            bg_ratio * 3.0,       # object size proxy
        ])
        features.append(feat)

        if (i + 1) % 500 == 0:
            print(f"    {i+1}/{len(chairs)}")

    features = np.array(features)
    print(f"  Feature shape: {features.shape}")
    return features


def greedy_nn_order(features):
    """
    Greedy nearest-neighbor TSP approximation.
    Start from the chair closest to the mean, then always jump to
    the closest unvisited neighbor.
    """
    n = features.shape[0]
    print(f"  Computing nearest-neighbor chain for {n} items...")

    # Start from the item closest to the centroid
    centroid = features.mean(axis=0)
    dists_to_center = np.linalg.norm(features - centroid, axis=1)
    start = np.argmin(dists_to_center)

    visited = np.zeros(n, dtype=bool)
    order = [start]
    visited[start] = True
    current = start

    # Batch distance computation for speed
    # Process in chunks to avoid memory issues
    CHUNK = 500
    for step in range(1, n):
        # Compute distance from current to all unvisited
        current_feat = features[current:current+1]

        best_dist = float('inf')
        best_idx = -1

        # Check all unvisited in chunks
        unvisited = np.where(~visited)[0]
        for chunk_start in range(0, len(unvisited), CHUNK):
            chunk_idx = unvisited[chunk_start:chunk_start + CHUNK]
            dists = cdist(current_feat, features[chunk_idx], metric='euclidean')[0]
            local_best = np.argmin(dists)
            if dists[local_best] < best_dist:
                best_dist = dists[local_best]
                best_idx = chunk_idx[local_best]

        order.append(best_idx)
        visited[best_idx] = True
        current = best_idx

        if (step + 1) % 500 == 0:
            print(f"    {step+1}/{n} (avg dist: {best_dist:.3f})")

    return order


def make_frame(img_path, index, total, chair, neighbor_dist=None):
    """Create one frame with chair image + info bar."""
    img = Image.open(img_path).convert("RGBA")
    img = img.resize((SIZE, SIZE), Image.LANCZOS)

    canvas = Image.new("RGB", (SIZE, TOTAL_H), (255, 255, 255))
    white_bg = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 255))
    white_bg.paste(img, mask=img.split()[3])
    canvas.paste(white_bg.convert("RGB"), (0, 0))

    draw = ImageDraw.Draw(canvas)
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
    draw.rectangle([(0, bar_y), (SIZE, bar_y + 3)], fill=(60, 60, 60))
    draw.rectangle([(0, bar_y), (int(SIZE * progress), bar_y + 3)], fill=(80, 180, 120))

    y_text = SIZE + 10
    # Left: name + year
    year_str = f" ({int(chair['year'])})" if chair['year'] else ""
    label = f"{chair['name']}{year_str}"
    if len(label) > 45:
        label = label[:42] + "..."
    draw.text((12, y_text), label, fill=(255, 255, 255), font=font_main)

    # Right: counter
    counter = f"{index + 1} / {total}"
    bb = draw.textbbox((0, 0), counter, font=font_main)
    draw.text((SIZE - (bb[2]-bb[0]) - 12, y_text), counter, fill=(160,160,160), font=font_main)

    # Second line: materials + producer
    parts = []
    if chair.get("producer"):
        parts.append(chair["producer"])
    if chair.get("mat"):
        mats = chair["mat"]
        if len(mats) > 50:
            mats = mats[:47] + "..."
        parts.append(mats)
    subtitle = "  --  ".join(parts)
    draw.text((12, y_text + 22), subtitle, fill=(120, 120, 120), font=font_small)

    return np.array(canvas)


def render_smooth_flipbook(chairs, order, features, out_dir):
    """Render WebM in visual-similarity order."""
    total = len(order)
    webm_path = os.path.join(out_dir, "flipbook_smooth.webm")
    print(f"  Rendering smooth flipbook -> {webm_path}")

    writer = imageio.get_writer(
        webm_path, fps=FPS, codec="libvpx-vp9",
        pixelformat="yuv420p",
        output_params=["-crf", "33", "-b:v", "0", "-row-mt", "1"])

    for step, chair_idx in enumerate(order):
        chair = chairs[chair_idx]
        frame = make_frame(chair["img"], step, total, chair)
        # Pad to even dimensions
        h, w = frame.shape[:2]
        if h % 2: frame = frame[:h-1]
        if w % 2: frame = frame[:,:w-1]
        writer.append_data(frame)

        if (step + 1) % 500 == 0:
            print(f"    {step+1}/{total}")

    writer.close()
    sz = os.path.getsize(webm_path) / 1e6
    dur = total / FPS
    print(f"    done: {sz:.1f} MB, {dur:.0f}s")
    return webm_path


def main():
    print("=== STOLAR Smooth Flipbook ===")
    chairs = load_data()
    print(f"  {len(chairs)} chairs loaded")

    # Step 1: extract features
    features = extract_features(chairs)

    # Step 2: find smooth ordering
    order = greedy_nn_order(features)

    # Compute total path distance for diagnostics
    total_dist = sum(
        np.linalg.norm(features[order[i]] - features[order[i+1]])
        for i in range(len(order)-1)
    )
    random_sample_dist = np.mean([
        np.linalg.norm(features[i] - features[j])
        for i, j in zip(np.random.randint(0, len(chairs), 100),
                        np.random.randint(0, len(chairs), 100))
    ])
    print(f"  Avg step distance: {total_dist/len(order):.3f}")
    print(f"  Avg random distance: {random_sample_dist:.3f}")
    print(f"  Smoothness ratio: {total_dist/len(order)/random_sample_dist:.2f}x (lower = smoother)")

    # Step 3: render
    os.makedirs(OUT_DIR, exist_ok=True)
    render_smooth_flipbook(chairs, order, features, OUT_DIR)

    # Also save ordering as CSV for reuse
    order_path = os.path.join(OUT_DIR, "smooth_order.csv")
    with open(order_path, "w") as f:
        f.write("position,chair_idx,obj_id\n")
        for pos, ci in enumerate(order):
            f.write(f"{pos},{ci},{chairs[ci]['id']}\n")
    print(f"  Order saved to {order_path}")

    print("\n  Done!")


if __name__ == "__main__":
    main()
