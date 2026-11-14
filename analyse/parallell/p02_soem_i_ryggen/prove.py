import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import felles_p as fp
D = fp.last()
MAPPE = os.path.dirname(os.path.abspath(__file__))

import json
import warnings
import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)

# p02 Sømmen i ryggen. Granska og retta før forsegling (sjå "gransking" i FORESEIINGAR.json).
# ------------------------------------------------------------------ oppsett
DZ = 2.5                      # cm per voksel
JS = np.arange(5, 23)         # 18 punkt: u = 2,5 j cm over setet (j = 5..22, 12,5 til 55 cm)
NJ = len(JS)
NAV = ["sete", "golv", "topp", "del"]
ANDRE = ["golv", "topp", "del"]
ZMAX = 59                     # 60 lag, 0..59
N = int(D["n"])
SEED = 20261113
PAALIT_KRAV = 0.7
NMIN_PUNKT = 30               # minste tal stolar i eit punkt for å rekne tau
NMIN_STOFF = 50               # minste tal stolar i kvar stoffgruppe (WOOD, andre) for f5
BAND = (35.0, 47.5)
PLANT_DTAU = 0.10
Q_F4 = 0.975                  # f4: G_sete over 97,5-persentilen i nullen (retta for krympinga, sjå krympe-placeboen)
TREKK_NAMN = ("d", "c", "w")
TREKK_FORSEGLA = ("w",)       # utfallet av pålitelegheitsregelen (sjå velg_trekk); opne stoppar om regelen gjev noko anna


def _kod(x):
    return np.unique(np.asarray(x).astype(str), return_inverse=True)[1].astype(np.int64)


SH0 = np.asarray(D["m"]["sete_h"], float)
SETT = np.asarray(D["sett"]).astype(str)
SUITE = np.asarray(D["suite"]).astype(str)
MUS = np.asarray(D["museum"]).astype(str)
MAT = np.asarray(D["mat"]).astype(str)
TYP = np.asarray(D["type"]).astype(str)
BOLK = np.asarray(D["bolk"]).astype(int)
AAR = np.asarray(D["aar"], float)
AAR_TIL = np.asarray(D["aar_til"], float)
ARMSTOL = np.nan_to_num(np.asarray(D["armlene"], float)) == 1
SETE_KAT = np.asarray(D["sete_kat"], float)                  # katalogsete (cm), nan der det manglar
SC = _kod(SETT)
SUC = _kod(SUITE)
MATK = _kod(MAT)
GK = _kod(np.char.add(np.char.add(MUS, "|"), np.char.add(MAT, np.char.add("|", TYP))))
KG = int(GK.max()) + 1
NSUITE = int(SUC.max()) + 1
FIRST = np.array([np.where(SUC == s)[0][0] for s in range(NSUITE)])   # første stol i kvar suite


def forbered():
    """Per stol: midband-belegg (bakdjupn-oppslag), setekant, c, w og ryggtopp frå vokslane."""
    yc = (np.arange(64) - 31.5) * DZ
    mid = np.abs(yc) <= 7.5
    bred = np.abs(yc) <= 15.0
    xr = np.arange(64)
    LF = np.full((N, 60, 64), -1, np.int16)   # LF[k, z, t] = største x <= t med belegg i midtbandet
    XF = np.full((N, 60), -1, np.int16)       # XF[k, z] = fremste fylte x i midtbandet (setekant når z = setelag)
    CZ = np.zeros((N, 60))                    # c: delen fylte ruter i |y| <= 15 sett framfrå
    WZ = np.zeros((N, 60))                    # w: breidda av det fylte sett framfrå, cm
    RT = np.full(N, np.nan)                   # ryggtopp, cm over golv (øvre kant)
    for k in range(N):
        V = fp.voksel(k)                       # (60 z, 64 x bak->fram, 64 y)
        M = V[:, :, mid].any(axis=2)
        LF[k] = np.maximum.accumulate(np.where(M, xr[None, :], -1), axis=1)
        XF[k] = np.where(M.any(axis=1), 63 - M[:, ::-1].argmax(axis=1), -1)
        P = V.any(axis=1)                      # framfrå: (60 z, 64 y)
        CZ[k] = P[:, bred].sum(axis=1) / bred.sum()
        hy = P.any(axis=1)
        lo = P.argmax(axis=1)
        hi = 63 - P[:, ::-1].argmax(axis=1)
        WZ[k] = np.where(hy, (hi - lo + 1) * DZ, 0.0)
        R = V[:, :32][:, :, mid].any(axis=(1, 2))   # bakre halvdel, midtbandet
        if R.any():
            RT[k] = (np.where(R)[0].max() + 1) * DZ
    return LF, XF, CZ, WZ, RT


LF, XF, CZ0, WZ0, RT = forbered()
RYGG = RT - SH0
ZS0 = np.round(SH0 / DZ)
_okz = np.isfinite(ZS0) & (ZS0 >= 0) & (ZS0 <= ZMAX) & np.isfinite(RT)
BASE = _okz & (RYGG >= 57.5)          # hovudutval: alle stolar med rygg minst 57,5 cm over setet (same stolar i alle lag)
BASE_ALLE = _okz                       # glidande tillegg: heile ramma, stolar som når laget
K0 = int(round(float(np.nanmedian(SH0)) / DZ))                      # golvgitter: 2,5 (j + K0) cm


