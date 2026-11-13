"""34_periode_stoff.py - den åttande forsegla prøva: føreseier perioden forma betre enn stoffet (føreseiing 11)?

Skriptet og forsegla8/FORESEIINGAR.json er pusha FØR nokon form er rekna.
Skriptet skal ikkje endrast etterpå; avvik blir førte i forsegla8/RESULTAT.json.

  python analyse/34_periode_stoff.py   Skriv forsegla8/RESULTAT.json og FIGURDATA.json.
"""
import csv, datetime, importlib.util, json, os, re, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
F8 = os.path.join(HER, "forsegla8")
P_FORE, P_RES, P_FIG = (os.path.join(F8, f) for f in ("FORESEIINGAR.json", "RESULTAT.json", "FIGURDATA.json"))
F = json.load(open(P_FORE, encoding="utf-8"))
_s = importlib.util.spec_from_file_location("to_alder", os.path.join(HER, "26_to_alder.py"))
TA = importlib.util.module_from_spec(_s)
_s.loader.exec_module(TA)
_f = importlib.util.spec_from_file_location("felles", os.path.join(HER, "forsegla2", "felles.py"))
felles = importlib.util.module_from_spec(_f)
sys.path.insert(0, os.path.join(HER, "forsegla2"))
_f.loader.exec_module(felles)
KLASSE = {"LINE": "LINE", "LINE+SHEET": "LINE", "SHEET": "SHEET", "WOOD": "WOOD"}
TYPAR = {"Stol", "Spisestol", "Armstol", "Klappstol"}
UTE_STRUKTUR = {"pidestall", "gyngande", "frittberande"}


def sjekk_forsegla():
    for rel in ("analyse/forsegla8/FORESEIINGAR.json", "analyse/34_periode_stoff.py"):
        c = TA.git("log", "-1", "--format=%H", "--", rel).stdout.strip()
        if not c:
            sys.exit("Stoppa: %s er ikkje committa." % rel)
        if TA.git("show", "%s:%s" % (c, rel)).stdout.replace("\r\n", "\n").encode("utf-8") != open(os.path.join(TA.ROT, rel), "rb").read().replace(b"\r\n", b"\n"):
            sys.exit("Stoppa: %s er endra etter siste commit." % rel)
        if not TA.git("branch", "-r", "--contains", c).stdout.strip():
            sys.exit("Stoppa: commiten %s med %s er ikkje pusha." % (c[:8], rel))
    return TA.git("log", "-1", "--format=%H", "--", "analyse/forsegla8/FORESEIINGAR.json").stdout.strip()


def loo(Z, grupper):
    """Middel av dei andre i same gruppe; None om gruppa har færre enn 5 andre."""
    ut = [None] * len(Z)
    for g in set(grupper):
        idx = [i for i, x in enumerate(grupper) if x == g]
        if len(idx) < 6:
            continue
        s = Z[idx].sum(0)
        for i in idx:
            ut[i] = (s - Z[i]) / (len(idx) - 1)
    return ut


def prov(Z, s_grupper, m_grupper, rng, nb):
    ps, pm = loo(Z, s_grupper), loo(Z, m_grupper)
    ok = [i for i in range(len(Z)) if ps[i] is not None and pm[i] is not None]
    es = np.array([((Z[i] - ps[i]) ** 2).sum() for i in ok])
    em = np.array([((Z[i] - pm[i]) ** 2).sum() for i in ok])
    d = em - es
    b = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(nb)])
    return {"n": len(ok), "Q": float(es.mean() / em.mean()), "skilnad": float(d.mean()),
            "ki95": [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))]}


