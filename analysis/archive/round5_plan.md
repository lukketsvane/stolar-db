# Round 5+ — bok-arkitektur, empirisk rigour, integrerte figurar

Mål frå Iver:
1. Styrk overgangane mellom kapittel 4→5 og 5→6
2. Utvid kapittel 6 (multi-agent, bandbreidde, koordinering)
3. Oppdater føreord med koordinatsystem-framing
4. Mykje finare formattert appendiks og innhaldsliste
5. Innhaldsliste FØR føreord
6. Sidetal
7. Bygg gradvis sterkare empirisk prov; vis at modellen er falsifiserbar
8. Figurar inline i teksten
9. Berre **veldig overtydande** funn skal stå — drop dei svake
10. Iterativ forsking: design test → kjør → vurder → kuter eller styrk

## Diagnose: kva er svakt no?

### Svake hypoteser i hypothesis_results.csv

| Test | Status | Problem |
|---|---|---|
| 3.1 OU vs Brownian | PARTIAL | slopes peikar rett, men p-verdiar ikkje signifikante. **DROPP** eller styrk med ny metode |
| 3.2 KDE multimodal | STADFESTA (2 modes) | berre 2 modes — kunne vere artefakt av binning. **STYRK med bootstrap** |
| 6.1 multi-agent gain | STADFESTA (+0.05 bits) | gain er liten. **STYRK med større effekt-storleik eller dropp** |
| NMI uplift | STADFESTA (2.0×) | NOTE.md baseline er 4.3×. Vår 2× er svakare. **STYRK med ulike trekk-sett** |
| 5.22 substrat-uavhengig | STADFESTA (excess +0.048) | excess er liten. **STYRK med større k eller andre metrikkar** |

### Sterke hypoteser å leie med

| Test | Statistikk | Status |
|---|---|---|
| 1.4 morphospace non-uniform | CV(nn) = 5.99 vs Poisson 0.36 | **veldig sterkt** (16× over nullhypotese) |
| 2.4 proxy dominance | stil > mat 4/4 dim, alle MI-ratioar 5–10× | **sterkt** |
| 5.1 KS-test ≠ uniform | p ≪ 1e-200 | **ekstremt sterkt** |
| 4.3 stase/brot | max jump/median = 6.08 | **sterkt** |
| 4.4 hylsterveolum monotont | 107× clipped, monotont | **sterkt** |
| 3.3 mesh channeling | 123× CV-spreiing | **sterkt** |
| 3.4 mesh silhouette | −0.31 (negativt = stadfest 3.4) | **sterkt teori-stadfestande** |
| Mahogni-kollapsen | 16/16 i 1825–1849, p < 0.001 | **ekstremt sterkt** |

### Manglande tester (for å vise falsifiserbarheit)

| Postulat | Eksisterande test | Treng |
|---|---|---|
| 2.2 (≥ 2 uavhengige trykk per klasse) | indirekte i 2.4 | **direkte test**: Cov(predictor_i, predictor_j) per klasse, sjekk at uavhengigheit held |
| 2.3 (motstridande gradientar) | ingen | **gradient-konflikttest** mellom material og stil |
| 4.1 (landskapet endrar seg) | indirekte i 4.3 | **EMD-test**: Earth Mover's Distance mellom periode-fordelingar |
| 5.1 (tilbakekoplingsdrivne agentar) | KS-test ✓ | OK |
| 5.22 (substrat-uavhengig) | k-NN ✓ moderat | **styrk** med per-material k-NN per region |

### Manglande robustnesstestar

- **Bootstrap konfidensintervall** på alle kjernetal
- **Per-museum kryss-validering**: Nasjonalmuseet vs V&A — same bilete?
- **Periode-stabilitet**: held funna seg når vi held ut éin periode?
- **Stilperiode-stabilitet**: held funna seg når vi held ut den dominerande stilen?

## Plan i fasar

### FASE A — strukturelle tekstendringar (round 5)

