"""36_fortid_framtid.py - den niande forsegla prøva: liknar dei nyskapande stolane fortida eller framtida?

Heile samlinga. Skriptet og forsegla9/FORESEIINGAR.json er pusha FØR nokon nabo er rekna.

  python analyse/36_fortid_framtid.py   Skriv forsegla9/RESULTAT.json og FIGURDATA.json.
"""
import csv, datetime, importlib.util, json, os, re, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
F9 = os.path.join(HER, "forsegla9")
P_FORE, P_RES, P_FIG = (os.path.join(F9, f) for f in ("FORESEIINGAR.json", "RESULTAT.json", "FIGURDATA.json"))
F = json.load(open(P_FORE, encoding="utf-8"))
_s = importlib.util.spec_from_file_location("to_alder", os.path.join(HER, "26_to_alder.py"))
TA = importlib.util.module_from_spec(_s)
_s.loader.exec_module(TA)
UTE_STIL = {"Historisme", "Nyrokokko", "Nybarokk", "Dragestil", "Postmodernisme", "Memphis / Postmodernisme"}
KOPI = re.compile(r"kopi|reproduksjon|replica|copy of|rekonstruksjon", re.I)
K = 7


def sjekk_forsegla():
    for rel in ("analyse/forsegla9/FORESEIINGAR.json", "analyse/36_fortid_framtid.py"):
        c = TA.git("log", "-1", "--format=%H", "--", rel).stdout.strip()
        if not c:
            sys.exit("Stoppa: %s er ikkje committa." % rel)
        if TA.git("show", "%s:%s" % (c, rel)).stdout.replace("\r\n", "\n").encode("utf-8") != open(os.path.join(TA.ROT, rel), "rb").read().replace(b"\r\n", b"\n"):
            sys.exit("Stoppa: %s er endra etter siste commit." % rel)
        if not TA.git("branch", "-r", "--contains", c).stdout.strip():
            sys.exit("Stoppa: commiten %s med %s er ikkje pusha." % (c[:8], rel))
    return TA.git("log", "-1", "--format=%H", "--", "analyse/forsegla9/FORESEIINGAR.json").stdout.strip()


def boot(x, rng, n):
    x = np.asarray(x, float)
    b = np.array([x[rng.integers(0, len(x), len(x))].mean() for _ in range(n)])
    return [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))]


