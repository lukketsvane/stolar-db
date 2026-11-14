"""Prove p04: ryggen i tomrommet, svanken foer Staffel (1884).

--kontroll: pålitelegheit, nullmodell, placebo, positiv kontroll, planta effektar og krympe-placebo. Skriv berre kontrolltal.
--opne: sjekkar forseglinga fyrst og reknar estimanden. Skal ikkje køyrast foer forseglinga.

Mål (sjå FORESEIINGAR.json):
  d(u)    djupna frå setekanten til den fremste ryggflata i midtbandet (|y| <= 7,5 cm) i 1 cm-laget u over setet
          (medianen av dei 5 % fremste punkta med normal som peikar fram; kvart tiande punkt i punktskya).
  K       d(12,5) + d(32,5) minus 2 d(22,5), kvar d snitt over lag innan 1 cm. Gyldig når |K| <= 15 cm.
  K_midt  same sonde sentrert ved T/2 (halve høgda frå setet til ryggtoppen T): d(T/2 minus 10) + d(T/2 + 10) minus 2 d(T/2).
          Berre for T >= 45 cm, så sonden aldri ligg lågare enn K-sonden.
  Delta   K minus K_midt. Jamn krumming (same andrederivert overalt) gjev Delta = 0, bule i fast høgd over setet gjev
          Delta > 0, bule midt på ryggen gjev Delta < 0.
  K_fri   d(45) + d(70) minus 2 d(57,5), for T >= 72,5 cm.
Krympegrensa c = 0,25 gonger øvre 95 %-grense for snittet av K i stolane etter 1948 (krav 2: prioren kan dra kvar rygg
0,25 av vegen mot ein moderne snittrygg). c3 tilsvarande for Delta.
"""
import os, sys, time, warnings
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
import felles_p as fp

D = fp.last()
MAPPE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(MAPPE, "_cache_profil.npz")
LAG = 80                        # 1 cm-lag over setet, 0 til 80 cm
SENTER = np.arange(LAG) + 0.5
GRID_C = 10.5 + np.arange(26)   # sentrum for u = 10,5 til 35,5
KMAKS = 15.0                    # |K| over 15 cm er ikkje ein rygg (krumningsradius under om lag 10 cm), men ein instrumentfeil
TMIN = 45.0                     # K_midt berre der T/2 minus 10 >= 12,5
KRYMP = 0.75                    # krympefaktor frå Studie 0a (djupn: høgst 26 % krymping)
N = int(D["n"])
SUITE = np.asarray(D["suite"])
MUS = np.asarray(D["museum"])
AAR = np.asarray(D["aar"], float)
AAR_TIL = np.asarray(D["aar_til"], float)
SETT = np.asarray(D["sett"])
SH = np.asarray(D["m"]["sete_h"], float)
PRE = AAR_TIL <= 1883
NY = AAR > 1948
MUSEUM = ("VA", "NM")
HUNDREAAR = (1600, 1700, 1800)
_U_ALLE, _INV_ALLE = np.unique(SUITE, return_inverse=True)


# ------------------------------------------------------------------ profil per stol (cachet, kan byggjast i fleire køyringar)
def _profil(k, r3, mm, h):
    idn = D["id"][k]
    zf = np.load(os.path.join(fp.HER, "data", "mesh_cache", idn + ".npz"))
    x, y, z, nx, ny, nz = r3.kanonisk(zf["p"], zf["n"], mm[idn], float(D["H"][k]))
    s = slice(None, None, 10)
    x, y, z, nx, nz = x[s], y[s], z[s], nx[s], nz[s]
    L = np.full(LAG, np.nan)
    if not np.isfinite(h):
        return L, np.nan, np.nan
    mid = np.abs(y) <= 7.5
    seat = mid & (np.abs(z - h) <= 2.0) & (nz > 0.5)
    if seat.sum() < 10:
        return L, np.nan, np.nan
    xs = float(np.quantile(x[seat], 0.995))
    u = z - h
    for j in range(LAG):
        m_ = mid & (u >= j) & (u < j + 1) & (nx > 0)
        if m_.sum() >= 5:
            xv = x[m_]
            thr = np.quantile(xv, 0.95)
            L[j] = xs - np.median(xv[xv >= thr])      # djupn: frå setekanten bak til ryggflata
    back = mid & (x < xs - 3) & (z > h + 5)
    T = float(np.quantile(z[back], 0.99) - h) if back.sum() >= 20 else np.nan
    return L, xs, T


