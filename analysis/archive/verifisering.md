# FORMLÆRE — verifiseringsrapport

Dato: 2026-04-07 (oppdatert etter round 5: empirisk audit + falsifiseringstestar)
Område: fase 1 av NOTE.md — verifisering av kvar proposisjon mot kjeldene i `referansar/`, og fase 2 — empirisk testing.

**Round 5 supplement:** Sjå `analysis/evidence_table.md` for endeleg evidens-styrke per funn (★ rating), `analysis/cross_validation.md` for hold-out-stabilitet (84/84 pass), og `analysis/falsification.md` for direkte falsifiseringstestar mot postulat 2.2, 4.1, 5.1 (alle held).
Metode: kvar fokusproposisjon er lest mot den primære kjelda. For interne logikkproposisjonar (T6, 5.521) er sjekken gjord ved utfalding av definisjonane. For empiriske påstandar (A.6) er tala reprodusert frå `STOLAR.csv` med same metode som `analysis/formlare_analyse.py`.

Statusmerkelapp:
- **OK** — proposisjonen står
- **PARTIAL** — kjernekravet held, men formuleringa eller attribusjonen treng korrigering
- **OVERSTATED** — påstanden er sterkare enn kjelda eller dataa kan bere
- **INCOHERENT** — proposisjonen motseier ein annan proposisjon eller har intern matematisk feil

---

## Samandrag av funn

| Proposisjon | Status | Hovudissue | Handling |
|---|---|---|---|
| Føreord (Stiny–Gips Turing) | OVERSTATED | "beviste" er feil; Stiny–Gips 1972 påstod, men leverte ikkje noko prov | Endre "beviste" → "argumenterte for", flagg som påstand utan konstruksjon |
| Føreord (C-K mapping) | PARTIAL | "Fire C-K-operatorar" er rett, men mappinga til fem lyskjegleop. er ikkje vist | Spesifiser mappinga eksplisitt |
| 1.2 (formrom) | (sjå Mitteroecker-rapport, ventar) | – | – |
| 2.6 (materialalgebra) | (sjå Gibson-rapport, ventar) | – | – |
| 2.61 (latent stål) | OVERSTATED | "230 år" er ikkje empirisk forankra; `den_universelle_stolen.md` rapporterer ikkje signifikans (p=0.485) | Hedge eller referer datasettavgrensinga |
| 3.1 (tilpassingslandskap) | (sjå Wright/Waddington-rapport, ventar) | – | – |
| 3.2 (fleire haugar) | (sjå Wright-rapport, ventar) | – | – |
| 3.3 (kanalisering) | (sjå Waddington-rapport, ventar) | – | – |
| 3.42 (formgrammatikk) | PARTIAL | Brua frå Stiny til seleksjonstrykk er FORMLÆRE sin, ikkje Stiny sin | Klargjer skiljet i formuleringa |
| 3.421 (kombinatorisk rikdom) | OK | – | Ingen endring |
| 4.3 (stase og brot) | (treng Eldredge-Gould-attribusjon — sjekk kjelde) | – | – |
| 5.1 (agent-postulat) | OK | – | Skil dei to delpåstandane |
| 5.2 (agent-definisjon) | PARTIAL | (g, d, δ)-trippelet er ikkje frå Rosenblueth/Wiener 1943; det er ein post-1950 kontrollteoretisk omformulering | Re-attribuer eller reformuler til to-leddet form |
| 5.21 | OK | – | Ingen endring |
| 5.22 (Turing universalitet) | OVERSTATED | Kategorifeil: Turing 1950 §5 gjeld diskrete tilstandsmaskinar, ikkje vilkårleg substrat | Drop Turing-attribusjonen eller restriker til diskret-tilstand-tilfellet |
| 5.521 (asymmetri under snitt) | INCOHERENT | I ein boolsk algebra fylgjer lukking under snitt frå lukking under sum og differanse (a ∩ b = a − (a − b)); 5.521 motseier seg sjølv | Reformuler som perseptuell vs generativ asymmetri (sjå internnotatet) |
| 5.56 (C-K spesialtilfelle) | PARTIAL+ERROR | "Fem operasjonar" er feil — C-K har fire; "spesialtilfelle" er strukturelt forsvarleg berre i agentklasse, ikkje i teoretisk uttrykkskraft | Korriger til "fire C-K-operatorar"; presisér spesialtilfelle-påstanden |
| D4 (formell formgrammatikk) | OVERSTATED | "Tre operasjonar" er ikkje Stiny 1991 (han har sum + differanse + transformasjonar); "produkt" er feil ord for snitt | Endre til to operasjonar pluss Trans(Eⁿ), eller bruk "snitt" i staden for "produkt" |
| D6 (agent, monoton nedstig) | OVERSTATED | d(δ(x), g) < d(x, g) er for sterkt — falsifiserer alle ekte tilbakekoplingssystem (overshoot, oscillasjon, PID) | Erstatt med Lyapunov-vilkår |
| D8 (innleiringsoppløysing) | NOTASJONSFEIL | C(A) ⊆ Shape × T (D7), men D8 skriv "(t, τ) ∈ C(A)" — τ kan ikkje vere tid | Korriger til "∃u ∈ T : (t, u) ∈ C(A)" |
| T6 (agent–grammatikk-kopling) | OK (men trivielt) | Provet er definisjonsutfalding; konklusjonen handlar om reglar, ikkje transformasjonar | Reformuler konklusjonen; flagg som korollar |
| A.6.1 (empirisk MI mat;H) | EMPIRISK FEIL | Docx hevdar I(mat;H) = 0.526 bits, men reprodusert verdi er ≈ 0.092 bits (sklearn k-NN) | Oppdater til faktisk verdi |
| A.6.5 (latent stål, n) | EMPIRISK FEIL | Docx hevdar n=5 pre-1925 / n=152 post; faktisk n=2 (strict) eller n=45 (broad iron+steel) pre / n=109 post | Oppdater n; eller hedge konklusjonen |

