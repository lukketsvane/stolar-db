"""26_to_alder.py - den fjerde forsegla prøva: har overdelen og understellet ulik alder?

Skriptet og forsegla4/FORESEIINGAR.json er pusha FØR delta er rekna for nokon stol.
Skriptet skal ikkje endrast etterpå; avvik blir førte i forsegla4/RESULTAT.json.

  python analyse/26_to_alder.py      Nektar om fila eller skriptet ikkje ligg uendra i ein pusha commit,
                                     eller om RESULTAT.json alt finst. Skriv RESULTAT.json og FIGURDATA.json.
"""
import csv, datetime, json, os, re, subprocess, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.dirname(HER)
F4 = os.path.join(HER, "forsegla4")
P_FORE, P_RES, P_FIG = (os.path.join(F4, f) for f in ("FORESEIINGAR.json", "RESULTAT.json", "FIGURDATA.json"))
F = json.load(open(P_FORE, encoding="utf-8"))
K, NR = 7, 140
SONER = F["maal"]["soner"]
ATTOPP = {"Historisme", "Nyrokokko", "Nybarokk", "Dragestil", "Renessanse", "Barokk", "Régence", "Rokokko", "Chippendale",
          "Chippendale / Rokokko", "Queen Anne", "Louis XVI", "Nyklassisisme", "Hepplewhite", "Sheraton", "Klassisisme", "Middelalder"}


def git(*a):
    return subprocess.run(["git", "-C", ROT] + list(a), capture_output=True, text=True, encoding="utf-8")


def sjekk_forsegla():
    for rel in ("analyse/forsegla4/FORESEIINGAR.json", "analyse/26_to_alder.py"):
        c = git("log", "-1", "--format=%H", "--", rel).stdout.strip()
        if not c:
            sys.exit("Stoppa: %s er ikkje committa." % rel)
        if git("show", "%s:%s" % (c, rel)).stdout.replace("\r\n", "\n").encode("utf-8") != open(os.path.join(ROT, rel), "rb").read().replace(b"\r\n", b"\n"):
            sys.exit("Stoppa: %s er endra etter siste commit." % rel)
        if not git("branch", "-r", "--contains", c).stdout.strip():
            sys.exit("Stoppa: commiten %s med %s er ikkje pusha." % (c[:8], rel))
    return git("log", "-1", "--format=%H", "--", "analyse/forsegla4/FORESEIINGAR.json").stdout.strip()


def utstr(img):
    k = np.where(img.any(0))[0]
    r = np.where(img.any(1))[0]
    return (int(k[0]), int(k[-1]), int(r[0]), int(r[-1])) if len(k) else (0, 0, 0, 0)


def radtrekk(side, front):
    ut = []
    for img in (front, side):
        img = img[:NR].astype(np.float32)
        occ = img > 0.5
        an = occ.any(1)
        f = np.where(an, occ.argmax(1), 0)
        l = np.where(an, 159 - occ[:, ::-1].argmax(1), 0)
        ut += [img.sum(1), np.where(an, l - f + 1, 0).astype(np.float32)]
    return np.array(ut)


def last():
    rein = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "stolar_reinsa.csv"), encoding="utf-8-sig"))}
    maal = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "mesh_maal.csv"), encoding="utf-8"))}
    z = np.load(os.path.join(HER, "data", "mesh_silhuettar.npz"))
    side = dict(zip(z["ids"], np.unpackbits(z["side"], axis=-1)))
    front = dict(zip(z["ids"], np.unpackbits(z["front"], axis=-1)))
    S = []
    for cid in side:
        r, m = rein.get(cid), maal.get(cid)
        if not r or not m or r["vaksenstol"] != "1" or not r["aar_fraa"] or float(r["aar_fraa"]) < 1000:
            continue
        if set(filter(None, (m.get("flagg") or "").split(";"))) & {"opp_ikkje_y", "opp_ned?", "silhuett_klipt"}:
            continue
        H, B, D = float(r["H"]), float(r["B"]), float(r["D"])
        k0, k1, r0, r1 = utstr(side[cid])
        f0, f1, _, _ = utstr(front[cid])
        if (k1 - k0) > 1.5 * D + 10 or (f1 - f0) > 1.5 * B + 10 or abs(r1 + 1 - H) > 6:
            continue
        aar, stil = int(float(r["aar_fraa"])), (r["stil"] or "").strip()
        g = ("attopptaking" if stil in ATTOPP else "viktoriansk" if stil == "Viktorianisme" else "samtidige") if 1830 <= aar <= 1914 else "anna"
        S.append({"id": cid, "aar": aar, "stil": stil, "gruppe": g, "museum": r["museum"], "type": r["type"], "H": H, "B": B,
                  "sete": float(m["sete_cm"]) if m.get("sete_cm") else None})
    X = np.array([radtrekk(side[s["id"]], front[s["id"]]) for s in S])
    return S, X


