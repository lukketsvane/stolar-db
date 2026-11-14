import os, sys, json, warnings
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import felles_p as fp
import numpy as np

# p06: kvadrert flytting mellom nabohundreår mot sann varians innan hundreåret, langs dei prinsipale aksane
# for spreiinga innan hundreåret. Teorem 2 (Kovarians) med isotropt skift i trykka gjev b = 2,
# nøytral kopiering (Lande) gjev b = 1. Sjå FORESEIINGAR.json.
#   --kontroll: pålitelegheit, aksar, placebo, nullmodellar og planta effekt. Skriv KONTROLL.json.
#               Reknar ALDRI flyttinga D på dei verkelege bolkmerka.
#   --opne:     forsegla køyring på heile ramma, VA og NM kvar for seg, og WOOD åleine.

warnings.filterwarnings("ignore", category=RuntimeWarning)
D = fp.last()
MAPPE = os.path.dirname(os.path.abspath(__file__))

FROE = 20261113
NSPLIT = 200          # delingar i halvdelar A og B etter suite
MIN_BOLK = 20         # bolk med færre stolar i museet fell ut
PAALIT_KRAV = 0.7     # port per koordinat og per akse
NB_OPNE = 500         # bootstrap over suitar i --opne
SKRIN = 0.75          # krympe-placebo: x' = median + 0,75 (x - median) for 3D-koordinatane
B_LAAG, B_HOEG = 1.5, 2.5
PHI = [0.3, 1.0, 3.0]   # planta flytting: sum D_i / sum lambda_i per hundreårssteg
R_VANDRING, R_DRIFT, R_FELLES, R_KRYMP, R_ANNA = 12, 16, 16, 6, 2
NB_SIM = 20           # bootstrap per realisering i kontrollen
NB_PLACEBO = 100
FPR_MAKS = 0.10       # høgste del nullrealiseringar som får domen HELDT
STYRKE_MIN = 0.80     # lågaste del drift-realiseringar (b = 2) som får domen HELDT
Q = np.round(np.arange(0.10, 0.9001, 0.05), 2)
BW = 100              # bolkbreidd i år: hundreår (1500-talet, ..., 1900-talet; år etter 1999 går i 1900-talet)


def sett_bolk(bw):
    global BW, START, KB, PAIRS, PLAC_PAIRS, CENT
    BW = bw
    START = 1500 if bw == 100 else 1550
    KB = (2000 - START) // bw
    PAIRS = np.array([[k, k + 1] for k in range(KB - 1)])
    PLAC_PAIRS = np.array([[2 * k, 2 * k + 1] for k in range(KB)])
    CENT = START + bw * (np.arange(KB) + 0.5)


sett_bolk(BW)


