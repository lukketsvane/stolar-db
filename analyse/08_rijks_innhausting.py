"""Blind innhausting av Rijksmuseum-stolar til den forsegla prøva.

Lagrar rådata uendra og skriv berre ut tal på postar, aldri mål.
Nektar å køyre før analyse/forsegla/FORESEIINGAR.json har "godkjend": true.

Køyr:  python analyse/08_rijks_innhausting.py
Ut:    analyse/forsegla/rijks_raa.jsonl
"""
import json, os, sys, time, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPE = os.path.join(ROT, "analyse", "forsegla")
if not json.load(open(os.path.join(MAPPE, "FORESEIINGAR.json"), encoding="utf-8")).get("godkjend"):
    sys.exit("Stoppa: føreseiingane er ikkje godkjende. Set godkjend til true, commit og push først.")

UA = {"User-Agent": "research-script/1.0"}


def hent(url, accept=None):
    h = dict(UA)
    if accept:
        h["Accept"] = accept
    for forsok in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40))
        except Exception:
            time.sleep(4 * (forsok + 1))
    return None


ids, url = [], "https://data.rijksmuseum.nl/search/collection?" + urllib.parse.urlencode({"type": "stoel"})
while url:
    side = hent(url)
    if not side:
        sys.exit("Stoppa: søket svara ikkje.")
    ids += [x["id"] for x in side.get("orderedItems", [])]
    url = (side.get("next") or {}).get("id")
print(f"postar i søket: {len(ids)}", flush=True)

UT = os.path.join(MAPPE, "rijks_raa.jsonl")
ferdig = set()
if os.path.exists(UT):
    ferdig = {json.loads(l)["id"] for l in open(UT, encoding="utf-8")}
feil = 0
with open(UT, "a", encoding="utf-8") as ut:
    for n, i in enumerate([x for x in ids if x not in ferdig], 1):
        rec = hent(i, "application/ld+json")
        feil += rec is None
        ut.write(json.dumps({"id": i, "record": rec}, ensure_ascii=False) + "\n")
        if n % 100 == 0:
            print(f"  {n} henta, feil {feil}", flush=True)
        time.sleep(0.1)
print(f"Ferdig. Nye postar: {len(ids) - len(ferdig)}, feil: {feil}")
