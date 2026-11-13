"""19_saumar.py - er stolen éi form eller to? Utforskande, på dei opne stolane (opplæringshalvparten).

Frå formlære: vurderinga er ein sum over omsyn (5.701), og spreiinga er den inverse krumminga (6.672).
Er omsyna skilde, er kovariansen delt i blokker: kvar blokk er eitt omsyn, og grensene mellom blokkene
er der eitt omsyn sluttar og eit anna tek til. Skriptet les blokkene ut av silhuettane:
  1. kor mykje av éi sone i stolen kan føreseiast frå ei anna (kryssvalidert forklart varians)
  2. kor godt kvar sone daterer stolen
  3. kimærar: understell og sete frå éin stol, alt over setet frå ein annan (formalgebra, 1.6101)
     og om dei ligg innanfor det busette formrommet

  python analyse/19_saumar.py     -> analyse/19_resultat.txt, analyse/figurar/png/dev_6_*.png, dev_7_*.png
Ingenting her er forsegla. Tala er frå opplæringshalvparten og må prøvast på dei tilbakehaldne stolane.
"""
import csv, os, re, sys
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
MONO, FG, DIM = "Consolas", "#0c0c0c", "#777777"
plt.rcParams.update({"font.family": SERIF, "text.color": FG, "figure.facecolor": "white", "savefig.facecolor": "white"})
FRO = 20261113
linjer = []


def skriv(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    linjer.append(s)


# ---------------------------------------------------------------- data (berre opplæringshalvparten)
rein = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "stolar_reinsa.csv"), encoding="utf-8-sig"))}
maal = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "dev_mesh_maal.csv"), encoding="utf-8"))}
z = np.load(os.path.join(HER, "data", "dev_silhuettar.npz"))
SIDE = dict(zip(z["ids"], np.unpackbits(z["side"], axis=-1)))
FRONT = dict(zip(z["ids"], np.unpackbits(z["front"], axis=-1)))
NR = 140


def utstr(img):
    k = np.where(img.any(0))[0]
    r = np.where(img.any(1))[0]
    return (int(k[0]), int(k[-1]), int(r[0]), int(r[-1])) if len(k) else (0, 0, 0, 0)


S = []
for cid in SIDE:
    r, m = rein.get(cid), maal.get(cid)
    if not r or not m or r["vaksenstol"] != "1" or not r["aar_fraa"] or float(r["aar_fraa"]) < 1000:
        continue
    if set(filter(None, (m.get("flagg") or "").split(";"))) & {"opp_ikkje_y", "opp_ned?", "silhuett_klipt"}:
        continue
    H, B, D = float(r["H"]), float(r["B"]), float(r["D"])
    k0, k1, r0, r1 = utstr(SIDE[cid])
    f0, f1, _, _ = utstr(FRONT[cid])
    if (k1 - k0) > 1.5 * D + 10 or (f1 - f0) > 1.5 * B + 10 or abs(r1 + 1 - H) > 6:
        continue
    S.append({"id": cid, "aar": int(float(r["aar_fraa"])), "H": H, "B": B, "museum": r["museum"], "type": r["type"],
              "sete": float(m["sete_cm"]) if m.get("sete_cm") else None})
n = len(S)


def radtrekk(side, front):
    """Per centimeter over golvet: mengd materiale og utstrekning, framanfrå og frå sida. -> (4, NR)"""
    ut = []
    for img in (front, side):
        img = img[:NR].astype(np.float32)
        occ = img > 0.5
        an = occ.any(1)
        f = np.where(an, occ.argmax(1), 0)
        l = np.where(an, 159 - occ[:, ::-1].argmax(1), 0)
        ut += [img.sum(1), np.where(an, l - f + 1, 0).astype(np.float32)]
    return np.array(ut)


X = np.array([radtrekk(SIDE[s["id"]], FRONT[s["id"]]) for s in S])
rng = np.random.default_rng(FRO)
fald = rng.permutation(n) % 5


