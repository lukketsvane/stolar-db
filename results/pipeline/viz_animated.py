"""
Animerte visualiseringar av STOLAR-databasen.
Fokus: data som flyt og veks over tid -- ikkje kamerarotasjon.

Produserer:
  1. 3D morfospace: punkt dukkar opp tiår for tiår, bygger opp skya
  2. 2D H×B scatter: kvart tiår glir inn, gamle punkt fader ut
  3. Varianstunnel: ±σ-envelopen veks frå venstre til høgre
  4. Sentroid-bane: sentroiden si reise gjennom formrommet, animert
  5. Dimensjonsdrift: rullande vindu langs tidslinja
"""

import csv
import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d import Axes3D
import imageio

OUT = "results/explore"
CSV_PATH = "STOLAR/STOLAR.csv"
FPS = 30


def load():
    chairs = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            chairs.append({
                "year": float(row["Frå år"] or 0),
                "height": float(row["Høgde (cm)"] or 0),
                "width": float(row["Breidde (cm)"] or 0),
                "depth": float(row["Djupn (cm)"] or 0),
                "seat_h": float(row["Setehøgde (cm)"] or 0),
                "weight": float(row["Estimert vekt (kg)"] or 0),
            })
    return chairs


def valid(chairs, keys):
    return [c for c in chairs if all(c.get(k, 0) > 0 for k in keys)]


def fig_to_array(fig):
    fig.canvas.draw()
    buf = np.array(fig.canvas.buffer_rgba())[:, :, :3]
    h, w = buf.shape[:2]
    return buf[:h - h % 2, :w - w % 2]


def style():
    plt.rcParams.update({
        "figure.facecolor": "#fafafa", "axes.facecolor": "#fafafa",
        "axes.edgecolor": "#ccc", "axes.grid": True, "grid.alpha": 0.25,
        "font.size": 11, "axes.titlesize": 15, "font.family": "sans-serif",
    })


# =========================================================================
# 1. 3D MORPHOSPACE -- TEMPORAL ACCUMULATION
# =========================================================================
def anim_3d_accumulate(chairs):
    """Points appear decade by decade. Camera stays still. Data grows."""
    style()
    data = valid(chairs, ["year", "height", "width", "depth"])
    years = np.array([c["year"] for c in data])
    h = np.array([c["height"] for c in data])
    w = np.array([c["width"] for c in data])
    d = np.array([c["depth"] for c in data])

    # Clip outliers
    mask = (h < np.percentile(h, 98)) & (w < np.percentile(w, 98)) & (d < np.percentile(d, 98))
    years, h, w, d = years[mask], h[mask], w[mask], d[mask]

    start_year, end_year = 1500, 2025
    n_frames = 300
    year_steps = np.linspace(start_year, end_year, n_frames)

    path = f"{OUT}/anim_3d_accumulate.webm"
    print(f"  3D accumulate -> {path} ({n_frames} frames)")
    writer = imageio.get_writer(path, fps=FPS, codec="libvpx-vp9",
                                pixelformat="yuv420p",
                                output_params=["-crf", "28", "-b:v", "0"])

    hlim = (0, h.max() * 1.05)
    wlim = (0, w.max() * 1.05)
    dlim = (0, d.max() * 1.05)

    for i, yr in enumerate(year_steps):
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")

        # Old points (before current year) -- faded
        old = years <= yr
        if old.sum() > 0:
            ax.scatter(w[old], d[old], h[old], alpha=0.25, s=8,
                       color="#888", edgecolors="none", depthshade=False)

        # New points (current decade) -- bright
        fresh = (years > yr - 15) & (years <= yr)
        if fresh.sum() > 0:
            ax.scatter(w[fresh], d[fresh], h[fresh], alpha=0.9, s=30,
                       color="#c44e52", edgecolors="white", linewidths=0.3,
                       depthshade=False)

        ax.set_xlim(*wlim); ax.set_ylim(*dlim); ax.set_zlim(*hlim)
        ax.set_xlabel("Breidde (cm)")
        ax.set_ylabel("Djupn (cm)")
        ax.set_zlabel("Høgde (cm)")
        ax.view_init(elev=22, azim=42)

        ax.set_title(f"Morfospace  --  {int(yr)}", fontsize=16)
        ax.text2D(0.02, 0.02, f"n = {old.sum()}", transform=ax.transAxes,
                  fontsize=11, color="#666")

        fig.tight_layout()
        writer.append_data(fig_to_array(fig))
        plt.close()
        if (i + 1) % 50 == 0:
            print(f"    {i+1}/{n_frames}")

    writer.close()
    print(f"    {os.path.getsize(path)/1e6:.1f} MB")


