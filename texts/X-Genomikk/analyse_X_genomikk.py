"""
analyse_X_genomikk.py
Article X: Formens genom -- JAILBREAK EDITION

Computational genomics, spectral analysis, causal inference,
power laws, network community detection, and phylogenetics
applied to 744 years of chair design.

Each figure = one rapid prototype experiment.
"""

import csv, math, warnings, itertools
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.ndimage import gaussian_filter
from scipy.signal import welch
from scipy.stats import linregress, pearsonr, spearmanr
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
import networkx as nx
import community as community_louvain

warnings.filterwarnings("ignore")

# ── Style ────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Palatino", "Palatino Linotype", "Book Antiqua", "Georgia"],
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "legend.fontsize": 6,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
})

FIG = Path(__file__).parent / "fig"
FIG.mkdir(exist_ok=True)
DATA = Path(__file__).parent.parent.parent / "STOLAR" / "STOLAR.csv"

# ── Palette ──────────────────────────────────────────────────────
CENT_C = {
    "1200-talet": "#4e342e", "1300-talet": "#5d4037",
    "1400-talet": "#6d4c41", "1500-talet": "#795548",
    "1600-talet": "#d32f2f", "1700-talet": "#e65100",
    "1800-talet": "#1565c0", "1900-talet": "#2e7d32",
    "2000-talet": "#6a1b9a",
}
CENT_ORDER = list(CENT_C.keys())


def parse_mats(cell):
    if not cell or not str(cell).strip():
        return []
    return [x.strip() for x in str(cell).split(",") if x.strip()]


