# -*- coding: utf-8 -*-
import sys
import re

def fix_unicode(text):
    return text.replace('Ã¥', 'å').replace('Ã¦', 'æ').replace('Ã¸', 'ø').replace('Ã©', 'é') \
               .replace('Ã\x85', 'Å').replace('Ã\x86', 'Æ').replace('Ã\x98', 'Ø')

with open('old_clean.tex', 'r', encoding='utf-8') as f:
    content = f.read()

content = fix_unicode(content)

# 1. Preamble adjustments
content = content.replace(r"\renewcommand{\footrulewidth}{0.4pt}", r"\renewcommand{\footrulewidth}{0pt}")
content = content.replace(r"\fancyfootoffset[L]{16mm}", "")

# 2. Footnote rule - keep invisible
content = re.sub(r"\\renewcommand{\\footnoterule}\{.*?\}", r"\\renewcommand{\\footnoterule}{}", content, flags=re.DOTALL)

# 3. Chapter 1 - "Posisjon" instead of "Konfigurasjon"
new_chapter_1 = r"""\addcontentsline{toc}{chapter}{1 Formverda er alt som er tilfelle}
\markboth{formverda er alt som er tilfelle\ldots}{}
\prop{1}{}{Formverda er alt som er tilfelle.}
\prop{1.1}{o}{Formverda er totaliteten av realiserte posisjonar, ikkje av ting.}
\prop{1.11}{t}{Alt som har form, har nettopp denne forma og ikkje ei anna.}
\prop{1.12}{t}{At ein posisjon tek ein eksakt form, når uendeleg mange andre var logisk moglege, krev ei årsaksforklaring utover posisjonen sjølv.}
\prop{1.13}{t}{Forklaringa ligg i relasjonen mellom den manifesterte posisjonen og det totale settet av posisjonar som var moglege, men ikkje vart realiserte.}
\prop{1.2}{d}{Eit \textbf{objekt} er den enklaste bestanddelen i ein form. Objektet er udeleleg og uforanderleg. Det utgjer formverdas substans.}
\prop{1.21}{d}{Ein \textbf{posisjon} er ein bestemt samanheng av objekt. Forma er posisjonens struktur.}
\prop{1.22}{t}{Sidan objektas natur inneber moglegheita for å inngå i posisjonar, er alle moglege former allereie gjeve i og med objekta.}
\prop{1.3}{d}{\textbf{Formrommet} (\textit{morphospace}) til ein klasse er mengda av alle moglege posisjonar for objekt i denne klassen.\footnote{Raup (1966); Mitteroecker \& Huttegger (2009)}}
\prop{1.31}{d}{Kvart realisert objekt utgjer eitt eksakt punkt i dette n-dimensjonale rommet.}
\prop{1.32}{d}{Det empiriske formrommet er always ein projeksjon. Inga endeleg mengd parametrar fangar den latente kompleksiteten fullt ut.\footnote{Thompson (1917)}}
\prop{1.4}{d}{Formrommet deler seg topologisk i tre regionar: dei busette, dei opne og dei forbodne.}
\prop{1.41}{o}{Dei busette regionane utgjer det historiske arkivet. Dei fungerer som ankerpunkt for all framtidig navigasjon og utgjer den induktive premissen for vidare form.}
\prop{1.42}{o}{Dei opne regionane utgjer det \textit{tilstøytande moglege}. Dei er teoretisk tilgjengelege, men uaktualiserte.}"""

content = re.sub(r"\\addcontentsline\{toc\}\{chapter\}\{1 .*?\}(?=\\clearpage\s+\\addcontentsline\{toc\}\{chapter\}\{2)", new_chapter_1, content, flags=re.DOTALL)

# 4. Update 5.61-5.64
new_561_564 = r"""\prop{5.61}{d}{Ein formalgebra $U$ er matematisk basert på dimensjonen til dei tilgjengelege grunnleggjande elementa: $U_0$ (punkt), $U_1$ (linjer), $U_2$ (plan), og $U_3$ (solidar og volum). Desse algebraene fungerer som boolske ringar, lukkast over alle euklidiske transformasjonar.}
\prop{5.62}{d}{Ein operativ formgrammatikk definerast utelukkande som eit 4-tuppel $G = (V, M, R, I)$ der $V$ utgjer settet av terminale former, $M$ er temporære markørar, $R$ er eit avgrensa sett reglar ($a \to b$), og $I$ er den tvingande initialforma.}
\prop{5.63}{t}{Reglane opererer reint romleg og utelukkande i kraft av relasjonen innleiring ($\le$). Viss venstre side av ein regel ($a$) matematisk kan finnast (innleirast) i ei eksisterande form gjennom euklidiske transformasjonar $f$ (translokasjon, rotasjon, proporsjonal skalering), tillatast den spesifikke delen av forma erstatta med høgre side ($b$).}
\prop{5.64}{d}{Formgrammatikken representerer det logiske moglegheitsrommet i sin totalitet. Berre den umiddelbare, noverande geometrien til forma avgjer suverent kva reglar som kan fyre. Konstruksjonshistoria er totalt logisk irrelevant; systemet har inga minne utover formens eigne, fysiske koordinatar i notida. Grammatikken spesifiserer kva som logisk let seg gjere, medan landskapet og seleksjonstrykka avgjer kva operasjonar agenten i realiteten oppfyller.}"""

