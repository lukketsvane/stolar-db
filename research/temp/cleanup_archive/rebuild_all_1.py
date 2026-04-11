# -*- coding: utf-8 -*-
import sys
import re

with open('old_clean.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix unicode characters
content = content.replace('Ã¥', 'å').replace('Ã¦', 'æ').replace('Ã¸', 'ø').replace('Ã©', 'é')
content = content.replace('Ã\x85', 'Å').replace('Ã\x86', 'Æ').replace('Ã\x98', 'Ø')

# 1. Clean up inline citations in the ordliste
content = content.replace(r"(Gibson, 1979)", r"\footnote{Gibson (1979)}")
content = content.replace(r"(Waddington, 1957)", r"\footnote{Waddington (1957)}")

# Replace specific substrings to add footnotes accurately 
replacements_substr = {
    r"kvar konfigurasjon utgjer eit punkt i eit formelt forløp.}": r"kvar konfigurasjon utgjer eit punkt i eit formelt forløp.\footnote{Kubler (1962)}}",
    r"form følgjer form.}": r"form følgjer form.\footnote{Michl (1995)}}",
    r"Dei samlar seg i klynger med store tomrom mellom seg.}": r"Dei samlar seg i klynger med store tomrom mellom seg.\footnote{Raup (1966)}}",
    r"Sannsynlegheitsfordelinga for formgenerering er isomorf med ein ergodisk Markoff-prosess.}": r"Sannsynlegheitsfordelinga for formgenerering er isomorf med ein ergodisk Markoff-prosess.\footnote{Shannon (1948)}}",
    r"Kvar realisert form er eit kompromiss. Eit kompromiss er ikkje ein svakheit; det er den einaste moglege balansen under dei vilkåra som rådde.}": r"Kvar realisert form er eit kompromiss. Eit kompromiss er ikkje ein svakheit; det er den einaste moglege balansen under dei vilkåra som rådde.\footnote{Michl (1995)}}",
    r"Signaturen er probabilistisk: repertoaret bind sannsynsfordelinga, ikkje det einskilde objektet.}": r"Signaturen er probabilistisk: repertoaret bind sannsynsfordelinga, ikkje det einskilde objektet.\footnote{Gibson (1979)}}",
    r"Tilpassingslandskapet er den aggregerte verknaden av alle samtidige seleksjonstrykk over formrommet.": r"Tilpassingslandskapet er den aggregerte verknaden av alle samtidige seleksjonstrykk over formrommet.\footnote{Wright (1932)}",
    r"Bratte veggar tyder kanalisering: forma er robust mot forstyrringar, slik eit embryo er robust mot genetisk variasjon.": r"Bratte veggar tyder kanalisering: forma er robust mot forstyrringar, slik eit embryo er robust mot genetisk variasjon.\footnote{Waddington (1957)}",
    r"At ein stil er ei klynge, ikkje ein kategori, forklarer kvifor stilar har uskarpe grenser": r"At ein stil er ei klynge, ikkje ein kategori, forklarer kvifor stilar har uskarpe grenser\footnote{Kubler (1962)}",
    r"ein eksplosiv radiasjon inn i ein nyopna region, fylgd av gradvis konvergens mot nye attraktorar.}": r"ein eksplosiv radiasjon inn i ein nyopna region, fylgd av gradvis konvergens mot nye attraktorar.\footnote{Eldredge \& Gould (1972)}}",
    r"All formgjeving er omformgjeving: agenten startar aldri frå ein tom posisjon.}": r"All formgjeving er omformgjeving: agenten startar aldri frå ein tom posisjon.\footnote{Arthur (1994)}}",
    r"Eit system som ikkje treng å vite kva det er laga av for å navigere mot eit mål, er ein agent uavhengig av kva det er laga av.}": r"Eit system som ikkje treng å vite kva det er laga av for å navigere mot eit mål, er ein agent uavhengig av kva det er laga av.\footnote{Rosenblueth, Wiener \& Bigelow (1943)}}",
    r"Ein flod som eroderer er ikkje ein agent; ein planaria som regenererer er det.}": r"Ein flod som eroderer er ikkje ein agent; ein planaria som regenererer er det.\footnote{Wiener (1948); Turing (1950)}}",
    r"Det som ligg utanfor lyskjegla, er kausalt utilgjengeleg.}": r"Det som ligg utanfor lyskjegla, er kausalt utilgjengeleg.\footnote{Fields \& Levin (2022)}}",
    r"Dei fire C-K-operatorane svarar til restriksjonar av lyskjegleoperasjonane:}": r"Dei fire C-K-operatorane svarar til restriksjonar av lyskjegleoperasjonane:\footnote{Hatchuel \& Weil (2003, 2009)}}",
    r"Kvar regel er definert under innleiring: ei delform kan identifiserast i den noverande forma uavhengig av korleis ho vart bygd. Reglane ser; dei hugsar ikkje.}": r"Kvar regel er definert under innleiring: ei delform kan identifiserast i den noverande forma uavhengig av korleis ho vart bygd. Reglane ser; dei hugsar ikkje.\footnote{Stiny \& Gips (1972)}}",
    r"Reglane transformerer former på fem måtar:}": r"Reglane transformerer former på fem måtar:\footnote{Stiny (1980, 1991, 2006)}}",
    r"Substrata er ulike; strukturen er identisk.}": r"Substrata er ulike; strukturen er identisk.\footnote{Levin (2022, 2025)}}",
    r"Ingen einskild agent dikterer den resulterande morfologien; ho emergerer i skjeringspunktet mellom dei, som ein posisjon ingen del kunne ha navigert mot åleine.}": r"Ingen einskild agent dikterer den resulterande morfologien; ho emergerer i skjeringspunktet mellom dei, som ein posisjon ingen del kunne ha navigert mot åleine.\footnote{Odling-Smee, Laland \& Feldman (2003)}}",
    r"Skiljet mellom ein aggregering av agentar og ein einskild agent er funksjonelt, ikkje ontologisk.}": r"Skiljet mellom ein aggregering av agentar og ein einskild agent er funksjonelt, ikkje ontologisk.\footnote{Kuhn (1962)}}",
    r"Nyhetsraten i formrommet er ein funksjon av det tilstøytande moglege: kvar realisert form opnar nye regionar av naboskapen som ikkje fanst før. Det moglege veks med det realiserte.}": r"Nyhetsraten i formrommet er ein funksjon av det tilstøytande moglege: kvar realisert form opnar nye regionar av naboskapen som ikkje fanst før. Det moglege veks med det realiserte.\footnote{Kauffman (1993)}}",
}

for old, new in replacements_substr.items():
    content = content.replace(old, new)

# Minor language fixes
content = content.replace("captures", "fangar")
content = content.replace("zoom", "rørsle") 

# Write intermediate content to apply block replacements
with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(content)
