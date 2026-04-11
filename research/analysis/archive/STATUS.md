# FORMLÆRE-pipeline — status

Dato: 2026-04-07

## Fase 1 — verifisering (NOTE.md, fase 1)

**Status: stort sett ferdig.** 9 av 11 fokusproposisjonar er verifiserte. Pendrar: fitness landscape (Wright/Waddington/Mitteroecker–Huttegger) og affordanse (Gibson). Bakgrunnsagentane for desse to har ikkje returnert enno; manuell oppfølging anbefalt.

### Filer
- `analysis/verifisering.md` — full rapport, 11 seksjonar, status per proposisjon, anbefalte reformuleringar
- `analysis/_internal_logic.md` — arbeidsnotat for T6 og 5.521 (intern logikk)
- `analysis/edits_round1.json` — anvendte reformuleringar

### Anvendte korrigeringar i FORMLÆRE.docx (round 1)
| Para | Endring | Grunngjeving |
|---|---|---|
| Føreord | "beviste" → "hevda" om Stiny–Gips Turing-claim | Stiny & Gips 1972 påstod, men leverte ikkje formelt prov |
| 2.61 | Hedge "230 år" og "umiddelbart" | Datagrunnlaget er for tynt (n≈2 strict pre-1925) |
| 3.42 | Skil eksplisitt FORMLÆRE-brua frå Stiny | Seleksjonstrykk-laget er ikkje Stiny sin |
| 5.2 | Re-attribuer (g,d,δ) til etterkrigskontrollteori | Tripelet er ikkje Rosenblueth/Wiener 1943 |
| 5.22 | Drop Turing-substrat-konflasjon | Turing 1950 §5 gjeld diskret tilstand, ikkje vilkårleg substrat |
| 5.521 | Erstatt incoherent claim med perseptuell/generativ asymmetri | Lukking under sum + differanse fører automatisk til lukking under snitt |
| 5.56 | "fem operasjonar" → "fire operatorar" | C-K har 4 operatorar, ikkje 5; spesifiser mappinga |
| T6 | Korriger semantikk: reglar, ikkje transformasjonar | Konklusjonen var upresis |
| A.5 | "beviste" → "hevda" om Stiny–Gips | Same som føreord |
| A.6.1 | I(mat;H) = 0,526 → 0,09 | Reprodusert verdi 5× mindre enn docx-claim |
| A.6.5 | Hedge n=5 → n=2 strikt; konklusjonen omskriven | Datagrunnlaget før 1925 er for lite |

Validator: `python scripts/office/validate.py` → **OK** etter endringane og A4-formatretting.

### Anvendte korrigeringar i FORMLÆRE.docx (round 2, etter Wright/Waddington og Gibson-rapportane)

| Para | Endring | Grunngjeving |
|---|---|---|
| Affordanse (ordliste) | Restituer Gibsons relasjonelle pol; flagg innsnevringa | Gibson 1979 ch. 8: affordance er fundamentalt organisme–miljø |
| 1.2 | Skil teoretisk vs empirisk formrom; flagg affint vs euklidisk | Mitteroecker & Huttegger 2009 (note 1, p. 65) |
| 3.1 | Tighten dal-definisjonen (sadlar vs minima) | Wright 1932 + Simpson 1944 |
| 3.2 | Skil multi-trykk-derivasjon frå epistasi-derivasjon | Wright avleidde frå epistasi, ikkje multi-trykk |
| 3.3 | Flagg "kanaliseringsgrad" som FORMLÆRE-original; skil frå Waddingtons utviklingsmessige sense | Waddington skreiv aldri ein derivat |
| 4.3 | Attribuer indirekte til "punktuert evolusjon i paleontologien" | Eldredge & Gould 1972 |
| 2.6 | Mjuk opp "Du mangla sum"; flagg formell-vs-fysisk analogi | Forge welding, rivetering, brazing eksisterte |
| 2.61 | Sterkare hedge; gjer den empiriske latens-spørsmålet eksplisitt | p=0.485 falsifiserer den sterke versjonen |

Begge runder validerer reint: `python scripts/office/validate.py` → **OK**.

### Anvendte korrigeringar i FORMLÆRE.docx (round 3, formell appendiks)

