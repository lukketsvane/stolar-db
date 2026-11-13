"""29_figur_regenerasjon.py - langtidseksponering til den femte prøva: stolane i tre og i nye material langs tida.

Kvar stol er sideomrisset frå 3D-modellen, sett der året hans er. Der mange stolar dekkjer same punkt, blir
biletet mørkt. Teikna frå forsegla5/FIGURDATA.json etter opninga.

  python analyse/29_figur_regenerasjon.py   -> analyse/figurar/png/prove5_setet_held.png
"""
import json, os, sys
import numpy as np
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

D = json.load(open(os.path.join(HER, "forsegla5", "FIGURDATA.json"), encoding="utf-8"))["stolar"]
R = json.load(open(os.path.join(HER, "forsegla5", "RESULTAT.json"), encoding="utf-8"))
z = np.load(os.path.join(HER, "data", "mesh_silhuettar.npz"))
SIDE = dict(zip(z["ids"], np.unpackbits(z["side"], axis=-1)))
HH = 140
PER = (("tidleg", (1920, 1949), "1920 til 1949"), ("seint", (1965, 1999), "1965 til 1999"))
RADER = (("tre", "Tre"), ("nye", "Røyr, kryssfiner og plast"))


def stabel(mat, per):
    ss = [s for s in D if s["mat"] == mat and s["per"] == per and s["id"] in SIDE]
    acc = np.zeros((HH, 160), np.float32)
    for s in ss:
        img = SIDE[s["id"]][:HH].astype(np.float32)
        k = np.where(img.any(0))[0]
        acc += np.roll(img, 80 - (k[0] + k[-1] + 1) // 2, axis=1)
    return acc / max(len(ss), 1), ss


fig = plt.figure(figsize=(7.4, 9.0))
CW, CH, X0, Y0 = 0.47, 0.36, 0.03, 0.085
sp = R["spreiing"]
k2 = lambda v: ("%.2f" % v).replace(".", ",")
for r, (mat, namn) in enumerate(RADER):
    for c, (per, _, ptekst) in enumerate(PER):
        P, ss = stabel(mat, per)
        ax = fig.add_axes([X0 + c * (CW + 0.02), Y0 + (1 - r) * (CH + 0.075), CW, CH])
        ax.imshow(P ** 0.75, cmap="gray_r", vmin=0, vmax=1, origin="lower", extent=[0, 160, 0, HH], interpolation="bilinear")
        ax.contour(np.arange(160) + .5, np.arange(HH) + .5, P, levels=[0.5], colors=FG, linewidths=0.7)
        for s in ss:                                         # strekar: setehøgd og totalhøgd for kvar stol
            ax.plot([128, 136], [s["sete"]] * 2, color=FG, lw=0.5, alpha=0.35, solid_capstyle="butt")
            if s["H"] < HH:
                ax.plot([144, 152], [s["H"]] * 2, color=FG, lw=0.5, alpha=0.35, solid_capstyle="butt")
        ax.text(132, -3, "sete", family=MONO, fontsize=6, color=DIM, ha="center", va="top")
        ax.text(148, -3, "høgd", family=MONO, fontsize=6, color=DIM, ha="center", va="top")
        ax.plot([14, 156], [0, 0], color=FG, lw=0.7)
        ax.set_xlim(14, 158)
        ax.set_ylim(-12, HH)
        ax.set_aspect("equal")
        ax.axis("off")
        if r == 0:
            ax.text(14, HH + 4, ptekst, family=MONO, fontsize=7.4, color=FG, va="bottom")
        if c == 0:
            ax.text(14, HH - 2, namn, fontsize=12.5, va="top")
        ax.text(14, -12, "%d stolar · spreiing sete %s, høgd %s" % (len(ss), k2(sp["%s_%s_sete" % (mat, per)]), k2(sp["%s_%s_H" % (mat, per)])),
                family=MONO, fontsize=6.4, color=FG, va="top")
fig.text(0.03, 1.005, "Høgda spreier seg, setet gjer det ikkje", fontsize=22, va="top")
fig.text(0.03, 0.965, "Føreseiinga var at setet i nye material skulle spreie seg i den første generasjonen og så samle seg.", fontsize=10.2, va="top")
fig.text(0.03, 0.945, "Det spreidde seg like mykje då som seinare. Det som spreier seg med tida, er høgda, i tre som i nye material.", fontsize=10.2, va="top")
fig.text(0.03, 0.040, "alle stolane i kvar rute lagde oppå kvarandre frå sida, éin per modell · linja: der halvparten av stolane har materiale",
         family=MONO, fontsize=6.6, color=DIM)
fig.text(0.03, 0.024, "strekane: setehøgd og totalhøgd for kvar stol · spreiing: kvartilavstand delt på median · forsegla prøve 5: R1 og R2 slo feil, R3 heldt",
         family=MONO, fontsize=6.6, color=DIM)
os.makedirs(UT, exist_ok=True)
p = os.path.join(UT, "prove5_setet_held.png")
fig.savefig(p, dpi=240, bbox_inches="tight", pad_inches=0.22)
print(p)
