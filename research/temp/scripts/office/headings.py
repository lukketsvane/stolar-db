#!/usr/bin/env python3
"""
Normalize all chapter, section and sub-section headings in FORMLÆRE.docx.

H1 (Garamond 14pt bold, 18pt before, 6pt after):
  Innhald, Føreord, Ordliste, "1 Form ...", "2 Ikkje ...", ..., "7 Ingen form ...",
  Etterord, "A  Formell spesifikasjon", Referansar

H2 (Garamond 12pt bold, 12pt before, 4pt after):
  A.1 Notasjon, A.2 Aksiom, A.3 Definisjonar, A.4 Teorem,
  A.5 Turing-komplettheitsargument, A.6 Empiriske testresultat

H3 (Garamond 11pt bold, 8pt before, 3pt after):
  A.6.1, A.6.2, A.6.3, A.6.4, A.6.5

The actual style names in python-docx are 'Heading 1' / 'Heading 2' / 'Heading 3'.
We additionally apply explicit run formatting so the look is preserved even if
the style definitions are reset.

Run:
  python scripts/office/headings.py
  python scripts/office/headings.py --dry-run
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).resolve().parents[2]
DOCX = ROOT / 'FORMLÆRE.docx'

H1_TEXTS = {'Innhald', 'Føreord', 'Ordliste', 'Etterord', 'Referansar'}
H1_PROP_RE = re.compile(r'^([1-7])\s')  # "1 Form ...", "2 Ikkje ..."
H1_APP_RE = re.compile(r'^A\s+Formell spesifikasjon')

H2_RE = re.compile(r'^A\.\d\s')          # A.1 Notasjon, A.2 Aksiom, ...
H3_RE = re.compile(r'^A\.\d\.\d\s')      # A.6.1 ...


def classify(text: str) -> str | None:
    t = text.strip()
    if not t:
        return None
    if t in H1_TEXTS:
        return 'h1'
    if H1_APP_RE.match(t):
        return 'h1'
    if H1_PROP_RE.match(t) and len(t) < 80:  # short top-level chapter line
        # Make sure this isn't a sub-prop like "1.1 o ..."
        if re.match(r'^[1-7]\.', t):
            return None
        return 'h1'
    if H3_RE.match(t):
        return 'h3'
    if H2_RE.match(t):
        return 'h2'
    return None


def style_paragraph(p, level: str) -> None:
    """Apply heading style + explicit run formatting for stable visual look."""
    style_name = {'h1': 'Heading 1', 'h2': 'Heading 2', 'h3': 'Heading 3'}[level]
    p.style = style_name
    size_pt = {'h1': 14, 'h2': 12, 'h3': 11}[level]
    space_before_pt = {'h1': 18, 'h2': 12, 'h3': 8}[level]
    space_after_pt = {'h1': 6, 'h2': 4, 'h3': 3}[level]

    p.paragraph_format.space_before = Pt(space_before_pt)
    p.paragraph_format.space_after = Pt(space_after_pt)
    # H1 chapter headings get a small left indent of 0 (no indent)
    p.paragraph_format.left_indent = None

    # Reset all runs: make every run Garamond + correct size + bold
    for r in p.runs:
        r.font.name = 'Garamond'
        r.font.size = Pt(size_pt)
        r.bold = True
        r.italic = False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    if not DOCX.exists():
        print(f'ERROR: {DOCX} not found', file=sys.stderr); return 1
    doc = Document(str(DOCX))
    counts = {'h1': 0, 'h2': 0, 'h3': 0}
    for i, p in enumerate(doc.paragraphs):
        level = classify(p.text)
        if level is None:
            continue
        counts[level] += 1
        print(f'  {level} para {i:3d}: {p.text[:70]}')
        if not args.dry_run:
            style_paragraph(p, level)
    if not args.dry_run:
        doc.save(str(DOCX))
    print(f"\n{'DRY' if args.dry_run else 'APPLY'}: {counts['h1']} H1, {counts['h2']} H2, {counts['h3']} H3")
    return 0


if __name__ == '__main__':
    sys.exit(main())
