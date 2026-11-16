"""Validering av fotobasert setehøgd (cm) mot katalogverdiar.

Bruk:
  python analyse/02_fotomaaling.py download   # hent valideringsbilete til STOLAR/bguw/
  python analyse/02_fotomaaling.py dev        # metrikk på DEV (for justering)
  python analyse/02_fotomaaling.py test       # ÉIN køyring på TEST + baselines + CSV

Metode (klassisk, berre alfa-maske):
  1. Alfa > 127 gir silhuett. Behald samanhengande komponentar med areal >= 0.2 % av største.
  2. Silhuetthøgd Hs = botn - topp (px). Botn = lågaste silhuettpunkt (golvkontakt).
  3. Setet = nedste rad over ein minimumsklaring (5 % av Hs) der
       - fyllgrad (mask-piksel / utstrekning i raden) >= FILL_MIN, og
       - utstrekning (venstre-høgre) >= EXT_MIN * breidda på heile silhuetten.
     Det er den første slike rad når ein søkjer oppover frå botnen: legga smelter saman
     til ei brei, samanhengande plate. Det er undersida av sitteplata, ikkje overflata.
  4. seat_cm = H_katalog * (botn - setrad) / Hs.
  Vald trekk: undersida av sitteplata (horisontal plate under sitteflata), ikkje framkant.
"""
import csv
import sys
import random
import math
import urllib.request
import concurrent.futures as cf
from pathlib import Path

import numpy as np
from PIL import Image
import cv2

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "STOLAR" / "STOLAR.csv"
BG_DIR = ROOT / "STOLAR" / "bguw"
OUT_CSV = ROOT / "analyse" / "02_validering.csv"

SEED = 20260
UA = "stolar-validation/1.0"

# Parametrar (justerte kun på DEV)
FILL_MIN = 0.6
EXT_MIN = 0.5
WIDE = 0.75
CONT_FILL = 0.0  # iter 3 (0.7) brot startraden (fyll 0.60); bbruka iter 2 som endeleg
CLEAR_FRAC = 0.05
AREA_FRAC = 0.002

EKS = {"Krakk", "Barnestol", "Benkestol", "Stol utan rygg"}
H, B, D, SE, NEM, NASJ, OID, URL = (
    "Høgde (cm)", "Breidde (cm)", "Djupn (cm)", "Setehøgde (cm)",
    "Nemning", "Nasjonalmuseet", "Objekt-ID", "Bilete-bguw",
)


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_validation():
    """Returnerer liste av dict for valideringssettet (228 rader)."""
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        h, b, d, s = _f(r[H]), _f(r[B]), _f(r[D]), _f(r[SE])
        if None in (h, b, d, s):
            continue
        if s == h:  # 51 kopiar av totalhøgd: forkast
            continue
        if r[NEM] in EKS:
            continue
        if not (50 <= h <= 200 and 25 <= b <= 150 and 25 <= d <= 150 and s < h):
            continue
        if not (30 <= s <= 65):
            continue
        out.append({
            "id": r[OID], "url": r[URL], "H": h, "SE": s,
            "museum": "VA" if "vam.ac.uk" in r[NASJ] else "NM",
        })
    # Fast splitt: seed, sortert på ID før shuffle så rekkjefølgja i CSV ikkje spelar rolle
    out.sort(key=lambda x: x["id"])
    random.Random(SEED).shuffle(out)
    half = len(out) // 2
    for i, r in enumerate(out):
        r["split"] = "DEV" if i < half else "TEST"
    return out


