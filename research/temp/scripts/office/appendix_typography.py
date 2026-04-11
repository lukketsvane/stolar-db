#!/usr/bin/env python3
"""
Polish appendix typography in FORMLÆRE.docx.

For each paragraph that sits inside the formal appendix (between
'A  Formell spesifikasjon' and 'Referansar'), if it contains
formula characters (∀ ∃ ∈ → ≤ ≥ ≠ ⊂ ⊆ Σ Π λ τ π ≔ := · etc) or is a
plain formula line under a Dn / Tn / An heading, switch its run font
to Cousine (monospace) and apply a small left indent so formulas sit
visibly under their headings.

Definition / theorem / axiom HEADINGS themselves (D4, T1, A1) stay in
the body font but get a hanging indent so their formula bodies appear
indented underneath.

Run:
  python scripts/office/appendix_typography.py
  python scripts/office/appendix_typography.py --dry-run
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
from docx.shared import Pt, Cm

ROOT = Path(__file__).resolve().parents[2]
DOCX = ROOT / 'FORMLÆRE_latest.docx'

# Characters that mark a paragraph as a formula line
FORMULA_CHARS = set('∀∃∈∉⊂⊆⊃⊇∪∩→←↔⇒⇔≤≥≠≔≈Σπλτεεδφψχω·×÷±√∞∑∏∫⊕⊗∧∨¬⊥⊤⊨ℝℕℤℚℂ')
# Lines starting with these patterns are formal headings
HEADING_RE = re.compile(r'^(D\d+|T\d+|A\d+)\s')


PROSE_WORDS_RE = re.compile(r'\b(er|og|ikkje|den|ein|ei|eit|som|av|i|på|for|med|alle|under|denne|dette|han|ho|over|under|brukar|finst|kan|må)\b', re.IGNORECASE)


def is_formula_line(text: str) -> bool:
    """A formula line is short, has formula symbols, and isn't carrying
    a Norwegian sentence. Mixed prose-with-math stays as prose."""
    t = text.strip()
    if not t:
        return False
    if HEADING_RE.match(t):
        return False
    has_formula = any(c in FORMULA_CHARS for c in t)
    if not has_formula:
        return False
    # If the line is long (> 90 chars), it's probably prose with embedded math
    if len(t) > 90:
        return False
    # If it has many Norwegian function words, it's prose
    n_prose_words = len(PROSE_WORDS_RE.findall(t))
    if n_prose_words >= 3:
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if not DOCX.exists():
        print(f'ERROR: {DOCX} not found', file=sys.stderr); return 1
    d = Document(str(DOCX))

    in_appendix = False
    formula_count = 0
    for i, p in enumerate(d.paragraphs):
        t = p.text.strip()
        if not t:
            continue
        if t.startswith('A  Formell') or t.startswith('A Formell'):
            in_appendix = True
            continue
        if t == 'Referansar':
            in_appendix = False
            continue
        if not in_appendix:
            continue
        if is_formula_line(t):
            formula_count += 1
            print(f'  para {i:3d} formula: {t[:80]}')
            if not args.dry_run:
                # Apply Cousine font + 11pt + left indent 0.6 cm for visual separation
                for r in p.runs:
                    r.font.name = 'Cousine'
                    r.font.size = Pt(11)
                p.paragraph_format.left_indent = Cm(0.6)
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
        elif HEADING_RE.match(t):
            # D4, T1, A1 etc — promote to small bold heading inside appendix
            if not args.dry_run:
                for r in p.runs:
                    r.font.name = 'Garamond'
                    r.font.size = Pt(11)
                    r.bold = True
                p.paragraph_format.left_indent = None
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(2)

    if not args.dry_run:
        d.save(str(DOCX))
    print(f"\n{'DRY' if args.dry_run else 'APPLY'}: {formula_count} formula lines styled")
    return 0


if __name__ == '__main__':
    sys.exit(main())
