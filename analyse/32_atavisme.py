"""32_atavisme.py - den sjuande forsegla prøva: fell dei mest nyskapande stolane i ein gammal dal?

Skriptet og forsegla7/FORESEIINGAR.json er pusha FØR avstanden til stolar frå før 1840 er rekna for nokon stol.
Skriptet skal ikkje endrast etterpå; avvik blir førte i forsegla7/RESULTAT.json.

  python analyse/32_atavisme.py   Nektar om fila eller skriptet ikkje ligg uendra i ein pusha commit,
                                  eller om RESULTAT.json alt finst. Skriv RESULTAT.json og FIGURDATA.json.
"""
import csv, datetime, importlib.util, json, os, re, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
F7 = os.path.join(HER, "forsegla7")
P_FORE, P_RES, P_FIG = (os.path.join(F7, f) for f in ("FORESEIINGAR.json", "RESULTAT.json", "FIGURDATA.json"))
F = json.load(open(P_FORE, encoding="utf-8"))
_s = importlib.util.spec_from_file_location("to_alder", os.path.join(HER, "26_to_alder.py"))
TA = importlib.util.module_from_spec(_s)
_s.loader.exec_module(TA)
_f = importlib.util.spec_from_file_location("felles", os.path.join(HER, "forsegla2", "felles.py"))
felles = importlib.util.module_from_spec(_f)
sys.path.insert(0, os.path.join(HER, "forsegla2"))
_f.loader.exec_module(felles)
UTE_STIL = {"Historisme", "Nyrokokko", "Nybarokk", "Dragestil", "Postmodernisme", "Memphis / Postmodernisme"}
KOPI = re.compile(r"kopi|reproduksjon|replica|copy of|rekonstruksjon", re.I)
KLASSE = {"LINE": "LINE", "LINE+SHEET": "LINE", "SHEET": "SHEET", "WOOD": "WOOD"}
K_NULL = 200


def sjekk_forsegla():
    for rel in ("analyse/forsegla7/FORESEIINGAR.json", "analyse/32_atavisme.py"):
        c = TA.git("log", "-1", "--format=%H", "--", rel).stdout.strip()
        if not c:
            sys.exit("Stoppa: %s er ikkje committa." % rel)
        if TA.git("show", "%s:%s" % (c, rel)).stdout.replace("\r\n", "\n").encode("utf-8") != open(os.path.join(TA.ROT, rel), "rb").read().replace(b"\r\n", b"\n"):
            sys.exit("Stoppa: %s er endra etter siste commit." % rel)
        if not TA.git("branch", "-r", "--contains", c).stdout.strip():
            sys.exit("Stoppa: commiten %s med %s er ikkje pusha." % (c[:8], rel))
    return TA.git("log", "-1", "--format=%H", "--", "analyse/forsegla7/FORESEIINGAR.json").stdout.strip()


def bootstrap(x, f, rng, n):
    b = np.array([f(x[rng.integers(0, len(x), len(x))]) for _ in range(n)])
    return [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))]