# =========================================================================
# 2. 2D H×B SCATTER -- SMOOTH DECADE SWEEP
# =========================================================================
def anim_2d_morphospace(chairs):
    """H vs W scatter, decade by decade, with fading trail."""
    style()
    data = valid(chairs, ["year", "height", "width"])
    years = np.array([c["year"] for c in data])
    h = np.array([c["height"] for c in data])
    w = np.array([c["width"] for c in data])

    mask = (h < np.percentile(h, 99)) & (w < np.percentile(w, 99))
    years, h, w = years[mask], h[mask], w[mask]

    start_year, end_year = 1500, 2025
    n_frames = 400
    year_steps = np.linspace(start_year, end_year, n_frames)

    path = f"{OUT}/anim_2d_morphospace.webm"
    print(f"  2D morphospace -> {path} ({n_frames} frames)")
    writer = imageio.get_writer(path, fps=FPS, codec="libvpx-vp9",
                                pixelformat="yuv420p",
                                output_params=["-crf", "28", "-b:v", "0"])

    hlim = (0, np.percentile(h, 99) * 1.1)
    wlim = (0, np.percentile(w, 99) * 1.1)

    for i, yr in enumerate(year_steps):
        fig, ax = plt.subplots(figsize=(9, 7))

        # History trail -- graduated fade
        for age_band, alpha, sz in [(100, 0.03, 4), (50, 0.08, 6), (20, 0.15, 10)]:
            band = (years <= yr) & (years > yr - age_band)
            if band.sum():
                ax.scatter(w[band], h[band], alpha=alpha, s=sz,
                           color="#999", edgecolors="none", zorder=1)

        # Current window (15 years)
        cur = (years > yr - 15) & (years <= yr)
        if cur.sum():
            ax.scatter(w[cur], h[cur], alpha=0.8, s=30,
                       color="#c44e52", edgecolors="white", linewidths=0.3, zorder=3)

        ax.set_xlim(*wlim); ax.set_ylim(*hlim)
        ax.set_xlabel("Breidde (cm)")
        ax.set_ylabel("Høgde (cm)")

        # Big year watermark
        ax.text(0.97, 0.03, f"{int(yr)}", transform=ax.transAxes,
                fontsize=48, ha="right", va="bottom", color="#c44e52",
                alpha=0.2, fontweight="bold")
        ax.text(0.03, 0.97, f"n = {(years <= yr).sum()}", transform=ax.transAxes,
                fontsize=12, ha="left", va="top", color="#666")
        ax.set_title("Morfospace: Høgde vs Breidde")

        fig.tight_layout()
        writer.append_data(fig_to_array(fig))
        plt.close()
        if (i + 1) % 50 == 0:
            print(f"    {i+1}/{n_frames}")

    writer.close()
    print(f"    {os.path.getsize(path)/1e6:.1f} MB")


