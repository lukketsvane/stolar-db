"""24_figur_met.py - krakken i to museum: den andre prøva (V&A og Nasjonalmuseet) mot den tredje (The Met).

  python analyse/24_figur_met.py      Ut: analyse/figurar/png/prove3_krakk.png
Teiknar berre det som alt er rekna og lagra i forsegla2/ og forsegla3/.
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
FONTMAPPE = os.path.join(os.path.dirname(os.path.dirname(HER)), "FORML-RE", "traktat", "layout", "fonts")
for f in ("EBGaramond12-Regular.otf", "EBGaramond12-Italic.otf"):
    if os.path.exists(os.path.join(FONTMAPPE, f)):
        fm.fontManager.addfont(os.path.join(FONTMAPPE, f))
SERIF = "EB Garamond" if any(f.name == "EB Garamond" for f in fm.fontManager.ttflist) else "Georgia"
MONO = "Consolas"
FG, DIM, LYS = "#0c0c0c", "#777777", "#f1f1f1"
plt.rcParams.update({"font.family": SERIF, "text.color": FG, "axes.edgecolor": FG, "figure.facecolor": "white",
                     "savefig.facecolor": "white", "axes.linewidth": 0.6})
tal = lambda x, d=1: ("%.*f" % (d, x)).replace(".", ",")

f2 = json.load(open(os.path.join(HER, "forsegla2", "FIGURDATA.json"), encoding="utf-8"))["t5_krakk"]
r2 = json.load(open(os.path.join(HER, "forsegla2", "RESULTAT.json"), encoding="utf-8"))["modular"]["t5_krakk"]
f3 = json.load(open(os.path.join(HER, "forsegla3", "FIGURDATA.json"), encoding="utf-8"))
r3 = json.load(open(os.path.join(HER, "forsegla3", "RESULTAT.json"), encoding="utf-8"))["M1_krakk"]
q1, q3 = f2["tersklar"]["P1"]
stol = [(a, v) for a, v in f2["stolsete_punkt_aar_cm"] if a]

panel = [("V&A og Nasjonalmuseet", [(p["aar"], p["H"]) for p in f2["krakk_punkt"] if p["status"] == "primaer" and p["aar"]],
          r2, "heldt"),
         ("The Met", [(a, h) for a, h, _ in f3["krakk"] if a], r3, "slo feil")]
fig = plt.figure(figsize=(7.6, 6.4))
for i, (namn, pkt, res, dom) in enumerate(panel):
    ax = fig.add_axes([0.08 + i * 0.46, 0.15, 0.40, 0.58])
    ax.axhspan(q1, q3, color=LYS, lw=0)
    ax.scatter([a for a, _ in stol], [v for _, v in stol], s=2.5, color="#b8b8b8", lw=0, zorder=2)
    ax.scatter([a for a, _ in pkt], [h for _, h in pkt], s=16, color=FG, lw=0, zorder=3)
    ax.set_xlim(1480, 2030)
    ax.set_ylim(0, 100)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xticks([1500, 1700, 1900])
    ax.set_yticks([0, 45, 90] if i == 0 else [])
    if i:
        ax.spines["left"].set_visible(False)
    ax.tick_params(length=2.5, width=0.5, labelsize=7.5, colors=DIM)
    for t in ax.get_xticklabels() + ax.get_yticklabels():
        t.set_family(MONO)
    p = {x["namn"][:2]: x for x in res["primaer"]}
    ax.text(1485, 97, namn, family=SERIF, fontsize=12.5, va="top")
    ax.text(1485, 90, "%d krakkar · %s" % (len(pkt) if i else res["n"], dom), family=MONO, fontsize=7.2, color=FG, va="top")
    ax.text(1485, 85, "median %s cm · spreiing %s" % (tal(p["P1"]["verdi"]), tal(p["P2"]["verdi"], 3)),
            family=MONO, fontsize=7.2, color=DIM, va="top")
    if i:
        ax.annotate("vindaugekrakkar\nmed sidestykke", xy=(1806, 81), xytext=(1855, 93), family=MONO, fontsize=6.4,
                    color=DIM, arrowprops=dict(arrowstyle="-", color=DIM, lw=0.5))
fig.text(0.08, 0.93, "Krakken i to museum", fontsize=23, family=SERIF)
fig.text(0.08, 0.885, "Same føreseiing, same tersklar. I Met held medianen, men spreiinga er dobbelt så stor som kravet.",
         fontsize=11.2, family=SERIF)
fig.text(0.08, 0.83, "krav: median 41 til 46 cm, robust spreiing under 0,126, øvre grense under 0,174", family=MONO,
         fontsize=7.4, color=FG)
for j, s in enumerate(["svart: krakkar i utvalet, høgd i cm · grå: setehøgda på 283 stolar i V&A · band: midtre halvdel av stolseta",
                       "Met: dei vestlege møbelavdelingane, MetObjects.csv d31d26f · forsegla før henting, opna éin gong 13.11.2026",
                       "merknaden om vindaugekrakkar er lesen etter opninga og endrar ikkje domen"]):
    fig.text(0.08, 0.075 - 0.02 * j, s, family=MONO, fontsize=7.0, color=DIM)
p = os.path.join(HER, "figurar", "png", "prove3_krakk.png")
fig.savefig(p, dpi=220, bbox_inches="tight", pad_inches=0.25)
print("skrive:", p)