def bolk_av(aar):
    return ((np.clip(np.asarray(aar, float), START, 1999) - START) // BW).astype(int)


def bolk50(aar):
    return (np.clip(np.asarray(aar, float), 1550, 1999) // 50).astype(int) - 31


def bygg_Y():
    lag = np.asarray(D["lag"], float)
    n = D["n"]
    cum = np.cumsum(lag, axis=1)
    tot = cum[:, -1]
    top = np.concatenate([[0.0], np.arange(1, 61) * 2.5])
    Hq = np.full((n, len(Q)), np.nan)
    for i in range(n):
        if not (np.isfinite(tot[i]) and tot[i] > 0):
            continue
        cn = np.concatenate([[0.0], cum[i] / tot[i]])
        Hq[i] = np.interp(Q, cn, top)
    Y = np.column_stack([Hq, np.asarray(D["m"]["sete_h"], float), np.asarray(D["H"], float)])
    names = ["log_h_q%02d" % int(round(q * 100)) for q in Q] + ["log_sete_h", "log_H"]
    with np.errstate(divide="ignore", invalid="ignore"):
        L = np.log(np.where(Y > 0, Y, np.nan))
    ok = np.all(np.isfinite(L), axis=1)
    return L, names, ok


# ------------------------------------------------------------------ ramme, port og koordinatar
L0, NAMN0, OK0 = bygg_Y()
ROW = np.where(OK0)[0]
RAW = L0[ROW]
SETT = np.asarray(D["sett"])[ROW]
SUITE = np.asarray(D["suite"])[ROW]
AAR = np.asarray(D["aar"], float)[ROW]
AART = np.asarray(D["aar_til"], float)[ROW]
MUS = np.asarray(D["museum"])[ROW]
MAT = np.asarray(D["mat"])[ROW]
BRA = np.log(np.asarray(D["m"]["breidd3d"], float)[ROW] / np.asarray(D["B"], float)[ROW])
DJA = np.log(np.asarray(D["m"]["djupn3d"], float)[ROW] / np.asarray(D["D"], float)[ROW])
PA_RAW = np.array([fp.paalit(RAW[:, c], SETT) for c in range(RAW.shape[1])])
G = np.where(PA_RAW >= PAALIT_KRAV)[0]
NAMN = [NAMN0[c] for c in G]
if "log_H" not in NAMN:
    sys.exit("log_H held ikkje porten; prøva kan ikkje byggjast.")
# Modellhøgdene er skalerte til katalog-H. Alle 18 modellkoordinatane blir difor skrivne som log(h / H):
# då fell skaleringsfeilen u i katalog-H bort frå dei (lærdom 9), og han står berre att i log H.
X = RAW[:, G].copy()
MOD = np.array([nm != "log_H" for nm in NAMN])
IH = NAMN.index("log_H")
X[:, MOD] -= RAW[:, [NAMN0.index("log_H")]]
NAMN_X = [("rel_" + nm[4:]) if mo else nm for nm, mo in zip(NAMN, MOD)]
PA_X = np.array([fp.paalit(X[:, c], SETT) for c in range(X.shape[1])])
P = X.shape[1]

# Målefeil: samla kovarians innan dei ekte setta. Alle setta ligg i NM; instrumentet er det same i VA,
# så same feilmatrise blir brukt i begge museum. I bootstrap blir setta trekte på nytt.
_us, _cs = np.unique(SETT, return_counts=True)
SETLIST = [np.where(SETT == s)[0] for s in _us[_cs >= 2]]
SCAT = np.array([(X[g] - X[g].mean(0)).T @ (X[g] - X[g].mean(0)) for g in SETLIST])
SDF = np.array([len(g) - 1 for g in SETLIST], float)
SETT_MUS = {mu: int(sum(MUS[g[0]] == mu for g in SETLIST)) for mu in ("VA", "NM")}


def E_fra(w):
    return np.tensordot(w, SCAT, 1) / (w @ SDF)


E0 = E_fra(np.ones(len(SETLIST)))
SK = np.where(MOD, SKRIN, 1.0)
E3D = np.where(np.outer(MOD, MOD), E0, 0.0)   # målefeilen til 3D-koordinatane, lagd på i krympe-placeboen


def varu_for(m):
    """Øvre grense for Var(u): Cov(log(breidd3d/B), log(djupn3d/D)) pluss 1,96 SE."""
    a, b = BRA[m], DJA[m]
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    p = (a - a.mean()) * (b - b.mean())
    v = p.sum() / (len(p) - 1)
    return float(v), float(v + 1.96 * p.std(ddof=1) / np.sqrt(len(p)))


# ------------------------------------------------------------------ estimator
def innan(Ys, bk, Kb):
    """Samla kovarians innan bolk (bolkar med minst MIN_BOLK). Brukar ikkje flyttinga."""
    N = len(Ys)
    O = np.zeros((N, Kb))
    O[np.arange(N), bk] = 1.0
    valid = O.sum(0) >= MIN_BOLK
    O = O * valid[None, :]
    rowv = O.sum(1) > 0
    cnt = O.sum(0)
    dfw = int(rowv.sum() - valid.sum())
    if dfw <= Ys.shape[1] or valid.sum() < 2:
        return None
    mu = (O.T @ Ys) / np.maximum(cnt, 1)[:, None]
    R = (Ys - O @ mu)[rowv]
    return R.T @ R / dfw, O


def aksar(S, E):
    lam, V = np.linalg.eigh(S - E)
    o = np.argsort(lam)[::-1]
    lam, V = lam[o], V[:, o]
    rel = 1.0 - np.einsum("ji,jk,ki->i", V, E, V) / np.einsum("ji,jk,ki->i", V, S, V)
    return lam, V, rel


def estimer(Ys, bk, hf, pairs, Kb, E, K):
    """-> lam (K sanne variansar langs aksane), Dc (K kvadrerte flyttingar), V. hf: (S, N) halvdelar etter suite."""
    r = innan(Ys, bk, Kb)
    if r is None:
        return None
    S, O = r
    lam, V, _ = aksar(S, E)
    lam, V = lam[:K], V[:, :K]
    Z = Ys @ V
    A = (hf == 0).astype(float)
    Bm = 1.0 - A
    OT = O.T
    TA = A[:, None, :] * OT[None, :, :]
    TB = Bm[:, None, :] * OT[None, :, :]
    cA, cB = TA.sum(2), TB.sum(2)
    mA = (TA @ Z) / cA[:, :, None]
    mB = (TB @ Z) / cB[:, :, None]
    p1, p2 = pairs[:, 0], pairs[:, 1]
    dA = mA[:, p2, :] - mA[:, p1, :]
    dB = mB[:, p2, :] - mB[:, p1, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        w = 4.0 / (1.0 / cA[:, p1] + 1.0 / cA[:, p2] + 1.0 / cB[:, p1] + 1.0 / cB[:, p2])
    prod = dA * dB
    good = np.isfinite(prod).all(axis=2) & np.isfinite(w) & (w > 0)
    w = np.where(good, w, 0.0)
    prod = np.where(np.isfinite(prod), prod, 0.0)
    den = w.sum(1)
    num = np.einsum("sp,spc->sc", w, prod)
    Ds = np.where(den[:, None] > 0, num / np.maximum(den, 1e-300)[:, None], np.nan)
    return lam, np.nanmean(Ds, axis=0), V


def fit_b(lam, Dc):
    """D_i = c lam_i^b. Minste kvadrat på råskala for D_i / lam_i = c lam_i^(b-1), så negative D_i blir verande."""
    ok = np.isfinite(lam) & np.isfinite(Dc) & (lam > 0)
    if ok.sum() < 4:
        return np.nan, np.nan
    l = lam[ok] / np.exp(np.mean(np.log(lam[ok])))
    y = Dc[ok] / lam[ok]

    def rss(a):
        F = l[None, :] ** a[:, None]
        c = (F * y[None, :]).sum(1) / (F * F).sum(1)
        return ((y[None, :] - c[:, None] * F) ** 2).sum(1), c

    g = np.linspace(-3.0, 5.0, 801)
    r, _ = rss(g)
    j = int(np.argmin(r))
    g2 = np.linspace(g[max(j - 1, 0)], g[min(j + 1, len(g) - 1)], 201)
    r2, c2 = rss(g2)
    k = int(np.argmin(r2))
    return float(g2[k] + 1.0), float(c2[k])


def velg_K(m):
    """Talet på leiande aksar med pålitelegheit minst 0,7 og positiv sann varians. Brukar berre spreiinga innan bolk."""
    a0, a1 = AAR[m], AART[m]
    S, _ = innan(X[m], bolk_av(np.floor((a0 + a1) / 2)), KB)
    lam, V, rel = aksar(S, E0)
    K = 0
    while K < P and rel[K] >= PAALIT_KRAV and lam[K] > 0:
        K += 1
    return K, lam, rel, V


# ------------------------------------------------------------------ éi køyring (verkeleg, placebo eller simulert)
def kjor(m, scen, nb, seed, phi=None, K=None):
    """scen: real, placebo, vandring, drift, felles, hfeil, krymp_vandring, krymp_drift."""
    rng = np.random.default_rng(seed)
    krymp = scen.startswith("krymp_")
    sc = scen[len("krymp_"):] if krymp else scen
    idx0 = np.where(m)[0]
    n = len(idx0)
    Xm = X[idx0]
    suite = SUITE[idx0]
    a0, a1 = AAR[idx0], AART[idx0]
    if K is None:
        K = velg_K(m)[0]
    uniq, inv = np.unique(suite, return_inverse=True)
    hf = rng.integers(0, 2, size=(NSPLIT, len(uniq)))[:, inv]
    bk_mid = bolk_av(np.floor((a0 + a1) / 2))
    pairs, Kb, base, phi_pl = PAIRS, KB, Xm, np.nan
    if sc == "placebo":
        pairs, Kb = PLAC_PAIRS, 2 * KB
    elif sc != "real":
        # Verkelege restar rundt 50-årsbolkane (midtpunktet); dei verkelege bolkmidla er tekne bort.
        b50 = bolk50(np.floor((a0 + a1) / 2))
        Om = np.zeros((n, 9))
        Om[np.arange(n), b50] = 1.0
        R = Xm - Om @ ((Om.T @ Xm) / np.maximum(Om.sum(0), 1)[:, None])
        S0, _ = innan(Xm, bk_mid, KB)
        lam0, V0, _ = aksar(S0, E0)
        lam0 = np.maximum(lam0, 0.0)
        # Restane er sentrerte i dei verkelege bolkane. Analyserer me dei i dei same bolkane, er bolkmidla nøyaktig null,
        # halvdelane A og B blir negativt korrelerte, og D blir skeiv nedover. Dateringane blir difor bytte mellom
        # suitar av same storleik: bolktala står, suitane held saman, og bolkmidla får vanleg utvalsstøy.
        groups = [np.where(inv == j)[0] for j in range(len(uniq))]
        sizes = np.array([len(g) for g in groups])
        a0p, a1p = a0.copy(), a1.copy()
        for sz in np.unique(sizes):
            js = np.where(sizes == sz)[0]
            for jf, jt in zip(js, rng.permutation(js)):
                a0p[groups[jt]] = a0[groups[jf]]
                a1p[groups[jt]] = a1[groups[jf]]
        a0, a1 = a0p, a1p
        bk_mid = bolk_av(np.floor((a0 + a1) / 2))
        # Eitt sant år per stol for heile realiseringa; analysen trekkjer år på nytt (dateringsuvisse).
        yr_true = np.clip(a0 + np.floor(rng.random(n) * (a1 - a0 + 1)), START, 1999)
        bk_true = bolk_av(yr_true)
        if sc == "vandring":      # Lande: steg ~ N(0, k Sigma)
            st = rng.normal(0, 1, (KB, P)) * np.sqrt(lam0)[None, :]
        elif sc in ("drift", "hfeil"):   # Teorem 2: steg = c Sigma beta, beta isotrop; langs akse i: c lam_i s_i
            st = np.tile(lam0 * rng.choice([-1.0, 1.0], P), (KB, 1))
        elif sc == "felles":      # éin felles faktor: berre den første aksen flyttar seg
            st = np.zeros((KB, P))
            st[:, 0] = rng.normal(0, 1, KB) * np.sqrt(lam0[0])
        else:
            raise ValueError(scen)
        st[0] = 0.0
        traj = np.cumsum(st, axis=0)
        cnt = np.bincount(bk_true, minlength=KB).astype(float)
        num = den = 0.0
        for k in range(KB - 1):
            if cnt[k] >= MIN_BOLK and cnt[k + 1] >= MIN_BOLK:
                wk = 1.0 / (1.0 / cnt[k] + 1.0 / cnt[k + 1])
                num += wk * np.sum((traj[k + 1, :K] - traj[k, :K]) ** 2)
                den += wk
        phi_raa = num / den / np.sum(lam0[:K])
        traj = traj * np.sqrt(phi / phi_raa)
        phi_pl = float(phi)
        # Middelet går samanhengande gjennom tida (lineært mellom bolkmidtane), så rørsla innan bolken òg er med.
        mu_aks = np.column_stack([np.interp(yr_true, CENT, traj[:, j]) for j in range(P)])
        base = R + mu_aks @ V0.T
        if sc == "hfeil":
            base = base.copy()
            base[:, IH] += rng.normal(0, np.sqrt(max(varu_for(m)[1], 1e-12)), n)
        if krymp:
            med = np.median(base, axis=0)
            base = med + SK[None, :] * (base - med) + rng.multivariate_normal(np.zeros(P), E3D, n, method="eigh")

    def E_d(w):
        E = E_fra(w)
        return (SK[:, None] * E * SK[None, :] + E3D) if krymp else E

    rec = []
    for d in range(nb + 1):
        if d == 0:
            idx, bkd, Ed = np.arange(n), bk_mid, E_d(np.ones(len(SETLIST)))
        else:
            idx = fp.suiteboot(suite, rng)
            bkd = bolk_av(a0[idx] + np.floor(rng.random(len(idx)) * (a1[idx] - a0[idx] + 1)))
            Ed = E_d(np.bincount(rng.integers(0, len(SETLIST), len(SETLIST)), minlength=len(SETLIST)).astype(float))
        bk = 2 * bkd + rng.integers(0, 2, len(idx)) if sc == "placebo" else bkd
        res = estimer(base[idx], bk, hf[:, idx], pairs, Kb, Ed, K)
        if res is None:
            rec.append(None)
            continue
        lam, Dc, _ = res
        b, c = fit_b(lam, Dc)
        ok = np.isfinite(Dc) & (lam > 0)
        ph = float(np.sum(Dc[ok]) / np.sum(lam[ok])) if ok.any() else np.nan
        yb = float(np.mean(Dc[ok] / lam[ok])) if ok.any() else np.nan
        sl = float(np.sum(Dc[ok] * lam[ok]) / np.sum(lam[ok] ** 2)) if ok.any() else np.nan
        rec.append((b, c, ph, yb, lam, Dc, sl, float(Dc[1]) if len(Dc) > 1 else np.nan))
    pt = rec[0]
    draws = [r for r in rec[1:] if r is not None]
    col = lambda j: np.array([r[j] for r in draws], float)
    bs, phs, ybs, sls, d2s = col(0), col(2), col(3), col(6), col(7)
    kif = lambda v: [float(x) for x in fp.ki(v)] if np.isfinite(v).sum() > 10 else [np.nan, np.nan]
    # D_2 > 0 er ein einsidig påstand: nedre grense er 5 %-kvantilen (einsidig 95 %).
    d2lo = float(np.quantile(d2s[np.isfinite(d2s)], 0.05)) if np.isfinite(d2s).sum() > 10 else np.nan
    return {
        "n": int(n), "K": int(K), "b": float(pt[0]), "c": float(pt[1]), "ki": kif(bs),
        "phi": float(pt[2]), "ki_phi": kif(phs), "ybar": float(pt[3]), "ki_ybar": kif(ybs),
        "stigning": float(pt[6]), "ki_stigning": kif(sls), "D2": float(pt[7]), "ki_D2": kif(d2s), "D2_nedre": d2lo,
        "nb": int(np.isfinite(bs).sum()), "bs": [float(x) for x in bs], "d2s": [float(x) for x in d2s],
        "lam": [float(x) for x in pt[4]], "D": [float(x) for x in pt[5]], "phi_planta": phi_pl,
    }


def robust_ki(v, z):
    """Normaltilnærma intervall med robust skala (1,4826 MAD). Brukt i kontrollen, der kvar realisering har få trekk."""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    med = np.median(v)
    s = 1.4826 * np.median(np.abs(v - med))
    return [float(med - z * s), float(med + z * s)]


def dekk(ki, x):
    return bool(ki[0] <= x <= ki[1])


def heldt(b, ki):
    """HELDT: b i [1,5; 2,5] og 95 %-KI for b dekkjer ikkje 1."""
    return bool(np.isfinite(b) and B_LAAG <= b <= B_HOEG and not dekk(ki, 1.0))


# ------------------------------------------------------------------ kontroll
def kontroll():
    print("Ramme: %d stolar i felles_p, %d med alle 19 mål (VA %d, NM %d)." % (
        D["n"], len(ROW), int((MUS == "VA").sum()), int((MUS == "NM").sum())))
    print("Pålitelegheit per koordinat (fp.paalit, krav 0,7), rå og som log(h/H):")
    for c, nm in enumerate(NAMN0):
        j = NAMN.index(nm) if nm in NAMN else None
        print("  %-12s %.3f  %s" % (nm, PA_RAW[c], ("%.3f" % PA_X[j]) if j is not None else "FJERNA"))
    print("Ekte sett: %d (VA %d, NM %d). Same feilmatrise i begge museum." % (len(SETLIST), SETT_MUS["VA"], SETT_MUS["NM"]))
    aks = {}
    for mus in ["VA", "NM"]:
        K, lam, rel, _ = velg_K(MUS == mus)
        aks[mus] = {"K": int(K), "lam": [float(x) for x in lam], "paalit_akse": [float(x) for x in rel]}
        print("%s: K = %d aksar. Sann varians: %s" % (mus, K, " ".join("%.2e" % x for x in lam[:K])))
        print("    pålitelegheit langs aksane: %s" % " ".join("%.3f" % x for x in rel[:K + 2]))
        print("    lambda_1 / lambda_K = %.0f" % (lam[0] / lam[K - 1]))
    tal, flagg, phi_min, phi_port = {}, {}, {}, {}
    for k, mus in enumerate(["VA", "NM"]):
        m = MUS == mus
        K = aks[mus]["K"]
        pl = kjor(m, "placebo", NB_PLACEBO, FROE + 10000 * k + 7, K=K)
        tal["placebo_" + mus] = {kk: pl[kk] for kk in ("phi", "ki_phi", "ybar", "ki_ybar", "stigning", "ki_stigning",
                                                       "D2", "ki_D2", "nb", "n", "K")}
        flagg["placebo_" + mus] = (dekk(pl["ki_ybar"], 0.0) and dekk(pl["ki_phi"], 0.0) and dekk(pl["ki_stigning"], 0.0)
                                   and dekk(pl["ki_D2"], 0.0))
        print("placebo %s: sum D / sum lambda %.4f KI [%.4f, %.4f]; middel D/lambda %.4f KI [%.4f, %.4f]; "
              "stigning D mot lambda %.4f KI [%.4f, %.4f]; D_2 KI [%.5f, %.5f]" % (
                  mus, pl["phi"], pl["ki_phi"][0], pl["ki_phi"][1], pl["ybar"], pl["ki_ybar"][0], pl["ki_ybar"][1],
                  pl["stigning"], pl["ki_stigning"][0], pl["ki_stigning"][1], pl["ki_D2"][0], pl["ki_D2"][1]))
        ok_phi = []
        for jp, phi in enumerate(PHI):
            scen = [("vandring", R_VANDRING), ("drift", R_DRIFT), ("felles", R_FELLES), ("krymp_vandring", R_KRYMP)]
            if jp == 1:
                scen += [("krymp_drift", R_ANNA), ("hfeil", R_ANNA)]
            res = {}
            for js, (s, R) in enumerate(scen):
                pts, kis, d2n, phm, bs = [], [], [], [], []
                for r in range(R):
                    o = kjor(m, s, NB_SIM, FROE + 10000 * k + 1000 * jp + 100 * js + r, phi=phi, K=K)
                    pts.append(o["b"])
                    kis.append(robust_ki(o["bs"], 1.96))
                    d2n.append(robust_ki(o["d2s"], 1.645)[0])
                    phm.append(o["phi"])
                    bs += o["bs"]
                kip = [float(x) for x in fp.ki(bs)]
                dom = [heldt(b, ki) for b, ki in zip(pts, kis)]
                d2pos = float(np.mean([dn > 0 for dn in d2n]))
                res[s] = {"b_median": float(np.nanmedian(pts)), "b_realiseringar": [float(x) for x in pts],
                          "ki_samla": kip, "del_heldt": float(np.mean(dom)), "del_D2_over_0": d2pos,
                          "phi_maalt_median": float(np.nanmedian(phm)), "R": R, "nb_per_realisering": NB_SIM}
                print("  %s phi=%.2f %-15s b median %.2f  KI samla [%.2f, %.2f]  del HELDT %.2f  del D2>0 %.2f  "
                      "phi målt %.3f  (b: %s)" % (mus, phi, s, np.nanmedian(pts), kip[0], kip[1], np.mean(dom), d2pos,
                                                  np.nanmedian(phm), " ".join("%.2f" % x for x in pts)))
            f = {
                "vandring": dekk(res["vandring"]["ki_samla"], 1.0) and not dekk(res["vandring"]["ki_samla"], 2.0)
                and res["vandring"]["del_heldt"] <= FPR_MAKS,
                "drift": dekk(res["drift"]["ki_samla"], 2.0) and not dekk(res["drift"]["ki_samla"], 1.0)
                and res["drift"]["del_heldt"] >= STYRKE_MIN,
                "felles": res["felles"]["del_heldt"] <= FPR_MAKS,
                "krymp_vandring": dekk(res["krymp_vandring"]["ki_samla"], 1.0)
                and not dekk(res["krymp_vandring"]["ki_samla"], 2.0) and res["krymp_vandring"]["del_heldt"] <= FPR_MAKS,
            }
            tal["phi%.2f_%s" % (phi, mus)] = res
            flagg["phi%.2f_%s" % (phi, mus)] = f
            ok_phi.append(all(f.values()))
            print("  %s phi=%.2f kontrollar: %s" % (mus, phi, f))
        # phi_min: lågaste nivå der alle kontrollane held, og held på alle høgare nivå
        pm = None
        for jp in range(len(PHI) - 1, -1, -1):
            if ok_phi[jp]:
                pm = PHI[jp]
            else:
                break
        phi_min[mus] = pm
        # Porten i --opne står på same skala som den målte flyttinga: median målt phi for drift ved phi_min.
        phi_port[mus] = tal["phi%.2f_%s" % (pm, mus)]["drift"]["phi_maalt_median"] if pm is not None else None
    klar = bool(all(flagg["placebo_" + mu] for mu in ("VA", "NM")) and all(phi_min[mu] is not None for mu in ("VA", "NM")))
    print("phi_min (planta):", phi_min, " port for målt phi:", phi_port)
    print("klar =", klar)
    fp.lagre(MAPPE, "KONTROLL.json", {
        "klar": klar, "phi_min": phi_min, "phi_port": phi_port, "aksar": aks, "koordinatar": NAMN_X,
        "koordinatar_paalit_raa": {nm: float(p) for nm, p in zip(NAMN0, PA_RAW)},
        "koordinatar_paalit_log_h_over_H": {nm: float(p) for nm, p in zip(NAMN_X, PA_X)},
        "ekte_sett": {"alle": len(SETLIST), **SETT_MUS},
        "ramme": {"felles_p": int(D["n"]), "komplette": int(len(ROW)), "VA": int((MUS == "VA").sum()),
                  "NM": int((MUS == "NM").sum())},
        "var_u_ovre_grense": {mu: varu_for(MUS == mu)[1] for mu in ("VA", "NM")},
        "kontrollar": flagg, "tal": tal, "phi_nivaa": PHI, "krav": {
            "fpr_maks": FPR_MAKS, "styrke_min": STYRKE_MIN, "nb_per_realisering": NB_SIM, "nb_placebo": NB_PLACEBO,
            "krympe": SKRIN},
        "merknad": "hfeil og krymp_drift er rapporterte, ikkje krav."})


# ------------------------------------------------------------------ opning
def opne():
    fp.sjekk_forsegla(MAPPE)
    kp = os.path.join(MAPPE, "KONTROLL.json")
    kt = json.load(open(kp, encoding="utf-8")) if os.path.exists(kp) else {"klar": False}
    runs = {"samla": np.ones(len(ROW), bool), "VA": MUS == "VA", "NM": MUS == "NM", "WOOD": MAT == "WOOD"}
    res = {}
    for i, (namn, m) in enumerate(runs.items()):
        res[namn] = kjor(m, "real", NB_OPNE, FROE + 1000 + i)

    def dom_for(mus):
        r = res[mus]
        pm = (kt.get("phi_port") or {}).get(mus)
        if not kt.get("klar") or pm is None:
            return "UGYLDIG", "kontrollane heldt ikkje"
        if not (np.isfinite(r["phi"]) and r["phi"] >= pm):
            return "UGYLDIG", "flyttinga er mindre enn porten der metoden skil 2 frå 1"
        if not np.isfinite(r["b"]):
            return "SLO FEIL", "b kunne ikkje tilpassast"
        return ("HELDT", "") if heldt(r["b"], r["ki"]) else ("SLO FEIL", "")

    dva, gva = dom_for("VA")
    dnm, gnm = dom_for("NM")
    if dva == "HELDT" and dnm == "HELDT":
        dom = "HELDT"
    elif "SLO FEIL" in (dva, dnm):
        dom = "SLO FEIL"
    else:
        dom = "UGYLDIG"
    fore = [
        {"namn": "b i %s" % mu, "verdi": res[mu]["b"], "ki95": res[mu]["ki"], "dom": dm, "grunn": gm,
         "D2": res[mu]["D2"], "D2_nedre_einsidig95": res[mu]["D2_nedre"], "phi": res[mu]["phi"],
         "phi_port": (kt.get("phi_port") or {}).get(mu)}
        for mu, dm, gm in (("VA", dva, gva), ("NM", dnm, gnm))
    ]
    kort = "Langs dei prinsipale aksane er b = %.2f i VA (95 %% KI %.2f til %.2f) og %.2f i NM (%.2f til %.2f); domen er %s." % (
        res["VA"]["b"], res["VA"]["ki"][0], res["VA"]["ki"][1], res["NM"]["b"], res["NM"]["ki"][0], res["NM"]["ki"][1], dom)
    fp.lagre(MAPPE, "RESULTAT.json", {
        "n": {k: v["n"] for k, v in res.items()},
        "per_museum": {k: {"b": v["b"], "ki95": v["ki"], "c": v["c"], "K": v["K"], "phi": v["phi"], "ki_phi": v["ki_phi"],
                           "D2": v["D2"], "D2_nedre": v["D2_nedre"], "nb": v["nb"]} for k, v in res.items()},
        "foreseiingar": fore, "dom": dom, "kort": kort,
        "ramme_talet_i_felles_p": int(D["n"]), "bootstrap": NB_OPNE,
    })
    fp.lagre(MAPPE, "FIGURDATA.json", {k: {"lam": v["lam"], "D": v["D"], "K": v["K"]} for k, v in res.items()})
    print(kort)


if __name__ == "__main__":
    if "--opne" in sys.argv:
        opne()
    elif "--kontroll" in sys.argv:
        kontroll()
    else:
        print("Bruk --kontroll eller --opne")