def bygg_cache(budsjett=200.0):
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        L, XS, T, done = z["L"], z["XS"], z["T"], z["done"]
    else:
        L = np.full((N, LAG), np.nan)
        XS = np.full(N, np.nan)
        T = np.full(N, np.nan)
        done = np.zeros(N, bool)
    if done.all():
        return L, XS, T
    import csv, importlib.util
    spec = importlib.util.spec_from_file_location("r3", os.path.join(fp.HER, "38_ramme3d.py"))
    r3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r3)
    mm = {r["id"]: r for r in csv.DictReader(open(os.path.join(fp.HER, "data", "mesh_maal.csv"), encoding="utf-8"))}
    t0 = time.time()
    teljar = 0
    for k in np.where(~done)[0]:
        if time.time() - t0 > budsjett:
            break
        L[k], XS[k], T[k] = _profil(k, r3, mm, SH[k])
        done[k] = True
        teljar += 1
        if teljar % 200 == 0:
            np.savez(CACHE, L=L, XS=XS, T=T, done=done)
    np.savez(CACHE, L=L, XS=XS, T=T, done=done)
    if not done.all():
        print("Cache ufullstendig: %d av %d stolar. Køyr att." % (done.sum(), N))
        sys.exit(0)
    return L, XS, T


# ------------------------------------------------------------------ mål per stol
def dsm(L, c):
    """Djupn ved høgd c over setet (same c for alle stolar), snitt over lag innan 1 cm."""
    idx = [j for j in range(LAG) if abs(j + 0.5 - c) <= 1 + 1e-9]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmean(L[:, idx], axis=1)


def dpt(L, c):
    """Djupn ved høgd c[k] over setet for kvar stol k, same regel som dsm."""
    c = np.asarray(c, float)
    M = (np.abs(SENTER[None, :] - c[:, None]) <= 1 + 1e-9) & np.isfinite(L)
    n = M.sum(axis=1)
    return np.where(n > 0, np.where(M, L, 0.0).sum(axis=1) / np.maximum(n, 1), np.nan)


def kmaal(L):
    G = np.column_stack([dsm(L, c) for c in GRID_C])
    G[np.isfinite(L[:, 10:36]).sum(axis=1) < 20] = np.nan   # rygg krev minst 20 lag i bandet 10 til 35 cm
    K = G[:, 2] + G[:, 22] - 2 * G[:, 12]                    # d(12,5) + d(32,5) minus 2 d(22,5)
    Kf = dsm(L, 45) + dsm(L, 70) - 2 * dsm(L, 57.5)          # placebo lenger opp
    return G, K, Kf


def kmidt(L, T):
    """Same sonde som K, sentrert ved T/2. Krev T >= 45 og minst 77 % av laga innan 11 cm frå T/2."""
    T = np.asarray(T, float)
    m = T / 2.0
    Km = dpt(L, m - 10) + dpt(L, m + 10) - 2 * dpt(L, m)
    band = np.abs(SENTER[None, :] - m[:, None]) <= 11
    ok = (T >= TMIN) & ((band & np.isfinite(L)).sum(axis=1) >= 0.77 * band.sum(axis=1))
    return np.where(ok, Km, np.nan)


def maal(L, T):
    """-> G, K, K_midt, Delta, K_fri, alle med gyldigheitsregelen |.| <= 15 cm."""
    G, K, Kf = kmaal(L)
    K = np.where(np.abs(K) <= KMAKS, K, np.nan)
    Km = kmidt(L, T)
    Km = np.where(np.abs(Km) <= KMAKS, Km, np.nan)
    Dl = np.where(np.isfinite(K) & np.isfinite(Km), K - Km, np.nan)
    Kf = np.where((np.asarray(T) >= 72.5) & (np.abs(Kf) <= KMAKS), Kf, np.nan)
    return G, K, Km, Dl, Kf


def rest(G):
    """Avvik frå korda mellom første og siste punkt i grid (10 til 35 cm)."""
    t = (GRID_C - GRID_C[0]) / (GRID_C[-1] - GRID_C[0])
    chord = G[:, [0]] + (G[:, [-1]] - G[:, [0]]) * t[None, :]
    return G - chord


