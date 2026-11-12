"""Sonde: kva museum katalogfører setehøgd for stolar, og kor mange?

BLIND: skriptet tel berre KOR MANGE postar som har eit setehøgdmål og kva merkelappar måla har.
Det skriv aldri ut og lagrar aldri sjølve måla. Slik kan eit museum veljast til den forsegla
prøva utan at nokon har sett utfallet.

Køyr:  python analyse/07_sonde_testmuseum.py [met|aic|cma] [utvalsstorleik]
"""
import collections, json, random, re, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "research-script/1.0"}
STOL = re.compile(r"\b(arm)?chair\b|\bside chair\b|\bstool\b", re.I)
IKKJE = re.compile(r"cover|panel|fragment|design for|drawing|print|photograph|model|miniature|doll|seat cushion|back\b.*for", re.I)


def hent(url, timeout=30):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))


def met(n):
    ids = hent("https://collectionapi.metmuseum.org/public/collection/v1/search?q=chair")["objectIDs"] or []
    print(f"Met: {len(ids)} treff på «chair»; trekkjer {min(n, len(ids))} tilfeldig (frø 1)")
    random.Random(1).shuffle(ids)

    def ein(i):
        try:
            return hent(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{i}")
        except Exception:
            return None

    with ThreadPoolExecutor(6) as ex:
        objs = [o for o in ex.map(ein, ids[:n]) if o]
    stolar = [o for o in objs if STOL.search(o.get("objectName") or "") and not IKKJE.search(o.get("objectName") or "")]
    merke = collections.Counter(); med_sete = med_hogd = 0; avd = collections.Counter()
    for o in stolar:
        har_sete = har_h = False
        for m in o.get("measurements") or []:
            namn = (m.get("elementName") or "").strip()
            em = m.get("elementMeasurements") or {}
            merke[(namn, tuple(sorted(em.keys())))] += 1
            if "Height" in em:
                har_h = True
                if "seat" in namn.lower():
                    har_sete = True
        if not har_sete and re.search(r"seat\s*h", o.get("dimensions") or "", re.I):
            har_sete = True
            merke[("(fritekst: seat h.)", ())] += 1
        med_sete += har_sete; med_hogd += har_h
        if har_sete: avd[o.get("department")] += 1
    print(f"  henta {len(objs)}, av dei stolar etter namn: {len(stolar)}")
    print(f"  med høgd: {med_hogd}   med setehøgd: {med_sete}")
    if stolar:
        print(f"  overslag for heile treffmengda: om lag {round(len(ids) * med_sete / max(len(objs), 1))} stolar med setehøgd")
    print("  avdeling (med setehøgd):", avd.most_common(5))
    print("  merkelappar (topp 12):", [(k[0], list(k[1]), v) for k, v in merke.most_common(12)])


def aic(n):
    felt = "id,title,classification_title,dimensions,dimensions_detail"
    r = hent("https://api.artic.edu/api/v1/artworks/search?" + urllib.parse.urlencode({"q": "chair", "limit": 100, "fields": felt}))
    data = r.get("data", []); tot = r.get("pagination", {}).get("total")
    stolar = [o for o in data if STOL.search(o.get("title") or "") and not IKKJE.search(o.get("title") or "")]
    sete = sum(1 for o in stolar if re.search(r"seat", json.dumps(o.get("dimensions_detail")) + (o.get("dimensions") or ""), re.I))
    print(f"AIC: {tot} treff; første 100: stolar {len(stolar)}, nemner «seat» i måla: {sete}")
    print("  nøklar i dimensions_detail:", collections.Counter(k for o in stolar for d in (o.get("dimensions_detail") or []) for k in d).most_common(8))


def cma(n):
    r = hent("https://openaccess-api.clevelandart.org/api/artworks/?" + urllib.parse.urlencode({"q": "chair", "limit": 200, "fields": "id,title,type,dimensions,measurements"}))
    data = r.get("data", []); tot = r.get("info", {}).get("total")
    stolar = [o for o in data if STOL.search(o.get("title") or "") and not IKKJE.search(o.get("title") or "")]
    sete = sum(1 for o in stolar if re.search(r"seat", json.dumps(o.get("dimensions")) + (o.get("measurements") or ""), re.I))
    print(f"CMA: {tot} treff; første {len(data)}: stolar {len(stolar)}, nemner «seat» i måla: {sete}")
    print("  nøklar i dimensions:", collections.Counter(k for o in stolar for k in (o.get("dimensions") or {})).most_common(8))


kva = sys.argv[1] if len(sys.argv) > 1 else "alle"
n = int(sys.argv[2]) if len(sys.argv) > 2 else 600
for namn, f in (("met", met), ("aic", aic), ("cma", cma)):
    if kva in (namn, "alle"):
        try:
            f(n)
        except Exception as e:
            print(f"{namn.upper()}: feil {type(e).__name__}: {str(e)[:200]}")
