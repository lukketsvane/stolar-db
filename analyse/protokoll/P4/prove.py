"""P4 Den einslege stolen: løyst framover eller bakover (tid T3, med avstandsspegel og eige instrument for einsemda).

  python prove.py --kontroll   teljetabellar, placebo, feller og planta verder. Frys tersklar, marginar og portar til
                               KONTROLL.json. Skriv aldri ut det verkelege utfallet.
  python prove.py --opne       (berre etter forsegling) reknar estimanden på heile ramma og i VA og NM kvar for seg,
                               og skriv RESULTAT.json og FIGURDATA.json.

Estimanden følgjer PROTOKOLL.json, P4, steg 1 til 11. Avvik frå protokollen står i FORESEIINGAR.json.
Forventninga over trekka i steg 3 er rekna eksakt (alle moglege trekk av 5 suitar per bolk og éin stol per suite);
det er det same talet som middelet over 200 trekk, utan trekkstøy. 200 trekk med frø 20261113 er køyrde som kontroll.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "parallell"))
import felles_p as fp
D = fp.last()
MAPPE = os.path.dirname(os.path.abspath(__file__))

import csv, json, math, re, time
import numpy as np
from numba import njit
from scipy import stats
from scipy.spatial.distance import cdist

sys.stdout.reconfigure(encoding="utf-8")
HER = fp.HER
ROT = fp.ROT
FROE = 20261113
T0 = time.time()

# ------------------------------------------------------------------ talet på trekk (sjå FORESEIINGAR.json)
N_PLACEBO = 200          # placebo 0 og 1b
N_PLACEBO2 = 200
N_FELLE = 100            # fellene (a), (b), (c)
N_PLANT = 100            # planta verder per forsprang
N_BOOT_FELLE = 300       # suiteboot inne i felle (a)
N_BOOT = 1000            # suiteboot ved opning
N_MC = 200               # trekk i kontrollen av den eksakte forventninga

# ------------------------------------------------------------------ data
N = D["n"]
AAR = D["aar"].astype(float)
TIL = D["aar_til"].astype(float)
MID = (AAR + TIL) / 2
MUS = D["museum"]
MUKODE = np.where(MUS == "VA", 0, 1)
_, SUITE = np.unique(D["suite"], return_inverse=True)
WOOD = D["mat"] == "WOOD"
TG = np.array([0 if t in ("Stol", "Spisestol", "Armstol") else 1 for t in D["type"]])
UKJENT = {"", "ukjent", "unknown", "ikkje registrert", "anonymous", "anoniem", "unknown maker", "unidentified"}
GENERISK = {"chair", "chairs", "armchair", "armchairs", "stol", "armstol", "pair of chairs", "windsor armchair", "windsor chair",
            "dining chair", "hall chair", "sgabello chair", "settee", "rocking chair", "set of chairs", "desk chair", "low chair",
            "spisestuestol", "spisestol", "bergère", "side chair", "lenestol", "karmstol", "easy chair", "corner chair",
            "folding chair", "high chair", "stool", "child's chair", "wing chair", "garden chair", "office chair"}
# attopptakingsstilar og kopiar: same lister som analyse/36_fortid_framtid.py
UTE_STIL = {"Historisme", "Nyrokokko", "Nybarokk", "Dragestil", "Postmodernisme", "Memphis / Postmodernisme"}
KOPI = re.compile(r"kopi|reproduksjon|replica|copy of|rekonstruksjon", re.I)


def pkey(p):
    p = (p or "").strip().lower()
    return "" if p in UKJENT else p


def nkey(namn):
    s = re.sub(r"\s+", " ", (namn or "").strip().lower().replace("originaltittel", "")).strip()
    maker = ""
    if "(" in s:
        s, maker = s.split("(", 1)
        s, maker = s.strip(), maker.rstrip(") ").strip()
    if maker in UKJENT or re.match(r"^(nmk|ok-|om-|nmk\.)", maker) or re.search(r"\d{4}\.\d", maker):
        maker = ""
    if s in GENERISK or s == "":
        return (s + "|" + maker) if maker else ""
    return s


PK = np.array([pkey(p) for p in D["produsent"]])
NK = np.array([nkey(n) for n in D["namn"]])
ATTOPP = np.array([(s in UTE_STIL) or bool(KOPI.search(n)) for s, n in zip(D["stil"], D["namn"])])

# ------------------------------------------------------------------ bolkar (steg 2)
SAM_E, SAM_Y, SAM_A, FOER, ETTER, FF = 0, 1, 2, 3, 4, 5


def spec(sam=12.5, grenser=(12.5, 37.5, 62.5), ff=(62.5, 87.5, 112.5), m=5, msam=5):
    r = [(SAM_E, 0.0, sam, msam, -1), (SAM_Y, 0.0, sam, msam, -1)]
    for side, gr in ((FOER, grenser), (ETTER, grenser), (FF, ff)):
        r += [(side, lo, hi, m, -1) for lo, hi in zip(gr[:-1], gr[1:])]
    return (np.array([x[0] for x in r], np.int64), np.array([x[1] for x in r]), np.array([x[2] for x in r]),
            np.array([x[3] for x in r], np.int64), np.array([x[4] for x in r], np.int64))


HOVUD = spec()
SPEC3 = spec(m=3, msam=3)
TIARS = spec(grenser=(12.5, 22.5, 32.5, 42.5, 52.5, 62.5), ff=(62.5, 72.5, 82.5, 92.5, 102.5, 112.5), m=2)
B8_40 = spec(sam=8.0, grenser=(8.0, 24.0, 40.0), ff=(40.0, 56.0, 72.0))
B20_80 = spec(grenser=(20.0, 50.0, 80.0), ff=(80.0, 110.0, 140.0))
_p = [(SAM_A, 0, 12.5, 5, 0), (SAM_A, 0, 12.5, 5, 1), (FOER, 12.5, 62.5, 5, 0), (FOER, 12.5, 62.5, 5, 1),
      (ETTER, 12.5, 62.5, 5, 0), (ETTER, 12.5, 62.5, 5, 1), (FF, 62.5, 112.5, 5, 0), (FF, 62.5, 112.5, 5, 1)]
POOL = tuple(np.array([x[j] for x in _p], dt) for j, dt in enumerate((np.int64, float, float, np.int64, np.int64)))
FRACS = np.array([0.5, 1 / 3, 2 / 3])


# ------------------------------------------------------------------ kjernen (numba)
@njit(cache=True)
def _binom(nmax, kmax):
    C = np.zeros((nmax + 1, kmax + 1))
    for n in range(nmax + 1):
        C[n, 0] = 1.0
        for k in range(1, min(n, kmax) + 1):
            C[n, k] = C[n - 1, k - 1] + (C[n - 1, k] if k <= n - 1 else 0.0)
    return C


@njit(cache=True)
def _eln_eksakt(d, bi, sl, Kb, mb, ssz, C):
    """Eksakt forventning av ln(minste avstand) når mb[b] av Kb[b] suitar blir trekte i kvar bolk b og éin stol per suite."""
    nbl = Kb.shape[0]
    order = np.argsort(d)
    passed = np.zeros(ssz.shape, np.int64)
    n1 = Kb.copy()
    Fl = np.zeros(ssz.shape, np.int64)
    Fn = np.zeros(nbl, np.int64)
    Gb = np.ones(nbl)
    e = np.zeros(16)
    G = 1.0
    res = 0.0
    for t in range(d.shape[0]):
        q = order[t]
        b = bi[q]
        s = sl[q]
        m = mb[b]
        passed[b, s] += 1
        sz = ssz[b, s]
        if sz == 1:
            n1[b] -= 1
        else:
            if passed[b, s] == 1:
                n1[b] -= 1
                Fl[b, Fn[b]] = s
                Fn[b] += 1
            if passed[b, s] == sz:
                for u in range(Fn[b]):
                    if Fl[b, u] == s:
                        Fl[b, u] = Fl[b, Fn[b] - 1]
                        Fn[b] -= 1
                        break
        for kk in range(m + 1):
            e[kk] = 0.0
        e[0] = 1.0
        for u in range(Fn[b]):
            f = Fl[b, u]
            p = 1.0 - passed[b, f] / ssz[b, f]
            for kk in range(m, 0, -1):
                e[kk] += p * e[kk - 1]
        g = 0.0
        for jj in range(m + 1):
            r = m - jj
            if r <= n1[b]:
                g += C[n1[b], r] * e[jj]
        Gb[b] = g / C[Kb[b], m]
        Gn = 1.0
        for bb in range(nbl):
            Gn *= Gb[bb]
        res += math.log(d[q]) * (G - Gn)
        G = Gn
    return res


@njit(cache=True)
def _eln_mc(d, bi, sl, Kb, mb, kn, ndraw):
    """Middel over ndraw trekk av ln(den kn-te minste avstanden)."""
    nbl = Kb.shape[0]
    E = d.shape[0]
    maxK = 0
    for b in range(nbl):
        maxK = max(maxK, Kb[b])
    cnt = np.zeros((nbl, maxK), np.int64)
    for t in range(E):
        cnt[bi[t], sl[t]] += 1
    off = np.zeros((nbl, maxK), np.int64)
    acc = 0
    for b in range(nbl):
        for s in range(Kb[b]):
            off[b, s] = acc
            acc += cnt[b, s]
    pos = off.copy()
    mem = np.empty(E, np.int64)
    for t in range(E):
        mem[pos[bi[t], sl[t]]] = t
        pos[bi[t], sl[t]] += 1
    tot = 0
    for b in range(nbl):
        tot += mb[b]
    buf = np.empty(tot)
    perm = np.empty(maxK, np.int64)
    res = 0.0
    for r in range(ndraw):
        c = 0
        for b in range(nbl):
            for s in range(Kb[b]):
                perm[s] = s
            for u in range(mb[b]):
                v = u + np.random.randint(Kb[b] - u)
                tmp = perm[u]
                perm[u] = perm[v]
                perm[v] = tmp
                s = perm[u]
                w = off[b, s] + np.random.randint(cnt[b, s])
                buf[c] = d[mem[w]]
                c += 1
        srt = np.sort(buf[:c])
        kk = min(kn, c) - 1
        res += math.log(srt[kk])
    return res / ndraw


@njit(cache=True)
def _wmed(p, w):
    o = np.argsort(p)
    tot = 0.0
    for t in range(p.shape[0]):
        tot += w[t]
    acc = 0.0
    for t in range(p.shape[0]):
        acc += w[o[t]]
        if acc >= 0.5 * tot - 1e-12:
            return p[o[t]]
    return p[o[p.shape[0] - 1]]


@njit(cache=True)
def _net(p, w, n, tau):
    s = 0.0
    for t in range(n):
        if p[t] > tau:
            s += w[t]
        elif p[t] < -tau:
            s -= w[t]
    return s


@njit(cache=True)
def _gruppe(sd):
    if sd <= 2:
        return 0
    if sd == 3:
        return 1
    if sd == 4:
        return 2
    return 3


@njit(cache=True)
def _kjerne(De, Da, X, mid, suite, grp, tiekey, excl, maal, lev, ddm, berre_dd, kmin, bs, blo, bhi, bm, bg, snu, kn, mc, ndraw, froe, fracs, C):
    n = mid.shape[0]
    nb = bs.shape[0]
    kd = X.shape[1]
    nf = fracs.shape[0]
    S = 0
    for j in range(n):
        S = max(S, suite[j] + 1)
    E = np.full(n, np.nan)
    LF = np.full(n, np.nan)
    LE = np.full(n, np.nan)
    K = np.zeros((n, nb), np.int64)
    DD = np.full((n, nf), np.nan)
    DDF = np.full((n, nf), np.nan)
    DDX = np.full(n, np.nan)
    bl = np.empty((nb, n), np.int64)
    bc = np.zeros(nb, np.int64)
    bsl = np.empty((nb, n), np.int64)
    ssz = np.zeros((nb, n), np.int64)
    slot = np.full(S, -1, np.int64)
    tie = np.empty(n, np.int64)
    tsu = np.empty(n, np.int64)
    bE = -1
    bY = -1
    for b in range(nb):
        if bs[b] == 0:
            bE = b
        if bs[b] == 1:
            bY = b
    if mc:
        np.random.seed(froe)
    pbuf = np.empty((3, n))
    wbuf = np.empty((3, n))
    nbuf = np.zeros(3, np.int64)
    cvec = np.empty(kd)
    cb = np.empty(kd)
    v = np.empty(kd)
    order = np.argsort(mid, kind="mergesort")
    smid = mid[order]
    for i in range(n):
        if not (maal[i] and lev[i]):
            continue
        for b in range(nb):
            bc[b] = 0
        nt = 0
        mi = mid[i]
        # bolkane er samanhengande intervall i sortert tid: lo <= -dl < hi (før), lo <= dl < hi (etter)
        for b in range(nb):
            sd = bs[b]
            if sd == 0:
                a0 = np.searchsorted(smid, mi - bhi[b], side="right")
                a1 = np.searchsorted(smid, mi, side="left")
            elif sd == 1:
                a0 = np.searchsorted(smid, mi, side="right")
                a1 = np.searchsorted(smid, mi + bhi[b], side="left")
            elif sd == 2:
                a0 = np.searchsorted(smid, mi - bhi[b], side="right")
                a1 = np.searchsorted(smid, mi + bhi[b], side="left")
            elif sd == 4:
                a0 = np.searchsorted(smid, mi + blo[b], side="left")
                a1 = np.searchsorted(smid, mi + bhi[b], side="left")
            else:
                a0 = np.searchsorted(smid, mi - bhi[b], side="right")
                a1 = np.searchsorted(smid, mi - blo[b], side="right")
            for t in range(a0, a1):
                j = order[t]
                if j == i or (not lev[j]) or excl[i, j]:
                    continue
                if bg[b] >= 0 and grp[j] != bg[b]:
                    continue
                bl[b, bc[b]] = j
                bc[b] += 1
        if bE >= 0:
            a0 = np.searchsorted(smid, mi, side="left")
            a1 = np.searchsorted(smid, mi, side="right")
            for t in range(a0, a1):
                j = order[t]
                if j == i or (not lev[j]) or excl[i, j]:
                    continue
                tie[nt] = j
                nt += 1
        if nt > 0:
            # stolar frå same år: suitane blir fordelte likt på dei to halvdelane, i ei fast tilfeldig rekkjefølgje
            ns = 0
            for t in range(nt):
                s = suite[tie[t]]
                if slot[s] < 0:
                    slot[s] = ns
                    tsu[ns] = s
                    ns += 1
            keys = np.empty(ns)
            for u in range(ns):
                keys[u] = tiekey[tsu[u]]
            od = np.argsort(keys)
            rk = np.empty(ns, np.int64)
            for r in range(ns):
                rk[od[r]] = r
            for t in range(nt):
                j = tie[t]
                r = rk[slot[suite[j]]]
                tilE = (r % 2 == 0) != snu
                b = bE if tilE else bY
                if b >= 0 and (bg[b] < 0 or grp[j] == bg[b]):
                    bl[b, bc[b]] = j
                    bc[b] += 1
            for u in range(ns):
                slot[tsu[u]] = -1
        for b in range(nb):
            ns = 0
            for t in range(bc[b]):
                s = suite[bl[b, t]]
                if slot[s] < 0:
                    slot[s] = ns
                    ssz[b, ns] = 0
                    ns += 1
                bsl[b, t] = slot[s]
                ssz[b, slot[s]] += 1
            for t in range(bc[b]):
                slot[suite[bl[b, t]]] = -1
            K[i, b] = ns
        kok = True
        for b in range(nb):
            if K[i, b] < kmin[b]:
                kok = False
        if not kok:
            continue
        for g in range(3):
            if berre_dd:
                break
            tot = 0
            nbl = 0
            maxK = 0
            for b in range(nb):
                if _gruppe(bs[b]) == g and K[i, b] > 0:
                    tot += bc[b]
                    nbl += 1
                    maxK = max(maxK, K[i, b])
            if nbl == 0:
                continue
            d = np.empty(tot)
            bi = np.empty(tot, np.int64)
            sl = np.empty(tot, np.int64)
            Kb = np.empty(nbl, np.int64)
            mb = np.empty(nbl, np.int64)
            sz = np.zeros((nbl, maxK), np.int64)
            c = 0
            lb = 0
            for b in range(nb):
                if _gruppe(bs[b]) != g or K[i, b] == 0:
                    continue
                Kb[lb] = K[i, b]
                mb[lb] = min(bm[b], K[i, b])
                for s in range(K[i, b]):
                    sz[lb, s] = ssz[b, s]
                for t in range(bc[b]):
                    j = bl[b, t]
                    d[c] = De[i, j] if g == 0 else Da[i, j]
                    bi[c] = lb
                    sl[c] = bsl[b, t]
                    c += 1
                lb += 1
            if mc:
                val = _eln_mc(d, bi, sl, Kb, mb, kn, ndraw)
            else:
                val = _eln_eksakt(d, bi, sl, Kb, mb, sz, C)
            if g == 0:
                E[i] = val
            elif g == 1:
                LF[i] = val
            else:
                LE[i] = val
        # steg 6: veksten mot stolen
        if not ddm[i]:
            continue
        nF = 0
        nE = 0
        for b in range(nb):
            if bs[b] == 3:
                nF += K[i, b]
            if bs[b] == 4:
                nE += K[i, b]
        if nF == 0 or nE == 0:
            continue
        for kk in range(kd):
            cvec[kk] = 0.0
        nsb = 0
        for b in range(nb):
            if bs[b] <= 2 and K[i, b] > 0:
                for kk in range(kd):
                    cb[kk] = 0.0
                for t in range(bc[b]):
                    j = bl[b, t]
                    w = 1.0 / (K[i, b] * ssz[b, bsl[b, t]])
                    for kk in range(kd):
                        cb[kk] += w * X[j, kk]
                for kk in range(kd):
                    cvec[kk] += cb[kk]
                nsb += 1
        if nsb == 0:
            continue
        r = 0.0
        for kk in range(kd):
            cvec[kk] /= nsb
            v[kk] = X[i, kk] - cvec[kk]
            r += v[kk] * v[kk]
        r = math.sqrt(r)
        if r <= 0.0:
            continue
        for kk in range(kd):
            v[kk] /= r
        sval = np.full(3, np.nan)
        for h in range(3):
            sd = 3 + h
            nbs = 0
            for b in range(nb):
                if bs[b] == sd and K[i, b] > 0:
                    nbs += 1
            nbuf[h] = 0
            if nbs == 0:
                continue
            for b in range(nb):
                if bs[b] != sd or K[i, b] == 0:
                    continue
                for t in range(bc[b]):
                    j = bl[b, t]
                    p = 0.0
                    for kk in range(kd):
                        p += (X[j, kk] - cvec[kk]) * v[kk]
                    pbuf[h, nbuf[h]] = p
                    wbuf[h, nbuf[h]] = 1.0 / (nbs * K[i, b] * ssz[b, bsl[b, t]])
                    nbuf[h] += 1
            pp = pbuf[h, :nbuf[h]]
            ww = wbuf[h, :nbuf[h]]
            med = _wmed(pp, ww)
            sval[h] = _wmed(np.abs(pp - med), ww)
        sF = sval[0]
        sE = sval[1]
        sFF = sval[2]
        for fi in range(nf):
            f = fracs[fi]
            sb = 0.5 * (sF + sE)
            if sb > 0.0:
                DD[i, fi] = _net(pbuf[1], wbuf[1], nbuf[1], f * r * sE / sb) - _net(pbuf[0], wbuf[0], nbuf[0], f * r * sF / sb)
            if nbuf[2] > 0:
                sb2 = 0.5 * (sF + sFF)
                if sb2 > 0.0:
                    DDF[i, fi] = _net(pbuf[0], wbuf[0], nbuf[0], f * r * sF / sb2) - _net(pbuf[2], wbuf[2], nbuf[2], f * r * sFF / sb2)
        DDX[i] = _net(pbuf[1], wbuf[1], nbuf[1], 0.5 * r) - _net(pbuf[0], wbuf[0], nbuf[0], 0.5 * r)
    return E, LF, LE, K, DD, DDF, DDX


C_TAB = _binom(2200, 6)


# ------------------------------------------------------------------ rom, avstand og kontekst
def rom(idx, kanal=(0, 1, 2, 3), k=15, klipp=False):
    """Steg 1: P = pca_rom(trekk[:, :, 2:125] flata ut, k), innan museum."""
    M = D["trekk"][idx][:, list(kanal), 2:125].reshape(len(idx), -1).astype(float)
    if klipp:
        sd = M.std(0)
        ok = sd > 1e-6
        M = np.clip((M[:, ok] - M[:, ok].mean(0)) / sd[ok], -3, 3)
    return fp.pca_rom(M, k)


def avstand(X):
    """Euklidsk avstand; avstandar under 1-prosentilen av alle paravstandar blir sette til han."""
    A = cdist(X, X)
    lo = np.percentile(A[np.triu_indices(len(X), 1)], 1)
    return np.maximum(A, max(lo, 1e-9))


def ekskl(suite, pk, nk, tg=None, med_prod=True):
    E = suite[:, None] == suite[None, :]
    if med_prod:
        E |= (pk[:, None] == pk[None, :]) & (pk[:, None] != "")
        E |= (nk[:, None] == nk[None, :]) & (nk[:, None] != "")
    if tg is not None:
        E |= tg[:, None] != tg[None, :]
    return E


def lag_ctx(X, suite, pk, nk, mus, gid, Xe=None, tg=None, med_prod=True, grp=None, suite_g=None):
    _, sl = np.unique(suite, return_inverse=True)
    c = dict(n=len(X), X=np.ascontiguousarray(X, float), Da=avstand(X), suite=sl.astype(np.int64), mus=mus, gid=gid,
             suite_g=suite if suite_g is None else suite_g)
    c["De"] = c["Da"] if Xe is None else avstand(Xe)
    c["tiekey"] = np.random.default_rng(FROE).random(sl.max() + 1)
    c["grp"] = np.zeros(len(X), np.int64) if grp is None else grp.astype(np.int64)
    c["excl"] = ekskl(suite, pk, nk, tg, med_prod)
    return c


def ctx_ramme(mu, X=None, Xe=None, **kw):
    idx = np.where(MUS == mu)[0]
    if X is None:
        X = rom(idx)
    return lag_ctx(X, SUITE[idx], PK[idx], NK[idx], MUKODE[idx], idx, Xe=Xe, **kw)


def _kmin(sp, regel):
    return np.where(sp[0] != FF, sp[3], 0).astype(np.int64) if regel == "hovud" else np.zeros(len(sp[0]), np.int64)


def kjoer1(c, mid, maal, lev, sp, regel="hovud", ddm=None, berre_dd=False, snu=False, kn=1, mc=False):
    """Éi køyring av kjernen. ddm: kvar steg 6 skal reknast."""
    n = c["n"]
    ddm = np.zeros(n, bool) if ddm is None else np.asarray(ddm, bool)
    E, LF, LE, K, DD, DDF, DDX = _kjerne(c["De"], c["Da"], c["X"], np.asarray(mid, float), c["suite"], c["grp"], c["tiekey"],
                                         c["excl"], np.asarray(maal, bool), np.asarray(lev, bool), ddm, berre_dd, _kmin(sp, regel),
                                         sp[0], sp[1], sp[2], sp[3], sp[4], snu, kn, mc, N_MC, FROE, FRACS, C_TAB)
    return dict(E=E, LF=LF, LE=LE, A=LF - LE, K=K, DD=DD, DDF=DDF, DDX=DDX, ddr=ddm & np.asarray(maal, bool))


def treng_dd(c, R, mid, aar, til, sp, regel, kand, lev, ekstra=None):
    """Steg 6 trengst for dei mest einslege (q >= 0,7 dekkjer 10, 20 og 30 %) som har alle tre mengdene, og for ekstra."""
    ok, ff = maalmaske(R, aar, til, sp, regel, kand)
    ok &= lev
    q = np.full(c["n"], np.nan)
    k = np.where(ok)[0]
    q[k] = rang_q(celle(c["mus"][k], np.asarray(mid)[k]), R["E"][k])
    t = ok & (q >= 0.7 - 1e-9)
    if ekstra is not None:
        t |= ekstra & ok
    return t


def fyll_dd(c, R, mid, lev, sp, treng, kw):
    need = treng & ~R["ddr"]
    if need.any():
        Rn = kjoer1(c, mid, need, lev, sp, "alle", ddm=need, berre_dd=True, **kw)
        for k in ("DD", "DDF", "DDX"):
            R[k][need] = Rn[k][need]
        R["ddr"] = R["ddr"] | need
    return R


def kjoer(c, mid, aar, til, regel="hovud", lev=None, sp=HOVUD, kand=None, ekstra_dd=None, maal=None, kw=None):
    """Heile kjeda i eitt museum: einsemd og pil for målstolane, deretter steg 6 der det trengst."""
    kw = kw or {}
    lev = np.ones(c["n"], bool) if lev is None else lev
    if maal is None:
        maal = lev.copy()
        if regel == "hovud":
            maal &= (til - aar) <= 10
        if kand is not None:
            maal &= kand
    R = kjoer1(c, mid, maal, lev, sp, regel, **kw)
    return fyll_dd(c, R, mid, lev, sp, treng_dd(c, R, mid, aar, til, sp, regel, kand, lev, ekstra_dd), kw)


def maalmaske(R, aar, til, sp, regel, kand=None):
    """-> (målstolar, målstolar som har alle tre mengdene). regel: hovud (smal datering og minst m suitar i kvar bolk
    og kvar halvdel av samtida), alle (alle stolar med avstand på begge sider), gjeven (kand, med avstand på begge sider)."""
    bs, bm = sp[0], sp[3]
    fin = np.isfinite(R["E"]) & np.isfinite(R["A"])
    ffb = bs == FF
    if regel == "hovud":
        krav = bs != FF
        ok = fin & np.all(R["K"][:, krav] >= bm[krav], axis=1) & ((til - aar) <= 10)
        if kand is not None:
            ok &= kand
        return ok, ok & np.all(R["K"][:, ffb] >= bm[ffb], axis=1)
    ok = fin if kand is None else fin & kand
    return ok, ok & np.all(R["K"][:, ffb] >= 1, axis=1)


def celle(mus, mid):
    return mus * 100 + np.floor(np.clip(mid, 1550, 1999.5) / 50).astype(int)


def rang_q(cell, e):
    q = np.full(len(e), np.nan)
    for c in np.unique(cell):
        k = np.where(cell == c)[0]
        if len(k) >= 2:
            q[k] = (stats.rankdata(e[k]) - 1) / (len(k) - 1)
    return q


def tabell(deler):
    """deler: liste av (R, c, mid, ok, ff). -> tabell over målstolane, samla over musea."""
    T = {k: [] for k in ("gid", "mus", "mid", "e", "a", "lf", "le", "DD", "DDF", "DDX", "ff", "suite")}
    for R, c, mid, ok, ff in deler:
        k = np.where(ok)[0]
        T["gid"].append(c["gid"][k]); T["mus"].append(c["mus"][k]); T["mid"].append(np.asarray(mid)[k])
        T["e"].append(R["E"][k]); T["a"].append(R["A"][k]); T["lf"].append(R["LF"][k]); T["le"].append(R["LE"][k])
        T["DD"].append(R["DD"][k]); T["DDF"].append(R["DDF"][k]); T["DDX"].append(R["DDX"][k]); T["ff"].append(ff[k])
        T["suite"].append(c["suite_g"][k])
    T = {k: np.concatenate(v) for k, v in T.items()}
    T["cell"] = celle(T["mus"], T["mid"])
    T["q"] = rang_q(T["cell"], T["e"])
    return T


def deltabell(T, sel):
    U = {k: v[sel] for k, v in T.items()}
    U["q"] = rang_q(U["cell"], U["e"])
    return U


# ------------------------------------------------------------------ andre steget: theta, DD og DD minus DD_før
def fe_theta(W, q, a, cell, sel, X=None):
    """Steg 5: stigninga av a mot q med faste effektar for museum gonger bolk (W: vekter, B x n). X: kovariatar."""
    ok = sel & np.isfinite(q) & np.isfinite(a)
    if X is not None:
        ok &= np.all(np.isfinite(X), axis=1)
    if ok.sum() < 3:
        return np.full(W.shape[0], np.nan)
    W, q, a, cell = W[:, ok], q[ok], a[ok], cell[ok]
    u, ci = np.unique(cell, return_inverse=True)
    I = np.zeros((len(q), len(u)))
    I[np.arange(len(q)), ci] = 1.0
    sw = W @ I

    def dm(x):
        s = (W * x) @ I
        mu = np.divide(s, sw, out=np.zeros_like(s), where=sw > 0)
        return x[None, :] - mu[:, ci]
    qt, at = dm(q), dm(a)
    if X is None:
        num, den = (W * qt * at).sum(1), (W * qt * qt).sum(1)
        return np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)
    X = X[ok]
    Xt = [dm(X[:, j]) for j in range(X.shape[1])]
    ut = np.full(W.shape[0], np.nan)
    for b in range(W.shape[0]):
        Z = np.column_stack([qt[b]] + [x[b] for x in Xt])
        w = W[b]
        A = Z.T @ (Z * w[:, None])
        try:
            ut[b] = np.linalg.lstsq(A, Z.T @ (w * at[b]), rcond=None)[0][0]
        except np.linalg.LinAlgError:
            pass
    return ut


def wmean(W, x, sel):
    ok = sel & np.isfinite(x)
    sw = W[:, ok].sum(1)
    return np.where(sw > 0, (W[:, ok] * x[ok]).sum(1) / np.where(sw > 0, sw, 1), np.nan)


def hovudstat(T, W=None, del_=0.2, fi=0, nivaa=("samla", "VA", "NM"), epokar=False, kvint=False):
    W = np.ones((1, len(T["a"]))) if W is None else W
    ein = T["q"] >= 1 - del_ - 1e-9
    ut = {}
    alle = np.ones(len(T["a"]), bool)
    sels = {"samla": alle, "VA": T["mus"] == 0, "NM": T["mus"] == 1, "RM": T["mus"] == 2}
    ep = {"": alle}
    if epokar:
        ep = {"": alle, "foer1850.": T["mid"] < 1850, "fraa1850.": T["mid"] >= 1850}
    for nm in nivaa:
        for epn, es in ep.items():
            s = sels[nm] & es
            ut[nm + "." + epn + "theta"] = fe_theta(W, T["q"], T["a"], T["cell"], s)
            s2 = s & ein & T["ff"]
            ut[nm + "." + epn + "dd"] = wmean(W, T["DD"][:, fi], s2)
            ut[nm + "." + epn + "dd_minus_ddfoer"] = wmean(W, T["DD"][:, fi] - T["DDF"][:, fi], s2)
            ut[nm + "." + epn + "ddfoer"] = wmean(W, T["DDF"][:, fi], s2)
            ut[nm + "." + epn + "dd_fast"] = wmean(W, T["DDX"], s2)
            ut[nm + "." + epn + "middel_a"] = wmean(W, T["a"], s)
            if kvint:
                for k in range(5):
                    sk = s & (T["q"] >= k / 5 - 1e-9) & ((T["q"] < (k + 1) / 5 - 1e-9) | (k == 4))
                    ut[nm + "." + epn + "kvint%d" % k] = wmean(W, T["a"], sk)
        if epokar:
            for x in ("theta", "dd", "dd_minus_ddfoer"):
                ut[nm + ".skilnad_epoke." + x] = ut[nm + ".fraa1850." + x] - ut[nm + ".foer1850." + x]
    return ut


def boot_vekter(suite, B, rng, bruk_fp=False, strata=None):
    """Suiteboot per museum (F3): heile suitar blir trekte, kvart museum for seg, så talet på suitar i kvart museum står fast."""
    n = len(suite)
    strata = np.zeros(n, int) if strata is None else np.asarray(strata)
    grupper = [np.where(strata == s)[0] for s in np.unique(strata)]
    W = np.zeros((B, n))
    if bruk_fp:
        for b in range(B):
            for k in grupper:
                W[b] += np.bincount(k[fp.suiteboot(suite[k], rng)], minlength=n)
        return W
    inv_g = [np.unique(suite[k], return_inverse=True)[1] for k in grupper]
    for b in range(B):
        for k, inv in zip(grupper, inv_g):
            nu = inv.max() + 1
            W[b, k] = np.bincount(rng.integers(0, nu, nu), minlength=nu)[inv]
    return W


# ------------------------------------------------------------------ køyring av heile kjeda med jackknife og suiteboot
class Kjede:
    """Éi køyring av estimanden over eitt eller fleire museum, med jackknife over 25-årsbolkar og suiteboot."""

    def __init__(self, cs, mids, aars, tils, sp=HOVUD, regel="hovud", levs=None, kands=None, kw=None, ekstra_dd=None):
        self.cs, self.mids, self.aars, self.tils, self.sp, self.regel = cs, mids, aars, tils, sp, regel
        self.levs = levs if levs is not None else [np.ones(c["n"], bool) for c in cs]
        self.kands = kands if kands is not None else [None] * len(cs)
        self.kw = kw or {}
        self.Rs = [kjoer(c, self.mids[m], self.aars[m], self.tils[m], regel, self.levs[m], sp, self.kands[m],
                         None if ekstra_dd is None else ekstra_dd[m], kw=self.kw) for m, c in enumerate(cs)]
        self.T = self.tabell(self.Rs, self.levs)

    def _maal(self, m, lev):
        aar, til = self.aars[m], self.tils[m]
        k = lev.copy()
        if self.regel == "hovud":
            k &= (til - aar) <= 10
        if self.kands[m] is not None:
            k &= self.kands[m]
        return k

    def _kjoer(self, m, lev, maal):
        c, mid = self.cs[m], self.mids[m]
        R2 = {k: v.copy() for k, v in self.Rs[m].items()}
        if maal.any():
            Rn = kjoer1(c, mid, maal, lev, self.sp, self.regel, **self.kw)
            for k in ("E", "LF", "LE", "A", "K"):
                R2[k][maal] = Rn[k][maal]
            for k in ("DD", "DDF", "DDX"):
                R2[k][maal] = np.nan
            R2["ddr"] = R2["ddr"] & ~maal
        treng = treng_dd(c, R2, mid, self.aars[m], self.tils[m], self.sp, self.regel, self.kands[m], lev)
        return fyll_dd(c, R2, mid, lev, self.sp, treng, self.kw)

    def tabell(self, Rs, levs):
        deler = []
        for m, R in enumerate(Rs):
            ok, ff = maalmaske(R, self.aars[m], self.tils[m], self.sp, self.regel, self.kands[m])
            ok &= levs[m]
            deler.append((R, self.cs[m], self.mids[m], ok, ff & ok))
        return tabell(deler)

    def jackknife(self, statfn):
        """Éin 25-årsbolk i eitt museum ute om gongen, både som målstolar og som naboar."""
        reach = float(np.max(self.sp[2])) + 0.5
        rep = []
        for m, c in enumerate(self.cs):
            mid, lev0 = self.mids[m], self.levs[m]
            b25 = np.floor(mid / 25)
            for g in np.unique(b25[lev0]):
                ut = (b25 == g) & lev0
                lev = lev0 & ~ut
                dmin = np.min(np.abs(mid[:, None] - mid[ut][None, :]), axis=1)
                aff = (dmin < reach) & self._maal(m, lev)
                R2 = self._kjoer(m, lev, aff)
                Rs = list(self.Rs)
                Rs[m] = R2
                levs = list(self.levs)
                levs[m] = lev
                rep.append((m, statfn(self.tabell(Rs, levs))))
        return rep

    def intervall(self, statfn, B, rng, bruk_fp=False, jk=True):
        est = {k: float(v[0]) for k, v in statfn(self.T).items()}
        W = boot_vekter(self.T["suite"], B, rng, bruk_fp, strata=self.T["mus"])
        bt = statfn(self.T, W)
        rep = self.jackknife(statfn) if jk else []
        ut = {}
        for k, v in est.items():
            mu = {"VA": 0, "NM": 1, "RM": 2}.get(k.split(".")[0])
            vals = np.array([float(s[k][0]) for m, s in rep if mu is None or m == mu])
            vals = vals[np.isfinite(vals)]
            r = {"verdi": v}
            b = bt[k][np.isfinite(bt[k])]
            for niv, nn in ((0.95, "95"), (0.90, "90")):
                kb = [float(np.quantile(b, (1 - niv) / 2)), float(np.quantile(b, 1 - (1 - niv) / 2))] if len(b) > 10 else [np.nan, np.nan]
                if len(vals) >= 3 and np.isfinite(v):
                    G = len(vals)
                    se = math.sqrt((G - 1) / G * np.sum((vals - vals.mean()) ** 2))
                    t = stats.t.ppf(1 - (1 - niv) / 2, G - 1)
                    kj = [v - t * se, v + t * se]
                else:
                    kj = [np.nan, np.nan]
                r["ki%s_jackknife" % nn] = kj
                r["ki%s_suiteboot" % nn] = kb
                bj = kj[1] - kj[0] if np.isfinite(kj[0]) else -1
                bb = kb[1] - kb[0] if np.isfinite(kb[0]) else -1
                r["ki" + nn] = kj if bj >= bb else kb
            r["bolkar_jackknife"] = int(len(vals))
            ut[k] = r
        return ut


# ------------------------------------------------------------------ permutasjon, planting og feller
SFIRST = np.array([np.where(SUITE == s)[0][0] for s in range(SUITE.max() + 1)])


def perm_aar(rng, strata_suite):
    """Placebo: aar og til permuterte mellom heile suitar innan strata. Kvar suite får datoane til første stol i ein annan suite."""
    p = fp.perm_innan(np.arange(len(SFIRST)), strata_suite, rng)
    src = SFIRST[p][SUITE]
    return AAR[src].copy(), TIL[src].copy()


STRATA_MUS = MUS[SFIRST]
STRATA_TYPE = np.array([m + "|" + t for m, t in zip(MUS[SFIRST], D["type"][SFIRST])])


def plant_datoar(rng, lead, aar, til, suite=None, mus=None, museum=None, berre=None, share=0.1):
    """Planta forsprang: 10 % av suitane, lagdelt på museum gonger bolk, flytte lead år (negativ: tidlegare).
    Heile suitar blir flytte, aar og til saman."""
    suite = SUITE if suite is None else suite
    mus = MUS if mus is None else mus
    u, first, inv = np.unique(suite, return_index=True, return_inverse=True)
    bolk = (np.clip(aar, 1550, 1999) // 50).astype(int)
    st = np.array([str(mus[f]) + "|%d" % bolk[f] for f in first])
    ok = np.ones(len(u), bool)
    if museum is not None:
        ok &= mus[first] == museum
    if berre is not None:
        ok &= berre[first]
    valt = np.zeros(len(u), bool)
    for s in np.unique(st[ok]):
        ks = np.where((st == s) & ok)[0]
        x = share * len(ks)
        k = int(math.floor(x)) + int(rng.random() < x - math.floor(x))
        if k:
            valt[rng.choice(ks, k, replace=False)] = True
    pl = valt[inv]
    return aar + lead * pl, til + lead * pl, pl


def gp_langs(mid, sigma2, rng, skala=40.0):
    """Stasjonær gaussisk prosess i tid, korrelasjon exp(-avstand i år / skala). Reversibel: ingen retning."""
    u, inv = np.unique(mid, return_inverse=True)
    Kc = sigma2 * np.exp(-np.abs(u[:, None] - u[None, :]) / skala) + 1e-9 * sigma2 * np.eye(len(u))
    L = np.linalg.cholesky(Kc)
    return (L @ rng.standard_normal(len(u)))[inv]


# ------------------------------------------------------------------ hjelparar
def js(x):
    if isinstance(x, dict):
        return {str(k): js(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [js(v) for v in x]
    if isinstance(x, np.ndarray):
        return [js(v) for v in x.tolist()]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        x = float(x)
        return None if not np.isfinite(x) else round(x, 6)
    return x


def oppsummer(vals):
    v = np.asarray(vals, float)
    v = v[np.isfinite(v)]
    if len(v) < 2:
        return {"n": int(len(v))}
    return {"n": int(len(v)), "middel": float(v.mean()), "sd": float(v.std(ddof=1)), "median": float(np.median(v)),
            "p2_5": float(np.quantile(v, 0.025)), "p97_5": float(np.quantile(v, 0.975))}


RUNDT_NULL = 0.25    # «rundt null»: |middel| høgst 0,25 standardavvik av fordelinga


def rundt_null(vals):
    v = np.asarray(vals, float)
    v = v[np.isfinite(v)]
    return bool(len(v) > 2 and abs(v.mean()) <= RUNDT_NULL * v.std(ddof=1))


def suite_ki(x, s, niv=0.95):
    """Middel og t-intervall over suitemiddel (suiten er eininga)."""
    ok = np.isfinite(x)
    x, s = x[ok], s[ok]
    if len(x) == 0:
        return np.nan, [np.nan, np.nan], 0
    u, inv = np.unique(s, return_inverse=True)
    m = np.bincount(inv, weights=x) / np.bincount(inv)
    if len(m) < 2:
        return float(m.mean()), [np.nan, np.nan], int(len(m))
    se = m.std(ddof=1) / math.sqrt(len(m))
    t = stats.t.ppf(1 - (1 - niv) / 2, len(m) - 1)
    return float(m.mean()), [float(m.mean() - t * se), float(m.mean() + t * se)], int(len(m))


def bolk25(mid):
    return (np.floor(np.asarray(mid, float) / 25) * 25).astype(int)


def tel(mus, mid):
    ut = {}
    for mu in np.unique(mus):
        k = mus == mu
        b, n = np.unique(bolk25(mid[k]), return_counts=True)
        ut[str(mu)] = {"i_alt": int(k.sum()), "per_25aar": {str(x): int(y) for x, y in zip(b, n)}}
    return ut


MUNAMN = np.array(["VA", "NM", "RM"])


class Oppsett:
    def __init__(self):
        self.cs = [ctx_ramme("VA"), ctx_ramme("NM")]
        self.IX = [c["gid"] for c in self.cs]

    def kjede(self, aar, til, mus=(0, 1), lev=None, ekstra=None, kand=None, cs=None, ix=None, **kw):
        cs = [self.cs[m] for m in mus] if cs is None else cs
        ix = [self.IX[m] for m in mus] if ix is None else ix
        mid = (aar + til) / 2
        return Kjede(cs, [mid[i] for i in ix], [aar[i] for i in ix], [til[i] for i in ix],
                     levs=None if lev is None else [lev[i].copy() for i in ix],
                     kands=None if kand is None else [kand[i] for i in ix],
                     ekstra_dd=None if ekstra is None else [ekstra[i] for i in ix], **kw)


def maske_fraa(T, n=N):
    m = np.zeros(n, bool)
    m[T["gid"]] = True
    return m


# ------------------------------------------------------------------ teljing: stolar utanfor ramma, retta sluttår
def utanfor_ramma():
    rein = list(csv.DictReader(open(os.path.join(HER, "data", "stolar_reinsa.csv"), encoding="utf-8-sig")))
    maal = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "mesh_maal.csv"), encoding="utf-8"))}
    z = np.load(os.path.join(HER, "data", "mesh_silhuettar.npz"))
    side = dict(zip(z["ids"], z["side"]))
    front = dict(zip(z["ids"], z["front"]))
    ut = {}
    for r in rein:
        i, m = r["id"], maal.get(r["id"])
        if r["vaksenstol"] != "1" or i not in side or not m or not r["H"] or not r["B"] or not r["D"]:
            continue
        if set(filter(None, (m.get("flagg") or "").split(";"))) & {"opp_ikkje_y", "opp_ned?", "silhuett_klipt"}:
            kat = "uviss_orientering"
        else:
            H, B, Dd = float(r["H"]), float(r["B"]), float(r["D"])
            k0, k1, _, r1 = fp.ramme._utstr(np.unpackbits(side[i], axis=-1))
            f0, f1, _, _ = fp.ramme._utstr(np.unpackbits(front[i], axis=-1))
            if (k1 - k0) > 1.5 * Dd + 10 or (f1 - f0) > 1.5 * B + 10 or abs(r1 + 1 - H) > 6:
                kat = "skalasjekk"
            else:
                continue
        a = float(r["aar_fraa"]) if r["aar_fraa"] else np.nan
        b = "utan_aar"
        if np.isfinite(a) and a >= 1000:
            t = float(r["aar_til"]) if r["aar_til"] else 0.0
            b = str(bolk25((a + max(t, a)) / 2))
        d = ut.setdefault(r["museum"], {}).setdefault(b, {"uviss_orientering": 0, "skalasjekk": 0})
        d[kat] += 1
    return ut


def retta_sluttaar():
    """F1: stolar der sluttåret er sett lik startåret, delt på årsak (aar_til under aar, eller aar_til manglar)."""
    rein = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "stolar_reinsa.csv"), encoding="utf-8-sig"))}
    ut = {}
    for i, mu in zip(D["id"], MUS):
        r = rein.get(i)
        if r is None:
            continue
        a = float(r["aar_fraa"])
        t = float(r["aar_til"]) if r["aar_til"] else np.nan
        d = ut.setdefault(str(mu), {"til_under_aar": 0, "til_manglar": 0})
        if not np.isfinite(t):
            d["til_manglar"] += 1
        elif t < a:
            d["til_under_aar"] += 1
    return ut


def instrument():
    """Steg 7: g = |ln(1 + avvik_b)| + |ln(1 + avvik_d)| og flagga frå mesh_maal.csv, kopla på id."""
    mm = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "mesh_maal.csv"), encoding="utf-8"))}
    G = np.full((N, 5), np.nan)
    for k, i in enumerate(D["id"]):
        r = mm.get(i)
        if r is None:
            continue
        try:
            g = abs(math.log(1 + float(r["avvik_b"]))) + abs(math.log(1 + float(r["avvik_d"])))
        except (ValueError, TypeError):
            g = np.nan
        fl = set(filter(None, (r.get("flagg") or "").split(";")))
        G[k] = [g] + [float(f in fl) for f in ("B_D_bytt?", "symmetri_uklar", "opp_usikker", "fleire_toppar")]
    return G


# ------------------------------------------------------------------ katalogversjonen (steg 8)
def _uf(n, par):
    forelder = list(range(n))

    def finn(a):
        while forelder[a] != a:
            forelder[a] = forelder[forelder[a]]
            a = forelder[a]
        return a
    for a, b in par:
        forelder[finn(a)] = finn(b)
    return np.array([finn(k) for k in range(n)])


def rijks_meta():
    ut = {}
    forste = lambda x: (x[0] if x else {}) if isinstance(x, list) else (x or {})
    for l in open(os.path.join(HER, "forsegla", "rijks_raa.jsonl"), encoding="utf-8"):
        p = json.loads(l)
        rec = p.get("record") or {}
        pb = forste(rec.get("produced_by"))
        ts = forste(pb.get("timespan"))
        m = re.match(r"\d{4}", ts.get("end_of_the_end") or "")
        makers = []
        for part in [pb] + list(pb.get("part") or []):
            if not isinstance(part, dict):
                continue
            for cb in (part.get("carried_out_by") or []):
                if not isinstance(cb, dict):
                    continue
                nott = cb.get("notation") or []
                for nn in (nott if isinstance(nott, list) else [nott]):
                    if isinstance(nn, dict) and nn.get("@language") == "en":
                        makers.append(nn.get("@value") or "")
                    elif isinstance(nn, str):
                        makers.append(nn)
        ut[p["id"].rsplit("/", 1)[-1]] = (int(m.group(0)) if m else None, makers[0] if makers else "")
    return ut


def katalogdata():
    """Alle stolar i analyse/data/tre_museum.csv med år, retta sluttår, utan kopierte målpostar; suitar og produsentar."""
    ST = {r["Objekt-ID"]: r for r in csv.DictReader(open(os.path.join(ROT, "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline=""))}
    rein = list(csv.DictReader(open(os.path.join(HER, "data", "stolar_reinsa.csv"), encoding="utf-8-sig")))
    reinid = {r["id"]: r for r in rein}
    grupper = {}
    for r in rein:
        if r["vaksenstol"] == "1" and r["maal_ok"] == "1":
            grupper.setdefault((r["museum"], r["H"], r["B"], r["D"]), []).append(r)
    kopi = set()
    for g in grupper.values():
        aar_g = [float(r["aar_fraa"]) for r in g if r["aar_fraa"] and float(r["aar_fraa"]) >= 1000]
        namn_g = {re.sub(r"\s*\(.*?\)\s*", " ", ST.get(r["id"], {}).get("Namn", "") or "").strip().lower() for r in g}
        if len(g) >= 2 and ((aar_g and max(aar_g) - min(aar_g) > 25) or len(namn_g) >= 3):
            kopi |= {r["id"] for r in g}
    rij = rijks_meta()
    rader = {"VA": [], "NM": [], "RM": []}
    tel_ut = {"VA": {"kopiert_maalpost": 0, "utan_aar": 0}, "NM": {"kopiert_maalpost": 0, "utan_aar": 0},
              "RM": {"utan_aar": 0, "utan_sluttaar": 0}}
    for r in csv.DictReader(open(os.path.join(HER, "data", "tre_museum.csv"), encoding="utf-8-sig")):
        mu = r["museum"]
        if mu in ("VA", "NM"):
            rr = reinid.get(r["id"])
            if rr is None or not rr["aar_fraa"] or float(rr["aar_fraa"]) < 1000:
                tel_ut[mu]["utan_aar"] += 1
                continue
            if r["id"] in kopi:
                tel_ut[mu]["kopiert_maalpost"] += 1
                continue
            a = int(float(rr["aar_fraa"]))
            t = max(int(float(rr["aar_til"])) if rr["aar_til"] else 0, a)
            s = ST.get(r["id"], {})
            rader[mu].append(dict(id=r["id"], aar=a, til=t, H=float(r["H"]), B=float(r["B"]), D=float(r["D"]),
                                  pk=pkey(s.get("Produsent")), nk=nkey(s.get("Namn")), hbd=(r["H"], r["B"], r["D"])))
        else:
            if not r["aar"]:
                tel_ut[mu]["utan_aar"] += 1
                continue
            a = int(r["aar"])
            end, maker = rij.get(r["id"], (None, ""))
            if end is None:
                tel_ut[mu]["utan_sluttaar"] += 1
            rader[mu].append(dict(id=r["id"], aar=a, til=max(end or a, a), H=float(r["H"]), B=float(r["B"]), D=float(r["D"]),
                                  pk=pkey(maker), nk="", hbd=None))
    ut = {}
    for mu, rr in rader.items():
        n = len(rr)
        par = []
        if mu in ("VA", "NM"):
            nok = {}
            for k, r in enumerate(rr):
                st = fp.ramme._RE_NMKDEL.sub(r"\1", fp.ramme._RE_STAMME.sub("", r["id"]))
                for nk_ in (("s", st), ("m",) + r["hbd"]):
                    if nk_ in nok:
                        par.append((k, nok[nk_]))
                    else:
                        nok[nk_] = k
        else:
            for k in range(n):
                for j in range(k + 1, n):
                    if rr[k]["aar"] == rr[j]["aar"] and abs(rr[k]["H"] - rr[j]["H"]) <= 2 and abs(rr[k]["B"] - rr[j]["B"]) <= 2:
                        par.append((k, j))
        f = lambda x, dt=float: np.array([r[x] for r in rr], dtype=dt)
        ut[mu] = dict(id=np.array([r["id"] for r in rr]), aar=f("aar"), til=f("til"), H=f("H"), B=f("B"), D=f("D"),
                      pk=np.array([r["pk"] for r in rr]), nk=np.array([r["nk"] for r in rr]), suite=_uf(n, par))
    return ut, tel_ut


def ctx_katalog(KD):
    cs = []
    for code, mu in enumerate(("VA", "NM", "RM")):
        r = KD[mu]
        X = np.column_stack([np.log(r["H"]), np.log(r["B"]), np.log(r["D"])])
        X = (X - X.mean(0)) / X.std(0)
        n = len(X)
        cs.append(lag_ctx(X, r["suite"], r["pk"], r["nk"], np.full(n, code), np.arange(n),
                          suite_g=r["suite"] + 1_000_000 * (code + 1)))
    return cs


def kjede_katalog(cs, KD, mus=(0, 1, 2), aar=None, til=None, ekstra=None):
    mu_n = ("VA", "NM", "RM")
    aars = [KD[mu_n[m]]["aar"] if aar is None else aar for m in mus]
    tils = [KD[mu_n[m]]["til"] if til is None else til for m in mus]
    return Kjede([cs[m] for m in mus], [(a + t) / 2 for a, t in zip(aars, tils)], aars, tils,
                 ekstra_dd=None if ekstra is None else [ekstra])


def katalog_kryss_X(mu):
    """Einsemd frå katalogmåla (ln H, ln B, ln D) for stolane i ramma, standardisert innan museum."""
    idx = np.where(MUS == mu)[0]
    X = np.column_stack([np.log(D["H"][idx]), np.log(D["B"][idx]), np.log(D["D"][idx])])
    return (X - X.mean(0)) / X.std(0)


# ------------------------------------------------------------------ planting: vurdering
def vurder(Tb, Tp, pl, lead, sb, mus_namn=("samla", "VA", "NM")):
    """Planta minus dei same stolane urørte, for dei planta stolane som er målstolar i begge køyringane."""
    mb = {g: k for k, g in enumerate(Tb["gid"])}
    mp = {g: k for k, g in enumerate(Tp["gid"])}
    common = [g for g in Tp["gid"][pl[Tp["gid"]]] if g in mb]
    jb = np.array([mb[g] for g in common], int)
    jp = np.array([mp[g] for g in common], int)
    s = Tb["suite"][jb]
    mus = Tb["mus"][jb]
    ep = Tb["mid"][jb] < 1850
    okdd = Tb["ff"][jb] & Tp["ff"][jp]
    da = Tp["a"][jp] - Tb["a"][jb]
    ddd = Tp["DD"][jp, 0] - Tb["DD"][jb, 0]
    dh3 = (Tp["DD"][jp, 0] - Tp["DDF"][jp, 0]) - (Tb["DD"][jb, 0] - Tb["DDF"][jb, 0])
    teikn = 1 if lead < 0 else -1
    ut = {"n_planta_maal": int(len(common))}
    alle = np.ones(len(common), bool)
    subs = {"samla": alle, "VA": mus == 0, "NM": mus == 1, "foer1850": ep, "fraa1850": ~ep}
    for nm, x, okm in (("a", da, alle), ("dd", ddd, okdd), ("h3", dh3, okdd)):
        for sn, sm in subs.items():
            m, ki, ns = suite_ki(x[okm & sm], s[okm & sm])
            funne = bool(np.isfinite(ki[0]) and (ki[0] > 0 if teikn > 0 else ki[1] < 0))
            ut[nm + "." + sn] = {"middel": m, "funne": funne, "rett_teikn": bool(np.isfinite(m) and teikn * m > 0), "suitar": ns}
    sp_ = hovudstat(Tp)
    for nm in mus_namn:
        for x in ("theta", "dd", "dd_minus_ddfoer"):
            k = nm + "." + x
            if k in sb:
                ut["d_" + k] = float(sp_[k][0] - sb[k][0])
    return ut


def samandrag(liste):
    ut = {}
    for k in liste[0]:
        v = [r[k] for r in liste]
        if isinstance(v[0], dict):
            ut[k] = {"del_funne": float(np.mean([x["funne"] for x in v])),
                     "del_rett_teikn": float(np.mean([x["rett_teikn"] for x in v])),
                     "middel": float(np.nanmean([x["middel"] for x in v])) if any(np.isfinite(x["middel"]) for x in v) else None,
                     "suitar_middel": float(np.mean([x["suitar"] for x in v]))}
        else:
            ut[k] = oppsummer(v)
    return ut


def planting(O, base, sb, lead, n, rng, mus=(0, 1), museum=None, berre=None, lev=None, sp=HOVUD, mus_namn=("samla", "VA", "NM")):
    res = []
    for r in range(n):
        aar_p, til_p, pl = plant_datoar(rng, lead, AAR, TIL, museum=museum, berre=berre)
        K = O.kjede(aar_p, til_p, mus=mus, lev=lev, ekstra=pl, sp=sp)
        res.append(vurder(base.T, K.T, pl, lead, sb, mus_namn))
    return samandrag(res)


def planting_katalog(csk, KD, base, sb, lead, n, rng):
    res = []
    r = KD["VA"]
    mus = np.array(["VA"] * len(r["aar"]))
    for _ in range(n):
        aar_p, til_p, pl = plant_datoar(rng, lead, r["aar"], r["til"], suite=r["suite"], mus=mus)
        K = kjede_katalog(csk, KD, mus=(0,), aar=aar_p, til=til_p, ekstra=pl)
        res.append(vurder(base.T, K.T, pl, lead, sb, ("VA",)))
    return samandrag(res)


def stat_kontroll(T, W=None):
    return hovudstat(T, W, epokar=True, kvint=True)


def stat_enkel(T, W=None):
    return hovudstat(T, W)


HOVUDTAL = ("theta", "dd", "dd_minus_ddfoer")


# ------------------------------------------------------------------ --kontroll
def kontroll():
    rng = np.random.default_rng(FROE)
    O = Oppsett()
    ut = {"prove": "P4", "skrive": "2026-11-13", "modus": "kontroll",
          "trekk": {"placebo_0": N_PLACEBO, "placebo_1b": N_PLACEBO, "placebo_2": N_PLACEBO2, "fellene": N_FELLE,
                    "planta_verder_per_forsprang": N_PLANT, "suiteboot_i_felle_a": N_BOOT_FELLE, "suiteboot_ved_opning": N_BOOT,
                    "steg_3": "eksakt forventning over alle trekk; 200 trekk med frø 20261113 som kontroll"}}
    print("Oppsett %.1f s" % (time.time() - T0))

    # (a) teljetabellar. Grunnkøyringane blir rekna, men ingen utfallstal blir skrivne ut.
    alle_dd = np.ones(N, bool)
    BASE = O.kjede(AAR, TIL, ekstra=alle_dd)
    ALLE = O.kjede(AAR, TIL, regel="alle", ekstra=alle_dd)
    WOODK = O.kjede(AAR, TIL, lev=WOOD, ekstra=alle_dd)
    T, TA, TW = BASE.T, ALLE.T, WOODK.T
    dok = ((TIL - AAR) <= 5) & (AAR % 5 != 0)
    tl = {"n_i_ramma": {mu: int((MUS == mu).sum()) for mu in ("VA", "NM")},
          "suitar_i_ramma": {mu: int(len(np.unique(SUITE[MUS == mu]))) for mu in ("VA", "NM")},
          "retta_sluttaar_per_museum": retta_sluttaar(),
          "smalt_daterte_per_museum": {mu: int(((TIL - AAR <= 10) & (MUS == mu)).sum()) for mu in ("VA", "NM")},
          "ramma_per_museum_og_25aar": tel(MUS, MID),
          "maalstolar_hovudkoeyringa": tel(MUNAMN[T["mus"]], T["mid"]),
          "maalstolar_med_alle_tre_mengdene": tel(MUNAMN[T["mus"][T["ff"]]], T["mid"][T["ff"]]),
          "maalstolar_alle": tel(MUNAMN[TA["mus"]], TA["mid"]),
          "maalstolar_wood": tel(MUNAMN[TW["mus"]], TW["mid"]),
          "wood_foer1850_maalstolar": int((TW["mid"] < 1850).sum()),
          "wood_foer1850_dokumentert_datering": int(((TW["mid"] < 1850) & dok[TW["gid"]]).sum()),
          "attopptaking_og_kopi_maalstolar": {"hovud": int(ATTOPP[T["gid"]].sum()), "alle": int(ATTOPP[TA["gid"]].sum())},
          "utanfor_ramma_per_museum_og_25aar": utanfor_ramma(),
          "einslege_20pst_med_alle_tre_mengdene": {mu: int(((T["q"] >= 0.8 - 1e-9) & T["ff"] & (T["mus"] == k)).sum())
                                                   for k, mu in enumerate(("VA", "NM"))}}
    ut["teljing"] = tl
    print("Teljing: målstolar", tl["maalstolar_hovudkoeyringa"]["VA"]["i_alt"], tl["maalstolar_hovudkoeyringa"]["NM"]["i_alt"],
          "| alle", TA["a"].shape[0], "| wood", TW["a"].shape[0], "| dok før 1850", tl["wood_foer1850_dokumentert_datering"],
          "(%.0f s)" % (time.time() - T0))
    sb = {k: v for k, v in hovudstat(T).items()}          # berre til skilnader i plantinga, blir aldri skrive ut
    sbw = {k: v for k, v in hovudstat(TW, epokar=True).items()}

    # kontroll av steg 3: eksakt forventning mot 200 trekk, på år-permuterte data
    ap, tp = perm_aar(rng, STRATA_MUS)
    c = O.cs[0]
    idx = O.IX[0]
    mid_p = ((ap + tp) / 2)[idx]
    maal = (tp - ap)[idx] <= 10
    R1 = kjoer1(c, mid_p, maal, np.ones(c["n"], bool), HOVUD)
    R2 = kjoer1(c, mid_p, maal, np.ones(c["n"], bool), HOVUD, mc=True)
    ok = np.isfinite(R1["A"]) & np.isfinite(R2["A"])
    ut["steg3_eksakt_mot_200_trekk"] = {"n": int(ok.sum()), "korrelasjon_a": float(np.corrcoef(R1["A"][ok], R2["A"][ok])[0, 1]),
                                        "middelskilnad_a": float(np.mean(R1["A"][ok] - R2["A"][ok])),
                                        "korrelasjon_e": float(np.corrcoef(R1["E"][ok], R2["E"][ok])[0, 1]),
                                        "middelskilnad_e": float(np.mean(R1["E"][ok] - R2["E"][ok]))}
    print("Steg 3 eksakt mot 200 trekk:", {k: round(v, 4) for k, v in ut["steg3_eksakt_mot_200_trekk"].items()})

    # (b) placebo 0 og 1b
    for namn, strata in (("placebo_0", STRATA_MUS), ("placebo_1b", STRATA_TYPE)):
        acc = {}
        for r in range(N_PLACEBO):
            ap, tp = perm_aar(rng, strata)
            st = stat_kontroll(O.kjede(ap, tp).T)
            for k, v in st.items():
                acc.setdefault(k, []).append(float(v[0]))
        ut[namn] = {k: oppsummer(v) for k, v in acc.items()}
        ut[namn + "_rundt_null"] = {k: rundt_null(acc[k]) for k in acc if k.split(".")[-1] in HOVUDTAL and "1850" not in k}
        print(namn, "rundt null:", ut[namn + "_rundt_null"], "(%.0f s)" % (time.time() - T0))

    # placebo 2: einsemda permutert innan museum gonger bolk. theta SKAL bli null; middelet av a står urørt.
    acc, ma_ok = {}, True
    for r in range(N_PLACEBO2):
        U = dict(T)
        U["e"] = fp.perm_innan(T["e"], T["cell"], rng)
        U["q"] = rang_q(U["cell"], U["e"])
        st = hovudstat(U)
        ma_ok &= bool(abs(st["samla.middel_a"][0] - sb["samla.middel_a"][0]) < 1e-12)
        for k in ("samla.theta", "VA.theta", "NM.theta"):
            acc.setdefault(k, []).append(float(st[k][0]))
    ut["placebo_2"] = {k: oppsummer(v) for k, v in acc.items()}
    ut["placebo_2_rundt_null"] = {k: rundt_null(v) for k, v in acc.items()}
    ut["placebo_2_middel_a_uroert"] = ma_ok
    print("placebo_2 rundt null:", ut["placebo_2_rundt_null"], "middel a urørt:", ma_ok)

    # placebo 3 (kodekontroll) på år-permuterte data: tida snudd med same frø
    p3 = []
    for r in range(3):
        ap, tp = perm_aar(rng, STRATA_MUS)
        K1 = O.kjede(ap, tp, ekstra=alle_dd)
        K2 = O.kjede(3549.5 - tp, 3549.5 - ap, ekstra=alle_dd, kw={"snu": True})
        s1, s2 = hovudstat(K1.T), hovudstat(K2.T)
        m2 = {g: k for k, g in enumerate(K2.T["gid"])}
        j1 = np.array([k for k, g in enumerate(K1.T["gid"]) if g in m2])
        j2 = np.array([m2[g] for g in K1.T["gid"][j1]])
        okd = np.isfinite(K1.T["DD"][j1, 0]) & np.isfinite(K2.T["DD"][j2, 0])
        ein1 = K1.T["q"][j1] >= 0.8 - 1e-9
        p3.append({"same_maalstolar": bool(len(j1) == len(K1.T["gid"]) == len(K2.T["gid"])),
                   "theta_sum": float(s1["samla.theta"][0] + s2["samla.theta"][0]),
                   "maks_a_sum": float(np.max(np.abs(K1.T["a"][j1] + K2.T["a"][j2]))),
                   "maks_e_skilnad": float(np.max(np.abs(K1.T["e"][j1] - K2.T["e"][j2]))),
                   "maks_dd_sum": float(np.max(np.abs(K1.T["DD"][j1][okd] + K2.T["DD"][j2][okd]))),
                   "dd_einslege_sum": float(np.mean(K1.T["DD"][j1][okd & ein1, 0]) + np.mean(K2.T["DD"][j2][okd & ein1, 0]))})
    ut["placebo_3"] = p3
    ut["placebo_3_held"] = bool(all(x["same_maalstolar"] and abs(x["theta_sum"]) < 1e-9 and x["maks_a_sum"] < 1e-9
                                    and x["maks_dd_sum"] < 1e-9 and abs(x["dd_einslege_sum"]) < 1e-9 for x in p3))
    print("placebo_3 held:", ut["placebo_3_held"], p3[0])

    # feller
    sig2 = []
    for m, c in enumerate(O.cs):
        x = c["X"][:, 0]
        b = np.floor(MID[O.IX[m]] / 25)
        ss = sum(((x[b == u] - x[b == u].mean()) ** 2).sum() for u in np.unique(b))
        sig2.append(0.2 * ss / (len(x) - len(np.unique(b))))

    def ctx_ny(c, X):
        c2 = dict(c)
        c2["X"] = np.ascontiguousarray(X)
        c2["Da"] = avstand(X)
        c2["De"] = c2["Da"]
        return c2
    # (a) reversibel prosess på år-permuterte data
    dekk = {nm + "." + x: [] for nm in ("samla", "VA", "NM") for x in HOVUDTAL}
    for r in range(N_FELLE):
        ap, tp = perm_aar(rng, STRATA_MUS)
        mid = (ap + tp) / 2
        cs2 = []
        for m, c in enumerate(O.cs):
            X = c["X"].copy()
            X[:, 0] += gp_langs(mid[O.IX[m]], sig2[m], rng)
            cs2.append(ctx_ny(c, X))
        iv = O.kjede(ap, tp, cs=cs2).intervall(stat_enkel, N_BOOT_FELLE, rng)
        for k in dekk:
            lo, hi = iv[k]["ki95"]
            dekk[k].append(bool(np.isfinite(lo) and lo <= 0 <= hi))
    ut["felle_a_dekning"] = {k: float(np.mean(v)) for k, v in dekk.items()}
    ut["felle_a_varians_gp"] = sig2
    print("felle (a) dekning:", ut["felle_a_dekning"], "(%.0f s)" % (time.time() - T0))
    # (b) rein utviding og (c) målefeil, på år-permuterte data
    for namn in ("felle_b", "felle_c"):
        acc = {}
        for r in range(N_FELLE):
            ap, tp = perm_aar(rng, STRATA_MUS)
            cs2 = []
            for m, c in enumerate(O.cs):
                X = c["X"].copy()
                if namn == "felle_b":
                    cen = X.mean(0)
                    X = cen + (X - cen) * (1 + 0.3 * (ap[O.IX[m]] - 1600) / 400)[:, None]
                else:
                    sel = rng.random(len(X)) < 0.05
                    X[sel] += rng.standard_normal((sel.sum(), X.shape[1])) * 2 * X.std(0)
                cs2.append(ctx_ny(c, X))
            st = stat_enkel(O.kjede(ap, tp, cs=cs2).T)
            for k, v in st.items():
                acc.setdefault(k, []).append(float(v[0]))
        ut[namn] = {k: oppsummer(v) for k, v in acc.items() if k.split(".")[-1] in HOVUDTAL + ("dd_fast",)}
        ut[namn + "_rundt_null"] = {k: rundt_null(v) for k, v in acc.items() if k.split(".")[-1] in HOVUDTAL + ("dd_fast",)}
        print(namn, "rundt null:", ut[namn + "_rundt_null"], "(%.0f s)" % (time.time() - T0))

    # planta verder i dei verkelege dataa (berre treff eller bom og skilnader blir skrivne ut)
    pl = {}
    for lead in (-15, -30, -45, 30):
        pl[str(lead)] = planting(O, BASE, sb, lead, N_PLANT, rng)
        print("planting %+d: funne a/dd/h3 samla" % lead, pl[str(lead)]["a.samla"]["del_funne"], pl[str(lead)]["dd.samla"]["del_funne"],
              pl[str(lead)]["h3.samla"]["del_funne"], "| VA", pl[str(lead)]["a.VA"]["del_funne"], "| NM", pl[str(lead)]["a.NM"]["del_funne"],
              "(%.0f s)" % (time.time() - T0))
    ut["planting"] = pl
    # Nasjonalmuseet åleine
    BNM = O.kjede(AAR, TIL, mus=(1,), ekstra=alle_dd)
    sbn = hovudstat(BNM.T, nivaa=("NM",))
    nm5 = planting(O, BNM, sbn, -30, N_PLANT, rng, mus=(1,), museum="NM", mus_namn=("NM",))
    ut["planting_nm_aaleine_5"] = nm5
    nm_spec = 5
    if nm5["a.NM"]["del_rett_teikn"] < 0.8:
        BNM3 = O.kjede(AAR, TIL, mus=(1,), ekstra=alle_dd, sp=SPEC3)
        nm3 = planting(O, BNM3, hovudstat(BNM3.T, nivaa=("NM",)), -30, N_PLANT, rng, mus=(1,), museum="NM", sp=SPEC3, mus_namn=("NM",))
        ut["planting_nm_aaleine_3"] = nm3
        if nm3["a.NM"]["del_rett_teikn"] >= 0.8:
            nm_spec = 3
    print("NM åleine: rett teikn", nm5["a.NM"]["del_rett_teikn"], "funne", nm5["a.NM"]["del_funne"], "spec", nm_spec)
    # WOOD-køyringa, før og frå 1850
    for lead in (-30, -45):
        ut["planting_wood_%d" % -lead] = planting(O, WOODK, sbw, lead, N_PLANT, rng, lev=WOOD, berre=WOOD)
        w = ut["planting_wood_%d" % -lead]
        print("WOOD %d: funne a før/frå" % -lead, w["a.foer1850"]["del_funne"], w["a.fraa1850"]["del_funne"],
              "dd", w["dd.foer1850"]["del_funne"], w["dd.fraa1850"]["del_funne"], "h3", w["h3.foer1850"]["del_funne"],
              w["h3.fraa1850"]["del_funne"], "(%.0f s)" % (time.time() - T0))
    # katalogversjonen i V&A
    KD, kat_ut = katalogdata()
    csk = ctx_katalog(KD)
    KB = kjede_katalog(csk, KD, mus=(0,), ekstra=np.ones(len(KD["VA"]["aar"]), bool))
    KALL = kjede_katalog(csk, KD)
    ut["teljing"]["katalog"] = {"stolar": {mu: int(len(KD[mu]["aar"])) for mu in ("VA", "NM", "RM")}, "tekne_ut": kat_ut,
                                "maalstolar": tel(MUNAMN[KALL.T["mus"]], KALL.T["mid"])}
    ut["planting_katalog_va_30"] = planting_katalog(csk, KD, KB, hovudstat(KB.T, nivaa=("VA",)), -30, N_PLANT, rng)
    print("katalog VA 30: funne a", ut["planting_katalog_va_30"]["a.VA"]["del_funne"], "(%.0f s)" % (time.time() - T0))

    # omvend kontroll: attopptakingsstilar og kopiar som målstolar (køyringa med alle målstolar) SKAL gje a under null
    sel = ATTOPP[TA["gid"]]
    m, ki, ns = suite_ki(TA["a"][sel], TA["suite"][sel])
    ut["omvend_kontroll"] = {"maalstolar": int(sel.sum()), "suitar": ns, "treff_a_under_null": bool(m < 0),
                             "treff_intervall_under_null": bool(np.isfinite(ki[1]) and ki[1] < 0)}
    print("omvend kontroll:", ut["omvend_kontroll"])

    # ---------------------------------------------------------- frys tersklar, marginar og portar
    def opploysing(namn, sub="samla"):
        for L in (15, 30, 45):
            if pl[str(-L)][namn + "." + sub]["del_funne"] >= 0.8:
                return L
        return None

    def spegel(namn):
        mn, mp = pl["-30"][namn + ".samla"]["middel"], pl["30"][namn + ".samla"]["middel"]
        ok = mn is not None and mp is not None and mn > 0 > mp and 0.5 <= abs(mp) / abs(mn) <= 2.0
        return {"minus30": mn, "pluss30": mp, "held": bool(ok)}
    L = {"theta": opploysing("a"), "dd": opploysing("dd"), "dd_minus_ddfoer": opploysing("h3")}
    sp_ = {"theta": spegel("a"), "dd": spegel("dd"), "dd_minus_ddfoer": spegel("h3")}
    # Terskelen er verknaden av det minste synlege forspranget på a (og DD) for ein stol som har det: om dei mest
    # einslege har forspranget og dei minst einslege ikkje, blir theta denne verdien over heile einsemdskalaen.
    # Verknaden av å plante 10 % av suitane på theta blir meld ved sida (han avheng av kor stor del som blir planta).
    terskel, terskel_alt = {}, {}
    for nm in ("samla", "VA"):
        terskel[nm] = {"theta": pl[str(-L["theta"])]["a." + nm]["middel"] if L["theta"] else None,
                       "dd": pl[str(-L["dd"])]["dd." + nm]["middel"] if L["dd"] else None}
        terskel_alt[nm] = {"theta": pl[str(-L["theta"])]["d_%s.theta" % nm]["middel"] if L["theta"] else None,
                           "dd": pl[str(-L["dd"])]["d_%s.dd" % nm]["middel"] if L["dd"] else None}
    lesande = {"samla": {x: bool(L[x] is not None and sp_[x]["held"]) for x in HOVUDTAL}}
    sub = {"theta": "a", "dd": "dd", "dd_minus_ddfoer": "h3"}
    lesande["VA"] = {x: bool(lesande["samla"][x] and pl[str(-L[x])][sub[x] + ".VA"]["del_funne"] >= 0.8) for x in HOVUDTAL}
    nm_pl = ut["planting_nm_aaleine_3"] if nm_spec == 3 else nm5
    nm_bind = {x: bool(nm_pl[sub[x] + ".NM"]["del_rett_teikn"] >= 0.8) for x in HOVUDTAL}
    portar = {}
    for nm in ("samla", "VA", "NM"):
        portar[nm] = {}
        for x in HOVUDTAL:
            k = nm + "." + x
            p = {"placebo_0": ut["placebo_0_rundt_null"].get(k, False)}
            if nm == "samla":
                p["felle_a"] = ut["felle_a_dekning"][k] >= 0.9
            elif k in ut["felle_a_dekning"]:
                p["felle_a"] = ut["felle_a_dekning"][k] >= 0.9
            if x in ("dd", "dd_minus_ddfoer"):
                p["felle_b"] = ut["felle_b_rundt_null"].get(k, False)
            if x in ("theta", "dd"):
                p["felle_c"] = ut["felle_c_rundt_null"].get(k, False)
            portar[nm][x] = p
    epoke = {e: {x: None for x in HOVUDTAL} for e in ("foer1850", "fraa1850")}
    for lead in (30, 45):
        w = ut["planting_wood_%d" % lead]
        for e in epoke:
            for x in HOVUDTAL:
                if epoke[e][x] is None and w[sub[x] + "." + e]["del_funne"] >= 0.8:
                    epoke[e][x] = lead
    p1b = {k: ut["placebo_1b"][k]["p97_5"] for k in ut["placebo_1b"] if k.split(".")[-1] in HOVUDTAL and "1850" not in k}
    frys = {
        "opploysing_aar": L, "spegla_planting": sp_, "terskel": terskel,
        "terskel_alternativ_verknad_av_10pst_planting_utan_dom": terskel_alt, "lesande": lesande,
        "nm_bindande": nm_bind, "nm_suitar_per_bolk": nm_spec,
        "epoke_wood_opploysing_aar": epoke,
        "katalog_va_lesande": bool(ut["planting_katalog_va_30"]["a.VA"]["del_funne"] >= 0.8),
        "placebo_1b_p97_5": p1b,
        "placebo_1b_median_theta": {nm: ut["placebo_1b"][nm + ".theta"]["median"] for nm in ("samla", "VA", "NM")},
        "placebo_1b_kvintil": {k: [ut["placebo_1b"][k]["p2_5"], ut["placebo_1b"][k]["p97_5"]] for k in ut["placebo_1b"] if "kvint" in k},
        "portar": portar,
        "rundt_null_regel": "|middel| høgst %.2f standardavvik av fordelinga" % RUNDT_NULL,
        "foer1850_rundt_null": "90 %-intervallet ligg innanfor pluss og minus terskelen for theta (for DD og DD minus DD_før: terskelen for DD)",
        "foer1850_minst_dokumenterte": 60,
        "einslege_del": 0.2, "dd_terskelfaktor": 0.5,
    }
    ut["frose"] = frys
    fp.lagre(MAPPE, "KONTROLL.json", js(ut))
    print("Frose:", json.dumps(js({k: frys[k] for k in ("opploysing_aar", "terskel", "lesande", "nm_bindande", "nm_suitar_per_bolk",
                                                          "epoke_wood_opploysing_aar", "katalog_va_lesande")}), ensure_ascii=False))
    print("Ferdig %.0f s" % (time.time() - T0))


# ------------------------------------------------------------------ domar
def _v(iv, k):
    r = iv.get(k, {})
    return r.get("verdi"), r.get("ki95", [np.nan, np.nan]), r.get("ki90", [np.nan, np.nan])


def _fin(*x):
    return all(v is not None and np.isfinite(v) for v in x)


def dom_hovud(v, ki, terskel, p975, lesande, portar):
    if not lesande:
        return "UGYLDIG", "planta forsprang vart ikkje funne i minst 80 % av plantingane, eller spegelen held ikkje"
    feil = [k for k, ok in portar.items() if not ok]
    if feil:
        return "UGYLDIG", "talet blir ikkje dømt: " + ", ".join(feil)
    if not _fin(v, ki[0], ki[1]):
        return "UGYLDIG", "manglar tal"
    if v <= 0 or ki[0] <= 0:
        return "SLO FEIL", "verdien er på null eller under, eller intervallet dekkjer null"
    if terskel is not None and v < terskel:
        return "UAVGJORD", "over null, men under den frosne terskelen"
    if p975 is not None and v <= p975:
        return "UAVGJORD", "over null, men ikkje over 97,5-prosentilen i placebo 1b"
    return "HELDT", ""


def dom_nm(v, ki, bind, portar):
    if not bind:
        return "UGYLDIG", "Nasjonalmuseet har ikkje styrke: planta forsprang gav rett forteikn i under 80 % av plantingane"
    feil = [k for k, ok in portar.items() if not ok]
    if feil:
        return "UGYLDIG", "talet blir ikkje dømt: " + ", ".join(feil)
    if not _fin(v):
        return "UGYLDIG", "manglar tal"
    if v <= 0:
        return "SLO FEIL", "ulikt forteikn i Nasjonalmuseet"
    return "HELDT", "same forteikn" + ("" if _fin(ki[0]) and ki[0] > 0 else "; intervallet dekkjer null")


def dom_epoke(x, IVW, F, n_dok):
    e = F["epoke_wood_opploysing_aar"]
    terskel = F["terskel"]["samla"]["theta" if x == "theta" else "dd"]
    vf, kf, _ = _v(IVW, "samla.fraa1850." + x)
    vb, kb, kb9 = _v(IVW, "samla.foer1850." + x)
    if e["fraa1850"][x] is None:
        return "UGYLDIG", "planta forsprang vart ikkje funne frå 1850"
    if not _fin(vf, kf[0]):
        return "UGYLDIG", "manglar tal"
    if vf <= 0 or kf[0] <= 0:
        return "SLO FEIL", "ingen retning frå 1850"
    if e["foer1850"][x] is None:
        return "UAVGJORD", "ikkje avgjort for tida før industrien: planta forsprang vart ikkje funne før 1850"
    if n_dok < F["foer1850_minst_dokumenterte"]:
        return "UAVGJORD", "ikkje avgjort for tida før industrien: færre enn 60 målstolar med dokumentert datering"
    if not _fin(vb, kb[0], kb[1]):
        return "UGYLDIG", "manglar tal før 1850"
    if kb[0] <= 0 <= kb[1] and kb[0] <= vf <= kb[1]:
        return "UAVGJORD", "ikkje avgjort for tida før industrien: intervallet dekkjer både null og verdien frå 1850"
    if vb > 0 and kb[0] > 0:
        return "HELDT", "same forteikn før og frå 1850"
    if terskel is not None and _fin(kb9[0], kb9[1]) and -terskel <= kb9[0] and kb9[1] <= terskel:
        return "SLO FEIL", "rundt null før 1850; påstanden står att som ei utsegn om industriell tid"
    if kb[1] < 0:
        return "SLO FEIL", "motsett forteikn før 1850"
    return "UAVGJORD", ""


def tal(x, d=2):
    return ("%.*f" % (d, x)).replace(".", ",") if _fin(x) else "manglar"


# ------------------------------------------------------------------ --opne
def opne():
    commit = fp.sjekk_forsegla(MAPPE)
    KK = json.load(open(os.path.join(MAPPE, "KONTROLL.json"), encoding="utf-8"))
    F = KK["frose"]
    rng = np.random.default_rng(FROE)
    O = Oppsett()
    GI = instrument()
    dok = ((TIL - AAR) <= 5) & (AAR % 5 != 0)

    def stat_opne(T, W=None):
        ut = hovudstat(T, W, epokar=True, kvint=True)
        Wn = np.ones((1, len(T["a"]))) if W is None else W
        gi = GI[T["gid"]]
        for nm, s in (("samla", np.ones(len(T["a"]), bool)), ("VA", T["mus"] == 0), ("NM", T["mus"] == 1)):
            ut[nm + ".theta_g_kovariat"] = fe_theta(Wn, T["q"], T["a"], T["cell"], s, X=gi)
        g90 = np.nanquantile(gi[:, 0], 0.9)
        keep = np.isfinite(gi[:, 0]) & (gi[:, 0] <= g90) & (np.nansum(gi[:, 1:], 1) == 0)
        U = deltabell(T, keep)
        for k, v in hovudstat(U, None if W is None else W[:, keep]).items():
            nm, x = k.split(".", 1)
            ut[nm + ".utan_flagg_og_g." + x] = v
        ut["samla.etter1900.theta"] = fe_theta(Wn, T["q"], T["a"], T["cell"], T["mid"] >= 1900)
        return ut

    def stat_wood(T, W=None):
        ut = hovudstat(T, W, epokar=True, kvint=True)
        sel = dok[T["gid"]] & (T["mid"] < 1850)
        U = deltabell(T, sel)
        st = hovudstat(U, None if W is None else W[:, sel], nivaa=("samla",))
        for x in HOVUDTAL:
            ut["samla.foer1850_dok." + x] = st["samla." + x]
        return ut

    print("Hovudkøyringa")
    MAIN = O.kjede(AAR, TIL, ekstra=np.ones(N, bool))
    T = MAIN.T
    IV = MAIN.intervall(stat_opne, N_BOOT, rng, bruk_fp=True)
    print("WOOD-køyringa")
    WOODK = O.kjede(AAR, TIL, lev=WOOD)
    IVW = WOODK.intervall(stat_wood, N_BOOT, rng, bruk_fp=True)
    n_dok = int(((WOODK.T["mid"] < 1850) & dok[WOODK.T["gid"]]).sum())
    print("Alle målstolar")
    IVA = O.kjede(AAR, TIL, regel="alle").intervall(stat_enkel, 300, rng, jk=False)
    print("Katalogversjonen")
    KD, _ = katalogdata()
    csk = ctx_katalog(KD)
    IVK = kjede_katalog(csk, KD).intervall(lambda T_, W=None: hovudstat(T_, W, nivaa=("VA", "NM", "RM")), N_BOOT, rng)
    IVKR = O.kjede(AAR, TIL, cs=[ctx_ramme(mu, Xe=katalog_kryss_X(mu)) for mu in ("VA", "NM")]).intervall(stat_enkel, 300, rng, jk=False)

    print("Robustheit")
    hov = maske_fraa(T)
    rob = {}

    def r_(namn, K):
        rob[namn] = K.intervall(stat_enkel, 300, rng, jk=False)
        print("  ", namn, "%.0f s" % (time.time() - T0))
    r_("datering_startaar", O.kjede(AAR, AAR, regel="gjeven", kand=hov))
    r_("datering_sluttaar", O.kjede(TIL, TIL, regel="gjeven", kand=hov))
    r_("fem_band_10aar_2_suitar", O.kjede(AAR, TIL, regel="gjeven", kand=hov, sp=TIARS))
    r_("bolkar_8_til_40", O.kjede(AAR, TIL, regel="gjeven", kand=hov, sp=B8_40))
    r_("bolkar_20_til_80", O.kjede(AAR, TIL, regel="gjeven", kand=hov, sp=B20_80))
    r_("tredje_naeraste", O.kjede(AAR, TIL, regel="gjeven", kand=hov, kw={"kn": 3, "mc": True}))
    for namn, d_, fi in (("einslege_10pst", 0.1, 0), ("einslege_30pst", 0.3, 0), ("terskel_r_3", 0.2, 1), ("terskel_2r_3", 0.2, 2)):
        rob[namn] = MAIN.intervall(lambda T_, W=None, d_=d_, fi=fi: hovudstat(T_, W, del_=d_, fi=fi), 300, rng, jk=False)
    idxs = [np.where(MUS == mu)[0] for mu in ("VA", "NM")]
    r_("typegruppe", O.kjede(AAR, TIL, regel="gjeven", kand=hov, cs=[ctx_ramme(mu, tg=TG[i]) for mu, i in zip(("VA", "NM"), idxs)]))
    r_("komponentar_10", O.kjede(AAR, TIL, regel="gjeven", kand=hov, cs=[ctx_ramme(mu, X=rom(i, k=10)) for mu, i in zip(("VA", "NM"), idxs)]))
    r_("komponentar_20", O.kjede(AAR, TIL, regel="gjeven", kand=hov, cs=[ctx_ramme(mu, X=rom(i, k=20)) for mu, i in zip(("VA", "NM"), idxs)]))
    r_("avkorta_3sd", O.kjede(AAR, TIL, regel="gjeven", kand=hov, cs=[ctx_ramme(mu, X=rom(i, klipp=True)) for mu, i in zip(("VA", "NM"), idxs)]))
    r_("med_nyutgaaver", O.kjede(AAR, TIL, regel="gjeven", kand=hov, cs=[ctx_ramme(mu, med_prod=False) for mu in ("VA", "NM")]))
    r_("einsemd_front_pil_side", O.kjede(AAR, TIL, regel="gjeven", kand=hov,
                                         cs=[ctx_ramme(mu, X=rom(i, (2, 3)), Xe=rom(i, (0, 1))) for mu, i in zip(("VA", "NM"), idxs)]))
    r_("einsemd_side_pil_front", O.kjede(AAR, TIL, regel="gjeven", kand=hov,
                                         cs=[ctx_ramme(mu, X=rom(i, (0, 1)), Xe=rom(i, (2, 3))) for mu, i in zip(("VA", "NM"), idxs)]))
    cpool = lag_ctx(rom(np.arange(N)), SUITE, PK, NK, MUKODE, np.arange(N), grp=MUKODE)
    r_("naboar_fraa_begge_museum", Kjede([cpool], [MID], [AAR], [TIL], sp=POOL, regel="gjeven", kands=[hov]))
    nyutg = {}
    for nm in ("samla", "VA", "NM"):
        a_, b_ = rob["med_nyutgaaver"][nm + ".theta"]["verdi"], IV[nm + ".theta"]["verdi"]
        nyutg[nm] = (a_ - b_) / a_ if _fin(a_, b_) and a_ != 0 else None

    # placebo 3 på dei verkelege dataa
    K2 = O.kjede(3549.5 - TIL, 3549.5 - AAR, kw={"snu": True})
    p3 = float(hovudstat(K2.T)["samla.theta"][0] + IV["samla.theta"]["verdi"])

    # ---------------------------------------------------------- domar
    fore = []
    P = F["portar"]
    for nm in ("samla", "VA", "NM"):
        for x, fid in (("theta", "H1"), ("dd", "H2"), ("dd_minus_ddfoer", "H3")):
            v, ki, _ = _v(IV, nm + "." + x)
            if nm == "NM":
                dm, mk = dom_nm(v, ki, F["nm_bindande"][x], P[nm][x])
            else:
                ter = F["terskel"][nm].get(x) if x in ("theta", "dd") else None
                dm, mk = dom_hovud(v, ki, ter, F["placebo_1b_p97_5"].get(nm + "." + x), F["lesande"][nm][x], P[nm][x])
            fore.append({"id": fid, "nivaa": nm, "storleik": x, "verdi": v, "ki95": ki, "dom": dm, "merknad": mk})
    # F4 datering
    vt = IV["samla.theta"]["verdi"]
    va_, vs_ = rob["datering_startaar"]["samla.theta"]["verdi"], rob["datering_sluttaar"]["samla.theta"]["verdi"]
    if not F["lesande"]["samla"]["theta"] or not all(P["samla"]["theta"].values()):
        d4 = "UGYLDIG"
    else:
        d4 = "HELDT" if _fin(vt, va_, vs_) and min(vt, va_, vs_) > 0 else "SLO FEIL"
    fore.append({"id": "F4", "nivaa": "samla", "storleik": "theta under startår, sluttår og midtår", "verdi": [va_, vs_, vt],
                 "ki95": None, "dom": d4, "merknad": "teikn for DD og DD minus DD_før: " + ", ".join(
                     "%s %s" % (x, [tal(rob[k]["samla." + x]["verdi"]) for k in ("datering_startaar", "datering_sluttaar")]) for x in ("dd", "dd_minus_ddfoer"))})
    # F5 katalogrommet i V&A
    vk, kk, _ = _v(IVK, "VA.theta")
    if not F["katalog_va_lesande"]:
        d5, m5 = "UGYLDIG", "planta forsprang vart ikkje funne i katalogrommet"
    elif not _fin(vk):
        d5, m5 = "UGYLDIG", "manglar tal"
    else:
        d5 = "HELDT" if vk > 0 else "SLO FEIL"
        v3 = IV["VA.theta"]["verdi"]
        m5 = "instrumentutfall: theta over null i 3D og ikkje i katalogrommet" if (vk <= 0 and _fin(v3) and v3 > 0) else ""
    fore.append({"id": "F5", "nivaa": "VA", "storleik": "theta i katalogrommet", "verdi": vk, "ki95": kk, "dom": d5, "merknad": m5})
    # F6 før og frå 1850, WOOD-køyringa
    for x in HOVUDTAL:
        dm, mk = dom_epoke(x, IVW, F, n_dok)
        fore.append({"id": "F6", "nivaa": "samla", "storleik": x + " før og frå 1850 (WOOD)",
                     "verdi": [IVW["samla.foer1850." + x]["verdi"], IVW["samla.fraa1850." + x]["verdi"]],
                     "ki95": [IVW["samla.foer1850." + x]["ki95"], IVW["samla.fraa1850." + x]["ki95"]], "dom": dm, "merknad": mk})
    dom = {(f["id"], f["nivaa"], f["storleik"]): f["dom"] for f in fore}
    skildring = dom[("H1", "samla", "theta")] == "HELDT" and d4 == "HELDT" and d5 == "HELDT"
    minne = skildring and dom[("H2", "samla", "dd")] == "HELDT" and dom[("H3", "samla", "dd_minus_ddfoer")] == "HELDT"
    vd, kd, _ = _v(IV, "samla.dd")
    kort = ("Dei mest einslege stolane ligg %s nærare generasjonen etter seg enn dei minst einslege (theta %s, intervall %s til %s), "
            "og svermen %s mot dei einslege (DD %s, intervall %s til %s)." % (
                "" if _fin(vt) and vt > 0 else "ikkje", tal(vt), tal(IV["samla.theta"]["ki95"][0]), tal(IV["samla.theta"]["ki95"][1]),
                "veks" if _fin(vd) and vd > 0 else "veks ikkje", tal(vd), tal(kd[0]), tal(kd[1]))).replace("  ", " ")
    per_museum = {nm: {k.split(".", 1)[1]: v for k, v in IV.items() if k.startswith(nm + ".")} for nm in ("VA", "NM")}
    n = {"maalstolar": {mu: int((T["mus"] == k).sum()) for k, mu in enumerate(("VA", "NM"))},
         "maalstolar_med_alle_tre_mengdene": {mu: int((T["ff"] & (T["mus"] == k)).sum()) for k, mu in enumerate(("VA", "NM"))},
         "einslege_med_alle_tre_mengdene": {mu: int((T["ff"] & (T["q"] >= 0.8 - 1e-9) & (T["mus"] == k)).sum()) for k, mu in enumerate(("VA", "NM"))},
         "wood_maalstolar": int(len(WOODK.T["a"])), "wood_foer1850_dokumentert": n_dok}
    res = {"prove": "P4", "opna": time.strftime("%Y-%m-%d"), "forsegling_commit": commit, "n": n,
           "samla": {k.split(".", 1)[1]: v for k, v in IV.items() if k.startswith("samla.")},
           "per_museum": per_museum, "foreseiingar": fore,
           "samla_dom": {"stoetta_som_skildring": skildring, "stoetta_som_minne_i_landskapet": minne},
           "theta_innan_type": {nm: IV[nm + ".theta"]["verdi"] - F["placebo_1b_median_theta"][nm] for nm in ("samla", "VA", "NM")},
           "dd_fast_terskel_utan_dom": {nm: IV[nm + ".dd_fast"] for nm in ("samla", "VA", "NM")},
           "alle_maalstolar_utan_dom": IVA, "wood": IVW, "katalog": IVK, "kryssmaaling_katalog_einsemd_3d_pil": IVKR,
           "robustheit": rob, "delen_av_pila_som_er_nyutgaaver": nyutg,
           "faget_jamfoering": {"theta_etter_1900": IV["samla.etter1900.theta"], "theta_foer_1850": IV["samla.foer1850.theta"]},
           "placebo_3_paa_verkelege_data_theta_sum": p3,
           "kort": kort}
    fp.lagre(MAPPE, "RESULTAT.json", js(res))
    ein = T["q"] >= 0.8 - 1e-9
    fig = {"venstre": {"x_ln_dfoer_minus_e": T["lf"] - T["e"], "y_ln_detter_minus_e": T["le"] - T["e"], "einsleg": ein, "museum": T["mus"]},
           "hogre_ovst": {kj: {ep: [{"femdel": k, "verdi": src["samla.%s.kvint%d" % (ep, k)]["verdi"], "ki95": src["samla.%s.kvint%d" % (ep, k)]["ki95"],
                                     "placebo_1b": F["placebo_1b_kvintil"].get("samla.%s.kvint%d" % (ep, k)) if kj == "hovud" else None}
                                    for k in range(5)] for ep in ("foer1850", "fraa1850")}
                          for kj, src in (("hovud", IV), ("wood", IVW))},
           "hogre_nedst": {"3d": {x: IV["samla." + x] for x in ("ddfoer", "dd", "dd_minus_ddfoer")},
                           "katalog_va": {x: IVK["VA." + x] for x in ("ddfoer", "dd", "dd_minus_ddfoer")}}}
    fp.lagre(MAPPE, "FIGURDATA.json", js(fig))
    print(kort)
    print("Ferdig %.0f s" % (time.time() - T0))


if __name__ == "__main__":
    if "--kontroll" in sys.argv:
        kontroll()
    elif "--opne" in sys.argv:
        opne()
    else:
        print(__doc__)