def linje(L, T):
    """Rett line per stol gjennom djupna frå 10 cm over setet til ryggtoppen (minst til 36 cm), rekna ut på alle lag."""
    Lr = np.full(L.shape, np.nan)
    for k in range(L.shape[0]):
        top = int(min(LAG, np.floor(T[k]))) if np.isfinite(T[k]) else 36
        j = np.arange(10, max(top, 36))
        ok = np.isfinite(L[k, j])
        if ok.sum() < 10:
            continue
        b1, b0 = np.polyfit(SENTER[j][ok], L[k, j][ok], 1)
        Lr[k] = b0 + b1 * SENTER
    return Lr


# ------------------------------------------------------------------ bootstrap over suitar
def ki_suite(v, suite, B=500, froe=1):
    """Snitt og 95 %-intervall med fp.suiteboot (heile suitar trekte med tilbakelegging). -> (snitt, [lo, hi], n)."""
    v = np.asarray(v, float)
    s = np.asarray(suite)
    ok = np.isfinite(v)
    v, s = v[ok], s[ok]
    rng = np.random.default_rng(froe)
    b = np.array([v[fp.suiteboot(s, rng)].mean() for _ in range(B)])
    return float(v.mean()), fp.ki(b), int(len(v))


class Rask:
    """Same trekk som fp.suiteboot (like mange suitar som finst, trekte med tilbakelegging), vektorisert med summar per suite.
    Brukt der mange simulerte datasett på same stolar treng kvar sitt intervall (placebo og planta effekt)."""

    def __init__(self, suite):
        self.u, self.inv = np.unique(np.asarray(suite), return_inverse=True)
        self.nS = len(self.u)
        self.C = np.bincount(self.inv, minlength=self.nS).astype(float)

    def ki(self, v, B, rng):
        S = np.bincount(self.inv, weights=v, minlength=self.nS)
        W = rng.multinomial(self.nS, np.full(self.nS, 1.0 / self.nS), size=B).astype(float)
        b = (W @ S) / np.maximum(W @ self.C, 1e-12)
        return float(v.mean()), float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))


def forteikn(rng):
    """Tilfeldig forteikn per suite (heile suitar snudde saman)."""
    return rng.choice([-1.0, 1.0], len(_U_ALLE))[_INV_ALLE]


# ------------------------------------------------------------------ avgjerdsreglar (same i kontroll og opning)
def regel1(lo_va, lo_nm, c):
    """Foreseiing 1: nedre 95 %-grense over krympegrensa c i VA og i NM kvar for seg."""
    return bool(lo_va > c and lo_nm > c)


def regel3(lo_samla, p_va, p_nm, c3):
    """Foreseiing 3: nedre 95 %-grense for Delta over c3 i samla ramme, og punktestimat over c3 i VA og i NM."""
    return bool(lo_samla > c3 and p_va > c3 and p_nm > c3)


# ------------------------------------------------------------------ positiv kontroll og krympegrenser (same i kontroll og opning)
def positiv(K, Km):
    ut = {}
    for m in ("samla",) + MUSEUM:
        sub = NY & np.isfinite(K) & ((MUS == m) if m != "samla" else True)
        mu, (lo, hi), n = ki_suite(K[sub], SUITE[sub], 500, 7)
        ut[m] = {"snitt": mu, "ki95": [lo, hi], "n": n}
    sub = NY & np.isfinite(Km)
    mm, (lom, him), nm = ki_suite(Km[sub], SUITE[sub], 500, 9)
    ut["K_midt_samla"] = {"snitt": mm, "ki95": [lom, him], "n": nm}
    ok = ut["samla"]["ki95"][0] > 0 and ut["VA"]["snitt"] > 0 and ut["NM"]["snitt"] > 0
    c = (1 - KRYMP) * max(0.0, ut["samla"]["ki95"][1])
    c3 = (1 - KRYMP) * max(0.0, ut["samla"]["ki95"][1] - min(0.0, lom))
    return ut, bool(ok), float(c), float(c3)


