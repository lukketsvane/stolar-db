"""t6_saumar.py - er stolen éi form eller to? Tre føreseiingar lesne ut av 5.701 og 6.672.

Frå læra: vurderinga er ein sum over omsyn (5.701), og spreiinga er den inverse krumminga (6.672).
Er omsyna skilde, er kovariansen delt i blokker. Kvar blokk er eitt omsyn. 2.122: eit trykk som er likt
over alle tilfelle, forklarer ingen skilnad. 1.6101: ein regel byter ut ei delform med ei anna.

  S1  To former: understellet føreseier ikkje overdelen, men det føreseier setesona.
  S2  Setet har ingen alder: setesona daterer ikkje stolen, overdelen gjer det.
  S3  Kimærar: understell frå éin stol og overdel frå ein annan, med minst 150 år mellom,
      ligg blant dei verkelege stolane.

Tersklane er faste tal, sette frå opplæringshalvparten (DEV) 13.11.2026 med regelen som står ved kvar.
Køyr frå repo-rota:  python analyse/forsegla2/t6_saumar.py     (berre DEV og syntetiske populasjonar)
"""
import json, os, sys
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import felles

NR = 140
SONER = {"understell": (2, 36), "setesone": (38, 58), "overdel": (62, 125)}
N_BOOT = 500                      # kvar oppattaking gjer ny kryssvalidering; 500 held for intervalla
N_KIM = 600

SPEC = {
    "id": "S",
    "tittel": "To former møtest i setet",
    "slag": "ny",
    "proposisjonar": ["5.701", "6.672", "2.122", "1.6101", "1.2011"],
    "paastand": "Understell og overdel er to skilde blokker i kovariansen. Setesona er lik over alle stolar og ber difor ingen tid. "
                "Fordi setet er halde, kan halvdelane byttast på tvers av hundreår.",
    "utval": "Tilbakehaldne vaksenstolar med år, silhuett og godkjend kvalitet (felles.kvalitet). Trekk per cm over golvet: "
             "mengd materiale og utstrekning, framanfrå og frå sida. Soner: understell 2 til 36 cm, setesone 38 til 58, overdel 62 til 125.",
    "primaer": [
        {"namn": "S1 to former", "statistikk": "kryssvalidert forklart varians (5 fald, fald etter suite), innan 50-årsbolk og museum: "
                                               "understell -> overdel (a) og understell -> setesone (b)",
         "terskel": "a <= 0.15 og b - a >= 0.15, med nedre 95 %-grense for b - a over 0",
         "regel_for_terskel": "a: om lag to gonger DEV-verdien (0.07); b - a: om lag halve DEV-skilnaden (0.32)",
         "dev_verdi": "sjå opplaeringstal"},
        {"namn": "S2 setet har ingen alder", "statistikk": "kryssvalidert median absolutt dateringsfeil per sone, delt på feilen ved å gisse medianåret",
         "terskel": "setesone >= 0.90 og overdel <= 0.80",
         "regel_for_terskel": "setesona skal ikkje slå gissing med meir enn ti prosent; overdelen skal slå gissing med minst tjue (DEV: om lag 1.1 og 0.6)",
         "dev_verdi": "sjå opplaeringstal"},
        {"namn": "S3 kimærar", "statistikk": "del av 600 kimærar med minst 150 år mellom halvdelane som ligg innanfor 95-persentilen "
                                             "av avstanden frå ein verkeleg stol til næraste andre verkelege stol (15 hovudkomponentar, suitefeller haldne utanfor)",
         "terskel": ">= 0.85",
         "regel_for_terskel": "DEV-verdien minus ti prosentpoeng",
         "dev_verdi": "sjå opplaeringstal"},
    ],
    "sekundaer": ["same tal over alle år utan periodejustering", "overdel -> understell", "dateringsfeil for understellet og for heile stolen",
                  "dateringsfeil for eit 12 cm band etter høgd over golvet", "kimærar med høgst 30 år mellom halvdelane", "per museum"],
    "port": [{"namn": "instrumentet ser samanheng der han finst", "terskel": "understell -> setesone >= 0.15", "ugyldig_dersom": "under terskelen: S1 er UGYLDIG"},
             {"namn": "nok stolar", "terskel": "minst 300 stolar og minst 100 før 1800 og 100 frå 1900", "ugyldig_dersom": "færre: S1, S2 og S3 er UGYLDIGE"}],
    "grunnmodell": "Stil som heilskap: understellet føreseier overdelen om lag like godt som setesona (b - a nær 0), alle soner daterer stolen "
                   "like godt, og kimærar på tvers av 150 år fell utanfor dei verkelege stolane.",
    "tel_imot": "a over 0.15, b - a under 0.15, setesona daterer stolen, overdelen gjer det ikkje, eller under 85 % av kimærane ligg blant dei verkelege.",
}


