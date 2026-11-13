#!/usr/bin/env python3
"""14_mesh_maal.py - maal og silhuettar fraa 3D-modellane (GLB) i STOLAR.

For kvar stol: last ned GLB til ei temp-fil, sample overflata (punkt + normalar),
slett GLB, og rekn ut
  1. oppretting: kva akse er opp, kva akse er breidde/djupn, kva side er ryggen
  2. skala: kor godt mesh-boksen passar katalog-H/B/D, og skalering til katalog-H
  3. sitjehoegd (cm) + sitjedjupn/-breidde (ikkje validert)
  4. to binaere silhuettar, 1 cm/piksel, 200 cm hoegt x 160 cm breitt, golv = rad 0

Bruk (kjoer fraa repo-rota):
  python analyse/14_mesh_maal.py --validering          # 510 valideringsstolar
  python analyse/14_mesh_maal.py --split dev           # berre DEV-halvparten
  python analyse/14_mesh_maal.py --split test          # berre TEST-halvparten (EIN gong)
  python analyse/14_mesh_maal.py                       # alle vaksenstolar med maal_ok=1
  python analyse/14_mesh_maal.py ID1 ID2 ...           # utvalde id-ar
Resumerbar: id-ar som alt ligg i mesh_maal.csv blir hoppa over (--ny tvingar omrekning).
--lagre-cache lagrar samplepunkt (ca 2 MB/stol) i analyse/data/mesh_cache/;
--fraa-cache les dei i staden for aa laste ned (til metodeutvikling).

Silhuett-npz: `side` og `front` er bitpakka, form (N, 200, 20) uint8. Pakk ut med
  np.unpackbits(a, axis=-1)  -> (N, 200, 160); rad 0 = golv (snu med [::-1] for plotting).
Side: kolonne 0 = bak (ryggen alltid til venstre), kolonne 159 = framside.
Front: kolonne 80 = midt paa bbox, venstre/hoegre er vilkaarleg (modellens x-akse).
"""
import argparse, csv, io, os, sys, time, tempfile, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
REINSA = os.path.join(DATA, "stolar_reinsa.csv")
OUT_CSV = os.path.join(DATA, "mesh_maal.csv")
OUT_NPZ = os.path.join(DATA, "mesh_silhuettar.npz")
OUT_VAL = os.path.join(HERE, "14_validering.csv")
CACHE = os.path.join(DATA, "mesh_cache")
URL = "https://media.githubusercontent.com/media/lukketsvane/stolar-db/main/STOLAR/glb/{}.glb"

N_PUNKT = 150_000          # overflatepunkt per stol
SPLIT_SEED = 20261112      # fast seed for DEV/TEST
CANVAS_H, CANVAS_W = 200, 160
SEAT_METHOD = "v2"         # sjaa seat_height(); v2 var best paa DEV av v1-v4
FORCE_Y = False            # --tving-y: ignorer opp-akse-detektoren, bruk glTF sin +y
                           # (IKKJE brukt i DEV/TEST-valideringa; sjaa rapport)

FIELDS = ["id", "museum", "status", "opp_akse", "opp_tryggleik", "breidde_akse",
          "rygg_tryggleik", "skala_h", "avvik_b", "avvik_d", "H", "B", "D",
          "sete_cm", "sete_frac", "sete_areal", "sete_djupn_cm", "sete_breidde_cm",
          "flagg", "sek"]


