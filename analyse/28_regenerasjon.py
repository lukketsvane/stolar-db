"""28_regenerasjon.py - den femte forsegla prøva: samlar setehøgda seg att etter eit materialskifte?

Skriptet og forsegla5/FORESEIINGAR.json er pusha FØR nokon spreiing er rekna.
Skriptet skal ikkje endrast etterpå; avvik blir førte i forsegla5/RESULTAT.json.

  python analyse/28_regenerasjon.py    Nektar om fila eller skriptet ikkje ligg uendra i ein pusha commit,
                                       eller om RESULTAT.json alt finst. Skriv RESULTAT.json og FIGURDATA.json.
"""
import csv, datetime, importlib.util, json, os, re, subprocess, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.dirname(HER)
F5 = os.path.join(HER, "forsegla5")
P_FORE, P_RES, P_FIG = (os.path.join(F5, f) for f in ("FORESEIINGAR.json", "RESULTAT.json", "FIGURDATA.json"))
F = json.load(open(P_FORE, encoding="utf-8"))
_s = importlib.util.spec_from_file_location("felles", os.path.join(HER, "forsegla2", "felles.py"))
felles = importlib.util.module_from_spec(_s)
sys.path.insert(0, os.path.join(HER, "forsegla2"))
_s.loader.exec_module(felles)
NYE = {"LINE", "LINE+SHEET", "SHEET"}


def git(*a):
    return subprocess.run(["git", "-C", ROT] + list(a), capture_output=True, text=True, encoding="utf-8")


def sjekk_forsegla():
    for rel in ("analyse/forsegla5/FORESEIINGAR.json", "analyse/28_regenerasjon.py"):
        c = git("log", "-1", "--format=%H", "--", rel).stdout.strip()
        if not c:
            sys.exit("Stoppa: %s er ikkje committa." % rel)
        if git("show", "%s:%s" % (c, rel)).stdout.replace("\r\n", "\n").encode("utf-8") != open(os.path.join(ROT, rel), "rb").read().replace(b"\r\n", b"\n"):
            sys.exit("Stoppa: %s er endra etter siste commit." % rel)
        if not git("branch", "-r", "--contains", c).stdout.strip():
            sys.exit("Stoppa: commiten %s med %s er ikkje pusha." % (c[:8], rel))
    return git("log", "-1", "--format=%H", "--", "analyse/forsegla5/FORESEIINGAR.json").stdout.strip()


def last():
    ST = {r["Objekt-ID"]: r for r in csv.DictReader(open(os.path.join(ROT, "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline=""))}
    rein = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "stolar_reinsa.csv"), encoding="utf-8-sig"))}
    maal = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "mesh_maal.csv"), encoding="utf-8"))}
    S = []
    for cid in sorted(maal):
        r, m = rein.get(cid), maal[cid]
        if not r or r["vaksenstol"] != "1" or not r["aar_fraa"] or not m.get("sete_cm") or not r["H"]:
            continue
        if set(filter(None, (m.get("flagg") or "").split(";"))) & {"opp_ikkje_y", "opp_ned?", "silhuett_klipt"}:
            continue
        s = ST.get(cid, {})
        k = felles.materialklasse(s.get("Materialar", ""), s.get("Teknikk", ""))
        mat = "nye" if k in NYE else "tre" if k == "WOOD" else None
        aar = int(float(r["aar_fraa"]))
        per = next((p for p, (a, b) in F["maal"]["periodar"].items() if a <= aar <= b), None)
        S.append({"id": cid, "aar": aar, "mat": mat, "klasse": k, "per": per, "museum": r["museum"], "sete": float(m["sete_cm"]),
                  "H": float(r["H"]), "B": r["B"], "D": r["D"], "type": r["type"]})
    # éin per modell: same museum og mål, eller same stamme
    sett, ut = set(), []
    for s in S:
        k1 = ("m", s["museum"], s["H"], s["B"], s["D"])
        k2 = ("s", re.sub(r"[A-Za-z]$|-\d+$", "", s["id"]))
        if k1 in sett or k2 in sett:
            continue
        sett |= {k1, k2}
        ut.append(s)
    return ut


def spreiing(x):
    q1, q2, q3 = np.quantile(x, [0.25, 0.5, 0.75])
    return (q3 - q1) / q2


if __name__ == "__main__":
    seal = sjekk_forsegla()
    if os.path.exists(P_RES):
        sys.exit("Stoppa: RESULTAT.json finst alt. Prøva er køyrd.")
    S = last()
    celle = {(m, p): [s for s in S if s["mat"] == m and s["per"] == p] for m in ("nye", "tre") for p in ("tidleg", "seint")}
    n = {"%s_%s" % k: len(v) for k, v in celle.items()}
    gyldig = min(n.values()) >= 25
    X = {k: {z: np.array([s[z] for s in v]) for z in ("sete", "H")} for k, v in celle.items()}

    def stat(X):
        f = lambda m, z: spreiing(X[(m, "tidleg")][z]) / spreiing(X[(m, "seint")][z])
        return {"R1": f("nye", "sete"), "R2": f("nye", "sete") / f("tre", "sete"), "R3": f("nye", "sete") - f("nye", "H"),
                "forhold": {m + "_" + z: f(m, z) for m in ("nye", "tre") for z in ("sete", "H")}}

    obs = stat(X)
    rng = np.random.default_rng(F["froe"])
    B = {"R1": [], "R2": [], "R3": []}
    for _ in range(F["n_boot"]):
        Xb = {k: {z: v[z][idx] for z in v} for k, v in X.items() for idx in [rng.integers(0, len(v["sete"]), len(v["sete"]))]}
        sb = stat(Xb)
        for k in B:
            B[k].append(sb[k])
    ki = {k: [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))] for k, v in B.items()}
    dom = lambda ok: "UGYLDIG" if not gyldig else "HELDT" if ok else "SLO FEIL"
    R = {"R1_setet_samlar_seg": {"forhold": obs["R1"], "ki95": ki["R1"], "dom": dom(obs["R1"] >= 1.3 and ki["R1"][0] > 1)},
         "R2_ikkje_tida": {"forhold": obs["R2"], "ki95": ki["R2"], "dom": dom(obs["R2"] >= 1.25 and ki["R2"][0] > 1)},
         "R3_ryggen_samlar_seg_ikkje": {"differanse": obs["R3"], "ki95": ki["R3"], "dom": dom(obs["R3"] > 0 and ki["R3"][0] > 0)}}
    spr = {"%s_%s_%s" % (m, p, z): float(spreiing(X[(m, p)][z])) for m in ("nye", "tre") for p in ("tidleg", "seint") for z in ("sete", "H")}
    med = {"%s_%s_%s" % (m, p, z): float(np.median(X[(m, p)][z])) for m in ("nye", "tre") for p in ("tidleg", "seint") for z in ("sete", "H")}
    ut = {"tid": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "forsegla_commit": seal, "n": n, "gyldig": gyldig,
          "resultat": R, "forhold": {k: float(v) for k, v in obs["forhold"].items()}, "spreiing": spr, "median": med, "avvik": []}
    json.dump(ut, open(P_RES, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    json.dump({"stolar": [{k: s[k] for k in ("id", "aar", "mat", "klasse", "per", "museum", "sete", "H", "type")} for s in S if s["mat"]]},
              open(P_FIG, "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
    print(json.dumps(ut, ensure_ascii=False, indent=1))
