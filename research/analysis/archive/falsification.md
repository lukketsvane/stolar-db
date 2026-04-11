# Falsifiseringstestar — postulat 2.2, 4.1, 5.1

| Postulat | Test | Resultat | Status |
|---|---|---|---|
| 2.2 | min pairwise MI between selection-pressure proxies (low = independent pair exists) | 0.030 bits (matgr-Nasj) | HELD (independent pair found) |
| 2.2 | gain in R² (HW) when adding all other predictors to stil alone | 0.0452 | HELD (other predictors add explanatory power) |
| 4.1 | mean Wasserstein-distance(H) between consecutive 50-y periods | 14.36 cm | HELD (positive movement) |
| 4.1 | mean Wasserstein(Ho) consecutive periods | 14.36 cm | HELD |
| 4.1 | mean Wasserstein(Br) consecutive periods | 8.19 cm | HELD |
| 4.1 | mean Wasserstein(Dj) consecutive periods | 5.89 cm | HELD |
| 5.1 | KS(H) vs uniform | KS=0.868, p=0.00e+00 | HELD (rejected uniform) |
| 5.1 | KS(H) vs gaussian random walk | KS=0.207, p=4.79e-63 | HELD (rejected RW) |
| 5.1 | KS(W) vs uniform | KS=0.845, p=0.00e+00 | HELD (rejected uniform) |
| 5.1 | KS(W) vs gaussian random walk | KS=0.284, p=3.75e-119 | HELD (rejected RW) |
| 5.1 | KS(D) vs uniform | KS=0.869, p=0.00e+00 | HELD (rejected uniform) |
| 5.1 | KS(D) vs gaussian random walk | KS=0.248, p=8.60e-91 | HELD (rejected RW) |

## Detaljar

**2.2 — min pairwise MI between selection-pressure proxies (low = independent pair exists)**

matgr-Nasj=0.030; Hundre-Nasj=0.165; matgr-Hundre=0.178; matgr-Stil=0.217; Stil-Nasj=0.485; Stil-Hundre=1.323

**2.2 — gain in R² (HW) when adding all other predictors to stil alone**

r2(stil)=0.084, r2(all)=0.129, n=1324

**4.1 — mean Wasserstein-distance(H) between consecutive 50-y periods**

max=21.37, near-zero (<0.5cm)=0/10, periods=16

