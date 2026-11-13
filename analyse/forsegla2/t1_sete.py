#!/usr/bin/env python3
"""t1_sete.py - module T1 of the second sealed test (3D-model data): the mesh seat-height instrument (G0),
its two positive controls (K1, K2) and two replications made with it (E1, E3).

Run from the repository root:   python analyse/forsegla2/t1_sete.py
(prints kjoer('dev') and syntetisk_kontroll() as JSON, about 6 minutes; the held-out path exists but is never
run here).

WHAT IS TESTED
  G0  instrument gate, read first. On chairs that have BOTH a catalogue seat height and a mesh seat height:
      how well the mesh value tracks the catalogue value, pooled and per museum, and how its error depends on
      footprint, material and period. A hypothesis is void (UGYLDIG) when a fixed limit is broken.
  K1  positive control: the upper tail of the mesh seat height falls from before 1700 to 1945 and after.
  K2  positive control, known group: the 8 high chairs among the children's chairs must show a seat that is
      higher than a fixed share of their total height would give.
  E1  replication (designers' D1): seat height is the tightest direction, in centimetres from the floor, also
      on chairs for which no museum recorded a seat height.
  E3  replication (merged D2 + R3 + K2): where seat height gives way it gives way AGAINST footprint.

SAMPLE RULES (all fixed here, all decided on DEV or on the catalogue)
  SETEREGEL  a chair has a usable mesh seat height when
               1. its catalogue measures are not a copied record (rec['maal_kopi']);
               2. it has a mesh row with status 'ok' (a seat surface was found);
               3. its silhouettes pass the shared quality rule felles.kvalitet().
             Step 3 was added after looking at DEV: of the chairs that pass 1-2 and carry none of the flags
             opp_ikkje_y / opp_ned? / silhuett_klipt, the 19 that fail felles.kvalitet() have a seat MAE of
             4.6 cm against 3.1 cm for the 212 that pass (one block-shaped armchair is off by 24 cm), the
             V&A log-slope of mesh on catalogue is 0.77 with them and 0.86 without, and the footprint artefact
             of E3 is -0.20 with them and -0.17 without. felles.kvalitet() uses no seat value. NOT used: the
             flags topp_ved_kant and fleire_toppar (they are statements about the seat value itself).
             DEV: 212 of 255 pass (NM 97, VA 115).
             Every primary statistic is repeated under the LOOSE rule (steps 1-2 and none of the three
             flags; DEV 231) as a secondary line.
  G0 sample  utval chairs with sete_kat not None that pass SETEREGEL.
  E1 / E3    PRIMARY: held-out V&A chairs with sete_kat None that pass SETEREGEL. Nasjonalmuseet is reported,
             not scored (on DEV the mesh barely tracks the catalogue there: log-slope 0.27, r2 0.13, and the
             structural footprint artefact is -0.28). E3 also needs a year (rec['aar']).
             On DEV every chair has a catalogue seat, so kjoer('dev') uses the DEV V&A chairs as a stand-in
             (n = 115, a sixth of the expected held-out n of about 700). Its intervals are about 2.5 times
             wider than the sealed ones will be, and its verdicts are not the prediction.
  Year       rec['aar'] (aar_fraa). Period dummies: 50-year bins, years before 1600 in one bin.
  Intervals  cluster bootstrap over suites, felles.klyngebootstrap, 2000 resamples, seed felles.FRO, percentile.

ROBUST SPREAD
  rsd(v) = half the distance between the 16th and the 84th percentile of v (for a normal variable this is
  its SD). Applied to natural logs. Chosen over 1.4826 x MAD because it is the definition under which the
  designers' and reviewers' DEV values and the threshold 0.80 were produced, and because it uses more of the
  sample (asymptotic efficiency about 0.55 against 0.37). The MAD version is a secondary line.

E1: THE COMPRESSION CORRECTION (decision)
  The instruction said the mesh understates the true spread (a reviewer found mesh = 20.9 + 0.53 x catalogue
  and robust SD 2.97 against 3.71 cm on the pooled DEV chairs). Recomputed on DEV by museum this is a
  property of the POOLED sample, where two museums with different catalogue levels (median 47.0 and 43.5 cm)
  are mixed. Within the V&A, the scored museum, the mesh spread is not smaller than the catalogue spread
  (rsd of log: mesh 0.091, catalogue 0.085), because the mesh adds noise; what is compressed there is the
  slope (log mesh on log catalogue: 0.856, bootstrap 95 % interval 0.61 to 1.12, n = 115).
  Decision: the correction guards against the slope alone and gives no credit for the noise.
      K_KOMPRESJON = 1.17 = 1 / 0.856 (inverse DEV V&A log-log slope, rounded to two decimals)
      corrected ratio = K x rsd(log mesh seat) / min(rsd(log H), rsd(log B), rsd(log D))
  If log mesh = a + b log true + e, then rsd(mesh)^2 is about b^2 rsd(true)^2 + rsd(e)^2, so K x rsd(mesh)
  with K = 1/b is not below rsd(true): the corrected ratio is an UPPER estimate of the true ratio (the slope b
  is itself attenuated by catalogue error, which makes K larger still). Under a size-factor population the
  corrected ratio is 1 without instrument noise and above 1 with it (syntetisk_kontroll, lines a and a0).
  The price is power: the noise is counted as if it were spread of the seat. In syntetisk_kontroll() the
  corrected ratio is 0.53 when every chair has the same true seat height, 0.73 at a true ratio of 0.45 (the
  value of the V&A catalogue on DEV; HELDT in 83 % of runs) and 0.84 at a true ratio of 0.60 (HELDT in 18 %).
  The test therefore holds for true ratios up to about 0.45, not up to 0.80. The correction is valid only
  while the slope on the held-out chairs is not much below the DEV slope; the held-out slope is printed in
  G0 and the ratio under K = 1 / (held-out slope) is a secondary line.
  Not applied, shown as secondary lines: K = 1.25 (the reviewer's pooled spread ratio 3.71 / 2.97) and K = 1.

E3: THE ARTEFACT REFERENCE (decision that departs from the instruction, flagged)
  Statistic: partial Spearman of mesh seat height on sqrt(B x D) given H (ranked) and 50-year period DUMMIES.
  The mesh error falls with footprint, so the mesh produces a negative seat-footprint coupling by itself.
  The instruction asked for the reviewers' shuffle procedure (kritikk-maaling/a8.py): shuffle the catalogue
  seat heights between chairs and add each chair's own error (mesh minus catalogue) back; the mean of the
  statistic over shuffles is the artefact. On DEV V&A this gives -0.135 (the instruction expected about -0.10).
  That construction is biased towards zero when the calibration chairs have a true coupling. The error is
  err = (b - 1) x true + e + const with b = 0.84 < 1, so it carries the chair's own true seat height with a
  negative sign; DEV V&A seats do fall with footprint (catalogue coefficient -0.33), so err brings a POSITIVE
  footprint component along into every shuffled population and cancels part of the instrument's own.
  The construction that matches a world without true coupling keeps the regression residual instead:
      mesh* = a + b x shuffled catalogue seat + residual of the chair    (a, b: least squares on the sample)
  On DEV V&A this gives -0.167 (-0.070 within 'Stol', -0.263 within 'Armstol').
  With the reference at -0.14 and the expected held-out n, the all-types criterion E3a lets a population
  built under the second null through in 8 % of runs, against 2 % with the reference at -0.17; a one-sided
  97.5 % bound should let 2.5 % through (syntetisk_kontroll, line 'a2_..._n700', columns
  'del_E3a_held_under_instruksreferansen' and 'del_E3a_held'). The module therefore uses:
      E3_ARTEFAKT      = -0.17   reference of E3a (all types): the more negative of the two constructions on
                                 DEV V&A, rounded to two decimals
      E3_STOL_TERSKEL  = -0.14   limit of E3b (point estimate within 'Stol'): the instruction's reference
                                 (error-kept construction, all types, -0.135, rounded away from zero). Within
                                 'Stol' the structural artefact is only -0.07, so -0.14 lies 0.07 beyond it,
                                 about 1.5 standard errors of the 'Stol' estimate at the expected n of 455.
      E3_ARTEFAKT_SPES = -0.14   the instruction's reference; the conjunction under it is reported, no verdict
  What neither construction can show: the artefact is measured on chairs WITH a catalogue seat and assumed
  to hold for chairs without one; the catalogue is treated as the true height although V&A mixes rail and
  top-of-seat measures; and the literal has a bootstrap SD of 0.07 (n = 114), about half the distance between
  the reference and the DEV estimate.

E3 GATE AND ITS COST
  The instruction's limit (-0.15) assumed an artefact of about -0.10, i.e. a margin of 0.05. With the DEV value
  of the instruction's own construction at -0.135 that limit lies 0.015 from DEV and would void E3 in 40 % of
  samples in which nothing has changed (scratch t1_sete/p1_portmakt.py: 400 cluster resamples of the 114 DEV
  V&A chairs; the artefact estimate has a bootstrap SD of 0.07). The module keeps the margin, not the number:
  E3 is void when the residual-kept artefact, recomputed on the held-out V&A chairs with catalogue seat, is
  below E3_ARTEFAKT - 0.05 = -0.22. Even so the gate voids E3 in 19 % of samples with nothing changed (a
  little more on the expected 94 held-out chairs). That is the price of a gate measured on so few chairs; it
  is stated here so that a void verdict is not read as bad luck after the fact. The instruction's literal
  gate is evaluated and printed ('port_instruks_ikkje_bindande').

K2: THE CHILDREN'S CHAIRS
  Twelve children's chairs have catalogue measures: 8 named 'High chair' (H 86.5 to 117 cm) and 4 named
  'Child's chair' (H 60 to 68 cm). A low chair comes out low for any instrument whose values scale with H,
  so the 4 low chairs cannot fail and are only reported. The informative group is the high chairs: their seat
  is high because an adult's table is high, so it sits at a larger share of the total height than in an
  adult chair. An instrument that returned a typical share of H would miss that.
      d = mesh seat - (median adult mesh seat fraction) x own catalogue H
      K2 is HELD when at least 60 % (rounded up) of the high chairs with a mesh seat have d >= 4.0 cm,
      and at least 5 of the 8 have a mesh seat.
  The one high chair with a catalogue seat (58.8 cm at H 102.5) has d = +9.6 cm against the DEV adult
  fraction 0.48. Mesh rule for these chairs: the LOOSE rule (with 8 chairs every loss matters).
  Power, from syntetisk_kontroll: an instrument that sees the seat passes in 95 % of runs or more IF
  high-chair seats sit near 0.57 H (one chair is the evidence for that); an instrument that returns a typical
  fraction of H, or a typical adult height, passes in under 4 %; a detector that returns a random height
  inside its search window (0.25 H to 0.65 H) passes in 4 to 19 %, depending on how many chairs have a mesh
  seat. The anthropometric report in wf1.json has adult tables only; the rule rests on the catalogue names,
  on the 72 cm desk height quoted there, and on that one catalogued high chair.

VERDICTS
  HELDT / SLO FEIL / UGYLDIG per hypothesis, one conjunction each, named in SPEC. Positive controls are
  reported as held / failed; when both fail (or cannot be decided), 'instrumentflagg' is set and every
  mesh-seat result of this module carries it. Secondary lines never change a verdict.

BLINDNESS
  Held-out material is reached only through felles.les('held'), felles.silhuett('held') and
  felles.les_ekstra('barnestol'), all guarded. Nothing in this file was tuned on it. Quantities the frozen
  script recomputes on the held-out side by instruction: the adult percentiles and median seat fraction used
  by K2, and every G0 value. All thresholds are literals below.

LOADER NOTE
  felles.partial_spearman treats a covariate as numeric whenever all its values can be read as numbers. Period
  labels such as '1700' would therefore enter as ONE ranked covariate. The labels here are 'b1700'.
"""
import json
import math
import os
import sys

