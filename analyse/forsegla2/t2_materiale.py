#!/usr/bin/env python3
"""t2_materiale.py - the material shift of the 1920s as a natural perturbation, read two ways on one sample.

Second sealed test (3D-model data), module T2. Two hypotheses, one sample, one material rule
(felles.materialklasse; no class is made here):

  N1 (new)          a material opens the zone where its operations remove a prohibition, and solid wood of
                    the same years does not follow.
  E2 (replication)  at the same release, structure became material-bound and seat height did not.

Run from the repository root:   python analyse/forsegla2/t2_materiale.py
It prints kjoer('dev') and syntetisk_kontroll() as JSON. The 'held' path exists, goes through the guarded
readers felles.les('held') / felles.silhuett('held'), and has never been run.

WHAT IS FROZEN HERE (every number below is a literal; the rule and the DEV value stand beside it)
  classes     LINE := felles class LINE or LINE+SHEET (a structural metal frame, with or without a shell)
              SHEET := felles class SHEET (plastic shell or laminate, no structural metal)
              WOOD  := felles class WOOD (solid wood only).   ANNA is dropped.
              LINE+SHEET goes to LINE for three reasons fixed before any outcome was read on the held-out side:
              (1) it is the history designer's definition of P1c ('linje = stål, med eller utan plast');
              (2) in the foot zone the bearing structure of such a chair is the metal frame;
              (3) it works AGAINST the crossing (a tube frame carrying a shell leaves the old envelope in
                  both zones), so the choice cannot manufacture the result.
              The pure-LINE version and the LINE+SHEET rates are reported as secondary lines.
  zones       centimetres from the floor: foot 0-30, shell/back 60-200 (historie/e09_endeleg.py). The seat
              band 30-60 is not used.
  distance    1 - soft Jaccard: silhouettes blurred with a Gaussian of sigma 2 cm (whole canvas), then
              1 - sum(min)/sum(max) over the rows of the zone, all 160 columns (historie/formrom.py).
  archive     DEV chairs of class WOOD with aar < 1900 that pass felles.kvalitet(): 152 chairs. Frozen.
  envelope    per view and zone: the 95th percentile of the archive's leave-one-out nearest-neighbour
              distance (KONVOLUTT below). A chair is OUTSIDE in a zone when its nearest archive distance
              exceeds that number.
  targets     chairs with aar >= 1925 in the three classes that pass felles.kvalitet().
  views       front view primary, side view secondary (the side view rests on generated depth).

LIMITS, STATED IN ADVANCE
  1.212 'Same silhuett er ikkje same bereform': the envelope measures likeness of a projection. A chair
        outside it is new as a silhouette; that is not yet a new bearing form, and a chair inside it may carry
        its load in a new way. 1.411: neighbours in the form space are not the positions that look alike.
  The envelope measures what was settled before 1900 in two museums, not what was possible.
  LINE leaving the foot envelope is what any design historian expects. It is not counted as a
  confirmation by itself: the crossing (a) and the wood-stays-inside statement (b) are the claims.

WEAKNESSES FOUND ON DEV WHILE WRITING THE MODULE (kept in the open; none of them changes a primary criterion)
  1. The shell zone in the front view is mostly a detector of TOTAL HEIGHT. The meshes are scaled to the
     catalogue H and the zone is fixed at 60-200 cm; the lowest archive chair is 78 cm. On DEV 0.70 of the
     targets below 78 cm fall outside in the shell zone and 0.04 of those at or above it; a solid shell planted
     in the range 60-80 cm on archive chairs is NOT detected, a back cut at 70 cm always is
     (syntetisk_kontroll: instrumentprobe_N1). So 'SHEET leaves the shell zone' can be read from the catalogue
     as 'sheet chairs are lower than any old wooden chair'. The secondary line hoegd_grunnmodell reports the
     crossing among chairs of at least 78 cm, the crossing with the shell flag replaced by 'H < 78 cm', and a
     permutation within 25-year bin x height band. A crossing that lives only in that replacement is a height
     effect, not a shape effect.
  2. The gate may sit close to its limit. Inside the archive the V&A chairs fall outside the foot envelope
     (leave-one-out, front view) at 0.12 and the Nasjonalmuseet chairs at 0.00; the held-out old-wood chairs
     are about nine tenths V&A, so a gate value near 0.10-0.12 is expected in the front-view foot zone, against
     a limit of 0.15.
  3. E2 corrects the mesh seat height for unreliability but not for class-specific BIAS. On DEV the mesh reads
     SHEET chairs about 3 cm low and WOOD chairs right (medians: mesh 39.0 / catalogue 43.0 for SHEET, 46.0 /
     45.5 for WOOD). That bias is a class effect of the instrument, and dividing by r2 = 0.32 triples it. E2
     can therefore fail when its claim is true (syntetisk_kontroll: E2 control d). The secondary lines on the
     CATALOGUE seat height are free of this and should be read beside the verdict.
  4. The under-fill is not corrected for its own unreliability; that works against the claim of E2.
  5. The quality rule drops a third of the LINE candidates on DEV (10 of 30), SHEET 5 of 20, WOOD 3 of 14. With
     the strict worst-case imputation the DEV crossing vanishes (-0.08).
"""
import json
import os
import sys

import cv2
import numpy as np
from scipy.stats import rankdata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import felles  # noqa: E402

ID = "T2"

# ============================================================================ frozen definitions
AAR_ARKIV = 1900                  # archive and gate: class WOOD with aar < 1900
AAR_MAAL = 1925                   # targets: aar >= 1925
SONER = {"fot": (0, 30), "rygg": (60, 200)}          # rows = cm from the floor
SIGMA = 2.0                       # cm, Gaussian blur before the soft Jaccard
Q_KONVOLUTT = 95.0                # percentile of the leave-one-out nearest-neighbour distance
NOKLAR = ("front_fot", "front_rygg", "side_fot", "side_rygg")
KLASSEKART = {"LINE": "LINE", "LINE+SHEET": "LINE", "SHEET": "SHEET", "WOOD": "WOOD"}
KLASSAR = ("LINE", "SHEET", "WOOD")
_KODE = {"LINE": 0, "SHEET": 1, "WOOD": 2}

# The frozen envelope. Rule: 95th percentile of the leave-one-out nearest-neighbour distance among the
# ARKIV_N DEV archive chairs. Computed on DEV on 13 Nov 2026; _arkiv() recomputes it from DEV at every run
# and stops if it differs by more than 1e-5 (then the DEV data or the loader has changed).
ARKIV_N = 152
KONVOLUTT = {
    "front_fot": 0.406169,
    "front_rygg": 0.374944,
    "side_fot": 0.434690,
    "side_rygg": 0.485362,
}

# ---- N1 thresholds
# Rule for both: lower 95 % cluster-bootstrap bound on DEV (suites, 2000 resamples, seed felles.FRO), rounded
# DOWN to the nearest 0.05, never below 0.10  (_terskelregel).
N1_TERSKEL_KRYSSING = 0.10        # (a) P1c, front view. DEV value +0.70, 95 % [+0.115, +1.19]: the rule gives
#                                       0.10 (the floor; the designer's own numbers gave 0.30 for the mean of
#                                       two views with his classes and his clusters)
N1_TERSKEL_TRE = 0.25             # (b) LINE share - WOOD share outside, foot zone, front view.
#                                       DEV value +0.60, 95 % [+0.278, +0.833] -> 0.25
N1_PERM_P = 0.01                  # (a) permutation of class within 25-year bins, one-sided
N1_N_PERM = 10000
N1_PORT_MAKS = 0.15               # gate: old wood outside the frozen envelope, per view and zone
N1_PORT_MIN_N = 30                # gate: at least this many gate chairs, else the gate cannot be read
N1_MIN_N_KLASSE = 20              # gate: at least this many target chairs in each class
N1_SETE_MIN = 42.0                # robustness line: targets with mesh seat height >= 42 cm
DILATASJON = 5                    # robustness line: 5 x 5 kernel = 2 px to each side
ARKIV_H_MIN = 78.0                # the lowest catalogue height H in the frozen archive (cm). Height base model:
#                                   a chair lower than every archive chair has little above 60 cm, and on DEV that
#                                   alone decides 'outside in the shell zone' (0.70 of the targets below 78 cm,
#                                   0.04 of those at or above it). See the secondary line hoegd_grunnmodell.

# ---- E2 thresholds
E2_BOKS = (0, 30)                 # under-fill box: rows 0-30 cm, columns = bounding box of the silhouette
E2_R2_MIN = 0.20                  # gate: reliability of the mesh seat height (UGYLDIG below this)
E2_TERSKEL = 0.0                  # the difference must be above 0 and its 95 % interval must exclude 0
E2_MIN_N_KLASSE = 20              # gate: at least this many chairs in each class
E2_BLOKK = 0.60                   # 'block': under-fill >= 0.60 in the side view AND in the front view

PRIMAER_VISNING = "front"


def _terskelregel(nedre):
    """Threshold rule of the history designer: lower DEV bound rounded down to 0.05, never below 0.10."""
    if nedre is None or not np.isfinite(nedre):
        return None
    return max(0.10, float(np.floor(nedre / 0.05 + 1e-9) * 0.05))


