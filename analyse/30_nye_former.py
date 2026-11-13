"""30_nye_former.py - den sjette forsegla prøva: held dei nyaste formene setet?

Skriptet og forsegla6/FORESEIINGAR.json er pusha FØR nyheit er rekna for nokon stol.
Skriptet skal ikkje endrast etterpå; avvik blir førte i forsegla6/RESULTAT.json.

  python analyse/30_nye_former.py   Nektar om fila eller skriptet ikkje ligg uendra i ein pusha commit,
                                    eller om RESULTAT.json alt finst. Skriv RESULTAT.json og FIGURDATA.json.
"""
import datetime, importlib.util, json, os, re, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
F6 = os.path.join(HER, "forsegla6")
P_FORE, P_RES, P_FIG = (os.path.join(F6, f) for f in ("FORESEIINGAR.json", "RESULTAT.json", "FIGURDATA.json"))
F = json.load(open(P_FORE, encoding="utf-8"))
_s = importlib.util.spec_from_file_location("to_alder", os.path.join(HER, "26_to_alder.py"))
TA = importlib.util.module_from_spec(_s)
_s.loader.exec_module(TA)                       # last(), radtrekk() og git() frå den fjerde prøva


def sjekk_forsegla():
    for rel in ("analyse/forsegla6/FORESEIINGAR.json", "analyse/30_nye_former.py"):
        c = TA.git("log", "-1", "--format=%H", "--", rel).stdout.strip()
        if not c:
            sys.exit("Stoppa: %s er ikkje committa." % rel)
        if TA.git("show", "%s:%s" % (c, rel)).stdout.replace("\r\n", "\n").encode("utf-8") != open(os.path.join(TA.ROT, rel), "rb").read().replace(b"\r\n", b"\n"):
            sys.exit("Stoppa: %s er endra etter siste commit." % rel)
        if not TA.git("branch", "-r", "--contains", c).stdout.strip():
            sys.exit("Stoppa: commiten %s med %s er ikkje pusha." % (c[:8], rel))
    return TA.git("log", "-1", "--format=%H", "--", "analyse/forsegla6/FORESEIINGAR.json").stdout.strip()


def spreiing(x):
    q1, q2, q3 = np.quantile(x, [0.25, 0.5, 0.75])
    return (q3 - q1) / q2


if __name__ == "__main__":
    seal = sjekk_forsegla()
    if os.path.exists(P_RES):
        sys.exit("Stoppa: RESULTAT.json finst alt. Prøva er køyrd.")
    S, X = TA.last()
    n = len(S)
    M = X[:, :, 2:125].reshape(n, -1)
    mu, sd = M.mean(0), M.std(0)
    ok = sd > 1e-6
    Z = (M[:, ok] - mu[ok]) / sd[ok]
    _, sv, Vt = np.linalg.svd(Z, full_matrices=False)
    P = Z @ Vt[:15].T
    aar = np.array([s["aar"] for s in S])
    stamme = [re.sub(r"[A-Za-z]$|-\d+$", "", s["id"]) for s in S]
    nokkel = [(s["museum"], s["H"], s["B"]) for s in S]
    maal = [i for i, s in enumerate(S) if s["aar"] >= 1900 and s["sete"]]
    ny, nabo = {}, {}
    for i in maal:
        kand = np.where(aar <= aar[i] - 10)[0]
        kand = np.array([j for j in kand if stamme[j] != stamme[i] and nokkel[j] != nokkel[i]])
        d = np.sqrt(((P[kand] - P[i]) ** 2).sum(1))
        ny[i] = float(d.min())
        nabo[i] = int(kand[np.argmin(d)])
    v = np.array([ny[i] for i in maal])
    grense = float(np.quantile(v, 0.80))
    nye = [i for i in maal if ny[i] > grense]
    resten = [i for i in maal if ny[i] <= grense]
    gyldig = len(nye) >= 60 and len(resten) >= 200
    sete = lambda idx: np.array([S[i]["sete"] for i in idx])
    hoegd = lambda idx: np.array([S[i]["H"] for i in idx])

    def stat(a, b):
        return spreiing(sete(a)) / spreiing(sete(b)), spreiing(hoegd(a)) / spreiing(hoegd(b))

    o1, o2 = stat(nye, resten)
    rng = np.random.default_rng(F["froe"])
    B1, B2 = [], []
    for _ in range(F["n_boot"]):
        a = [nye[k] for k in rng.integers(0, len(nye), len(nye))]
        b = [resten[k] for k in rng.integers(0, len(resten), len(resten))]
        x1, x2 = stat(a, b)
        B1.append(x1)
        B2.append(x2)
    k1 = [float(np.quantile(B1, 0.025)), float(np.quantile(B1, 0.975))]
    k2 = [float(np.quantile(B2, 0.025)), float(np.quantile(B2, 0.975))]
    dom = lambda okk: "UGYLDIG" if not gyldig else "HELDT" if okk else "SLO FEIL"
    R = {"N1_setet_held": {"forhold": float(o1), "ki95": k1, "dom": dom(o1 <= 1.25 and k1[1] < 1.6)},
         "N2_hoegda_slepp": {"forhold": float(o2), "ki95": k2, "dom": dom(o2 >= 1.5 and k2[0] > 1)},
         "N3_setet_held_fastare": {"forhold": float(o1), "dom": dom(o1 < 1)}}
    ut = {"tid": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "forsegla_commit": seal,
          "n": {"maal": len(maal), "nye": len(nye), "resten": len(resten)}, "gyldig": gyldig, "grense": grense, "resultat": R,
          "spreiing": {"nye_sete": float(spreiing(sete(nye))), "resten_sete": float(spreiing(sete(resten))),
                       "nye_H": float(spreiing(hoegd(nye))), "resten_H": float(spreiing(hoegd(resten)))},
          "median": {"nye_sete": float(np.median(sete(nye))), "resten_sete": float(np.median(sete(resten))),
                     "nye_H": float(np.median(hoegd(nye))), "resten_H": float(np.median(hoegd(resten)))},
          "avvik": []}
    json.dump(ut, open(P_RES, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    json.dump({"stolar": [{"id": S[i]["id"], "aar": S[i]["aar"], "sete": S[i]["sete"], "H": S[i]["H"], "type": S[i]["type"],
                           "nyheit": ny[i], "ny": ny[i] > grense, "nabo": S[nabo[i]]["id"], "nabo_aar": S[nabo[i]]["aar"]} for i in maal]},
              open(P_FIG, "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
    print(json.dumps(ut, ensure_ascii=False, indent=1))