import numpy as np
from scipy.stats import rankdata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import felles as F  # noqa: E402

# ============================================================================ frozen literals
SETE_FLAGG = frozenset({"opp_ikkje_y", "opp_ned?", "silhuett_klipt"})    # used by the LOOSE rule only
PERIODESTEG, PERIODEGOLV = 50, 1600
PERIODAR = (("<1700", None, 1700), ("1700-1799", 1700, 1800), ("1800-1899", 1800, 1900),
            ("1900-1944", 1900, 1945), ("1945+", 1945, None))

# --- G0
DEV_MEDIAN_KAT = {"samla": 45.6, "NM": 47.0, "VA": 43.5}     # DEV median catalogue seat height (cm), SETEREGEL chairs
G0_R2_GOLV_SAMLA = 0.16      # half the DEV pooled r2 of log mesh on log catalogue (0.322)
G0_R2_GOLV_VA = 0.20         # half the DEV V&A r2 (0.396); added because E1 is scored on V&A only
G0_ARTEFAKT_STRUKT_MIN = -0.22   # GATE: residual-kept artefact on held-out V&A not beyond E3_ARTEFAKT - 0.05 (DEV -0.167)
G0_ARTEFAKT_SPES_MIN = -0.15     # the instruction's literal for the error-kept artefact (DEV -0.135); printed, NOT a gate
G0_N_MIN_VA = 40             # fewer V&A calibration chairs than this: the gate cannot be read, E1 and E3 void
N_PERM = 1000                # shuffles per artefact value

# --- E1
K_KOMPRESJON = 1.17          # 1 / 0.856, inverse DEV V&A log-log slope of mesh on catalogue seat
K_MELDAR = 1.25              # reviewer's pooled factor 3.71 / 2.97 (secondary line only)
E1_TERSKEL = 0.80            # corrected ratio must be below
E1_OVRE = 1.00               # upper 95 % bound of the corrected ratio must be below
E_N_MIN = 100                # primary sample smaller than this: void
E3_N_MIN_STOL = 60

# --- E3
E3_ARTEFAKT = -0.17          # reference of E3a: residual-kept shuffle artefact, DEV V&A all types (-0.167)
E3_ARTEFAKT_SPES = -0.14     # the instruction's reference: error-kept shuffle artefact, DEV V&A all types (-0.135)
E3_STOL_TERSKEL = -0.14      # limit of E3b = E3_ARTEFAKT_SPES (structural artefact within 'Stol' on DEV: -0.070)

# --- K1
K1_HMIN = 80.0               # cm; seat detector ceiling 0.65 H is then at least 52 cm
K1_FALL = 3.5                # cm; 90th percentile before 1700 minus 90th percentile 1945 and after
K1_N_MIN = 10                # per period

# --- K2
K2_HOG_NAMN = "high chair"   # catalogue name contains this (lower-cased) -> high chair; else low child's chair
K2_HOG_MARGIN = 4.0          # cm above (adult median mesh seat fraction x own catalogue H)
K2_HOG_DEL = 0.60            # share of the high chairs with a mesh seat that must clear the margin (rounded up)
K2_HOG_N_MIN = 5             # fewer high chairs with a mesh seat than this: not decided
# catalogue heights (cm) of the 8 high chairs, read from stolar_reinsa.csv (catalogue, not sealed);
# used ONLY to build the synthetic children in syntetisk_kontroll()
K2_KATALOG_H_HOG = (86.5, 91.0, 91.5, 92.8, 94.0, 102.5, 106.0, 117.0)

# --- variance field
FELT_HREF = 95               # common height (rows) of the height-normalised registration
FELT_RADER_SIDE = (30, 60)   # rows 30-59
FELT_RAD_FRONT = 60          # front view, rows 60 and above

# --- synthetic control
SYN_N = 700                  # size of the synthetic populations (expected held-out n of the primary sample)
SYN_BOOT = 300               # bootstrap resamples inside each synthetic run (2000 in kjoer)
SYN_RUNS = 60

SPEC_G0 = {
    "id": "G0", "slag": "instrument",
    "tittel": "Instrument gate: mesh seat height against catalogue seat height",
    "utval": "utval chairs with catalogue seat height (sete_kat not None) that pass SETEREGEL; pooled and per museum "
             "(expected held-out n: V&A about 94, NM about 66)",
    "rapport": ["n", "MAE mesh against catalogue", "MAE of a constant (DEV median, literal)", "median error",
                "Spearman", "r2 of log mesh on log catalogue", "slope (cm and log-log)",
                "partial Spearman of error on sqrt(B*D) given H (and given H and period)",
                "shuffle artefacts (two constructions)", "catalogue-seat coefficient of the E3 statistic",
                "error by material class", "error by period", "tail confusion at 49 cm",
                "V&A error by seat convention (rail / topp)"],
    "port": [
        {"namn": "n_VA", "gjeld": "E1, E3", "terskel": G0_N_MIN_VA, "ugyldig_dersom": "fewer than 40 V&A calibration chairs",
         "regel_for_terskel": "under half of the expected 94", "dev_verdi": 115},
        {"namn": "r2_samla", "gjeld": "E1", "terskel": G0_R2_GOLV_SAMLA, "ugyldig_dersom": "pooled r2 < 0.16",
         "regel_for_terskel": "half the DEV pooled r2", "dev_verdi": 0.322},
        {"namn": "r2_VA", "gjeld": "E1", "terskel": G0_R2_GOLV_VA, "ugyldig_dersom": "V&A r2 < 0.20",
         "regel_for_terskel": "half the DEV V&A r2 (added: E1 is scored on V&A)", "dev_verdi": 0.396},
        {"namn": "artefakt_strukt_VA", "gjeld": "E3", "terskel": G0_ARTEFAKT_STRUKT_MIN,
         "ugyldig_dersom": "residual-kept shuffle artefact on V&A calibration chairs < -0.22",
         "regel_for_terskel": "reference E3_ARTEFAKT (-0.17) minus 0.05, the margin of the instruction's gate (-0.15 against an expected -0.10)",
         "dev_verdi": -0.167, "sjanse_for_ugyldig_utan_endring": 0.19},
        {"namn": "katalogkoeffisient_VA", "gjeld": "E3", "terskel": 0.0,
         "ugyldig_dersom": "E3 statistic computed with CATALOGUE seat on the V&A calibration chairs >= 0",
         "regel_for_terskel": "instruction: the calibration subset must agree in sign", "dev_verdi": -0.332},
    ],
    "ikkje_bindande": [
        {"namn": "artefakt_spes_VA (the instruction's literal gate)", "terskel": G0_ARTEFAKT_SPES_MIN,
         "merknad": "error-kept shuffle artefact < -0.15. Evaluated and printed, not used: its DEV value is -0.135, 0.015 from the limit.",
         "dev_verdi": -0.135, "sjanse_for_ugyldig_utan_endring": 0.40},
    ],
}

SPEC_K = {
    "id": "K", "slag": "instrument",
    "tittel": "Positive controls of the mesh seat height",
    "kontrollar": [
        {"namn": "K1 upper tail falls",
         "utval": "utval chairs that pass SETEREGEL, with a year and catalogue H >= 80 cm; both museums, with and without catalogue seat",
         "statistikk": "90th percentile of mesh seat height, years before 1700, minus the same for 1945 and after",
         "terskel": K1_FALL, "retning": ">=",
         "regel_for_terskel": "instruction (3.5 cm); DEV fall 8.4 cm pooled, 6.0 cm in V&A", "dev_verdi": 8.4,
         "merknad": "both periods need at least 10 chairs, else 'ikkje avgjord' (counts as failed for the flag)"},
        {"namn": "K2 high chairs",
         "utval": "the 12 children's chairs of felles.les_ekstra('barnestol'); high chair = catalogue name contains 'high chair' (8); mesh seat by the LOOSE rule",
         "statistikk": "d = mesh seat - (median adult mesh seat fraction x own catalogue H); k = high chairs with d >= 4.0 cm. Adult median fraction recomputed on the utval chairs that pass SETEREGEL (DEV 0.480).",
         "terskel": "k >= ceil(0.60 x number of high chairs with a mesh seat), and at least 5 of the 8 have a mesh seat",
         "retning": ">=",
         "regel_for_terskel": "4.0 cm is about one residual SD of the instrument on DEV V&A (4.3 cm) and under half the 9.6 cm of the one high chair with a catalogue seat; 60 % keeps a fraction-of-H instrument under 4 % and a seeing instrument at 95 % or more in the synthetic control",
         "dev_verdi": None,
         "merknad": "the 4 low child's chairs are reported, not scored: any instrument that scales with H puts them low"},
    ],
    "flagg": "if K1 and K2 both fail (or are not decided), 'instrumentflagg' is true and every mesh-seat result of T1 carries it",
}

SPEC_E1 = {
    "id": "E1", "slag": "replikasjon",
    "tittel": "Seat height is the tightest direction in centimetres, also on chairs the museums never measured",
    "proposisjonar": ["6.672", "6.6721", "1.321", "3.21", "7.153"],
    "paastand": "Among chairs without a catalogued seat height, the robust spread of log seat height (from the "
                "3D model, corrected for the compression of that instrument) is below 0.80 of the smallest "
                "robust spread among log height, log width and log depth.",
    "utval": "held-out V&A chairs with sete_kat None that pass SETEREGEL (expected n about 700 of 874). "
             "Nasjonalmuseet reported, not scored. On 'dev': DEV V&A chairs (all catalogued) as stand-in.",
    "primaer": [
        {"namn": "E1a corrected ratio",
         "statistikk": "K_KOMPRESJON x rsd(log sete_mesh) / min(rsd(log H), rsd(log B), rsd(log D)), rsd = half the 16-84 percentile range",
         "terskel": E1_TERSKEL, "retning": "<",
         "regel_for_terskel": "designers' rule kept by the PI: midpoint between the DEV upper bound (0.60, pooled, uncorrected) and the base-model value 1; the correction K = 1.17 = 1 / (DEV V&A log-log slope 0.856) is applied on top of it",
         "dev_verdi": 0.580},
        {"namn": "E1b upper 95 % bound of the corrected ratio",
         "statistikk": "97.5th percentile of the cluster bootstrap of E1a", "terskel": E1_OVRE, "retning": "<",
         "regel_for_terskel": "the base-model value itself", "dev_verdi": 0.909},
    ],
    "konjunksjon": "HELDT only if E1a and E1b both hold",
    "sekundaer": ["uncorrected ratio, and ratio under K = 1.25 and under K recomputed on held-out V&A calibration chairs",
                  "period-centred variant (log values centred on the median of their 50-year bin)",
                  "MAD variant of the robust spread", "the LOOSE mesh rule (without felles.kvalitet)",
                  "Nasjonalmuseet (uncorrected and corrected with the V&A factor, for the record only)",
                  "loadings of the smallest eigen-direction of cov(log seat, log H, log B, log D) and sum/2",
                  "variance-field gain, side view rows 30-59, floor-anchored against height-normalised; front view above row 60 as control",
                  "MAE of a constant against a fixed fraction of H (mesh seat; and catalogue seat on the G0 chairs)",
                  "share of mesh seats above 49 cm by period"],
    "port": [
        {"namn": "G0 n_VA", "terskel": G0_N_MIN_VA, "ugyldig_dersom": "fewer than 40 V&A calibration chairs"},
        {"namn": "G0 r2_samla", "terskel": G0_R2_GOLV_SAMLA, "ugyldig_dersom": "pooled r2 of log mesh on log catalogue < 0.16"},
        {"namn": "G0 r2_VA", "terskel": G0_R2_GOLV_VA, "ugyldig_dersom": "V&A r2 < 0.20"},
        {"namn": "n", "terskel": E_N_MIN, "ugyldig_dersom": "primary sample below 100 chairs"},
    ],
    "grunnmodell": "One common size factor: every chair is a scaled copy, seat height is a fixed share of the size. "
                   "It predicts a true ratio of 1; the corrected statistic is then 1.00 without instrument noise and "
                   "about 1.2 with the DEV noise (synthetic control), so E1a fails.",
    "tel_imot": "corrected ratio >= 0.80, or its upper 95 % bound >= 1. A failure here together with the pass on "
                "catalogued chairs in the first test would mean that the earlier result depended on which chairs "
                "cataloguers chose to measure, or that the mesh instrument is too noisy to show it.",
    "sjanse_for_feil": "about 0.3: DEV itself would pass at the sealed sample size, but the uncatalogued V&A chairs are another population (reviewers: narrower H) and the test only holds for true ratios up to about 0.45",
}