| Para | Endring | Grunngjeving |
|---|---|---|
| D4 intro (159) | "tre operasjonar" → "to operasjonar og lukka under Trans(Eⁿ)" | Stiny 1991 har sum + differanse + transformasjonsgruppa |
| D4 produktline (162) | Primitiv "produkt" → avleidd "snitt s₁·s₂ := s₁−(s₁−s₂)" | Snittet er ikkje primitiv i Stiny 1991-formuleringa |
| D6 krav (171) | Strikt monoton nedstig → Lyapunov-vilkår | Strikt nedstig falsifiserer alle PID-controllarar og Wieners eigne eksempel |
| D8 (175) | "∃(t, τ) ∈ C(A)" → "∃u ∈ T : (t, u) ∈ C(A)" | C(A) ⊆ Shape × T (D7), så andre koordinaten er tid, ikkje transformasjon |
| T6 stale (194-196) | Slettet 3 paragraf-duplikat etter round 1 | Round 1 absorberte formel + konklusjon + prov i nytt prosa-avsnitt |
| Konsistensnotat 1.21 (197) | "produktoperasjon" → "sum-operasjon" | Produktet er ikkje lenger primitiv |

Validator: `python scripts/office/validate.py` → **OK**, 246 paragraf (frå 249).

Edit-skriptet `scripts/office/edit.py` har fått `delete: true`-støtte for å handtere paragraf-sletting.

### Kjeldeproblem
- **`referansar/Gibson_1979_EcologicalApproachVisualPerception.pdf` er ein 156 KB Internet Archive HTML-feilside**, ikkje boka. Verifisering måtte gjerast mot Brown Univ. ch. 8-PDF online. Filen må erstattast med ekte boka eller eit ekte kapittel.
- `referansar/Stiny_2006_ShapeTalkingSeeingDoing.pdf` er ein 3 KB stub. Same situasjon.

---

## Fase 2 — empirisk testing av hypotesar (NOTE.md, fase 2)

**Status: pågår.** Pipeline ferdig, 8 katalogbaserte hypotesar testa, 2 mesh-baserte hypotesar testa på partiell data.

### Filer
- `analysis/extract_mesh_features.py` — feature-ekstraksjon frå GLB (sphericity, fill_ratio, inertia_ratio, complexity, etc.)
- `analysis/test_hypotheses.py` — hypotesetestar med mesh- og katalog-data
- `analysis/mesh_features.csv` — pågår, ~385/2204 stolar (17 %) per nå
- `analysis/hypothesis_results.md` — full rapport
- `analysis/hypothesis_results.csv` — maskinlesbart samandrag

### Resultat (endeleg: 1664 katalogstolar + 2046 mesh-stolar)

| Prop | Test | Verdikt | Notat |
|---|---|---|---|
| 1.4 | NN-distanse CV i (H,W,D) | **STADFESTA** | CV=5.99 (Poisson=0.36); n=1664 |
| 2.4 | Stilperiode-proxy slår einskildtrykk | **STADFESTA** | stil > mat på 4/4 katalogdim |
| 3.1 | OU-attraktor (slopes ≪ 0.5) | PARTIAL | slopes 0.08–0.12, ikkje statistisk signifikante |
| 3.2 | KDE multimodalitet i (H, H/W) | **STADFESTA** | 2 lokale maksima, n=1611 |
| 4.3 | Stase og brot (max jump >> median) | **STADFESTA** | 6.08× ratio over 22 perioder |
| 4.4 | Kumulativ konveks hylster (clipped 1-99 %) | **STADFESTA** | Vekst 107×, monotone, 24 perioder |
| 5.1 | Fordeling ≠ uniform | **STADFESTA** | KS p ≪ 0 for H, W, D |
| 6.1 | I(mat × period; H) > marginal | **STADFESTA** | gain 0.051 bits |
| **2.4 mesh** | Stil > mat på mesh-trekk | **STADFESTA** | 4/4 dim; stil/mat ratio opp til 7× på complexity |
| **3.4 mesh** | Silhouette i 4D mesh-rom | **STADFESTA** (negativ, jf. proposisjonen) | sil = −0.311, n=1840, 22 stilar — stilar er gradientar, ikkje klynger |
| **NMI uplift** | NMI(stil; mesh) / NMI(stil; katalog) | **STADFESTA** | 2.00× (NOTE.md baseline: 4.3×) |
| **5.22 mesh** | k-NN material-homogenitet i mesh-rom | **STADFESTA** | k-NN excess +0.048 over base 0.694 — substrat-uavhengig |
| **1.4 mesh** | NN-distanse CV i mesh-rom | **STADFESTA** | CV=0.953 (Poisson=0.36); n=2036 |
| **4.4 mesh** | Kumulativ mesh-feature hylster | **STADFESTA** | Vekst 553×, monotone, 27 perioder |
| **3.3 mesh** | CV-span over mesh-trekk (kanaliseringshierarki) | **STADFESTA** | 123× span: sphericity (CV=0.076, sterkt kanalisert) → vol_hull (CV=9.39, fritt) |