---

## 1. Føreord — Turing-komplettheit

### Påstand
> "Stiny og Gips beviste at formgrammatikkar er berekningsmessig universelle: for kvar Turing-maskin finst det ein formgrammatikk som simulerer han."

### Funn
Stiny & Gips 1972 inneheld éi setning på s. 131:
> "they can also be used to simulate Turing machines and to generate musical scores, structural descriptions of chemical compounds, and the sentences—and their tree structures—in languages defined by phrase structure grammars."

Dette er ein **påstand utan konstruksjon, utan teorem og utan referanse**. Stiny 1980 og 1991 nemner ikkje Turing-maskinar i det heile. Bruken av "beviste" er difor faktuelt feil for 1972-artikkelen.

### Reformulering
> "Stiny og Gips (1972, s. 131) hevdar — utan formelt prov i artikkelen — at formgrammatikkar generaliserer Chomskys frasestrukturgrammatikkar over til ein geometrisk alfabet, og at dei kan brukast til å simulere Turing-maskinar. Sidan uavgrensa frasestrukturgrammatikkar er Turing-ekvivalente, fylgjer det at formgrammatikkar er minst like uttrykksfulle som ein Turing-maskin."

Same korrigering må gjerast i A.5 (Turing-komplettheitsargument).

---

## 2. Føreord — C-K mapping (sjå òg 5.56)

### Påstand
> "Denne traktaten viser at dei fire C-K-operatorane svarar til operasjonar på den kognitive lyskjegla (def. 5.5): utviding, auka oppløysing, rørsle, kollaps og skjerping."

### Funn
Hatchuel & Weil 2003/2009 har nøyaktig **fire** operatorar i "design square": K→C (disjunksjon), C→K (konjunksjon), C→C (partisjonering), K→K (slutning). Føreordet seier "fire C-K-operatorar" — korrekt — og listar deretter fem lyskjegleoperasjonar etter kolonet. Lesaren må sjølv slutte seg til mappinga, som ikkje er ein bijeksjon.

Påstanden om at "C-K er eit spesialtilfelle av den meir generelle strukturen" er forsvarleg berre om "spesialtilfelle" tyder restriksjon i agentklasse: lyskjegla gjeld for vilkårlege tilbakekoplingsstyrte agentar, mens C-K krev intensjonale agentar med proposisjonslogikk. Det er ikkje ein generaliteitspåstand om teoretisk apparat.

### Reformulering
> "Dei fire C-K-operatorane (K→C, C→K, C→C, K→K, jfr. Hatchuel & Weil 2003, 2009) kan tolkast som eit underutval av dei fem operasjonane på den kognitive lyskjegla (def. 5.5): K→C tilsvarar utviding og rørsle, C→C tilsvarar auka oppløysing, C→K tilsvarar kollaps, og K→K tilsvarar skjerping. C-K krev intensjonale agentar med proposisjonslogikk; lyskjegla krev berre negativ tilbakekopling (def. 5.2). I denne tydinga — restriksjon til ein mindre agentklasse — er C-K eit spesialtilfelle av lyskjegle-strukturen."

---

## 3. Proposisjon 2.61 — latent stål

### Påstand
> "Stål og tre hadde overlappande algebraar i 230 år. Då sveisinga kom, vart stålets algebra komplett, og strengt tatt større enn tre sin. Formene divergerte umiddelbart."

### Funn
1. **"230 år"** har ingen kjelde i `referansar/`. Latensperioden avheng heilt av kva som tel som "stål-stol": jern/smijern frå 1700-talet, eller spesifikt stål frå seint 1800-tal. Sveiseteknikkar (smigjering vs gass vs lysboge) går attende lenger enn ein konventionelt rekn med.
2. **Empirisk reproduksjon på STOLAR.csv (n = 2 048):**
   - Strikt "stål" som stoffnemning, utan tre i materiallista: **n = 2** før 1920 (frå 1745, 1904), **n = 109** etter. n=2 er for lite til ein hypotesetest.
   - Brei "stål, jern, metall" som stoffnemning: **n = 45** før 1920, **n = 225** etter. Welch t-test på H/W: pre μ=1.46, post μ=inf (flere null-cells skapar problem).
   - `analysis/resultater_samandrag.csv` rapporterer p=0.485 ("ikkje signifikant") for pre-1925 (n=97) vs post (n=86). Tala matchar ikkje verken docx A.6.5 eller mi reproduksjon — sannsynlegvis grunna ein tidlegare versjon av datasettet.
3. **Konklusjon:** "Formene divergerte umiddelbart" er ein sterk kausal påstand som verken `den_universelle_stolen.md` eller dei reproduserbare tala stadfestar i statistisk meining. Datagrunnlaget er for tynt.

