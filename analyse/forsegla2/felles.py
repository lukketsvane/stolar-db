#!/usr/bin/env python3
"""felles.py - shared loader for the SECOND sealed test (3D-model data), analyse/forsegla2.

Pure numpy / scipy / csv. All paths are relative to this file. Run the self-test with
    python analyse/forsegla2/felles.py

BLINDNESS
  Sealed material: data/mesh_maal.csv, data/mesh_silhuettar.npz, 14_validering.csv, mesh_cache files of
  non-DEV ids, the catalogue heights of stools (type Krakk / Stol utan rygg) and every mesh value of
  children's chairs (type Barnestol). Every read of these goes through _vakt(), which raises
  PermissionError unless  os.environ['STOL_OPNE'] == 'ja'  AND  forsegla2/FORSEGLA.json exists.
  Stool heights are blanked when the catalogue table is read without the guard (only a presence mark is kept),
  the column 'stil' of stolar_reinsa.csv (a copy of STOLAR.csv 'Stilperiode') is dropped at read time, and from
  STOLAR.csv only the whitelisted columns in _STOLAR_KOL are read (never 'Stilperiode', never the five
  mesh-derived shape columns, never its dimension columns).

PUBLIC API (binding contract for the test modules)
  FRO = 20261113, N_BOOT = 2000
  les(utval)                    -> list of records, utval in {'dev', 'held'}            ('held' guarded)
  silhuett(utval)               -> dict id -> (side, front), each (200,160) uint8, row 0 = floor
                                   utval in {'dev', 'held', 'barnestol'}                 (the last two guarded)
  kvalitet(rec, side, front)    -> (ok, grunn)   the frozen silhouette quality rule
  kvalitet_front(rec, front)    -> (ok, grunn)   optional extra gate for modules that use the FRONT view
  materialklasse(materialar, teknikk='') -> 'LINE' | 'SHEET' | 'LINE+SHEET' | 'WOOD' | 'ANNA'
  materialflagg(materialar, teknikk='')  -> frozenset of {'metall','metall_usikker','plast','laminat','tre'}
  mat3(rec)                     -> 'metall' | 'plast' | 'tre' | 'anna'  (the regulation designer's three classes)
  suite(rec)                    -> cluster id (same set / same model)
  klyngebootstrap(recs, stat_fn, n=N_BOOT, seed=FRO, strata=None) -> np.ndarray
  ki(boot, niva=0.95)           -> (lo, hi) percentile interval, NaN-safe
  robust_spreiing(x), mad_sd(x), spearman(x, y), partial_spearman(x, y, covars)
  les_ekstra(kind)              -> records, kind in {'barnestol', 'krakk'}                (guarded)
  tel_ekstra(kind)              -> counts and names only                                  (unguarded)
  tel_held()                    -> counts of the held-out sample, catalogue only         (unguarded)
  punktsky(id)                  -> (p, n) surface points of one chair (DEV ids free, others guarded)
  dev_ids(), aarsbolk(aar, steg), klassetabell(recs)

RECORD KEYS (les, les_ekstra)
  id, museum ('NM'|'VA'), type, namn,
  aar        int(aar_fraa) if aar_fraa >= 1000 else None.  aar_fraa is THE year; never a midpoint.
  aar_til    int, or None when missing / 0 / below 1000 / below aar
  spenn      aar_til - aar, or None
  H, B, D    float cm (catalogue)
  sete_kat   float cm if sete_ok == '1' else None (catalogue seat height, 30-65 cm and below H)
  sete_konvensjon  'rail' | 'topp' | None   (rule: see sete_konvensjon())
  sete_konv_eksplisitt  True when the catalogue label itself states rail or top/upholstery; False when the
             convention is ASSUMED (all Nasjonalmuseet seats, and V&A labels that only say 'seat')
  sete_merke raw label of the seat-height dimension ('' for NM)
  sete_rail_kat, sete_topp_kat   V&A only: first Height labelled rail/frame, and first seat-labelled Height
             that is not rail (cm, kept only when 30-65 and below H); lets a module compare the two
             conventions inside one record. For NM sete_topp_kat = sete_kat, sete_rail_kat = None.
  nasjonalitet, materialar (raw string), teknikk (raw string), materialklasse, materialflagg (frozenset),
  nemning, produsent, bilete_bguw, bilete_url,
  suite      cluster id (the smallest id of the cluster; a chair alone has suite == id)
  maal_delt  int: how many OTHER population chairs carry exactly the same (museum, H, B, D)
  maal_kopi  bool: the catalogue measures are a dimension record copied across unrelated objects (MAALKOPIREGEL).
             H is then not this chair's height, and since every mesh is scaled to H, sete_mesh and the
             silhouettes are in false centimetres. kvalitet() fails these chairs; a module that does not call
             kvalitet() must drop them itself.
  mesh_status status string of the frozen mesh script ('ok', 'ok_utan_sete', 'missing', ...) or None when the
             chair has no row in the mesh table
  sete_mesh, sete_breidde_mesh, sete_djupn_mesh   float cm or None
  flagg      frozenset of flag strings from the mesh script
  mesh       the whole mesh row as dict ({} when there is no row)

FROZEN RULES (each documented at its definition)
  population      vaksenstol == '1' and maal_ok == '1'                                       (1598 chairs)
  DEV             ids in data/dev_ids.txt                                                    (255 chairs)
  HELD            population minus DEV minus every chair whose suite contains a DEV chair    (1258 chairs,
                  of which 39 carry maal_kopi)
  materialklasse  see MATERIALREGEL below
  suite           see SUITEREGEL below
  maal_kopi       see MAALKOPIREGEL below
  kvalitet        see KVALITETSREGEL below

CHANGES BY THE INDEPENDENT CHECK (13 Nov 2026), each marked '[independent check' or 'INDEPENDENT CHECK' below
  1. material: Polyamid is no longer a shell token (5 chairs change class).
  2. suite: the measure key is (museum, H, B, D) without the year. 1324 clusters (was 1370); 85 held-out
     chairs leave as suite-mates of DEV chairs (was 75); HELD is 1258 (was 1268).
  3. new record keys maal_delt, maal_kopi; kvalitet() has a condition 8 ('maal_kopi'); DEV pass 212 of 250
     (was 215).
  4. tel_ekstra('krakk') no longer returns 'n_maal_ok', and the unguarded reader blanks maal_ok and sete_ok of
     stools: both are range tests on the sealed stool heights.
"""
import csv
import json
import os
import re
import sys

import numpy as np
from scipy import ndimage
from scipy.stats import rankdata

FRO = 20261113      # fixed seed for every bootstrap
N_BOOT = 2000       # resamples in every interval

HER = os.path.dirname(os.path.abspath(__file__))        # .../analyse/forsegla2
ANALYSE = os.path.dirname(HER)                           # .../analyse
ROT = os.path.dirname(ANALYSE)                           # repository root
DATA = os.path.join(ANALYSE, "data")

REINSA = os.path.join(DATA, "stolar_reinsa.csv")
STOLAR = os.path.join(ROT, "STOLAR", "STOLAR.csv")
VA_RAA = os.path.join(DATA, "va_dimensjonar_raa.jsonl")
DEV_IDS = os.path.join(DATA, "dev_ids.txt")
DEV_MESH = os.path.join(DATA, "dev_mesh_maal.csv")
DEV_SIL = os.path.join(DATA, "dev_silhuettar.npz")
MESH_CACHE = os.path.join(DATA, "mesh_cache")
# sealed files: only reachable through _vakt()
HELD_MESH = os.path.join(DATA, "mesh_maal.csv")
HELD_SIL = os.path.join(DATA, "mesh_silhuettar.npz")
FORSEGLA_JSON = os.path.join(HER, "FORSEGLA.json")

KRAKKTYPAR = frozenset({"Krakk", "Stol utan rygg"})
BARNETYPE = "Barnestol"
CANVAS_H, CANVAS_W = 200, 160


# ============================================================================ guard
def _open_er():
    return os.environ.get("STOL_OPNE") == "ja" and os.path.exists(FORSEGLA_JSON)


def _vakt(kva):
    """Raise PermissionError unless the seal has been broken on purpose (env STOL_OPNE == 'ja' AND
    forsegla2/FORSEGLA.json exists). Called before every read of sealed material."""
    if not _open_er():
        raise PermissionError(
            "FORSEGLA: %s er forsegla materiale. Krev STOL_OPNE=ja og %s." % (kva, FORSEGLA_JSON))


