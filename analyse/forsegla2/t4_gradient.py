#!/usr/bin/env python3
"""t4_gradient.py - N3: "Stilperiodar er gradientar, ikkje oeyar" (prop 3.302), second sealed test.

Run from the repository root (DEV and synthetic populations only, never the held-out sample):
    python analyse/forsegla2/t4_gradient.py

WHAT IS TESTED
  Within one material regime (solid-wood chairs before 1900) no date is an island edge: chairs on either side
  of a boundary year differ no more than chairs the same number of years apart on one side of it.

THE STATISTIC, in the order it is computed (every number below is a literal constant of this file)
  1. Sample: records of felles.les(utval) with materialklasse == 'WOOD', a year (aar = aar_fraa) below 1900,
     passing felles.kvalitet() and felles.kvalitet_front().
  2. Distance d(i, j): front silhouette (200 x 160, 1 cm per pixel, as stored, no re-alignment), blurred with a
     Gaussian of sigma 2 cm (cv2.GaussianBlur, kernel from sigma), d = 1 - sum(min) / sum(max) over the whole
     canvas (soft Jaccard distance; the history designer's formrom.avst with zone 'heil').
  3. S(b) for a boundary year b: take the chairs with |aar - b| <= 50. Pairs: unordered, both chairs in the
     same museum, not in the same suite, 10 <= |aar_i - aar_j| <= 40. A pair straddles b when exactly one of
     its chairs has aar >= b; otherwise it is a same-side pair. Time-gap classes c = min((gap - 10) // 5, 6)
     (10-14, 15-19, ..., 35-39, 40). Over the classes that hold at least 3 straddling and at least 3 same-side
     pairs:   S(b) = sum_c n_kryss(c) * [mean d(straddling, c) - mean d(same side, c)] / sum_c n_kryss(c).
     S(b) is undefined (NaN) with fewer than 30 straddling or fewer than 30 same-side pairs. A smooth gradient
     gives S(b) = 0; an island edge at b gives S(b) > 0.
  4. splice(G), the planted island: for a site b0, delete the chairs with b0 <= aar < b0 + G, move every later
     chair G years back, and compute S(b0) on the changed dates (the chairs just before b0 now face chairs that
     are really G years younger than their dates say). splice(G) is the MEAN over the sites b0 in
     (1662, 1687, ..., 1862 - G) that keep at least 150 straddling pairs after the splice.
  5. Armchair against chair: the same statistic with the two sides defined by catalogue type (Armstol against
     Stol/Spisestol) instead of a year, pairs 0-40 years apart (classes 0-4, ..., 35-39, 40), whole sample.
  6. Intervals: felles.klyngebootstrap over suites, 2000 resamples, seed felles.FRO. The bootstrap draws whole
     suites; a chair drawn m times enters every pair with weight m (pairs of a chair with its own copy are
     same-suite pairs and never counted), which is exactly the statistic recomputed on the resampled list.

SCORING (three outcomes fixed in advance, plus the void verdict)
  UGYLDIG  if a gate fails (see SPEC['port']).
  SLO FEIL ('OEY')      some primary boundary with >= 150 straddling pairs has a 95 % lower bound above 0 AND a
                        point estimate at or above splice(50).
  HELDT ('GRADIENT')    for every such boundary the one-sided upper bound of S(b), Bonferroni-corrected over
                        the boundaries used (quantile 1 - 0.05/k of the bootstrap), lies below splice(50).
  UAVGJORT              neither: reported as such. It is NOT support for 3.302.

WHAT THE DESIGN CAN AND CANNOT DO (measured by syntetisk_kontroll(), see SPEC['eigenskapar_fraa_simulering'])
  HELDT is practically out of reach at the available sample sizes: the Bonferroni upper bounds (about 0.10)
  are three times the 50-year splice (about 0.03). The informative outcomes are SLO FEIL and UAVGJORT.
  Under a pure gradient the plain 95 % lower bound of the OEY rule gives a false SLO FEIL in about one run in
  eight; the Bonferroni variant (reported as a secondary line) in about one in twenty.

RUNTIME on an idle machine: about 10 minutes (kjoer('dev') 5 s; the synthetic controls score about 800
populations). kjoer('held') is expected to take a few minutes (about 640 silhouettes, 204 000 distances).

BLINDNESS: the only reads of sealed material are felles.les('held') and felles.silhuett('held') inside
_last('held'); both are guarded by felles and are never called by __main__.
"""
import os
import sys

import cv2
import numpy as np
from scipy import sparse
from scipy.spatial.distance import cdist, pdist, squareform

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import felles  # noqa: E402

# ============================================================================ frozen constants
GRENSER_PRIM = (1662, 1687, 1712, 1737, 1762, 1787, 1812, 1837, 1862, 1887)     # off the heaped round years
GRENSER_RUNDE = (1650, 1675, 1700, 1725, 1750, 1775, 1800, 1825, 1850, 1875)    # robustness line
AAR_MAKS = 1900          # sample: aar < 1900
VINDAUGE = 50            # chairs within b +/- 50 years
GAP_LO, GAP_HI = 10, 40  # pair time gap for S(b) and splice
ARM_LO, ARM_HI = 0, 40   # pair time gap for the armchair control
KLASSE = 5               # width of the time-gap classes (years)
MIN_KLASSE = 3           # pairs of each kind needed for a gap class to count
MIN_GOLV = 30            # below this many straddling or same-side pairs S is undefined (NaN)
MIN_KRYSS = 150          # straddling pairs needed for a boundary (or a splice site) to be used
MIN_GRENSER = 5          # primary boundaries needed for a valid test
SPENN_MAKS = 15          # dating restriction of the primary sample: spenn known and <= 15 years
SIGMA = 2.0              # cm, Gaussian blur of the silhouettes
ALFA = 0.05              # one-sided level, Bonferroni-divided over the boundaries used (GRADIENT bound)
OEY_NEDRE_KVANTIL = 2.5  # percentile of the bootstrap used as 'lower bound' in the OEY rule (plain 95 % interval)
SPLEIS_G = (25, 50, 75, 100)                                 # ladder of planted islands (years)
SPLEIS_SISTE_SEINSIDE = 1862                                  # a site b0 is admissible for G if b0 + G <= 1862
PRIMAERMUSEUM = "VA"
ARMTYPE = "Armstol"
STOLTYPAR = ("Stol", "Spisestol")

