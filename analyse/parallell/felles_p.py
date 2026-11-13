"""felles_p.py - felles verktøy for dei parallelle prøvene. Alle prøver bruker HEILE ramma (1 377 stolar: V&A 1 009, Nasjonalmuseet 368; 33 stolar med kopiert målpost er tekne ut).

Bruk frå analyse/parallell/<id>/prove.py:
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    import felles_p as fp
    D = fp.last()

D er ein dict:
  D["n"]                     talet på stolar (1 377)
  D["id"], D["museum"] ("VA"/"NM"), D["type"], D["stil"], D["aar"], D["aar_til"], D["H"], D["B"], D["D"] (katalog, cm),
  D["sete_kat"] (katalogsete, nan der det manglar), D["mat"] (WOOD, LINE, LINE+SHEET, SHEET, ANNA), D["produsent"], D["namn"],
  D["armlene"] (1 for type Armstol), D["suite"] (same modell eller same mål: hald saman i bootstrap og kryssvalidering),
  D["sett"]  (ekte sett: same id-stamme. Brukt til å måle målefeilen),
  D["bolk"]  (50-årsbolk: aar klipt til 1550..1999 // 50),
  D["trekk"] (n, 4, 140): per cm over golvet [front mengd, front utstrekning, side mengd, side utstrekning] frå silhuettane,
  D["m"]     dict med 3D-mål i cm og grader (nan der målet manglar):
             sete_h, sete_djupn, sete_breidd, sete_halling (positiv når framkanten er høgast), rygg_halling (frå loddlina, positiv bakover),
             rom_djupn (framkanten av setet til ryggflata 20 cm over setet), arm_v, arm_h (høgd over setet), arm_opning,
             fot_djupn, fot_breidd, fot_areal, djupn3d, breidd3d,
             tp_x, tp_y, tp_z (tyngdepunktet til overflata; x fram, y breidd, z opp), margin_bak, margin_fram, margin_side (cm frå
             tyngdepunktet til kanten av fotavtrykket), velt_bak_grad, velt_fram_grad, velt_side_grad (veltevinkel), flate_opp,
             flate_ned, flate_loddrett, flate_fram, flate_bak (del av overflata som vender slik), asymmetri (1 minus IoU mot spegelbiletet),
             hylster_volum, boks_volum, fylling
  D["lag"]   (n, 60): del av overflata i kvart 2,5 cm lag frå golvet
fp.voksel(k) -> (60, 64, 64) bool for stol k: [z-lag, x (bak til fram), y (breidd)], ruter på 2,5 cm, golvet i lag 0, stolen sentrert i x og y.
fp.voksel_alle() -> (n, 60, 64, 64) bool (om lag 350 MB; bruk berre om du treng alt på ein gong).
Punktskyene (150 000 punkt per stol) ligg i analyse/data/mesh_cache/<id>.npz; bruk fp.punktsky(k) -> x, y, z, nx, ny, nz i cm.
Det er tungt (3 GB i alt): les berre punktskyene om prøva di ikkje kan gjerast med måla og vokslane, og ta då kvart tiande punkt.

Pålitelegheit (ekte sett, 44 sett): sete_h 0,94 (feil 1,4 cm), sete_djupn 0,95 (1,7), sete_breidd 0,93 (2,5), sete_halling 0,90 (1,0 grad),
rom_djupn 0,92 (2,2), rygg_halling 0,79 (3,8 grader), fot_breidd 0,93, fot_djupn 0,53 (IKKJE bruk), djupn3d 0,93, breidd3d 0,95.
Måla i tyngdepunkt, margin, flate, asymmetri og fylling er IKKJE kontrollerte: rekn pålitelegheita sjølv med fp.paalit() før du bruker dei.
"""
import csv, importlib.util, json, os, subprocess, sys
import numpy as np

PAR = os.path.dirname(os.path.abspath(__file__))
HER = os.path.dirname(PAR)                      # analyse/
ROT = os.path.dirname(HER)
sys.path.insert(0, HER)
import ramme  # noqa: E402

_D = None


def last():
    global _D
    if _D is not None:
        return _D
    R = ramme.last()
    z3 = np.load(os.path.join(HER, "data", "ramme3d.npz"))
    ze = np.load(os.path.join(HER, "data", "ramme3d_ekstra.npz"))
    m = {a: z3["maal"][:, j] for j, a in enumerate(z3["namn"])}
    m.update({a: ze["ekstra"][:, j] for j, a in enumerate(ze["namn"])})
    D = dict(R)
    D["n"] = len(R["id"])
    D["m"] = m
    D["lag"] = ze["lag"]
    D["sett"] = np.array([mu + "|" + ramme._RE_NMKDEL.sub(r"\1", ramme._RE_STAMME.sub("", i)) for i, mu in zip(R["id"], R["museum"])])
    D["bolk"] = np.clip(R["aar"], 1550, 1999) // 50
    D["_voksel"] = z3["voksel"]
    _D = D
    return D


def voksel(k):
    return np.unpackbits(last()["_voksel"][k]).reshape(60, 64, 64).astype(bool)


def voksel_alle():
    return np.unpackbits(last()["_voksel"], axis=1).reshape(-1, 60, 64, 64).astype(bool)


def punktsky(k):
    spec = importlib.util.spec_from_file_location("r3", os.path.join(HER, "38_ramme3d.py"))
    r3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r3)
    D = last()
    if not hasattr(punktsky, "mm"):
        punktsky.mm = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "mesh_maal.csv"), encoding="utf-8"))}
    zf = np.load(os.path.join(HER, "data", "mesh_cache", D["id"][k] + ".npz"))
    return r3.kanonisk(zf["p"], zf["n"], punktsky.mm[D["id"][k]], float(D["H"][k]))


