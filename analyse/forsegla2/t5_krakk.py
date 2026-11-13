#!/usr/bin/env python3
"""t5_krakk.py - N4: THE STOOL. Same goal by other means (props 5.15, 1.0211, 6.672).

Module of the SECOND sealed test (analyse/forsegla2). Run from the repository root:
    python analyse/forsegla2/t5_krakk.py          (DEV stand-in and synthetic controls only; never 'held')

THE ARGUMENT
  A stool has no back, so its catalogued total height is its seat height. If seat height is held against the
  body, and is not a convention copied from chairs as chairs, sitting stools should lie where chair seats lie
  and as tightly. Stools were flagged out of every earlier analysis; their heights are sealed as a group.

BLINDNESS (what this module has and has not seen)
  SEEN (open): names, types, museum, year and presence-of-height counts of the 87 stools (felles.tel_ekstra);
        the catalogue seat heights and total heights of the V&A adult CHAIRS (stools are blanked by the reader).
  NOT SEEN: any stool height, width, depth or seat height, any statistic of them, any raw V&A dimension record
        of a stool. The only reader of stool heights is felles.les_ekstra('krakk'), which is guarded and is
        called from exactly one place, _les('held'). The author never ran that path on the real loader.
  The scoring code was developed on a STAND-IN (DEV chair seat heights + noise) and on synthetic populations.
  There is therefore NO DEV VALUE for stools: every 'dev_verdi' below is the stand-in value and says so.

WHAT IS FROZEN HERE (all literals in SPEC)
  reference values from the V&A adult chairs (recomputed 13 Nov 2026 from open catalogue data; see
  _referanse_fraa_data(), which re-derives them at run time and reports any mismatch without applying it);
  the name rule; the height rule; the gates; the three lines of the primary conjunction; the secondary lines.

VERDICT
  UGYLDIG  if a gate fails;
  HELDT    if all three primary lines hold (one conjunction, named in advance);
  SLO FEIL otherwise.

CHANGE BY THE INDEPENDENT CHECK (13 Nov 2026), marked '[independent check' in _doem()
  The three primary lines are decided on the unrounded statistics ('verdi_uavrunda'), not on the rounded display
  values. No threshold, gate, sample rule or reference literal was changed.
"""
import json
import re
import sys

import numpy as np

import felles

