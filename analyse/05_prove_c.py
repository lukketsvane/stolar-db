"""Prøve C: slår «held fast»-modellen ein felles storleiksfaktor?

Éin parameter avgjer det: den allometriske stiginga b i  log(mål) = a + b * log(storleik).
  b = 1  -> målet skalerer med stolen (grunnmodellen, éin storleiksfaktor)
  b = 0  -> målet er halde fast uavhengig av kor stor stolen er
Storleik blir målt på to måtar: totalhøgd H, og setegrunnflate sqrt(B*D).

I tillegg: kryssvalidert feil (5 fald) for fire måtar å føreseie setehøgd på.

Køyr:  python analyse/05_prove_c.py [sti til reinsa tabell]
Utan argument blir STOLAR.csv lesen med same reinsing som 01_prove_a_utforskande.py.
Reinsa tabell må ha kolonnane: H, B, D, sete, stil, museum.
"""
import csv, math, os, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
rng = np.random.default_rng(20261112)
ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def les_standard():
    rader = list(csv.DictReader(open(os.path.join(ROT, "STOLAR", "STOLAR.csv"), encoding="utf-8-sig", newline="")))
    ut = []
    for r in rader:
        try:
            h, b, d, s = (float(r[k]) for k in ("Høgde (cm)", "Breidde (cm)", "Djupn (cm)", "Setehøgde (cm)"))
        except ValueError:
            continue
        if r["Nemning"] in ("Krakk", "Barnestol", "Benkestol", "Stol utan rygg"):
            continue
        if not (50 <= h <= 200 and 25 <= b <= 150 and 25 <= d <= 150):
            continue
        if abs(s - h) < 0.01 or s >= h or not (30 <= s <= 65):
            continue
        ut.append(dict(H=h, B=b, D=d, sete=s, stil=r["Stilperiode"],
                       museum="VA" if "vam.ac.uk" in r["Nasjonalmuseet"] else "NM"))
    return ut


def les_tabell(sti):
    ut = []
    for r in csv.DictReader(open(sti, encoding="utf-8-sig", newline="")):
        if any(r.get(k, "1") != "1" for k in ("vaksenstol", "maal_ok", "sete_ok")):
            continue
        try:
            ut.append(dict(H=float(r["H"]), B=float(r["B"]), D=float(r["D"]), sete=float(r["sete"]),
                           stil=r.get("stil", ""), museum=r.get("museum", "")))
        except (ValueError, KeyError):
            pass
    return ut


def theil_sen(x, y):
    i, j = np.triu_indices(len(x), 1)
    dx = x[j] - x[i]
    ok = dx != 0
    return float(np.median((y[j] - y[i])[ok] / dx[ok]))


def stiging(x, y, n_boot=1000):
    b = theil_sen(x, y)
    bs = []
    for _ in range(n_boot):
        k = rng.integers(0, len(x), len(x))
        bs.append(theil_sen(x[k], y[k]))
    ols = float(np.polyfit(x, y, 1)[0])
    return b, float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975)), ols


data = les_tabell(sys.argv[1]) if len(sys.argv) > 1 else les_standard()
if len(sys.argv) > 2:  # valfritt: berre eitt museum, t.d. NM eller VA
    data = [r for r in data if r["museum"] == sys.argv[2]]
    print("delutval:", sys.argv[2])
H = np.array([r["H"] for r in data]); B = np.array([r["B"] for r in data])
D = np.array([r["D"] for r in data]); S = np.array([r["sete"] for r in data])
stil = np.array([r["stil"] for r in data])
G = np.sqrt(B * D)
print(f"n = {len(data)}   museum: { {m: int(sum(1 for r in data if r['museum'] == m)) for m in ('NM', 'VA')} }")

print("\nAllometrisk stiging b (Theil-Sen, 95 % bootstrap) | OLS")
for namn, y, x, xn in (("setehøgd", S, H, "totalhøgd"), ("setehøgd", S, G, "sqrt(B*D)"),
                        ("djupn", D, H, "totalhøgd"), ("breidd", B, H, "totalhøgd"),
                        ("rygg (H-sete)", H - S, G, "sqrt(B*D)"), ("totalhøgd", H, G, "sqrt(B*D)")):
    b, lo, hi, ols = stiging(np.log(x), np.log(y))
    print(f"  {namn:14s} mot {xn:10s}: b = {b:+.2f} [{lo:+.2f}, {hi:+.2f}] | {ols:+.2f}")

print("\nKryssvalidert feil for setehøgd (5 fald, snitt absolutt feil i cm)")
idx = rng.permutation(len(S)); fald = np.array_split(idx, 5)
feil = {k: [] for k in ("konstant", "fast del av H", "potenslov i H", "konstant per stil")}
for f in fald:
    tr = np.setdiff1d(idx, f)
    feil["konstant"] += list(np.abs(S[f] - np.median(S[tr])))
    feil["fast del av H"] += list(np.abs(S[f] - np.median(S[tr] / H[tr]) * H[f]))
    a = np.polyfit(np.log(H[tr]), np.log(S[tr]), 1)
    feil["potenslov i H"] += list(np.abs(S[f] - np.exp(a[1] + a[0] * np.log(H[f]))))
    med = {s: np.median(S[tr][stil[tr] == s]) for s in set(stil[tr])}
    feil["konstant per stil"] += list(np.abs(S[f] - np.array([med.get(s, np.median(S[tr])) for s in stil[f]])))
for k, v in feil.items():
    print(f"  {k:18s} {np.mean(v):.2f}")
