"""22_met_prove.py - den tredje forsegla prøva: krakken og armlenet i katalogen til The Met.

Skriptet og forsegla3/FORESEIINGAR.json er skrivne og pusha FØR katalogen er henta. Skriptet skal
ikkje endrast etterpå; avvik blir førte i forsegla3/RESULTAT.json under «avvik».

  python analyse/22_met_prove.py --haust   Lastar ned MetObjects.csv frå den låste commiten i Met sitt opne
                                           repo. Nektar om FORESEIINGAR.json og dette skriptet ikkje ligg
                                           uendra i ein commit som finst på ei fjerngrein.
  python analyse/22_met_prove.py --opne    Køyrer M1 (krakken) og M2 (armlenet) éin gong. Nektar om
                                           RESULTAT.json alt finst. Skriv RESULTAT.json og FIGURDATA.json.
  python analyse/22_met_prove.py --sjolvtest   Prøver tolkinga av dimensjonsteksten på oppdikta døme.

MetObjects.csv blir ikkje committa (341 MB); sjekksummen blir lagra i HAUST.json.
"""
import csv, datetime, hashlib, json, os, re, subprocess, sys, urllib.request
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.dirname(HER)
F3 = os.path.join(HER, "forsegla3")
P_FORE = os.path.join(F3, "FORESEIINGAR.json")
P_CSV = os.path.join(F3, "MetObjects.csv")
P_HAUST = os.path.join(F3, "HAUST.json")
P_RES = os.path.join(F3, "RESULTAT.json")
P_FIG = os.path.join(F3, "FIGURDATA.json")
F = json.load(open(P_FORE, encoding="utf-8"))
no = lambda: datetime.datetime.now().astimezone().isoformat(timespec="seconds")
csv.field_size_limit(10 ** 8)


def git(*a):
    return subprocess.run(["git", "-C", ROT] + list(a), capture_output=True, text=True, encoding="utf-8")


def normalisert(p):
    return open(p, "rb").read().replace(b"\r\n", b"\n")


def sjekk_forsegla():
    """Begge filene må liggje uendra i siste commit som rørte dei, og den commiten må finnast på ei fjerngrein."""
    for rel in ("analyse/forsegla3/FORESEIINGAR.json", "analyse/22_met_prove.py"):
        c = git("log", "-1", "--format=%H", "--", rel).stdout.strip()
        if not c:
            sys.exit("Stoppa: %s er ikkje committa." % rel)
        i_commit = git("show", "%s:%s" % (c, rel)).stdout.replace("\r\n", "\n").encode("utf-8")
        if i_commit != normalisert(os.path.join(ROT, rel)):
            sys.exit("Stoppa: %s er endra etter siste commit." % rel)
        if not git("branch", "-r", "--contains", c).stdout.strip():
            sys.exit("Stoppa: commiten %s med %s er ikkje pusha." % (c[:8], rel))
    return git("log", "-1", "--format=%H", "--", "analyse/forsegla3/FORESEIINGAR.json").stdout.strip()


# ------------------------------------------------------------------ tolking av dimensjonsteksten
TAL = r"(\d+(?:[.,]\d+)?)"
CM_PARENTES = re.compile(r"\(\s*" + TAL + r"(?:\s*[x×]\s*" + TAL + r")?(?:\s*[x×]\s*" + TAL + r")?\s*cm\s*\)", re.I)
CM_FRI = re.compile(TAL + r"(?:\s*[x×]\s*" + TAL + r")?(?:\s*[x×]\s*" + TAL + r")?\s*cm\b", re.I)
H_MERKE = re.compile(r"(^|[^a-z])h(\.|\b)|height", re.I)
IKKJE_HEIL = re.compile(r"seat|arm|back|rail|leg|crest|stretcher|cushion|frame|base\b|top\b|leaf|closed|without|apron|splat|foot|post|rung|slat|panel", re.I)