# ====================================================================================================== SPEC
SPEC = {
    "id": "N4",
    "modul": "t5_krakk.py",
    "tittel": "The stool: same goal by other means. Stool height lies where chair seats lie, and as tightly",
    "slag": "ny",
    "proposisjonar": ["5.15", "1.0211", "6.672"],
    "paastand": (
        "A stool has no back, so its catalogued total height is its seat height. If seat height is held against "
        "the body and not copied from chairs as chairs, stools made for sitting with the feet on the floor have "
        "(1) a median height inside the interquartile range of V&A chair seat heights and (2) a robust spread of "
        "height nearer that of chair seat height than that of chair total height."),
    "utval": {
        "kjelde": "felles.les_ekstra('krakk'): type in {Krakk, Stol utan rygg}; 87 objects (NM 2, VA 85)",
        "hogd": ("H as delivered by the loader, accepted when H_kjelde is 'H' (whole-object height of the cleaned "
                 "table) or 'sete' (the record has only a seat-labelled height). H_kjelde 'raa' (first Height of "
                 "an unknown named part) is NOT accepted in the primary sample; it enters the unrestricted line. "
                 "No range filter on height (a range filter on the outcome would manufacture tightness)."),
        "namneregel": ("Dropped when the name matches a term below. Text searched: catalogue 'Namn' with the "
                       "parenthesised maker removed, plus 'Nemning', lower-cased. Terms are regular expressions "
                       "(case-insensitive). Each object is counted under the first group it matches."),
        "namnetermar": [
            # group, regular expression
            ["fotskammel", r"foot[\s-]?stools?|foot[\s-]?rests?|\bhassocks?\b|\bfot(skamm?el|krakk|benk|kvilar|hvilar)\w*"],
            ["knelekrakk", r"\bkneel\w*|prie[\s-]?dieu|\bknele\w*|\bbede(skamm?el|stol|pult)\w*"],
            ["trapp", r"\bsteps?\b|step[\s-]?stools?|step[\s-]?ladders?|\bladders?\b|\b(gardin|bibliotek)?trapp(a|e\w*)?\b|\bstiger?\b"],
            ["barn", r"\bchild(ren)?('s|s')?\b|\bnursery\b|\bbab(y|ies)\b|\binfants?\b|\bbarne(krakk|stol|m(ø|o)bel)\w*"],
            ["barn_namngjeven", r"\bstool thing\b"],
            ["bar_hog", r"\bbar[\s-]?stools?|\bhigh[\s-]?stools?|\btall[\s-]stools?|\bcounter[\s-]?stools?|"
                        r"\bdraughts?man\w*|\bdrafting\b|\bbar(krakk|stol)\w*|\bh(ø|o)ge? krakk|\bh(ø|o)y krakk"],
            ["bord_stativ", r"\btables?\b|\bstands?\b|\bpedestals?\b|\bbord\b|\bbordkrakk\w*|\bpidestall\w*|\bstativ\w*"],
            ["miniatyr_dokke", r"\bminiatures?\b|\bdolls?('s|')?\b|\btoys?\b|\bmaquettes?\b|\bscale model\b|"
                               r"\bminiatyr\w*|\bdokke(stove|hus|m(ø|o)bel|krakk|stol)\w*|\bdukke(stue|hus|m(ø|o)bel|krakk|stol)\w*|"
                               r"\bleiket(ø|o)y\w*|\bleket(ø|o)y\w*"],
        ],
        "namngjeven_grunngjeving": (
            "'Stool Thing' (1968, paper) belongs to Peter Murdoch's children's furniture range 'Those Things' "
            "(Chair Thing, Table Thing, Stool Thing). This is outside knowledge about the object, not about its "
            "height; decided blind and flagged as such."),
        "fraafall_rekkjefolgje": ["namneregel", "utan_hogd", "kjelde_raa", "maal_kopi"],
        "namn_brukbare": ("Names are nearly uninformative: 75 of 87 are the bare type word 'Stool' with or without "
                          "a maker (share with any other word: 12 of 87 = 0.138), and only 1 of those 12 names a "
                          "function (footstool). On the 87 known names the rule removes exactly 2 objects: "
                          "fotskammel 1 (O10416), barn_namngjeven 1 (O370014), every other group 0. The rule "
                          "cannot find a footstool, bar stool or child's stool that is catalogued as 'Stool'."),
        "forventa_n": ("87 - 2 by name - 5 without height - (0 or 1) source 'raa' - copied records = about 79 "
                       "(before 1700: 19, 1700-1899: 29, from 1900: 31)"),
    },
    "referanse": {
        "kjelde": ("stolar_reinsa.csv, museum VA, vaksenstol == '1', maal_ok == '1', sete_ok == '1' (n = 285, 252 "
                   "suites); quantiles by linear interpolation (numpy default); spread = 1.4826 MAD / median"),
        "n_sete": 285,
        "sete_q1": 41.0,            # recomputed 41.000
        "sete_median": 43.8,        # recomputed 43.800
        "sete_q3": 46.0,            # recomputed 46.000
        "sete_p5": 36.0,            # recomputed 36.000
        "sete_p95": 51.8,           # recomputed 51.840
        "sete_spreiing": 0.0779,    # recomputed 0.07785; cluster bootstrap 95 % [0.067, 0.101]
        "H_kjelde": ("all V&A adult chairs with accepted measures (vaksenstol == '1', maal_ok == '1'; n = 1204). "
                     "This is the population that gives the 0.173 named in the specification. On the 285 chairs "
                     "that have a seat height the spread of H is 0.2381; the SMALLER value is frozen because it is "
                     "the stricter one for the theory (lower threshold, lower ceiling)."),
        "n_H": 1204,
        "H_median": 94.0,           # recomputed 94.000
        "H_spreiing": 0.1735,       # recomputed 0.17350
        "H_spreiing_paa_dei_285": 0.2381,
        "periodar": {               # chair seat quartiles by period (aar_fraa), for the secondary lines and the figure
            "foer_1700": {"n": 60, "q1": 42.0, "median": 46.5, "q3": 48.5, "spreiing": 0.0797},
            "1700_1899": {"n": 106, "q1": 41.5, "median": 43.0, "q3": 45.0, "spreiing": 0.0690},
            "fraa_1900": {"n": 117, "q1": 40.5, "median": 43.5, "q3": 45.8, "spreiing": 0.0784},
        },
        "merknad": ("The chair seat heights passed the range filter sete_ok (30-65 cm and below H); stool heights "
                    "pass no range filter. The asymmetry works against the theory. The reference values are "
                    "estimates treated as fixed numbers (bootstrap 95 %: Q1 40.5-42.0, Q3 45.5-46.5). Re-weighting "
                    "the chairs to the period mix of the stools (19/29/31) gives quartiles 41.1 / 44.0 / 46.0 and "
                    "spread 0.084, so the pooled literals are not an artefact of the period mix."),
    },
    "primaer": [
        {"namn": "P1_median_i_kvartilbreidda",
         "statistikk": "median stool height (cm), primary sample",
         "terskel": [41.0, 46.0],
         "retning": "inside, bounds included (41.0 <= median <= 46.0); decided on the unrounded median",
         "regel_for_terskel": "first and third quartile of V&A adult chair seat height (n = 285), frozen literals",
         "dev_verdi": ("NO DEV VALUE (stools are sealed as a whole). Stand-in (80 DEV V&A chair seat heights + "
                       "N(0, 1 cm), with planted attrition; n = 75): median 43.24")},
        {"namn": "P2_spreiing_under_midtpunktet",
         "statistikk": "robust spread of stool height, 1.4826 MAD / median, primary sample",
         "terskel": 0.1257,
         "retning": "below (strict); decided on the unrounded spread",
         "regel_for_terskel": ("midpoint of the frozen chair seat-height spread 0.0779 and the frozen chair "
                               "total-height spread 0.1735: (0.0779 + 0.1735) / 2 = 0.1257"),
         "dev_verdi": "NO DEV VALUE. Stand-in: 0.1090"},
        {"namn": "P3_oevre_grense_under_totalhogdspreiinga",
         "statistikk": ("upper end of the 95 % percentile interval (97.5th percentile) of the robust spread, "
                        "cluster bootstrap over suites, 2000 resamples, seed felles.FRO"),
         "terskel": 0.1735,
         "retning": "below (strict); decided on the unrounded 97.5th percentile",
         "regel_for_terskel": "robust spread of total height H of all V&A adult chairs (n = 1204), frozen literal",
         "dev_verdi": "NO DEV VALUE. Stand-in: 0.1526"},
    ],
    "primaer_konjunksjon": "HELDT only if P1 and P2 and P3 all hold",
    "sekundaer": [
        "S1 by period (before 1700, 1700-1899, 1900 on, no year): n, median, spread, against the period's chair quartiles",
        "S2 unrestricted sample: every stool with a height from any source, name rule off, copied records kept",
        "S2b primary rules but name rule off",
        "S3 stools that have BOTH a whole-object height and a seat-labelled height: H minus seat (consistency of "
        "'height is seat height'); S3b the primary line with the seat-labelled height substituted where it exists",
        "S4 V&A only (Nasjonalmuseet has 2 stools, at most 1 with a height)",
        "S5 like-for-like window: stools with 30 <= H <= 65 (the range filter the chair seats passed)",
        "S6 share of stool heights inside the central 90 % range of chair seat heights [36.0, 51.8]",
        "S7 non-robust spread SD / mean, and the ratios spread / 0.0779 and spread / 0.1735",
        "the 20 stools with a mesh are not used",
    ],
    "port": [
        {"namn": "G1_n", "terskel": 60, "ugyldig_dersom": "fewer than 60 stools in the primary sample",
         "regel": ("three quarters of the 79 expected from catalogue counts: if more than a quarter is lost to "
                   "copied dimension records or a loader fault, the sample is not the one the prediction was made for")},
        {"namn": "G2_suitar", "terskel": 40, "ugyldig_dersom": "fewer than 40 suites in the primary sample",
         "regel": ("smallest tested number of independent suites at which the planted-effect control (b) holds all "
                   "three primary lines in at least 0.95 of the populations (scratch sweep, 400 populations each: "
                   "30 suites 0.89, 40 suites 0.95, 50 suites 0.98; repeated in syntetisk_kontroll()['suite_sveip'])")},
    ],
    "grunnmodell": (
        "Stool height varies like furniture height in general, or stools sit at another level than chair seats. "
        "Version A (stools as furniture): heights distributed like chair total heights: median about 94 cm, robust "
        "spread 0.17 or more; P1, P2 and P3 all fail. Version B (right level, loose): median inside 41-46 but "
        "spread 0.1735; P2 fails (P3 as well). Version C (tight, other level): spread about 0.08 but median "
        "outside 41-46; P1 fails."),
    "tel_imot": (
        "Median stool height outside 41.0-46.0 cm, or robust spread at or above 0.1257, or a bootstrap upper bound "
        "at or above 0.1735. Any one of the three makes the verdict SLO FEIL."),
    "merknad_om_styrke": (
        "The threshold of P2 is a midpoint: a population whose true spread is exactly 0.1257 is HELDT in about a "
        "third of the runs (chair-seat shape; about half with a normal shape, and a normal population with true "
        "spread 0.15 is still HELDT in about 0.10 of the runs: independent check, 300 populations each). "
        "The test separates 0.08 from 0.17; it does not separate 0.11 from 0.14. Mislabelled "
        "objects (footstools, bar stools, stools with raised ends whose H is not the seat) all push towards SLO "
        "FEIL: the verdict survives about 10 % of them and not 25 % (syntetisk_kontroll()['c_forureining']). "
        "A SLO FEIL is therefore ambiguous between the theory and the sample; a HELDT is not. "
        "[independent check, 13 Nov] What a HELDT does NOT show: the robust spread describes the central half of "
        "the stools. If the core is tighter than chair seats (SD 2.5 cm), a sample in which 20 % of the stools lie "
        "far away (20-32 or 58-80 cm) is HELDT in 0.997 of the runs and one with 30 % in 0.71 (300 populations "
        "each). The tolerance of 'about 10 %' above holds for a core as wide as chair seats. A HELDT must "
        "therefore be read together with S6 (share inside 36.0-51.8 cm; 0.90 if stools are like chair seats) and "
        "S7 (SD / mean). P1 does not separate levels within about 1 cm of the bounds: a population centred at "
        "40.5 or 46.5 cm holds P1 in about 0.17 of the runs, at 40.0 in 0.02-0.13, at 47.0 in 0.03-0.05, and at "
        "39 or 48 cm in less than 0.01."),
}