# ============================================================================ SPEC
SPEC_N1 = {
    "id": "N1",
    "tittel": "Line material opens the foot, sheet material opens the shell, and solid wood of the same "
              "years does not follow",
    "slag": "ny",
    "proposisjonar": ["1.42", "1.421", "1.422", "1.51", "1.53", "2.2", "2.2021"],
    "paastand": (
        "A new material does not make chairs new all over. It opens the part of the form space where its "
        "operations remove a prohibition: tube and rod open the load-bearing zone under the seat, sheet and "
        "shell materials open the seat-back shell. After 1925 the cantilever and the tube foot are thought by "
        "everyone (1.53), so if solid-wood chairs made from 1925 still lie inside the region wood held before "
        "1900 in the foot zone, that region is forbidden for wood (1.42, 1.421) and not merely unthought (1.51). "
        "LIMIT (1.212): silhouette novelty is not novelty of bearing form; the test reads a projection. "
        "LINE leaving the foot envelope alone is what any design historian expects and is not the claim: the "
        "crossing (a) and the wood-stays-inside statement (b) are the claims, and both are required."),
    "utval": (
        "Targets: chairs of the sample with aar_fraa >= 1925, felles.materialklasse in LINE, LINE+SHEET (both "
        "counted as LINE), SHEET or WOOD, passing felles.kvalitet(). Archive: the 152 DEV chairs of class WOOD "
        "with aar_fraa < 1900 passing felles.kvalitet(), frozen, with the envelope KONVOLUTT (95th percentile of "
        "the leave-one-out nearest-neighbour distance, soft Jaccard, sigma 2 cm). Zones: foot 0-30 cm, "
        "shell/back 60-200 cm from the floor. Gate chairs: chairs of the sample of class WOOD with "
        "aar_fraa < 1900 passing felles.kvalitet() (on DEV these are the archive itself, scored leave-one-out). "
        "Intervals: cluster bootstrap over suites, 2000 resamples, seed felles.FRO."),
    "primaer": [
        {"namn": "a_kryssing_P1c_front",
         "statistikk": "P1c = (share of LINE outside - share of SHEET outside) in the foot zone minus the same "
                       "difference in the shell zone; front view",
         "terskel": N1_TERSKEL_KRYSSING, "retning": ">=",
         "tilleggskrav": "lower 95 % cluster-bootstrap bound > 0 AND one-sided permutation p < 0.01 (class "
                         "labels permuted between suites within 25-year bins, 10000 permutations)",
         "regel_for_terskel": "lower 95 % cluster-bootstrap bound on DEV, rounded down to 0.05, never below 0.10",
         "dev_verdi": "+0.70, 95 % [+0.115, +1.19], permutation p = 0.013 (n = 20 LINE, 15 SHEET, 11 WOOD; "
                      "40 suites). On DEV alone (a) does NOT meet its own permutation requirement."},
        {"namn": "b_forbode_ikkje_utenkt_front_fot",
         "statistikk": "share of LINE chairs outside the envelope in the foot zone minus the share of WOOD "
                       "chairs from 1925 outside it; front view",
         "terskel": N1_TERSKEL_TRE, "retning": ">=",
         "tilleggskrav": "lower 95 % cluster-bootstrap bound > 0",
         "regel_for_terskel": "lower 95 % cluster-bootstrap bound on DEV, rounded down to 0.05, never below 0.10",
         "dev_verdi": "+0.60, 95 % [+0.278, +0.833] (LINE 0.60 of 20, WOOD 0.00 of 11)"},
    ],
    "konjunksjon": "HELDT only if (a) AND (b) hold; SLO FEIL if either fails; UGYLDIG if a gate fails.",
    "avgrensingar": [
        "1.212: silhouette novelty is not novelty of bearing form; 1.411: likeness is not adjacency.",
        "The shell zone in the front view responds mostly to total height (catalogue H below 78 cm, the lowest "
        "archive chair): on DEV 0.70 of such targets are outside there, 0.04 of the others. Read (a) together "
        "with the secondary line hoegd_grunnmodell; a crossing that survives only when the shell flag is "
        "replaced by 'H < 78 cm' is a height effect.",
        "(b) is LINE minus WOOD; its LINE half is the expected part. The share of WOOD chairs from 1925 outside "
        "the foot envelope, and its difference from old wood, is the number that bears on forbidden against "
        "unthought and is reported with its interval.",
        "P1c is a sum of two terms and can reach its threshold on the foot term alone (LINE leaves the foot "
        "more than SHEET does), which is the expected part; the line kryssinga_ledd_for_ledd shows both terms.",
        "Zones, envelope level, blur and classes were chosen on DEV with 46 target chairs; expect shrinkage.",
        "A third of the LINE candidates fail the quality rule on DEV; the worst-case lines show what that could hide.",
    ],
    "sekundaer": [
        "side view: P1c and (b); the mean of the two views (the designer's original P1c)",
        "share outside per class, view and zone, with intervals; the WOOD-from-1925 share in the foot zone and "
        "its difference from the gate share of old wood",
        "the two terms of the crossing separately (LINE - SHEET in the foot; SHEET - LINE in the shell), since "
        "P1c can be carried by the foot term alone",
        "P1a (LINE - WOOD, foot, side view) and P1b (SHEET - WOOD, shell, front view) as the designer wrote them",
        "pure LINE (LINE+SHEET left out) and LINE+SHEET as a class of its own",
        "robustness: targets with mesh seat height >= 42 cm only",
        "robustness: all silhouettes dilated by 2 px (5 x 5), envelope recomputed from the dilated archive",
        "robustness: targets that also pass felles.kvalitet_front() (front width against catalogue B)",
        "height base model for the shell zone: the crossing among targets with catalogue H >= 78 cm (the lowest "
        "archive chair), the crossing with the shell-zone flag replaced by 'H < 78 cm', and the permutation p "
        "within 25-year bin x height band",
        "attrition per class from the quality rule; worst case with all dropped LINE chairs counted inside, "
        "and the strict worst case (dropped LINE inside the foot and outside the shell, dropped SHEET the "
        "reverse, dropped WOOD outside the foot)",
        "lag statistic (designers' F2): share outside the own zone for non-wood chairs before 1925 minus the "
        "same share, in the same zones, for WOOD chairs 1900-1924",
        "per museum",
    ],
    "port": [
        {"namn": "gammalt_tre_utanfor_konvolutten",
         "terskel": N1_PORT_MAKS,
         "ugyldig_dersom": "the share of gate chairs outside the frozen envelope exceeds 0.15 in the front-view "
                           "foot zone or in the front-view shell zone (the crossing cannot be read in the "
                           "primary view without both), or there are fewer than 30 gate chairs. A side-view "
                           "zone that fails is removed from the secondary lines before the targets are read."},
        {"namn": "n_per_klasse", "terskel": N1_MIN_N_KLASSE,
         "ugyldig_dersom": "fewer than 20 target chairs in LINE, SHEET or WOOD (not applied on DEV, where "
                           "the classes hold 20, 15 and 11)"},
    ],
    "grunnmodell": (
        "Three base models can win. (1) Period only: once the 25-year bin is known, material class adds "
        "nothing; it predicts P1c = 0 and (b) = 0 (tested by the permutation). (2) Modern all over: metal and "
        "shell chairs are both new in every zone; it predicts P1c = 0 while (b) may hold. (3) Unthought, not "
        "forbidden: once the tube foot is thought, wood follows; it predicts (b) = 0. Each makes N1 SLO FEIL. "
        "A fourth base model is NOT excluded by the primary criterion: (4) height only. Sheet chairs are lower "
        "than any chair of the archive (catalogue H below 78 cm), which alone puts them outside in the shell "
        "zone; together with the expected foot effect of LINE this produces a crossing. Only the secondary line "
        "hoegd_grunnmodell separates it from a shape effect."),
    "tel_imot": (
        "P1c below 0.10 or with an interval reaching 0 or with permutation p >= 0.01: new-material chairs are "
        "then equally novel in every zone. (b) below 0.25 or with an interval reaching 0: solid wood from 1925 "
        "leaves the old foot region about as often as metal does, so the region was unthought and not "
        "forbidden. If only (b) holds the result is the one any design historian would state, and N1 has failed."),
}

SPEC_E2 = {
    "id": "E2",
    "tittel": "At the release of the 1920s the structure under the seat became material-bound and the seat "
              "height did not",
    "slag": "replikasjon",
    "proposisjonar": ["5.011", "5.012", "1.412", "5.15"],
    "paastand": (
        "Steel tube, shells and laminates tore the structure loose from the joiner's template. A dimension "
        "that was only carried by the copied template (1.412) should become material-bound together with the "
        "structure; a dimension held in the work around the body (5.012) should not (5.011: the perturbation "
        "tells them apart). Prediction: material class explains more of the fill under the seat than of the "
        "seat height, after the seat height has been corrected for the unreliability of the mesh. A pass "
        "rejects template inheritance; it does not by itself establish regulation against the body."),
    "utval": (
        "Chairs of the sample with aar_fraa >= 1925 in the classes LINE (felles LINE or LINE+SHEET), SHEET, "
        "WOOD, passing felles.kvalitet() and having a mesh seat height. Reliability sample: all chairs of "
        "the sample (any year, any class) passing felles.kvalitet() with both a mesh and a catalogue seat "
        "height. Cluster bootstrap over suites on the union of the two, 2000 resamples."),
    "primaer": [
        {"namn": "eps2_underfyll_minus_eps2_sete_korrigert",
         "statistikk": "epsilon squared (Kelley; one-way, three classes) of class on under-fill, MINUS "
                       "epsilon squared of class on log mesh seat height divided by r2, where under-fill = "
                       "filled share of the box rows 0-30 cm x bounding-box columns of the SIDE silhouette, and "
                       "r2 = squared Pearson correlation of log mesh seat height with log catalogue seat height "
                       "in the reliability sample (the corrected value is clipped to [-1, 1])",
         "terskel": E2_TERSKEL, "retning": ">",
         "tilleggskrav": "the 95 % cluster-bootstrap interval excludes 0 (lower bound > 0)",
         "regel_for_terskel": "contrast against equality; no tuned number",
         "dev_verdi": "+0.06, 95 % [-0.71, +0.38] (eps2 under-fill 0.20; eps2 log mesh seat 0.046; r2 0.32; "
                      "corrected 0.14; n = 46). NOT secured on DEV."},
    ],
    "sekundaer": [
        "the parts: eps2 of class on under-fill, on log mesh seat height (raw and corrected), r2",
        "eps2 of class on log CATALOGUE seat height for the catalogued chairs from 1925 (no mesh in it): all, "
        "those passing the quality rule, and those with block-like lounge chairs excluded; per museum; and on "
        "the catalogued chairs that pass the quality rule, eps2 of the under-fill minus eps2 of the catalogue "
        "seat height (same chairs, no correction needed)",
        "the primary difference with block-like chairs excluded (block = under-fill >= 0.60 in both views)",
        "the primary difference with r2 taken from the catalogued chairs from 1925 only",
        "the primary difference with the front-view under-fill, with ranks, and with four classes",
        "per museum",
        "equifinality (5.15): median mesh seat height of LINE, SHEET and WOOD chairs from 1925, with intervals; "
        "the same for catalogue seat height",
    ],
    "port": [
        {"namn": "reliabilitet_mesh_sete_r2", "terskel": E2_R2_MIN,
         "ugyldig_dersom": "r2 of log mesh seat height against log catalogue seat height in the reliability "
                           "sample is below 0.20 (or the correlation is not positive)"},
        {"namn": "n_per_klasse", "terskel": E2_MIN_N_KLASSE,
         "ugyldig_dersom": "fewer than 20 chairs in LINE, SHEET or WOOD (not applied on DEV)"},
    ],
    "avgrensingar": [
        "The correction divides by a reliability but cannot remove a class-specific BIAS of the mesh seat "
        "height (on DEV shells read about 3 cm low, wood reads right); that bias counts as a class effect and "
        "is multiplied by 1 / r2. E2 can fail for this reason alone; the catalogue lines are the check.",
        "r2 is taken over chairs of all periods as specified; on DEV it is 0.32 overall, 0.47 among chairs from "
        "1925 and 0.23 before 1925, so the overall value over-corrects (against the claim).",
        "The under-fill is not corrected for its own unreliability (against the claim).",
        "The box 0-30 cm is not defined by the seat, but a seat lower than about 35 cm enters it.",
        "A pass rejects template inheritance of the seat height; it does not establish regulation against the body.",
    ],
    "grunnmodell": (
        "Form follows material: every dimension, the seat height included, carries the material signature "
        "to a similar degree. It predicts a difference of 0 (interval covering 0) and wins if the corrected "
        "eps2 of the seat height is as large as the eps2 of the under-fill."),
    "tel_imot": (
        "A difference at or below 0, or an interval that includes 0: material explains seat height about as "
        "well as it explains the structure under the seat, and the seat height was carried by the template."),
}

SPEC = {
    "id": ID,
    "tittel": "The material shift of the 1920s as a natural perturbation (N1: zone-specific opening; "
              "E2: structure material-bound, seat height not)",
    "slag": "ny + replikasjon",
    "proposisjonar": sorted(set(SPEC_N1["proposisjonar"] + SPEC_E2["proposisjonar"])),
    "paastand": "Two hypotheses on one sample with one material rule; see 'hypotesar'. Each has its own verdict.",
    "utval": "see 'hypotesar'",
    "primaer": [dict(p, hypotese="N1") for p in SPEC_N1["primaer"]] + [dict(p, hypotese="E2") for p in SPEC_E2["primaer"]],
    "sekundaer": ["N1: " + s for s in SPEC_N1["sekundaer"]] + ["E2: " + s for s in SPEC_E2["sekundaer"]],
    "port": [dict(p, hypotese="N1") for p in SPEC_N1["port"]] + [dict(p, hypotese="E2") for p in SPEC_E2["port"]],
    "grunnmodell": {"N1": SPEC_N1["grunnmodell"], "E2": SPEC_E2["grunnmodell"]},
    "tel_imot": {"N1": SPEC_N1["tel_imot"], "E2": SPEC_E2["tel_imot"]},
    "hypotesar": [SPEC_N1, SPEC_E2],
}


# ============================================================================ small helpers
def _r(x, d=4):
    """Round for JSON; NaN / None -> None."""
    if x is None:
        return None
    x = float(x)
    return round(x, d) if np.isfinite(x) else None


def _ki(boot, j=None):
    b = np.asarray(boot, float)
    if j is not None:
        b = b[:, j]
    lo, hi = felles.ki(b)
    return [_r(lo), _r(hi)]


def _mjuk(s):
    return cv2.GaussianBlur(np.asarray(s, np.float32), (0, 0), SIGMA)


def _dilater(s):
    return cv2.dilate(np.asarray(s, np.uint8), np.ones((DILATASJON, DILATASJON), np.uint8))


def _sonevektorar(side, front):
    """-> dict key -> flat float32 vector of the blurred silhouette inside the zone."""
    ut = {}
    for vn, s in (("front", front), ("side", side)):
        bl = _mjuk(s)
        for z, (lo, hi) in SONER.items():
            ut[vn + "_" + z] = bl[lo:hi].ravel()
    return ut


def _nn(v, A, ekskl=None, sumA=None):
    """Nearest-neighbour soft-Jaccard distance from one zone vector v to the archive matrix A (n, pixels):
    min over the archive of 1 - sum(min(v, a)) / sum(max(v, a)).
    Computed through sum(min) = (sum v + sum a - sum|v - a|) / 2 and sum(max) = (sum v + sum a + sum|v - a|) / 2,
    with the sums accumulated in float64. ekskl: index of an archive chair to leave out (leave-one-out)."""
    if sumA is None:
        sumA = A.sum(1, dtype=np.float64)
    diff = np.abs(A - v[None, :]).sum(1, dtype=np.float64)
    tot = sumA + float(v.sum(dtype=np.float64))
    d = 1.0 - (tot - diff) / np.maximum(tot + diff, 1e-6)
    if ekskl is not None:
        d[ekskl] = np.inf
    return float(d.min())


