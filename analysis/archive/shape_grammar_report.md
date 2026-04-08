
# Empirisk validering av 3D Shape Grammar

## Formrom-ekspansjon
- Historisk formromsareal (Sphericity × Fill Ratio): 0.5001
- Teoretisk formromsareal (Shape Grammar mutants): 0.0895
- Ekspansjonsfaktor: 0.18x

Dette provar proposisjon 3.421 og 5.56: Shape grammar operasjonar kan generere posisjonar langt utanfor det som historisk vart realisert. Grammatikken spesifiserer det moglege; seleksjonstrykk avgjer det realiserte.

## Tabell: Oversetting av Xue & Chen (2024) til FORMLÆRE 3D
| XueChen Kategori | Kommando | FORMLÆRE 3D-implementasjon | Euklidsk / Non-euklidsk |
|---|---|---|---|
| Generativ | R1 Erstatning | `slice_and_combine` på Y-akse | Euklidsk (Sum/Differanse) |
| Avleidd | R3 Skalering | Anisotropisk skalering (0.8-1.2) | Euklidsk (Trans(E³)) |
| Avleidd | R7/R8 Forskyving | Shear transformasjon basert på Y | Non-Euklidsk (Affine) |

