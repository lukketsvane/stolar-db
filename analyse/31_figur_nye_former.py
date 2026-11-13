"""31_figur_nye_former.py - figuren til den sjette prøva: dei nyaste stolane etter 1900 mot like mange av dei andre.

Kvar stol er sideomrisset frå 3D-modellen. Den stipla lina går gjennom medianen for setehøgda hos dei andre.
Teikna frå forsegla6/FIGURDATA.json etter opninga.

  python analyse/31_figur_nye_former.py   -> analyse/figurar/png/prove6_nye_former.png
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

D = json.load(open(os.path.join(HER, "forsegla6", "FIGURDATA.json"), encoding="utf-8"))["stolar"]
R = json.load(open(os.path.join(HER, "forsegla6", "RESULTAT.json"), encoding="utf-8"))
z = np.load(os.path.join(HER, "data", "mesh_silhuettar.npz"))
SIDE = dict(zip(z["ids"], np.unpackbits(z["side"], axis=-1)))
nye = sorted([s for s in D if s["ny"]], key=lambda s: (s["aar"], s["id"]))
andre = [s for s in D if not s["ny"]]
rng = np.random.default_rng(20261113)
andre = sorted([andre[i] for i in rng.choice(len(andre), len(nye), replace=False)], key=lambda s: (s["aar"], s["id"]))
SM = R["median"]["resten_sete"]
KOL, CW, CH = 14, 80, 128


def blokk(ax, stolar, y_topp):
    rader = (len(stolar) + KOL - 1) // KOL
    for r in range(rader):
        y0 = y_topp - (r + 1) * (CH + 16)
        ax.plot([0, KOL * CW], [y0, y0], color=FG, lw=0.5)
        ax.plot([0, KOL * CW], [y0 + SM, y0 + SM], color=DIM, lw=0.5, dashes=(3, 2.5))
        for c, s in enumerate(stolar[r * KOL:(r + 1) * KOL]):
            img = SIDE[s["id"]][:CH]
            k = np.where(img.any(0))[0]
            x0 = c * CW + CW / 2 - (k[0] + k[-1] + 1) / 2
            ax.imshow(np.where(img > 0, 1.0, np.nan), cmap="gray_r", vmin=0, vmax=1, origin="lower",
                      extent=[x0, x0 + 160, y0, y0 + CH], interpolation="nearest", zorder=2)
            ax.text(c * CW + CW / 2, y0 - 3, str(s["aar"]), family=MONO, fontsize=4.6, color=DIM, ha="center", va="top")
    return y_topp - rader * (CH + 16)


rader = 2 * ((len(nye) + KOL - 1) // KOL)
H0 = 1.95 + rader * 0.935
fig = plt.figure(figsize=(7.4, H0))
ax = fig.add_axes([0.02, 0.35 / H0, 0.96, 1 - 1.75 / H0])
y = 0
ax.text(0, y + 8, "Dei %d nyaste formene etter 1900" % len(nye), fontsize=12, va="bottom")
y = blokk(ax, nye, y)
y -= 78
ax.text(0, y + 8, "%d av dei andre, trekte tilfeldig" % len(andre), fontsize=12, va="bottom")
y = blokk(ax, andre, y)
ax.set_xlim(-4, KOL * CW + 4)
ax.set_ylim(y - 14, 40)
ax.set_aspect("equal")
ax.axis("off")
sp = R["spreiing"]
k2 = lambda v: ("%.2f" % v).replace(".", ",")
fig.text(0.02, 1 - 0.18 / H0, "Dei nyaste stolane flyttar setet", fontsize=22, va="top")
fig.text(0.02, 1 - 0.62 / H0, "Føreseiinga var at nye former skulle halde setet og sleppe høgda. Det var omvendt:", fontsize=10.2, va="top")
fig.text(0.02, 1 - 0.84 / H0, "setehøgda spreier seg %s mot %s hos dei andre, totalhøgda %s mot %s." % (k2(sp["nye_sete"]), k2(sp["resten_sete"]), k2(sp["nye_H"]), k2(sp["resten_H"])),
         fontsize=10.2, va="top")
fig.text(0.02, 0.012, "nyheit: avstanden til den likaste stolen som er minst 10 år eldre, heile stolen med setet · stipla: median setehøgd hos dei andre (%d cm) · forsegla prøve 6, N1 til N3 slo feil" % round(SM),
         family=MONO, fontsize=5.6, color=DIM)
os.makedirs(UT, exist_ok=True)
p = os.path.join(UT, "prove6_nye_former.png")
fig.savefig(p, dpi=240, bbox_inches="tight", pad_inches=0.2)
print(p, len(nye))
