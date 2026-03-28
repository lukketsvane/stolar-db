"""
STOLAR -- Encode frame-sekvensar til smooth WebM (VP9).

Generelt verktøy for å konvertere ei mappe med PNG-frames
til ein VP9-video med same kvalitet som dei andre STOLAR-animasjonane.

Bruk:
  python pipeline/encode_frames.py results/pointcloud_frames
  python pipeline/encode_frames.py results/flipbook_frames/aarstal --fps 24 --crf 30
  python pipeline/encode_frames.py results/explore/morphospace_anim -o results/explore/morph_rotate.webm
"""

import argparse, glob, os, sys, re
sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None

import imageio.v2 as imageio


def natural_sort_key(s):
    """Sorter filer naturleg: frame_2 < frame_10."""
    return [int(c) if c.isdigit() else c.lower()
            for c in re.split(r'(\d+)', s)]


def encode(frames_dir, output=None, fps=30, crf=28):
    frames_dir = frames_dir.rstrip("/\\")

    # Finn alle PNG-frames, sortert naturleg
    patterns = [os.path.join(frames_dir, "*.png")]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    files.sort(key=natural_sort_key)

    if not files:
        print(f"Ingen PNG-filer funne i {frames_dir}")
        sys.exit(1)

    # Standard output-namn: same stad som mappa, med .webm
    if output is None:
        output = frames_dir.rstrip("/\\") + ".webm"

    print(f"Encoder {len(files)} frames -> {output}")
    print(f"  fps={fps}  crf={crf}  codec=libvpx-vp9")

    # Finn felles storleik (maks dimensjonar, avrunda opp til partal for yuv420p)
    from PIL import Image
    import numpy as np

    max_w, max_h = 0, 0
    for f in files:
        im = Image.open(f)
        max_w = max(max_w, im.size[0])
        max_h = max(max_h, im.size[1])
    # Avrund til partal (krav for yuv420p)
    tw = max_w if max_w % 2 == 0 else max_w + 1
    th = max_h if max_h % 2 == 0 else max_h + 1
    print(f"  Kanvas: {tw}x{th}")

    writer = imageio.get_writer(
        output, fps=fps, codec="libvpx-vp9",
        pixelformat="yuv420p",
        output_params=["-crf", str(crf), "-b:v", "0", "-row-mt", "1"])

    for i, f in enumerate(files):
        frame = imageio.imread(f)
        # Sørg for RGB (drop alpha om den finst)
        if frame.ndim == 3 and frame.shape[2] == 4:
            frame = frame[:, :, :3]
        fh, fw = frame.shape[:2]
        # Resize/pad til felles kanvas
        if fw != tw or fh != th:
            canvas = np.zeros((th, tw, 3), dtype=np.uint8)
            canvas[:min(fh, th), :min(fw, tw)] = frame[:min(fh, th), :min(fw, tw)]
            frame = canvas
        writer.append_data(frame)
        if (i + 1) % 100 == 0 or i == len(files) - 1:
            pct = 100 * (i + 1) / len(files)
            print(f"  {i+1}/{len(files)} ({pct:.0f}%)")

    writer.close()
    size_mb = os.path.getsize(output) / 1024 / 1024
    duration = len(files) / fps
    print(f"\nFERDIG: {output}")
    print(f"  {size_mb:.1f} MB, {duration:.1f}s @ {fps}fps")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encode PNG-frames til WebM VP9")
    parser.add_argument("frames_dir", help="Mappe med PNG-frames")
    parser.add_argument("-o", "--output", help="Output-filsti (standard: <mappe>.webm)")
    parser.add_argument("--fps", type=int, default=30, help="Frames per sekund (standard: 30)")
    parser.add_argument("--crf", type=int, default=28, help="Kvalitet 0-63, lågare=betre (standard: 28)")
    args = parser.parse_args()
    encode(args.frames_dir, args.output, args.fps, args.crf)