# ---- constants taken from SPEC (one source for every number)
REF = SPEC["referanse"]
Q1, Q3 = SPEC["primaer"][0]["terskel"]
T_SPREIING = SPEC["primaer"][1]["terskel"]
T_OEVRE = SPEC["primaer"][2]["terskel"]
N_MIN = SPEC["port"][0]["terskel"]
SUITAR_MIN = SPEC["port"][1]["terskel"]
P5, P95 = REF["sete_p5"], REF["sete_p95"]
VINDAUGE = (30.0, 65.0)                      # the sete_ok window of the chairs (secondary line S5 only)
GODKJEND_KJELDE = ("H", "sete")
NAMNETERMAR = [(g, re.compile(m, re.I)) for g, m in SPEC["utval"]["namnetermar"]]
GENERISKE_NAMN = frozenset({"", "stool", "stol", "krakk", "stol uten rygg", "stol utan rygg"})
PERIODAR = ("foer_1700", "1700_1899", "fraa_1900", "utan_aar")
DOMAR = ("HELDT", "SLO FEIL", "UGYLDIG")
EPS = 1e-9                                   # floating-point tolerance at the inclusive bounds of P1 (cm); not a tuning constant

# ---- synthetic populations (documented in syntetisk_kontroll)
SYN_SETT = (4, 2, 2, 2, 2)                   # planted sets whose members share one height; the rest are singles
N_SUITAR_SYN = 71                            # suites per synthetic population -> 78 stools (71 - 5 + 12)
SYN_STOEY = 1.0                              # cm, N(0, 1) added to every drawn height
N_REP_KONTROLL = 400                         # synthetic populations per scenario, the five controls
N_REP = 200                                  # synthetic populations per scenario, the sweeps
N_BOOT_REP = 300                             # bootstrap resamples inside the rate estimates (2000 in every verdict)

_INNERSTE_PARENTES = re.compile(r"\([^()]*\)")


# ====================================================================================================== helpers
def _rein(o):
    """Recursively make JSON-serialisable: numpy scalars -> python, NaN / inf -> None, tuples -> lists."""
    if isinstance(o, dict):
        return {str(k): _rein(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set, frozenset)):
        return [_rein(v) for v in o]
    if isinstance(o, np.ndarray):
        return [_rein(v) for v in o.tolist()]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        v = float(o)
        return v if np.isfinite(v) else None
    return o


def _avrund(v, d=4):
    return None if v is None or not np.isfinite(v) else round(float(v), d)


def _endeleg_tal(v):
    """Unrounded float, or None when missing / NaN / infinite."""
    return None if v is None or not np.isfinite(v) else float(v)


def _utan_parentes(s):
    """Name without its parenthesised parts (the maker), nested parentheses included; whitespace collapsed."""
    s = s or ""
    while True:
        t = _INNERSTE_PARENTES.sub(" ", s)
        if t == s:
            break
        s = t
    return " ".join(s.split())


def _namnetekst(rec):
    """The text the name rule reads: Namn without the parenthesised maker + Nemning, lower-cased."""
    return (_utan_parentes(rec.get("namn")) + " | " + (rec.get("nemning") or "")).lower()


def _namnegruppe(rec):
    """First name-rule group the object matches, or None."""
    t = _namnetekst(rec)
    for g, m in NAMNETERMAR:
        if m.search(t):
            return g
    return None


def _namn_har_andre_ord(rec):
    """True when the name carries any word beyond the bare type word (maker in parentheses not counted)."""
    return _utan_parentes(rec.get("namn")).lower() not in GENERISKE_NAMN


def _hogd(rec):
    """Accepted height in cm or None (None, NaN, zero and negative values are 'no height')."""
    H = rec.get("H")
    try:
        H = float(H)
    except (TypeError, ValueError):
        return None
    return H if np.isfinite(H) and H > 0 else None


def _periode(aar):
    if aar is None:
        return "utan_aar"
    return "foer_1700" if aar < 1700 else ("1700_1899" if aar < 1900 else "fraa_1900")


