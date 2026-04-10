# -*- coding: utf-8 -*-
import sys

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Restore \prop definition and remove footer rule
preamble_fix = r"""\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\scshape\leftmark}  % chapter title at left on every page
\fancyhead[R]{\small\thepage}           % page number at right on every page
\fancyheadoffset[L]{16mm}               % extend header left over the number margin
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}      % Remove footer line
% plain style (chapter-opening pages): identical to fancy (full header).
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{\small\scshape\leftmark}
  \fancyhead[R]{\small\thepage}
  \fancyheadoffset[L]{16mm}
  \renewcommand{\headrulewidth}{0.4pt}
  \renewcommand{\footrulewidth}{0pt}
}
% title style — used ONLY on the title page: nothing in the header at all.
\fancypagestyle{titlepage}{
  \fancyhf{}
  \fancyheadoffset[L]{0pt}
  \renewcommand{\headrulewidth}{0pt}
  \renewcommand{\footrulewidth}{0pt}
}

% ... (omitting some parts for the replace) ...

\usepackage[bottom]{footmisc}
\usepackage{calc}
\newlength{\propnumwidth}
\setlength{\propnumwidth}{13mm}  % column reserved for the number itself
\newlength{\propnumgap}
\setlength{\propnumgap}{2mm}     % gap between number column and body text

% Footnote rule — invisible
\renewcommand{\footnoterule}{}

% ─── Proposition environment ──────────────────────────────────────────────

% \prop{num}{status}{body}
%   The number is placed in a left-aligned 13 mm box, then a 2 mm gap,
%   and the whole 15 mm slug is \llap'd into the LEFT margin so its right
%   edge sits flush against the text-block left edge. Body text starts at
%   the text margin and wraps there too — a perfect rectangle.
%   The number itself is rendered in a heavier weight so it stands out
%   against the regular body text.
\newcommand{\prop}[3]{%
  \par\addvspace{6pt}%
  \noindent\llap{\makebox[\propnumwidth][l]{\textbf{#1}\textsuperscript{\textit{#2}}}\hspace{\propnumgap}}%
  #3\par%
  \addvspace{2pt}%
}

% Continuation paragraph — plain paragraph at the body column (no number).
"""

# I will use a safer approach: direct replacement of blocks.
# Find the block from \usepackage{fancyhdr} to \newcommand{\propcont}

fancy_start = content.find(r"\usepackage{fancyhdr}")
propcont_start = content.find(r"\newcommand{\propcont}")

if fancy_start != -1 and propcont_start != -1:
    content = content[:fancy_start] + preamble_fix + content[propcont_start:]

# 2. Terminology change: Replace "konfigurasjon" with "posisjon" in Chapter 1
# And update 5.61-5.64

# Chapter 1 replacement
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
\prop{1.32}{d}{Det empiriske formrommet er alltid ein projeksjon. Inga endeleg mengd parametrar fangar den latente kompleksiteten fullt ut.\footnote{Thompson (1917)}}
\prop{1.4}{d}{Formrommet deler seg topologisk i tre regionar: dei busette, dei opne og dei forbodne.}
\prop{1.41}{o}{Dei busette regionane utgjer det historiske arkivet. Dei fungerer som ankerpunkt for all framtidig navigasjon og utgjer den induktive premissen for vidare form.}
\prop{1.42}{o}{Dei opne regionane utgjer det \textit{tilstøytande moglege}. Dei er teoretisk tilgjengelege, men uaktualiserte.}"""

chap1_start = content.find(r"\addcontentsline{toc}{chapter}{1 Formverda er alt som er tilfelle}")
chap2_start = content.find(r"\clearpage" + "\n" + r"\addcontentsline{toc}{chapter}{2 Ikkje alle posisjonar er like sannsynlege}")

if chap1_start != -1 and chap2_start != -1:
    content = content[:chap1_start] + new_chapter_1 + content[chap2_start:]

# Update 5.61-5.64
new_561_564 = r"""\prop{5.61}{d}{Ein formalgebra $U$ er matematisk basert på dimensjonen til dei tilgjengelege grunnleggjande elementa: $U_0$ (punkt), $U_1$ (linjer), $U_2$ (plan), og $U_3$ (solidar og volum). Desse algebraene fungerer som boolske ringar, lukkast over alle euklidiske transformasjonar.}
\prop{5.62}{d}{Ein operativ formgrammatikk definerast utelukkande som eit 4-tuppel $G = (V, M, R, I)$ der $V$ utgjer settet av terminale former, $M$ er temporære markørar, $R$ er eit avgrensa sett reglar ($a \to b$), og $I$ er den tvingande initialforma.}
\prop{5.63}{t}{Reglane opererer reint romleg og utelukkande gjennom relasjonen innleiring ($\le$). Viss venstre side av ein regel ($a$) matematisk kan finnast (innleirast) i ei eksisterande form gjennom euklidiske transformasjonar $f$ (translokasjon, rotasjon, proporsjonal skalering), tillatast den spesifikke delen av forma erstatta med høgre side ($b$).}
\prop{5.64}{d}{Formgrammatikken representerer det logiske moglegheitsrommet i sin totalitet. Berre den umiddelbare, noverande geometrien til forma avgjer suverent kva reglar som kan fyre. Konstruksjonshistoria er totalt logisk irrelevant; systemet har inga minne utover formens eigne, fysiske koordinatar i notida. Grammatikken spesifiserer kva som logisk let seg gjere, medan landskapet og seleksjonstrykka avgjer kva operasjonar agenten i realiteten oppfyller.}"""

# Find where the old 5.61 started
p561_start = content.find(r"\prop{5.61}{d}")
# Find where 5.65 starts (to mark the end of the block)
p565_start = content.find(r"\prop{5.65}{t}")

if p561_start != -1 and p565_start != -1:
    content = content[:p561_start] + new_561_564 + "\n" + content[p565_start:]

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(content)

print("Preamble restored, footer removed, terminology and 5.61-5.64 updated.")
