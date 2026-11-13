"""15_mesh_test.py - prøv setehøgda frå 3D-modellane på TEST-halvparten, éin gong.

Føresetnad: 14_mesh_maal.py er køyrt på alle stolane med uendra metode (SEAT_METHOD v2),
og har skrive 14_validering.csv med både DEV og TEST.

Grunnmodellane er tilpassa på DEV og prøvde på dei same TEST-radene:
  fast verdi        = medianen av katalogført setehøgd i DEV
  fast del av H     = medianen av sete/H i DEV
Køyr:  python analyse/15_mesh_test.py   -> analyse/15_resultat.txt
"""
import csv, os, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
val = list(csv.DictReader(open(os.path.join(HER, "14_validering.csv"), encoding="utf-8")))
rein = {r["id"]: r for r in csv.DictReader(open(os.path.join(HER, "data", "stolar_reinsa.csv"), encoding="utf-8-sig"))}

ut = []


def skriv(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    ut.append(s)


def tal(rader, namn):
    sann = np.array([float(r["true_sete_cm"]) for r in rader])
    est = np.array([float(r["estimate_cm"]) for r in rader])
    H = np.array([float(rein[r["id"]]["H"]) for r in rader])
    f = est - sann
    r2 = lambda p: 1 - float(((p - sann) ** 2).sum() / ((sann - sann.mean()) ** 2).sum())
    skriv("  %-4s n=%3d | 3D-modell: snittfeil %.2f cm, medianfeil %.2f, skeivskap %+.2f, R2 %+.2f, innanfor 2 cm %.0f %%, r %.2f"
          % (namn, len(f), np.abs(f).mean(), np.median(np.abs(f)), f.mean(), r2(est), 100 * (np.abs(f) <= 2).mean(),
             np.corrcoef(est, sann)[0, 1]))
    skriv("       fast verdi (%.1f cm): snittfeil %.2f, R2 %+.2f | fast del av H (%.3f): snittfeil %.2f, R2 %+.2f"
          % (K, np.abs(K - sann).mean(), r2(np.full_like(sann, K)), F, np.abs(F * H - sann).mean(), r2(F * H)))
    return float(np.abs(f).mean()), float(np.abs(K - sann).mean())


dev = [r for r in val if r["split"] == "DEV"]
test = [r for r in val if r["split"] == "TEST"]
K = float(np.median([float(r["true_sete_cm"]) for r in dev]))
F = float(np.median([float(r["true_sete_cm"]) / float(rein[r["id"]]["H"]) for r in dev]))

for namn, sett in (("DEV", dev), ("TEST", test)):
    med = [r for r in sett if r["estimate_cm"] != ""]
    skriv("== %s: %d stolar, %d med estimat, %d utan (%.1f %%)" % (namn, len(sett), len(med), len(sett) - len(med),
                                                                 100 * (len(sett) - len(med)) / max(len(sett), 1)))
    if not med:
        continue
    m, k = tal(med, "alle")
    for mus in ("NM", "VA"):
        d = [r for r in med if rein[r["id"]]["museum"] == mus]
        if len(d) >= 10:
            tal(d, mus)
    utan = [r for r in med if r["flagg"] == ""]
    if len(utan) >= 10:
        tal(utan, "utan flagg")
    if namn == "TEST":
        skriv("  DOM: 3D-målinga %s den faste verdien på TEST (%.2f mot %.2f cm)." % ("slår" if m < k else "slår ikkje", m, k))

open(os.path.join(HER, "15_resultat.txt"), "w", encoding="utf-8").write("\n".join(ut) + "\n")
