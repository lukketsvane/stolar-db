"""25_sonde_profilfoto.py - blind sonde: kor mange Met-stolar har eit katalogfoto i profil?

Før kanten ved 1712 kan prøvast på 2D-sidesilhuettar, må det vere nok stolar med foto i profil.
Sonden trekkjer eit tilfeldig utval av trestolar 1600 til 1899 (dei vestlege møbelavdelingane, datert
innan 15 år, fri for rettar), hentar bileta via Met-API-et sakte (under eitt kall i sekundet), segmenterer
på CPU og tel kor mange som har minst eitt foto i profil. Ingen silhuett blir lagra, ingen avstand rekna.

  python analyse/25_sonde_profilfoto.py [n]      Ut: analyse/forsegla3/SONDE_PROFIL.json (berre teljingar)
"""
import csv, json, os, random, re, sys, time, urllib.request
import numpy as np
import cv2

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(10 ** 8)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
UA = {"User-Agent": "research-script/1.0"}
API = "https://collectionapi.metmuseum.org/public/collection/v1/objects/%s"
AVD = {"The American Wing", "European Sculpture and Decorative Arts"}
STOL = re.compile(r"\bchairs?\b|armchair|fauteuil|berg[eè]re|\bchaise\b", re.I)
IKKJE = re.compile(r"stool|settee|sofa|bench|table|model|miniature|doll|toy|back\b|seat\b|frame|cover|panel|fragment|cushion|leg", re.I)
TRE = re.compile(r"\b(wood|walnut|oak|mahogany|maple|beech|cherry|pine|ash|birch|elm|rosewood|tulip|poplar|hickory|chestnut|fruitwood|satinwood|gilt|giltwood|lime|linden|cedar|cypress|ebon|pear|boxwood|hornbeam)", re.I)
METALL = re.compile(r"steel|iron|alumin|plastic|fiberglass|papier|cast", re.I)
HWD = re.compile(r"\(\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*cm", re.I)


def hent(url, binar=False):
    for i in range(3):
        try:
            time.sleep(0.9)                                           # under eitt kall i sekundet
            d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
            return d if binar else json.loads(d)
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def hwd(dims):
    """(H, B, D) i cm frå første «(a x b x c cm)» i dimensjonsteksten (Met: høgd x breidd x djupn)."""
    m = HWD.search(dims or "")
    return tuple(float(x) for x in m.groups()) if m else None


def silhuett(bilete):
    """Binær maske frå eit katalogfoto på studiobakgrunn: avstand i Lab frå kantfargen, Otsu, opning, lukking."""
    s = 600 / max(bilete.shape[:2])
    b = cv2.resize(bilete, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else bilete
    lab = cv2.cvtColor(b, cv2.COLOR_BGR2LAB).astype(np.float32)
    k = max(3, int(0.04 * min(lab.shape[:2])))
    kant = np.concatenate([lab[:k].reshape(-1, 3), lab[-k:].reshape(-1, 3), lab[:, :k].reshape(-1, 3), lab[:, -k:].reshape(-1, 3)])
    d = np.linalg.norm(lab - np.median(kant, 0), axis=2)
    d8 = np.clip(d * 2, 0, 255).astype(np.uint8)
    t, _ = cv2.threshold(d8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m = (d8 > max(t, 24)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab_, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        return None
    stor = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, h = st[stor, :4]
    behald = np.zeros(n, bool); behald[stor] = True
    for i in range(1, n):
        a = st[i, cv2.CC_STAT_AREA]; xi, yi, wi, hi = st[i, :4]
        if a >= 0.01 * st[stor, cv2.CC_STAT_AREA] and xi < x + 1.1 * w and xi + wi > x - 0.1 * w and yi < y + 1.1 * h and yi + hi > y - 0.1 * h:
            behald[i] = True
    return behald[lab_].astype(np.uint8)


def profiltrekk(m, H, B, D):
    """-> (er_profil, trekk). Profil: breidd/høgd i biletet nær D/H, og ryggen (øvste 30 %) ligg på éi side."""
    ys, xs = np.nonzero(m)
    if len(xs) < 500:
        return False, None
    rand = np.concatenate([m[0], m[-1], m[:, 0], m[:, -1]]).mean()
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    w, h = x1 - x0 + 1, y1 - y0 + 1
    aspekt = w / h
    topp = ys < y0 + 0.30 * h
    skeiv = abs(xs[topp].mean() - (x0 + x1) / 2) / w if topp.any() else 0.0
    dh, bh = D / H, B / H
    naer_d = abs(aspekt - dh) / dh <= 0.20
    tvetydig = abs(bh - dh) / dh < 0.15
    er = bool(rand < 0.30 and naer_d and skeiv >= 0.15 and (not tvetydig or skeiv >= 0.20))
    return er, {"aspekt": round(float(aspekt), 3), "d_over_h": round(dh, 3), "skeiv": round(float(skeiv), 3), "rand": round(float(rand), 3)}


rader = []
with open(os.path.join(HER, "forsegla3", "MetObjects.csv"), encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        on = r.get("Object Name") or ""
        if r.get("Department") not in AVD or not STOL.search(on) or IKKJE.search(on) or r.get("Is Public Domain") != "True":
            continue
        med = r.get("Medium") or ""
        if not TRE.search(med) or METALL.search(med):
            continue
        try:
            a, b = int(r["Object Begin Date"]), int(r["Object End Date"])
        except ValueError:
            continue
        mal = hwd(r.get("Dimensions"))
        if 1600 <= a < 1900 and 0 <= b - a <= 15 and mal:
            rader.append((r["Object ID"], a, mal))
random.Random(20261113).shuffle(rader)
utval = rader[:N]
print("kandidatar:", len(rader), "| utval:", len(utval), flush=True)
tel = {"objekt": 0, "med_bilete": 0, "bilete": 0, "bilete_lese": 0, "med_profil": 0, "profil_foer_1712": 0, "profil_fraa_1712": 0,
       "foer_1712": 0, "fraa_1712": 0}
bilete_per_objekt = []
for oid, aar, (H, B, D) in utval:
    tel["objekt"] += 1
    tel["foer_1712" if aar < 1712 else "fraa_1712"] += 1
    o = hent(API % oid) or {}
    urlar = ([o["primaryImageSmall"]] if o.get("primaryImageSmall") else []) + \
            [u.replace("/original/", "/web-large/") for u in (o.get("additionalImages") or [])][:6]
    bilete_per_objekt.append(len(urlar))
    tel["med_bilete"] += bool(urlar)
    funne = False
    for u in urlar:
        tel["bilete"] += 1
        raw = hent(u, binar=True)
        img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR) if raw else None
        if img is None:
            continue
        tel["bilete_lese"] += 1
        m = silhuett(img)
        if m is None:
            continue
        er, _ = profiltrekk(m, H, B, D)
        if er:
            funne = True
            break
    if funne:
        tel["med_profil"] += 1
        tel["profil_foer_1712" if aar < 1712 else "profil_fraa_1712"] += 1
    if tel["objekt"] % 10 == 0:
        print(tel, flush=True)
tel["del_med_profil"] = round(tel["med_profil"] / max(tel["objekt"], 1), 3)
tel["bilete_per_objekt_median"] = float(np.median(bilete_per_objekt)) if bilete_per_objekt else 0
ut = {"tid": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "kandidatar": len(rader), "teljingar": tel,
      "merknad": "Berre teljingar. Ingen silhuett lagra, ingen avstand rekna."}
json.dump(ut, open(os.path.join(HER, "forsegla3", "SONDE_PROFIL.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print(json.dumps(ut, ensure_ascii=False))
