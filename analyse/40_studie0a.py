"""40_studie0a.py - Studie 0a: kor mykje dreg 3D-modellane måla mot gjennomsnittsstolen? Kalibrering mot katalogen.

For måla der katalogen gjev ein uavhengig verdi (breidd B, djupn D, setehøgd) blir stigninga til 3D-målet på katalogmålet
rekna, per museum, tidsrom og materiale. Katalogmålet har sjølv målefeil, så ei enkel stigning undervurderer krympinga.
Frisch-grensene gjev eit intervall utan å kjenne feilen: nedre grense er stigninga til 3D-målet på katalogen, øvre grense er
variansen til 3D-målet delt på kovariansen (stigninga til katalogen på 3D-målet snudd). Den sanne krympefaktoren ligg
mellom dei når feilane i dei to målingane er uavhengige. Intervall frå bootstrap over suitar.

  python analyse/40_studie0a.py   -> analyse/data/studie0a.json
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "parallell"))
import felles_p as fp

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
D = fp.last()
m = D["m"]
PAR = {"breidd (B)": (m["breidd3d"], D["B"].astype(float)), "djupn (D)": (m["djupn3d"], D["D"].astype(float)),
       "setehøgd": (m["sete_h"], D["sete_kat"])}
UTVAL = {"alle": np.ones(D["n"], bool), "V&A": D["museum"] == "VA", "Nasjonalmuseet": D["museum"] == "NM",
         "før 1800": D["aar"] < 1800, "1800 til 1899": (D["aar"] >= 1800) & (D["aar"] < 1900), "frå 1900": D["aar"] >= 1900,
         "tre": D["mat"] == "WOOD", "metall og plast": D["mat"] != "WOOD"}
rng = np.random.default_rng(20261113)


def grenser(x, y):
    """x = katalog, y = 3D. -> (nedre, øvre) for krympefaktoren."""
    c = np.cov(x, y)
    return float(c[0, 1] / c[0, 0]), float(c[1, 1] / c[0, 1])


def boot(idx, x, y, n=500):
    lo, hi = [], []
    for _ in range(n):
        k = idx[fp.suiteboot(D["suite"][idx], rng)]
        ok = np.isfinite(x[k]) & np.isfinite(y[k])
        a, b = grenser(x[k][ok], y[k][ok])
        lo.append(a)
        hi.append(b)
    return fp.ki(lo), fp.ki(hi)


ut = {"n_ramme": D["n"], "forklaring": __doc__.strip().split("\n")[0], "resultat": {}}
for namn, (y, x) in PAR.items():
    ut["resultat"][namn] = {}
    for u, ik in UTVAL.items():
        ok = ik & np.isfinite(x) & np.isfinite(y)
        if ok.sum() < 40:
            continue
        idx = np.where(ok)[0]
        a, b = grenser(x[idx], y[idx])
        kl, kh = boot(idx, x, y)
        ut["resultat"][namn][u] = {"n": int(ok.sum()), "nedre": a, "ovre": b, "ki_nedre": kl, "ki_ovre": kh,
                                   "r": float(np.corrcoef(x[idx], y[idx])[0, 1])}
# katalogsetet åleine mot totalhøgda (ingen 3D): held påstanden om at setet står fastare enn høgda utan modellane?
kat = {}
for u in ("alle", "V&A", "Nasjonalmuseet"):
    ok = UTVAL[u] & np.isfinite(D["sete_kat"])
    idx = np.where(ok)[0]
    cv = lambda v: np.std(v, ddof=1) / np.median(v)
    f = lambda k: cv(D["sete_kat"][k]) / cv(D["H"][k].astype(float))
    kat[u] = {"n": int(ok.sum()), "cv_sete": float(cv(D["sete_kat"][idx])), "cv_H": float(cv(D["H"][idx].astype(float))),
              "forhold": float(f(idx)), "ki95": fp.ki([f(idx[fp.suiteboot(D["suite"][idx], rng)]) for _ in range(1000)])}
ut["katalogsete_mot_hoegd"] = kat
json.dump(ut, open(os.path.join(HER, "data", "studie0a.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("%-12s %-16s %5s %7s %7s  %-18s %-18s" % ("mål", "utval", "n", "nedre", "øvre", "KI nedre", "KI øvre"))
for namn, v in ut["resultat"].items():
    for u, r in v.items():
        print("%-12s %-16s %5d %7.2f %7.2f  [%.2f, %.2f]       [%.2f, %.2f]" % (namn, u, r["n"], r["nedre"], r["ovre"], r["ki_nedre"][0], r["ki_nedre"][1], r["ki_ovre"][0], r["ki_ovre"][1]))
print(json.dumps(kat, ensure_ascii=False))
