"""Slår saman Nasjonalmuseet, V&A og Rijksmuseum i éin tabell med same reglar.

Rijksmuseum-dataa er opna i den forsegla prøva (09). Alt som blir rekna på dei herifrå er UTFORSKANDE.

Ut: analyse/data/tre_museum.csv   (vaksenstolar med gyldig H, B, D; setemål der dei finst)
Kolonnar: museum,id,aar,H,B,D,sete,seteB,seteD,sete_raa (sete_raa = oppgjeven setehøgd utan 30-65-regelen)
"""
import csv, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROT, "analyse")
TIL_CM = {"cm": 1.0, "mm": 0.1, "in": 2.54, "ft": 30.48, "m": 100.0}
ok_maal = lambda H, B, D: bool(H and B and D and 50 <= H <= 200 and 25 <= B <= 150 and 25 <= D <= 150)
ok_sete = lambda S, H: bool(S and H and S < H and 30 <= S <= 65)
ut = []

# Nasjonalmuseet og V&A: frå den reinsa tabellen
va_sete = {}
for l in open(os.path.join(A, "data", "va_dimensjonar_raa.jsonl"), encoding="utf-8"):
    p = json.loads(l); sb = sd = None
    for d in p.get("dimensions") or []:
        f = TIL_CM.get((d.get("unit") or "").strip().lower())
        try:
            v = float(d.get("value")) * f
        except (TypeError, ValueError):
            continue
        tekst = " ".join([(d.get("part") or ""), (d.get("qualifier") or ""), (d.get("note") or "")]).lower()
        if "seat" in tekst and v > 0:
            if d.get("dimension") == "Width" and sb is None: sb = v
            if d.get("dimension") == "Depth" and sd is None: sd = v
    va_sete[p["id"]] = (sb, sd)
for r in csv.DictReader(open(os.path.join(A, "data", "stolar_reinsa.csv"), encoding="utf-8-sig")):
    if r["vaksenstol"] != "1" or r["maal_ok"] != "1":
        continue
    sb, sd = va_sete.get(r["id"], (None, None)) if r["museum"] == "VA" else (None, None)
    ut.append(dict(museum=r["museum"], id=r["id"], aar=r["aar_fraa"][:4] if r["aar_fraa"] else "",
                   H=r["H"], B=r["B"], D=r["D"], sete=r["sete"] if r["sete_ok"] == "1" else "",
                   seteB=f"{sb:.1f}" if sb else "", seteD=f"{sd:.1f}" if sd else "", sete_raa=r["sete"]))

# Rijksmuseum: same lesing som i 09
ute = re.compile(r"kinder|poppen|miniatuur|model|kruk|tabouret|\bbank\b", re.I)
forste = lambda x: (x[0] if x else {}) if isinstance(x, list) else (x or {})
for l in open(os.path.join(A, "forsegla", "rijks_raa.jsonl"), encoding="utf-8"):
    p = json.loads(l); rec = p.get("record")
    if not rec or ute.search(" ".join((n.get("content") or "") for n in rec.get("identified_by", []) if n.get("type") == "Name")):
        continue
    heil = {"height": None, "width": None, "depth": None}; sete = {"height": None, "width": None, "depth": None}
    for x in rec.get("dimension") or []:
        typ = next((n["@value"] for c in x.get("classified_as", []) for n in c.get("notation", []) if n.get("@language") == "en"), None)
        if typ not in heil or (x.get("unit") or {}).get("id", "").rsplit("/", 1)[-1] != "300379098":
            continue
        try:
            v = float(str(x.get("value")).replace(",", "."))
        except ValueError:
            continue
        del_ = " ".join((n.get("content") or "").lower() for n in x.get("identified_by", []))
        mål = sete if "zitting" in del_ else heil if del_ in ("", "geheel") else None
        if mål is not None and mål[typ] is None and v > 0:
            mål[typ] = v
    H, B, D = heil["height"], heil["width"], heil["depth"]
    if not ok_maal(H, B, D):
        continue
    t = forste(forste(rec.get("produced_by")).get("timespan")).get("begin_of_the_begin") or ""
    m = re.match(r"\d{4}", t)
    S = sete["height"]
    ut.append(dict(museum="RM", id=p["id"].rsplit("/", 1)[-1], aar=m.group(0) if m else "", H=f"{H:.1f}", B=f"{B:.1f}", D=f"{D:.1f}",
                   sete=f"{S:.1f}" if ok_sete(S, H) else "",
                   seteB=f"{sete['width']:.1f}" if sete["width"] else "", seteD=f"{sete['depth']:.1f}" if sete["depth"] else "",
                   sete_raa=f"{S:.1f}" if S else ""))

with open(os.path.join(A, "data", "tre_museum.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(ut[0].keys())); w.writeheader(); w.writerows(ut)
for m in ("NM", "VA", "RM"):
    s = [r for r in ut if r["museum"] == m]
    print(f"{m}: {len(s)} stolar | setehøgd {sum(1 for r in s if r['sete'])} | setebreidd {sum(1 for r in s if r['seteB'])} | setedjupn {sum(1 for r in s if r['seteD'])} | med år {sum(1 for r in s if r['aar'])}")