### Reformulering
> "Stål og tre hadde i lang tid overlappande algebraar. Då sveisinga vart utbreidd, vart stålets algebra komplett. I STOLAR-datasettet (1280–2024) er det observert ein retning av aukande forskjell mellom stål- og treprodukt etter at sveiseteknikkane vart tilgjengelege, men sample-storleiken før den industrielle bruken av stål er for liten til å gjere statistisk signifikante samanlikningar over heile latensperioden."

Hedge er det rette her, ikkje sletting: argumentet er teoretisk gyldig som operasjonelt prinsipp, men den kvantitative påstanden ("230 år", "umiddelbart") må vike for det datagrunnlaget faktisk støttar.

---

## 4. Proposisjon 3.42, 3.421, D4 — formgrammatikk og algebra

### Funn (kjelde: Stiny & Gips 1972, Stiny 1980, 1991; 2006-PDF i `referansar/` er 3 KB stub, ikkje lesbar)

**3.42:** PARTIAL. Kjernepåstanden — at ein formgrammatikk er reglar over former i euklidsk rom, at reglar fyrer under innleiring, og at konstruksjonshistoria er irrelevant — er direkte forankra i Stiny 1991 s. 175 ("the necessity to know how objects have been described or have come to be never intrudes ... the history of objects may play a role by choice, or may be ignored completely"). Den siste setninga om at "seleksjonstrykka avgjer kva av dei moglege formene som vert realiserte" er FORMLÆRE sitt eige tillegg, ikkje Stiny sitt. Dette er forsvarleg som teoribygging, men formuleringa bør gjere skiljet eksplisitt.

**3.421:** OK. Påstanden er sentral i Stiny 1991 (figs 9–13, s. 175): "Neither of these chevrons, however, is recognized in the other description." Ingen endring naudsynt.

**D4:** OVERSTATED. Tre konkrete problem:
1. **"Tre operasjonar" er feil etter Stiny 1991** (s. 171, 174): "shapes are closed under operations of sum and difference, and transformations that are Euclidean". Det er **to operasjonar pluss transformasjonsgruppa**, ikkje tre. 1980-formuleringa har snitt som primitiv, men 1991 absorberer snittet i den boolske ringstrukturen.
2. **"Produkt" er feil ord** for Stiny sin "·". Stiny brukar konsekvent "intersection"/"snitt"; "produkt" er berre forsvarleg om D4 eksplisitt identifiserer strukturen som ein boolsk ring.
3. **Trans(Eⁿ) er ikkje med i operasjonslista**, men dukkar opp i innleiringsklausulen. Trans(Eⁿ) bør vere ein konstituent av strukturen.

### Reformulering av D4
> **D4 (Formalgebra og formgrammatikk, prop. 3.42).** Lat U_i vere ei algebra av former bygde av basiselement med dimensjon i (punkt, liner, plan, lekamar) i eit euklidsk rom Eⁿ, utstyrt med to operasjonar — sum (s₁ + s₂) og differanse (s₁ − s₂) — og lukka under den euklidske transformasjonsgruppa Trans(Eⁿ). Delformrelasjonen ≤ er ei partiell ordning på U_i. Ei innleiring av a i s er ein transformasjon τ ∈ Trans(Eⁿ) slik at τ(a) ≤ s. Ein formgrammatikk er eit trippel SG = (S, R, ω) der S ⊆ U_i, ω ∈ S er startforma, og R = { rᵢ : (aᵢ, bᵢ) } er ei endeleg mengd av regelpar. Regelapplikasjon: dersom τ(aᵢ) ≤ s, då s → (s − τ(aᵢ)) + τ(bᵢ). Språket er L(SG) = { s ∈ U_i : ω →* s ved bruk av reglar i R }.

### Reformulering av 3.42
> "Ei klynge i formrommet er det statistiske sporet av ein generativ struktur. Ein formgrammatikk er eit system av reglar som opererer direkte på former i eit euklidsk rom, ikkje på symbol som representerer former. Ein regel a → b kan brukast på ei form s når det finst ein euklidsk transformasjon τ slik at τ(a) ≤ s; resultatet er (s − τ(a)) + τ(b). Operasjonen er definert under innleiring, difor avgjer forma sjølv kva regelapplikasjonar som er tilgjengelege, og konstruksjonshistoria er irrelevant. Grammatikken spesifiserer kva former som er moglege; seleksjonstrykka — eit empirisk tillegg utanfor sjølve grammatikken — avgjer kva av dei moglege formene som vert realiserte."

---

## 5. Proposisjonar 5.1, 5.2, 5.21, 5.22 — agent og kybernetikk

### Funn (kjelde: Rosenblueth, Wiener & Bigelow 1943; Wiener 1948; Turing 1950)

**5.1 (postulat):** OK som postulat. Falsifiseringsvilkåret (uskiljbar frå tilfeldig prosess) er ditt eige tillegg, ikkje frå Rosenblueth/Wiener. Dei to delpåstandane bør skiljast: (i) den kybernetiske generaliseringa (Rosenblueth 1943 s. 19: "All purposeful behavior may be considered to require negative feed-back"), og (ii) den morforommeske påstanden (om at fordelinga av former er statistisk uskiljbar frå ein tilbakekoplingsfri prosess).

