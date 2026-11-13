"""17_figurar_profil.py - figurar teikna frå dei verkelege profilane (silhuettar frå 3D-modellane).

  python analyse/17_figurar_profil.py dev     # dei 250 opne stolane (opplæringshalvparten)
  python analyse/17_figurar_profil.py alle    # alle; nektar før den andre prøva er forsegla og køyrd

Ut: analyse/figurar/png/<utval>_*.png. Svart på kvitt, same målestokk i alle figurane (1 px = 1 cm).
"""
import csv, os, sys
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
UT = os.path.join(HER, "figurar", "png")
os.makedirs(UT, exist_ok=True)
UTVAL = sys.argv[1] if len(sys.argv) > 1 else "dev"
if UTVAL == "alle" and not os.path.exists(os.path.join(HER, "forsegla2", "RESULTAT.json")):
    sys.exit("Stoppa: dei tilbakehaldne stolane er ikkje opna enno.")

# ---------------------------------------------------------------- skrift og fargar
FONTMAPPE = os.path.join(os.path.dirname(os.path.dirname(HER)), "FORML-RE", "traktat", "layout", "fonts")
for f in ("EBGaramond12-Regular.otf", "EBGaramond12-Italic.otf"):
    p = os.path.join(FONTMAPPE, f)
    if os.path.exists(p):
        fm.fontManager.addfont(p)
SERIF = "EB Garamond" if any(f.name == "EB Garamond" for f in fm.fontManager.ttflist) else "Georgia"
MONO = "Consolas"
FG, DIM, HAIR = "#0c0c0c", "#777777", "#dedede"
plt.rcParams.update({"font.family": SERIF, "text.color": FG, "axes.edgecolor": FG, "figure.facecolor": "white",
                     "savefig.facecolor": "white", "axes.linewidth": 0.6})

# ---------------------------------------------------------------- data
rein = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "stolar_reinsa.csv"), encoding="utf-8-sig"))}
if UTVAL == "dev":
    maal = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "dev_mesh_maal.csv"), encoding="utf-8"))}
    z = np.load(os.path.join(HER, "data", "dev_silhuettar.npz"))
else:
    maal = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "mesh_maal.csv"), encoding="utf-8"))}
    z = np.load(os.path.join(HER, "data", "mesh_silhuettar.npz"))
SIDE = dict(zip(z["ids"], np.unpackbits(z["side"], axis=-1)))
FRONT = dict(zip(z["ids"], np.unpackbits(z["front"], axis=-1)))


def utstrekning(img):
    k = np.where(img.any(0))[0]
    r = np.where(img.any(1))[0]
    return (k[0], k[-1], r[0], r[-1]) if len(k) else (0, 0, 0, 0)


STOLAR = []
for cid in SIDE:
    r, m = rein.get(cid), maal.get(cid)
    if not r or not m or r["vaksenstol"] != "1":
        continue
    flagg = set(filter(None, (m.get("flagg") or "").split(";")))
    if flagg & {"opp_ikkje_y", "opp_ned?", "silhuett_klipt"}:
        continue
    H, B, D = float(r["H"]), float(r["B"]), float(r["D"])
    k0, k1, r0, r1 = utstrekning(SIDE[cid])
    f0, f1, _, _ = utstrekning(FRONT[cid])
    if (k1 - k0) > 1.5 * D + 10 or (f1 - f0) > 1.5 * B + 10 or abs(r1 + 1 - H) > 6:
        continue                                     # fleire gjenstandar i éin modell, eller feil skala
    aar = float(r["aar_fraa"]) if r["aar_fraa"] else 0
    STOLAR.append({"id": cid, "aar": int(aar) if aar >= 1000 else None, "H": H, "museum": r["museum"],
                   "sete": float(m["sete_cm"]) if m.get("sete_cm") else None, "type": r["type"]})
N = len(STOLAR)
print("utval:", UTVAL, "| stolar i figurane:", N, "av", len(SIDE))
SETE = float(np.median([s["sete"] for s in STOLAR if s["sete"]]))


def stabel(ids, bilete):
    return np.mean([bilete[i] for i in ids], axis=0)[:150]