def _underfyll(s):
    """Filled share of the box rows E2_BOKS x bounding-box columns of the silhouette (not defined by the seat)."""
    s = np.asarray(s) > 0
    kol = np.nonzero(s.any(0))[0]
    if len(kol) == 0:
        return None
    return float(s[E2_BOKS[0]:E2_BOKS[1], kol.min():kol.max() + 1].mean())


# ============================================================================ archive (DEV only, frozen)
_CACHE = {}


def _arkiv(dilatert=False):
    """The frozen archive: DEV chairs of class WOOD, aar < 1900, passing felles.kvalitet().
    -> dict: ids, indeks (id -> row), A (key -> matrix), loo (key -> leave-one-out NN distances),
             terskel (key -> envelope). For dilatert=False the envelope is the literal KONVOLUTT and the
             recomputed value must agree with it; for dilatert=True it is recomputed (robustness line only)."""
    nok = ("arkiv", dilatert)
    if nok in _CACHE:
        return _CACHE[nok]
    dev = felles.les("dev")
    sil = felles.silhuett("dev")
    medl = [r for r in dev
            if r["materialklasse"] == "WOOD" and r["aar"] is not None and r["aar"] < AAR_ARKIV
            and felles.kvalitet(r, *sil.get(r["id"], (None, None)))[0]]
    vek = []
    for r in medl:
        side, front = sil[r["id"]]
        if dilatert:
            side, front = _dilater(side), _dilater(front)
        vek.append(_sonevektorar(side, front))
    A = {k: np.stack([v[k] for v in vek]) for k in NOKLAR}
    sumA = {k: A[k].sum(1, dtype=np.float64) for k in NOKLAR}
    loo = {k: np.array([_nn(A[k][i], A[k], i, sumA[k]) for i in range(len(medl))]) for k in NOKLAR}
    rekna = {k: float(np.percentile(loo[k], Q_KONVOLUTT)) for k in NOKLAR}
    if dilatert:
        terskel = rekna
    else:
        if len(medl) != ARKIV_N:
            raise RuntimeError("arkivet har %d stolar, frose tal er %d" % (len(medl), ARKIV_N))
        for k in NOKLAR:
            if abs(rekna[k] - KONVOLUTT[k]) > 1e-5:
                raise RuntimeError("konvolutten %s er %.6f på DEV, frose tal er %.6f" % (k, rekna[k], KONVOLUTT[k]))
        terskel = dict(KONVOLUTT)
    ut = {"ids": [r["id"] for r in medl], "indeks": {r["id"]: i for i, r in enumerate(medl)},
          "suite": [r["suite"] for r in medl], "A": A, "sumA": sumA, "loo": loo, "terskel": terskel, "rekna": rekna}
    _CACHE[nok] = ut
    return ut


def _kryssvalidert_port(n_del=2, seed=felles.FRO):
    """What the gate should show on new old-wood chairs, estimated inside DEV: the archive is split into two
    halves by suite; each half is given its own 95 % leave-one-out envelope and the other half is scored against
    it. Returns the pooled share outside per key. (Half an archive is sparser than the whole one, so this is an
    upper estimate of the out-of-sample rate of the full archive.)"""
    ark = _arkiv()
    rng = np.random.default_rng(seed)
    suitar = sorted(set(ark["suite"]))
    rng.shuffle(suitar)
    del_av = {s: j % n_del for j, s in enumerate(suitar)}
    d = np.array([del_av[s] for s in ark["suite"]])
    ut = {}
    for k in NOKLAR:
        A = ark["A"][k]
        utanfor = []
        for j in range(n_del):
            tren, test = np.nonzero(d != j)[0], np.nonzero(d == j)[0]
            At = A[tren]
            loo = np.array([_nn(At[i], At, i) for i in range(len(tren))])
            thr = np.percentile(loo, Q_KONVOLUTT)
            utanfor += [_nn(A[i], At) > thr for i in test]
        ut[k] = _r(np.mean(utanfor))
    return ut


# ============================================================================ per-chair features
def _trekk(recs, sil):
    """One feature dict per record (every record of the sample, also those that fail the quality rule)."""
    ark, ark_d = _arkiv(False), _arkiv(True)
    ut = []
    for r in recs:
        s = sil.get(r["id"])
        ok, grunn = felles.kvalitet(r, *(s if s is not None else (None, None)))
        f = {"id": r["id"], "museum": r["museum"], "aar": r["aar"], "namn": r["namn"], "H": r["H"],
             "klasse4": r["materialklasse"], "klasse": KLASSEKART.get(r["materialklasse"]),
             "suite": r["suite"], "bolk": felles.aarsbolk(r["aar"], 25),
             "sete_mesh": r["sete_mesh"] if (r["sete_mesh"] is not None and r["sete_mesh"] > 0) else None,
             "sete_kat": r["sete_kat"], "maal_kopi": bool(r["maal_kopi"]),
             "kv": bool(ok), "grunn": grunn, "kv_front": False,
             "d": None, "ut": None, "ut_d": None, "uf_side": None, "uf_front": None, "blokk": None}
        if ok:
            side, front = s
            v = _sonevektorar(side, front)
            eks = ark["indeks"].get(r["id"])                 # leave-one-out for the archive's own chairs
            f["d"] = {k: _nn(v[k], ark["A"][k], eks, ark["sumA"][k]) for k in NOKLAR}
            f["ut"] = {k: bool(f["d"][k] > ark["terskel"][k]) for k in NOKLAR}
            vd = _sonevektorar(_dilater(side), _dilater(front))
            f["ut_d"] = {k: bool(_nn(vd[k], ark_d["A"][k], eks, ark_d["sumA"][k]) > ark_d["terskel"][k])
                         for k in NOKLAR}
            f["uf_side"], f["uf_front"] = _underfyll(side), _underfyll(front)
            f["blokk"] = bool(f["uf_side"] >= E2_BLOKK and f["uf_front"] >= E2_BLOKK)
            f["kv_front"] = bool(felles.kvalitet_front(r, front)[0])
        ut.append(f)
    return ut


def _last(utval):
    """Feature dicts of the sample. 'held' goes through the guarded readers of felles."""
    if utval not in ("dev", "held"):
        raise ValueError("utval må vere 'dev' eller 'held'")
    nok = ("trekk", utval)
    if nok not in _CACHE:
        _CACHE[nok] = _trekk(felles.les(utval), felles.silhuett(utval))
    return _CACHE[nok]


def _er_maal(f):
    return bool(f["kv"] and f["klasse"] in _KODE and f["aar"] is not None and f["aar"] >= AAR_MAAL)


def _er_port(f):
    return bool(f["kv"] and f["klasse4"] == "WOOD" and f["aar"] is not None and f["aar"] < AAR_ARKIV)


# ============================================================================ N1: scoring
N1_NAMN = (["P1c_front", "b_front", "P1c_side", "b_side", "P1c_snitt", "P1b_front"]
           + ["%s_%s" % (kl, k) for kl in KLASSAR for k in NOKLAR]
           + ["ledd_fot_front", "ledd_rygg_front"])
N1_RATENAMN = N1_NAMN[6:18]


def _boot(recs, stat_idx, n_boot):
    """Cluster bootstrap over suites through felles.klyngebootstrap (fixed seed felles.FRO). For speed the
    records are replaced by light stand-ins (suite and row number); stat_idx receives the row numbers of the
    drawn chairs (a suite drawn twice appears twice) and works on arrays."""
    lette = [{"suite": r["suite"], "_i": i} for i, r in enumerate(recs)]
    return felles.klyngebootstrap(
        lette, lambda rs: stat_idx(np.fromiter((x["_i"] for x in rs), np.int64, len(rs))), n=n_boot)


def _n1_tabell(recs, nokkel="ut"):
    """-> (class codes (n,), outside flags (n, 4) in the order of NOKLAR)."""
    k = np.fromiter((_KODE[r["klasse"]] for r in recs), np.int64, len(recs))
    u = np.array([[r[nokkel][n] for n in NOKLAR] for r in recs], float).reshape(len(recs), 4)
    return k, u


def _n1_vektor(k, u):
    """All N1 statistics of one (re)sample of target chairs, in the order of N1_NAMN.
    P1c  = (LINE - SHEET) in the foot minus (LINE - SHEET) in the shell: the crossing
    b    = LINE - WOOD in the foot   (side view: the designer's P1a)
    P1b  = SHEET - WOOD in the shell, front view
    ledd_fot_front = LINE - SHEET in the foot, ledd_rygg_front = SHEET - LINE in the shell: the two terms whose
    sum is P1c_front. P1c can be carried by one of them alone; a crossing in the plain sense needs both above 0."""
    rate = np.full((3, 4), np.nan)
    for c in range(3):
        m = k == c
        if m.any():
            rate[c] = u[m].mean(0)
    L, S, W = rate
    p1c_f = (L[0] - S[0]) - (L[1] - S[1])
    p1c_s = (L[2] - S[2]) - (L[3] - S[3])
    return ([p1c_f, L[0] - W[0], p1c_s, L[2] - W[2], 0.5 * (p1c_f + p1c_s), S[1] - W[1]] + list(rate.ravel())
            + [L[0] - S[0], S[1] - L[1]])


def _n1_perm(maal, nokkel="ut", n_perm=N1_N_PERM, seed=felles.FRO + 1, visning="front", hoegdband=False):
    """One-sided permutation p for P1c: class labels are permuted between units within 25-year bins.
    A unit is the set of target chairs that share suite, bin and class, so a set of chairs moves as one.
    p = (1 + number of permutations with P1c >= observed) / (1 + n_perm); an undefined permuted value counts
    as >= observed.
    hoegdband=True (secondary line only): the strata are 25-year bin x height band (catalogue H below
    ARKIV_H_MIN or not), so the base model is 'period and height band only'."""
    lag = (lambda r: (r["bolk"], bool(r["H"] < ARKIV_H_MIN))) if hoegdband else (lambda r: r["bolk"])
    einingar = {}
    for i, r in enumerate(maal):
        einingar.setdefault((lag(r), r["suite"], r["klasse"]), []).append(i)
    nokl = list(einingar)
    e_bolk = np.array([str(b) for b, _, _ in nokl])
    e_kl = np.array([_KODE[c] for _, _, c in nokl])
    medlem = np.empty(len(maal), int)
    for j, kk in enumerate(nokl):
        medlem[einingar[kk]] = j
    fot = np.array([r[nokkel][visning + "_fot"] for r in maal], float)
    rygg = np.array([r[nokkel][visning + "_rygg"] for r in maal], float)

    def p1c(k):
        L, S = k == 0, k == 1
        if not L.any() or not S.any():
            return np.nan
        return (fot[L].mean() - fot[S].mean()) - (rygg[L].mean() - rygg[S].mean())

    obs = p1c(e_kl[medlem])
    if not np.isfinite(obs):
        return None
    bolkar = [np.nonzero(e_bolk == b)[0] for b in np.unique(e_bolk)]
    rng = np.random.default_rng(seed)
    teljar = 0
    for _ in range(n_perm):
        p = e_kl.copy()
        for ix in bolkar:
            p[ix] = e_kl[rng.permutation(ix)]
        if not (p1c(p[medlem]) < obs):
            teljar += 1
    return (1 + teljar) / (1 + n_perm)


def _n1_kjerne(maal, nokkel="ut", n_boot=felles.N_BOOT, n_perm=N1_N_PERM, perm=True):
    """Point values, cluster-bootstrap intervals and the permutation p of one set of target chairs."""
    if not maal:
        return {"n": {c: 0 for c in KLASSAR}, "verdi": {n: None for n in N1_NAMN},
                "ki95": {n: [None, None] for n in N1_NAMN}, "perm_p": None, "n_suitar": 0}
    k, u = _n1_tabell(maal, nokkel)
    v = _n1_vektor(k, u)
    boot = _boot(maal, lambda ix: _n1_vektor(k[ix], u[ix]), n_boot)
    return {"n": {c: sum(1 for r in maal if r["klasse"] == c) for c in KLASSAR},
            "n_suitar": len({r["suite"] for r in maal}),
            "verdi": {n: _r(v[j]) for j, n in enumerate(N1_NAMN)},
            "ki95": {n: _ki(boot, j) for j, n in enumerate(N1_NAMN)},
            "perm_p": (_n1_perm(maal, nokkel, n_perm) if perm else None)}