def load():
    df = pd.read_csv(DATA, encoding="utf-8-sig")
    for col in ["Høgde (cm)", "Breidde (cm)", "Djupn (cm)",
                 "Setehøgde (cm)", "Estimert vekt (kg)", "Frå år"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "."), errors="coerce"
            )
    mask = (
        df["Høgde (cm)"].notna() & (df["Høgde (cm)"] > 0) &
        df["Breidde (cm)"].notna() & (df["Breidde (cm)"] > 0) &
        df["Hundreår"].notna()
    )
    df = df[mask].copy()
    df["Year"] = df["Frå år"]
    df["Decade"] = (df["Year"] // 10 * 10).astype("Int64")
    df["MatList"] = df["Materialar"].apply(parse_mats)
    df["MatCount"] = df["MatList"].apply(len)
    print(f"Loaded: {len(df)} chairs")
    return df


# ══════════════════════════════════════════════════════════════════
# EXPERIMENT 1: PHYLOGENETIC TREE OF CHAIR STYLES
# ══════════════════════════════════════════════════════════════════
def exp1_phylogenetics(df):
    """Build a neighbor-joining-style phylogenetic tree of chair styles."""
    print("\n[EXP 1] PHYLOGENETIC TREE")

    # Encode each style as a feature vector
    styles = df["Stilperiode"].dropna().unique()
    styles = [s for s in styles if df[df["Stilperiode"] == s].shape[0] >= 10]

    # Feature vector per style: mean H, W, D, matcount + material frequencies
    all_mats = set()
    for ml in df["MatList"]:
        all_mats.update(ml)
    all_mats = sorted(all_mats)
    mat_idx = {m: i for i, m in enumerate(all_mats)}

    profiles = {}
    for style in styles:
        sub = df[df["Stilperiode"] == style]
        vec = [
            sub["Høgde (cm)"].mean(),
            sub["Breidde (cm)"].mean(),
            sub["Djupn (cm)"].mean() if "Djupn (cm)" in sub else 0,
            sub["MatCount"].mean(),
        ]
        # Material frequency vector
        mat_freq = np.zeros(len(all_mats))
        for ml in sub["MatList"]:
            for m in ml:
                if m in mat_idx:
                    mat_freq[mat_idx[m]] += 1
        if len(sub) > 0:
            mat_freq /= len(sub)
        vec.extend(mat_freq.tolist())
        profiles[style] = vec

    style_names = sorted(profiles.keys())
    X = np.array([profiles[s] for s in style_names])
    X_s = StandardScaler().fit_transform(X)

    # Hierarchical clustering (Ward's method as proxy for NJ)
    Z = linkage(X_s, method="ward", metric="euclidean")

    # Color by rough era
    def era_color(style):
        sub = df[df["Stilperiode"] == style]
        median_year = sub["Year"].median()
        if median_year < 1600: return "#795548"
        elif median_year < 1700: return "#d32f2f"
        elif median_year < 1800: return "#e65100"
        elif median_year < 1900: return "#1565c0"
        elif median_year < 2000: return "#2e7d32"
        else: return "#6a1b9a"

    fig, ax = plt.subplots(figsize=(7, 6))
    dend = dendrogram(
        Z, labels=style_names, orientation="left",
        leaf_font_size=6, ax=ax, color_threshold=0.7 * max(Z[:, 2]),
    )

    # Color labels by era
    ylbls = ax.get_yticklabels()
    for lbl in ylbls:
        txt = lbl.get_text()
        if txt in profiles:
            lbl.set_color(era_color(txt))
            lbl.set_fontweight("bold")

    ax.set_xlabel("Ward-avstand")
    ax.set_title("Fig. 1: Fylogenetisk tre over stilperiodar", fontweight="bold")
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("white")

    # Era legend
    handles = [
        mpatches.Patch(color="#795548", label="Pre-1600"),
        mpatches.Patch(color="#d32f2f", label="1600-talet"),
        mpatches.Patch(color="#e65100", label="1700-talet"),
        mpatches.Patch(color="#1565c0", label="1800-talet"),
        mpatches.Patch(color="#2e7d32", label="1900-talet"),
        mpatches.Patch(color="#6a1b9a", label="2000-talet"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=6)

    plt.tight_layout()
    fig.savefig(FIG / "fig01_fylogenese.pdf")
    fig.savefig(FIG / "fig01_fylogenese.png")
    plt.close()
    print(f"  {len(style_names)} styles in phylogenetic tree")

    # Report deepest splits
    from scipy.cluster.hierarchy import leaves_list
    leaves = [style_names[i] for i in leaves_list(Z)]
    print(f"  Leaf order (bottom to top): {leaves[:5]}...{leaves[-5:]}")


# ══════════════════════════════════════════════════════════════════
# EXPERIMENT 2: FFT POWER SPECTRUM -- HIDDEN FREQUENCIES
# ══════════════════════════════════════════════════════════════════
def exp2_fft_spectrum(df):
    """Fourier analysis of chair dimension time series."""
    print("\n[EXP 2] FFT POWER SPECTRUM")

    # Build yearly time series (interpolated)
    yearly = df.groupby("Year").agg({
        "Høgde (cm)": "mean",
        "Breidde (cm)": "mean",
    }).sort_index()

    # Resample to regular 1-year intervals
    full_idx = np.arange(yearly.index.min(), yearly.index.max() + 1)
    h_interp = np.interp(full_idx, yearly.index, yearly["Høgde (cm)"])
    w_interp = np.interp(full_idx, yearly.index, yearly["Breidde (cm)"])

    # Detrend
    h_detrend = h_interp - np.polyval(np.polyfit(full_idx, h_interp, 2), full_idx)
    w_detrend = w_interp - np.polyval(np.polyfit(full_idx, w_interp, 2), full_idx)

    # Welch PSD (more robust than raw FFT)
    fs = 1.0  # 1 sample/year
    nperseg = min(128, len(h_detrend) // 2)

    f_h, psd_h = welch(h_detrend, fs=fs, nperseg=nperseg)
    f_w, psd_w = welch(w_detrend, fs=fs, nperseg=nperseg)

    # Convert frequency to period
    with np.errstate(divide="ignore"):
        period_h = 1.0 / f_h
        period_w = 1.0 / f_w

    fig, axes = plt.subplots(2, 2, figsize=(7, 5.5))

    # Top left: H time series
    ax = axes[0, 0]
    ax.plot(full_idx, h_interp, color="#1565c0", linewidth=0.5, alpha=0.6)
    ax.plot(full_idx, gaussian_filter(h_interp, sigma=10),
            color="#1565c0", linewidth=1.5, label="10-ars glatta")
    ax.set_xlabel("Ar")
    ax.set_ylabel("Hogde (cm)")
    ax.set_title("a) Hogdetidsserie")
    ax.legend(fontsize=5)
    ax.set_facecolor("#fafafa")

    # Top right: W time series
    ax = axes[0, 1]
    ax.plot(full_idx, w_interp, color="#d32f2f", linewidth=0.5, alpha=0.6)
    ax.plot(full_idx, gaussian_filter(w_interp, sigma=10),
            color="#d32f2f", linewidth=1.5, label="10-ars glatta")
    ax.set_xlabel("Ar")
    ax.set_ylabel("Breidde (cm)")
    ax.set_title("b) Breiddetidsserie")
    ax.legend(fontsize=5)
    ax.set_facecolor("#fafafa")

    # Bottom left: H power spectrum
    ax = axes[1, 0]
    mask = (f_h > 0) & (period_h < 500) & (period_h > 5)
    ax.semilogy(period_h[mask], psd_h[mask], color="#1565c0", linewidth=1)
    ax.set_xlabel("Periode (ar)")
    ax.set_ylabel("Spektraltettleik")
    ax.set_title("c) Hogde: effektspektrum")
    ax.set_facecolor("#fafafa")
    ax.invert_xaxis()

    # Annotate dominant peaks
    peak_idx = np.argsort(-psd_h[mask])[:3]
    periods_peak = period_h[mask][peak_idx]
    for pp in periods_peak:
        ax.axvline(pp, color="red", alpha=0.3, linewidth=0.8, linestyle="--")
        ax.annotate(f"{pp:.0f} ar", (pp, psd_h[mask][np.argmin(abs(period_h[mask] - pp))]),
                    fontsize=5, color="red", rotation=90, va="bottom")

    # Bottom right: W power spectrum
    ax = axes[1, 1]
    mask_w = (f_w > 0) & (period_w < 500) & (period_w > 5)
    ax.semilogy(period_w[mask_w], psd_w[mask_w], color="#d32f2f", linewidth=1)
    ax.set_xlabel("Periode (ar)")
    ax.set_ylabel("Spektraltettleik")
    ax.set_title("d) Breidde: effektspektrum")
    ax.set_facecolor("#fafafa")
    ax.invert_xaxis()

    peak_idx_w = np.argsort(-psd_w[mask_w])[:3]
    periods_peak_w = period_w[mask_w][peak_idx_w]
    for pp in periods_peak_w:
        ax.axvline(pp, color="red", alpha=0.3, linewidth=0.8, linestyle="--")
        ax.annotate(f"{pp:.0f} ar", (pp, psd_w[mask_w][np.argmin(abs(period_w[mask_w] - pp))]),
                    fontsize=5, color="red", rotation=90, va="bottom")

    fig.suptitle("Fig. 2: Spektralanalyse -- stolens skjulte frekvensar",
                 fontsize=9, fontweight="bold")
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    fig.savefig(FIG / "fig02_fft_spektrum.pdf")
    fig.savefig(FIG / "fig02_fft_spektrum.png")
    plt.close()

    print(f"  H dominant periods: {periods_peak}")
    print(f"  W dominant periods: {periods_peak_w}")
    print(f"  Time span: {full_idx[0]}-{full_idx[-1]} ({len(full_idx)} years)")


# ══════════════════════════════════════════════════════════════════
# EXPERIMENT 3: ZIPF'S LAW ON MATERIALS
# ══════════════════════════════════════════════════════════════════
def exp3_zipf(df):
    """Test Zipf's law: do materials follow a power law?"""
    print("\n[EXP 3] ZIPF'S LAW")

    all_mats = []
    for ml in df["MatList"]:
        all_mats.extend(ml)

    counts = Counter(all_mats)
    ranked = sorted(counts.values(), reverse=True)
    ranks = np.arange(1, len(ranked) + 1)
    freqs = np.array(ranked)

    # Log-log regression
    log_r = np.log10(ranks)
    log_f = np.log10(freqs)
    slope, intercept, r_val, p_val, _ = linregress(log_r, log_f)

    fig, axes = plt.subplots(1, 2, figsize=(7, 3.5))

    # Left: Zipf plot
    ax = axes[0]
    ax.scatter(ranks, freqs, s=15, color="#1565c0", alpha=0.7, zorder=2)
    ax.plot(ranks, 10 ** (intercept + slope * log_r),
            color="red", linewidth=1.5, linestyle="--",
            label=f"Zipf: $\\alpha = {-slope:.2f}$, $R^2 = {r_val**2:.3f}$")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Rang")
    ax.set_ylabel("Frekvens")
    ax.set_title("a) Zipf-plott (log-log)")
    ax.legend(fontsize=6)
    ax.set_facecolor("#fafafa")

    # Right: Top 25 materials bar chart
    ax = axes[1]
    top25 = counts.most_common(25)
    names = [m for m, _ in top25]
    vals = [c for _, c in top25]
    colors = plt.cm.magma_r(np.linspace(0.2, 0.8, len(names)))
    ax.barh(range(len(names)), vals, color=colors)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=5)
    ax.set_xlabel("Frekvens")
    ax.set_title("b) Topp 25 materialar")
    ax.invert_yaxis()
    ax.set_facecolor("#fafafa")

    fig.suptitle("Fig. 3: Zipfs lov -- folger materialar ein maktlov?",
                 fontsize=9, fontweight="bold")
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    fig.savefig(FIG / "fig03_zipf.pdf")
    fig.savefig(FIG / "fig03_zipf.png")
    plt.close()

    print(f"  Zipf exponent alpha = {-slope:.3f}")
    print(f"  R^2 = {r_val**2:.4f}, p = {p_val:.2e}")
    print(f"  Total unique materials: {len(counts)}")
    print(f"  Top 5: {counts.most_common(5)}")


# ══════════════════════════════════════════════════════════════════
# EXPERIMENT 4: MATERIAL CO-OCCURRENCE NETWORK
# ══════════════════════════════════════════════════════════════════
def exp4_network(df):
    """Material co-occurrence network with Louvain community detection."""
    print("\n[EXP 4] MATERIAL CO-OCCURRENCE NETWORK")

    # Build co-occurrence matrix
    all_mats = set()
    for ml in df["MatList"]:
        all_mats.update(ml)
    mat_counts = Counter()
    for ml in df["MatList"]:
        mat_counts.update(ml)

    # Filter to materials with >= 20 occurrences
    freq_mats = {m for m, c in mat_counts.items() if c >= 20}
    print(f"  Materials with >= 20 occurrences: {len(freq_mats)}")

    cooc = defaultdict(int)
    for ml in df["MatList"]:
        mats_in = [m for m in ml if m in freq_mats]
        for a, b in itertools.combinations(sorted(set(mats_in)), 2):
            cooc[(a, b)] += 1

    # Build networkx graph
    G = nx.Graph()
    for (a, b), w in cooc.items():
        if w >= 5:  # Min co-occurrence threshold
            G.add_edge(a, b, weight=w)

    # Remove isolated nodes
    isolates = list(nx.isolates(G))
    G.remove_nodes_from(isolates)

    if len(G.nodes) == 0:
        print("  WARNING: No nodes in network")
        return

    # Louvain communities
    partition = community_louvain.best_partition(G, random_state=42)
    n_communities = len(set(partition.values()))
    print(f"  Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
    print(f"  Louvain communities: {n_communities}")

    # Community colors
    comm_colors = plt.cm.Set2(np.linspace(0, 1, max(n_communities, 8)))
    node_colors = [comm_colors[partition[n]] for n in G.nodes()]

    # Layout
    pos = nx.spring_layout(G, k=2.5, iterations=100, seed=42, weight="weight")

    # Node sizes by degree
    degrees = dict(G.degree(weight="weight"))
    max_deg = max(degrees.values())
    node_sizes = [300 * degrees[n] / max_deg + 30 for n in G.nodes()]

    # Edge widths
    edge_weights = [G[u][v]["weight"] for u, v in G.edges()]
    max_ew = max(edge_weights)
    edge_widths = [2.0 * w / max_ew + 0.2 for w in edge_weights]

    fig, ax = plt.subplots(figsize=(7, 6))

    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.15, width=edge_widths,
                           edge_color="#888888")
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=node_sizes, alpha=0.85,
                           edgecolors="white", linewidths=0.5)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=5, font_weight="bold")

    # Community legend
    comm_members = defaultdict(list)
    for n, c in partition.items():
        comm_members[c].append(n)

    handles = []
    for c_id in sorted(comm_members.keys()):
        members = comm_members[c_id]
        top_member = max(members, key=lambda m: degrees.get(m, 0))
        handles.append(mpatches.Patch(
            color=comm_colors[c_id],
            label=f"Klynge {c_id}: {top_member} +{len(members)-1}"
        ))
    ax.legend(handles=handles, loc="upper left", fontsize=5, framealpha=0.9)

    ax.set_title("Fig. 4: Materialnettverket -- Louvain-fellesskap",
                 fontsize=9, fontweight="bold")
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("white")
    ax.axis("off")

    plt.tight_layout()
    fig.savefig(FIG / "fig04_nettverk.pdf")
    fig.savefig(FIG / "fig04_nettverk.png")
    plt.close()

    # Report communities
    for c_id in sorted(comm_members.keys()):
        members = sorted(comm_members[c_id], key=lambda m: -degrees.get(m, 0))
        print(f"  Community {c_id}: {', '.join(members[:6])}")


