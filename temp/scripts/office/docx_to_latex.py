#!/usr/bin/env python3
"""
Convert FORMLÆRE_latest.docx to LaTeX, then compile to a print-ready PDF
that mirrors the digibok layout (Norwegian Tractatus translation, Gyldendal
1999, page format ~125 × 200 mm with hanging-indent propositions).

The script walks the docx paragraph-by-paragraph, classifies each one
(title / heading / proposition / appendix / caption / image / body / TOC)
and emits LaTeX accordingly. Then runs xelatex to produce FORMLÆRE.pdf.

Run:
  python scripts/office/docx_to_latex.py
  python scripts/office/docx_to_latex.py --no-compile     # tex only
"""
from __future__ import annotations
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[3]  # script lives in temp/scripts/office/
DOCX = ROOT / 'FORMLÆRE.docx'
TEX = ROOT / 'FORMLÆRE.tex'
PDF = ROOT / 'FORMLÆRE.pdf'
FIG_DIR = ROOT / 'analysis' / 'figures'
BUILD_DIR = ROOT / 'build_latex'


# ── LaTeX preamble ────────────────────────────────────────────────────────────

PREAMBLE = r"""\documentclass[10pt,oneside]{book}

% Page geometry — 125 × 200 mm (Gyldendal 1999 Tractatus format).
% Wide LEFT margin holds the proposition numbers (marginal numbering style):
% numbers are \llap'd into this margin so the body text block is a clean
% rectangle with all lines (including continuation) flush left at the body
% column. Right margin is narrow (no marginalia on the right).
% Top includes the running header band; footskip minimal (no footer text).
\usepackage[
  paperwidth=125mm,
  paperheight=200mm,
  top=20mm,
  bottom=18mm,
  left=28mm,
  right=12mm,
  headheight=12pt,
  headsep=6mm,
  footskip=8mm,
]{geometry}

% UTF-8 + Norwegian (nynorsk)
\usepackage{fontspec}
\usepackage{polyglossia}
\setdefaultlanguage[variant=nynorsk]{norwegian}

% Body font — the digibok is set in Sabon. EB Garamond is the closest
% free serif with the same general feel; fall back to TeX Gyre Pagella.
\IfFontExistsTF{EB Garamond}{
  \setmainfont{EB Garamond}[
    Numbers={Lining,Proportional},
    SmallCapsFeatures={LetterSpace=4},
  ]
}{
  \setmainfont{TeX Gyre Pagella}
}
% Body size 10.5 pt on 12.5 pt leading (close to Sabon 10.5/12 in the digibok)
\renewcommand{\normalsize}{\fontsize{10.5}{12.5}\selectfont}
\normalsize

% Better line breaking (must be loaded after font setup)
\usepackage{microtype}

% Math-symbol fallback font — EB Garamond lacks ∀ ∃ ∈ ⊆ ⊃ ≠ etc.,
% so the Python preprocessor wraps them in \msym{...} which uses
% Cambria Math (always present on Windows).
\newfontfamily{\mathfbfont}{Cambria Math}[Scale=0.95]
\newcommand{\msym}[1]{{\mathfbfont #1}}

% Headings — small caps, centred, generous spacing
\usepackage{titlesec}
\titleformat{\chapter}[block]
  {\normalfont\centering\scshape\addfontfeature{LetterSpace=10}\large}
  {}{0em}{\MakeLowercase}
\titlespacing*{\chapter}{0pt}{2.5em}{2.5em}

\titleformat{\section}[block]
  {\normalfont\centering\scshape\addfontfeature{LetterSpace=6}\normalsize}
  {}{0em}{\MakeLowercase}
\titlespacing*{\section}{0pt}{2.5em}{1.5em}

\titleformat{\subsection}[block]
  {\normalfont\scshape\addfontfeature{LetterSpace=2}\small}
  {}{0em}{\MakeLowercase}
\titlespacing*{\subsection}{0pt}{1.5em}{0.8em}

% Hide chapter numbers (chapters are titled by name)
\renewcommand{\thechapter}{}

% Running headers — chapter title at left, page number at right, thin rule.
% The header rule is extended LEFT by 16 mm via \fancyheadoffset so it
% spans the full content width INCLUDING the marginal number column
% (otherwise the rule looks narrow because it's anchored to the body
% text block which sits to the right of the number margin).
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\scshape\leftmark}  % chapter title at left on every page
\fancyhead[R]{\small\thepage}           % page number at right on every page
\fancyheadoffset[L]{16mm}               % extend header left over the number margin
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}
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

% \silentchapter{display name}{lowercase mark}
%   Starts a new page, sets the running mark, adds a TOC entry, and uses the
%   plain pagestyle for the opening page — but DOES NOT emit a centred chapter
%   title (the chapter is identified by the running header and by its content).
\newcommand{\silentchapter}[2]{%
  \clearpage
  \markboth{#2}{}%
  \addcontentsline{toc}{chapter}{#1}%
}

% Redefine \tableofcontents to skip the centred "Innhald" title and to
% emit the entire TOC at \footnotesize so it fits compactly on one page.
\makeatletter
\renewcommand\tableofcontents{%
  \markboth{innhald}{}%
  \begingroup\footnotesize
  \@starttoc{toc}%
  \endgroup
}
% Very compact chapter-level TOC entries
\renewcommand*\l@chapter[2]{%
  \ifnum \c@tocdepth >\m@ne
    \vskip 0pt%
    \setlength\@tempdima{1.5em}%
    \begingroup
      \footnotesize
      \parindent \z@ \rightskip \@pnumwidth
      \parfillskip -\@pnumwidth
      \leavevmode \normalfont
      \advance\leftskip\@tempdima
      \hskip -\leftskip
      #1\nobreak\leaders\hbox{$\m@th\mkern \@dotsep mu\hbox{.}\mkern \@dotsep mu$}\hfill
      \nobreak\hb@xt@\@pnumwidth{\hss #2}\par
    \endgroup
  \fi}
% Compact section / subsection entries — tight indents.
% Font size is set via \footnotesize on the entire TOC (see \tableofcontents
% redefinition above), so the entries inherit it.
\renewcommand*\l@section{\@dottedtocline{1}{1.0em}{2.0em}}
\renewcommand*\l@subsection{\@dottedtocline{2}{3.0em}{2.6em}}
\makeatother

% ─── Proposition environment ──────────────────────────────────────────────
%
% \prop{1.21}{d}{Body text...}
%   ⇒  number sits in the LEFT MARGIN (\llap'd outside the text block);
%      body text fills the entire text block as a clean justified rectangle;
%      continuation lines wrap to the body column (= text margin).
%
% This is the Gyldendal 1999 Tractatus / Töpfer marginal-numbering layout:
% the body text is a single uniform column and the proposition numbers hang
% out into the white space to the left.
%
% Numbers in the digibok appear in the same weight as the body (regular,
% not bold). The status letter is rendered as an italic superscript right
% after the number.
\usepackage{calc}
\newlength{\propnumwidth}
\setlength{\propnumwidth}{13mm}  % column reserved for the number itself
\newlength{\propnumgap}
\setlength{\propnumgap}{2mm}     % gap between number column and body text

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
\newcommand{\propcont}[1]{%
  \par\addvspace{3pt}%
  \noindent #1\par%
}

% Italic transition between chapters
\newenvironment{overgang}{%
  \par\addvspace{12pt}%
  \begingroup\itshape\noindent
}{%
  \endgroup\par\addvspace{12pt}%
}

% Glossary entries — bold term, regular body, with breathing room
% between entries. Spans up to two pages comfortably.
\newenvironment{ordliste}{%
  \begingroup\small\setlength{\parskip}{2pt plus 0.6pt}%
  \linespread{0.97}\selectfont
}{%
  \endgroup
}
\newcommand{\ordlisteentry}[2]{%
  \par\addvspace{2.5pt}%
  \noindent\textbf{#1:} #2\par%
}

% Compact Føreord body — small font, very tight parskip and linespread
% so the foreword fits on a single page.
\newenvironment{foreordbody}{%
  \begingroup\small\setlength{\parskip}{0.5pt plus 0.2pt}%
  \linespread{0.90}\selectfont
}{%
  \endgroup
}

% A.6.x explanatory body text — slightly smaller, tight line spacing
% so each A.6.x entry (heading + figure + explanation) fits compactly.
\newcommand{\anote}[1]{%
  \par\addvspace{1pt}%
  {\footnotesize\linespread{0.93}\selectfont\noindent #1\par}%
  \addvspace{1pt}%
}

% Reference entries — very compact, tight line spacing, hanging indent.
% Designed to fit ~30 entries on a single page.
\newcommand{\refentry}[1]{%
  \par\addvspace{0pt}%
  \begingroup\footnotesize\linespread{0.92}\selectfont
  \noindent\hangindent=4mm\hangafter=1 #1\par%
  \endgroup
}

% Figures — centred, max width = text width
\usepackage{graphicx}
\graphicspath{{analysis/figures/}}
\usepackage{caption}
\captionsetup{
  font={small,it},
  labelformat=empty,
  justification=centering,
  skip=4pt,
}
\usepackage{float}

% Formula display blocks (for D4, D6, etc.) — monospace, small left indent
\newenvironment{formelblokk}{%
  \par\addvspace{4pt}%
  \begingroup\ttfamily\small\leftskip=4mm\noindent
}{%
  \endgroup\par\addvspace{4pt}%
}

% Avoid widows/orphans
\widowpenalty=10000
\clubpenalty=10000

% Body paragraph defaults — tight for the small page
\setlength{\parindent}{0pt}
\setlength{\parskip}{3pt plus 0.6pt minus 0.4pt}
\linespread{1.0}

% Wide environment for back-matter sections (Etterord, Referansar) that
% should fill the full content width including the 16 mm marginal number
% column. Pulls the left edge 16 mm to the left of the body block.
\usepackage{changepage}
\newenvironment{widebody}{%
  \begin{adjustwidth}{-16mm}{0mm}%
}{%
  \end{adjustwidth}%
}

% Full-bleed cover page support — image at exact paper size, title overlaid.
\usepackage{tikz}
\usetikzlibrary{positioning}

\begin{document}
\frontmatter
"""