# =========================================================================
# 3. VARIANCE TUNNEL -- GROWING FROM LEFT TO RIGHT
# =========================================================================
def anim_variance_tunnel(chairs):
    """±σ envelope grows along the time axis, revealing the design corridor."""
    style()
    data = valid(chairs, ["year", "height", "width", "depth"])
    years = np.array([c["year"] for c in data])
    h = np.array([c["height"] for c in data])
    w = np.array([c["width"] for c in data])
    d = np.array([c["depth"] for c in data])

    # Pre-compute stats per year-center
    centers = np.arange(1500, 2026, 1)
    window = 25  # ±12.5 years

    dims = [("Høgde (cm)", h, "#c44e52"),
            ("Breidde (cm)", w, "#4c72b0"),
            ("Djupn (cm)", d, "#55a868")]

    stats = {}
    for name, arr, _ in dims:
        means, lo1, hi1, lo2, hi2 = [], [], [], [], []
        for c in centers:
            m = (years >= c - window/2) & (years < c + window/2)
            if m.sum() > 5:
                mu = np.mean(arr[m])
                s = np.std(arr[m])
                means.append(mu); lo1.append(mu - s); hi1.append(mu + s)
                lo2.append(mu - 2*s); hi2.append(mu + 2*s)
            else:
                means.append(np.nan); lo1.append(np.nan); hi1.append(np.nan)
                lo2.append(np.nan); hi2.append(np.nan)
        stats[name] = {
            "mean": np.array(means), "lo1": np.array(lo1), "hi1": np.array(hi1),
            "lo2": np.array(lo2), "hi2": np.array(hi2)
        }

    n_frames = 350
    reveal_positions = np.linspace(0, len(centers) - 1, n_frames).astype(int)

    path = f"{OUT}/anim_variance_tunnel.webm"
    print(f"  Variance tunnel -> {path} ({n_frames} frames)")
    writer = imageio.get_writer(path, fps=FPS, codec="libvpx-vp9",
                                pixelformat="yuv420p",
                                output_params=["-crf", "28", "-b:v", "0"])

    for fi, reveal_idx in enumerate(reveal_positions):
        fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
        cx = centers[:reveal_idx + 1]

        for ax, (name, _, color) in zip(axes, dims):
            s = stats[name]
            m = s["mean"][:reveal_idx + 1]
            good = ~np.isnan(m)
            if good.sum() > 1:
                ax.fill_between(cx[good], s["lo2"][:reveal_idx+1][good],
                                s["hi2"][:reveal_idx+1][good],
                                color=color, alpha=0.08)
                ax.fill_between(cx[good], s["lo1"][:reveal_idx+1][good],
                                s["hi1"][:reveal_idx+1][good],
                                color=color, alpha=0.2)
                ax.plot(cx[good], m[good], color=color, lw=2.5)

            # Also scatter raw points up to this year
            yr_cutoff = centers[reveal_idx]
            raw_mask = years <= yr_cutoff
            _, arr, _ = [(n, a, c) for n, a, c in dims if n == name][0]
            if raw_mask.sum():
                ax.scatter(years[raw_mask], arr[raw_mask], alpha=0.07, s=4,
                           color=color, edgecolors="none")

            ax.set_ylabel(name)
            ax.set_xlim(1500, 2025)
            ax.set_ylim(0, 180)

        axes[0].set_title(f"Varianstunnel  --  opp til {int(centers[reveal_idx])}")
        axes[-1].set_xlabel("År")
        fig.tight_layout()
        writer.append_data(fig_to_array(fig))
        plt.close()
        if (fi + 1) % 50 == 0:
            print(f"    {fi+1}/{n_frames}")

    writer.close()
    print(f"    {os.path.getsize(path)/1e6:.1f} MB")