def segment(dims):
    """Del dimensjonsteksten i (merkelapp, første cm-verdi) per segment."""
    ut = []
    for seg in re.split(r";|\r?\n|\|", dims or ""):
        seg = seg.strip()
        if not seg:
            continue
        m = CM_PARENTES.search(seg) or CM_FRI.search(seg)
        if not m:
            continue
        d = re.search(r"\d", seg)
        merkelapp = seg[:d.start()].strip().lower() if d else ""
        try:
            ut.append((merkelapp, float(m.group(1).replace(",", "."))))
        except ValueError:
            continue
    return ut


def maal(dims):
    """(H, sete, arm) i cm frå Met sin dimensjonstekst, etter reglane i FORESEIINGAR.json."""
    H = sete = arm = None
    seg = segment(dims)
    open_ = [v for l, v in seg if "open" in l and not IKKJE_HEIL.search(l.replace("open", ""))]
    for l, v in seg:
        if sete is None and "seat" in l and (H_MERKE.search(l) or l.rstrip(":. ").endswith("seat")):
            sete = v
        elif arm is None and re.search(r"\barms?\b", l) and H_MERKE.search(l):
            arm = v
        elif H is None and not IKKJE_HEIL.search(l) and (l == "" or re.match(r"^(overall|h\b|h\.|height|dimensions)", l)
                                                         or "open" in l):
            H = v
    if open_:
        H = open_[0]
    return H, sete, arm


def sjolvtest():
    dome = [("H. 39 1/2 in. (100.3 cm); W. 24 in. (61 cm); D. 21 in. (53.3 cm); Seat H. 17 in. (43.2 cm)", (100.3, 43.2, None)),
            ("Overall: 34 1/2 x 21 x 19 in. (87.6 x 53.3 x 48.3 cm)", (87.6, None, None)),
            ("H. 45 in. (114.3 cm); Seat H. 16 3/4 in. (42.5 cm); Arm H. 25 1/2 in. (64.8 cm)", (114.3, 42.5, 64.8)),
            ("Open: H. 18 in. (45.7 cm); Closed: H. 30 in. (76.2 cm)", (45.7, None, None)),
            ("H. of seat 17 in. (43.2 cm); H. to arms 26 in. (66 cm); H. 40 in. (101.6 cm)", (101.6, 43.2, 66.0)),
            ("H. 18 in. (45.7 cm)", (45.7, None, None))]
    feil = 0
    for tekst, venta in dome:
        fekk = maal(tekst)
        ok = fekk == venta
        feil += not ok
        print("ok  " if ok else "FEIL", fekk, "<-", tekst)
    sys.exit(1 if feil else 0)


# ------------------------------------------------------------------ statistikk
rs = lambda x: float(1.4826 * np.median(np.abs(x - np.median(x))) / np.median(x))


def klynge(nummer):
    """Same sett: Object Number utan siste ledd når det har minst tre ledd (1972.130.1 og 1972.130.2 er eitt sett)."""
    n = re.sub(r"[a-z,\s]+$", "", (nummer or "").strip().lower())
    ledd = n.split(".")
    return ".".join(ledd[:-1]) if len(ledd) >= 3 else n


def bootstrap(klyngjer, fn, n, seed):
    """Klyngebootstrap: trekk sett med tilbakelegging, rekn fn på indeksane."""
    rng = np.random.default_rng(seed)
    grupper = {}
    for i, k in enumerate(klyngjer):
        grupper.setdefault(k, []).append(i)
    g = list(grupper.values())
    ut = []
    for _ in range(n):
        idx = np.concatenate([g[j] for j in rng.integers(0, len(g), len(g))])
        ut.append(fn(idx))
    return np.asarray(ut, float)