# ══════════════════════════════════════════════════════════════════
# EXPERIMENT 5: GRANGER CAUSALITY -- WHAT CAUSES WHAT?
# ══════════════════════════════════════════════════════════════════
def exp5_granger(df):
    """Granger causality between dimensional and material time series."""
    print("\n[EXP 5] GRANGER CAUSALITY")
    from statsmodels.tsa.stattools import grangercausalitytests

    # Build decade time series
    decades = sorted(df["Decade"].dropna().unique())
    series = {"H": [], "W": [], "MatCount": [], "H_entropy": []}

    for dec in decades:
        sub = df[df["Decade"] == dec]
        if len(sub) < 3:
            continue
        series["H"].append(sub["Høgde (cm)"].mean())
        series["W"].append(sub["Breidde (cm)"].mean())
        series["MatCount"].append(sub["MatCount"].mean())

        # Material entropy
        all_m = []
        for ml in sub["MatList"]:
            all_m.extend(ml)
        c = Counter(all_m)
        total = sum(c.values())
        h_ent = -sum((v/total) * math.log2(v/total) for v in c.values() if v > 0) if total > 0 else 0
        series["H_entropy"].append(h_ent)

    vars_list = list(series.keys())
    n = len(series["H"])

    # Pairwise Granger causality
    max_lag = 3
    gc_matrix = np.zeros((len(vars_list), len(vars_list)))
    gc_pvals = np.ones((len(vars_list), len(vars_list)))

    for i, v1 in enumerate(vars_list):
        for j, v2 in enumerate(vars_list):
            if i == j:
                continue
            try:
                data = np.column_stack([series[v1], series[v2]])
                result = grangercausalitytests(data, maxlag=max_lag, verbose=False)
                # Best lag p-value (F-test)
                best_p = min(result[lag][0]["ssr_ftest"][1] for lag in range(1, max_lag + 1))
                gc_pvals[i, j] = best_p
                gc_matrix[i, j] = -np.log10(best_p + 1e-10)
            except Exception:
                pass

    fig, axes = plt.subplots(1, 2, figsize=(7, 3.5))

    # Left: Granger causality heatmap (-log10 p-value)
    ax = axes[0]
    labels = ["Hogde", "Breidde", "Materialtal", "Mat. entropi"]
    im = ax.imshow(gc_matrix, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=6)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=6)
    ax.set_xlabel("Effekt (Y)")
    ax.set_ylabel("Arsak (X)")
    ax.set_title("a) Granger-kausalitet $(-\\log_{10}\\, p)$")

    # Annotate significant cells
    for i in range(len(labels)):
        for j in range(len(labels)):
            if i == j:
                ax.text(j, i, "--", ha="center", va="center", fontsize=6, color="gray")
            else:
                p = gc_pvals[i, j]
                stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
                color = "white" if gc_matrix[i, j] > 2 else "black"
                ax.text(j, i, f"{gc_matrix[i,j]:.1f}{stars}", ha="center",
                        va="center", fontsize=5, color=color, fontweight="bold")

    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("$-\\log_{10}(p)$", fontsize=6)

    # Right: Causal arrow diagram
    ax = axes[1]
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)

    # Position variables in a circle
    angles = np.linspace(0, 2 * np.pi, len(vars_list), endpoint=False)
    positions = {v: (np.cos(a), np.sin(a)) for v, a in zip(vars_list, angles)}

    # Draw nodes
    for v, (x, y) in positions.items():
        label = {"H": "Hogde", "W": "Breidde", "MatCount": "Materialtal",
                 "H_entropy": "Entropi"}[v]
        ax.scatter(x, y, s=800, color="#1565c0", alpha=0.8, zorder=3,
                   edgecolors="white", linewidths=1.5)
        ax.text(x, y, label, ha="center", va="center", fontsize=5,
                fontweight="bold", color="white", zorder=4)

    # Draw significant arrows
    for i, v1 in enumerate(vars_list):
        for j, v2 in enumerate(vars_list):
            if i == j:
                continue
            if gc_pvals[i, j] < 0.05:
                x1, y1 = positions[v1]
                x2, y2 = positions[v2]
                # Shorten arrow
                dx, dy = x2 - x1, y2 - y1
                length = np.sqrt(dx**2 + dy**2)
                shrink = 0.2
                x1s = x1 + shrink * dx / length
                y1s = y1 + shrink * dy / length
                x2s = x2 - shrink * dx / length
                y2s = y2 - shrink * dy / length

                width = 3.0 * gc_matrix[i, j] / gc_matrix.max()
                alpha = 0.4 + 0.5 * gc_matrix[i, j] / gc_matrix.max()
                ax.annotate("",
                            xy=(x2s, y2s), xytext=(x1s, y1s),
                            arrowprops=dict(arrowstyle="-|>", color="red",
                                            lw=width, alpha=alpha))

    ax.set_title("b) Kausale pilar (p < 0.05)")
    ax.set_facecolor("#fafafa")
    ax.axis("off")

    fig.suptitle("Fig. 5: Granger-kausalitet -- kva driv formendring?",
                 fontsize=9, fontweight="bold")
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    fig.savefig(FIG / "fig05_granger.pdf")
    fig.savefig(FIG / "fig05_granger.png")
    plt.close()

    # Report
    print("  Significant Granger causalities (p < 0.05):")
    for i, v1 in enumerate(vars_list):
        for j, v2 in enumerate(vars_list):
            if i != j and gc_pvals[i, j] < 0.05:
                print(f"    {v1} -> {v2}: p = {gc_pvals[i,j]:.4f}")