# ============================================================================ small helpers
def _tal(s):
    """float or None ('' / non-numeric / NaN -> None)."""
    try:
        v = float(str(s).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return v if v == v else None


def _aar(s):
    """Year rule: int(value) if value >= 1000 else None (0.0, empty and values below 1000 are missing codes)."""
    v = _tal(s)
    return int(v) if v is not None and v >= 1000 else None


def _teikn(s):
    """Comma-separated catalogue field -> set of stripped tokens (case kept; the field is normalised)."""
    return {t.strip() for t in (s or "").split(",") if t.strip()}


def aarsbolk(aar, steg=25, golv=None):
    """Start year of the bin of width `steg` that holds `aar` (None stays None). With golv, years below golv
    are put in one bin labelled golv - steg (printed as '<golv')."""
    if aar is None:
        return None
    b = (int(aar) // steg) * steg
    if golv is not None and b < golv:
        return golv - steg
    return b


_CACHE = {}


def _ein_gong(namn, fn):
    if namn not in _CACHE:
        _CACHE[namn] = fn()
    return _CACHE[namn]


# ============================================================================ raw readers
def _reinsa():
    """Rows of stolar_reinsa.csv (UTF-8 BOM). The column 'stil' is dropped. For stools (KRAKKTYPAR) the sealed
    catalogue measures H, B, D, sete are blanked and replaced by the presence mark '_har_H'."""
    def les_():
        ut = []
        with open(REINSA, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                r.pop("stil", None)
                if r["type"] in KRAKKTYPAR:
                    r["_har_H"] = bool(r["H"])
                    # maal_ok and sete_ok are blanked too: they are range tests on the sealed heights
                    # (maal_ok needs H >= 50), so even their counts would describe the sealed group
                    for k in ("H", "B", "D", "sete", "sete_merke", "maal_ok", "sete_ok"):
                        r[k] = ""
                ut.append(r)
        return ut
    return _ein_gong("reinsa", les_)


def _reinsa_krakk():
    """GUARDED: the stool rows of stolar_reinsa.csv with their catalogue measures."""
    _vakt("kataloghøgdene til krakkane")
    ut = []
    with open(REINSA, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            r.pop("stil", None)
            if r["type"] in KRAKKTYPAR:
                ut.append(r)
    return ut


# Whitelist: the only STOLAR.csv columns ever read. 'Stilperiode', the five '(mesh)' shape columns, the
# dimension columns and the model-made annotation columns are never read.
_STOLAR_KOL = ("Namn", "Materialar", "Materialkommentar", "Teknikk", "Nemning", "Produsent",
               "Produksjonsstad", "Bilete-bguw", "Bilete-URL")


def _stolar():
    def les_():
        ut = {}
        with open(STOLAR, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                ut[r["Objekt-ID"]] = {k: (r.get(k) or "") for k in _STOLAR_KOL}
        return ut
    return _ein_gong("stolar", les_)


def dev_ids():
    """The DEV ids, in file order."""
    def les_():
        with open(DEV_IDS, encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    return list(_ein_gong("dev_ids", les_))


def _les_meshcsv(sti):
    with open(sti, encoding="utf-8-sig", newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def _dev_mesh():
    return _ein_gong("dev_mesh", lambda: _les_meshcsv(DEV_MESH))


def _held_mesh():
    """GUARDED: the full mesh table."""
    _vakt("data/mesh_maal.csv")
    return _ein_gong("held_mesh", lambda: _les_meshcsv(HELD_MESH))


# ---------------------------------------------------------------------------- V&A raw dimension records
TIL_CM = {"cm": 1.0, "mm": 0.1, "in": 2.54, "ft": 30.48, "m": 100.0}    # unit rules of 04_reinsa_tabell.py


def _va_tal(s):
    """R1 of 04_reinsa_tabell.py: 0 (or negative, or non-numeric) is a missing value."""
    v = _tal(s)
    return v if v is not None and v > 0 else None


def _va_hoegder(dims):
    """All Height entries of one V&A dimension list as (cm, label, er_sete), in catalogue order.
    label = part + qualifier + note, lower-cased (as in 04_reinsa_tabell.py); er_sete = 'seat' in label."""
    ut = []
    for d in dims or []:
        if (d.get("dimension") or "").strip() != "Height":
            continue
        f = TIL_CM.get((d.get("unit") or "").strip().lower())
        v = _va_tal(d.get("value"))
        if f is None or v is None:
            continue
        merke = " ".join([(d.get("part") or "").strip().lower(), (d.get("qualifier") or "").lower(),
                          (d.get("note") or "").lower()]).strip()
        ut.append((v * f, merke, "seat" in merke))
    return ut


def _va_maal(dims):
    """Exact re-implementation of va_maal() in 04_reinsa_tabell.py -> (H, B, D, sete, sete_merke) in cm.
    Whole-object measure: part empty; else part starting with overall / maximum / from floor to top.
    Seat height: the FIRST Height whose part, qualifier or note mentions 'seat'."""
    heil = {"Height": [], "Width": [], "Depth": []}
    samla = {"Height": [], "Width": [], "Depth": []}
    sete, merke = None, ""
    for d in dims or []:
        typ = (d.get("dimension") or "").strip()
        f = TIL_CM.get((d.get("unit") or "").strip().lower())
        v = _va_tal(d.get("value"))
        if typ not in heil or f is None or v is None:
            continue
        v *= f
        del_ = (d.get("part") or "").strip().lower()
        ekstra = " ".join([del_, (d.get("qualifier") or "").lower(), (d.get("note") or "").lower()])
        if typ == "Height" and "seat" in ekstra:
            if sete is None:
                sete, merke = v, ekstra.strip()
            continue
        if "seat" in ekstra:
            continue
        if del_ == "":
            heil[typ].append(v)
        elif del_.startswith(("overall", "maximum", "from floor to top")):
            samla[typ].append(v)
    vel = lambda t: (heil[t] or samla[t] or [None])[0]
    return vel("Height"), vel("Width"), vel("Depth"), sete, merke


def _va_raa(krakk=False):
    """dict id -> dimension list from va_dimensjonar_raa.jsonl (status ok only).
    krakk=False: stool records are skipped on their id, before their dimensions are parsed.
    krakk=True : GUARDED, returns the stool records only."""
    stol_ids = {r["id"] for r in _reinsa() if r["type"] in KRAKKTYPAR}
    if krakk:
        _vakt("V&A-måla til krakkane")

    def les_():
        ut = {}
        with open(VA_RAA, encoding="utf-8") as f:
            for linje in f:
                m = re.match(r'\{"id":\s*"([^"]+)"', linje)
                oid = m.group(1) if m else None
                if (oid in stol_ids) != krakk:
                    continue
                p = json.loads(linje)
                if p.get("status") == "ok":
                    ut[p["id"]] = p.get("dimensions") or []
        return ut
    return _ein_gong("va_raa_krakk" if krakk else "va_raa", les_)


# ============================================================================ seat convention
# SETEKONVENSJON (frozen). Applies to the label of the seat-height value actually used (the FIRST Height that
# mentions 'seat' in the V&A record; stolar_reinsa.csv 'sete_merke' is the same label cut at 60 characters).
#   1. label mentions upholstery / cover / stuffing / cushion           -> 'topp'  (explicit)
#      (wins over 2: 'topmost point of seat cover; top of seat rail is 53cm' is a top measure)
#   2. else label mentions 'rail' or 'frame'                            -> 'rail'  (explicit)
#   3. else ('seat', 'of seat', 'seat height', 'to top of seat', ...)   -> 'topp'  (explicit only if it says 'top')
#   Nasjonalmuseet (field 'Setehøgde', no label)                         -> 'topp'  (ASSUMED, never explicit)
#   no accepted catalogue seat height (sete_ok != '1')                   -> None
# Catalogue count, V&A adult chairs with sete_ok: rail 75, topp 210 (28 records carry both a rail and a top value).
_RE_TOPP = re.compile(r"uphol|cover|stuff|cushion")
_RE_RAIL = re.compile(r"rail|frame")


def sete_konvensjon(merke, museum="VA"):
    """-> (konvensjon, eksplisitt) for one seat-height label. See SETEKONVENSJON above."""
    m = (merke or "").lower()
    if museum != "VA":
        return "topp", False
    if _RE_TOPP.search(m):
        return "topp", True
    if _RE_RAIL.search(m):
        return "rail", True
    return "topp", ("top" in m)


# ============================================================================ material class
# MATERIALREGEL (frozen). Input: the normalised catalogue field 'Materialar' (75 tokens in the population) and
# 'Teknikk', split on commas, exact tokens. Nothing else is used (no style, no date, no name).
#   strong metal  = Stål, Stålrør, Aluminium                          (always structure)
#   weak metal    = Jern, Metall                                       (structure ONLY if the chair has no solid-wood
#                   token: with wood these are fittings, castors, braces; flag 'metall_usikker' marks the cases)
#   solid wood    = Tre, Løvtre and the named species in TREVERK
#   plastic shell = Plast, Glasfiber, Polypropylen, Polyester, Polyetylen, Polykarbonat, Polyuretan, Melamin
#                   (NOT Polyamid: see deviation (e))
#   laminate      = Kryssfiner, Sponplate, or Teknikk token Laminering
#   LINE  := strong metal, or weak metal without solid wood
#   SHEET := plastic shell or laminate
#   class := 'LINE+SHEET' if LINE and SHEET   (metal frame carrying a shell: DSR, Ant, Polyprop)
#            'LINE'       if LINE only
#            'SHEET'      if SHEET only        (also with solid-wood legs, and with weak metal + wood)
#            'WOOD'       if solid wood and none of the above
#            'ANNA'       otherwise (no structural token: rattan/bamboo only, textile only, paper, marble, ...)
#   Do NOT change the class: upholstery and covers (Tekstil, Lær, Skinn, Silke, Ull, Hestetagl, Skumplast, Polyamid, ...),
#   cane and weave (Rotting, Strå, Bambus, Palme, Papirsnor, Vegetabilsk fiber), surface and ornament (Finer,
#   Maling, Perlemor, Emalje, Voks, Pappmasjé), small fittings (Messing, Bronse, Sølv), Gummi, Papir, Linoleum.
# Deviations from the history designer's DEV rule (scratch historie/felles.py), all decided on catalogue tokens:
#   (a) metal + shell is its own class instead of being counted as steel;
#   (b) Teknikk Formbøying / Dampbøying / Bøygd no longer make SHEET: in Nasjonalmuseet 'Formbøying' is also
#       used for bent steel (B.K.F., Diamond Chair) and steam-bent solid rods (Windsor, CH 24) are solid wood;
#       only Laminering (bent laminated wood) counts;
#   (c) Rotting, Bambus, Palme and Finer do not count as solid wood, so 'Jern, Rotting' (Mambo) is LINE;
#   (d) Sponplate counts as laminate.
#   (e) [independent check, 13 Nov] Polyamid is NOT a shell token. In all 10 population chairs that carry it the
#       nylon is rope, jersey, mesh or glides (Reflex 1, Berlage chair 'Eik med nylon', De La Warr Pavilion
#       Chair, Schultz sling chair, UN Lounge Chair, UP 3), never a shell. 5 chairs change class: Berlage x2 SHEET -> WOOD
#       (one of them DEV, O1153451), De La Warr x2 and UN Lounge LINE+SHEET -> LINE. DEV from 1925 is therefore
#       SHEET 20 (the history designer's rule gave 21), WOOD 14.
#   On the 1598 population chairs the two rules agree on LINE-or-not for all but 3 chairs.
# MEASURED ERROR (independent check, seeded sample of 40 population chairs from 1900, judged by eye against name
# and material comment): 3 clear errors (7.5 %), 3 debatable. The errors that tokens cannot remove:
#   'Plast' is a vinyl cover, glide or armrest and not a shell in 11 of the 35 chairs where it alone decides
#       (Kinsman T-series, Bertoia 'Metall, Plast', Breuer 1926 armrests, a mahogany chair of 1840 with a plastic
#       dust cover); 'Polyuretan' is upholstery foam in 3 of 12 (Djinn, Aeo, NMK.2016.0133);
#   'Stål'/'Aluminium' is a fitting and not the frame in about 6 of the 45 chairs that also have solid wood
#       (Jalk plywood chair 'steel bolts', Wagner 1901/1904 aluminium shoes, Lange 1966);
#   the Eames Lounge Chair ('Lær, Palisander, Stål', laminated shells) is LINE, not LINE+SHEET.
# All of these push chairs between classes at random with respect to shape; none can be fixed without reading
# the free-text comment, which is partly machine-written from the photographs and therefore not used.
# Known noise, left in on purpose (the rule is date-free): 'Kryssfiner' on a few chairs dated before 1870
# (repairs / normalisation), 'Jern' alone on 19th-century cast iron, and weak metal + wood after 1925 where the
# metal is in fact the frame (Breuer B64 'Metall, Tre' -> WOOD); 18 such chairs from 1925, flag 'metall_usikker'.
METALL_STERK = frozenset({"Stål", "Stålrør", "Aluminium"})
METALL_SVAK = frozenset({"Jern", "Metall"})
TREVERK = frozenset({"Tre", "Løvtre", "Mahogni", "Bøk", "Nøttetre", "Eik", "Furu", "Bjørk", "Ask", "Buksbom",
                     "Alm", "Palisander", "Ibenholt", "Teak", "Lønn", "Lind", "Gran", "Pæretre", "Or"})
PLASTSKAL = frozenset({"Plast", "Glasfiber", "Polypropylen", "Polyester", "Polyetylen", "Polykarbonat",
                       "Polyuretan", "Melamin"})
LAMINAT = frozenset({"Kryssfiner", "Sponplate"})
LAMINAT_TEKNIKK = frozenset({"Laminering"})
KLASSAR = ("LINE", "LINE+SHEET", "SHEET", "WOOD", "ANNA")


def materialflagg(materialar, teknikk=""):
    """frozenset of the structural facts behind the class:
    'metall' (structural metal = LINE), 'metall_usikker' (weak metal token together with solid wood, NOT counted
    as structure), 'plast', 'laminat', 'tre'."""
    t, k = _teikn(materialar), _teikn(teknikk)
    ut = set()
    tre = bool(t & TREVERK)
    if t & METALL_STERK or (t & METALL_SVAK and not tre):
        ut.add("metall")
    elif t & METALL_SVAK:
        ut.add("metall_usikker")
    if t & PLASTSKAL:
        ut.add("plast")
    if t & LAMINAT or k & LAMINAT_TEKNIKK:
        ut.add("laminat")
    if tre:
        ut.add("tre")
    return frozenset(ut)


def materialklasse(materialar, teknikk=""):
    """The ONE frozen material rule (MATERIALREGEL above) -> 'LINE' | 'LINE+SHEET' | 'SHEET' | 'WOOD' | 'ANNA'."""
    f = materialflagg(materialar, teknikk)
    line = "metall" in f
    sheet = "plast" in f or "laminat" in f
    if line and sheet:
        return "LINE+SHEET"
    if line:
        return "LINE"
    if sheet:
        return "SHEET"
    if "tre" in f:
        return "WOOD"
    return "ANNA"


def mat3(rec):
    """The regulation designer's three classes, derived from the same flags so that both designs use one rule:
    'metall' = structural metal (LINE or LINE+SHEET); 'plast' = plastic shell without structural metal;
    'tre' = everything else with wood or laminate (WOOD, and SHEET made of plywood/laminate); 'anna' = ANNA."""
    f = rec["materialflagg"]
    if "metall" in f:
        return "metall"
    if "plast" in f:
        return "plast"
    if "tre" in f or "laminat" in f:
        return "tre"
    return "anna"


# ============================================================================ suites
# SUITEREGEL (frozen, catalogue only). Two chairs belong to the same suite when they are linked by (a) or (b),
# and links are closed transitively (union-find), so a suite is a connected component:
#   (a) Nasjonalmuseet id stem: the id with a trailing set letter removed, with or without a following
#       '-number' ('OK-1989-0002A' and 'OK-1989-0002F' -> 'OK-1989-0002'; 'OK-05441B-1' -> 'OK-05441'),
#       and a trailing '.NNN' part number after 'NMK.YYYY.NNNN'. A 4-digit running number is never stripped.
#   (b) any museum: identical key (museum, H, B, D) shared by two or more rows (same model or set catalogued
#       under separate numbers, or one dimension record copied onto several objects).
#       [independent check, 13 Nov] The year is NO LONGER part of the key. With the year in it, sets and models
#       whose members carry slightly different datings were split (Selene 1967/1968, 3107 1955/1967, a set by
#       William Jones 1913/1914, Chippendale-pattern chairs 1755/1763, Bofinger 1964/1965), and 10 chairs that
#       share their exact dimension record with a DEV chair stayed in the held-out sample. The price: a few
#       unrelated chairs with coinciding measures are tied together, which only widens the intervals.
# The suite id is the smallest id in the component. Computed within the population of adult chairs
# (and separately within children's chairs and within stools).
# Not linked (known): the same model catalogued with different measures (Jason x3, Contour chair x2, Panton
# chair x2, Antelope x2); about 4 held-out chairs are such model-mates of a DEV chair.
_RE_STAMME = re.compile(r"(?<=\d)[A-Za-z](-\d+)?$")
_RE_NMKDEL = re.compile(r"^(NMK\.\d{4}\.\d{4})\.\d+$")


def id_stamme(oid, museum="NM"):
    """Rule (a): the Nasjonalmuseet id stem. V&A ids are returned unchanged."""
    if museum != "NM":
        return oid
    return _RE_STAMME.sub("", _RE_NMKDEL.sub(r"\1", oid))


def _maalnokkel(r):
    """(museum, H, B, D) as floats, or None when one of the three measures is missing."""
    H, B, D = _tal(r["H"]), _tal(r["B"]), _tal(r["D"])
    if H is None or B is None or D is None:
        return None
    return (r["museum"], H, B, D)


def _suitar(rader):
    """rader: dicts with id, museum, H, B, D (strings as in the table) -> dict id -> suite id."""
    forelder = {r["id"]: r["id"] for r in rader}

    def finn(x):
        while forelder[x] != x:
            forelder[x] = forelder[forelder[x]]
            x = forelder[x]
        return x

    grupper = {}
    for r in rader:
        if r["museum"] == "NM":
            grupper.setdefault(("stamme", id_stamme(r["id"])), []).append(r["id"])
        k = _maalnokkel(r)
        if k is not None:
            grupper.setdefault(("maal",) + k, []).append(r["id"])
    for g in grupper.values():
        for x in g[1:]:
            a, b = finn(g[0]), finn(x)
            if a != b:
                forelder[max(a, b)] = min(a, b)
    return {i: finn(i) for i in forelder}


def _populasjon():
    """Catalogue rows of the population: vaksenstol == '1' and maal_ok == '1'."""
    return _ein_gong("pop", lambda: [r for r in _reinsa() if r["vaksenstol"] == "1" and r["maal_ok"] == "1"])


def _suitetabell():
    return _ein_gong("suitar", lambda: _suitar(_populasjon()))


# ============================================================================ copied dimension records
# MAALKOPIREGEL (frozen, catalogue only; added by the independent check, 13 Nov).
# FINDING: the V&A API returns one and the same dimension record for groups of unrelated objects. Seven chairs
# (Antelope, Cross Check Chair, Margrét, Noah, Polypropylene Chair, Little Heavy, Atlantis Chair) all carry
# H 80.7, B 103.5, D 56.5, seat 45.8 and the note 'JS (17.12.2010)'; eight (Zig-Zag, Ad Hoc, Wait Chair, Laser
# Chair, Cabbage Chair, ...) all carry 66 x 78 x 76; four (Djinn, UP 3, Ball Chair, Keeler) 119 x 97.7 x 66.
# The frozen mesh script scales every mesh to the catalogue H, so for these chairs every centimetre value
# (sete_mesh, the silhouettes) is scaled to another object's height, and sete_kat is another object's seat.
# On DEV three of them (Cross Check Chair, Margrét, Little Heavy) passed the silhouette quality rule.
# RULE: let G be the population chairs with identical (museum, H, B, D).
#   maal_delt = len(G) - 1                      (how many OTHER chairs carry the same three measures)
#   maal_kopi = len(G) >= 2 and ( the years aar in G span more than MAALKOPI_AAR = 25 years
#                                 or G holds at least MAALKOPI_NAMN = 3 different names )
#   name = catalogue 'Namn' with parenthesised parts removed, lower-cased ('Chair (ukjent)' -> 'chair').
# A set or a model run (same measures, datings within 25 years, at most two names) is NOT flagged; it is a suite.
# Whole groups are flagged, because the catalogue cannot say which member owns the record: 46 population
# chairs in 11 groups (DEV 4, the group 80.7 x 103.5 x 56.5). Some flagged members are sound (six chairs of
# c. 1780 that share 82 x 53 x 45 with the Flax chair of 2016): the flag errs on the side of exclusion.
# USE: kvalitet() fails a flagged chair ('maal_kopi'). A module that uses sete_mesh, sete_kat or any other
# centimetre value WITHOUT kvalitet() must drop rec['maal_kopi'] itself.
MAALKOPI_AAR = 25
MAALKOPI_NAMN = 3
_RE_PARENTES = re.compile(r"\s*\(.*?\)\s*")


def _namn_norm(s):
    return _RE_PARENTES.sub(" ", s or "").strip().lower()


def _maalgrupper(rader):
    """rader: catalogue rows -> dict id -> (maal_delt, maal_kopi). See MAALKOPIREGEL."""
    s = _stolar()
    g = {}
    for r in rader:
        k = _maalnokkel(r)
        if k is not None:
            g.setdefault(k, []).append(r)
    ut = {}
    for v in g.values():
        aar = [a for a in (_aar(r["aar_fraa"]) for r in v) if a is not None]
        namn = {_namn_norm(s.get(r["id"], {}).get("Namn", "")) for r in v}
        kopi = len(v) >= 2 and ((bool(aar) and max(aar) - min(aar) > MAALKOPI_AAR) or len(namn) >= MAALKOPI_NAMN)
        for r in v:
            ut[r["id"]] = (len(v) - 1, bool(kopi))
    return ut


def _maaltabell():
    return _ein_gong("maalgrupper", lambda: _maalgrupper(_populasjon()))


def suite(rec):
    """Cluster id of a chair. Accepts a record (uses rec['suite'] when present) or an id string."""
    if isinstance(rec, dict):
        s = rec.get("suite")
        if s:
            return s
        oid = rec["id"]
    else:
        oid = rec
    return _suitetabell().get(oid, oid)


def _held_ids():
    """Catalogue-only definition of the held-out sample -> (ids, removed suite-mates of DEV chairs)."""
    def rekn():
        dev = set(dev_ids())
        st = _suitetabell()
        dev_suitar = {st[i] for i in dev}
        held, fjerna = [], []
        for r in _populasjon():
            if r["id"] in dev:
                continue
            (fjerna if st[r["id"]] in dev_suitar else held).append(r["id"])
        return sorted(held), sorted(fjerna)
    return _ein_gong("held_ids", rekn)


# ============================================================================ records
def _va_seteinfo():
    """dict id -> (full label of the seat value used, rail value, top value) for V&A non-stool records."""
    def rekn():
        ut = {}
        for oid, dims in _va_raa().items():
            hs = [h for h in _va_hoegder(dims) if h[2]]
            if not hs:
                continue
            rail = next((v for v, m, _ in hs if sete_konvensjon(m)[0] == "rail"), None)
            topp = next((v for v, m, _ in hs if sete_konvensjon(m)[0] == "topp"), None)
            ut[oid] = (hs[0][1], rail, topp)
        return ut
    return _ein_gong("va_seteinfo", rekn)


def _post(r, mesh, suite_id, maal=None):
    """One record from a catalogue row r, its mesh row (or None), its suite id and its (maal_delt, maal_kopi)
    pair (default: looked up in the population table; (0, False) for a chair outside it)."""
    if maal is None:
        maal = _maaltabell().get(r["id"], (0, False))
    s = _stolar().get(r["id"], {})
    aar = _aar(r["aar_fraa"])
    til = _aar(r["aar_til"])
    if til is not None and aar is not None and til < aar:
        til = None
    H = _tal(r["H"])
    sete_kat = _tal(r["sete"]) if r["sete_ok"] == "1" else None
    merke, rail, topp = r.get("sete_merke", ""), None, None
    if r["museum"] == "VA" and r["id"] in _va_seteinfo() and r.get("kjelde_sete") == "V&A API":
        merke, rail, topp = _va_seteinfo()[r["id"]]
    innanfor = lambda v: v if (v is not None and H is not None and 30 <= v <= 65 and v < H) else None
    if sete_kat is None:
        konv, eksp = None, False
    else:
        konv, eksp = sete_konvensjon(merke, r["museum"])
    if r["museum"] != "VA":
        rail, topp = None, sete_kat
    mat, tek = s.get("Materialar", ""), s.get("Teknikk", "")
    m = mesh or {}
    return {
        "id": r["id"], "museum": r["museum"], "type": r["type"], "namn": s.get("Namn", ""),
        "aar": aar, "aar_til": til, "spenn": (til - aar) if (aar is not None and til is not None) else None,
        "H": H, "B": _tal(r["B"]), "D": _tal(r["D"]),
        "sete_kat": sete_kat, "sete_konvensjon": konv, "sete_konv_eksplisitt": bool(eksp) and konv is not None,
        "sete_merke": merke, "sete_rail_kat": innanfor(rail), "sete_topp_kat": innanfor(topp),
        "nasjonalitet": r["nasjonalitet"], "materialar": mat, "teknikk": tek,
        "materialklasse": materialklasse(mat, tek), "materialflagg": materialflagg(mat, tek),
        "nemning": s.get("Nemning", ""), "produsent": s.get("Produsent", ""),
        "bilete_bguw": s.get("Bilete-bguw", ""), "bilete_url": s.get("Bilete-URL", ""),
        "suite": suite_id, "maal_delt": int(maal[0]), "maal_kopi": bool(maal[1]),
        "mesh_status": m.get("status") or None,
        "sete_mesh": _tal(m.get("sete_cm")),
        "sete_breidde_mesh": _tal(m.get("sete_breidde_cm")),
        "sete_djupn_mesh": _tal(m.get("sete_djupn_cm")),
        "flagg": frozenset(x for x in (m.get("flagg") or "").split(";") if x),
        "mesh": dict(m),
    }


def _katalogpostar(ids):
    """Records WITHOUT mesh fields for population ids (catalogue only). Internal: used for counting."""
    rad = {r["id"]: r for r in _populasjon()}
    st = _suitetabell()
    return [_post(rad[i], None, st[i]) for i in ids]


def les(utval):
    """Records of the sample.
    'dev' : the ids of data/dev_ids.txt, in file order; mesh fields ONLY from data/dev_mesh_maal.csv
            (5 of the 255 DEV chairs have no mesh row: mesh_status None).
    'held': GUARDED. Population minus DEV minus every chair whose suite contains a DEV chair, sorted by id;
            mesh fields from data/mesh_maal.csv."""
    rad = {r["id"]: r for r in _populasjon()}
    st = _suitetabell()
    if utval == "dev":
        mesh = _dev_mesh()
        ids = dev_ids()
        utanfor = [i for i in ids if i not in rad]
        if utanfor:
            raise ValueError("DEV-id utanfor populasjonen: %s" % utanfor[:5])
    elif utval == "held":
        _vakt("les('held')")
        mesh = _held_mesh()
        ids = _held_ids()[0]
    else:
        raise ValueError("utval må vere 'dev' eller 'held'")
    return [_post(rad[i], mesh.get(i), st[i]) for i in ids]


# ============================================================================ silhouettes and points
def _pakk_ut(sti, berre=None):
    z = np.load(sti, allow_pickle=False)
    ids = [str(i) for i in z["ids"]]
    side = np.unpackbits(z["side"], axis=-1)
    front = np.unpackbits(z["front"], axis=-1)
    return {i: (side[j], front[j]) for j, i in enumerate(ids) if berre is None or i in berre}


def silhuett(utval):
    """dict id -> (side, front); each (200,160) uint8 in {0,1}; 1 cm per pixel; row 0 = floor.
    Side view: column 0 = back, column 159 = front, centred on the bounding box. Front view: column 80 = middle.
    'dev'       reads data/dev_silhuettar.npz only (250 of the 255 DEV chairs have a silhouette).
    'held'      GUARDED; reads data/mesh_silhuettar.npz and returns only the ids of les('held').
    'barnestol' GUARDED; the ids of les_ekstra('barnestol')."""
    if utval == "dev":
        return _pakk_ut(DEV_SIL)
    if utval == "held":
        _vakt("data/mesh_silhuettar.npz")
        return _pakk_ut(HELD_SIL, set(_held_ids()[0]))
    if utval == "barnestol":
        _vakt("data/mesh_silhuettar.npz (barnestolar)")
        return _pakk_ut(HELD_SIL, {r["id"] for r in _barnerader()})
    raise ValueError("utval må vere 'dev', 'held' eller 'barnestol'")


def punktsky(oid):
    """(p, n): the 150 000 cached surface points (float32, model units) and unit normals (float32) of one chair,
    orientation and scaling as in analyse/14_mesh_maal.py. DEV ids are free; every other id is GUARDED."""
    if oid not in set(dev_ids()):
        _vakt("mesh_cache/%s.npz" % oid)
    z = np.load(os.path.join(MESH_CACHE, oid + ".npz"), allow_pickle=False)
    return z["p"], z["n"].astype(np.float32) / 127.0


# ============================================================================ quality rule
# KVALITETSREGEL (frozen). Starts from the history designer's DEV rule (scratch historie/formrom.py, conditions
# 2-5 with the same numbers) and adds 1, 6 and 7. A silhouette pair passes when ALL hold:
#   1. the chair has a mesh row with status 'ok...' and both silhouettes are non-empty         ('ingen_mesh', 'tom')
#   2. side bounding-box fill (pixels / (height x width of the bbox)) is within [0.08, 0.75]
#        above 0.75 = a block, not a chair ('blokk'); below 0.08 = dust / noise ('tynn')
#   3. the side silhouette does not touch column 0 or column 159 (clipped by the canvas)       ('kant')
#   4. the largest 8-connected component holds >= 0.90 of the side pixels
#        (several objects in one mesh, loose fragments)                                         ('fragment')
#   5. |side bbox width - catalogue D| / D <= 0.35 (depth far from the catalogue)               ('djupn')
#   6. none of the orientation flags of the frozen mesh script:                                 ('flagg:<name>')
#        opp_ikkje_y (up axis is not the model's y; 8 of 9 on DEV are debris), opp_ned? (upside-down suspicion),
#        rygg_usikker (back side undecided; all 10 on DEV are swapped side/front views, two chairs or debris),
#        silhuett_klipt (points outside the canvas)
#   7. the front silhouette does not touch column 0 or 159 and its largest component holds >= 0.90
#        of its pixels                                                                          ('front_kant', 'front_fragment')
#   8. the catalogue measures are not a copied dimension record (rec['maal_kopi'], MAALKOPIREGEL):
#        the mesh is scaled to the catalogue H, so a foreign H makes every centimetre wrong     ('maal_kopi')
# Quantities used: bbox fill, component share, canvas contact, side depth against catalogue D, flags that the
# mesh script sets from orientation, symmetry and catalogue B/D, and the catalogue-only copy flag. NOT used:
# seat height or any seat flag (ingen_flate, topp_ved_kant, fleire_toppar); opp_usikker and symmetri_uklar (on
# DEV those silhouettes are sound); B_D_bytt? (it compares the mesh box with catalogue B and D, which condition 5
# already does; the 3 DEV chairs that carry it and pass 2-5 are correctly oriented on inspection); front width,
# arm height, zone content, boundary statistics, year, material.
# Two indirect links to outcomes, both inherited and both small: the frozen script decides rygg_usikker with the
# seat-level points as its reference when a seat was found; and the bbox fill of condition 2 rises with the
# filled share under the seat (its upper limit removes fully upholstered block-shaped armchairs: 1 on DEV).
# DEV: conditions 2-5 alone fail 29 of 250; conditions 1-7 fail 35; the full rule fails 38 of 250 (212 pass:
# share 0.848 of the chairs with a silhouette, 0.831 of the 255 DEV chairs). The flags in 6 were chosen after
# looking at DEV contact sheets.
# INDEPENDENT CHECK (13 Nov, contact sheets of the 35 rejected and of 40 accepted DEV silhouettes, seeded):
#   rejected: 22 are debris, blocks, two chairs in one mesh or swapped views; 1 has a broken mesh; 9 are sound
#   silhouettes whose depth is more than 35 % above catalogue D (raked back legs, projecting arms: the catalogue D
#   of those chairs looks like a seat depth), 1 is a sound block-shaped club chair ('blokk'), 1 a sound Ekstrem
#   chair (opp_ikkje_y), 1 a sound Dr Sonderbar (rygg_usikker: front and back cannot be told apart).
#   So up to 12 of 35 rejections drop a usable silhouette; all 12 are conservative, none depends on a seat value.
#   accepted: 39 of 40 sound, 1 doubtful (O134354, front view slightly rotated); no swapped or upside-down view.
#   opp_ned? never decides alone on DEV (its 7 chairs all fail another condition as well).
KV_FYLL_MIN, KV_FYLL_MAX = 0.08, 0.75
KV_STORSTE_MIN = 0.90
KV_DJUPN_REL = 0.35
KV_FLAGG = frozenset({"opp_ikkje_y", "opp_ned?", "rygg_usikker", "silhuett_klipt"})
KV_FRONT_BREIDD_REL = 0.35      # only in kvalitet_front()
_ATTE = np.ones((3, 3), int)


def _bbox(s):
    ys, xs = np.nonzero(s)
    if len(ys) == 0:
        return None
    return int(ys.max()) + 1, int(xs.max() - xs.min()) + 1, int(len(ys))    # height from floor, width, pixels


def _storste_del(s, n_piksel):
    lab, n = ndimage.label(s, structure=_ATTE)
    if n == 0:
        return 0.0
    return float(np.bincount(lab.ravel())[1:].max()) / n_piksel


def kvalitet(rec, side, front):
    """The frozen silhouette quality rule (KVALITETSREGEL above).
    -> (ok, grunn): grunn is 'ok' or the ';'-joined codes of ALL failed conditions.
    A chair without a silhouette is passed as kvalitet(rec, None, None) and fails with 'ingen_mesh':
        sil = silhuett('dev');  ok, grunn = kvalitet(rec, *sil.get(rec['id'], (None, None)))"""
    if side is None or front is None or not str(rec.get("mesh_status") or "").startswith("ok"):
        return False, "ingen_mesh"
    side = np.asarray(side) > 0
    front = np.asarray(front) > 0
    bs, bf = _bbox(side), _bbox(front)
    if bs is None or bf is None:
        return False, "tom"
    grunnar = []
    h, w, npx = bs
    fyll = npx / float(h * w)
    if fyll > KV_FYLL_MAX:
        grunnar.append("blokk")
    if fyll < KV_FYLL_MIN:
        grunnar.append("tynn")
    if side[:, 0].any() or side[:, -1].any():
        grunnar.append("kant")
    if _storste_del(side, npx) < KV_STORSTE_MIN:
        grunnar.append("fragment")
    D = rec.get("D")
    if D is None or abs(w - D) / D > KV_DJUPN_REL:
        grunnar.append("djupn")
    for fl in sorted(rec.get("flagg", frozenset()) & KV_FLAGG):
        grunnar.append("flagg:" + fl)
    if front[:, 0].any() or front[:, -1].any():
        grunnar.append("front_kant")
    if _storste_del(front, bf[2]) < KV_STORSTE_MIN:
        grunnar.append("front_fragment")
    if rec.get("maal_kopi"):
        grunnar.append("maal_kopi")
    return (not grunnar), (";".join(grunnar) if grunnar else "ok")


def kvalitet_front(rec, front):
    """OPTIONAL extra gate, not part of kvalitet(): for a module that reads shape from the FRONT view and whose
    outcome is not the front width itself. Passes when the front silhouette is non-empty, does not touch the
    canvas sides, has its largest component >= 0.90 of the pixels, and
    |front bbox width - catalogue B| / B <= 0.35 ('front_breidd').
    DEV: 5 of the 212 chairs that pass kvalitet() fail this gate."""
    if front is None:
        return False, "ingen_mesh"
    front = np.asarray(front) > 0
    bf = _bbox(front)
    if bf is None:
        return False, "tom"
    grunnar = []
    if front[:, 0].any() or front[:, -1].any():
        grunnar.append("front_kant")
    if _storste_del(front, bf[2]) < KV_STORSTE_MIN:
        grunnar.append("front_fragment")
    B = rec.get("B")
    if B is None or abs(bf[1] - B) / B > KV_FRONT_BREIDD_REL:
        grunnar.append("front_breidd")
    return (not grunnar), (";".join(grunnar) if grunnar else "ok")


# ============================================================================ statistics
def _endeleg(x):
    x = np.asarray([np.nan if v is None else v for v in x], float) if not isinstance(x, np.ndarray) \
        else np.asarray(x, float)
    return x[np.isfinite(x)]


def mad_sd(x):
    """1.4826 * median(|x - median(x)|): robust SD. None / NaN are dropped; NaN if nothing is left."""
    x = _endeleg(x)
    if len(x) == 0:
        return float("nan")
    return float(1.4826 * np.median(np.abs(x - np.median(x))))


def robust_spreiing(x):
    """1.4826 * MAD / median: robust coefficient of variation. None / NaN are dropped."""
    x = _endeleg(x)
    if len(x) == 0:
        return float("nan")
    m = np.median(x)
    return float(1.4826 * np.median(np.abs(x - m)) / m) if m != 0 else float("nan")


def _flyt(x):
    return np.asarray([np.nan if v is None else v for v in x], float)


def spearman(x, y):
    """Spearman rank correlation (float). Pairs with None / NaN are dropped; NaN if fewer than 3 pairs or no variation."""
    x, y = _flyt(x), _flyt(y)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        return float("nan")
    rx, ry = rankdata(x[ok]), rankdata(y[ok])
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def _kovariatar(covars, n):
    """-> (list of numeric columns, list of categorical columns). A covariate is categorical when its values
    cannot all be read as numbers (strings such as museum or class); booleans are numeric 0/1."""
    if covars is None:
        return [], []
    if isinstance(covars, np.ndarray):
        covars = [covars] if covars.ndim == 1 else [covars[:, j] for j in range(covars.shape[1])]
    else:
        covars = list(covars)
        if covars and not isinstance(covars[0], (list, tuple, np.ndarray)):
            covars = [covars]                  # a single covariate given as a flat list
    num, kat = [], []
    for c in covars:
        c = list(c)
        if len(c) != n:
            raise ValueError("kovariat med lengd %d, venta %d" % (len(c), n))
        try:
            num.append(np.asarray([np.nan if v is None else float(v) for v in c], float))
        except (TypeError, ValueError):
            kat.append(np.asarray([None if v is None else str(v) for v in c], object))
    return num, kat


def partial_spearman(x, y, covars):
    """Partial Spearman correlation of x and y given covariates.
    covars: a list of covariates (each a sequence of length n), a single sequence, or a 2-D array (columns).
    Numeric covariates are rank-transformed; non-numeric ones (museum, class, ...) enter as dummy variables
    (one level dropped). x and y are rank-transformed, both are residualised by least squares on
    [1, ranked numeric covariates, dummies], and the Pearson correlation of the residuals is returned.
    Rows with None / NaN in x, y or any covariate are dropped. NaN if too few rows or no residual variation."""
    x, y = _flyt(x), _flyt(y)
    n = len(x)
    num, kat = _kovariatar(covars, n)
    ok = np.isfinite(x) & np.isfinite(y)
    for c in num:
        ok &= np.isfinite(c)
    for c in kat:
        ok &= np.asarray([v is not None for v in c])
    m = int(ok.sum())
    kol = [np.ones(m)]
    for c in num:
        kol.append(rankdata(c[ok]))
    for c in kat:
        v = c[ok]
        for niva in sorted(set(v))[1:]:
            kol.append((v == niva).astype(float))
    Z = np.column_stack(kol)
    if m - Z.shape[1] < 3:
        return float("nan")
    rx, ry = rankdata(x[ok]), rankdata(y[ok])
    ex = rx - Z @ np.linalg.lstsq(Z, rx, rcond=None)[0]
    ey = ry - Z @ np.linalg.lstsq(Z, ry, rcond=None)[0]
    if ex.std() < 1e-9 or ey.std() < 1e-9:
        return float("nan")
    return float(np.corrcoef(ex, ey)[0, 1])


def klyngebootstrap(recs, stat_fn, n=N_BOOT, seed=FRO, strata=None):
    """Cluster bootstrap over suites. Whole suites (suite(rec)) are drawn with replacement, as many as there are
    suites in recs; stat_fn receives the list of records of the drawn suites (a suite drawn twice appears twice)
    and returns a number or a fixed-length sequence of numbers. Returns np.ndarray of shape (n,) or (n, k).
    strata: optional function rec -> label (for instance lambda r: r['museum']); suites are then resampled within
    each stratum so that its number of suites is fixed. Deterministic for a given order of recs.
    stat_fn must itself return NaN for a degenerate resample; exceptions are not swallowed. Use ki() for the interval."""
    recs = list(recs)
    grupper = {}
    for r in recs:
        grupper.setdefault(suite(r), []).append(r)
    klynger = list(grupper.values())
    if not klynger:
        return np.full(n, np.nan)
    if strata is None:
        lag = [np.arange(len(klynger))]
    else:
        etter = {}
        for j, k in enumerate(klynger):
            etter.setdefault(strata(k[0]), []).append(j)
        lag = [np.asarray(v) for _, v in sorted(etter.items(), key=lambda kv: str(kv[0]))]
    rng = np.random.default_rng(seed)
    ut = []
    for _ in range(n):
        idx = np.concatenate([l[rng.integers(0, len(l), len(l))] for l in lag])
        ut.append(stat_fn([r for j in idx for r in klynger[j]]))
    return np.asarray(ut, float)


def ki(boot, niva=0.95):
    """Percentile interval (lo, hi) of bootstrap values along axis 0, ignoring NaN."""
    a = 100 * (1 - niva) / 2
    b = np.asarray(boot, float)
    if b.size == 0 or np.all(np.isnan(b)):
        return float("nan"), float("nan")
    lo, hi = np.nanpercentile(b, [a, 100 - a], axis=0)
    return (float(lo), float(hi)) if np.ndim(lo) == 0 else (lo, hi)


# ============================================================================ extra groups (sealed)
def _barnerader():
    """Catalogue rows of children's chairs: type == 'Barnestol' and maal_ok == '1'."""
    return [r for r in _reinsa() if r["type"] == BARNETYPE and r["maal_ok"] == "1"]


def _krakkhoegd(r, dims):
    """Frozen rule for the height of a stool -> (H cm or None, source, seat-labelled height or None).
      1. H of stolar_reinsa.csv when present (whole-object height by the rules of 04_reinsa_tabell.py; it is there
         also when maal_ok == '0', which a stool gets because R6 demands H >= 50)          source 'H'
      2. else the first V&A Height whose label mentions 'seat' (unit rules of 04)           source 'sete'
      3. else the first V&A Height of any part                                              source 'raa'
    No range filter is applied here; the test module fixes its own limits."""
    hs = _va_hoegder(dims)
    sete = next((v for v, _, er in hs if er), None)
    if sete is None:
        sete = _tal(r.get("sete"))
    H = _tal(r.get("H"))
    if H is not None:
        return H, "H", sete
    if sete is not None:
        return sete, "sete", sete
    if hs:
        return hs[0][0], "raa", None
    return None, "", None


def _krakkpost(r, dims, suite_id, maal=(0, False)):
    """Record of one stool from its (unblanked) catalogue row and raw V&A dimension list."""
    H, kjelde, sete = _krakkhoegd(r, dims)
    r2 = dict(r)
    r2["sete_ok"] = "0"
    p = _post(r2, None, suite_id, maal)
    p["H"], p["H_kjelde"] = H, kjelde
    p["sete_kat"] = sete                    # seat-labelled height, NOT range-filtered for stools
    p["sete_topp_kat"] = p["sete_rail_kat"] = None
    p["maal_ok"] = r.get("maal_ok") == "1"
    return p


def les_ekstra(kind):
    """GUARDED exactly like les('held').
    'barnestol': children's chairs (type == 'Barnestol', maal_ok == '1'), the record keys of les(), mesh fields
                 from data/mesh_maal.csv (mesh_status None if the frozen mesh script has no row for the chair).
    'krakk'    : stools (type in {'Krakk', 'Stol utan rygg'}), catalogue fields only. H follows _krakkhoegd()
                 (key 'H_kjelde' gives the source); B, D as catalogued (may be None); 'maal_ok' is a bool;
                 'sete_kat' is the seat-labelled height when the record has one; mesh fields are empty."""
    if kind == "barnestol":
        _vakt("les_ekstra('barnestol')")
        rader = _barnerader()
        st = _suitar(rader)
        mesh = _held_mesh()
        mg = _maalgrupper(_populasjon() + rader)      # copied records are judged against the adult chairs too
        return [_post(r, mesh.get(r["id"]), st[r["id"]], mg.get(r["id"], (0, False)))
                for r in sorted(rader, key=lambda r: r["id"])]
    if kind == "krakk":
        _vakt("les_ekstra('krakk')")
        rader = _reinsa_krakk()
        raa = _va_raa(krakk=True)
        utfylt = []
        for r in rader:                      # suites need a height: fill H from the frozen rule first
            H = _krakkhoegd(r, raa.get(r["id"]))[0]
            utfylt.append(dict(r, H=("" if H is None else "%.1f" % H)))
        st = _suitar(utfylt)
        mg = _maalgrupper(_populasjon() + utfylt)     # only stools with H, B and D can be judged
        return [_krakkpost(r, raa.get(r["id"]), st[r["id"]], mg.get(r["id"], (0, False)))
                for r in sorted(rader, key=lambda r: r["id"])]
    raise ValueError("kind må vere 'barnestol' eller 'krakk'")


def tel_ekstra(kind):
    """UNGUARDED. Counts and names only, no measured value is returned or compared.
    'barnestol': n (maal_ok == '1', the group of les_ekstra), n_alle (all rows of the type), per museum,
                 n_med_katalogsete, namn (sorted list of (id, name, aar)).
    'krakk'    : n (all rows of the types), per museum, n_med_H (a height is present in the cleaned table),
                 n_H_berre_i_raadata (no height there, but a Height entry in the raw V&A record), n_utan_H,
                 namn (sorted list of (id, name, aar)) so that a module can freeze a name rule
                 (footstools) before unsealing."""
    s = _stolar()
    namn = lambda rader: sorted((r["id"], s.get(r["id"], {}).get("Namn", ""), _aar(r["aar_fraa"])) for r in rader)
    tel = lambda rader, f: {m: sum(1 for r in rader if r["museum"] == m and f(r)) for m in ("NM", "VA")}
    if kind == "barnestol":
        alle = [r for r in _reinsa() if r["type"] == BARNETYPE]
        rader = _barnerader()
        return {"kind": kind, "n": len(rader), "n_alle": len(alle), "per_museum": tel(rader, lambda r: True),
                "n_med_katalogsete": sum(1 for r in rader if r["sete_ok"] == "1"), "namn": namn(rader)}
    if kind == "krakk":
        rader = [r for r in _reinsa() if r["type"] in KRAKKTYPAR]
        utan = {r["id"] for r in rader if not r["_har_H"]}
        raa_har = set()
        if utan:                             # presence of a Height entry only; no value is kept
            with open(VA_RAA, encoding="utf-8") as f:
                for linje in f:
                    m = re.match(r'\{"id":\s*"([^"]+)"', linje)
                    if m and m.group(1) in utan:
                        p = json.loads(linje)
                        if any((d.get("dimension") or "").strip() == "Height" and _va_tal(d.get("value")) is not None
                               and (d.get("unit") or "").strip().lower() in TIL_CM
                               for d in (p.get("dimensions") or [])):
                            raa_har.add(p["id"])
        # 'n_maal_ok' was removed by the independent check: maal_ok demands H >= 50 cm, so the count of stools
        # that pass it is a statistic of the sealed heights.
        return {"kind": kind, "n": len(rader), "per_museum": tel(rader, lambda r: True),
                "n_med_H": sum(1 for r in rader if r["_har_H"]),
                "n_H_berre_i_raadata": len(raa_har), "n_utan_H": len(utan - raa_har), "namn": namn(rader)}
    raise ValueError("kind må vere 'barnestol' eller 'krakk'")


# ============================================================================ counting (catalogue only)
def klassetabell(recs, steg=25, golv=1800):
    """dict bin -> dict class -> n, for printing; bin = aarsbolk(aar, steg, golv), None = no year."""
    ut = {}
    for r in recs:
        b = aarsbolk(r["aar"], steg, golv)
        ut.setdefault(b, dict.fromkeys(KLASSAR, 0))[r["materialklasse"]] += 1
    return ut


def tel_held():
    """UNGUARDED. Counts of the held-out sample, computed from the catalogue only (no mesh file is opened)."""
    ids, fjerna = _held_ids()
    recs = _katalogpostar(ids)
    fj = _katalogpostar(fjerna)
    mus = ("NM", "VA")
    per = lambda rs, f=lambda r: True: {m: sum(1 for r in rs if r["museum"] == m and f(r)) for m in mus}
    kl25 = {m: dict.fromkeys(KLASSAR, 0) for m in mus + ("alle",)}
    for r in recs:
        if r["aar"] is not None and r["aar"] >= 1925:
            kl25[r["museum"]][r["materialklasse"]] += 1
            kl25["alle"][r["materialklasse"]] += 1
    b50 = {}
    for r in recs:
        b = aarsbolk(r["aar"], 50, 1600)
        b50.setdefault(b, {"NM": 0, "VA": 0})[r["museum"]] += 1
    return {
        "populasjon": len(_populasjon()), "dev": len(dev_ids()),
        "n": len(recs), "per_museum": per(recs),
        "med_katalogsete": per(recs, lambda r: r["sete_kat"] is not None),
        "utan_katalogsete": per(recs, lambda r: r["sete_kat"] is None),
        "sete_konvensjon": {k: sum(1 for r in recs if r["sete_konvensjon"] == k) for k in ("rail", "topp")},
        "materialklasse_fraa_1925": kl25,
        "per_50_aar": {k: b50[k] for k in sorted(b50, key=lambda v: (v is None, v))},
        "utan_aar": sum(1 for r in recs if r["aar"] is None),
        "suitar": len({r["suite"] for r in recs}),
        "maal_kopi": per(recs, lambda r: r["maal_kopi"]),
        "maal_kopi_med_katalogsete": per(recs, lambda r: r["maal_kopi"] and r["sete_kat"] is not None),
        "fjerna_suitefeller": len(fj), "fjerna_per_museum": per(fj),
        "fjerna_med_katalogsete": per(fj, lambda r: r["sete_kat"] is not None),
    }


# ============================================================================ self-test
def _skriv_klassetabell(tittel, recs):
    t = klassetabell(recs)
    print(tittel)
    print("    %-7s %5s %5s %10s %6s %5s %5s" % ("bolk", "n", "LINE", "LINE+SHEET", "SHEET", "WOOD", "ANNA"))
    for b in sorted(t, key=lambda v: (v is None, v)):
        namn = "utan år" if b is None else ("<1800" if b < 1800 else str(b))
        c = t[b]
        print("    %-7s %5d %5d %10d %6d %5d %5d" % (namn, sum(c.values()), c["LINE"], c["LINE+SHEET"],
                                                    c["SHEET"], c["WOOD"], c["ANNA"]))
    tot = dict.fromkeys(KLASSAR, 0)
    for c in t.values():
        for k in KLASSAR:
            tot[k] += c[k]
    print("    %-7s %5d %5d %10d %6d %5d %5d" % ("sum", sum(tot.values()), tot["LINE"], tot["LINE+SHEET"],
                                                tot["SHEET"], tot["WOOD"], tot["ANNA"]))


def _sjolvtest():
    from collections import Counter
    sys.stdout.reconfigure(encoding="utf-8")
    print("felles.py sjølvtest   FRO=%d  N_BOOT=%d   forsegling open: %s" % (FRO, N_BOOT, _open_er()))

    # ---- guard
    if not _open_er():
        for namn, fn in (("les('held')", lambda: les("held")), ("silhuett('held')", lambda: silhuett("held")),
                         ("les_ekstra('barnestol')", lambda: les_ekstra("barnestol")),
                         ("les_ekstra('krakk')", lambda: les_ekstra("krakk")),
                         ("silhuett('barnestol')", lambda: silhuett("barnestol")),
                         ("punktsky(<ikkje-DEV>)", lambda: punktsky(_held_ids()[0][0]))):
            try:
                fn()
                raise SystemExit("FEIL: %s gjekk gjennom utan nøkkel" % namn)
            except PermissionError:
                print("  vakt ok: %-26s -> PermissionError" % namn)

    # ---- DEV
    dev = les("dev")
    sil = silhuett("dev")
    c = Counter(r["museum"] for r in dev)
    print("\nDEV: %d stolar (NM %d, VA %d); mesh-rad %d; silhuett %d; sete_mesh %d; sete_kat %d"
          % (len(dev), c["NM"], c["VA"], sum(r["mesh_status"] is not None for r in dev), len(sil),
             sum(r["sete_mesh"] is not None for r in dev), sum(r["sete_kat"] is not None for r in dev)))
    print("  mesh_status:", dict(Counter(str(r["mesh_status"]) for r in dev)))
    print("  flagg:", dict(Counter(f for r in dev for f in r["flagg"]).most_common()))
    print("  setekonvensjon:", dict(Counter((r["museum"], r["sete_konvensjon"], r["sete_konv_eksplisitt"]) for r in dev)))
    print("  utan år: %d; med aar_til: %d; suitar i DEV: %d (stolar i fleirstol-suitar innan DEV: %d)"
          % (sum(r["aar"] is None for r in dev), sum(r["aar_til"] is not None for r in dev),
             len({r["suite"] for r in dev}),
             sum(v for v in Counter(r["suite"] for r in dev).values() if v > 1)))

    # ---- material classes (catalogue only)
    pop_ids = [r["id"] for r in _populasjon()]
    pop = _katalogpostar(pop_ids)
    _skriv_klassetabell("\nMaterialklasse per 25 år, heile populasjonen (%d, berre katalog):" % len(pop), pop)
    _skriv_klassetabell("\nMaterialklasse per 25 år, DEV (%d):" % len(dev), dev)
    print("\n  mat3 (regulering) frå 1925, populasjon:",
          dict(Counter(mat3(r) for r in pop if r["aar"] and r["aar"] >= 1925)),
          "| DEV:", dict(Counter(mat3(r) for r in dev if r["aar"] and r["aar"] >= 1925)))
    print("  flagg 'metall_usikker' frå 1925: populasjon %d, DEV %d"
          % (sum("metall_usikker" in r["materialflagg"] for r in pop if r["aar"] and r["aar"] >= 1925),
             sum("metall_usikker" in r["materialflagg"] for r in dev if r["aar"] and r["aar"] >= 1925)))

    # ---- suites
    st = Counter(r["suite"] for r in pop)
    nm_stammer = Counter(id_stamme(r["id"]) for r in pop if r["museum"] == "NM")
    maal = Counter((r["museum"], r["H"], r["B"], r["D"], r["aar"]) for r in pop)
    maal3 = Counter((r["museum"], r["H"], r["B"], r["D"]) for r in pop)
    print("\nSuitar (populasjon %d): %d klynger; %d med fleire stolar, som held %d stolar; største %d"
          % (len(pop), len(st), sum(v > 1 for v in st.values()), sum(v for v in st.values() if v > 1), max(st.values())))
    print("  storleik -> tal klynger:", dict(sorted(Counter(st.values()).items())))
    print("  NM: %d av %d stolar i id-stammer med fleire stolar; %d rader deler (museum, H, B, D, år) med ei anna rad"
          % (sum(v for v in nm_stammer.values() if v > 1), sum(nm_stammer.values()),
             sum(v for v in maal.values() if v > 1)))
    print("  %d rader deler (museum, H, B, D) utan år (nøkkelen i regelen)" % sum(v for v in maal3.values() if v > 1))
    kop = [r for r in pop if r["maal_kopi"]]
    print("  kopierte målpostar (maal_kopi): %d stolar i %d grupper (NM %d, VA %d); i DEV: %d (%s)"
          % (len(kop), len({(r["museum"], r["H"], r["B"], r["D"]) for r in kop}),
             sum(r["museum"] == "NM" for r in kop), sum(r["museum"] == "VA" for r in kop),
             sum(r["maal_kopi"] for r in dev), ", ".join(r["namn"] for r in dev if r["maal_kopi"])))

    # ---- quality rule on DEV
    res = {r["id"]: kvalitet(r, *sil.get(r["id"], (None, None))) for r in dev}
    med = [r for r in dev if r["id"] in sil]
    n_ok = sum(res[r["id"]][0] for r in med)
    print("\nKvalitetsregel, DEV: %d av %d med silhuett går gjennom (del %.3f); av alle %d DEV: %.3f"
          % (n_ok, len(med), n_ok / len(med), len(dev), n_ok / len(dev)))
    print("  grunnar (ein stol kan ha fleire):",
          dict(Counter(g for r in dev for g in res[r["id"]][1].split(";") if g != "ok").most_common()))
    for k in KLASSAR:
        a = [r for r in med if r["materialklasse"] == k and r["aar"] and r["aar"] >= 1925]
        b = [r for r in med if r["materialklasse"] == k and r["aar"] and r["aar"] < 1900]
        print("  %-10s frå 1925: %2d av %2d gjennom | før 1900: %3d av %3d"
              % (k, sum(res[r["id"]][0] for r in a), len(a), sum(res[r["id"]][0] for r in b), len(b)))
    godk = [r for r in med if res[r["id"]][0]]
    print("  kvalitet_front i tillegg: %d av %d fell" % (sum(not kvalitet_front(r, sil[r["id"]][1])[0] for r in godk), len(godk)))

    # ---- statistics helpers on DEV (sanity only)
    par = [r for r in dev if r["sete_mesh"] is not None and r["sete_kat"] is not None]
    rho = lambda rs: spearman([r["sete_mesh"] for r in rs], [r["sete_kat"] for r in rs])
    b = klyngebootstrap(par, rho)
    print("\nSjekk av hjelparane på DEV: Spearman(sete_mesh, sete_kat) = %.3f, klyngebootstrap 95 %% [%.3f, %.3f] (n=%d, %d suitar)"
          % (rho(par), *ki(b), len(par), len({r["suite"] for r in par})))
    print("  partial (| museum, H) = %.3f; robust spreiing sete_kat %.3f, sete_mesh %.3f; MAD-SD sete_kat %.2f cm"
          % (partial_spearman([r["sete_mesh"] for r in par], [r["sete_kat"] for r in par],
                              [[r["museum"] for r in par], [r["H"] for r in par]]),
             robust_spreiing([r["sete_kat"] for r in par]), robust_spreiing([r["sete_mesh"] for r in par]),
             mad_sd([r["sete_kat"] for r in par])))

    # ---- held-out counts (catalogue only)
    t = tel_held()
    print("\ntel_held() (berre katalog): populasjon %d - DEV %d - suitefeller %d = HELD %d  (NM %d, VA %d); %d suitar"
          % (t["populasjon"], t["dev"], t["fjerna_suitefeller"], t["n"], t["per_museum"]["NM"], t["per_museum"]["VA"],
             t["suitar"]))
    print("  fjerna som suitefeller av DEV-stolar: NM %d, VA %d (med katalogsete: NM %d, VA %d)"
          % (t["fjerna_per_museum"]["NM"], t["fjerna_per_museum"]["VA"],
             t["fjerna_med_katalogsete"]["NM"], t["fjerna_med_katalogsete"]["VA"]))
    print("  med katalogsete: NM %d, VA %d | utan: NM %d, VA %d | konvensjon: rail %d, topp %d"
          % (t["med_katalogsete"]["NM"], t["med_katalogsete"]["VA"], t["utan_katalogsete"]["NM"],
             t["utan_katalogsete"]["VA"], t["sete_konvensjon"]["rail"], t["sete_konvensjon"]["topp"]))
    print("  av desse med kopiert målpost (maal_kopi): NM %d, VA %d (med katalogsete: NM %d, VA %d)"
          % (t["maal_kopi"]["NM"], t["maal_kopi"]["VA"], t["maal_kopi_med_katalogsete"]["NM"],
             t["maal_kopi_med_katalogsete"]["VA"]))
    for m in ("alle", "NM", "VA"):
        print("  materialklasse frå 1925, %-4s:" % m, t["materialklasse_fraa_1925"][m])
    print("  per 50 år (NM/VA):", "  ".join(
        "%s: %d/%d" % ("utan år" if k is None else ("<1600" if k < 1600 else k), v["NM"], v["VA"])
        for k, v in t["per_50_aar"].items()))

    # ---- extra groups (counts and names only)
    for kind in ("barnestol", "krakk"):
        e = tel_ekstra(kind)
        print("\ntel_ekstra('%s'):" % kind, {k: v for k, v in e.items() if k != "namn"})
        print("  namn (dei 8 første av %d):" % len(e["namn"]), "; ".join("%s %s" % (n, a) for _, n, a in e["namn"][:8]))
    print("\nferdig.")


if __name__ == "__main__":
    _sjolvtest()
