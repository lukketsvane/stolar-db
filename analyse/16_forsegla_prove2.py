"""16_forsegla_prove2.py - den andre forsegla prøva: silhuettar og mål frå 3D-modellane.

Tre steg. Kvar modul blir forsegla før han blir opna, og blir opna éin gong.

  python analyse/16_forsegla_prove2.py --skriv [modul ...]
      Samlar SPEC frå modulane i analyse/forsegla2/ og skriv forsegla2/FORESEIINGAR.json med tersklar og
      sjekksummar. Modulane som er nemnde, blir òg køyrde på DEV-halvparten. Rører ikkje dei tilbakehaldne
      stolane. Modular som alt er opna, står urørte.

  python analyse/16_forsegla_prove2.py --forsegl <commit>
      Krev at FORESEIINGAR.json ligg uendra i <commit> saman med modulane.
      Legg ei line til forsegla2/FORSEGLA.json. Først då let lastaren seg opne.

  python analyse/16_forsegla_prove2.py --opne [modul ...]
      Køyrer dei nemnde modulane (eller alle som ikkje er opna) på dei tilbakehaldne stolane.
      Krev at modulfila er lik den som ligg i siste forsegling. Skriv RESULTAT.json og FIGURDATA.json.

Avvik blir førte i RESULTAT.json.
"""
import datetime, hashlib, importlib, json, os, subprocess, sys, traceback

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.dirname(HER)
F2 = os.path.join(HER, "forsegla2")
sys.path.insert(0, F2)

MODULAR = ["t1_sete", "t2_materiale", "t3_olboge", "t4_gradient", "t5_krakk", "t6_saumar"]
FELLES = ["analyse/14_mesh_maal.py", "analyse/15_mesh_test.py", "analyse/16_forsegla_prove2.py", "analyse/forsegla2/felles.py"]
DATA = ["analyse/data/stolar_reinsa.csv", "analyse/data/dev_ids.txt", "analyse/data/dev_mesh_maal.csv",
        "analyse/data/dev_silhuettar.npz", "analyse/data/mesh_maal.csv", "analyse/data/mesh_silhuettar.npz",
        "analyse/14_validering.csv", "analyse/data/va_dimensjonar_raa.jsonl", "STOLAR/STOLAR.csv"]
P_FORE = os.path.join(F2, "FORESEIINGAR.json")
P_TEKST = os.path.join(F2, "tekst.json")
P_SEGL = os.path.join(F2, "FORSEGLA.json")
P_RES = os.path.join(F2, "RESULTAT.json")
P_FIG = os.path.join(F2, "FIGURDATA.json")
modfil = lambda m: "analyse/forsegla2/%s.py" % m
no = lambda: datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def sjekksum(rel):
    """SHA-256 med linjeskift normalisert for tekstfiler, så Windows og Linux gjev same sum."""
    p = os.path.join(ROT, rel)
    if not os.path.exists(p):
        return None
    b = open(p, "rb").read()
    if not rel.endswith(".npz"):
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def les(p, tom):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else tom


def lagre(p, d):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=1, default=float)
        f.write("\n")


def git(*a):
    return subprocess.run(["git", "-C", ROT] + list(a), capture_output=True, text=True, encoding="utf-8")


def skriv(koyr):
    gamal, res, tekst = les(P_FORE, {}), les(P_RES, {"modular": {}}), les(P_TEKST, {})
    modular = {}
    for m in MODULAR:
        if m in res.get("modular", {}):                       # alt opna: føreseiinga står som ho stod
            modular[m] = gamal["modular"][m]
            continue
        e = {"sjekksum": sjekksum(modfil(m)), "status": "klar", "spec": None,
             "opplaeringstal_DEV": gamal.get("modular", {}).get(m, {}).get("opplaeringstal_DEV")}
        if m in koyr:
            try:
                mod = importlib.import_module(m)
                e["spec"] = mod.SPEC
                e["opplaeringstal_DEV"] = mod.kjoer("dev")
                print("DEV", m, "->", e["opplaeringstal_DEV"].get("dom"))
            except Exception:
                e["status"] = "under arbeid: " + traceback.format_exc()[-300:]
        else:
            e["spec"] = gamal.get("modular", {}).get(m, {}).get("spec")
            if e["opplaeringstal_DEV"] is None:
                e["status"] = "spesifikasjonen står i modulfila (SPEC); opplæringstal ikkje rekna her enno"
        modular[m] = e
    d = {"tersklar_gjennomgaatt_av_forfattaren": bool(tekst.get("tersklar_gjennomgaatt_av_forfattaren", False)), "skriven": no(),
         "merknad": tekst.get("merknad", ""), "utval": tekst.get("utval", ""), "blindskap": tekst.get("blindskap", ""),
         "foreseiingar": tekst.get("foreseiingar", {}), "tapsliste": tekst.get("tapsliste", []),
         "modular": modular, "sjekksummar_felles": {r: sjekksum(r) for r in FELLES}, "sjekksummar_data": {r: sjekksum(r) for r in DATA}}
    lagre(P_FORE, d)
    print("skrive:", P_FORE)