POSTAMBLE = r"""
\end{document}
"""


# ── LaTeX escaping ────────────────────────────────────────────────────────────

LATEX_ESCAPES = {
    '\\': r'\textbackslash{}',
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
}

# Math/logic symbols that EB Garamond lacks; these get routed through
# Cambria Math via the \msym{...} command defined in the preamble.
MATH_SYMBOLS = set(
    '∀∃∄∈∉∋⊂⊃⊄⊆⊇∪∩∅∧∨¬≠≤≥≈≡≔→←↦⇒⇐⇔∞∑∏∫√'
    'ℝℕℤℚℂ·×÷±∓∂∇∝⟨⟩'
)


def escape_latex(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in MATH_SYMBOLS:
            # Group consecutive math symbols (and spaces between them) into
            # a single \msym{...} call to minimise font-switching overhead.
            j = i + 1
            while j < n and (text[j] in MATH_SYMBOLS):
                j += 1
            out.append(r'\msym{' + text[i:j] + '}')
            i = j
            continue
        out.append(LATEX_ESCAPES.get(ch, ch))
        i += 1
    return ''.join(out)


# ── Paragraph classification ──────────────────────────────────────────────────

# Match BOTH "1.21 d Body" and "1.21d\tBody" (book_layout.py drops the space)
PROP_RE = re.compile(r'^(\d+(?:\.\d+)*)\s*([daiot])[\s\t]+(.*)$', re.DOTALL)
APPENDIX_PROP_RE = re.compile(r'^([DTA])(\d+)[\s\t]+(.*)$', re.DOTALL)
CHAPTER_TITLES = {
    '1 Form er ein posisjon i eit rom av moglegheiter.',
    '2 Ikkje alle posisjonar er like sannsynlege.',
    '3 Seleksjonstrykka produserer eit landskap over formrommet.',
    '4 Landskapet er dynamisk.',
    '5 Det finst agentar som responderer på landskapet.',
    '6 Forma oppstår mellom agentane.',
    '7 Ingen form er endeleg.',
    '7 Ingen form er endeleg; navigasjonen held fram.',
}
SECTION_NAMES = {'Innhald', 'Føreord', 'Ordliste', 'Etterord', 'Referansar'}

# Footnotes that the docx leaves stranded as plain numbered paragraphs at the
# end of the file (after the bibliography). They're injected as real LaTeX
# \footnote{} calls on the chapter-opening propositions where they belong, so
# they appear at the bottom of the correct page. Mapping by chapter number:
CHAPTER_FOOTNOTES: dict[str, list[str]] = {
    '2': [
        'Av 1.5: dei observerte posisjonane må vere resultat av krefter som favoriserer visse regionar. Desse trykka har ein bestemt karakter.',
        'Falsifiseringsvilkår: Postulatet fell om det finst ein klasse der fordelinga av former i formrommet er statistisk uavskiljbar frå ein tilfeldig prosess utan tilbakekopling.',
    ],
    '3': [
        'Dei aggregerte gradientane produserer ein topologi over formrommet.',
    ],
    '4': [
        'Proposisjon 3 definerer landskapet som ein funksjon av seleksjonstrykka. Seleksjonstrykka er ikkje konstante. Altså er heller ikkje landskapet det.',
        'Postulatet fell om tilpassingslandskapet for ein klasse kan visast å vere topologisk uendra over ein periode der den observerte fordelinga av former endrar seg.',
    ],
    '5': [
        'Proposisjonane 1 til 4 skildrar rommet, kreftene, landskapet og dynamikken. Dei spesifiserer topografien, men seier ingenting om kven eller kva som navigerer gradientane. Ei ny antaking er naudsynt.',
    ],
}

# Pattern matching the orphan numbered footnote paragraphs at the end of the
# docx (after Referansar). They look like "1 Some text..." through "6 ...".
# We skip them entirely from the rendered output because they're injected as
# real footnotes via CHAPTER_FOOTNOTES instead.
ORPHAN_FOOTNOTE_RE = re.compile(r'^[1-6]\s+\S')

# Replacement Etterord text — overrides the docx body for that section.
ETTERORD_PARAGRAPHS = [
    'Empirien er tufta på eit korpus av om lag 2 300 europeiske stolar (1280–2024). '
    'Datasettet tillet kvantitativ testing av formhistoriske hypotesar. Analysen av '
    'meshgeometri har synt at sju mesh-avleia trekk aukar den prediktive krafta for '
    'stilperiode med ein faktor på over fire samanlikna med katalogdimensjonar.',

    'Overgangen frå prosa til proposisjonsform var ein logisk nødvendigheit. '
    'Desimalnummereringa angjev den logiske vekta, og superscript (d, a, t, o, i) '
    'indikerer logisk status. Til skilnad frå Wittgensteins original, er kvar '
    'proposisjon knytt til eit eksplisitt falsifiseringsvilkår; traktaten er '
    'konstruert for å kunne fellast. Dei empiriske testane stadfestar '
    'hovudproposisjonane: formrommet er ikkje-uniformt busett; stilperiode er ein '
    'effektiv proxy for aggregerte seleksjonstrykk; og landskapet er i uopphøyrleg '
    'endring. Funna er robuste på tvers av ulike geometriske representasjonar.',

    'Observert latens i stålillustrasjonen viser at formhistoria er langsamare enn '
    'materialhistoria; eit nytt substrat arvar formspråket til det substratet det '
    'erstattar, heilt til eigne affordansar pressar det ut i nye regionar.',

    'Traktaten skildrar krefter og posisjonar, ikkje verdiar. Ho kan forklare '
    'avstanden i formrommet, men ho kan ikkje felle estetiske domar. Estetikk er '
    'transcendent til formsystemet, på same vis som etikk er transcendent til '
    'logikken (Wittgenstein). Agenten navigerer; modellen registrerer berre den '
    'resulterande posisjonen. Proposisjonane skal erkjennast som ein stige. Dei '
    'skal ikkje erstatte handverket, men gjere den intuitive navigasjonen '
    'eksplisitt ved å vise agenten kva han allereie gjer.',

    'At teksten kan fellast, er garantien for hennar gyldigheit. Om eitt einaste '
    'seleksjonstrykk forklarer all formvariasjon, kollapsar den logiske kjeden. '
    'Traktaten er stigen som skal kastast.',

    'Takk til Jan Petter Neverdahl og Hermann Stange for kommentarar under arbeidet.',
]

# Polished explanatory texts for the docx-native A.6.1 to A.6.7 sections.
# These OVERRIDE the original docx body paragraphs.
A6_BODY_OVERRIDES: dict[str, str] = {
    'A.6.1':
        'Gjensidig informasjon (sklearn k-NN) mellom stilperiode og kvar geometrisk '
        'dimensjon ligg på 0.48–0.92 bits, mot 0.23–0.42 for materialgruppe. '
        'Stilperiode er den sterkare prediktoren på alle fire dimensjonar (1.9× til '
        '2.3× høgare MI). Eit reint funksjonalistisk syn ville venta motsett resultat: '
        'materialet er den fysiske avgrensninga, stilperioden er ein kulturell '
        'merkelapp utan eige biomekanisk innhald. At den kulturelle merkelappen vinn, '
        'er ein direkte støtte til proposisjon 1.4 — formrommet er ikkje uniformt, '
        'og strukturen er stilistisk, ikkje materiell (n = 1469).',

    'A.6.2':
        'Variasjonskoeffisienten på tvers av seks mesh-trekk strekkjer seg over to '
        'storleiksordnar. Sphericity er det mest kanaliserte trekket (CV = 0.074); '
        'hylster-volumet det friaste (CV = 9.5). Spreiinga er 128× — funksjonen åleine '
        'kan ikkje forklare ei så ujamn fordeling av varians. Nokre dimensjonar er '
        'haldne stramt på plass av seleksjonstrykka, andre er nær fritt. Resultatet '
        'er robust under museum/periode/stil-undermengder (n = 2202).',

    'A.6.3':
        'Silhuett-skoren for stilperiode i 4D mesh-trekk-rom (sphericity, fill_ratio, '
        'inertia_ratio, complexity) er −0.338, 95 % CI [−0.346, −0.329] over 25 '
        'stilar med minst 10 medlemar kvar (n = 1971). Negativ silhouette betyr at '
        'gjennomsnittspunktet i ein stil ligg nærmare punkta i nabostiar enn dei '
        'eigne. Stilkategoriane er gradientar, ikkje topologiske klynger. Berre 4 av '
        '25 stilar har positiv silhouette, og dei fire er små samples (n = 12–16). '
        'Permutasjons-p-verdi < 0.001.',

    'A.6.4':
        'Det kumulative konvekse hylsterveolumet i (H, B, D), etter klipping til '
        '1.–99. persentil per dimensjon, veks monotont gjennom 10 femtjueårsperiodar '
        'frå 1500 til 2050. Totalvekst på 7×, frå 79 392 cm³ til 589 796 cm³. Eit '
        'fast funksjonsenvelop ville krevja metning, ikkje monoton vekst. Formrommet '
        'sjølv ekspanderer kontinuerleg — dette er den mest direkte stødtte til '
        'proposisjon 4.4 (n = 1041 stolar med komplette dimensjonar).',

    'A.6.5':
        'I utvalet av norskproduserte stolar frå perioden 1825–1849 er bruken av '
        'mahogni deterministisk (16 av 16), samanlikna med ein fraksjon på null i '
        'perioden 1750–1799 (0 av 16). Mahogni og valnøtt er funksjonelt utbytbare; '
        'lock-in over éin generasjon er ikkje optimisering, men sti-avhengig kollaps '
        'av seleksjonsrommet. Dette illustrerer korleis lokale seleksjonstrykk kan '
        'kollapse heile materialaksen i ei kohort.',

    'A.6.6':
        'Wasserstein-1 distansen mellom suksessive 50-årsperiodar gjev mean 15.8 cm '
        'for høgde, 9.2 cm for breidde og 5.8 cm for djupn. Ingen av dei ti '
        'periodepara har distanse under 0.5 cm. Postulatet om at landskapet er '
        'statisk vert direkte falsifisert: kvar suksessiv periode har ei distinkt '
        'fordeling. Menneskeleg ergonomi har ikkje endra seg så raskt; form endrar '
        'seg fortare enn funksjon.',

    'A.6.7':
        'Sentroidvandringa i (Breidde × Høgde)-projeksjon over 50-årsperiodar '
        '1500–2050 har banelengde 84 cm og netto skift 25 cm. Tortuositeten på 3.45 '
        'betyr at sentroiden vandrar fram og tilbake — ein dynamisk-systemsignatur, '
        'ikkje monoton funksjonell optimisering. Ein konstant tilpassingslandskap '
        'kunne aldri produsert ein så vandrande bane (n = 1041).',
}

# Notation entries in A.1 Notasjon: a short identifier (≤12 non-space chars)
# directly followed by ":" and a description. These get rendered with the
# identifier in the LEFT margin (\prop layout) so they line up like D1, D2.
# (Entries with a space before the colon, e.g. "π : Shape → ℝⁿ:", do NOT
# match — they fall through to the regular body-paragraph handler.)
NOTATION_RE = re.compile(r'^(\S{1,12}):\s+(\S.*)$')


def is_chapter(text: str) -> bool:
    return text.strip() in CHAPTER_TITLES or any(text.strip().startswith(c.split(' ', 1)[0] + ' ') and len(text.strip()) < 80 for c in CHAPTER_TITLES if False)


def chapter_title(text: str) -> str:
    """Strip the leading number from a chapter title for use as the heading."""
    t = text.strip()
    if not t: return t
    # "1 Form er ein posisjon..." → "Form er ein posisjon..."
    return re.sub(r'^[1-7]\s+', '', t).rstrip('.')


# ── Paragraph runs → LaTeX inline ─────────────────────────────────────────────

def running_head(text: str, max_chars: int = 38) -> str:
    """Return a LaTeX-escaped string suitable for a running header.
    Truncates at a word boundary if the text exceeds max_chars."""
    t = text.lower().strip().rstrip('.')
    if len(t) <= max_chars:
        return escape_latex(t)
    # Truncate at last word boundary before max_chars
    trunc = t[:max_chars].rsplit(' ', 1)[0]
    return escape_latex(trunc) + r'\ldots'


def prop_indent(num: str) -> str:
    """Return a LaTeX length for the left offset of a proposition number.
    Depth is determined by the number of digits in the final decimal segment:
      N.N   → 1 digit → 0pt   (flush left)
      N.NN  → 2 digits → 6mm  (one step in)
      N.NNN → 3 digits → 12mm (two steps in)
    """
    parts = num.split('.')
    if len(parts) < 2:
        return '0pt'
    depth = len(parts[-1])   # digits after the last period
    if depth <= 1:
        return '0pt'
    elif depth == 2:
        return '6mm'
    else:
        return '12mm'


def runs_to_latex(p) -> str:
    """Convert a paragraph's runs to LaTeX, preserving italic and bold."""
    out = []
    for r in p.runs:
        text = r.text
        if not text:
            continue
        text = escape_latex(text)
        # Handle italic and bold
        if r.italic:
            text = r'\textit{' + text + '}'
        if r.bold:
            text = r'\textbf{' + text + '}'
        if r.font.superscript:
            text = r'\textsuperscript{' + text + '}'
        out.append(text)
    return ''.join(out).strip()


def has_image(p) -> str | None:
    """Return the relationship id (rId) of the first image in this paragraph,
    or None if there's no image."""
    for r in p.runs:
        for drawing in r._element.iter(qn('w:drawing')):
            for blip in drawing.iter(qn('a:blip')):
                rid = blip.get(qn('r:embed'))
                if rid:
                    return rid
    return None


def resolve_image(p, rid: str) -> str | None:
    """Look up the image filename for the given rId in the document part."""
    try:
        part = p.part
        rels = part.rels
        if rid in rels:
            target = rels[rid].target_ref
            # target_ref looks like 'media/image1.png'
            return target.split('/')[-1]
    except Exception:
        pass
    return None


# ── Conversion ────────────────────────────────────────────────────────────────

def convert(doc: 'Document') -> str:
    """Walk the docx and emit LaTeX body."""
    out = [PREAMBLE]
    in_glossary = False
    in_appendix = False
    in_referansar = False
    in_widebody = False
    in_foreord = False
    in_a6_body = False
    seen_a6 = False
    saw_first_chapter = False
    first_chapter_seen = False

    # Identify which images are exported via the docx → which file in /word/media/
    # We need to map rIds to actual filenames in analysis/figures/
    # For our case, the images are also stored as files in analysis/figures/ —
    # the docx has its own copies but we use the source pngs for cleaner output.

    # Build a list of (anchor, fig_filename) by walking known A.6 sub-section headings
    a6_figure_map = {
        'A.6.1':  'fig-A.6.1-uniformitet.pdf',
        'A.6.2':  'fig-A.6.2-kanalisering.pdf',
        'A.6.3':  'fig-A.6.3-silhouette.pdf',
        'A.6.4':  'fig-A.6.4-ekspansjon.pdf',
        'A.6.5':  'fig-A.6.5-mahogni.pdf',
        'A.6.6':  'fig-A.6.6-wasserstein.pdf',
        'A.6.7':  'fig-A.6.7-trajektorie.pdf',
        'A.6.8':  'fig-A.6.8-materialblanding.pdf',
        'A.6.9':  'fig-A.6.9-materialstraum.pdf',
        'A.6.10': 'fig-A.6.10-proporsjon.pdf',
        'A.6.11': 'fig-A.6.11-materialnisjar.pdf',
        'A.6.12': 'fig-A.6.12-nyhetsrate.pdf',
        'A.6.13': 'fig-A.6.13-3d-trajektorie.pdf',
        'A.6.14': 'fig-A.6.15-fylogenese.pdf',
        'A.6.15': 'fig-A.6.16-rekurrens.pdf',
        'A.6.16': 'fig-A.6.17-fitnesslandskap.pdf',
    }
    # New A.6.x sections that aren't in the docx, injected after the last
    # existing A.6.x entry. Each tuple is (label, title, explanatory body).
    extra_a6_sections = [
        (
            'A.6.8',
            'Materiell kompleksitet per nasjon (5.3)',
            'Talet på distinkte material per stol varierer systematisk '
            'mellom nasjonale tradisjonar. Norske og danske stolar har '
            'medianverdi 3 (IQR 2--3 og 2--3), italienske og britiske '
            'medianverdi 2. Dette er ein kulturell signatur som ikkje '
            'kan reduserast til geografi eller tilgjengelegheit aleine; '
            'det reflekterer ulike funksjonelle nisjepartisjonar i kvart '
            'produksjonssystem (n = 1582 stolar med både material og land).',
        ),
        (
            'A.6.9',
            'Materialstraumen 1500 til 2025 (4.5)',
            'Stabla område-plott av dei ti vanlegaste materiala over fem '
            'hundreår syner klare seleksjonsbølger. Eik dominerer 1500 til '
            '1700; nøttetre kulminerer kring 1675; mahogni stig brått frå '
            '1750 og dominerer 1750--1850; modernismen sine material (stål, '
            'plast, kryssfiner, aluminium) tek over etter 1900. Ingen av '
            'overgangane er gradvise: kvar er ein lokal seleksjons-event '
            'som foreinleg med proposisjon 4.5.',
        ),
        (
            'A.6.10',
            'H/B-proporsjonen 1500 til 2024 (4.1)',
            'Den rullande 50-årsmedianen for høgde over breidde fell frå '
            'om lag 1.88 i 1600 til 1.36 i 2000 — ein endring på over '
            'eitt halvt standardavvik. Endringa er ikkje monoton; ho har '
            'eit lokalt platå 1700--1900 og fell brått etter 1900. '
            'Postulatet om eit statisk landskap (4.1) blir falsifisert '
            'av denne enkle eindimensjonale tidsserien (n = 1133).',
        ),
        (
            'A.6.11',
            'Materialnisjar i 3D-morforommet (5.3)',
            'Når kvar stol blir plotta som eit punkt i (Breidde, Djupn, '
            'Høgde) og fargelagt etter primærmaterialet, er sentroidane '
            'klart åtskilde i den vertikale dimensjonen. Tre-stolar '
            '(eik, nøttetre, mahogni) ligg kring H = 85--87 cm; metall- '
            'og plast-stolar kring H = 67--68 cm. Material er ein '
            'geometrisk axe, ikkje berre ein temporal merkelapp.',
        ),
        (
            'A.6.12',
            'Nyhetsraten og det tilstøytande moglege (6.5)',
            'Ved å diskretisere morforommet i 5 cm-voksler og telje kor '
            'mange voksler kvar 25-årsperiode opnar opp for første gong, '
            'får vi nyhetsraten over tid. Han fell ikkje monotont mot '
            'metning slik ein lukka modell ville krevje; han hentar seg '
            'inn igjen i moderne tid (1925--1975, rate 0.5--0.6) med '
            'introduksjonen av nye material. Dette er svak støtte for '
            'Kauffmans «det tilstøytande moglege» som ekspanderande rom.',
        ),
        (
            'A.6.13',
            '3D-vandring gjennom morforommet (4.1)',
            'Tre stabla tidsseriar over Høgde, Breidde og Djupn '
            'over fem hundreår. Høgda er den dominerande drifta: '
            'frå 100 cm i 1550 til 75 cm i moderne tid, ein endring '
            'på 25 cm som langt overstig nokon ergonomisk forklaring. '
            'Funksjonen åleine kan ikkje forklare ein så stor drift; '
            'menneske har ikkje krympa.',
        ),
        (
            'A.6.14',
            'Stilperiodefylogenese ved Ward-klynging (3.4)',
            'Hierarkisk klynging av stilperiodane sine sentroidar i '
            'mesh-trekk-rommet ved Ward-linkage avdekker ein meiningsfull '
            'genealogi: rokokko sit nær barokk og renessanse, '
            'modernismen har sin eigen gren med funksjonalisme og '
            'Bauhaus, og 1800-tals stilane (nyklassisisme, historisme, '
            'viktorianisme) klynger saman. Funksjonen har ingen '
            'genealogi; berre forma kan arve frå ei tidlegare form.',
        ),
        (
            'A.6.15',
            'Rekurrensanalyse av periodesentroidar (4.1, 4.4)',
            'Symmetrisk avstandsmatrise over alle 25-årsperiodar i '
            '(H, B, D)-rommet. Mørke celler er like periodar; lyse er '
            'fjerne. Det modernistiske brotet etter 1900 er synleg '
            'som ei lys L-form i nedre høgre hjørne: ingen periode '
            'før 1900 liknar nokon periode etter 1900. Formhistoria '
            'gjentar seg ikkje på tvers av modernismen.',
        ),
        (
            'A.6.16',
            'Tilpassingslandskapet med stabile attraktorar (3.2)',
            'KDE-tettleiken p̂(B, H) over alle stolar har to '
            'klare lokale maksimum: éin ved (B = 50, H = 91) — den '
            'tradisjonelle høgrygga stolen — og éin ved (B = 50, '
            'H = 45) — den lågare modernistiske stolen. Dei tomme '
            'dalane mellom toppane er forbodne regionar i '
            'morforommet, ein direkte falsifisering av uniform '
            'fordeling og støtte til proposisjon 3.2.',
        ),
    ]
    pending_a6_fig: str | None = None
    skip_manual_toc = False  # set after \tableofcontents until next H1

    paras = list(doc.paragraphs)
    i = 0
    while i < len(paras):
        p = paras[i]
        text = p.text.strip()
        if not text:
            i += 1
            continue

        style = p.style.name if p.style else 'normal'

        # Skip manual TOC entries that follow the Innhald heading in the docx
        if skip_manual_toc:
            # Stop skipping when we hit the next recognised section/chapter
            if (text in SECTION_NAMES or text in CHAPTER_TITLES
                    or text.startswith('A  Formell') or text.startswith('A Formell')):
                skip_manual_toc = False
                # fall through to handle this paragraph normally
            else:
                i += 1
                continue

        # Title page — book-cover layout. FORMLÆRE in big bold serif at the
        # TOP LEFT of the page (extending into the marginal column area),
        # the subtitle just below it, and the chair grid image centred
        # in the lower portion. No dark scrim — cream paper background.
        if style == 'Title':
            cover_path = FIG_DIR / 'cover-stolar.png'
            j = i + 1
            while j < len(paras) and not paras[j].text.strip():
                j += 1
            sub_text = ''
            if j < len(paras):
                p2 = paras[j]
                if (p2.style.name if p2.style else '') == 'Subtitle':
                    sub_text = p2.text.strip()
                    i = j + 1
                else:
                    i += 1
            else:
                i += 1

            out.append(r'\thispagestyle{titlepage}')
            out.append(r'\markboth{}{}')
            out.append(r'\begin{tikzpicture}[remember picture, overlay]')
            # Big bold FORMLÆRE in the top-left corner, 12 mm in from the
            # paper edge, 18 mm down from the top.
            out.append(r'  \node[anchor=north west, inner sep=0] '
                       r'at ([xshift=12mm, yshift=-18mm]current page.north west) {%')
            out.append(r'    {\fontsize{36}{40}\selectfont\bfseries '
                       + escape_latex(text) + '}%')
            out.append(r'  };')
            if sub_text:
                out.append(r'  \node[anchor=north west, inner sep=0] '
                           r'at ([xshift=12mm, yshift=-32mm]current page.north west) {%')
                out.append(r'    {\large\itshape '
                           + escape_latex(sub_text) + '}%')
                out.append(r'  };')
            # Chair grid image centred in the lower half of the page
            if cover_path.exists():
                out.append(r'  \node[anchor=center, inner sep=0] '
                           r'at ([yshift=-18mm]current page.center) {%')
                out.append(r'    \includegraphics[width=0.86\paperwidth]'
                           r'{cover-stolar.png}%')
                out.append(r'  };')
            out.append(r'\end{tikzpicture}')
            out.append(r'\clearpage')
            continue
        if style == 'Subtitle':
            # Subtitle without a preceding Title (defensive) — render plain.
            if text:
                out.append(r'\begin{center}')
                out.append(r'  {\large\itshape ' + escape_latex(text) + '}')
                out.append(r'\end{center}')
            i += 1
            continue

        # Section headings — all front/back-matter sections use \silentchapter
        # which suppresses the centred chapter title (the running header is
        # enough since it shows the section name on every page).
        if text in SECTION_NAMES:
            # Close any open env from the previous section
            if in_glossary:
                out.append(r'\end{ordliste}')
            if in_foreord:
                out.append(r'\end{foreordbody}')
                in_foreord = False
            if in_widebody:
                out.append(r'\end{widebody}')
                in_widebody = False
            if text == 'Innhald':
                # Custom \tableofcontents (defined in preamble) skips the
                # centred "Innhald" title and emits a compact TOC.
                # Wrapped in widebody so it fills the full content width
                # (no marginal column space needed for the TOC).
                out.append(r'\silentchapter{' + escape_latex(text) + '}{' + running_head(text) + '}')
                out.append(r'\begin{widebody}')
                out.append(r'\tableofcontents')
                out.append(r'\end{widebody}')
                skip_manual_toc = True
            elif text == 'Etterord':
                # Inject extra A.6.x sections before leaving the appendix.
                # Each section: heading + figure + explanatory body paragraph.
                for ex_label, ex_title, ex_body in extra_a6_sections:
                    out.append(r'\prop{' + escape_latex(ex_label) + '}{}{' +
                               escape_latex(ex_title) + '}')
                    out.append(r'\addcontentsline{toc}{subsection}{' +
                               escape_latex(ex_label + ' ' + ex_title) + '}')
                    ex_fig = a6_figure_map.get(ex_label)
                    if ex_fig and (FIG_DIR / ex_fig).exists():
                        out.append(r'\par\addvspace{2pt}\noindent\centerline{%')
                        out.append(r'  \includegraphics[width=\linewidth]{' +
                                   ex_fig + '}}')
                        out.append(r'\par\addvspace{2pt}')
                    out.append(r'\anote{' + escape_latex(ex_body) + '}')
                    out.append('')
                if in_appendix:
                    in_appendix = False
                out.append(r'\backmatter')
                out.append(r'\silentchapter{' + escape_latex(text) + '}{' + running_head(text) + '}')
                out.append(r'\begin{widebody}')
                in_widebody = True
                # Emit the polished Etterord text and skip the docx body
                for para in ETTERORD_PARAGRAPHS:
                    out.append(escape_latex(para))
                    out.append('')
                # Advance past the docx Etterord body until Referansar
                j = i + 1
                while j < len(paras):
                    nt = paras[j].text.strip()
                    if nt == 'Referansar':
                        break
                    j += 1
                i = j
                in_glossary = False
                in_referansar = False
                continue
            elif text == 'Referansar':
                out.append(r'\silentchapter{' + escape_latex(text) + '}{' + running_head(text) + '}')
                out.append(r'\begin{widebody}')
                in_widebody = True
            elif text == 'Ordliste':
                # Ordliste fills full content width and uses the compact env
                out.append(r'\silentchapter{' + escape_latex(text) + '}{' + running_head(text) + '}')
                out.append(r'\begin{widebody}')
                out.append(r'\begin{ordliste}')
                in_widebody = True
            elif text == 'Føreord':
                # Føreord fills full content width and uses the compact body
                out.append(r'\silentchapter{' + escape_latex(text) + '}{' + running_head(text) + '}')
                out.append(r'\begin{widebody}')
                out.append(r'\begin{foreordbody}')
                in_widebody = True
                in_foreord = True
            else:
                out.append(r'\silentchapter{' + escape_latex(text) + '}{' + running_head(text) + '}')
            in_glossary = (text == 'Ordliste')
            in_referansar = (text == 'Referansar')
            i += 1
            continue

        # Chapter-level proposition (1, 2, 3, ..., 7) — same visual format as
        # any other proposition; only the TOC entry and running header differ.
        if text in CHAPTER_TITLES:
            # Close any open glossary/foreord/widebody before main matter
            if in_glossary:
                out.append(r'\end{ordliste}')
                in_glossary = False
            if in_foreord:
                out.append(r'\end{foreordbody}')
                in_foreord = False
            if in_widebody:
                out.append(r'\end{widebody}')
                in_widebody = False
            if not first_chapter_seen:
                out.append(r'\mainmatter')
                first_chapter_seen = True
            # Parse "1 Form er ein posisjon..." → num="1", body="Form er ein..."
            m_ch = re.match(r'^(\d)\s+(.*)', text.strip())
            if m_ch:
                ch_num, ch_body = m_ch.group(1), m_ch.group(2).rstrip('.')
            else:
                ch_num, ch_body = '?', text
            # New page for each chapter, update running head, add TOC entry
            out.append(r'\clearpage')
            out.append(r'\addcontentsline{toc}{chapter}{' + escape_latex(text.rstrip('.')) + '}')
            out.append(r'\markboth{' + running_head(ch_body) + '}{}')
            # Inject any chapter-level footnotes (originally orphan paragraphs
            # at the end of the docx) so they appear at the bottom of THIS page.
            body_tex = escape_latex(ch_body)
            for fn in CHAPTER_FOOTNOTES.get(ch_num, []):
                body_tex += r'\footnote{' + escape_latex(fn) + '}'
            out.append(r'\prop{' + escape_latex(ch_num) + '}{}{' + body_tex + '}')
            in_glossary = False
            i += 1
            continue

        # Skip orphan numbered footnote paragraphs at the end of the doc
        # (after the bibliography). They are already injected as real
        # \footnote{} calls on the chapter-opening propositions above.
        if ORPHAN_FOOTNOTE_RE.match(text):
            i += 1
            continue

        # Appendix top-level (explicit heading, if any) — use silent chapter
        if text.startswith('A  Formell') or text.startswith('A Formell'):
            out.append(r'\appendix')
            out.append(r'\silentchapter{Formell spesifikasjon}{formell spesifikasjon}')
            in_appendix = True
            i += 1
            continue

        # A.6.x sub-section — render as marginal \prop (label in left margin),
        # then immediately embed the falsification figure for that section.
        m_a6 = re.match(r'^(A\.\d\.\d)\s+(.*)$', text)
        if m_a6:
            label = m_a6.group(1)
            rest = m_a6.group(2)
            # First A.x heading also marks the start of the appendix
            if not in_appendix:
                out.append(r'\appendix')
                out.append(r'\silentchapter{Formell spesifikasjon}{formell spesifikasjon}')
                in_appendix = True
            # Force the first A.6.x entry to start on a fresh page so the
            # empirical results section opens cleanly after the definitions.
            if not seen_a6:
                out.append(r'\clearpage')
                seen_a6 = True
            out.append(r'\prop{' + escape_latex(label) + '}{}{' + escape_latex(rest) + '}')
            out.append(r'\addcontentsline{toc}{subsection}{' + escape_latex(label + ' ' + rest) + '}')

            # Embed the falsification figure right under the heading
            fig_filename = a6_figure_map.get(label)
            if fig_filename:
                fig_path = FIG_DIR / fig_filename
                if fig_path.exists():
                    out.append(r'\par\addvspace{2pt}\noindent\centerline{%')
                    out.append(r'  \includegraphics[width=\linewidth]{' + fig_filename + '}}')
                    out.append(r'\par\addvspace{2pt}')
            # If we have an override body for this section, emit it now
            # and skip the original docx body paragraphs that follow.
            override = A6_BODY_OVERRIDES.get(label)
            if override:
                out.append(r'\anote{' + escape_latex(override) + '}')
                # Skip docx body paragraphs until the next heading
                j = i + 1
                while j < len(paras):
                    nt = paras[j].text.strip()
                    if not nt:
                        j += 1
                        continue
                    if (re.match(r'^A\.\d', nt) or nt in SECTION_NAMES
                            or nt in CHAPTER_TITLES):
                        break
                    j += 1
                i = j
                in_a6_body = False
                continue
            in_a6_body = True
            i += 1
            continue

        # A.x section heading — render as marginal \prop (label in left margin).
        m_ax = re.match(r'^(A\.\d)\s+(.*)$', text)
        if m_ax:
            label = m_ax.group(1)
            rest = m_ax.group(2)
            # First A.x heading also marks the start of the appendix
            if not in_appendix:
                out.append(r'\appendix')
                out.append(r'\silentchapter{Formell spesifikasjon}{formell spesifikasjon}')
                in_appendix = True
            in_a6_body = False
            out.append(r'\prop{' + escape_latex(label) + '}{}{' + escape_latex(rest) + '}')
            out.append(r'\addcontentsline{toc}{section}{' + escape_latex(label + ' ' + rest) + '}')
            i += 1
            continue

        # Proposition
        m = PROP_RE.match(text)
        if m:
            num, status, body = m.groups()
            body_tex = escape_latex(body.strip())
            # Peek ahead: collect any immediately-following Falsifiseringsvilkår
            # paragraphs and attach them as footnotes to this proposition.
            j = i + 1
            footnotes: list[str] = []
            while j < len(paras):
                nxt = paras[j].text.strip()
                if not nxt:
                    j += 1
                    continue
                if nxt.startswith('Falsifiseringsvilkår'):
                    # Strip the "Falsifiseringsvilkår:" prefix; what remains is
                    # the actual condition text.
                    after = nxt.split(':', 1)[1].strip() if ':' in nxt else nxt
                    footnotes.append(escape_latex(after))
                    j += 1
                    continue
                break
            if footnotes:
                body_tex += ''.join(r'\footnote{' + fn + '}' for fn in footnotes)
                i = j
            else:
                i += 1
            out.append(r'\prop{' + escape_latex(num) + '}{' + escape_latex(status) + '}{' + body_tex + '}')
            continue

        # Appendix notation entry (e.g. "c: ein klasse", "Cov: kovarians")
        # — render with the identifier in the LEFT margin like D1/D2.
        if in_appendix:
            m_not = NOTATION_RE.match(text)
            if m_not:
                name, descr = m_not.groups()
                # Avoid mis-matching APPENDIX_PROP_RE (D1, T6) — they are
                # handled by the next branch.
                if not APPENDIX_PROP_RE.match(text):
                    out.append(r'\prop{' + escape_latex(name) + '}{}{' + escape_latex(descr.strip()) + '}')
                    i += 1
                    continue

        # Appendix definition entry (D4, T6, A1) — look ahead for body lines
        if in_appendix:
            m_app = APPENDIX_PROP_RE.match(text)
            if m_app:
                letter, num, body = m_app.groups()
                label = f'{letter}{num}'
                out.append(r'\prop{' + escape_latex(label) + '}{}{' + escape_latex(body.strip()) + '}')
                # Consume continuation lines (formulas, sub-clauses) until we hit
                # the next definition, section heading, or other structural marker
                j = i + 1
                while j < len(paras):
                    nt = paras[j].text.strip()
                    if not nt:
                        j += 1
                        continue
                    # Stop on next definition, section heading, or chapter heading
                    if (APPENDIX_PROP_RE.match(nt)
                            or re.match(r'^A\.\d', nt)
                            or nt in SECTION_NAMES
                            or nt in CHAPTER_TITLES
                            or PROP_RE.match(nt)):
                        break
                    out.append(r'\propcont{' + escape_latex(nt) + '}')
                    j += 1
                i = j
                continue

        # Stray Falsifiseringsvilkår not attached to a preceding proposition
        # (the proposition handler normally consumes these as footnotes)
        if text.startswith('Falsifiseringsvilkår'):
            after = text.split(':', 1)[1].strip() if ':' in text else text
            out.append(r'{\small\itshape ' + escape_latex(after) + r'\par}')
            i += 1
            continue

        # Glossary entry: "Term: definition"
        if in_glossary and ':' in text and not text.startswith(' '):
            term, _, defn = text.partition(':')
            if term and defn:
                out.append(r'\ordlisteentry{' + escape_latex(term.strip()) + '}{' + escape_latex(defn.strip()) + '}')
                i += 1
                continue

        # Skip the Ordliste intro paragraph entirely
        if in_glossary and text.startswith('Ordlista gjev'):
            i += 1
            continue

        # Skip stray single-digit paragraphs (page-number artefacts from the docx)
        if re.fullmatch(r'\d', text):
            i += 1
            continue

        # Italic-only paragraph → italic transition (overgang)
        all_italic = bool(p.runs) and all(r.italic for r in p.runs if r.text.strip())
        if all_italic and len(text) < 200:
            out.append(r'\begin{overgang}' + escape_latex(text) + r'\end{overgang}')
            i += 1
            continue

        # References — emit as compact \refentry{...}
        if in_referansar:
            out.append(r'\refentry{' + escape_latex(text) + '}')
            i += 1
            continue

        # A.6.x explanatory body text — wrap in \anote{} for compact format
        if in_a6_body:
            out.append(r'\anote{' + escape_latex(text) + '}')
            out.append('')
            i += 1
            continue

        # Body paragraph
        out.append(escape_latex(text))
        out.append('')
        i += 1

    if in_widebody:
        out.append(r'\end{widebody}')
    out.append(POSTAMBLE)
    return '\n'.join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-compile', action='store_true', help='write .tex only, do not run xelatex')
    args = ap.parse_args()

    if not DOCX.exists():
        print(f'ERROR: {DOCX} not found', file=sys.stderr); return 1

    print(f'reading {DOCX}')
    doc = Document(str(DOCX))
    tex = convert(doc)
    TEX.write_text(tex, encoding='utf-8')
    print(f'wrote {TEX} ({len(tex)} chars)')

    if args.no_compile:
        return 0

    # Compile via xelatex
    xelatex = shutil.which('xelatex')
    if not xelatex:
        print('xelatex not found; .tex written but not compiled', file=sys.stderr)
        return 0

    # Run twice for TOC resolution
    BUILD_DIR.mkdir(exist_ok=True)
    print('compiling with xelatex (1/2)...')
    for run in range(2):
        result = subprocess.run(
            [xelatex, '-interaction=nonstopmode',
             '-output-directory=' + str(BUILD_DIR),
             str(TEX)],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        if result.returncode != 0:
            print(f'\nxelatex run {run+1} failed (rc={result.returncode}):', file=sys.stderr)
            print(result.stdout[-3000:] if result.stdout else '', file=sys.stderr)
            print(result.stderr[-1000:] if result.stderr else '', file=sys.stderr)
            return 1
        print(f'compiling with xelatex ({run+2}/2)...' if run == 0 else 'done')

    pdf_built = BUILD_DIR / 'FORMLÆRE.pdf'
    if pdf_built.exists():
        shutil.copy(pdf_built, PDF)
        print(f'wrote {PDF} ({PDF.stat().st_size} bytes)')
    else:
        print('PDF not produced', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