SPEC = {
    "id": "N3",
    "tittel": "Period styles are gradients, not islands: no boundary year inside wood before 1900 is an island "
              "edge as large as 50 years of drift (front silhouettes of 3D models)",
    "slag": "ny",
    "proposisjonar": ["3.302", "3.3", "4.12", "4.2"],
    "paastand": (
        "Within one material regime (solid-wood chairs before 1900) no date is an island edge. Chairs on either "
        "side of any boundary year differ no more than chairs the same number of years apart on one side of it. "
        "An edge at splice level within wood before 1900 counts against 3.302 whatever its historical "
        "explanation (Restoration, a new court style, a change of workshop practice); 4.12 is then the "
        "proposition that must carry it, and 3.302 gets a qualifier. "
        "A GRADIENT verdict means only: 'no island larger than about 50 years of drift is visible with this "
        "instrument'. It is not support for gradients in general. Museum datings are in part assigned from the "
        "look of the chair, which favours gradients, and the splice control shares that weakness; rounded and "
        "uncertain datings smear a real edge. A pass is therefore weaker evidence than a fail."),
    "utval": {
        "definisjon": (
            "felles.les(utval) records with materialklasse == 'WOOD' (felles.materialklasse on the catalogue "
            "tokens), aar (= aar_fraa) known and < 1900, passing felles.kvalitet(rec, side, front) (which also "
            "drops copied dimension records, maal_kopi) and felles.kvalitet_front(rec, front). No lower year "
            "limit; chairs outside every window simply enter no boundary statistic."),
        "primaer": (
            "museum == 'VA' and dating span known and at most 15 years (rec['spenn'] is not None and "
            "rec['spenn'] <= 15; spenn == 0 is a catalogued exact year). Pairs within the museum only."),
        "dateringsval": (
            "DECIDED 13 Nov 2026 FROM CATALOGUE COUNTS ONLY (function tel_par_katalog(), no mesh file read). "
            "V&A held-out, WOOD, aar < 1900, not maal_kopi: 624 chairs, of which 243 have spenn <= 15 (75 exact "
            "year, 168 with 1-15 years), 223 have no end year (single-year or 'ca.' datings whose span is not "
            "recorded: NOT counted as narrow), 158 have spenn > 15. Straddling pairs of the 243 at the ten "
            "primary boundaries, before any silhouette loss: 149, 280, 400, 678, 1797, 1372, 374, 288, 545, 581. "
            "The DEV pass rate of the silhouette rules for this class is 149 of 175 = 0.85, so about 0.72 of "
            "the pairs survive: 9 of 10 boundaries are expected to keep >= 150 straddling pairs (8 even if only "
            "half the pairs survive). The rule was: restricted sample primary if at least five boundaries keep "
            "150 pairs. It does, so the RESTRICTED sample is primary and the unrestricted sample is a robustness "
            "line. Cost, known in advance: boundary 1662 (the Restoration date of the handbooks and the "
            "designer's one DEV candidate) is expected to fall below 150 pairs in the primary sample and is then "
            "judged on the unrestricted robustness line only."),
        "robustheit": [
            "V&A, all datings (unrestricted), primary boundaries",
            "V&A, restricted, round-year boundaries 1650 ... 1875",
            "V&A, all datings, round-year boundaries",
            "V&A, restricted, pairs of the same catalogue type only (armchair-armchair, chair-chair)",
            "V&A, restricted, SIDE silhouette (depth is partly generated by the 3D model; secondary by design)",
            "Nasjonalmuseet, restricted and unrestricted (secondary; too few chairs for most boundaries)",
            "both museums together, pairs within one museum only, bootstrap stratified by museum",
        ],
    },
    "avstand": "front silhouette, Gaussian blur sigma 2 cm, d = 1 - sum(min)/sum(max) over the whole 200 x 160 canvas",
    "grensestatistikk": (
        "S(b): chairs with |aar - b| <= 50; unordered pairs within one museum, not in the same suite, with time "
        "gap 10-40 years; straddling = exactly one chair has aar >= b. Gap classes of 5 years (10-14, ..., "
        "35-39, 40); over classes with >= 3 straddling and >= 3 same-side pairs, S(b) = straddling-pair-weighted "
        "mean over classes of [mean distance of straddling pairs - mean distance of same-side pairs]. "
        "Undefined below 30 pairs of either kind. Pure gradient: S(b) = 0."),
    "grenser": {"primaer": list(GRENSER_PRIM), "runde_robustheit": list(GRENSER_RUNDE)},
    "positive_kontrollar": {
        "spleis": (
            "splice(G): at site b0 delete chairs with b0 <= aar < b0 + G, move later chairs G years back, compute "
            "S(b0). splice(G) = mean over the admissible sites b0 in the primary grid with b0 + G <= 1862 "
            "(G = 50: 1662 ... 1812; G = 100: 1662 ... 1762) that keep >= 150 straddling pairs. Recomputed by "
            "this frozen script on the sample it scores (the held-out sample at unsealing). "
            "WHY A MEAN OVER SITES (decided here; the designer used the single site 1750): a real island lying "
            "in the deleted span of a single splice site adds its own size to the yardstick, so that the island "
            "could never reach 'splice level'; and one site is as noisy as one boundary. Averaged over the sites "
            "an island still raises the yardstick somewhat (in the latent model splice(50) rises from 0.034 to "
            "0.039 with a 100-year island), so OEY is expected only for islands clearly larger than 50 years."),
        "armstol_mot_stol": (
            "type 'Armstol' against type 'Stol' or 'Spisestol' (other types left out of this control), pairs "
            "0-40 years apart within one museum and not in one suite, gap classes of 5 years, same formula."),
    },
    "primaer": [
        {"namn": "OEY (island found): number of primary boundaries with >= 150 straddling pairs whose 95 % "
                 "cluster-bootstrap lower bound of S(b) is above 0 AND whose point estimate is >= splice(50)",
         "statistikk": "count over the boundaries used of [q2.5(S(b)) > 0 and S(b) >= splice(50)]",
         "terskel": 0, "retning": "== 0 (one or more gives SLO FEIL)",
         "regel_for_terskel": (
             "inference reviewer's ISLAND rule, read literally: the lower bound is that of the plain 95 % "
             "percentile interval (2.5th percentile), NOT Bonferroni-corrected. Measured consequence (latent "
             "model, pure gradient, expected primary sample size): OEY by chance in about 11-14 % of runs; with "
             "a Bonferroni lower bound it would be about 5 %. The Bonferroni variant is computed and reported "
             "as a secondary line. splice(50) is recomputed on the scored sample."),
         "dev_verdi": "0 of 8 boundaries used (DEV proxy: both museums as one, all datings, n = 149); the primary "
                      "line itself cannot be computed on DEV (24 chairs, no boundary with 150 pairs)"},
        {"namn": "GRADIENT: largest Bonferroni one-sided upper bound of S(b) over the boundaries used, minus "
                 "splice(50)",
         "statistikk": "max_b q(1 - 0.05/k)(S(b)) - splice(50), k = number of boundaries used",
         "terskel": 0.0, "retning": "< 0",
         "regel_for_terskel": (
             "inference reviewer's equivalence rule: every upper bound below the planted 50-year island. "
             "0.05 one-sided, divided by k. splice(50) is the point value recomputed on the scored sample."),
         "dev_verdi": "+0.089 (DEV proxy: largest upper bound 0.118 at 1837, splice(50) 0.029)"},
    ],
    "konjunksjon": "dom = UGYLDIG if a gate fails; else SLO FEIL if OEY count >= 1; else HELDT if GRADIENT "
                   "difference < 0; else UAVGJORT (reported as such; not support).",
    "sekundaer": [
        "smallest detectable splice: the smallest G in (25, 50, 75, 100) whose splice(G) has a 95 % lower bound "
        "above 0 (the resolution of the instrument on the scored sample)",
        "OEY with the Bonferroni one-sided lower bound (quantile 0.05/k) in place of the plain 95 % bound",
        "GRADIENT with the uncertainty of the yardstick included: Bonferroni upper bound of S(b) - splice(50) "
        "from the joint bootstrap, below 0 at every boundary used",
        "mean of S(b) over the boundaries used against half of splice(50) (the designer's original second line)",
        "S(b), interval and outcome on each robustness line of SPEC['utval']['robustheit']",
        "per-site splice values, splice(100) - splice(50) with its own bootstrap SE",
        "share of straddling and same-side pairs that mix armchair and chair, per boundary (type-mix check: "
        "armchair-chair pairs are about 0.09 farther apart, so a change of the armchair share across a boundary "
        "moves S(b) without any change of form)",
        "share of chairs dated exactly on a 25-year mark in the scored sample",
    ],
    "port": [
        {"namn": "P1 splice(50) detected", "terskel": 0.0,
         "ugyldig_dersom": "95 % cluster-bootstrap lower bound of splice(50) <= 0",
         "dev_verdi": "-0.002 (DEV proxy; splice(50) = 0.029 [-0.002, 0.055]): the gate FAILS on DEV by a hair"},
        {"namn": "P2 armchair against chair detected", "terskel": 0.0,
         "ugyldig_dersom": "95 % cluster-bootstrap lower bound of the armchair statistic <= 0",
         "dev_verdi": "+0.058 (DEV proxy; statistic 0.092 [0.058, 0.126])"},
        {"namn": "P3 dose-response of the splice", "terskel": "splice(50) - 1 bootstrap SE of splice(50)",
         "ugyldig_dersom": "splice(100) < splice(50) - SE_boot(splice(50))  (SE = SD of the 2000 bootstrap "
                           "values of splice(50); the reviewer's wording, read literally)",
         "dev_verdi": "splice(100) = 0.078 against a threshold of 0.029 - 0.015 = 0.014 (DEV proxy): passes"},
        {"namn": "P4 enough boundaries", "terskel": 5,
         "ugyldig_dersom": "fewer than 5 primary boundaries with >= 150 straddling pairs, or no admissible "
                           "splice site with >= 150 straddling pairs for G = 50 or for G = 100",
         "dev_verdi": "8 (DEV proxy); 0 on the real primary line of DEV"},
    ],
    "grunnmodell": (
        "ISLANDS: the periodisation of the handbooks, with sharp changes near 1660, 1715-30, 1770 and 1830. "
        "Named before sealing: it predicts S(b) at or above splice(50) with a lower bound above 0 at one or "
        "more of the primary boundaries 1662, 1712 or 1737, 1762 or 1787, and 1837 (round-year line: 1650, 1725, "
        "1775, 1825). If that happens the base model wins and 3.302 has lost at that date. A second base model, "
        "'no time structure in silhouettes at all', is excluded by gate P1."),
    "tel_imot": (
        "One or more primary boundaries at splice level (OEY). No historical explanation offered afterwards "
        "rescues 3.302 (7.153); the edge is then carried by 4.12. UAVGJORT does not count for 3.302 either."),
    "dev": {
        "primaerlinja_paa_DEV": "V&A with spenn <= 15: 24 chairs, no boundary with 150 straddling pairs, no "
                                "splice site: UGYLDIG. DEV cannot run the primary line.",
        "DEV_proxy": (
            "all DEV WOOD chairs before 1900 that pass the silhouette rules (149; NM 83, V&A 66), all datings, the "
            "two museums treated as one (cross-museum pairs allowed): 8 boundaries used. S(b) at 1662 ... 1837: "
            "-0.004, -0.044, -0.015, -0.011, -0.002, +0.020, -0.024, +0.008 (bootstrap SE 0.023-0.043). "
            "splice(25) 0.020 [-0.006, 0.042]; splice(50) 0.029 [-0.002, 0.055]; splice(75) 0.066 [0.026, 0.094]; "
            "splice(100) 0.078 [0.032, 0.117]; armchair against chair 0.092 [0.058, 0.126]. Smallest detectable "
            "splice 75 years. Outcome UGYLDIG (P1). Round-year line: 1650 has S = +0.093 [0.029, 0.161] on 60 "
            "pairs (below the 150-pair rule), the designer's candidate."),
        "DEV_par_innan_museum": (
            "same 149 chairs with pairs inside one museum only: 3 boundaries used (1687, 1712, 1737: -0.058, "
            "-0.008, -0.028), splice(50) 0.011 [-0.057, 0.072] on 2 sites, armchair 0.099 [0.061, 0.134]: UGYLDIG."),
    },
    "eigenskapar_fraa_simulering": (
        "Operating characteristics of this exact scoring code, from syntetisk_kontroll() (seed 3302). "
        "(1) HELDT is out of reach: with the expected primary sample (about 206 chairs) the largest Bonferroni "
        "upper bound is about 0.10 and splice(50) about 0.034; a latent pure gradient gave GRADIENT in 0 of 60 "
        "runs (1 of 60 at the size of the unrestricted sample, about 530 chairs). The test can end SLO FEIL, "
        "UGYLDIG or UAVGJORT; it can practically not end HELDT. "
        "(2) Under a latent pure gradient at the expected size: UAVGJORT 0.77, OEY 0.13, UGYLDIG 0.10 (60 runs; "
        "a separate run of 150 gave 0.74, 0.11, 0.15). "
        "(3) Power against an island cut into the latent history at 1762: 50 years OEY 0.35, 100 years 0.68, "
        "150 years 0.70. An island of 150 years at 1662 is seen in 0.08 of runs, the false-alarm rate: the "
        "primary sample is blind at 1662. "
        "(4) DEV-sized real silhouettes (149 chairs as one museum), dates jittered +-25 years: UAVGJORT 0.77, "
        "UGYLDIG 0.17, OEY 0.06, GRADIENT 0.00 (100 draws). With a 50-year island planted at 1737: OEY 0.17, "
        "UAVGJORT 0.34, UGYLDIG 0.49; planting by deletion shrinks a DEV-sized sample so much that the gates "
        "fail, and with a 100-year island every run is UGYLDIG."),
}


