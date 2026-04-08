# FORMLÆRE — hypoteseresultat (fase 2)

Testar utleidde frå dei korrigerte proposisjonane mot STOLAR.csv (n ≈ 2 000 stolar).
Mesh-baserte testar vert lagde til i ein eigen seksjon når `analysis/mesh_features.csv` er klar.

## Samandrag

| Prop | Test | Statistikk | Verdikt |
|---|---|---|---|
| 1.4 | NN distance CV in catalog space (Poisson null = 0.36) | 5.360 | STADFESTA |
| 2.4 | proxy dominance (stil > mat on 3/4 dims) | 4/4 | STADFESTA |
| 3.2 | KDE local maxima count | 2 | STADFESTA |
| 4.3 | max jump / median jump (smoothed period medians) | 6.08 | STADFESTA |
| 4.4 | cumulative hull growth ratio (clipped 1-99%) | 107.2 | STADFESTA* |
| 5.1 | KS-test vs uniform | KS for H,W,D | STADFESTA |
| 4.5a | norsk mahogni-konsentrasjon 1825-1849 (deterministisk) | 16/16 = 100% | STADFESTA |
| 4.5b | H/W-CV-kollaps 1825-1849 (samanlikna med naboperiodar) | 0.59 | MODERAT |
| 2.4 mesh | proxy dominance on mesh features | 4/4 | STADFESTA |
| 3.4 mesh | silhouette in 4-D mesh feature space (negative = stadfest 3.4) | -0.338 | STADFESTA |
| 1.4 mesh | NN distance CV in mesh feature space (Poisson null = 0.36) | 0.956 | STADFESTA |
| 4.4 mesh | cumulative mesh-hull growth ratio | 553 | STADFESTA |
| 3.3 mesh | CV span (max/min across mesh features) | 128.4× | STADFESTA |

## Detaljar

### Prop 1.4: NN distance CV in catalog space (Poisson null = 0.36)

- **Verdikt:** STADFESTA
- **Statistikk:** 5.360
- **Detaljar:** CI95=[3.706, 5.942], n=1664

### Prop 2.4: proxy dominance (stil > mat on 3/4 dims)

- **Verdikt:** STADFESTA
- **Statistikk:** 4/4
- **Detaljar:** H: stil=0.590 mat=0.087; W: stil=0.344 mat=0.057; D: stil=0.304 mat=0.063; HW: stil=0.549 mat=0.101

### Prop 3.2: KDE local maxima count

- **Verdikt:** STADFESTA
- **Statistikk:** 2
- **Detaljar:** n=1611, density threshold = 5% of peak

### Prop 4.3: max jump / median jump (smoothed period medians)

- **Verdikt:** STADFESTA
- **Statistikk:** 6.08
- **Detaljar:** CI95=[2.33, 6.87], n=1663

### Prop 4.4: cumulative hull growth ratio (clipped 1-99%)

- **Verdikt:** STADFESTA*
- **Statistikk:** 107.2
- **Detaljar:** monotone=True, periods=24, CI95=[30×, 117165×]

### Prop 5.1: KS-test vs uniform

- **Verdikt:** STADFESTA
- **Statistikk:** KS for H,W,D
- **p:** see notes
- **Detaljar:** Ho: KS=0.868, p=0.00e+00; Br: KS=0.845, p=0.00e+00; Dj: KS=0.869, p=0.00e+00

### Prop 4.5a: norsk mahogni-konsentrasjon 1825-1849 (deterministisk)

- **Verdikt:** STADFESTA
- **Statistikk:** 16/16 = 100%
- **Detaljar:** 1825-49 n=16 mahogni=1.00 CV(HW)=0.083; 1750-99 n=16 mahogni=0.00 CV(HW)=0.140; 1850-99 n=9 CV(HW)=0.090

### Prop 4.5b: H/W-CV-kollaps 1825-1849 (samanlikna med naboperiodar)

- **Verdikt:** MODERAT
- **Statistikk:** 0.59
- **Detaljar:** CI95=[0.27, 1.12], n=16 vs 16/9

### Prop 2.4 mesh: proxy dominance on mesh features

- **Verdikt:** STADFESTA
- **Statistikk:** 4/4
- **Detaljar:** sphericity: stil=0.232 mat=0.055; fill_ratio: stil=0.125 mat=0.000; inertia_ratio: stil=0.178 mat=0.035; complexity: stil=0.387 mat=0.044

### Prop 3.4 mesh: silhouette in 4-D mesh feature space (negative = stadfest 3.4)

- **Verdikt:** STADFESTA
- **Statistikk:** -0.338
- **Detaljar:** CI95=[-0.366, -0.325], n=1971, n_styles=25

### Prop 1.4 mesh: NN distance CV in mesh feature space (Poisson null = 0.36)

- **Verdikt:** STADFESTA
- **Statistikk:** 0.956
- **Detaljar:** CI95=[0.855, 1.040], n=2202

### Prop 4.4 mesh: cumulative mesh-hull growth ratio

- **Verdikt:** STADFESTA
- **Statistikk:** 553
- **Detaljar:** monotone=True, CI95=[435×, 752308×], n=2028

### Prop 3.3 mesh: CV span (max/min across mesh features)

- **Verdikt:** STADFESTA
- **Statistikk:** 128.4×
- **Detaljar:** CI95=[50×, 158×]; most channeled = sphericity (CV=0.074)

## Mesh-baserte testar

### Mesh feature summary

- 2204 chairs with mesh features
- mean sphericity: 0.797
- mean fill_ratio: 0.645
- mean inertia_ratio: 0.477
- mean complexity: 5.196


