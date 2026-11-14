"""Studie B: evolusjonsmodus per formakse (stase, tilfeldig vandring, retta vandring, Ornstein-Uhlenbeck) på katalogmål.

Katalogmåla (H, B, D, sete_kat) er direkte målingar, ikkje 3D. Kvar akse blir gjort om til ei tidsserie av middel i 50-årsbolkar
(minst 8 stolar per bolk, minst 6 bolkar), etter at typen (stol, armstol, anna) er trekt ut innan museum. Fire modellar blir tilpassa
med maksimal sannsyn på bolkmiddel med kjend utvalsvarians (paleoTS-logikk, Hunt 2006):
  stase   z_i ~ N(theta, omega + v_i)
  URW     z_i = z_1 + Brownsk rørsle med varians sigma2 per tidseining
  GRW     som URW med fast drift mu
  OU      stasjonær Ornstein-Uhlenbeck med middel theta, stasjonær varians omega og tilbakekopling alfa
Modellval med AICc (Akaike-vekter). Usikkerheit frå 150 repetisjonar der kvar stol får eit år trekt jamt frå [aar, aar_til] og suitane
blir trekte på nytt (suiteboot). Tidseininga er 50 år.

  python prove.py --kontroll   placebo (permuterte år) og planta trend. Skriv KONTROLL.json. Skriv ALDRI ut utfallet for dei verkelege seriane.
  python prove.py --opne       éin gong, etter forsegling. Skriv RESULTAT.json.
"""
import json, os, sys, time
import numpy as np
from scipy.optimize import minimize

MAPPE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(MAPPE, "..", "parallell"))
import felles_p as fp

sys.stdout.reconfigure(encoding="utf-8")
D = fp.last()
BIN, MIN_N, MIN_BOLK, FROE = 50, 8, 6, 20261113
MODELLAR = ("stase", "urw", "grw", "ou")
K = {"stase": 2, "urw": 2, "grw": 3, "ou": 3}
TYPEGR = np.array([t if t in ("Stol", "Armstol") else "anna" for t in D["type"]])
AKSAR = {"logH": np.log(D["H"].astype(float)), "logB": np.log(D["B"].astype(float)), "logD": np.log(D["D"].astype(float)),
         "logSH_kat": np.log(D["sete_kat"]), "logSH_3d": np.log(D["m"]["sete_h"])}
HOVUD = ("logH", "logB", "logD", "logSH_kat")


def juster_type(y, idx):
    """Trekk ut typen (stol, armstol, anna) innan museum; behald museumsmiddelet."""
    ut = y.copy()
    for mus in np.unique(D["museum"][idx]):
        for tg in np.unique(TYPEGR[idx]):
            k = idx[(D["museum"][idx] == mus) & (TYPEGR[idx] == tg)]
            ok = k[np.isfinite(y[k])]
            if len(ok) >= 5:
                ut[ok] = y[ok] - y[ok].mean()
        k = idx[D["museum"][idx] == mus]
        ok = k[np.isfinite(y[k])]
        if len(ok):
            ut[ok] += np.nanmean(y[k])
    return ut


def serie(y, aar, idx):
    """Bolkmiddel: t (50-årseiningar frå første bolk), m, v (varians til middelet), n."""
    ok = idx[np.isfinite(y[idx])]
    b = np.clip(aar[ok], 1550, 1999) // BIN
    T, M, V, N = [], [], [], []
    for k in np.unique(b):
        j = ok[b == k]
        if len(j) >= MIN_N:
            T.append(aar[j].mean())
            M.append(y[j].mean())
            V.append(y[j].var(ddof=1) / len(j))
            N.append(len(j))
    if len(T) < MIN_BOLK:
        return None
    T = (np.array(T) - T[0]) / BIN
    return T, np.array(M), np.array(V), np.array(N)


def nll(par, kind, t, m, v):
    n = len(m)
    if kind == "stase":
        S = np.exp(par[1]) * np.eye(n) + np.diag(v)
        mu = np.full(n, par[0])
    elif kind == "urw":
        S = np.exp(par[1]) * np.minimum.outer(t, t) + np.diag(v)
        mu = np.full(n, par[0])
    elif kind == "grw":
        S = np.exp(par[2]) * np.minimum.outer(t, t) + np.diag(v)
        mu = par[0] + par[1] * t
    else:
        a = np.exp(np.clip(par[2], -4, 3))
        S = np.exp(par[1]) * np.exp(-a * np.abs(np.subtract.outer(t, t))) + np.diag(v)
        mu = np.full(n, par[0])
    try:
        L = np.linalg.cholesky(S + 1e-12 * np.eye(n))
    except np.linalg.LinAlgError:
        return 1e9
    r = np.linalg.solve(L, m - mu)
    return float(0.5 * (n * np.log(2 * np.pi) + 2 * np.log(np.diag(L)).sum() + r @ r))


