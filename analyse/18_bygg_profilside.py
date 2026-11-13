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
                     "prove": "%d av %d føreseiingar heldt på %s stolar som ikkje var opna då dei vart skrivne ned" % (
                         sum(d == "HELDT" for d in domar), len(domar), "{:,}".format(t6["n"]).replace(",", " "))}

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

# 6 den andre prøva, modulane t1 til t5: berre det som alt er rekna og lagra då modulane vart opna
pf = os.path.join(HER, "forsegla2", "FIGURDATA.json")
D["p2"] = None
if UTVAL == "alle" and os.path.exists(pf) and os.path.exists(pr):
    FD = json.load(open(pf, encoding="utf-8"))
    RS = json.load(open(pr, encoding="utf-8")).get("modular", {})
    p2 = {}

    def prim(res, namn):
        return next((p for p in res.get("primaer", []) if p.get("namn", "").startswith(namn)), {})

    fa, ra = FD.get("t3_olboge"), RS.get("t3_olboge", {})
    if fa and fa.get("punkt"):                                   # armlenet: sideriss med setet på same line
        M = np.zeros((Y1, X1 - X0), np.float32)
        A = np.asarray(fa["side_sete_paa_rad_60"], np.float32) / 100.0      # 135 x 100, kolonnar 30 til 129
        M[:A.shape[0]] = A
        pkt = [[round(p[3] - p[4], 1), round(p[6] - p[4], 1)] for p in fa["punkt"]]
        p2["arm"] = {"kart": {**kode(M, False), "k": konturar(M, (0.1, 0.25, 0.5, 0.75))}, "n": fa["n"], "band": fa["band"],
                     "pkt": pkt, "mrygg": round(float(np.median([p[0] for p in pkt])), 1),
                     "median": prim(ra, "median_A").get("verdi"), "helling": prim(ra, "helling").get("verdi"),
                     "mae": fa["mae"], "dom": ra.get("dom")}
    fk, rk = FD.get("t5_krakk"), RS.get("t5_krakk", {})
    if fk and fk.get("krakk_punkt"):                             # krakken: høgd mot år, med stolseta bak
        p2["krakk"] = {"pkt": [[p["aar"], p["H"], int(p["status"] == "primaer")] for p in fk["krakk_punkt"] if p["aar"]],
                       "stol": [[a, v] for a, v in fk["stolsete_punkt_aar_cm"] if a], "band": fk["tersklar"]["P1"],
                       "n": rk.get("n"), "median": prim(rk, "P1").get("verdi"), "spreiing": prim(rk, "P2").get("verdi"),
                       "sete": [fk["stolsete_band"]["median"], fk["tersklar"]["sete_spreiing"]],
                       "H": [94.0, fk["tersklar"]["H_spreiing"]], "dom": rk.get("dom")}
    fg, rg = FD.get("t4_gradient"), RS.get("t4_gradient", {})
    if fg:                                                       # gradient eller øy: snittstolar og kant per grenseår
        L = fg["linjer"][fg["primaerlinje"]]
        ruter = []
        for b in fg["snittsilhuettar_front"]["VA_alle_dateringar"]:
            if b["n"]:
                m = np.array([[int(c) for c in rad] for rad in b["rader"]], np.float32)     # 75 x 60, rad 0 = golv, 2 cm
                ruter.append({"aar": b["fraa"], "n": b["n"], **kode(np.where(m > 0, m / 10 + 0.05, 0)[:, 10:50], False)})
        sp = L["spleis"].get("50", {})
        gr = [[g["b"], g["S"], g["ki95"][0], g["ki95"][1], int(g["brukt"])] for g in L["grenser"] if g["S"] is not None]
        oey = [g[0] for g in gr if g[4] and sp.get("verdi") is not None and g[2] > 0 and g[1] >= sp["verdi"]]
        p2["grad"] = {"ruter": ruter, "grenser": gr, "spleis": [sp.get("verdi")] + list(sp.get("ki95", [None, None])),
                      "n": L["n"], "brukt": sum(g[4] for g in gr), "oey": oey, "dom": rg.get("dom")}
    fm, rm = FD.get("t2_materiale"), RS.get("t2_materiale", {})
    du = (fm or {}).get("del_utanfor", {}).get("verdi")
    if du:                                                       # materialet: del med ny fot og ny rygg, framanfrå
        p2["mat"] = {k: [round(100 * du[k + "_front_fot"]), round(100 * du[k + "_front_rygg"])] for k in ("LINE", "SHEET", "WOOD")}

    # Lista over alle føreseiingane i den andre prøva, slik dei fall ut. Tap står som tap.
    kom = lambda x, d=2: ("%.*f" % (d, x)).replace(".", ",")
    liste = []
    t6 = RS.get("t6_saumar", {})
    if "primaer" in t6:
        a, b, c = t6["primaer"]
        liste += [[a["dom"], "understellet føreseier setesona, ikkje overdelen",
                   "%d %% mot %d %%" % (round(100 * a["verdi"]["understell->setesone"]), round(100 * a["verdi"]["understell->overdel"]))],
                  [b["dom"], "setesona daterer ikkje stolen", "%s mot kravet 0,90" % kom(b["verdi"]["setesone/gissing"], 3)],
                  [c["dom"], "ein stol sett saman av to ligg blant dei verkelege", "%d %%" % round(100 * c["verdi"]["innanfor"])]]
    if ra.get("dom"):
        liste.append([ra["dom"], "armlenet ligg 20 til 25 cm over setet", "%s cm" % kom(prim(ra, "median_A")["verdi"], 1)])
    if rk.get("dom"):
        liste.append([rk["dom"], "krakken står der stolsetet står", "%s cm" % kom(prim(rk, "P1")["verdi"], 1)])
    if rg.get("dom"):
        liste.append([rg["dom"], "stilskifta er gradientar", "kant ved %s" % " og ".join(str(v) for v in p2["grad"]["oey"]) if p2.get("grad", {}).get("oey") else ""])
    f1, r1 = FD.get("t1_sete"), RS.get("t1_sete", {})
    if isinstance(r1.get("dom"), dict):
        e1 = prim(r1, "E1a")
        liste += [[r1["dom"]["E1"], "setehøgda varierer minst, òg der ingen målte", "%s mot kravet 0,80" % kom(e1["verdi"])],
                  [r1["dom"]["E3"], "breiare stol, lågare sete", "kan ikkje skiljast frå instrumentet"]]
    if isinstance(rm.get("dom"), dict):
        pa = prim(rm, "a_kryssing")
        liste += [[rm["dom"]["N1"], "kvart materiale opnar si sone", "p = %s mot kravet 0,01" % kom(pa["perm_p"], 3)],
                  [rm["dom"]["E2"], "materialet bind strukturen, ikkje setet", "intervallet rekk null"]]
    tagg = lambda xs, t: [[x[0], x[1], t + (" · " + x[2] if x[2] else "")] for x in xs]
    liste = tagg(liste, "V&A og NM")
    prover = [{"namn": "Prøve 2", "kvar": "V&A og Nasjonalmuseet", "instrument": "3D-modellar frå eitt foto",
               "forsegla": "ebde1f9", "domar": [x[0] for x in liste]}]

    p1r = os.path.join(HER, "forsegla", "RESULTAT.json")         # den første prøva: setehøgda i Rijksmuseum
    if os.path.exists(p1r):
        R1 = json.load(open(p1r, encoding="utf-8"))
        dm, sp, sn = R1["dom"], R1["spreiing"], R1["snittfeil_cm"]
        dom = lambda k: "HELDT" if dm[k] else "SLO FEIL"
        l1 = [[dom("P1a"), "setehøgda varierer minst av måla", "sete %s, breidd %s, djupn %s, rygg %s" % (
                  kom(sp["sete"], 3), kom(sp["breidd"], 3), kom(sp["djupn"], 3), kom(sp["rygg"], 3))],
              [dom("P1b"), "spreiinga i setehøgd er under 0,10", kom(sp["sete"], 3)],
              [dom("P1c"), "spreiinga i rygghøgd er over 0,20", kom(sp["rygg"], 3)],
              [dom("P2a"), "tidsbolken forklarer under 20 % av setehøgda", "%d %%" % round(100 * R1["tidsbolk_del"]["sete"])],
              [dom("P2b"), "tidsbolken forklarer over 40 % av rygghøgda", "%d %%" % round(100 * R1["tidsbolk_del"]["rygg"])],
              [dom("P3"), "setet stig mindre enn 0,3 cm per cm totalhøgd", "%s [%s til %s]" % tuple(kom(v, 2) for v in R1["stiging"])],
              [dom("P4a"), "fast setehøgd treffer betre enn fast del av høgda", "%s mot %s cm" % (kom(sn["fast verdi"]), kom(sn["fast del av H"]))],
              [dom("P4b"), "ei potenslov slår fast setehøgd med høgst 0,3 cm", "%s mot %s cm" % (kom(sn["potenslov"]), kom(sn["fast verdi"]))]]
        l1 = tagg(l1, "Rijksmuseum")
        prover.insert(0, {"namn": "Prøve 1", "kvar": "Rijksmuseum", "instrument": "katalogmål, %d stolar" % R1["n"], "forsegla": "0ab99d0",
                          "domar": [x[0] for x in l1]})
        liste = l1 + liste

    p3r = os.path.join(HER, "forsegla3", "RESULTAT.json")
    if os.path.exists(p3r):                                      # den tredje prøva: same føreseiingar i The Met
        R3 = json.load(open(p3r, encoding="utf-8"))
        m1, m2, m3 = R3.get("M1_krakk", {}), R3.get("M2_armlene", {}), R3.get("M3_kant_1712", {})
        l3 = []
        if m1.get("dom"):
            p_ = {x["namn"][:2]: x for x in m1.get("primaer", [])}
            l3.append([m1["dom"], "krakken står der stolsetet står",
                       "spreiing %s mot kravet 0,126" % kom(p_["P2"]["verdi"], 3) if "P2" in p_ else ""])
        if m2.get("dom"):
            l3.append([m2["dom"], "armlenet ligg i olbogehøgd", "Met katalogfører ikkje armhøgd"
                       if m2.get("flyt", {}).get("analysert") == 0 else ""])
        p3b = os.path.join(HER, "forsegla3", "RESULTAT_M3.json")
        m3 = json.load(open(p3b, encoding="utf-8")) if os.path.exists(p3b) else m3
        if m3.get("dom"):
            l3.append([m3["dom"], "1712 er ikkje ein kant", m3.get("kort", "krev sidesilhuettar")])
        l3 = tagg(l3, "The Met")
        prover.append({"namn": "Prøve 3", "kvar": "The Met", "instrument": "katalogmål", "forsegla": "f36e692",
                       "domar": [x[0] for x in l3]})
        liste = liste + l3
    p4r = os.path.join(HER, "forsegla4", "RESULTAT.json")
    if os.path.exists(p4r):                                      # den fjerde prøva: overdel mot understell
        R4 = json.load(open(p4r, encoding="utf-8"))["resultat"]
        t1, t2, t3 = R4["T1_overdelen_er_eldre"], R4["T2_ikkje_tida"], R4["T3_viktoriansk"]
        l4 = tagg([[t1["dom"], "ein stol som tek opp att ein eldre stil, har eldre overdel enn understell", "skilnad %d år" % round(t1["median"])],
                   [t2["dom"], "skilnaden kjem av attopptakinga, ikkje av tida", "%d år mot samtidige" % round(t2["differanse"])],
                   [t3["dom"], "viktorianske stolar har eldre overdel enn understell", "skilnad %d år" % round(t3["median"])]], "V&A og NM")
        prover.append({"namn": "Prøve 4", "kvar": "Overdel mot understell", "instrument": "3D-modellar, V&A og NM", "forsegla": "975c13c",
                       "domar": [x[0] for x in l4]})
        liste = liste + l4
    p5r = os.path.join(HER, "forsegla5", "RESULTAT.json")
    if os.path.exists(p5r):                                      # den femte prøva: setet etter materialskiftet
        R5 = json.load(open(p5r, encoding="utf-8"))["resultat"]
        a, b, c = R5["R1_setet_samlar_seg"], R5["R2_ikkje_tida"], R5["R3_ryggen_samlar_seg_ikkje"]
        l5 = tagg([[a["dom"], "setet i nye material spreier seg først og samlar seg så", "forhold %s mot kravet 1,30" % kom(a["forhold"])],
                   [b["dom"], "det er materialet som samlar setet, ikkje tida", "%s mot kravet 1,25" % kom(b["forhold"])],
                   [c["dom"], "setet samlar seg meir enn høgda", "differanse %s" % kom(c["differanse"])]], "V&A og NM")
        prover.append({"namn": "Prøve 5", "kvar": "Setet etter materialskiftet", "instrument": "3D-modellar, V&A og NM", "forsegla": "eafe7d5",
                       "domar": [x[0] for x in l5]})
        liste = liste + l5
    rekkjefolgje = {"HELDT": 0, "SLO FEIL": 1, "UGYLDIG": 2, "UTSETT": 3}
    p2["liste"] = sorted(liste, key=lambda x: rekkjefolgje.get(x[0], 4))
    p2["prover"] = [{**p, "tal": {d: p["domar"].count(d) for d in ("HELDT", "SLO FEIL", "UGYLDIG", "UTSETT")}} for p in prover]
    D["p2"] = p2 or None