# =========================================================================
# 4. CENTROID PATH -- ANIMATED TRACE
# =========================================================================
def anim_centroid_path(chairs):
    """The centroid of (H, W, D) traces a path through 3D space over time."""
    style()
    data = valid(chairs, ["year", "height", "width", "depth"])
    years = np.array([c["year"] for c in data])
    h = np.array([c["height"] for c in data])
    w = np.array([c["width"] for c in data])
    d = np.array([c["depth"] for c in data])

    mask = (h < np.percentile(h, 98)) & (w < np.percentile(w, 98)) & (d < np.percentile(d, 98))
    years, h, w, d = years[mask], h[mask], w[mask], d[mask]

    # Compute centroids per 25-year window
    centers = np.arange(1525, 2025, 5)
    ch, cw, cd = [], [], []
    for c in centers:
        m = (years >= c - 25) & (years < c + 25)
        if m.sum() > 5:
            ch.append(np.mean(h[m])); cw.append(np.mean(w[m])); cd.append(np.mean(d[m]))
        else:
            ch.append(np.nan); cw.append(np.nan); cd.append(np.nan)
    ch, cw, cd = np.array(ch), np.array(cw), np.array(cd)
    good = ~np.isnan(ch)
    centers_g = centers[good]; ch_g = ch[good]; cw_g = cw[good]; cd_g = cd[good]

    n_frames = 250
    path = f"{OUT}/anim_centroid_path.webm"
    print(f"  Centroid path -> {path} ({n_frames} frames)")
    writer = imageio.get_writer(path, fps=FPS, codec="libvpx-vp9",
                                pixelformat="yuv420p",
                                output_params=["-crf", "28", "-b:v", "0"])

    reveal_steps = np.linspace(1, len(centers_g), n_frames, dtype=int)

    for fi, n_show in enumerate(reveal_steps):
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")

        # Background scatter (all data, very faded)
        ax.scatter(w, d, h, alpha=0.03, s=3, color="#aaa", edgecolors="none", depthshade=False)

        # Centroid trail
        if n_show > 1:
            ax.plot(cw_g[:n_show], cd_g[:n_show], ch_g[:n_show],
                    color="#c44e52", lw=3, alpha=0.7, zorder=5)

        # Current centroid (big dot)
        idx = n_show - 1
        ax.scatter([cw_g[idx]], [cd_g[idx]], [ch_g[idx]],
                   s=120, color="#c44e52", edgecolors="white", linewidths=1.5,
                   zorder=10, depthshade=False)

        # Start point
        ax.scatter([cw_g[0]], [cd_g[0]], [ch_g[0]],
                   s=60, color="#4c72b0", edgecolors="white", linewidths=1,
                   zorder=10, depthshade=False)

        ax.set_xlabel("Breidde (cm)")
        ax.set_ylabel("Djupn (cm)")
        ax.set_zlabel("Høgde (cm)")
        ax.set_xlim(w.min() * 0.8, w.max() * 0.5)
        ax.set_ylim(d.min() * 0.8, d.max() * 0.5)
        ax.set_zlim(h.min() * 0.8, h.max() * 0.6)
        ax.view_init(elev=25, azim=42)
        ax.set_title(f"Sentroidbane  --  {int(centers_g[idx])}", fontsize=15)

        fig.tight_layout()
        writer.append_data(fig_to_array(fig))
        plt.close()
        if (fi + 1) % 50 == 0:
            print(f"    {fi+1}/{n_frames}")

    writer.close()
    print(f"    {os.path.getsize(path)/1e6:.1f} MB")


# =========================================================================
# 5. DIMENSION DRIFT -- SCROLLING WINDOW
# =========================================================================
def anim_dimension_drift(chairs):
    """Rolling window moves along the timeline, showing H/W/D distributions."""
    style()
    data = valid(chairs, ["year", "height", "width", "depth"])
    years = np.array([c["year"] for c in data])
    h = np.array([c["height"] for c in data])
    w = np.array([c["width"] for c in data])
    d = np.array([c["depth"] for c in data])

    n_frames = 400
    year_steps = np.linspace(1500, 2025, n_frames)
    window = 30

    path = f"{OUT}/anim_dimension_drift.webm"
    print(f"  Dimension drift -> {path} ({n_frames} frames)")
    writer = imageio.get_writer(path, fps=FPS, codec="libvpx-vp9",
                                pixelformat="yuv420p",
                                output_params=["-crf", "28", "-b:v", "0"])

    dims = [("Høgde", h, "#c44e52"), ("Breidde", w, "#4c72b0"), ("Djupn", d, "#55a868")]
    hlim = max(np.percentile(h, 99), np.percentile(w, 99), np.percentile(d, 99)) * 1.1

    for fi, yr in enumerate(year_steps):
        fig, axes = plt.subplots(1, 3, figsize=(14, 5))

        cur = (years >= yr - window/2) & (years < yr + window/2)
        n_cur = cur.sum()

        for ax, (name, arr, color) in zip(axes, dims):
            # Full distribution (ghost)
            ax.hist(arr, bins=40, range=(0, hlim), alpha=0.1, color="#999",
                    density=True, edgecolor="none")

            # Current window distribution
            if n_cur > 3:
                ax.hist(arr[cur], bins=25, range=(0, hlim), alpha=0.7, color=color,
                        density=True, edgecolor="white", linewidth=0.5)
                med = np.median(arr[cur])
                ax.axvline(med, color=color, lw=2, ls="--", alpha=0.8)
                ax.text(med + 2, ax.get_ylim()[1] * 0.9, f"{med:.0f}",
                        color=color, fontsize=10, fontweight="bold")

            ax.set_xlim(0, hlim)
            ax.set_xlabel(f"{name} (cm)")
            ax.set_title(name)

        fig.suptitle(f"Dimensjonsfordeling  {int(yr - window/2)}--{int(yr + window/2)}  (n={n_cur})",
                     fontsize=14)
        fig.tight_layout()
        writer.append_data(fig_to_array(fig))
        plt.close()
        if (fi + 1) % 50 == 0:
            print(f"    {fi+1}/{n_frames}")

    writer.close()
    print(f"    {os.path.getsize(path)/1e6:.1f} MB")