def tilpass(t, m, v):
    """-> {modell: (AICc, parametrar)}"""
    n = len(m)
    sm, s2 = m.mean(), max(m.var(), 1e-8)
    drift0 = np.polyfit(t, m, 1)[0] if n > 2 else 0.0
    starts = {"stase": [[sm, np.log(s2)], [sm, np.log(s2 / 10)]],
              "urw": [[m[0], np.log(s2 / max(t[-1], 1))], [m[0], np.log(s2 / 10 / max(t[-1], 1))]],
              "grw": [[m[0], drift0, np.log(s2 / 20 / max(t[-1], 1))], [m[0], drift0 / 2, np.log(s2 / 100 / max(t[-1], 1))]],
              "ou": [[sm, np.log(s2), np.log(a)] for a in (0.1, 1.0, 4.0)]}
    ut = {}
    for kind in MODELLAR:
        best = None
        for p0 in starts[kind]:
            r = minimize(nll, p0, args=(kind, t, m, v), method="Nelder-Mead", options={"maxiter": 500, "xatol": 1e-5, "fatol": 1e-8})
            if best is None or r.fun < best.fun:
                best = r
        k = K[kind]
        aicc = 2 * best.fun + 2 * k + (2 * k * (k + 1) / (n - k - 1) if n - k - 1 > 0 else np.inf)
        ut[kind] = (aicc, best.x)
    return ut


def vekter(fit):
    a = np.array([fit[k][0] for k in MODELLAR])
    if not np.all(np.isfinite(a)):
        a = np.where(np.isfinite(a), a, 1e9)
    w = np.exp(-0.5 * (a - a.min()))
    return dict(zip(MODELLAR, w / w.sum()))


def repetisjon(rng, y, idx, aar_trekk):
    """Éin repetisjon for éin serie: suitane trekte på nytt, år trekte jamt. -> dict eller None"""
    k = idx[fp.suiteboot(D["suite"][idx], rng)]
    aar = np.where(True, aar_trekk, 0.0)
    s = serie(y, aar, k)
    if s is None:
        return None
    t, m, v, n = s
    fit = tilpass(t, m, v)
    w = vekter(fit)
    ou = fit["ou"][1]
    sd_mellom = float(np.sqrt(np.exp(fit["stase"][1][1])))
    return {"w": w, "halveringstid_aar": float(np.log(2) / np.exp(np.clip(ou[2], -4, 3)) * BIN), "sd_mellom": sd_mellom,
            "ou_stasjonaer_sd": float(np.sqrt(np.exp(ou[1]))), "n_bolkar": int(len(m)), "sd_innan": float(np.sqrt(np.average(v * n)))}


def trekk_aar(rng):
    return rng.uniform(D["aar"].astype(float), D["aar_til"].astype(float) + 1.0)


def kjor_serie(y, idx, n_rep, rng, aar_fun=None):
    ut = []
    for _ in range(n_rep):
        a = trekk_aar(rng) if aar_fun is None else aar_fun(rng)
        r = repetisjon(rng, y, idx, a)
        if r is not None:
            ut.append(r)
    return ut


def samandrag(rep, n_rep):
    if not rep:
        return {"gyldig": 0.0}
    w = {k: float(np.median([r["w"][k] for r in rep])) for k in MODELLAR}
    return {"gyldig": len(rep) / n_rep, "median_vekt": w, "hoegste_modell": max(w, key=w.get),
            "del_stase_over_halv": float(np.mean([r["w"]["stase"] > 0.5 for r in rep])),
            "median_halveringstid_aar": float(np.median([r["halveringstid_aar"] for r in rep])),
            "ki95_halveringstid": fp.ki([r["halveringstid_aar"] for r in rep]),
            "median_sd_mellom": float(np.median([r["sd_mellom"] for r in rep])), "ki95_sd_mellom": fp.ki([r["sd_mellom"] for r in rep]),
            "median_sd_innan": float(np.median([r["sd_innan"] for r in rep])), "n_bolkar": int(np.median([r["n_bolkar"] for r in rep]))}


def alle_serier(n_rep, rng, aksar=HOVUD, modifiser=None, aar_fun=None):
    ut = {}
    for mus in ("VA", "NM"):
        idx = np.where(D["museum"] == mus)[0]
        for namn in aksar:
            y = juster_type(AKSAR[namn], idx)
            if modifiser:
                y = modifiser(namn, y, idx)
            ut["%s|%s" % (mus, namn)] = samandrag(kjor_serie(y, idx, n_rep, rng, aar_fun), n_rep)
    return ut