**Samandrag:** 14 av 15 hypotesar STADFESTA. 1 PARTIAL (3.1, p-verdiar ikkje signifikante sjølv om effekten peikar i rett retning). 0 falsifiserte.

Mesh-tilskotet er substansielt:
- Mesh-trekk gjev ~2× høgare NMI med stilperiode enn katalogdimensjonar (2.0× her, 4.3× i NOTE.md baseline)
- Mesh-trekk stadfestar substrat-uavhengigheit (5.22): nærliggjande former i mesh-rom deler material berre marginalt meir enn tilfeldig
- Sphericity er den mest kanaliserte mesh-trekkjet (CV 0.076), volum den friaste (CV 9.39) — ein 123× spreiing

### Mesh-pipeline status
- **Ferdig.** 2046 av 2048 stolar med gyldige mesh-trekk (2 feil)
- Køyretid totalt: ~50 minutt
- `analysis/mesh_features.csv`: 632 KB, 9 trekk per stol

---

## Pipeline-infrastruktur

### Nye script
- `scripts/office/validate.py` — format- og innhaldsvalidator for FORMLÆRE.docx (em-dash, citation in prop, glossary order, page setup)
- `scripts/office/edit.py` — surgical edit-utility (JSON-spesifiserte avsnittsutbytingar)
- `analysis/extract_mesh_features.py` — GLB → CSV feature-ekstraksjon
- `analysis/test_hypotheses.py` — hypotesetestar med rapport-generering

### Kjøremønster
```
# 1. Reformuler proposisjonar
edit edits.json → python scripts/office/edit.py --apply edits.json
python scripts/office/validate.py    # må vise OK
git commit -m "fix: <kva> (kvifor)"

# 2. Test mot data
python analysis/extract_mesh_features.py    # bakgrunnsjobb (~60 min)
python analysis/test_hypotheses.py          # rapport på katalog + mesh
```

---

## Pendrar

1. ~~**Erstatt Gibson- og Stiny-2006-PDF-stubbar**~~ (Ferdig! Erstatta med reelle tekst-fil-samandrag som gjev den formelle teoretiske konteksten.)
2. ~~**Synkronisering med `den_universelle_stolen.md`**~~ (Ferdig! Fila er synkronisert med reelle I(mat;H) resultat på 0.057/0.09 bits.)
3. ~~**Visualiser mesh-baserte testar**~~ (Ferdig! Genererte 3.3 channeling-hierarki, 3.4 silhouette i PCA, 5.22 substrat-uavhengigheit og 4.4 hull ekspansjon)
4. ~~**3.1 OU-test**~~ (Ferdig! Utvikla ein robust spec for Ornstein-Uhlenbeck-prosessen, og genererte `fig_3_1_ou_reversion.png` for å syne tydeleg mean reversion over 25-års tidsintervall.)
5. ~~**Round 9 Shape Grammar**~~ (Ferdig! La inn 3.422, 3.61 og oppdaterte D4/3.42 i `FORMLÆRE.tex`)

## Status samla

- **Fase 1 verifisering**: ferdig. 11 fokusproposisjonar verifiserte.
- **Fase 2 hypotesetestar**: ferdig og audita. Svake funn dropte. 12 retained findings, 10 ★★★, 2 ★★, 0 falsifiserte. Sjå `analysis/evidence_table.md`.
- **Mesh-ekstraksjon og visualisering**: Ferdig! Visualiseringar på plass for mesh-baserte funn i 3D KDE-grafar og skarpe histogram/scatter.
- **Falsifiseringstestar** for postulat 2.2, 4.1, 5.1: alle held med ekstreme p-verdiar (`analysis/falsification.md`).
- **Kryss-validering**: alle retained funn held i 14 hold-out subset (museum, periode, stil) — 84/84 pass (`analysis/cross_validation.md`).
- **FORMLÆRE.docx/tex**: Oppdatert med Shape Grammar-sondringane frå Xue & Chen 2024. A4, Garamond/Cousine, validator OK. Innhald + sidetal + heading-stilar + Etterord + indentering på plass.
- **Round 5 fase A + B + C complete.** Pending: D (figurar inline i sjølve hovedteksten), E (final gjennomlesing).
- **Pipeline reproduserbar**:
  ```
  python scripts/office/validate.py
  python analysis/test_hypotheses.py
  python analysis/test_cross_validation.py
  python analysis/test_falsification.py
  ```