# ------------------------------------------------------------------ statistikk (same reglar for alle prøver)
suiteboot = ramme.suiteboot          # suiteboot(suite, rng) -> indeksar der heile suitar er trekte
perm_innan = ramme.perm_innan        # perm_innan(merke, strata, rng) -> merke permuterte innan strata
suitefald = ramme.suitefald          # suitefald(suite, k=5) -> fald der suitar er haldne samla
pca_rom = ramme.pca_rom              # pca_rom(M, k) -> standardisert og projisert


def feilvarians(v, sett, rng=None):
    """Målefeilen til eit mål: samla varians innan ekte sett. rng: trekk setta på nytt (til bootstrap)."""
    u = [s for s in np.unique(sett) if (np.isfinite(v) & (sett == s)).sum() >= 2]
    if rng is not None and len(u):
        u = list(rng.choice(u, len(u)))
    ss, df = 0.0, 0
    for s in u:
        g = v[(sett == s) & np.isfinite(v)]
        ss += ((g - g.mean()) ** 2).sum()
        df += len(g) - 1
    return ss / max(df, 1), len(u)


def paalit(v, sett):
    """Pålitelegheit = 1 minus feilvarians delt på total varians. Under 0,7: ikkje bruk målet."""
    return float(1 - feilvarians(v, sett)[0] / np.nanvar(v, ddof=1))


def cv_sann(v, feilvar):
    v = v[np.isfinite(v)]
    return float(np.sqrt(max(v.var(ddof=1) - feilvar, 0.0)) / np.median(v))


def eta2(v, grupper):
    """Del av variansen mellom grupper, justert for talet på grupper."""
    ok = np.isfinite(v)
    v, g = v[ok], np.asarray(grupper)[ok]
    k = len(np.unique(g))
    sst = ((v - v.mean()) ** 2).sum()
    ssw = sum(((v[g == a] - v[g == a].mean()) ** 2).sum() for a in np.unique(g))
    return float(max(1 - (ssw / max(len(v) - k, 1)) / (sst / (len(v) - 1)), 0.0))


def spearman(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(np.argsort(np.argsort(a[ok])), np.argsort(np.argsort(b[ok])))[0, 1])


def ki(x, niva=0.95):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return [float(np.quantile(x, (1 - niva) / 2)), float(np.quantile(x, 1 - (1 - niva) / 2))]


def museum_idx(D):
    """-> {"samla": alle, "VA": ..., "NM": ...}. Kvar påstand skal haldast i VA og NM kvar for seg."""
    return {"samla": np.arange(D["n"]), "VA": np.where(D["museum"] == "VA")[0], "NM": np.where(D["museum"] == "NM")[0]}


# ------------------------------------------------------------------ forsegling
def sjekk_forsegla(mappe):
    """Stopp om FORESEIINGAR.json eller prove.py i mappa ikkje ligg uendra i ein pusha commit, eller om RESULTAT.json finst."""
    git = lambda *a: subprocess.run(["git", "-C", ROT] + list(a), capture_output=True, text=True, encoding="utf-8")
    for fil in ("FORESEIINGAR.json", "prove.py"):
        sti = os.path.join(mappe, fil)
        rel = os.path.relpath(sti, ROT).replace("\\", "/")
        c = git("log", "-1", "--format=%H", "--", rel).stdout.strip()
        if not c:
            sys.exit("Stoppa: %s er ikkje committa. Prøva er ikkje forsegla." % rel)
        if git("show", "%s:%s" % (c, rel)).stdout.replace("\r\n", "\n").encode("utf-8") != open(sti, "rb").read().replace(b"\r\n", b"\n"):
            # Einaste unntak: prove.py krasja ved opning og er retta utan å røre estimanden. Då MÅ AVVIK.md i mappa seie kva som vart retta.
            if fil == "prove.py" and os.environ.get("AVVIK_ETTER_KRASJ") == "1" and os.path.exists(os.path.join(mappe, "AVVIK.md")):
                continue
            sys.exit("Stoppa: %s er endra etter forseglinga." % rel)
        if not git("branch", "-r", "--contains", c).stdout.strip():
            sys.exit("Stoppa: forseglinga av %s er ikkje pusha." % rel)
    if os.path.exists(os.path.join(mappe, "RESULTAT.json")):
        sys.exit("Stoppa: RESULTAT.json finst alt. Prøva er køyrd.")
    return git("log", "-1", "--format=%H", "--", os.path.relpath(os.path.join(mappe, "FORESEIINGAR.json"), ROT).replace("\\", "/")).stdout.strip()


def lagre(mappe, namn, obj):
    json.dump(obj, open(os.path.join(mappe, namn), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)


# ------------------------------------------------------------------ figurstil: svart på kvitt, same skrift som resten
def figurstil():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm
    mappe = os.path.join(os.path.dirname(ROT), "FORML-RE", "traktat", "layout", "fonts")
    for f in ("EBGaramond12-Regular.otf", "EBGaramond12-Italic.otf"):
        if os.path.exists(os.path.join(mappe, f)):
            fm.fontManager.addfont(os.path.join(mappe, f))
    serif = "EB Garamond" if any(f.name == "EB Garamond" for f in fm.fontManager.ttflist) else "Georgia"
    plt.rcParams.update({"font.family": serif, "text.color": "#0c0c0c", "axes.edgecolor": "#0c0c0c", "figure.facecolor": "white",
                         "savefig.facecolor": "white", "axes.linewidth": 0.6})
    return {"plt": plt, "SERIF": serif, "MONO": "Consolas", "FG": "#0c0c0c", "DIM": "#8a8a8a"}
