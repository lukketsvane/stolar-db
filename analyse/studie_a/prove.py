"""Studie A: kva forklarer forma på katalogmåla (H, B, D): tid, materiale, stil, region, teknikk? Med lekkasjekontroll og revival.

Form = log H, log B, log D (standardisert). Dette er direkte katalogmål, ikkje 3D. Kvar faktorgruppe sitt unike bidrag er auken i
justert R2 (Peres-Neto) når gruppa kjem med i modellen sist, med alle andre grupper inne (tid som kubisk spline, materiale, museum,
type, region, teknikk, og stil eller pseudostil). Pseudostilen er stilen som året åleine gjev (modus blant dei fem næraste i år, same
suite ute): han måler kva ein stilmerkelapp kan ha fått frå dateringa. Intervall: bootstrap over suitar (300 trekk).

  python prove.py --kontroll   placebo (permuterte stilmerke innan stratum) og planta stileffekt og planta revivaleffekt. Skriv KONTROLL.json.
  python prove.py --opne       éin gong, etter forsegling. Skriv RESULTAT.json.
"""
import collections, csv, json, os, sys, time
import numpy as np

MAPPE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(MAPPE, "..", "parallell"))
import felles_p as fp

sys.stdout.reconfigure(encoding="utf-8")
D = fp.last()
N = D["n"]
FROE, NB = 20261113, 300
ST = {r["Objekt-ID"]: r for r in csv.DictReader(open(os.path.join(fp.ROT, "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline=""))}
MID = (D["aar"].astype(float) + D["aar_til"].astype(float)) / 2.0
TYPEGR = np.array([t if t in ("Stol", "Armstol") else "anna" for t in D["type"]])


def z(x):
    return (x - x.mean()) / x.std(ddof=1)


Y3 = np.column_stack([z(np.log(D["H"].astype(float))), z(np.log(D["B"].astype(float))), z(np.log(D["D"].astype(float)))])


def dummies(kat, min_n=10, ref=None):
    """Faktor -> dummykolonnar; sjeldne nivå blir «anna». Første (mest vanlege eller ref) er referanse."""
    kat = np.array(kat, dtype=object)
    c = collections.Counter(kat)
    kat = np.array([k if c[k] >= min_n else "anna" for k in kat], dtype=object)
    nivaa = [k for k, _ in collections.Counter(kat).most_common()]
    if ref in nivaa:
        nivaa.remove(ref)
        nivaa.insert(0, ref)
    return np.column_stack([(kat == k).astype(float) for k in nivaa[1:]]) if len(nivaa) > 1 else np.zeros((len(kat), 0))


def spline(t):
    t = (t - 1800.0) / 100.0
    kol = [t, t ** 2, t ** 3] + [np.clip(t - k, 0, None) ** 3 for k in (-1.5, -0.5, 0.5, 1.25)]
    return np.column_stack([(k - k.mean()) / k.std() for k in kol])


def teknikk():
    ord_ = collections.Counter()
    rad = []
    for i in D["id"]:
        v = [w.strip().lower() for w in (ST.get(i, {}).get("Teknikk") or "").split(",") if w.strip() and w.strip() != "-"]
        rad.append(v)
        ord_.update(set(v))
    topp = [w for w, _ in ord_.most_common(8)]
    M = np.array([[float(w in v) for w in topp] + [float(len(v) == 0)] for v in rad])
    return M[:, M.std(0) > 0]


def pseudostil():
    """Stilen året åleine gjev: modus blant dei fem næraste i midtår (same suite ute)."""
    ut = np.empty(N, dtype=object)
    for i in range(N):
        k = np.where(D["suite"] != D["suite"][i])[0]
        j = k[np.argsort(np.abs(MID[k] - MID[i]), kind="stable")[:5]]
        ut[i] = collections.Counter(D["stil"][j]).most_common(1)[0][0]
    return ut


NASJ = np.array([(ST.get(i, {}).get("Nasjonalitet") or "ukjend").strip() or "ukjend" for i in D["id"]], dtype=object)
BLOKKER = {"tid": spline(MID), "materiale": dummies(D["mat"], 10, "WOOD"), "museum": dummies(D["museum"], 1, "VA"),
           "type": dummies(TYPEGR, 5, "Stol"), "region": dummies(NASJ, 15, "Storbritannia"), "teknikk": teknikk(),
           "stil": dummies(D["stil"], 10), "pseudostil": dummies(pseudostil(), 10)}


def r2adj(X, Y):
    n = len(Y)
    X1 = np.column_stack([np.ones(n), X]) if X.shape[1] else np.ones((n, 1))
    coef, _, rank, _ = np.linalg.lstsq(X1, Y, rcond=None)
    rss = ((Y - X1 @ coef) ** 2).sum()
    tss = ((Y - Y.mean(0)) ** 2).sum()
    r2 = 1 - rss / tss
    m = rank - 1
    return float(1 - (1 - r2) * (n - 1) / (n - m - 1))


def unik(idx, Y, blokkar, namn, med=("tid", "materiale", "museum", "type", "region", "teknikk"), stilblokk="stil"):
    """Unikt bidrag (auke i justert R2) frå blokk `namn` til modellen med alle blokkene i `med` pluss stilblokken."""
    liste = list(med) + [stilblokk]
    if namn not in liste:
        liste = liste + [namn]
    full = np.column_stack([blokkar[b][idx] for b in liste if blokkar[b].shape[1]])
    utan = np.column_stack([blokkar[b][idx] for b in liste if b != namn and blokkar[b].shape[1]])
    return r2adj(full, Y[idx]) - r2adj(utan, Y[idx])


def med_utval(utval):
    return tuple(b for b in ("tid", "materiale", "museum", "type", "region", "teknikk") if not (utval != "samla" and b == "museum"))


def dekomponer(idx, Y, blokkar, rng, n_boot=NB, utval="samla"):
    med = med_utval(utval)
    namn = list(med) + ["stil", "pseudostil"]
    def alle(ii):
        ut = {}
        for b in med:
            ut[b] = unik(ii, Y, blokkar, b, med, "stil")
        ut["stil"] = unik(ii, Y, blokkar, "stil", med, "stil")
        ut["pseudostil"] = unik(ii, Y, blokkar, "pseudostil", med, "pseudostil")
        ut["stil_minus_pseudostil"] = ut["stil"] - ut["pseudostil"]
        ut["stil_minus_materiale"] = ut["stil"] - ut["materiale"]
        return ut
    obs = alle(idx)
    rep = [alle(idx[fp.suiteboot(D["suite"][idx], rng)]) for _ in range(n_boot)]
    return {"n": int(len(idx)), "unik": obs, "ki95": {k: fp.ki([r[k] for r in rep]) for k in obs}}


def revival(Y, rng, n_perm=4999, plant=0.0):
    """Nyrokokko (revival) mot Rokokko (forbilde) og dei samtidige (1830 til 1900, ikkje nyrokokko): ligg revivalstolane nærare forbildet enn dei samtidige gjer?"""
    rev = np.array([s == "Nyrokokko" for s in D["stil"]])
    fob = np.array([s == "Rokokko" for s in D["stil"]]) & ~rev
    sam = ((MID >= 1830) & (MID < 1900) & ~rev & ~np.isin(D["stil"], ["Rokokko", "Barokk"]))
    Yp = Y.copy()
    typ = np.where(rev, 0, 0)
    for t in np.unique(TYPEGR):
        kf = fob & (TYPEGR == t)
        if plant and kf.sum() > 3:
            Yp[rev & (TYPEGR == t)] += plant * (Y[kf].mean(0) - Y[rev & (TYPEGR == t)])
    unionk = np.where(rev | sam)[0]
    s = np.full(N, np.nan)
    for t in np.unique(TYPEGR[unionk]):
        kf = fob & (TYPEGR == t)
        if kf.sum() < 5:
            continue
        s[unionk[TYPEGR[unionk] == t]] = np.linalg.norm(Yp[unionk[TYPEGR[unionk] == t]] - Yp[kf].mean(0), axis=1)
    ok = unionk[np.isfinite(s[unionk])]
    lab = rev[ok]
    stat = float(np.median(s[ok][lab]) - np.median(s[ok][~lab]))
    strata = TYPEGR[ok]
    null = np.array([np.median(s[ok][pl]) - np.median(s[ok][~pl]) for pl in (fp.perm_innan(lab, strata, rng) for _ in range(n_perm))])
    p_naerare = float((np.sum(null <= stat) + 1) / (n_perm + 1))
    return {"n_revival": int(lab.sum()), "n_samtidige": int((~lab).sum()), "median_avstand_revival": float(np.median(s[ok][lab])),
            "median_avstand_samtidige": float(np.median(s[ok][~lab])), "stat": stat, "p_naerare_forbildet": p_naerare}


def kontroll():
    t0 = time.time()
    rng = np.random.default_rng(FROE)
    alle = np.arange(N)
    med = med_utval("samla")
    ut = {"n": N, "df_blokker": {k: int(v.shape[1]) for k, v in BLOKKER.items()}}
    ut["stil_leking"] = {"del_stolar_med_stil": float(np.mean([s != "" for s in D["stil"]])),
                         "pseudostil_lik_stil": float(np.mean(pseudostil() == D["stil"]))}
    # placebo: permuter stilmerka innan museum x type x 50-årsbolk. Unikt bidrag frå stil skal ligge rundt null (justert R2 er forventingsrett)
    strata = np.array(["%s|%s|%d" % (m, t, int(a // 50)) for m, t, a in zip(D["museum"], TYPEGR, np.clip(MID, 1550, 1999))])
    pl = []
    for _ in range(40):
        p = fp.perm_innan(D["stil"], strata, rng)
        B2 = dict(BLOKKER)
        B2["stil"] = dummies(p, 10)
        pl.append(unik(alle, Y3, B2, "stil", med, "stil"))
    ut["placebo_stil"] = {"middel": float(np.mean(pl)), "sd": float(np.std(pl)), "ovre95": float(np.quantile(pl, 0.95))}
    # planta stileffekt: legg ein tilfeldig effekt per stilnivå (SD 0,25 standardiserte einingar) på log B. Det unike bidraget frå stil skal bli funne
    nivaa = {k: rng.normal(0, 0.25) for k in set(D["stil"])}
    Yp = Y3.copy()
    Yp[:, 1] += np.array([nivaa[s] for s in D["stil"]])
    ut["planta_stil"] = {"unik_stil": unik(alle, Yp, BLOKKER, "stil", med, "stil")}
    # planta materialeffekt av same storleik: skal bli funnen som unikt bidrag frå materiale, ikkje frå stil
    nm = {k: rng.normal(0, 0.25) for k in set(D["mat"])}
    Ym = Y3.copy()
    Ym[:, 2] += np.array([nm[s] for s in D["mat"]])
    ut["planta_materiale"] = {"unik_materiale": unik(alle, Ym, BLOKKER, "materiale", med, "stil"), "unik_stil": unik(alle, Ym, BLOKKER, "stil", med, "stil")}
    # revival: planta effekt (halvparten av vegen til forbildet) skal bli funnen i minst 80 % av 100 simuleringar; placebo (permuterte etikettar) gjev p rundt 0,5
    sim = []
    for _ in range(100):
        Yn = Y3 + rng.normal(0, 0.02, Y3.shape)
        sim.append(revival(Yn, rng, n_perm=999, plant=0.5)["p_naerare_forbildet"] < 0.05)
    ut["planta_revival"] = {"del_funne": float(np.mean(sim)), "n_sim": 100}
    ut["revival_n"] = {k: v for k, v in revival(Y3, np.random.default_rng(1), n_perm=9).items() if k.startswith("n_")}
    ut["sekund"] = round(time.time() - t0)
    fp.lagre(MAPPE, "KONTROLL.json", ut)
    print(json.dumps(ut, ensure_ascii=False, indent=1))


def opne():
    seal = fp.sjekk_forsegla(MAPPE)
    F = json.load(open(os.path.join(MAPPE, "FORESEIINGAR.json"), encoding="utf-8"))
    T = F["tersklar"]
    rng = np.random.default_rng(FROE + 1)
    ut = {"forsegla_commit": seal, "dekomponering": {}}
    for namn, idx in (("samla", np.arange(N)), ("VA", np.where(D["museum"] == "VA")[0]), ("NM", np.where(D["museum"] == "NM")[0])):
        ut["dekomponering"][namn] = dekomponer(idx, Y3, BLOKKER, rng, utval=namn)
    ut["revival"] = revival(Y3, rng)
    # sekundært, utan dom: same dekomponering på 3D-silhuettane (generative; krymping ukjend)
    P = fp.pca_rom(D["trekk"].reshape(N, -1), 10)
    ut["dekomponering_3d_silhuett"] = dekomponer(np.arange(N), np.column_stack([z(P[:, j]) for j in range(10)]), BLOKKER, rng, n_boot=150)
    dom = {}
    d = ut["dekomponering"]
    for mus in ("samla", "VA"):
        dom["A1_stil_er_aggregat_" + mus] = "HELDT" if d[mus]["ki95"]["stil_minus_pseudostil"][1] < T["unik_stil_minus_pseudo_maks"] else "SLO FEIL"
    for mus in ("VA", "NM"):
        dom["A2_stil_slaar_materiale_" + mus] = "HELDT" if d[mus]["ki95"]["stil_minus_materiale"][0] > 0 else "SLO FEIL"
    dom["A3_revival_ikkje_naerare_forbildet"] = "HELDT" if ut["revival"]["p_naerare_forbildet"] >= T["revival_p_min"] else "SLO FEIL"
    if F.get("kontroll_revival_styrke", 1.0) < T["revival_styrke_min"]:
        dom["A3_revival_ikkje_naerare_forbildet"] = "UGYLDIG"
    ut["dom"] = dom
    fp.lagre(MAPPE, "RESULTAT.json", ut)
    print(json.dumps(dom, ensure_ascii=False, indent=1))
    for mus, v in d.items():
        print(mus, "n", v["n"], {k: round(x, 3) for k, x in v["unik"].items()})
    print("revival", ut["revival"])


if __name__ == "__main__":
    if "--kontroll" in sys.argv:
        kontroll()
    elif "--opne" in sys.argv:
        opne()
    else:
        print(__doc__)
