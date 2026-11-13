"""39_kontaktflata.py - den tiande forsegla prøva: kor fast held kroppen kvar akse i kontaktflata? 3D-mål, heile ramma.

Tre delar, alle på heile ramma og i V&A og Nasjonalmuseet kvar for seg:
  A  spreiing: kvar kroppsakse mot heile stolen i same retning (setehøgd mot totalhøgd, rommet frå setekant
     til rygg mot totaldjupn, setebreidd mot totalbreidd), med målefeilen trekt frå
  B  tid: kor mykje av kvar akse 50-årsbolken forklarer, kroppsakse mot partnar
  C  stilling eller storleik: forteiknet på samanhengen mellom setehøgd, setedjupn og rygghalling

  python analyse/39_kontaktflata.py --kontroll   placebo og planta effekt. Skriv berre om kontrollane held.
  python analyse/39_kontaktflata.py --opne       éin gong, etter forsegling. Skriv forsegla10/RESULTAT.json.
"""
import json, os, subprocess, sys
import numpy as np
import ramme

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
F10 = os.path.join(HER, "forsegla10")
P_FORE, P_RES = os.path.join(F10, "FORESEIINGAR.json"), os.path.join(F10, "RESULTAT.json")
NB = 1000
PAR = [("sete_h", "H"), ("rom_djupn", "djupn3d"), ("sete_breidd", "breidd3d")]
SEK = [("arm_hoegd", "rygg_over_sete"), ("sete_djupn", "djupn3d"), ("arm_opning", "breidd3d")]


def data():
    R = ramme.last()
    z = np.load(os.path.join(HER, "data", "ramme3d.npz"))
    M = {a: z["maal"][:, j] for j, a in enumerate(z["namn"])}
    A = {"sete_h": M["sete_h"], "H": R["H"].astype(float), "rygg_over_sete": R["H"] - M["sete_h"], "rom_djupn": M["rom_djupn"],
         "sete_djupn": M["sete_djupn"], "djupn3d": M["djupn3d"], "sete_breidd": M["sete_breidd"], "breidd3d": M["breidd3d"],
         "arm_hoegd": 0.5 * (M["arm_v"] + M["arm_h"]), "arm_opning": M["arm_opning"], "rygg_halling": M["rygg_halling"],
         "sete_halling": M["sete_halling"]}
    sett = np.array([m + "|" + ramme._RE_NMKDEL.sub(r"\1", ramme._RE_STAMME.sub("", i)) for i, m in zip(R["id"], R["museum"])])
    bolk = np.clip(R["aar"], 1550, 1999) // 50
    return R, A, sett, bolk


def feilvarians(v, sett, rng=None):
    """Målefeilen: samla varians innan ekte sett (same id-stamme). rng: trekk setta på nytt."""
    u = [s for s in np.unique(sett) if (np.isfinite(v) & (sett == s)).sum() >= 2]
    if rng is not None:
        u = list(rng.choice(u, len(u)))
    ss, df = 0.0, 0
    for s in u:
        g = v[(sett == s) & np.isfinite(v)]
        ss += ((g - g.mean()) ** 2).sum()
        df += len(g) - 1
    return ss / max(df, 1), len(u)


def cv_sann(v, ve):
    v = v[np.isfinite(v)]
    return float(np.sqrt(max(v.var(ddof=1) - ve, 0.0)) / np.median(v))


def eta2(v, b):
    """Del av variansen mellom bolkar, justert for talet på bolkar (epsilon i andre)."""
    ok = np.isfinite(v)
    v, b = v[ok], b[ok]
    sst = ((v - v.mean()) ** 2).sum()
    ssw = sum(((v[b == k] - v[b == k].mean()) ** 2).sum() for k in np.unique(b))
    k = len(np.unique(b))
    return float(max(1 - (ssw / max(len(v) - k, 1)) / (sst / (len(v) - 1)), 0.0))