# ---------------------------------------------------------------- trekk
def radtrekk(side, front):
    ut = []
    for img in (front, side):
        img = np.asarray(img[:NR], np.float32)
        occ = img > 0.5
        an = occ.any(1)
        f = np.where(an, occ.argmax(1), 0)
        l = np.where(an, 159 - occ[:, ::-1].argmax(1), 0)
        ut += [img.sum(1), np.where(an, l - f + 1, 0).astype(np.float32)]
    return np.array(ut)


def utval(namn):
    R, S = felles.les(namn), felles.silhuett(namn)
    ut, fraafall = [], {"utan år": 0, "utan silhuett": 0, "kvalitet": 0}
    for r in R:
        if r["aar"] is None:
            fraafall["utan år"] += 1
        elif r["id"] not in S:
            fraafall["utan silhuett"] += 1
        elif not felles.kvalitet(r, *S[r["id"]])[0]:
            fraafall["kvalitet"] += 1
        else:
            ut.append(dict(r, side=np.asarray(S[r["id"]][0], np.uint8), front=np.asarray(S[r["id"]][1], np.uint8)))
    return ut, fraafall


def pca(M, maxk=8, andel=0.85):
    M = M - M.mean(0)
    sd = M.std(0)
    M = M[:, sd > 1e-6] / sd[sd > 1e-6]
    U, sv, _ = np.linalg.svd(M, full_matrices=False)
    v = sv ** 2 / max((sv ** 2).sum(), 1e-12)
    k = int(min(maxk, np.searchsorted(np.cumsum(v), andel) + 1))
    return U[:, :k] * sv[:k], v[:k]


def kv_pred(P, y, fald):
    pred = np.zeros(len(y))
    for f in np.unique(fald):
        tr, te = fald != f, fald == f
        b, *_ = np.linalg.lstsq(np.column_stack([np.ones(tr.sum()), P[tr]]), y[tr], rcond=None)
        pred[te] = np.column_stack([np.ones(te.sum()), P[te]]) @ b
    return pred


def innan_periode(M, aar, museum):
    b = np.clip(aar, 1550, 1999) // 50
    D = np.column_stack([(b == k).astype(float) for k in np.unique(b)] + [(museum == "NM").astype(float)])
    beta, *_ = np.linalg.lstsq(D, M, rcond=None)
    return M - D @ beta


def forklart(X, a, b, fald):
    n = len(X)
    Pa, _ = pca(X[:, :, a[0]:a[1]].reshape(n, -1))
    Pb, vb = pca(X[:, :, b[0]:b[1]].reshape(n, -1))
    r2 = [1 - ((Pb[:, j] - kv_pred(Pa, Pb[:, j], fald)) ** 2).sum() / max(((Pb[:, j] - Pb[:, j].mean()) ** 2).sum(), 1e-12)
          for j in range(Pb.shape[1])]
    return float((np.clip(r2, 0, 1) * vb).sum() / vb.sum())


def fald_etter_suite(suitar, rng):
    unike = sorted(set(suitar))
    nr = dict(zip(unike, rng.permutation(len(unike)) % 5))
    return np.array([nr[s] for s in suitar])


def s1(X, aar, museum, suitar, rng, innan=True):
    Xs = innan_periode(X.reshape(len(X), -1), aar, museum).reshape(X.shape) if innan else X
    fald = fald_etter_suite(suitar, rng)
    a = forklart(Xs, SONER["understell"], SONER["overdel"], fald)
    b = forklart(Xs, SONER["understell"], SONER["setesone"], fald)
    c = forklart(Xs, SONER["overdel"], SONER["understell"], fald)
    return a, b, c


def dateringsfeil(X, aar, suitar, rng, band):
    n = len(X)
    P, _ = pca(X[:, :, band[0]:band[1]].reshape(n, -1), maxk=10, andel=0.9)
    return float(np.median(np.abs(aar - kv_pred(P, aar, fald_etter_suite(suitar, rng)))))


# ---------------------------------------------------------------- kimærar
def _sete_i_riss(img, s):
    k = np.where(img[max(int(s) - 4, 0):int(s)].any(0))[0]
    return (int(k[0]), int(k[-1]) - int(k[0]) + 1) if len(k) else (60, 45)