# 7 den fjerde prøva: kvar stol med alderen til overdelen og understellet, og dei sju likaste av kvar
p4f, p4r = (os.path.join(HER, "forsegla4", f) for f in ("FIGURDATA.json", "RESULTAT.json"))
D["alder"] = None
if UTVAL == "alle" and os.path.exists(p4f) and os.path.exists(p4r):
    idx = {s["id"]: i for i, s in enumerate(MED_AAR)}
    GK = {"attopptaking": 1, "viktoriansk": 2}
    rad = [[idx[s["id"]], round(s["overdel"]), round(s["understell"]), GK.get(s["gruppe"], 0),
            [idx[j] for j in s["nabo_overdel"] if j in idx], [idx[j] for j in s["nabo_understell"] if j in idx]]
           for s in json.load(open(p4f, encoding="utf-8"))["stolar"] if s["id"] in idx]
    kand = [r for r in rad if r[3] == 1 and abs(r[1] - r[2]) <= 10]   # førehandsval: attopptakinga som går lengst attende i begge delane
    val = max(kand, key=lambda r: min(MED_AAR[r[0]]["aar"] - r[1], MED_AAR[r[0]]["aar"] - r[2]))[0] if kand else rad[0][0]
    R4 = json.load(open(p4r, encoding="utf-8"))["resultat"]
    D["alder"] = {"rad": rad, "val": val, "t1": R4["T1_overdelen_er_eldre"], "t2": R4["T2_ikkje_tida"], "t3": R4["T3_viktoriansk"]}