if __name__ == "__main__":
    seal = sjekk_forsegla()
    if os.path.exists(P_RES):
        sys.exit("Stoppa: RESULTAT.json finst alt. Prøva er køyrd.")
    ST = {r["Objekt-ID"]: r for r in csv.DictReader(open(os.path.join(TA.ROT, "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline=""))}
    S, X = TA.last()
    n = len(S)
    M = X[:, :, 2:125].reshape(n, -1)
    mu, sd = M.mean(0), M.std(0)
    ok = sd > 1e-6
    Z = (M[:, ok] - mu[ok]) / sd[ok]
    _, sv, Vt = np.linalg.svd(Z, full_matrices=False)
    P = Z @ Vt[:15].T
    aar = np.array([s["aar"] for s in S])
    namn = [(ST.get(s["id"], {}).get("Namn") or "") for s in S]
    stamme = np.array([re.sub(r"[A-Za-z]$|-\d+$", "", s["id"]) for s in S])
    nokkel = np.array(["%s|%s|%s" % (s["museum"], s["H"], s["B"]) for s in S])
    rad = []
    for i in range(n):
        if S[i]["stil"] in UTE_STIL or KOPI.search(namn[i]):
            continue
        annan = (stamme != stamme[i]) & (nokkel != nokkel[i])
        dt = aar - aar[i]
        eldre, yngre = annan & (dt <= -25), annan & (dt >= 25)
        naer = np.where(annan & (dt <= -5) & (dt >= -80))[0]
        if (aar <= aar[i] - 25).sum() < 30 or (aar >= aar[i] + 25).sum() < 30 or ((dt <= -5) & (dt >= -80)).sum() < 30 or len(naer) < 1:
            continue
        naer = naer[np.argsort(-aar[naer], kind="stable")][:60]
        d_all = np.sqrt(((P - P[i]) ** 2).sum(1))
        pool = np.where(eldre | yngre)[0]
        nb = pool[np.argsort(d_all[pool], kind="stable")][:K]
        rad.append({"i": i, "ny": float(d_all[naer].min()), "nb": nb, "p_eldre": float(eldre.sum() / len(pool)),
                    "a_eldre": float((aar[nb] < aar[i]).mean()), "a_djup": float((aar[nb] <= aar[i] - 100).mean()),
                    "p_djup": float((annan & (dt <= -100)).sum() / len(pool))})
    bolk = np.array([aar[r["i"]] // 50 for r in rad])
    nyh = np.array([r["ny"] for r in rad])
    kvint = np.zeros(len(rad), int)
    for b in np.unique(bolk):
        k = np.where(bolk == b)[0]
        rang = np.argsort(np.argsort(nyh[k], kind="stable"), kind="stable")
        kvint[k] = np.minimum(4, (5 * rang) // len(k))
    e = np.array([r["a_eldre"] - r["p_eldre"] for r in rad])
    ed = np.array([r["a_djup"] - r["p_djup"] for r in rad])
    ya = np.array([aar[r["i"]] for r in rad])
    nye = kvint == 4
    rng = np.random.default_rng(F["froe"])
    gyldig = int(nye.sum()) >= 150
    dom = lambda okk: "UGYLDIG" if not gyldig else "HELDT" if okk else "SLO FEIL"
    d1 = {"middel": float(e[nye].mean()), "ki95": boot(e[nye], rng, F["n_boot"]), "n": int(nye.sum())}
    foer, etter = nye & (ya < 1850), nye & (ya >= 1850)
    d2 = {"foer_1850": {"middel": float(e[foer].mean()), "ki95": boot(e[foer], rng, F["n_boot"]), "n": int(foer.sum())},
          "fraa_1850": {"middel": float(e[etter].mean()), "ki95": boot(e[etter], rng, F["n_boot"]), "n": int(etter.sum())}}
    R = {"D1_fortida": {**d1, "dom": dom(d1["middel"] > 0 and d1["ki95"][0] > 0)},
         "D2_begge_tider": {**d2, "dom": dom(d2["foer_1850"]["middel"] > 0 and d2["fraa_1850"]["middel"] > 0)}}
    sek = {"vanlege": {"middel": float(e[~nye].mean()), "ki95": boot(e[~nye], rng, F["n_boot"]), "n": int((~nye).sum())},
           "per_kvintil": [{"kvintil": q + 1, "middel": float(e[kvint == q].mean()), "ki95": boot(e[kvint == q], rng, F["n_boot"]), "n": int((kvint == q).sum())} for q in range(5)],
           "djup_nye": {"middel": float(ed[nye].mean()), "ki95": boot(ed[nye], rng, F["n_boot"])},
           "raa_nye": {"del_eldre_naboar": float(np.mean([r["a_eldre"] for r, v in zip(rad, nye) if v])),
                       "del_eldre_i_samlinga": float(np.mean([r["p_eldre"] for r, v in zip(rad, nye) if v]))}}
    ut = {"tid": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "forsegla_commit": seal,
          "n": {"samling": n, "maal": len(rad), "nye": int(nye.sum())}, "gyldig": gyldig, "resultat": R, "sekundaert": sek, "avvik": []}
    json.dump(ut, open(P_RES, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    json.dump({"stolar": [{"id": S[r["i"]]["id"], "aar": int(aar[r["i"]]), "kvintil": int(kvint[k]) + 1, "e": float(e[k]),
                           "naboar": [[S[j]["id"], int(aar[j])] for j in r["nb"]]} for k, r in enumerate(rad)]},
              open(P_FIG, "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
    print(json.dumps(ut, ensure_ascii=False, indent=1))
