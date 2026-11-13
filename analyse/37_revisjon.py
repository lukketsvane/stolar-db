"""37_revisjon.py - revisjon av dei opne grunntala på heile ramma (1 410 stolar), med suitar haldne samla
i kryssvalideringa, per museum, og med placebo. Ingen nye hypotesar: dette er dei same storleikane som i
19_saumar.py og t6, rekna om med strengare reglar.

  python analyse/37_revisjon.py   -> analyse/data/revisjon.json
"""
import json, os, sys
import numpy as np
import ramme

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
R = ramme.last()
n = len(R["id"])
X = R["trekk"]                                    # (n, 4, 140)
aar = R["aar"].astype(float)
mus = R["museum"]
fald = ramme.suitefald(R["suite"])
SONER = dict(ramme.SONER, heile=(2, 125))


def pca(M, maxk=10, andel=0.9):
    M = M - M.mean(0)
    sd = M.std(0)
    M = M[:, sd > 1e-6] / sd[sd > 1e-6]
    U, sv, _ = np.linalg.svd(M, full_matrices=False)
    v = sv ** 2 / (sv ** 2).sum()
    k = int(min(maxk, np.searchsorted(np.cumsum(v), andel) + 1))
    return U[:, :k] * sv[:k], v[:k]


def kv(P, y, f):
    pred = np.zeros(len(y))
    for k in np.unique(f):
        tr, te = f != k, f == k
        b, *_ = np.linalg.lstsq(np.column_stack([np.ones(tr.sum()), P[tr]]), y[tr], rcond=None)
        pred[te] = np.column_stack([np.ones(te.sum()), P[te]]) @ b
    return pred


def dateringsfeil(idx, y=None):
    """Median absolutt feil i år per sone, og for gissing (medianåret i treningsfalda)."""
    y = aar[idx] if y is None else y
    f = fald[idx]
    ut = {}
    for namn, (lo, hi) in SONER.items():
        P, _ = pca(X[idx][:, :, lo:hi].reshape(len(idx), -1))
        ut[namn] = float(np.median(np.abs(y - kv(P, y, f))))
    g = np.zeros(len(idx))
    for k in np.unique(f):
        g[f == k] = np.median(y[f != k])
    ut["gissing"] = float(np.median(np.abs(y - g)))
    return ut


def residual(M, idx):
    b = np.array([min(max(a, 1550), 1999) // 50 for a in aar[idx]])
    kol = [(b == k).astype(float) for k in np.unique(b)]
    if len(set(mus[idx])) > 1:
        kol.append((mus[idx] == "NM").astype(float))
    Dm = np.column_stack(kol)
    beta, *_ = np.linalg.lstsq(Dm, M, rcond=None)
    return M - Dm @ beta


def forklart(idx, a, b, perm=None):
    """Kryssvalidert del av variansen i sone b som sone a føreseier, innan 50-årsbolk og museum."""
    Xr = residual(X[idx].reshape(len(idx), -1), idx).reshape(len(idx), 4, -1)
    Pa, _ = pca(Xr[:, :, a[0]:a[1]].reshape(len(idx), -1), maxk=8, andel=0.85)
    Pb, vb = pca(Xr[:, :, b[0]:b[1]].reshape(len(idx), -1), maxk=8, andel=0.85)
    if perm is not None:
        Pb = Pb[perm]
    f = fald[idx]
    r2 = [1 - ((Pb[:, j] - kv(Pa, Pb[:, j], f)) ** 2).sum() / ((Pb[:, j] - Pb[:, j].mean()) ** 2).sum() for j in range(Pb.shape[1])]
    return float((np.clip(r2, 0, 1) * vb).sum() / vb.sum())


ut = {"n": n, "suitar": int(len(set(R["suite"])))}
alle = np.arange(n)
grupper = {"samla": alle, "VA": np.where(mus == "VA")[0], "NM": np.where(mus == "NM")[0]}
ut["datering"] = {g: dict(dateringsfeil(i), n=int(len(i))) for g, i in grupper.items()}
rng = np.random.default_rng(20261113)
pl = [dateringsfeil(alle, ramme.perm_innan(aar, mus, rng)) for _ in range(40)]
ut["datering_placebo"] = {k: [float(np.quantile([p[k] for p in pl], q)) for q in (0.025, 0.5, 0.975)] for k in pl[0]}
par = [("understell", "setesone"), ("understell", "overdel"), ("setesone", "overdel"), ("overdel", "understell")]
ut["forklart"] = {g: {a + "->" + b: forklart(i, ramme.SONER[a], ramme.SONER[b]) for a, b in par} for g, i in grupper.items()}
plf = {a + "->" + b: [] for a, b in par}
strata = np.array(["%s|%d" % (m, min(max(a, 1550), 1999) // 50) for m, a in zip(mus, aar)])
for _ in range(40):
    p = ramme.perm_innan(alle, strata, rng)
    for a, b in par:
        plf[a + "->" + b].append(forklart(alle, ramme.SONER[a], ramme.SONER[b], perm=p))
ut["forklart_placebo"] = {k: [float(np.quantile(v, q)) for q in (0.025, 0.5, 0.975)] for k, v in plf.items()}
json.dump(ut, open(os.path.join(HER, "data", "revisjon.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print(json.dumps(ut, ensure_ascii=False, indent=1))