SPEC_E3 = {
    "id": "E3", "slag": "replikasjon",
    "tittel": "Seat height yields against footprint, not with it",
    "proposisjonar": ["6.672", "6.675", "1.324", "2.122", "4.5"],
    "paastand": "Among V&A chairs without a catalogued seat height, mesh seat height falls as footprint sqrt(B x D) "
                "grows, given total height and period, by more than the mesh instrument produces by itself; and "
                "the fall is also there inside the type 'Stol'.",
    "utval": "held-out V&A chairs with sete_kat None that pass SETEREGEL and have a year (expected n about 695; "
             "type 'Stol' about 455). Nasjonalmuseet reported, not scored. On 'dev': DEV V&A chairs as stand-in.",
    "primaer": [
        {"namn": "E3a all types: upper 95 % bound",
         "statistikk": "partial Spearman of sete_mesh on sqrt(B*D) given H (ranked) and 50-year period dummies; 97.5th percentile of the cluster bootstrap",
         "terskel": E3_ARTEFAKT, "retning": "<",
         "regel_for_terskel": "artefact reference: mean of the statistic over populations in which catalogue seat heights are shuffled and mesh* = a + b x shuffled seat + the chair's regression residual; DEV V&A -0.167, rounded. The instruction's construction (error kept) gives -0.135 and is reported beside it.",
         "dev_verdi": -0.140, "dev_punktestimat": -0.334},
        {"namn": "E3b type 'Stol': point estimate",
         "statistikk": "the same partial Spearman within type 'Stol'", "terskel": E3_STOL_TERSKEL, "retning": "<=",
         "regel_for_terskel": "the instruction's reference (error-kept shuffle artefact, all types, DEV V&A -0.135, rounded away from zero); the structural artefact within 'Stol' alone is -0.070 on DEV, so the limit lies 0.07 beyond it",
         "dev_verdi": -0.257},
    ],
    "konjunksjon": "HELDT only if E3a and E3b both hold. E3a holds and E3b fails: SLO FEIL with the text 'two type valleys' "
                   "(the coupling is a difference between chair types, not a slope inside one).",
    "sekundaer": ["point estimate and interval, all types and 'Stol' and 'Armstol'",
                  "the conjunction under the instruction's reference -0.14 for both parts (no verdict)",
                  "Nasjonalmuseet", "raw Spearman", "the same statistic with D and with B in place of footprint",
                  "the LOOSE mesh rule", "catalogue-seat coefficient on the G0 V&A chairs, by convention rail / topp"],
    "port": [
        {"namn": "G0 n_VA", "terskel": G0_N_MIN_VA, "ugyldig_dersom": "fewer than 40 V&A calibration chairs"},
        {"namn": "G0 artefakt_strukt_VA", "terskel": G0_ARTEFAKT_STRUKT_MIN, "ugyldig_dersom": "residual-kept shuffle artefact on V&A calibration chairs < -0.22"},
        {"namn": "G0 katalogkoeffisient_VA", "terskel": 0.0, "ugyldig_dersom": "catalogue-seat coefficient on V&A calibration chairs >= 0"},
        {"namn": "kontrollpar B~D", "terskel": 0.0, "ugyldig_dersom": "partial Spearman of B on D given H and period <= 0 on the primary sample"},
        {"namn": "kontrollpar sete~H", "terskel": 0.0, "ugyldig_dersom": "Spearman of sete_mesh on H <= 0 on the primary sample"},
        {"namn": "n", "terskel": E_N_MIN, "ugyldig_dersom": "primary sample below 100 chairs"},
        {"namn": "n_Stol", "terskel": E3_N_MIN_STOL, "ugyldig_dersom": "fewer than 60 chairs of type 'Stol'"},
    ],
    "grunnmodell": "Three can win. (1) One size factor: seat rises with footprint, coefficient positive. (2) Independent hold: "
                   "no true coupling; the statistic then sits at the artefact (about -0.17) and its upper bound stays above the "
                   "reference in about 97 % of samples. (3) Two type valleys: a coupling between types and none inside 'Stol'; "
                   "E3b then fails.",
    "tel_imot": "upper bound at or above -0.17 (the coupling is not distinguishable from what the instrument makes), or "
                "the 'Stol' estimate above -0.14.",
    "sjanse_for_feil": "about 0.2 for SLO FEIL and about 0.2 for UGYLDIG through the artefact gate",
}

SPEC = {
    "id": "T1",
    "tittel": "The mesh seat-height instrument and two replications with it",
    "slag": "instrument + replikasjon",
    "fil": "analyse/forsegla2/t1_sete.py",
    "seteregel": "not maal_kopi; mesh_status == 'ok'; felles.kvalitet() passed",
    "delar": {"G0": SPEC_G0, "K": SPEC_K, "E1": SPEC_E1, "E3": SPEC_E3},
    # the flat keys of the module contract, for a reader that expects one hypothesis per module
    "proposisjonar": sorted(set(SPEC_E1["proposisjonar"] + SPEC_E3["proposisjonar"])),
    "paastand": "E1: " + SPEC_E1["paastand"] + " E3: " + SPEC_E3["paastand"],
    "utval": "see delar; primary sample of E1 and E3: held-out V&A chairs without catalogue seat height that pass SETEREGEL",
    "primaer": [dict(p, hypotese="E1") for p in SPEC_E1["primaer"]] + [dict(p, hypotese="E3") for p in SPEC_E3["primaer"]],
    "sekundaer": {"E1": SPEC_E1["sekundaer"], "E3": SPEC_E3["sekundaer"]},
    "port": [dict(p, hypotese="E1") for p in SPEC_E1["port"]] + [dict(p, hypotese="E3") for p in SPEC_E3["port"]],
    "grunnmodell": {"E1": SPEC_E1["grunnmodell"], "E3": SPEC_E3["grunnmodell"]},
    "tel_imot": {"E1": SPEC_E1["tel_imot"], "E3": SPEC_E3["tel_imot"]},
}


# ============================================================================ small helpers
def _r(x, nd=4):
    """JSON-safe number: None for NaN / inf, rounded float otherwise."""
    if x is None:
        return None
    x = float(x)
    return None if not math.isfinite(x) else round(x, nd)


def _rl(xs, nd=4):
    return [_r(x, nd) for x in xs]


def _laus(r):
    """The LOOSE mesh rule (steps 1-2 of SETEREGEL and none of the three orientation flags) -> (ok, reason)."""
    if r.get("maal_kopi"):
        return False, "maal_kopi"
    st = r.get("mesh_status")
    if st is None:
        return False, "ingen_meshrad"
    if st != "ok" or r.get("sete_mesh") is None:
        return False, ("utan_seteflate" if st == "ok_utan_sete" else "mesh_feil")
    if r["flagg"] & SETE_FLAGG:
        return False, "flagg"
    return True, "ok"


def _seteregel(r, sil):
    """SETEREGEL -> (ok, reason); the reason is the first step that fails."""
    if r.get("maal_kopi"):
        return False, "maal_kopi"
    st = r.get("mesh_status")
    if st is None:
        return False, "ingen_meshrad"
    if st != "ok" or r.get("sete_mesh") is None:
        return False, ("utan_seteflate" if st == "ok_utan_sete" else "mesh_feil")
    s = sil.get(r["id"])
    if s is None:
        return False, "ingen_silhuett"
    if not F.kvalitet(r, s[0], s[1])[0]:
        return False, "kvalitetsregel"
    return True, "ok"


def _sil(recs, grunnlag, merke):
    """Keep the records marked ok in merke (id -> (ok, reason)) -> (kept records, attrition dict)."""
    ut, tap = [], {}
    for r in recs:
        ok, g = merke[r["id"]]
        if ok:
            ut.append(r)
        else:
            tap[g] = tap.get(g, 0) + 1
    return ut, {"grunnlag": grunnlag, "n_inn": len(recs), "n_ut": len(ut), "tapt": dict(sorted(tap.items()))}


def _bolk(r):
    """Label of the 50-year bin. It starts with a letter ON PURPOSE: felles.partial_spearman treats a covariate
    whose values can all be read as numbers as numeric (ranked), and '1700' can; 'b1700' cannot, so the bins
    enter as dummy variables."""
    return "b%d" % F.aarsbolk(r["aar"], PERIODESTEG, PERIODEGOLV)


def _periode(aar):
    for namn, lo, hi in PERIODAR:
        if (lo is None or aar >= lo) and (hi is None or aar < hi):
            return namn
    return None


def rsd(v):
    """Robust SD: half the distance between the 16th and 84th percentile. NaN below 5 values."""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if len(v) < 5:
        return float("nan")
    lo, hi = np.percentile(v, [16, 84])
    return float(0.5 * (hi - lo))


def _kol(recs, k):
    return np.array([r[k] for r in recs], float)


def _ki(boot):
    lo, hi = F.ki(boot)
    return [_r(lo), _r(hi)]


# ============================================================================ E1 statistics
def e1_vektor(recs, sete="sete_mesh", spreiing=rsd, sentrer=False):
    """-> array [ratio (uncorrected), spread log seat, spread log H, spread log B, spread log D].
    sentrer=True: the four log columns are centred on the median of their 50-year bin first (chairs need a year)."""
    if len(recs) < 5:
        return np.full(5, np.nan)
    X = np.log(np.column_stack([_kol(recs, sete), _kol(recs, "H"), _kol(recs, "B"), _kol(recs, "D")]))
    if sentrer:
        b = np.array([_bolk(r) for r in recs])
        for niva in set(b):
            m = b == niva
            X[m] -= np.median(X[m], axis=0)
    s = [spreiing(X[:, j]) for j in range(4)]
    nemnar = min(s[1:])
    forhold = s[0] / nemnar if nemnar and nemnar > 0 else float("nan")
    return np.array([forhold] + s, float)


def _e1_dom(korr, ovre):
    return bool(korr is not None and ovre is not None and korr < E1_TERSKEL and ovre < E1_OVRE)


def _e1_linje(recs, boot=True, **kw):
    v = e1_vektor(recs, **kw)
    ut = {"n": len(recs), "suitar": len({F.suite(r) for r in recs}),
          "forhold_ukorrigert": _r(v[0]), "forhold_korrigert": _r(K_KOMPRESJON * v[0]),
          "spreiing_log": {"sete": _r(v[1]), "H": _r(v[2]), "B": _r(v[3]), "D": _r(v[4])}}
    if boot and len(recs) >= 5:
        b = F.klyngebootstrap(recs, lambda rs: e1_vektor(rs, **kw)[0])
        lo, hi = F.ki(b)
        ut["ki95_ukorrigert"] = [_r(lo), _r(hi)]
        ut["ki95_korrigert"] = [_r(K_KOMPRESJON * lo), _r(K_KOMPRESJON * hi)]
    return ut


