"""Studie B2: kor mykje flyttar nivået til kvar formakse seg mellom 50-årsbolkar? Variansdel mellom bolkar på stolnivå, katalogmål.

Erstatning for Studie B (AICc-val mellom stase og vandring), som ikkje kunne opnast: kontrollane viste at 8 til 9 bolkmiddel ikkje let
stase skilje seg frå tilfeldig vandring (placebo gav stasevekt 0,46 til 0,59, og ein planta trend på 12 % vart ikkje funnen).

Kvar akse (log H, log B, log D, log sete_kat) blir først justert for typen (stol, armstol, anna) innan museum. Variansen mellom 50-årsbolkar blir
rekna som ein varianskomponent (ANOVA-estimat, minst 8 stolar per bolk, minst 6 bolkar): omega = (MSB minus MSW) delt på n0, avkorta ved 0, og
SD mellom = rota av omega, i log-einingar. Målestøy i eit katalogmål aukar berre variansen innan bolkar (MSW), ikkje omega, så denne storleiken
er ikkje blåst opp eller trekt ned av at katalogsetet er mindre presist enn H. Intervall: 1 000 repetisjonar der kvar stol får eit år
trekt jamt frå [aar, aar_til] og suitane blir trekte på nytt.

  python prove.py --kontroll   placebo (permuterte år) og planta trendar. Skriv KONTROLL.json.
  python prove.py --opne       éin gong, etter forsegling. Skriv RESULTAT.json.
"""
import json, os, sys
import numpy as np

MAPPE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(MAPPE, "..", "parallell"))
import felles_p as fp

sys.stdout.reconfigure(encoding="utf-8")
D = fp.last()
BIN, MIN_N, MIN_BOLK, FROE, NREP = 50, 8, 6, 20261113, 1000
TYPEGR = np.array([t if t in ("Stol", "Armstol") else "anna" for t in D["type"]])
AKSAR = {"logH": np.log(D["H"].astype(float)), "logB": np.log(D["B"].astype(float)), "logD": np.log(D["D"].astype(float)),
         "logSH_kat": np.log(D["sete_kat"])}
AAR0, AAR1 = D["aar"].astype(float), D["aar_til"].astype(float) + 1.0


def juster_type(y, idx):
    ut = y.copy()
    for mus in np.unique(D["museum"][idx]):
        for tg in np.unique(TYPEGR[idx]):
            k = idx[(D["museum"][idx] == mus) & (TYPEGR[idx] == tg)]
            ok = k[np.isfinite(y[k])]
            if len(ok) >= 5:
                ut[ok] = y[ok] - y[ok].mean()
    return ut


def omega(y, aar, idx):
    ok = idx[np.isfinite(y[idx])]
    b = np.clip(aar[ok], 1550, 1999) // BIN
    gr = [y[ok][b == k] for k in np.unique(b) if (b == k).sum() >= MIN_N]
    if len(gr) < MIN_BOLK:
        return None
    n_i = np.array([len(g) for g in gr], float)
    N = n_i.sum()
    k = len(gr)
    mid = np.array([g.mean() for g in gr])
    gm = np.concatenate(gr).mean()
    msb = (n_i * (mid - gm) ** 2).sum() / (k - 1)
    msw = sum(((g - g.mean()) ** 2).sum() for g in gr) / (N - k)
    n0 = (N - (n_i ** 2).sum() / N) / (k - 1)
    return max((msb - msw) / n0, 0.0), float(np.sqrt(msw)), k


def repeter(y, idx, rng, aar_fun, n=NREP):
    ut = []
    for _ in range(n):
        a = aar_fun(rng)
        k = idx[fp.suiteboot(D["suite"][idx], rng)]
        r = omega(y, a, k)
        if r is not None:
            ut.append(r)
    return ut


def trekk(rng):
    return rng.uniform(AAR0, AAR1)


def serier(rng, y_av, aar_fun=trekk, n=NREP):
    """-> {museum: {akse: [(omega, sd_innan, k), ...]}} med same trekk av år og suitar for alle aksane (parvis samanlikning)."""
    ut = {}
    for mus in ("VA", "NM"):
        idx = np.where(D["museum"] == mus)[0]
        Y = {a: y_av(a, juster_type(AKSAR[a], idx), idx) for a in AKSAR}
        rep = {a: [] for a in AKSAR}
        for _ in range(n):
            ar = aar_fun(rng)
            k = idx[fp.suiteboot(D["suite"][idx], rng)]
            r = {a: omega(Y[a], ar, k) for a in AKSAR}
            if all(v is not None for v in r.values()):
                for a in AKSAR:
                    rep[a].append(r[a])
        ut[mus] = rep
    return ut