**5.2 (definisjon):** PARTIAL. (g, d, δ)-trippelet er **ikkje** Rosenblueth/Wiener/Bigelow 1943. Dei seier (s. 19) at åtferd er "controlled by the margin of error at which the object stands at a given time with reference to a relatively specific goal" — to element (mål + feilmargin), ikkje tre. Wiener 1948 ch. IV (Fig. 2, s. 102) har eit kontrollflytdiagram med subtractor + plant + gain — også tre boksar, men dei tilsvarar ikkje (mål, måling, justering); dei tilsvarar (feilsignal-kalkulator, plant, tilbakekoplingsforsterking). Den reine (mål, måling, justering)-trippelet er den standardiserte kontrollteoretiske omformuleringa frå 1950–60-talet (Bellman, Kalman, Åström). Den er **konsistent med** Rosenblueth/Wiener, men er ikkje deira formulering.

### Reformulering av 5.2
Anten (a) re-attribuer til etterkrigskontrollteori, eller (b) skriv om til den opphavlege to-leddsforma. Anbefalt (a):
> "Ein agent er eit system med tre eigenskapar: (a) eit mål det styrer mot, (b) ei måling av avstanden mellom noverande tilstand og målet, (c) ei justering i retning av målet. Trippelet (mål, måling, justering) er den standard kontrollteoretiske omformuleringa av Rosenblueth, Wiener og Bigelows (1943) negativ-tilbakekopling-definisjon av målretta åtferd."

**5.21:** OK. Direkte støtta av Rosenblueth et al. 1943 s. 18, 19, 22: "uniform behavioristic analysis is applicable to both machines and living organisms"; torpedoes og amoebar er i same celle av tabellen s. 21.

**5.22 (Turing universalitet):** OVERSTATED. To uavhengige resultat blir samanblanda:
- (a) Turing universalitet (1950 §5): digital maskin kan simulere kvar diskret tilstandsmaskin. Universaliteten er over diskret-tilstand-klassen, ikkje over vilkårleg fysisk substrat. Turing seier eksplisitt i §7 (s. 12) at "the nervous system is certainly not a discrete-state machine".
- (b) Multippel realiserbarheit av tilbakekoplingsstrukturar (Rosenblueth/Wiener): same negativ-tilbakekoplingsstruktur kan byggjast i mekaniske, elektriske, termiske og biologiske medium. Dette er observasjon, ikkje teorem.

Desse er uavhengige. Turing-universaliteten gjeld berre simulasjon av diskrete berekningar.

### Reformulering av 5.22
> "Funksjonell organisering kan i prinsippet realiserast i ulike substrat: Rosenblueth, Wiener og Bigelow (1943) demonstrerer at same negativ-tilbakekoplingsstruktur finst i mekaniske, elektriske, termiske og biologiske system. For diskret-tilstand-realisasjonar styrkjer Turings universalitetsresultat (1950, §5) dette ved at vilkårlege diskrete berekningar kan simulerast på ein universal maskin; men resultatet gjeld berre den diskrete klassen og innebér ikkje at vilkårleg fysikk kan realiserast i vilkårleg substrat."

### Reformulering av D6
D6 sin strikte monotone nedstig d(δ(x), g) < d(x, g) er for sterk — han falsifiserer kvar PID-kontrollar, kvar overshoot-respons, kvart Wiener-eksempel i Cybernetics ch. IV. Bytt ut med Lyapunov-vilkår:
> **D6 (Agent, prop. 5.2).** Agent A := (g, d, δ). Det finst ein Lyapunov-funksjon V over tilstandsrommet med V(g) = 0, V(x) > 0 for x ≠ g, slik at V er ikkje-aukande i forventning langs sekvensen x_{n+1} = δ(x_n). Den enklaste, men strengaste forma er V = d(·, g) med strikt monoton nedstig; svakare former tillèt forbiskyting og oscillasjon.

---

## 6. Proposisjon 5.521 — asymmetri under snitt

### Påstand
> "Mengda av delformer ein agent kan identifisere er lukka under sum og differanse, men ikkje under snitt."

### Funn
I ein boolsk algebra (eller boolsk ring) gjeld identiteten **a ∩ b = a − (a − b)**. Lukking under sum og differanse fører automatisk til lukking under snitt. Påstanden i 5.521 er difor matematisk inkoherent — han motseier seg sjølv så snart E(s, A) er behandla som ein boolsk delalgebra av Stiny si formalgebra.

Vidare står 5.521 i konflikt med D4 same måte: om D4 har snitt som primitiv, så fylgjer lukking under snitt frå sum og differanse; om D4 fylgjer Stiny 1991 (utan snitt som primitiv), har 5.521 ingenting å snakke om.

### Reformulering (anbefalt: perseptuell vs generativ asymmetri)
> "Den generative kapasiteten til ein agent — operasjonane han kan utføre på dei delformene han alt har identifisert — er lukka under sum og differanse: summen av to synlege delar gjev ei synleg form, og det som er att etter å fjerne ein synleg del frå ein annan er synleg. Den perseptuelle identifikasjonen av snittet mellom to former er derimot ein eigen operasjon: når to former møtest, kan overlappsregionen ha ein indre struktur som ikkje er avleidd frå nokon av dei to operandane sine eksisterande dekomposisjonar (jf. 3.421). Denne asymmetrien — at sum og differanse fylgjer av delformene agenten alt ser, medan snitt kan krevje ny resolusjon — er mekanismen bak 5.52."

---

## 7. Proposisjon 5.56 — C-K spesialtilfelle

