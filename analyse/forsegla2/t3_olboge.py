#!/usr/bin/env python3
"""t3_olboge.py - N2 (designers' K1): THE ELBOW. Second sealed test, analyse/forsegla2.

Run from the repository root:   python analyse/forsegla2/t3_olboge.py      (DEV and synthetic controls only)

WHAT IS TESTED
  A dimension that no museum catalogues - the height of the armrest above the seat - against a target region
  taken from the seated body BEFORE measuring (formlaere 1.324: an axis with a target region and a tolerance;
  3.11; and the warning of the illustration 6.6721 that spread alone does not say why).
  A = arm top above the floor (T1) minus seat height, in cm.

  PRIMARY, a conjunction, both required:
   (1) the median of A over held-out armchairs lies in [20.0, 25.0] cm;
   (2) A does not scale with the chair: the Theil-Sen slope of A on back height (H - seat) has a
       cluster-bootstrap upper 95 % bound below 0.20.
  Three verdicts: HELDT, SLO FEIL, UGYLDIG (a gate fixed below failed).

WHERE THE BAND COMES FROM (not from DEV)
  Pheasant, S. (1996) Bodyspace, 2nd ed., London: Taylor & Francis, section 4.3.7: an elbow rest 200-250 mm
  above the seat surface is generally considered suitable, and one somewhat lower than sitting elbow height is
  preferable to one that is higher. Table 2.3 (British adults 19-65): sitting elbow height 5th/50th/95th
  percentile 195/245/295 mm (men), 185/235/280 mm (women). The band [20.0, 25.0] is that rule, verbatim.
  DEV was seen before this file was written (median A 22.5); the band was not moved to fit it.

INSTRUMENT (frozen; starts from the body designer's side_measures, scratch kropp/inst.py, zone unchanged)
  Side silhouette, 1 cm per pixel, row 0 = floor, column 0 = back. Depth extent = first to last filled column.
  Zone = columns from 0.50 to 0.85 of the depth extent, counted from the back. In each zone column the filled
  runs are listed bottom-up and runs separated by fewer than 3 empty pixels are merged.
    T1 = median over the zone columns of the top of the TOPMOST run   (arm top above the floor, cm)
    T2 = median of the top of the next run below, if more than half of the columns have one (the detector's own
         seat line; missing for closed, upholstered arms)
  Seat reference: felles sete_mesh (seat height of the frozen mesh script, same mesh, same scale).
    A = T1 - sete_mesh                                   PRIMARY definition, used throughout
  Secondary definition (the measurement reviewer's alternative): only chairs whose own seat line agrees with the
  mesh seat, |T2 - sete_mesh| <= 6 cm; reported as a line without verdict, with A and with T1 - T2.
  WHY THIS CHOICE: T1 - sete_mesh is defined for closed arms as well (T2 is missing there), it uses one seat
  reference for every chair, and the failure the reviewer found (arm outside the zone, T1 = seat, T2 = a
  stretcher, 'A' of 20-30 cm) cannot occur: such a chair gets A near 0 and is counted as 'no arm in the zone'.

WHICH CHAIRS COUNT AS ARMCHAIRS (frozen)
  catalogue:  type == 'Armstol'  or  'arm' in the lower-cased catalogue name       (catalogue only)
  AND the frozen quality rule felles.kvalitet() passes (this also drops copied dimension records)
  AND sete_mesh exists
  AND the detector finds an arm:  8.0 <= A <= 45.0  (below 8: the top of the zone is the seat, the arm is short,
      low or outside the zone; above 45: the top of the zone is a back, a wing or a swapped view).
  The window 8-45 is the designer's; it is wide against the band (the band lies 12 cm above its lower edge).
  A secondary line uses the detector on ALL chairs whatever the catalogue calls them.

KNOWN BIASES, WITH DIRECTION
  median of A (criterion 1):
   - UNLOADED SEAT, downwards. Pheasant's 200-250 mm is above the seat surface as sat upon. The mesh gives the
     unloaded surface. A soft seat sinks under the sitter (the body designer's unverified figure: 2-4 cm), so
     the measured A understates the distance in use on upholstered chairs by up to that much.
   - MESH SEAT AGAINST CATALOGUE, about -0.75 cm on DEV. sete_mesh is the upper edge of the largest up-facing
     surface (cushion top). Catalogue seats are partly rail heights. DEV armchairs (n=36): sete_mesh minus
     catalogue seat median 0.0, mean +0.25, mean absolute 2.45 cm; median A with the mesh seat 22.5, with the
     catalogue seat 23.25.
   - SLOPING ARMS, downwards. The zone is the middle and front of the arm. Arms that sweep down towards the front
     (Hepplewhite, Sheraton and Regency patterns) are read below the height at the elbow. Four zone choices move
     the DEV median between 22.0 and 23.0.
   - WINDOW, upwards and small: arms lower than 8 cm above the seat are not counted (2 of 38 on DEV).
  slope (criterion 2):
   - SHARED SEAT ERROR, upwards (towards failure). A = T1 - s and back = H - s carry the same seat error with the
     same sign, which adds about var(error)/var(back) to the slope: 0.02 on DEV with the robust error variance
     of sete_mesh against the catalogue (2.2 cm)^2, 0.10 with the classical one (4.8 cm)^2, var(back) = 236.
     The bias makes criterion 2 harder to pass, not easier. A secondary line gives the slope of A on catalogue
     H, which is free of it.
  DEV is not a random half of the armchairs: every DEV chair has a catalogue seat height, only 40 of the 324
  held-out catalogue armchairs have one.

NO GROUND TRUTH
  No museum records arm height. The detector was checked by eye against the mesh silhouettes of all 45 DEV
  catalogue armchairs and of the 20 DEV chairs not catalogued as armchairs in which it reports an arm (15 of the
  20 have arms: settees, Windsor chairs, a corner chair, lounge chairs; 1 is a sofa seen end-on; 4 are shell or
  low chairs without arms). Of the 45 armchairs the detector reads the arm where the eye sees it in the zone;
  it misses two whose arm ends behind the zone (O56348) or sweeps down to the seat inside it (O63266), and it
  reads swept arms (O145061, O372368) at mid-slope, 5-10 cm below their height at the back.
  That is a check against the mesh, not against the chair. The blind
  hand-measurement from the museum photographs that the measurement reviewer asked for has NOT been done.
  [independent check, 13 Nov] A by-eye audit against the museum photographs of 20 DEV armchairs (seeded) has
  now been done; it is not a hand-measurement and not strictly blind. Result in SPEC['augnemaal_mot_foto']:
  detector A minus photograph A has median -0.75 cm and median absolute difference 1.25 cm on the 18 chairs the
  detector analyses; 2 of the 20 have arms and are dropped as 'no arm in the zone'.

CHANGES BY THE INDEPENDENT CHECK (13 Nov 2026), each marked '[independent check'
  1. Criterion 2 is decided on the unrounded upper bound (was: on the bound rounded to three decimals, which
     failed a bound in [0.1995, 0.2000)). No effect on DEV (0.196).
  2. SPEC: every gate now carries 'regel_for_terskel' and 'dev_verdi'; new keys 'kjende_skeivskapar' (with
     the datum offset T1 against sete_mesh, +0.4 to +1 cm, which was not listed) and 'augnemaal_mot_foto';
     the single name-only match in the held-out catalogue is named in 'utval'.
  No threshold, constant, sample rule or statistic was changed.

BLINDNESS
  The held-out path goes through felles.les('held') and felles.silhuett('held') only; both are guarded and were
  never called while this file was written. Every number below marked DEV comes from kjoer('dev').
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import felles  # noqa: E402

# ============================================================================ frozen constants
SONE = (0.50, 0.85)          # zone of the side depth extent, from the back (designer's choice, unchanged)
SONE_ALBOGE = (0.30, 0.65)   # sensitivity zone nearer the back (secondary line only)
MINGAP = 3                   # runs separated by fewer than 3 empty pixels are merged
ARM_MIN, ARM_MAX = 8.0, 45.0     # detector window on A = T1 - sete_mesh
SAMSVAR_CM = 6.0             # secondary definition: |T2 - sete_mesh| <= 6 cm

BAND = (20.0, 25.0)          # criterion 1; Pheasant (1996) section 4.3.7, verbatim
HELLING_TAK = 0.20           # criterion 2; upper 95 % bound of the slope must be BELOW this

# gates (UGYLDIG when one fails)
PORT_N_MIN = 100             # analysed armchairs
PORT_DEL_ANALYSERT_MIN = 0.50    # analysed / catalogue armchairs
PORT_DEL_FUNNE_MIN = 0.70    # detector finds an arm / catalogue armchairs with quality and seat
PORT_KONTROLL_ABS_MAX = 3.0  # |median(T1 - sete_mesh)| on chairs NOT catalogued as armchairs
PORT_KONTROLL_DEL_MAX = 0.25     # share of those chairs in which the detector reports an arm
PORT_RYGG_IQR_MIN = 10.0     # interquartile range of back height among analysed armchairs, cm

# three-way comparison: coefficients FROZEN from DEV (36 analysed armchairs)
C_KROPP_MESH = 22.5          # body:  arm top = sete_mesh + 22.5      (DEV median of T1 - sete_mesh)
C_KROPP_KAT = 23.25          # body:  arm top = catalogue seat + 23.25 (DEV median of T1 - catalogue seat)
C_BORD = 67.5                # table: arm top = 67.5 cm from the floor (DEV median of T1)
C_STORLEIK = 0.6236          # size:  arm top = 0.6236 * H            (DEV median of T1 / H)

# seat noise from DEV suite pairs: all 63 pairs of DEV chairs in one suite (19 suites) with sete_mesh, no copied
# record. d = difference of sete_mesh within a pair; noise variance of one reading = E[d^2] / 2.
SETESTOY_VAR_ROBUST = 1.10   # (1.4826 * median|d|)^2 / 2                 = 1.10 cm^2 (SD 1.05 cm)
SETESTOY_VAR_KLASSISK = 1.37     # mean(d^2) / 2 over the 61 pairs with |d| <= 10 cm = 1.37 cm^2 (SD 1.17 cm)
# NOT used: the untrimmed mean(d^2) / 2 = 11.25 cm^2. Two pairs (one Selene chair read at 20 cm against 45)
# carry 88 % of it; a seat error of that size puts A outside the window 8-45, so it is not in the analysed
# sample, and subtracting 11.25 over-corrects: in synthetic control d (arm at a constant height above the
# floor, where the ratio must exceed 1) it gave R = 0.91. This is repeatability between meshes of one model,
# not the error of sete_mesh against the true seat (DEV, against the catalogue: MAD-SD 2.2 cm, SD 4.8 cm).

PERIODAR = (("before 1700", None, 1700), ("1700-1799", 1700, 1800), ("1800-1899", 1800, 1900),
            ("1900 on", 1900, None))

SPEC = {
    "id": "N2",
    "tittel": "The elbow: the armrest sits at sitting elbow height above the seat and does not follow the size "
              "of the chair",
    "slag": "ny",
    "proposisjonar": ["6.6721", "1.324", "3.11"],
    "paastand": (
        "The seated body gives a two-sided target that no museum catalogues: the armrest 200-250 mm above the "
        "seat (Pheasant 1996, section 4.3.7; sitting elbow height medians 245 mm men, 235 mm women, Table 2.3). "
        "If the body is the source, the median arm height above the seat of museum armchairs lies in that "
        "region, and the arm does not grow with the chair: backs that are tens of centimetres taller do not "
        "carry higher arms. 6.6721 is an illustration and bears no inference; what is tested is the auxiliary "
        "claim that the body is the source of the arm's place, with the region fixed from outside the chairs "
        "(1.324, 3.11). A failure revises that auxiliary claim, no proposition. The wording is 'the arm sits at "
        "elbow height and does not follow the size of the chair', NOT 'the arm is regulated relative to the "
        "seat': the primary criterion cannot tell an arm held to the seat from an arm at a constant height "
        "above the floor (synthetic control d passes it). That question is the headline secondary reading."),
    "utval": (
        "Held-out adult chairs (felles.les('held')) with type == 'Armstol' or 'arm' in the lower-cased catalogue "
        "name; felles.kvalitet() passes (drops copied dimension records); sete_mesh exists; the detector finds "
        "an arm, 8.0 <= T1 - sete_mesh <= 45.0. Catalogue count before the mesh conditions: 330 (V&A 322, "
        "Nasjonalmuseet 8), of which 6 carry a copied dimension record; 324 remain in 302 suites, 40 with a "
        "catalogue seat height; periods 53 / 120 / 76 / 74, 1 undated. With the DEV pass rate (36 of 46) about "
        "250 are expected in the analysis and about 30 with a catalogue seat height. [independent check] The "
        "name rule adds exactly one held-out chair that is not of type 'Armstol': 'Chair (Russian Imperial "
        "Arms Factory, Tula)', matched on the 'arm' in 'Arms'. The rule is left as frozen; if that chair has "
        "no arms the detector drops it as 'no arm in the zone'."),
    "primaer": [
        {"namn": "median_A",
         "statistikk": "median of A = T1 - sete_mesh over the analysed held-out armchairs (point estimate; "
                       "cluster-bootstrap 95 % interval reported beside it)",
         "terskel": [20.0, 25.0],
         "retning": "the median must lie inside the closed interval",
         "regel_for_terskel": "Pheasant (1996) Bodyspace 2nd ed., section 4.3.7: elbow rest 200-250 mm above "
                              "the seat surface. Fixed from the source, not from DEV.",
         "dev_verdi": "22.5, 95 % interval [20.0, 24.0], n = 36 (36 suites)"},
        {"namn": "helling_A_paa_rygg",
         "statistikk": "Theil-Sen slope (median of all pairwise slopes) of A on back height H - sete_mesh; "
                       "the upper end of the cluster-bootstrap 95 % percentile interval (97.5th percentile)",
         "terskel": 0.20,
         "retning": "the upper bound must be below 0.20",
         "regel_for_terskel": "The inference reviewer's rule: about half of what an arm proportional to the "
                              "back predicts. Recomputed on DEV: median of A / (H - seat) = 0.359 with the "
                              "mesh seat and 0.361 with the catalogue seat (the designers' 'about 0.39'); "
                              "an arm at a fixed share of H predicts more (DEV median T1 / H = 0.6236; the "
                              "synthetic controls a1-a3 give slopes of 0.44 to 0.67). The estimator "
                              "(Theil-Sen, not least squares) was fixed before this module computed a DEV "
                              "slope, because single bad meshes give outliers; least squares is a secondary "
                              "line (DEV 0.065).",
         "dev_verdi": "slope 0.057, 95 % interval [-0.056, 0.196], n = 36 (36 suites): the upper bound is just "
                      "below 0.20 on DEV; at the expected held-out n (about 250) the interval is about 0.4 "
                      "times as wide"},
    ],
    "sekundaer": [
        "HEADLINE (no verdict, reported as the main reading whichever way it falls): three-way comparison with "
        "coefficients frozen from DEV. BODY: arm top = seat + c (c = 22.5 with sete_mesh, 23.25 with the "
        "catalogue seat). TABLE: arm top = 67.5 cm above the floor. SIZE: arm top = 0.6236 * H. Held-out mean "
        "absolute error of each on all analysed armchairs (seat = sete_mesh) and on those with a catalogue seat "
        "height (seat = catalogue seat, about 30 chairs). Reading rule fixed now: one model 'wins' over another "
        "only if the cluster-bootstrap 95 % interval of the paired difference in mean absolute error excludes "
        "0; otherwise 'uavgjort' (undecided). 'Constant from the floor wins' would speak AGAINST 'held to the "
        "seat' and FOR a setpoint stored in the table (props 3.401, 1.021); it is reported as such. Caveat "
        "written in advance: with sete_mesh the arm and the seat come from one mesh and the detector window "
        "8-45 cm bounds the body model's error but not the others', so the all-chairs comparison leans towards "
        "BODY; the catalogue-seat comparison shares only the window. DEV (in-sample, n = 36): mean absolute "
        "error body 4.07, table 5.01, size 8.09 cm; MEDIAN absolute error body 4.00, table 2.75, size 7.26.",
        "Var(arm - seat) against Var(arm above floor), seat-noise variance subtracted from the first: "
        "R = (Var(A) - noise) / Var(T1), classical (noise 1.37 cm^2) and robust (squared MAD-SD, noise "
        "1.10 cm^2), both from the 63 DEV suite pairs (the untrimmed classical estimate, 11.25 cm^2, is stated "
        "and not used). Reading rule: 'seat tighter' if both 95 % intervals lie below 1, 'floor tighter' if "
        "both lie above 1, else undecided. DEV: classical 0.56, robust 2.05, i.e. the two disagree on DEV (the "
        "arm above the floor has a tight core, MAD-SD 4.1 cm, and long tails, SD 6.7 cm). In the synthetic "
        "controls this line came out undecided under both the body truth and the table truth: at this "
        "sample size it has little power, and it is reported as such.",
        "Theil-Sen slope of arm top (T1) on CATALOGUE seat height with interval: body predicts 1, table "
        "predicts 0; undecided unless the interval excludes one of them. DEV 0.83.",
        "Period medians of A in four periods (before 1700, 1700-1799, 1800-1899, 1900 on) against the period "
        "medians of back height for the same chairs, and the ratio of their ranges. DEV: A 23.0 / 22.0 / 27.0 / "
        "20.0 (n 11 / 12 / 4 / 8), back 76.0 / 58.2 / 51.1 / 40.9.",
        "Median A per museum; share of A inside the band; OLS slope of A on back height; Theil-Sen slope of A "
        "on catalogue H (free of the shared seat error).",
        "Other definitions, same statistics: (i) only chairs with |T2 - sete_mesh| <= 6 cm, A and T1 - T2; "
        "(ii) T1 - catalogue seat where a catalogue seat exists; (iii) zone 0.30-0.65; (iv) detector on all "
        "chairs whatever the catalogue calls them; (v) catalogue armchairs that fail the quality rule only on "
        "'djupn' or 'blokk' added back.",
        "Attrition: share of catalogue armchairs removed by the quality rule, by A < 8 and by A > 45.",
    ],
    # [independent check, 13 Nov] 'regel_for_terskel' and 'dev_verdi' added to every gate. None of the six gate
    # thresholds comes from a formula: each is a round number set by judgement between the DEV value and the
    # level at which the measurement would be unusable, and is said to be so. No number was changed.
    "port": [
        {"namn": "n_analysert", "terskel": 100, "ugyldig_dersom": "fewer than 100 analysed armchairs "
         "(the slope bound needs about that many; DEV has 36 and is therefore UGYLDIG by this gate)",
         "regel_for_terskel": "judgement: the half-width of the slope interval is 0.126 on DEV (n = 36) and "
                              "falls with 1/sqrt(n) to about 0.075 at n = 100, so a slope as on DEV (0.06) "
                              "can still give an upper bound below 0.20; much below 100 it cannot",
         "dev_verdi": 36},
        {"namn": "del_analysert", "terskel": 0.50, "ugyldig_dersom": "analysed / catalogue armchairs below 0.50 "
         "(DEV 36 / 46 = 0.78)",
         "regel_for_terskel": "judgement: at least half of the catalogue armchairs must be measured",
         "dev_verdi": 0.783},
        {"namn": "del_arm_funne", "terskel": 0.70, "ugyldig_dersom": "the detector finds an arm in fewer than "
         "0.70 of the catalogue armchairs that pass quality and have a mesh seat (DEV 36 / 38 = 0.95)",
         "regel_for_terskel": "judgement: a round number between the DEV value and one half",
         "dev_verdi": 0.947},
        {"namn": "kontroll_median_T1_minus_sete", "terskel": 3.0, "ugyldig_dersom": "on chairs NOT catalogued "
         "as armchairs (quality ok, mesh seat) the median of T1 - sete_mesh is more than 3.0 cm from 0: the "
         "zone top does not read the seat where there is no arm, so T1 and sete_mesh do not share a datum "
         "(DEV +1.0, n = 174)",
         "regel_for_terskel": "judgement: three times the DEV offset",
         "dev_verdi": 1.0},
        {"namn": "kontroll_del_arm", "terskel": 0.25, "ugyldig_dersom": "the detector reports an arm in more "
         "than 0.25 of the chairs not catalogued as armchairs (DEV 20 / 174 = 0.115, of which 15 have arms)",
         "regel_for_terskel": "judgement: about twice the DEV value",
         "dev_verdi": 0.115},
        {"namn": "rygg_iqr", "terskel": 10.0, "ugyldig_dersom": "interquartile range of back height among the "
         "analysed armchairs below 10 cm: no spread to estimate a slope on (DEV 25.2)",
         "regel_for_terskel": "judgement: less than half of the DEV spread. Catalogue H alone (no mesh) has "
                              "an interquartile range of 23.8 cm among the DEV and 20.4 cm among the held-out "
                              "catalogue armchairs",
         "dev_verdi": 25.25},
    ],
    # [independent check, 13 Nov] the known biases and the photograph audit, stated inside SPEC as well
    "kjende_skeivskapar": [
        "UNLOADED SEAT, pulls the median of A DOWN against Pheasant's rule: the rule is above the seat as sat "
        "upon, the mesh gives the unloaded surface; a soft seat sinks 2-4 cm (unverified figure).",
        "MESH SEAT AGAINST CATALOGUE SEAT, pulls the median of A DOWN by about 0.75 cm on DEV: median A is 22.5 "
        "with sete_mesh and 23.25 with the catalogue seat (same 36 chairs).",
        "DATUM, pushes A UP by 0.4-1 cm: T1 is the upper edge of the top pixel, sete_mesh the lower edge of "
        "the top 1-cm bin of the seat surface. On DEV chairs without arms T1 - sete_mesh is 0 in 37 % and 1 in "
        "44 % (median +1.0); on analysed armchairs the detector's own seat line T2 lies 0.4 cm above sete_mesh.",
        "ZONE, pulls the median of A DOWN: the zone 0.50-0.85 is the front half of the arm. Arms that sweep "
        "down to the front, arms that rise towards the back, and padded arms whose support dips in front of "
        "the pad are read below the height at the elbow (photograph audit: up to 6 cm), and armchairs whose "
        "arm ends behind the zone or reaches the seat inside it are dropped as 'no arm' (2 of 38 on DEV).",
        "SHARED SEAT ERROR, pushes the slope UP (towards SLO FEIL): A and back height carry the same seat "
        "error with the same sign; about +0.02 to +0.10 on DEV.",
        "ZONE AND PERIOD, may pull the slope DOWN (towards HELDT), size unknown: tall-backed chairs before "
        "1700 often have arms that rise towards the back, so reading the front half understates their arm "
        "height at the elbow more than it does on low chairs. In the photograph audit the detector's error "
        "in A had a Theil-Sen slope of -0.03 on back height (18 chairs, not distinguishable from 0).",
    ],
    "augnemaal_mot_foto": (
        "Independent check, 13 Nov 2026: 20 DEV catalogue armchairs that reach the detector (seeded sample, "
        "seed 20261113, all V&A), arm top and seat top read by eye from the museum photograph on a ruled copy "
        "and converted with catalogue H and a two-plane perspective correction. Precision of a reading about "
        "3 cm; the reader had seen the detector table earlier, so the audit is not strictly blind; the seat "
        "readings lean on the catalogue seat for the scale of the front plane. Result: 18 of the 20 are "
        "analysed by the detector; for these, detector A minus photograph A has median -0.75 cm, mean -1.3 cm, "
        "median absolute difference 1.25 cm, 14 of 18 within 3 cm, worst -6.0 cm (O129655, padded arm read on "
        "the support in front of the pad); arm top alone: detector 2.0 cm lower (median); correlation between "
        "photograph A and detector A 0.91; median A 22.25 (photograph) against 22.0 (detector). The other 2 "
        "(O56348, O63266) have arms in the photograph, at about 21 and 19 cm above the seat at the elbow, and "
        "are dropped by the detector as 'no arm in the zone'."),
    "grunnmodell": (
        "SIZE FACTOR: the arm is a fixed share of the chair. As a share of total height (arm top = 0.6236 * H) "
        "it predicts a slope of A on back height of 0.4 to 0.7 and a median A outside the band for tall and for "
        "low chairs; as a share of the back (A = 0.36 * (H - seat)) it predicts a slope near 0.36. Either gives an "
        "upper bound far above 0.20, so criterion 2 fails. Criterion 1 is the weaker half and this is said in "
        "advance: the level was known on DEV (22.5) when the test was written, a size model whose coefficient is "
        "fitted to armchairs reproduces any level, and so criterion 1 on the held-out chairs is a replication "
        "of the DEV level against a band fixed from the source. The detector window 8-45 does not by itself put "
        "the median in the band (its midpoint is 26.5; synthetic control a1 gives 16). The base model wins or "
        "loses on criterion 2. Synthetic controls a1-a3 plant it; all must come out not HELDT."),
    "tel_imot": (
        "A median of A outside [20.0, 25.0] cm; or an upper bound of the slope of A on back height at or above "
        "0.20. Either gives SLO FEIL. Not counted for the verdict but written down in advance as speaking "
        "against 'held to the seat': the table model beating the body model in the three-way comparison, and a "
        "slope of arm top on catalogue seat height whose interval includes 0 and excludes 1."),
}


# ============================================================================ instrument
def er_katalogarm(rec):
    """Catalogue definition of an armchair (catalogue only): type 'Armstol' or 'arm' in the name."""
    return rec["type"] == "Armstol" or "arm" in (rec["namn"] or "").lower()


def _renn(col):
    """(bottom, top) of the filled runs of one column, bottom-up."""
    c = np.concatenate([[0], col.astype(np.int8), [0]])
    d = np.diff(c)
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0] - 1))


def sidemaal(side, sone=SONE, mingap=MINGAP):
    """The designer's side_measures (scratch kropp/inst.py), unchanged in substance.
    -> dict c0, D, T1, T2 (NaN when at most half of the zone columns have a second run), or None."""
    side = np.asarray(side) > 0
    cols = np.where(side.any(axis=0))[0]
    rows = np.where(side.any(axis=1))[0]
    if len(cols) < 10 or len(rows) < 10:
        return None
    c0, c1 = int(cols[0]), int(cols[-1])
    D = c1 - c0 + 1
    T1, T2 = [], []
    for x in range(int(round(c0 + sone[0] * D)), int(round(c0 + sone[1] * D)) + 1):
        if x < 0 or x >= side.shape[1]:
            continue
        mr = []
        for b, t in _renn(side[:, x]):
            if mr and b - mr[-1][1] - 1 < mingap:
                mr[-1] = (mr[-1][0], t)
            else:
                mr.append((b, t))
        if not mr:
            continue
        T1.append(mr[-1][1] + 1)
        T2.append(mr[-2][1] + 1 if len(mr) > 1 else np.nan)
    if not T1:
        return None
    T1, T2 = np.asarray(T1, float), np.asarray(T2, float)
    har2 = np.isfinite(T2)
    return {"c0": c0, "D": D, "T1": float(np.median(T1)),
            "T2": float(np.median(T2[har2])) if har2.mean() > 0.5 else float("nan")}


_LETT = frozenset({"djupn", "blokk"})      # quality reasons added back in secondary line (v)


def maal_stol(rec, side, front):
    """One chair -> row dict (always returned; 'steg' says how far the chair got):
    'ingen_mesh' | 'kvalitet' | 'utan_sete' | 'utan_sidemaal' | 'A<8' | 'A>45' | 'ok'."""
    rad = {"id": rec["id"], "suite": rec["suite"], "museum": rec["museum"], "aar": rec["aar"],
           "H": rec["H"], "sete_mesh": rec["sete_mesh"], "sete_kat": rec["sete_kat"],
           "katalogarm": er_katalogarm(rec), "T1": None, "T2": None, "T1_d": None, "A": None,
           "kval": "ingen_mesh", "kval_lett": False}
    if side is None or front is None:
        rad["steg"] = "ingen_mesh"
        return rad
    ok, grunn = felles.kvalitet(rec, side, front)
    rad["kval"] = grunn
    rad["kval_lett"] = ok or set(grunn.split(";")) <= _LETT
    m = sidemaal(side) if (ok or rad["kval_lett"]) else None
    if m is not None:
        rad["T1"], rad["T2"] = m["T1"], (m["T2"] if np.isfinite(m["T2"]) else None)
        md = sidemaal(side, SONE_ALBOGE)
        rad["T1_d"] = md["T1"] if md else None
        if rec["sete_mesh"] is not None:
            rad["A"] = m["T1"] - rec["sete_mesh"]
    if not ok:
        rad["steg"] = "ingen_mesh" if grunn == "ingen_mesh" else "kvalitet"
    elif rec["sete_mesh"] is None:
        rad["steg"] = "utan_sete"
    elif m is None:
        rad["steg"] = "utan_sidemaal"
    elif rad["A"] < ARM_MIN:
        rad["steg"] = "A<8"
    elif rad["A"] > ARM_MAX:
        rad["steg"] = "A>45"
    else:
        rad["steg"] = "ok"
    return rad


def tabell(recs, sil):
    """All chairs of a sample -> list of row dicts (maal_stol)."""
    return [maal_stol(r, *sil.get(r["id"], (None, None))) for r in recs]


# ============================================================================ statistics
def _med(x):
    x = np.asarray(x, float)
    return float(np.median(x)) if len(x) else float("nan")


def theil_sen(x, y):
    """Median of all pairwise slopes (pairs with equal x are left out). NaN if fewer than 3 points or no pair."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3:
        return float("nan")
    i, j = np.triu_indices(len(x), 1)
    dx = x[j] - x[i]
    k = dx != 0
    if not k.any():
        return float("nan")
    return float(np.median((y[j] - y[i])[k] / dx[k]))