def samandrag(rep):
    ut = {}
    for mus, v in rep.items():
        s = {"n_rep": len(v["logH"])}
        for a, lst in v.items():
            if lst:
                s[a] = {"sd_mellom": float(np.sqrt(np.median([x[0] for x in lst]))), "sd_mellom_ki95": [float(np.sqrt(q)) for q in fp.ki([x[0] for x in lst])],
                        "sd_innan": float(np.median([x[1] for x in lst])), "n_bolkar": int(np.median([x[2] for x in lst]))}
        if len(v["logH"]):
            d = np.array([h[0] - sh[0] for h, sh in zip(v["logH"], v["logSH_kat"])])
            s["diff_omega_H_minus_sete"] = float(np.median(d))
            s["diff_omega_H_minus_sete_ki95"] = fp.ki(d)
            for a in ("logB", "logD"):
                dd = np.array([h[0] - x[0] for h, x in zip(v["logH"], v[a])])
                s["diff_omega_H_minus_" + a] = [float(np.median(dd))] + fp.ki(dd)
        ut[mus] = s
    return ut


def kontroll():
    rng = np.random.default_rng(FROE)
    strata = np.array(["%s|%s" % (m, t) for m, t in zip(D["museum"], TYPEGR)])
    perm = lambda r: fp.perm_innan(trekk(r), strata, r)
    ingen = lambda a, y, idx: y
    N = 200
    pl = samandrag(serier(rng, ingen, aar_fun=perm, n=N))
    # planta: på permuterte år, legg ein trend på H (0,0005 per år, om lag 0,2 per 400 år) og ein mindre på setet (0,0001 per år)
    def plant(a, y, idx):
        if a == "logH":
            return y + 0.0005 * (AAR0 - 1800.0)
        if a == "logSH_kat":
            return y + 0.0001 * (AAR0 - 1800.0)
        return y
    # trendane skal ligge i dei verkelege åra, så bruk dei verkelege åra til å lage dei og permuter ikkje
    pt = samandrag(serier(rng, plant, aar_fun=trekk, n=N))
    # lik trend på begge: skilnaden skal vere nær null
    def plant_lik(a, y, idx):
        return y + 0.0003 * (AAR0 - 1800.0) if a in ("logH", "logSH_kat") else y
    pl_lik = samandrag(serier(rng, plant_lik, aar_fun=perm, n=N))
    ut = {"n_rep": N, "placebo_permuterte_aar": pl, "planta_H_sterk_sete_svak": pt, "planta_lik_trend_paa_begge_permuterte_aar": pl_lik}
    fp.lagre(MAPPE, "KONTROLL.json", ut)
    for namn, s in (("placebo", pl), ("planta H sterk, sete svak (verkelege år)", pt), ("lik trend, permuterte år", pl_lik)):
        for mus, v in s.items():
            print(namn, mus, "n_rep", v["n_rep"], "diff omega H minus sete: %.5f [%.5f, %.5f]" % (v["diff_omega_H_minus_sete"], *v["diff_omega_H_minus_sete_ki95"]))


def opne():
    seal = fp.sjekk_forsegla(MAPPE)
    F = json.load(open(os.path.join(MAPPE, "FORESEIINGAR.json"), encoding="utf-8"))
    rng = np.random.default_rng(FROE + 1)
    rep = serier(rng, lambda a, y, idx: y)
    s = samandrag(rep)
    dom = {}
    for mus in ("VA", "NM"):
        v = s[mus]
        dom["B1_setet_flyttar_seg_mindre_enn_hoegda_" + mus] = "UGYLDIG" if (v["n_rep"] < F["tersklar"]["min_rep"] or mus not in F["tersklar"]["gyldige_museum"]) else ("HELDT" if v["diff_omega_H_minus_sete_ki95"][0] > 0 else "SLO FEIL")
    ut = {"forsegla_commit": seal, "n_repetisjonar": NREP, "per_museum": s, "dom": dom}
    fp.lagre(MAPPE, "RESULTAT.json", ut)
    print(json.dumps(dom, ensure_ascii=False, indent=1))
    for mus, v in s.items():
        print(mus, "n_rep", v["n_rep"], {a: (round(v[a]["sd_mellom"], 3), v[a]["n_bolkar"]) for a in AKSAR if a in v}, "diff H minus sete", round(v["diff_omega_H_minus_sete"], 5), [round(x, 5) for x in v["diff_omega_H_minus_sete_ki95"]])


if __name__ == "__main__":
    if "--kontroll" in sys.argv:
        kontroll()
    elif "--opne" in sys.argv:
        opne()
    else:
        print(__doc__)