def _n1_port(alle, nokkel="ut", n_boot=felles.N_BOOT):
    """The gate: share of old-wood chairs (WOOD, aar < 1900, quality ok) outside the frozen envelope."""
    port = [f for f in alle if _er_port(f)]
    ut = {"n": len(port), "terskel": N1_PORT_MAKS, "min_n": N1_PORT_MIN_N, "verdi": {}, "ki95": {}, "ok": {}}
    med_ki = bool(port) and n_boot > 0
    if med_ki:
        up = np.array([[f[nokkel][k] for k in NOKLAR] for f in port], float)
        boot = _boot(port, lambda ix: up[ix].mean(0), n_boot)
    ut["per_museum"] = {m: {"n": sum(1 for f in port if f["museum"] == m),
                            "verdi": {k: _r(np.mean([f[nokkel][k] for f in port if f["museum"] == m]))
                                      if any(f["museum"] == m for f in port) else None for k in NOKLAR}}
                        for m in ("NM", "VA")}
    for j, k in enumerate(NOKLAR):
        v = float(np.mean([f[nokkel][k] for f in port])) if port else float("nan")
        ut["verdi"][k] = _r(v)
        ut["ki95"][k] = _ki(boot, j) if med_ki else [None, None]
        ut["ok"][k] = bool(len(port) >= N1_PORT_MIN_N and np.isfinite(v) and v <= N1_PORT_MAKS)
    return ut


def _n1_dom(port, kjerne, krev_n=True):
    """-> (dom, list of primary lines). The conjunction named in SPEC_N1 and nothing else decides."""
    v, ki = kjerne["verdi"], kjerne["ki95"]
    a_v, a_lo, p = v["P1c_front"], ki["P1c_front"][0], kjerne["perm_p"]
    b_v, b_lo = v["b_front"], ki["b_front"][0]
    a_held = bool(a_v is not None and a_lo is not None and p is not None
                  and a_v >= N1_TERSKEL_KRYSSING and a_lo > 0 and p < N1_PERM_P)
    b_held = bool(b_v is not None and b_lo is not None and b_v >= N1_TERSKEL_TRE and b_lo > 0)
    primaer = [
        {"namn": "a_kryssing_P1c_front", "verdi": a_v, "ki95": ki["P1c_front"], "perm_p": _r(p, 5),
         "terskel": N1_TERSKEL_KRYSSING,
         "krav": "verdi >= %.2f og nedre grense > 0 og perm_p < %.2f" % (N1_TERSKEL_KRYSSING, N1_PERM_P),
         "held": a_held},
        {"namn": "b_forbode_ikkje_utenkt_front_fot", "verdi": b_v, "ki95": ki["b_front"],
         "terskel": N1_TERSKEL_TRE, "krav": "verdi >= %.2f og nedre grense > 0" % N1_TERSKEL_TRE,
         "held": b_held},
    ]
    port_ok = port["ok"]["front_fot"] and port["ok"]["front_rygg"]
    n_ok = (not krev_n) or all(kjerne["n"][c] >= N1_MIN_N_KLASSE for c in KLASSAR)
    if not port_ok or not n_ok:
        return "UGYLDIG", primaer
    return ("HELDT" if (a_held and b_held) else "SLO FEIL"), primaer


def _avheng(namn):
    """The view-zone keys a statistic depends on."""
    fast = {"P1c_front": {"front_fot", "front_rygg"}, "b_front": {"front_fot"},
            "ledd_fot_front": {"front_fot"}, "ledd_rygg_front": {"front_rygg"},
            "P1c_side": {"side_fot", "side_rygg"}, "b_side": {"side_fot"},
            "P1c_snitt": set(NOKLAR), "P1b_front": {"front_rygg"},
            "del_utanfor": {"front_fot"}, "minus_gammalt_tre": {"front_fot"},
            "front": {"front_fot", "front_rygg"}, "designar": {"side_fot", "front_rygg"}}
    if namn in fast:
        return fast[namn]
    return {k for k in NOKLAR if namn.endswith(k)}


def _masker(d, fjerna):
    """A zone that failed the gate is removed before the target classes are read: every statistic that uses
    it is blanked (None), in the primary and in the secondary lines alike."""
    if not fjerna:
        return d
    return {k: (None if _avheng(k) & set(fjerna) else v) for k, v in d.items()}


def _linje(namn, kjerne, kva=("P1c_front", "b_front"), fjerna=()):
    return {"namn": namn, "n": kjerne["n"], "n_suitar": kjerne.get("n_suitar"),
            "verdi": _masker({k: kjerne["verdi"][k] for k in kva}, fjerna),
            "ki95": _masker({k: kjerne["ki95"][k] for k in kva}, fjerna)}


def _dummy(klasse, flagg, i):
    return {"id": "_imputert_%d" % i, "suite": "_imputert_%d" % i, "klasse": klasse, "bolk": None,
            "ut": dict(zip(NOKLAR, flagg))}


def _etterslep(alle, n_boot=felles.N_BOOT):
    """Lag statistic (designers' F2, as a secondary without verdict): share outside the OWN zone for non-wood
    chairs dated before 1925 (LINE: foot; SHEET: shell) minus the share of WOOD chairs of 1900-1924 outside the
    same zones, weighted by the class mix of the early non-wood chairs. Near 0: the first chairs in a new
    material sit where wood sat (lag). Clearly positive: the region opened at once.
    Two versions: 'front' (both zones in the front view) and 'designar' (LINE foot in the side view, SHEET
    shell in the front view, as in historie/e10_etterslep.py)."""
    tidleg = [f for f in alle if f["kv"] and f["klasse"] in ("LINE", "SHEET")
              and f["aar"] is not None and f["aar"] < AAR_MAAL]
    tre = [f for f in alle if f["kv"] and f["klasse4"] == "WOOD"
           and f["aar"] is not None and AAR_ARKIV <= f["aar"] < AAR_MAAL]
    soner = {"front": {"LINE": "front_fot", "SHEET": "front_rygg"},
             "designar": {"LINE": "side_fot", "SHEET": "front_rygg"}}

    def stat(rs):
        ut = []
        t = [r for r in rs if r["klasse"] in ("LINE", "SHEET") and r["aar"] < AAR_MAAL and r["klasse4"] != "WOOD"]
        w = [r for r in rs if r["klasse4"] == "WOOD"]
        for ver in ("front", "designar"):
            if not t or not w:
                ut.append(np.nan)
                continue
            eigen = np.mean([r["ut"][soner[ver][r["klasse"]]] for r in t])
            same = np.mean([np.mean([x["ut"][soner[ver][r["klasse"]]] for x in w]) for r in t])
            ut.append(eigen - same)
        return ut

    begge = tidleg + tre
    v = stat(begge) if begge else [np.nan, np.nan]
    boot = felles.klyngebootstrap(begge, stat, n=n_boot) if begge else np.full((2, 2), np.nan)
    return {"namn": "etterslep_F2", "n_tidleg_ikkje_tre": len(tidleg),
            "n_tidleg_per_klasse": {c: sum(1 for f in tidleg if f["klasse"] == c) for c in ("LINE", "SHEET")},
            "n_tre_1900_1924": len(tre),
            "verdi": {"front": _r(v[0]), "designar": _r(v[1])},
            "ki95": {"front": _ki(boot, 0), "designar": _ki(boot, 1)},
            "merknad": "no verdict; decided by very few chairs with the least reliable material tokens"}


def _hoegdlinje(maal, n_boot, n_perm):
    """Height base model for the shell zone (secondary, no verdict). The meshes are scaled to the catalogue
    height H and the shell zone is fixed at 60-200 cm, so a chair lower than every archive chair (H below
    ARKIV_H_MIN) is almost empty there and falls outside whatever its shape. The line shows how much of the
    crossing is more than that: the crossing among targets with H >= ARKIV_H_MIN, the crossing when the
    shell-zone flag is REPLACED by the catalogue fact 'H < ARKIV_H_MIN', and the permutation p when class is
    permuted within 25-year bin x height band."""
    m = [f for f in maal if f.get("H") is not None]
    if not m:
        return {"namn": "hoegd_grunnmodell", "n": 0, "verdi": None}
    lav = np.array([f["H"] < ARKIV_H_MIN for f in m])
    ur = np.array([f["ut"]["front_rygg"] for f in m], bool)
    kl = np.array([f["klasse"] for f in m])
    del_ = lambda x: _r(x.mean()) if len(x) else None
    per = {c: {"n": int((kl == c).sum()), "del_lagare_enn_arkivet": del_(lav[kl == c]),
               "rygg_utanfor_blant_laage": del_(ur[(kl == c) & lav]),
               "rygg_utanfor_blant_hoege": del_(ur[(kl == c) & ~lav])} for c in KLASSAR}
    hoege = _n1_kjerne([f for f, x in zip(m, lav) if not x], "ut", n_boot, perm=False)
    berre_h = _n1_kjerne([dict(f, ut=dict(f["ut"], front_rygg=bool(x))) for f, x in zip(m, lav)], "ut", n_boot,
                         perm=False)
    return {"namn": "hoegd_grunnmodell", "n": len(m), "grense_cm": ARKIV_H_MIN, "per_klasse": per,
            "samsvar_ryggflagg_og_laag_hoegd": _r(np.mean(ur == lav)),
            "verdi": {"P1c_front_berre_H_minst_78": hoege["verdi"]["P1c_front"],
                      "P1c_front_ryggflagg_bytt_med_H_under_78": berre_h["verdi"]["P1c_front"],
                      "perm_p_innan_bolk_og_hoegdband": _r(_n1_perm(m, "ut", n_perm, hoegdband=True), 5)},
            "ki95": {"P1c_front_berre_H_minst_78": hoege["ki95"]["P1c_front"],
                     "P1c_front_ryggflagg_bytt_med_H_under_78": berre_h["ki95"]["P1c_front"]},
            "n_H_minst_78": hoege["n"]}