# ══════════════════════════════════════════════════════════════════
# EXPERIMENT 6: MORPHOSPACE VORONOI (FORBIDDEN ZONES)
# ══════════════════════════════════════════════════════════════════
def exp6_voronoi(df):
    """Voronoi tessellation of morphospace revealing empty/forbidden zones."""
    print("\n[EXP 6] MORPHOSPACE VORONOI")

    h = df["Høgde (cm)"].values
    w = df["Breidde (cm)"].values

    # Create 2D density map
    h_range = (30, 170)
    w_range = (15, 130)
    bins = 80

    hist, xedges, yedges = np.histogram2d(h, w, bins=bins, range=[h_range, w_range])
    hist_smooth = gaussian_filter(hist.T, sigma=2)
    hist_norm = hist_smooth / hist_smooth.max()

    # Find empty zones (density < threshold)
    threshold = 0.02

    fig, axes = plt.subplots(1, 2, figsize=(7, 4))

    # Left: Density with forbidden zone overlay
    ax = axes[0]
    xc = (xedges[:-1] + xedges[1:]) / 2
    yc = (yedges[:-1] + yedges[1:]) / 2
    X, Y = np.meshgrid(xc, yc)

    im = ax.pcolormesh(X, Y, hist_norm, cmap="magma_r", shading="auto")
    # Overlay forbidden zones as contour
    ax.contour(X, Y, hist_norm, levels=[threshold], colors=["cyan"],
               linewidths=1, linestyles="--")
    ax.contourf(X, Y, (hist_norm < threshold).astype(float),
                levels=[0.5, 1.5], colors=["cyan"], alpha=0.15)

    ax.set_xlabel("Hogde (cm)")
    ax.set_ylabel("Breidde (cm)")
    ax.set_title("a) Tetleikskart + forbodne sonar (cyan)")
    ax.set_facecolor("#fafafa")
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Normalisert tettleik")

    # Right: Scatter with century + convex hulls per century
    ax = axes[1]
    from scipy.spatial import ConvexHull

    for cent in CENT_ORDER:
        sub = df[df["Hundreår"] == cent]
        if len(sub) < 5:
            continue
        hc = sub["Høgde (cm)"].values
        wc = sub["Breidde (cm)"].values
        color = CENT_C.get(cent, "#999")

        ax.scatter(hc, wc, c=color, s=3, alpha=0.3, rasterized=True)

        # Convex hull
        try:
            points = np.column_stack([hc, wc])
            hull = ConvexHull(points)
            hull_pts = np.append(hull.vertices, hull.vertices[0])
            ax.plot(points[hull_pts, 0], points[hull_pts, 1],
                    color=color, linewidth=1, alpha=0.7)
        except Exception:
            pass

    ax.set_xlabel("Hogde (cm)")
    ax.set_ylabel("Breidde (cm)")
    ax.set_title("b) Konvekse hylster per hundre ar")
    ax.set_facecolor("#fafafa")

    # Legend
    handles = [mpatches.Patch(color=CENT_C[c], label=c) for c in CENT_ORDER
               if c in df["Hundreår"].values]
    ax.legend(handles=handles, fontsize=4, loc="upper right", ncol=2)

    fig.suptitle("Fig. 6: Morforommet -- tetleik, forbodne sonar og hylster",
                 fontsize=9, fontweight="bold")
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    fig.savefig(FIG / "fig06_voronoi.pdf")
    fig.savefig(FIG / "fig06_voronoi.png")
    plt.close()

    # Report forbidden zone area fraction
    total_cells = hist_norm.size
    empty_cells = (hist_norm < threshold).sum()
    print(f"  Forbidden zone: {empty_cells}/{total_cells} cells ({100*empty_cells/total_cells:.1f}%)")

    # Report hull areas per century
    for cent in CENT_ORDER:
        sub = df[df["Hundreår"] == cent]
        if len(sub) < 5:
            continue
        try:
            points = np.column_stack([sub["Høgde (cm)"].values, sub["Breidde (cm)"].values])
            hull = ConvexHull(points)
            print(f"  {cent}: hull area = {hull.volume:.0f} cm^2, n = {len(sub)}")
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════
# EXPERIMENT 7: MUTATION RATE -- HOW FAST DO FEATURES CHANGE?
# ══════════════════════════════════════════════════════════════════
def exp7_mutation_rate(df):
    """Mutation rate: rate of feature change between adjacent decades."""
    print("\n[EXP 7] MUTATION RATE")

    decades = sorted(df["Decade"].dropna().unique())
    dec_data = []

    for dec in decades:
        sub = df[df["Decade"] == dec]
        if len(sub) < 3:
            continue
        mat_set = set()
        for ml in sub["MatList"]:
            mat_set.update(ml)

        dec_data.append({
            "decade": int(dec),
            "h_mean": sub["Høgde (cm)"].mean(),
            "w_mean": sub["Breidde (cm)"].mean(),
            "mat_set": mat_set,
            "n": len(sub),
        })

    # Compute "mutation rates" between adjacent decades
    mut_rates = []
    for i in range(1, len(dec_data)):
        d0, d1 = dec_data[i-1], dec_data[i]
        dt = d1["decade"] - d0["decade"]
        if dt == 0:
            continue

        # Dimensional mutation: absolute change in H + W
        dH = abs(d1["h_mean"] - d0["h_mean"])
        dW = abs(d1["w_mean"] - d0["w_mean"])
        dim_mut = (dH + dW) / dt  # cm/year

        # Material mutation: Jaccard distance
        union = d0["mat_set"] | d1["mat_set"]
        inter = d0["mat_set"] & d1["mat_set"]
        jacc = 1 - len(inter) / len(union) if union else 0

        mut_rates.append({
            "decade": d1["decade"],
            "dim_mut": dim_mut,
            "mat_mut": jacc,
            "combined": dim_mut * 10 + jacc,  # weighted combo
        })

    mdf = pd.DataFrame(mut_rates)

    fig, axes = plt.subplots(2, 1, figsize=(7, 5), sharex=True)

    # Top: dimensional mutation rate
    ax = axes[0]
    ax.bar(mdf["decade"], mdf["dim_mut"], width=8, color="#1565c0", alpha=0.7)
    ax.axhline(mdf["dim_mut"].mean(), color="red", linestyle="--", linewidth=0.8,
               label=f"Snitt = {mdf['dim_mut'].mean():.3f}")
    ax.set_ylabel("Dimensjonsmutasjon\n(cm/ar)")
    ax.set_title("a) Dimensjonal endringsrate")
    ax.legend(fontsize=5)
    ax.set_facecolor("#fafafa")

    # Highlight extreme periods
    top5 = mdf.nlargest(5, "dim_mut")
    for _, row in top5.iterrows():
        ax.annotate(f"{int(row['decade'])}s", (row["decade"], row["dim_mut"]),
                    fontsize=5, color="red", fontweight="bold", ha="center",
                    xytext=(0, 3), textcoords="offset points")

    # Bottom: material mutation (Jaccard)
    ax = axes[1]
    ax.bar(mdf["decade"], mdf["mat_mut"], width=8, color="#e65100", alpha=0.7)
    ax.axhline(mdf["mat_mut"].mean(), color="red", linestyle="--", linewidth=0.8,
               label=f"Snitt = {mdf['mat_mut'].mean():.3f}")
    ax.set_ylabel("Materialmutasjon\n(Jaccard-avstand)")
    ax.set_xlabel("Tiar")
    ax.set_title("b) Materiell endringsrate")
    ax.legend(fontsize=5)
    ax.set_facecolor("#fafafa")

    fig.suptitle("Fig. 7: Mutasjonsrate -- kor raskt endrar formen seg?",
                 fontsize=9, fontweight="bold")
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    fig.savefig(FIG / "fig07_mutasjonsrate.pdf")
    fig.savefig(FIG / "fig07_mutasjonsrate.png")
    plt.close()

    # Report
    print(f"  Mean dimensional mutation: {mdf['dim_mut'].mean():.4f} cm/yr")
    print(f"  Mean material mutation: {mdf['mat_mut'].mean():.4f} Jaccard/decade")
    print(f"  Peak dimensional decades: {top5['decade'].tolist()}")
    print(f"  Peak material decades: {mdf.nlargest(5, 'mat_mut')['decade'].tolist()}")


