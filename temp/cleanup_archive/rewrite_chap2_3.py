# -*- coding: utf-8 -*-
import sys

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = r"\prop{2}{}{Ikkje alle posisjonar er like sannsynlege}"
end_marker = r"\clearpage" + "\n" + r"  \addcontentsline{toc}{chapter}{4 Landskapet er dynamisk}"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('Markers not found!')
    sys.exit(1)

new_text = r"""\prop{2}{}{Ikkje alle posisjonar er like sannsynlege}
\prop{2.1}{a}{Den observerte asymmetrien i formrommet (1.6) krev ein dynamisk mekanikk; posisjonar inntreffer ikkje tilfeldig.}
\prop{2.11}{t}{Sannsynlegheitsfordelinga for formgenerering er isomorf med ein ergodisk Markoff-prosess; posisjonen er radikalt betinga av historia.\footnote{Shannon (1948)}}
\prop{2.2}{d}{Eit seleksjonstrykk er ein vektor som aukar eller minkar sannsynlegheita for aktualisering i ei gjeven region av morforommet.}
\prop{2.21}{t}{Av 2.2: Eit seleksjonstrykk åleine determinerer ikkje éin bestemt posisjon. Det opererer ved å utelukke posisjonar; form er det som vert att når trykka har utelukka det sub-optimale.}
\prop{2.3}{a}{Kvar posisjon i morforommet er samstundes underlagt eit sett av minst to uavhengige seleksjonstrykk.}
\prop{2.31}{o}{Vektorane frå ulike seleksjonstrykk (t.d. materialøkonomi versus ergonomi) er i regelen ortogonale eller i direkte algebraisk opposisjon.}
\prop{2.4}{t}{Av 2.3 og 2.31 følgjer: Det eksisterer inga form som maksimerer verdien for alle verksame seleksjonstrykk samstundes.}
\prop{2.41}{t}{Ergo er kvar realisert form logisk definert som eit formelt kompromiss.\footnote{Michl (1995)}}
\prop{2.42}{t}{Sidan eit kompromiss kan balanserast på meir enn éin måte, vil former under dei same vilkåra fordele seg kring distribuerte lokale jamvekter (sjå Kapittel 3).}
\prop{2.5}{t}{Hovudfunksjonen som definerer klassen (1.2) er konstant for alle gjenstandar i rommet. Det som er konstant har null varians og kan difor ikkje forklare morfologisk variasjon.}
\prop{2.6}{d}{Materialaffordansen fungerer som eit tvingande seleksjonstrykk. Det determinerer grensene for den forbodne regionen (1.33) ved å diktere kva operasjonar substratet tillèt.\footnote{Gibson (1979)}}
\prop{2.61}{o}{Signaturen til materialaffordansen er latent. Eit substrat kan vere til stades i hundreår før den formelle operasjonen som utnyttar det fullt ut, vert oppdaga.}
\prop{2.62}{t}{Av 2.61: Formhistoria er naudsynleg langsamare enn materialhistoria.}
\prop{2.7}{o}{Ein samlevariabel som er korrelert med alle samtidige trykk (t.d. «stilperiode»), absorberer kompromisset i éin etikett. Stilkategorien beskriv kvar kompromisset mellombels stansa, men har inga eigen kausal forklaringsevne.}
  \clearpage
  \addcontentsline{toc}{chapter}{3 Seleksjonstrykka produserer eit landskap over formrommet}
  \markboth{seleksjonstrykka produserer eit\ldots}{}
\prop{3}{}{Seleksjonstrykka produserer eit landskap over formrommet}
\prop{3.1}{d}{Tilpassingslandskapet er den aggregerte verknaden av alle samtidige seleksjonstrykk (2.2) over morforommet.\footnote{Wright (1932)}}
\prop{3.11}{t}{Av 3.1: Kvar posisjon i landskapet har ein topologisk høgdeverdi som svarar til kor robust kompromisset (2.41) på det koordinatet stettar dei samla trykka.}
\prop{3.2}{t}{Av 2.42 og 3.1: Tilpassingsfunksjonen har generisk fleire lokale maksima. Landskapet kjenneteiknast difor av å vere ruglete (multitopp).}
\prop{3.21}{t}{Eit lokalt maksimum fungerer matematisk som ein attraktor for formelle vandringar.}
\prop{3.22}{t}{For å forlate eit lokalt maksimum, må posisjonen vandre gjennom punkt med lågare høgd. Å endre konfigurasjon krev difor logisk eit mellombels adaptivt tap.}
\prop{3.3}{d}{Gradienten kring eit lokalt maksimum definerer graden av kanalisering. Bratte veggar tyder sterk kanalisering: formsekvensen er robust mot forstyrringar.\footnote{Waddington (1957)}}
\prop{3.31}{o}{Seleksjonstrykka er hierarkiske. Dei sterkaste trykka (t.d. gravitasjon) grev djupe kanalar der hovudproporsjonane er ekstremt robuste.}
\prop{3.4}{d}{Ein stil er den deskriptive nemninga på ei klynge av aktualiserte former kring den same attraktoren i landskapet.}
\prop{3.41}{t}{Av 3.4: Sidan landskapet er eit topologisk kontinuum, manglar stilar skarpe logiske grenser. Klassifikasjon med absolutte grenser er inkoherent.\footnote{Kubler (1962)}}
\prop{3.5}{t}{Seleksjon er ein operator for eliminasjon. Han skapar ingen posisjonar; han slettar utelukkande dei formene som fell for djupt ned i dalane.}
\prop{3.6}{o}{Konvergent formgjeving oppstår når uavhengige tradisjonar navigerer langs identiske gradientar mot den same attraktoren.}
"""

final_content = content[:start_idx] + new_text + content[end_idx:]

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Chapter 2 and 3 rewritten successfully.")