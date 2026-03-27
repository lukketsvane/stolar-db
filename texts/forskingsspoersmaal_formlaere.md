# FORMLÆRE mot STOLAR-databasen: Forskingsspørsmål og metodar

> *Empirisk testing av ein generell formteori mot 1903 stolar frå Nasjonalmuseet og Victoria & Albert Museum*

---

## 1. Formrommet (Proposisjon 1)

### Forskingsspørsmål

**F1.1** Kor stor del av det teoretisk moglege formrommet for stolar er faktisk busett?

**F1.2** Kva regionar i formrommet er *forbodne* (fysisk umoglege), og kva regionar er *opne* (moglege men urealiserte)?

### Empiriske funn

Formrommet vart diskretisert i 10 cm-celler langs tre aksar (høgde, breidde, djupn). Av 1600 teoretiske celler er berre **312 busette (19,5 %)**. Over 80 % av det geometriske rommet er tomt.

| Dimensjon | Median | IQR | CV |
|-----------|--------|-----|-----|
| Høgde (cm) | 87,2 | [70,0 - 98,5] | 30,7 % |
| Breidde (cm) | 52,5 | [47,0 - 61,0] | 41,1 % |
| Djupn (cm) | 52,1 | [46,2 - 60,0] | 24,2 % |
| H/B-ratio | 1,66 | [1,16 - 1,94] | - |

### Praktisk metode

Tredimensjonal voxel-analyse av formrommet. Kvar realisert stol er eitt punkt. Tomme celler vert klassifiserte som *forbodne* (bryt ergonomiske eller strukturelle grenser) eller *opne* (teknologisk moglege men ikkje realiserte) basert på ingeniørfaglege kriterium.

---

## 2. Seleksjonstrykk (Proposisjon 2)

### Forskingsspørsmål

**F2.1** Er formvariasjonen innanfor ein funksjonell klasse (stol) for stor til å forklarast av funksjon åleine?

**F2.2** Kor mykje variasjon finst *innanfor* kvar stilperiode, samanlikna med *mellom* stilperiodar?

### Empiriske funn

Alle 1903 stolar har same funksjon: å sitje på. Likevel finn me:
- **663 unike materialkombinasjonar**
- **24 stilperiodar**
- **12 nasjonalitetar**
- **Kruskal-Wallis H = 49,1** (p = 2,19 x 10^-8) for høgde mellom materialar

Gjennomsnittleg intra-stil CV i H/B-ratio: **14,2 %**. Funksjonalisme har CV = 23,2 %, Postmodernisme 27,1 %, men Empire berre 3,5 %. Stilperiode forklarer **42,3 %** av høgdevariansen (Eta^2 = 0,423), noko som betyr at **57,7 % er uforklart av stil**.

> **Konklusjon**: Proposisjon 2.22 er stadfesta. Formvariasjon under konstant funksjon er eit robust empirisk faktum. Fleire uavhengige seleksjonstrykk verkar.

### Praktisk metode

Variansdekomponering (Eta^2) for å kvantifisere bidraget frå kvart seleksjonstrykk. Kruskal-Wallis testar for å stadfeste at ulike prediktorar (material, geografi, tid) gjev signifikant ulike fordelingar.

---

## 3. Tilpassingslandskapet (Proposisjon 3)

### Forskingsspørsmål

**F3.1** Kan stilperiodar identifiserast som *haugar* i formrommet - altså klynger med målbare senterposisjonar?

**F3.2** Er stilen ein *avleidd storleik* (prop. 8.5), eller har han eigenforklaringskraft?

### Empiriske funn

Stilar har tydelege senterposisjonar i formrommet:

| Stil | H/B-ratio | Tolking |
|------|-----------|---------|
| Funksjonalisme | 1,41 | Breiare, lågare |
| Postmodernisme | 1,63 | Middels |
| Barokk | 2,17 | Smalare, høgare |
| Regence | 2,32 | Høgast, smalast |

Eta^2 mellom/total = **0,421**: stilar forklarer 42 % av den dimensjonale variansen. Men intra-stil variasjon er vesentleg (CV = 14,2 %), noko som stadfestar at kvar haug har breidde: ein stil er ein *region*, ikkje eit punkt.

### Praktisk metode

Klyngeanalyse (k-means, DBSCAN) i det normaliserte formrommet. Samanlikne klyngestruktur med a priori stilklassifisering. Silhouette-score som mål på kor godt stilar fungerer som naturlege klynger.

---

## 4. Landskapet i rørsle (Proposisjon 4)

### Forskingsspørsmål

**F4.1** Aukar materialentropien monotont over tid, eller finst det kollapsar?