def _n1_resultat(alle, utval="dev", n_boot=felles.N_BOOT, n_perm=N1_N_PERM, med_sekundaer=True, krev_n=True):
    """N1 on one population of feature dicts (real or synthetic). The gate is computed first; it decides on
    its point values (its intervals are only computed for the full report)."""
    port = _n1_port(alle, "ut", n_boot if med_sekundaer else 0)
    fjerna = [k for k in NOKLAR if not port["ok"][k]]
    maal = [f for f in alle if _er_maal(f)]
    kjerne = _n1_kjerne(maal, "ut", n_boot, n_perm)
    dom, primaer = _n1_dom(port, kjerne, krev_n)
    for pr, nokkel in zip(primaer, ("P1c_front", "b_front")):
        if _avheng(nokkel) & set(fjerna):          # not read: its zone failed the gate
            pr.update({"verdi": None, "ki95": [None, None], "held": None, "merknad": "sona fall i porten; ikkje lesen"})
            if "perm_p" in pr:
                pr["perm_p"] = None
    res = {
        "id": "N1", "n": kjerne["n"], "n_suitar": kjerne["n_suitar"],
        "port": [
            {"namn": "gammalt_tre_utanfor_konvolutten", "n": port["n"], "terskel": N1_PORT_MAKS,
             "verdi": port["verdi"], "ki95": port["ki95"], "per_museum": port["per_museum"],
             "ok_per_sone": port["ok"],
             "fjerna_soner": fjerna,
             "leave_one_out_paa_arkivet": bool(utval == "dev"),
             "merknad": ("on DEV the gate chairs ARE the archive, scored leave-one-out, so 0.05 holds by "
                         "construction; the gate is a real test on the held-out side only" if utval == "dev"
                         else "held-out old-wood chairs scored against the frozen DEV archive"),
             "ok": bool(port["ok"]["front_fot"] and port["ok"]["front_rygg"])},
            {"namn": "n_per_klasse", "terskel": N1_MIN_N_KLASSE, "verdi": kjerne["n"],
             "ok": bool((not krev_n) or all(kjerne["n"][c] >= N1_MIN_N_KLASSE for c in KLASSAR)),
             "brukt": bool(krev_n)},
        ],
        "primaer": primaer, "dom": dom,
    }
    if not med_sekundaer:
        return res

    mask = lambda d: _masker(d, fjerna)
    linje = lambda namn, kj: _linje(namn, kj, fjerna=fjerna)

    sek = []
    sek.append({"namn": "del_utanfor_per_klasse_visning_sone", "n": kjerne["n"],
                "verdi": mask({n: kjerne["verdi"][n] for n in N1_RATENAMN}),
                "ki95": mask({n: kjerne["ki95"][n] for n in N1_RATENAMN})})
    sek.append({"namn": "kryssinga_ledd_for_ledd", "n": kjerne["n"],
                "verdi": mask({k: kjerne["verdi"][k] for k in ("ledd_fot_front", "ledd_rygg_front")}),
                "ki95": mask({k: kjerne["ki95"][k] for k in ("ledd_fot_front", "ledd_rygg_front")}),
                "merknad": "P1c_front = ledd_fot_front + ledd_rygg_front. The foot term (LINE leaves the foot more "
                           "than SHEET) is the expected part; the shell term (SHEET leaves the shell more than "
                           "LINE) is the other half of the crossing. If only the foot term is above 0, the primary "
                           "statistic was carried by the expected part alone."})
    sek.append({"namn": "sidevisning_og_snitt", "n": kjerne["n"],
                "verdi": mask({k: kjerne["verdi"][k] for k in ("P1c_side", "b_side", "P1c_snitt", "P1b_front")}),
                "ki95": mask({k: kjerne["ki95"][k] for k in ("P1c_side", "b_side", "P1c_snitt", "P1b_front")}),
                "merknad": "b_side is the designer's P1a; P1b_front = SHEET - WOOD in the shell zone"})
    # the WOOD rate that bears on forbidden against unthought, against the old-wood rate of the gate
    tre_ny = [f for f in maal if f["klasse"] == "WOOD"]
    gml = [f for f in alle if _er_port(f)]
    if tre_ny and gml:
        begge_tre = tre_ny + gml
        ny_m = np.array([r["aar"] >= AAR_MAAL for r in begge_tre])
        ut_m = np.array([r["ut"]["front_fot"] for r in begge_tre], float)

        def tre_stat(ix):
            a, b = ut_m[ix][ny_m[ix]], ut_m[ix][~ny_m[ix]]
            return [a.mean() if len(a) else np.nan, (a.mean() - b.mean()) if len(a) and len(b) else np.nan]
        tv = tre_stat(np.arange(len(begge_tre)))
        tb = _boot(begge_tre, tre_stat, n_boot)
        sek.append({"namn": "tre_fraa_1925_utanfor_fot_front", "n": len(tre_ny),
                    "verdi": mask({"del_utanfor": _r(tv[0]), "minus_gammalt_tre": _r(tv[1])}),
                    "ki95": mask({"del_utanfor": _ki(tb, 0), "minus_gammalt_tre": _ki(tb, 1)})})
    # pure LINE and LINE+SHEET as its own class
    rein = [f for f in maal if f["klasse4"] != "LINE+SHEET"]
    sek.append(linje("rein_LINE_utan_LINE+SHEET", _n1_kjerne(rein, "ut", n_boot, perm=False)))
    ls = [f for f in maal if f["klasse4"] == "LINE+SHEET"]
    if ls:
        lb = felles.klyngebootstrap(ls, lambda rs: [np.mean([r["ut"][k] for r in rs]) for k in NOKLAR], n=n_boot)
        sek.append({"namn": "LINE+SHEET_som_eigen_klasse", "n": len(ls),
                    "verdi": mask({k: _r(np.mean([f["ut"][k] for f in ls])) for k in NOKLAR}),
                    "ki95": mask({k: _ki(lb, j) for j, k in enumerate(NOKLAR)})})
    # robustness lines
    sek.append(linje("robust_mesh_sete_minst_42cm",
                     _n1_kjerne([f for f in maal if f["sete_mesh"] is not None and f["sete_mesh"] >= N1_SETE_MIN],
                                "ut", n_boot, perm=False)))
    port_d = _n1_port(alle, "ut_d", 200)
    sek.append(dict(linje("robust_dilatert_2px", _n1_kjerne(maal, "ut_d", n_boot, perm=False)),
                    konvolutt_dilatert={k: _r(v, 6) for k, v in _arkiv(True)["terskel"].items()},
                    port_dilatert=port_d["verdi"]))
    sek.append(linje("robust_ogsaa_kvalitet_front", _n1_kjerne([f for f in maal if f["kv_front"]], "ut",
                                                                n_boot, perm=False)))
    # attrition from the quality rule and worst-case imputation
    kand = [f for f in alle if f["klasse"] in _KODE and f["aar"] is not None and f["aar"] >= AAR_MAAL]
    falt = [f for f in kand if not f["kv"]]
    fra = {c: {"kandidatar": sum(1 for f in kand if f["klasse"] == c),
               "falt": sum(1 for f in falt if f["klasse"] == c)} for c in KLASSAR}
    inne = [_dummy("LINE", (False, False, False, False), i) for i, f in enumerate(falt) if f["klasse"] == "LINE"]
    streng = []
    for i, f in enumerate(falt):
        flagg = {"LINE": (False, True, False, True), "SHEET": (True, False, True, False),
                 "WOOD": (True, False, True, False)}[f["klasse"]]
        streng.append(_dummy(f["klasse"], flagg, i))
    sek.append(dict(linje("fraafall_verste_fall_LINE_innanfor", _n1_kjerne(maal + inne, "ut", n_boot, perm=False)),
                    fraafall_per_klasse=fra))
    sek.append(linje("fraafall_strengt_verste_fall", _n1_kjerne(maal + streng, "ut", n_boot, perm=False)))
    hl = _hoegdlinje(maal, n_boot, n_perm)
    if hl.get("verdi") and ("front_fot" in fjerna or "front_rygg" in fjerna):
        hl["verdi"] = {k: None for k in hl["verdi"]}
        hl["ki95"] = {k: [None, None] for k in hl["ki95"]}
    sek.append(hl)
    lag = _etterslep(alle, n_boot)
    lag["verdi"], lag["ki95"] = mask(lag["verdi"]), mask(lag["ki95"])
    sek.append(lag)
    for mus in ("NM", "VA"):
        sek.append(linje("museum_" + mus, _n1_kjerne([f for f in maal if f["museum"] == mus], "ut", n_boot,
                                                      perm=False)))
    res["sekundaer"] = sek
    return res


# ============================================================================ E2: scoring
def _eps2(y, g, krev=3):
    """Kelley's epsilon squared of a one-way layout: (SS_between - (k-1) MS_within) / SS_total.
    NaN unless exactly `krev` classes are present with at least 2 values each."""
    y = np.asarray(y, float)
    g = np.asarray(g)
    kl = np.unique(g)
    n, k = len(y), len(kl)
    if k != krev or n - k < 1:
        return float("nan")
    m = y.mean()
    sst = float(((y - m) ** 2).sum())
    if sst <= 0:
        return float("nan")
    ssb = 0.0
    for c in kl:
        v = y[g == c]
        if len(v) < 2:
            return float("nan")
        ssb += len(v) * (v.mean() - m) ** 2
    return float((ssb - (k - 1) * (sst - ssb) / (n - k)) / sst)


def _r2_log(lm, lk):
    """Reliability of the log mesh seat height: squared Pearson correlation with the log catalogue seat height
    (arrays of logs). NaN with fewer than 10 pairs or a correlation that is not positive."""
    if len(lm) < 10 or lm.std() == 0 or lk.std() == 0:
        return float("nan")
    r = float(np.corrcoef(lm, lk)[0, 1])
    return r * r if r > 0 else float("nan")


def _korriger(e, r2):
    """Disattenuation: observed eps2 divided by the reliability, clipped to [-1, 1]."""
    if not np.isfinite(e) or not np.isfinite(r2) or r2 <= 0:
        return float("nan")
    return float(np.clip(e / r2, -1.0, 1.0))


def _i_rel(f):
    return bool(f["kv"] and f["sete_mesh"] is not None and f["sete_kat"] is not None)


def _i_e2(f):
    return bool(_er_maal(f) and f["sete_mesh"] is not None and f["uf_side"] is not None)


E2_NAMN = ["differanse", "eps2_underfyll", "eps2_sete_mesh", "r2", "eps2_sete_korrigert",
           "differanse_r2_fraa_1925", "r2_fraa_1925", "differanse_front", "differanse_rang",
           "differanse_utan_blokk", "differanse_fire_klassar",
           "median_sete_mesh_LINE", "median_sete_mesh_SHEET", "median_sete_mesh_WOOD"]
_K4 = {c: j for j, c in enumerate(felles.KLASSAR)}


def _e2_tabell(recs):
    """Arrays for E2 from feature dicts of chairs in the reliability sample, in the E2 sample, or in both."""
    nan = float("nan")
    tal = lambda nok: np.array([nan if r[nok] is None else float(r[nok]) for r in recs], float)
    with np.errstate(invalid="ignore"):
        return {"rel": np.array([_i_rel(r) for r in recs], bool),
                "e2": np.array([_i_e2(r) for r in recs], bool),
                "ny": np.array([r["aar"] is not None and r["aar"] >= AAR_MAAL for r in recs], bool),
                "lm": np.log(tal("sete_mesh")), "lk": np.log(tal("sete_kat")),
                "g": np.array([_KODE.get(r["klasse"], -1) for r in recs]),
                "g4": np.array([_K4.get(r["klasse4"], -1) for r in recs]),
                "uf": tal("uf_side"), "uff": tal("uf_front"),
                "blokk": np.array([bool(r["blokk"]) for r in recs], bool)}


def _e2_vektor(t, ix=None, heil=True):
    """E2 statistics of one (re)sample, in the order of E2_NAMN (only the first five when heil is False).
    differanse = eps2(class -> under-fill) - eps2(class -> log mesh seat height) / r2."""
    T = t if ix is None else {k: v[ix] for k, v in t.items()}
    nan = float("nan")
    n_ut = len(E2_NAMN) if heil else 5
    rel = T["rel"]
    r2 = _r2_log(T["lm"][rel], T["lk"][rel])
    e = T["e2"]
    if e.sum() < 6:
        return [nan] * n_ut
    g, uf, ls = T["g"][e], T["uf"][e], T["lm"][e]
    e_uf, e_s = _eps2(uf, g), _eps2(ls, g)
    kor = _korriger(e_s, r2)
    ut = [e_uf - kor, e_uf, e_s, r2, kor]
    if not heil:
        return ut
    ny = rel & T["ny"]
    r2_ny = _r2_log(T["lm"][ny], T["lk"][ny])
    uff, g4, ib = T["uff"][e], T["g4"][e], ~T["blokk"][e]
    k4 = len(np.unique(g4))
    med = [float(np.median(np.exp(ls[g == c]))) if (g == c).any() else nan for c in range(3)]
    return ut + [e_uf - _korriger(e_s, r2_ny), r2_ny,
                 _eps2(uff, g) - kor,
                 _eps2(rankdata(uf), g) - _korriger(_eps2(rankdata(ls), g), r2),
                 _eps2(uf[ib], g[ib]) - _korriger(_eps2(ls[ib], g[ib]), r2),
                 _eps2(uf, g4, krev=k4) - _korriger(_eps2(ls, g4, krev=k4), r2)] + med


def _e2_katalog(alle, n_boot):
    """eps2 of class on log CATALOGUE seat height, chairs from 1925 with a catalogue seat (no mesh value enters;
    copied dimension records dropped). Three samples: all, those passing the quality rule, those not block-like."""
    def stat(rs):
        ut = []
        for utv in (rs, [r for r in rs if r["kv"]], [r for r in rs if r["kv"] and not r["blokk"]]):
            if len(utv) < 6:
                ut.append(np.nan)
                continue
            ut.append(_eps2(np.log([r["sete_kat"] for r in utv]), np.array([_KODE[r["klasse"]] for r in utv])))
        kv = [r for r in rs if r["kv"]]
        if len(kv) < 6:
            ut.append(np.nan)
        else:       # same chairs, same statistic, no correction: under-fill against the catalogue seat height
            ut.append(_eps2(np.array([r["uf_side"] for r in kv]), np.array([_KODE[r["klasse"]] for r in kv])) - ut[1])
        g = {c: [r["sete_kat"] for r in rs if r["klasse"] == c] for c in KLASSAR}
        return ut + [float(np.median(g[c])) if g[c] else np.nan for c in KLASSAR]

    namn = ["alle", "kvalitet_ok", "kvalitet_ok_utan_blokk", "eps2_underfyll_minus_eps2_katalogsete_kvalitet_ok",
            "median_LINE", "median_SHEET", "median_WOOD"]
    ut = []
    for merke, f in (("alle_museum", lambda r: True), ("NM", lambda r: r["museum"] == "NM"),
                     ("VA", lambda r: r["museum"] == "VA")):
        kat = [r for r in alle if r["klasse"] in _KODE and r["aar"] is not None and r["aar"] >= AAR_MAAL
               and r["sete_kat"] is not None and not r["maal_kopi"] and f(r)]
        if not kat:
            ut.append({"namn": "eps2_katalogsete_" + merke, "n": 0, "verdi": None})
            continue
        v = stat(kat)
        b = felles.klyngebootstrap(kat, stat, n=n_boot)
        ut.append({"namn": "eps2_katalogsete_" + merke, "n": len(kat),
                   "n_kvalitet_ok": sum(1 for r in kat if r["kv"]),
                   "n_blokk": sum(1 for r in kat if r["kv"] and r["blokk"]),
                   "n_per_klasse": {c: sum(1 for r in kat if r["klasse"] == c) for c in KLASSAR},
                   "verdi": {k: _r(v[j]) for j, k in enumerate(namn)},
                   "ki95": {k: _ki(b, j) for j, k in enumerate(namn)}})
    return ut


