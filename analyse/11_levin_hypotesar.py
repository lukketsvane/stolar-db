"""Hypotesar utleidde frå formlære, prøvde slik Levin prøver eit system: som ein agent med målpunkt.

Alle tre musea er opna. Alt her er UTFORSKANDE og må stadfestast på nye, forsegla data.

H1  Same mål, andre middel [5.151]: setehøgda er lik på tvers av materiale (tre, metall, plast).
H2  Den regulerte storleiken er sitjaren, ikkje stolen [5.28]: lågare sete er djupare,
    og ein kombinasjon av setemåla er tettare enn noko enkeltmål.
H3  Omhug som gjenopprettande kraft [5.2, 6.672]: haldne aksar vender attende, frie aksar driv.
H4  Skilde målpunkt [1.4]: setehøgdene klumpar seg i fråskilde stillingar med tomrom mellom.
H5  Avkopling [6.752-6.755]: der kanalen frå sitjar til formgjevar er broten, løyser bindinga seg opp.
"""
import collections, csv, math, os, re, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = list(csv.DictReader(open(os.path.join(ROT, "analyse", "data", "tre_museum.csv"), encoding="utf-8-sig")))
ST = {r["Objekt-ID"]: r for r in csv.DictReader(open(os.path.join(ROT, "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline=""))}
f = lambda r, k: float(r[k]) if r.get(k) else np.nan
rcv = lambda x: float(1.4826 * np.median(np.abs(x - np.median(x))) / np.median(x))


def eps2(v, g, minn=8):
    d = collections.defaultdict(list)
    for a, k in zip(v, g):
        if k and not np.isnan(a): d[k].append(math.log(a))
    d = {k: x for k, x in d.items() if len(x) >= minn}
    if len(d) < 2: return float("nan"), {}
    al = np.concatenate([np.array(x) for x in d.values()]); N, k = len(al), len(d)
    ssb = sum(len(x) * (np.mean(x) - al.mean()) ** 2 for x in d.values()); sst = ((al - al.mean()) ** 2).sum()
    return float((ssb - (k - 1) * (sst - ssb) / (N - k)) / sst), {g: (len(x), float(np.exp(np.median(x)))) for g, x in d.items()}


def materiale(tekst):
    t = tekst.lower()
    if re.search(r"plast|polyamid|polyprop|glasfiber|akryl|polyuretan|pvc|nylon|fiberglass|plastic", t): return "plast"
    if re.search(r"stål|metall|jern|aluminium|krom|messingrør|steel|iron|chrom", t): return "metall"
    if re.search(r"eik|bøk|furu|bjørk|mahogni|nøttetre|tre\b|ask|alm|teak|palisander|lønn|kirsebær|rotting|finer", t): return "tre"
    return ""


print("== H1 SAME MÅL, ANDRE MIDDEL: materiale (Nasjonalmuseet + V&A)")
for lab, vel in (("alle år", lambda r: True), ("etter 1900", lambda r: r["aar"] and float(r["aar"]) >= 1900)):
    S = [r for r in T if r["museum"] in ("NM", "VA") and vel(r)]
    g = [materiale(ST[r["id"]]["Materialar"]) if r["id"] in ST else "" for r in S]
    for akse, v in (("setehøgd", [f(r, "sete") for r in S]), ("rygg", [f(r, "H") - f(r, "sete") for r in S]),
                    ("totalhøgd", [f(r, "H") for r in S]), ("breidd", [f(r, "B") for r in S])):
        e, grupper = eps2(v, g)
        print(f"  {lab:10s} {akse:10s} del forklart av materiale {e:5.2f} | " + "  ".join(f"{k}: {m:.1f} (n={n})" for k, (n, m) in sorted(grupper.items())))

print("\n== H2 DEN REGULERTE STORLEIKEN: setehøgd, setedjupn, setebreidd")
for m in ("RM", "VA"):
    S = [r for r in T if r["museum"] == m and r["sete"] and r["seteD"]]
    h, d = np.log([f(r, "sete") for r in S]), np.log([f(r, "seteD") for r in S])
    ok = (np.exp(d) > 25) & (np.exp(d) < 80); h, d = h[ok], d[ok]
    if len(h) < 30: print(f"  {m}: for få ({len(h)})"); continue
    r_ = float(np.corrcoef(h, d)[0, 1]); b = float(np.polyfit(d, h, 1)[0])
    w, v = np.linalg.eigh(np.cov(np.c_[h, d].T)); komb = np.c_[h, d] @ v[:, 0]
    print(f"  {m}: n={len(h)} korrelasjon høgd-djupn {r_:+.2f}, stiging {b:+.2f} | SD(log): høgd {h.std():.3f}, djupn {d.std():.3f}, tettaste kombinasjon {komb.std():.3f} "
          f"(vekter høgd {v[0, 0]:+.2f}, djupn {v[1, 0]:+.2f})")

print("\n== H3 GJENOPPRETTANDE KRAFT: 25-årsmedianar, alle tre museum samla")
S = [r for r in T if r["aar"] and 1550 <= float(r["aar"]) < 2025]
bolk = np.array([int(float(r["aar"]) // 25 * 25) for r in S])
for akse, v in (("setehøgd", np.array([f(r, "sete") for r in S])), ("rygg", np.array([f(r, "H") - f(r, "sete") for r in S])),
                ("breidd", np.array([f(r, "B") for r in S])), ("djupn", np.array([f(r, "D") for r in S])), ("totalhøgd", np.array([f(r, "H") for r in S]))):
    med, inn = [], []
    for b in sorted(set(bolk)):
        x = v[(bolk == b) & ~np.isnan(v)]
        if len(x) >= 8: med.append(np.median(np.log(x))); inn.append(np.std(np.log(x)))
    med = np.array(med); d1 = np.diff(med); d4 = med[4:] - med[:-4]
    ac = float(np.corrcoef(med[:-1], med[1:])[0, 1])
    print(f"  {akse:10s} bolkar {len(med):2d} | SD mellom bolkar {med.std():.3f} mot innan {np.mean(inn):.3f} (forhold {med.std() / np.mean(inn):.2f}) | "
          f"autokorr {ac:+.2f} | varians(4 steg)/varians(1 steg) {d4.var() / d1.var():.1f}  (1 = vender attende, 4 = driv)")

print("\n== H4 SKILDE MÅLPUNKT: oppgjeven setehøgd utan 30-65-regelen, 2,5 cm-klassar (alle tre museum)")
raa = np.array([f(r, "sete_raa") for r in T]); H = np.array([f(r, "H") for r in T])
raa = raa[~np.isnan(raa) & (raa < H) & (raa >= 10) & (raa <= 100)]
tel = collections.Counter((raa // 2.5 * 2.5).tolist())
print("  n =", len(raa)); print("  " + " ".join(f"{k:g}:{tel[k]}" for k in sorted(tel)))

print("\n== H5 AVKOPLING: spreiing i setehøgd etter tid (oppgjeven setehøgd 10-100 cm, lågare enn H)")
for m in ("NM", "VA", "RM"):
    ut = []
    for a, b in ((1500, 1800), (1800, 1900), (1900, 1970), (1970, 2030)):
        x = np.array([f(r, "sete_raa") for r in T if r["museum"] == m and r["aar"] and a <= float(r["aar"]) < b and r["sete_raa"] and 10 <= f(r, "sete_raa") <= 100 and f(r, "sete_raa") < f(r, "H")])
        if len(x) >= 8: ut.append(f"{a}-{b}: n={len(x)} median {np.median(x):.1f} robust {rcv(x):.3f} SD {x.std(ddof=1):.1f}")
    print(f"  {m}: " + " | ".join(ut))
S = [r for r in T if r["museum"] in ("NM", "VA") and r["sete_raa"] and r["id"] in ST and 10 <= f(r, "sete_raa") <= 100 and f(r, "sete_raa") < f(r, "H")]
g = collections.defaultdict(list)
for r in S: g[ST[r["id"]]["Stilperiode"]].append(f(r, "sete_raa"))
print("  per stil (n>=12), sortert etter SD: " + " | ".join(f"{k} {np.std(v, ddof=1):.1f} (n={len(v)})" for k, v in sorted(g.items(), key=lambda kv: np.std(kv[1])) if len(v) >= 12))
