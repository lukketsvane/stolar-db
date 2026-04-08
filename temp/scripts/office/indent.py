#!/usr/bin/env python3
"""
Apply Wittgenstein-style visual indentation to numbered propositions in
FORMLÆRE.docx. Each proposition's left indent corresponds to its
decimal depth, so the tree structure becomes visible at a glance.

Depth scheme (in cm):
  1, 2, 3 ...        depth 1  →  0.0 cm
  1.1, 1.2 ...       depth 2  →  0.6 cm
  1.21, 1.22 ...     depth 3  →  1.2 cm
  1.211 ...          depth 4  →  1.8 cm
  1.2111 ...         depth 5  →  2.4 cm

Also indents formal-appendix items D1..D9, T1..T6, A1..A4 to depth 2 so
they sit slightly under their A.x heading.

Run:
  python scripts/office/indent.py            # apply
  python scripts/office/indent.py --dry-run  # preview only
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

try:
    from docx import Document
    from docx.shared import Cm
except ImportError:
    print("ERROR: python-docx not installed.", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[2]
DOCX = ROOT / "FORMLÆRE.docx"

# Step size per nesting level
STEP_CM = 0.6

# A "1.21 d ..." style proposition: number + status + body
PROP_RE = re.compile(r'^(\d+(?:\.\d+)*)\s+[daiot]\s+')
# A formal-appendix entry like "D4 (..."  "T6 (..."  "A1 (..."
APPENDIX_RE = re.compile(r'^([DTA])(\d+)\s')


def depth_for(num: str) -> int:
    """Wittgenstein decimal depth.
    '1' → 1
    '1.1' → 2     (one digit after the dot)
    '1.21' → 3    (two digits after the dot)
    '1.211' → 4
    '5.521' → 4
    """
    if '.' not in num:
        return 1
    after = num.split('.', 1)[1]
    return len(after) + 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if not DOCX.exists():
        print(f"ERROR: {DOCX} not found", file=sys.stderr)
        return 1
    doc = Document(str(DOCX))

    changed = 0
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if not t:
            continue
        depth: int | None = None
        m = PROP_RE.match(t)
        if m:
            depth = depth_for(m.group(1))
        else:
            m2 = APPENDIX_RE.match(t)
            if m2:
                depth = 2  # treat formal-appendix items as one indent level
        if depth is None:
            continue
        indent_cm = (depth - 1) * STEP_CM
        if indent_cm < 0:
            continue
        # Check current indent (in cm)
        current = p.paragraph_format.left_indent
        current_cm = current.cm if current else 0.0
        if abs(current_cm - indent_cm) > 0.05:
            print(f"para {i:3d} depth {depth} {indent_cm:.2f}cm  {t[:60]}")
            if not args.dry_run:
                p.paragraph_format.left_indent = Cm(indent_cm)
            changed += 1

    if not args.dry_run:
        doc.save(str(DOCX))
    print(f"\n{'DRY' if args.dry_run else 'APPLY'}: {changed} paragraphs touched")
    return 0


if __name__ == '__main__':
    sys.exit(main())