def rom(X, bak, lo, hi):
    M = X[:, :, lo:hi].reshape(len(X), -1)
    mu, sd = M[bak].mean(0), M[bak].std(0)
    ok = sd > 1e-6
    Z = (M[:, ok] - mu[ok]) / sd[ok]
    _, sv, Vt = np.linalg.svd(Z[bak], full_matrices=False)
    v = sv ** 2 / (sv ** 2).sum()
    k = int(min(10, np.searchsorted(np.cumsum(v), 0.90) + 1))
    return Z @ Vt[:k].T, k


def alder(P, bak, aar, sett):
    bi = np.where(bak)[0]
    ut = np.zeros(len(P))
    nabo = []
    for i in range(len(P)):
        d = np.sqrt(((P[bi] - P[i]) ** 2).sum(1))
        d[np.isin(bi, list(sett[i]))] = np.inf
        o = np.argsort(d)[:K]
        ut[i] = np.median(aar[bi[o]])
        nabo.append([int(bi[j]) for j in o])
    return ut, nabo


def boot_median(x, rng, n):
    b = np.array([np.median(rng.choice(x, len(x))) for _ in range(n)])
    return float(np.median(x)), float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))


def boot_diff(x, y, rng, n):
    b = np.array([np.median(rng.choice(x, len(x))) - np.median(rng.choice(y, len(y))) for _ in range(n)])
    return float(np.median(x) - np.median(y)), float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))


if __name__ == "__main__":
    seal = sjekk_forsegla()
    if os.path.exists(P_RES):
        sys.exit("Stoppa: RESULTAT.json finst alt. Prøva er køyrd.")
    S, X = last()
    aar = np.array([s["aar"] for s in S], float)
    gr = np.array([s["gruppe"] for s in S])
    bak = (gr == "anna") | (gr == "samtidige")
    stamme = lambda i: re.sub(r"[A-Za-z]$|-\d+$", "", i)
    sam = {}
    for i, s in enumerate(S):
        sam.setdefault((stamme(s["id"]), s["H"], s["B"]), set()).add(i)
    sett = [sam[(stamme(s["id"]), s["H"], s["B"])] for s in S]
    AL, NABO, KOMP = {}, {}, {}
    for namn, (lo, hi) in SONER.items():
        P, KOMP[namn] = rom(X, bak, lo, hi)
        AL[namn], NABO[namn] = alder(P, bak, aar, sett)
    delta = AL["overdel"] - AL["understell"]
    rng = np.random.default_rng(F["froe"])
    NB = F["n_boot"]
    g = {k: delta[gr == k] for k in ("attopptaking", "viktoriansk", "samtidige")}
    n = {k: int(len(v)) for k, v in g.items()}
    R = {}
    port12 = n["attopptaking"] >= 60 and n["samtidige"] >= 40
    m1 = boot_median(g["attopptaking"], rng, NB)
    R["T1_overdelen_er_eldre"] = {"median": m1[0], "ki95": [m1[1], m1[2]], "n": n["attopptaking"],
                                  "dom": "UGYLDIG" if not port12 else "HELDT" if m1[0] <= -20 and m1[2] < 0 else "SLO FEIL"}
    m2 = boot_diff(g["attopptaking"], g["samtidige"], rng, NB)
    R["T2_ikkje_tida"] = {"differanse": m2[0], "ki95": [m2[1], m2[2]], "median_samtidige": float(np.median(g["samtidige"])),
                          "n": [n["attopptaking"], n["samtidige"]],
                          "dom": "UGYLDIG" if not port12 else "HELDT" if m2[0] <= -20 and m2[2] < 0 else "SLO FEIL"}
    m3 = boot_median(g["viktoriansk"], rng, NB)
    R["T3_viktoriansk"] = {"median": m3[0], "ki95": [m3[1], m3[2]], "n": n["viktoriansk"],
                           "dom": "UGYLDIG" if n["viktoriansk"] < 40 else "HELDT" if m3[0] < 0 and m3[2] < 0 else "SLO FEIL"}
    ut = {"tid": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "forsegla_commit": seal,
          "n_stolar": len(S), "n_bakgrunn": int(bak.sum()), "komponentar": KOMP, "resultat": R,
          "median_absolutt_feil_bakgrunn": {z: float(np.median(np.abs(AL[z][bak] - aar[bak]))) for z in SONER},
          "avvik": []}
    json.dump(ut, open(P_RES, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    json.dump({"stolar": [{"id": s["id"], "aar": s["aar"], "stil": s["stil"], "gruppe": s["gruppe"], "museum": s["museum"],
                           "type": s["type"], "sete": s["sete"], "overdel": float(AL["overdel"][i]), "understell": float(AL["understell"][i]),
                           "nabo_overdel": [S[j]["id"] for j in NABO["overdel"][i]], "nabo_understell": [S[j]["id"] for j in NABO["understell"][i]]}
                          for i, s in enumerate(S)]},
              open(P_FIG, "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
    print(json.dumps(ut, ensure_ascii=False, indent=1))