def kimaer(A, B, kva):
    """Understell og sete frå A, alt over setet frå B: flytt til setehøgda til A og skalert til setet til A."""
    a, b = A[kva], B[kva]
    sa, sb = int(round(A["sete_mesh"])), int(round(B["sete_mesh"]))
    xa, da = _sete_i_riss(a, sa)
    xb, db = _sete_i_riss(b, sb)
    f = da / max(db, 1)
    ny = cv2.resize(b[sb:], None, fx=f, fy=1, interpolation=cv2.INTER_NEAREST)
    ut = np.zeros((200, 160), np.uint8)
    ut[:sa] = a[:sa]
    x0 = int(round(xa - xb * f))
    h = min(ny.shape[0], 200 - sa)
    aa, bb = max(x0, 0), min(x0 + ny.shape[1], 160)
    if bb > aa:
        ut[sa:sa + h, aa:bb] |= ny[:h, aa - x0:bb - x0]
    return ut


def s3(stolar, rng, par=None):
    OK = [s for s in stolar if s["sete_mesh"] and 34 <= s["sete_mesh"] <= 56]
    R = np.array([radtrekk(s["side"], s["front"]).ravel() for s in OK])
    mu, sd = R.mean(0), R.std(0)
    okc = sd > 1e-6
    _, sv, Vt = np.linalg.svd((R - mu)[:, okc] / sd[okc], full_matrices=False)
    proj = lambda M: (((M - mu)[:, okc] / sd[okc]) @ Vt[:15].T) / sv[:15] * np.sqrt(len(R))
    PR = proj(R)
    suite = {}
    for i, s in enumerate(OK):
        suite.setdefault(s["suite"], set()).add(i)

    def naeraste(p, utan):
        d = np.sqrt(((PR - p) ** 2).sum(1))
        d[list(utan)] = np.inf
        return float(d.min())

    ekte = np.array([naeraste(PR[i], suite[OK[i]["suite"]]) for i in range(len(OK))])
    q95 = float(np.quantile(ekte, 0.95))
    ut = {"n_stolar": len(OK), "ekte_median": float(np.median(ekte)), "ekte_q95": q95}
    for namn, test in (("ulik_tid", lambda dt: dt >= 150), ("same_tid", lambda dt: dt <= 30)):
        v, forsok = [], 0
        while len(v) < N_KIM and forsok < 200000:
            forsok += 1
            i, j = (rng.choice(len(OK), 2, replace=False) if par is None else par(OK, rng))
            if not test(abs(OK[i]["aar"] - OK[j]["aar"])):
                continue
            k = radtrekk(kimaer(OK[i], OK[j], "side"), kimaer(OK[i], OK[j], "front")).ravel()
            v.append(naeraste(proj(k[None])[0], suite[OK[i]["suite"]] | suite[OK[j]["suite"]]))
        ut[namn] = {"n": len(v), "median": float(np.median(v)) if v else None, "innanfor": float(np.mean(np.array(v) <= q95)) if v else None}
    return ut


# ---------------------------------------------------------------- skåring
def skaar(stolar, fraafall=None, boot=True):
    rng = np.random.default_rng(felles.FRO)
    n = len(stolar)
    aar = np.array([s["aar"] for s in stolar], float)
    museum = np.array([s["museum"] for s in stolar])
    suitar = [s["suite"] for s in stolar]
    X = np.array([radtrekk(s["side"], s["front"]) for s in stolar])
    port_n = n >= 300 and (aar < 1800).sum() >= 100 and (aar >= 1900).sum() >= 100
    a, b, c = s1(X, aar, museum, suitar, rng)
    raa = s1(X, aar, museum, suitar, rng, innan=False)
    lo = None
    if boot:
        unike = sorted(set(suitar))
        idx = {u: [i for i, s in enumerate(suitar) if s == u] for u in unike}
        d = []
        for _ in range(N_BOOT):
            trekk = rng.choice(len(unike), len(unike))
            ii = np.concatenate([idx[unike[t]] for t in trekk])
            ss = ["%d" % t for t in trekk for _ in idx[unike[t]]]          # same suite, same fald
            aa, bb, _ = s1(X[ii], aar[ii], museum[ii], ss, rng)
            d.append(bb - aa)
        lo = float(np.quantile(d, 0.025))
    gissing = float(np.median(np.abs(aar - np.median(aar))))
    dat = {k: dateringsfeil(X, aar, suitar, rng, v) for k, v in SONER.items()}
    dat["heile"] = dateringsfeil(X, aar, suitar, rng, (2, 125))
    kurve = [[cc, round(dateringsfeil(X, aar, suitar, rng, (cc - 6, cc + 6)), 1)] for cc in range(8, 121, 4)]
    kim = s3(stolar, rng)
    port_s1 = b >= 0.15
    h1 = a <= 0.15 and (b - a) >= 0.15 and (lo is None or lo > 0)
    h2 = dat["setesone"] / gissing >= 0.90 and dat["overdel"] / gissing <= 0.80
    h3 = kim["ulik_tid"]["innanfor"] is not None and kim["ulik_tid"]["innanfor"] >= 0.85
    dom = lambda held, gyldig: "UGYLDIG" if not gyldig else ("HELDT" if held else "SLO FEIL")
    return {
        "id": "S", "n": n, "fraafall": fraafall or {},
        "port": [{"namn": "nok stolar", "verdi": [n, int((aar < 1800).sum()), int((aar >= 1900).sum())], "ok": bool(port_n)},
                 {"namn": "instrumentet ser samanheng der han finst", "verdi": round(b, 3), "ok": bool(port_s1)}],
        "primaer": [
            {"namn": "S1 to former", "verdi": {"understell->overdel": round(a, 3), "understell->setesone": round(b, 3), "skilnad": round(b - a, 3)},
             "ki95_nedre_skilnad": None if lo is None else round(lo, 3), "terskel": "a <= 0.15, b - a >= 0.15, nedre grense > 0",
             "held": bool(h1), "dom": dom(h1, port_n and port_s1)},
            {"namn": "S2 setet har ingen alder", "verdi": {"setesone/gissing": round(dat["setesone"] / gissing, 3), "overdel/gissing": round(dat["overdel"] / gissing, 3)},
             "terskel": "setesone >= 0.90, overdel <= 0.80", "held": bool(h2), "dom": dom(h2, port_n)},
            {"namn": "S3 kimærar", "verdi": kim["ulik_tid"], "terskel": ">= 0.85", "held": bool(h3), "dom": dom(h3, port_n)},
        ],
        "sekundaer": {"over alle år (a, b, overdel->understell)": [round(v, 3) for v in raa], "overdel->understell": round(c, 3),
                      "dateringsfeil_aar": {**{k: round(v, 1) for k, v in dat.items()}, "gissing": round(gissing, 1)},
                      "tidskurve": kurve, "kimaerar": kim,
                      "per_museum": {m: int((museum == m).sum()) for m in sorted(set(museum))}},
        "dom": " | ".join("%s %s" % (p, d) for p, d in (("S1", dom(h1, port_n and port_s1)), ("S2", dom(h2, port_n)), ("S3", dom(h3, port_n)))),
    }