def theil_sen(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    i, j = np.triu_indices(len(x), 1)
    dx = x[j] - x[i]
    ok = dx != 0
    return float(np.median((y[j] - y[i])[ok] / dx[ok])) if ok.any() else float("nan")


def r(v, d=4):
    return None if v is None or (isinstance(v, float) and not np.isfinite(v)) else round(float(v), d)


# ------------------------------------------------------------------ innhausting
def haust():
    c = sjekk_forsegla()
    K = F["kjelde"]
    print("forsegla i", c[:8], "| lastar ned", K["url"])
    req = urllib.request.Request(K["url"], headers={"User-Agent": "research-script/1.0"})
    h = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=120) as svar, open(P_CSV, "wb") as f:
        while True:
            b = svar.read(1 << 20)
            if not b:
                break
            h.update(b)
            f.write(b)
    d = {"tid": no(), "forsegla_commit": c, "url": K["url"], "bytes": os.path.getsize(P_CSV), "sha256": h.hexdigest()}
    json.dump(d, open(P_HAUST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(d, ensure_ascii=False))


# ------------------------------------------------------------------ prøva
def les():
    M1, M2 = F["M1_krakk"]["utval"], F["M2_armlene"]["utval"]
    rx_krakk, rx_arm = re.compile(M1["objektnamn"], re.I), re.compile(M2["objektnamn"], re.I)
    termar = [(g, re.compile(m, re.I)) for g, m in M1["namnetermar"]]
    krakk, arm = [], []
    with open(P_CSV, encoding="utf-8-sig", newline="") as f:
        for rad in csv.DictReader(f):
            on = (rad.get("Object Name") or "").strip()
            erk, era = bool(rx_krakk.search(on)), bool(rx_arm.search(on))
            if not (erk or era):
                continue
            H, sete, armh = maal(rad.get("Dimensions") or "")
            try:
                aar = int(rad.get("Object Begin Date") or "")
            except ValueError:
                aar = None
            rec = {"id": rad.get("Object ID"), "nummer": rad.get("Object Number"), "avd": rad.get("Department"),
                   "namn": on, "tittel": (rad.get("Title") or "")[:80], "aar": aar, "kultur": (rad.get("Culture") or "")[:40],
                   "H": H, "sete": sete, "arm": armh, "klynge": klynge(rad.get("Object Number"))}
            if erk:
                tekst = (re.sub(r"\([^()]*\)", " ", rec["tittel"]) + " " + on).lower()
                rec["namnegruppe"] = next((g for g, rx in termar if rx.search(tekst)), None)
                krakk.append(rec)
            if era:
                arm.append(rec)
    return krakk, arm


def m1(krakk):
    S = F["M1_krakk"]
    prim_avd = set(S["utval"]["avdelingar_primaer"])
    flyt = {"inn": len(krakk)}
    rest = [k for k in krakk if k["avd"] in prim_avd]; flyt["andre_avdelingar"] = len(krakk) - len(rest)
    a = [k for k in rest if k["namnegruppe"] is None]; flyt["namneregel"] = len(rest) - len(a)
    hogd = lambda k: k["H"] if k["H"] is not None else k["sete"]
    p = [k for k in a if hogd(k) is not None]; flyt["utan_hogd"] = len(a) - len(p)
    flyt["primaer"] = len(p)
    h = np.array([hogd(k) for k in p], float)
    kl = [k["klynge"] for k in p]
    T = S["tersklar"]
    port = [{"namn": "n", "verdi": len(p), "terskel": T["n_min"], "ok": len(p) >= T["n_min"]},
            {"namn": "klyngjer", "verdi": len(set(kl)), "terskel": T["klyngjer_min"], "ok": len(set(kl)) >= T["klyngjer_min"]}]
    res = {"flyt": flyt, "port": port}
    if not all(x["ok"] for x in port):
        res["dom"] = "UGYLDIG"
        return res, p
    bm = bootstrap(kl, lambda i: np.median(h[i]), F["n_boot"], F["froe"])
    bs = bootstrap(kl, lambda i: rs(h[i]), F["n_boot"], F["froe"])
    med, spr, ovre = float(np.median(h)), rs(h), float(np.percentile(bs, 97.5))
    prim = [{"namn": "P1 median i kvartilbreidda for stolsete", "verdi": r(med, 2), "ki95": [r(np.percentile(bm, 2.5), 2), r(np.percentile(bm, 97.5), 2)],
             "terskel": T["P1"], "held": T["P1"][0] <= med <= T["P1"][1]},
            {"namn": "P2 robust spreiing under midtpunktet", "verdi": r(spr), "ki95": [r(np.percentile(bs, 2.5)), r(ovre)],
             "terskel": T["P2"], "held": spr < T["P2"]},
            {"namn": "P3 øvre grense under spreiinga i totalhøgd", "verdi": r(ovre), "terskel": T["P3"], "held": ovre < T["P3"]}]
    res["primaer"] = prim
    res["dom"] = "HELDT" if all(x["held"] for x in prim) else "SLO FEIL"
    # sekundære liner, utan dom
    sek = {"S6_del_i_36_til_51_8": r(np.mean((h >= 36.0) & (h <= 51.8)), 3), "SD_over_snitt": r(np.std(h) / np.mean(h)),
           "per_periode": {}, "per_avdeling_alle": {}}
    for namn, lo, hi in (("foer_1700", -9999, 1700), ("1700_1899", 1700, 1900), ("fraa_1900", 1900, 9999)):
        x = np.array([hogd(k) for k in p if k["aar"] is not None and lo <= k["aar"] < hi], float)
        if len(x) >= 5:
            sek["per_periode"][namn] = {"n": len(x), "median": r(np.median(x), 1), "spreiing": r(rs(x))}
    for avd in sorted(set(k["avd"] for k in krakk)):
        x = np.array([hogd(k) for k in krakk if k["avd"] == avd and k["namnegruppe"] is None and hogd(k) is not None], float)
        if len(x) >= 5:
            sek["per_avdeling_alle"][avd] = {"n": len(x), "median": r(np.median(x), 1), "spreiing": r(rs(x)),
                                             "del_i_41_46": r(np.mean((x >= 41) & (x <= 46)), 3)}
    res["sekundaer"] = sek
    return res, p


def m2(arm):
    S = F["M2_armlene"]
    T = S["tersklar"]
    prim_avd = set(S["utval"]["avdelingar_primaer"])
    flyt = {"inn": len(arm)}
    a = [k for k in arm if k["avd"] in prim_avd]; flyt["andre_avdelingar"] = len(arm) - len(a)
    b = [k for k in a if k["H"] and k["sete"] and k["arm"]]; flyt["utan_alle_tre_maal"] = len(a) - len(b)
    c = [k for k in b if 30 <= k["sete"] <= 65 and k["sete"] < k["H"] and k["sete"] < k["arm"] <= k["H"]]
    flyt["urimelege_maal"] = len(b) - len(c)
    p = [k for k in c if T["A_vindauge"][0] <= k["arm"] - k["sete"] <= T["A_vindauge"][1]]
    flyt["A_utanfor_vindauget"] = len(c) - len(p)
    flyt["analysert"] = len(p)
    A = np.array([k["arm"] - k["sete"] for k in p], float)
    R = np.array([k["H"] - k["sete"] for k in p], float)
    kl = [k["klynge"] for k in p]
    iqr = float(np.subtract(*np.percentile(R, [75, 25]))) if len(R) else 0.0
    port = [{"namn": "n", "verdi": len(p), "terskel": T["n_min"], "ok": len(p) >= T["n_min"]},
            {"namn": "rygg_iqr_cm", "verdi": r(iqr, 2), "terskel": T["rygg_iqr_min"], "ok": iqr >= T["rygg_iqr_min"]}]
    res = {"flyt": flyt, "port": port}
    if not all(x["ok"] for x in port):
        res["dom"] = "UGYLDIG"
        return res, p
    bm = bootstrap(kl, lambda i: np.median(A[i]), F["n_boot"], F["froe"])
    bh = bootstrap(kl, lambda i: theil_sen(R[i], A[i]), F["n_boot"], F["froe"])
    med, hell = float(np.median(A)), theil_sen(R, A)
    ovre = float(np.nanpercentile(bh, 97.5))
    prim = [{"namn": "median_A", "verdi": r(med, 2), "ki95": [r(np.percentile(bm, 2.5), 2), r(np.percentile(bm, 97.5), 2)],
             "terskel": T["median_A"], "held": T["median_A"][0] <= med <= T["median_A"][1]},
            {"namn": "helling_A_paa_rygg", "verdi": r(hell), "ki95": [r(np.nanpercentile(bh, 2.5)), r(ovre)],
             "terskel": T["helling_ovre"], "held": ovre < T["helling_ovre"]}]
    res["primaer"] = prim
    res["dom"] = "HELDT" if all(x["held"] for x in prim) else "SLO FEIL"
    Hh = np.array([k["H"] for k in p], float); se = np.array([k["sete"] for k in p], float); ar = np.array([k["arm"] for k in p], float)
    K = S["treveg_koeffisientar"]
    mae = {"kropp": r(np.mean(np.abs(ar - (se + K["kropp"]))), 2), "bord": r(np.mean(np.abs(ar - K["bord"])), 2),
           "storleik": r(np.mean(np.abs(ar - K["storleik"] * Hh)), 2)}
    sek = {"treveg_mae": mae, "ols_helling": r(np.polyfit(R, A, 1)[0]) if len(R) > 2 else None,
           "del_i_band": r(np.mean((A >= T["median_A"][0]) & (A <= T["median_A"][1])), 3), "per_periode": {}}
    for namn, lo, hi in (("foer_1700", -9999, 1700), ("1700_1799", 1700, 1800), ("1800_1899", 1800, 1900), ("fraa_1900", 1900, 9999)):
        ix = [i for i, k in enumerate(p) if k["aar"] is not None and lo <= k["aar"] < hi]
        if len(ix) >= 5:
            sek["per_periode"][namn] = {"n": len(ix), "median_A": r(np.median(A[ix]), 1), "median_rygg": r(np.median(R[ix]), 1)}
    res["sekundaer"] = sek
    return res, p


def opne():
    if os.path.exists(P_RES):
        sys.exit("Stoppa: prøva er alt opna (RESULTAT.json finst).")
    c = sjekk_forsegla()
    haust_ = json.load(open(P_HAUST, encoding="utf-8"))
    h = hashlib.sha256(open(P_CSV, "rb").read()).hexdigest()
    if h != haust_["sha256"]:
        sys.exit("Stoppa: MetObjects.csv er ikkje den som vart henta.")
    krakk, arm = les()
    r1, p1 = m1(krakk)
    r2, p2 = m2(arm)
    res = {"opna": no(), "forsegla_commit": c, "kjelde_sha256": h, "avvik": F.get("kjende_avvik_foer_opning", []),
           "M1_krakk": r1, "M2_armlene": r2, "M3_kant_1712": {"dom": "UTSETT", "grunn": F["M3_kant_1712"]["status"]}}
    json.dump(res, open(P_RES, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    fig = {"krakk": [[k["aar"], (k["H"] if k["H"] is not None else k["sete"]), k["avd"]] for k in p1],
           "krakk_alle": [[k["aar"], (k["H"] if k["H"] is not None else k["sete"]), k["avd"], int(k["namnegruppe"] is None)]
                          for k in krakk if (k["H"] if k["H"] is not None else k["sete"]) is not None],
           "arm": [[k["aar"], k["H"], k["sete"], k["arm"]] for k in p2]}
    json.dump(fig, open(P_FIG, "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
    print("M1 krakk:", r1["dom"], "| M2 armlene:", r2["dom"])
    print(json.dumps(res, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--haust"]:
        haust()
    elif a == ["--opne"]:
        opne()
    elif a == ["--sjolvtest"]:
        sjolvtest()
    else:
        sys.exit(__doc__)