def spearman(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    ra, rb = np.argsort(np.argsort(a[ok])), np.argsort(np.argsort(b[ok]))
    return float(np.corrcoef(ra, rb)[0, 1])


def ki(x):
    return [float(np.quantile(x, 0.025)), float(np.quantile(x, 0.975))]


def del_a(A, sett, suite, idx, rng, par):
    ut = {}
    for kropp, heil in par:
        vk, vh = A[kropp], A[heil]
        ek, eh = feilvarians(vk, sett)[0], feilvarians(vh, sett)[0]
        obs = cv_sann(vk[idx], ek) / cv_sann(vh[idx], eh)
        b = []
        for _ in range(NB):
            k = idx[ramme.suiteboot(suite[idx], rng)]
            ekb, ehb = feilvarians(vk, sett, rng)[0], feilvarians(vh, sett, rng)[0]
            nemnar = cv_sann(vh[k], ehb)
            b.append(cv_sann(vk[k], ekb) / nemnar if nemnar > 0 else np.nan)
        ut[kropp + "/" + heil] = {"forhold": obs, "ki95": ki(np.array(b)[np.isfinite(b)]), "cv_kropp": cv_sann(vk[idx], ek), "cv_heil": cv_sann(vh[idx], eh),
                                  "n": int(np.isfinite(vk[idx]).sum())}
    return ut


def paalit(v, sett):
    return max(1 - feilvarians(v, sett)[0] / np.nanvar(v, ddof=1), 0.05)


def del_b(A, sett, suite, bolk, idx, rng, par, bolk_perm=None):
    ut = {}
    bb = bolk if bolk_perm is None else bolk_perm
    for kropp, heil in par:
        rk, rh = paalit(A[kropp], sett), paalit(A[heil], sett)
        f = lambda k: eta2(A[heil][k], bb[k]) / rh - eta2(A[kropp][k], bb[k]) / rk
        obs = f(idx)
        res = {"skilnad": obs, "eta_kropp": eta2(A[kropp][idx], bb[idx]) / rk, "eta_heil": eta2(A[heil][idx], bb[idx]) / rh}
        if bolk_perm is None:
            res["ki95"] = ki([f(idx[ramme.suiteboot(suite[idx], rng)]) for _ in range(NB)])
        ut[kropp + "/" + heil] = res
    return ut


def del_c(A, suite, idx, rng):
    ut = {}
    for a, b in (("sete_h", "sete_djupn"), ("sete_h", "rygg_halling"), ("sete_djupn", "rygg_halling")):
        obs = spearman(A[a][idx], A[b][idx])
        bs = []
        for _ in range(NB):
            k = idx[ramme.suiteboot(suite[idx], rng)]
            bs.append(spearman(A[a][k], A[b][k]))
        ut[a + "~" + b] = {"rho": obs, "ki95": ki(bs)}
    return ut


def kontroll():
    """Placebo og planta effekt. Skriv berre om kontrollane held, aldri dei verkelege utfalla."""
    R, A, sett, bolk = data()
    rng = np.random.default_rng(1)
    alle = np.arange(len(R["id"]))
    ut = {}
    # 1 feilkorreksjonen: legg kjend støy på ein akse og sjå at den sanne spreiinga kjem att
    v = A["breidd3d"].copy()
    e0 = feilvarians(v, sett)[0]
    sann = cv_sann(v, e0)
    stoey = v + rng.normal(0, 4.0, len(v))
    ut["feilkorreksjon_held"] = bool(abs(cv_sann(stoey, feilvarians(stoey, sett)[0]) / sann - 1) < 0.08)
    ut["utan_korreksjon_ville_blaase_opp"] = bool(cv_sann(stoey, 0.0) / sann > 1.03)
    # 2 placebo for tid: permuterte bolkar innan museum skal gje skilnad rundt null
    pl = []
    for _ in range(100):
        bp = ramme.perm_innan(bolk, R["museum"], rng)
        pl.append([x["skilnad"] for x in del_b(A, sett, R["suite"], bolk, alle, rng, PAR, bolk_perm=bp).values()])
    pl = np.array(pl)
    ut["placebo_tid_rundt_null"] = bool(np.all(np.abs(pl.mean(0)) < 0.02))
    ut["placebo_tid_95_band"] = [round(float(np.quantile(np.abs(pl), 0.95)), 3)]
    # 3 planta effekt for tid: ei rein tidsline lagd på ein permutert akse skal bli funnen
    bp = ramme.perm_innan(bolk, R["museum"], rng)
    B2 = dict(A)
    sd = np.nanstd(A["sete_h"])
    B2["sete_h"] = A["sete_h"] + 0.6 * sd * (bp - bp.mean()) / bp.std()
    plant = del_b(B2, sett, R["suite"], bolk, alle, rng, [("sete_h", "H")], bolk_perm=bp)["sete_h/H"]
    ut["planta_tid_funnen"] = bool(plant["eta_kropp"] > 0.15)
    # 4 samanheng: permutert akse gjev rho rundt null, planta samanheng blir funnen
    p = rng.permutation(len(alle))
    ut["placebo_rho_rundt_null"] = bool(abs(spearman(A["sete_h"], A["sete_djupn"][p])) < 0.08)
    z = (A["sete_h"] - np.nanmean(A["sete_h"])) / np.nanstd(A["sete_h"])
    ut["planta_rho_funnen"] = bool(spearman(A["sete_h"], A["sete_djupn"][p] - 0.5 * np.nanstd(A["sete_djupn"]) * z) < -0.25)
    ut["n"] = {a: int(np.isfinite(A[a]).sum()) for a in A}
    ut["sett"] = feilvarians(A["sete_h"], sett)[1]
    print(json.dumps(ut, ensure_ascii=False, indent=1))


def opne():
    git = lambda *a: subprocess.run(["git", "-C", ramme.ROT] + list(a), capture_output=True, text=True, encoding="utf-8")
    for rel in ("analyse/forsegla10/FORESEIINGAR.json", "analyse/39_kontaktflata.py"):
        c = git("log", "-1", "--format=%H", "--", rel).stdout.strip()
        if not c or git("show", "%s:%s" % (c, rel)).stdout.replace("\r\n", "\n").encode("utf-8") != open(os.path.join(ramme.ROT, rel), "rb").read().replace(b"\r\n", b"\n"):
            sys.exit("Stoppa: %s er ikkje committa uendra." % rel)
        if not git("branch", "-r", "--contains", c).stdout.strip():
            sys.exit("Stoppa: %s er ikkje pusha." % rel)
    if os.path.exists(P_RES):
        sys.exit("Stoppa: RESULTAT.json finst alt.")
    R, A, sett, bolk = data()
    rng = np.random.default_rng(20261113)
    ut = {"n": int(len(R["id"])), "per_museum": {}, "feil_sd": {a: float(np.sqrt(feilvarians(A[a], sett)[0])) for a in A}}
    for namn, idx in (("samla", np.arange(len(R["id"]))), ("VA", np.where(R["museum"] == "VA")[0]), ("NM", np.where(R["museum"] == "NM")[0])):
        ut["per_museum"][namn] = {"n": int(len(idx)), "A": del_a(A, sett, R["suite"], idx, rng, PAR), "A_sek": del_a(A, sett, R["suite"], idx, rng, SEK),
                                  "B": del_b(A, sett, R["suite"], bolk, idx, rng, PAR), "B_sek": del_b(A, sett, R["suite"], bolk, idx, rng, SEK),
                                  "C": del_c(A, R["suite"], idx, rng),
                                  "cv": {a: cv_sann(A[a][idx], feilvarians(A[a], sett)[0]) for a in A},
                                  "median": {a: float(np.nanmedian(A[a][idx])) for a in A}}
    dom = {}
    for k_, h_ in PAR:
        n_ = k_ + "/" + h_
        dom["A_" + k_] = "HELDT" if all(ut["per_museum"][m]["A"][n_]["ki95"][1] < 1 for m in ("VA", "NM")) else "SLO FEIL"
        dom["B_" + k_] = "HELDT" if all(ut["per_museum"][m]["B"][n_]["ki95"][0] > 0 for m in ("VA", "NM")) else "SLO FEIL"
    c = lambda m, n_: ut["per_museum"][m]["C"][n_]["ki95"]
    dom["C_stilling"] = "HELDT" if all(c(m, "sete_h~sete_djupn")[1] < 0 and c(m, "sete_h~rygg_halling")[1] < 0 and c(m, "sete_djupn~rygg_halling")[0] > 0 for m in ("VA", "NM")) else "SLO FEIL"
    ut["dom"] = dom
    json.dump(ut, open(P_RES, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps(ut, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if "--kontroll" in sys.argv:
        kontroll()
    elif "--opne" in sys.argv:
        opne()
    else:
        print(__doc__)