def _e2_resultat(alle, n_boot=felles.N_BOOT, med_sekundaer=True, krev_n=True):
    """E2 on one population of feature dicts (real or synthetic). The gate is computed first."""
    begge = [f for f in alle if _i_rel(f) or _i_e2(f)]
    e = [f for f in alle if _i_e2(f)]
    n_kl = {c: sum(1 for f in e if f["klasse"] == c) for c in KLASSAR}
    n_rel = sum(1 for f in alle if _i_rel(f))
    t = _e2_tabell(begge)
    namn = E2_NAMN if med_sekundaer else E2_NAMN[:5]
    v = _e2_vektor(t, None, med_sekundaer)
    boot = _boot(begge, lambda ix: _e2_vektor(t, ix, med_sekundaer), n_boot)
    verdi = {k: _r(v[j]) for j, k in enumerate(namn)}
    ki = {k: _ki(boot, j) for j, k in enumerate(namn)}
    r2_ok = bool(verdi["r2"] is not None and verdi["r2"] >= E2_R2_MIN)
    n_ok = bool((not krev_n) or all(n_kl[c] >= E2_MIN_N_KLASSE for c in KLASSAR))
    d, lo = verdi["differanse"], ki["differanse"][0]
    held = bool(d is not None and lo is not None and d > E2_TERSKEL and lo > 0)
    dom = "UGYLDIG" if not (r2_ok and n_ok) else ("HELDT" if held else "SLO FEIL")
    res = {
        "id": "E2", "n": n_kl, "n_reliabilitet": n_rel, "n_suitar": len({f["suite"] for f in begge}),
        "port": [
            {"namn": "reliabilitet_mesh_sete_r2", "n": n_rel, "terskel": E2_R2_MIN, "verdi": verdi["r2"],
             "ki95": ki["r2"], "ok": r2_ok},
            {"namn": "n_per_klasse", "terskel": E2_MIN_N_KLASSE, "verdi": n_kl, "ok": n_ok, "brukt": bool(krev_n)},
        ],
        "primaer": [{"namn": "eps2_underfyll_minus_eps2_sete_korrigert", "verdi": d, "ki95": ki["differanse"],
                     "terskel": E2_TERSKEL, "krav": "verdi > 0 og nedre grense > 0", "held": held}],
        "dom": dom,
    }
    if not med_sekundaer:
        return res
    sek = [{"namn": "delane", "verdi": {k: verdi[k] for k in E2_NAMN[1:5]}, "ki95": {k: ki[k] for k in E2_NAMN[1:5]}},
           {"namn": "differanse_variantar",
            "verdi": {k: verdi[k] for k in E2_NAMN[5:11]}, "ki95": {k: ki[k] for k in E2_NAMN[5:11]},
            "n_blokk": sum(1 for f in e if f["blokk"]),
            "n_fraa_1925_med_katalogsete": sum(1 for f in alle if _i_rel(f) and f["aar"] is not None
                                               and f["aar"] >= AAR_MAAL)},
           {"namn": "ekvifinalitet_median_mesh_sete_cm", "n": n_kl,
            "verdi": {c: verdi["median_sete_mesh_" + c] for c in KLASSAR},
            "ki95": {c: ki["median_sete_mesh_" + c] for c in KLASSAR}}]
    sek += _e2_katalog(alle, n_boot)
    for mus in ("NM", "VA"):
        bm = [f for f in begge if f["museum"] == mus]
        if len([f for f in bm if _i_e2(f)]) < 6:
            sek.append({"namn": "museum_" + mus, "n": {c: sum(1 for f in bm if _i_e2(f) and f["klasse"] == c)
                                                       for c in KLASSAR}, "verdi": None})
            continue
        tm = _e2_tabell(bm)
        vm = _e2_vektor(tm, None, False)
        bb = _boot(bm, lambda ix: _e2_vektor(tm, ix, False), n_boot)
        sek.append({"namn": "museum_" + mus,
                    "n": {c: sum(1 for f in bm if _i_e2(f) and f["klasse"] == c) for c in KLASSAR},
                    "n_reliabilitet": sum(1 for f in bm if _i_rel(f)),
                    "verdi": {k: _r(vm[j]) for j, k in enumerate(E2_NAMN[:5])},
                    "ki95": {k: _ki(bb, j) for j, k in enumerate(E2_NAMN[:5])}})
    res["sekundaer"] = sek
    return res


# ============================================================================ attrition
def _fraafall(alle):
    """Attrition with reasons, for both hypotheses."""
    from collections import Counter
    fra1925 = [f for f in alle if f["aar"] is not None and f["aar"] >= AAR_MAAL]
    kand = [f for f in fra1925 if f["klasse"] in _KODE]
    grunnar = {c: dict(Counter(g for f in kand if f["klasse"] == c and not f["kv"]
                               for g in f["grunn"].split(";")).most_common()) for c in KLASSAR}
    gml = [f for f in alle if f["klasse4"] == "WOOD" and f["aar"] is not None and f["aar"] < AAR_ARKIV]
    return {
        "i_utvalet": len(alle),
        "utan_aar": sum(1 for f in alle if f["aar"] is None),
        "fraa_1925": len(fra1925),
        "fraa_1925_klasse_ANNA_ute": sum(1 for f in fra1925 if f["klasse"] is None),
        "fraa_1925_i_klassane": {c: sum(1 for f in kand if f["klasse"] == c) for c in KLASSAR},
        "av_desse_LINE+SHEET": sum(1 for f in kand if f["klasse4"] == "LINE+SHEET"),
        "fall_i_kvalitetsregelen": {c: sum(1 for f in kand if f["klasse"] == c and not f["kv"]) for c in KLASSAR},
        "grunnar_per_klasse (ein stol kan ha fleire)": grunnar,
        "N1_maal": {c: sum(1 for f in kand if f["klasse"] == c and f["kv"]) for c in KLASSAR},
        "E2_utan_mesh_sete": sum(1 for f in kand if f["kv"] and f["sete_mesh"] is None),
        "E2_utval": {c: sum(1 for f in kand if f["klasse"] == c and _i_e2(f)) for c in KLASSAR},
        "gammalt_tre_foer_1900": {"kandidatar": len(gml), "fall_i_kvalitetsregelen": sum(1 for f in gml if not f["kv"]),
                                   "portstolar": sum(1 for f in gml if f["kv"])},
        "1900_1924_ikkje_maal": sum(1 for f in alle if f["aar"] is not None and AAR_ARKIV <= f["aar"] < AAR_MAAL),
    }


# ============================================================================ public: kjoer
def kjoer(utval):
    """Run both hypotheses on 'dev' or 'held'. 'held' reads through the guarded loaders and has never been run."""
    alle = _last(utval)
    n1 = _n1_resultat(alle, utval, krev_n=(utval == "held"))
    e2 = _e2_resultat(alle, krev_n=(utval == "held"))
    ut = {
        "id": ID, "utval": utval, "n": len(alle), "fraafall": _fraafall(alle),
        "arkiv": {"n": ARKIV_N, "konvolutt": KONVOLUTT,
                  "kryssvalidert_del_utanfor_paa_DEV (to halvdelar)": _kryssvalidert_port()},
        "port": [dict(p, hypotese="N1") for p in n1["port"]] + [dict(p, hypotese="E2") for p in e2["port"]],
        "primaer": [dict(p, hypotese="N1") for p in n1["primaer"]] + [dict(p, hypotese="E2") for p in e2["primaer"]],
        "sekundaer": [dict(s, hypotese="N1") for s in n1["sekundaer"]] + [dict(s, hypotese="E2") for s in e2["sekundaer"]],
        "dom": {"N1": n1["dom"], "E2": e2["dom"]},
        "hypotesar": [n1, e2],
    }
    if utval == "dev":
        # how the literal thresholds follow from DEV (shown beside the literals; never recomputed on 'held')
        maal = [f for f in alle if _er_maal(f)]
        k = _n1_kjerne(maal, "ut", perm=False)
        ra, rb = _terskelregel(k["ki95"]["P1c_front"][0]), _terskelregel(k["ki95"]["b_front"][0])
        ut["dev_frysing"] = {
            "N1_TERSKEL_KRYSSING": {"literal": N1_TERSKEL_KRYSSING, "nedre_DEV": k["ki95"]["P1c_front"][0],
                                    "regel_gir": _r(ra), "stemmer": bool(ra is not None and abs(ra - N1_TERSKEL_KRYSSING) < 1e-9)},
            "N1_TERSKEL_TRE": {"literal": N1_TERSKEL_TRE, "nedre_DEV": k["ki95"]["b_front"][0],
                               "regel_gir": _r(rb), "stemmer": bool(rb is not None and abs(rb - N1_TERSKEL_TRE) < 1e-9)},
            "KONVOLUTT_rekna_paa_DEV": {kk: _r(v, 6) for kk, v in _arkiv()["rekna"].items()},
        }
    return ut