def eigenretning(recs, sete="sete_mesh"):
    """Smallest eigen-direction of the covariance of (log seat, log H, log B, log D), museum-centred (median),
    winsorised at 3 robust SD per column. -> [v_seat, v_H, v_B, v_D, sum(v)/2, sd along v, rsd of log seat].
    Sign: v_seat >= 0. A proportion (size-free ratio) has sum(v) = 0; an absolute length has sum(v)/2 away from 0."""
    if len(recs) < 10:
        return np.full(7, np.nan)
    X = np.log(np.column_stack([_kol(recs, sete), _kol(recs, "H"), _kol(recs, "B"), _kol(recs, "D")]))
    mus = np.array([r["museum"] for r in recs])
    for m in set(mus):
        X[mus == m] -= np.median(X[mus == m], axis=0)
    s = 1.4826 * np.median(np.abs(X - np.median(X, axis=0)), axis=0)
    if not np.all(s > 0):
        return np.full(7, np.nan)
    Z = np.clip((X - np.median(X, axis=0)) / s, -3, 3) * s
    w, V = np.linalg.eigh(np.cov(Z.T))
    v = V[:, 0] * (1.0 if V[0, 0] >= 0 else -1.0)
    return np.array(list(v) + [v.sum() / 2.0, math.sqrt(max(w[0], 0.0)), rsd(X[:, 0])], float)


def mae_konstant_mot_del(recs, sete="sete_mesh"):
    """-> [MAE of the sample median, MAE of (median seat fraction x H), ratio]."""
    if len(recs) < 5:
        return np.full(3, np.nan)
    s, H = _kol(recs, sete), _kol(recs, "H")
    a = float(np.abs(s - np.median(s)).mean())
    b = float(np.abs(s - np.median(s / H) * H).mean())
    return np.array([a, b, a / b if b > 0 else np.nan], float)


def del_over_49(recs, sete="sete_mesh"):
    ut = {}
    for namn, _, _ in PERIODAR:
        v = [r[sete] for r in recs if r["aar"] is not None and _periode(r["aar"]) == namn]
        ut[namn] = {"n": len(v), "del_over_49": _r(np.mean(np.array(v) > 49.0)) if v else None,
                    "median": _r(np.median(v), 2) if v else None, "p90": _r(np.percentile(v, 90), 2) if v else None}
    return ut


# ============================================================================ variance field (silhouettes)
def _hogdnorm(S):
    """Rows resampled so that the top of the silhouette lands on row FELT_HREF (as fordeling/a9.py rel())."""
    rad = np.nonzero(S.any(axis=1))[0]
    ut = np.zeros_like(S)
    if len(rad) == 0:
        return ut
    hk = int(rad.max()) + 1
    idx = (np.arange(FELT_HREF) * hk / FELT_HREF).astype(int)
    ut[:FELT_HREF] = S[idx]
    return ut


def _feltdata(recs, sil):
    """Stacked silhouettes of recs (all of them pass SETEREGEL, hence felles.kvalitet) -> dict of arrays."""
    recs = [r for r in recs if r["id"] in sil]
    if not recs:
        return None
    side = np.stack([sil[r["id"]][0] for r in recs]).astype(np.uint8)
    front = np.stack([sil[r["id"]][1] for r in recs]).astype(np.uint8)
    side_n = np.stack([_hogdnorm(s) for s in side])
    front_n = np.stack([_hogdnorm(s) for s in front])
    a, b = FELT_RADER_SIDE
    flat = lambda A: A.reshape(len(A), -1).astype(np.float32)
    return {"ids": [r["id"] for r in recs], "n": len(recs),
            "side_golv": side, "side_norm": side_n,
            "s_g": flat(side[:, a:b]), "s_n": flat(side_n[:, a:b]),
            "f_g": flat(front[:, FELT_RAD_FRONT:]), "f_n": flat(front_n[:, FELT_RAD_FRONT:])}


def _feltvinst(fd, w=None):
    """-> [gain side rows 30-59, V floor-anchored, V height-normalised, gain front rows >= 60, V floor, V norm].
    V = sum over pixels of p(1-p), p = share of chairs that cover the pixel; gain = 1 - V_floor / V_norm.
    gain > 0: the floor-anchored stack agrees better."""
    n = fd["n"]
    w = np.full(n, 1.0 / n, np.float32) if w is None else (w / w.sum()).astype(np.float32)
    V = []
    for k in ("s_g", "s_n", "f_g", "f_n"):
        p = w @ fd[k]
        V.append(float((p * (1.0 - p)).sum()))
    g_side = 1.0 - V[0] / V[1] if V[1] > 0 else float("nan")
    g_front = 1.0 - V[2] / V[3] if V[3] > 0 else float("nan")
    return np.array([g_side, V[0], V[1], g_front, V[2], V[3]], float)


def _felt(recs, sil, boot=True):
    fd = _feltdata(recs, sil)
    if fd is None or fd["n"] < 10:
        return {"n": 0 if fd is None else fd["n"], "merknad": "too few silhouettes"}, fd
    v = _feltvinst(fd)
    ut = {"n": fd["n"],
          "side_rader_30_59": {"vinst": _r(v[0]), "V_golvfesta": _r(v[1], 1), "V_hogdnormalisert": _r(v[2], 1)},
          "front_rader_fraa_60": {"vinst": _r(v[3]), "V_golvfesta": _r(v[4], 1), "V_hogdnormalisert": _r(v[5], 1),
                                  "kontroll_hogdnormalisert_vinn": bool(v[3] < 0)},
          "lesing": "vinst > 0: chairs stacked in centimetres from the floor agree better than chairs scaled to a common "
                    "height. The top edge of every silhouette is the catalogue H by construction."}
    if boot:
        pos = {i: j for j, i in enumerate(fd["ids"])}
        med = [r for r in recs if r["id"] in pos]

        def st(rs):
            w = np.bincount([pos[r["id"]] for r in rs], minlength=fd["n"]).astype(np.float32)
            return _feltvinst(fd, w)[[0, 3]]
        b = F.klyngebootstrap(med, st)
        ut["side_rader_30_59"]["ki95"] = _ki(b[:, 0])
        ut["front_rader_fraa_60"]["ki95"] = _ki(b[:, 1])
    return ut, fd


# ============================================================================ E3 statistics
def e3_stat(recs, y=None, x=None):
    """Partial Spearman of y (default: sete_mesh) on x (default: sqrt(B*D)) given H and 50-year period dummies."""
    if len(recs) < 8:
        return float("nan")
    y = [r["sete_mesh"] for r in recs] if y is None else list(y)
    x = [math.sqrt(r["B"] * r["D"]) for r in recs] if x is None else list(x)
    return F.partial_spearman(y, x, [[r["H"] for r in recs], [_bolk(r) for r in recs]])


def _e3_linje(recs, boot=True, y=None):
    f = (lambda rs: e3_stat(rs)) if y is None else (lambda rs: e3_stat(rs, y=[r[y] for r in rs]))
    ut = {"n": len(recs), "suitar": len({F.suite(r) for r in recs}), "verdi": _r(f(recs))}
    if boot and len(recs) >= 8:
        ut["ki95"] = _ki(F.klyngebootstrap(recs, f))
    return ut


def _lineaer(recs):
    """Least squares of sete_mesh on sete_kat (cm) -> (a, b, residuals)."""
    c, m = _kol(recs, "sete_kat"), _kol(recs, "sete_mesh")
    b, a = np.polyfit(c, m, 1)
    return float(a), float(b), m - (a + b * c)


class _E3Kjerne:
    """Fast evaluation of the E3 statistic for many y vectors on ONE fixed set of chairs (or index resamples of
    it). Same arithmetic as felles.partial_spearman: ranks of y and x, residuals after least squares on
    [1, rank(H), period dummies], Pearson correlation of the residuals. Checked against felles.partial_spearman
    in _sjolvsjekk()."""

    def __init__(self, recs):
        self.n = len(recs)
        self.x = np.array([math.sqrt(r["B"] * r["D"]) for r in recs])
        self.H = _kol(recs, "H")
        b = np.array([_bolk(r) for r in recs])
        self.D = np.column_stack([(b == niva).astype(float) for niva in sorted(set(b))])
        self.typ = np.array([r["type"] for r in recs])

    def stat(self, y, idx=None):
        x, H, D = self.x, self.H, self.D
        if idx is not None:
            x, H, D, y = x[idx], H[idx], D[idx], y[idx]
        n = len(y)
        D = D[:, D.any(axis=0)]
        if n - D.shape[1] - 1 < 3:
            return float("nan")
        Z = np.column_stack([rankdata(H), D])          # the dummies sum to 1: they hold the intercept
        R = np.column_stack([rankdata(x), rankdata(y)])
        E = R - Z @ np.linalg.lstsq(Z, R, rcond=None)[0]
        s = E.std(axis=0)
        if s[0] < 1e-9 or s[1] < 1e-9:
            return float("nan")
        return float(np.corrcoef(E[:, 0], E[:, 1])[0, 1])


def artefakt(recs, slag, n_perm=N_PERM, seed=F.FRO):
    """Mean of the E3 statistic over n_perm populations WITHOUT true coupling, built from chairs that have both
    seat heights. Catalogue seat heights are shuffled within museum, then
      slag 'feil'  (the instruction, kritikk-maaling/a8.py): mesh* = shuffled seat + (mesh - catalogue) of the chair
      slag 'rest'  (reference of this module):               mesh* = a + b x shuffled seat + regression residual of the chair
    -> (mean, sd over shuffles)."""
    if len(recs) < 12:
        return float("nan"), float("nan")
    c, m = _kol(recs, "sete_kat"), _kol(recs, "sete_mesh")
    mus = np.array([r["museum"] for r in recs])
    grupper = [np.nonzero(mus == g)[0] for g in sorted(set(mus))]
    if slag == "feil":
        behald = m - c
        bygg = lambda cp: cp + behald
    elif slag == "rest":
        a, b, res = _lineaer(recs)
        bygg = lambda cp: a + b * cp + res
    else:
        raise ValueError(slag)
    kjerne = _E3Kjerne(recs)
    rng = np.random.default_rng(seed)
    ut = np.empty(n_perm)
    for i in range(n_perm):
        cp = c.copy()
        for k in grupper:
            cp[k] = c[rng.permutation(k)]
        ut[i] = kjerne.stat(bygg(cp))
    return float(np.nanmean(ut)), float(np.nanstd(ut))


def _e3_dom(ovre_alle, punkt_stol, ref=E3_ARTEFAKT, ref_stol=E3_STOL_TERSKEL):
    a = bool(ovre_alle is not None and math.isfinite(ovre_alle) and ovre_alle < ref)
    b = bool(punkt_stol is not None and math.isfinite(punkt_stol) and punkt_stol <= ref_stol)
    if a and b:
        return "HELDT", "seat height yields against footprint, beyond the instrument artefact, also within 'Stol'", a, b
    if a and not b:
        return "SLO FEIL", "two type valleys: the coupling holds across types but not within 'Stol'", a, b
    return "SLO FEIL", "the coupling is not distinguishable from the instrument artefact", a, b


