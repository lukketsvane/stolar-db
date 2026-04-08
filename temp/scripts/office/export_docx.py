"""Export FORMLÆRE.tex to a clean, properly-formatted .docx for
Google Docs / Word import.

Pandoc converts LaTeX to docx but cannot interpret the custom commands
the book uses (\\prop, \\anote, \\silentchapter, \\widebody, tikz cover,
adjustwidth, etc.). This script:

  1. Reads FORMLÆRE.tex
  2. Rewrites it into a "clean" .tex that pandoc can convert losslessly:
       - \\prop{num}{status}{body}    -> \\textbf{num<sup>status</sup>} body
       - \\propcont{body}             -> body
       - \\anote{body}                -> body (in italic)
       - \\refentry{body}             -> body
       - \\ordlisteentry{term}{def}   -> \\textbf{term:} def
       - \\silentchapter{name}{mark}  -> \\chapter*{name}
       - \\begin{widebody}/\\end      -> stripped
       - \\begin{ordliste}/\\end       -> stripped
       - \\begin{foreordbody}/\\end    -> stripped
       - \\begin{adjustwidth}{...}{...}/\\end -> stripped
       - The tikzpicture cover         -> a centred title block
  3. Runs pandoc with our reference template (correct page size + font)
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEX  = ROOT / 'FORMLÆRE.tex'
CLEAN = ROOT / 'temp' / 'FORMLÆRE-clean.tex'
OUT  = ROOT / 'FORMLÆRE-export.docx'
REF  = ROOT / 'temp' / 'reference.docx'
PANDOC = (
    'C:/Users/Shadow/AppData/Local/Microsoft/WinGet/Packages/'
    'JohnMacFarlane.Pandoc_Microsoft.Winget.Source_8wekyb3d8bbwe/'
    'pandoc-3.9.0.2/pandoc.exe'
)


def find_balanced(src: str, start: int, open_ch: str = '{', close_ch: str = '}') -> int:
    """Given src and an index `start` pointing at `open_ch`, return the
    index of the matching close character (one past)."""
    assert src[start] == open_ch
    depth = 1
    i = start + 1
    while i < len(src) and depth > 0:
        ch = src[i]
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
        i += 1
    return i  # one past the close


def replace_one_arg_macro(src: str, name: str, repl_fn) -> str:
    """Replace \\name{ARG} occurrences. repl_fn(arg) -> replacement."""
    out = []
    i = 0
    pat = '\\' + name + '{'
    while i < len(src):
        idx = src.find(pat, i)
        if idx < 0:
            out.append(src[i:])
            break
        out.append(src[i:idx])
        brace = idx + len(pat) - 1
        end = find_balanced(src, brace)
        arg = src[brace + 1: end - 1]
        out.append(repl_fn(arg))
        i = end
    return ''.join(out)


def replace_n_arg_macro(src: str, name: str, n: int, repl_fn) -> str:
    """Replace \\name{A1}{A2}...{An} occurrences."""
    out = []
    i = 0
    pat = '\\' + name + '{'
    while i < len(src):
        idx = src.find(pat, i)
        if idx < 0:
            out.append(src[i:])
            break
        out.append(src[i:idx])
        # Read N arguments
        args = []
        cur = idx + len('\\' + name)
        for _ in range(n):
            # Skip whitespace
            while cur < len(src) and src[cur] in ' \t\n':
                cur += 1
            if cur >= len(src) or src[cur] != '{':
                break
            end = find_balanced(src, cur)
            args.append(src[cur + 1: end - 1])
            cur = end
        if len(args) == n:
            out.append(repl_fn(*args))
            i = cur
        else:
            out.append(pat)
            i = idx + len(pat)
    return ''.join(out)


MINIMAL_PREAMBLE = r"""\documentclass[10pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{hyperref}
\graphicspath{{analysis/figures/}}
\begin{document}
"""


def clean_tex(src: str) -> str:
    # Extract just the body between \begin{document} and \end{document},
    # then prepend a minimal preamble pandoc can handle.
    m = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', src, re.DOTALL)
    if m:
        body = m.group(1)
        src = MINIMAL_PREAMBLE + body + '\n\\end{document}\n'

    # Remove the entire tikzpicture cover block, then add a simple title
    # at the start of the document body.
    src = re.sub(
        r'\\begin\{tikzpicture\}\[remember picture, overlay\].*?'
        r'\\end\{tikzpicture\}',
        r'\n{\\Huge\\bfseries FORMLÆRE}\n\n'
        r'{\\large\\itshape Ei traktatform om korleis form oppstår}\n\n',
        src,
        flags=re.DOTALL,
    )

    # Strip the inline \noindent\centerline{...image...} wrapper around
    # figure embeds. Replace with just the bare \includegraphics call.
    def strip_centerline(m):
        return m.group(1)
    src = re.sub(
        r'\\noindent\\centerline\{%?\s*(\\includegraphics\[[^\]]*\]\{[^}]+\})\s*\}',
        strip_centerline, src,
    )

    # Strip silent-chapter mark argument: \silentchapter{NAME}{mark} -> \chapter*{NAME}
    src = replace_n_arg_macro(
        src, 'silentchapter', 2,
        lambda name, mark: '\\chapter*{' + name + '}'
    )

    # \prop{num}{status}{body} -> \textbf{num$^{status}$} body
    def prop_repl(num, status, body):
        sup = f'\\textsuperscript{{\\textit{{{status}}}}}' if status.strip() else ''
        return f'\n\n\\noindent\\textbf{{{num}}}{sup}\\quad {body}\n\n'
    src = replace_n_arg_macro(src, 'prop', 3, prop_repl)

    # \propcont{body} -> body
    src = replace_one_arg_macro(src, 'propcont', lambda body: '\n\n' + body + '\n\n')

    # \anote{body} -> italic body
    src = replace_one_arg_macro(src, 'anote',
                                lambda body: '\n\n\\textit{' + body + '}\n\n')

    # \refentry{body} -> body
    src = replace_one_arg_macro(src, 'refentry', lambda body: '\n\n' + body + '\n\n')

    # \ordlisteentry{term}{def} -> \textbf{term:} def
    src = replace_n_arg_macro(
        src, 'ordlisteentry', 2,
        lambda term, defn: f'\n\n\\textbf{{{term}:}} {defn}\n\n'
    )

    # Remove environment wrappers that pandoc cannot interpret cleanly.
    # adjustwidth has two arguments after \begin
    src = re.sub(
        r'\\begin\{adjustwidth\}\{[^}]*\}\{[^}]*\}', '', src)
    src = re.sub(r'\\end\{adjustwidth\}', '', src)
    for env in ('widebody', 'ordliste', 'foreordbody', 'appendixbody', 'overgang'):
        src = re.sub(r'\\begin\{' + env + r'\}', '', src)
        src = re.sub(r'\\end\{' + env + r'\}', '', src)

    # Remove things that don't translate
    src = re.sub(r'\\thispagestyle\{[^}]*\}', '', src)
    src = re.sub(r'\\pagestyle\{[^}]*\}', '', src)
    src = re.sub(r'\\markboth\{[^}]*\}\{[^}]*\}', '', src)
    src = re.sub(r'\\addcontentsline\{[^}]*\}\{[^}]*\}\{[^}]*\}', '', src)
    src = re.sub(r'\\vspace\*?\{[^}]*\}', '', src)
    src = re.sub(r'\\addvspace\{[^}]*\}', '', src)
    src = re.sub(r'\\par\\addvspace\{[^}]*\}', '', src)
    src = re.sub(r'\\noindent\\centerline\{%?', '', src)
    src = re.sub(r'\\clearpage', '', src)
    src = re.sub(r'\\par\b', '\n\n', src)

    # Strip the tikz package import (we removed all uses)
    src = re.sub(r'\\usepackage\{tikz\}', '', src)
    src = re.sub(r'\\usetikzlibrary\{[^}]*\}', '', src)

    return src


def main():
    if not TEX.exists():
        print(f'ERROR: {TEX} not found', file=sys.stderr)
        return 1

    print(f'reading {TEX}')
    src = TEX.read_text(encoding='utf-8')
    cleaned = clean_tex(src)
    CLEAN.parent.mkdir(exist_ok=True)
    CLEAN.write_text(cleaned, encoding='utf-8')
    print(f'wrote {CLEAN} ({len(cleaned)} chars)')

    print('exporting via pandoc...')
    cmd = [PANDOC,
           '--reference-doc', str(REF),
           '--resource-path=analysis/figures:.',
           '-f', 'latex', '-t', 'docx',
           str(CLEAN), '-o', str(OUT)]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    if result.returncode != 0:
        print(result.stderr[-2000:], file=sys.stderr)
        return 1
    print(f'wrote {OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