# ══════════════════════════════════════════════════════════════════
# EXPERIMENT 8: TRANSFER ENTROPY -- INFORMATION FLOW
# ══════════════════════════════════════════════════════════════════
def exp8_transfer_entropy(df):
    """Transfer entropy: directed information flow between features over time."""
    print("\n[EXP 8] TRANSFER ENTROPY")

    # Build decade-level time series
    decades = sorted(df["Decade"].dropna().unique())
    ts = {"H": [], "W": [], "D": [], "MC": [], "H_ent": []}

    for dec in decades:
        sub = df[df["Decade"] == dec]
        if len(sub) < 3:
            continue
        ts["H"].append(sub["Høgde (cm)"].mean())
        ts["W"].append(sub["Breidde (cm)"].mean())
        d_val = sub["Djupn (cm)"].dropna()
        ts["D"].append(d_val.mean() if len(d_val) > 0 else np.nan)
        ts["MC"].append(sub["MatCount"].mean())

        all_m = []
        for ml in sub["MatList"]:
            all_m.extend(ml)
        c = Counter(all_m)
        total = sum(c.values())
        h_ent = -sum((v/total)*math.log2(v/total) for v in c.values() if v > 0) if total > 0 else 0
        ts["H_ent"].append(h_ent)

    # Convert to arrays, forward-fill NaN
    for k in ts:
        arr = np.array(ts[k], dtype=float)
        mask = np.isnan(arr)
        if mask.any():
            arr[mask] = np.nanmean(arr)
        ts[k] = arr

    n = len(ts["H"])
    vars_list = list(ts.keys())
    var_labels = ["Hogde", "Breidde", "Djupn", "Materialtal", "Mat. entropi"]

    # Simple transfer entropy estimate: TE(X->Y) = I(Y_t+1; X_t | Y_t)
    # Approximated via correlation-based proxy
    def transfer_entropy_proxy(x, y, lag=1):
        """Proxy: partial correlation of Y_future with X_past given Y_past."""
        if len(x) < lag + 3:
            return 0.0
        y_future = y[lag:]
        x_past = x[:-lag]
        y_past = y[:-lag]

        # Correlation Y_future with X_past
        r_yx, _ = pearsonr(y_future, x_past)
        # Correlation Y_future with Y_past
        r_yy, _ = pearsonr(y_future, y_past)
        # Correlation X_past with Y_past
        r_xy, _ = pearsonr(x_past, y_past)

        # Partial correlation (X -> Y | Y_past)
        denom = np.sqrt((1 - r_yy**2) * (1 - r_xy**2))
        if denom < 1e-10:
            return 0.0
        partial_r = (r_yx - r_yy * r_xy) / denom
        # Convert to mutual information analog
        te = -0.5 * np.log(1 - partial_r**2 + 1e-10)
        return max(0, te)

    te_matrix = np.zeros((len(vars_list), len(vars_list)))
    for i, v1 in enumerate(vars_list):
        for j, v2 in enumerate(vars_list):
            if i == j:
                continue
            te_matrix[i, j] = transfer_entropy_proxy(ts[v1], ts[v2])

    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(te_matrix, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(len(var_labels)))
    ax.set_xticklabels(var_labels, rotation=45, ha="right", fontsize=6)
    ax.set_yticks(range(len(var_labels)))
    ax.set_yticklabels(var_labels, fontsize=6)
    ax.set_xlabel("Mottakar (Y)")
    ax.set_ylabel("Sendar (X)")

    for i in range(len(var_labels)):
        for j in range(len(var_labels)):
            val = te_matrix[i, j]
            color = "white" if val > te_matrix.max() * 0.6 else "black"
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    fontsize=5, color=color)

    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Transfer-entropi (bits)", fontsize=6)

    ax.set_title("Fig. 8: Transfer-entropi -- informasjonsflyt mellom eigenskapar",
                 fontsize=9, fontweight="bold")
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    fig.savefig(FIG / "fig08_transfer_entropi.pdf")
    fig.savefig(FIG / "fig08_transfer_entropi.png")
    plt.close()

    # Report top flows
    flows = []
    for i, v1 in enumerate(vars_list):
        for j, v2 in enumerate(vars_list):
            if i != j:
                flows.append((v1, v2, te_matrix[i, j]))
    flows.sort(key=lambda x: -x[2])
    print("  Top information flows:")
    for v1, v2, te in flows[:8]:
        print(f"    {v1} -> {v2}: TE = {te:.4f} bits")