# ============================================================================ G0
def _g0_gruppe(recs, dev_median, boot=True):
    n = len(recs)
    if n < 8:
        return {"n": n, "merknad": "too few chairs"}
    c, m = _kol(recs, "sete_kat"), _kol(recs, "sete_mesh")
    e = m - c

    def kjerne(rs):
        cc, mm = np.log(_kol(rs, "sete_kat")), np.log(_kol(rs, "sete_mesh"))
        if len(rs) < 8 or cc.std() == 0 or mm.std() == 0:
            return np.full(4, np.nan)
        r = np.corrcoef(cc, mm)[0, 1]
        return np.array([r * r, np.polyfit(cc, mm, 1)[0], np.abs(np.exp(mm) - np.exp(cc)).mean(),
                         F.partial_spearman(list(np.exp(mm) - np.exp(cc)),
                                            [math.sqrt(q["B"] * q["D"]) for q in rs], [[q["H"] for q in rs]])])
    k = kjerne(recs)
    b_cm, a_cm = np.polyfit(c, m, 1)
    med_aar = [r for r in recs if r["aar"] is not None]
    ut = {
        "n": n, "suitar": len({F.suite(r) for r in recs}),
        "MAE_mesh_mot_katalog": _r(np.abs(e).mean(), 2),
        "MAE_konstant_devmedian": _r(np.abs(c - dev_median).mean(), 2), "devmedian_brukt": dev_median,
        "mesh_slaar_konstanten": bool(np.abs(e).mean() < np.abs(c - dev_median).mean()),
        "medianfeil": _r(np.median(e), 2), "median_katalog": _r(np.median(c), 2), "median_mesh": _r(np.median(m), 2),
        "spearman": _r(F.spearman(m, c)), "r2_log": _r(k[0]),
        "stiging_cm": _r(b_cm), "konstantledd_cm": _r(a_cm, 2), "stiging_log": _r(k[1]),
        "rsd_log_katalog": _r(rsd(np.log(c))), "rsd_log_mesh": _r(rsd(np.log(m))),
        "feil_mot_fotavtrykk_gitt_H": _r(k[3]),
        "feil_mot_fotavtrykk_gitt_H_og_periode": _r(e3_stat(med_aar, y=[r["sete_mesh"] - r["sete_kat"] for r in med_aar])),
        "hale_49": {"katalog_over": int((c > 49).sum()), "mesh_over": int((m > 49).sum()),
                    "begge": int(((c > 49) & (m > 49)).sum())},
        "MAE_konstant_mot_del_av_H_katalog": _rl(mae_konstant_mot_del(recs, "sete_kat"), 3),
    }
    if boot:
        bb = F.klyngebootstrap(recs, kjerne)
        ut["ki95"] = {"r2_log": _ki(bb[:, 0]), "stiging_log": _ki(bb[:, 1]), "MAE": _ki(bb[:, 2]),
                      "feil_mot_fotavtrykk_gitt_H": _ki(bb[:, 3])}
    return ut


def _feiltabell(recs, nokkel):
    ut = {}
    for r in recs:
        g = nokkel(r)
        if g is not None:
            ut.setdefault(g, []).append(r["sete_mesh"] - r["sete_kat"])
    return {g: {"n": len(v), "medianfeil": _r(np.median(v), 2), "snittfeil": _r(np.mean(v), 2),
                "MAE": _r(np.mean(np.abs(v)), 2)} for g, v in sorted(ut.items())}


def g0(kal, boot=True):
    """kal: chairs with catalogue AND usable mesh seat height. -> (table dict, gate list)."""
    va = [r for r in kal if r["museum"] == "VA"]
    nm = [r for r in kal if r["museum"] == "NM"]
    tab = {"samla": _g0_gruppe(kal, DEV_MEDIAN_KAT["samla"], boot),
           "VA": _g0_gruppe(va, DEV_MEDIAN_KAT["VA"], boot),
           "NM": _g0_gruppe(nm, DEV_MEDIAN_KAT["NM"], boot),
           "feil_etter_materialklasse": {mu: _feiltabell(rs, lambda r: r["materialklasse"])
                                         for mu, rs in (("samla", kal), ("VA", va), ("NM", nm))},
           "feil_etter_periode": {mu: _feiltabell(rs, lambda r: _periode(r["aar"]) if r["aar"] is not None else None)
                                  for mu, rs in (("samla", kal), ("VA", va), ("NM", nm))},
           "VA_feil_etter_setekonvensjon": _feiltabell(va, lambda r: r["sete_konvensjon"])}
    # ---- the E3 side of the gate: V&A chairs with a year
    va_aar = [r for r in va if r["aar"] is not None]
    kop = {}
    for namn, rs in (("VA", va_aar), ("VA_Stol", [r for r in va_aar if r["type"] == "Stol"]),
                     ("VA_Armstol", [r for r in va_aar if r["type"] == "Armstol"]),
                     ("NM", [r for r in nm if r["aar"] is not None])):
        if len(rs) < 12:
            kop[namn] = {"n": len(rs), "merknad": "too few chairs"}
            continue
        af, af_sd = artefakt(rs, "feil")
        ar, ar_sd = artefakt(rs, "rest")
        kop[namn] = {"n": len(rs),
                     "mesh_koeffisient": _r(e3_stat(rs)),
                     "katalog_koeffisient": _r(e3_stat(rs, y=[r["sete_kat"] for r in rs])),
                     "artefakt_feil_behalden": _r(af), "sd_over_stokkingar_feil": _r(af_sd),
                     "artefakt_rest_behalden": _r(ar), "sd_over_stokkingar_rest": _r(ar_sd)}
    for konv in ("rail", "topp"):
        rs = [r for r in va_aar if r["sete_konvensjon"] == konv]
        kop["VA_" + konv] = {"n": len(rs), "katalog_koeffisient": _r(e3_stat(rs, y=[r["sete_kat"] for r in rs])),
                             "mesh_koeffisient": _r(e3_stat(rs))}
    if boot and len(va_aar) >= 12:
        kop["VA"]["ki95_katalog_koeffisient"] = _ki(
            F.klyngebootstrap(va_aar, lambda rs: e3_stat(rs, y=[r["sete_kat"] for r in rs])))
    tab["kopling"] = kop

    def les(d, *vei):
        for k in vei:
            d = d.get(k) if isinstance(d, dict) else None
        return d
    r2s, r2v = les(tab, "samla", "r2_log"), les(tab, "VA", "r2_log")
    afv, arv, kkv = les(kop, "VA", "artefakt_feil_behalden"), les(kop, "VA", "artefakt_rest_behalden"), \
        les(kop, "VA", "katalog_koeffisient")
    n_va = len(va)
    port = [
        {"namn": "n_VA", "gjeld": ["E1", "E3"], "verdi": n_va, "terskel": G0_N_MIN_VA, "ok": bool(n_va >= G0_N_MIN_VA)},
        {"namn": "r2_samla", "gjeld": ["E1"], "verdi": r2s, "terskel": G0_R2_GOLV_SAMLA,
         "ok": bool(r2s is not None and r2s >= G0_R2_GOLV_SAMLA)},
        {"namn": "r2_VA", "gjeld": ["E1"], "verdi": r2v, "terskel": G0_R2_GOLV_VA,
         "ok": bool(r2v is not None and r2v >= G0_R2_GOLV_VA)},
        {"namn": "artefakt_strukt_VA", "gjeld": ["E3"], "verdi": arv, "terskel": G0_ARTEFAKT_STRUKT_MIN,
         "ok": bool(arv is not None and arv >= G0_ARTEFAKT_STRUKT_MIN)},
        {"namn": "katalogkoeffisient_VA", "gjeld": ["E3"], "verdi": kkv, "terskel": 0.0,
         "ok": bool(kkv is not None and kkv < 0.0)},
    ]
    tab["port_instruks_ikkje_bindande"] = {
        "namn": "artefakt_spes_VA", "verdi": afv, "terskel": G0_ARTEFAKT_SPES_MIN,
        "ville_gjeve_ugyldig": bool(afv is None or afv < G0_ARTEFAKT_SPES_MIN),
        "merknad": "the instruction's literal gate on the error-kept artefact; printed, not used (see module docstring)"}
    return tab, port


# ============================================================================ positive controls
def kontroll_k1(sete_ok, boot=True):
    """K1: fall of the 90th percentile of mesh seat height, before 1700 against 1945 and after, H >= 80 cm."""
    med = [r for r in sete_ok if r["aar"] is not None]

    def delar(rs, hmin):
        a = [r["sete_mesh"] for r in rs if r["aar"] < 1700 and r["H"] >= hmin]
        b = [r["sete_mesh"] for r in rs if r["aar"] >= 1945 and r["H"] >= hmin]
        return a, b

    def fall(rs, hmin=K1_HMIN):
        a, b = delar(rs, hmin)
        if len(a) < 3 or len(b) < 3:
            return float("nan")
        return float(np.percentile(a, 90) - np.percentile(b, 90))
    a, b = delar(med, K1_HMIN)
    a0, b0 = delar(med, 0.0)
    f = fall(med)
    avgjord = len(a) >= K1_N_MIN and len(b) >= K1_N_MIN
    ut = {"namn": "K1", "fall_p90_cm": _r(f, 2), "terskel": K1_FALL,
          "n_foer_1700": len(a), "n_fraa_1945": len(b),
          "tapt_paa_H_under_80": {"foer_1700": len(a0) - len(a), "fraa_1945": len(b0) - len(b)},
          "p90_foer_1700": _r(np.percentile(a, 90), 2) if a else None,
          "p90_fraa_1945": _r(np.percentile(b, 90), 2) if b else None,
          "fall_utan_H_grense": _r(fall(med, 0.0), 2),
          "per_museum": {mu: {"fall_p90_cm": _r(fall([r for r in med if r["museum"] == mu]), 2),
                              "n": [len(x) for x in delar([r for r in med if r["museum"] == mu], K1_HMIN)]}
                         for mu in ("NM", "VA")},
          "utan_katalogsete": {"fall_p90_cm": _r(fall([r for r in med if r["sete_kat"] is None]), 2),
                               "n": [len(x) for x in delar([r for r in med if r["sete_kat"] is None], K1_HMIN)]},
          "avgjord": bool(avgjord),
          "held": bool(avgjord and math.isfinite(f) and f >= K1_FALL)}
    ut["status"] = "held" if ut["held"] else ("failed" if avgjord else "ikkje avgjord (too few chairs in a period)")
    if boot and avgjord:
        ut["ki95"] = _ki(F.klyngebootstrap(med, fall))
    return ut


def barneregel(barn, p10, p90, frac_median):
    """K2 scoring. barn: records with keys namn, H, sete_mesh (None = no usable mesh seat).
    p10, p90: adult 10th and 90th percentile of mesh seat height (cm), used for the reported lines only;
    frac_median: adult median of sete_mesh / H."""
    hog = [r for r in barn if K2_HOG_NAMN in (r["namn"] or "").lower()]
    lag = [r for r in barn if K2_HOG_NAMN not in (r["namn"] or "").lower()]
    har = lambda rs: [r for r in rs if r["sete_mesh"] is not None]
    d = [r["sete_mesh"] - frac_median * r["H"] for r in har(hog)]
    k = sum(1 for x in d if x >= K2_HOG_MARGIN)
    n_hog = len(har(hog))
    krav = int(math.ceil(K2_HOG_DEL * n_hog))
    avgjord = n_hog >= K2_HOG_N_MIN
    held = bool(avgjord and k >= krav)
    return {"namn": "K2", "n_hog": len(hog), "n_hog_med_mesh": n_hog, "k_hog": k, "krav_k_hog": krav,
            "d_cm": _rl(sorted(d), 1), "margin_cm": K2_HOG_MARGIN,
            "hoge_over_vaksen_p90": sum(1 for r in har(hog) if r["sete_mesh"] > p90),
            "laage_rapportert": {"n": len(lag), "n_med_mesh": len(har(lag)),
                                 "under_vaksen_p10": sum(1 for r in har(lag) if r["sete_mesh"] < p10),
                                 "merknad": "not scored: any instrument that scales with H puts a low chair low"},
            "utanfor_vaksenbandet_av_alle": sum(1 for r in har(barn) if r["sete_mesh"] < p10 or r["sete_mesh"] > p90),
            "utanfor_bandet_for_eit_instrument_som_gjev_typisk_del_av_H":
                sum(1 for r in barn if frac_median * r["H"] < p10 or frac_median * r["H"] > p90),
            "vaksen_p10": _r(p10, 2), "vaksen_p90": _r(p90, 2), "vaksen_median_setedel": _r(frac_median),
            "avgjord": bool(avgjord), "held": held,
            "status": "held" if held else ("failed" if avgjord else "ikkje avgjord (too few high chairs with a mesh seat)")}