def ols_helling(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or np.var(x) == 0:
        return float("nan")
    return float(np.cov(x, y)[0, 1] / np.var(x, ddof=1))


def _mad_var(x):
    return felles.mad_sd(x) ** 2 if len(x) else float("nan")


def _periode(aar):
    if aar is None:
        return None
    for k, (_, lo, hi) in enumerate(PERIODAR):
        if (lo is None or aar >= lo) and (hi is None or aar < hi):
            return k
    return None


def _kol(rader, namn):
    return np.asarray([np.nan if r[namn] is None else r[namn] for r in rader], float)


def _matrise(rader):
    """Rows -> dict of numpy columns (NaN for missing), so that a bootstrap resample is an index vector."""
    m = {k: _kol(rader, k) for k in ("T1", "T2", "T1_d", "A", "H", "sete_mesh", "sete_kat")}
    m["per"] = np.asarray([-1 if _periode(r["aar"]) is None else _periode(r["aar"]) for r in rader], int)
    m["nm"] = np.asarray([r["museum"] == "NM" for r in rader], bool)
    return m


def _boot(rader, fn, n_boot, k):
    """(point estimate, bootstrap array) of fn(matrix, index vector) -> vector of length k.
    Cluster bootstrap over suites through felles.klyngebootstrap, seed felles.FRO."""
    if len(rader) < 3:
        return np.full(k, np.nan), np.full((n_boot, k), np.nan)
    m = _matrise(rader)
    lette = [{"suite": r["suite"], "i": i} for i, r in enumerate(rader)]
    stat = lambda rs: fn(m, np.fromiter((r["i"] for r in rs), int, len(rs)))
    return np.asarray(fn(m, np.arange(len(rader))), float), felles.klyngebootstrap(lette, stat, n=n_boot)


def _prim(m, ix):
    """The two primary statistics -> (median A, Theil-Sen slope of A on back height H - sete_mesh)."""
    if len(ix) < 3:
        return [float("nan"), float("nan")]
    A = m["A"][ix]
    return [_med(A), theil_sen(m["H"][ix] - m["sete_mesh"][ix], A)]


def _mae3(T1, sete, H, c_kropp):
    """Mean absolute errors of body, table, size, their paired differences (body-table, body-size,
    table-size), and the three median absolute errors."""
    if len(T1) == 0:
        return [float("nan")] * 9
    e = [np.abs(T1 - (sete + c_kropp)), np.abs(T1 - C_BORD), np.abs(T1 - C_STORLEIK * H)]
    mm = [float(v.mean()) for v in e]
    return mm + [mm[0] - mm[1], mm[0] - mm[2], mm[1] - mm[2]] + [float(np.median(v)) for v in e]


_MAE = ("mae_kropp", "mae_bord", "mae_storleik", "d_kropp_bord", "d_kropp_storleik", "d_bord_storleik",
        "medae_kropp", "medae_bord", "medae_storleik")
_NOKLAR = (["median_A", "ts_rygg", "ols_rygg", "ts_H", "del_i_band"]
           + ["mesh_" + k for k in _MAE] + ["kat_" + k for k in _MAE]
           + ["R_klassisk", "R_robust", "ts_T1_paa_katalogsete", "median_A_NM", "median_A_VA"]
           + ["A_p%d" % k for k in range(4)] + ["rygg_p%d" % k for k in range(4)] + ["spennforhold"]
           + ["median_A_samsvar", "median_T1_minus_T2_samsvar", "median_A_katalogsete", "median_A_sone_alboge"])


def _alle(m, ix):
    """Every statistic of the analysed armchairs, as a vector in the order of _NOKLAR."""
    ut = dict.fromkeys(_NOKLAR, float("nan"))
    if len(ix) >= 3:
        T1, s, H, A, sk = m["T1"][ix], m["sete_mesh"][ix], m["H"][ix], m["A"][ix], m["sete_kat"][ix]
        rygg = H - s
        ut["median_A"] = _med(A)
        ut["ts_rygg"] = theil_sen(rygg, A)
        ut["ols_rygg"] = ols_helling(rygg, A)
        ut["ts_H"] = theil_sen(H, A)
        ut["del_i_band"] = float(((A >= BAND[0]) & (A <= BAND[1])).mean())
        for k, v in zip(_MAE, _mae3(T1, s, H, C_KROPP_MESH)):
            ut["mesh_" + k] = v
        kat = np.isfinite(sk)
        if kat.sum() >= 3:
            for k, v in zip(_MAE, _mae3(T1[kat], sk[kat], H[kat], C_KROPP_KAT)):
                ut["kat_" + k] = v
            ut["ts_T1_paa_katalogsete"] = theil_sen(sk[kat], T1[kat])
            ut["median_A_katalogsete"] = _med(T1[kat] - sk[kat])
        vT = float(np.var(T1, ddof=1))
        if vT > 0:
            ut["R_klassisk"] = (float(np.var(A, ddof=1)) - SETESTOY_VAR_KLASSISK) / vT
        vTr = _mad_var(T1)
        if vTr > 0:
            ut["R_robust"] = (_mad_var(A) - SETESTOY_VAR_ROBUST) / vTr
        nm = m["nm"][ix]
        if nm.any():
            ut["median_A_NM"] = _med(A[nm])
        if (~nm).any():
            ut["median_A_VA"] = _med(A[~nm])
        per = m["per"][ix]
        mA, mR = [], []
        for k in range(4):
            if (per == k).any():
                ut["A_p%d" % k], ut["rygg_p%d" % k] = _med(A[per == k]), _med(rygg[per == k])
                mA.append(ut["A_p%d" % k])
                mR.append(ut["rygg_p%d" % k])
        if len(mA) == 4 and max(mR) > min(mR):
            ut["spennforhold"] = (max(mA) - min(mA)) / (max(mR) - min(mR))
        T2 = m["T2"][ix]
        sam = np.isfinite(T2) & (np.abs(np.nan_to_num(T2, nan=1e9) - s) <= SAMSVAR_CM)
        if sam.any():
            ut["median_A_samsvar"] = _med(A[sam])
            ut["median_T1_minus_T2_samsvar"] = _med((T1 - T2)[sam])
        d = m["T1_d"][ix] - s
        d = d[np.isfinite(d)]
        d = d[(d >= ARM_MIN) & (d <= ARM_MAX)]
        if len(d):
            ut["median_A_sone_alboge"] = _med(d)
    return [ut[k] for k in _NOKLAR]


def _r(v, d=3):
    """Round for JSON; NaN / None -> None."""
    if v is None:
        return None
    v = float(v)
    return round(v, d) if v == v else None


def _ki(boot_col):
    lo, hi = felles.ki(boot_col)
    return [_r(lo), _r(hi)]


# ============================================================================ scoring (one code path for all)
def skaar(rader, n_boot=felles.N_BOOT, full=True):
    """rader: tabell() of a whole sample (armchairs and others). -> result dict with gates, primary criteria,
    secondary lines and the verdict. The same function scores DEV, the held-out sample and every synthetic
    population. full=False computes the gates and the primary only (used for repeated synthetic draws)."""
    from collections import Counter
    kat = [r for r in rader if r["katalogarm"]]
    arm = [r for r in kat if r["steg"] == "ok"]
    andre = [r for r in rader if not r["katalogarm"] and r["steg"] in ("ok", "A<8", "A>45")]
    steg = Counter(r["steg"] for r in kat)
    grunnar = Counter(g for r in kat if r["steg"] == "kvalitet" for g in r["kval"].split(";"))
    n_kval_sete = steg["ok"] + steg["A<8"] + steg["A>45"]
    fraafall = {
        "katalogarmstolar": len(kat),
        "utan_mesh_eller_silhuett": steg["ingen_mesh"],
        "fell_paa_kvalitetsregelen": steg["kvalitet"],
        "kvalitetsgrunnar (ein stol kan ha fleire)": dict(grunnar.most_common()),
        "utan_sete_mesh": steg["utan_sete"], "utan_sidemaal": steg["utan_sidemaal"],
        "A_under_8 (ingen arm i sona)": steg["A<8"], "A_over_45": steg["A>45"],
        "analysert": len(arm),
        "del_fjerna_av_kvalitet": _r(steg["kvalitet"] / len(kat)) if kat else None,
        "del_fjerna_av_A_under_8": _r(steg["A<8"] / n_kval_sete) if n_kval_sete else None,
        "del_fjerna_av_A_over_45": _r(steg["A>45"] / n_kval_sete) if n_kval_sete else None,
        "analysert_per_museum": dict(Counter(r["museum"] for r in arm)),
        "analysert_suitar": len({r["suite"] for r in arm}),
        "analysert_med_katalogsete": sum(r["sete_kat"] is not None for r in arm),
    }

    # ---- gates
    k_d = np.asarray([r["A"] for r in andre], float)
    rygg = _kol(arm, "H") - _kol(arm, "sete_mesh") if arm else np.asarray([])
    iqr = float(np.subtract(*np.percentile(rygg, [75, 25]))) if len(rygg) else float("nan")
    v = {
        "n_analysert": len(arm),
        "del_analysert": len(arm) / len(kat) if kat else float("nan"),
        "del_arm_funne": len(arm) / n_kval_sete if n_kval_sete else float("nan"),
        "kontroll_median_T1_minus_sete": _med(k_d),
        "kontroll_del_arm": float(((k_d >= ARM_MIN) & (k_d <= ARM_MAX)).mean()) if len(k_d) else float("nan"),
        "rygg_iqr": iqr,
    }
    port = [
        {"namn": "n_analysert", "verdi": v["n_analysert"], "terskel": PORT_N_MIN,
         "ok": bool(v["n_analysert"] >= PORT_N_MIN)},
        {"namn": "del_analysert", "verdi": _r(v["del_analysert"]), "terskel": PORT_DEL_ANALYSERT_MIN,
         "ok": bool(v["del_analysert"] >= PORT_DEL_ANALYSERT_MIN)},
        {"namn": "del_arm_funne", "verdi": _r(v["del_arm_funne"]), "terskel": PORT_DEL_FUNNE_MIN,
         "ok": bool(v["del_arm_funne"] >= PORT_DEL_FUNNE_MIN)},
        {"namn": "kontroll_median_T1_minus_sete", "verdi": _r(v["kontroll_median_T1_minus_sete"]),
         "terskel": PORT_KONTROLL_ABS_MAX, "n": len(k_d),
         "ok": bool(abs(v["kontroll_median_T1_minus_sete"]) <= PORT_KONTROLL_ABS_MAX)},
        {"namn": "kontroll_del_arm", "verdi": _r(v["kontroll_del_arm"]), "terskel": PORT_KONTROLL_DEL_MAX,
         "n": len(k_d), "ok": bool(v["kontroll_del_arm"] <= PORT_KONTROLL_DEL_MAX)},
        {"namn": "rygg_iqr", "verdi": _r(v["rygg_iqr"]), "terskel": PORT_RYGG_IQR_MIN,
         "ok": bool(v["rygg_iqr"] >= PORT_RYGG_IQR_MIN)},
    ]
    port_ok = all(p["ok"] for p in port)

    # ---- primary
    if full:
        pv, boot = _boot(arm, _alle, n_boot, len(_NOKLAR))
        punkt = dict(zip(_NOKLAR, pv))
        b = {k: boot[:, j] for j, k in enumerate(_NOKLAR)}
    else:
        pv, boot = _boot(arm, _prim, n_boot, 2)
        punkt = {"median_A": pv[0], "ts_rygg": pv[1]}
        b = {"median_A": boot[:, 0], "ts_rygg": boot[:, 1]}
    ki_med, ki_h = _ki(b["median_A"]), _ki(b["ts_rygg"])
    held1 = bool(punkt["median_A"] == punkt["median_A"] and BAND[0] <= punkt["median_A"] <= BAND[1])
    # [independent check, 13 Nov] criterion 2 is decided on the UNROUNDED upper bound. Before, the bound was
    # rounded to three decimals first, so that a bound in [0.1995, 0.2000) was shown as 0.2 and failed although
    # it is below 0.20. The printed ki95 stays rounded; 'ovre_grense_uavrunda' gives the deciding number.
    ovre = felles.ki(b["ts_rygg"])[1]
    held2 = bool(ovre == ovre and ovre < HELLING_TAK)
    primaer = [
        {"namn": "median_A", "verdi": _r(punkt["median_A"]), "ki95": ki_med, "terskel": list(BAND),
         "held": held1},
        {"namn": "helling_A_paa_rygg", "verdi": _r(punkt["ts_rygg"]), "ki95": ki_h,
         "avgjerande_tal": "ovre grense " + str(ki_h[1]), "ovre_grense_uavrunda": _r(ovre, 6),
         "terskel": HELLING_TAK, "held": held2},
    ]
    dom = "UGYLDIG" if not port_ok else ("HELDT" if (held1 and held2) else "SLO FEIL")
    ut = {"n": len(arm), "fraafall": fraafall, "port": port, "primaer": primaer,
          "primaer_konjunksjon_held": bool(held1 and held2), "dom": dom}
    if not full:
        return ut

    # ---- secondary lines (no verdict)
    def linje(k, d=3):
        return {"verdi": _r(punkt[k], d), "ki95": _ki(b[k])}

    def vinnar(dk, a, bb):
        lo, hi = felles.ki(b[dk])
        if not (lo == lo and hi == hi):
            return "ikkje utrekna"
        return a if hi < 0 else (bb if lo > 0 else "uavgjort")

    def treveg(pre, n):
        return {
            "n": n,
            "mae": {m: linje(pre + "mae_" + m, 2) for m in ("kropp", "bord", "storleik")},
            "median_absolutt_feil": {m: _r(punkt[pre + "medae_" + m], 2) for m in ("kropp", "bord", "storleik")},
            "differanse_mae": {"kropp_minus_bord": linje(pre + "d_kropp_bord", 2),
                               "kropp_minus_storleik": linje(pre + "d_kropp_storleik", 2),
                               "bord_minus_storleik": linje(pre + "d_bord_storleik", 2)},
            "lesing": {"kropp_mot_bord": vinnar(pre + "d_kropp_bord", "kropp", "bord"),
                       "kropp_mot_storleik": vinnar(pre + "d_kropp_storleik", "kropp", "storleik"),
                       "bord_mot_storleik": vinnar(pre + "d_bord_storleik", "bord", "storleik")},
        }

    def side_av_1(k):
        lo, hi = felles.ki(b[k])
        if not (lo == lo and hi == hi):
            return None
        return "under" if hi < 1 else ("over" if lo > 1 else "uavgjort")

    sk, sr = side_av_1("R_klassisk"), side_av_1("R_robust")
    varlesing = ("sete tettare" if sk == sr == "under" else "golv tettare" if sk == sr == "over" else "uavgjort")
    T1 = _kol(arm, "T1") if arm else np.asarray([])
    A = _kol(arm, "A") if arm else np.asarray([])
    n_kat = fraafall["analysert_med_katalogsete"]
    lo_s, hi_s = felles.ki(b["ts_T1_paa_katalogsete"])
    if not (lo_s == lo_s):
        seteles = "ikkje utrekna"
    elif lo_s > 0 and hi_s >= 1:
        seteles = "utelukkar 0 (bord), ikkje 1 (kropp)"
    elif lo_s <= 0 and hi_s < 1:
        seteles = "utelukkar 1 (kropp), ikkje 0 (bord)"
    elif lo_s > 0 and hi_s < 1:
        seteles = "utelukkar baade 0 og 1"
    else:
        seteles = "uavgjort"
    per_tal = Counter(_periode(r["aar"]) for r in arm)
    periodar = [{"periode": PERIODAR[k][0], "n": per_tal.get(k, 0), "median_A": linje("A_p%d" % k, 2),
                 "median_rygg": linje("rygg_p%d" % k, 2)} for k in range(4)]
    mR = [punkt["rygg_p%d" % k] for k in range(4)]
    rygg_spenn = (max(mR) - min(mR)) if all(x == x for x in mR) else float("nan")

    # (iv) detector on all chairs whatever the catalogue says; (v) light quality rule
    alle_det = [r for r in rader if r["steg"] == "ok"]
    p4, b4 = _boot(alle_det, _prim, n_boot, 2)
    lett = [r for r in kat if r["kval_lett"] and r["A"] is not None and ARM_MIN <= r["A"] <= ARM_MAX]
    p5, b5 = _boot(lett, _prim, n_boot, 2)

    ut["sekundaer"] = [
        {"namn": "HOVUDLESING treveg, sete = sete_mesh, alle analyserte armstolar",
         "koeffisientar_fraa_DEV": {"kropp": C_KROPP_MESH, "bord": C_BORD, "storleik": C_STORLEIK},
         **treveg("mesh_", len(arm)),
         "atterhald": "arm and seat from one mesh, and the window 8-45 cm bounds the body model's error only"},
        {"namn": "HOVUDLESING treveg, sete = katalogsete, armstolar med katalogsete",
         "koeffisientar_fraa_DEV": {"kropp": C_KROPP_KAT, "bord": C_BORD, "storleik": C_STORLEIK},
         **treveg("kat_", n_kat)},
        {"namn": "varians arm-sete mot varians arm fraa golv, setestoey trekt fraa",
         "var_A": _r(np.var(A, ddof=1), 2) if len(A) > 1 else None,
         "var_T1": _r(np.var(T1, ddof=1), 2) if len(T1) > 1 else None,
         "madsd_A": _r(felles.mad_sd(A), 2) if len(A) else None,
         "madsd_T1": _r(felles.mad_sd(T1), 2) if len(T1) else None,
         "setestoey_var": {"klassisk": SETESTOY_VAR_KLASSISK, "robust": SETESTOY_VAR_ROBUST},
         "R_klassisk": linje("R_klassisk"), "R_robust": linje("R_robust"), "lesing": varlesing},
        {"namn": "Theil-Sen-helling av armtopp (T1) paa katalogsete (kropp 1, bord 0)", "n": n_kat,
         **linje("ts_T1_paa_katalogsete"), "lesing": seteles},
        {"namn": "periodemedianar av A mot periodemedianar av rygghoegd", "periodar": periodar,
         "spenn_A_over_spenn_rygg": linje("spennforhold"),
         "spenn_rygg_cm": _r(rygg_spenn, 2),
         "positiv_kontroll_ryggspenn_minst_15": bool(rygg_spenn >= 15) if rygg_spenn == rygg_spenn else None},
        {"namn": "median A per museum", "NM": {"n": sum(r["museum"] == "NM" for r in arm), **linje("median_A_NM", 2)},
         "VA": {"n": sum(r["museum"] == "VA" for r in arm), **linje("median_A_VA", 2)}},
        {"namn": "fordeling av A", "del_i_band": linje("del_i_band"),
         "kvartilar": [_r(x, 2) for x in np.percentile(A, [25, 75])] if len(A) else None,
         "madsd": _r(felles.mad_sd(A), 2) if len(A) else None,
         "median_armtopp_fraa_golv": _r(_med(T1), 2)},
        {"namn": "andre hellingar", "ols_A_paa_rygg": linje("ols_rygg"), "theil_sen_A_paa_katalog_H": linje("ts_H")},
        {"namn": "andre definisjonar",
         "(i) samsvar |T2 - sete_mesh| <= 6": {
             "n": sum(1 for r in arm if r["T2"] is not None and abs(r["T2"] - r["sete_mesh"]) <= SAMSVAR_CM),
             "median_A": linje("median_A_samsvar", 2), "median_T1_minus_T2": linje("median_T1_minus_T2_samsvar", 2)},
         "(ii) T1 - katalogsete": {"n": n_kat, "median": linje("median_A_katalogsete", 2)},
         "(iii) sone 0.30-0.65": {"median_A": linje("median_A_sone_alboge", 2)},
         "(iv) detektor paa alle stolar": {"n": len(alle_det),
                                           "per_museum": dict(Counter(r["museum"] for r in alle_det)),
                                           "median_A": {"verdi": _r(p4[0], 2), "ki95": _ki(b4[:, 0])},
                                           "helling": {"verdi": _r(p4[1]), "ki95": _ki(b4[:, 1])}},
         "(v) lett kvalitetsregel (djupn og blokk attende)": {"n": len(lett),
                                                              "median_A": {"verdi": _r(p5[0], 2), "ki95": _ki(b5[:, 0])},
                                                              "helling": {"verdi": _r(p5[1]), "ki95": _ki(b5[:, 1])}}},
    ]
    return ut


# ============================================================================ public functions
def _les(utval):
    """Records and silhouettes of a sample. 'held' goes through the guarded loader and nowhere else."""
    if utval not in ("dev", "held"):
        raise ValueError("utval må vere 'dev' eller 'held'")
    return felles.les(utval), felles.silhuett(utval)


def kjoer(utval):
    """Score the sample. -> {id, utval, n, fraafall, port, primaer, sekundaer, dom}."""
    recs, sil = _les(utval)
    res = skaar(tabell(recs, sil))
    return {"id": SPEC["id"], "utval": utval, **res}


def figurdata(utval):
    """What one figure needs (under 300 KB as compact JSON): per-armchair points (seat, arm top, H, year), the
    mean front and side silhouettes of the analysed armchairs aligned at the floor, the side silhouettes
    stacked with the seat on one row (the designer's figure), and the three mean absolute errors.
    Maps: percent of armchairs filled, 1 cm cells, rows 0-134 from the floor, canvas columns 30-129."""
    recs, sil = _les(utval)
    rader = tabell(recs, sil)
    arm = [r for r in rader if r["katalogarm"] and r["steg"] == "ok"]
    punkt = [[r["id"], r["museum"], r["aar"], r["H"], r["sete_mesh"], r["sete_kat"], r["T1"]] for r in arm]
    R0, K0, K1 = 135, 30, 130
    if arm:
        front = np.mean([sil[r["id"]][1][:R0, K0:K1] for r in arm], axis=0)
        side = np.mean([sil[r["id"]][0][:R0, K0:K1] for r in arm], axis=0)
        just = np.zeros((R0, K1 - K0))
        for r in arm:
            s = sil[r["id"]][0].astype(float)
            d = 60 - int(round(r["sete_mesh"]))
            flytt = np.zeros_like(s)
            if d >= 0:
                flytt[d:] = s[:s.shape[0] - d]
            else:
                flytt[:d] = s[-d:]
            just += flytt[:R0, K0:K1]
        just /= len(arm)
        mm = _mae3(_kol(arm, "T1"), _kol(arm, "sete_mesh"), _kol(arm, "H"), C_KROPP_MESH)
    else:
        front = side = just = np.zeros((R0, K1 - K0))
        mm = [float("nan")] * 9
    pst = lambda a: np.rint(100 * a).astype(int).tolist()
    return {"id": SPEC["id"], "utval": utval, "n": len(arm), "band": list(BAND),
            "koeffisientar": {"kropp": C_KROPP_MESH, "bord": C_BORD, "storleik": C_STORLEIK},
            "modellar": "feil = armtopp - (sete_mesh + kropp) | armtopp - bord | armtopp - storleik * H",
            "mae": {"kropp": _r(mm[0], 2), "bord": _r(mm[1], 2), "storleik": _r(mm[2], 2)},
            "median_absolutt_feil": {"kropp": _r(mm[6], 2), "bord": _r(mm[7], 2), "storleik": _r(mm[8], 2)},
            "punkt_kolonnar": ["id", "museum", "aar", "H", "sete_mesh", "sete_kat", "armtopp"],
            "punkt": punkt,
            "silhuett_forklaring": "percent of armchairs filled; row 0 = floor; 1 cm cells; canvas columns "
                                   "30-129; in 'side_sete_paa_rad_60' every chair is shifted so that its "
                                   "sete_mesh lies on row 60 (the band 20-25 cm is then rows 80-85)",
            "middel_front": pst(front), "middel_side": pst(side), "side_sete_paa_rad_60": pst(just)}


# ============================================================================ synthetic controls
SYN_STOY_SD = 5.0     # cm; DEV SD of A among analysed armchairs is 5.14 (it includes seat error)
SYN_NIVAA = 23.0      # cm above the seat: the planted level
SYN_REPETISJONAR = 40
SYN_BOOT_REP = 300


def _plant(side, h, c0, D):
    """Paint an armrest into a side silhouette: a bar 3 cm thick whose top is at height h (cm above the floor),
    from 0.10 to 0.90 of the depth extent."""
    s = np.array(side, copy=True)
    h = int(min(max(h, 3), s.shape[0] - 1))
    s[h - 3:h, c0 + int(round(0.10 * D)):c0 + int(round(0.90 * D)) + 1] = 1
    return s


def _syn_grunnlag():
    """DEV chairs that are NOT catalogued as armchairs, pass quality, have a mesh and a catalogue seat and in
    which the detector finds NO arm: the clean armless chairs. -> (records, silhouettes, all DEV rows)."""
    recs, sil = _les("dev")
    rader = tabell(recs, sil)
    reine = {r["id"] for r in rader if not r["katalogarm"] and r["steg"] == "A<8" and r["sete_kat"] is not None}
    return [r for r in recs if r["id"] in reine], sil, rader


def _syn_hoegder(slag, recs, rng):
    """Planted arm-top heights (cm above the floor) for one synthetic population. The true seat is the
    CATALOGUE seat; the scoring then uses sete_mesh, so the real mesh-against-catalogue error is in."""
    H = np.asarray([r["H"] for r in recs], float)
    s = np.asarray([r["sete_kat"] for r in recs], float)
    e = rng.normal(0.0, SYN_STOY_SD, len(recs))
    if slag == "a1":      # size, coefficient frozen from the DEV armchairs
        return C_STORLEIK * H + e, {"modell": "armtopp = 0.6236 * H + stoey"}
    if slag == "a2":      # size, coefficient tuned so that the LEVEL is right (criterion 1 holds by construction)
        c = float(np.median((s + SYN_NIVAA) / H))
        return c * H + e, {"modell": "armtopp = c * H + stoey", "c": round(c, 4)}
    if slag == "a3":      # share of the back, tuned to the same level
        f = float(np.median(SYN_NIVAA / (H - s)))
        return s + f * (H - s) + e, {"modell": "armtopp = sete + f * (H - sete) + stoey", "f": round(f, 4)}
    if slag == "b":       # the effect: seat + 23 cm
        return s + SYN_NIVAA + e, {"modell": "armtopp = katalogsete + 23.0 + stoey"}
    if slag == "d":       # table: constant height above the floor, level right on average
        c = float(np.median(s)) + SYN_NIVAA
        return np.full(len(recs), c) + e, {"modell": "armtopp = c + stoey (fast hoegd fraa golvet)", "c": round(c, 2)}
    raise ValueError(slag)


def _syn_rader(slag, recs, sil, andre, seed):
    rng = np.random.default_rng(seed)
    h, info = _syn_hoegder(slag, recs, rng)
    rader = []
    for r, hh in zip(recs, h):
        side, front = sil[r["id"]]
        m = sidemaal(side)
        rad = maal_stol(r, _plant(side, int(round(hh)), m["c0"], m["D"]), front)
        rad["katalogarm"] = True          # in the synthetic population every chair is an 'armchair'
        rader.append(rad)
    return rader + andre, info


def syntetisk_kontroll():
    """The same scoring code (skaar) on synthetic populations built from DEV.
    Population: the 154 clean armless DEV chairs (see _syn_grunnlag); an armrest is PAINTED INTO THE SIDE
    SILHOUETTE of each at a height given by the model, and the chair then goes through the whole pipeline
    (quality rule, detector, window, gates, bootstrap). The unchanged DEV chairs not catalogued as armchairs
    serve as the control group of the gates. Noise: normal, SD 5.0 cm.
      a1  base model: arm top = 0.6236 * H (coefficient of the DEV armchairs)        must NOT be HELDT
      a2  base model: arm top = c * H, c tuned so that the median of A is 23          must NOT be HELDT
      a3  base model: arm = seat + f * (H - seat), f tuned to the same level          must NOT be HELDT
      b   effect:     arm top = catalogue seat + 23.0                                 must be HELDT
      d   table:      arm top = constant above the floor, level 23 above the median seat
                      (NOT a base model of the primary: the primary cannot reject it, and says so)
      c   detector on the real DEV chairs of type 'Stol' that are not catalogued as armchairs
    Each of a1-d: one full scoring (2000 resamples, seed FRO) and 40 further draws scored with 300 resamples
    (gates and primary only), to give the frequency of each verdict."""
    from collections import Counter
    recs, sil, dev_rader = _syn_grunnlag()
    andre = [r for r in dev_rader if not r["katalogarm"]]
    ut = {"populasjon": {"n": len(recs), "kva": "DEV chairs not catalogued as armchairs, quality ok, detector "
                                                 "finds no arm, catalogue seat present; arm painted into the "
                                                 "side silhouette",
                         "stoey_sd_cm": SYN_STOY_SD, "nivaa_cm": SYN_NIVAA},
          "scenario": {}}
    krav = {"a1": "ikkje HELDT", "a2": "ikkje HELDT", "a3": "ikkje HELDT", "b": "HELDT", "d": "(ingen krav)"}
    for slag in ("a1", "a2", "a3", "b", "d"):
        rader, info = _syn_rader(slag, recs, sil, andre, felles.FRO)
        res = skaar(rader)
        rep, rep_port = Counter(), Counter()
        for k in range(SYN_REPETISJONAR):
            rr, _ = _syn_rader(slag, recs, sil, andre, felles.FRO + 1 + k)
            rk = skaar(rr, n_boot=SYN_BOOT_REP, full=False)
            rep[rk["dom"]] += 1
            rep_port.update(p["namn"] for p in rk["port"] if not p["ok"])
        dom = res["dom"]
        ok = (dom == "HELDT") if krav[slag] == "HELDT" else (dom != "HELDT" if slag != "d" else None)
        sek = res["sekundaer"]
        ut["scenario"][slag] = {
            **info, "krav": krav[slag], "dom": dom, "krav_oppfylt": ok,
            "n": res["n"], "port_ok": all(p["ok"] for p in res["port"]),
            "port_som_fall": [p["namn"] for p in res["port"] if not p["ok"]],
            "median_A": res["primaer"][0]["verdi"], "median_A_ki95": res["primaer"][0]["ki95"],
            "helling": res["primaer"][1]["verdi"], "helling_ki95": res["primaer"][1]["ki95"],
            "dom_i_%d_nye_trekk" % SYN_REPETISJONAR: dict(rep),
            "portar_som_fall_i_nye_trekk": dict(rep_port),
            "treveg_mesh_lesing": sek[0]["lesing"], "treveg_mesh_mae": {m: sek[0]["mae"][m]["verdi"] for m in sek[0]["mae"]},
            "treveg_kat_lesing": sek[1]["lesing"], "treveg_kat_mae": {m: sek[1]["mae"][m]["verdi"] for m in sek[1]["mae"]},
            "varianslesing": sek[2]["lesing"], "R_klassisk": sek[2]["R_klassisk"]["verdi"],
            "R_robust": sek[2]["R_robust"]["verdi"],
            "helling_T1_paa_katalogsete": sek[3]["verdi"], "helling_T1_paa_katalogsete_ki95": sek[3]["ki95"],
        }
    # ---- c: false positives of the detector on real armless chairs
    stol = [r for r in dev_rader if not r["katalogarm"] and r["steg"] in ("ok", "A<8", "A>45")]
    typ = {r["id"]: r["type"] for r in _les("dev")[0]}
    stol = [r for r in stol if typ[r["id"]] == "Stol"]
    funne = [r for r in stol if r["steg"] == "ok"]
    ut["scenario"]["c"] = {
        "kva": "detector on DEV chairs of type 'Stol' not catalogued as armchairs (quality ok, mesh seat)",
        "n": len(stol), "melder_arm": len(funne), "del": _r(len(funne) / len(stol)) if stol else None,
        "median_A_blant_dei": _r(_med([r["A"] for r in funne]), 2),
        "ids": sorted(r["id"] for r in funne),
        "augnemaal": "Judged by eye on the mesh silhouettes (13 Nov 2026). 15 of the 20 have arms: O1176648, "
                     "O120378 (corner chair, continuous arm rail), O134281, O134354, O144081, O314704, O372342 "
                     "(settee), O52933 and O58656, O60670 (settee), O68464, OK-05441D, OK-05441F, OK-06932, "
                     "OK-1987-0130. 4 have none (shells or low chairs: O21633, O372084, O48633, O76386). 1 is a "
                     "sofa seen end-on with a wrong seat (O1227036). False reports on chairs that truly lack "
                     "arms are thus 5 of 157 (3 %); the raw share mostly measures how incomplete the catalogue "
                     "name is.",
    }
    ut["samandrag"] = {s: ut["scenario"][s]["dom"] for s in ("a1", "a2", "a3", "b", "d")}
    ut["design_ok"] = all(ut["scenario"][s]["krav_oppfylt"] for s in ("a1", "a2", "a3", "b"))
    return ut


if __name__ == "__main__":
    import json
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"kjoer_dev": kjoer("dev"), "syntetisk_kontroll": syntetisk_kontroll()},
                     ensure_ascii=False, indent=1))