def plant2(L, T, Dl, c3, rundar=200):
    """Forankringstesten på bakgrunn utan forteikn (Delta snudd tilfeldig per suite), med tre planta former i alle stolar:
    bule 1,5 cm fram innan 4 cm frå T/2 (midt), bule 1,5 cm fram innan 4 cm frå 20 cm over setet (fast), og jamn krumming
    med K = 3 cm (parabel). Regel 3 skal slå til for fast i minst 90 % av rundane, og for midt og parabel i høgst 10 %."""
    sel = PRE & np.isfinite(Dl)
    Tm = np.where(np.isfinite(T), T, 0.0)[:, None]
    former = {
        "midt": np.where(np.abs(SENTER[None, :] - Tm / 2.0) <= 4.0, 1.5, 0.0),
        "fast": np.where(np.abs(SENTER[None, :] - 20.0) <= 4.0, 1.5, 0.0) + 0 * Tm,
        "parabel": -0.015 * (SENTER[None, :] - 22.5) ** 2 + 0 * Tm,
    }
    Rs = Rask(SUITE[sel])
    Rm = {m: Rask(SUITE[sel & (MUS == m)]) for m in MUSEUM}
    ut = {}
    for f, P in former.items():
        _, _, _, Dp, _ = maal(L - P, T)
        e = Dp - Dl
        ok_e = sel & np.isfinite(e)
        e = np.where(ok_e, e, 0.0)
        rng = np.random.default_rng({"midt": 71, "fast": 72, "parabel": 73}[f])
        slaar, midt_sett = 0, 0
        for r in range(rundar):
            v = forteikn(rng) * np.where(np.isfinite(Dl), Dl, 0.0) + e
            _, lo, hi = Rs.ki(v[sel], 200, rng)
            pv = {m: float(np.mean(v[sel & (MUS == m)])) for m in MUSEUM}
            slaar += regel3(lo, pv["VA"], pv["NM"], c3)
            midt_sett += hi < 0
        ut[f] = {"plantverknad": float(np.mean(e[ok_e])), "regel3": slaar / rundar, "ki_under_0": midt_sett / rundar}
    ok = ut["fast"]["regel3"] >= 0.9 and ut["midt"]["regel3"] <= 0.1 and ut["parabel"]["regel3"] <= 0.1
    return ut, bool(ok), int(sel.sum())


def paalit_alle(K, Dl, Kf):
    ut = {}
    for namn, v in (("K", K), ("Delta", Dl), ("K_fri", Kf)):
        fin = np.isfinite(v)
        p = fp.paalit(v[fin], SETT[fin]) if fin.sum() >= 20 else np.nan
        lo, hi = np.nanquantile(v[fin], [0.05, 0.95])
        pw = fp.paalit(np.clip(v[fin], lo, hi), SETT[fin]) if fin.sum() >= 20 else np.nan
        fv, ns = fp.feilvarians(np.where(fin, v, np.nan), SETT)
        ut[namn] = {"paalit": float(p), "paalit_winsor5": float(pw), "feil_sd": float(np.sqrt(fv)), "sett": int(ns)}
    return ut