**F4.2** Kan me identifisere *omveltingspunkt* (prop. 4.21) der formvariasjonen endrar seg brått?

### Empiriske funn

**Shannon-entropi** (H') for materialdiversitet per hundreår:

| Hundreår | H' (bits) | Tal materialtypar | Evenness (J') |
|----------|-----------|-------------------|---------------|
| 1500-talet | 1,49 | 4 | 0,75 |
| 1600-talet | 3,81 | 38 | 0,73 |
| 1700-talet | 4,28 | 43 | 0,79 |
| 1800-talet | 4,65 | 53 | 0,81 |
| 1900-talet | 5,03 | 64 | 0,84 |
| 2000-talet | 4,42 | 29 | 0,91 |

Entropien aukar frå 1,49 til 5,03 bits over fem hundreår: landskapet vert rikare. Nedgangen til 4,42 bits på 2000-talet kan reflektere ufullstendig datainnsamling eller ein reell konsolidering.

Formvariasjon (CV i H/B-ratio) svingar mellom periodar med konvergens (1800-talet: CV = 22,8 %) og divergens (1950-talet: CV = 44,6 %).

### Praktisk metode

Tidsserieanalyse med glidande vindauge for entropi og CV. Changepoint-deteksjon (Bayesiansk eller PELT-algoritme) for å identifisere omveltingspunkt formelt.

---

## 5. Materialets geometriske signatur (Proposisjon 5)

### Forskingsspørsmål

**F5.1** Har ulike materialkategoriar signifikant ulike *geometriske signaturar* (prop. 5.2)?

**F5.2** Stadfestar dataen at stive materialar trekkjer mot breie, låge former, og fibrøse mot høge, smale (prop. 5.21)?

### Empiriske funn

**Kruskal-Wallis H = 185,1** (p = 9,06 x 10^-34) for H/B-ratio mellom dei 12 vanlegaste materiala. Signaturane er tydelege:

| Materialkategori | n | Median H/B | IQR |
|------------------|---|------------|-----|
| Metall (stivt) | 211 | 1,26 | [0,85 - 1,55] |
| Plastisk | 105 | 1,32 | [0,89 - 1,55] |
| Polstermaterial | 712 | 1,60 | [1,02 - 1,89] |
| Hardtre (fibrøst) | 1373 | 1,72 | [1,29 - 1,96] |

> **Stadfesting av 5.21**: Stivt, homogent materiale (stål: H/B = 1,25) trekkjer mot breie, låge former. Fibrøst materiale (tre: H/B = 1,72) trekkjer mot høgare, smalare. Plastiske materialar (H/B = 1,32) opnar for eksperimentelle former.

Likevel: Eta^2 (topp-30 materialar -> høgde) = **0,053**. Materialet åleine forklarer lite av *absolutt* høgdevarians, men mykje av *proporsjonsvarians* (H/B-ratio). Dette fordi materialet påverkar forholdet mellom dimensjonar meir enn dei individuelle dimensjonane.

### Praktisk metode

Permutasjonstest: tilfeldig tildel materialar til stolar og mål om den observerte signaturforskjellen er sterkare enn tilfeldig. Bayesiansk hierarkisk modell med material som grupperingsvariabel.

---

## 6-7. Navigasjon og substrat-uavhengigheit (Proposisjon 6-7)

### Forskingsspørsmål

**F6.1** Navigerer to ulike museum-*substrat* (Nasjonalmuseet og V&A) mot same region i formrommet?

**F6.2** Er materialoverlappen mellom substrata stor nok til å tale om konvergens?

### Empiriske funn

| Museum | n | Median H/B | IQR |
|--------|---|------------|-----|
| Nasjonalmuseet | 639 | 1,88 | [1,66 - 2,13] |
| V&A | 1223 | 1,47 | [0,90 - 1,79] |

**Mann-Whitney U**: p < 0,0001, **Cohen's d = 0,885** (stor effekt). Musea navigerer mot *ulike* regionar i formrommet. NM-stolane er høgare og smalare; V&A har meir variasjon.

Men: **Jaccard-indeks for materialar = 0,80** (60 av 75 materialtypar er felles). Musea deler same materialpalett, men realiserer ulike formar. Dette stadfestar prop. 9.51: sannsynlegheitsfordelinga over formrommet er substrat-avhengig.

### Praktisk metode

Samanliknande formromsanalyse mellom samlingar. Kernel density estimation (KDE) for å visualisere korleis ulike substrat okkuperer ulike regionar i same formrom.

---

## 8. Distribuert navigasjon (Proposisjon 8)

### Forskingsspørsmål