# ------------------------------------------------------------------ geometri og trekk
def lag_ell(a, sh, rt):
    """Lagindeks for kvart av 18 punkt og kvar stol under forankring a. (NJ, m), NaN der laget ikkje finst."""
    if a == "sete":
        L = np.round(sh / DZ)[None, :] + JS[:, None]
    elif a == "golv":
        L = np.broadcast_to((JS[:, None] + K0).astype(float), (NJ, len(sh))).copy()
    elif a == "topp":
        L = np.round(rt / DZ)[None, :] - JS[:, None]
    elif a == "del":
        r = ((JS - 4) / 19.0)[:, None]
        L = np.round((sh[None, :] + r * (rt - sh)[None, :]) / DZ)
    else:
        raise ValueError(a)
    return np.where((L >= 0) & (L <= ZMAX), L.astype(float), np.nan)


def xkoord(a):
    if a == "del":
        return 100.0 * (JS - 4) / 19.0
    if a == "golv":
        return DZ * (JS + K0).astype(float)
    return DZ * JS.astype(float)


def trekk_alle(idx, a, sh, rt):
    """(3, NJ, m): d (djupn frå setekanten til første fylte rute bak, midtbandet), c (fylt del framfrå), w (breidd).
    Setekanten er alltid teken i det målte setelaget til stolen sjølv. Berre brukt til pålitelegheitstabellen."""
    L = lag_ell(a, sh[idx], rt[idx])
    Li = np.where(np.isfinite(L), L, 0).astype(int)
    ii = np.broadcast_to(idx[None, :], Li.shape)
    zs = np.where(np.isfinite(ZS0[idx]), ZS0[idx], 0).astype(int)
    xs = XF[idx, zs].astype(int)
    xb = np.broadcast_to(np.maximum(xs, 0)[None, :], Li.shape)
    lf = LF[ii, Li, xb].astype(int)
    d = np.where((lf >= 0) & (xb >= 0) & (xs[None, :] >= 0), (xb + 1 - lf) * DZ, np.nan)
    c = CZ0[ii, Li]
    w = WZ0[ii, Li]
    F = np.stack([d, c, w])
    return np.where(np.isfinite(L)[None], F, np.nan)


def wverdi(idx, a, sh, wz, rt):
    L = lag_ell(a, sh[idx], rt[idx])
    Li = np.where(np.isfinite(L), L, 0).astype(int)
    v = wz[idx[None, :], Li]
    return np.where(np.isfinite(L), v, np.nan), L


def feil_rask(v, s):
    """Same som fp.feilvarians(v, sett), vektorisert. -> (feilvarians, df)."""
    ok = np.isfinite(v)
    v, s = v[ok], s[ok]
    if len(v) == 0:
        return np.nan, 0.0
    k = int(s.max()) + 1
    cnt = np.bincount(s, minlength=k).astype(float)
    tot = np.bincount(s, weights=v, minlength=k)
    mu = tot / np.maximum(cnt, 1)
    ss = np.bincount(s, weights=(v - mu[s]) ** 2, minlength=k)
    inc = cnt >= 2
    df = float((cnt[inc] - 1).sum())
    return float(ss[inc].sum() / max(df, 1.0)), df


def paalit_rask(v, s):
    ok = np.isfinite(v)
    f, _ = feil_rask(v[ok], s[ok])
    return float(1 - f / np.var(v[ok], ddof=1))


def resid_rask(v, g, kg):
    """Residual etter gruppemiddel innan (museum x mat x type)."""
    ok = np.isfinite(v)
    sm = np.bincount(g[ok], weights=v[ok], minlength=kg)
    cn = np.bincount(g[ok], minlength=kg)
    mu = sm / np.maximum(cn, 1)
    return np.where(ok, v - mu[g], np.nan)


def eta2_ujustert(v, g):
    """Same formel som fp.eta2 (justert for talet på grupper), utan klipping til 0. Klippinga gjev skeive snitt i tau."""
    _, gi = np.unique(g, return_inverse=True)
    k = int(gi.max()) + 1
    n = len(v)
    cnt = np.bincount(gi, minlength=k)
    mu = np.bincount(gi, weights=v, minlength=k) / np.maximum(cnt, 1)
    ssw = float(((v - mu[gi]) ** 2).sum())
    sst = float(((v - v.mean()) ** 2).sum())
    if sst <= 0 or n <= k:
        return np.nan
    return float(1 - (ssw / (n - k)) / (sst / (n - 1)))


def velg_trekk():
    """Pålitelegheitsregelen, fastsett éin gong på hovudutvalet med dei målte ankera (ingen merke):
    eit trekk blir brukt berre om fp.paalit er minst 0,7 i alle 18 punkt under alle fire forankringane.
    Då er samansetjinga av tau den same i kvart punkt og under kvart anker, så skiftet mellom trekk kan ikkje lage steg."""
    idx = np.where(BASE)[0]
    tab = {}
    for a in NAV:
        F = trekk_alle(idx, a, SH0, RT)
        tab[a] = {}
        for t, nv in enumerate(TREKK_NAMN):
            tab[a][nv] = [paalit_rask(F[t, p], SC[idx]) if np.isfinite(F[t, p]).sum() >= NMIN_PUNKT else np.nan for p in range(NJ)]
    bruk = tuple(nv for nv in TREKK_NAMN if min(np.nanmin(tab[a][nv]) for a in NAV) >= PAALIT_KRAV)
    return bruk, tab


def feilvar_fast():
    """Målefeilen til w per anker og punkt, rekna éin gong på hovudutvalet (residual, ekte sett) og halden fast
    i alle delutval, bootstrap-trekk, nullar og plantar. VA har ingen ekte sett; feilen kjem frå NM-setta."""
    idx = np.where(BASE)[0]
    fe = {}
    for a in NAV:
        v, _ = wverdi(idx, a, SH0, WZ0, RT)
        fe[a] = np.array([feil_rask(resid_rask(v[p], GK[idx], KG), SC[idx])[0] for p in range(NJ)])
    return fe


