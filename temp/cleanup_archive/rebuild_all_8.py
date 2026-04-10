# -*- coding: utf-8 -*-
import sys
import re

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. PREAMBLE AND STYLING FIXES
# Remove footer line and offset as requested "fjern og botmlinja"
content = content.replace(r"\renewcommand{\footrulewidth}{0.4pt}", r"\renewcommand{\footrulewidth}{0pt}")
content = content.replace(r"\fancyfootoffset[L]{16mm}", "")

# Ensure header rule is correct
if r"\fancyheadoffset[L]{16mm}" not in content:
    content = content.replace(r"\fancyhead[R]{\small\thepage}", r"\fancyhead[R]{\small\thepage}\n\fancyheadoffset[L]{16mm}")

# Footnote rule - keep invisible
content = re.sub(r"\\renewcommand{\\footnoterule}\{.*?\}", r"\\renewcommand{\\footnoterule}{}", content, flags=re.DOTALL)

# 2. RECONSTRUCT MAIN CONTENT
# We will identify the range from \mainmatter to \appendix
main_start = content.find(r"\mainmatter")
appendix_start = content.find(r"\appendix")

if main_start == -1 or appendix_start == -1:
    print("Markers not found!")
    sys.exit(1)

new_main_text = r"""\mainmatter
\silentchapter{Proposisjonar}{proposisjonar}

\prop{1}{}{Formverda er alt som er tilfelle.}

\prop{1.1}{o}{Formverda er totaliteten av realiserte konfigurasjonar, ikkje av ting.}

\prop{1.11}{t}{Alt som har form, har nettopp denne forma og ikkje ei anna.}

\prop{1.111}{t}{At ein konfigurasjon tek éin eksakt form, når uendeleg mange andre var logisk moglege, krev ei årsaksforklaring utover konfigurasjonen sjølv.}

\prop{1.1111}{t}{Forklaringa ligg i relasjonen mellom den manifesterte konfigurasjonen og totaliteten av dei formene som var moglege men ikkje vart realiserte. Det er ein relasjonell, ikkje ein absolutt, eigenskap.}

\prop{1.112}{d}{Eit \textbf{objekt} er den enklaste bestanddelen i ein form. Det er udeleleg og uforanderleg.}

\prop{1.1121}{t}{Sidan objektas natur inneber moglegheita for å inngå i konfigurasjonar, er alle moglege former allereie gjeve i og med objekta.}

\prop{1.1122}{o}{Moglegheita er logisk tilgjengeleg fordi objekta er der, ikkje fordi nokon tenkjer ho.}

\prop{1.12}{d}{Ein \textbf{konfigurasjon} er ein bestemt samanheng av objekt. Forma er konfigurasjonens struktur.}

\prop{1.2}{d}{\textbf{Formrommet} (\textit{morphospace}) til ein klasse er mengda av alle moglege konfigurasjonar for objekt i denne klassen.\footnote{Raup (1966); Mitteroecker \& Huttegger (2009)}}

\prop{1.21}{d}{Kvart realisert objekt er eitt eksakt punkt i dette n-dimensjonale rommet.}

\prop{1.211}{d}{Det empiriske formrommet er alltid ein projeksjon. Inga endeleg mengd parametrar fangar den latente kompleksiteten fullt ut.\footnote{Thompson (1917)}}

\prop{1.2111}{o}{Kvar projeksjon er eit val: ho avslører nokre relasjonar og gøymer andre. Det finst ingen nøytral projeksjon.}

\prop{1.2112}{o}{Projeksjonen er naudsynleg for empirisk testing, men ho konstituerer ikkje forma. Forma eksisterer uavhengig av korleis vi måler ho.}

\prop{1.22}{d}{Klassen er den funksjonelle kategorien som definerer formrommet. Ho set grensene; seleksjonstrykka formar fordelinga innanfor grensene.}

\prop{1.3}{d}{Formrommet deler seg topologisk i tre regionar: dei busette, dei opne og dei forbodne.}

\prop{1.31}{o}{Dei busette regionane utgjer det historiske arkivet. Dei fungerer som ankerpunkt for all framtidig navigasjon.}

\prop{1.311}{t}{Tyngda til eit ankerpunkt er proporsjonal med lengda på okkupasjonen og talet på uavhengige tradisjonar som har konvergert mot same posisjon.}

\prop{1.3111}{t}{Konvergens frå uavhengige kjelder er sterkare evidens for at ein posisjon svarer til ein reell haug i landskapet enn konvergens frå éin tradisjon åleine.}

\prop{1.32}{o}{Dei opne regionane utgjer det \textit{tilstøytande moglege}. Dei er tilgjengelege men uaktualiserte.}

\prop{1.321}{t}{Det tilstøytande moglege er ikkje uendeleg. Det er avgrensa av naboskapet til dei allereie busette regionane og av grensene til dei forbodne regionane.}

\prop{1.3211}{o}{Naboskapet til dei busette regionane tiltrekker; grensene til dei forbodne frastøter. Det realiserte rommet er ein funksjon av begge.}

\prop{1.33}{d}{Dei forbodne regionane er dei som vert utelukka av materielle, strukturelle eller energetiske avgrensingar under dei gjeldande vilkåra.}

\prop{1.331}{t}{Det som er forbode under eitt sett av vilkår, treng ikkje vere forbode under eit anna. Grensa mellom det opne og det forbodne er dynamisk.}

\prop{1.3311}{o}{Eit materiale som gjer ein region forboden, kan verte erstatta av eit materiale som opnar same region. Grensa er ikkje ein eigenskap ved forma; ho er ein eigenskap ved vilkåra.}

\clearpage
\addcontentsline{toc}{chapter}{2 Ikkje alle posisjonar er like sannsynlege}
\markboth{ikkje alle posisjonar er like sannsynlege}{}
\prop{2}{}{Ikkje alle posisjonar er like sannsynlege.}

\prop{2.1}{d}{Eit \textbf{seleksjonstrykk} er ein faktor som endrar sannsynlegheitsfordelinga over formrommet. Det er ikkje ein regel som dikterer éi form, men ein gradient som gjer visse posisjonar meir sannsynlege enn andre.\footnote{Wright (1932)}}

\prop{2.11}{t}{Eit seleksjonstrykk åleine determinerer ikkje ein posisjon. Det avgrensar kvar posisjonen ikkje kan vere.}

\prop{2.111}{t}{Form er det som vert att når alle seleksjonstrykk har utelukka det dei kan utelukke. Ho er ein rest, ikkje ein konstruksjon.}

\prop{2.1111}{t}{Eit trykk som ikkje utelukkar nokon region er ingen trykk; det er ein tom kategori. Eit trykk som utelukkar alle regionar unntatt éin er ingen trykk; det er ein determinisme. Dei trykka vi observerer ligg mellom desse ytterpunkta.}

\prop{2.12}{a}{For kvar funksjonell klasse verkar det alltid meir enn eitt seleksjonstrykk samstundes.}

\prop{2.121}{t}{Einsidige forklaringar av form er alltid ufullstendige.}

\prop{2.1211}{t}{Dersom berre eitt trykk verka, ville alle former i klassen anten vere identiske eller tilfeldig fordelte langs éin akse. Den observerte ikkje-uniformiteten med variasjon langs fleire uavhengige aksar krev fleire uavhengige trykk.}

\prop{2.1212}{t}{At eit trykk er latent betyr ikkje at det er fråverande. Det er vanskeleg å telje trykk som ikkje varierer i det observerte utvalet; metodisk krev dette variasjon i vilkåra, ikkje berre variasjon i formene.}

\prop{2.13}{a}{For minst eitt par av seleksjonstrykk peikar gradientane i motstridande retningar i minst éin region av formrommet.}

\prop{2.131}{t}{Av 2.12 og 2.13: sidan fleire uavhengige trykk verkar og dreg i ulike retningar, kan ikkje alle verte optimalt tilfredsstilte samstundes. Kvar realisert form er eit kompromiss.\footnote{Michl (1995)}}

\prop{2.1311}{t}{Eit kompromiss er ikkje ein svakheit; det er den einaste moglege balansen under dei vilkåra som rådde.}

\prop{2.1312}{t}{Sidan det finst fleire gyldige kompromiss, er skilnaden mellom to former ikkje ein feil, men eit uttrykk for at kreftene kan balanserast på meir enn éin måte.}

\prop{2.1313}{o}{Å kalle ein form «suboptimal» føresett at ein veit kva ho er suboptimal \textit{i høve til}: kva trykk som tel, med kva vekt og kva som er ignorert. Utan eksplisitt spesifisering av trykk-settet er «suboptimal» ikkje falsifiserbart.}

\prop{2.14}{t}{Funksjonen definerer klassen og med det formrommet. Innanfor klassen er funksjonen konstant.}

\prop{2.141}{t}{Det som er konstant har null varians og ber null informasjon om kvifor éi bestemt form vart realisert framfor ei anna. All observert formvariasjon under konstant funksjon er driven av dei andre seleksjonstrykka.}

\prop{2.1411}{i}{Stolen og sofaen har ulik funksjon og utgjer ulike klasser. To stolar med ulik stil har same funksjon. All skilnaden mellom dei er ikkje-funksjonell.}

\prop{2.1412}{t}{At materialet er den faktiske mekaniske avgrensninga, medan stilperioden ber ingen ergonomisk bodskap, og likevel forklarer stilperioden meir formvariasjon enn materialet, er ein direkte empirisk motbevising av den funksjonalistiske doktrinen innanfor denne klassen.}

\prop{2.2}{d}{\textbf{Materialaffordansen} er dei operasjonane eit materiale tilbyr og motset seg under gjevne kostnads- og tilgjengelegheitsavgrensingar. Signaturen er probabilistisk: repertoaret bind sannsynsfordelinga, ikkje det einskilde objektet.\footnote{Gibson (1979)}}

\prop{2.21}{o}{Signaturen er latent. Det teoretiske repertoaret slår ikkje nødvendigvis ut i observerbar geometri.}

\prop{2.211}{o}{Materialet er til stades, men algebraen manglar. Det som endrar seg over tid er ikkje materialet, men kva operasjonar som er praktisk tilgjengelege.}

\prop{2.2111}{o}{Latensen kan vere lang. Stål var tilgjengeleg i hundreår før den fyrste røyrstolen; materialet fanst, men operasjonen som kunne utnytte det, fanst ikkje.}

\prop{2.2112}{t}{Formhistoria er difor systematisk langsamare enn materialhistoria. Nye materiale arvar formspråket til det substratet dei erstattar, heilt til eigne affordansar pressar dei ut i nye regionar av formrommet.}

\prop{2.22}{o}{Ein samlevariabel korrelert med alle samtidige seleksjonstrykk bør predikere formvariasjon betre enn kvart einskildtrykk.}

\prop{2.221}{o}{Stilperiode er ein slik samlevariabel. Han er ikkje ein forklaring; han er ein proxy som absorberer alle samtidige trykk in éin etikett.}

\prop{2.2211}{o}{Stilkategoriane beskriv kvar vandringa stansa. Dei forklarer ikkje kvifor ho stansa der.}

\prop{2.2212}{o}{Å forveksle den deskriptive og den kausale krafta til stilomgrepet er den vanlegaste feilen i formhistorieskrivinga. Stilperioden er eit symptom; seleksjonstrykka er årsaka.}

\clearpage
\addcontentsline{toc}{chapter}{3 Seleksjonstrykka produserer eit landskap over formrommet}
\markboth{seleksjonstrykka produserer eit landskap over formrommet}{}
\prop{3}{}{Seleksjonstrykka produserer eit landskap over formrommet.}

\prop{3.1}{d}{\textbf{Tilpassingslandskapet} er den aggregerte verknaden av alle samtidige seleksjonstrykk over formrommet. Kvar posisjon har ein verdi: kor godt forma tilfredsstiller alle verksame trykk samstundes.\footnote{Wright (1932)}}

\prop{3.11}{o}{Kvart seleksjonstrykk bidreg med ein vekt som varierer over tid.}

\prop{3.111}{o}{Vektene er ikkje frie parametrar; dei er empirisk tilgjengelege som samvariasjonen mellom kvart trykk og den observerte fordelinga, betinga på alle andre trykk.}

\prop{3.1111}{o}{Landskapet er retrospektivt rekonstruerbart. For eit gjeve tidspunkt kan vektene estimerast frå dei realiserte formene i ein temporal nærleik.}

\prop{3.1112}{o}{Landskapet er lokalt prediktivt: det predikerer kva regionar som har høgast sannsynlegheit for neste okkupasjon, ikkje kva einskildform som vert realisert.}

\prop{3.1113}{o}{Prediksjonshorisonten er ein funksjon av landskapets endringsrate. I periodar med stase som prediksjonen lang; i bifurkasjonar kort.}

\prop{3.12}{t}{Av 2.12, 2.13 og 3.1: tilpassingsfunksjonen har generisk fleire lokale maksima. Landskapet har difor fleire haugar.}

\prop{3.121}{d}{Ein haug er ein posisjon der kvar lita endring gjev dårlegare tilpassing.}

\prop{3.1211}{d}{Dalar er posisjonar ingen selekterer. Dei er ikkje forbodne; dei er berre ulønnsame.}

\prop{3.1212}{t}{Eit landskap med éin global optimal er eit spesialtilfelle, ikkje det generiske tilfellet. Funksjonalismens implisitte føresetnad om éin optimal løysing er empirisk feil for dei fleste funksjonelle klasser.}

\prop{3.1213}{t}{Multimodalitet i fordelinga er direkte støtte til proposisjon 3.12: todelinga mellom ein høgrygga og ein lågare modernistisk klynge er ikkje tilfelle, men eit empirisk mælbart trekk ved tilpassingslandskapet.}

\prop{3.2}{d}{Stabilitetsgraden til ein haug er brattleiken på dalveggane. Bratte veggar tyder kanalisering: forma er robust mot forstyrringar.\footnote{Waddington (1957)}}

\prop{3.21}{t}{Nokre seleksjonstrykk are sterkare enn andre. Dei sterkaste kanaliserer formrommet i få retningar.}

\prop{3.211}{t}{Hierarkiet av trykk produserer eit hierarki av kanalar: grove kanalar fyrst, finare innanfor dei grove.}

\prop{3.2111}{o}{Kanaliseringa er målbar som brattleiken på dalveggane i tettleikskartets topografi. Dei grove kanalane svarer til dimensjonar med låg variasjonskoeffisient; dei fine til dimensjonar med høg variasjonskoeffisient.}

\prop{3.2112}{o}{At nokre dimensjonar er nær låste og andre nær frie er ein direkte empirisk signatur av kanaliseringshierarkiet. Det er ikkje eit artefakt av projeksjonen.}

\prop{3.22}{d}{Ein \textbf{stil} er ei klynge av realiserte former kring same haug.\footnote{Kubler (1962)}}

\prop{3.221}{t}{At ein stil er ei klynge, ikkje ein kategori, forklarer kvifor stilar har uskarpe grenser. Grensa mellom to klynger i eit kontinuerleg rom er naudsynleg diffus.}

\prop{3.2211}{o}{Stilperiodar er gradientar, ikkje topologiske klynger. Gjennomsnittsstolen i ein stilperiode ligg nærmare nabostilane enn sine eigne medkandidatar.}

\prop{3.2212}{t}{At ein stil er eit statistisk fenomen og ikkje ein ontologisk kategori, forklarer kvifor kantane mellom periodar alltid er akademisk stridomne. Det finst ingen naturleg grense å finne; diffusheten er strukturelt naudsynt.}

\prop{3.3}{t}{Formgjeving konstruerer ikkje landskapet. Landskapet er gjeve av vilkåra. Å oppdage ein haug er ikkje å skape han.}

\prop{3.31}{t}{Ei form som dukkar opp uavhengig i tradisjonar utan kontakt, er sterkt prov for at haugen er ein eigenskap ved landskapet, ikkje ved nokon einskild tradisjon.}

\prop{3.311}{t}{Konvergensen forklarer seg sjølv: same vilkår, same gradient, same haug. Ho krev ingen kommunikasjon mellom tradisjonane; ho krev berre at dei navigerer det same landskapet.}

\prop{3.3111}{i}{At reduktive former oppstår parallelt i tradisjonar utan direkte kontakt, krev ingen intellektuell påverknad som forklaring. Same avgrensingstrykk produserer same haug, uavhengig av kven som navigerer.}

\clearpage
\addcontentsline{toc}{chapter}{4 Landskapet er dynamisk}
\markboth{landskapet er dynamisk}{}
\prop{4}{}{Landskapet er dynamisk.}

\prop{4.1}{a}{Seleksjonstrykka er ikkje konstante over tid.}

\prop{4.11}{t}{Av 3.1 og 4.1: landskapet er ein dynamisk flate. Haugar kan stige, søkke, flytte seg, bifurkere eller koalescere.}

\prop{4.111}{t}{Ein posisjon som var optimalt tilpassa under eitt sett av vilkår, kan i neste augeblink vere suboptimal. Optimal tilpassing er alltid lokal i tid.}

\prop{4.1111}{o}{Ein ny teknologi flyttar grensa for det forbodne. Ein ny marknad rekonfigurerer kva som vert belønna. Eit nytt materiale utvidar mengda av moglege operasjonar. Kvart av desse er eit inngrep i landskapet.}

\prop{4.1112}{o}{Den rullande medianen av høgde delt på breidde fell systematisk over fem hundreår. Proporsjonen 1.36 er ikkje meir ergonomisk enn 1.88: begge er innanfor menneskeleg sitteområde. Det er ein form-drift, ikkje ein funksjonsdrift.}

\prop{4.12}{o}{Endringa er diskontinuerleg. Lange periodar med stase vert avbrotne av brå topologiske skifte.\footnote{Eldredge \& Gould (1972)}}

\prop{4.121}{o}{Det typiske forløpet er: eksplosiv radiasjon inn i ein nyopna region, fylgd av gradvis konvergens mot nye attraktorar.}

\prop{4.1211}{o}{Episodisk diskontinuitet er ikkje brot med den underliggande dynamikken; ho er den dynamikken si synlege signatur. At endringsraten er diskontinuerleg, ikkje bimodalt fordelt, presiserer dette.}

\prop{4.1212}{o}{Det modernistiske brotet etter 1900 manifesterer seg som eit rekurrensmatrisemønster der ingen periode før 1900 liknar nokon periode etter 1900. Formhistoria gjentar seg ikkje på tvers av dette brotpunktet.}

\prop{4.13}{o}{Landskapet har minne. Kvar realisert form etterlet eit spor som modifiserer seleksjonstrykka for den neste.\footnote{Arthur (1994)}}

\prop{4.131}{t}{Forma og landskapet endrar kvarandre gjensidig. All formgjeving er omformgjeving: agenten startar aldri frå ein tom posisjon.}

\prop{4.1311}{t}{At agenten startar frå ein posisjon, tyder at ho arvar alt denne posisjonen impliserer: alle naboregionane som er tilgjengelege, og alle dei som er utelukka. Utgangspunktet er ikkje nøytralt.}

\prop{4.1312}{o}{Stiavhengigheit er difor eit strukturelt trekk ved formhistoria, ikkje ein anomali. At mahogni okkuperte 16 av 16 norske stolar i perioden 1825–1849, etter å ha vore fråverande i den føregåande tilgjengelege perioden, er stiavhengig seleksjonskollaps i sitt klaraste empiriske uttrykk.}

\prop{4.14}{o}{Formrommet ekspanderer kumulativt. Nye regionar vert busette; gamle vert sjeldan heilt forlate.}

\prop{4.141}{o}{Det kumulative konvekse hylsterveolumet veks monotont over alle tilgjengelege periodar, utan ein einaste tilbakegang. Eit fast funksjonsenvelop ville krevja metning.}

\prop{4.1411}{o}{Nyhetsraten fell ikkje monotont mot metning; han hentar seg inn att når nye materiale kjem inn. Det tilstøytande moglege er eit aktivt ekspanderande rom, ikkje eit tømmande lager.\footnote{Kauffman (1993)}}

\prop{4.1412}{o}{Materialstraumar er ein hovudmekanisme for landskapsendring. Kvart nytt materiale opnar nye regionar og stengjer andre. Materialstraumen 1500–2025 viser klare seleksjonsbølgjer, kvar av dei ein lokal kohortevent, ikkje gradvise overgangar mellom funksjonelt overlegne alternativ.}

\prop{4.15}{i}{Når eitt seleksjonstrykk vert dominant, kollapsar landskapet mot éin attraktor. Eit einsidig trykk som overkøyrer alle andre er ikkje ei forklaring av form; det er eit fråvær av forklaring.}

\prop{4.151}{t}{Diversiteten i det realisert formrommet er ein funksjon av mangfaldet i dei aktive trykka. Ein monokultur i formrommet er eit symptom på at eitt trykk har vorte uforholdsmessig dominant.}

\clearpage
\addcontentsline{toc}{chapter}{5 Det finst agentar som responderer på landskapet}
\markboth{det finst agentar som responderer på landskapet}{}
\prop{5}{}{Det finst agentar som responderer på landskapet.}

\prop{5.1}{a}{For kvar funksjonell klasse finst det minst eitt system som navigerer tilpassingslandskapet via negativ tilbakekopling.}

\prop{5.11}{d}{Ein \textbf{agent} er ein operator definert uttømande ved trippelet: måltilstand, avstandsmåling, justeringsmekanisme.\footnote{Rosenblueth, Wiener \& Bigelow (1943)}}

\prop{5.111}{t}{Definisjonen krev tilbakekopling. Ho krev korkje medvit, intensjon eller nervesystem; ho krev berre funksjonell organisering.\footnote{Wiener (1948); Turing (1950)}}

\prop{5.1111}{t}{Eit system som ikkje treng å vite kva det er laga av for å navigere mot eit mål, er ein agent uavhengig av kva det er laga av.}

\prop{5.1112}{t}{Ein stein som rullar nedover ei skråning er ikkje ein agent. Rørsla hans responderer ikkje på nokon avstand til nokon måltilstand. Grensa mellom agent og ikkje-agent går ved informasjonsflyt.}

\prop{5.112}{o}{Agentar skil seg i tre målbare eigenskapar: kor mykje av formrommet dei kan representere, kor rask tilbakekoplinga er, og kor djup læringsevna er.}

\par\addvspace{4pt}\noindent\includegraphics[width=\linewidth]{fig-5.23-agentar.pdf}\par\addvspace{2pt}

\prop{5.1121}{o}{Definisjonen er ikkje vakuøs; ho er stratifisert. Differansen mellom ein termostat og ein meisterhåndverkar ligg ikkje i substrat, mas i kompleksiteten i navigasjonskapasiteten.}

\prop{5.12}{t}{Agenten responderer ikkje på forma, men på landskapet. Måltilstanden er ikkje ein posisjon agenten oppfinnar; det er ein haug i landskapet agenten oppdagar.}

\prop{5.121}{t}{Agenten treng ikkje å forstå landskapet for å navigere det. Det er tilstrekkeleg å registrere den lokale gradienten. Navigasjonskompetanse krev ikkje kartografi.}

\prop{5.1211}{t}{Two agentar produserer same resultat om dei registrerer same lokale gradient, uavhengig av om dei har nokon representasjon av det globale landskapet. Kompetansen er lokal; effekten er global.}

\prop{5.2}{d}{Den \textbf{kognitive lyskjegla} til ein agent er den delmengda av formrommet han kan representere og påverke. Det som ligg utanfor lyskjegla, er kausalt utilgjengeleg.\footnote{Fields \& Levin (2022)}}

\prop{5.21}{o}{Lyskjeglene varierer i skala: frå cellulær fysiologi over minutt til designtradisjonar over hundreår.}

\prop{5.211}{o}{Lyskjegla avgrensar oppløysinga: kva delformer ein agent kan identifisere, avgjer kva transformasjonar som er tilgjengelege.}

\prop{5.2111}{o}{Barnet, snikkaren og algoritmen dekomponerer same form i ulike operasjonelle einingar. Same form; ulik oppløysing; ulike tilgjengelege operasjonar.}

\prop{5.2112}{t}{Ein agent oppdagar ikkje former; han oppdagar affordansar. Ein affordans er ein lokal eigenskap ved landskapet som berre er synleg innanfor lyskjegla.}

\prop{5.2113}{t}{Å utvide lyskjegla er å gjere latente affordansar synlege. Å krympe lyskjegla er å gjere realiserte affordansar usynlege.}

\prop{5.22}{d}{Five operasjonar modifiserer lyskjegla: utviding, oppløysingsauke, rørsle, kollaps, skjerping.}

\par\addvspace{4pt}\noindent\includegraphics[width=\linewidth]{fig-5.44-lyskjegle.pdf}\par\addvspace{2pt}

\prop{5.221}{d}{Utviding: lyskjegla dekkjer nye regionar. Handverkaren oppdagar eit nytt materiale.}

\prop{5.222}{d}{Oppløysingsauke: fleire delformer vert synlege i same region. Snikkaren lærer å sjå nye samanføyingar.}

\prop{5.223}{d}{Rørsle: lyskjegla flyttar seg til ukjent territorium. Designaren går frå møbel til arkitektur.}

\prop{5.224}{d}{Kollaps: lyskjegla krympar til éin realisert posisjon. Avgjersla vert endeleg.}

\prop{5.225}{d}{Skjerping: same dekning, høgare presisjon. Meistaren foredlar teknikken sin.}

\prop{5.2251}{t}{Operasjonane føreset berre kausal rekkevidd og tilbakekopling. Dei krev ingen representasjon av heile formrommet.}

\prop{5.23}{d}{Blant agentens kompetansar er evna til å operere direkte på geometri. Mengda av former i eit euklidsk rom, utstyrt med operasjonane sum og differanse, utgjer ein \textbf{formalgebra}. Formalgebraen er grunnlaget for det generative systemet.}

\prop{5.231}{d}{Ein \textbf{formgrammatikk} er eit sett reglar som opererer direkte på geometri: finn denne delforma i den noverande forma; erstatt ho med denne andre.}

\par\addvspace{4pt}\noindent\includegraphics[width=\linewidth]{fig-5.62-grammatikk.pdf}\par\addvspace{2pt}

\prop{5.2311}{t}{Kvar regel er definert under innleiring: ei delform kan identifiserast i den noverande forma uavhengig av korleis ho vart bygd. Reglane ser; dei hugsar ikkje.\footnote{Stiny \& Gips (1972)}}

\par\addvspace{2pt}\noindent\includegraphics[width=\linewidth]{shape_grammar_fig1.png}\par\addvspace{2pt}

\prop{5.2312}{t}{Forma sjølv avgjer kva reglar som kan fyre. Den noverande geometrien er den einaste premissen. Konstruksjonshistoria er irrelevant.}

\prop{5.232}{d}{Grammatikken genererer ein naboskap for kvar form: mengda av alle former som kan nåast ved éin operasjon. Naboskapen er formens lokale moglegheitsrom.}

\prop{5.2321}{t}{Naboskapen er ikkje symmetrisk. At du kan kome dit, tyder ikkje at du kan kome attende. Formrommet har ein retta struktur.}

\prop{5.2322}{t}{Kombinasjonen av to former kan framkalle delformer ingen av dei inneheldt åleine. Same form, ulike dekomposisjonar: ikkje fordi forma er tvetydig, men fordi ho er rikare enn kvar einskild operasjon som produserte ho.}

\prop{5.233}{t}{Grammatikken spesifiserer kva som er mogleg; seleksjonstrykka avgjer kva som vert realisert.}

\prop{5.2331}{t}{Grammatikken og landskapet møtest i agentens val: naboskapen gjev moglegheitene, landskapet gjev kvar moglegheit ein verdi, agenten aktualiserer den forma som tilfredsstiller gradienten.}

\prop{5.2332}{t}{Sidan lyskjegla avgjer kva innleiringar agenten kan oppdage, og sidan innleiringa avgjer kva reglar som kan fyre, er den generative kapasiteten avgrensa av lyskjegla. To agentar med same grammatikk men ulike lyskjeglar produserer ulike former.}

\prop{5.24}{o}{Materialet er ein agent av null-orden: det navigerer ikkje mot ein måltilstand, men det utelukkar posisjonar og favoriserer andre gjennom sine affordansar. Materialet gjev landskapet sin topografi.}

\prop{5.241}{i}{Ein planaria navigerer morforommet via bioelektriske gradientar. Ein handverkar navigerer formrommet via taktil tilbakemelding. Ein diffusjonsmodell navigerer eit latent rom via denoising. Substrata er ulike; strukturen er identisk.\footnote{Levin (2022, 2025)}}

\par\addvspace{4pt}\noindent\includegraphics[width=\linewidth]{fig-5.45-ck.pdf}\par\addvspace{2pt}

\prop{5.25}{t}{Navigasjonskompetanse er akkumulert. Kvar realisert form utvidar agentens lyskjegle. Læring er den temporale utvidinga av agentens tilgjengelege formrom.}

\prop{5.251}{t}{Læring er hierarkisk: frå enkel navigasjon via strategiskifte til restrukturering av sjølve formrommet.}

\prop{5.2511}{t}{Læring, biologisk seleksjon og bayesiansk inferens er isomorfe operasjonar i ulike substrat; dei minskar alle avstanden mellom modell og verd.}

\clearpage
\addcontentsline{toc}{chapter}{6 Forma oppstår mellom agentane}
\markboth{forma oppstår mellom agentane}{}
\prop{6}{}{Forma oppstår mellom agentane.}

\prop{6.1}{t}{Av 2.12 og 5.1: sidan meir enn eitt seleksjonstrykk alltid verkar, og sidan ulike agentar responderer på ulike trykk, er kvar realisert form eit poly-agentisk kompromiss.\footnote{Odling-Smee, Laland \& Feldman (2003)}}

\prop{6.11}{t}{Materialaffordansen, reiskapen, marknaden og kulturen utgjer uavhengige gradientar. Ingen einskild agent dikterer den resulterande morfologien; ho emergerer i skjeringspunktet mellom dei.}

\prop{6.111}{t}{Kvart hierarkisk nivå er ein kompetent problemløysar innanfor sin eigen lyskjegle. Dei lågare komponentane navigerer etter lokale gradientar, men bidreg samstundes til mål dei sjølve manglar kapasitet til å representere.}

\prop{6.1111}{t}{Reduksjonisme og holisme er komplementære skildringsnivå; begge er sanne, men ingen er tilstrekkeleg åleine.}

\prop{6.12}{t}{Sjølv når éin agent har nominell kontroll, avgjer landskapet kva reglar som faktisk fyrer. Agenten vel frå naboskapen; landskapet filtrerer naboskapen. Kontrollen er alltid delt.}

\prop{6.121}{o}{Kommunikasjonen mellom agentar vert avgrensa av ein endeleg bandbreidde.}

\prop{6.1211}{o}{Ved låg bandbreidde er navigasjonen grov og stokastisk; ved høg bandbreidde kan forma artikulerast gjennom eksplisitt spesifikasjon.}

\prop{6.1212}{t}{Det finst eit byttetilhøve mellom bandbreidde og uavhengigheit. Tett kopla agentar konvergerer mot eit felles representasjonsformat som avgrensar kva regionar dei kan utforske. Lauskopla agentar opprettheld kognitiv autonomi, men koordinerer dårlegare.}

\prop{6.1213}{t}{Det optimale koplingsregimet avheng av kva fase systemet er i: utforsking krev lauskopla agentar; utnytting krev tett kopla agentar.}

\prop{6.13}{o}{Bandbreidda har ein temporal dimensjon i form av latens. Ved høg latens må kvar agent operere på ein intern modell av dei andre agentane sin framtidige tilstand.}

\prop{6.131}{t}{Koordineringa er då berre so presis som modellens adekvatheit. Latensen er ikkje berre ein teknisk eigenskap ved kanalen, men ein epistemisk eigenskap ved agentens situasjon.}

\prop{6.14}{o}{Når koplinga mellom agentar er robust, emergerer eit overordna system med større lyskjegle og meir samansette mål.}

\prop{6.141}{t}{Når samanbindinga er tilstrekkeleg tett til at heilskapen realiserer ein eigen tilbakekoplingssyklus, vert heilskapen sjølv ein agent etter definisjonen i 5.11.\footnote{Kuhn (1962)}}

\prop{6.1411}{o}{Eit multi-agent-system kan oppnå metastabilitet på tvers av fleire skalaer utan at nokon einskild skala er fullt optimalisert. Denne stabiliteten let tradisjonar persistere gjennom fluktuasjonar som ville ha utsletta delane deira om dei opererte i isolasjon.}

\prop{6.15}{t}{Stilar og tradisjonar are deskriptive mellomkonstruksjonar utan kausal kraft. Dei skildrar dei punkta i formrommet der vandringa mellombels har stansa.}

\prop{6.151}{t}{Å formgje «i ein stil» er ein logisk feil: det er å imitere eit statistisk symptom utan å forstå dei seleksjonstrykka som genererte klynga i utgangspunktet.}

\prop{6.1511}{t}{Den som imiterer ein stil, imiterer ein effekt og ikkje ei årsak. Resultatet er ei form som liknar på tidlegare former utan å svare på dei same trykka.}

\prop{6.16}{o}{Nyhetsraten i formrommet er ein funksjon av det tilstøytande moglege: kvar realisert form opnar nye regionar av naboskapen som ikkje fanst før. Det moglege veks med det realiserte.\footnote{Kauffman (1993)}}

\prop{6.161}{t}{Formhistoria er ikkje ein uttapping av eit gjeve repertoar; ho er ein ekspansjon av repertoaret gjennom sin eigen rørsle.}

\clearpage
\addcontentsline{toc}{chapter}{7 Ingen form er endeleg}
\markboth{ingen form er endeleg}{}
\prop{7}{}{Ingen form er endeleg.}

\prop{7.1}{t}{Av 2.131 og 4.1: sidan seleksjonstrykka endrar seg, vil kvar realisert balanse med tida verte suboptimal. Kvar realisert form er gyldig berre for dei vilkåra som rådde i det augeblinket ho vart aktualisert.}

\prop{7.11}{t}{Dei mest robuste tradisjonane er ikkje dei rigide, men dei med høgast agensstratifisering: fleire uavhengige tilpassingsmekanismar på fleire skalaer gjev raskare respons når landskapet endrar seg.}

\prop{7.111}{o}{Det einaste varige er den generative strukturen: formrommet, seleksjonstrykka, landskapet, agentane. Formene i seg sjølve er flyktige spor; grammatikken er stabil.}

\prop{7.12}{o}{Dette rammeverket er ikkje ein ontologisk påstand om kva form er. Det er eit koordinatsystem for spesifikasjon.}

\prop{7.121}{o}{At strukturen er substrat-uavhengig er eit teikn på fruktbarheit, ikkje eit prov for sanning.}

\prop{7.1211}{o}{Agenten som skildrar formverda er sjølv ein del av ho. Det finst ingen arkimedisk punkt på utsida. Ei formlære er aldri transcendent; ho er alltid lokal og situert.}

\prop{7.13}{o}{Å gje form er: å definere kva måltilstand materien skal navigere mot; å velje kva krefter som skal utgjere landskapet; å utvide agentens kognitive lyskjegle slik at latente affordansar vert synlege; å akseptere at forma emergerer mellom agentane; å leggje til rette for vilkåra som dei kompetente delane opererer under.}

\prop{7.2}{}{Formverda er alt som er tilfelle. Tilpassingslandskapet er alt som verkar. Navigasjonen er utan slutt.}

\prop{7.3}{}{Denne traktaten er sjølv ein posisjon i eit formrom. At teksten kan fellast, er garantien for hennar gyldigheit.}
"""

# Re-apply the preamble from earlier turn but with updated header/footer rules
# Let's find the mainmatter start
mainmatter_start = content.find(r"\mainmatter")
appendix_start = content.find(r"\appendix")

if mainmatter_start != -1 and appendix_start != -1:
    content = content[:mainmatter_start] + new_main_text + "\n\n" + content[appendix_start:]

# Fix specific typos and formatting from the provided text
content = content.replace("always", "alltid")
content = content.replace("captures", "fangar")
content = content.replace("Two agentar", "To agentar")
content = content.replace("with éin global", "med éin global")
content = content.replace("are sterke", "er sterke")
content = content.replace("are deskriptive", "er deskriptive")
content = content.replace("Five operasjonar", "Fem operasjonar")
content = content.replace("mas i kompleksiteten", "men i kompleksiteten")

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(content)

print("Document Reconstructed with detailed numbering and correct formatting.")
