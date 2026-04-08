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
% oneside layout: same header on every page (no recto/verso distinction).
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\scshape\leftmark}  % chapter title at left on all pages
\fancyhead[R]{\small\thepage}           % page number at right on all pages
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}
% plain style (chapter-opening pages): same header, no footer
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{\small\scshape\leftmark}
  \fancyhead[R]{\small\thepage}
  \renewcommand{\headrulewidth}{0.4pt}
  \renewcommand{\footrulewidth}{0pt}
}
% empty style: only used on title page
\fancypagestyle{empty}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \renewcommand{\footrulewidth}{0pt}
}

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
\newcommand{\prop}[3]{%
  \par\addvspace{6pt}%
  \noindent\llap{\makebox[\propnumwidth][l]{#1\textsuperscript{\textit{#2}}}\hspace{\propnumgap}}%
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

% Glossary entries — bold term, regular body, small hanging indent
\newcommand{\ordlisteentry}[2]{%
  \par\addvspace{4pt}%
  {\setlength{\leftskip}{3mm}%
   \setlength{\parindent}{-3mm}%
   \noindent\textbf{#1:} #2\par}%
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

% Body paragraph defaults
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt plus 1pt minus 0.5pt}
\linespread{1.0}

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
    saw_first_chapter = False
    first_chapter_seen = False

    # Identify which images are exported via the docx → which file in /word/media/
    # We need to map rIds to actual filenames in analysis/figures/
    # For our case, the images are also stored as files in analysis/figures/ —
    # the docx has its own copies but we use the source pngs for cleaner output.

    # Build a list of (anchor, fig_filename) by walking known A.6 sub-section headings
    a6_figure_map = {
        'A.6.1': 'fig-1.4-morphospace.png',
        'A.6.2': 'fig-2.4-prediktor.png',
        'A.6.3': 'fig-3.3-channeling-v2.png',
        'A.6.4': 'fig-3.4-silhouette.png',
        'A.6.5': 'I-4_morphospace_ekspansjon.png',
        'A.6.6': 'fig-4.5-mahogni.png',
        'A.6.7': 'fig-falsification-4.1.png',
    }
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

        # Title page — always blank header and no page number
        if style == 'Title':
            out.append(r'\pagestyle{empty}\vspace*{4cm}')
            out.append(r'\begin{center}')
            out.append(r'  {\Huge\scshape\addfontfeature{LetterSpace=12} ' + escape_latex(text) + '}')
            out.append(r'\end{center}')
            i += 1
            continue
        if style == 'Subtitle':
            if text:
                out.append(r'\begin{center}')
                out.append(r'  {\large\itshape ' + escape_latex(text) + '}')
                out.append(r'\end{center}')
            # Restore normal page style after title+subtitle
            out.append(r'\pagestyle{fancy}')
            i += 1
            continue

        # Section headings
        if text in SECTION_NAMES:
            if text == 'Føreord' and not first_chapter_seen:
                # \frontmatter is already in the preamble; don't reset page counter
                out.append(r'\chapter*{' + escape_latex(text) + '}')
                out.append(r'\addcontentsline{toc}{chapter}{' + escape_latex(text) + '}')
                out.append(r'\markboth{' + running_head(text) + '}{}')
            elif text == 'Innhald':
                # Use LaTeX's auto-TOC; skip the manual TOC entries that follow
                out.append(r'\tableofcontents')
                out.append(r'\clearpage')
                skip_manual_toc = True
            elif text == 'Etterord':
                out.append(r'\backmatter\chapter*{' + escape_latex(text) + '}')
                out.append(r'\addcontentsline{toc}{chapter}{' + escape_latex(text) + '}')
                out.append(r'\markboth{' + running_head(text) + '}{}')
            elif text == 'Referansar':
                out.append(r'\chapter*{' + escape_latex(text) + '}')
                out.append(r'\addcontentsline{toc}{chapter}{' + escape_latex(text) + '}')
                out.append(r'\markboth{' + running_head(text) + '}{}')
            else:
                out.append(r'\chapter*{' + escape_latex(text) + '}')
                out.append(r'\addcontentsline{toc}{chapter}{' + escape_latex(text) + '}')
                out.append(r'\markboth{' + running_head(text) + '}{}')
            in_glossary = (text == 'Ordliste')
            i += 1
            continue

        # Chapter-level proposition (1, 2, 3, ..., 7) — same visual format as
        # any other proposition; only the TOC entry and running header differ.
        if text in CHAPTER_TITLES:
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
            # Emit as a regular proposition (no status letter)
            out.append(r'\prop{' + escape_latex(ch_num) + '}{}{' + escape_latex(ch_body) + '}')
            in_glossary = False
            i += 1
            continue

        # Appendix top-level (explicit heading, if any)
        if text.startswith('A  Formell') or text.startswith('A Formell'):
            out.append(r'\appendix')
            out.append(r'\chapter*{' + escape_latex('A  Formell spesifikasjon') + '}')
            out.append(r'\addcontentsline{toc}{chapter}{Formell spesifikasjon}')
            in_appendix = True
            i += 1
            continue

        # A.6.x sub-section
        m_a6 = re.match(r'^(A\.\d\.\d)\s+(.*)$', text)
        if m_a6:
            label = m_a6.group(1)
            rest = m_a6.group(2)
            # First A.x heading also marks the start of the appendix
            if not in_appendix:
                out.append(r'\appendix')
                out.append(r'\chapter*{' + escape_latex('Formell spesifikasjon') + '}')
                out.append(r'\addcontentsline{toc}{chapter}{Formell spesifikasjon}')
                out.append(r'\markboth{formell spesifikasjon}{}')
                in_appendix = True
            out.append(r'\subsection*{' + escape_latex(label + ' ' + rest) + '}')
            out.append(r'\addcontentsline{toc}{subsection}{' + escape_latex(label + ' ' + rest) + '}')
            pending_a6_fig = a6_figure_map.get(label)
            i += 1
            continue

        # A.x section heading
        m_ax = re.match(r'^(A\.\d)\s+(.*)$', text)
        if m_ax:
            label = m_ax.group(1)
            rest = m_ax.group(2)
            # First A.x heading also marks the start of the appendix
            if not in_appendix:
                out.append(r'\appendix')
                out.append(r'\chapter*{' + escape_latex('Formell spesifikasjon') + '}')
                out.append(r'\addcontentsline{toc}{chapter}{Formell spesifikasjon}')
                out.append(r'\markboth{formell spesifikasjon}{}')
                in_appendix = True
            out.append(r'\section*{' + escape_latex(label + ' ' + rest) + '}')
            out.append(r'\markboth{' + running_head(label + ' ' + rest) + '}{}')

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

        # Skip stray single-digit paragraphs (page-number artefacts from the docx)
        if re.fullmatch(r'\d', text):
            i += 1
            continue

        # Italic-only paragraph → likely a transition or caption
        all_italic = bool(p.runs) and all(r.italic for r in p.runs if r.text.strip())
        if all_italic and len(text) < 200:
            # Caption following an A.6.x heading: emit as figure block
            if pending_a6_fig is not None:
                fig_path = FIG_DIR / pending_a6_fig
                if fig_path.exists():
                    out.append(r'\begin{figure}[H]')
                    out.append(r'  \centering')
                    out.append(r'  \includegraphics[width=\linewidth]{' + pending_a6_fig + '}')
                    out.append(r'  \caption{' + escape_latex(text) + '}')
                    out.append(r'\end{figure}')
                    pending_a6_fig = None
                    i += 1
                    continue
            # Otherwise: italic transition
            out.append(r'\begin{overgang}' + escape_latex(text) + r'\end{overgang}')
            i += 1
            continue

        # Body paragraph
        out.append(escape_latex(text))
        out.append('')
        i += 1

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