def innan_periode(M):
    b = np.array([min(max(s["aar"], 1550), 1999) // 50 for s in S])
    Dm = np.column_stack([(b == k).astype(float) for k in np.unique(b)] + [np.array([s["museum"] == "NM" for s in S], float)])
    beta, *_ = np.linalg.lstsq(Dm, M, rcond=None)
    return M - Dm @ beta


def pca(M, maxk=8, andel=0.85):
    M = M - M.mean(0)
    sd = M.std(0)
    M = M[:, sd > 1e-6] / sd[sd > 1e-6]
    U, sv, _ = np.linalg.svd(M, full_matrices=False)
    v = sv ** 2 / (sv ** 2).sum()
    k = int(min(maxk, np.searchsorted(np.cumsum(v), andel) + 1))
    return U[:, :k] * sv[:k], v[:k]


def kv_pred(P, y):
    pred = np.zeros(len(y))
    for f in range(5):
        tr, te = fald != f, fald == f
        b, *_ = np.linalg.lstsq(np.column_stack([np.ones(tr.sum()), P[tr]]), y[tr], rcond=None)
        pred[te] = np.column_stack([np.ones(te.sum()), P[te]]) @ b
    return pred


def forklart(Xs, a, b):
    """Kryssvalidert del av variansen i sone b som sone a føreseier."""
    Pa, _ = pca(Xs[:, :, a[0]:a[1]].reshape(n, -1))
    Pb, vb = pca(Xs[:, :, b[0]:b[1]].reshape(n, -1))
    r2 = [1 - ((Pb[:, j] - kv_pred(Pa, Pb[:, j])) ** 2).sum() / ((Pb[:, j] - Pb[:, j].mean()) ** 2).sum() for j in range(Pb.shape[1])]
    return float((np.clip(r2, 0, 1) * vb).sum() / vb.sum())


SONER = [("understell", (2, 36)), ("setesone", (38, 58)), ("overdel", (62, 125))]
skriv("Opplæringshalvparten: %d stolar med år og brukande silhuett. Utforskande, ikkje forsegla." % n)
skriv("\n== 1. Kor mykje av éi sone føreseier ei anna (kryssvalidert forklart varians)")
TAL = {}
for namn, Xs in (("over alle år", X), ("innan 50-årsbolk og museum", innan_periode(X.reshape(n, -1)).reshape(n, 4, NR))):
    skriv("  " + namn)
    for a, ra in SONER:
        for b, rb in SONER:
            if a != b:
                TAL[(namn, a, b)] = forklart(Xs, ra, rb)
                skriv("     %-10s -> %-10s %.2f" % (a, b, TAL[(namn, a, b)]))

skriv("\n== 2. Kor godt daterer kvar sone stolen (kryssvalidert, median absolutt feil i år)")
aar = np.array([s["aar"] for s in S], float)
DAT = {"gissing (medianåret)": float(np.median(np.abs(aar - np.median(aar))))}
for namn, r in SONER + [("heile stolen", (2, 125))]:
    P, _ = pca(X[:, :, r[0]:r[1]].reshape(n, -1), maxk=10, andel=0.9)
    DAT[namn] = float(np.median(np.abs(aar - kv_pred(P, aar))))
for k, v in DAT.items():
    skriv("     %-22s %.0f år" % (k, v))


# ---------------------------------------------------------------- 3. kimærar
def sete_i_riss(img, s):
    k = np.where(img[max(int(s) - 4, 0):int(s)].any(0))[0]
    return (int(k[0]), int(k[-1]) - int(k[0]) + 1) if len(k) else (60, 45)


def kimaer(A, B, bilete):
    """Understell og sete frå A, alt over setet frå B: flytt til setehøgda til A og skalert til setet til A."""
    a, b = bilete[A["id"]].astype(np.uint8), bilete[B["id"]].astype(np.uint8)
    sa, sb = int(round(A["sete"])), int(round(B["sete"]))
    xa, da = sete_i_riss(a, sa)
    xb, db = sete_i_riss(b, sb)
    f = da / max(db, 1)
    ny = cv2.resize(b[sb:], None, fx=f, fy=1, interpolation=cv2.INTER_NEAREST)
    ut = np.zeros((200, 160), np.uint8)
    ut[:sa] = a[:sa]
    x0 = int(round(xa - xb * f))
    h = min(ny.shape[0], 200 - sa)
    aa, bb = max(x0, 0), min(x0 + ny.shape[1], 160)
    if bb > aa:
        ut[sa:sa + h, aa:bb] |= ny[:h, aa - x0:bb - x0]
    return ut


OK = [s for s in S if s["sete"] and 34 <= s["sete"] <= 56]
R = np.array([radtrekk(SIDE[s["id"]], FRONT[s["id"]]).ravel() for s in OK])
mu, sd = R.mean(0), R.std(0)
okc = sd > 1e-6
_, sv, Vt = np.linalg.svd((R - mu)[:, okc] / sd[okc], full_matrices=False)
proj = lambda M: (((M - mu)[:, okc] / sd[okc]) @ Vt[:15].T) / sv[:15] * np.sqrt(len(R))
PR = proj(R)
stamme = lambda i: re.sub(r"[A-Za-z]$|-\d+$", "", i)
gr = {}
for i, s in enumerate(OK):
    gr.setdefault((stamme(s["id"]), s["H"], s["B"]), set()).add(i)
sett = [gr[(stamme(s["id"]), s["H"], s["B"])] for s in OK]


def naeraste(p, utan):
    d = np.sqrt(((PR - p) ** 2).sum(1))
    d[list(utan)] = np.inf
    return float(d.min())


ekte = np.array([naeraste(PR[i], sett[i]) for i in range(len(OK))])
q95 = float(np.quantile(ekte, 0.95))
KIM = {"same tid (høgst 30 år mellom halvdelane)": [], "ulik tid (minst 150 år mellom)": []}
while min(len(v) for v in KIM.values()) < 600:
    i, j = rng.choice(len(OK), 2, replace=False)
    dt = abs(OK[i]["aar"] - OK[j]["aar"])
    key = list(KIM)[0] if dt <= 30 else list(KIM)[1] if dt >= 150 else None
    if key is None or len(KIM[key]) >= 600:
        continue
    k = radtrekk(kimaer(OK[i], OK[j], SIDE), kimaer(OK[i], OK[j], FRONT)).ravel()
    KIM[key].append(naeraste(proj(k[None])[0], sett[i] | sett[j]))
skriv("\n== 3. Kimærar: ligg dei innanfor det busette formrommet?")
skriv("     verkelege stolar: median avstand til næraste andre stol %.2f, 95-persentil %.2f (n=%d)" % (np.median(ekte), q95, len(ekte)))
for k, v in KIM.items():
    skriv("     kimærar, %-42s median %.2f | innanfor 95-persentilen: %.0f %% (n=%d)" % (k, np.median(v), 100 * np.mean(np.array(v) <= q95), len(v)))
# Tida, centimeter for centimeter: kor godt eit 12 cm høgt band daterer stolen
skriv("")
skriv("== 4. Dateringsfeil for eit 12 cm band, etter høgd over golvet (median absolutt feil i år)")
TIDSKURVE = []
for c in range(8, 121, 2):
    Pb, _ = pca(X[:, :, c - 6:c + 6].reshape(n, -1), maxk=6, andel=0.9)
    TIDSKURVE.append([c, round(float(np.median(np.abs(aar - kv_pred(Pb, aar)))), 1)])
skriv("     " + "  ".join("%d:%.0f" % (c, e) for c, e in TIDSKURVE[::3]))
open(os.path.join(HER, "19_resultat.txt"), "w", encoding="utf-8").write("\n".join(linjer) + "\n")
import json
_i = "innan 50-årsbolk og museum"
json.dump({"n": n, "uo": round(100 * TAL[(_i, "understell", "overdel")]), "ou": round(100 * TAL[(_i, "overdel", "understell")]),
           "us": round(100 * TAL[(_i, "understell", "setesone")]), "dat": {k.split()[0]: round(v) for k, v in DAT.items()},
           "kim": round(100 * float(np.mean(np.array(KIM[list(KIM)[1]]) <= q95))), "tidskurve": TIDSKURVE},
          open(os.path.join(HER, "data", "saumar_dev.json"), "w", encoding="utf-8"), ensure_ascii=False)


# ================================================================ figur 6: to former som møtest i setet
def mono(ax, x, y, s, **kw):
    kw.setdefault("color", DIM)
    kw.setdefault("fontsize", 7.6)
    ax.text(x, y, s, family=MONO, **kw)


P = np.mean([SIDE[s["id"]] for s in S], axis=0)[:150]
fig = plt.figure(figsize=(6.6, 7.6))
ax = fig.add_axes([0.04, 0.09, 0.92, 0.72])
ax.imshow(P ** 0.8, cmap="gray_r", vmin=0, vmax=1, origin="lower", extent=[0, 160, 0, 150], interpolation="bilinear")
ax.contour(np.arange(160) + .5, np.arange(150) + .5, cv2.GaussianBlur(P.astype(np.float32), (0, 0), 1.2), levels=[0.5], colors=FG, linewidths=0.8)
ax.set_xlim(20, 215)
ax.set_ylim(0, 140)
ax.set_aspect("equal")
ax.axis("off")
ax.plot([20, 215], [0, 0], color=FG, lw=0.8)
innan = "innan 50-årsbolk og museum"
for (namn, (lo, hi)), tekst in zip(SONER, (
        ["daterer stolen ±%.0f år" % DAT["understell"]],
        ["daterer ikkje stolen", "(±%.0f år; rein gissing ±%.0f)" % (DAT["setesone"], DAT["gissing (medianåret)"])],
        ["daterer stolen ±%.0f år," % DAT["overdel"], "like godt som heile stolen (±%.0f)" % DAT["heile stolen"]])):
    for y in (lo, hi):
        ax.plot([42, 128], [y, y], color=DIM, lw=0.45, dashes=(4, 3))
    ax.plot([128, 131], [(lo + hi) / 2] * 2, color=FG, lw=0.6)
    ax.text(134, (lo + hi) / 2 + (3.2 if len(tekst) > 1 else 1.6), namn, fontsize=13, family=SERIF, va="center")
    for i, t in enumerate(tekst):
        mono(ax, 134, (lo + hi) / 2 - 2.6 - 4.2 * i + (3.2 if len(tekst) > 1 else 1.6) - 1.4, t, va="center")
mono(ax, 22, 36, "36", ha="left", va="bottom", fontsize=6.8)
mono(ax, 22, 62, "62 cm", ha="left", va="bottom", fontsize=6.8)
fig.text(0.04, 0.955, "To former møtest i setet", fontsize=25, family=SERIF, va="top")
fig.text(0.04, 0.895, "Understellet føreseier %.0f %% av overdelen, og overdelen %.0f %% av understellet." % (
    100 * TAL[(innan, "understell", "overdel")], 100 * TAL[(innan, "overdel", "understell")]), fontsize=11.5, family=SERIF, va="top")
fig.text(0.04, 0.865, "Setesona heng saman med understellet (%.0f %%). Tida sit i overdelen." % (100 * TAL[(innan, "understell", "setesone")]),
         fontsize=11.5, family=SERIF, va="top")
fig.text(0.04, 0.055, "%d stolar, opplæringshalvparten · forklart varians er kryssvalidert, innan 50-årsbolk og museum" % n, family=MONO, fontsize=7.0, color=DIM)
fig.text(0.04, 0.035, "trekk per cm over golvet: mengd materiale og utstrekning, framanfrå og frå sida · ikkje forsegla", family=MONO, fontsize=7.0, color=DIM)
fig.savefig(os.path.join(UT, "dev_6_to_former.png"), dpi=220, bbox_inches="tight", pad_inches=0.25)
plt.close(fig)

# ================================================================ figur 7: kimærar
VAL = [("O192594", None), ("O192596", None), ("O53092", None), ("O176184", None), ("O182426", None), ("O144058", None)]
idx = {s["id"]: s for s in OK}
valde = [idx[i] for i, _ in VAL if i in idx]
if len(valde) < 5:                                    # reserve: jamt spreidde stolar
    valde = [OK[i] for i in np.linspace(0, len(OK) - 1, 6).astype(int)]
valde.sort(key=lambda s: s["aar"])
m = len(valde)
CW, CH = 92, 138
fig = plt.figure(figsize=(6.9, 6.9 * (m * CH + 150) / (m * CW + 70)))
ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
ax.set_xlim(-70, m * CW)
ax.set_ylim(-(m * CH) - 40, 125)
ax.set_aspect("equal")
ax.axis("off")
for i, A in enumerate(valde):
    for j, B in enumerate(valde):
        img = SIDE[A["id"]] if i == j else kimaer(A, B, SIDE)
        k = np.where(img.any(0))[0]
        c = (k[0] + k[-1]) // 2
        ut = img[:CH - 6, max(c - CW // 2 + 2, 0):c + CW // 2 - 2]
        x0, y0 = j * CW + (CW - ut.shape[1]) / 2, -(i + 1) * CH
        ax.imshow(np.where(ut > 0, 1.0, np.nan), cmap="gray_r", vmin=0, vmax=1, origin="lower",
                  extent=[x0, x0 + ut.shape[1], y0, y0 + ut.shape[0]], interpolation="nearest", zorder=2)
        ax.plot([j * CW + 6, (j + 1) * CW - 6], [y0, y0], color=FG if i == j else DIM, lw=1.1 if i == j else 0.35, zorder=3)
for i, A in enumerate(valde):
    mono(ax, -8, -(i + 1) * CH + 22, str(A["aar"]), ha="right", va="center", color=FG, fontsize=8.5)
    mono(ax, i * CW + CW / 2, 8, str(A["aar"]), ha="center", va="bottom", color=FG, fontsize=8.5)
mono(ax, -8, 8, "understell ↓   overdel →", ha="right", va="bottom", fontsize=6.6)
ax.text(-66, 112, "%d stolar. %d av dei er aldri laga." % (m * m, m * m - m), fontsize=23, family=SERIF, va="top")
ax.text(-66, 80, "Understell og sete frå éin stol, alt over setet frå ein annan. Diagonalen er dei verkelege.", fontsize=10.8, family=SERIF, va="top")
ax.text(-66, 56, "%.0f %% av kimærar med minst 150 år mellom halvdelane ligg like nær ein verkeleg stol" % (100 * np.mean(np.array(KIM[list(KIM)[1]]) <= q95)),
        family=MONO, fontsize=7.0, color=DIM, va="top")
ax.text(-66, 44, "som verkelege stolar ligg kvarandre (n = 600) · opplæringshalvparten · ikkje forsegla", family=MONO, fontsize=7.0, color=DIM, va="top")
fig.savefig(os.path.join(UT, "dev_7_kimaerar.png"), dpi=220, bbox_inches="tight", pad_inches=0.2)
plt.close(fig)
print("figurar skrivne")
