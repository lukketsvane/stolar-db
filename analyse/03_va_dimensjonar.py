"""Hentar dei strukturerte måla for alle V&A-stolane i STOLAR rett frå V&A sitt opne API.

Kvifor: STOLAR.csv har 0.0 i høgd/breidd/djupn for 239-330 V&A-stolar, og setehøgd for berre 6.
API-et gjev mål som liste med type (Height/Width/Depth), del (t.d. seat) og eining.
Skriptet lagrar rådata uendra, éi linje per objekt, og kan startast på nytt utan å hente dobbelt.

Køyr:  python analyse/03_va_dimensjonar.py
Ut:    analyse/data/va_dimensjonar_raa.jsonl
"""
import csv, json, os, sys, time, urllib.request, urllib.error

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INN = os.path.join(ROT, "STOLAR", "STOLAR.csv")
UT = os.path.join(ROT, "analyse", "data", "va_dimensjonar_raa.jsonl")
os.makedirs(os.path.dirname(UT), exist_ok=True)

rader = list(csv.DictReader(open(INN, encoding="utf-8-sig", newline="")))
ids = [r["Objekt-ID"] for r in rader if "vam.ac.uk" in r["Nasjonalmuseet"]]

ferdig = set()
if os.path.exists(UT):
    for linje in open(UT, encoding="utf-8"):
        try:
            ferdig.add(json.loads(linje)["id"])
        except Exception:
            pass

att = [i for i in ids if i not in ferdig]
print(f"V&A-objekt: {len(ids)}  alt henta: {len(ferdig)}  att: {len(att)}", flush=True)

feil = 0
with open(UT, "a", encoding="utf-8") as ut:
    for n, oid in enumerate(att, 1):
        post = {"id": oid}
        for forsok in range(3):
            try:
                req = urllib.request.Request(
                    f"https://api.vam.ac.uk/v2/object/{oid}",
                    headers={"User-Agent": "research-script/1.0"},
                )
                rec = json.load(urllib.request.urlopen(req, timeout=30)).get("record", {})
                post["dimensions"] = rec.get("dimensions")
                post["dimensionsNote"] = rec.get("dimensionsNote")
                post["objectType"] = rec.get("objectType")
                post["status"] = "ok"
                break
            except urllib.error.HTTPError as e:
                post["status"] = f"http {e.code}"
                if e.code in (404, 410):
                    break
                time.sleep(5 * (forsok + 1))
            except Exception as e:
                post["status"] = f"feil {type(e).__name__}"
                time.sleep(5 * (forsok + 1))
        if post.get("status") != "ok":
            feil += 1
        ut.write(json.dumps(post, ensure_ascii=False) + "\n")
        ut.flush()
        if n % 200 == 0:
            print(f"  {n}/{len(att)}  feil så langt: {feil}", flush=True)
        time.sleep(0.15)

print(f"Ferdig. Feil: {feil}", flush=True)