# ══════════════════════════════════════════════════════════════════
# EXPERIMENT 9: STYLE "GENOME" ALIGNMENT
# ══════════════════════════════════════════════════════════════════
def exp9_genome_alignment(df):
    """Encode each style as a binary genome and visualize alignment."""
    print("\n[EXP 9] STYLE GENOME ALIGNMENT")

    # Get all materials
    all_mats = set()
    for ml in df["MatList"]:
        all_mats.update(ml)
    all_mats = sorted(all_mats)

    # Get styles with enough data
    style_counts = df["Stilperiode"].value_counts()
    styles = [s for s in style_counts.index if style_counts[s] >= 15]

    # Order by median year
    style_years = {}
    for s in styles:
        style_years[s] = df[df["Stilperiode"] == s]["Year"].median()
    styles = sorted(styles, key=lambda x: style_years.get(x, 0))

    # Build binary genome: 1 if material present in >10% of style's chairs
    genomes = {}
    for style in styles:
        sub = df[df["Stilperiode"] == style]
        n = len(sub)
        mat_counts = Counter()
        for ml in sub["MatList"]:
            mat_counts.update(ml)
        genome = np.zeros(len(all_mats))
        for i, m in enumerate(all_mats):
            if mat_counts[m] / n > 0.10:
                genome[i] = 1
        genomes[style] = genome

    # Build matrix
    genome_matrix = np.array([genomes[s] for s in styles])

    # Filter to materials that appear in at least 2 styles
    mat_presence = genome_matrix.sum(axis=0)
    active_mats = mat_presence >= 2
    genome_filtered = genome_matrix[:, active_mats]
    mat_names = [all_mats[i] for i in range(len(all_mats)) if active_mats[i]]

    fig, ax = plt.subplots(figsize=(7, 5))

    # Heatmap
    cmap = mcolors.ListedColormap(["#f5f5f5", "#1565c0"])
    im = ax.imshow(genome_filtered, cmap=cmap, aspect="auto", interpolation="nearest")

    ax.set_yticks(range(len(styles)))
    ax.set_yticklabels(styles, fontsize=4)
    ax.set_xticks(range(len(mat_names)))
    ax.set_xticklabels(mat_names, rotation=90, fontsize=3)

    # Add grid
    ax.set_xticks(np.arange(-0.5, len(mat_names)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(styles)), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.3)

    # Side bar: number of "genes" active
    gene_counts = genome_filtered.sum(axis=1)
    for i, gc in enumerate(gene_counts):
        ax.text(len(mat_names) + 0.5, i, f"{int(gc)}", fontsize=4,
                va="center", color="#1565c0", fontweight="bold")

    ax.set_title("Fig. 9: Stilgenomet -- materialisk DNA per stilperiode",
                 fontsize=9, fontweight="bold")
    ax.set_xlabel("Material-gen")
    ax.set_ylabel("Stilperiode (kronologisk)")
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    fig.savefig(FIG / "fig09_genom.pdf")
    fig.savefig(FIG / "fig09_genom.png")
    plt.close()

    print(f"  {len(styles)} styles, {len(mat_names)} active material-genes")
    print(f"  Most gene-rich: {styles[np.argmax(gene_counts)]} ({int(max(gene_counts))} genes)")
    print(f"  Most gene-poor: {styles[np.argmin(gene_counts)]} ({int(min(gene_counts))} genes)")

    # "Conserved genes" -- materials present in ALL styles
    conserved = genome_filtered.min(axis=0)
    conserved_names = [mat_names[i] for i in range(len(mat_names)) if conserved[i] == 1]
    print(f"  Universally conserved genes: {conserved_names}")

    # "Novel genes" -- materials unique to one style
    for s_idx, style in enumerate(styles):
        unique = []
        for m_idx, m in enumerate(mat_names):
            if genome_filtered[s_idx, m_idx] == 1 and genome_filtered[:, m_idx].sum() == 1:
                unique.append(m)
        if unique:
            print(f"  Unique to {style}: {unique}")