def kontroll():
    t0 = time.time()
    rng = np.random.default_rng(FROE)
    N = 60
    # teljingar (ikkje utfall): kor mange gyldige bolkar har kvar serie
    tel = {}
    for mus in ("VA", "NM"):
        idx = np.where(D["museum"] == mus)[0]
        for namn in HOVUD + ("logSH_3d",):
            s = serie(juster_type(AKSAR[namn], idx), D["aar"].astype(float), idx)
            tel["%s|%s" % (mus, namn)] = None if s is None else {"n_bolkar": int(len(s[1])), "n_per_bolk": [int(x) for x in s[3]]}
    # placebo: år permuterte innan museum og typegruppe. Då finst ingen tidsstruktur, og stase skal vinne
    def perm_aar(rng_):
        a = trekk_aar(rng_)
        return fp.perm_innan(a, np.array(["%s|%s" % (m, t) for m, t in zip(D["museum"], TYPEGR)]), rng_)
    placebo = alle_serier(N, rng, aar_fun=perm_aar)
    # planta trend: legg ein lineær trend på setehøgda (0,12 log-einingar per 400 år) på dei verkelege åra
    def plant(namn, y, idx):
        if namn != "logSH_kat":
            return y
        return y + 0.0003 * (D["aar"].astype(float) - 1800.0)
    planta = alle_serier(N, rng, aksar=("logSH_kat",), modifiser=plant)
    # planta stase: erstatt setehøgda med eit konstant middel pluss den verkelege støyen rundt trendlina
    def plant_stase(namn, y, idx):
        if namn != "logSH_kat":
            return y
        ok = idx[np.isfinite(y[idx])]
        b = np.polyfit(D["aar"][ok].astype(float), y[ok], 1)
        ut_ = y.copy()
        ut_[ok] = y[ok] - np.polyval(b, D["aar"][ok].astype(float)) + y[ok].mean()
        return ut_
    planta_stase = alle_serier(N, rng, aksar=("logSH_kat",), modifiser=plant_stase)
    ut = {"teljing": tel, "placebo_permuterte_aar": placebo, "planta_trend": planta, "planta_stase_trendfjerna": planta_stase,
          "n_repetisjonar": N, "sekund": round(time.time() - t0)}
    fp.lagre(MAPPE, "KONTROLL.json", ut)
    for k, v in placebo.items():
        print("placebo %-14s gyldig %.2f  stase-vekt %s  høgste %s" % (k, v["gyldig"], v.get("median_vekt", {}).get("stase"), v.get("hoegste_modell")))
    for k, v in planta.items():
        print("planta trend %-10s gyldig %.2f  vekter %s" % (k, v["gyldig"], {a: round(b, 2) for a, b in v.get("median_vekt", {}).items()}))
    for k, v in planta_stase.items():
        print("planta stase %-10s gyldig %.2f  vekter %s" % (k, v["gyldig"], {a: round(b, 2) for a, b in v.get("median_vekt", {}).items()}))
    print({k: (v and v["n_bolkar"]) for k, v in tel.items()}, ut["sekund"], "s")


def opne():
    seal = fp.sjekk_forsegla(MAPPE)
    F = json.load(open(os.path.join(MAPPE, "FORESEIINGAR.json"), encoding="utf-8"))
    rng = np.random.default_rng(FROE + 1)
    N = F["n_repetisjonar"]
    res = alle_serier(N, rng, aksar=HOVUD + ("logSH_3d",))
    T = F["tersklar"]
    dom = {}
    for mus in ("VA", "NM"):
        s = res["%s|logSH_kat" % mus]
        h = res["%s|logH" % mus]
        ok_s, ok_h = s["gyldig"] >= T["min_gyldig"], h["gyldig"] >= T["min_gyldig"]
        dom["H1_setet_i_stase_" + mus] = "UGYLDIG" if not ok_s else ("HELDT" if (s["hoegste_modell"] == "stase" and s["median_vekt"]["stase"] >= T["stase_vekt_setet"]) else "SLO FEIL")
        dom["H2_hoegda_ikkje_stase_" + mus] = "UGYLDIG" if not ok_h else ("HELDT" if h["median_vekt"]["stase"] <= T["stase_vekt_hoegda_maks"] else "SLO FEIL")
        if ok_s and ok_h:
            kvot = s["median_sd_mellom"] / h["median_sd_mellom"]
            dom["H3_mindre_mellombolkvarians_" + mus] = "HELDT" if kvot <= T["sd_kvot_maks"] else "SLO FEIL"
            res["%s|kvote_sd_mellom_setet_mot_hoegda" % mus] = kvot
        else:
            dom["H3_mindre_mellombolkvarians_" + mus] = "UGYLDIG"
    ut = {"forsegla_commit": seal, "n_repetisjonar": N, "serier": res, "dom": dom}
    fp.lagre(MAPPE, "RESULTAT.json", ut)
    print(json.dumps(dom, ensure_ascii=False, indent=1))
    for k, v in res.items():
        if isinstance(v, dict) and v.get("gyldig"):
            print("%-18s bolkar %s gyldig %.2f høgste %-5s vekter %s halveringstid %s" % (k, v["n_bolkar"], v["gyldig"], v["hoegste_modell"], {a: round(b, 2) for a, b in v["median_vekt"].items()}, round(v["median_halveringstid_aar"])))


if __name__ == "__main__":
    if "--kontroll" in sys.argv:
        kontroll()
    elif "--opne" in sys.argv:
        opne()
    else:
        print(__doc__)