if __name__ == "__main__":
    seal = sjekk_forsegla()
    if os.path.exists(P_RES):
        sys.exit("Stoppa: RESULTAT.json finst alt. Prøva er køyrd.")
    ST = {r["Objekt-ID"]: r for r in csv.DictReader(open(os.path.join(TA.ROT, "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline=""))}
    S, X = TA.last()
    PER = {st: p for p, l in F["maal"]["periodar"].items() for st in l}
    rader, sett = [], set()
    for i in sorted(range(len(S)), key=lambda i: S[i]["id"]):
        s, r = S[i], ST.get(S[i]["id"], {})
        if not (1915 <= s["aar"] <= 2020) or s["type"] not in TYPAR or r.get("struktur_type") in UTE_STRUKTUR:
            continue
        mat = KLASSE.get(felles.materialklasse(r.get("Materialar", ""), r.get("Teknikk", "")))
        if not mat:
            continue
        k1, k2 = ("m", s["museum"], s["H"], s["B"]), ("s", re.sub(r"[A-Za-z]$|-\d+$", "", s["id"]))
        if k1 in sett or k2 in sett:
            continue
        sett |= {k1, k2}
        bolk = next(b for b, (a0, a1) in F["maal"]["aarsbolkar"].items() if a0 <= s["aar"] <= a1)
        rader.append({"i": i, "id": s["id"], "aar": s["aar"], "museum": s["museum"], "mat": mat, "per": PER.get(s["stil"]), "bolk": bolk})
    M = np.array([np.concatenate([X[r["i"], 1, 2:125], X[r["i"], 3, 2:125]]) for r in rader])
    sd = M.std(0)
    Z = (M[:, sd > 1e-6] - M[:, sd > 1e-6].mean(0)) / sd[sd > 1e-6]
    rng = np.random.default_rng(F["froe"])
    # P1: perioden etter stil (berre stolar med stilmerke i ei gruppe)
    med = [k for k, r in enumerate(rader) if r["per"]]
    p1 = prov(Z[med], [(rader[k]["per"], rader[k]["museum"]) for k in med], [(rader[k]["mat"], rader[k]["museum"]) for k in med], rng, F["n_boot"])
    # P2: årsbolkar (alle stolane)
    p2 = prov(Z, [(r["bolk"], r["museum"]) for r in rader], [(r["mat"], r["museum"]) for r in rader], rng, F["n_boot"])
    # P3: rutenettet
    celle = {}
    for k in med:
        celle.setdefault((rader[k]["per"], rader[k]["mat"]), []).append(k)
    mid = {c: Z[v].mean(0) for c, v in celle.items() if len(v) >= 8}
    dist = lambda a, b: float(np.sqrt(((mid[a] - mid[b]) ** 2).sum()))
    sp = [dist(a, b) for a in mid for b in mid if a < b and a[0] == b[0] and a[1] != b[1]]
    ss = [dist(a, b) for a in mid for b in mid if a < b and a[1] == b[1] and a[0] != b[0]]
    p3 = {"same_periode_ulikt_stoff": float(np.mean(sp)) if sp else None, "same_stoff_ulik_periode": float(np.mean(ss)) if ss else None,
          "celler": {"%s_%s" % c: len(v) for c, v in celle.items()}}
    dom = lambda g, okk: "UGYLDIG" if not g else "HELDT" if okk else "SLO FEIL"
    R = {"P1_stilmerka": {**p1, "dom": dom(p1["n"] >= 150, p1["Q"] <= 0.95 and p1["ki95"][0] > 0)},
         "P2_aarsbolkane": {**p2, "dom": dom(p2["n"] >= 150, p2["Q"] <= 0.95 and p2["ki95"][0] > 0)},
         "P3_rutenettet": {**p3, "dom": dom(bool(sp and ss), bool(sp and ss) and np.mean(sp) < np.mean(ss))}}
    ut = {"tid": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "forsegla_commit": seal,
          "n_utval": len(rader), "resultat": R, "avvik": []}
    json.dump(ut, open(P_RES, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    json.dump({"stolar": [{k: r[k] for k in ("id", "aar", "museum", "mat", "per", "bolk")} for r in rader]},
              open(P_FIG, "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
    print(json.dumps(ut, ensure_ascii=False, indent=1))
