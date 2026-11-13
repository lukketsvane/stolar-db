"""21_sonde_met.py - blind sonde mot The Met før den tredje forsegla prøva.

BLIND: skriptet tel berre kva Met katalogfører for stolar og krakkar: objektnamn, avdelingar, kulturar,
hundreår og kva merkelappar måla har (til dømes «Seat», «Arm»). Det skriv aldri ut og lagrar aldri
eit einaste mål. Slik kan føreseiingane skrivast og forseglast før nokon har sett utfallet.

  python analyse/21_sonde_met.py [utvalsstorleik]

Ut: analyse/forsegla3/SONDE.json (berre teljingar).
"""
import collections, json, os, random, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
UT = os.path.join(HER, "forsegla3")
os.makedirs(UT, exist_ok=True)
UA = {"User-Agent": "research-script/1.0"}
API = "https://collectionapi.metmuseum.org/public/collection/v1/"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 500


def hent(url, forsok=4):
    for i in range(forsok):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40))
        except Exception:
            time.sleep(1.5 * (i + 1))
    return None


def ids(q, steg=500):
    """Søket v1 vart lagt ned 1.10.2026; v1.1 er sidedelt med offset og limit."""
    ut, off = set(), 0
    while True:
        d = hent(API.replace("/v1/", "/v1.1/") + "search?q=%s&limit=%d&offset=%d" % (q, steg, off)) or {}
        nye = d.get("objectIDs") or []
        ut.update(nye)
        off += steg
        if not nye or off >= (d.get("total") or 0):
            return ut


alle = {"chair": ids("chair"), "stool": ids("stool"), "armchair": ids("armchair"), "side%20chair": ids("side%20chair")}
union = sorted(set().union(*alle.values()))
print("søketreff:", {k: len(v) for k, v in alle.items()}, "| samla:", len(union))
random.Random(1).shuffle(union)
with ThreadPoolExecutor(6) as ex:
    objs = [o for o in ex.map(lambda i: hent(API + "objects/%d" % i), union[:N]) if o]

namn = collections.Counter(); avd = collections.Counter(); kultur = collections.Counter(); klasse = collections.Counter()
hundreaar = collections.Counter(); merke = collections.Counter(); fritekst = collections.Counter(); harbilete = 0
typar = collections.Counter()
TYPAR = [("krakk", re.compile(r"\bstool\b", re.I)), ("fotskammel", re.compile(r"foot\s*stool|footrest", re.I)),
         ("armstol", re.compile(r"\barm\s*chair|\barmchair|fauteuil|bergère", re.I)),
         ("stol", re.compile(r"\bchair\b|\bside chair\b|chaise", re.I))]
for o in objs:
    on = (o.get("objectName") or "").strip()
    namn[on.lower()] += 1; avd[o.get("department") or ""] += 1; kultur[(o.get("culture") or "")[:30]] += 1
    klasse[o.get("classification") or ""] += 1
    b = o.get("objectBeginDate")
    hundreaar[(int(b) // 100 * 100) if isinstance(b, int) else None] += 1
    harbilete += bool(o.get("primaryImage"))
    t = next((k for k, rx in TYPAR if rx.search(on)), "anna")
    typar[t] += 1
    for m in o.get("measurements") or []:
        merke[(t, (m.get("elementName") or "").strip().lower()[:30], tuple(sorted((m.get("elementMeasurements") or {}).keys())))] += 1
    d = (o.get("dimensions") or "").lower()
    for nokkel, rx in (("seat h", r"seat\s*h"), ("arm h", r"arm\w*\s*h|h\.?\s*(to|of)\s*arm"), ("to seat", r"to\s*seat"),
                       ("in.", r"\bin\.\b"), ("cm", r"\bcm\b")):
        if re.search(rx, d):
            fritekst[(t, nokkel)] += 1

ut = {"tid": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "utval": len(objs), "av": len(union),
      "søketreff": {k: len(v) for k, v in alle.items()}, "med_bilete": harbilete,
      "typar": typar.most_common(), "objektnamn_topp40": namn.most_common(40), "avdelingar": avd.most_common(20),
      "klassifikasjon_topp15": klasse.most_common(15), "kultur_topp25": kultur.most_common(25),
      "hundreaar": sorted(((k if k is not None else -99999), v) for k, v in hundreaar.items()),
      "maalemerkelappar_topp60": [[list(k), v] for k, v in merke.most_common(60)],
      "fritekst_merkelappar": [[list(k), v] for k, v in fritekst.most_common()],
      "merknad": "Berre teljingar. Ingen mål er lesne ut, skrivne ut eller lagra."}
json.dump(ut, open(os.path.join(UT, "SONDE.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: ut[k] for k in ("utval", "av", "med_bilete", "typar")}, ensure_ascii=False))
print("avdelingar:", ut["avdelingar"][:12])
print("namn:", ut["objektnamn_topp40"][:30])
print("merkelappar:", ut["maalemerkelappar_topp60"][:40])
print("fritekst:", ut["fritekst_merkelappar"])
print("hundreår:", ut["hundreaar"])
print("kultur:", ut["kultur_topp25"][:15])