FE = feilvar_fast()


def tau_kurve(idx, a, sh, lab, wz=None, rt=None, naar=False):
    """Sann tidsdel tau_j per punkt: eta2(resid w, merke) * Var/(Var - feilvar), feilvar fast per punkt,
    korreksjonen avgrensa til 1/0,7. naar=True: berre stolar der ryggen når laget (glidande tillegg)."""
    wz = WZ0 if wz is None else wz
    rt = RT if rt is None else rt
    v, L = wverdi(idx, a, sh, wz, rt)
    if naar:
        v = np.where(L * DZ < rt[idx][None, :], v, np.nan)
    g, b = GK[idx], lab[idx]
    tau = np.full(NJ, np.nan)
    for p in range(NJ):
        r = resid_rask(v[p], g, KG)
        ok = np.isfinite(r)
        if ok.sum() < NMIN_PUNKT:
            continue
        rr, bb = r[ok], b[ok]
        var = float(np.var(rr, ddof=1))
        if not var > 0:
            continue
        fac = min(var / max(var - FE[a][p], 1e-12), 1.0 / PAALIT_KRAV)
        eta = eta2_ujustert(rr, bb)
        tau[p] = min(eta * fac, 1.0) if np.isfinite(eta) else np.nan
    return tau, xkoord(a)


def stegmodell(tau, x):
    """tau = a + b x + D 1[x >= x*], x* søkt i gitteret. d = RSS utan steg minus RSS med steg; G = d / TSS."""
    ok = np.isfinite(tau) & np.isfinite(x)
    t, xx = tau[ok], x[ok]
    nan = {"d": np.nan, "tss": np.nan, "G": np.nan, "u": np.nan, "delta": np.nan}
    if len(t) < 8:
        return nan
    tss = float(((t - t.mean()) ** 2).sum())
    X0 = np.column_stack([np.ones_like(xx), xx])
    r0 = t - X0 @ np.linalg.lstsq(X0, t, rcond=None)[0]
    rss0 = float(r0 @ r0)
    best = (np.inf, np.nan, np.nan)
    for xk in xx[1:-1]:
        X1 = np.column_stack([X0, (xx >= xk).astype(float)])
        b1 = np.linalg.lstsq(X1, t, rcond=None)[0]
        r1 = t - X1 @ b1
        rss1 = float(r1 @ r1)
        if rss1 < best[0]:
            best = (rss1, float(xk), float(b1[2]))
    d = rss0 - best[0]
    return {"d": float(d), "tss": tss, "G": float(d / tss) if tss > 0 else np.nan, "u": best[1], "delta": best[2]}


def estimer(idx, sh, lab, wz=None, anchors=NAV, rt=None, naar=False):
    """Kurve og stegmodell per anker. Gf = d / TSS_sete: same nemnar for alle anker, så G_sete = Gf_sete
    og dei fire steggevinstane står på same skala (same stolar, same trekk, same tau-eining)."""
    out = {}
    for a in anchors:
        tau, x = tau_kurve(idx, a, sh, lab, wz, rt, naar)
        st = stegmodell(tau, x)
        st["tau"], st["x"] = tau, x
        out[a] = st
    if "sete" in out:
        ts = out["sete"]["tss"]
        for a in out:
            out[a]["Gf"] = out[a]["d"] / ts if (np.isfinite(ts) and ts > 0) else np.nan
    return out


def ki(x):
    x = np.asarray(x, float)
    return fp.ki(x) if np.isfinite(x).any() else [np.nan, np.nan]


def diff_sete(e):
    return float(e["sete"]["Gf"] - np.nanmax([e[a]["Gf"] for a in ANDRE]))


def vinnar(e, anchors=NAV):
    d = np.array([e[a]["d"] for a in anchors], float)
    return anchors[int(np.nanargmax(d))] if np.isfinite(d).any() else "ingen"


# ------------------------------------------------------------------ nullar og kontrollar (ingen verkelege merke i kontrollen)
def placebo_suite(rng):
    """Suitevise bolkmerke permuterte innan museum: same gruppestorleikar, ingen samanheng med forma. -> per suite."""
    return fp.perm_innan(BOLK[FIRST], MUS[FIRST], rng)


def placebo_lab(rng):
    return placebo_suite(rng)[SUC]


class SetePerm:
    """sete_h permutert mellom suitar innan bolk x mat: éin verdi per suite (median), same forskyving for heile suiten."""

    def __init__(self, idx, base=None):
        self.base = SH0 if base is None else base
        self.idx = idx
        us, self.inv = np.unique(SUC[idx], return_inverse=True)
        bi = self.base[idx]
        self.med = np.array([np.nanmedian(bi[self.inv == i]) for i in range(len(us))])
        first = np.zeros(len(us), int)
        first[self.inv[::-1]] = np.arange(len(idx))[::-1]
        self.strat = BOLK[idx][first] * 100 + MATK[idx][first]

    def trekk(self, rng):
        newmed = fp.perm_innan(self.med, self.strat, rng)
        sh = self.base.copy()
        sh[self.idx] = self.base[self.idx] + (newmed - self.med)[self.inv]
        return sh


def null_sete(idx, lab, rng, B, base=None, wz=None):
    sp = SetePerm(idx, base)
    return np.array([estimer(idx, sp.trekk(rng), lab, wz, anchors=["sete"])["sete"]["G"] for _ in range(B)])