# ---------------------------------------------------------------- nedlasting
def _fetch(row):
    dest = BG_DIR / f"{row['id']}_bguw.png"
    if dest.exists() and dest.stat().st_size > 0:
        return row["id"], "finst"
    if not row["url"]:
        return row["id"], "manglar_url"
    try:
        req = urllib.request.Request(row["url"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return row["id"], "ok"
    except urllib.error.HTTPError as e:
        return row["id"], f"http_{e.code}"
    except Exception as e:  # nettverksfeil
        return row["id"], f"feil_{type(e).__name__}"


def download(rows):
    BG_DIR.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        res = list(ex.map(_fetch, rows))
    from collections import Counter
    c = Counter(s for _, s in res)
    print("Nedlasting:", dict(c))
    return res


# ---------------------------------------------------------------- metode
SIL_DIST = 40  # maks kanal-avstand frå kvitt for å rekne piksel som objekt


def _white_mask(rgb):
    d = 255 - rgb.astype(np.int16).min(axis=2)  # 0 for kvitt, stor for mørkt/farga
    m = (d > SIL_DIST).astype(np.uint8)
    # fjern små støyflekkar og lukk 1-px hol frå kantsmoothing
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return m


def silhouette(path):
    """Returnerer bool-maske (rader x kolonnar) eller None.

    Dei nedlasta PNG-filene er RGB utan alfakanal (kvit bakgrunn, 255,255,255).
    Då blir silhuetten teken som piksel som avvik frå kvitt (maks kanal-avstand > SIL_DIST).
    Med ekte alfakanal (transparent bakgrunn) blir alfa > 127 brukt.
    """
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or "transparency" in im.info:
        im = im.convert("RGBA")
        alpha = np.array(im)[:, :, 3]
        if (alpha < 128).any():
            m = (alpha > 127).astype(np.uint8)
        else:
            m = _white_mask(np.array(im.convert("RGB")))
    else:
        m = _white_mask(np.array(im.convert("RGB")))
    if m.sum() == 0:
        return None
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    areas = stats[1:, cv2.CC_STAT_AREA]
    if len(areas) == 0:
        return None
    keep = np.zeros(n, bool)
    big = areas.max()
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= AREA_FRAC * big:
            keep[i] = True
    mask = keep[lab]
    ys, xs = np.where(mask)
    return mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def estimate(path, H_cat):
    """Seat height in cm, or None if no estimate."""
    m = silhouette(path)
    if m is None:
        return None
    rows = m.shape[0]
    occ = np.where(m.any(axis=1))[0]
    top, bot = occ.min(), occ.max()
    Hs = bot - top + 1
    if Hs < 20:
        return None
    cols = np.where(m.any(axis=0))[0]
    W = cols.max() - cols.min() + 1
    clear = int(CLEAR_FRAC * Hs)

    def row_stats(y):
        xs = np.where(m[y])[0]
        if xs.size == 0:
            return 0, 0.0
        ext = xs.max() - xs.min() + 1
        return ext, xs.size / ext

    # 1) finn nedre kant av sitteplata: første rad oppover med brei, fylt rad
    start = None
    for y in range(bot - clear, top, -1):
        ext, fill = row_stats(y)
        if fill >= FILL_MIN and ext >= EXT_MIN * W:
            start = y
            break
    if start is None:
        return None
    # 2) gå oppover så lenge raden er brei: øvste brei rad = overflata på sitteplata
    seat_row = start
    for y in range(start, top, -1):
        ext, fill_y = row_stats(y)
        if ext >= WIDE * W and fill_y >= CONT_FILL:
            seat_row = y
        else:
            break
    seat_px = bot - seat_row
    return H_cat * seat_px / Hs


# ---------------------------------------------------------------- evaluering
def metrics(true, pred_or_none):
    pairs = [(t, p) for t, p in zip(true, pred_or_none) if p is not None]
    n_all = len(true)
    n_none = n_all - len(pairs)
    if not pairs:
        return {"n": 0, "none_share": 1.0}
    t = np.array([a for a, _ in pairs])
    p = np.array([b for _, b in pairs])
    e = p - t
    sst = ((t - t.mean()) ** 2).sum()
    r2 = 1 - (e ** 2).sum() / sst if sst > 0 else float("nan")
    return {
        "n": len(pairs),
        "MAE": float(np.abs(e).mean()),
        "medAE": float(np.median(np.abs(e))),
        "bias": float(e.mean()),
        "R2": float(r2),
        "within2": float((np.abs(e) <= 2).mean()),
        "none_share": n_none / n_all,
    }


def fmt(name, m):
    if m.get("n", 0) == 0:
        return f"{name}: ingen estimat"
    return (f"{name}: n={m['n']} MAE={m['MAE']:.2f} medAE={m['medAE']:.2f} "
            f"bias={m['bias']:+.2f} R2={m['R2']:.3f} <=2cm={m['within2']:.1%} "
            f"ingen-estimat={m['none_share']:.1%}")


def run_method(rows):
    for r in rows:
        p = BG_DIR / f"{r['id']}_bguw.png"
        r["est"] = estimate(p, r["H"]) if p.exists() else None
    return rows


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "dev"
    rows = load_validation()
    from collections import Counter
    print(f"Valideringssett: n={len(rows)} museum={dict(Counter(r['museum'] for r in rows))} "
          f"split={dict(Counter(r['split'] for r in rows))}")
    if mode == "download":
        download(rows)
        return
    run_method(rows)
    dev = [r for r in rows if r["split"] == "DEV"]
    test = [r for r in rows if r["split"] == "TEST"]
    if mode == "dev":
        print(fmt("DEV metode", metrics([r["SE"] for r in dev], [r["est"] for r in dev])))
        return
    if mode == "test":
        # Baselines fitt på DEV
        c_const = float(np.median([r["SE"] for r in dev]))
        ratio = float(np.median([r["SE"] / r["H"] for r in dev]))
        T = [r["SE"] for r in test]
        print(fmt("TEST metode", metrics(T, [r["est"] for r in test])))
        print(fmt("TEST baseline konstant", metrics(T, [c_const] * len(test))))
        print(fmt("TEST baseline andel av H", metrics(T, [ratio * r["H"] for r in test])))
        # Same subset comparison: test rows where method has estimate
        sub = [r for r in test if r["est"] is not None]
        if sub:
            Ts = [r["SE"] for r in sub]
            print(fmt("TEST samme delsett: konstant", metrics(Ts, [c_const] * len(sub))))
            print(fmt("TEST samme delsett: andel av H", metrics(Ts, [ratio * r["H"] for r in sub])))
            print(fmt("TEST samme delsett: metode", metrics(Ts, [r["est"] for r in sub])))
        print(f"DEV median setehøgd={c_const:.2f}, DEV median ratio={ratio:.4f}")
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["Objekt-ID", "split", "setehøgd_sann_cm", "estimat_cm", "feil_cm"])
            for r in rows:
                est = r["est"]
                w.writerow([r["id"], r["split"], f"{r['SE']:.2f}",
                            "" if est is None else f"{est:.2f}",
                            "" if est is None else f"{est - r['SE']:+.2f}"])
        print("Skreiv", OUT_CSV)
        # Worst TEST cases
        worst = sorted([r for r in test if r["est"] is not None],
                       key=lambda r: -abs(r["est"] - r["SE"]))[:10]
        for r in worst:
            print(f"  {r['id']}  sann={r['SE']:.1f} est={r['est']:.1f} feil={r['est']-r['SE']:+.1f}")


if __name__ == "__main__":
    main()
