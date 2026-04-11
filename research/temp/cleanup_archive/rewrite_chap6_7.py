# -*- coding: utf-8 -*-
import sys

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = r"\prop{6}{}{Forma oppstår mellom agentane}"
end_marker = r"\appendix"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('Markers not found!')
    sys.exit(1)

new_text = r"""\prop{6}{}{Forma oppstår mellom agentane}
\prop{6.1}{t}{Av 2.2 og 5.1 følgjer: Sidan meir enn eitt seleksjonstrykk alltid verkar, og sidan ulike agentar responderer på ulike trykk, er all form eit poly-agentisk kompromiss.\footnote{Odling-Smee, Laland \& Feldman (2003)}}
\prop{6.11}{o}{Materialaffordansen, den fysiske reiskapen og den menneskelege handverkaren utgjer uavhengige, interagerande agentar.}
\prop{6.12}{t}{Av 6.11: Ingen einskild agent utøver absolutt diktat over forma. Forma materialiserer seg i metastabile skjeringspunkt mellom overlappande lyskjegler.}
\prop{6.2}{d}{Nisjekonstruksjon: Kvar transformasjon utført av éin agent, endrar landskapet for alle andre agentar i nettverket.}
\prop{6.21}{t}{Av 6.2 følgjer: Kvar aktualisert form fungerer formelt som økosystemingeniør ved å fryse temporære val til materiell infrastruktur.}
\prop{6.3}{t}{Kvar generasjon av formgjevarar etterlet eit modifisert tilpassingslandskap; eit fryst lag av fastlåste maskinar og verktøy. Dette utgjer den økologiske arven.}
\prop{6.4}{o}{Kommunikasjonen mellom agentar vert bestemd av bandbreidde og latens.}
\prop{6.41}{t}{Agentar med smale lyskjegler kan kople seg saman for å auke si totale kognitive bandbreidde. Når samanbindinga er tilstrekkeleg tett til at heilskapen realiserer ein eigen cybernetisk syklus, vert heilskapen sjølv ein agent etter definisjonen i 5.11.\footnote{Kuhn (1962)}}
\prop{6.42}{d}{Ein slik tett kopla makro-agent manifesterer seg empirisk som ein tradisjon. I stase utfører tradisjonen problemløysing kollektivt, strengt innanfor grensa av eit etablert Kunnskapsrom (K).}
\prop{6.5}{t}{Paradigmeskifte utløysast viss og berre viss akkumulerte anomaliar i landskapet tvingar makro-agenten til systemisk restrukturering, der K-rommet kollapsar og C-rommet må omkodast.}
\prop{6.6}{t}{Av 1.32 og 6.2: Nyheitsraten i formrommet er ein funksjon av det tilstøytande moglege. Det moglege veks med det realiserte.\footnote{Kauffman (1993)}}
\clearpage
\addcontentsline{toc}{chapter}{7 Ingen form er endeleg}
\markboth{ingen form er endeleg}{}
\prop{7}{}{Ingen form er endeleg}
\prop{7.1}{t}{Gitt landskapets evige deformasjon (4.11) og agentanes uopphøyrlege nisjekonstruksjon (6.2), er morfologisk flyktigheit logisk absolutt.}
\prop{7.11}{t}{Av 7.1: Eit endeleg, stabilt kvilepunkt for form lèt seg logisk berre realisere i termodynamisk døds-likevekt.}
\prop{7.2}{t}{Kvar realisert form er utelukkande ei midlertidig løysing av eit sett med ulikskapar i eit ekspanderande rom. Forma er ein posisjon si eiga midlertidige kvile.}
\prop{7.3}{t}{Når seleksjonstrykka fluktuerer, vil kvar posisjon som var optimal ved tidspunkt \textit{t} ubønnhøyrleg forfalle til sub-optimalitet ved tidspunkt \textit{t+n}. Ingen telos er avslutta.}
\prop{7.4}{t}{Alt som presist og etterprøvbart kan skildrast om form, er uttømt gjennom posisjon, topologi og tid.}
\prop{7.5}{t}{Gyldigheita til dette formelle systemet er identisk med dets kapasitet til å generere empirisk falsifiserbare prediksjonar over morforommet. Sanning er tekstens evne til å falle.}
\prop{7.6}{t}{Det som ligg utanfor posisjonen -- formgjevarens intensjon, den indre kognitive opplevinga av å skape, skjønnleiken og den estetiske verdien av tingen -- fell logisk utanfor formalgebraen.}
\prop{7.61}{t}{Om det som ligg utanfor morforommet, lyt formlæra teie.}

"""

final_content = content[:start_idx] + new_text + content[end_idx:]

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Chapter 6 and 7 rewritten successfully.")