def plant_w(typ, A, halv, zs, sh=None):
    """Planta steg i w over fast høgd: sete (42,5 cm over setet), golv (85 cm), del (0,6 av ryggen over setet).
    Halvparten av suitane får A * z, der z er bolkmerket (permutert) skalert til [-0,5; 0,5]."""
    sh = SH0 if sh is None else sh
    sel = halv[SUC]
    z = zs[SUC]
    if typ == "sete":
        thr = np.round(sh / DZ) + 17
    elif typ == "golv":
        thr = np.full(N, 34.0)
    else:
        thr = np.ceil((sh + 0.6 * (RT - sh)) / DZ)
    mask = sel[:, None] & (np.arange(60)[None, :] >= thr[:, None])
    return np.clip(WZ0 + np.where(mask, A * z[:, None], 0.0), 0.0, 64 * DZ)


PTS = {"sete": JS * DZ >= 42.5, "golv": DZ * (JS + K0) >= 85, "del": (JS - 4) / 19.0 >= 0.6}


def trekk_plant(rng):
    ls = placebo_suite(rng)
    zs = (ls - ls.mean()) / max(ls.max() - ls.min(), 1)
    halv = rng.random(NSUITE) < 0.5
    return ls[SUC], zs, halv


def kalibrer(typ, rng, R=20):
    """Finn A slik at middel tau-auke over dei planta punkta er 0,10, snitt over R merketrekk (ingen verkelege merke)."""
    idx = np.where(BASE)[0]
    dr = [trekk_plant(rng) for _ in range(R)]
    base = [tau_kurve(idx, typ, SH0, lab)[0] for lab, _, _ in dr]

    def dtau(A):
        return float(np.mean([np.nanmean((tau_kurve(idx, typ, SH0, lab, plant_w(typ, A, halv, zs))[0] - b)[PTS[typ]])
                              for (lab, zs, halv), b in zip(dr, base)]))

    lo, hi = 0.0, 200.0
    for _ in range(20):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if dtau(m) < PLANT_DTAU else (lo, m)
    A = (lo + hi) / 2
    return A, dtau(A)


def planttest(typ, A, rng, B):
    idx = np.where(BASE)[0]
    grp = {"samla": idx, "VA": idx[MUS[idx] == "VA"], "NM": idx[MUS[idx] == "NM"]}
    res = {g: {"vinn": [], "u": []} for g in grp}
    for _ in range(B):
        lab, zs, halv = trekk_plant(rng)
        wz = plant_w(typ, A, halv, zs)
        for g, ii in grp.items():
            e = estimer(ii, SH0, lab, wz)
            res[g]["vinn"].append(vinnar(e))
            res[g]["u"].append(e["sete"]["u"])
    return {g: (np.array(v["vinn"]), np.array(v["u"], float)) for g, v in res.items()}


def krymp_kopi(idx, rng):
    """Kopi av katalogsete trekt mot medianen med faktor 0,75, pluss målefeilen til 3D-setehøgda (1,4 cm)."""
    med = float(np.median(SETE_KAT[idx]))
    shk = SH0.copy()
    shk[idx] = med + 0.75 * (SETE_KAT[idx] - med) + rng.normal(0.0, 1.4, len(idx))
    return shk, med


def krymp_test(rng, A_golv, RA=100, R=20, B=100, RB=200):
    """KRYMPE-PLACEBO (krav 2). Stolar i hovudutvalet med katalogsete. Kopien erstattar setemålet i estimanden.
    (a) Permuterte merke: G_sete med kopien mot si eiga nullfordeling (kopien permutert innan bolk x mat).
    (b) Sanninga er eit steg i fast høgd over golvet (85 cm). Krympinga åleine skal ikkje få seteankeret til å vinne
        over golvankeret oftare enn det 3D-setet gjer på dei same stolane, og G_sete skal ikkje gå over nullen oftare enn ved tilfelle."""
    idx = np.where(BASE & np.isfinite(SETE_KAT))[0]
    rang = []
    for _ in range(RA):
        shk, med = krymp_kopi(idx, rng)
        lab = placebo_lab(rng)
        G = estimer(idx, shk, lab, anchors=["sete"])["sete"]["G"]
        rang.append(float(np.mean(null_sete(idx, lab, rng, B, base=shk) < G)))
    rang = np.array(rang)
    vinn_k, vinn_3d = [], []
    for _ in range(RB):
        lab, zs, halv = trekk_plant(rng)
        wz = plant_w("golv", A_golv, halv, zs)
        shk, _ = krymp_kopi(idx, rng)
        ek = estimer(idx, shk, lab, wz, anchors=["sete", "golv"])
        e3 = estimer(idx, SH0, lab, wz, anchors=["sete", "golv"])
        vinn_k.append(ek["sete"]["d"] > ek["golv"]["d"])
        vinn_3d.append(e3["sete"]["d"] > e3["golv"]["d"])
    Gb, qb = [], []
    for _ in range(R):
        lab, zs, halv = trekk_plant(rng)
        wz = plant_w("golv", A_golv, halv, zs)
        shk, _ = krymp_kopi(idx, rng)
        Gb.append(estimer(idx, shk, lab, wz, anchors=["sete"])["sete"]["G"])
        qb.append(float(np.quantile(null_sete(idx, lab, rng, B, base=shk, wz=wz), Q_F4)))
    Gb, qb = np.array(Gb), np.array(qb)
    return {"n": int(len(idx)), "krymp_faktor": 0.75, "maalefeil_cm": 1.4,
            "a_placebo_andel_G_over_q95": round(float(np.mean(rang > 0.95)), 3),
            "a_placebo_andel_G_over_q975": round(float(np.mean(rang > Q_F4)), 3),
            "b_golvsanning_andel_sete_slaar_golv_med_kopi": round(float(np.mean(vinn_k)), 3),
            "b_golvsanning_andel_sete_slaar_golv_med_3d_sete": round(float(np.mean(vinn_3d)), 3),
            "b_golvsanning_andel_G_sete_over_q975": round(float(np.mean(Gb > qb)), 3)}