A1. **Etterord** som proper heading-stil
A2. **Føreord oppdatering**: legg til koordinatsystem-avsnitt frå gamle 7.4
A3. **Overgangar styrking**: kap 4→5 og 5→6
A4. **Kapittel 6 utviding**: nye proposisjonar 6.31, 6.32, 6.41, 6.42 om bandbreidde, koordinering, multi-skala
A5. Validator + commit

### FASE B — dokument-arkitektur (round 6)

B1. **Sidetal** i footer (sjekk eksisterande, fiks om nødvendig)
B2. **Auto-TOC** frå H1 + H2, plassert FØR føreordet
B3. **Appendiks-formatering**: math-typografi, betre indentering, korrekt monospace for D-formelblokkene
B4. **Heading-stilar** konsistent: kapittelnummer + tittel som H1, A.x som H1, A.x.y som H2, etc.
B5. Validator + commit

### FASE C — empirisk rigour (round 7) — STØRST

C1. **Audit av eksisterande hypoteser**: kvar kvifor svak/sterk, dropp svake
C2. **Bootstrap CI** på alle kjernetal (1000 samples, 95% CI)
C3. **Per-museum kryss-validering**: NMK vs V&A separat
C4. **Hold-out testar**: dropp éin periode/stil, sjekk stabilitet
C5. **Direkte falsifiseringstestar**:
   - 2.2: Cov(p_i, p_j) per klasse
   - 2.3: gradient-konflikt mellom material og stil
   - 4.1: EMD mellom periodar
C6. **Effektstorleiks-rekning**: ikkje berre p-verdiar; Cohen's d, η², bootstrap CI
C7. **Skriv evidens-tabell** med styrkemerking (★, ★★, ★★★)
C8. **Oppdater verifisering.md og hypothesis_results.md** med nye tal og dropp svake
C9. Commit per delkøyring

### FASE D — figurar i teksten (round 8)

D1. **Generer publikasjonskvalitet-figurar** for kvar SLAGKRAFTIG funn
D2. **Captions** i nynorsk, prosa-stil, kort
D3. **Embed inline i docx** etter relevante proposisjonar (ikkje berre i figures/)
D4. **Refer figurane frå etterordet** der dei stør prosa-argumentet
D5. Sjekk at figurar har éi-linje overskrift utan "(prop X.Y)"
D6. Validator + commit

### FASE E — iterer (round 9+)

E1. **Les heile traktaten på nytt** etter alle endringane
E2. **Identifiser gjenståande logiske hopp** og fyll dei
E3. **Identifiser gjenståande svake påstandar** og styrk eller dropp
E4. **Foreslå dedikasjon** (om relevant)
E5. Final validator + commit

## Kva eg dropper frå analysen

Etter Iver sitt krav om "berre veldig overtydande funn":
- ❌ **3.1 OU vs Brownian** — p-verdiar ikkje signifikante, dropp eller erstatt med ein direkte attraktor-test
- ❌ **NMI uplift 2.0×** — under baseline 4.3×, dropp inntil vi finn rett feature-sett
- ❌ **6.1 multi-agent gain (+0.05 bits)** — for liten gain, dropp eller erstatt
- ❌ **5.22 substrat-uavhengig (+0.048 excess)** — for liten effektstorleik, dropp eller styrk

Behaldne sterke funn (★★★):
- **1.4** (CV=5.99 vs Poisson 0.36)
- **5.1** (KS p ≪ 1e-200)
- **3.4 mesh** (silhouette = −0.31, sterkt teori-stadfestande)
- **3.3 mesh** (123× CV-spreiing)
- **Mahogni-kollapsen** (16/16, p < 0.001)
- **2.4 proxy dominance** (stil > mat 4/4)
- **4.4 hylsterveolum monotont** (107× clipped)

## Suksesskriterie

- Alle behaldne hypoteser har CI95% utan å krysse nullhypotesen
- Falsifiseringstestar finst for kvart postulat
- Per-museum og per-periode kryss-validering held
- Etterord refererer til figurar
- TOC før føreord, sidetal i footer
- Validator OK
- Ingen påstand er svakare enn ★★ i evidens-tabellen
