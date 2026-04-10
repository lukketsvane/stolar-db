# -*- coding: utf-8 -*-
import sys

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Define boundaries for Chapter 1
start_marker = r"\prop{1}{}{Form er ein posisjon i eit rom av moglegheiter}"
end_marker = r"\clearpage" + "\n" + r"  \addcontentsline{toc}{chapter}{2 Ikkje alle posisjonar er like sannsynlege}"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('Markers not found!')
    sys.exit(1)

new_chapter_1 = r"""\prop{1}{}{Form er ein posisjon i eit rom av moglegheiter}
\prop{1.1}{a}{Alt som eksisterer materielt med ein bestemt funksjon, inntar éin eksakt formell konfigurasjon.}
\prop{1.11}{t}{Av 1.1: At eit objekt inntar nettopp denne konfigurasjonen, når uendeleg mange andre logisk sett var moglege, krev ei årsaksforklaring.}
\prop{1.12}{t}{Forklaringa kan ikkje liggje i forma sjølv, men i tilhøvet mellom den realiserte konfigurasjonen og det totale settet av posisjonar som ikkje er aktualiserte.}
\prop{1.2}{d}{Morforommet er den logiske mengda av alle moglege konfigurasjonar for ein gjeven funksjonell klasse.\footnote{Raup (1966); Mitteroecker \& Huttegger (2009)}}
\prop{1.21}{t}{Kvar realisert form utgjer eitt diskret koordinat i dette formrommet.}
\prop{1.22}{t}{Forma er soleis uttømande definert av sin posisjon relativt til resten av rommet.}
\prop{1.3}{d}{Morforommet er topologisk inndelt i tre disjunkte regionar: den aktualiserte, den tilstøytande og den forbodne.}
\prop{1.31}{d}{Den aktualiserte regionen er mengda av instansierte posisjonar. Dette utgjer det historiske arkivet; fundamentet for all vidare formgjeving.}
\prop{1.32}{d}{Den tilstøytande regionen er mengda av uaktualiserte posisjonar som teoretisk kan nåast med éin logisk operasjon frå den aktualiserte.}
\prop{1.33}{d}{Den forbodne regionen er lukka av fysikkens aksiom eller teknologiske avgrensingar ved eit gjeve tidspunkt.}
\prop{1.4}{o}{Kvar empirisk måling av fysisk form utgjer ein dimensjonsreduserande projeksjon. Valet av matematiske aksar avgjer kva topologiske grenser som er synlege.\footnote{Thompson (1917)}}
\prop{1.41}{t}{Av 1.4: Inga endeleg mengd variablar i ein projeksjon kan fange den latente kompleksiteten i den fysiske forma fullt ut.}
\prop{1.5}{t}{Morforommet er absolutt substrat-uavhengig. Den eksakt same matematiske posisjonen kan instansierast i tre av ein handverkar, i stål av ein maskin, eller i eit latent rom av ein algoritme.}
\prop{1.6}{o}{Observasjon av det empiriske formrommet syner at det ikkje er uniformt busett. Formene samlar seg i tette klynger med store tomrom mellom seg.}
\prop{1.61}{t}{Av 1.6: Denne ikkje-uniforme fordelinga provar logisk at det lyt eksistere kausale mekanismar som favoriserer nokre posisjonar over andre (sjå Kapittel 2).}

"""

final_content = content[:start_idx] + new_chapter_1 + content[end_idx:]

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Chapter 1 rewritten perfectly.")