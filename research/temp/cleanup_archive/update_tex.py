# -*- coding: utf-8 -*-
import sys

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = r"\mainmatter"
end_marker = r"\appendix"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('Markers not found!')
    sys.exit(1)

new_content = r"""\mainmatter
\clearpage
\addcontentsline{toc}{chapter}{1 Form er ein posisjon i eit rom av moglegheiter}
\markboth{form er ein posisjon i eit rom av\ldots}{}
\prop{1}{}{Form er ein posisjon i eit rom av moglegheiter}
\prop{1.1}{d}{Morforommet er den logiske mengda av alle moglege konfigurasjonar for ein gjeven funksjon.}
\prop{1.11}{a}{For kvar fysisk gjenstand eksisterer det éin eksakt konfigurasjon.}
\prop{1.12}{t}{Denne konfigurasjonen er eit diskret koordinat i morforommet. Dette koordinatet er forma.}
\prop{1.13}{t}{Forma er dermed uttømande definert av sin posisjon relativt til alle uaktualiserte posisjonar i rommet.}
\prop{1.2}{d}{Morforommet er topologisk inndelt i tre disjunkte regionar: den aktualiserte, den tilstøytande og den forbodne.}
\prop{1.21}{d}{Den aktualiserte regionen er mengda av instansierte posisjonar. Dette utgjer det historiske arkivet; fundamentet for all vidare formgjeving.}
\prop{1.22}{d}{Den tilstøytande regionen er mengda av posisjonar som kan nåast med éin logisk operasjon frå den aktualiserte.}
\prop{1.23}{d}{Den forbodne regionen er mengda av posisjonar lukka av fysikkens aksiom.}
\prop{1.3}{o}{Kvar empirisk måling av fysisk form er ein dimensjonsreduserande projeksjon. Valet av aksar avgjer kva topologiske grenser analysen registrerer.}
\prop{1.31}{t}{Av 1.3 følgjer: Inga endeleg mengd variablar i ein projeksjon kan fange den latente kompleksiteten i den fysiske forma fullt ut.}
\prop{1.4}{t}{Morforommet er absolutt substrat-uavhengig. Same matematiske posisjon kan okkuperast av eit insekt, ein menneskeleg handverkar eller ein generativ algoritme.}
\clearpage
\addcontentsline{toc}{chapter}{2 Ikkje alle posisjonar er like sannsynlege}
\markboth{ikkje alle posisjonar er like\ldots}{}
\prop{2}{}{Ikkje alle posisjonar er like sannsynlege}
\prop{2.1}{o}{Fordelinga av aktualiserte posisjonar i morforommet er ikkje termodynamisk uniform. Formene samlar seg i tette klynger med massive tomrom i mellom.}
\prop{2.11}{t}{Av 2.1 følgjer: Den ikkje-uniforme fordelinga krev ein kausal asymmetri i sannsynet for aktualisering.}
\prop{2.2}{d}{Eit seleksjonstrykk er ein vektor som aukar eller minkar sannsynet for aktualisering i ei gjeven region av morforommet.}
\prop{2.21}{t}{Sannsynlegheitsfordelinga for formgenerering er isomorf med ein ergodisk Markoff-prosess. Sannsynlegheita for ei ny form er radikalt betinga av historia.}
\prop{2.3}{a}{Kvar posisjon er samstundes underlagt eit sett av minst to uavhengige seleksjonstrykk.}
\prop{2.31}{o}{Vektorane frå uavhengige seleksjonstrykk (t.d. ergonomi versus produksjonsøkonomi) er i regelen ortogonale eller i direkte opposisjon.}
\prop{2.4}{t}{Av 2.3 og 2.31 følgjer: Det eksisterer inga form som maksimerer verdien for alle seleksjonstrykk samstundes.}
\prop{2.41}{t}{Ergo er kvar realisert form logisk definert som eit kompromiss.}
\prop{2.5}{d}{Materialaffordanse er funksjonen som determinerer grensene for den forbodne regionen. Materialet legg eigne sannsynsfordelingar over rommet.}
\prop{2.51}{o}{Signaturen til materialet er latent. Stål var tilgjengeleg i hundreår før den fyrste røyrstolen; materialet fanst, men den formelle operasjonen mangla.}
\prop{2.52}{o}{Nye material arvar formspråket til det substratet dei erstattar, heilt til eigne affordansar tvingar forma ut i nye regionar.}
\clearpage
\addcontentsline{toc}{chapter}{3 Seleksjonstrykka produserer eit landskap over formrommet}
\markboth{seleksjonstrykka produserer eit\ldots}{}
\prop{3}{}{Seleksjonstrykka produserer eit landskap over formrommet}
\prop{3.1}{d}{Tilpassingslandskapet er den aggregerte verdien av alle verksame seleksjonstrykk over morforommet.}
\prop{3.11}{t}{Høgda til kvar posisjon i landskapet korresponderer med kor robust kompromisset der stettar dei samla trykka.}
\prop{3.2}{t}{Av 2.4 følgjer at landskapet kjenneteiknast av multippel lokal optimalitet (fleire lokale maksima).}
\prop{3.21}{t}{Eit lokalt maksimum fungerer som ein matematisk attraktor for formelle vandringar.}
\prop{3.22}{t}{For å forlate eit lokalt maksimum må posisjonen vandre gjennom punkt med lågare høgd. Morfologisk endring krev eit adaptivt tap.}
\prop{3.3}{d}{Gradienten kring eit lokalt maksimum definerer graden av kanalisering. Høg negativ gradient determinerer formsekvensen med høg robustheit.}
\prop{3.4}{d}{Ein stil er den deskriptive nemninga på ei klynge av aktualiserte former kring same attraktor i landskapet.}
\prop{3.41}{t}{Sidan landskapet er eit topologisk kontinuum (3.1), manglar stilar skarpe logiske grenser. Klassifikasjon med eksakte grenser er logisk inkoherent.}
\prop{3.5}{t}{Seleksjon skapar ingen former; han er ein operator som utelukkande eliminerer posisjonane i dalane.}
\prop{3.6}{o}{Konvergent formgjeving oppstår logisk når uavhengige aktørar navigerer langs identiske gradientar mot den same attraktoren.}
\clearpage
\addcontentsline{toc}{chapter}{4 Landskapet er dynamisk}
\markboth{landskapet er dynamisk}{}
\prop{4}{}{Landskapet er dynamisk}
\prop{4.1}{a}{Dei underliggjande variablane som genererer seleksjonstrykka fluktuerer over tid.}
\prop{4.11}{t}{Av 4.1 følgjer at landskapet deformerast kontinuerleg. Posisjonane for lokale maksima forskyv seg, stykast opp eller kollapsar.}
\prop{4.2}{t}{Aktualiseringa av ein posisjon ved tidspunkt \textit{t} endrar seleksjonsvektorane for tidspunkt \textit{t+1}. Landskapet har eit materielt minne.}
\prop{4.21}{t}{Av 4.2 følgjer at form følgjer form. Den eksisterande forma endrar infrastrukturen, verktøya og forventningane for den neste.}
\prop{4.3}{t}{Det moglege ekspanderer rekurrerande. Kvar ny posisjon utvidar den tilstøytande regionen (1.22).}
\prop{4.4}{o}{Morfologisk endringsrate manifesterer ei trappefunksjon (avbrote likevekt): lange periodar med stase avbrote av episodisk radiasjon.}
\prop{4.41}{t}{Stasen opphøyrer når eit lokalt maksimum kollapsar under trykkendringar (4.11), noko som tvingar fram ei valdsam vandring mot nyleg opna regionar.}
\prop{4.5}{o}{Materialstraumar er ein radikal vektor for landskapsdeformasjon.}
\prop{4.51}{i}{Introduksjonen av eit nytt substrat slettar momentant eksisterande attraktorar. Mahogni-kollapsen (1825-1849) utgjorde ei slik massiv sletting av gamle gradientar, etterfylgd av låsing i nye kanalar.}
\clearpage
\addcontentsline{toc}{chapter}{5 Det finst agentar som responderer på landskapet}
\markboth{det finst agentar som responderer på\ldots}{}
\prop{5}{}{Det finst agentar som responderer på landskapet}
\prop{5.1}{a}{Transformasjon av posisjon i morforommet krev ein operator (agens).}
\prop{5.11}{d}{Ein agent er ein operator definert uttømande ved ei cybernetisk sløyfe: måling av avvik frå eit mål, og applikasjon av ei korrigerande transformasjon.}
\prop{5.12}{t}{Agens er substrat-uavhengig. Definisjonen krev korkje eit biologisk nervesystem, menneskeleg medvit eller intensjon.}
\prop{5.13}{t}{Grensa mellom agent og ikkje-agent går strengt ved informasjonsflyt. Ein flod som eroderer har inga tilbakekopling og er ingen agent; ein planaria som regenererer, er det.}
\prop{5.14}{d}{Formgjevar er heretter definert strengt synonymt med agent. Materialet, den handlande kroppen og algoritmen er alle formgjevarar.}
\prop{5.2}{d}{Den kognitive lyskjegla er den delmengda av morforommet agenten har algoritmisk oppløysing til å representere og transformere.}
\prop{5.21}{t}{Det som ligg utanfor lyskjegla, er for agenten kausalt utilgjengeleg og logisk ueksisterande.}
\prop{5.22}{o}{Agentar skil seg empirisk i volumet og oppløysinga på si lyskjegle. Agens er stratifisert:}
\par\addvspace{4pt}\begin{widebody}\noindent\centerline{%
  \includegraphics[width=\linewidth]{fig-5.23-agentar.pdf}}\end{widebody}
\par\addvspace{2pt}
\prop{5.3}{d}{Fem formelle operasjonar modifiserer agentens lyskjegle:}
\par\addvspace{4pt}\begin{widebody}\noindent\centerline{%
  \includegraphics[width=\linewidth]{fig-5.44-lyskjegle.pdf}}\end{widebody}
\par\addvspace{2pt}
\prop{5.4}{t}{C-K-teorien er det proposisjonslogiske spesialtilfellet av navigasjon i lyskjegla. Design er den felles ekspansjonen av eit Kunnskapsrom (K) og eit Konseptrom (C).}
\prop{5.41}{d}{Eit konsept (C) er ein uavgjord proposisjon; korkje sann eller falsk i K. Kunnskap (K) er proposisjonar med etablert logisk status.}
\prop{5.42}{d}{Dei fire C-K-operatorane (C\msym{→}K, K\msym{→}C, C\msym{→}C, K\msym{→}K) svarar formelt til restriksjonar av dei fem lyskjegleoperasjonane:}
\par\addvspace{4pt}\begin{widebody}\noindent\centerline{%
  \includegraphics[width=\linewidth]{fig-5.45-ck.pdf}}\end{widebody}
\par\addvspace{2pt}
\prop{5.5}{t}{Læring er den temporale utvidinga av den kognitive lyskjegla. Læring, biologisk seleksjon og bayesiansk inferens er logisk isomorfe operasjonar realisert i ulike substrat; dei minskar alle avstanden mellom intern representasjon og eksternt landskap.}
\prop{5.6}{d}{Agenten transformerer forma utelukkande via matematisk innleiring (embedding) i notida.}
\prop{5.61}{t}{Konstruksjonshistoria manglar logisk verdi for operatoren. Geometrien er minnelaus.}
\prop{5.62}{i}{Reglane for innleiring og geometrisk transformasjon utførast via formgrammatikk:}
\par\addvspace{4pt}\begin{widebody}\noindent\centerline{%
  \includegraphics[width=\linewidth]{fig-5.62-grammatikk.pdf}}\end{widebody}
\par\addvspace{2pt}\noindent\centerline{%
  \includegraphics[width=0.78\linewidth]{shape_grammar_fig1.png}}
\par\addvspace{2pt}
\prop{5.7}{t}{Av 5.12 og 5.6 følgjer same underliggjande algebra: Ein planaria navigerer morforommet via bioelektriske gradientar. Ein handverkar navigerer morforommet via taktil tilbakemelding. Ein diffusjonsmodell navigerer eit latent rom via denoising. Substrata er ulike; den kybernetiske strukturen er identisk.}
\clearpage
\addcontentsline{toc}{chapter}{6 Forma oppstår mellom agentane}
\markboth{forma oppstår mellom agentane}{}
\prop{6}{}{Forma oppstår mellom agentane}
\prop{6.1}{t}{Av 2.3 og 5.1 følgjer: All form er eit poly-agentisk kompromiss. Ingen einskild agent utøver absolutt kontroll over posisjonen.}
\prop{6.11}{t}{Materialet fungerer som agenten av nullte-orden; eit tvingande anker som returnerer falsk for alle transformasjonar mot den forbodne regionen.}
\prop{6.2}{d}{Nisjekonstruksjon: Kvar transformasjon utført av éin agent, endrar landskapet for alle andre agentar i nettverket.}
\prop{6.21}{t}{Av 6.2 følgjer: Kvar aktualisert form fungerer formelt som økosystemingeniør ved å modifisere straumen av informasjon og materie.}
\prop{6.3}{t}{Kvar generasjon av formgjevarar etterlet eit modifisert tilpassingslandskap; eit fryst lag av fastlåste maskinar, standardar og verktøy. Dette utgjer den økologiske arven.}
\prop{6.4}{o}{Kommunikasjonen mellom agentar vert bestemd av bandbreidde og latens. Agentar med smale lyskjegler koplar seg saman for å auke si totale kognitive bandbreidde.}
\prop{6.41}{d}{Eit slikt tett kopla system fungerer som ein makro-agent. Tradisjon er ein makro-agent i stase; problemløysing utførast kollektivt strengt innanfor grensa av eit etablert Kunnskapsrom (K).}
\prop{6.5}{t}{Paradigmeskifte utløysast viss og berre viss akkumulerte anomaliar i landskapet tvingar makro-agenten til systemisk restrukturering, der K-rommet kollapsar og C-rommet må omkodast.}
\clearpage
\addcontentsline{toc}{chapter}{7 Ingen form er endeleg}
\markboth{ingen form er endeleg}{}
\prop{7}{}{Ingen form er endeleg}
\prop{7.1}{t}{Gitt landskapets evige deformasjon (4.11) og agentanes uopphøyrlege nisjekonstruksjon (6.2), er morfologisk flyktigheit logisk absolutt.}
\prop{7.11}{t}{Eit endeleg, stabilt kvilepunkt for form lèt seg logisk berre realisere i termodynamisk døds-likevekt.}
\prop{7.2}{t}{Kvar realisert form er utelukkande ei midlertidig løysing av eit sett med ulikskapar i eit ekspanderande rom. Ho er ein posisjon si eiga midlertidige kvile.}
\prop{7.3}{t}{Når seleksjonstrykka fluktuerer, vil kvar posisjon som er optimal ved tidspunkt \textit{t} ubønnhøyrleg forfalle til sub-optimalitet ved tidspunkt \textit{t+n}. Ingen telos er avslutta.}
\prop{7.4}{t}{Alt som kan skildrast presist om form, er uttømt gjennom posisjon, topologi og tid.}
\prop{7.5}{t}{Gyldigheita til dette formelle systemet er identisk med dets kapasitet til å generere empirisk falsifiserbare prediksjonar over morforommet. Sanning er tekstens evne til å falle.}
\prop{7.6}{t}{Det som ligg utanfor posisjonen -- formgjevarens intensjon, den indre kjensla av å skape, skjønnleiken og den estetiske verdien av tingen -- fell logisk utanfor formalgebraen.}
\prop{7.61}{t}{Om det som ligg utanfor morforommet, lyt formlæra teie.}

\appendix