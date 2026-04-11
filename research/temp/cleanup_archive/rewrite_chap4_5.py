# -*- coding: utf-8 -*-
import sys

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = r"\prop{4}{}{Landskapet er dynamisk}"
end_marker = r"\clearpage" + "\n" + r"  \addcontentsline{toc}{chapter}{6 Forma oppstår mellom agentane}"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('Markers not found!')
    sys.exit(1)

new_text = r"""\prop{4}{}{Landskapet er dynamisk}
\prop{4.1}{a}{Dei underliggjande variablane som genererer seleksjonstrykka (t.d. teknologi, tilgang på ressursar) fluktuerer over tid.}
\prop{4.11}{t}{Av 3.1 og 4.1 følgjer at landskapet er ein dynamisk flate. Posisjonane for lokale maksima forskyv seg, oppstår og kollapsar.}
\prop{4.2}{t}{Landskapet besitt eit materielt minne. Aktualiseringa av ein posisjon ved tidspunkt \textit{t} endrar uavvikeleg seleksjonsvektorane for tidspunkt \textit{t+1}.\footnote{Arthur (1994)}}
\prop{4.21}{t}{Av 4.2 følgjer at form følgjer form. Den eksisterande forma endrar infrastrukturen, verktøya og forventningane for den neste.}
\prop{4.3}{t}{Av 1.32 og 4.21: Det moglege ekspanderer rekurrerande. Kvar ny aktualisert posisjon opnar eit nytt tilstøytande rom.}
\prop{4.4}{o}{Morfologisk endringsrate manifesterer ei trappefunksjon (avbrote likevekt): lange periodar med stase vert avbrotne av episodisk radiasjon.\footnote{Eldredge \& Gould (1972)}}
\prop{4.41}{t}{Stasen opphøyrer når eit lokalt maksimum kollapsar under trykkendringar (4.11), noko som tvingar fram ei valdsam vandring mot nyleg opna regionar.}
\prop{4.5}{o}{Materialstraumar utgjer ein radikal vektor for landskapsdeformasjon.}
\prop{4.51}{i}{Introduksjon av eit nytt substrat kan momentant slette eksisterande attraktorar. Mahogni-kollapsen utgjorde ei slik sletting av gamle gradientar, etterfølgt av låsing i nye kanalar.}
\prop{4.6}{t}{Når eitt enkelt seleksjonstrykk vert dominant, kollapsar landskapet mot éin global attraktor. Forma misser sin fridom og vert reint determinert.}
  \clearpage
  \addcontentsline{toc}{chapter}{5 Det finst agentar som responderer på landskapet}
  \markboth{det finst agentar som responderer på\ldots}{}
\prop{5}{}{Det finst agentar som responderer på landskapet}
\prop{5.1}{a}{For at transformasjon av posisjon i morforommet skal skje, krevst ein operator (agens).}
\prop{5.11}{d}{Ein agent er ein operator definert uttømande ved si cybernetiske sløyfe: måling av avvik frå eit mål, og applikasjon av ei korrigerande transformasjon.\footnote{Rosenblueth, Wiener \& Bigelow (1943)}}
\prop{5.12}{t}{Agens er absolutt substrat-uavhengig. Definisjonen krev korkje eit biologisk nervesystem, menneskeleg medvit eller intensjon.\footnote{Wiener (1948); Turing (1950)}}
\prop{5.13}{t}{Grensa mellom agent og ikkje-agent går strengt ved informasjonsflyt og tilbakekopling. Ein flod som eroderer har inga tilbakekopling og er ingen agent; ein planaria som regenererer form, er det.}
\prop{5.14}{d}{"Formgjevar" er heretter definert strengt synonymt med agent. Materialet, den handlande kroppen og algoritmen er alle formgjevarar.}
\prop{5.2}{d}{Den kognitive lyskjegla er den delmengda av morforommet agenten har algoritmisk oppløysing til å representere og transformere.\footnote{Fields \& Levin (2022)}}
\prop{5.21}{t}{Det som ligg utanfor lyskjegla, er for agenten kausalt utilgjengeleg og logisk ueksisterande.}
\prop{5.22}{o}{Agentar skil seg empirisk utelukkande i volumet og oppløysinga på si lyskjegle. Agens er stratifisert:}
\par\addvspace{4pt}\begin{widebody}\noindent\centerline{%
  \includegraphics[width=\linewidth]{fig-5.23-agentar.pdf}}\end{widebody}
\par\addvspace{2pt}
\prop{5.3}{d}{Fem formelle operasjonar modifiserer agentens lyskjegle:}
\par\addvspace{4pt}\begin{widebody}\noindent\centerline{%
  \includegraphics[width=\linewidth]{fig-5.44-lyskjegle.pdf}}\end{widebody}
\par\addvspace{2pt}
\prop{5.4}{t}{C-K-teorien er eit proposisjonslogisk spesialtilfelle av navigasjon i lyskjegla. Design er den felles ekspansjonen av eit Kunnskapsrom (K) og eit Konseptrom (C).\footnote{Hatchuel \& Weil (2003, 2009)}}
\prop{5.41}{d}{Eit konsept (C) er ein uavgjord proposisjon; korkje sann eller falsk i K. Kunnskap (K) er proposisjonar med etablert logisk status.}
\prop{5.42}{t}{Dei fire C-K-operatorane svarar direkte til restriksjonar av dei fem lyskjegleoperasjonane:}
\par\addvspace{4pt}\begin{widebody}\noindent\centerline{%
  \includegraphics[width=\linewidth]{fig-5.45-ck.pdf}}\end{widebody}
\par\addvspace{2pt}
\prop{5.5}{t}{Læring er den temporale utvidinga av agentens lyskjegle. Læring, biologisk seleksjon og bayesiansk inferens er isomorfe operasjonar realiserte i ulike substrat; dei reduserer alle avstanden mellom intern modell og eksternt landskap.}
\prop{5.6}{d}{Agenten transformerer forma si utelukkande via matematisk innleiring (embedding) i notida.\footnote{Stiny \& Gips (1972)}}
\prop{5.61}{t}{Konstruksjonshistoria manglar logisk verdi for operatoren. Geometrien er minnelaus.}
\prop{5.62}{i}{Reglane for innleiring og geometrisk transformasjon utførast via formgrammatikk:\footnote{Stiny (1980, 1991, 2006)}}
\par\addvspace{4pt}\begin{widebody}\noindent\centerline{%
  \includegraphics[width=\linewidth]{fig-5.62-grammatikk.pdf}}\end{widebody}
\par\addvspace{2pt}\noindent\centerline{%
  \includegraphics[width=0.78\linewidth]{shape_grammar_fig1.png}}
\par\addvspace{2pt}
\prop{5.63}{t}{Av 5.6 og 5.61: Berre den noverande geometrien avgjer kva reglar som i det heile kan fyre. Forma determinerer sine eigne umiddelbare moglegheiter.}
\prop{5.7}{t}{Av 5.12 og 5.6 følgjer same underliggjande algebra for all formgjeving: Ein planaria navigerer morforommet via bioelektriske gradientar. Ein handverkar navigerer morforommet via taktil tilbakemelding. Ein diffusjonsmodell navigerer eit latent rom via denoising. Substrata er radikalt ulike; den cybernetiske strukturen er identisk.\footnote{Levin (2022, 2025)}}
"""

final_content = content[:start_idx] + new_text + content[end_idx:]

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Chapter 4 and 5 rewritten successfully.")