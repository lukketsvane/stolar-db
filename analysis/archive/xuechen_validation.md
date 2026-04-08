# Validering av FORMLÆRE si shape-grammar-implementering mot XueChen 2024

Kjelde: Xue, G. & Chen, J. (2024). "Strategies for Applying Shape Grammar to Wooden Furniture Design: Taking Traditional Chinese Ming-Style Recessed-Leg Table as an Example." *BioResources* 19(1): 1707-1727.

Mål: bruke ein moderne, rotmøbel-applisert shape-grammar-artikkel som målestokk for å sjå om FORMLÆRE har implementert nok shape-grammar-apparat til å vere konsistent med gjeldande praksis.

## Korleis XueChen formaliserer shape grammar

**Tuple-definisjon (s. 1711):** SG = ⟨S, L, R, I⟩ der:
- S = endeleg mengd initialformer
- L = endeleg mengd merka former
- R = endeleg mengd avleiingsreglar
- I = initialform

Dei attribuerer dette til "Stinney og Gipps 1972" (typo i artikkelen, dvs. Stiny & Gips). Notasjonen avvik litt frå Stinys klassiske SG = (V_T, V_M, R, I) og frå FORMLÆRE D4 sin SG = (S, R, ω). Skilnadene er notasjonelle, ikkje innhaldsmessige.

**To kategoriar avleiingsreglar (Tabell 1):**

| Kategori | Kommando | Operasjon |
|---|---|---|
| **Generativ** | R1 Erstatning | bytt ut delform |
| | R2a Tillegg | legg til delform |
| | R2b Sletting | fjern delform |
| **Avleidd** (transformativ) | R3 Skalering | proporsjonal vekst/krymping |
| | R4 Spegling | refleksjon over akse |
| | R5 Kopiering | dupliser om referansepunkt |
| | R6 Rotasjon | roter om referansepunkt |
| | R7 Forskyvd snitt | flytt punkt langs retning |
| | R8 Bezier-kurve | glatt nodar til kurve |

Skilet mellom **generativ** (endrar lokalt innhald: R1, R2) og **avleidd** (transformerer eksisterande form: R3-R8) er XueChens didaktiske grep, ikkje frå Stiny.

**Praktisk arbeidsflyt (Tabell 2-4, s. 1717-1718):**
1. Bygg eit DNA-genbasseng på 8 prototypar (A1-A8 — 8 ekte Ming-stol-bord)
2. Bygg eit erstatningsbasseng med 8 quetí-prototypar (B1-B8 — 8 arkitektoniske komponentar frå tempel-dekorasjon)
3. Velg éin prototype A1 som grunnform, dekomponer i nummerert linje­sett (a1...a20 for "yazi" + "c" for bein)
4. Bruk ein sekvens av R1-R8 med backup-element frå B-bassenget for å avleie tre alternative planar (Plan A, B, C)
5. Evaluer planane med semantisk differensial-spørjeskjema (6 aksar: simpel-kompleks, elegant-meretrikøs, lett-tung, moderne-tradisjonell, implisitt-eksplisitt, delikat-grov)
6. Velg det beste, modeller og render

**Avgrensing eksplisitt nemnd i konklusjonen (s. 1724):**
> "The experimental plan is only suitable for reasoning and deduction of two-dimensional grammar. In the future in-depth research, attempts and breakthroughs will be made in three-dimensional grammar."

XueChen 2024 jobbar **berre i 2D**. Dei strekar tre-dimensjonal shape grammar som ein open utfordring.

## Validering: kva FORMLÆRE allereie dekkjer

| XueChen-konsept | FORMLÆRE-dekning | Status |
|---|---|---|
| Stiny–Gips opphav | Føreord nemner Stiny & Gips 1972; A.5 diskuterer Turing-komplettheit; D4 byggjer på Stiny 1991 | ✓ |
| Tuple-definisjon SG = (S, R, ω) eller varianten med labels | D4 har SG = (S, R, ω); ingen labels (defensiv forenkling, jf. Stiny 1991) | ✓ |
| Regelapplikasjon under innleiring | 3.42 og D4 spesifiserer τ(a) ≤ s og s → (s − τ(a)) + τ(b) | ✓ |
| Konstruksjonshistorie irrelevant | 3.42 (operasjonen er definert under innleiring; forma sjølv avgjer kva reglar som kan fyre) | ✓ |
| Algebraisk emergens (delformer ingen operand inneheldt åleine) | 3.421 dekkjer dette eksplisitt | ✓ |
| Klynger i formrommet er statistiske spor av generative strukturar | 3.42 fyrste setning, og D5 (∀G : π(L(G)) dannar ei klynge) | ✓ |
| Tre-dimensjonal mesh-analyse | Fase 2 av prosjektet jobbar med 3D mesh-trekk; A.6.3 (sphericity, fill_ratio, inertia_ratio) | ✓✓ — overgår XueChen |

**Konklusjon:** FORMLÆRE implementerer det matematiske kjernen i shape grammar fullstendig, og gjer 3D-arbeid som XueChen eksplisitt nemner som ein open utfordring.

## Validering: tre konkrete moglege påbygg

Tre ting hjå XueChen som FORMLÆRE for tida ikkje nemner. Eg er ikkje sikker på at dei treng å vere med — det er stilval — men dei er kandidatar for round 9.

