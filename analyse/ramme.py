"""ramme.py - éi felles ramme for alle analysane: heile samlinga, éin gong, same reglar.

  python analyse/ramme.py        byggjer analyse/data/ramme.npz og analyse/data/ramme_teljing.json

Ramma inneheld kvar vaksenstol med 3D-silhuett i centimeter som går gjennom kvalitetsreglane (dei same som
17_figurar_profil.py), med år, museum, type, stil, materialklasse, produsent, suite (same modell), katalogmål,
setehøgd frå katalog og frå 3D-modell, og trekka per cm. Statistikkverktøya under er dei alle prøver skal bruke:
kryssvalidering som held suitar samla, permutasjon innan strata, bootstrap over suitar, og dei to kontrollane
som må køyrast FØR ei prøve rører utfallet: placebo (permuterte merke skal gje null) og planta effekt (ein
kjend effekt skal bli funnen).
"""
import csv, importlib.util, json, os, re, sys
import numpy as np

HER = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.dirname(HER)
P_NPZ = os.path.join(HER, "data", "ramme.npz")
P_TEL = os.path.join(HER, "data", "ramme_teljing.json")
NR = 140
SONER = {"understell": (2, 36), "setesone": (38, 58), "overdel": (62, 125)}
_RE_STAMME = re.compile(r"(?<=\d)[A-Za-z](-\d+)?$")
_RE_NMKDEL = re.compile(r"^(NMK\.\d{4}\.\d{4})\.\d+$")


def _felles():
    s = importlib.util.spec_from_file_location("felles", os.path.join(HER, "forsegla2", "felles.py"))
    m = importlib.util.module_from_spec(s)
    sys.path.insert(0, os.path.join(HER, "forsegla2"))
    s.loader.exec_module(m)
    return m


def _utstr(img):
    k = np.where(img.any(0))[0]
    r = np.where(img.any(1))[0]
    return (int(k[0]), int(k[-1]), int(r[0]), int(r[-1])) if len(k) else (0, 0, 0, 0)


def radtrekk(side, front):
    """Per cm over golvet: mengd materiale og utstrekning, framanfrå og frå sida. -> (4, NR)"""
    ut = []
    for img in (front, side):
        img = img[:NR].astype(np.float32)
        occ = img > 0.5
        an = occ.any(1)
        f = np.where(an, occ.argmax(1), 0)
        l = np.where(an, 159 - occ[:, ::-1].argmax(1), 0)
        ut += [img.sum(1), np.where(an, l - f + 1, 0).astype(np.float32)]
    return np.array(ut)