def _median(x):
    """Median of a 1-D float array by sorting (same value as np.median: mean of the two middle elements when
    the length is even; several times faster on short arrays, which matters inside the bootstrap)."""
    x = np.sort(x)
    n = len(x)
    return float(x[n // 2]) if n % 2 else float((x[n // 2 - 1] + x[n // 2]) / 2.0)


def _stat(rr):
    """Bootstrap statistic: [median, robust spread, SD/mean, share inside P5-P95]; NaN when degenerate.
    Robust spread = 1.4826 * median(|x - median|) / median, the formula of felles.robust_spreiing."""
    x = np.asarray([r["H"] for r in rr], float)
    if len(x) < 3:
        return [np.nan] * 4
    m = _median(x)
    if not m > 0:
        return [np.nan] * 4
    return [m, 1.4826 * _median(np.abs(x - m)) / m, float(x.std(ddof=1) / x.mean()),
            float(np.count_nonzero((x >= P5) & (x <= P95))) / len(x)]


def _linje(recs, n_boot, raa=None):
    """One reported line: n, suites, median, robust spread, SD/mean, share in the chair-seat 90 % range, each
    with a cluster-bootstrap 95 % percentile interval (felles.klyngebootstrap over suites, seed felles.FRO).
    raa: optional dict that receives the UNROUNDED median, spread and upper bound of the spread interval
    (keys 'median', 'spreiing', 'oevre'); the verdict is decided on these, never on the rounded display values."""
    recs = list(recs)
    ut = {"n": len(recs), "suitar": len({felles.suite(r) for r in recs}),
          "median": None, "median_ki95": [None, None], "spreiing": None, "spreiing_ki95": [None, None],
          "sd_over_snitt": None, "del_i_p5_p95": None, "del_i_p5_p95_ki95": [None, None]}
    if len(recs) < 3:
        return ut
    v = _stat(recs)
    if raa is not None:
        raa["median"], raa["spreiing"] = float(v[0]), float(v[1])
    ut["median"], ut["spreiing"] = _avrund(v[0], 2), _avrund(v[1])
    ut["sd_over_snitt"], ut["del_i_p5_p95"] = _avrund(v[2]), _avrund(v[3], 3)
    if n_boot and ut["suitar"] >= 2:
        b = felles.klyngebootstrap(recs, _stat, n=n_boot, seed=felles.FRO)
        lo, hi = felles.ki(b)
        if raa is not None:
            raa["oevre"] = float(hi[1])
        ut["median_ki95"] = [_avrund(lo[0], 2), _avrund(hi[0], 2)]
        ut["spreiing_ki95"] = [_avrund(lo[1]), _avrund(hi[1])]
        ut["del_i_p5_p95_ki95"] = [_avrund(lo[3], 3), _avrund(hi[3], 3)]
    return ut


# ====================================================================================================== sample
def _sil(recs):
    """Apply the frozen sample rules. -> (primary records, attrition dict, name-hit counts over ALL objects).
    Every object leaves at the first reason that applies, in the order of SPEC['utval']['fraafall_rekkjefolgje'].
    The primary records are shallow copies with H as a float."""
    treff = {g: 0 for g, _ in NAMNETERMAR}
    flyt = {"inn": 0, "namneregel": 0, "utan_hogd": 0, "kjelde_raa": 0, "maal_kopi": 0, "primaer": 0}
    prim = []
    for r in recs:
        flyt["inn"] += 1
        g = _namnegruppe(r)
        if g is not None:
            treff[g] += 1
            flyt["namneregel"] += 1
            continue
        h = _hogd(r)
        if h is None:
            flyt["utan_hogd"] += 1
            continue
        if r.get("H_kjelde") not in GODKJEND_KJELDE:
            flyt["kjelde_raa"] += 1
            continue
        if r.get("maal_kopi"):
            flyt["maal_kopi"] += 1
            continue
        prim.append(dict(r, H=h))
    flyt["primaer"] = len(prim)
    return prim, flyt, treff


def _doem(recs, n_boot=None, fullt=True):
    """THE scoring code. Used unchanged for the held-out stools, the DEV stand-in and every synthetic population.
    recs: records with keys id, museum, namn, nemning, aar, H, H_kjelde, sete_kat, suite, maal_kopi.
    fullt=False skips the secondary lines (used for the synthetic controls)."""
    n_boot = felles.N_BOOT if n_boot is None else n_boot
    recs = list(recs)
    prim, flyt, treff = _sil(recs)
    raa = {}
    hovud = _linje(prim, n_boot, raa)

    port = [
        {"namn": "G1_n", "verdi": hovud["n"], "terskel": N_MIN, "ok": hovud["n"] >= N_MIN},
        {"namn": "G2_suitar", "verdi": hovud["suitar"], "terskel": SUITAR_MIN, "ok": hovud["suitar"] >= SUITAR_MIN},
    ]
    port_ok = all(p["ok"] for p in port)

    # [independent check, 13 Nov] The three lines are decided on the UNROUNDED statistics. Before the check they
    # were decided on the display values (median rounded to 2 decimals, spreads to 4), so that a median of 46.004
    # counted as inside 41.0-46.0 and a spread of 0.12566 as not below 0.1257. 'verdi' is still the rounded
    # display value; 'verdi_uavrunda' is the number that decides. EPS only absorbs floating-point noise in the
    # mean of the two middle heights at the inclusive bounds of P1.
    med, spr, oevre = (_endeleg_tal(raa.get(k)) for k in ("median", "spreiing", "oevre"))
    primaer = [
        {"namn": "P1_median_i_kvartilbreidda", "verdi": hovud["median"], "verdi_uavrunda": med,
         "ki95": hovud["median_ki95"], "terskel": [Q1, Q3],
         "held": bool(med is not None and Q1 - EPS <= med <= Q3 + EPS)},
        {"namn": "P2_spreiing_under_midtpunktet", "verdi": hovud["spreiing"], "verdi_uavrunda": spr,
         "ki95": hovud["spreiing_ki95"], "terskel": T_SPREIING, "held": bool(spr is not None and spr < T_SPREIING)},
        {"namn": "P3_oevre_grense_under_totalhogdspreiinga", "verdi": hovud["spreiing_ki95"][1],
         "verdi_uavrunda": oevre, "ki95": hovud["spreiing_ki95"], "terskel": T_OEVRE,
         "held": bool(oevre is not None and oevre < T_OEVRE)},
    ]
    if not port_ok:
        dom = "UGYLDIG"
    elif all(p["held"] for p in primaer):
        dom = "HELDT"
    else:
        dom = "SLO FEIL"

    andre_ord = [_namn_har_andre_ord(r) for r in recs]
    ut = {"n": hovud["n"], "suitar": hovud["suitar"],
          "fraafall": {"flyt": flyt, "namneregel_treff_per_gruppe": treff,
                       "namn_med_andre_ord_enn_typeordet": int(sum(andre_ord)),
                       "del_namn_med_andre_ord": _avrund(np.mean(andre_ord), 3) if recs else None,
                       "per_museum_primaer": {m: sum(1 for r in prim if r.get("museum") == m) for m in ("NM", "VA")},
                       "per_kjelde_primaer": {k: sum(1 for r in prim if r.get("H_kjelde") == k)
                                              for k in GODKJEND_KJELDE}},
          "port": port, "port_ok": port_ok, "primaer": primaer, "dom": dom}
    if fullt:
        ut["sekundaer"] = _sekundaer(recs, prim, hovud, n_boot)
    return ut


def _sete_merkt(r):
    """Seat-labelled height of a record as a positive float, or None."""
    try:
        v = float(r.get("sete_kat"))
    except (TypeError, ValueError):
        return None
    return v if np.isfinite(v) and v > 0 else None


def _sekundaer(recs, prim, hovud, n_boot):
    """Secondary lines. Reported without a verdict."""
    sek = []
    # S1 by period, against the period's own chair quartiles (frozen literals)
    for p in PERIODAR:
        rr = [r for r in prim if _periode(r.get("aar")) == p]
        l = _linje(rr, n_boot)
        ref = REF["periodar"].get(p)
        l.update({"namn": "S1_periode_" + p, "stolreferanse": ref,
                  "median_i_periodens_kvartilbreidd": (None if ref is None or l["median"] is None
                                                       else bool(ref["q1"] <= l["median"] <= ref["q3"])),
                  "median_i_41_46": None if l["median"] is None else bool(Q1 <= l["median"] <= Q3)})
        sek.append(l)
    # S2 unrestricted: any height, any source, name rule off, copied records kept
    alle = [dict(r, H=_hogd(r)) for r in recs if _hogd(r) is not None]
    l = _linje(alle, n_boot)
    l.update({"namn": "S2_urestriktert",
              "median_i_41_46": None if l["median"] is None else bool(Q1 <= l["median"] <= Q3),
              "spreiing_under_0.1257": None if l["spreiing"] is None else bool(l["spreiing"] < T_SPREIING),
              "oevre_under_0.1735": None if l["spreiing_ki95"][1] is None else bool(l["spreiing_ki95"][1] < T_OEVRE)})
    sek.append(l)
    # S2b primary rules, name rule off
    utan = [r for r in alle if r.get("H_kjelde") in GODKJEND_KJELDE and not r.get("maal_kopi")]
    l = _linje(utan, n_boot)
    l.update({"namn": "S2b_utan_namneregel"})
    sek.append(l)
    # S3 consistency of 'height is seat height'
    baae = [r for r in prim if r.get("H_kjelde") == "H" and _sete_merkt(r) is not None]
    d = np.asarray([r["H"] - _sete_merkt(r) for r in baae], float)
    sek.append({"namn": "S3_hogd_mot_setemerkt_hogd", "n": len(baae),
                "median_H_minus_sete_cm": _avrund(np.median(d), 2) if len(d) else None,
                "median_abs_avvik_cm": _avrund(np.median(np.abs(d)), 2) if len(d) else None,
                "del_innanfor_2cm": _avrund(np.mean(np.abs(d) <= 2.0), 3) if len(d) else None,
                "merknad": ("selected subset: a separate seat height is catalogued mostly where the top of the "
                            "object is not the seat (raised ends, dished seat)")})
    baae_id = {r["id"] for r in baae}
    bytt = [dict(r, H=_sete_merkt(r)) if r["id"] in baae_id else r for r in prim]
    l = _linje(bytt, n_boot)
    l.update({"namn": "S3b_setemerkt_hogd_sett_inn"})
    sek.append(l)
    # S4 V&A only
    l = _linje([r for r in prim if r.get("museum") == "VA"], n_boot)
    l.update({"namn": "S4_berre_VA", "n_NM_i_primaer": sum(1 for r in prim if r.get("museum") == "NM")})
    sek.append(l)
    # S5 like-for-like window 30-65 cm
    inne = [r for r in prim if VINDAUGE[0] <= r["H"] <= VINDAUGE[1]]
    l = _linje(inne, n_boot)
    l.update({"namn": "S5_vindauge_30_65",
              "del_av_primaer_i_vindauget": _avrund(len(inne) / len(prim), 3) if prim else None,
              "n_under_30": sum(1 for r in prim if r["H"] < VINDAUGE[0]),
              "n_over_65": sum(1 for r in prim if r["H"] > VINDAUGE[1])})
    sek.append(l)
    # S6 / S7 descriptive, on the primary line
    sek.append({"namn": "S6_del_i_stolsetets_90_prosent_omraade", "omraade": [P5, P95],
                "verdi": hovud["del_i_p5_p95"], "ki95": hovud["del_i_p5_p95_ki95"],
                "under_grunnmodell_A": "0.004 (share of the 1204 V&A chair total heights inside 36.0-51.8)",
                "dersom_som_stolsete": "0.90"})
    sek.append({"namn": "S7_spreiingsforhold", "sd_over_snitt": hovud["sd_over_snitt"],
                "spreiing_over_setespreiing": (None if hovud["spreiing"] is None
                                               else _avrund(hovud["spreiing"] / REF["sete_spreiing"], 3)),
                "spreiing_over_totalhogdspreiing": (None if hovud["spreiing"] is None
                                                    else _avrund(hovud["spreiing"] / REF["H_spreiing"], 3))})
    return sek


# ====================================================================================================== open data
def _va_stolar():
    """Open catalogue rows of V&A adult chairs (felles._reinsa blanks every stool measure at read time).
    -> (rows with seat height: the 285; rows with accepted measures: the 1204)."""
    R = [r for r in felles._reinsa() if r["museum"] == "VA" and r["vaksenstol"] == "1" and r["maal_ok"] == "1"
         and r["type"] not in felles.KRAKKTYPAR]
    return [r for r in R if r["sete_ok"] == "1"], R


def _referanse_fraa_data():
    """Re-derive the frozen reference literals from the open catalogue and compare. The LITERALS decide; a
    mismatch is reported, never applied."""
    med_sete, alle = _va_stolar()
    s = np.asarray([float(r["sete"]) for r in med_sete])
    H = np.asarray([float(r["H"]) for r in alle])
    H285 = np.asarray([float(r["H"]) for r in med_sete])
    no = {"n_sete": len(s), "sete_q1": float(np.percentile(s, 25)), "sete_median": float(np.median(s)),
          "sete_q3": float(np.percentile(s, 75)), "sete_p5": float(np.percentile(s, 5)),
          "sete_p95": float(np.percentile(s, 95)), "sete_spreiing": felles.robust_spreiing(s),
          "n_H": len(H), "H_median": float(np.median(H)), "H_spreiing": felles.robust_spreiing(H),
          "H_spreiing_paa_dei_285": felles.robust_spreiing(H285)}
    toleranse = {"sete_spreiing": 0.0005, "H_spreiing": 0.0005, "H_spreiing_paa_dei_285": 0.0005, "n_sete": 0, "n_H": 0}
    avvik = {k: [REF[k], _avrund(v, 5)] for k, v in no.items() if abs(v - REF[k]) > toleranse.get(k, 0.05)}
    per = {}
    for p in PERIODAR[:3]:
        x = np.asarray([float(r["sete"]) for r in med_sete if _periode(felles._aar(r["aar_fraa"])) == p])
        per[p] = {"n": len(x), "q1": _avrund(np.percentile(x, 25), 2), "median": _avrund(np.median(x), 2),
                  "q3": _avrund(np.percentile(x, 75), 2), "spreiing": _avrund(felles.robust_spreiing(x))}
        f = REF["periodar"][p]
        if per[p]["n"] != f["n"] or any(abs(per[p][k] - f[k]) > 0.051 for k in ("q1", "median", "q3")):
            avvik["periode_" + p] = [f, per[p]]
    return {"utrekna_no": {k: _avrund(v, 5) for k, v in no.items()}, "periodar_no": per,
            "midtpunkt_av_literalane": _avrund((REF["sete_spreiing"] + REF["H_spreiing"]) / 2, 5),
            "terskel_P2": T_SPREIING, "avvik_fraa_literalane": avvik, "samsvar": not avvik}


def forventa_n():
    """Counts only, from open catalogue fields (names, years, presence of a height): what the primary sample of
    the sealed run should look like. No stool measure is read."""
    e = felles.tel_ekstra("krakk")
    s = felles._stolar()
    rader = [r for r in felles._reinsa() if r["type"] in felles.KRAKKTYPAR]
    treff = {g: 0 for g, _ in NAMNETERMAR}
    per = {p: 0 for p in PERIODAR}
    n_namn = n_h = n_ord = 0
    for r in rader:
        rec = {"namn": s.get(r["id"], {}).get("Namn", ""), "nemning": s.get(r["id"], {}).get("Nemning", "")}
        n_ord += _namn_har_andre_ord(rec)
        g = _namnegruppe(rec)
        if g is not None:
            treff[g] += 1
            n_namn += 1
            continue
        if r["_har_H"]:
            n_h += 1
            per[_periode(felles._aar(r["aar_fraa"]))] += 1
    return {"n_krakk": e["n"], "per_museum": e["per_museum"], "n_med_H_i_reinsa_tabell": e["n_med_H"],
            "n_H_berre_i_raadata": e["n_H_berre_i_raadata"], "n_utan_H": e["n_utan_H"],
            "namneregel_treff_per_gruppe": treff, "fjerna_av_namneregelen": n_namn,
            "namn_med_andre_ord_enn_typeordet": int(n_ord), "del_namn_med_andre_ord": _avrund(n_ord / len(rader), 3),
            "forventa_primaer_n": n_h, "forventa_primaer_per_periode": per,
            "merknad": ("upper count: copied dimension records (maal_kopi) leave at run time; the one stool whose "
                        "height exists only in raw data adds 1 if that height is seat-labelled")}


# ====================================================================================================== synthetic
def _dev_va():
    """DEV V&A chairs with catalogue seat height, without copied dimension records: the material every synthetic
    population is built from. -> list of records (H = total height, sete_kat = seat height, aar)."""
    return [r for r in felles.les("dev") if r["museum"] == "VA" and r["sete_kat"] is not None
            and r["H"] is not None and not r["maal_kopi"]]


def _basis():
    d = _dev_va()
    return (np.asarray([r["sete_kat"] for r in d], float), np.asarray([r["H"] for r in d], float),
            [r["aar"] for r in d])


def _form(x):
    """Robust standard scores of an empirical distribution: (x - median) / (1.4826 MAD)."""
    x = np.asarray(x, float)
    m = np.median(x)
    return (x - m) / (1.4826 * np.median(np.abs(x - m)))


def _bygg(hogder, aar, sett, merke="syn"):
    """Wrap drawn heights (one per SUITE) as stool-like records. The first len(sett) suites are sets of the given
    sizes whose members share one height (the worst case for the effective sample size); the rest are singles."""
    recs, k = [], 0
    storleik = list(sett) + [1] * (len(hogder) - len(sett))
    for j, st in enumerate(storleik):
        for _ in range(st):
            recs.append({"id": "%s%03d" % (merke, k), "museum": "VA", "type": "Krakk", "namn": "Stool (ukjent)",
                         "nemning": "Krakk", "aar": aar[j], "H": float(hogder[j]), "H_kjelde": "H",
                         "sete_kat": None, "suite": "%s_s%03d" % (merke, j), "maal_kopi": False})
            k += 1
    return recs


def _trekk(scenario, rng, basis, n_suitar=N_SUITAR_SYN, sett=SYN_SETT):
    """One synthetic population. basis = (seat heights, total heights, years) of the DEV V&A chairs.
    scenario = (kind, parameter). Every height gets N(0, SYN_STOEY) cm of noise."""
    s, H, aar = basis
    slag, par = scenario
    i = rng.integers(0, len(s), n_suitar)
    stoey = rng.normal(0, SYN_STOEY, n_suitar)
    if slag == "a_totalhogd":                 # base model A: heights drawn like chair TOTAL heights
        x = H[i] + stoey
    elif slag == "a2_rett_nivaa_laus":        # base model B: chair-seat level, spread par, shape of chair H
        x = REF["sete_median"] * (1 + par * _form(H)[i]) + stoey
    elif slag == "a3_anna_nivaa":             # base model C: chair-seat spread, level multiplied by par
        x = par * s[i] + stoey
    elif slag == "b_som_stolsete":            # the effect: heights drawn like chair seat heights
        x = s[i] + stoey
    elif slag == "spreiing":                  # chair-seat level and shape, spread set to par
        x = REF["sete_median"] * (1 + par * _form(s)[i]) + stoey
    elif slag in ("c_fotskammel", "c_hoge", "c_begge"):
        x = s[i] + stoey                      # (b) with a share par of the suites replaced by mislabelled objects
        k = int(round(par * n_suitar))
        kven = rng.permutation(n_suitar)[:k]
        if slag == "c_fotskammel":
            x[kven] = rng.uniform(20, 30, k)                       # footstools catalogued as 'Stool'
        elif slag == "c_hoge":
            x[kven] = rng.uniform(65, 80, k)                       # bar stools, or H taken at raised ends
        else:
            lag = rng.random(k) < 0.5
            x[kven] = np.where(lag, rng.uniform(20, 30, k), rng.uniform(65, 80, k))
    else:
        raise ValueError(slag)
    return _bygg(np.maximum(x, 1.0), [aar[j] for j in i], sett)


def _rate(scenario, basis, froe, n_rep=N_REP, n_suitar=N_SUITAR_SYN, sett=SYN_SETT):
    """Verdict rates over n_rep synthetic populations (bootstrap N_BOOT_REP inside each).
    'del_alle_tre_held' ignores the gates (it is what the suite sweep needs)."""
    rng = np.random.default_rng(froe)
    tel = {d: 0 for d in DOMAR}
    med, spr, p, alle = [], [], [0, 0, 0], 0
    for _ in range(n_rep):
        r = _doem(_trekk(scenario, rng, basis, n_suitar, sett), n_boot=N_BOOT_REP, fullt=False)
        tel[r["dom"]] += 1
        med.append(r["primaer"][0]["verdi"])
        spr.append(r["primaer"][1]["verdi"])
        for j in range(3):
            p[j] += r["primaer"][j]["held"]
        alle += all(q["held"] for q in r["primaer"])
    return {"n_rep": n_rep, "del_HELDT": round(tel["HELDT"] / n_rep, 3),
            "del_SLO_FEIL": round(tel["SLO FEIL"] / n_rep, 3), "del_UGYLDIG": round(tel["UGYLDIG"] / n_rep, 3),
            "del_P1_P2_P3_held": [round(v / n_rep, 3) for v in p], "del_alle_tre_held": round(alle / n_rep, 3),
            "snitt_median": _avrund(np.mean(med), 2), "snitt_spreiing": _avrund(np.mean(spr))}


def _ein(scenario, basis, froe):
    """The verdict of ONE synthetic population at the full N_BOOT (the control proper)."""
    r = _doem(_trekk(scenario, np.random.default_rng(froe), basis), fullt=False)
    return {"dom": r["dom"], "n": r["n"], "suitar": r["suitar"],
            "primaer": [{"namn": p["namn"], "verdi": p["verdi"], "held": p["held"]} for p in r["primaer"]]}


def syntetisk_kontroll():
    """Runs _doem() (the scoring code of the sealed run) on synthetic populations built from the DEV V&A chairs.
    Every population: 78 stool-like records in 71 suites (one set of 4 and four pairs share a height); heights =
    a draw with replacement from the DEV chairs + N(0, 1 cm).
      (a)  base model A true: heights drawn like chair TOTAL heights                    -> must not be HELDT
      (a2) base model B true: chair-seat level, robust spread 0.1735, shape of chair H  -> must not be HELDT
      (a3) base model C true: chair-seat spread, level x 1.15 and x 0.87                -> must not be HELDT
      (b)  effect planted: heights drawn like chair SEAT heights (spread about 0.085)    -> must be HELDT
      (c)  (b) with a share of mislabelled objects (footstools 20-30 cm; tall objects 65-80 cm; both)
    Each control scenario is judged once at the full 2000 resamples and its verdict rate is estimated over
    N_REP_KONTROLL populations with N_BOOT_REP resamples; requirement: the single verdict as stated AND the rate
    of HELDT at most 0.05 under every base model and at least 0.95 under (b)."""
    basis = _basis()
    F = felles.FRO
    ut = {"id": SPEC["id"],
          "oppsett": {"n_per_populasjon": N_SUITAR_SYN - len(SYN_SETT) + sum(SYN_SETT), "suitar": N_SUITAR_SYN,
                      "sett": list(SYN_SETT), "stoey_cm": SYN_STOEY, "n_rep_kontroll": N_REP_KONTROLL,
                      "n_rep_sveip": N_REP, "n_boot_i_ratane": N_BOOT_REP, "n_boot_i_domane": felles.N_BOOT,
                      "bygd_paa": "DEV V&A chairs with catalogue seat height, copied records dropped",
                      "n_dev_stolar": int(len(basis[0])),
                      "dev_sete_median": _avrund(np.median(basis[0]), 2),
                      "dev_sete_spreiing": _avrund(felles.robust_spreiing(basis[0])),
                      "dev_H_median": _avrund(np.median(basis[1]), 2),
                      "dev_H_spreiing": _avrund(felles.robust_spreiing(basis[1]))}}
    sc = {
        "a_grunnmodell_A_totalhogd": ("a_totalhogd", None),
        "a2_grunnmodell_B_rett_nivaa_spreiing_0.1735": ("a2_rett_nivaa_laus", REF["H_spreiing"]),
        "a3_grunnmodell_C_nivaa_x1.15": ("a3_anna_nivaa", 1.15),
        "a3_grunnmodell_C_nivaa_x0.87": ("a3_anna_nivaa", 0.87),
        "b_effekt_som_stolsete": ("b_som_stolsete", None),
    }
    kontroll = {}
    for j, (namn, s) in enumerate(sc.items()):
        kontroll[namn] = {"ein_populasjon": _ein(s, basis, F + 10 + j),
                          "rate": _rate(s, basis, F + 100 + j, n_rep=N_REP_KONTROLL)}
    ut["kontroll"] = kontroll
    krav = {k: bool(v["ein_populasjon"]["dom"] != "HELDT" and v["rate"]["del_HELDT"] <= 0.05)
            for k, v in kontroll.items() if k.startswith("a")}
    b = kontroll["b_effekt_som_stolsete"]
    krav["b_effekt_som_stolsete"] = bool(b["ein_populasjon"]["dom"] == "HELDT" and b["rate"]["del_HELDT"] >= 0.95)
    ut["krav"] = krav
    ut["kontroll_ok"] = all(krav.values())

    # (c) contamination: how much mislabelled material the robust statistics survive
    foru = {"c_25_prosent_fotskammel_ein_populasjon": _ein(("c_fotskammel", 0.25), basis, F + 20)}
    for a, slag in enumerate(("c_fotskammel", "c_hoge", "c_begge")):
        rad = {}
        for j, p in enumerate((0.05, 0.10, 0.15, 0.20, 0.25)):
            rad["%.2f" % p] = _rate((slag, p), basis, F + 200 + 10 * a + j)
        foru[slag] = rad
        ok = [float(k) for k, v in rad.items() if v["del_HELDT"] >= 0.80]
        foru[slag + "_taaler_inntil"] = max(ok) if ok else 0.0
    foru["lesemaate"] = ("share of suites replaced by mislabelled objects catalogued as 'Stool'; 'taaler_inntil' = "
                         "largest tested share at which the verdict is still HELDT in at least 0.80 of the "
                         "populations")
    ut["c_forureining"] = foru

    # operating characteristic: verdict rate against the TRUE spread (chair-seat level and shape)
    ut["spreiing_sveip"] = {"%.4f" % v: _rate(("spreiing", v), basis, F + 300 + j)
                            for j, v in enumerate((0.0779, 0.10, 0.1257, 0.15, 0.1735))}
    # the rule behind gate G2: (b) with fewer suites, no sets; read 'del_alle_tre_held' (gates ignored)
    ut["suite_sveip"] = {str(m): _rate(("b_som_stolsete", None), basis, F + 400 + j, n_suitar=m, sett=())
                         for j, m in enumerate((30, 40, 50, 60))}
    return _rein(ut)


def _standin():
    """The DEV STAND-IN for the sealed stools: 80 DEV V&A chair seat heights + N(0, 1 cm), dressed as stool
    records, with planted cases for every branch of the sample rule (2 excluded names, 1 without height, 1 source
    'raa', 1 copied record) and 8 records carrying a seat-labelled height. NOT stools; NOT evidence."""
    d = _dev_va()
    rng = np.random.default_rng(felles.FRO + 1)
    kven = rng.permutation(len(d))[:80]
    recs = []
    for k, j in enumerate(kven):
        r = d[j]
        recs.append({"id": "standin%03d" % k, "museum": "VA", "type": "Krakk", "namn": "Stool (ukjent)",
                     "nemning": "Krakk", "aar": r["aar"], "H": float(r["sete_kat"] + rng.normal(0, SYN_STOEY)),
                     "H_kjelde": "H", "sete_kat": None, "suite": "standin_" + r["suite"], "maal_kopi": False})
    recs[0].update(namn="Juxon's Footstool", H=22.0)
    recs[1].update(namn="Stool Thing", H=30.0)
    recs[2].update(H=None, H_kjelde="")
    recs[3].update(H_kjelde="raa")
    recs[4].update(maal_kopi=True)
    recs[5].update(namn="Thebes stool")
    for r in recs[6:14]:
        r["sete_kat"] = r["H"] - float(rng.uniform(0, 3))
    return recs


# ====================================================================================================== contract
def _les(utval):
    if utval == "dev":
        return _standin()
    if utval == "held":
        return felles.les_ekstra("krakk")        # GUARDED. The only read of stool heights in this module.
    raise ValueError("utval må vere 'dev' eller 'held'")


def kjoer(utval):
    """utval 'held': the sealed stools (run exactly once, after sealing). utval 'dev': the stand-in (see _standin);
    its numbers describe DEV chair seats, not stools."""
    recs = _les(utval)
    r = _doem(recs)
    ut = {"id": SPEC["id"], "utval": utval,
          "utval_merknad": ("the sealed stools" if utval == "held" else
                            "STAND-IN: DEV V&A chair seat heights + noise dressed as stools; no stool was read"),
          "n": r["n"], "suitar": r["suitar"], "fraafall": r["fraafall"],
          "port": r["port"], "primaer": r["primaer"], "sekundaer": r["sekundaer"], "dom": r["dom"],
          "referanse_kontroll": _referanse_fraa_data(),
          "forventa_held_fraa_katalogteljingar": forventa_n()}
    return _rein(ut)


def figurdata(utval):
    """What one figure needs: stool heights as points by year with the chair seat band behind them.
    'held': the stool points (primary sample, and the objects left out with the reason).
    'dev' : the stand-in points. Both: the reference chair distributions from open catalogue data."""
    recs = _les(utval)
    prim = {r["id"] for r in _sil(recs)[0]}
    punkt = []
    for r in recs:
        h = _hogd(r)
        if h is None:
            continue
        g = _namnegruppe(r)
        if r["id"] in prim:
            status = "primaer"
        elif g is not None:
            status = "namneregel:" + g
        elif r.get("H_kjelde") not in GODKJEND_KJELDE:
            status = "kjelde_raa"
        else:
            status = "maal_kopi"
        punkt.append({"id": r["id"], "aar": r.get("aar"), "H": round(h, 1), "status": status,
                      "museum": r.get("museum"), "namn": r.get("namn") if utval == "held" else None})
    med_sete, alle = _va_stolar()
    stol = [[felles._aar(r["aar_fraa"]), float(r["sete"])] for r in med_sete]
    s = np.asarray([v for _, v in stol])
    H = np.asarray([float(r["H"]) for r in alle])
    band = []
    for a in range(1450, 2050, 50):
        x = np.asarray([v for y, v in stol if y is not None and a <= y < a + 50])
        if len(x) >= 5:
            band.append({"fraa": a, "til": a + 50, "n": int(len(x)), "q1": _avrund(np.percentile(x, 25), 2),
                         "median": _avrund(np.median(x), 2), "q3": _avrund(np.percentile(x, 75), 2)})
    hs, ks = np.histogram(s, bins=np.arange(30, 66, 1.0))
    hH, kH = np.histogram(H, bins=np.arange(50, 185, 5.0))
    return _rein({
        "id": SPEC["id"], "utval": utval,
        "merknad": None if utval == "held" else "STAND-IN points (DEV chair seats + noise), not stools",
        "krakk_punkt": punkt,
        "stolsete_band": {"q1": Q1, "q3": Q3, "median": REF["sete_median"], "p5": P5, "p95": P95,
                          "per_periode": REF["periodar"], "per_50_aar": band},
        "stolsete_punkt_aar_cm": stol,
        "stolsete_histogram": {"kantar_cm": ks, "tal": hs},
        "stol_totalhogd_histogram": {"kantar_cm": kH, "tal": hH},
        "tersklar": {"P1": [Q1, Q3], "P2": T_SPREIING, "P3": T_OEVRE,
                     "sete_spreiing": REF["sete_spreiing"], "H_spreiing": REF["H_spreiing"]},
    })


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"kjoer_dev": kjoer("dev"), "syntetisk_kontroll": syntetisk_kontroll()},
                     ensure_ascii=False, indent=1))