def forsegl(commit):
    r = git("show", "%s:analyse/forsegla2/FORESEIINGAR.json" % commit)
    if r.returncode != 0 or r.stdout.replace("\r\n", "\n").strip() != open(P_FORE, encoding="utf-8").read().replace("\r\n", "\n").strip():
        sys.exit("Stoppa: FORESEIINGAR.json i commit %s er ikkje lik arbeidsfila." % commit)
    for rel in FELLES + [modfil(m) for m in MODULAR]:
        if git("cat-file", "-e", "%s:%s" % (commit, rel)).returncode != 0:
            sys.exit("Stoppa: %s ligg ikkje i commit %s." % (rel, commit))
    fjern = git("branch", "-r", "--contains", commit).stdout.split()
    segl = les(P_SEGL, [])
    segl.append({"commit": git("rev-parse", commit).stdout.strip(), "forsegla_lokalt": no(), "paa_fjerngreiner": fjern,
                 "modular": {m: sjekksum(modfil(m)) for m in MODULAR}, "felles": {r: sjekksum(r) for r in FELLES},
                 "data": {r: sjekksum(r) for r in DATA}})
    lagre(P_SEGL, segl)
    print("forsegla mot commit", commit, "| fjerngreiner:", fjern or "INGEN (ikkje pusha)")


def opne(ynskte):
    segl = les(P_SEGL, [])
    if not segl:
        sys.exit("Stoppa: prøva er ikkje forsegla.")
    siste = segl[-1]
    for rel, sum_ in list(siste["felles"].items()) + list(segl[0]["data"].items()):
        if sjekksum(rel) != sum_:
            sys.exit("Stoppa: %s er endra etter forseglinga." % rel)
    res = les(P_RES, {"avvik": [], "instrumentprove_TEST": None, "modular": {}, "opningar": []})
    fig = les(P_FIG, {})
    os.environ["STOL_OPNE"] = "ja"
    if res["instrumentprove_TEST"] is None:
        r = subprocess.run([sys.executable, os.path.join(HER, "15_mesh_test.py")], capture_output=True, text=True, encoding="utf-8")
        res["instrumentprove_TEST"] = r.stdout if r.returncode == 0 else "FEIL: " + r.stderr[-2000:]
    for m in (ynskte or [x for x in MODULAR if x not in res["modular"]]):
        if m in res["modular"]:
            print(m, "er alt opna; hoppar over")
            continue
        if sjekksum(modfil(m)) != siste["modular"].get(m):
            print(m, "er endra etter siste forsegling; forsegl på nytt før opning")
            continue
        try:
            mod = importlib.import_module(m)
            res["modular"][m] = mod.kjoer("held")
            print("HELD", m, "->", res["modular"][m].get("dom"))
        except Exception:
            res["modular"][m] = {"dom": "KRASJ", "feil": traceback.format_exc()[-3000:]}
            print("HELD", m, "-> KRASJ")
        res["opningar"].append({"modul": m, "tid": no(), "forsegla_commit": siste["commit"]})
        lagre(P_RES, res)
        try:
            fig[m] = mod.figurdata("held")
        except Exception:
            fig[m] = {"feil": traceback.format_exc()[-1500:]}
        lagre(P_FIG, fig)
    lagre(P_RES, res)
    print("skrive:", P_RES)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--skriv"]:
        skriv(a[1:])
    elif a[:1] == ["--forsegl"] and len(a) == 2:
        forsegl(a[1])
    elif a[:1] == ["--opne"]:
        opne(a[1:])
    else:
        sys.exit(__doc__)