def kraft_f4(typ, A, rng, R=20, B=100):
    """Kor ofte G_sete går over q97,5 i nullen når eit kjent steg er planta (berre syntetiske merke)."""
    idx = np.where(BASE)[0]
    hit = []
    for _ in range(R):
        lab, zs, halv = trekk_plant(rng)
        wz = plant_w(typ, A, halv, zs)
        G = estimer(idx, SH0, lab, wz, anchors=["sete"])["sete"]["G"]
        hit.append(G > np.quantile(null_sete(idx, lab, rng, B, wz=wz), Q_F4))
    return round(float(np.mean(hit)), 3)


def domskraft(A, rng, R=8, Bb=100):
    """Kor ofte domsreglane for f1 og f2 (med suiteboot) gjev HELDT når eit steg er planta ved 42,5 cm over setet,
    og når ingenting er planta. Opplysing til forfattaren, ikkje krav. Berre syntetiske merke."""
    idx = np.where(BASE)[0]
    grp = {"samla": idx, "VA": idx[MUS[idx] == "VA"], "NM": idx[MUS[idx] == "NM"]}
    res = {}
    for namn, skala in (("planta", 1.0), ("ingenting_planta", 0.0)):
        f1, f2 = [], []
        for _ in range(R):
            lab, zs, halv = trekk_plant(rng)
            wz = plant_w("sete", A * skala, halv, zs) if skala > 0 else WZ0
            pt = {g: estimer(ii, SH0, lab, wz) for g, ii in grp.items()}
            db, ub = [], []
            for _ in range(Bb):
                e = estimer(idx[fp.suiteboot(SUC[idx], rng)], SH0, lab, wz)
                db.append(diff_sete(e))
                ub.append(e["sete"]["u"])
            k = ki(ub)
            f1.append(bool(np.mean(np.array(db) > 0) >= 0.95 and all(diff_sete(pt[g]) > 0 for g in grp)))
            f2.append(bool(all(BAND[0] <= pt[g]["sete"]["u"] <= BAND[1] for g in grp) and k[0] >= BAND[0] and k[1] <= BAND[1]))
        res[namn] = {"trekk": R, "f1_heldt": round(float(np.mean(f1)), 3), "f2_heldt": round(float(np.mean(f2)), 3)}
    return res