def mono(ax, x, y, s, **kw):
    kw.setdefault("color", DIM)
    kw.setdefault("fontsize", 7.5)
    ax.text(x, y, s, family=MONO, **kw)


def teikn_stabel(ax, p, konturar=(0.1, 0.25, 0.5, 0.75), xlim=(30, 130)):
    ax.imshow(p ** 0.8, cmap="gray_r", vmin=0, vmax=1.0, origin="lower", extent=[0, 160, 0, 150], interpolation="bilinear")
    g = cv2.GaussianBlur(p.astype(np.float32), (0, 0), 1.2)
    ax.contour(np.arange(160) + 0.5, np.arange(150) + 0.5, g, levels=list(konturar), colors=FG,
               linewidths=[0.35, 0.45, 0.9, 0.45][:len(konturar)])
    ax.set_xlim(*xlim)
    ax.set_ylim(0, 145)
    ax.set_aspect("equal")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])


def lagre(fig, namn):
    p = os.path.join(UT, "%s_%s.png" % (UTVAL, namn))
    fig.savefig(p, dpi=220, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("skrive:", p)


alle_id = [s["id"] for s in STOLAR]
KJELDE = "sideriss frå 3D-modellar av museumsstolar · Nasjonalmuseet og V&A"

# ================================================================ 1. kart over stolen
fig = plt.figure(figsize=(6.2, 8.4))
ax = fig.add_axes([0.10, 0.10, 0.86, 0.74])
P = stabel(alle_id, SIDE)
teikn_stabel(ax, P)
for y in (0, 45, 90, 135):
    ax.plot([31, 33], [y, y], color=FG, lw=0.6)
    mono(ax, 29.5, y, "%d" % y, ha="right", va="center")
mono(ax, 29.5, 143, "cm", ha="right", va="center")
fig.text(0.10, 0.925, "%s stolar oppå kvarandre" % "{:,}".format(N).replace(",", " "), fontsize=25, family=SERIF)
fig.text(0.10, 0.888, "Kvar stol står på same golv, i same målestokk, med ryggen til venstre.", fontsize=11.5, family=SERIF, color=FG)
fig.text(0.10, 0.065, "gråtone: del av stolane som dekkjer punktet · liner: 10, 25, 50 og 75 %", family=MONO, fontsize=7.2, color=DIM)
fig.text(0.10, 0.045, KJELDE, family=MONO, fontsize=7.2, color=DIM)
lagre(fig, "1_kart")

# ================================================================ 2. frå golvet eller i proporsjon
Hmed = float(np.median([s["H"] for s in STOLAR]))


def skalert(img, H):
    """Skaler stolen jamt slik at høgda blir Hmed. Golvet og midten står fast."""
    f = Hmed / H
    ny = cv2.resize(img.astype(np.uint8), None, fx=f, fy=f, interpolation=cv2.INTER_NEAREST)
    ut = np.zeros((200, 160), np.uint8)
    h = min(ny.shape[0], 200)
    k0 = int(round(80 - 80 * f))
    a, b = max(k0, 0), min(k0 + ny.shape[1], 160)
    ut[:h, a:b] = ny[:h, a - k0:b - k0]
    return ut


P_golv = stabel(alle_id, SIDE)
P_prop = np.mean([skalert(SIDE[s["id"]], s["H"]) for s in STOLAR], axis=0)[:150]


def kant(p):
    """Kor skarpt biletet skiftar i høgda: middels absolutt endring per cm, rad for rad."""
    return np.abs(np.diff(p, axis=0)).sum(1) / max(p.sum() / 150, 1e-9)


fig = plt.figure(figsize=(6.2, 6.4))
for i, (p, tittel) in enumerate(((P_golv, "målt frå golvet"), (P_prop, "skalert til same høgd"))):
    ax = fig.add_axes([0.06 + 0.47 * i, 0.16, 0.34, 0.56])
    teikn_stabel(ax, p, konturar=(0.25, 0.5))
    mono(ax, 30, -9, tittel, color=FG, fontsize=8.5, va="top")
    axk = fig.add_axes([0.06 + 0.47 * i + 0.345, 0.16, 0.085, 0.56], sharey=ax)
    k = kant(p)
    axk.plot(k, np.arange(len(k)) + 1, color=FG, lw=0.8)
    axk.set_xlim(0, max(kant(P_golv).max(), kant(P_prop).max()) * 1.05)
    axk.axis("off")
sete_cm = np.array([s["sete"] for s in STOLAR if s["sete"]])
sete_del = np.array([s["sete"] / s["H"] for s in STOLAR if s["sete"]])
rs = lambda x: 1.4826 * np.median(np.abs(x - np.median(x))) / np.median(x)
fig.text(0.06, 0.90, "Stolen er ordna i centimeter,\nikkje i proporsjonar", fontsize=21, family=SERIF, va="top", linespacing=1.05)
fig.text(0.06, 0.095, "kurva: kor brått biletet skiftar for kvar centimeter oppover · skalert fell toppen saman av seg sjølv", family=MONO, fontsize=7.2, color=DIM)
fig.text(0.06, 0.072, "spreiing i setehøgda: %.1f %% målt i cm, %.1f %% som del av totalhøgda · %d stolar" % (100 * rs(sete_cm), 100 * rs(sete_del), N),
         family=MONO, fontsize=7.2, color=DIM)
lagre(fig, "2_golv_eller_proporsjon")

# ================================================================ 3. alle stolane etter år
med_aar = sorted([s for s in STOLAR if s["aar"]], key=lambda s: (s["aar"], s["id"]))
PER_RAD, CELLE, RADH, BOTN = 11, 80, 150, 24      # BOTN: plass til årstalet under golvet
T = RADH + BOTN
rader = int(np.ceil(len(med_aar) / PER_RAD))
W, Hh = PER_RAD * CELLE, rader * T
golv = lambda rad: Hh - (rad + 1) * T + BOTN       # y for golvet i rad nr. rad, talt ovanfrå
lerret = np.zeros((Hh, W), np.uint8)               # rad 0 i lerretet = nedst (origin="lower")
for n, s in enumerate(med_aar):
    rad, kol = divmod(n, PER_RAD)
    img = SIDE[s["id"]][:RADH]
    k0, k1, _, _ = utstrekning(img)
    b = min(k1 - k0 + 1, CELLE - 4)
    k0 += (k1 - k0 + 1 - b) // 2
    x0 = kol * CELLE + (CELLE - b) // 2
    lerret[golv(rad):golv(rad) + RADH, x0:x0 + b] |= img[:, k0:k0 + b]
topp = 0.16 * W / (Hh + 0.16 * W)                  # tittelfeltet som del av figurhøgda
fig = plt.figure(figsize=(6.6, 6.6 * Hh / W / (1 - topp - 0.005)))
ax = fig.add_axes([0.03, 0.005, 0.94, 1 - topp - 0.005])
ax.imshow(lerret, cmap="gray_r", vmin=0, vmax=1, interpolation="nearest", origin="lower", extent=[0, W, 0, Hh])
for rad in range(rader):
    ax.plot([0, W], [golv(rad), golv(rad)], color=FG, lw=0.4)
    ax.plot([0, W], [golv(rad) + SETE, golv(rad) + SETE], color=DIM, lw=0.45, dashes=(4, 3), zorder=0)
    for kol in range(PER_RAD):
        n = rad * PER_RAD + kol
        if n < len(med_aar):
            ax.text(kol * CELLE + CELLE / 2, golv(rad) - 5, str(med_aar[n]["aar"]), family=MONO, fontsize=5.2,
                    color=DIM, ha="center", va="top")
ax.set_xlim(0, W)
ax.set_ylim(0, Hh)
ax.axis("off")
fig.text(0.03, 1 - 0.12 * topp, "Setet står. Ryggen vandrar.", fontsize=23, family=SERIF, va="top")
fig.text(0.03, 1 - 0.56 * topp, "%d stolar i same målestokk, ordna etter år · stipla line: %.0f cm over golvet" % (len(med_aar), SETE),
         family=MONO, fontsize=7.2, color=DIM, va="top")
lagre(fig, "3_etter_aar")

# ================================================================ 4. fire hundreår
bolkar = [("før 1700", lambda a: a < 1700), ("1700-talet", lambda a: 1700 <= a < 1800),
          ("1800-talet", lambda a: 1800 <= a < 1900), ("etter 1900", lambda a: a >= 1900)]
fig = plt.figure(figsize=(6.6, 3.9))
for i, (namn, test) in enumerate(bolkar):
    ids = [s["id"] for s in med_aar if test(s["aar"])]
    ax = fig.add_axes([0.03 + 0.24 * i, 0.14, 0.225, 0.62])
    teikn_stabel(ax, stabel(ids, SIDE), konturar=(0.5,), xlim=(35, 125))
    ax.plot([35, 125], [SETE, SETE], color=DIM, lw=0.45, dashes=(4, 3))
    mono(ax, 36, -8, "%s · %d" % (namn, len(ids)), color=FG, fontsize=7.5, va="top")
fig.text(0.03, 0.93, "Fire hundreår oppå kvarandre", fontsize=20, family=SERIF, va="top")
fig.text(0.03, 0.045, "svart line: omrisset halvparten av stolane dekkjer · stipla: %.0f cm" % SETE, family=MONO, fontsize=7.2, color=DIM)
lagre(fig, "4_hundreaar")

# ================================================================ 5. materialskiftet
import re
ST = {r["Objekt-ID"]: r for r in csv.DictReader(open(os.path.join(os.path.dirname(HER), "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline=""))}
RX_LINE = re.compile(r"stål|aluminium|jern|metall|krom", re.I)
RX_FLATE = re.compile(r"kryssfiner|finer|laminat|sponplate|plast|glasfiber|polyprop|polyester|polyetylen|polykarbonat|polyamid|melamin|akryl", re.I)


def klasse(s):
    m = ST.get(s["id"], {}).get("Materialar", "")
    if RX_LINE.search(m):
        return "line"
    if RX_FLATE.search(m):
        return "flate"
    return "tre"


grupper = [("tre, før 1900", [s for s in med_aar if s["aar"] < 1900 and klasse(s) == "tre"]),
           ("stålrøyr og stong, frå 1925", [s for s in med_aar if s["aar"] >= 1925 and klasse(s) == "line"]),
           ("plate og skal, frå 1925", [s for s in med_aar if s["aar"] >= 1925 and klasse(s) == "flate"])]
fig = plt.figure(figsize=(6.6, 7.4))
for i, (namn, gr) in enumerate(grupper):
    ids = [s["id"] for s in gr]
    for j, (bilete, xlim) in enumerate(((SIDE, (35, 125)), (FRONT, (35, 125)))):
        ax = fig.add_axes([0.03 + 0.32 * i, 0.50 - 0.40 * j, 0.30, 0.36])
        teikn_stabel(ax, stabel(ids, bilete), konturar=(0.5,), xlim=xlim)
        ax.plot(xlim, [SETE, SETE], color=DIM, lw=0.45, dashes=(4, 3))
        ax.plot(xlim, [30, 30], color=DIM, lw=0.3)
        if j == 1:
            kat = [float(rein[s["id"]]["sete"]) for s in gr if rein[s["id"]]["sete_ok"] == "1"]
            mono(ax, xlim[0] + 1, -8, "%s · %d" % (namn, len(ids)), color=FG, fontsize=7.2, va="top")
            mono(ax, xlim[0] + 1, -17, "høgd %.0f cm · sete %.0f cm" % (np.median([s["H"] for s in gr]), np.median(kat)), fontsize=7.0, va="top")
fig.text(0.03, 0.955, "Nytt materiale, same sete", fontsize=22, family=SERIF, va="top")
fig.text(0.03, 0.905, "Under setet løyser stolen seg opp. Totalhøgda fell om lag 20 cm, setet 3.", fontsize=11.5, family=SERIF, va="top")
fig.text(0.03, 0.03, "øvst: frå sida · nedst: framanfrå · stipla: %.0f cm · tynn line: 30 cm · høgd og sete: medianar frå katalogen" % SETE,
         family=MONO, fontsize=7.0, color=DIM)
lagre(fig, "5_materiale")
