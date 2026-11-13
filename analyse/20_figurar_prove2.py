"""20_figurar_prove2.py - figurar frå den andre forsegla prøva (modulane t1 til t5).

  python analyse/20_figurar_prove2.py                 # les forsegla2/FIGURDATA.json og RESULTAT.json
  python analyse/20_figurar_prove2.py <figurdata.json> <resultat.json> <prefiks>     # til utprøving

Ut: analyse/figurar/png/<prefiks>_*.png. Svart på kvitt. Teiknar berre det som alt er rekna; ingen ny statistikk.
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
P_FIG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HER, "forsegla2", "FIGURDATA.json")
P_RES = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HER, "forsegla2", "RESULTAT.json")
PREFIKS = sys.argv[3] if len(sys.argv) > 3 else "prove2"
FIG = json.load(open(P_FIG, encoding="utf-8"))
RES = json.load(open(P_RES, encoding="utf-8")) if os.path.exists(P_RES) else {}
RES = RES.get("modular", RES)

FONTMAPPE = os.path.join(os.path.dirname(os.path.dirname(HER)), "FORML-RE", "traktat", "layout", "fonts")
for f in ("EBGaramond12-Regular.otf", "EBGaramond12-Italic.otf"):
    p = os.path.join(FONTMAPPE, f)
    if os.path.exists(p):
        fm.fontManager.addfont(p)
SERIF = "EB Garamond" if any(f.name == "EB Garamond" for f in fm.fontManager.ttflist) else "Georgia"
MONO = "Consolas"
FG, DIM, HAIR, LYS = "#0c0c0c", "#777777", "#dedede", "#f1f1f1"
plt.rcParams.update({"font.family": SERIF, "text.color": FG, "axes.edgecolor": FG, "figure.facecolor": "white",
                     "savefig.facecolor": "white", "axes.linewidth": 0.6})
KJELDE = "3D-modellar og katalogmål av museumsstolar · Nasjonalmuseet og V&A · tilbakehaldne stolar, opna éin gong"


def tal(x, d=1):
    return ("%.*f" % (d, x)).replace(".", ",")


def heiltal(n):
    return "{:,}".format(int(n)).replace(",", " ")


def mono(ax, x, y, s, **kw):
    kw.setdefault("color", DIM)
    kw.setdefault("fontsize", 7.2)
    ax.text(x, y, s, family=MONO, **kw)


def naken(ax, behald=("bottom",)):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(s in behald)
    ax.set_xticks([])
    ax.set_yticks([])


def hovud(fig, tittel, under, y=0.93, x=0.08):
    fig.text(x, y, tittel, fontsize=23, family=SERIF)
    fig.text(x, y - 0.045, under, fontsize=11.2, family=SERIF)


def fot(fig, liner, x=0.08, y=0.05):
    for i, s in enumerate(liner):
        fig.text(x, y - 0.02 * i, s, family=MONO, fontsize=7.0, color=DIM)


def lagre(fig, namn):
    p = os.path.join(UT, "%s_%s.png" % (PREFIKS, namn))
    fig.savefig(p, dpi=220, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("skrive:", p)


def kart(ax, M, celle=1.0, x0=0.0, nivaa=(10, 25, 50, 75), glatt=1.2):
    """Teikn eit dekningskart (prosent, rad 0 = golv) med gråtone og nivåliner."""
    M = np.asarray(M, float) / 100.0
    r, k = M.shape
    ax.imshow(M ** 0.8, cmap="gray_r", vmin=0, vmax=1.0, origin="lower", extent=[x0, x0 + k * celle, 0, r * celle],
              interpolation="bilinear")
    g = cv2.GaussianBlur(M.astype(np.float32), (0, 0), glatt)
    ax.contour(x0 + (np.arange(k) + 0.5) * celle, (np.arange(r) + 0.5) * celle, g, levels=[v / 100 for v in nivaa],
               colors=FG, linewidths=[0.35, 0.45, 0.9, 0.45][:len(nivaa)])
    ax.set_aspect("equal")


def prim(res, namn):
    for p in res.get("primaer", []):
        if p.get("namn", "").startswith(namn):
            return p
    return {}


# ================================================================ t5: krakken
def fig_krakk():
    d, r = FIG.get("t5_krakk"), RES.get("t5_krakk", {})
    if not d or "krakk_punkt" not in d:
        return
    pk = d["krakk_punkt"]
    inne = [p for p in pk if p["status"] == "primaer"]
    ute = [p for p in pk if p["status"] != "primaer"]
    stol = [(a, v) for a, v in d["stolsete_punkt_aar_cm"] if a]
    q1, q3 = d["tersklar"]["P1"]
    fig = plt.figure(figsize=(7.6, 6.0))
    ax = fig.add_axes([0.08, 0.13, 0.62, 0.66])
    ax.axhspan(q1, q3, color=LYS, lw=0)
    ax.scatter([a for a, _ in stol], [v for _, v in stol], s=3, color="#b5b5b5", lw=0, zorder=2)
    X_UTAN = 2052
    xs = lambda p: p["aar"] if p["aar"] else X_UTAN
    ax.scatter([xs(p) for p in ute], [p["H"] for p in ute], s=20, facecolor="white", edgecolor=FG, lw=0.6, zorder=3)
    ax.scatter([xs(p) for p in inne], [p["H"] for p in inne], s=20, color=FG, lw=0, zorder=4)
    ax.set_xlim(1440, 2070)
    ax.set_ylim(0, 150)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xticks([1500, 1600, 1700, 1800, 1900, 2000])
    ax.set_yticks([0, 45, 90, 135])
    ax.tick_params(length=2.5, width=0.5, labelsize=7.5, colors=DIM)
    for t in ax.get_xticklabels() + ax.get_yticklabels():
        t.set_family(MONO)
    mono(ax, 1446, 144, "cm frå golvet")
    if any(not p["aar"] for p in pk):
        mono(ax, X_UTAN, 3, "utan år", ha="center", fontsize=6.4)
    # fordelingane til høgre
    bx = fig.add_axes([0.72, 0.13, 0.22, 0.66], sharey=ax)
    naken(bx, behald=())
    hs = d["stolsete_histogram"]
    hH = d["stol_totalhogd_histogram"]

    def trapp(kant, t, **kw):
        t = np.asarray(t, float) / max(1, max(t))
        bx.step(np.r_[0, np.repeat(t, 2), 0], np.r_[kant[0], np.repeat(kant, 2)[1:-1], kant[-1]], **kw)
        return t

    kH = np.asarray(hH["kantar_cm"], float)
    trapp(kH, hH["tal"], color=DIM, lw=0.6)
    ks = np.asarray(hs["kantar_cm"], float)
    ts = np.asarray(hs["tal"], float) / max(hs["tal"])
    bx.fill_betweenx(np.repeat(ks, 2)[1:-1], 0, np.repeat(ts, 2), color=HAIR, lw=0)
    hk, kk = np.histogram([p["H"] for p in inne], bins=np.arange(0, 152.5, 2.5))
    tk = hk / max(1, hk.max())
    bx.barh((kk[:-1] + kk[1:]) / 2, tk, height=1.5, color=FG, lw=0)
    bx.set_xlim(0, 1.25)
    mono(bx, 0.42, float(kH[int(np.argmax(hH["tal"]))]) + 14, "høgda på stolar", color=DIM)
    mono(bx, 0.55, 57, "stolsete", color=DIM)
    mono(bx, 0.55, 30, "krakkar", color=FG)
    med, spr = prim(r, "P1"), prim(r, "P2")
    dom = r.get("dom", "")
    tittel = "Krakken står der setet står" if dom == "HELDT" else "Krakken og setet"
    under = "Ein krakk har ingen rygg. Høgda på krakken er setehøgda."
    hovud(fig, tittel, under)
    if med:
        fig.text(0.08, 0.835, "%d krakkar: median %s cm, spreiing %s %%.   Stolsete: %s cm, %s %%.   Stolhøgd: %s cm, %s %%."
                 % (r.get("n", len(inne)), tal(med["verdi"]), tal(100 * spr["verdi"]), tal(d["stolsete_band"]["median"]),
                    tal(100 * d["tersklar"]["sete_spreiing"]), "94", tal(100 * d["tersklar"]["H_spreiing"])),
                 family=MONO, fontsize=7.4, color=FG)
    fot(fig, ["fylt: krakk i utvalet · open: halden utanfor (fotskammel, barnekrakk, uviss kjelde) · grå punkt: setehøgda på %d stolar"
              % len(stol), "grått band: midtre halvdel av stolseta, %s til %s cm" % (tal(q1, 0), tal(q3, 0)), KJELDE], y=0.07)
    lagre(fig, "krakk")


# ================================================================ t3: armlenet
def fig_arm():
    d, r = FIG.get("t3_olboge"), RES.get("t3_olboge", {})
    if not d or not d.get("punkt"):
        return
    P = d["punkt"]
    H = np.array([p[3] for p in P], float)
    sete = np.array([p[4] for p in P], float)
    arm = np.array([p[6] for p in P], float)
    A, rygg = arm - sete, H - sete
    lo, hi = d["band"]
    fig = plt.figure(figsize=(7.6, 6.2))
    ax = fig.add_axes([0.06, 0.12, 0.42, 0.66])
    M = np.asarray(d["side_sete_paa_rad_60"], float)
    kart(ax, M, x0=30)
    ax.set_xlim(30, 130)
    ax.set_ylim(0, 135)
    naken(ax)
    ax.plot([30, 130], [60, 60], color=FG, lw=0.5)
    for y in (60 + lo, 60 + hi):
        ax.plot([30, 130], [y, y], color=FG, lw=0.5, dashes=(4, 3))
    mono(ax, 129, 61.5, "setet", ha="right", color=FG)
    mono(ax, 129, 60 + hi + 2.5, "%d til %d cm over setet" % (lo, hi), ha="right", color=FG)
    bx = fig.add_axes([0.58, 0.12, 0.36, 0.66])
    bx.axhspan(lo, hi, color=LYS, lw=0)
    bx.scatter(rygg, A, s=9, color=FG, lw=0, zorder=3)
    xa = np.array([max(15, np.percentile(rygg, 1)), np.percentile(rygg, 99)])
    h = prim(r, "helling")
    m = prim(r, "median_A")
    if h and m:
        bx.plot(xa, m["verdi"] + h["verdi"] * (xa - np.median(rygg)), color=FG, lw=0.9, zorder=4)
        xb = np.array([xa[0], min(xa[1], 46 * np.median(rygg) / m["verdi"])])
        bx.plot(xb, xb * (m["verdi"] / np.median(rygg)), color=DIM, lw=0.6, dashes=(4, 3), zorder=2)
    bx.set_xlim(10, 110)
    bx.set_ylim(0, 50)
    for s in ("top", "right"):
        bx.spines[s].set_visible(False)
    bx.set_xticks([20, 40, 60, 80, 100])
    bx.set_yticks([0, 10, 20, 30, 40, 50])
    bx.tick_params(length=2.5, width=0.5, labelsize=7.5, colors=DIM)
    for t in bx.get_xticklabels() + bx.get_yticklabels():
        t.set_family(MONO)
    mono(bx, 11, 47.5, "armlenet over setet, cm")
    mono(bx, 109, 1.5, "ryggen over setet, cm", ha="right")
    if h and m:
        mono(bx, xa[1] + 1.5, m["verdi"] + h["verdi"] * (xa[1] - np.median(rygg)), "målt", va="center", color=FG)
        ys = m["verdi"] * xa[1] / np.median(rygg)
        mono(bx, min(xa[1], 46 * np.median(rygg) / m["verdi"]) - 1.5, min(ys, 46) + 1.2, "om armlenet følgde ryggen", ha="right")
    dom = r.get("dom", "")
    hovud(fig, "Armlenet følgjer olbogen" if dom == "HELDT" else "Armlenet og olbogen",
          "Kor høgt over setet armlenet ligg, mot kor høg ryggen er.")
    mae = d.get("mae", {})
    if m and mae:
        fig.text(0.08, 0.835, "%d armstolar: armlenet %s cm over setet.   Snittfeil: frå setet %s cm · frå golvet %s cm · som del av høgda %s cm."
                 % (d["n"], tal(m["verdi"]), tal(mae["kropp"]), tal(mae["bord"]), tal(mae["storleik"])),
                 family=MONO, fontsize=7.4, color=FG)
    fot(fig, ["venstre: armstolane frå sida, rygg til venstre, kvar flytta så setet ligg på same line · høgre: éin prikk per armstol",
              "bandet %d til %d cm er olbogehøgda over setet hjå ein sitjande vaksen (Pheasant 1996)" % (lo, hi), KJELDE], y=0.07)
    lagre(fig, "armlene")


# ================================================================ t4: gradient eller øy
def fig_gradient():
    d, r = FIG.get("t4_gradient"), RES.get("t4_gradient", {})
    if not d:
        return
    L = d["linjer"][d["primaerlinje"]]
    S = d["snittsilhuettar_front"]["VA_alle_dateringar"]
    fig = plt.figure(figsize=(7.6, 6.4))
    n = len(S)
    for i, b in enumerate(S):
        ax = fig.add_axes([0.06 + i * 0.88 / n, 0.56, 0.88 / n * 0.96, 0.22])
        naken(ax)
        if b["n"]:
            M = np.array([[int(c) for c in rad] for rad in b["rader"]], float)
            M = np.where(M > 0, M * 10 + 5, 0)
            kart(ax, M, celle=2.0, nivaa=(25, 50, 75), glatt=0.8)
        ax.set_xlim(20, 100)
        ax.set_ylim(0, 150)
        mono(ax, 60, -18, "%d" % b["fraa"], ha="center", color=FG, fontsize=6.6)
        mono(ax, 60, -34, "n %d" % b["n"], ha="center", fontsize=6.0)
    bx = fig.add_axes([0.10, 0.16, 0.84, 0.27])
    sp = L["spleis"].get("50", {})
    if sp.get("verdi") is not None:
        bx.axhspan(sp["ki95"][0], sp["ki95"][1], color=LYS, lw=0)
        bx.axhline(sp["verdi"], color=FG, lw=0.6, dashes=(4, 3))
        mono(bx, 1903, sp["verdi"], "ei øy på 50 år", va="center", color=FG)
    bx.axhline(0, color=FG, lw=0.6)
    mono(bx, 1903, 0, "ingen kant", va="center", color=FG)
    ys = []
    for g in L["grenser"]:
        if g["S"] is None:
            continue
        ys += [g["S"]] + [v for v in g["ki95"] if v is not None]
        if g["ki95"][0] is not None:
            bx.plot([g["b"], g["b"]], g["ki95"], color=FG if g["brukt"] else DIM, lw=0.7)
        bx.scatter([g["b"]], [g["S"]], s=22, color=FG if g["brukt"] else "white", edgecolor=FG, lw=0.6, zorder=3)
    if sp.get("verdi") is not None:
        ys += list(sp["ki95"])
    if ys:
        a, b_ = min(ys + [0]), max(ys + [0])
        bx.set_ylim(a - 0.15 * (b_ - a), b_ + 0.15 * (b_ - a))
    bx.set_xlim(1640, 1900)
    for s in ("top", "right", "left"):
        bx.spines[s].set_visible(False)
    bx.set_yticks([])
    bx.set_xticks([g["b"] for g in L["grenser"]])
    bx.tick_params(length=2.5, width=0.5, labelsize=7.2, colors=DIM)
    for t in bx.get_xticklabels():
        t.set_family(MONO)
    mono(bx, 1641, bx.get_ylim()[1], "kor mykje meir stolane skil seg over året enn på same side av det", va="top")
    dom = r.get("dom", "")
    brukt = [g for g in L["grenser"] if g["brukt"] and g["S"] is not None]
    oey = [g["b"] for g in brukt if sp.get("verdi") is not None and g["ki95"][0] > 0 and g["S"] >= sp["verdi"]]
    if dom == "HELDT" or not oey:
        tittel, under = "Stilane er gradientar", "Trestolar før 1900, sedde framanfrå. Ingen av grenseåra er ein kant."
    else:
        ord_ = ["null", "éin", "to", "tre", "fire", "fem", "seks", "sju", "åtte", "ni", "ti"]
        tittel = "%s gradientar og %s kant" % (ord_[len(brukt) - len(oey)].capitalize(), ord_[len(oey)])
        under = "Trestolar før 1900, sedde framanfrå. Ved %s skil stolane seg meir over året enn femti års drift." % " og ".join(str(b_) for b_ in oey)
    hovud(fig, tittel, under)
    port = [p_ for p_ in r.get("port", []) if p_.get("ok") is False and p_.get("namn") != "alle portar"]
    linje = "%s stolar frå V&A, daterte innan 15 år · %d grenseår med nok par" % (heiltal(L["n"]), L["k"])
    if dom == "UGYLDIG" and port:
        linje += " · prøva er ugyldig etter eigen port"
    fig.text(0.08, 0.835, linje, family=MONO, fontsize=7.4, color=FG)
    liner = ["øvst: snittstolen per 25 år, alle V&A-stolane i utvalet · nedst: kant ved kvart grenseår med 95 % intervall; fylt prikk = nok par til å telje"]
    if dom == "UGYLDIG" and port:
        liner.append("porten som fall: ei planta øy på 100 år skulle gje minst like stort utslag som ei på 50, og gjorde det ikkje")
    fot(fig, liner + [KJELDE], y=0.09)
    lagre(fig, "gradient")


# ================================================================ t2: materialskiftet
def fig_materiale():
    d, r = FIG.get("t2_materiale"), RES.get("t2_materiale", {})
    if not d or "kart" not in d:
        return
    K = d["kart"]
    rekkje = [("arkiv", "tre før 1900"), ("WOOD", "tre frå 1925"), ("LINE", "stålrøyr frå 1925"), ("SHEET", "skal frå 1925")]
    du = d["del_utanfor"]["verdi"]
    ki = d["del_utanfor"].get("ki95", {})
    fig = plt.figure(figsize=(7.6, 5.4))
    for i, (k, namn) in enumerate(rekkje):
        ax = fig.add_axes([0.06 + i * 0.225, 0.30, 0.205, 0.50])
        naken(ax)
        if K[k].get("front"):
            M = np.asarray(K[k]["front"], float)
            M[M < 4] = 0
            kart(ax, M, celle=2.0, glatt=0.8)
        ax.set_xlim(14, 114)
        ax.set_ylim(0, 140)
        for y in (30, 60):
            ax.plot([14, 114], [y, y], color=FG, lw=0.4, dashes=(4, 3))
        mono(ax, 64, -11, namn, ha="center", color=FG, fontsize=7.4)
        mono(ax, 64, -21, "n %d" % K[k]["n"], ha="center", fontsize=6.4)
        if k != "arkiv":
            mono(ax, 64, -34, "ny fot %d %%" % round(100 * du["%s_front_fot" % k]), ha="center", color=FG, fontsize=7.0)
            mono(ax, 64, -44, "ny rygg %d %%" % round(100 * du["%s_front_rygg" % k]), ha="center", color=FG, fontsize=7.0)
    dom = r.get("dom", {})
    dn = dom.get("N1") if isinstance(dom, dict) else dom
    if dn == "HELDT":
        hovud(fig, "Materialet opnar éi sone", "Stolar frå 1925 sedde framanfrå, mot trestolane før 1900.")
    else:
        hovud(fig, "Røyret opna foten", "Ryggen vart ny i alle materiale, mest i tre. Føreseiinga om éi sone per materiale slo feil.")
    pa = next((p_ for p_ in r.get("primaer", []) if p_.get("namn", "").startswith("a_kryssing")), None)
    if pa:
        fig.text(0.08, 0.835, "kryssinga fot mot rygg: %s, intervall %s til %s, p = %s mot kravet 0,01 · tre held seg i den gamle foten: %s"
                 % (tal(pa["verdi"], 2), tal(pa["ki95"][0], 2), tal(pa["ki95"][1], 2), tal(pa["perm_p"], 3), tal(du["b_front"], 2)),
                 family=MONO, fontsize=7.4, color=FG)
    fot(fig, ["stipla liner: 30 og 60 cm · fot = under 30 cm, rygg = over 60 cm · stolar frå 1925, framanfrå",
              "ny = silhuetten i sona ligg lenger frå næraste trestol før 1900 enn 95 % av dei gamle trestolane ligg kvarandre",
              KJELDE], y=0.09)
    lagre(fig, "materiale")


# ================================================================ t1: setet på stolane ingen målte
def fig_sete():
    d, r = FIG.get("t1_sete"), RES.get("t1_sete", {})
    if not d or "punkt_VA" not in d:
        return
    R = np.array([[v if v is not None else np.nan for v in rad[:2]] for rad in d["punkt_VA"]["rader"]], float)
    H, s = R[:, 0], R[:, 1]
    fig = plt.figure(figsize=(7.6, 6.0))
    ax = fig.add_axes([0.08, 0.13, 0.66, 0.66])
    ax.scatter(H, s, s=5, color=FG, lw=0, alpha=0.75, zorder=3)
    xa = np.array([55.0, 150.0])
    ms, mH = float(np.nanmedian(s)), float(np.nanmedian(H))
    ax.plot(xa, [ms, ms], color=FG, lw=0.9)
    ax.plot(xa, ms / mH * xa, color=DIM, lw=0.6, dashes=(4, 3))
    ax.set_xlim(50, 155)
    ax.set_ylim(15, 85)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_xticks([60, 80, 100, 120, 140])
    ax.set_yticks([20, 40, 60, 80])
    ax.tick_params(length=2.5, width=0.5, labelsize=7.5, colors=DIM)
    for t in ax.get_xticklabels() + ax.get_yticklabels():
        t.set_family(MONO)
    mono(ax, 51, 82, "setehøgd frå 3D-modellen, cm")
    mono(ax, 154, 16.5, "høgda på stolen, cm", ha="right")
    mono(ax, 52, ms + 1.6, "same sete uansett storleik", color=FG)
    mono(ax, 150, min(80, ms / mH * 150) + 2.2, "sete som fast del av høgda", ha="right")
    bx = fig.add_axes([0.76, 0.13, 0.18, 0.66])
    bx.set_ylim(15, 85)
    naken(bx, behald=())
    hk, kk = np.histogram(s[~np.isnan(s)], bins=np.arange(15, 86, 2))
    bx.barh((kk[:-1] + kk[1:]) / 2, hk / max(1, hk.max()), height=1.4, color=FG, lw=0)
    sp_ = d.get("spreiing", {}).get("VA", {})
    dom = r.get("dom", {})
    d1 = dom.get("E1") if isinstance(dom, dict) else dom
    hovud(fig, "Setet held òg der ingen målte" if d1 == "HELDT" else "Setet på stolane ingen målte",
          "Stolar der museet aldri skreiv ned setehøgda. Ho er lesen av 3D-modellen." if d1 == "HELDT" else
          "Setehøgda varierer minst av måla, men ikkje nok til å halde kravet. Føreseiinga slo feil.")
    if sp_:
        v = sp_.get("rsd_log_sete_H_B_D") or [None] * 4
        fig.text(0.08, 0.835, "%s stolar · spreiing: sete %s %% · høgd %s %% · breidd %s %% · djupn %s %% · sete mot minste andre mål, retta for instrumentet: %s mot kravet under 0,80"
                 % (heiltal(len(H)), tal(100 * v[0]), tal(100 * v[1]), tal(100 * v[2]), tal(100 * v[3]), tal(sp_.get("forhold_korrigert", float("nan")), 2)),
                 family=MONO, fontsize=7.4, color=FG)
    fot(fig, ["éin prikk per stol · til høgre: fordelinga av setehøgda", KJELDE])
    lagre(fig, "sete")


for f in (fig_krakk, fig_arm, fig_gradient, fig_materiale, fig_sete):
    try:
        f()
    except Exception as e:
        import traceback
        print("FEIL i", f.__name__, traceback.format_exc()[-900:])