# ============================================================================ sample
def _er_smal(r):
    """Dating restriction of the primary sample: span known and <= SPENN_MAKS years."""
    return r["spenn"] is not None and r["spenn"] <= SPENN_MAKS


def _last(utval):
    """-> (recs, sil, fraafall). recs: the sample of SPEC['utval']['definisjon'] (both museums, all datings).
    'held' goes through the guarded felles.les('held') / felles.silhuett('held')."""
    alle = felles.les(utval)
    sil = felles.silhuett(utval)
    fraafall = {"lese": len(alle), "ikkje_WOOD": 0, "utan_aar": 0, "aar_fraa_1900": 0, "kvalitet": 0,
                "kvalitet_grunnar": {}, "front_kvalitet": 0}
    recs = []
    for r in alle:
        if r["materialklasse"] != "WOOD":
            fraafall["ikkje_WOOD"] += 1
            continue
        if r["aar"] is None:
            fraafall["utan_aar"] += 1
            continue
        if r["aar"] >= AAR_MAKS:
            fraafall["aar_fraa_1900"] += 1
            continue
        side, front = sil.get(r["id"], (None, None))
        ok, grunn = felles.kvalitet(r, side, front)
        if not ok:
            fraafall["kvalitet"] += 1
            for g in grunn.split(";"):
                fraafall["kvalitet_grunnar"][g] = fraafall["kvalitet_grunnar"].get(g, 0) + 1
            continue
        ok, grunn = felles.kvalitet_front(r, front)
        if not ok:
            fraafall["front_kvalitet"] += 1
            continue
        recs.append(r)
    fraafall["i_utvalet"] = len(recs)
    for m in ("VA", "NM"):
        fraafall["i_utvalet_" + m] = sum(r["museum"] == m for r in recs)
        fraafall["i_utvalet_%s_spenn_hoegst_15" % m] = sum(r["museum"] == m and _er_smal(r) for r in recs)
        fraafall["i_utvalet_%s_utan_sluttaar" % m] = sum(r["museum"] == m and r["spenn"] is None for r in recs)
    return recs, sil, fraafall


def _avstand(bilete):
    """bilete: list of (200,160) 0/1 arrays -> (N,N) float64 soft Jaccard distance after Gaussian blur.
    Uses sum(min) = (A + B - L1)/2 and sum(max) = (A + B + L1)/2, so d = 2*L1 / (A + B + L1); identical (to
    1e-6) to the designer's loop 1 - sum(min)/sum(max)."""
    if len(bilete) == 0:
        return np.zeros((0, 0))
    X = np.stack([cv2.GaussianBlur(np.asarray(b, np.float32), (0, 0), SIGMA) for b in bilete])
    X = X.reshape(len(X), -1).astype(np.float64)
    X = X[:, X.max(0) > 0]                      # columns that are zero everywhere add nothing to L1
    A = X.sum(1)
    L1 = squareform(pdist(X, "cityblock")) if len(X) > 1 else np.zeros((1, 1))
    return 2.0 * L1 / np.maximum(A[:, None] + A[None, :] + L1, 1e-9)


def _populasjon(recs, sil, syn="front", D=None):
    """Arrays for the scoring code. syn: 'front' or 'side'."""
    if D is None:
        k = 1 if syn == "front" else 0
        D = _avstand([sil[r["id"]][k] for r in recs])
    suitar = sorted({felles.suite(r) for r in recs})
    kode = {s: j for j, s in enumerate(suitar)}
    typ = np.array([1 if r["type"] == ARMTYPE else (0 if r["type"] in STOLTYPAR else -1) for r in recs], int)
    return {
        "id": [r["id"] for r in recs],
        "aar": np.array([r["aar"] for r in recs], int),
        "mus": np.array([r["museum"] for r in recs], object),
        "suite": np.array([kode[felles.suite(r)] for r in recs], int),
        "suitenamn": [felles.suite(r) for r in recs],
        "arm": typ,
        "smal": np.array([_er_smal(r) for r in recs], bool),
        "D": D,
    }


