"""27_figur_to_alder.py - bogefiguren til den fjerde prøva: kor langt attende overdelen og understellet hugsar.

Kvar stol er ein boge frå året han vart laga til medianåret for dei sju likaste overdelane (over linja)
og dei sju likaste understella (under linja). Teikna frå forsegla4/FIGURDATA.json etter opninga.

  python analyse/27_figur_to_alder.py   -> analyse/figurar/png/prove4_to_alder.png
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import font_manager as fm

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
UT = os.path.join(HER, "figurar", "png")
FONTMAPPE = os.path.join(os.path.dirname(os.path.dirname(HER)), "FORML-RE", "traktat", "layout", "fonts")
for f in os.listdir(FONTMAPPE) if os.path.isdir(FONTMAPPE) else []:
    if f.endswith((".otf", ".ttf")):
        fm.fontManager.addfont(os.path.join(FONTMAPPE, f))
namn = {f.name for f in fm.fontManager.ttflist}
SERIF = "Literata" if "Literata" in namn else "EB Garamond" if "EB Garamond" in namn else "Georgia"
MONO = "IBM Plex Mono" if "IBM Plex Mono" in namn else "Consolas"
FG, DIM = "#0c0c0c", "#8a8a8a"
plt.rcParams.update({"font.family": SERIF, "text.color": FG, "figure.facecolor": "white", "savefig.facecolor": "white"})

D = json.load(open(os.path.join(HER, "forsegla4", "FIGURDATA.json"), encoding="utf-8"))["stolar"]
R = json.load(open(os.path.join(HER, "forsegla4", "RESULTAT.json"), encoding="utf-8"))
T0, T1 = 1540, 2030
rng = np.random.default_rng(3)


def boge(a, b, opp):
    """Halvsirkel frå a til b, over (opp=1) eller under (opp=-1) linja."""
    r = abs(b - a) / 2
    if r < 0.5:
        return None
    t = np.linspace(0, np.pi, max(12, int(r)))
    return np.column_stack([(a + b) / 2 + r * np.cos(t) * np.sign(a - b), opp * r * np.sin(t)])


def lag(gruppe):
    over, under = [], []
    for s in D:
        if (s["gruppe"] == "attopptaking") != gruppe:
            continue
        a = s["aar"] + rng.uniform(-0.4, 0.4)
        for z, opp, ut in (("overdel", 1, over), ("understell", -1, under)):
            p = boge(a, s[z], opp)
            if p is not None:
                ut.append(p)
    return over, under


fig = plt.figure(figsize=(7.4, 8.5))
ax = fig.add_axes([0.03, 0.075, 0.94, 0.79])
for gruppe, farge, lw, a in ((False, "#000000", 0.32, 0.075), (True, "#000000", 0.55, 0.42)):
    o, u = lag(gruppe)
    ax.add_collection(LineCollection(o + u, colors=farge, linewidths=lw, alpha=a, capstyle="round"))
ax.plot([T0, T1], [0, 0], color=FG, lw=0.7)
for y in range(1550, 2030, 50):
    ax.plot([y, y], [-2.5, 2.5], color=FG, lw=0.6)
    ax.text(y, -7, str(y), family=MONO, fontsize=6.4, color=DIM, ha="center", va="top", zorder=5,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.6))
ax.set_xlim(T0, T1)
ax.set_ylim(-226, 226)
ax.set_aspect("equal")
ax.axis("off")
ax.text(T0 + 2, 222, "overdelen", fontsize=13, va="top")
ax.text(T0 + 2, 208, "kvar boge går til året dei sju likaste overdelane vart laga", family=MONO, fontsize=6.4, color=DIM, va="top")
ax.text(T0 + 2, -222, "understellet", fontsize=13, va="bottom")
ax.text(T0 + 2, -208, "kvar boge går til året dei sju likaste understella vart laga", family=MONO, fontsize=6.4, color=DIM, va="bottom")
t1 = R["resultat"]["T1_overdelen_er_eldre"]
mi = lambda v: "%d" % round(v)
fig.text(0.03, 0.972, "Overdel og understell peikar på same år", fontsize=22, va="top")
fig.text(0.03, 0.928, "Føreseiinga var at stolar som tek opp att ein eldre stil (svart), skulle ha ein eldre overdel.", fontsize=10.4, va="top")
fig.text(0.03, 0.906, "Skilnaden er %s år i median (95 %%: %s til %s). Ein heil sirkel er ein stol med éin alder." % (
    mi(t1["median"]), mi(t1["ki95"][0]), mi(t1["ki95"][1])), fontsize=10.4, va="top")
fig.text(0.03, 0.045, "%s stolar · svart: %d attopptakingar laga 1830 til 1914 · forsegla prøve 4, T1 til T3 slo feil" % (
    format(len(D), ",").replace(",", " "), t1["n"]), family=MONO, fontsize=6.6, color=DIM)
fig.text(0.03, 0.028, "likskap: materiale og utstrekning per cm over golvet, framanfrå og frå sida · understell 2 til 36 cm, overdel 62 til 125 cm",
         family=MONO, fontsize=6.6, color=DIM)
os.makedirs(UT, exist_ok=True)
p = os.path.join(UT, "prove4_to_alder.png")
fig.savefig(p, dpi=240, bbox_inches="tight", pad_inches=0.22)
print(p)
