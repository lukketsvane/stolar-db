"""H3 prøvd på ein annan måte: parvis semivariogram utan tidsbolkar.

For alle par av stolar i same museum: halve kvadratet av skilnaden i log-mål, mot kor mange år som skil dei.
Ein akse som blir halden på plass gjev same skilnad anten stolane er laga same tiår eller 150 år frå kvarandre.
Ein akse som driv, gjev større skilnad jo lengre tid som skil.
Driftindeks = semivarians ved 100-175 års avstand delt på semivarians ved 0-25 års avstand (1 = ingen drift).
Same stolar for alle aksar (dei med setehøgd), 95 % bootstrap over stolar. UTFORSKANDE.
"""
import csv, os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
rng = np.random.default_rng(20261112)
ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = [r for r in csv.DictReader(open(os.path.join(ROT, "analyse", "data", "tre_museum.csv"), encoding="utf-8-sig")) if r["sete"] and r["aar"] and float(r["aar"]) >= 1500]
AKS = {"setehøgd": lambda r: float(r["sete"]), "rygg": lambda r: float(r["H"]) - float(r["sete"]), "breidd": lambda r: float(r["B"]),
       "djupn": lambda r: float(r["D"]), "totalhøgd": lambda r: float(r["H"])}
KL = [(0, 25), (25, 60), (60, 100), (100, 175), (175, 300)]

def gamma(y, x):
    i, j = np.triu_indices(len(y), 1)
    dt = np.abs(y[i] - y[j]); d2 = 0.5 * (x[i] - x[j]) ** 2
    return np.array([d2[(dt >= a) & (dt < b)].mean() if ((dt >= a) & (dt < b)).sum() > 30 else np.nan for a, b in KL])

ut = []
for m in ("NM", "VA", "RM"):
    S = [r for r in T if r["museum"] == m]
    y = np.array([float(r["aar"]) for r in S])
    print(f"== {m}: n = {len(S)}, år {int(y.min())}-{int(y.max())}")
    for namn, fn in AKS.items():
        x = np.log(np.array([fn(r) for r in S]))
        g = gamma(y, x); idx = g[3] / g[0]
        bs = []
        for _ in range(300):
            k = rng.integers(0, len(y), len(y)); gb = gamma(y[k], x[k]); bs.append(gb[3] / gb[0])
        lo, hi = np.nanquantile(bs, [0.025, 0.975])
        print(f"   {namn:10s} semivarians x1000 per avstandsklasse: " + " ".join(f"{v*1000:6.1f}" for v in g) + f" | driftindeks {idx:5.2f} [{lo:4.2f}, {hi:4.2f}]")
        ut.append(dict(museum=m, akse=namn, driftindeks=round(float(idx), 3), lo=round(float(lo), 3), hi=round(float(hi), 3), n=len(S)))
with open(os.path.join(ROT, "analyse", "data", "driftindeks.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(ut[0].keys())); w.writeheader(); w.writerows(ut)