### Påstand
> "C-K-designteorien formaliserer same fem operasjonar for intensjonale agentar med proposisjonslogikk. Lyskjegla krev berre def. 5.2. C-K er eit spesialtilfelle."

### Funn
**Tellingsfeil:** C-K har **fire** operatorar (K→C, C→K, C→C, K→K — Hatchuel & Weil 2003 s. 9–10; 2009 §3.4.1 s. 188). Lyskjegla har **fem** operasjonar. "Same fem operasjonar" er feil.

**Mappinga er ikkje rein:** Den naturlege mappinga er fan-out:
- utviding ≈ K→C (utvidande partisjon)
- rørsle ≈ K→C (utvidande partisjon, anna form) eller K→K
- auka oppløysing ≈ C→C (restriserande partisjon)
- kollaps ≈ C→K
- skjerping ≈ K→K

5-til-4-mappinga er ein surjeksjon, ikkje ein bijeksjon, og ho er ikkje opplagd.

**"Spesialtilfelle"** er forsvarleg berre i agentklasse: C-K krev intensjonale propositionslogiske agentar; lyskjegla krev berre negativ tilbakekopling. Den klassen lyskjegla gjeld for er strikt større. Men dette er ikkje det same som å seie at C-K-teorien er eit teoretisk spesialtilfelle: H&W posisjonerer eksplisitt C-K som **det samlande rammeverket** og reduserer andre designteoriar (Suh, GDT, German systematic) til spesialtilfelle av C-K (2003 §4.2).

### Reformulering
> "**5.56 o.** C-K-designteorien (Hatchuel & Weil 2003, 2009) formaliserer fire operatorar — K→C (disjunksjon), C→K (konjunksjon), C→C (partisjonering) og K→K (slutning) — for intensjonale agentar med proposisjonslogikk. Dei fem lyskjegleoperasjonane i def. 5.5 omfattar desse fire som ein restriksjon: utviding og rørsle svarar til K→C, auka oppløysing til C→C, kollaps til C→K, og skjerping til K→K. Lyskjegla krev berre def. 5.2 (negativ tilbakekopling) og gjeld difor for ein større klasse av agentar. C-K er såleis det propositionslogiske spesialtilfellet av lyskjegla."

---

## 8. T6 og D8 — agent–grammatikk-kopling

### Funn
**T6** er gyldig som korollar — provet er ein utfalding av D4 og D8, ikkje eit substansielt resultat. Konklusjonen "ulike agentar: ulike transformasjonar moglege" er semantisk upresis: Fireable er ei mengd av **reglar**, ikkje av transformasjonar. Den semantisk korrekte konklusjonen er at ulike agentar ser ulike reglar som fyringsklare.

**D8** har ein notasjonsfeil: D7 seier C(A) ⊆ Shape × T (form × tid), men D8 skriv "(t, τ) ∈ C(A)". τ er ein transformasjon, ikkje ein tid; det skal vere "∃u ∈ T : (t, u) ∈ C(A)".

### Reformulering av D8
> **D8 (Innleiringsoppløysing, prop. 5.52).**
> E(s, A) := { t ∈ Shape : t ≤ s ∧ ∃u ∈ T : (t, u) ∈ C(A) }

### Reformulering av T6
> **T6 (Agent–grammatikk-kopling, av D4 og D8).**
> Lat R vere ei mengd grammatikkreglar, s ei form, A ein agent. Definer
> Fireable(R, s, A) := { rᵢ ∈ R : ∃τ ∈ Trans(Eⁿ) : τ(aᵢ) ≤ s ∧ τ(aᵢ) ∈ E(s, A) }.
> Same grammatikk, same form, ulike agentar: ulike reglar er fyringsklare. Konsekvens: kva av dei moglege regelapplikasjonane som faktisk er tilgjengelege, er agent-relativt.
> Prov. Ved utfalding av D4 og D8. ∎

---

## 9. Empiriske påstandar i A.6 — kryss-sjekk mot STOLAR.csv

Reproduksjon med same metode som `analysis/formlare_analyse.py` (sklearn `mutual_info_regression` med `discrete_features=True` for diskrete prediktorar, `LabelEncoder` for kategoriske variablar).

### A.6.1 Multi-determinasjon

| Verdi | Docx hevdar | Reprodusert |
|---|---|---|
| I(materiale; H) | 0.526 bits | **0.092 bits** |
| I(stilperiode; H) | 0.593 bits | 0.578 bits |

`den_universelle_stolen.md` rapporterer I(mat; H) = 0.057 bits — også svært ulikt 0.526. Verdien 0.526 i A.6.1 ser ut til å vere ein **transponert eller forveksla verdi**. Truleg har materialet og stilen blitt forveksla i ein tidlegare versjon.

**Korrigering:** A.6.1 må oppdaterast til faktiske verdiar. Forslag:
> "I(materiale; H) = 0,09 bits. I(stil; H) = 0,58 bits. Begge er positive og uavhengige. A1 stadfesta: minst to uavhengige trykk finst, men stil dominerer over materiale når både er gruppert i grove kategoriar. (Sjå òg A.6.2.)"

### A.6.5 Latent stål