# ══════════════════════════════════════════════════════════════════
# EXPERIMENT 10: THE MASTER PLOT -- ENTROPY vs COMPLEXITY vs TIME
# ══════════════════════════════════════════════════════════════════
def exp10_master(df):
    """The master plot: entropy x complexity x time as a 3D trajectory."""
    print("\n[EXP 10] MASTER PLOT")

    decades = sorted(df["Decade"].dropna().unique())
    trajectory = []

    for dec in decades:
        sub = df[df["Decade"] == dec]
        if len(sub) < 3:
            continue

        # Axis 1: Material entropy
        all_m = []
        for ml in sub["MatList"]:
            all_m.extend(ml)
        c = Counter(all_m)
        total = sum(c.values())
        h_ent = -sum((v/total)*math.log2(v/total) for v in c.values() if v > 0) if total > 0 else 0

        # Axis 2: Dimensional complexity (CV of all dims)
        h_vals = sub["Høgde (cm)"].dropna().values
        w_vals = sub["Breidde (cm)"].dropna().values
        cv_h = np.std(h_vals)/np.mean(h_vals) if len(h_vals) > 1 and np.mean(h_vals) > 0 else 0
        cv_w = np.std(w_vals)/np.mean(w_vals) if len(w_vals) > 1 and np.mean(w_vals) > 0 else 0
        complexity = (cv_h + cv_w) / 2

        # Axis 3: Material richness (unique materials / ln(n))
        n_unique = len(c)
        margalef = (n_unique - 1) / np.log(total) if total > 1 else 0

        trajectory.append({
            "decade": int(dec),
            "entropy": h_ent,
            "complexity": complexity,
            "margalef": margalef,
            "n": len(sub),
        })

    tdf = pd.DataFrame(trajectory)

    # Assign century color
    tdf["century"] = tdf["decade"].apply(
        lambda x: f"{(x // 100) * 100}-talet" if x < 2000 else "2000-talet"
    )

    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, projection="3d")

    # Draw trajectory
    colors = [CENT_C.get(c, "#999") for c in tdf["century"]]

    ax.plot(tdf["entropy"], tdf["complexity"], tdf["margalef"],
            color="#cccccc", linewidth=0.5, alpha=0.5)
    sc = ax.scatter(tdf["entropy"], tdf["complexity"], tdf["margalef"],
                    c=colors, s=tdf["n"] * 0.5 + 10, alpha=0.85,
                    edgecolors="white", linewidths=0.3, depthshade=True)

    # Arrows for direction
    for i in range(0, len(tdf) - 1, 4):
        r0, r1 = tdf.iloc[i], tdf.iloc[i + 1]
        ax.quiver(r0["entropy"], r0["complexity"], r0["margalef"],
                  r1["entropy"] - r0["entropy"],
                  r1["complexity"] - r0["complexity"],
                  r1["margalef"] - r0["margalef"],
                  color=colors[i], alpha=0.5, arrow_length_ratio=0.3,
                  linewidth=0.8)

    # Label endpoints
    ax.text(tdf.iloc[0]["entropy"], tdf.iloc[0]["complexity"],
            tdf.iloc[0]["margalef"], f"  {int(tdf.iloc[0]['decade'])}s",
            fontsize=5, fontweight="bold")
    ax.text(tdf.iloc[-1]["entropy"], tdf.iloc[-1]["complexity"],
            tdf.iloc[-1]["margalef"], f"  {int(tdf.iloc[-1]['decade'])}s",
            fontsize=5, fontweight="bold")

    ax.set_xlabel("Materialentropi H' (bits)", labelpad=8)
    ax.set_ylabel("Dimensjonskompleksitet (CV)", labelpad=8)
    ax.set_zlabel("Margalef-rikdom", labelpad=5)
    ax.set_title("Fig. 10: Meisterplottet -- entropi x kompleksitet x rikdom",
                 fontsize=9, fontweight="bold")
    ax.view_init(elev=25, azim=135)
    fig.patch.set_facecolor("white")

    handles = [mpatches.Patch(color=CENT_C[c], label=c) for c in CENT_ORDER
               if c in tdf["century"].values]
    ax.legend(handles=handles, loc="upper left", fontsize=5)

    plt.tight_layout()
    fig.savefig(FIG / "fig10_meisterplott.pdf")
    fig.savefig(FIG / "fig10_meisterplott.png")
    plt.close()

    print(f"  Trajectory: {len(tdf)} decades")
    print(f"  Entropy range: {tdf['entropy'].min():.2f} - {tdf['entropy'].max():.2f}")
    print(f"  Complexity range: {tdf['complexity'].min():.3f} - {tdf['complexity'].max():.3f}")
    print(f"  Margalef range: {tdf['margalef'].min():.2f} - {tdf['margalef'].max():.2f}")


# ══════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("ARTIKKEL X: FORMENS GENOM -- JAILBREAK EDITION")
    print("10 rapid prototype experiments")
    print("=" * 70)

    df = load()

    exp1_phylogenetics(df)
    exp2_fft_spectrum(df)
    exp3_zipf(df)
    exp4_network(df)
    exp5_granger(df)
    exp6_voronoi(df)
    exp7_mutation_rate(df)
    exp8_transfer_entropy(df)
    exp9_genome_alignment(df)
    exp10_master(df)

    print("\n" + "=" * 70)
    print("ALL 10 EXPERIMENTS COMPLETE")
    print(f"Output: {FIG}")
    print("=" * 70)


if __name__ == "__main__":
    main()