def kjoer(namn):
    stolar, fraafall = utval(namn)
    res = skaar(stolar, fraafall)
    res["utval"] = namn
    return res


def figurdata(namn):
    stolar, _ = utval(namn)
    P = np.mean([s["side"] for s in stolar], axis=0)[:146, 30:130]
    P = cv2.resize(P.astype(np.float32), (50, 73), interpolation=cv2.INTER_AREA)
    return {"n": len(stolar), "stabel_side_2cm": np.round(P[::-1] * 255).astype(int).tolist()}


def syntetisk_kontroll():
    """(a) Stil som heilskap: kvar stol får overdelen frå stolen med same rang langs første hovudkomponent, så halvdelane
    heng saman. S1 skal ikkje halde. (b) Uavhengige halvdelar: overdelane er stokka tilfeldig innan 50-årsbolk. Då skal
    understellet ikkje føreseie overdelen (a <= 0.15). Setesona i ein kimære kjem delvis frå overdelen, så b er ikkje meint å halde her."""
    stolar, _ = utval("dev")
    OK = [s for s in stolar if s["sete_mesh"] and 34 <= s["sete_mesh"] <= 56]
    rng = np.random.default_rng(felles.FRO + 1)
    X = np.array([radtrekk(s["side"], s["front"]) for s in OK])
    n = len(OK)
    pu, _ = pca(X[:, :, 2:36].reshape(n, -1), maxk=1, andel=1.0)
    po, _ = pca(X[:, :, 62:125].reshape(n, -1), maxk=1, andel=1.0)
    ru, ro = np.argsort(pu[:, 0]), np.argsort(po[:, 0])
    ut = {}
    for namn, makker in (("a_heilskap", dict(zip(ru, ro))),
                         ("b_uavhengig", None)):
        ny = []
        for i, s in enumerate(OK):
            if makker is None:
                kand = [j for j in range(n) if abs(OK[j]["aar"] - s["aar"]) <= 25 and j != i] or [i]
                j = int(rng.choice(kand))
            else:
                j = int(makker[i])
            ny.append(dict(s, side=kimaer(s, OK[j], "side"), front=kimaer(s, OK[j], "front"), suite="syn%d" % i))
        r = skaar(ny, boot=False)
        a = r["primaer"][0]["verdi"]["understell->overdel"]
        ut[namn] = {"S1": r["primaer"][0]["verdi"], "held": r["primaer"][0]["held"], "a_innanfor_terskel": bool(a <= 0.15)}
    return ut


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(kjoer("dev"), ensure_ascii=False, indent=1, default=float))
    print(json.dumps(syntetisk_kontroll(), ensure_ascii=False, indent=1, default=float))