| Verdi | Docx A.6.5 | resultater_samandrag.csv | Reprodusert (strikt "stål") | Reprodusert (brei) |
|---|---|---|---|---|
| n pre-1925 | 5 | 97 | 2 | 45 |
| n post-1925 | 152 | 86 | 109 | 225 |
| H/W pre | 1.46 ± 0.37 | 1.22 ± 1.28 | 1.06 ± 0.37 | 1.45 ± 0.59 |
| H/W post | 1.18 ± 1.05 | 1.32 ± 0.41 | 1.16 ± 0.69 | – |

Tre uforeinlege talsett. Antakeleg stammar dei frå ulike subset, ulike materialdefinisjonar, eller ulike datasettsversjonar. Ingen av dei tre stadfestar at H/W "divergerte umiddelbart" etter 1925; det reproduserbare talet er at nesten alle stål-stolar i datasettet kjem etter 1925 (n=109 vs n=2 strikt), så *det er ikkje nok pre-data til å seie noko om divergens i det heile*.

**Korrigering:** A.6.5 må enten (a) hedge konklusjonen, (b) bruke ein anna metric (t.d. variansforhold, eller standardisert mahalanobis-avstand mellom stål- og treperioder), eller (c) bli erstatta av ein klarare formulert observasjon med tala faktisk støttar.

---

## 10. Wright/Waddington/Mitteroecker–Huttegger og Gibson — fullstendig

### 10.1 Proposisjon 1.2 (formrom)

**Status: PARTIAL** — konflaterer teoretisk og empirisk morphospace.

**Funn (Mitteroecker & Huttegger 2009, s. 55, 57–58, 65 fotnote 1):**
- "Mengda av alle former ein klasse kan ha" beskriv eit **teoretisk** morphospace (à la Raup 1966, McGhee 1999) — ein a priori parameterrom frå ein generativ modell.
- "Kvar målbar eigenskap svarar til ein akse. Kvar realisert gjenstand er eitt punkt i denne projeksjonen" beskriv eit **empirisk** Q-rom — eit affint rom utspent av målbare variablar (PCA-tradisjonen).
- M&H understrekar (s. 58): "Many classical morphospaces, such as Raup's space or the ones produced in early morphometrics, are affine spaces" — distansar, retningar og vinklar er ikkje bevarte utan eksplisitt metrisk konstruksjon (Kendall-form-rom).
- Kombinasjonen i 1.2 er problematisk fordi seinare proposisjonar (3.1 om landskap, 3.3 om kanalisering, 4.4 om hylsterveksten) implisitt antek euklidisk struktur som ikkje er garantert.

**Reformulering:**
> "1.2 d. Det **teoretiske formrommet** til ein klasse er mengda av alle formelt moglege former, definert av eit sett genererande parameter. Det **empiriske formrommet** er det affine rommet utspent av ein endeleg samling målbare eigenskapar; kvar realisert gjenstand er eitt punkt i dette rommet. Med mindre anna er sagt, brukar denne traktaten empirisk formrom."

### 10.2 Proposisjon 3.1 (tilpassingslandskap)

**Status: OK** — substansielt korrekt og trufast mot Wright 1932, men attribusjonen kan styrkjast og dal-definisjonen er upresis.

**Funn:**
- Topp/dal-rammeverket og lokal-maksimum-kriteriet er Wright 1932 (s. 3, "selection will easily carry the species to the nearest peak"; s. 5).
- Dal-definisjonen i FORMLÆRE ("posisjonar ingen selekterer, fordi kvar lita endring fører mot ein betre posisjon") beskriv geometrisk **sadlar**, ikkje lokale minima. Wright behandlar dalar som lågfit-regionar **mellom** toppar.
- Wrights landskap er over **gen-kombinasjonsrom**, ikkje morphospace. Spranget frå "formrom" til "tilpassingslandskap" føresett at seleksjon verkar på fenotype — fint, men bør attribuerast til **Simpson 1944**, som er den kanoniske kjelda for landskap over fenotype-rom.

**Reformulering (mindre):**
> "3.1 d. Tilpassingslandskapet (etter Wright 1932 og Simpson 1944) er grafen til den aggregerte verknaden av alle samtidige seleksjonstrykk over formrommet. Kvar posisjon har ein verdi: kor godt forma tilfredsstiller alle verksame seleksjonstrykk samstundes. Lokale maksimum er haugar: posisjonar der alle små endringar gjev dårlegare tilpassing. Former samlar seg på haugane fordi dei er stabile. Lokale minimum er dalar: posisjonar med lågare tilpassing enn alle nabopunkt. Mellom haugane finst sadlar."

### 10.3 Proposisjon 3.2 (fleire haugar)

**Status: PARTIAL** — konklusjonen er Wrights, men derivasjonen i FORMLÆRE substituerer ein anna mekanisme.

**Funn:**
- Wright 1932 (s. 3) avleider multi-toppigheit frå **kombinatorisk epistasi**: ~10^1000 gen-kombinasjonar med ikkje-additive interaksjonar gjev "an enormous number of widely separated harmonious combinations... 10^800 separate peaks". Argumentet er *ikkje* "mange seleksjonstrykk, derfor mange toppar" — det er "rugged genotype-fenotype-mapping, derfor mange toppar sjølv under konstant seleksjon".
- FORMLÆRE-derivasjonen "Av 2.2 og 2.3" (multi-trykk + konflikt) er eit anna sufficient condition: multi-mål Pareto-trade-offar gjev òg lokale optimum. Dette er velkjent i fleirobjektiv-optimalisering.
- Begge er gyldige, men dei er ikkje den same argumentet. FORMLÆRE risikerer å attribuere til Wright ein derivasjon han ikkje gav.