if __name__ == "__main__":
    seal = sjekk_forsegla()
    if os.path.exists(P_RES):
        sys.exit("Stoppa: RESULTAT.json finst alt. Prøva er køyrd.")
    ST = {r["Objekt-ID"]: r for r in csv.DictReader(open(os.path.join(TA.ROT, "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline=""))}
    S, X = TA.last()
    n = len(S)
    M = X[:, :, 2:125].reshape(n, -1)
    mu, sd = M.mean(0), M.std(0)
    ok = sd > 1e-6
    Z = (M[:, ok] - mu[ok]) / sd[ok]
    _, sv, Vt = np.linalg.svd(Z, full_matrices=False)
    P = Z @ Vt[:15].T
    var15 = P.var(0)
    aar = np.array([s["aar"] for s in S])
    mat = [KLASSE.get(felles.materialklasse(ST.get(s["id"], {}).get("Materialar", ""), ST.get(s["id"], {}).get("Teknikk", ""))) for s in S]
    namn = [(ST.get(s["id"], {}).get("Namn") or "") for s in S]
    stamme = [re.sub(r"[A-Za-z]$|-\d+$", "", s["id"]) for s in S]
    nokkel = [(s["museum"], s["H"], s["B"]) for s in S]
    djup = np.where(aar <= 1840)[0]
    maal = [i for i, s in enumerate(S) if 1900 <= s["aar"] <= 2020 and mat[i] and s["stil"] not in UTE_STIL and not KOPI.search(namn[i])]
    rad = []
    for i in maal:
        kand = [j for j in range(n) if mat[j] == mat[i] and 5 <= aar[i] - aar[j] <= 80 and stamme[j] != stamme[i] and nokkel[j] != nokkel[i]]
        if len(kand) < 30:
            continue
        kand = sorted(kand, key=lambda j: -aar[j])[:60]
        d = np.sqrt(((P[kand] - P[i]) ** 2).sum(1))
        q = kand[int(np.argmin(d))]
        do = np.sqrt(((P[djup] - P[i]) ** 2).sum(1))
        rad.append({"i": i, "n": float(d.min()), "q": q, "o": float(do.min()), "tvilling": int(djup[int(np.argmin(do))])})
    nv = np.array([r["n"] for r in rad])
    grense = float(np.quantile(nv, 0.80))
    nye = [r for r in rad if r["n"] > grense]
    vanlege = [r for r in rad if r["n"] <= grense]
    gyldig = len(nye) >= 50 and len(vanlege) >= 200
    rng = np.random.default_rng(F["froe"])
    for r in nye:                                     # nullmodell: like langt steg frå q_i i tilfeldig retning
        u = rng.normal(0, np.sqrt(var15), (K_NULL, 15))
        u /= np.linalg.norm(u, axis=1, keepdims=True)
        pts = P[r["q"]] + r["n"] * u
        dn = np.sqrt(((pts[:, None, :] - P[djup][None, :, :]) ** 2).sum(2)).min(1)
        r["null_median"] = float(np.median(dn))
        r["under"] = bool(r["o"] < r["null_median"])
    o = np.array([r["o"] for r in nye])
    nm = np.array([r["null_median"] for r in nye])
    und = np.array([r["under"] for r in nye], float)
    a1 = float(und.mean())
    a1_ki = bootstrap(und, np.mean, rng, F["n_boot"])
    a2 = float(np.median(o) / np.median(nm))
    b = []
    for _ in range(F["n_boot"]):
        k = rng.integers(0, len(nye), len(nye))
        b.append(np.median(o[k]) / np.median(nm[k]))
    a2_ki = [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))]
    dom = lambda okk: "UGYLDIG" if not gyldig else "HELDT" if okk else "SLO FEIL"
    R = {"A1_under_nullmedianen": {"del": a1, "ki95": a1_ki, "dom": dom(a1 >= 0.60 and a1_ki[0] > 0.50)},
         "A2_naerare_enn_tilfeldig": {"R": a2, "ki95": a2_ki, "dom": dom(a2 <= 0.95 and a2_ki[1] < 1.00)}}
    sek = {}
    for namn_m, kl in (("tre", {"WOOD"}), ("metall_og_plast", {"LINE", "SHEET"})):
        g = [r for r in nye if mat[r["i"]] in kl]
        if g:
            sek[namn_m] = {"n": len(g), "del_under": float(np.mean([r["under"] for r in g])),
                           "R": float(np.median([r["o"] for r in g]) / np.median([r["null_median"] for r in g]))}
    tiaar = lambda r: aar[r["i"]] // 10
    van_o = {}
    for r in vanlege:
        van_o.setdefault(tiaar(r), []).append(r["o"])
    sek["R_mot_vanlege_same_tiaar"] = float(np.median([r["o"] / np.median(van_o[tiaar(r)]) for r in nye if tiaar(r) in van_o]))
    sek["tvillingaar"] = {"median": float(np.median([aar[r["tvilling"]] for r in nye])),
                          "kvartilar": [float(np.quantile([aar[r["tvilling"]] for r in nye], q)) for q in (0.25, 0.75)]}
    ut = {"tid": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "forsegla_commit": seal,
          "n": {"maal": len(rad), "nye": len(nye), "vanlege": len(vanlege), "djup_fortid": int(len(djup))}, "gyldig": gyldig,
          "grense": grense, "resultat": R, "sekundaert": sek, "avvik": []}
    json.dump(ut, open(P_RES, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    json.dump({"stolar": [{"id": S[r["i"]]["id"], "aar": int(aar[r["i"]]), "mat": mat[r["i"]], "n": r["n"], "o": r["o"], "ny": r["n"] > grense,
                           "null_median": r.get("null_median"), "tvilling": S[r["tvilling"]]["id"], "tvilling_aar": int(aar[r["tvilling"]]),
                           "naer": S[r["q"]]["id"], "naer_aar": int(aar[r["q"]])} for r in rad]},
              open(P_FIG, "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
    print(json.dumps(ut, ensure_ascii=False, indent=1))
