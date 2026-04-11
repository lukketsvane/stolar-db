# Empirisk Oversikt (FORMLÆRE)

Status pr. 2026-04-08. Filer: `analysis/scripts_v2/fig_a6_*.py`,
`analysis/figures/fig-A.6.*.pdf`. Datakjelder: `STOLAR/STOLAR.csv` (2048 stolar),
`analysis/mesh_features.csv` (2202 stolar med mesh-trekk).

## Ferdige tester (figurar embedda i FORMLÆRE.pdf)

| §       | Prop  | Test                                          | Resultat                                              | Skript |
|---------|-------|-----------------------------------------------|-------------------------------------------------------|--------|
| A.6.1   | 1.4   | Mutual info (stilperiode vs materiale)        | Stil 1.9–2.3× over mat på alle 4 dim, n=1469          | `fig_a6_1_uniformitet.py` |
| A.6.2   | 2.4   | CV over 6 mesh-trekk                          | 128× spreiing (sphericity 0.074 → vol_hull 9.52), n=2202 | `fig_a6_2_kanalisering.py` |
| A.6.3   | 3.3   | Silhouette over 25 stilperiodar i 4D mesh-rom | s = −0.338 [−0.346, −0.329], 21/25 negative, p<0.001  | `fig_a6_3_silhouette.py` |
| A.6.4   | 4.4   | Kumulativ konveks hull-volum 1500–2050        | 7× monoton vekst over 10 50-årsperiodar, n=1041       | `fig_a6_4_ekspansjon.py` |
| A.6.5   | 4.5   | Mahogni-kohort i norske stolar 1825–1849      | 16/16 mahogni mot 0/16 i 1750–1799                    | `fig_a6_5_mahogni.py` |
| A.6.6   | 4.5   | Wasserstein-1 mellom 50-årsperiodar           | Mean 15.8 / 9.2 / 5.8 cm (H/W/D), 0/10 < 0.5 cm       | `fig_a6_6_wasserstein.py` |
| A.6.7   | 4.1   | Sentroid-trajektorie 1500–2050                | Bane 84 cm, netto 25 cm, tortuositet 3.45             | `fig_a6_7_trajektorie.py` |
| A.6.8   | 5.3   | Materialkompleksitet per nasjon               | Median 3 (NO/DK/FR) mot 2 (UK/IT), n=1582             | `fig_a6_8_materialblanding.py` |
| A.6.9   | 4.5   | Materialstraumen 1500–2025                    | Klare bølgjer: eik → nøttetre → mahogni → modernismen | `fig_a6_9_materialstraum.py` |
| A.6.10  | 4.1   | H/B-proporsjonen, rullande median             | Median fell frå 1.88 (1600) til 1.36 (2000)           | `fig_a6_10_proporsjon.py` |

## Delvis dekt / planlagde

| §       | Prop    | Test                                       | Status                                  |
|---------|---------|--------------------------------------------|-----------------------------------------|
| A.6.11  | 3.1     | OU mean reversion på dim-tidsserier        | TODO — fit `scipy` OU på H, W, D, H/W   |
| A.6.12  | 3.2     | Multimodalt landskap (KDE-haugar)          | TODO — gauss-mix på (PC1, PC2)          |
| A.6.13  | 4.3     | Diskontinuitet (changepoint)               | TODO — Bayesian changepoint på dim-snitt |
| A.6.14  | 4.3/4.5 | Vektorfelt / sti-avhengig flyt             | TODO — quiver på (W, H) flow            |
| A.6.15  | 5.1     | Levin-feedback (autokorrelasjon)           | TODO — ACF på dim-residual              |
| A.6.16  | 5.3     | Funksjonell nisjepartisjonering            | Delvis dekt av A.6.8                    |
| A.6.17  | 6.5     | Kauffmans tilstøytande moglege             | TODO — innovation rate via novel features |
| A.6.18  | 7.2     | Varians-felle: tettleik vs varians         | TODO — local density vs local σ²        |

## Noter

- Alle tal er reproduserbare frå skripta i `analysis/scripts_v2/`. Køyr ein
  enkelt fil med `python analysis/scripts_v2/fig_a6_X_*.py`.
- Felles stil ligg i `analysis/scripts_v2/style.py`. Endring i palett eller
  font slår gjennom på alle figurar i ein omgang.
- Originale (utdaterte) figurar er flytta til `analysis/figures_archive/`.