def _delpop(pop, maske):
    """Sub-population (boolean mask or index array)."""
    ix = np.nonzero(maske)[0] if np.asarray(maske).dtype == bool else np.asarray(maske, int)
    return {
        "id": [pop["id"][i] for i in ix], "aar": pop["aar"][ix].copy(), "mus": pop["mus"][ix],
        "suite": pop["suite"][ix], "suitenamn": [pop["suitenamn"][i] for i in ix], "arm": pop["arm"][ix],
        "smal": pop["smal"][ix], "D": pop["D"][np.ix_(ix, ix)],
    }


# ============================================================================ pair statistic
def _par(pop, aar, med, side, lo, hi, same_type=False):
    """Eligible pairs among the chairs in `med`: same museum, different suite, lo <= gap <= hi.
    side: bool per chair (the two sides). -> dict with i, j, d, g (= 2*gap class + straddling), counts."""
    ix = np.nonzero(med)[0]
    t = aar[ix]
    dt = np.abs(t[:, None] - t[None, :])
    m = np.triu(np.ones((len(ix), len(ix)), bool), 1) & (dt >= lo) & (dt <= hi)
    m &= pop["mus"][ix][:, None] == pop["mus"][ix][None, :]
    m &= pop["suite"][ix][:, None] != pop["suite"][ix][None, :]
    if same_type:
        a = pop["arm"][ix]
        m &= (a[:, None] == a[None, :]) & (a[:, None] >= 0)
    a, b = np.nonzero(m)
    i, j = ix[a], ix[b]
    nkl = (hi - lo) // KLASSE + 1
    kl = np.minimum((dt[a, b] - lo) // KLASSE, nkl - 1)
    kryss = (side[i] != side[j]).astype(int)
    g = 2 * kl + kryss
    arm = pop["arm"]
    blanda = (arm[i] >= 0) & (arm[j] >= 0) & (arm[i] != arm[j])
    return {"i": i, "j": j, "d": pop["D"][i, j], "g": g.astype(int), "nkl": int(nkl),
            "n_kryss": int(kryss.sum()), "n_same": int(len(kryss) - kryss.sum()), "n_stolar": int(len(ix)),
            "blanda_kryss": float(blanda[kryss == 1].mean()) if kryss.sum() else None,
            "blanda_same": float(blanda[kryss == 0].mean()) if (kryss == 0).sum() else None}


def _par_grense(pop, b, same_type=False):
    aar = pop["aar"]
    return _par(pop, aar, np.abs(aar - b) <= VINDAUGE, aar >= b, GAP_LO, GAP_HI, same_type)


def _spleis_datoar(aar, b0, G):
    """The planted island: -> (new dates, kept mask). Chairs with b0 <= aar < b0 + G are deleted, later chairs
    are moved G years back."""
    ny = aar.copy()
    ny[aar >= b0 + G] -= G
    return ny, ~((aar >= b0) & (aar < b0 + G))


def _par_spleis(pop, b0, G, same_type=False):
    ny, behald = _spleis_datoar(pop["aar"], b0, G)
    return _par(pop, ny, behald & (np.abs(ny - b0) <= VINDAUGE), ny >= b0, GAP_LO, GAP_HI, same_type)


def _par_arm(pop):
    arm = pop["arm"]
    return _par(pop, pop["aar"], arm >= 0, arm == 1, ARM_LO, ARM_HI)


def _S_fraa_summar(n, s):
    """n, s: (R, 2*nkl) weighted pair counts and distance sums per group (even = same side, odd = straddling).
    -> (R,) S values (NaN where undefined)."""
    ns, nk = n[:, 0::2], n[:, 1::2]
    ss, sk = s[:, 0::2], s[:, 1::2]
    ok = (nk >= MIN_KLASSE) & (ns >= MIN_KLASSE)
    with np.errstate(divide="ignore", invalid="ignore"):
        diff = np.where(ok, sk / nk - ss / ns, 0.0)
        w = np.where(ok, nk, 0.0)
        S = (w * diff).sum(1) / w.sum(1)
    S[(nk.sum(1) < MIN_GOLV) | (ns.sum(1) < MIN_GOLV) | (w.sum(1) <= 0)] = np.nan
    return S


def _S(par, M=None):
    """S for one pair set. M None: the point value (float). M (R, N) chair multiplicities of R bootstrap
    resamples: (R,) values, each exactly the statistic on the resampled list of chairs."""
    G = 2 * par["nkl"]
    P = len(par["i"])
    if M is None:
        n = np.bincount(par["g"], minlength=G).astype(float)[None]
        s = np.bincount(par["g"], weights=par["d"], minlength=G)[None]
        return float(_S_fraa_summar(n, s)[0])
    R = M.shape[0]
    if P == 0:
        return np.full(R, np.nan)
    # weighted count of group g in resample r = sum over its pairs of M[r, i] * M[r, j] = m A_g m^T, with m the
    # multiplicities of the chairs that occur in the pair set and A_g the sparse incidence of the pairs of
    # group g; the G matrices are stacked into one
    lok, inv = np.unique(np.concatenate([par["i"], par["j"]]), return_inverse=True)
    i, j, N = inv[:P], inv[P:], len(lok)
    A = sparse.csr_matrix((np.ones(P), (par["g"] * N + i, j)), shape=(G * N, N))
    Ad = sparse.csr_matrix((par["d"], (par["g"] * N + i, j)), shape=(G * N, N))
    ut = np.empty(R)
    steg = max(1, int(2e7 // (G * N)))
    for a in range(0, R, steg):
        Mt = np.ascontiguousarray(M[a:a + steg, lok].T, dtype=np.float64)       # (N, r)
        n = np.einsum("gnr,nr->rg", (A @ Mt).reshape(G, N, -1), Mt)
        sd = np.einsum("gnr,nr->rg", (Ad @ Mt).reshape(G, N, -1), Mt)
        ut[a:a + steg] = _S_fraa_summar(n, sd)
    return ut


def _multiplisitetar(pop, n_boot, seed, strata=None):
    """(n_boot, N) float32: how many times each chair is drawn in each cluster-bootstrap resample.
    The resampling itself is felles.klyngebootstrap (whole suites, with replacement)."""
    N = len(pop["id"])
    recs = [{"id": pop["id"][i], "suite": pop["suitenamn"][i], "museum": pop["mus"][i], "_i": i} for i in range(N)]
    if N == 0:
        return np.zeros((n_boot, 0), np.float32)
    M = felles.klyngebootstrap(recs, lambda rs: np.bincount([r["_i"] for r in rs], minlength=N),
                               n=n_boot, seed=seed, strata=strata)
    return np.asarray(M, np.float32).reshape(n_boot, N)


def _kv(x, q):
    x = np.asarray(x, float)
    return float(np.nanpercentile(x, q)) if np.isfinite(x).any() else float("nan")


def _f(x, d=4):
    """JSON-safe rounded float (NaN/None -> None)."""
    if x is None:
        return None
    x = float(x)
    return round(x, d) if np.isfinite(x) else None


def _oppsummer(verdi, boot):
    boot = np.asarray(boot, float)
    return {"verdi": _f(verdi), "ki95": [_f(_kv(boot, 2.5)), _f(_kv(boot, 97.5))],
            "se_boot": _f(np.nanstd(boot)) if np.isfinite(boot).any() else None,
            "nan_del_boot": _f(np.mean(~np.isfinite(boot)), 3)}


# ============================================================================ scoring (one code path for all)
def _stader(G):
    return [b for b in GRENSER_PRIM if b + G <= SPLEIS_SISTE_SEINSIDE]


def _skaar(pop, grenser, n_boot=None, seed=None, strata=None, same_type=False, full=True):
    """The whole scoring of one population and one set of boundaries.
    -> dict with per-boundary values, controls, gates, the two primary criteria and 'utfall' in
    {'GRADIENT', 'OEY', 'UAVGJORT', 'UGYLDIG'}. Used unchanged for DEV, held-out and synthetic populations."""
    n_boot = felles.N_BOOT if n_boot is None else n_boot
    seed = felles.FRO if seed is None else seed
    M = _multiplisitetar(pop, n_boot, seed, strata)

    # ---- boundaries
    gr = []
    for b in grenser:
        par = _par_grense(pop, b, same_type)
        v = _S(par)
        bt = _S(par, M)
        gr.append({"b": int(b), "n_stolar": par["n_stolar"], "n_kryss": par["n_kryss"], "n_same": par["n_same"],
                   "brukt": bool(par["n_kryss"] >= MIN_KRYSS and np.isfinite(v)),
                   "blanda_kryss": _f(par["blanda_kryss"], 3), "blanda_same": _f(par["blanda_same"], 3),
                   "_v": v, "_boot": bt})
    brukt = [g for g in gr if g["brukt"]]
    k = len(brukt)

    # ---- splice ladder (mean over admissible sites with enough pairs)
    spleis = {}
    for G in SPLEIS_G:
        per = []
        for b0 in _stader(G):
            par = _par_spleis(pop, b0, G, same_type)
            v = _S(par)
            if par["n_kryss"] >= MIN_KRYSS and np.isfinite(v):
                per.append({"stad": int(b0), "n_kryss": par["n_kryss"], "n_same": par["n_same"], "_v": v,
                            "_boot": _S(par, M)})
        if per:
            v = float(np.mean([p["_v"] for p in per]))
            bt = np.mean([p["_boot"] for p in per], axis=0)      # NaN at a site makes the resample NaN
        else:
            v, bt = float("nan"), np.full(n_boot, np.nan)
        spleis[G] = {"_v": v, "_boot": bt, "per": per}
    s50, s100 = spleis[50], spleis[100]

    # ---- armchair against chair
    pa = _par_arm(pop)
    arm_v, arm_b = _S(pa), _S(pa, M)

    # ---- gates
    s50_lo = _kv(s50["_boot"], 2.5)
    s50_se = float(np.nanstd(s50["_boot"])) if np.isfinite(s50["_boot"]).any() else float("nan")
    arm_lo = _kv(arm_b, 2.5)
    p1 = bool(np.isfinite(s50_lo) and s50_lo > 0.0)
    p2 = bool(np.isfinite(arm_lo) and arm_lo > 0.0)
    p3 = bool(np.isfinite(s100["_v"]) and np.isfinite(s50["_v"]) and np.isfinite(s50_se)
              and s100["_v"] >= s50["_v"] - s50_se)
    p4 = bool(k >= MIN_GRENSER and len(s50["per"]) >= 1 and len(s100["per"]) >= 1)
    port = [
        {"namn": "P1 splice(50) lower bound > 0", "verdi": _f(s50_lo), "terskel": 0.0, "ok": p1},
        {"namn": "P2 armchair-against-chair lower bound > 0", "verdi": _f(arm_lo), "terskel": 0.0, "ok": p2},
        {"namn": "P3 splice(100) >= splice(50) - SE", "verdi": _f(s100["_v"]),
         "terskel": _f(s50["_v"] - s50_se), "ok": p3},
        {"namn": "P4 boundaries with >= %d straddling pairs" % MIN_KRYSS, "verdi": k, "terskel": MIN_GRENSER,
         "ok": p4, "spleisestader_G50": len(s50["per"]), "spleisestader_G100": len(s100["per"])},
    ]
    port_ok = p1 and p2 and p3 and p4

    # ---- the two primary criteria
    q_bonf = 100.0 * (1.0 - ALFA / k) if k else float("nan")
    n_oey, oey_ved, oey_bonf_ved, ovre_maks, ovre_felles_maks = 0, [], [], float("nan"), float("nan")
    for g in gr:
        bt = g["_boot"] if np.isfinite(g["_v"]) else np.full(n_boot, np.nan)   # no interval without a point value
        g["_boot"] = bt
        g["ki95"] = [_kv(bt, OEY_NEDRE_KVANTIL), _kv(bt, 100.0 - OEY_NEDRE_KVANTIL)]
        g["ovre_bonf"] = _kv(bt, q_bonf) if (k and g["brukt"]) else float("nan")
        g["nedre_bonf"] = _kv(bt, 100.0 - q_bonf) if (k and g["brukt"]) else float("nan")
        g["ovre_bonf_mot_spleis"] = _kv(bt - s50["_boot"], q_bonf) if (k and g["brukt"]) else float("nan")
        paa_nivaa = bool(g["brukt"] and np.isfinite(s50["_v"]) and g["_v"] >= s50["_v"])
        g["oey"] = bool(paa_nivaa and g["ki95"][0] > 0.0)
        g["oey_bonf"] = bool(paa_nivaa and g["nedre_bonf"] > 0.0)
        if g["oey"]:
            n_oey += 1
            oey_ved.append(g["b"])
        if g["oey_bonf"]:
            oey_bonf_ved.append(g["b"])
    if k:
        ovre_maks = float(np.max([g["ovre_bonf"] for g in brukt]))
        ovre_felles_maks = float(np.max([g["ovre_bonf_mot_spleis"] for g in brukt]))
    gradient_diff = ovre_maks - s50["_v"] if (k and np.isfinite(s50["_v"])) else float("nan")
    gradient = bool(np.isfinite(gradient_diff) and gradient_diff < 0.0)
    if not port_ok:
        utfall = "UGYLDIG"
    elif n_oey >= 1:
        utfall = "OEY"
    elif gradient:
        utfall = "GRADIENT"
    else:
        utfall = "UAVGJORT"

    # ---- smallest detectable splice
    minste = None
    for G in SPLEIS_G:
        lo = _kv(spleis[G]["_boot"], 2.5)
        if np.isfinite(lo) and lo > 0.0:
            minste = G
            break

    snitt_S = float(np.mean([g["_v"] for g in brukt])) if k else float("nan")
    snitt_boot = np.mean([g["_boot"] for g in brukt], axis=0) if k else np.full(n_boot, np.nan)
    ut = {
        "n": len(pop["id"]), "n_suitar": int(len(set(pop["suite"].tolist()))), "n_boot": int(n_boot),
        "grenser_brukte": [g["b"] for g in brukt], "k": k,
        "bonferroni_kvantil": _f(q_bonf, 3) if k else None,
        "utfall": utfall, "port_ok": bool(port_ok), "port": port,
        "oey": {"tal": n_oey, "ved": oey_ved},
        "oey_med_bonferroni_nedre_grense": {"tal": len(oey_bonf_ved), "ved": oey_bonf_ved},
        "gradient": {"storste_ovre_grense": _f(ovre_maks), "spleis50": _f(s50["_v"]),
                     "differanse": _f(gradient_diff), "held": gradient},
        "spleis50": _oppsummer(s50["_v"], s50["_boot"]),
        "spleis100": _oppsummer(s100["_v"], s100["_boot"]),
        "armstol_mot_stol": dict(_oppsummer(arm_v, arm_b), n_kryss=pa["n_kryss"], n_same=pa["n_same"]),
        "minste_paaviselege_spleis": minste,
    }
    if full:
        ut["grenser"] = [{
            "b": g["b"], "n_stolar": g["n_stolar"], "n_kryss": g["n_kryss"], "n_same": g["n_same"],
            "brukt": g["brukt"], "S": _f(g["_v"]), "ki95": [_f(g["ki95"][0]), _f(g["ki95"][1])],
            "ovre_bonf": _f(g["ovre_bonf"]), "nedre_bonf": _f(g["nedre_bonf"]),
            "ovre_bonf_S_minus_spleis50": _f(g["ovre_bonf_mot_spleis"]),
            "se_boot": _f(np.nanstd(g["_boot"])) if np.isfinite(g["_boot"]).any() else None,
            "nan_del_boot": _f(np.mean(~np.isfinite(g["_boot"])), 3), "oey": g["oey"],
            "blanda_type_kryss": g["blanda_kryss"], "blanda_type_same": g["blanda_same"]} for g in gr]
        ut["spleis"] = {str(G): dict(_oppsummer(spleis[G]["_v"], spleis[G]["_boot"]),
                                     per_stad=[{"stad": p["stad"], "n_kryss": p["n_kryss"], "S": _f(p["_v"]),
                                                "ki95": [_f(_kv(p["_boot"], 2.5)), _f(_kv(p["_boot"], 97.5))]}
                                               for p in spleis[G]["per"]]) for G in SPLEIS_G}
        d = s100["_boot"] - s50["_boot"]
        ut["spleis100_minus_spleis50"] = _oppsummer(s100["_v"] - s50["_v"], d)
        ut["gradient_med_uvisse_i_maalestokken"] = {
            "storste_ovre_grense_S_minus_spleis50": _f(ovre_felles_maks),
            "held": bool(np.isfinite(ovre_felles_maks) and ovre_felles_maks < 0.0)}
        ut["snitt_S_mot_halv_spleis"] = dict(_oppsummer(snitt_S, snitt_boot), halv_spleis50=_f(s50["_v"] / 2)
                                             if np.isfinite(s50["_v"]) else None)
        ut["del_paa_25_aars_merke"] = _f(np.mean(pop["aar"] % 25 == 0), 3) if len(pop["id"]) else None
    return ut


def _dom(utfall):
    return {"GRADIENT": "HELDT", "OEY": "SLO FEIL", "UGYLDIG": "UGYLDIG", "UAVGJORT": "UAVGJORT"}[utfall]


# ============================================================================ the run
_MINNE = {}


def _alt(utval):
    """Sample, populations (front and side) and all scored lines for one utval; cached within the process."""
    if utval in _MINNE:
        return _MINNE[utval]
    recs, sil, fraafall = _last(utval)
    pop = _populasjon(recs, sil, "front")
    va, nm = pop["mus"] == PRIMAERMUSEUM, pop["mus"] == "NM"
    smal = pop["smal"]
    mus_lag = lambda r: r["museum"]
    linjer = {}

    def linje(namn, maske, grenser, **kw):
        linjer[namn] = _skaar(_delpop(pop, maske), grenser, **kw)

    linje("PRIMAER VA spenn<=15, primaergrenser", va & smal, GRENSER_PRIM)
    linje("VA spenn<=15, runde grenser", va & smal, GRENSER_RUNDE)
    linje("VA alle dateringar, primaergrenser", va, GRENSER_PRIM)
    linje("VA alle dateringar, runde grenser", va, GRENSER_RUNDE)
    linje("VA spenn<=15, berre par av same type", va & smal, GRENSER_PRIM, same_type=True)
    linje("NM spenn<=15, primaergrenser", nm & smal, GRENSER_PRIM)
    linje("NM alle dateringar, primaergrenser", nm, GRENSER_PRIM)
    linje("begge museum spenn<=15 (par innan museum), primaergrenser", smal, GRENSER_PRIM, strata=mus_lag)
    linje("begge museum alle dateringar (par innan museum), primaergrenser", np.ones(len(smal), bool),
          GRENSER_PRIM, strata=mus_lag)
    linje("begge museum alle dateringar (par innan museum), runde grenser", np.ones(len(smal), bool),
          GRENSER_RUNDE, strata=mus_lag)
    ix = np.nonzero(va & smal)[0]
    Dside = _avstand([sil[recs[i]["id"]][0] for i in ix])
    side_pop = _delpop(pop, ix)
    side_pop["D"] = Dside
    linjer["VA spenn<=15, SIDEsilhuett, primaergrenser"] = _skaar(side_pop, GRENSER_PRIM)
    _MINNE[utval] = {"recs": recs, "sil": sil, "fraafall": fraafall, "pop": pop, "linjer": linjer}
    return _MINNE[utval]


def kjoer(utval):
    """utval in {'dev', 'held'}. 'held' reads the sealed sample through the guarded loader."""
    a = _alt(utval)
    L = a["linjer"]
    namn_p = "PRIMAER VA spenn<=15, primaergrenser"
    p = L[namn_p]
    dom = _dom(p["utfall"])
    primaer = [
        {"namn": SPEC["primaer"][0]["namn"], "verdi": p["oey"]["tal"], "ved_grenser": p["oey"]["ved"],
         "ki95": None, "terskel": 0, "held": bool(p["port_ok"] and p["oey"]["tal"] == 0),
         "merknad": "a count; the intervals are those of S(b) under 'grenser'"},
        {"namn": SPEC["primaer"][1]["namn"], "verdi": p["gradient"]["differanse"],
         "storste_ovre_grense": p["gradient"]["storste_ovre_grense"], "spleis50": p["spleis50"]["verdi"],
         "spleis50_ki95": p["spleis50"]["ki95"], "ki95": None, "terskel": 0.0,
         "held": bool(p["port_ok"] and p["gradient"]["held"]),
         "merknad": "the statistic is itself a Bonferroni bound minus the yardstick; see 'grenser' for intervals"},
    ]
    sekundaer = [{"namn": "primary line in full (boundaries, splice ladder, controls)", "verdi": p}]
    sekundaer.append({"namn": "smallest detectable splice (years), primary line",
                      "verdi": p["minste_paaviselege_spleis"],
                      "merknad": "None = not even the 100-year splice has a lower bound above 0"})
    sekundaer.append({"namn": "OEY with the Bonferroni one-sided lower bound instead of the plain 95 % bound, "
                              "primary line (no verdict)",
                      "verdi": p["oey_med_bonferroni_nedre_grense"]["tal"],
                      "ved_grenser": p["oey_med_bonferroni_nedre_grense"]["ved"]})
    sekundaer.append({"namn": "GRADIENT with the uncertainty of the yardstick included, primary line (no verdict)",
                      "verdi": p["gradient_med_uvisse_i_maalestokken"]})
    sekundaer.append({"namn": "mean S(b) over the boundaries used against half of splice(50), primary line",
                      "verdi": p["snitt_S_mot_halv_spleis"]})
    for namn, v in L.items():
        if namn != namn_p:
            sekundaer.append({"namn": "robustness line: " + namn, "utfall_utan_dom": v["utfall"], "verdi": v})
    return {
        "id": SPEC["id"], "utval": utval, "n": p["n"], "n_suitar": p["n_suitar"],
        "fraafall": dict(a["fraafall"], primaerlinje_VA_spenn_hoegst_15=p["n"]),
        "port": p["port"] + [{"namn": "alle portar", "ok": p["port_ok"]}],
        "primaer": primaer, "sekundaer": sekundaer, "utfall": p["utfall"], "dom": dom,
        "domsforklaring": "HELDT = GRADIENT, SLO FEIL = OEY, UGYLDIG = a gate failed, UAVGJORT = neither "
                          "criterion met (reported as such, no support for 3.302)",
    }


# ============================================================================ figure data
BOLKAR = tuple(range(1600, 1900, 25))


def _snittsilhuettar(recs, sil, maske):
    """Mean front silhouette per 25-year bin 1600-1899, at 2 cm resolution, rows 0-149 cm (row 0 = floor),
    columns 20-139 (120 cm wide, middle at column 30 of the small array). Each row is a string of digits 0-9:
    digit = floor(10 * share of chairs that cover the cell), 9 also for a share of 1."""
    ut = []
    for a in BOLKAR:
        ids = [r["id"] for r, m in zip(recs, maske) if m and a <= r["aar"] < a + 25]
        if not ids:
            ut.append({"fraa": a, "n": 0, "rader": []})
            continue
        m = np.mean([sil[i][1].astype(np.float32) for i in ids], axis=0)[:150, 20:140]
        m = m.reshape(75, 2, 60, 2).mean(axis=(1, 3))
        z = np.minimum((m * 10).astype(int), 9)
        ut.append({"fraa": a, "n": len(ids), "rader": ["".join(str(v) for v in rad) for rad in z]})
    return ut


def figurdata(utval):
    a = _alt(utval)
    L, pop, recs, sil = a["linjer"], a["pop"], a["recs"], a["sil"]

    def kort(v):
        return {"utfall": v["utfall"], "n": v["n"], "k": v["k"],
                "grenser": [{"b": g["b"], "S": g["S"], "ki95": g["ki95"], "ovre_bonf": g["ovre_bonf"],
                             "n_kryss": g["n_kryss"], "brukt": g["brukt"]} for g in v["grenser"]],
                "spleis": {G: {"verdi": s["verdi"], "ki95": s["ki95"]} for G, s in v["spleis"].items()},
                "armstol_mot_stol": {"verdi": v["armstol_mot_stol"]["verdi"], "ki95": v["armstol_mot_stol"]["ki95"]}}

    # mean distance against time gap (10-year classes), within-museum pairs, for an inset
    kurve = {}
    for m in ("VA", "NM"):
        ix = np.nonzero(pop["mus"] == m)[0]
        if len(ix) < 3:
            continue
        t = pop["aar"][ix]
        dt = np.abs(t[:, None] - t[None, :])
        iu = np.triu(np.ones_like(dt, bool), 1) & (pop["suite"][ix][:, None] != pop["suite"][ix][None, :])
        D = pop["D"][np.ix_(ix, ix)]
        kurve[m] = [{"gap_fraa": g, "n_par": int((iu & (dt >= g) & (dt < g + 10)).sum()),
                     "snitt_d": _f(D[iu & (dt >= g) & (dt < g + 10)].mean())
                     if (iu & (dt >= g) & (dt < g + 10)).any() else None} for g in range(0, 250, 10)]
    va = [r["museum"] == "VA" for r in recs]
    return {
        "id": SPEC["id"], "utval": utval,
        "linjer": {namn: kort(v) for namn, v in L.items()},
        "primaerlinje": "PRIMAER VA spenn<=15, primaergrenser",
        "avstand_mot_tidsgap": kurve,
        "snittsilhuettar_front": {
            "forklaring": "per 25-year bin 1600-1899; 75 rows (2 cm each, row 0 = floor) x 60 columns (2 cm each, "
                          "canvas columns 20-139); digit = floor(10 x share of chairs covering the cell), max 9",
            "VA_alle_dateringar": _snittsilhuettar(recs, sil, va),
            "begge_museum": _snittsilhuettar(recs, sil, [True] * len(recs)),
        },
    }


# ============================================================================ catalogue-only counts
def tel_par_katalog():
    """UNGUARDED, CATALOGUE ONLY: the counts behind SPEC['utval']['dateringsval']. Straddling pairs per primary
    boundary among held-out WOOD chairs before 1900 (not maal_kopi), per museum, restricted and unrestricted,
    BEFORE any silhouette loss. Uses felles._held_ids() and felles._katalogpostar(), which read stolar_reinsa.csv
    and STOLAR.csv only (no mesh file, no silhouette)."""
    recs = felles._katalogpostar(felles._held_ids()[0])
    ut = {}
    for mus in ("VA", "NM"):
        u = [r for r in recs if r["museum"] == mus and r["materialklasse"] == "WOOD" and r["aar"] is not None
             and r["aar"] < AAR_MAKS and not r["maal_kopi"]]
        for namn, rs in (("spenn<=15", [r for r in u if _er_smal(r)]), ("alle", u)):
            suitar = sorted({r["suite"] for r in rs})
            kode = {s: j for j, s in enumerate(suitar)}
            pop = {"aar": np.array([r["aar"] for r in rs], int), "mus": np.array([mus] * len(rs), object),
                   "suite": np.array([kode[r["suite"]] for r in rs], int), "arm": np.zeros(len(rs), int),
                   "D": np.zeros((len(rs), len(rs)))}
            ut["%s %s" % (mus, namn)] = {
                "n": len(rs), "utan_sluttaar": sum(r["spenn"] is None for r in rs),
                "kryssande_par": {b: _par_grense(pop, b)["n_kryss"] for b in GRENSER_PRIM}}
    return ut


# ============================================================================ synthetic controls
SYN_FRO = 3302            # seed of the synthetic populations (the bootstrap keeps felles.FRO)
SYN_REP = 100             # jitter replicates for the DEV-sized outcome frequencies
SYN_LATENT_REP = 60       # replicates per scenario of the latent model
SYN_BOOT_REP = 1000       # bootstrap resamples inside the replicate loops (the two named runs use 2000)
SYN_OEY_STAD = 1737       # where the island is planted in control (a)
SYN_SLINGRING = 25        # years of uniform jitter in control (b)


def _dev_syntetisk_grunnlag():
    """The DEV sample (both museums, all datings) as ONE synthetic museum, so that a DEV-sized population has
    enough pairs: real silhouettes, real dates, real suites and types; only the museum label is merged."""
    a = _alt("dev")
    pop = _delpop(a["pop"], np.ones(len(a["pop"]["id"]), bool))
    pop["mus"] = np.array(["SYN"] * len(pop["id"]), object)
    return pop


def _plant_oey(pop, b0, G):
    """Plant an island of G years at b0 in the dates: delete chairs with b0 <= aar < b0 + G, move later chairs
    G years back (the splice, applied to the population itself)."""
    ny, behald = _spleis_datoar(pop["aar"], b0, G)
    p = _delpop(pop, behald)
    p["aar"] = ny[behald]
    return p


def _slingre(pop, rng, breidd=SYN_SLINGRING):
    """Dates jittered by a uniform integer in [-breidd, +breidd]: every edge in the dates is smeared, the
    gradient stays. The base model 'islands' is false by construction."""
    p = _delpop(pop, np.ones(len(pop["id"]), bool))
    p["aar"] = pop["aar"] + rng.integers(-breidd, breidd + 1, len(pop["id"]))
    return p


# Calibration of the latent model: least-squares fit of the mean SQUARED front distance against time gap on the
# merged DEV sample (149 chairs, 10-year gap classes 0-220, pairs of different suites):
#     E d^2(gap) = 0.210 + 0.000333 * gap + 0.065 * (1 - exp(-gap / 81.5))
# (DEV: mean d 0.44 at 0-10 years, 0.47 at 10-40, 0.49 at 40-60, 0.53 at 100, 0.58 at 200; SD of d within a gap
# class 0.11-0.14.) Armchair against chair on DEV: +0.092.
LAT_A0, LAT_STIG, LAT_OU, LAT_THETA = 0.210, 0.000333, 0.065, 81.5
LAT_K = 12               # dimensions; sets the pair-to-pair scatter (SD of d about 0.11)
LAT_ARM_DEL, LAT_ARM_S = 0.35, 0.09


def _latent(rng, aar, oey=None):
    """A parametric population with a KNOWN history, for the power of the design at the expected held-out size.
    Each chair is a point in R^K: z = h(year) + individual noise. The history h is a random walk plus a
    mean-reverting (Ornstein-Uhlenbeck) component, both without any edge: a pure gradient whose mean squared
    distance follows the DEV fit above. An island of G years at b is G years of that same history cut out:
    chairs with aar >= b get h(aar + G). d = Euclidean distance in R^K. Armchairs (share LAT_ARM_DEL) are
    displaced by one fixed vector that gives an armchair effect of about LAT_ARM_S."""
    N, K = len(aar), LAT_K
    eff = aar.copy()
    for b, G in (oey or []):
        eff = eff + np.where(aar >= b, G, 0)
    t0, T_ = int(eff.min()), int(eff.max()) - int(eff.min()) + 1
    rw = np.cumsum(rng.normal(0, np.sqrt(LAT_STIG / K), (T_, K)), axis=0)
    rho = np.exp(-1.0 / LAT_THETA)
    sd_ou = np.sqrt(LAT_OU / (2.0 * K))
    ou = np.empty((T_, K))
    ou[0] = rng.normal(0, sd_ou, K)
    sjokk = rng.normal(0, sd_ou * np.sqrt(1 - rho ** 2), (T_, K))
    for j in range(1, T_):
        ou[j] = rho * ou[j - 1] + sjokk[j]
    z = (rw + ou)[eff - t0] + rng.normal(0, np.sqrt(LAT_A0 / (2.0 * K)), (N, K))
    arm = (rng.random(N) < LAT_ARM_DEL).astype(int)
    v = rng.normal(0, 1, K)
    d0 = np.sqrt(LAT_A0)
    v *= np.sqrt((d0 + LAT_ARM_S) ** 2 - d0 ** 2) / np.linalg.norm(v)
    z[arm == 1] += v
    return {"id": ["L%04d" % i for i in range(N)], "aar": aar.copy(), "mus": np.array(["SYN"] * N, object),
            "suite": np.arange(N), "suitenamn": ["L%04d" % i for i in range(N)], "arm": arm,
            "smal": np.ones(N, bool), "D": cdist(z, z)}


def _forventa_held_datoar(rng, smal=True, overleving=0.85):
    """Dates of the expected held-out V&A sample, FROM THE CATALOGUE ONLY: V&A held-out WOOD chairs before 1900
    (not maal_kopi), with spenn <= 15 when smal, thinned at random to the DEV quality pass rate (149 of 175)."""
    recs = felles._katalogpostar(felles._held_ids()[0])
    aar = np.array([r["aar"] for r in recs if r["museum"] == "VA" and r["materialklasse"] == "WOOD"
                    and r["aar"] is not None and r["aar"] < AAR_MAKS and not r["maal_kopi"]
                    and (_er_smal(r) or not smal)], int)
    return aar[rng.random(len(aar)) < overleving]


def _frekvens(skaarar):
    """Outcome frequencies over replicates (list of _skaar results). 'OEY_med_bonferroni_nedre_grense' = share
    of runs that are valid and would be OEY with the Bonferroni lower bound instead of the plain 95 % bound."""
    u = [v["utfall"] for v in skaarar]
    ut = {x: round(float(np.mean([y == x for y in u])), 3) for x in ("GRADIENT", "OEY", "UAVGJORT", "UGYLDIG")}
    ut["OEY_med_bonferroni_nedre_grense"] = round(float(np.mean(
        [v["port_ok"] and v["oey_med_bonferroni_nedre_grense"]["tal"] > 0 for v in skaarar])), 3)
    ut["port_feil_P1_P2_P3_P4"] = [round(float(np.mean([not v["port"][j]["ok"] for v in skaarar])), 3)
                                   for j in range(4)]
    tal = lambda x: np.nan if x is None else x
    ut["median_spleis50"] = _f(np.nanmedian([tal(v["spleis50"]["verdi"]) for v in skaarar]))
    ut["median_storste_ovre_grense"] = _f(np.nanmedian([tal(v["gradient"]["storste_ovre_grense"]) for v in skaarar]))
    ut["median_minste_paaviselege_spleis"] = _f(np.median(
        [v["minste_paaviselege_spleis"] or 125 for v in skaarar]), 0)
    return ut


def syntetisk_kontroll(rep=SYN_REP, latent_rep=SYN_LATENT_REP):
    """Runs _skaar (the scoring code of kjoer) on synthetic populations.
    A. real DEV silhouettes, DEV-sized (both museums merged into one synthetic museum, all datings):
       (a) an island of 50 years planted at 1737 in the DEV dates            -> must NOT be GRADIENT
       (a100) an island of 100 years planted at 1737                           -> reported
       (b) DEV dates jittered by +-25 years (no edges)                         -> must NOT be OEY
       plus outcome frequencies over `rep` jitter draws with and without a planted island.
    B. latent-vector populations with a known history at the EXPECTED size and date distribution of the primary
       held-out sample (catalogue counts only) and at the size of the unrestricted V&A sample: frequencies of
       the four outcomes under a pure gradient and under islands cut into the history."""
    grunn = _dev_syntetisk_grunnlag()
    rng = np.random.default_rng(SYN_FRO)
    kort = lambda v: {"utfall": v["utfall"], "dom": _dom(v["utfall"]), "n": v["n"], "k": v["k"],
                      "port": [(p["namn"], p["verdi"], p["terskel"], p["ok"]) for p in v["port"]],
                      "spleis50": v["spleis50"], "spleis100": v["spleis100"],
                      "armstol_mot_stol": v["armstol_mot_stol"], "oey_ved": v["oey"]["ved"],
                      "gradient": v["gradient"], "minste_paaviselege_spleis": v["minste_paaviselege_spleis"],
                      "grenser": [(g["b"], g["n_kryss"], g["S"], g["ki95"], g["ovre_bonf"]) for g in v["grenser"]]}
    ut = {"grunnlag": {"n": len(grunn["id"]), "kjelde": "DEV, WOOD < 1900, quality-passed, both museums merged "
                       "into one synthetic museum, all datings (the V&A restricted DEV sample has too few chairs)"}}

    # ---- A: named single runs, full bootstrap
    a50 = _skaar(_plant_oey(grunn, SYN_OEY_STAD, 50), GRENSER_PRIM)
    a100 = _skaar(_plant_oey(grunn, SYN_OEY_STAD, 100), GRENSER_PRIM)
    b = _skaar(_slingre(grunn, np.random.default_rng(SYN_FRO)), GRENSER_PRIM)
    urort = _skaar(grunn, GRENSER_PRIM)
    ut["a_planta_oey_50_aar_ved_1737"] = dict(kort(a50), krav="not GRADIENT", krav_oppfylt=a50["utfall"] != "GRADIENT")
    ut["a100_planta_oey_100_aar_ved_1737"] = dict(kort(a100), krav="not GRADIENT (OEY wanted, reported)",
                                                  krav_oppfylt=a100["utfall"] != "GRADIENT")
    ut["b_datoar_slingra_25_aar"] = dict(kort(b), krav="not OEY", krav_oppfylt=b["utfall"] != "OEY")
    ut["dev_urort_eitt_syntetisk_museum"] = kort(urort)

    # ---- A: frequencies over jitter draws (DEV-sized samples)
    fr = {"slingra": [], "oey50": [], "oey100": []}
    S_ved = {"oey50": [], "oey100": []}
    for _ in range(rep):
        p = _slingre(grunn, rng)
        fr["slingra"].append(_skaar(p, GRENSER_PRIM, n_boot=SYN_BOOT_REP, full=False))
        for G in (50, 100):
            v = _skaar(_plant_oey(p, SYN_OEY_STAD, G), GRENSER_PRIM, n_boot=SYN_BOOT_REP)
            fr["oey%d" % G].append(v)
            g = [x for x in v["grenser"] if x["b"] == SYN_OEY_STAD][0]
            S_ved["oey%d" % G].append(np.nan if g["S"] is None else g["S"])
    ut["frekvensar_DEV_storleik"] = {
        "rep": rep, "n_boot": SYN_BOOT_REP,
        "b_slingra_utan_oey": _frekvens(fr["slingra"]),
        "a_slingra_pluss_oey_50_ved_1737": dict(_frekvens(fr["oey50"]),
                                                median_S_ved_planta_grense=_f(np.nanmedian(S_ved["oey50"]))),
        "a_slingra_pluss_oey_100_ved_1737": dict(_frekvens(fr["oey100"]),
                                                 median_S_ved_planta_grense=_f(np.nanmedian(S_ved["oey100"]))),
    }

    # ---- B: latent populations at the expected held-out sizes
    def latent(datoar, scenario):
        res = {}
        ns = []
        for namn, oey in scenario:
            sk = []
            for _ in range(latent_rep):
                aar = datoar()
                ns.append(len(aar))
                sk.append(_skaar(_latent(rng, aar, oey), GRENSER_PRIM, n_boot=SYN_BOOT_REP, full=False))
            res[namn] = _frekvens(sk)
        return int(np.median(ns)), res

    scen = (("gradient", None), ("oey_50_ved_1762", [(1762, 50)]), ("oey_100_ved_1762", [(1762, 100)]),
            ("oey_150_ved_1762", [(1762, 150)]), ("oey_150_ved_1662", [(1662, 150)]))
    n1, r1 = latent(lambda: _forventa_held_datoar(rng, True), scen)
    n2, r2 = latent(lambda: _forventa_held_datoar(rng, False), (scen[0], scen[2]))
    ut["latent_modell"] = {
        "rep": latent_rep, "n_boot": SYN_BOOT_REP,
        "modell": "points in R^12; history = random walk + mean-reverting component fitted to the DEV curve of "
                  "squared distance against time gap; an island = that many years of the history cut out; dates = "
                  "V&A held-out catalogue dates thinned to the DEV quality pass rate 0.85. A MODEL, not data: "
                  "real silhouettes have heavier tails, dating error and type-mix changes.",
        "primaerutval_VA_spenn_hoegst_15": {"n_median": n1, "frekvensar": r1},
        "robustheit_VA_alle_dateringar": {"n_median": n2, "frekvensar": r2}}
    ut["krav_oppfylte"] = bool(ut["a_planta_oey_50_aar_ved_1737"]["krav_oppfylt"]
                               and ut["b_datoar_slingra_25_aar"]["krav_oppfylt"])
    return ut


if __name__ == "__main__":
    import json
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"kjoer_dev": kjoer("dev"), "syntetisk_kontroll": syntetisk_kontroll()},
                     ensure_ascii=False, indent=1))
