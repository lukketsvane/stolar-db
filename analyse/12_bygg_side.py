"""Byggjer figurar/stol-db.html (til traktat.iverfinne.no) og figurar/stolen.html frå figurar/kropp.html.
Køyr:  python analyse/12_bygg_side.py
"""
import collections, csv, json, os, re, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROT, "analyse")
T = list(csv.DictReader(open(os.path.join(A, "data", "tre_museum.csv"), encoding="utf-8-sig")))
ST = {r["Objekt-ID"]: r for r in csv.DictReader(open(os.path.join(ROT, "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline=""))}
M = {"NM": 0, "VA": 1, "RM": 2}
f = lambda r, k: float(r[k]) if r.get(k) else None

stolar = [[M[r["museum"]], (int(float(r["aar"])) if r["aar"] and float(r["aar"]) >= 1000 else None), f(r, "H"), f(r, "B"), f(r, "D"), f(r, "sete")] for r in T if r["sete"]]

# 25-årsmedianar, avvik i prosent frå aksen sin eigen langtidsmedian
bolkar = {}
aksar = {"sete": lambda r: f(r, "sete"), "rygg": lambda r: (f(r, "H") - f(r, "sete")) if r["sete"] else None,
         "breidd": lambda r: f(r, "B"), "djupn": lambda r: f(r, "D")}
for namn, fn in aksar.items():
    d = collections.defaultdict(list)
    for r in T:
        v = fn(r)
        if v and r["aar"] and 1550 <= float(r["aar"]) < 2025:
            d[int(float(r["aar"]) // 25 * 25)].append(v)
    med = {b: float(np.median(x)) for b, x in d.items() if len(x) >= 8}
    midt = float(np.median(list(med.values())))
    bolkar[namn] = [[b, round(100 * (med[b] / midt - 1), 1), len(d[b]), round(med[b], 1)] for b in sorted(med)]


def materiale(t):
    t = t.lower()
    if re.search(r"plast|polyamid|polyprop|glasfiber|akryl|polyuretan|pvc|nylon|fiberglass|plastic", t): return "plast"
    if re.search(r"stål|metall|jern|aluminium|krom|messingrør|steel|iron|chrom", t): return "metall"
    if re.search(r"eik|bøk|furu|bjørk|mahogni|nøttetre|tre\b|ask|alm|teak|palisander|lønn|kirsebær|rotting|finer", t): return "tre"
    return ""


g = collections.defaultdict(lambda: {"sete": [], "rygg": [], "breidd": []})
for r in T:
    if r["museum"] in ("NM", "VA") and r["sete"] and r["aar"] and float(r["aar"]) >= 1900 and r["id"] in ST:
        m = materiale(ST[r["id"]]["Materialar"])
        if m:
            g[m]["sete"].append(f(r, "sete")); g[m]["rygg"].append(f(r, "H") - f(r, "sete")); g[m]["breidd"].append(f(r, "B"))
kv = lambda x: [round(float(np.quantile(x, q)), 1) for q in (0.25, 0.5, 0.75)] + [len(x)]
mat = [{"namn": k, "sete": kv(g[k]["sete"]), "rygg": kv(g[k]["rygg"]), "breidd": round(float(np.median(g[k]["breidd"])), 1)} for k in ("tre", "metall", "plast") if k in g]

skala = []
for namn, kode in M.items():
    S = np.array([s[5] for s in stolar if s[0] == kode]); H = np.array([s[2] for s in stolar if s[0] == kode])
    i, j = np.triu_indices(len(S), 1); dx = np.log(H)[j] - np.log(H)[i]; ok = dx != 0
    b = float(np.median((np.log(S)[j] - np.log(S)[i])[ok] / dx[ok]))
    skala.append({"m": kode, "b": round(b, 3), "a": round(float(np.median(np.log(S) - b * np.log(H))), 4),
                  "del": round(float(np.median(S / H)), 4), "n": int(len(S))})

drift = [{"m": M[r["museum"]], "a": r["akse"], "v": float(r["driftindeks"]), "lo": float(r["lo"]), "hi": float(r["hi"]), "n": int(r["n"])}
         for r in csv.DictReader(open(os.path.join(A, "data", "driftindeks.csv"), encoding="utf-8-sig"))]
data = {"stolar": stolar, "bolkar": bolkar, "materiale": mat, "skala": skala, "drift": drift}
kropp = open(os.path.join(A, "figurar", "kropp.html"), encoding="utf-8").read().replace('"__DATA__"', json.dumps(data, ensure_ascii=False, separators=(",", ":")))
FONT = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,300..400;1,7..72,300..400&family=IBM+Plex+Mono:wght@400;500&display=swap">'
HOVUD = """<!doctype html>
<html lang="nn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme:light)">
<meta name="theme-color" content="#080808" media="(prefers-color-scheme:dark)">
<meta name="formlaere-source" content="@@SOURCE_HASH@@">
<title>formlære · stol-db</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
""" + FONT + """
</head>
<body>
"""
# 1) Sida til traktat.iverfinne.no (mal for traktat/scripts/build.py i FORML-RE)
open(os.path.join(A, "figurar", "stol-db.html"), "w", encoding="utf-8").write(HOVUD + kropp + "</body>" + chr(10) + "</html>" + chr(10))
# 2) Same innhald utan meny, til førehandsvising
utan_meny = re.sub(r"<!--NAV-->.*?<!--/NAV-->", "", kropp, flags=re.S)
open(os.path.join(A, "figurar", "stolen.html"), "w", encoding="utf-8").write("<title>Kva stolen held fast</title>" + chr(10) + FONT + chr(10) + utan_meny)
print("stolar:", len(stolar), "| skrive: stol-db.html og stolen.html")