# =========================================================================
# 6. SQUATNESS EVOLUTION -- RATIO OVER TIME
# =========================================================================
def anim_squatness(chairs):
    """W/H ratio accumulating over time with running median."""
    style()
    data = valid(chairs, ["year", "height", "width"])
    years = np.array([c["year"] for c in data])
    ratio = np.array([c["width"] / c["height"] for c in data])

    n_frames = 350
    year_steps = np.linspace(1500, 2025, n_frames)

    path = f"{OUT}/anim_squatness.webm"
    print(f"  Squatness -> {path} ({n_frames} frames)")
    writer = imageio.get_writer(path, fps=FPS, codec="libvpx-vp9",
                                pixelformat="yuv420p",
                                output_params=["-crf", "28", "-b:v", "0"])

    for fi, yr in enumerate(year_steps):
        fig, ax = plt.subplots(figsize=(11, 6))

        shown = years <= yr
        if shown.sum():
            ax.scatter(years[shown], ratio[shown], alpha=0.15, s=8,
                       color="#8172b2", edgecolors="none")

        # Running median up to this year
        decades = np.arange(1400, int(yr) + 1, 10)
        meds = []
        for dec in decades:
            m = (years >= dec) & (years < dec + 20) & (years <= yr)
            meds.append(np.median(ratio[m]) if m.sum() > 3 else np.nan)
        meds = np.array(meds)
        good = ~np.isnan(meds)
        if good.sum() > 1:
            ax.plot(decades[good], meds[good], color="#8172b2", lw=2.5)

        ax.axhline(1.0, color="#999", ls="--", lw=1, alpha=0.4)
        ax.set_xlim(1450, 2030)
        ax.set_ylim(0, 2.5)
        ax.set_xlabel("År")
        ax.set_ylabel("Breidde / Høgde")
        ax.set_title(f"Squatness-indeks (B/H)  --  {int(yr)}")
        ax.text(0.97, 0.97, f"n = {shown.sum()}", transform=ax.transAxes,
                fontsize=11, ha="right", va="top", color="#666")

        fig.tight_layout()
        writer.append_data(fig_to_array(fig))
        plt.close()
        if (fi + 1) % 50 == 0:
            print(f"    {fi+1}/{n_frames}")

    writer.close()
    print(f"    {os.path.getsize(path)/1e6:.1f} MB")


def main():
    print("=== STOLAR Animated Explorations ===")
    os.makedirs(OUT, exist_ok=True)
    chairs = load()
    print(f"  {len(chairs)} chairs\n")

    anim_2d_morphospace(chairs)
    anim_squatness(chairs)
    anim_variance_tunnel(chairs)
    anim_dimension_drift(chairs)
    anim_3d_accumulate(chairs)
    anim_centroid_path(chairs)

    print(f"\n  Done! All in {OUT}/")


if __name__ == "__main__":
    main()
