"""Byggjer analysetabellen for artikkel 2 med faste, skrivne reglar.

Inn:  STOLAR/STOLAR.csv  og  analyse/data/va_dimensjonar_raa.jsonl (frå 03_va_dimensjonar.py)
Ut:   analyse/data/stolar_reinsa.csv  (éi rad per objekt, ingen rader blir sletta; flagg seier kva som gjeld)

Reglar
  R1  0.0 i eit mål tyder manglande verdi.
  R2  For V&A-objekt gjeld måla frå V&A sitt API framfor STOLAR.csv (einingar rekna om til cm).
      Heile-objektet-mål: del-feltet tomt; elles «overall»/«maximum»; elles manglande.
  R3  Setehøgd frå V&A: Height der del, kvalifikator eller merknad nemner «seat» (ikkje breidd/djupn).
  R4  Setehøgd lik totalhøgd i Nasjonalmuseet-rader er ein kopifeil og blir sett til manglande.
  R5  vaksenstol = Nemning ikkje i {Krakk, Barnestol, Benkestol, Stol utan rygg} og ikkje fotografi (NAMF-ID).
  R6  maal_ok = H 50-200, B 25-150, D 25-150 (cm).
  R7  sete_ok = setehøgd finst, er lågare enn H og ligg i 30-65 cm.
"""
import csv, json, os, sys

sys.stdout.reconfigure(encoding="utf-8")
ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIL_CM = {"cm": 1.0, "mm": 0.1, "in": 2.54, "ft": 30.48, "m": 100.0}


def tal(s):
    try:
        v = float(str(s).replace(",", "."))
        return v if v > 0 else None  # R1
    except (ValueError, TypeError):
        return None


def va_maal(dims):
    """Returnerer (H, B, D, sete, sete_merke) i cm frå V&A si dimensjonsliste."""
    heil = {"Height": [], "Width": [], "Depth": []}
    samla = {"Height": [], "Width": [], "Depth": []}
    sete, merke = None, ""
    for d in dims or []:
        typ = (d.get("dimension") or "").strip()
        f = TIL_CM.get((d.get("unit") or "").strip().lower())
        v = tal(d.get("value"))
        if typ not in heil or f is None or v is None:
            continue
        v *= f
        del_ = (d.get("part") or "").strip().lower()
        ekstra = " ".join([del_, (d.get("qualifier") or "").lower(), (d.get("note") or "").lower()])
        if typ == "Height" and "seat" in ekstra:
            if sete is None:
                sete, merke = v, ekstra.strip()[:60]
            continue
        if "seat" in ekstra:
            continue
        if del_ == "":
            heil[typ].append(v)
        elif del_.startswith(("overall", "maximum", "from floor to top")):
            samla[typ].append(v)
    vel = lambda t: (heil[t] or samla[t] or [None])[0]
    return vel("Height"), vel("Width"), vel("Depth"), sete, merke


va = {}
sti_va = os.path.join(ROT, "analyse", "data", "va_dimensjonar_raa.jsonl")
if os.path.exists(sti_va):
    for linje in open(sti_va, encoding="utf-8"):
        p = json.loads(linje)
        if p.get("status") == "ok":
            va[p["id"]] = va_maal(p.get("dimensions"))

rader = list(csv.DictReader(open(os.path.join(ROT, "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline="")))
UTE = {"Krakk", "Barnestol", "Benkestol", "Stol utan rygg"}
ut = []
for r in rader:
    oid = r["Objekt-ID"]
    museum = "VA" if "vam.ac.uk" in r["Nasjonalmuseet"] else "NM"
    H, B, D, S = (tal(r[k]) for k in ("Høgde (cm)", "Breidde (cm)", "Djupn (cm)", "Setehøgde (cm)"))
    kjelde_maal, kjelde_sete, merke = "STOLAR.csv", ("katalog" if S else ""), ""
    if museum == "VA" and oid in va:  # R2, R3
        h, b, d, s, merke = va[oid]
        H, B, D = h or H, b or B, d or D
        kjelde_maal = "V&A API"
        if s:
            S, kjelde_sete = s, "V&A API"
    if museum == "NM" and S and H and abs(S - H) < 0.01:  # R4
        S, kjelde_sete = None, ""
    vaksen = r["Nemning"] not in UTE and not oid.startswith("NAMF")  # R5
    maal_ok = bool(H and B and D and 50 <= H <= 200 and 25 <= B <= 150 and 25 <= D <= 150)  # R6
    sete_ok = bool(S and H and S < H and 30 <= S <= 65)  # R7
    f = lambda x: "" if x is None else f"{x:.1f}"
    ut.append(dict(id=oid, museum=museum, type=r["Nemning"], aar_fraa=r["Frå år"], aar_til=r["Til år"],
                   stil=r["Stilperiode"], nasjonalitet=r["Nasjonalitet"], H=f(H), B=f(B), D=f(D), sete=f(S),
                   kjelde_maal=kjelde_maal, kjelde_sete=kjelde_sete, sete_merke=merke,
                   vaksenstol=int(vaksen), maal_ok=int(maal_ok), sete_ok=int(sete_ok)))

sti_ut = os.path.join(ROT, "analyse", "data", "stolar_reinsa.csv")
with open(sti_ut, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(ut[0].keys()))
    w.writeheader(); w.writerows(ut)

n = lambda f: sum(1 for x in ut if f(x))
print(f"rader: {len(ut)}   V&A-postar frå API: {len(va)}")
for m in ("NM", "VA"):
    print(f"  {m}: totalt {n(lambda x: x['museum'] == m)}"
          f" | vaksenstol {n(lambda x: x['museum'] == m and x['vaksenstol'])}"
          f" | + mål ok {n(lambda x: x['museum'] == m and x['vaksenstol'] and x['maal_ok'])}"
          f" | + sete ok {n(lambda x: x['museum'] == m and x['vaksenstol'] and x['maal_ok'] and x['sete_ok'])}"
          f" | setehøgd oppgjeven {n(lambda x: x['museum'] == m and x['sete'])}")
print("skrive:", sti_ut)
