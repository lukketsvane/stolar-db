"""35_figur_periode_stoff.py - rutenettet til den åttande prøva: snittstolen frå sida for kvar periode og kvart stoff.

  python analyse/35_figur_periode_stoff.py   -> analyse/figurar/png/prove8_periode_stoff.png
"""
import json, os, sys
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
UT = os.path.join(HER, "figurar", "png")
FONTMAPPE = os.path.join(os.path.dirname(os.path.dirname(HER)), "FORML-RE", "traktat", "layout", "fonts")
for f in ("EBGaramond12-Regular.otf", "EBGaramond12-Italic.otf"):
    if os.path.exists(os.path.join(FONTMAPPE, f)):
        fm.fontManager.addfont(os.path.join(FONTMAPPE, f))
SERIF = "EB Garamond" if any(f.name == "EB Garamond" for f in fm.fontManager.ttflist) else "Georgia"
MONO, FG, DIM = "Consolas", "#0c0c0c", "#8a8a8a"
plt.rcParams.update({"font.family": SERIF, "text.color": FG, "figure.facecolor": "white", "savefig.facecolor": "white"})

D = json.load(open(os.path.join(HER, "forsegla8", "FIGURDATA.json"), encoding="utf-8"))["stolar"]
R = json.load(open(os.path.join(HER, "forsegla8", "RESULTAT.json"), encoding="utf-8"))["resultat"]
z = np.load(os.path.join(HER, "data", "mesh_silhuettar.npz"))
SIDE = dict(zip(z["ids"], np.unpackbits(z["side"], axis=-1)))
PER = [("P1", "Art deco og funksjonalisme"), ("P2", "Modernisme"), ("P3", "Postmodernisme og samtid")]
MAT = [("WOOD", "Tre"), ("LINE", "Metall"), ("SHEET", "Plast og kryssfiner")]
HH = 120


def snitt(ids):
    acc = np.zeros((HH, 160), np.float32)
    for i in ids:
        img = SIDE[i][:HH].astype(np.float32)
        k = np.where(img.any(0))[0]
        acc += np.roll(img, 80 - (k[0] + k[-1] + 1) // 2, axis=1)
    return acc / max(len(ids), 1)


fig = plt.figure(figsize=(7.4, 8.4))
W, H0, X0, Y0, GX, GY = 0.285, 0.235, 0.12, 0.10, 0.012, 0.025
for r, (m, mn) in enumerate(MAT):
    for c, (p, pn) in enumerate(PER):
        ids = [s["id"] for s in D if s["mat"] == m and s["per"] == p and s["id"] in SIDE]
        P = snitt(ids)
        ax = fig.add_axes([X0 + c * (W + GX), Y0 + (2 - r) * (H0 + GY), W, H0])
        ax.imshow(P ** 0.75, cmap="gray_r", vmin=0, vmax=1, origin="lower", extent=[0, 160, 0, HH], interpolation="bilinear")
        ax.contour(np.arange(160) + .5, np.arange(HH) + .5, cv2.GaussianBlur(P, (0, 0), 1.0), levels=[0.5], colors=FG, linewidths=0.8)
        ax.plot([25, 135], [0, 0], color=FG, lw=0.7)
        ax.set_xlim(25, 135)
        ax.set_ylim(-2, HH)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.text(132, HH - 4, "%d" % len(ids), family=MONO, fontsize=7, color=DIM, ha="right", va="top")
        if r == 0:
            ax.text(80, HH + 6, pn, fontsize=10.5, ha="center", va="bottom")
        if c == 0:
            ax.text(18, HH / 2, mn, fontsize=10.5, ha="right", va="center", rotation=90)
p1, p2 = R["P1_stilmerka"], R["P2_aarsbolkane"]
k2 = lambda v: ("%.2f" % v).replace(".", ",")
fig.text(0.03, 0.99, "Tida og stoffet veg like mykje", fontsize=22, va="top")
fig.text(0.03, 0.945, "Ein stol etter 1915 kan føreseiast like godt frå perioden han er laga i som frå stoffet han er laga av.", fontsize=10.2, va="top")
fig.text(0.03, 0.922, "Feilen med perioden er %s av feilen med stoffet etter stil, %s etter årsbolk." % (k2(p1["Q"]), k2(p2["Q"])), fontsize=10.2, va="top")
fig.text(0.03, 0.04, "snittstolen frå sida for kvar celle, éin per modell · linja: der halvparten av stolane har materiale · tal: stolar i cella",
         family=MONO, fontsize=6.6, color=DIM)
fig.text(0.03, 0.024, "føresegn: middelet av dei andre stolane i same periode og museum mot same stoff og museum · formlære, føreseiing 11 · forsegla prøve 8",
         family=MONO, fontsize=6.6, color=DIM)
os.makedirs(UT, exist_ok=True)
p = os.path.join(UT, "prove8_periode_stoff.png")
fig.savefig(p, dpi=240, bbox_inches="tight", pad_inches=0.22)
print(p)