def kontroll():
    rng = np.random.default_rng(SEED)
    idx = np.where(BASE)[0]
    rap = {"n_hovudutval": int(len(idx)), "n_hovudutval_VA": int((MUS[idx] == "VA").sum()), "n_hovudutval_NM": int((MUS[idx] == "NM").sum()),
           "n_suitar": int(len(np.unique(SUC[idx]))), "n_totalt": N, "n_glidande": int(BASE_ALLE.sum()),
           "n_ikkje_WOOD": {m: int(((MAT[idx] != "WOOD") & (MUS[idx] == m)).sum()) for m in ["VA", "NM"]},
           "n_katalogsete": int((BASE & np.isfinite(SETE_KAT)).sum()), "K0_cm": K0 * DZ}
    v = WZ0[idx, 30]
    rap["sjekk_feilvarians_lik_fp"] = bool(np.isclose(feil_rask(v, SC[idx])[0], fp.feilvarians(v, SETT[idx])[0]))
    lab_t = placebo_lab(rng)
    rap["sjekk_eta2_lik_fp"] = bool(np.isclose(max(eta2_ujustert(v, lab_t[idx]), 0.0), fp.eta2(v, lab_t[idx])))
    # 1 pålitelegheit (ingen utfall, berre måla og trekka)
    bruk, tab = velg_trekk()
    rap["paalit"] = {"sete_h": round(fp.paalit(SH0[idx], SETT[idx]), 3), "ryggtopp": round(fp.paalit(RT[idx], SETT[idx]), 3),
                     "ekte_sett_i_hovudutvalet": int(sum(1 for s in np.unique(SC[idx]) if (SC[idx] == s).sum() >= 2))}
    for nv in TREKK_NAMN:
        rap["paalit"][nv] = {a: {"min": round(float(np.nanmin(tab[a][nv])), 3), "median": round(float(np.nanmedian(tab[a][nv])), 3),
                                 "punkt_under_0_7": int(np.sum(np.array(tab[a][nv]) < PAALIT_KRAV))} for a in NAV}
    rap["trekk_brukt"] = list(bruk)
    trekk_ok = bruk == TREKK_FORSEGLA
    # pålitelegheita til w i kvart museum med den faste feilen (kor ofte korreksjonen blir avgrensa)
    rap["paalit_w_museum"] = {}
    for m in ["VA", "NM"]:
        ii = idx[MUS[idx] == m]
        mins = []
        for a in NAV:
            vv, _ = wverdi(ii, a, SH0, WZ0, RT)
            for p in range(NJ):
                r = resid_rask(vv[p], GK[ii], KG)
                mins.append(1 - FE[a][p] / np.nanvar(r, ddof=1))
        rap["paalit_w_museum"][m] = {"min": round(float(np.min(mins)), 3), "punkt_under_0_7": int(np.sum(np.array(mins) < PAALIT_KRAV))}
    # nullen: kor stor del av suitane kan flyttast (strata bolk x mat med minst to suitar)
    rap["null_flyttbare_suitar"] = {}
    for m in ["VA", "NM"]:
        sp = SetePerm(idx[MUS[idx] == m])
        u, c = np.unique(sp.strat, return_counts=True)
        rap["null_flyttbare_suitar"][m] = round(float(np.isin(sp.strat, u[c >= 2]).mean()), 3)
    # 2 placebo: permuterte suitevise merke skal gje tau nær null og G under nullen, og seteankeret skal ikkje vinne oftare enn dei andre
    pl, rang = [], []
    for r in range(100):
        lab = placebo_lab(rng)
        e = estimer(idx, SH0, lab)
        pl.append(e)
        if r < 60:                                   # kvart placebotrekk får si eiga nullfordeling (100 permutasjonar)
            rang.append(float(np.mean(null_sete(idx, lab, rng, 100) < e["sete"]["G"])))
    rang = np.array(rang)
    tau_pl = np.array([e["sete"]["tau"] for e in pl])
    G_pl = np.array([e["sete"]["G"] for e in pl])
    vinn_pl = np.array([vinnar(e) for e in pl])
    rap["placebo"] = {"tau_middel_abs": round(float(np.nanmean(np.abs(tau_pl))), 4),
                      "tau_middel": round(float(np.nanmean(tau_pl)), 4),
                      "tau_maks": round(float(np.nanmax(tau_pl)), 4),
                      "G_middel": round(float(np.nanmean(G_pl)), 4),
                      "andel_G_over_q95": round(float(np.mean(rang > 0.95)), 3),
                      "andel_G_over_q975": round(float(np.mean(rang > Q_F4)), 3),
                      "vinnar_100_trekk": {a: int(np.sum(vinn_pl == a)) for a in NAV},
                      "andel_diff_over_0": round(float(np.mean([diff_sete(e) > 0 for e in pl])), 3)}
    placebo_ok = (rap["placebo"]["tau_middel_abs"] <= 0.03 and rap["placebo"]["andel_G_over_q95"] <= 0.15
                  and rap["placebo"]["andel_G_over_q975"] <= 0.075 and rap["placebo"]["andel_diff_over_0"] <= 0.35)
    # 3 planta effekt: finn A, deretter 200 trekk per plantetype
    rap["planta"] = {}
    planta_ok = True
    As = {}
    for typ in ["sete", "golv", "del"]:
        A, dt = kalibrer(typ, rng)
        As[typ] = A
        res = planttest(typ, A, rng, 200)
        r = {"A_cm": round(A, 2), "dtau_kalibrert": round(dt, 3)}
        for g, (wins, us) in res.items():
            rg = {"vinnarfordeling": {k: int(np.sum(wins == k)) for k in NAV + ["ingen"]}}
            if typ == "sete":
                rg["andel_sete_vinn_og_u_ok"] = round(float(np.mean((wins == "sete") & (np.abs(us - 42.5) <= 2.5))), 3)
                rg["andel_u_ok"] = round(float(np.mean(np.abs(us - 42.5) <= 2.5)), 3)
            else:
                rg["andel_vinn"] = round(float(np.mean(wins == typ)), 3)
            r[g] = rg
        treff = r["samla"]["andel_sete_vinn_og_u_ok"] if typ == "sete" else r["samla"]["andel_vinn"]
        r["ok"] = bool(treff >= 0.9)
        rap["planta"][typ] = r
        planta_ok = planta_ok and r["ok"]
    # 2b krympe-placebo (krav 2: setemålet er eit 3D-mål)
    rap["krympe"] = krymp_test(rng, As["golv"])
    k = rap["krympe"]
    k["b_auke_fraa_krymping"] = round(k["b_golvsanning_andel_sete_slaar_golv_med_kopi"] - k["b_golvsanning_andel_sete_slaar_golv_med_3d_sete"], 3)
    krymp_ok = (k["a_placebo_andel_G_over_q975"] <= 0.075 and k["b_auke_fraa_krymping"] <= 0.05
                and k["b_golvsanning_andel_G_sete_over_q975"] <= 0.15)
    # 4 kraft for f4 (opplysing, ikkje krav)
    rap["kraft_f4"] = {"sete_planta": kraft_f4("sete", As["sete"], rng), "golv_planta": kraft_f4("golv", As["golv"], rng)}
    rap["domskraft_f1_f2"] = domskraft(As["sete"], rng)
    rap["trekk_ok"] = bool(trekk_ok)
    rap["placebo_ok"] = bool(placebo_ok)
    rap["krympe_ok"] = bool(krymp_ok)
    rap["planta_ok"] = bool(planta_ok)
    rap["klar"] = bool(trekk_ok and placebo_ok and krymp_ok and planta_ok and rap["paalit"]["sete_h"] >= PAALIT_KRAV
                       and rap["sjekk_feilvarians_lik_fp"] and rap["sjekk_eta2_lik_fp"])
    print(json.dumps(rap, ensure_ascii=False, indent=1, default=float))