**Reformulering:**
> "3.2 t. Wright (1932) viste at multi-toppigheit er generisk i rugged epistatiske landskap. Same konklusjon fylgjer her av eit anna premiss: når fleire seleksjonstrykk verkar samstundes (2.2) og dreg i ulike retningar (2.3), gjev kvar trade-off ein eigen lokal Pareto-optimum. Talet på haugar som er synlege avheng òg av oppløysinga i det rommet ein måler. Få aksar, få haugar. Mange aksar, fleire. Dimensjonaliteten i formrommet avgjer kva topologi analysen kan registrere."

### 10.4 Proposisjon 3.3 (kanalisering som andrederiverte)

**Status: ORIGINAL FORMALISERING (skal flagga som FORMLÆRE sin, ikkje Waddingtons).**

**Funn:**
- Waddingtons kanalisering er eit **utviklingsmessig** omgrep (Strategy of the Genes ch. 2): stabilitet av ein ontogenetisk bane (creode) mot perturbasjon, sikra av tilbakekopling i gen-nettverket. Han seier eksplisitt (s. 38) at landskapet er ein **visuell representasjon** av buffering, ikkje sjølve mekanismen.
- Waddington skriv aldri ein derivat. Han brukar "the steepness of valley walls" (s. 23) som ein kvalitativ visuell metafor.
- Den moderne formalisering av kanalisering (Wagner, Booth, Bagheri-Chaichian 1997 *Evolution*; Rice 1998, 2002) gjer det som ein eigenskap av andre moment av genotype-fenotype-mappinga, ikkje som andrederiverte av tilpassingsfunksjonen.
- Den andrederiverte av tilpassingsfunksjonen ved eit lokalt maksimum er **stabiliserande seleksjon** (Lande 1979) — ein relatert men ikkje identisk storleik. Konflasjon av dei to er teknisk slurvete.

**Reformulering:**
> "3.3 d. Kvar haug er ein attraktor: ei form som er stabil fordi små endringar i alle retningar gjev dårlegare tilpassing. Brattleiken på dalveggane uttrykkjer kvalitativt kor stabilt forma er, etter Waddingtons (1957) bilete av epigenetiske landskap. Den andrederiverte av tilpassingsfunksjonen ved haugen — i denne traktaten kalla **kanaliseringsgrad** — operasjonaliserer dette geometrisk. Storleiken er knytt til, men ikkje identisk med, Waddingtons utviklingsmessige omgrep om kanalisering, og fell saman med Lande (1979) sitt mål for stabiliserande seleksjon i grenseskiftet."

### 10.5 Proposisjon 4.3 (stase og brot)

**Status: KORREKT INNHALD, MEN UATTRIBUERT.**

**Funn:** "Stase og brot" er kjerneinnhaldet i punctuated equilibrium (Eldredge & Gould 1972). Wright og Waddington har ingenting tilsvarande. Eldredge & Gould 1972 ligg i `referansar/`. Kauffman 1993 gjev den formelle modellen (NK-landskap, koevolusjonære skred).

**Reformulering:**
> "4.3 o. Empirisk (Eldredge og Gould 1972; jf. òg Kauffman 1993 for ein formell modell) er endringa ikkje jamn. Lange periodar med små justeringar vert avbrotne av brå opningar. Mønsteret er stase og brot. Etter kvart brot fylgjer rask spreiing inn i den nyopna regionen, deretter gradvis innsnevring mot nye haugar."

### 10.6 Affordanse (ordliste) og 2.6 (materialalgebra)

**KRITISK FUNN:** Filen `referansar/Gibson_1979_EcologicalApproachVisualPerception.pdf` er **156 KB Internet Archive HTML-feilside**, ikkje boka. Verifisering måtte gjerast mot Brown Univ. ch. 8-PDF online. Filen må erstattast.

**Affordanse-ordlista — Status: TENDENSIØS UTVIDING.**

Gibsons opphavlege definisjon (ch. 8, s. 127): *"The affordances of the environment are what it offers the animal"*. Affordanse er **fundamentalt relasjonell** mellom organisme og miljø. FORMLÆRE droppar organisme-polen og lèt materialet "tilby former" til seg sjølv. Likevel: Gibson **diskuterer** materialaffordansar eksplisitt: *"Solids also afford various kinds of manufacture, depending on the kind of solid state. Some, such as flint, can be chipped; others, such as clay, can be molded"*. FORMLÆRE-utvidinga er reachable frå Gibson, men eliderar relasjonspolen.

**Reformulering (ordliste):**
> "Affordanse (Gibson 1979): Det eit materiale tilbyr handverkaren — kva operasjonar substansen og dei tilgjengelege produksjonsprosessane gjer mogleg eller motset seg. Hjå Gibson er omgrepet relasjonelt mellom organisme og omgjevnad ('what it offers the animal'); her vert det innsnevra til relasjonen handverkar–materiale. Sml. Gibson 1979, kap. 8, om at faste stoff 'afford various kinds of manufacture'."

**Proposisjon 2.6 — Status: OVERSTATED.**