def kontroll_k2(utval, sete_ok):
    """K2: children's chairs. Runs only on the held-out side (their mesh values are sealed)."""
    if utval != "held":
        return {"namn": "K2", "status": "ikkje køyrd (the mesh values of children's chairs are sealed)",
                "held": None, "avgjord": False}
    m = np.array([r["sete_mesh"] for r in sete_ok])
    frac = np.array([r["sete_mesh"] / r["H"] for r in sete_ok])
    barn = []
    for r in F.les_ekstra("barnestol"):          # GUARDED
        ok, grunn = _laus(r)
        barn.append({"id": r["id"], "namn": r["namn"], "H": r["H"], "aar": r["aar"],
                     "sete_mesh": r["sete_mesh"] if ok else None, "grunn": grunn})
    ut = barneregel(barn, float(np.percentile(m, 10)), float(np.percentile(m, 90)), float(np.median(frac)))
    ut["stolar"] = [{"id": b["id"], "namn": b["namn"], "H": b["H"], "sete_mesh": b["sete_mesh"], "meshregel": b["grunn"]}
                    for b in barn]
    ut["n_vaksne_i_referansen"] = len(sete_ok)
    return ut


# ============================================================================ the run
def _utval(utval):
    """-> dict of the samples of one run. utval in {'dev', 'held'}; 'held' is guarded inside felles."""
    if utval not in ("dev", "held"):
        raise ValueError("utval må vere 'dev' eller 'held'")
    alle = F.les(utval)
    sil = F.silhuett(utval)
    merke = {r["id"]: _seteregel(r, sil) for r in alle}
    laus = {r["id"]: _laus(r) for r in alle}
    sete_ok, tap_alle = _sil(alle, "alle stolar i utvalet", merke)
    med_kat = [r for r in alle if r["sete_kat"] is not None]
    kal, tap_kal = _sil(med_kat, "stolar med katalogsete (G0)", merke)
    if utval == "held":
        prim_inn = [r for r in alle if r["sete_kat"] is None]
        merknad = "held-out chairs WITHOUT catalogue seat height"
    else:
        prim_inn = list(alle)
        merknad = "DEV stand-in: every DEV chair has a catalogue seat height, so the catalogued chairs are used"
    va_inn = [r for r in prim_inn if r["museum"] == "VA"]
    nm_inn = [r for r in prim_inn if r["museum"] == "NM"]
    va, tap_va = _sil(va_inn, "V&A, primærutval", merke)
    nm, tap_nm = _sil(nm_inn, "Nasjonalmuseet, rapportert", merke)
    return {"utval": utval, "alle": alle, "sil": sil, "sete_ok": sete_ok, "kal": kal, "va": va, "nm": nm,
            "va_laus": _sil(va_inn, "", laus)[0], "kal_laus": _sil(med_kat, "", laus)[0], "merknad": merknad,
            "fraafall": {"alle": tap_alle, "G0": tap_kal, "VA": tap_va, "NM": tap_nm}}


def _kjoer_e1(u, port_g0, g0tab, boot=True):
    va, nm = u["va"], u["nm"]
    hoved = _e1_linje(va, boot)
    korr = hoved["forhold_korrigert"]
    ovre = hoved.get("ki95_korrigert", [None, None])[1]
    port = [p for p in port_g0 if "E1" in p["gjeld"]]
    port.append({"namn": "n", "verdi": len(va), "terskel": E_N_MIN, "ok": bool(len(va) >= E_N_MIN)})
    port_ok = all(p["ok"] for p in port)
    a = bool(korr is not None and korr < E1_TERSKEL)
    b = bool(ovre is not None and ovre < E1_OVRE)
    primaer = [
        {"namn": "E1a corrected ratio", "verdi": korr, "ki95": hoved.get("ki95_korrigert"), "terskel": E1_TERSKEL,
         "retning": "<", "held": a},
        {"namn": "E1b upper 95 % bound of the corrected ratio", "verdi": ovre, "ki95": hoved.get("ki95_korrigert"),
         "terskel": E1_OVRE, "retning": "<", "held": b},
    ]
    dom = "UGYLDIG" if not port_ok else ("HELDT" if (a and b) else "SLO FEIL")

    # ---- secondary lines (no verdict)
    sek = {"hovudlinje": hoved, "K_brukt": K_KOMPRESJON}
    uk = hoved["forhold_ukorrigert"]
    b_held = (g0tab.get("VA") or {}).get("stiging_log")
    sek["andre_korreksjonar"] = {
        "K=1 (ingen)": uk, "K=1.25 (meldar, samla spreiingsforhold)": _r(K_MELDAR * uk) if uk is not None else None,
        "K=1/stiging_log paa G0-stolane i V&A": _r(uk / b_held) if (uk is not None and b_held and b_held > 0) else None,
        "stiging_log_G0_VA": b_held}
    med_aar = [r for r in va if r["aar"] is not None]
    sek["periodesentrert"] = _e1_linje(med_aar, boot, sentrer=True)
    sek["MAD_variant"] = _e1_linje(va, boot, spreiing=F.mad_sd)
    sek["laus_meshregel"] = _e1_linje(u["va_laus"], boot)
    sek["laus_meshregel"]["merknad"] = "without felles.kvalitet(); on DEV the slope of this sample is 0.77, so its own factor would be 1.30"
    sek["NM_rapportert"] = _e1_linje(nm, boot)
    sek["NM_rapportert"]["merknad"] = "not scored; the V&A factor K is applied for the record only (DEV NM slope is 0.27)"
    sek["samla_VA_og_NM"] = _e1_linje(va + nm, boot)
    ev = eigenretning(va)
    sek["eigenretning"] = {"lading_sete_H_B_D": _rl(ev[:4], 3), "sum_halv": _r(ev[4], 3), "sd_langs_retninga": _r(ev[5]),
                           "rsd_log_sete": _r(ev[6])}
    if boot and len(va) >= 10:
        bb = F.klyngebootstrap(va, lambda rs: eigenretning(rs)[[0, 4]])
        sek["eigenretning"]["ki95_lading_sete"] = _ki(bb[:, 0])
        sek["eigenretning"]["ki95_sum_halv"] = _ki(bb[:, 1])
    sek["eigenretning"]["lesing"] = "a proportion has sum_halv = 0; the size-factor model predicts loadings summing to zero"
    felt, _ = _felt(va, u["sil"], boot)
    sek["variansfelt"] = felt
    mk = mae_konstant_mot_del(va)
    sek["MAE_konstant_mot_del_av_H_mesh"] = {"MAE_konstant": _r(mk[0], 2), "MAE_del_av_H": _r(mk[1], 2), "forhold": _r(mk[2], 3)}
    if boot and len(va) >= 5:
        sek["MAE_konstant_mot_del_av_H_mesh"]["ki95_forhold"] = _ki(F.klyngebootstrap(va, lambda rs: mae_konstant_mot_del(rs)[2]))
    sek["del_over_49_etter_periode"] = del_over_49(va)
    sek["sensur"] = {"topp_ved_kant": sum(1 for r in va if "topp_ved_kant" in r["flagg"]),
                     "fleire_toppar": sum(1 for r in va if "fleire_toppar" in r["flagg"]),
                     "merknad": "the seat detector searches 0.25 H to 0.65 H only"}
    return {"id": "E1", "utval": u["utval"], "utvalsmerknad": u["merknad"], "n": len(va),
            "fraafall": u["fraafall"]["VA"], "port": port, "primaer": primaer, "sekundaer": sek, "dom": dom}


def _kjoer_e3(u, port_g0, boot=True):
    va = [r for r in u["va"] if r["aar"] is not None]
    nm = [r for r in u["nm"] if r["aar"] is not None]
    stol = [r for r in va if r["type"] == "Stol"]
    arm = [r for r in va if r["type"] == "Armstol"]
    alle_l, stol_l = _e3_linje(va, boot), _e3_linje(stol, boot)
    ovre = alle_l.get("ki95", [None, None])[1]
    punkt_stol = stol_l["verdi"]
    bd = F.partial_spearman([r["B"] for r in va], [r["D"] for r in va], [[r["H"] for r in va], [_bolk(r) for r in va]]) \
        if len(va) >= 8 else float("nan")
    sh = F.spearman([r["sete_mesh"] for r in va], [r["H"] for r in va])
    port = [p for p in port_g0 if "E3" in p["gjeld"]]
    port += [
        {"namn": "kontrollpar B~D", "verdi": _r(bd), "terskel": 0.0, "ok": bool(math.isfinite(bd) and bd > 0)},
        {"namn": "kontrollpar sete~H", "verdi": _r(sh), "terskel": 0.0, "ok": bool(math.isfinite(sh) and sh > 0)},
        {"namn": "n", "verdi": len(va), "terskel": E_N_MIN, "ok": bool(len(va) >= E_N_MIN)},
        {"namn": "n_Stol", "verdi": len(stol), "terskel": E3_N_MIN_STOL, "ok": bool(len(stol) >= E3_N_MIN_STOL)},
    ]
    port_ok = all(p["ok"] for p in port)
    dom, tekst, a, b = _e3_dom(ovre, punkt_stol)
    if not port_ok:
        dom, tekst = "UGYLDIG", "a gate fixed in advance failed: " + ", ".join(p["namn"] for p in port if not p["ok"])
    primaer = [
        {"namn": "E3a all types: upper 95 % bound", "verdi": ovre, "punktestimat": alle_l["verdi"], "ki95": alle_l.get("ki95"),
         "terskel": E3_ARTEFAKT, "retning": "<", "held": a},
        {"namn": "E3b type 'Stol': point estimate", "verdi": punkt_stol, "ki95": stol_l.get("ki95"),
         "terskel": E3_STOL_TERSKEL, "retning": "<=", "held": b},
    ]
    d2, _, a2, b2 = _e3_dom(ovre, punkt_stol, E3_ARTEFAKT_SPES, E3_ARTEFAKT_SPES)
    laus = [r for r in u["va_laus"] if r["aar"] is not None]
    sek = {"alle_typar": alle_l, "Stol": stol_l, "Armstol": _e3_linje(arm, boot),
           "under_referansen_i_instruksen": {"referanse": E3_ARTEFAKT_SPES, "E3a": a2, "E3b": b2, "konjunksjon": d2,
                                             "merknad": "what the conjunction would give with the instruction's artefact value for both parts; no verdict"},
           "NM_rapportert": _e3_linje(nm, boot),
           "raa_spearman_sete_fotavtrykk": _r(F.spearman([r["sete_mesh"] for r in va], [math.sqrt(r["B"] * r["D"]) for r in va])),
           "med_D_i_staden_for_fotavtrykk": _r(e3_stat(va, x=[r["D"] for r in va])),
           "med_B_i_staden_for_fotavtrykk": _r(e3_stat(va, x=[r["B"] for r in va])),
           "typefordeling": {t: sum(1 for r in va if r["type"] == t) for t in sorted({r["type"] for r in va})},
           "laus_meshregel": {"alle_typar": _e3_linje(laus, boot),
                              "Stol": _e3_linje([r for r in laus if r["type"] == "Stol"], boot),
                              "merknad": "without felles.kvalitet(); on DEV the structural artefact of this sample is -0.20"}}
    tap = dict(u["fraafall"]["VA"])
    tap["utan_aar"] = len(u["va"]) - len(va)
    return {"id": "E3", "utval": u["utval"], "utvalsmerknad": u["merknad"], "n": len(va), "n_Stol": len(stol),
            "fraafall": tap, "port": port, "primaer": primaer, "sekundaer": sek, "dom": dom, "domstekst": tekst}


