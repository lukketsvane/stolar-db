"""18_bygg_profilside.py - byggjer den interaktive sida «Stolen i profil» frå silhuettane.

  python analyse/18_bygg_profilside.py dev     # dei opne stolane (opplæringshalvparten)
  python analyse/18_bygg_profilside.py alle    # alle; nektar før den andre prøva er forsegla og køyrd

Ut: analyse/figurar/profil.html (innhaldet utan <html>-skal, slik førehandsvisinga vil ha det).
"""
import base64, csv, json, os, re, sys
import numpy as np
import cv2
import contourpy

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
UTVAL = sys.argv[1] if len(sys.argv) > 1 else "dev"
if UTVAL == "alle" and not os.path.exists(os.path.join(HER, "forsegla2", "RESULTAT.json")):
    sys.exit("Stoppa: dei tilbakehaldne stolane er ikkje opna enno.")

rein = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "stolar_reinsa.csv"), encoding="utf-8-sig"))}
ST = {r["Objekt-ID"]: r for r in csv.DictReader(open(os.path.join(os.path.dirname(HER), "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline=""))}
pre = "dev_" if UTVAL == "dev" else ""
maal = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", pre + "mesh_maal.csv"), encoding="utf-8"))}
z = np.load(os.path.join(HER, "data", pre + "silhuettar.npz" if UTVAL == "dev" else "mesh_silhuettar.npz"))
SIDE = dict(zip(z["ids"], np.unpackbits(z["side"], axis=-1)))
FRONT = dict(zip(z["ids"], np.unpackbits(z["front"], axis=-1)))
TOTALT = sum(1 for r in rein.values() if r["vaksenstol"] == "1" and r["maal_ok"] == "1")


def utstrekning(img):
    k = np.where(img.any(0))[0]
    r = np.where(img.any(1))[0]
    return (int(k[0]), int(k[-1]), int(r[0]), int(r[-1])) if len(k) else (0, 0, 0, 0)


STOLAR = []
for cid in SIDE:
    r, m = rein.get(cid), maal.get(cid)
    if not r or not m or r["vaksenstol"] != "1":
        continue
    if set(filter(None, (m.get("flagg") or "").split(";"))) & {"opp_ikkje_y", "opp_ned?", "silhuett_klipt"}:
        continue
    H, B, D = float(r["H"]), float(r["B"]), float(r["D"])
    k0, k1, r0, r1 = utstrekning(SIDE[cid])
    f0, f1, _, _ = utstrekning(FRONT[cid])
    if (k1 - k0) > 1.5 * D + 10 or (f1 - f0) > 1.5 * B + 10 or abs(r1 + 1 - H) > 6:
        continue
    aar = float(r["aar_fraa"]) if r["aar_fraa"] else 0
    STOLAR.append({"id": cid, "aar": int(aar) if aar >= 1000 else None, "H": H, "type": r["type"],
                   "sete": float(m["sete_cm"]) if m.get("sete_cm") else None,
                   "kat": float(r["sete"]) if r["sete_ok"] == "1" else None})
N = len(STOLAR)
MED_AAR = sorted([s for s in STOLAR if s["aar"]], key=lambda s: (s["aar"], s["id"]))
SETE = float(np.median([s["sete"] for s in STOLAR if s["sete"]]))
X0, X1, Y1 = 30, 130, 146                               # utsnittet i cm


def stabel(stolar, bilete, vekter=None):
    a = np.stack([bilete[s["id"]] for s in stolar]).astype(np.float32)
    p = a.mean(0) if vekter is None else np.tensordot(vekter / vekter.sum(), a, axes=1)
    return p[:Y1, X0:X1]


def kode(p, halv=True):
    """Stabel -> base64 av uint8, rad 0 = øvst. halv=True gjev 2 cm per punkt."""
    if halv:
        p = cv2.resize(p, (p.shape[1] // 2, p.shape[0] // 2), interpolation=cv2.INTER_AREA)
    return {"w": int(p.shape[1]), "h": int(p.shape[0]),
            "b": base64.b64encode(np.clip(np.round(p[::-1] * 255), 0, 255).astype(np.uint8).tobytes()).decode()}


def konturar(p, nivaa):
    """Glatte nivåkurver i cm (x frå venstre i utsnittet, y frå golvet), éin desimal."""
    g = cv2.GaussianBlur(p, (0, 0), 1.3)
    cg = contourpy.contour_generator(x=np.arange(g.shape[1]) + 0.5, y=np.arange(g.shape[0]) + 0.5, z=g)
    ut = []
    for nv in nivaa:
        for l in cg.lines(nv):
            if len(l) >= 8:
                l = cv2.approxPolyDP(l.astype(np.float32).reshape(-1, 1, 2), 0.25, False)[:, 0, :]
                ut.append([nv] + [round(float(v), 1) for xy in l for v in xy])
    return ut


def figur(stolar, bilete, nivaa=(0.5,), halv=True):
    p = stabel(stolar, bilete)
    return {**kode(p, halv), "k": konturar(p, nivaa), "n": len(stolar)}


rs = lambda x: float(1.4826 * np.median(np.abs(x - np.median(x))) / np.median(x))
D = {"n": N, "totalt": TOTALT, "sete": round(SETE, 1), "utval": UTVAL, "x0": X0, "x1": X1, "y1": Y1}

# 1 kart
D["kart"] = figur(STOLAR, SIDE, nivaa=(0.1, 0.25, 0.5, 0.75), halv=False)
D["kartf"] = figur(STOLAR, FRONT, nivaa=(0.1, 0.25, 0.5, 0.75), halv=False)

# 2 tidsglidar: stolar nær eit år, vekta med avstand i tid
AAR = list(range(1600, 2001, 10))
aar = np.array([s["aar"] for s in MED_AAR], float)
ramer, neff = [], []
for y in AAR:
    w = np.exp(-0.5 * ((aar - y) / 22.0) ** 2)
    ramer.append(kode(stabel(MED_AAR, SIDE, w))["b"])
    neff.append(int(round(float(w.sum() ** 2 / (w ** 2).sum()))))
D["tid"] = {"aar": AAR, "ramer": ramer, "n": neff, "w": (X1 - X0) // 2, "h": Y1 // 2}

# 3 alle stolane som omriss
CELLE = 80
sil = []
for s in MED_AAR:
    img = SIDE[s["id"]][:150].astype(np.uint8)
    k0, k1, _, _ = utstrekning(img)
    dx = CELLE / 2 - (k0 + k1 + 1) / 2
    cs, _ = cv2.findContours(img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    d = ""
    for c in cs:
        if cv2.contourArea(c) < 3:
            continue
        c = cv2.approxPolyDP(c, 0.55, True)[:, 0, :]
        if len(c) < 3:
            continue
        d += "M" + "L".join("%d %d" % (round(x + dx), 150 - y) for x, y in c) + "Z"
    st = ST.get(s["id"], {})
    ks = [0, 0, 0]
    if s["sete"] and 34 <= s["sete"] <= 56:                      # til kimærane: setehøgd, bakkant og djupn på setet
        kk = np.where(img[max(int(round(s["sete"])) - 4, 0):int(round(s["sete"]))].any(0))[0]
        if len(kk):
            ks = [int(round(s["sete"])), int(round(kk[0] + dx)), int(kk[-1] - kk[0] + 1)]
    sil.append([s["aar"], d, st.get("Nasjonalmuseet", ""), (st.get("Namn") or "").strip()[:60]] + ks)
D["sil"] = sil
pj = os.path.join(HER, "data", "saumar_dev.json")
D["saum"] = json.load(open(pj, encoding="utf-8")) if UTVAL == "dev" and os.path.exists(pj) else None
pr = os.path.join(HER, "forsegla2", "RESULTAT.json")
if UTVAL == "alle" and os.path.exists(pr):
    # tala frå den forsegla prøva (modul t6) på dei tilbakehaldne stolane
    t6 = json.load(open(pr, encoding="utf-8")).get("modular", {}).get("t6_saumar")
    if t6 and "primaer" in t6:
        dat = t6["sekundaer"]["dateringsfeil_aar"]
        domar = [p["dom"] for p in t6["primaer"]]
        D["saum"] = {"n": t6["n"], "uo": round(100 * t6["primaer"][0]["verdi"]["understell->overdel"]),
                     "us": round(100 * t6["primaer"][0]["verdi"]["understell->setesone"]),
                     "dat": {k: round(v) for k, v in dat.items()}, "kim": round(100 * t6["primaer"][2]["verdi"]["innanfor"]),
                     "tidskurve": t6["sekundaer"]["tidskurve"],
                     "prove": "prøvd på %s nye stolar: %d av %d føreseiingar heldt" % (
                         "{:,}".format(t6["n"]).replace(",", " "), sum(d == "HELDT" for d in domar), len(domar))}

# 4 centimeter mot proporsjon
Hmed = float(np.median([s["H"] for s in STOLAR]))


def skalert(img, H):
    f = Hmed / H
    ny = cv2.resize(img.astype(np.uint8), None, fx=f, fy=f, interpolation=cv2.INTER_NEAREST)
    ut = np.zeros((200, 160), np.uint8)
    h = min(ny.shape[0], 200)
    k0 = int(round(80 - 80 * f))
    a, b = max(k0, 0), min(k0 + ny.shape[1], 160)
    ut[:h, a:b] = ny[:h, a - k0:b - k0]
    return ut


SKAL = {s["id"]: skalert(SIDE[s["id"]], s["H"]) for s in STOLAR}
sc = np.array([s["sete"] for s in STOLAR if s["sete"]])
sd = np.array([s["sete"] / s["H"] for s in STOLAR if s["sete"]])
D["golv"] = figur(STOLAR, SIDE, nivaa=(0.25, 0.5))
D["prop"] = figur(STOLAR, SKAL, nivaa=(0.25, 0.5))
D["spreiing"] = [round(100 * rs(sc), 1), round(100 * rs(sd), 1)]

# 5 materialskiftet
RX_LINE = re.compile(r"stål|aluminium|jern|metall|krom", re.I)
RX_FLATE = re.compile(r"kryssfiner|finer|laminat|sponplate|plast|glasfiber|polyprop|polyester|polyetylen|polykarbonat|polyamid|melamin|akryl", re.I)


def klasse(s):
    m = ST.get(s["id"], {}).get("Materialar", "")
    return "line" if RX_LINE.search(m) else "flate" if RX_FLATE.search(m) else "tre"


mat = []
for namn, gr in (("tre, før 1900", [s for s in MED_AAR if s["aar"] < 1900 and klasse(s) == "tre"]),
                 ("stålrøyr og stong, frå 1925", [s for s in MED_AAR if s["aar"] >= 1925 and klasse(s) == "line"]),
                 ("plate og skal, frå 1925", [s for s in MED_AAR if s["aar"] >= 1925 and klasse(s) == "flate"])):
    kat = [s["kat"] for s in gr if s["kat"]]
    mat.append({"namn": namn, "n": len(gr), "H": round(float(np.median([s["H"] for s in gr]))),
                "sete": round(float(np.median(kat))) if kat else None,
                "side": figur(gr, SIDE), "front": figur(gr, FRONT)})
D["mat"] = mat

MAL = open(os.path.join(HER, "figurar", "profil_mal.html"), encoding="utf-8").read()
ut = MAL.replace('"__DATA__"', json.dumps(D, ensure_ascii=False, separators=(",", ":")))
p = os.path.join(HER, "figurar", "profil.html")
open(p, "w", encoding="utf-8", newline="\n").write(ut)
print("skrive:", p, "| %d KB | stolar: %d av %d | med år: %d" % (len(ut.encode("utf-8")) // 1024, N, TOTALT, len(MED_AAR)))
# same side med skal, til lokal vising (førehandsvisinga legg til sitt eige skal)
open(os.path.join(HER, "figurar", "profil_lokal.html"), "w", encoding="utf-8", newline="\n").write(
    '<!doctype html><html lang="nn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,'
    'initial-scale=1,viewport-fit=cover"></head><body>' + ut + "</body></html>")

# Nettstadsutgåva til traktat.iverfinne.no: heilt dokument med meny. Byggjaren i FORML-RE set inn
# kjeldesummen og «ressursar»-menyen (etter tl;dr-lenkja).
hovud, resten = ut.split("<style>", 1)
nettstad = ('<!doctype html>\n<html lang="nn">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            '<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme:light)">\n'
            '<meta name="theme-color" content="#080808" media="(prefers-color-scheme:dark)">\n'
            '<meta name="formlaere-source" content="@@SOURCE_HASH@@">\n'
            '<title>formlære · stolen i profil</title>\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400&family=Literata:opsz,wght@7..72,400&display=swap">\n'
            '</head>\n<body>\n<style>' + resten + "\n</body>\n</html>\n")
nettstad = nettstad.replace('<div class="page">', '<div class="page">\n<nav aria-label="Dokument og lesemåte">\n'
                            '  <span class="links"><a href="/kortversjon/">tl;dr</a></span>\n  <a href="/">heile teksten</a>\n</nav>', 1)
nettstad = nettstad.replace('href="https://traktat.iverfinne.no/stol-db/"', 'href="/stol-db/"')
assert nettstad.count("@@SOURCE_HASH@@") == 1 and nettstad.count(">tl;dr</a>") == 1
open(os.path.join(HER, "figurar", "profil_nettstad.html"), "w", encoding="utf-8", newline="\n").write(nettstad)
print("skrive: profil_nettstad.html")
