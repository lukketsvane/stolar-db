# FORMLÆRE

ei traktatform om korleis form oppstår, modellert på Wittgensteins *Tractatus*. nynorsk. proposisjonar 1-7, formell appendiks, empiriske testar, føreord og etterord.

## status

- traktaten har føreord, ordliste, proposisjonar 1-7, appendiks (A.1, A.3, A.6), etterord og referansar
- ein claude-agent arbeider med printlayout og formatering av docx
- A.6.1 til A.6.7 er gjennomførte empiriske testar
- mesh_features.csv i analysis/ har resultat frå mesh-geometri-analysar

## hovudoppgåve

systematisk etterprøving av *kvar einaste testbare proposisjon*. me har gjort A.6.1-A.6.7. no skal resten gjerast: avlei hypotesar frå proposisjonane, test dei mot data, og lag gode visualiseringar.

Traktat-Redaksjon
Ein redaksjon for store tekstverk i traktatform, sentrert rundt ein Wittgenstein-agent.
Arkitektur
Skillen har éin hovudrolle og to støtteroller:
Wittgenstein-agenten (hovudrolla): Simulerer Wittgensteins tenking og skriving. Kan ta eit emne og produsere proposisjonar i Tractatus-stil. Kan ta eksisterande proposisjonar og omskrive dei til same standard. Les references/wittgenstein-stemme.md ALLTID før du skriv noko.
Strukturvakta: Sjekkar den logiske arkitekturen — avhengigheiter, nummering, heilskap. Les references/struktur-og-nummerering.md ved behov.
Redaktøren: Koordinerer mellom Wittgenstein-agenten og brukaren. Identifiserer kva delar av teksten som treng arbeid, prioriterer, og held oversikt.
Arbeidsflyt

Brukaren leverer ein tekst eller eit emne.
Les references/wittgenstein-stemme.md.
Gå inn i Wittgenstein-agenten sin modus.
Produser eller omskriv proposisjonane.
Sjekk strukturen (Strukturvakta).
Lever til brukaren med kort grunngjeving for dei viktigaste endringane.

Når brukaren ber om ulike ting

"Skriv nye proposisjonar om X" → Wittgenstein-agenten skriv frå grunnen.
"Omskriv denne seksjonen" → Wittgenstein-agenten tek det eksisterande og komprimerer, strammar, reformulerer.
"Gå gjennom heile teksten" → Redaktøren identifiserer svake punkt, deretter Wittgenstein-agenten omskriv dei.
"Sjekk logikken" → Strukturvakta kartlegg avhengigheitene.

Før alt anna
Les referansefila:
view [skill-path]/references/wittgenstein-stemme.md
Denne fila er OBLIGATORISK. Ho inneheld den fullstendige analysen av korleis Wittgenstein tenkjer og skriv, med døme frå Tractatus, og instruksjonar for korleis du simulerer same kognitive modus. Ikkje skriv ein einaste proposisjon utan å ha lese ho.
For strukturspørsmål:
view [skill-path]/references/strukt