Tre konkrete problem:
1. **Stiny-mappinga er ikkje i Stiny.** Stinys sum og differanse er **formelle set-teoretiske operasjonar på former i tegningsalgebraen**, ikkje fysiske fabrikasjonsoperasjonar. Stiny 1991 s. 180 nemner møblar berre som målmengd for grammatikkar, ikkje som operatorar. FORMLÆRE-mappinga (lim ↔ sum, fil ↔ differanse) er ein analogisk overføring som må flagga som sådan.
2. **"Du mangla sum" er faktuelt feil.** Pre-bogesveis-metallarbeid hadde fleire føyingsteknologiar: **forge welding** (jernalderen og fram), **rivetering** (antikken til skipsbygging på 1900-talet), **brazing/lodding** (antikken), **mekanisk tap-and-slot, lock-seams**, **støyping**. Den haldbare versjonen er at **bogesveis gjorde kontinuerleg billig fuging langs vilkårleg geometri tilgjengeleg**, ikkje at sum-operasjonen var fråverande før.
3. **"Tre = komplett algebra" er òg overforenkla.** Tre fekk dampbøying (Thonet ~1859), bøyd kryssfiner (Eames 1940-talet), CNC. Treet sitt repertoar er òg historisk variabelt.
4. **Determinisme vs probabilisme:** "Det avgjer kva former som finst" er hard determinisme; same setning hedge med "signaturen er probabilistisk". Pick one.

**Reformulering:**
> "2.6 d. Kvar gong ein handverkar arbeider i eit materiale, opererer han under ei kostnads- og tilgjengelegheits-avgrensing på kva operasjonar materialet og dei tilgjengelege prosessane tillèt. Tre kan limast, skjærast, dampbøyast, dreiast og samanføyast (mortise-and-tenon, lamellering): det gjev eit rikt repertoar av både konstruktive og subtraktive operasjonar. Metall før den elektriske bogesveisen kunne filast, borast, hamrast, smias, naglast og loddast, men kontinuerleg materialføyning langs ei vilkårleg fuge var dyr og spesialisert. Sveiseteknologien gjorde slik føyning billeg og generell. Vi tek dette som ein analogi til Stiny (1991) sine formoperasjonar sum og differanse, utan å hevde at handverksoperasjonane er identiske med Stiny sine formelle algebra-operasjonar. Signaturen er probabilistisk: operasjonsrepertoaret bind sannsynsfordelinga over former, ikkje det enkelte objektet."

### 10.7 Proposisjon 2.61 — empirisk falsifisering av sterk versjon

Vidareføring av seksjon 3 i denne rapporten: bakgrunnsagenten stadfestar at den sterke versjonen ("formene divergerte umiddelbart") er **falsifisert** i `analysis/resultater_samandrag.csv` (rad 9): pre-1925 stål n=97, μ_HW=1.22; post-1925 n=86, μ_HW=1.32; **p=0.485**. Den svake versjonen (algebra som constraint, ikkje som driver) er konsistent med stil-MI ≈ 10× materiale-MI og er den haldbare formuleringa.

Reformuleringa i round 1 hedge'a delvis. Round 2 bør gå lenger og eksplisitt inkludere den empiriske null-resultatet.

### 10.8 Mitteroecker–Huttegger sin generelle åtvaring

Heile kapittel 1–4 i FORMLÆRE kjedar: formrom → tilpassingslandskap → kanalisering → punktuasjon, og antek euklidisk struktur over alt. Mitteroecker & Huttegger 2009 s. 64 åtvarar eksplisitt mot dette: "the usefulness and meaningfulness of statements about fitness landscapes partly depend on the geometrical and topological properties of the underlying phenotype or genotype space". For stoldata analysert via PCA er det underliggjande rommet **i beste fall affint**; euklidisk distanse, andrederivat og gradient-ascent vert alle approksimasjonar med vilkårsvilkår som bør statast.

**Anbefaling:** Legg til ein parentes/note i fase 1 (kanskje 1.2 eller 1.21) som flaggar at empiriske morphospaces er affine, og at euklidiske operasjonar (distanse, gradient, andrederivat) er approksimasjonar som krev grunngjeving.

---

## 11. Anbefalt rekkefølgje for endringar

1. **Kritiske empiriske/faktuelle feil først:**
   - A.6.1: oppdater I(mat; H) til reell verdi
   - Føreord + A.5: "beviste" → "hevda" om Stiny–Gips Turing-claim
   - 5.521: erstatt incoherent claim med perseptuell/generativ asymmetri
   - D8: korriger τ → u i innleiringsdefinisjonen
   - 5.56: "fem" → "fire", spesifiser mappinga
2. **Strukturelle korrigeringar:**
   - D4: to operasjonar + Trans(Eⁿ), eller bruk "snitt" for "produkt"
   - D6: bytt strikt monoton nedstig med Lyapunov-vilkår
   - 5.22: drop Turing-attribusjonen eller restriker til diskret-tilstand
   - 5.2: re-attribuer til etterkrigskontrollteori
3. **Hedge der dataa er tynne:**
   - 2.61: "230 år" → tonet ned, datagrunnlaget rapportert
   - A.6.5: hedge eller erstatt
4. **Kosmetisk/klargjering:**
   - 3.42: presiser at brua til seleksjonstrykk er FORMLÆRE sin
   - T6: marker som korollar, korriger semantikken til "reglar" ikkje "transformasjonar"

Endringane skal gjerast med `scripts/office/edit.py`, validert med `scripts/office/validate.py`, og kvar endring committa separat med kva+kvifor i meldinga.