# 8 den femte prøva: fire stablar (tre og nye material, tidleg og seint) med setehøgd og totalhøgd for kvar stol
p5f, p5r = (os.path.join(HER, "forsegla5", f) for f in ("FIGURDATA.json", "RESULTAT.json"))
D["held"] = None
if UTVAL == "alle" and os.path.exists(p5f) and os.path.exists(p5r):
    F5 = json.load(open(p5f, encoding="utf-8"))["stolar"]
    R5 = json.load(open(p5r, encoding="utf-8"))
    SENT = {}
    for s in F5:
        if s["id"] in SIDE:
            k = np.where(SIDE[s["id"]].any(0))[0]
            SENT[s["id"]] = np.roll(SIDE[s["id"]], 80 - (k[0] + k[-1] + 1) // 2, axis=1) if len(k) else SIDE[s["id"]]
    celler = []
    for mat, mnamn in (("tre", "Tre"), ("nye", "Røyr, kryssfiner og plast")):
        for per, pnamn in (("tidleg", "1920 til 1949"), ("seint", "1965 til 1999")):
            ss = [s for s in F5 if s["mat"] == mat and s["per"] == per and s["id"] in SENT]
            celler.append({**figur(ss, SENT, nivaa=(0.5,)), "namn": mnamn, "per": pnamn,
                           "t": [[round(s["sete"]), round(s["H"])] for s in ss],
                           "sp": [round(R5["spreiing"]["%s_%s_sete" % (mat, per)], 2), round(R5["spreiing"]["%s_%s_H" % (mat, per)], 2)]})
    D["held"] = {"celler": celler, "dom": [R5["resultat"]["R1_setet_samlar_seg"]["dom"], R5["resultat"]["R3_ryggen_samlar_seg_ikkje"]["dom"]]}

MAL =open(os.path.join(HER, "figurar", "profil_mal.html"), encoding="utf-8").read()
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
