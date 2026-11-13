"""33_figur_atavisme.py - tvillingane til den sjuande prøva: kvar av dei mest nyskapande stolane etter 1900,
fylt svart, med den likaste stolen frå før 1840 som tynn kontur oppå.

  python analyse/33_figur_atavisme.py   -> analyse/figurar/png/prove7_atavisme.png, data/atavisme_vend.json
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

D = json.load(open(os.path.join(HER, "forsegla7", "FIGURDATA.json"), encoding="utf-8"))["stolar"]
R = json.load(open(os.path.join(HER, "forsegla7", "RESULTAT.json"), encoding="utf-8"))
z = np.load(os.path.join(HER, "data", "mesh_silhuettar.npz"))
SIDE = dict(zip(z["ids"], np.unpackbits(z["side"], axis=-1)))
nye = sorted([s for s in D if s["ny"]], key=lambda s: (s["aar"], s["id"]))
KOL, CW, CH = 8, 92, 140


def sentrert(img):
    k = np.where(img.any(0))[0]
    return np.roll(img, 80 - (k[0] + k[-1] + 1) // 2, axis=1) if len(k) else img


vend = {}
fig_h = 1.9 + ((len(nye) + KOL - 1) // KOL) * 1.575
fig = plt.figure(figsize=(7.4, fig_h))
ax = fig.add_axes([0.02, 0.32 / fig_h, 0.96, 1 - 1.75 / fig_h])
for k, s in enumerate(nye):
    r, c = divmod(k, KOL)
    x0, y0 = c * CW, -(r + 1) * (CH + 22)
    a = sentrert(SIDE[s["id"]][:CH]).astype(np.uint8)
    b = sentrert(SIDE[s["tvilling"]][:CH]).astype(np.uint8)
    bf = sentrert(b[:, ::-1].copy())
    iou = lambda p, q: (p & q).sum() / max((p | q).sum(), 1)
    v = iou(a, bf) > iou(a, b)
    vend[s["id"]] = bool(v)
    b = bf if v else b
    ax.imshow(np.where(a > 0, 1.0, np.nan), cmap="gray_r", vmin=0, vmax=1, origin="lower",
              extent=[x0 + CW / 2 - 80, x0 + CW / 2 + 80, y0, y0 + CH], interpolation="nearest", zorder=2)
    cs, _ = cv2.findContours(b, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    for cc in cs:
        if len(cc) < 12:
            continue
        p = cc[:, 0, :].astype(float)
        p = np.vstack([p, p[:1]])
        ax.plot(x0 + CW / 2 - 80 + p[:, 0] + 0.5, y0 + p[:, 1] + 0.5, color=FG, lw=0.45, zorder=3)
    ax.plot([x0 + 6, x0 + CW - 6], [y0, y0], color=FG, lw=0.5)
    ax.text(x0 + CW / 2, y0 - 4, "%d · %d" % (s["aar"], s["tvilling_aar"]), family=MONO, fontsize=5.2, color=DIM, ha="center", va="top")
rader = (len(nye) + KOL - 1) // KOL
ax.set_xlim(-2, KOL * CW + 2)
ax.set_ylim(-rader * (CH + 22) - 16, 4)
ax.set_aspect("equal")
ax.axis("off")
a1, a2 = R["resultat"]["A1_under_nullmedianen"], R["resultat"]["A2_naerare_enn_tilfeldig"]
tv = R["sekundaert"]["tvillingaar"]
pc = lambda v: "%d %%" % round(100 * v)
fig.text(0.02, 1 - 0.16 / fig_h, "Den som bryt med fortida, fell i ein gammal dal", fontsize=21, va="top")
fig.text(0.02, 1 - 0.62 / fig_h, "Dei %d mest nyskapande stolane etter 1900 (svarte) og den likaste stolen frå før 1840 (strek)." % len(nye), fontsize=10.2, va="top")
fig.text(0.02, 1 - 0.86 / fig_h, "%s ligg nærare ein gammal stol enn eit like langt steg i tilfeldig retning, og avstanden er %s kortare." % (
    pc(a1["del"]), pc(1 - a2["R"])), fontsize=10.2, va="top")
fig.text(0.02, 0.14 / fig_h, "år for stolen · år for tvillingen · median tvilling %d, kvartilar %d og %d · nullmodell: 200 steg frå den nære fortida per stol · forsegla prøve 7" % (
    tv["median"], tv["kvartilar"][0], tv["kvartilar"][1]), family=MONO, fontsize=5.8, color=DIM)
os.makedirs(UT, exist_ok=True)
p = os.path.join(UT, "prove7_atavisme.png")
fig.savefig(p, dpi=240, bbox_inches="tight", pad_inches=0.2)
json.dump(vend, open(os.path.join(HER, "data", "atavisme_vend.json"), "w", encoding="utf-8"))
print(p, len(nye), sum(vend.values()))