# ============================================================================ public: figurdata
def _kart(sils, lo=0, hi=140, v=16, h=144, steg=2):
    """Occupancy map in percent (int), rows lo..hi from the floor, columns v..h, in cells of `steg` cm."""
    if not sils:
        return None
    m = np.mean([np.asarray(s, float) for s in sils], 0)[lo:hi, v:h]
    r, k = m.shape
    m = m.reshape(r // steg, steg, k // steg, steg).mean((1, 3))
    return np.rint(100 * m).astype(int).tolist()


def _omriss(s, eps):
    """Outline polygons of one silhouette as lists of [column, row] (row 0 = floor), simplified by eps px."""
    kont, _ = cv2.findContours(np.asarray(s, np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    ut = []
    for c in kont:
        if cv2.contourArea(c) < 6:
            continue
        p = cv2.approxPolyDP(c, eps, True).reshape(-1, 2)
        ut.append([[int(x), int(y)] for x, y in p])
    return ut


def figurdata(utval):
    """What one plate needs: occupancy maps (front, side) of the frozen wood archive and of each target class
    from 1925, the envelope, the share outside per class and zone, per-chair nearest-archive distances, and 12
    example outlines per class (every k-th target chair in id order: no choice by eye). Under 300 KB."""
    alle = _last(utval)
    sil = felles.silhuett(utval)
    devsil = felles.silhuett("dev")
    ark = _arkiv()
    maal = [f for f in alle if _er_maal(f)]
    kjerne = _n1_kjerne(maal, "ut", perm=False)
    kart = {"ramme": {"rader_cm": [0, 140], "kolonnar_px": [16, 144], "celle_cm": 2, "eining": "prosent fylt",
                      "rad_0": "golv", "side_kolonne_0": "bak"},
            "arkiv": {"n": len(ark["ids"]), "front": _kart([devsil[i][1] for i in ark["ids"]]),
                      "side": _kart([devsil[i][0] for i in ark["ids"]])}}
    for c in KLASSAR:
        ids = [f["id"] for f in maal if f["klasse"] == c]
        kart[c] = {"n": len(ids), "front": _kart([sil[i][1] for i in ids]), "side": _kart([sil[i][0] for i in ids])}
    punkt = [{"id": f["id"], "klasse": f["klasse"], "klasse4": f["klasse4"], "aar": f["aar"], "museum": f["museum"],
              "H": f["H"], "d": {k: _r(f["d"][k], 3) for k in NOKLAR}, "ut": {k: int(f["ut"][k]) for k in NOKLAR},
              "underfyll_side": _r(f["uf_side"], 3), "sete_mesh": f["sete_mesh"], "sete_kat": f["sete_kat"]}
             for f in maal]
    ut = {"id": ID, "utval": utval, "soner_cm": SONER, "konvolutt": KONVOLUTT, "sigma_cm": SIGMA,
          "kart": kart,
          "del_utanfor": {"n": kjerne["n"], "verdi": {n: kjerne["verdi"][n] for n in N1_NAMN},
                          "ki95": {n: kjerne["ki95"][n] for n in N1_NAMN}},
          "arkiv_loo_avstand": {k: [_r(x, 3) for x in ark["loo"][k]] for k in NOKLAR},
          "stolar": punkt}
    for eps in (0.8, 1.2, 1.8, 2.5, 3.5):
        dome = {}
        for c in KLASSAR:
            kl = sorted((f for f in maal if f["klasse"] == c), key=lambda f: f["id"])
            if len(kl) > 12:
                kl = [kl[int(j * len(kl) / 12)] for j in range(12)]
            dome[c] = [{"id": f["id"], "namn": f["namn"][:40], "aar": f["aar"], "ut": {k: int(f["ut"][k]) for k in NOKLAR},
                        "front": _omriss(sil[f["id"]][1], eps), "side": _omriss(sil[f["id"]][0], eps)} for f in kl]
        ut["omriss"] = {"forenkling_px": eps, "per_klasse": dome}
        if len(json.dumps(ut, ensure_ascii=False).encode("utf-8")) < 290000:
            break
    if len(json.dumps(ut, ensure_ascii=False).encode("utf-8")) >= 290000:      # last resort: thin the point list
        ut["stolar"] = [{"id": q["id"], "klasse": q["klasse"], "H": q["H"],
                         "d": {k: q["d"][k] for k in ("front_fot", "front_rygg")}} for q in punkt]
        ut["arkiv_loo_avstand"] = {k: ut["arkiv_loo_avstand"][k] for k in ("front_fot", "front_rygg")}
    return ut


# ============================================================================ synthetic controls
# Expected held-out class sizes after the quality rule, used for the synthetic populations. Rule: catalogue
# counts of felles.tel_held() from 1925 (LINE 76, LINE+SHEET 80, SHEET 110, WOOD 111) times the DEV pass
# rates of the quality rule (8/14, 12/16, 15/20, 11/14), rounded to 5.
SYN_N = {"LINE": 100, "SHEET": 80, "WOOD": 85}
SYN_N_REL_ELDRE = 130       # old chairs with both seat heights in the synthetic reliability sample
SYN_DEL_KATALOG = 0.20      # share of the synthetic chairs from 1925 that get a catalogue seat height
SYN_REP = 100               # replicate populations per scenario (with reduced resampling, see below)
SYN_BOOT_REP = 300
SYN_PERM_REP = 1000


def _syn_aar(rng, n, aar_kjelde):
    return [int(a) for a in rng.choice(aar_kjelde, n)]


def _syn_n1_pop(rng, rater, aar_kjelde, port, n=SYN_N):
    """Feature-level synthetic N1 population: n[c] target chairs per class, each its own suite, years drawn from
    the DEV target years independently of class, the four outside flags drawn as independent Bernoulli variables
    with the rates rater[c] = (front_fot, front_rygg, side_fot, side_rygg). The gate chairs are the real DEV
    archive chairs."""
    ut = list(port)
    i = 0
    for c in KLASSAR:
        for a in _syn_aar(rng, n[c], aar_kjelde):
            fl = rng.random(4) < np.asarray(rater[c])
            ut.append({"id": "syn%d" % i, "suite": "syn%d" % i, "museum": "VA", "aar": a, "namn": "", "H": None,
                       "klasse": c, "klasse4": c, "bolk": felles.aarsbolk(a, 25), "kv": True, "kv_front": True,
                       "grunn": "ok", "sete_mesh": None, "sete_kat": None, "maal_kopi": False,
                       "ut": dict(zip(NOKLAR, (bool(x) for x in fl))), "ut_d": None, "d": None,
                       "uf_side": None, "uf_front": None, "blokk": False})
            i += 1
    return ut


def _permuter_klasse(alle, rng):
    """Copy of a population in which the class labels of the chairs from 1925 (three classes) are permuted
    within 25-year bins. Everything else (silhouette flags, under-fill, seat heights, suites) stays."""
    ut = [dict(f) for f in alle]
    ix = [i for i, f in enumerate(ut) if f["klasse"] in _KODE and f["aar"] is not None and f["aar"] >= AAR_MAAL]
    for b in sorted({ut[i]["bolk"] for i in ix}):
        medl = [i for i in ix if ut[i]["bolk"] == b]
        lapp = [(ut[i]["klasse"], ut[i]["klasse4"]) for i in medl]
        for i, j in zip(medl, rng.permutation(len(medl))):
            ut[i]["klasse"], ut[i]["klasse4"] = lapp[j]
    return ut


PLANTA_KUTT = 70            # cm: the planted 'low back' erases everything above this height


def _bbox_kol(s):
    kol = np.nonzero(s.any(0))[0]
    v, h = int(kol.min()), int(kol.max())
    return (v + h) // 2, h - v + 1


def _plant_fot(s):
    """Foot zone (rows 0-30) erased and replaced by a pedestal: a 4 px column on the centre line and a 2 px
    floor plate over 60 % of the width."""
    s = np.array(s, np.uint8)
    mid, br = _bbox_kol(s)
    s[0:30] = 0
    s[0:30, mid - 2:mid + 2] = 1
    s[0:2, mid - int(0.3 * br):mid + int(0.3 * br) + 1] = 1
    return s


def _plant_laag_rygg(s):
    """Everything above PLANTA_KUTT cm erased: a low back."""
    s = np.array(s, np.uint8)
    s[PLANTA_KUTT:] = 0
    return s


def _plant_laagt_skal(s):
    """Everything from 60 cm up erased and replaced by a solid shell, rows 60-80, 70 % of the width."""
    s = np.array(s, np.uint8)
    mid, br = _bbox_kol(s)
    s[60:] = 0
    s[60:80, mid - int(0.35 * br):mid + int(0.35 * br) + 1] = 1
    return s


def _plant_plate(s):
    """The back from 60 cm to the top filled solid over the whole width (a slab back)."""
    s = np.array(s, np.uint8)
    kol = np.nonzero(s.any(0))[0]
    topp = int(np.nonzero(s.any(1))[0].max())
    s[60:topp + 1, kol.min():kol.max() + 1] = 1
    return s


def _instrumentprobe():
    """What does the frozen envelope respond to? Each change is applied to all 152 archive chairs, which are
    then scored leave-one-out against the rest of the archive (front view). Untouched chairs fall outside at
    0.05 by construction."""
    ark = _arkiv()
    sil = felles.silhuett("dev")
    ut = {}
    for namn, fn in (("pidestallfot", _plant_fot), ("rygg_kutta_ved_70cm", _plant_laag_rygg),
                     ("laagt_tett_skal_60_80cm", _plant_laagt_skal), ("tett_plate_i_ryggen", _plant_plate)):
        fot, rygg = [], []
        for j, oid in enumerate(ark["ids"]):
            v = _sonevektorar(fn(sil[oid][0]), fn(sil[oid][1]))
            fot.append(_nn(v["front_fot"], ark["A"]["front_fot"], j, ark["sumA"]["front_fot"])
                       > ark["terskel"]["front_fot"])
            rygg.append(_nn(v["front_rygg"], ark["A"]["front_rygg"], j, ark["sumA"]["front_rygg"])
                        > ark["terskel"]["front_rygg"])
        ut[namn] = {"utanfor_front_fot": _r(np.mean(fot), 3), "utanfor_front_rygg": _r(np.mean(rygg), 3)}
    ut["lesing"] = ("the foot-zone envelope detects a changed layout of the foot and does not leak into the shell "
                    "zone; the shell-zone envelope detects a LOWER back but not a different solid shape in the same "
                    "height range: in the front view it is mostly a detector of total height")
    return ut


def _plant_silhuettar(rng):
    """Silhouette-level planted population for N1 (tests the instrument, not only the scoring). Every DEV
    archive chair is used once as the source of a synthetic chair 'from 1925' and scored leave-one-out against
    the rest of the archive. The sources are dealt at random into three classes, and the effect is planted in
    exactly every second chair of the class (planted size: half of the class):
      LINE-syn  : the foot zone is replaced by a pedestal (_plant_fot); shell untouched
      SHEET-syn : everything above 70 cm is erased, a low back (_plant_laag_rygg); foot untouched
      WOOD-syn  : untouched.
    Untouched zones fall outside at the leave-one-out rate of the archive (0.05 by construction). The years are
    drawn from the DEV target years independently of class."""
    ark = _arkiv()
    sil = felles.silhuett("dev")
    dev = {r["id"]: r for r in felles.les("dev")}
    aar_kjelde = [r["aar"] for r in dev.values() if r["aar"] is not None and r["aar"] >= AAR_MAAL]
    rekkje = rng.permutation(len(ark["ids"]))
    ut, n_pl = [], {"LINE": 0, "SHEET": 0, "WOOD": 0}
    for n, j in enumerate(rekkje):
        oid = ark["ids"][j]
        c = KLASSAR[n % 3]
        side, front = sil[oid]
        planta = bool((n // 3) % 2 == 0) and c != "WOOD"
        if planta and c == "LINE":
            side, front = _plant_fot(side), _plant_fot(front)
        if planta and c == "SHEET":
            side, front = _plant_laag_rygg(side), _plant_laag_rygg(front)
        n_pl[c] += int(planta)
        v = _sonevektorar(side, front)
        d = {k: _nn(v[k], ark["A"][k], j, ark["sumA"][k]) for k in NOKLAR}
        a = int(rng.choice(aar_kjelde))
        ut.append({"id": "plant_" + oid, "suite": "plant_" + dev[oid]["suite"], "museum": dev[oid]["museum"],
                   "aar": a, "namn": "", "H": None, "klasse": c, "klasse4": c, "bolk": felles.aarsbolk(a, 25),
                   "kv": True, "kv_front": True, "grunn": "ok", "sete_mesh": None, "sete_kat": None,
                   "maal_kopi": False, "d": d, "ut": {k: bool(d[k] > ark["terskel"][k]) for k in NOKLAR},
                   "ut_d": None, "uf_side": None, "uf_front": None, "blokk": False, "_planta": planta})
    return ut, n_pl


def _syn_e2_pop(rng, dev_alle, modus, n=SYN_N):
    """Feature-level synthetic E2 population built from DEV.
    Chairs from 1925 (n[c] per class, each its own suite):
      under-fill = DEV class mean of the side under-fill (modus 'planta', 'like_bunde') or the pooled DEV mean
                   (modus 'ingen') + a residual drawn from the pooled class-centred DEV residuals;
      true log seat height = DEV mean + a residual drawn from the pooled class-centred DEV catalogue residuals,
                   plus, in modus 'like_bunde', a class effect with the same standardised pattern as the under-fill
                   (so the population eta squared of the true seat height equals that of the under-fill);
      mesh seat height = true value x exp(e), e normal with the SD that gives the DEV reliability (r2 = 0.32);
                   in modus 'meshfeil' (as 'planta', seat height NOT class-bound) the mesh value also gets the
                   class-specific bias seen on DEV: the median of log(mesh / catalogue) of the class;
      catalogue seat height = the true value, kept for a share SYN_DEL_KATALOG of the chairs.
    Old chairs (SYN_N_REL_ELDRE, class WOOD, year 1800): true log seat height drawn from the DEV catalogue
    values of chairs before 1925, mesh value with the same error; they only feed the reliability."""
    e2 = [f for f in dev_alle if _i_e2(f) and f["sete_kat"] is not None]
    kl = np.array([f["klasse"] for f in e2])
    uf = np.array([f["uf_side"] for f in e2])
    lk = np.log(np.array([f["sete_kat"] for f in e2]))
    uf_m = {c: float(uf[kl == c].mean()) for c in KLASSAR}
    uf_res = np.concatenate([uf[kl == c] - uf_m[c] for c in KLASSAR])
    lk_res = np.concatenate([lk[kl == c] - lk[kl == c].mean() for c in KLASSAR])
    vekt = np.array([n[c] for c in KLASSAR], float) / sum(n.values())
    uf_snitt = float(sum(vekt[j] * uf_m[c] for j, c in enumerate(KLASSAR)))
    z = {c: (uf_m[c] - uf_snitt) / uf_res.std() for c in KLASSAR}          # standardised class pattern
    eldre = np.log(np.array([f["sete_kat"] for f in dev_alle if _i_rel(f) and f["aar"] is not None
                             and f["aar"] < AAR_MAAL]))
    lm = np.log(np.array([f["sete_mesh"] for f in e2]))
    skeiv = {c: (float(np.median(lm[kl == c] - lk[kl == c])) if modus == "meshfeil" else 0.0) for c in KLASSAR}
    sd_sann = float(np.sqrt(np.var(lk_res)))
    sd_feil = sd_sann * np.sqrt(1 / 0.32 - 1)
    aar_kjelde = [f["aar"] for f in e2]
    ut, i = [], 0
    for c in KLASSAR:
        for a in _syn_aar(rng, n[c], aar_kjelde):
            u = (uf_snitt if modus == "ingen" else uf_m[c]) + rng.choice(uf_res)
            t = lk.mean() + rng.choice(lk_res) + (z[c] * lk_res.std() if modus == "like_bunde" else 0.0)
            ut.append({"id": "syn%d" % i, "suite": "syn%d" % i, "museum": "VA", "aar": a, "namn": "", "H": None,
                       "klasse": c, "klasse4": c, "bolk": felles.aarsbolk(a, 25), "kv": True, "kv_front": True,
                       "grunn": "ok", "maal_kopi": False,
                       "sete_mesh": float(np.exp(t + skeiv[c] + rng.normal(0, sd_feil))),
                       "sete_kat": float(np.exp(t)) if rng.random() < SYN_DEL_KATALOG else None,
                       "uf_side": float(np.clip(u, 0, 1)), "uf_front": float(np.clip(u, 0, 1)), "blokk": False,
                       "ut": None, "ut_d": None, "d": None})
            i += 1
    for _ in range(SYN_N_REL_ELDRE):
        t = float(rng.choice(eldre))
        ut.append({"id": "syn%d" % i, "suite": "syn%d" % i, "museum": "VA", "aar": 1800, "namn": "", "H": None,
                   "klasse": "WOOD", "klasse4": "WOOD", "bolk": 1800, "kv": True, "kv_front": True, "grunn": "ok",
                   "maal_kopi": False, "sete_mesh": float(np.exp(t + rng.normal(0, sd_feil))),
                   "sete_kat": float(np.exp(t)), "uf_side": 0.3, "uf_front": 0.3, "blokk": False,
                   "ut": None, "ut_d": None, "d": None})
        i += 1
    return ut


def _kort_n1(res):
    return {"dom": res["dom"], "n": res["n"],
            "P1c_front": res["primaer"][0]["verdi"], "P1c_ki95": res["primaer"][0]["ki95"],
            "perm_p": res["primaer"][0]["perm_p"], "a_held": res["primaer"][0]["held"],
            "b_front": res["primaer"][1]["verdi"], "b_ki95": res["primaer"][1]["ki95"],
            "b_held": res["primaer"][1]["held"]}


def _kort_e2(res):
    return {"dom": res["dom"], "n": res["n"], "r2": res["port"][0]["verdi"],
            "differanse": res["primaer"][0]["verdi"], "ki95": res["primaer"][0]["ki95"]}


def _del_heldt(lagar, skaar, rep=SYN_REP):
    """Share of `rep` replicate populations judged HELDT (reduced resampling: SYN_BOOT_REP, SYN_PERM_REP)."""
    dommar = [skaar(lagar(np.random.default_rng(felles.FRO + 1000 + j)))["dom"] for j in range(rep)]
    return {"replikat": rep, "del_HELDT": _r(np.mean([d == "HELDT" for d in dommar]), 3),
            "del_SLO_FEIL": _r(np.mean([d == "SLO FEIL" for d in dommar]), 3),
            "del_UGYLDIG": _r(np.mean([d == "UGYLDIG" for d in dommar]), 3)}


def syntetisk_kontroll():
    """The same scoring code on synthetic populations built from DEV.
    Each control states the verdict it must give ('krav'); 'ok' says whether it did.
    The single verdict of each control uses the full procedure (2000 resamples, 10000 permutations) on one
    seeded population; 'operasjonskarakteristikk' repeats it on SYN_REP populations with reduced resampling."""
    dev = _last("dev")
    port = [f for f in dev if _er_port(f)]
    maal = [f for f in dev if _er_maal(f)]
    aar_kjelde = [f["aar"] for f in maal]
    k = _n1_vektor(*_n1_tabell(maal))
    rate = {c: tuple(k[6 + 4 * j: 10 + 4 * j]) for j, c in enumerate(KLASSAR)}       # DEV rates per class
    vekt = np.array([SYN_N[c] for c in KLASSAR], float) / sum(SYN_N.values())
    felles_rate = tuple(float(sum(vekt[j] * rate[c][m] for j, c in enumerate(KLASSAR))) for m in range(4))
    halv = {c: tuple(0.5 * (rate[c][m] + felles_rate[m]) for m in range(4)) for c in KLASSAR}
    # 'modern all over': LINE and SHEET share one rate in each zone (their weighted mean), WOOD as on DEV
    w2 = vekt[:2] / vekt[:2].sum()
    ls = tuple(float(w2[0] * rate["LINE"][m] + w2[1] * rate["SHEET"][m]) for m in range(4))
    overalt = {"LINE": ls, "SHEET": ls, "WOOD": rate["WOOD"]}
    # 'wood follows': the DEV crossing, but WOOD leaves the foot envelope as often as LINE
    fylgjer = {"LINE": rate["LINE"], "SHEET": rate["SHEET"],
               "WOOD": (rate["LINE"][0], rate["WOOD"][1], rate["LINE"][2], rate["WOOD"][3])}
    full = lambda pop: _n1_resultat(pop, "dev", med_sekundaer=False)
    rask = lambda pop: _n1_resultat(pop, "dev", n_boot=SYN_BOOT_REP, n_perm=SYN_PERM_REP, med_sekundaer=False)
    rng0 = lambda: np.random.default_rng(felles.FRO + 7)

    n1 = {}
    # (a) base model true: labels of the real DEV chairs permuted within 25-year bins
    n1["a_etikettar_permuterte_DEV"] = dict(
        _kort_n1(_n1_resultat(_permuter_klasse(dev, rng0()), "dev", med_sekundaer=False, krev_n=False)),
        krav="ikkje HELDT",
        operasjonskarakteristikk=_del_heldt(lambda r: _permuter_klasse(dev, r),
                                            lambda p: _n1_resultat(p, "dev", n_boot=SYN_BOOT_REP,
                                                                   n_perm=SYN_PERM_REP, med_sekundaer=False,
                                                                   krev_n=False)))
    n1["a_ingen_klasseeffekt_venta_storleik"] = dict(
        _kort_n1(full(_syn_n1_pop(rng0(), {c: felles_rate for c in KLASSAR}, aar_kjelde, port))),
        krav="ikkje HELDT", rater={c: [_r(x, 3) for x in felles_rate] for c in KLASSAR},
        operasjonskarakteristikk=_del_heldt(
            lambda r: _syn_n1_pop(r, {c: felles_rate for c in KLASSAR}, aar_kjelde, port), rask))
    # (b) effect planted
    pl, n_pl = _plant_silhuettar(rng0())
    snitt = lambda kl, nok, pla: _r(np.mean([f["ut"][nok] for f in pl if f["klasse"] == kl and f["_planta"] == pla]), 3)
    n1["b_planta_i_silhuettane"] = dict(
        _kort_n1(_n1_resultat(pl + port, "dev", med_sekundaer=False)), krav="HELDT",
        planta={"storleik": "every second chair of LINE-syn (pedestal foot) and of SHEET-syn (back cut at 70 cm)",
                "tal_planta": n_pl,
                "LINE_planta_utanfor_fot_front": snitt("LINE", "front_fot", True),
                "LINE_planta_utanfor_rygg_front (lekkasje)": snitt("LINE", "front_rygg", True),
                "SHEET_planta_utanfor_rygg_front": snitt("SHEET", "front_rygg", True),
                "SHEET_planta_utanfor_fot_front (lekkasje)": snitt("SHEET", "front_fot", True),
                "uroerte_utanfor_fot_front": _r(np.mean([f["ut"]["front_fot"] for f in pl if not f["_planta"]]), 3),
                "uroerte_utanfor_rygg_front": _r(np.mean([f["ut"]["front_rygg"] for f in pl if not f["_planta"]]), 3)})
    n1["b_planta_DEV_ratene_venta_storleik"] = dict(
        _kort_n1(full(_syn_n1_pop(rng0(), rate, aar_kjelde, port))), krav="HELDT",
        rater={c: [_r(x, 3) for x in rate[c]] for c in KLASSAR},
        operasjonskarakteristikk=_del_heldt(lambda r: _syn_n1_pop(r, rate, aar_kjelde, port), rask))
    n1["b_planta_halv_DEV_effekt (utan krav)"] = dict(
        _kort_n1(full(_syn_n1_pop(rng0(), halv, aar_kjelde, port))), krav=None,
        rater={c: [_r(x, 3) for x in halv[c]] for c in KLASSAR},
        operasjonskarakteristikk=_del_heldt(lambda r: _syn_n1_pop(r, halv, aar_kjelde, port), rask))
    # rival base models
    n1["c_moderne_overalt"] = dict(
        _kort_n1(full(_syn_n1_pop(rng0(), overalt, aar_kjelde, port))), krav="ikkje HELDT",
        rater={c: [_r(x, 3) for x in overalt[c]] for c in KLASSAR},
        operasjonskarakteristikk=_del_heldt(lambda r: _syn_n1_pop(r, overalt, aar_kjelde, port), rask))
    n1["d_tre_fylgjer_etter (utenkt, ikkje forbode)"] = dict(
        _kort_n1(full(_syn_n1_pop(rng0(), fylgjer, aar_kjelde, port))), krav="ikkje HELDT",
        rater={c: [_r(x, 3) for x in fylgjer[c]] for c in KLASSAR},
        operasjonskarakteristikk=_del_heldt(lambda r: _syn_n1_pop(r, fylgjer, aar_kjelde, port), rask))

    e2 = {}
    e2f = lambda pop: _e2_resultat(pop, med_sekundaer=False)
    e2r = lambda pop: _e2_resultat(pop, n_boot=SYN_BOOT_REP, med_sekundaer=False)
    e2["a_etikettar_permuterte_DEV"] = dict(
        _kort_e2(_e2_resultat(_permuter_klasse(dev, rng0()), med_sekundaer=False, krev_n=False)), krav="ikkje HELDT",
        operasjonskarakteristikk=_del_heldt(lambda r: _permuter_klasse(dev, r),
                                            lambda p: _e2_resultat(p, n_boot=SYN_BOOT_REP, med_sekundaer=False,
                                                                   krev_n=False)))
    e2["a_ingen_klasseeffekt_venta_storleik"] = dict(
        _kort_e2(e2f(_syn_e2_pop(rng0(), dev, "ingen"))), krav="ikkje HELDT",
        operasjonskarakteristikk=_del_heldt(lambda r: _syn_e2_pop(r, dev, "ingen"), e2r))
    e2["b_underfyll_klassebunde_sete_ikkje"] = dict(
        _kort_e2(e2f(_syn_e2_pop(rng0(), dev, "planta"))), krav="HELDT",
        operasjonskarakteristikk=_del_heldt(lambda r: _syn_e2_pop(r, dev, "planta"), e2r))
    e2["c_sete_like_klassebunde_som_underfyll"] = dict(
        _kort_e2(e2f(_syn_e2_pop(rng0(), dev, "like_bunde"))), krav="ikkje HELDT",
        operasjonskarakteristikk=_del_heldt(lambda r: _syn_e2_pop(r, dev, "like_bunde"), e2r))
    # not a requirement but a warning: the claim is TRUE in this population (seat height not class-bound), yet the
    # mesh reads the classes with the different biases seen on DEV, and the correction multiplies that by 1 / r2
    e2x = [f for f in dev if _i_e2(f) and f["sete_kat"] is not None]
    e2["d_paastanden_sann_men_meshfeilen_klassebunden (utan krav)"] = dict(
        _kort_e2(e2f(_syn_e2_pop(rng0(), dev, "meshfeil"))), krav=None,
        planta_skeivskap_cm_ved_43cm={c: _r(43 * (np.exp(np.median(
            [np.log(f["sete_mesh"] / f["sete_kat"]) for f in e2x if f["klasse"] == c])) - 1), 2) for c in KLASSAR},
        operasjonskarakteristikk=_del_heldt(lambda r: _syn_e2_pop(r, dev, "meshfeil"), e2r))

    def stettar(d):
        if d["krav"] is None:
            return None
        return bool(d["dom"] == "HELDT") if d["krav"] == "HELDT" else bool(d["dom"] != "HELDT")

    for blokk in (n1, e2):
        for d in blokk.values():
            d["ok"] = stettar(d)
    return {"id": ID, "syntetisk_storleik": {"per_klasse": SYN_N, "eldre_i_reliabilitetsutvalet": SYN_N_REL_ELDRE,
                                             "replikat": SYN_REP, "resampling_i_replikat": SYN_BOOT_REP,
                                             "permutasjonar_i_replikat": SYN_PERM_REP},
            "instrumentprobe_N1": _instrumentprobe(),
            "N1": n1, "E2": e2,
            "alle_krav_stetta": bool(all(d["ok"] is not False for b in (n1, e2) for d in b.values()))}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"kjoer_dev": kjoer("dev"), "syntetisk_kontroll": syntetisk_kontroll()},
                     ensure_ascii=False, indent=1))
