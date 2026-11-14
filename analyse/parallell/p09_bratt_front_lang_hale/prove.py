"""p09_bratt_front_lang_hale: ein formregion blir teken på ein gong og forlaten seint.

--kontroll: pålitelegheit for måla og dei sju koordinatane, nullmodell 1 (permuterte årstal), krympe-placebo,
            kant-placebo, instrumentplacebo (jamt spreidde skingrupper på dei verkelege intervalla), dateringsklassar
            (rapporterte for seg) og planta effekt med spegel. Skriv ut kontrolltal, aldri verkelege utfall.
            Kontrollen reknar ingen FH for formregionane på dei verkelege årstala.
--opne:     forseglingssjekk først, deretter estimanden på heile ramma, VA og NM kvar for seg og samla,
            med KI frå bootstrap over suitar, null 1, null 2 og null 3.

Kvar storleik blir rekna i to versjonar:
  alle:  log(E/S) for kvar region og årstrekning, slik spesifikasjonen seier.
  kant:  same, men ei region-trekning der dei tre første ligg i den første kantsona (u(3) <= KANT) eller dei tre
         siste i den siste (u(n-2) >= 1 - KANT), er teken ut. Regelen er lik når tida blir spegla, så null 1 er
         framleis symmetrisk om 0. Han tek bort regionar som held kanten av samlinga. Der er inngangen eller
         utgangen ikkje observert (sensur), og log(E/S) kan bli nær pluss eller minus 3 utan nokon mekanisme.
Regionane har lik vekt (vekta er invers varians: log(E/S) har om lag same varians for alle n, sjå FORESEIINGAR.json).
"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
import felles_p as fp

D = fp.last()
MAPPE = os.path.dirname(os.path.abspath(__file__))
PROVE = "p09_bratt_front_lang_hale"
SETT = np.asarray(D["sett"])
MUS = ("VA", "NM")
SELS = ("samla",) + MUS
MUKODE = {"VA": 1, "NM": 2}
RNG = 20261113
NPERM = 200      # køyreregel: høgst 200 permutasjonar
NBOOT = 500      # køyreregel: høgst 500 bootstrap-trekk
NPLANT = 200     # plantingar per museum
NPLAC = 200      # trekksett for instrumentplaceboen og dateringsklassane
NKANT = 100      # falske verder i kant-placeboen
NTREKK = 20      # årstrekningar per eining (ei eining = éin suite)
MIN_EN = 6       # minste tal einingar i ein region innan museum
K = 40
KS = (25, 80)    # robustheit saman med K
FROER = 5
KANT = 0.03      # kantsona: dei første og siste 3 % av einingane i museet
KANT_ROB = 0.05  # rapportert for seg
M_KANT = 5       # einingar som blir flytte inn i kantsona per region i kant-placeboen
MAALE = ("sete_h", "sete_djupn", "sete_breidd", "breidd3d", "djupn3d", "sete_halling", "rygg_halling")
UKJEND = {"", "ukjent", "ukjend", "unknown"}
STORL = ("FH", "F", "T", "FHk", "Fk", "Tk")


def _r(x):
    x = float(x)
    return None if not np.isfinite(x) else round(x, 4)


def _band(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return {"middel": _r(v.mean()), "sd": _r(v.std()), "p5": _r(np.quantile(v, 0.05)), "p95": _r(np.quantile(v, 0.95))}


# ------------------------------------------------------------------ form per stol (ingen årstal)
def _helmert(p):
    Hm = np.zeros((p - 1, p))
    for i in range(1, p):
        Hm[i - 1, :i] = 1.0
        Hm[i - 1, i] = -float(i)
        Hm[i - 1] /= np.linalg.norm(Hm[i - 1])
    return Hm


def _stol_trekk(over=None):
    """Sju koordinatar per stol: fem Helmert-kontrastar av sentrerte loggar av sete_h, sete_djupn, sete_breidd,
    breidd3d, djupn3d og H, pluss sete_halling og rygg_halling (som i p08). Ein feil i katalog-H som skalerer alle
    lengder, fell bort i sentreringa (lærdom 9). over: erstatningar for 3D-mål (berre i krympe-placeboen)."""
    m = dict(D["m"])
    if over:
        m.update(over)
    cols = [np.asarray(m[a], float) for a in ("sete_h", "sete_djupn", "sete_breidd", "breidd3d", "djupn3d")]
    with np.errstate(all="ignore"):
        L = np.log(np.column_stack(cols + [np.asarray(D["H"], float)]))
    L = np.where(np.isfinite(L), L, np.nan)
    Lc = L - L.mean(axis=1, keepdims=True)
    return np.column_stack([Lc @ _helmert(6).T, np.asarray(m["sete_halling"], float), np.asarray(m["rygg_halling"], float)])


def einingar(over=None):
    """Suitar slegne saman til einingar (museum|suite). Intervall: tidlegaste aar til seinaste aar_til i eininga.
    Alle einingar er med på tidsaksen (heile ramma). Berre einingar med minst éin stol med alle sju koordinatar
    (FORM) får ein region; dei andre tel likevel med i rangen."""
    x = _stol_trekk(over)
    mu_st = np.asarray(D["museum"])
    key = np.array([a + "|" + str(b) for a, b in zip(mu_st, np.asarray(D["suite"]))])
    names, inv = np.unique(key, return_inverse=True)
    inv = inv.reshape(-1)
    nu = len(names)
    ok_st = np.all(np.isfinite(x), axis=1)
    cnt = np.bincount(inv[ok_st], minlength=nu).astype(float)
    X = np.column_stack([np.bincount(inv[ok_st], weights=x[ok_st, j], minlength=nu) for j in range(x.shape[1])])
    with np.errstate(all="ignore"):
        X = X / cnt[:, None]
    LO = np.full(nu, np.inf)
    HI = np.full(nu, -np.inf)
    np.minimum.at(LO, inv, np.asarray(D["aar"], float))
    np.maximum.at(HI, inv, np.asarray(D["aar_til"], float))
    first = np.full(nu, -1)
    for i, j in enumerate(inv):
        if first[j] < 0:
            first[j] = i
    ok = np.isfinite(LO) & np.isfinite(HI)
    return {"names": names[ok], "MU": mu_st[first][ok], "X": X[ok], "FORM": (cnt > 0)[ok], "LO": LO[ok], "HI": HI[ok],
            "MAT": np.asarray(D["mat"])[first][ok], "PROD": np.asarray(D["produsent"])[first][ok],
            "BOLK": (np.clip(LO, 1550, 1999) // 50).astype(int)[ok], "NST": np.bincount(inv, minlength=nu)[ok]}


def _kmeans(Z, k, seed, iters=100):
    rng = np.random.default_rng(seed)
    C = [Z[rng.integers(len(Z))]]
    for _ in range(1, k):
        d = np.min(((Z[:, None, :] - np.array(C)[None]) ** 2).sum(-1), axis=1)
        C.append(Z[rng.choice(len(Z), p=d / d.sum())])
    C = np.array(C)
    for _ in range(iters):
        lab = (((Z[:, None, :] - C[None]) ** 2).sum(-1)).argmin(1)
        Cn = np.array([Z[lab == j].mean(0) if np.any(lab == j) else C[j] for j in range(k)])
        if np.allclose(Cn, C):
            break
        C = Cn
    dist = ((Z[:, None, :] - C[None]) ** 2).sum(-1)
    return dist.argmin(1), float(dist.min(1).sum())


def regionar(E, k, froer=None, base=RNG):
    """k-means på dei standardiserte koordinatane til einingane med form, begge musea saman, utan årstal.
    froer None: beste av FROER frø etter innertraust. -1 for einingar utan form."""
    F = E["FORM"]
    X = E["X"][F]
    Z = (X - X.mean(0)) / X.std(0)
    froer = range(FROER) if froer is None else froer
    lab = min((_kmeans(Z, k, base + s) for s in froer), key=lambda t: t[1])[0]
    REG = np.full(len(F), -1)
    REG[F] = lab
    return REG


def grp_av(MU, REG):
    """Region innan museum: kode = museum * 1000 + region. -1 utan region."""
    kode = np.array([MUKODE[m] for m in MU])
    return np.where(REG >= 0, kode * 1000 + REG, -1)


def ari(a, b):
    _, ai = np.unique(a, return_inverse=True)
    _, bi = np.unique(b, return_inverse=True)
    M = np.zeros((ai.max() + 1, bi.max() + 1))
    np.add.at(M, (ai.reshape(-1), bi.reshape(-1)), 1)
    c2 = lambda v: float((v * (v - 1) / 2).sum())
    sij, sa, sb, n = c2(M), c2(M.sum(1)), c2(M.sum(0)), len(a) * (len(a) - 1) / 2
    e = sa * sb / n
    return float((sij - e) / (0.5 * (sa + sb) - e))


# ------------------------------------------------------------------ u, FH, F, T
def uverdi(lo, hi, mu, rng):
    """NTREKK årstrekningar per eining (uniform i [lo, hi]; eksakt år blir [år, år + 1)).
    u = (rang innan museum + 0,5) / talet på einingar i museet, så u er symmetrisk når tida blir spegla."""
    U = np.zeros((NTREKK, len(lo)))
    width = np.maximum(hi - lo, 1.0)
    for m in np.unique(mu):
        c = np.where(mu == m)[0]
        y = lo[c] + rng.random((NTREKK, len(c))) * width[c]
        U[:, c] = (np.argsort(np.argsort(y, axis=1), axis=1) + 0.5) / len(c)
    return U


def grupper(GRP):
    return [(int(g), np.where(GRP == g)[0]) for g in np.unique(GRP) if g >= 0 and np.sum(GRP == g) >= MIN_EN]


def grpstat(U, GRP, kant=KANT, gl=None):
    """Ei rad per region med minst MIN_EN einingar: museum, trekningar, sum log(E/S), sum F, sum T, behaldne
    trekningar i kant-versjonen og summane der, og snittet av log(E/S) over trekningane."""
    gl = grupper(GRP) if gl is None else gl
    rows = np.zeros((len(gl), 10))
    for i, (g, c) in enumerate(gl):
        A = np.sort(U[:, c], axis=1)
        lr = np.log((A[:, 2] - A[:, 0] + 1e-12) / (A[:, -1] - A[:, -3] + 1e-12))
        gap = np.diff(A, axis=1)
        med = np.median(gap, axis=1)
        Fi = gap[:, 0] > 3 * med
        Ti = gap[:, -1] > 3 * med
        keep = (A[:, 2] > kant) & (A[:, -3] < 1 - kant)
        rows[i] = [g // 1000, len(lr), lr.sum(), Fi.sum(), Ti.sum(), keep.sum(), lr[keep].sum(), Fi[keep].sum(),
                   Ti[keep].sum(), lr.mean()]
    return rows


def agg(rows, nm):
    """FH, F og T med lik vekt per region (kvar region har NTREKK trekningar). samla = VA og NM saman, regionane
    framleis innan museum. Kant-versjonen vektar kvar behalden region-trekning likt."""
    r = rows if nm == "samla" else rows[rows[:, 0] == MUKODE[nm]]
    n, nk = r[:, 1].sum(), r[:, 5].sum()
    q = lambda a, b: float(a / b) if b > 0 else float("nan")
    return {"FH": q(r[:, 2].sum(), n), "F": q(r[:, 3].sum(), n), "T": q(r[:, 4].sum(), n),
            "FHk": q(r[:, 6].sum(), nk), "Fk": q(r[:, 7].sum(), nk), "Tk": q(r[:, 8].sum(), nk),
            "regionar": int(len(r)), "del_tekne_ut_kant": q(n - nk, n)}


def nullfordeling(E, GRP, strata, n, seed, kant=KANT, lr=False):
    """n permutasjonar av (aar, aar_til) som pakke innan strata. Regionane blir ståande."""
    rng = np.random.default_rng(seed)
    nu = len(E["MU"])
    gl = grupper(GRP)
    ut = {nm: {s: [] for s in STORL} for nm in SELS}
    lrs = {m: [] for m in MUS}
    for _ in range(n):
        p = fp.perm_innan(np.arange(nu), strata, rng)
        U = uverdi(E["LO"][p], E["HI"][p], E["MU"], rng)
        rows = grpstat(U, GRP, kant, gl)
        for nm in SELS:
            a = agg(rows, nm)
            for s in STORL:
                ut[nm][s].append(a[s])
        if lr:
            for m in MUS:
                lrs[m].extend(rows[rows[:, 0] == MUKODE[m], 9].tolist())
    out = {nm: {s: np.array(v) for s, v in d.items()} for nm, d in ut.items()}
    if lr:
        out["lr"] = lrs
    return out


def planta(U, GRP, mu, m, rng, speil=False):
    """Halvdelen av regionane i museum m: i kvar trekning blir den første tredjedelen av regionen pressa mot
    q33 i regionen (u' = q33 minus 0,3 (q33 minus u)) og den siste tredjedelen strekt frå q67 i regionen
    (u' = q67 + 1,5 (u minus q67)); spegel: motsett. q33 og q67 er kvantilane til regionen sjølv. Med kvantilane
    til heile museet (førre versjon) byter fronten og halen plass i regionar som ligg tidleg eller seint, og
    effekten snur der. Ikkje klipping og ikkje ny rangering; affin skalering per trekning til [0, 1] innan
    museet. log(E/S), F og T er uendra av affin skalering."""
    U = U.copy()
    cm = np.where(mu == m)[0]
    regs = [c for g, c in grupper(GRP) if g // 1000 == MUKODE[m]]
    if not regs:
        return U
    fa, fb = (1.5, 0.3) if speil else (0.3, 1.5)
    for i in rng.choice(len(regs), len(regs) // 2, replace=False):
        c = regs[i]
        Uc = U[:, c]
        n = Uc.shape[1]
        t = n // 3
        rang = np.argsort(np.argsort(Uc, axis=1), axis=1)
        q33 = np.quantile(Uc, 1 / 3, axis=1, keepdims=True)
        q67 = np.quantile(Uc, 2 / 3, axis=1, keepdims=True)
        ny = np.where(rang < t, q33 - fa * (q33 - Uc), Uc)
        ny = np.where(rang >= n - t, q67 + fb * (Uc - q67), ny)
        U[:, c] = ny
    lo_ = U[:, cm].min(axis=1, keepdims=True)
    hi_ = U[:, cm].max(axis=1, keepdims=True)
    U[:, cm] = (U[:, cm] - lo_) / (hi_ - lo_)
    return U


# ------------------------------------------------------------------ placeboar (ingen formregionar)
def dateringsklassar(E):
    """Klassar etter breidda på intervallet (eksakt, under 10, 10 til 25, 26 til 50, over 50 år). Rapporterte for seg."""
    kl = np.digitize(E["HI"] - E["LO"], [1e-9, 10, 26, 51])
    return np.array([MUKODE[m] for m in E["MU"]]) * 1000 + kl


def skingrupper(E, storl):
    """Instrumentplacebo: grupper med kjend symmetrisk tidsprofil. Einingane i kvart museum blir ordna etter
    midten av intervallet; ei gruppe er kvar s-te eining, så medlemene ligg jamt spreidde over heile samlinga
    (skala 1) eller over kvar halvdel (skala 2). Gruppestorleiken er medianen av regionstorleikane i museet.
    Ingen form går inn; forskjellen mellom front og hale kan berre kome frå dateringa (breidda på intervalla
    heng saman med tida) og frå rangeringa."""
    rng = np.random.default_rng(RNG + 7)
    G1 = np.full(len(E["MU"]), -1)
    G2 = np.full(len(E["MU"]), -1)
    for m in MUS:
        cm = np.where(E["MU"] == m)[0]
        order = cm[np.lexsort((rng.random(len(cm)), (E["LO"][cm] + E["HI"][cm]) / 2))]
        ng = max(int(np.median(storl[m])), MIN_EN)
        s = max(len(order) // ng, 1)
        for j in range(s):
            G1[order[j::s]] = MUKODE[m] * 1000 + j
        h = len(order) // 2
        for hh, half in enumerate((order[:h], order[h:])):
            s2 = max(len(half) // ng, 1)
            for j in range(s2):
                G2[half[j::s2]] = MUKODE[m] * 1000 + 500 * hh + j
    return G1, G2


def placebo_snitt(E, grps, seed):
    """Snitt over NPLAC trekksett på dei verkelege intervalla (ingen formregionar)."""
    rng = np.random.default_rng(seed)
    gls = [grupper(G) for G in grps]
    res = {nm: {s: [] for s in ("FH", "FHk")} for nm in SELS}
    for _ in range(NPLAC):
        U = uverdi(E["LO"], E["HI"], E["MU"], rng)
        rows = np.vstack([grpstat(U, G, KANT, gl) for G, gl in zip(grps, gls)])
        for nm in SELS:
            a = agg(rows, nm)
            res[nm]["FH"].append(a["FH"])
            res[nm]["FHk"].append(a["FHk"])
    return {nm: {s: _r(np.nanmean(v)) for s, v in d.items()} for nm, d in res.items()}


def kant_placebo(E, GRP, seed):
    """Falske verder: årstala permuterte innan museum, så får to tilfeldige regionar i kvart museum dei
    M_KANT tidlegaste intervalla (den første) og dei M_KANT neste (den andre). Det liknar ein region som
    held starten av samlinga. Viser kor mykje kanten åleine flyttar FH, og kor mykje som er att i kant-versjonen."""
    rng = np.random.default_rng(seed)
    MU = E["MU"]
    nu = len(MU)
    gl = grupper(GRP)
    medl = dict(gl)
    regs = {m: [g for g, c in gl if g // 1000 == MUKODE[m]] for m in MUS}
    res = {m: {"FH": [], "FHk": []} for m in MUS}
    for _ in range(NKANT):
        p = fp.perm_innan(np.arange(nu), MU, rng)
        lo, hi = E["LO"][p].copy(), E["HI"][p].copy()
        for m in MUS:
            cm = np.where(MU == m)[0]
            order = cm[np.lexsort((rng.random(len(cm)), (lo[cm] + hi[cm]) / 2))]
            sone = set(order[:2 * M_KANT].tolist())
            for ri, g in enumerate(rng.choice(regs[m], 2, replace=False)):
                mem = set(medl[g].tolist())
                fri = [e for e in order[ri * M_KANT:(ri + 1) * M_KANT] if e not in mem]
                kand = np.array([t for t in medl[g] if t not in sone])
                if len(kand) == 0 or not fri:
                    continue
                tgt = rng.choice(kand, min(len(fri), len(kand)), replace=False)
                for e, t in zip(fri, tgt):
                    lo[e], lo[t] = lo[t], lo[e]
                    hi[e], hi[t] = hi[t], hi[e]
        U = uverdi(lo, hi, MU, rng)
        rows = grpstat(U, GRP, KANT, gl)
        for m in MUS:
            a = agg(rows, m)
            res[m]["FH"].append(a["FH"])
            res[m]["FHk"].append(a["FHk"])
    return {m: {s: np.array(v) for s, v in d.items()} for m, d in res.items()}


def krympe_over():
    """KRYMPE-PLACEBO (krav 2): ein kopi av katalogmålet B trekt mot medianen med faktor 0,75, skalert til
    skalaen til sete_breidd (median og spreiing), med målefeilen til sete_breidd lagd på. Han erstattar
    sete_breidd i formrommet. Manglar i sete_breidd blir manglar her òg."""
    rng = np.random.default_rng(RNG + 5)
    sb = np.asarray(D["m"]["sete_breidd"], float)
    B = np.asarray(D["B"], float)
    medB = np.nanmedian(B)
    Bk = medB + 0.75 * (B - medB)
    a = np.nanstd(sb) / np.nanstd(B)
    kp = np.nanmedian(sb) + a * (Bk - medB)
    kp = kp + rng.normal(0.0, np.sqrt(fp.feilvarians(sb, SETT)[0]), len(kp))
    kp[~np.isfinite(sb)] = np.nan
    return {"sete_breidd": kp}


# ------------------------------------------------------------------ kontroll (berre permuterte, syntetiske eller ikkje-form-merke)
def kontroll():
    E = einingar()
    MU = E["MU"]
    nu = len(MU)
    REG = regionar(E, K)
    GRP = grp_av(MU, REG)
    gl = grupper(GRP)
    storl = {m: sorted(len(c) for g, c in gl if g // 1000 == MUKODE[m]) for m in MUS}
    ut = {"prove": PROVE, "stolar": int(D["n"]), "einingar": int(nu), "einingar_med_form": int(E["FORM"].sum()),
          "stolar_med_form": int(np.all(np.isfinite(_stol_trekk()), axis=1).sum()),
          "einingar_per_museum": {m: int((MU == m).sum()) for m in MUS},
          "regionar_med_minst_6_einingar": {m: len(storl[m]) for m in MUS},
          "regionstorleik": storl,
          "kantsone_einingar": {m: _r(KANT * (MU == m).sum()) for m in MUS}}

    # pålitelegheit (krav 0,7): råmåla og dei sju koordinatane som regionane er laga av
    pa = {a: _r(fp.paalit(np.asarray(D["m"][a], float), SETT)) for a in MAALE}
    pa["H"] = _r(fp.paalit(np.asarray(D["H"], float), SETT))
    x = _stol_trekk()
    pk = {"koord_%d" % (j + 1): _r(fp.paalit(x[:, j], SETT)) for j in range(x.shape[1])}
    ut["paalit"] = pa
    ut["paalit_koordinatar"] = pk
    ut["paalit_port"] = bool(all(v >= 0.7 for v in list(pa.values()) + list(pk.values())))

    # nullmodell 1: årstal permuterte innan museum. Symmetrisk om 0 for kvar region.
    n1 = nullfordeling(E, GRP, MU, NPERM, RNG + 1)
    ut["nullmodell_1"] = {}
    port = True
    for nm in SELS:
        d = {"alle": _band(n1[nm]["FH"]), "kant": _band(n1[nm]["FHk"]),
             "F_middel": _r(np.nanmean(n1[nm]["F"])), "T_middel": _r(np.nanmean(n1[nm]["T"])),
             "Fk_middel": _r(np.nanmean(n1[nm]["Fk"])), "Tk_middel": _r(np.nanmean(n1[nm]["Tk"]))}
        for v in ("alle", "kant"):
            b = d[v]
            port &= abs(b["middel"]) <= 0.05 and b["p5"] < 0 < b["p95"]
        port &= abs(d["F_middel"] - d["T_middel"]) <= 0.02 and abs(d["Fk_middel"] - d["Tk_middel"]) <= 0.02
        ut["nullmodell_1"][nm] = d
    ut["nullmodell_port"] = bool(port)
    band = lambda m, v: (ut["nullmodell_1"][m][v]["p5"], ut["nullmodell_1"][m][v]["p95"])

    # krympe-placebo: formrommet med krympa katalogkopi i staden for sete_breidd
    Ek = einingar(krympe_over())
    REGk = regionar(Ek, K)
    nk = nullfordeling(Ek, grp_av(Ek["MU"], REGk), Ek["MU"], NPERM, RNG + 4)
    F_ = E["FORM"] & Ek["FORM"]
    ut["krympe_placebo"] = {"ari_mot_regionane": _r(ari(REG[F_], REGk[F_])),
                            "ari_andre_froe_til_samanlikning": _r(ari(REG[E["FORM"]], regionar(E, K, base=RNG + 100)[E["FORM"]]))}
    kp = True
    for m in MUS:
        d = {}
        for v, s in (("alle", "FH"), ("kant", "FHk")):
            mid = float(np.nanmean(nk[m][s]))
            p5, p95 = band(m, v)
            d[v] = {"middel": _r(mid), "innan_null1_90": bool(p5 <= mid <= p95)}
            kp &= d[v]["innan_null1_90"]
        ut["krympe_placebo"][m] = d
    ut["krympe_port"] = bool(kp)

    # kant-placebo: kor mykje ein region som held starten av samlinga flyttar FH, med og utan kantregelen
    kpl = kant_placebo(E, GRP, RNG + 6)
    ut["kant_placebo"] = {}
    kport = True
    for m in MUS:
        d = {}
        for v, s in (("alle", "FH"), ("kant", "FHk")):
            arr = kpl[m][s]
            p5, p95 = band(m, v)
            d[v] = {"middel": _r(np.nanmean(arr)), "del_under_p5_null1": _r(np.mean(arr < p5)),
                    "innan_null1_90": bool(p5 <= np.nanmean(arr) <= p95)}
        kport &= d["kant"]["innan_null1_90"] and d["kant"]["del_under_p5_null1"] <= 0.15
        ut["kant_placebo"][m] = d
    ut["kant_port"] = bool(kport)

    # instrumentplacebo (krav F6): jamt spreidde skingrupper på dei verkelege intervalla
    G1, G2 = skingrupper(E, storl)
    ip = placebo_snitt(E, (G1, G2), RNG + 8)
    ut["instrumentplacebo"] = {"grupper": {m: int(sum(1 for G in (G1, G2) for g, c in grupper(G) if g // 1000 == MUKODE[m])) for m in MUS}}
    iport = True
    for m in MUS:
        d = {}
        for v, s in (("alle", "FH"), ("kant", "FHk")):
            p5, p95 = band(m, v)
            d[v] = {"middel": ip[m][s], "innan_null1_90": bool(p5 <= ip[m][s] <= p95)}
            iport &= d[v]["innan_null1_90"]
        ut["instrumentplacebo"][m] = d
    ut["instrumentplacebo_port"] = bool(iport)

    # dateringsklassar (rapporterte for seg, ikkje krav: dei er bundne til tida og held kanten av samlinga)
    dk = placebo_snitt(E, (dateringsklassar(E),), RNG + 9)
    ut["dateringsklassar"] = {m: {"alle": dk[m]["FH"], "kant": dk[m]["FHk"]} for m in MUS}

    # planta effekt og spegelplanting, på permuterte årstal
    rng = np.random.default_rng(RNG + 2)
    ut["planta"] = {}
    pport = True
    for m in MUS:
        pa5, pa95 = band(m, "alle")
        pk5, pk95 = band(m, "kant")
        fl, flk, sp, spk = [], [], [], []
        for _ in range(NPLANT):
            p = fp.perm_innan(np.arange(nu), MU, rng)
            U = uverdi(E["LO"][p], E["HI"][p], MU, rng)
            a = agg(grpstat(planta(U, GRP, MU, m, rng), GRP, KANT, gl), m)
            s = agg(grpstat(planta(U, GRP, MU, m, rng, speil=True), GRP, KANT, gl), m)
            fl.append(a["FH"]); flk.append(a["FHk"]); sp.append(s["FH"]); spk.append(s["FHk"])
        fl, flk, sp, spk = map(np.array, (fl, flk, sp, spk))
        d = {"alle": {"styrke_planta": _r(np.mean(fl < pa5)), "styrke_spegel": _r(np.mean(sp > pa95)),
                      "FH_planta_middel": _r(np.nanmean(fl)), "FH_spegel_middel": _r(np.nanmean(sp))},
             "kant": {"styrke_planta": _r(np.mean(flk < pk5)), "styrke_spegel": _r(np.mean(spk > pk95)),
                      "FH_planta_middel": _r(np.nanmean(flk)), "FH_spegel_middel": _r(np.nanmean(spk))}}
        for v in ("alle", "kant"):
            pport &= d[v]["styrke_planta"] >= 0.8 and d[v]["styrke_spegel"] >= 0.8
        ut["planta"][m] = d
    ut["planta_port"] = bool(pport)

    ut["klar"] = bool(ut["paalit_port"] and ut["nullmodell_port"] and ut["krympe_port"] and ut["kant_port"]
                      and ut["instrumentplacebo_port"] and ut["planta_port"])
    ut["merknad"] = ("Null 1, krympe-placebo, kant-placebo og planta effekt er rekna på permuterte årstal. Instrumentplaceboen "
                     "og dateringsklassane er rekna på dei verkelege intervalla, men utan formregionar. Null 2, null 3 og dei "
                     "verkelege utfalla er ikkje rekna her; dei ligg i --opne.")
    print(json.dumps(ut, ensure_ascii=False, indent=1))
    return ut


# ------------------------------------------------------------------ opning (forsegla køyring)
def _utan_produsent(GRP, PROD):
    """Tek ut einingar der same kjende produsent har meir enn fem einingar i same region. Ukjend produsent tel ikkje."""
    keys = np.array([str(g) + "|" + str(p) for g, p in zip(GRP, PROD)])
    kjend = np.array([str(p).strip().lower() not in UKJEND for p in PROD])
    u, c = np.unique(keys[kjend], return_counts=True)
    cnt = dict(zip(u, c))
    drop = np.array([kj and cnt.get(k, 0) > 5 for k, kj in zip(keys, kjend)])
    return np.where(drop, -1, GRP)


def _nvekt(rows, gl, nm):
    """FH med vekt lik talet på einingar i regionen (versjonen til byggjaren), rapportert for seg."""
    n = np.array([len(c) for g, c in gl], float)
    s = np.ones(len(rows), bool) if nm == "samla" else rows[:, 0] == MUKODE[nm]
    return float(np.sum(rows[s, 9] * n[s]) / np.sum(n[s]))


def _nn(x):
    if x is None or not np.isfinite(x):
        return "ikkje rekna"
    s = ("%.2f" % abs(x)).replace(".", ",")
    return ("minus " + s) if x < 0 else s


def opne():
    """Forsegla køyring. Blir ikkje køyrd før FORESEIINGAR.json og prove.py er committa og pusha."""
    fp.sjekk_forsegla(MAPPE)
    E = einingar()
    MU = E["MU"]
    nu = len(MU)
    LO, HI = E["LO"], E["HI"]
    REG = regionar(E, K)
    GRP = grp_av(MU, REG)
    gl = grupper(GRP)
    storl = {m: sorted(len(c) for g, c in gl if g // 1000 == MUKODE[m]) for m in MUS}
    GRPK = {k: grp_av(MU, regionar(E, k)) for k in KS}
    GRPS = [grp_av(MU, regionar(E, K, froer=[s])) for s in range(FROER)]
    rng = np.random.default_rng(RNG)
    U = uverdi(LO, HI, MU, rng)
    rows = grpstat(U, GRP, KANT, gl)
    est = {nm: agg(rows, nm) for nm in SELS}

    BOLKS = np.array([a + "|" + str(b) for a, b in zip(MU, E["BOLK"])])
    MATS = np.array([a + "|" + str(b) for a, b in zip(MU, E["MAT"])])
    n1 = nullfordeling(E, GRP, MU, NPERM, RNG + 1, lr=True)
    n2 = nullfordeling(E, GRP, BOLKS, NPERM, RNG + 2)
    n3 = nullfordeling(E, GRP, MATS, NPERM, RNG + 3)

    boot = {nm: {s: [] for s in STORL} for nm in SELS}
    for _ in range(NBOOT):
        j = fp.suiteboot(np.arange(nu), rng)
        rb = grpstat(uverdi(LO[j], HI[j], MU[j], rng), GRP[j], KANT)
        for nm in SELS:
            a = agg(rb, nm)
            for s in STORL:
                boot[nm][s].append(a[s])
    ki = {nm: {s: [_r(v) for v in fp.ki(np.array(boot[nm][s]))] for s in STORL} for nm in SELS}

    G1, G2 = skingrupper(E, storl)
    ip = placebo_snitt(E, (G1, G2), RNG + 8)
    dk_rows = grpstat(U, dateringsklassar(E), KANT)
    rk = {k: grpstat(U, G, KANT) for k, G in GRPK.items()}
    rk[K] = rows
    rs = [grpstat(U, G, KANT) for G in GRPS]
    rrob = grpstat(U, GRP, KANT_ROB, gl)
    rprod = grpstat(U, _utan_produsent(GRP, E["PROD"]), KANT)
    # datering etter stil: berre einingar med intervall under 10 år (rang innan desse), med eigen null 1
    sm = (HI - LO) < 10
    Esm = {"MU": MU[sm], "LO": LO[sm], "HI": HI[sm]}
    rsm = grpstat(uverdi(LO[sm], HI[sm], MU[sm], np.random.default_rng(RNG + 11)), GRP[sm], KANT)
    nsm = nullfordeling(Esm, GRP[sm], MU[sm], NPERM, RNG + 12)

    res = {"prove": PROVE,
           "n": {"stolar": int(D["n"]), "einingar": int(nu), "einingar_med_form": int(E["FORM"].sum()),
                 "einingar_VA": int((MU == "VA").sum()), "einingar_NM": int((MU == "NM").sum()),
                 "regionar_VA": len(storl["VA"]), "regionar_NM": len(storl["NM"])},
           "per_museum": {}}
    for nm in SELS:
        e = est[nm]
        res["per_museum"][nm] = {
            "FH": _r(e["FH"]), "FH_ki95": ki[nm]["FH"], "FHk": _r(e["FHk"]), "FHk_ki95": ki[nm]["FHk"],
            "F": _r(e["F"]), "T": _r(e["T"]), "Fk": _r(e["Fk"]), "Tk": _r(e["Tk"]),
            "F_ki95": ki[nm]["F"], "T_ki95": ki[nm]["T"],
            "regionar": e["regionar"], "del_tekne_ut_kant": _r(e["del_tekne_ut_kant"]),
            "null1": {"FH": _band(n1[nm]["FH"]), "FHk": _band(n1[nm]["FHk"]),
                      "F_middel": _r(np.nanmean(n1[nm]["F"])), "T_middel": _r(np.nanmean(n1[nm]["T"])),
                      "Fk_middel": _r(np.nanmean(n1[nm]["Fk"])), "Tk_middel": _r(np.nanmean(n1[nm]["Tk"]))},
            "null2": {"FH": _band(n2[nm]["FH"]), "FHk": _band(n2[nm]["FHk"])},
            "null3": {"FH": _band(n3[nm]["FH"]), "FHk": _band(n3[nm]["FHk"])},
            "p_null1_FH": _r((np.sum(n1[nm]["FH"] <= e["FH"]) + 1) / (NPERM + 1)),
            "p_null2_FH": _r((np.sum(n2[nm]["FH"] <= e["FH"]) + 1) / (NPERM + 1)),
            "p_null3_FH": _r((np.sum(n3[nm]["FH"] <= e["FH"]) + 1) / (NPERM + 1)),
            "p_null1_FHk": _r((np.sum(n1[nm]["FHk"] <= e["FHk"]) + 1) / (NPERM + 1)),
            "robustheit": {
                "k25": {s: _r(agg(rk[25], nm)[s]) for s in ("FH", "FHk")},
                "k80": {s: _r(agg(rk[80], nm)[s]) for s in ("FH", "FHk")},
                "k40_kvart_froe_FH": [_r(agg(r, nm)["FH"]) for r in rs],
                "k40_kvart_froe_FHk": [_r(agg(r, nm)["FHk"]) for r in rs],
                "kant_0_05_FHk": _r(agg(rrob, nm)["FHk"]),
                "utan_produsentklumpar": {s: _r(agg(rprod, nm)[s]) for s in ("FH", "FHk")},
                "n_vekta_FH": _r(_nvekt(rows, gl, nm)),
                "smal_datering": {"einingar": int(np.sum(sm & ((MU == nm) | (nm == "samla")))),
                                  "FH": _r(agg(rsm, nm)["FH"]), "FHk": _r(agg(rsm, nm)["FHk"]),
                                  "null1_FH": _band(nsm[nm]["FH"]), "null1_FHk": _band(nsm[nm]["FHk"])},
            },
            "instrumentplacebo": ip[nm],
            "dateringsklassar": {s: _r(agg(dk_rows, nm)[s]) for s in ("FH", "FHk")},
        }

    # ------------------------------------------------------------ domar
    pm = res["per_museum"]
    lt = lambda a, b: a is not None and b is not None and a < b
    n1ok = all(abs(pm[m]["null1"][v]["middel"]) <= 0.05 for m in SELS for v in ("FH", "FHk"))
    pl_ok = all(ip[m][s] is not None and pm[m]["null1"][v]["p5"] <= ip[m][s] <= pm[m]["null1"][v]["p95"]
                for m in MUS for v, s in (("FH", "FH"), ("FHk", "FHk")))
    ugyldig = lambda m: (not n1ok) or (not pl_ok) or pm[m]["regionar"] < 5 or pm[m]["FH"] is None or pm[m]["FHk"] is None
    dom = lambda ok, ug: "UGYLDIG" if ug else ("HELDT" if ok else "SLO FEIL")
    F = []
    for fid, m in (("F1", "VA"), ("F2", "NM")):
        ok = lt(pm[m]["FH"], 0) and lt(pm[m]["FHk"], 0)
        F.append({"id": fid, "museum": m, "verdi": {"FH": pm[m]["FH"], "FHk": pm[m]["FHk"]},
                  "ki95": {"FH": pm[m]["FH_ki95"], "FHk": pm[m]["FHk_ki95"]}, "terskel": "FH < 0 og FHk < 0",
                  "dom": dom(ok, ugyldig(m))})
    s_ = pm["samla"]
    ok3 = (lt(s_["FH"], s_["null1"]["FH"]["p5"]) and lt(s_["FH"], s_["null2"]["FH"]["p5"])
           and lt(s_["FHk"], s_["null1"]["FHk"]["p5"]))
    F.append({"id": "F3", "museum": "samla", "verdi": {"FH": s_["FH"], "FHk": s_["FHk"]},
              "ki95": {"FH": s_["FH_ki95"], "FHk": s_["FHk_ki95"]},
              "terskel": {"FH_under_p5_null1": s_["null1"]["FH"]["p5"], "FH_under_p5_null2": s_["null2"]["FH"]["p5"],
                          "FHk_under_p5_null1": s_["null1"]["FHk"]["p5"]},
              "dom": dom(ok3, ugyldig("VA") or ugyldig("NM"))})
    ok4 = all(lt(pm[m]["F"], pm[m]["null1"]["F_middel"]) and lt(pm[m]["null1"]["T_middel"], pm[m]["T"])
              and lt(pm[m]["Fk"], pm[m]["null1"]["Fk_middel"]) and lt(pm[m]["null1"]["Tk_middel"], pm[m]["Tk"]) for m in MUS)
    F.append({"id": "F4", "museum": "VA og NM",
              "verdi": {m: {"F": pm[m]["F"], "T": pm[m]["T"], "Fk": pm[m]["Fk"], "Tk": pm[m]["Tk"]} for m in MUS},
              "ki95": {m: {"F": pm[m]["F_ki95"], "T": pm[m]["T_ki95"]} for m in MUS},
              "terskel": {m: {s: pm[m]["null1"][s + "_middel"] for s in ("F", "T", "Fk", "Tk")} for m in MUS},
              "dom": dom(ok4, ugyldig("VA") or ugyldig("NM"))})
    v5 = {m: {"k%d" % k: {s: _r(agg(rk[k], m)[s]) for s in ("FH", "FHk")} for k in (KS[0], K, KS[1])} for m in MUS}
    ok5 = all(lt(v5[m][kk][s], 0) for m in MUS for kk in v5[m] for s in ("FH", "FHk"))
    F.append({"id": "F5", "museum": "VA og NM", "verdi": v5, "ki95": None, "terskel": "FH < 0 og FHk < 0 for k = 25, 40 og 80",
              "dom": dom(ok5, ugyldig("VA") or ugyldig("NM"))})
    F.append({"id": "F6", "museum": "VA og NM", "verdi": {m: ip[m] for m in MUS}, "ki95": None,
              "terskel": {m: {v: [pm[m]["null1"][v]["p5"], pm[m]["null1"][v]["p95"]] for v in ("FH", "FHk")} for m in MUS},
              "dom": "HELDT" if pl_ok else "SLO FEIL"})
    res["foreseiingar"] = F
    fell = (F[0]["dom"] == "SLO FEIL" or F[1]["dom"] == "SLO FEIL"
            or any(not (lt(pm[m]["F"], pm[m]["null1"]["F_middel"]) and lt(pm[m]["Fk"], pm[m]["null1"]["Fk_middel"])) for m in MUS))
    res["hypotesen_fell"] = bool(fell)
    nh = sum(f["dom"] == "HELDT" for f in F[:5])
    res["kort"] = ("FH er %s i VA og %s i NM, og %s og %s når regionar som held kanten av samlinga er tekne ut; "
                   "%d av fem føreseiingar heldt." % (_nn(pm["VA"]["FH"]), _nn(pm["NM"]["FH"]), _nn(pm["VA"]["FHk"]),
                                                     _nn(pm["NM"]["FHk"]), nh))

    fig = {"regionar": {}, "lr": {}, "lr_null1": {}}
    for m in MUS:
        rws = []
        for g, c in gl:
            if g // 1000 != MUKODE[m]:
                continue
            med_u = np.sort(np.median(U[:, c], axis=0))
            A = np.sort(U[:, c], axis=1)
            rws.append({"region": int(g % 1000), "n": int(len(c)), "median": _r(np.median(med_u)),
                        "lr": _r(np.log((A[:, 2] - A[:, 0]) / (A[:, -1] - A[:, -3])).mean()),
                        "prikkar": [_r(v) for v in med_u]})
        rws.sort(key=lambda d: d["median"])
        fig["regionar"][m] = rws
        fig["lr"][m] = [d["lr"] for d in rws]
        fig["lr_null1"][m] = [_r(v) for v in n1["lr"][m][:4000]]
    fp.lagre(MAPPE, "RESULTAT.json", res)
    fp.lagre(MAPPE, "FIGURDATA.json", fig)
    print(json.dumps({"kort": res["kort"], "domar": {f["id"]: f["dom"] for f in F}}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if "--opne" in sys.argv:
        opne()
    else:
        kontroll()
