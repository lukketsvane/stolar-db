"""38_ramme3d.py - 3D-ramma: kontaktflatene og vokselforma til kvar stol i ramma, rett frå punktskyene.

Les analyse/data/mesh_cache/<id>.npz (150 000 overflatepunkt med normalar), set stolen i ei felles ramme
(x: bak til fram, y: breidd, z: opp, alt i cm, golvet i z = 0) og måler:
  sete:   høgd, djupn, breidd, halling (grader, positiv når framkanten ligg høgast)
  rygg:   halling frå loddlina (grader, positiv bakover), målt 12 til 45 cm over setet midt på stolen
  rom:    avstanden frå framkanten av setet til ryggflata 20 cm over setet (plassen kroppen har)
  arm:    høgd over setet (venstre og høgre), og opninga mellom armlena
  fot:    djupn, breidd og areal på fotavtrykket (punkt under 3 cm)
  voksel: 64 x 64 x 60 ruter på 2,5 cm

  python analyse/38_ramme3d.py   -> analyse/data/ramme3d.npz, analyse/data/ramme3d_paalitelegheit.json
"""
import csv, json, os, sys, time
import numpy as np
import ramme

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HER, "data", "mesh_cache")
MAAL = ["sete_h", "sete_djupn", "sete_breidd", "sete_halling", "rygg_halling", "rom_djupn", "arm_v", "arm_h", "arm_opning",
        "fot_djupn", "fot_breidd", "fot_areal", "djupn3d", "breidd3d"]
VX, VZ, RUTE = 64, 60, 2.5


def kanonisk(P, N, m, H):
    """Modellramme -> (x fram, y breidd, z opp) i cm, og normalane i same ramme."""
    ua, wa = "xyz".index(m["opp_akse"]), "xyz".index(m["breidde_akse"])
    da = [a for a in range(3) if a not in (ua, wa)][0]
    up = P[:, ua] - P[:, ua].min()
    s = H / float(up.max())
    z = up * s
    d = (P[:, da] - 0.5 * (P[:, da].min() + P[:, da].max())) * s
    fram = 1.0 if (m.get("rygg_retning") or "-").startswith("-") else -1.0
    x = d * fram
    y = (P[:, wa] - 0.5 * (P[:, wa].min() + P[:, wa].max())) * s
    Nf = N.astype(np.float32) / 127.0
    return x, y, z, Nf[:, da] * fram, Nf[:, wa], Nf[:, ua]


def linje(u, v, steg, min_n=30, min_bolk=4):
    """Robust stigning dv/du: median av v i bolkar av u, så minste kvadrat på bolkmedianane."""
    b = np.floor(u / steg).astype(int)
    uu, vv = [], []
    for k in np.unique(b):
        i = b == k
        if i.sum() >= min_n:
            uu.append(np.median(u[i]))
            vv.append(np.median(v[i]))
    if len(uu) < min_bolk:
        return np.nan, np.nan
    st, sk = np.polyfit(uu, vv, 1)
    return float(st), float(sk)