content = re.sub(r"\\prop\{5\.61\}\{d\}.*?\\prop\{5\.64\}\{d\}\{.*?\}", new_561_564, content, flags=re.DOTALL)

# 5. Fix images - remove widebody and centerline, use linewidth
content = re.sub(r"\\begin\{widebody\}\s*\\noindent\\centerline\{%?\s*\\includegraphics\[width=\\linewidth\]\{([^}]+)\}\}\s*\\end\{widebody\}", r"\\par\\addvspace{4pt}\\noindent\\includegraphics[width=\\linewidth]{\1}\\par\\addvspace{2pt}", content)
content = re.sub(r"\\noindent\\centerline\{%?\s*\\includegraphics\[width=\\linewidth\]\{([^}]+)\}\}", r"\\par\\addvspace{2pt}\\noindent\\includegraphics[width=\\linewidth]{\1}\\par\\addvspace{2pt}", content)

# 6. Apply styles to other key terms
content = content.replace("Eit seleksjonstrykk er", "Eit \\textbf{seleksjonstrykk} er")
content = content.replace("Materialaffordansen er", "\\textbf{Materialaffordansen} er")
content = content.replace("Tilpassingslandskapet er", "\\textbf{Tilpassingslandskapet} er")
content = content.replace("Ein stil er", "Ein \\textbf{stil} er")
content = content.replace("Ein agent er ein operator", "Ein \\textbf{agent} er ein operator")
content = content.replace("Den kognitive lyskjegla er", "Den \\textbf{kognitive lyskjegla} er")
content = content.replace("Nisjekonstruksjon:", "\\textbf{Nisjekonstruksjon}:")

# 7. Add footnotes to susequent chapters
replacements_fn = {
    "Sannsynlegheitsfordelinga for formgenerering er isomorf med ein ergodisk Markoff-prosess.": "Sannsynlegheitsfordelinga for formgenerering er isomorf med ein ergodisk Markoff-prosess.\\footnote{Shannon (1948)}",
    "Kvar realisert form er eit kompromiss. Eit kompromiss er ikkje ein svakheit; det er den einaste moglege balansen under dei vilkåra som rådde.": "Kvar realisert form er eit kompromiss. Eit kompromiss er ikkje ein svakheit; det er den einaste moglege balansen under dei vilkåra som rådde.\\footnote{Michl (1995)}",
    "ein eksplosiv radiasjon inn i ein nyopna region, fylgd av gradvis konvergens mot nye attraktorar.": "ein eksplosiv radiasjon inn i ein nyopna region, fylgd av gradvis konvergens mot nye attraktorar.\\footnote{Eldredge \& Gould (1972)}",
    "All formgjeving er omformgjeving: agenten startar aldri frå ein tom posisjon.": "All formgjeving er omformgjeving: agenten startar aldri frå ein tom posisjon.\\footnote{Arthur (1994)}",
    "Eit system som ikkje treng å vite kva det er laga av for å navigere mot eit mål, er ein agent uavhengig av kva det er laga av.": "Eit system som ikkje treng å vite kva det er laga av for å navigere mot eit mål, er ein agent uavhengig av kva det er laga av.\\footnote{Rosenblueth, Wiener \& Bigelow (1943)}",
    "Ein flod som eroderer er ikkje ein agent; ein planaria som regenererer er det.": "Ein flod som eroderer er ikkje ein agent; ein planaria som regenererer er det.\\footnote{Wiener (1948); Turing (1950)}",
    "Det som ligg utanfor lyskjegla, er kausalt utilgjengeleg.": "Det som ligg utanfor lyskjegla, er kausalt utilgjengeleg.\\footnote{Fields \& Levin (2022)}",
    "Dei fire fundamentale operatorane for navigasjon mellom desse domena svarar til spesifikke restriksjonar av lyskjegleoperasjonane:": "Dei fire fundamentale operatorane for navigasjon mellom desse domena svarar til spesifikke restriksjonar av lyskjegleoperasjonane:\\footnote{Hatchuel \& Weil (2003, 2009)}",
    "Substrata er ulike; strukturen er identisk.": "Substrata er ulike; strukturen er identisk.\\footnote{Levin (2022, 2025)}",
    "Ingen einskild agent dikterer den resulterande morfologien; ho emergerer i skjeringspunktet mellom dei, som ein posisjon ingen del kunne ha navigert mot åleine.": "Ingen einskild agent dikterer den resulterande morfologien; ho emergerer i skjeringspunktet mellom dei, som ein posisjon ingen del kunne ha navigert mot åleine.\\footnote{Odling-Smee, Laland \& Feldman (2003)}",
    "vert heilskapen sjølv ein agent etter definisjonen i 5.2.": "vert heilskapen sjølv ein agent etter definisjonen i 5.2.\\footnote{Kuhn (1962)}",
    "Det moglege veks med det realiserte.": "Det moglege veks med det realiserte.\\footnote{Kauffman (1993)}",
}

for old, new in replacements_fn.items():
    content = content.replace(old, new)

content = content.replace("always", "alltid")

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(content)

print("Rebuild complete.")