def kjoer(utval, boot=True):
    """The whole module on one sample. utval in {'dev', 'held'}. -> JSON-serialisable dict.
    boot=False skips every bootstrap (quick checks); verdicts then cannot be HELDT."""
    u = _utval(utval)                            # 'held' is guarded inside felles
    g0tab, port_g0 = g0(u["kal"], boot)
    g0tab["laus_meshregel"] = {"VA": _g0_gruppe([r for r in u["kal_laus"] if r["museum"] == "VA"], DEV_MEDIAN_KAT["VA"], False),
                               "NM": _g0_gruppe([r for r in u["kal_laus"] if r["museum"] == "NM"], DEV_MEDIAN_KAT["NM"], False)}
    k1 = kontroll_k1(u["sete_ok"], boot)
    k2 = kontroll_k2(utval, u["sete_ok"])
    if utval == "dev":
        flagg = not k1["held"]
        flagg_tekst = "K2 cannot run on DEV; the flag follows K1 alone here"
    else:
        flagg = (not k1["held"]) and (not k2.get("held"))
        flagg_tekst = "both positive controls failed or were not decided: every mesh-seat result is flagged" if flagg \
            else "at least one positive control held"
    e1 = _kjoer_e1(u, port_g0, g0tab, boot)
    e3 = _kjoer_e3(u, port_g0, boot)
    m = np.array([r["sete_mesh"] for r in u["sete_ok"]])
    return {
        "id": "T1", "utval": utval, "n_boot": F.N_BOOT if boot else 0, "froe": F.FRO,
        "n": {"alle": len(u["alle"]), "med_brukande_meshsete": len(u["sete_ok"]), "G0": len(u["kal"]),
              "E1_VA": e1["n"], "E3_VA": e3["n"], "E3_VA_Stol": e3["n_Stol"], "NM_rapportert": len(u["nm"])},
        "fraafall": u["fraafall"],
        "vaksne_meshsete": {"p10": _r(np.percentile(m, 10), 2), "median": _r(np.median(m), 2), "p90": _r(np.percentile(m, 90), 2),
                            "median_setedel": _r(np.median([r["sete_mesh"] / r["H"] for r in u["sete_ok"]]))},
        "G0": {"tabell": g0tab, "port": port_g0},
        "kontrollar": {"K1": k1, "K2": k2, "instrumentflagg": bool(flagg), "flaggtekst": flagg_tekst},
        "delar": {"E1": e1, "E3": e3},
        # flat view of the module contract
        "port": [dict(p, hypotese="E1") for p in e1["port"]] + [dict(p, hypotese="E3") for p in e3["port"]],
        "primaer": [dict(p, hypotese="E1") for p in e1["primaer"]] + [dict(p, hypotese="E3") for p in e3["primaer"]],
        "sekundaer": {"E1": e1["sekundaer"], "E3": e3["sekundaer"]},
        "dom": {"E1": e1["dom"], "E3": e3["dom"], "E3_tekst": e3["domstekst"], "instrumentflagg": bool(flagg)},
    }


# ============================================================================ figure data
def figurdata(utval):
    """What one figure needs: the stacked side-silhouette occupancy map under both registrations (integer per
    cent, rows 0-109 from the floor, columns 25-134), per-chair (H, mesh seat) points of the primary sample, the
    spread ratios and the gate table. No bootstrap. Under 300 KB."""
    u = _utval(utval)
    va = u["va"]
    felt, fd = _felt(va, u["sil"], boot=False)
    kart = None
    if fd is not None:
        r0, r1, c0, c1 = 0, 110, 25, 135
        pst = lambda A: np.rint(100.0 * A[:, r0:r1, c0:c1].mean(axis=0)).astype(int).tolist()
        kart = {"rader": [r0, r1 - 1], "kolonnar": [c0, c1 - 1],
                "eining": "per cent of chairs covering the pixel; 1 cm per pixel; row 0 = floor; column 0 = back",
                "golvfesta": pst(fd["side_golv"]), "hogdnormalisert": pst(fd["side_norm"]),
                "hogdnormalisert_til_rad": FELT_HREF, "n": fd["n"]}
    g0tab, port_g0 = g0(u["kal"], boot=False)
    v = e1_vektor(va)
    vn = e1_vektor(u["nm"])
    korr = lambda t: {k: t.get(k) for k in ("n", "MAE_mesh_mot_katalog", "MAE_konstant_devmedian", "medianfeil", "spearman",
                                            "r2_log", "stiging_log", "feil_mot_fotavtrykk_gitt_H")} if isinstance(t, dict) else None
    va_aar = [r for r in va if r["aar"] is not None]
    ut = {
        "id": "T1", "utval": utval,
        "kart_side": kart, "variansfelt": felt,
        "punkt_VA": {"kolonnar": ["H", "sete_mesh", "aar", "fotavtrykk", "er_Stol"],
                     "rader": [[_r(r["H"], 1), _r(r["sete_mesh"], 1), r["aar"], _r(math.sqrt(r["B"] * r["D"]), 1),
                                int(r["type"] == "Stol")] for r in va]},
        "punkt_NM": {"kolonnar": ["H", "sete_mesh", "aar"],
                     "rader": [[_r(r["H"], 1), _r(r["sete_mesh"], 1), r["aar"]] for r in u["nm"]]},
        "spreiing": {"VA": {"rsd_log_sete_H_B_D": _rl(v[1:]), "forhold_ukorrigert": _r(v[0]), "forhold_korrigert": _r(K_KOMPRESJON * v[0])},
                     "NM": {"rsd_log_sete_H_B_D": _rl(vn[1:]), "forhold_ukorrigert": _r(vn[0])},
                     "K": K_KOMPRESJON, "terskel": E1_TERSKEL, "grunnmodell": 1.0},
        "E3": {"referanse": E3_ARTEFAKT, "terskel_Stol": E3_STOL_TERSKEL, "referanse_instruks": E3_ARTEFAKT_SPES,
               "alle_typar": _r(e3_stat(va_aar)), "Stol": _r(e3_stat([r for r in va_aar if r["type"] == "Stol"]))},
        "porttabell": {"samla": korr(g0tab.get("samla")), "VA": korr(g0tab.get("VA")), "NM": korr(g0tab.get("NM")),
                       "kopling": g0tab.get("kopling"), "port": port_g0},
    }
    storleik = len(json.dumps(ut, ensure_ascii=False))
    if storleik >= 300000:
        raise RuntimeError("figurdata er for stor: %d teikn" % storleik)
    ut["storleik_teikn"] = storleik
    return ut


# ============================================================================ synthetic control
def _syn_grupper(suitar):
    """Index arrays of the suites, in order of first appearance (as felles.klyngebootstrap groups them)."""
    grupper = {}
    for i, s in enumerate(suitar):
        grupper.setdefault(s, []).append(i)
    return [np.array(v) for v in grupper.values()]


def _syn_boot_idx(g, n, rng):
    """Index resample that draws whole suites with replacement (as felles.klyngebootstrap does).
    g = None: every chair is its own suite."""
    if g is None:
        return rng.integers(0, n, n)
    return np.concatenate([g[j] for j in rng.integers(0, len(g), len(g))])


def _syn_e1_ein(X, rng):
    """X: array (n, 4) of seat, H, B, D (each chair its own cluster). -> (corrected ratio, upper bound, verdict)."""
    def forhold(A):
        L = np.log(A)
        s = [rsd(L[:, j]) for j in range(4)]
        return s[0] / min(s[1:])
    n = len(X)
    punkt = K_KOMPRESJON * forhold(X)
    b = np.array([K_KOMPRESJON * forhold(X[rng.integers(0, n, n)]) for _ in range(SYN_BOOT)])
    ovre = float(np.nanpercentile(b, 97.5))
    return punkt, ovre, ("HELDT" if _e1_dom(punkt, ovre) else "SLO FEIL")


def _syn_e3_ein(kjerne, y, grupper, rng):
    """One synthetic E3 population -> (point all, upper bound all, point Stol, verdict).
    grupper: suite index arrays of _syn_grupper(), or None when every chair is its own suite."""
    punkt = kjerne.stat(y)
    b = np.array([kjerne.stat(y, _syn_boot_idx(grupper, kjerne.n, rng)) for _ in range(SYN_BOOT)])
    ovre = float(np.nanpercentile(b, 97.5))
    stol = np.nonzero(kjerne.typ == "Stol")[0]
    ps = kjerne.stat(y, stol) if len(stol) >= 8 else float("nan")
    return punkt, ovre, ps, _e3_dom(ovre, ps)[0]


def _plant(kjerne, verdiar, lam, rng):
    """Assign the given seat values to the chairs so that their partial coupling with footprint (given H and period)
    is about -lam: latent z = -lam * e + sqrt(1 - lam^2) * noise, e = standardised residual of rank(footprint) on
    [rank(H), period dummies]; the sorted values are handed out in the order of z."""
    D = kjerne.D[:, kjerne.D.any(axis=0)]
    Z = np.column_stack([rankdata(kjerne.H), D])
    rx = rankdata(kjerne.x)
    e = rx - Z @ np.linalg.lstsq(Z, rx, rcond=None)[0]
    e = e / e.std()
    z = -lam * e + math.sqrt(1.0 - lam * lam) * rng.standard_normal(len(e))
    ut = np.empty(len(e))
    ut[np.argsort(z)] = np.sort(verdiar)
    return ut


def _sjolvsjekk(dev_va_aar):
    """The fast kernel must reproduce felles.partial_spearman."""
    k = _E3Kjerne(dev_va_aar)
    a = k.stat(_kol(dev_va_aar, "sete_mesh"))
    b = e3_stat(dev_va_aar)
    if not (abs(a - b) < 1e-9):
        raise AssertionError("_E3Kjerne (%.6f) avvik frå felles.partial_spearman (%.6f)" % (a, b))
    return a