def _tal(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def bygg():
    felles = _felles()
    ST = {r["Objekt-ID"]: r for r in csv.DictReader(open(os.path.join(ROT, "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline=""))}
    rein = list(csv.DictReader(open(os.path.join(HER, "data", "stolar_reinsa.csv"), encoding="utf-8-sig")))
    maal = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "mesh_maal.csv"), encoding="utf-8"))}
    z = np.load(os.path.join(HER, "data", "mesh_silhuettar.npz"))
    side = dict(zip(z["ids"], z["side"]))
    front = dict(zip(z["ids"], z["front"]))
    tel = {"objekt": len(rein)}
    rad = []
    for r in sorted(rein, key=lambda r: r["id"]):
        i, m = r["id"], maal.get(r["id"])
        if r["vaksenstol"] != "1":
            tel["ut_ikkje_vaksenstol"] = tel.get("ut_ikkje_vaksenstol", 0) + 1
            continue
        if i not in side or not m or not r["H"] or not r["B"] or not r["D"]:
            tel["ut_utan_katalogmaal_eller_silhuett"] = tel.get("ut_utan_katalogmaal_eller_silhuett", 0) + 1
            continue
        if set(filter(None, (m.get("flagg") or "").split(";"))) & {"opp_ikkje_y", "opp_ned?", "silhuett_klipt"}:
            tel["ut_uviss_orientering"] = tel.get("ut_uviss_orientering", 0) + 1
            continue
        H, B, D = float(r["H"]), float(r["B"]), float(r["D"])
        s_img, f_img = np.unpackbits(side[i], axis=-1), np.unpackbits(front[i], axis=-1)
        k0, k1, _, r1 = _utstr(s_img)
        f0, f1, _, _ = _utstr(f_img)
        if (k1 - k0) > 1.5 * D + 10 or (f1 - f0) > 1.5 * B + 10 or abs(r1 + 1 - H) > 6:
            tel["ut_skalasjekk"] = tel.get("ut_skalasjekk", 0) + 1
            continue
        if not r["aar_fraa"] or float(r["aar_fraa"]) < 1000:
            tel["ut_utan_aar"] = tel.get("ut_utan_aar", 0) + 1
            continue
        s = ST.get(i, {})
        rad.append({"id": i, "museum": r["museum"], "type": r["type"], "stil": (r["stil"] or "").strip(),
                    "aar": int(float(r["aar_fraa"])), "aar_til": int(float(r["aar_til"])) if r["aar_til"] else int(float(r["aar_fraa"])),
                    "H": H, "B": B, "D": D, "sete_kat": _tal(r["sete"]) if r["sete_ok"] == "1" else np.nan,
                    "sete_mesh": _tal(m.get("sete_cm")), "mat": felles.materialklasse(s.get("Materialar", ""), s.get("Teknikk", "")),
                    "produsent": (s.get("Produsent") or "").strip(), "namn": (s.get("Namn") or "").strip(),
                    "armlene": int(r["type"] == "Armstol"), "side": side[i], "front": front[i],
                    "trekk": radtrekk(s_img, f_img)})
    n = len(rad)
    tel["i_ramma"] = n
    # suitar: same stamme, eller same museum, H, B og D (union-find)
    forelder = list(range(n))

    def finn(a):
        while forelder[a] != a:
            forelder[a] = forelder[forelder[a]]
            a = forelder[a]
        return a

    nokkel = {}
    for k, r in enumerate(rad):
        st = _RE_NMKDEL.sub(r"\1", _RE_STAMME.sub("", r["id"]))
        for nk in (("s", r["museum"], st), ("m", r["museum"], r["H"], r["B"], r["D"])):
            if nk in nokkel:
                forelder[finn(k)] = finn(nokkel[nk])
            else:
                nokkel[nk] = k
    suite = np.array([finn(k) for k in range(n)])
    tel["suitar"] = int(len(set(suite)))
    tel["per_museum"] = {m_: int(sum(r["museum"] == m_ for r in rad)) for m_ in ("VA", "NM")}
    tel["per_hundreaar"] = {str(c): int(sum(r["aar"] // 100 * 100 == c for r in rad)) for c in sorted({r["aar"] // 100 * 100 for r in rad})}
    tel["per_materiale"] = {k_: int(sum(r["mat"] == k_ for r in rad)) for k_ in sorted({r["mat"] for r in rad})}
    tel["med_katalogsete"] = int(sum(np.isfinite(r["sete_kat"]) for r in rad))
    tel["med_mesh_sete"] = int(sum(np.isfinite(r["sete_mesh"]) for r in rad))
    os.makedirs(os.path.dirname(P_NPZ), exist_ok=True)
    felt = lambda k_, dt=None: np.array([r[k_] for r in rad], dtype=dt) if dt else np.array([r[k_] for r in rad])
    np.savez_compressed(P_NPZ, id=felt("id"), museum=felt("museum"), type=felt("type"), stil=felt("stil"), aar=felt("aar", int),
                        aar_til=felt("aar_til", int), H=felt("H", float), B=felt("B", float), D=felt("D", float),
                        sete_kat=felt("sete_kat", float), sete_mesh=felt("sete_mesh", float), mat=felt("mat"), produsent=felt("produsent"),
                        namn=felt("namn"), armlene=felt("armlene", int), suite=suite, side=np.stack([r["side"] for r in rad]),
                        front=np.stack([r["front"] for r in rad]), trekk=np.stack([r["trekk"] for r in rad]).astype(np.float32))
    json.dump(tel, open(P_TEL, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    return tel


def last():
    """-> dict med felta i ramma. Byggjer ho om ho manglar."""
    if not os.path.exists(P_NPZ):
        bygg()
    z = np.load(P_NPZ, allow_pickle=False)
    return {k: z[k] for k in z.files}


# ------------------------------------------------------------------ statistikkverktøy
def pca_rom(M, k=15):
    """Standardiser og projiser på dei k første hovudkomponentane."""
    sd = M.std(0)
    ok = sd > 1e-6
    Z = (M[:, ok] - M[:, ok].mean(0)) / sd[ok]
    _, _, Vt = np.linalg.svd(Z, full_matrices=False)
    return Z @ Vt[:k].T


def suitefald(suite, k=5, froe=20261113):
    """Kryssvalideringsfald der stolar i same suite alltid hamnar i same fald."""
    rng = np.random.default_rng(froe)
    u = np.unique(suite)
    f = dict(zip(u, rng.permutation(len(u)) % k))
    return np.array([f[s] for s in suite])


def perm_innan(merke, strata, rng):
    """Permuter merka innan kvart stratum (t.d. museum gonger type)."""
    ut = np.array(merke).copy()
    for s in np.unique(strata):
        k = np.where(strata == s)[0]
        ut[k] = ut[rng.permutation(k)]
    return ut


def suiteboot(suite, rng):
    """Indeksar for eitt bootstrap-utval der heile suitar blir trekte."""
    u = np.unique(suite)
    grupper = {s: np.where(suite == s)[0] for s in u}
    return np.concatenate([grupper[s] for s in rng.choice(u, len(u))])


def placebo(statistikk, merke, strata, n=200, froe=20261113):
    """Køyr statistikken på permuterte merke. -> fordelinga under null. Skal liggje rundt null."""
    rng = np.random.default_rng(froe)
    return np.array([statistikk(perm_innan(merke, strata, rng)) for _ in range(n)])


def p_verdi(obs, null, tosidig=True):
    null = np.asarray(null, float)
    if tosidig:
        return float((np.sum(np.abs(null - null.mean()) >= abs(obs - null.mean())) + 1) / (len(null) + 1))
    return float((np.sum(null >= obs) + 1) / (len(null) + 1))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(bygg(), ensure_ascii=False, indent=1))