### A. Sondringa generativ vs avleidd regel

XueChen sin Tabell 1 deler reglar i to kategoriar:
- **Generative reglar** endrar lokalt innhald (erstatning, tillegg, sletting)
- **Avleidde reglar** transformerer eksisterande form (skalering, spegling, kopi, rotasjon, forskyvd snitt, kurve)

FORMLÆRE D4 har éin abstrakt regelapplikasjon: s → (s − τ(aᵢ)) + τ(bᵢ). Dette dekkjer **alt** matematisk (sidan τ er ein vilkårleg euklidisk transformasjon, og rule-paret (a, b) kan vere tomt), men sondringa mellom innhalds-endring og struktur-transformasjon er ikkje synleg i den abstrakte forma.

**Forslag:** Legg til ein liten sub-prop 3.422 t som flaggar at praktiske implementasjonar vanlegvis skiljer mellom generative reglar (a → b der b ≠ ∅) og transformative reglar (a → τ(a) for ein τ ∈ Trans(Eⁿ)). Dette er ein rein klassifisering av regelpara, ikkje ny teori.

### B. Konkrete transformasjonar enumererte

XueChen listar 6 konkrete transformasjonar (R3-R8). FORMLÆRE D4 nemner berre Trans(Eⁿ) abstrakt.

**Forslag:** Ein parentetisk merknad i 3.42 eller D4 om at den euklidiske transformasjonsgruppa Trans(Eⁿ) typisk vert realisert som translasjon, rotasjon, refleksjon og uniform skalering, og at praktiske implementasjonar i tillegg ofte tek med ikkje-euklidiske operasjonar (kurvefitting, ikkje-uniform skalering, parameteriserte deformasjonar) som ligg utanfor den strenge euklidiske ramma men er nyttige i designarbeid.

Dette ville dekkje at XueChen sin "Bezier curve command" (R8) ikkje er ein euklidisk operasjon, og at FORMLÆRE-formuleringa difor er strengare enn praktiske implementasjonar.

### C. Forholdet mellom klynge og prototype-bibliotek

XueChen byggjer ein "DNA gen-basseng" av 8 prototypar (Tabell 2). Dette er ein praktisk operasjonalisering: ei klynge i formrommet vert modellert som eit eksplisitt utval konkrete eksemplar som dekkjer variasjonen.

FORMLÆRE 3.4 definerer stil som klynge, og 3.6 talar om arketype som dukkar opp uavhengig. Men det er ikkje sagt at ein arbeidsflyt for å bruke klynger som prototype-bibliotek er ein aktiv praksis i feltet.

**Forslag:** Ein liten merknad i 3.6 eller som ny 3.61 om at klynger vert operasjonalisert i praksis som endelege utval av representative former (prototype-bibliotek), og at dei reglar som transformerer mellom dei utvalde formene gjev grammatikken si effektive uttrykskraft.

## Kva skal ikkje gjerast

- **Ikkje legg til "Zoom Command" eller andre engelske kommandoar.** XueChen brukar dei (R3-R8 har engelske namn), men FORMLÆRE forbyr "zoom" stilistisk og brukar nynorsk gjennomgåande. Ingen grunn til å leggje til engelsk terminologi.

- **Ikkje legg til DNA-metaforen.** XueChen sin "DNA gen-basseng" er ein didaktisk metafor, ikkje formell. FORMLÆRE har allereie eit meir presist vokabular (klynge, attraktor, formrom).

- **Ikkje legg til labels (L i tuple).** XueChen tek labels med, men dei er Stiny 1972-arven. Stiny 1991 og seinare har gått bort frå dei. FORMLÆRE D4 fylgjer Stiny 1991. Det er rett.

- **Ikkje legg til semantic differential evaluation.** XueChen brukar dette for å velje mellom planar — det er konsumentpreferanse, ikkje shape grammar. FORMLÆRE skil eksplisitt at estetisk dom er transcendent til formsystemet (føreord); difor høyrer dette ikkje heime i traktaten.

## Konklusjon

**FORMLÆRE har implementert shape grammar tilstrekkjeleg.** Det matematiske apparatet (sum/differanse-algebra over Eⁿ, regelapplikasjon under innleiring, emergens av delformer i 3.421, klynge-grammatikk-bru i D5) er på eller over nivået i den siste empiriske artikkelen som faktisk brukar shape grammar på møblar.

På to punkt overgår FORMLÆRE XueChen:
1. **Tre-dimensjonalitet:** XueChen jobbar i 2D og nemner 3D som ein open utfordring; FORMLÆRE har 3D mesh-trekk på 2 202 stolar.
2. **Empirisk testing:** XueChen demonstrerer ein arbeidsflyt på éin prototype; FORMLÆRE har 14 hypoteser med bootstrap-CI95 og 84 hold-out-testar.

På tre punkt kunne FORMLÆRE leggje til klargjerande merknadar utan å endre teorien:
- A: Generativ vs avleidd regel-sondring (kandidat 3.422)
- B: Konkrete transformasjonar i Trans(Eⁿ) (parentetisk i 3.42 eller D4)
- C: Klynge som prototype-bibliotek (kandidat 3.61)

Eg foreslår å implementere alle tre i ein kompakt round 9. Dei utvidar ikkje teorien; dei gjer henne lesbar for nokon som kjem frå applikasjonsdomenet.