def syntetisk_kontroll(runs=SYN_RUNS):
    """The scoring code of E1, E3 and K2 on synthetic populations built from DEV chairs (never held-out).
    Every population has SYN_N = 700 chairs unless the line says DEV size; each chair is then its own cluster.
    Bootstrap inside a run: SYN_BOOT = 300 resamples (kjoer uses 2000). Gates are not simulated.
    Requirement: base-model populations give HELDT in at most 10 % of runs, planted effects in at least 80 %."""
    dev = F.les("dev")
    sil = F.silhuett("dev")
    vaksne = [r for r in dev if _seteregel(r, sil)[0]]
    va = [r for r in vaksne if r["museum"] == "VA"]
    va_aar = [r for r in va if r["aar"] is not None]
    ut = {"runs": runs, "n_syntetisk": SYN_N, "n_boot_i_kvar_koeyring": SYN_BOOT,
          "grunnlag": "DEV V&A chairs that pass SETEREGEL (n = %d; with a year %d)" % (len(va), len(va_aar))}

    # ------------------------------------------------------------------ E1
    lc, lm = np.log(_kol(va, "sete_kat")), np.log(_kol(va, "sete_mesh"))
    b_log, a_log = np.polyfit(lc, lm, 1)
    res_log = lm - (a_log + b_log * lc)
    HBD = np.column_stack([_kol(va, "H"), _kol(va, "B"), _kol(va, "D")])
    med = np.median(HBD, axis=0)
    t_med = float(np.median(_kol(va, "sete_kat")))
    g = np.cbrt(HBD.prod(axis=1))
    g = g / np.median(g)
    s_min = min(rsd(np.log(HBD[:, j])) for j in range(3))
    instrument = lambda t, e: np.exp(a_log + b_log * np.log(t) + e)
    e1 = {"instrumentmodell": {"log_mesh = a + b log_true + e": [_r(a_log), _r(b_log)], "rsd_e": _r(rsd(res_log)),
                               "rsd_log_storleik": _r(rsd(np.log(g))), "minste_rsd_log_HBD": _r(s_min),
                               "K_x_b": _r(K_KOMPRESJON * b_log)}}

    def e1_scenario(namn, bygg, froe):
        rng = np.random.default_rng(F.FRO + froe)
        res = [_syn_e1_ein(bygg(rng), rng) for _ in range(runs)]
        k = np.array([x[0] for x in res])
        e1[namn] = {"korrigert_forhold_median": _r(np.median(k), 3), "spenn_5_95": _rl(np.percentile(k, [5, 95]), 3),
                    "ukorrigert_median": _r(np.median(k) / K_KOMPRESJON, 3),
                    "del_HELDT": _r(np.mean([x[2] == "HELDT" for x in res]), 3)}
        return e1[namn]

    def storleik(rng, stoy=True):
        i = rng.integers(0, len(va), SYN_N)
        e = res_log[rng.integers(0, len(va), SYN_N)] if stoy else 0.0
        return np.column_stack([instrument(t_med * g[i], e), med[0] * g[i], med[1] * g[i], med[2] * g[i]])

    def halden(rng, rho):
        i = rng.integers(0, len(va), SYN_N)
        t = t_med * np.exp(rho * s_min * rng.standard_normal(SYN_N))
        return np.column_stack([instrument(t, res_log[rng.integers(0, len(va), SYN_N)]), HBD[i]])

    def dev_som_han_er(rng):
        i = rng.integers(0, len(va), SYN_N)
        return np.column_stack([_kol(va, "sete_mesh")[i], HBD[i]])

    a1 = e1_scenario("a_rein_storleik_med_DEV_stoey", lambda rng: storleik(rng, True), 1)
    a1["bygd"] = ("BASE MODEL: every chair is the median chair times its own size factor (cube root of H x B x D of a DEV chair); "
                  "true seat, H, B, D have identical log spread (true ratio 1); mesh = instrument(true seat) + a DEV residual")
    a0 = e1_scenario("a0_rein_storleik_utan_stoey", lambda rng: storleik(rng, False), 2)
    a0["bygd"] = "the same without instrument noise: the worst case for the correction (uncorrected ratio = slope b)"
    b30 = e1_scenario("b_halden_sann_0.30", lambda rng: halden(rng, 0.30), 3)
    b30["bygd"] = ("PLANTED EFFECT: true seat independent of size with log spread 0.30 x the smallest log spread of H, B, D "
                   "(real DEV H, B, D); mesh = instrument(true seat) + a DEV residual")
    b45 = e1_scenario("b_halden_sann_0.45", lambda rng: halden(rng, 0.45), 4)
    b45["bygd"] = "PLANTED EFFECT with true ratio 0.45, the value of the V&A catalogue on DEV"
    b60 = e1_scenario("b_halden_sann_0.60", lambda rng: halden(rng, 0.60), 5)
    b60["bygd"] = "the same with true ratio 0.60"
    b00 = e1_scenario("b_halden_sann_0.00", lambda rng: halden(rng, 0.0), 6)
    b00["bygd"] = "every chair has the same true seat height: the floor of the statistic with DEV noise"
    bd = e1_scenario("b0_DEV_VA_oppskalert", dev_som_han_er, 7)
    bd["bygd"] = ("the real DEV V&A chairs with their real mesh seats, resampled to n = 700; this line carries the sampling "
                  "uncertainty of the DEV chairs themselves, not that of 700 new chairs")
    e1["krav"] = {"a_grunnmodell_ikkje_HELDT": bool(a1["del_HELDT"] <= 0.10 and a0["del_HELDT"] <= 0.10),
                  "b_planta_effekt_HELDT": bool(b45["del_HELDT"] >= 0.80)}
    ut["E1"] = e1

    # ------------------------------------------------------------------ E3
    sjekk = _sjolvsjekk(va_aar)
    a_cm, b_cm, res_cm = _lineaer(va_aar)
    cat = _kol(va_aar, "sete_kat")
    mesh = _kol(va_aar, "sete_mesh")
    feil = mesh - cat
    kj_dev = _E3Kjerne(va_aar)
    grupper_dev = _syn_grupper([F.suite(r) for r in va_aar])
    e3 = {"instrumentmodell_cm": {"mesh = a + b katalog + rest": [_r(a_cm, 2), _r(b_cm)], "sd_rest": _r(res_cm.std(), 2)},
          "referanse": E3_ARTEFAKT, "terskel_Stol": E3_STOL_TERSKEL, "referanse_instruks": E3_ARTEFAKT_SPES,
          "kjernesjekk_mot_felles": _r(sjekk, 6)}

    def e3_scenario(namn, storleik_n, bygg, froe):
        """bygg(rng, kjerne, idx) -> y vector for the chairs kjerne covers (idx: rows of va_aar)."""
        rng = np.random.default_rng(F.FRO + froe)
        res = []
        for _ in range(runs):
            if storleik_n is None:
                idx = np.arange(len(va_aar))
                kj, grupper = kj_dev, grupper_dev
            else:
                idx = rng.integers(0, len(va_aar), storleik_n)
                kj = _E3Kjerne([va_aar[i] for i in idx])
                grupper = None
            y = bygg(rng, kj, idx)
            p, o, ps, d = _syn_e3_ein(kj, y, grupper, rng)
            d_spes = _e3_dom(o, ps, E3_ARTEFAKT_SPES, E3_ARTEFAKT_SPES)[0]
            res.append((p, o, ps, d, d_spes, o < E3_ARTEFAKT, o < E3_ARTEFAKT_SPES, ps <= E3_STOL_TERSKEL))
        e3[namn] = {"n": len(va_aar) if storleik_n is None else storleik_n,
                    "punkt_median": _r(np.nanmedian([x[0] for x in res]), 3),
                    "ovre_grense_median": _r(np.nanmedian([x[1] for x in res]), 3),
                    "punkt_Stol_median": _r(np.nanmedian([x[2] for x in res]), 3),
                    "del_HELDT": _r(np.mean([x[3] == "HELDT" for x in res]), 3),
                    "del_SLO_FEIL": _r(np.mean([x[3] == "SLO FEIL" for x in res]), 3),
                    "del_E3a_held": _r(np.mean([x[5] for x in res]), 3),
                    "del_E3b_held": _r(np.mean([x[7] for x in res]), 3),
                    "del_E3a_held_under_instruksreferansen": _r(np.mean([x[6] for x in res]), 3),
                    "del_HELDT_under_instruksreferansen": _r(np.mean([x[4] == "HELDT" for x in res]), 3)}
        return e3[namn]

    stokk = lambda rng, idx: cat[idx][rng.permutation(len(idx))]
    s1 = e3_scenario("a1_stokka_feil_behalden_DEV_n", None, lambda rng, kj, idx: stokk(rng, idx) + feil[idx], 11)
    s1["bygd"] = ("THE INSTRUCTION'S NULL: catalogue seats shuffled among the DEV V&A chairs, each chair keeps mesh minus "
                  "catalogue; DEV size, real suites")
    s1b = e3_scenario("a1_stokka_feil_behalden_n700", SYN_N, lambda rng, kj, idx: stokk(rng, idx) + feil[idx], 12)
    s1b["bygd"] = "the same at n = 700"
    s2 = e3_scenario("a2_stokka_rest_behalden_DEV_n", None, lambda rng, kj, idx: a_cm + b_cm * stokk(rng, idx) + res_cm[idx], 13)
    s2["bygd"] = "STRUCTURAL NULL: mesh* = a + b x shuffled catalogue seat + the chair's regression residual; DEV size"
    s2b = e3_scenario("a2_stokka_rest_behalden_n700", SYN_N, lambda rng, kj, idx: a_cm + b_cm * stokk(rng, idx) + res_cm[idx], 14)
    s2b["bygd"] = ("the same at n = 700; 'del_E3a_held_under_instruksreferansen' shows what the reference -0.14 would let "
                   "through on the all-types criterion")
    p15 = e3_scenario("b_planta_0.15_n700", SYN_N, lambda rng, kj, idx: a_cm + b_cm * _plant(kj, cat[idx], 0.15, rng) + res_cm[idx], 15)
    p15["bygd"] = "PLANTED: true seats re-assigned with a partial coupling of about -0.15 with footprint; mesh* = a + b x true + residual"
    p30 = e3_scenario("b_planta_0.30_n700", SYN_N, lambda rng, kj, idx: a_cm + b_cm * _plant(kj, cat[idx], 0.30, rng) + res_cm[idx], 16)
    p30["bygd"] = "PLANTED EFFECT of the size seen in the DEV V&A catalogue (-0.33): partial coupling about -0.30"
    pd = e3_scenario("b0_DEV_VA_oppskalert", SYN_N, lambda rng, kj, idx: mesh[idx], 17)
    pd["bygd"] = ("the real DEV V&A chairs with their real mesh seats, resampled to n = 700; carries the sampling uncertainty "
                  "of the DEV chairs themselves")
    e3["krav"] = {"a_instruksen_sin_null_SLO_FEIL_minst_90": bool(s1["del_SLO_FEIL"] >= 0.90 and s1b["del_SLO_FEIL"] >= 0.90),
                  "a_strukturell_null_SLO_FEIL_minst_90": bool(s2["del_SLO_FEIL"] >= 0.90 and s2b["del_SLO_FEIL"] >= 0.90),
                  "b_planta_effekt_HELDT": bool(p30["del_HELDT"] >= 0.80)}
    ut["E3"] = e3

    # ------------------------------------------------------------------ K2
    m = _kol(vaksne, "sete_mesh")
    p10, p90 = float(np.percentile(m, 10)), float(np.percentile(m, 90))
    fmed = float(np.median(m / _kol(vaksne, "H")))
    a_k, b_k, res_k = _lineaer(va)                      # V&A instrument line and residuals in cm
    rng = np.random.default_rng(F.FRO + 21)
    Hh_alle = np.array(K2_KATALOG_H_HOG)
    n_k2 = 2000
    k2 = {"vaksenreferanse_DEV": {"p10": _r(p10, 1), "p90": _r(p90, 1), "median_setedel": _r(fmed, 3)},
          "instrumentlinje_cm": [_r(a_k, 2), _r(b_k, 3)], "sd_rest_cm": _r(res_k.std(), 2), "del_held": {}}
    for n_mesh in (8, 7, 6, 5):
        tel = {"ser_setet": 0, "blind_del_av_H": 0, "blind_vaksen_cm": 0, "tilfeldig_i_soekjevindauget": 0}
        for _ in range(n_k2):
            Hh = Hh_alle[rng.permutation(8)[:n_mesh]]
            stoy = res_k[rng.integers(0, len(res_k), n_mesh)]
            sett = {
                # an instrument that sees the seat: high-chair seats at 0.574 H (the one catalogued high chair:
                # 58.8 cm at H 102.5), read through the DEV V&A instrument line and noise, capped at 0.65 H
                "ser_setet": np.minimum(a_k + b_k * 0.574 * Hh + stoy, 0.65 * Hh),
                # an instrument that returns the typical adult seat fraction times H, plus the same noise
                "blind_del_av_H": fmed * Hh + stoy,
                # an instrument that returns a draw from the adult centimetre distribution whatever the chair
                "blind_vaksen_cm": m[rng.integers(0, len(m), n_mesh)],
                # a detector that returns a random height inside its search window
                "tilfeldig_i_soekjevindauget": rng.uniform(0.25 * Hh, 0.65 * Hh),
            }
            for namn, s in sett.items():
                barn = [{"namn": "High chair", "H": float(h), "sete_mesh": float(x)} for h, x in zip(Hh, s)]
                tel[namn] += barneregel(barn, p10, p90, fmed)["held"]
        k2["del_held"]["%d_hoge_stolar_med_mesh" % n_mesh] = {k: _r(v / n_k2, 3) for k, v in tel.items()}
    alle_rader = list(k2["del_held"].values())
    k2["krav"] = {"blinde_instrument_fell": bool(all(x["blind_del_av_H"] <= 0.05 and x["blind_vaksen_cm"] <= 0.05 for x in alle_rader)),
                  "sjaaande_instrument_held": bool(all(x["ser_setet"] >= 0.80 for x in alle_rader))}
    k2["atterhald"] = ("the seeing instrument is ASSUMED: high-chair seats at 0.574 H rest on one catalogued chair, and the DEV V&A "
                       "line (mesh = %.1f + %.2f x true) is extrapolated to seats above 55 cm. A detector that returns a random "
                       "height in its window passes more often than 5 %% (line 'tilfeldig_i_soekjevindauget')." % (a_k, b_k))
    ut["K2"] = k2
    ut["alle_krav_oppfylte"] = bool(all(ut["E1"]["krav"].values()) and all(ut["E3"]["krav"].values())
                                    and all(ut["K2"]["krav"].values()))
    return ut


# ============================================================================ main
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"kjoer_dev": kjoer("dev"), "syntetisk_kontroll": syntetisk_kontroll()},
                     ensure_ascii=False, indent=1))