# ------------------------------------------------------------------ data
def read_rows():
    with open(REINSA, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_of(ids):
    """Fast DEV/TEST-deling av valideringsmengda (halvparten kvar)."""
    ids = sorted(ids)
    perm = np.random.default_rng(SPLIT_SEED).permutation(len(ids))
    half = len(ids) // 2
    dev = {ids[i] for i in perm[:half]}
    return {i: ("DEV" if i in dev else "TEST") for i in ids}


# ------------------------------------------------------------------ innlasting
def download(cid, path):
    url = URL.format(urllib.parse.quote(cid))
    last = None
    for k in range(3):
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(path, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            return "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return "missing"
            last = e
        except Exception as e:  # nettverk
            last = e
        time.sleep(2 * (k + 1))
    return "dlfail:%s" % last


def sample_glb(path, n=N_PUNKT):
    """GLB -> (punkt float32 (n,3), normalar float32 (n,3)) i modellens eigen ramme."""
    import trimesh
    m = trimesh.load(path, force="mesh")
    pts, fi = trimesh.sample.sample_surface(m, n, seed=0)
    nor = m.face_normals[fi]
    return pts.astype(np.float32), nor.astype(np.float32)


def fetch_points(cid, tmpdir, use_cache, save_cache):
    cp = os.path.join(CACHE, cid + ".npz")
    if use_cache:
        if not os.path.exists(cp):
            return "missing", None, None     # (i cache-modus: ikkje i cachen = fanst ikkje ved nedlasting)
        z = np.load(cp)
        return "ok", z["p"], z["n"].astype(np.float32) / 127.0
    path = os.path.join(tmpdir, cid + ".glb")
    st = download(cid, path)
    if st != "ok":
        if os.path.exists(path):
            os.remove(path)
        return st, None, None
    try:
        p, n = sample_glb(path)
    except Exception as e:
        return "loadfail:%s" % type(e).__name__, None, None
    finally:
        if os.path.exists(path):
            os.remove(path)          # aldri behald GLB
    if save_cache:
        os.makedirs(CACHE, exist_ok=True)
        np.savez_compressed(cp, p=p, n=np.round(n * 127).astype(np.int8))
    return "ok", p, n


# ------------------------------------------------------------------ geometri
def up_axis(P, N):
    """Opp-akse: aksen med mest horisontal flate (|n.a|>0.9) samla i eit tynt hoegdesjikt
    (sete/underside). Returnerer (akse, tryggleik = best/nest-best)."""
    sc = []
    for a in range(3):
        lo, hi = P[:, a].min(), P[:, a].max()
        f = (P[:, a] - lo) / max(hi - lo, 1e-9)
        ok = np.abs(N[:, a]) > 0.9
        h = np.histogram(f[ok], bins=100, range=(0, 1))[0].astype(float)
        h = np.convolve(h, np.ones(3), "same")
        sc.append(h[15:86].max() / len(P))
    o = np.argsort(sc)[::-1]
    return int(o[0]), float(sc[o[0]] / max(sc[o[1]], 1e-9))


def seat_height(z, nz, H, method=SEAT_METHOD):
    """Sitjehoegd (cm) fraa punkt med hoegde z (cm, golv=0) og oppover-komponent nz av normalen.
    Returnerer (hoegde, areal-andel i toppen, flagg-liste)."""
    flags = []
    lo, hi = 0.25 * H, 0.65 * H
    cos = {"v1": 0.9, "v2": 0.9, "v3": 0.8, "v4": 0.9}[method]
    ok = nz > cos
    bins = np.arange(0, np.ceil(H) + 2, 1.0)          # 1 cm
    h = np.histogram(z[ok], bins=bins)[0].astype(float) / len(z)
    hs = np.convolve(h, np.ones(3) / 3, "same")
    centres = bins[:-1] + 0.5
    win = (centres >= lo) & (centres <= hi)
    if not win.any() or hs[win].max() <= 0:
        return np.nan, 0.0, ["ingen_flate"]
    idx = np.where(win)[0]
    k = idx[np.argmax(hs[idx])]
    peak = hs[k]
    if peak < 0.004:
        return np.nan, float(peak), ["ingen_flate"]
    if k in (idx[0], idx[-1]):
        flags.append("topp_ved_kant")
    # fleire like sterke toppar (t.d. armlene/fotbrett) -> flagg
    far = idx[np.abs(centres[idx] - centres[k]) > 8]
    if len(far) and hs[far].max() > 0.8 * peak:
        flags.append("fleire_toppar")
    est = centres[k]
    if method in ("v2", "v3", "v4"):
        # overkant av flata: hoegaste bin innanfor +-6 cm som har >= 50 % av toppen
        near = idx[(np.abs(centres[idx] - centres[k]) <= 6) & (centres[idx] >= centres[k] - 1)]
        strong = near[hs[near] >= 0.5 * peak]
        if method == "v2":
            est = centres[strong].max() - 0.5 if len(strong) else est
        if method in ("v3", "v4"):
            # areal-vekta middel av dei sterke binane (stabilare enn max)
            est = float((centres[strong] * hs[strong]).sum() / hs[strong].sum())
    return float(est), float(peak), flags


def width_axis(P, a_up, N_SUB=12000):
    """Breiddeaksen = den horisontale aksen med best speglsymmetri."""
    from scipy.spatial import cKDTree
    hor = [a for a in range(3) if a != a_up]
    rng = np.random.default_rng(0)
    S = P[rng.choice(len(P), min(N_SUB, len(P)), replace=False)]
    tree = cKDTree(S[:, hor])
    err = []
    for a in hor:
        c = 0.5 * (P[:, a].min() + P[:, a].max())
        Q = S[:, hor].copy()
        Q[:, hor.index(a)] = 2 * c - Q[:, hor.index(a)]
        d, _ = tree.query(Q)
        err.append(float(np.median(d)))
    w = hor[int(np.argmin(err))]
    return w, [a for a in hor if a != w][0], err


def project(Ppix_x, Ppix_y):
    """Punkt -> binaer bilete (CANVAS_H x CANVAS_W), rad 0 = golv."""
    import cv2
    img = np.zeros((CANVAS_H, CANVAS_W), np.uint8)
    x = np.floor(Ppix_x).astype(int)
    y = np.floor(Ppix_y).astype(int)
    ok = (x >= 0) & (x < CANVAS_W) & (y >= 0) & (y < CANVAS_H)
    img[y[ok], x[ok]] = 1
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return img, int((~ok).sum())


def analyse(P, N, rec, method=SEAT_METHOD):
    """P,N: punkt/normalar i modellramma. rec: katalograd (H,B,D i cm).
    Returnerer (rad-dict, side-bilete, front-bilete)."""
    H, B, D = float(rec["H"]), float(rec["B"]), float(rec["D"])
    row = {"id": rec["id"], "museum": rec["museum"], "H": H, "B": B, "D": D}
    flags = []
    ua, ucon = up_axis(P, N)
    if FORCE_Y:
        ua = 1
    row["opp_akse"] = "xyz"[ua]
    row["opp_tryggleik"] = round(ucon, 2)
    if ua != 1:
        flags.append("opp_ikkje_y")
    if ucon < 1.5:
        flags.append("opp_usikker")
    # opp-koordinat (positiv retning = +akse; sjaa kommentar om fortegn i rapport)
    up = P[:, ua] - P[:, ua].min()
    nzu = N[:, ua]
    ext_up = float(up.max())
    row["skala_h"] = round(ext_up * 100.0 / H, 4)        # mesh-hoegd (om meter) / katalog-H
    s = H / ext_up                                         # modell-eining -> cm, hoegd = H
    z = up * s
    sete, areal, f = seat_height(z, nzu, H, method)
    flags += f
    row["sete_cm"] = None if np.isnan(sete) else round(sete, 2)
    row["sete_frac"] = None if np.isnan(sete) else round(sete / H, 4)
    row["sete_areal"] = round(areal, 4)

    wa, da, err = width_axis(P, ua)
    row["breidde_akse"] = "xyz"[wa]
    ew, ed = float(np.ptp(P[:, wa])) * s, float(np.ptp(P[:, da])) * s
    row["avvik_b"] = round(ew / B - 1, 3)
    row["avvik_d"] = round(ed / D - 1, 3)
    # samsvar med katalog: er aksen eg kalla breidde nærmast B (relativt D)?
    if abs(np.log(ew / B)) + abs(np.log(ed / D)) > abs(np.log(ed / B)) + abs(np.log(ew / D)) + 0.15:
        flags.append("B_D_bytt?")
    if err[0] / max(err[1], 1e-9) > 0.8 and err[1] / max(err[0], 1e-9) > 0.8:
        flags.append("symmetri_uklar")

    # rygg-retning langs djupneaksen: hoge punkt (z > 70 % H) vs sete-sentrum
    d = (P[:, da] - 0.5 * (P[:, da].min() + P[:, da].max())) * s
    hi = z > 0.70 * H
    if not np.isnan(sete):
        ref = (np.abs(z - sete) <= 1.5) & (nzu > 0.9)
    else:
        ref = (z > 0.25 * H) & (z < 0.55 * H)
    if hi.sum() > 50 and ref.sum() > 50:
        diff = float(d[hi].mean() - d[ref].mean())
    else:
        diff = 0.0
    sgn = 1.0 if diff < 0 else -1.0                        # rygg paa den sida hoge punkt ligg
    # framretning-koordinat: aukar mot framsida (ryggen = lav kolonne)
    # rygg ved negativ d (diff<0) -> front = +d ; elles snu
    d_front = d if diff < 0 else -d
    row["rygg_tryggleik"] = round(abs(diff) / max(ed, 1e-9), 3)
    row["rygg_retning"] = ("+" if diff > 0 else "-") + "xyz"[da]
    if abs(diff) / max(ed, 1e-9) < 0.04:
        flags.append("rygg_usikker")

    # sitjedjupn/-breidde: oppovervendte punkt i +-1.5 cm rundt sitjehoegda, 2-98 persentil
    if not np.isnan(sete):
        m = (np.abs(z - sete) <= 1.5) & (nzu > 0.9)
        if m.sum() > 300:
            u_w = (P[m, wa] - P[:, wa].mean()) * s
            row["sete_djupn_cm"] = round(float(np.percentile(d_front[m], 98) - np.percentile(d_front[m], 2)), 1)
            row["sete_breidde_cm"] = round(float(np.percentile(u_w, 98) - np.percentile(u_w, 2)), 1)
    # silhuettar
    wcoord = (P[:, wa] - 0.5 * (P[:, wa].min() + P[:, wa].max())) * s
    side, c1 = project(d_front + CANVAS_W / 2, z)
    front, c2 = project(wcoord + CANVAS_W / 2, z)
    if c1 or c2:
        flags.append("silhuett_klipt")
    # fortegn paa opp: +akse er antatt opp. Kontroll (berre flagg): i ei oppreist stol er djupne-
    # spreiinga i dei 15 % hoegaste punkta (rygg) mindre enn i dei 15 % lagaste (bein/golvkontakt).
    top, bot = z > 0.85 * H, z < 0.15 * H
    if top.sum() > 50 and bot.sum() > 50 and d[top].std() > 1.0 * d[bot].std():
        flags.append("opp_ned?")
    row["flagg"] = ";".join(flags)
    return row, side, front


# ------------------------------------------------------------------ hovudloekke
def load_state():
    rows, ids, sid, sside, sfront = {}, [], [], [], []
    if os.path.exists(OUT_CSV):
        with open(OUT_CSV, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if r["status"].startswith("ok") or r["status"] == "missing":
                    rows[r["id"]] = r      # nettverks-/lastefeil blir prøvd paa nytt
    if os.path.exists(OUT_NPZ):
        z = np.load(OUT_NPZ, allow_pickle=False)
        sid = list(z["ids"])
        sside = list(z["side"])
        sfront = list(z["front"])
    return rows, {i: (a, b) for i, a, b in zip(sid, sside, sfront)}


def save_state(rows, sils):
    tmp = OUT_CSV + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS + ["rygg_retning"], extrasaction="ignore")
        w.writeheader()
        for i in sorted(rows):
            w.writerow(rows[i])
    os.replace(tmp, OUT_CSV)
    ids = sorted(sils)
    tmp = OUT_NPZ + ".tmp.npz"
    np.savez_compressed(tmp, ids=np.array(ids),
                        side=np.array([sils[i][0] for i in ids], np.uint8).reshape(-1, CANVAS_H, CANVAS_W // 8),
                        front=np.array([sils[i][1] for i in ids], np.uint8).reshape(-1, CANVAS_H, CANVAS_W // 8))
    os.replace(tmp, OUT_NPZ)


def write_validation(all_rows, truth, split):
    out = []
    for cid in sorted(truth):
        if cid not in all_rows:
            continue
        r = all_rows[cid]
        est = r.get("sete_cm")
        est = float(est) if est not in (None, "") else None
        out.append({"id": cid, "split": split[cid], "true_sete_cm": truth[cid],
                    "estimate_cm": "" if est is None else est,
                    "error_cm": "" if est is None else round(est - truth[cid], 2),
                    "status": r["status"], "flagg": r.get("flagg", "")})
    with open(OUT_VAL, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "split", "true_sete_cm", "estimate_cm", "error_cm", "status", "flagg"])
        w.writeheader()
        w.writerows(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--validering", action="store_true")
    ap.add_argument("--split", choices=["dev", "test"])
    ap.add_argument("--ny", action="store_true", help="rekn om alt, ignorer eksisterande resultat")
    ap.add_argument("--lagre-cache", action="store_true")
    ap.add_argument("--fraa-cache", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--sjekk", type=int, default=20, help="lagre kvar N-te stol")
    ap.add_argument("--tving-y", action="store_true", help="bruk +y som opp (glTF-standard) i staden for detektoren")
    a = ap.parse_args()
    global FORCE_Y
    FORCE_Y = a.tving_y

    recs = {r["id"]: r for r in read_rows()}
    base = [r for r in recs.values() if r["vaksenstol"] == "1" and r["maal_ok"] == "1"]
    val = [r["id"] for r in base if r["sete_ok"] == "1"]
    split = split_of(val)
    truth = {r["id"]: float(r["sete"]) for r in base if r["sete_ok"] == "1"}
    if a.ids:
        todo = a.ids
    elif a.split:
        todo = [i for i in val if split[i] == a.split.upper()]
    elif a.validering:
        todo = val
    else:
        todo = [r["id"] for r in base]
    todo = sorted(todo)
    for i in todo:
        if i not in recs or recs[i]["maal_ok"] != "1" or not recs[i]["H"]:
            print("hopper over (ikkje maal_ok):", i)
    todo = [i for i in todo if i in recs and recs[i]["maal_ok"] == "1" and recs[i]["H"]]

    rows, sils = ({}, {}) if a.ny else load_state()
    todo = [i for i in todo if i not in rows]
    if a.limit:
        todo = todo[:a.limit]
    print("skal gjere %d stolar (%d ferdige frå før)" % (len(todo), len(rows)), flush=True)

    tmpdir = tempfile.mkdtemp(prefix="stolar_glb_")
    t0 = time.time()
    done = 0
    try:
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            window = []
            it = iter(todo)

            def submit():
                try:
                    cid = next(it)
                except StopIteration:
                    return
                window.append((cid, ex.submit(fetch_points, cid, tmpdir, a.fraa_cache, a.lagre_cache)))
            for _ in range(a.workers + 1):
                submit()
            while window:
                cid, fut = window.pop(0)
                submit()
                st, P, N = fut.result()
                t1 = time.time()
                rec = recs[cid]
                if st != "ok":
                    rows[cid] = {"id": cid, "museum": rec["museum"], "status": st,
                                 "H": rec["H"], "B": rec["B"], "D": rec["D"]}
                else:
                    try:
                        row, side, front = analyse(P, N, rec)
                        row["status"] = "ok" if row.get("sete_cm") not in (None, "") else "ok_utan_sete"
                        row["sek"] = round(time.time() - t1, 2)
                        rows[cid] = row
                        sils[cid] = (np.packbits(side, axis=-1), np.packbits(front, axis=-1))
                    except Exception as e:
                        rows[cid] = {"id": cid, "museum": rec["museum"], "status": "feil:%s" % type(e).__name__,
                                     "H": rec["H"], "B": rec["B"], "D": rec["D"]}
                done += 1
                if done % a.sjekk == 0:
                    save_state(rows, sils)
                    print("%d/%d  %.1f s/stol" % (done, len(todo), (time.time() - t0) / done), flush=True)
    finally:
        save_state(rows, sils)
        try:
            for f in os.listdir(tmpdir):
                os.remove(os.path.join(tmpdir, f))
            os.rmdir(tmpdir)
        except OSError:
            pass
    write_validation(rows, truth, split)
    print("ferdig: %d stolar paa %.0f s (%.1f s/stol)" % (done, time.time() - t0, (time.time() - t0) / max(done, 1)))


if __name__ == "__main__":
    main()
