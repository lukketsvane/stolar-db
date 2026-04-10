# -*- coding: utf-8 -*-
import sys

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Define boundaries for Chapter 1
start_marker = r"\addcontentsline{toc}{chapter}{1 "
end_marker = r"\clearpage" + "\n" + r"\addcontentsline{toc}{chapter}{2 Ikkje alle posisjonar er like sannsynlege}"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('Markers not found! start_idx:', start_idx, 'end_idx:', end_idx)
    sys.exit(1)

new_chapter_1 = r"""\addcontentsline{toc}{chapter}{1 Formverda er alt som er tilfelle}
\markboth{formverda er alt som er tilfelle\ldots}{}
\prop{1}{}{Formverda er alt som er tilfelle.}
\prop{1.1}{o}{Formverda er totaliteten av realiserte konfigurasjonar, ikkje av ting.}
\prop{1.11}{t}{Alt som har form, har nettopp denne forma og ikkje ei anna.}
\prop{1.12}{t}{At ein konfigurasjon tek ein eksakt form, når uendeleg mange andre var logisk moglege, krev ei forklaring utover konfigurasjonen sjølv.}
\prop{1.13}{t}{Forklaringa ligg i relasjonen mellom den manifesterte konfigurasjonen og det totale settet av konfigurasjonar som var moglege, men ikkje vart realiserte.}
\prop{1.2}{d}{Eit objekt er den enklaste bestanddelen i ein form. Objektet er udeleleg og uforanderleg. Det utgjer formverdas substans.}
\prop{1.21}{d}{Ein konfigurasjon er ein bestemt samanheng av objekt. Forma er konfigurasjonens struktur.}
\prop{1.22}{t}{Sidan objektas natur inneber moglegheita for å inngå i konfigurasjonar, er alle moglege former allereie gjeve i og med objekta.}
\prop{1.3}{d}{Formrommet (morphospace) til ein klasse er mengda av alle moglege konfigurasjonar for objekt i denne klassen.\footnote{Raup (1966); Mitteroecker \& Huttegger (2009)}}
\prop{1.31}{d}{Kvart realisert objekt utgjer eitt eksakt punkt i dette n-dimensjonale rommet.}
\prop{1.32}{d}{Det empiriske formrommet er alltid ein projeksjon. Inga endeleg mengd parametrar fangar den latente kompleksiteten fullt ut.\footnote{Thompson (1917)}}
\prop{1.4}{d}{Formrommet deler seg topologisk i tre regionar: dei busette, dei opne og dei forbodne.}
\prop{1.41}{o}{Dei busette regionane utgjer det historiske arkivet. Dei fungerer som ankerpunkt for all framtidig navigasjon og utgjer den induktive premissen for vidare form.}
\prop{1.42}{o}{Dei opne regionane utgjer det tilstøytande moglege. Dei er teoretisk tilgjengelege, men uaktualiserte.}

"""

final_content = content[:start_idx] + new_chapter_1 + content[end_idx:]

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Chapter 1 rewritten perfectly to match Tractatus style.")