# ------------------------------------------------------------------ opning (køyrast berre etter forsegling)
def opne():
    fp.sjekk_forsegla(MAPPE)
    bruk, _ = velg_trekk()
    if bruk != TREKK_FORSEGLA:
        sys.exit("Stoppa: pålitelegheitsregelen gjev andre trekk (%s) enn dei forsegla (%s)." % (bruk, TREKK_FORSEGLA))
    rng = np.random.default_rng(SEED + 7)
    B, PN = 500, 200
    idx_alle = np.where(BASE)[0]
    grupper = {"samla": idx_alle, "VA": idx_alle[MUS[idx_alle] == "VA"], "NM": idx_alle[MUS[idx_alle] == "NM"]}
    res = {"n": {k: int(len(v)) for k, v in grupper.items()}, "per_museum": {}}
    kurver = {}
    for navn, idx in grupper.items():
        pk = estimer(idx, SH0, BOLK)
        db, ub, dl, tb, Gb = [], [], [], [], []
        for _ in range(B):
            bi = idx[fp.suiteboot(SUC[idx], rng)]
            e = estimer(bi, SH0, BOLK)
            db.append(diff_sete(e))
            ub.append(e["sete"]["u"])
            dl.append(e["sete"]["delta"])
            tb.append(e["sete"]["tau"])
            Gb.append([e[a]["Gf"] for a in NAV])
        qn = null_sete(idx, BOLK, rng, PN)
        ustar = pk["sete"]["u"]
        tau_under = float(np.nanmean(pk["sete"]["tau"][pk["sete"]["x"] < ustar])) if np.isfinite(ustar) else np.nan
        wood, andre = idx[MAT[idx] == "WOOD"], idx[MAT[idx] != "WOOD"]
        nok = len(wood) >= NMIN_STOFF and len(andre) >= NMIN_STOFF
        uw = estimer(wood, SH0, BOLK, anchors=["sete"])["sete"]["u"] if nok else np.nan
        ua = estimer(andre, SH0, BOLK, anchors=["sete"])["sete"]["u"] if nok else np.nan
        res["per_museum"][navn] = {
            "G": {a: float(pk[a]["Gf"]) for a in NAV}, "G_eigen_tss": {a: float(pk[a]["G"]) for a in NAV},
            "u_sete": float(ustar), "u_sete_ki95": ki(ub),
            "delta_sete": float(pk["sete"]["delta"]), "delta_ki95": ki(dl),
            "tau_under_soem": tau_under,
            "diff_sete_mot_andre": diff_sete(pk), "diff_ki95": ki(db),
            "diff_andel_over_0": float(np.mean(np.array(db) > 0)),
            "G_q975_null": float(np.nanquantile(qn, Q_F4)), "G_median_null": float(np.nanmedian(qn)), "G_null_ki95": ki(qn),
            "n_wood": int(len(wood)), "n_andre": int(len(andre)),
            "u_wood": float(uw), "u_andre": float(ua), "u_diff_wood_andre": float(uw - ua),
        }
        # bandet rundt tau er persentilbandet flytt med skeivskapen i bootstrap (dobla suitar blåser opp eta2 i kvart trekk)
        tb = np.array(tb)
        t0 = np.asarray(pk["sete"]["tau"], float)
        skeiv = np.nanmean(tb, axis=0) - t0
        kurver[navn] = {"tau": [float(v) for v in t0], "x": [float(v) for v in pk["sete"]["x"]], "band": "persentil minus skeivskap",
                        "tau_lo": [float(v) for v in np.nanquantile(tb, 0.025, axis=0) - skeiv],
                        "tau_hi": [float(v) for v in np.nanquantile(tb, 0.975, axis=0) - skeiv],
                        "tau_boot_skeivskap": [float(v) for v in skeiv],
                        "tau_andre_anker": {a: [float(v) for v in pk[a]["tau"]] for a in ANDRE},
                        "x_andre_anker": {a: [float(v) for v in pk[a]["x"]] for a in ANDRE},
                        "G_null": [float(v) for v in qn], "G_obs": {a: float(pk[a]["Gf"]) for a in NAV},
                        "G_ki95": {a: ki([g[i] for g in Gb]) for i, a in enumerate(NAV)}}
    # tillegg (ikkje avgjerande)
    til = {}
    idx_b = idx_alle
    ia = np.where(BASE_ALLE)[0]
    eg = estimer(ia, SH0, BOLK, anchors=["sete"], naar=True)["sete"]
    til["glidande_heile_ramma"] = {"n": int(len(ia)), "G_sete": eg["G"], "u_sete": eg["u"], "delta_sete": eg["delta"],
                                   "tau": [float(v) for v in eg["tau"]]}
    iu = np.where(BASE & ~ARMSTOL)[0]
    eu = estimer(iu, SH0, BOLK)
    til["utan_armstolar"] = {"n": int(len(iu)), "u_sete": eu["sete"]["u"], "diff_sete_mot_andre": diff_sete(eu)}
    ik = np.where(BASE & np.isfinite(SETE_KAT))[0]
    shk = SH0.copy()
    shk[ik] = SETE_KAT[ik]
    ek = estimer(ik, shk, BOLK)
    e3 = estimer(ik, SH0, BOLK)
    til["katalogsete_som_anker"] = {"n": int(len(ik)), "u_sete_kat": ek["sete"]["u"], "diff_kat": diff_sete(ek),
                                    "u_sete_3d_same_stolar": e3["sete"]["u"], "diff_3d_same_stolar": diff_sete(e3)}
    vv, _ = wverdi(idx_b, "sete", SH0, WZ0, RT)
    st = stegmodell(np.nanmean(vv, axis=1), xkoord("sete"))
    til["struktur_ved_soemmen"] = {"u_middelbreidd": st["u"], "G_middelbreidd": st["G"], "delta_cm": st["delta"],
                                   "merknad": "Steg i middelbreidda (ikkje tidsdelen). Ligg det ved u_sete, fell sømmen saman med ei formgrense."}
    a0 = AAR
    a1 = np.where(np.isfinite(AAR_TIL), AAR_TIL, AAR)
    yr = np.clip(a0 + rng.random(N) * (a1 - a0), 1550, 1999)
    ey = estimer(idx_b, SH0, (yr // 50).astype(int))
    til["aar_trekt_i_intervall"] = {"u_sete": ey["sete"]["u"], "diff_sete_mot_andre": diff_sete(ey)}
    res["tillegg"] = til

    # foreseiingar: 95 %-kravet gjeld samla; VA og NM må kvar for seg ha same forteikn og passere same terskel i punktestimatet
    pm = res["per_museum"]
    G3 = ["samla", "VA", "NM"]
    fin = lambda *xs: all(np.isfinite(x) for x in xs)
    f = {}
    f["f1_sete_storre_enn_andre"] = {
        "verdi": {m: pm[m]["diff_sete_mot_andre"] for m in G3}, "ki95": {m: pm[m]["diff_ki95"] for m in G3},
        "andel_bootstrap": {m: pm[m]["diff_andel_over_0"] for m in G3},
        "dom": ("UGYLDIG" if not fin(*[pm[m]["diff_sete_mot_andre"] for m in G3])
                else "SLO FEIL" if any(pm[m]["diff_sete_mot_andre"] <= 0 for m in G3)
                else "HELDT" if pm["samla"]["diff_andel_over_0"] >= 0.95 else "UGYLDIG")}
    inn = lambda u: np.isfinite(u) and BAND[0] <= u <= BAND[1]
    kis = pm["samla"]["u_sete_ki95"]
    f["f2_u_i_band"] = {
        "verdi": {m: pm[m]["u_sete"] for m in G3}, "ki95": {m: pm[m]["u_sete_ki95"] for m in G3},
        "dom": ("UGYLDIG" if any(not np.isfinite(pm[m]["u_sete"]) for m in G3)
                else "SLO FEIL" if any(not inn(pm[m]["u_sete"]) for m in G3)
                else "HELDT" if (kis[0] >= BAND[0] and kis[1] <= BAND[1]) else "UGYLDIG")}
    f["f3_steg_og_under_soem"] = {
        "verdi": {m: pm[m]["delta_sete"] for m in G3}, "ki95": {m: pm[m]["delta_ki95"] for m in G3},
        "tau_under_soem": {m: pm[m]["tau_under_soem"] for m in G3},
        "dom": ("UGYLDIG" if not fin(*[pm[m]["delta_sete"] for m in G3], *[pm[m]["tau_under_soem"] for m in G3])
                else "SLO FEIL" if any(pm[m]["delta_sete"] < 0.10 or pm[m]["tau_under_soem"] >= 0.10 for m in G3)
                else "HELDT" if pm["samla"]["delta_ki95"][0] >= 0.10 else "UGYLDIG")}
    f["f4_over_nullen"] = {
        "verdi": {m: pm[m]["G"]["sete"] for m in G3}, "ki95": {m: kurver[m]["G_ki95"]["sete"] for m in G3},
        "q975_null": {m: pm[m]["G_q975_null"] for m in G3},
        "median_null": {m: pm[m]["G_median_null"] for m in G3},
        "dom": ("UGYLDIG" if not fin(*[pm[m]["G"]["sete"] for m in G3])
                else "HELDT" if (pm["samla"]["G"]["sete"] > pm["samla"]["G_q975_null"]
                                 and all(pm[m]["G"]["sete"] > pm[m]["G_median_null"] for m in ["VA", "NM"])) else "SLO FEIL")}
    dv = {m: pm[m]["u_diff_wood_andre"] for m in G3}
    f["f5_wood_mot_andre"] = {
        "verdi": dv, "ki95": None, "n": {m: [pm[m]["n_wood"], pm[m]["n_andre"]] for m in G3},
        "dom": ("UGYLDIG" if any(not np.isfinite(dv[m]) for m in ["VA", "NM"])
                else "HELDT" if all(abs(dv[m]) <= 5 for m in ["VA", "NM"]) else "SLO FEIL")}
    res["foreseiingar"] = f
    tal = {k: sum(1 for v in f.values() if v["dom"] == k) for k in ["HELDT", "SLO FEIL", "UGYLDIG"]}
    ps = pm["samla"]
    kt = lambda x, n=1: ("%.*f" % (n, x)).replace(".", ",")
    res["kort"] = ("Tidsdelen i ryggbreidda har sitt største steg %s cm over setet (samla, 95 %% mellom %s og %s), "
                   "seteankeret slår dei tre andre i %s %% av trekka, og av fem føreseiingar held %d, %d slo feil og %d er ugyldige."
                   % (kt(ps["u_sete"]), kt(kis[0]), kt(kis[1]), kt(100 * ps["diff_andel_over_0"], 0),
                      tal["HELDT"], tal["SLO FEIL"], tal["UGYLDIG"]))
    fp.lagre(MAPPE, "RESULTAT.json", res)
    fp.lagre(MAPPE, "FIGURDATA.json", kurver)

    # figur: to panel, VA og NM
    S = fp.figurstil()
    plt = S["plt"]
    fig, akser = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
    for ax, m in zip(akser, ["VA", "NM"]):
        k = kurver[m]
        x = np.array(k["x"])
        ax.axhspan(BAND[0], BAND[1], color="#e6e6e6", lw=0, zorder=0)
        ax.fill_betweenx(x, k["tau_lo"], k["tau_hi"], color="#bdbdbd", lw=0, zorder=1)
        ax.plot(k["tau"], x, color="#0c0c0c", lw=1.0, zorder=2)
        if np.isfinite(pm[m]["u_sete"]):
            ax.axhline(pm[m]["u_sete"], color="#0c0c0c", lw=0.5, ls=":", zorder=3)
        ax.axvline(0, color=S["DIM"], lw=0.4, zorder=0)
        ax.set_title(m, fontsize=9, color=S["FG"])
        ax.set_xlabel("tidsdel τ", fontsize=8)
    akser[0].set_ylabel("høgd over setet (cm)", fontsize=8)
    for ax in akser:
        ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(MAPPE, "figur_p02.png"), dpi=200)
    print(json.dumps({"kort": res["kort"], "dom": tal}, ensure_ascii=False))


if __name__ == "__main__":
    modus = sys.argv[1] if len(sys.argv) > 1 else ""
    if modus == "--kontroll":
        kontroll()
    elif modus == "--opne":
        opne()
    else:
        sys.exit("Bruk --kontroll eller --opne")