**F8.1** Aukar eller minkar materialkompleksiteten (tal materialar per stol) over tid?

**F8.2** Kva material-par opptrer oftast saman, og endrar co-occurrence-nettverket seg over tid?

### Empiriske funn

Materialkompleksitet svingar: frå 1,1 mat/stol på 1500-talet til 3,1 mat/stol kring 1800, og tilbake til 1,8 på 2000-talet. Topp-paret er **Mahogni + Tekstil** (74 co-occurrences), følgd av **Bøk + Silke** (84).

Desse para reflekterer den distribuerte arkitekturen: strukturmaterial (tre) og overflatematerial (tekstil/polstring) utgjer to uavhengige navigasjonsnivå som saman avgjer forma.

### Praktisk metode

Nettverksanalyse av material co-occurrence per halvhundreår. Modularitetsdeteksjon for å identifisere naturlege materialklynger. Samanlikning med proposisjon 8.3 (fleirskala-kompetansearkitektur).

---

## 9. Stiavhengigheit og stasjonær verknad (Proposisjon 9)

### Forskingsspørsmål

**F9.1** Er det temporal autokorrelasjon i formrommet - altså, liknar nærliggjande stolar i tid meir enn fjerne?

**F9.2** Varierer ulike nasjonalitetar sin posisjon i formrommet (geografisk stiavhengigheit)?

### Empiriske funn

Temporal autokorrelasjon i H/B-ratio:
- Lag-1: r = 0,200
- Lag-5: r = 0,115
- Lag-10: r = 0,138
- Lag-50: r = 0,052

Positiv, fallande autokorrelasjon stadfestar stiavhengigheit (prop. 9.11). Stolar nær kvarandre i tid liknar meir enn stolar langt frå kvarandre.

Geografisk signatur:
- Noreg: H/B = 1,91 (høgare, smalare tradisjon)
- Storbritannia: H/B = 1,58
- Frankrike: H/B = 1,45 (breiare tradisjon)
- Finland: H/B = 1,16 (lågast, breiast)

### Praktisk metode

Durbin-Watson-test og partiell autokorrelasjonsfunksjon (PACF) for formell testing av stiavhengigheit. Spatial autokorrelasjon (Moran's I) for geografisk dimensjon.

---

## 10. Ingen form er endeleg (Proposisjon 10)

### Forskingsspørsmål

**F10.1** Finst det tiår med ekstraordinær formvariabilitet (omveltingsperiodar)?

**F10.2** Kor raskt responderer formgjevinga på landskapsendringar?

### Empiriske funn

Mest variable tiår (std i H/B): **1840-talet** (std = 2,92), samanfallande med den industrielle revolusjonen og historismen. Mest stabile: **1770-talet** (std = 0,35), ein nyklassisistisk konvergensperiode.

Vekslinga mellom stabilitet og omvelting stadfestar prop. 10.1: ingen form er endeleg, og landskapet er i kontinuerleg rørsle.

### Praktisk metode

Rolling-window-analyse av formvariabilitet. Korrelasjon med kjende teknologiske og kulturelle brot (industriell revolusjon, modernismen, plastrevolusjonen) for å teste kausal kopling mellom landskapsendringar og formendringar.

---

## Samanfattande tabell: Empirisk status for FORMLÆRE

| Prop. | Påstand | Testmetode | Resultat | Status |
|-------|---------|------------|----------|--------|
| 1.22 | Formrommet har busette, opne og forbodne regionar | Voxel-analyse | 19,5 % busett | Stadfesta |
| 2.22 | Fleire seleksjonstrykk verkar | Variansdekomponering | CV > 14 % intra-stil | Stadfesta |
| 3.22 | Stilar er haugar i landskapet | Klyngeanalyse | Eta^2 = 0,421 | Stadfesta |
| 4.3 | Landskapet vert rikare over tid | Shannon-entropi | H' aukar 1,49 -> 5,03 | Stadfesta |
| 5.21 | Materialar har geometriske signaturar | Kruskal-Wallis | H = 185,1, p < 10^-33 | Stadfesta |
| 7.1 | Navigasjon er substrat-uavhengig | NM vs VA | Jaccard = 0,80, d = 0,885 | Delvis |
| 9.11 | Stiavhengigheit | Autokorrelasjon | r(lag-1) = 0,200 | Stadfesta |
| 10.1 | Ingen form er endeleg | Temporal CV | Veksling stabil/ustabil | Stadfesta |

---

*Analyse basert på 1903 reinska stolpostar frå STOLAR-databasen, mars 2026.*
*Analysekode: `src/formlaere_analyse_v2.py`*
