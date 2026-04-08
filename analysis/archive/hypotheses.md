# Testbare hypotesar frå FORMLÆRE

Fylgjande er ei systematisk utleiing av empirisk testbare hypotesar frå proposisjonane merka med `^a^`, `^o^` eller `^t^` som gjer ein empirisk prediksjon, og som ikkje allereie er dekte i A.6.1 til A.6.7.

## Proposisjon 2.2 ^a^
**Proposisjon:** For kvar funksjonell klasse finst det minst to seleksjonstrykk som er statistisk uavhengige av kvarandre.
**Falsifiseringsvilkår:** Postulatet fell om eitt einaste seleksjonstrykk kan forklare all observert formvariasjon.
**Testbar hypotese:** Viss vi modellerer formvariasjon (t.d. fysiske dimensjonar eller mesh-trekk), vil to uavhengige variablar (t.d. `materials_desc` og `style`) begge bidra signifikant og uavhengig til å forklare variansen.

## Proposisjon 3.2 ^t^
**Proposisjon:** Tilpassingsfunksjonen har generisk fleire lokale maksimum. Landskapet har difor fleire haugar.
**Testbar hypotese:** Fordelinga av stolar i formrommet (både empirisk ut frå bounding box, og frå mesh-trekk) vil framstå som multimodal i ein kjernedestitetsestimering (KDE), og ikkje som ein unimodal normalfordeling.

## Proposisjon 4.3 ^o^
**Proposisjon:** Endringa i formrommet er diskontinuerleg. Lange periodar med stase vert avbrotne av brå topologiske skifte.
**Testbar hypotese:** Viss vi reknar ut den morfologiske avstanden (t.d. Wasserstein-distanse i formrommet) mellom påfølgjande tidsperiodar, vil vi sjå at distribusjonen av endringsratar er tung-hala: median-endringa er låg (stase), men maksimum-endringa er eit signifikant hopp (brot).

## Proposisjon 5.1 ^a^
**Proposisjon:** For kvar funksjonell klasse finst det minst éin agent som navigerer tilpassingslandskapet via negativ tilbakekopling.
**Falsifiseringsvilkår:** Postulatet fell om fordelinga av former er statistisk uavskiljbar frå ein tilfeldig prosess.
**Testbar hypotese:** Tidsrekka av former i formrommet skil seg signifikant frå ein rein 'random walk' (Brownsk rørsle); variasjonen er underlagt styring og kanalisering mot attraktorar.

## Proposisjon 5.22 ^t^
**Proposisjon:** Agens er substrat-uavhengig.
**Testbar hypotese:** Ulike materiale (substrat) utelukkar ikkje same form. Naboar i formrommet (k-NN) vil difor dele materiale berre litt over tilfeldig sjanse, ettersom same posisjon kan nåast med ulike material.

## Proposisjon 6.1 ^t^
**Proposisjon:** Kvar realisert form er eit poly-agentisk kompromiss.
**Testbar hypotese:** Den gjensidige informasjonen (NMI) mellom form og kombinasjonen av to seleksjonstrykk (t.d. materiale × stil) er strengt større enn informasjonen frå dei to marginalt.