# ------------------------------------------------------------------ kontrollar (berre kontrolltal)
def kontroll():
    L, XS, T = bygg_cache()
    G, K, Km, Dl, Kf = maal(L, T)
    _, Kraa, _ = kmaal(L)
    fin = np.isfinite(K)
    print("Stolar: %d. K rekna: %d. Utanfor |K| <= 15 (instrumentfeil): %d (foer 1884: %d, etter 1948: %d)." % (
        N, np.isfinite(Kraa).sum(), (np.isfinite(Kraa) & ~fin).sum(), (np.isfinite(Kraa) & ~fin & PRE).sum(),
        (np.isfinite(Kraa) & ~fin & NY).sum()))
    print("Gyldig K: %d (VA %d, NM %d). Foer 1884: VA %d, NM %d. Delta foer 1884: VA %d, NM %d. K_fri foer 1884: %d." % (
        fin.sum(), (fin & (MUS == "VA")).sum(), (fin & (MUS == "NM")).sum(), (fin & PRE & (MUS == "VA")).sum(),
        (fin & PRE & (MUS == "NM")).sum(), (np.isfinite(Dl) & PRE & (MUS == "VA")).sum(),
        (np.isfinite(Dl) & PRE & (MUS == "NM")).sum(), (np.isfinite(Kf) & PRE).sum()))
    for m in MUSEUM:
        print("   hundreår %s: %s" % (m, ", ".join("%d: %d" % (h, (fin & PRE & (MUS == m) & (AAR // 100 * 100 == h)).sum())
                                                  for h in HUNDREAAR)))
    kont = {}

    # 1 pålitelegheit
    pa = paalit_alle(K, Dl, Kf)
    for namn in ("K", "Delta", "K_fri"):
        q = pa[namn]
        print("1 paalit(%s) = %.3f (winsor 5 %%: %.3f), feil-sd %.2f cm, %d ekte sett  krav 0,7  -> %s" % (
            namn, q["paalit"], q["paalit_winsor5"], q["feil_sd"], q["sett"], "HELD" if q["paalit"] >= 0.7 else "IKKJE HELD"))
    kont["port1"] = pa["K"]["paalit"] >= 0.7
    kont["port3"] = pa["Delta"]["paalit"] >= 0.7
    kont["port4"] = pa["K_fri"]["paalit"] >= 0.7

    # 2 nullmodell: restane stokka om i høgda innanfor kvar stol
    rng = np.random.default_rng(20261113)
    for m in MUSEUM:
        sel = fin & PRE & (MUS == m) & np.all(np.isfinite(G), axis=1)
        Ri = rest(G[sel])[:, 1:25]
        vals = np.empty(1000)
        for r in range(1000):
            perm = np.argsort(rng.random(Ri.shape), axis=1)
            full = np.zeros((Ri.shape[0], 26))
            full[:, 1:25] = np.take_along_axis(Ri, perm, axis=1)
            vals[r] = np.mean(full[:, 2] + full[:, 22] - 2 * full[:, 12])
        ok = abs(vals.mean()) <= 1.96 * vals.std() / np.sqrt(len(vals))
        kont["null_" + m] = ok
        print("2 nullmodell %s: middel %.4f, sd %.4f (n=%d)  -> %s" % (m, vals.mean(), vals.std(), sel.sum(), "HELD" if ok else "IKKJE HELD"))

    # 3 placebo: permuterte merke innan museum
    lab = PRE.astype(int)
    for m in MUSEUM:
        allm = fin & (MUS == m)
        base = np.mean(K[allm])
        vals = np.array([np.mean(K[allm & (fp.perm_innan(lab, MUS, rng) == 1)]) - base for _ in range(200)])
        ok = abs(vals.mean()) <= 1.96 * vals.std() / np.sqrt(len(vals))
        kont["placebo_" + m] = ok
        print("3 placebo-permutasjon %s: middel %.4f, sd %.4f  -> %s" % (m, vals.mean(), vals.std(), "HELD" if ok else "IKKJE HELD"))

    # 4 positiv kontroll (stolar etter 1948) og krympegrensene c og c3
    pos, ok_pos, c, c3 = positiv(K, Km)
    for m in ("samla",) + MUSEUM:
        q = pos[m]
        print("4 positiv kontroll %s: n %d, snitt K %.3f, KI [%.3f, %.3f]" % (m, q["n"], q["snitt"], q["ki95"][0], q["ki95"][1]))
    q = pos["K_midt_samla"]
    print("4 positiv kontroll K_midt (T >= 45): n %d, snitt %.3f, KI [%.3f, %.3f]" % (q["n"], q["snitt"], q["ki95"][0], q["ki95"][1]))
    print("4 positiv kontroll (KI over 0 samla, snitt over 0 i VA og NM)  -> %s" % ("HELD" if ok_pos else "IKKJE HELD (prøva er blind)"))
    print("4 krympegrenser: c = %.3f cm (K), c3 = %.3f cm (Delta)" % (c, c3))
    kont["positiv"] = ok_pos

    # 5 placebo utan forteikn: K snudd tilfeldig per suite. Regel 1 skal slå til i høgst 5 % av 200 rundar.
    sel = PRE & fin
    Rm = {m: Rask(SUITE[sel & (MUS == m)]) for m in MUSEUM}
    rng5 = np.random.default_rng(505)
    slaar, slaar0 = 0, {m: 0 for m in MUSEUM}
    Kz = np.where(fin, K, 0.0)
    for r in range(200):
        v = forteikn(rng5) * Kz
        lo = {}
        for m in MUSEUM:
            _, lo[m], _ = Rm[m].ki(v[sel & (MUS == m)], 200, rng5)
            slaar0[m] += lo[m] > 0
        slaar += regel1(lo["VA"], lo["NM"], c)
    ok5 = slaar / 200 <= 0.05
    kont["forteikn"] = ok5
    print("5 placebo utan forteikn: regel 1 slår til i %d av 200 (KI over 0 utan krympegrense: VA %d, NM %d)  -> %s" % (
        slaar, slaar0["VA"], slaar0["NM"], "HELD" if ok5 else "IKKJE HELD"))

    # 6 planta effekt 1: ryggflata 1,5 cm fram mellom 18 og 27 cm over setet i 20 % av suitane, på bakgrunn utan forteikn.
    # Planten går gjennom same mål (maal). Fasit: 0,2 gonger 3 cm = 0,6 cm. KI skal dekkje fasiten i minst 90 % av 200 rundar,
    # i samla ramme og i VA og NM kvar for seg.
    P1 = np.zeros(LAG)
    P1[18:27] = 1.5
    _, Kp, _, _, _ = maal(L - P1[None, :], T)
    e = Kp - K
    sel = PRE & fin & np.isfinite(e)
    print("6 planta effekt 1: verknad per planta stol %.3f cm (sd %.3f)" % (np.mean(e[sel]), np.std(e[sel])))
    su = np.unique(SUITE)
    FASIT = 0.2 * 3.0
    Rs = Rask(SUITE[sel])
    Rm = {m: Rask(SUITE[sel & (MUS == m)]) for m in MUSEUM}
    dek = {m: 0 for m in ("samla",) + MUSEUM}
    kraft, auke = 0, []
    ez = np.where(sel, e, 0.0)
    for t in range(200):
        r = np.random.default_rng(5000 + t)
        pl = np.isin(SUITE, r.choice(su, int(round(0.2 * len(su))), replace=False))
        v = forteikn(r) * Kz + np.where(pl, ez, 0.0)
        mu, lo, hi = Rs.ki(v[sel], 200, r)
        auke.append(mu)
        dek["samla"] += lo <= FASIT <= hi
        lom = {}
        for m in MUSEUM:
            _, lom[m], him = Rm[m].ki(v[sel & (MUS == m)], 200, r)
            dek[m] += lom[m] <= FASIT <= him
        kraft += regel1(lom["VA"], lom["NM"], c)
    ok6 = all(dek[m] >= 180 for m in dek)
    kont["plant1"] = ok6
    print("6 planta effekt 1: snitt %.3f cm (fasit %.2f); KI dekkjer fasiten: samla %d, VA %d, NM %d av 200; regel 1 slår til i %d av 200  -> %s" % (
        np.mean(auke), FASIT, dek["samla"], dek["VA"], dek["NM"], kraft, "HELD" if ok6 else "IKKJE HELD"))

    # 7 planta effekt 2: forankringstesten (Delta) skil bule i fast høgd frå bule midt på ryggen og frå jamn krumming
    p2, ok7, n7 = plant2(L, T, Dl, c3)
    for f in ("fast", "midt", "parabel"):
        q = p2[f]
        print("7 planta effekt 2 %-7s: verknad på Delta %.3f cm, regel 3 slår til i %.0f %%, KI under 0 i %.0f %% (n %d)" % (
            f, q["plantverknad"], 100 * q["regel3"], 100 * q["ki_under_0"], n7))
    kont["plant2"] = ok7
    print("7 planta effekt 2 (fast >= 90 %%, midt og parabel <= 10 %%)  -> %s" % ("HELD" if ok7 else "IKKJE HELD"))

    # 8 krympe-placebo (krav 2). Kvar rygg før 1884 blir gjort rett (K = 0), dregen 0,25 av vegen mot snittforma til stolane
    # etter 1948 (krumminga deira, rest frå eiga line), og får målefeilen til K og Delta. Utan krympegrense skal han kunne
    # gje utslag; med krympegrensa c og c3 skal regel 1 og regel 3 ikkje slå til.
    Lr = linje(L, T)
    ny = NY & fin
    res = L[ny] - Lr[ny]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        tres = np.where(np.isfinite(res).sum(axis=0) >= 10, np.nanmean(res, axis=0), 0.0)
    Lsh = np.where(np.isfinite(L), Lr + (1 - KRYMP) * tres[None, :], np.nan)
    _, Ksh, _, Dsh, _ = maal(Lsh, T)
    rng8 = np.random.default_rng(8008)
    Ksh = Ksh + rng8.normal(0.0, pa["K"]["feil_sd"], N)
    Dsh = Dsh + rng8.normal(0.0, pa["Delta"]["feil_sd"], N)
    lo8 = {}
    for m in ("samla",) + MUSEUM:
        sub = PRE & np.isfinite(Ksh) & ((MUS == m) if m != "samla" else True)
        mu, (lo, hi), n = ki_suite(Ksh[sub], SUITE[sub], 500, 8)
        lo8[m] = lo
        print("8 krympe-placebo K %s: n %d, snitt %.3f, KI [%.3f, %.3f]; over 0: %s, over c: %s" % (
            m, n, mu, lo, hi, "ja" if lo > 0 else "nei", "ja" if lo > c else "nei"))
    sub = PRE & np.isfinite(Dsh)
    mu, (lo, hi), n = ki_suite(Dsh[sub], SUITE[sub], 500, 18)
    pv = {m: float(np.mean(Dsh[sub & (MUS == m)])) for m in MUSEUM}
    r3_0 = regel3(lo, pv["VA"], pv["NM"], 0.0)
    r3_c = regel3(lo, pv["VA"], pv["NM"], c3)
    print("8 krympe-placebo Delta: n %d, snitt %.3f, KI [%.3f, %.3f], VA %.3f, NM %.3f; regel 3 utan grense: %s, med c3: %s" % (
        n, mu, lo, hi, pv["VA"], pv["NM"], "slår til" if r3_0 else "slår ikkje til", "slår til" if r3_c else "slår ikkje til"))
    ok8 = (not any(lo8[m] > c for m in lo8)) and not r3_c
    kont["krymp"] = ok8
    print("8 krympe-placebo (regel 1 og 3 med krympegrense slår ikkje til)  -> %s" % ("HELD" if ok8 else "IKKJE HELD"))

    lese = [kont["port1"], kont["positiv"], kont["null_VA"], kont["null_NM"], kont["placebo_VA"], kont["placebo_NM"],
            kont["forteikn"], kont["plant1"], kont["krymp"]]
    print("SAMLA for å lese prøva (port, positiv kontroll, null, placebo, planta effekt 1, krympe): %s" % (
        "alle held" if all(lese) else "ein eller fleire held ikkje"))
    print("Foreseiing 3 (port Delta og planta effekt 2): %s" % ("kan prøvast" if kont["port3"] and kont["plant2"] else "UGYLDIG"))
    print("Foreseiing 4 (port K_fri): %s" % ("kan prøvast" if kont["port4"] else "UGYLDIG"))


# ------------------------------------------------------------------ opning (forsegla; skal ikkje køyrast foer forseglinga)
def opne():
    fp.sjekk_forsegla(MAPPE)
    L, XS, T = bygg_cache()
    G, K, Km, Dl, Kf = maal(L, T)
    pa = paalit_alle(K, Dl, Kf)
    port1, port3, port4 = (pa[x]["paalit"] >= 0.7 for x in ("K", "Delta", "K_fri"))
    pos, ok_pos, c, c3 = positiv(K, Km)
    p2, ok_p2, _ = plant2(L, T, Dl, c3)
    blind = not (ok_pos and port1)
    idx = fp.museum_idx(D)
    ut = {"n": int(N), "per_museum": {}, "foreseiingar": {}, "kort": "",
          "kontroll": {"paalit": pa, "positiv": pos, "positiv_held": ok_pos, "c": c, "c3": c3, "plant2": p2, "plant2_held": ok_p2}}
    for m in ("samla",) + MUSEUM:
        msk = np.zeros(N, bool)
        msk[idx[m]] = True
        rad = {}
        for namn, v, froe in (("K", K, 1), ("Delta", Dl, 2), ("K_fri", Kf, 3)):
            sub = PRE & np.isfinite(v) & msk
            mu, kiv, n = ki_suite(v[sub], SUITE[sub], 500, froe)
            rad[namn] = {"n": n, "snitt": mu, "ki95": kiv}
        for h in HUNDREAAR:
            sub = PRE & np.isfinite(K) & msk & (AAR // 100 * 100 == h)
            rad["K_%d" % h] = {"n": int(sub.sum()), "snitt": float(np.mean(K[sub])) if sub.sum() else None}
        ut["per_museum"][m] = rad
    pm = ut["per_museum"]

    def dom(held, gyldig=True):
        if not gyldig:
            return "UGYLDIG"
        return "HELDT" if held else "SLO FEIL"

    v1 = regel1(pm["VA"]["K"]["ki95"][0], pm["NM"]["K"]["ki95"][0], c)
    ut["foreseiingar"]["1"] = {"verdi": {m: pm[m]["K"]["snitt"] for m in ("samla",) + MUSEUM}, "ki95": {m: pm[m]["K"]["ki95"] for m in ("samla",) + MUSEUM},
                               "terskel_c": c, "dom": dom(v1, not blind)}
    celler = [pm[m]["K_%d" % h] for m in MUSEUM for h in HUNDREAAR]
    v2 = all(q["snitt"] is not None and q["snitt"] > c for q in celler)
    g2 = all(q["n"] >= 10 for q in celler)
    ut["foreseiingar"]["2"] = {"verdi": {m: {str(h): pm[m]["K_%d" % h]["snitt"] for h in HUNDREAAR} for m in MUSEUM}, "ki95": None,
                               "terskel_c": c, "dom": dom(v2, (not blind) and g2)}
    v3 = regel3(pm["samla"]["Delta"]["ki95"][0], pm["VA"]["Delta"]["snitt"], pm["NM"]["Delta"]["snitt"], c3)
    ut["foreseiingar"]["3"] = {"verdi": {m: pm[m]["Delta"]["snitt"] for m in ("samla",) + MUSEUM}, "ki95": pm["samla"]["Delta"]["ki95"],
                               "terskel_c3": c3, "dom": dom(v3, (not blind) and port3 and ok_p2)}
    v4 = pm["samla"]["K_fri"]["ki95"][0] <= c and pm["samla"]["K_fri"]["snitt"] < 0.5 * pm["samla"]["K"]["snitt"]
    ut["foreseiingar"]["4"] = {"verdi": pm["samla"]["K_fri"]["snitt"], "ki95": pm["samla"]["K_fri"]["ki95"], "dom": dom(v4, (not blind) and port4)}
    f = lambda x: ("%.2f" % x).replace(".", ",")
    ut["kort"] = ("Før 1884 er snittet av K %s cm i VA (95 %% KI %s til %s) og %s cm i NM (%s til %s) mot ei krympegrense på %s cm, "
                  "og Delta er %s cm (%s til %s) i samla ramme." % (
                      f(pm["VA"]["K"]["snitt"]), f(pm["VA"]["K"]["ki95"][0]), f(pm["VA"]["K"]["ki95"][1]), f(pm["NM"]["K"]["snitt"]),
                      f(pm["NM"]["K"]["ki95"][0]), f(pm["NM"]["K"]["ki95"][1]), f(c), f(pm["samla"]["Delta"]["snitt"]),
                      f(pm["samla"]["Delta"]["ki95"][0]), f(pm["samla"]["Delta"]["ki95"][1])))
    fp.lagre(MAPPE, "RESULTAT.json", ut)
    # figurdata: snittprofilen (rest frå korda mellom 10,5 og 35,5 cm) før 1884 per museum og etter 1948
    fig = {"u": GRID_C.tolist()}
    for namn, grp in (("VA_foer_1884", PRE & (MUS == "VA")), ("NM_foer_1884", PRE & (MUS == "NM")), ("etter_1948", NY)):
        sub = grp & np.isfinite(K) & np.all(np.isfinite(G), axis=1)
        fig[namn] = {"n": int(sub.sum()), "rest": np.mean(rest(G[sub]), axis=0).tolist()}
    fp.lagre(MAPPE, "FIGURDATA.json", fig)


if __name__ == "__main__":
    if "--opne" in sys.argv:
        opne()
    else:
        kontroll()