def maal_stol(x, y, z, nx, ny, nz, s0):
    ut = dict.fromkeys(MAAL, np.nan)
    ut["djupn3d"], ut["breidd3d"] = float(np.ptp(x)), float(np.ptp(y))
    golv = z < 3
    if golv.sum() > 200:
        ut["fot_djupn"] = float(np.percentile(x[golv], 99) - np.percentile(x[golv], 1))
        ut["fot_breidd"] = float(np.percentile(y[golv], 99) - np.percentile(y[golv], 1))
        try:
            from scipy.spatial import ConvexHull
            k = np.where(golv)[0]
            k = k[:: max(1, len(k) // 4000)]
            ut["fot_areal"] = float(ConvexHull(np.column_stack([x[k], y[k]])).volume)
        except Exception:
            pass
    if not np.isfinite(s0):
        return ut
    flate = (np.abs(z - s0) <= 2.5) & (nz > 0.85)
    if flate.sum() < 300:
        return ut
    ut["sete_h"] = float(s0)
    xf, xb = np.percentile(x[flate], 98), np.percentile(x[flate], 2)
    ut["sete_djupn"] = float(xf - xb)
    ut["sete_breidd"] = float(np.percentile(y[flate], 98) - np.percentile(y[flate], 2))
    w = max(ut["sete_breidd"], 30.0)
    midt = np.abs(y) < 0.30 * w
    # setehalling: oppovervende flate innan 6 cm frå setehøgda, midtstripa
    sf = midt & (nz > 0.8) & (np.abs(z - s0) <= 6) & (x > xb + 0.1 * (xf - xb)) & (x < xf - 0.05 * (xf - xb))
    if sf.sum() > 300:
        st, _ = linje(x[sf], z[sf], 3.0)
        if np.isfinite(st):
            ut["sete_halling"] = float(np.degrees(np.arctan(st)))
    # rygghalling: framovervende flate bak midten av setet, 12 til 45 cm over setet, midtstripa
    rf = midt & (nx > 0.3) & (z > s0 + 12) & (z < s0 + 45) & (x < 0.5 * (xf + xb))
    if rf.sum() > 300:
        st, sk = linje(z[rf], x[rf], 3.0)
        if np.isfinite(st):
            ut["rygg_halling"] = float(np.degrees(np.arctan(-st)))
            ut["rom_djupn"] = float(xf - (st * (s0 + 20) + sk))
    # armlene: oppovervende flater 10 til 40 cm over setet, utanfor 80 % av halve setebreidda
    af = (nz > 0.8) & (z > s0 + 10) & (z < s0 + 40) & (np.abs(y) > 0.4 * ut["sete_breidd"]) & (x > xb) & (x < xf + 5)
    v, h = af & (y < 0), af & (y > 0)
    if v.sum() > 250 and h.sum() > 250:
        ut["arm_v"], ut["arm_h"] = float(np.median(z[v]) - s0), float(np.median(z[h]) - s0)
        ut["arm_opning"] = float(np.percentile(y[h], 5) - np.percentile(y[v], 95))
    return ut


def voksel(x, y, z):
    g = np.zeros((VZ, VX, VX), bool)
    ix, iy, iz = np.floor((x + 80) / RUTE).astype(int), np.floor((y + 80) / RUTE).astype(int), np.floor(z / RUTE).astype(int)
    ok = (ix >= 0) & (ix < VX) & (iy >= 0) & (iy < VX) & (iz >= 0) & (iz < VZ)
    g[iz[ok], ix[ok], iy[ok]] = True
    return np.packbits(g.reshape(-1))


def icc(verdiar, suite):
    """Einvegs ICC(1) over suitar med minst to medlemer: kor likt blir stolar av same modell målte?"""
    ok = np.isfinite(verdiar)
    grupper = [verdiar[ok & (suite == s)] for s in np.unique(suite[ok])]
    grupper = [g for g in grupper if len(g) >= 2]
    if len(grupper) < 15:
        return np.nan, len(grupper)
    k = np.mean([len(g) for g in grupper])
    alle = np.concatenate(grupper)
    msb = sum(len(g) * (g.mean() - alle.mean()) ** 2 for g in grupper) / (len(grupper) - 1)
    msw = sum(((g - g.mean()) ** 2).sum() for g in grupper) / (len(alle) - len(grupper))
    return float((msb - msw) / (msb + (k - 1) * msw)), len(grupper)


if __name__ == "__main__":
    R = ramme.last()
    mm = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "mesh_maal.csv"), encoding="utf-8"))}
    n = len(R["id"])
    M = np.full((n, len(MAAL)), np.nan)
    V = np.zeros((n, VZ * VX * VX // 8), np.uint8)
    t0 = time.time()
    for k, cid in enumerate(R["id"]):
        sti = os.path.join(CACHE, cid + ".npz")
        if not os.path.exists(sti):
            continue
        zf = np.load(sti)
        x, y, z, nx, ny, nz = kanonisk(zf["p"], zf["n"], mm[cid], float(R["H"][k]))
        r = maal_stol(x, y, z, nx, ny, nz, float(R["sete_mesh"][k]))
        M[k] = [r[a] for a in MAAL]
        V[k] = voksel(x, y, z)
        if k % 200 == 0:
            print(k, "av", n, "| %.0f s" % (time.time() - t0), flush=True)
    np.savez_compressed(os.path.join(HER, "data", "ramme3d.npz"), id=R["id"], maal=M, namn=np.array(MAAL), voksel=V)
    # pålitelegheit: same modell fotografert kvar for seg (ICC over suitar), og samsvar med katalogen
    ut = {"n": n, "maal": {}}
    for j, a in enumerate(MAAL):
        ic, ng = icc(M[:, j], R["suite"])
        ut["maal"][a] = {"n": int(np.isfinite(M[:, j]).sum()), "icc_suite": None if np.isnan(ic) else round(ic, 3), "suitar": ng,
                         "median": round(float(np.nanmedian(M[:, j])), 2),
                         "kvartilar": [round(float(np.nanpercentile(M[:, j], q)), 2) for q in (25, 75)]}
    for namn_, mesh, kat in (("sete_h mot katalogsete", M[:, 0], R["sete_kat"]), ("djupn3d mot katalog D", M[:, 12], R["D"]), ("breidd3d mot katalog B", M[:, 13], R["B"])):
        for mus in ("VA", "NM"):
            ok = np.isfinite(mesh) & np.isfinite(kat) & (R["museum"] == mus)
            if ok.sum() > 20:
                ut.setdefault("samsvar", {})["%s, %s" % (namn_, mus)] = {"n": int(ok.sum()), "r": round(float(np.corrcoef(mesh[ok], kat[ok])[0, 1]), 3),
                                                                             "median_avvik": round(float(np.median(mesh[ok] - kat[ok])), 2),
                                                                             "median_abs_avvik": round(float(np.median(np.abs(mesh[ok] - kat[ok]))), 2)}
    json.dump(ut, open(os.path.join(HER, "data", "ramme3d_paalitelegheit.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps(ut, ensure_ascii=False, indent=1))
